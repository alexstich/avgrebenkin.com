#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Датасет страницы из CSV по муниципалитетам: страны, регионы NUTS 3, города.

    python3 research/housing-europe/src/data.py      # печатает размеры, пишет data.json

Вход: research/data/house4all-lau-2024.csv (см. extract.py) и src/region-names.json
(см. names.py). Геометрия сюда больше не нужна: имена регионов приходят из
статистической номенклатуры, а не из файла контуров.
Выход: src/data.json — то, что build.py вшивает в страницу переменной DATA.

Что внутри и почему именно столько:
  * countries — 31 страна проекта ESPON плюс три без данных (AL, MK, RS): ставка
    ипотеки, население, взвешенные по населению средние — доступные метры,
    доход, цена и аренда, — и доля населения, у которой вообще есть данные;
  * regions — 1 253 региона NUTS 3, те же взвешенные средние: карта раскрашивается
    по ним, потому что 89 601 полигон LAU в страницу не влезает;
  * places — муниципалитеты от 10 000 жителей плюс самый населённый в каждом
    NUTS 3 (чтобы поиск находил хоть что-то в любом регионе): около 9 000 строк,
    компактными массивами, чтобы страница осталась в пределах мегабайта;
  * hist — население по классам доступности и степени урбанизации, для
    воспроизведения рисунка 3 статьи.

Доступные метры считаются в браузере из дохода, цены и ставки той же формулой,
что у ESPON: sa_m2 = (income24/12/3 · аннуитет(ставка, 30 лет)) / sp_corr,
ra_m2 = (income24/12/3) / rp_corr. Формула проверена на всех 78 758 LAU с данными
о продаже: расхождение с sa_m2 сервиса меньше 1e-9.
"""
import csv, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
CSV = os.path.join(ROOT, 'research', 'data', 'house4all-lau-2024.csv')

NAMES = {
    'AT': 'Austria', 'BE': 'Belgium', 'BG': 'Bulgaria', 'CH': 'Switzerland', 'CY': 'Cyprus',
    'CZ': 'Czechia', 'DE': 'Germany', 'DK': 'Denmark', 'EE': 'Estonia', 'EL': 'Greece',
    'ES': 'Spain', 'FI': 'Finland', 'FR': 'France', 'HR': 'Croatia', 'HU': 'Hungary',
    'IE': 'Ireland', 'IS': 'Iceland', 'IT': 'Italy', 'LI': 'Liechtenstein', 'LT': 'Lithuania',
    'LU': 'Luxembourg', 'LV': 'Latvia', 'MT': 'Malta', 'NL': 'Netherlands', 'NO': 'Norway',
    'PL': 'Poland', 'PT': 'Portugal', 'RO': 'Romania', 'SE': 'Sweden', 'SI': 'Slovenia',
    'SK': 'Slovakia', 'AL': 'Albania', 'MK': 'North Macedonia', 'RS': 'Serbia',
}
# Четыре части Европы для фильтров. Прибалтика идёт с Севером — статья говорит
# о «скандинавских и балтийских странах» одной фразой.
REGION = {
    'north': ['DK', 'FI', 'IS', 'NO', 'SE', 'EE', 'LV', 'LT'],
    'west': ['AT', 'BE', 'CH', 'DE', 'FR', 'IE', 'LU', 'NL', 'LI'],
    'south': ['CY', 'EL', 'ES', 'HR', 'IT', 'MT', 'PT', 'SI'],
    'east': ['BG', 'CZ', 'HU', 'PL', 'RO', 'SK', 'AL', 'MK', 'RS'],
}
ESPON31 = set(NAMES) - {'AL', 'MK', 'RS'}

# Английские экзонимы — только для поиска, не для показа. Названия на странице
# остаются такими, как их даёт источник (Wien, Praha, København): переводить их
# значило бы разойтись с данными, как и у исследования про города. Но читатель
# набирает Vienna и Athens, и без этого списка поиск его не находит. Греческие
# имена вдобавок приходят из таблицы Евростата в родительном падеже
# («Κοινότητα Αθηναίων» → Athinaion), так что там алиас — единственный вход.
ALIAS = {
    ('AT', 'Wien'): 'Vienna',
    ('BE', 'Brussel'): 'Brussels', ('BE', 'Antwerpen'): 'Antwerp', ('BE', 'Gent'): 'Ghent',
    ('BE', 'Luik'): 'Liege',
    ('BG', 'Stolichna'): 'Sofia',
    ('CH', 'Zürich'): 'Zurich', ('CH', 'Genève'): 'Geneva', ('CH', 'Basel'): 'Basle',
    ('CH', 'Bern'): 'Berne',
    ('CY', 'Lefkosia'): 'Nicosia', ('CY', 'Lemesos'): 'Limassol',
    ('CZ', 'Praha'): 'Prague',
    ('DE', 'München, Landeshauptstadt'): 'Munich', ('DE', 'Köln, Stadt'): 'Cologne',
    ('DE', 'Frankfurt am Main, Stadt'): 'Frankfurt', ('DE', 'Nürnberg'): 'Nuremberg',
    ('DE', 'Hannover, Landeshauptstadt'): 'Hanover',
    ('DK', 'København'): 'Copenhagen',
    ('EL', 'Athinaion'): 'Athens', ('EL', 'Thessalonikis'): 'Thessaloniki',
    ('EL', 'Patreon'): 'Patras', ('EL', 'Irakleioy'): 'Heraklion',
    ('EL', 'Peiraios'): 'Piraeus', ('EL', 'Larisaion'): 'Larissa',
    ('ES', 'Sevilla'): 'Seville', ('ES', 'Coruña, A'): 'A Coruna',
    ('HR', 'Grad Zagreb'): 'Zagreb',
    ('IT', 'Roma'): 'Rome', ('IT', 'Milano'): 'Milan', ('IT', 'Napoli'): 'Naples',
    ('IT', 'Torino'): 'Turin', ('IT', 'Firenze'): 'Florence', ('IT', 'Venezia'): 'Venice',
    ('IT', 'Genova'): 'Genoa', ('IT', 'Padova'): 'Padua',
    ('LT', 'Vilniaus miesto savivaldybė'): 'Vilnius',
    ('LT', 'Kauno miesto savivaldybė'): 'Kaunas',
    ('LT', 'Klaipėdos miesto savivaldybė'): 'Klaipeda',
    ('LT', 'Šiaulių miesto savivaldybė'): 'Siauliai',
    ('NL', "'s-Gravenhage"): 'The Hague',
    ('PL', 'Warszawa'): 'Warsaw',
    ('RO', 'Municipiul Bucureşti'): 'Bucharest', ('RO', 'Municipiul Cluj-Napoca'): 'Cluj',
    ('RO', 'Municipiul Timişoara'): 'Timisoara', ('RO', 'Municipiul Iaşi'): 'Iasi',
    ('RO', 'Municipiul Constanţa'): 'Constanta',
    ('SE', 'Göteborg'): 'Gothenburg',
}
CLASSES = [50, 75, 100, 150]          # границы классов легенды статьи
POP_MIN = 10000


def f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def cls(v):
    """Класс доступности по легенде рисунков 1 и 2: <50, 50–75, 76–100, 101–150, >150 м²."""
    if not v:
        return 5
    for i, b in enumerate(CLASSES):
        if v <= b:
            return i
    return 4


def wmean(rows, key, weight='pop', where=None):
    num = den = 0.0
    for r in rows:
        if r[key] and (where is None or where(r)):
            num += r[key] * r[weight]; den += r[weight]
    return num / den if den else 0.0


def main():
    rows = []
    with open(CSV, encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            if not r['mun_id'].strip():
                continue
            rows.append({
                'id': r['mun_id'], 'cc': r['cc'], 'name': r['name'], 'nuts3': r['nuts3'],
                'pop': f(r['pop']), 'inc': f(r['income24']), 'sp': f(r['sp_corr']), 'rp': f(r['rp_corr']),
                'rate': f(r['rate']), 'sa': f(r['sa_m2']), 'ra': f(r['ra_m2']),
                'lat': f(r['lat']), 'lon': f(r['lon']),
                'deg': int(r['degurba']) if r['degurba'] else 0,
                'coast': int(r['coastal']) if r['coastal'] else 0,
                'sl': f(r['s_listings']), 'rl': f(r['r_listings']),
                'sp_a': f(r['sp_a']), 'sp_b': f(r['sp_b']), 'sp_c': f(r['sp_c']),
                'sp_d': f(r['sp_d']), 'sp_e': f(r['sp_e']),
                'rp_a': f(r['rp_a']), 'rp_b': f(r['rp_b']), 'rp_c': f(r['rp_c']),
                'rp_d': f(r['rp_d']), 'rp_e': f(r['rp_e']),
            })
    rnames = json.load(open(os.path.join(HERE, 'region-names.json'), encoding='utf-8'))

    # ---- страны
    region_of = {c: k for k, cs in REGION.items() for c in cs}
    countries = []
    by_cc = {}
    for r in rows:
        by_cc.setdefault(r['cc'], []).append(r)
    for cc in sorted(by_cc):
        rs = by_cc[cc]
        pop = sum(r['pop'] for r in rs)
        rates = {}
        for r in rs:
            if r['rate']:
                rates[r['rate']] = rates.get(r['rate'], 0) + 1
        rate = max(rates, key=rates.get) if rates else 0
        countries.append({
            'c': cc, 'n': NAMES.get(cc, cc), 'reg': region_of.get(cc, ''), 'espon': cc in ESPON31,
            'rate': rate, 'pop': round(pop),
            'sa': round(wmean(rs, 'sa'), 1), 'ra': round(wmean(rs, 'ra'), 1),
            'inc': round(wmean(rs, 'inc')), 'sp': round(wmean(rs, 'sp')), 'rp': round(wmean(rs, 'rp'), 2),
            'covS': round(sum(r['pop'] for r in rs if r['sa']) / pop, 3) if pop else 0,
            'covR': round(sum(r['pop'] for r in rs if r['ra']) / pop, 3) if pop else 0,
            'places': len(rs),
            # Валюта самих данных, а не читателя: таблица ESPON целиком в евро.
            # Источник помечен, потому что «Where the numbers come from» должен
            # показывать построчно, откуда взята каждая страна.
            'cur': 'EUR', 'src': 'espon',
        })

    # ---- NUTS 3
    by_n3 = {}
    for r in rows:
        if r['nuts3'].strip():
            by_n3.setdefault(r['nuts3'], []).append(r)
    regions = []
    n3index = {}
    for code in sorted(by_n3):
        rs = by_n3[code]
        pop = sum(r['pop'] for r in rs)
        n3index[code] = len(regions)
        regions.append([
            code, rnames.get(code, code), rs[0]['cc'], round(pop),
            round(wmean(rs, 'inc')), round(wmean(rs, 'sp')), round(wmean(rs, 'rp'), 2),
            round(wmean(rs, 'sa'), 1), round(wmean(rs, 'ra'), 1),
            round(sum(r['pop'] for r in rs if r['sa']) / pop, 2) if pop else 0,
            round(sum(r['pop'] for r in rs if r['ra']) / pop, 2) if pop else 0,
        ])

    # ---- муниципалитеты: крупные плюс по одному на регион
    cc_index = {c['c']: i for i, c in enumerate(countries)}
    keep = set()
    for r in rows:
        if r['pop'] >= POP_MIN and (r['sa'] or r['ra']):
            keep.add(r['id'])
    for code, rs in by_n3.items():
        best = max(rs, key=lambda r: (1 if (r['sa'] or r['ra']) else 0, r['pop']))
        if best['sa'] or best['ra']:
            keep.add(best['id'])
    # Каждый алиас обязан найти свою строку: имя в сервисе меняется молча, и без
    # этой проверки поиск по «Vienna» однажды перестал бы работать незаметно.
    seen_alias = set()
    places = []
    for r in rows:
        if r['id'] not in keep:
            continue
        if (r['cc'], r['name']) in ALIAS:
            seen_alias.add((r['cc'], r['name']))
        places.append([
            r['id'], r['name'], cc_index[r['cc']], n3index.get(r['nuts3'], -1), round(r['pop']),
            round(r['inc']), round(r['sp']), round(r['rp'] * 10), round(r['lat'] * 100), round(r['lon'] * 100),
            r['deg'], r['coast'],
        ])
    lost = sorted(set(ALIAS) - seen_alias)
    if lost:
        raise SystemExit('алиасы не нашли своих строк: %s' % (lost,))
    aliases = {r['id']: ALIAS[(r['cc'], r['name'])] for r in rows
               if (r['cc'], r['name']) in ALIAS and r['id'] in keep}
    places.sort(key=lambda x: -x[4])

    # ---- рисунок 3: население по классам × степень урбанизации
    def hist(key):
        m = [[0.0] * 4 for _ in range(6)]       # 6 классов (5 + нет данных) × (город, пригород, село, не размечено)
        for r in rows:
            if r['cc'] not in ESPON31:
                continue
            d = {1: 0, 2: 1, 3: 2}.get(r['deg'], 3)
            m[cls(r[key])][d] += r['pop']
        return [[round(v / 1e6, 3) for v in row] for row in m]

    total31 = sum(r['pop'] for r in rows if r['cc'] in ESPON31)
    # ---- надбавка за размер: отношение цены класса к общей, медиана по стране
    # Сервис отдаёт цену по пяти классам площади, и она заметно нелинейна: метр в
    # маленькой квартире дороже. Отношение берётся медианой по муниципалитетам
    # страны, а не по каждому месту отдельно: по классам данных втрое меньше, чем
    # по общей цене, и на уровне места они рваные. Стран с малым числом наблюдений
    # ставится общеевропейская медиана, чтобы не было дыр.
    CK = ['a', 'b', 'c', 'd', 'e']
    MIN_N = 30

    def med(v):
        v = sorted(v)
        return round(v[len(v) // 2], 3) if v else None

    def ratios(prefix, base):
        per_cc, pooled = {}, {k: [] for k in CK}
        for r in rows:
            b = r.get(base) or 0
            if not b:
                continue
            for k in CK:
                v = r.get(prefix + k) or 0
                # Связки отбрасываются. Если у муниципалитета объявления только в
                # одном классе, сервис кладёт в поле класса ту же общую цену — это
                # одно число, записанное дважды, и о зависимости цены от размера оно
                # не говорит ничего. Таких строк от 13 % в Румынии до 82 % в
                # крупнейшем классе Мальты, и медиана по ним ложилась ровно на 1.00,
                # то есть «надбавки нет» вместо «неизвестно». У Румынии кривая
                # выпрямлялась в 1.00 на всех классах, и страна ехала на 13 мест в
                # рейтинге по чисто счётной причине.
                if v and abs(v / b - 1) > 1e-9:
                    per_cc.setdefault(r['cc'], {k2: [] for k2 in CK})[k].append(v / b)
                    pooled[k].append(v / b)
        eu = [med(pooled[k]) or 1.0 for k in CK]
        out_cc = {}
        for cc, d in per_cc.items():
            out_cc[cc] = [(med(d[k]) if len(d[k]) >= MIN_N else None) or eu[i]
                          for i, k in enumerate(CK)]
        return {'eu': eu, 'cc': out_cc}

    size = {'edges': [30, 60, 90, 120], 'mids': [25, 45, 75, 100, 200],
            'sp': ratios('sp_', 'sp'), 'rp': ratios('rp_', 'rp')}

    out = {
        'classes': CLASSES, 'size': size,
        'popTotal': round(total31),
        'countries': countries, 'regions': regions, 'places': places,
        'hist': {'sale': hist('sa'), 'rent': hist('ra')},
        'aliases': aliases,
        'placefields': ['id', 'name', 'cc', 'reg', 'pop', 'inc', 'sp', 'rp10', 'lat100', 'lon100', 'deg', 'coast'],
        'regionfields': ['id', 'name', 'cc', 'pop', 'inc', 'sp', 'rp', 'sa', 'ra', 'covS', 'covR'],
    }
    p = os.path.join(HERE, 'data.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('data.json: %d стран, %d регионов, %d мест, %d английских алиасов, %d байт'
          % (len(countries), len(regions), len(places), len(aliases), os.path.getsize(p)))
    for k in ('sale', 'rent'):
        h = out['hist'][k]
        print(k, [round(sum(row) / total31 * 1e8) / 1e0 for row in h])


if __name__ == '__main__':
    main()
