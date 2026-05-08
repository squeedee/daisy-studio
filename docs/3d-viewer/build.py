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

# US Legal page (project default); used as SVG canvas in --page-size-mode 1.
PAGE_W_MM, PAGE_H_MM = 355.6, 215.9


# ----- color palette (composite mode) -----------------------------------------
SUBSTRATE_RGB = (90, 60, 30)        # FR4 brown showing through silk/mask gaps
COPPER_RGB    = (200, 145, 70)      # bare copper / HASL pads
MASK_RGB      = (15, 90, 45)        # green soldermask
MASK_ALPHA    = 215                 # 0..255 — translucency over copper
SILK_RGB      = (235, 235, 225)     # off-white silkscreen
EDGE_RGB      = (40, 25, 10)        # board edge (between top and bottom)


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
    """Export ONE layer to an SVG using the project page (mode 1).
    All SVGs share the same coordinate system, so per-pixel composite is safe."""
    args = [
        KICAD, "pcb", "export", "svg",
        "--layers", layer,
        "--page-size-mode", "1",
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
    """Render a B&W SVG to a uint8 grayscale mask. White=255 ink, black=0 ink
    is what KiCad emits with --black-and-white (paths are black on white bg).

    We invert: returned array is 0=background, 255=ink. Shape: (H, W).
    """
    width = round(PAGE_W_MM * px_per_mm)
    height = round(PAGE_H_MM * px_per_mm)
    # resvg-py rejects "mm" units in width/height attributes — strip them
    # (svg viewBox already encodes the geometry; unitless = px which we override anyway).
    svg = svg_path.read_text()
    svg = _MM_UNIT_RE.sub(r'\1="\2"', svg)
    png_data = bytes(resvg_py.svg_to_bytes(
        svg_string=svg, width=width, height=height,
        background='white',  # B&W SVG bg is transparent; force white so ink reads as 0
    ))
    img = Image.open(io.BytesIO(png_data)).convert("L")
    arr = np.asarray(img, dtype=np.uint8)
    return 255 - arr  # invert: ink → 255


def crop_board(arr: np.ndarray, px_per_mm: float) -> np.ndarray:
    """Crop a full-page raster to the Edge.Cuts rectangle."""
    x0 = round(BOARD_X0 * px_per_mm)
    y0 = round(BOARD_Y0 * px_per_mm)
    x1 = round(BOARD_X1 * px_per_mm)
    y1 = round(BOARD_Y1 * px_per_mm)
    return arr[y0:y1, x0:x1]


def composite_face(side: str, px_per_mm: float, mirror_x: bool = False) -> Image.Image:
    """Build the top or bottom texture by stacking copper, mask, silk masks."""
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

    # Compose RGBA board face.
    img = np.zeros((h, w, 4), dtype=np.uint8)
    img[..., :3] = SUBSTRATE_RGB
    img[..., 3] = 255

    # Copper
    cu = masks["cu"][..., None] / 255.0
    img[..., :3] = (img[..., :3] * (1 - cu) + np.array(COPPER_RGB) * cu).astype(np.uint8)

    # Soldermask: covers everything inside the board EXCEPT mask openings (F.Mask).
    # Mask layer ink = openings. Coverage = 1 - mask_ink.
    coverage = 1.0 - (masks["mask"][..., None] / 255.0)
    a = coverage * (MASK_ALPHA / 255.0)
    img[..., :3] = (
        img[..., :3] * (1 - a) + np.array(MASK_RGB) * a
    ).astype(np.uint8)

    # Silkscreen: opaque white where ink.
    silk = masks["silk"][..., None] / 255.0
    img[..., :3] = (
        img[..., :3] * (1 - silk) + np.array(SILK_RGB) * silk
    ).astype(np.uint8)

    pil = Image.fromarray(img, "RGBA")
    if mirror_x:
        pil = pil.transpose(Image.FLIP_LEFT_RIGHT)
    return pil


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

def build_board_mesh(top_tex: Image.Image, bottom_tex: Image.Image | None) -> trimesh.Scene:
    """Build a glTF scene containing:
      - top face plane with top texture
      - bottom face plane with bottom texture (mirrored on X)
      - thin extrusion for board edge thickness
    Coordinates: same as KiCad GLB export — X = PCB X (m), Y = up (m),
    Z = PCB Y (m). The board occupies Y ∈ [-t/2, +t/2]."""
    # Convert mm → m for glTF.
    x0, x1 = BOARD_X0 / 1000.0, BOARD_X1 / 1000.0
    z0, z1 = BOARD_Y0 / 1000.0, BOARD_Y1 / 1000.0
    yt = +(BOARD_THICKNESS_MM / 2) / 1000.0
    yb = -(BOARD_THICKNESS_MM / 2) / 1000.0

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
    top.visual = trimesh.visual.TextureVisuals(uv=uvs, image=top_tex)
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
        bot.visual = trimesh.visual.TextureVisuals(uv=uvs_b, image=bottom_tex)
        scene.add_geometry(bot, geom_name="board_bottom")

    # --- Edge band ------------------------------------------------------------
    # Side ribbon connecting top and bottom — solid color, no texture.
    edge_v = np.array([
        # north side (Z = z0)
        [x0, yt, z0], [x1, yt, z0], [x1, yb, z0], [x0, yb, z0],
        # south side (Z = z1)
        [x0, yt, z1], [x1, yt, z1], [x1, yb, z1], [x0, yb, z1],
        # west side (X = x0)
        [x0, yt, z0], [x0, yt, z1], [x0, yb, z1], [x0, yb, z0],
        # east side (X = x1)
        [x1, yt, z0], [x1, yt, z1], [x1, yb, z1], [x1, yb, z0],
    ])
    edge_f = []
    for i in range(0, 16, 4):
        edge_f.extend([[i, i + 2, i + 1], [i, i + 3, i + 2]])
    edge_f = np.array(edge_f)
    edge = trimesh.Trimesh(vertices=edge_v, faces=edge_f, process=False)
    edge.visual.face_colors = list(EDGE_RGB) + [255]
    scene.add_geometry(edge, geom_name="board_edge")

    return scene


def merge_scenes(scene: trimesh.Scene, components_glb: Path) -> trimesh.Scene:
    """Append every geometry from components_glb into scene with its world transform."""
    print(f"merging {components_glb}...")
    comp = trimesh.load(str(components_glb))
    if isinstance(comp, trimesh.Scene):
        # Apply each node's world transform to its geometry, then add.
        for node_name in comp.graph.nodes_geometry:
            T, geom_name = comp.graph[node_name]
            geom = comp.geometry[geom_name].copy()
            geom.apply_transform(T)
            # Make geom_name unique in dest
            unique = f"{geom_name}_{node_name}"
            scene.add_geometry(geom, geom_name=unique)
    else:
        scene.add_geometry(comp, geom_name="components")
    return scene


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
        top_tex = composite_face("top", px_per_mm, mirror_x=False)
        top_tex.save(TEX_DIR / "top.png")
        print(f"  saved {TEX_DIR / 'top.png'} ({(TEX_DIR / 'top.png').stat().st_size:,} bytes)")

        bottom_tex = None
        if not args.no_bottom:
            bottom_tex = composite_face("bottom", px_per_mm, mirror_x=True)
            bottom_tex.save(TEX_DIR / "bottom.png")
            print(f"  saved {TEX_DIR / 'bottom.png'}")

        components = TEX_DIR / "_components.glb"
        export_components_glb(components)

        scene = build_board_mesh(top_tex, bottom_tex)
        scene = merge_scenes(scene, components)
    else:  # baked
        top_tex = render_baked("top", target_w, target_h)
        bottom_tex = None
        if not args.no_bottom:
            bottom_tex = render_baked("bottom", target_w, target_h)
            # Bottom render from kicad-cli is already correctly oriented for "looking from below"
        scene = build_board_mesh(top_tex, bottom_tex)

    out = OUT_DIR / "model.glb"
    print(f"writing {out}...")
    scene.export(str(out))
    print(f"  {out.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
