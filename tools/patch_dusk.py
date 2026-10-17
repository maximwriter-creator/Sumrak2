#!/usr/bin/env python3
"""Очко судьбы за сумрачную карму: светлая + тёмная в выбранной пропорции.
   python3 patch_dusk.py in.html out.html   (после patch_hints.py)"""
import sys, pathlib
s = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
out = pathlib.Path(sys.argv[2])

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, f'не найдено ровно {count}: {old[:90]!r} ({s.count(old)})'
    s = s.replace(old, new)

if 'function duskOpen' in s:
    sys.exit('Уже применено')

# окно «Очки судьбы»: четвёртая кнопка
rep('<button class="btn big" id="fateDark" data-ico="dark"><span class="lbl">За 5 тёмной кармы</span></button>',
    '<button class="btn big" id="fateDark" data-ico="dark"><span class="lbl">За 5 тёмной кармы</span></button><button class="btn big" id="fateDusk" data-ico="dusk"><span class="lbl">За 5 сумрачной кармы</span></button>')
rep('["light","dark"].forEach(k=>{const fc=fateCost(k);const b=$(k==="light"?"#fateLight":"#fateDark");',
    '["light","dark","dusk"].forEach(k=>{const fc=fateCost(k);const b=$(k==="light"?"#fateLight":k==="dark"?"#fateDark":"#fateDusk");')
rep('${k==="light"?"светлой":"тёмной"} кармы`;}', '${k==="light"?"светлой":k==="dark"?"тёмной":"сумрачной"} кармы`;}')
rep('["fateTest","fateLight","fateDark","fateBurn"].forEach(id=>$("#"+id).disabled=f.left<=0);',
    '["fateTest","fateLight","fateDark","fateDusk","fateBurn"].forEach(id=>{const b=$("#"+id);if(b)b.disabled=f.left<=0;});')
rep('    case "fateDark": fateActivate("dark");break;', '    case "fateDark": fateActivate("dark");break;\n    case "fateDusk": duskOpen("fate");break;')
# оплата
rep('else{const k=how;const fc=fateCost(k);let cost=fc.c;let bk="";',
    'else if(how==="dusk"){const pr=payDusk();if(!pr.ok){renderFate(pr.msg);return;}var kmsg=pr.msg+" ";}\n  else{const k=how;const fc=fateCost(k);let cost=fc.c;let bk="";')
rep('function payFate(how){const f=fateInfo();', 'function payFate(how){if(how==="dusk")return payDusk();const f=fateInfo();')
# способность отметки судьбы: оплата сумраком
rep('''>${icon("dark")}${fd} тёмной кармы <span style="opacity:.85;font-weight:400">(есть ${K("dark")})</span></button>''',
    '''>${icon("dark")}${fd} тёмной кармы <span style="opacity:.85;font-weight:400">(есть ${K("dark")})</span></button><button class="btn big primary" data-duskopen="mark" ${K("light")+K("dark")<fateCost("dusk").c?"disabled":""}>${bigIco("dusk")}${fateCost("dusk").c} сумрачной кармы <span style="opacity:.85;font-weight:400">(свет + тьма)</span></button>''')
# иконка сумрака: половина солнца, половина луны
rep("  dice:'<rect", "  dusk:'<path d=\"M12 3v18\"/><path d=\"M12 7a5 5 0 0 0 0 10\"/><path d=\"M12 3a9 9 0 0 1 0 18\"/><path d=\"M5 5l1.4 1.4M3 12h2M5 19l1.4-1.4\"/>',\n  dice:'<rect")

js = r'''
/* ---------- Очко судьбы за сумрачную карму ---------- */
var DUSK=null;
function duskHave(){const R=compute(C);return {L:Math.max(0,(R.extra.light||0)+(C.adj.light||0)),D:Math.max(0,(R.extra.dark||0)+(C.adj.dark||0))};}
function duskOpen(ctx){const fc=fateCost("dusk");let cost=fc.c,bk="";if(fc.baikal){const b=baikalCut();cost=Math.max(0,cost-b.r);bk=b.txt;}
  const h=duskHave();let L=Math.max(cost-h.D,Math.min(h.L,Math.ceil(cost/2)));L=Math.max(0,Math.min(L,cost));
  DUSK={ctx,cost,bk,L,why:fc.why};duskRender();}
function duskRender(){const d=DUSK;if(!d)return;const h=duskHave(),D=d.cost-d.L,enough=d.L<=h.L&&D<=h.D;
  const html=`<div class="duskbox"><div class="q">Сумрачная карма: всего ${d.cost}${d.bk?` <span class="note">${esc(d.bk)}</span>`:""}</div>
    <p class="note" style="margin:2px 0 8px">Выберите, сколько потратить светлой — остальное спишется из тёмной.</p>
    <div class="duskrow"><span class="dn">${icon("light")} Светлой</span><button class="pm" data-dusk="-" aria-label="Меньше светлой" ${d.L<=0?"disabled":""}>−</button><b class="dv">${d.L}</b><button class="pm" data-dusk="+" aria-label="Больше светлой" ${d.L>=d.cost?"disabled":""}>+</button><span class="note">есть ${h.L}</span></div>
    <div class="duskrow"><span class="dn">${icon("dark")} Тёмной</span><span></span><b class="dv">${D}</b><span></span><span class="note">есть ${h.D}</span></div>
    ${enough?"":`<div class="warnbox" style="margin-top:6px">${h.L+h.D<d.cost?`Не хватает кармы: всего есть ${h.L+h.D}, нужно ${d.cost}.`:`Столько ${d.L>h.L?"светлой":"тёмной"} кармы нет — сдвиньте распределение.`}</div>`}
    <div class="inline" style="gap:10px;margin-top:8px"><button class="btn big primary" data-dusk="go" ${enough?"":"disabled"}>${bigIco("dusk")}<span>Оплатить ${d.L} + ${D}</span></button><button class="jump ph" data-dusk="cancel">отмена</button></div></div>`;
  const el=d.ctx==="fate"?$("#fateRes"):$("#mkRes");if(el)el.innerHTML=html;}
function payDusk(){const d=DUSK;if(!d)return {ok:false,msg:"Не выбрано, сколько светлой и тёмной кармы потратить."};
  const h=duskHave(),D=d.cost-d.L;if(d.L>h.L||D>h.D)return {ok:false,msg:`Не хватает кармы: светлой есть ${h.L}, тёмной ${h.D}.`};
  C.adj.light=(C.adj.light||0)-d.L;C.adj.dark=(C.adj.dark||0)-D;DUSK=null;
  return {ok:true,msg:`Потрачено ${d.L} светлой и ${D} тёмной кармы (Сумрак)${d.bk}${d.why&&d.why.length?" ["+d.why.join(", ")+"]":""}.`};}
document.addEventListener("click",e=>{const b=e.target.closest("[data-dusk],[data-duskopen]");if(!b)return;
  if(b.dataset.duskopen){duskOpen(b.dataset.duskopen);return;}
  const d=DUSK;if(!d)return;const a=b.dataset.dusk;
  if(a==="-"){d.L=Math.max(0,d.L-1);duskRender();return;}
  if(a==="+"){d.L=Math.min(d.cost,d.L+1);duskRender();return;}
  if(a==="cancel"){DUSK=null;const el=d.ctx==="fate"?$("#fateRes"):$("#mkRes");if(el)el.innerHTML="";if(d.ctx==="mark")MKPEND=null;return;}
  if(a==="go"){if(d.ctx==="fate"){fateActivate("dusk");return;}
    const box=$("#mkRes");if(!box)return;const t=document.createElement("button");t.dataset.mkgo="dusk";t.hidden=true;box.appendChild(t);t.click();}});
'''
rep('/* ---------- Комната мастера (Supabase) ---------- */', js + '/* ---------- Комната мастера (Supabase) ---------- */')

css = r'''
/* ---- сумрачная карма ---- */
.duskbox{border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin-top:6px;background:var(--panel)}
.duskbox .q{font-weight:700}
.duskrow{display:grid;grid-template-columns:minmax(0,1fr) 44px 36px 44px auto;align-items:center;gap:6px;margin:6px 0}
.duskrow .dn{display:inline-flex;align-items:center;gap:6px}
.duskrow .dv{text-align:center;font-size:20px;font-variant-numeric:tabular-nums}
.duskrow .pm{width:44px;height:40px;font-size:20px}
</style>'''
i = s.index('</style>', s.index('<title>Сумрак 2096'))
s = s[:i] + css + s[i + len('</style>'):]
out.write_text(s, encoding='utf-8')
print('ok', out, len(s))
