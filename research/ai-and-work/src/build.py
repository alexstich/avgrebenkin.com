#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка страницы «The door didn't close. It narrowed.» на всех языках.

    python3 research/ai-and-work/src/build.py            # все языки
    python3 research/ai-and-work/src/build.py en ru      # только эти

Что откуда:
  occupations.json — 825 профессий с занятостью, прогнозом, медианной оплатой,
                     категорией экспозиции и составом по полу; не переводится;
  strings/<l>.json — то, что переводится: проза, интерфейс, источники;
  page.tmpl, page.css, page.js — оболочка, стили и поведение, общие для всех.

Английский кладётся в research/ai-and-work/, остальные — в подпапки по коду
языка. Названия профессий остаются английскими на всех языках: это официальные
имена SOC, по которым читатель ищет себя, и в каталоге городов имена городов
живут ровно так же.
"""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUTDIR = os.path.normpath(os.path.join(HERE, '..'))
SITE = 'https://avgrebenkin.com'
BASE = '/research/ai-and-work/'
DEFAULT = 'en'                       # язык на базовом адресе
ORDER = ['en', 'ru', 'uk', 'de', 'fr', 'es', 'pt-BR', 'it', 'nl', 'pl', 'tr', 'ja', 'zh-Hans']
LD_TYPE, LD_ANCHOR = 'Article', '#article'

DATA = json.load(open(os.path.join(HERE, 'occupations.json'), encoding='utf-8'))

# Строки, которые уезжают в скрипт: он рисует карточки, плитки и подписи сам.
JS_KEYS = [
    'ages', 'cats', 'catsGen', 'catsHead', 'na', 'numLocale', 'thousands', 'millions',
    'wordWomen', 'wordWomenNom', 'wordMen', 'wordMenNom', 'sexAny', 'sexWoman', 'sexMan',
    'cExposure', 'cExposureNote', 'cProjected', 'cProjectedNote',
    'cEmployed', 'cEmployedNote', 'cTasks', 'cTasksNote',
    'cWomen', 'cWomenPlain', 'cWomenMajority', 'cWomenMinority',
    'yAge', 'yAgeNote', 'yWhere', 'yWhereNote', 'afterPlot',
    'tileAria', 'tileLine', 'tileWomen', 'groupCount', 'groupLargest',
    'copied', 'copyManual',
]


# ── мелкая разметка внутри строк ────────────────────────────────────────────

def rich(s):
    """Экранирование плюс та капля разметки, что есть в текстах: **жирное**,
    *курсив* и [сноска](3). Больше в переводах ничего быть не должно."""
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s, flags=re.S)
    s = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'\[\^(\d+)\]', r'<sup><a href="#s\1">\1</a></sup>', s)
    return s


def chunks(s):
    """Строка, разбитая пустыми строками, — это несколько абзацев. Место
    разрыва остаётся за каждым языком: где по-английски одна длинная мысль,
    по-немецки может быть две."""
    return [x.strip() for x in re.split(r'\n\s*\n', s.strip()) if x.strip()]


def paras(s):
    return '\n  '.join('<p>%s</p>' % rich(x) for x in chunks(s))


def plain(s):
    """Та же строка без разметки — для буфера обмена и печати."""
    s = re.sub(r'\[\^(\d+)\]', '', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'\1', s, flags=re.S)
    return re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'\1', s)


def md(s):
    """Markdown: сноски на печатной странице не нужны, ударения остаются."""
    return re.sub(r'\[\^(\d+)\]', '', s)


def fill(tpl, **kw):
    for k, v in kw.items():
        tpl = tpl.replace('{%s}' % k, str(v))
    return tpl


class Lang(dict):
    """Строки одного языка с проверкой: отсутствующий ключ — ошибка сборки,
    а не тихо пустое место на странице."""
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


# ── числа ───────────────────────────────────────────────────────────────────

def dec(L, s):
    """Десятичный разделитель языка. Знак минуса везде U+2212, как в тексте."""
    return s.replace('.', L['decimal'])


# ── служебные куски ─────────────────────────────────────────────────────────

def path_for(code):
    return BASE if code == DEFAULT else BASE + code + '/'


def render_langpicker(L, code, langs):
    """Список языков — на нативном <details>: работает и без скрипта."""
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
    """og:locale:alternate на все прочие языки — Open Graph не знает hreflang."""
    return '\n'.join('<meta property="og:locale:alternate" content="%s">' % langs[c]['htmlLocale']
                     for c in ORDER if c in langs and c != code)


def render_ld_translations(code, langs):
    """Кто здесь оригинал, а кто перевод: английский — канон, прочие — версии.

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


# ── короткая версия ─────────────────────────────────────────────────────────

def tldr_parts(L, url):
    """Простой текст и Markdown короткой версии — из тех же строк, что стоят
    в окне. Второй копии, которая разъедется с первой, здесь нет."""
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


# ── сборка ──────────────────────────────────────────────────────────────────

def build(code, langs):
    L = langs[code]
    tmpl = open(os.path.join(HERE, 'page.tmpl'), encoding='utf-8').read()
    css = open(os.path.join(HERE, 'page.css'), encoding='utf-8').read()
    js = open(os.path.join(HERE, 'page.js'), encoding='utf-8').read()

    up = '../' if code == DEFAULT else '../../'
    url = SITE + path_for(code)
    text, md_out = tldr_parts(L, url)

    # Строки скрипта размечены так же, как проза: **жирное** и сноски [^1].
    # Скрипт вставляет их через innerHTML, поэтому разметка разворачивается
    # здесь — в каталоге языка HTML не появляется ни у одного исследования.
    def markup(v):
        if isinstance(v, str):
            return rich(v)
        if isinstance(v, list):
            return [markup(x) for x in v]
        if isinstance(v, dict):
            return {k: markup(x) for k, x in v.items()}
        return v

    i18n = {k: markup(L.at('js.' + k)) for k in JS_KEYS}
    # десятичный разделитель и оправа процента общие с разметкой: скрипт
    # рисует те же числа, что стоят в таблицах, и разойтись они не должны
    i18n['decimal'] = L['decimal']
    i18n['percent'] = L.at('ui.percent')
    i18n['up'] = up
    i18n['tldrText'] = text
    i18n['tldrMd'] = md_out

    fixed = {
        'css': css, 'js': js, 'up': up,
        'data': json.dumps(DATA, ensure_ascii=False, separators=(',', ':')),
        'i18n': json.dumps(i18n, ensure_ascii=False, separators=(',', ':')),
        'lang': L['lang'], 'dir': L['dir'], 'locale': L['htmlLocale'],
        'canonical': url,
        'hreflang': render_hreflang(langs),
        'ogLocaleAlt': render_og_alt(code, langs),
        'ldTranslations': render_ld_translations(code, langs),
        'langpicker': render_langpicker(L, code, langs),
        'translationNote': ('<p class="fsrc transnote">%s</p>' % rich(L.at('ui.translationNote'))
                            if L.at('ui.translationNote') else ''),
    }

    def sub(mo):
        key = mo.group(1)
        if key in fixed:
            return fixed[key]
        # Одна и та же строка стоит и в <h1>, и в <meta content="…">, и внутри
        # JSON-LD, а экранирование у этих трёх мест разное. Кто где — решает
        # префикс в шаблоне: сущности HTML внутри JSON-LD не раскрываются, и
        # апостроф заголовка уехал бы в выдачу как &#x27;.
        if key.startswith('a:'):
            return html.escape(L.at(key[2:]), quote=True)
        if key.startswith('j:'):
            return json.dumps(plain(L.at(key[2:])), ensure_ascii=False)[1:-1]
        if key.startswith('m.'):                       # {{m.53.2}} → 53,2 млн
            return fill(L.at('ui.millions'), n=dec(L, key[2:]))
        if key.startswith('pc.'):                      # {{pc.+2.0}} → +2,0 %
            return fill(L.at('ui.percent'), n=dec(L, key[3:]))
        if key.startswith('cats.'):
            return rich(L.at('js.catsHead.' + key[5:]))
        if key.endswith('|p'):
            return paras(L.at(key[:-2]))
        return rich(L.at(key))

    out = re.sub(r'\{\{([a-zA-Z0-9_.|:+−]+)\}\}', sub, tmpl)

    left = re.findall(r'\{\{[^}]{0,40}\}\}', out)
    if left:
        raise AssertionError('%s: остались плейсхолдеры %s' % (code, left[:5]))

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
