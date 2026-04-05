# Design for THAT1264 receiver into Seed Rev 7 PCM3060 Codec

PCM3060 Analog Input Stage Design Summary

## System Topology

The signal chain is designed to convert balanced professional line-level signals (+4 dBu nominal or +24 dBu "Hot") into
a single-ended signal compatible with the 3.3V/5V logic of the Daisy Seed.

Signal Chain:

```mermaid
flowchart LR
    A[Pro Audio In] --> B["THAT 1246 (-6dB Receiver)"]
    B --> C[Switchable -20dB Pad]
    C --> D[AC Coupling]
    D --> E["DC Bias (2.5V)"]
    E --> F[BAT54S Protection]
    F --> G[Daisy Input circuit]
    G --> H[PCM3060 ADC]
```

# Component Values (Per Channel)

| Component       | Value      | Purpose                                                                |
|-----------------|------------|------------------------------------------------------------------------|
| Active Stage    | THAT 1246  | Balanced-to-single-ended conversion with -6dB gain.                    |
| Series Resistor | 1.2 kΩ     | Current limiting for protection and top of Pad divider.                |
| Pad Resistor    | 120 Ω      | Shunt resistor to Ground (activated via DPDT switch for two channels). |
| Coupling Cap    | 10 µF      | DC blocking; preserves low-frequency response.                         |
| Bias Resistors  | 2 x 100 kΩ | Voltage divider to center signal at 2.5V (VCC/2).                      |
| Clamp Diode     | BAT54S     | Dual Schottky to VIN (5V) and AGND (0V).                               |

## Observed Performance (Simulated)
   Simulations were performed using LTspice with a 0.868V Peak source (representing +4 dBu after the THAT 1246).
   Frequency Response

* Audio Band (20Hz – 20kHz): Exceptionally flat.
* Low-End Roll-off: -0.047 dB at 20Hz (Cutoff frequency < 1Hz).
* High-End Roll-off: Flat beyond 100kHz (Cutoff frequency ~4.4MHz).

Headroom & Clipping

* Nominal (+4 dBu Input): Arrives at Codec at 1.64 Vp-p (-5.2 dBFS). High signal-to-noise utilization.
* Digital Clipping Point: Occurs at +9.2 dBu input (Pad OFF).
* Hot Input (+24 dBu Input): With Pad ON, arrives at Codec at 2.64 Vp-p.
* Max Headroom: Supports up to +25.1 dBu before digital clipping (Pad ON).

Hardware Protection ("The Seatbelt")

* Positive Clamp: Engages at ~5.3V.
* Negative Clamp: Engages at ~ -0.3V.
* Current Limiting: The 1.2 kΩ resistor restricts fault current to <10mA during extreme overvoltage, ensuring the
  PCM3060 and Daisy Seed remain physically safe.

