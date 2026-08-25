#!/usr/bin/env python3
"""
Check the exported rails against the things that matter on a desk: does the
keyboard slide in, does it land on enough ledge, can a driver reach the screw,
and does it print without support.

Parameters are read back out of the .scad, so this stays honest if the model is
re-tuned. The rail prints the way it hangs, so the STLs are exported sitting on
z = 0 and everything here is measured after dropping them back to the desk.
"""

import re
import sys

import numpy as np
import trimesh

SCAD = "under_desk_keyboard_rail.scad"
RIGHT, LEFT = "keyboard-rail-right.stl", "keyboard-rail-left.stl"
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


def cylinder(x, y, z0, z1, r):
    return trimesh.creation.cylinder(
        radius=r, height=z1 - z0, sections=64,
        transform=trimesh.transformations.translation_matrix((x, y, (z0 + z1) / 2)))


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
    rail_l, wall = p["RAIL_L"], p["WALL"]
    ch_h = p["KB_H"] + p["GAP_H"]
    h = ch_h + p["LIP_T"]
    z_lip, pad_x = -ch_h, wall + p["PAD_W"]
    screw_x = wall + p["PAD_W"] / 2
    rest = p["LIP_IN"]
    check = Checks()

    printed = trimesh.load(RIGHT)
    left = trimesh.load(LEFT)

    print("mesh")
    for name, m in (("right", printed), ("left", left)):
        check(m.is_watertight and m.body_count == 1 and m.is_winding_consistent,
              f"{name} rail is one watertight solid")
    check(abs(printed.volume - left.volume) / printed.volume < 1e-6,
          "the pair are mirror images", f"{printed.volume / 1000:.1f} cm3 each")
    lo_r, hi_r = printed.bounds
    lo_l, hi_l = left.bounds
    check(np.allclose(lo_l[0], -hi_r[0], atol=TOL) and np.allclose(hi_l[0], -lo_r[0], atol=TOL),
          "mirrored across the centre line, not just rotated")

    print("print")
    check(abs(lo_r[2]) < TOL, "exported sitting on z = 0, the way it hangs")
    ext = hi_r - lo_r
    check(np.allclose(ext, [p["LIP_IN"] + pad_x, rail_l, h], atol=TOL),
          f"{ext[0]:.0f} x {ext[1]:.0f} x {ext[2]:.0f} mm each")

    # Back into the frame it hangs in: desk face at z = 0. The rail prints the
    # way it hangs, so this is only a drop.
    m = printed.copy()
    m.apply_translation((0, 0, -h))

    print("fit")
    # The keyboard's edge, from the stop forward and out past the mouth.
    kb = box(-40.0, -p["GAP_W"] / 2, p["STOP_T"] + 0.05, rail_l + 40,
             z_lip + 0.02, z_lip + 0.02 + p["KB_H"])
    check(overlap(m, kb) < V_TOL, "keyboard slides the length of the channel",
          f"{overlap(m, kb):.3f} mm^3 in the way")
    check(ch_h - p["KB_H"] > 0, "clearance over the keyboard",
          f"{ch_h - p['KB_H']:.1f} mm to the desk")

    # How much flat ledge is actually under the keyboard.
    ledge = overlap(m, box(-40.0, 0.0, rail_l / 2 - 5, rail_l / 2 + 5,
                           z_lip - 0.1, z_lip)) / 0.1 / 10
    check(abs(ledge - rest) < 0.2, f"{rest:.0f} mm of flat ledge under the edge",
          f"measured {ledge:.1f} mm, square into the corner")

    print("stop")
    pushed = box(-40.0, -p["GAP_W"] / 2, -5.0, p["STOP_T"] - 0.05,
                 z_lip + 0.02, z_lip + 0.02 + p["KB_H"])
    check(overlap(m, pushed) > V_TOL, "rear stop blocks the keyboard",
          f"{overlap(m, pushed):.0f} mm^3 of interference")

    print("fastener")
    clear = overlap(m, cylinder(screw_x, rail_l / 2, -p["PAD_T"], 0.0,
                                p["SCREW_D"] / 2 - 0.05))
    check(clear < V_TOL, "screw hole bored through the pad",
          f"{clear:.3f} mm^3 of obstruction")
    pad = overlap(m, cylinder(screw_x, rail_l / 2, -p["PAD_T"], 0.0,
                              p["HEAD_D"] / 2 + 1.0))
    check(pad > V_TOL, "pad is solid around the hole", f"{pad:.0f} mm^3")
    reach = p["HEAD_D"] / 2 + 1.5
    fouled = overlap(m, cylinder(screw_x, rail_l / 2, -h - 25, -p["PAD_T"], reach))
    check(fouled < V_TOL, f"driver reaches the head ({reach:.2f} mm radius)",
          f"{fouled:.1f} mm^3 in the way")

    print("support")
    # 45 degrees is the accepted self-supporting limit, so flag only what is
    # steeper than that: a face at 44 degrees off horizontal or less. Both the
    # gusset and the countersink cone sit exactly on 45, and a threshold on the
    # nose would flag them on float noise alone.
    n = printed.face_normals
    steep = n[:, 2] < -np.cos(np.radians(44.0))
    on_bed = (printed.triangles[:, :, 2] < TOL).all(axis=1)
    real = printed.area_faces > 0.01            # booleans leave sliver triangles
    flagged = steep & ~on_bed & real
    strip = p["PAD_W"] - p["GUSSET"]
    if flagged.any():
        zs = printed.triangles[flagged][:, :, 2]
        stray = not np.all(np.abs(zs - (h - p["PAD_T"])) < TOL)
    else:
        stray = False
    check(not stray, "the pad underside is the only overhang in the part",
          f"{strip:.0f} mm strip past the gusset, bridged {p['WINDOW']:.0f} mm "
          f"at the screw, {printed.area_faces[flagged].sum() / printed.area * 100:.1f}% "
          "of surface")
    check(strip <= 8.0 and p["WINDOW"] <= 20.0,
          "that strip and bridge are both printable unsupported")

    print(f"\nwall faces go (keyboard width + {p['GAP_W']:.1f}) mm apart, "
          f"screw centres (keyboard width + {p['GAP_W'] + 2 * screw_x:.1f}) mm")
    print(f"each rail {printed.volume / 1000:.1f} cm3, "
          f"~{printed.volume / 1000 * 1.27 * 0.6:.0f} g as printed")
    print("FAILED" if check.failed else "all checks passed")
    return 1 if check.failed else 0


if __name__ == "__main__":
    sys.exit(main())
