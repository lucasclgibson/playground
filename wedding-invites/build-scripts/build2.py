"""5x7 (127 x 178 mm) pocketfold insert: front-only and two-sided (front + details) print PDFs."""
import os, sys
from PIL import Image
import bg, build

TW, TH = 127.0, 178.0
FR = 4.5                                  # frame inset from trim
bg.TRIM_W, bg.TRIM_H = TW, TH
bg.OUT_W = int(round((TW + 2 * bg.BLEED) * bg.PXMM))
bg.OUT_H = int(round((TH + 2 * bg.BLEED) * bg.PXMM))
bg.NOTCH = 3.0
IW, IH = TW - 2 * FR, TH - 2 * FR
bg.P1 = {
    'day':     dict(cx=727.0, top=36.0, s=IW / 1312.0, frame=FR, card=(29, 27, 1383, 2006)),
    'evening': dict(cx=792.0, top=26.0, s=IH / 1995.0, frame=FR, card=(39, 25, 1499, 2022)),
}
build.TW, build.TH = TW, TH
from build import Page, place_bg, SLUG, MM, rl

LW = 0.5
ISZ = {'Timings': dict(r=3.7), 'Dress code': dict(r=3.5), 'A small note': dict(w=7.4), 'Accommodation': dict(w=8.6)}


def front(pg, n):
    t = pg.text
    pg.notched_frame(FR, FR, TW - FR, TH - FR, bg.NOTCH, lw=LW)
    cx = TW / 2
    y = 80.0 if n == 'day' else 82.5
    t('WE INVITE YOU TO JOIN US', cx, y, 'EBG5', 8.2, track=0.12)
    t('TO CELEBRATE THE MARRIAGE OF', cx, y + 4.3, 'EBG5', 8.2, track=0.12)
    t('LOREN SHORT', cx, y + 15.5, 'EBG5', 28, width=73)
    t('&', cx, y + 22.3, 'EBG5', 19)
    t('JACK FELLOWS', cx, y + 31.8, 'EBG5', 28, width=75)
    t('08 . 07 . 2027', cx, y + 41.6, 'EBG5', 16, track=0.1)
    t('THURSDAY, THE EIGHTH OF JULY', cx, y + 46.7, 'EBG5', 8.2, track=0.08)
    t('TWO THOUSAND AND TWENTY-SEVEN', cx, y + 50.9, 'EBG5', 8.2, track=0.08)
    if n == 'day':
        l1, l2 = 'Guests are invited to arrive at 1:30pm', 'for the ceremony at 2:00pm'
    else:
        l1, l2 = 'Guests are invited to arrive at 7:00pm', 'for the evening reception'
    t(l1, cx, y + 57.8, 'EBG', 10.5)
    t(l2, cx, y + 62.4, 'EBG', 10.5)
    t('CHICHELEY HALL', cx, y + 71.0, 'EBG5', 17, width=52)
    t('NEWPORT PAGNELL', cx, y + 75.8, 'EBG5', 8.2, track=0.22)
    if n == 'day':
        t('Reception to follow', cx, y + 83.2, 'Script', 15)


def back_layout(n):
    w_top = 36.0
    _, h = bg.crop_size_mm(n, 'det_top', w_top)
    w_bot = 31.0
    _, hb = bg.crop_size_mm(n, 'det_bot', w_bot)
    return {'det_top': (TW - FR - 0.6 - w_top, FR + 0.6, w_top),
            'det_bot': (TW - FR - 0.6 - w_bot, TH - FR - 0.6 - hb, w_bot)}


def back(pg, n):
    t = pg.text
    pg.notched_frame(FR, FR, TW - FR, TH - FR, bg.NOTCH, lw=LW)
    x0 = 14.0
    t('The Details', x0, 27.0, 'Script', 34, align='l')
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
    y = 44.0
    for head, icon, body in sections:
        t(head, tx, y, 'Script', 17, align='l')
        icon(ix, y + 2.6, **ISZ[head])
        yy = y + 5.6
        for line in body:
            t(line, tx, yy, 'EBG', 9.3, align='l')
            yy += 4.2
        y = yy + 6.4
    # RSVP / QR block
    qy = y + 2.0
    q = 25.0
    pg.notched_frame(x0 - 1, qy - 1.5, x0 + q + 2, qy + q + 1.5, 2.0, lw=0.4)
    pg.qr(build.URL, x0 + q / 2 + 0.5, qy + q / 2, q - 4)
    rx = x0 + q + 6
    t('RSVP', rx, qy + 8.0, 'Script', 20, align='l')
    for i, line in enumerate(['Kindly scan the QR code to RSVP', 'and for travel, local tips and', 'further wedding information.']):
        t(line, rx, qy + 13.2 + i * 4.0, 'EBG', 8.6, align='l')
    t(build.URL_PRINTED, rx, qy + 13.2 + 3 * 4.0 + 0.6, 'EBG5', 6.8, align='l')


def make(n, outdir, two_sided):
    tmp = f'{bg.HERE}/tmp57_{n}'
    os.makedirs(tmp, exist_ok=True)
    title = {'day': 'Day', 'evening': 'Evening'}[n]
    kind = 'Front-and-Back' if two_sided else 'Front'
    out = f'{outdir}/Loren-and-Jack_{title}-Invitation_5x7_{kind}_print.pdf'
    W, H = (TW + 2 * SLUG) * MM, (TH + 2 * SLUG) * MM
    c = rl.Canvas(out, pagesize=(W, H), initialFontName='EBG', initialFontSize=10, pageCompression=1)
    c.setTitle(f'Loren & Jack – {title} Invitation ({kind})')
    f_png = f'{tmp}/front.png'
    if os.path.exists(f_png):
        bg1 = __import__('numpy').asarray(Image.open(f_png))
        paper = __import__('numpy').load(f'{tmp}/paper.npy')
    else:
        bg1, paper = bg.page1(n)
        Image.fromarray(bg1).save(f_png); __import__('numpy').save(f'{tmp}/paper.npy', paper)
    pages = [(bg1, front, 'front')]
    if two_sided:
        pages.append((bg.page2(n, back_layout(n), paper), back, 'back'))
    for i, (arr, drawer, side) in enumerate(pages):
        pg = Page(c)
        place_bg(pg, arr, f'{tmp}/{side}_cmyk.jpg')
        drawer(pg, n)
        pg.crop_marks()
        pg.slug(f'Loren & Jack · {title} · {side} · 127 × 178 mm trim · 3 mm bleed · PSO Coated v3')
        c.showPage()
    c.save()
    return out


if __name__ == '__main__':
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    for n in ('day', 'evening'):
        for two in (False, True):
            print(make(n, outdir, two))
