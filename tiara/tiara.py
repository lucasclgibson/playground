"""Mesh the tiara: a curved face standing upright, comb at right angles below it.

    python3 tiara.py --out tiara_comb_97mm.stl

The face is drawn flat in `design.py` and wrapped onto a cylinder of radius
`--curve`, so the tiara follows the head. Strands are rounded to their own half
width, giving a round wire section; pin heads become spheres. The comb is a flat
plate at right angles to that face, and the piece prints standing on it -- comb
down on the bed, crown in the air, which is also the way it is worn.
"""

import argparse

import numpy as np
import shapely
import trimesh
from shapely import affinity
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union
from skimage.measure import label, marching_cubes

import design

CURVE_R = 110.0           # mm: radius the face is wrapped on
WALL_T = 2.3              # mm: the face is a constant-thickness wall, square edged
COMB_T = 2.0              # mm: comb thickness where it meets the band
COMB_TIP = 1.2            # mm: ... tapering to this at the tooth tips
SPINE_W = 5.0             # mm: how deep the comb's spine is, front to back
JOIN_K = 1.2              # fillet where the face meets the comb


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


def distance_2d(poly, X, Y, chunk=40000):
    """Exact signed distance to `poly` over a grid (negative inside)."""
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


def lookup_2d(poly, step=0.2, pad=4.0):
    """Precompute the face's distance field once, to sample per 3D voxel.

    Evaluating an exact distance for every voxel would mean millions of points
    against thousands of segments; a flat lookup plus bilinear sampling is the
    same answer for a fraction of the work.
    """
    x0, y0, x1, y1 = poly.bounds
    us = np.arange(x0 - pad, x1 + pad + step, step, dtype=np.float32)
    vs = np.arange(y0 - pad, y1 + pad + step, step, dtype=np.float32)
    U, V = np.meshgrid(us, vs, indexing="ij")
    return distance_2d(poly, U, V), us[0], vs[0], step, us[-1], vs[-1]


def sample_2d(table, U, V):
    D, u0, v0, step, u1, v1 = table
    gu = np.clip((U - u0) / step, 0, D.shape[0] - 1.001)
    gv = np.clip((V - v0) / step, 0, D.shape[1] - 1.001)
    i = gu.astype(np.int32)
    j = gv.astype(np.int32)
    tu, tv = gu - i, gv - j
    out = ((1 - tu) * (1 - tv) * D[i, j] + tu * (1 - tv) * D[i + 1, j]
           + (1 - tu) * tv * D[i, j + 1] + tu * tv * D[i + 1, j + 1])
    # Anything off the edge of the table is outside the face, not near it.
    off = (U < u0) | (U > u1) | (V < v0) | (V > v1)
    return np.where(off, np.maximum(out, 5.0), out)


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b + (a - b) * h - k * h * (1.0 - h)


def build(voxel=0.25, curve_r=CURVE_R, scale=1.0, decimate=None, verbose=True):
    jewel, band, _ = design.face()          # pin heads are discs in the drawing
    if scale != 1.0:
        jewel, band = (affinity.scale(g, scale, scale, origin=(0, 0)) for g in (jewel, band))
    face = unary_union([jewel, band])
    comb = design.comb_plan(curve_r, span=28.0 * scale, spine_w=SPINE_W)

    table = lookup_2d(face)
    u_max = max(abs(face.bounds[0]), abs(face.bounds[2]))
    reach = curve_r * np.sin(u_max / curve_r) + 3.0
    cx0, cy0, cx1, cy1 = comb.bounds
    xs = np.arange(-reach, reach + voxel, voxel, dtype=np.float32)
    ys = np.arange(min(cy0, curve_r * np.cos(u_max / curve_r) - curve_r) - 3.0,
                   max(cy1, 0.0) + 3.0 + voxel, voxel, dtype=np.float32)
    zs = np.arange(-1.0, face.bounds[3] + 2.5 + voxel, voxel, dtype=np.float32)
    if verbose:
        print(f"  face {face.bounds[2]-face.bounds[0]:.1f} x {face.bounds[3]:.1f} mm "
              f"wrapped on R{curve_r:.0f}; grid {len(xs)}x{len(ys)}x{len(zs)} "
              f"= {len(xs)*len(ys)*len(zs)/1e6:.1f}M")

    X = xs[:, None, None]
    Y = ys[None, :, None]
    Z = zs[None, None, :]

    # Wrap: u runs along the head curve, d is the distance off that surface.
    ring = Y + curve_r
    rad = np.sqrt(X * X + ring * ring)
    U = curve_r * np.arctan2(X, ring)
    Dface = sample_2d(table, np.broadcast_to(U, (len(xs), len(ys), 1)),
                      np.broadcast_to(Z, (len(xs), 1, len(zs))))
    # A flat wall of one thickness, not a rolled-over section: square edges are
    # far less work for a slicer than a bevel running along every strand, and
    # the pin heads read the same as flat discs.
    f = np.maximum(Dface, np.abs(rad - curve_r) - WALL_T / 2)

    gx, gy = np.meshgrid(xs, ys, indexing="ij")
    d_comb = distance_2d(comb, gx, gy)[:, :, None]
    # Taper the plate with how far back it sits from the band, so the teeth end
    # thin and springy where they go into the hair and keep their full section
    # where they carry the tiara. The underside stays flat on the bed.
    back = np.clip((curve_r - rad) / design.TOOTH_LEN, 0.0, 1.0)
    t_comb = COMB_T + (COMB_TIP - COMB_T) * back
    f = smin(f, np.maximum(d_comb, np.maximum(Z - t_comb, -Z)), JOIN_K)
    f = np.maximum(f, 1e-3 - Z).astype(np.float32)   # sit flat on the bed

    for sl in (np.s_[0, :, :], np.s_[-1, :, :], np.s_[:, 0, :], np.s_[:, -1, :],
               np.s_[:, :, 0], np.s_[:, :, -1]):
        f[sl] = np.abs(f[sl]) + 1.0
    f[np.abs(f) < 1e-3] = -1e-3
    return f, (xs[0], ys[0], zs[0]), voxel, face, comb


def unsupported(field, voxel):
    """Area per layer that starts with nothing under it anywhere in its island.

    Material anchored at either end of its own layer is a bridge, which prints;
    a component with no support at all under any of it is what needs support.
    """
    occ = field < 0.0
    out = np.zeros(occ.shape[2])
    for k in range(1, occ.shape[2]):
        layer = occ[:, :, k]
        if not layer.any():
            continue
        below = occ[:, :, k - 1]
        prop = below.copy()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                prop |= np.roll(np.roll(below, dx, axis=0), dy, axis=1)
        lab = label(layer, connectivity=2)
        held = np.unique(lab[layer & prop])
        floating = layer & ~np.isin(lab, held[held > 0])
        out[k] = floating.sum() * voxel * voxel
    return out


def mesh_from(field, origin, voxel, decimate=None):
    verts, faces, _, _ = marching_cubes(field, level=0.0, spacing=(voxel,) * 3)
    verts += np.asarray(origin, dtype=verts.dtype)
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
        # Decimation can weld two surfaces that pass close together -- here the
        # wall meeting the comb spine at the bed -- leaving non-manifold pinch
        # edges. Keep the reduction only if the result is still a clean solid.
        d = m.simplify_quadric_decimation(face_count=decimate)
        d.merge_vertices()
        if d.is_watertight and d.is_winding_consistent:
            print(f"  decimated to {len(d.faces):,} faces")
            m = d
        else:
            print(f"  decimation to {decimate:,} pinched the mesh; keeping "
                  f"{len(m.faces):,} faces")
    return m


def report(m, face, comb, per_layer, voxel, z0):
    lo, hi = m.bounds
    print(f"  size      {hi[0]-lo[0]:.1f} W x {hi[1]-lo[1]:.1f} D x {hi[2]-lo[2]:.1f} H mm")
    print(f"  triangles {len(m.faces):,}   bodies {m.body_count}")
    print(f"  volume    {m.volume/1000:.1f} cm^3  (~{m.volume/1000*1.24:.0f} g of PLA solid)")
    print(f"  watertight {m.is_watertight}   winding-consistent {m.is_winding_consistent}")

    opened = face.buffer(-0.7, quad_segs=32).buffer(0.7, quad_segs=32)
    thin = face.area - face.intersection(opened).area
    print(f"  drawing   {len(parts(face))} piece(s); {thin:.2f} mm2 of the face in walls "
          f"under 1.4 mm")

    foot = m.vertices[m.vertices[:, 2] < lo[2] + 0.4]
    com = m.center_mass
    inside = (foot[:, 0].min() < com[0] < foot[:, 0].max()
              and foot[:, 1].min() < com[1] < foot[:, 1].max())
    print(f"  footprint {foot[:,0].max()-foot[:,0].min():.0f} x "
          f"{foot[:,1].max()-foot[:,1].min():.0f} mm, centre of mass over it: {inside}")
    print(f"  comb      {COMB_T:.1f} mm thick at the band, tapering to {COMB_TIP:.1f} mm "
          f"at the tips over {design.TOOTH_LEN:.0f} mm")
    print(f"  face      flat wall, {WALL_T:.1f} mm thick throughout")

    z = z0 + voxel * np.arange(len(per_layer))
    above = per_layer[z > 0.5]
    zz = z[z > 0.5]
    total = above.sum()
    worst = float(above.max()) if len(above) else 0.0
    where = zz[int(np.argmax(above))] if len(above) else 0.0
    print(f"  islands   {total:.2f} mm2 starts with nothing under it (bridges excluded); "
          f"worst layer {worst:.2f} mm2 at z = {where:.0f} mm")
    return (m.is_watertight and m.is_winding_consistent and m.body_count == 1
            and len(parts(face)) == 1 and thin < 1.0 and inside and total < 5.0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--curve", type=float, default=CURVE_R, help="head radius, mm")
    ap.add_argument("--scale", type=float, default=1.0, help="scale the face drawing")
    ap.add_argument("--voxel", type=float, default=0.25)
    ap.add_argument("--decimate", type=int, default=140000)
    ap.add_argument("--out", default="tiara_comb.stl")
    a = ap.parse_args()

    field, origin, voxel, face, comb = build(a.voxel, a.curve, a.scale)
    per_layer = unsupported(field, voxel)
    m = mesh_from(field, origin, voxel, a.decimate or None)
    ok = report(m, face, comb, per_layer, voxel, origin[2])
    m.export(a.out)
    print(f"  wrote {a.out}")
    raise SystemExit(0 if ok else 1)
