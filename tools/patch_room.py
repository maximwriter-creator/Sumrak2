#!/usr/bin/env python3
"""Комната мастера: не оставлять пустую вкладку, возврат мастера в свою комнату, сброс сессии.
   python3 patch_room.py in.html out.html   (после patch_sheet.py, до patch_app.py)"""
import sys, pathlib
s = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
out = pathlib.Path(sys.argv[2])

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, f'не найдено ровно {count}: {old[:90]!r} ({s.count(old)})'
    s = s.replace(old, new)

if 'function renderRoomInner' in s:
    sys.exit('Уже применено')

# 1. ошибка отрисовки больше не оставляет пустую вкладку
rep('function renderRoom(){const body=$("#roomView");if(!body)return;ROOM.dirty=false;',
    'function renderRoom(){const body=$("#roomView");if(!body)return;if(typeof ROOM==="undefined"||!ROOM){setTimeout(renderRoom,30);return;}try{renderRoomInner(body);}catch(e){console.error(e);body.innerHTML=roomCrashHTML(e);}}\n'
    'function renderRoomInner(body){ROOM.dirty=false;')

rep('err=ROOM.err?`<div class="warnbox" style="margin-top:8px">${esc(ROOM.err)}</div>`:""',
    'err=ROOM.err?`<div class="warnbox" style="margin-top:8px">${esc(ROOM.err)}${ROOM.uidBad?`<div style="margin-top:8px"><button class="btn small" data-room="reset">Сбросить подключение</button></div>`:""}</div>`:""')
# 1б. случайное «Создать комнату» вместо входа игрока
rep('if(a==="create")return roomCreate();', 'if(a==="create")return askConfirm("Создать новую комнату? Вы станете в ней мастером. Если вы игрок — нажмите «Отмена» и введите код в поле «Я игрок».",()=>roomCreate());')
rep('<p class="note" style="margin-bottom:0">Игроки: «Комната» → «Я игрок» → этот код. Листы обновляются сами.</p></div>',
    '<p class="note" style="margin-bottom:0">Вы — мастер этой комнаты. Игроки: «Комната» → «Я игрок» → этот код. Попали сюда по ошибке? Нажмите внизу «Выйти» и введите код в поле «Я игрок».</p></div>')
# 2. мастер может вернуться в свою комнату
rep('<div class="card"><h3 style="margin-top:0">Я мастер</h3><button class="btn primary" data-room="create" ${ROOM.busy?"disabled":""}>Создать комнату</button></div>',
    '<div class="card"><h3 style="margin-top:0">Я мастер</h3><button class="btn primary" data-room="create" ${ROOM.busy?"disabled":""}>Создать комнату</button>${gmRoomsHTML()}</div>')
rep('ROOM.st={role:"gm",code};lsSet(RST_KEY,ROOM.st);', 'ROOM.st={role:"gm",code,uid:ROOM.uid};lsSet(RST_KEY,ROOM.st);ROOM.mine=null;')
rep('ROOM.st={role:"player",code,charId:c.id};lsSet(RST_KEY,ROOM.st);', 'ROOM.st={role:"player",code,charId:c.id,uid:ROOM.uid};lsSet(RST_KEY,ROOM.st);')

rep('(b.data||[]).forEach(r=>ROOM.mods[rmKey(r)]=r.mods||[]);ROOM.err="";}', '(b.data||[]).forEach(r=>ROOM.mods[rmKey(r)]=r.mods||[]);ROOM.err="";roomCheckUid();}')
# 3. сессия: следим за сбросом входа и сменой учётной записи устройства
rep('  ROOM.uid=(data.session||data).user.id;return ROOM.sb;}',
    '  ROOM.uid=(data.session||data).user.id;\n'
    '  if(!ROOM.authHook){ROOM.authHook=true;try{ROOM.sb.auth.onAuthStateChange((ev,ses)=>{const id=ses&&ses.user?ses.user.id:null;if(!id){ROOM.uid=null;}else ROOM.uid=id;});}catch(e){}}\n'
    '  roomCheckUid();return ROOM.sb;}')
rep('document.addEventListener("visibilitychange",()=>{if(!document.hidden&&ROOM&&ROOM.st)roomPoll();});',
    'document.addEventListener("visibilitychange",()=>{if(!document.hidden&&ROOM&&ROOM.st){roomPoll();if(ROOM.status!=="SUBSCRIBED")roomSubscribe().catch(()=>{});}});\n'
    'window.addEventListener("online",()=>{if(ROOM&&ROOM.st){roomPoll();if(ROOM.status!=="SUBSCRIBED")roomSubscribe().catch(()=>{});}});')

js = r'''
/* ---------- Комната: устойчивость на телефонах ---------- */
function roomCheckUid(){const st=ROOM.st;if(!st||!ROOM.uid)return;
  if(!st.uid){st.uid=ROOM.uid;lsSet(RST_KEY,st);return;}
  if(st.uid!==ROOM.uid){ROOM.uidBad=true;ROOM.err=st.role==="gm"
    ?"Сервер сбросил вход этого устройства, поэтому прежняя комната ему больше не принадлежит. Нажмите «Сбросить подключение» и создайте комнату заново — игроки войдут по новому коду."
    :"Сервер сбросил вход этого устройства. Нажмите «Сбросить подключение» и войдите в комнату по коду ещё раз.";}}
function roomCrashHTML(e){return `<div class="warnbox" style="margin-top:8px">Не удалось показать комнату: ${esc(String(e&&e.message||e))}</div>
  <div class="inline" style="gap:8px;margin-top:10px"><button class="btn small" data-room="redraw">Показать ещё раз</button><button class="btn small" data-room="reset">Сбросить подключение</button></div>
  <p class="note">«Сбросить подключение» убирает комнату только с этого устройства. Сама комната на сервере остаётся: мастер вернётся в неё через «Мои комнаты», игрок — по коду.</p>`;}
function gmRoomsHTML(){
  if(!roomCfgOk())return "";
  if(ROOM.mine==null){ROOM.mine="loading";roomMine();}
  if(ROOM.mine==="loading")return `<p class="note" style="margin:10px 0 0">Ищу ваши комнаты…</p>`;
  if(!Array.isArray(ROOM.mine)||!ROOM.mine.length)return "";
  return `<div style="margin-top:12px"><div class="note">Мои комнаты на этом устройстве:</div><div class="inline" style="gap:6px;margin-top:6px">${ROOM.mine.map(r=>`<button class="btn small" data-roomback="${esc(r.code)}">Вернуться в <b>${esc(r.code)}</b> <span class="note">· ${agoTxt(r.created_at)}</span></button>`).join("")}</div></div>`;}
async function roomMine(){try{const sb=await roomClient();const {data,error}=await sb.from("rooms").select("code,created_at").eq("gm",ROOM.uid).order("created_at",{ascending:false}).limit(10);if(error)throw error;ROOM.mine=data||[];}catch(e){ROOM.mine=[];}roomRefresh();}
async function roomBack(code){ROOM.busy=true;ROOM.err="";roomRefresh();try{await roomClient();ROOM.st={role:"gm",code,uid:ROOM.uid};lsSet(RST_KEY,ROOM.st);ROOM.msg="";ROOM.players=[];ROOM.mods={};await roomSubscribe();await roomFetch();}catch(e){ROOM.err=roomErr(e);}ROOM.busy=false;roomRefresh();renderRoomBtn();}
document.addEventListener("click",e=>{const b=e.target.closest("[data-roomback],[data-room=redraw],[data-room=reset]");if(!b)return;
  if(b.dataset.roomback){roomBack(b.dataset.roomback);return;}
  if(b.dataset.room==="redraw"){ROOM.err="";roomFetch().finally(()=>renderRoom());return;}
  if(b.dataset.room==="reset"){askConfirm("Сбросить подключение к комнате на этом устройстве? Комната на сервере останется.",()=>{roomGone("");ROOM.err="";ROOM.uidBad=false;ROOM.mine=null;renderRoom();});return;}
},true);
'''
rep('/* ---------- Комната мастера (Supabase) ---------- */', js + '/* ---------- Комната мастера (Supabase) ---------- */')
out.write_text(s, encoding='utf-8')
print('ok', out, len(s))
