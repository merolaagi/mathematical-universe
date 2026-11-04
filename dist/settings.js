(()=>{
 // Local-only settings panel. The server answers /api/settings only for http://127.0.0.1:18765 on this Mac,
 // so on the public site the request 404s and no button is shown.
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const GROUPS=[['Who writes the explainers',['SWARM_BACKEND','SWARM_ESCALATE','SWARM_MIN_SCORE']],
  ['Local model (Ollama)',['OLLAMA_MODEL','OLLAMA_HOST','OLLAMA_THINK','OLLAMA_JSON']],
  ['Claude API',['ANTHROPIC_API_KEY','CLAUDE_MODEL']],
  ['Videos and speed',['SWARM_VIDEOS','MANIM_BIN','SWARM_WORKERS']]];
 const CLAUDE_MODELS=['claude-sonnet-5-5','claude-opus-5-5','claude-haiku-5-5','claude-fable-5-1'];
 let view=null,dlg=null;
 async function api(path,body){const r=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{cache:'no-store'});const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||('HTTP '+r.status));return d}
 function pill(s){return `<span class="st-pill ${s.ok?'ok':'no'}">${s.ok?'●':'○'} ${esc(s.message)}</span>`}
 function field(r){
  const id='st_'+r.key,help=`<small>${esc(r.help)}${r.from_env?' <b>Overridden by an environment variable.</b>':''}</small>`;
  let input;
  if(r.kind==='choice')input=`<select id="${id}" data-key="${r.key}">${r.choices.map(c=>`<option ${c===r.value?'selected':''}>${esc(c)}</option>`).join('')}</select>`;
  else if(r.kind==='secret')input=`<div class="st-secret"><input id="${id}" data-key="${r.key}" type="password" autocomplete="off" spellcheck="false" placeholder="${r.is_set?esc(r.value)+' · type to replace':'paste key (sk-ant-…)'}">${r.is_set?'<button type="button" data-clear="'+r.key+'">Remove</button>':''}<button type="button" data-test="claude">Test</button></div>`;
  else if(r.key==='OLLAMA_MODEL'){const opts=[...new Set([...(view.ollama_models||[]),r.value].filter(Boolean))];input=`<div class="st-secret"><select id="${id}" data-key="${r.key}">${opts.map(m=>`<option ${m===r.value?'selected':''}>${esc(m)}</option>`).join('')}</select><button type="button" data-test="ollama">Test</button></div>`}
  else if(r.key==='CLAUDE_MODEL')input=`<input id="${id}" data-key="${r.key}" list="st_claude_models" value="${esc(r.value)}" spellcheck="false"><datalist id="st_claude_models">${CLAUDE_MODELS.map(m=>`<option value="${m}">`).join('')}</datalist>`;
  else if(r.kind==='number')input=`<input id="${id}" data-key="${r.key}" type="number" min="${r.range[0]}" max="${r.range[1]}" step="${r.key==='SWARM_MIN_SCORE'?'0.5':'1'}" value="${esc(r.value)}">`;
  else input=`<input id="${id}" data-key="${r.key}" value="${esc(r.value)}" spellcheck="false" placeholder="${esc(r.default)}">`;
  return `<div class="st-field"><label for="${id}">${esc(r.label)}</label>${input}${help}</div>`}
 function render(){
  const by=Object.fromEntries(view.settings.map(r=>[r.key,r]));
  dlg.querySelector('.st-body').innerHTML=`<div class="st-status">${pill(view.status.ollama)}${pill(view.status.claude)}${pill(view.status.manim)}</div>`+
   GROUPS.map(([t,keys])=>`<fieldset><legend>${esc(t)}</legend>${keys.map(k=>by[k]?field(by[k]):'').join('')}</fieldset>`).join('')+
   `<p class="extraction">Saved only on this Mac in <code>${esc(view.file)}</code> (readable only by you). The key is never sent back to the browser. The next swarm run uses these values; command-line flags still override them for one run.</p>`;
  dlg.querySelectorAll('[data-test]').forEach(b=>b.onclick=()=>test(b.dataset.test,b));
  dlg.querySelectorAll('[data-clear]').forEach(b=>b.onclick=()=>save({[b.dataset.clear]:''},'Key removed.'));
 }
 function changes(){const out={},by=Object.fromEntries(view.settings.map(r=>[r.key,r]));
  dlg.querySelectorAll('[data-key]').forEach(e=>{const r=by[e.dataset.key];const v=e.value.trim();if(r.kind==='secret'){if(v)out[r.key]=v}else if(v!==String(r.value))out[r.key]=v});return out}
 function note(msg,bad){const n=dlg.querySelector('.st-note');n.textContent=msg;n.className='st-note'+(bad?' bad':'')}
 async function save(c,msg){c=c||changes();if(!Object.keys(c).length){note('Nothing changed.');return}
  try{view=await api('/api/settings',{changes:c});render();note(msg||'Saved. The next run uses these settings.')}catch(e){note(e.message,true)}}
 async function test(target,btn){
  const c=changes();if(Object.keys(c).length){try{view=await api('/api/settings',{changes:c});render()}catch(e){note(e.message,true);return}}
  note(target==='claude'?'Asking Claude for a one-word reply…':'Checking Ollama…');
  try{const r=await api('/api/settings/test',{target});note(r.message,!r.ok)}catch(e){note(e.message,true)}}
 async function openPanel(){
  try{view=await api('/api/settings')}catch(e){alertless(e.message);return}
  if(!dlg){dlg=document.createElement('dialog');dlg.id='settingsDialog';dlg.setAttribute('aria-labelledby','stTitle');
   dlg.innerHTML=`<form method="dialog" class="st-form"><div class="st-head"><div><h2 id="stTitle">Settings</h2><p>Explainer swarm · this Mac only</p></div><button value="cancel" aria-label="Close settings">Close</button></div><div class="st-body"></div><div class="st-foot"><span class="st-note" role="status"></span><button type="button" class="primary" id="stSave">Save</button></div></form>`;
   document.body.append(dlg);dlg.querySelector('#stSave').onclick=()=>save()}
  render();note('');dlg.showModal()}
 function alertless(msg){const t=document.getElementById('toast');if(t){t.textContent=msg;t.style.display='block';setTimeout(()=>t.style.display='none',3500)}}
 fetch('/api/settings',{cache:'no-store'}).then(r=>{if(!r.ok)return;const h=document.querySelector('header');if(!h||document.getElementById('settingsOpen'))return;
  const b=document.createElement('button');b.id='settingsOpen';b.className='st-open';b.type='button';b.innerHTML='<span aria-hidden="true">⚙</span><span class="st-label"> Settings</span>';b.setAttribute('aria-label','Settings');b.title='Explainer swarm settings (this Mac only)';b.onclick=openPanel;h.append(b)}).catch(()=>{});
})();
