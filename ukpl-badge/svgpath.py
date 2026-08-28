"""Minimal SVG path reader: tokenise, walk the commands, flatten to polylines.

Only what real logo paths use -- M/L/H/V/C/S/Q/T/Z in both cases. Elliptical
arcs (A) raise, loudly, rather than being silently approximated.
"""

import re

import numpy as np

NUMBER = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
COMMAND = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]")

ARGC = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


def _tokenise(d):
    """Split path data into (command, [numbers]) pairs, expanding repeats."""
    out, i = [], 0
    cmd = None
    while i < len(d):
        ch = d[i]
        if ch in " ,\t\r\n":
            i += 1
            continue
        if COMMAND.match(ch):
            cmd = ch
            i += 1
            if cmd in "Zz":
                out.append((cmd, []))
                cmd = None
            continue
        if cmd is None:
            raise ValueError(f"path data starts with a number at {i}")
        n = ARGC[cmd.upper()]
        args = []
        while len(args) < n:
            m = NUMBER.match(d, i)
            if not m:
                raise ValueError(f"expected a number at {i}: {d[i:i+20]!r}")
            args.append(float(m.group()))
            i = m.end()
            while i < len(d) and d[i] in " ,\t\r\n":
                i += 1
        out.append((cmd, args))
        if cmd == "M":            # repeated pairs after a moveto are linetos
            cmd = "L"
        elif cmd == "m":
            cmd = "l"
    return out


def _cubic(p0, p1, p2, p3, tol):
    """Flatten one cubic to a polyline (excluding p0), fine enough for `tol`."""
    p0, p1, p2, p3 = (np.asarray(p, float) for p in (p0, p1, p2, p3))
    chord = np.linalg.norm(p3 - p0)
    net = (np.linalg.norm(p1 - p0) + np.linalg.norm(p2 - p1) + np.linalg.norm(p3 - p2))
    n = int(np.clip(np.ceil(np.sqrt((net + chord) / max(tol, 1e-6)) * 2), 4, 240))
    t = np.linspace(0.0, 1.0, n + 1)[1:, None]
    return ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1
            + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)


def parse(d, tol=0.02):
    """Return the path's subpaths as lists of (x, y) points."""
    subpaths, pts = [], []
    cur = np.zeros(2)
    start = np.zeros(2)
    prev_ctrl = None          # reflection point for S/T
    prev_cmd = ""

    def flush():
        if len(pts) > 2:
            subpaths.append(np.array(pts))

    for cmd, a in _tokenise(d):
        rel = cmd.islower()
        up = cmd.upper()
        if up == "Z":
            if pts:
                pts.append(start.copy())
            flush()
            pts = []
            cur = start.copy()
        elif up == "M":
            flush()
            cur = (cur + a if rel else np.array(a))
            start = cur.copy()
            pts = [cur.copy()]
        elif up in ("L", "H", "V"):
            if up == "L":
                cur = (cur + a if rel else np.array(a))
            elif up == "H":
                cur = np.array([cur[0] + a[0] if rel else a[0], cur[1]])
            else:
                cur = np.array([cur[0], cur[1] + a[0] if rel else a[0]])
            pts.append(cur.copy())
        elif up in ("C", "S"):
            if up == "C":
                c1 = cur + a[0:2] if rel else np.array(a[0:2])
                c2 = cur + a[2:4] if rel else np.array(a[2:4])
                end = cur + a[4:6] if rel else np.array(a[4:6])
            else:
                c1 = 2 * cur - prev_ctrl if prev_cmd in "CcSs" and prev_ctrl is not None else cur
                c2 = cur + a[0:2] if rel else np.array(a[0:2])
                end = cur + a[2:4] if rel else np.array(a[2:4])
            pts.extend(_cubic(cur, c1, c2, end, tol))
            prev_ctrl, cur = c2, end
        elif up in ("Q", "T"):
            if up == "Q":
                q = cur + a[0:2] if rel else np.array(a[0:2])
                end = cur + a[2:4] if rel else np.array(a[2:4])
            else:
                q = 2 * cur - prev_ctrl if prev_cmd in "QqTt" and prev_ctrl is not None else cur
                end = cur + a[0:2] if rel else np.array(a[0:2])
            pts.extend(_cubic(cur, cur + 2 / 3 * (q - cur), end + 2 / 3 * (q - end), end, tol))
            prev_ctrl, cur = q, end
        else:
            raise NotImplementedError(f"path command {cmd!r} is not supported")
        if up not in ("C", "S", "Q", "T"):
            prev_ctrl = None
        prev_cmd = cmd
    flush()
    return subpaths


def signed_area(ring):
    x, y = ring[:, 0], ring[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))
