#!/usr/bin/env python3
"""Render preview.png from the exported rails - four views, no GPU required."""

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402
from matplotlib.collections import PolyCollection                 # noqa: E402
import trimesh                                                    # noqa: E402

from verify import params                                         # noqa: E402

OUT = "preview.png"
LIGHT = np.array([0.35, -0.75, 0.55])
BODY, KB, DESK = "#6d7f96", "#22262b", "#c9a227"
DEMO_W = 300.0                      # illustrative keyboard width


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
        keep = mesh.face_normals @ d < 0
        tri, n = mesh.triangles[keep], mesh.face_normals[keep]
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
    p = params("under_desk_keyboard_rail.scad")
    h = p["KB_H"] + p["GAP_H"] + p["LIP_T"]
    z_lip = -(p["KB_H"] + p["GAP_H"])
    half = (DEMO_W + p["GAP_W"]) / 2

    def hung(path, sign):
        m = trimesh.load(path)
        m.apply_translation((0, 0, -h))           # back to the frame it hangs in
        m.apply_translation((sign * half, 0, 0))
        return m

    right, left = hung("keyboard-rail-right.stl", 1), hung("keyboard-rail-left.stl", -1)
    kb = trimesh.creation.box(
        extents=(DEMO_W, p["KB_D"], p["KB_H"]),
        transform=trimesh.transformations.translation_matrix(
            (0, p["STOP_T"] + p["KB_D"] / 2, z_lip + p["KB_H"] / 2)))
    desk = trimesh.creation.box(
        extents=(DEMO_W + 120, 190, 18),
        transform=trimesh.transformations.translation_matrix((0, 55, 9)))

    fig = plt.figure(figsize=(19, 9), dpi=120)
    ax = fig.add_subplot(2, 3, 1)
    solo = trimesh.load("keyboard-rail-right.stl")
    render(ax, [(solo, BODY)], (-0.7, 0.8, -0.55), "one rail, as it prints")
    render(fig.add_subplot(2, 3, 2), [(right, BODY), (left, BODY), (kb, KB)],
           (-0.6, 0.85, -0.5), f"the pair, {DEMO_W:.0f} mm apart")
    render(fig.add_subplot(2, 3, 3), [(right, BODY), (left, BODY), (kb, KB)],
           (-0.5, 0.8, 0.55), "from below")
    render(fig.add_subplot(2, 3, 4), [(desk, DESK), (right, BODY), (left, BODY), (kb, KB)],
           (-0.5, 0.9, -0.12), "screwed under a desk top")

    # Section: what actually holds the keyboard.
    ax = fig.add_subplot(2, 3, 5)
    sec = solo.section(plane_origin=[0, p["RAIL_L"] / 2, 0], plane_normal=[0, 1, 0])
    for ent in sec.entities:
        pts = sec.vertices[ent.points]
        ax.plot(pts[:, 0], pts[:, 2] - h, "-", color="#334", lw=1.5)
    ax.add_patch(plt.Rectangle((-45, z_lip), 45 - p["GAP_W"] / 2, p["KB_H"],
                               fill=False, ls="--", lw=1.2, color="#b4472e"))
    ax.annotate("keyboard", (-20, z_lip + p["KB_H"] / 2), color="#b4472e",
                fontsize=8, va="center")
    ax.annotate("desk", (10, 1), fontsize=8, color="#666")
    ax.axhline(0, ls="-", lw=1.0, color="#c9a227")
    ax.set_xlim(-30, 20)
    ax.set_ylim(-20, 6)
    ax.set_aspect("equal")
    ax.set_title("section - lip, wall, pad, gusset", fontsize=10, color="#333")
    ax.tick_params(labelsize=7)

    fig.tight_layout()
    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
