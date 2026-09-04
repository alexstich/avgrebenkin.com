# -*- coding: utf-8 -*-
"""Сверяет каталог языка с английским: те же ключи, те же плейсхолдеры,
те же сноски. Молчаливая нехватка строки хуже, чем падение сборки."""
import json, os, re, sys
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'strings')
EN = json.load(open(os.path.join(D, 'en.json'), encoding='utf-8'))
ORDER = ['ru', 'uk', 'de', 'fr', 'es', 'pt-BR', 'it', 'nl', 'pl', 'tr', 'ja', 'zh-Hans']

def walk(node, path=''):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, path + '.' + k if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, '%s.%d' % (path, i))
    else:
        yield path, node

REF = dict(walk(EN))
bad = 0
for code in (sys.argv[1:] or ORDER):
    L = dict(walk(json.load(open(os.path.join(D, code + '.json'), encoding='utf-8'))))
    miss = [k for k in REF if k not in L]
    extra = [k for k in L if k not in REF]
    if miss:  print('%s: нет ключей %s' % (code, miss)); bad += 1
    if extra: print('%s: лишние ключи %s' % (code, extra)); bad += 1
    for k, v in REF.items():
        if k not in L: continue
        for pat, name in ((r'\{(\w+)\}', 'плейсхолдеры'), (r'\[\^(\d+)\]', 'сноски'),
                          (r'href="#s(\d+)"', 'ссылки на источники')):
            a, b = sorted(re.findall(pat, str(v))), sorted(re.findall(pat, str(L[k])))
            if a != b:
                print('%s: %s расходятся в %s — en %s, %s %s' % (code, name, k, a, code, b))
                bad += 1
    empty = [k for k, v in L.items() if isinstance(v, str) and not v.strip()
             and REF.get(k, '').strip()]
    if empty: print('%s: пустые строки %s' % (code, empty)); bad += 1
    if not (miss or extra):
        print('%s: %d строк, ключи и подстановки сходятся' % (code, len(L)))
print('расхождений:', bad)
sys.exit(1 if bad else 0)
