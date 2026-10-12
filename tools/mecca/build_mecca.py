#!/usr/bin/env python3
"""Собирает mecca.html: опубликованная карта + d3 внутри файла + база Supabase + вход редактора.
   python3 build_mecca.py [map_base.html] [out.html]"""
import sys, pathlib
here = pathlib.Path(__file__).parent
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else here / 'map_base.html').read_text(encoding='utf-8')
out = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else here / 'mecca.html')
d3 = (here / 'd3.min.js').read_text(encoding='utf-8')
shim = (here / 'shim.js').read_text(encoding='utf-8')
auth = (here / 'auth.html').read_text(encoding='utf-8')

def rep(s, old, new, count=1):
    assert s.count(old) == count, f'не найдено ровно {count}: {old[:70]!r} ({s.count(old)})'
    return s.replace(old, new)

s = src
s = rep(s, '<title>Сумрак 2096 — Карта государств</title>', '<title>Проект Мекка — Сумрак 2096</title>')
s = rep(s, '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>',
        '<script>' + d3 + '</script>\n<script>' + shim + '</script>')
s = rep(s, '<h1 class="page-title">Мекка</h1>', '<h1 class="page-title">Мекка</h1>\n' + auth)
# права редактора переключаются без перезагрузки
s = rep(s, "    document.body.classList.toggle('can-edit', isOwner);\n",
        "    document.body.classList.toggle('can-edit', isOwner);\n"
        "    window.__meccaOwner = on => { isOwner = !!on; document.body.classList.toggle('can-edit', isOwner && !!db);"
        " try{ refreshAll(); renderUserZones(); renderHiddenRow(); if(mState && !mState.editing && !modal.hidden) renderModal(); }catch(e){ console.error(e); } };\n")
s = rep(s, "  function toast(msg, bad, action){", "  window.__meccaToast = (m, b) => toast(m, b);\n  function toast(msg, bad, action){")
s = rep(s, "'Миссии недоступны в этом просмотре.'", "'Нет связи с общей базой — миссии появятся, когда будет интернет.'")
s = rep(s, "'Подразделения и миссии недоступны в этом просмотре.'", "'Нет связи с общей базой — подразделения появятся, когда будет интернет.'")
out.write_text(s, encoding='utf-8')
print('ok', out, len(s))
