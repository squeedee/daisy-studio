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

### Populate:

- Barrel jack, DMP3056L reverse-polarity FET, SMBJ15CA input TVS,
  100 µF / 25 V bulk on +12V_RAW. Leave SW1 unjumpered initially —
  see 1.2; we're not stocking the JST switch header for this run, so
  SW1 will be wire-bridged after the open-state safety checks.
- TPS54302 + L3 (10 µH) + input MLCC (10 µF X7R 1206) + output caps
  (2× 22 µF / 25 V X7R 1206) + feedback divider + bootstrap cap.
- RS3-1212D + L1, L2 ferrites + post-ferrite bulk caps.
- SMAJ5.0A TVS on +5 V near the Seed footprint.

(JP1 ships pre-bridged from fab — no soldering required to keep
AGND/DGND/CHASSIS tied. See 1.1 for the optional cut-and-restore
isolation check.)

### Preload:

Before first power-up, install dummy loads across the rail breakout
header so each regulator has something to drive — confirms rails
come up under load and surfaces shorts/runaway without putting
downstream silicon at risk:

- **+12VA → AGND**: ~480 Ω, 1 W (≈ 25 mA).
- **−12VA → AGND**: ~480 Ω, 1 W (≈ 25 mA).
- **+5V → DGND**: ~100 Ω, 0.5 W (≈ 50 mA) — gives the TPS54302
  enough load to leave discontinuous-conduction mode for a clean
  ripple measurement; the Seed isn't fitted yet.

Leave these in place for the full Stage 1 power-up sequence — the
RS3-1212D should never see a no-load condition.

### Verify:

All Stage 1 power-up steps use a **bench-top PSU with current
limiting** in place of a wall-wart. Suggested starting limit: 300 mA
at 12 V — comfortably above the expected ~100–200 mA stage-1 draw
(dummy loads + DC/DC quiescent + buck efficiency loss) and tight
enough to fold back on a short before damage.

- [x] **1.1 Ground continuity (power off).** With JP1 bridged
  (default), DMM continuity from AGND through to each chassis
  mounting hole and to the ground shell of every Neutrik combo
  jack. Catches missing CHASSIS bonds and unstitched ground pours
  before any rail comes up.
    - *Optional isolation check (one board only):* cut JP1, confirm
      AGND/DGND no longer reads continuous to CHASSIS while the
      chassis-to-Neutrik-shell continuity remains. Re-bridge JP1
      with solder before continuing.
- [ ] **1.2 SW1-open safety pass (board still powered down).** With
  SW1 unjumpered, set PSU to 12 V / 300 mA limit, leads connected to
  the barrel jack with correct polarity. DMM on +12V_RAW — should
  stay at 0 V, PSU current ≈ 0. Reverse the PSU leads, repeat —
  again 0 V at +12V_RAW, no current. This proves SW1 isolates the
  rest of the board and that nothing bypasses it. Then **bridge
  SW1** with a short wire link soldered across its two pads (the
  panel-switch JST hardware isn't stocked for this build).
- [x] **1.3 +12V_RAW present.** PSU at 12 V, correct polarity, ramp
  from 0 V watching current. DMM on +12V_RAW downstream of the bulk
  cap reaches 11.7–11.9 V (small Vds drop across DMP3056L). Steady-
  state PSU current matches the preload + quiescent budget; nothing
  unexpected. **FAILED** ground not connected
- [ ] **1.4 Reverse-polarity blocks (FET).** Power down, reverse the
  PSU leads, ramp back up. DMP3056L blocks; +12V_RAW stays at 0 V,
  PSU current limited only by leakage (≪ 1 mA). Power down, restore
  polarity, confirm rails recover. **FAILED** Reverse S and D on mosfet
- [ ] **1.5 +5 V rail.** DMM on +5 V should read 5.05–5.15 V (FB
  divider 100 k / 13.3 k → 0.6 V × 8.52). AC-coupled scope at the
  same node — ripple well under 50 mV pp at the 500 kHz switching
  frequency. **REVISIT** after everything is fitted.
- [ ] **1.6 ±12 V rails (under preload).** DMM at the +12VA / −12VA
  test points: ±11.76 to ±12.24 V (RS3-1212D ±2%). Scope ripple at
  the same nodes after the ferrites — target < 10 mVpp in the audio
  band. The Preload resistors are the load throughout — **do not
  power the RS3-1212D unloaded**, no-load operation is the failure
  mode we're avoiding.

## Stage 2 — Daisy Seed + MIDI

### Populate:

- Daisy Seed module (**Rev 7 — required for Stage 3.4's PCM3060
  noise test**).
- H11L1SM optoisolator.
- MIDI passives: 220 Ω × 2, 1N4148W, 270 Ω, 33 Ω × 2, 33 Ω, 10 Ω,
  100 nF decouple.
- 3× SDS-50J DIN-5 jacks.
- Micro SD socket.

### Verify:

- [x] **2.1 Seed boots.** Power up. Boot LED on; USB enumerate when
  plugged into a host (DFU / serial device).
- [ ] **2.2 +3V3D from Seed.** DMM at the +3V3D pin on the GPIO
  breakout header.
- [x] **2.3 MIDI THRU passthrough.** External MIDI source (synth or
  USB-MIDI interface) into DIN-5 IN, monitor DIN-5 THRU with an
  external MIDI sink. Send a stream of note-ons; THRU should emit
  the same messages, byte-for-byte, with no Seed firmware involved
  — this exercises the H11L1SM forward path + 33 Ω THRU buffer
  resistors only.
- [x] **2.4 MIDI IN + OUT (digital thru on the Seed).** Load a Seed
  program that echoes every received MIDI byte straight back out
  (RX → TX, a software MIDI thru). External source → DIN-5 IN; sink
  on DIN-5 OUT. Notes sent in should reappear at OUT, exercising
  the full IN-side optoisolation path *and* the OUT-side driver in
  a single loop.
    - Firmware: `firmware/projects/test-midi/`.
- [ ] **2.5 SD card.** Mount + read a card from a test program. **NOT RUN** I'm not in the mood to solder that thing :P

## Stage 3 — Audio output stage

Lower clamp risk than the input — build it first so the codec
spectral check (3.4) runs without depending on input-side silicon.

### Populate:

- OPA1656 (output sheet) + R_in (2.2 kΩ) + R_fb_fixed (15 kΩ) +
  R_fb_trim (10 kΩ Bourns 3296W-1-103) + C_fb (100 pF C0G).
- OPA1656 supply decoupling (100 nF + 1 nF per rail).
- THAT1646 + datasheet decoupling.
- 4× SM4004 per channel (phantom protection at XLR pins).
- 2× SMBJ15CA bidirectional TVS on ±12 V → AGND near the RS3-1212D.
- 2× Neutrik NCJ6FA-H-0 output combo jacks.
- Daughterboard header (main-PCB side — IDC or stack-mount, your
  build mode).

### Calibrate:

- [x] **3.1 Output gain trim, channel L.**
    1. Set the L output level pot fully clockwise on the
       daughterboard.
    2. Play a digital full-scale 1 kHz sine from the Seed.
    3. Scope differential XLR output.
    4. Adjust R_fb_trim until the differential output reads +24 dBu
       (12.28 Vrms = 34.73 V p-p on the scope math channel A−B, or
       17.36 V p-p per leg single-ended assuming balanced output).
    5. Lock the trim with nail polish / trim paint.
- [x] **3.2 Output gain trim, channel R.** Same procedure on R.
  L/R within ~0.2 dB after both trims locked. See F1 in findings.
  **Done (Board 1, post-F1 R_fb swap):** both channels calibrated to
  +24 dBu at full gain; L/R match set by ear — scope p-p reading
  jittered in the mV range so a numeric delta wasn't recorded.

### Verify:

- [ ] **3.3 Phantom-power survival (bench-PSU simulated +48 V).**
  Daisy Studio fully powered down throughout this test (no supply
  on the barrel jack). A separate bench PSU plus two resistors
  emulates the phantom feed network of a real preamp.
    1. Build the phantom feed: 2× **6.81 kΩ, ¼ W** resistors, in
       parallel between the bench PSU's positive output and the two
       hot pins (XLR pin 2 + pin 3) of one Daisy Studio output. PSU
       − returns to Daisy Studio AGND or chassis.
    2. Scope on +12 V at the RS3-1212D output / an OPA1656 supply
       pin, DC-coupled.
    3. Set the bench PSU to **48 V, current limit ≈ 50 mA**. If the
       supply caps below 48 V, stack two channels in series; a 30 V
       test exercises the same path but won't push +12 V high enough
       to engage the TVS, so it isn't a complete check.
    4. Ramp from 0 → 48 V watching scope and PSU current. Expected:
       ~5 mA per pin, ~10 mA total into +12 V via the SM4004 forward
       clamps. SMBJ15CA on +12 V → AGND clamps at **16–24 V** — the
       +12 V rail should rise to that band and stop, no runaway
       above.
    5. Power down phantom PSU, swap to the other XLR output, repeat.
    6. Disconnect the phantom rig, restore Daisy Studio power,
       confirm op-amp + THAT1646 still pass signal cleanly (no
       SM4004 / TVS damage).
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

### Populate:

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

### Verify:

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

**Later with more boards:**

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

## Findings

### F1 — Output gain stage clips at R_fb = 15 kΩ on ±12 V rails

**Symptom (Board 1, Stage 3.1):** With R_fb_fixed = 15 kΩ + 10 kΩ
trim, the trim had to be dialled fully CCW (R_fb_total = 15 kΩ,
gain 6.82×) to get an undistorted output. Any rotation above the
end stop clipped at 0 dBFS.

**Bench measurements:**

- Codec output, single-ended on the codec side of R5/R6, at 0 dBFS
  1 kHz sine (sent via `firmware/projects/calibrate-output/`):
  **3.43 V p-p = 1.213 Vrms = +3.89 dBu**.
- ±12 V rails under signal load: **±12.12 V**, no sag.

**Analysis:** OPA1656 on ±12.12 V swings to ~±11.6 V peak under
the THAT1646 + 10 kΩ pot load — ~8.2 Vrms = **+20.5 dBu SE** =
**+26.5 dBu differential** at the rail limit. At gain 6.82× the
target OPA output is 1.213 × 6.82 = 8.27 Vrms = +20.6 dBu SE,
which is 0.1 dB into clipping. Matches the bench.

The Rev 2 design memo's "+21 to +25.6 dBu peak" headroom estimate
assumed ~1.5 dB more rail clearance than the OPA1656 actually
delivers on ±12 V. The 15 kΩ fixed value was set under that
optimistic ceiling.

**Resolution:** Swap R_fb_fixed (R2, R7) from 15 kΩ to **6.8 kΩ**
(or closest E12 from stock — 5.6 kΩ also workable). Keep the
10 kΩ Bourns trim. New range 6.8–16.8 kΩ → gain 3.09× to 7.64× →
peak differential output +19.7 to +27.6 dBu (OPA clip ceiling
+26.5 dBu).

- **+24 dBu calibration target lands at trim ≈ 44 % rotation** —
  near mid-pot, best resolution per turn and best tolerance margin
  between L and R during 3.2 channel-match.
- Top of trim travel sits ~1.1 dB past OPA clip — provides margin
  for component tolerance and lets the calibration procedure verify
  headroom by dialling up to clip and backing off.
- Minimum gain 3.09× = +19.7 dBu diff does *not* reach the +18 dBu
  consumer level. Acceptable — user can attenuate at the output
  level pot on the daughterboard if a lower nominal is needed.

**Action:** Swap R2 and R7 to 6.8 kΩ (or in-stock equivalent) on
all populated boards; update the Stage 3 Populate parts list before
the next build. Re-run 3.1 / 3.2 after the swap.

### F2 — GPIO header collides with Seed USB during programming

**Symptom (Board 1):** The GPIO breakout header on the main PCB sits
close enough to the Daisy Seed's USB connector that a USB cable
plugged in for programming/DFU fouls the header (or anything mated
into it). Programming the Seed in-circuit while the daughterboard
ribbon is connected is awkward at best.

**Resolution:** TBD — two candidate directions:

- **PCB-side fix (Rev 3):** Move the GPIO header further from the
  Seed USB cutout so a standard USB-micro plug + boot has clearance.
  Cheaper if we're already respinning for other reasons.
- **BOM-side fix (could apply to remaining Rev 2 boards):** Swap
  the GPIO header for a low-profile variant (e.g. surface-mount or
  shrouded low-stack), so its mating connector clears the USB plug.
  Constrains the daughterboard cable choice — needs cross-check
  against the existing mating part.

**Action:** Defer to Rev 3 issue triage. Don't change the Rev 2
schematic / PCB / BOM mid-validation.

## Equipment

- **Digilent Analog Discovery 2** — scope + spectrum analyzer + arb
  generator. Covers Stages 1, 2, 3.4 (>40 kHz hash), 4.1–4.6.
  AD2 self-noise ~1–2 mV RMS makes it unsuitable for audio-band
  noise-floor measurement (Stages 3.4 audio-band confirmation,
  4.8).
- Balanced signal source capable of +4 / +14 / +24 dBu, or AD2
  WaveGen + a balanced driver.
- **Bench-top PSU with current limit and voltage ramp** — primary
  Stage 1 supply. Reverse-polarity test is done by reversing the
  leads, no sacrificial cable needed.
- 3× dummy-load resistors for the Stage 1 preload: 2× ~480 Ω 1 W
  (±12 V) + 1× ~100 Ω 0.5 W (+5 V).
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
