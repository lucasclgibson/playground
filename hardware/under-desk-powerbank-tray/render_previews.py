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

STL = "under-desk-powerbank-tray.stl"
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
    p = params("under_desk_powerbank_tray.scad")
    z_floor = -(p["TOP_T"] + p["BANK_H"] + p["GAP_TOP"])
    mount = trimesh.load(STL)
    pc = trimesh.creation.box(
        extents=(p["BANK_W"], p["BANK_D"], p["BANK_H"]),
        transform=trimesh.transformations.translation_matrix(
            (0, p["BACK_T"] + p["BANK_D"] / 2, z_floor + p["BANK_H"] / 2)))
    desk = trimesh.creation.box(
        extents=(230, 200, 18),
        transform=trimesh.transformations.translation_matrix((0, 60, 9)))

    z_floor = -(p["TOP_T"] + p["BANK_H"] + p["GAP_TOP"])
    x_cav = p["BANK_W"] / 2 + p["GAP_SIDE"]
    out_d = p["BACK_T"] + p["BANK_D"] + p["GAP_BACK"] + p["FRONT_LIP"]
    pc_front = p["BACK_T"] + p["BANK_D"]
    r_demo = 5.0                       # a power bank is a fairly square brick

    fig, axes = plt.subplots(2, 3, figsize=(19, 10), dpi=120)
    render(axes[0, 0], [(mount, BODY)], (-0.75, 0.85, -0.6),
           "front / right / above - empty")
    render(axes[0, 1], [(mount, BODY), (pc, PC)], (-0.75, 0.85, -0.6),
           "power bank seated")
    render(axes[0, 2], [(mount, BODY)], (-0.55, 0.8, 0.55),
           "from below - shelves and the two sprung arms")
    render(axes[1, 0], [(desk, DESK), (mount, BODY), (pc, PC)], (-0.6, 0.9, -0.15),
           "screwed under a desk top")

    # Plan: where the barbs land against a machine with rounded corners.
    ax = axes[1, 1]
    outline(ax, mount, [0, 0, z_floor - p["ARM_T"] / 2], [0, 0, 1], (1, 0),
            "#9aa7b8", lw=1.0, label="sprung arms")
    outline(ax, mount, [0, 0, z_floor + p["BARB_H"] / 2], [0, 0, 1], (1, 0),
            "#334", label="barbs and walls")
    corner = plt.matplotlib.patches.FancyBboxPatch(
        (p["BACK_T"] + r_demo, -p["BANK_W"] / 2 + r_demo),
        p["BANK_D"] - 2 * r_demo, p["BANK_W"] - 2 * r_demo,
        boxstyle=f"round,pad={r_demo}", fill=False, lw=1.6, color="#b4472e")
    ax.add_patch(corner)
    ax.annotate(f"power bank, {r_demo:.0f} mm corners",
                (pc_front - 40, -p["BANK_W"] / 2 + 4),
                color="#b4472e", fontsize=8, ha="center", va="bottom")
    ax.annotate(f"barbs clear a\nradius up to {p['MAX_CORNER_R']:.0f} mm",
                (pc_front - 8, p["BANK_W"] / 2 - 18),
                color="#b4472e", fontsize=7.5, ha="right", va="center")
    ax.annotate("barbs", (pc_front + 4, 0), color="#334", fontsize=8, ha="left",
                va="center")
    ax.set_xlim(out_d - 78, out_d + 4)
    ax.set_ylim(-p["BANK_W"] / 2 - 10, p["BANK_W"] / 2 + 10)
    ax.set_aspect("equal")
    ax.legend(fontsize=8, loc="center left", frameon=False)
    ax.set_title("plan - barbs reach the flat middle of the face", fontsize=10,
                 color="#333")
    ax.tick_params(labelsize=7)

    # Elevation through one arm: the barb profile and the air it ducks into.
    ax = axes[1, 2]
    outline(ax, mount, [p["ARM_X"], 0, 0], [1, 0, 0], (1, 2), "#334")
    ax.axvline(pc_front, ls="--", lw=1.0, color="#b4472e")
    ax.annotate("PC front face", (pc_front - 2, z_floor + 14), rotation=90,
                fontsize=8, color="#b4472e", ha="right")
    ax.annotate(f"ducks {p['BARB_H']:.1f} mm", (out_d - 8, z_floor - 10),
                fontsize=8, color="#666", ha="center")
    ax.arrow(out_d - 6, z_floor - p["ARM_T"] - 1, 0, -p["BARB_H"] + 1,
             head_width=1.5, head_length=1.0, fc="#666", ec="#666", lw=0.8)
    ax.set_xlim(out_d - 34, out_d + 4)
    ax.set_ylim(z_floor - 12, z_floor + 10)
    ax.set_aspect("equal")
    ax.set_title("elevation through one arm", fontsize=10, color="#333")
    ax.tick_params(labelsize=7)

    fig.tight_layout()
    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
