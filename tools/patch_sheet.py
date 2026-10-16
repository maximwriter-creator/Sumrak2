#!/usr/bin/env python3
"""Лист персонажа: «У меня уже есть персонаж» и режим правки листа с записью в историю.
   python3 patch_sheet.py app.html out.html   (применяется до patch_app.py)"""
import sys, pathlib
s = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
out = pathlib.Path(sys.argv[2])

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, f'не найдено ровно {count}: {old[:90]!r} ({s.count(old)})'
    s = s.replace(old, new)

if 'function sheetEditPanel' in s:
    sys.exit('Уже применено')

# ---- данные: правки листа хранятся отдельно, как модификаторы «Правка листа» ----
rep('manual:[], adj:{', 'manual:[], fix:{}, adj:{')
rep('  steps.manual = man;\n', '''  steps.manual = man;
  const fixo = {mods:[],notes:[],choices:[],pending:0};
  Object.entries(c.fix||{}).forEach(([k,v])=>{v=Number(v)||0;if(v){fixo.mods.push({k,v,src:"Правка листа"});ctx.apply(k,v);}});
  steps.fix = fixo;
''')
rep('"merits","manual"].forEach(s=>(R.steps[s]', '"merits","manual","fix"].forEach(s=>(R.steps[s]')

# ---- история: происхождение и производные значения, пометка «Правка листа» ----
rep('  const sets={"Снаряжение":', '''  o["Имя"]=C.name||null; o["Ранг талантов"]=C.rankLvl||null;
  o["Класс"]=R.cl?R.cl.variant+" ("+R.cl.group+")":null; o["Место рождения"]=R.vr?R.nat.name+" → "+R.vr.name:R.nat?R.nat.name:null;
  o["Родители"]=R.pr?R.pr.name:null; o["Характер"]=R.ch?R.ch.name:null; o["Отметка судьбы"]=R.mark?R.mark.name:null; o["Недостаток"]=R.fl?R.fl.name:null;
  o["Устойчивость"]=Math.max(0,Math.floor((R.tot.tou-1)/3))+(R.extra.res||0); o["Инициатива"]=2*R.tot.agi+(R.extra.ini||0);
  const sets={"Снаряжение":''')
rep('Object.keys(s.o).forEach(k=>{const a=prev.o[k],b=s.o[k];', 'Object.keys(s.o).forEach(k=>{if(!(k in prev.o))return;const a=prev.o[k],b=s.o[k];')
rep('C.history.unshift({t:Date.now(),items});', 'C.history.unshift(Object.assign({t:Date.now(),items},sheetEditOn()?{src:"Правка листа"}:{}));')
rep('return `<div class="entry"><div class="note">${ts}</div>', 'return `<div class="entry"><div class="note">${ts}${h.src?` · <b class="histsrc">${esc(h.src)}</b>`:""}</div>')

# ---- лист ----
rep('const statRows = TILE_ORDER.map(', 'const statRows = sheetEditOn()?sheetEditTiles(R,TILE_ORDER):TILE_ORDER.map(')
rep('<button class="btn" id="openNotes">${notesLabel()}</button>',
    '<button class="btn" id="openNotes">${notesLabel()}</button><button class="btn ${sheetEditOn()?"primary":""}" id="sheetEdit" aria-pressed="${sheetEditOn()}">${sheetEditOn()?"Готово":"Редактировать лист"}</button>${!C.legacy&&!isFinished(C)?`<button class="btn" data-legacy="1" title="Перенести готового персонажа: все этапы создания пропускаются, значения вписываются вручную">У меня уже есть персонаж</button>`:""}')
rep('  <div class="sheet" id="sheet">\n', '  ${sheetEditOn()?sheetEditPanel(R,res,ini):""}<div class="sheet" id="sheet">\n')
rep('Пропустить всё и открыть лист</button>`:""}', 'Пропустить всё и открыть лист</button><button class="btn small" data-legacy="1" title="Перенести готового персонажа и вписать его значения вручную">У меня уже есть персонаж</button>`:""}')
rep('function syncStepItems(R){\n', 'function syncStepItems(R){\n  if(C.legacy)return;  /* перенесённый персонаж: снаряжение только то, что вписал игрок */\n')
rep('[stClass,stStats,stBirth,stParents,stChar,stMark,stFlaw,stSheet,stAcademy,stDice,stMission,stRoom,stLore][STEP](R) + navBtns();',
    '[stClass,stStats,stBirth,stParents,stChar,stMark,stFlaw,stSheet,stAcademy,stDice,stMission,stRoom,stLore][STEP](R) + navBtns();\n  document.body.classList.toggle("sheetedit",sheetEditOn());')

js = r'''
/* ---------- Правка листа и перенос готового персонажа ---------- */
var SHEETEDIT=false;
function sheetEditOn(){try{return SHEETEDIT&&STEP===7;}catch(e){return false;}}
function sheetCur(R,k){
  if(k==="hp")return R.hp; if(k==="fate")return R.fate;
  if(k==="ini")return 2*R.tot.agi+(R.extra.ini||0);
  if(k==="res")return Math.max(0,Math.floor((R.tot.tou-1)/3))+(R.extra.res||0);
  return R.tot[k];
}
function sheetEditTiles(R,order){
  return order.map(k=>`<div class="stile sedit" data-ik="s:${k}"><label class="sedlab">${icon(k,"ico sico")}<span class="sname">${LABEL[k]}</span><input class="inp sedinp" type="number" inputmode="numeric" data-sfix="${k}" value="${R.tot[k]}" aria-label="${LABEL[k]}"></label></div>`).join("");
}
function sheetEditPanel(R,res,ini){
  const opt=(arr,cur,lab)=>`<option value="">—</option>`+arr.map((x,i)=>`<option value="${i}" ${cur===i?"selected":""}>${esc(lab(x))}</option>`).join("");
  const nat=C.birth.nation;
  const num=(k,label,v,ph)=>`<label>${label}<input class="inp" type="number" inputmode="numeric" data-sfix="${k}" value="${v==null?"":v}" placeholder="${ph||""}"></label>`;
  return `<div class="card sedpanel noprint">
  <div class="sedhead"><h3>Правка листа</h3><button class="btn primary" id="sheetEditDone">Готово</button></div>
  <p class="note">Впишите значения, как в бумажном листе: в итоговом листе будут именно они. Характеристики правятся прямо в плитках ниже, карма, опыт и влияние — в «Трекерах». Каждое изменение записывается в историю изменений.${C.legacy?" Снаряжение, таланты и заслуги добавьте в их разделах.":""}</p>
  <div class="sedgrid">
    <label>Класс<select class="sel" data-sedit="cls">${opt(BOOK.classes,C.cls.i,x=>x.variant+" ("+x.group+")")}</select></label>
    <label>Место рождения<select class="sel" data-sedit="nation">${opt(BOOK.births,nat,x=>x.name)}</select></label>
    ${nat!=null?`<label>Вариант места рождения<select class="sel" data-sedit="variant">${opt(BOOK.births[nat].variants,C.birth.variant,x=>x.name)}</select></label>`:""}
    <label>Родители<select class="sel" data-sedit="parents">${opt(BOOK.parents,C.parents.i,x=>x.name)}</select></label>
    <label>Характер<select class="sel" data-sedit="char">${opt(BOOK.chars,C.char.i,x=>x.name)}</select></label>
    <label>Отметка судьбы<select class="sel" data-sedit="mark">${opt(BOOK.fates,C.mark.i,x=>x.name)}</select></label>
    <label>Недостаток<select class="sel" data-sedit="flaw">${opt(BOOK.flaws,C.flaw.on?C.flaw.i:null,x=>x.name)}</select></label>
    ${num("hp","Очки здоровья (максимум)",C.stats.hp!=null?R.hp:null,"не указаны")}
    ${num("fate","Очки судьбы (всего)",C.stats.fate!=null?R.fate:null,"не указаны")}
    ${num("res","Устойчивость",res)}
    ${num("ini","Инициатива (без d20)",ini)}
  </div></div>`;
}
/* значения, которые игрок видит в листе; при смене класса и т. п. они не должны «уезжать» */
function sheetVals(R){const v={};SKEYS.forEach(k=>v[k]=R.tot[k]);v.hp=R.hp;v.fate=R.fate;v.ini=R.extra.ini||0;v.res=R.extra.res||0;["light","dark","ins","infl","xp"].forEach(k=>v["t:"+k]=R.extra[k]||0);return v;}
function keepSheetVals(mutate){
  const a=sheetVals(compute(C)); mutate(); const b=sheetVals(compute(C));
  C.fix=C.fix||{};
  Object.keys(a).forEach(k=>{const d=a[k]-b[k];if(!d)return;
    if(k.startsWith("t:")){const t=k.slice(2);C.adj[t]=(Number(C.adj[t])||0)+d;return;}
    if((k==="hp"&&C.stats.hp==null)||(k==="fate"&&C.stats.fate==null))return;
    C.fix[k]=(Number(C.fix[k])||0)+d;if(!C.fix[k])delete C.fix[k];});
}
function rerenderKeepFocus(){
  const a=document.activeElement, ds=a&&a.dataset||{};
  const key=ds.sfix?["sfix",ds.sfix]:ds.sedit?["sedit",ds.sedit]:ds.trk?["trk",ds.trk]:null;
  render();
  if(key){const el=document.querySelector(`[data-${key[0]}="${key[1]}"]`);if(el){try{el.focus({preventScroll:true});if(el.select)el.select();}catch(e){}}}
}
document.addEventListener("click",e=>{
  const b=e.target.closest("#sheetEdit,#sheetEditDone,[data-legacy],#dlSheet,#printBtn");if(!b)return;
  if(b.id==="dlSheet"||b.id==="printBtn"){if(SHEETEDIT){SHEETEDIT=false;render();}return;}  /* в файл и печать — без полей ввода */
  if(b.dataset.legacy){
    C.skip=C.skip||{};[0,1,2,3,4,5,6].forEach(i=>C.skip[i]=true);
    C.reopen=false;C.finished=true;C.legacy=true;
    if(C.stats.hp==null)C.stats.hp=0; if(C.stats.fate==null)C.stats.fate=0;
    C._snap=null; SHEETEDIT=true; STEP=7; render(); scrollTo(0,0);
    toast("Впишите значения своего персонажа — они сразу попадут в лист");return;
  }
  SHEETEDIT=b.id==="sheetEdit"?!SHEETEDIT:false;
  render();
  if(SHEETEDIT){const p=document.querySelector(".sedpanel");if(p)p.scrollIntoView({block:"start",behavior:"smooth"});toast("Правка листа: изменения пишутся в историю");}
  else toast("Правка листа закончена");
},true);
document.addEventListener("change",e=>{
  const t=e.target, d=t.dataset||{};
  if(d.sfix){
    e.stopPropagation();
    if(t.value==="")return; const val=Math.round(Number(t.value)); if(!Number.isFinite(val))return;
    const k=d.sfix;
    if(k==="hp"&&C.stats.hp==null)C.stats.hp=0; if(k==="fate"&&C.stats.fate==null)C.stats.fate=0;
    const R=compute(C), diff=val-sheetCur(R,k);
    if(diff){C.fix=C.fix||{};C.fix[k]=(Number(C.fix[k])||0)+diff;if(!C.fix[k])delete C.fix[k];}
    setTimeout(rerenderKeepFocus,0);return;
  }
  if(d.sedit){
    e.stopPropagation();
    const v=t.value===""?null:Number(t.value), k=d.sedit;
    const STEPOF={cls:0,nation:2,variant:2,parents:3,char:4,mark:5,flaw:6};
    keepSheetVals(()=>{
      if(k==="cls")C.cls={i:v,ans:{}};
      if(k==="nation")C.birth={d66:null,nation:v,variant:null,ans:{}};
      if(k==="variant"){C.birth.variant=v;C.birth.ans={};}
      if(k==="parents")C.parents={roll:null,i:v,ans:{}};
      if(k==="char")C.char={roll:null,i:v,ans:{}};
      if(k==="mark")C.mark={roll:null,i:v};
      if(k==="flaw")C.flaw={on:v!=null,roll:null,i:v,ans:{}};
    });
    C.skip=C.skip||{}; C.skip[STEPOF[k]]=true;
    setTimeout(rerenderKeepFocus,0);return;
  }
},true);
'''
rep('/* ---------- Комната мастера (Supabase) ---------- */', js + '/* ---------- Комната мастера (Supabase) ---------- */')

css = r'''
/* ---- Правка листа ---- */
.sedpanel{border:2px solid var(--accent);margin:0 0 16px}
.sedhead{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
.sedhead h3{margin:0}
.sedgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px 14px;margin-top:10px}
.sedgrid label{display:flex;flex-direction:column;gap:4px;font-size:14px;color:var(--muted);min-width:0}
.sedgrid .sel,.sedgrid .inp{width:100%;min-width:0;color:var(--ink);box-sizing:border-box}
.stile.sedit .sedlab{display:grid;grid-template-columns:22px minmax(0,1fr);row-gap:6px;column-gap:7px;align-items:center;min-height:86px;padding:10px;border-radius:6px;background:var(--soft);box-shadow:0 0 0 2px var(--accent);box-sizing:border-box;font-family:var(--narrow);text-transform:uppercase;letter-spacing:.02em}
.stile.sedit .sname{white-space:normal;hyphens:auto;line-height:1.1;font-size:clamp(14px,4.2vw,22px);min-width:0}
@media (max-width:420px){.stile.sedit .sico{display:none}.stile.sedit .sedlab{grid-template-columns:minmax(0,1fr)}.stile.sedit .sname{font-size:14px;letter-spacing:0;text-transform:none;overflow-wrap:anywhere}}
.stile.sedit .sedinp{grid-column:1/-1;width:100%;font-size:24px;font-weight:700;padding:4px 8px;box-sizing:border-box;font-family:var(--sans)}
body.sheetedit .dbtn[data-rollres],body.sheetedit .dbtn[data-rollini]{display:none}
.histsrc{color:var(--accent);font-weight:700}
@media print{.sedpanel{display:none!important}}
</style>'''
i = s.index('</style>', s.index('<title>Сумрак 2096'))
s = s[:i] + css + s[i + len('</style>'):]
out.write_text(s, encoding='utf-8')
print('ok', out, len(s))
