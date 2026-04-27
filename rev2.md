# Daisy Studio — Rev 2 Design Document

## Contents

- [Part 0: Design-Wide Changes](#part-0-design-wide-changes)
  - [Schematic Conventions](#schematic-conventions)
    - [`ideal-placement` component property](#ideal-placement-component-property)
  - [J2 — Seed GPIO Breakout (Issue #3)](#j2--seed-gpio-breakout-issue-3)
    - [Pin assignment deferred to PCB layout](#pin-assignment-deferred-to-pcb-layout)
  - [Silkscreen Artwork (Issue #4)](#silkscreen-artwork-issue-4)
  - [Daughterboard Architectural Invariant](#daughterboard-architectural-invariant)
- [Part 1: Op-Amp Gain-Staged Audio Input](#part-1-op-amp-gain-staged-audio-input)
  - [Design Objectives](#design-objectives)
  - [Changes vs. Rev 1](#changes-vs-rev-1)
  - [Codec Voltage Budget](#codec-voltage-budget)
  - [Signal Path](#signal-path)
  - [Op-Amp Selection: OPA1656](#op-amp-selection-opa1656)
  - [Fixed Gain Selection (R_fb = 12kΩ)](#fixed-gain-selection-r_fb--12kω)
  - [Output Series Resistor (3.3kΩ)](#output-series-resistor-33kω)
  - [Symmetric Clamp](#symmetric-clamp)
    - [Reference Divider Calculations](#reference-divider-calculations)
    - [Fault Analysis](#fault-analysis)
    - [Signal Interaction at Normal Levels](#signal-interaction-at-normal-levels)
    - [Clip Indicator](#clip-indicator)
    - [Tolerance Analysis](#tolerance-analysis)
  - [Anti-Alias Filter at Seed Input](#anti-alias-filter-at-seed-input)
  - [Daughterboard Interface (Input Stage)](#daughterboard-interface-input-stage)
    - [Signal-integrity notes for the input-stage cable](#signal-integrity-notes-for-the-input-stage-cable)
  - [Components](#components)
  - [Power Budget (input-stage contribution)](#power-budget-input-stage-contribution)
  - [Performance Summary](#performance-summary)
    - [LPF corner across pot travel](#lpf-corner-across-pot-travel)
  - [Stability Analysis](#stability-analysis)
    - [Feedback Loop](#feedback-loop)
    - [BJT Parasitic Capacitances](#bjt-parasitic-capacitances)
    - [Clamp Transition Transients](#clamp-transition-transients)
    - [Op-Amp Decoupling](#op-amp-decoupling)
  - [Layout Guidelines](#layout-guidelines)
    - [Component Placement](#component-placement)
    - [Trace Routing](#trace-routing)
  - [Ground Rules](#ground-rules)
  - [Verification](#verification)
- [Part 2: MIDI Section](#part-2-midi-section)
  - [Design Objectives](#design-objectives-1)
  - [Topology (unchanged from Rev 1)](#topology-unchanged-from-rev-1)
  - [Changes vs. Rev 1](#changes-vs-rev-1-1)
  - [Components (Rev 2, unchanged from Rev 1 except footprint fix)](#components-rev-2-unchanged-from-rev-1-except-footprint-fix)
  - [Verification](#verification-1)
- [Part 3: Output Section](#part-3-output-section)
  - [Design Objectives](#design-objectives-2)
  - [Changes vs. Rev 1](#changes-vs-rev-1-2)
  - [Signal Path](#signal-path-1)
  - [Op-Amp Gain Stage (OPA1656)](#op-amp-gain-stage-opa1656)
    - [Calibration procedure](#calibration-procedure)
    - [Reconstruction Low-Pass Filter (C_fb across R_fb)](#reconstruction-low-pass-filter-c_fb-across-r_fb)
  - [Output Level Pot](#output-level-pot)
    - [Impedance behaviour](#impedance-behaviour)
  - [Daughterboard Control Header](#daughterboard-control-header)
    - [Architectural invariant (recap from Part 0)](#architectural-invariant-recap-from-part-0)
    - [Signal inventory](#signal-inventory)
    - [Connector](#connector)
    - [Pin assignment](#pin-assignment)
    - [Signal-integrity notes](#signal-integrity-notes)
  - [THAT1646 Balanced Driver](#that1646-balanced-driver)
  - [Phantom-Power Protection Diodes](#phantom-power-protection-diodes)
  - [Rail Protection (TVS per rail)](#rail-protection-tvs-per-rail)
  - [Components](#components-1)
- [Part 4: Power Section](#part-4-power-section)
  - [Design Objectives](#design-objectives-3)
  - [Topology](#topology)
  - [Changes vs. Rev 1](#changes-vs-rev-1-3)
  - [Power Budget (±12V Rails)](#power-budget-12v-rails)
  - [+5V Rail (TPS54302 buck)](#5v-rail-tps54302-buck)
  - [Panel Power Switch (J_SW)](#panel-power-switch-j_sw)
  - [Grounding (unchanged from Rev 1)](#grounding-unchanged-from-rev-1)
  - [Components](#components-2)
  - [Layout Guidelines](#layout-guidelines-1)
    - [Buck converter (TPS54302) — Issue #1 rework](#buck-converter-tps54302--issue-1-rework)
    - [±12V DC/DC module (TMR 3-1222)](#12v-dcdc-module-tmr-3-1222)
    - [General](#general)
  - [Verification](#verification-2)
- [Appendix: Other Clamp Designs Considered](#appendix-other-clamp-designs-considered)
  - [BAV99 Passive Diode Clamp](#bav99-passive-diode-clamp)
  - [Diode Substitution (1N4148, BAT54)](#diode-substitution-1n4148-bat54)
  - [Post-Clamp Feedback Tap (Active Limiting)](#post-clamp-feedback-tap-active-limiting)
    - [Normal-Level Performance (+4 dBu)](#normal-level-performance-4-dbu)
    - [Failure Mode: Reference Pumping Under Overdrive](#failure-mode-reference-pumping-under-overdrive)
    - [References](#references)

---

# Part 0: Design-Wide Changes

Cross-cutting decisions and housekeeping for Rev 2 — concerns that don't
belong to a specific functional block. Each subsection stands alone.

## Schematic Conventions

### `ideal-placement` component property

Every component in the schematic gets an `ideal-placement` custom property
(free-text). It records any non-obvious layout requirement — proximity to a
specific pin, trace-length constraint, loop-area rule, thermal concern —
that the layout engineer should respect. Examples:

* `R_fb`: "adjacent to OPA1656 pin 1 and pin 2; short summing-junction
  trace, no parallel run to pin 1 output"
* `C6`: "directly at U2 Vin and PGND pads, input-cap loop < 20 mm²"
* `Q1` (clamp BJT): "close to Seed input pin; short traces to emitter"

Components with no layout constraint leave the property empty. The
property never holds behavioural spec — values, footprints, and references
live in their normal KiCad fields.

## J2 — Seed GPIO Breakout (Issue #3)

Rev 1's J2 declared a `Conn_02x12_Odd_Even` symbol and
`PinHeader_2x12_P2.54mm_Vertical_SMD` footprint, but the physical Rev 1
board shipped a 2×5. Rev 2 standardises on a **2×12 vertical through-hole
pin header** (2.54 mm pitch) and commits symbol, footprint, and BOM to the
same truth.

J2 carries:

* `+5V`, `+3V3D`, and `DGND` — digital supply rails and return for user
  extensions. Both rails available so downstream circuits can pick whichever
  matches their logic family.
* Every Seed GPIO not already committed to audio I/O (ADC/DAC pins), MIDI
  UART (UART_RX/TX), or USB (D+/D−, VBUS). No Seed GPIO is omitted unless
  it's already in use.

(Analog ±12V rails distribute via the existing dedicated power header J1 —
see Part 4. They do not appear on J2 or on the daughterboard header.)

### Pin assignment deferred to PCB layout

The schematic declares nets for each Seed GPIO brought out (`SEED_D0`,
`SEED_D1`, ..., `+3V3D`, `DGND`) but **leaves J2's pin-to-net mapping
flexible**. Pin-to-net assignment is decided at PCB layout time to
minimise via count and trace crossings between the Seed and J2. Either
use KiCad pin-swap on the J2 symbol or edit the symbol's pin numbers
after routing — the spec is that schematic pin order is not authoritative
for this connector.

## Silkscreen Artwork (Issue #4)

Candidate top-silk content, to be decided and placed at PCB layout time
(not committed in the schematic):

1. Board name: "Daisy Studio"
2. Revision marker: "Rev 2"
3. Author handle / signature
4. Daisy illustration — contingent on trademark / licensing review
5. GitHub URL: `github.com/squeedee/daisy-studio`
6. Board version date

Treated as suggestions, not requirements — revisit during layout once the
board outline is stable and free silk real estate is known.

## Daughterboard Architectural Invariant

### Design intent: Daisy Studio as a carrier

Daisy Studio is a **flexible carrier**. The main PCB (audio I/O, power,
MIDI, Daisy Seed interface, gain stages, clamps, comparator) is identical
across every form factor. The user-facing controls live on a separate
**daughterboard** connected to the main PCB through a single 20-way
header. Target form factors include:

* **Keybed integration** — controls in a side or top strip of the keybed
  enclosure.
* **Desktop module** — top-panel controls some distance above the main
  PCB.
* **Rack module** — 3U/1U front-panel controls, offset front-to-back from
  the main PCB.

The daughterboard's layout, pot/LED selection, and faceplate ergonomics
are user-defined per form factor. The main PCB commits only to the header
pinout (see **Part 3 → "Daughterboard Control Header"**) and to the
fully-passive constraint below.

### What crosses the header

Daughterboard PCBs are **fully passive**. They populate only:

* Input level pots (10 kΩ log, 1 per channel)
* Output level pots (10 kΩ log, 1 per channel)
* Clip LEDs (1 per channel)

The clip-threshold trim pots are **not** on the daughterboard. They are
calibration trims (set once at bring-up, locked with paint), not
user-facing controls — they live on the main PCB next to the comparator,
in the same category as the `R_fb_trim` output gain trim. This keeps a
high-Z comparator input off the header and saves four pins.

No ICs, no raw power rails, and no high-impedance feedback nodes cross
the header. The header carries only:

* Low-impedance audio signals (op-amp outputs and pot-wiper returns)
* AGND returns (interleaved with signal pins)
* Current-limited LED drive pairs (`CLIP_LED_A_*` is 1 kΩ-limited from
  +12 V on the main PCB, max ~12 mA; `CLIP_LED_K_*` is the LM2903
  open-collector output)

This invariant simplifies user daughterboard design: shorting any two
daughterboard signals together will not damage the main PCB. The tradeoff
is that users can't draw power off the header for their own active
circuits — out of scope for Rev 2's "attenuators + clip indicators" panel
goal. User extensions that need active circuitry use J2 (Seed GPIO
breakout) instead, where +5V, +3V3D, DGND and GPIO are available.

### Connector — one footprint, two build modes

The main PCB commits to a **2×10, 2.54 mm pitch, through-hole footprint**
for the daughterboard header (20 pins). The signal inventory needs 18;
the bottom two pins (19/20) are tied to AGND for a small extra return
guard. 2×10 is chosen over 2×9 for sourcing — 20-pin IDC headers and
matching ribbon cable are stocked everywhere; 18-pin parts are less
common. That single footprint supports two build modes without redesign:

* **Cable-mount (default for keybed / desktop / rack):** populate the
  main-PCB side with a shrouded IDC header (e.g. Samtec TSS-110-01-G-D)
  and connect via 20-way IDC ribbon to a matching socket on the
  daughterboard. Cable length tuned to the form factor (≤ 150 mm
  comfortable; see Part 3 SI notes).
* **Stack-mount (for prototypes / freestanding builds):** populate with a
  Samtec flex-stacking post system
  ([samtec.com/flex-stacking](https://www.samtec.com/flex-stacking/)) and
  socket the daughterboard directly above the main PCB at a chosen height.
  No cable.

The pinout is the same in both modes. AGND interleave on every audio pair
(see Part 3) is preserved by both ribbon and stacking — that's the
load-bearing constraint that rules out FFC/FPC and other low-density
flex-cable formats.

# Part 1: Op-Amp Gain-Staged Audio Input

## Design Objectives

1. Maximise ADC headroom at +4 dBu (standard studio operating level).
2. Continuous trim from +4 dBu up to +24 dBu peak via a single pot per channel.
   Gain is set by a **fixed op-amp stage** on the main PCB; the user pot is a
   **passive attenuator after the op-amp** on the daughterboard — architecturally
   symmetric with the Part 3 output stage.
3. Protect the PCM3060 codec. This design is only validated for Rev7 Seeds with the PCM3060 and input schematic as
   published [here](https://daisy.nyc3.cdn.digitaloceanspaces.com/products/seed/ES_Daisy_Seed_Rev7.pdf)

## Changes vs. Rev 1

* **Gain-staging architecture:** variable-gain op-amp (pot in feedback) →
  **fixed-gain OPA1656 + passive pot downstream**. Noise gain no longer
  varies with user level, op-amp loop phase margin is independent of pot
  position, and the inverting summing junction stays on the main PCB.
* **Fixed gain:** R_fb = 12 kΩ (gain 1.2×, +1.58 dB). Chosen to keep
  +24 dBu peaks within the ±11 V rails on ±12 V supplies.
* **Signal clamp:** passive BAV99 → **complementary BJT clamp**
  (2N3904/2N3906) against per-channel ±1.565 V references. Sharper knee
  (NF ≈ 1.24 vs 1.82), β-reduced reference pumping, 164 mV margin to the
  4.8 V codec abs-max in the worst tolerance corner.
* **Clip indicator (new):** LM2903 comparator monitors Seed_In against a
  per-channel trim-pot threshold and drives an LED through a 1 kΩ
  current-limit on the main PCB.
* **Anti-alias cap (C_aa):** 1 nF C0G at the Seed pin (was 2.2 nF in an
  earlier Rev 2 draft; 1 nF keeps the LPF corner above 27 kHz even at
  pot-mid max source impedance).
* **Output series resistor (R_out):** 3.3 kΩ, raised from Rev 1's 2.2 kΩ
  to cap clamp current under pathological overdrive.
* **Daughterboard:** user pot, trim pot, and LED now live on a separate
  passive PCB per the Part 0 architectural invariant.
* **Op-amp:** OPA1656 dual (SOIC-8). Same part and decoupling scheme as
  the Part 3 output stage.

## Codec Voltage Budget

The PCM3060 codec on the Daisy Seed has an internal AC coupling capacitor and a 2.5V
V_COM bias. The Seed Rev 7 input network additionally attenuates the Seed input pin's
AC signal before it reaches the codec (series resistor + 47 kΩ shunt after the
AC-coupling cap). All voltages below are measured at the codec; the "Seed pin
equivalent" column back-translates through this network, so Seed pin ±2.04V
corresponds to 3.0 V p-p at the codec. Three operating zones:

| Zone   | Target range V(codec)                               | Sim range V(codec)                                  | Seed pin equivalent | Design intent                                                             |
|--------|-----------------------------------------------------|-----------------------------------------------------|---------------------|---------------------------------------------------------------------------|
| Signal | 1.0V to 4.0V (3V p-p nom)                           | 1.00V to 4.00V (3.00V p-p, sim-verified, THD 0.05%) | ±2.04V              | Full ADC utilisation. No BJT conduction.                                  |
| Clamp  | 4.0V to 4.64V                                       | 4.00V to 4.64V (worst tolerance corner)             | ±2.04V to ±2.92V    | Progressive BJT conduction limits overdrive. Keep this as low as possible |
| Damage | -0.3V to +4.8V (Vcc + 0.3V = 4.8V, LDO Vcc is 4.5V) | Not reached (worst case 4.64V, 164mV margin)        | > ±3.0V             | Must never be reached.                                                    |

Design goals:

1. The 3V p-p full-scale signal must remain entirely below the clamp circuit’s
   start-of-knee — zero clamp conduction at nominal operating level.
2. The hard clamp (full clamp conduction under fault current) targets 4.5V at the
   codec, providing maximum overdrive margin above 3V p-p without approaching the
   absolute maximum rating.
3. The gape between the top of the "Clamp" zone and the "Damage" zone should be maximised without encroaching on the
   Signal Zone

Tolerance validation (5-corner sim, `sim/input/amp-atten-bjt-tolerance.asc`):
Signal zone stays clean (THD 0.05%) across all corners at pk=0.26 full-scale;
pathological overdrive (+24 dBu at pot max) reaches codec_max = 4.64V in the
worst corner (CLAMP_LOOSE: rails +5%, R_ref at tolerance max) — 164 mV margin
to 4.8V damage ceiling.

## Signal Path

```
                                                  ┌──────────── main PCB ────────────┐
Balanced in → THAT 1246 (Vout) ── R_in (10kΩ) ──┬── OPA1656 inv-input (−)             │
                  │ (Sense, pin 5) ─────────────┘    ↑                                 │
                  │                                 R_fb 12kΩ fixed                    │
                  └── Sense closes feedback past R_in (remote / Kelvin)                │
                                                                                      │
        ┌──────── header ────────┐                                                    │
        │  IN_OPA  ──────────────┼─────── IN_OPA (main, OPA_Out)                      │
        │                        │                                                    │
        │  10kΩ log pot          │                                                    │
        │  (3-term divider)      │                                                    │
        │                        │                                                    │
        │  wiper ────────────────┼─────── IN_WIPER (main) → R_out (3.3kΩ)             │
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

**Sense routing — remote / Kelvin to the OPA inverting node.** Pin 5 (Sense)
is **not** tied at the IC pad; it runs as a separate trace to the OPA1656
inverting input — i.e. to the far side of `R_in`, the same node as `R_fb`'s
input-side terminal. This closes the THAT1246's internal output-buffer
feedback loop *past* `R_in`, so any voltage drop across `R_in` (trace
resistance and the 1% resistor tolerance itself) is compensated by the
THAT1246 rather than appearing as a gain error at the OPA. Sense is high-Z
into the THAT1246's internal feedback amp, so no loading concern; layout
keeps the Sense trace tight against AGND for shielding and physically
separate from the Vout trace (no piggyback). Pin 6 (Vout) routes only to
`R_in`'s near terminal.

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
the same part (and same decoupling scheme) used in the Part 3 output stage.

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

## Output Series Resistor (3.3kΩ)

A 3.3kΩ resistor between the pot wiper (returning from the daughterboard) and
the clamp node at the Seed input pin limits fault current to a level the clamp
reference divider can absorb. During normal operation, the Seed's 13.6kΩ input
impedance draws minimal current through the 3.3kΩ — the signal loss
(3.3kΩ / 16.9kΩ ≈ 20%) is baked into the calibration of the user pot position.

During fault conditions (op-amp clipping at ±11V, pot wiper at CW terminal),
the clamp pulls the Seed pin to V_ref + Vbe ≈ 1.565V + 0.7V = 2.26V, and the
resistor limits current to:

    (11V − 2.26V) / 3.3kΩ = 2.65mA

Raised from the Rev 1 / early Rev 2 value of 2.2kΩ specifically to reduce
clamp current under pathological overdrive — lower Ic into the BJT caps the
effective Vbe saturation peak, which directly sets codec_max at hard clamp.
With the pot wiper anywhere between CW and CCW, the pot's internal series
resistance (0–2.5kΩ, peak at mid-rotation) adds to R_out, reducing fault
current further. The worst case is pot at CW (wiper shorted to OPA_Out,
full 2.65 mA).

## Symmetric Clamp

The clamp sits at the Seed pin, after the 3.3kΩ series resistor. Per-channel resistive
dividers from the ±12V analog supply establish independent positive and negative reference
rails (avoiding crosstalk). Ceramic capacitors (47µF MLCC) hold the references stiff at
audio frequencies. A complementary BJT pair (2N3906 PNP + 2N3904 NPN, both SOT-23) per channel
clamps the signal to these rails:

```
Per channel:

            (+1.565V)                  (-1.565V)
+12V ── 10kΩ ──┬── 1.5kΩ ── AGND ── 1.5kΩ ──┬── 10kΩ ── -12V
               │                            │
             47µF                         47µF
               │                            │
             AGND                         AGND

Per channel (BJT clamp):

              +1.565V ref ── Base (Q1, PNP 2N3906)
                                │
R_out ──────────────── Emitter ──┬── Seed pin
                                │
              -1.565V ref ── Base (Q2, NPN 2N3904)

              Q1 Collector → AGND
              Q2 Collector → AGND

Clip indicator (per channel):

              Seed_In ─────────── Comparator inv- input
              Trim pot (AGND to +VCLAMP_*) ── Comparator non-inv+ input  (threshold, 0V to +1.565V)
              +12V → 1kΩ → LED anode; LED cathode → Comparator output (open collector)
```

Q1 (PNP) conducts when the signal exceeds V(+VCLAMP_*) + Vbe, sinking current
from Seed_In through the transistor to AGND. Q2 (NPN) conducts when the signal
falls below V(-VCLAMP_*) − Vbe, sourcing current from AGND into Seed_In. The transistors'
current gain (β≈200) means only Ic/β flows through the reference divider base
connection, largely eliminating reference pumping under overdrive. The base-emitter
forward ideality factor (NF≈1.24) provides a sharper clamp knee than diode
alternatives (BAV99 N=1.82). See "Other Clamp Designs Considered" appendix for the
investigation that led to this choice.

### Reference Divider Calculations

    V_ref = 12V × 1.5kΩ / (10kΩ + 1.5kΩ) = 1.565V
    R_th  = 10kΩ ∥ 1.5kΩ = 1304Ω
    Quiescent: 12V / 11.5kΩ = 1.04mA per divider

The divider was dimensioned so the worst-case-tight tolerance corner (rails
−5%, R at 1%) still keeps codec_pp knee above 3.15V — clean full-scale
preserved across all corners — while the worst-case-loose corner (rails +5%,
R at 1% max) keeps codec_max under hard clamp below the 4.8V damage ceiling
with 164 mV margin.

At 20Hz (worst case for capacitor impedance):

    Z_cap = 1 / (2π × 20Hz × 47µF) = 169Ω
    Z_eff = 1304Ω ∥ 169Ω = 150Ω

### Fault Analysis

Under fault conditions (op-amp clipping at ±11V), the clamp current flows through the
BJT collector to ground (or -12V via the LED). Only the base current loads the
reference divider:

    I_clamp = (11V − V_clamp) / 3.3kΩ ≈ 2.7mA
    I_base  = I_clamp / β ≈ 2.7mA / 200 = 13.5µA
    ΔV_ref  = I_base × R_th = 13.5µA × 1304Ω = 18mV  (negligible)

SPICE simulation (LTspice, `sim/input/amp-atten-bjt-tolerance.asc`, 5-corner
× 3-testcase sweep with the fixed-R_fb + 10k/1.5k divider + R_out=3.3k
topology) shows **codec_max = 4.64V worst-case — 164mV margin** to the 4.8V
absolute maximum, under pathological +24 dBu input with pot at CW max and
the CLAMP_LOOSE corner (rails +5%, R_ref at 1% max). At the nominal full-scale
operating point (+24 dBu, pk=0.26) the signal stays under 3 Vpp at the codec
across all five corners with THD 0.05%.

### Signal Interaction at Normal Levels

At the ±2.04V signal peak at the Seed pin (3V p-p at the codec, 100% ADC
utilisation), the BJT base-emitter bias is V_peak − V_ref = 2.04 − 1.565 =
0.475V. With 2N3904/2N3906 model parameters (NF≈1.24), the collector
current at this bias is negligible — the sharper knee (NF=1.24 vs N=1.82
for BAV99) means less sub-threshold conduction, sim-confirmed as THD 0.05%
at the clean ceiling across all tolerance corners.

### Clip Indicator

A comparator monitors Seed_In directly and drives the LED when the signal peak
exceeds an adjustable threshold. This approach was chosen after prototype testing
showed that monitoring Q1's collector voltage is impractical — the onset voltage
change at Q1.C is only millivolts above the -12V rail, indistinguishable from supply
ripple.

The comparator's inverting input connects to Seed_In. A trim pot between AGND
and `+VCLAMP_L` / `+VCLAMP_R` (0V to +1.565V) sets the threshold on the
non-inverting input. When the positive signal peak exceeds the threshold,
V(inv) > V(non-inv) and the
open-collector output pulls low, lighting the LED. At audio frequencies the LED
flickers faster than the eye can see — dim glow at light clipping, bright at
heavy clipping.

The full trim pot range (0V to 1.565V) corresponds directly to the useful signal
range at Seed_In, giving fine adjustment with no dead zone. The threshold is set
during calibration to the onset of audible clipping.

A single LM2903 dual comparator covers both channels, running on the existing ±12V
rails. The LM2903's open-collector output wires naturally against the +12V rail to
drive the LED (see diagram above) — when the output pulls low, the LED lights; when
it floats, the LED has no current path and is cleanly off with no reverse bias on
the LED junction. Fast response (~1.3µs) cleanly tracks individual signal peaks at
audio frequencies.

    Seed_In signal range:   0V to ±2.04V (clean), ±2.92V (clamp worst tolerance)
    Threshold range:        0V to +1.565V (trim pot)
    LED behaviour:          off below threshold, proportional glow above

### Tolerance Analysis

With ±5% supply tolerance (conservative; the Rev 2 TMR 3-1222 is
regulated to ±2% — the sim analysis below stays worst-case under the
looser bound) and ±1% resistors:

| Parameter | Nominal | Min (low rail, high R_top, low R_bot) | Max (high rail, low R_top, high R_bot) |
|-----------|---------|---------------------------------------|----------------------------------------|
| V_ref     | 1.565V  | 1.461V                                | 1.673V                                 |

Sim-verified 5-corner × 3-testcase sweep (`sim/input/amp-atten-bjt-tolerance.asc`,
corners = TYP / OPA_CLIP / CLAMP_TIGHT / CLAMP_LOOSE / GAIN_LOW):

* **+4 dBu, pk=1.0 (nominal pro, pot max):** clean across all corners, THD
  ~0.07%, codec_pp 1.23V (41% ADC).
* **+24 dBu, pk=0.26 (hot signal at full-scale calibration):** codec_pp
  2.82–2.93V across all corners, THD 0.05%. OPA does not rail-clip even at
  OPA_CLIP corner (max gain + min rails).
* **+24 dBu, pk=1.0 (pathological — hot signal mis-set at pot max):**
  codec_max ranges 4.49–4.64V. Worst corner CLAMP_LOOSE (rails +5%, R_ref
  at 1% max) gives 4.64V — **164 mV margin** to the 4.8V damage ceiling.

The ±12V rails carry the clamp-divider base-current shift (~13 µA per
active clamp) and the continuous divider quiescent (~1 mA per side) with
negligible rail sag — well within the TMR 3-1222's ±125 mA per-rail
rating.

## Anti-Alias Filter at Seed Input

A **1nF C0G capacitor from Seed_In to AGND**, placed immediately at the
Seed input pin (after the BJT clamp node), forms a single-pole low-pass
with the series resistance between the OPA_Out and the Seed pin:

    R_series = Z_pot_wiper + R_out
    Z_pot_wiper = 0 to 2.5 kΩ (peak at mid-rotation of the 10kΩ user pot)
    R_out = 3.3 kΩ
    → R_series varies from 3.3 kΩ (pot at CW or CCW) to 5.8 kΩ (pot at mid)

    f_LPF = 1 / (2π × R_series × 1nF)
          = 48.2 kHz (pot at ends) → 27.4 kHz (pot at mid)

The LPF corner stays safely above the audio band across pot travel. This
attenuates wideband noise from the OPA1656 (noise bandwidth extends into
the MHz range due to the 53 MHz GBW) and any out-of-band content above the
audio band before it reaches the PCM3060's sigma-delta ADC. The Seed's own
internal input network (R4/C1) contributes additional filtering upstream of
the codec but is insufficient on its own for this purpose.

**Why 1nF and not the earlier 2.2nF value:** with the old architecture
(fixed R_out, no pot in the series path), 2.2nF gave a 32.9 kHz corner. In
the new architecture the pot wiper source impedance adds to R_out, so 2.2nF
would sag the corner well into the audio band at mid-rotation — not
acceptable. With Option E's R_out=3.3kΩ, 1nF gives 48/27 kHz worst-case
across pot travel, still safely above audio band.

**Placement:** 0402 or 0603 C0G (NP0) MLCC, directly at the Seed input pin,
short trace from the pin to the cap and short return to the analog ground
pour. Do not place it on the daughterboard or at the op-amp output — the
R_out resistor plus pot wiper Z is what makes the filter work, so the cap
must be on the Seed side of R_out.

Value tradeoff (corner frequencies at worst-case pot-mid R_series = 5.8kΩ
with R_out = 3.3kΩ):

| C_aa  | f_LPF (pot ends) | f_LPF (pot mid)    | Notes                                            |
|-------|------------------|--------------------|--------------------------------------------------|
| 680pF | 70.9 kHz         | 40.4 kHz           | Wider, less noise rejection                      |
| 1nF   | 48.2 kHz         | 27.4 kHz           | **Chosen** — clear of audio band across all pot positions |
| 1.5nF | 32.1 kHz         | 18.3 kHz           | Unacceptable — audible rolloff at pot mid        |
| 2.2nF | 21.9 kHz         | 12.5 kHz           | Unacceptable — audible rolloff at pot mid        |

## Daughterboard Interface (Input Stage)

The input level pot, clip-threshold trim pot, and clip LED live on the
daughterboard per the Part 0 passive-only invariant. The 1 kΩ LED
current-limit resistor and all active parts (OPA1656, LM2903, clamp BJTs,
reference dividers) stay on the main PCB; only passive controls and the
LED cross the header.

The input level pot is a 10 kΩ log-taper voltage divider downstream of the
op-amp — architecturally identical to the Part 3 output pot (same part,
same wiring). See Part 3 "Output Level Pot → Impedance behaviour" for the
analysis of constant op-amp load and wiper-position-dependent source
impedance that applies to both stages.

Input-stage signals on the header (see **Part 3 "Daughterboard Control
Header"** for the canonical L+R pinout):

* `IN_OPA_L` / `IN_OPA_R` — op-amp output (main PCB, low-Z) to the pot CW
  terminal.
* `IN_WIPER_L` / `IN_WIPER_R` — pot wiper back to main PCB (moderate-Z: 0
  to ~2.5 kΩ depending on pot position) into R_out.
* `AGND` — pot CCW terminal (proper mute leg) + signal-pair return.
* `+VCLAMP_L` / `+VCLAMP_R` — clamp-reference rail, to the clip-threshold
  trim pot top.
* `IN_THRESH_L` / `IN_THRESH_R` — trim-pot wiper, back to the comparator
  non-inverting input.
* `CLIP_LED_A_L` / `CLIP_LED_A_R` — current-limited LED anode drive (1 kΩ
  to +12 V on main PCB; max ~12 mA, safe to short to any other
  daughterboard net).
* `CLIP_LED_K_L` / `CLIP_LED_K_R` — LED cathode, driven by the LM2903
  open-collector output.

Both audio legs (`IN_OPA_*` and `IN_WIPER_*`) are low-impedance — op-amp
drives one end directly, pot wiper source impedance peaks at 2.5 kΩ at
mid-rotation on the other. No summing-junction / high-Z feedback node
leaves the main PCB.

### Signal-integrity notes for the input-stage cable

* Pair each signal with an adjacent AGND return pin on the header
  (enforced by the Part 3 pinout). Loop area stays small across the
  ribbon.
* The `IN_WIPER_*` line is moderate-Z (up to 2.5 kΩ at pot mid). Keep it
  physically separate from `CLIP_LED_K_*` (the comparator open-collector
  output, which carries fast digital edges during clipping). The Part 3
  pinout places these pairs at opposite ends of the header.
* Interaction with C_aa: C_aa sees R_out + wiper Z as its series R. The
  LPF corner varies from 48 kHz (pot ends) to 27 kHz (pot mid) — all
  safely above the audio band. See "Anti-Alias Filter at Seed Input"
  above.
* Cable length: ≤ 150 mm comfortable; ≤ 50 mm conservative. No hard
  upper bound driven by inverting-input sensitivity (it doesn't leave
  the main PCB).

## Components

**Per channel (main PCB):**

* 10kΩ input resistor (R_in, 0805 1%)
* 12kΩ feedback resistor (R_fb, 0805 1%) — fixed, sets op-amp gain 1.2×
* 3.3kΩ series output resistor (R_out, 0805 1%)
* 1× 2N3906 PNP transistor, SOT-23 (positive clamp)
* 1× 2N3904 NPN transistor, SOT-23 (negative clamp)
* 2× 10kΩ resistors, 1% (R1, reference dividers)
* 2× 1.5kΩ resistors, 1% (R2, reference dividers)
* 2× 47µF MLCC, 1206 or 1210, X5R/X7R (reference rail filtering)
* 1× 1nF C0G MLCC, 0402 or 0603 (C_aa, anti-alias at Seed input)
* 1× 1kΩ resistor, 0805 1% (LED current limit, +12V → `CLIP_LED_A_*`
  header pin; the daughterboard sees only the current-limited node)

**Per channel (daughterboard — user-swappable controls):**

* 1× 10kΩ log-taper pot — user input level control (three-terminal voltage divider)
* 1× LED (clip indicator)
* 1× 10kΩ trim pot (clip threshold, AGND to `+VCLAMP_*`; wiper to
  comparator non-inverting input)

**Shared:**

* 1× OPA1656 dual op-amp (SOIC-8)
* 1× LM2903 dual comparator (clip indicator, both channels)
* 2× 100nF MLCC, 0402 or 0603 (OPA1656 supply decoupling, V+ and V-)
* 2× 1nF MLCC, 0402 (OPA1656 supply decoupling, VHF, V+ and V-)
* 2× 100nF MLCC, 0402 or 0603 (LM2903 supply decoupling, V+ and V-)

## Power Budget (input-stage contribution)

| Source                   | Current (±12V) | Power     |
|--------------------------|----------------|-----------|
| 2× THAT 1246             | ~16 mA         | 384 mW    |
| OPA1656 (both channels)  | 7.8 mA         | 187 mW    |
| Clamp reference dividers | 4.3 mA         | 52 mW     |
| LM2903 comparator        | ~1 mA          | 24 mW     |
| **Input-stage subtotal** | **~29 mA**     | **647 mW** |

This subtotal rolls into the Part 4 whole-board power budget alongside the
output-stage draw. The ±12V module selection (Traco TMR 3-1222) is sized
against that total, not this line-item subtotal — see Part 4 for the full
sizing argument.

## Performance Summary

Sim-verified signal levels (`sim/input/amp-atten-bjt.asc` pk sweep,
`amp-atten-bjt-tolerance.asc` 5-corner × 3-testcase sweep) for the new
architecture with fixed R_fb = 12kΩ (gain 1.2×) and 10kΩ log pot wired as
voltage divider. Pot position `pk` is the wiper fraction from CCW
(pk=0=mute) to CW (pk=1.0=max):

| Input level      | OPA_Out   | Pot setting           | codec_pp       | ADC util | THD   |
|------------------|-----------|-----------------------|----------------|----------|-------|
| +4 dBu nominal   | 2.08 Vpp  | 1.0 (max)             | 1.23 Vpp       | 41%      | 0.07% |
| +24 dBu peak     | 20.9 Vpp  | **~0.275**            | 3.00 Vpp       | 100%     | 0.05% |
| +24 dBu, pot max | 20.9 Vpp  | 1.0 (mis-set, worst)  | clamp 4.64V    | protected | 30%  |
| Any, pot mute    | n/a       | 0.0 (CCW)             | 0V             | muted    | —     |

Full-scale calibration point (hot signal input, user dial set for 3 Vpp at
the codec) is `pk ≈ 0.275`. The sweep from pk=0.1 to pk=0.3 shows signal
monotonically ramping then rolling over into the clamp knee between
pk=0.28 and pk=0.30 (180 mV margin between 3 Vpp clean and clamp onset).

### LPF corner across pot travel

With R_out = 3.3kΩ and C_aa = 1nF, the single-pole LPF formed at the Seed
input has its corner determined by (R_out + Z_wiper) × C_aa:

* Pot at either end: R_series = 3.3kΩ, f_LPF = 48 kHz
* Pot at mid (worst): R_series = 3.3kΩ + 2.5kΩ = 5.8kΩ, f_LPF = 27 kHz

Both safely above audio band. Sim-verified flat across all pot positions.

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
of wiper position — voltage-divider wiring) and, through that pot, the 3.3kΩ
R_out plus clamp bias. Net load is approximately 5–6kΩ resistive. Benign, no
reactive component at the output node.

### BJT Parasitic Capacitances

The 2N3904/2N3906 present Cbe ≈ 4–5pF and Ccb ≈ 3–4pF at the Seed_In node. Behind
the 3.3kΩ series resistor, the associated pole is at:

    f_pole = 1 / (2π × 3.3kΩ × 10pF) ≈ 4.8 MHz

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
* **Daughterboard header pins for input pot:** The `IN_OPA_*` pin should
  sit close to the op-amp output (pin 1); the `IN_WIPER_*` pin should sit
  close to R_out. Adjacent AGND pins on both pairs keep return loop area
  small.
* **R_out (3.3kΩ):** Place close to the `IN_WIPER_*` header pin (not at
  the op-amp output, as in Rev 1 and the older Rev 2 drafts). The pot
  wiper returns via cable and feeds directly into R_out; the clamp and
  C_aa are on the Seed side of R_out.
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
* **THAT1246 Sense trace (pin 5):** Route as a *separate* trace from
  THAT1246 pin 5 to the OPA inverting node (the R_in / R_fb junction at op-
  amp pin 2). Do **not** piggyback on the Vout trace; they share endpoints
  electrically through R_in but must be physically distinct copper, with the
  Sense trace tight against AGND for shielding. High-Z node, so vulnerable
  to coupling — keep it short and away from the op-amp output trace and the
  ±12V supplies.
* **Analog ground pour:** Continuous copper pour under the OPA1656 and the entire
  signal path from R_in to Seed_In. No splits or slots under the op-amp. Digital
  ground (Seed, USB, MIDI) should not share this pour.
* **Supply traces (±12V):** Route as a pair to the decoupling caps. Avoid long runs
  from the TMR 3-1222 — place the module close to the analog section or use wide
  traces (≥0.5mm).
* **Seed_In to Seed pin:** Short, direct trace. This node carries the clamped signal
  and connects to both BJT emitters, R_out, C_aa, and R4/C1 (Seed input network).
* **C_aa (1nF anti-alias):** Place directly at the Seed input pin, short trace
  from the pin to the cap, short return to the AGND pour under the Seed. The
  filter's R side is R_out plus the pot wiper Z, so the cap must be on the
  Seed end of R_out.

## Ground Rules

All components in this circuit are in the analog signal path and connect to Analog
Ground. The clamp reference dividers derive from the ±12V analog supply
(TMR 3-1222 secondary, Part 4) and terminate at AGND.

## Verification

Sim (LTspice) references:

* `sim/input/amp-atten-bjt.asc` — pk-sweep of the input stage
  (OPA1656 + passive pot + BJT clamp + C_aa). Used for the Performance
  Summary table.
* `sim/input/amp-atten-bjt-tolerance.asc` — 5-corner × 3-testcase sweep
  (TYP / OPA_CLIP / CLAMP_TIGHT / CLAMP_LOOSE / GAIN_LOW) backing the
  Tolerance Analysis subsection (codec_max 4.64 V worst case, 164 mV
  margin).
* `sim/input/feedback-clamp.asc`, `sim/input/thd-plus4db.asc` / `.csv` —
  Appendix investigation of alternative clamp topologies.

Schematic checks:

* `kicad-cli sch export netlist --output /dev/null audio.kicad_sch` —
  parse the input-stage sheet.
* `kicad-cli sch erc audio.kicad_sch` — ERC clean (expect all audio
  nets bonded, no floating clamp bases).

Bench validation (post-board, TODO):

1. +4 dBu / +14 dBu / +24 dBu input at the THAT1246; scope codec-pin
   voltage across the pot travel and compare to the sim's Performance
   Summary.
2. Pathological overdrive (+24 dBu, pot at CW) — verify codec_max stays
   ≤ 4.8 V across a handful of boards.
3. Clip-LED behaviour at threshold pot mid-travel — confirm off below
   threshold, proportional glow above.
4. Audio-band noise floor at Seed_In with input shorted; compare to
   sim's 1.4 µV rms output-noise estimate.

# Part 2: MIDI Section

## Design Objectives

1. Standard MIDI 1.0 IN / OUT / THRU on DIN-5 connectors, galvanically
   isolated on the input per the MIDI 1.0 electrical spec.
2. Fix the Rev 1 optocoupler footprint defect
   ([Issue #6](https://github.com/squeedee/daisy-studio/issues/6)).

## Topology (unchanged from Rev 1)

```
DIN-5 IN ── 220R × 2 ── 1N4148W ── H11L1SM (opto, Schmitt-out) ── MIDI_RX → Seed UART RX
                                         │
                                         └── 270R pull-up to +3V3D
                                         │
                                         └── 33R × 2 ── DIN-5 THRU

Seed UART TX ── MIDI_TX ── 10R ── 33R ── DIN-5 OUT
```

Textbook MIDI 1.0: 5 mA current loop driven at 31.25 kbaud, 220 Ω series
resistors at the DIN-5 IN pins, reverse-polarity protection via a 1N4148W,
H11L1SM Schmitt-trigger optocoupler for edge-clean UART. Output side is
pulled up to +3V3D through 270 Ω (matches the Seed UART RX logic level);
MIDI_THRU buffers the opto output through
a second pair of 33 Ω series resistors to a parallel DIN-5 jack. MIDI OUT
driven directly from the Seed UART TX through a series 33 Ω, with a 10 Ω
to the jack's sink pin.

No signal-path changes for Rev 2.

## Changes vs. Rev 1

* **U4 (H11L1SM) footprint:** current `Package_SO:SO-6_4.4x3.6mm_P1.27mm`
  is wrong for the actual H11L1SM package
  ([Issue #6](https://github.com/squeedee/daisy-studio/issues/6)). Fix:
  verify the correct pad dimensions against the ON Semi H11L1SM datasheet
  and either use a vetted standard footprint or draw a matched one in
  `daisy-studio.pretty`. No schematic change; footprint assignment only.

## Components (Rev 2, unchanged from Rev 1 except footprint fix)

* 3× SDS-50J DIN-5 jack (J_MIDI_IN_1, J_MIDI_OUT_1, J_MIDI_THRU_1)
* 1× H11L1SM optocoupler (U4) — **footprint corrected**
* 1× 1N4148W diode, SOD-123 (D3)
* 2× 220 Ω 0805 (R14, R15) — MIDI IN current limit
* 1× 270 Ω 0805 (R16) — H11L1 output pull-up to +3V3D
* 2× 33 Ω 0805 (R17, R18) — MIDI THRU series
* 1× 33 Ω 0805 (R12) — MIDI OUT series
* 1× 10 Ω 0805 (R13) — MIDI OUT sink series
* 1× 100 nF 0402/0603 MLCC (C9) — H11L1 supply decouple

## Verification

* `kicad-cli sch erc daisy_seed.kicad_sch` — ERC clean.
* Footprint visual check against the ON Semi H11L1SM datasheet pad diagram
  before the board order; confirm pad pitch, size, and land length match.
* Bench: MIDI loopback test (IN → THRU, OUT → external synth) at 31.25
  kbaud once the Rev 2 board is built.

# Part 3: Output Section

## Design Objectives

1. Bring the Daisy Seed's digital full-scale output up to a standard studio peak level
   (~+24 dBu) — as close to rail-to-rail on the ±12V analog supply as headroom allows.
2. Preserve the balanced XLR output and its tolerance to hot-plug mishaps
   (phantom power on the line).
3. Remove the 3.5mm input/output jacks. [Github Issue](https://github.com/squeedee/daisy-studio/issues/11)

## Changes vs. Rev 1

* **Added OPA1656 gain stage** between the Seed and the THAT1646.
  Calibrated mid-trim gain ~9.1× brings the Seed's ~2 V p-p digital
  full-scale up to +24 dBu peak at the XLR — ~20 dB of rail-utilisation
  headroom closed.
* **Added output level pot** (10 kΩ log, passive voltage divider on the
  daughterboard, one per channel). User-facing level control, architecturally
  symmetric with the Part 1 input pot.
* **Added reconstruction LPF** (C_fb = 100 pF C0G across R_fb). Single-pole
  at ~80 kHz, attenuates PCM3060 delta-sigma noise above the audio band per
  Seed Rev 7 community guidance. Sim-verified −0.27 dB at 20 kHz, −22 dB at
  1 MHz.
* **Added ±12 V rail protection** (one SMBJ15CA bidirectional TVS per
  rail, placed on the power sheet near the TMR 3-1222 output —
  consolidated with D1 input over-voltage TVS, single BOM line). Absorbs
  phantom-power back-feed when the gear is powered off and an XLR
  output is plugged into a phantom-enabled mic preamp. See Rail
  Protection → Placement for the trade-off.
* **Removed 3.5 mm in/out jacks** ([Issue #11](https://github.com/squeedee/daisy-studio/issues/11)).
  XLR is the only audio I/O now.
* **Unchanged from Rev 1:** THAT1646 balanced driver and phantom-protection
  SM4004 diodes.

## Signal Path

```
Seed audio out → OPA1656 (inverting, ±12V, calibrated gain + C_fb reconstruction LPF) → Output level pot → THAT1646 balanced driver → clamp diodes → XLR
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

### Reconstruction Low-Pass Filter (C_fb across R_fb)

**Purpose.** The Daisy Seed Rev 7's PCM3060 codec has out-of-band
delta-sigma noise above the audio band. Per the PCM3060 datasheet, the
codec's internal continuous-time RC alone is insufficient "for many
applications" — an external LPF is expected. The Seed carries no
additional reconstruction filter, and a community report on PedalPCB
traced an audible Rev 7 noise-floor issue to this and resolved it with a
post-Seed RC. See
https://forum.pedalpcb.com/threads/terrarium-rev-1-with-daisy-seed-v1-2-rev-7-noise-issue-work-around-applies-to-old-terrarium-rev-1-board-only.21901/
and the PCM3060 datasheet output-filter section.

**Topology.** A single C0G capacitor, C_fb, in parallel with R_fb turns
the inverting gain stage into a 1-pole LPF. DC gain is unchanged; only
the high-frequency behaviour shifts:

    f_c = 1 / (2π × R_fb × C_fb)

No series parts added to the signal path, no change in source impedance
to the THAT1646, and — because the OPA1656 is unity-gain stable at 53 MHz
GBW — no stability margin cost.

**Chosen value: C_fb = 100 pF C0G.** At R_fb_nominal = 20 kΩ, f_c = 80 kHz.

Sim-verified AC sweep (`sim/output/output-lpf.asc`,
`sim/output/output-lpf.csv`; R_in = 2.2kΩ, R_fb = 20kΩ, DC gain = 18.79 dB):

| C_fb       | f_c       | 20 kHz   | 100 kHz  | 500 kHz  | 1 MHz    |
|------------|-----------|----------|----------|----------|----------|
| 47 pF      | 169 kHz   | −0.06 dB | −1.4 dB  | −10.1 dB | −15.8 dB |
| **100 pF** | **80 kHz**| **−0.27 dB** | **−4.2 dB**  | **−16.2 dB** | **−22.1 dB** |
| 220 pF     | 36 kHz    | −1.17 dB | −9.4 dB  | −22.9 dB | −28.9 dB |
| 470 pF     | 17 kHz    | −3.79 dB | −15.6 dB | −29.4 dB | −35.4 dB |

100 pF is the sweet spot: audio band effectively untouched (−0.27 dB at
20 kHz is below audibility), meaningful rejection into the codec noise
band (−22 dB at 1 MHz). 47 pF leaves too much noise through; 220 pF
starts nibbling the audible top octave; 470 pF is audibly dark.

Across the R_fb trim range (15 kΩ → 25 kΩ), f_c at 100 pF varies from
106 kHz (min trim) down to 64 kHz (max trim) — all safely above audio.
After bring-up calibration the trimmer is locked, so per-unit f_c is
effectively fixed.

Phase response is monotonic across all four C_fb values — no peaking, no
ringing. 1-pole inverting LPF behaviour as expected.

**TODO — bench validation on Seed Rev 7.**
Sim confirms the filter does what it's designed to do, but cannot predict
whether 1-pole at 80 kHz provides *enough* attenuation for the PCM3060's
actual noise spectrum (no validated codec noise model available). Bench
procedure:

1. On a Seed Rev 7 unit playing digital silence (all-zero output),
   capture XLR differential output noise with C_fb unpopulated.
2. Repeat with C_fb = 100 pF populated.
3. Compare broadband noise floor and spectral content using a
   192 kHz-capable ADC + FFT or a scope with FFT — look for residual
   spectral content above 40 kHz.
4. If the 1-pole at 80 kHz is insufficient, **escalate to a 2-pole
   Sallen-Key post-gain-stage** (−40 dB/dec past f_c) rather than
   increasing C_fb (which would eat the audio top octave). Larger-scope
   change — deferred until bench data shows the simpler fix is not
   enough.

**Placement.** 0402 or 0603 C0G (NP0) MLCC, directly across R_fb with the
shortest possible traces between the op-amp inverting input node and
output node. C0G chosen for voltage-coefficient stability — X5R/X7R
exhibit voltage-dependent capacitance shift that would modulate f_c with
signal level and introduce low-order distortion in a feedback-path cap.

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

## Daughterboard Control Header

A single 2×10 header (J_DB) carries every user-control signal for both
channels of both stages — input attenuator, output attenuator, and clip
LED. The clip-threshold trim is a main-PCB calibration trim and does
not cross the header (see Part 0 invariant). 18 pins carry signals; the
bottom pair (19/20) is AGND. This is the canonical pinout spec; Part 1
and Part 0 both reference it.

### Architectural invariant (recap from Part 0)

Daughterboard populates passives only (pots, trim, LEDs). No IC supplies,
no raw power rails, no high-Z feedback nodes cross the header. Shorting
any two daughterboard signals together will not damage the main PCB.

### Signal inventory

**Input stage (per channel, from Part 1):**

* `IN_OPA_L` / `IN_OPA_R` — op-amp output, low-Z, to input pot CW terminal
* `IN_WIPER_L` / `IN_WIPER_R` — input pot wiper, moderate-Z (0–2.5 kΩ),
  back to `R_out`
* `CLIP_LED_A_L` / `CLIP_LED_A_R` — current-limited LED anode (1 kΩ to
  +12 V on main PCB)
* `CLIP_LED_K_L` / `CLIP_LED_K_R` — LED cathode, LM2903 open-collector
  output

**Output stage (per channel, from Part 3):**

* `OUT_OPA_L` / `OUT_OPA_R` — op-amp output, low-Z, to output pot CW
  terminal
* `OUT_WIPER_L` / `OUT_WIPER_R` — output pot wiper, feeds THAT1646 input
* (Pot CCW grounds to AGND — shared with input-stage AGND returns)

### Connector

The main-PCB footprint is **2×10 (20 pins), 2.54 mm pitch, through-hole,
polarised (keyed)**. See **Part 0 → "Connector — one footprint, two
build modes"** for the rationale. Two supported build modes from the
same footprint:

* **Cable-mount (default):** populate with a shrouded IDC header — e.g.
  Samtec TSS-110-01-G-D or equivalent. Mate with a 20-way IDC ribbon
  socket on the daughterboard side.
* **Stack-mount:** populate with a Samtec flex-stacking post (see Part 0)
  and socket the daughterboard directly above. No cable.

Daughterboard side is user's choice — shrouded socket for cable-mount, or
matching stack-mount socket for direct stacking.

### Pin assignment

Pinout is designed to group audio together, isolate moderate-Z audio from
fast-edge digital, and interleave AGND returns on every audio pair.

| Pin | Signal          |  Pin | Signal          | Notes                                  |
|----:|-----------------|-----:|-----------------|----------------------------------------|
|   1 | AGND            |    2 | AGND            | Top-of-header AGND guard               |
|   3 | `IN_OPA_L`      |    4 | `IN_OPA_R`      | Input-stage audio out (low-Z)          |
|   5 | `IN_WIPER_L`    |    6 | `IN_WIPER_R`    | Input-stage audio back (moderate-Z)    |
|   7 | AGND            |    8 | AGND            | Audio-pair guard                       |
|   9 | `OUT_OPA_L`     |   10 | `OUT_OPA_R`     | Output-stage audio out (low-Z)         |
|  11 | `OUT_WIPER_L`   |   12 | `OUT_WIPER_R`   | Output-stage audio back                |
|  13 | AGND            |   14 | AGND            | Separates audio from fast-edge digital |
|  15 | `CLIP_LED_A_L`  |   16 | `CLIP_LED_A_R`  | Current-limited LED anodes             |
|  17 | `CLIP_LED_K_L`  |   18 | `CLIP_LED_K_R`  | LM2903 OC outputs (fast digital edges) |
|  19 | AGND            |   20 | AGND            | Bottom-of-header AGND guard            |

Physical separation between the moderate-Z `IN_WIPER_*` pair (pins 5/6) and
the fast-edge `CLIP_LED_K_*` pair (pins 17/18) is 12 pins across the header —
well clear of capacitive crosstalk concerns with a standard ribbon. AGND
guards at pins 1/2, 7/8, 13/14, and 19/20 bracket every audio pair and the
clip-LED block.

### Signal-integrity notes

Applies to both build modes unless otherwise noted.

* **AGND interleave (both modes).** Every audio signal pair is bracketed
  by AGND pins above and below. Do not reroute to pack more signals — the
  AGND guards are load-bearing for both ribbon and stack mounts.
* **No power rails on the header (both modes).** If the daughterboard
  needs an active LED driver or user IC, route through J2 (Seed GPIO
  breakout, +3V3D available) — not this header.
* **Moderate-Z `IN_WIPER_*` vs. fast-edge `CLIP_LED_K_*` (cable-mount).**
  The pinout places these at opposite ends of the header. On cable side,
  route `IN_WIPER_*` on the lowest-noise ribbon pair; route `CLIP_LED_K_*`
  on the opposite end or through a separate cable if the daughterboard is
  more than ~150 mm away. Stack-mount sidesteps this — no cable
  capacitive coupling.
* **`OUT_WIPER_*` is high-Z at the THAT1646 input (cable-mount).** Route
  through a low-noise ribbon pair with its adjacent AGND. Negligible on
  stack-mount.
* **Cable length (cable-mount only).** ≤ 150 mm comfortable, ≤ 50 mm
  conservative. Beyond 150 mm, consider a shielded cable (foil/braid tied
  to AGND at the main-PCB end only). N/A for stack-mount.

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
Per XLR pin (Hot and Cold, identical):

     +12V
      │
      K                  (cathode up — conducts when pin > +12V + Vf)
      ▲
      D_up
      │
      ├─── Hot (or Cold) → XLR pin 2 (or 3), THAT1646 output
      │
      D_dn
      ▼
      A                  (anode down — conducts when pin < -12V - Vf)
      │
     -12V
```

Protects the THAT1646 output stage when an XLR output is accidentally plugged
into a mic preamp with phantom power asserted. +48V through the preamp's 6.8kΩ
phantom feed produces ~5 mA per pin into the clamp — SM4004 (1A SMA) handles
this with huge margin and provides surge capacity for hot-plug transients.

## Rail Protection (TVS per rail)

The TMR 3-1222 is a regulated isolated DC-DC converter: it can source
current but cannot sink it (like the Rev 1 TMA-1212D). If current is forced **into** the ±12V rails from outside,
the rail voltage rises uncontrollably.

**The fault scenario:** our gear is powered off, but the XLR output stays
connected to a mic preamp with +48V phantom asserted. The THAT1646 outputs
float (no supply), the clamp diodes conduct from each XLR pin toward the
dead +12V rail, and ~7 mA per pin (up to 28 mA stereo) sustains into a node
with no sink. Rail caps charge up; eventually the rail can pump toward the
phantom supply voltage, destroying the OPA1656 (±22V abs max) and THAT1646
(±20V abs max) when the gear is next powered on.

**Mitigation:** one TVS per rail to AGND, both **bidirectional SMBJ15CA**
(SMB package) — same part as the input over-voltage TVS (D1) for BOM
consolidation across the project.

* `+12V → AGND`: SMBJ15CA, either terminal to either node (bidirectional).
  Clamps when +12V exceeds ~16V (normal operation: reverse-biased, ~µA
  leakage).
* `-12V → AGND`: SMBJ15CA, same part. Clamps when -12V drops below ~−16V.

Under a sustained 28 mA fault each TVS dissipates ~0.4 W — well within
the SMB-package 600 W (peak pulse) / ~3 W (steady-state derated) rating.
Also handles hot-plug surge transients.

### Placement

**Both rail TVSs sit on the power sheet, adjacent to the TMR 3-1222
output stage** — grouped with D1 (input over-voltage) and the bulk
caps in a single power-management zone.

Rationale: the dominant fault here is sustained DC (powered-off phantom,
28 mA continuous) which is governed by trace *resistance* — not
inductance — so a few cm of +12VA / -12VA rail trace produces sub-mV
drop and is electrically irrelevant. The hot-plug surge case is brief
(tens of ns) and small in current (SM4004s absorb the bulk at the XLR
pin), leaving multi-volt margin to the OPA1656 / THAT1646 abs-max
ratings even with the TVS at the DC-DC end of the rail.

Trade-off: the textbook-best layout (TVS near THAT1646 outputs,
minimising loop inductance for fast-edge surge containment) is not used
here. The DC-DC-side placement is the simplification picked for layout
cleanliness; documented here so the choice is traceable.

## Components

**Per channel (main PCB):**

* 1× R_in (2.2kΩ, 1%) — op-amp inverting input resistor
* 1× R_fb_fixed (15kΩ, any tolerance) — op-amp feedback floor; absolute
  value is trimmed out by R_fb_trim during bring-up calibration, so 1%
  is not required (5% is fine)
* 1× R_fb_trim (10kΩ multi-turn cermet, e.g. Bourns 3296W-1-103) — gain
  calibration, wired rheostat-mode in series with R_fb_fixed
* 1× C_fb (100pF C0G MLCC, 0402 or 0603) — reconstruction LPF across
  R_fb; see "Reconstruction Low-Pass Filter" subsection
* 4× SM4004 (SMA) — XLR output clamp to ±12V rails
* 1× THAT1646 balanced line driver (SOIC-8)

**Per channel (daughterboard — user-swappable controls):**

* 1× 10kΩ log pot — output level (three-terminal voltage divider)

**Shared (main PCB):**

* 1× OPA1656 dual op-amp (SOIC-8) — both output channels
* 2× 100nF + 2× 1nF MLCC — OPA1656 supply decoupling (V+ and V-), same
  scheme as the input stage
* THAT1646 decoupling per datasheet (unchanged from Rev 1)
* (Rail-protection TVSs live on the power sheet, not the audio_output
  sheet — see Rail Protection → Placement above.)


# Part 4: Power Section

## Design Objectives

1. Deliver clean ±12V analog rails to the Rev 2 input stage, output stage,
   comparator, and any user daughterboard circuitry, with headroom.
2. Deliver a +5V rail to the Daisy Seed and MIDI front-end with correct
   component derating.
3. Protect the board from common user errors: polarity reversal, over-voltage
   wall wart, phantom-power back-feed (handled in Part 3).
4. Offer an optional panel power switch without forcing the switch onto users
   who don't want one.
5. Address Rev 1 defects: buck converter layout
   ([Issue #1](https://github.com/squeedee/daisy-studio/issues/1)) and +5V
   rail capacitor ratings
   ([Issue #2](https://github.com/squeedee/daisy-studio/issues/2)).

## Topology

```
Barrel jack (J_DC1, 2.1mm)
     │
     ▼
  +12V_IN (local label)
     │
     ▼
  JST VH 2-pin (J_SW) ── panel switch or shunt harness (Issue #5)
     │
     ▼
  Q1  (SI2301 P-FET reverse-polarity protection)
     │
     ▼
  D1  (SMBJ15CA bidirectional TVS — overvoltage clamp)
     │
     ▼
  C5  (100 µF / 25 V electrolytic, bulk)
     │
     ▼
  +12V_RAW ─────────┬──────────────────────────────┐
                    │                              │
                    ▼                              ▼
                 U2 (TPS54302 buck)          U1 (TMR 3-1222 isolated ±12V, 3 W)
                 + L3, C1/C2/C6/C7,          ±12V output → L1/L2 ferrites
                 R5/R6 feedback              → +12VA / −12VA rails
                    │
                    ▼
                 +5V rail → Daisy Seed, MIDI
```

## Changes vs. Rev 1

* **±12V DC/DC module:** Traco **TMA-1212D** (1 W, ±42 mA/rail) → Traco
  **TMR 3-1222** (3 W regulated ±2%, ±125 mA/rail). Driven by the Rev 2
  load budget: OPA1656 input + output gain stages, LM2903 comparator, and
  BJT clamp reference dividers on top of the Rev 1 THAT1246/THAT1646 draw.
  The daughterboard is fully passive (Part 0) and consumes no ±12V, so the
  budget is entirely main-PCB consumers plus a defensive margin. New SIP-8
  footprint; pinout re-verify against datasheet.
* **+5V rail caps C6 and C7:** 22 µF 0805 10 V → **22 µF 1206 25 V** X7R.
  10 V rating was insufficient derating for a 5 V MLCC
  ([Issue #2](https://github.com/squeedee/daisy-studio/issues/2)). 1206 /
  25 V restores ≥5× derating on rail voltage and supplies enough bulk for
  the TPS54302 buck at nominal load.
* **Buck converter PCB layout:** rework per TPS54302 datasheet layout
  guidelines (https://www.ti.com/document-viewer/tps54302/datasheet)
  ([Issue #1](https://github.com/squeedee/daisy-studio/issues/1)). No
  schematic change. See Layout Guidelines below.
* **Panel power switch:** new J_SW (JST B2P-VH, 3.96 mm pitch, 2-pin) in
  series between the barrel jack and Q1. Ships with a pre-crimped shunt
  harness (VHR-2N housing, two SVH-21T-P1.1 contacts bonded by a short wire
  loop) populated by default — bypasses the switch for users who don't need
  one ([Issue #5](https://github.com/squeedee/daisy-studio/issues/5)).
  Selected over a pin-header + shorting jumper because users wiring a panel
  switch want a robust, mechanically-keyed, pullable connector with
  generous current rating (10 A); the JST VH family is the standard for
  this.
* **ADC bias reference (2.5V from +5V):** removed. Rev 2's input stage
  relies on the PCM3060's internal V_COM and the Daisy Seed Rev 7 internal
  AC coupling; no external bias network needed
  ([Issue #9](https://github.com/squeedee/daisy-studio/issues/9) resolved —
  node no longer exists).
* **+5V rail fault clamp:** not required. Rev 1's concern
  ([Issue #10](https://github.com/squeedee/daisy-studio/issues/10)) was the
  passive input clamp dumping signal overdrive into +5V. Rev 2's BJT clamp
  references ±1.565 V derived from ±12V and sinks clamp current to AGND via
  the BJT collectors; +5V is no longer in the fault path. A defensive
  SMAJ5.0A across +5V → GND near the Seed header is left as **optional** —
  5 ¢ of insurance against future back-feeds, does nothing at nominal 5 V.
  Recommend populating on the first Rev 2 build.

## Power Budget (±12V Rails)

Per rail, quiescent:

| Consumer                          | +12V (mA) | −12V (mA) | Notes                                |
|-----------------------------------|-----------|-----------|--------------------------------------|
| 2× THAT1246 (input receiver)      | 16.0      | 16.0      | Rev 1                                |
| 2× THAT1646 (output driver)       | 18.0      | 18.0      | Rev 1                                |
| 1× OPA1656 (input gain, dual)     | 7.8       | 7.8       | Rev 2; 3.9 mA/channel typ × 2 ch     |
| 1× OPA1656 (output gain, dual)    | 7.8       | 7.8       | Rev 2; same part, one per stage      |
| BJT clamp ref dividers            | 2.1       | 2.1       | Rev 2; 1.04 mA per 11.5 kΩ divider   |
| LM2903 quiescent                  | 0.5       | 0.5       | Rev 2; ~0.4 mA/comparator            |
| Clip LEDs (peak, +12V only)       | up to 10  | —         | Intermittent; excluded from sizing   |
| **Main-board total**              | **~52**   | **~52**   |                                      |

Total output power ≈ 2 × 12 V × 52 mA = **1.25 W**. TMR 3-1222 rating 3 W
/ ±125 mA per rail gives **~2.4× headroom** — defensive margin against
component-tolerance, temperature, and Rev 1 part-to-part variation; not
allocated to any user extension.

±12V does **not** appear on the daughterboard header (Part 0 invariant —
passive only) or on J2 (digital only — +5V/+3V3D/DGND + GPIO). Analog
rails distribute through the dedicated power header J1 for on-main-PCB
consumers only. User extensions that need power run off J2's digital
rails.

+5V draw is dominated by the Daisy Seed (~150 mA typical, ~500 mA peak at
boot/USB enumerate) plus MIDI front-end (~5 mA) plus whatever the user
attaches via J2. TPS54302 is rated 3 A — not power-budget-constrained at
any realistic load.

## +5V Rail (TPS54302 buck)

Unchanged topology from Rev 1 — FB divider R5/R6 = 100 kΩ / 13.3 kΩ,
setting Vout ≈ 5.07 V. Inductor L3 = 10 µH (Bourns SRN6045TA). Load is the
Daisy Seed (~150 mA typical, up to ~500 mA peak at boot/USB activity) plus
MIDI front-end (~5 mA). TPS54302 is rated 3 A — very large headroom.

Two fixes apply:

* **C6, C7 cap spec:** 22 µF **1206 / 25 V X7R** (was 0805 / 10 V).
  [Issue #2](https://github.com/squeedee/daisy-studio/issues/2).
* **PCB layout:** follow the TPS54302 datasheet layout guidelines
  (https://www.ti.com/document-viewer/tps54302/datasheet) — specifically
  (a) input cap loop from Vin to PGND as short as possible, both on the
  top layer, (b) switch-node trace from SW pin to L3 as short and fat as
  practical, no stubs, (c) feedback sense trace from Vout to FB pin routed
  away from the SW node, preferably on an inner layer with a ground pour
  reference, (d) local GND pour under the IC stitched to the inner ground
  plane with a via farm directly at the PGND pin.
  [Issue #1](https://github.com/squeedee/daisy-studio/issues/1). No
  schematic change.

## Panel Power Switch (J_SW)

JST VH 2-pin header, through-hole, placed physically close to the barrel
jack and before the reverse-polarity FET:

```
Barrel jack (+)  ──▶  J_SW pin 1
                         │
                       (external switch closes loop)
                         │
Q1 source        ──▶  J_SW pin 2
```

* Connector: JST **B2P-VH** (vertical, 3.96 mm pitch). Unshrouded is
  adequate for an internal harness; switch to B2PS-VH if the build
  experience warrants keying.
* Mating housing: JST **VHR-2N** with two **SVH-21T-P1.1** crimp contacts.
* Default populated: pre-crimped **shunt harness** — VHR-2N housing with
  the two contacts bonded by a ~20 mm wire loop. Users remove the shunt
  and plug in a switch harness when they want a panel switch.
* Current rating: 10 A — far beyond the ~200–300 mA peak input current of
  the regulated DC/DC + buck combination.

The switch is placed **after** the barrel jack and **before** Q1 so that
reverse-polarity protection and input TVS clamping still function normally
during a miswired wall-wart event regardless of switch state.

## Grounding (unchanged from Rev 1)

* JP1 (`CHASSIS`-GND solder jumper) next to the Daisy Seed AGND/DGND pins,
  default bridged; cut if chassis-ground loops become a problem in a given
  enclosure.
* J7, J8 mounting holes on `CHASSIS`, bonded to enclosure via M3 hardware.
* Star topology: AGND, DGND, `CHASSIS` meet only at JP1 / mounting-hole
  bond.

## Components

**Main PCB:**

* 1× barrel jack 2.1 mm (J_DC1, THT) — unchanged
* 1× JST B2P-VH 2-pin THT header (J_SW) — **new, [Issue #5](https://github.com/squeedee/daisy-studio/issues/5)**
* 1× SI2301 P-FET, SOT-23 (Q1) — unchanged, reverse-polarity protection
* 1× SMBJ15CA bidirectional TVS, SMB (D1) — input over-voltage clamp on +12V_RAW
* 2× SMBJ15CA bidirectional TVS, SMB — rail protection on +12VA→AGND and
  -12VA→AGND, placed near the TMR 3-1222 output. Same part as D1 (single
  BOM line for all three TVSs across the project). See Part 3 → Rail
  Protection → Placement.
* 1× 100 µF / 25 V electrolytic, CP_Elec_6.3x7.7 (C5) — unchanged
* 1× TPS54302 buck, SOT-23-6 (U2) — unchanged
* 1× 10 µH Bourns SRN6045TA inductor (L3) — unchanged
* 2× 22 µF / 25 V X7R MLCC, **1206** (C6, C7) — **changed footprint & voltage**
* Supporting R/C around the buck (C1, C2, C3, C4, C8, R1, R2, R3, R4, R5, R6)
  — unchanged values; verify footprints during the Issue #1 layout rework
* 1× **TMR 3-1222** isolated DC/DC, SIP-8 (U1) — **replaces TMA-1212D**
* 2× BLM18PG121SN1 ferrite beads, 0603 (L1, L2) — unchanged, on ±12VA
* 1× SMAJ5.0A TVS near Seed +5V input — **optional, recommended**

**Shunt harness (shipped in kit):**

* 1× JST VHR-2N housing
* 2× SVH-21T-P1.1 contacts
* 1× short bonding wire (~20 mm)

## Layout Guidelines

### Buck converter (TPS54302) — Issue #1 rework

Per the TPS54302 datasheet layout guidelines
(https://www.ti.com/document-viewer/tps54302/datasheet):

1. **Input capacitor loop.** Place C_in (one of C3/C4, whichever is Vin
   decoupling) directly adjacent to U2 pins 1 (Vin) and 2 (GND), both on
   the top layer. Loop area < 20 mm².
2. **Switch-node trace.** SW (pin 6) to L3 input pin: shortest possible,
   wide copper (≥0.6 mm), top layer only, no stubs, no vias. This is the
   high-dV/dt node — keep its exposed area minimum.
3. **Feedback sense.** Route Vout → FB (pin 5) on the bottom or inner
   layer, away from the SW trace, with a ground pour reference directly
   underneath. Tap Vout at the output cap, not at the inductor.
4. **Ground pour.** Continuous ground pour on the bottom layer under U2.
   Stitch to the inner ground plane with a via farm (≥4 vias) directly at
   U2's PGND pin and another ≥4 vias at each input/output cap's GND pad.
5. **Bootstrap cap (C8, 75 pF across BOOT-SW):** placed directly adjacent
   to U2 pins 3 (BOOT) and 6 (SW), short trace.

### ±12V DC/DC module (TMR 3-1222)

* Place the module physically close to the balanced I/O section so ±12V
  delivery traces to THAT1246 / THAT1646 / OPA1656 are short.
* L1, L2 ferrites immediately at the module output pins.
* Post-ferrite bulk cap (reuse existing or increase to 10 µF X7R if
  measurement shows ripple > 10 mVpp at the op-amp supply pins).
* Isolation slot under the module: the TMR 3-1222 has isolated primary
  and secondary; preserve 3 mm creepage between PGND (primary) and AGND
  (secondary) on the PCB.

### General

* No split of AGND between input and output sections — continuous analog
  ground pour across the entire analog path (Part 1 and Part 3 agree on
  this).
* Digital ground (Seed, USB, MIDI) stays separate from AGND; the two meet
  only at JP1.

## Verification

Schematic-level checks (pre-layout):

1. `kicad-cli sch export netlist --output /dev/null power.kicad_sch` — parse.
2. `kicad-cli sch erc power.kicad_sch` — check unconnected pins, missing
   flags, rail conflicts.
3. Confirm TMR 3-1222 symbol / footprint present in
   `daisy-studio.kicad_sym` or an imported library.
4. Confirm J_SW footprint (JST VH B2P-VH) present in `daisy-studio.pretty`
   or a library.

Bench validation (post-board):

1. Measure ±12V rail voltage at the op-amp supply pins under nominal Seed
   idle load.
2. Measure ±12V rail voltage under full-scale audio drive (input +24 dBu,
   output 24 Vpp differential).
3. Scope ±12V ripple at op-amp supply pins; verify < 10 mVpp audio band.
4. Pull a 25 mA/rail test load at the ±12V rail caps; verify rails stay
   within the TMR 3-1222's ±2% spec. (Not a user-extension test — daughter-
   board and J2 don't carry ±12V; this is a defensive margin check.)
5. Verify power switch header: shunt populated → power on; shunt removed →
   power off.
6. Reverse-polarity test with 12V wall wart on the bench — Q1 should
   block, no rail activity.

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

