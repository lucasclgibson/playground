"""Build the badge as a standing desk piece: a solid, rounded 3D form on a plinth.

    python3 stand.py --width 110 --out ukpl_badge_stand.stl

The mark is inflated into a rounded prism (a 2D distance field extruded and
offset, so every edge is a bullnose and the roof bar becomes a rounded bar),
bridged across its shadow gap by a recessed web, and blended into a plinth.
The field is sampled on a grid and meshed with marching cubes, which is what
lets the plinth join the mark with a proper fillet instead of a seam.
"""

import argparse
import time

import numpy as np
import shapely
import trimesh
from shapely import affinity
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union
from skimage.measure import marching_cubes

import shapes


# ----------------------------------------------------------------- 2D field
def boundary_segments(poly):
    """Every edge of every ring, as (start, end) arrays."""
    a, b = [], []
    for p in (poly.geoms if isinstance(poly, MultiPolygon) else [poly]):
        for ring in [p.exterior, *p.interiors]:
            c = np.asarray(ring.coords)
            a.append(c[:-1])
            b.append(c[1:])
    return np.vstack(a), np.vstack(b)


def signed_distance_2d(poly, xs, zs, chunk=20000):
    """Exact signed distance to `poly` on the xs x zs grid (negative inside)."""
    A, B = boundary_segments(poly)
    AB = B - A
    denom = np.einsum("ij,ij->i", AB, AB)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    pts = np.column_stack([X.ravel(), Z.ravel()])

    out = np.empty(len(pts), dtype=np.float32)
    for i in range(0, len(pts), chunk):
        p = pts[i:i + chunk, None, :]
        t = np.clip(np.einsum("psj,sj->ps", p - A[None], AB) / denom, 0.0, 1.0)
        proj = A[None] + t[..., None] * AB[None]
        out[i:i + chunk] = np.sqrt(((p - proj) ** 2).sum(-1)).min(axis=1)
    inside = shapely.contains_xy(poly, pts[:, 0], pts[:, 1])
    out[inside] *= -1.0
    return out.reshape(X.shape)


# ----------------------------------------------------------------- 3D field
def dome_profile(d2, dome, falloff=9.0):
    """Extra half-depth toward the middle of a shape: 0 at the rim, `dome` deep in.

    Keeps the rim crisp while letting broad areas swell, so the faces read as
    sculpted rather than sliced off a extrusion.
    """
    if dome <= 0:
        return 0.0
    return dome * (1.0 - np.exp(np.minimum(d2, 0.0) / falloff))


def rounded_prism(d2, Y, half_depth, r):
    """Extrude a 2D field to `2*half_depth` deep and round every edge by `r`.

    Erode by r, extrude, then offset back out by r: the exact distance field of
    a prism with a bullnose all the way round, holes included.
    """
    a = d2 + r
    b = np.abs(Y) - (half_depth - r)
    return (np.minimum(np.maximum(a, b), 0.0)
            + np.sqrt(np.maximum(a, 0.0) ** 2 + np.maximum(b, 0.0) ** 2) - r)


def round_box(X, Y, Z, c, b, r):
    qx = np.abs(X - c[0]) - b[0]
    qy = np.abs(Y - c[1]) - b[1]
    qz = np.abs(Z - c[2]) - b[2]
    return (np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2
                    + np.maximum(qz, 0) ** 2)
            + np.minimum(np.maximum(np.maximum(qx, qy), qz), 0.0) - r)


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b + (a - b) * h - k * h * (1.0 - h)


# ------------------------------------------------------------------- layout
def place(svg, width):
    """Mark in millimetres: y-up, centred on x, sitting on z = 0."""
    poly, _ = shapes.load(svg)
    x0, _, x1, _ = poly.bounds
    s = width / (x1 - x0)
    poly = affinity.scale(poly, xfact=s, yfact=-s, origin=(0, 0))
    x0, y0, x1, y1 = poly.bounds
    return affinity.translate(poly.simplify(0.03).buffer(0), -(x0 + x1) / 2, -y0)


def parts(poly):
    return list(poly.geoms) if isinstance(poly, MultiPolygon) else [poly]


def build(svg="badge.svg", width=110.0, depth=15.0, edge=3.2, dome=1.5, web_depth=3.5,
          web_reach=6.0, base=(76.0, 36.0, 12.0), embed=10.0, fillet=4.0,
          voxel=0.35, web_flush=True, verbose=True):
    mark = place(svg, width)
    web = shapes.bridge_web(mark, web_reach)
    lift = base[2] - embed if base else 0.0     # where the mark's foot sits

    half = depth / 2
    x0, _, x1, _ = mark.bounds
    wide = max(x1, base[0] / 2 if base else 0.0)
    deep = max(half, base[1] / 2 if base else 0.0)
    bx = (-wide - 3, wide + 3)
    by = (-deep - 3, deep + 3)
    bz = (-5.0, mark.bounds[3] + lift + 3)

    n = [int(np.ceil((hi - lo) / voxel)) + 1 for lo, hi in (bx, by, bz)]
    xs = bx[0] + voxel * np.arange(n[0])
    ys = by[0] + voxel * np.arange(n[1])
    zs = bz[0] + voxel * np.arange(n[2])
    if verbose:
        print(f"  grid {n[0]}x{n[1]}x{n[2]} = {np.prod(n)/1e6:.1f}M samples @ {voxel} mm")

    t0 = time.time()
    d_mark = signed_distance_2d(mark, xs, zs - lift)[:, None, :]
    d_web = (signed_distance_2d(web, xs, zs - lift)[:, None, :]
             if web is not None else None)
    if verbose:
        print(f"  2D distance fields in {time.time()-t0:.1f}s")

    Y = ys[None, :, None].astype(np.float32)
    Z = zs[None, None, :].astype(np.float32)
    X = xs[:, None, None].astype(np.float32)

    f = rounded_prism(d_mark, Y, half + dome_profile(d_mark, dome), edge)
    if d_web is not None:
        # Sit the web against the back face rather than mid-depth. It reads the
        # same from the front -- the gap becomes a deep blind slot -- and it
        # means the block can be printed lying on its back with nothing
        # overhanging, which a web floating mid-depth would not allow.
        back = -(half - web_depth / 2) if web_flush else 0.0
        f = smin(f, rounded_prism(d_web, Y - back, web_depth / 2, edge), 0.25)

    if base:
        drop = 4.0                              # plinth continues below the cut
        plinth = round_box(X, Y, Z, (0.0, 0.0, (base[2] - drop) / 2),
                           (base[0] / 2 - 3.0, base[1] / 2 - 3.0,
                            (base[2] + drop) / 2 - 3.0), 3.0)
        f = smin(f, plinth, fillet)
    f = np.maximum(f, 1e-3 - Z)                 # flat bottom, off the sample plane

    for sl in (np.s_[0, :, :], np.s_[-1, :, :], np.s_[:, 0, :], np.s_[:, -1, :],
               np.s_[:, :, 0], np.s_[:, :, -1]):
        f[sl] = np.abs(f[sl]) + 1.0

    # The prism's flat faces lie exactly on |y| = depth/2, and a grid plane can
    # land right on them. Samples there evaluate to zero give or take float
    # noise, so marching cubes sees a sheet of ties and mixed signs and emits
    # degenerate triangles and spurious tunnels. Push that whole band a micron
    # inside: far below print resolution, far above the noise.
    f = f.astype(np.float32)
    f[np.abs(f) < 1e-3] = -1e-3
    return f, (bx[0], by[0], bz[0]), voxel, mark, web


def unsupported_area(field, voxel):
    """Area that would start mid-air, layer by layer -- i.e. what needs support.

    A cell counts as unsupported when the layer below is empty in its whole
    3x3 neighbourhood, which is roughly the overhang a slicer can still anchor.
    """
    occ = field < 0.0
    below = occ[:, :, :-1]
    pad = np.zeros_like(below)
    for dx in (-1, 0, 1):                       # cheap 3x3 dilation of the layer below
        for dy in (-1, 0, 1):
            pad |= np.roll(np.roll(below, dx, axis=0), dy, axis=1)
    island = occ[:, :, 1:] & ~pad
    return island.sum(axis=(0, 1)) * voxel * voxel


# ------------------------------------------------------------------ meshing
def mesh_from(field, origin, voxel, decimate=None):
    verts, faces, _, _ = marching_cubes(field, level=0.0, spacing=(voxel,) * 3)
    verts += np.asarray(origin, dtype=verts.dtype)
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    if m.volume < 0:
        m.invert()

    pieces = m.split(only_watertight=False)
    if len(pieces) > 1:
        pieces = sorted(pieces, key=lambda p: -abs(p.volume))
        for p in pieces[1:]:
            lo, hi = p.bounds
            print(f"  dropped stray shell: {len(p.faces)} faces, {abs(p.volume):.2f} mm^3 "
                  f"at ({lo[0]:.0f},{lo[1]:.0f},{lo[2]:.0f})")
        m = pieces[0]
    m.merge_vertices()
    m.update_faces(m.nondegenerate_faces())
    m.remove_unreferenced_vertices()

    if decimate and len(m.faces) > decimate:
        try:
            m = m.simplify_quadric_decimation(face_count=decimate)
            m.merge_vertices()
            print(f"  decimated to {len(m.faces):,} faces")
        except Exception as exc:
            print(f"  (decimation unavailable: {exc})")
    return m


def report(mesh, per_layer=None, voxel=0.0, z0=0.0):
    lo, hi = mesh.bounds
    print(f"  size      {hi[0]-lo[0]:.1f} W x {hi[1]-lo[1]:.1f} D x {hi[2]-lo[2]:.1f} H mm")
    print(f"  triangles {len(mesh.faces):,}   bodies {mesh.body_count}")
    shell = mesh.area * 1.2
    est = (shell + 0.15 * max(mesh.volume - shell, 0.0)) / 1000 * 1.24
    print(f"  volume    {mesh.volume/1000:.1f} cm^3 solid  (~{est:.0f} g of PLA, "
          f"3 walls / 15% infill)")
    print(f"  watertight {mesh.is_watertight}   winding-consistent "
          f"{mesh.is_winding_consistent}   euler {mesh.euler_number}")

    com = mesh.center_mass
    foot = mesh.vertices[mesh.vertices[:, 2] < lo[2] + 0.6]
    fx, fy = foot[:, 0], foot[:, 1]
    margin = min(com[0] - fx.min(), fx.max() - com[0], com[1] - fy.min(), fy.max() - com[1])
    stable = margin > 0
    print(f"  footprint {fx.max()-fx.min():.0f} x {fy.max()-fy.min():.0f} mm; centre of "
          f"mass {margin:.0f} mm inside it, {com[2]:.0f} mm up -> "
          f"{'stands' if stable else 'TIPS OVER'}")
    print(f"  tips at   {np.degrees(np.arctan2(min(fx.max()-com[0], com[0]-fx.min(), fy.max()-com[1], com[1]-fy.min()), com[2])):.0f}"
          f" deg of lean")

    n, a = mesh.face_normals, mesh.area_faces
    steep = n[:, 2] < -np.cos(np.radians(45))
    print(f"  overhang  {100*a[steep].sum()/a.sum():.1f}% of the surface faces down "
          f"steeper than 45 deg (mostly the bullnose undersides, which self-support)")
    if per_layer is not None:
        z = z0 + voxel * (1 + np.arange(len(per_layer)))
        above = per_layer[z > 0.5]              # the first layer sits on the bed
        zz = z[z > 0.5]
        worst = int(np.argmax(above))
        print(f"  islands   {above.sum():.0f} mm2 of material starts mid-air above the "
              f"bed; worst single layer {above[worst]:.1f} mm2 at z = {zz[worst]:.0f} mm")
        heights = zz[above > 0.05]
        if len(heights):
            print(f"            found between z = {heights.min():.0f} and "
                  f"{heights.max():.0f} mm")
    return mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1 and stable


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--svg", default="badge.svg")
    ap.add_argument("--width", type=float, default=110.0, help="width of the mark, mm")
    ap.add_argument("--depth", type=float, default=15.0, help="how deep the mark is, mm")
    ap.add_argument("--edge", type=float, default=3.2,
                    help="edge radius; 0 keeps the extrusion square")
    ap.add_argument("--dome", type=float, default=1.5,
                    help="extra swell toward the middle of the faces, mm")
    ap.add_argument("--web", type=float, default=3.5, help="bridging web depth, mm")
    ap.add_argument("--web-centred", action="store_true",
                    help="put the web mid-depth instead of against the back")
    ap.add_argument("--web-reach", type=float, default=6.0)
    ap.add_argument("--base", default="76,36,12",
                    help="plinth W,D,H in mm, or 'none' for the mark on its own")
    ap.add_argument("--embed", type=float, default=10.0, help="mark's foot into plinth, mm")
    ap.add_argument("--fillet", type=float, default=4.0)
    ap.add_argument("--voxel", type=float, default=0.28,
                    help="sampling grid; finer is slower and heavier")
    ap.add_argument("--decimate", type=int, default=80000,
                    help="target triangle count; 0 keeps the full mesh")
    ap.add_argument("--out", default="ukpl_badge_stand_110mm.stl")
    a = ap.parse_args()

    base = None if a.base.lower() in ("none", "") else tuple(
        float(v) for v in a.base.split(","))
    field, origin, voxel, mark, web = build(a.svg, a.width, a.depth, a.edge, a.dome,
                                            a.web, a.web_reach, base, a.embed,
                                            a.fillet, a.voxel, not a.web_centred)
    per_layer = unsupported_area(field, voxel)
    mesh = mesh_from(field, origin, voxel, a.decimate or None)
    ok = report(mesh, per_layer, voxel, origin[2])
    mesh.export(a.out)
    print(f"  wrote {a.out}")
    raise SystemExit(0 if ok else 1)
