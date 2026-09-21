(function () {
  "use strict";
  /* Всё, что видно на странице, считается здесь из одной вшитой таблицы: DATA —
     страны, регионы NUTS 3 и 8 489 муниципалитетов (см. src/data.py), GEO —
     контуры регионов в проекции Ламберта (см. src/geo.py). Ни одного запроса в
     сеть страница не делает и открывается локальным файлом. */
  var DATA = {{data}};
  var GEO = {{geo}};

  // ---- расшифровка компактных массивов
  var C = DATA.countries, CI = {};
  C.forEach(function (c, i) { CI[c.c] = i; });
  var N3 = DATA.regions.map(function (a, i) {
    return { kind: "region", idx: i, id: a[0], name: a[1], cc: a[2], pop: a[3], inc: a[4], sp: a[5], rp: a[6],
             sa: a[7], ra: a[8], covS: a[9], covR: a[10], grp: a[11] };
  });
  var N3I = {};
  N3.forEach(function (n, i) { N3I[n.id] = i; });
  var L = DATA.places.map(function (a, i) {
    return { kind: "place", idx: i, id: a[0], name: a[1], cc: C[a[2]].c, reg: a[3], pop: a[4], inc: a[5], sp: a[6],
             rp: a[7] / 10, lat: a[8] / 100, lon: a[9] / 100, deg: a[10], coast: a[11],
             alias: (DATA.aliases || {})[a[0]] || "" };
  });
  var LI = {};
  L.forEach(function (l, i) { LI[l.id] = i; });
  // Аренда в США задана не за метр, а за жильё с таким-то числом спален
  // (см. extract_us.py). «Доля дохода на аренду» считается там от двухкомнатной
  // квартиры, а в Европе — от N м²: это две разные величины, и подписаны они по
  // кадру, а не общей строкой на всю карту.
  var EX = {};
  (DATA.extra || []).forEach(function (a) { EX[a[0]] = { val: a[1], rent: a[2], moe: a[3] }; });
  // Ниже этого числа сделок за год медиана округа собрана из единиц, и верить ей
  // нельзя. Строки не выброшены — карточка места называет число сделок вслух.
  var MOEHI = DATA.moe || 20;
  C.forEach(function (c) { c.kind = "cc"; c.id = "c:" + c.c; c.name = c.n; c.cc = c.c; });

  var DEG = { 1: "city", 2: "town or suburb", 3: "rural", 0: "" };
  var CLASSES = DATA.classes;                       // [50, 75, 100, 150]
  var CLASS_LABEL = ["under 50 m²", "50–75 m²", "76–100 m²", "101–150 m²", "over 150 m²"];
  var DIFF_BREAKS = [-20, -5, 5, 20];
  var DIFF_LABEL = ["buying gives 20 m² more", "buying gives 5–20 m² more", "within 5 m²", "renting gives 5–20 m² more", "renting gives 20 m² more"];
  // Метры считаются от дохода: чем больше, тем лучше. Годы дохода и доля на аренду
  // читаются наоборот, поэтому у них своё направление шкалы — иначе красный и
  // зелёный поменялись бы смыслом между режимами одной и той же карты.
  var YEARS_BREAKS = [3, 5, 8, 12];
  var SHARE_BREAKS = [20, 30, 40, 50];
  var MODES = {
    buy:   { inv: false, m2: true, title: "m² to buy" },
    rent:  { inv: false, m2: true, title: "m² to rent" },
    diff:  { inv: false, m2: true, title: "rent minus buy, m²" },
    years: { inv: true,  breaks: YEARS_BREAKS, title: "years of income" },
    share: { inv: true,  breaks: SHARE_BREAKS, title: "rent, % of income" }
  };
  function mapN() { return S.want || 70; }
  function modeText() {
    if (S.mode === "buy") return "square metres to buy";
    if (S.mode === "rent") return "square metres to rent";
    if (S.mode === "diff") return "square metres to rent minus square metres to buy";
    if (S.mode === "years") return "years of income for " + (m2Here() ? mapN() + " m²" : fr().home);
    return "rent of " + (m2Here() ? mapN() + " m²" : fr().rental) + " as a share of income";
  }
  function modeLabels() {
    if (S.mode === "years") return ["under 3 years", "3–5", "5–8", "8–12", "over 12"];
    if (S.mode === "share") return ["under 20 % of income", "20–30 %", "30–40 %", "40–50 %", "over 50 %"];
    return S.mode === "diff" ? DIFF_LABEL : CLASS_LABEL;
  }
  // Кадры карты. Европа и США — два слоя одного исследования, но не одна шкала:
  // своя проекция, своя валюта, свои слова для единицы и, главное, свой источник
  // дохода. Поэтому всё, что считается по местным деньгам, живёт внутри кадра, а
  // сравнивать слои честно только на доходе читателя (см. «Where the numbers
  // come from»).
  var FRAMES = DATA.frames;
  function fr() { return FRAMES[S.frame] || FRAMES[GEO.order[0]]; }
  // Есть ли у кадра цена за метр. У европейского есть, у американского нет:
  // площадь жилья в США не собирает ни одно государственное обследование по
  // округам, а частные данные MLS перепубликовать нельзя. Поэтому «сколько
  // метров» там не «нет данных по этому округу», а «такой величины не
  // существует», и метрики считаются на медианное жильё округа.
  function hasM2(key) { return !!(FRAMES[key || S.frame] || {}).m2; }
  function m2Here() { return hasM2(S.frame); }
  function basketOf(pl, what) {
    var f = FRAMES[frameOf(pl)] || {};
    return hasM2(frameOf(pl)) ? mapN() + " m²" : (what === "rent" ? f.rental : f.home);
  }
  function regionsList() { return DATA.groups[S.frame] || []; }
  function frameOf(pl) { var c = C[CI[pl.cc]]; return (c && c.frame) || GEO.order[0]; }
  function inFrame(pl) { return frameOf(pl) === S.frame; }
  function allRegOn() {
    var o = {};
    Object.keys(DATA.groups).forEach(function (f) {
      DATA.groups[f].forEach(function (r) { o[r[0]] = 1; });
    });
    return o;
  }
  // Курсы ЕЦБ на 11 сентября 2026: единиц валюты за евро. Вшиты, чтобы ссылка
  // означала ту же сумму и через месяц.
  var FX = { EUR: 1, USD: 1.1592, GBP: 0.85815, CHF: 0.9451, PLN: 4.3250, CZK: 24.264, HUF: 364.45,
             SEK: 11.2373, NOK: 10.7805, DKK: 7.4748, RON: 5.2547, ISK: 139.60, TRY: 56.3329 };
  var FX_DATE = "11 Sep 2026";

  // ---- состояние: всё живёт в адресной строке
  // Исследование берёт РОВНО ТРЕТЬ дохода, а не 33 %. Разница кажется мелкой, но
  // она ровно 1 %, и с 33 % страница расходилась с опубликованными sa_m2 и ra_m2
  // на этот самый 1 % — при этом обещая точное совпадение. С третью расхождение
  // 7.7e-10 на 78 758 строках продажи и 4.9e-9 на 47 154 строках аренды.
  var THIRD = 100 / 3;
  var S = { inc: 0, cur: "EUR", share: THIRD, term: 30, rate: null, dep: 0, adults: 1, kids: 0,
            mode: "buy", basis: "local", want: 0, cmp: [], frame: GEO.order[0], reg: allRegOn(),
            sort: "buy", dir: "desc", mf: null, mt: null, mi: 0, mc: null, rank: "countries", sel: null, coast: 0, sav: 500 };
  var DEFAULTS = JSON.parse(JSON.stringify(S));

  function readURL() {
    var p = new URLSearchParams(location.search);
    function num(k, lo, hi, def) {
      if (!p.has(k) || p.get(k) === "") return def;
      var v = parseFloat(p.get(k)); return isNaN(v) ? def : Math.max(lo, Math.min(hi, v));
    }
    S.inc = num("i", 0, 1e7, 0);
    S.cur = FX[p.get("c")] ? p.get("c") : "EUR";
    S.share = num("s", 20, 45, THIRD);
    S.term = [10, 15, 20, 25, 30].indexOf(num("t", 10, 30, 30)) >= 0 ? num("t", 10, 30, 30) : 30;
    S.rate = p.has("r") && p.get("r") !== "" ? num("r", 0, 25, null) : null;
    S.dep = num("d", 0, 40, 0);
    S.adults = num("a", 1, 6, 1); S.kids = num("k", 0, 8, 0);
    S.mode = MODES[p.get("m")] ? p.get("m") : "buy";
    S.basis = p.get("b") === "mine" && S.inc > 0 ? "mine" : "local";
    S.want = num("q", 0, 150, 0);
    S.cmp = (p.get("x") || "").split(",").filter(function (id) { return placeById(id); }).slice(0, 4);
    S.frame = GEO.order.indexOf(p.get("f")) >= 0 ? p.get("f") : GEO.order[0];
    var g = p.get("g");
    if (g && /^[01]{4}$/.test(g)) regionsList().forEach(function (r, i) { S.reg[r[0]] = g.charAt(i) === "1" ? 1 : 0; });
    var o = p.get("o") || "";
    if (/^-?(buy|rent|price|rentp|years|share|val|rnt|inc|pop|name|rate)$/.test(o)) { S.sort = o.replace("-", ""); S.dir = o.charAt(0) === "-" ? "asc" : "desc"; }
    S.rank = p.get("v") === "cities" ? "cities" : "countries";
    S.sel = placeById(p.get("p")) ? p.get("p") : null;
    S.coast = p.get("z") === "1" ? 1 : 0;
    S.sav = num("sv", 0, 1e6, 500);
    S.mf = placeById(p.get("mf")) ? p.get("mf") : null;
    S.mt = placeById(p.get("mt")) ? p.get("mt") : null;
    S.mi = num("mi", 0, 1e7, 0);
    S.mc = FX[p.get("mc")] ? p.get("mc") : null;
    // Ссылка может нести место одного слоя и кадр другого — например «?p=us48453»
    // без «f». Кадр идёт за выбранным местом: показывать метку там, где её на
    // карте нет, хуже, чем переключить карту.
    var sel = placeById(S.sel);
    if (sel && frameOf(sel) !== S.frame) S.frame = frameOf(sel);
  }
  function shareURL() {
    var q = [];
    function put(k, v, def) { if (v !== def && v !== null && v !== "" && v !== undefined) q.push(k + "=" + encodeURIComponent(v)); }
    put("i", S.inc, 0); put("c", S.cur, "EUR"); put("s", S.share, THIRD); put("t", S.term, 30);
    put("r", S.rate, null); put("d", S.dep, 0); put("a", S.adults, 1); put("k", S.kids, 0);
    put("m", S.mode, "buy"); put("b", S.basis, "local"); put("q", S.want, 0);
    put("x", S.cmp.join(","), ""); put("f", S.frame, GEO.order[0]);
    put("g", regionsList().map(function (r) { return S.reg[r[0]]; }).join(""), "1111");
    put("o", (S.dir === "asc" ? "-" : "") + S.sort, "buy"); put("v", S.rank, "countries");
    put("p", S.sel, null); put("z", S.coast, 0); put("sv", S.sav, 500);
    put("mf", S.mf, null); put("mt", S.mt, null); put("mi", S.mi, 0); put("mc", S.mc, null);
    return location.origin + location.pathname + (q.length ? "?" + q.join("&") : "");
  }
  var urlTimer = null;
  function syncURL() {
    clearTimeout(urlTimer);
    urlTimer = setTimeout(function () {
      try { history.replaceState(null, "", shareURL().replace(location.origin, "") ); } catch (e) {}
    }, 250);
  }

  // ---- арифметика: та же, что у ESPON; с настройками по умолчанию сходится с sa_m2 и ra_m2
  function placeById(id) {
    if (!id) return null;
    if (id.slice(0, 2) === "c:") { var c = C[CI[id.slice(2)]]; return c && (c.sp || c.rp) ? c : null; }
    if (id.slice(0, 2) === "n:") { var n = N3[N3I[id.slice(2)]]; return n || null; }
    var l = L[LI[id]]; return l || null;
  }
  function pid(pl) { return pl.kind === "place" ? pl.id : pl.kind === "region" ? "n:" + pl.id : "c:" + pl.c; }
  // Две цифры одной строкой для списков внутри карточки. В кадре с метрами это
  // метры на покупку и аренду, в кадре без них — годы дохода и доля на аренду:
  // прочерк на месте метров сообщал бы о дыре в данных, которой нет.
  function summaryOf(pl) {
    if (hasM2(frameOf(pl))) return fmtM2(buyM2(pl)) + " · " + fmtM2(rentM2(pl)) + " m²";
    var y = yearsFor(pl), sv = rentShare(pl);
    return (y === null ? "—" : y.toFixed(1) + " yrs") + " · " + (sv === null ? "—" : Math.round(sv) + " %");
  }
  function annuity(ratePct, years) {
    var i = ratePct / 100 / 12, n = years * 12;
    return i > 0 ? (1 - Math.pow(1 + i, -n)) / i : n;
  }
  function eqFactor() { return 1 + 0.5 * (S.adults - 1) + 0.3 * S.kids; }
  function incEUR() { return S.inc > 0 ? S.inc / FX[S.cur] : 0; }
  // Цены и доходы места записаны в валюте его страны, а доход читателя — в его
  // собственной. Без перевода бюджет в долларовом округе делился бы на долларовую
  // цену, оставаясь при этом в евро.
  function curOf(pl) { var c = C[CI[pl.cc]]; return (c && c.cur) || "EUR"; }
  function symOf(pl) { var u = curOf(pl); return u === "USD" ? "$" : u === "EUR" ? "\u20ac" : u + "\u00a0"; }
  function myIncome(pl) { return incEUR() * (FX[curOf(pl)] || 1); }
  function mine() { return S.basis === "mine" && S.inc > 0; }
  function localMonthly(pl) { return pl.inc / 12; }
  function shareText() { return S.share === THIRD ? "a third" : Math.round(S.share) + " %"; }
  function budget(pl) { return (mine() ? myIncome(pl) : localMonthly(pl)) * S.share / 100; }
  function rateOf(pl) {
    if (S.rate !== null) return S.rate;
    var c = C[CI[pl.cc]]; return c && c.rate ? c.rate : null;
  }
  function buyM2(pl, opt) {
    opt = opt || {};
    if (!pl.sp || !pl.inc && !mine()) return null;
    var r = opt.rate != null ? opt.rate : rateOf(pl);
    if (r === null) return null;
    var b = (opt.income != null ? opt.income : (mine() ? myIncome(pl) : localMonthly(pl))) * (opt.share || S.share) / 100;
    var loan = b * annuity(r, opt.term || S.term);
    var dep = opt.dep != null ? opt.dep : S.dep;
    return loan / (1 - dep / 100) / pl.sp;
  }
  function rentM2(pl, opt) {
    opt = opt || {};
    if (!pl.rp || !pl.inc && !mine()) return null;
    var b = (opt.income != null ? opt.income : (mine() ? myIncome(pl) : localMonthly(pl))) * (opt.share || S.share) / 100;
    return b / pl.rp;
  }
  // Цифры самой статьи: средний местный доход, треть, 30 лет, национальная ставка, без взноса.
  function studyBuy(pl) { return pl.inc && pl.sp ? buyM2(pl, { income: localMonthly(pl), share: THIRD, term: 30, dep: 0, rate: (C[CI[pl.cc]] || {}).rate || null }) : null; }
  function studyRent(pl) { return pl.inc && pl.rp ? localMonthly(pl) * THIRD / 100 / pl.rp : null; }
  function incomeNeeded(pl, m2) {          // чистый доход в месяц, чтобы купить m2 при текущих условиях
    var r = rateOf(pl); if (!pl.sp || r === null) return null;
    return m2 * priceAt(pl, m2) * (1 - S.dep / 100) / annuity(r, S.term) / (S.share / 100);
  }
  function cls(v) {
    if (v === null || v === undefined || !(v > 0)) return -1;
    for (var i = 0; i < CLASSES.length; i++) if (v <= CLASSES[i]) return i;
    return 4;
  }
  function dcls(v) {
    if (v === null || v === undefined || isNaN(v)) return -1;
    for (var i = 0; i < DIFF_BREAKS.length; i++) if (v <= DIFF_BREAKS[i]) return i;
    return 4;
  }
  // ---- надбавка за размер
  // Цена за метр нелинейна по площади: в Испании метр в квартире до 30 м² стоит
  // на 83 % дороже среднего, в Германии на 13 %. Коэффициенты по странам считает
  // data.py из тех же пяти классов сервиса.
  //
  // Применяется ТОЛЬКО там, где размер назван читателем: «лет дохода», «доля на
  // аренду», «сколько нужно дохода на N м²» и фильтр «хочу N м²». Основные метры
  // на покупку и аренду остаются на общей цене — это арифметика самого
  // исследования, и страница обязана сходиться с ним при настройках по умолчанию.
  var SZ = DATA.size || null;
  function sizeIdx(n) {
    if (!SZ) return -1;
    for (var i = 0; i < SZ.edges.length; i++) if (n <= SZ.edges[i]) return i;
    return SZ.edges.length;
  }
  function sizeFactor(pl, what, n) {
    if (!SZ || !n) return 1;
    var t = SZ[what]; if (!t) return 1;
    var row = t.cc[pl.cc];
    // Общеевропейскую кривую можно достроить европейской стране, у которой мало
    // наблюдений, но не американскому округу: надбавка за размер там не измерена
    // вовсе, и подставить чужую значило бы выдумать число.
    if (!row) { if (frameOf(pl) !== "eu") return 1; row = t.eu; }
    var v = row[sizeIdx(n)];
    return v > 0 ? v : 1;
  }
  function priceAt(pl, n) { return pl.sp ? pl.sp * sizeFactor(pl, "sp", n) : 0; }
  function rentAt(pl, n) { return pl.rp ? pl.rp * sizeFactor(pl, "rp", n) : 0; }

  // Годы дохода и доля на аренду считаются на то же жильё, которое читатель задал
  // ползунком «хочу N м²». Своего «типового жилья» страница не выдумывает: медианной
  // цены квартиры в данных нет, а подставить её размер было бы догадкой.
  function yearsFor(pl) {
    var inc = mine() ? myIncome(pl) * 12 : pl.inc;
    if (!inc) return null;
    if (!hasM2(frameOf(pl))) {
      var x = EX[pid(pl)];
      return x && x.val ? x.val / inc : null;
    }
    if (!pl.sp) return null;
    return priceAt(pl, mapN()) * mapN() / inc;
  }
  function rentShare(pl) {
    var inc = mine() ? myIncome(pl) : localMonthly(pl);
    if (!inc) return null;
    if (!hasM2(frameOf(pl))) {
      var x = EX[pid(pl)];
      return x && x.rent ? x.rent / inc * 100 : null;
    }
    if (!pl.rp) return null;
    return rentAt(pl, mapN()) * mapN() / inc * 100;
  }
  function valueOf(pl) {
    if (S.mode === "buy") return buyM2(pl);
    if (S.mode === "rent") return rentM2(pl);
    if (S.mode === "years") return yearsFor(pl);
    if (S.mode === "share") return rentShare(pl);
    var b = buyM2(pl), r = rentM2(pl);
    return b === null || r === null ? null : r - b;
  }
  // Индекс цвета: уже с учётом направления шкалы режима. Режим передаётся, а не
  // берётся из состояния: карточка показывает годы и долю одновременно, в каком
  // бы режиме ни была карта.
  function clsFor(mode, v) {
    var m = MODES[mode];
    if (!m.breaks) return cls(v);
    if (v === null || v === undefined || !(v > 0)) return -1;
    var i = 0;
    while (i < m.breaks.length && v > m.breaks[i]) i++;
    return m.inv ? 4 - i : i;
  }
  function colourOf(v) { return clsFor(S.mode, v); }
  function bigCls(c) { return c < 0 ? "nd" : "c" + c; }
  function fmtMetric(v) {
    if (v === null || v === undefined || isNaN(v)) return "—";
    if (S.mode === "years") return v.toFixed(1) + " years";
    if (S.mode === "share") return Math.round(v) + " %";
    return fmtM2(v) + " m²";
  }
  function reaches(pl) {                      // проходит ли место фильтр «хочу N м²»
    if (!S.want) return true;
    if (S.mode === "years" || S.mode === "share") return true;
    // Проверяется по цене класса, в который попадает сам запрошенный размер:
    // «хочу 25 м²» в Испании стоит за метр вдвое дороже среднего.
    var b = buyAtSize(pl, S.want), r = rentAtSize(pl, S.want);
    if (S.mode === "rent") return r >= S.want;
    if (S.mode === "buy") return b >= S.want;
    return b >= S.want || r >= S.want;
  }
  // Сколько метров даёт бюджет, если метр стоит по классу запрошенного размера.
  function buyAtSize(pl, n) {
    var p = priceAt(pl, n); if (!p) return 0;
    var r = rateOf(pl); if (r === null) return 0;
    var loan = budget(pl) * annuity(r, S.term);
    return loan / (1 - S.dep / 100) / p;
  }
  function rentAtSize(pl, n) {
    var p = rentAt(pl, n);
    return p ? budget(pl) / p : 0;
  }
  // Группа фильтра живёт на регионе, а не на стране: в Европе все регионы страны
  // в одной группе, а США — одна страна на четыре переписных региона.
  var GRP_CC = {};
  N3.forEach(function (n) { (GRP_CC[n.cc] || (GRP_CC[n.cc] = {}))[n.grp] = 1; });
  function passReg(pl) {
    if (pl.kind === "region") return !!S.reg[pl.grp];
    if (pl.kind === "place") { var n = N3[pl.reg]; return n ? !!S.reg[n.grp] : true; }
    var g = GRP_CC[pl.cc] || {};
    for (var k in g) if (S.reg[k]) return true;
    return false;
  }
  function ccName(cc) { var c = C[CI[cc]]; return c ? c.n : cc; }

  // ---- форматирование
  function fmtInt(v) { return v === null || v === undefined ? "—" : Math.round(v).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ","); }
  function fmtM2(v) { return v === null || v === undefined || isNaN(v) ? "—" : (v < 10 ? v.toFixed(1) : Math.round(v).toString()); }
  function fmtEur(v) { return v === null || v === undefined ? "—" : "€" + fmtInt(v); }
  // Деньги места — в валюте места. Карточка и подсказка показывают местные цены и
  // местный доход, и подписывать их евро означало бы врать на весь американский
  // слой: $185 700 в Сан-Франциско — это не 185 700 евро.
  function fmtLoc(pl, v, dec) {
    if (v === null || v === undefined) return "—";
    return symOf(pl) + (dec ? v.toFixed(dec) : fmtInt(v));
  }
  function fmtRate(v) { return v === null || v === undefined ? "—" : v.toFixed(2) + " %"; }
  function fmtSigned(v) { return v === null || v === undefined ? "—" : (v > 0 ? "+" : "") + fmtM2(v); }
  function esc(v) { return String(v).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;"); }
  // Диакритика снимается разложением, но перечёркнутые и лигатурные буквы им не
  // разбираются: "Wrocław" осталось бы с «ł», и запрос "wroclaw" его не находил.
  var LETTERS = { "ł": "l", "ø": "o", "đ": "d", "ð": "d", "þ": "th", "ß": "ss", "æ": "ae", "œ": "oe", "ı": "i" };
  function fold(v) {
    v = String(v).toLowerCase();
    if (v.normalize) v = v.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    return v.replace(/[łøđðþßæœı]/g, function (c) { return LETTERS[c]; });
  }
  function el(tag, attrs, html) {
    var n = document.createElement(tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (html !== undefined) n.innerHTML = html;
    return n;
  }
  function svgel(name, attrs) {
    var n = document.createElementNS("http://www.w3.org/2000/svg", name);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }

  // ---- проекция: та же, что в geo.py, но кадров теперь несколько, и у каждого
  // свой центр. Одна азимутальная проекция с центром в Европе растянула бы
  // Северную Америку до неузнаваемости, поэтому переменные ниже переставляются
  // при смене кадра, а project() читает их каждый раз.
  var GF = null, BOX, SC, LAT0, LON0;
  function setGeoFrame(key) {
    GF = GEO.frames[key] || GEO.frames[GEO.order[0]];
    BOX = GF.box; SC = GF.w / (BOX[1] - BOX[0]);
    LAT0 = GF.lat0 * Math.PI / 180; LON0 = GF.lon0 * Math.PI / 180;
  }
  setGeoFrame(GEO.order[0]);
  function project(lat, lon) {
    var p = lat * Math.PI / 180, l = lon * Math.PI / 180;
    var k = Math.sqrt(2 / (1 + Math.sin(LAT0) * Math.sin(p) + Math.cos(LAT0) * Math.cos(p) * Math.cos(l - LON0)));
    var x = k * Math.cos(p) * Math.sin(l - LON0);
    var y = k * (Math.cos(LAT0) * Math.sin(p) - Math.sin(LAT0) * Math.cos(p) * Math.cos(l - LON0));
    return [(x - BOX[0]) * SC, (BOX[3] - y) * SC];
  }

  // ======================================================================
  // калькулятор
  // ======================================================================
  var $ = function (id) { return document.getElementById(id); };
  var incEl = $("inc"), curEl = $("cur"), shareEl = $("share"), rateEl = $("rate"), depEl = $("dep"), wantEl = $("want");
  Object.keys(FX).forEach(function (k) { curEl.appendChild(el("option", { value: k }, k)); });

  var PRESETS = [
    { n: "The study's own view", d: "average local income, 30 years, no deposit", s: {} },
    { n: "Junior developer", d: "2,000 € net, alone, 30 years", s: { inc: 2000, adults: 1, kids: 0, basis: "mine", term: 30 } },
    { n: "Couple with a child", d: "4,500 € net, wants 75 m²", s: { inc: 4500, adults: 2, kids: 1, basis: "mine", want: 75 } },
    { n: "Remote worker, coast", d: "3,000 € net, cities on the coast", s: { inc: 3000, adults: 1, basis: "mine", coast: 1, rank: "cities", sort: "buy" } },
    { n: "Buying with savings", d: "2,400 € net, two adults, 40 % deposit, 15 years", s: { inc: 2400, adults: 2, basis: "mine", dep: 40, term: 15 } },
    { n: "Student, renting", d: "900 € net, rent map", s: { inc: 900, adults: 1, basis: "mine", mode: "rent" } }
  ];
  var presetsBox = $("presets");
  PRESETS.forEach(function (p, i) {
    var b = el("button", { type: "button", "class": "preset", "data-i": i, "aria-pressed": "false" },
               esc(p.n) + "<small>" + esc(p.d) + "</small>");
    b.addEventListener("click", function () {
      var keep = { cmp: S.cmp, sel: S.sel, reg: S.reg };
      var fresh = JSON.parse(JSON.stringify(DEFAULTS));
      for (var k in fresh) S[k] = fresh[k];
      for (var k2 in p.s) S[k2] = p.s[k2];
      S.cmp = keep.cmp; S.sel = keep.sel; S.reg = keep.reg;
      syncControls(); update(); syncURL();
    });
    presetsBox.appendChild(b);
  });
  function presetActive() {
    for (var i = 0; i < PRESETS.length; i++) {
      var p = PRESETS[i], ok = true;
      ["inc", "cur", "share", "term", "rate", "dep", "adults", "kids", "mode", "basis", "want", "coast"].forEach(function (k) {
        var want = k in p.s ? p.s[k] : DEFAULTS[k];
        if (String(S[k]) !== String(want)) ok = false;
      });
      if (ok) return i;
    }
    return -1;
  }

  function syncControls() {
    incEl.value = S.inc || "";
    curEl.value = S.cur;
    shareEl.value = Math.round(S.share); $("share-o").textContent = shareText();
    rateEl.value = S.rate === null ? "" : S.rate; $("rate-x").hidden = S.rate === null;
    depEl.value = S.dep; $("dep-o").textContent = S.dep + " %";
    $("adults-o").textContent = S.adults; $("kids-o").textContent = S.kids;
    $("hhhint").textContent = "Equivalence factor " + eqFactor().toFixed(1) + " (OECD-modified scale: first adult 1, each further adult 0.5, each child 0.3). Used only for the line comparing your income with the local average \u2014 which is per adult-equivalent in Europe and per household in the United States.";
    wantEl.value = S.want;
    $("want-o").textContent = !m2Here() ? "no floor area in US data" : S.want ? S.want + " m²" : "any size";
    normMode();
    segSet("frame", S.frame); segSet("term", S.term); segSet("mapmode", S.mode);
    // Кнопки метров в американском кадре не «временно пустые», а неприменимые:
    // площади жилья по округам нет ни в одном открытом источнике, и карта из
    // прочерков читалась бы как дыра в данных, а не как отсутствие величины.
    Array.prototype.forEach.call(document.querySelectorAll("#mapmode button"), function (b) {
      var m = MODES[b.getAttribute("data-v")];
      b.disabled = !!(m && m.m2) && !m2Here();
      b.title = b.disabled ? "No floor area is published for US " + fr().units + " — see \u201cWhere the numbers come from\u201d" : "";
    });
    // Фильтр «хочу N м²» там же и по той же причине.
    wantEl.disabled = !m2Here();
    // Подсказка при наведении объясняет только тем, у кого есть мышь. Причина
    // обязана быть видна и на телефоне, поэтому она ещё и строкой под кнопками.
    $("modehint").hidden = m2Here();
    segSet("basis", S.basis); segSet("rankwhat", S.rank);
    var mineBtn = document.querySelector('#basis [data-v="mine"]');
    mineBtn.disabled = !(S.inc > 0);
    mineBtn.title = S.inc > 0 ? "" : "Enter your income above";
    $("inchint").textContent = S.cur === "EUR" ? "After tax, all earners together. Leave empty to see every place on its own average income."
      : "After tax, all earners together. " + fmtInt(S.inc) + " " + S.cur + " = €" + fmtInt(incEUR()) + " at the ECB reference rate of " + FX_DATE + ".";
    var act = presetActive();
    Array.prototype.forEach.call(presetsBox.children, function (b, i) { b.setAttribute("aria-pressed", String(i === act)); });
    Array.prototype.forEach.call(document.querySelectorAll("#regs .reg"), function (b) { b.setAttribute("aria-pressed", String(!!S.reg[b.getAttribute("data-r")])); });
    var cb = $("coastbtn"); if (cb) cb.setAttribute("aria-pressed", String(!!S.coast));
    setupLine();
  }
  // Режим, требующий метров, в кадре без метров невозможен. Нормализация живёт
  // в одном месте, потому что кадр меняют трое: кнопка, ссылка и выбор места из
  // поиска, — и каждый из них иначе оставил бы карту в режиме без данных.
  function normMode() {
    if (!m2Here() && MODES[S.mode] && MODES[S.mode].m2) S.mode = "years";
  }
  function segSet(id, v) {
    Array.prototype.forEach.call(document.querySelectorAll("#" + id + " button"), function (b) {
      b.setAttribute("aria-pressed", String(String(b.getAttribute("data-v")) === String(v)));
    });
  }
  function segBind(id, fn) {
    $(id).addEventListener("click", function (e) {
      var b = e.target.closest("button[data-v]"); if (!b || b.disabled) return;
      fn(b.getAttribute("data-v")); syncControls(); update(); syncURL();
    });
  }
  // Переключатель кадра строится из данных: кадры приходят из geo.py, и список
  // кнопок обязан следовать за ними, а не повторять их в разметке.
  (function () {
    var box = $("frame");
    GEO.order.forEach(function (k) {
      box.appendChild(el("button", { type: "button", "data-v": k, "aria-pressed": String(k === S.frame) }, FRAMES[k].label));
    });
  })();
  segBind("frame", function (v) {
    if (S.frame === v) return;
    S.frame = v;
    // Выбранное место осталось в другом кадре — на этой карте его просто нет.
    if (S.sel && !inFrame(placeById(S.sel) || { cc: "" })) S.sel = null;
    // В кадре с одной страной рейтинг стран — это одна строка. Показывать её
    // вместо трёх тысяч округов бессмысленно, поэтому вид переключается сам.
    if (C.filter(inFrame).length < 2) S.rank = "cities";
    buildRegButtons();
  });
  segBind("term", function (v) { S.term = +v; });
  segBind("mapmode", function (v) { S.mode = v; });
  segBind("basis", function (v) { S.basis = v; });
  segBind("rankwhat", function (v) { S.rank = v; });
  incEl.addEventListener("input", function () {
    S.inc = Math.max(0, parseFloat(incEl.value) || 0);
    if (S.inc > 0 && S.basis === "local" && !incEl._touchedBasis) { S.basis = "mine"; }
    if (!(S.inc > 0)) S.basis = "local";
    syncControls(); update(); syncURL();
  });
  curEl.addEventListener("change", function () { S.cur = curEl.value; syncControls(); update(); syncURL(); });
  shareEl.addEventListener("input", function () { S.share = +shareEl.value; syncControls(); update(); syncURL(); });
  rateEl.addEventListener("input", function () {
    S.rate = rateEl.value === "" ? null : Math.max(0, Math.min(25, parseFloat(rateEl.value) || 0));
    $("rate-x").hidden = S.rate === null; update(); syncURL(); setupLine();
  });
  $("rate-x").addEventListener("click", function () { S.rate = null; syncControls(); update(); syncURL(); });
  depEl.addEventListener("input", function () { S.dep = +depEl.value; syncControls(); update(); syncURL(); });
  wantEl.addEventListener("input", function () { S.want = +wantEl.value; cardN = null; syncControls(); update(); syncURL(); });
  Array.prototype.forEach.call(document.querySelectorAll("[data-hh]"), function (b) {
    b.addEventListener("click", function () {
      var k = b.getAttribute("data-hh"), d = +b.getAttribute("data-d");
      if (k === "adults") S.adults = Math.max(1, Math.min(6, S.adults + d)); else S.kids = Math.max(0, Math.min(8, S.kids + d));
      syncControls(); update(); syncURL();
    });
  });
  function rateNote() {
    if (S.rate !== null) return S.rate.toFixed(2) + " % everywhere";
    return "each country's own rate";
  }
  function setupLine() {
    var t;
    if (mine()) {
      t = "<b>€" + fmtInt(incEUR()) + "</b> net per month" + (S.cur !== "EUR" ? " (" + fmtInt(S.inc) + " " + S.cur + ")" : "") +
          " · <b>" + shareText() + "</b> for housing = <b>€" + fmtInt(incEUR() * S.share / 100) + "</b> a month · <b>" + S.term + "-year</b> mortgage at " + rateNote() +
          " · deposit <b>" + S.dep + " %</b> · household of " + S.adults + (S.adults > 1 ? " adults" : " adult") + (S.kids ? " and " + S.kids + (S.kids > 1 ? " children" : " child") : "") +
          " (factor " + eqFactor().toFixed(1) + ")";
    } else {
      t = "Every place on its <b>own average income</b> · <b>" + shareText() + "</b> for housing · <b>" + S.term + "-year</b> mortgage at " + rateNote() + " · deposit <b>" + S.dep + " %</b>" +
          // «Как в статье» — это про европейский кадр. У американского слоя
          // published map нет, там те же условия просто называются условиями.
          (S.share === THIRD && S.term === 30 && S.rate === null && S.dep === 0
            ? (S.frame === "eu" ? " — the published map exactly" : " — the study's terms, applied here") : "");
    }
    if (S.want) t += " · looking for <b>" + S.want + " m²</b>";
    $("setupline").innerHTML = t;
  }

  // ======================================================================
  // карта
  // ======================================================================
  var mapEl = $("map"), mapg = $("mapg"), regionsG = $("regions"), marksG = $("marks");
  // Контуры теперь страновые: полигонов уровня NUTS 3 в свободной лицензии нет
  // (см. geo.py). Страна красится заливкой, места показываются точками поверх.
  var pathOf = {}, FL = L, frameBuilt = null;

  // Центроид региона — среднее по его местам: собственной геометрии у него больше
  // нет, а «перелететь к региону» и поставить метку всё равно нужно.
  var regXY = {};
  (function () {
    var acc = {};
    L.forEach(function (l) {
      if (l.reg < 0) return;
      var a = acc[l.reg] || (acc[l.reg] = [0, 0, 0]);
      a[0] += l.lat * l.pop; a[1] += l.lon * l.pop; a[2] += l.pop;
    });
    Object.keys(acc).forEach(function (k) {
      var a = acc[k]; if (a[2]) regXY[N3[k].id] = [a[0] / a[2], a[1] / a[2]];
    });
  })();

  // Точки мест. Все 8 489 кружков разом — лишняя работа для браузера на обзорном
  // масштабе, где они всё равно сливаются, поэтому показывается столько, сколько
  // различимо при текущем зуме, начиная с самых населённых (L уже отсортирован).
  var dotsG = svgel("g", { id: "dots" });
  regionsG.parentNode.insertBefore(dotsG, marksG);
  var dotOf = [], dotsShown = 0;

  // Кадр перестраивается целиком: и контуры, и точки посчитаны в его проекции.
  function buildFrame() {
    setGeoFrame(S.frame);
    mapEl.setAttribute("viewBox", "0 0 " + GF.w + " " + GF.h);
    mapEl.setAttribute("aria-label", "Map of " + fr().label + ": countries filled and "
      + fr().units + " marked as dots, coloured by " + modeText());
    while (regionsG.firstChild) regionsG.removeChild(regionsG.firstChild);
    pathOf = {};
    Object.keys(GF.countries).forEach(function (id) {
      var p = svgel("path", { d: GF.countries[id], "data-id": "c:" + id });
      regionsG.appendChild(p); pathOf[id] = p;
    });
    FL = L.filter(inFrame);
    while (dotOf.length) dotsG.removeChild(dotOf.pop());
    dotsShown = 0;
    Z.k = 1; Z.x = 0; Z.y = 0; applyZ();
    frameBuilt = S.frame;
  }
  function dotBudget() { return Math.min(FL.length, Math.round(420 * Z.k * Z.k)); }
  function buildDots() {
    var n = dotBudget();
    if (n === dotsShown) return;
    if (n < dotsShown) {
      while (dotOf.length > n) dotsG.removeChild(dotOf.pop());
    } else {
      for (var i = dotOf.length; i < n; i++) {
        var l = FL[i], xy = project(l.lat, l.lon);
        var c = svgel("circle", { cx: xy[0].toFixed(1), cy: xy[1].toFixed(1), "data-id": l.id });
        dotsG.appendChild(c); dotOf.push(c);
      }
    }
    dotsShown = n;
    sizeDots(); paintDots();
  }
  function sizeDots() {
    // Радиус по населению, но в экранных единицах: при зуме точки не раздуваются.
    for (var i = 0; i < dotOf.length; i++) {
      var l = FL[i], r = Math.max(1.6, Math.min(9, Math.sqrt(l.pop) / 170));
      dotOf[i].setAttribute("r", (r / Z.k).toFixed(2));
    }
  }
  function paintDots() {
    for (var i = 0; i < dotOf.length; i++) {
      var l = FL[i];
      dotOf[i].setAttribute("class", "dot " + klass(l, "nd") + (S.sel === l.id ? " sel" : ""));
    }
  }

  // Один классификатор на страну и на точку: раньше одна и та же логика стояла
  // дважды и уже начинала расходиться.
  function klass(pl, none) {
    // Отсутствие данных определяет сама метрика, а не наличие цены за метр: в
    // американском кадре цены за метр нет ни у кого, и прежняя проверка красила
    // серым всю страну при том, что годы дохода и доля на аренду там посчитаны.
    var v = valueOf(pl), c;
    if (S.mode === "diff") { var d = dcls(v); c = d < 0 ? none : "e" + d; }
    else { var k = colourOf(v); c = k < 0 ? none : "c" + k; }
    if (c !== none && !reaches(pl)) c = "dim";
    return c;
  }
  function paintMap() {
    if (frameBuilt !== S.frame) buildFrame();
    C.forEach(function (cc) {
      var p = pathOf[cc.c]; if (!p) return;
      // Страна чужого слоя в этот кадр попадает заморскими владениями — у
      // Нидерландов есть острова в Карибском море, и они лежат внутри окна
      // американской карты. Красить их европейской метрикой нельзя: это и
      // чужая величина, и чужая корзина. Поэтому такие контуры остаются фоном.
      var c = inFrame(cc) ? klass(cc, "") : "";
      p.setAttribute("class", c + (S.sel === "c:" + cc.c ? " sel" : ""));
    });
    buildDots(); paintDots();
    var lg = $("legend"), pre = S.mode === "diff" ? "e" : "c", inv = MODES[S.mode].inv;
    // Подпись легенды зависит от кадра: в США обе метрики считаются от
    // медианного жилья округа, а не от N м², и делать вид, что это одно и то же,
    // нельзя.
    var sz = (S.mode !== "years" && S.mode !== "share") ? ""
           : " for " + (m2Here() ? mapN() + " m²" : S.mode === "share" ? fr().rental : fr().home);
    var head = MODES[S.mode].title + sz;
    var html = "<b>" + head + "</b>";
    // Номер образца берётся тем же правилом, что и цвет на карте: у перевёрнутых
    // шкал подпись «меньше трёх лет» обязана стоять рядом с зелёным, а не с красным.
    modeLabels().forEach(function (t, i) {
      html += "<span><i class=\"" + pre + (inv ? 4 - i : i) + "\"></i>" + t + "</span>";
    });
    var dimmed = S.want && S.mode !== "years" && S.mode !== "share";
    html += "<span><i class=\"nd\"></i>" + (dimmed ? "no data or under " + S.want + " m²" : "no data") + "</span>";
    lg.innerHTML = html;
  }

  // зум и панорама: transform на группе, точка под курсором остаётся на месте
  var Z = { k: 1, x: 0, y: 0 };
  function applyZ() { mapg.setAttribute("transform", "translate(" + Z.x.toFixed(1) + " " + Z.y.toFixed(1) + ") scale(" + Z.k.toFixed(3) + ")"); buildDots(); sizeDots(); drawMarks(); }
  function svgPoint(cx, cy) {
    var r = mapEl.getBoundingClientRect();
    return [(cx - r.left) / r.width * GF.w, (cy - r.top) / r.height * GF.h];
  }
  function zoomAt(f, sx, sy) {
    var nk = Math.max(1, Math.min(14, Z.k * f)); f = nk / Z.k;
    if (sx === undefined) { sx = GF.w / 2; sy = GF.h / 2; }
    Z.x = sx - (sx - Z.x) * f; Z.y = sy - (sy - Z.y) * f; Z.k = nk;
    if (Z.k === 1) { Z.x = 0; Z.y = 0; }
    applyZ();
  }
  $("zin").addEventListener("click", function () { zoomAt(1.5); });
  $("zout").addEventListener("click", function () { zoomAt(1 / 1.5); });
  $("zreset").addEventListener("click", function () { Z.k = 1; Z.x = 0; Z.y = 0; applyZ(); });
  mapEl.addEventListener("wheel", function (e) {
    if (!e.ctrlKey && !e.metaKey) return;
    e.preventDefault();
    var p = svgPoint(e.clientX, e.clientY);
    zoomAt(e.deltaY < 0 ? 1.2 : 1 / 1.2, p[0], p[1]);
  }, { passive: false });
  var ptrs = {}, dragFrom = null, pinch = null, moved = 0;
  mapEl.addEventListener("pointerdown", function (e) {
    ptrs[e.pointerId] = [e.clientX, e.clientY];
    var ids = Object.keys(ptrs);
    if (ids.length === 1) { dragFrom = [e.clientX, e.clientY, Z.x, Z.y]; moved = 0; mapEl.classList.add("drag"); }
    else if (ids.length === 2) {
      var a = ptrs[ids[0]], b = ptrs[ids[1]];
      pinch = { d: Math.hypot(a[0] - b[0], a[1] - b[1]), k: Z.k, cx: (a[0] + b[0]) / 2, cy: (a[1] + b[1]) / 2, x: Z.x, y: Z.y };
      dragFrom = null;
    }
    mapEl.setPointerCapture(e.pointerId);
  });
  mapEl.addEventListener("pointermove", function (e) {
    if (!ptrs[e.pointerId]) return;
    ptrs[e.pointerId] = [e.clientX, e.clientY];
    var r = mapEl.getBoundingClientRect(), sc = GF.w / r.width;
    if (pinch) {
      var ids = Object.keys(ptrs), a = ptrs[ids[0]], b = ptrs[ids[1]];
      var d = Math.hypot(a[0] - b[0], a[1] - b[1]);
      var nk = Math.max(1, Math.min(14, pinch.k * d / pinch.d));
      var p = svgPoint(pinch.cx, pinch.cy), f = nk / pinch.k;
      Z.k = nk; Z.x = p[0] - (p[0] - pinch.x) * f + ((a[0] + b[0]) / 2 - pinch.cx) * sc;
      Z.y = p[1] - (p[1] - pinch.y) * f + ((a[1] + b[1]) / 2 - pinch.cy) * sc;
      applyZ();
    } else if (dragFrom) {
      var dx = (e.clientX - dragFrom[0]) * sc, dy = (e.clientY - dragFrom[1]) * sc;
      moved = Math.max(moved, Math.abs(dx) + Math.abs(dy));
      if (e.pointerType === "touch" && Z.k === 1) return;      // на телефоне вертикальный свайп — прокрутка страницы
      Z.x = dragFrom[2] + dx; Z.y = dragFrom[3] + dy; applyZ();
    }
  });
  function ptrEnd(e) {
    delete ptrs[e.pointerId];
    if (!Object.keys(ptrs).length) { dragFrom = null; pinch = null; mapEl.classList.remove("drag"); }
    else if (Object.keys(ptrs).length === 1) { pinch = null; var id = Object.keys(ptrs)[0]; dragFrom = [ptrs[id][0], ptrs[id][1], Z.x, Z.y]; }
  }
  mapEl.addEventListener("pointerup", ptrEnd); mapEl.addEventListener("pointercancel", ptrEnd);

  // подсказка и выбор региона
  var tip = $("maptip"), hoverId = null;
  function tipHTML(pl) {
    var b = buyM2(pl), r = rentM2(pl);
    var h = "<b>" + esc(pl.name) + "</b> · " + esc(ccName(pl.cc));
    // Первой строкой — то, чем сейчас раскрашена карта: иначе подсказка отвечает
    // на другой вопрос, чем цвет под курсором.
    if (S.mode === "years" || S.mode === "share") {
      h += "<div class=\"r lead\"><span>" + (S.mode === "years" ? "years of income for " : "rent of ") +
           (m2Here() ? mapN() + " m²" : S.mode === "share" ? fr().rental : fr().home) + "</span>" +
           "<span>" + fmtMetric(valueOf(pl)) + "</span></div>";
    }
    var x = EX[pid(pl)];
    if (hasM2(frameOf(pl))) {
      h += "<div class=\"r\"><span>to buy</span><span>" + fmtM2(b) + " m²</span></div>" +
        "<div class=\"r\"><span>to rent</span><span>" + fmtM2(r) + " m²</span></div>";
      if (pl.sp) h += "<div class=\"r\"><span>price</span><span>" + fmtLoc(pl, pl.sp) + "/m²</span></div>";
      if (pl.rp) h += "<div class=\"r\"><span>rent</span><span>" + fmtLoc(pl, pl.rp, 1) + "/m²·mo</span></div>";
      if (!pl.sp && !pl.rp) h += "<div class=\"r\"><span>no listings data</span></div>";
    } else {
      // Метров здесь нет и быть не может, поэтому строки «to buy» не притворяются
      // пустыми — вместо них то, что в данных действительно есть.
      h += "<div class=\"r\"><span>median home</span><span>" + (x && x.val ? fmtLoc(pl, x.val) : "no data") + "</span></div>" +
        "<div class=\"r\"><span>median rent</span><span>" + (x && x.rent ? fmtLoc(pl, x.rent) + "/mo" : "no data") + "</span></div>" +
        "<div class=\"r\"><span>income</span><span>" + (pl.inc ? fmtLoc(pl, pl.inc / 12) + "/mo" : "no data") + "</span></div>";
    }
    return h;
  }
  function showTipAt(pl, cx, cy) {
    var r = $("mapbox").getBoundingClientRect();
    tip.innerHTML = tipHTML(pl);
    var x = cx - r.left, y = cy - r.top - 12;
    var w = tip.offsetWidth; x = Math.max(w / 2 + 4, Math.min(x, r.width - w / 2 - 4));
    tip.style.left = x + "px"; tip.style.top = y + "px"; tip.style.opacity = "1";
  }
  // Точка места перекрывает страну, поэтому цель ищется сначала среди точек.
  function targetOf(e) {
    var el = e.target.closest("circle[data-id], path[data-id]");
    if (!el) return null;
    var id = el.getAttribute("data-id");
    return id.indexOf("c:") === 0 ? C[CI[id.slice(2)]] : L[LI[id]];
  }
  function onMapMove(e) {
    if (dragFrom && moved > 6) return;
    var t = targetOf(e);
    if (!t) { tip.style.opacity = "0"; hoverId = null; return; }
    if (e.pointerType === "touch") return;
    hoverId = pid(t); showTipAt(t, e.clientX, e.clientY);
  }
  function onMapClick(e) {
    if (moved > 6) return;
    var t = targetOf(e); if (!t) return;
    select(pid(t), false);
    if (e.pointerType === "touch" || matchMedia("(hover: none)").matches) showTipAt(t, e.clientX, e.clientY);
  }
  [regionsG, dotsG].forEach(function (g) {
    g.addEventListener("pointermove", onMapMove);
    g.addEventListener("click", onMapClick);
    g.addEventListener("pointerleave", function () { tip.style.opacity = "0"; hoverId = null; });
  });
  mapEl.addEventListener("keydown", function (e) {
    if (e.key === "+" || e.key === "=") zoomAt(1.5); else if (e.key === "-") zoomAt(1 / 1.5);
  });
  mapEl.setAttribute("tabindex", "0");

  function drawMarks() {
    marksG.innerHTML = "";
    var pl = placeById(S.sel);
    if (!pl) return;
    var xy;
    if (pl.kind === "place") xy = project(pl.lat, pl.lon);
    else if (pl.kind === "region" && regXY[pl.id]) xy = project(regXY[pl.id][0], regXY[pl.id][1]);
    else return;
    var r = 7 / Z.k;
    marksG.appendChild(svgel("circle", { cx: xy[0].toFixed(1), cy: xy[1].toFixed(1), r: (r * 1.8).toFixed(2) }));
    marksG.appendChild(svgel("circle", { cx: xy[0].toFixed(1), cy: xy[1].toFixed(1), r: (r * 0.55).toFixed(2), "class": "core" }));
  }
  function flyTo(pl) {
    var xy;
    if (pl.kind === "place") xy = project(pl.lat, pl.lon);
    else if (pl.kind === "region") { var r = regXY[pl.id]; if (!r) return; xy = project(r[0], r[1]); }
    else { var b = pathOf[pl.c] && pathOf[pl.c].getBBox(); if (!b) return; xy = [b.x + b.width / 2, b.y + b.height / 2]; }
    var k = pl.kind === "place" ? Math.max(Z.k, 4) : Math.max(Z.k, 2.5);
    Z.k = k; Z.x = GF.w / 2 - xy[0] * k; Z.y = GF.h / 2 - xy[1] * k; applyZ();
  }

  // ======================================================================
  // поиск: муниципалитеты, регионы, страны
  // ======================================================================
  var qEl = $("q"), qsug = $("qsug"), qx = $("qx");
  // Показывается всегда имя источника (Wien, Praha), но ищется и по английскому
  // экзониму: читатель набирает Vienna, а в данных его нет.
  L.forEach(function (l) { l._q = fold(l.name); l._qa = l.alias ? fold(l.alias) : ""; });
  N3.forEach(function (n) { n._q = fold(n.name); });
  C.forEach(function (c) { c._q = fold(c.n); });
  // Поиск нужен в трёх местах: на карте и в двух полях блока переезда. Раньше он
  // был жёстко привязан к одному полю, поэтому вынесен в фабрику.
  function find(q, filter) {
    q = fold(q).trim(); if (!q) return [];
    var exact = [], head = [], tail = [];
    function scan(list, pred) {
      for (var i = 0; i < list.length; i++) {
        var it = list[i]; if (pred && !pred(it)) continue;
        if (filter && !filter(it)) continue;
        var a = it._qa || "";
        if (it._q === q || a === q) exact.push(it);
        else if (it._q.indexOf(q) === 0 || (a && a.indexOf(q) === 0)) head.push(it);
        else if (q.length > 2 && (it._q.indexOf(q) > 0 || (a && a.indexOf(q) > 0))) tail.push(it);
      }
    }
    scan(C, function (c) { return c.espon; }); scan(L); scan(N3, function (n) { return n.sp || n.rp; });
    return exact.concat(head, tail).slice(0, 9);
  }

  function makePicker(o) {
    var el = $(o.input), box = $(o.sug), clr = o.clear ? $(o.clear) : null;
    var sug = [], idx = -1;
    function close() { box.hidden = true; box.innerHTML = ""; sug = []; idx = -1; el.setAttribute("aria-expanded", "false"); }
    function draw() {
      box.innerHTML = sug.length ? sug.map(function (it, i) {
        var kind = it.kind === "place" ? (DEG[it.deg] || FRAMES[frameOf(it)].unit)
                 : it.kind === "region" ? FRAMES[frameOf(it)].reg : "country";
        var right = it.kind === "cc" ? fmtInt(it.pop) + " people" : esc(ccName(it.cc)) + (it.kind === "place" ? " · " + fmtInt(it.pop) : "");
        var shown = esc(it.name) + (it.alias ? " <em>" + esc(it.alias) + "</em>" : "");
        return "<li role=\"option\" data-i=\"" + i + "\" aria-selected=\"" + (i === idx) + "\"><span>" + shown + "</span><span class=\"kind\">" + kind + "</span><span class=\"cy\">" + right + "</span></li>";
      }).join("") : "<li class=\"none\">Nothing matches. Try the local spelling: Wien, Praha, København.</li>";
      box.hidden = false; el.setAttribute("aria-expanded", "true");
    }
    function take(it) {
      if (!it) return;
      el.value = it.name; if (clr) clr.hidden = false;
      close(); o.onPick(it);
    }
    el.addEventListener("input", function () {
      if (clr) clr.hidden = !el.value;
      sug = find(el.value, o.filter); idx = sug.length ? 0 : -1;
      if (!el.value.trim()) { close(); if (o.onClear) o.onClear(); } else draw();
    });
    el.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { if (sug.length) { idx = (idx + 1) % sug.length; draw(); } e.preventDefault(); }
      else if (e.key === "ArrowUp") { if (sug.length) { idx = (idx - 1 + sug.length) % sug.length; draw(); } e.preventDefault(); }
      else if (e.key === "Enter") { take(sug[idx]); e.preventDefault(); }
      else if (e.key === "Escape") close();
    });
    el.addEventListener("focus", function () { if (sug.length) draw(); });
    box.addEventListener("mousedown", function (e) {
      var li = e.target.closest("li[data-i]"); if (li) { e.preventDefault(); take(sug[+li.getAttribute("data-i")]); }
    });
    if (clr) clr.addEventListener("click", function () { el.value = ""; clr.hidden = true; close(); if (o.onClear) o.onClear(); el.focus(); });
    document.addEventListener("click", function (e) { if (!e.target.closest("#" + o.input) && !e.target.closest("#" + o.sug)) close(); });
    return { set: function (name) { el.value = name || ""; if (clr) clr.hidden = !name; }, close: close };
  }

  var mapPick = makePicker({ input: "q", sug: "qsug", clear: "qx", onPick: function (it) { select(pid(it), true); } });

  // Поля блока переезда: те же подсказки, но выбор кладётся в своё состояние.
  movePickFrom = makePicker({ input: "mfrom", sug: "mfromsug", clear: "mfromx",
    onPick: function (it) { S.mf = pid(it); drawMove(); syncURL(); },
    onClear: function () { S.mf = null; drawMove(); syncURL(); } });
  movePickTo = makePicker({ input: "mto", sug: "mtosug", clear: "mtox",
    onPick: function (it) { S.mt = pid(it); drawMove(); syncURL(); },
    onClear: function () { S.mt = null; drawMove(); syncURL(); } });
  (function () {
    var mi = $("minc"), mc = $("mcur");
    Object.keys(FX).forEach(function (k) { mc.appendChild(el("option", { value: k }, k)); });
    mc.value = S.mc || S.cur;
    mi.value = S.mi || "";
    mi.addEventListener("input", function () {
      S.mi = Math.max(0, Math.min(1e7, +mi.value || 0));
      S.mc = S.mi ? mc.value : null;
      drawMove(); syncURL();
    });
    mc.addEventListener("change", function () { if (S.mi) { S.mc = mc.value; drawMove(); syncURL(); } });
  })();
  // Поля заполняются не здесь, а после readURL(): на этом шаге состояние ещё пустое.
  function syncMoveInputs() {
    var a = placeById(S.mf), b = placeById(S.mt);
    movePickFrom.set(a ? a.name : "");
    movePickTo.set(b ? b.name : "");
    $("minc").value = S.mi || "";
    $("mcur").value = S.mc || S.cur;
  }

  document.addEventListener("keydown", function (e) {
    if (e.key !== "/" || e.metaKey || e.ctrlKey || e.altKey) return;
    var t = e.target, tag = t && t.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (t && t.isContentEditable)) return;
    e.preventDefault(); qEl.focus(); qEl.select();
  });

  // ======================================================================
  // переезд за работой: сколько должно стоить предложение
  // ======================================================================
  // Считается «эквивалентное предложение» — доход в новом месте, при котором
  // читателю хватит на столько же метров, сколько дома. Для аренды это простое
  // отношение цен за метр, для покупки в него входит и ставка: одна и та же цена
  // при 2 % и при 6 % даёт разную площадь, и это ровно тот эффект ипотечного
  // продукта, который иначе остаётся невидимым.
  var movePickFrom, movePickTo;
  function moveIncEUR() { return S.mi > 0 && S.mc ? S.mi / FX[S.mc] : 0; }
  // Ставки у двух слоёв разного возраста, и молчать об этом нельзя: европейские —
  // национальные средние 2023 года из статьи, американская — средняя недельная
  // ставка Freddie Mac за 2024 год: в этих долларах ACS и выражает суммы.
  function rateVintage(a, b) {
    var f = {}; f[frameOf(a)] = 1; f[frameOf(b)] = 1;
    var t = [];
    if (f.eu) t.push("European rates are the national averages the study used, mostly 2023, not today's");
    if (f.na) t.push("the US rate is the Freddie Mac 30-year average for 2024, the year whose dollars the ACS estimates are in");
    return t.join("; ") + ". Put your own in the rate field above if you know better ones.";
  }
  function annuityOf(pl, fallback) {
    var r = rateOf(pl);
    return r === null ? fallback : annuity(r, S.term);
  }
  // Блок переезда считает всё в евро. Цены места записаны в валюте его страны, и
  // без приведения отношение «цена там к цене дома» между долларовым округом и
  // европейским городом было бы умножено на курс — то есть просто неверно.
  function toEUR(v, pl) { return v / (FX[curOf(pl)] || 1); }
  function spEUR(pl) { return pl.sp ? toEUR(pl.sp, pl) : 0; }
  function rpEUR(pl) { return pl.rp ? toEUR(pl.rp, pl) : 0; }
  // Корзина жилья — то, что сравнивается между двумя местами. Там, где есть цена
  // за метр, это N м² читателя; там, где её нет, — медианное жильё округа.
  // Отношение корзин имеет смысл всегда, но обещать «столько же метров» можно
  // только когда обе корзины измерены в метрах; иначе честный ответ — «та же
  // доля дохода на своё типовое жильё», и блок говорит именно это.
  function basketRentEUR(pl) {
    if (hasM2(frameOf(pl))) return pl.rp ? toEUR(rentAt(pl, mapN()) * mapN(), pl) : 0;
    var x = EX[pid(pl)]; return x && x.rent ? toEUR(x.rent, pl) : 0;
  }
  function basketPriceEUR(pl) {
    if (hasM2(frameOf(pl))) return pl.sp ? toEUR(priceAt(pl, mapN()) * mapN(), pl) : 0;
    var x = EX[pid(pl)]; return x && x.val ? toEUR(x.val, pl) : 0;
  }
  function sameSpace(a, b) { return hasM2(frameOf(a)) && hasM2(frameOf(b)); }
  function basketWord(pl, what) {
    if (hasM2(frameOf(pl))) return mapN() + " m²";
    return what === "rent" ? "the median rental" : "the median home";
  }
  function homeIncome(pl) { return mine() ? incEUR() : toEUR(localMonthly(pl), pl); }
  function drawMove() {
    var box = $("moveout");
    var a = placeById(S.mf), b = placeById(S.mt);
    if (!a || !b) {
      box.innerHTML = "<p class=\"mempty\">Pick both places to see the answer. Everything else on this page already applies: your term, deposit and the share of income you are willing to spend.</p>";
      return;
    }
    var incA = homeIncome(a);
    if (!incA) { box.innerHTML = "<p class=\"mempty\">No income on record for " + esc(a.name) + ". Enter your own above and switch to \u201cMy income\u201d.</p>"; return; }

    var rows = [], notes = [], rateNote2 = false, buyNeed = null;
    var same = sameSpace(a, b);
    var rentA = basketRentEUR(a), rentB = basketRentEUR(b);
    if (rentA && rentB) {
      var needRent = incA * (rentB / rentA);
      rows.push({ what: same ? "to rent the same space" : "to keep rent at the same share of income",
                  need: needRent, now: incA,
                  detail: same
                    ? fmtM2(rentM2(a)) + " m² at home costs " + fmtEur(Math.round(needRent)) + " a month of income there"
                    : basketWord(a, "rent") + " at home against " + basketWord(b, "rent") + " there \u2014 " +
                      fmtEur(Math.round(rentA)) + " a month against " + fmtEur(Math.round(rentB)) });
    } else {
      var noRp = rentA ? b : a;
      notes.push("No rent on record for " + esc(noRp.name) + ", so renting cannot be compared.");
    }

    // Покупка: в отношение входит и цена корзины, и аннуитет по ставке своей страны.
    var annA = annuityOf(a, null), annB = annuityOf(b, null);
    var buyA = basketPriceEUR(a), buyB = basketPriceEUR(b);
    if (buyA && buyB && annA && annB) {
      var needBuy = incA * (buyB / buyA) * (annA / annB);
      rows.push({ what: same ? "to buy the same space" : "to keep buying at the same share of income",
                  need: needBuy, now: incA,
                  detail: (same ? fmtM2(buyM2(a)) + " m² at home" : basketWord(a) + " at home against " + basketWord(b) + " there") +
                          ", on a " + S.term + "-year mortgage at " + fmtRate(rateOf(b)) + " there against " + fmtRate(rateOf(a)) + " at home" });
      buyNeed = needBuy;
      rateNote2 = S.rate === null;
    } else notes.push("No price or no mortgage rate for one of the two, so buying cannot be compared.");
    // Разные корзины — не мелочь оформления, и читатель обязан узнать об этом до
    // того, как поверит проценту: площади жилья в США нет, поэтому сравнивается
    // не одинаковая площадь, а одинаковая доля дохода на своё типовое жильё.
    if (!same && rows.length) {
      notes.push("The two layers are not measured in the same unit: Europe has a price per square metre, the United States does not publish floor area, so the comparison keeps the share of income equal rather than the space. Part of the gap is therefore size and not price \u2014 the American basket is a whole home, and how big it is, is exactly what the data does not say.");
    }

    if (!rows.length) { box.innerHTML = "<p class=\"mempty\">" + notes.join(" ") + "</p>"; return; }

    var offer = moveIncEUR();
    var h = "<p class=\"mhead\">Moving from <b>" + esc(a.name) + "</b> to <b>" + esc(b.name) + "</b> on " + fmtEur(Math.round(incA)) + " net a month</p><div class=\"mgrid\">";
    rows.forEach(function (r) {
      var ratio = r.need / r.now;
      var cls = ratio > 1.02 ? "up" : ratio < 0.98 ? "down" : "same";
      var verdict = ratio > 1.02 ? "+" + Math.round((ratio - 1) * 100) + " %" : ratio < 0.98 ? "−" + Math.round((1 - ratio) * 100) + " %" : "about the same";
      h += "<div class=\"mcard " + cls + "\"><p class=\"mlabel\">The offer needs to be</p>" +
           "<p class=\"mbig\">" + fmtEur(Math.round(r.need)) + "</p>" +
           "<p class=\"mwhat\">net per month " + r.what + " <b>" + verdict + "</b></p>" +
           "<p class=\"mdetail\">" + r.detail + "</p>";
      if (offer) {
        var gap = offer - r.need;
        h += "<p class=\"mverdict " + (gap >= 0 ? "ok" : "no") + "\">Your offer of " + fmtEur(Math.round(offer)) + " is " +
             (gap >= 0 ? fmtEur(Math.round(gap)) + " above" : fmtEur(Math.round(-gap)) + " short") + "</p>";
      }
      h += "</div>";
    });
    h += "</div>";
    if (offer) {
      // Что предложение даёт на самом деле — прямой расчёт, а не через отношение.
      var got = [];
      var offerB = offer * (FX[curOf(b)] || 1);          // предложение в валюте места
      if (hasM2(frameOf(b))) {
        if (b.sp) got.push(fmtM2(buyM2(b, { income: offerB })) + " m² to buy");
        if (b.rp) got.push(fmtM2(offerB * S.share / 100 / b.rp) + " m² to rent");
        if (got.length) h += "<p class=\"mnote\">On " + fmtEur(Math.round(offer)) + " in " + esc(b.name) + " you could take " + got.join(" or ") +
          (hasM2(frameOf(a)) ? ", against " + fmtM2(buyM2(a)) + " m² and " + fmtM2(rentM2(a)) + " m² at home" : "") + ".</p>";
      } else {
        // В кадре без метров то же самое говорится про целое жильё: сколько лет
        // предложения стоит медианный дом и какую долю съедает медианная аренда.
        var xb = EX[pid(b)];
        if (xb && xb.val) got.push((xb.val / (offerB * 12)).toFixed(1) + " years of it for the median home");
        if (xb && xb.rent) got.push(Math.round(xb.rent / offerB * 100) + " % of it for the median rent");
        if (got.length) h += "<p class=\"mnote\">On " + fmtEur(Math.round(offer)) + " in " + esc(b.name) + " the median home costs " + got.join(", and ") + ".</p>";
      }
    }
    if (rateNote2) {
      // Подписи года мало: читатель увидит год и не поймёт, что от него зависит
      // знак. Поэтому вклад ставки показывается числом. При равных ставках
      // аннуитеты сокращаются, и остаётся чистое отношение цен — это и есть ответ
      // «а если бы ипотека стоила одинаково».
      var flat = (buyA && buyB) ? incA * (buyB / buyA) : null;
      if (flat && buyNeed) {
        var dp = Math.round((flat / incA - 1) * 100);
        h += "<p class=\"mnote\"><b>How much of this is the mortgage, not the housing.</b> If both countries charged the same interest, the offer would need to be " +
             fmtEur(Math.round(flat)) + " (" + (dp >= 0 ? "+" : "−") + Math.abs(dp) + " %) " + (same ? "to buy the same space" : "to keep the same share of income") + " — that is the price difference alone. The rate difference moves it by " +
             fmtEur(Math.round(Math.abs(buyNeed - flat))) +  " a month. " + rateVintage(a, b) + "</p>";
      } else {
        h += "<p class=\"mnote\">" + rateVintage(a, b) + "</p>";
      }
    }
    if (notes.length) h += "<p class=\"mnote\">" + notes.join(" ") + "</p>";
    box.innerHTML = h;
  }

  // ======================================================================
  // карточка выбранного места
  // ======================================================================
  var cardEl = $("card");
  function select(id, fly) {
    S.sel = id;
    var pl = placeById(id);
    // Поиск ищет по обоим слоям, а карта показывает один: выбрали американский
    // округ из европейского кадра — кадр переезжает следом, иначе метка улетела
    // бы за край.
    if (pl && !inFrame(pl)) {
      S.frame = frameOf(pl);
      buildRegButtons(); syncControls();
      buildFrame();          // до перелёта: точка считается в проекции кадра
    }
    if (pl && fly) flyTo(pl);
    paintMap(); drawMarks(); drawCard(); drawRank(); drawMove(); syncURL();
  }
  var cardN = null;                          // «сколько метров» в карточке: своё поле, фильтр не двигает
  function wantN() { return cardN || S.want || 70; }
  function drawCard() {
    var pl = placeById(S.sel);
    if (!pl) {
      cardEl.innerHTML = "<p class=\"plabel\">Selected place</p><p class=\"cempty\">Search a town above or click a region on the map. The card shows what your settings mean there, and what it would take.</p>";
      return;
    }
    var b = buyM2(pl), r = rentM2(pl), rate = rateOf(pl), bud = budget(pl);
    var kindLine = pl.kind === "place" ? (DEG[pl.deg] ? DEG[pl.deg] + (pl.coast ? ", coastal" : "") + " · " : "") + fmtInt(pl.pop) + " people · " + FRAMES[frameOf(pl)].reg + " " + esc(N3[pl.reg] ? N3[pl.reg].name : "")
                 : pl.kind === "region" ? (frameOf(pl) === "eu" ? "NUTS 3 region" : "state") + " · " + fmtInt(pl.pop) + " people · data for " + Math.round(pl.covS * 100) + " % of them"
                 : "country · " + fmtInt(pl.pop) + " people · " + fmtInt(pl.places) + " " + FRAMES[frameOf(pl)].units;
    // Насколько твёрдая медиана. У европейского слоя такой меры нет: сервис не
    // публикует числа объявлений. У ACS она есть — доверительный интервал, — и
    // округа, где он шире пятой части оценки, обязаны сказать это сами, а не
    // выглядеть как все остальные.
    var us = !hasM2(frameOf(pl));
    var xs = EX[pid(pl)];
    if (us && xs && xs.moe && xs.val) {
      var relMoe = xs.moe / xs.val * 100;
      kindLine += " · median home value \u00b1" + Math.round(relMoe) + " %";
      if (relMoe > MOEHI) kindLine += ", a wide interval for a median";
    }
    function cap(t) { return t.charAt(0).toUpperCase() + t.slice(1); }
    var h = "<p class=\"plabel\">" + (pl.kind === "place" ? cap(FRAMES[frameOf(pl)].unit)
                                     : pl.kind === "region" ? cap(FRAMES[frameOf(pl)].reg) : "Country") + "</p>" +
      "<h3 class=\"cname\">" + esc(pl.name) + "</h3><p class=\"cmeta\">" + esc(ccName(pl.cc)) + " · " + kindLine + "</p>";
    if (us) {
      // Метров здесь нет — и крупными цифрами стоят те две метрики, которые в
      // американских данных действительно есть. Обе считаются на медианное жильё
      // округа, а не на площадь, и подписаны именно так.
      var yv = yearsFor(pl), sv = rentShare(pl);
      h += "<div class=\"cbig\"><div><b class=\"" + bigCls(clsFor("years", yv)) + "\">" + (yv === null ? "—" : yv.toFixed(1)) + "</b><span>years of income for the median home</span></div>" +
           "<div><b class=\"" + bigCls(clsFor("share", sv)) + "\">" + (sv === null ? "—" : Math.round(sv) + " %") + "</b><span>of income for the median rent</span></div></div>";
    } else {
      h += "<div class=\"cbig\"><div><b class=\"" + bigCls(cls(b)) + "\">" + fmtM2(b) + "</b><span>m² to buy" + (b === null ? "" : ", " + S.term + " years") + "</span></div>" +
           "<div><b class=\"" + bigCls(cls(r)) + "\">" + fmtM2(r) + "</b><span>m² to rent</span></div></div>";
    }
    h += "<div class=\"crow\"><span>" + (mine() ? "Your housing budget" : "A third of the local income") + "</span><span>" + fmtLoc(pl, bud) + " / month</span></div>";
    if (b !== null || (us && rate !== null)) {
      var loan = bud * annuity(rate, S.term);
      h += "<div class=\"crow\"><span>Loan that pays off</span><span>" + fmtLoc(pl, loan) + "</span></div>";
      if (S.dep) h += "<div class=\"crow\"><span>Plus a " + S.dep + " % deposit</span><span>" + fmtLoc(pl, loan / (1 - S.dep / 100) - loan) + "</span></div>";
      // В кадре без метров бюджет всё равно можно сопоставить с жильём — только не
      // в метрах, а в целых домах: вот цена, которую он вытягивает, и вот медиана.
      // Без взноса цена равна кредиту, и вторая строка была бы тем же числом
      // под другим названием.
      if (us && S.dep) h += "<div class=\"crow\"><span>Home price that reaches</span><span>" + fmtLoc(pl, loan / (1 - S.dep / 100)) + "</span></div>";
    }
    if (us) {
      h += "<div class=\"crow\"><span>Median home value, owner's estimate</span><span>" + (xs && xs.val ? fmtLoc(pl, xs.val) : "no data") + "</span></div>";
      h += "<div class=\"crow\"><span>Median rent, utilities included</span><span>" + (xs && xs.rent ? fmtLoc(pl, xs.rent) + " / month" : "no data") + "</span></div>";
      h += "<div class=\"crow\"><span>Price per m²</span><span>not published for US counties</span></div>";
    } else {
      h += "<div class=\"crow\"><span>Sale price, taxes and fees in</span><span>" + (pl.sp ? fmtLoc(pl, pl.sp) + " / m²" : "no data") + "</span></div>";
      h += "<div class=\"crow\"><span>Rent</span><span>" + (pl.rp ? fmtLoc(pl, pl.rp, 2) + " / m² / month" : "no data") + "</span></div>";
    }
    // Название дохода — от слоя: у Евростата это эквивалентный располагаемый после
    // налогов, у ACS — медианный по домохозяйству до налогов. Одна подпись на оба
    // была бы ровно той ошибкой, о которой страница предупреждает читателя.
    h += "<div class=\"crow\"><span>" + (us ? "Median household income, before tax"
                                        : "Average income per adult-equivalent") + "</span><span>" + (pl.inc ? fmtLoc(pl, pl.inc / 12) + " / month" : "no data") + "</span></div>";
    h += "<div class=\"crow\"><span>Mortgage rate used</span><span>" + fmtRate(rate) + (S.rate !== null ? " (yours)" : "") + "</span></div>";
    if (studyBuy(pl) || studyRent(pl)) h += "<div class=\"crow\"><span>The study's own figures</span><span>" + fmtM2(studyBuy(pl)) + " m² buy · " + fmtM2(studyRent(pl)) + " m² rent</span></div>";
    if (mine() && pl.inc) {
      // Оба числа — в валюте места, иначе евро делились бы на доллары. И подпись
      // от слоя: «на взрослого-эквивалента» верно для Евростата и неверно для
      // медианного дохода домохозяйства у ACS.
      var eq = myIncome(pl) / eqFactor(), ratio = eq / (pl.inc / 12);
      h += "<div class=\"crow\"><span>Your income vs the local " + (us ? "median" : "average") + "</span><span>" + ratio.toFixed(2) + "\u00d7 " +
           (us ? "of a median household, before tax" : "per adult-equivalent") + "</span></div>";
    }
    // что нужно
    var N = wantN();
    h += "<p class=\"csub\">What it would take</p>";
    if (pl.sp && rate !== null) {
      var need = incomeNeeded(pl, N);
      var have = myIncome(pl);          // доход читателя в валюте места
      h += "<p class=\"cwhat\">To buy <input type=\"number\" id=\"c-n\" value=\"" + N + "\" min=\"10\" max=\"400\" step=\"5\"> m² here on " + shareText() + " of income over " + S.term + " years" + (S.dep ? " with a " + S.dep + " % deposit" : "") + " you need <b>" + fmtLoc(pl, need) + " net a month</b>" +
           (mine() ? " — you have " + fmtLoc(pl, have) + (have >= need ? ", enough" : ", " + Math.round((1 - have / need) * 100) + " % short") : "") + ".</p>";
      var depAmt = N * pl.sp * (S.dep || 20) / 100;
      // Взнос — в валюте места, сбережения читателя — в евро, поэтому для счёта
      // они приводятся; без этого доллары делились бы на евро.
      var savLoc = S.sav * (FX[curOf(pl)] || 1);
      h += "<p class=\"cwhat\">A " + (S.dep || 20) + " % deposit on " + N + " m² is <b>" + fmtLoc(pl, depAmt) + "</b>. Saving <input type=\"number\" id=\"c-sav\" value=\"" + S.sav + "\" min=\"0\" step=\"50\"> € a month, that takes <b>" + (savLoc > 0 ? (depAmt / savLoc / 12).toFixed(1) + " years" : "forever") + "</b>.</p>";
    }
    if (pl.rp) h += "<p class=\"cwhat\">To rent " + N + " m² here on " + shareText() + " of income you need <b>" + fmtLoc(pl, N * pl.rp / (S.share / 100)) + " net a month</b>.</p>";
    if (us && xs && xs.val && rate !== null) {
      // Тот же вопрос, что и в Европе, но заданный к целому дому: площади нет, и
      // «сколько нужно на 70 м²» здесь не имеет ответа — а «сколько нужно на
      // медианный дом округа» имеет, и это ровно то же арифметическое действие.
      var needUS = xs.val * (1 - S.dep / 100) / annuity(rate, S.term) / (S.share / 100);
      var haveUS = myIncome(pl);
      h += "<p class=\"cwhat\">To buy the median home here (" + fmtLoc(pl, xs.val) + ") on " + shareText() + " of income over " + S.term + " years" + (S.dep ? " with a " + S.dep + " % deposit" : "") + " you need <b>" + fmtLoc(pl, needUS) + " net a month</b>" +
           (mine() ? " — you have " + fmtLoc(pl, haveUS) + (haveUS >= needUS ? ", enough" : ", " + Math.round((1 - haveUS / needUS) * 100) + " % short") : "") + ".</p>";
      var depUS = xs.val * (S.dep || 20) / 100, savUS = S.sav * (FX[curOf(pl)] || 1);
      h += "<p class=\"cwhat\">A " + (S.dep || 20) + " % deposit on it is <b>" + fmtLoc(pl, depUS) + "</b>. Saving <input type=\"number\" id=\"c-sav\" value=\"" + S.sav + "\" min=\"0\" step=\"50\"> € a month, that takes <b>" + (savUS > 0 ? (depUS / savUS / 12).toFixed(1) + " years" : "forever") + "</b>.</p>";
    }
    if (us && xs && xs.rent) h += "<p class=\"cwhat\">To rent the median home here (" + fmtLoc(pl, xs.rent) + " a month) on " + shareText() + " of income you need <b>" + fmtLoc(pl, xs.rent / (S.share / 100)) + " net a month</b>.</p>";
    // список внутри региона или страны
    if (pl.kind !== "place") {
      var inside = L.filter(function (l) { return pl.kind === "region" ? l.reg === pl.idx : l.cc === pl.c; })
                    .sort(function (a, b2) { return b2.pop - a.pop; }).slice(0, 8);
      if (inside.length) {
        var uw = FRAMES[frameOf(pl)].units;
        h += "<p class=\"csub\">" + (pl.kind === "region" ? cap(uw) + " in the " + FRAMES[frameOf(pl)].reg : "Largest " + uw) + "</p><ul class=\"clist\">" +
          inside.map(function (l) { return "<li data-id=\"" + esc(l.id) + "\"><span>" + esc(l.name) + "</span><span>" + summaryOf(l) + "</span></li>"; }).join("") + "</ul>";
      }
    } else if (N3[pl.reg]) {
      h += "<p class=\"csub\">Around it</p><ul class=\"clist\"><li data-id=\"n:" + esc(N3[pl.reg].id) + "\"><span>" + cap(FRAMES[frameOf(pl)].reg) + " " + esc(N3[pl.reg].name) + "</span><span>" + summaryOf(N3[pl.reg]) + "</span></li>" +
           "<li data-id=\"c:" + pl.cc + "\"><span>" + esc(ccName(pl.cc)) + "</span><span>" + summaryOf(C[CI[pl.cc]]) + "</span></li></ul>";
    }
    var inCmp = S.cmp.indexOf(pid(pl)) >= 0;
    h += "<div class=\"cbtns\"><button type=\"button\" class=\"cbtn" + (inCmp ? " on" : "") + "\" data-cmp=\"" + esc(pid(pl)) + "\">" + (inCmp ? "✓ In the comparison" : "+ Compare") + "</button>" +
         (pl.kind !== "cc" ? "<button type=\"button\" class=\"cbtn\" data-fly>Show on the map</button>" : "") +
         "<button type=\"button\" class=\"cbtn\" data-unsel>Clear</button></div>";
    cardEl.innerHTML = h;
  }
  cardEl.addEventListener("click", function (e) {
    var li = e.target.closest("li[data-id]"); if (li) { select(li.getAttribute("data-id"), true); return; }
    var cb = e.target.closest("[data-cmp]"); if (cb) { toggleCmp(cb.getAttribute("data-cmp")); return; }
    if (e.target.closest("[data-fly]")) { var pl = placeById(S.sel); if (pl) flyTo(pl); return; }
    if (e.target.closest("[data-unsel]")) { select(null, false); return; }
  });
  cardEl.addEventListener("input", function (e) {
    var pl = placeById(S.sel); if (!pl) return;
    if (e.target.id === "c-n") { cardN = Math.max(10, Math.min(400, +e.target.value || 70)); redrawWhat(pl, cardN); drawCmp(); }
    if (e.target.id === "c-sav") { S.sav = Math.max(0, +e.target.value || 0); redrawWhat(pl, wantN()); syncURL(); }
  });
  function redrawWhat(pl, N) {
    var rate = rateOf(pl);
    var ps = cardEl.querySelectorAll(".cwhat");
    if (!ps.length) return;
    if (pl.sp && rate !== null) {
      var need = incomeNeeded(pl, N);
      ps[0].querySelector("b").innerHTML = fmtLoc(pl, need) + " net a month";
      var depAmt = N * pl.sp * (S.dep || 20) / 100;
      var bs = ps[1].querySelectorAll("b");
      bs[0].textContent = fmtLoc(pl, depAmt);
      var savLoc = S.sav * (FX[curOf(pl)] || 1);   // как в drawCard: евро → валюта места
      bs[1].textContent = savLoc > 0 ? (depAmt / savLoc / 12).toFixed(1) + " years" : "forever";
      ps[1].firstChild.nodeValue = "A " + (S.dep || 20) + " % deposit on " + N + " m² is ";
    }
    // У американского округа площади нет, и абзац про взнос свой — к целому дому.
    var xs = EX[pid(pl)], savIn = $("c-sav");
    if (!pl.sp && xs && xs.val && savIn) {
      var depUS = xs.val * (S.dep || 20) / 100, savUS = S.sav * (FX[curOf(pl)] || 1);
      var bu = savIn.parentNode.querySelectorAll("b");
      bu[bu.length - 1].textContent = savUS > 0 ? (depUS / savUS / 12).toFixed(1) + " years" : "forever";
    }
    if (pl.rp) { var last = ps[ps.length - 1]; last.innerHTML = "To rent " + N + " m² here on " + shareText() + " of income you need <b>" + fmtLoc(pl, N * pl.rp / (S.share / 100)) + " net a month</b>."; }
  }

  // ======================================================================
  // сравнение
  // ======================================================================
  function toggleCmp(id) {
    var i = S.cmp.indexOf(id);
    if (i >= 0) S.cmp.splice(i, 1); else { if (S.cmp.length >= 4) S.cmp.shift(); S.cmp.push(id); }
    drawCard(); drawCmp(); drawRank(); syncURL();
  }
  var chipsEl = $("chips"), cmpEl = $("cmptable");
  function cmpRows() {
    var P = S.cmp.map(placeById).filter(Boolean);
    var N = wantN();
    // Деньги в таблице обязаны быть в одной валюте. Если все выбранные места из
    // одного слоя, показывается его собственная — иначе всё сводится к евро по
    // курсу ЕЦБ, и заголовок группы это говорит: сравнивать доллары с евро
    // столбец в столбец и подсвечивать «лучшее» было бы враньём.
    var seen = {};
    P.forEach(function (p) { seen[curOf(p)] = 1; });
    var keys = Object.keys(seen), one = keys.length === 1;
    var cur = one ? keys[0] : "EUR";
    var sym = cur === "USD" ? "$" : cur === "EUR" ? "\u20ac" : cur + "\u00a0";
    function money(p, v) { return v === null || v === undefined ? null : v / (FX[curOf(p)] || 1) * (FX[cur] || 1); }
    function row(label, fn, best, fmt) { return { label: label, vals: P.map(fn), best: best, fmt: fmt || "int" }; }
    function ex(p, k) { var x = EX[pid(p)]; return x && x[k] ? x[k] : null; }
    // Метры есть не у всех слоёв, и от этого зависит не оформление, а смысл
    // строк. Три случая: все места с метрами, ни одного, и смесь — в последнем
    // остаются только те величины, которые определены по обе стороны.
    var allM2 = P.every(function (p) { return hasM2(frameOf(p)); });
    var noM2 = P.every(function (p) { return !hasM2(frameOf(p)); });
    var money2 = one ? "" : " \u00b7 money converted to euro at the ECB rate of " + FX_DATE;
    var groups;

    if (allM2) {
      groups = [
        ["With your settings" + money2, [
          row("m² to buy", function (p) { return buyM2(p); }, "max", "m2"),
          row("m² to rent", function (p) { return rentM2(p); }, "max", "m2"),
          row("Monthly housing budget, " + sym, function (p) { return money(p, budget(p)); }, null),
          row("Income needed for " + N + " m² to buy, " + sym + "/month", function (p) { return money(p, incomeNeeded(p, N)); }, "min"),
          row("Income needed for " + N + " m² to rent, " + sym + "/month", function (p) { return money(p, p.rp ? N * p.rp / (S.share / 100) : null); }, "min")
        ]],
        ["Same terms for everyone" + (mine() ? " (your income)" : " (local income)"), [
          row("m² to buy, 20 years", function (p) { return buyM2(p, { term: 20 }); }, "max", "m2"),
          row("m² to buy, 30 years", function (p) { return buyM2(p, { term: 30 }); }, "max", "m2"),
          row("m² to buy at 25 % of income", function (p) { return buyM2(p, { share: 25 }); }, "max", "m2"),
          row("m² to buy at a third of income", function (p) { return buyM2(p, { share: THIRD }); }, "max", "m2"),
          row("m² to rent at 25 % of income", function (p) { return rentM2(p, { share: 25 }); }, "max", "m2"),
          row("m² to rent at a third of income", function (p) { return rentM2(p, { share: THIRD }); }, "max", "m2")
        ]],
        ["The study's own figures", [
          row("m² to buy, average local income, 30 years", function (p) { return studyBuy(p); }, "max", "m2"),
          row("m² to rent, average local income", function (p) { return studyRent(p); }, "max", "m2")
        ]],
        ["The market" + money2, [
          row("Sale price incl. taxes and fees, " + sym + "/m²", function (p) { return money(p, p.sp || null); }, "min"),
          row("Rent, " + sym + "/m²/month", function (p) { return money(p, p.rp || null); }, "min", "dec2"),
          row("Average local income, " + sym + "/month", function (p) { return money(p, p.inc ? p.inc / 12 : null); }, "max"),
          row("Mortgage rate used, %", function (p) { return rateOf(p); }, "min", "dec2"),
          row("Population", function (p) { return p.pop; }, null)
        ]]
      ];
    } else if (noM2) {
      groups = [
        ["With your settings" + money2, [
          row("Years of income for the median home", function (p) { return yearsFor(p); }, "min", "dec1"),
          row("Median rent as a share of income, %", function (p) { return rentShare(p); }, "min", "pct"),
          row("Monthly housing budget, " + sym, function (p) { return money(p, budget(p)); }, null),
          row("Income needed to buy the median home, " + sym + "/month", function (p) {
            var v = ex(p, "val"), r = rateOf(p);
            return v && r !== null ? money(p, v * (1 - S.dep / 100) / annuity(r, S.term) / (S.share / 100)) : null;
          }, "min"),
          row("Income needed to rent the median home, " + sym + "/month", function (p) {
            var v = ex(p, "rent");
            return v ? money(p, v / (S.share / 100)) : null;
          }, "min")
        ]],
        ["The market" + money2, [
          row("Median home value, " + sym, function (p) { return money(p, ex(p, "val")); }, "min"),
          row("Median rent, " + sym + "/month", function (p) { return money(p, ex(p, "rent")); }, "min"),
          row("Median household income, " + sym + "/month", function (p) { return money(p, p.inc ? p.inc / 12 : null); }, "max"),
          row("Mortgage rate used, %", function (p) { return rateOf(p); }, "min", "dec2"),
          row("Population", function (p) { return p.pop; }, null)
        ]]
      ];
    } else {
      // Смесь слоёв. Метров у части мест нет вовсе, поэтому остаются только две
      // метрики, определённые везде, — но корзина под ними разная, и заголовок
      // группы обязан это сказать: в Европе это N м², в США медианное жильё.
      groups = [
        ["Both layers \u00b7 in Europe the basket is " + N + " m², in the United States the median home \u2014 floor area is not published for US counties" + money2, [
          row("Years of income", function (p) { return yearsFor(p); }, null, "dec1"),
          row("Rent as a share of income, %", function (p) { return rentShare(p); }, null, "pct"),
          row("Monthly housing budget, " + sym, function (p) { return money(p, budget(p)); }, null),
          row("Local income, " + sym + "/month", function (p) { return money(p, p.inc ? p.inc / 12 : null); }, null),
          row("Mortgage rate used, %", function (p) { return rateOf(p); }, null, "dec2"),
          row("Population", function (p) { return p.pop; }, null)
        ]],
        ["Europe only \u00b7 these need a price per square metre", [
          row("m² to buy", function (p) { return buyM2(p); }, null, "m2"),
          row("m² to rent", function (p) { return rentM2(p); }, null, "m2"),
          row("Sale price incl. taxes and fees, " + sym + "/m²", function (p) { return money(p, p.sp || null); }, null)
        ]],
        ["United States only \u00b7 these need a whole-home median", [
          row("Median home value, " + sym, function (p) { return money(p, ex(p, "val")); }, null),
          row("Median rent, " + sym + "/month", function (p) { return money(p, ex(p, "rent")); }, null)
        ]]
      ];
    }
    // «Лучшее» в смешанной таблице не подсвечивается вовсе: строки там сравнимы
    // по смыслу, но не по корзине, и зелёная клетка выдала бы разницу
    // определений за разницу мест.
    return { P: P, groups: groups, mixed: !allM2 && !noM2 };
  }
  function fmtCell(r, v) {
    if (v === null || v === undefined) return "—";
    if (r.fmt === "m2") return fmtM2(v);
    if (r.fmt === "dec2") return v.toFixed(2);
    if (r.fmt === "dec1") return v.toFixed(1);
    if (r.fmt === "pct") return Math.round(v) + " %";
    return fmtInt(v);
  }
  function drawCmp() {
    var P = S.cmp.map(placeById).filter(Boolean);
    chipsEl.innerHTML = P.map(function (p) {
      return "<span class=\"chip\">" + esc(p.name) + (p.kind !== "cc" ? " <small>" + esc(p.cc) + "</small>" : "") + "<button type=\"button\" data-rm=\"" + esc(pid(p)) + "\" aria-label=\"Remove\">×</button></span>";
    }).join("") + (P.length < 4 ? "<span class=\"chip empty\">" + (P.length ? "add up to " + (4 - P.length) + " more" : "nothing selected yet — add a place from the card or the rankings") + "</span>" : "");
    if (!P.length) { cmpEl.innerHTML = ""; return; }
    var cr = cmpRows();
    var h = "<thead><tr><th></th>" + P.map(function (p) { return "<th>" + esc(p.name) + "<br><small style=\"color:var(--ink-3);font-weight:400\">" + esc(ccName(p.cc)) + "</small></th>"; }).join("") + "</tr></thead><tbody>";
    cr.groups.forEach(function (g) {
      h += "<tr class=\"grp\"><td colspan=\"" + (P.length + 1) + "\">" + esc(g[0]) + "</td></tr>";
      g[1].forEach(function (r) {
        var bestIdx = -1;
        if (r.best && P.length > 1) {
          var bv = null;
          r.vals.forEach(function (v, i) { if (v === null) return; if (bv === null || (r.best === "max" ? v > bv : v < bv)) { bv = v; bestIdx = i; } });
        }
        h += "<tr><td>" + esc(r.label) + "</td>" + r.vals.map(function (v, i) { return "<td" + (i === bestIdx ? " class=\"best\"" : "") + ">" + fmtCell(r, v) + "</td>"; }).join("") + "</tr>";
      });
    });
    cmpEl.innerHTML = h + "</tbody>";
  }
  chipsEl.addEventListener("click", function (e) { var b = e.target.closest("[data-rm]"); if (b) toggleCmp(b.getAttribute("data-rm")); });

  // ======================================================================
  // рейтинги
  // ======================================================================
  var regsEl = $("regs");
  // Кнопки групп свои у каждого кадра: Европа делится на четыре части света, США —
  // на четыре переписных региона, и общего списка у них нет.
  function buildRegButtons() {
    var list = regionsList();
    regsEl.innerHTML = "";
    list.forEach(function (r) {
      var b = el("button", { type: "button", "class": "reg", "data-r": r[0], "aria-pressed": "true" }, r[1]);
      b.addEventListener("click", function () {
        S.reg[r[0]] = S.reg[r[0]] ? 0 : 1;
        if (!list.some(function (x) { return S.reg[x[0]]; })) list.forEach(function (x) { S.reg[x[0]] = 1; });
        syncControls(); drawRank(); syncURL();
      });
      regsEl.appendChild(b);
    });
    // Признак приморья приходит из европейского датасета; у американских округов
    // его нет, и показывать выключатель, который ничего не отфильтрует, незачем.
    if (S.frame === "eu") {
      var coastBtn = el("button", { type: "button", "class": "reg", id: "coastbtn", "aria-pressed": String(!!S.coast), title: "EU-27 municipalities flagged coastal by Eurostat" }, "coast only");
      coastBtn.addEventListener("click", function () { S.coast = S.coast ? 0 : 1; syncControls(); drawRank(); syncURL(); });
      regsEl.appendChild(coastBtn);
    } else {
      S.coast = 0;
    }
  }

  // Валюта и слова в шапке — от кадра: в европейском кадре цены в евро за метр
  // муниципалитета, в американском — в долларах за метр округа.
  // Колонки рейтинга — от кадра, потому что величины разные. Метров в
  // американском кадре нет вовсе, и колонка из прочерков притворялась бы дырой в
  // данных; вместо неё те же две метрики, что и на карте.
  function cap1(t) { return t.charAt(0).toUpperCase() + t.slice(1); }
  function rankCols() {
    var m = fr().sym, eu = m2Here();
    var cols = [["name", S.rank === "countries" ? "Country" : (eu ? "City" : cap1(fr().unit))]];
    if (eu) {
      cols.push(["buy", "m² to buy"], ["rent", "m² to rent"],
                ["price", "Price " + m + "/m²"], ["rentp", "Rent " + m + "/m²·mo"]);
    } else {
      cols.push(["years", "Years of income"], ["share", "Rent, % of income"],
                ["val", "Median home " + m], ["rnt", "Median rent " + m + "/mo"]);
    }
    cols.push(["inc", "Income " + m + "/mo"]);
    if (S.rank === "countries") cols.push(["rate", "Rate %"]);
    cols.push(["pop", "People"]);
    return cols;
  }
  // Ключ сортировки тоже живёт в кадре: «по метрам на покупку» в американском
  // кадре отсортировало бы таблицу по пустоте.
  function normSort() {
    var ok = rankCols().some(function (c) { return c[0] === S.sort; });
    if (ok) return;
    // Вместе с ключом меняется и направление: у метров больше — лучше, у лет
    // дохода и доли на аренду наоборот, и рейтинг, открывающийся худшими
    // местами, читался бы как список лучших.
    S.sort = m2Here() ? "buy" : "years";
    S.dir = m2Here() ? "desc" : "asc";
  }
  // Подписи вкладок рейтинга тоже от кадра, и вкладка стран прячется там, где
  // страна одна: рейтинг из одной строки — не рейтинг.
  function syncRankTabs() {
    var btns = document.querySelectorAll("#rankwhat button");
    var many = C.filter(inFrame).length > 1;
    btns[0].hidden = !many;
    btns[1].textContent = S.frame === "eu" ? "Cities" : "Counties";
    if (!many) { S.rank = "cities"; segSet("rankwhat", S.rank); }
  }
  function rankRows() {
    // Рейтинг не смешивает кадры. Доход в США считает ACS по домохозяйству и до
    // налогов, в Европе Евростат — эквивалентный и после налогов; поставить их в
    // одну таблицу значило бы выдать разницу определений за разницу рынков.
    var src = S.rank === "countries" ? C.filter(function (c) { return inFrame(c) && (c.sp || c.rp || EX["c:" + c.c]); })
                                     : L.filter(function (l) { return inFrame(l) && l.pop >= 100000; });
    var rows = src.filter(function (p) { return passReg(p) && (!S.coast || S.rank === "countries" || p.coast) && reaches(p); })
      .map(function (p) {
        var x = EX[pid(p)];
        return { p: p, name: p.name, buy: buyM2(p), rent: rentM2(p), price: p.sp || null,
                 rentp: p.rp || null, val: x && x.val ? x.val : null, rnt: x && x.rent ? x.rent : null,
                 years: yearsFor(p), share: rentShare(p),
                 inc: p.inc ? p.inc / 12 : null, rate: rateOf(p), pop: p.pop };
      });
    var k = S.sort, d = S.dir === "asc" ? 1 : -1;
    rows.sort(function (a, b) {
      var x = a[k], y = b[k];
      if (k === "name") return d * String(x).localeCompare(String(y));
      if (x === null) return 1; if (y === null) return -1;
      return d * (x - y);
    });
    return { rows: rows, total: src.length };
  }
  function drawRank() {
    syncRankTabs(); normSort();
    var cols = rankCols(), rr = rankRows();
    $("rankhead").innerHTML = "<th>#</th>" + cols.map(function (c) {
      return "<th data-sort=\"" + c[0] + "\"" + (S.sort === c[0] ? " aria-sort=\"" + (S.dir === "asc" ? "ascending" : "descending") + "\"" : "") + ">" + c[1] + "</th>";
    }).join("") + "<th></th>";
    $("rankbody").innerHTML = rr.rows.map(function (r, i) {
      var id = pid(r.p), inCmp = S.cmp.indexOf(id) >= 0;
      return "<tr data-id=\"" + esc(id) + "\"" + (S.sel === id ? " class=\"sel\"" : "") + "><td>" + (i + 1) + "</td>" + cols.map(function (c) {
        var v = r[c[0]];
        // Подпись под названием — страна там, где стран много, и регион там, где
        // страна одна: «Macon County, IL — United States» не сообщает ничего.
        if (c[0] === "name") {
          var sub = "";
          if (S.rank === "cities") {
            var many = C.filter(inFrame).length > 1, n = N3[r.p.reg];
            sub = "<span class=\"cc\">" + esc(many ? ccName(r.p.cc) : (n ? n.name : "")) + "</span>";
          }
          return "<td class=\"nm\">" + esc(v) + sub + "</td>";
        }
        if (c[0] === "buy" || c[0] === "rent") return "<td class=\"cls\"><i class=\"" + bigCls(cls(v)) + "\"></i> " + fmtM2(v) + "</td>";
        if (c[0] === "years") return "<td class=\"cls\"><i class=\"" + bigCls(clsFor("years", v)) + "\"></i> " + (v === null ? "—" : v.toFixed(1)) + "</td>";
        if (c[0] === "share") return "<td class=\"cls\"><i class=\"" + bigCls(clsFor("share", v)) + "\"></i> " + (v === null ? "—" : Math.round(v)) + "</td>";
        if (c[0] === "rate") return "<td>" + (v === null ? "—" : v.toFixed(2)) + "</td>";
        if (c[0] === "rentp") return "<td>" + (v === null ? "—" : v.toFixed(2)) + "</td>";
        return "<td>" + fmtInt(v) + "</td>";
      }).join("") + "<td><button type=\"button\" class=\"rowbtn" + (inCmp ? " on" : "") + "\" data-cmp=\"" + esc(id) + "\" title=\"" + (inCmp ? "Remove from the comparison" : "Add to the comparison") + "\">" + (inCmp ? "✓" : "+") + "</button></td></tr>";
    }).join("");
    var note = rr.rows.length + " of " + rr.total + " " + (S.rank === "countries" ? "countries" : fr().units + " of 100,000 people or more") +
      (S.want ? " where " + S.want + " m² are within reach" : "") + (S.coast && S.rank === "cities" ? ", coastal only" : "") +
      ". " + (mine() ? "On your income of €" + fmtInt(incEUR()) + " a month." : "Each on its own average income.") +
      " " + fr().label + " only: the two layers use different income definitions and do not belong in one ranking." +
      (S.rank === "countries" ? " Country values are population-weighted means of " + fr().units + "." : " Click a row to open the place on the map.");
    $("ranknote").textContent = note;
  }
  $("rankhead").addEventListener("click", function (e) {
    var th = e.target.closest("th[data-sort]"); if (!th) return;
    var k = th.getAttribute("data-sort");
    if (S.sort === k) S.dir = S.dir === "asc" ? "desc" : "asc";
    else { S.sort = k; S.dir = /^(name|price|rentp|rate|years|share|val|rnt)$/.test(k) ? "asc" : "desc"; }
    drawRank(); syncURL();
  });
  $("rankbody").addEventListener("click", function (e) {
    var b = e.target.closest("[data-cmp]"); if (b) { toggleCmp(b.getAttribute("data-cmp")); return; }
    var tr = e.target.closest("tr[data-id]"); if (tr) { select(tr.getAttribute("data-id"), true); $("p-map").scrollIntoView({ behavior: "smooth", block: "start" }); }
  });

  // ======================================================================
  // рисунок 3: население по классам и степени урбанизации
  // ======================================================================
  function drawHist(id, m) {
    var svg = $(id); svg.innerHTML = "";
    var W = 520, H = 300, L0 = 40, R0 = 10, T0 = 26, B0 = 40, total = DATA.popTotal / 1e6;
    var labels = ["<50", "50–75", "76–100", "101–150", ">150", "no data"];
    var pw = (W - L0 - R0) / 6, maxPct = 0;
    m.forEach(function (row) { var s = row.reduce(function (a, b) { return a + b; }, 0) / total * 100; if (s > maxPct) maxPct = s; });
    var yMax = Math.ceil(maxPct / 10) * 10 || 10;
    function y(pct) { return T0 + (H - T0 - B0) * (1 - pct / yMax); }
    for (var g = 0; g <= yMax; g += 10) {
      svg.appendChild(svgel("line", { x1: L0, x2: W - R0, y1: y(g), y2: y(g) }));
      var t = svgel("text", { x: L0 - 6, y: y(g) + 3.5, "text-anchor": "end" }); t.textContent = g + " %"; svg.appendChild(t);
    }
    m.forEach(function (row, i) {
      var x = L0 + i * pw + pw * 0.16, w = pw * 0.68, acc = 0;
      var order = [0, 1, 2, 3], klass = ["d1", "d2", "d3", "d0"];
      order.forEach(function (j) {
        var pct = row[j] / total * 100; if (!pct) return;
        var r = svgel("rect", { x: x, y: y(acc + pct), width: w, height: y(acc) - y(acc + pct), "class": klass[j] });
        var tt = svgel("title"); tt.textContent = ["cities", "towns and suburbs", "rural", "not classified"][j] + ": " + pct.toFixed(1) + " % of population (" + row[j].toFixed(1) + " M)";
        r.appendChild(tt); svg.appendChild(r); acc += pct;
      });
      var v = svgel("text", { x: x + w / 2, y: y(acc) - 6, "text-anchor": "middle", "class": "v" }); v.textContent = acc.toFixed(0) + " %"; svg.appendChild(v);
      var lb = svgel("text", { x: x + w / 2, y: H - B0 + 16, "text-anchor": "middle" }); lb.textContent = labels[i]; svg.appendChild(lb);
    });
    var ax = svgel("text", { x: W / 2, y: H - 6, "text-anchor": "middle" }); ax.textContent = "affordable square metres on a third of the local average income"; svg.appendChild(ax);
  }
  drawHist("hist-sale", DATA.hist.sale); drawHist("hist-rent", DATA.hist.rent);

  // ======================================================================
  // поделиться, картинка, CSV, печать
  // ======================================================================
  function flash(btn, msg) {
    var t = el("div", { "class": "copied", role: "status" }, esc(msg));
    document.body.appendChild(t);
    var r = btn.getBoundingClientRect(), w = t.offsetWidth, h = t.offsetHeight;
    function clamp(v, max) { return Math.max(8, Math.min(v, max - 8)); }
    var top = r.bottom + 8 + h > window.innerHeight ? r.top - h - 8 : r.bottom + 8;
    t.style.left = clamp(r.right - w, window.innerWidth - w) + "px"; t.style.top = clamp(top, window.innerHeight - h) + "px";
    setTimeout(function () { t.classList.add("in"); }, 16);
    setTimeout(function () { t.classList.remove("in"); setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 260); }, 1800);
  }
  var TICK = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="m5 12.5 4.5 4.5L19 7"/></svg>';
  function done(btn, msg, keepLabel) {
    var icon = btn.classList.contains("ibtn"), label = btn.innerHTML, title = btn.title;
    btn.innerHTML = icon ? TICK : msg; btn.classList.add("done"); if (icon) btn.title = msg; flash(btn, msg);
    setTimeout(function () { btn.innerHTML = label; btn.title = title; btn.classList.remove("done"); }, 2400);
  }
  Array.prototype.forEach.call(document.querySelectorAll("[data-share]"), function (btn) {
    btn.addEventListener("click", function () {
      var url = shareURL(); syncURL();
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(function () { done(btn, "Link copied"); }, function () { done(btn, "Address bar holds the link"); });
      } else done(btn, "Address bar holds the link");
    });
  });
  Array.prototype.forEach.call(document.querySelectorAll(".pactions"), function (box) {
    box.addEventListener("click", function (e) { if (e.target.closest(".ibtn")) { e.preventDefault(); e.stopPropagation(); } });
  });

  function gvar(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
  function legendRows() {
    var rows = [
      ["Income", mine() ? "€" + fmtInt(incEUR()) + " net a month" + (S.cur !== "EUR" ? " (" + fmtInt(S.inc) + " " + S.cur + ")" : "") + ", household of " + S.adults + " adult" + (S.adults > 1 ? "s" : "") + (S.kids ? " and " + S.kids + " child" + (S.kids > 1 ? "ren" : "") : "") : "the average local income of each place"],
      ["Terms", shareText() + " of income for housing, " + S.term + "-year mortgage at " + rateNote() + ", deposit " + S.dep + " %"],
      ["Map", modeText() + (S.want && S.mode !== "years" && S.mode !== "share" ? "; places where " + S.want + " m² are out of reach are greyed" : "")],
      // Источник — от кадра: экспорт американского рейтинга не должен
      // подписываться европейской статьёй. И контуры здесь Natural Earth:
      // границы GISCO были сняты именно из-за запрета коммерческого
      // использования, и ссылаться на них в выгрузке нельзя тем более.
      ["Source", (m2Here()
        ? "Sielker & Banabak 2026, Journal of Maps; ESPON HOUSE4ALL feature service, 14 Sep 2026"
        : "US Census Bureau, American Community Survey 2020-2024 (public domain); Freddie Mac PMMS 2024") +
        "; outlines Natural Earth, public domain"]
    ];
    return rows;
  }
  function inlineStyles(src, clone) {
    var props = ["fill", "fill-opacity", "stroke", "stroke-width", "stroke-opacity", "opacity", "font-family", "font-size", "font-weight", "text-anchor"];
    var a = src.querySelectorAll("*"), b = clone.querySelectorAll("*");
    for (var i = 0; i < a.length; i++) {
      var cs = getComputedStyle(a[i]), css = "";
      for (var j = 0; j < props.length; j++) { var v = cs.getPropertyValue(props[j]); if (v) css += props[j] + ":" + v + ";"; }
      b[i].setAttribute("style", css); b[i].removeAttribute("class");
    }
  }
  function mapImage() {
    var clone = mapEl.cloneNode(true);
    inlineStyles(mapEl, clone);
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg"); clone.setAttribute("width", GF.w); clone.setAttribute("height", GF.h);
    var img = new Image();
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(clone));
    return img.decode ? img.decode().then(function () { return img; }) : new Promise(function (ok) { img.onload = function () { ok(img); }; });
  }
  function wrapText(ctx, text, x, y, maxW, lh) {
    var words = text.split(" "), line = "", used = 0;
    for (var i = 0; i < words.length; i++) {
      var probe = line ? line + " " + words[i] : words[i];
      if (ctx.measureText(probe).width > maxW && line) { ctx.fillText(line, x, y + used * lh); used++; line = words[i]; } else line = probe;
    }
    if (line) { ctx.fillText(line, x, y + used * lh); used++; }
    return used * lh;
  }
  var PNG_W = 1400, PAD = 52, PNG_SCALE = 2;
  var head = "'Space Grotesk', system-ui, sans-serif", body = "'Inter', system-ui, sans-serif", mono = "'JetBrains Mono', ui-monospace, Menlo, monospace";
  function legendBlock(ctx, y, rows, inner) {
    var labelW = 110, textW = inner - labelW;
    ctx.strokeStyle = gvar("--hair"); ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(PAD, y); ctx.lineTo(PNG_W - PAD, y); ctx.stroke();
    y += 12;
    rows.forEach(function (r) {
      ctx.fillStyle = gvar("--ink-3"); ctx.font = "600 12px " + mono; ctx.fillText(r[0].toUpperCase(), PAD, y + 14);
      ctx.fillStyle = gvar("--ink-2"); ctx.font = "15px " + body;
      y += wrapText(ctx, r[1], PAD + labelW, y + 14, textW, 24) + 12;
    });
    y += 14; ctx.fillStyle = gvar("--ink-3"); ctx.font = "12px " + mono; ctx.fillText(shareURL().replace(/^https?:\/\//, ""), PAD, y);
    return y + 8;
  }
  function measureLegend(rows, inner) {
    var probe = document.createElement("canvas").getContext("2d"); probe.font = "15px " + body;
    var textW = inner - 110;
    return rows.reduce(function (sum, r) {
      var lines = 1, line = "", words = r[1].split(" ");
      for (var i = 0; i < words.length; i++) { var pl = line ? line + " " + words[i] : words[i]; if (probe.measureText(pl).width > textW && line) { lines++; line = words[i]; } else line = pl; }
      return sum + lines * 24 + 12;
    }, 12 + 14 + 8 + 12);
  }
  function buildMapPNG() {
    return mapImage().then(function (img) {
      var inner = PNG_W - PAD * 2, mapH = Math.round(inner * GF.h / GF.w), rows = legendRows();
      var legendH = 0, lgLines = modeLabels();
      var height = PAD + 44 + 28 + 20 + mapH + 16 + 22 + 20 + measureLegend(rows, inner) + PAD;
      var cv = document.createElement("canvas"); cv.width = PNG_W * PNG_SCALE; cv.height = height * PNG_SCALE;
      var ctx = cv.getContext("2d"); ctx.scale(PNG_SCALE, PNG_SCALE); ctx.textBaseline = "alphabetic";
      ctx.fillStyle = gvar("--bg"); ctx.fillRect(0, 0, PNG_W, height);
      var y = PAD + 36;
      ctx.fillStyle = gvar("--ink"); ctx.font = "600 34px " + head; ctx.fillText({{js:title}}, PAD, y);
      y += 28; ctx.fillStyle = gvar("--ink-2"); ctx.font = "16px " + body;
      ctx.fillText(modeText().charAt(0).toUpperCase() + modeText().slice(1) + (mine() ? " on €" + fmtInt(incEUR()) + " net a month" : " on the average local income") + ", by country and town", PAD, y);
      y += 20; ctx.drawImage(img, PAD, y, inner, mapH); y += mapH + 16;
      var x = PAD; ctx.font = "12px " + mono;
      lgLines.forEach(function (t, i) {
        var ci = MODES[S.mode].inv ? 4 - i : i;
        ctx.fillStyle = gvar(S.mode === "diff" ? "--d" + (i + 1) : "--m" + (ci + 1)); ctx.fillRect(x, y, 16, 12);
        ctx.fillStyle = gvar("--ink-2"); ctx.fillText(t, x + 22, y + 11); x += 22 + ctx.measureText(t).width + 24;
      });
      ctx.fillStyle = gvar("--nd") || "#888"; ctx.strokeStyle = gvar("--hair"); ctx.fillRect(x, y, 16, 12); ctx.strokeRect(x + .5, y + .5, 15, 11);
      ctx.fillStyle = gvar("--ink-2"); ctx.fillText("no data", x + 22, y + 11);
      y += 22 + 20;
      legendBlock(ctx, y, rows, inner);
      return new Promise(function (ok) { cv.toBlob(ok, "image/png"); });
    });
  }
  function buildCmpPNG() {
    var cr = cmpRows(); if (!cr.P.length) return Promise.reject(new Error("empty"));
    var inner = PNG_W - PAD * 2, rows = legendRows(), colW = Math.min(240, (inner - 420) / cr.P.length), labelW = inner - colW * cr.P.length;
    var nrows = cr.groups.reduce(function (s, g) { return s + g[1].length + 1; }, 0);
    var height = PAD + 44 + 28 + 24 + 40 + nrows * 28 + 30 + measureLegend(rows, inner) + PAD;
    var cv = document.createElement("canvas"); cv.width = PNG_W * PNG_SCALE; cv.height = height * PNG_SCALE;
    var ctx = cv.getContext("2d"); ctx.scale(PNG_SCALE, PNG_SCALE); ctx.textBaseline = "alphabetic";
    ctx.fillStyle = gvar("--bg"); ctx.fillRect(0, 0, PNG_W, height);
    var y = PAD + 36;
    ctx.fillStyle = gvar("--ink"); ctx.font = "600 34px " + head; ctx.fillText({{js:title}}, PAD, y);
    y += 28; ctx.fillStyle = gvar("--ink-2"); ctx.font = "16px " + body; ctx.fillText("Side by side: " + cr.P.map(function (p) { return p.name; }).join(", "), PAD, y);
    y += 24;
    ctx.font = "600 15px " + head; ctx.fillStyle = gvar("--ink"); ctx.textAlign = "right";
    cr.P.forEach(function (p, i) { ctx.fillText(p.name, PAD + labelW + colW * (i + 1), y + 18); });
    ctx.font = "12px " + mono; ctx.fillStyle = gvar("--ink-3");
    cr.P.forEach(function (p, i) { ctx.fillText(ccName(p.cc), PAD + labelW + colW * (i + 1), y + 34); });
    ctx.textAlign = "left"; y += 40;
    cr.groups.forEach(function (g) {
      y += 28; ctx.fillStyle = gvar("--ink-3"); ctx.font = "600 11px " + mono; ctx.fillText(g[0].toUpperCase(), PAD, y - 8);
      ctx.strokeStyle = gvar("--hair"); ctx.beginPath(); ctx.moveTo(PAD, y - 2); ctx.lineTo(PNG_W - PAD, y - 2); ctx.stroke();
      g[1].forEach(function (r) {
        y += 28; ctx.fillStyle = gvar("--ink-2"); ctx.font = "14px " + body; ctx.fillText(r.label, PAD, y - 8);
        var bestIdx = -1, bv = null;
        if (r.best && cr.P.length > 1) r.vals.forEach(function (v, i) { if (v === null) return; if (bv === null || (r.best === "max" ? v > bv : v < bv)) { bv = v; bestIdx = i; } });
        ctx.textAlign = "right"; ctx.font = "15px " + mono;
        r.vals.forEach(function (v, i) { ctx.fillStyle = i === bestIdx ? gvar("--ok") : gvar("--ink"); ctx.fillText(fmtCell(r, v), PAD + labelW + colW * (i + 1), y - 8); });
        ctx.textAlign = "left";
        ctx.strokeStyle = gvar("--hair-soft"); ctx.beginPath(); ctx.moveTo(PAD, y); ctx.lineTo(PNG_W - PAD, y); ctx.stroke();
      });
    });
    y += 30; legendBlock(ctx, y, rows, inner);
    return new Promise(function (ok) { cv.toBlob(ok, "image/png"); });
  }
  function savePNG(blob, name, btn) {
    var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name; a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000); done(btn, "PNG saved");
  }
  function pngAction(sel, dl) {
    Array.prototype.forEach.call(document.querySelectorAll(sel), function (btn) {
      btn.addEventListener("click", function () {
        var which = btn.getAttribute(dl ? "data-png-dl" : "data-png");
        var build = which === "map" ? buildMapPNG : buildCmpPNG, name = which === "map" ? "housing-map.png" : "housing-comparison.png";
        build().then(function (blob) {
          if (!dl && window.ClipboardItem && navigator.clipboard && navigator.clipboard.write) {
            navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]).then(function () { done(btn, "PNG copied"); }, function () { savePNG(blob, name, btn); });
          } else savePNG(blob, name, btn);
        }, function () { flash(btn, which === "cmp" ? "Add a place to compare first" : "Could not build the image"); });
      });
    });
  }
  pngAction("[data-png]", false); pngAction("[data-png-dl]", true);

  function csvSettings() {
    return legendRows().map(function (r) { return "# " + r[0] + ": " + r[1]; }).concat(["# " + shareURL()]).join("\n") + "\n";
  }
  function csvCell(v) { v = v === null || v === undefined ? "" : String(v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }
  function saveText(text, name, btn) {
    var a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text], { type: "text/csv;charset=utf-8" })); a.download = name; a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000); done(btn, "CSV saved");
  }
  Array.prototype.forEach.call(document.querySelectorAll("[data-csv]"), function (btn) {
    btn.addEventListener("click", function () {
      var which = btn.getAttribute("data-csv"), out = csvSettings();
      if (which === "rank") {
        var cols = rankCols(), rr = rankRows();
        out += "rank," + cols.map(function (c) { return csvCell(c[1]); }).join(",") + (S.rank === "cities" ? ",country" : "") + "\n";
        rr.rows.forEach(function (r, i) {
          out += (i + 1) + "," + cols.map(function (c) { var v = r[c[0]]; return csvCell(typeof v === "number" ? Math.round(v * 100) / 100 : v); }).join(",") + (S.rank === "cities" ? "," + csvCell(ccName(r.p.cc)) : "") + "\n";
        });
      } else {
        var cr = cmpRows(); if (!cr.P.length) { flash(btn, "Add a place to compare first"); return; }
        out += "metric," + cr.P.map(function (p) { return csvCell(p.name + " (" + ccName(p.cc) + ")"); }).join(",") + "\n";
        cr.groups.forEach(function (g) { g[1].forEach(function (r) { out += csvCell(r.label) + "," + r.vals.map(function (v) { return csvCell(v === null ? "" : Math.round(v * 100) / 100); }).join(",") + "\n"; }); });
      }
      saveText(out, which === "rank" ? "housing-" + S.rank + ".csv" : "housing-comparison.csv", btn);
    });
  });

  // печать: один блок на лист, светлая палитра
  var printedTheme = null;
  function beforePrint(part) {
    $("printurl").textContent = (location.origin + location.pathname).replace(/^https?:\/\//, "");
    // Органы управления на лист не идут, поэтому настройка и режим карты
    // печатаются словами в шапке — иначе распечатку не прочесть без экрана.
    $("printsetup").textContent = $("setupline").textContent +
      (part === "map" ? " · map: " + modeText() : "") +
      (part === "rank" ? " · " + $("ranknote").textContent : "");
    var root = document.documentElement;
    printedTheme = root.getAttribute("data-theme");
    if (printedTheme !== "light") root.setAttribute("data-theme", "light");
    root.setAttribute("data-print", part);
    var wide = part === "rank", pw = wide ? 1033 : 710, ph = (wide ? 710 : 1033) - 80;
    var node = $("p-" + part), sc = 1, w = pw;
    if (part === "rank") { w = $("ranktable").scrollWidth + 44; sc = Math.min(1, pw / w); }
    else { var prev = node.style.width; node.style.width = pw + "px"; var h = node.getBoundingClientRect().height; node.style.width = prev; if (part !== "cmp") sc = Math.min(1, ph / h); }
    root.style.setProperty("--pscale", sc.toFixed(4)); root.style.setProperty("--pwidth", Math.round(w) + "px");
  }
  function afterPrint() {
    var root = document.documentElement;
    root.removeAttribute("data-print"); root.style.removeProperty("--pscale"); root.style.removeProperty("--pwidth");
    if (printedTheme && printedTheme !== "light") root.setAttribute("data-theme", printedTheme);
    printedTheme = null;
  }
  window.addEventListener("afterprint", afterPrint);
  Array.prototype.forEach.call(document.querySelectorAll("[data-print]"), function (btn) {
    btn.addEventListener("click", function () {
      beforePrint(btn.getAttribute("data-print")); window.print();
      setTimeout(function () { if (document.documentElement.hasAttribute("data-print")) afterPrint(); }, 800);
    });
  });

  // ======================================================================
  function update() { paintMap(); drawCard(); drawCmp(); drawRank(); drawMove(); setupLine(); }
  document.addEventListener("themechange", function () { paintMap(); });
  readURL();
  buildRegButtons();
  syncControls();
  syncMoveInputs();
  update();
  var first = placeById(S.sel);
  if (first && first.kind !== "cc") flyTo(first);
  drawMarks();
})();
