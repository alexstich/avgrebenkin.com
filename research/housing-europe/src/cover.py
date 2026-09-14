#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Обложки страницы из самих данных: карта NUTS 3 в пяти классах статьи.

    python3 research/housing-europe/src/cover.py

Пишет два SVG рядом и растрирует их через rsvg-convert и cwebp:
  cover.svg       → images/research/housing-europe.jpg   1200×630, с английским заголовком,
                    для карточки на индексе и соцсетей (+ .webp для карточки)
  cover-page.svg  → images/research/housing-europe-page.webp 1600×560, без единого слова,
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


def project(lat, lon):
    """Та же проекция, что в geo.py, в те же экранные единицы: обложка обязана
    совпадать с картой на странице, а не жить своей геометрией."""
    p, l = math.radians(lat), math.radians(lon)
    p0, l0 = math.radians(geo['lat0']), math.radians(geo['lon0'])
    k = math.sqrt(2 / (1 + math.sin(p0) * math.sin(p) + math.cos(p0) * math.cos(p) * math.cos(l - l0)))
    x = k * math.cos(p) * math.sin(l - l0)
    y = k * (math.cos(p0) * math.sin(p) - math.sin(p0) * math.cos(p) * math.cos(l - l0))
    minx, maxx, miny, maxy = geo['box']
    scale = geo['w'] / (maxx - minx)
    return (x - minx) * scale, (maxy - y) * scale


def map_svg(x0, y0, w, h):
    """Карта в прямоугольнике (x0, y0, w, h): страны заливкой, города точками —
    как на странице. Контуров уровня региона больше нет, см. geo.py."""
    sc = min(w / geo['w'], h / geo['h'])
    out = ['<g transform="translate(%.1f %.1f) scale(%.4f)">' % (x0 + (w - geo['w'] * sc) / 2, y0 + (h - geo['h'] * sc) / 2, sc)]
    cval = {c['c']: c['sa'] for c in data['countries']}
    for cc, d in geo['countries'].items():
        k = cls(cval.get(cc, 0))
        fill = RAMP[k] if k >= 0 else ND
        out.append('<path d="%s" fill="%s" fill-opacity="0.8" stroke="%s" stroke-width="%.2f"/>' % (d, fill, BG, 0.6 / sc))
    # Точки — самые населённые места; порядок в data['places'] уже по населению.
    F = data['placefields']
    ip, ilat, ilon, isp = F.index('pop'), F.index('lat100'), F.index('lon100'), F.index('sp')
    icc, iinc = F.index('cc'), F.index('inc')
    rates = {i: c.get('rate') or 0 for i, c in enumerate(data['countries'])}
    for a in data['places'][:900]:
        if not a[isp]:
            continue
        x, y = project(a[ilat] / 100.0, a[ilon] / 100.0)
        r = max(2.6, min(11.0, math.sqrt(a[ip]) / 130.0))
        k = cls(afford(a[iinc], a[isp], rates.get(a[icc], 0)))
        out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" stroke-width="%.2f"/>'
                   % (x, y, r, RAMP[k] if k >= 0 else ND, BG, 0.8 / sc))
    out.append('</g>')
    return ''.join(out)


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
         map_svg(560, 20, 640, 600),
         '<text x="56" y="150" font-family="Space Grotesk, Inter, system-ui, sans-serif" font-size="52" font-weight="700" fill="%s" letter-spacing="-1.5">How many</text>' % INK,
         '<text x="56" y="208" font-family="Space Grotesk, Inter, system-ui, sans-serif" font-size="52" font-weight="700" fill="%s" letter-spacing="-1.5">square metres</text>' % INK,
         '<text x="56" y="266" font-family="Space Grotesk, Inter, system-ui, sans-serif" font-size="52" font-weight="700" fill="%s" letter-spacing="-1.5">can you afford?</text>' % INK,
         '<text x="56" y="318" font-family="Inter, system-ui, sans-serif" font-size="19" fill="%s">Your income against 22 million listings</text>' % MUTED,
         '<text x="56" y="346" font-family="Inter, system-ui, sans-serif" font-size="19" fill="%s">in 8,489 European towns — buy or rent.</text>' % MUTED,
         legend(56, 400),
         '<text x="56" y="560" font-family="JetBrains Mono, Menlo, monospace" font-size="13" fill="%s">m² a third of the average income buys on a 30-year mortgage</text>' % MUTED,
         '<text x="56" y="582" font-family="JetBrains Mono, Menlo, monospace" font-size="13" fill="%s">data: Sielker &amp; Banabak 2026, TU Wien · ESPON HOUSE4ALL</text>' % MUTED,
         '<text x="56" y="76" font-family="JetBrains Mono, Menlo, monospace" font-size="14" fill="#8b7cff" letter-spacing="2">AVGREBENKIN.COM / RESEARCH</text>',
         '</svg>']
    return '\n'.join(s)


def cover_page():
    W, H = 1600, 560
    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H),
         '<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG),
         map_svg(0, -140, W, 840),
         '</svg>']
    return '\n'.join(s)


def main():
    p1 = os.path.join(HERE, 'cover.svg'); open(p1, 'w', encoding='utf-8').write(cover())
    p2 = os.path.join(HERE, 'cover-page.svg'); open(p2, 'w', encoding='utf-8').write(cover_page())
    png1 = os.path.join(HERE, 'cover.png'); png2 = os.path.join(HERE, 'cover-page.png')
    subprocess.check_call(['rsvg-convert', '-w', '1200', '-h', '630', '-o', png1, p1])
    subprocess.check_call(['rsvg-convert', '-w', '1600', '-h', '560', '-o', png2, p2])
    subprocess.check_call(['magick', png1, '-quality', '86', os.path.join(IMG, 'housing-europe.jpg')])
    subprocess.check_call(['cwebp', '-quiet', '-q', '82', png1, '-o', os.path.join(IMG, 'housing-europe.webp')])
    subprocess.check_call(['cwebp', '-quiet', '-q', '82', png2, '-o', os.path.join(IMG, 'housing-europe-page.webp')])
    os.remove(png1); os.remove(png2)
    for f in ('housing-europe.jpg', 'housing-europe.webp', 'housing-europe-page.webp'):
        print(f, os.path.getsize(os.path.join(IMG, f)), 'байт')


if __name__ == '__main__':
    main()
