"""The tiara: a beaded scrollwork crown over a crescent band, on a hair comb.

Coordinates are millimetres in the tiara's own face, origin at the middle of the
band's baseline, +y up. Everything is drawn once for the right-hand side and
mirrored, so the piece is symmetric by construction.
"""

import math

import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

from curves import arc, bead_points, bezier, mirror, spiral, stroke

WIDTH = 90.0              # tip to tip of the band
BAND_RISE = 7.5           # how far the crescent arcs above its baseline
TEETH = 9
TOOTH_PITCH = 7.0
TOOTH_LEN = 23.0

BEAD_R = 1.65             # the "stones" set along every strand
BEAD_PITCH = 4.2


def band_arc():
    """Circular arc through (-W/2, 0) and (W/2, 0), rising BAND_RISE in the middle."""
    half = WIDTH / 2
    r = (half * half) / (2 * BAND_RISE) + BAND_RISE / 2
    cy = BAND_RISE - r
    span = math.degrees(math.asin(half / r))
    return arc((0.0, cy), r, 90 - span, 90 + span, 160)


def scroll_curves():
    """Every strand of the crown, right-hand side plus the centre pieces."""
    heart = [
        bezier((-1.2, 7.5), (-7, 13), (-19.5, 29), (-16, 41)),    # up to the left lobe
        bezier((-16, 41), (-12.5, 47), (-4, 45), (0, 36)),        # over it, into the dip
    ]
    loop = [
        bezier((11, 7.5), (26, 9), (37.5, 21), (33, 33)),         # sweep out and up
        bezier((33, 33), (29.5, 41.5), (18, 38.5), (15.5, 27.5)),  # curl back onto the heart
    ]
    curl = [
        bezier((34, 5.5), (43, 6.5), (48.5, 13), (45.3, 20.6)),   # rise at the end
        spiral((41.5, 18.8), 4.2, 1.4, 25, -230, 90),             # and curl inward
    ]
    stem = [np.array([(0.0, 35.0), (0.0, 44.0)])]                 # crown stem
    drop = [np.array([(0.0, 36.0), (0.0, 29.0)])]                 # pendant
    return heart, loop, curl, stem, drop


def crown():
    """The scrollwork above the band: strands, then stones set along them."""
    heart, loop, curl, stem, drop = scroll_curves()
    strands, stones = [], []

    def add(pts, w0, w1, bead=BEAD_R, pitch=BEAD_PITCH, mirrored=True, skip=1.2):
        for p in ([pts, mirror(pts)] if mirrored else [pts]):
            strands.append(stroke(p, w0, w1))
            if bead:
                stones.extend((tuple(q), bead) for q in bead_points(p, pitch, skip))

    for seg in heart:
        add(seg, 2.6, 2.2)
    for seg in loop:
        add(seg, 2.4, 2.0)
    for seg in curl:
        add(seg, 2.2, 1.8)
    add(stem[0], 2.0, 1.8, bead=None, mirrored=False)
    add(drop[0], 1.7, 1.5, bead=None, mirrored=False)

    stones += [((0.0, 46.0), 2.7),                    # stone crowning the stem
               ((-3.8, 42.4), 1.9), ((3.8, 42.4), 1.9),
               ((0.0, 26.6), 3.0)]                    # the drop
    return strands, stones


def band():
    """The crescent: arc on top, straight underside for the comb to hang from."""
    a = band_arc()
    lune = Polygon(np.vstack([a, [[-WIDTH / 2, 0.0], [WIDTH / 2, 0.0]][::-1]]))
    return unary_union([lune.buffer(0), stroke(a, 2.8)])   # stroke keeps the tips solid


def comb():
    """Spine along the band's underside, and the teeth."""
    parts = [stroke(np.array([(-33.0, -0.2), (33.0, -0.2)]), 3.4)]
    x0 = -TOOTH_PITCH * (TEETH - 1) / 2
    for i in range(TEETH):
        x = x0 + i * TOOTH_PITCH
        parts.append(stroke(np.array([(x, 0.5), (x, -TOOTH_LEN)]), 2.9, 2.2))
    return unary_union(parts)


def build():
    strands, stones = crown()
    jewel = unary_union(strands + [Point(c).buffer(r, 32) for c, r in stones])
    return jewel, band(), comb(), stones
