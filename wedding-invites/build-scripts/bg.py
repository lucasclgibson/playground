"""Background builder: cleaned + upscaled artwork -> 400 dpi bleed-size rasters."""
import os, numpy as np, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

DPI = 400
PXMM = DPI / 25.4
BLEED = 3.0
TRIM_W, TRIM_H = 210.0, 297.0
OUT_W = int(round((TRIM_W + 2 * BLEED) * PXMM))
OUT_H = int(round((TRIM_H + 2 * BLEED) * PXMM))
HERE = os.path.dirname(os.path.abspath(__file__))

# ---- page-1 mapping (source px -> trim mm) -------------------------------
# day: full-bleed art, centred on the building; evening: art inside a 6 mm framed border
P1 = {
    'day':     dict(cx=727.0, top=36.0, s=0.1595, frame=None, card=(29, 27, 1383, 2006)),
    'evening': dict(cx=792.0, top=26.0, s=285.0 / 1995.0, frame=6.0, card=(39, 25, 1499, 2022)),
}
NOTCH = 4.0  # mm, concave corner radius on frames

# ---- page-2 floral crops (source px boxes) and placement (trim mm) ---------
CROPS = {
    'day': dict(rsvp_top=(1470, 195, 2140, 560), rsvp_bot=(1420, 1530, 2160, 1972),
                det_top=(2560, 178, 3003, 735), det_bot=(2240, 1370, 3003, 1972)),
    'evening': dict(rsvp_top=(1590, 210, 2200, 560), rsvp_bot=(1557, 1510, 2228, 1972),
                    det_top=(2570, 182, 3018, 735), det_bot=(2310, 1350, 3018, 1972)),
}


def load(n):
    up = f'{HERE}/up/{n}_x4.png'
    clean = np.asarray(Image.open(f'{HERE}/clean/{n}_clean.png').convert('RGB'))
    mask = cv2.imread(f'{HERE}/clean/{n}_mask.png', 0) > 0
    if os.path.exists(up):
        big = np.asarray(Image.open(up).convert('RGB'))
    else:  # placeholder while the AI upscale is still running
        big = cv2.resize(clean, None, fx=4, fy=4, interpolation=cv2.INTER_LANCZOS4)
    return clean, mask, big


def art_mask(clean, textmask):
    """Pixels that are artwork (not paper) at source resolution."""
    f = clean.astype(np.float32)
    w = (~textmask).astype(np.float32)
    est = cv2.GaussianBlur(f * w[..., None], (0, 0), 25) / np.maximum(cv2.GaussianBlur(w, (0, 0), 25), 1e-4)[..., None]
    dev = np.abs(f - est).max(2)
    art = (dev > 11) & ~textmask
    art = cv2.morphologyEx(art.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    # drop isolated specks (stray remnants), keep real artwork
    k, lab, st, _ = cv2.connectedComponentsWithStats(art, 8)
    keep = np.zeros(k, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] >= 40
    return keep[lab]


def paper_colour(clean, textmask, art):
    sel = ~textmask & ~cv2.dilate(art.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    return np.median(clean[sel], 0).astype(np.float32)


def grain(h, w, seed):
    rng = np.random.default_rng(seed)
    fine = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 0.8)
    fine /= fine.std()
    low = cv2.GaussianBlur(rng.normal(0, 1, (h // 8, w // 8)).astype(np.float32), (0, 0), 6)
    low = cv2.resize(low / low.std(), (w, h), interpolation=cv2.INTER_CUBIC)
    return fine * 1.6 + low * 0.45


def sample(img, x0, y0, x1, y1, ow, oh, scale=1):
    """Crop source-px box (may exceed image; reflected) from img at given scale, resize to ow x oh."""
    X0, Y0, X1, Y1 = [int(round(v * scale)) for v in (x0, y0, x1, y1)]
    H, W = img.shape[:2]
    pl, pt, pr, pb = max(0, -X0), max(0, -Y0), max(0, X1 - W), max(0, Y1 - H)
    crop = img[max(Y0, 0):min(Y1, H), max(X0, 0):min(X1, W)]
    if pl or pt or pr or pb:
        crop = cv2.copyMakeBorder(crop, pt, pb, pl, pr, cv2.BORDER_REFLECT)
    interp = cv2.INTER_AREA if crop.shape[1] > ow else cv2.INTER_CUBIC
    return cv2.resize(crop, (ow, oh), interpolation=interp)


def notched_mask(w, h, x0, y0, x1, y1, r):
    """Raster mask (bleed px) of a rectangle with concave quarter-circle corners (trim mm args)."""
    m = np.zeros((h, w), np.uint8)
    P = lambda v: int(round((v + BLEED) * PXMM))
    cv2.rectangle(m, (P(x0), P(y0)), (P(x1), P(y1)), 1, -1)
    rr = int(round(r * PXMM))
    for cx, cy in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
        cv2.circle(m, (P(cx), P(cy)), rr, 0, -1)
    return m


def page1(n):
    clean, tmask, big = load(n)
    p = P1[n]
    s = p['s']
    art = art_mask(clean, tmask)
    paper = paper_colour(clean, tmask, art)

    # replace everything around the removed lettering with smooth paper (kills emboss/halo ghosts)
    R = cv2.dilate(tmask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))) > 0
    R &= ~cv2.dilate(art.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
    keep = (~R & ~art).astype(np.float32)
    f = clean.astype(np.float32)
    fill = cv2.GaussianBlur(f * keep[..., None], (0, 0), 30) / np.maximum(cv2.GaussianBlur(keep, (0, 0), 30), 1e-4)[..., None]
    alpha = cv2.GaussianBlur(R.astype(np.float32), (0, 0), 3)
    alpha = np.minimum(alpha, 1 - cv2.GaussianBlur(art.astype(np.float32), (0, 0), 1.5))

    if p['frame'] is None:
        x0 = p['cx'] - (TRIM_W / 2 + BLEED) / s
        y0 = p['top']
        box = (x0, y0, x0 + (TRIM_W + 2 * BLEED) / s, y0 + (TRIM_H + 2 * BLEED) / s)
        out_w, out_h, off = OUT_W, OUT_H, (0, 0)
    else:
        fr = p['frame']
        iw, ih = TRIM_W - 2 * fr, TRIM_H - 2 * fr
        x0 = p['cx'] - (iw / 2) / s
        box = (x0, p['top'], x0 + iw / s, p['top'] + ih / s)
        out_w, out_h = int(round(iw * PXMM)), int(round(ih * PXMM))
        off = (int(round((fr + BLEED) * PXMM)), int(round((fr + BLEED) * PXMM)))

    cx0, cy0, cx1, cy1 = p['card']
    box = (box[0] - cx0, box[1] - cy0, box[2] - cx0, box[3] - cy0)
    big_c = big[cy0 * 4:cy1 * 4, cx0 * 4:cx1 * 4]
    art_rgb = sample(big_c, *box, out_w, out_h, scale=4).astype(np.float32)
    fill_o = sample(fill[cy0:cy1, cx0:cx1], *box, out_w, out_h)
    a_o = sample(alpha[cy0:cy1, cx0:cx1], *box, out_w, out_h)[..., None]
    art_rgb = art_rgb * (1 - a_o) + fill_o * a_o

    canvas = np.empty((OUT_H, OUT_W, 3), np.float32)
    canvas[:] = paper
    if p['frame'] is None:
        canvas = art_rgb
    else:
        ox, oy = off
        region = canvas[oy:oy + out_h, ox:ox + out_w]
        fr = p['frame']
        m = notched_mask(OUT_W, OUT_H, fr, fr, TRIM_W - fr, TRIM_H - fr, NOTCH)[oy:oy + out_h, ox:ox + out_w]
        m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.0)[..., None]
        canvas[oy:oy + out_h, ox:ox + out_w] = region * (1 - m) + art_rgb * m
    canvas += grain(OUT_H, OUT_W, 11)[..., None]
    return np.clip(canvas, 0, 255).astype(np.uint8), paper


def page2(n, placements, paper):
    clean, tmask, big = load(n)
    art = art_mask(clean, tmask)
    canvas = np.empty((OUT_H, OUT_W, 3), np.float32)
    canvas[:] = paper
    for key, (x_mm, y_mm, w_mm) in placements.items():
        bx0, by0, bx1, by1 = CROPS[n][key]
        h_mm = w_mm * (by1 - by0) / (bx1 - bx0)
        ow, oh = int(round(w_mm * PXMM)), int(round(h_mm * PXMM))
        rgb = sample(big, bx0, by0, bx1, by1, ow, oh, scale=4).astype(np.float32)
        # local paper of the crop -> match to target paper
        sub = clean[by0:by1, bx0:bx1]
        sa = art[by0:by1, bx0:bx1]
        st = tmask[by0:by1, bx0:bx1]
        cp = np.median(sub[~cv2.dilate(sa.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool) & ~st], 0)
        rgb *= (paper / cp)
        a = cv2.dilate(sa.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))).astype(np.float32)
        a = cv2.GaussianBlur(a, (0, 0), 3)
        core = cv2.resize(cv2.GaussianBlur(sa.astype(np.float32), (0, 0), 1.0), (ow, oh), interpolation=cv2.INTER_LINEAR)[..., None]
        # fade out at crop borders so nothing is ever cut with a hard edge
        e = np.ones_like(a)
        k = 6
        e[:k, :] *= np.linspace(0, 1, k)[:, None]; e[-k:, :] *= np.linspace(1, 0, k)[:, None]
        e[:, :k] *= np.linspace(0, 1, k)[None]; e[:, -k:] *= np.linspace(1, 0, k)[None]
        a = np.clip(a, 0, 1) * e
        a_o = cv2.resize(a, (ow, oh), interpolation=cv2.INTER_LINEAR)[..., None]
        X = int(round((x_mm + BLEED) * PXMM)); Y = int(round((y_mm + BLEED) * PXMM))
        reg = canvas[Y:Y + oh, X:X + ow]
        # outside the painted strokes never let the crop be lighter than the paper (no glow halos)
        rgb = core * rgb + (1 - core) * np.minimum(rgb, paper)
        canvas[Y:Y + oh, X:X + ow] = reg * (1 - a_o) + rgb * a_o
    canvas += grain(OUT_H, OUT_W, 23)[..., None]
    return np.clip(canvas, 0, 255).astype(np.uint8)


def crop_size_mm(n, key, w_mm):
    bx0, by0, bx1, by1 = CROPS[n][key]
    return w_mm, w_mm * (by1 - by0) / (bx1 - bx0)
