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
  unexpected. **FAILED** ground not connected (issue #13, Rev 2c fix)
- [ ] **1.4 Reverse-polarity blocks (FET).** Power down, reverse the
  PSU leads, ramp back up. DMP3056L blocks; +12V_RAW stays at 0 V,
  PSU current limited only by leakage (≪ 1 mA). Power down, restore
  polarity, confirm rails recover. **FAILED** Reverse S and D on mosfet
  (issue #14, Rev 2c fix)
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

**Preferred method — loopback THD analyzer.** The
`firmware/projects/thd-meter` build + `thd-meter.html` Web Serial UI in
**Loopback mode** is the gold-standard trim aid here, far more sensitive
than scope p-p readings. The harmonic table shows H2..H9 in dB below the
fundamental; a clean output stage leaves H4..H9 sitting in the codec
noise floor (~−115 dB and below). The instant the output stage (or
input clamp graze) begins to distort, the **broadband H4..H9 fanout
lifts off the noise floor by 10–30 dB** while the scalar THD number
barely changes. That fanout is the most sensitive single indicator we
have of "clean ceiling crossed" — visible long before THD or scope
shape moves. See F9 below for the method's full story.

- [x] **3.1 Output gain trim, channel L (RV2).**
    1. Set the L output level pot fully clockwise on the
       daughterboard.
    2. Flash `thd-meter`, open `thd-meter.html`, set Mode = Loopback,
       Channel = L (capture), Drive = 1.0 (digital full scale), Window
       = Coherent. Connect L XLR OUT to L XLR IN with a known-good
       cable.
    3. Trim **RV2** until the harmonic table shows H4..H9 dropping
       into the noise floor (≤ −115 dB below fundamental). Around the
       transition you'll see a 0.1 dB rotation pop H4..H9 up 15–25 dB
       — back off the trim until they re-merge with the floor, then
       give yourself a small additional CCW margin (~0.5 dB at the
       codec input level) so component-tolerance drift can't drift
       the chain back into the graze.
    4. Note the codec input level at the locked trim (typically
       −4 to −5 dBFS at digital scale 1.0). Calibrated full-scale
       output is now somewhat below +24 dBu — quote the actual figure
       in the calibration sticker.
    5. Lock the trim with nail polish / trim paint.
- [x] **3.2 Output gain trim, channel R (RV4).** Same procedure on R,
  trimming **RV4**. Match L's locked codec input level within
  ~0.1 dB. See F1 and F9 in findings.
  **Done (Board 1, post-F1 R_fb swap, post-F9 procedure update):** both
  channels re-trimmed using the loopback-THD method. Earlier scope-only
  trim landed both channels at the BJT-clamp graze threshold (per F5)
  with R about 0.8 dB hotter than L — produced a clear H4..H9 fanout on
  R at digital full scale. After re-trim, fanout merged into the noise
  floor on both channels.

**Reference designator note:** **RV2 = L feedback trim**, **RV4 = R
feedback trim** (audio_output.kicad_sch). RV2 sits in the top half of
the sheet near `AUDIO_OUT_L`; RV4 in the bottom near `AUDIO_OUT_R`.
Worth a hand-label on the silkscreen — same class of L/R-identification
trap as F8.

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

### Signal-level reference (sim)

Source: `sim/input/measure.asc` — 1 kHz sine, `.tran` with `.step amp` ×
`.step pk`. All values **V p-p**.

**Per-stage levels** (independent of pot position):

| Input level | Balanced (each leg) | THAT1246 out |       OPA1656 out |
|-------------|--------------------:|-------------:|------------------:|
| +4 dBu      |                1.74 |         1.74 |              2.08 |
| +18 dBu     |                8.70 |         8.70 |             10.45 |
| +24 dBu     |               17.36 | 17.36(17.23) | 20.83(20.6/20.72) |

Each leg p-p ≡ differential p-p / 2. THAT1246 has −6 dB ⇒ single-ended
output p-p numerically matches each-leg p-p. OPA1656 fixed gain ×1.2;
stays inside ±11 V rails at +24 dBu — no opamp clip.

**Pot sweep — +4 dBu in** (OPA out = 2.08 V p-p):

| Pot rotation |             Wiper |           Seed_In | measured without seed |
|-------------:|------------------:|------------------:|-----------------------|
|           0% |           ~0(0/0) |           ~0(0/0) | 0/0                   |
|          20% |              0.38 |              0.30 |                       |
|          50% | 0.91(1.049/1.025) | 0.73(0.485/0.479) | 1.039/1.019           |
|          70% |              1.29 |              1.04 |                       |
|         100% |   2.08(2.10/2.12) | 1.67(1.046/1.046) | 2.06/2.05             |

**Pot sweep — +18 dBu in** (OPA out = 10.45 V p-p):

| Pot rotation | Wiper |                            Seed_In | opa out |
|-------------:|------:|-----------------------------------:|--------:|
|           0% |    ~0 |                                 ~0 |   10.36 |
|          20% |  1.90 |                               1.53 |   10.36 | 
|          50% |  4.54 |                   3.64 (2.35/2.27) |   10.36 |
|          70% |  6.27 |              4.63 ⚠ clamp engaging |   10.37 |
|         100% | 10.45 | 4.79 ⚠ clamp asymptote (4.17/4.15) |   10.37 |

**Pot sweep — +24 dBu in** (OPA out = 20.83 V p-p):

| Pot rotation |               Wiper |                           Seed_In |
|-------------:|--------------------:|----------------------------------:|
|           0% |                  ~0 |                                ~0 |
|          20% |                3.80 |             3.04 ⚠ clamp engaging |
|          50% |    7.96 (9.63/9.48) | 4.73 ⚠ clamp asymptote(4.14/4.12) |
|          70% |               10.78 |                              4.80 |
|         100% | 20.83 (20.75/20.62) |                  4.92 (4.26/4.24) |

Clamp asymptote at Seed_In is **~4.8–4.9 V p-p** (≈ ±2.45 V peaks)
regardless of how hard the wiper is driven — symmetric ±1.565 V
reference assumed. Per F5 the actual bench reference is asymmetric, so
expect positive peaks to clamp ~9% earlier.

### Verify:

- [ ] **4.1 Reference rails.** DMM at +VCLAMP_L, +VCLAMP_R, −VCLAMP_L,
  −VCLAMP_R. **Note: asymmetric per F5** (clip-threshold pot loading
  the + dividers):
    - −VCLAMP_L/R: **−1.51 to −1.62 V** (nominal −1.565 V, R ±1 % +
      rail ±2 %).
    - +VCLAMP_L/R: **+1.34 to +1.45 V** (nominal +1.40 V, R ±1 % +
      pot ±5 % end-to-end + rail ±2 %).
    - Confirm per-channel independence — driving overdrive on one
      channel must not move the other channel's reference.
- [ ] **4.2 Clean-signal gain sweep.** Inject +4 / +14 dBu balanced
  at the THAT1246. Scope the Seed input pin across pot travel.
  Scaling matches the README Performance table — clean at +4 dBu,
  OPA output ~3.3 V peak at +14 dBu, no clamp conduction.
- [ ] **4.3 Pathological overdrive — codec_max.** +24 dBu balanced
  in, input level pot fully clockwise (worst case). Scope the Seed
  input pin: **p-p ≤ 4.8 V** (set by the Seed's input-pin ESD clamp
  diodes — the codec itself is AC-coupled and re-biased to mid-rail
  internally). Sim says **4.49–4.64 V p-p** across tolerance
  corners (assumed symmetric ±1.565 V VCLAMP); want ≥ 100 mV
  margin to 4.8 V p-p. Per F5, the actual clamp is asymmetric —
  expect ~+2.08 V on positive peaks, ~−2.27 V on negative peaks
  (≈ 4.35 V p-p) on the bench.
- [ ] **4.4 Op-amp recovery.** Drop input back to +4 dBu after the
  +24 dBu overdrive — signal returns clean within < 100 µs, no
  latch-up, no rail-stick.
- [ ] **4.5 Reference pumping under overdrive.** During +24 dBu
  overdrive, scope +VCLAMP_* and −VCLAMP_* — should shift < 50 mV
  (sim says 18 mV). This is the BJT clamp's headline behaviour over
  passive diode alternatives.
- [ ] **4.6 Clip-LED threshold trim (RV7 channel L, RV8 channel R —
  see F8 note on swapped sides).** Set the trip point at the actual
  input-clamp engagement, using the loopback-THD method as the
  reference, *not* an arbitrary mid-travel position:
    1. Mode = Loopback, Channel = side under trim, Drive = 1.0,
       Window = Coherent. Output level pot full CW.
    2. Slowly raise the output level pot (or equivalently the
       feedback trim) until the **H4..H9 fanout** just begins to lift
       off the noise floor — this is the BJT clamp graze threshold
       per F5.
    3. Adjust the clip-LED trim (RV7/RV8) so the LED transitions from
       dark to first visible glow at exactly that signal level.
    4. Verify: back off the output pot slightly → LED returns to dark
       and H4..H9 return to floor. Drive a bit harder → LED brightens
       proportionally and H4..H9 lift further. The LED should fire
       just before the THD analyzer detects audible distortion onset.
    5. Per F5, the +VCLAMP asymmetry means the positive-peak clamp
       engages first; this naturally aligns the LED with the worst-
       side limit, which is the conservative choice.

**Later with more boards:**

- [ ] **4.7 codec_max across boards.** Repeat 4.3 on all five.
  Single-board codec_max is not representative; tolerance corner
  validation needs the population. Want every board ≤ 4.8 V p-p
  with ≥ 100 mV margin.

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

**Resolution (Rev 2c — issue #15):** Swap R_fb_fixed (R2, R7) from
15 kΩ to **6.8 kΩ** (5.6 kΩ acceptable as a stock alternate). Keep
the 10 kΩ Bourns trim. New range 6.8–16.8 kΩ → gain 3.09× to 7.64× →
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

**Action:** Rev 2b bench mitigation — hand-swap R2/R7 to **10 kΩ**
(closest in-stock value, sufficient to clear the clip ceiling and let
Stage 3 validation proceed). Rev 2c spin ships with 6.8 kΩ default
per the schematic / BOM update. Re-run 3.1 / 3.2 after the swap.

### F2 — GPIO header collides with Seed USB during programming

**Symptom (Board 1):** The GPIO breakout header on the main PCB sits
close enough to the Daisy Seed's USB connector that a USB cable
plugged in for programming/DFU fouls the header (or anything mated
into it). Programming the Seed in-circuit while the daughterboard
ribbon is connected is awkward at best.

**Resolution (Rev 3 — issue #16):** Move the GPIO header further from
the Seed USB cutout so a standard USB-micro plug + boot has clearance.
Assume a right-angle low-profile USB breakout cable on the host side
(specific part TBD) — pick the header position to accommodate it.

**Action:** Defer to Rev 3. No change to Rev 2b / 2c schematic / PCB.

### F3 — H11L1SM optoisolator pads still under-sized

**Symptom (Board 1, pre-build inspection / hand-soldering):** The Rev 2
H11L1SM footprint pads are *just* wide enough to capture the package
leads — soldering is workable but there's almost no land beyond the
lead edges for fillet or for visual inspection. Better than Rev 1
(where the footprint was outright wrong, flagged in pre-build sanity)
but still under IPC-recommended land allowance.

**Resolution (Rev 2c — issue #17):** Extend the pad lengths outward
(away from the package body) so each lead sits on a land with normal
toe/heel fillet allowance per IPC-7351. No change to the pitch or
pad width (which appear to match the package).

**Action:** Rev 2b mitigation — careful hand-soldering on populated
boards; not a blocker. Rev 2c spin ships with corrected footprint.
Pre-build sanity item ("H11L1SM footprint matches the populated
package") to be updated for the new land geometry on Rev 2c.

### F4 — BJT clamp symbol/footprint pin mismatch (E↔B swapped)

**Symptom (Board 1, Stage 4.1):** All four VCLAMP reference nodes
read ±0.65 V at idle instead of the expected ±1.565 V:

| Node      | Expected | Measured |
|-----------|----------|----------|
| VCLAMP_R+ | +1.565 V | +0.652 V |
| VCLAMP_R− | −1.565 V | −0.649 V |
| VCLAMP_L+ | +1.565 V | +0.677 V |
| VCLAMP_L− | −1.565 V | −0.622 V |

All four sit at ~±V_BE — a forward-biased BJT base-emitter junction
is clamping each reference to one diode drop from the signal node
(which idles near 0 V).

**Root cause:** The schematic symbol for the BJTs uses the TO-92
pin convention **1=E, 2=B, 3=C** but the assigned footprint is
**SOT-23 SMD** (MMBT3904 / MMBT3906), whose JEDEC standard pinout
is **1=B, 2=E, 3=C**. When the SOT-23 parts are populated correctly
per their package markings, physical Base and physical Emitter end
up swapped relative to schematic intent (Collector matches).

Q1 (NPN) PCB pad assignment, as a representative example:

| Pad | Schematic pinfunction | Net                 | Physical SOT-23 pin |
|-----|-----------------------|---------------------|---------------------|
| 1   | E                     | AUDIO_IN_L (signal) | **Base**            |
| 2   | B                     | −VCLAMP_L           | **Emitter**         |
| 3   | C                     | GND                 | Collector ✓         |

At idle (V_B ≈ 0 V on signal, divider tries to pull V_E to −1.565 V),
V_BE = 0 − (−1.565) = +1.565 V → BE forward-biased hard → BJT
conducts continuously → base-emitter clamps the −VCLAMP_L node up
to V_B − 0.65 V = −0.65 V. ✓ Matches bench measurement.

Same mechanism mirror-polarity for the PNPs on +VCLAMP.

**Consequences:**

- All four BJT clamps are non-functional as designed.
- Clean-signal gain sweep (4.2) is unaffected — BJTs only matter
  on overdrive.
- **Codec_max test (4.3) is unsafe to run with stock Rev 2 boards:**
  without functional clamps, the OPA1656 will rail-clip on +24 dBu
  overdrive rather than being soft-clamped to ≤4.8 V at the Seed
  pin. Could exceed the Seed's input rating.

**Resolution (Rev 2c — issue #18):** Update the footprint to JEDEC
SOT-23 (1 = B, 2 = E, 3 = C) so subsequent SOT-23 part substitutions
are electrically correct without further rework. The Sim.Pins property
on the symbol must agree with the new footprint mapping.

**Action (Board 1, this validation pass):** Dead-bug rework — Q1–Q4
package clipped, leads bent down and reconnected to the correct nets
to recover the intended pin function, then continued Stage 4.
Remaining four Rev 2b boards: weigh the dead-bug effort vs. waiting
for Rev 2c.

### F5 — +VCLAMP loaded by clip-threshold trim pot (asymmetric clamps)

**Symptom (Board 1, Stage 4.1, post-F4 dead-bug rework):**

| Node        | Stage 4.1 "expected" | Measured      |
|-------------|----------------------|---------------|
| −VCLAMP_L/R | −1.565 V             | **−1.57 V** ✓ |
| +VCLAMP_L/R | +1.565 V             | **+1.38 V** ✗ |

Both polarities behave consistently across L and R. With rails at
±12.1 V (no sag) and the BJTs correctly oriented after rework, the
+VCLAMP nodes still sit ~12 % low.

**Root cause:** The clip-threshold trim pots (RV7 channel L, RV8
channel R — both 10 kΩ) are wired as 3-terminal dividers from
+VCLAMP_x to GND, wiper feeding the LM2903 comparator's IN_THRESH_x
input. The wiper draws no current (comparator input is high-Z), so
each pot acts as a constant **10 kΩ resistor from +VCLAMP to GND** —
permanently in parallel with the 1.5 kΩ bottom resistor of the
+VCLAMP divider.

| Side | Bottom-to-GND eff.      | Divider @ ±12.1 V                    | Measured  |
|------|-------------------------|--------------------------------------|-----------|
| −    | 1.5k (no pot)           | 12.1 × 1.5 / 11.5 = **−1.578 V**     | −1.57 V ✓ |
| +    | 1.5k ∥ 10k = **1.304k** | 12.1 × 1.304 / 11.304 = **+1.396 V** | +1.38 V ✓ |

Both sides match the divider math to DMM precision.

**Consequences:**

- **Stage 4.1 +VCLAMP spec is wrong** — the original "±1.51 to ±1.62 V"
  expected window assumed no pot loading. Real +VCLAMP nominal is
  **~+1.40 V** with the trim pot population. Realistic tolerance
  window: ~+1.34 to +1.45 V (R ±1 %, pot ±5 % end-to-end,
  rail ±2 %).
- **BJT clamp thresholds become asymmetric:** positive overdrive
  clamps signal at ~+2.03 V (= +1.38 + V_BE); negative overdrive
  clamps at ~−2.22 V (= −1.57 − V_BE). ~9 % earlier clamping on
  positives.
- **Stage 4.3 (codec_max) impact:** the asymmetric clamp lowers
  the positive-peak Seed pin voltage relative to the sim, which
  used a symmetric ±1.565 V reference. Bench will confirm; needs
  measurement before settling the new spec.

**Resolution (issue #19):**

- **Rev 2c:** swap RV7/RV8 to **47 kΩ or 100 kΩ** — loading on
  +VCLAMP drops to <3 %, reaching symmetric ±1.565 V again.
  Single-part change, smallest blast radius.
- **Rev 3:** move the clip-threshold derivation to its own divider
  off +12 V so it doesn't share impedance with +VCLAMP at all.
  Cleaner — eliminates the impedance coupling between the clamp
  reference and the clip-threshold detector entirely.

**Knock-on:** once F5 is fixed, full +24 dBu calibration headroom is
restored and the output trims (RV2 / RV4) can be re-set to the
original spec rather than the F9 work-around level (~+22–23 dBu).
Stage 3.1 / 3.2 and F9 procedure notes will need updating once the
fix is in.

**Action (Rev 2b):** No hardware change on the current bench boards.
Stage 4.1's +VCLAMP tolerance documented inline with the asymmetric
reality; Stage 4.3 measured against the realistic clamp thresholds.

### F6 — Input stage rails on small input; THAT1246 SENSE topology is fragile

**Symptom (Board 1, Stage 4 input signal sweep):** With 200 mV peak
on each AD2 WaveGen channel, 180° phased (= 400 mV peak differential
= −8.7 dBu), R16 pad 1 (right-channel THAT1246 output) **and** the
OPA1656 output (IN_OPA_R) both sit at ~20 V p-p, essentially a square
wave following the input zero-crossings. Both stages railing at the
±12 V supply. Same behaviour on the left channel. Expected OPA output
for that input is ~240 mV peak (≈ −0.6× chain gain at −8.7 dBu in).

**Root cause:** Rev 2 wires the THAT1246 SENSE pin (U4 pin 5,
U5 pin 5) to the OPA1656's −IN summing junction — i.e., the OPA's
virtual ground node, on the **OPA-side** of R8 / R16. This makes a
*nested* feedback topology: THAT1246's internal output amplifier
has **no local self-feedback**, and depends on the downstream
OPA1656 loop (R9 feedback) to close the loop through R16. The
intent is "active ground sensing" — the OPA's virtual ground
becomes the THAT1246's output reference.

That topology is fragile in practice. The THAT1246's internal amp
is open-loop unless the OPA's loop is closed and stable; any
startup glitch, marginal phase margin, or upstream-induced
transient can latch the system at the rails. Both stages then
mutually saturate each other (THAT railed → R16 drives OPA −IN
hard → OPA rails → no recovery). Both channels exhibit the failure
identically because the topology is mirrored.

User also identified that on the physical PCB, the SENSE trace
visually appears to be routed to the OUTPUT side of R8 / R16 rather
than to the OPA −IN side per the schematic netlist — possible
layout error compounding the topology fragility.

**Consequences:**

- Stage 4 input path is non-functional on Rev 2 boards as built.
- Stage 4.1 (±VCLAMP) unaffected — measured with no audio drive.
- Stages 4.2–4.6 cannot run on stock Rev 2 boards without rework.

**Resolution (issue #20):**

- **Rev 2c:** drop the active-ground-sense topology. Tie SENSE
  directly to OUTPUT at the THAT1246. OPA1656 becomes a conventional
  downstream inverting gain stage with self-contained R9 / R16
  feedback. Two independently stable stages, no nested loop. REF /
  pin 1 stays at AGND. Update both schematic and PCB.
- **Rev 3:** keep the active-ground-sense concept correctly. Move R16
  close to the OPA1656 and run the SENSE trace **back to the
  THAT1246 from the load-side of R16** (sensing across the board
  rather than at the OPA virtual ground). Recovers the original
  remote-ground-referenced sensing intent without the nested-loop
  instability.

**Action (Board 1, this validation pass):** Rework on each THAT1246
— cut the SENSE trace from its current destination, short-jumper
**U4 pin 5 → U4 pin 6** and **U5 pin 5 → U5 pin 6** (SENSE tied
directly to OUTPUT at the chip — equivalent to the Rev 2c fix). The
OPA −IN node is left fed only by R16 (input) and R9 (feedback) as a
normal inverting amp. Sanity check: −8.7 dBu diff input should give
a clean ~240 mV-peak sine at the OPA output, not a railed square.

### F7 — Input-stage THD floor on Board 1 limited by AD2 measurement rig

**Symptom (Board 1, post-F6 rework, daughterboard disconnected):**
Spectrum-based THD measurement on AD2 at the OPA1656 output
(IN_OPA_R), 997 Hz balanced test tone via WaveGen (5 V amplitude
per leg, 180° phased), 32-average RMS, Flat Top window.

| Drive level (per leg) | Diff input | THD measured     |
|-----------------------|------------|------------------|
| Shorted (no signal)   | —          | **−62.0268 dBc** |
| 2 V p-p (≈ +5 dBu)    | 4 V p-p    | **−62.0268 dBc** |
| 18 V p-p (≈ +23 dBu)  | 36 V p-p   | −56.77 dBc       |
| 19 V p-p (≈ +24 dBu)  | 38 V p-p   | **−57.43 dBc**   |
| 20 V p-p (≈ +25 dBu)  | 40 V p-p   | −57.20 dBc       |

**Analysis:**

- The shorted-input reading (−62.0268 dBc) is bit-identical to the
  +5 dBu reading. That confirms the THD measurement is hitting an
  instrument-side noise floor at exactly **−62 dBc**, not measuring
  the chain's actual harmonic content at low drive.
- The 18–20 V readings sit ~5 dB above the floor and *do* track
  with input level, so the ~−57 dBc figure represents real
  soft-clip distortion, though the absolute value may be 1–3 dB
  understated by floor contribution.
- Soft-clip onset around **18–19 V p-p per leg (≈ +23–24 dBu
  balanced)** — consistent with OPA1656 rail behaviour on ±12 V
  under light load. Above 20 V the OPA enters fully developed
  soft-clip; THD plateaus rather than climbing further because the
  chip rail-pins symmetrically.
- The original "3–9 kHz bump" observed on the scope FFT when
  stepping 19 → 20 V is the 3rd / 5th / 7th / 9th odd harmonics of
  997 Hz — exactly the spectral signature of symmetric soft-clip.

**Consequences:**

- **Input section's small-signal THD is below the −62 dBc AD2
  measurement floor.** Datasheet-consistent estimate is
  ~−95 to −100 dBc at +5 dBu, but un-measurable on this rig.
- For Stage 4.2 (clean-signal gain sweep at +4 / +14 dBu) the
  chain is qualitatively confirmed clean — no audible or
  measurable distortion until soft-clip onset above +20 dBu.
- For Stage 4.3 (codec_max at +24 dBu) the OPA is already at the
  edge of soft-clip, and the BJT clamps downstream of the pot will
  dominate the final waveform at the Seed pin (per F4 / F5
  analysis).

**Resolution:** No hardware change needed; this is a measurement-
rig limitation, not a DUT issue. For any future spec-sheet-grade
THD numbers (e.g., Rev 3 marketing claims), characterize with a
real audio analyzer — Cosmos APU, RME ADI-2 Pro, MOTU M2/M4 +
loopback, or Audio Precision. Typical floors ~−110 to −130 dBc,
plenty of headroom to resolve the chain's actual distortion.

**Action:** None on Rev 2. Document the AD2 measurement floor as a
known limitation of this validation pass. When a better audio
analyzer becomes available, re-run +5 dBu and +14 dBu THD to fill
in the dynamic range and confirm the chain's actual clean-signal
floor.

**RESOLVED (post-F9 procedure, Board 1 loopback at digital full scale,
1007.8125 Hz coherent FFT via `firmware/projects/thd-meter`):**
**THD ≤ −88 dB (≤ 0.004 %)** on both channels after the loopback-THD
re-trim. That's 34 dB cleaner than the AD2's −62 dBc ceiling that
originally flagged this finding, and within ~5–10 dB of the PCM3060
codec's own datasheet floor — the practical ceiling for this analog
chain. Measurement covers the full round trip
(OPA1656 out + THAT1646 + balanced loopback + THAT1246 + OPA1656 in
+ BJT clamp + codec ADC); the dominant remaining contribution is the
input/output OPA at high swing plus the codec itself. Result is well
below any plausible audibility threshold for music material; at normal
operating level (~−20 dBFS) the chain should land another 10–15 dB
lower until the noise floor dominates. **Finding closed.** Re-run on
other boards as they're populated, alongside the F9-spec retrim.

### F8 — RV7 / RV8 clip-threshold trim pots placed on swapped sides

**Symptom (Board 1, Stage 4.6 trim prep):** The clip-threshold
trim pots **RV7 (channel L)** and **RV8 (channel R)** are
positioned on the PCB on the opposite physical sides from their
respective channel sections — i.e., RV7 sits on the right-channel
side of the board layout and RV8 on the left side, mirrored
relative to the channel groupings of the rest of the input stage.

**Consequences:** No electrical issue — just an ergonomic /
build-error trap. During trim it's easy to adjust the wrong
channel without realizing it, and during board population it
invites mis-stuffing. Compounds with F2 (GPIO header position)
as a class of layout-usability fixes due in Rev 3.

**Resolution (Rev 3 — issue #21):** Re-place RV7 and RV8 in the PCB
layout so each sits adjacent to its respective channel's BJT clamp /
op-amp group. No schematic change required. Combine with the F10
silkscreen-labelling improvements while the layout is open.

**Action:** None on Rev 2b boards. Mark the silkscreen with hand
labels if doing further trim work; deferred to Rev 3.

### F9 — Broadband H4..H9 fanout is the most sensitive distortion indicator; calibrate output trims via loopback-THD, not scope p-p

**Symptom (Board 1, Stage 3.1/3.2 post-trim, Stage 4 loopback investigation):**
The "by-ear" scope p-p trim landed both output channels at the BJT
clamp graze threshold (per F5's depressed +VCLAMP), with R sitting
~0.8 dB hotter than L. At digital full-scale loopback drive, R
produced a clear H4–H9 fanout in the on-Seed FFT (15–35 dB above
noise floor), while L stayed clean. Reducing the R feedback trim
0.1 dB at a time showed the transition is a **hard threshold** — fanout
either fully off (H4–H9 in noise floor) or fully on. Pushing L by the
same 0.1 dB across its threshold produced an identical fanout on L.

**Analysis:** Two compounding facts make the broadband-fanout view
uniquely useful:

1. **The clamp engagement is a hard knee.** The BJT clamp is not a
   smooth limiter — once a peak crosses +VCLAMP + V_BE the BJT
   conducts and pins that peak. The result is a sharp transfer-curve
   kink that generates broadband mid-to-high-order harmonics (H4..H9)
   without proportional growth in H2/H3. Below threshold the chain is
   smooth; above, it's sharply clipping. Sub-1 dB of trim flips the
   chain between regimes.
2. **Scalar THD barely moves.** Because H2/H3 dominate the THD sum and
   they stay roughly constant across the threshold, the THD figure
   shifts only ~1–2 dB. H4..H9 individually shift 15–35 dB. Looking at
   THD alone you'd think nothing happened; looking at the harmonic
   spectrum you see the regime change immediately.

Scope p-p trim was insufficient even at +24 dBu calibration:

- Scope p-p reading jittered in the mV range → can't distinguish
  ±0.5 dB by eye.
- Scope shape inspection at the XLR output showed no flat-tops or
  visible distortion — because the distortion source (BJT clamp
  graze) is downstream of the XLR output, at the codec input pin.

**Procedure that worked (now adopted in 3.1/3.2 and 4.6):**

1. Loopback mode, drive 1.0 (digital full scale), coherent FFT
   at 1007.8125 Hz.
2. Watch H4..H9 in the harmonic table (and the lighter overlay traces
   on the THD-history sparkline — H4..H9 ride at the noise floor when
   clean, lift above when distorting).
3. Trim the channel until H4..H9 just return to the noise floor.
4. Back off ~0.5 dB for tolerance margin.
5. Repeat for the other channel, matching the codec-input level at
   the final lock within ~0.1 dB.

**Consequences:**

- Stage 3.1/3.2 procedures updated to use the loopback-THD method as
  the preferred path. Scope p-p stays in the procedure as a sanity
  cross-check (gives the "what's my actual +dBu number" answer).
- Stage 4.6 (clip-LED trim) updated to set the LED firing point at
  the same threshold the THD analyzer identifies — the clip LED
  becomes a direct visual indicator of "you're about to make broadband
  distortion".
- Calibrated full-scale output drops from +24 dBu (which was at the
  clamp edge with zero margin) to roughly +22 to +23 dBu, depending on
  margin choice. Worth quoting the actual measured number on the
  calibration sticker rather than the spec target.

**Resolution:** Procedural improvement, no schematic change. Captured
in 3.1/3.2/4.6 above.

**Action:** Re-trim all five boards using the new procedure once
populated. Record locked codec-input-level value per channel for QA
records.

### F10 — Silkscreen labelling improvements

**Symptom (recurring across F2, F8, F9 and the RV2 / RV4 output-trim
confusion that bit the first Stage 3.1 trim pass):** Several
layout-usability traps trace back to ambiguous silkscreen. Operators
have to consult the schematic to distinguish L vs R trims, identify
connector roles (In / Out / Thru), or locate the correct
clip-threshold pot for the channel under test. Each instance is
small, but they compound during build, trim, and field service.

**Resolution (issue #24):** Add explicit silkscreen labelling on the
PCB for:

- **Audio jacks:** "Input-Left", "Input-Right", "Output-Left",
  "Output-Right" near each Neutrik combo.
- **MIDI jacks:** "In", "Out", "Thru" near each DIN-5.
- **Clip-threshold trims:** "Clip Trim Left" / "Clip Trim Right"
  alongside RV7 / RV8 (combine with the F8 re-placement so labels
  and physical sides agree).
- **Output-feedback trims:** "Output Trim Left" / "Output Trim Right"
  alongside RV2 / RV4 (prevents the L/R-confusion class of bug that
  surfaced during the F9 calibration work).

**Action:** Land in Rev 2c silk if the spin happens before Rev 3, or
combine with the broader Rev 3 layout pass. No schematic change. No
electrical impact.

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
