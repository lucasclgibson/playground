"""Mesh the highland cow SDF and write a print-ready STL.

    python3 generate.py --voxel 0.35 --out highland_cow_110mm.stl
"""

import argparse
import time

import numpy as np
import trimesh
from skimage.measure import marching_cubes

import cow


def sample(voxel, base=False, verbose=True):
    (x0, x1), (y0, y1), (z0, z1) = cow.BOUNDS
    nx = int(np.ceil((x1 - x0) / voxel)) + 1
    ny = int(np.ceil((y1 - y0) / voxel)) + 1
    nz = int(np.ceil((z1 - z0) / voxel)) + 1
    xs = x0 + voxel * np.arange(nx, dtype=np.float32)
    ys = y0 + voxel * np.arange(ny, dtype=np.float32)
    zs = z0 + voxel * np.arange(nz, dtype=np.float32)

    groups = cow.build(base=base)
    vol = np.empty((nx, ny, nz), dtype=np.float32)
    if verbose:
        parts = sum(len(g.items) for g in groups)
        print(f"grid {nx}x{ny}x{nz} = {nx*ny*nz/1e6:.1f}M samples @ {voxel} mm, "
              f"{parts} primitives")

    slab = max(1, int(round(8.0 / voxel)))
    t0 = time.time()
    for k in range(0, nz, slab):
        k1 = min(k + slab, nz)
        X = xs[:, None, None]
        Y = ys[None, :, None]
        Z = zs[None, None, k:k1]
        vol[:, :, k:k1] = cow.field(X, Y, Z, groups, float(zs[k]), float(zs[k1 - 1]),
                                    floor=-cow.PLINTH_MM if base else 0.0)
        if verbose and (k // slab) % 8 == 0:
            print(f"  z {zs[k]:7.1f} mm  ({100*k/nz:4.0f}%)", flush=True)
    if verbose:
        print(f"  field sampled in {time.time()-t0:.1f}s")

    # Guarantee a closed surface: force the volume border to read as "outside".
    for sl in (np.s_[0, :, :], np.s_[-1, :, :], np.s_[:, 0, :], np.s_[:, -1, :],
               np.s_[:, :, 0], np.s_[:, :, -1]):
        vol[sl] = np.abs(vol[sl]) + 1.0
    return vol, (x0, y0, z0), voxel


def mesh_from(vol, origin, voxel):
    verts, faces, _, _ = marching_cubes(vol, level=0.0, spacing=(voxel,) * 3)
    verts += np.asarray(origin, dtype=verts.dtype)
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    if m.volume < 0:                       # marching-cubes winding points inward
        m.invert()

    parts = m.split(only_watertight=False)
    if len(parts) > 1:
        parts = sorted(parts, key=lambda p: -abs(p.volume))
        for p in parts[1:]:
            lo, hi = p.bounds
            print(f"  dropped stray shell: {len(p.faces)} faces, "
                  f"{abs(p.volume):.2f} mm^3 at ({lo[0]:.0f},{lo[1]:.0f},{lo[2]:.0f})"
                  f"-({hi[0]:.0f},{hi[1]:.0f},{hi[2]:.0f})")
        m = parts[0]
    m.merge_vertices()
    m.update_faces(m.nondegenerate_faces())
    m.remove_unreferenced_vertices()
    return m


def finish(m, height, decimate=None, base=False):
    if decimate and len(m.faces) > decimate:
        try:
            m = m.simplify_quadric_decimation(face_count=decimate)
            print(f"  decimated to {len(m.faces)} faces")
        except Exception as exc:                              # optional dependency
            print(f"  (decimation unavailable: {exc})")
    lo, hi = m.bounds
    m.apply_scale(height / (hi[2] - lo[2] - (cow.PLINTH_MM if base else 0.0)))
    lo, hi = m.bounds
    m.apply_translation([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    return m


def report(m):
    lo, hi = m.bounds
    size = hi - lo
    print(f"  size      {size[0]:.1f} W x {size[1]:.1f} D x {size[2]:.1f} H mm")
    print(f"  triangles {len(m.faces):,}   vertices {len(m.vertices):,}")
    shell = m.area * 1.2                                  # 3 perimeters at 0.4 mm
    filament = (shell + 0.15 * max(m.volume - shell, 0.0)) / 1000 * 1.24
    print(f"  volume    {m.volume/1000:.1f} cm^3 solid, surface {m.area/100:.0f} cm^2")
    print(f"  filament  ~{filament:.0f} g of PLA (3 walls, 15% infill)")
    print(f"  watertight {m.is_watertight}   winding-consistent {m.is_winding_consistent}"
          f"   bodies {m.body_count}   euler {m.euler_number}")

    com = m.center_mass
    foot = m.vertices[m.vertices[:, 2] < lo[2] + 0.6]
    inside = (foot[:, 0].min() < com[0] < foot[:, 0].max()
              and foot[:, 1].min() < com[1] < foot[:, 1].max())
    print(f"  centre of mass ({com[0]:+.1f}, {com[1]:+.1f}) vs footprint "
          f"x[{foot[:,0].min():.0f},{foot[:,0].max():.0f}] y[{foot[:,1].min():.0f},"
          f"{foot[:,1].max():.0f}] -> {'stable' if inside else 'TIPS OVER'}")
    print(f"  contact patch {len(foot)} verts on the bed")
    return m.is_watertight and m.is_winding_consistent and m.body_count == 1 and inside


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--voxel", type=float, default=0.35)
    ap.add_argument("--out", default="highland_cow_110mm.stl")
    ap.add_argument("--decimate", type=int, default=0)
    ap.add_argument("--height", type=float, default=cow.TARGET_HEIGHT_MM)
    ap.add_argument("--base", action="store_true",
                    help="add a 3 mm plinth under the hooves")
    a = ap.parse_args()

    vol, origin, voxel = sample(a.voxel, base=a.base)
    m = mesh_from(vol, origin, voxel)
    m = finish(m, a.height, a.decimate or None, base=a.base)
    ok = report(m)
    m.export(a.out)
    print(f"  wrote {a.out}")
    raise SystemExit(0 if ok else 1)
