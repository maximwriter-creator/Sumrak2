#!/usr/bin/env python3
"""Очередь боя руками: мастер добавляет любого (из бестиария или своё имя) с броском d20 или с готовым числом,
   двигает строки ↑/↓ (после ручного порядка новые встают по инициативе, не ломая остальных),
   «Упорядочить по инициативе» возвращает автоматическую сортировку; «Собрать очередь вручную» без «Боя!».
   python3 patch_initadd.py in.html out.html   (после patch_initask.py, до patch_app.py)"""
import sys, pathlib
s = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
out = pathlib.Path(sys.argv[2])

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, f'не найдено ровно {count}: {old[:90]!r} ({s.count(old)})'
    s = s.replace(old, new)

if 'function iniAddDo' in s:
    sys.exit('Уже применено')

# сортировка: при ручном порядке новые строки вставляются на своё место, остальные не двигаются
rep('function iniResort(I,c){I.list.sort(iniSort);if(!I.moved||!c){I.cur=0;return;}',
    '''function iniResort(I,c){if(I.manual){const old=I.list.filter(r=>r.o),nw=I.list.filter(r=>!r.o).sort(iniSort);I.list=old;
    nw.forEach(r=>{r.o=1;const j=I.list.findIndex(x=>iniSort(r,x)<0);I.list.splice(j<0?I.list.length:j,0,r);});}
  else{I.list.sort(iniSort);I.list.forEach(r=>r.o=1);}
  if(!I.moved||!c){I.cur=0;return;}''')
# переброс бестиария не трогает добавленных руками
rep('I.list=I.list.filter(r=>r.k!=="npc");I.list.push(...rows);', 'I.list=I.list.filter(r=>r.k!=="npc"||r.man);I.list.push(...rows);')

# таблица: число без броска, пометка «добавлен», стрелки
rep('function iniRollTxt(r){return `${r.base!=null?r.base:r.ini+r.r} − ${r.r}`;}',
    'function iniRollTxt(r){return r.r==null?"без броска":`${r.base!=null?r.base:r.ini+r.r} − ${r.r}`;}')
rep('<span class="note">${gm?iniRollTxt(r):"d20 "+r.r}</span>', '<span class="note">${gm||r.r==null?iniRollTxt(r):"d20 "+r.r}</span>')
rep('${r.k==="npc"?` <span class="note">бест.</span>`:gm&&r.gm?',
    '${gm&&r.man?` <span class="note">${r.k==="npc"?"бест., ":""}добавлен</span>`:r.k==="npc"?` <span class="note">бест.</span>`:gm&&r.gm?')
rep('<td>${i===cu?"▶":i+1}</td>',
    '<td class="ininum">${gm?`<button class="mvb" data-ini="up|${i}" ${i?"":"disabled"} aria-label="${esc(r.n)}: выше">▲</button>`:""}<span>${i===cu?"▶":i+1}</span>${gm?`<button class="mvb" data-ini="dn|${i}" ${i<list.length-1?"":"disabled"} aria-label="${esc(r.n)}: ниже">▼</button>`:""}</td>')
rep('<th>Действий</th>', '<th>Дейст.</th>')

# карточка: форма добавления, «по инициативе», ручная очередь без боя
rep('Таблица заполнится, когда придут первые броски.</p>`}',
    '''${I.ask?"Таблица заполнится, когда придут первые броски.":"Очередь пуста — добавьте участников ниже."}</p>`}
   ${I.manual&&I.list.length>1?`<button class="btn small" data-ini="sort" style="margin-top:6px">Упорядочить по инициативе</button> <span class="note">порядок задан вручную</span>`:""}
   ${iniAddUI()}''')
rep('''(${np} игр. бросят сами + ${nb} из бестиария)</span></span></button>${hint}''',
    '''(${np} игр. бросят сами + ${nb} из бестиария)</span></span></button>
   <button class="btn small" data-ini="manual" style="margin-top:8px">Собрать очередь вручную</button>${hint}''')
rep('${I.ask?`<div class="iniwait">', '${!I.ask?`<p class="note" style="margin:6px 0 0">Очередь собрана вручную: игрокам запрос на бросок не отправлялся.</p>`:""}${I.ask?`<div class="iniwait">')

# поля формы не перерисовываются под пальцами
rep(",[data-inihp]')", ",[data-inihp],[data-iad]')")

rep('''  if(a==="npc"){''', '''  if(a==="addroll"||a==="addfix"){iniAddDo(a==="addroll");return;}
  if(a==="up"||a==="dn"){const i=Number(x),j=a==="up"?i-1:i+1;if(j<0||j>=I.list.length)return;const c=I.list[I.cur];
    [I.list[i],I.list[j]]=[I.list[j],I.list[i]];I.manual=1;I.list.forEach(r=>r.o=1);I.cur=I.moved&&c?I.list.indexOf(c):0;initSave(true);renderRoom();return;}
  if(a==="sort"){const c=I.list[I.cur];I.manual=0;iniResort(I,c);initSave(true);renderRoom();return;}
  if(a==="npc"){''')
rep('''  if(a==="me"){initMeRoll();return;}''', '''  if(a==="me"){initMeRoll();return;}
  if(a==="manual"){if(I)return;const A=iniAddS();A.open=true;ROOM.init={t:Date.now(),round:1,cur:0,list:[],show:true,ask:0};initSave(true);renderRoom();return;}''')

js = r'''
/* ---------- Очередь боя: добавление руками ---------- */
function iniAddS(){return ROOM.iniAdd||(ROOM.iniAdd={open:false,src:"",name:"",base:"",act:"",sec:false});}
function iniAddUI(){const A=iniAddS(),B=bestS().list;
  return `<details class="iniadd" ${A.open?"open":""}><summary data-iadsum>＋ Добавить в очередь</summary><div class="iniadd-b">
   <label class="note" for="iadSrc">Кто</label><select class="inp" id="iadSrc" data-iad="src" style="width:100%;box-sizing:border-box"><option value="" ${A.src?"":"selected"}>Свой вариант — ввести имя</option>${B.map(n=>`<option value="${n.id}" ${A.src===n.id?"selected":""}>Бестиарий: ${esc(n.name||"Без имени")}</option>`).join("")}</select>
   ${A.src?"":`<label class="note" for="iadName" style="display:block;margin-top:6px">Имя</label><input class="inp" id="iadName" data-iad="name" value="${esc(A.name)}" placeholder="Например: Подкрепление, Турель" style="width:100%;box-sizing:border-box">`}
   <div class="iadrow"><label class="note">Инициатива<input class="inp" type="number" inputmode="numeric" data-iad="base" value="${esc(A.base)}" placeholder="20"></label>
    <label class="note">Действий<input class="inp" type="number" inputmode="numeric" data-iad="act" value="${esc(A.act)}" placeholder="${ACT_BASE}"></label></div>
   <label class="chk"><input type="checkbox" data-iad="sec" ${A.sec?"checked":""}> Скрыть имя от игроков («???»)</label>
   <div class="inline" style="gap:8px"><button class="btn small primary" data-ini="addroll">Бросить d20 и добавить</button><button class="btn small" data-ini="addfix">Добавить с этим числом</button></div>
   <p class="note" style="margin:6px 0 0">«Бросить»: в поле — база (2 × Ловкость + бонус), итог = база − d20, крит/провал как у всех. «С этим числом» — встанет ровно с ним, без броска.</p></div></details>`;}
function iniAddPick(id){const A=iniAddS(),n=id&&npcById(id);A.src=n?id:"";if(n){A.base=String(npcIni(n));A.act=String(Math.max(1,npcEff(n,"act")));A.sec=!!n.secret;}}
function iniAddDo(roll){const I=ROOM.init,A=iniAddS();if(!I)return;const base=Math.round(Number(String(A.base).replace("−","-")));
  if(String(A.base).trim()===""||!Number.isFinite(base)){toast("Укажите инициативу (число)");return;}
  const npc=A.src&&npcById(A.src);let name=npc?(npc.name||"Без имени"):String(A.name||"").trim();if(!name){toast("Введите имя");return;}
  if(npc){const k=I.list.filter(r=>r.k==="npc"&&r.id===npc.id).length;if(k)name+=" "+(k+1);}
  const r=roll?rnd(20):null,ab=Math.max(1,Math.round(Number(A.act))||ACT_BASE),hm=npc?npcEff(npc,"hp"):null;
  const row={k:npc?"npc":"x",id:npc?npc.id:null,n:name,sec:!!A.sec,base,r,ini:roll?base-r:base,agi:npc?npcEff(npc,"agi"):0,d100:rnd(100),ab,act:roll?iniActs(r,ab):ab,hp:hm,hpMax:hm,man:1};
  const c=I.list[I.cur];I.list.push(row);iniResort(I,c);initSave(true);
  const pos=I.list.indexOf(row)+1;const t=`${name}: инициатива ${row.ini}${roll?` (${base} − d20 ${r})`:""}, место ${pos}`;
  if(roll)try{gmRollPush("Инициатива: "+(row.sec?"??? ("+name+")":name)+" "+row.ini);}catch(e){}
  toast(t);if(!npc)A.name="";renderRoom();}
document.addEventListener("input",e=>{const t=e.target;if(!t.dataset||!t.dataset.iad||t.type==="checkbox"||t.tagName==="SELECT")return;iniAddS()[t.dataset.iad]=t.value;});
document.addEventListener("change",e=>{const t=e.target;if(!t.dataset||!t.dataset.iad)return;const A=iniAddS();
  if(t.dataset.iad==="src"){iniAddPick(t.value);t.blur();renderRoom();return;}
  if(t.type==="checkbox"){A.sec=t.checked;return;}});
document.addEventListener("toggle",e=>{const d=e.target;if(d&&d.classList&&d.classList.contains("iniadd"))iniAddS().open=d.open;},true);
'''
rep('/* ---------- Комната мастера (Supabase) ---------- */', js + '/* ---------- Комната мастера (Supabase) ---------- */')

css = r'''
/* ---- очередь боя руками ---- */
.iniadd{margin-top:10px;border:1px solid var(--line);border-radius:6px;padding:0 10px}
.iniadd>summary{cursor:pointer;padding:10px 0;font-weight:600;color:var(--accent)}
.iniadd-b{padding-bottom:10px}
.iadrow{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px}
.iadrow label{display:flex;flex-direction:column;gap:2px}.iadrow .inp{width:100%;box-sizing:border-box}
.initt td.ininum{text-align:center;padding:2px 4px}
.initt td.ininum>span{display:block;padding:2px 0}
.initt .mvb{display:block;width:30px;height:26px;margin:0 auto;padding:0;border:1px solid var(--line);border-radius:6px;background:none;color:inherit;font-size:12px;line-height:1;cursor:pointer}
.initt .inihp{width:48px}
@media (max-width:380px){.initt{font-size:14px}.initt th,.initt td{padding:4px 3px}.initt td.ininum{padding:2px 1px}.initt .mvb{width:26px}
 .initt .inihp{width:42px;padding:4px 2px}.initt td .note{font-size:11px}.initt td:last-child{padding-left:0;padding-right:0}}
.initt .mvb:disabled{opacity:.3;cursor:default}
</style>'''
i = s.index('</style>', s.index('<title>Сумрак 2096'))
s = s[:i] + css + s[i + len('</style>'):]
out.write_text(s, encoding='utf-8')
print('ok', out, len(s))
