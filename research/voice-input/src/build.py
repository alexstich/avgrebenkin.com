#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка страницы «The quiet comeback of voice» на всех языках.

    python3 research/voice-input/src/build.py            # все языки
    python3 research/voice-input/src/build.py en ru      # только эти

Что откуда:
  structure.json   — числа графиков и адреса источников; не переводится;
  strings/<l>.json — то, что переводится: проза, подписи, названия источников;
  page.tmpl, page.css, page.js — оболочка, стили и поведение, общие для всех.

Сноски в строках пишутся ключом, а не номером: [^foley]. Номер ставит сборка
по порядку первого появления на готовой странице, и по тому же порядку
собирается список источников. Так переводчику не нужно следить за номерами,
а вставленный посередине абзац не заставляет перенумеровывать всё ниже.
"""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUTDIR = os.path.normpath(os.path.join(HERE, '..'))
SITE = 'https://avgrebenkin.com'
BASE = '/research/voice-input/'
DEFAULT = 'en'
ORDER = ['en', 'ru', 'uk', 'de', 'fr', 'es', 'pt-BR', 'it', 'nl', 'pl', 'tr', 'ja', 'zh-Hans']
LD_TYPE, LD_ANCHOR = 'Article', '#article'

STRUCT = json.load(open(os.path.join(HERE, 'structure.json'), encoding='utf-8'))
SOURCES = STRUCT['sources']

# Метка сноски до нумерации. Символы вне обычного текста, чтобы ни экранирование,
# ни разметка не могли её задеть.
MARK = '⁣{%s}⁣'
MARK_RE = re.compile('⁣\\{([A-Za-z0-9]+)\\}⁣')


# ── мелкая разметка внутри строк ────────────────────────────────────────────

def rich(s):
    """Экранирование плюс та капля разметки, что есть в текстах: **жирное**,
    *курсив* и сноска [^ключ]."""
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s, flags=re.S)
    s = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'\[\^([A-Za-z0-9]+)\]', lambda m: MARK % m.group(1), s)
    return s


def chunks(s):
    return [x.strip() for x in re.split(r'\n\s*\n', s.strip()) if x.strip()]


def paras(s):
    return '\n  '.join('<p>%s</p>' % rich(x) for x in chunks(s))


def plain(s):
    s = re.sub(r'\[\^[A-Za-z0-9]+\]', '', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'\1', s, flags=re.S)
    return re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'\1', s)


def md(s):
    return re.sub(r'\[\^[A-Za-z0-9]+\]', '', s)


class Lang(dict):
    def __init__(self, code):
        p = os.path.join(HERE, 'strings', code + '.json')
        super().__init__(json.load(open(p, encoding='utf-8')))
        self.code = code

    def at(self, path):
        cur = self
        for part in path.split('.'):
            if isinstance(cur, list):
                cur = cur[int(part)]
            else:
                if part not in cur:
                    raise KeyError('%s: нет строки %s' % (self.code, path))
                cur = cur[part]
        return cur


def path_for(code):
    return BASE if code == DEFAULT else BASE + code + '/'


def render_langpicker(L, code, langs):
    items = ''.join(
        '<li%s><a href="%s" hreflang="%s" lang="%s"%s>%s</a></li>'
        % (' class="is-current"' if c == code else '', path_for(c), c, c,
           ' aria-current="true"' if c == code else '', html.escape(langs[c]['endonym']))
        for c in ORDER if c in langs)
    return ('<details class="langpick"><summary aria-label="%s"><span class="globe" '
            'aria-hidden="true">◍</span>%s</summary><ul>%s</ul></details>'
            % (html.escape(L.at('ui.langGroup')), html.escape(L['endonym']), items))


def render_hreflang(langs):
    out = ''.join('<link rel="alternate" hreflang="%s" href="%s%s">\n' % (c, SITE, path_for(c))
                  for c in ORDER if c in langs)
    return out + '<link rel="alternate" hreflang="x-default" href="%s%s">' % (SITE, BASE)


def render_og_alt(code, langs):
    return '\n'.join('<meta property="og:locale:alternate" content="%s">' % langs[c]['htmlLocale']
                     for c in ORDER if c in langs and c != code)


def render_ld_translations(code, langs):
    if code == DEFAULT:
        items = ',\n'.join(
            '      { "@type": "%s", "@id": "%s%s%s", "inLanguage": "%s" }'
            % (LD_TYPE, SITE, path_for(c), LD_ANCHOR, c)
            for c in ORDER if c in langs and c != DEFAULT)
        if not items:
            return ''
        return '"workTranslation": [\n%s\n    ],' % items
    return ('"translationOfWork": { "@type": "%s", "@id": "%s%s%s", '
            '"inLanguage": "%s" },' % (LD_TYPE, SITE, path_for(DEFAULT), LD_ANCHOR, DEFAULT))


def short_url(u):
    u = re.sub(r'^https?://(www\.)?', '', u)
    return u if len(u) <= 60 else u[:57].rstrip('/') + '…'


def tldr_parts(L, url):
    bul = [L.at('tldr.b%d' % i) for i in range(1, 8)]
    head = [L.at('page.title'), L.at('tldr.sub')]
    text = '\n\n'.join([plain(head[0]), plain(head[1])]
                       + ['— ' + plain(b) for b in bul]
                       + [plain(L.at('tldr.src')),
                          '%s %s' % (plain(L.at('tldr.full')), url)])
    md_out = '\n'.join(['# %s' % md(head[0]), '', '*%s*' % md(head[1]), '']
                       + ['- %s' % md(b) for b in bul]
                       + ['', md(L.at('tldr.src')), '',
                          '%s <%s>' % (md(L.at('tldr.full')), url)])
    return text, md_out


def build(code, langs):
    L = langs[code]
    tmpl = open(os.path.join(HERE, 'page.tmpl'), encoding='utf-8').read()
    css = open(os.path.join(HERE, 'page.css'), encoding='utf-8').read()
    js = open(os.path.join(HERE, 'page.js'), encoding='utf-8').read()

    up = '../' if code == DEFAULT else '../../'
    url = SITE + path_for(code)
    text, md_out = tldr_parts(L, url)

    def markup(v):
        if isinstance(v, str):
            return rich(v)
        if isinstance(v, list):
            return [markup(x) for x in v]
        if isinstance(v, dict):
            return {k: markup(x) for k, x in v.items()}
        return v

    i18n = markup(L.at('js'))
    i18n['decimal'] = L['decimal']
    i18n['percent'] = L.at('ui.percent')
    i18n['tldrText'] = text
    i18n['tldrMd'] = md_out

    cited = [k for k in SOURCES]
    fixed = {
        'css': css, 'js': js, 'up': up,
        'data': json.dumps(STRUCT['data'], ensure_ascii=False, separators=(',', ':')),
        'i18n': json.dumps(i18n, ensure_ascii=False, separators=(',', ':')),
        'lang': L['lang'], 'dir': L['dir'], 'locale': L['htmlLocale'],
        'canonical': url,
        'hreflang': render_hreflang(langs),
        'ogLocaleAlt': render_og_alt(code, langs),
        'ldTranslations': render_ld_translations(code, langs),
        'langpicker': render_langpicker(L, code, langs),
        'translationNote': ('<p class="fsrc transnote">%s</p>' % rich(L.at('ui.translationNote'))
                            if L.at('ui.translationNote') else ''),
        'sourceList': '⁣SOURCES⁣',
        'ldCitations': '⁣CITATIONS⁣',
    }

    def sub(mo):
        key = mo.group(1)
        if key in fixed:
            return fixed[key]
        if key.startswith('a:'):
            return html.escape(plain(L.at(key[2:])), quote=True)
        if key.startswith('j:'):
            return json.dumps(plain(L.at(key[2:])), ensure_ascii=False)[1:-1]
        if key.endswith('|p'):
            return paras(L.at(key[:-2]))
        return rich(L.at(key))

    out = re.sub(r'\{\{([a-zA-Z0-9_.|:]+)\}\}', sub, tmpl)

    left = re.findall(r'\{\{[^}]{0,40}\}\}', out)
    if left:
        raise AssertionError('%s: остались плейсхолдеры %s' % (code, left[:5]))

    # Нумерация сносок — по первому появлению в теле страницы. Скрипт строк
    # сносок не несёт: подписи графиков со сносками стоят в разметке.
    order = []
    for k in MARK_RE.findall(out):
        if k not in SOURCES:
            raise AssertionError('%s: сноска на неизвестный источник %s' % (code, k))
        if k not in order:
            order.append(k)
    unused = [k for k in SOURCES if k not in order]
    if unused:
        raise AssertionError('%s: источники без сносок: %s' % (code, ', '.join(unused)))
    num = {k: i + 1 for i, k in enumerate(order)}
    out = MARK_RE.sub(lambda m: '<sup><a href="#src-%s">%d</a></sup>' % (m.group(1), num[m.group(1)]), out)

    items = []
    for k in order:
        links = ' · '.join('<a href="%s">%s</a>' % (html.escape(u, quote=True), html.escape(short_url(u)))
                           for u in SOURCES[k])
        items.append('    <li id="src-%s">%s %s</li>' % (k, rich(L.at('src.' + k)), links))
    out = out.replace('⁣SOURCES⁣', '\n'.join(items))
    out = out.replace('⁣CITATIONS⁣', ', '.join('"%s"' % SOURCES[k][0] for k in order))
    if '⁣' in out:
        raise AssertionError('%s: осталась необработанная метка сноски' % code)

    d = OUTDIR if code == DEFAULT else os.path.join(OUTDIR, code)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, 'index.html')
    open(p, 'w', encoding='utf-8').write(out)
    return p, len(out.encode('utf-8'))


def main():
    avail = sorted(f[:-5] for f in os.listdir(os.path.join(HERE, 'strings')) if f.endswith('.json'))
    unknown = [c for c in avail if c not in ORDER]
    if unknown:
        raise SystemExit('язык не объявлен в ORDER: %s' % ', '.join(unknown))
    langs = {c: Lang(c) for c in avail}

    want = sys.argv[1:] or [c for c in ORDER if c in langs]
    for c in want:
        if c not in langs:
            raise SystemExit('нет strings/%s.json' % c)

    os.chdir(ROOT)
    for c in want:
        p, n = build(c, langs)
        print('%-8s %-46s %d байт' % (c, os.path.relpath(p, ROOT), n))


if __name__ == '__main__':
    main()
