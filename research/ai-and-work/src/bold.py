# -*- coding: utf-8 -*-
"""Обернуть фразу в ** внутри значения каталога.

    python3 bold.py <код> <путь.к.ключу> <фраза>

Ищет фразу по всему значению, а не по номеру абзаца: разбивка на абзацы
у языков своя, и одна и та же мысль лежит в разных по счёту абзацах.
Требует ровно одного вхождения. Слова не трогаются — добавляются звёздочки.
"""
import io, json, sys, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'strings')


def apply(root, code, path, phrase):
    p = os.path.join(root, code + '.json')
    d = json.load(io.open(p, encoding='utf-8'))
    node, keys = d, path.split('.')
    for k in keys[:-1]:
        node = node[k]
    val = node[keys[-1]]
    if '**' + phrase + '**' in val:
        return 'уже'
    n = val.count(phrase)
    if n != 1:
        raise SystemExit('%s %s: вхождений %d — %r' % (code, path, n, phrase))
    node[keys[-1]] = val.replace(phrase, '**' + phrase + '**')
    io.open(p, 'w', encoding='utf-8').write(
        json.dumps(d, ensure_ascii=False, indent=2) + '\n')
    return 'ok'


if __name__ == '__main__':
    print(apply(D, sys.argv[1], sys.argv[2], sys.argv[3]))
