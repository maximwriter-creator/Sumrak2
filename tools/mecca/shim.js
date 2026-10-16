/* ===== Мекка: общая база Supabase вместо базы артефакта =====
   Тот же интерфейс, что ждёт карта (window.claude.use('db' | 'user')),
   но данные лежат в таблице public.mecca_docs (см. mecca.sql и mecca-access.sql).
   Кампейн закрыт: без логина и пароля данные не загружаются. Читать и писать можно только
   через функции сервера, которые проверяют пароль (роль edit — правка, view — только просмотр).
   Если на сервере ещё старая схема (чтение открыто), модуль работает по-старому. */
(function(){
  const DEF = { url:"https://jwvyixjrpfmcnpdxmyvq.supabase.co", key:"sb_publishable_TMmU-o5j_7BBXm9p3pHESQ_QM5DuQMT" };
  const WATCH = ['missions','units','veilzones','veilstate','readiness'];
  const CACHE_KEY = 'mecca_cache_v1', AUTH_KEY = 'mecca_editor_v1';
  let P = null;
  try{ if(window.parent && window.parent !== window){ void window.parent.document; P = window.parent; } }catch(e){ P = null; }

  const ls = {
    get(k){ try{ return JSON.parse(localStorage.getItem(k) || 'null'); }catch(e){ return null; } },
    set(k, v){ try{ if(v == null) localStorage.removeItem(k); else localStorage.setItem(k, JSON.stringify(v)); }catch(e){} }
  };
  function cfg(){
    try{ const c = P && P.ROOM && P.ROOM.cfg; if(c && c.url && c.key) return { url:String(c.url).trim(), key:String(c.key).trim() }; }catch(e){}
    return DEF;
  }
  function lib(){
    if(window.supabase && window.supabase.createClient) return Promise.resolve(window.supabase);
    try{ if(P && P.supabase && P.supabase.createClient) return Promise.resolve(P.supabase); }catch(e){}
    return new Promise((ok, bad) => {
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js';
      s.onload = () => (window.supabase ? ok(window.supabase) : bad(new Error('offline')));
      s.onerror = () => { s.remove(); bad(new Error('offline')); };
      document.head.appendChild(s);
    });
  }
  let sbP = null;
  function sb(){
    if(!sbP){
      sbP = lib().then(L => { const c = cfg(); return L.createClient(c.url, c.key, { auth:{ persistSession:false, autoRefreshToken:false, detectSessionInUrl:false, storageKey:'mecca-auth' }, global:{ fetch:(u, o) => fetch(u, Object.assign({}, o, { cache:'no-store' })) } }); });
      sbP.catch(() => { sbP = null; });
    }
    return sbP;
  }

  /* ---- вход ---- */
  let creds = ls.get(AUTH_KEY);                      // {login, pass, role:'edit'|'view'}
  if(creds && !creds.role) creds.role = 'edit';      // вход из прошлой версии был только редакторским
  const canEdit = () => !!(creds && creds.role === 'edit');
  // 'rpc' — закрытая схема (mecca-access.sql), 'open' — старая схема с открытым чтением
  let mode = null;
  const noFn = e => { const m = (e && (e.message || '')) + ' ' + (e && e.code || ''); return /PGRST202|Could not find the function|function .* does not exist/i.test(m); };
  const isDenied = e => /access denied/i.test((e && (e.message || e.details)) || '');

  /* ---- локальная копия: коллекция → Map(id → данные) ---- */
  const store = {}; const loaded = {};
  if(creds){                                          // без входа сохранённую копию не показываем
    const cached = ls.get(CACHE_KEY);
    if(cached && cached.store) for(const c of WATCH){ if(cached.store[c]){ store[c] = new Map(Object.entries(cached.store[c])); loaded[c] = 'cache'; } }
  }
  let cacheT = null;
  function saveCache(){
    clearTimeout(cacheT);
    cacheT = setTimeout(() => { if(!creds) return; const o = {}; for(const c of WATCH) if(store[c]) o[c] = Object.fromEntries(store[c]); ls.set(CACHE_KEY, { t:Date.now(), store:o }); }, 400);
  }
  const collL = {}, docL = {};
  const snapDoc = (id, d) => ({ id, exists:d != null, data:() => d });
  function emit(coll){
    const m = store[coll] || new Map();
    const docs = [...m].map(([id, d]) => snapDoc(id, d));
    (collL[coll] || new Set()).forEach(l => { try{ l.next({ docs, size:docs.length, empty:!docs.length }); }catch(e){ console.error(e); } });
    for(const key of Object.keys(docL)){
      const [c, id] = key.split('/');
      if(c !== coll) continue;
      docL[key].forEach(l => { try{ l.next(snapDoc(id, m.has(id) ? m.get(id) : null)); }catch(e){ console.error(e); } });
    }
  }
  function emitError(coll, e){ (collL[coll] || new Set()).forEach(l => { if(l.error) try{ l.error(e); }catch(_){} }); }

  const sigOf = m => { try{ return JSON.stringify([...m].sort((a, b) => a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0)); }catch(e){ return String(Math.random()); } };
  const sig = {};
  for(const c of WATCH) if(store[c]) sig[c] = sigOf(store[c]);

  // чтение: сначала закрытая схема, при её отсутствии — старая открытая
  async function readList(coll, idsOnly){
    const c = await sb();
    if(mode !== 'open'){
      const r = idsOnly ? await c.rpc('mecca_ids', { p_login:creds.login, p_pass:creds.pass, p_coll:coll })
                        : await c.rpc('mecca_list', { p_login:creds.login, p_pass:creds.pass, p_coll:coll });
      if(!r.error){ mode = 'rpc'; return idsOnly ? (r.data || []).map(x => typeof x === 'string' ? { id:x } : x) : (r.data || []); }
      if(!noFn(r.error)) throw r.error;
      mode = 'open';
    }
    const q = await c.from('mecca_docs').select(idsOnly ? 'id' : 'id,data').eq('coll', coll).limit(5000);
    if(q.error) throw q.error;
    return q.data;
  }
  async function readOne(coll, id){
    const c = await sb();
    if(mode !== 'open'){
      const r = await c.rpc('mecca_get', { p_login:creds.login, p_pass:creds.pass, p_coll:coll, p_id:id });
      if(!r.error){ mode = 'rpc'; return r.data == null ? null : r.data; }
      if(!noFn(r.error)) throw r.error;
      mode = 'open';
    }
    const q = await c.from('mecca_docs').select('data').eq('coll', coll).eq('id', id).maybeSingle();
    if(q.error) throw q.error;
    return q.data ? q.data.data : null;
  }

  async function fetchColl(coll){
    const data = await readList(coll, false);
    const m = new Map(data.map(r => [r.id, r.data]));
    const ns = sigOf(m), first = loaded[coll] !== 'net' && loaded[coll] !== 'cache';
    store[coll] = m; loaded[coll] = 'net';
    if(ns === sig[coll] && !first) return;      // ничего не поменялось — окна не трогаем
    sig[coll] = ns;
    emit(coll); saveCache();
  }
  let netState = 'idle', started = false, chan = null;
  function setNet(s){ netState = s; try{ window.dispatchEvent(new CustomEvent('mecca-net', { detail:s })); }catch(e){} }
  async function refreshAll(){
    if(!creds){ setNet('locked'); return; }
    try{ await Promise.all(WATCH.map(fetchColl)); setNet('online'); setTimeout(prefetchImages, 1500); if(mode === 'open' && !chan) subscribe(); }
    catch(e){
      if(isDenied(e)){ setUser(null, true); return; }
      setNet('offline');
      for(const c of WATCH){ if(!loaded[c]){ store[c] = store[c] || new Map(); loaded[c] = 'empty'; emit(c); } }
      if(!WATCH.some(c => loaded[c] === 'cache' || loaded[c] === 'net')) WATCH.forEach(c => emitError(c, e));
    }
  }
  // мгновенные обновления есть только при открытой схеме; в закрытой — опрос
  async function subscribe(){
    if(mode !== 'open' || !creds) return;
    try{
      const c = await sb();
      if(chan) return;
      chan = c.channel('mecca-docs')
        .on('postgres_changes', { event:'*', schema:'public', table:'mecca_docs' }, p => {
          const row = (p.new && p.new.coll) ? p.new : p.old;
          if(!row || !row.coll || !WATCH.includes(row.coll)) return;
          const m = store[row.coll] || (store[row.coll] = new Map());
          if(p.eventType === 'DELETE') m.delete(row.id); else m.set(row.id, row.data);
          const ns = sigOf(m); if(ns === sig[row.coll]) return;
          sig[row.coll] = ns; emit(row.coll); saveCache();
        })
        .subscribe(st => { if(st === 'CHANNEL_ERROR' || st === 'TIMED_OUT'){ try{ c.removeChannel(chan); }catch(e){} chan = null; } });
    }catch(e){ chan = null; }
  }
  function start(){
    if(started) return; started = true;
    refreshAll();
    setInterval(() => { if(!document.hidden) refreshAll(); }, 15000);
    document.addEventListener('visibilitychange', () => { if(document.visibilityState === 'visible') refreshAll(); });
    window.addEventListener('online', () => refreshAll());
  }

  /* ---- запись ---- */
  function failure(e){
    const m = (e && (e.message || e.details)) || String(e || '');
    const err = new Error(m);
    if(/access denied/i.test(m)) err.code = 'invalid_argument', err.denied = true;
    else if(/too big/i.test(m)) err.code = 'invalid_argument';
    else err.code = 'unavailable';
    return err;
  }
  async function rpc(fn, args){
    if(!canEdit()) throw Object.assign(new Error('access denied'), { code:'invalid_argument', denied:true });
    let c; try{ c = await sb(); }catch(e){ throw failure(e); }
    const { data, error } = await c.rpc(fn, Object.assign({ p_login:creds.login, p_pass:creds.pass }, args));
    if(error){ const f = failure(error); if(f.denied) MECCA.recheck(); throw f; }
    return data;
  }
  const rid = () => { const a = 'abcdefghijklmnopqrstuvwxyz0123456789'; let s = ''; const r = crypto.getRandomValues(new Uint8Array(20)); for(const x of r) s += a[x % 36]; return s; };
  const clone = v => JSON.parse(JSON.stringify(v === undefined ? null : v));
  function stripDeletes(o){ if(o && typeof o === 'object' && !Array.isArray(o)) for(const k of Object.keys(o)){ if(o[k] && o[k].__delete__ === true) delete o[k]; else stripDeletes(o[k]); } return o; }
  async function put(coll, id, data){
    data = stripDeletes(clone(data));
    await rpc('mecca_put', { p_coll:coll, p_id:id, p_data:data });
    if(WATCH.includes(coll)){ const m = store[coll] || (store[coll] = new Map()); m.set(id, data); sig[coll] = sigOf(m); emit(coll); saveCache(); }
    else { imgLocal.set(coll + '/' + id, data); if(coll === 'images') idb.put(id, data); }
  }
  async function del(coll, id){
    await rpc('mecca_del', { p_coll:coll, p_id:id });
    if(store[coll]){ store[coll].delete(id); sig[coll] = sigOf(store[coll]); emit(coll); saveCache(); }
    imgLocal.delete(coll + '/' + id);
    if(coll === 'images') idb.del(id);
  }
  const imgLocal = new Map();

  /* картинки не меняются после загрузки (новая картинка = новый id), поэтому их можно хранить на устройстве */
  const idb = (() => {
    let dbP = null;
    function open(){
      if(!dbP) dbP = new Promise((ok, bad) => {
        try{
          const r = indexedDB.open('mecca-images', 1);
          r.onupgradeneeded = () => r.result.createObjectStore('img');
          r.onsuccess = () => ok(r.result); r.onerror = () => bad(r.error);
        }catch(e){ bad(e); }
      }).catch(e => { dbP = null; throw e; });
      return dbP;
    }
    const tx = (mode, fn) => open().then(db => new Promise((ok, bad) => {
      const t = db.transaction('img', mode); const st = t.objectStore('img'); const r = fn(st);
      t.oncomplete = () => ok(r && r.result); t.onerror = () => bad(t.error); t.onabort = () => bad(t.error);
    }));
    return {
      get: id => tx('readonly', st => st.get(id)).catch(() => undefined),
      put: (id, d) => tx('readwrite', st => st.put(d, id)).catch(() => {}),
      del: id => tx('readwrite', st => st.delete(id)).catch(() => {}),
      keys: () => tx('readonly', st => st.getAllKeys()).then(k => k || []).catch(() => null),
      clear: () => tx('readwrite', st => st.clear()).catch(() => {})
    };
  })();
  const wait = ms => new Promise(r => setTimeout(r, ms));
  async function fetchOne(coll, id){
    let last;
    for(const pause of [0, 1200, 3500]){          // три попытки: сразу, через 1,2 с и через 3,5 с
      if(pause) await wait(pause);
      try{ return await readOne(coll, id); }
      catch(e){ last = e; if(isDenied(e) || !navigator.onLine) break; }
    }
    throw last;
  }
  let prefetchAt = 0, prefetching = false;
  async function prefetchImages(){                 // докачать на устройство все картинки, которых ещё нет
    if(!creds || prefetching || Date.now() - prefetchAt < 10 * 60 * 1000) return;
    prefetching = true; prefetchAt = Date.now();
    try{
      const have = await idb.keys(); if(!have) return;
      const ids = new Set((await readList('images', true)).map(r => r.id));
      for(const k of have) if(!ids.has(k)) idb.del(k);               // удалённые на сервере
      for(const id of ids){ if(have.includes(id)) continue;
        try{ const d = await fetchOne('images', id); if(d) await idb.put(id, d); }catch(e){ prefetchAt = 0; break; } }
    }catch(e){ prefetchAt = 0; }
    finally{ prefetching = false; }
  }

  function docRef(path){
    const [coll, id] = String(path).split('/');
    return {
      id,
      async get(){
        if(WATCH.includes(coll) && loaded[coll] === 'net') return snapDoc(id, store[coll].has(id) ? store[coll].get(id) : null);
        if(imgLocal.has(coll + '/' + id)) return snapDoc(id, imgLocal.get(coll + '/' + id));
        if(!creds) return snapDoc(id, null);
        if(coll === 'images'){ const d = await idb.get(id); if(d) return snapDoc(id, d); }
        try{
          const d = await fetchOne(coll, id);
          if(d && coll === 'images') idb.put(id, d);
          return snapDoc(id, d);
        }catch(e){
          if(store[coll] && store[coll].has(id)) return snapDoc(id, store[coll].get(id));
          throw failure(e);
        }
      },
      set(d){ return put(coll, id, d); },
      async update(patch){
        const cur = (await this.get()); const base = cur.exists ? clone(cur.data()) : {};
        return put(coll, id, Object.assign(base, patch));
      },
      delete(){ return del(coll, id); },
      onSnapshot(next, error){
        const key = coll + '/' + id; const l = { next, error };
        (docL[key] || (docL[key] = new Set())).add(l);
        start();
        if(loaded[coll]){ const m = store[coll] || new Map(); setTimeout(() => next(snapDoc(id, m.has(id) ? m.get(id) : null)), 0); }
        return () => docL[key].delete(l);
      }
    };
  }
  const db = {
    collection(coll){
      return {
        doc(id){ return docRef(coll + '/' + id); },
        async add(d){ const id = rid(); await put(coll, id, d); return { id }; },
        onSnapshot(next, error){
          const l = { next, error };
          (collL[coll] || (collL[coll] = new Set())).add(l);
          start();
          if(loaded[coll]) setTimeout(() => emit(coll), 0);
          return () => collL[coll].delete(l);
        }
      };
    },
    doc: docRef
  };

  const hooks = new Set();
  function setUser(c, silent){
    const had = !!creds;
    creds = c; ls.set(AUTH_KEY, c);
    if(!c){                                           // выход: убрать данные с устройства и с экрана
      ls.set(CACHE_KEY, null); idb.clear(); imgLocal.clear();
      for(const k of WATCH){ store[k] = new Map(); sig[k] = sigOf(store[k]); loaded[k] = 'empty'; emit(k); }
      setNet('locked');
    }
    hooks.forEach(f => { try{ f(canEdit(), silent, had); }catch(e){} });
    if(c) refreshAll();
  }
  async function askRole(login, pass){
    const c = await sb();
    const r = await c.rpc('mecca_login2', { p_login:login, p_pass:pass });
    if(!r.error) return r.data || null;
    if(!noFn(r.error)) throw r.error;
    const o = await c.rpc('mecca_login', { p_login:login, p_pass:pass });   // старая схема: только редактор
    if(o.error) throw o.error;
    return o.data === true ? 'edit' : null;
  }
  window.MECCA = {
    get user(){ return creds ? creds.login : null; },
    get role(){ return creds ? creds.role : null; },
    get editor(){ return canEdit() ? creds.login : null; },
    get net(){ return netState; },
    onOwner(f){ hooks.add(f); },
    async login(login, pass){
      login = String(login || '').trim(); pass = String(pass || '');
      const role = await askRole(login, pass);
      if(!role) return false;
      setUser({ login, pass, role }); return true;
    },
    logout(){ setUser(null); },
    async recheck(){
      if(!creds) return;
      try{ const role = await askRole(creds.login, creds.pass);
        if(!role) setUser(null, true);
        else if(role !== creds.role){ creds.role = role; ls.set(AUTH_KEY, creds); hooks.forEach(f => { try{ f(canEdit(), true, true); }catch(e){} }); }
      }catch(e){}
    }
  };
  window.claude = {
    async use(what){
      if(what === 'db') return db;
      if(what === 'user') return { async isOwner(){ return canEdit(); }, async name(){ return creds ? creds.login : null; } };
      return null;
    }
  };
})();
