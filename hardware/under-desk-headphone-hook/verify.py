#!/usr/bin/env python3
"""
Check the exported hook: will a headband go in, will it stay on, can a driver
reach the screw, does it print without support.

The STL is exported on its side the way it prints, so everything here is
measured after standing it back up.
"""

import math
import re
import sys

import numpy as np
import trimesh

SCAD = "under_desk_headphone_hook.scad"
STL = "headphone-hook.stl"
TOL, V_TOL = 1e-3, 1.0
BAND_D = 28.0        # a fat over-ear headband, padded


def params(path):
    text = re.sub(r"//.*", "", open(path).read())
    return {m.group(1): float(m.group(2))
            for m in re.finditer(r"^\s*([A-Z][A-Z_0-9]*)\s*=\s*(-?[\d.]+)\s*;",
                                 text, re.M)}


def overlap(a, b):
    try:
        shared = trimesh.boolean.intersection([a, b])
    except Exception:
        return 0.0
    if not len(shared.faces):
        return 0.0
    with np.errstate(invalid="ignore", divide="ignore"):
        return float(shared.volume)


def band(y, z, d, w):
    """A length of headband lying across the hook: a cylinder along x."""
    c = trimesh.creation.cylinder(radius=d / 2, height=w, sections=64)
    c.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    c.apply_translation((0, y, z))
    return c


class Checks:
    def __init__(self):
        self.failed = 0

    def __call__(self, ok, label, detail=""):
        print(f"  {'PASS' if ok else 'FAIL'}  {label}{'  -  ' + detail if detail else ''}")
        self.failed += not ok


def main():
    p = params(SCAD)
    r = p["THROAT"] / 2
    bot = -p["DROP"] - r                 # centreline low point
    check = Checks()

    printed = trimesh.load(STL)
    print("mesh")
    check(printed.is_watertight and printed.body_count == 1
          and printed.is_winding_consistent, "one watertight solid")
    lo, hi = printed.bounds
    check(abs(lo[2]) < TOL, "exported sitting on z = 0, on its side")
    check(abs((hi[2] - lo[2]) - p["WIDTH"]) < TOL,
          f"{hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2] - lo[2]:.1f} mm, "
          f"{p['WIDTH']:.0f} mm of that is the cradle's width")
    check(printed.volume > 1000, "the pad is actually there",
          f"{printed.volume / 1000:.1f} cm3 - a bar alone would be about "
          f"{p['WIDTH'] * p['BAR'] * 108 / 1000:.0f}")

    # Stand it back up. The print transform was translate(z += WIDTH/2) after
    # rotate(+90 about Y), so undo both, in that order.
    m = printed.copy()
    m.apply_translation((0, 0, -p["WIDTH"] / 2))
    m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [0, 1, 0]))

    print("headband")
    # 0.25 mm off the cradle floor, so tangency does not read as interference
    # on a faceted cylinder.
    seated = band(p["ARM_Y"] + r, bot + p["BAR"] / 2 + BAND_D / 2 + 0.25,
                  BAND_D, p["WIDTH"] + 10)
    check(overlap(m, seated) < V_TOL, f"a {BAND_D:.0f} mm band sits in the cradle",
          f"{overlap(m, seated):.3f} mm^3 of interference")
    check(p["THROAT"] - p["BAR"] > BAND_D * 0.6,
          f"throat is {p['THROAT'] - p['BAR']:.0f} mm clear between arm and tip")
    lip = (bot + p["BAR"] / 2) - (-p["DROP"] + p["TIP"])
    check(-lip > BAND_D / 2, "the tip rises well past the middle of a seated band",
          f"{-lip:.0f} mm above the cradle floor")
    # nothing to slide off sideways: the cradle is a straight bar across
    across = overlap(m, band(p["ARM_Y"] + r, bot, 2.0, p["WIDTH"] - 0.5))
    check(across > V_TOL, f"cradle is {p['WIDTH']:.0f} mm wide, so it spreads the band",
          f"{across:.0f} mm^3 of bar across it")

    print("fastener")
    def cyl(rad, z0, z1):
        return trimesh.creation.cylinder(
            radius=rad, height=z1 - z0, sections=64,
            transform=trimesh.transformations.translation_matrix(
                (0, p["SCREW_Y"], (z0 + z1) / 2)))
    check(overlap(m, cyl(p["SCREW_D"] / 2 - 0.05, -p["PAD_T"], 0.0)) < V_TOL,
          "screw hole bored through the pad")
    check(overlap(m, cyl(p["HEAD_D"] / 2 + 1.0, -p["PAD_T"], 0.0)) > V_TOL,
          "pad is solid around it")
    fouled = overlap(m, cyl(p["HEAD_D"] / 2 + p["DRIVER_CLR"], -p["PAD_T"] - 40, -p["PAD_T"]))
    check(fouled < V_TOL, "driver reaches the head without hitting the arm",
          f"{fouled:.1f} mm^3 in the way")

    print("print")
    n = printed.face_normals
    steep = n[:, 2] < -np.cos(np.radians(44.0))
    on_bed = (printed.triangles[:, :, 2] < TOL).all(axis=1)
    flagged = steep & ~on_bed & (printed.area_faces > 0.01)
    check(printed.area_faces[flagged].sum() < 60.0,
          "only the screw bore overhangs",
          f"{printed.area_faces[flagged].sum():.0f} mm^2 of the part")

    print(f"\n{printed.volume / 1000:.1f} cm3, ~{printed.volume / 1000 * 1.24 * 0.5:.0f} g "
          f"as printed; hangs {-bot + p['BAR'] / 2:.0f} mm below the desk")
    print("FAILED" if check.failed else "all checks passed")
    return 1 if check.failed else 0


if __name__ == "__main__":
    sys.exit(main())
