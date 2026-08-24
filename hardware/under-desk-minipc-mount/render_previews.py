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


def outline(ax, mesh, origin, normal, ij, colour, lw=1.4, label=None):
    """Plot a planar section straight from its 3D vertices - no frame guessing."""
    sec = mesh.section(plane_origin=origin, plane_normal=normal)
    if sec is None:
        return
    for n, ent in enumerate(sec.entities):
        pts = sec.vertices[ent.points]
        ax.plot(pts[:, ij[0]], pts[:, ij[1]], "-", color=colour, lw=lw,
                label=label if n == 0 else None)


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

    latch_z = -(p["TOP_T"] + (p["PC_H"] + p["GAP_TOP"]) / 2)
    x_cav = p["PC_W"] / 2 + p["GAP_SIDE"]
    x_out = x_cav + p["WALL"]
    out_d = p["BACK_T"] + p["PC_D"] + p["GAP_BACK"] + p["FRONT_LIP"]
    pc_front = p["BACK_T"] + p["PC_D"]

    fig, axes = plt.subplots(2, 3, figsize=(19, 10), dpi=120)
    render(axes[0, 0], [(mount, BODY)], (-0.75, 0.85, -0.6),
           "front / right / above - empty")
    render(axes[0, 1], [(mount, BODY), (pc, PC)], (-0.75, 0.85, -0.6),
           "mini PC seated")
    render(axes[0, 2], [(mount, BODY)], (-0.55, 0.8, 0.55),
           "from below - open bottom, shelves and nubs")
    render(axes[1, 0], [(desk, DESK), (mount, BODY), (pc, PC)], (-0.6, 0.9, -0.15),
           "screwed under a desk top")

    # Plan cut through the latches: the barb sits behind the PC's front face.
    ax = axes[1, 1]
    outline(ax, mount, [0, 0, latch_z], [0, 0, 1], (1, 0), "#334")
    ax.add_patch(plt.Rectangle((p["BACK_T"], -p["PC_W"] / 2), p["PC_D"], p["PC_W"],
                               fill=False, ls="--", lw=1.2, color="#b4472e"))
    ax.annotate("PC, seated", (pc_front - 4, p["PC_W"] / 2 - 9), color="#b4472e",
                fontsize=8, ha="right")
    ax.annotate("barb", (out_d - 6, x_cav + 7), color="#334", fontsize=8,
                ha="center", arrowprops=dict(arrowstyle="->", color="#334", lw=1),
                xytext=(out_d - 6, x_cav + 14))
    ax.set_xlim(out_d - 55, out_d + 6)
    ax.set_ylim(x_out + 6, 40)
    ax.set_aspect("equal")
    ax.set_title("plan cut at latch height - right side", fontsize=10, color="#333")
    ax.tick_params(labelsize=7)

    # Elevation through the wall: the beam, the slots that free it, the barb.
    ax = axes[1, 2]
    outline(ax, mount, [(x_cav + x_out) / 2, 0, 0], [1, 0, 0], (1, 2), "#334",
            label="side wall")
    outline(ax, mount, [x_cav - p["LATCH_BARB"] / 2, 0, 0], [1, 0, 0], (1, 2),
            "#b4472e", lw=1.1, label="barb")
    ax.axvline(pc_front, ls="--", lw=1.0, color="#888")
    ax.annotate("PC front face", (pc_front - 2, latch_z + 18), rotation=90,
                fontsize=8, color="#666", ha="right")
    ax.set_xlim(out_d - 55, out_d + 6)
    ax.set_ylim(latch_z - 22, latch_z + 22)
    ax.set_aspect("equal")
    ax.legend(fontsize=8, loc="lower left", frameon=False)
    ax.set_title("wall elevation - beam, slots and barb", fontsize=10, color="#333")
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
