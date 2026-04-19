# Part 0: General changes in design

* Annotate all components in the schematic with ideal placement notes - make a property for them called
  `ideal-placement`.
* Add some details about the project to the
  silkscreen. [Github Issue](https://github.com/squeedee/daisy-studio/issues/4)
* GPIO component is wrong [Github Issue](https://github.com/squeedee/daisy-studio/issues/3)

# Part 1: Op-Amp Gain-Staged Audio Input

## Design Objectives

1. Maximise ADC headroom at +4 dBu (standard studio operating level).
2. Continuous trim from +4 dBu up to +24 dBu peak via a single pot per channel.
   Gain is set by a **fixed op-amp stage** on the main PCB; the user pot is a
   **passive attenuator after the op-amp** on the daughterboard — architecturally
   symmetric with the Part 4 output stage.
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
                                                  ┌──────────── main PCB ────────────┐
Balanced in → THAT 1246 (-6dB) → R_in (10kΩ) → OPA1656 (inverting, ±12V, fixed gain)  │
                                                       ↑                              │
                                                   R_fb 12kΩ fixed                    │
                                                                                      │
        ┌──────── header ────────┐                                                    │
        │  OPA_Out  ─────────────┼─────── OPA_Out (main)                              │
        │                        │                                                    │
        │  10kΩ log pot          │                                                    │
        │  (3-term divider)      │                                                    │
        │                        │                                                    │
        │  wiper ────────────────┼─────── Wiper_Return (main) → R_out (2.2kΩ)         │
        │                        │                              → BJT clamp          │
        │  AGND ─────────────────┼─── AGND                      → C_aa (1nF)          │
        └────── daughterboard ───┘                              → Seed pin            │
                                                                                      │
                                                                           LED (clip) │
                                                                                      │
                                                  └──────────────────────────────────┘
```

The THAT 1246 converts the balanced input to single-ended with -6dB of gain, preserving
common-mode rejection and keeping +24 dBu signals (±8.7V peak at the output) within the
±10V output swing of the ±12V rails.

The OPA1656 is configured as an inverting amplifier at a **fixed gain of 1.2×**
(R_fb = 12kΩ / R_in = 10kΩ), chosen to keep +24 dBu peak inputs within the
OPA1656's ±11V rail limits while running the pot input a little hotter than
THAT1246 output alone. The user's level control is a 10kΩ log-taper pot wired
as a three-terminal voltage divider on the daughterboard, **downstream of the
op-amp**. The op-amp always runs at the same operating point; the user simply
attenuates its output to taste.

Both cable legs between main PCB and daughterboard are low-impedance: the
op-amp drives the pot CW terminal directly, and the pot wiper feeds R_out
on the main PCB. The op-amp's inverting summing junction never leaves the
main PCB.

The signal remains centred at 0V throughout. The Daisy Seed's internal AC coupling
capacitor and V_COM bias (2.5V) handle the DC offset for the PCM3060 ADC; no external
bias network is required.

## Op-Amp Selection: OPA1656

The OPA1656 (TI, dual, SOIC-8) is selected for low voltage noise (4.3 nV/√Hz at 1kHz),
low distortion (THD+N 0.000029% at 1kHz), and 53 MHz GBW — comfortably exceeding audio
bandwidth requirements at the target gain range. Supply range extends to ±18V; the ±12V
rails provide generous output headroom. Rail-to-rail output ensures the clipping threshold
is close to the supply rails. Both channels are served by a single dual package —
the same part (and same decoupling scheme) used in the Part 4 output stage.

## Fixed Gain Selection (R_fb = 12kΩ)

    Gain = -R_fb / R_in = -12kΩ / 10kΩ = -1.2× (+1.58 dB)

Worst-case signal budget at the op-amp output:

| Input level    | THAT1246 SE output | OPA_Out (gain 1.2×) | Rail margin |
|----------------|--------------------|---------------------|-------------|
| +4 dBu nominal | ±0.87V (1.74 Vpp)  | ±1.04V (2.08 Vpp)   | ~10V        |
| +14 dBu        | ±2.75V (5.51 Vpp)  | ±3.30V (6.61 Vpp)   | ~7.7V       |
| +24 dBu peak   | ±8.71V (17.4 Vpp)  | ±10.45V (20.9 Vpp)  | ~0.55V      |

At the design maximum (+24 dBu balanced input peak) the OPA1656 output reaches
±10.45V, leaving ~550mV to the ±11V rail clip point — tight but workable on
nominal supplies. A ±5% supply sag shrinks this margin; if bench measurement
shows premature rail clipping, R_fb drops to 11kΩ (gain 1.1×, +0.8 dB,
~1.4V margin) without any other changes. **Verify in sim** before committing
to PCB.

The op-amp noise gain at this setting is 1 + R_fb/R_in = 2.2; referred to
its input, 4.3 nV/√Hz × 2.2 over 20 kHz ≈ 1.4 µV rms output noise. Far
below the THAT1246's own noise floor and the PCM3060 ADC's codec noise —
negligible in the signal budget.

## Output Series Resistor (2.2kΩ)

A 2.2kΩ resistor between the pot wiper (returning from the daughterboard) and
the clamp node at the Seed input pin limits fault current to a level the clamp
reference divider can absorb. During normal operation, the Seed's 13.6kΩ input
impedance draws minimal current through the 2.2kΩ — the small signal loss
(2.2kΩ / 15.8kΩ ≈ 14%) is baked into the calibration of the user pot position.

During fault conditions (op-amp clipping at ±11V, pot wiper at CW terminal),
the resistor limits current to:

    (11V − 1.82V) / 2.2kΩ = 4.2mA

This is within the capacity of the reference divider and clamp diodes. With
the pot wiper anywhere between CW and CCW, the pot's internal series
resistance (0–2.5kΩ, peak at mid-rotation) adds to R_out, reducing fault
current further. The worst case is pot at CW (wiper shorted to OPA_Out,
full 4.2 mA), which is the current Rev 1 / old Rev 2 design point.

## Symmetric Clamp

The clamp sits at the Seed pin, after the 2.2kΩ series resistor. Per-channel resistive
dividers from the ±12V analog supply establish independent positive and negative reference
rails (avoiding crosstalk). Ceramic capacitors (47µF MLCC) hold the references stiff at
audio frequencies. A complementary BJT pair (2N3906 PNP + 2N3904 NPN, both SOT-23) per channel
clamps the signal to these rails:

```
Per channel:

            (+1.09V)                  (-1.09V)
+12V ── 10kΩ ──┬── 1kΩ ── AGND ── 1kΩ ──┬── 10kΩ ── -12V
               │                        │
             47µF                     47µF
               │                        │
             AGND                     AGND

Per channel (BJT clamp):

              +1.09V ref ── Base (Q1, PNP 2N3906)
                                │
R_out ──────────────── Emitter ──┬── Seed pin
                                │
              -1.09V ref ── Base (Q2, NPN 2N3904)

              Q1 Collector → AGND
              Q2 Collector → AGND

Clip indicator (per channel):

              Seed_In ─────────── Comparator non-inv+ input
              Trim pot (AGND to n+) ── Comparator inv- input  (threshold, 0V to +1.09V)
              +12V → 1kΩ → LED anode; LED cathode → Comparator output (open collector)
```

Q1 (PNP) conducts when the signal exceeds V(n+) + Vbe, sinking current from
Seed_In through the transistor to -12V via the 1kΩ collector resistor. Q2 (NPN)
conducts when the signal falls below V(n-) − Vbe, sourcing current from ground
into Seed_In. The transistors'
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

    Z_cap = 1 / (2π × 20Hz × 47µF) = 169Ω
    Z_eff = 909Ω ∥ 169Ω = 143Ω

### Fault Analysis

Under fault conditions (op-amp clipping at ±11V), the clamp current flows through the
BJT collector to ground (or -12V via the LED). Only the base current loads the
reference divider:

    I_clamp = (11V − V_clamp) / 2.2kΩ ≈ 4mA
    I_base  = I_clamp / β ≈ 4mA / 200 = 20µA
    ΔV_ref  = I_base × R_th = 20µA × 909Ω = 18mV  (negligible)

SPICE simulation (LTspice, +24 dBu overdrive with the old variable-R_fb topology
at R_fb = 25kΩ) showed **codec_max = 4.50V — 300mV margin** to the 4.8V absolute
maximum. That fault path (OPA clips to ±11V → R_out → clamp → Seed) is unchanged
in the new architecture; only the feedback-path R_fb has moved from variable-pot
to fixed. With R_fb = 12kΩ the OPA no longer rail-clips at +24 dBu, so the actual
clamp-engagement fault is rarer, but the worst-case current calculation above
still applies when it does.

> TODO: Re-run 5-corner tolerance sweep (±5% supply, ±1% resistors, ±20% caps,
> β variation) with the new fixed-R_fb topology and a pot-model sweep to
> validate worst-case margin and confirm OPA rail-margin at +24 dBu.

### Signal Interaction at Normal Levels

At the ±1.5V signal peak (3V p-p, 100% ADC utilisation), the BJT base-emitter bias
is V_peak − V_ref = 1.5 − 1.091 = 0.41V. With 2N3904/2N3906 model parameters
(NF≈1.24), the collector current at this bias is negligible — the sharper knee
(NF=1.24 vs N=1.82 for BAV99) means less sub-threshold conduction. The clamp is
unchanged from the previous Rev 2 draft; the THD and ADC utilisation results
established for the variable-R_fb sim still apply here, but are now set by the
**user pot position** (and fixed input level) instead of R_fb. See the THD vs
Pot Position subsection below for the new sweep plan.

### Clip Indicator

A comparator monitors Seed_In directly and drives the LED when the signal peak
exceeds an adjustable threshold. This approach was chosen after prototype testing
showed that monitoring Q1's collector voltage is impractical — the onset voltage
change at Q1.C is only millivolts above the -12V rail, indistinguishable from supply
ripple.

The comparator's non-inverting input connects to Seed_In. A trim pot between AGND
and n+ (0V to +1.091V) sets the threshold on the inverting input. When the positive
signal peak exceeds the threshold, the comparator output goes high and lights the
LED. At audio frequencies the LED flickers faster than the eye can see — dim glow at
light clipping, bright at heavy clipping.

The full trim pot range (0V to 1.091V) corresponds directly to the useful signal
range at Seed_In, giving fine adjustment with no dead zone. The threshold is set
during calibration to the onset of audible clipping.

A single LM2903 dual comparator covers both channels, running on the existing ±12V
rails. The LM2903's open-collector output wires naturally against the +12V rail to
drive the LED (see diagram above) — when the output pulls low, the LED lights; when
it floats, the LED has no current path and is cleanly off with no reverse bias on
the LED junction. Fast response (~1.3µs) cleanly tracks individual signal peaks at
audio frequencies.

    Seed_In signal range:   0V to ±1.82V (clean), ±2.73V (clamp)
    Threshold range:        0V to +1.091V (trim pot)
    LED behaviour:          off below threshold, proportional glow above

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

**Per channel (main PCB):**

* 10kΩ input resistor (R_in, 0805 1%)
* 12kΩ feedback resistor (R_fb, 0805 1%) — fixed, sets op-amp gain 1.2×
* 2.2kΩ series output resistor (R_out, 0805 1%)
* 1× 2N3906 PNP transistor, SOT-23 (positive clamp)
* 1× 2N3904 NPN transistor, SOT-23 (negative clamp)
* 2× 10kΩ resistors, 1% (R1, reference dividers)
* 2× 1kΩ resistors, 1% (R2, reference dividers)
* 2× 47µF MLCC, 1206 or 1210, X5R/X7R (reference rail filtering)
* 1× 1nF C0G MLCC, 0402 or 0603 (C_aa, anti-alias at Seed input)

**Per channel (daughterboard — user-swappable controls):**

* 1× 10kΩ log-taper pot — user input level control (three-terminal voltage divider)
* 1× LED (clip indicator)
* 1× 1kΩ resistor (LED current limit, +12V → LED anode)
* 1× 10kΩ trim pot (clip threshold, AGND to n+; wiper to comparator inv input)

**Shared:**

* 1× OPA1656 dual op-amp (SOIC-8)
* 1× LM2903 dual comparator (clip indicator, both channels)
* 2× 100nF MLCC, 0402 or 0603 (OPA1656 supply decoupling, V+ and V-)
* 2× 1nF MLCC, 0402 (OPA1656 supply decoupling, VHF, V+ and V-)
* 2× 100nF MLCC, 0402 or 0603 (LM2903 supply decoupling, V+ and V-)

## Power Budget (TMA-1212D, 1W)

| Source                   | Current (±12V) | Power     |
|--------------------------|----------------|-----------|
| 2× THAT 1246             | ~16mA          | 384mW     |
| OPA1656 (both channels)  | 7.8mA          | 187mW     |
| Clamp reference dividers | 4.3mA          | 52mW      |
| LM2903 comparator        | ~1mA           | 24mW      |
| **Total**                | **~29mA**      | **647mW** |

## Performance Summary

Projected (pre-sim) signal levels for the new architecture with fixed
R_fb = 12kΩ (gain 1.2×) and pot wired as voltage divider. Pot position
expressed as fraction of OPA_Out amplitude passed to R_out (1.0 = CW max,
0.0 = CCW mute):

| Input level    | OPA_Out  | Pot setting | At Seed pin | ADC utilisation     |
|----------------|----------|-------------|-------------|---------------------|
| +4 dBu nominal | 2.08 Vpp | 1.0 (max)   | 1.8 Vpp*    | ~60%                |
| +14 dBu        | 6.61 Vpp | ~0.45       | 2.9 Vpp     | ~97% (clean ceiling) |
| +24 dBu peak   | 20.9 Vpp | ~0.14       | 2.9 Vpp     | ~97% (clean ceiling) |
| +24 dBu, pot max | 20.9 Vpp | 1.0 (max) | clamped ±2.73V | protected       |
| Any, pot mute  | n/a      | 0.0 (CCW)   | 0V          | muted               |

*includes the 14% loss across R_out and the Seed's 13.6kΩ input impedance.

> TODO: Re-verify all rows against sim (`sim/input/`) once the new architecture
> is modelled. Rows above are calculated, not simulated.

### THD vs Pot Position (pending sim)

With R_fb fixed, there is no "R_fb sweep" anymore. The new sweep of
interest is:

* **Input level × Pot position** grid — verify ADC utilisation and clip-free
  operation across typical operating points (+4 / +14 / +24 dBu input ×
  pot 0.1 / 0.5 / 1.0).
* **Op-amp rail margin at +24 dBu input** — confirm the 0.55V nominal
  margin holds with ±5% supply and ±1% R_fb/R_in tolerance stack.
* **LPF corner sweep across pot position** — confirm −3 dB corner stays
  above 30 kHz at all pot positions with C_aa = 1nF.

Existing sim artefacts (`sim/input/sharper-diode.asc`, `thd-plus4db.asc`,
`tolerances-plus24db.asc`, `feedback-clamp.asc`) were all built for the
old variable-R_fb topology. They need reworking for the new architecture:
fix R_fb = 12k, add a pot model (two resistors in series, parameter-swept
tap point) between OPA_Out and R_out, reduce C_aa to 1nF.

For comparison with alternative clamp designs (BAV99 passive, post-clamp
feedback tap), see the appendix. The clamp topology itself is unchanged
from the previous Rev 2 draft.

## Stability Analysis

The BJT clamp sits after R_out, entirely outside the op-amp feedback loop. The loop
gain, phase margin, and compensation are determined solely by R_fb, R_in, and the
OPA1656's internal compensation — the clamp engaging does not alter the feedback
network. The user pot is a passive voltage divider downstream of the op-amp, also
outside the feedback loop. This is the primary reason the topology is inherently
stable, and why pot position has **no effect** on loop phase margin.

### Feedback Loop

The OPA1656's unity-gain crossover frequency at the fixed gain:

    f_crossover = GBW / (1 + R_fb / R_in) = 53 MHz / 2.2 ≈ 24 MHz

An RF frequency. The op-amp's output load is R_fb (12kΩ) back to the inverting
node in parallel with the 10kΩ pot seen from OPA_Out (constant load regardless
of wiper position — voltage-divider wiring) and, through that pot, the 2.2kΩ
R_out plus clamp bias. Net load is approximately 5–6kΩ resistive. Benign, no
reactive component at the output node.

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

* **OPA1656, R_in, R_fb:** Place as a tight group. The inverting input node
  (junction of R_in and R_fb) is the most sensitive node in the circuit — and
  it lives entirely on the main PCB in this architecture, never crossing a
  header. Minimise its trace length and area. R_fb is a fixed 0805 1%, not a
  pot — so the node is just three component terminals (R_in, R_fb, op-amp pin
  2) clustered together.
* **Decoupling caps (100nF + 1nF per rail):** Within 5mm of OPA1656 pins 4 and 8,
  with vias directly to the ground pour. Place the 1nF closer to the pin than the
  100nF.
* **Daughterboard header pins for input pot:** The `OPA_Out_In` pin should sit
  close to the op-amp output (pin 1); the `Wiper_Return_In` pin should sit
  close to R_out. Adjacent AGND pins on both pairs keep return loop area small.
* **R_out (2.2kΩ):** Place close to the `Wiper_Return_In` header pin (not at
  the op-amp output, as in Rev 1 and the older Rev 2 drafts). The pot wiper
  returns via cable and feeds directly into R_out; the clamp and C_aa are on
  the Seed side of R_out.
* **BJT clamp (Q1, Q2):** Place close to the Seed input pin, not close to the op-amp.
  The clamp protects the Seed pin, so short traces to the protected node matter more
  than proximity to the op-amp.
* **Reference dividers and caps:** Place near the BJT bases. The 47µF MLCCs are
  compact (1206/1210) — place directly at the BJT base nodes with short returns to
  AGND.

### Trace Routing

* **Inverting input trace (pin 2):** Keep short, on the main PCB only. Do not
  run parallel to the output trace (pin 1) — parasitic capacitance between
  these traces creates unwanted feedback at tens of MHz, potentially causing
  ringing or oscillation above the audio band.
* **R_fb trace:** Route R_fb directly between op-amp pin 1 and pin 2 with no
  parallel segments to the input signal path. Because R_fb is fixed and both
  nodes are on the main PCB, this is a short, tightly-controlled trace.
* **Analog ground pour:** Continuous copper pour under the OPA1656 and the entire
  signal path from R_in to Seed_In. No splits or slots under the op-amp. Digital
  ground (Seed, USB, MIDI) should not share this pour.
* **Supply traces (±12V):** Route as a pair to the decoupling caps. Avoid long runs
  from the TMA-1212D — place the module close to the analog section or use wide
  traces (≥0.5mm).
* **Seed_In to Seed pin:** Short, direct trace. This node carries the clamped signal
  and connects to both BJT emitters, R_out, C_aa, and R4/C1 (Seed input network).
* **C_aa (1nF anti-alias):** Place directly at the Seed input pin, short trace
  from the pin to the cap, short return to the AGND pour under the Seed. The
  filter's R side is R_out plus the pot wiper Z, so the cap must be on the
  Seed end of R_out.

## Ground Rules

All components in this circuit are in the analog signal path and connect to Analog
Ground. The clamp reference dividers derive from the ±12V analog supply (TMA-1212D
secondary) and terminate at AGND.

## Anti-Alias Filter at Seed Input

A **1nF C0G capacitor from Seed_In to AGND**, placed immediately at the
Seed input pin (after the BJT clamp node), forms a single-pole low-pass
with the series resistance between the OPA_Out and the Seed pin:

    R_series = Z_pot_wiper + R_out
    Z_pot_wiper = 0 to 2.5 kΩ (peak at mid-rotation of the 10kΩ user pot)
    R_out = 2.2 kΩ
    → R_series varies from 2.2 kΩ (pot at CW or CCW) to 4.7 kΩ (pot at mid)

    f_LPF = 1 / (2π × R_series × 1nF)
          = 72.3 kHz (pot at ends) → 33.9 kHz (pot at mid)

The LPF corner stays safely above the audio band across pot travel. This
attenuates wideband noise from the OPA1656 (noise bandwidth extends into
the MHz range due to the 53 MHz GBW) and any out-of-band content above the
audio band before it reaches the PCM3060's sigma-delta ADC. The Seed's own
internal input network (R4/C1) contributes additional filtering upstream of
the codec but is insufficient on its own for this purpose.

**Why 1nF and not the earlier 2.2nF value:** with the old architecture
(fixed R_out, no pot in the series path), 2.2nF gave a 32.9 kHz corner. In
the new architecture the pot wiper source impedance adds to R_out, so 2.2nF
would sag the corner to ~15 kHz at mid-rotation — inside the audio band, not
acceptable. Dropping to 1nF restores sub-audio-band flatness across all pot
positions.

**Placement:** 0402 or 0603 C0G (NP0) MLCC, directly at the Seed input pin,
short trace from the pin to the cap and short return to the analog ground
pour. Do not place it on the daughterboard or at the op-amp output — the
R_out resistor plus pot wiper Z is what makes the filter work, so the cap
must be on the Seed side of R_out.

Value tradeoff (corner frequencies given at worst-case pot-mid R_series = 4.7kΩ):

| C_aa  | f_LPF (pot ends) | f_LPF (pot mid)    | Notes                                            |
|-------|------------------|--------------------|--------------------------------------------------|
| 680pF | 106 kHz          | 49.8 kHz           | Wider, less noise rejection                     |
| 1nF   | 72.3 kHz         | 33.9 kHz           | **Chosen** — clear of audio band across all pot positions |
| 1.5nF | 48.2 kHz         | 22.6 kHz           | Marginal — corner touches top of audio at pot mid |
| 2.2nF | 32.9 kHz         | 15.4 kHz           | Unacceptable — audible rolloff at pot mid        |

## User Controls on Daughterboard

The **input level pot**, the **clip-indicator threshold trim pot**, and the
**clip LED** for each channel are not populated on the main PCB. They live
on a separate control PCB connected via a header. This lets users design
their own front panel (pot types, LED colours/packages, panel layout)
without forking the main board.

The input level pot is a **10kΩ log-taper voltage divider downstream of the
op-amp** — architecturally identical to the Part 4 output pot (same part,
same wiring, same impedance behaviour). See "Output Level Pot" and its
"Impedance behaviour" subsection in Part 4 for the full analysis of
constant op-amp load and wiper-position-dependent source impedance.

Signals on the header (per channel, input stage):

* `OPA_Out_In` — op-amp output (main PCB, low-Z) to the pot CW terminal.
* `Wiper_Return_In` — pot wiper back to main PCB (moderate-Z: 0 to ~2.5kΩ
  depending on pot position) into R_out.
* `AGND` (pot CCW terminal) — proper mute leg; return for the signal pair.
* `n+` (upper reference rail) — clip-threshold trim pot top.
* Comparator inverting input — clip-threshold trim pot wiper.
* `+12V` — LED anode supply through 1kΩ.
* Comparator open-collector output — LED cathode.

Both audio signal legs on the cable (`OPA_Out_In` and `Wiper_Return_In`)
are low-impedance — the op-amp directly drives one end, and the pot wiper
source impedance peaks at 2.5kΩ at mid-rotation on the other. No
summing-junction / high-Z feedback node leaves the main PCB. This makes
the daughterboard cable routing substantially less critical than in the
previous Rev 2 draft.

See Part 4 for the shared header pinout; a single stereo header carries all
L/R input and output control signals.

### Signal-integrity notes for the input-stage cable

* Pair each signal with an adjacent AGND return pin on the header. A
  ground pin every two or three signal pins keeps loop area small.
* The `Wiper_Return_In` line is moderate-Z (up to 2.5kΩ at pot mid). Keep
  it physically separate from the comparator open-collector output (which
  carries fast digital edges when clipping) — ideally not on an adjacent
  header pin to it. Use ribbon cable pinout or bundle grouping to enforce
  separation.
* Interaction with C_aa: C_aa sees R_out + wiper Z as its series R. The
  LPF corner varies from 72 kHz (pot at ends) to 34 kHz (pot at mid) — all
  safely above the audio band. See "Anti-Alias Filter at Seed Input" above.
* Cable length guideline: ≤ 150mm is comfortable; ≤ 50mm is conservative.
  Unlike the old Rev 2 draft, there is no hard upper bound driven by
  inverting-input sensitivity.

# Part 2: Midi Section

* TODO: Midi section still needs review on the Rev1 Board
* Obtain correct footprint for the Midi Optocoupler. [Github Issue](https://github.com/squeedee/daisy-studio/issues/6)

# Part 3: Optional Power Switch

* Add a header with a good retention mechanism on the board near the barrel jack for an external power
  switch [Github Issue](https://github.com/squeedee/daisy-studio/issues/5)
* When not desired, do not populate and replace with jumper OR add a plug with jumper built in

# Part 4: Output Section

## Design Objectives

1. Bring the Daisy Seed's digital full-scale output up to a standard studio peak level
   (~+24 dBu) — as close to rail-to-rail on the ±12V analog supply as headroom allows.
2. Preserve the balanced XLR output and its tolerance to hot-plug mishaps
   (phantom power on the line).
3. Remove the 3.5mm input/output jacks. [Github Issue](https://github.com/squeedee/daisy-studio/issues/11)

## Signal Path

```
Seed audio out → OPA1656 (inverting, ±12V, calibrated gain) → Output level pot → THAT1646 balanced driver → clamp diodes → XLR
```

The Seed's PCM3060 outputs ~2.0 V p-p at digital full scale (0.6 × AVCC, AC-coupled
through the Seed's 4.7µF / 47k / 100R network — DC-blocked, 0V-centred, ~100Ω
source). That lands at roughly −1 dBu single-ended, or +5 dBu across the Rev 1
THAT1646 differential output — ~20 dB short of the rails. Rev 2 adds an OPA1656
gain stage ahead of the THAT1646 to close that gap, plus a user-facing output
level control to match downstream gear.

## Op-Amp Gain Stage (OPA1656)

Inverting configuration on the ±12V rails, same part and topology as the Part 1
input stage. The op-amp runs at a **fixed calibrated gain** set by a bring-up
trimmer; output level is varied downstream by a passive pot (see below).

    Gain = -R_fb / R_in
    R_in     = 2.2kΩ  (fixed, 1%)
    R_fb     = 15kΩ fixed + 10kΩ multi-turn trimmer (rheostat, in series)
    Range    = 15kΩ to 25kΩ → gain 6.8× to 11.4× → peak +21.0 to +25.6 dBu
    Nominal  = 20kΩ (trim mid-travel) → gain 9.1× → peak +23.7 dBu at XLR

The **15kΩ fixed + 10kΩ trim** split puts the calibration window exactly where
it matters — the 25-turn cermet trimmer (e.g. Bourns 3296W-1-103) gives ~400Ω
per turn, resolving to ~0.5% of R_fb. The fixed 15kΩ floor prevents the gain
from dropping into unusable territory if the wiper loses contact; the 25kΩ
ceiling prevents accidental hard clipping (sim shows onset at R_fb ≈ 23kΩ).

Sim results (`sim/output/gain-controlled-output.asc`, swept `R_fb`) confirm
the signal path is clean (THD ≈ 0.07%, behavioural-model floor) up to
`R_fb = 22kΩ` (+24.8 dBu peak), then clips hard at `R_fb = 25kΩ` (THD = 1.18%,
3rd/5th/7th harmonics dominant). On ±12V supplies the THAT1646 reaches its
±10.5V single-ended limit just before the OPA1656 hits its ±11V rails — the
line driver is the tighter constraint.

The 100Ω Seed source impedance is absorbed into R_in (≈ 4.5% gain error,
trimmed out during calibration). DC coupling is acceptable — the Seed pin is
already AC-coupled by the Rev 7 4.7µF cap, so no offset reaches the op-amp
input. The op-amp's own input bias current through R_in develops a negligible
DC offset at the output given the gain and rail budget.

### Calibration procedure

1. Set output level pot fully clockwise (no attenuation).
2. Play a digital full-scale 1 kHz sine from the Seed.
3. Measure differential XLR output with a scope or audio analyser.
4. Adjust R_fb trimmer until differential output reads +24 dBu peak
   (12.28 V p-p, nominal mid-trim should land close to this).
5. Lock trimmer with a dab of nail polish or trim paint.

## Output Level Pot

Two **10kΩ log pots** (one per channel, **not ganged** by default) sit between
each channel's `OPA_Out` and its THAT1646 input, acting as passive voltage
dividers. The pots live on the daughterboard (see "User Controls on
Daughterboard" below) so users can choose their own taper, package, or swap
to a ganged stereo pot if they want linked L/R behaviour.

```
OPA_Out ──┬── R_top of pot
          │
       wiper ── to THAT1646 input (high-Z, no loading)
          │
         GND ── R_bot of pot
```

Placed **after** the op-amp, not inside its feedback loop:

* Op-amp always runs at calibrated gain → consistent noise floor, stable
  feedback phase margin regardless of pot position.
* Passive attenuator at a low-impedance node → signal and noise scale together
  cleanly; no gain-dependent hiss.
* THAT1646 input is high-Z, so a 10kΩ pot presents negligible load to the
  op-amp and no meaningful source impedance variation to the THAT1646.

Log (audio) taper gives smooth perceived level control at low settings, where
the ear is most sensitive to small adjustments. Because L and R are separate
pots, users pick their own tolerance/matching strategy: two budget pots ≈ 2–3
dB imbalance worst case (user-trimmable by ear); a matched stereo pot
eliminates imbalance at the cost of forcing the same taper on both channels.

### Impedance behaviour

One useful property of the voltage-divider wiring: the op-amp sees a **constant
load** regardless of knob position. End-to-end pot resistance is fixed at
10kΩ, and the THAT1646 input is high-Z (~50kΩ+), so:

    Z_load(OPA_Out) = R_top + (R_bottom ∥ Z_THAT_in) ≈ R_top + R_bottom = 10kΩ

Independent of wiper position. The op-amp's load line never changes as the
user turns the knob.

What does vary is the source impedance presented to the THAT1646 input:

| Wiper position   | Source Z to THAT1646 input         |
|------------------|------------------------------------|
| Full CW (max)    | ~0Ω (direct to low-Z op-amp output) |
| Mid-rotation     | ~2.5kΩ (R_top ∥ R_bottom at midpoint) |
| Full CCW (mute)  | ~0Ω (direct to AGND)               |

Peak source impedance ~2.5kΩ at mid-rotation is well within the THAT1646's
tolerance — its input bias current is small enough that the resulting offset
is negligible, and no bandwidth limitation arises at audio frequencies.

## THAT1646 Balanced Driver

Unchanged from Rev 1. Converts the single-ended op-amp output into a balanced
differential pair with fixed unity S.E.-to-each-output gain (+6 dB hot-to-cold).
Sense pins close the feedback loop at the XLR connector, giving cross-coupled
output impedance control and immunity to load imbalance on the two legs. On ±12V
the THAT1646 can swing ~±21V differentially before clipping — well above the
op-amp's clipping point, so the op-amp sets the clean ceiling.

## Phantom-Power Protection Diodes

Retained from Rev 1: four SM4004 diodes per channel, two per output pin
(hot and cold), clamping each XLR output to the ±12V rails.

```
+12V ────┬──────┬────
         │K     │K         (cathodes to +12V)
         ▼      ▼
         D      D
         ▲      ▲          (anodes to -12V)
         │A     │A
-12V ────┴──────┴────
         │      │
        Hot    Cold   → XLR pins 2, 3
```

Protects the THAT1646 output stage when an XLR output is accidentally plugged
into a mic preamp with phantom power asserted. +48V through the preamp's 6.8kΩ
phantom feed produces ~5 mA per pin into the clamp — SM4004 (1A SMA) handles
this with huge margin and provides surge capacity for hot-plug transients.

## Signal Budget

| Node                              | Full-scale level        | Notes                                 |
|-----------------------------------|-------------------------|---------------------------------------|
| PCM3060 VOUTL/R (on Seed die)     | 1.98 V p-p, V_COM ±     | 0.6 × AVCC, AVCC=3.3V                 |
| Seed audio-out pin (post Rev 7 net) | 2.0 V p-p, 0V-centred | 4.7µF HPF @ 0.72 Hz, 100Ω source      |
| OPA1656 output (calibrated, mid-trim) | ~18.2 V p-p         | 9.1× gain, ~2V margin to ±11V op-amp clip |
| Output pot wiper (pot at 100%)    | ~18.2 V p-p             | Passive divider, full level           |
| XLR pin 2 vs pin 3 (calibrated, pot 100%) | ~24.6 V p-p ≈ +24 dBu peak | Calibration target                |
| Clean ceiling (sim-verified)      | ~38 V p-p ≈ +24.8 dBu   | THAT1646 hits ±10.5V limit first      |
| Hard clip (sim-verified)          | ~42 V p-p ≈ +25.6 dBu   | THD 1.18%, beyond usable range        |

## User Controls on Daughterboard

All user-facing controls (output level pots L+R, plus the input-stage clip
LEDs and clip-threshold trim pots from Part 1) live on a separate PCB
connected to the main board via a single header. This lets users build their
own panel layout without forking the main PCB.

**Per channel signals on the header (output stage):**

* `OPA_Out` — pot CW terminal (input to attenuator)
* `THAT_In` — pot wiper (output, feeds THAT1646 input)
* `AGND` — pot CCW terminal (attenuator ground leg for proper mute)

Pot is wired as a three-terminal voltage divider; all three pins are
required.

**Signal-integrity notes for the header:**

* Keep the `OPA_Out` ↔ `THAT_In` loop short and close to AGND. The return
  path (AGND pin adjacent to each signal pair on the header) matters — a
  ground pin every two or three signal pins keeps loop area small.
* Use a shielded cable or flat ribbon with dedicated ground between header
  and daughterboard if the daughterboard is more than ~50mm away from the
  main board.
* The `THAT_In` node is high-Z at the THAT1646 input — route it through the
  lowest-noise pair on the cable.

## Rail Protection (TVS per rail)

The TMA-1212D is a switching DC-DC converter: it can source current but
cannot sink it. If current is forced **into** the ±12V rails from outside,
the rail voltage rises uncontrollably.

**The fault scenario:** our gear is powered off, but the XLR output stays
connected to a mic preamp with +48V phantom asserted. The THAT1646 outputs
float (no supply), the clamp diodes conduct from each XLR pin toward the
dead +12V rail, and ~7 mA per pin (up to 28 mA stereo) sustains into a node
with no sink. Rail caps charge up; eventually the rail can pump toward the
phantom supply voltage, destroying the OPA1656 (±22V abs max) and THAT1646
(±20V abs max) when the gear is next powered on.

**Mitigation:** one TVS per rail to AGND:

* `+12V → AGND`: unidirectional 15V TVS (e.g. SMAJ15A), cathode on +12V,
  anode on AGND. Reverse-biased in normal operation, clamps when +12V pumps
  above ~16V.
* `-12V → AGND`: unidirectional 15V TVS, cathode on AGND, anode on -12V.
* Or a single bidirectional 15V TVS (SMAJ15CA) per rail works equally well
  and simplifies BOM by part-number consolidation.

Under a sustained 28 mA fault the TVS dissipates ~0.4 W — well within the
1 W rating of a SMAJ part. Also handles hot-plug surge transients.

Place the TVS physically close to where the clamp-diode return currents
enter the rail — i.e. near the THAT1646s, not near the TMA-1212D output —
so fault current has the shortest possible path.

## Components

**Per channel (main PCB):**

* 1× R_in (2.2kΩ, 1%) — op-amp inverting input resistor
* 1× R_fb_fixed (15kΩ, 1%) — op-amp feedback floor
* 1× R_fb_trim (10kΩ multi-turn cermet, e.g. Bourns 3296W-1-103) — gain
  calibration, wired rheostat-mode in series with R_fb_fixed
* 4× SM4004 (SMA) — XLR output clamp to ±12V rails
* 1× THAT1646 balanced line driver (SOIC-8)

**Per channel (daughterboard — user-swappable controls):**

* 1× 10kΩ log pot — output level (three-terminal voltage divider)

**Shared (main PCB):**

* 1× OPA1656 dual op-amp (SOIC-8) — both output channels
* 2× 100nF + 2× 1nF MLCC — OPA1656 supply decoupling (V+ and V-), same
  scheme as the input stage
* 2× SMAJ15A (or 1× SMAJ15CA per rail) — rail protection against
  powered-off phantom faults
* THAT1646 decoupling per datasheet (unchanged from Rev 1)


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

