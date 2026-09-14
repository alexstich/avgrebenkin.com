#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка страницы «How many square metres can you afford?».

    python3 research/housing-europe/src/build.py

Что откуда:
  strings/en.json — заголовки и метаданные страницы; пока один язык, но каркас
                    тот же, что у соседних исследований, чтобы переводы легли
                    без перестройки;
  page.tmpl, page.css, page.js — разметка, стили и поведение;
  data.json — датасет (см. data.py), geo.json — контуры (см. geo.py).

Данные вшиваются в скрипт литералами DATA и GEO: страница открывается по file://
и не делает ни одного запроса. Доли населения по классам, которые упоминает
текст, считаются здесь же из data.json и подставляются как {{statSale50}} и
т. п. — чтобы цифры в прозе не могли разойтись с диаграммой.
"""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUTDIR = os.path.normpath(os.path.join(HERE, '..'))
SITE = 'https://avgrebenkin.com'
BASE = '/research/housing-europe/'
DEFAULT = 'en'
ORDER = ['en']

ICONS = {
    'svgShare': '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="18" cy="5" r="2.6"/><circle cx="6" cy="12" r="2.6"/><circle cx="18" cy="19" r="2.6"/><path d="M8.4 10.8 15.6 6.4M8.4 13.2l7.2 4.4"/></svg>',
    'svgPng': '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="3.2" y="5" width="17.6" height="14" rx="2.4"/><circle cx="8.6" cy="10" r="1.5"/><path d="m4.4 16.6 4.4-4 3.4 3 3-2.6 4.4 4"/></svg>',
    'svgDl': '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 4v10.4"/><path d="m7.6 10.6 4.4 4.4 4.4-4.4"/><path d="M4.8 19.2h14.4"/></svg>',
    'svgPrint': '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M7 9V3.8h10V9"/><path d="M7 17.5H4.6v-6A2.4 2.4 0 0 1 7 9h10a2.4 2.4 0 0 1 2.4 2.4v6H17"/><path d="M7 14.4h10v5.8H7z"/></svg>',
    'svgCsv': '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M5 4h9l5 5v11H5z"/><path d="M14 4v5h5"/><path d="M8 13h8M8 16.5h8"/></svg>',
}


def path_for(code):
    return BASE if code == DEFAULT else BASE + code + '/'


def render_hreflang(langs):
    out = ''.join('<link rel="alternate" hreflang="%s" href="%s%s">\n' % (c, SITE, path_for(c))
                  for c in ORDER if c in langs)
    return out + '<link rel="alternate" hreflang="x-default" href="%s%s">' % (SITE, BASE)


def stats(data):
    """Доли населения 31 страны по классам, в процентах с одним знаком."""
    total = data['popTotal'] / 1e6
    out = {}
    for tenure, key in (('sale', 'Sale'), ('rent', 'Rent')):
        h = data['hist'][tenure]
        out['stat%s50' % key] = '%.0f' % (sum(h[0]) / total * 100)
        out['stat%s75' % key] = '%.0f' % (sum(h[1]) / total * 100)
        out['stat%sNd' % key] = '%.0f' % (sum(h[5]) / total * 100)
    sz = data.get('size') or {}
    own = sz.get('own') or []
    espon = [c for c in data['countries'] if c.get('espon')]
    out['statOwnCurve'] = str(len([c for c in own if any(e['c'] == c for e in espon)]))
    out['statCountries'] = str(len(espon))
    return out


def attr_keys(tmpl):
    out = set()
    for m in re.finditer(r'=\s*"[^"]*"', tmpl):
        out.update(re.findall(r'\{\{(\w+)\}\}', m.group(0)))
    return out


def build(code, langs):
    L = langs[code]
    tmpl = open(os.path.join(HERE, 'page.tmpl'), encoding='utf-8').read()
    css = open(os.path.join(HERE, 'page.css'), encoding='utf-8').read().rstrip('\n')
    js = open(os.path.join(HERE, 'page.js'), encoding='utf-8').read().rstrip('\n')
    data = json.load(open(os.path.join(HERE, 'data.json'), encoding='utf-8'))
    geo = json.load(open(os.path.join(HERE, 'geo.json'), encoding='utf-8'))

    js = re.sub(r'\{\{js:(\w+)\}\}', lambda m: json.dumps(L[m.group(1)], ensure_ascii=False), js)
    js = js.replace('{{data}}', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    js = js.replace('{{geo}}', json.dumps(geo, ensure_ascii=False, separators=(',', ':')))
    # </script> внутри строки данных закрыл бы тег раньше времени
    js = js.replace('</script', '<\\/script')

    url = SITE + path_for(code)
    inattr = attr_keys(tmpl)
    fields = {k: (html.escape(v) if k in inattr and isinstance(v, str) else v) for k, v in L.items()}
    fields.update(ICONS)
    fields.update(stats(data))
    fields.update({
        'css': css, 'js': js,
        'up': '../' if code == DEFAULT else '../../',
        'canonical': url,
        'hreflang': render_hreflang(langs),
        'printUrl': url.replace('https://', ''),
        'ldTitle': json.dumps(L['htmlTitle'], ensure_ascii=False)[1:-1],
        'ldName': json.dumps(L['title'], ensure_ascii=False)[1:-1],
        'ldDescription': json.dumps(L['ldDescription'], ensure_ascii=False)[1:-1],
        'ldDatasetName': json.dumps(L['ldDatasetName'], ensure_ascii=False)[1:-1],
        'ldDatasetDescription': json.dumps(L['ldDatasetDescription'], ensure_ascii=False)[1:-1],
        'locale': L['htmlLocale'],
        # viewBox первого кадра: дальше его переставляет сам скрипт при смене
        # кадра, но разметка обязана быть осмысленной и до выполнения скрипта.
        'geoW': geo['frames'][geo['order'][0]]['w'],
        'geoH': geo['frames'][geo['order'][0]]['h'],
    })

    def sub(m):
        k = m.group(1)
        if k not in fields:
            raise SystemExit('%s: нет строки %s' % (code, k))
        return str(fields[k])
    out = re.sub(r'\{\{([\w]+)\}\}', sub, tmpl)
    left = re.findall(r'\{\{[\w:.]+\}\}', out)
    if left:
        raise SystemExit('%s: не подставлено %s' % (code, sorted(set(left))))

    d = OUTDIR if code == DEFAULT else os.path.join(OUTDIR, code)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(out)
    return os.path.join(d, 'index.html'), len(out)


def main():
    avail = sorted(f[:-5] for f in os.listdir(os.path.join(HERE, 'strings')) if f.endswith('.json'))
    want = sys.argv[1:] or [c for c in ORDER if c in avail]
    langs = {c: json.load(open(os.path.join(HERE, 'strings', c + '.json'), encoding='utf-8')) for c in avail}
    os.chdir(ROOT)
    for c in want:
        p, n = build(c, langs)
        print('%-8s %-42s %7d байт' % (c, os.path.relpath(p, ROOT), n))


if __name__ == '__main__':
    main()
