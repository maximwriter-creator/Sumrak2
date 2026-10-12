/* ===== Мекка: общая база Supabase вместо базы артефакта =====
   Тот же интерфейс, что ждёт карта (window.claude.use('db' | 'user')),
   но данные лежат в таблице public.mecca_docs (см. mecca.sql).
   Читать может любой; писать — только после входа редактора (логин/пароль проверяет сервер). */
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

  /* ---- локальная копия: коллекция → Map(id → данные) ---- */
  const store = {}; const loaded = {};
  const cached = ls.get(CACHE_KEY);
  if(cached && cached.store) for(const c of WATCH){ if(cached.store[c]){ store[c] = new Map(Object.entries(cached.store[c])); loaded[c] = 'cache'; } }
  let cacheT = null;
  function saveCache(){
    clearTimeout(cacheT);
    cacheT = setTimeout(() => { const o = {}; for(const c of WATCH) if(store[c]) o[c] = Object.fromEntries(store[c]); ls.set(CACHE_KEY, { t:Date.now(), store:o }); }, 400);
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

  async function fetchColl(coll){
    const c = await sb();
    const { data, error } = await c.from('mecca_docs').select('id,data').eq('coll', coll).limit(5000);
    if(error) throw error;
    store[coll] = new Map(data.map(r => [r.id, r.data]));
    loaded[coll] = 'net';
    emit(coll); saveCache();
  }
  let netState = 'idle', started = false, chan = null;
  function setNet(s){ netState = s; try{ window.dispatchEvent(new CustomEvent('mecca-net', { detail:s })); }catch(e){} }
  async function refreshAll(){
    try{ await Promise.all(WATCH.map(fetchColl)); setNet('online'); }
    catch(e){
      setNet('offline');
      for(const c of WATCH){ if(!loaded[c]){ store[c] = store[c] || new Map(); loaded[c] = 'empty'; emit(c); } }
      if(!WATCH.some(c => loaded[c] === 'cache' || loaded[c] === 'net')) WATCH.forEach(c => emitError(c, e));
    }
  }
  async function subscribe(){
    try{
      const c = await sb();
      if(chan) return;
      chan = c.channel('mecca-docs')
        .on('postgres_changes', { event:'*', schema:'public', table:'mecca_docs' }, p => {
          const row = (p.new && p.new.coll) ? p.new : p.old;
          if(!row || !row.coll || !WATCH.includes(row.coll)) return;
          const m = store[row.coll] || (store[row.coll] = new Map());
          if(p.eventType === 'DELETE') m.delete(row.id); else m.set(row.id, row.data);
          emit(row.coll); saveCache();
        })
        .subscribe(st => { if(st === 'SUBSCRIBED') setNet('online'); if(st === 'CHANNEL_ERROR' || st === 'TIMED_OUT'){ try{ c.removeChannel(chan); }catch(e){} chan = null; } });
    }catch(e){ chan = null; }
  }
  function start(){
    if(started) return; started = true;
    refreshAll().then(subscribe);
    setInterval(() => { refreshAll(); if(!chan) subscribe(); }, 30000);
    document.addEventListener('visibilitychange', () => { if(document.visibilityState === 'visible'){ refreshAll(); if(!chan) subscribe(); } });
    window.addEventListener('online', () => { refreshAll(); if(!chan) subscribe(); });
  }

  /* ---- редактор ---- */
  let creds = ls.get(AUTH_KEY);
  function failure(e){
    const m = (e && (e.message || e.details)) || String(e || '');
    const err = new Error(m);
    if(/access denied/i.test(m)) err.code = 'invalid_argument', err.denied = true;
    else if(/too big/i.test(m)) err.code = 'invalid_argument';
    else err.code = 'unavailable';
    return err;
  }
  async function rpc(fn, args){
    if(!creds) throw Object.assign(new Error('access denied'), { code:'invalid_argument', denied:true });
    let c; try{ c = await sb(); }catch(e){ throw failure(e); }
    const { data, error } = await c.rpc(fn, Object.assign({ p_login:creds.login, p_pass:creds.pass }, args));
    if(error){ const f = failure(error); if(f.denied) setEditor(null, true); throw f; }
    return data;
  }
  const rid = () => { const a = 'abcdefghijklmnopqrstuvwxyz0123456789'; let s = ''; const r = crypto.getRandomValues(new Uint8Array(20)); for(const x of r) s += a[x % 36]; return s; };
  const clone = v => JSON.parse(JSON.stringify(v === undefined ? null : v));
  function stripDeletes(o){ if(o && typeof o === 'object' && !Array.isArray(o)) for(const k of Object.keys(o)){ if(o[k] && o[k].__delete__ === true) delete o[k]; else stripDeletes(o[k]); } return o; }
  async function put(coll, id, data){
    data = stripDeletes(clone(data));
    await rpc('mecca_put', { p_coll:coll, p_id:id, p_data:data });
    if(WATCH.includes(coll)){ (store[coll] || (store[coll] = new Map())).set(id, data); emit(coll); saveCache(); }
    else imgLocal.set(coll + '/' + id, data);
  }
  async function del(coll, id){
    await rpc('mecca_del', { p_coll:coll, p_id:id });
    if(store[coll]){ store[coll].delete(id); emit(coll); saveCache(); }
    imgLocal.delete(coll + '/' + id);
  }
  const imgLocal = new Map();

  function docRef(path){
    const [coll, id] = String(path).split('/');
    return {
      id,
      async get(){
        if(WATCH.includes(coll) && loaded[coll] === 'net') return snapDoc(id, store[coll].has(id) ? store[coll].get(id) : null);
        if(imgLocal.has(coll + '/' + id)) return snapDoc(id, imgLocal.get(coll + '/' + id));
        try{
          const c = await sb();
          const { data, error } = await c.from('mecca_docs').select('data').eq('coll', coll).eq('id', id).maybeSingle();
          if(error) throw error;
          return snapDoc(id, data ? data.data : null);
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

  const ownerHooks = new Set();
  function setEditor(c, silent){
    creds = c; ls.set(AUTH_KEY, c);
    ownerHooks.forEach(f => { try{ f(!!c, silent); }catch(e){} });
  }
  window.MECCA = {
    get editor(){ return creds ? creds.login : null; },
    get net(){ return netState; },
    onOwner(f){ ownerHooks.add(f); },
    async login(login, pass){
      login = String(login || '').trim(); pass = String(pass || '');
      const c = await sb();
      const { data, error } = await c.rpc('mecca_login', { p_login:login, p_pass:pass });
      if(error) throw error;
      if(data !== true) return false;
      setEditor({ login, pass }); return true;
    },
    logout(){ setEditor(null); },
    async recheck(){
      if(!creds) return;
      try{ const c = await sb(); const { data, error } = await c.rpc('mecca_login', { p_login:creds.login, p_pass:creds.pass }); if(!error && data === false) setEditor(null, true); }catch(e){}
    }
  };
  window.claude = {
    async use(what){
      if(what === 'db') return db;
      if(what === 'user') return { async isOwner(){ return !!creds; }, async name(){ return creds ? creds.login : null; } };
      return null;
    }
  };
})();
