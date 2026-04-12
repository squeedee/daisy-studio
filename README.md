# Daisy Studio

A carrier board for the [Electrosmith Daisy Seed](https://www.electro-smith.com/daisy/daisy) DSP module, providing
professional studio-grade balanced line input and output.

## Features

- **Balanced audio I/O** using THAT Corporation ICs
    - 2x THAT1246 balanced line receivers (stereo input)
    - 2x THAT1646 balanced line drivers (stereo output)
- **Neutrik combo jacks** (NCJ6FA-H-0) — accepts both XLR and 1/4" TRS on all 4 audio connectors
    - Inputs capable of withstanding hot signals up to 24dBu (with substantial clipping)
    - Input -12dBu pad for hot (up to 24dBu) signals.
- **3.5mm stereo jacks** for unbalanced line in/out
- **MIDI** in, out, and thru via 5-pin DIN connectors with optoisolated input
- **Micro SD card** slot
- **GPIO breakout** header (2x12) for expansion

## Power

- 12V DC barrel jack input (2.1mm)
- TPS54302 buck converter for 5V rail (powers the Daisy Seed)
- TMA-1212D isolated DC-DC converter for clean ±12V analog supply
- TVS diode and reverse-polarity protection

## Project Structure

Designed in KiCad 8 with a hierarchical schematic:

| File                     | Description                                      |
|--------------------------|--------------------------------------------------|
| `daisy-studio.kicad_sch` | Root schematic sheet                             |
| `power.kicad_sch`        | Power supply (12V input, 5V buck, ±12V isolated) |
| `daisy_seed.kicad_sch`   | Daisy Seed module connections                    |
| `audio.kicad_sch`        | Balanced line receivers/drivers and connectors   |
| `daisy-studio.kicad_pcb` | PCB layout                                       |
| `bom.csv`                | Bill of materials with Mouser part numbers       |
| `daisy-studio.kicad_sym` | Project symbol library                           |
| `daisy-studio.pretty/`   | Project footprint library                        |

## Documentation

- [Schematic (PDF)](docs/daisy-studio-schematic.pdf)
- [PCB Layout (PDF)](docs/daisy-studio-pcb.pdf)
- [Input Stage Design & Simulation](sim/input/DESIGN.md)

## Status

[Known Issues](https://github.com/squeedee/daisy-studio/issues?q=is%3Aissue%20state%3Aopen%20label%3Abug)

