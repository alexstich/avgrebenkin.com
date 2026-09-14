#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Контуры стран для карты — из Natural Earth в компактный SVG.

    python3 research/housing-europe/src/geo.py [папка с geojson]

Почему не GISCO. Контуры NUTS Евростата выглядели очевидным выбором и были здесь
сначала, но их лицензия проверена по первоисточнику и не подходит: на страницах
«Administrative units» и «Statistical units» условие сформулировано дословно —
«The permission to use the data is granted on condition that: the data will not be
used for commercial purposes», а за коммерческой лицензией отсылают в
EuroGeographics. На страницах раздела стоит баннер собственного продукта, так что
некоммерческий характер как минимум спорен. Формулировка живёт на родительской
странице, а на конечных страницах про NUTS её нет вовсе — поэтому эти контуры
часто перераспространяют как свободные, хотя первоисточник такого права не даёт.

Natural Earth — общественное достояние без условий, и покрывает весь мир, а не
одну Европу, что нужно для не-европейских слоёв.

Источник: https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/
  geojson/ne_50m_admin_0_countries.geojson — репозиторий сопровождающего Natural Earth.

Что изменилось в модели. Полигонов уровня региона больше нет: в Natural Earth их
нет, а лицензионно чистой замены с кодами NUTS не нашлось. Карта красит страны, а
места показывает точками по центроидам — они и так есть в данных. Регионы остаются
в поиске, рейтингах и сравнении, просто не красятся на карте.

Проекция — азимутальная равновеликая Ламберта с центром 52° с. ш., 10° в. д.
Координаты квантуются в сетку 1400 единиц по ширине, путь пишется относительными
отрезками. Рамка −25…45° по долготе и 34…72° по широте.

Рамка считается по странам, у которых есть данные (читается из data.json), иначе
Турция и Северная Африка раздвигают кадр и Европа съёживается. Соседи рисуются и
обрезаются границами viewBox.

Что пишется: src/geo.json — {w, h, lat0, lon0, box, countries: {ISO-2: путь}}.
"""
import json, math, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
URL = ('https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/'
       'geojson/ne_50m_admin_0_countries.geojson')
NAME = 'ne_50m_admin_0_countries.geojson'
W = 1400
LAT0, LON0 = 52.0, 10.0

# Natural Earth держит код в ISO_A2, но для спорных и мелких территорий там '-99'.
# Тогда берём ISO_A2_EH, где эти случаи разведены (Франция, Норвегия, Косово).
def iso2(props):
    for k in ('ISO_A2_EH', 'ISO_A2', 'WB_A2'):
        v = (props.get(k) or '').strip()
        if v and v != '-99':
            return v
    return ''


def laea(lat, lon):
    p, l = math.radians(lat), math.radians(lon)
    p0, l0 = math.radians(LAT0), math.radians(LON0)
    k = math.sqrt(2 / (1 + math.sin(p0) * math.sin(p) + math.cos(p0) * math.cos(p) * math.cos(l - l0)))
    return k * math.cos(p) * math.sin(l - l0), k * (math.cos(p0) * math.sin(p) - math.sin(p0) * math.cos(p) * math.cos(l - l0))


def inbox(lon, lat):
    return -25 <= lon <= 45 and 34 <= lat <= 72


def rings(feature):
    g = feature['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for poly in polys:
        ring = poly[0]
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        if inbox(cx, cy):
            yield ring


def load(src):
    p = os.path.join(src, NAME)
    if not os.path.exists(p):
        print('скачиваю', NAME)
        urllib.request.urlretrieve(URL, p)
    return json.load(open(p, encoding='utf-8'))


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else HERE
    g = load(src)
    feats = [f for f in g['features'] if iso2(f['properties']) and list(rings(f))]

    # Рамка — по странам, для которых есть данные. Если считать по всем контурам в
    # кадре, Турция и Северная Африка раздвигают её, и Европа съёживается вдвое.
    dp = os.path.join(HERE, 'data.json')
    core = {c['c'] for c in json.load(open(dp, encoding='utf-8'))['countries']} if os.path.exists(dp) else None
    frame = [f for f in feats if core is None or iso2(f['properties']) in core] or feats

    xs, ys = [], []
    for f in frame:
        for ring in rings(f):
            for p in ring:
                x, y = laea(p[1], p[0]); xs.append(x); ys.append(y)
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    sc = W / (maxx - minx)
    H = int(math.ceil((maxy - miny) * sc))

    def encode(f):
        paths = []
        for ring in rings(f):
            pts, last = [], None
            for p in ring:
                x, y = laea(p[1], p[0])
                q = (round((x - minx) * sc), round((maxy - y) * sc))
                if q != last:
                    pts.append(q); last = q
            if len(pts) < 4:
                continue
            d = 'M%d %d' % pts[0]
            px, py = pts[0]
            for x, y in pts[1:-1]:
                d += 'l%d %d' % (x - px, y - py); px, py = x, y
            paths.append(d + 'z')
        return ''.join(paths)

    countries = {}
    for f in feats:
        d = encode(f)
        if d:
            countries[iso2(f['properties'])] = d
    out = {'w': W, 'h': H, 'lat0': LAT0, 'lon0': LON0,
           'box': [minx, maxx, miny, maxy], 'countries': countries}
    p = os.path.join(HERE, 'geo.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('geo.json: %d стран, %d×%d, %d байт' % (len(countries), W, H, os.path.getsize(p)))


if __name__ == '__main__':
    main()
