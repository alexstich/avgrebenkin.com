/* Графики и инструменты страницы. Всё рисуется DOM-ом и SVG на CSS-переменных:
   тема сайта переключается без перерисовки. Числа — из DATA (structure.json),
   подписи — из T (strings/<язык>.json). */
(function(){
'use strict';

function $(id){ return document.getElementById(id); }
function el(tag, cls, html){
  var e=document.createElement(tag);
  if(cls) e.className=cls;
  if(html!=null) e.innerHTML=html;
  return e;
}
function fill(s, o){ return String(s).replace(/\{(\w+)\}/g, function(m,k){ return k in o ? o[k] : m; }); }
function num(v, dp){
  var s=(dp==null ? String(v) : v.toFixed(dp));
  return s.replace('.', T.decimal);
}
function pct(v, dp){ return fill(T.percent, {n: num(v, dp)}); }
/* В китайском и японском слова пишутся слитно: предложение не склеивается
   пробелами, а скорость печати не делится на пять знаков. */
var CJK=/^(ja|zh)/.test(document.documentElement.lang), SEP=CJK ? '' : ' ';
function svgEl(tag, attrs){
  var e=document.createElementNS('http://www.w3.org/2000/svg', tag);
  for(var k in attrs) e.setAttribute(k, attrs[k]);
  return e;
}

/* Полоса со значением. Ширина ставится при появлении на экране, чтобы полоса
   дорастала до своего значения на глазах читателя, а не стояла готовой. */
function bar(w, cls, val){
  var b=el('div','bar');
  var tr=el('div','bar-track');
  var f=el('div','bar-fill'+(cls?' '+cls:''));
  f.style.width='0%'; f.dataset.w=Math.max(0, Math.min(100, w));
  tr.appendChild(f); b.appendChild(tr);
  if(val!=null) b.appendChild(el('span','bar-val',val));
  return b;
}
function mark(track, at){
  var m=el('span','bar-mark'); m.style.left=at+'%'; track.classList.add('marked'); track.appendChild(m);
}
function grow(root){
  root.classList && root.classList.add('in');
  [].forEach.call(root.querySelectorAll('[data-w]'), function(f){ f.style.width=f.dataset.w+'%'; });
  [].forEach.call(root.querySelectorAll('[data-h]'), function(f){ f.style.height=f.dataset.h+'%'; });
}
var io = ('IntersectionObserver' in window) ? new IntersectionObserver(function(es){
  es.forEach(function(e){
    if(!e.isIntersecting) return;
    e.target.classList.remove('pre'); grow(e.target); io.unobserve(e.target);
  });
}, {rootMargin:'0px 0px -12% 0px'}) : null;
function watch(node){
  if(!node) return;
  if(io && !matchMedia('(prefers-reduced-motion: reduce)').matches){ node.classList.add('pre'); io.observe(node); }
  else grow(node);
}

/* ── 01: две волны ───────────────────────────────────────────────────── */
(function(){
  var root=$('waves'); if(!root) return;
  var left=el('div','wave-panel'), right=el('div','wave-panel claims');
  left.appendChild(el('p','wave-h',T.surveyH));
  right.appendChild(el('p','wave-h',T.vendorH));

  DATA.survey.forEach(function(r){
    var row=el('div','row');
    row.appendChild(el('p','row-lab',T.survey[r.k]));
    var b=el('div','bar'), tr=el('div','bar-track');
    var f=el('div','bar-fill'); f.style.width='0%'; f.dataset.w=r.b; tr.appendChild(f);
    if(r.a!=null) mark(tr, r.a);
    b.appendChild(tr); b.appendChild(el('span','bar-val',pct(r.b)));
    row.appendChild(b);
    row.appendChild(el('p','pair', r.a!=null
      ? r.ay+' <b>'+pct(r.a)+'</b> → '+r.by+' <b>'+pct(r.b)+'</b>'
      : r.by));
    left.appendChild(row);
  });

  function unit(r, v){
    if(r.unit==='bnDay') return fill(T.bnDay,{n:num(v)});
    if(r.unit==='usdBn') return fill(T.usdBn,{n:num(v)});
    return pct(v);
  }
  DATA.vendor.forEach(function(r){
    var row=el('div','row');
    row.appendChild(el('p','row-lab',T.vendor[r.k]));
    var shown=unit(r, r.b); if(r.plus) shown=fill(T.plus,{n:shown});
    if(r.a!=null){
      var b=el('div','bar'), tr=el('div','bar-track');
      var fa=el('div','bar-fill claim'); fa.style.width='0%'; fa.dataset.w=100; tr.appendChild(fa);
      mark(tr, r.a/r.b*100);
      b.appendChild(tr); b.appendChild(el('span','bar-val',fill(T.times,{n:num(r.b/r.a,1)})));
      row.appendChild(b);
      row.appendChild(el('p','pair', r.ay+' <b>'+unit(r,r.a)+'</b> → '+r.by+' <b>'+shown+'</b>'));
    } else {
      row.appendChild(bar(r.b,'claim',shown));
      row.appendChild(el('p','pair', r.by+' · '+T.noMethod));
    }
    right.appendChild(row);
  });
  root.appendChild(left); root.appendChild(right);
  watch(root.parentNode);
})();

/* ── 02: куда ушло время одного сообщения ────────────────────────────── */
(function(){
  var root=$('split'); if(!root) return;
  var F=DATA.foley, max=Math.max(F.v.total, F.k.total);
  [['v',T.voice],['k',T.keys]].forEach(function(p){
    var d=F[p[0]], row=el('div','row');
    row.appendChild(el('p','row-lab',p[1]));
    var b=el('div','bar'), st=el('div','stack');
    var a=el('span','prep '+p[0]); a.style.width='0%'; a.dataset.w=d.prep/max*100;
    var c=el('span','rest '+p[0]); c.style.width='0%'; c.dataset.w=(d.total-d.prep)/max*100;
    a.title=T.prep+': '+fill(T.sec,{n:num(d.prep,1)});
    c.title=T.entry+': '+fill(T.sec,{n:num(d.total-d.prep,1)});
    st.appendChild(a); st.appendChild(c); b.appendChild(st);
    b.appendChild(el('span','bar-val',fill(T.sec,{n:num(d.total)})));
    row.appendChild(b);
    row.appendChild(el('p','pair', T.prep+' <b>'+fill(T.sec,{n:num(d.prep,1)})+'</b>'));
    root.appendChild(row);
  });
  root.appendChild(el('p','split-legend','<span><i></i>'+T.prep+'</span><span><i class="full"></i>'+T.entry+'</span>'));
  watch(root.parentNode);
})();

/* ── 02: замер «рот против пальцев» ──────────────────────────────────── */
/* Два секундомера над одним предложением. Первый идёт от первой клавиши до
   Enter, второй — пока нажата кнопка, под которую читатель читает то же
   предложение вслух. Микрофон не включается: страница ничего не слышит, она
   только меряет время, и из двух времён выходят две скорости. */
(function(){
  var box=$('typeBox'); if(!box) return;
  var phrase=$('phrase').textContent.trim(), chars=phrase.length;
  var hold=$('holdBtn'), again=$('againBtn'), msg=$('labMsg'), rates=$('rates'), sum=$('labSum');
  var c1=$('clock1'), c2=$('clock2'), s1=$('step1'), s2=$('step2'), hint=$('holdHint');
  var res=$('labRes'), rT=$('resType'), rS=$('resSpeak');
  var t0=0, typed=null, spoken=null, h0=0, pasted=false, raf=0;

  function norm(x){ return x.toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim(); }
  /* Слово в скорости печати — это пять знаков: так считают Ruan и Foley.
     В китайском и японском знак почти слово, и деление на пять занизило бы
     скорость впятеро; там слова в предложении считает сегментатор браузера. */
  var perWord=5;
  if(CJK){
    var nw=0;
    try{ nw=Array.from(new Intl.Segmenter(document.documentElement.lang,{granularity:'word'}).segment(phrase))
      .filter(function(x){ return x.isWordLike; }).length; }catch(e){}
    perWord = nw ? chars/nw : 2;
  }
  function wpm(n, ms){ return (n/perWord)/(ms/60000); }
  function sec(ms){ return fill(T.sec,{n:num(ms/1000,1)}); }
  function tick(){
    if(t0 && typed==null) c1.textContent=sec(performance.now()-t0);
    if(h0) c2.textContent=sec(performance.now()-h0);
    if(!((t0 && typed==null) || h0)){ clearInterval(raf); raf=0; }
  }
  /* Обычный таймер, а не requestAnimationFrame: тот замирает, когда вкладка
     в фоне, и секундомер стоял бы на нуле, хотя время идёт. */
  function run(){ if(!raf) raf=setInterval(tick, 100); }

  function draw(){
    rates.innerHTML='';
    var rows=DATA.rates.map(function(r){ return {lab:T.rates[r.k], v:r.v, who:r.who}; });
    if(typed) rows.push({lab:T.youType, v:typed, who:'k', me:true});
    if(spoken) rows.push({lab:T.youSpeak, v:spoken, who:'v', me:true});
    rows.sort(function(a,b){ return b.v-a.v; });
    var max=Math.max(200, Math.min(260, rows[0].v));
    rows.forEach(function(r){
      var row=el('div','row'+(r.me?' me':''));
      row.appendChild(el('p','row-lab',r.lab));
      row.appendChild(bar(r.v/max*100, r.who==='k'?'keys':'', fill(T.wpm,{n:num(Math.round(r.v))})));
      rates.appendChild(row);
    });
    grow(rates);
    res.hidden = !(typed||spoken);
    rT.textContent = typed ? num(Math.round(typed)) : '—';
    rS.textContent = spoken ? num(Math.round(spoken)) : '—';
    sum.innerHTML='';
    if(typed && spoken){
      var ratio=spoken/typed, F=DATA.foley;
      var kept=(F.k.total/F.v.total)/(F.v.rate/F.k.rate);        /* 1.40 из 3.32 */
      var s_=ratio*kept;
      sum.innerHTML = ratio<1.15 ? T.ratioSlow
        : s_<1.05 ? fill(T.ratioLoss,{r:num(ratio,1)})
        : fill(T.ratioYou,{r:num(ratio,1), s:num(s_,1)});
    }
  }

  box.addEventListener('input', function(){ if(!t0 && box.value.length){ t0=performance.now(); run(); } });
  box.addEventListener('paste', function(){ pasted=true; });
  box.addEventListener('keydown', function(e){
    /* Enter, которым китайская или японская раскладка подтверждает иероглиф,
       не конец набора. */
    if(e.key!=='Enter' || e.isComposing || e.keyCode===229) return;
    e.preventDefault();
    if(!t0 || box.value.trim().length<chars*0.5){ msg.textContent=T.typeMore; return; }
    var ms=performance.now()-t0, v=wpm(box.value.trim().length, ms);
    /* Быстрее 220 слов в минуту не печатает никто: это вставка из буфера
       или автозаполнение, и такое число испортило бы всё сравнение. */
    if(pasted || v>220){ msg.textContent=T.tooFast; t0=0; pasted=false; box.value=''; c1.textContent=sec(0); return; }
    typed=v; c1.textContent=sec(ms);
    msg.textContent = norm(box.value)!==norm(phrase) ? T.typedWrong : '';
    box.disabled=true; s1.classList.add('done'); s2.classList.remove('off');
    hold.disabled=false; hint.textContent=T.holdReady; hold.focus();
    draw();
  });

  function start(e){
    if(hold.disabled || h0) return;
    if(e) e.preventDefault();
    h0=performance.now(); hold.classList.add('on'); hint.textContent=T.holdNow; run();
  }
  function stop(){
    if(!h0) return;
    var ms=performance.now()-h0; h0=0; hold.classList.remove('on'); c2.textContent=sec(ms);
    /* Меньше полутора секунд — это не чтение предложения из 19 слов вслух. */
    if(ms<1500){ msg.textContent=T.tooShort; hint.textContent=T.holdReady; return; }
    msg.textContent=''; hint.textContent=T.holdAgain;
    spoken=wpm(chars, ms); s2.classList.add('done');
    draw();
  }
  hold.addEventListener('pointerdown', function(e){ hold.setPointerCapture && hold.setPointerCapture(e.pointerId); start(e); });
  hold.addEventListener('pointerup', stop);
  hold.addEventListener('pointercancel', stop);
  hold.addEventListener('contextmenu', function(e){ e.preventDefault(); });
  document.addEventListener('keydown', function(e){
    if(e.code!=='Space' || e.repeat || hold.disabled) return;
    var t=e.target; if(t && (t.tagName==='TEXTAREA' || t.tagName==='INPUT')) return;
    if(!$('lab').contains(t) && t!==document.body) return;
    start(e);
  });
  document.addEventListener('keyup', function(e){ if(e.code==='Space') stop(); });

  again.addEventListener('click', function(){
    t0=0; typed=null; spoken=null; pasted=false; box.disabled=false; box.value='';
    hold.disabled=true; hint.textContent=T.holdWait; c1.textContent=sec(0); c2.textContent=sec(0);
    s1.classList.remove('done'); s2.classList.remove('done'); s2.classList.add('off');
    msg.textContent=''; draw(); box.focus();
  });
  c1.textContent=sec(0); c2.textContent=sec(0);
  draw();
  watch($('lab'));
})();

/* ── 03: лестница ошибок и одно предложение ──────────────────────────── */
(function(){
  var root=$('ladder'); if(!root) return;
  var words=T.werWords, out=$('heard'), cnt=$('heardCount'), hb=$('halluBtn');
  var cur='whisper', hallu=false;
  var max=Math.max.apply(null, DATA.wer.map(function(r){ return r.v; }));

  function esc(s){ var d=document.createElement('div'); d.textContent=s; return d.innerHTML; }
  function render(){
    var r=DATA.wer.filter(function(x){ return x.k===cur; })[0];
    var n=words.length, e=Math.max(1, Math.round(n*r.v/100));
    out.innerHTML=words.map(function(w){
      return w[2]<=e ? '<span class="miss" title="'+esc(w[0])+'">'+esc(w[1])+'</span>' : esc(w[0]);
    }).join(SEP)+(hallu ? SEP+'<span class="made">'+T.hallu+'</span>' : '');
    cnt.textContent=fill(T.werErrors,{e:e, n:n});
    [].forEach.call(root.children, function(b){ b.setAttribute('aria-checked', b.dataset.k===cur ? 'true':'false'); });
  }
  DATA.wer.forEach(function(r){
    var b=el('button','rung');
    b.type='button'; b.setAttribute('role','radio'); b.dataset.k=r.k;
    b.appendChild(el('span','',T.wer[r.k]));
    var tr=el('span','bar-track'), f=el('span','bar-fill'); f.style.width='0%'; f.dataset.w=r.v/max*100;
    tr.appendChild(f); b.appendChild(tr);
    b.appendChild(el('span','bar-val',pct(r.v)));
    b.addEventListener('click', function(){ cur=r.k; render(); });
    root.appendChild(b);
  });
  root.addEventListener('keydown', function(e){
    if(['ArrowDown','ArrowUp','ArrowRight','ArrowLeft'].indexOf(e.key)<0) return;
    e.preventDefault();
    var ks=DATA.wer.map(function(x){ return x.k; }), i=ks.indexOf(cur);
    i=(i+(e.key==='ArrowDown'||e.key==='ArrowRight'?1:-1)+ks.length)%ks.length;
    cur=ks[i]; render(); root.children[i].focus();
  });
  hb.addEventListener('click', function(){ hallu=!hallu; hb.setAttribute('aria-pressed', hallu?'true':'false'); render(); });
  render();
  watch(root.parentNode);
})();

/* ── 04: спектр задач ────────────────────────────────────────────────── */
(function(){
  var root=$('spec'); if(!root) return;
  root.appendChild(el('li','spec-end',T.specCopyEnd));
  DATA.spectrum.forEach(function(r){
    if(r.k==='ld') root.appendChild(el('li','spec-end',T.specThinkEnd));
    var li=el('li','e'+r.e+(r.k==='ld'?' extra':''));
    var meta=(r.n ? fill(T.nPeople,{n:r.n.toLocaleString(document.documentElement.lang)}) : T.nNa)+' · '+r.y+(r.k==='ld' ? ' · '+T.specExtra : '');
    li.innerHTML=T.spec[r.k]+'<small>'+meta+'</small>';
    root.appendChild(li);
  });
  watch(root.parentNode);
})();

/* ── 04: промпты, 919 студентов ──────────────────────────────────────── */
(function(){
  var root=$('prompts'); if(!root) return;
  var top=70;
  DATA.prompts.forEach(function(p){
    var g=el('div','pgroup');
    g.appendChild(el('h4','',fill(T.prompt,{p:p.p})));
    var cols=el('div','pcols');
    [['text',p.text],['raw',p.raw],['edit',p.edit]].forEach(function(c){
      var col=el('div','pcol '+c[0]);
      col.appendChild(el('span','',pct(c[1])));
      var i=el('i'); i.style.height='0%'; i.dataset.h=c[1]/top*100;
      col.appendChild(i); cols.appendChild(col);
    });
    g.appendChild(cols); root.appendChild(g);
  });
  var leg=el('p','plegend',
    '<span><i style="background:var(--keys)"></i>'+T.pText+'</span>'+
    '<span><i style="background:rgba(var(--voice-rgb),.4)"></i>'+T.pRaw+'</span>'+
    '<span><i style="background:var(--voice)"></i>'+T.pEdit+'</span>');
  root.parentNode.insertBefore(leg, root.nextSibling);

  var ch=$('choice'), C=DATA.choice;
  ch.appendChild(el('p','choice-h',T.choiceH));
  var cb=el('div','choice-bar');
  [['c-text',C.text,T.cText],['c-both',C.both,''],['c-voice',C.voice,'']].forEach(function(s){
    var sp=el('span',s[0], s[2] ? pct(s[1])+' '+s[2] : ''); sp.style.width=s[1]+'%'; cb.appendChild(sp);
  });
  ch.appendChild(cb);
  ch.appendChild(el('p','choice-leg',
    '<span>'+pct(C.text)+' '+T.cText+'</span><span>'+pct(C.both)+' '+T.cBoth+'</span><span>'+pct(C.voice)+' '+T.cVoice+'</span>'));
  watch(root.parentNode);
})();

/* ── 05: время фонации у учителей ────────────────────────────────────── */
(function(){
  var root=$('phon'); if(!root) return;
  var top=30;
  root.appendChild(el('p','phon-leg',
    '<span><i style="background:var(--voice)"></i>'+T.phonA+'</span>'+
    '<span><i style="background:rgba(var(--voice-rgb),.4)"></i>'+T.phonB+'</span>'));
  DATA.phon.forEach(function(r){
    var row=el('div','row');
    row.appendChild(el('p','row-lab',T.phon[r.k]));
    row.appendChild(bar(r.a/top*100,'',pct(r.a)));
    row.appendChild(bar(r.b/top*100,'was',pct(r.b,1)));
    root.appendChild(row);
  });
  watch(root.parentNode);
})();

/* ── 05: нагрузка и восстановление, SVG ──────────────────────────────── */
/* Рисуется в ширину колонки, а не масштабируется из одной картинки:
   сжатый до 343 px вид уменьшал подписи до шести пикселей. */
function responsive(root, draw){
  var w=0;
  function go(){
    var nw=Math.round(root.clientWidth); if(!nw || nw===w) return;
    w=nw; root.innerHTML=''; draw(Math.max(300, w));
  }
  go();
  var t; window.addEventListener('resize', function(){ clearTimeout(t); t=setTimeout(go, 150); });
}
(function(){
  var root=$('rec'); if(!root) return;
  var cap=root.parentNode.querySelector('figcaption').textContent;
  responsive(root, function(W){
    var H=250, L=44, R=14, Tp=34, B=78;
    var X=function(h){ return L+(W-L-R)*h/24; }, Y=function(p){ return Tp+(H-Tp-B)*(1-p/100); };
    var s=svgEl('svg',{viewBox:'0 0 '+W+' '+H, width:W, height:H, role:'img', 'aria-label':cap});
    var defs=svgEl('defs',{}), pat=svgEl('pattern',{id:'recHatch', width:8, height:8, patternUnits:'userSpaceOnUse', patternTransform:'rotate(45)'});
    pat.appendChild(svgEl('line',{x1:0,y1:0,x2:0,y2:8,'class':'hatchline'})); defs.appendChild(pat); s.appendChild(defs);
    s.appendChild(svgEl('rect',{x:X(0),y:Tp,width:X(2)-X(0),height:H-Tp-B,'class':'load'}));
    s.appendChild(svgEl('rect',{x:X(6),y:Tp,width:X(8)-X(6),height:H-Tp-B,'class':'band'}));
    s.appendChild(svgEl('rect',{x:X(14),y:Tp,width:X(20)-X(14),height:H-Tp-B,'class':'band'}));
    s.appendChild(svgEl('line',{x1:L,y1:H-B,x2:W-R,y2:H-B,'class':'axis'}));
    var step=W<460 ? 8 : 4;
    for(var h=0; h<=24; h+=step){
      var t=svgEl('text',{x:X(h),y:H-B+16,'text-anchor':'middle','class':'tick'}); t.textContent=h; s.appendChild(t);
    }
    var hl=svgEl('text',{x:W-R,y:H-B+32,'text-anchor':'end','class':'tick'}); hl.textContent=T.recHours; s.appendChild(hl);
    [0,50,90,100].forEach(function(p){
      if(W<460 && p===90) return;
      var t=svgEl('text',{x:L-6,y:Y(p)+4,'text-anchor':'end','class':'tick'}); t.textContent=pct(p); s.appendChild(t);
    });
    var path='M'+X(2)+','+Y(0)+' C'+X(3.5)+','+Y(55)+' '+X(5)+','+Y(84)+' '+X(7)+','+Y(90)
           +' S'+X(13)+','+Y(99)+' '+X(17)+','+Y(100)+' L'+X(24)+','+Y(100);
    s.appendChild(svgEl('path',{d:path,'class':'curve'}));
    s.appendChild(svgEl('circle',{cx:X(7),cy:Y(90),r:5,'class':'dot'}));
    s.appendChild(svgEl('circle',{cx:X(17),cy:Y(100),r:5,'class':'dot'}));
    function lab(x,y,txt,anchor,cls){ var t=svgEl('text',{x:x,y:y,'text-anchor':anchor||'start','class':'lab'+(cls?' '+cls:'')}); t.textContent=txt; s.appendChild(t); }
    lab(X(0)+2, Tp-10, T.recLoad, 'start', 'strong');
    lab(X(7)+9, Y(90)+22, T.rec90, 'start');
    lab(Math.min(X(17), W-R-4), Tp-10, T.rec100, W<460 ? 'end' : 'middle');
    s.appendChild(svgEl('rect',{x:L,y:H-B+42,width:W-L-R,height:22,rx:6,'class':'unk'}));
    lab(L+10, H-B+57, T.recUnknown, 'start', 'strong');
    root.appendChild(s);
  });
  watch(root.parentNode);
})();

/* ── 06: где и при ком вы бы заговорили ──────────────────────────────── */
(function(){
  var P=$('accPlaces'), Q=$('accPeople'); if(!P) return;
  var ans={}, shown=false, btnShow=$('accShow'), sum=$('accSum');
  function list(root, rows, names){
    rows.forEach(function(r){
      var li=el('li'), b=el('button','acc-btn');
      b.type='button';
      b.innerHTML='<span>'+names[r.k]+'</span><span class="ans">·</span>';
      b.addEventListener('click', function(){
        var s=ans[r.k]; ans[r.k] = s==null ? 'yes' : s==='yes' ? 'no' : null;
        b.className='acc-btn'+(ans[r.k] ? ' '+ans[r.k] : '');
        b.querySelector('.ans').textContent = ans[r.k] ? T[ans[r.k]] : '·';
        b.setAttribute('aria-pressed', ans[r.k]==='yes' ? 'true' : ans[r.k]==='no' ? 'mixed' : 'false');
        summary();
      });
      b.setAttribute('aria-pressed','false');
      li.appendChild(b);
      var st=el('div','acc-study');
      st.appendChild(bar(r.v,'',pct(r.v)+' '+T.voiceOk));
      st.appendChild(bar(r.t,'keys',pct(r.t)+' '+T.textOk));
      li.appendChild(st);
      root.appendChild(li);
    });
  }
  list(P, DATA.accept.places, T.places);
  list(Q, DATA.accept.people, T.people);
  function summary(){
    var y=0, n=0; for(var k in ans){ if(ans[k]){ n++; if(ans[k]==='yes') y++; } }
    sum.innerHTML = n ? fill(T.acceptSum,{y:y, n:n}) : (shown ? '' : T.acceptNone);
  }
  btnShow.addEventListener('click', function(){
    shown=!shown;
    P.classList.toggle('show', shown); Q.classList.toggle('show', shown);
    btnShow.textContent = shown ? btnShow.dataset.hide : btnShow.dataset.show;
    if(shown){ grow(P); grow(Q); }
    summary();
  });
  summary();
  watch($('accept'));
})();

/* ── 07: три недели с колонкой ───────────────────────────────────────── */
(function(){
  var root=$('habit'); if(!root) return;
  var H=DATA.habit, cap=root.parentNode.querySelector('figcaption').textContent;
  var plot=el('div','habit-plot'), conf=el('div','habit-conf');
  conf.innerHTML='<span class="habit-confv">'+T.sevenOfSeven+'</span><span>'+T.habitConf+'</span>';
  var top_=el('div','habit-top'); top_.appendChild(plot); top_.appendChild(conf); root.appendChild(top_);
  responsive(plot, function(W){
    var Ht=220, B=34, top=70, base=Ht-B, hmax=base-40;
    var gap=Math.max(14, W*0.06), colW=(W-2*gap)/3;
    var s=svgEl('svg',{viewBox:'0 0 '+W+' '+Ht, width:W, height:Ht, role:'img', 'aria-label':cap});
    function t(x,y,txt,cls,anchor){ var e=svgEl('text',{x:x,y:y,'class':cls,'text-anchor':anchor||'middle'}); e.textContent=txt; s.appendChild(e); }
    t(0, 14, T.habitCmd, 'lab', 'start');
    s.appendChild(svgEl('line',{x1:0,y1:base,x2:W,y2:base,'class':'axis'}));
    H.cmd.forEach(function(v,i){
      var x=i*(colW+gap), h=hmax*v/top;
      s.appendChild(svgEl('rect',{x:x,y:base-h,width:colW,height:h,rx:6,'class':'cmd'}));
      t(x+colW/2, base-h-8, num(v), 'val');
      t(x+colW/2, base+18, fill(T.week,{n:i+1}), 'tick');
    });
    plot.appendChild(s);
  });
  /* Доля музыки — отдельной строкой: на одной оси с числом команд
     она читалась как третья величина той же шкалы. */
  var mu=el('div','row habit-music');
  mu.appendChild(el('p','row-lab',T.habitMusic));
  H.music.forEach(function(v,i){
    if(v==null) return;
    mu.appendChild(bar(v/30*100,'',fill(T.week,{n:i+1})+' · '+pct(v)));
  });
  root.appendChild(mu);
  watch(root.parentNode);
})();

/* ── 08: текст или голосовое, по странам ─────────────────────────────── */
(function(){
  var root=$('pref'); if(!root) return;
  DATA.textPref.forEach(function(r){
    var row=el('div','row'+(r.k==='all'?' all':''));
    row.appendChild(el('p','row-lab',T.pref[r.k]));
    row.appendChild(bar(r.v,'',pct(r.v)));
    root.appendChild(row);
  });
  watch(root.parentNode);
})();

/* ── 08: звонок в автобусе, кино и на улице, пять культур ────────────── */
(function(){
  var chips=$('cplace'), root=$('phone'); if(!chips) return;
  var C=DATA.campbell, cur='bus';
  function render(){
    root.innerHTML='';
    var vals=C[cur], min=Math.min.apply(null, vals);
    C.cultures.forEach(function(k,i){
      var row=el('div','row'+(vals[i]===min?' low':''));
      row.appendChild(el('p','row-lab',T.cultures[k]));
      row.appendChild(bar((vals[i]-1)/4*100,'',num(vals[i],2)));
      root.appendChild(row);
    });
    [].forEach.call(chips.children, function(b){ b.setAttribute('aria-pressed', b.dataset.k===cur?'true':'false'); });
    requestAnimationFrame(function(){ grow(root); });
  }
  ['bus','cinema','sidewalk'].forEach(function(k){
    var b=el('button','chip',T.cplaces[k]); b.type='button'; b.dataset.k=k;
    b.addEventListener('click', function(){ cur=k; render(); });
    chips.appendChild(b);
  });
  render();
  watch(root.parentNode);
})();

/* ── короткая версия ─────────────────────────────────────────────────── */
(function(){
  var dlg=$('tldr'); if(!dlg) return;
  var timer;
  $('tldrOpen').addEventListener('click', function(){ dlg.showModal(); });
  $('tldrClose').addEventListener('click', function(){ dlg.close(); });
  dlg.addEventListener('click', function(e){ if(e.target===dlg) dlg.close(); });
  function flash(btn, text){
    var label=btn.querySelector('span'), was=label.textContent;
    btn.classList.add('done'); label.textContent=text;
    clearTimeout(timer);
    timer=setTimeout(function(){ btn.classList.remove('done'); label.textContent=was; }, 1800);
  }
  function copy(btn, text){
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(function(){ flash(btn, T.copied); }, fallback);
    } else fallback();
    function fallback(){
      var ta=document.createElement('textarea');
      ta.value=text; ta.setAttribute('readonly',''); ta.style.cssText='position:fixed;top:-1000px';
      document.body.appendChild(ta); ta.select();
      var ok=false; try{ ok=document.execCommand('copy'); }catch(e){}
      ta.remove(); flash(btn, ok ? T.copied : T.copyManual);
      if(!ok){ var r=document.createRange(); r.selectNodeContents($('tldrDoc'));
        var sel=getSelection(); sel.removeAllRanges(); sel.addRange(r); }
    }
  }
  [].forEach.call(document.querySelectorAll('[data-tldr-copy]'), function(btn){
    btn.addEventListener('click', function(){ copy(btn, btn.dataset.tldrCopy==='md' ? T.tldrMd : T.tldrText); });
  });
  var doc=$('tldrDoc'), home=doc.parentNode, root=document.documentElement;
  function restore(){ if(doc.parentNode!==home) home.appendChild(doc); root.removeAttribute('data-print'); }
  $('tldrPrint').addEventListener('click', function(){
    document.body.appendChild(doc); root.setAttribute('data-print','tldr'); window.print(); restore();
  });
  window.addEventListener('afterprint', restore);
})();

})();
