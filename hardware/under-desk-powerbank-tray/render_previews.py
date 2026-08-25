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
BODY, PC, DESK, BAND = "#6d7f96", "#22262b", "#c9a227", "#b4472e"


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
    x_cav = p["BANK_W"] / 2 + p["GAP_SIDE"]
    out_d = p["BACK_T"] + p["BANK_D"] + p["GAP_BACK"] + p["FRONT_LIP"]

    mount = trimesh.load(STL)
    pc = trimesh.creation.box(
        extents=(p["BANK_W"], p["BANK_D"], p["BANK_H"]),
        transform=trimesh.transformations.translation_matrix(
            (0, p["BACK_T"] + p["BANK_D"] / 2, z_floor + p["BANK_H"] / 2)))
    # The band on the brick's side, standing proud of the wall.
    side = 1.0 if p["BAND_SIDE"] > 0 else -1.0
    out_w = p["BANK_W"] + 2 * p["GAP_SIDE"] + 2 * p["WALL"]
    band_z = z_floor + p["BANK_H"] / 2 + p["BAND_OFF"]
    bank_front = p["BACK_T"] + p["BANK_D"] + p["GAP_BACK"]
    band_x0, band_x1 = side * p["BANK_W"] / 2, side * (out_w / 2 + 1.5)
    band = trimesh.creation.box(
        extents=(abs(band_x1 - band_x0), p["BAND_DEPTH"], p["BAND_W"]),
        transform=trimesh.transformations.translation_matrix(
            ((band_x0 + band_x1) / 2, bank_front - p["BAND_DEPTH"] / 2, band_z)))

    desk = trimesh.creation.box(
        extents=(230, 230, 18),
        transform=trimesh.transformations.translation_matrix((0, 70, 9)))

    fig, axes = plt.subplots(2, 3, figsize=(19, 10), dpi=120)
    render(axes[0, 0], [(mount, BODY)], (-1.0, 0.15, -0.25),
           "banded wall - slot open at the mouth")
    render(axes[0, 1], [(mount, BODY), (pc, PC), (band, BAND)], (-0.75, 0.85, -0.6),
           "power bank seated, band through the slot")
    render(axes[0, 2], [(mount, BODY)], (-0.55, 0.8, 0.55),
           "from below - open bottom and shelves")
    render(axes[1, 0], [(desk, DESK), (mount, BODY), (pc, PC), (band, BAND)],
           (-0.6, 0.9, -0.15), "screwed under a desk top")
    render(axes[1, 1], [(mount, BODY), (pc, PC)], (0.75, -0.85, -0.5),
           "from the back - closed off")

    # Section across the tray: what carries the bank.
    ax = axes[1, 2]
    y_sec = bank_front - p["BAND_DEPTH"] / 2          # through the band slot
    outline(ax, mount, [0, y_sec, 0], [0, 1, 0], (0, 2), "#334")
    ax.add_patch(plt.Rectangle((-p["BANK_W"] / 2, z_floor), p["BANK_W"], p["BANK_H"],
                               fill=False, ls="--", lw=1.2, color=BAND))
    ax.add_patch(plt.Rectangle((min(band_x0, band_x1), band_z - p["BAND_W"] / 2),
                               abs(band_x1 - band_x0), p["BAND_W"],
                               fill=False, ls="--", lw=1.2, color=BAND))
    ax.annotate("power bank", (0, z_floor + p["BANK_H"] / 2), color=BAND,
                fontsize=8, ha="center", va="center")
    ax.annotate("band", (band_x1 + side * 12, band_z), color=BAND,
                fontsize=8, ha="center", va="center")
    ax.axhline(0, ls="-", lw=1.0, color="#c9a227")
    ax.annotate("desk", (x_cav + 22, 1.5), fontsize=8, color="#666")
    ax.set_xlim(-p["BANK_W"] / 2 - 30, p["BANK_W"] / 2 + 30)
    ax.set_ylim(-p["TOP_T"] - p["BANK_H"] - p["GAP_TOP"] - p["SHELF_T"] - 6, 8)
    ax.set_aspect("equal")
    ax.set_title("section through the band slot", fontsize=10, color="#333")
    ax.tick_params(labelsize=7)

    fig.tight_layout()
    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
