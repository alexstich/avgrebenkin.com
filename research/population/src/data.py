#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Датасет страницы «Eight billion, one doubling at a time».

    python3 research/population/src/data.py      # скачать источники и собрать data.json

Источники (кэшируются в $TMPDIR/population-src, в репозиторий не кладутся):
  population.csv     — Our World in Data, Population (HYDE 3.3 до 1800, Gapminder 1800–1949,
                       UN WPP 2024 с 1950), страны в сегодняшних границах, −10 000…2023;
  countries-110m.json — Natural Earth 1:110m через world-atlas (TopoJSON), контуры стран;
  countries.json     — mledoze/countries: коды ISO, центр, площадь, часть света;
  estimates.wiki     — Википедия, «Estimates of historical world population», таблица
                       «Before 1950»: оценки мира у девяти авторов.

Что получается в data.json:
  years/world — узлы ряда и население мира в них (прореженные: тысячелетия до 1 н. э.,
                века до 1700, десятилетия до 1950, пятилетки до 2020, плюс 2020 и 2023);
  pop         — те же узлы по 165 странам, у которых ряд полный с −10 000;
  names       — [английское имя, широта, долгота центра, площадь км², часть света, ISO alpha-2];
  dots        — по точке на миллион человек максимума страны, брошенных случайно (с зерном)
                внутрь её контура; порядок перемешан, чтобы страна заполнялась равномерно;
  shapes      — контуры стран, округлённые до 0,1°;
  est         — [год, {автор: [нижняя, верхняя]}] — независимые оценки мира.
"""
import csv, json, math, os, random, re, sys, tempfile, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(tempfile.gettempdir(), 'population-src')
SRC = {
    'population.csv': 'https://ourworldindata.org/grapher/population.csv?v=1&csvType=full&useColumnShortNames=true',
    'countries-110m.json': 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json',
    'countries.json': 'https://cdn.jsdelivr.net/npm/world-countries@5/countries.json',
    'estimates.wiki': 'https://en.wikipedia.org/w/index.php?title=Estimates_of_historical_world_population&action=raw',
}
YEARS = (list(range(-10000, 0, 1000)) + list(range(0, 1700, 100)) + list(range(1700, 1800, 10))
         + list(range(1800, 1950, 10)) + list(range(1950, 2020, 5)) + [2020, 2023])
UNIT = 1_000_000


def fetch(name):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, name)
    if not os.path.exists(p):
        req = urllib.request.Request(SRC[name], headers={'User-Agent': 'avgrebenkin-research/1.0'})
        with urllib.request.urlopen(req, timeout=120) as r, open(p, 'wb') as f:
            f.write(r.read())
    return p


def population():
    want = set(YEARS)
    pop = {}
    for r in csv.DictReader(open(fetch('population.csv'), encoding='utf-8')):
        c = r['code']
        if not c or (c.startswith('OWID') and c != 'OWID_WRL'):
            continue
        y = int(r['year'])
        if y in want:
            pop.setdefault(c, {})[y] = int(r['population_historical'])
    world = pop.pop('OWID_WRL')
    series = {c: [d[y] for y in YEARS] for c, d in pop.items() if len(d) == len(YEARS)}
    return [world[y] for y in YEARS], series


def shapes(num2a3):
    t = json.load(open(fetch('countries-110m.json'), encoding='utf-8'))
    sc, tr = t['transform']['scale'], t['transform']['translate']
    arcs = []
    for a in t['arcs']:
        x = y = 0; pts = []
        for dx, dy in a:
            x += dx; y += dy
            pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
        arcs.append(pts)

    def ring(ids):
        out = []
        for i in ids:
            p = arcs[i] if i >= 0 else arcs[~i][::-1]
            out.extend(p if not out else p[1:])
        return out
    res = {}
    for g in t['objects']['countries']['geometries']:
        a3 = num2a3.get(str(g.get('id', '')).zfill(3))
        if not a3:
            continue  # Северный Кипр, Сомалиленд, Косово — без кода ISO и без ряда OWID
        if g['type'] == 'Polygon':
            res[a3] = [[ring(r) for r in g['arcs']]]
        elif g['type'] == 'MultiPolygon':
            res[a3] = [[ring(r) for r in p] for p in g['arcs']]
    return res


def inside(x, y, poly):
    ins = False
    for r in poly:
        j = len(r) - 1
        for i in range(len(r)):
            xi, yi = r[i]; xj, yj = r[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                ins = not ins
            j = i
    return ins


def area(poly):
    r = poly[0]
    s = sum((r[i][0] - r[i - 1][0]) * (r[i][1] + r[i - 1][1]) for i in range(len(r)))
    return abs(s) / 2 * math.cos(math.radians(sum(q[1] for q in r) / len(r)))


def dots(series, sh, meta):
    rnd = random.Random(7)
    out = {}
    for c, s in series.items():
        n = math.ceil(max(s) / UNIT)
        polys, pts = sh.get(c), []
        if polys:
            ws = [area(p) for p in polys]; tot = sum(ws); tries = 0
            while len(pts) < n and tries < n * 400:
                tries += 1
                r = rnd.random() * tot; k = 0
                while r > ws[k]:
                    r -= ws[k]; k += 1
                p = polys[k]; xs = [q[0] for q in p[0]]; ys = [q[1] for q in p[0]]
                x, y = rnd.uniform(min(xs), max(xs)), rnd.uniform(min(ys), max(ys))
                if inside(x, y, p):
                    pts.append((x, y))
        lat, lon = meta[c]['latlng'] if c in meta else (0, 0)
        while len(pts) < n:  # острова мельче карты 1:110m — вокруг центра
            pts.append((lon + rnd.gauss(0, .6), lat + rnd.gauss(0, .6)))
        rnd.shuffle(pts)
        out[c] = [v for p in pts for v in (round(p[0], 1), round(p[1], 1))]
    return out


def estimates():
    s = open(fetch('estimates.wiki'), encoding='utf-8').read()
    t = s[s.index('===Before 1950==='):s.index('===1950 to 2016===')]
    t = re.sub(r'<ref[^>]*/>', '', t)
    t = re.sub(r'<ref[^>]*>.*?</ref>', '', t, flags=re.S)
    cols = ['PRB', 'UN', 'Maddison', 'HYDE', 'Biraben', 'McEvedy', 'Thomlinson', 'Durand', 'Clark', 'Gapminder']

    def val(c):
        c = c.strip().replace('&nbsp;', ' ').replace(',', '')
        mul = lambda u: 1e6 if u == 'M' else 1e9
        m = re.match(r'^([\d.]+)\s*[–-]\s*([\d.]+)\s*([MB])', c)
        if m:
            return [float(m.group(1)) * mul(m.group(3)), float(m.group(2)) * mul(m.group(3))]
        m = re.match(r'^([\d.]+)\s*([MB])', c)
        if m:
            v = float(m.group(1)) * mul(m.group(2)); return [v, v]
        return None
    out = []
    for r in t.split('\n|-')[1:]:
        lines = [l for l in r.strip().split('\n') if l.startswith('|') and not l.startswith('|}')]
        if not lines:
            continue
        cells = '||'.join(l[1:] for l in lines).split('||')
        y = cells[0].strip().replace('−', '-').replace(',', '')
        if not re.match(r'^-?\d+$', y):
            continue
        d = {cols[i]: v for i, v in enumerate(val(c) for c in cells[1:11]) if v}
        # Gapminder до 1800 года сам берёт мир у Бирабена и Макэведи — это не
        # независимая оценка, а повтор чужой, и в коридоре она лишняя.
        d.pop('Gapminder', None)
        # Сверено с таблицей US Census Bureau: у Томлинсона на 1 год н. э.
        # 200 млн; 226 в Википедии совпадает с Мэддисоном — ошибка переноса.
        if int(y) == 1 and 'Thomlinson' in d:
            d['Thomlinson'] = [200e6, 200e6]
        # В 1500 году 425 в столбце Бирабена — это Макэведи; у Бирабена 460.
        if int(y) == 1500 and d.get('Biraben') == [425e6, 425e6]:
            d['Biraben'], d['McEvedy'] = [460e6, 460e6], [425e6, 425e6]
        # В 1700 году строка Википедии сдвинута на 400 млн (1079, 1010, 1000).
        # У Census: Бирабен 679, Макэведи 610, Томлинсон 600. Кларка в таблице
        # Census нет, а сдвинутому значению Википедии верить нельзя — убираем.
        if int(y) == 1700 and d.get('Biraben') == [1079e6, 1079e6]:
            d.update(Biraben=[679e6, 679e6], McEvedy=[610e6, 610e6], Thomlinson=[600e6, 600e6])
            d.pop('Clark', None)
        if d:
            out.append([int(y), d])
    return out


def main():
    meta = {c['cca3']: c for c in json.load(open(fetch('countries.json'), encoding='utf-8'))}
    num2a3 = {c['ccn3']: a3 for a3, c in meta.items() if c.get('ccn3')}
    world, series = population()
    sh = shapes(num2a3)
    names = {}
    for c in series:
        m = meta.get(c)
        names[c] = [m['name']['common'], m['latlng'][0], m['latlng'][1], m['area'], m['region'], m['cca2']] if m \
            else [c, 0, 0, 1, 'Asia', '']
    def simp(r):  # округлить до 0,1° и снять подряд идущие повторы
        o = []
        for x, y in r:
            q = (round(x, 1), round(y, 1))
            if not o or q != o[-1]:
                o.append(q)
        return [v for q in o for v in q]
    D = {'years': YEARS, 'world': world, 'pop': series, 'names': names, 'dots': dots(series, sh, meta),
         'shapes': {c: [[simp(r) for r in p] for p in ps] for c, ps in sh.items()}, 'est': estimates()}
    json.dump(D, open(os.path.join(HERE, 'data.json'), 'w', encoding='utf-8'), separators=(',', ':'))
    have = sum(v[-1] for v in series.values())
    print('стран %d, точек %d, в стране-ряду %.3f млрд из %.3f, оценок %d'
          % (len(series), sum(len(v) // 2 for v in D['dots'].values()), have / 1e9, world[-1] / 1e9, len(D['est'])))


if __name__ == '__main__':
    main()
