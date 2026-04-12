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
        1. 10µF Filter Capacitor (from the 2.5V junction to GND) to scrub buck-regulator
           noise. [Github Issue](https://github.com/squeedee/daisy-studio/issues/9)
        1. > TODO: Validate on Rev1
        1. > TODO Question: best layout position for this part? **New in Rev 2**
6. Protection Diodes (1N4148 Pair):
    1. One diode to 5V Rail (Cathode to rail).
        1. One diode to GND (Anode to GND).
        1. > TODO: Swap from BAT54A to 1N4148 to eliminate low-voltage leakage distortion.
        1. [Github Issue](https://github.com/squeedee/daisy-studio/issues/8)
        1. This is already tested and validated on the rev 1 board using a bodge.
7. Daisy Seed Input (Pins 16/17): Includes an internal 3.6k series resistor.
8. Anti-Alias Cap (1.5nF to 2.2nF): Recommended at the pin to Ground to filter switching ripple.
    1. > Todo: test this on Rev1
10. A 5.1V Zener Diode (e.g., 1N4733A) must be placed across the 5V rail to Ground to act as a "current sink"
    and lock the rail at 5.1V during over-voltage
    events. [Github Issue](https://github.com/squeedee/daisy-studio/issues/10)
    1. > Todo: Place this in the power section
    1. > Todo: Test this on Rev1

## 2. Critical Findings & Resolutions

* The Distortion Issue: The original BAT54A Schottky diodes were "leaky" and caused non-linear distortion on the
  positive peak of the sine wave. Swapping to 1N4148 silicon diodes restored signal integrity at audio rates.
* The 5V Rail "Lift": Because the Buck Regulator cannot sink current, the audio signal was dumping current through the
  protection diodes into the 5V rail, pushing it to 6V.
* Grounding: Analog and Digital grounds are separated by a jumper pad, allowing for noise isolation while ensuring a DC
  reference for the protection circuit.

------------------------------

## 3. Performance Specs

* Safe Input Voltage: Up to +/-30V peaks (limited by resistor power/heat).
* Clamping Level: ~ -0.6V to +5.8V. (At seed input)
* Distortion-Free Range: ~ 0.6V to 4.4V. (at Seed Input)
* Full-Scale Range: Scaled by the 120Ω pad to fit the 3.6Vpp ADC limit.

> TODO: Gather better specs (I've already got some good data, need to synthesize it)

## Ground Rules

Include the appropriate rule in the component properties in the schematic:

* If it touches the audio signal or bias, use Analog Ground.
* If it touches the 5V power rail or is meant to clamp a fault, use Digital Ground.

| Component                 | Connect Ground To... | Reason                                                          |
|---------------------------|----------------------|-----------------------------------------------------------------|
| THAT 1246 (Pin 1 & 4)     | Analog Ground        | Ensures the input signal reference is clean.                    |
| 120Ω Pad Switch           | Analog Ground        | Keeps the "shunted" audio signal from picking up digital noise. |
| 10µF Bias Filter Cap      | Analog Ground        | Creates a quiet AC reference for your 2.5V bias.                |
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