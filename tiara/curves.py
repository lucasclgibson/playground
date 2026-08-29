"""Curve primitives and strokes, for drawing jewellery-like scrollwork.

Everything ends up as a polyline, then gets stroked into a polygon by chaining
tapered bars -- the convex hull of two circles -- so the narrowest width a design
asks for is a hard floor on its feature size.
"""

import math

import numpy as np
from shapely.geometry import Point
from shapely.ops import unary_union


def bezier(p0, p1, p2, p3, n=72):
    t = np.linspace(0.0, 1.0, n)[:, None]
    p0, p1, p2, p3 = (np.asarray(p, float) for p in (p0, p1, p2, p3))
    return ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1
            + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)


def arc(c, r, a0, a1, n=72):
    a = np.radians(np.linspace(a0, a1, n))
    return np.column_stack([c[0] + r * np.cos(a), c[1] + r * np.sin(a)])


def spiral(c, r0, r1, a0, a1, n=90):
    """Logarithmic-ish curl: radius eases from r0 to r1 as it sweeps."""
    t = np.linspace(0.0, 1.0, n)
    a = np.radians(a0 + (a1 - a0) * t)
    r = r0 * (r1 / r0) ** t
    return np.column_stack([c[0] + r * np.cos(a), c[1] + r * np.sin(a)])


def mirror(pts):
    out = np.array(pts, dtype=float)
    out[:, 0] *= -1
    return out


def stroke(pts, w0, w1=None):
    """Sweep a round pen of width w0 -> w1 along a polyline."""
    w1 = w0 if w1 is None else w1
    pts = np.asarray(pts, dtype=float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    if s[-1] <= 0:
        return Point(pts[0]).buffer(w0 / 2, 24)
    w = w0 + (w1 - w0) * (s / s[-1])
    return unary_union([
        unary_union([Point(pts[i]).buffer(w[i] / 2, 24),
                     Point(pts[i + 1]).buffer(w[i + 1] / 2, 24)]).convex_hull
        for i in range(len(pts) - 1)])


def bead_points(pts, spacing, skip_ends=0.0):
    """Evenly spaced points along a polyline, for setting stones on."""
    pts = np.asarray(pts, dtype=float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    total = s[-1]
    if total <= 2 * skip_ends:
        return np.empty((0, 2))
    lo, hi = skip_ends, total - skip_ends
    n = max(1, int(round((hi - lo) / spacing)))
    want = np.linspace(lo, hi, n + 1)
    return np.column_stack([np.interp(want, s, pts[:, 0]), np.interp(want, s, pts[:, 1])])
