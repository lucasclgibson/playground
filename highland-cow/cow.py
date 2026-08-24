"""The highland cow: a signed-distance field assembled from smooth blobs.

Axes:  +X = the cow's left, +Y = the direction it faces, +Z = up.
Units are millimetres in "design space"; the mesher rescales the finished
model so the printed height comes out at exactly TARGET_HEIGHT_MM.

The parts are sorted into five groups so the shaggy displacement only touches
the coat, and the horns, snout, eyes and spectacles stay crisp:

    body    barrel, legs, head, cheeks, ears, tail   -- blended broadly
    locks   fringe, topknot, the skirt round the barrel -- blended tightly,
            so each lock keeps its own edge; grooved by fur_grooves()
    smooth  snout, horns, hooves, eyeballs
    glass   spectacle rims, bridge, temple arms
    cut     nostrils, mouth, philtrum, pupils, hoof clefts  (subtracted)
"""

import numpy as np

import sdf
from sdf import (basis_from_axis, ellipsoid, normalize, ring_on_sphere,
                 round_box, round_cone, smin, sphere)

TARGET_HEIGHT_MM = 110.0

# --------------------------------------------------------------- proportions
# Chibi silhouette: head ~ half the total height, barrel body, stubby legs.
BODY_C, BODY_R = (0.0, -4.0, 42.0), (26.0, 28.0, 22.0)
HEAD_C, HEAD_R = (0.0, 15.0, 80.0), 24.5   # the skull; the coat builds it out to ~29
NOSE_FRONT = 39.6         # the nose pad is clipped flat at this Y

LEGS = [(14.0, 14.0), (-14.0, 14.0), (15.0, -17.0), (-15.0, -17.0)]
LEG_TOP_Z, LEG_TOP_R = 30.0, 10.0
HOOF_Z, HOOF_R = 3.5, 9.0

GLASS_SHELL = 26.6        # frames stand ~4.6 mm proud of the skull
GLASS_TUBE = 2.5          # -> 5 mm thick frames before the final rescale
GLASS_ANG = 0.36          # angular radius of a lens ~ 10 mm
GLASS_AXIS = (0.44, 1.0, -0.13)

K_MAIN = 6.0              # blend radius for the underlying body masses
K_LOCK = 1.8              # locks keep their own edges instead of melting together
K_COAT = 2.6              # ... then the coat merges onto the body
K_ADD = 3.0               # blend for muzzle / horns onto the fur
K_GLASS = 0.9             # spectacles stay crisp but still weld to the face
K_CUT = 0.7
MARGIN = K_MAIN + 2.0     # slab culling safety band

FUR_AMP = 1.2             # groove depth (mm)
FUR_N = 23                # locks around the circumference


# ------------------------------------------------------------------ assembly
class Group:
    """A smooth union of parts, each tagged with its Z extent for slab culling."""

    def __init__(self, k):
        self.k = k
        self.items = []

    def add(self, fn, zmin, zmax):
        self.items.append((zmin, zmax, fn))
        return self

    def add_sphere(self, c, r):
        return self.add(lambda X, Y, Z: sphere(X, Y, Z, c, r), c[2] - r, c[2] + r)

    def add_ellipsoid(self, c, r, rot=None):
        rad = max(r) if rot is not None else r[2]
        return self.add(lambda X, Y, Z: ellipsoid(X, Y, Z, c, r, rot),
                        c[2] - rad, c[2] + rad)

    def add_cone(self, a, b, r1, r2):
        return self.add(lambda X, Y, Z: round_cone(X, Y, Z, a, b, r1, r2),
                        min(a[2] - r1, b[2] - r2), max(a[2] + r1, b[2] + r2))

    def add_capsule(self, a, b, r):
        return self.add_cone(a, b, r, r)

    def eval(self, X, Y, Z, z0, z1):
        out = None
        for zmin, zmax, fn in self.items:
            if zmax < z0 - MARGIN or zmin > z1 + MARGIN:
                continue
            v = fn(X, Y, Z)
            out = v if out is None else smin(out, v, self.k)
        return out


def _shell_point(centre, radius, azim, elev):
    """Point on a sphere: azimuth measured from +Y toward +X, elevation from the equator."""
    ce = np.cos(elev)
    return np.array([centre[0] + radius * ce * np.sin(azim),
                     centre[1] + radius * ce * np.cos(azim),
                     centre[2] + radius * np.sin(elev)])


def _bezier(p0, p1, p2, t):
    p0, p1, p2 = map(np.asarray, (p0, p1, p2))
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2


def _lock(group, azim, elev0, elev1, r0, r1, shell, segs=3, bow=1.5):
    """One shaggy lock combed along the head, arcing slightly off the surface."""
    for s in range(segs):
        t0, t1 = s / segs, (s + 1) / segs
        pts = []
        for t in (t0, t1):
            e = elev0 + (elev1 - elev0) * t
            pts.append(_shell_point(HEAD_C, shell + bow * t, azim, e))
        group.add_cone(tuple(pts[0]), tuple(pts[1]),
                       r0 + (r1 - r0) * t0, r0 + (r1 - r0) * t1)


def _surface_y(x, z, y_lo=20.0, y_hi=60.0):
    """Y where the snout surface crosses the ray (x, *, z) -- found by bisection.

    Carved details (nostrils, mouth) are positioned from this so they always cut
    to a real depth, however the snout is retuned.
    """
    ax = np.array([float(x)])
    az = np.array([float(z)])
    for _ in range(40):
        mid = 0.5 * (y_lo + y_hi)
        if muzzle(ax, np.array([mid]), az)[0] < 0.0:
            y_lo = mid
        else:
            y_hi = mid
    return 0.5 * (y_lo + y_hi)


def _rim_gap(p, r):
    """Clearance between a lock of radius `r` at point `p` and the nearest rim.

    Negative means the two solids genuinely overlap (fine -- they weld); a small
    positive value is the dangerous case, leaving a hairline slot that a slicer
    cannot resolve and a decimator will pinch shut.
    """
    px, py, pz = (np.array([p[0]]), np.array([p[1]]), np.array([p[2]]))
    gaps = []
    for sgn in (-1.0, 1.0):
        axis = normalize((sgn * GLASS_AXIS[0], GLASS_AXIS[1], GLASS_AXIS[2]))
        gaps.append(ring_on_sphere(px, py, pz, HEAD_C, GLASS_SHELL, axis,
                                   GLASS_ANG, GLASS_TUBE)[0] - r)
    return min(gaps)


def _clear_elev(azim, elev_start, elev_end, r_tip, shell, bow):
    """Raise a lock's end until it either clears the frames or overlaps them."""
    for _ in range(14):
        risky = False
        for t in (0.7, 0.85, 1.0):
            e = elev_start + (elev_end - elev_start) * t
            q = _shell_point(HEAD_C, shell + bow * t, azim, e)
            if -0.6 < _rim_gap(q, r_tip) < 1.8:
                risky = True
                break
        if not risky:
            return elev_end
        elev_end += np.radians(2.0)
    return elev_end


def build(base=False):
    rng = np.random.default_rng(20260824)
    body, locks = Group(K_MAIN), Group(K_LOCK)
    smooth, glass, cut = Group(K_ADD), Group(K_GLASS), Group(K_CUT)

    # ---- barrel body, stubby legs, big round head ------------------------
    body.add_ellipsoid(BODY_C, BODY_R)
    body.add_ellipsoid((0.0, 8.0, 52.0), (23.0, 20.0, 18.0))       # chest / shoulders
    for x, y in LEGS:
        body.add_cone((x, y, HOOF_Z), (x * 0.8, y * 0.75, LEG_TOP_Z), 9.0, LEG_TOP_R)
    body.add_sphere(HEAD_C, HEAD_R)

    # ---- the coat: locks combed down all round the head ------------------
    # A lens spans roughly 3..50 deg of azimuth and reaches 14 deg of elevation,
    # so locks over the brow stop just above the frames; everywhere else they
    # hang past the cheeks and down the neck.
    n = 26
    for i in range(n):
        azim = -np.pi + 2.0 * np.pi * (i + 0.5) / n
        deg = abs(np.degrees(azim))
        if deg < 9.0:                       # tuft down between the lenses
            elev_end = 13.0
        elif deg < 50.0:                    # brow, kept clear of the frames
            elev_end = 19.0
        elif deg < 74.0:                    # side locks framing the face
            elev_end = 19.0 - 53.0 * (deg - 50.0) / 24.0
        else:                               # cheeks and shaggy neck
            elev_end = -34.0
        elev_end += rng.uniform(-3.5, 3.5)
        r_tip = 3.1 + rng.uniform(-0.4, 0.7)
        e0 = np.radians(63.0 + rng.uniform(-6.0, 6.0))
        e1 = _clear_elev(azim, e0, np.radians(elev_end), r_tip, HEAD_R - 0.5, 4.8)
        _lock(locks, azim, e0, e1, 4.7 + rng.uniform(-0.4, 0.5), r_tip,
              HEAD_R - 0.5, bow=4.8)
        if i % 2 == 0:                      # a shorter staggered layer for depth
            a2 = azim + np.pi / n
            e2 = _clear_elev(a2, np.radians(70.0),
                             np.radians(max(elev_end + 22.0, 30.0)), 3.4,
                             HEAD_R - 1.5, 4.2)
            _lock(locks, a2, np.radians(70.0), e2, 4.4, 3.4,
                  HEAD_R - 1.5, segs=2, bow=4.2)

    # ---- topknot between the horns ---------------------------------------
    for i in range(7):
        u = (i - 3) / 3.0
        a = _shell_point(HEAD_C, HEAD_R - 2.0, u * 0.85, np.radians(62.0))
        b = _shell_point(HEAD_C, HEAD_R + 5.5, u * 0.95, np.radians(86.0 - 7.0 * abs(u)))
        b[1] += 4.0
        locks.add_cone(tuple(a), tuple(b), 5.0, 3.0 + rng.uniform(-0.3, 0.4))

    # ---- cheek fluff and a shaggy chest ----------------------------------
    for sgn in (-1.0, 1.0):
        body.add_ellipsoid((sgn * 17.0, 20.0, 60.0), (10.0, 9.5, 8.5))
    body.add_ellipsoid((0.0, 20.0, 48.0), (16.0, 12.0, 12.0))      # brisket
    # A skirt of long hair round the barrel: the axes hug the body so each lock
    # is surface relief (2-3 mm proud) rather than a stuck-on sausage.
    m = 18
    for i in range(m):
        phi = 2.0 * np.pi * (i + 0.5) / m
        d = np.array([np.sin(phi) * BODY_R[0], np.cos(phi) * BODY_R[1], 0.0])
        top = np.array([BODY_C[0], BODY_C[1], 0.0]) + 0.90 * d + [0, 0, 48.0]
        bot = np.array([BODY_C[0], BODY_C[1], 0.0]) + 1.00 * d + [0, 0, 33.0]
        bot[2] += 3.0 * abs(np.cos(phi)) + rng.uniform(-2.5, 3.5)
        locks.add_cone(tuple(top), tuple(bot),
                       3.6 + rng.uniform(-0.4, 0.4), 2.6 + rng.uniform(-0.4, 0.5))
    for i in range(m):                                   # a second, upper row
        phi = 2.0 * np.pi * i / m
        d = np.array([np.sin(phi) * BODY_R[0], np.cos(phi) * BODY_R[1], 0.0])
        top = np.array([BODY_C[0], BODY_C[1], 0.0]) + 0.82 * d + [0, 0, 60.0]
        bot = np.array([BODY_C[0], BODY_C[1], 0.0]) + 0.99 * d + [0, 0, 46.0]
        bot[2] += rng.uniform(-2.5, 3.0)
        locks.add_cone(tuple(top), tuple(bot),
                       3.4 + rng.uniform(-0.4, 0.4), 2.6 + rng.uniform(-0.4, 0.5))

    # ---- ears, tucked under the horns ------------------------------------
    for sgn in (-1.0, 1.0):
        axis = normalize((sgn * 0.90, -0.26, -0.35))
        c = np.array(HEAD_C) + np.array([sgn * 22.0, -1.0, -7.0])
        body.add_ellipsoid(tuple(c + axis * 7.0), (9.5, 7.0, 4.0), basis_from_axis(axis))

    # ---- tail, laid against the rump so it needs no support --------------
    tail = [(0.0, -28.0, 58.0), (0.0, -36.0, 47.0), (0.0, -37.5, 39.0)]
    for a, b, r0, r1 in zip(tail[:-1], tail[1:], (3.2, 2.6), (2.6, 2.2)):
        body.add_cone(a, b, r0, r1)
    body.add_sphere((0.0, -37.5, 34.5), 5.2)

    # ---- snout, hooves, horns, eyes: kept out of the fur displacement ----
    smooth.add(muzzle, 42.0, 76.0)                                   # snout + jaw
    for x, y in LEGS:
        smooth.add_cone((x, y, 0.5), (x, y, 8.0), HOOF_R, 8.2)

    for sgn in (-1.0, 1.0):
        p0 = np.array([sgn * 18.0, 13.0, 89.0])
        p1 = np.array([sgn * 36.0, 15.0, 95.0])
        p2 = np.array([sgn * 43.0, 25.0, 110.0])
        steps = 11
        pts = [_bezier(p0, p1, p2, t) for t in np.linspace(0, 1, steps + 1)]
        rad = np.linspace(7.4, 2.6, steps + 1) ** 1.0
        for j in range(steps):
            smooth.add_cone(tuple(pts[j]), tuple(pts[j + 1]), float(rad[j]), float(rad[j + 1]))

    eye_axes = []
    for sgn in (-1.0, 1.0):
        axis = normalize((sgn * GLASS_AXIS[0], GLASS_AXIS[1], GLASS_AXIS[2]))
        eye_axes.append(axis)
        smooth.add_ellipsoid(tuple(np.array(HEAD_C) + axis * 23.4), (3.4, 5.1, 5.1),
                             basis_from_axis(axis))

    # ---- spectacles -------------------------------------------------------
    for axis in eye_axes:
        glass.add(lambda X, Y, Z, a=axis: ring_on_sphere(
            X, Y, Z, HEAD_C, GLASS_SHELL, a, GLASS_ANG, GLASS_TUBE),
            HEAD_C[2] - (GLASS_SHELL + GLASS_TUBE), HEAD_C[2] + GLASS_SHELL + GLASS_TUBE)

    def rim_point(axis, phi, shell=GLASS_SHELL):
        """Point on a lens rim; phi=0 is the outer edge, phi=pi the nose side."""
        a = normalize(axis)
        u = np.array([1.0, 0.0, 0.0]) * np.sign(a[0])
        u = normalize(u - (u @ a) * a)
        v = np.cross(a, u)
        d = (np.cos(GLASS_ANG) * a
             + np.sin(GLASS_ANG) * (np.cos(phi) * u + np.sin(phi) * v))
        return np.array(HEAD_C) + shell * d

    bridge = [rim_point(a, np.pi) for a in eye_axes]
    glass.add_capsule(tuple(bridge[0] + [0, 0.5, 0]), tuple(bridge[1] + [0, 0.5, 0]), 2.0)

    for axis in eye_axes:                                   # temple arms
        sgn = np.sign(axis[0])
        start = rim_point(axis, 0.0)
        d0 = normalize(start - np.array(HEAD_C))
        d1 = normalize((sgn * 1.0, -0.62, 0.12))
        prev, prev_r = start, 2.0
        for s in (0.45, 1.0):
            d = normalize(d0 * (1 - s) + d1 * s)
            shell = GLASS_SHELL * (1 - s) + 25.2 * s
            p = np.array(HEAD_C) + d * shell
            glass.add_cone(tuple(prev), tuple(p), prev_r, 1.9)
            prev, prev_r = p, 1.9

    # ---- carved details ---------------------------------------------------
    for sgn in (-1.0, 1.0):                                                   # nostrils
        nx, nz = sgn * 4.6, 60.6
        cut.add_ellipsoid((nx, _surface_y(nx, nz) + 0.7, nz), (2.5, 2.9, 2.0))
    smile = []                                                                # smile
    for t in np.linspace(-1.0, 1.0, 9):
        x, z = 8.2 * t, 51.8 + 3.4 * t * t
        smile.append((x, _surface_y(x, z) + 0.35, z))
    for a, b in zip(smile[:-1], smile[1:]):
        cut.add_capsule(a, b, 1.6)
    px, pz = 0.0, 55.4                                                        # philtrum
    cut.add_capsule((px, _surface_y(px, pz) + 0.5, pz),
                    (px, _surface_y(px, 58.6) + 0.5, 58.6), 1.0)
    for axis in eye_axes:                                                     # pupils
        cut.add_sphere(tuple(np.array(HEAD_C) + axis * 28.0), 3.0)
    for x, y in LEGS:                                                         # hoof cleft
        cut.add_capsule((x, y + 7.6, -1.0), (x, y + 8.4, 6.5), 1.3)

    if base:                                 # optional plinth, PLINTH_MM below the hooves
        smooth.add(lambda X, Y, Z: round_box(X, Y, Z, (0.0, -1.5, -1.6),
                                             (19.0, 21.0, 0.0), 2.6), -5.0, 1.5)
    return body, locks, smooth, glass, cut


def muzzle(X, Y, Z):
    """Snout: bridge of the nose, broad nose pad and jaw, planed flat in front."""
    m = ellipsoid(X, Y, Z, (0.0, 23.0, 66.5), (9.5, 8.5, 8.0))        # bridge
    m = smin(m, ellipsoid(X, Y, Z, (0.0, 31.5, 58.5), (10.8, 7.8, 6.6)), 4.5)   # pad
    m = smin(m, ellipsoid(X, Y, Z, (0.0, 28.5, 52.0), (9.5, 7.5, 5.5)), 4.5)    # jaw
    return sdf.smax(m, Y - NOSE_FRONT, 2.0)


# ------------------------------------------------------------ fur "shagginess"
def rim_distance(X, Y, Z):
    """Distance to the nearer spectacle rim (negative inside the frame)."""
    d = None
    for sgn in (-1.0, 1.0):
        axis = normalize((sgn * GLASS_AXIS[0], GLASS_AXIS[1], GLASS_AXIS[2]))
        v = ring_on_sphere(X, Y, Z, HEAD_C, GLASS_SHELL, axis, GLASS_ANG, GLASS_TUBE)
        d = v if d is None else np.minimum(d, v)
    return d


def fur_grooves(X, Y, Z, near_glasses=False):
    """Vertical grooves that break the coat into wavy locks (positive = carve in)."""
    theta = np.arctan2(X, Y - 6.0)
    warp = theta * FUR_N + 0.22 * Z + 1.6 * np.sin(0.11 * Z + 3.0 * theta)
    lock = 0.5 - 0.5 * np.cos(warp)
    amp = FUR_AMP * (0.62 + 0.38 * np.sin(0.19 * Z + 5.0 * theta))
    radial = np.sqrt(X * X + (Y - 6.0) ** 2)
    amp = amp * np.clip((radial - 6.0) / 8.0, 0.0, 1.0)
    if near_glasses:
        amp = amp * np.clip(rim_distance(X, Y, Z) / 3.5, 0.0, 1.0)
    return amp * (np.sqrt(lock + 0.02) - 0.1414)


def field(X, Y, Z, groups, z0, z1, floor=0.0):
    """Evaluate the whole cow over one slab of the sampling grid."""
    body, locks, smooth, glass, cut = groups
    f = body.eval(X, Y, Z, z0, z1)
    lk = locks.eval(X, Y, Z, z0, z1)
    if lk is not None:
        f = lk if f is None else smin(f, lk, K_COAT)
    if f is not None:
        near = (z1 > HEAD_C[2] - GLASS_SHELL - 8.0
                and z0 < HEAD_C[2] + GLASS_SHELL + 8.0)
        f = f + fur_grooves(X, Y, Z, near_glasses=near)
    s = smooth.eval(X, Y, Z, z0, z1)
    if s is not None:
        f = s if f is None else smin(f, s, K_ADD)
    if f is None:
        return np.full(np.broadcast(X, Y, Z).shape, sdf.BIG, dtype=np.float32)

    g = glass.eval(X, Y, Z, z0, z1)
    if g is not None:
        f = smin(f, g, K_GLASS)

    c = cut.eval(X, Y, Z, z0, z1)
    if c is not None:
        f = sdf.ssubtract(f, c, K_CUT)

    return np.maximum(f, sdf.plane_z(Z, floor + 1e-3))   # flat, printable feet


PLINTH_MM = 3.0           # thickness of the optional --base plinth
BOUNDS = ((-50.0, 50.0), (-44.0, 54.0), (-7.0, 122.0))
