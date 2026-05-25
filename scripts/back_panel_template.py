"""Generate a 1:1 SVG drilling template for the Daisy-Studio back panel.

Open the output in a browser or Inkscape and print at 100% / Actual Size.
Verify with the 25 mm calibration bar at the bottom before drilling.

Footprint placements + the local offset to each connector front-face centre
come from daisy-studio.kicad_pcb and the KiCad footprint files. The panel
X-coordinates are PCB X minus the V-groove cutline (62.075 mm).
"""
import math
from pathlib import Path

# ---- Panel size & PCB placement (edit) ---------------------------------------
# 10" x 2 1/4" aluminium panel; board centred; board bottom 1/2" from panel bottom
PANEL_WIDTH_MM  = 10.0 * 25.4         # 254.0 mm
PANEL_HEIGHT_MM = 2.25 * 25.4         # 57.15 mm
PCB_LEFT_X      = (PANEL_WIDTH_MM - 241.625) / 2  # PCB centred horizontally
PCB_THICKNESS   = 1.6
PCB_BOTTOM_Y    = 0.5 * 25.4          # 12.7 mm — bottom of board above panel bottom
PCB_TOP_Y       = PCB_BOTTOM_Y + PCB_THICKNESS    # PCB top-surface reference

# ---- Connector axis heights above PCB top surface ----------------------------
XLR_AXIS_ABOVE_PCB = 12.5  # from NCJ6FA-H 3D model z-offset
DIN_AXIS_ABOVE_PCB = 7.0   # estimated for SDS-50J (verify)
SD_SLOT_BELOW_PCB  = 1.5   # microSD mounts on B.Cu (under PCB), slot just under PCB plane

# ---- Cutout dimensions (Neutrik NCJ6FA-H from datasheet ST-NCJ6FAH-0) -------
XLR_HOLE_D            = 22.0   # Ø22 panel cutout (rear-side view)
XLR_SCREW_D           = 3.2    # 2x M3 clearance
XLR_SCREW_OFFSET_H    = 9.9    # screws at ±9.9 mm horizontal from bezel centre
XLR_SCREW_OFFSET_V    = 9.9    # AND ±9.9 mm vertical (diagonally opposed)
XLR_SCREW_DIAGONAL    = "TR_BL"  # "TR_BL" = top-right + bottom-left; "TL_BR" to flip

# ---- Cutout dimensions (DIN) -------
DIN_HOLE_D        = 15.0       # 5-pin DIN socket bezel cutout
DIN_SCREW_D       = 1.6        # 3-Ø1.6 per SDS-50J datasheet (triangular pattern)
DIN_SCREW_RADIUS  = 10.0       # mm from DIN centre to each mounting hole
DIN_SCREW_ANGLES  = (0, 120, 240)  # degrees, 0° = straight up from DIN centre

# ---- Cutout dimensions (SD) -------
SD_SLOT_W = 14.0
SD_SLOT_H = 3.0

# Barrel jack — back-facing face envelope from the KiCad 3D model
# (Connector_BarrelJack.3dshapes/BarrelJack_Horizontal.wrl, vertex bounds):
#   local y: [-4.80, +4.50]  → 9.30 mm wide, centre at -0.15 mm
#   local z: [0,    10.70]   → 10.70 mm tall, centre at  5.35 mm above PCB top
BARREL_CLEARANCE             = 0.5   # added to each side of the envelope
BARREL_BODY_W                = 9.30 + 2 * BARREL_CLEARANCE
BARREL_BODY_H                = 10.70 + 2 * BARREL_CLEARANCE
BARREL_BODY_CENTRE_ABOVE_PCB = 5.35
BARREL_LOCAL_Y_CENTRE        = -0.15  # body geometric centre in footprint local y


# ---- Board geometry & V-groove ----------------------------------------------
BOARD_LEFT_AFTER_VGROOVE = 62.075

# ---- Connector placements (read from daisy-studio.kicad_pcb) ----------------
# Each entry: (placement_x, placement_y, rotation_deg, local_front_face_x, local_front_face_y)
# local_front_face_(x,y) is the centre of the connector front face in the
# footprint's local coordinate frame (origin = footprint anchor pin).
XLRS = [
    (76.97,  43.865, 90, 22.115, 6.985),   # H1 / J1 — input L
    (103.43, 43.865, 90, 22.115, 6.985),   # input R
    (136.43, 43.865, 90, 22.115, 6.985),   # output L
    (162.43, 43.865, 90, 22.115, 6.985),   # output R
]
DINS = [
    (194.55,  37.825, 180, -7.5, 12.5),  # J7  MIDI
    (217.25,  37.825, 180, -7.5, 12.5),  # J9  MIDI
    (239.975, 37.775, 180, -7.5, 12.5),  # J10 MIDI
]
SD = (267.425, 33.575, 0)  # Hirose DM3BT, on B.Cu

# DC barrel jack placement
BARREL_JACK = (288.825, 39.125, -90)

# -----------------------------------------------------------------------------
def transform(local_x, local_y, place_x, place_y, rot_deg):
    """Footprint-local point -> board coords. KiCad: +rot is CCW on screen,
    which equals -theta in standard math because Y is down."""
    th = math.radians(-rot_deg)
    rx = local_x * math.cos(th) - local_y * math.sin(th)
    ry = local_x * math.sin(th) + local_y * math.cos(th)
    return (place_x + rx, place_y + ry)

def to_panel_x(board_x):  return board_x - BOARD_LEFT_AFTER_VGROOVE + (PCB_LEFT_X - 0)

# Effective panel-X: PCB origin (snapped board left) lands at PCB_LEFT_X
def board_to_panel(board_x):
    return PCB_LEFT_X + (board_x - BOARD_LEFT_AFTER_VGROOVE)

# -----------------------------------------------------------------------------
H, W = PANEL_HEIGHT_MM, PANEL_WIDTH_MM
def fy(y): return H - y  # SVG y-down -> panel y-up

STROKE_CUT = 'stroke="black" stroke-width="0.2" fill="none"'
STROKE_MARK = 'stroke="red" stroke-width="0.15" fill="none"'
STROKE_GUIDE = 'stroke="#999" stroke-width="0.1" fill="none" stroke-dasharray="1,1"'

def crosshair(cx, cy, size=3.0):
    return (
        f'<line x1="{cx-size/2}" y1="{fy(cy)}" x2="{cx+size/2}" y2="{fy(cy)}" {STROKE_MARK}/>'
        f'<line x1="{cx}" y1="{fy(cy)-size/2}" x2="{cx}" y2="{fy(cy)+size/2}" {STROKE_MARK}/>'
    )

def circle(cx, cy, d):
    return f'<circle cx="{cx}" cy="{fy(cy)}" r="{d/2}" {STROKE_CUT}/>'

def slot(cx, cy, w, h):
    r = h / 2
    x0, x1 = cx - w/2 + r, cx + w/2 - r
    y0, y1 = fy(cy) - r, fy(cy) + r
    return (
        f'<path d="M {x0} {y0} L {x1} {y0} A {r} {r} 0 0 1 {x1} {y1} '
        f'L {x0} {y1} A {r} {r} 0 0 1 {x0} {y0} Z" {STROKE_CUT}/>'
    )

def rect_g(x, y, w, h, style):
    return f'<rect x="{x}" y="{fy(y)-h}" width="{w}" height="{h}" {style}/>'

def label(cx, cy, text, size=2.5):
    return (f'<text x="{cx}" y="{fy(cy)}" font-size="{size}" '
            f'text-anchor="middle" fill="black">{text}</text>')

body = []

# Panel outline
body.append(f'<rect x="0" y="0" width="{W}" height="{H}" {STROKE_CUT}/>')

# PCB top edge (guide only — the only PCB feature that lies in the panel plane)
body.append(
    f'<line x1="{PCB_LEFT_X}" y1="{fy(PCB_TOP_Y)}" '
    f'x2="{PCB_LEFT_X + 241.625}" y2="{fy(PCB_TOP_Y)}" {STROKE_GUIDE}/>'
)
body.append(
    f'<text x="{PCB_LEFT_X + 2}" y="{fy(PCB_TOP_Y) - 1}" font-size="2" '
    f'fill="#999">PCB top edge (guide only — do not cut)</text>'
)
# PCB bottom-surface guide line (1/2" above panel bottom)
body.append(
    f'<line x1="{PCB_LEFT_X}" y1="{fy(PCB_BOTTOM_Y)}" '
    f'x2="{PCB_LEFT_X + 241.625}" y2="{fy(PCB_BOTTOM_Y)}" {STROKE_GUIDE}/>'
)

# XLR cutouts — Ø22 hole + 2 M3 screws diagonally outside the bezel
xlr_panel_y = PCB_TOP_Y + XLR_AXIS_ABOVE_PCB
if XLR_SCREW_DIAGONAL == "TR_BL":
    diag_offsets = [(+XLR_SCREW_OFFSET_H, +XLR_SCREW_OFFSET_V),
                    (-XLR_SCREW_OFFSET_H, -XLR_SCREW_OFFSET_V)]
else:  # TL_BR
    diag_offsets = [(-XLR_SCREW_OFFSET_H, +XLR_SCREW_OFFSET_V),
                    (+XLR_SCREW_OFFSET_H, -XLR_SCREW_OFFSET_V)]

for i, (px, py, rot, lx, ly) in enumerate(XLRS):
    bx, by = transform(lx, ly, px, py, rot)
    panel_x = board_to_panel(bx)
    body.append(circle(panel_x, xlr_panel_y, XLR_HOLE_D))
    body.append(crosshair(panel_x, xlr_panel_y))
    for (dx, dy) in diag_offsets:
        body.append(circle(panel_x + dx, xlr_panel_y + dy, XLR_SCREW_D))
        body.append(crosshair(panel_x + dx, xlr_panel_y + dy, size=2.0))
    body.append(label(panel_x, xlr_panel_y - XLR_HOLE_D/2 - 2.5, f"XLR{i+1}"))

# MIDI DIN cutouts — Ø15 bezel + 3 Ø1.6 mounting holes at 0°/120°/240°
din_panel_y = PCB_TOP_Y + DIN_AXIS_ABOVE_PCB
for i, (px, py, rot, lx, ly) in enumerate(DINS):
    bx, by = transform(lx, ly, px, py, rot)
    panel_x = board_to_panel(bx)
    body.append(circle(panel_x, din_panel_y, DIN_HOLE_D))
    body.append(crosshair(panel_x, din_panel_y))
    for angle_deg in DIN_SCREW_ANGLES:
        a = math.radians(angle_deg)
        dx = DIN_SCREW_RADIUS * math.sin(a)
        dy = DIN_SCREW_RADIUS * math.cos(a)
        body.append(circle(panel_x + dx, din_panel_y + dy, DIN_SCREW_D))
        body.append(crosshair(panel_x + dx, din_panel_y + dy, size=2.0))
    body.append(label(panel_x, din_panel_y - DIN_HOLE_D/2 - 2.5, f"MIDI{i+1}"))

# microSD slot — back-mounted, slot just below PCB plane
sd_px, sd_py, sd_rot = SD
# microSD card aperture is centred near the right edge of the connector body;
# without a verified front-face offset, use the placement X as the slot centre.
sd_panel_x = board_to_panel(sd_px)
sd_panel_y = PCB_TOP_Y - SD_SLOT_BELOW_PCB
body.append(slot(sd_panel_x, sd_panel_y, SD_SLOT_W, SD_SLOT_H))
body.append(crosshair(sd_panel_x, sd_panel_y, size=2.0))
body.append(label(sd_panel_x, sd_panel_y - 4, "microSD (B.Cu — verify)"))

# DC barrel jack — cutout matches the back-facing face envelope so the body
# can protrude through the panel. We project the body's local y-centre through
# the placement rotation to get panel X; panel Y comes from the body z-centre.
bjx, bjy, bjrot = BARREL_JACK
bx_centre, _ = transform(0, BARREL_LOCAL_Y_CENTRE, bjx, bjy, bjrot)
barrel_panel_x = board_to_panel(bx_centre)
barrel_panel_y = PCB_TOP_Y + BARREL_BODY_CENTRE_ABOVE_PCB
body.append(rect_g(barrel_panel_x - BARREL_BODY_W/2,
                   barrel_panel_y - BARREL_BODY_H/2,
                   BARREL_BODY_W, BARREL_BODY_H, STROKE_CUT))
body.append(crosshair(barrel_panel_x, barrel_panel_y, size=3.0))
body.append(label(barrel_panel_x, barrel_panel_y + BARREL_BODY_H/2 + 2,
                  "DC barrel (body)"))

# 25 mm calibration bar
bx0, by0 = 5.0, 3.0
body.append(
    f'<line x1="{bx0}" y1="{fy(by0)}" x2="{bx0 + 25}" y2="{fy(by0)}" '
    f'stroke="black" stroke-width="0.4"/>'
    f'<line x1="{bx0}" y1="{fy(by0)-1}" x2="{bx0}" y2="{fy(by0)+1}" '
    f'stroke="black" stroke-width="0.4"/>'
    f'<line x1="{bx0+25}" y1="{fy(by0)-1}" x2="{bx0+25}" y2="{fy(by0)+1}" '
    f'stroke="black" stroke-width="0.4"/>'
    f'<text x="{bx0 + 12.5}" y="{fy(by0) - 1.5}" font-size="2" '
    f'text-anchor="middle">25 mm — verify with ruler after printing at 100%</text>'
)

svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">'
    + "".join(body)
    + "</svg>"
)

OUT = Path(__file__).resolve().parent.parent / "back_panel_template.svg"
OUT.write_text(svg)
print(f"Wrote {OUT}  ({W} x {H} mm, print at 100%)")
