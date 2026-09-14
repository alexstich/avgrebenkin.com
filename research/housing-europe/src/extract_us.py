#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Американский слой: цена за метр и доход по округам США.

    python3 research/housing-europe/src/extract_us.py [папка с исходниками]

Два источника, оба открытые и без ключа.

1. Redfin Data Center, county_market_tracker.tsv000.gz — помесячные медианы по
   округам: медианная цена продажи и медианная цена за квадратный ФУТ, обе по
   фактическим сделкам. Свободное использование с указанием источника.

2. HUD Income Limits, Section8-FY25.xlsx — медианный доход по всем округам.

ВАЖНАЯ ОГОВОРКА, которая обязана попасть на страницу: у HUD это медианный доход
СЕМЬИ, а не домохозяйства. Семьи не включают одиночек, поэтому величина
систематически выше медианного дохода домохозяйства, и с европейским
эквивалентным располагаемым доходом на взрослого-эквивалента она несопоставима
напрямую. В таблице происхождения это отдельная строка, а не та же колонка.

Площадь НЕ получается делением медианной цены на медианную цену за фут: отношение
медиан не равно медиане отношений, а на рынке, где смешаны квартиры и дома,
расхождение заметное. Поэтому бюджет из дохода и ставки делится прямо на цену за
фут, без единого допущения о площади.

ВТОРАЯ ОГОВОРКА, не менее важная. HUD задаёт доход не по округу, а по своей
зоне (HMFA): все округа одной агломерации получают одно и то же число. Атланта —
24 округа с $114 200 на всех, Вашингтон — 14. Из 1133 метро-округов различных
значений дохода всего 625, из 1901 неметро-округа — 1747. Значит внутри
агломерации карта показывает только разброс цен, а не разброс доходов, и это надо
сказать читателю прямо, а не надеяться, что он догадается.

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

Непокрытое НЕ отбрасывается молча: причины известных разрывов перечислены в
KNOWN_GAP, они печатаются и пишутся в us-gaps.csv, а любой новый непокрытый округ
валит сборку. Сейчас известных девять из 3043 — весь Коннектикут и одна
упразднённая переписная область Аляски.
"""
import collections, csv, gzip, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(ROOT, 'research', 'data', 'us-counties.csv')
GAPS = os.path.join(ROOT, 'research', 'data', 'us-gaps.csv')
REDFIN = 'county_market_tracker.tsv000.gz'
HUD = 'hud_il25.xlsx'
MONTHS = 12                      # окно усреднения: год сделок гасит месячный шум
SQFT_PER_M2 = 10.7639

COLS = ['fips', 'st', 'county', 'name', 'income_family', 'metro',
        'price_m2', 'median_price', 'sales']


# Родовые слова, которые в названии округа ничего не различают. Порядок перебора
# задаётся длиной, а не тем, как записано здесь: «Juneau City and Borough» иначе
# теряет только « Borough» и остаётся «juneau city and», а HUD ждёт «juneau».
GENERIC = sorted((' county', ' parish', ' borough', ' census area', ' municipality',
                  ' city and borough', ' planning region'), key=len, reverse=True)

# Штаты, где город может не входить ни в один округ и живёт в статистике отдельной
# строкой. Redfin пишет такой город без родового слова («Alexandria, VA»), HUD — с
# маленькой буквы («Alexandria city»), и это единственное, что отличает его от
# одноимённого округа. Подстановка « city» пробуется только здесь и только после
# того, как прямое совпадение не нашлось: в Виргинии есть и Richmond County, и
# Richmond city, и перепутать их нельзя.
INDEPENDENT_CITY = {'VA', 'MD', 'MO', 'NV'}

# Разные написания одного и того же округа. Ключ — то, что пишет Redfin.
ALIAS = {
    ('IL', 'lasalle'): 'la salle',
}

# Расхождения не в написании, а в самой географии: пара не находится потому, что
# два источника делят страну по-разному. Причина записывается здесь и попадает и в
# отчёт сборки, и в файл пропусков — чтобы на странице было что сказать читателю,
# который не найдёт свой округ. Всё, чего здесь нет, печатается как неожиданное.
KNOWN_GAP = {
    'CT': ('Redfin публикует Коннектикут по восьми округам, упразднённым в 2023 году, '
           'HUD с FY2024 — по девяти плановым регионам. Границы не вложены друг в '
           'друга: Фэрфилд делится между Greater Bridgeport и Western Connecticut с '
           'очень разным доходом. Честной стыковки без переписных весов по 169 '
           'городам нет, поэтому штат остаётся без данных.'),
    'AK': ('Valdez-Cordova Census Area упразднена в 2019 году и разделена на Chugach '
           'и Copper River; Redfin всё ещё пишет старое название, HUD — новые.'),
}


def norm(name):
    """Название округа к сравнимому виду: регистр, пунктуация и родовое слово."""
    s = name.lower().strip()
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
        if n <= 0:
            continue
        out[(st, region)] = (sp / n, pr / n, n)
    return out, first, last


def read_hud(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb[wb.sheetnames[0]]
    it = ws.iter_rows(values_only=True)
    hdr = list(next(it))
    # У штатов Новой Англии на округ приходится несколько строк (по городам),
    # поэтому строки сворачиваются: берётся медиана по строкам округа.
    grp = collections.defaultdict(list)
    meta = {}
    for r in it:
        d = dict(zip(hdr, r))
        st, cname = d.get('stusps'), d.get('County_Name')
        inc = d.get('median2025')
        if not (st and cname and inc):
            continue
        k = (st, norm(cname))
        grp[k].append(float(inc))
        meta.setdefault(k, (str(d.get('state') or '') + str(d.get('county') or ''),
                            cname, 1 if d.get('metro') else 0))
    out = {}
    for k, v in grp.items():
        v.sort()
        out[k] = (v[len(v) // 2], meta[k])
    return out


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else HERE
    redfin, first, last = read_redfin(os.path.join(src, REDFIN))
    hud = read_hud(os.path.join(src, HUD))
    print('Redfin: %d округов, окно %s..%s' % (len(redfin), first, last))
    print('HUD: %d округов после свёртки' % len(hud))

    rows, miss = [], []
    for (st, region), (ppsf, price, sold) in sorted(redfin.items()):
        base = region.rsplit(',', 1)[0]
        h = None
        for k in keys_for(st, base):
            h = hud.get((st, k))
            if h:
                break
        if not h:
            miss.append((st, region, int(sold)))
            continue
        inc, (fips, cname, metro) = h
        rows.append([fips, st, cname, region, round(inc), metro,
                     round(ppsf * SQFT_PER_M2, 1), round(price), int(sold)])

    # Молча терять округа нельзя: так появляется ошибка, которую потом не найти.
    miss.sort(key=lambda x: -x[2])
    share = 100.0 * len(miss) / max(1, len(redfin))
    print('без пары в HUD: %d из %d (%.1f %%)' % (len(miss), len(redfin), share))
    by_st = collections.Counter(m[0] for m in miss)
    if miss:
        print('  по штатам:', dict(by_st.most_common(8)))
        print('  крупнейшие по числу сделок:')
        for st, region, sold in miss[:8]:
            print('    %s · %s · сделок %d' % (st, region, sold))
        print('  причины:', ', '.join(sorted(by_st)))

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
    print('%s: %d строк, %d байт' % (os.path.relpath(OUT, ROOT), len(rows), os.path.getsize(OUT)))


if __name__ == '__main__':
    main()
