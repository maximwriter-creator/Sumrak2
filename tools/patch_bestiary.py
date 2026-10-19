#!/usr/bin/env python3
"""Бестиарий мастера (свои персонажи со статами и бафами) + общий бросок инициативы в комнате.
   Сервер: supabase/room-bestiary.sql (колонка rooms.gm_init и таблица gm_bestiary).
   python3 patch_bestiary.py in.html out.html   (после patch_dusk.py, до patch_app.py)"""
import sys, pathlib
s = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
out = pathlib.Path(sys.argv[2])

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, f'не найдено ровно {count}: {old[:90]!r} ({s.count(old)})'
    s = s.replace(old, new)

if 'function bestView' in s:
    sys.exit('Уже применено')

# вкладки мастера: Комната | Бестиарий | База персонажей
rep('<button role="tab" aria-selected="${tb==="base"}" data-gmtab="base">База персонажей',
    '<button role="tab" aria-selected="${tb==="best"}" data-gmtab="best">Бестиарий${bestS().list.length?` (${bestS().list.length})`:""}</button><button role="tab" aria-selected="${tb==="base"}" data-gmtab="base">База персонажей')
rep('if(tb==="base")return sw+vbView();', 'if(tb==="base")return sw+vbView();if(tb==="best")return sw+initCard()+bestView();')
rep('    ${gmRollCard()}${ps.length?', '    ${initCard()}${gmRollCard()}${ps.length?')
# игрок: порядок ходов
rep('    ${gmLogPlayerUI()}<div class="inline"', '    ${initPlayerUI()}${gmLogPlayerUI()}<div class="inline"')
# поля ввода не перерисовываются под пальцами
rep("a.matches('[data-rmd],#rcUrl,#rcKey,#rmCode,#vbSearch')", "a.matches('[data-rmd],#rcUrl,#rcKey,#rmCode,#vbSearch,[data-npc],[data-npcn],[data-bd],[data-inihp]')")
# сервер: инициатива приходит игрокам, мастер восстанавливает свою
rep('p=>{if(p.new&&Array.isArray(p.new.gm_log))gmLogSet(p.new.gm_log,false);});',
    'p=>{if(p.new&&Array.isArray(p.new.gm_log))gmLogSet(p.new.gm_log,false);if(p.new&&p.new.gm_init)initSetP(p.new.gm_init,false);});')
rep('  if(st.role!=="gm"||ROOM.gmLog==null)gmLogLoad(st.role!=="gm");',
    '  if(st.role!=="gm"||ROOM.gmLog==null)gmLogLoad(st.role!=="gm");\n  initBoot();')
rep('if(st.role==="gm")return roomFetch();gmLogLoad(false);', 'if(st.role==="gm")return roomFetch();gmLogLoad(false);initLoad(false);')

js = r'''
/* ---------- Бестиарий мастера ---------- */
var BEST;
const BEST_KEY="sumrak2096_bestiary";
const NPC_X=[["hp","Очки здоровья",10],["armor","Броня",0],["res","Устойчивость",0],["ini","Бонус инициативы",0],["act","Действий за раунд",4]];
const NPC_SHORT={rng:"ДБ",mel:"ББ",str:"Сил",agi:"Лов",tou:"Стк",wil:"Вол",wit:"Сооб",per:"Набл",cha:"Хар",int:"Инт"};
const NPC_TPL=[["Слабый",6],["Обычный",8],["Опытный",11],["Элита",14]];
function bestS(){if(!BEST){BEST={list:[],sel:null,bd:{k:"agi",v:"",n:""},last:"",srv:""};const l=lsGet(BEST_KEY);if(Array.isArray(l))BEST.list=l.map(npcFix);}return BEST;}
function npcLbl(k){const x=NPC_X.find(x=>x[0]===k);return x?x[1]:(LABEL[k]||k);}
function npcFix(n){n=n||{};const st={};SKEYS.forEach(k=>st[k]=Number.isFinite(Number((n.st||{})[k]))?Number(n.st[k]):8);
  const o={id:n.id||uid(),name:n.name==null?"Новый персонаж":String(n.name),kind:String(n.kind||""),st,buffs:Array.isArray(n.buffs)?n.buffs.filter(b=>b&&b.k):[],notes:String(n.notes||""),on:n.on!==false,qty:Math.max(1,Math.min(20,Number(n.qty)||1)),secret:!!n.secret};
  NPC_X.forEach(([k,,d])=>o[k]=Number.isFinite(Number(n[k]))?Number(n[k]):d);o.hpCur=Number.isFinite(Number(n.hpCur))?Number(n.hpCur):o.hp;return o;}
function npcBuff(n,k){return (n.buffs||[]).filter(b=>b.k===k).reduce((a,b)=>a+(Number(b.v)||0),0);}
function npcEff(n,k){return (SKEYS.includes(k)?n.st[k]:Number(n[k])||0)+npcBuff(n,k);}
function npcIni(n){return 2*npcEff(n,"agi")+npcEff(n,"ini");}
function npcById(id){return bestS().list.find(n=>n.id===id);}
function bestSave(){const B=bestS();lsSet(BEST_KEY,B.list);clearTimeout(bestSave.t);bestSave.t=setTimeout(bestPush,1200);}
async function bestPush(){if(!roomCfgOk())return;try{const sb=await roomClient();const {error}=await sb.from("gm_bestiary").upsert({uid:ROOM.uid,npcs:bestS().list,updated_at:new Date().toISOString()});if(error)throw error;BEST.srv="ok";}
  catch(e){const m=String(e&&e.message||e);BEST.srv=/gm_bestiary|relation|schema cache|does not exist/i.test(m)?"missing":"err";}}
async function bestPull(){const B=bestS();if(B.pulled||!roomCfgOk())return;B.pulled=true;try{const sb=await roomClient();const {data,error}=await sb.from("gm_bestiary").select("npcs").eq("uid",ROOM.uid).maybeSingle();if(error)throw error;
    B.srv="ok";if(!B.list.length&&data&&Array.isArray(data.npcs)&&data.npcs.length){B.list=data.npcs.map(npcFix);lsSet(BEST_KEY,B.list);roomRefresh();}}
  catch(e){const m=String(e&&e.message||e);B.srv=/gm_bestiary|relation|schema cache|does not exist/i.test(m)?"missing":"err";roomRefresh();}}
function npcPM(path,label,v,eff){return `<div class="npcrow"><span class="npcl">${path.startsWith("st.")?`<button class="linkish" data-npctest="${path.slice(3)}" title="Бросить тест">${esc(label)}</button>`:esc(label)}</span>
  <button class="pm" data-npcpm="${path}|-1" aria-label="${esc(label)}: минус 1">−</button><input class="inp npcv" type="number" inputmode="numeric" data-npcn="${path}" value="${v}" aria-label="${esc(label)}"><button class="pm" data-npcpm="${path}|1" aria-label="${esc(label)}: плюс 1">+</button>
  <span class="npce">${eff!==v?`<b class="${eff>v?"pos":"neg"}">= ${eff}</b>`:""}</span></div>`;}
function bestEditor(n){const B=bestS(),bd=B.bd;
  const keys=[...SKEYS,...NPC_X.map(x=>x[0])];
  return `<div class="inline" style="gap:8px;justify-content:space-between;margin:4px 0 8px"><button class="btn small" data-best="back">← Весь бестиарий</button><span class="note">Сохраняется само</span></div>
  <div class="card"><label class="note" for="npcName">Имя</label><input class="inp" id="npcName" data-npc="name" value="${esc(n.name)}" style="width:100%;box-sizing:border-box">
   <label class="note" for="npcKind" style="display:block;margin-top:8px">Кто это (видно только вам)</label><input class="inp" id="npcKind" data-npc="kind" value="${esc(n.kind)}" placeholder="Например: наёмник «Чёрного солнца»" style="width:100%;box-sizing:border-box">
   ${B.last?`<div class="npclast">${B.last}</div>`:""}
   <h3>Характеристики</h3><div class="note" style="margin-bottom:6px">Быстро заполнить все: ${NPC_TPL.map(([t,v])=>`<button class="btn small" data-npctpl="${v}">${t} ${v}</button>`).join(" ")}</div>
   <p class="note" style="margin:0 0 4px">Нажмите на название характеристики — бросок теста d20.</p>
   ${SKEYS.map(k=>npcPM("st."+k,LABEL[k],n.st[k],npcEff(n,k))).join("")}
   <h3>Бой</h3>${NPC_X.map(([k,l])=>npcPM(k,l,n[k],npcEff(n,k))).join("")}
   <div class="note" style="margin-top:4px">Инициатива: 2 × Ловкость + бонус = <b>${npcIni(n)}</b>, затем минус d20.</div>
   <h3>Бафы и дебафы</h3>
   ${n.buffs.length?n.buffs.map((b,j)=>`<div class="inline" style="gap:6px;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--line)"><span><b>${esc(npcLbl(b.k))} ${sgn(Number(b.v))}</b>${b.note?` <span class="note">${esc(b.note)}</span>`:""}</span><button class="del delico" data-npcbdel="${j}" aria-label="Убрать">×</button></div>`).join(""):`<div class="note">Пока нет. Бафы прибавляются к характеристикам, ОЗ, броне, инициативе.</div>`}
   <div class="inline" style="gap:6px;margin-top:8px;flex-wrap:wrap"><select class="inp" data-bd="k" aria-label="Что меняет">${keys.map(k=>`<option value="${k}" ${bd.k===k?"selected":""}>${esc(npcLbl(k))}</option>`).join("")}</select>
    <input class="inp" data-bd="v" inputmode="numeric" placeholder="+2" value="${esc(bd.v)}" style="width:70px" aria-label="Значение"><input class="inp" data-bd="n" placeholder="Откуда: стимулятор, укрытие…" value="${esc(bd.n)}" style="flex:1;min-width:140px" aria-label="Пояснение">
    <button class="btn small" data-best="badd">Добавить</button></div>
   <h3>В бою</h3>
   <div class="npcrow"><span class="npcl">Сколько таких в бою</span><button class="pm" data-npcpm="qty|-1" aria-label="Меньше">−</button><input class="inp npcv" type="number" data-npcn="qty" value="${n.qty}" aria-label="Количество"><button class="pm" data-npcpm="qty|1" aria-label="Больше">+</button><span></span></div>
   <label class="chk"><input type="checkbox" data-npc="on" ${n.on?"checked":""}> Участвует в общей инициативе</label>
   <label class="chk"><input type="checkbox" data-npc="secret" ${n.secret?"checked":""}> Скрыть имя от игроков (в порядке ходов будет «???»)</label>
   <h3>Оружие, способности, заметки</h3><textarea class="inp" data-npc="notes" rows="4" style="width:100%;box-sizing:border-box" placeholder="Штурмовая винтовка: 2d10, ББ 2…">${esc(n.notes)}</textarea>
   <div class="inline" style="gap:8px;margin-top:10px"><button class="btn small" data-best="back">Готово</button><button class="btn small" data-best="copy">Сделать копию</button><button class="btn small" data-best="del">Удалить</button></div></div>`;}
function bestView(){const B=bestS();if(!B.pulled)bestPull();
  const n=B.sel&&npcById(B.sel);if(n)return bestEditor(n);B.sel=null;
  return `<div class="card"><h3 style="margin-top:0">Бестиарий</h3><p class="note" style="margin-top:0">Ваши персонажи: противники, союзники, монстры. Настраивайте им характеристики и бафы, бросайте тесты, отмечайте, кто участвует в общей инициативе. Игроки их листы не видят.</p>
   <button class="btn big primary" data-best="new">${bigIco("plus")}<span>Новый персонаж</span></button>
   ${B.srv==="missing"?`<div class="warnbox" style="margin-top:8px">Бестиарий хранится только на этом устройстве: на сервере нет таблицы. Запустите в Supabase → SQL Editor файл <b>room-bestiary.sql</b>.</div>`:""}
   ${B.last?`<div class="npclast">${B.last}</div>`:""}</div>
   ${B.list.map(n=>`<div class="card npccard"><div class="inline" style="gap:8px;justify-content:space-between;align-items:flex-start"><div style="min-width:0"><b style="font-size:18px">${esc(n.name||"Без имени")}</b>${n.qty>1?` <span class="note">×${n.qty}</span>`:""}${n.secret?` <span class="note">· имя скрыто</span>`:""}${n.kind?`<div class="note">${esc(n.kind)}</div>`:""}</div>
     <button class="btn small ${n.on?"primary":""}" data-npcon="${n.id}" aria-pressed="${n.on}">${n.on?"В бою ✓":"Не в бою"}</button></div>
     <div class="npcstats">${SKEYS.map(k=>{const e=npcEff(n,k);return `<button class="npcst" data-npctest="${k}" data-npcid="${n.id}" title="${esc(LABEL[k])}: тест"><span>${NPC_SHORT[k]}</span><b class="${e>n.st[k]?"pos":e<n.st[k]?"neg":""}">${e}</b></button>`;}).join("")}</div>
     <div class="note" style="margin-top:6px">ОЗ ${npcEff(n,"hp")} · броня ${npcEff(n,"armor")} · устойчивость ${npcEff(n,"res")} · инициатива ${npcIni(n)} · действий ${npcEff(n,"act")}${n.buffs.length?` · бафов ${n.buffs.length}`:""}</div>
     <div class="inline" style="gap:8px;margin-top:8px"><button class="btn small" data-npcedit="${n.id}">Изменить</button><button class="btn small" data-npccopy="${n.id}">Копия</button></div></div>`).join("")||`<p class="note">Пока пусто. Нажмите «Новый персонаж».</p>`}`;}
function npcTest(n,k){const v=npcEff(n,k),r=rnd(20);const crit=r===1?" Критический успех!":r===20?" Критический провал!":"";
  const ok=r<=v,txt=`${n.name||"Без имени"}: ${LABEL[k]} ${v}, d20 = ${r} — ${ok?(v-r?`успех, степеней ${v-r}`:"базовый успех"):`провал, степеней ${r-v}`}.${crit}`;
  bestS().last=`<span class="${ok?"pos":"neg"}">${esc(txt)}</span>`;try{gmRollPush(txt);}catch(e){}toast(txt);renderRoom();}
function npcSet(n,path,v){if(path.startsWith("st.")){n.st[path.slice(3)]=v;}else if(path==="qty"){n.qty=Math.max(1,Math.min(20,v));}else{if(path==="hp"&&n.hpCur===n.hp)n.hpCur=v;n[path]=path==="act"?Math.max(1,v):v;}bestSave();}
document.addEventListener("click",e=>{const b=e.target.closest("[data-best],[data-npcpm],[data-npctpl],[data-npcbdel],[data-npctest],[data-npcon],[data-npcedit],[data-npccopy]");if(!b||!$("#roomView")||!$("#roomView").contains(b))return;
  const B=bestS(),d=b.dataset,cur=B.sel&&npcById(B.sel);
  if(d.npcedit){B.sel=d.npcedit;B.last="";renderRoom();window.scrollTo(0,0);return;}
  if(d.npccopy){const n=npcById(d.npccopy);if(!n)return;const c=npcFix({...JSON.parse(JSON.stringify(n)),id:uid(),name:n.name+" (копия)"});B.list.splice(B.list.indexOf(n)+1,0,c);bestSave();toast("Копия создана");renderRoom();return;}
  if(d.npcon){const n=npcById(d.npcon);if(!n)return;n.on=!n.on;bestSave();renderRoom();return;}
  if(d.npctest){const n=d.npcid?npcById(d.npcid):cur;if(n)npcTest(n,d.npctest);return;}
  if(d.best==="new"){const n=npcFix({});B.list.unshift(n);B.sel=n.id;B.last="";bestSave();renderRoom();setTimeout(()=>{const i=$("#npcName");if(i){i.focus();i.select();}},50);return;}
  if(d.best==="back"){B.sel=null;B.last="";renderRoom();return;}
  if(!cur)return;
  if(d.npcpm){const [p,dv]=d.npcpm.split("|");const v=p.startsWith("st.")?cur.st[p.slice(3)]:cur[p];npcSet(cur,p,(Number(v)||0)+Number(dv));renderRoom();return;}
  if(d.npctpl){SKEYS.forEach(k=>cur.st[k]=Number(d.npctpl));bestSave();renderRoom();return;}
  if(d.npcbdel!=null){cur.buffs.splice(Number(d.npcbdel),1);bestSave();renderRoom();return;}
  if(d.best==="badd"){const v=Number(String(B.bd.v).replace("−","-").replace(",","."));if(!v){toast("Введите значение, например −2 или 3");return;}cur.buffs.push({k:B.bd.k,v,note:String(B.bd.n||"").trim()});B.bd.v="";B.bd.n="";bestSave();renderRoom();return;}
  if(d.best==="copy"){const c=npcFix({...JSON.parse(JSON.stringify(cur)),id:uid(),name:cur.name+" (копия)"});B.list.splice(B.list.indexOf(cur)+1,0,c);B.sel=c.id;bestSave();toast("Копия создана, вы в ней");renderRoom();return;}
  if(d.best==="del"){askConfirm(`Удалить «${cur.name||"Без имени"}» из бестиария?`,()=>{B.list=B.list.filter(x=>x!==cur);B.sel=null;bestSave();renderRoom();});return;}
});
document.addEventListener("input",e=>{const t=e.target;if(!t.closest||!$("#roomView")||!$("#roomView").contains(t))return;const B=bestS();
  if(t.dataset.bd){B.bd[t.dataset.bd]=t.value;return;}
  if(t.dataset.npc&&t.type!=="checkbox"){const n=B.sel&&npcById(B.sel);if(!n)return;n[t.dataset.npc]=t.value;bestSave();}});
document.addEventListener("change",e=>{const t=e.target;if(!t.closest||!$("#roomView")||!$("#roomView").contains(t))return;const B=bestS(),n=B.sel&&npcById(B.sel);
  if(t.dataset.npc&&t.type==="checkbox"&&n){n[t.dataset.npc]=t.checked;bestSave();return;}
  if(t.dataset.npcn&&n){const v=Math.round(Number(String(t.value).replace("−","-")));if(Number.isFinite(v))npcSet(n,t.dataset.npcn,v);t.blur();renderRoom();return;}
  if(t.dataset.inihp){const I=ROOM.init,r=I&&I.list[Number(t.dataset.inihp)];const v=Math.round(Number(t.value));if(r&&Number.isFinite(v)){r.hp=v;initSave(false);}t.blur();renderRoom();}});

/* ---------- Общая инициатива ---------- */
function iniGroup(r){return r===1?0:r===2?1:r===20?4:r===19?3:2;}
function iniSort(a,b){return iniGroup(a.r)-iniGroup(b.r)||b.ini-a.ini||b.agi-a.agi||b.d100-a.d100;}
function iniActs(r,base){return r===1?base+4:r===20?2:base;}
function initRollAll(){const rows=[],skip=[];
  (ROOM.players||[]).forEach(p=>{const v=roomPeek(p.sheet,ROOM.mods[rmKey(p)]||[]);if(v.err){skip.push(p.name||"Без имени");return;}
    let r=rnd(20);const mk=v.s&&v.s.mark&&v.s.mark.i!=null&&BOOK.fates[v.s.mark.i]?BOOK.fates[v.s.mark.i].name:"";if(mk==="Аура удачи"&&r===3)r=2;if(mk==="Аура неудачи"&&r===18)r=19;
    rows.push({k:"p",n:p.name||"Без имени",u:p.uid,who:p.char_id,base:v.ini,r,ini:v.ini-r,agi:v.R.tot.agi,d100:rnd(100),ab:ACT_BASE,act:iniActs(r,ACT_BASE),hp:v.hpCur,hpMax:v.hpMax});});
  bestS().list.filter(n=>n.on).forEach(n=>{for(let q=1;q<=n.qty;q++){const base=npcIni(n),r=rnd(20),ab=Math.max(1,npcEff(n,"act")),hm=npcEff(n,"hp");
    rows.push({k:"npc",id:n.id,n:(n.name||"Без имени")+(n.qty>1?" "+q:""),sec:n.secret,base,r,ini:base-r,agi:npcEff(n,"agi"),d100:rnd(100),ab,act:iniActs(r,ab),hp:hm,hpMax:hm});}});
  if(!rows.length){toast("Некого бросать: в комнате нет игроков, а в бестиарии никто не отмечен «В бою»");return;}
  rows.sort(iniSort);const show=ROOM.init?ROOM.init.show!==false:true;
  ROOM.init={t:Date.now(),round:1,cur:0,list:rows,show};initSave(true);
  try{gmRollPush("Инициатива: "+rows.map((r,i)=>`${i+1}. ${r.sec?"???":r.n} ${r.ini}`).join(", "));}catch(e){}
  toast(`Инициатива брошена: ${rows.length} участников`+(skip.length?`. Не удалось прочитать лист: ${skip.join(", ")}`:""));renderRoom();}
function initKey(){return "sumrak2096_init_"+(ROOM.st&&ROOM.st.code||"");}
function initShared(){const I=ROOM.init;if(!I)return {t:Date.now(),list:[]};if(I.show===false)return {t:I.t,off:true};
  return {t:I.t,round:I.round,cur:I.cur,list:I.list.map(r=>({k:r.k,n:r.sec?"???":r.n,ini:r.ini,r:r.r,act:r.act,u:r.u||null,who:r.who||null}))};}
function initSave(now){lsSet(initKey(),ROOM.init);clearTimeout(initSave.t);initSave.t=setTimeout(initPush,now?50:400);}
async function initPush(){const st=ROOM.st;if(!st||st.role!=="gm")return;
  try{const sb=await roomClient();const {error}=await sb.from("rooms").update({gm_init:initShared()}).eq("code",st.code);if(error)throw error;ROOM.initMissing=false;}
  catch(e){const m=String(e&&e.message||e);if(/gm_init|column/i.test(m))ROOM.initMissing=true;}try{roomRefresh();}catch(e){}}
function initBoot(){const st=ROOM.st;if(!st)return;if(st.role==="gm"){const l=lsGet(initKey());if(l&&Array.isArray(l.list)){ROOM.init=l;return;}ROOM.init=null;initLoad(true);}else initLoad(true);}
async function initLoad(initial){const st=ROOM.st;if(!st)return;
  try{const sb=await roomClient();const {data,error}=await sb.from("rooms").select("gm_init").eq("code",st.code).maybeSingle();if(error)throw error;ROOM.initMissing=false;
    if(!data||!data.gm_init)return;if(st.role==="gm"){if(!ROOM.init&&Array.isArray(data.gm_init.list)&&data.gm_init.list.length){ROOM.init={...data.gm_init,show:!data.gm_init.off,list:data.gm_init.list.map(r=>({...r,base:r.ini+r.r,ab:ACT_BASE,agi:0,d100:0,sec:r.n==="???"}))};roomRefresh();}return;}
    initSetP(data.gm_init,initial);}
  catch(e){const m=String(e&&e.message||e);if(/gm_init|column/i.test(m))ROOM.initMissing=true;}}
function initMine(r){const st=ROOM.st;return !!(st&&r.k==="p"&&r.who===st.charId&&(!r.u||r.u===ROOM.uid));}
function initSetP(v,initial){if(gmIsMaster()||!v)return;const old=ROOM.initP;const was=JSON.stringify(old||null);ROOM.initP=v;if(was===JSON.stringify(v))return;
  const list=Array.isArray(v.list)?v.list:[];const me=list.findIndex(initMine);
  if(!initial&&!v.off&&list.length){
    if(!old||old.t!==v.t){if(me>=0){const r=list[me];toast(`Инициатива: вы ходите ${me+1}-м из ${list.length}, действий ${r.act}`);
        try{const c=roomChar();if(c&&C&&C.id===c.id){cbIni(r.r);save();if(STEP===10)render();}}catch(e){}}else toast("Мастер бросил инициативу");}
    else if(old.cur!==v.cur||old.round!==v.round){const c=list[v.cur];if(c&&initMine(c))toast("Ваш ход!");else if(old.round!==v.round)toast(`Раунд ${v.round}`);}}
  try{roomRefresh();}catch(e){}}
function iniRollTxt(r){return `${r.base!=null?r.base:r.ini+r.r} − ${r.r}`;}
function initTable(I,gm){const list=I.list||[];
  return `<div class="tblwrap"><table class="initt"><thead><tr><th>#</th><th>Кто</th><th>Иниц.</th><th>Действий</th>${gm?"<th>ОЗ</th><th></th>":""}</tr></thead><tbody>${list.map((r,i)=>{const me=!gm&&initMine(r);
    return `<tr class="${i===I.cur?"cur":""} ${me?"me":""}"><td>${i===I.cur?"▶":i+1}</td><td><b>${esc(r.n)}</b>${r.k==="npc"?` <span class="note">бест.</span>`:""}${me?` <span class="note">вы</span>`:""}</td>
      <td><b>${r.ini}</b> <span class="note">${gm?iniRollTxt(r):"d20 "+r.r}</span>${r.r===1?` <span class="pos">крит!</span>`:r.r===20?` <span class="neg">провал</span>`:""}</td><td>${r.act}</td>
      ${gm?`<td>${r.k==="npc"?`<input class="inp inihp ${r.hp<=0?"neg":""}" type="number" data-inihp="${i}" value="${r.hp}" aria-label="ОЗ ${esc(r.n)}"><span class="note">/${r.hpMax}</span>`:`<span class="note">${r.hp!=null&&r.hpMax?r.hp+"/"+r.hpMax:""}</span>`}</td><td><button class="del delico" data-ini="drop|${i}" aria-label="Убрать ${esc(r.n)} из боя">×</button></td>`:""}</tr>`;}).join("")}</tbody></table></div>`;}
function initCard(){const I=ROOM.init,np=(ROOM.players||[]).length,nb=bestS().list.filter(n=>n.on).reduce((a,n)=>a+n.qty,0);
  return `<div class="card initcard"><h3 style="margin-top:0">Инициатива</h3>
   <button class="btn big primary" data-ini="roll">${bigIco("dice")}<span>${I?"Перебросить инициативу всем":"Бросить инициативу всем"} <span style="opacity:.85;font-weight:400">(${np} игр. + ${nb} из бестиария)</span></span></button>
   ${hintBtn("hIni",`<p>Каждому участнику: 2 × Ловкость + бонусы инициативы − d20 (у игроков учитываются ваши модификаторы). Выше результат — раньше ход.</p><p>Выпала 1 — ходит первым и получает 8 действий; 2 — первым, если ни у кого нет 1. Выпало 19 — последним; 20 — последним и только 2 действия (это только в первом раунде). При равенстве раньше ходит тот, у кого выше Ловкость, затем d100.</p><p>Из бестиария в бросок попадают персонажи с отметкой «В бою», каждый экземпляр отдельно.</p>`,"Как считается")}
   ${ROOM.initMissing?`<div class="warnbox" style="margin-top:8px">Порядок ходов не уходит игрокам: на сервере нет колонки. Запустите в Supabase → SQL Editor файл <b>room-bestiary.sql</b>.</div>`:""}
   ${I&&I.list&&I.list.length?`<div class="inline" style="gap:8px;justify-content:space-between;margin-top:10px"><b>Раунд ${I.round}</b><span class="note">брошено ${agoTxt(I.t)}</span></div>${initTable(I,true)}
   <div class="inline" style="gap:8px;margin-top:8px"><button class="btn primary" data-ini="next">Следующий ход →</button><button class="btn small" data-ini="round">Новый раунд</button><button class="btn small" data-ini="show">${I.show===false?"Игроки не видят порядок":"Игроки видят порядок"}</button><button class="btn small" data-ini="clear">Закончить бой</button></div>`:""}</div>`;}
function initPlayerUI(){const v=ROOM.initP;if(!v||v.off||!Array.isArray(v.list)||!v.list.length)return "";
  const c=v.list[v.cur];
  return `<div class="iblk rev initcard" style="margin-top:10px"><div class="iblk-t">Порядок ходов · раунд ${v.round||1}</div><div class="iblk-b">${c?`<div style="margin-bottom:6px">Сейчас ходит: <b>${esc(c.n)}</b>${initMine(c)?" — это вы!":""}</div>`:""}${initTable(v,false)}</div></div>`;}
document.addEventListener("click",e=>{const b=e.target.closest("[data-ini]");if(!b)return;const [a,x]=b.dataset.ini.split("|"),I=ROOM.init;
  if(a==="roll"){if(I&&I.list&&I.list.length)askConfirm("Перебросить инициативу всем? Текущий порядок и раунд сбросятся.",initRollAll);else initRollAll();return;}
  if(!I)return;
  if(a==="next"){I.cur++;if(I.cur>=I.list.length){I.cur=0;I.round++;I.list.forEach(r=>r.act=r.ab||ACT_BASE);toast(`Раунд ${I.round}`);}initSave(true);renderRoom();return;}
  if(a==="round"){I.cur=0;I.round++;I.list.forEach(r=>r.act=r.ab||ACT_BASE);initSave(true);toast(`Раунд ${I.round}`);renderRoom();return;}
  if(a==="show"){I.show=I.show===false;initSave(true);renderRoom();return;}
  if(a==="drop"){const i=Number(x),r=I.list[i];if(!r)return;askConfirm(`Убрать «${r.n}» из порядка ходов?`,()=>{I.list.splice(i,1);if(I.cur>i||I.cur>=I.list.length)I.cur=Math.max(0,I.cur>i?I.cur-1:0);initSave(true);renderRoom();});return;}
  if(a==="clear"){askConfirm("Закончить бой и убрать порядок ходов у всех?",()=>{ROOM.init=null;lsSet(initKey(),null);clearTimeout(initSave.t);initPush();renderRoom();});return;}
});
'''
rep('/* ---------- Комната мастера (Supabase) ---------- */', js + '/* ---------- Комната мастера (Supabase) ---------- */')

# иконка «плюс» для крупной кнопки
rep("  dice:'<rect", "  plus:'<path d=\"M12 5v14M5 12h14\"/>',\n  dice:'<rect")

css = r'''
/* ---- бестиарий и инициатива ---- */
.gmtabs{grid-template-columns:repeat(3,minmax(0,1fr))}
.gmtabs button{overflow-wrap:anywhere;line-height:1.2}
.initcard .btn.big,.npccard~.card .btn.big{width:100%;justify-content:flex-start}
.initcard>.btn.big{width:100%;justify-content:flex-start}
.tblwrap{overflow-x:auto;margin-top:6px}
.initt{width:100%;border-collapse:collapse;font-size:15px}
.initt th{text-align:left;font-size:13px;color:var(--muted);font-weight:600;padding:4px 6px;border-bottom:1px solid var(--line)}
.initt td{padding:6px;border-bottom:1px solid var(--line);vertical-align:middle}
.initt tr.cur td{background:color-mix(in srgb,var(--accent) 18%,transparent)}
.initt tr.me td:nth-child(2){text-decoration:underline;text-underline-offset:3px}
.initt td .note{font-size:12px}.initt td:nth-child(3) .note{display:block}
.initt .inihp{width:58px;padding:4px 6px;box-sizing:border-box}
.pos{color:var(--ok,#2e9d5b)}.neg{color:var(--warn,#c0392b)}
.npcrow{display:grid;grid-template-columns:minmax(0,1fr) 44px 64px 44px 52px;align-items:center;gap:6px;margin:4px 0}
.npcrow .pm{width:44px;height:40px;font-size:20px}
.npcrow .npcv{width:64px;text-align:center;box-sizing:border-box;font-size:17px}
.npcrow .npcl{min-width:0;overflow-wrap:anywhere}
.linkish{background:none;border:0;padding:0;color:var(--accent);font:inherit;text-decoration:underline dotted;text-underline-offset:3px;cursor:pointer;text-align:left}
.npcstats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:4px;margin-top:8px}
.npcst{display:flex;flex-direction:column;align-items:center;border:1px solid var(--line);border-radius:6px;background:none;color:inherit;padding:4px 2px;cursor:pointer;font:inherit}
.npcst span{font-size:12px;color:var(--muted)}.npcst b{font-size:17px}
.npclast{margin-top:8px;padding:8px 10px;border:1px solid var(--line);border-radius:6px}
label.chk{display:flex;gap:8px;align-items:center;margin:8px 0}
</style>'''
i = s.index('</style>', s.index('<title>Сумрак 2096'))
s = s[:i] + css + s[i + len('</style>'):]
out.write_text(s, encoding='utf-8')
print('ok', out, len(s))
