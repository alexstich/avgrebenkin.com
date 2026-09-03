#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка страницы «Find your city» на всех языках.

    python3 research/cities/src/build.py            # все языки
    python3 research/cities/src/build.py en ru      # только эти

Что откуда:
  strings/<l>.json — 170 переводимых строк на язык плюс шапка (код, направление
                     письма, самоназвание, локаль);
  page.tmpl, page.css, page.js — разметка, стили и поведение, общие для всех.

Данные (303 города, координаты) лежат внутри page.js и от языка не зависят:
названия городов и стран везде латиницей, как в источниках.

Английский кладётся в research/cities/, остальные — в подпапки по коду языка.
"""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUTDIR = os.path.normpath(os.path.join(HERE, '..'))
SITE = 'https://avgrebenkin.com'
BASE = '/research/cities/'
DEFAULT = 'en'
ORDER = ['en', 'ru', 'uk', 'de', 'fr', 'es', 'pt-BR', 'it', 'nl', 'pl', 'tr', 'ja', 'zh-Hans']

HEAD_KEYS = ('lang', 'dir', 'endonym', 'htmlLocale')


LD_TYPE = 'Dataset'      # чем страница представлена в разметке
LD_ANCHOR = '#dataset'


def path_for(code):
    return BASE if code == DEFAULT else BASE + code + '/'


def render_hreflang(langs):
    out = ''.join('<link rel="alternate" hreflang="%s" href="%s%s">\n' % (c, SITE, path_for(c))
                  for c in ORDER if c in langs)
    return out + '<link rel="alternate" hreflang="x-default" href="%s%s">' % (SITE, BASE)


def render_og_alt(code, langs):
    """og:locale:alternate на все прочие языки — Open Graph не знает hreflang."""
    return '\n'.join('<meta property="og:locale:alternate" content="%s">' % langs[c]['htmlLocale']
                     for c in ORDER if c in langs and c != code)


def render_ld_translations(code, langs):
    """Кто здесь оригинал, а кто перевод: английский — канон, прочие 12 — его версии.

    Без этого поисковик видит тринадцать похожих страниц и решает сам, какая
    первична; hreflang говорит только о равноправии языков, но не о родстве.
    """
    if code == DEFAULT:
        items = ',\n'.join(
            '      { "@type": "%s", "@id": "%s%s%s", "inLanguage": "%s" }'
            % (LD_TYPE, SITE, path_for(c), LD_ANCHOR, c)
            for c in ORDER if c in langs and c != DEFAULT)
        return '"workTranslation": [\n%s\n    ],' % items
    return ('"translationOfWork": { "@type": "%s", "@id": "%s%s%s", '
            '"inLanguage": "%s" },' % (LD_TYPE, SITE, path_for(DEFAULT), LD_ANCHOR, DEFAULT))


def render_langpicker(L, code, langs):
    """Список языков на нативном <details>: работает и без скрипта."""
    items = ''.join(
        '<li%s><a href="%s" hreflang="%s" lang="%s"%s>%s</a></li>'
        % (' class="is-current"' if c == code else '', path_for(c), c, c,
           ' aria-current="true"' if c == code else '', html.escape(langs[c]['endonym']))
        for c in ORDER if c in langs)
    return ('<details class="langpick"><summary aria-label="%s"><span class="globe" '
            'aria-hidden="true">◍</span>%s</summary><ul>%s</ul></details>'
            % (html.escape(L['langGroup']), html.escape(L['endonym']), items))


def attr_keys(tmpl):
    """Ключи, которые шаблон подставляет внутрь HTML-атрибута.

    В каталоге строки нарочно несут разметку (<b>, <a href>, &nbsp;) и в текст
    страницы идут как есть. Но те же строки бывают заголовком, alt-текстом или
    aria-label, и там кавычка в переводе рвала бы тег — значит, экранируем.
    """
    out = set()
    for m in re.finditer(r'=\s*"[^"]*"', tmpl):
        out.update(re.findall(r'\{\{(\w+)\}\}', m.group(0)))
    return out


def build(code, langs):
    L = langs[code]
    tmpl = open(os.path.join(HERE, 'page.tmpl'), encoding='utf-8').read()
    css = open(os.path.join(HERE, 'page.css'), encoding='utf-8').read().rstrip('\n')
    js = open(os.path.join(HERE, 'page.js'), encoding='utf-8').read().rstrip('\n')

    # строки внутри скрипта — только как JSON-литералы, никакой склейки руками
    js = re.sub(r'\{\{js:(\w+)\}\}',
                lambda m: json.dumps(L[m.group(1)], ensure_ascii=False), js)

    url = SITE + path_for(code)
    inattr = attr_keys(tmpl)
    fields = {k: (html.escape(v) if k in inattr and isinstance(v, str) else v)
              for k, v in L.items()}
    fields.update({
        'css': css, 'js': js,
        'up': '../' if code == DEFAULT else '../../',
        'canonical': url,
        'hreflang': render_hreflang(langs),
        'ogLocaleAlt': render_og_alt(code, langs),
        'ldTranslations': render_ld_translations(code, langs),
        'langpicker': render_langpicker(L, code, langs),
        'printUrl': url.replace('https://', ''),
        'ldTitle': json.dumps(L['htmlTitle'], ensure_ascii=False)[1:-1],
        'ldName': json.dumps(L['title'], ensure_ascii=False)[1:-1],
        'ldDescription': json.dumps(L['ldDescription'], ensure_ascii=False)[1:-1],
        'ldDatasetName': json.dumps(L['ldDatasetName'], ensure_ascii=False)[1:-1],
        'ldDatasetDescription': json.dumps(L['ldDatasetDescription'], ensure_ascii=False)[1:-1],
        'locale': L['htmlLocale'],
        'transNote': ('<p class="transnote">%s</p>' % L['transNote']) if L['transNote'] else '',
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
    langs = {c: json.load(open(os.path.join(HERE, 'strings', c + '.json'), encoding='utf-8'))
             for c in avail}
    ref = set(langs[DEFAULT])
    for c, L in langs.items():
        miss, extra = ref - set(L), set(L) - ref
        if miss or extra:
            raise SystemExit('%s: не хватает %s, лишние %s' % (c, sorted(miss)[:8], sorted(extra)[:8]))
    os.chdir(ROOT)
    for c in want:
        if c not in langs:
            raise SystemExit('нет strings/%s.json' % c)
        p, n = build(c, langs)
        print('%-8s %-42s %6d байт' % (c, os.path.relpath(p, ROOT), n))


if __name__ == '__main__':
    main()
