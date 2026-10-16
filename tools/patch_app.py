#!/usr/bin/env python3
"""Добавляет вкладку «Кампейн» (Проект Мекка) в приложение игрока.
   python3 patch_app.py app.html mecca.html out.html"""
import sys, json, re, pathlib
app = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
mecca = pathlib.Path(sys.argv[2]).read_text(encoding='utf-8')
out = pathlib.Path(sys.argv[3])

def rep(s, old, new, count=1):
    assert s.count(old) == count, f'не найдено ровно {count}: {old[:80]!r} ({s.count(old)})'
    return s.replace(old, new)

s = app
# если уже встроено (повторная сборка) — заменить только саму карту
import base64
# base64: сборка (build_www.py) не должна ничего менять внутри карты — ни ссылок, ни тегов, ни кавычек
b64 = base64.b64encode(mecca.encode('utf-8')).decode('ascii')
blob = '\n'.join(b64[i:i+1000] for i in range(0, len(b64), 1000))
TAG = '<script id="meccaSrc" type="text/plain">'
if 'id="meccaSrc"' in s:
    s = re.sub(r'<script id="meccaSrc" type="[^"]*">.*?</script>', lambda m: TAG + blob + '</script>', s, count=1, flags=re.S)
    s = s.replace('src=JSON.parse(document.getElementById("meccaSrc").textContent);', 'src=meccaDecode();')
    out.write_text(s, encoding='utf-8'); print('карта обновлена', out, len(s)); sys.exit()

s = rep(s, '"Кубы и тесты","Миссия","Комната","Лор"];', '"Кубы и тесты","Миссия","Комната","Лор","Кампейн"];')
s = rep(s, '<button role="tab" aria-selected="${STEP===12}" data-go="12">Лор</button>`;',
        '<button role="tab" aria-selected="${STEP===12}" data-go="12">Лор</button><button role="tab" aria-selected="${STEP===13}" data-go="13">Кампейн</button>`;')
s = rep(s, '$("#modeTabs").classList.toggle("six",$("#modeTabs").children.length>5);',
        '$("#modeTabs").classList.toggle("six",$("#modeTabs").children.length>5);$("#modeTabs").classList.toggle("seven",$("#modeTabs").children.length>6);')
s = rep(s, '[stClass,stStats,stBirth,stParents,stChar,stMark,stFlaw,stSheet,stAcademy,stDice,stMission,stRoom,stLore][STEP](R) + navBtns();',
        '[stClass,stStats,stBirth,stParents,stChar,stMark,stFlaw,stSheet,stAcademy,stDice,stMission,stRoom,stLore,stCampaign][STEP](R) + navBtns();\n  campShow(STEP===13);')
s = rep(s, 'if(STEP===9||STEP===10||STEP===11){STEP=7;render();scrollTo(0,0);return;}',
        'if(STEP===13){const f=campFrame();try{const w=f&&f.contentWindow;const open=w&&w.document.querySelector(\'.auth-dlg:not([hidden]), .modal:not([hidden]), .lightbox:not([hidden]), .m-overlay:not([hidden]), [role="dialog"]:not([hidden])\');if(open){w.document.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape",bubbles:true}));return;}}catch(e){}}\n'
        '    if(STEP===9||STEP===10||STEP===11||STEP===12||STEP===13){STEP=7;render();scrollTo(0,0);return;}')
s = rep(s, '    <main id="main"></main>\n  </div>\n', '    <main id="main"></main>\n  </div>\n  <div id="campHost" hidden></div>\n')

css = r'''
/* ---- Кампейн: Проект Мекка ---- */
@media (max-width:560px){#modeTabs.seven{grid-template-columns:repeat(4,minmax(0,1fr))!important}#modeTabs.seven button{font-size:14px;letter-spacing:0;padding:8px 2px}#modeTabs.seven button:nth-child(n+5){border-top:1px solid var(--line)}#modeTabs.seven button:nth-child(5){border-left:0}}
@media (min-width:561px){#modeTabs.seven button{font-size:12px;letter-spacing:-.01em;padding-left:2px;padding-right:2px}}
#campHost{margin-top:14px;border:1px solid var(--line);border-radius:3px;overflow:hidden;background:#0a0a10}
#campHost iframe{display:block;width:100%;border:0;background:#0a0a10;height:70vh}
body.camp #main{display:none}
body.camp .layout{margin-top:0}
@media (max-width:700px){#campHost{margin:10px -2px 0}}
@media print{#campHost{display:none!important}}
</style>'''
# CSS — перед первым закрытием стилей в <head> приложения
i = s.index('</style>', s.index('<title>Сумрак 2096'))
s = s[:i] + css + s[i+len('</style>'):]

js = r'''
/* ---------- Кампейн: Проект Мекка (карта государств, общая база) ---------- */
function stCampaign(){return "";}
var CAMP;  /* без «=null»: приложение может открыться сразу на «Кампейн», и окно карты уже создано */
function campFrame(){return CAMP;}
function meccaDecode(){const el=document.getElementById("meccaSrc");if(!el)throw new Error("нет блока meccaSrc");
  const b=atob(el.textContent.replace(/[^A-Za-z0-9+/=]/g,""));const u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);
  const h=new TextDecoder("utf-8").decode(u);if(h.length<1000)throw new Error("блок пустой");return h;}
function campFit(){if(!CAMP)return;const h=$("#campHost");const top=h.getBoundingClientRect().top;CAMP.style.height=Math.max(420,Math.round(window.innerHeight-Math.max(0,top)-10))+"px";}
function campShow(on){
  document.body.classList.toggle("camp",on);
  const host=$("#campHost");host.hidden=!on;
  if(!on)return;
  if(!CAMP)CAMP=host.querySelector("iframe");
  if(!CAMP){
    CAMP=document.createElement("iframe");CAMP.title="Проект Мекка — карта государств";
    CAMP.setAttribute("allow","clipboard-write");
    let src="";try{src=meccaDecode();}catch(e){src="<p style='color:#fff;font:16px sans-serif;padding:20px'>Карта не встроена в эту сборку ("+String(e&&e.message||e).replace(/[<>&]/g,"")+").</p>";}
    CAMP.srcdoc=src;host.appendChild(CAMP);
    window.addEventListener("resize",()=>{if(STEP===13)campFit();});
  }
  requestAnimationFrame(campFit);setTimeout(campFit,300);
  /* пока вкладка была скрыта, карта не могла измерить себя — перерисовать после показа */
  const kick=()=>{try{CAMP.contentWindow.dispatchEvent(new Event("resize"));}catch(e){}};
  requestAnimationFrame(()=>requestAnimationFrame(kick));setTimeout(kick,350);
}
'''
s = rep(s, '/* ---------- Комната мастера (Supabase) ---------- */', js + '/* ---------- Комната мастера (Supabase) ---------- */')

# сама карта — отдельным JSON-блоком рядом с данными книги
s = rep(s, '<script id="book" type="application/json">',
        TAG + blob + '</script>\n<script id="book" type="application/json">')
out.write_text(s, encoding='utf-8')
print('ok', out, len(s))
