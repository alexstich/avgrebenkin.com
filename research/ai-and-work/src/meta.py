# -*- coding: utf-8 -*-
"""Сверяет метаданные всех тринадцати собранных страниц.

    python3 research/ai-and-work/src/meta.py

Проверяет набор мета-тегов, полноту hreflang и og:locale:alternate, совпадение
canonical с og:url и headline с og:title, локаль и язык страницы, наличие
workTranslation у оригинала и translationOfWork у переводов. Отдельно ловит
подпись обложки, пережившую смену картинки: og:image:alt описывает картинку,
и после новой обложки он остаётся старым молча.
"""
import glob, html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REQ = ['description', 'og:title', 'og:description', 'og:image', 'og:image:alt', 'og:url',
       'og:type', 'og:locale', 'og:site_name', 'twitter:card', 'twitter:title',
       'twitter:description', 'twitter:image', 'author', 'robots',
       'article:published_time', 'article:modified_time']
LOCALE = {'en': 'en_US', 'ru': 'ru_RU', 'uk': 'uk_UA', 'de': 'de_DE', 'fr': 'fr_FR',
          'es': 'es_ES', 'pt-BR': 'pt_BR', 'it': 'it_IT', 'nl': 'nl_NL', 'pl': 'pl_PL',
          'tr': 'tr_TR', 'ja': 'ja_JP', 'zh-Hans': 'zh_CN'}
# Фразы прежней обложки: если подпись всё ещё их содержит, её забыли переписать.
STALE = ['twelve months in the most exposed occupations, by age']


def check(path):
    s = open(path, encoding='utf-8').read()
    code = os.path.basename(os.path.dirname(path))
    if code == os.path.basename(ROOT):
        code = 'en'
    metas = {m.group(1): html.unescape(m.group(2)) for m in
             re.finditer(r'<meta[^>]*(?:name|property)="([^"]+)"[^>]*content="([^"]*)"', s)}
    p = []
    miss = [k for k in REQ if not metas.get(k, '').strip()]
    if miss:
        p.append('нет: ' + ', '.join(miss))
    langs = re.findall(r'<link rel="alternate" hreflang="([^"]+)"', s)
    if len(langs) != 14 or 'x-default' not in langs:
        p.append('hreflang %d, ожидалось 14' % len(langs))
    if len(re.findall(r'og:locale:alternate', s)) != 12:
        p.append('og:locale:alternate не 12')
    canon = re.search(r'<link rel="canonical" href="([^"]+)"', s)
    if not canon:
        p.append('нет canonical')
    elif canon.group(1) != metas.get('og:url'):
        p.append('canonical ≠ og:url')
    if metas.get('og:locale') != LOCALE.get(code):
        p.append('og:locale %s' % metas.get('og:locale'))
    ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S).group(1))
    art = {n['@type']: n for n in ld['@graph']}['Article']
    if art['headline'] != metas.get('og:title'):
        p.append('headline ≠ og:title')
    if art.get('inLanguage') != code:
        p.append('inLanguage %s' % art.get('inLanguage'))
    key = 'workTranslation' if code == 'en' else 'translationOfWork'
    if key not in art:
        p.append('нет ' + key)
    if code == 'en' and len(art.get('workTranslation', [])) != 12:
        p.append('workTranslation не 12')
    for phrase in STALE:
        if phrase in metas.get('og:image:alt', ''):
            p.append('og:image:alt описывает прежнюю обложку')
    return code, p


def main():
    files = sorted(glob.glob(os.path.join(ROOT, 'index.html')) +
                   glob.glob(os.path.join(ROOT, '*', 'index.html')))
    bad = 0
    for f in files:
        code, p = check(f)
        print('%-9s %s' % (code, '; '.join(p) if p else 'полный набор, всё сходится'))
        bad += len(p)
    print('проблем:', bad)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
