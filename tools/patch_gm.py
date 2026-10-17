#!/usr/bin/env python3
"""Броски мастера в комнате: открытые (видны игрокам) или скрытые.
   Нужна колонка rooms.gm_log — supabase/room-gmlog.sql.
   python3 patch_gm.py in.html out.html   (после patch_hints.py, до patch_app.py)"""
import sys, pathlib
s = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
out = pathlib.Path(sys.argv[2])

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, f'не найдено ровно {count}: {old[:90]!r} ({s.count(old)})'
    s = s.replace(old, new)

if 'function gmRollPush' in s:
    sys.exit('Уже применено')

# каждый бросок мастера (если он мастер комнаты) уходит в комнату
rep('  return ROLLS.length;}', '  try{gmRollPush(x);}catch(e){}\n  return ROLLS.length;}')
# игроки: подписка на изменения комнаты и загрузка бросков мастера
rep('  ch.subscribe(s=>{ROOM.status=s;',
    '  if(st.role!=="gm")ch.on("postgres_changes",{event:"UPDATE",schema:"public",table:"rooms",filter:`code=eq.${st.code}`},p=>{if(p.new&&Array.isArray(p.new.gm_log))gmLogSet(p.new.gm_log,false);});\n'
    '  if(st.role!=="gm"||ROOM.gmLog==null)gmLogLoad(st.role!=="gm");\n'
    '  ch.subscribe(s=>{ROOM.status=s;')
rep('if(st.role==="gm")return roomFetch();try{', 'if(st.role==="gm")return roomFetch();gmLogLoad(false);try{')
# мастер: переключатель и броски мастера в общей ленте
rep('${ps.length?`${roomFeedUI(ps)}', '${gmRollCard()}${ps.length?`${roomFeedUI(ps)}')
rep('const all=[];ps.forEach(p=>rollLogOf(p).slice(0,40).forEach(r=>all.push({...r,n:p.name||"Без имени"})));',
    'const all=[];ps.forEach(p=>rollLogOf(p).slice(0,40).forEach(r=>all.push({...r,n:p.name||"Без имени"})));(ROOM.gmMine||ROOM.gmLog||[]).slice(0,40).forEach(r=>all.push({...r,n:"Мастер"+(r.hid?" (скрыто)":"")}));')
# игрок: лента бросков мастера
rep('<div class="inline" style="gap:8px;margin-top:10px"><button class="btn small" data-room="push">',
    '${gmLogPlayerUI()}<div class="inline" style="gap:8px;margin-top:10px"><button class="btn small" data-room="push">')
# «Кубы»: напоминание мастеру, видны ли его броски
rep('  document.body.classList.toggle("sheetedit",sheetEditOn());', '  document.body.classList.toggle("sheetedit",sheetEditOn());\n  gmDiceBar();')

js = r'''
/* ---------- Броски мастера в комнате ---------- */
function gmIsMaster(){return typeof ROOM!=="undefined"&&ROOM&&ROOM.st&&ROOM.st.role==="gm";}
function gmHid(){if(ROOM.gmHidden==null){try{ROOM.gmHidden=localStorage.getItem("sumrak2096_gm_hidden")==="1";}catch(e){ROOM.gmHidden=false;}}return ROOM.gmHidden;}
function gmSetHid(v){ROOM.gmHidden=!!v;try{localStorage.setItem("sumrak2096_gm_hidden",v?"1":"0");}catch(e){}}
function gmEye(open){return open
  ?'<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>'
  :'<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3l18 18"/><path d="M10.6 5.1A10.8 10.8 0 0 1 12 5c6.4 0 10 7 10 7a17.6 17.6 0 0 1-3.2 4.2M6.6 6.6C3.8 8.4 2 12 2 12s3.6 7 10 7a10 10 0 0 0 4.4-1"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/></svg>';}
function gmRollPush(x){
  if(!gmIsMaster())return;
  const t=Date.now(),txt=String(x).slice(0,300),hid=gmHid();
  ROOM.gmMine=[{t,x:txt,hid},...(ROOM.gmMine||[])].slice(0,40);
  ROOM.gmLog=[hid?{t,x:"Скрытый бросок",hid:true}:{t,x:txt},...(ROOM.gmLog||[])].slice(0,40);
  clearTimeout(ROOM.gmT);ROOM.gmT=setTimeout(gmLogSave,400);
  try{roomRefresh();}catch(e){}}
async function gmLogSave(){const st=ROOM.st;if(!st||st.role!=="gm")return;
  try{const sb=await roomClient();const {error}=await sb.from("rooms").update({gm_log:ROOM.gmLog||[]}).eq("code",st.code);
    if(error)throw error;ROOM.gmLogMissing=false;}
  catch(e){const m=String(e&&e.message||e);if(/gm_log|column/i.test(m))ROOM.gmLogMissing=true;}
  try{roomRefresh();}catch(e){}}
async function gmLogLoad(initial){const st=ROOM.st;if(!st)return;
  try{const sb=await roomClient();const {data,error}=await sb.from("rooms").select("gm_log").eq("code",st.code).maybeSingle();
    if(error)throw error;ROOM.gmLogMissing=false;if(data&&Array.isArray(data.gm_log))gmLogSet(data.gm_log,initial);}
  catch(e){const m=String(e&&e.message||e);if(/gm_log|column/i.test(m))ROOM.gmLogMissing=true;}}
function gmLogSet(list,initial){
  list=(list||[]).filter(r=>r&&r.t&&r.x);
  if(gmIsMaster()){if(ROOM.gmLog==null)ROOM.gmLog=list;return;}
  const seen=ROOM.gmSeen||0,fresh=list.filter(r=>r.t>seen);
  const was=JSON.stringify(ROOM.gmLog||[]);ROOM.gmLog=list;ROOM.gmSeen=list.reduce((a,r)=>Math.max(a,r.t),seen);
  if(!initial&&seen&&fresh.length){const r=fresh[0];toast(r.hid?"Мастер бросил кубы втайне":"Мастер: "+r.x);}
  if(was!==JSON.stringify(list))try{roomRefresh();}catch(e){}}
function gmToggleBtn(){const h=gmHid();
  return `<button class="btn big ${h?"":"primary"}" data-gmhide="1" aria-pressed="${h}">${gmEye(!h)}<span>${h?"Мои броски скрыты от игроков":"Мои броски видны игрокам"}</span></button>`;}
function gmRollCard(){const mine=(ROOM.gmMine||[]).slice(0,5);
  return `<div class="card gmroll"><h3 style="margin-top:0">Ваши броски</h3>${gmToggleBtn()}
    <p class="note" style="margin:8px 0 0">${gmHid()?"Игроки увидят только, что вы бросили кубы втайне. Нажмите, чтобы снова показывать броски.":"Игроки видят ваши броски из любого раздела приложения: «Кубы», калькулятор, тесты. Нажмите, чтобы бросать втайне."}</p>
    ${ROOM.gmLogMissing?`<div class="warnbox" style="margin-top:8px">На сервере нет колонки для бросков мастера: запустите в Supabase → SQL Editor файл <b>room-gmlog.sql</b>.</div>`:""}
    ${mine.length?`<ol class="rlog">${mine.map(r=>`<li class="${rollFresh(r.t)?"fresh":""}"><span class="rlt">${rollClock(r.t)}</span>${r.hid?`<span class="note">скрыто · </span>`:""}${esc(r.x)}</li>`).join("")}</ol>`:""}</div>`;}
function gmLogPlayerUI(){const l=(ROOM.gmLog||[]).slice(0,15);
  return `<div class="iblk rev" style="margin-top:10px"><div class="iblk-t">Броски мастера</div><div class="iblk-b">${l.length?`<ol class="rlog" style="margin-top:0">${l.map(r=>`<li class="${rollFresh(r.t)?"fresh":""}"><span class="rlt">${rollClock(r.t)}</span>${r.hid?`<i class="note">Скрытый бросок</i>`:esc(r.x)}</li>`).join("")}</ol>`:`<div class="note">Мастер пока не бросал кубы открыто.</div>`}</div></div>`;}
function gmDiceBar(){if(STEP!==9||!gmIsMaster())return;const m=$("#main");if(!m||m.querySelector(".gmbar"))return;
  m.insertAdjacentHTML("afterbegin",`<div class="card gmbar"><div class="note" style="margin-bottom:6px">Вы мастер комнаты <b>${esc(ROOM.st.code)}</b></div>${gmToggleBtn()}</div>`);}
document.addEventListener("click",e=>{const b=e.target.closest("[data-gmhide]");if(!b)return;
  gmSetHid(!gmHid());toast(gmHid()?"Броски скрыты: игроки увидят только, что вы бросили":"Броски снова видны игрокам");
  if(STEP===9)render();else try{renderRoom();}catch(err){}});
'''
rep('/* ---------- Комната мастера (Supabase) ---------- */', js + '/* ---------- Комната мастера (Supabase) ---------- */')

css = r'''
/* ---- броски мастера ---- */
.gmroll .btn.big,.gmbar .btn.big{width:100%;justify-content:flex-start}
.gmbar{margin-bottom:12px}
</style>'''
i = s.index('</style>', s.index('<title>Сумрак 2096'))
s = s[:i] + css + s[i + len('</style>'):]
out.write_text(s, encoding='utf-8')
print('ok', out, len(s))
