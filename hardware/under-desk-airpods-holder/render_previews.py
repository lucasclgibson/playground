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
    p = params("under_desk_airpods_holder.scad")
    h = p["TOP_T"] + p["DEPTH"]
    z_ceil = -p["TOP_T"]

    printed = trimesh.load("airpods-holder.stl")
    hung = printed.copy()
    hung.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))

    # The case, drawn with fully rounded ends - the shape it most likely is.
    r = p["CASE_T"] / 2
    case = trimesh.boolean.union([
        trimesh.creation.box(
            extents=(p["CASE_W"] - 2 * r, p["CASE_T"], p["CASE_H"]),
            transform=trimesh.transformations.translation_matrix(
                (0, 0, z_ceil - p["CASE_H"] / 2)))] + [
        trimesh.creation.cylinder(
            radius=r, height=p["CASE_H"], sections=64,
            transform=trimesh.transformations.translation_matrix(
                (s * (p["CASE_W"] / 2 - r), 0, z_ceil - p["CASE_H"] / 2)))
        for s in (-1, 1)])
    desk = trimesh.creation.box(
        extents=(140, 110, 16),
        transform=trimesh.transformations.translation_matrix((0, 0, 8)))

    fig, axes = plt.subplots(1, 4, figsize=(20, 6), dpi=120)
    render(axes[0], [(printed, BODY)], (-0.7, 0.8, -0.55), "as it prints, ceiling down")
    render(axes[1], [(hung, BODY), (case, KB)], (-0.7, 0.8, -0.5), "case in place")
    render(axes[2], [(hung, BODY)], (-0.5, 0.8, 0.6), "from below - mouth and tongue")
    render(axes[3], [(desk, DESK), (hung, BODY), (case, KB)], (-0.55, 0.9, -0.1),
           "screwed under a desk top")
    fig.tight_layout()
    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
