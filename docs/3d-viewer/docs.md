# Daisy Studio

[[view:overview|Front View]] and [[view:back|Back View]]

Development board for the Electrosmith Daisy Seed that brings a slew of features

## Clean Power [[view:power|Power]]

* 5v for the seed and your UX with the TPS54302.
* An RS3-1212D provides clean **±12V dual** rails for analog input/output. 
* Overvoltage protection on all rails via SMBJ15CA.
* Reverse polarity protection with the DMP3056L-13.
* Optional power switch header at SW1 (can be jumpered).

## Power Headers [[view:power-header|Power Headers]]

* 5V and 3.3V at J12.
* ±12V at J8

## Balanced Audio In [[view:audio-input|Balanced Input]] 

- Studio level (+24 dBu peak), balanced input on Neutrik Combo Jacks (J4, J6) via THAT1246 differential receivers (U4, U5).
- Gain control and clip indicators for perfect gain staging.
- Trim control so the clip LED lights *before* the protection clamp engages.
- BJT clamp (2N3904/2N3906 pairs) protects the Seed's PCM3060 ADC from overdrive — sharp transistor knee, no diode-clamp distortion bleeding into your signal.
- C0G anti-alias cap on each Seed input pin attenuates out-of-band noise before the codec's sigma-delta ADC sees it.

## Balanced Audio Out [[view:audio-output|Balanced Output]]

- Studio level (+24 dBu peak) on Neutrik Combo Jacks (J1, J2) via THAT1646 line drivers.
- Per-channel volume pots on the daughterboard so each output trims independently.
- Output gain trimmed once at calibration with a 25-turn cermet on the OPA1656 gain stage.
- Phantom-power-safe: SM4004 diode clamps to the ±12V rails on every XLR pin.
- Rail TVS (SMBJ15CA) catches phantom back-feed when the gear is powered off.

## 5-Pin MIDI [[view:midi|MIDI]]

- IN, OUT, and THRU on three DIN-5 jacks (J7, J9, J10).
- Galvanically isolated input via the H11L1SM Schmitt-trigger optocoupler (U8) — clean UART edges to the Seed.
- THRU echoes the optoisolated input through a second pair of 33 Ω resistors, no buffer needed.
- Standard MIDI 1.0 electrical spec: 5 mA current loop at 31.25 kbaud.

## Seed [[view:seed|Seed]]

- Socketed Daisy Seed Rev 7 at U9.
- Every Seed GPIO not committed to onboard audio, MIDI, or USB is on the **2×14 GPIO breakout** at J11, plus +5V, +3V3D and DGND for your circuits.
- MicroSD slot (J14) wired to the Seed's SD interface.
- USB and audio I/O routed straight through, no muxing.

## Daughter Board [[view:daughter-header|Daughter Board]]

- **2×10 (20-pin) 0.1" header** at J3 — your daughterboard, your UX layout.
- Fully passive: input/output pots + clip LEDs only. No ICs cross the header.
- Stack-mount or IDC ribbon — pick whichever fits your enclosure.
- AGND interleaved on every audio pair, so shorting any two pins won't damage the main PCB.

---

<p style="color: var(--muted); font-size: 12px;">
Source: <code>daisy-studio.kicad_pcb</code> · GLB exported with
<code>kicad-cli pcb export glb</code> · Viewer:
<a href="https://modelviewer.dev/" target="_blank" rel="noopener">&lt;model-viewer&gt;</a>
</p>
