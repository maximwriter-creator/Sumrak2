#!/usr/bin/env python3
"""Веб-версия (PWA) для GitHub Pages: www/index.html → site/.
   Добавляет манифест, иконки, service worker (офлайн), плашку «Доступна новая версия»
   и одноразовую подсказку «На экран Домой» для iPhone. Запуск после build_www.py."""
import hashlib, pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent
WWW = ROOT / 'www' / 'index.html'
WEB = ROOT / 'web'
SITE = ROOT / 'site'
if not WWW.exists():
    sys.exit('Нет www/index.html — сначала python3 build_www.py')

html = WWW.read_text(encoding='utf-8')
ver = hashlib.sha256(html.encode('utf-8')).hexdigest()[:12]

HEAD = '''<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#130321">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Сумрак 2096">
<link rel="apple-touch-icon" href="icons/icon-180.png">
'''
BODY = '''<div id="pwaUpd" hidden style="position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom,0px));z-index:9999;display:flex;gap:10px;align-items:center;justify-content:space-between;background:#2a1747;color:#fff;padding:10px 14px;border-radius:6px;font:15px/1.3 'PT Sans',Arial,sans-serif;box-shadow:0 8px 24px rgba(0,0,0,.4)">
<span>Доступна новая версия</span><button type="button" id="pwaUpdBtn" style="background:#fff;color:#2a1747;border:0;border-radius:4px;padding:7px 12px;font:inherit;font-weight:700">Обновить</button></div>
<div id="pwaA2hs" hidden style="position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom,0px));z-index:9998;background:#1d1030;color:#fff;padding:12px 14px;border-radius:6px;font:15px/1.4 'PT Sans',Arial,sans-serif;box-shadow:0 8px 24px rgba(0,0,0,.4)">
Чтобы приложение работало без интернета и открывалось как отдельное: «Поделиться» → «На экран Домой». <button type="button" id="pwaA2hsX" style="float:right;background:none;border:0;color:#fff;font-size:20px;line-height:1">×</button></div>
<script>
(function(){
  if(!('serviceWorker' in navigator)) return;
  var upd=document.getElementById('pwaUpd'), reloading=false;
  navigator.serviceWorker.register('sw.js').then(function(reg){
    function offer(w){ upd.hidden=false; document.getElementById('pwaUpdBtn').onclick=function(){ w.postMessage('skipWaiting'); }; }
    if(reg.waiting && navigator.serviceWorker.controller) offer(reg.waiting);
    reg.addEventListener('updatefound', function(){ var w=reg.installing; w.addEventListener('statechange', function(){ if(w.state==='installed' && navigator.serviceWorker.controller) offer(w); }); });
    document.addEventListener('visibilitychange', function(){ if(!document.hidden) reg.update().catch(function(){}); });
  }).catch(function(){});
  navigator.serviceWorker.addEventListener('controllerchange', function(){ if(reloading) return; reloading=true; location.reload(); });
  try{
    var ios=/iphone|ipad|ipod/i.test(navigator.userAgent), standalone=navigator.standalone||matchMedia('(display-mode: standalone)').matches;
    if(ios && !standalone && !localStorage.getItem('pwaA2hsSeen')){ var a=document.getElementById('pwaA2hs'); a.hidden=false;
      document.getElementById('pwaA2hsX').onclick=function(){ a.hidden=true; try{localStorage.setItem('pwaA2hsSeen','1');}catch(e){} }; }
  }catch(e){}
})();
</script>
'''
i = html.find('</head>')
html = html[:i] + HEAD + html[i:]
j = html.rfind('</body>')
if j < 0:
    sys.exit('Нет </body> в www/index.html')
html = html[:j] + BODY + html[j:]

if SITE.exists():
    shutil.rmtree(SITE)
SITE.mkdir()
(SITE / 'index.html').write_text(html, encoding='utf-8')
shutil.copy(WEB / 'manifest.webmanifest', SITE / 'manifest.webmanifest')
shutil.copytree(WEB / 'icons', SITE / 'icons')
(SITE / 'sw.js').write_text((WEB / 'sw.js').read_text(encoding='utf-8').replace('__VERSION__', ver), encoding='utf-8')
(SITE / '.nojekyll').write_text('')
print('site/ готов, версия', ver)
