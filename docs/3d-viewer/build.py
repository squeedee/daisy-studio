#!/usr/bin/env python3
"""
build.py — generate model.glb for the 3D viewer.

Two modes (--mode flag):

  composite (default):
    - Export F.Cu, F.Mask, F.SilkS, B.* as individual B&W SVG layers.
    - Rasterize each, composite into top.png / bottom.png with our chosen
      substrate / copper / mask / silk colors. No baked lighting.
    - Build a flat textured board mesh, merge with a components-only
      KiCad GLB export.

  baked:
    - kicad-cli pcb render top + bottom raytraced PNGs (includes shadows
      and components — components are baked into the texture).
    - Build a flat textured board mesh ONLY. No live 3D components.
      Lighter file, less interactive.

Run from anywhere:
    .venv-3d/bin/python docs/3d-viewer/build.py composite
    .venv-3d/bin/python docs/3d-viewer/build.py baked --resolution 4096
"""

import argparse
import io
import json
import math
import re
import struct
import subprocess
from pathlib import Path

import numpy as np
import resvg_py
import trimesh
from PIL import Image

REPO = Path(__file__).resolve().parent.parent.parent
PCB = REPO / "daisy-studio.kicad_pcb"
KICAD = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
OUT_DIR = REPO / "docs/3d-viewer"
TEX_DIR = OUT_DIR / "textures"

# Board outline (Edge.Cuts rectangle) in PCB mm coordinates.
BOARD_X0, BOARD_Y0 = 25.35, 25.3
BOARD_X1, BOARD_Y1 = 303.7, 82.0
BOARD_W = BOARD_X1 - BOARD_X0
BOARD_H = BOARD_Y1 - BOARD_Y0
BOARD_THICKNESS_MM = 1.6

# With --fit-page-to-board, KiCad fits the SVG canvas to all plottable content
# (Edge.Cuts + any layer overflow like rotated silkscreen text). Same bbox is
# returned for every layer of the same project, so layers composite pixel-for-
# pixel. Measured for daisy-studio.kicad_pcb; if the board changes, re-run
# `kicad-cli pcb export svg --layers Edge.Cuts --fit-page-to-board ...` and
# update these.
PAGE_W_MM, PAGE_H_MM = 278.4856, 70.5612

# Texture-vs-component alignment calibration. Source: in-viewer sliders
# (index.html). Workflow: load the page, dial sliders until pads/silk align
# with their 3D components, hit Copy, paste values here, rerun this build.
# After baking, the sliders can sit at zero — this is the residual that the
# automatic SVG-path-derived crop doesn't catch (rasterizer sub-pixel quirks,
# stroke-width nuances).
CAL_OFFSET_X_MM = -0.23   # slider 'length offset'
CAL_OFFSET_Y_MM = -0.25   # slider 'width offset'
CAL_SCALE_X     = 0.9985  # slider 'length scale'
CAL_SCALE_Y     = 1.0025  # slider 'width scale'


# ----- color palette (composite mode) -----------------------------------------
SUBSTRATE_RGB = (90, 60, 30)        # FR4 brown showing through silk/mask gaps
COPPER_RGB    = (200, 145, 70)      # bare copper / HASL pads
MASK_RGB      = (15, 90, 45)        # green soldermask
MASK_ALPHA    = 215                 # 0..255 — translucency over copper
SILK_RGB      = (235, 235, 225)     # off-white silkscreen
EDGE_RGB      = (40, 25, 10)        # board edge (between top and bottom)

# ----- PBR material per layer  -----------------------------------------------
# glTF metallic-roughness texture:
#   R = occlusion (we keep at 1.0 = no AO)
#   G = roughness (0 = mirror, 255 = matte)
#   B = metallic  (0 = dielectric, 255 = metal)
ROUGH_SUBSTRATE = 230   # rough FR4 weave
ROUGH_COPPER    =  20   # nearly mirror finish
ROUGH_MASK      = 180   # matte-ish soldermask (was glossy)
ROUGH_SILK      = 230   # matte ink
METAL_COPPER    = 255   # full metal
METAL_DIELEC    =   0


def run(*cmd, **kw):
    """subprocess.run with stdout passthrough, fail loud on nonzero."""
    p = subprocess.run(cmd, **kw, text=True, capture_output=True)
    if p.returncode != 0:
        print("CMD FAILED:", " ".join(str(c) for c in cmd))
        print(p.stdout)
        print(p.stderr)
        raise SystemExit(p.returncode)
    return p


def export_layer_svg(layer: str, out_path: Path, black_and_white: bool = True):
    """Export ONE layer to an SVG fitted tight to the board+overflow.
    All SVGs of the same project share the same viewBox so layers composite
    pixel-for-pixel."""
    args = [
        KICAD, "pcb", "export", "svg",
        "--layers", layer,
        "--fit-page-to-board",
        "--exclude-drawing-sheet",
        "--mode-single",
        "--output", str(out_path),
    ]
    if black_and_white:
        args.append("--black-and-white")
    args.append(str(PCB))
    run(*args)


_MM_UNIT_RE = __import__("re").compile(r'(width|height)="([\d.]+)mm"')


def rasterize_svg_mask(svg_path: Path, px_per_mm: float) -> np.ndarray:
    """Render a B&W SVG to a uint8 grayscale mask. KiCad's --black-and-white
    SVG draws paths as black on transparent; with background='white', ink reads
    as low values. We invert so 255 = ink, 0 = background. Shape: (H, W).

    NOTE on resvg-py sizing: when BOTH width and height are passed, resvg
    rounds the content scale internally and undersizes by ~30 px on the right
    edge. Passing only width and letting resvg compute height from the SVG
    viewBox aspect produces correct, full-width content. Verified empirically.
    """
    width = round(PAGE_W_MM * px_per_mm)
    # Strip "mm" suffix — resvg-py rejects unit-suffixed dimensions.
    svg = svg_path.read_text()
    svg = _MM_UNIT_RE.sub(r'\1="\2"', svg)
    png_data = bytes(resvg_py.svg_to_bytes(
        svg_string=svg, width=width, background='white',
    ))
    img = Image.open(io.BytesIO(png_data)).convert("L")
    arr = np.asarray(img, dtype=np.uint8)
    return 255 - arr  # invert: ink → 255


_CROP_BOX_CACHE: dict[float, tuple[int, int, int, int]] = {}
_EDGE_CUTS_SVG_BBOX_CACHE: tuple[float, float, float, float] | None = None


def get_edge_cuts_svg_bbox() -> tuple[float, float, float, float]:
    """Parse the Edge.Cuts SVG path to extract the rect's CENTERLINE coords
    (in SVG mm). Returns (x_min, y_min, x_max, y_max). KiCad emits Edge.Cuts
    as a `<path d="M x0,y0 x1,y0 x1,y1 x0,y1 Z" />` — we just read the path."""
    global _EDGE_CUTS_SVG_BBOX_CACHE
    if _EDGE_CUTS_SVG_BBOX_CACHE is not None:
        return _EDGE_CUTS_SVG_BBOX_CACHE

    edge_svg = TEX_DIR / "_edge.svg"
    if not edge_svg.exists():
        export_layer_svg("Edge.Cuts", edge_svg)
    text = edge_svg.read_text()
    # The first <path d="M ..."> in the Edge.Cuts SVG is the board outline.
    m = __import__("re").search(
        r'<path[^>]*d="M\s*([\d.-]+),([\d.-]+)\s+([\d.-]+),([\d.-]+)\s+([\d.-]+),([\d.-]+)',
        text,
    )
    if not m:
        raise RuntimeError("Could not locate Edge.Cuts path in SVG")
    x0, y0 = float(m[1]), float(m[2])
    x1, _ = float(m[3]), float(m[4])
    _, y1 = float(m[5]), float(m[6])
    raw = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
    print(f"  Edge.Cuts SVG path bbox: {raw} mm")

    # Apply user-tuned calibration (see CAL_* constants above).
    # Center shift comes from the slider 'offset' values; width/height shrink
    # by the slider 'scale' values (zoom = expand source crop region).
    cx = (raw[0] + raw[2]) / 2 - CAL_OFFSET_X_MM
    cy = (raw[1] + raw[3]) / 2 + CAL_OFFSET_Y_MM
    w  = (raw[2] - raw[0]) / CAL_SCALE_X
    h  = (raw[3] - raw[1]) / CAL_SCALE_Y
    bbox = (cx - w/2, cy - h/2, cx + w/2, cy + h/2)
    print(f"  after calibration: {bbox} mm "
          f"(center shift X={-CAL_OFFSET_X_MM:+.3f} Y={CAL_OFFSET_Y_MM:+.3f}, "
          f"size ×({1/CAL_SCALE_X:.4f},{1/CAL_SCALE_Y:.4f}))")
    _EDGE_CUTS_SVG_BBOX_CACHE = bbox
    return bbox


def get_crop_box(px_per_mm: float) -> tuple[int, int, int, int]:
    """(x0, y0, x1, y1) pixel crop covering the Edge.Cuts CENTERLINE rectangle
    in the rendered raster. Uses the path coordinates parsed straight from the
    SVG — sidesteps inkbbox + stroke-width approximation, which was off by
    fractions of a millimetre."""
    if px_per_mm in _CROP_BOX_CACHE:
        return _CROP_BOX_CACHE[px_per_mm]

    sx0, sy0, sx1, sy1 = get_edge_cuts_svg_bbox()
    box = (
        round(sx0 * px_per_mm),
        round(sy0 * px_per_mm),
        round(sx1 * px_per_mm),
        round(sy1 * px_per_mm),
    )
    _CROP_BOX_CACHE[px_per_mm] = box
    print(f"  centerline crop @ {px_per_mm:.4f} px/mm: {box} "
          f"(mm: {box[0]/px_per_mm:.3f},{box[1]/px_per_mm:.3f} → "
          f"{box[2]/px_per_mm:.3f},{box[3]/px_per_mm:.3f})")
    return box


def crop_board(arr: np.ndarray, px_per_mm: float) -> np.ndarray:
    """Crop the full-page raster tight to the Edge.Cuts CENTERLINE rect.

    Two axes need independent scale factors: resvg renders the SVG with NON-
    uniform scaling (verified empirically — horizontal scale matches `width=`
    arg exactly, vertical can be off by ~0.8% from viewBox aspect). Using a
    single px_per_mm shifts content widthwise by a fraction of a millimetre.
    Compute axis-specific px/mm from the actual image dimensions and the
    fitted-SVG canvas size, then sample at sub-pixel float coords via PIL
    bilinear."""
    sx0, sy0, sx1, sy1 = get_edge_cuts_svg_bbox()
    img_h, img_w = arr.shape[:2]
    ppm_x = img_w / PAGE_W_MM
    ppm_y = img_h / PAGE_H_MM
    fx0, fy0 = sx0 * ppm_x, sy0 * ppm_y
    fx1, fy1 = sx1 * ppm_x, sy1 * ppm_y
    # Use the requested px_per_mm to size the OUTPUT (so all layers share the
    # same final dimensions even with axis-asymmetric source rasters).
    out_w = round((sx1 - sx0) * px_per_mm)
    out_h = round((sy1 - sy0) * px_per_mm)
    sx_out_to_in = (fx1 - fx0) / out_w
    sy_out_to_in = (fy1 - fy0) / out_h
    img = Image.fromarray(arr)
    # AFFINE: input_x = sx_out_to_in * out_x + fx0, input_y = sy_out_to_in * out_y + fy0.
    cropped = img.transform(
        (out_w, out_h), Image.AFFINE,
        (sx_out_to_in, 0, fx0, 0, sy_out_to_in, fy0),
        resample=Image.BILINEAR,
    )
    return np.asarray(cropped, dtype=np.uint8)


def composite_face(side: str, px_per_mm: float, mirror_x: bool = False) -> tuple[Image.Image, Image.Image]:
    """Build the top or bottom face textures: returns (baseColor_RGBA, metallicRoughness_RGB)."""
    prefix = "F" if side == "top" else "B"
    print(f"[{side}] exporting layers...")

    layers = {
        "cu":   f"{prefix}.Cu",
        "mask": f"{prefix}.Mask",
        "silk": f"{prefix}.SilkS",
    }
    masks = {}
    for key, layer in layers.items():
        svg = TEX_DIR / f"{side}-{key}.svg"
        export_layer_svg(layer, svg)
        full = rasterize_svg_mask(svg, px_per_mm)
        masks[key] = crop_board(full, px_per_mm)
        print(f"  {layer:12s} -> {masks[key].shape[1]}x{masks[key].shape[0]} px")

    h, w = masks["cu"].shape

    # ----- Base color -----
    img = np.zeros((h, w, 4), dtype=np.uint8)
    img[..., :3] = SUBSTRATE_RGB
    img[..., 3] = 255

    cu = masks["cu"][..., None] / 255.0
    img[..., :3] = (img[..., :3] * (1 - cu) + np.array(COPPER_RGB) * cu).astype(np.uint8)

    # Soldermask: covers everything except where F.Mask has openings (ink).
    coverage = 1.0 - (masks["mask"][..., None] / 255.0)
    a = coverage * (MASK_ALPHA / 255.0)
    img[..., :3] = (img[..., :3] * (1 - a) + np.array(MASK_RGB) * a).astype(np.uint8)

    silk = masks["silk"][..., None] / 255.0
    img[..., :3] = (img[..., :3] * (1 - silk) + np.array(SILK_RGB) * silk).astype(np.uint8)

    # ----- Metallic / roughness -----
    # Compute per-pixel material lookup. Order of precedence (front-to-back):
    # silk on top, then mask coverage (where mask isn't opened), then copper
    # under mask openings, then bare substrate.
    cu_a    = masks["cu"]   / 255.0
    mask_a  = (1.0 - masks["mask"] / 255.0)   # 1 = mask covers, 0 = opening
    silk_a  = masks["silk"] / 255.0

    rough = np.full((h, w), ROUGH_SUBSTRATE, dtype=np.float32)
    metal = np.full((h, w), METAL_DIELEC,    dtype=np.float32)

    # Copper showing through mask opening: under-mask = copper visible only
    # where mask is opened. Bare-copper roughness/metallic.
    cu_visible = cu_a * (1.0 - mask_a)  # copper not covered by mask
    rough = rough * (1 - cu_visible) + ROUGH_COPPER * cu_visible
    metal = metal * (1 - cu_visible) + METAL_COPPER * cu_visible

    # Soldermask coverage (everywhere mask covers, regardless of underlying)
    rough = rough * (1 - mask_a) + ROUGH_MASK * mask_a
    # Mask is dielectric — metal stays at whatever's beneath; force to 0
    # under mask coverage.
    metal = metal * (1 - mask_a) + METAL_DIELEC * mask_a

    # Silk on top of everything
    rough = rough * (1 - silk_a) + ROUGH_SILK * silk_a
    metal = metal * (1 - silk_a) + METAL_DIELEC * silk_a

    mr = np.zeros((h, w, 3), dtype=np.uint8)
    mr[..., 0] = 255                   # occlusion = 1.0 (no AO)
    mr[..., 1] = rough.astype(np.uint8)  # G = roughness
    mr[..., 2] = metal.astype(np.uint8)  # B = metallic

    base = Image.fromarray(img, "RGBA")
    mr_img = Image.fromarray(mr, "RGB")
    if mirror_x:
        base = base.transpose(Image.FLIP_LEFT_RIGHT)
        mr_img = mr_img.transpose(Image.FLIP_LEFT_RIGHT)
    return base, mr_img


def render_baked(side: str, w: int, h: int) -> Image.Image:
    """kicad-cli raytraced render — top or bottom, components included."""
    out = TEX_DIR / f"{side}-baked.png"
    print(f"[{side}] raytraced render -> {out}...")
    run(
        KICAD, "pcb", "render",
        "--side", side,
        "--width", str(w),
        "--height", str(h),
        "--background", "transparent",
        "--quality", "high",
        "--output", str(out),
        str(PCB),
    )
    return Image.open(out).convert("RGBA")


def export_components_glb(out_path: Path):
    """Components-only GLB (no board body, no tracks/silk/mask geometry).
    Used in composite mode where we replace the board with a textured plane."""
    print(f"exporting components-only GLB -> {out_path}...")
    run(
        KICAD, "pcb", "export", "glb",
        "--no-board-body",
        "--subst-models",
        "--force",
        "--output", str(out_path),
        str(PCB),
    )


# ----- mesh construction ------------------------------------------------------

def build_board_mesh(
    top_tex: Image.Image,
    bottom_tex: Image.Image | None,
    top_mr: Image.Image | None = None,
    bottom_mr: Image.Image | None = None,
) -> trimesh.Scene:
    """Build a glTF scene containing:
      - top face plane with top texture
      - bottom face plane with bottom texture (mirrored on X)
      - thin extrusion for board edge thickness
    Coordinates: same as KiCad GLB export — X = PCB X (m), Y = up (m),
    Z = PCB Y (m). The board occupies Y ∈ [-t/2, +t/2]."""
    # Convert mm → m for glTF.
    # KiCad's GLB export places the board substrate from Y=0 (bottom copper)
    # to Y=+thickness (top copper), with SMD component bases sitting on the
    # top surface. Match that so components don't float above the texture.
    x0, x1 = BOARD_X0 / 1000.0, BOARD_X1 / 1000.0
    z0, z1 = BOARD_Y0 / 1000.0, BOARD_Y1 / 1000.0
    yt = BOARD_THICKNESS_MM / 1000.0
    yb = 0.0

    scene = trimesh.Scene()

    # --- Top face -------------------------------------------------------------
    # CCW winding viewed from above (+Y normal). For glTF: standard right-hand
    # rule, fingers curl in vertex order, thumb = normal.
    vertices = np.array([
        [x0, yt, z0],   # 0: NW
        [x1, yt, z0],   # 1: NE
        [x1, yt, z1],   # 2: SE
        [x0, yt, z1],   # 3: SW
    ])
    # UVs: PNG origin is top-left. SVG plotted with KiCad Y down, so KiCad Y+ → V+.
    # We want top-left of texture to align with NW corner (X0, Y0 in PCB).
    # V flipped: trimesh/glTF effectively places texture row 0 at V=1 in our
    # build (verified empirically — UVs that "should" map small-PCB-Y to V=0
    # render with widthwise axis reversed). So V=1 at small Z, V=0 at large Z.
    uvs = np.array([
        [0.0, 1.0],  # NW (small PCB-Y) → texture top
        [1.0, 1.0],  # NE
        [1.0, 0.0],  # SE (large PCB-Y) → texture bottom
        [0.0, 0.0],  # SW
    ])
    # Winding NW → SW → SE gives normal (0, +Y, 0) — face normal points up.
    faces = np.array([[0, 3, 2], [0, 2, 1]])
    top = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    top.visual = trimesh.visual.TextureVisuals(
        uv=uvs,
        material=trimesh.visual.material.PBRMaterial(
            name="board_top_pbr",
            baseColorTexture=top_tex,
            metallicRoughnessTexture=top_mr,
            metallicFactor=1.0,
            roughnessFactor=1.0,
        ),
    )
    scene.add_geometry(top, geom_name="board_top")

    # --- Bottom face ----------------------------------------------------------
    if bottom_tex is not None:
        vertices_b = np.array([
            [x0, yb, z0],   # 0: NW
            [x1, yb, z0],   # 1: NE
            [x1, yb, z1],   # 2: SE
            [x0, yb, z1],   # 3: SW
        ])
        # Bottom view is mirrored on X (looking up from below, KiCad's B.* plot
        # is "as seen from above looking through the board", so X needs to flip).
        # Same V-flip as top face (see comment on top-face UVs).
        uvs_b = np.array([
            [1.0, 1.0],  # NW (small PCB-Y) → texture top-right (X mirrored for back layer)
            [0.0, 1.0],  # NE
            [0.0, 0.0],  # SE (large PCB-Y) → texture bottom-left
            [1.0, 0.0],  # SW
        ])
        # Winding NW → NE → SE gives normal (0, -Y, 0) — face normal points down.
        faces_b = np.array([[0, 1, 2], [0, 2, 3]])
        bot = trimesh.Trimesh(vertices=vertices_b, faces=faces_b, process=False)
        bot.visual = trimesh.visual.TextureVisuals(
            uv=uvs_b,
            material=trimesh.visual.material.PBRMaterial(
                name="board_bottom_pbr",
                baseColorTexture=bottom_tex,
                metallicRoughnessTexture=bottom_mr,
                metallicFactor=1.0,
                roughnessFactor=1.0,
            ),
        )
        scene.add_geometry(bot, geom_name="board_bottom")

    # --- Edge band ------------------------------------------------------------
    # Side ribbon connecting top and bottom — solid color, no texture.
    # Each side: 4 vertices ordered CCW when viewed from OUTSIDE the board, so
    # the outward normal comes out of the (a→b) × (b→c) cross product.
    edge_v = np.array([
        # NORTH (z=z0, outward normal -Z)
        [x0, yt, z0], [x1, yt, z0], [x1, yb, z0], [x0, yb, z0],
        # SOUTH (z=z1, outward normal +Z)
        [x1, yt, z1], [x0, yt, z1], [x0, yb, z1], [x1, yb, z1],
        # WEST  (x=x0, outward normal -X)
        [x0, yt, z1], [x0, yt, z0], [x0, yb, z0], [x0, yb, z1],
        # EAST  (x=x1, outward normal +X)
        [x1, yt, z0], [x1, yt, z1], [x1, yb, z1], [x1, yb, z0],
    ])
    edge_f = []
    for i in range(0, 16, 4):
        edge_f.extend([[i, i + 1, i + 2], [i, i + 2, i + 3]])
    edge_f = np.array(edge_f)
    edge = trimesh.Trimesh(vertices=edge_v, faces=edge_f, process=False)
    edge.visual.face_colors = list(EDGE_RGB) + [255]
    scene.add_geometry(edge, geom_name="board_edge")

    return scene


_REF_SAFE = re.compile(r"[^A-Za-z0-9]")
# glTF / three.js GLTFLoader silently strips characters from node names —
# notably "." (e.g. "P2.54mm" -> "P254mm"), spaces, and parens — so any name
# we generate at build time must be sanitized the SAME way before we save it
# to components.json, otherwise the runtime map keys won't match the loaded
# Mesh.name values.
_NAME_SAFE = re.compile(r"[^A-Za-z0-9_\-]")


def sanitize_glb_name(name: str) -> str:
    """Return name with characters that GLTFLoader strips removed."""
    return _NAME_SAFE.sub("", name)


def parse_footprints() -> list[dict]:
    """Walk the .kicad_pcb file and pull out every footprint's reference,
    value, lib_id, position, layer. Used to map glTF leaf meshes back to a
    reference designator for hover highlighting."""
    text = PCB.read_text()
    out = []
    # Footprint blocks live at indent level 1 (one tab); they close with `\n\t)\n`.
    for m in re.finditer(r'\(footprint "([^"]+)"(.*?)\n\t\)\n', text, re.DOTALL):
        lib_id = m.group(1)
        block = m.group(2)
        ref_m = re.search(r'\(property "Reference" "([^"]+)"', block)
        val_m = re.search(r'\(property "Value" "([^"]+)"', block)
        at_m = re.search(r'\(at\s+([\-\d.]+)\s+([\-\d.]+)(?:\s+([\-\d.]+))?\)', block)
        layer_m = re.search(r'\(layer "([^"]+)"\)', block)
        if not (ref_m and at_m):
            continue
        out.append({
            "ref": ref_m.group(1),
            "value": val_m.group(1) if val_m else "",
            "lib_id": lib_id,
            "pos": [float(at_m.group(1)), float(at_m.group(2))],
            "layer": layer_m.group(1) if layer_m else "F.Cu",
        })
    print(f"parsed {len(out)} footprints from {PCB.name}")
    return out


def merge_scenes(
    scene: trimesh.Scene,
    components_glb: Path,
    footprints: list[dict] | None = None,
) -> tuple[trimesh.Scene, dict]:
    """Append every geometry from components_glb into scene (with world transform).

    If `footprints` is provided, each leaf is matched to its nearest footprint
    (by 2D PCB-space distance to the leaf's centroid). The output mesh name
    is rewritten to `comp_<REF>__<orig_name>` so the viewer can read the ref
    directly from `Object3D.name`. A second return value is the per-ref index
    used to write components.json (bbox + mesh names + value/lib_id/layer).
    """
    print(f"merging {components_glb}...")
    comp = trimesh.load(str(components_glb))
    index_by_ref: dict[str, dict] = {}

    if not isinstance(comp, trimesh.Scene):
        scene.add_geometry(comp, geom_name="components")
        return scene, index_by_ref

    fp_by_ref = {f["ref"]: f for f in (footprints or [])}
    parents = comp.graph.transforms.parents  # node_name -> parent_name dict

    def parent_chain(node):
        """Yield the parent chain of `node`, omitting `node` itself."""
        cur = node
        for _ in range(32):  # guard against cycles
            p = parents.get(cur)
            if not p or p == cur or p == "world":
                return
            yield p
            cur = p

    for node_name in comp.graph.nodes_geometry:
        T, geom_name = comp.graph[node_name]
        geom = comp.geometry[geom_name].copy()
        geom.apply_transform(T)

        # KiCad's GLB exporter writes each footprint as a parent node named
        # after its reference designator (e.g. 'R24', 'U2'); the leaf meshes
        # are children. Walk up the parent chain to find a name that matches
        # a known footprint ref — way more reliable than position matching.
        ref = None
        for p in parent_chain(node_name):
            if p in fp_by_ref:
                ref = p
                break
        fp = fp_by_ref.get(ref) if ref else None

        prefix = f"comp_{_REF_SAFE.sub('_', ref)}__" if ref else "comp_unknown__"
        unique = f"{prefix}{geom_name[:32]}_{node_name[-10:]}"[:96]
        unique = sanitize_glb_name(unique)
        scene.add_geometry(geom, geom_name=unique)

        if ref and fp:
            entry = index_by_ref.setdefault(ref, {
                "value": fp["value"],
                "lib_id": fp["lib_id"],
                "pos_pcb": fp["pos"],
                "layer": fp["layer"],
                "mesh_names": [],
                "bbox_gltf": [list(geom.bounds[0]), list(geom.bounds[1])],
            })
            entry["mesh_names"].append(unique)
            lo, hi = entry["bbox_gltf"]
            entry["bbox_gltf"] = [
                [min(lo[i], geom.bounds[0][i]) for i in range(3)],
                [max(hi[i], geom.bounds[1][i]) for i in range(3)],
            ]

    return scene, index_by_ref


# ----- main -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["composite", "baked"], default="composite",
                        nargs="?", help="texture generation mode")
    parser.add_argument("--resolution", type=int, default=8192,
                        help="texture width in pixels (default 8192)")
    parser.add_argument("--no-bottom", action="store_true",
                        help="skip bottom-face texture (top only)")
    args = parser.parse_args()

    TEX_DIR.mkdir(parents=True, exist_ok=True)

    target_w = args.resolution
    target_h = round(target_w * BOARD_H / BOARD_W)
    px_per_mm = target_w / BOARD_W

    print(f"mode: {args.mode}")
    print(f"target texture: {target_w} x {target_h} ({px_per_mm:.2f} px/mm)")

    if args.mode == "composite":
        top_tex, top_mr = composite_face("top", px_per_mm, mirror_x=False)
        top_tex.save(TEX_DIR / "top.png")
        top_mr.save(TEX_DIR / "top-mr.png")
        print(f"  saved {TEX_DIR / 'top.png'} + top-mr.png")

        bottom_tex, bottom_mr = (None, None)
        if not args.no_bottom:
            bottom_tex, bottom_mr = composite_face("bottom", px_per_mm, mirror_x=True)
            bottom_tex.save(TEX_DIR / "bottom.png")
            bottom_mr.save(TEX_DIR / "bottom-mr.png")
            print(f"  saved {TEX_DIR / 'bottom.png'} + bottom-mr.png")

        components = TEX_DIR / "_components.glb"
        export_components_glb(components)

        footprints = parse_footprints()
        scene = build_board_mesh(top_tex, bottom_tex, top_mr, bottom_mr)
        scene, index = merge_scenes(scene, components, footprints)
        # Drop a per-ref hover index next to model.glb. Keys: ref designator;
        # values: { value, lib_id, pos_pcb, layer, mesh_names, bbox_gltf }.
        (OUT_DIR / "components.json").write_text(json.dumps(index, indent=2))
        print(f"  wrote components.json ({len(index)} refs)")
    else:  # baked
        top_tex = render_baked("top", target_w, target_h)
        bottom_tex = None
        if not args.no_bottom:
            bottom_tex = render_baked("bottom", target_w, target_h)
        scene = build_board_mesh(top_tex, bottom_tex)

    out = OUT_DIR / "model.glb"
    print(f"writing {out}...")
    scene.export(str(out))
    print(f"  {out.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
