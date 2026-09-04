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
function signed(v){return (v>0?'+':'−')+pct(Math.abs(v).toFixed(1));}
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
  paintMatrix();
}

/* map */
/* Не `top`: на верхнем уровне классического скрипта это имя занято
   неперезаписываемым window.top, и присваивание молча не срабатывает. */
var biggest=DATA.slice().sort(function(a,b){return b[2]-a[2];}).slice(0,120);
var maxE=biggest[0][2], mt=document.getElementById('matrix'), mout=document.getElementById('mout');

/* Плитки собраны в четыре блока по категориям: россыпь вперемешку не отвечала
   ни на один вопрос, а так сразу виден объём каждой категории и кто в ней
   крупнейший. Клик по плитке уводит в поиск наверху — карта перестаёт быть
   тыканьем наугад и становится входом в персональный ответ. */
function tile(o){
  var side=Math.max(13,Math.round(Math.sqrt(o[2]/maxE)*74));
  return '<button class="tile" type="button" style="width:'+side+'px;height:'+side
       +'px;background:'+(CATCOL[o[5]]||'var(--ink-3)')+'" data-i="'+DATA.indexOf(o)
       +'" aria-label="'+fill(T.tileAria,{occ:o[0],cat:CATNAME[o[5]]||T.na})+'"></button>';
}
mt.innerHTML=[4,3,2,1].map(function(cat){
  var occ=biggest.filter(function(o){return o[5]===cat;});
  if(!occ.length)return '';
  var emp=occ.reduce(function(a,o){return a+o[2];},0);
  return '<div class="mgroup"><p class="mgh">'
    +'<i class="swatch sw" style="background:'+CATCOL[cat]+'"></i>'
    +'<b>'+T.catsHead[cat]+'</b>'
    +'<span class="n">'+fill(T.groupCount,{n:occ.length,emp:millions(emp)})+'</span>'
    +'<span class="n">'+fill(T.groupLargest,{list:occ.slice(0,3).map(function(o){return o[0];}).join(', ')})+'</span>'
    +'</p><div class="matrix">'+occ.map(tile).join('')+'</div></div>';
}).join('');

/* Профессия, выбранная в поиске, обводится на карте — иначе её там не найти. */
function paintMatrix(){
  var i=st.occ?String(DATA.indexOf(st.occ)):null;
  [].forEach.call(mt.querySelectorAll('.tile'),function(t){
    t.classList.toggle('on',t.dataset.i===i);
  });
}
function tileInfo(e){
  var t=e.target.closest('.tile'); if(!t)return;
  var o=DATA[+t.dataset.i];
  mout.innerHTML='<b>'+o[0]+'</b> — '+fill(T.tileLine,{
    emp:thousands(o[2]),cat:CATNAME[o[5]]||T.na,proj:signed(o[3])})
    +(o[7]>=0?fill(T.tileWomen,{pct:pct(o[7].toFixed(0))}):'');
}
mt.addEventListener('mouseover',tileInfo);
mt.addEventListener('focusin',tileInfo);
mt.addEventListener('click',function(e){
  var t=e.target.closest('.tile'); if(!t)return;
  tileInfo(e);
  var o=DATA[+t.dataset.i];
  st.occ=o; q.value=o[0]; hits.innerHTML=''; show();
  document.getElementById('res').scrollIntoView({block:'center'});
});

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
