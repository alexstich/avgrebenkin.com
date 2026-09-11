#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка страницы «Anything that writes back» на всех языках.

    python3 research/wiki-incident/src/build.py            # все языки
    python3 research/wiki-incident/src/build.py en ru       # только эти

Что откуда:
  structure.json   — то, что не переводится: голоса и цвета, площадки,
                     типы, фазы и события, связи расхождений, адреса ссылок;
  strings/<l>.json — то, что переводится;
  page.tmpl, page.css, page.js — оболочка, стили и поведение, общие для всех.

Английский кладётся в research/wiki-incident/, остальные — в подпапки по коду
языка. Разметка получается полной: вся проза лежит в HTML, поэтому страница
читается и без скрипта. Устроено так же, как соседнее исследование про взлом.
"""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUTDIR = os.path.normpath(os.path.join(HERE, '..'))
SITE = 'https://avgrebenkin.com'
BASE = '/research/wiki-incident/'
DEFAULT = 'en'
ORDER = ['en', 'ru', 'uk', 'de', 'fr', 'es', 'pt-BR', 'it', 'nl', 'pl', 'tr', 'ja', 'zh-Hans']

S = json.load(open(os.path.join(HERE, 'structure.json'), encoding='utf-8'))
SRC = {s['id']: s for s in S['sources']}
KIND = {k['id']: k for k in S['kinds']}


# ── мелкая разметка внутри строк ────────────────────────────────────────────

def rich(s):
    """Экранирование плюс капля разметки: **жирное**, `моноширинное` и <em>.
    <em> оставлен живым тегом — он есть в подзаголовке; больше HTML быть не должно."""
    s = re.sub(r'<em>(.+?)</em>', '\x00\x01\\1\x00\x02', s, flags=re.S)
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s, flags=re.S)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = s.replace('\x00\x01', '<em>').replace('\x00\x02', '</em>')
    return s


def chunks(s):
    return [x.strip() for x in re.split(r'\n\s*\n', s.strip()) if x.strip()]


def paras(s):
    return ''.join('<p>%s</p>' % rich(x) for x in chunks(s))


def fill(tpl, **kw):
    for k, v in kw.items():
        tpl = tpl.replace('{%s}' % k, str(v))
    return tpl


def walk(node, path=''):
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, path + '.' + k if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, '%s.%d' % (path, i))


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


# ── метки времени ───────────────────────────────────────────────────────────

def fmt_day(L, iso):
    y, m, d = iso.split('-')
    return fill(L['dateFormat'], d=int(d), m=L['months'][int(m) - 1])


def fmt_ts(L, ev):
    if 'd2' in ev:
        m1, d1 = ev['d'].split('-')[1:]
        m2, d2 = ev['d2'].split('-')[1:]
        if m1 == m2:
            return fill(L['dateRangeSameMonth'], d1=int(d1), d2=int(d2), m=L['months'][int(m1) - 1])
        return fill(L['dateRange'], full1=fmt_day(L, ev['d']), full2=fmt_day(L, ev['d2']))
    date = fmt_day(L, ev['d'])
    if 't' in ev:
        return fill(L['timeFormat'], date=date, t=ev['t'])
    return date


# ── единицы и подписи площадок ──────────────────────────────────────────────

UNIT_KEY = {'rev': 'ui.unitRev', 'link': 'ui.unitLink', 'paste': 'ui.unitPaste',
            'pkg': 'ui.unitPkg', 'doc': 'ui.unitDoc'}


def site_when(L, s):
    if 'from' in s and 'to' in s:
        return fmt_ts(L, {'d': s['from'], 'd2': s['to']}) if s['from'] != s['to'] else fmt_day(L, s['from'])
    return '—'


def voice_dots(ids):
    return ('<span class="dots" aria-hidden="true">'
            + ''.join('<i class="%s"></i>' % SRC[i]['cls'] for i in ids) + '</span>')


# ── куски страницы ──────────────────────────────────────────────────────────

def render_numbers(L):
    cells = ''.join('<div class="num"><b>%s</b><span>%s</span></div>'
                    % (rich(L.at('numbers.%s.value' % n['id'])),
                       rich(L.at('numbers.%s.caption' % n['id'])))
                    for n in S['numbers'])
    return '<div class="nums">%s</div>' % cells


def render_intro(L):
    out = ''.join(paras(x['t']).replace('<p>', '<p><b>%s</b> ' % rich(x['h']), 1)
                  for x in L.at('intro.full'))
    return '<div class="prose">%s</div>' % out


def render_legend(L):
    cards = []
    for s in S['sources']:
        i = s['id']
        cards.append(
            '<article class="lg %s"><p class="lgrole">%s</p><p class="lgname">%s</p>'
            '<p class="lgdoc">%s</p></article>'
            % (s['cls'], rich(L.at('voices.%s.role' % i)), rich(L.at('voices.%s.name' % i)),
               rich(L.at('voices.%s.doc' % i))))
    return '<div class="legend">%s</div>' % ''.join(cards)


def render_channels(L):
    blocks = []
    for k in S['kinds']:
        kid = k['id']
        sites = sorted([s for s in S['sites'] if s['kind'] == kid],
                       key=lambda s: -s['edits'])
        total_edits = sum(s['edits'] for s in sites)
        rows = []
        for s in sites:
            unit = rich(L.at(UNIT_KEY[s['unit']]))
            by = (rich(L.at('ui.foundAuthors')) if s['by'] == 'authors'
                  else rich(L.at('ui.foundCommunity'))
                       + (' · ' + html.escape(s['finder']) if s.get('finder') else ''))
            meta = fill(rich(L.at('ui.byLine')),
                        edits='<b>%d</b>' % s['edits'], units=s['units'], unit=unit,
                        when=site_when(L, s))
            rows.append(
                '<li class="site%s"><span class="shost">%s</span>'
                '<span class="smeta">%s</span><span class="sby">%s</span></li>'
                % (' site-new' if s['by'] != 'authors' else '',
                   html.escape(s['host']), meta, by))
        toggle = fill(rich(L.at('ui.sitesToggle')), n=len(sites))
        blocks.append(
            '<details class="chan">\n'
            '  <summary class="chan-head">\n'
            '    <span class="chan-num">%s</span>\n'
            '    <span class="chan-main"><span class="chan-name">%s</span>'
            '<span class="chan-trick">%s</span></span>\n'
            '    <span class="chan-count"><b>%d</b><span>%s</span></span>\n'
            '    <span class="chev" aria-hidden="true">▾</span>\n'
            '  </summary>\n'
            '  <div class="chan-body">\n'
            '    <p class="chan-how"><span class="rw-read">GET</span>'
            '<span class="rw-arrow" aria-hidden="true">→</span>'
            '<span class="rw-write">%s</span></p>\n'
            '    <div class="prose chan-ex">%s</div>\n'
            '    <p class="chan-toggle">%s</p>\n'
            '    <ul class="sites">%s</ul>\n'
            '  </div>\n'
            '</details>\n'
            % (k['num'], rich(L.at('kinds.%s.name' % kid)),
               rich(L.at('kinds.%s.trick' % kid)),
               total_edits, rich(L.at('ui.editsWord')),
               rich(L.at('kinds.%s.how' % kid)),
               paras(L.at('kinds.%s.example' % kid)),
               toggle, ''.join(rows)))
    return '<div class="channels">%s</div>' % ''.join(blocks)


def render_step(L, ev):
    T = L.at('events.' + ev['id'])
    ids = ev['who']
    cls = 'step ' + SRC[ids[0]]['cls']
    badges = ''.join('<span class="badge %s">%s</span>'
                     % (SRC[i]['cls'], rich(L.at('voices.%s.name' % i))) for i in ids)
    return (
        '<details class="%s" id="%s" open>\n'
        '  <summary class="step-head">\n'
        '    <span class="step-ts">%s</span>\n'
        '    %s\n'
        '    <h4 class="step-title">%s</h4>\n'
        '    <p class="step-sum">%s</p>\n'
        '    <span class="step-foot">%s</span>\n'
        '    <span class="chev" aria-hidden="true">▾</span>\n'
        '  </summary>\n'
        '  <div class="step-body"><div class="step-inner">%s</div></div>\n'
        '</details>\n'
    ) % (cls, ev['id'], rich(fmt_ts(L, ev)), voice_dots(ids),
         rich(T['title']), rich(T['summary']), badges, paras(T['summary']))


def render_trail(L):
    out = []
    for ph in S['phases']:
        P = L.at('phases.' + ph['id'])
        evs = [e for e in S['events'] if e['phase'] == ph['id']]
        out.append(
            '<section class="act" id="%s" aria-labelledby="%s-t">\n'
            '  <div class="act-head">\n'
            '    <span class="act-num">%s</span>\n'
            '    <h3 id="%s-t">%s</h3>\n'
            '    <p class="act-dates">%s</p>\n'
            '    <p class="act-lede">%s</p>\n'
            '  </div>\n%s</section>\n'
            % (ph['id'], ph['id'],
               fill(rich(L.at('ui.phaseLabel')), n=ph['num']), ph['id'],
               rich(P['title']),
               fmt_ts(L, {'d': ph['from'], 'd2': ph['to']}),
               rich(P['lede']),
               ''.join(render_step(L, e) for e in evs)))
    return ''.join(out)


def render_divergences(L):
    blocks = []
    for i, d in enumerate(S['divergences'], 1):
        T = L.at('divergences.' + d['id'])
        voices = ''.join(
            '<div class="voice %s"><span class="who">%s</span>%s</div>'
            % (SRC[sid]['cls'], rich(L.at('voices.%s.name' % sid)), paras(txt))
            for sid, txt in zip(d['voices'], T['voices']))
        blocks.append(
            '<article class="dv"><span class="dvnum">%02d</span>'
            '<h3>%s</h3>%s<div class="why"><p><b class="lbl">%s</b> %s</p></div></article>'
            % (i, rich(T['title']), voices, rich(L.at('ui.whyLabel')), rich(T['why'])))
    return '<div class="dvlist">%s</div>' % ''.join(blocks)


def render_facts(L):
    cards = []
    for f in S['facts']:
        T = L.at('facts.' + f['id'])
        cards.append(
            '<article class="fact%s"><p class="hook">%s</p><h3>%s</h3>'
            '%s<p class="fwhy">%s %s</p></article>'
            % (' wide' if f['wide'] else '', rich(T['hook']), rich(T['title']),
               paras(T['text']), rich(L.at('ui.factWhyPrefix')), rich(T['why'])))
    return '<div class="facts">%s</div>' % ''.join(cards)


def render_unconf(L):
    items = ''.join('<li>%s</li>' % rich(L.at('unconf.' + u)) for u in S['unconfirmed'])
    return ('<div class="h2note">%s</div><ul class="unconf">%s</ul>'
            % (paras(L.at('unconfNote')), items))


def render_sources(L):
    rows = []
    for item in S['sourceList']['primary']:
        n, url = item['n'], item['url']
        rows.append('<li class="tag-%s"><span class="n">%02d</span><span>'
                    '<a href="%s" target="_blank" rel="noopener">%s</a>'
                    '<span class="sd">%s</span></span></li>'
                    % (item['src'], n, url, rich(L.at('sourceList.primary.%d' % n)),
                       html.escape(url, quote=False)))
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


# ── краткая версия ──────────────────────────────────────────────────────────

def plain(s):
    s = re.sub(r'</?em>', '', s)
    s = re.sub(r'`([^`]+)`', r'\1', s)
    return re.sub(r'\*\*(.+?)\*\*', r'\1', s, flags=re.S)


def tldr_parts(L, url):
    nums = [(L.at('numbers.%s.value' % n['id']), L.at('numbers.%s.caption' % n['id']))
            for n in S['numbers']]
    divs = [L.at('divergences.%s.title' % d['id']) for d in S['divergences']]
    head = [L.at('page.title'), L.at('page.subtitle'), L.at('page.gist')]
    hn, hd = L.at('sections.numbers.h'), L.at('sections.divergences.h')

    html_out = (
        '<h3>%s</h3><p class="tldr-sub">%s</p>%s'
        '<h4>%s</h4><ul class="tldr-nums">%s</ul>'
        '<h4>%s</h4><ol class="tldr-divs">%s</ol>'
        '<p class="tldr-src">%s</p>'
        '<p class="tldr-link">%s <a href="%s">%s</a></p>'
        % (rich(head[0]), rich(head[1]), paras(head[2]),
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
        ['# %s' % plain(L.at('page.title')), '', '*%s*' % plain(L.at('page.subtitle')), '',
         plain(L.at('page.gist')), '', '## %s' % plain(hn), '']
        + ['- **%s** — %s' % (plain(v), plain(c)) for v, c in nums]
        + ['', '## %s' % plain(hd), '']
        + ['%d. %s' % (i, plain(t)) for i, t in enumerate(divs, 1)]
        + ['', plain(L.at('page.sourcesLine')), '', '%s <%s>' % (plain(L.at('ui.tldrFull')), url)])

    return html_out, text, md


# ── метаданные и языки ───────────────────────────────────────────────────────

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
            '      { "@type": "Article", "@id": "%s%s#article", "inLanguage": "%s" }'
            % (SITE, path_for(c), c)
            for c in ORDER if c in langs and c != DEFAULT)
        return '"workTranslation": [\n%s\n    ],' % items if items else ''
    return ('"translationOfWork": { "@type": "Article", "@id": "%s%s#article", '
            '"inLanguage": "%s" },' % (SITE, path_for(DEFAULT), DEFAULT))


# ── сборка ──────────────────────────────────────────────────────────────────

def build(code, langs):
    L = langs[code]
    tmpl = open(os.path.join(HERE, 'page.tmpl'), encoding='utf-8').read()
    css = open(os.path.join(HERE, 'page.css'), encoding='utf-8').read()
    js = open(os.path.join(HERE, 'page.js'), encoding='utf-8').read()

    index = {'phases': [{'id': p['id'], 'num': p['num'],
                         'title': L.at('phases.%s.title' % p['id']),
                         'dates': fmt_ts(L, {'d': p['from'], 'd2': p['to']})} for p in S['phases']],
             'kinds': [{'id': k['id'], 'num': k['num'],
                        'name': L.at('kinds.%s.name' % k['id'])} for k in S['kinds']],
             'sites': [{'id': s['id'], 'name': s['name'], 'host': s['host'],
                        'kind': s['kind'], 'edits': s['edits'], 'units': s['units'],
                        'unit': L.at(UNIT_KEY[s['unit']]),
                        'new': s['by'] != 'authors',
                        'when': site_when(L, s),
                        'by': (L.at('ui.foundAuthors') if s['by'] == 'authors'
                               else L.at('ui.foundCommunity')
                               + (' · ' + s['finder'] if s.get('finder') else ''))}
                       for s in S['sites']],
             'ui': {'mapPlay': L.at('ui.mapPlay'), 'mapPause': L.at('ui.mapPause'),
                    'mapReplay': L.at('ui.mapReplay'), 'mapCount': L.at('ui.mapCount'),
                    'editsWord': L.at('ui.editsWord'),
                    'foundCommunity': L.at('ui.foundCommunity')}}

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
        'syText': rich(L.at('ui.syText')), 'syCta': rich(L.at('ui.syCta')),
        'backToResearch': rich(L.at('ui.backToResearch')),
        'title': rich(L.at('page.title')),
        'subtitle': rich(L.at('page.subtitle')),
        'gist': paras(L.at('page.gist')),
        'date': rich(L.at('page.date')),
        'sourcesLine': rich(L.at('page.sourcesLine')),
        'scaleLine': rich(L.at('page.scaleLine')),
        'utcHint': rich(L.at('ui.utcHint')),
        'trailGroup': html.escape(L.at('ui.trailGroup')),
        'hNumbers': rich(L.at('sections.numbers.h')),
        'hWhat': rich(L.at('sections.what.h')),
        'hChannels': rich(L.at('sections.channels.h')),
        'nChannels': paras(L.at('sections.channels.note')),
        'hMap': rich(L.at('sections.map.h')), 'nMap': paras(L.at('sections.map.note')),
        'mapPlay': html.escape(L.at('ui.mapPlay')), 'mapHint': rich(L.at('ui.mapHint')),
        'mapLegendSize': rich(L.at('ui.mapLegendSize')),
        'hTrail': rich(L.at('sections.trail.h')), 'nTrail': paras(L.at('sections.trail.note')),
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
        'channels': render_channels(L), 'trail': render_trail(L),
        'divergences': render_divergences(L), 'facts': render_facts(L),
        'unconf': render_unconf(L), 'sources': render_sources(L),
    }
    out = tmpl
    for k, v in fields.items():
        out = out.replace('{{%s}}' % k, str(v))
    left = re.findall(r'\{\{(\w+)\}\}', out)
    if left:
        raise SystemExit('%s: не подставлено %s' % (code, sorted(set(left))))

    d = OUTDIR if code == DEFAULT else os.path.join(OUTDIR, code)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(out)
    return os.path.join(d, 'index.html'), len(out)


def main():
    avail = sorted(f[:-5] for f in os.listdir(os.path.join(HERE, 'strings')) if f.endswith('.json'))
    want = sys.argv[1:] or [c for c in ORDER if c in avail]
    langs = {c: Lang(c) for c in avail}

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
