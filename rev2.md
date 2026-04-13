# Part 0: General changes in design

* Annotate all components in the schematic with ideal placement notes - make a property for them called
  `ideal-placement`.
* Add some details about the project to the silkscreen. [Github Issue](https://github.com/squeedee/daisy-studio/issues/4)
* GPIO component is wrong [Github Issue](https://github.com/squeedee/daisy-studio/issues/3)

# Part 1: High-Voltage Protected Audio Input for Daisy Seed

Goal: Interface a +24dBu (+/-17V peak) balanced signal into the Daisy Seed (PCM3060) while maintaining audio
transparency and hardware safety.

## Final Circuit Architecture (Signal Path Order)

1. THAT 1246 Line Receiver: Powered by +/-12V. Converts balanced signal to single-ended and provides -6dB gain (scaling
   +24dBu down to ~8.7V peak). **Unchanged**
2. Series Resistor (1.2kΩ): Acts as the primary current limiter for protection. **Unchanged**
3. Pad Switch (120Ω to Ground): Placed after the 1.2k resistor. When engaged, creates a ~20dB divider to prevent digital
   clipping of hot signals. **Unchanged**
5. Bias Junction (2.5V):
    1. 2x 100kΩ resistors (forming a divider between 5V and GND). **Unchanged**
        1. 10µF Filter Capacitor (from the 2.5V junction to GND) to suppress buck-regulator
           ripple. [Github Issue](https://github.com/squeedee/daisy-studio/issues/9)
        1. > TODO: Validate on Rev1
        1. > TODO Question: best layout position for this part? **New in Rev 2**
6. Protection Diodes (BAV99 — silicon, replaces BAT54S Schottky):
    1. One diode to 5V Rail (Cathode to rail).
        1. One diode to GND (Anode to GND).
        1. [Github Issue](https://github.com/squeedee/daisy-studio/issues/8)
        1. Validated on Rev 1 board with 1N4148 bodge. BAV99 is the pin-compatible
           dual silicon equivalent in SOT-23.
7. Daisy Seed Input (Pins 16/17): Includes an internal 3.6k series resistor.
8. Anti-Alias Cap (1.5nF to 2.2nF): Recommended at the pin to Ground to filter switching ripple.
    1. > Todo: test this on Rev1
10. 5.1V Zener Diode (1N4733A) across the 5V rail to Ground. Sinks current injected into the
    rail by the upper protection diode, clamping the rail at
    5.1V. [Github Issue](https://github.com/squeedee/daisy-studio/issues/10) **Placed in power section for Rev 2.**
    1. > TODO: Validate on Rev1

## 2. Critical Findings & Resolutions

* Schottky Leakage Distortion: The original BAT54A Schottky diodes exhibited excessive reverse leakage,
  causing non-linear distortion on the positive peak of the sine wave. Replacing with silicon diodes (1N4148,
  now BAV99) restored signal integrity at audio rates.
* 5V Rail Lift: The buck regulator cannot sink current. Audio signal energy dumped through the upper
  protection diode was raising the 5V rail to ~6V. Addressed by the 5.1V zener (1N4733A) on the rail.
* Grounding: Analog and Digital grounds are separated by a jumper pad, allowing for noise isolation while ensuring a DC
  reference for the protection circuit.

------------------------------

## 3. Performance Specs

* Safe Input Voltage: Up to +/-30V peaks (limited by resistor power/heat).
* Clamping Level: ~ -0.6V to +5.8V. (At seed input)
* Distortion-Free Range: ~ 0.6V to 4.4V. (at Seed Input)
* Full-Scale Range: Scaled by the 120Ω pad to fit the 3.6Vpp ADC limit.

> TODO: Gather better specs (we have raw data, needs synthesis)

## Ground Rules

Include the appropriate rule in the component properties in the schematic:

* If it touches the audio signal or bias, use Analog Ground.
* If it touches the 5V power rail or is meant to clamp a fault, use Digital Ground.

| Component                 | Connect Ground To... | Reason                                                          |
|---------------------------|----------------------|-----------------------------------------------------------------|
| THAT 1246 (Pin 1 & 4)     | Analog Ground        | Ensures the input signal reference is clean.                    |
| 120Ω Pad Switch           | Analog Ground        | Keeps the "shunted" audio signal from picking up digital noise. |
| 10µF Bias Filter Cap      | Analog Ground        | Creates a quiet AC reference for the 2.5V bias.                 |
| Bottom 100k Bias Resistor | Analog Ground        | Sets the 2.5V center point relative to the clean audio ground.  |
| Bottom 1N4148 Diode       | Digital Ground       | Dumps over-voltage spikes directly to the power return path.    |
| 5.1V Zener (on 5V Rail)   | Digital Ground       | Dumps the "injected" rail current to ground.                    |
| Daisy Seed DGnd Pins      | Digital Ground       |                                                                 |
| External Buck Regulator   | Digital Ground       | High-frequency switching noise should stay on the digital side. |
| Daisy Seed AGnd Pins      | Analog Ground        |                                                                 |
| Jumper Pad                | Both                 | as close as possible to the Daisy Seed’s AGND/DGND pins.        |

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
* Completely ignored layout rules for the buck convert [Github Issue](https://github.com/squeedee/daisy-studio/issues/1)

------------------------------

# Investigated: Replace Bias Network with Symmetric Clamp (Deferred)

## Summary

The 2.5V bias network (2x 100k resistors per channel + scrubber cap) exists solely to center the signal in
the 0-5V protection clamp window. However, the Daisy Seed's audio inputs are **AC coupled on the module
PCB** with an internal 2.5V bias via V_COM. The external bias is stripped by the coupling cap and is
redundant for the ADC.

This opens the possibility of replacing the asymmetric rail clamp + bias with a simpler **symmetric clamp to
ground**, eliminating several components and the 5V rail lift problem entirely.

## Evidence

From the **Daisy Seed datasheet (v1.2.0)**:
* "Audio inputs are AC coupled and 3.6Vpp, or approx. 1Vrms." (p.2)
* Audio input absolute max: **-1.8V to +1.8V** (Table 1, p.2)
* Input impedance: **13.6kΩ** (Figure 1.2, p.6) = 3.6k series resistor + 10k PCM3060 internal

From the **PCM3060 datasheet (SLAS533B)**:
* ADC center voltage: 0.5 V_CC = 2.5V (set internally)
* V_COM output: 0.5 V_CC, 12.5kΩ output impedance — provides internal bias after the AC coupling cap
* ADC full scale: 0.6 V_CC = 3 Vp-p (1V to 4V at the PCM3060 pin, after AC coupling)
* Analog input absolute max on the PCM3060 itself: -0.3V to (V_CC + 0.3V) — but the Seed's AC coupling
  cap isolates the header pin from this limit

## Internal signal path on the Daisy Seed module

```
Header Pin 16/17 → 3.6k series R → AC coupling cap → V_COM bias (2.5V) → PCM3060 VINL/VINR
```

## Proposed revised external signal path

```
THAT1246 → 1.2k series R → pad switch (120Ω to AGND) → bidirectional TVS clamp (to AGND) → Seed pin 16/17
```

* **Bidirectional TVS or back-to-back zeners** clamping at ~±1.5V (margin below ±1.8V abs max)
* 1.2k series resistor limits fault current through the TVS during overvoltage
* Signal stays centered at 0V; Seed AC coupling + V_COM handles the DC offset for the ADC

## Components eliminated per channel

* 2x 100k bias resistors (R21/R22 or R23/R24)
* 1x 10µF scrubber cap (was planned for Rev 2)
* 1x protection diode to 5V rail (upper clamp diode)
* 5.1V zener on 5V rail (no longer needed — no current dumped into 5V rail)

## Issues resolved

* **5V rail lift problem**: eliminated — no current path from signal to 5V rail
* **BAT54A/1N4148 leakage distortion**: eliminated — TVS has no forward-bias leakage at normal signal levels
* **Buck regulator noise coupling through bias network**: eliminated — no bias network

## Status: Deferred

No suitable bidirectional TVS or zener exists at the ±1.5V clamp level required. Standard zener
series (BZX84) start at 2.4V; back-to-back zeners clamp at Vz + Vf ≈ 3.0V minimum — above the
±1.8V abs max. ESD protection diodes (e.g., Nexperia PESD series) operate at the right voltage
but are rated for nanosecond transients, not sustained audio-rate clamping.

Rev 2 proceeds with the validated asymmetric clamp (BAV99 + 2.5V bias + 5.1V zener). This
approach is superseded by the Rev 3 op-amp concept below.

------------------------------

# Rev 3 Idea: Op-Amp Gain Stage on ±12V Rails

Replace the protection clamp circuit with a gain stage on the existing ±12V analog supply.

## Signal Path

```
THAT1246 (-6dB) → series input R → op-amp (±12V, ~-16dB) → Seed pin 16/17
```

The THAT1246 clips at ±10V on ±12V rails. At -16dB gain, worst-case output is ±1.6V — within the
Seed's ±1.8V abs max. The gain itself is the protection mechanism. Signal stays centered at 0V;
the Seed's AC coupling and V_COM handle the DC offset.

## Trade: eliminates 7 components per channel, adds 4

Eliminated: 2x 100k bias resistors, 1x diode pair, 1x bias cap, 1x 5.1V zener (shared).
Added: 1x op-amp (e.g., half OPA2134 on ±12V), 2x gain resistors, 1x series input resistor.

## Notes

* Pad switch integrates into the gain stage (switched feedback resistor)
* Eliminates the 5V rail lift problem and bias network noise coupling at the source
* Series input resistor limits current through the op-amp's internal clamp diodes if a
  gain resistor fails open