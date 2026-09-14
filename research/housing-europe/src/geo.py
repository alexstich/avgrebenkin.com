#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Контуры NUTS 3 и границы стран для карты — из GISCO Евростата в компактный SVG.

    python3 research/housing-europe/src/geo.py [папка с geojson]

Источник: https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/
  NUTS_RG_20M_2021_4326_LEVL_3.geojson — регионы NUTS 3 редакции 2021, масштаб 1:20 млн
  NUTS_RG_20M_2021_4326_LEVL_0.geojson — контуры стран той же редакции
(© EuroGeographics для административных границ). Если файлов в папке нет,
скрипт их скачает.

Проекция — азимутальная равновеликая Ламберта с центром 52° с. ш., 10° в. д.
(то же семейство, что EPSG:3035 у самого ESPON). Координаты квантуются в сетку
1400 единиц по ширине, путь пишется относительными отрезками: 1499 полигонов
NUTS 3 занимают около 135 КБ. Заморские территории (Французская Гвиана, Канары,
Азоры, Мадейра, Шпицберген) в кадр не попадают: рамка −25…45° по долготе и
34…72° по широте.

Что пишется: src/geo.json — {w, h, nuts3: {код: путь}, nuts0: {код: путь},
names: {код NUTS3: латинское имя}}.
"""
import json, math, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = 'https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/'
FILES = {3: 'NUTS_RG_20M_2021_4326_LEVL_3.geojson', 0: 'NUTS_RG_20M_2021_4326_LEVL_0.geojson'}
W = 1400
LAT0, LON0 = 52.0, 10.0


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


def load(src, level):
    p = os.path.join(src, FILES[level])
    if not os.path.exists(p):
        print('скачиваю', FILES[level])
        urllib.request.urlretrieve(BASE + FILES[level], p)
    return json.load(open(p, encoding='utf-8'))


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else HERE
    g3, g0 = load(src, 3), load(src, 0)
    xs, ys = [], []
    for f in g3['features']:
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

    nuts3, names, nuts0 = {}, {}, {}
    for f in g3['features']:
        d = encode(f)
        if d:
            nuts3[f['properties']['NUTS_ID']] = d
            names[f['properties']['NUTS_ID']] = f['properties']['NAME_LATN']
    for f in g0['features']:
        d = encode(f)
        if d:
            nuts0[f['properties']['NUTS_ID']] = d
    out = {'w': W, 'h': H, 'lat0': LAT0, 'lon0': LON0,
           'box': [minx, maxx, miny, maxy], 'regions': nuts3, 'countries': nuts0, 'names': names}
    p = os.path.join(HERE, 'geo.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('geo.json: %d NUTS3, %d стран, %d×%d, %d байт' % (len(nuts3), len(nuts0), W, H, os.path.getsize(p)))


if __name__ == '__main__':
    main()
