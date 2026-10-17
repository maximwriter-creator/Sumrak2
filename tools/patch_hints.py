#!/usr/bin/env python3
"""Подсказки по кнопке, раскрывающиеся заголовки в «Очках судьбы», крупные кнопки с иконками.
   python3 patch_hints.py in.html out.html   (после patch_rolls.py, до patch_app.py)"""
import sys, pathlib, re
s = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
out = pathlib.Path(sys.argv[2])

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, f'не найдено ровно {count}: {old[:90]!r} ({s.count(old)})'
    s = s.replace(old, new)

if 'function hintBtn' in s:
    sys.exit('Уже применено')

H4 = '<h4 style="font-family:var(--narrow);margin:12px 0 4px">'

# ---------- Лист персонажа ----------
rep('<div><h2>Лист персонажа</h2><p class="lead" style="margin-bottom:12px">Здесь ведётся персонаж по ходу кампании: опыт, таланты, снаряжение, одолжения и миссии.</p></div>',
    '<div><h2>Лист персонажа</h2></div>')
rep('<p class="note">Урон: сначала броня (минус ББ атаки), затем прочность брони, остаток снижает Устойчивость. Инициатива: удвоенная Ловкость минус d20. <span class="noprint">Нажмите на любой блок характеристики, Устойчивости или Инициативы, чтобы бросить d20.</span></p>',
    '${hintBtn("stats","<p>Нажмите на любой блок характеристики, Устойчивости или Инициативы, чтобы бросить d20.</p><p>Урон: сначала броня (минус ББ атаки), затем прочность брони, остаток снижает Устойчивость.</p><p>Инициатива: удвоенная Ловкость минус d20.</p>")}')

# ---------- Миссия: правки только на миссию ----------
rep('''  if(st)st.insertAdjacentHTML("beforebegin",`<div class="mstip" style="margin:0 0 8px">Кнопки − и + меняют значения только на эту миссию, в листе персонажа их нет.${act.length?` Сейчас: <b>${act.map(([k,v])=>esc(fxLabel(k))+" "+sgn(Number(v))).join(", ")}</b> <button class="jump ph" data-msreset="1">сбросить</button>`:""}</div>`);}''',
    '''  if(st)st.insertAdjacentHTML("beforebegin",`${act.length?`<div class="mstip" style="margin:0 0 8px">Только на эту миссию: <b>${act.map(([k,v])=>esc(fxLabel(k))+" "+sgn(Number(v))).join(", ")}</b> <button class="jump ph" data-msreset="1">сбросить</button></div>`:""}${hintBtn("mispm","<p>Кнопки − и + меняют значения только на эту миссию, в листе персонажа их нет.</p><p>Нажмите на блок характеристики, Устойчивости или Инициативы, чтобы бросить d20.</p><p>Урон: сначала броня (минус ББ атаки), затем прочность брони, остаток снижает Устойчивость.</p><p>Инициатива: удвоенная Ловкость минус d20.</p>")}`);}''')

# ---------- Бой ----------
rep('''<p class="note" style="margin:4px 0 0">Против ближнего боя — уклонение или парирование, против дальнего — только уклонение. Перезарядка: ${reloadCost()} ${reloadCost()===1?"действие":"действия"}${hasFastReload()?" (Быстрая перезарядка)":""}. Атаки и предметы списывают действия; если их не хватает, недостача спишется в следующем раунде.</p></div>`;}''',
    '''${hintBtn("combat",`<p>Против ближнего боя — уклонение или парирование, против дальнего — только уклонение.</p><p>Перезарядка: ${reloadCost()} ${reloadCost()===1?"действие":"действия"}${hasFastReload()?" (Быстрая перезарядка)":""}.</p><p>Атаки и предметы списывают действия; если их не хватает, недостача спишется в следующем раунде.</p>`)}</div>`;}''')

# ---------- Запрос на влияние ----------
rep('''  <p class="note">${inflSpecial()?"Место рождения Индия: у обычного запроса 19 не автоматический провал, а 20 тратит один запрос вместо двух; у сложного и невозможного 19 на кубе не даёт лишних степеней провала, а 20 даёт 3 вместо 7.":"Обычный запрос: 19 — автоматический провал, 20 — провал и тратит два запроса. Сложный и невозможный: кубы складываются; на каждом кубе 1 даёт +7 степеней успеха, 2 — +3, 19 — 3 степени провала, 20 — 7."}</p>''',
    '''  ${hintBtn("infl",inflSpecial()?"<p>Место рождения Индия: у обычного запроса 19 не автоматический провал, а 20 тратит один запрос вместо двух.</p><p>У сложного и невозможного 19 на кубе не даёт лишних степеней провала, а 20 даёт 3 вместо 7.</p>":"<p>Обычный запрос: 19 — автоматический провал, 20 — провал и тратит два запроса.</p><p>Сложный и невозможный: кубы складываются; на каждом кубе 1 даёт +7 степеней успеха, 2 — +3, 19 — 3 степени провала, 20 — 7.</p>")}''')
rep('''Влияние: <b>${v}</b>${sum?`, с бонусами <b>${v+sum}</b>`:""}. Бросок d20, успех если выпало не больше значения.</p>''',
    '''Влияние: <b>${v}</b>${sum?`, с бонусами <b>${v+sum}</b>`:""}. Бросок d20: успех, если выпало не больше значения.</p>''')
rep('<div class="inline"><button class="btn primary" id="inflRoll">Бросить запрос</button>',
    '<div class="inline"><button class="btn big primary" id="inflRoll">${icon("infl")}<span>Бросить запрос</span></button>')

# ---------- Очки судьбы: статичная часть окна ----------
rep('''  <h4 style="font-family:var(--narrow);margin:10px 0 4px">Активировать</h4>
  <p class="note">Нужно пройти тест на Волю или потратить 5 любой кармы. Затем бросьте 2d6 на Безудержные Силы, как при обычном Взывании. Активированное очко возвращается в конце миссии.</p>
  <div class="inline"><button class="btn small primary" id="fateTest">Тест на Волю</button><button class="btn small" id="fateLight">За 5 светлой кармы</button><button class="btn small" id="fateDark">За 5 тёмной кармы</button></div>''',
    '''  <details class="hsec" data-hint="fate-act"><summary><h4 style="font-family:var(--narrow);margin:10px 0 4px">Активировать</h4><span class="hsec-i" aria-hidden="true"></span></summary><div class="hintbody"><p>Нужно пройти тест на Волю или потратить 5 любой кармы.</p><p>Затем бросьте 2d6 на Безудержные Силы, как при обычном Взывании.</p><p>Активированное очко возвращается в конце миссии.</p></div></details>
  <div class="bigbtns"><button class="btn big primary" id="fateTest" data-ico="wil"><span class="lbl">Тест на Волю</span></button><button class="btn big" id="fateLight" data-ico="light"><span class="lbl">За 5 светлой кармы</span></button><button class="btn big" id="fateDark" data-ico="dark"><span class="lbl">За 5 тёмной кармы</span></button></div>''')
rep('''<button class="btn small primary" id="fateUfRoll">Бросить 2d6</button>''', '''<button class="btn big primary" id="fateUfRoll" data-ico="dice"><span class="lbl">Бросить 2d6</span></button>''')
rep('''<details><summary>Что даёт активация</summary>''', '''<details class="hsec" data-hint="fate-gives"><summary><h4 style="font-family:var(--narrow);margin:12px 0 4px">Что даёт активация</h4><span class="hsec-i" aria-hidden="true"></span></summary>''')
rep('''  <h4 style="font-family:var(--narrow);margin:12px 0 4px">Другое</h4>
  <p class="note">Сжигается очко навсегда и только в крайнем случае: чтобы избежать смерти, отменить Безудержные Силы и т.п. Особые способы использования есть у класса и Отметки судьбы.</p>
  <div class="inline"><button class="btn small" id="fateBurn" style="color:var(--warn)">Сжечь очко</button><button class="btn small" id="fateUnburn">Вернуть сожжённое</button><button class="btn small" id="fateReset">Миссия завершена: вернуть активированные</button></div>''',
    '''  <details class="hsec" data-hint="fate-other"><summary><h4 style="font-family:var(--narrow);margin:12px 0 4px">Другое</h4><span class="hsec-i" aria-hidden="true"></span></summary><div class="hintbody"><p>Сжигается очко навсегда и только в крайнем случае: чтобы избежать смерти, отменить Безудержные Силы и т.п.</p><p>Особые способы использования есть у класса и Отметки судьбы.</p></div></details>
  <div class="bigbtns"><button class="btn big" id="fateBurn" data-ico="burn" style="color:var(--warn)"><span class="lbl">Сжечь очко</span></button><button class="btn big" id="fateUnburn" data-ico="undo"><span class="lbl">Вернуть сожжённое</span></button><button class="btn big" id="fateReset" data-ico="reset"><span class="lbl">Миссия завершена: вернуть активированные</span></button></div>''')
# подпись кнопок кармы меняется кодом — менять только текст, не стирая иконку
rep('''if(b)b.textContent=`За ${fc.c}${fc.baikal?"−d5":""} ${k==="light"?"светлой":"тёмной"} кармы`;''',
    '''if(b){const l=b.querySelector(".lbl");(l||b).textContent=`За ${fc.c}${fc.baikal?"−d5":""} ${k==="light"?"светлой":"тёмной"} кармы`;}''')
rep('function renderFate(msg){const f=fateInfo();', 'function renderFate(msg){bigIcons();const f=fateInfo();')

# ---------- Очки судьбы: отметка судьбы и место рождения ----------
rep('''return `<h4 style="font-family:var(--narrow);margin:12px 0 4px">Отметка судьбы: ${esc(mk.name)}</h4><p class="note">После нажатия выберите оплату: светлая карма, тёмная карма или тест на Волю. Затем тратится Очко судьбы и сразу бросается 2d6 на Безудержные Силы. Осталось очков: <b>${f.left}</b> из ${f.tot}.</p><details class="iblk"><summary>Что даёт Очко судьбы</summary><div class="rules">${paras(sp)}</div></details>${on}''',
    '''return `<details class="hsec" data-hint="fate-mark"><summary><h4 style="font-family:var(--narrow);margin:12px 0 4px">Отметка судьбы: ${esc(mk.name)}</h4><span class="hsec-i" aria-hidden="true">${hintIco()}</span></summary><div class="hintbody"><p>После нажатия выберите оплату: светлая карма, тёмная карма или тест на Волю. Затем тратится Очко судьбы и сразу бросается 2d6 на Безудержные Силы.</p><p class="hsub">Что даёт Очко судьбы</p><div class="rules">${paras(sp)}</div></div></details>${on}''')
rep('''return `<h4 style="font-family:var(--narrow);margin:12px 0 4px">Место рождения: ${esc(bf.name)}</h4><details class="iblk" open><summary>Правило</summary><div class="rules">${paras(bf.text)}</div></details>${act}''',
    '''return `<details class="hsec" data-hint="fate-birth"><summary><h4 style="font-family:var(--narrow);margin:12px 0 4px">Место рождения: ${esc(bf.name)}</h4><span class="hsec-i" aria-hidden="true">${hintIco()}</span></summary><div class="hintbody rules">${paras(bf.text)}</div></details>${act}''')
# кнопки способностей отметки и места рождения — крупные
for fn in ('function markFateUI(f){', 'function birthFateUI(f){'):
    a = s.index(fn); b = s.index('\nfunction ', a + 10)
    seg = s[a:b]
    seg2 = re.sub(r'class="btn small( primary)?" (data-(?:mk|bf)=)', lambda m: f'class="btn big{m.group(1) or ""}" {m.group(2)}', seg)
    assert seg2 != seg, fn
    s = s[:a] + seg2 + s[b:]
# выбор оплаты для способности отметки
rep('''<button class="btn small primary" data-mkgo="light" ${K("light")<fl?"disabled":""}>''', '''<button class="btn big primary" data-mkgo="light" ${K("light")<fl?"disabled":""}>${icon("light")}''')
rep('''<button class="btn small primary" data-mkgo="dark" ${K("dark")<fd?"disabled":""}>''', '''<button class="btn big primary" data-mkgo="dark" ${K("dark")<fd?"disabled":""}>${icon("dark")}''')
rep('''<button class="btn small" data-mkgo="test">Тест на Волю (${R.tot.wil})</button>''', '''<button class="btn big" data-mkgo="test">${icon("wil")}<span>Тест на Волю (${R.tot.wil})</span></button>''')

js = r'''
/* ---------- Подсказки по кнопке и крупные кнопки с иконками ---------- */
function hintSet(){return window.__hintOpen||(window.__hintOpen=new Set());}
function hintIco(){return `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9.2"/><path d="M9.6 9.3a2.5 2.5 0 0 1 4.8 1c0 1.7-2.4 2.2-2.4 3.7"/><path d="M12 17.2h.01"/></svg>`;}
function hintBtn(id,html,label){const o=hintSet().has(id);return `<details class="hint noprint" data-hint="${id}" ${o?"open":""}><summary class="hintbtn">${hintIco()}<span>${label||"Подсказка"}</span></summary><div class="hintbody">${html}</div></details>`;}
function bigIco(k){const P={
  burn:'<path d="M12 3c1 3.5 5 5.2 5 10a5 5 0 0 1-10 0c0-2.4 1.3-3.8 2.4-5 .3 1.6 1 2.6 2.1 3.1C11 8.6 11.2 5.6 12 3z"/>',
  undo:'<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
  reset:'<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>',
  dice:'<rect x="4" y="4" width="16" height="16" rx="3"/><circle cx="9" cy="9" r="1.2" fill="currentColor"/><circle cx="15" cy="15" r="1.2" fill="currentColor"/><circle cx="15" cy="9" r="1.2" fill="currentColor"/><circle cx="9" cy="15" r="1.2" fill="currentColor"/>'};
  if(P[k])return `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[k]}</svg>`;
  return icon(k);}
function bigIcons(){document.querySelectorAll("[data-ico]").forEach(b=>{if(!b.querySelector("svg"))b.insertAdjacentHTML("afterbegin",bigIco(b.dataset.ico));});
  document.querySelectorAll(".hsec-i:empty").forEach(x=>x.innerHTML=hintIco());}
document.addEventListener("toggle",e=>{const d=e.target;if(!(d instanceof HTMLElement)||!d.dataset.hint)return;if(d.open)hintSet().add(d.dataset.hint);else hintSet().delete(d.dataset.hint);},true);
document.addEventListener("DOMContentLoaded",bigIcons);
'''
rep('/* ---------- Комната мастера (Supabase) ---------- */', js + '/* ---------- Комната мастера (Supabase) ---------- */')

css = r'''
/* ---- подсказки по кнопке ---- */
.hint{margin:8px 0}
.hint>summary{list-style:none}
.hint>summary::-webkit-details-marker{display:none}
.hintbtn{display:inline-flex;align-items:center;gap:7px;min-height:38px;padding:6px 14px 6px 10px;border:1px solid var(--line);border-radius:999px;background:var(--panel);color:var(--accent);font-family:var(--narrow);font-size:16px;cursor:pointer;user-select:none}
.hintbtn .ico{width:20px;height:20px}
.hint[open]>.hintbtn{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
.hintbody{margin-top:8px;padding:10px 12px;border-left:3px solid var(--accent);background:var(--soft);border-radius:4px;font-size:15px;line-height:1.45}
.hintbody p{margin:0 0 6px}.hintbody p:last-child{margin-bottom:0}
.hintbody .hsub{font-weight:700;margin-top:8px}
/* ---- раскрывающиеся заголовки ---- */
.hsec>summary{list-style:none;display:flex;align-items:center;gap:8px;cursor:pointer}
.hsec>summary::-webkit-details-marker{display:none}
.hsec>summary h4{display:inline}
.hsec-i{display:inline-flex;color:var(--accent)}
.hsec-i .ico{width:20px;height:20px}
.hsec[open] .hsec-i{opacity:.55}
.hsec>.hintbody{margin:2px 0 10px}
/* ---- крупные кнопки с иконками ---- */
.bigbtns{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:6px 0 10px}
.btn.big{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:52px;padding:10px 14px;font-size:17px;line-height:1.2;text-align:left;border-radius:8px}
.btn.big .ico{width:24px;height:24px;flex:none}
.btn.big:disabled{opacity:.45}
.btn.big .ico{color:inherit}
.btn.big:not(.primary) .ico{color:var(--accent)}
.hint[open]>.hintbtn .ico{color:inherit}
.hintbtn .ico{color:var(--accent)}
body.mis .hint[data-hint="stats"]{display:none}
@media print{.hint{display:none!important}}
</style>'''
i = s.index('</style>', s.index('<title>Сумрак 2096'))
s = s[:i] + css + s[i + len('</style>'):]
out.write_text(s, encoding='utf-8')
print('ok', out, len(s))
