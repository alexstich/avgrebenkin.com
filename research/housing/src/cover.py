#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Обложки страницы из самих данных: карта NUTS 3 в пяти классах статьи.

    python3 research/housing/src/cover.py

Пишет два SVG рядом и растрирует их через rsvg-convert и cwebp:
  cover.svg       → images/research/housing.jpg   1200×630, с английским заголовком,
                    для карточки на индексе и соцсетей (+ .webp для карточки)
  cover-page.svg  → images/research/housing-page.webp 1600×560, без единого слова,
                    в шапку самой страницы
Карта — та же, что на странице: покупка, средний местный доход, 30 лет.
"""
import json, math, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
IMG = os.path.join(ROOT, 'images', 'research')
geo = json.load(open(os.path.join(HERE, 'geo.json'), encoding='utf-8'))
data = json.load(open(os.path.join(HERE, 'data.json'), encoding='utf-8'))

RAMP = ['#f43f5e', '#fb923c', '#facc15', '#a3e635', '#3ecf8e']   # <50 … >150, тёмная тема
BG, INK, MUTED, ND = '#0b0c11', '#e9eaf0', '#9298a8', '#1a1d27'


def cls(v):
    if not v:
        return -1
    for i, b in enumerate(data['classes']):
        if v <= b:
            return i
    return 4


# Тот же цветовой порядок, что на странице: у метров больше — лучше, у лет дохода
# наоборот, поэтому индекс переворачивается. Кадр без цены за метр красится
# годами дохода — не потому что так красивее, а потому что метров там нет.
YEARS_BREAKS = [3, 5, 8, 12]


def ycls(v):
    if not v or v <= 0:
        return -1
    i = 0
    while i < len(YEARS_BREAKS) and v > YEARS_BREAKS[i]:
        i += 1
    return 4 - i


EXTRA = {}
for _a in data.get('extra', []):
    EXTRA[_a[0]] = {'val': _a[1], 'rent': _a[2]}


def years(income_year, key):
    x = EXTRA.get(key)
    return (x['val'] / income_year) if (x and x.get('val') and income_year) else 0.0


def afford(income_year, price_m2, rate_pct, share=100.0 / 3.0, years=30):
    """Формула самого исследования: РОВНО треть дохода (не 33 %, разница 1 %),
    аннуитет на 30 лет по ставке
    страны. Совпадает с buyM2() на странице при настройках по умолчанию."""
    if not price_m2 or not income_year or not rate_pct:
        return 0.0
    i = rate_pct / 100.0 / 12.0
    n = years * 12
    ann = (1 - (1 + i) ** -n) / i if i > 0 else n
    return (income_year / 12.0) * share / 100.0 * ann / price_m2


def project(fr, lat, lon):
    """Та же проекция, что в geo.py, в те же экранные единицы: обложка обязана
    совпадать с картой на странице, а не жить своей геометрией. Кадр передаётся
    явно — у Европы и у США центры проекции разные."""
    p, l = math.radians(lat), math.radians(lon)
    p0, l0 = math.radians(fr['lat0']), math.radians(fr['lon0'])
    k = math.sqrt(2 / (1 + math.sin(p0) * math.sin(p) + math.cos(p0) * math.cos(p) * math.cos(l - l0)))
    x = k * math.cos(p) * math.sin(l - l0)
    y = k * (math.cos(p0) * math.sin(p) - math.sin(p0) * math.cos(p) * math.cos(l - l0))
    minx, maxx, miny, maxy = fr['box']
    scale = fr['w'] / (maxx - minx)
    return (x - minx) * scale, (maxy - y) * scale


# Страна → кадр: точки чужого слоя в чужой кадр попадать не должны, иначе
# американские округа разлетятся по Европе.
FRAME_OF = {c['c']: c.get('frame', geo['order'][0]) for c in data['countries']}


def frame_box(key, x0, y0, w, h):
    """Куда карта кадра ляжет на самом деле: подписи обязаны стоять над картой, а
    не над прямоугольником, в который её вписали."""
    fr = geo['frames'][key]
    sc = min(w / fr['w'], h / fr['h'])
    return x0 + (w - fr['w'] * sc) / 2, y0 + (h - fr['h'] * sc) / 2, fr['w'] * sc, fr['h'] * sc


def map_svg(key, x0, y0, w, h, dots=900):
    """Карта кадра в прямоугольнике (x0, y0, w, h): страны заливкой, места
    точками — как на странице. Контуров уровня региона больше нет, см. geo.py."""
    fr = geo['frames'][key]
    sc = min(w / fr['w'], h / fr['h'])
    ox, oy = x0 + (w - fr['w'] * sc) / 2, y0 + (h - fr['h'] * sc) / 2
    # Кадр обязан обрезаться ровно так же, как viewBox на странице: соседи
    # выходят за рамку, и без обрезки Турция и Северная Африка лезут в заголовок.
    cid = 'clip-' + key
    out = ['<clipPath id="%s"><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f"/></clipPath>'
           % (cid, ox, oy, fr['w'] * sc, fr['h'] * sc),
           '<g clip-path="url(#%s)"><g transform="translate(%.1f %.1f) scale(%.4f)">' % (cid, ox, oy, sc)]
    m2 = data['frames'].get(key, {}).get('m2', True)
    cval, cyear = {}, {}
    for c in data['countries']:
        cval[c['c']] = c['sa']
        cyear[c['c']] = years(c.get('inc') or 0, 'c:' + c['c'])
    for cc, d in fr['countries'].items():
        k = cls(cval.get(cc, 0)) if m2 else ycls(cyear.get(cc, 0))
        fill = RAMP[k] if k >= 0 else ND
        out.append('<path d="%s" fill="%s" fill-opacity="0.8" stroke="%s" stroke-width="%.2f"/>' % (d, fill, BG, 0.6 / sc))
    # Точки — самые населённые места кадра; порядок в data['places'] уже по населению.
    F = data['placefields']
    ip, ilat, ilon, isp = F.index('pop'), F.index('lat100'), F.index('lon100'), F.index('sp')
    icc, iinc = F.index('cc'), F.index('inc')
    codes = [c['c'] for c in data['countries']]
    rates = {i: c.get('rate') or 0 for i, c in enumerate(data['countries'])}
    n = 0
    iid = F.index('id')
    for a in data['places']:
        if n >= dots:
            break
        if FRAME_OF.get(codes[a[icc]]) != key:
            continue
        if m2:
            if not a[isp]:
                continue
            k = cls(afford(a[iinc], a[isp], rates.get(a[icc], 0)))
        else:
            y2 = years(a[iinc], a[iid])
            if not y2:
                continue
            k = ycls(y2)
        x, y = project(fr, a[ilat] / 100.0, a[ilon] / 100.0)
        r = max(2.6, min(11.0, math.sqrt(a[ip]) / 130.0))
        out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" stroke-width="%.2f"/>'
                   % (x, y, r, RAMP[k] if k >= 0 else ND, BG, 0.8 / sc))
        n += 1
    out.append('</g></g>')
    return ''.join(out)


def frame_label(key, box, text, dy=-10):
    x, y, w, _ = frame_box(key, *box)
    return ('<text x="%.0f" y="%.0f" text-anchor="middle" font-family="JetBrains Mono, Menlo, monospace" '
            'font-size="12" fill="%s" letter-spacing="1.5">%s</text>'
            % (x + w / 2, y + dy, MUTED, text.upper()))


def legend(x, y):
    labels = ['under 50 m²', '50–75', '76–100', '101–150', 'over 150']
    out = []
    for i, t in enumerate(labels):
        out.append('<rect x="%d" y="%d" width="22" height="14" rx="3" fill="%s"/>' % (x, y + i * 24, RAMP[i]))
        out.append('<text x="%d" y="%d" font-family="JetBrains Mono, Menlo, monospace" font-size="13" fill="%s">%s</text>' % (x + 30, y + i * 24 + 12, MUTED, t))
    return ''.join(out)


def cover():
    W, H = 1200, 630
    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H),
         '<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG),
         map_svg('na', 560, 44, 620, 268, 520),
         frame_label('na', (560, 44, 620, 268), 'United States'),
         map_svg('eu', 560, 352, 620, 258, 520),
         frame_label('eu', (560, 352, 620, 258), 'Europe'),
         '<text x="56" y="150" font-family="Space Grotesk, Inter, system-ui, sans-serif" font-size="52" font-weight="700" fill="%s" letter-spacing="-1.5">How many</text>' % INK,
         '<text x="56" y="208" font-family="Space Grotesk, Inter, system-ui, sans-serif" font-size="52" font-weight="700" fill="%s" letter-spacing="-1.5">square metres</text>' % INK,
         '<text x="56" y="266" font-family="Space Grotesk, Inter, system-ui, sans-serif" font-size="52" font-weight="700" fill="%s" letter-spacing="-1.5">can you afford?</text>' % INK,
         '<text x="56" y="316" font-family="Inter, system-ui, sans-serif" font-size="19" fill="%s">Your income against 8,489 European towns</text>' % MUTED,
         '<text x="56" y="344" font-family="Inter, system-ui, sans-serif" font-size="19" fill="%s">and 3,141 US counties.</text>' % MUTED,
         '<text x="56" y="386" font-family="JetBrains Mono, Menlo, monospace" font-size="12" fill="%s" letter-spacing="1.5">EUROPE — M² A THIRD OF THE INCOME BUYS</text>' % MUTED,
         legend(56, 400),
         '<text x="56" y="542" font-family="JetBrains Mono, Menlo, monospace" font-size="12" fill="%s" letter-spacing="1.5">UNITED STATES — YEARS OF INCOME, SAME COLOURS</text>' % MUTED,
         '<text x="56" y="564" font-family="JetBrains Mono, Menlo, monospace" font-size="13" fill="%s">no floor area is published for US counties, so no m² there</text>' % MUTED,
         '<text x="56" y="586" font-family="JetBrains Mono, Menlo, monospace" font-size="13" fill="%s">data: ESPON HOUSE4ALL · US Census Bureau ACS · Freddie Mac</text>' % MUTED,
         '<text x="56" y="76" font-family="JetBrains Mono, Menlo, monospace" font-size="14" fill="#8b7cff" letter-spacing="2">AVGREBENKIN.COM / RESEARCH</text>',
         '</svg>']
    return '\n'.join(s)


def cover_page():
    W, H = 1600, 560
    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H),
         '<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG),
         # Два кадра во всю ширину, без единого слова: Европа слева, США справа.
         map_svg('eu', 40, -20, 560, 600, 700),
         map_svg('na', 640, 10, 920, 540, 700),
         '</svg>']
    return '\n'.join(s)


def main():
    p1 = os.path.join(HERE, 'cover.svg'); open(p1, 'w', encoding='utf-8').write(cover())
    p2 = os.path.join(HERE, 'cover-page.svg'); open(p2, 'w', encoding='utf-8').write(cover_page())
    png1 = os.path.join(HERE, 'cover.png'); png2 = os.path.join(HERE, 'cover-page.png')
    subprocess.check_call(['rsvg-convert', '-w', '1200', '-h', '630', '-o', png1, p1])
    subprocess.check_call(['rsvg-convert', '-w', '1600', '-h', '560', '-o', png2, p2])
    subprocess.check_call(['magick', png1, '-quality', '86', os.path.join(IMG, 'housing.jpg')])
    subprocess.check_call(['cwebp', '-quiet', '-q', '82', png1, '-o', os.path.join(IMG, 'housing.webp')])
    subprocess.check_call(['cwebp', '-quiet', '-q', '82', png2, '-o', os.path.join(IMG, 'housing-page.webp')])
    os.remove(png1); os.remove(png2)
    for f in ('housing.jpg', 'housing.webp', 'housing-page.webp'):
        print(f, os.path.getsize(os.path.join(IMG, f)), 'байт')


if __name__ == '__main__':
    main()
