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

| Zone   | Codec voltage range                                 | Seed pin equivalent | Design intent                                                               |
|--------|-----------------------------------------------------|---------------------|-----------------------------------------------------------------------------|
| Signal | 1.0V to 4.0V (3V p-p nom)                           | ±1.5V               | Full ADC utilisation. No diode conduction.                                  |
| Clamp  | 4.0V to 4.5V                                        | ±1.5V to ±2.0V      | Progressive diode conduction limits overdrive. Keep this as low as possible |
| Damage | -0.3V to +4.8V (Vcc + 0.3V = 4.8V, LDO Vcc is 4.5V) | > ±2.8V             | Must never be reached.                                                      |

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

    (11V - V_clamp) / 2.2kΩ

where V_clamp is the clamp diode conduction voltage. This must remain within the
capacity of the reference divider and clamp diodes.

## Symmetric Clamp

The clamp sits at the Seed pin, after the 2.2kΩ series resistor. Resistive dividers from
the ±12V analog supply establish positive and negative reference rails. Electrolytic
capacitors hold the references stiff at audio frequencies. Two silicon signal diodes per
channel clamp the signal to these rails:

The reference rails are per channel to avoid cross talk.

```
Per channel:

          (+V_ref)                (-V_ref)
+12V ── R1 ───┬── R2 ── AGND ── R2 ───┬── R1 ── -12V
              │                       │
            C_ref                   C_ref
              │                       │
            AGND                    AGND

Per channel:

              +V_ref
                │
           D+ (cathode)
                │
R_out ──────── node ──── Seed pin
                │
           D- (anode)
                │
              -V_ref
```

D+ conducts when the signal exceeds +V_ref + Vf, sinking current into the positive
reference rail. D- conducts when the signal falls below -V_ref - Vf, sourcing current
from the negative reference rail.

The reference rail voltages are selected so that the hard clamp point (V_ref + diode Vf + rail shift under fault
current) maps to 4.5V-4.8V at the codec.
The start-of-knee (V_ref + diode onset ~0.3V) must remain above the 3V p-p signal peak.

> TODO: Select divider resistor ratio and capacitor value. The calculation structure is:
>
>     V_ref = 12V × R2 / (R1 + R2)
>     R_th  = R1 ∥ R2               (Thévenin impedance)
>     Z_cap = 1 / (2π × f × C_ref)  (capacitor impedance at frequency f)
>     Z_eff = R_th ∥ Z_cap           (effective impedance at frequency f)
>
>     Fault current:  I_fault = (V_clip - V_ref - Vf) / R_out
>     Rail shift:     ΔV = I_fault × Z_eff
>     Hard clamp:     V_clamp = V_ref + ΔV + Vf
>
> Target: V_clamp maps to 4.5V–4.8V at the codec (after AC coupling and 2.5V bias).
> Constraint: V_ref + 0.3V (diode onset) must exceed the 1.5V signal peak at the Seed pin.

The ±12V analog supply (TMA-1212D) can sink fault current in both directions.

## Components

**Per channel:**

* 10kΩ input resistor (R_in)
* 25kΩ trim pot (R_fb)
* 2.2kΩ series output resistor
* 2× silicon signal diodes (to reference rails)

**Shared:**

* 1× OPA1656 dual op-amp (SOIC-8)
* Reference divider resistors (values TBD per clamp target calculations) - consider tight tolerance parts, at least 1%
* 2× electrolytic capacitors (reference rail filtering, value TBD)

## Power Budget (TMA-1212D, 1W)

| Source                   | Current (±12V) | Power   |
|--------------------------|----------------|---------|
| 2× THAT 1246             | ~16mA          | 384mW   |
| OPA1656 (both channels)  | 7.8mA          | 187mW   |
| Clamp reference dividers | TBD            | TBD     |
| **Total**                | **TBD**        | **TBD** |

> TODO: Update divider current and total power after reference resistor values are finalised.

## Performance Summary

| Condition                    | Op-amp output | At Seed pin   | ADC utilisation |
|------------------------------|---------------|---------------|-----------------|
| +4 dBu, trim at 86%          | ±1.86V        | ±1.60V        | 89%             |
| +24 dBu, trim at ~10%        | ±2.09V        | ±1.80V        | 100%            |
| +24 dBu, trim at max (fault) | clips ±11V    | clamped (TBD) | protected       |
| Muted (trim at 0%)           | 0V            | 0V            | —               |

> TODO: Update clamped voltage after reference rail values are finalised.
> TODO: +4 dBu target should be ±1.50V for 100% utilisation - recalculate this table based on nominal range from the
> PCM3060's datasheet (3v p-p).

## Ground Rules

All components in this circuit are in the analog signal path and connect to Analog
Ground. The clamp reference dividers derive from the ±12V analog supply (TMA-1212D
secondary) and terminate at AGND.

## Open Design Questions

* **Pot taper:** Audio (logarithmic) taper provides finer control in the low-gain region
  where hot signals are trimmed. Linear taper provides uniform gain-per-rotation.
* **Clamp diode packaging:** Two diodes per channel in opposite orientations. Options
  include discrete 1N4148 (SOD-323) or dual packages sharing a reference rail across
  both channels — e.g., BAV70 (common cathode) for the positive clamp rail and a
  common-anode dual for the negative clamp rail. Investigate if the shared package provides better thermal characteristics.
* **Op-amp decoupling:** 100nF ceramic on each supply pin, placed close to the OPA1656.
* **Anti-alias filtering:** The OPA1656’s low output impedance changes the filtering
  requirements at the Seed input pin. The 1.5–2.2nF capacitor may still be useful for
  attenuating wideband op-amp noise above the audio band.
* **Reference divider component selection:** Resistor values and capacitor sizing per
  the codec voltage budget targets above.

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
* Completely ignored layout rules for the buck converter [Github Issue](https://github.com/squeedee/daisy-studio/issues/1)

