"""
Convert SDS-50J.stp to a WRL where each CAD face is its own IndexedFaceSet.
Vertices are not shared across CAD-face boundaries, so corners stay sharp
when re-tessellated by OCCT's GLB writer (no auto-smoothing across edges).
Within a face, vertices are shared and creaseAngle keeps curves smooth.
"""
import os
import Part

src = "/Users/rash/workspace/daisy-studio/daisy-studio.pretty/SDS-50J.original.stp"
dst = "/Users/rash/workspace/daisy-studio/daisy-studio.pretty/SDS-50J.wrl"

shape = Part.Shape()
shape.read(src)
print(f"loaded: faces={len(shape.Faces)} solids={len(shape.Solids)}")

DIFFUSE = (0.20, 0.20, 0.20)
SPEC    = (0.05, 0.05, 0.05)
SHIN    = 0.15

out = []
out.append("#VRML V2.0 utf8")
out.append("Transform {")
out.append("  children [")

total_tris = 0
total_pts = 0

for fi, face in enumerate(shape.Faces):
    # Tessellate this face only — returns (vertices, triangle_indices)
    verts, tris = face.tessellate(0.05)
    if not verts or not tris:
        continue
    total_pts += len(verts)
    total_tris += len(tris)

    out.append("    Shape {")
    out.append("      appearance Appearance {")
    out.append("        material Material {")
    out.append(f"          diffuseColor {DIFFUSE[0]:.3f} {DIFFUSE[1]:.3f} {DIFFUSE[2]:.3f}")
    out.append(f"          specularColor {SPEC[0]:.3f} {SPEC[1]:.3f} {SPEC[2]:.3f}")
    out.append(f"          shininess {SHIN}")
    out.append("        }")
    out.append("      }")
    out.append("      geometry IndexedFaceSet {")
    out.append("        creaseAngle 0.785398")
    out.append("        solid TRUE")
    out.append("        coord Coordinate { point [")
    for v in verts:
        out.append(f"          {v.x:.4f} {v.y:.4f} {v.z:.4f},")
    out.append("        ] }")
    out.append("        coordIndex [")
    for t in tris:
        out.append(f"          {t[0]} {t[1]} {t[2]} -1,")
    out.append("        ]")
    out.append("      }")
    out.append("    }")

out.append("  ]")
out.append("}")

with open(dst, "w") as f:
    f.write("\n".join(out))

print(f"wrote {dst}")
print(f"  faces written: {len(shape.Faces)}")
print(f"  total vertices: {total_pts}")
print(f"  total triangles: {total_tris}")
print(f"  size: {os.path.getsize(dst)} bytes")
