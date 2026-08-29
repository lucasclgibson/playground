"""Flat PNGs of the tiara: the face as drawn, and the comb in plan."""

import sys

import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union

import design

BG, INK, SOFT = (16, 18, 28), (228, 238, 252), (150, 170, 205)


def parts(g):
    return list(g.geoms) if isinstance(g, MultiPolygon) else [g]


def panel(dr, geoms, box, pad=26):
    x0b, y0b, x1b, y1b = box
    whole = unary_union([g for g, _ in geoms])
    x0, y0, x1, y1 = whole.bounds
    s = min((x1b - x0b - 2 * pad) / (x1 - x0), (y1b - y0b - 2 * pad) / (y1 - y0))
    ox = x0b + (x1b - x0b - (x1 - x0) * s) / 2 - x0 * s
    oy = y1b - (y1b - y0b - (y1 - y0) * s) / 2 + y0 * s

    def xy(coords):
        return [(ox + x * s, oy - y * s) for x, y in coords]

    for geom, colour in geoms:
        for p in parts(geom):
            dr.polygon(xy(p.exterior.coords), fill=colour)
            for r in p.interiors:
                dr.polygon(xy(r.coords), fill=BG)


def draw(out="preview.png", px=1500, curve_r=110.0):
    jewel, band, stones = design.face()
    comb = design.comb_plan(curve_r)
    face = unary_union([jewel, band])
    ratio = (face.bounds[3] - face.bounds[1]) / (face.bounds[2] - face.bounds[0])
    top = int(px * ratio) + 52
    bot = int(px * 0.42)
    img = Image.new("RGB", (px, top + bot), BG)
    dr = ImageDraw.Draw(img)
    panel(dr, [(band, SOFT), (jewel, INK)], (0, 0, px, top))
    panel(dr, [(comb, SOFT)], (0, top, px, top + bot))
    dr.text((16, top - 20), "face, as drawn flat then wrapped", fill=SOFT)
    dr.text((16, top + bot - 22), "comb in plan, at right angles to it", fill=SOFT)
    img.save(out)
    print(f"  face {face.bounds[2]-face.bounds[0]:.1f} x {face.bounds[3]:.1f} mm, "
          f"{len(parts(face))} piece(s); comb {comb.bounds[2]-comb.bounds[0]:.1f} x "
          f"{comb.bounds[3]-comb.bounds[1]:.1f} mm")
    print(f"  wrote {out}")


if __name__ == "__main__":
    draw(sys.argv[1] if len(sys.argv) > 1 else "preview.png")
