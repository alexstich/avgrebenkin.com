/* Население мира, −10 000 … 2023. Всё, что видно, считается из одного вшитого
   датасета (src/data.json, см. data.py). build.py кладёт его в общий для всех
   языков data.js, который грузится с defer и кэшируется; кроме него страница
   ничего не запрашивает. Слова, которые рисует скрипт, — из каталога строк (T);
   числа и годы форматирует Intl по языку страницы.
   Запуск — после первой отрисовки: сначала читатель видит текст, потом глобусы. */
(function () {
  'use strict';
  function start() { requestAnimationFrame(function () { setTimeout(boot, 0); }); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();

  function boot() {
  var POP = window.POP_DATA;
  /* данные не пришли — показываем страницу как без скриптов, а не пустые сцены */
  if (!POP) { document.documentElement.classList.remove('js'); return; }
  var T = {{i18n}};
  var P = POP, Y = P.years, N = Y.length, END = 2023, PRESENT = 2030, D2R = Math.PI / 180;
  var root = document.documentElement;
  var CODES = Object.keys(P.pop);
  var LANDCODES = Object.keys(P.shapes);
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── числа ─────────────────────────────────────────────────────── */
  function seek(year) {
    if (year <= Y[0]) return [0, 0, 0];
    if (year >= Y[N - 1]) return [N - 1, N - 1, 0];
    var lo = 0, hi = N - 1;
    while (hi - lo > 1) { var m = (lo + hi) >> 1; if (Y[m] <= year) lo = m; else hi = m; }
    return [lo, hi, (year - Y[lo]) / (Y[hi] - Y[lo])];
  }
  function interp(arr, year) {
    var s = seek(year), a = arr[s[0]], b = arr[s[1]], f = s[2];
    if (s[0] === s[1]) return a;
    return (a > 0 && b > 0) ? a * Math.pow(b / a, f) : a + (b - a) * f;
  }
  function worldAt(y) { return interp(P.world, y); }
  function popAt(c, y) { return interp(P.pop[c], y); }
  var LANG = root.getAttribute('lang') || 'en';
  function nf(o) { try { return new Intl.NumberFormat(LANG, o); } catch (e) { return new Intl.NumberFormat('en', o); } }
  var NF_LONG = nf({ notation: 'compact', compactDisplay: 'long', maximumSignificantDigits: 3 });
  var NF_SHORT = nf({ notation: 'compact', compactDisplay: 'short', maximumSignificantDigits: 3 });
  var NF_INT = nf({ maximumFractionDigits: 0 });
  /* знак процента и пробел перед ним — по правилам языка: 12.3%, 12,3 %, %12,3 */
  var NF_PCT = [null, 1, 2].map(function (d) { return d && nf({ style: 'percent', minimumFractionDigits: d, maximumFractionDigits: d }); });
  var NF_Y = nf({ maximumFractionDigits: 0, useGrouping: false });
  function tpl(s, o) { return String(s).replace(/\{(\w+)\}/g, function (m, k) { return o[k] != null ? o[k] : m; }); }
  function fmtPop(v) { return NF_LONG.format(v); }
  function fmtShort(v) { return NF_SHORT.format(v); }
  function fmtInt(v) { return NF_INT.format(Math.round(v)); }
  function fmtDec(v, d) { return nf({ minimumFractionDigits: d, maximumFractionDigits: d }).format(v); }
  function fmtYear(y) {
    y = Math.round(y);
    if (y < 0) return tpl(T.bce, { n: (-y >= 10000 ? NF_INT : NF_Y).format(-y) });
    if (y === 0) return T.ce1;
    if (y < 1000) return tpl(T.ce, { n: NF_Y.format(y) });
    return NF_Y.format(y);
  }
  /* Имя страны на языке страницы — из самого браузера (Intl.DisplayNames по коду
     ISO), чтобы не везти тринадцать словарей; без поддержки — английское. */
  var DN = null; try { DN = new Intl.DisplayNames([LANG], { type: 'region' }); } catch (e) {}
  function cname(c) { var a2 = P.names[c][5]; try { return (DN && a2 && DN.of(a2)) || P.names[c][0]; } catch (e) { return P.names[c][0]; } }

  var SOURCES = [
    { key: 'hyde', to: 1800, name: T.hydeName, kind: T.kindHyde, cite: T.citeHyde },
    { key: 'gap', to: 1950, name: T.gapName, kind: T.kindGap, cite: T.citeGap },
    { key: 'un', to: 99999, name: T.unName, kind: T.kindUn, cite: T.citeUn }
  ];
  function sourceAt(y) { for (var i = 0; i < SOURCES.length; i++) if (y < SOURCES[i].to) return SOURCES[i]; return SOURCES[2]; }

  /* ── темп: доля круга u → год ──────────────────────────────────── */
  var SET = { start: -5000, mode: 'doubling', dur: 40 };
  var maps = {};
  function makeMap(y0, y1, mode) {
    var key = y0 + '|' + y1 + '|' + mode;
    if (maps[key]) return maps[key];
    var m;
    if (mode === 'linear') {
      m = { toYear: function (u) { return y0 + u * (y1 - y0); }, toU: function (y) { return (y - y0) / (y1 - y0); } };
    } else if (mode === 'log') {
      var A = Math.log(PRESENT - y0), B = Math.log(PRESENT - y1);
      m = { toYear: function (u) { return PRESENT - Math.exp(A + (B - A) * u); },
            toU: function (y) { return (Math.log(PRESENT - y) - A) / (B - A); } };
    } else {
      var lg = makeMap(y0, y1, 'log'), S = 1600, ys = [], gs = [], run = 0, i;
      for (i = 0; i <= S; i++) {
        var y = lg.toYear(i / S); ys.push(y);
        run = Math.max(run, worldAt(y)); gs.push(Math.log(run));
      }
      var g0 = gs[0], span = gs[S] - g0 || 1, eps = 0.05;
      for (i = 0; i <= S; i++) gs[i] = ((gs[i] - g0) / span + eps * i / S) / (1 + eps);
      var find = function (arr, v) { var lo = 0, hi = arr.length - 1; while (hi - lo > 1) { var k = (lo + hi) >> 1; if (arr[k] <= v) lo = k; else hi = k; } return lo; };
      m = { toYear: function (u) { if (u <= 0) return ys[0]; if (u >= 1) return ys[S]; var k = find(gs, u), f = (u - gs[k]) / (gs[k + 1] - gs[k] || 1); return ys[k] + (ys[k + 1] - ys[k]) * f; },
            toU: function (y) { if (y <= ys[0]) return 0; if (y >= ys[S]) return 1; var k = find(ys, y), f = (y - ys[k]) / (ys[k + 1] - ys[k] || 1); return gs[k] + (gs[k + 1] - gs[k]) * f; } };
    }
    maps[key] = m;
    return m;
  }

  /* ── геометрия: всё переводим в точки на единичной сфере один раз ── */
  function xyz(lon, lat, out, k) {
    var l = lon * D2R, p = lat * D2R, c = Math.cos(p);
    out[k] = c * Math.sin(l); out[k + 1] = Math.sin(p); out[k + 2] = c * Math.cos(l);
  }
  var GEO = {};
  LANDCODES.forEach(function (c) {
    var rings = [], bb = [180, 90, -180, -90];
    P.shapes[c].forEach(function (poly) {
      poly.forEach(function (r) {
        var n = r.length / 2, f = new Float32Array(n * 3);
        for (var i = 0; i < n; i++) {
          var lon = r[2 * i], lat = r[2 * i + 1];
          xyz(lon, lat, f, 3 * i);
          if (lon < bb[0]) bb[0] = lon; if (lat < bb[1]) bb[1] = lat; if (lon > bb[2]) bb[2] = lon; if (lat > bb[3]) bb[3] = lat;
        }
        rings.push({ xyz: f, ll: r });
      });
    });
    GEO[c] = { rings: rings, bb: bb };
  });
  var DOTS = {}, CEN = {}, AREA = {}, REGION = {}, NAME = {};
  CODES.forEach(function (c) {
    var d = P.dots[c] || [], n = d.length / 2, f = new Float32Array(n * 3);
    for (var i = 0; i < n; i++) xyz(d[2 * i], d[2 * i + 1], f, 3 * i);
    DOTS[c] = f;
    var nm = P.names[c];
    var ce = new Float32Array(3); xyz(nm[2], nm[1], ce, 0); CEN[c] = ce;
    AREA[c] = nm[3] || 1; REGION[c] = nm[4]; NAME[c] = cname(c);
  });
  CODES.sort(function (a, b) { return P.pop[b][N - 1] - P.pop[a][N - 1]; });
  var GRAT = [];
  (function () {
    var lon, lat, pts, f, i;
    for (lon = -180; lon < 180; lon += 30) { pts = []; for (lat = -90; lat <= 90; lat += 3) pts.push(lon, lat); GRAT.push(pts); }
    for (lat = -60; lat <= 60; lat += 30) { pts = []; for (lon = -180; lon <= 180; lon += 3) pts.push(lon, lat); GRAT.push(pts); }
    GRAT = GRAT.map(function (r) { f = new Float32Array(r.length / 2 * 3); for (i = 0; i < r.length / 2; i++) xyz(r[2 * i], r[2 * i + 1], f, 3 * i); return f; });
  })();

  function inRing(x, y, r) {
    var ins = false, n = r.length / 2;
    for (var i = 0, j = n - 1; i < n; j = i++) {
      var xi = r[2 * i], yi = r[2 * i + 1], xj = r[2 * j], yj = r[2 * j + 1];
      if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) ins = !ins;
    }
    return ins;
  }
  function countryAt(lon, lat) {
    for (var k = 0; k < LANDCODES.length; k++) {
      var c = LANDCODES[k], g = GEO[c], b = g.bb;
      if (lon < b[0] || lon > b[2] || lat < b[1] || lat > b[3]) continue;
      var ins = false;
      for (var i = 0; i < g.rings.length; i++) if (inRing(lon, lat, g.rings[i].ll)) ins = !ins;
      if (ins) return c;
    }
    return null;
  }

  /* ── глобус ────────────────────────────────────────────────────── */
  function Globe(cv, o) {
    o = o || {};
    this.cv = cv; this.ctx = cv.getContext('2d');
    this.a = o.a != null ? o.a : -60; this.b = o.b != null ? o.b : 22;
    this.spin = o.spin != null ? o.spin : 5; this.scale = o.scale || 0.42;
    this.target = null; this.drag = null; this.onclick = null; this.onhover = null;
    this.resize();
    var self = this;
    if (o.interactive !== false) {
      cv.addEventListener('pointerdown', function (e) {
        self.drag = { x: e.clientX, y: e.clientY, a: self.a, b: self.b, moved: 0 };
        cv.setPointerCapture(e.pointerId); cv.classList.add('drag'); self.target = null;
      });
      cv.addEventListener('pointermove', function (e) {
        if (self.drag) {
          var dx = e.clientX - self.drag.x, dy = e.clientY - self.drag.y, k = 57 / (self.R / self.dpr);
          self.drag.moved = Math.max(self.drag.moved, Math.abs(dx) + Math.abs(dy));
          self.a = self.drag.a + dx * k; self.b = Math.max(-80, Math.min(80, self.drag.b + dy * k));
        } else if (self.onhover) self.onhover(e);
      });
      var up = function (e) {
        if (!self.drag) return;
        var click = self.drag.moved < 5; self.drag = null; cv.classList.remove('drag');
        if (click && self.onclick) self.onclick(e);
      };
      cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
      cv.addEventListener('pointerleave', function (e) { if (!self.drag && self.onhover) self.onhover(null); });
    }
  }
  Globe.prototype.resize = function () {
    var r = this.cv.getBoundingClientRect(), dpr = Math.min(2, window.devicePixelRatio || 1);
    var w = Math.max(10, Math.round(r.width * dpr)), h = Math.max(10, Math.round(r.height * dpr));
    if (this.cv.width !== w || this.cv.height !== h) { this.cv.width = w; this.cv.height = h; }
    this.dpr = dpr; this.W = w; this.H = h; this.cx = w / 2; this.cy = h / 2;
    this.R = Math.min(w, h) * this.scale;
  };
  Globe.prototype.step = function (dt) {
    if (this.drag) return;
    if (this.target) {
      var da = ((this.target[0] - this.a + 540) % 360) - 180, db = this.target[1] - this.b, k = Math.min(1, dt * 3.5);
      this.a += da * k; this.b += db * k;
      if (Math.abs(da) < 0.05 && Math.abs(db) < 0.05) this.target = null;
    } else if (!reduce) this.a += this.spin * dt;
  };
  Globe.prototype.setup = function () {
    var a = this.a * D2R, b = this.b * D2R;
    this.ca = Math.cos(a); this.sa = Math.sin(a); this.cb = Math.cos(b); this.sb = Math.sin(b);
  };
  /* проекция: пишет x, y, z в out */
  Globe.prototype.p = function (x, y, z, out) {
    var X1 = x * this.ca + z * this.sa, Z1 = z * this.ca - x * this.sa;
    out[0] = this.cx + this.R * X1;
    out[1] = this.cy - this.R * (y * this.cb - Z1 * this.sb);
    out[2] = y * this.sb + Z1 * this.cb;
  };
  Globe.prototype.inv = function (clientX, clientY) {
    var r = this.cv.getBoundingClientRect();
    var x = ((clientX - r.left) * this.dpr - this.cx) / this.R, y = -((clientY - r.top) * this.dpr - this.cy) / this.R;
    var r2 = x * x + y * y; if (r2 > 1) return null;
    var z = Math.sqrt(1 - r2);
    var Y1 = y * this.cb + z * this.sb, Z1 = -y * this.sb + z * this.cb;
    var X = x * this.ca - Z1 * this.sa, Z = x * this.sa + Z1 * this.ca;
    return [Math.atan2(X, Z) / D2R, Math.asin(Math.max(-1, Math.min(1, Y1))) / D2R];
  };
  Globe.prototype.sphere = function (c1, c2, glow) {
    var g = this.ctx, R = this.R;
    if (glow) {
      var hg = g.createRadialGradient(this.cx, this.cy, R * 0.95, this.cx, this.cy, R * 1.25);
      hg.addColorStop(0, glow); hg.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = hg; g.beginPath(); g.arc(this.cx, this.cy, R * 1.25, 0, 7); g.fill();
    }
    var gr = g.createRadialGradient(this.cx - R * 0.35, this.cy - R * 0.4, R * 0.1, this.cx, this.cy, R);
    gr.addColorStop(0, c1); gr.addColorStop(1, c2);
    g.fillStyle = gr; g.beginPath(); g.arc(this.cx, this.cy, R, 0, 7); g.fill();
  };
  var TMP = [0, 0, 0];
  /* путь страны; невидимые точки прижимаются к краю диска, чтобы заливка не рвалась */
  Globe.prototype.countryPath = function (c) {
    var g = this.ctx, rings = GEO[c].rings, any = false;
    g.beginPath();
    for (var i = 0; i < rings.length; i++) {
      var f = rings[i].xyz, n = f.length / 3, vis = false, j;
      for (j = 0; j < n; j++) { this.p(f[3 * j], f[3 * j + 1], f[3 * j + 2], TMP); if (TMP[2] > 0) { vis = true; break; } }
      if (!vis) continue;
      any = true;
      for (j = 0; j < n; j++) {
        this.p(f[3 * j], f[3 * j + 1], f[3 * j + 2], TMP);
        var x = TMP[0], y = TMP[1];
        if (TMP[2] < 0) { var dx = x - this.cx, dy = y - this.cy, L = Math.sqrt(dx * dx + dy * dy) || 1; x = this.cx + dx / L * this.R; y = this.cy + dy / L * this.R; }
        if (j === 0) g.moveTo(x, y); else g.lineTo(x, y);
      }
      g.closePath();
    }
    return any;
  };
  Globe.prototype.land = function (fill, stroke, lw, skip) {
    var g = this.ctx;
    g.lineWidth = (lw || 0.8) * this.dpr; g.lineJoin = 'round';
    for (var k = 0; k < LANDCODES.length; k++) {
      var c = LANDCODES[k];
      if (skip && skip[c]) continue;
      if (!this.countryPath(c)) continue;
      var fs = typeof fill === 'function' ? fill(c) : fill;
      if (fs) { g.fillStyle = fs; g.fill('evenodd'); }
      if (stroke) { g.strokeStyle = stroke; g.stroke(); }
    }
  };
  Globe.prototype.graticule = function (stroke) {
    var g = this.ctx; g.strokeStyle = stroke; g.lineWidth = this.dpr;
    for (var i = 0; i < GRAT.length; i++) {
      var f = GRAT[i], n = f.length / 3, pen = false;
      g.beginPath();
      for (var j = 0; j < n; j++) {
        this.p(f[3 * j], f[3 * j + 1], f[3 * j + 2], TMP);
        if (TMP[2] > 0) { if (pen) g.lineTo(TMP[0], TMP[1]); else g.moveTo(TMP[0], TMP[1]); pen = true; } else pen = false;
      }
      g.stroke();
    }
  };
  /* точки: одна = unit человек, последняя неполная — прозрачнее */
  Globe.prototype.dots = function (codes, year, color, size, unit, alphaMul) {
    var g = this.ctx, s = size * this.dpr, h = s / 2, total = 0;
    g.fillStyle = color;
    for (var k = 0; k < codes.length; k++) {
      var c = codes[k], f = DOTS[c], n = popAt(c, year) / unit, full = Math.floor(n), m = Math.min(Math.ceil(n), f.length / 3);
      total += n;
      for (var j = 0; j < m; j++) {
        this.p(f[3 * j], f[3 * j + 1], f[3 * j + 2], TMP);
        if (TMP[2] <= 0) continue;
        var a = (j < full ? 1 : n - full) * Math.min(1, 0.25 + TMP[2] * 1.6) * (alphaMul || 1);
        g.globalAlpha = a; g.fillRect(TMP[0] - h, TMP[1] - h, s, s);
      }
    }
    g.globalAlpha = 1;
    return total;
  };
  Globe.prototype.clear = function (bg) {
    var g = this.ctx; g.setTransform(1, 0, 0, 1, 0, 0);
    if (bg) { g.fillStyle = bg; g.fillRect(0, 0, this.W, this.H); } else g.clearRect(0, 0, this.W, this.H);
    this.setup();
  };

  /* ── палитра варианта из CSS ───────────────────────────────────── */
  function palette(el) {
    var cs = getComputedStyle(el), o = {};
    ['bg', 's1', 's2', 'land', 'line', 'dot', 'ink', 'mute', 'acc', 'star', 'r0', 'r1', 'r2', 'grat', 'sa', 'sb', 'ring', 'grid', 'band', 'est', 'teal', 'line2']
      .forEach(function (k) { o[k] = cs.getPropertyValue('--v-' + k).trim(); });
    ['hyde', 'gap', 'un'].forEach(function (k) { o[k] = cs.getPropertyValue('--s-' + k).trim(); });
    return o;
  }
  function hex(c) {
    c = c.replace('#', ''); if (c.length === 3) c = c.replace(/./g, '$&$&');
    return [parseInt(c.slice(0, 2), 16), parseInt(c.slice(2, 4), 16), parseInt(c.slice(4, 6), 16)];
  }
  function mix(a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
  function rgb(c, al) { return 'rgba(' + Math.round(c[0]) + ',' + Math.round(c[1]) + ',' + Math.round(c[2]) + ',' + (al == null ? 1 : al) + ')'; }

  /* ── плеер ─────────────────────────────────────────────────────── */
  var ICON_PLAY = '<svg viewBox="0 0 16 16"><path d="M4 2.5v11l9-5.5z"/></svg>';
  var ICON_PAUSE = '<svg viewBox="0 0 16 16"><path d="M3.5 2.5h3v11h-3zM9.5 2.5h3v11h-3z"/></svg>';
  function Player(box, o) {
    o = o || {};
    this.u = o.u0 || 0; this.playing = !reduce; this.hold = 0; this.mode = o.mode || null; this.range = o.range || null;
    var self = this;
    this.btn = document.createElement('button'); this.btn.type = 'button';
    this.slider = document.createElement('input'); this.slider.type = 'range'; this.slider.min = 0; this.slider.max = 1000; this.slider.step = 1;
    this.slider.setAttribute('aria-label', T.time);
    this.out = document.createElement('output');
    box.appendChild(this.btn); box.appendChild(this.slider); box.appendChild(this.out);
    this.btn.addEventListener('click', function () { self.playing = !self.playing; if (self.playing && self.u >= 1) self.u = 0; self.sync(); });
    this.slider.addEventListener('input', function () { self.playing = false; self.hold = 0; self.u = self.slider.value / 1000; self.sync(); });
    this.sync();
  }
  Player.prototype.span = function () { return this.range ? this.range() : [SET.start, END]; };
  Player.prototype.map = function () { var s = this.span(); return makeMap(s[0], s[1], this.mode || SET.mode); };
  Player.prototype.year = function () { return this.map().toYear(this.u); };
  Player.prototype.setYear = function (y) { this.u = Math.max(0, Math.min(1, this.map().toU(y))); this.sync(); };
  Player.prototype.step = function (dt) {
    if (!this.playing) return;
    if (this.hold > 0) { this.hold -= dt; if (this.hold <= 0) this.u = 0; }
    else { this.u += dt / SET.dur; if (this.u >= 1) { this.u = 1; this.hold = 2.5; } }
    this.sync();
  };
  Player.prototype.sync = function () {
    if (this.shown !== this.playing) {
      this.shown = this.playing;
      this.btn.innerHTML = this.playing ? ICON_PAUSE : ICON_PLAY;
      this.btn.setAttribute('aria-label', this.playing ? T.pause : T.play);
    }
    this.slider.value = Math.round(this.u * 1000);
    this.out.textContent = fmtYear(this.year());
  };

  function chipHTML(y, color) {
    var s = sourceAt(y), exact = Y.indexOf(Math.round(y)) !== -1;
    return '<i style="background:' + (color || 'currentColor') + '"></i>' + s.name + ' · ' + (exact ? T.dataPoint : T.interp);
  }

  /* ── общий цикл: рисуем только то, что на экране ───────────────── */
  var STAGES = [];
  function stage(el, tick, onResize) {
    var s = { el: el, tick: tick, visible: false, pal: null, onResize: onResize };
    STAGES.push(s);
    return s;
  }
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) { STAGES.forEach(function (s) { if (s.el === e.target) s.visible = e.isIntersecting; }); });
  }, { rootMargin: '80px' });
  var last = 0;
  function loop(ts) {
    var dt = last ? Math.min(0.1, (ts - last) / 1000) : 0; last = ts;
    STAGES.forEach(function (s) { if (s.visible) { if (!s.pal) s.pal = palette(s.el); s.tick(dt); } });
    requestAnimationFrame(loop);
  }


  /* ══ состояние страницы: вид, начало, темп, страна — живёт в адресе ══ */
  var VIEW = 'dots';
  SET.dur = 45;
  var CS = { c: 'ITA', f: 1500, t: 2023 };
  (function () {
    var q = new URLSearchParams(location.search);
    if (q.get('v') === 'density') VIEW = 'density';
    if (q.has('s') && [-10000, -5000, 0, 1800].indexOf(+q.get('s')) !== -1) SET.start = +q.get('s');
    if (['linear', 'log', 'doubling'].indexOf(q.get('p')) !== -1) SET.mode = q.get('p');
    if (q.get('c') && P.pop[q.get('c')]) CS.c = q.get('c');
    if (q.has('f')) CS.f = +q.get('f');
    if (q.has('t')) CS.t = +q.get('t');
  })();
  function shareURL() {
    return location.pathname + '?v=' + VIEW + '&s=' + SET.start + '&p=' + SET.mode + '&c=' + CS.c + '&f=' + CS.f + '&t=' + CS.t + location.hash;
  }
  var urlT;
  function syncURL() { clearTimeout(urlT); urlT = setTimeout(function () { history.replaceState(null, '', shareURL()); }, 250); }

  /* ── общий рисунок шара в двух видах ─────────────────────────── */
  var DLO = -1, DHI = 3; // 0,1 … 1000 человек на км²
  function dcol(p, d) {
    var t = (Math.log10(Math.max(d, 1e-3)) - DLO) / (DHI - DLO); t = Math.max(0, Math.min(1, t));
    var a = hex(p.r0), b = hex(p.r1), c = hex(p.r2);
    return t < 0.5 ? mix(a, b, t * 2) : mix(b, c, (t - 0.5) * 2);
  }
  var STARS = []; for (var si = 0; si < 160; si++) STARS.push([Math.random(), Math.random(), Math.random()]);
  function isLight() { return root.getAttribute('data-theme') === 'light'; }
  function drawView(G, p, y, o) {
    o = o || {};
    var g = G.ctx;
    if (o.stars && !isLight()) {
      g.fillStyle = p.star;
      STARS.forEach(function (st) { var s = G.dpr * (st[2] > 0.8 ? 1.6 : 1); g.globalAlpha = 0.3 + st[2] * 0.7; g.fillRect(st[0] * G.W, st[1] * G.H, s, s); });
      g.globalAlpha = 1;
    }
    G.sphere(p.s1, p.s2, isLight() ? null : 'rgba(90,130,220,.10)');
    if (VIEW === 'density') {
      G.land(function (c) { return P.pop[c] ? rgb(dcol(p, popAt(c, y) / AREA[c])) : p.land; }, p.line, 0.6);
    } else {
      G.land(p.land, p.line, 0.7);
      var w = worldAt(y);
      return G.dots(CODES, y, p.dot, Math.max(1.3, Math.min(3.4, 4.6 - 1.05 * Math.log10(w / 5e6))) * (o.dotScale || 1), 1e6, o.alpha);
    }
  }
  function tipHTML(c, y) {
    var v = popAt(c, y), w = worldAt(y), d = v / AREA[c];
    return '<b>' + esc(NAME[c]) + '</b><br>' + fmtPop(v) + ' · ' + tpl(T.ofWorld, { n: fmtDec(v / w * 100, v / w < 0.01 ? 2 : 1) }) + '<br>' +
      tpl(T.perKm, { n: d < 10 ? fmtDec(d, 1) : fmtInt(d) }) + '<br><span class="tiny">' + sourceAt(y).name + ' · ' +
      (Y.indexOf(Math.round(y)) !== -1 ? T.dataPoint : T.interp) + '</span>';
  }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;'); }
  function placeTip(tip, box, x, y) {
    var r = box.getBoundingClientRect();
    tip.style.left = Math.max(8, Math.min(x - r.left + 14, r.width - 200)) + 'px'; tip.style.top = (y - r.top + 14) + 'px';
    tip.classList.add('in');
  }

  /* ══ 1 · Прокрутка ═════════════════════════════════════════════ */
  (function () {
    var sec = document.getElementById('scroll'), sc = sec.querySelector('.scroller'), st = sec.querySelector('.sticky'), cv = sec.querySelector('canvas.globe');
    var G = new Globe(cv, { a: -80, b: 18, spin: 3, scale: 0.44 });
    var $ = function (k) { return sec.querySelector('[data-' + k + ']'); };
    var prog = sec.querySelector('.prog');
    function crossing(level) {
      if (worldAt(END) < level) return null;
      var lo = 1700, hi = END;
      for (var k = 0; k < 40; k++) { var m = (lo + hi) / 2; if (worldAt(m) >= level) hi = m; else lo = m; }
      return Math.round(hi);
    }
    var MILES = []; for (var b = 1; b <= 8; b++) MILES.push([b * 1e9, crossing(b * 1e9)]);
    $('miles').innerHTML = MILES.map(function (m) { return '<div><b>' + tpl(T.milestone, { n: m[0] / 1e9 }) + '</b> · ' + NF_Y.format(m[1]) + '</div>'; }).join('');
    var mEls = $('miles').children;
    /* Подпись к эпохе: с какого года она встаёт (сами слова — в каталоге строк). */
    var CAPY = [-99999, -3200, -200, 600, 1300, 1450, 1780, 1880, 1955, 2000];
    var CAPS = CAPY.map(function (y, i) { return [y, T.caps[i]]; });
    var s = stage(st, function (dt) {
      var p = s.pal, r = sc.getBoundingClientRect(), vh = window.innerHeight;
      var u = Math.max(0, Math.min(1, -(r.top - 90) / Math.max(1, r.height - vh * 0.85)));
      var y = makeMap(SET.start, END, SET.mode).toYear(u), w = worldAt(y);
      G.step(dt); G.resize(); G.clear(p.bg);
      drawView(G, p, y, { stars: true, alpha: 0.9 });
      var big = T.big[T.big.length - 1]; for (var bi = 0; bi < T.big.length; bi++) if (w >= T.big[bi][0]) { big = T.big[bi]; break; }
      $('num').textContent = fmtDec(w / big[0], big[1]);
      $('unit').textContent = big[2];
      $('year').textContent = fmtYear(y);
      $('src').textContent = tpl(T.via, { source: sourceAt(y).name });
      var cap = CAPS[0][1]; CAPS.forEach(function (c) { if (y >= c[0]) cap = c[1]; }); $('cap').textContent = cap;
      MILES.forEach(function (m, i) { mEls[i].classList.toggle('on', w >= m[0] * 0.995); });
      prog.style.width = (u * 100).toFixed(2) + '%';
    });
    io.observe(st);
  })();

  /* ══ 2 · Глобус + паспорт цифры ════════════════════════════════ */
  var drawLegend;
  (function () {
    var sec = document.getElementById('main'), cv = sec.querySelector('canvas.globe');
    var G = new Globe(cv, { a: -70, b: 24, spin: 5 }), pl = new Player(sec.querySelector('.player'));
    var $ = function (k) { return sec.querySelector('[data-' + k + ']'); };
    var tip = sec.querySelector('.tip'), leg = $('legend'), hover = null;
    G.onhover = function (e) {
      if (!e) { hover = null; tip.classList.remove('in'); return; }
      var ll = G.inv(e.clientX, e.clientY), c = ll && countryAt(ll[0], ll[1]);
      hover = c && P.pop[c] ? { c: c, x: e.clientX, y: e.clientY } : null;
      if (!hover) tip.classList.remove('in');
    };
    drawLegend = function () {
      var p = palette(sec);
      if (VIEW === 'dots') { leg.innerHTML = '<span class="tiny">' + T.dotUnit + '<br><span data-dots></span></span>'; return; }
      leg.innerHTML = '<div class="tiny" style="margin-bottom:6px">' + T.kmUnit + '</div><canvas class="ramp" width="440" height="60" style="width:220px;height:30px"></canvas>';
      var rc = leg.querySelector('canvas'), rg = rc.getContext('2d'), W = rc.width;
      for (var x = 0; x < W; x++) { rg.fillStyle = rgb(dcol(p, Math.pow(10, DLO + (DHI - DLO) * x / W))); rg.fillRect(x, 0, 1, 24); }
      rg.fillStyle = p.mute; rg.font = '20px JetBrains Mono, monospace';
      [0.1, 1, 10, 100, 1000].map(function (v) { return v < 1 ? fmtDec(v, 1) : fmtInt(v); }).forEach(function (t, i) { rg.textAlign = i === 0 ? 'left' : i === 4 ? 'right' : 'center'; rg.fillText(t, i / 4 * (W - 1), 54); });
    };

    /* паспорт */
    var chart = sec.querySelector('canvas.chart'), g2 = chart.getContext('2d');
    var AUTH = { PRB: 'PRB', UN: 'UN (1999)', Maddison: 'Maddison (2010)', HYDE: 'HYDE 3.1 (2010)', Biraben: 'Biraben (1980)',
                 McEvedy: 'McEvedy & Jones (1978)', Thomlinson: 'Thomlinson (1975)', Durand: 'Durand (1974)', Clark: 'Clark (1967)' };
    var EST = P.est.map(function (r) {
      var lo = Infinity, hi = 0, n = 0;
      Object.keys(r[1]).forEach(function (k) { lo = Math.min(lo, r[1][k][0]); hi = Math.max(hi, r[1][k][1]); n++; });
      return { y: r[0], v: r[1], lo: lo, hi: hi, n: n };
    });
    var M = { l: 50, r: 14, t: 16, b: 56 }, CW, CH, cdpr, LY0 = 6, LY1 = 10;
    function sx(u) { return (M.l + u * ((CW / cdpr) - M.l - M.r)) * cdpr; }
    function sy(v) { return (M.t + (1 - (Math.log10(v) - LY0) / (LY1 - LY0)) * ((CH / cdpr) - M.t - M.b)) * cdpr; }
    chart.addEventListener('pointermove', function (e) {
      var r = chart.getBoundingClientRect(), u = (e.clientX - r.left - M.l) / (r.width - M.l - M.r);
      if (u < 0 || u > 1) return;
      pl.playing = false; pl.hold = 0; pl.u = u; pl.sync();
    });
    function nearestEst(map, y) {
      var u = map.toU(y), best = null, bd = 0.035;
      EST.forEach(function (e) { if (e.y < SET.start) return; var d = Math.abs(map.toU(e.y) - u); if (d < bd) { bd = d; best = e; } });
      return best;
    }
    var lastPassKey = '';
    function passport(p, y, w) {
      var r = chart.getBoundingClientRect(), i; cdpr = G.dpr;
      CW = Math.round(r.width * cdpr); CH = Math.round(r.height * cdpr);
      if (chart.width !== CW || chart.height !== CH) { chart.width = CW; chart.height = CH; }
      var map = pl.map(), g = g2;
      g.clearRect(0, 0, CW, CH); g.font = (10.5 * cdpr) + 'px JetBrains Mono, monospace'; g.lineWidth = cdpr;
      for (i = LY0; i <= LY1; i++) {
        var yy = sy(Math.pow(10, i)); g.strokeStyle = p.grid; g.beginPath(); g.moveTo(sx(0), yy); g.lineTo(sx(1), yy); g.stroke();
        g.fillStyle = p.mute; g.textAlign = 'right'; g.fillText(fmtShort(Math.pow(10, i)), sx(0) - 8 * cdpr, yy + 3.5 * cdpr);
      }
      var cand = [-10000, -8000, -5000, -3000, -1000, 0, 500, 1000, 1300, 1500, 1700, 1800, 1900, 1950, 1975, 2000, 2023], lastX = -1e9;
      g.textAlign = 'center';
      cand.forEach(function (cy) {
        if (cy < SET.start) return; var x = sx(map.toU(cy)); if (x - lastX < 46 * cdpr) return; lastX = x;
        g.strokeStyle = p.grid; g.beginPath(); g.moveTo(x, sy(1e10)); g.lineTo(x, sy(1e6)); g.stroke();
        g.fillStyle = p.mute; g.fillText(fmtYear(cy), x, sy(1e6) + 14 * cdpr);
      });
      var ests = EST.filter(function (e) { return e.y >= SET.start && e.n >= 2; });
      if (ests.length > 1) {
        g.fillStyle = p.band; g.beginPath();
        ests.forEach(function (e, k) { var x = sx(map.toU(e.y)); if (k) g.lineTo(x, sy(e.hi)); else g.moveTo(x, sy(e.hi)); });
        for (i = ests.length - 1; i >= 0; i--) g.lineTo(sx(map.toU(ests[i].y)), sy(ests[i].lo));
        g.closePath(); g.fill();
      }
      g.fillStyle = p.est; g.globalAlpha = 0.75;
      EST.forEach(function (e) {
        if (e.y < SET.start) return; var x = sx(map.toU(e.y));
        Object.keys(e.v).forEach(function (k) { var v = e.v[k]; if (v[0] === v[1]) { g.beginPath(); g.arc(x, sy(v[0]), 2.2 * cdpr, 0, 7); g.fill(); } else g.fillRect(x - cdpr, sy(v[1]), 2 * cdpr, sy(v[0]) - sy(v[1])); });
      });
      g.globalAlpha = 1;
      g.strokeStyle = p.line2; g.lineWidth = 2 * cdpr; g.lineJoin = 'round'; g.beginPath();
      for (i = 0; i <= 400; i++) { var u = i / 400, x = sx(u), v = worldAt(map.toYear(u)); if (i) g.lineTo(x, sy(v)); else g.moveTo(x, sy(v)); }
      g.stroke();
      var by = sy(1e6) + 24 * cdpr, bh = 7 * cdpr, prev = SET.start;
      SOURCES.forEach(function (src) {
        var a = Math.max(prev, SET.start), b = Math.min(src.to, END); prev = src.to;
        if (b <= a) return;
        var x0 = sx(map.toU(a)), x1 = sx(map.toU(b));
        g.fillStyle = p[src.key]; g.fillRect(x0, by, Math.max(1, x1 - x0 - 2 * cdpr), bh);
        if (x1 - x0 > 70 * cdpr) { g.fillStyle = p.mute; g.textAlign = 'left'; g.fillText(src.name, x0 + 2 * cdpr, by + bh + 13 * cdpr); }
      });
      var cx = sx(pl.u), ink = getComputedStyle(document.body).color;
      g.strokeStyle = ink; g.globalAlpha = 0.45; g.lineWidth = cdpr; g.beginPath(); g.moveTo(cx, sy(1e10)); g.lineTo(cx, sy(1e6)); g.stroke(); g.globalAlpha = 1;
      g.fillStyle = p.line2; g.beginPath(); g.arc(cx, sy(w), 5 * cdpr, 0, 7); g.fill();

      /* карточка — перестраивается, только если сменилось что-то видимое */
      var src = sourceAt(y), sk = seek(y), exact = sk[0] === sk[1] || Math.abs(y - Y[sk[0]]) < 0.5, e = nearestEst(map, y);
      var key = Math.round(y) + '|' + (e ? e.y : '') + '|' + root.getAttribute('data-theme');
      if (key === lastPassKey) return; lastPassKey = key;
      $('pyear').textContent = fmtYear(y);
      $('pnum').textContent = fmtPop(w);
      $('psrc').innerHTML = '<span class="chip"><i style="background:' + p[src.key] + '"></i>' + src.name + '</span><span class="chip">' + src.kind + '</span>';
      $('cite').textContent = src.cite;
      $('how').textContent = exact ? tpl(T.exact, { y: fmtYear(Y[sk[0]]) }) :
        tpl(T.between, { a: fmtYear(Y[sk[0]]), av: fmtShort(P.world[sk[0]]), b: fmtYear(Y[sk[1]]), bv: fmtShort(P.world[sk[1]]) });
      var strip = $('strip'), list = $('estl'), sp = $('spread');
      if (e) {
        $('esth').textContent = tpl(T.estFor, { y: fmtYear(e.y) });
        var lo = Math.log10(Math.min(e.lo, worldAt(e.y)) * 0.8), hi = Math.log10(Math.max(e.hi, worldAt(e.y)) * 1.2);
        var pos = function (v) { return ((Math.log10(v) - lo) / (hi - lo) * 100).toFixed(1) + '%'; };
        var sh = '', lh = '';
        Object.keys(e.v).sort(function (a, b) { return e.v[a][0] - e.v[b][0]; }).forEach(function (k) {
          var v = e.v[k];
          sh += v[0] === v[1] ? '<span class="e" style="left:' + pos(v[0]) + '" title="' + AUTH[k] + '"></span>'
                              : '<span class="e rng" style="left:' + pos(v[0]) + ';width:calc(' + pos(v[1]) + ' - ' + pos(v[0]) + ')"></span>';
          lh += '<li>' + AUTH[k] + ' <b>' + (v[0] === v[1] ? fmtShort(v[0]) : fmtShort(v[0]) + '–' + fmtShort(v[1])) + '</b></li>';
        });
        sh += '<span class="o" style="left:' + pos(worldAt(e.y)) + '" title="' + esc(T.markTitle) + '"></span>';
        strip.innerHTML = sh; list.innerHTML = lh;
        sp.innerHTML = e.n > 1 ? tpl(T.spread, { lo: fmtShort(e.lo), hi: fmtShort(e.hi), x: fmtDec(e.hi / e.lo, 1) }) : T.estOne;
      } else {
        $('esth').textContent = T.estNone;
        strip.innerHTML = ''; list.innerHTML = '';
        sp.textContent = y >= 1950 ? T.after1950 : T.noEst;
      }
    }

    var s = stage(sec, function (dt) {
      var p = s.pal; pl.step(dt); if (!hover) G.step(dt); G.resize(); G.clear(p.bg);
      var y = pl.year(), w = worldAt(y);
      var n = drawView(G, p, y, { stars: true });
      $('num').textContent = fmtPop(w); $('year').textContent = fmtYear(y);
      $('src').innerHTML = chipHTML(y, p.acc);
      var dEl = leg.querySelector('[data-dots]'); if (dEl && n != null) dEl.textContent = tpl(T.dotsNow, { n: fmtInt(n) });
      if (hover) { tip.innerHTML = tipHTML(hover.c, y); placeTip(tip, tip.parentNode, hover.x, hover.y); }
      passport(p, y, w);
    });
    io.observe(sec);
  })();

  /* ══ 3 · Страна в мире ═════════════════════════════════════════ */
  (function () {
    var sec = document.getElementById('country'), stg = sec.querySelector('.stage'), cv = sec.querySelector('canvas.globe');
    var selC = document.getElementById('cc'), selF = document.getElementById('cf'), selT = document.getElementById('ct');
    var FROM = [-10000, -5000, -3000, -1000, 0, 500, 1000, 1500, 1700, 1800, 1900, 1950, 2000];
    var TO = [-1000, 0, 1000, 1500, 1800, 1900, 1950, 2000, 2023];
        var coll = null; try { coll = new Intl.Collator(LANG); } catch (e) {}
    selC.innerHTML = CODES.slice().sort(function (a, b) { return coll ? coll.compare(NAME[a], NAME[b]) : (NAME[a] < NAME[b] ? -1 : 1); })
      .map(function (c) { return '<option value="' + c + '">' + esc(NAME[c]) + '</option>'; }).join('');
    selF.innerHTML = FROM.map(function (y) { return '<option value="' + y + '">' + fmtYear(y) + '</option>'; }).join('');
    selT.innerHTML = TO.map(function (y) { return '<option value="' + y + '">' + fmtYear(y) + '</option>'; }).join('');
    if (FROM.indexOf(CS.f) === -1) CS.f = 1500; if (TO.indexOf(CS.t) === -1) CS.t = 2023;
    selC.value = CS.c; selF.value = String(CS.f); selT.value = String(CS.t);
    var span = function () { var a = CS.f, b = CS.t; if (b <= a) b = TO.filter(function (t) { return t > a; })[0] || END; return [a, b]; };
    var G = new Globe(cv, { scale: 0.4, spin: 0 }), pl = new Player(stg.querySelector('.player'), { range: span });
    var $ = function (k) { return sec.querySelector('[data-' + k + ']'); };
    var mini = sec.querySelector('canvas.mini'), mg = mini.getContext('2d');
    function aim() { var nm = P.names[CS.c]; G.target = [-nm[2], Math.max(-45, Math.min(55, nm[1]))]; }
    function pick(c) { if (!P.pop[c]) return; CS.c = c; selC.value = c; aim(); syncURL(); }
    selC.addEventListener('change', function () { pick(selC.value); });
    selF.addEventListener('change', function () { CS.f = +selF.value; pl.u = 0; pl.playing = true; pl.sync(); syncURL(); });
    selT.addEventListener('change', function () { CS.t = +selT.value; pl.u = 0; pl.playing = true; pl.sync(); syncURL(); });
    G.onclick = function (e) { var ll = G.inv(e.clientX, e.clientY), c = ll && countryAt(ll[0], ll[1]); if (c) pick(c); };
    G.a = -P.names[CS.c][2]; G.b = Math.max(-45, Math.min(55, P.names[CS.c][1]));
    var one = [];
    var s = stage(stg, function (dt) {
      var p = s.pal; pl.step(dt); G.step(dt); G.resize(); G.clear(p.bg);
      var cur = CS.c, y = pl.year(), w = worldAt(y), v = popAt(cur, y), sp = span(), g = G.ctx;
      G.sphere(p.s1, p.s2);
      var skip = {}; skip[cur] = 1;
      G.land(p.land, p.line, 0.6, skip);
      if (G.countryPath(cur)) { g.fillStyle = p.teal; g.globalAlpha = 0.28; g.fill('evenodd'); g.globalAlpha = 1; g.strokeStyle = p.teal; g.lineWidth = 1.4 * G.dpr; g.stroke(); }
      G.dots(CODES.filter(function (c) { return c !== cur; }), y, p.dot, 1.4, 1e6, 0.35);
      one[0] = cur; G.dots(one, y, p.teal, 2.2, 1e6);
      $('cname').textContent = NAME[cur];
      $('year').textContent = fmtYear(y) + ' · ' + sourceAt(y).name;
      $('cpop').textContent = fmtPop(v);
      $('cshare').textContent = NF_PCT[v / w < 0.01 ? 2 : 1].format(v / w);
      var rank = 1; CODES.forEach(function (c) { if (c !== cur && popAt(c, y) > v) rank++; });
      $('crank').textContent = tpl(T.rank, { n: rank });
      var v0 = popAt(cur, sp[0]); $('cgrow').textContent = '×' + fmtDec(v / v0, v / v0 < 10 ? 1 : 0);
      $('cgrowl').textContent = tpl(T.growth, { y: fmtYear(sp[0]) });
      $('src').innerHTML = chipHTML(y, p.teal);
      var r = mini.getBoundingClientRect(), dpr = G.dpr, MW = Math.round(r.width * dpr), MH = Math.round(r.height * dpr);
      if (mini.width !== MW || mini.height !== MH) { mini.width = MW; mini.height = MH; }
      mg.clearRect(0, 0, MW, MH);
      var map = pl.map(), mx = 0, i, pts = [];
      for (i = 0; i <= 160; i++) { var yy = map.toYear(i / 160), sh = popAt(cur, yy) / worldAt(yy); pts.push(sh); mx = Math.max(mx, sh); }
      mx = mx * 1.15 || 1;
      var X = function (u) { return 4 * dpr + u * (MW - 8 * dpr); }, Yp = function (sh) { return MH - 16 * dpr - sh / mx * (MH - 26 * dpr); };
      mg.fillStyle = p.teal; mg.globalAlpha = 0.15; mg.beginPath(); mg.moveTo(X(0), Yp(0));
      pts.forEach(function (sh, k) { mg.lineTo(X(k / 160), Yp(sh)); }); mg.lineTo(X(1), Yp(0)); mg.fill(); mg.globalAlpha = 1;
      mg.strokeStyle = p.teal; mg.lineWidth = 2 * dpr; mg.beginPath(); pts.forEach(function (sh, k) { if (k) mg.lineTo(X(k / 160), Yp(sh)); else mg.moveTo(X(0), Yp(sh)); }); mg.stroke();
      mg.fillStyle = p.mute; mg.font = (10 * dpr) + 'px JetBrains Mono, monospace'; mg.textAlign = 'left';
      mg.fillText(fmtYear(sp[0]), X(0), MH - 3 * dpr); mg.textAlign = 'right'; mg.fillText(fmtYear(sp[1]), X(1), MH - 3 * dpr);
      mg.textAlign = 'left'; mg.fillText(tpl(T.peak, { n: fmtDec(mx / 1.15 * 100, 1) }), X(0), 10 * dpr);
      var cx = X(pl.u); mg.strokeStyle = p.ink; mg.globalAlpha = 0.5; mg.lineWidth = dpr; mg.beginPath(); mg.moveTo(cx, 12 * dpr); mg.lineTo(cx, MH - 16 * dpr); mg.stroke(); mg.globalAlpha = 1;
    });
    io.observe(stg);
  })();

  /* ══ 4 · Раскадровка ═══════════════════════════════════════════ */
  var drawFrames = (function () {
    var box = document.querySelector('[data-frames]'), lb = document.getElementById('lb'), lbc = lb.querySelector('canvas');
    var YEARS = [-5000, -1000, 0, 1000, 1500, 1800, 1900, 1950, 2023], open = -1;
    var ZOOM = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"/></svg>';
    box.innerHTML = YEARS.map(function (y, i) {
      return '<figure><button type="button" data-i="' + i + '" aria-label="' + esc(tpl(T.openFrame, { y: fmtYear(y) })) + '"><canvas></canvas></button><span class="zoom">' + ZOOM + '</span>' +
        '<figcaption><b>' + fmtYear(y) + '</b>' + fmtPop(worldAt(y)) + '</figcaption></figure>';
    }).join('');
    var cvs = box.querySelectorAll('canvas');
    /* одна отрисовка на миниатюру и на большой кадр: меняются только размер и толщина точки */
    /* Чукотка и Фиджи пересекают 180-й меридиан: долготы в кольце разворачиваются
       без скачков, а то, что вышло за край карты, рисуется второй раз с другой стороны */
    function flat(rg) {
      if (!rg.flat) {
        var ll = rg.ll, o = [], prev = ll[0], min = 1e9, max = -1e9;
        for (var k = 0; k < ll.length; k += 2) {
          var lon = ll[k]; while (lon - prev > 180) lon -= 360; while (prev - lon > 180) lon += 360; prev = lon;
          o.push(lon, ll[k + 1]); min = Math.min(min, lon); max = Math.max(max, lon);
        }
        rg.flat = o; rg.offs = [0].concat(max > 180 ? [-360] : [], min < -180 ? [360] : []);
      }
      return rg.offs;
    }
    function ring(g, f, X, Yl, off) {
      for (var k = 0; k < f.length; k += 2) { var x = X(f[k] + off), y = Yl(f[k + 1]); if (k) g.lineTo(x, y); else g.moveTo(x, y); }
      g.closePath();
    }
    function paint(cv, y, p, big) {
      var r = cv.getBoundingClientRect(), dpr = Math.min(2, window.devicePixelRatio || 1);
      var W = Math.round(r.width * dpr), H = Math.round(r.height * dpr); if (!W) return;
      if (big) { var k = Math.min(1, 3000 / W); W = Math.round(W * k); H = Math.round(H * k); }
      cv.width = W; cv.height = H;
      var g = cv.getContext('2d'); g.fillStyle = p.bg; g.fillRect(0, 0, W, H);
      var X = function (lon) { return (lon + 180) / 360 * W; }, Yl = function (lat) { return (82 - lat) / 140 * H; };
      g.lineWidth = Math.max(0.5, W / 2400); g.strokeStyle = p.line; g.lineJoin = 'round';
      LANDCODES.forEach(function (c) {
        g.beginPath();
        GEO[c].rings.forEach(function (rg) { flat(rg).forEach(function (off) { ring(g, rg.flat, X, Yl, off); }); });
        g.fillStyle = VIEW === 'density' && P.pop[c] ? rgb(dcol(p, popAt(c, y) / AREA[c])) : p.land;
        g.fill('evenodd');
        if (big) g.stroke();
      });
      if (VIEW === 'density') return;
      g.fillStyle = p.dot; var s = big ? Math.max(1.5, W / 1000) : Math.max(1, 1.1 * dpr);
      CODES.forEach(function (c) {
        var d = P.dots[c], n = popAt(c, y) / 1e6, m = Math.min(Math.ceil(n), d.length / 2), full = Math.floor(n);
        for (var k = 0; k < m; k++) { g.globalAlpha = k < full ? 0.9 : (n - full) * 0.9; g.fillRect(X(d[2 * k]) - s / 2, Yl(d[2 * k + 1]) - s / 2, s, s); }
      });
      g.globalAlpha = 1;
    }
    function showBig(i) {
      open = (i + YEARS.length) % YEARS.length;
      var y = YEARS[open];
      lb.querySelector('[data-lby]').textContent = fmtYear(y);
      lb.querySelector('[data-lbn]').textContent = fmtPop(worldAt(y));
      lb.querySelector('[data-lbf]').textContent = (VIEW === 'density' ? T.lbDensity : T.lbDots) + ' · ' + tpl(T.via, { source: sourceAt(y).name });
      if (!lb.open) lb.showModal();
      paint(lbc, y, palette(box), true);
    }
    box.addEventListener('click', function (e) { var b = e.target.closest('button[data-i]'); if (b) showBig(+b.dataset.i); });
    lb.querySelector('[data-lbprev]').addEventListener('click', function () { showBig(open - 1); });
    lb.querySelector('[data-lbnext]').addEventListener('click', function () { showBig(open + 1); });
    lb.querySelector('[data-lbclose]').addEventListener('click', function () { lb.close(); });
    lb.addEventListener('click', function (e) { if (e.target === lb) lb.close(); });
    lb.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') { e.preventDefault(); showBig(open - 1); }
      if (e.key === 'ArrowRight') { e.preventDefault(); showBig(open + 1); }
    });
    /* девять карт — самая дорогая отрисовка на странице; до них ещё листать,
       поэтому рисуем, только когда раскадровка подошла к экрану */
    var near = false;
    function draw() {
      if (!near) return;
      var p = palette(box);
      YEARS.forEach(function (y, i) { paint(cvs[i], y, p, false); });
      if (lb.open) showBig(open);
    }
    new IntersectionObserver(function (es, ob) {
      if (es.some(function (e) { return e.isIntersecting; })) { near = true; ob.disconnect(); draw(); }
    }, { rootMargin: '600px 0px' }).observe(box);
    return draw;
  })();

  /* ── переключатели ─────────────────────────────────────────────── */
  var HINT = { linear: T.hintLinear, log: T.hintLog, doubling: T.hintDoubling };
  function mark(el, v) { [].forEach.call(el.children, function (b) { b.setAttribute('aria-pressed', String(b.dataset.v === String(v))); }); }
  function segCtl(el, get, set) {
    mark(el, get());
    el.addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; set(b.dataset.v); });
  }
  var viewSegs = document.querySelectorAll('[data-viewseg]');
  function setView(v) {
    VIEW = v; [].forEach.call(viewSegs, function (el) { mark(el, v); });
    drawLegend(); drawFrames(); syncURL();
  }
  [].forEach.call(viewSegs, function (el) { segCtl(el, function () { return VIEW; }, setView); });
  var cStart = document.getElementById('c-start'), cMode = document.getElementById('c-mode'), hint = document.getElementById('pacehint');
  segCtl(cStart, function () { return SET.start; }, function (v) { SET.start = +v; mark(cStart, v); syncURL(); });
  segCtl(cMode, function () { return SET.mode; }, function (v) { SET.mode = v; mark(cMode, v); hint.textContent = HINT[v]; syncURL(); });
  hint.textContent = HINT[SET.mode];

  var shareBtn = document.getElementById('share');
  shareBtn.addEventListener('click', function () {
    var url = location.origin + shareURL(), lab = shareBtn.querySelector('span'), was = lab.textContent;
    var done = function (t, ok) { lab.textContent = t; shareBtn.classList.toggle('done', !!ok); setTimeout(function () { lab.textContent = was; shareBtn.classList.remove('done'); }, 1600); };
    if (navigator.clipboard && location.protocol !== 'file:') navigator.clipboard.writeText(url).then(function () { done(T.copied, true); }, function () { done(T.copyManual); });
    else done(T.copyManual);
  });

  document.addEventListener('themechange', function () { STAGES.forEach(function (s) { s.pal = null; }); drawLegend(); drawFrames(); });
  var rt; window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(drawFrames, 150); });
  drawLegend(); drawFrames();
  requestAnimationFrame(loop);
  }
})();
