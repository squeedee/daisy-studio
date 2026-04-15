# Part 0: General changes in design

* Annotate all components in the schematic with ideal placement notes - make a property for them called
  `ideal-placement`.
* Add some details about the project to the
  silkscreen. [Github Issue](https://github.com/squeedee/daisy-studio/issues/4)
* GPIO component is wrong [Github Issue](https://github.com/squeedee/daisy-studio/issues/3)

# Part 1: Op-Amp Gain-Staged Audio Input

## Design Objectives

1. Maximise ADC headroom at +4 dBu (standard studio operating level).
2. Continuous trim from +4 dBu to +24 dBu via a single pot per channel.
3. Protect the PCM3060 codec. This design is only validated for Rev7 Seeds with the PCM3060 and input schematic as
   published [here](https://daisy.nyc3.cdn.digitaloceanspaces.com/products/seed/ES_Daisy_Seed_Rev7.pdf)

## Codec Voltage Budget

The PCM3060 codec on the Daisy Seed has an internal AC coupling capacitor and a 2.5V
V_COM bias. All voltages below are measured at the codec (after AC coupling and bias),
establishing three operating zones:

| Zone   | Target range V(codec)                               | Sim range V(codec)                           | Seed pin equivalent | Design intent                                                             |
|--------|-----------------------------------------------------|----------------------------------------------|---------------------|---------------------------------------------------------------------------|
| Signal | 1.0V to 4.0V (3V p-p nom)                           | 1.17V to 3.84V (2.66V p-p)                   | ±1.82V              | Full ADC utilisation. No BJT conduction.                                  |
| Clamp  | 4.0V to 4.5V                                        | 3.84V to 4.50V                               | ±1.82V to ±2.73V    | Progressive BJT conduction limits overdrive. Keep this as low as possible |
| Damage | -0.3V to +4.8V (Vcc + 0.3V = 4.8V, LDO Vcc is 4.5V) | Not reached (worst case 4.50V, 300mV margin) | > ±2.8V             | Must never be reached.                                                    |

Design goals:

1. The 3V p-p full-scale signal must remain entirely below the clamp circuit’s
   start-of-knee — zero clamp conduction at nominal operating level.
2. The hard clamp (full clamp conduction under fault current) targets 4.5V at the
   codec, providing maximum overdrive margin above 3V p-p without approaching the
   absolute maximum rating.
3. The gape between the top of the "Clamp" zone and the "Damage" zone should be maximised without encroaching on the
   Signal Zone

> TODO: Validate component tolerance ranges to ensure whatever we select does not encrouch on Signal, while staying
> as far from Damage as possible.

## Signal Path

```
Balanced in → THAT 1246 (-6dB) → R_in (10kΩ) → OPA1656 (inverting, ±12V) → R_out (2.2kΩ) → BJT clamp → Seed pin
                                                       ↑                                         │
                                                 25kΩ pot (R_fb)                              LED (clip)
```

The THAT 1246 converts the balanced input to single-ended with -6dB of gain, preserving
common-mode rejection and keeping +24 dBu signals (±8.7V peak at the output) within the
±10V output swing of the ±12V rails.

The OPA1656 is configured as an inverting amplifier with gain set by the ratio of the
feedback pot to the input resistor (gain = -R_fb / R_in).

Todo: calculate reasonable pot values for the stated design objectives for input loudness.

The signal remains centred at 0V throughout. The Daisy Seed’s internal AC coupling
capacitor and V_COM bias (2.5V) handle the DC offset for the PCM3060 ADC; no external
bias network is required.

## Op-Amp Selection: OPA1656

The OPA1656 (TI, dual, SOIC-8) is selected for low voltage noise (4.3 nV/√Hz at 1kHz),
low distortion (THD+N 0.000029% at 1kHz), and 53 MHz GBW — comfortably exceeding audio
bandwidth requirements at the target gain range. Supply range extends to ±18V; the ±12V
rails provide generous output headroom. Rail-to-rail output ensures the clipping threshold
is close to the supply rails. Both channels are served by a single dual package.

## Output Series Resistor (2.2kΩ)

A 2.2kΩ resistor between the op-amp output and the clamp node limits fault current to a
level the reference divider can absorb. During normal operation, the Seed’s 13.6kΩ input
impedance draws minimal current through the 2.2kΩ, producing a small signal loss of
approximately 14% (2.2kΩ / 15.8kΩ). The op-amp gain compensates for this loss.

During fault conditions (op-amp clipping at ±11V), the resistor limits current to:

    (11V − 1.82V) / 2.2kΩ = 4.2mA

This is within the capacity of the reference divider and clamp diodes.

## Symmetric Clamp

The clamp sits at the Seed pin, after the 2.2kΩ series resistor. Per-channel resistive
dividers from the ±12V analog supply establish independent positive and negative reference
rails (avoiding crosstalk). Electrolytic capacitors hold the references stiff at audio
frequencies. A complementary BJT pair (2N3906 PNP + 2N3904 NPN, both SOT-23) per channel
clamps the signal to these rails:

```
Per channel:

            (+1.09V)                  (-1.09V)
+12V ── 10kΩ ──┬── 1kΩ ── AGND ── 1kΩ ──┬── 10kΩ ── -12V
               │                        │
             470µF                    470µF
               │                        │
             AGND                     AGND

Per channel (BJT clamp):

              +1.09V ref ── Base (Q1, PNP 2N3906)
                                │
R_out ──────────────── Emitter ──┬── Seed pin
                                │
              -1.09V ref ── Base (Q2, NPN 2N3904)

              Q1 Collector → 1kΩ → LED → -12V  (clip indicator)
              Q2 Collector → AGND
```

Q1 (PNP) conducts when the signal exceeds V(n+) + Vbe, sinking current from
Seed_In to -12V through the clip indicator LED. Q2 (NPN) conducts when the signal
falls below V(n-) − Vbe, sourcing current from ground into Seed_In. The transistors'
current gain (β≈200) means only Ic/β flows through the reference divider base
connection, largely eliminating reference pumping under overdrive. The base-emitter
forward ideality factor (NF≈1.24) provides a sharper clamp knee than diode
alternatives (BAV99 N=1.82). See "Other Clamp Designs Considered" appendix for the
investigation that led to this choice.

### Reference Divider Calculations

    V_ref = 12V × 1kΩ / (10kΩ + 1kΩ) = 1.091V
    R_th  = 10kΩ ∥ 1kΩ = 909Ω
    Quiescent: 12V / 11kΩ = 1.09mA per divider

At 20Hz (worst case for capacitor impedance):

    Z_cap = 1 / (2π × 20Hz × 470µF) = 16.9Ω
    Z_eff = 909Ω ∥ 16.9Ω = 16.6Ω

### Fault Analysis

Under fault conditions (op-amp clipping at ±11V), the clamp current flows through the
BJT collector to ground (or -12V via the LED). Only the base current loads the
reference divider:

    I_clamp = (11V − V_clamp) / 2.2kΩ ≈ 4mA
    I_base  = I_clamp / β ≈ 4mA / 200 = 20µA
    ΔV_ref  = I_base × R_th = 20µA × 909Ω = 18mV  (negligible)

SPICE simulation (LTspice, +24 dBu overdrive at R_fb = 25kΩ) shows **codec_max =
4.50V — 300mV margin** to the 4.8V absolute maximum. The BJT's current gain
eliminates the reference pumping that plagues diode-based clamps under the same
conditions.

> TODO: Re-run 5-corner tolerance sweep (±5% supply, ±1% resistors, ±20% caps,
> β variation) with BJT clamp to validate worst-case margin.

### Signal Interaction at Normal Levels

At the ±1.5V signal peak (3V p-p, 100% ADC utilisation), the BJT base-emitter bias
is V_peak − V_ref = 1.5 − 1.091 = 0.41V. With 2N3904/2N3906 model parameters
(NF≈1.24), the collector current at this bias is negligible — the sharper knee
(NF=1.24 vs N=1.82 for BAV99) means less sub-threshold conduction. SPICE simulation
confirms THD remains at the noise floor (0.071%) up to R_fb = 21kΩ, corresponding
to codec p-p = 2.31V (77% ADC utilisation).

### Tolerance Analysis

With ±5% supply tolerance (TMA-1212D) and ±1% resistors:

| Parameter | Nominal | Min (low supply) | Max (high supply) |
|-----------|---------|------------------|-------------------|
| V_ref     | 1.09V   | 1.02V            | 1.17V             |

At worst-case low V_ref (1.02V), diode current at the ±1.5V signal peak rises to ~89µA
(197mV drop). This is the absolute worst case (supply and all resistors at tolerance
extremes simultaneously); typical variation is much smaller.

The five SPICE tolerance corners (nominal, outer max, inner max, upper/lower DC offset)
confirm:

* Worst-case codec high: 4.72V (80mV margin to 4.8V abs max)
* Worst-case codec low: 155mV (well above -0.3V abs min)

The ±12V analog supply (TMA-1212D) can sink fault current in both directions.

## Components

**Per channel:**

* 10kΩ input resistor (R_in)
* 25kΩ trim pot (R_fb)
* 2.2kΩ series output resistor
* 1× 2N3906 PNP transistor, SOT-23 (positive clamp)
* 1× 2N3904 NPN transistor, SOT-23 (negative clamp)
* 1× LED + 1kΩ resistor (clip indicator, on Q1 collector to -12V)
* 2× 10kΩ resistors, 1% (R1, reference dividers)
* 2× 1kΩ resistors, 1% (R2, reference dividers)
* 2× 470µF electrolytic capacitors, 25V (reference rail filtering)

**Shared:**

* 1× OPA1656 dual op-amp (SOIC-8)
* 2× 100nF MLCC, 0402 or 0603 (op-amp supply decoupling, V+ and V-)
* 2× 1nF MLCC, 0402 (op-amp supply decoupling, VHF, V+ and V-)

## Power Budget (TMA-1212D, 1W)

| Source                   | Current (±12V) | Power     |
|--------------------------|----------------|-----------|
| 2× THAT 1246             | ~16mA          | 384mW     |
| OPA1656 (both channels)  | 7.8mA          | 187mW     |
| Clamp reference dividers | 4.3mA          | 52mW      |
| **Total**                | **~28mA**      | **623mW** |

## Performance Summary

| Condition                    | Op-amp output | At Seed pin    | ADC utilisation |
|------------------------------|---------------|----------------|-----------------|
| +4 dBu, R_fb = 21kΩ (clean)  | ±1.82V        | ±1.57V         | 77%             |
| +4 dBu, R_fb = 25kΩ (max)    | ±2.17V        | ±1.82V (clamp) | 89%             |
| +24 dBu, R_fb = 25kΩ (fault) | clips ±11V    | clamped ±2.73V | protected       |
| Muted (trim at 0%)           | 0V            | 0V             | —               |

> TODO: Recalculate signal rows once pot values are finalised.

### THD vs Gain (SPICE, +4 dBu input)

LTspice `.four` analysis at 1kHz with nominal component values:

**BJT clamp (2N3906/2N3904, V_ref = 1.091V):** Distortion-free up to R_fb ≈ 21.5kΩ.
THD rises gradually — 0.083% at 22kΩ, 0.105% at 23kΩ, 1.16% at 25kΩ. At the knee
the codec sees 2.36V p-p (79% ADC utilisation). At R_fb = 25kΩ the codec reaches
2.66V p-p (89%) with codec_max = 3.84V (signal zone). Under +24 dBu overdrive,
codec_max = 4.50V with 300mV damage margin.

For comparison with alternative clamp designs (BAV99 passive, post-clamp feedback
tap), see the appendix. The BJT clamp outperforms the BAV99 passive clamp (knee at
18.3kΩ, 67% utilisation) and avoids the reference pumping failure that disqualified
the feedback tap under overdrive.

See `sim/input/sharper-diode.csv` for the BJT clamp dataset and
`sim/input/thd-plus4db.csv` for the BAV99 baseline.

## Stability Analysis

The BJT clamp sits after R_out, entirely outside the op-amp feedback loop. The loop
gain, phase margin, and compensation are determined solely by R_fb, R_in, and the
OPA1656’s internal compensation — the clamp engaging does not alter the feedback
network. This is the primary reason the topology is inherently stable.

### Feedback Loop

The OPA1656’s unity-gain crossover frequency depends on the closed-loop gain:

    f_crossover = GBW / (R_fb / R_in)
    At R_fb = 10kΩ (gain = 1): 53 MHz
    At R_fb = 25kΩ (gain = 2.5): 21 MHz

These are RF frequencies. The op-amp’s load is R_fb (10k–25kΩ) in parallel with R_out
(2.2kΩ) — approximately 2.2kΩ resistive. This is a benign load with no reactive
component at the output node.

### BJT Parasitic Capacitances

The 2N3904/2N3906 present Cbe ≈ 4–5pF and Ccb ≈ 3–4pF at the Seed_In node. Behind
the 2.2kΩ series resistor, the associated pole is at:

    f_pole = 1 / (2π × 2.2kΩ × 10pF) ≈ 7.2 MHz

This pole is outside the feedback loop and does not affect phase margin. When the BJTs
turn on, the emitter impedance drops (re ≈ 26mV/Ic) but the op-amp only sees
increased current draw through R_out — no change to the feedback path.

### Clamp Transition Transients

At the clamp threshold, Cbe charges through R_out, producing a small current spike
(picojoules of energy). On a PCB with short traces this settles in nanoseconds. On a
breadboard prototype, lead inductance may produce visible ringing at a few MHz during
clamp onset — this is a breadboard artifact, not a circuit deficiency.

### Op-Amp Decoupling

The OPA1656’s 53 MHz GBW requires decoupling effective into the VHF range. A single
100nF MLCC resonates at ~20 MHz (depending on package); above that, its impedance
rises. A parallel smaller capacitor with a higher self-resonant frequency covers the
gap:

* **100nF (0402 or 0603 MLCC)** — effective to ~20 MHz
* **1nF (0402 MLCC)** — effective from ~20 MHz to ~200 MHz

Both capacitors on each supply pin (V+ and V-), placed within 5mm of the OPA1656
supply pins, with short returns to the analog ground pour.

## Layout Guidelines

### Component Placement

* **OPA1656, R_in, R_fb (pot):** Place as a tight group. The inverting input node
  (junction of R_in, R_fb wiper, and pin 2) is the most sensitive node in the circuit
  — minimise its trace length and area.
* **Decoupling caps (100nF + 1nF per rail):** Within 5mm of OPA1656 pins 4 and 8,
  with vias directly to the ground pour. Place the 1nF closer to the pin than the
  100nF.
* **R_out (2.2kΩ):** Place close to the op-amp output (pin 1). This resistor isolates
  the op-amp from all downstream parasitics — everything after it is non-critical for
  stability.
* **BJT clamp (Q1, Q2):** Place close to the Seed input pin, not close to the op-amp.
  The clamp protects the Seed pin, so short traces to the protected node matter more
  than proximity to the op-amp.
* **Reference dividers and caps:** Place near the BJT bases. The 470µF electrolytics
  are large — route them with short traces to the BJT base nodes and to AGND.
* **Clip LED + resistor:** Non-critical placement. Route from Q1 collector to -12V
  wherever convenient.

### Trace Routing

* **Inverting input trace (pin 2):** Keep short. Do not run parallel to the output
  trace (pin 1) — parasitic capacitance between these traces creates unwanted feedback
  at tens of MHz, potentially causing ringing or oscillation above the audio band.
* **R_fb traces:** Route the pot wiper and CCW terminal to pin 2 and pin 1
  respectively with no parallel segments to each other or to the input signal path.
* **Analog ground pour:** Continuous copper pour under the OPA1656 and the entire
  signal path from R_in to Seed_In. No splits or slots under the op-amp. Digital
  ground (Seed, USB, MIDI) should not share this pour.
* **Supply traces (±12V):** Route as a pair to the decoupling caps. Avoid long runs
  from the TMA-1212D — place the module close to the analog section or use wide
  traces (≥0.5mm).
* **Seed_In to Seed pin:** Short, direct trace. This node carries the clamped signal
  and connects to both BJT emitters, R_out, and R4/C1 (Seed input network).

## Ground Rules

All components in this circuit are in the analog signal path and connect to Analog
Ground. The clamp reference dividers derive from the ±12V analog supply (TMA-1212D
secondary) and terminate at AGND.

## Open Design Questions

* **Pot taper:** Audio (logarithmic) taper provides finer control in the low-gain region
  where hot signals are trimmed. Linear taper provides uniform gain-per-rotation.
* **Anti-alias filtering:** The OPA1656’s low output impedance changes the filtering
  requirements at the Seed input pin. The 1.5–2.2nF capacitor may still be useful for
  attenuating wideband op-amp noise above the audio band.

# Part 2: Midi Section

* TODO: Midi section still needs review on the Rev1 Board
* Obtain correct footprint for the Midi Optocoupler. [Github Issue](https://github.com/squeedee/daisy-studio/issues/6)

# Part 3: Optional Power Switch

* Add a header with a good retention mechanism on the board near the barrel jack for an external power
  switch [Github Issue](https://github.com/squeedee/daisy-studio/issues/5)
* When not desired, do not populate and replace with jumper OR add a plug with jumper built in

# Part 4: Output Section

* TODO: The output section still needs review on the Rev1 Board
* Remove the 3.5mm input output jacks. [Github Issue](https://github.com/squeedee/daisy-studio/issues/11)

# Part 5: Additional Power section issues

* Caps wrong voltage and dimension [github Issue](https://github.com/squeedee/daisy-studio/issues/2)
* Completely ignored layout rules for the buck
  converter [Github Issue](https://github.com/squeedee/daisy-studio/issues/1)

---

# Appendix: Other Clamp Designs Considered

## BAV99 Passive Diode Clamp

The original Rev 2 design used a BAV99 dual diode (SOT-23) per channel in place of
the BJT clamp. The topology was identical (diodes between Seed_In and the ±V_ref
rails) but with the full clamp current flowing through the reference divider.

The BAV99's high ideality factor (N=1.82) produces a ~200mV wide conduction knee,
limiting clean ADC utilisation to **67% (2.0V p-p at codec)** at the clamp onset
(R_fb ≈ 18.3kΩ). At R_fb = 25kΩ, THD reached 5.8%.

Under overdrive (+24 dBu), the full clamp current (~4mA) flows through the reference
divider's Thevenin resistance (R_th = 909Ω), producing a DC reference shift of up to
909mV — **reference pumping**. This was not identified in the original fault analysis,
which incorrectly used the AC impedance (R_th ∥ Z_cap ≈ 16.6Ω at 20Hz) instead of
the DC R_th.

The BJT clamp solves both problems: sharper knee (NF≈1.24) and β-reduced reference
loading (ΔV_ref = 4.5mV vs 909mV).

Simulation data: `sim/input/thd-plus4db.csv`, `sim/input/thd-plus4db.asc`

## Diode Substitution (1N4148, BAT54)

Investigated as a simpler alternative to the BJT clamp.

**1N4148:** Standard SPICE model has N=1.752 — nearly identical to BAV99's N=1.82.
All common silicon PN signal diodes cluster in the N=1.7–1.9 range, so no meaningful
knee improvement is available from diode selection alone.

**BAT54 (Schottky):** Lower ideality factor (N≈1.04) but exhibited significant
clamping asymmetry and very low Vf on the Rev 1 board. The high reverse leakage and
part-to-part variation within the package made it unsuitable for a precision symmetric
clamp.

## Post-Clamp Feedback Tap (Active Limiting)

Instead of changing the clamp element, the feedback resistor R_fb is reconnected from
the op-amp output to the Seed_In node (after R_out and the passive clamp). This puts
the BAV99 clamp inside the feedback loop, using loop gain to compress the diode knee
into a near-ideal brick-wall limiter.

```
Feedback from V_out (standard):

V_in → R_in → V_inv → op-amp → V_out → R_out → [clamp] → Seed_In
                ↑                  ↑
                └──── R_fb ────────┘

Feedback from Seed_In (post-clamp tap):

V_in → R_in → V_inv → op-amp → V_out → R_out → [clamp] → Seed_In
                ↑                                              ↑
                └──────────────── R_fb ────────────────────────┘
```

### Normal-Level Performance (+4 dBu)

With V_ref raised to 1.818V (5.6kΩ/1kΩ dividers) to compensate for R_out loss:

| Metric                   | Passive clamp | Feedback clamp |
|--------------------------|---------------|----------------|
| Knee onset (R_fb)        | ~18.3kΩ       | ~22kΩ          |
| codec p-p at knee        | 2.01V (67%)   | 2.81V (94%)    |
| THD at R_fb = 25kΩ       | 5.80%         | 0.11%          |
| codec p-p at R_fb = 25kΩ | hard clamp    | 3.19V          |

The best normal-level performance of any topology tested — 94% ADC utilisation at the
clean headroom limit.

### Failure Mode: Reference Pumping Under Overdrive

Under heavy overdrive (+24 dBu), the op-amp saturates and the clamp reverts to
passive behaviour. The half-wave rectified clamp current charges the reference
capacitors through R_th, shifting V_ref away from nominal.

With 5.6kΩ/1kΩ dividers (R_th = 848Ω), V(n+) shifted from 1.818V to ~3.0V, pushing
codec_max to 5.2V — well above the 4.8V damage threshold. Lowering divider impedance
to 2.7kΩ/470Ω improved this to codec_max = 4.77V, but only 30mV margin — insufficient
for component tolerances.

The fundamental limitation is that resistive dividers cannot hold V_ref stiff against
milliamps of rectified clamp current without consuming excessive quiescent power.

**This topology was not selected** because the overdrive protection failure cannot be
solved without adding an active voltage reference (e.g. TL431) or consuming most of
the remaining power budget for lower-impedance dividers. The BJT clamp achieves
comparable knee improvement with inherent overdrive protection via β-reduced reference
loading.

Simulation data: `sim/input/feedback-clamp.asc`, `sim/input/thd-plus4db.csv`

### References

The feedback clamp topology is well-established in precision analog and pro audio
design. Key references consulted:

1. Circuit Cellar, "Precision Clamps" —
   https://circuitcellar.com/resources/quickbits/precision-clamps/
2. Analog Devices, "Op Amp Precision Positive & Negative Clipper" —
   https://www.analog.com/en/resources/technical-articles/op-amp-precision-positive-negative-clipper-using-lt6015-lt6016-lt6017.html
3. Electronic Design, "Op Amps Make Precision Clipper, Protect ADC" —
   https://www.electronicdesign.com/technologies/analog/article/21801600/op-amps-make-precision-clipper-protect-adc
4. All About Circuits, "An Op-Amp Limiter" —
   https://www.allaboutcircuits.com/technical-articles/an-op-amp-limiter-how-to-limit-the-amplitude-of-amplified-signals/
5. Microchip AN1353, "Op Amp Rectifiers, Peak Detectors and Clamps" —
   https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ApplicationNotes/ApplicationNotes/01353A.pdf
6. Analog Devices AN-402, "Replacing Output Clamping with Input Clamping" —
   https://www.analog.com/en/resources/app-notes/an-402.html
7. Analog Devices, "Differential Op-Amp Driver Protects High-Resolution ADC" —
   https://www.analog.com/en/resources/technical-articles/differential-opamp-driver-protects-a-highresolution-adc-from-input-overvoltage.html
8. TI Precision Labs, "Op-Amps Stability — Phase Margin" —
   https://training.ti.com/ti-precision-labs-op-amps-stability-phase-margin

