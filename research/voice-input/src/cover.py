#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Обложки исследования про голосовой ввод: cover.svg (карточка и og:image,
1200×630, с английским заголовком) и cover-page.svg (шапка страницы, 1200×420,
без слов). Мотив один: звуковая волна, которая к правому краю становится тише
и переходит в строки текста. В этом и тезис статьи: голос возвращается, но
всё тише, и на выходе у него текст.

    python3 research/voice-input/src/cover.py      # пишет оба SVG и собирает картинки

Фон — нейтральный чёрный из COVERS.md, весь цвет в мотиве: бирюза (голос)
и золото (текст, клавиатура).
"""
import math, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'images', 'research'))
BG, INK, MUTED, DIM = '#0e1116', '#ffffff', '#aeb6c2', '#6b7480'
TEAL, TEAL2, GOLD, AMBER = '#3fd9bd', '#17c0a6', '#ffce3d', '#ffb020'


def wave(x0, x1, cy, amp, n, seed=7):
    """Столбики волны: огибающая затухает слева направо, внутри — «речь»,
    то есть неровные слоги, а не синусоида."""
    out, w = [], (x1 - x0) / n
    for i in range(n):
        t = i / (n - 1)
        env = (1 - t) ** 1.35 * 0.92 + 0.08
        syl = 0.55 + 0.45 * abs(math.sin(i * 0.61 + seed) * math.cos(i * 0.23 + seed * 0.5))
        h = max(4, amp * env * syl)
        x = x0 + i * w
        col = TEAL if t < 0.55 else TEAL2
        op = 0.95 - 0.45 * t
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" fill="%s" opacity="%.2f"/>'
                   % (x, cy - h / 2, w * 0.56, h, w * 0.28, col, op))
    return '\n  '.join(out)


def lines(x0, y0, widths, gap=22, h=8):
    out = []
    for i, wd in enumerate(widths):
        col = GOLD if i % 3 != 2 else AMBER
        out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="4" fill="%s" opacity="%.2f"/>'
                   % (x0, y0 + i * gap, wd, h, col, 0.95 - i * 0.06))
    return '\n  '.join(out)


def grid(w, h):
    return ('<defs><pattern id="g" width="16" height="16" patternUnits="userSpaceOnUse">'
            '<path d="M16 0H0V16" fill="none" stroke="#ffffff" stroke-opacity=".05"/></pattern></defs>'
            '<rect width="%d" height="%d" fill="url(#g)"/>' % (w, h))


def cover():
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="{BG}"/>
  {grid}
  {wave}
  {lines}
  <text x="72" y="190" font-family="Helvetica Neue, Helvetica, Arial" font-weight="800" font-size="70" letter-spacing="-1.8" fill="{INK}">The quiet</text>
  <text x="72" y="266" font-family="Helvetica Neue, Helvetica, Arial" font-weight="800" font-size="70" letter-spacing="-1.8" fill="{INK}">comeback of <tspan fill="{TEAL}">voice</tspan></text>
  <rect x="72" y="296" width="70" height="5" rx="2.5" fill="{TEAL}"/>
  <text x="72" y="352" font-family="Helvetica Neue, Helvetica, Arial" font-size="23" fill="{MUTED}">Faster, tiring, embarrassing — what do the studies say?</text>
  <text x="72" y="520" font-family="Menlo, monospace" font-size="14.5" letter-spacing="1.5" fill="{DIM}">57 SOURCES · SPEED · FATIGUE · SHYNESS · HABIT</text>
  <text x="72" y="566" font-family="Menlo, monospace" font-size="14.5" letter-spacing="1" fill="{DIM}">avgrebenkin.com/research</text>
</svg>
'''.format(BG=BG, INK=INK, MUTED=MUTED, DIM=DIM, TEAL=TEAL, grid=grid(1200, 630),
           wave=wave(770, 1045, 318, 330, 30),
           lines=lines(1058, 296, [96, 78, 90]))


def cover_page():
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="420" viewBox="0 0 1200 420">
  <rect width="1200" height="420" fill="{BG}"/>
  {grid}
  {wave}
  {lines}
</svg>
'''.format(BG=BG, grid=grid(1200, 420),
           wave=wave(70, 860, 210, 300, 64, seed=3),
           lines=lines(890, 150, [240, 210, 236, 170, 120, 60], gap=26, h=10))


def main():
    a = os.path.join(HERE, 'cover.svg'); open(a, 'w').write(cover())
    b = os.path.join(HERE, 'cover-page.svg'); open(b, 'w').write(cover_page())
    tmp = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'voice-cover.png')
    subprocess.check_call(['rsvg-convert', '-w', '1200', '-h', '630', a, '-o', tmp])
    subprocess.check_call(['cwebp', '-quiet', '-q', '88', tmp, '-o', os.path.join(IMG, 'voice-input.webp')])
    subprocess.check_call(['magick', tmp, '-quality', '88', os.path.join(IMG, 'voice-input.jpg')])
    subprocess.check_call(['rsvg-convert', '-w', '2400', '-h', '840', b, '-o', tmp])
    subprocess.check_call(['cwebp', '-quiet', '-q', '86', '-resize', '1600', '560', tmp, '-o', os.path.join(IMG, 'voice-input-page.webp')])
    print('ok')


if __name__ == '__main__':
    main()
