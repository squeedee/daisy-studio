# Proto Board: Op-Amp Gain-Staged Input with BJT Clamp

Single-channel prototype of the Rev 2 input circuit for real-world testing.
Uses the Rev 1 PCB for power supply and THAT 1246 differential receiver.

## Parts List (all THT)

| Ref      | Value    | Part                       | Notes                                                                                          |
|----------|----------|----------------------------|------------------------------------------------------------------------------------------------|
| U1       | Op-amp   | TL072CP (DIP-8)            | Use one half. OPA1656 is SMD only — TL072 is fine for clamp testing (JFET input, ±15V, DIP-8). |
| R_in     | 10k      | 1/4W metal film            |                                                                                                |
| R_fb     | 25k pot  | 16mm panel pot or trim pot | Linear taper for testing                                                                       |
| R_out    | 2.2k     | 1/4W metal film            |                                                                                                |
| Q1       | 2N3906   | TO-92 (EBC pinout)         | PNP positive clamp                                                                             |
| Q2       | 2N3904   | TO-92 (EBC pinout)         | NPN negative clamp                                                                             |
| R11, R14 | 10k      | 1/4W metal film, 1%        | Reference divider high side                                                                    |
| R12, R13 | 1k       | 1/4W metal film, 1%        | Reference divider low side                                                                     |
| C5, C6   | 47uF/25V | Electrolytic, radial       | Reference filtering. Observe polarity — long leg (+) to n+/n- node.                            |
| R_led    | 1k       | 1/4W                       | LED current limit                                                                              |
| LED      | Red 3mm  | Standard                   | Clip indicator                                                                                 |
| C3, C4   | 100nF    | MLCC ceramic               | Op-amp decoupling, one per supply pin                                                          |

## Connections to Rev 1 Board

**Power (3 wires):**

- +12V analog supply
- -12V analog supply
- AGND

**Signal in:**

- THAT 1246 output -> proto board "IN"

**Signal out:**

- Proto board "Seed_In" -> Daisy Seed audio input pin (pin 21 or 22 for L/R)

## Breadboard Layout (single channel)

```
     +12V rail ──────────────────────────────────────────────────────────
     AGND rail ──────────────────────────────────────────────────────────
     -12V rail ──────────────────────────────────────────────────────────

┌───────── Ref Dividers ──────────┐   ┌──── Op-Amp Gain Stage ─────┐   ┌──────────────── BJT Clamp ───────────────┐

+12V ─┤R11 10k├─ n+ ─┤R12 1k├─ AGND    IN ─┤R_in 10k├─┬─ U1:2 (inv-)                   Seed_In ─┬─ Q1.E (PNP)
                  │                                      │                                      │
                 C5 47u                        R_fb pot │              U1:1 (out)           Q2.E (NPN)
                  │                               wiper──┘                 │                    │
                AGND                                                       ├─┤R_out 2.2k├─── Seed_In ─── to Seed
                                                                           │                    │
AGND ─┤R13 1k├─ n- ─┤R14 10k├─ -12V    U1:3 (non-inv+)                  Q1.B ── n+            Q1.C
                 │                          │                                                   │
                C6 47u                   AGND              Q2.B ── n-                       R_led 1k
                 │                                          Q2.C ── AGND                        │
               AGND                      U1:8  +12V (+ C3 100nF to AGND)                       LED
                                         U1:4  -12V (+ C4 100nF to AGND)                        │
                                                                                               -12V
```

## Op-Amp Wiring (TL072CP, DIP-8)

```
        ┌───U───┐
 OUT A  │1     8│  V+   <- +12V (C3 100nF to AGND)
 IN- A  │2     7│  OUT B   (unused)
 IN+ A  │3     6│  IN- B   (unused)
 V-     │4     5│  IN+ B   (unused, tie to AGND)
        └───────┘
          <- -12V (C4 100nF to AGND)
```

- Pin 1 (OUT A): to R_fb pot CCW terminal + R_out
- Pin 2 (IN- A): to R_in + R_fb pot wiper
- Pin 3 (IN+ A): to AGND
- Pin 5 (IN+ B): tie to AGND (prevents unused half from oscillating)

## R_fb Pot Wiring

```
     CCW          CW
      │     pot    │
      ├────/\/\/───┤
      │      │     │
  U1:1 (out) │   U1:2 (inv-)
           wiper
           (also to U1:2)
```

- CW terminal: to U1 pin 2 (inverting input) and R_in
- CCW terminal: to U1 pin 1 (output)
- Wiper: to U1 pin 2 (inverting input)

This way, turning the pot CW increases R_fb (more gain). At full CCW the
wiper shorts to the output, giving minimum gain.

## BJT Wiring (TO-92, flat side facing you, pins down)

```
2N3906 (Q1, PNP):            2N3904 (Q2, NPN):
   E     B     C                E     B     C
   │     │     │                │     │     │
 Seed   n+   R_led->LED->-12V  Seed  n-   AGND
  _In          (clip indicator)  _In
```

Both emitters connect to the same Seed_In node. This is the critical
junction where R_out, both BJT emitters, and the wire to the Seed pin
all meet.

## Key Nodes

| Node    | DC voltage       | What connects here                                 |
|---------|------------------|----------------------------------------------------|
| +12V    | +12V             | R11, U1 pin 8, C3                                  |
| -12V    | -12V             | R14, U1 pin 4, C4, LED cathode (via R_led)         |
| AGND    | 0V               | R12, R13, C5, C6, U1 pin 3, U1 pin 5, Q2.C, C3, C4 |
| n+      | +1.091V          | R11/R12 junction, C5+, Q1.B                        |
| n-      | -1.091V          | R13/R14 junction, C6-, Q2.B                        |
| IN      | signal           | THAT 1246 output, R_in                             |
| inv-    | virtual ground   | R_in, R_fb wiper, U1 pin 2                         |
| U1 out  | signal           | R_fb CCW, R_out                                    |
| Seed_In | signal (clamped) | R_out, Q1.E, Q2.E, wire to Seed pin                |

## Test Points

- **n+, n-**: verify +/-1.091V DC with multimeter
- **U1 pin 1**: op-amp output — should swing freely below clamp, saturate at ~+/-11V under overdrive
- **Seed_In**: signal after clamp — scope here to observe clamp knee and hard limiting
- **LED**: visual clip indication — lights when positive clamp conducts
