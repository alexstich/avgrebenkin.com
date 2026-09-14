#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Американский слой: цена за метр, доход, аренда и население по округам США.

    python3 research/housing/src/extract_us.py [папка с исходниками]

Недостающие файлы скачиваются в эту папку сами. Пять источников, все открытые и
все без ключа — это было условием: у Бюро переписи API просит ключ, а bulk-файлы
на www2.census.gov отдают 403 через Cloudflare, так что федеральную статистику
здесь пересказывает HUD, который ничем не закрыт.

1. Redfin Data Center, county_market_tracker.tsv000.gz — помесячные медианы по
   округам: медианная цена продажи и медианная цена за квадратный ФУТ, обе по
   фактическим сделкам.
2. HUD Income Limits FY2025 — медианный доход по округам.
3. HUD Fair Market Rents FY2025 — аренда по числу спален и население округа.
4. Natural Earth admin-2 — центроид округа для карты (общественное достояние,
   тот же репозиторий, что и контуры стран в geo.py).
5. Freddie Mac PMMS — недельная ставка 30-летней фиксированной ипотеки.

ОГОВОРКА ПЕРВАЯ, обязана попасть на страницу: у HUD это медианный доход СЕМЬИ, а
не домохозяйства. Семьи не включают одиночек, поэтому величина систематически
выше медианного дохода домохозяйства, и с европейским эквивалентным
располагаемым доходом на взрослого-эквивалента она несопоставима напрямую. В
таблице происхождения это отдельная строка, а не та же колонка.

ОГОВОРКА ВТОРАЯ. HUD задаёт доход не по округу, а по своей зоне (HMFA): все
округа одной агломерации получают одно и то же число. Атланта — 24 округа с
одним доходом на всех, Вашингтон — 14. Из 1133 метро-округов различных значений
дохода всего 625, из 1901 неметро-округа — 1747. Значит внутри агломерации карта
показывает разброс цен, а не разброс доходов.

ОГОВОРКА ТРЕТЬЯ. Fair Market Rent — не рыночная медиана, а 40-й процентиль
валовой аренды жилья стандартного качества, то есть административная величина для
жилищных программ. Она ниже медианы объявлений и считается по числу спален, а не
по площади: сравнивать её с европейской ценой аренды за метр нельзя, это
отдельная метрика, а не та же в других единицах.

Площадь НЕ получается делением медианной цены на медианную цену за фут: отношение
медиан не равно медиане отношений, а на рынке, где смешаны квартиры и дома,
расхождение заметное. Поэтому бюджет из дохода и ставки делится прямо на цену за
фут, без единого допущения о площади.

Стыковка по названию округа и коду штата: Redfin не несёт федеральных кодов, его
числовой идентификатор внутренний. Ловушки, проверенные в данных: Луизиана с
приходами, Аляска с боро и переписными областями, независимые города Виргинии,
и штаты Новой Англии, где у HUD несколько строк на округ.

Виргиния устроена хитрее, чем кажется. Там, где независимый город тёзка округа,
Redfin пишет «Richmond City County, VA» против «Richmond County, VA», и обе
строки стыкуются сами. Но «James City County» — настоящий округ, а не город
Джеймс, поэтому родовое слово нельзя срезать по подстроке «city»: срезается
только хвост « County», а подстановка « city» пробуется в последнюю очередь и
лишь в четырёх штатах с независимыми городами.

Коннектикут пришлось собирать вручную, и это оказалось возможно точно. Redfin и
Natural Earth знают восемь округов, упразднённых в 2023 году; Income Limits с
FY2024 перешли на девять плановых регионов. Мост — файл аренды: он остался на
старых округах и при этом расписан по 169 городам с населением, а в файле дохода
у тех же 169 городов стоит их плановый регион. Списки городов совпадают полностью,
169 на 169, поэтому доход старого округа считается как среднее по его городам,
взвешенное населением. Это не медиана округа, а взвешенная смесь медиан регионов,
и так это и подписано — но веса настоящие, а не придуманные.

Аляска проще: Valdez-Cordova Census Area упразднена в 2019 году и разделена на
Chugach и Copper River, объединение точное, поэтому округ Redfin собирается из
двух единиц HUD теми же весами.

Непокрытое НЕ отбрасывается молча: причины известных разрывов перечислены в
KNOWN_GAP, они печатаются и пишутся в us-gaps.csv, а любой новый непокрытый округ
валит сборку.
"""
import collections, csv, gzip, io, json, os, re, sys, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(ROOT, 'research', 'data', 'us-counties.csv')
GAPS = os.path.join(ROOT, 'research', 'data', 'us-gaps.csv')
META = os.path.join(ROOT, 'research', 'data', 'us-meta.json')

# Имя файла → откуда взять, если его нет на диске. Redfin сюда не входит: 230 МБ
# качаются долго, а ссылка на выгрузку живёт в Data Center и меняется.
SOURCES = {
    'hud_il25.xlsx': 'https://www.huduser.gov/portal/datasets/il/il25/Section8-FY25.xlsx',
    'hud_fmr25.xlsx': 'https://www.huduser.gov/portal/datasets/fmr/fmr2025/FY25_FMRs_revised.xlsx',
    'pmms.csv': 'https://www.freddiemac.com/pmms/docs/PMMS_history.csv',
    'ne_10m_admin_2_counties.geojson':
        'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/'
        'geojson/ne_10m_admin_2_counties.geojson',
}
REDFIN = 'county_market_tracker.tsv000.gz'
MONTHS = 12                      # окно усреднения: год сделок гасит месячный шум
SQFT_PER_M2 = 10.7639
BEDROOMS = 5                     # fmr_0 … fmr_4: студия и до четырёх спален

COLS = (['fips', 'st', 'county', 'name', 'pop', 'lat', 'lon', 'metro',
         'income_family', 'price_m2', 'median_price', 'sales']
        + ['fmr_%d' % i for i in range(BEDROOMS)])

# Родовые слова, которые в названии округа ничего не различают. Порядок перебора
# задаётся длиной, а не тем, как записано здесь: «Juneau City and Borough» иначе
# теряет только « Borough» и остаётся «juneau city and».
GENERIC = sorted((' county', ' parish', ' borough', ' census area', ' municipality',
                  ' city and borough', ' planning region'), key=len, reverse=True)

# Штаты, где город может не входить ни в один округ и живёт в статистике отдельной
# строкой. Redfin пишет такой город без родового слова («Alexandria, VA»), HUD — со
# словом «city», и это единственное, что отличает его от одноимённого округа.
INDEPENDENT_CITY = {'VA', 'MD', 'MO', 'NV'}

# Разные написания одного и того же округа. Ключ — то, что пишет Redfin.
ALIAS = {
    ('IL', 'lasalle'): 'la salle',
}

# Единица Redfin, которой у HUD отвечают несколько: границы переносились, но
# объединение точное. Valdez-Cordova упразднена в 2019 году и целиком разошлась
# на Chugach и Copper River.
UNION = {
    ('AK', 'valdez cordova'): ['chugach', 'copper river'],
}

# Разрывы, которые остаются после всех правил, с причиной. Пусто — и хорошо;
# всё, чего здесь нет, валит сборку, чтобы новая дыра не проехала незамеченной.
KNOWN_GAP = {}


def fetch(src, name):
    p = os.path.join(src, name)
    if os.path.exists(p):
        return p
    print('скачиваю', name)
    req = urllib.request.Request(SOURCES[name], headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'})
    with urllib.request.urlopen(req, timeout=300) as r, open(p, 'wb') as f:
        f.write(r.read())
    return p


def sheet(path, name=None):
    """Строки листа словарями. Файл аренды HUD чинится на лету: в его docProps
    дата записана как «2025- 2-18T20:40:31Z», и openpyxl отказывается открывать
    книгу целиком из-за поля, которое нам не нужно."""
    import openpyxl
    buf = io.BytesIO()
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            b = zin.read(it.filename)
            if it.filename == 'docProps/core.xml':
                b = re.sub(rb'(\d{4}-)\s*(\d)-', rb'\g<1>0\g<2>-', b)
            zout.writestr(it, b)
    buf.seek(0)
    wb = openpyxl.load_workbook(buf, read_only=True)
    ws = wb[name or wb.sheetnames[0]]
    it = ws.iter_rows(values_only=True)
    hdr = list(next(it))
    return [dict(zip(hdr, r)) for r in it]


def norm(name):
    """Название округа к сравнимому виду: регистр, пунктуация и родовое слово."""
    s = (name or '').lower().strip()
    for a, b in (('.', ''), (',', ''), ('’', "'"), ('-', ' '), ('&', 'and')):
        s = s.replace(a, b)
    for w in GENERIC:
        if s.endswith(w):
            s = s[: -len(w)]
            break
    return ' '.join(s.split())


def keys_for(st, base):
    """Ключи-кандидаты для строки Redfin, в порядке убывания надёжности."""
    n = norm(base)
    yield n
    a = ALIAS.get((st, n))
    if a:
        yield a
    if st in INDEPENDENT_CITY and not base.strip().lower().endswith('county'):
        yield n + ' city'


def read_redfin(path):
    """Средневзвешенная по числу сделок цена за фут и цена жилья за последний год."""
    last = ''
    with gzip.open(path, 'rt', encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            end = row['PERIOD_END'][:7]
            if end > last:
                last = end
    # Второй проход: окно известно только после первого.
    y, m = int(last[:4]), int(last[5:7])
    m -= MONTHS - 1
    while m <= 0:
        m += 12; y -= 1
    first = '%04d-%02d' % (y, m)
    acc = collections.defaultdict(lambda: [0.0, 0.0, 0.0])
    with gzip.open(path, 'rt', encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            if row['PROPERTY_TYPE'] != 'All Residential':
                continue
            if not (first <= row['PERIOD_END'][:7] <= last):
                continue
            try:
                ppsf = float(row['MEDIAN_PPSF'] or 0)
                price = float(row['MEDIAN_SALE_PRICE'] or 0)
                sold = float(row['HOMES_SOLD'] or 0)
            except ValueError:
                continue
            if not (ppsf > 0 and sold > 0):
                continue
            a = acc[(row['STATE_CODE'], row['REGION'])]
            a[0] += ppsf * sold
            a[1] += price * sold
            a[2] += sold
    out = {}
    for (st, region), (sp, pr, n) in acc.items():
        if n > 0:
            out[(st, region)] = (sp / n, pr / n, n)
    return out, first, last


def read_fmr(path):
    """География HUD со старыми округами: (штат, округ) → строки по городам.

    Именно этот файл задаёт единицу американского слоя: только он совпадает и с
    Redfin, и с контурами Natural Earth, и при этом несёт население.
    """
    units = collections.defaultdict(list)
    for d in sheet(path, 'FY25_FMRs_revised'):
        st, cname = d.get('stusps'), d.get('countyname')
        if not (st and cname):
            continue
        units[(st, norm(cname))].append({
            'fips': str(d.get('fips') or '')[:5],
            'town': (d.get('county_town_name') or '').strip(),
            'name': cname,
            'pop': float(d.get('pop2022') or 0),
            'metro': 1 if d.get('metro') else 0,
            'fmr': [float(d.get('fmr_%d' % i) or 0) for i in range(BEDROOMS)],
        })
    return units


def read_income(path):
    """Доход двумя ключами: по округу и по городу.

    Ключ по городу нужен Новой Англии, где на округ приходится до 169 строк, а в
    Коннектикуте — ещё и потому, что округ в этом файле уже другой.
    """
    by_county, by_town = collections.defaultdict(list), {}
    for d in sheet(path):
        st, cname, inc = d.get('stusps'), d.get('County_Name'), d.get('median2025')
        if not (st and cname and inc):
            continue
        by_county[(st, norm(cname))].append(float(inc))
        town = (d.get('county_town_name') or '').strip()
        if town:
            by_town[(st, town)] = float(inc)
    out = {}
    for k, v in by_county.items():
        v.sort()
        out[k] = v[len(v) // 2]
    return out, by_town


def read_centroids(path):
    out = {}
    for f in json.load(open(path, encoding='utf-8'))['features']:
        p = f['properties']
        if p.get('ADM0_A3') == 'USA' and p.get('CODE_LOCAL') and p.get('latitude') is not None:
            out[str(p['CODE_LOCAL']).zfill(5)] = (float(p['latitude']), float(p['longitude']))
    return out


def read_rate(path, first, last):
    """Средняя ставка 30-летней фиксированной за то же окно, что и сделки.

    Не последняя неделя: цены усреднены за год, и ставка обязана быть за тот же
    год, иначе метры считаются по кредиту, которого в этих сделках не было.
    """
    vals = []
    for r in csv.DictReader(open(path, encoding='utf-8')):
        try:
            m, d, y = r['date'].split('/')
        except (AttributeError, ValueError):
            continue
        ym = '%04d-%02d' % (int(y), int(m))
        if first <= ym <= last and (r.get('pmms30') or '').strip():
            vals.append(float(r['pmms30']))
    return (sum(vals) / len(vals), len(vals)) if vals else (0.0, 0)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else HERE
    redfin, first, last = read_redfin(os.path.join(src, REDFIN))
    units = read_fmr(fetch(src, 'hud_fmr25.xlsx'))
    inc_county, inc_town = read_income(fetch(src, 'hud_il25.xlsx'))
    cent = read_centroids(fetch(src, 'ne_10m_admin_2_counties.geojson'))
    rate, weeks = read_rate(fetch(src, 'pmms.csv'), first, last)
    print('Redfin: %d округов, окно %s..%s' % (len(redfin), first, last))
    print('HUD FMR: %d единиц; HUD IL: %d округов и %d городов'
          % (len(units), len(inc_county), len(inc_town)))
    print('PMMS 30 лет: %.2f %% в среднем за %d недель окна' % (rate, weeks))

    rows, miss = [], []
    for (st, region), (ppsf, price, sold) in sorted(redfin.items()):
        base = region.rsplit(',', 1)[0]
        part = None
        for k in keys_for(st, base):
            if (st, k) in units:
                part = units[(st, k)]
                break
            if (st, k) in UNION:
                part = [r for n in UNION[(st, k)] for r in units.get((st, n), [])]
                if part:
                    break
                part = None
        if not part:
            miss.append((st, region, int(sold)))
            continue

        # Вес — население. У обычного округа строка одна и веса ни на что не
        # влияют; у Новой Англии и Аляски они и делают стыковку честной.
        def wavg(get):
            num = den = 0.0
            for p in part:
                v = get(p)
                if v:
                    w = p['pop'] or 1.0
                    num += v * w; den += w
            return num / den if den else 0.0

        income = wavg(lambda p: inc_town.get((st, p['town'])) if p['town'] else None)
        if not income:
            income = inc_county.get((st, norm(part[0]['name']))) or 0.0
        if not income:
            miss.append((st, region, int(sold)))
            continue

        latlon = [cent[p['fips']] for p in part if p['fips'] in cent]
        lat = sum(a for a, _ in latlon) / len(latlon) if latlon else 0.0
        lon = sum(b for _, b in latlon) / len(latlon) if latlon else 0.0
        rows.append([part[0]['fips'], st, part[0]['name'], region,
                     round(sum(p['pop'] for p in part)), round(lat, 4), round(lon, 4),
                     max(p['metro'] for p in part), round(income),
                     round(ppsf * SQFT_PER_M2, 1), round(price), int(sold)]
                    + [round(wavg(lambda p, i=i: p['fmr'][i])) for i in range(BEDROOMS)])

    # Молча терять округа нельзя: так появляется ошибка, которую потом не найти.
    miss.sort(key=lambda x: -x[2])
    print('без пары в HUD: %d из %d (%.1f %%)' % (len(miss), len(redfin),
                                                  100.0 * len(miss) / max(1, len(redfin))))
    if miss:
        print('  по штатам:', dict(collections.Counter(m[0] for m in miss).most_common(8)))
        for st, region, sold in miss[:8]:
            print('    %s · %s · сделок %d' % (st, region, sold))
    unexpected = [m for m in miss if m[0] not in KNOWN_GAP]
    if unexpected:
        raise SystemExit('новые непокрытые округа, разберитесь до сборки: %s'
                         % ([(st, r) for st, r, _ in unexpected[:20]],))

    with open(GAPS, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['st', 'region', 'sales', 'reason'])
        for st, region, sold in miss:
            w.writerow([st, region, sold, KNOWN_GAP[st]])
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(COLS)
        w.writerows(rows)
    json.dump({
        'window': [first, last], 'counties': len(rows), 'gaps': len(miss),
        # Население всех единиц HUD, а не только покрытых Redfin: только так
        # видно, какую долю страны рынок вообще показывает.
        'popTotal': round(sum(p['pop'] for u in units.values() for p in u)),
        'popCovered': round(sum(r[COLS.index('pop')] for r in rows)),
        'rate30': round(rate, 2), 'rateWeeks': weeks,
        'price': 'Redfin Data Center, county market tracker, median price per square foot',
        'income': 'HUD Income Limits FY2025, median family income of the HUD area',
        'rent': 'HUD Fair Market Rents FY2025, 40th percentile gross rent by bedrooms',
        'pop': 'HUD Fair Market Rents FY2025, pop2022',
        'geo': 'Natural Earth 10m admin-2 county centroids',
        'rate': 'Freddie Mac Primary Mortgage Market Survey, 30-year fixed',
    }, open(META, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('%s: %d строк, %d байт' % (os.path.relpath(OUT, ROOT), len(rows), os.path.getsize(OUT)))


if __name__ == '__main__':
    main()
