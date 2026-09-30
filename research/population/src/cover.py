#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Обложки исследования: cover.svg (карточка и og:image, 1200×630, со словами)
и cover-page.svg (шапка страницы, 1600×560, без единого слова).

    python3 research/population/src/cover.py
    rsvg-convert -w 1200 -h 630 research/population/src/cover.svg -o /tmp/c.png
    cwebp -q 88 /tmp/c.png -o images/research/population.webp
    magick /tmp/c.png -quality 88 images/research/population.jpg
    rsvg-convert -w 1600 -h 560 research/population/src/cover-page.svg -o /tmp/p.png
    cwebp -q 86 /tmp/p.png -o images/research/population-page.webp
    rsvg-convert -w 800 -h 280 research/population/src/cover-page.svg -o /tmp/p8.png
    cwebp -q 84 /tmp/p8.png -o images/research/population-page-800.webp   # телефоны, srcset

Мотив (COVERS.md): восемь полос — сколько лет заняло каждое удвоение населения
мира с 5000 года до н. э., от 1 652 до 37, — и шар из золотых точек, по точке на
миллион человек 2023 года. Всё считается из data.json, как и сама страница.
Фон «космос» #0a0e16, ведущий акцент — бирюза, полосы — тёплый ряд.
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'data.json'), encoding='utf-8'))
Y, W = D['years'], D['world']
BG, INK, MUTE, DIM = '#0a0e16', '#ffffff', '#aeb6c2', '#8a93a0'
TEAL, GOLD = '#2ec4b6', '#ffce3d'
WARM = ['#ff5a3c', '#ff6e30', '#ff8a1e', '#ff9d1c', '#ffb020', '#ffbf2c', '#ffce3d', '#ffe07a']
HEL = 'Helvetica Neue, Helvetica, Arial, sans-serif'


def at(y):
    for i in range(len(Y) - 1):
        if Y[i] <= y <= Y[i + 1]:
            a, b = W[i], W[i + 1]
            return a * (b / a) ** ((y - Y[i]) / (Y[i + 1] - Y[i]))
    return W[-1]


def first(level):
    for i in range(len(Y) - 1):
        a, b = W[i], W[i + 1]
        if a < level <= b:
            return Y[i] + (Y[i + 1] - Y[i]) * math.log(level / a) / math.log(b / a)


def doublings():
    lv, y0, out = at(-5000), -5000, []
    while True:
        y1 = first(2 * lv)
        if y1 is None:
            return out
        out.append((lv, 2 * lv, y0, y1)); lv, y0 = 2 * lv, y1


def fmt(v):
    return '%.0fM' % (v / 1e6) if v < 1e9 else '%.1fB' % (v / 1e9)


def globe(cx, cy, R, a=-62, b=18):
    ca, sa, cb, sb = math.cos(math.radians(a)), math.sin(math.radians(a)), math.cos(math.radians(b)), math.sin(math.radians(b))

    def p(lon, lat):
        l, f = math.radians(lon), math.radians(lat)
        x, y, z = math.cos(f) * math.sin(l), math.sin(f), math.cos(f) * math.cos(l)
        X1, Z1 = x * ca + z * sa, z * ca - x * sa
        return cx + R * X1, cy - R * (y * cb - Z1 * sb), y * sb + Z1 * cb
    o = ['<defs><radialGradient id="sph" cx="38%" cy="34%" r="70%"><stop offset="0" stop-color="#1b2944"/>'
         '<stop offset="1" stop-color="#080d1a"/></radialGradient>'
         '<radialGradient id="halo" r="50%"><stop offset=".78" stop-color="#5a82dc" stop-opacity=".16"/>'
         '<stop offset="1" stop-color="#5a82dc" stop-opacity="0"/></radialGradient></defs>',
         '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="url(#halo)"/>' % (cx, cy, R * 1.28),
         '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="url(#sph)"/>' % (cx, cy, R)]
    for polys in D['shapes'].values():
        for poly in polys:
            for r in poly:
                pts = [p(r[i], r[i + 1]) for i in range(0, len(r), 2)]
                if sum(1 for q in pts if q[2] > 0) < len(pts) * 0.9:
                    continue
                o.append('<path d="M%s Z" fill="#7896d7" fill-opacity=".09" stroke="#96afeb" stroke-opacity=".2" stroke-width=".7"/>'
                         % ' L'.join('%.1f %.1f' % (q[0], q[1]) for q in pts))
    dots = []
    for c, s in D['pop'].items():
        n, d = int(s[-1] / 1e6), D['dots'][c]
        for k in range(min(n, len(d) // 2)):
            x, y, z = p(d[2 * k], d[2 * k + 1])
            if z > 0:
                dots.append('<circle cx="%.1f" cy="%.1f" r="1.25" fill-opacity="%.2f"/>' % (x, y, min(1, .3 + z * 1.4)))
    o.append('<g fill="%s">%s</g>' % (GOLD, ''.join(dots)))
    return '\n'.join(o)


def bars(x0, y0, width, step, h, labels):
    rows, mx, o = doublings(), 0, []
    mx = max(r[3] - r[2] for r in rows)
    for i, (a, b, ya, yb) in enumerate(rows):
        y = y0 + i * step
        w = max(4, (yb - ya) / mx * width)
        bx = x0 + (118 if labels else 0)
        if labels:
            o.append('<text x="%d" y="%.1f" font-family="Menlo, monospace" font-size="13" fill="%s">%s → %s</text>'
                     % (x0, y + h - 3, MUTE, fmt(a), fmt(b)))
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%d" rx="%.1f" fill="%s"/>' % (bx, y, w, h, h / 2, WARM[i]))
        if labels:
            o.append('<text x="%.1f" y="%.1f" font-family="Menlo, monospace" font-size="13" fill="%s">%s yrs</text>'
                     % (bx + w + 8, y + h - 3, INK if i == len(rows) - 1 else MUTE, format(round(yb - ya), ',')))
    return '\n'.join(o)


card = '\n'.join([
    '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">',
    '<rect width="1200" height="630" fill="%s"/>' % BG,
    globe(930, 300, 250),
    '<text font-family="%s" font-size="58" font-weight="800" fill="%s" letter-spacing="-1.8">'
    '<tspan x="56" y="112">Eight billion,</tspan><tspan x="56" y="178" fill="%s">one doubling</tspan>'
    '<tspan x="56" y="244">at a time</tspan></text>' % (HEL, INK, TEAL),
    '<rect x="56" y="270" width="70" height="5" rx="2.5" fill="%s"/>' % TEAL,
    '<text x="56" y="316" font-family="%s" font-size="22" fill="%s">How long did humanity take to double?</text>' % (HEL, MUTE),
    '<text x="56" y="360" font-family="Menlo, monospace" font-size="12" fill="%s" letter-spacing="1.5">'
    'WORLD POPULATION DOUBLED, 5000 BCE → 2023</text>' % MUTE,
    bars(56, 376, 330, 25, 15, True),
    '<text x="56" y="604" font-family="Menlo, monospace" font-size="13" fill="%s" letter-spacing="1">avgrebenkin.com/research</text>' % DIM,
    '</svg>'])
page = '\n'.join([
    '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="560" viewBox="0 0 1600 560">',
    '<rect width="1600" height="560" fill="%s"/>' % BG,
    globe(1180, 280, 250),
    bars(140, 96, 620, 48, 26, False),
    '</svg>'])
open(os.path.join(HERE, 'cover.svg'), 'w').write(card + '\n')
open(os.path.join(HERE, 'cover-page.svg'), 'w').write(page + '\n')
print('\n'.join('%s→%s %d..%d %d' % (fmt(a), fmt(b), ya, yb, yb - ya) for a, b, ya, yb in doublings()))
