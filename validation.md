# Rev 2 Build & Validation

5 boards on order with full BOM. Build the **first board incrementally**
— populate one subsystem, validate, then move on. Catches PCB issues
(shorts, missing nets, footprint mismatches) before each new section's
parts are at risk. Once Board 1 passes through Stage 4, the remaining
four can be built straight through using the proven sequence.

For circuit operation, see [README.md → Circuit Function](README.md#circuit-function).

## Pre-build sanity

Before reflow / hand-soldering anything:

- [ ] **All five PCBs visually inspected.** Look for fab defects on the
  power section's high-current traces and the BJT clamp ground pours.
- [ ] **H11L1SM footprint matches the populated package.** Datasheet
  pad pitch / size / land length vs. the actual PCB pads. Footprint
  was wrong in Rev 1 and is the highest-confidence fab-side risk.
- [ ] **RS3-1212D pin 3 (CTRL) routed to nothing.** Datasheet forbids
  a low state on this pin; ERC catches the schematic via the
  no-connect flag, but the PCB is the final truth.

## Stage 1 — Power

Goal: all three rails (+5 V, ±12 V) up and clean before any signal-path
silicon is at risk.

**Populate:**
- Barrel jack, SW1 with shunt harness, DMP3056L reverse-polarity FET,
  SMBJ15CA input TVS, 100 µF / 25 V bulk on +12V_RAW.
- TPS54302 + L3 (10 µH) + input MLCC (10 µF X7R 1206) + output caps
  (2× 22 µF / 25 V X7R 1206) + feedback divider + bootstrap cap.
- RS3-1212D + L1, L2 ferrites + post-ferrite bulk caps.
- SMAJ5.0A TVS on +5 V near the Seed footprint.
- JP1 solder jumper bridged.

**Verify:**
- [ ] **1.1 +12V_RAW present.** 12 V wall-wart in, shunt on SW1, DMM on
  +12V_RAW (downstream of bulk cap). 11.5–13 V depending on supply.
- [ ] **1.2 Reverse-polarity blocks.** Reverse the wall-wart with a
  sacrificial cable. DMP3056L blocks; no rail activity, no current
  draw. Restore polarity, confirm rails recover.
- [ ] **1.3 Panel-switch header.** Pull the shunt harness — power off.
  Reinstall — power on. (Verifies SW1 is in series, not parallel.)
- [ ] **1.4 +5 V rail.** DMM on +5 V should read 5.05–5.15 V (FB
  divider 100 k / 13.3 k → 0.6 V × 8.52). AC-coupled scope at the
  same node — ripple well under 50 mV pp at the 500 kHz switching
  frequency.
- [ ] **1.5 ±12 V rails (no Seed yet).** DMM at the +12VA / −12VA test
  points: ±11.76 to ±12.24 V (RS3-1212D ±2%). Scope ripple at the same
  nodes after the ferrites — target < 10 mVpp in the audio band.
- [ ] **1.6 ±12 V under load.** Apply ~25 mA dummy load per rail
  (≈ 480 Ω, 1 W resistor between each rail and AGND). Rails stay
  within ±2%. Defensive margin check — neither header carries ±12 V
  to user circuitry.

## Stage 2 — Daisy Seed + MIDI

**Populate:**
- Daisy Seed module (**Rev 7 — required for Stage 3.4's PCM3060
  noise test**).
- H11L1SM optoisolator.
- MIDI passives: 220 Ω × 2, 1N4148W, 270 Ω, 33 Ω × 2, 33 Ω, 10 Ω,
  100 nF decouple.
- 3× SDS-50J DIN-5 jacks.
- Micro SD socket.

**Verify:**
- [ ] **2.1 Seed boots.** Power up. Boot LED on; USB enumerate when
  plugged into a host (DFU / serial device).
- [ ] **2.2 +3V3D from Seed.** DMM at the +3V3D pin on the GPIO
  breakout header.
- [ ] **2.3 MIDI loopback.** External synth or USB-MIDI interface +
  DIN cables. DIN-5 IN → THRU passes notes through unchanged. Seed
  UART TX → DIN-5 OUT → external MIDI input (load a Seed program
  emitting note-ons). 31.25 kbaud.
- [ ] **2.4 SD card.** Mount + read a card from a test program.

## Stage 3 — Audio output stage

Lower clamp risk than the input — build it first so the codec
spectral check (3.4) runs without depending on input-side silicon.

**Populate:**
- OPA1656 (output sheet) + R_in (2.2 kΩ) + R_fb_fixed (15 kΩ) +
  R_fb_trim (10 kΩ Bourns 3296W-1-103) + C_fb (100 pF C0G).
- OPA1656 supply decoupling (100 nF + 1 nF per rail).
- THAT1646 + datasheet decoupling.
- 4× SM4004 per channel (phantom protection at XLR pins).
- 2× SMBJ15CA bidirectional TVS on ±12 V → AGND near the RS3-1212D.
- 2× Neutrik NCJ6FA-H-0 output combo jacks.
- Daughterboard header (main-PCB side — IDC or stack-mount, your
  build mode).

**Calibrate:**
- [ ] **3.1 Output gain trim, channel L.**
  1. Either set the L output level pot fully clockwise on the
     daughterboard, **or** temporarily jumper the daughterboard
     header's `OUT_OPA_L` to `OUT_WIPER_L` if the daughterboard
     isn't built yet.
  2. Play a digital full-scale 1 kHz sine from the Seed.
  3. Scope differential XLR output.
  4. Adjust R_fb_trim until output reads +24 dBu peak (12.28 V p-p
     differential).
  5. Lock the trim with nail polish / trim paint.
- [ ] **3.2 Output gain trim, channel R.** Same procedure on R.
  L/R within ~0.2 dB after both trims locked.

**Verify:**
- [ ] **3.3 Phantom-power survival.** Power *off* Daisy Studio. Plug
  an XLR output into a phantom-enabled mic preamp with +48 V
  asserted. Watch ±12 V rail with scope — SMBJ15CA should clamp at
  ≈ 16 V, no excursion above. Disconnect, power Daisy Studio back
  on, confirm op-amp + THAT1646 still pass signal cleanly.
- [ ] **3.4 Reconstruction-LPF spectral check (Seed Rev 7 only).**
  - 3.4a XLR diff noise floor with C_fb **un**populated, Seed playing
    digital silence.
  - 3.4b Repeat with C_fb = 100 pF populated.
  - 3.4c Compare broadband floor + spectral content above 40 kHz.
    AD2 spectrum analyzer at 1 MS/s sample rate covers this — the
    relative delta in the >40 kHz region is what matters; AD2 self-
    noise is ~40 dB above the codec's audio-band floor so this is
    *not* an audio-band measurement. (For audio-band confirmation
    you'd need an audio-grade interface — see Equipment.)
  - 3.4d **Escalation gate.** If 1-pole @ 80 kHz looks insufficient
    against the codec's actual spectrum → escalate to a 2-pole
    Sallen-Key post-gain-stage (board-revision-scale change). Do
    **not** increase C_fb — it kills the audio top octave. Pause
    further population on remaining boards until decided.

## Stage 4 — Audio input stage (highest-risk block)

The BJT clamp + OPA1656 + ±1.565 V reference is sim-validated only.
This stage is where Rev 2's novel circuitry gets bench-confirmed.

**Populate (Board 1 only at first):**
- THAT1246 + datasheet decoupling.
- OPA1656 (input sheet) + R_in (10 kΩ) + R_fb (12 kΩ) + supply
  decoupling.
- R_out (3.3 kΩ).
- BJT clamp per channel: 2N3906 PNP + 2N3904 NPN.
- Reference dividers per channel: 10 kΩ + 1.5 kΩ each rail + 47 µF
  X7R 1206 holding caps to AGND.
- C_aa (1 nF C0G) at the Seed input pin.
- LM2903 dual comparator + 1 kΩ LED limit + decoupling.
- 2× Neutrik NCJ6FA-H-0 input combo jacks.

**Verify on Board 1 before populating Boards 2–5:**
- [ ] **4.1 Reference rails.** DMM at +VCLAMP_L, +VCLAMP_R, −VCLAMP_L,
  −VCLAMP_R: each ±1.51 to ±1.62 V (nominal 1.565 V, ±1 % R + ±2 %
  rail). Confirm per-channel independence — driving overdrive on one
  channel must not move the other channel's reference.
- [ ] **4.2 Clean-signal gain sweep.** Inject +4 / +14 dBu balanced
  at the THAT1246. Scope the Seed input pin across pot travel.
  Scaling matches the README Performance table — clean at +4 dBu,
  OPA output ~3.3 V peak at +14 dBu, no clamp conduction.
- [ ] **4.3 Pathological overdrive — codec_max.** +24 dBu balanced
  in, input level pot fully clockwise (worst case). Scope the Seed
  input pin: peak ≤ 4.8 V. Sim says 4.49–4.64 V across tolerance
  corners; want ≥ 100 mV margin to 4.8 V.
- [ ] **4.4 Op-amp recovery.** Drop input back to +4 dBu after the
  +24 dBu overdrive — signal returns clean within < 100 µs, no
  latch-up, no rail-stick.
- [ ] **4.5 Reference pumping under overdrive.** During +24 dBu
  overdrive, scope +VCLAMP_* and −VCLAMP_* — should shift < 50 mV
  (sim says 18 mV). This is the BJT clamp's headline behaviour over
  passive diode alternatives.
- [ ] **4.6 Clip-LED behaviour.** Threshold trim mid-travel — LED
  off below threshold, proportional glow above. Trim range covers
  the full clean-signal range (0 V to 1.565 V threshold).

**After Boards 2–5 reach this stage:**
- [ ] **4.7 codec_max across boards.** Repeat 4.3 on all five.
  Single-board codec_max is not representative; tolerance corner
  validation needs the population. Want every board ≤ 4.8 V with
  ≥ 100 mV margin.

**Open noise-floor item:**
- [ ] **4.8 Audio-band noise floor.** Input shorted at the XLR.
  Compare to sim's 1.4 µV rms output-noise estimate. Requires an
  audio-grade interface (MOTU M2/M4, RME Babyface, Cosmos APU) —
  AD2's ~1–2 mV RMS self-noise is ~40 dB above the expected floor.
  If only AD2 is available, document the gap rather than reporting
  the AD2 measurement as the board's noise floor.

## Stage 5 — Daughterboard + integration

**Populate (daughterboard fab — separate PCB):**
- 2× 10 kΩ log audio pots (input level, L + R).
- 2× 10 kΩ log audio pots (output level, L + R).
- 2× 10 kΩ trim pots (clip threshold, L + R).
- 2× clip LEDs.
- Mating header (IDC ribbon socket or Samtec stack-mount socket).

**Verify:**
- [ ] **5.1 Pot rotation matches level change.** L and R separately,
  both stages.
- [ ] **5.2 Mute leg works.** CCW = silence, no leakage with full
  upstream signal.
- [ ] **5.3 Clip-threshold trim through the cable.** Behaviour
  matches the bench-trim version from Stage 4.
- [ ] **5.4 End-to-end signal path.** Balanced input → balanced
  output, both channels, levelled to taste.
- [ ] **5.5 Soak / listen test.** Real audio source for 30+ min —
  hum, hiss, intermittents, thermal drift.

## Equipment

- **Digilent Analog Discovery 2** — scope + spectrum analyzer + arb
  generator. Covers Stages 1, 2, 3.4 (>40 kHz hash), 4.1–4.6.
  AD2 self-noise ~1–2 mV RMS makes it unsuitable for audio-band
  noise-floor measurement (Stages 3.4 audio-band confirmation,
  4.8).
- Balanced signal source capable of +4 / +14 / +24 dBu, or AD2
  WaveGen + a balanced driver.
- 2× ~480 Ω, 1 W dummy-load resistors (Stage 1.6).
- Sacrificial 12 V wall-wart / cable for the reverse-polarity test
  (Stage 1.2).
- External synth + 2× DIN-5 MIDI cables, or USB-MIDI interface
  (Stage 2.3).
- Phantom-enabled mic preamp (Stage 3.3).
- **Audio-grade interface** *(optional, only if you want a usable
  audio-band noise-floor number for 3.4 / 4.8)*: MOTU M2/M4, RME
  Babyface, Cosmos APU. Cost vs. value: lets you confirm the
  audible C_fb delta and put a real µV figure on the input-stage
  floor. Skip if you're satisfied with sim-only audio-band claims
  and AD2 out-of-band confirmation.

## Escalation parts (don't pre-order — pull from local stock if needed)

- **2-pole Sallen-Key escalation set** (extra OPA1656 + matched
  R/C) — only if 3.4d fires.
- **R_fb = 11 kΩ** for the input stage (gain 1.1×, +0.8 dB) — only
  if 4.3 shows premature OPA1656 rail clipping at +24 dBu.
