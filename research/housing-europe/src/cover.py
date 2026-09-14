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
import json, os, subprocess

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


def map_svg(x0, y0, w, h):
    """Карта, вписанная в прямоугольник (x0, y0, w, h), без Турции и Балкан без данных."""
    sc = min(w / geo['w'], h / geo['h'])
    out = ['<g transform="translate(%.1f %.1f) scale(%.4f)">' % (x0 + (w - geo['w'] * sc) / 2, y0 + (h - geo['h'] * sc) / 2, sc)]
    val = {n[0]: n[7] for n in data['nuts3']}
    for nid, d in geo['nuts3'].items():
        k = cls(val.get(nid, 0))
        fill = RAMP[k] if k >= 0 else ND
        out.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%.2f"/>' % (d, fill, BG, 0.6 / sc))
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
