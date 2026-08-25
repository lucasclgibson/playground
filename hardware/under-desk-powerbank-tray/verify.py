#!/usr/bin/env python3
"""
Check the exported STLs against the things that actually matter on a desk:
does the PC fit, does it slide in, does it stay in, will it print unsupported.

Parameters are read back out of the .scad file, so this stays honest if the
model is re-tuned. Run after ./build.sh (or on its own once the STLs exist).
"""

import re
import sys

import numpy as np
import trimesh

SCAD = "under_desk_powerbank_tray.scad"
STL = "under-desk-powerbank-tray.stl"
STL_PRINT = "under-desk-powerbank-tray-print.stl"

TOL = 1e-3          # mm
V_TOL = 1.0         # mm^3, slack for mesh boolean noise


def params(path):
    """Pull the scalar parameters straight out of the model."""
    text = re.sub(r"//.*", "", open(path).read())
    return {m.group(1): float(m.group(2))
            for m in re.finditer(r"^\s*([A-Z][A-Z_0-9]*)\s*=\s*(-?[\d.]+)\s*;",
                                 text, re.M)}


def box(x0, x1, y0, y1, z0, z1):
    """Box from two opposite corners, in either order."""
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return trimesh.creation.box(
        extents=(x1 - x0, y1 - y0, z1 - z0),
        transform=trimesh.transformations.translation_matrix(
            ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)))


def overlap(a, b):
    """Volume shared by two solids, in mm^3."""
    try:
        shared = trimesh.boolean.intersection([a, b])
    except Exception:
        return 0.0
    if not len(shared.faces):
        return 0.0
    with np.errstate(invalid="ignore", divide="ignore"):        # empty result -> 0/0 in trimesh
        return float(shared.volume)


def cylinder(x, y, z0, z1, r):
    return trimesh.creation.cylinder(
        radius=r, height=z1 - z0, sections=64,
        transform=trimesh.transformations.translation_matrix((x, y, (z0 + z1) / 2)))


def vent_cells(u_ext, v_ext, w, length, angle):
    """Cell count of one vent field - mirrors the module in the .scad."""
    rise = w / 2 * np.tan(np.radians(angle))
    dv = length - rise
    nrow = int((v_ext - length) // dv) + 1
    kmax = int(np.ceil(u_ext / w))
    return sum(1
               for j in range(nrow)
               for k in range(-kmax, kmax + 1)
               if abs((j % 2) * w / 2 + k * w) + w / 2 <= u_ext / 2 + TOL)


class Checks:
    def __init__(self):
        self.failed = 0

    def __call__(self, ok, label, detail=""):
        print(f"  {'PASS' if ok else 'FAIL'}  {label}{'  -  ' + detail if detail else ''}")
        self.failed += not ok


def main():
    p = params(SCAD)
    pc_w, pc_d, pc_h = p["BANK_W"], p["BANK_D"], p["BANK_H"]

    cav_w = pc_w + 2 * p["GAP_SIDE"]
    cav_h = pc_h + p["GAP_TOP"]
    out_w = cav_w + 2 * p["WALL"]
    out_d = p["BACK_T"] + pc_d + p["GAP_BACK"] + p["FRONT_LIP"]
    out_h = p["TOP_T"] + cav_h + p["SHELF_T"]
    total_w = out_w + 2 * p["EAR_L"]
    z_floor = -(p["TOP_T"] + cav_h)
    z_cav_top = -p["TOP_T"]
    screw_x = out_w / 2 + p["EAR_L"] / 2
    bank_front = p["BACK_T"] + pc_d + p["GAP_BACK"]
    band_y0 = bank_front - p["BAND_DEPTH"] - p["BAND_CLR"]

    mount = trimesh.load(STL)
    check = Checks()

    print("mesh")
    check(mount.is_watertight, "watertight")
    check(mount.body_count == 1, "one connected solid", f"{mount.body_count} bodies")
    check(mount.is_winding_consistent, "consistent winding")

    print("envelope")
    lo, hi = mount.bounds
    want_lo = np.array([-total_w / 2, 0.0, -out_h])
    want_hi = np.array([total_w / 2, out_d, 0.0])
    check(np.allclose(lo, want_lo, atol=TOL) and np.allclose(hi, want_hi, atol=TOL),
          f"{total_w:.1f} x {out_d:.1f} x {out_h:.1f} mm",
          f"got {np.round(hi - lo, 2).tolist()}")

    # The PC pushed fully home: nothing may touch it.
    seated = box(-pc_w / 2, pc_w / 2,
                 p["BACK_T"], p["BACK_T"] + pc_d,
                 z_floor, z_floor + pc_h)
    print("fit")
    touching = overlap(mount, seated)
    check(touching < V_TOL, "seated bank clears the frame", f"{touching:.3f} mm^3")
    check(z_floor + pc_h + TOL < z_cav_top,
          "headroom above the seated bank",
          f"{z_cav_top - (z_floor + pc_h):.2f} mm")

    # Nothing latches it, so the whole travel has to be clear - in and out.
    print("slide")
    x_cav = cav_w / 2
    sweep = box(-pc_w / 2, pc_w / 2, p["BACK_T"], out_d + pc_d,
                z_floor + 0.02, z_floor + 0.02 + pc_h)
    blocked = overlap(mount, sweep)
    check(blocked < V_TOL, "slides the whole way in and out, nothing in the path",
          f"{blocked:.3f} mm^3 of obstruction")
    back = overlap(mount, box(-pc_w / 2, pc_w / 2, -20.0, p["BACK_T"] - 0.05,
                              z_floor + 0.02, z_floor + 0.02 + pc_h))
    check(back > V_TOL, "the far end is closed off", f"{back:.0f} mm^3 of back wall")
    ledge = overlap(mount, box(-x_cav, x_cav, out_d / 2 - 5, out_d / 2 + 5,
                               z_floor - 0.1, z_floor)) / 0.1 / 10
    check(ledge > 2 * p["SHELF_W"] - 0.2,
          f"{2 * p['SHELF_W']:.0f} mm of shelf carries it",
          f"measured {ledge:.1f} mm across both sides")

    # The band on the brick's side has to pass down the slot the whole way in.
    print("band")
    side = 1.0 if p["BAND_SIDE"] > 0 else -1.0
    band_z = z_floor + pc_h / 2 + p["BAND_OFF"]
    # Stand it well proud of the wall: the slot is cut right through, so however
    # far the band sticks out it must meet nothing.
    def band_box(y0, y1):
        return box(side * pc_w / 2, side * (out_w / 2 + 10.0), y0, y1,
                   band_z - p["BAND_W"] / 2, band_z + p["BAND_W"] / 2)

    seated_band = band_box(bank_front - p["BAND_DEPTH"], bank_front)
    fouled_band = overlap(mount, seated_band)
    check(fouled_band < V_TOL,
          f"seated band clears the slot "
          f"({p['BAND_W']:.0f} mm across, {p['BAND_DEPTH']:.0f} mm down)",
          f"{fouled_band:.3f} mm^3")
    swept_band = overlap(mount, band_box(bank_front - p["BAND_DEPTH"],
                                         bank_front + pc_d))
    check(swept_band < V_TOL, "band slides the whole way in and out",
          f"{swept_band:.3f} mm^3 of obstruction")
    # ... and no further: the wall has to close up again behind it.
    behind = overlap(mount, box(side * cav_w / 2, side * out_w / 2,
                                band_y0 - p["VENT_RIB"], band_y0 - 0.1,
                                band_z - p["BAND_W"] / 2, band_z + p["BAND_W"] / 2))
    check(behind > V_TOL, "wall closes again behind the slot",
          f"{behind:.0f} mm^3 of solid wall, slot ends {out_d - band_y0:.1f} mm "
          f"in from the mouth")
    check(band_z - p["BAND_W"] / 2 - p["BAND_CLR"] > z_floor + TOL
          and band_z + p["BAND_W"] / 2 + p["BAND_CLR"] < z_cav_top - TOL,
          "slot stays clear of the shelf and the top plate",
          f"{band_z - p['BAND_W'] / 2 - p['BAND_CLR'] - z_floor:.1f} mm below, "
          f"{z_cav_top - (band_z + p['BAND_W'] / 2 + p['BAND_CLR']):.1f} mm above")

    # Vents. Genus counts the through-holes, so a field that silently came out
    # empty shows up here instead of just as a heavier part.
    print("vents")
    top_cells = vent_cells(out_w - 2 * p["TOP_VENT_BORDER"],
                           out_d - 2 * p["TOP_VENT_BORDER"],
                           p["VENT_W"], p["VENT_LEN"], p["VENT_ANGLE"])
    plain_cells = vent_cells(cav_h - 2 * p["SIDE_VENT_MARGIN"],
                             out_d - 2 * p["SIDE_VENT_BORDER"],
                             p["VENT_W"], p["VENT_LEN"], p["VENT_ANGLE"])
    band_cells = vent_cells(cav_h - 2 * p["SIDE_VENT_MARGIN"],
                            band_y0 - p["VENT_RIB"] - p["SIDE_VENT_BORDER"],
                            p["VENT_W"], p["VENT_LEN"], p["VENT_ANGLE"])
    # The band slot opens into the mouth rather than through a closed wall, so
    # it widens the front opening instead of adding a handle: no extra genus.
    want_holes = top_cells + plain_cells + band_cells + 4   # + screws; closed back
    genus = (2 - mount.euler_number) // 2
    check(genus == want_holes,
          f"{top_cells} top cells, {plain_cells} in the plain wall, "
          f"{band_cells} in the banded wall, 4 screws, closed back",
          f"{genus} through-holes in the mesh, expected {want_holes}")

    # Screw holes: clear all the way through, with solid flange around them.
    print("fasteners")
    clear, solid, n_holes = 0.0, 0.0, 0
    for sx in (-screw_x, screw_x):
        for sy in (p["SCREW_INSET"], out_d - p["SCREW_INSET"]):
            n_holes += 1
            clear += overlap(mount, cylinder(sx, sy, -p["EAR_T"], 0.0,
                                             p["SCREW_D"] / 2 - 0.05))
            solid += overlap(mount, cylinder(sx, sy, -p["EAR_T"], 0.0,
                                             p["HEAD_D"] / 2 + 2.0))
    check(n_holes == 4 and clear < V_TOL, f"{n_holes} screw holes bored through",
          f"{clear:.3f} mm^3 of obstruction")
    check(solid > V_TOL, "pad is solid around every hole",
          f"{solid:.0f} mm^3 of pad")

    # A screw is no use if a driver cannot reach it: nothing may sit inside the
    # head's approach below the pad.
    reach = p["HEAD_D"] / 2 + p["DRIVER_CLR"]
    fouled = 0.0
    for sx in (-screw_x, screw_x):
        for sy in (p["SCREW_INSET"], out_d - p["SCREW_INSET"]):
            fouled += overlap(mount, cylinder(sx, sy, -p["EAR_T"] - 25,
                                              -p["EAR_T"], reach))
    check(fouled < V_TOL, f"driver reaches every head ({reach:.1f} mm radius)",
          f"{fouled:.1f} mm^3 in the way")

    # Print orientation: flat on the bed, no supports needed.
    print("print")
    pm = trimesh.load(STL_PRINT)
    plo, phi = pm.bounds
    check(abs(plo[2]) < TOL and np.allclose(plo[:2], [-total_w / 2, 0], atol=TOL),
          "print copy sits on z = 0")
    check(abs(pm.volume - mount.volume) / mount.volume < 1e-6,
          "print copy is the same solid", f"{pm.volume / 1000:.2f} cm3")
    footprint = phi - plo
    check(abs(footprint[0] - total_w) < TOL and abs(footprint[2] - out_d) < TOL,
          f"bed footprint {footprint[0]:.1f} x {footprint[1]:.1f} mm, "
          f"{footprint[2]:.1f} mm tall")
    # Nothing may need support: the only downward-facing patches off the bed
    # should be the rounded ends of the vent slots and the horizontal screw
    # bores. A real unsupported roof would show up as one large patch.
    n = pm.face_normals
    steep = n[:, 2] < -np.cos(np.radians(45.0))
    on_bed = (pm.triangles[:, :, 2] < TOL).all(axis=1)
    flagged = steep & ~on_bed
    biggest, where = 0.0, None
    if flagged.any():
        idx = np.flatnonzero(flagged)
        root = {i: i for i in idx}

        def find(i):
            while root[i] != i:
                root[i] = root[root[i]]
                i = root[i]
            return i

        pairs = pm.face_adjacency
        for a, b in pairs[flagged[pairs].all(axis=1)]:
            ra, rb = find(a), find(b)
            if ra != rb:
                root[ra] = rb
        patches = {}
        for i in idx:
            patches.setdefault(find(i), []).append(i)
        for faces in patches.values():
            a = pm.area_faces[faces].sum()
            if a > biggest:
                biggest, where = a, np.ptp(pm.triangles[faces].reshape(-1, 3), axis=0)
    check(biggest < 100.0, "no overhang large enough to need support",
          f"largest patch {biggest:.0f} mm^2 "
          f"({np.round(where, 1).tolist() if where is not None else 'none'} mm), "
          f"{pm.area_faces[flagged].sum() / pm.area * 100:.1f}% of surface")

    print(f"\nsolid volume {mount.volume / 1000:.1f} cm3 "
          f"(~{mount.volume / 1000 * 1.24:.0f} g if printed 100% infill)")
    print("FAILED" if check.failed else "all checks passed")
    return 1 if check.failed else 0


if __name__ == "__main__":
    sys.exit(main())
