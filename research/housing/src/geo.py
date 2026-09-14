#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Контуры стран для карты — из Natural Earth в компактные SVG-кадры.

    python3 research/housing/src/geo.py [папка с geojson]

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
одну Европу, что и нужно, когда слоёв становится больше одного.

Источник: https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/
  geojson/ne_50m_admin_0_countries.geojson — репозиторий сопровождающего Natural Earth.

Что изменилось в модели. Полигонов уровня региона нет: в Natural Earth их нет, а
лицензионно чистой замены с кодами NUTS не нашлось. Карта красит страны, а места
показывает точками по центроидам — они и так есть в данных. Регионы остаются в
поиске, рейтингах и сравнении, просто не красятся на карте.

Почему кадров несколько. Одна проекция на весь мир годится только для глобуса:
равновеликая азимутальная с центром в Европе растягивает Северную Америку до
неузнаваемости, а мировая цилиндрическая врёт про площади там, где как раз и
живут данные. Поэтому у каждого материка свой кадр со своим центром проекции, а
страница их переключает. Контуры стран в каждом кадре свои, но 50-метровый
масштаб достаточно груб, чтобы два кадра весили меньше 200 КБ вдвоём.

Рамка кадра считается по странам кадра, у которых есть данные (читается из
data.json): иначе Турция и Северная Африка раздвигают европейский кадр, а Канада
с Гренландией — американский. Соседи рисуются и обрезаются границами viewBox.

Проекция — азимутальная равновеликая Ламберта. Координаты квантуются в сетку
1400 единиц по ширине, путь пишется относительными отрезками.

Что пишется: src/geo.json — {order: [...], frames: {ключ: {w, h, lat0, lon0,
box, countries: {ISO-2: путь}}}}. Подписи кадров живут в data.py.
"""
import json, math, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
URL = ('https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/'
       'geojson/ne_50m_admin_0_countries.geojson')
NAME = 'ne_50m_admin_0_countries.geojson'
W = 1400

# Кадры. lon/lat — окно отбора контуров, lat0/lon0 — центр проекции. Окно задано
# руками, а не по данным: Алеутские острова уходят за 180-й меридиан и растянули
# бы американский кадр вдвое ради десятка домов, а Гавайи и Аляска в кадре нужны.
# Подписи здесь нет намеренно: она живёт в data.py, потому что подписывать надо не
# кадр, а слой данных. Кадр «na» рисует и Канаду с Мексикой, а данные в нём только
# американские, и кнопка обязана говорить «United States», а не «North America».
FRAMES = [
    {'key': 'eu', 'name': 'Европа', 'lat0': 52.0, 'lon0': 10.0,
     'lon': (-25.0, 45.0), 'lat': (34.0, 72.0)},
    {'key': 'na', 'name': 'Северная Америка', 'lat0': 42.0, 'lon0': -98.0,
     'lon': (-170.0, -52.0), 'lat': (17.0, 72.0)},
]


# Natural Earth держит код в ISO_A2, но для спорных и мелких территорий там '-99'.
# Тогда берём ISO_A2_EH, где эти случаи разведены (Франция, Норвегия, Косово).
def iso2(props):
    for k in ('ISO_A2_EH', 'ISO_A2', 'WB_A2'):
        v = (props.get(k) or '').strip()
        if v and v != '-99':
            return v
    return ''


def laea(lat, lon, lat0, lon0):
    p, l = math.radians(lat), math.radians(lon)
    p0, l0 = math.radians(lat0), math.radians(lon0)
    k = math.sqrt(2 / (1 + math.sin(p0) * math.sin(p) + math.cos(p0) * math.cos(p) * math.cos(l - l0)))
    return (k * math.cos(p) * math.sin(l - l0),
            k * (math.cos(p0) * math.sin(p) - math.sin(p0) * math.cos(p) * math.cos(l - l0)))


def rings(feature, fr):
    g = feature['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for poly in polys:
        ring = poly[0]
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        if fr['lon'][0] <= cx <= fr['lon'][1] and fr['lat'][0] <= cy <= fr['lat'][1]:
            yield ring


def load(src):
    p = os.path.join(src, NAME)
    if not os.path.exists(p):
        print('скачиваю', NAME)
        urllib.request.urlretrieve(URL, p)
    return json.load(open(p, encoding='utf-8'))


def build(g, fr, core):
    feats = [f for f in g['features'] if iso2(f['properties']) and list(rings(f, fr))]
    if not feats:
        return None
    # Рамка — по странам, для которых есть данные. Если считать по всем контурам в
    # кадре, соседи раздвигают её, и сам предмет съёживается вдвое.
    frame = [f for f in feats if core is None or iso2(f['properties']) in core] or feats
    xs, ys = [], []
    for f in frame:
        for ring in rings(f, fr):
            for p in ring:
                x, y = laea(p[1], p[0], fr['lat0'], fr['lon0'])
                xs.append(x); ys.append(y)
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    sc = W / (maxx - minx)
    h = int(math.ceil((maxy - miny) * sc))

    def encode(f):
        paths = []
        for ring in rings(f, fr):
            pts, last = [], None
            for p in ring:
                x, y = laea(p[1], p[0], fr['lat0'], fr['lon0'])
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
    return {'w': W, 'h': h, 'lat0': fr['lat0'], 'lon0': fr['lon0'],
            'box': [minx, maxx, miny, maxy], 'countries': countries}


FR_NAME = {f['key']: f['name'] for f in FRAMES}


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else HERE
    g = load(src)
    dp = os.path.join(HERE, 'data.json')
    core = {c['c'] for c in json.load(open(dp, encoding='utf-8'))['countries']} if os.path.exists(dp) else None

    frames, order = {}, []
    for fr in FRAMES:
        out = build(g, fr, core)
        if not out:
            continue
        # Кадр без единой страны с данными не нужен: он показал бы пустую карту.
        if core is not None and not (set(out['countries']) & core):
            print('кадр %s пропущен: нет стран с данными' % fr['key'])
            continue
        frames[fr['key']] = out
        order.append(fr['key'])
    p = os.path.join(HERE, 'geo.json')
    json.dump({'order': order, 'frames': frames}, open(p, 'w', encoding='utf-8'),
              ensure_ascii=False, separators=(',', ':'))
    for k in order:
        f = frames[k]
        print('  %-3s %-17s %d стран, %d×%d' % (k, FR_NAME[k], len(f['countries']), f['w'], f['h']))
    print('geo.json: %d кадров, %d байт' % (len(order), os.path.getsize(p)))


if __name__ == '__main__':
    main()
