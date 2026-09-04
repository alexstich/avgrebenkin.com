#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Переписывает языковые записи исследований в корневом sitemap.xml.

    python3 research/sitemap.py

У каждого исследования 13 языков, и у каждого адреса должен стоять полный
набор alternate-ссылок на остальные 12 плюс x-default — 39 записей по 14 ссылок.
Руками это не живёт: любой новый язык надо было бы дописать в 39 местах.

Трогается один непрерывный блок: от первого адреса первого исследования из
STUDIES до последнего адреса последнего. Всё остальное в файле — главная,
Speak-Y, /research/ — остаётся как есть. Порядок STUDIES должен совпадать с
порядком блоков в sitemap.xml, иначе вырезанный кусок захватит чужие записи.
"""
import datetime, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://avgrebenkin.com'
ORDER = ['en', 'ru', 'uk', 'de', 'fr', 'es', 'pt-BR', 'it', 'nl', 'pl', 'tr', 'ja', 'zh-Hans']
DEFAULT = 'en'

STUDIES = [
    dict(base='/research/ai-and-work/', dirname='ai-and-work',
         image='/images/research/ai-and-work.jpg',
         title=lambda L: L['page']['htmlTitle']),
    dict(base='/research/cities/', dirname='cities',
         image='/images/research/find-your-city.jpg', title=lambda L: L['htmlTitle']),
    dict(base='/research/hugging-face/', dirname='hugging-face',
         image='/images/research/hugging-face-incident.jpg',
         title=lambda L: L['page']['htmlTitle']),
]


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;')
             .replace('>', '&gt;').replace('"', '&quot;'))


def url_for(base, code):
    return SITE + base + ('' if code == DEFAULT else code + '/')


def blocks(study, day):
    d = os.path.join(ROOT, 'research', study['dirname'], 'src', 'strings')
    langs = {c: json.load(open(os.path.join(d, c + '.json'), encoding='utf-8'))
             for c in ORDER if os.path.exists(os.path.join(d, c + '.json'))}
    alts = ''.join(
        '    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>\n' % (c, url_for(study['base'], c))
        for c in ORDER if c in langs)
    alts += ('    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>\n'
             % url_for(study['base'], DEFAULT))
    out = []
    for c in ORDER:
        if c not in langs:
            continue
        out.append(
            '  <url>\n'
            '    <loc>%s</loc>\n'
            '    <lastmod>%s</lastmod>\n'
            '    <changefreq>yearly</changefreq>\n'
            '    <priority>%s</priority>\n'
            '%s'
            '    <image:image>\n'
            '      <image:loc>%s%s</image:loc>\n'
            '      <image:title>%s</image:title>\n'
            '    </image:image>\n'
            '  </url>'
            % (url_for(study['base'], c), day, '0.8' if c == DEFAULT else '0.6',
               alts, SITE, study['image'], esc(study['title'](langs[c]))))
    return out


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    p = os.path.join(ROOT, 'sitemap.xml')
    s = open(p, encoding='utf-8').read()

    if 'xmlns:xhtml' not in s:
        s = s.replace('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
                      '        xmlns:xhtml="http://www.w3.org/1999/xhtml"', 1)

    # Начало блока ищется от <loc> назад, а не вперёд от точки «минус столько-то
    # символов»: у записей разная длина, и фиксированный отступ рано или поздно
    # промахнётся мимо своего <url>.
    first = s.rindex('<url>', 0, s.index('<loc>%s</loc>' % url_for(STUDIES[0]['base'], DEFAULT)))
    last_loc = url_for(STUDIES[-1]['base'], ORDER[-1])
    last = s.index('</url>', s.index('<loc>%s</loc>' % last_loc)) + len('</url>')

    body = []
    for st in STUDIES:
        body += blocks(st, day)
    s = s[:first] + '\n'.join(body).lstrip() + s[last:]
    open(p, 'w', encoding='utf-8').write(s)
    print('sitemap.xml: %d записей исследований, lastmod %s' % (len(body), day))


if __name__ == '__main__':
    main()
