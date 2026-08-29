"""Mesh the tiara: flat back, rounded strands, domed stones.

    python3 tiara.py --out tiara_comb_95mm.stl

The piece is a height field over a flat base -- every surface either rises from
the bed or curves over -- so it prints face-up with no supports anywhere, and the
back comes out flat against the hair. Strands are rounded to their own half
width, so a 2.2 mm strand ends up round in section like wire; stones sit on top
as hemispheres of the radius they were drawn with.
"""

import argparse

import numpy as np
import shapely
import trimesh
from shapely import affinity
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union
from skimage.measure import marching_cubes

import design

COMB_T = 2.6              # mm: band and comb, the structural part
JEWEL_T = 1.2             # mm: flat core under the scrollwork, before the doming
STRAND_R = 1.3            # mm: strands round over to this radius
BAND_R = 1.2              # mm: how far the crescent's edges roll over


def parts(g):
    return list(g.geoms) if isinstance(g, MultiPolygon) else [g]


def segments(poly):
    a, b = [], []
    for p in parts(poly):
        for ring in [p.exterior, *p.interiors]:
            c = np.asarray(ring.coords)
            a.append(c[:-1])
            b.append(c[1:])
    return np.vstack(a), np.vstack(b)


def distance_2d(poly, X, Y, chunk=30000):
    """Exact signed distance to `poly` over the grid (negative inside)."""
    A, B = segments(poly)
    AB = B - A
    denom = np.einsum("ij,ij->i", AB, AB)
    pts = np.column_stack([X.ravel(), Y.ravel()])
    out = np.empty(len(pts), dtype=np.float32)
    for i in range(0, len(pts), chunk):
        p = pts[i:i + chunk, None, :]
        t = np.clip(np.einsum("psj,sj->ps", p - A[None], AB) / denom, 0.0, 1.0)
        proj = A[None] + t[..., None] * AB[None]
        out[i:i + chunk] = np.sqrt(((p - proj) ** 2).sum(-1)).min(axis=1)
    out[shapely.contains_xy(poly, pts[:, 0], pts[:, 1])] *= -1.0
    return out.reshape(X.shape)


def dome(d, r):
    """Height of a roll-over of radius `r` at signed distance `d` (inside < 0)."""
    u = np.minimum(np.maximum(-d, 0.0), r)
    return np.sqrt(np.maximum(r * r - (r - u) ** 2, 0.0))


def height_field(jewel, band, comb, stones, X, Y):
    """How tall the piece stands at each point of the grid."""
    d_band = distance_2d(band, X, Y)
    d_comb = distance_2d(comb, X, Y)
    d_jewel = distance_2d(jewel, X, Y)

    h = np.where(d_comb < 0, COMB_T, 0.0)                  # teeth keep a flat section
    h = np.where(d_band < 0, np.maximum(h, COMB_T + dome(d_band, BAND_R)), h)

    h = np.where(d_jewel < 0, np.maximum(h, JEWEL_T + dome(d_jewel, STRAND_R)), h)

    for (cx, cy), r in stones:                             # set the stones on top
        d2 = (X - cx) ** 2 + (Y - cy) ** 2
        cap = np.sqrt(np.maximum(r * r - d2, 0.0))
        h = np.maximum(h, np.where(d2 < r * r, JEWEL_T + cap, 0.0))
    return h, np.minimum(np.minimum(d_band, d_comb), d_jewel)


def build(voxel=0.25, decimate=None, scale=1.0, verbose=True):
    jewel, band, comb, stones = design.build()
    if scale != 1.0:
        # Scale the drawing only: thicknesses stay in millimetres, because they
        # are set by what the printer can do, not by how big the tiara is.
        jewel, band, comb = (affinity.scale(g, scale, scale, origin=(0, 0))
                             for g in (jewel, band, comb))
        stones = [((cx * scale, cy * scale), r * scale) for (cx, cy), r in stones]
    whole = unary_union([jewel, band, comb])
    x0, y0, x1, y1 = whole.bounds
    pad = 1.5
    xs = np.arange(x0 - pad, x1 + pad, voxel, dtype=np.float32)
    ys = np.arange(y0 - pad, y1 + pad, voxel, dtype=np.float32)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    if verbose:
        print(f"  outline {x1-x0:.1f} x {y1-y0:.1f} mm, {len(stones)} stones, "
              f"grid {len(xs)}x{len(ys)}")

    h, d2 = height_field(jewel, band, comb, stones, X, Y)
    zs = np.arange(-0.75, h.max() + 0.75, voxel, dtype=np.float32)
    Z = zs[None, None, :]

    # Solid where we are inside the outline and between the bed and the height
    # field; the max() gives vertical walls, h gives the rounded top.
    f = np.maximum(d2[:, :, None], np.maximum(Z - h[:, :, None], -Z))
    f = f.astype(np.float32)
    for sl in (np.s_[0, :, :], np.s_[-1, :, :], np.s_[:, 0, :], np.s_[:, -1, :],
               np.s_[:, :, 0], np.s_[:, :, -1]):
        f[sl] = np.abs(f[sl]) + 1.0
    f[np.abs(f) < 1e-3] = -1e-3        # flat faces land on grid planes; nudge them off

    verts, faces, _, _ = marching_cubes(f, level=0.0, spacing=(voxel,) * 3)
    verts += np.array([xs[0], ys[0], zs[0]], dtype=verts.dtype)
    m = trimesh.Trimesh(verts, faces, process=False)
    if m.volume < 0:
        m.invert()
    pieces = m.split(only_watertight=False)
    if len(pieces) > 1:
        pieces = sorted(pieces, key=lambda p: -abs(p.volume))
        for p in pieces[1:]:
            print(f"  dropped stray shell: {len(p.faces)} faces, {abs(p.volume):.2f} mm^3")
        m = pieces[0]
    m.merge_vertices()
    m.update_faces(m.nondegenerate_faces())
    m.remove_unreferenced_vertices()
    if decimate and len(m.faces) > decimate:
        m = m.simplify_quadric_decimation(face_count=decimate)
        m.merge_vertices()
        print(f"  decimated to {len(m.faces):,} faces")
    return m, whole


def report(m, whole):
    lo, hi = m.bounds
    print(f"  size      {hi[0]-lo[0]:.1f} W x {hi[2]-lo[2]:.1f} D x {hi[1]-lo[1]:.1f} H mm")
    print(f"  triangles {len(m.faces):,}   bodies {m.body_count}")
    print(f"  volume    {m.volume/1000:.1f} cm^3  (~{m.volume/1000*1.24:.0f} g of PLA solid)")
    print(f"  watertight {m.is_watertight}   winding-consistent {m.is_winding_consistent}"
          f"   euler {m.euler_number}")

    opened = whole.buffer(-0.7, quad_segs=32).buffer(0.7, quad_segs=32)
    thin = whole.area - whole.intersection(opened).area
    closed = whole.buffer(0.4, quad_segs=32).buffer(-0.4, quad_segs=32)
    print(f"  drawing   {len(parts(whole))} connected piece(s); "
          f"{thin:.1f} mm2 in walls under 1.4 mm; "
          f"{closed.area - whole.area:.1f} mm2 in slots under 0.8 mm")

    n, a = m.face_normals, m.area_faces
    down = n[:, 2] < -np.cos(np.radians(45))
    bed = np.abs(m.triangles_center[down][:, 2] - lo[2]) < 0.3 if down.any() else np.array([True])
    print(f"  overhang  {100*a[down].sum()/a.sum():.1f}% faces down steeper than 45 deg"
          f" -- all of it the flat back on the bed: {bool(bed.all())}")
    return (m.is_watertight and m.is_winding_consistent and m.body_count == 1
            and len(parts(whole)) == 1 and thin < 1.0 and bool(bed.all()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0,
                    help="scale the drawing (1.0 = 96 mm wide)")
    ap.add_argument("--voxel", type=float, default=0.25)
    ap.add_argument("--decimate", type=int, default=120000)
    ap.add_argument("--out", default="tiara_comb.stl")
    a = ap.parse_args()
    m, whole = build(a.voxel, a.decimate or None, a.scale)
    ok = report(m, whole)
    m.export(a.out)
    print(f"  wrote {a.out}")
    raise SystemExit(0 if ok else 1)
