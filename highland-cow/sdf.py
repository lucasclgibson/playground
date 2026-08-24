"""Tiny signed-distance-field toolkit (numpy, vectorised over point grids).

Every primitive takes three broadcastable coordinate arrays (X, Y, Z) and
returns a float32 field: negative inside the solid, positive outside.
Distance formulas follow the standard analytic derivations popularised by
Inigo Quilez.
"""

import numpy as np

BIG = np.float32(1e5)


# --------------------------------------------------------------- combinators
def smin(a, b, k):
    """Polynomial smooth minimum (smooth union). Exact outside the blend band."""
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b + (a - b) * h - k * h * (1.0 - h)


def smax(a, b, k):
    """Smooth maximum (smooth intersection)."""
    return -smin(-a, -b, k)


def ssubtract(a, b, k):
    """Smoothly remove solid `b` from solid `a`."""
    return smax(a, -b, k)


# ---------------------------------------------------------------- primitives
def sphere(X, Y, Z, c, r):
    dx = X - c[0]
    dy = Y - c[1]
    dz = Z - c[2]
    return np.sqrt(dx * dx + dy * dy + dz * dz) - r


def ellipsoid(X, Y, Z, c, r, rot=None):
    """Scaled-sphere distance bound (exact enough for grid sampling).

    `rot` is the world->local rotation matrix (rows are the local axes).
    """
    dx = X - c[0]
    dy = Y - c[1]
    dz = Z - c[2]
    if rot is not None:
        dx, dy, dz = (
            rot[0, 0] * dx + rot[0, 1] * dy + rot[0, 2] * dz,
            rot[1, 0] * dx + rot[1, 1] * dy + rot[1, 2] * dz,
            rot[2, 0] * dx + rot[2, 1] * dy + rot[2, 2] * dz,
        )
    px, py, pz = dx / r[0], dy / r[1], dz / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    qx, qy, qz = px / r[0], py / r[1], pz / r[2]
    k1 = np.sqrt(qx * qx + qy * qy + qz * qz)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def round_cone(X, Y, Z, a, b, r1, r2):
    """Tapered capsule: sphere r1 at a, sphere r2 at b, plus the tangent hull."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    ba = b - a
    l2 = float(ba @ ba)
    rr = float(r1 - r2)
    a2 = l2 - rr * rr
    il2 = 1.0 / l2

    pax = X - a[0]
    pay = Y - a[1]
    paz = Z - a[2]
    y = pax * ba[0] + pay * ba[1] + paz * ba[2]
    z = y - l2

    cx = pax * l2 - ba[0] * y
    cy = pay * l2 - ba[1] * y
    cz = paz * l2 - ba[2] * y
    x2 = cx * cx + cy * cy + cz * cz
    y2 = y * y * l2
    z2 = z * z * l2

    k = np.sign(rr) * rr * rr * x2
    body = (np.sqrt(np.maximum(x2 * a2 * il2, 0.0)) + y * rr) * il2 - r1
    cap_b = np.sqrt(np.maximum(x2 + z2, 0.0)) * il2 - r2
    cap_a = np.sqrt(np.maximum(x2 + y2, 0.0)) * il2 - r1
    out = np.where(np.sign(z) * a2 * z2 > k, cap_b,
                   np.where(np.sign(y) * a2 * y2 < k, cap_a, body))
    return out


def capsule(X, Y, Z, a, b, r):
    return round_cone(X, Y, Z, a, b, r, r)


def round_box(X, Y, Z, c, b, r, rot=None):
    """Box of half-extents `b` with corner radius `r` (exact SDF)."""
    dx = X - c[0]
    dy = Y - c[1]
    dz = Z - c[2]
    if rot is not None:
        dx, dy, dz = (
            rot[0, 0] * dx + rot[0, 1] * dy + rot[0, 2] * dz,
            rot[1, 0] * dx + rot[1, 1] * dy + rot[1, 2] * dz,
            rot[2, 0] * dx + rot[2, 1] * dy + rot[2, 2] * dz,
        )
    qx = np.abs(dx) - b[0]
    qy = np.abs(dy) - b[1]
    qz = np.abs(dz) - b[2]
    outside = np.sqrt(np.maximum(qx, 0.0) ** 2 + np.maximum(qy, 0.0) ** 2
                      + np.maximum(qz, 0.0) ** 2)
    inside = np.minimum(np.maximum(np.maximum(qx, qy), qz), 0.0)
    return outside + inside - r


def torus(X, Y, Z, c, major, minor, rot=None):
    """Torus with its axis along local +Z."""
    dx = X - c[0]
    dy = Y - c[1]
    dz = Z - c[2]
    if rot is not None:
        dx, dy, dz = (
            rot[0, 0] * dx + rot[0, 1] * dy + rot[0, 2] * dz,
            rot[1, 0] * dx + rot[1, 1] * dy + rot[1, 2] * dz,
            rot[2, 0] * dx + rot[2, 1] * dy + rot[2, 2] * dz,
        )
    q = np.sqrt(dx * dx + dy * dy) - major
    return np.sqrt(q * q + dz * dz) - minor


def ring_on_sphere(X, Y, Z, c, shell, axis, ang, tube):
    """A circle drawn on a sphere of radius `shell` about `c`.

    The circle is the set of shell points whose angle to `axis` equals `ang`;
    `tube` is the frame thickness. Used for the spectacle rims so they follow
    the curve of the face instead of floating off it.
    """
    axis = np.asarray(axis, dtype=np.float64)
    axis = axis / np.linalg.norm(axis)
    dx = X - c[0]
    dy = Y - c[1]
    dz = Z - c[2]
    r = np.sqrt(dx * dx + dy * dy + dz * dz)
    cosa = (dx * axis[0] + dy * axis[1] + dz * axis[2]) / np.maximum(r, 1e-9)
    theta = np.arccos(np.clip(cosa, -1.0, 1.0))
    dr = r - shell
    dt = shell * (theta - ang)
    return np.sqrt(dr * dr + dt * dt) - tube


def plane_z(Z, z0):
    """Half-space Z >= z0 (solid above the plane)."""
    return z0 - Z


# ------------------------------------------------------------------- helpers
def normalize(v):
    v = np.asarray(v, dtype=np.float64)
    return v / np.linalg.norm(v)


def basis_from_axis(axis):
    """Orthonormal world->local rotation whose local +X is `axis`."""
    x = normalize(axis)
    up = np.array([0.0, 0.0, 1.0])
    if abs(x @ up) > 0.95:
        up = np.array([0.0, 1.0, 0.0])
    y = normalize(np.cross(up, x))
    z = np.cross(x, y)
    return np.stack([x, y, z])
