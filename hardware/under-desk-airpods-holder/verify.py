#!/usr/bin/env python3
"""
Check the exported holder: does the case go in, is the tongue actually free,
can a driver reach the screw, does it print without support.

The STL is exported ceiling-down the way it prints, so everything here is
measured after turning it back over.
"""

import math
import re
import sys

import numpy as np
import trimesh

SCAD = "under_desk_airpods_holder.scad"
STL = "airpods-holder.stl"
TOL, V_TOL = 1e-3, 1.0


def params(path):
    text = re.sub(r"//.*", "", open(path).read())
    return {m.group(1): float(m.group(2))
            for m in re.finditer(r"^\s*([A-Z][A-Z_0-9]*)\s*=\s*(-?[\d.]+)\s*;",
                                 text, re.M)}


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return trimesh.creation.box(
        extents=(x1 - x0, y1 - y0, z1 - z0),
        transform=trimesh.transformations.translation_matrix(
            ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)))


def rrect_prism(w, t, r, z0, z1):
    """Rounded-rectangle prism - the case, or something case-shaped."""
    parts = []
    if w - 2 * r > TOL:                     # degenerate when r = w/2 or t/2
        parts.append(box(-w / 2 + r, w / 2 - r, -t / 2, t / 2, z0, z1))
    if t - 2 * r > TOL:
        parts.append(box(-w / 2, w / 2, -t / 2 + r, t / 2 - r, z0, z1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = trimesh.creation.cylinder(
                radius=r, height=z1 - z0, sections=64,
                transform=trimesh.transformations.translation_matrix(
                    (sx * (w / 2 - r), sy * (t / 2 - r), (z0 + z1) / 2)))
            parts.append(c)
    return trimesh.boolean.union(parts)


def overlap(a, b):
    try:
        shared = trimesh.boolean.intersection([a, b])
    except Exception:
        return 0.0
    if not len(shared.faces):
        return 0.0
    with np.errstate(invalid="ignore", divide="ignore"):
        return float(shared.volume)


class Checks:
    def __init__(self):
        self.failed = 0

    def __call__(self, ok, label, detail=""):
        print(f"  {'PASS' if ok else 'FAIL'}  {label}{'  -  ' + detail if detail else ''}")
        self.failed += not ok


def main():
    p = params(SCAD)
    h = p["TOP_T"] + p["DEPTH"]
    pock_w, pock_t = p["CASE_W"] + 2 * p["GAP"], p["CASE_T"] + 2 * p["GAP"]
    z_ceil, z_mouth = -p["TOP_T"], -h
    check = Checks()

    printed = trimesh.load(STL)
    print("mesh")
    check(printed.is_watertight and printed.body_count == 1
          and printed.is_winding_consistent, "one watertight solid")
    lo, hi = printed.bounds
    check(abs(lo[2]) < TOL, "exported sitting on z = 0, ceiling down")
    check(np.allclose(hi - lo, [pock_w + 2 * p["WALL"], pock_t + 2 * p["WALL"], h],
                      atol=TOL),
          f"{hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2] - lo[2]:.1f} mm")

    m = printed.copy()                       # back the way it hangs
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))

    print("fit")
    # The case, at the squarest it can be and still be expected to fit: corners
    # exactly the pocket radius less the clearance. If this goes in, a rounder
    # one does too.
    worst_r = p["POCKET_R"] - p["GAP"]
    for label, r in ((f"squarest case it claims ({worst_r:.1f} mm corners)", worst_r),
                     (f"fully rounded ends ({p['CASE_T'] / 2:.2f} mm)", p["CASE_T"] / 2)):
        case = rrect_prism(p["CASE_W"], p["CASE_T"], r, z_ceil - p["CASE_H"], z_ceil)
        hit = overlap(m, case)
        # the bump is meant to be in the way; measure with it pressed flat
        bumpless = overlap(m, trimesh.boolean.difference(
            [case, box(-p["TONGUE_W"] / 2 - 1, p["TONGUE_W"] / 2 + 1,
                       pock_t / 2 - p["BUMP"] - 0.05, pock_t / 2 + 5,
                       z_mouth - 1, z_ceil + 1)]))
        check(bumpless < V_TOL, f"pocket takes the {label}",
              f"{bumpless:.3f} mm^3 outside the bump")
    check(overlap(m, rrect_prism(p["CASE_W"], p["CASE_T"], p["CASE_T"] / 2,
                                 z_ceil - p["CASE_H"], z_ceil)) > V_TOL,
          "the bump does bear on the case", "it is the grip")

    print("grip")
    slot = 0.0
    for s in (-1.0, 1.0):
        slot += overlap(m, box(s * (p["TONGUE_W"] / 2 + 0.05),
                               s * (p["TONGUE_W"] / 2 + p["SLOT"] - 0.05),
                               pock_t / 2 + 0.05, pock_t / 2 + p["WALL"] - 0.05,
                               z_mouth + 0.05, z_mouth + p["TONGUE_L"] - 0.05))
    check(slot < V_TOL, "the tongue is cut free either side",
          f"{slot:.3f} mm^3 bridging a slot")
    crest = trimesh.boolean.intersection(
        [m, box(-p["TONGUE_W"] / 2, p["TONGUE_W"] / 2, 0, pock_t,
                z_mouth + p["BUMP_Z"] - 0.4, z_mouth + p["BUMP_Z"] + 0.4)])
    stands = pock_t / 2 - crest.bounds[0][1] if len(crest.faces) else 0.0
    check(abs(stands - p["BUMP"]) < 0.05,
          f"bump stands {p['BUMP']:.1f} mm into the pocket",
          f"measured {stands:.2f} mm")

    print("fastener")
    def cyl(r, z0, z1):
        return trimesh.creation.cylinder(
            radius=r, height=z1 - z0, sections=64,
            transform=trimesh.transformations.translation_matrix((0, 0, (z0 + z1) / 2)))
    check(overlap(m, cyl(p["SCREW_D"] / 2 - 0.05, z_ceil, 0.0)) < V_TOL,
          "screw hole bored through the ceiling")
    check(overlap(m, cyl(p["HEAD_D"] / 2 + 1.0, z_ceil, 0.0)) > V_TOL,
          "ceiling is solid around it")
    check(overlap(m, cyl(p["HEAD_D"] / 2 + 1.5, z_mouth - 30, z_ceil)) < V_TOL,
          "driver reaches it through the open mouth",
          "screw it up before the case goes in")

    print("support")
    n = printed.face_normals
    steep = n[:, 2] < -np.cos(np.radians(44.0))
    on_bed = (printed.triangles[:, :, 2] < TOL).all(axis=1)
    flagged = steep & ~on_bed & (printed.area_faces > 0.01)
    check(not flagged.any(), "nothing in the part overhangs at all",
          f"{flagged.sum()} faces steeper than 45 degrees")

    print(f"\n{printed.volume / 1000:.1f} cm3, ~{printed.volume / 1000 * 1.24 * 0.6:.0f} g "
          f"as printed; the case stands {p['CASE_H'] - p['DEPTH']:.0f} mm proud to grab")
    print("FAILED" if check.failed else "all checks passed")
    return 1 if check.failed else 0


if __name__ == "__main__":
    sys.exit(main())
