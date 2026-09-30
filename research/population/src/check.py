# -*- coding: utf-8 -*-
"""Сверяет каталог языка с английским: те же ключи, те же подстановки, та же
разметка и те же ссылки. Молчаливая нехватка строки хуже, чем падение сборки.

    python3 research/population/src/check.py          # все языки
    python3 research/population/src/check.py de fr    # только эти

Сверх того: t.ui (кроме примечания переводчика) слово в слово как у жилья (баннер Speak-Y и кнопки «Коротко»
одни на весь раздел, AUTHORING §7), абзац не длиннее 330 знаков (200 в японском
и китайском), htmlTitle до 60 и metaDescription до 155 знаков, в js.big —
числа, а не строки, и цифры английского абзаца встречаются в переводе.
"""
import json, os, re, sys
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'strings')
ORDER = ['ru', 'uk', 'de', 'fr', 'es', 'pt-BR', 'it', 'nl', 'pl', 'tr', 'ja', 'zh-Hans']
CLDR = {'zero', 'one', 'two', 'few', 'many', 'other'}
KEEP = {'lang', 'dir', 'endonym', 'htmlLocale'}


def load(code):
    d = json.load(open(os.path.join(D, code + '.json'), encoding='utf-8'))
    js = os.path.join(D, 'js-' + code + '.json')
    if 'js' not in d and os.path.exists(js):
        d['js'] = json.load(open(js, encoding='utf-8'))
    return d


def is_plural(v):
    return isinstance(v, dict) and v and set(v) <= CLDR


def walk(node, path=''):
    if is_plural(node):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, path + '.' + k if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, '%s.%d' % (path, i))
    else:
        yield path, node


def tags(s):
    """Теги с их атрибутами, без порядка: переводчик вправе переставить
    <b> внутри фразы, но не потерять и не добавить."""
    return sorted(re.findall(r'<(/?[a-z][a-z0-9]*)((?:\s+[\w-]+="[^"]*")*)\s*/?>', s))


def marks(s):
    return (sorted(re.findall(r'\{\{\w+\}\}', s)), sorted(re.findall(r'(?<!\{)\{(\w+)\}(?!\})', s)),
            sorted(re.findall(r'href="([^"]+)"', s)))


EN = load('en')
REF = dict(walk(EN))
bad = 0
for code in (sys.argv[1:] or ORDER):
    try:
        L = dict(walk(load(code)))
    except FileNotFoundError:
        print('%s: нет каталога' % code); bad += 1; continue
    miss = [k for k in REF if k not in L]
    extra = [k for k in L if k not in REF]
    if miss:  print('%s: нет ключей %s' % (code, miss[:12])); bad += 1
    if extra: print('%s: лишние ключи %s' % (code, extra[:12])); bad += 1
    for k, v in REF.items():
        if k not in L:
            continue
        w = L[k]
        if is_plural(v):
            if not is_plural(w) or 'other' not in w:
                print('%s: %s — формы числа без other' % (code, k)); bad += 1
                continue
            v, w = v['other'], w['other']
        if not isinstance(v, str):
            continue
        if k in KEEP:
            continue
        if not isinstance(w, str):
            print('%s: %s — не строка' % (code, k)); bad += 1; continue
        if v.strip() and not w.strip():
            print('%s: пустая строка %s' % (code, k)); bad += 1; continue
        if tags(v) != tags(w):
            print('%s: разметка расходится в %s\n   en %s\n   %s %s' % (code, k, tags(v), code, tags(w))); bad += 1
        if marks(v) != marks(w):
            print('%s: подстановки или ссылки расходятся в %s: en %s, %s %s' % (code, k, marks(v), code, marks(w))); bad += 1
        if re.search(r'&(nbsp|thinsp|mdash|ndash|laquo|raquo|#\d+);', w):
            print('%s: HTML-сущность в %s' % (code, k)); bad += 1
    if not (miss or extra):
        print('%s: %d строк, ключи сходятся' % (code, len(L)))

HOUSING = os.path.join(D, '..', '..', '..', 'housing', 'src', 'strings')
DIGITS = re.compile(r'\d[\d\s\u00a0\u202f.,]*\d|\d')


def nums(s):
    """Числа строки без разделителей разрядов: «1 442», «1.442» и «1,442» — одно число."""
    out = set()
    for m in DIGITS.findall(re.sub(r'<[^>]+>', '', s)):
        m = re.sub(r'[\s\u00a0\u202f]', '', m)
        out.add(re.sub(r'[.,](?=\d{3}\b)', '', m))
    return out


for code in (sys.argv[1:] or ORDER):
    try:
        L = load(code)
    except FileNotFoundError:
        continue
    h = json.load(open(os.path.join(HOUSING, code + '.json'), encoding='utf-8'))
    # Примечание переводчика своё у каждого исследования, остальное в t.ui — общее.
    strip = lambda u: {k: v for k, v in (u or {}).items() if k != 'translationNote'}
    if strip(L['t'].get('ui')) != strip(h['t']['ui']):
        print('%s: t.ui расходится с жильём' % code); bad += 1
    lim = 200 if code in ('ja', 'zh-Hans') else 330
    for k, v in walk(L['t']):
        if isinstance(v, str) and not k.startswith('ui.') and not k.startswith('weak.s'):
            for par in re.split(r'\n\s*\n', v):
                n = len(re.sub(r'<[^>]+>', '', par))
                if n > lim:
                    print('%s: абзац %s — %d знаков, предел %d' % (code, k, n, lim)); bad += 1
    if len(L['htmlTitle']) > 60:
        print('%s: htmlTitle %d знаков' % (code, len(L['htmlTitle']))); bad += 1
    if len(L['metaDescription']) > 155:
        print('%s: metaDescription %d знаков' % (code, len(L['metaDescription']))); bad += 1
    if not all(isinstance(r[0], (int, float)) and isinstance(r[1], int) for r in L['js']['big']):
        print('%s: js.big — нужны числа' % code); bad += 1
    en_t = dict(walk(EN['t']))
    for k, v in walk(L['t']):
        if isinstance(v, str) and k in en_t and not k.startswith('ui.'):
            lost = nums(en_t[k]) - nums(v)
            if lost:
                print('%s: в %s нет чисел %s' % (code, k, sorted(lost)))
print('расхождений:', bad)
sys.exit(1 if bad else 0)
