// Мок supabase-js: все запросы уходят в window.__db (expose_binding из Python, общая память для всех контекстов)
(function(){
  const UID = window.__UID || ("u-" + Math.random().toString(36).slice(2));
  function Q(table){this.t=table;this.op="select";this.f=[];this.payload=null;this.single=false;this.opts=null;}
  Q.prototype.select=function(){if(this.op==="select")this.op="select";return this;};
  Q.prototype.eq=function(k,v){this.f.push([k,v]);return this;};
  Q.prototype.order=function(){return this;};
  Q.prototype.limit=function(){return this;};
  Q.prototype.maybeSingle=function(){this.single=true;return this;};
  Q.prototype.single_=function(){this.single=true;return this;};
  Q.prototype.upsert=function(p,o){this.op="upsert";this.payload=p;this.opts=o||{};return this;};
  Q.prototype.insert=function(p){this.op="insert";this.payload=p;return this;};
  Q.prototype.update=function(p){this.op="update";this.payload=p;return this;};
  Q.prototype.delete=function(){this.op="delete";return this;};
  Q.prototype.then=function(ok,bad){
    return window.__db(JSON.stringify({uid:UID,t:this.t,op:this.op,f:this.f,p:this.payload,single:this.single,opts:this.opts}))
      .then(r=>JSON.parse(r)).then(ok,bad);};
  const ch={on(){return ch;},subscribe(cb){setTimeout(()=>cb&&cb("SUBSCRIBED"),10);return ch;}};
  window.supabase={createClient(){return {
    auth:{getSession:async()=>({data:{session:{user:{id:UID}}}}),signInAnonymously:async()=>({data:{user:{id:UID}}}),onAuthStateChange(){}},
    from:t=>new Q(t), channel:()=>ch, removeChannel(){}, rpc:async()=>({data:null,error:null})};}};
})();
