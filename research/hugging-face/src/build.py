#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка страницы «Три отчёта об одном взломе» на всех языках.

    python3 research/hugging-face/src/build.py            # все языки
    python3 research/hugging-face/src/build.py en ru       # только эти

Что откуда:
  structure.json   — то, что не переводится: связи шагов и актов, статусы,
                     источники, метки времени, адреса ссылок;
  strings/<l>.json — то, что переводится: 470 строк на язык;
  page.tmpl, page.css, page.js — оболочка, стили и поведение, общие для всех.

Английский кладётся в research/hugging-face/, остальные — в подпапки
по коду языка. Разметка получается полной: оба режима чтения и все версии
лежат в HTML, поэтому страница читается и без скрипта.
"""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUTDIR = os.path.normpath(os.path.join(HERE, '..'))
SITE = 'https://avgrebenkin.com'
BASE = '/research/hugging-face/'
DEFAULT = 'en'                       # язык на базовом адресе
ORDER = ['en', 'ru', 'uk', 'de', 'fr', 'es', 'pt-BR', 'it', 'nl', 'pl', 'tr', 'ja', 'zh-Hans']

S = json.load(open(os.path.join(HERE, 'structure.json'), encoding='utf-8'))
SRC = {s['id']: s for s in S['sources']}
STAMP_ORDER = ('consensus', 'divergent', 'single', 'unexplained')


# ── мелкая разметка внутри строк ────────────────────────────────────────────

def rich(s):
    """Экранирование плюс та капля разметки, что есть в текстах: **жирное**
    и `моноширинное`. Больше в переводах ничего быть не должно."""
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s, flags=re.S)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return s


def chunks(s):
    """Строка, разбитая пустыми строками, — это несколько абзацев.

    Переводы — плоские строки JSON, и длинный текст приходил одним абзацем на
    десять строк. Теперь автор ставит внутри строки пустую строку там, где
    мысль кончается, и место разрыва остаётся за каждым языком.
    """
    return [x.strip() for x in re.split(r'\n\s*\n', s.strip()) if x.strip()]


def paras(s):
    return ''.join('<p>%s</p>' % rich(x) for x in chunks(s))


def walk(node, path=''):
    """Все строки каталога с их путями, в порядке объявления."""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, path + '.' + k if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, '%s.%d' % (path, i))


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


# ── метки времени ───────────────────────────────────────────────────────────

def fmt_day(L, iso):
    y, m, d = iso.split('-')
    return fill(L['dateFormat'], d=int(d), m=L['months'][int(m) - 1])


def fmt_ts(L, ts):
    if 'd2' in ts:
        m1, d1 = ts['d'].split('-')[1:]
        m2, d2 = ts['d2'].split('-')[1:]
        if m1 == m2:
            return fill(L['dateRangeSameMonth'], d1=int(d1), d2=int(d2),
                        m=L['months'][int(m1) - 1])
        return fill(L['dateRange'], full1=fmt_day(L, ts['d']), full2=fmt_day(L, ts['d2']))
    date = fmt_day(L, ts['d'])
    if 'w' in ts:
        return fill(L['wordFormat'], date=date, w=L['tsWords'][ts['w']])
    if 't2' in ts:
        return fill(L['timeRangeFormat'], date=date, t=ts['t'], t2=ts['t2'])
    if 't' in ts:
        return fill(L['timeFormat'], date=date, t=ts['t'])
    return date


# ── куски страницы ──────────────────────────────────────────────────────────

def modal(node, tag='p', cls=''):
    """Один и тот же кусок в двух режимах: оба лежат в разметке, лишний
    убирает CSS по data-mode на корне."""
    out = []
    for mode in ('simple', 'full'):
        if not node.get(mode):
            continue
        c = ' class="%s"' % cls if cls else ''
        # абзацем может быть только абзац: у step-sum тег span, внутрь <p> не лезет
        parts = chunks(node[mode]) if tag == 'p' else [node[mode]]
        out.append(''.join('<%s%s data-when="%s">%s</%s>' % (tag, c, mode, rich(x), tag)
                           for x in parts))
    return ''.join(out)


def fork_svg(ids):
    n = len(ids)
    parts = ['<path d="M50 0 V7" fill="none" stroke="var(--border)" stroke-width="1.5" '
             'vector-effect="non-scaling-stroke"/>']
    for i, sid in enumerate(ids):
        x = (i + 0.5) * 100.0 / n
        d = 'M50 7 V22' if abs(x - 50) < 0.01 else 'M50 7 H%.2f V22' % x
        parts.append('<path d="%s" fill="none" stroke="var(--%s)" stroke-width="1.5" '
                     'stroke-linejoin="miter" vector-effect="non-scaling-stroke"/>'
                     % (d, 'src-' + sid))
    return ('<div class="fork" aria-hidden="true"><svg viewBox="0 0 100 22" '
            'preserveAspectRatio="none" focusable="false">%s</svg></div>' % ''.join(parts))


def render_step(L, st):
    T = L.at('steps.' + st['id'])
    ids, status, vers = st['sources'], st['status'], st['versions']
    style, cls = [], ['step']

    if status == 'single' and ids:
        cls.append(SRC[ids[0]]['cls'])
    if vers:
        stops = ['var(--src-%s) %.1f%% %.1f%%' % (s, i * 100.0 / len(vers), (i + 1) * 100.0 / len(vers))
                 for i, s in enumerate(vers)]
        style.append('--rail:linear-gradient(180deg,%s)' % ','.join(stops))
        style.append('--railh:linear-gradient(90deg,%s)' % ','.join(stops))
        style.append('--c1:var(--src-%s);--c1-rgb:var(--src-%s-rgb)' % (vers[0], vers[0]))
        second = vers[1] if len(vers) > 1 else vers[0]
        style.append('--c2:var(--src-%s);--c2-rgb:var(--src-%s-rgb)' % (second, second))

    label = L.at('stamps.' + status)
    if status == 'consensus':
        stamp = ('<span class="stamp">%s</span><span class="consensus-dots" aria-hidden="true">'
                 '<i></i><i></i><i></i></span>' % rich(label))
    else:
        stamp = '<span class="stamp stamp-%s">%s</span>' % (status, rich(label))

    badges = ''.join('<span class="badge %s">%s</span>'
                     % (SRC[i]['cls'], rich(L.at('sourceNames.' + i))) for i in ids)

    body = [modal(T['detail'])]
    if vers:
        body.append(fork_svg(vers))
        cards = []
        for sid, vt in zip(vers, T['versions']):
            cards.append(
                '<div class="version %s"><span class="vsrc">%s</span>'
                '<span class="vlabel">%s</span>%s</div>'
                % (SRC[sid]['cls'],
                   rich(fill(L.at('ui.versionPrefix'), source=L.at('sourceNames.' + sid))),
                   rich(vt['label']), modal(vt['claim'])))
        body.append('<div class="versions" data-n="%d">%s</div>' % (len(vers), ''.join(cards)))

    return (
        '<details class="%s" id="%s" data-level="%s" data-status="%s"%s open>\n'
        '  <summary class="step-head">\n'
        '    <span class="step-ts">%s</span>\n'
        '    <span class="stamp-wrap">%s</span>\n'
        '    <h4 class="step-title">%s</h4>\n'
        '    %s\n'
        '    <span class="step-foot">%s</span>\n'
        '    <span class="chev" aria-hidden="true">▾</span>\n'
        '  </summary>\n'
        '  <div class="step-body"><div class="step-inner">%s</div></div>\n'
        '</details>\n'
    ) % (' '.join(cls), st['id'], st['level'], status,
         (' style="%s"' % ';'.join(style)) if style else '',
         rich(fmt_ts(L, st['ts'])), stamp, rich(T['title']),
         modal(T['summary'], tag='span', cls='step-sum'), badges, ''.join(body))


def render_timeline(L):
    out = []
    for act in S['acts']:
        A = L.at('acts.' + act['id'])
        steps = [s for s in S['steps'] if s['act'] == act['id']]
        out.append(
            '<section class="act" id="%s" aria-labelledby="%s-t">\n'
            '  <div class="act-head">\n'
            '    <span class="act-num">%s</span>\n'
            '    <h3 id="%s-t">%s</h3>\n'
            '    <p class="act-dates">%s</p>\n'
            '    %s\n'
            '  </div>\n%s</section>\n'
            % (act['id'], act['id'],
               rich(L.at('ui.actLabel')).replace('{n}', str(act['num'])), act['id'],
               rich(A['title']), rich(A['dates']),
               modal(A['lede'], cls='act-lede'),
               ''.join(render_step(L, s) for s in steps)))
    return ''.join(out)


def plain(s):
    """Тот же текст без разметки — для буфера в виде простого текста."""
    return re.sub(r'`([^`]+)`', r'\1', re.sub(r'\*\*(.+?)\*\*', r'\1', s, flags=re.S))


def tldr_parts(L, url):
    """Краткая версия статьи: заголовок, вводный абзац, 6 чисел, 5 расхождений.

    Ничего не пишется заново — берутся те же строки, что стоят на странице,
    поэтому пересказ не может разойтись со статьёй и переведён он уже носителем.
    Возвращается тройка: разметка окна, простой текст и Markdown.
    """
    nums = [(L.at('numbers.%s.value' % n['id']), L.at('numbers.%s.caption' % n['id']))
            for n in S['numbers']]
    divs = [L.at('divergences.%s.title' % d['id']) for d in S['divergences']]
    head = [L.at('page.title'), L.at('page.subtitle'), L.at('page.gist')]
    hn, hd = L.at('sections.numbers.h'), L.at('sections.divergences.h')

    html_out = (
        '<h3>%s</h3><p class="tldr-sub">%s</p><p>%s</p>'
        '<h4>%s</h4><ul class="tldr-nums">%s</ul>'
        '<h4>%s</h4><ol class="tldr-divs">%s</ol>'
        '<p class="tldr-src">%s</p>'
        '<p class="tldr-link">%s <a href="%s">%s</a></p>'
        % (rich(head[0]), rich(head[1]), rich(head[2]),
           rich(hn), ''.join('<li><b>%s</b> %s</li>' % (rich(v), rich(c)) for v, c in nums),
           rich(hd), ''.join('<li>%s</li>' % rich(t) for t in divs),
           rich(L.at('page.sourcesLine')),
           rich(L.at('ui.tldrFull')), url, url))

    text = '\n'.join(
        [plain(head[0]), '', plain(head[1]), '', plain(head[2]), '', plain(hn), '']
        + ['%s — %s' % (plain(v), plain(c)) for v, c in nums]
        + ['', plain(hd), '']
        + ['%d. %s' % (i, plain(t)) for i, t in enumerate(divs, 1)]
        + ['', plain(L.at('page.sourcesLine')), '', '%s %s' % (plain(L.at('ui.tldrFull')), url)])

    md = '\n'.join(
        ['# %s' % L.at('page.title'), '', '*%s*' % L.at('page.subtitle'), '',
         L.at('page.gist'), '', '## %s' % hn, '']
        + ['- **%s** — %s' % (v, c) for v, c in nums]
        + ['', '## %s' % hd, '']
        + ['%d. %s' % (i, t) for i, t in enumerate(divs, 1)]
        + ['', L.at('page.sourcesLine'), '', '%s <%s>' % (L.at('ui.tldrFull'), url)])

    return html_out, text, md


def render_numbers(L):
    cells = ''.join('<div class="num"><b>%s</b><span>%s</span></div>'
                    % (rich(L.at('numbers.%s.value' % n['id'])),
                       rich(L.at('numbers.%s.caption' % n['id'])))
                    for n in S['numbers'])
    return '<div class="nums">%s</div>' % cells


def render_intro(L):
    simple = ''.join(paras(p) for p in L.at('intro.simple'))
    full = ''.join(paras(x['t']).replace('<p>', '<p><b>%s</b> ' % rich(x['h']), 1)
                   for x in L.at('intro.full'))
    return ('<div class="prose" data-when="simple">%s</div>'
            '<div class="prose" data-when="full">%s</div>' % (simple, full))


def render_legend(L):
    cards = []
    for s in S['sources']:
        sid = s['id']
        cards.append(
            '<article class="lg %s"><p class="lgrole">%s</p><p class="lgname">%s</p>'
            '<p class="lgdoc">%s</p>%s</article>'
            % (s['cls'], rich(L.at('sourceRoles.' + sid)), html.escape(s['name'], quote=False),
               rich(L.at('sourceDocs.' + sid)),
               ''.join(paras(x) for x in L.at('legend.%s.lines' % sid))))
    return '<div class="legend">%s</div>' % ''.join(cards)


def render_divergences(L):
    blocks = []
    for i, d in enumerate(S['divergences'], 1):
        T = L.at('divergences.' + d['id'])
        voices = ''.join(
            '<div class="voice %s"><span class="who">%s</span>%s</div>'
            % (SRC[sid]['cls'], rich(L.at('sourceNames.' + sid)), paras(txt))
            for sid, txt in zip(d['voices'], T['voices']))
        blocks.append(
            '<article class="dv" data-level="%s"><span class="dvnum">%02d</span>'
            '<h3>%s</h3>%s<div class="why"><p><b class="lbl">%s</b> %s</p></div></article>'
            % (d['level'], i, rich(T['title']), voices,
               rich(L.at('ui.whyLabel')), rich(T['why'])))
    minor = ('<div class="minor"><p class="minor-head">%s</p>%s</div>'
             % (rich(L.at('ui.minorHead')),
                ''.join('<div><b>%s</b>%s</div>'
                        % (rich(L.at('minor.%s.title' % m['id'])),
                           rich(L.at('minor.%s.text' % m['id']))) for m in S['minor'])))
    return '<div class="dvlist">%s%s</div>' % (''.join(blocks), minor)


def render_facts(L):
    cards = []
    for f in S['facts']:
        T = L.at('facts.' + f['id'])
        cards.append(
            '<article class="fact%s" data-level="%s"><p class="hook">%s</p><h3>%s</h3>'
            '%s<p class="fwhy">%s %s</p></article>'
            % (' wide' if f['wide'] else '', f['level'], rich(T['hook']), rich(T['title']),
               paras(T['text']), rich(L.at('ui.factWhyPrefix')), rich(T['why'])))
    return '<div class="facts">%s</div>' % ''.join(cards)


def render_sources(L):
    rows = []
    for item in S['sourceList']['primary']:
        n, url = item['n'], item['url']
        extra = ''
        if 'metr.org/blog' in url:
            extra = ' · ' + ' · '.join(
                '<a href="%s" target="_blank" rel="noopener">%s</a>' % (m['url'], rich(t))
                for m, t in zip(S['sourceList']['mirrors'], L.at('sourceList.mirrors')))
        rows.append('<li class="tag-%s"><span class="n">%02d</span><span>'
                    '<a href="%s" target="_blank" rel="noopener">%s</a>'
                    '<span class="sd">%s%s</span></span></li>'
                    % (item['src'], n, url, rich(L.at('sourceList.primary.%d' % n)),
                       html.escape(url, quote=False), extra))
    out = ('<p class="srchead">%s</p><ul class="srclist">%s</ul>'
           % (rich(L.at('ui.srcPrimary')), ''.join(rows)))

    rows = []
    for item in S['sourceList']['secondary']:
        n, url = item['n'], item['url']
        rows.append('<li><span class="n">%02d</span><span>'
                    '<a href="%s" target="_blank" rel="noopener">%s</a>'
                    '<span class="sd">%s</span></span></li>'
                    % (n, url, rich(L.at('sourceList.secondary.%d' % n)),
                       html.escape(url, quote=False)))
    out += ('<p class="srchead">%s</p><ul class="srclist">%s</ul>'
            % (rich(L.at('ui.srcSecondary')), ''.join(rows)))
    return out


LD_TYPE = 'Article'      # чем страница представлена в разметке
LD_ANCHOR = '#article'


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


# ── сборка ──────────────────────────────────────────────────────────────────

def build(code, langs):
    L = langs[code]
    tmpl = open(os.path.join(HERE, 'page.tmpl'), encoding='utf-8').read()
    css = open(os.path.join(HERE, 'page.css'), encoding='utf-8').read()
    js = open(os.path.join(HERE, 'page.js'), encoding='utf-8').read()

    total = len(S['steps'])
    basic = sum(1 for s in S['steps'] if s['level'] == 'basic')
    index = {'acts': [{'id': a['id'], 'num': a['num'],
                       'title': L.at('acts.%s.title' % a['id']),
                       'dates': L.at('acts.%s.dates' % a['id'])} for a in S['acts']],
             'steps': [{'id': s['id'], 'act': s['act'], 'level': s['level']} for s in S['steps']]}

    up = '../' if code == DEFAULT else '../../'
    tldr_html, tldr_text, tldr_md = tldr_parts(L, SITE + path_for(code))
    fields = {
        'css': css, 'js': js, 'up': up,
        'data': json.dumps(index, ensure_ascii=False, separators=(',', ':')),
        'lang': L['lang'], 'dir': L['dir'], 'locale': L['htmlLocale'],
        'canonical': SITE + path_for(code),
        'hreflang': render_hreflang(langs),
        'ogLocaleAlt': render_og_alt(code, langs),
        'ldTranslations': render_ld_translations(code, langs),
        'langpicker': render_langpicker(L, code, langs),
        'htmlTitle': html.escape(L.at('page.htmlTitle')),
        'metaDescription': html.escape(L.at('page.metaDescription')),
        'ogDescription': html.escape(L.at('page.ogDescription')),
        'imageAlt': html.escape(L.at('page.imageAlt')),
        'ldHeadline': json.dumps(L.at('page.ldHeadline'), ensure_ascii=False)[1:-1],
        'ldAlternative': json.dumps(L.at('page.ldAlternative'), ensure_ascii=False)[1:-1],
        'ldDescription': json.dumps(L.at('page.ldDescription'), ensure_ascii=False)[1:-1],
        'ldName': json.dumps(L.at('page.title'), ensure_ascii=False)[1:-1],
        'crumb': rich(L.at('ui.crumb')),
        'backToResearch': rich(L.at('ui.backToResearch')),
        'title': rich(L.at('page.title')),
        'subtitle': rich(L.at('page.subtitle')),
        'gist': paras(L.at('page.gist')),
        'date': rich(L.at('page.date')),
        'sourcesLine': rich(L.at('page.sourcesLine')),
        'scaleLine': rich(L.at('page.scaleLine')),
        'modeGroup': html.escape(L.at('ui.modeGroup')),
        'modeSimple': rich(L.at('ui.modeSimple')),
        'modeFull': rich(L.at('ui.modeFull')),
        'counterFull': rich(fill(L.at('ui.counterFull'), total=total, shown=basic)),
        'utcHint': rich(L.at('ui.utcHint')),
        'counterSimpleJS': json.dumps(L.at('ui.counterSimple'), ensure_ascii=False),
        'counterFullJS': json.dumps(L.at('ui.counterFull'), ensure_ascii=False),
        'actsGroup': html.escape(L.at('ui.actsGroup')),
        'hNumbers': rich(L.at('sections.numbers.h')),
        'hWhat': rich(L.at('sections.what.h')), 'nWhat': paras(L.at('sections.what.note')),
        'hLegend': rich(L.at('sections.legend.h')), 'nLegend': paras(L.at('sections.legend.note')),
        'hExplorer': rich(L.at('sections.explorer.h')),
        'nExplorer': fill(paras(L.at('sections.explorer.note')).replace('&lt;', '<').replace('&gt;', '>'),
                          keys=L.at('sections.explorer.keys')),
        'hDiv': rich(L.at('sections.divergences.h')), 'nDiv': paras(L.at('sections.divergences.note')),
        'hFacts': rich(L.at('sections.facts.h')), 'nFacts': paras(L.at('sections.facts.note')),
        'hSources': rich(L.at('sections.sources.h')), 'nSources': paras(L.at('sections.sources.note')),
        'disclaimer': rich(L.at('disclaimer')),
        'translationNote': ('<p class="disclaimer transnote">%s</p>' % rich(L.at('ui.translationNote'))
                            if L.at('ui.translationNote') else ''),
        'tldrBody': tldr_html, 'tldrText': json.dumps(tldr_text, ensure_ascii=False),
        'tldrMd': json.dumps(tldr_md, ensure_ascii=False),
        'tldrOpen': rich(L.at('ui.tldrOpen')), 'tldrHead': rich(L.at('ui.tldrHead')),
        'tldrCopyText': rich(L.at('ui.tldrCopyText')), 'tldrCopyMd': rich(L.at('ui.tldrCopyMd')),
        'tldrCopied': json.dumps(L.at('ui.tldrCopied'), ensure_ascii=False),
        'tldrPrint': rich(L.at('ui.tldrPrint')), 'tldrClose': rich(L.at('ui.tldrClose')),
        'numbers': render_numbers(L), 'intro': render_intro(L), 'legend': render_legend(L),
        'timeline': render_timeline(L), 'divergences': render_divergences(L),
        'facts': render_facts(L), 'sources': render_sources(L),
    }
    out = tmpl
    for k, v in fields.items():
        out = out.replace('{{%s}}' % k, str(v))
    left = re.findall(r'\{\{(\w+)\}\}', out)
    if left:
        raise SystemExit('%s: не подставлено %s' % (code, sorted(set(left))))

    # счётчики собирает скрипт, но текст обязан знать про числа
    for name, need in (('counterSimple', ('{shown}', '{total}')),
                       ('counterFull', ('{total}',))):
        tpl = L.at('ui.' + name)
        miss = [p for p in need if p not in tpl]
        if miss:
            raise SystemExit('%s: в %s нет %s' % (code, name, ' '.join(miss)))

    d = OUTDIR if code == DEFAULT else os.path.join(OUTDIR, code)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(out)
    return os.path.join(d, 'index.html'), len(out)


def main():
    avail = sorted(f[:-5] for f in os.listdir(os.path.join(HERE, 'strings')) if f.endswith('.json'))
    want = sys.argv[1:] or [c for c in ORDER if c in avail]
    langs = {c: Lang(c) for c in avail}

    # каждый язык обязан повторять дерево оригинала строка в строку: Lang.at
    # ловит только те ключи, до которых дошла отрисовка, а лишний или потерянный
    # где-нибудь в глубине массива мы иначе заметим уже на живой странице
    ref = [p for p, _ in walk(langs[DEFAULT])]
    for c, L in langs.items():
        got = [p for p, _ in walk(L)]
        if got != ref:
            miss = [p for p in ref if p not in set(got)]
            extra = [p for p in got if p not in set(ref)]
            raise SystemExit('%s: не хватает %s, лишние %s%s'
                             % (c, miss[:5], extra[:5],
                                '' if miss or extra else ', порядок ключей другой'))

    os.chdir(ROOT)
    for c in want:
        if c not in langs:
            raise SystemExit('нет strings/%s.json' % c)
        p, n = build(c, langs)
        print('%-8s %-46s %6d байт' % (c, os.path.relpath(p, ROOT), n))


if __name__ == '__main__':
    main()
