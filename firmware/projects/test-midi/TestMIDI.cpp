#include "daisy_seed.h"

using namespace daisy;

DaisySeed       hw;
MidiUartHandler midi;

constexpr uint32_t kLedFlashMs = 30;
uint32_t           led_off_time = 0;

static uint8_t StatusByteFor(const MidiEvent& msg)
{
    uint8_t ch = static_cast<uint8_t>(msg.channel) & 0x0F;
    switch(msg.type)
    {
        case NoteOff:               return 0x80 | ch;
        case NoteOn:                return 0x90 | ch;
        case PolyphonicKeyPressure: return 0xA0 | ch;
        case ControlChange:         return 0xB0 | ch;
        case ProgramChange:         return 0xC0 | ch;
        case ChannelPressure:       return 0xD0 | ch;
        case PitchBend:             return 0xE0 | ch;
        default:                    return 0;
    }
}

static int DataByteCount(MidiMessageType type)
{
    switch(type)
    {
        case ProgramChange:
        case ChannelPressure:
            return 1;
        case NoteOff:
        case NoteOn:
        case PolyphonicKeyPressure:
        case ControlChange:
        case PitchBend:
            return 2;
        default:
            return 0;
    }
}

static void EmitSysExSummary(MidiEvent& msg)
{
    if(msg.sysex_message_len < 1)
        return;

    bool   extended = (msg.sysex_data[0] == 0x00);
    size_t mfr_len  = extended ? 3 : 1;
    if(msg.sysex_message_len < mfr_len)
        return;

    uint8_t  out[7];
    size_t   i   = 0;
    uint16_t len = msg.sysex_message_len;

    out[i++] = 0xF0;
    for(size_t k = 0; k < mfr_len; k++)
        out[i++] = msg.sysex_data[k];
    out[i++] = len & 0x7F;
    out[i++] = (len >> 7) & 0x7F;
    out[i++] = 0xF7;

    midi.SendMessage(out, i);
}

static void EchoEvent(MidiEvent& msg)
{
    if(msg.type == SystemRealTime)
    {
        uint8_t status = 0xF8 | (static_cast<uint8_t>(msg.srt_type) & 0x07);
        midi.SendMessage(&status, 1);
        return;
    }

    if(msg.type == SystemCommon && msg.sc_type == SystemExclusive)
    {
        EmitSysExSummary(msg);
        return;
    }

    uint8_t status = StatusByteFor(msg);
    if(status == 0)
        return;
    uint8_t bytes[3] = {status, msg.data[0], msg.data[1]};
    midi.SendMessage(bytes, 1 + DataByteCount(msg.type));
}

int main(void)
{
    hw.Init();

    MidiUartHandler::Config midi_config;
    midi.Init(midi_config);
    midi.StartReceive();

    while(1)
    {
        midi.Listen();

        while(midi.HasEvents())
        {
            MidiEvent msg = midi.PopEvent();

            EchoEvent(msg);

            if(msg.type == NoteOn && msg.data[1] > 0)
            {
                hw.SetLed(true);
                led_off_time = System::GetNow() + kLedFlashMs;
            }
        }

        if(led_off_time != 0 && System::GetNow() >= led_off_time)
        {
            hw.SetLed(false);
            led_off_time = 0;
        }
    }
}
