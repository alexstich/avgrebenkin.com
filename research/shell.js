/* Shell behaviour shared by the /research/ pages: theme switcher, language
   memory, burger menu and the border the navigation grows once the page is
   scrolled. The theme is
   read from and written to the same localStorage key as the front page, so the
   choice follows the reader across the site. */
(function () {
  'use strict';

  var root = document.documentElement;
  var themeBtns = Array.prototype.slice.call(document.querySelectorAll('.theme-btn'));
  var THEMES = ['dark', 'light', 'cyber'];

  function applyTheme(name) {
    root.setAttribute('data-theme', name);
    themeBtns.forEach(function (b) {
      var on = b.dataset.theme === name;
      b.classList.toggle('theme-btn-active', on);
      b.setAttribute('aria-checked', String(on));
    });
    try { localStorage.setItem('theme', name); } catch (e) {}
    document.dispatchEvent(new CustomEvent('themechange', { detail: name }));
  }
  var current = root.getAttribute('data-theme');
  applyTheme(THEMES.indexOf(current) === -1 ? 'dark' : current);
  themeBtns.forEach(function (b) {
    b.addEventListener('click', function () { applyTheme(b.dataset.theme); });
  });

  /* A language picked by hand outranks the browser's own preference list the
     next time this reader opens a bare /research/<study>/ address. The head
     script there does the sending; all this has to do is remember. */
  var langpick = document.querySelector('.langpick');
  if (langpick) {
    langpick.addEventListener('click', function (e) {
      var a = e.target.closest('a[hreflang]');
      if (!a) return;
      try { localStorage.setItem('lang', a.getAttribute('hreflang').toLowerCase()); } catch (err) {}
    });
  }

  var burger = document.getElementById('nav-burger');
  var navLinks = document.getElementById('nav-links');
  function closeMenu() {
    navLinks.classList.remove('is-open');
    burger.setAttribute('aria-expanded', 'false');
  }
  burger.addEventListener('click', function () {
    var open = navLinks.classList.toggle('is-open');
    burger.setAttribute('aria-expanded', String(open));
  });
  navLinks.addEventListener('click', function (e) {
    if (e.target.closest('.nav-link')) closeMenu();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeMenu();
  });

  var nav = document.getElementById('site-nav');
  function onScroll() { nav.classList.toggle('is-scrolled', window.scrollY > 8); }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();
