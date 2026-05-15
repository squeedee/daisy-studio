#include "daisy_seed.h"
#include "arm_math.h"
#include <cmath>
#include <cstring>
#include <cstdlib>

using namespace daisy;

DaisySeed hw;

static constexpr size_t kFftSize    = 4096;
static constexpr float  kSampleRate = 48000.0f;
static constexpr float  kBinHz      = kSampleRate / float(kFftSize);
static constexpr size_t kNumBins    = kFftSize / 2 + 1;
static constexpr float  kTwoPi      = 6.28318530717958647692f;

enum Mode    { THD_MODE_INPUT = 0, THD_MODE_LOOPBACK = 1 };
enum Window  { THD_WIN_NONE   = 0, THD_WIN_HANN      = 1 };
enum Channel { THD_CH_L       = 0, THD_CH_R          = 1 };

static volatile uint8_t g_mode       = THD_MODE_INPUT;
static volatile uint8_t g_window     = THD_WIN_NONE;
static volatile uint8_t g_channel    = THD_CH_L;
static volatile float   g_freq_hz    = 1007.8125f;
static volatile float   g_drive_amp  = 0.25f;
static volatile float   g_phase      = 0.0f;
static volatile float   g_phase_inc  = 0.0f;

float DSY_SDRAM_BSS g_cap_buf[2][kFftSize];
float DSY_SDRAM_BSS g_work[kFftSize];
float DSY_SDRAM_BSS g_fft_out[kFftSize];
float DSY_SDRAM_BSS g_mag[kNumBins];
float DSY_SDRAM_BSS g_hann[kFftSize];

static volatile uint8_t  g_active_idx  = 0;
static volatile size_t   g_fill_pos    = 0;
static volatile uint8_t  g_ready_idx   = 0;
static volatile bool     g_frame_ready = false;

// Broadband peak tracking (cleared each LVL report).
static volatile float    g_peak       = 0.0f;
static volatile uint32_t g_peak_count = 0;

static arm_rfft_fast_instance_f32 g_rfft;

FIFO<char, 256> g_cmd_fifo;

static void RecomputePhaseInc(float fhz)
{
    g_phase_inc = kTwoPi * fhz / kSampleRate;
}

static size_t FundBin(float fhz)
{
    int b = int(roundf(fhz / kBinHz));
    if(b < 1) b = 1;
    if(b > int(kNumBins) - 1) b = int(kNumBins) - 1;
    return size_t(b);
}

static void SnapFreqToBin(float fhz)
{
    size_t b = FundBin(fhz);
    g_freq_hz = float(b) * kBinHz;
    RecomputePhaseInc(g_freq_hz);
}

static void UsbRxCallback(uint8_t* buff, uint32_t* length)
{
    if(!buff || !length) return;
    for(uint32_t i = 0; i < *length; ++i)
        g_cmd_fifo.PushBack((char)buff[i]);
}

static void AudioCallback(AudioHandle::InterleavingInputBuffer  in,
                          AudioHandle::InterleavingOutputBuffer out,
                          size_t                                size)
{
    uint8_t  mode   = g_mode;
    uint8_t  ch     = g_channel;
    float    amp    = g_drive_amp;
    float    phase  = g_phase;
    float    pinc   = g_phase_inc;
    uint8_t  active = g_active_idx;
    size_t   pos    = g_fill_pos;
    float    pk     = g_peak;
    uint32_t pkcnt  = g_peak_count;

    for(size_t i = 0; i < size; i += 2)
    {
        float sl = in[i];
        float sr = in[i + 1];

        float s = (ch == THD_CH_L) ? sl : sr;
        float a = fabsf(s);
        if(a > pk) pk = a;
        ++pkcnt;

        if(pos < kFftSize)
            g_cap_buf[active][pos++] = s;
        if(pos >= kFftSize)
        {
            g_ready_idx   = active;
            active        = 1 - active;
            pos           = 0;
            g_frame_ready = true;
        }

        float drv = 0.0f;
        if(mode == THD_MODE_LOOPBACK)
        {
            drv   = amp * sinf(phase);
            phase += pinc;
            if(phase > kTwoPi) phase -= kTwoPi;
        }
        out[i]     = drv;
        out[i + 1] = drv;
    }

    g_active_idx = active;
    g_fill_pos   = pos;
    g_phase      = phase;
    g_peak       = pk;
    g_peak_count = pkcnt;
}

static void BuildHannLUT()
{
    for(size_t i = 0; i < kFftSize; ++i)
        g_hann[i] = 0.5f * (1.0f - cosf(kTwoPi * float(i) / float(kFftSize - 1)));
}

static void PrintState()
{
    hw.PrintLine("STATE M%u W%u C%c F%.4f A%.4f BIN%u",
                 (unsigned)g_mode,
                 (unsigned)g_window,
                 g_channel == THD_CH_L ? 'l' : 'r',
                 g_freq_hz,
                 g_drive_amp,
                 (unsigned)FundBin(g_freq_hz));
}

static void HandleCommand(const char* cmd, size_t len)
{
    if(len < 1) return;
    char c = cmd[0];
    switch(c)
    {
        case 'M':
            if(len >= 2 && (cmd[1] == '0' || cmd[1] == '1'))
                g_mode = (cmd[1] == '0') ? THD_MODE_INPUT : THD_MODE_LOOPBACK;
            break;
        case 'W':
            if(len >= 2 && (cmd[1] == '0' || cmd[1] == '1'))
            {
                g_window = (cmd[1] == '0') ? THD_WIN_NONE : THD_WIN_HANN;
                if(g_window == THD_WIN_NONE) SnapFreqToBin(g_freq_hz);
            }
            break;
        case 'C':
            if(len >= 2 && (cmd[1] == 'l' || cmd[1] == 'L')) g_channel = THD_CH_L;
            else if(len >= 2 && (cmd[1] == 'r' || cmd[1] == 'R')) g_channel = THD_CH_R;
            break;
        case 'F':
        {
            if(len >= 2)
            {
                char tmp[32];
                size_t n = (len - 1 < sizeof(tmp) - 1) ? len - 1 : sizeof(tmp) - 1;
                memcpy(tmp, cmd + 1, n);
                tmp[n] = '\0';
                float f = strtof(tmp, nullptr);
                if(f > 1.0f && f < kSampleRate / 2.0f)
                {
                    g_freq_hz = f;
                    if(g_window == THD_WIN_NONE) SnapFreqToBin(f);
                    else RecomputePhaseInc(f);
                }
            }
            break;
        }
        case 'A':
        {
            if(len >= 2)
            {
                char tmp[32];
                size_t n = (len - 1 < sizeof(tmp) - 1) ? len - 1 : sizeof(tmp) - 1;
                memcpy(tmp, cmd + 1, n);
                tmp[n] = '\0';
                float a = strtof(tmp, nullptr);
                if(a >= 0.0f && a <= 1.0f) g_drive_amp = a;
            }
            break;
        }
        case '?':
            PrintState();
            break;
        default:
            break;
    }
}

static void ProcessFrame()
{
    uint8_t      idx = g_ready_idx;
    const float* src = g_cap_buf[idx];
    uint8_t      win = g_window;

    if(win == THD_WIN_HANN)
    {
        for(size_t i = 0; i < kFftSize; ++i) g_work[i] = src[i] * g_hann[i];
    }
    else
    {
        memcpy(g_work, src, sizeof(float) * kFftSize);
    }

    arm_rfft_fast_f32(&g_rfft, g_work, g_fft_out, 0);

    // arm_rfft_fast_f32 output layout (size N reals):
    //   [0]      = DC (real)
    //   [1]      = Nyquist (real)
    //   [2k..2k+1] = bin k {re, im} for k = 1 .. N/2 - 1
    g_mag[0]            = fabsf(g_fft_out[0]);
    g_mag[kFftSize / 2] = fabsf(g_fft_out[1]);
    for(size_t k = 1; k < kFftSize / 2; ++k)
    {
        float re = g_fft_out[2 * k];
        float im = g_fft_out[2 * k + 1];
        g_mag[k] = sqrtf(re * re + im * im);
    }

    // Amplitude scale: real-sine of amplitude A at exact bin →
    //   coherent: mag = N/2 · A          ⇒ A = 2·mag/N
    //   Hann (CG = 0.5): mag = N/4 · A   ⇒ A = 4·mag/N
    float amp_scale = (win == THD_WIN_HANN) ? (4.0f / float(kFftSize))
                                        : (2.0f / float(kFftSize));

    size_t fund_bin = FundBin(g_freq_hz);
    if(win == THD_WIN_HANN)
    {
        size_t lo   = (fund_bin >= 2) ? fund_bin - 2 : 0;
        size_t hi   = (fund_bin + 2 < kNumBins) ? fund_bin + 2 : kNumBins - 1;
        size_t best = fund_bin;
        float  bv   = g_mag[fund_bin];
        for(size_t k = lo; k <= hi; ++k)
            if(g_mag[k] > bv) { bv = g_mag[k]; best = k; }
        fund_bin = best;
    }

    auto bin_energy = [&](size_t b) -> float {
        if(win == THD_WIN_HANN)
        {
            float e = g_mag[b] * g_mag[b];
            if(b > 0)             e += g_mag[b - 1] * g_mag[b - 1];
            if(b + 1 < kNumBins)  e += g_mag[b + 1] * g_mag[b + 1];
            return e;
        }
        return g_mag[b] * g_mag[b];
    };

    float fund_e = bin_energy(fund_bin);
    float harm_e = 0.0f;
    for(int k = 2; k <= 9; ++k)
    {
        size_t hb = fund_bin * size_t(k);
        if(hb >= kNumBins) break;
        harm_e += bin_energy(hb);
    }

    float total_e = 0.0f;
    for(size_t k = 1; k < kNumBins; ++k) total_e += g_mag[k] * g_mag[k];

    float fund_mag  = sqrtf(fund_e);
    float fund_amp  = fund_mag * amp_scale;
    float fund_dbfs = (fund_amp > 1e-20f) ? 20.0f * log10f(fund_amp) : -200.0f;

    float thd      = (fund_e > 0.0f) ? sqrtf(harm_e / fund_e) : 0.0f;
    float thd_db   = (thd > 1e-20f) ? 20.0f * log10f(thd) : -200.0f;

    float noise_e  = total_e - fund_e - harm_e;
    if(noise_e < 0.0f) noise_e = 0.0f;
    float thdn     = (fund_e > 0.0f) ? sqrtf((harm_e + noise_e) / fund_e) : 0.0f;
    float thdn_db  = (thdn > 1e-20f) ? 20.0f * log10f(thdn) : -200.0f;

    float noise_sum = 0.0f;
    size_t noise_cnt = 0;
    for(size_t k = 1; k < kNumBins; ++k)
    {
        bool is_special = (k == fund_bin);
        if(!is_special)
        {
            for(int j = 2; j <= 9; ++j)
                if(k == fund_bin * size_t(j)) { is_special = true; break; }
        }
        if(!is_special) { noise_sum += g_mag[k]; ++noise_cnt; }
    }
    float noise_mag = (noise_cnt > 0) ? (noise_sum / float(noise_cnt)) : 0.0f;
    float noise_amp = noise_mag * amp_scale;
    float noise_db  = (noise_amp > 1e-20f) ? 20.0f * log10f(noise_amp) : -200.0f;

    float h_db[8];
    for(int k = 0; k < 8; ++k)
    {
        size_t hb = fund_bin * size_t(k + 2);
        if(hb >= kNumBins) { h_db[k] = -200.0f; continue; }
        float hm = sqrtf(bin_energy(hb));
        h_db[k]  = (hm > 1e-20f && fund_mag > 1e-20f)
                       ? 20.0f * log10f(hm / fund_mag)
                       : -200.0f;
    }

    hw.PrintLine("THD %.3f %.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f",
                 fund_dbfs,
                 thd_db,
                 thdn_db,
                 noise_db,
                 h_db[0], h_db[1], h_db[2], h_db[3],
                 h_db[4], h_db[5], h_db[6], h_db[7]);
}

int main(void)
{
    hw.Configure();
    hw.Init();
    hw.SetAudioBlockSize(48);
    hw.StartLog(false);
    hw.usb_handle.SetReceiveCallback(UsbRxCallback,
                                     UsbHandle::UsbPeriph::FS_INTERNAL);

    BuildHannLUT();
    arm_rfft_fast_init_f32(&g_rfft, kFftSize);
    SnapFreqToBin(g_freq_hz);

    hw.StartAudio(AudioCallback);

    char   cmd_buf[64];
    size_t cmd_len = 0;

    uint32_t next_led = System::GetNow() + 500;
    uint32_t next_lvl = System::GetNow() + 33;
    bool     led      = false;

    while(1)
    {
        while(!g_cmd_fifo.IsEmpty())
        {
            char c = g_cmd_fifo.PopFront();
            if(c == '\r') continue;
            if(c == '\n')
            {
                HandleCommand(cmd_buf, cmd_len);
                cmd_len = 0;
            }
            else if(cmd_len < sizeof(cmd_buf) - 1)
            {
                cmd_buf[cmd_len++] = c;
            }
            else
            {
                cmd_len = 0;
            }
        }

        if(g_frame_ready)
        {
            g_frame_ready = false;
            ProcessFrame();
        }

        uint32_t now = System::GetNow();
        if(now >= next_lvl)
        {
            __disable_irq();
            float    pk = g_peak;
            uint32_t pc = g_peak_count;
            g_peak       = 0.0f;
            g_peak_count = 0;
            __enable_irq();
            if(pc > 0)
            {
                float db = (pk > 1e-20f) ? 20.0f * log10f(pk) : -200.0f;
                hw.PrintLine("LVL %.3f", db);
            }
            next_lvl = now + 33;
        }
        if(now >= next_led)
        {
            led = !led;
            hw.SetLed(led);
            next_led = now + 500;
        }
    }
}
