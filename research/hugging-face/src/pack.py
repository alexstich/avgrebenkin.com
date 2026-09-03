#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Плоский список строк языка и сборка обратно.

    python3 src/pack.py dump en > en.tsv      # пронумерованный список строк
    python3 src/pack.py load de de.tsv        # собрать strings/de.json

Формат TSV: «номер \t путь \t значение», по строке на строку. Номер и путь
сверяются с эталоном en.json — сдвиг на одну строку сборка не пропустит.
Порядок строк одинаков для всех языков, поэтому перевод не может разъехаться
с ключами: ключи в файле перевода вообще не набираются руками.
"""
import copy, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, 'strings', 'en.json')   # английский — оригинал статьи


def walk(node, path=''):
    """Обход в фиксированном порядке: словари — по порядку объявления."""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, path + '.' + k if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, '%s.%d' % (path, i))


def put(root, path, value):
    """Кладём значение по пути в уже готовую копию эталона: форма дерева
    берётся из ru.json, поэтому «12» остаётся ключом словаря, а не индексом."""
    parts = path.split('.')
    cur = root
    for p in parts[:-1]:
        cur = cur[int(p)] if isinstance(cur, list) else cur[p]
    last = parts[-1]
    if isinstance(cur, list):
        cur[int(last)] = value
    else:
        cur[last] = value


def main():
    cmd = sys.argv[1]
    ref = json.load(open(REF, encoding='utf-8'))
    items = list(walk(ref))

    if cmd == 'dump':
        code = sys.argv[2]
        src = json.load(open(os.path.join(HERE, 'strings', code + '.json'), encoding='utf-8'))
        vals = dict(walk(src))
        for i, (path, _v) in enumerate(items, 1):
            v = vals.get(path, '')
            assert '\n' not in v and '\t' not in v, path
            sys.stdout.write('%03d\t%s\t%s\n' % (i, path, v))
        return

    if cmd == 'load':
        code, tsv = sys.argv[2], sys.argv[3]
        lines = [l.rstrip('\n') for l in open(tsv, encoding='utf-8') if l.strip()]
        if len(lines) != len(items):
            raise SystemExit('строк %d, ожидалось %d' % (len(lines), len(items)))
        out = copy.deepcopy(ref)
        for (i, (path, _src)), line in zip(enumerate(items, 1), lines):
            # третье поле необязательное: у пустой строки хвостовой табулятор
            # часто съедает редактор, а номер и путь всё равно сверяются ниже
            parts = line.split('\t', 2)
            if len(parts) < 2:
                raise SystemExit('строка %d: нет ключа — %r' % (i, line[:60]))
            num, p = parts[0], parts[1]
            val = parts[2] if len(parts) > 2 else ''
            if int(num) != i or p != path:
                raise SystemExit('строка %d: ожидался %03d %s, пришло %s %s' % (i, i, path, num, p))
            put(out, path, val)
        dst = os.path.join(HERE, 'strings', code + '.json')
        json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('%s: %d строк → %s' % (code, len(lines), os.path.relpath(dst, HERE)))
        return

    raise SystemExit(__doc__)


if __name__ == '__main__':
    main()
