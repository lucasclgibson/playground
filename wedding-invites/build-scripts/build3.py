"""Pocket inserts: Details (portrait 120 x 160 mm) and RSVP (landscape 120 x 90 mm)."""
import os, sys
import numpy as np
from PIL import Image
import bg, build
from build import Page, place_bg, SLUG, MM, rl

FR = 4.5
SIZES = {'details': (120.0, 160.0), 'rsvp': (120.0, 90.0)}
ISZ = {'Timings': dict(r=3.5), 'Dress code': dict(r=3.3), 'A small note': dict(w=7.0), 'Accommodation': dict(w=8.2)}


def set_size(w, h):
    bg.TRIM_W, bg.TRIM_H = w, h
    bg.OUT_W = int(round((w + 2 * bg.BLEED) * bg.PXMM))
    bg.OUT_H = int(round((h + 2 * bg.BLEED) * bg.PXMM))
    bg.NOTCH = 3.0
    build.TW, build.TH = w, h


def details_layout(n, TW, TH):
    wt, wb = 34.0, 40.0
    _, hb = bg.crop_size_mm(n, 'det_bot', wb)
    return {'det_top': (TW - FR - 0.6 - wt, FR + 0.6, wt),
            'det_bot': (TW - FR - 0.6 - wb, TH - FR - 0.6 - hb, wb)}


def details(pg, n, TW, TH):
    t = pg.text
    pg.notched_frame(FR, FR, TW - FR, TH - FR, bg.NOTCH, lw=0.5)
    x0 = 13.0
    t('The Details', x0, 26.0, 'Script', 34, align='l')
    ix, tx = x0 + 4.5, x0 + 13.0
    sections = [
        ('Timings', pg.icon_clock,
         ['Guests are invited to arrive at 1:30pm', 'for a ceremony at 2:00pm.'] if n == 'day' else
         ['Guests are invited to arrive at 7:00pm', 'for the evening reception.']),
        ('Dress code', pg.icon_flower, ['We welcome', 'Garden Party Florals & Pastels']),
        ('A small note', pg.icon_heart, ['We adore your little ones,', 'however, this celebration is',
                                        'intended for adults.']),
        ('Accommodation', pg.icon_bed, ['Accommodation is available at', 'Chicheley Hall. Please book directly',
                                         'with the venue to secure your stay.']),
    ]
    y = 42.0
    for head, icon, body in sections:
        t(head, tx, y, 'Script', 16.5, align='l')
        icon(ix, y + 2.5, **ISZ[head])
        yy = y + 5.4
        for line in body:
            t(line, tx, yy, 'EBG', 9.2, align='l')
            yy += 4.1
        y = yy + 5.6
    yy = y + 0.5
    for line in ['For more information, including travel', 'and local recommendations, please visit',
                 'our wedding website via the QR code', 'on the RSVP card.']:
        t(line, tx, yy, 'EBG', 8.4, align='l')
        yy += 3.8


def rsvp_layout(n, TW, TH):
    w = 47.0
    return {'rsvp_top': (83.0 - w / 2, FR + 1.5, w)}


def rsvp(pg, n, TW, TH):
    t = pg.text
    pg.notched_frame(FR, FR, TW - FR, TH - FR, bg.NOTCH, lw=0.5)
    q, qx, qy = 40.0, 12.0, (TH - 40.0) / 2
    pg.notched_frame(qx, qy, qx + q, qy + q, 2.5, lw=0.45)
    pg.qr(build.URL, qx + q / 2, qy + q / 2, q - 8)
    cx = 83.0
    t('RSVP', cx, 50.5, 'Script', 34)
    for i, line in enumerate(['KINDLY SCAN THE QR CODE', 'TO RSVP AND ACCESS FURTHER', 'WEDDING INFORMATION.']):
        t(line, cx, 58.0 + i * 4.3, 'EBG5', 7.6, track=0.1)
    t(build.URL_PRINTED, cx, 75.2, 'EBG', 7.6)


def make(n, card, outdir):
    TW, TH = SIZES[card]
    set_size(TW, TH)
    tmp = f'{bg.HERE}/tmp_ins_{n}_{card}'
    os.makedirs(tmp, exist_ok=True)
    paper = np.load(f'{bg.HERE}/tmp57_{n}/paper.npy')
    lay = details_layout if card == 'details' else rsvp_layout
    arr = bg.page2(n, lay(n, TW, TH), paper)
    title = {'day': 'Day', 'evening': 'Evening'}[n]
    name = {'details': 'Details', 'rsvp': 'RSVP'}[card]
    out = f'{outdir}/Loren-and-Jack_{title}_{name}-card_{int(TW)}x{int(TH)}mm_print.pdf'
    W, H = (TW + 2 * SLUG) * MM, (TH + 2 * SLUG) * MM
    c = rl.Canvas(out, pagesize=(W, H), initialFontName='EBG', initialFontSize=10, pageCompression=1)
    c.setTitle(f'Loren & Jack – {title} {name} card')
    pg = Page(c)
    place_bg(pg, arr, f'{tmp}/bg_cmyk.jpg')
    (details if card == 'details' else rsvp)(pg, n, TW, TH)
    pg.crop_marks()
    pg.slug(f'{title} {name} · {int(TW)} × {int(TH)} mm · 3 mm bleed')
    c.showPage(); c.save()
    return out


if __name__ == '__main__':
    os.makedirs(sys.argv[1], exist_ok=True)
    for n in ('day', 'evening'):
        for card in ('details', 'rsvp'):
            print(make(n, card, sys.argv[1]))
