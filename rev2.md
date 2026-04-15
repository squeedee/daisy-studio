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

LTspice `.four` analysis at 1kHz with nominal component values. Three configurations
compared:

**Passive clamp (BAV99, V_ref = 1.091V, feedback from V_out):** Distortion-free up to
R_fb ≈ 18.3kΩ (gain ≈ -1.83). Above this point THD rises steeply — ~0.15% at 19kΩ,
~0.5% at 20kΩ, ~5.8% at 25kΩ. At the knee the codec sees 2.0V p-p (67% ADC
utilisation).

**Post-clamp feedback tap (BAV99, V_ref = 1.818V, feedback from Seed_In):**
Distortion-free up to R_fb ≈ 22kΩ (gain = -2.2). The loop gain compresses the BAV99
knee so THD rises gently — 0.074% at 22.5kΩ, 0.082% at 23kΩ, 0.109% at 25kΩ. At
the knee the codec sees 2.81V p-p (94% ADC utilisation). At R_fb = 25kΩ the codec
reaches 3.19V p-p with THD still under 0.11% — but fails under overdrive due to
reference pumping (see below).

**BJT clamp (2N3906/2N3904, V_ref = 1.091V, feedback from V_out):** Distortion-free
up to R_fb ≈ 21.5kΩ. THD rises gradually — 0.083% at 22kΩ, 0.105% at 23kΩ, 1.16%
at 25kΩ. At the knee the codec sees 2.36V p-p (79% ADC utilisation). At R_fb = 25kΩ
the codec reaches 2.66V p-p (89%) with codec_max = 3.84V (signal zone). Under +24 dBu
overdrive, codec_max = 4.50V with 300mV damage margin — reference pumping is
eliminated by the BJT's current gain.

See `sim/input/thd-plus4db.csv` for the passive and feedback clamp datasets, and
`sim/input/sharper-diode.csv` for the BJT clamp dataset.

## Ground Rules

All components in this circuit are in the analog signal path and connect to Analog
Ground. The clamp reference dividers derive from the ±12V analog supply (TMA-1212D
secondary) and terminate at AGND.

## Reducing the Clamp Zone

The current passive clamp limits clean ADC utilisation to 67% (2.0V p-p at the codec
vs 3.0V p-p full scale). The root cause is the BAV99's wide conduction knee: with an
ideality factor of N=1.82, the transition from negligible diode current to hard
limiting spans approximately 200mV at the Seed pin. This forces V_ref to be set low
enough that the hard clamp stays within damage margin, leaving the signal zone
under-utilised.

Two approaches to narrowing the clamp zone Under investigation:

### Sharper Clamp Element — BJT Clamp

Simple diode substitution does not help: the standard 1N4148 SPICE model has N=1.752,
nearly identical to the BAV99's N=1.82. All common silicon PN signal diodes cluster in
the N=1.7–1.9 range. Schottky diodes (e.g. BAT54) have lower ideality factors but
exhibit significant clamping asymmetry and very low Vf that eats into signal headroom —
this was confirmed on the Rev 1 board.

The solution is to replace each clamp diode with a BJT transistor. A PNP (2N3906)
clamps positive excursions; an NPN (2N3904) clamps negative excursions. The base-
emitter junction has a forward ideality factor NF≈1.24 (vs N=1.82 for BAV99),
producing a meaningfully sharper knee. More importantly, the transistor's current gain
(β≈200) means only microamps of base current flow through the reference divider, while
the collector handles the full clamp current — largely eliminating reference pumping.

```
BJT clamp topology (replaces BAV99 diodes):

                n+ ref ──── Base (Q1, PNP 2N3906)
                                │
R_out ──────────────── Emitter ──┬── Seed_In
                                │
                n- ref ──── Base (Q2, NPN 2N3904)
                                │
                Collectors ──── AGND
```

**How it works:**

- **Positive clamp (Q1, PNP):** When V(Seed_In) exceeds V(n+) + Vbe, the PNP turns
  on and sinks current from Seed_In to ground through its collector. The base current
  (Ic/β) is the only load on the reference divider.
- **Negative clamp (Q2, NPN):** When V(Seed_In) drops below V(n-) − Vbe, the NPN
  turns on and sources current from ground into Seed_In.

**Knee width comparison (10µA to 1mA transition):**

    BAV99:  ΔVf  = N × Vt × ln(100) = 1.82 × 25.85mV × 4.605 = 216mV
    2N3904: ΔVbe = NF × Vt × ln(100) = 1.259 × 25.85mV × 4.605 = 150mV  (31% narrower)

**Reference pumping comparison (at 1mA clamp current, R_th = 909Ω):**

    BAV99:  ΔV_ref = I_clamp × R_th = 1mA × 909Ω = 909mV  (catastrophic)
    BJT:    ΔV_ref = I_base × R_th = 5µA × 909Ω = 4.5mV   (negligible)

#### SPICE Validation — Normal Levels (+4 dBu)

LTspice simulation (`sim/input/sharper-diode.asc`) with 10kΩ/1kΩ dividers
(V_ref = 1.091V), 2N3904/2N3906 models (NF = 1.259/1.232):

| Metric                   | BAV99 passive   | BJT clamp        |
|--------------------------|-----------------|------------------|
| Knee onset (R_fb)        | ~18.3kΩ         | ~21.5kΩ          |
| codec p-p at knee        | 2.01V (67%)     | 2.36V (79%)      |
| THD at R_fb = 25kΩ       | 5.80%           | 1.16%            |
| codec p-p at R_fb = 25kΩ | hard clamp      | 2.66V (89%)      |
| codec_max at R_fb = 25kΩ | 4.72V           | 3.84V            |

The BJT clamp extends the clean gain range by ~3kΩ and keeps THD under 1.2% even at
maximum gain, where the BAV99 was already at 5.8%. At rfb = 25k, the codec peak
(3.84V) is still within the signal zone.

#### SPICE Validation — Overdrive (+24 dBu, full rfb sweep)

Simulation (`sim/input/sharper-diode-overdrive.asc`) at +24 dBu (8.68V) across the
full rfb range confirms the BJT clamp survives heavy overdrive:

| Metric            | At R_fb = 10kΩ | At R_fb = 25kΩ |
|-------------------|----------------|----------------|
| codec_max         | 4.19V          | 4.50V          |
| codec_pp          | 3.38V          | 4.00V          |
| seed_max          | 2.32V          | 2.73V          |
| seed_min          | −2.28V         | −2.69V         |
| Clamp asymmetry   | 34mV           | 44mV (1.6%)    |
| THD               | 31.6%          | 39.9%          |

**codec_max = 4.50V at worst case (rfb = 25kΩ) — 300mV margin to the 4.8V damage
threshold.** The clamp asymmetry (44mV between positive and negative thresholds) comes
from the NF mismatch between the two transistors (1.232 vs 1.259) and is well within
acceptable limits.

The reference pumping that made the feedback clamp topology fail under overdrive is
effectively eliminated — the BJT's current gain reduces reference divider loading by
a factor of β (≈200), keeping V_ref stable even under sustained clamp current.

#### Clip Indicator LED

The BJT topology enables a passive clip indicator. The PNP collector current only
flows when the positive clamp is active, so routing it through an LED makes the
clamping directly visible:

```
Q1 (PNP, positive clamp):
  E → Seed_In
  B → n+
  C → 1kΩ → LED → -12V
```

The collector sits at approximately −12V + Vled + Ic×R ≈ −8V during clamping — far
below the emitter voltage, so the PNP stays in active mode and clamping behaviour is
unaffected. Only one LED (on Q1) is needed since the signal is symmetric.

The LED requires ~0.5–1mA of collector current to become visible, which corresponds
to moderate clamping rather than the theoretical onset — a useful threshold for
indicating audible clipping.

#### Component Impact

Replaces 1× BAV99 (SOT-23) per channel with 1× 2N3906 + 1× 2N3904 (both SOT-23).
Same footprint class, same cost tier. Reference dividers and capacitors unchanged.
Adds 1× LED + 1× 1kΩ resistor per channel for optional clip indication.

> TODO: Run tolerance analysis (±5% supply, ±1% resistors, BJT β variation) to
> validate worst-case codec_max stays below 4.8V. Adjust divider values if needed to
> optimise signal zone utilisation vs damage margin.

### Post-Clamp Feedback Tap (Active Limiting)

Instead of moving the clamp diodes, the feedback resistor R_fb is reconnected from
the op-amp output to the Seed_In node (after R_out and the passive clamp). This puts
the existing passive clamp inside the feedback loop, using the op-amp's loop gain to
sharpen the diode knee without changing any clamp components.

This is not automatic gain control. The limiter only acts when the signal enters the
clamp zone. All gain below the threshold is set entirely by R_fb/R_in.

```
Current topology (feedback from V_out):

V_in → R_in → V_inv → op-amp → V_out → R_out → [BAV99 clamp] → Seed_In
                ↑                  ↑
                └──── R_fb ────────┘

Proposed topology (feedback from Seed_In):

V_in → R_in → V_inv → op-amp → V_out → R_out → [BAV99 clamp] → Seed_In
                ↑                                                   ↑
                └──────────────── R_fb ─────────────────────────────┘
```

The passive clamp (BAV99 diodes, reference dividers, filter capacitors) remains
exactly as specified above. The only physical change is reconnecting R_fb from the
op-amp output to the Seed_In node.

#### Operating Modes

**Normal operation (below clamp):** The op-amp maintains virtual ground at V_inv.
Gain at the Seed_In node is exactly -R_fb/R_in. The R_out signal loss (~14%) is
automatically compensated by the loop — the op-amp increases its output to maintain
the correct voltage at Seed_In. This is an improvement over the current topology,
where the gain at Seed_In is reduced by the R_out / Seed impedance divider.

**At the clamp threshold:** When V(Seed_In) reaches V_ref + Vf, the BAV99 starts
conducting. The op-amp responds by increasing V_out to maintain virtual ground, but
the clamp diode absorbs the excess current, holding Seed_In near V_ref + Vf. The loop
gain compresses the BAV99's soft exponential knee into a near-ideal brick-wall limit
at the Seed_In node — the exact node that determines ADC headroom.

**Heavy overdrive (op-amp saturation):** Under extreme input levels, the op-amp
output saturates at the rail (~±12V). The clamp reverts to passive behaviour.
However, the half-wave rectified clamp current (each diode conducts on one polarity
only) charges the reference capacitors through the divider's Thevenin resistance
(R_th), shifting V_ref away from its nominal value. This **reference pumping** is the
primary limitation of the feedback clamp topology with resistive dividers — see
"Reference Pumping" below.

#### Advantages

1. **Precision:** V_ref is set by the existing resistive divider (1% resistors), not
   by diode forward voltage which varies with current and temperature.
2. **Minimal change:** Only R_fb reconnection — no new components, no removed
   components, no change to the clamp or reference dividers.
3. **Direct control:** V_ref sets the clamp voltage directly at the Seed_In node
   (V_clamp ≈ V_ref + Vf). No R_out divider correction needed.
4. **Gain accuracy:** Gain at Seed_In is exactly R_fb/R_in, automatically
   compensating for R_out loss that the current topology must account for.

#### Fault Protection

No additional passive protection is required. If the ±12V supply is lost, the op-amp
has no output swing and gain drops to zero — there is no signal to clamp. The
existing R_out (2.2kΩ) remains in the signal path and limits current in any scenario.

#### Stability

The feedback loop now includes R_out (2.2kΩ). The additional pole from R_out and
stray capacitance at Seed_In is at very high frequency (few pF → pole well above
10MHz). The Seed input impedance (R4=3.6kΩ, C1=4.7µF) is a load at Seed_In, not in
the feedback path, and does not add a pole to the loop.

When the clamp engages, the effective impedance at Seed_In drops (clamp diode
provides a low-impedance path to V_ref). Audio quality in the clamp region is
irrelevant — the concern is that an unstable loop could oscillate and produce voltage
spikes that overshoot into the damage zone (4.8V at codec). The reference capacitors
(470µF) hold V_ref stiff, limiting the impedance change. SPICE transient simulation
driving hard into the clamp will verify that no overshoot exceeds the damage
threshold.

#### V_ref Adjustment

With the feedback loop compensating for R_out loss, the original V_ref (1.091V, from
10kΩ/1kΩ dividers) causes the clamp to engage too early — the op-amp drives Seed_In
to exactly R_fb/R_in × V_in, so the signal reaches V_ref at a lower R_fb than with
the passive topology. Raising the divider to 5.6kΩ/1kΩ sets V_ref = 1.818V,
shifting the clamp knee to R_fb ≈ 22kΩ.

    V_ref = 12V × 1kΩ / (5.6kΩ + 1kΩ) = 1.818V

#### SPICE Validation — Normal Levels (+4 dBu)

LTspice transient simulation (`sim/input/feedback-clamp.asc`) with V_ref = 1.818V
at +4 dBu input confirms the feedback tap dramatically outperforms the passive clamp
at normal operating levels:

| Metric                          | Passive clamp     | Feedback clamp     |
|---------------------------------|-------------------|--------------------|
| V_ref                           | 1.091V (10k/1k)  | 1.818V (5k6/1k)   |
| Knee onset (R_fb)               | ~18.3kΩ           | ~22kΩ              |
| codec p-p at knee               | 2.01V (67%)       | 2.81V (94%)        |
| THD at R_fb = 25kΩ              | 5.80%             | 0.11%              |
| codec p-p at R_fb = 25kΩ        | hard clamp        | 3.19V              |

The feedback loop compresses the BAV99 knee from ~200mV of soft transition into a
near-ideal clamp. THD rises from the noise floor (0.071%) to only 0.109% across the
full 10kΩ–25kΩ gain range. ADC utilisation at the clean headroom limit **improves
from 67% to 94%.**

See `sim/input/thd-plus4db.csv` for the complete dataset.

#### Reference Pumping — Overdrive (+24 dBu, R_fb = 25kΩ)

Under heavy overdrive the op-amp saturates at the supply rails and the clamp reverts
to passive behaviour. The clamp current is half-wave rectified at each reference
node — D2 conducts into n+ on positive excursions only, D1 conducts from n- on
negative excursions only. This DC current charges the reference capacitors through
the divider's Thevenin resistance (R_th), shifting V_ref away from its nominal
value.

With 5.6kΩ/1kΩ dividers (R_th = 848Ω), simulation at +24 dBu with R_fb = 25kΩ
shows V(n+) shifting from the nominal 1.818V to approximately 3.0V. The resulting
codec peak reaches 5.2V — well above the 4.8V absolute maximum.

Lowering the divider impedance reduces the shift. With 2.7kΩ/470Ω dividers
(R_th = 401Ω, V_ref = 1.78V), simulation shows:

    codec_pp  = 4.54V
    codec_max = 4.77V  (30mV margin to 4.8V abs max — insufficient)

This margin is too thin to survive component tolerances. The fundamental limitation
is that resistive dividers cannot hold V_ref stiff against milliamps of rectified
clamp current without consuming excessive quiescent power (the TMA-1212D has ~400mW
available for reference dividers).

**Note:** This reference pumping problem also affects the existing passive clamp
topology under the same overdrive conditions. It was not identified in the original
fault analysis because the AC reference impedance (R_th ∥ Z_cap ≈ 16.6Ω at 20Hz)
was used instead of the DC Thevenin resistance (R_th = 909Ω) that governs the
steady-state voltage shift.

#### Status

The post-clamp feedback tap is validated for normal operation and moderate overdrive.
The outstanding problem is fault-level overdrive protection, where reference pumping
shifts V_ref and erodes the damage margin. Possible paths forward:

1. **Active voltage reference** (e.g. TL431 shunt regulator) — holds V_ref stiff
   regardless of clamp current, eliminating the pumping problem entirely.
2. **Lower divider impedance** — trades quiescent power for stiffer V_ref. Requires
   R_th below ~200Ω for adequate margin, consuming ~400mW of the 1W power budget.
3. **Hybrid approach** — keep the passive clamp with original dividers (V_ref =
   1.091V) for fault protection, add the feedback tap for signal-zone knee
   compression only. Requires the feedback loop to disengage cleanly before the
   op-amp saturates.

### References

The feedback clamp topology is well-established in precision analog and pro audio
design. Key references consulted for this investigation:

1. Circuit Cellar, "Precision Clamps" — two-diode precision clamp topology; explains
   why feedback-path diodes prevent op-amp saturation during clamping.
   https://circuitcellar.com/resources/quickbits/precision-clamps/

2. Analog Devices, "Op Amp Precision Positive & Negative Clipper (LT6015/6016/6017)"
   — precision clipper application note with sub-100µV offset analysis.
   https://www.analog.com/en/resources/technical-articles/op-amp-precision-positive-negative-clipper-using-lt6015-lt6016-lt6017.html

3. Electronic Design, "Op Amps Make Precision Clipper, Protect ADC" — directly
   addresses ADC input protection using op-amp feedback clamp.
   https://www.electronicdesign.com/technologies/analog/article/21801600/op-amps-make-precision-clipper-protect-adc

4. All About Circuits, "An Op-Amp Limiter" — tutorial on limiting amplified signal
   amplitude using diodes in the feedback loop.
   https://www.allaboutcircuits.com/technical-articles/an-op-amp-limiter-how-to-limit-the-amplitude-of-amplified-signals/

5. Microchip AN1353, "Op Amp Rectifiers, Peak Detectors and Clamps" — comprehensive
   application note covering precision clamp circuit variations.
   https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ApplicationNotes/ApplicationNotes/01353A.pdf

6. Analog Devices AN-402, "Replacing Output Clamping with Input Clamping" — confirms
   input-clamping amps (AD8036/8037) are not suitable for inverting configurations;
   output-clamping (feedback) topology is correct for our inverting amplifier.
   https://www.analog.com/en/resources/app-notes/an-402.html

7. Analog Devices, "Differential Op-Amp Driver Protects High-Resolution ADC
   (MAX44205)" — integrated approach to the same problem with built-in output
   clamping for ADC protection.
   https://www.analog.com/en/resources/technical-articles/differential-opamp-driver-protects-a-highresolution-adc-from-input-overvoltage.html

8. TI Precision Labs, "Op-Amps Stability — Phase Margin" — training module on
   measuring and ensuring phase margin, applicable to feedback clamp stability.
   https://training.ti.com/ti-precision-labs-op-amps-stability-phase-margin

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

