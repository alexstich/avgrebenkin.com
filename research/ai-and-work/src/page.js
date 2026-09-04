/* Поведение страницы. Ни одной английской строки: всё, что видит читатель,
   приходит в T из strings/<язык>.json, а числа и профессии — в DATA. */

var SDEL={1:[0.0,1.8,-0.2,2.7,1.4,0.6],2:[2.3,3.1,0.7,4.2,3.2,1.0],3:[-3.0,-2.4,-1.3,1.6,2.7,1.3],4:[-3.0,-2.1,-1.6,1.3,1.9,0.4]};
var CATCOL={4:'var(--cat-4)',3:'var(--cat-3)',2:'var(--cat-2)',1:'var(--cat-1)'};
var AGES=T.ages;
var CATNAME=T.cats;      /* именительный: «очень высокая» */
/* Отдельный падеж для оборота «в профессиях ... уязвимости»: в русском,
   немецком и польском согласование внутри фразы одной формой не обходится. */
var st={occ:null,age:0,sex:'n'};

/* Подстановка {имя} в переведённую строку: у языков разный порядок слов,
   и склеивать куски конкатенацией нельзя — фраза должна приходить целой. */
function fill(s,vals){
  return s.replace(/\{(\w+)\}/g,function(_,k){return k in vals?vals[k]:'{'+k+'}';});
}

/* Доля занятости каждого пола, приходящаяся на категорию экспозиции. Считается
   из того же вшитого датасета по профессиям, где обследование даёт состав по
   полу — 282 из 825, но 117 из 170 миллионов занятых. Сходится с цифрой
   раздела 08: в высшей категории выходит 57,5 % женщин. */
var SEXSHARE=(function(){
  var f={1:0,2:0,3:0,4:0},m={1:0,2:0,3:0,4:0},tf=0,tm=0;
  DATA.forEach(function(o){
    if(o[7]<0||!f.hasOwnProperty(o[5]))return;
    var w=o[2]*o[7]/100;
    f[o[5]]+=w; tf+=w; m[o[5]]+=o[2]-w; tm+=o[2]-w;
  });
  function sh(src,total){var r={};for(var k in src)r[k]=src[k]/total*100;return r;}
  var women={word:T.wordWomen,nom:T.wordWomenNom,share:sh(f,tf)},
      men={word:T.wordMen,nom:T.wordMenNom,share:sh(m,tm)};
  women.other=men; men.other=women;
  return {f:women,m:men,n:null};
})();

/* Числа языка: разделитель разрядов даёт toLocaleString, десятичную запятую
   и пробел перед знаком процента — каталог. Знак минуса везде U+2212, как
   в наборе статьи, а не дефис. */
function num(n){return n.toLocaleString(T.numLocale);}
function dec(s){return String(s).replace('.',T.decimal);}
function pct(v){return fill(T.percent,{n:dec(v)});}
function signed(v){return (v>0?'+':v<0?'−':'')+pct(Math.abs(v).toFixed(1));}
function thousands(n){return fill(T.thousands,{n:num(Math.round(n/1000))});}
function millions(n){return fill(T.millions,{n:dec((n/1e6).toFixed(1))});}

var q=document.getElementById('q'), hits=document.getElementById('hits');
function list(a){
  hits.innerHTML='';
  a.slice(0,7).forEach(function(o){
    var li=document.createElement('li'),b=document.createElement('button');
    b.type='button';
    b.innerHTML='<span>'+o[0]+'</span><span class="n">'+thousands(o[2])+'</span>';
    b.onclick=function(){st.occ=o;q.value=o[0];hits.innerHTML='';show();};
    li.appendChild(b);hits.appendChild(li);
  });
}
q.addEventListener('input',function(){
  var v=q.value.trim().toLowerCase();
  if(v.length<2){hits.innerHTML='';return;}
  list(DATA.filter(function(o){return o[0].toLowerCase().indexOf(v)>-1;}));
});
function chips(el,items,key){
  items.forEach(function(t,i){
    var b=document.createElement('button');
    b.type='button';b.className='chip';b.textContent=t.l;
    b.setAttribute('aria-pressed',String(key==='age'?i===0:t.v==='n'));
    b.onclick=function(){
      [].forEach.call(el.children,function(c){c.setAttribute('aria-pressed','false');});
      b.setAttribute('aria-pressed','true');st[key]=t.v;show();
    };
    el.appendChild(b);
  });
}
chips(document.getElementById('age'),AGES.map(function(a,i){return{l:a,v:i};}),'age');
chips(document.getElementById('sex'),[{l:T.sexAny,v:'n'},{l:T.sexWoman,v:'f'},{l:T.sexMan,v:'m'}],'sex');

function card(x){
  return '<div class="card"><span class="k">'+x.k+'</span><span class="v '+(x.cls||'')+'">'
       + x.v+'</span><span class="c">'+x.c+'</span></div>';
}
function show(){
  var o=st.occ; if(!o) return;
  document.getElementById('res').hidden=false;
  var cat=o[5],aei=o[6],w=o[7],chg=o[3];
  var c=[
    {k:T.cExposure,v:CATNAME[cat]||T.na,c:fill(T.cExposureNote,{soc:o[1]})},
    {k:T.cProjected,v:signed(chg),cls:chg<0?'dn':'up',c:T.cProjectedNote},
    {k:T.cEmployed,v:thousands(o[2]),c:fill(T.cEmployedNote,{wage:num(o[4])})}
  ];
  if(aei>=0)c.push({k:T.cTasks,v:pct((aei*100).toFixed(1)),c:T.cTasksNote});
  if(w>=0){
    var g=st.sex==='n'?T.cWomenPlain:((w>=50)===(st.sex==='f')?T.cWomenMajority:T.cWomenMinority);
    c.push({k:T.cWomen,v:pct(w.toFixed(0)),c:g+'<sup><a href="#s4">4</a></sup>'});
  }
  document.getElementById('cards').innerHTML=c.map(card).join('');

  /* Вторая сетка — единственная, которую двигают переключатели. Возраст берёт
     свою строку из той же панели, что и график ниже; пол — свою долю занятости
     в этой категории экспозиции, посчитанную из вшитого датасета. */
  var mine=(SDEL[cat]||SDEL[1])[st.age];
  var you=[{k:T.yAge,v:signed(mine),cls:mine<0?'dn':'up',
            c:fill(T.yAgeNote,{band:AGES[st.age]})}];
  var g=SEXSHARE[st.sex];
  if(g)you.push({k:fill(T.yWhere,{who:g.nom}),v:pct(g.share[cat].toFixed(1)),
    c:fill(T.yWhereNote,{who:g.word,cat:T.catsGen[cat],other:g.other.word,
                         otherShare:pct(g.other.share[cat].toFixed(1))})});
  document.getElementById('youCards').innerHTML=you.map(card).join('');

  var s=SDEL[cat]||SDEL[1],max=3.2;
  document.getElementById('agePlot').innerHTML=s.map(function(v,i){
    var wd=Math.abs(v)/max*46,neg=v<0;
    return '<div class="lane'+(i===st.age?' hi':'')+'"><span class="lab">'+AGES[i]+'</span><span class="track"><span class="axis"></span><span class="bar'+(neg?' dn':'')+'" style="'+(neg?'right:50%':'left:50%')+';width:'+wd+'%"></span></span><span class="val">'+signed(v)+'</span></div>';
  }).join('');
  document.getElementById('afterPlot').innerHTML=T.afterPlot;
  paintRow();
}

/* ── лестница возрастов, раздел 04 ──────────────────────────────────
   Возраст выбирает читатель, строки — четыре категории уязвимости. Цвет
   полосы берётся из категории, а не из знака: направление от оси и так
   говорит, вверх это или вниз, а краска должна отвечать на другой вопрос —
   насколько профессия уязвима. Синего в шкале нет ни в одной теме. */
(function(){
  var box=document.getElementById('ladAge'), plot=document.getElementById('ladPlot'),
      note=document.getElementById('ladNote'), cur=0;
  /* 4.4 — чуть больше самого длинного значения панели (4,2). Общий предел
     на все шесть возрастов: пересчитывать его под выбранный возраст нельзя,
     иначе полосы прыгали бы в длине при неизменных числах. */
  var MAX=4.4;
  function draw(){
    plot.innerHTML=[4,3,2,1].map(function(c){
      var v=SDEL[c][cur], neg=v<0, wd=Math.abs(v)/MAX*46;
      return '<div class="lane"><span class="lab">'+T.catsHead[c]+'</span>'
        +'<span class="track"><span class="axis"></span><span class="bar'+(neg?' dn':'')
        +'" style="'+(neg?'right:50%':'left:50%')+';width:'+wd+'%;background:'+CATCOL[c]+'"></span></span>'
        +'<span class="val'+(v<0?' dn':v>0?' up':'')+'">'+signed(v)+'</span></div>';
    }).join('');
    note.innerHTML=fill(T.ladNote,{band:AGES[cur]});
  }
  AGES.forEach(function(a,i){
    var b=document.createElement('button');
    b.type='button'; b.className='chip'; b.textContent=a;
    b.setAttribute('aria-pressed',String(i===0));
    b.onclick=function(){
      [].forEach.call(box.children,function(c){c.setAttribute('aria-pressed','false');});
      b.setAttribute('aria-pressed','true'); cur=i; draw();
    };
    box.appendChild(b);
  });
  draw();
})();

/* ── таблица профессий, раздел 06 ───────────────────────────────────
   Все 825 профессий, а не 120 крупнейших, как было на карте. Сортировка
   по любой колонке, фильтр по названию, категория уязвимости — цветной
   меткой у имени. Профессия, выбранная поиском в разделе 05, подсвечивается
   строкой и подтягивается в видимую часть: связь карты с поиском была
   единственным, что стоило из неё сохранить. */
var paintRow;
(function(){
  var q2=document.getElementById('tq'), tn=document.getElementById('tn'),
      tb=document.getElementById('tb'), tth=document.getElementById('tth'),
      leg=document.getElementById('tleg'), box=document.querySelector('.occbox');
  var COLS=[['occ',0],['emp',2],['proj',3],['wage',4],['tasks',6]];
  var key=2, dir=-1, flt='', rows=[];

  q2.placeholder=T.tabPlaceholder;
  q2.setAttribute('aria-label',T.tabAria);

  leg.innerHTML=['emp','proj','wage','tasks','color','sort'].map(function(k){
    return '<li><b>'+T.tabLeg[k].k+'</b><span>'+T.tabLeg[k].v+'</span></li>';
  }).join('');

  function head(){
    tth.innerHTML='<tr>'+COLS.map(function(c,i){
      var on=c[1]===key;
      return '<th'+(i?' class="n"':'')+(on?' aria-sort="'+(dir<0?'descending':'ascending')+'"':'')
        +'><button type="button" class="sortb" data-k="'+c[1]+'">'+T.tabTh[c[0]]
        +'<i aria-hidden="true">'+(on?(dir<0?'\u2193':'\u2191'):'')+'</i></button></th>';
    }).join('')+'</tr>';
    [].forEach.call(tth.querySelectorAll('.sortb'),function(b){
      b.onclick=function(){
        var k=+b.dataset.k;
        dir=(k===key)?-dir:(k===0?1:-1); key=k; draw();
      };
    });
  }

  function draw(){
    rows=DATA.filter(function(o){return !flt||o[0].toLowerCase().indexOf(flt)>-1;});
    rows.sort(function(a,b){
      if(key===0)return dir*(a[0]<b[0]?-1:a[0]>b[0]?1:0);
      /* «нет данных» — это −1, и при сортировке по возрастанию такие строки
         вылезали бы вперёд настоящих нулей. Отправляем их всегда в конец. */
      var x=a[key],y=b[key];
      if(x<0&&y<0)return 0; if(x<0)return 1; if(y<0)return -1;
      return dir*(x-y);
    });
    tb.innerHTML=rows.length?rows.map(function(o){
      return '<tr data-i="'+DATA.indexOf(o)+'"><td class="nm">'
        +'<i class="swatch sw" style="background:'+(CATCOL[o[5]]||'var(--ink-3)')+'"></i>'
        +'<span>'+o[0]+'</span></td>'
        +'<td class="n">'+thousands(o[2])+'</td>'
        +'<td class="n '+(o[3]<0?'dn':o[3]>0?'up':'')+'">'+signed(o[3])+'</td>'
        +'<td class="n">'+num(o[4])+'</td>'
        +'<td class="n">'+(o[6]>=0?dec(o[6].toFixed(2)):T.na)+'</td></tr>';
    }).join(''):'<tr><td class="empty" colspan="5">'+T.tabEmpty+'</td></tr>';
    tn.textContent=fill(T.tabCount,{shown:num(rows.length),total:num(DATA.length)});
    head(); paintRow();
  }

  paintRow=function(){
    var i=st.occ?String(DATA.indexOf(st.occ)):null, hit=null;
    [].forEach.call(tb.querySelectorAll('tr'),function(t){
      var on=t.dataset.i===i;
      t.classList.toggle('on',on); if(on)hit=t;
    });
    /* Не scrollIntoView: он тянет за собой всю страницу к разделу 06,
       а читатель в этот момент смотрит на карточки раздела 05. Двигаем
       только внутренний скролл таблицы. */
    if(hit)box.scrollTop=hit.offsetTop-box.clientHeight/2+hit.offsetHeight/2;
  };

  q2.addEventListener('input',function(){
    flt=q2.value.trim().toLowerCase(); draw();
  });
  draw();
})();

/* Полоса под двумя числами: 1,2× от 474× — это 0,3 % шкалы, столько она и
   показывает. Ширина берётся из самих чисел, чтобы они не разошлись. */
(function(){
  var big=document.querySelectorAll('.cost-cell .big');
  var hi=parseFloat(big[0].textContent), lo=parseFloat(big[1].textContent);
  document.querySelector('.cost-fill').style.width=Math.max(lo/hi*100,0.4).toFixed(2)+'%';
})();

/* Короткая версия. Простой текст и Markdown собраны сборкой из тех же строк,
   что стоят в окне, — второй копии, которая разъедется с первой, здесь нет. */
(function(){
  var dlg=document.getElementById('tldr');
  var openBtn=document.getElementById('tldrOpen');
  var timer;

  openBtn.addEventListener('click',function(){ dlg.showModal(); });
  document.getElementById('tldrClose').addEventListener('click',function(){ dlg.close(); });
  /* Клик мимо карточки закрывает: у модального диалога фон — это сам dialog. */
  dlg.addEventListener('click',function(e){ if(e.target===dlg) dlg.close(); });

  function flash(btn,text){
    var label=btn.querySelector('span');
    var was=label.textContent;
    btn.classList.add('done'); label.textContent=text;
    clearTimeout(timer);
    timer=setTimeout(function(){ btn.classList.remove('done'); label.textContent=was; },1800);
  }
  function copy(btn,text){
    if(navigator.clipboard&&navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(function(){flash(btn,T.copied);},fallback);
    } else fallback();
    function fallback(){
      var ta=document.createElement('textarea');
      ta.value=text; ta.setAttribute('readonly','');
      ta.style.cssText='position:fixed;top:-1000px';
      document.body.appendChild(ta); ta.select();
      var ok=false; try{ ok=document.execCommand('copy'); }catch(e){}
      ta.remove(); flash(btn,ok?T.copied:T.copyManual);
      if(!ok){ var r=document.createRange(); r.selectNodeContents(document.getElementById('tldrDoc'));
        var sel=getSelection(); sel.removeAllRanges(); sel.addRange(r); }
    }
  }
  [].forEach.call(document.querySelectorAll('[data-tldr-copy]'),function(btn){
    btn.addEventListener('click',function(){
      copy(btn, btn.dataset.tldrCopy==='md'?T.tldrMd:T.tldrText);
    });
  });

  /* Печать одного листа: узел уезжает прямо в body, иначе его накрывают
     `overflow` диалога и правила печати всей статьи. */
  var doc=document.getElementById('tldrDoc'), home=doc.parentNode, root=document.documentElement;
  function restore(){
    if(doc.parentNode!==home) home.appendChild(doc);
    root.removeAttribute('data-print');
  }
  document.getElementById('tldrPrint').addEventListener('click',function(){
    document.body.appendChild(doc);
    root.setAttribute('data-print','tldr');
    window.print();
    restore();
  });
  window.addEventListener('afterprint',restore);
})();

/* Обложка вверху — единственная растровая графика на странице, и цвета в ней
   запечены. Всё остальное здесь живёт на CSS-переменных и переключается само,
   а этой нужен второй файл, поэтому страница и слушает themechange. Кибертема
   берёт тёмный вариант: у неё фон почти чёрный. */
var heroShot=document.getElementById('heroShot');
function heroSrc(){
  var light=document.documentElement.getAttribute('data-theme')==='light';
  var want=T.up+'../images/research/ai-and-work-hero'+(light?'-light':'')+'.webp';
  if(heroShot.getAttribute('src')!==want) heroShot.setAttribute('src',want);
}
document.addEventListener('themechange',heroSrc);
heroSrc();
