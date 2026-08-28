"""Software-render an STL to PNG turntable views (numpy z-buffer, no GPU).

    python3 render.py model.stl preview.png --views 4
"""

import argparse

import numpy as np
import trimesh
from PIL import Image


def look_at(azim_deg, elev_deg):
    """World -> camera rotation; camera looks down -Z_cam, +Y_cam is up."""
    a, e = np.radians(azim_deg), np.radians(elev_deg)
    fwd = np.array([np.sin(a) * np.cos(e), np.cos(a) * np.cos(e), np.sin(e)])
    up = np.array([0.0, 0.0, 1.0])
    right = np.cross(fwd, up)
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return np.stack([right, up, -fwd])          # rows = camera axes


def render(mesh, azim, elev, w=560, h=760, margin=1.06):
    R = look_at(azim, elev)
    V = mesh.vertices @ R.T
    N = mesh.vertex_normals @ R.T

    lo, hi = V.min(0), V.max(0)
    ctr = (lo + hi) / 2
    scale = min(w / ((hi[0] - lo[0]) * margin), h / ((hi[1] - lo[1]) * margin))
    px = (V[:, 0] - ctr[0]) * scale + w / 2
    py = h / 2 - (V[:, 1] - ctr[1]) * scale

    F = mesh.faces
    x, y, z = px[F], py[F], V[:, 2][F]
    area = (x[:, 1] - x[:, 0]) * (y[:, 2] - y[:, 0]) - (x[:, 2] - x[:, 0]) * (y[:, 1] - y[:, 0])
    keep = area < -1e-9                          # front facing after the y-flip
    x, y, z, area = x[keep], y[keep], z[keep], area[keep]
    n = N[F][keep]

    zbuf = np.full((h, w), -np.inf, dtype=np.float32)
    nbuf = np.zeros((h, w, 3), dtype=np.float32)

    x0 = np.clip(np.floor(x.min(1)).astype(int), 0, w - 1)
    x1 = np.clip(np.ceil(x.max(1)).astype(int) + 1, 0, w)
    y0 = np.clip(np.floor(y.min(1)).astype(int), 0, h - 1)
    y1 = np.clip(np.ceil(y.max(1)).astype(int) + 1, 0, h)

    for t in range(len(x)):
        if x1[t] <= x0[t] or y1[t] <= y0[t]:
            continue
        gx = np.arange(x0[t], x1[t]) + 0.5
        gy = np.arange(y0[t], y1[t]) + 0.5
        gx, gy = gx[None, :], gy[:, None]
        ax, ay = x[t], y[t]
        w0 = ((ax[1] - ax[0]) * (gy - ay[0]) - (gx - ax[0]) * (ay[1] - ay[0])) / area[t]
        w1 = ((gx - ax[0]) * (ay[2] - ay[0]) - (ax[2] - ax[0]) * (gy - ay[0])) / area[t]
        w2 = 1.0 - w0 - w1
        m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not m.any():
            continue
        zz = w2 * z[t, 0] + w1 * z[t, 1] + w0 * z[t, 2]
        sub = zbuf[y0[t]:y1[t], x0[t]:x1[t]]
        m &= zz > sub
        if not m.any():
            continue
        sub[m] = zz[m]
        nn = (w2[..., None] * n[t, 0] + w1[..., None] * n[t, 1] + w0[..., None] * n[t, 2])
        nbuf[y0[t]:y1[t], x0[t]:x1[t]][m] = nn[m]

    hit = np.isfinite(zbuf)
    nb = nbuf / np.maximum(np.linalg.norm(nbuf, axis=-1, keepdims=True), 1e-9)

    key = np.array([-0.42, 0.55, 0.72]);  key /= np.linalg.norm(key)
    fill = np.array([0.65, 0.15, 0.35]);  fill /= np.linalg.norm(fill)
    lam = np.clip(nb @ key, 0, 1) * 0.78 + np.clip(nb @ fill, 0, 1) * 0.26
    rim = np.clip(1.0 - nb[..., 2], 0, 1) ** 3 * 0.5
    shade = np.clip(0.16 + lam + rim, 0, 1.15)

    base = np.array([0.80, 0.62, 0.42])                       # ginger highland coat
    img = np.clip(shade[..., None] * base, 0, 1)
    grad = np.linspace(0.99, 0.86, h)[:, None, None] * np.array([0.96, 0.95, 0.94])
    out = np.where(hit[..., None], img, grad)
    return (out * 255).astype(np.uint8)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stl")
    ap.add_argument("out")
    ap.add_argument("--angles", default="0,-35,-90,180")
    ap.add_argument("--elev", type=float, default=8.0)
    ap.add_argument("--width", type=int, default=560)
    ap.add_argument("--flat", action="store_true",
                    help="face normals instead of smoothed ones, for faceted parts")
    a = ap.parse_args()

    mesh = trimesh.load(a.stl)
    if a.flat:
        mesh.unmerge_vertices()
    tiles = [render(mesh, float(t), a.elev, w=a.width) for t in a.angles.split(",")]
    Image.fromarray(np.concatenate(tiles, axis=1)).save(a.out)
    print(f"wrote {a.out}  ({len(tiles)} views)")
