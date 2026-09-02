"""Turn the rings of an SVG path into shapely geometry, honouring winding.

SVG fills with the non-zero rule by default: a ring is a hole only when it winds
against the ring enclosing it. Working that out from the containment tree (rather
than assuming "second subpath = hole") is what keeps the tag's eyelet a hole and
the roof chevron a solid.
"""

import re
import xml.etree.ElementTree as ET

import shapely

from shapely.geometry import Polygon
from shapely.ops import unary_union

import svgpath


def paths_from_svg(path):
    """Every path's `d` attribute in document order."""
    root = ET.parse(path).getroot()
    ds = [el.get("d") for el in root.iter() if el.tag.endswith("path") and el.get("d")]
    if not ds:
        raise ValueError(f"no <path d=...> found in {path}")
    return ds


def rings_to_polygon(rings):
    """Combine rings into one (multi)polygon using the SVG non-zero fill rule."""
    polys = [Polygon(r).buffer(0) for r in rings]         # buffer(0) repairs slivers
    orient = [1 if svgpath.signed_area(r) > 0 else -1 for r in rings]
    n = len(rings)

    parents = [[j for j in range(n) if j != i and polys[j].contains(polys[i])]
               for i in range(n)]
    depth = [len(p) for p in parents]

    outers, holes = {}, {}
    for i in range(n):
        outside = sum(orient[j] for j in parents[i])      # winding just outside ring i
        inside = outside + orient[i]                      # ... and just inside it
        if outside == 0 and inside != 0:
            outers.setdefault(depth[i], []).append(polys[i])
        elif outside != 0 and inside == 0:
            holes.setdefault(depth[i], []).append(polys[i])

    result = Polygon()
    for d in sorted(set(list(outers) + list(holes))):     # shallowest rings first
        if d in outers:
            result = result.union(unary_union(outers[d]))
        if d in holes:
            result = result.difference(unary_union(holes[d]))
    if result.is_empty:
        raise ValueError("the path encloses no filled area")
    return result


def load(svg_file, tol=0.02):
    """Filled area of an SVG, as shapely geometry in SVG (y-down) coordinates."""
    rings = []
    for d in paths_from_svg(svg_file):
        rings.extend(svgpath.parse(d, tol=tol))
    return rings_to_polygon(rings), rings


def thin_area_fraction(poly, min_wall):
    """Fraction of the area sitting in features narrower than `min_wall`.

    A morphological opening: anything that does not survive being eroded by half
    the minimum wall and grown back is too thin to print reliably.
    """
    opened = poly.buffer(-min_wall / 2, quad_segs=32).buffer(min_wall / 2, quad_segs=32)
    return max(0.0, (poly.area - poly.intersection(opened).area) / poly.area)


def merge_radius(polys):
    """Smallest buffer radius that fuses a set of polygons into one piece.

    Bottleneck of the minimum spanning tree over pairwise gaps: buffering by
    half the widest gap you must cross is exactly what connects everything.
    """
    n = len(polys)
    if n < 2:
        return 0.0
    edges = sorted((polys[i].distance(polys[j]), i, j)
                   for i in range(n) for j in range(i + 1, n))
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    widest, joined = 0.0, 0
    for d, i, j in edges:
        a, b = find(i), find(j)
        if a != b:
            parent[a] = b
            widest = max(widest, d)
            joined += 1
            if joined == n - 1:
                break
    return widest / 2


def bridge_web(poly, reach):
    """The membrane that bridges a mark's shadow gap, and nothing else.

    A morphological closing fills any gap narrower than 2*reach and leaves the
    outline alone everywhere else, so the silhouette is untouched. Holes are put
    back afterwards -- otherwise the closing would seal the tag's eyelet.
    """
    if reach <= 0:
        return None
    closed = poly.buffer(reach, quad_segs=32).buffer(-reach, quad_segs=32)
    holes = unary_union([Polygon(r) for g in (poly.geoms if hasattr(poly, "geoms")
                                              else [poly]) for r in g.interiors])
    if not holes.is_empty:
        closed = closed.difference(holes)
    # Buffering leaves near-duplicate and collinear points that the ear-clipping
    # triangulator quietly chokes on, so the extrusion comes out with holes in
    # it. Snapping alone does not clear them at tighter reaches -- the simplify
    # is what drops the collinear runs -- so do both.
    closed = shapely.set_precision(closed.simplify(0.01).buffer(0), 1e-3)
    return None if closed.is_empty else closed
