#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Американский слой: стоимость жилья, доход, аренда и население по округам США.

    python3 research/housing/src/extract_us.py [папка с исходниками]

Недостающие файлы скачиваются в эту папку сами. Три источника, все открытые, без
ключа и без запрета на коммерческое использование — последнее и есть причина, по
которой слой переписан.

ПОЧЕМУ ЗДЕСЬ БОЛЬШЕ НЕТ КВАДРАТНОГО МЕТРА
------------------------------------------
Первая версия слоя считала метры из Redfin: у него есть медианная цена за
квадратный ФУТ по сделкам, и она давала ту же метрику, что у европейского слоя.
Пользоваться ею нельзя. Обновлённый Data Center не несёт ни лицензии на данные,
ни разрешения цитировать — проверены сам центр, страница загрузок и статья
поддержки «Downloading Data», — а общие Terms of Use от 29 сентября 2025
(§ 2.3.2–2.3.3) дают «limited, personal, non-exclusive, non-transferable» право
«access, view, and use the Services» и прямо запрещают воспроизведение,
перепубликацию и производные работы. Страница бесплатная, но несёт баннер моего
продукта и встраивает производную таблицу в файл — это ровно то, что запрещено.

Замены у метража нет, и это не лень поиска, а свойство американской статистики:
**площадь жилья в США не является государственной статистикой.** ACS её не
собирает вовсе; American Housing Survey собирает, но только по трём десяткам
агломераций; Survey of Construction — только по новостройкам и только по четырём
переписным регионам. Цена за фут по округам существует лишь у Redfin, Zillow (и
там только по новостройкам и только по метро) и realtor.com, то есть у частных
компаний, у которых она взята из MLS. Ни один из них не даёт права на
перепубликацию: те же ряды realtor.com FRED помечает «Copyrighted: Citation
Required» и запрещает коммерческую перепубликацию без письменного разрешения.

Поэтому американские округа на карте живут без метров — с честной подписью, а не
с правдоподобной выдумкой, — и несут две другие метрики страницы, которые в
государственных данных есть. Письма с просьбой о разрешении лежат в
letter-to-authors.md; придёт ответ — метры включатся одной пересборкой.

ИСТОЧНИКИ
---------
1. ACS 2024 5-year (American Community Survey, Бюро переписи США): B25077 —
   медианная стоимость жилья, занятого владельцем; B19013 — медианный доход
   домохозяйства; B25064 — медианная валовая аренда; B01003 — население.
   Читается через открытый API Census Reporter: у Бюро переписи собственный API
   с недавних пор требует ключ, то есть аккаунт, а bulk-файлы на www2.census.gov
   отдают 403 через Cloudflare. Census Reporter про свои данные говорит прямо:
   «Data on Census Reporter comes from the US Census Bureau and is not
   copyrighted», — это те же федеральные цифры, общественное достояние.
2. Natural Earth 10m admin-2 — центроид округа для карты (общественное
   достояние, тот же репозиторий, что и контуры стран в geo.py).
3. Freddie Mac PMMS — ставка 30-летней фиксированной ипотеки. Их условия:
   «Information from this document may be used with proper attribution».

ОГОВОРКА ПЕРВАЯ: пять лет в одной цифре. ACS 5-year — это не «2024 год», а
опрос, размазанный по 2020–2024 годам. Для округов это единственный доступный
уровень: годичный ACS публикуется только для мест крупнее 65 тысяч жителей, а
таких округов меньше половины. Суммы Бюро переписи приводит к долларам
последнего года периода, то есть к долларам 2024-го, — поэтому и ставка здесь
средняя за 2024 календарный год, а не за пять лет и не за последнюю неделю.

ОГОВОРКА ВТОРАЯ: стоимость — это оценка владельца, а не цена сделки. B25077
спрашивает владельца, за сколько, по его мнению, дом был бы продан. Европейский
слой стоит на объявлениях. Систематическая разница между самооценкой и рынком
известна и меняет знак в зависимости от фазы цикла; сравнивать эти два числа
между слоями нельзя, и страница этого не делает.

ОГОВОРКА ТРЕТЬЯ: аренда валовая. B25064 — медианная валовая аренда, то есть плата
плюс коммунальные услуги, которые платит наниматель. Европейская цена аренды —
без коммунальных. Это тоже разные величины, и подписаны они порознь.

ОГОВОРКА ЧЕТВЁРТАЯ: медиана округа — это медиана, а не среднее. Штат и страна
берутся отдельными запросами к тем же таблицам, а не собираются из округов:
взвешенное по населению среднее медиан — не медиана, и там, где настоящую
медиану можно просто спросить, выдумывать суррогат незачем.

КОННЕКТИКУТ. С 2022 года Бюро переписи считает штат по девяти плановым регионам
вместо восьми упразднённых округов, а Natural Earth остался на старых границах.
Центроиды девяти регионов берутся из геометрии TIGER 2024 (те же федеральные
данные, тот же открытый API) и считаются как центр тяжести многоугольника,
взвешенный по площади колец. Это не подстановка чужой точки, а вычисление по
настоящей границе.

ТЕРРИТОРИИ. Пуэрто-Рико (78 муниципалитетов) в выгрузке есть, но в слой не идёт:
его опрашивает отдельное обследование PRCS, и в общенациональные итоги Бюро
переписи Пуэрто-Рико не входит — страна в данных страницы должна быть той же,
что в строке «United States». Причина записана в us-gaps.csv, а не подразумевается.

Непокрытое НЕ отбрасывается молча: каждый пропуск попадает в us-gaps.csv с
причиной, а округ без центроида валит сборку.
"""
import csv, json, os, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(ROOT, 'research', 'data', 'us-counties.csv')
GAPS = os.path.join(ROOT, 'research', 'data', 'us-gaps.csv')
META = os.path.join(ROOT, 'research', 'data', 'us-meta.json')

CR = 'https://api.censusreporter.org/1.0'
RELEASE = 'acs2024_5yr'          # последний, где есть все округа
TIGER = 'tiger2024'
TABLES = ['B25077', 'B19013', 'B25064', 'B01003']
VALUE, INCOME, RENT, POP = 'B25077001', 'B19013001', 'B25064001', 'B01003001'
RATE_YEAR = '2024'               # суммы ACS — в долларах последнего года периода

SOURCES = {
    'pmms.csv': 'https://www.freddiemac.com/pmms/docs/PMMS_history.csv',
    'ne_10m_admin_2_counties.geojson':
        'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/'
        'geojson/ne_10m_admin_2_counties.geojson',
}
# Территории: в ACS есть, в слой не идут. Ключ — код штата, значение — причина.
TERRITORY = {'72': 'Пуэрто-Рико: отдельное обследование PRCS, в итоги США не входит'}

COLS = ['fips', 'st', 'county', 'name', 'pop', 'lat', 'lon',
        'value', 'value_moe', 'income', 'income_moe', 'rent', 'rent_moe']


# Census Reporter отвечает «use a user agent specific to your project» на общий
# браузерный заголовок, и это их правило, а не техническая помеха: чужой сервер
# должен видеть, кто и зачем его читает. Здесь стоит адрес самой страницы.
UA = 'avgrebenkin.com-housing-research/1.0 (+https://avgrebenkin.com/research/housing/)'


def get(url, path, timeout=300):
    """Скачать в файл. Заголовок обязателен: без него GitHub и API Census
    Reporter отвечают 403."""
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r, open(path, 'wb') as f:
        f.write(r.read())


def fetch(src, name):
    p = os.path.join(src, name)
    if os.path.exists(p):
        return p
    print('скачиваю', name)
    get(SOURCES[name], p)
    return p


def api(src, name, url):
    """Ответ API с кэшем на диске: пересборка не должна дёргать чужой сервер."""
    p = os.path.join(src, name)
    if not os.path.exists(p):
        print('запрашиваю', name)
        get(url, p, timeout=600)
    d = json.load(open(p, encoding='utf-8'))
    if 'error' in d:
        raise SystemExit('%s: %s' % (name, d['error']))
    return d


def acs(src, name, geo_ids):
    url = '%s/data/show/%s?table_ids=%s&geo_ids=%s' % (
        CR, RELEASE, ','.join(TABLES), urllib.parse.quote(geo_ids, safe='|,'))
    return api(src, name, url)


def cell(row, table, col):
    """Оценка и её погрешность. Отсутствующая медиана — это None, а не ноль:
    в округе, где жильё владельцев не продавалось, ноль означал бы «бесплатно»."""
    t = row.get(table) or {}
    est = (t.get('estimate') or {}).get(col)
    moe = (t.get('error') or {}).get(col)
    return (None if est is None else float(est),
            None if moe is None else float(moe))


def ring_centroid(ring):
    """Центр тяжести замкнутого кольца и его площадь со знаком (формула Гаусса)."""
    a = cx = cy = 0.0
    for i in range(len(ring) - 1):
        x0, y0 = ring[i][0], ring[i][1]
        x1, y1 = ring[i + 1][0], ring[i + 1][1]
        f = x0 * y1 - x1 * y0
        a += f
        cx += (x0 + x1) * f
        cy += (y0 + y1) * f
    if a == 0:
        return None
    a *= 0.5
    return cx / (6 * a), cy / (6 * a), a


def centroid_of(geom):
    """Центр тяжести многоугольника: кольца складываются со своим знаком площади,
    поэтому дырки вычитаются сами, а не игнорируются."""
    if not geom:
        return None
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    num_x = num_y = den = 0.0
    for poly in polys:
        for i, ring in enumerate(poly):
            c = ring_centroid(ring)
            if not c:
                continue
            x, y, a = c
            if i:                      # внутреннее кольцо: дырка
                a = -abs(a)
            else:
                a = abs(a)
            num_x += x * a; num_y += y * a; den += a
    if not den:
        return None
    return num_y / den, num_x / den    # (широта, долгота)


def read_centroids(path):
    out = {}
    for f in json.load(open(path, encoding='utf-8'))['features']:
        p = f['properties']
        if p.get('ADM0_A3') == 'USA' and p.get('CODE_LOCAL') and p.get('latitude') is not None:
            out[str(p['CODE_LOCAL']).zfill(5)] = (float(p['latitude']), float(p['longitude']))
    return out


def tiger_centroids(src, geoids):
    """Центроиды из федеральной геометрии — для округов, которых нет в Natural Earth."""
    if not geoids:
        return {}
    url = '%s/geo/show/%s?geo_ids=%s' % (CR, TIGER, urllib.parse.quote(','.join(geoids), safe=','))
    d = api(src, 'tiger_extra.json', url)
    out = {}
    for f, gid in zip(d.get('features', []), geoids):
        c = centroid_of(f.get('geometry'))
        if c:
            out[gid[7:]] = c
    return out


def read_rate(path, year):
    """Средняя 30-летняя фиксированная за календарный год долларов ACS."""
    vals = []
    for r in csv.DictReader(open(path, encoding='utf-8')):
        try:
            m, d, y = r['date'].split('/')
        except (AttributeError, ValueError):
            continue
        if y == year and (r.get('pmms30') or '').strip():
            vals.append(float(r['pmms30']))
    return (sum(vals) / len(vals), len(vals)) if vals else (0.0, 0)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else HERE
    counties = acs(src, 'acs_counties.json', '050|01000US')
    states = acs(src, 'acs_states.json', '040|01000US')
    nation = acs(src, 'acs_nation.json', '01000US')
    rel = counties['release']
    print('%s (%s), таблицы %s' % (rel['name'], rel['years'], ', '.join(TABLES)))

    cent = read_centroids(fetch(src, 'ne_10m_admin_2_counties.geojson'))
    print('Natural Earth: %d центроидов округов' % len(cent))

    # Штат по суффиксу названия округа: «Travis County, TX». Своего поля с
    # аббревиатурой у ACS нет, а код штата — это первые две цифры FIPS.
    st_of = {}
    for gid, g in counties['geography'].items():
        n = g['name']
        if ', ' in n:
            st_of[gid[7:12][:2]] = n.rsplit(', ', 1)[1]

    need = sorted(gid for gid in counties['data']
                  if gid[7:12] not in cent and gid[7:9] not in TERRITORY)
    if need:
        print('нет в Natural Earth: %d — беру геометрию TIGER' % len(need))
        cent.update(tiger_centroids(src, need))

    rows, gaps = [], []
    pop_total = pop_covered = 0.0
    for gid in sorted(counties['data']):
        fips = gid[7:12]
        d = counties['data'][gid]
        name = counties['geography'][gid]['name']
        pop = cell(d, 'B01003', POP)[0] or 0.0
        st = fips[:2]
        if st in TERRITORY:
            gaps.append([fips, name, TERRITORY[st]])
            continue
        pop_total += pop
        value, value_moe = cell(d, 'B25077', VALUE)
        income, income_moe = cell(d, 'B19013', INCOME)
        rent, rent_moe = cell(d, 'B25064', RENT)
        if not income:
            gaps.append([fips, name, 'ACS не публикует медианный доход домохозяйства'])
            continue
        if value is None and rent is None:
            gaps.append([fips, name, 'ACS не публикует ни стоимости жилья, ни аренды'])
            continue
        if fips not in cent:
            raise SystemExit('нет центроида: %s %s' % (fips, name))
        lat, lon = cent[fips]
        pop_covered += pop
        rows.append({
            'fips': fips, 'st': st_of.get(st, st),
            'county': name.rsplit(', ', 1)[0], 'name': name,
            'pop': int(round(pop)), 'lat': round(lat, 4), 'lon': round(lon, 4),
            'value': int(value) if value else '', 'value_moe': int(value_moe) if value_moe else '',
            'income': int(income), 'income_moe': int(income_moe) if income_moe else '',
            'rent': int(rent) if rent else '', 'rent_moe': int(rent_moe) if rent_moe else '',
        })

    rate, weeks = read_rate(fetch(src, 'pmms.csv'), RATE_YEAR)
    print('PMMS 30 лет: %.2f %% в среднем за %d недель %s года' % (rate, weeks, RATE_YEAR))

    def agg(block, gid):
        d = block['data'][gid]
        return {
            'pop': int(cell(d, 'B01003', POP)[0] or 0),
            'value': int(cell(d, 'B25077', VALUE)[0] or 0),
            'income': int(cell(d, 'B19013', INCOME)[0] or 0),
            'rent': int(cell(d, 'B25064', RENT)[0] or 0),
        }

    st_rows = {}
    for gid in states['data']:
        code = gid[7:9]
        if code in TERRITORY:
            continue
        st_rows[st_of.get(code, code)] = agg(states, gid)

    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    with open(GAPS, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['fips', 'name', 'reason'])
        w.writerows(gaps)

    # Сколько за медианой: у ACS вместо числа сделок — погрешность оценки.
    # Относительная погрешность и есть мера доверия к строке, и она едет дальше.
    rel_moe = sorted(r['value_moe'] / r['value'] * 100
                     for r in rows if r['value'] and r['value_moe'])
    meta = {
        'release': rel['id'], 'releaseName': rel['name'], 'years': rel['years'],
        'tables': TABLES, 'rate30': round(rate, 2), 'rateWeeks': weeks,
        'rateYear': RATE_YEAR, 'counties': len(rows), 'gaps': len(gaps),
        'popTotal': int(round(pop_total)), 'popCovered': int(round(pop_covered)),
        'nation': agg(nation, '01000US'), 'states': st_rows,
        'moeMedian': round(rel_moe[len(rel_moe) // 2], 1) if rel_moe else 0,
        'moeP90': round(rel_moe[int(len(rel_moe) * 0.9)], 1) if rel_moe else 0,
        'source': 'acs+ne+pmms',
    }
    json.dump(meta, open(META, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    print('округов: %d, пропусков: %d' % (len(rows), len(gaps)))
    print('население: %d из %d (%.1f %%)'
          % (pop_covered, pop_total, pop_covered / pop_total * 100 if pop_total else 0))
    print('погрешность стоимости: медиана %.1f %%, девяностая перцентиль %.1f %%'
          % (meta['moeMedian'], meta['moeP90']))
    print('страна: доход %d, жильё %d, аренда %d'
          % (meta['nation']['income'], meta['nation']['value'], meta['nation']['rent']))
    for g in gaps[:5]:
        print('  пропуск:', g[0], g[1], '—', g[2])
    if len(gaps) > 5:
        print('  … и ещё %d' % (len(gaps) - 5))


if __name__ == '__main__':
    main()
