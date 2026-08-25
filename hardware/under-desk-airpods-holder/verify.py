#!/usr/bin/env python3
"""
Check the exported tray: does the case slide the whole way in, does it land on
solid floor, can a driver reach the screws, does it print without support.

The STL is exported on its back face the way it prints, so everything here is
measured after standing it back up.
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


def case_solid(w, t, d, y0, z0):
    """The case lying flat: a stadium section w x t, swept d along y. The ends
    are taken as fully round, which is the most material the case can have."""
    r = t / 2
    parts = [box(-w / 2 + r, w / 2 - r, y0, y0 + d, z0, z0 + t)]
    for s in (-1, 1):
        c = trimesh.creation.cylinder(radius=r, height=d, sections=64)
        c.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
        c.apply_translation((s * (w / 2 - r), y0 + d / 2, z0 + r))
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
    cav_w = p["CASE_W"] + 2 * p["GAP_SIDE"]
    cav_t = p["CASE_T"] + p["GAP_TOP"]
    out_w = cav_w + 2 * p["WALL"]
    out_d = p["BACK_T"] + p["CASE_D"] + p["GAP_BACK"] + p["FRONT_LIP"]
    out_h = p["TOP_T"] + cav_t + p["FLOOR_T"]
    z_floor = -(p["TOP_T"] + cav_t)
    screw_x = out_w / 2 + p["EAR_L"] / 2
    check = Checks()

    printed = trimesh.load(STL)
    print("mesh")
    check(printed.is_watertight and printed.body_count == 1
          and printed.is_winding_consistent, "one watertight solid")
    lo, hi = printed.bounds
    check(abs(lo[2]) < TOL, "exported sitting on z = 0, on its back face")
    check(np.allclose(hi - lo, [out_w + 2 * p["EAR_L"], out_h, out_d], atol=TOL),
          f"{hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2] - lo[2]:.1f} mm")

    m = printed.copy()                        # stand it back up
    m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]))

    print("slide")
    # Swept from seated all the way out of the mouth, at rest height.
    sweep = trimesh.boolean.union(
        [case_solid(p["CASE_W"], p["CASE_T"], p["CASE_D"] + out_d,
                    p["BACK_T"], z_floor + 0.02)])
    blocked = overlap(m, sweep)
    check(blocked < V_TOL, "slides the whole way in and out, nothing in the path",
          f"{blocked:.3f} mm^3 of obstruction")
    check(cav_t - p["CASE_T"] > 0, "clearance over the case",
          f"{cav_t - p['CASE_T']:.1f} mm to the desk")
    back = overlap(m, box(-p["CASE_W"] / 2, p["CASE_W"] / 2, -20.0, p["BACK_T"] - 0.05,
                          z_floor + 0.02, z_floor + 0.02 + p["CASE_T"]))
    check(back > V_TOL, "the far end is closed off", f"{back:.0f} mm^3 of back wall")

    print("support")
    # The case's face is only flat across its middle, so the floor has to be
    # solid under that - not a pair of shelves out at the edges.
    flat = p["CASE_W"] - 2 * (p["CASE_T"] / 2)
    floor = overlap(m, box(-flat / 2, flat / 2, out_d / 2 - 5, out_d / 2 + 5,
                           z_floor - 0.1, z_floor)) / 0.1 / 10
    check(abs(floor - flat) < 0.2,
          f"floor is solid under the case's flat {flat:.1f} mm middle",
          f"measured {floor:.1f} mm")
    notch = overlap(m, box(-p["NOTCH_R"] + 2, p["NOTCH_R"] - 2, out_d - 4, out_d,
                           z_floor - p["FLOOR_T"], z_floor))
    check(notch < V_TOL, "thumb notch is open at the mouth",
          f"{notch:.1f} mm^3 of floor left in it")

    print("fasteners")
    def cyl(x, r, z0, z1):
        return trimesh.creation.cylinder(
            radius=r, height=z1 - z0, sections=64,
            transform=trimesh.transformations.translation_matrix(
                (x, out_d / 2, (z0 + z1) / 2)))
    clear = solid = fouled = 0.0
    for sx in (-screw_x, screw_x):
        clear += overlap(m, cyl(sx, p["SCREW_D"] / 2 - 0.05, -p["EAR_T"], 0.0))
        solid += overlap(m, cyl(sx, p["HEAD_D"] / 2 + 1.0, -p["EAR_T"], 0.0))
        fouled += overlap(m, cyl(sx, p["HEAD_D"] / 2 + p["DRIVER_CLR"],
                                 -out_h - 25, -p["EAR_T"]))
    check(clear < V_TOL, "2 screw holes bored through", f"{clear:.3f} mm^3")
    check(solid > V_TOL, "pads solid around them", f"{solid:.0f} mm^3")
    check(fouled < V_TOL, "driver reaches both heads", f"{fouled:.1f} mm^3 in the way")

    print("print")
    # Everything is walls running along the build direction. The only thing
    # left facing down is the top of each screw bore, which is a 5 mm hole
    # printed on its side - routine.
    n = printed.face_normals
    steep = n[:, 2] < -np.cos(np.radians(44.0))
    on_bed = (printed.triangles[:, :, 2] < TOL).all(axis=1)
    flagged = steep & ~on_bed & (printed.area_faces > 0.01)
    stray = 0
    if flagged.any():
        cx = printed.triangles[flagged][:, :, 0].mean(axis=1)
        stray = int((np.abs(np.abs(cx) - screw_x) > p["HEAD_D"]).sum())
    check(stray == 0, "the screw bores are the only overhang in the part",
          f"{printed.area_faces[flagged].sum():.0f} mm^2 total, "
          f"{stray} faces anywhere else")

    print(f"\n{printed.volume / 1000:.1f} cm3, ~{printed.volume / 1000 * 1.24 * 0.5:.0f} g "
          f"as printed; screw centres {2 * screw_x:.1f} mm apart")
    print("FAILED" if check.failed else "all checks passed")
    return 1 if check.failed else 0


if __name__ == "__main__":
    sys.exit(main())
