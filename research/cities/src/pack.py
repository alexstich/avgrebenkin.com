#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Каталог строк ↔ плоский TSV, чтобы ключи не набивались заново.

    python3 research/cities/src/pack.py dump en > en.tsv
    python3 research/cities/src/pack.py load de de.tsv

Формат строки: номер, ключ, значение — через табуляцию. Порядок ключей всегда
берётся из en.json, поэтому номера у всех языков совпадают.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF = json.load(open(os.path.join(HERE, 'strings', 'en.json'), encoding='utf-8'))


def main():
    cmd, code = sys.argv[1], sys.argv[2]
    path = os.path.join(HERE, 'strings', code + '.json')

    if cmd == 'dump':
        src = json.load(open(path, encoding='utf-8'))
        for i, k in enumerate(REF, 1):
            v = src.get(k, '')
            assert '\n' not in v and '\t' not in v, k
            sys.stdout.write('%03d\t%s\t%s\n' % (i, k, v))
        return

    if cmd == 'load':
        # у пустой строки перевода хвостовой табулятор часто съедает редактор,
        # поэтому третье поле необязательное — иначе развалится весь файл
        got = {}
        for n, line in enumerate(open(sys.argv[3], encoding='utf-8'), 1):
            if not line.strip():
                continue
            parts = line.rstrip('\n').split('\t', 2)
            if len(parts) < 2:
                raise SystemExit('строка %d: нет ключа — %r' % (n, line[:60]))
            got[parts[1]] = parts[2] if len(parts) > 2 else ''
        miss = [k for k in REF if k not in got]
        extra = [k for k in got if k not in REF]
        if miss or extra:
            raise SystemExit('%s: не хватает %s, лишние %s' % (code, miss[:8], extra[:8]))
        out = {k: got[k] for k in REF}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('%s: %d строк → strings/%s.json' % (code, len(out), code))
        return

    raise SystemExit('dump | load')


if __name__ == '__main__':
    main()
