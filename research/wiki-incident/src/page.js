(function () {
  "use strict";

  /* Разметка страницы полная: вся проза и все шаги лежат в HTML, скрытое
     складывается скриптом. Скрипт добавляет поведение — аккордеон хронологии,
     ленту фаз, клавиатуру и краткую версию, — но ничего не сочиняет. Каналы
     выше — нативные <details>, скрипта не требуют. */

  var root = document.documentElement;
  var page = document.getElementById("wiki");
  if (!page) return;

  var reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var explorer = document.getElementById("explorer");
  var steps = explorer ? Array.prototype.slice.call(explorer.querySelectorAll(".step")) : [];
  var timeline = document.getElementById("timeline");
  var barEl = explorer ? explorer.querySelector(".exbar") : null;

  function stickyOffset() {
    var nav = parseFloat(getComputedStyle(root).getPropertyValue("--nav-h")) || 60;
    return nav + (barEl ? barEl.getBoundingClientRect().height : 0) + 14;
  }

  /* ── аккордеон хронологии ──────────────────────────────────── */

  function collapseNow(step) {
    var body = step.querySelector(".step-body");
    body.style.transition = ""; body.style.height = "";
    step.open = false;
  }

  function animate(step, open, done) {
    var body = step.querySelector(".step-body");
    if (reduced) { step.open = open; if (done) done(); return; }
    if (body._t) { clearTimeout(body._t); body._t = null; }
    if (open) step.open = true;
    var h = body.scrollHeight;
    body.style.transition = "none";
    body.style.height = (open ? 0 : h) + "px";
    body.offsetHeight;
    body.style.transition = "height .2s ease-out";
    body.style.height = (open ? h : 0) + "px";
    body._t = setTimeout(function () {
      body.style.transition = ""; body.style.height = "";
      if (!open) step.open = false;
      body._t = null;
      if (done) done();
    }, 210);
  }

  function closeOthers(except) {
    var top = except ? except.getBoundingClientRect().top : 0;
    steps.forEach(function (s) {
      if (s === except || !s.open) return;
      var r = s.getBoundingClientRect(), h = s.querySelector(".step-body").offsetHeight;
      collapseNow(s);
      if (except && r.top < top) window.scrollBy({ top: -h, behavior: "instant" });
    });
  }

  function openStep(step) { closeOthers(step); animate(step, true); writeHash(step.id); }

  steps.forEach(function (step) {
    step.querySelector(".step-head").addEventListener("click", function (e) {
      e.preventDefault();
      if (step.open) { animate(step, false); writeHash(null); }
      else openStep(step);
    });
  });

  /* ── адрес: раскрытый шаг ──────────────────────────────────── */

  var hash = "";
  function writeHash(id) { hash = id ? "#" + id : ""; syncURL(); }
  function syncURL() {
    try { history.replaceState(null, "", location.pathname + hash); } catch (e) {}
  }

  /* ── лента фаз, активная фаза, прогресс ────────────────────── */

  var ribbon = document.getElementById("ribbon");
  var phaseEls = {};
  if (ribbon && DATA.phases) {
    DATA.phases.forEach(function (a) {
      var el = document.getElementById(a.id);
      if (el) phaseEls[a.id] = el;
      var b = document.createElement("button");
      b.type = "button";
      b.dataset.phase = a.id;
      b.innerHTML = '<span class="rnum">' + a.num + '</span>' +
                    '<span class="rtitle"></span><span class="rdate"></span>';
      b.querySelector(".rtitle").textContent = a.title;
      b.querySelector(".rdate").textContent = a.dates;
      b.addEventListener("click", function () { goToPhase(a.id); });
      ribbon.appendChild(b);
    });
  }
  var ribbonBtns = ribbon ? Array.prototype.slice.call(ribbon.querySelectorAll("button")) : [];

  function scrollToEl(el, smooth) {
    window.scrollTo({
      top: window.pageYOffset + el.getBoundingClientRect().top - stickyOffset(),
      behavior: smooth && !reduced ? "smooth" : "instant"
    });
  }
  function goToPhase(id) { if (phaseEls[id]) scrollToEl(phaseEls[id], true); }

  var progressFill = explorer ? explorer.querySelector(".progress i") : null;
  var activePhase = null;

  function onScroll() {
    if (!DATA.phases) return;
    var edge = stickyOffset() + 6;
    var found = DATA.phases[0].id;
    DATA.phases.forEach(function (a) {
      var el = phaseEls[a.id];
      if (el && el.getBoundingClientRect().top <= edge) found = a.id;
    });
    if (found !== activePhase) {
      activePhase = found;
      ribbonBtns.forEach(function (b) {
        var on = b.dataset.phase === found;
        b.setAttribute("aria-current", String(on));
        if (on && ribbon.scrollWidth > ribbon.clientWidth) {
          var r = b.getBoundingClientRect(), rr = ribbon.getBoundingClientRect();
          if (r.left < rr.left + 8 || r.right > rr.right - 8) {
            ribbon.scrollTo({ left: b.offsetLeft - 12, behavior: reduced ? "auto" : "smooth" });
          }
        }
      });
    }
    if (progressFill && timeline) {
      var r = timeline.getBoundingClientRect();
      var span = r.height - window.innerHeight * 0.5;
      var done = span > 0 ? (edge - r.top) / span : 1;
      progressFill.style.width = Math.max(0, Math.min(1, done)) * 100 + "%";
    }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll, { passive: true });

  /* ── клавиатура внутри проводника ──────────────────────────── */

  page.addEventListener("keydown", function (e) {
    var inside = document.activeElement && document.activeElement.closest &&
                 document.activeElement.closest("#explorer");
    if (!inside) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var vis = steps.filter(function (s) { return s.offsetParent; });
    var cur = document.activeElement.closest(".step");
    var i = cur ? vis.indexOf(cur) : -1;

    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      var next = e.key === "ArrowDown"
        ? vis[i < 0 ? 0 : Math.min(i + 1, vis.length - 1)]
        : vis[i <= 0 ? 0 : i - 1];
      if (next) next.querySelector(".step-head").focus();
    } else if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
      e.preventDefault();
      var k = DATA.phases.findIndex(function (a) { return a.id === activePhase; });
      if (k < 0) k = 0;
      k = e.key === "ArrowRight" ? Math.min(k + 1, DATA.phases.length - 1) : Math.max(k - 1, 0);
      goToPhase(DATA.phases[k].id);
    } else if (e.key === "Escape") {
      steps.forEach(function (s) { if (s.open) animate(s, false); });
      writeHash(null);
    }
  });

  /* ── старт ─────────────────────────────────────────────────── */

  steps.forEach(collapseNow);

  var want = location.hash.replace("#", "");
  var target = want && document.getElementById(want);
  if (target && target.classList.contains("step")) {
    hash = "#" + want;
    target.open = true;
    requestAnimationFrame(function () {
      scrollToEl(target, false);
      setTimeout(function () { scrollToEl(target, false); onScroll(); }, 180);
    });
  }
  syncURL();
  onScroll();

  window.addEventListener("beforeprint", function () {
    steps.forEach(function (s) { s.open = true; });
  });
  window.addEventListener("afterprint", function () {
    steps.forEach(function (s) { s.open = false; });
    var h = location.hash.replace("#", "");
    var t = h && document.getElementById(h);
    if (t && t.classList.contains("step")) t.open = true;
  });

  /* ── краткая версия: открыть, скопировать, распечатать ─────── */

  var tldr = document.getElementById("tldr");
  if (tldr) {
    var TLDR_TEXT = {{tldrText}};
    var TLDR_MD = {{tldrMd}};
    var TLDR_DONE = {{tldrCopied}};

    document.querySelector("[data-tldr-open]").addEventListener("click", function () {
      if (tldr.showModal) tldr.showModal(); else tldr.setAttribute("open", "");
    });
    tldr.querySelector("[data-tldr-close]").addEventListener("click", function () {
      tldr.close ? tldr.close() : tldr.removeAttribute("open");
    });
    tldr.addEventListener("click", function (e) { if (e.target === tldr) tldr.close(); });

    tldr.querySelectorAll("[data-tldr-copy]").forEach(function (btn) {
      var label = btn.textContent;
      btn.addEventListener("click", function () {
        var text = btn.dataset.tldrCopy === "md" ? TLDR_MD : TLDR_TEXT;
        function done() {
          btn.textContent = TLDR_DONE; btn.classList.add("done");
          setTimeout(function () { btn.textContent = label; btn.classList.remove("done"); }, 2000);
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done, selectBody);
        } else { selectBody(); }
      });
    });

    function selectBody() {
      var r = document.createRange();
      r.selectNodeContents(tldr.querySelector(".tldr-body"));
      var sel = getSelection(); sel.removeAllRanges(); sel.addRange(r);
    }

    var tbody = tldr.querySelector(".tldr-body"), tbodyHome = tbody.parentNode;
    function restoreTldr() {
      if (tbody.parentNode !== tbodyHome) tbodyHome.insertBefore(tbody, tbodyHome.firstChild);
      root.removeAttribute("data-printing");
    }
    tldr.querySelector("[data-tldr-print]").addEventListener("click", function () {
      document.body.appendChild(tbody);
      root.setAttribute("data-printing", "tldr");
      window.print();
      restoreTldr();
    });
    window.addEventListener("afterprint", restoreTldr);
  }

  /* ── карта роя: 30 площадок, анимация «крупные первыми» ─────── */

  var stage = document.getElementById("swarm-stage");
  if (stage && DATA.sites && DATA.kinds) {
    var U = DATA.ui || {};
    var countEl = document.getElementById("swarm-count");
    var playBtn = document.getElementById("swarm-play");
    var maxE = Math.max.apply(null, DATA.sites.map(function (s) { return s.edits; }));
    var maxR = Math.sqrt(maxE);
    function bubSize(e) { return Math.round(16 + (Math.sqrt(e) - 1) / (maxR - 1) * 42); }
    var totalEdits = DATA.sites.reduce(function (a, s) { return a + s.edits; }, 0);

    var tip = document.createElement("div");
    tip.className = "swarm-tip";
    document.getElementById("swarm").appendChild(tip);

    var bubbles = [];   // в порядке убывания правок — порядок посадки
    DATA.kinds.forEach(function (k) {
      var lane = document.createElement("div");
      lane.className = "lane";
      var label = document.createElement("div");
      label.className = "lane-label";
      var kSites = DATA.sites.filter(function (s) { return s.kind === k.id; })
                             .sort(function (a, b) { return b.edits - a.edits; });
      var kEdits = kSites.reduce(function (a, s) { return a + s.edits; }, 0);
      label.innerHTML = '<b>' + k.num + '</b>' + k.name;
      var wrap = document.createElement("div");
      wrap.className = "lane-bubbles";
      kSites.forEach(function (s) {
        var b = document.createElement("span");
        b.className = "bub" + (s["new"] ? " new" : "");
        var sz = bubSize(s.edits);
        b.style.width = b.style.height = sz + "px";
        b.tabIndex = 0;
        b.setAttribute("role", "img");
        b.setAttribute("aria-label", s.host + " — " + s.edits + " " + (U.editsWord || "edits"));
        b._site = s;
        wrap.appendChild(b);
        bubbles.push(b);
      });
      lane.appendChild(label); lane.appendChild(wrap);
      stage.appendChild(lane);
    });
    bubbles.sort(function (a, b) { return b._site.edits - a._site.edits; });

    function setCount(nSites, nEdits) {
      if (!countEl) return;
      var t = (U.mapCount || "{sites} sites · {edits} edits")
        .replace("{sites}", "<b>" + nSites + "</b>")
        .replace("{edits}", "<b>" + nEdits.toLocaleString("en-US") + "</b>");
      countEl.innerHTML = t;
    }

    function showTip(b) {
      var s = b._site;
      tip.innerHTML = '<b>' + s.host + '</b><span class="tmeta">' + s.edits +
        ' ' + (U.editsWord || "edits") + ' · ' + s.units + ' ' + s.unit +
        (s.when && s.when !== "—" ? ' · ' + s.when : '') +
        '<br>' + s.by + '</span>';
      var fig = document.getElementById("swarm").getBoundingClientRect();
      var r = b.getBoundingClientRect();
      tip.style.left = Math.max(6, Math.min(r.left - fig.left + r.width / 2 - 110, fig.width - 226)) + "px";
      tip.style.top = (r.bottom - fig.top + 8) + "px";
      tip.classList.add("show");
    }
    function hideTip() { tip.classList.remove("show"); }
    bubbles.forEach(function (b) {
      b.addEventListener("mouseenter", function () { showTip(b); });
      b.addEventListener("mouseleave", hideTip);
      b.addEventListener("focus", function () { showTip(b); });
      b.addEventListener("blur", hideTip);
    });

    var lbl = playBtn ? playBtn.querySelector(".sp-label") : null;
    function setLabel(t) { if (lbl && t) lbl.textContent = t; if (playBtn) playBtn.setAttribute("aria-label", t || ""); }
    var timer = null, landed = 0;
    function stopPlay() {
      if (timer) { clearInterval(timer); timer = null; }
      if (playBtn) playBtn.classList.remove("playing");
    }
    function revealAll() {
      stopPlay();
      bubbles.forEach(function (b) { b.classList.add("in"); });
      landed = bubbles.length; setCount(bubbles.length, totalEdits);
      setLabel(U.mapReplay);
    }
    function play() {
      stopPlay();
      bubbles.forEach(function (b) { b.classList.remove("in"); });
      landed = 0; setCount(0, 0);
      if (playBtn) { playBtn.classList.add("playing"); }
      setLabel(U.mapPause);
      var running = 0;
      timer = setInterval(function () {
        if (landed >= bubbles.length) { stopPlay(); setLabel(U.mapReplay); return; }
        var b = bubbles[landed++];
        b.classList.add("in");
        running += b._site.edits;
        setCount(landed, running);
      }, 70);
    }

    if (playBtn) {
      playBtn.addEventListener("click", function () {
        if (timer) { revealAll(); } else { play(); }
      });
    }

    if (reduced || !("IntersectionObserver" in window)) {
      revealAll();
    } else {
      setCount(0, 0);
      var io = new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting) { play(); io.disconnect(); } });
      }, { threshold: .35 });
      io.observe(stage);
    }
  }

  /* ── числа: счёт от нуля при появлении ─────────────────────── */

  var numB = Array.prototype.slice.call(page.querySelectorAll(".num b"));
  if (numB.length && !reduced && "IntersectionObserver" in window) {
    var nio = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        countUp(e.target); nio.unobserve(e.target);
      });
    }, { threshold: .6 });
    numB.forEach(function (el) { nio.observe(el); });
  }
  function countUp(el) {
    var orig = el.textContent;
    var m = orig.match(/[\d][\d,]*/);   // первое число
    if (!m) return;
    var target = parseInt(m[0].replace(/,/g, ""), 10);
    if (!(target > 0)) return;
    var t0 = null, dur = 900;
    function frame(t) {
      if (!t0) t0 = t;
      var k = Math.min(1, (t - t0) / dur);
      var v = Math.round((1 - Math.pow(1 - k, 3)) * target);
      el.textContent = orig.replace(m[0], v.toLocaleString("en-US"));
      if (k < 1) requestAnimationFrame(frame); else el.textContent = orig;
    }
    requestAnimationFrame(frame);
  }

  /* ── появление блоков при прокрутке ────────────────────────── */

  if (!reduced && "IntersectionObserver" in window) {
    var rev = page.querySelectorAll(".lg, .chan, .fact, .dv, .num");
    var rio = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); rio.unobserve(e.target); }
      });
    }, { threshold: .15, rootMargin: "0px 0px -8% 0px" });
    Array.prototype.forEach.call(rev, function (el) { el.classList.add("reveal"); el._r = 1; rio.observe(el); });
  }

  document.addEventListener("themechange", onScroll);
})();
