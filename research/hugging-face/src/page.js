(function () {
  "use strict";

  /* Разметка страницы полная: оба режима и все версии лежат в HTML, скрытое
     убирается классом на корне. Скрипт добавляет к статье поведение —
     тумблер, аккордеон, ленту актов и клавиатуру, — но ничего не сочиняет. */

  var root = document.documentElement;
  var page = document.getElementById("hf");
  if (!page) return;

  var reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var steps = Array.prototype.slice.call(page.querySelectorAll(".step"));
  var timeline = document.getElementById("timeline");
  var barEl = document.querySelector(".exbar");

  /* ── режим «Просто / Подробно» ─────────────────────────────── */

  var segs = Array.prototype.slice.call(page.querySelectorAll("[data-seg]"));
  var counters = Array.prototype.slice.call(page.querySelectorAll("[data-counter]"));
  var total = DATA.steps.length;
  var basic = DATA.steps.filter(function (s) { return s.level === "basic"; }).length;

  /* Формулировки счётчика приходят из строк языка: во множественном числе
     каждый язык согласуется по-своему, и в скрипте этому не место. */
  function fill(t) {
    return String(t).replace("{shown}", basic).replace("{total}", total);
  }

  function currentMode() { return root.getAttribute("data-mode") === "full" ? "full" : "simple"; }

  function paintMode() {
    var m = currentMode();
    segs.forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.seg === m)); });
    var text = fill(m === "simple" ? UI.counterSimple : UI.counterFull);
    counters.forEach(function (c) { c.textContent = text; });
  }

  /* Липкая панель проводника стоит под шапкой сайта: всё, что целится
     «под панель», обязано вычесть обе высоты. */
  function stickyOffset() {
    var nav = parseFloat(getComputedStyle(root).getPropertyValue("--nav-h")) || 60;
    return nav + (barEl ? barEl.getBoundingClientRect().height : 0) + 14;
  }

  /* Опора для прокрутки: раскрытый шаг, иначе первый видимый под липкой панелью. */
  function anchorStep() {
    var open = page.querySelector(".step[open]");
    if (open && open.offsetParent) return open;
    var edge = stickyOffset();
    for (var i = 0; i < steps.length; i++) {
      if (!steps[i].offsetParent) continue;
      if (steps[i].getBoundingClientRect().bottom > edge) return steps[i];
    }
    return null;
  }

  function nearestVisible(step) {
    if (!step) return null;
    var i = steps.indexOf(step), j;
    for (j = i; j >= 0; j--) if (steps[j].offsetParent) return steps[j];
    for (j = i; j < steps.length; j++) if (steps[j].offsetParent) return steps[j];
    return null;
  }

  function setMode(m, remember) {
    if (m === currentMode()) return;
    var ref = anchorStep();
    var before = ref ? ref.getBoundingClientRect().top : 0;

    if (!reduced) {
      page.classList.add("fading");
      setTimeout(function () { page.classList.remove("fading"); }, 130);
    }
    root.setAttribute("data-mode", m);
    paintMode();

    /* Шаг мог исчезнуть вместе с режимом — держимся за ближайший видимый. */
    var after = nearestVisible(ref);
    /* Прокрутку правим мгновенно: у сайта html{scroll-behavior:smooth},
       и плавная доводка здесь читалась бы как самопроизвольный отъезд страницы. */
    if (after) window.scrollBy({ top: after.getBoundingClientRect().top - before,
                                 behavior: "instant" });
    if (remember !== false) { try { localStorage.setItem("hf-mode", m); } catch (e) {} }
    syncURL();
    onScroll();
  }

  segs.forEach(function (b) {
    b.addEventListener("click", function () { setMode(b.dataset.seg, true); });
  });

  /* ── аккордеон ─────────────────────────────────────────────── */

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

  /* Соседей закрываем мгновенно и подправляем прокрутку, если они были выше:
     иначе страница уезжает под курсором ровно в момент клика. */
  function closeOthers(except) {
    var top = except ? except.getBoundingClientRect().top : 0;
    steps.forEach(function (s) {
      if (s === except || !s.open) return;
      var r = s.getBoundingClientRect(), h = s.querySelector(".step-body").offsetHeight;
      collapseNow(s);
      if (except && r.top < top) window.scrollBy({ top: -h, behavior: "instant" });
    });
  }

  function openStep(step) {
    closeOthers(step);
    animate(step, true);
    writeHash(step.id);
  }

  steps.forEach(function (step) {
    var head = step.querySelector(".step-head");
    head.addEventListener("click", function (e) {
      e.preventDefault();
      if (step.open) { animate(step, false); writeHash(null); }
      else openStep(step);
    });
  });

  /* ── адрес: режим и раскрытый шаг ──────────────────────────── */

  var hash = "";
  function writeHash(id) { hash = id ? "#" + id : ""; syncURL(); }
  function syncURL() {
    var q = currentMode() === "full" ? "?mode=full" : "";
    try {
      history.replaceState(null, "", location.pathname + q + hash);
    } catch (e) {}
  }

  /* ── лента актов, активный акт, прогресс ───────────────────── */

  var ribbon = document.getElementById("ribbon");
  var actEls = {};
  DATA.acts.forEach(function (a) {
    var el = document.getElementById(a.id);
    if (el) actEls[a.id] = el;
    var b = document.createElement("button");
    b.type = "button";
    b.dataset.act = a.id;
    b.innerHTML = '<span class="rnum">' + a.num + '</span>' +
                  '<span class="rtitle"></span><span class="rdate"></span>';
    b.querySelector(".rtitle").textContent = a.title;
    b.querySelector(".rdate").textContent = a.dates;
    b.addEventListener("click", function () { goToAct(a.id); });
    ribbon.appendChild(b);
  });
  var ribbonBtns = Array.prototype.slice.call(ribbon.querySelectorAll("button"));

  function scrollToEl(el, smooth) {
    window.scrollTo({
      top: window.pageYOffset + el.getBoundingClientRect().top - stickyOffset(),
      behavior: smooth && !reduced ? "smooth" : "instant"
    });
  }

  function goToAct(id) {
    if (actEls[id]) scrollToEl(actEls[id], true);
  }

  var progressFill = document.querySelector(".progress i");
  var activeAct = null;

  function onScroll() {
    /* Тот же порог, к которому целится scrollToEl, плюс волос: иначе акт,
       к которому только что прокрутили, не становится активным. */
    var edge = stickyOffset() + 6;
    var found = DATA.acts[0].id;
    DATA.acts.forEach(function (a) {
      var el = actEls[a.id];
      if (el && el.getBoundingClientRect().top <= edge) found = a.id;
    });
    if (found !== activeAct) {
      activeAct = found;
      ribbonBtns.forEach(function (b) {
        var on = b.dataset.act === found;
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

  function visibleSteps() {
    return steps.filter(function (s) { return s.offsetParent; });
  }

  page.addEventListener("keydown", function (e) {
    var inside = document.activeElement && document.activeElement.closest &&
                 document.activeElement.closest("#explorer");
    if (!inside) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var vis = visibleSteps();
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
      var k = DATA.acts.findIndex(function (a) { return a.id === activeAct; });
      if (k < 0) k = 0;
      k = e.key === "ArrowRight" ? Math.min(k + 1, DATA.acts.length - 1) : Math.max(k - 1, 0);
      goToAct(DATA.acts[k].id);
    } else if (e.key === "Escape") {
      steps.forEach(function (s) { if (s.open) animate(s, false); });
      writeHash(null);
    }
  });

  /* ── старт ─────────────────────────────────────────────────── */

  /* В разметке всё раскрыто — так страница читается и без скрипта.
     Скрипт складывает карточки и дальше управляет ими сам. */
  steps.forEach(collapseNow);
  paintMode();

  var want = location.hash.replace("#", "");
  var target = want && document.getElementById(want);
  if (target && target.classList.contains("step")) {
    if (target.dataset.level === "full") setMode("full", false);
    hash = "#" + want;
    target.open = true;
    /* Второй проход — после того как шрифты встали и высоты устоялись. */
    requestAnimationFrame(function () {
      scrollToEl(target, false);
      setTimeout(function () { scrollToEl(target, false); onScroll(); }, 180);
    });
  }
  syncURL();
  onScroll();

  /* На бумаге нет тумблера и аккордеона — печатаем всё и подробно. */
  var printMode = null;
  window.addEventListener("beforeprint", function () {
    printMode = currentMode();
    root.setAttribute("data-mode", "full");
    steps.forEach(function (s) { s.open = true; });
  });
  window.addEventListener("afterprint", function () {
    if (printMode) root.setAttribute("data-mode", printMode);
    steps.forEach(function (s) { s.open = false; });
    var h = location.hash.replace("#", "");
    var t = h && document.getElementById(h);
    if (t && t.classList.contains("step")) t.open = true;
  });


  // ---- краткая версия: открыть, скопировать, распечатать -----------------
  // Тексты собраны сборщиком из тех же строк, что и статья, — здесь только
  // буфер обмена и печать.
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
    // клик мимо содержимого — тоже закрытие: у нативного диалога подложка это он сам
    tldr.addEventListener("click", function (e) {
      if (e.target === tldr) tldr.close();
    });

    tldr.querySelectorAll("[data-tldr-copy]").forEach(function (btn) {
      var label = btn.textContent;
      btn.addEventListener("click", function () {
        var text = btn.dataset.tldrCopy === "md" ? TLDR_MD : TLDR_TEXT;
        function done() {
          btn.textContent = TLDR_DONE;
          btn.classList.add("done");
          setTimeout(function () {
            btn.textContent = label;
            btn.classList.remove("done");
          }, 2000);
        }
        // без https буфер недоступен — тогда выделяем текст, чтобы копировали руками
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done, selectBody);
        } else { selectBody(); }
      });
    });

    function selectBody() {
      var r = document.createRange();
      r.selectNodeContents(tldr.querySelector(".tldr-body"));
      var sel = getSelection();
      sel.removeAllRanges();
      sel.addRange(r);
    }

    tldr.querySelector("[data-tldr-print]").addEventListener("click", function () {
      root.setAttribute("data-printing", "tldr");
      window.print();
    });
    window.addEventListener("afterprint", function () {
      root.removeAttribute("data-printing");
    });
  }

  document.addEventListener("themechange", onScroll);
})();
