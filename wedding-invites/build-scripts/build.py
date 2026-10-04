"""Builds print-ready 2-page A4 PDFs (3 mm bleed, crop marks, CMYK) for the day and evening invites."""
import os, sys, math, io
import numpy as np, qrcode
from PIL import Image, ImageCms
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
from reportlab.pdfgen import canvas as rl
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import bg

HERE = os.path.dirname(os.path.abspath(__file__))
MM = 72 / 25.4
SLUG = 12.0                     # mm of paper around the bleed for crop marks / slug info
TW, TH, B = bg.TRIM_W, bg.TRIM_H, bg.BLEED
URL = 'http://lorenandjack-08-07-2027.wvsa.co.uk'
URL_PRINTED = 'lorenandjack-08-07-2027.wvsa.co.uk'
ICC = f'{HERE}/models/PSOcoated_v3.icc'

for name, f in [('EBG', 'EB_Garamond_400'), ('EBG5', 'EB_Garamond_500'), ('EBG6', 'EB_Garamond_600'),
                ('Script', 'Pinyon_Script_400')]:
    pdfmetrics.registerFont(TTFont(name, f'{HERE}/fonts/{f}.ttf'))

BLUE = (1.00, 0.78, 0.0, 0.05)
PINK = (0.0, 0.40, 0.22, 0.0)
PINK_LINE = (0.03, 0.78, 0.52, 0.02)
REG = (1, 1, 1, 1)


class Page:
    def __init__(self, c):
        self.c = c

    # trim-mm (top-left origin) -> PDF points
    def X(self, x): return (SLUG + x) * MM
    def Y(self, y): return (SLUG + TH - y) * MM

    def fill(self, col): self.c.setFillColorCMYK(*col)
    def stroke(self, col): self.c.setStrokeColorCMYK(*col)

    def text(self, s, x, y, font, size, col=BLUE, track=0.0, align='c', width=None):
        """Baseline at y (mm). track in em; or width (mm) solves tracking to fit."""
        c = self.c
        n = len(s)
        nat = pdfmetrics.stringWidth(s, font, size)
        if width is not None and n > 1:
            cs = (width * MM - nat) / (n - 1)
        else:
            cs = track * size
        w = nat + cs * (n - 1)
        x0 = self.X(x) - (w / 2 if align == 'c' else (w if align == 'r' else 0))
        t = c.beginText(x0, self.Y(y))
        t.setFont(font, size)
        t.setCharSpace(cs)
        t.setFillColorCMYK(*col)
        t.textOut(s)
        c.drawText(t)
        return w / MM

    def heart_path(self, cx, cy, w):
        """Classic heart, width w mm, centre (cx, cy) mm."""
        p = self.c.beginPath()
        s = w / 2.0
        X, Y = self.X, self.Y
        top = cy - 0.30 * s
        p.moveTo(X(cx), Y(top))
        p.curveTo(X(cx - 0.05 * s), Y(cy - 0.75 * s), X(cx - 1.0 * s), Y(cy - 0.85 * s), X(cx - 1.0 * s), Y(cy - 0.20 * s))
        p.curveTo(X(cx - 1.0 * s), Y(cy + 0.30 * s), X(cx - 0.35 * s), Y(cy + 0.55 * s), X(cx), Y(cy + 0.95 * s))
        p.curveTo(X(cx + 0.35 * s), Y(cy + 0.55 * s), X(cx + 1.0 * s), Y(cy + 0.30 * s), X(cx + 1.0 * s), Y(cy - 0.20 * s))
        p.curveTo(X(cx + 1.0 * s), Y(cy - 0.85 * s), X(cx + 0.05 * s), Y(cy - 0.75 * s), X(cx), Y(top))
        p.close()
        return p

    def divider(self, cx, cy, heart=3.2, arm=9.0):
        c = self.c
        gap = heart * 0.75
        # tapered arms: blue near the heart, thinning to a hairline point
        for sgn in (-1, 1):
            x_in, x_out = cx + sgn * gap, cx + sgn * (gap + arm)
            self.fill(BLUE)
            p = c.beginPath()
            p.moveTo(self.X(x_in), self.Y(cy - 0.13))
            p.lineTo(self.X(x_out), self.Y(cy - 0.02))
            p.lineTo(self.X(x_out), self.Y(cy + 0.02))
            p.lineTo(self.X(x_in), self.Y(cy + 0.13))
            p.close()
            c.drawPath(p, stroke=0, fill=1)
        self.fill(PINK); self.stroke(PINK_LINE)
        c.setLineWidth(0.35)
        c.drawPath(self.heart_path(cx, cy, heart), stroke=1, fill=1)

    def leaf(self, bx, by, length, width, ang):
        """Outlined almond leaf from base (bx,by), angle in degrees (0 = +x, y down)."""
        c = self.c
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy, ux
        tx, ty = bx + ux * length, by + uy * length
        w = width / 2
        p = c.beginPath()
        p.moveTo(self.X(bx), self.Y(by))
        p.curveTo(self.X(bx + ux * length * 0.3 + nx * w * 1.3), self.Y(by + uy * length * 0.3 + ny * w * 1.3),
                  self.X(bx + ux * length * 0.75 + nx * w * 1.1), self.Y(by + uy * length * 0.75 + ny * w * 1.1),
                  self.X(tx), self.Y(ty))
        p.curveTo(self.X(bx + ux * length * 0.75 - nx * w * 1.1), self.Y(by + uy * length * 0.75 - ny * w * 1.1),
                  self.X(bx + ux * length * 0.3 - nx * w * 1.3), self.Y(by + uy * length * 0.3 - ny * w * 1.3),
                  self.X(bx), self.Y(by))
        p.close()
        c.drawPath(p, stroke=1, fill=0)

    def sprig(self, x_tip, y, length, direction):
        """Laurel-arrow ornament. direction=+1 points right (tip at x_tip), -1 points left."""
        c = self.c
        self.stroke(BLUE); self.fill(BLUE)
        c.setLineWidth(0.7); c.setLineCap(1); c.setLineJoin(1)
        d = direction
        x_tail = x_tip - d * length
        c.line(self.X(x_tail + d * 3.2), self.Y(y), self.X(x_tip), self.Y(y))
        c.setLineWidth(0.5)
        # small oval at tail
        self.leaf(x_tail + d * 3.4, y, 3.2, 1.25, 180 if d > 0 else 0)
        n = 4
        for i in range(n):
            bx = x_tail + d * (7.0 + i * (length - 14.0) / (n - 1))
            for side in (-1, 1):
                ang = (180 + side * 33) if d > 0 else (0 - side * 33)
                self.leaf(bx, y, 4.6, 1.9, ang)

    def notched_frame(self, x0, y0, x1, y1, r, lw=0.5):
        c = self.c
        self.stroke(BLUE)
        c.setLineWidth(lw)
        p = c.beginPath()
        X, Y = self.X, self.Y
        k = 0.5523 * r
        p.moveTo(X(x0 + r), Y(y0))
        p.lineTo(X(x1 - r), Y(y0))
        p.curveTo(X(x1 - r), Y(y0 + k), X(x1 - k), Y(y0 + r), X(x1), Y(y0 + r))
        p.lineTo(X(x1), Y(y1 - r))
        p.curveTo(X(x1 - k), Y(y1 - r), X(x1 - r), Y(y1 - k), X(x1 - r), Y(y1))
        p.lineTo(X(x0 + r), Y(y1))
        p.curveTo(X(x0 + r), Y(y1 - k), X(x0 + k), Y(y1 - r), X(x0), Y(y1 - r))
        p.lineTo(X(x0), Y(y0 + r))
        p.curveTo(X(x0 + k), Y(y0 + r), X(x0 + r), Y(y0 + k), X(x0 + r), Y(y0))
        p.close()
        c.drawPath(p, stroke=1, fill=0)

    def qr(self, data, cx, cy, size):
        q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, border=0)
        q.add_data(data); q.make(fit=True)
        m = q.get_matrix()
        n = len(m)
        cell = size / n
        x0, y0 = cx - size / 2, cy - size / 2
        self.fill(BLUE)
        p = self.c.beginPath()
        for r in range(n):
            col = 0
            while col < n:
                if m[r][col]:
                    st = col
                    while col < n and m[r][col]: col += 1
                    p.rect(self.X(x0 + st * cell), self.Y(y0 + (r + 1) * cell), (col - st) * cell * MM, cell * MM)
                else:
                    col += 1
        self.c.drawPath(p, stroke=0, fill=1)
        return n

    # ---------- line icons ----------
    def icon_clock(self, cx, cy, r=5.0):
        c = self.c; self.stroke(BLUE)
        c.setLineWidth(0.75); c.circle(self.X(cx), self.Y(cy), r * MM, stroke=1, fill=0)
        c.setLineWidth(0.35); c.circle(self.X(cx), self.Y(cy), (r - 0.75) * MM, stroke=1, fill=0)
        c.setLineCap(1)
        for k in range(4):
            a = k * math.pi / 2
            c.line(self.X(cx + math.sin(a) * (r - 1.15)), self.Y(cy - math.cos(a) * (r - 1.15)),
                   self.X(cx + math.sin(a) * (r - 1.85)), self.Y(cy - math.cos(a) * (r - 1.85)))
        c.setLineWidth(0.7)
        c.line(self.X(cx), self.Y(cy), self.X(cx), self.Y(cy - (r - 1.5)))
        a = math.radians(120)
        c.line(self.X(cx), self.Y(cy), self.X(cx + math.sin(a) * (r - 2.3)), self.Y(cy - math.cos(a) * (r - 2.3)))
        self.fill(BLUE); c.circle(self.X(cx), self.Y(cy), 0.35 * MM, stroke=0, fill=1)

    def icon_flower(self, cx, cy, r=4.9):
        c = self.c; self.stroke(BLUE)
        petals = []
        for k in range(4):
            a = math.radians(45 + k * 90)
            # each petal = two lobes -> heart-shaped notched petal
            for da in (-21, 21):
                aa = a + math.radians(da)
                petals.append(Point(math.cos(aa) * r * 0.56, math.sin(aa) * r * 0.56).buffer(r * 0.34, 48))
            petals.append(Point(math.cos(a) * r * 0.40, math.sin(a) * r * 0.40).buffer(r * 0.30, 48))
        shape = unary_union(petals + [Point(0, 0).buffer(r * 0.40, 48)])
        p = c.beginPath()
        for ring in [shape.exterior]:
            pts = list(ring.coords)
            p.moveTo(self.X(cx + pts[0][0]), self.Y(cy + pts[0][1]))
            for x, y in pts[1:]: p.lineTo(self.X(cx + x), self.Y(cy + y))
            p.close()
        c.setLineWidth(0.55); c.setLineJoin(1)
        c.drawPath(p, stroke=1, fill=0)
        c.setLineWidth(0.4)
        c.circle(self.X(cx), self.Y(cy), r * 0.17 * MM, stroke=1, fill=0)
        c.setLineCap(1)
        for k in range(10):
            a = k * math.pi / 5
            c.line(self.X(cx + math.cos(a) * r * 0.25), self.Y(cy + math.sin(a) * r * 0.25),
                   self.X(cx + math.cos(a) * r * 0.36), self.Y(cy + math.sin(a) * r * 0.36))
        c.setLineWidth(0.55)
        from shapely.geometry import LineString
        hit = shape.exterior.intersection(LineString([(0, 0), (0, 2 * r)]))
        y_bot = cy + max(g.y for g in getattr(hit, 'geoms', [hit]))
        c.line(self.X(cx), self.Y(y_bot), self.X(cx), self.Y(cy + r * 1.8))

    def icon_heart(self, cx, cy, w=10.0):
        c = self.c; self.stroke(BLUE); c.setLineWidth(0.6); c.setLineJoin(1)
        c.drawPath(self.heart_path(cx, cy, w), stroke=1, fill=0)

    def icon_bed(self, cx, cy, w=11.5):
        c = self.c; self.stroke(BLUE); c.setLineWidth(0.65); c.setLineCap(1); c.setLineJoin(1)
        x0, x1 = cx - w / 2, cx + w / 2
        top, base = cy - 0.30 * w, cy + 0.26 * w
        mt, mb = cy - 0.02 * w, cy + 0.11 * w
        X, Y = self.X, self.Y
        c.line(X(x0), Y(top), X(x0), Y(base))                 # headboard post
        c.line(X(x1), Y(cy - 0.08 * w), X(x1), Y(base))       # footboard post
        c.line(X(x0), Y(mb), X(x1), Y(mb))                    # bed frame
        c.setLineWidth(0.5)
        c.line(X(x0), Y(mt), X(x1), Y(mt))                    # mattress
        c.circle(X(x0 + 0.17 * w), Y(mt - 0.10 * w), 0.085 * w * MM, stroke=1, fill=0)   # head
        p = c.beginPath()                                      # blanket over body
        p.moveTo(X(x0 + 0.29 * w), Y(mt))
        p.lineTo(X(x0 + 0.29 * w), Y(mt - 0.09 * w))
        p.curveTo(X(x0 + 0.29 * w), Y(mt - 0.14 * w), X(x0 + 0.33 * w), Y(mt - 0.14 * w), X(x0 + 0.38 * w), Y(mt - 0.14 * w))
        p.lineTo(X(x1 - 0.06 * w), Y(mt - 0.14 * w))
        p.lineTo(X(x1 - 0.06 * w), Y(mt))
        c.drawPath(p, stroke=1, fill=0)

    # ---------- marks ----------
    def crop_marks(self, extra_x=()):
        c = self.c
        c.setStrokeColorCMYK(*REG); c.setLineWidth(0.25)
        off, ln = B, 5.0         # start at bleed edge, 5 mm long
        for x in (0, TW):
            for y, sgn in ((0, -1), (TH, 1)):
                c.line(self.X(x), self.Y(y + sgn * off), self.X(x), self.Y(y + sgn * (off + ln)))
        for y in (0, TH):
            for x, sgn in ((0, -1), (TW, 1)):
                c.line(self.X(x + sgn * off), self.Y(y), self.X(x + sgn * (off + ln)), self.Y(y))
        for x in extra_x:
            for y, sgn in ((0, -1), (TH, 1)):
                c.line(self.X(x), self.Y(y + sgn * off), self.X(x), self.Y(y + sgn * (off + ln)))

    def slug(self, label):
        c = self.c
        t = c.beginText(self.X(0), self.Y(TH + B + 5.5))
        t.setFont('EBG', 6); t.setCharSpace(0); t.setFillColorCMYK(0, 0, 0, 1)
        t.textOut(label)
        c.drawText(t)


def to_cmyk_jpeg(arr):
    im = Image.fromarray(arr)
    srgb = ImageCms.createProfile('sRGB')
    prof = ImageCms.getOpenProfile(ICC)
    t = ImageCms.buildTransform(srgb, prof, 'RGB', 'CMYK', renderingIntent=0)
    cm = ImageCms.applyTransform(im, t)
    buf = io.BytesIO()
    cm.save(buf, 'JPEG', quality=95, subsampling=0, dpi=(bg.DPI, bg.DPI))
    buf.seek(0)
    return buf


def place_bg(pg, arr, path):
    with open(path, 'wb') as f:
        f.write(to_cmyk_jpeg(arr).getvalue())
    pg.c.drawImage(path, pg.X(-B), pg.Y(TH + B), (TW + 2 * B) * MM, (TH + 2 * B) * MM)


# ======================= LAYOUT =======================

def draw_page1(pg, n):
    t = pg.text
    if bg.P1[n]['frame']:
        fr = bg.P1[n]['frame']
        pg.notched_frame(fr, fr, TW - fr, TH - fr, bg.NOTCH, lw=0.6)
    cx = TW / 2
    t('WE INVITE YOU TO JOIN US', cx, 131.0, 'EBG5', 12.5, width=70)
    t('TO CELEBRATE THE MARRIAGE OF', cx, 137.6, 'EBG5', 12.5, width=87)
    t('LOREN SHORT', cx, 155.5, 'EBG5', 47, width=126)
    t('&', cx, 166.2, 'EBG5', 34)
    pg.sprig(cx - 11.5, 163.2, 36, +1)
    pg.sprig(cx + 11.5, 163.2, 36, -1)
    t('JACK FELLOWS', cx, 183.2, 'EBG5', 47, width=128)
    pg.divider(cx, 190.3)
    t('08 . 07 . 2027', cx, 201.6, 'EBG5', 27, track=0.13)
    t('THURSDAY, THE EIGHTH OF JULY', cx, 208.4, 'EBG5', 12, width=83)
    t('TWO THOUSAND AND TWENTY-SEVEN', cx, 214.6, 'EBG5', 12, width=94)
    pg.divider(cx, 219.7)
    if n == 'day':
        t('Guests are invited to arrive at 1:30pm', cx, 228.0, 'EBG', 15.5)
        t('for the ceremony at 2:00pm', cx, 235.4, 'EBG', 15.5)
    else:
        t('Guests are invited to arrive at 7:00pm', cx, 228.0, 'EBG', 15.5)
        t('for the evening reception', cx, 235.4, 'EBG', 15.5)
    pg.divider(cx, 241.6)
    t('CHICHELEY HALL', cx, 254.4, 'EBG5', 28, width=91)
    t('NEWPORT PAGNELL', cx, 262.0, 'EBG5', 12.5, width=63)
    if n == 'day':
        t('Reception to follow', cx, 275.0, 'Script', 27)
        pg.divider(cx, 283.5)
    else:
        pg.divider(cx, 270.5)


# page 2 panel geometry (trim mm)
PF = 6.0          # frame inset from each panel edge
PW = TW / 2


def p2_layout(n):
    """Floral placements (x, y, width) in trim mm for page 2."""
    return {
        'rsvp_top': (PW / 2 - 40, 11.0, 80),
        'rsvp_bot': (PW / 2 - 43.5, 0, 87),
        'det_top': (PW + PW - PF - 0.8 - 46, PF + 0.8, 46),
        'det_bot': (PW + PW / 2 - 41, 0, 82),
    }


def resolve_p2(n):
    L = p2_layout(n)
    # bottom florals sit on the frame's inner bottom edge
    for k in ('rsvp_bot', 'det_bot'):
        x, _, w = L[k]
        _, h = bg.crop_size_mm(n, k, w)
        L[k] = (x, TH - PF - 1.2 - h, w)
    return L


def draw_page2(pg, n):
    t = pg.text
    # ---- RSVP panel ----
    pg.notched_frame(PF, PF, PW - PF, TH - PF, bg.NOTCH)
    cx = PW / 2
    t('RSVP', cx, 83.0, 'Script', 58)
    pg.divider(cx, 92.5)
    pg.notched_frame(cx - 32, 101, cx + 32, 165, 4.0, lw=0.5)
    pg.qr(URL, cx, 133, 44)
    t('KINDLY SCAN THE QR CODE', cx, 178.5, 'EBG5', 9.5, track=0.16)
    t('TO RSVP AND ACCESS FURTHER', cx, 184.3, 'EBG5', 9.5, track=0.16)
    t('WEDDING INFORMATION.', cx, 190.1, 'EBG5', 9.5, track=0.16)
    pg.divider(cx, 196.6)
    t(URL_PRINTED, cx, 204.0, 'EBG', 10.5)

    # ---- Details panel ----
    ox = PW
    pg.notched_frame(ox + PF, PF, ox + PW - PF, TH - PF, bg.NOTCH)
    dcx = ox + PW / 2
    tw = t('The Details', ox + 13.5, 47.0, 'Script', 40, align='l')
    pg.divider(ox + 13.5 + tw / 2, 56.5)
    ix, tx = ox + 18.5, ox + 28.5
    sections = [
        ('Timings', pg.icon_clock,
         ['Guests are invited to arrive at 1:30pm', 'for a ceremony at 2:00pm.'] if n == 'day' else
         ['Guests are invited to arrive at 7:00pm', 'for the evening reception.']),
        ('Dress code', pg.icon_flower, ['We welcome', 'Garden Party Florals & Pastels']),
        ('A small note', pg.icon_heart, ['We adore your little ones,', 'however, this celebration is', 'intended for adults.']),
        ('Accommodation', pg.icon_bed, ['Accommodation is available at', 'Chicheley Hall. Please book directly',
                                         'with the venue to secure your stay.']),
    ]
    y = 72.0
    for i, (head, icon, body) in enumerate(sections):
        t(head, tx, y, 'Script', 22, align='l')
        icon(ix, y + 3.6)
        yy = y + 7.4
        for line in body:
            t(line, tx, yy, 'EBG', 10.2, align='l')
            yy += 4.9
        dy = yy + 1.3
        pg.divider(ox + 13.5 + tw / 2, dy)
        y = dy + 12.5
    yy = y - 4.5
    for line in ['For more information, including travel', 'and local recommendations, please visit',
                 'our wedding website via the QR code.']:
        t(line, dcx, yy, 'EBG', 9.4)
        yy += 4.5


def build(n, outdir):
    os.makedirs(outdir, exist_ok=True)
    tmp = f'{HERE}/tmp_{n}'
    os.makedirs(tmp, exist_ok=True)
    W, H = (TW + 2 * SLUG) * MM, (TH + 2 * SLUG) * MM
    title = {'day': 'Day Invitation', 'evening': 'Evening Invitation'}[n]
    out = f'{outdir}/Loren-and-Jack_{title.replace(" ", "-")}_A4_print.pdf'
    c = rl.Canvas(out, pagesize=(W, H), initialFontName='EBG', initialFontSize=10, pageCompression=1)
    c.setTitle(f'Loren & Jack – {title}')
    c.setAuthor('Loren Short & Jack Fellows')

    bg1, paper = bg.page1(n)
    Image.fromarray(bg1).save(f'{tmp}/p1_rgb.png')
    bg2 = bg.page2(n, resolve_p2(n), paper)
    Image.fromarray(bg2).save(f'{tmp}/p2_rgb.png')

    for i, (arr, drawer, extra) in enumerate([(bg1, draw_page1, ()), (bg2, draw_page2, (PW,))]):
        pg = Page(c)
        place_bg(pg, arr, f'{tmp}/p{i + 1}_cmyk.jpg')
        drawer(pg, n)
        pg.crop_marks(extra)
        pg.slug(f'Loren & Jack · {title} · p{i + 1}/2 · A4 trim, 3 mm bleed · PSO Coated v3'
                + (' · centre marks: optional cut to 2 × (105 × 297 mm)' if i else ''))
        c.showPage()
    c.save()
    return out


if __name__ == '__main__':
    outdir = sys.argv[2] if len(sys.argv) > 2 else f'{HERE}/out'
    for n in sys.argv[1].split(','):
        print(build(n, outdir))
