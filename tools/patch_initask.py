#!/usr/bin/env python3
"""Бой: мастер нажимает «Бой!», игроки комнаты сами бросают инициативу у себя,
   результаты собираются в таблицу очерёдности. Мастер отдельно бросает за бестиарий
   и при необходимости — за игроков, которые не бросили.
   Бросок игрока уходит через его лист (C.iniRoll {t,r,base,ini,agi,d100}, t = id боя) —
   новых таблиц/колонок на сервере не нужно.
   python3 patch_initask.py in.html out.html   (после patch_bestiary.py, до patch_app.py)"""
import sys, pathlib
s = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
out = pathlib.Path(sys.argv[2])

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, f'не найдено ровно {count}: {old[:90]!r} ({s.count(old)})'
    s = s.replace(old, new)

if 'function initMerge' in s:
    sys.exit('Уже применено')

# мастер: после каждого обновления списка игроков — подхватить их броски
rep('ROOM.mods[rmKey(r)]=r.mods||[]);ROOM.err="";roomCheckUid();}catch(e){ROOM.err=roomErr(e);}roomRefresh();renderRoomBtn();}',
    'ROOM.mods[rmKey(r)]=r.mods||[]);ROOM.err="";roomCheckUid();try{initMerge();}catch(e){}}catch(e){ROOM.err=roomErr(e);}roomRefresh();renderRoomBtn();}')

# общий вид для игроков: флаг сбора бросков (виден, даже если порядок скрыт)
rep('if(I.show===false)return {t:I.t,off:true};\n  return {t:I.t,round:I.round,cur:I.cur,',
    'if(I.show===false)return {t:I.t,off:true,ask:I.ask?1:0};\n  return {t:I.t,ask:I.ask?1:0,go:I.moved?1:0,round:I.round,cur:I.cur,')

# игрок: тост о начале боя
rep('''toast(`Инициатива: вы ходите ${me+1}-м из ${list.length}, действий ${r.act}`);''',
    '''if(!v.ask)toast(`Инициатива: вы ходите ${me+1}-м из ${list.length}, действий ${r.act}`);''')
rep('''else toast("Мастер бросил инициативу");}''',
    '''else toast(v.ask?"Бой! Бросьте инициативу":"Мастер бросил инициативу");}''')
rep('if(!initial&&!v.off&&list.length){', 'if(!initial&&v.ask&&v.off&&(!old||old.t!==v.t))toast("Бой! Бросьте инициативу");\n  if(!initial&&!v.off&&(list.length||v.ask)){')
rep('''  try{roomRefresh();}catch(e){}}
function iniRollTxt''', '''  try{roomRefresh();}catch(e){}try{iniAskBar();}catch(e){}}
function iniRollTxt''')

# старую карточку инициативы мастера и блок игрока заменяем целиком
a = s.index('function initCard(){')
b = s.index('document.addEventListener("click",e=>{const b=e.target.closest("[data-ini]")')
s = s[:a] + r'''function iniNpcN(){return bestS().list.filter(n=>n.on).reduce((a,n)=>a+n.qty,0);}
function iniHas(I,p){return I.list.some(r=>r.k==="p"&&r.u===p.uid&&r.who===p.char_id);}
function iniPending(I){return I?(ROOM.players||[]).filter(p=>!iniHas(I,p)):[];}
function iniResort(I,c){I.list.sort(iniSort);if(!I.moved||!c){I.cur=0;return;}const i=I.list.indexOf(c);I.cur=i<0?0:i;}
function iniPRow(p,x,v){return {k:"p",n:p.name||"Без имени",u:p.uid,who:p.char_id,base:x.base,r:x.r,ini:x.ini,agi:x.agi,d100:x.d100,ab:ACT_BASE,act:iniActs(x.r,ACT_BASE),hp:v&&!v.err?v.hpCur:null,hpMax:v&&!v.err?v.hpMax:null,gm:!!x.gm};}
function iniRollFor(v){let r=rnd(20);const mk=v.s&&v.s.mark&&v.s.mark.i!=null&&BOOK.fates[v.s.mark.i]?BOOK.fates[v.s.mark.i].name:"";
  if(mk==="Аура удачи"&&r===3)r=2;if(mk==="Аура неудачи"&&r===18)r=19;return {r,base:v.ini,ini:v.ini-r,agi:v.R.tot.agi,d100:rnd(100)};}
/* мастер: подхватить броски игроков из их листов */
function initMerge(){const I=ROOM.init;if(!gmIsMaster()||!I||!I.ask)return;const got=[],cur0=I.list[I.cur];
  (ROOM.players||[]).forEach(p=>{const x=p.sheet&&p.sheet.iniRoll;if(!x||x.t!==I.t||iniHas(I,p))return;
    const v=roomPeek(p.sheet,ROOM.mods[rmKey(p)]||[]);I.list.push(iniPRow(p,x,v));got.push(`${p.name||"Без имени"} ${x.ini}`);});
  if(!got.length)return;iniResort(I,cur0);initSave(true);
  const left=iniPending(I).length;toast(`Инициатива: ${got.join(", ")}`+(left?` · ждём ещё ${left}`:" · все игроки бросили ✓"));}
function initStart(){const show=ROOM.init?ROOM.init.show!==false:true;
  ROOM.init={t:Date.now(),round:1,cur:0,list:[],show,ask:1};initNpcRoll(true);initSave(true);
  toast("Бой! Игроки получили запрос на инициативу"+(iniNpcN()?`, бестиарий брошен (${iniNpcN()})`:""));renderRoom();}
function initNpcRoll(quiet){const I=ROOM.init;if(!I)return;const rows=[];
  bestS().list.filter(n=>n.on).forEach(n=>{for(let q=1;q<=n.qty;q++){const base=npcIni(n),r=rnd(20),ab=Math.max(1,npcEff(n,"act")),hm=npcEff(n,"hp");
    rows.push({k:"npc",id:n.id,n:(n.name||"Без имени")+(n.qty>1?" "+q:""),sec:n.secret,base,r,ini:base-r,agi:npcEff(n,"agi"),d100:rnd(100),ab,act:iniActs(r,ab),hp:hm,hpMax:hm});}});
  if(!rows.length){if(!quiet)toast("В бестиарии никто не отмечен «В бою»");return;}
  const c=I.list[I.cur];I.list=I.list.filter(r=>r.k!=="npc");I.list.push(...rows);
  iniResort(I,c&&c.k==="npc"?null:c);
  try{gmRollPush("Инициатива бестиария: "+rows.map(r=>`${r.sec?"???":r.n} ${r.ini}`).join(", "));}catch(e){}
  if(!quiet){initSave(true);toast(`Бестиарий брошен: ${rows.length}`);renderRoom();}}
function initGmFor(list){const I=ROOM.init;if(!I)return;const cur0=I.list[I.cur];const skip=[],done=[];
  list.forEach(p=>{if(iniHas(I,p))return;const v=roomPeek(p.sheet,ROOM.mods[rmKey(p)]||[]);if(v.err){skip.push(p.name||"Без имени");return;}
    const x={...iniRollFor(v),gm:true};I.list.push(iniPRow(p,x,v));done.push(`${p.name||"Без имени"} ${x.ini}`);});
  if(done.length){iniResort(I,cur0);initSave(true);try{gmRollPush("Инициатива за игроков: "+done.join(", "));}catch(e){}}
  toast((done.length?`Брошено за: ${done.join(", ")}`:"Никого не бросили")+(skip.length?`. Не удалось прочитать лист: ${skip.join(", ")}`:""));renderRoom();}
function initCard(){const I=ROOM.init,np=(ROOM.players||[]).length,nb=iniNpcN(),pend=iniPending(I);
  const hint=hintBtn("hIni",`<p>Нажмите «Бой!» — каждый игрок в комнате получит запрос и сам бросит инициативу в своём приложении: 2 × Ловкость + бонусы − d20. Броски сразу попадают в таблицу. Персонажи бестиария с отметкой «В бою» бросаются автоматически (каждый экземпляр отдельно), их можно перебросить кнопкой.</p><p>Если игрок не может бросить сам — бросьте за него (учитываются ваши модификаторы).</p><p>Выпала 1 — ходит первым и получает 8 действий; 2 — первым, если ни у кого нет 1. Выпало 19 — последним; 20 — последним и только 2 действия (только в первом раунде). При равенстве раньше ходит тот, у кого выше Ловкость, затем d100.</p>`,"Как это работает");
  if(!I)return `<div class="card initcard"><h3 style="margin-top:0">Инициатива</h3>
   <button class="btn big primary" data-ini="start">${bigIco("dice")}<span>Бой! <span style="opacity:.85;font-weight:400">(${np} игр. бросят сами + ${nb} из бестиария)</span></span></button>${hint}
   ${ROOM.initMissing?`<div class="warnbox" style="margin-top:8px">Запрос не уходит игрокам: на сервере нет колонки. Запустите в Supabase → SQL Editor файл <b>room-bestiary.sql</b>.</div>`:""}</div>`;
  const rolled=I.list.filter(r=>r.k==="p").length;
  return `<div class="card initcard"><div class="inline" style="gap:8px;justify-content:space-between"><h3 style="margin:0">Бой · раунд ${I.round}</h3><span class="note">начат ${agoTxt(I.t)}</span></div>
   ${I.ask?`<div class="iniwait">${pend.length?`<b>Ждём бросков (${rolled}/${rolled+pend.length}):</b><div class="iniwl">${pend.map(p=>`<span class="iniw"><span>${esc(p.name||"Без имени")}</span><button class="btn small" data-ini="gmfor|${esc(p.uid)}|${esc(p.char_id)}">Бросить за него</button></span>`).join("")}</div>${pend.length>1?`<button class="btn small" data-ini="gmall" style="margin-top:6px">Бросить за всех оставшихся (${pend.length})</button>`:""}`
     :np?`<b class="pos">Все игроки бросили ✓</b>`:`<span class="note">В комнате нет игроков.</span>`}</div>`:""}
   <div class="inline" style="gap:8px;margin-top:8px"><button class="btn small" data-ini="npc">${I.list.some(r=>r.k==="npc")?"Перебросить бестиарий":"Бросить за бестиарий"} (${nb})</button></div>
   ${ROOM.initMissing?`<div class="warnbox" style="margin-top:8px">Порядок ходов не уходит игрокам: на сервере нет колонки. Запустите в Supabase → SQL Editor файл <b>room-bestiary.sql</b>.</div>`:""}
   ${I.list.length?`<h4 style="margin:12px 0 0">Очерёдность</h4>${initTable(I,true)}`:`<p class="note" style="margin:10px 0 0">Таблица заполнится, когда придут первые броски.</p>`}
   <div class="inline" style="gap:8px;margin-top:8px">${I.list.length?`<button class="btn primary" data-ini="next">Следующий ход →</button><button class="btn small" data-ini="round">Новый раунд</button>`:""}<button class="btn small" data-ini="show">${I.show===false?"Игроки не видят порядок":"Игроки видят порядок"}</button><button class="btn small" data-ini="start">Новый бой</button><button class="btn small" data-ini="clear">Закончить бой</button></div>${hint}</div>`;}
/* игрок */
function iniMyRoll(v){const c=roomChar();if(!v||!c)return null;const me=(v.list||[]).find(initMine);if(me)return me;const x=c.iniRoll;return x&&x.t===v.t?x:null;}
function initMeRoll(){const v=ROOM.initP,c=roomChar();if(!v||!v.ask){toast("Мастер ещё не начал бой");return;}if(!c){toast("Нет персонажа в комнате");return;}
  if(iniMyRoll(v)){toast("Вы уже бросили инициативу в этом бою");return;}
  const pk=roomPeek(c);if(pk.err){toast("Не удалось прочитать лист: "+pk.err);return;}
  const x=iniRollFor(pk);c.iniRoll={t:v.t,...x};const txt=`Инициатива: ${x.base} − d20 (${x.r}) = ${x.ini}${x.r===1?" — критический успех, 8 действий!":x.r===20?" — провал, 2 действия":""}`;
  try{ROLLS.unshift(txt);c.rollLog=Array.isArray(c.rollLog)?c.rollLog:[];c.rollLog.unshift({t:Date.now(),x:txt});if(c.rollLog.length>150)c.rollLog.length=150;}catch(e){}
  try{if(C&&C.id===c.id){cbIni(x.r);}}catch(e){}
  save();roomPush();toast(txt);try{iniAskBar();}catch(e){}try{roomRefresh();}catch(e){}if(STEP===10)try{render();}catch(e){}}
function initPlayerUI(){const v=ROOM.initP;if(!v)return "";const list=Array.isArray(v.list)?v.list:[];const mine=v.ask?iniMyRoll(v):null;
  const ask=v.ask?(mine?`<div class="iniasked">Ваша инициатива: <b>${mine.ini}</b> <span class="note">(d20 = ${mine.r}${mine.r===1?", крит!":mine.r===20?", провал":""})</span>${list.some(initMine)?"":" · отправлено мастеру"}</div>`
    :`<button class="btn big primary iniaskbtn" data-ini="me">${bigIco("dice")}<span>Бой! Бросить инициативу</span></button>`):"";
  if(v.off||!list.length)return ask?`<div class="iblk rev initcard" style="margin-top:10px"><div class="iblk-t">Бой</div><div class="iblk-b">${ask}${v.off?`<div class="note" style="margin-top:6px">Порядок ходов мастер пока не показывает.</div>`:mine?`<div class="note" style="margin-top:6px">Ждём остальных.</div>`:""}</div></div>`:"";
  const c=list[v.cur];
  return `<div class="iblk rev initcard" style="margin-top:10px"><div class="iblk-t">Порядок ходов · раунд ${v.round||1}</div><div class="iblk-b">${ask}${c&&(!v.ask||v.go)?`<div style="margin:6px 0">Сейчас ходит: <b>${esc(c.n)}</b>${initMine(c)?" — это вы!":""}</div>`:""}${initTable(v,false)}</div></div>`;}
/* плашка «Бросить инициативу» поверх любой вкладки, пока игрок не бросил */
function iniAskBar(){let el=document.getElementById("iniAsk");const v=typeof ROOM==="undefined"?null:ROOM.initP;
  const need=!!(v&&v.ask&&ROOM.st&&ROOM.st.role==="player"&&!iniMyRoll(v))&&STEP!==11;
  if(!need){if(el)el.remove();return;}
  if(!el){el=document.createElement("button");el.id="iniAsk";el.type="button";el.className="btn primary";el.dataset.ini="me";el.innerHTML=`<span aria-hidden="true">⚔</span> Бой! Бросить инициативу`;document.body.appendChild(el);}}
''' + s[b:]

# обработчики кнопок
rep('''  if(a==="roll"){if(I&&I.list&&I.list.length)askConfirm("Перебросить инициативу всем? Текущий порядок и раунд сбросятся.",initRollAll);else initRollAll();return;}''',
    '''  if(a==="me"){initMeRoll();return;}
  if(a==="start"){if(I)askConfirm("Начать новый бой? Текущий порядок и раунд сбросятся, игроки бросят заново.",initStart);else initStart();return;}
  if(a==="roll"){if(I&&I.list&&I.list.length)askConfirm("Перебросить инициативу всем? Текущий порядок и раунд сбросятся.",initRollAll);else initRollAll();return;}''')
rep('  if(a==="next"){I.cur++;', '  if(a==="next"){I.moved=1;I.cur++;')
rep('  if(a==="round"){I.cur=0;', '  if(a==="round"){I.moved=1;I.cur=0;')
rep('''  if(a==="show"){I.show=I.show===false;initSave(true);renderRoom();return;}''',
    '''  if(a==="show"){I.show=I.show===false;initSave(true);renderRoom();return;}
  if(a==="npc"){if(I.list.some(r=>r.k==="npc"))askConfirm("Перебросить инициативу всему бестиарию?",()=>initNpcRoll(false));else initNpcRoll(false);return;}
  if(a==="gmall"){initGmFor(iniPending(I));return;}
  if(a==="gmfor"){const [,u,w]=b.dataset.ini.split("|");const p=(ROOM.players||[]).find(p=>p.uid===u&&p.char_id===w);if(p)initGmFor([p]);return;}''')
# «Убрать» игрока: снова попадает в «ждём», можно бросить ещё раз; пометка «за него бросил мастер»
rep('''${r.k==="npc"?` <span class="note">бест.</span>`:""}''', '''${r.k==="npc"?` <span class="note">бест.</span>`:gm&&r.gm?` <span class="note">бросил мастер</span>`:""}''')

# плашка обновляется при каждой отрисовке приложения
rep('  renderInner();\n  if(fk){', '  renderInner();\n  try{iniAskBar();}catch(e){}\n  if(fk){')


# у игрока ▶ появляется, только когда мастер пошёл по ходам
rep('function initTable(I,gm){const list=I.list||[];', 'function initTable(I,gm){const list=I.list||[],cu=gm||!I.ask||I.go?I.cur:-1;')
rep('<tr class="${i===I.cur?"cur":""}', '<tr class="${i===cu?"cur":""}')
rep('<td>${i===I.cur?"▶":i+1}</td>', '<td>${i===cu?"▶":i+1}</td>')
rep('ROOM.init={...data.gm_init,show:!data.gm_init.off,', 'ROOM.init={...data.gm_init,moved:data.gm_init.go?1:0,show:!data.gm_init.off,')

css = r'''
/* ---- бой: сбор инициативы ---- */
.iniwait{margin-top:10px;padding:8px 10px;border:1px solid var(--line);border-radius:6px}
.iniwl{display:flex;flex-direction:column;gap:6px;margin-top:6px}
.iniw{display:flex;gap:8px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.iniw>span{min-width:0;overflow-wrap:anywhere}
.iniasked{padding:6px 0}
.initcard .iniaskbtn{width:100%;justify-content:flex-start}
#iniAsk{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(72px + env(safe-area-inset-bottom,0px));z-index:900;max-width:calc(100% - 32px);box-shadow:0 4px 18px rgba(0,0,0,.45);font-size:17px;padding:12px 18px;white-space:nowrap}
</style>'''
i = s.index('</style>', s.index('<title>Сумрак 2096'))
s = s[:i] + css + s[i + len('</style>'):]
out.write_text(s, encoding='utf-8')
print('ok', out, len(s))
