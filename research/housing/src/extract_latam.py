#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Латиноамериканский слой: цена жилья за квадратный метр там, где она открыта.

    python3 research/housing/src/extract_latam.py [папка с исходниками]

Недостающие файлы скачиваются в эту папку сами.

ПОЧЕМУ ЗДЕСЬ ТОЛЬКО ДВА ГОРОДА, А НЕ РЕГИОН
--------------------------------------------
Латинская Америка проверена целиком: национальные статистики Мексики, Колумбии,
Перу, Бразилии, Аргентины, Чили и Уругвая, плюс межстрановые источники —
CEPALSTAT, Межамериканский банк развития, Всемирный банк, UN-Habitat, OECD.

Цена жилья ЗА КВАДРАТНЫЙ МЕТР под лицензией, которая разрешает переопубликацию
без чьего-либо согласия, нашлась ровно в двух местах: районы Лимы и кварталы
Буэнос-Айреса. Всё остальное отпадает, и причина у каждого своя — она записана
в latam-gaps.csv, а не подразумевается.

Отдельно стоит назвать то, что выглядело перспективным и не прошло:
  * CEPALSTAT (комиссия ООН) — лучший охват региона, но «may not be used,
    reproduced or transmitted… without permission in writing from the publisher»;
  * Межамериканский банк развития — 225 наборов по жилью, но license_id пустой,
    а корпоративный стандарт CC-IGO BY-NC-ND запрещает и коммерцию, и производные;
  * UN-Habitat — показатель «цена жилья к доходу» по городам существует, но
    данные в нём за 1993–1998 годы;
  * кадастр Чили — содержит и оценку, и площадь построек, но массовой выгрузки
    нет, а перепродают её частники на своих условиях;
  * Бразилия — данные отличные и бесплатные (см. ниже), но текст лицензии
    подтвердить не удалось: страницы условий отдают 404, портал открытых данных
    вместо лицензии показывает заглушку «Texto destinado a exibição…».

БРАЗИЛИЯ НЕ ВКЛЮЧЕНА НАМЕРЕННО. У неё есть открытый интерфейс без ключа
(apisidra.ibge.gov.br), доход по 5 570 муниципалитетам из переписи 2022 и
стоимость строительства метра по 27 штатам с помесячной свежестью до августа
2026. Технически это лучший охват в регионе. Но пока не прочитан текст лицензии,
слой не строится — это то же правило, по которому из страницы был убран Redfin.
Что проверить: условия использования IBGE и карточки наборов IBGE на dados.gov.br.

ИСТОЧНИКИ
---------
1. ПЕРУ. Banco Central de Reserva del Perú, категория серий «Mercado
   inmobiliario»: цена продажи квартир в долларах за квадратный метр по 12
   районам Лимы, поквартально с 2008 (для двух районов с 2013) по IV квартал
   2025, плюс отношение цены продажи к годовой аренде по тем же районам.
   Берётся через открытый интерфейс estadisticas.bcrp.gob.pe, без ключа.
   Лицензия, дословно со страницы https://www.bcrp.gob.pe/condiciones-de-uso.html:
   «Puede reproducirse total o parcialmente, sin autorización expresa, siempre y
   cuando se cite la fuente». Ни запрета на коммерческое использование, ни
   требования письменного согласия.

   ВАЖНО ПРО ДОСТУП: сайт www.bcrp.gob.pe (где лежат xlsx с микроданными сделок)
   закрыт защитой Imperva и отдаёт обычным клиентам страницу-заглушку вместо
   файла. Обходить её нельзя и не нужно: те же показатели публикуются рядом,
   на estadisticas.bcrp.gob.pe, обычным JSON без всякой защиты. Этот скрипт
   берёт данные оттуда.

2. АРГЕНТИНА. Buenos Aires Data, Instituto de Vivienda: средняя цена предложения
   в долларах за квадратный метр по кварталам города (barrios), с разбивкой по
   числу комнат и по новостройкам/вторичке. Лицензия в поле «Licencia» карточки
   набора: CC-BY-2.5-AR (Creative Commons Atribución 2.5 Argentina) — коммерческое
   использование и производные разрешены при указании авторства.

3. OECD Affordable Housing Database, лист HC1.2.1.a: медианная доля платежей
   по ипотеке (тело и проценты) или аренды в доходе домохозяйства, по годам.
   Коммунальные платежи и налоги сюда не входят. Из Латинской Америки покрыты
   Чили, Колумбия, Коста-Рика и Мексика. Для Чили, Колумбии и Мексики OECD
   делит на доход ДО налогов, для Коста-Рики — на располагаемый (сноска 2
   листа): между собой эти четыре цифры сравниваются с оговоркой. Чилийский
   2020 год (0,32) — пандемийный выпуск обследования CASEN, выброс, а не тренд.
   Лицензия OECD по умолчанию — CC BY 4.0.

ОГОВОРКА ПЕРВАЯ: это два города, а не континент. Лима и Буэнос-Айрес — столицы,
и цены в них не говорят ничего о стране. Подписывать надо городом, а не флагом.

ОГОВОРКА ВТОРАЯ: разные величины. Перу — цена СДЕЛОК, собранная центральным
банком у застройщиков и агентств. Аргентина — цена ПРЕДЛОЖЕНИЯ из объявлений,
то есть то же, что в европейском слое. Сравнивать их напрямую нельзя.

ОГОВОРКА ТРЕТЬЯ: свежесть разная и у Аргентины плохая. Перу доведено до IV
квартала 2025. Аргентинский ряд на портале обрывается на II квартале 2019:
свежая серия (до II квартала 2026) публикуется городским статистическим
институтом на estadisticaciudad.gob.ar, и там нет ни слова о лицензии — я
проверял страницу целиком. По правилу страницы она не берётся.

ОГОВОРКА ЧЕТВЁРТАЯ: местного дохода в этом слое нет. У Перу доход по районам
Лимы есть только в обследовании ENAHO (INEI), где текст условий найти не
удалось; у Буэнос-Айреса доход публикуется по агломерации, а не по кварталам.
Это не блокирует страницу: её калькулятор считает от дохода ЧИТАТЕЛЯ, а не от
местного. Но «средний местный житель» для этих городов не показывается, и в
latam-gaps.csv записано почему.

СТАВКА ИПОТЕКИ. Режим «сколько метров можно купить» без ставки не считается.
Для Лимы она берётся из того же центрального банка и под той же лицензией:
серия PN07857NM — средняя ставка банков по ипотеке в долларах (ME, moneda
extranjera), в эффективных годовых процентах (TEA), усреднённая по трём месяцам
того же квартала, что и цены. Доллары выбраны потому, что в долларах и цены.
У Буэнос-Айреса своей ставки в слое нет, и чужая не подставляется: страница
считает там покупку только по ставке, которую читатель ввёл сам.

КОНТУРЫ РАЙОНОВ. Лицензия каждого прочитана в первоисточнике, а не в пересказе:
  * Лима — «Peru - Subnational Administrative Boundaries» на HDX (OCHA),
    источник Instituto Geográfico Nacional. Поле license_id карточки набора:
    cc-by-igo, то есть CC BY 3.0 IGO; раздел 3 текста лицензии разрешает
    воспроизводить и делать производные работы при пометке, что оригинал
    изменён, — контуры упрощены, и страница об этом говорит. geoBoundaries,
    первый кандидат, не подошёл не по лицензии, а по содержанию: у Перу там
    есть только провинции (ADM2), районов (ADM3) нет вовсе;
  * Буэнос-Айрес — набор «Barrios» того же портала Buenos Aires Data, поле
    «Licencia» карточки и license_id его метаданных: CC-BY-2.5-AR, как у цен.
Контуры упрощаются здесь же, чтобы в репозиторий не ложились 74 МБ исходника.

Непокрытое НЕ отбрасывается молча: каждый пропуск попадает в latam-gaps.csv
с причиной — и решения о контурах тоже.
"""
import csv, io, json, math, os, sys, unicodedata, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
DATA = os.path.join(ROOT, 'research', 'data')
OUT_PE = os.path.join(DATA, 'latam-pe-lima.csv')
OUT_AR = os.path.join(DATA, 'latam-ar-caba.csv')
OUT_OECD = os.path.join(DATA, 'latam-oecd.csv')
GAPS = os.path.join(DATA, 'latam-gaps.csv')
META = os.path.join(DATA, 'latam-meta.json')
OUT_GEO = os.path.join(DATA, 'latam-geo.json')

UA = 'avgrebenkin.com/research/housing (+https://avgrebenkin.com/research/housing/)'

BCRP_META = 'https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata'
BCRP_API = 'https://estadisticas.bcrp.gob.pe/estadisticas/series/api'
AR_SALE = ('https://cdn.buenosaires.gob.ar/datosabiertos/datasets/'
           'instituto-de-vivienda/mercado-inmobiliario/precio-venta-deptos.csv')
AR_RENT = ('https://cdn.buenosaires.gob.ar/datosabiertos/datasets/'
           'instituto-de-vivienda/mercado-inmobiliario/precio-alquiler-deptos.csv')
OECD_HC12 = ('https://webfs.oecd.org/els-com/Affordable_Housing_Database/'
             'HC1-2-Housing-costs-over-income.xlsx')
BCRP_RATE = 'PN07857NM'
# Ссылка на ресурс берётся из API карточки HDX, а не вшивается: у ресурса в
# адресе его uuid, и при новом выпуске он меняется.
HDX_PER = 'https://data.humdata.org/api/3/action/package_show?id=cod-ab-per'
HDX_PER_PAGE = 'https://data.humdata.org/dataset/cod-ab-per'
AR_BARRIOS = ('https://cdn.buenosaires.gob.ar/datosabiertos/datasets/'
              'innovacion-transformacion-digital/barrios/barrios.geojson')
AR_BARRIOS_PAGE = 'https://data.buenosaires.gob.ar/dataset/barrios'

# Из Латинской Америки в базе OECD есть только эти четыре страны-члена.
OECD_LATAM = ['Chile', 'Colombia', 'Costa Rica', 'Mexico']

gaps = []


def note(scope, item, reason):
    gaps.append({'scope': scope, 'item': item, 'reason': reason})


def fetch(url, path, binary=True):
    """Скачивает один раз и кладёт рядом: повторный запуск не ходит в сеть."""
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=180) as r, open(path, 'wb') as f:
        f.write(r.read())
    return path


# ---------------------------------------------------------------- Перу

def peru(src):
    """12 районов Лимы: доллары за м² и отношение цены к годовой аренде."""
    meta = fetch(BCRP_META, os.path.join(src, 'bcrp-metadata.csv'))
    rows = list(csv.reader(open(meta, encoding='latin-1'), delimiter=';'))
    hdr = rows[0]
    iCode, iGrp, iNom = 0, hdr.index('Grupo de serie'), hdr.index('Nombre de serie')
    iFin = hdr.index('Fecha de fin')

    sale, ratio = {}, {}
    for r in rows[1:]:
        if len(r) <= iFin:
            continue
        g, n = r[iGrp], r[iNom].strip()
        if 'descontinuada' in n.lower():
            continue
        # «Venta de departamentos por distrito (dólares corrientes por m2)»
        if g.startswith('Venta de departamentos por distrito'):
            sale[n] = (r[iCode], r[iFin])
        # «Indicador Precio de Venta/Alquiler Anual» — во сколько годовых аренд
        # обходится покупка. Обратная величина даёт аренду за м² в год.
        elif g.startswith('Indicador Precio de Venta/Alquiler'):
            ratio[n] = (r[iCode], r[iFin])

    if not sale:
        raise SystemExit('BCRP: серии по районам не найдены — изменилась структура каталога')

    codes = [c for c, _ in sale.values()] + [c for c, _ in ratio.values()]
    end = max(f for _, f in sale.values())          # напр. «T4-2025»
    q, year = end.split('-')[0], end.split('-')[1]
    start = f'{int(year) - 1}-1'
    url = f'{BCRP_API}/{"-".join(codes)}/json/{start}/{year}-{q[1]}'
    raw = json.load(open(fetch(url, os.path.join(src, 'bcrp-lima.json')), encoding='utf-8'))

    # Сопоставление ТОЛЬКО по коду серии. Имя района стоит в хвосте и у цены,
    # и у отношения цены к аренде: поиск по имени находил цену дважды, и
    # «аренда» выходила ровно 1/12 во всех районах. Интерфейс возвращает серии
    # в порядке запроса — это проверяется, а не предполагается.
    names = [s['name'] for s in raw['config']['series']]
    if len(names) != len(codes):
        raise SystemExit(f'BCRP: запрошено {len(codes)} серий, пришло {len(names)}')
    who = {c: d for t in (sale, ratio) for d, (c, _) in t.items()}
    for code, nm in zip(codes, names):
        mine = who[code]
        if not nm.rstrip().endswith(mine):
            raise SystemExit(f'BCRP: порядок серий сбит — {code} ожидался «{mine}», пришёл «{nm}»')

    last = raw['periods'][-1]
    period = last['name']

    def num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None
    by_code = {c: num(v) for c, v in zip(codes, last['values'])}

    rows_out = []
    for district in sorted(sale):
        price = by_code[sale[district][0]]
        if price is None:
            note('PE', district, f'нет значения цены за м² в {period}')
            continue
        years = by_code[ratio[district][0]] if district in ratio else None
        if years is None:
            note('PE', district, 'нет отношения цены к аренде — аренда за м² не считается')
        rows_out.append({
            'city': 'Lima', 'country': 'PE', 'district': district,
            'period': period, 'usd_m2': round(price, 2),
            'price_to_rent_years': round(years, 2) if years else '',
            'rent_usd_m2_month': round(price / years / 12, 2) if years else '',
        })
    return rows_out, period


# ----------------------------------------------------------- Аргентина

# Источник делит каждый квартал на срезы: 2 комнаты вторичка, 3 комнаты
# вторичка, 3 комнаты новостройка («A estrer» — так в файле). Среднее по
# срезам делало кварталы несравнимыми: где новостроек нет, цена занижена.
# Главная цифра — один срез с самым широким охватом, остальные — колонками.
AR_MAIN = ('3 ambientes', 'Usado')
AR_EXTRA = {'usd_m2_2amb_used': ('2 ambientes', 'Usado'),
            'usd_m2_3amb_new': ('3 ambientes', 'A estrer')}


def argentina(src):
    """Кварталы Буэнос-Айреса: доллары за м² предложения, последний непустой срез."""
    path = fetch(AR_SALE, os.path.join(src, 'caba-venta.csv'))
    rd = list(csv.DictReader(open(path, encoding='utf-8-sig'), delimiter=';'))
    if not rd:
        raise SystemExit('CABA: пустой файл цен продажи')

    def price(r):
        try:
            return float(r['precio_prom'])
        except ValueError:
            return None

    filled = [r for r in rd if price(r) is not None]
    if not filled:
        raise SystemExit('CABA: во всём файле нет ни одной цены')
    y = max(int(r['año']) for r in filled)
    q = max(int(r['trimestre']) for r in filled if int(r['año']) == y)
    period = f'{y} Q{q}'

    cell, comuna = {}, {}
    for r in filled:
        if int(r['año']) == y and int(r['trimestre']) == q:
            b = r['barrio'].strip()
            cell[(b, r['ambientes'], r['estado'])] = price(r)
            comuna[b] = r['comuna'].strip()

    out = []
    for b in sorted({r['barrio'].strip() for r in rd}):
        if b not in comuna:
            note('AR', b, f'ни одной цены в {period}')
            continue
        main = cell.get((b, *AR_MAIN))
        if main is None:
            note('AR', b, f'нет среза «3 комнаты, вторичка» в {period} — есть только другие')
            continue
        row = {'city': 'Buenos Aires', 'country': 'AR', 'district': b,
               'comuna': comuna[b], 'period': period, 'usd_m2': round(main, 2)}
        for col, key in AR_EXTRA.items():
            v = cell.get((b, *key))
            row[col] = round(v, 2) if v is not None else ''
        out.append(row)
    return out, period


# ---------------------------------------------------------------- OECD

OECD_SHEET = 'HC12_A1_a'
# Сноска 2 листа HC1.2.1.a, дословно: «In Chile, Colombia, Mexico, Korea and
# the United States, gross income instead of disposable income is used».
OECD_GROSS = {'Chile', 'Colombia', 'Mexico'}


def oecd(src):
    """Медианная доля ипотеки или аренды в доходе, по годам, четыре страны."""
    try:
        import openpyxl
    except ImportError:
        note('OECD', 'все страны', 'openpyxl не установлен — слой пропущен')
        return [], None
    path = fetch(OECD_HC12, os.path.join(src, 'oecd-hc12.xlsx'))
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)[OECD_SHEET]
    grid = [list(r) for r in ws.iter_rows(values_only=True)]

    # Строка заголовка — та, где подряд идут годы. Колонки берутся из неё,
    # а не «первое число в строке»: так в прошлый раз вышел 2010 год вместо
    # последнего.
    hdr = next(r for r in grid if sum(isinstance(c, int) and 2000 < c < 2100 for c in r) >= 5)
    years = {i: c for i, c in enumerate(hdr) if isinstance(c, int) and 2000 < c < 2100}

    out = []
    for r in grid:
        name = str(r[0]).strip() if r and r[0] is not None else ''
        if name not in OECD_LATAM:
            continue
        series = {years[i]: r[i] for i in years
                  if i < len(r) and isinstance(r[i], (int, float))}
        if not series:
            note('OECD', name, 'в строке нет ни одного значения')
            continue
        ly = max(series)
        out.append({
            'country': name, 'year': ly, 'share': round(series[ly], 4),
            'income_basis': 'gross' if name in OECD_GROSS else 'disposable',
            'series': ' '.join(f'{k}:{series[k]:.4f}' for k in sorted(series)),
        })
    for c in OECD_LATAM:
        if c not in {o['country'] for o in out}:
            note('OECD', c, f'страна не найдена на листе {OECD_SHEET}')
    return out, OECD_SHEET


# ------------------------------------------------------- ставка Перу

def peru_rate(src, period):
    """Средняя TEA по долларовой ипотеке за три месяца квартала цен.

    Серия запрашивается одна: интерфейс BCRP возвращает несколько серий не в
    том порядке, в каком их просили (проверено на паре MN/ME), и сопоставлять
    их по позиции нельзя.
    """
    q, yy = period[1], period.split('.')[1]          # «T4.25»
    y, m0 = 2000 + int(yy), (int(q) - 1) * 3 + 1
    url = f'{BCRP_API}/{BCRP_RATE}/json/{y}-{m0}/{y}-{m0 + 2}'
    raw = json.load(open(fetch(url, os.path.join(src, f'bcrp-rate-{y}q{q}.json')), encoding='utf-8'))
    name = raw['config']['series'][0]['name']
    if 'ME - Hipotecario' not in name:
        raise SystemExit(f'BCRP: вместо долларовой ипотечной ставки пришло «{name}»')
    vals = [float(p['values'][0]) for p in raw['periods'] if p['values'][0] not in ('n.d.', '')]
    if len(vals) != 3:
        raise SystemExit(f'BCRP: за {period} нашлось {len(vals)} месяцев ставки из 3')
    return round(sum(vals) / 3, 4), name


# ------------------------------------------------------------ контуры

def fold(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').strip()


# Имена, которые источник цен и источник контуров пишут по-разному. «Paterl» —
# так квартал Paternal записан в самом файле цен, это не ошибка извлечения.
GEO_ALIAS = {
    'PE': {'Magdalena': 'Magdalena del Mar', 'Surco': 'Santiago de Surco'},
    'AR': {'Boca': 'La Boca', 'Paterl': 'Paternal'},
}


def outer_rings(geom):
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    return [p[0] for p in polys]


def clip(ring, box):
    """Сазерленд — Ходжмен по прямоугольнику: соседи за рамкой врезки не нужны."""
    x0, y0, x1, y1 = box
    edges = [(lambda p: p[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0]))),
             (lambda p: p[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0]))),
             (lambda p: p[1] >= y0, lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / (b[1] - a[1]), y0)),
             (lambda p: p[1] <= y1, lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / (b[1] - a[1]), y1))]
    pts = [tuple(p[:2]) for p in ring]
    for inside, cut in edges:
        if not pts:
            break
        out, prev = [], pts[-1]
        for cur in pts:
            if inside(cur):
                if not inside(prev):
                    out.append(cut(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cut(prev, cur))
            prev = cur
        pts = out
    return pts


def simplify(pts, tol_m, lat):
    """Дуглас — Пекер в метрах: градус долготы у экватора и в Буэнос-Айресе разный."""
    kx, ky = 111320 * math.cos(math.radians(lat)), 110540
    xy = [(p[0] * kx, p[1] * ky) for p in pts]

    def dp(a, b):
        (ax, ay), (bx, by) = xy[a], xy[b]
        dx, dy = bx - ax, by - ay
        ln = math.hypot(dx, dy) or 1e-9
        best, idx = 0.0, None
        for i in range(a + 1, b):
            d = abs(dy * xy[i][0] - dx * xy[i][1] + bx * ay - by * ax) / ln
            if d > best:
                best, idx = d, i
        if idx is None or best <= tol_m:
            return [a]
        return dp(a, idx) + dp(idx, b)

    if len(pts) < 4:
        return pts
    # У замкнутого кольца первая точка совпадает с последней, отрезок между
    # ними нулевой, и алгоритм выбросил бы всё. Кольцо режется надвое в точке,
    # самой далёкой от начала.
    far = max(range(len(xy)), key=lambda i: math.hypot(xy[i][0] - xy[0][0], xy[i][1] - xy[0][1]))
    keep = dp(0, far) + dp(far, len(pts) - 1) + [len(pts) - 1]
    return [pts[i] for i in keep]


def bbox(rings):
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    return min(xs), min(ys), max(xs), max(ys)


def city_geo(feats, name_of, keys, cc, tol_m, pad):
    """Районы города: ключ — имя района в CSV цен, None — района в слое нет.

    Окно — рамка районов с ценами плюс поле pad с каждой стороны: соседи без
    данных рисуются фоном, иначе врезка висела бы в пустоте.
    """
    names = GEO_ALIAS.get(cc, {})
    alias = {fold(k): fold(v) for k, v in names.items()}
    want = {alias.get(fold(k), fold(k)): k for k in keys}
    rows, matched = [], set()
    for f in feats:
        nm = name_of(f)
        key = want.get(fold(nm))
        if key:
            matched.add(key)
        rows.append((nm, key, outer_rings(f['geometry'])))
    for k in keys:
        if k not in matched:
            raise SystemExit(f'{cc}: район «{k}» из цен не нашёл контура')
    for k, v in names.items():
        note('контуры', cc, f'«{k}» в ценах = «{v}» в контурах')
    x0, y0, x1, y1 = bbox([r for _, key, rs in rows if key for r in rs])
    px, py = (x1 - x0) * pad, (y1 - y0) * pad
    win = (x0 - px, y0 - py, x1 + px, y1 + py)
    lat = (y0 + y1) / 2
    out = []
    for nm, key, rs in rows:
        rings = []
        for r in rs:
            c = clip(r, win)
            if len(c) < 3:
                continue
            s = simplify(c + [c[0]], tol_m, lat)
            if len(s) >= 4:
                rings.append([[round(p[0], 5), round(p[1], 5)] for p in s])
        if rings:
            # «as» — как район пишет файл цен, даже когда цены у него нет: по
            # этому имени страница находит причину пропуска в latam-gaps.csv.
            spelled = key or {fold(v): k for k, v in names.items()}.get(fold(nm), nm)
            out.append({'name': nm, 'key': key, 'as': spelled, 'rings': rings})
    out.sort(key=lambda d: d['name'])
    return out


def boundaries(src, pe_rows, ar_rows):
    pkg = json.load(open(fetch(HDX_PER, os.path.join(src, 'hdx-cod-ab-per.json')), encoding='utf-8'))['result']
    if pkg.get('license_id') != 'cc-by-igo':
        raise SystemExit(f'HDX: лицензия набора сменилась на {pkg.get("license_id")} — перечитать до сборки')
    res = next(r for r in pkg['resources'] if r['format'] == 'GeoJSON')
    zp = fetch(res['url'], os.path.join(src, 'per_admin_boundaries.geojson.zip'))
    with zipfile.ZipFile(zp) as z:
        per = json.load(z.open('per_admin3.geojson'))
    # Провинции Лима и Кальяо: это один город, и Кальяо ограничивает
    # Сан-Мигель и Магдалену с запада.
    lima_feats = [f for f in per['features']
                  if (f['properties']['adm1_name'], f['properties']['adm2_name']) in {('Lima', 'Lima'), ('Callao', 'Callao')}]
    lima = city_geo(lima_feats, lambda f: f['properties']['adm3_name'],
                    [r['district'] for r in pe_rows], 'PE', tol_m=25, pad=0.12)
    note('контуры', 'PE', 'geoBoundaries не подошёл: у Перу там только провинции (ADM2), районов (ADM3) нет; '
         'взяты районы IGN из набора HDX cod-ab-per, CC BY 3.0 IGO, упрощены')
    n_lima = sum(1 for d in lima if not d['key'])
    note('контуры', 'PE', f'{n_lima} соседних районов без цены рисуются фоном: BCRP публикует только 12 районов')

    ba = json.load(open(fetch(AR_BARRIOS, os.path.join(src, 'caba-barrios.geojson')), encoding='utf-8'))
    ar = city_geo(ba['features'], lambda f: f['properties']['nombre'],
                  [r['district'] for r in ar_rows], 'AR', tol_m=15, pad=0.02)
    note('контуры', 'AR', 'barrios с портала Buenos Aires Data, CC-BY-2.5-AR (поле «Licencia» набора), упрощены')
    meta = {
        'PE': {'source': 'Instituto Geográfico Nacional (IGN), via OCHA / HDX «Peru - Subnational Administrative Boundaries»',
               'url': HDX_PER_PAGE, 'licence': 'CC BY 3.0 IGO',
               'licence_url': 'https://creativecommons.org/licenses/by/3.0/igo/legalcode',
               'modified': 'контуры упрощены и обрезаны рамкой врезки'},
        'AR': {'source': 'Buenos Aires Data, «Barrios»', 'url': AR_BARRIOS_PAGE, 'licence': 'CC-BY-2.5-AR',
               'licence_url': 'https://creativecommons.org/licenses/by/2.5/ar/',
               'modified': 'контуры упрощены'},
    }
    return {'PE': lima, 'AR': ar}, meta


# ---------------------------------------------------------------- сборка

def write(path, rows, cols):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '_latam_src')
    os.makedirs(src, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)

    pe, pe_period = peru(src)
    pe_rate, pe_rate_name = peru_rate(src, pe_period)
    ar, ar_period = argentina(src)
    oe, oe_tag = oecd(src)
    geo, geo_meta = boundaries(src, pe, ar)
    note('ставка', 'AR', 'своей ставки ипотеки у слоя нет; покупка считается только по ставке, введённой читателем')

    # Страны, проверенные и не вошедшие: причина записывается всегда.
    for c, why in [
        ('BR', 'данные открыты и бесплатны, но текст лицензии IBGE подтвердить не удалось'),
        ('CL', 'цены за м² в открытом доступе нет: кадастр SII массово не выгружается'),
        ('UY', 'лицензия лучшая в регионе, но цен жилья и аренды нет ни на одном портале'),
        ('CO', 'цена за м² по кварталам Боготы есть, но поле лицензии набора пустое'),
        ('MX', 'условия сайта gob.mx ограничивают личным некоммерческим использованием, '
               'хотя наборы помечены CC-BY-4.0 — противоречие не разрешено'),
    ]:
        note('регион', c, why)

    n1 = write(OUT_PE, pe, ['city', 'country', 'district', 'period', 'usd_m2',
                            'price_to_rent_years', 'rent_usd_m2_month'])
    n2 = write(OUT_AR, ar, ['city', 'country', 'district', 'comuna', 'period',
                            'usd_m2', *AR_EXTRA])
    n3 = write(OUT_OECD, oe, ['country', 'year', 'share', 'income_basis', 'series'])
    write(GAPS, gaps, ['scope', 'item', 'reason'])

    meta = {
        'built': __import__('datetime').date.today().isoformat(),
        'layers': {
            'PE': {'rows': n1, 'period': pe_period, 'city': 'Lima',
                   'source': 'Banco Central de Reserva del Perú, series «Mercado inmobiliario»',
                   'url': 'https://estadisticas.bcrp.gob.pe/estadisticas/series/',
                   'licence': 'Puede reproducirse total o parcialmente, sin autorización '
                              'expresa, siempre y cuando se cite la fuente',
                   'licence_url': 'https://www.bcrp.gob.pe/condiciones-de-uso.html',
                   'kind': 'цена сделок',
                   # TEA — эффективная годовая: месячная ставка из неё
                   # (1 + TEA)^(1/12) − 1, а не TEA / 12.
                   'rate_tea': pe_rate, 'rate_series': BCRP_RATE, 'rate_name': pe_rate_name},
            'AR': {'rows': n2, 'period': ar_period, 'city': 'Buenos Aires',
                   'source': 'Buenos Aires Data, Instituto de Vivienda',
                   'url': 'https://data.buenosaires.gob.ar/dataset/mercado-inmobiliario',
                   'licence': 'CC-BY-2.5-AR',
                   'licence_url': 'https://creativecommons.org/licenses/by/2.5/ar/',
                   'kind': 'цена предложения',
                   'stratum': '3 ambientes, Usado (главная колонка usd_m2)'},
            'OECD': {'rows': n3, 'indicator': oe_tag,
                     'source': 'OECD Affordable Housing Database, HC1.2',
                     'url': 'https://www.oecd.org/en/data/datasets/oecd-affordable-housing-database.html',
                     'licence': 'CC BY 4.0',
                     'measure': 'медиана доли ипотеки (тело и проценты) или аренды в доходе',
                     'caveat': 'Чили, Колумбия, Мексика — доход до налогов, Коста-Рика — располагаемый',
                     'licence_url': 'https://creativecommons.org/licenses/by/4.0/',
                     'countries': OECD_LATAM},
        },
        'geo': geo_meta,
        'gaps': len(gaps),
    }
    with open(META, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    with open(OUT_GEO, 'w', encoding='utf-8') as f:
        json.dump(geo, f, ensure_ascii=False, separators=(',', ':'))

    print(f'Перу, районы Лимы:        {n1:3}  ({pe_period})')
    print(f'Аргентина, кварталы CABA: {n2:3}  ({ar_period})')
    print(f'OECD, страны региона:     {n3:3}')
    print(f'ставка Лимы, TEA:       {pe_rate:6.3f}  ({BCRP_RATE})')
    for cc in geo:
        print(f'контуры {cc}: {len(geo[cc])} районов, {sum(1 for d in geo[cc] if d["key"])} с ценой')
    print(f'latam-geo.json: {os.path.getsize(OUT_GEO)} байт')
    print(f'пропусков с причиной:     {len(gaps):3}  → {os.path.relpath(GAPS, ROOT)}')


if __name__ == '__main__':
    main()
