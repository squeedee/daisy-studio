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

| Zone   | Target range V(codec)                               | Sim range V(codec)                          | Seed pin equivalent | Design intent                                                               |
|--------|-----------------------------------------------------|---------------------------------------------|---------------------|-----------------------------------------------------------------------------|
| Signal | 1.0V to 4.0V (3V p-p nom)                           | 1.5V to 3.5V (2.0V p-p)                     | ±1.5V               | Full ADC utilisation. No diode conduction.                                  |
| Clamp  | 4.0V to 4.5V                                        | 3.5V to 4.72V                               | ±1.5V to ±2.0V      | Progressive diode conduction limits overdrive. Keep this as low as possible |
| Damage | -0.3V to +4.8V (Vcc + 0.3V = 4.8V, LDO Vcc is 4.5V) | Not reached (worst case 4.72V, 80mV margin) | > ±2.8V             | Must never be reached.                                                      |

Design goals:

1. The 3V p-p full-scale signal must remain entirely below the clamp circuit’s
   start-of-knee — zero diode conduction at nominal operating level.
2. The hard clamp (full diode conduction + reference rail shift under fault current)
   targets 4.5V at the codec, providing maximum overdrive margin above 3V p-p
   without approaching the absolute maximum rating.
3. The gape between the top of the "Clamp" zone and the "Damage" zone should be maximised without encroaching on the
   Signal Zone

> TODO: Validate component tolerance ranges to ensure whatever we select does not encrouch on Signal, while staying
> as far from Damage as possible.

## Signal Path

```
Balanced in → THAT 1246 (-6dB) → R_in (10kΩ) → OPA1656 (inverting, ±12V) → R_out (2.2kΩ) → clamp → Seed pin
                                                       ↑
                                                 25kΩ pot (R_fb)
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
frequencies. A BAV99 dual diode (SOT-23) per channel clamps the signal to these rails:

```
Per channel:

            (+1.09V)                  (-1.09V)
+12V ── 10kΩ ──┬── 1kΩ ── AGND ── 1kΩ ──┬── 10kΩ ── -12V
               │                        │
             470µF                    470µF
               │                        │
             AGND                     AGND

Per channel (BAV99, SOT-23):

              +1.09V ref ── pin 2 (K2)
                              │
                             D2
                              │
R_out ────────────── pin 3 (K1/A2) ──── Seed pin
                              │
                             D1
                              │
              -1.09V ref ── pin 1 (A1)
```

D2 conducts when the signal exceeds +1.09V + Vf, sinking current into the positive
reference rail. D1 conducts when the signal falls below -1.09V - Vf, sourcing current
from the negative reference rail.

### Reference Divider Calculations

    V_ref = 12V × 1kΩ / (10kΩ + 1kΩ) = 1.091V
    R_th  = 10kΩ ∥ 1kΩ = 909Ω
    Quiescent: 12V / 11kΩ = 1.09mA per divider

At 20Hz (worst case for capacitor impedance):

    Z_cap = 1 / (2π × 20Hz × 470µF) = 16.9Ω
    Z_eff = 909Ω ∥ 16.9Ω = 16.6Ω

### Fault Analysis

Under fault conditions (op-amp clipping at ±11V):

    I_fault = (11V − 1.82V) / 2.2kΩ = 4.2mA
    ΔV      = 4.2mA × 16.6Ω = 0.070V
    V_clamp = 1.09V + 0.07V + 0.66V (Vf at 4mA) = 1.82V at Seed pin

SPICE simulation (LTspice, 5-corner tolerance sweep with ±5% supply, ±1% resistors,
±20% caps) validates worst-case hard clamp at **4.72V at the codec — 80mV margin** to
the 4.8V absolute maximum.

### Signal Interaction at Normal Levels

At the ±1.5V signal peak (3V p-p, 100% ADC utilisation), the diode forward bias is
0.41V. Using BAV99 SPICE model parameters (Is = 3.18nA, N = 1.82), diode current at
this bias is ~19µA, producing a ~42mV drop through the 2.2kΩ series resistor — 2.8%
peak compression. This is below the threshold of audibility for musical signals.

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
* 1× BAV99 dual diode, SOT-23 (symmetric clamp to reference rails)
* 2× 10kΩ resistors, 1% (R1, reference dividers)
* 2× 1kΩ resistors, 1% (R2, reference dividers)
* 2× 470µF electrolytic capacitors, 25V (reference rail filtering)

**Shared:**

* 1× OPA1656 dual op-amp (SOIC-8)

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
| +4 dBu, trim at 86%          | ±1.86V        | ±1.60V         | 89%             |
| +24 dBu, trim at ~10%        | ±2.09V        | ±1.80V         | 100%            |
| +24 dBu, trim at max (fault) | clips ±11V    | clamped ±1.82V | protected       |
| Muted (trim at 0%)           | 0V            | 0V             | —               |

> TODO: Recalculate signal rows once pot values are finalised — target ±1.50V at Seed pin
> for 100% ADC utilisation (3V p-p at codec).

### THD vs Gain (SPICE, +4 dBu input)

LTspice `.four` analysis at 1kHz with nominal component values shows the circuit is
distortion-free (THD at the simulator noise floor of ~0.07%) up to R_fb ≈ 18.3kΩ
(gain ≈ -1.83). Above this point the signal peaks enter the clamp diode knee and THD
rises steeply — reaching ~0.15% at 19kΩ, ~0.5% at 20kΩ, and ~5.8% at 25kΩ.

At R_fb = 18.3kΩ the codec sees 2.0V p-p of the available 3.0V p-p full scale (67%
ADC utilisation, approximately -3.5 dB). The remaining ~1V p-p of headroom is
unavailable without entering the clamp knee — a direct consequence of the V_ref
(1.091V) chosen for codec protection margin.

See `sim/input/thd-plus4db.csv` for the full dataset.

## Ground Rules

All components in this circuit are in the analog signal path and connect to Analog
Ground. The clamp reference dividers derive from the ±12V analog supply (TMA-1212D
secondary) and terminate at AGND.

## Open Design Questions

* **Pot taper:** Audio (logarithmic) taper provides finer control in the low-gain region
  where hot signals are trimmed. Linear taper provides uniform gain-per-rotation.
* **Op-amp decoupling:** 100nF ceramic on each supply pin, placed close to the OPA1656.
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

