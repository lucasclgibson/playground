#!/usr/bin/env python3
"""
Render preview.png from the exported STL - four views, no GPU required.

Plain painter's-algorithm rasteriser: project the triangles orthographically,
drop the back faces, sort by depth, shade by normal. Enough to eyeball the
part and to spot a geometry change in a diff.
"""

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402
from matplotlib.collections import PolyCollection                 # noqa: E402
import trimesh                                                    # noqa: E402

from verify import params                                         # noqa: E402

STL = "under-desk-minipc-mount.stl"
OUT = "preview.png"
LIGHT = np.array([0.35, -0.75, 0.55])
BODY, PC, DESK = "#6d7f96", "#22262b", "#c9a227"


def basis(view):
    d = np.asarray(view, float)
    d /= np.linalg.norm(d)
    up = np.array([0.0, 0.0, 1.0])
    if abs(d @ up) > 0.99:
        up = np.array([0.0, 1.0, 0.0])
    right = np.cross(d, up)
    right /= np.linalg.norm(right)
    return d, right, np.cross(right, d)


def render(ax, items, view, title):
    d, right, up = basis(view)
    light = LIGHT / np.linalg.norm(LIGHT)
    polys, colours, depths = [], [], []
    for mesh, base in items:
        tri = mesh.triangles[mesh.face_normals @ d < 0]
        n = mesh.face_normals[mesh.face_normals @ d < 0]
        polys += list(np.stack([tri @ right, tri @ up], axis=-1))
        shade = 0.35 + 0.65 * np.clip(n @ light, 0.0, 1.0)
        colours.append(np.clip(np.array(matplotlib.colors.to_rgb(base))[None, :]
                               * shade[:, None], 0.0, 1.0))
        depths.append(tri.mean(axis=1) @ d)
    colours = np.vstack(colours)
    order = np.argsort(-np.concatenate(depths))
    ax.add_collection(PolyCollection([polys[i] for i in order],
                                     facecolors=colours[order], edgecolors="none"))
    pts = np.vstack(polys)
    ax.set_xlim(pts[:, 0].min() - 6, pts[:, 0].max() + 6)
    ax.set_ylim(pts[:, 1].min() - 6, pts[:, 1].max() + 6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=10, color="#333")


def main():
    p = params("under_desk_minipc_mount.scad")
    z_floor = -(p["TOP_T"] + p["PC_H"] + p["GAP_TOP"])
    mount = trimesh.load(STL)
    pc = trimesh.creation.box(
        extents=(p["PC_W"], p["PC_D"], p["PC_H"]),
        transform=trimesh.transformations.translation_matrix(
            (0, p["BACK_T"] + p["PC_D"] / 2, z_floor + p["PC_H"] / 2)))
    desk = trimesh.creation.box(
        extents=(230, 200, 18),
        transform=trimesh.transformations.translation_matrix((0, 60, 9)))

    fig, axes = plt.subplots(2, 2, figsize=(13, 10), dpi=120)
    render(axes[0, 0], [(mount, BODY)], (-0.75, 0.85, -0.6),
           "front / right / above - empty")
    render(axes[0, 1], [(mount, BODY), (pc, PC)], (-0.75, 0.85, -0.6),
           "mini PC seated")
    render(axes[1, 0], [(mount, BODY)], (-0.55, 0.8, 0.55),
           "from below - open bottom, shelves and nubs")
    render(axes[1, 1], [(desk, DESK), (mount, BODY), (pc, PC)], (-0.6, 0.9, -0.15),
           "screwed under a desk top")
    fig.tight_layout()
    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
