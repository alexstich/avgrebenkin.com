# -*- coding: utf-8 -*-
"""Сверяет каталог языка с английским: те же ключи, те же подстановки, та же
разметка и те же ссылки. Молчаливая нехватка строки хуже, чем падение сборки.

    python3 research/housing/src/check.py          # все языки
    python3 research/housing/src/check.py de fr    # только эти

Исключение одно — формы множественного числа: объект, чьи ключи — категории
CLDR (one, few, many, other…), у каждого языка свой набор, и сверяется только
наличие 'other'.
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
print('расхождений:', bad)
sys.exit(1 if bad else 0)
