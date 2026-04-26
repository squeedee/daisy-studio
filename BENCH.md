# Rev 2 Bench Validation Plan

Sourced from `rev2.md`. Line refs point to the source spec.

## Pre-order checks

- [ ] **H11L1SM footprint** — visual check against ON Semi datasheet (pad pitch, size, land length) before board order. (`rev2.md:804`)
- [ ] **R_fb sim verify** *(conditional)* — only if Part 1 bench item 2 shows premature rail clipping at +24 dBu: re-sim with R_fb = 11 kΩ (gain 1.1×, +0.8 dB, ~1.4 V margin) before committing PCB change. (`rev2.md:260`)

---

## Pre-PCB design validation (breadboard)

Three new design elements warrant breadboard-proving *before* committing the Rev 2 PCB. In priority order:

### A. BJT clamp + OPA1656 input stage (highest risk reduction)

Sim-only so far. The 2N3904/2N3906 complementary clamp against ±1.565 V references with the OPA1656 driving 3.3 kΩ → Seed_In is the most novel block. Bench-proving clamp action, soft knee, and op-amp recovery before PCB order de-risks Issue #1 of Rev 2.

What to verify on breadboard:
- Clamp action: drive 0 → ±12 V at the op-amp output, scope the clamp node — verify ≤ 4.8 V codec_max.
- THD at +4 dBu nominal (sim says 0.05% at -1 dBFS).
- Op-amp recovery from overdrive (no latch-up, no rail-stick).

### B. C_fb spectral check vs. live PCM3060 (Seed Rev 7)

This is the Part 3 question, and you don't need a Rev 2 PCB to answer it. Tap a Seed Rev 7's I²S DAC analog output, run it through a breadboard OPA1656 + R_fb_fixed/trim + swap-able C_fb, into the AD2 spectrum analyzer. Same answer as Part 3.3, no PCB risk.

### C. TMR 3-1222 ripple + load (optional but cheap)

Module is an SIP-8 brick — wire ±IN to a 12 V supply, ±OUT through L1/L2 ferrites + bulk caps, scope ripple under a 25 mA/rail load. Validates that the 3 W module + ferrite filtering actually meets the < 10 mVpp audio-band ripple target before the PCB locks in placement.

### D. LM2903 clip indicator (low risk, do if convenient)

Simple comparator + trim pot + LED — works on breadboard against the ±12 V rail. Mostly a sanity check that the 0–1.565 V trim range gives sensible LED behaviour.

---

## Buy list — pre-PCB validation

Cross-referenced against `~/inventory.csv` (35 lines, current as of 2026-04-25). Quantities are bench-experiment counts, not PCB BOM.

### A. BJT clamp prototype

| Need | Have? | Buy |
|------|-------|-----|
| 2N3904 NPN, TO-92 (breadboard-friendly) | no | ×10 — also fine in SOT-23 if you have adapters |
| 2N3906 PNP, TO-92 | no | ×10 |
| 12 kΩ 0805 1% (R_fb) | no (have 13k3, 13k7, 10k) | ×20 |
| 3.3 kΩ 0805 1% (R_out) | no | ×20 |
| 1.5 kΩ 0805 1% (divider lower leg for ±1.565 V ref) | no | ×20 |
| 47 µF 1210 X7R ≥ 25 V (ref-rail filter) | no (the 22 µF is 10 V only — unusable here) | ×10 |
| 1 nF C0G 0603 (C_aa + supply VHF decouple) | no | ×20 |
| 10 kΩ 0805 1% (R_in, divider upper leg) | yes ×19 | — |
| OPA1656 SOIC-8 | yes ×11 | — |
| 1 kΩ THT (LED current limit) | yes ×25 | — |
| SOIC-8 → DIP-8 adapter PCBs | no | ×5 (for OPA1656 / LM2903 on breadboard) |

### B. C_fb spectral check

| Need | Have? | Buy |
|------|-------|-----|
| 100 pF C0G 0603 | no (have 75 pF — close, but not what the design specifies) | ×10 |
| 47 pF C0G 0603 (sweep table) | no | ×5 |
| 220 pF C0G 0603 (sweep table) | no | ×5 |
| 470 pF C0G 0603 (sweep table) | no | ×5 |
| 15 kΩ 0805 1% (R_fb_fixed, output stage) | no | ×10 |
| 2.2 kΩ 0805 1% (R_in, output stage) | no | ×10 |
| 10 kΩ multi-turn cermet trim, e.g. Bourns 3296W-1-103 (R_fb_trim) | no | ×4 (also covers D below + Part 1.3 clip-threshold) |
| OPA1656 SOIC-8 | yes ✓ | — |
| Seed Rev 7 DUT | (verify on hand) | — |

### C. TMR 3-1222 power-supply prototype

| Need | Have? | Buy |
|------|-------|-----|
| TMR 3-1222 SIP-8 isolated DC/DC | no | ×2 (one bench, one production unit) |
| BLM18PG121SN1 ferrite, 0603 | yes ×2 (exact qty — fine for one prototype) | optionally ×4 more for spares |
| 22 µF 1206 25 V X7R (C6, C7 — replacing the 10 V parts) | no (current 22 µF stock is 10 V — explicitly flagged in inventory note) | ×10 |
| 100 nF, 10 µF, 100 µF caps | yes ✓ | — |

### D. LM2903 clip indicator

| Need | Have? | Buy |
|------|-------|-----|
| LM2903 dual comparator, DIP-8 (breadboard) + SOIC-8 (PCB) | no | ×3 DIP, ×3 SOIC |
| 10 kΩ multi-turn trim pot | (covered by row above in B) | — |
| Generic 3 mm or 5 mm LED (red, low-Vf) | (verify on hand) | ×10 if not |

### Summary — single Mouser cart

The minimum to unlock all four pre-PCB experiments:

- **Active:** 2N3904 ×10, 2N3906 ×10, LM2903 DIP ×3, LM2903 SOIC ×3, TMR 3-1222 ×2
- **Resistors (0805 1%):** 12 k ×20, 3.3 k ×20, 1.5 k ×20, 15 k ×10, 2.2 k ×10
- **Capacitors:** 47 µF 1210 X7R 25 V ×10, 22 µF 1206 X7R 25 V ×10, 1 nF C0G 0603 ×20, 100 pF C0G 0603 ×10, 47 pF / 220 pF / 470 pF C0G 0603 ×5 each
- **Mechanical/other:** 10 kΩ multi-turn trim pot (Bourns 3296W-1-103) ×4, SOIC-8→DIP-8 adapter PCBs ×5, LEDs ×10 (if needed)

This buy unblocks experiments A–D. None of these parts are wasted if the experiments succeed — they all reappear in the Rev 2 PCB BOM (so quantities should round up toward final-board counts × 2 for spares if budget allows).

### Deferred until PCB order

These are PCB-only parts; no breadboard validation possible, so order alongside the Rev 2 PCBs once experiments above pass:

- THAT1246 (input receiver), THAT1646 (output driver) — dedicated balanced-line ICs, not breadboard-friendly
- TPS54302 buck — high-frequency switching, requires PCB-quality layout
- H11L1SM (after footprint verification, item in pre-order checks)
- SMAJ5.0A TVS, SMBJ15A TVS (have ×3 already — good for first build)
- JST B2P-VH + VHR-2N + SVH-21T-P1.1 contacts
- 10 kΩ log-taper audio pots ×4 (input + output, both channels)
- DIN-5 jacks (have ×0 — order with PCBs)

---

## Part 1 — Input stage (post-board)

`rev2.md:737-747`

- [ ] **1.1 Gain sweep.** +4 dBu / +14 dBu / +24 dBu at THAT1246; scope codec-pin voltage across pot travel; compare to Performance Summary table.
- [ ] **1.2 Pathological overdrive.** +24 dBu, pot CW, across a handful of boards — verify codec_max ≤ 4.8 V.
- [ ] **1.3 Clip-LED behaviour.** Threshold pot at mid-travel — confirm off below threshold, proportional glow above.
- [ ] **1.4 Noise floor.** Audio-band noise at Seed_In with input shorted; compare to sim's 1.4 µV rms output-noise estimate.

## Part 2 — MIDI (post-board)

`rev2.md:806-807`

- [ ] **2.1 MIDI loopback.** IN → THRU, OUT → external synth, 31.25 kbaud.

## Part 3 — Output stage (post-board, Seed Rev 7)

`rev2.md:941-957`. Largest open item — sim cannot predict whether 1-pole @ 80 kHz is enough against the actual PCM3060 noise spectrum.

- [ ] **3.1 Baseline noise (no C_fb).** Seed Rev 7 playing digital silence; capture XLR differential output noise with C_fb unpopulated.
- [ ] **3.2 Filtered noise (100 pF C_fb).** Repeat 3.1 with C_fb = 100 pF populated.
- [ ] **3.3 Compare.** Broadband floor + spectral content using 192 kHz ADC+FFT or scope FFT; look for residual content >40 kHz.
- [ ] **3.4 Escalation decision.** If 1-pole @ 80 kHz insufficient → escalate to 2-pole Sallen-Key post-gain-stage (do **not** increase C_fb — kills audio top octave).

## Part 4 — Power (post-board)

`rev2.md:1450-1463`

- [ ] **4.1 ±12V under idle load.** Measure at op-amp supply pins under nominal Seed idle.
- [ ] **4.2 ±12V under full drive.** Input +24 dBu, output 24 Vpp diff — measure at op-amp supply pins.
- [ ] **4.3 ±12V ripple.** Scope at op-amp supply pins; verify < 10 mVpp in audio band.
- [ ] **4.4 25 mA/rail load test.** At ±12V rail caps; rails stay within TMR 3-1222 ±2%. Defensive margin check (daughterboard/J2 don't carry ±12V).
- [ ] **4.5 Power switch header.** Shunt populated → on; removed → off.
- [ ] **4.6 Reverse-polarity.** 12 V wall wart reversed — Q1 blocks, no rail activity.

---

## Equipment / setup notes

- Signal source: balanced output capable of +4 / +14 / +24 dBu (or attenuated bench gen).
- Capture: Digilent **Analog Discovery 2** (AD9648, 14-bit, 100 MSPS dual). WaveForms Spectrum Analyzer with averaging covers Parts 1, 2, 4 fully. See Part 3 caveat below.
- Loads: 25 mA/rail dummy load for Part 4.4.
- Reference DUT: Seed Rev 7 (Part 3 specifically requires Rev 7 — PCM3060 codec is the noise source under test).

### AD2 / AD9648 capability for Part 3

What the AD2 *can* do:
- **Out-of-band hash detection** (the actual Part 3 question — "is there sigma-delta noise above 40 kHz?"). At 1 MS/s sample rate you have 500 kHz Nyquist, plenty for spotting PCM3060 noise-shaping bumps. Codec ultrasonic content unfiltered is typically tens of mV, well above AD2's ~1–2 mV self-noise on ±5 V range.
- **Spectral comparison** before/after C_fb populate — *relative* delta in the >40 kHz region is what 3.3 actually asks for, and that's well within AD2 reach.

What the AD2 *cannot* do:
- **Absolute audio-band noise-floor measurement.** AD2 front-end self-noise (~1–2 mV RMS) sits ~40 dB above the codec's actual audio-band floor (~10–15 µV). You will measure the AD2, not the codec.
- This means you can't directly verify the audible delta from C_fb on the AD2. If the spectrum check (3.3) shows the 1-pole is sufficient out-of-band, you're done. If it's marginal and you need the audio-band confirmation, you'd need a real audio interface (see "Order LATER" — only if needed).

---

## Order plan

### Order NOW (needed for first bench pass)

Things blocking the moment Rev 2 boards arrive:

- [ ] **Rev 2 PCBs** — multiple units (≥3) so item 1.2 (codec_max across boards) is meaningful.
- [ ] **Rev 2 BOM** — full kit per `rev2.md` Components lists across all 4 parts. Notably:
  - TMR 3-1222 (Part 4)
  - 22 µF 1206 25 V X7R (C6, C7)
  - JST B2P-VH + VHR-2N + SVH-21T-P1.1 contacts (power switch + shunt harness)
  - H11L1SM (with vetted footprint!)
  - SMAJ5.0A TVS (optional, recommended)
- [ ] **Seed Rev 7** — required for Part 3; also fine for Parts 1/2/4. If you only have one DUT generation, this is the priority.
- [ ] **C_fb candidates** — 0402 or 0603 C0G/NP0, 100 pF (handful). Also worth stocking 47 pF / 220 pF / 470 pF in the same package for the escalation table sweep if Part 3.4 fires.
- [ ] **MIDI loopback gear** — external synth or USB-MIDI interface + 2× DIN-5 MIDI cables (Part 2).
- [ ] **±12V dummy load resistors** — ~480 Ω, ≥1 W (gives ~25 mA at 12 V) ×2 for Part 4.4. Or a programmable bench load if you have one.
- [ ] **Spare 12 V barrel-jack wall wart** — for the reverse-polarity test (4.6); use one you don't mind sacrificing or wire a reverse-polarity adapter cable.

### Order LATER (conditional / escalation only)

Don't buy these up front — wait for bench data to confirm need:

- [ ] **Audio-grade interface (192 kHz, low self-noise)** *(only if Part 3.3 spectral check is inconclusive and you need audio-band floor confirmation)*. The AD2 handles the >40 kHz hash question; an audio interface is only needed if you have to prove the audible C_fb delta. Candidates: MOTU M2/M4, RME Babyface, Cosmos APU. Skip unless escalated.
- [ ] **2-pole Sallen-Key escalation parts** *(only if Part 3.4 fires)* — extra OPA1656 + matched R/C set for a post-gain-stage filter. Hold off until 3.3 says the 1-pole is insufficient; this is a board-revision-scale change, not a populate-option.
- [ ] **R_fb = 11 kΩ 0805** *(only if Part 1.2 shows rail clipping)* — single value swap; trivially substitutable, don't pre-order unless you want it on hand.

### Already on hand (verify before bench day)

- [ ] Digilent Analog Discovery 2 (scope + spectrum analyzer + arb gen — covers most of the bench)
- [ ] Balanced signal source (+24 dBu capable) — or use AD2 WaveGen + balanced driver
- [ ] Multimeter
- [ ] Soldering iron / hot air for C_fb populate-depop cycle
