#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка страницы «How many square metres can you afford?».

    python3 research/housing/src/build.py

Что откуда:
  strings/<l>.json — всё, что переводится: метаданные, проза страницы (t.*),
                    короткая версия (t.tldr), интерфейс (t.ui) и строки, которые
                    рисует скрипт (js). Английский — канон, остальные от него;
  tldr.js — окно короткой версии, одно на все языки;
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
BASE = '/research/housing/'
DEFAULT = 'en'
ORDER = ['en', 'ru', 'uk', 'de', 'fr', 'es', 'pt-BR', 'it', 'nl', 'pl', 'tr', 'ja', 'zh-Hans']

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


def render_langpicker(L, code, langs):
    """Список языков — на нативном <details>: работает и без скрипта."""
    items = ''.join(
        '<li%s><a href="%s" hreflang="%s" lang="%s"%s>%s</a></li>'
        % (' class="is-current"' if c == code else '', path_for(c), c, c,
           ' aria-current="true"' if c == code else '', html.escape(langs[c]['endonym']))
        for c in ORDER if c in langs)
    return ('<details class="langpick"><summary aria-label="%s"><span class="globe" '
            'aria-hidden="true">◍</span>%s</summary><ul>%s</ul></details>'
            % (html.escape(L['t']['ui']['langGroup']), html.escape(L['endonym']), items))


def render_og_alt(code, langs):
    return '\n'.join('<meta property="og:locale:alternate" content="%s">' % langs[c]['htmlLocale']
                     for c in ORDER if c in langs and c != code)


def render_ld_translations(code, langs):
    """Кто оригинал, а кто перевод: hreflang говорит только о равноправии языков."""
    if code == DEFAULT:
        items = ', '.join('{ "@type": "WebPage", "@id": "%s%s#webpage", "inLanguage": "%s" }'
                          % (SITE, path_for(c), c) for c in ORDER if c in langs and c != DEFAULT)
        return '"workTranslation": [ %s ],' % items if items else ''
    return ('"translationOfWork": { "@type": "WebPage", "@id": "%s%s#webpage", "inLanguage": "%s" },'
            % (SITE, path_for(DEFAULT), DEFAULT))


def at(L, path):
    cur = L['t']
    for part in path.split('.'):
        if part not in cur:
            raise SystemExit('%s: нет строки t.%s' % (L['lang'], path))
        cur = cur[part]
    return cur


def plain(s):
    """Строка каталога без разметки — для буфера обмена."""
    s = re.sub(r'<[^>]+>', '', s)
    return html.unescape(s)


def md(s):
    s = re.sub(r'</?b>', '**', s)
    s = re.sub(r'</?i>', '*', s)
    return plain(s)


def tldr_parts(L, url):
    bul = [at(L, 'tldr.b%d' % i) for i in range(1, 8)]
    text = '\n\n'.join([plain(L['title']), plain(at(L, 'tldr.sub'))]
                        + ['— ' + plain(b) for b in bul]
                        + [plain(at(L, 'tldr.src')), '%s %s' % (plain(at(L, 'tldr.full')), url)])
    md_out = '\n'.join(['# %s' % L['title'], '', '*%s*' % md(at(L, 'tldr.sub')), '']
                        + ['- %s' % md(b) for b in bul]
                        + ['', md(at(L, 'tldr.src')), '', '%s <%s>' % (md(at(L, 'tldr.full')), url)])
    return text, md_out


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
    out['statOtherCurve'] = str(len(espon) - int(out['statOwnCurve']))
    return out


# Разделитель разрядов по языку — тот же, что даёт Intl.NumberFormat в
# скрипте страницы, чтобы число в прозе и число на карте выглядели одинаково.
# Испанский и польский четырёхзначные не делят (у Intl minimumGroupingDigits 2).
GROUP = {'en': ',', 'ja': ',', 'zh-Hans': ',', 'de': '.', 'es': '.', 'it': '.', 'nl': '.',
         'pt-BR': '.', 'tr': '.', 'ru': ' ', 'uk': ' ', 'pl': ' ', 'fr': ' '}
LATAM_META = os.path.join(ROOT, 'research', 'data', 'latam-meta.json')
# Проза называет период словами, а не подстановкой: «четвёртый квартал 2025»
# склоняется по-своему в каждом языке. Поэтому новый выпуск данных обязан
# остановить сборку, пока текст не перечитан.
LATAM_PERIODS = {'PE': [2025, 4], 'AR': [2019, 2]}


def num(code, L, v, dec=0):
    s = '%.*f' % (dec, v)
    whole, _, frac = s.partition('.')
    neg = whole.startswith('-')
    whole = whole.lstrip('-')
    g = GROUP[code]
    if not (code in ('es', 'pl') and len(whole) <= 4):
        parts = []
        while len(whole) > 3:
            parts.insert(0, whole[-3:]); whole = whole[:-3]
        whole = g.join([whole] + parts)
    return ('-' if neg else '') + whole + (L['decimal'] + frac if frac else '')


def latam_fields(code, L, T, data, geo):
    la = data.get('latam')
    if not la:
        raise SystemExit('data.json: нет слоя latam — запустить data.py')
    for cc, want in LATAM_PERIODS.items():
        if la[cc]['period'] != want:
            raise SystemExit('latam %s: период данных %s, а текст написан про %s — перечитать прозу'
                             % (cc, la[cc]['period'], want))
    pe, ar = la['PE']['rows'], la['AR']['rows']
    lo = lambda rows, i: min(rows, key=lambda r: r[i])
    hi = lambda rows, i: max(rows, key=lambda r: r[i])
    oe = {r[0]: r for r in la['oecd']}
    cl = oe['Chile'][4]
    pct = lambda v: num(code, L, v * 100, 1)
    out = {
        'latPeW': geo['latam']['PE']['w'], 'latPeH': geo['latam']['PE']['h'],
        'latArW': geo['latam']['AR']['w'], 'latArH': geo['latam']['AR']['h'],
        'latPeN': str(len(pe)), 'latArN': str(len(ar)),
        'latArAll': str(len(geo['latam']['AR']['paths'])),
        'latArMiss': str(len(la['AR'].get('gaps') or {})),
        'latPeLo': num(code, L, lo(pe, 1)[1]), 'latPeLoName': lo(pe, 1)[0],
        'latPeHi': num(code, L, hi(pe, 1)[1]), 'latPeHiName': hi(pe, 1)[0],
        'latPeRentLo': num(code, L, lo(pe, 2)[2], 1), 'latPeRentLoName': lo(pe, 2)[0],
        'latPeRentHi': num(code, L, hi(pe, 2)[2], 1), 'latPeRentHiName': hi(pe, 2)[0],
        'latRate': num(code, L, la['PE']['rate'], 2),
        'latArLo': num(code, L, lo(ar, 1)[1]), 'latArLoName': lo(ar, 1)[0],
        'latArHi': num(code, L, hi(ar, 1)[1]), 'latArHiName': hi(ar, 1)[0],
        'latClShare': pct(oe['Chile'][2]), 'latClYear': str(oe['Chile'][1]),
        'latCl2020': pct(dict(cl)[2020]),
        'latCoShare': pct(oe['Colombia'][2]), 'latCoYear': str(oe['Colombia'][1]),
        'latCrShare': pct(oe['Costa Rica'][2]), 'latCrYear': str(oe['Costa Rica'][1]),
        'latMxShare': pct(oe['Mexico'][2]), 'latMxYear': str(oe['Mexico'][1]),
    }
    # Таблица OECD — статикой, чтобы цифры были на странице и без скрипта;
    # график поверх неё берёт имена стран отсюда же (data-cc), чтобы у страны
    # было одно имя, а не два из разных словарей.
    ISO = {'Chile': 'CL', 'Colombia': 'CO', 'Costa Rica': 'CR', 'Mexico': 'MX'}
    rows = []
    for r in la['oecd']:
        cc = ISO[r[0]]
        rows.append('<tr data-cc="%s"><th scope="row">%s</th><td>%s</td><td>%s</td><td>%s</td></tr>'
                    % (cc, at(L, 'latam.c' + cc), r[1], T['units']['pct'].replace('{n}', pct(r[2])),
                       at(L, 'latam.gross' if r[3] == 'gross' else 'latam.disposable')))
    out['latOecdRows'] = ''.join(rows)
    # Атрибуция — из latam-meta.json: имена источников, адреса и лицензии как их
    # записал извлекатель. Словарь даёт только подписи вокруг них.
    meta = json.load(open(LATAM_META, encoding='utf-8'))
    ly, gm = meta['layers'], meta['geo']
    a = lambda href, text: '<a href="%s" target="_blank" rel="noopener">%s</a>' % (html.escape(href, quote=True), html.escape(text))
    lic = lambda m: at(L, 'latam.a07').replace('{licence}', a(m['licence_url'], m['licence']))
    quote = lambda m: at(L, 'latam.a07').replace('{licence}', a(m['licence_url'], at(L, 'latam.a10').replace('{q}', m['licence'])))
    items = [
        (at(L, 'latam.a01'), a(ly['PE']['url'], ly['PE']['source']), quote(ly['PE'])),
        (at(L, 'latam.a02'), a(ly['PE']['url'], ly['PE']['source'] + ', ' + ly['PE']['rate_series']), quote(ly['PE'])),
        (at(L, 'latam.a03'), a(ly['AR']['url'], ly['AR']['source']), lic(ly['AR'])),
        (at(L, 'latam.a04'), a(ly['OECD']['url'], ly['OECD']['source'] + ' (' + ly['OECD']['indicator'] + ')'), lic(ly['OECD'])),
        (at(L, 'latam.a05'), a(gm['PE']['url'], gm['PE']['source']), lic(gm['PE']) + ' ' + at(L, 'latam.a08')),
        (at(L, 'latam.a06'), a(gm['AR']['url'], gm['AR']['source']), lic(gm['AR']) + ' ' + at(L, 'latam.a09')),
    ]
    out['latAttrib'] = ''.join('<li><b>%s</b> %s. %s</li>' % it for it in items)
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
    # Строки интерфейса, которые рисует сам скрипт: карточка, сравнение, легенда.
    T = L.get('js')
    if T is None and os.path.exists(os.path.join(HERE, 'strings', 'js-' + code + '.json')):
        T = json.load(open(os.path.join(HERE, 'strings', 'js-' + code + '.json'), encoding='utf-8'))
    js = js.replace('{{i18n}}', json.dumps(T or {}, ensure_ascii=False, separators=(',', ':')))
    js = js.replace('{{data}}', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    js = js.replace('{{geo}}', json.dumps(geo, ensure_ascii=False, separators=(',', ':')))
    # </script> внутри строки данных закрыл бы тег раньше времени
    js = js.replace('</script', '<\\/script')

    url = SITE + path_for(code)
    # Проза каталога: {{t:раздел.ключ}} — HTML как есть, {{ta:…}} — в атрибут.
    # Внутри строк бывают свои подстановки ({{statSale50}}, {{up}}), поэтому
    # эта замена идёт первой, а общая — после неё.
    # Пустая строка внутри значения — новый абзац (AUTHORING §3). Работает только
    # там, где строка и так целиком занимает <p> или <dd>: абзац в абзац не вложишь.
    def para(m):
        tag, attrs, val = m.group(1), m.group(2), at(L, m.group(3))
        parts = [x.strip() for x in re.split(r'\n\s*\n', val) if x.strip()]
        # Абзац с id (подсказка, которую переписывает скрипт) не размножается:
        # два элемента с одним id — это уже ошибка разметки.
        if len(parts) < 2 or ' id=' in attrs:
            return '<%s%s>%s</%s>' % (tag, attrs, ' '.join(parts) if parts else val, tag)
        if tag == 'dd':
            return '<dd%s>%s</dd>' % (attrs, ''.join('<p>%s</p>' % x for x in parts))
        return '\n'.join('<%s%s>%s</%s>' % (tag, attrs, x, tag) for x in parts)
    tmpl = re.sub(r'<(p|dd)((?:\s[^>]*)?)>\{\{t:([\w.-]+)\}\}</\1>', para, tmpl)
    tmpl = re.sub(r'\{\{t:([\w.-]+)\}\}', lambda m: at(L, m.group(1)), tmpl)
    tmpl = re.sub(r'\{\{ta:([\w.-]+)\}\}', lambda m: html.escape(plain(at(L, m.group(1))), quote=True), tmpl)
    text, md_out = tldr_parts(L, url)
    tl = {'copied': plain(at(L, 'ui.copied')), 'copyManual': plain(at(L, 'ui.copyManual')),
          'text': text, 'md': md_out}
    tldrjs = open(os.path.join(HERE, 'tldr.js'), encoding='utf-8').read().rstrip('\n')
    tldrjs = tldrjs.replace('{{tldrI18n}}', json.dumps(tl, ensure_ascii=False).replace('</', '<\\/'))
    note = at(L, 'ui.translationNote')
    inattr = attr_keys(tmpl)
    fields = {k: (html.escape(v) if k in inattr and isinstance(v, str) else v) for k, v in L.items()
              if isinstance(v, str)}
    fields.update(ICONS)
    fields.update(stats(data))
    fields.update(latam_fields(code, L, T or {}, data, geo))
    fields.update({
        'css': css, 'js': js,
        'up': '../' if code == DEFAULT else '../../',
        'canonical': url,
        'hreflang': render_hreflang(langs),
        'ogLocaleAlt': render_og_alt(code, langs),
        'ldTranslations': render_ld_translations(code, langs),
        'langpicker': render_langpicker(L, code, langs),
        'translationNote': '<p class="fine transnote">%s</p>' % note if note else '',
        'tldrjs': tldrjs,
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
    avail = sorted(f[:-5] for f in os.listdir(os.path.join(HERE, 'strings')) if f.endswith('.json') and not f.startswith('js-'))
    unknown = [c for c in avail if c not in ORDER]
    if unknown:
        raise SystemExit('язык не объявлен в ORDER: %s' % ', '.join(unknown))
    want = sys.argv[1:] or [c for c in ORDER if c in avail]
    langs = {c: json.load(open(os.path.join(HERE, 'strings', c + '.json'), encoding='utf-8')) for c in avail}
    os.chdir(ROOT)
    for c in want:
        p, n = build(c, langs)
        print('%-8s %-42s %7d байт' % (c, os.path.relpath(p, ROOT), n))


if __name__ == '__main__':
    main()
