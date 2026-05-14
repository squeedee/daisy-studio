#include "daisy_seed.h"
#include <cmath>

using namespace daisy;

DaisySeed hw;

static volatile float    g_peak_l = 0.f, g_peak_r = 0.f;
static volatile float    g_sumsq_l = 0.f, g_sumsq_r = 0.f;
static volatile uint32_t g_count = 0;

static void AudioCallback(AudioHandle::InterleavingInputBuffer  in,
                          AudioHandle::InterleavingOutputBuffer out,
                          size_t                                size)
{
    float    pk_l = g_peak_l, pk_r = g_peak_r;
    float    ss_l = g_sumsq_l, ss_r = g_sumsq_r;
    uint32_t cnt = g_count;

    for(size_t i = 0; i < size; i += 2)
    {
        float sl   = in[i];
        float sr   = in[i + 1];
        out[i]     = sl;
        out[i + 1] = sr;

        float al = fabsf(sl);
        float ar = fabsf(sr);
        if(al > pk_l)
            pk_l = al;
        if(ar > pk_r)
            pk_r = ar;
        ss_l += sl * sl;
        ss_r += sr * sr;
        cnt += 1;
    }

    g_peak_l  = pk_l;
    g_peak_r  = pk_r;
    g_sumsq_l = ss_l;
    g_sumsq_r = ss_r;
    g_count   = cnt;
}

int main(void)
{
    hw.Configure();
    hw.Init();
    hw.SetAudioBlockSize(48);
    hw.StartLog(false);
    hw.StartAudio(AudioCallback);

    constexpr uint32_t kReportIntervalMs    = 33;
    constexpr float    kPeakHoldDecayPerRpt = 0.95f;

    float    peak_hold_l    = 0.f;
    float    peak_hold_r    = 0.f;
    uint32_t next_report    = System::GetNow() + kReportIntervalMs;
    bool     led_state      = false;
    uint32_t next_led       = System::GetNow() + 500;

    while(1)
    {
        uint32_t now = System::GetNow();

        if(now >= next_report)
        {
            float    pk_l, pk_r, ss_l, ss_r;
            uint32_t cnt;
            __disable_irq();
            pk_l      = g_peak_l;
            pk_r      = g_peak_r;
            ss_l      = g_sumsq_l;
            ss_r      = g_sumsq_r;
            cnt       = g_count;
            g_peak_l  = 0.f;
            g_peak_r  = 0.f;
            g_sumsq_l = 0.f;
            g_sumsq_r = 0.f;
            g_count   = 0;
            __enable_irq();

            float rms_l = cnt > 0 ? sqrtf(ss_l / (float)cnt) : 0.f;
            float rms_r = cnt > 0 ? sqrtf(ss_r / (float)cnt) : 0.f;

            peak_hold_l *= kPeakHoldDecayPerRpt;
            peak_hold_r *= kPeakHoldDecayPerRpt;
            if(pk_l > peak_hold_l)
                peak_hold_l = pk_l;
            if(pk_r > peak_hold_r)
                peak_hold_r = pk_r;

            hw.PrintLine("%.6f %.6f %.6f %.6f %.6f %.6f",
                         pk_l,
                         rms_l,
                         peak_hold_l,
                         pk_r,
                         rms_r,
                         peak_hold_r);

            next_report = now + kReportIntervalMs;
        }

        if(now >= next_led)
        {
            led_state = !led_state;
            hw.SetLed(led_state);
            next_led = now + 500;
        }
    }
}
