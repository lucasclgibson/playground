"""Flat top-down PNG of the tiara outline, for judging the drawing."""

import sys

from PIL import Image, ImageDraw
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union

import design


def parts(g):
    return list(g.geoms) if isinstance(g, MultiPolygon) else [g]


def draw(out="preview.png", px=1500, pad=30, show_stones=False):
    jewel, band, comb, stones = design.build()
    base = unary_union([band, comb])
    whole = unary_union([jewel, base])
    x0, y0, x1, y1 = whole.bounds
    s = (px - 2 * pad) / (x1 - x0)
    h = int((y1 - y0) * s) + 2 * pad
    img = Image.new("RGB", (px, h), (16, 18, 28))
    dr = ImageDraw.Draw(img)

    def xy(coords):
        return [(pad + (x - x0) * s, h - pad - (y - y0) * s) for x, y in coords]

    for colour, geom in (((150, 170, 205), base), ((228, 238, 252), jewel)):
        for p in parts(geom):
            dr.polygon(xy(p.exterior.coords), fill=colour)
            for r in p.interiors:
                dr.polygon(xy(r.coords), fill=(16, 18, 28))
    print(f"  outline: {x1-x0:.1f} x {y1-y0:.1f} mm, "
          f"{len(parts(whole))} piece(s), {len(stones)} stones")
    img.save(out)
    print(f"  wrote {out}")


if __name__ == "__main__":
    draw(sys.argv[1] if len(sys.argv) > 1 else "preview.png")
