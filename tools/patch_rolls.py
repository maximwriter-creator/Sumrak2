#!/usr/bin/env python3
"""Журнал бросков персонажа и его просмотр мастером в комнате.
   python3 patch_rolls.py in.html out.html   (после patch_room.py, до patch_app.py)"""
import sys, pathlib
s = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
out = pathlib.Path(sys.argv[2])

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, f'не найдено ровно {count}: {old[:90]!r} ({s.count(old)})'
    s = s.replace(old, new)

if 'function rollRec' in s:
    sys.exit('Уже применено')

# все броски проходят через ROLLS.unshift — пишем их ещё и в персонажа (C.rollLog), с временем
n = s.count('ROLLS.unshift(')
assert n >= 4, n
s = s.replace('ROLLS.unshift(', 'rollRec(')

# мастер: общая лента бросков комнаты и журнал выбранного игрока
rep('${ps.length?`<div class="ptabbar" role="tablist">${tabs}</div>',
    '${ps.length?`${roomFeedUI(ps)}<div class="ptabbar" role="tablist">${tabs}</div>')
rep('${roomModsUI(p,i)}<div class="peek" id="peekBox">', '${roomModsUI(p,i)}${roomRollsUI(p)}<div class="peek" id="peekBox">')

js = r'''
/* ---------- Журнал бросков (виден мастеру в комнате) ---------- */
function rollRec(x){
  ROLLS.unshift(x);
  try{const c=C;if(c){c.rollLog=Array.isArray(c.rollLog)?c.rollLog:[];
    c.rollLog.unshift({t:Date.now(),x:String(x).slice(0,400)});if(c.rollLog.length>150)c.rollLog.length=150;rollSaveSoon();}}catch(e){}
  return ROLLS.length;}
function rollSaveSoon(){clearTimeout(rollSaveSoon.t);rollSaveSoon.t=setTimeout(()=>{try{save();}catch(e){}},300);}
function rollClock(t){return new Date(t).toLocaleTimeString("ru-RU",{hour:"2-digit",minute:"2-digit"});}
function rollFresh(t){return Date.now()-t<90*1000;}
function rollLogOf(p){const l=p&&p.sheet&&p.sheet.rollLog;return Array.isArray(l)?l.filter(r=>r&&r.x&&r.t):[];}
function roomFeedUI(ps){
  const all=[];ps.forEach(p=>rollLogOf(p).slice(0,40).forEach(r=>all.push({...r,n:p.name||"Без имени"})));
  all.sort((a,b)=>b.t-a.t);const top=all.slice(0,12);
  const open=ROOM.feedOpen!==false;
  return `<details class="card rollfeed" data-rfeed="1" ${open?"open":""}><summary><h3 style="display:inline;margin:0">Последние броски в комнате</h3></summary>
    ${top.length?`<ol class="rlog">${top.map(r=>`<li class="${rollFresh(r.t)?"fresh":""}"><span class="rlt">${rollClock(r.t)}</span><b>${esc(r.n)}</b>: ${esc(r.x)}</li>`).join("")}</ol>`:`<p class="note">Пока никто не бросал кубы. Броски игроков появляются здесь сами.</p>`}</details>`;}
function roomRollsUI(p){
  const l=rollLogOf(p),open=ROOM.rollOpen!==false;
  return `<details class="card rollfeed" data-rlog="1" ${open?"open":""}><summary><h3 style="display:inline;margin:0">Броски: ${esc(p.name||"Без имени")}${l.length?` (${l.length})`:""}</h3></summary>
    ${l.length?`<ol class="rlog">${l.slice(0,40).map(r=>`<li class="${rollFresh(r.t)?"fresh":""}"><span class="rlt">${rollClock(r.t)}</span>${esc(r.x)}</li>`).join("")}</ol>${l.length>40?`<p class="note">Показаны последние 40 из ${l.length}.</p>`:""}`
      :`<p class="note">Бросков пока нет. Если игрок уже бросал, а здесь пусто, у него старая версия приложения.</p>`}</details>`;}
document.addEventListener("toggle",e=>{const d=e.target;if(!(d instanceof HTMLElement))return;if(d.dataset.rfeed)ROOM.feedOpen=d.open;if(d.dataset.rlog)ROOM.rollOpen=d.open;},true);
'''
rep('/* ---------- Комната мастера (Supabase) ---------- */', js + '/* ---------- Комната мастера (Supabase) ---------- */')

css = r'''
/* ---- журнал бросков в комнате ---- */
.rollfeed{margin-top:10px}
.rollfeed>summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:8px}
.rollfeed>summary::-webkit-details-marker{display:none}
.rollfeed>summary::before{content:"▸";color:var(--muted);font-size:14px}
.rollfeed[open]>summary::before{content:"▾"}
.rlog{list-style:none;margin:8px 0 0;padding:0;max-height:320px;overflow-y:auto}
.rlog li{display:block;padding:5px 0;border-bottom:1px solid var(--line);font-size:14px;line-height:1.35;overflow-wrap:anywhere}
.rlog li:last-child{border-bottom:0}
.rlog .rlt{display:inline-block;min-width:44px;margin-right:6px;color:var(--muted);font-variant-numeric:tabular-nums;font-size:13px}
.rlog li.fresh{background:color-mix(in srgb,var(--accent) 12%,transparent);border-radius:4px;padding-left:6px;padding-right:6px}
</style>'''
i = s.index('</style>', s.index('<title>Сумрак 2096'))
s = s[:i] + css + s[i + len('</style>'):]
out.write_text(s, encoding='utf-8')
print('ok', out, len(s), 'замен ROLLS.unshift:', n)
