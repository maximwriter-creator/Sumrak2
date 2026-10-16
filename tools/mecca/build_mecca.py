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

# ---- 2026-10-13: сноски очков, переход к подразделению, досье с картинки ----
s = rep(s, """      const unit = g.select('.co-unit').attr('x', 9 + w + 4).text('оч.');
      const uw = unit.node().getComputedTextLength();
      g.select('.co-bg').attr('width', 9 + w + 4 + uw + 7);
    });
  }""", """      let tw = w;
      if(!(tw > 0)) tw = String(d.v.toLocaleString('ru-RU')).length * 6.95;   // окно скрыто — мерить нельзя; шрифт моноширинный
      g.select('.co-unit').text('');
      d._w = 9 + tw + 7;
      g.select('.co-bg').attr('width', d._w);
    });
    placeCallouts();
  }
  // сноска не должна вылезать за край карты: если справа не помещается — уходит влево, у верхнего края — вниз
  function placeCallouts(){
    if(!projection) return;
    const t = d3.zoomTransform(svg.node());
    gCallouts.selectAll('.callout').each(function(d){
      if(!d._xy) return;
      const sx = t.x + d._xy[0] * t.k, sy = t.y + d._xy[1] * t.k, w = d._w || 40;
      let px = 10;
      if(sx + 10 + w > width - 4) px = (sx - 10 - w >= 4) ? -10 - w : Math.max(4 - sx, width - 4 - sx - w);
      const down = sy - 21 < 4, py = down ? 2 : -21;
      const g = d3.select(this);
      g.select('.co-pill').attr('transform', `translate(${px},${py})`);
      g.select('.co-lead').attr('x2', px < 0 ? px + w : px).attr('y2', down ? 11 : -10);
    });
  }""")
s = rep(s, """    gCallouts.selectAll('.callout').attr('transform', d => `translate(${d._xy}) scale(${1 / zoomK})`);
    svg.classed""", """    gCallouts.selectAll('.callout').attr('transform', d => `translate(${d._xy}) scale(${1 / zoomK})`);
    placeCallouts();
    svg.classed""")
# переход к блоку подразделения
s = rep(s, """    const card = el('article','unit');
    card.style.setProperty('--uc', unitColor(u));""", """    const card = el('article','unit');
    card.dataset.unit = u.id;
    card.style.setProperty('--uc', unitColor(u));""")
s = rep(s, """  // ---- unit dossier window ----""", """  function goToUnit(id){
    const u = unitById(id); if(!u) return;
    if(!modal.hidden) closeModal();
    if(!uModal.hidden) closeDossier();
    openState(u.faction);
    setTimeout(() => {
      const c = sBody.querySelector('[data-unit="' + id + '"]'); if(!c) return;
      c.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block:'start' });
      c.classList.add('unit-flash'); setTimeout(() => c.classList.remove('unit-flash'), 1800);
    }, 60);
  }
  // ---- unit dossier window ----""")
s = rep(s, """    if(u){ const uu = btn('meta-unit meta-link', null, () => openDossier(u.id));""", """    if(u){ const uu = btn('meta-unit meta-link', null, () => goToUnit(u.id));""")
# досье начинается с картинки подразделения
s = rep(s, """    if(u.image){ const pic = btn('dos-pic', null, () => openLightbox(u.image)); pic.setAttribute('aria-label','Открыть картинку подразделения'); pic.append(imgEl(u.image, 'unit-img', u.name)); panel.append(pic); }
""", "")
s = rep(s, """    head.append(eb, close);
    panel.append(head);
    const nr = el('div','dos-name');""", """    head.append(eb, close);
    panel.append(head);
    if(u.image){ const pic = btn('dos-pic dos-pic-top', null, () => openLightbox(u.image)); pic.setAttribute('aria-label','Открыть картинку подразделения'); pic.append(imgEl(u.image, 'unit-img', u.name)); panel.append(pic); }
    const nr = el('div','dos-name');""")
s = rep(s, """  .dos-text{ margin-bottom:0; }""", """  .dos-text{ margin-bottom:0; }
  .dos-pic.dos-pic-top{ margin:2px 0 14px; max-height:none; }
  .dos-pic.dos-pic-top .unit-img{ max-height:420px; object-fit:contain; background:#0b0b12; }
  .unit{ scroll-margin-top:72px; transition:box-shadow .3s ease; }
  .unit.unit-flash{ box-shadow:0 0 0 2px var(--uc), 0 0 22px color-mix(in srgb, var(--uc) 40%, transparent); }""")

out.write_text(s, encoding='utf-8')
print('ok', out, len(s))
