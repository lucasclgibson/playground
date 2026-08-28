"""Extrude the UK Property Looker badge into a printable solid.

    python3 badge.py --width 100 --style plaque --out ukpl_badge_plaque_100mm.stl

The mark is two disconnected shapes -- a roof chevron floating 5.5 mm (at 100 mm
wide) above a rounded tag. `plaque` sits them on a thin backing plate that
follows their outline, giving one solid piece; `flat` extrudes the two shapes
alone, for gluing up or printing as separate parts.
"""

import argparse

import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union
from trimesh.creation import extrude_polygon

import shapes

MIN_WALL = 1.5            # mm: two nozzle widths, the thinnest we call printable


def parts(poly):
    return list(poly.geoms) if isinstance(poly, MultiPolygon) else [poly]


def to_millimetres(poly, width_mm, simplify=0.02):
    """Scale to the requested width, flip SVG's y-down axis, centre on the origin.

    The flattened curves carry far more points than a printer can resolve;
    simplifying at `simplify` mm drops the redundant ones (and with them the
    degenerate slivers that would otherwise survive into the mesh).
    """
    x0, y0, x1, y1 = poly.bounds
    s = width_mm / (x1 - x0)
    poly = affinity.scale(poly, xfact=s, yfact=-s, origin=(0, 0))
    x0, y0, x1, y1 = poly.bounds
    poly = affinity.translate(poly, -(x0 + x1) / 2, -(y0 + y1) / 2)
    return poly.simplify(simplify).buffer(0)


def extrude(poly, bottom, top):
    """Extrude a (multi)polygon between two Z heights."""
    meshes = []
    for p in parts(poly):
        m = extrude_polygon(p, height=top - bottom)
        m.apply_translation([0, 0, bottom])
        m.update_faces(m.nondegenerate_faces())
        m.remove_unreferenced_vertices()
        meshes.append(m)
    return trimesh.util.concatenate(meshes) if len(meshes) > 1 else meshes[0]


def default_border(outline, width):
    """Wide enough to fuse the mark into one piece, with a little margin."""
    need = shapes.merge_radius(parts(outline))
    return round(max(need + 0.6, 0.025 * width), 1)


def build(svg="badge.svg", width=100.0, style="plaque", thickness=6.0,
          plate=2.5, border=None):
    logo = to_millimetres(shapes.load(svg)[0], width)

    if style == "flat":
        mesh = extrude(logo, 0.0, thickness)
        plate_poly = None
    else:
        # The plate follows the mark's outline; ignoring the eyelet keeps it
        # solid there, so the hole reads as a recess rather than a puncture.
        outline = unary_union([Polygon(p.exterior) for p in parts(logo)])
        if border is None:
            border = default_border(outline, width)
        plate_poly = outline.buffer(border, join_style=1, quad_segs=64)
        if len(parts(plate_poly)) > 1:
            need = shapes.merge_radius(parts(outline))
            raise SystemExit(f"--border {border} mm cannot join the mark into one "
                             f"piece; it needs at least {need:.1f} mm at this width")
        print(f"  plate border {border:.1f} mm")
        mesh = trimesh.boolean.union([extrude(plate_poly, 0.0, plate),
                                      extrude(logo, plate, thickness)])
    mesh.merge_vertices()
    mesh.remove_unreferenced_vertices()
    return mesh, logo, plate_poly


def report(mesh, logo, plate_poly, style, plate, thickness):
    lo, hi = mesh.bounds
    print(f"  size      {hi[0]-lo[0]:.1f} W x {hi[1]-lo[1]:.1f} D x {hi[2]-lo[2]:.1f} H mm")
    print(f"  triangles {len(mesh.faces):,}   bodies {mesh.body_count}")
    # A flat part is mostly solid top/bottom skin, so estimate that explicitly
    # rather than pretending infill dominates.
    foot = (plate_poly if plate_poly is not None else logo)
    skin = foot.area * 1.6                       # 0.8 mm solid top and bottom
    walls = (foot.length + logo.length) * 1.2 * max(thickness - 1.6, 0.0)
    est = (skin + walls + 0.15 * max(mesh.volume - skin - walls, 0.0)) / 1000 * 1.24
    print(f"  volume    {mesh.volume/1000:.1f} cm^3 solid  "
          f"(~{est:.0f} g of PLA at 15% infill, ~{mesh.volume/1000*1.24:.0f} g solid)")
    print(f"  watertight {mesh.is_watertight}   winding-consistent "
          f"{mesh.is_winding_consistent}   euler {mesh.euler_number}")

    thin = shapes.thin_area_fraction(logo, MIN_WALL)
    print(f"  mark:  {100*thin:.2f}% of its area is narrower than {MIN_WALL} mm")
    ok = thin < 0.005
    if plate_poly is not None:
        pthin = shapes.thin_area_fraction(plate_poly, MIN_WALL)
        print(f"  plate: {100*pthin:.2f}% narrower than {MIN_WALL} mm, "
              f"one piece = {len(parts(plate_poly)) == 1}")
        ok = ok and pthin < 0.005 and len(parts(plate_poly)) == 1
        print(f"  colour change at layer Z = {plate:.2f} mm splits plate from mark")
    expect = 1 if style == "plaque" else 2
    ok = ok and mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == expect
    if mesh.body_count != expect:
        print(f"  ! expected {expect} bodies for style {style}")
    return ok


def preview(logo, plate_poly, out, px=1400):
    """Flat top-down PNG, to check the outline still matches the source art."""
    from PIL import Image, ImageDraw
    geoms = [plate_poly] if plate_poly is not None else []
    bounds = unary_union([g for g in geoms + parts(logo)]).bounds
    w = bounds[2] - bounds[0]
    s = (px - 60) / w
    h = int((bounds[3] - bounds[1]) * s) + 60
    img = Image.new("RGB", (px, h), (250, 250, 251))
    dr = ImageDraw.Draw(img)

    def xy(coords):
        return [(30 + (x - bounds[0]) * s, h - 30 - (y - bounds[1]) * s) for x, y in coords]

    for p in parts(plate_poly) if plate_poly is not None else []:
        dr.polygon(xy(p.exterior.coords), fill=(206, 215, 230))
    for p in parts(logo):
        dr.polygon(xy(p.exterior.coords), fill=(26, 90, 200))
        for ring in p.interiors:
            dr.polygon(xy(ring.coords), fill=(206, 215, 230) if plate_poly is not None
                       else (250, 250, 251))
    img.save(out)
    print(f"  wrote {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--svg", default="badge.svg")
    ap.add_argument("--width", type=float, default=100.0, help="width of the mark, mm")
    ap.add_argument("--style", choices=("plaque", "flat"), default="plaque")
    ap.add_argument("--thickness", type=float, default=6.0, help="total, mm")
    ap.add_argument("--plate", type=float, default=2.5, help="backing plate, mm")
    ap.add_argument("--border", type=float, default=None,
                    help="plate border in mm (default: scales with --width)")
    ap.add_argument("--preview", default=None, help="also write a flat PNG here")
    ap.add_argument("--out", default="ukpl_badge.stl")
    a = ap.parse_args()

    mesh, logo, plate_poly = build(a.svg, a.width, a.style, a.thickness, a.plate, a.border)
    ok = report(mesh, logo, plate_poly, a.style, a.plate, a.thickness)
    if a.preview:
        preview(logo, plate_poly, a.preview)
    mesh.export(a.out)
    print(f"  wrote {a.out}")
    raise SystemExit(0 if ok else 1)
