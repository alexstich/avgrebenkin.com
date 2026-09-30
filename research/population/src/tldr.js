/* Короткая версия. Простой текст и Markdown собраны сборкой из тех же строк,
   что стоят в окне, — второй копии, которая разъедется с первой, здесь нет.
   Ссылка внутри — на страницу того же языка, что открыт. */
(function () {
  var TL = {{tldrI18n}};
  var dlg = document.getElementById('tldr');
  if (!dlg || !dlg.showModal) return;
  var timer;

  document.getElementById('tldrOpen').addEventListener('click', function () { dlg.showModal(); });
  document.getElementById('tldrClose').addEventListener('click', function () { dlg.close(); });
  /* Клик мимо карточки закрывает: у модального диалога фон — это сам dialog. */
  dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });

  function flash(btn, text) {
    var label = btn.querySelector('span');
    var was = label.textContent;
    btn.classList.add('done'); label.textContent = text;
    clearTimeout(timer);
    timer = setTimeout(function () { btn.classList.remove('done'); label.textContent = was; }, 1800);
  }
  function copy(btn, text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { flash(btn, TL.copied); }, fallback);
    } else fallback();
    function fallback() {
      var ta = document.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly', '');
      ta.style.cssText = 'position:fixed;top:-1000px';
      document.body.appendChild(ta); ta.select();
      var ok = false; try { ok = document.execCommand('copy'); } catch (e) {}
      ta.remove(); flash(btn, ok ? TL.copied : TL.copyManual);
      if (!ok) {
        var r = document.createRange(); r.selectNodeContents(document.getElementById('tldrDoc'));
        var sel = getSelection(); sel.removeAllRanges(); sel.addRange(r);
      }
    }
  }
  [].forEach.call(document.querySelectorAll('[data-tldr-copy]'), function (btn) {
    btn.addEventListener('click', function () {
      copy(btn, btn.getAttribute('data-tldr-copy') === 'md' ? TL.md : TL.text);
    });
  });

  /* Печать одного листа: тело окна уезжает прямо в body (сам диалог в верхнем
     слое закрылся бы, как только его вынули), остальное снимает @media print. */
  var doc = document.getElementById('tldrDoc'), home = doc.parentNode, root = document.documentElement;
  function restore() {
    if (doc.parentNode !== home) home.appendChild(doc);
    if (root.getAttribute('data-print') === 'tldr') root.removeAttribute('data-print');
  }
  document.getElementById('tldrPrint').addEventListener('click', function () {
    document.body.appendChild(doc);
    root.setAttribute('data-print', 'tldr');
    window.print();
    restore();
  });
  window.addEventListener('afterprint', restore);
})();
