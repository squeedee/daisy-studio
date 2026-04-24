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
- **MIDI** in, out, and thru via 5-pin DIN connectors with optoisolated input
- **Micro SD card** slot
- **GPIO breakout** header (2x12) for expansion

## Power

- 12V DC barrel jack input (2.1mm)
- TPS54302 buck converter for 5V rail (powers the Daisy Seed)
- TMA-1212D isolated DC-DC converter for clean ±12V analog supply
- TVS diode and reverse-polarity protection

## Project Structure

Designed in KiCad 8 with a hierarchical schematic

## Documentation

- [Input Stage Design & Simulation](sim/input/DESIGN.md)

## Status

Developing Rev2