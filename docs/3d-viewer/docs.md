# Daisy Studio

<p style="color: var(--muted); margin-top: 0;">Development board for the Electrosmith Daisy Seed — balanced studio I/O, MIDI, and ±12 V analog rails. Click a <span class="view-btn" style="cursor:default">section</span> tag to focus the 3D model on that part of the board.</p>

<div class="quickbar">
[[view:overview|Overview]]
[[view:audio-input|Input]]
[[view:audio-output|Output]]
[[view:midi|MIDI]]
[[view:power|Power]]
[[view:seed|Seed]]
[[view:daughter-header|Daughter]]
[[view:back|Back]]
</div>

---

## Audio Input [[view:audio-input]]

```
Balanced in → THAT1246 → OPA1656 (fixed gain) → daughterboard pot
                                                       ↓
   Daisy Seed ← C_aa anti-alias ← BJT clamp ← R_out (3.3 kΩ) ←
```

The **THAT1246** balanced receiver converts the differential XLR input to single-ended at −6 dB, keeping +24 dBu peaks within the ±10 V output swing of the ±12 V rails. Its **Sense pin (5)** is brought back as a separate trace to the OPA1656 inverting node — Kelvin-connected past the input resistor — so the THAT1246's internal feedback amp absorbs any voltage drop across `R_in`, eliminating it as a gain-error term.

The **OPA1656** runs as an inverting amplifier at a **fixed gain of 1.2×** (R_fb = 12 kΩ, R_in = 10 kΩ). At +24 dBu peak input the op-amp output reaches ±10.45 V, ~550 mV from the ±11 V clip rails. Fixed gain (rather than a pot in the feedback path) keeps loop phase margin constant across user level adjustments, and the high-impedance summing junction stays entirely on the main PCB.

User level is set by a **10 kΩ log pot on the daughterboard**, wired as a passive three-terminal voltage divider downstream of the op-amp. Both header legs are low-impedance: the op-amp drives the CW terminal, and the pot wiper returns to the main PCB into `R_out` (3.3 kΩ) which caps fault current into the clamp under pathological overdrive.

The **BJT clamp** is the design's centrepiece. A complementary pair (2N3906 PNP + 2N3904 NPN) per channel clamps the Seed input pin against ±1.565 V references derived from the ±12 V rails by 10 kΩ / 1.5 kΩ dividers and held stiff at audio frequencies by 47 µF MLCCs. The transistors' β ≈ 200 means only Ic / β flows through the reference divider base connection, so the references stay nearly stationary even under sustained overdrive — the "reference pumping" failure mode that limits passive diode clamps. The sharp emitter-base knee (NF ≈ 1.24, versus ~1.82 for diodes) lets the clean signal use the full ADC range with no distortion.

A **1 nF C0G capacitor** at the Seed input pin, after the clamp, forms a single-pole LPF with `R_out` plus the pot wiper source impedance. The corner stays between 27 kHz (pot mid) and 48 kHz (pot ends), well above the audio band, attenuating wideband op-amp noise and out-of-band content before it reaches the PCM3060's sigma-delta ADC.

A **clip indicator** uses an LM2903 comparator monitoring the Seed input against an adjustable threshold. A trim pot on the daughterboard (0 V to +1.565 V) sets the threshold; the open-collector output sinks an LED current path against +12 V through a 1 kΩ limit on the main PCB. At audio frequencies the LED flickers faster than the eye sees — a dim glow at light clipping, bright at heavy. A single LM2903 covers both channels.

## MIDI [[view:midi]]

Standard MIDI 1.0 — a 5 mA current loop at 31.25 kbaud on three SDS-50J DIN-5 jacks (IN, OUT, THRU).

```
DIN-5 IN ── 220R × 2 ── 1N4148W ── H11L1SM (opto, Schmitt)
                                       ├── 270R pull-up to +3V3D
                                       ├── → MIDI_RX → Seed UART RX
                                       └── 33R × 2 → DIN-5 THRU

Seed UART TX ── MIDI_TX ── 33R + 10R ── DIN-5 OUT
```

The H11L1SM Schmitt-trigger optocoupler galvanically isolates the input per the MIDI 1.0 electrical spec and presents clean UART edges to the Seed. THRU buffers the same opto output through a second pair of 33 Ω series resistors. OUT is driven directly from the Seed UART TX through a 33 Ω + 10 Ω series pair.

## Audio Output [[view:audio-output]]

```
Seed audio → OPA1656 (gain ~9.1×, C_fb LPF) → daughterboard pot
                                                       ↓
        XLR ← SM4004 phantom clamps ← THAT1646 balanced driver ←
```

The Seed's PCM3060 outputs ~2 V p-p at digital full scale (~−1 dBu single-ended, ~+5 dBu differential through the THAT1646 alone). An OPA1656 inverting gain stage closes the ~20 dB gap to the +24 dBu studio peak target. R_in is a fixed 2.2 kΩ; R_fb is **15 kΩ fixed in series with a 10 kΩ multi-turn cermet trimmer** (e.g. Bourns 3296W-1-103). Mid-trim lands at gain ~9.1× (+23.7 dBu peak); the 25-turn trim resolves to ~0.5% of R_fb. The fixed floor prevents accidental hard clipping if the wiper loses contact, and the ceiling (R_fb ≤ 25 kΩ) stays below the OPA1656's onset of clipping.

A **100 pF C0G across R_fb** turns the gain stage into a single-pole LPF with f_c ≈ 80 kHz at nominal trim. The Seed Rev 7's PCM3060 has out-of-band delta-sigma noise that the codec's internal RC alone does not adequately attenuate; the in-feedback-loop LPF handles this without adding any series parts. C0G dielectric is required — X5R/X7R have voltage-coefficient distortion that would intrude into the audio band when the cap is in the feedback path. Sim shows −0.27 dB at 20 kHz, −22 dB at 1 MHz.

User output level is a **10 kΩ log pot per channel on the daughterboard**, voltage-divider-wired downstream of the op-amp. Two separate pots (not ganged) let users pick their own taper or matching strategy. The THAT1646's high-Z input means the op-amp sees a constant 10 kΩ load regardless of wiper position.

The **THAT1646** balanced driver converts the single-ended pot wiper back to a differential XLR pair. Sense pins close the feedback loop at the XLR connector for cross-coupled output impedance and immunity to load imbalance.

**Phantom-power protection**: four SM4004 diodes per channel (two per XLR pin) clamp the THAT1646 output to the ±12 V rails. If an XLR is plugged into a phantom-enabled mic preamp, +48 V through the preamp's 6.8 kΩ feed produces ~5 mA per pin into the clamp — well within the SM4004's 1 A rating.

**Rail protection** (phantom back-feed when the gear is powered off): one SMBJ15CA bidirectional TVS on each ±12 V rail to AGND, placed near the RS3-1212D output. Same part as the input over-voltage TVS for BOM consolidation. Clamps when the rail magnitude exceeds ~16 V.

## Daughterboard Header [[view:daughter-header]]

The main PCB commits to a **2×10 (20-pin) 2.54 mm pitch through-hole footprint** for the daughterboard header. Daughterboard PCBs are **fully passive**, populating only:

- 2× input level pots (10 kΩ log)
- 2× output level pots (10 kΩ log)
- 2× clip LEDs

No ICs, no power rails, and no high-impedance feedback nodes cross the header — shorting any two daughterboard signals together cannot damage the main PCB. The 18 needed signal pins fit in the 20-pin footprint with two AGND pins at the bottom; AGND is interleaved on every audio pair.

## Daisy Seed &amp; GPIO Breakout [[view:seed]]

A **2×14 (28-pin) 2.54 mm vertical pin header** brings out every Seed GPIO not committed to the on-board audio (ADC/DAC), MIDI (UART_RX/TX), or USB (D+/D−, VBUS) — plus +5 V, +3V3D, and DGND for downstream circuits. Pin-to-net assignment is slightly illogical, as they were selected to minimise via count and trace crossings between the Seed and the breakout.

Analog ±12 V rails are not on the breakout (or on the daughterboard header); they distribute through the dedicated power header.

## Power [[view:power]]

```
12 V barrel jack → SW1 (panel switch / shunt) → DMP3056L (rev-polarity)
                                                       ↓
                                              SMBJ15CA TVS (overvoltage)
                                                       ↓
                                                100 µF bulk → +12V_RAW
                                                       ├─→ TPS54302 → +5V
                                                       └─→ RS3-1212D → ±12V
```

A 12 V wall-wart feeds a 2.1 mm barrel jack. **SW1** — a JST B2P-VH 2-pin THT header in series after the jack — takes either a pre-crimped shunt harness (default, bypasses the switch) or an external panel switch harness. Placing the switch *before* reverse-polarity protection means rev-pol and TVS clamping still function during a miswired wall-wart event regardless of switch state.

Reverse polarity is blocked by a **DMP3056L-13** P-FET (VGS_max ±20 V, RDS_on ~51 mΩ). An **SMBJ15CA** bidirectional TVS clamps any over-voltage spike from a misbehaved supply. A 100 µF / 25 V electrolytic provides bulk on +12V_RAW.

The **TPS54302 buck** (SOT-23-6) generates +5 V from +12V_RAW for the Daisy Seed and the MIDI front-end. A dedicated **10 µF / 25 V X7R 1206** input MLCC sits at the VIN pin to handle the buck's pulsed input current at 500 kHz with low loop inductance. A defensive **SMAJ5.0A** TVS clamps +5 V to GND near the Seed.

The **Recom RS3-1212D** isolated DC/DC (SIP-8, 3 W, regulated ±2%, ±125 mA per rail) generates the ±12 V analog rails. The output passes through 2× BLM18PG121SN1 ferrite beads into the rest of the board.

---

<p style="color: var(--muted); font-size: 12px;">
Source: <code>daisy-studio.kicad_pcb</code> · GLB exported with
<code>kicad-cli pcb export glb</code> · Viewer:
<a href="https://modelviewer.dev/" target="_blank" rel="noopener">&lt;model-viewer&gt;</a>
</p>
