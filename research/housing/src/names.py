#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Имена регионов NUTS — из статистической номенклатуры Евростата.

    python3 research/housing/src/names.py

Зачем отдельный шаг. Раньше имена приходили атрибутом NAME_LATN из того же файла
контуров GISCO, что и геометрия. Геометрия оттуда убрана по лицензии (см. geo.py),
и имена вместе с ней: брать их из файла, который нельзя использовать коммерчески,
непоследовательно. Номенклатура — это статистические данные, а не геометрия, и
общая заметка Евростата разрешает их повторное использование в любых целях при
указании источника.

Источник: эндпоинт SDMX Евростата, кодлист GEO —
  https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/codelist/ESTAT/GEO

Пишет src/region-names.json — {код NUTS: английское имя}. Файл остаётся в src и на
страницу не едет: data.py забирает из него только те имена, которые нужны.
"""
import json, os, re, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
URL = 'https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/codelist/ESTAT/GEO'
ENT = (('&amp;', '&'), ('&apos;', "'"), ('&quot;', '"'), ('&lt;', '<'), ('&gt;', '>'))


def main():
    raw = urllib.request.urlopen(URL, timeout=120).read().decode('utf-8')
    names = {}
    for m in re.finditer(r'<s:Code id="([A-Z]{2}[A-Z0-9]{0,3})"(.*?)</s:Code>', raw, re.S):
        n = re.search(r'<c:Name xml:lang="en">(.*?)</c:Name>', m.group(2), re.S)
        if not n:
            continue
        v = n.group(1).strip()
        for a, b in ENT:
            v = v.replace(a, b)
        names[m.group(1)] = v

    # Весь кодлист целиком: файл лежит в src и на страницу не едет, а зависимость
    # от data.json сделала бы связь по кругу — data.py читает имена отсюда.
    have = {k: names[k] for k in sorted(names)}
    out = os.path.join(HERE, 'region-names.json')
    json.dump(have, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('region-names.json: %d имён, %d байт' % (len(have), os.path.getsize(out)))


if __name__ == '__main__':
    main()
