"""The tiara: a fine arched crown over a slim band, on a hair comb.

Coordinates are millimetres in the tiara's own face, origin at the middle of the
band's baseline, +y up. The crown is a lens between two arcs -- a slim base band
and a rim arching over it -- filled with a row of pointed leaves, with a
ball-tipped pin standing in each gap and a small curl at either end.

Everything is drawn as thin smooth strands; the only round forms are the pins'
heads. Strand widths are set here and nothing is narrower than MIN_STRAND, which
is what keeps the piece printable.
"""

import math

import numpy as np
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

from curves import arc, bezier, mirror, spiral, stroke

WIDTH = 95.0              # tip to tip of the band
BASE_RISE = 3.2           # the band's own gentle arch
RIM_RISE = 26.0           # how high the outer rim arcs over it

LEAVES = 5
LEAF_ASPECT = 0.30        # leaf half width as a fraction of its own height
LEAF_HALF_MIN, LEAF_HALF_MAX = 2.4, 5.2
PIN_HEIGHT = 0.62         # how far up its gap a pin stands, as a fraction

MIN_STRAND = 1.6
W_RIM, W_BASE, W_LEAF, W_PIN, W_CURL = 1.8, 2.4, 1.7, 1.6, 1.7
PIN_R = 1.55

TEETH = 9
TOOTH_PITCH = 7.0
TOOTH_LEN = 22.0


def _circle(width, rise):
    """Centre and radius of the arc spanning `width` and rising `rise`."""
    half = width / 2
    r = (half * half) / (2 * rise) + rise / 2
    return rise - r, r


def _arc(width, rise, n=200):
    cy, r = _circle(width, rise)
    span = math.degrees(math.asin(half_of(width) / r))
    return arc((0.0, cy), r, 90 - span, 90 + span, n)


def half_of(width):
    return width / 2


def height_at(x, width, rise):
    """Where the arc sits at x (nan-safe at the tips)."""
    cy, r = _circle(width, rise)
    return cy + math.sqrt(max(r * r - x * x, 0.0))


def base_y(x):
    return height_at(x, WIDTH, BASE_RISE)


def rim_y(x):
    return height_at(x, WIDTH - 2.0, RIM_RISE)


def crown():
    """Strands of the crown, plus the pin heads to be domed as stones."""
    strands, stones = [], []

    strands.append(stroke(_arc(WIDTH - 2.0, RIM_RISE), W_RIM))          # outer rim

    pitch = (WIDTH - 20.0) / LEAVES
    xs = [(i - (LEAVES - 1) / 2) * pitch for i in range(LEAVES)]
    for x in xs:                                                        # pointed leaves
        y0, y1 = base_y(x), rim_y(x)
        h = y1 - y0
        # widen with height, so the short outer leaves stay as slender as the
        # tall middle ones instead of turning into circles
        w = min(max(LEAF_ASPECT * h, LEAF_HALF_MIN), LEAF_HALF_MAX)
        side = bezier((x, y0), (x - w, y0 + 0.30 * h),
                      (x - w, y1 - 0.30 * h), (x, y1))
        strands.append(stroke(side, W_LEAF))
        strands.append(stroke(mirror(side) + np.array([2 * x, 0.0]), W_LEAF))

    for a, b in zip(xs[:-1], xs[1:]):                                   # pins in the gaps
        x = (a + b) / 2
        y0 = base_y(x)
        top = y0 + PIN_HEIGHT * (rim_y(x) - y0)
        strands.append(stroke(np.array([(x, y0), (x, top)]), W_PIN))
        stones.append(((x, top), PIN_R))
    stones.append(((0.0, RIM_RISE + 2.1), 1.9))                         # finial on top
    strands.append(stroke(np.array([(0.0, RIM_RISE - 1.0), (0.0, RIM_RISE + 1.6)]), W_PIN))

    for sgn in (-1.0, 1.0):                                             # curls at the ends
        cx = sgn * 37.0
        c = spiral((cx, base_y(37.0) + 4.9), 4.4, 1.5,
                   -95 - sgn * 5, -95 - sgn * 215, 80)
        strands.append(stroke(c, W_CURL, W_CURL - 0.1))
    return strands, stones


def band():
    """Slim crescent: the arc, plus the sliver down to the comb's straight top."""
    a = _arc(WIDTH, BASE_RISE)
    lune = Polygon(np.vstack([a, [[-WIDTH / 2, 0.0], [WIDTH / 2, 0.0]][::-1]]))
    return unary_union([lune.buffer(0), stroke(a, W_BASE)])


def comb():
    """Spine along the band's underside, and the teeth."""
    parts = [stroke(np.array([(-33.0, -0.5), (33.0, -0.5)]), 2.8)]
    x0 = -TOOTH_PITCH * (TEETH - 1) / 2
    for i in range(TEETH):
        x = x0 + i * TOOTH_PITCH
        parts.append(stroke(np.array([(x, 0.4), (x, -TOOTH_LEN)]), 2.9, 2.2))
    return unary_union(parts)


def build():
    strands, stones = crown()
    jewel = unary_union(strands + [Point(c).buffer(r, 32) for c, r in stones])
    return jewel, band(), comb(), stones
