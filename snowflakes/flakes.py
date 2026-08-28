"""Six little snowflakes, drawn as line skeletons and extruded flat.

    python3 flakes.py                 # all six, 70 mm across, 3 mm thick

Every element is a bar between two points with a round cap at each end, so the
narrowest feature in a design is just the smallest width it asks for -- nothing
can accidentally come out thinner than the printer can lay down. A design is one
arm; the arm is mirrored and stepped round six times for the crystal's symmetry.
"""

import argparse
import math

import numpy as np
import shapely
import trimesh
from shapely import affinity
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.ops import unary_union
from trimesh.creation import extrude_polygon

MIN_WALL = 1.4            # mm: about three extrusion widths, the printable floor


# ------------------------------------------------------------------ drawing
def bar(p0, p1, w0, w1):
    """A tapered bar with rounded ends: the convex hull of two circles."""
    return unary_union([Point(p0).buffer(w0 / 2, 48),
                        Point(p1).buffer(w1 / 2, 48)]).convex_hull


def hexagon(c, r, rot=0.0):
    return Polygon([(c[0] + r * math.cos(rot + k * math.pi / 3),
                     c[1] + r * math.sin(rot + k * math.pi / 3)) for k in range(6)])


def along(t, ang, length):
    """Point `length` from the shaft at height `t`, `ang` degrees off the shaft."""
    a = math.radians(ang)
    return (math.sin(a) * length, t + math.cos(a) * length)


def arm(spec, L):
    """One arm, drawn pointing along +y, in millimetres."""
    out = []
    for t0, t1, w0, w1 in spec["shaft"]:
        out.append(bar((0.0, t0 * L), (0.0, t1 * L), w0, w1))

    for br in spec.get("branches", []):
        t, ang, ln, w0, w1 = br[:5]
        subs = br[5] if len(br) > 5 else []
        base = (0.0, t * L)
        tip = along(t * L, ang, ln * L)
        out.append(bar(base, tip, w0, w1))
        for s, sang, sln, sw0, sw1 in subs:
            sbase = (base[0] + (tip[0] - base[0]) * s, base[1] + (tip[1] - base[1]) * s)
            a = math.radians(sang)
            stip = (sbase[0] + math.sin(a) * sln * L, sbase[1] + math.cos(a) * sln * L)
            out.append(bar(sbase, stip, sw0, sw1))

    for t, r in spec.get("plates", []):
        out.append(hexagon((0.0, t * L), r * L, math.pi / 6))
    for t, ang, d, r in spec.get("dots", []):
        p = along(t * L, ang, d * L)
        out.append(Point(p).buffer(r, 48))
    return unary_union(out)


def flake(spec, size):
    """Mirror the arm and step it round six times."""
    L = size / 2
    half = arm(spec, L)
    both = unary_union([half, affinity.scale(half, xfact=-1, origin=(0, 0))])
    kind, r, rot = spec.get("hub", ("hex", 0.15, 0.0))
    hub = (hexagon((0, 0), r * L, rot) if kind == "hex"
           else Point(0, 0).buffer(r * L, 64))
    rings = [hexagon((0, 0), rr * L, math.pi / 2).exterior.buffer(w / 2, 16)
             for rr, w in spec.get("rings", [])]
    geom = unary_union([hub] + rings + [affinity.rotate(both, 60 * k, origin=(0, 0))
                                        for k in range(6)])
    # Snapping to a micron grid drops the near-duplicate points thrown off by
    # unioning dozens of rounded bars; without it the ear-clipping triangulator
    # leaves unfilled slivers and the extrusion comes out with holes in it.
    return shapely.set_precision(geom.simplify(0.02).buffer(0), 1e-3)


# ------------------------------------------------------------------ designs
# t values are fractions of the arm; widths are millimetres.
FLAKES = {
    "star": {
        "hub": ("hex", 0.171, math.pi / 6),
        "shaft": [(0.0, 0.90, 3.6, 1.8)],
        "branches": [(0.40, 58, 0.30, 2.4, 1.5),
                     (0.68, 58, 0.19, 2.0, 1.4)],
        "plates": [(0.90, 0.103)],
    },
    "dendrite": {
        "hub": ("hex", 0.149, math.pi / 6),
        "shaft": [(0.0, 1.0, 3.2, 1.5)],
        "branches": [(0.22, 60, 0.26, 2.2, 1.4),
                     (0.40, 60, 0.23, 2.1, 1.4),
                     (0.57, 60, 0.19, 1.9, 1.4),
                     (0.73, 60, 0.14, 1.8, 1.4),
                     (0.87, 60, 0.10, 1.7, 1.4)],
    },
    "fern": {
        "hub": ("hex", 0.131, math.pi / 6),
        "shaft": [(0.0, 1.0, 3.0, 1.5)],
        "branches": [(0.22, 64, 0.32, 2.0, 1.4, [(0.55, 16, 0.15, 1.5, 1.4)]),
                     (0.48, 64, 0.25, 1.9, 1.4, [(0.55, 16, 0.12, 1.5, 1.4)]),
                     (0.72, 64, 0.18, 1.8, 1.4),
                     (0.90, 64, 0.11, 1.6, 1.4)],
    },
    "plate": {
        "hub": ("hex", 0.314, math.pi / 6),
        "shaft": [(0.0, 0.78, 4.0, 2.6)],
        "branches": [(0.55, 60, 0.16, 1.8, 1.4)],
        "plates": [(0.84, 0.177)],
    },
    "ring": {
        "hub": ("hex", 0.131, math.pi / 6),
        "shaft": [(0.0, 1.0, 3.0, 1.6)],
        "rings": [(0.42, 1.9)],
        "branches": [(0.66, 60, 0.17, 1.9, 1.4),
                     (0.86, 60, 0.10, 1.7, 1.4)],
        "plates": [(0.97, 0.080)],
    },
    "crystal": {
        "hub": ("circle", 0.154, 0.0),
        "shaft": [(0.0, 0.92, 3.4, 1.6)],
        "branches": [(0.30, 55, 0.24, 2.2, 1.5),
                     (0.52, 55, 0.20, 2.0, 1.5),
                     (0.74, 55, 0.15, 1.8, 1.4)],
        "plates": [(0.30, 0.086), (0.98, 0.074)],
    },
}


# ----------------------------------------------------------------- building
def gap_area(poly, gap):
    """Area sitting in slots narrower than `gap` -- a closing fills exactly those.

    Walls that are too thin fail to print; gaps that are too tight fuse shut.
    Only the first is guaranteed by construction, so measure the second.
    """
    closed = poly.buffer(gap / 2, quad_segs=32).buffer(-gap / 2, quad_segs=32)
    return closed.area - poly.area


def thin_fraction(poly, wall):
    """Share of the area in features narrower than `wall` (morphological opening)."""
    opened = poly.buffer(-wall / 2, quad_segs=32).buffer(wall / 2, quad_segs=32)
    if opened.is_empty:
        return 1.0
    return max(0.0, (poly.area - poly.intersection(opened).area) / poly.area)


def build(name, size=45.0, thickness=2.5):
    poly = flake(FLAKES[name], size)
    mesh = extrude_polygon(poly, height=thickness)
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    return poly, mesh


def declared_width(spec):
    """Narrowest element the design asks for -- the width is set, not discovered."""
    w = [v for t0, t1, w0, w1 in spec["shaft"] for v in (w0, w1)]
    for br in spec.get("branches", []):
        w += [br[3], br[4]]
        for sub in (br[5] if len(br) > 5 else []):
            w += [sub[3], sub[4]]
    w += [2 * r for _, _, _, r in spec.get("dots", [])]
    return min(w)


def report(name, poly, mesh):
    lo, hi = mesh.bounds
    pieces = len(poly.geoms) if isinstance(poly, MultiPolygon) else 1
    narrow = declared_width(FLAKES[name])
    # Unioning bars can only ever add material, so the narrowest bar a design
    # asks for is a hard floor on its feature size. The opening test is a
    # cross-check; the small residue it reports is hexagon corners, which a
    # nozzle just rounds off.
    thin = thin_fraction(poly, narrow - 0.2)
    tight = gap_area(poly, 0.8)
    ok = (pieces == 1 and narrow >= MIN_WALL and thin < 0.01 and tight < 15.0
          and mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1)
    print(f"  {name:9s} {hi[0]-lo[0]:5.1f} x {hi[1]-lo[1]:5.1f} mm  {len(mesh.faces):5d} tri  "
          f"{mesh.volume/1000*1.24:4.1f} g  walls >={narrow:.1f} mm  "
          f"gaps <0.8 mm: {tight:4.1f} mm2  pieces {pieces}  "
          f"watertight {str(mesh.is_watertight):5s} {'ok' if ok else 'FAIL'}")
    return ok


def contact_sheet(polys, out, cols=3, px=1500, pad=14):
    """Flat top-down sheet of every design, for judging the drawing."""
    from PIL import Image, ImageDraw
    rows = (len(polys) + cols - 1) // cols
    span = max(max(p.bounds[2] - p.bounds[0], p.bounds[3] - p.bounds[1]) for _, p in polys)
    cell = px // cols
    s = (cell - 2 * pad) / span
    img = Image.new("RGB", (px, cell * rows), (18, 22, 34))
    dr = ImageDraw.Draw(img)
    for i, (name, poly) in enumerate(polys):
        ox, oy = (i % cols) * cell + cell / 2, (i // cols) * cell + cell / 2
        for p in (poly.geoms if isinstance(poly, MultiPolygon) else [poly]):
            dr.polygon([(ox + x * s, oy - y * s) for x, y in p.exterior.coords],
                       fill=(226, 238, 252))
            for ring in p.interiors:
                dr.polygon([(ox + x * s, oy - y * s) for x, y in ring.coords],
                           fill=(18, 22, 34))
        dr.text((ox - cell / 2 + 10, oy + cell / 2 - 18), name, fill=(120, 140, 170))
    img.save(out)
    print(f"  wrote {out}")


def plate(meshes, gap=6.0, cols=3):
    """Lay every flake out on one build plate, ready to slice in a single go."""
    span = max(m.extents[0] for m in meshes) + gap
    tall = max(m.extents[1] for m in meshes) + gap
    out = []
    for i, m in enumerate(meshes):
        m = m.copy()
        m.apply_translation([(i % cols - 1) * span, (1 - i // cols) * tall - tall / 2, 0])
        out.append(m)
    return trimesh.util.concatenate(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=float, default=45.0, help="tip to tip, mm")
    ap.add_argument("--thickness", type=float, default=2.5)
    ap.add_argument("--only", default=None, help="build just this design")
    ap.add_argument("--sheet", default="preview.png")
    a = ap.parse_args()

    names = [a.only] if a.only else list(FLAKES)
    polys, meshes, ok = [], [], True
    for name in names:
        poly, mesh = build(name, a.size, a.thickness)
        ok &= report(name, poly, mesh)
        mesh.export(f"snowflake_{name}_{a.size:.0f}mm.stl")
        polys.append((name, poly))
        meshes.append(mesh)

    if len(meshes) > 1:
        sheet = plate(meshes)
        sheet.export(f"snowflakes_all_{a.size:.0f}mm.stl")
        print(f"  plate     {sheet.extents[0]:.0f} x {sheet.extents[1]:.0f} mm, "
              f"{sheet.body_count} bodies -> snowflakes_all_{a.size:.0f}mm.stl")
    if a.sheet:
        contact_sheet(polys, a.sheet)
    raise SystemExit(0 if ok else 1)
