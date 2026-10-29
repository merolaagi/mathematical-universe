const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let nodes=new Map(),edges=[],edgeKeys=new Set(),catalogue,selected,rootId,visible=new Set(),loaded=new Set(),detailCache={},history=[],database=false,scale=1,pan={x:0,y:0},requestSeq=0;
const colors={Family:'#274e48',Manuscript:'#b0794f',Proof:'#729386',Step:'#729386',Formalization:'#516b8b',Concept:'#9268a6',Argument:'#367c92',Claim:'#367c92',Candidate:'#bb7c36'};
const names={USES_RESULT:'Requires result · curated',SOURCE_SUPPORT:'Source support · unverified',HAS_ARGUMENT:'Proof contract',ALTERNATIVE_PROOF:'Alternative complete route',PROPOSES_CHANGE:'Proposed change · not a proof',MISSING_PREMISE:'Missing required premise',LEARNING_PREREQUISITE:'Simpler foundation · curated',SUGGESTED_BACKGROUND:'Suggested background · subject-based',HAS_MANUSCRIPT:'Manuscript',HAS_FORMALIZATION:'Formalization scope',CONTAINS:'Contains',FOLLOWED_BY_PROOF:'Adjacent proof · unreviewed',HAS_PASSAGE:'Proof passage',REFERENCES:'Source reference',CITES:'Citation',CATALOGUE_REFERENCE:'Catalog reference'};
function merge(data){for(const n of data.nodes)nodes.set(n.id,n);for(const e of data.edges){const k=e.source+'|'+e.target+'|'+e.type;if(!edgeKeys.has(k)){edgeKeys.add(k);edges.push(e)}}}
function toast(s){$('#toast').textContent=s;$('#toast').style.display='block';clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('#toast').style.display='none',4500)}
async function read(url){const compressed=url.startsWith('graphs/')||url.startsWith('details/');const r=await fetch(url+(compressed?'.gz':''));if(!r.ok)throw new Error('Unable to load '+url);if(!compressed)return r.json();const bytes=await r.arrayBuffer();const magic=new Uint8Array(bytes);if(magic[0]!==31||magic[1]!==139)return JSON.parse(new TextDecoder().decode(bytes));return new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).json()}
async function loadFamily(id){if(!id||loaded.has(id))return;merge(await read('graphs/'+id+'.json'));loaded.add(id)}
function neighborhood(id){return edges.filter(e=>e.source===id||e.target===id).sort((a,b)=>a.type==='HAS_PASSAGE'&&b.type==='HAS_PASSAGE'?Number(a.evidence)-Number(b.evidence):0)}
async function select(id,record=true){
 if(selected===id){await details();return}
 const sequence=++requestSeq;
 try{
  const n=nodes.get(id);if(!n)return;
  await loadFamily(n.kind==='Family'?id:n.family);
  if(sequence!==requestSeq)return;
  if(database){try{merge(await read('/api/neighbors?id='+encodeURIComponent(id)))}catch{toast('Database unavailable; showing pinned source snapshot.')}}
  if(sequence!==requestSeq)return;
  if(record&&selected)history.push(selected);selected=id;visible.add(id);
  $('#graphTitle').textContent=nodes.get(rootId)?.title||n.title;
  location.hash=id;inspect();draw();renderList();
 }catch(e){toast(e.message)}
}
async function openFamily(id){rootId=id;visible=new Set([id]);selected=null;scale=1;pan={x:0,y:0};await select(id);if(nodes.get(id)?.kind==='Concept')showFoundations();else expand()}
function renderList(){
 const q=$('#search').value.toLowerCase(),subject=$('#subject').value;
 const lab=$('#reasoningMode')?.checked;
 const families=(lab?[...nodes.values()].filter(n=>n.id.startsWith('reason:')):$('#learningMode')?.checked?[...nodes.values()].filter(n=>n.kind==='Concept').sort((a,b)=>b.uses-a.uses):catalogue.nodes).filter(n=>(n.kind==='Family'||n.kind==='Concept'||lab)&&(!subject||lab||n.kind==='Concept'||n.subject===subject)&&(!q||n.title.toLowerCase().includes(q)||n.summary.toLowerCase().includes(q)||catalogue.nodes.some(m=>m.kind==='Manuscript'&&m.family===n.id&&m.title.toLowerCase().includes(q))));
 $('#resultCount').textContent=families.length+(lab?' PROOF CONTRACTS':$('#learningMode')?.checked?' FOUNDATIONS · MOST SHARED FIRST':' FAMILIES');$('#results').innerHTML='';
 for(const n of families){const b=document.createElement('button');b.className='family-row'+(rootId===n.id?' active':'');b.innerHTML=esc(n.title)+'<small>'+esc(n.kind==='Concept'?n.uses+' incoming learning links':n.status||n.subject)+'</small>';b.onclick=()=>openFamily(n.id);$('#results').append(b)}
 if(!families.length)$('#results').textContent='No matches. Try another term.';
}
function showFoundations(){
 const n=nodes.get(selected);let from=selected;
 let prerequisites=edges.filter(e=>e.source===from&&['LEARNING_PREREQUISITE','SUGGESTED_BACKGROUND'].includes(e.type));
 if(!prerequisites.length&&n.family){from=n.family;prerequisites=edges.filter(e=>e.source===from&&e.type==='SUGGESTED_BACKGROUND');visible.add(from)}
 for(const e of prerequisites)visible.add(e.target);
 draw();inspect();
 toast(prerequisites.length?'Select a purple foundation, then follow its Simpler foundations or read its example.':n.kind==='Concept'?'This is a starting concept in the current learning map.':'No curated learning path is available for this node yet.');
}
function expand(){
 const adjacent=neighborhood(selected);let count=0;
 for(const e of adjacent){const id=e.source===selected?e.target:e.source;if(!visible.has(id)&&nodes.has(id)){visible.add(id);count++;if(count===18)break}}
 draw();inspect();toast(count?`Expanded ${count} nodes. Use Expand again for more.`:'All connected nodes are visible.');
}
function dependencyReport(id,omitted=''){
 const found=new Set(),missing=[],cycles=[];
 function walk(current,path){if(path.includes(current)){cycles.push([...path,current]);return}if(found.has(current))return;found.add(current);
 for(const e of edges.filter(e=>e.source===current&&e.type==='USES_RESULT')){if(e.target===omitted){missing.push({from:current,to:e.target});continue}walk(e.target,[...path,current])}}
 walk(id,[]);return {found:[...found],missing,cycles};
}
function renderContract(n){
 const box=$('#contract');if(!n.id.startsWith('reason:')){
 const links=edges.filter(e=>e.source===(n.kind==='Family'?n.id:n.family||n.id)&&e.type==='HAS_ARGUMENT');
 if(links.length){const b=document.createElement('button');b.className='primary';b.textContent='Open proof workshop';b.onclick=()=>openFamily(links[0].target);box.append(b)}return}
 box.innerHTML='<div class="section-title">ASSUMPTIONS · ALL REQUIRED</div><ul>'+n.assumptions.map(a=>'<li>'+esc(a)+'</li>').join('')+'</ul><div class="section-title">CONCLUSION</div><p>'+esc(n.conclusion)+'</p>';
 const alternatives=edges.filter(e=>e.source===n.id&&e.type==='ALTERNATIVE_PROOF');
 for(const e of alternatives){const b=document.createElement('button');b.className='neighbor';b.textContent='Compare route: '+nodes.get(e.target).title;b.onclick=()=>openFamily(e.target);box.append(b)}
 const report=dependencyReport(n.id),dependencies=report.found.filter(id=>id!==n.id);
 if(!dependencies.length)return;
 const section=document.createElement('section');section.className='contract-check';section.innerHTML='<div class="section-title">TRY REMOVING A PREMISE</div><p>Checks only the declared dependency graph. It cannot establish mathematical truth or discover replacements.</p><label for="omitPremise">Omit a result</label><select id="omitPremise"><option value="">Keep all declared results</option>'+dependencies.map(id=>'<option value="'+esc(id)+'">'+esc(nodes.get(id)?.title||id)+'</option>').join('')+'</select><div id="contractReport" role="status"></div>';box.append(section);
 function check(){const result=dependencyReport(n.id,$('#omitPremise').value);$('#contractReport').innerHTML=result.cycles.length?'<p>Circular dependency detected. This route needs review.</p>':result.missing.length?'<p class="blocked">Blocked: a required result was removed.</p>'+result.missing.map(m=>'<p>'+esc(nodes.get(m.from).title)+' still requires '+esc(nodes.get(m.to).title)+'.</p>').join(''):'<p>Declared dependencies present. The source premises and mathematical validity still require verification.</p>';}
 $('#omitPremise').onchange=check;check();
}
function inspect(){
 const n=nodes.get(selected);if(!n)return;
 const connections=neighborhood(selected),outgoing=connections.filter(e=>e.source===selected),incoming=connections.filter(e=>e.target===selected);
 $('#inspector').innerHTML=`<span class="kind">${esc(n.kind==='Step'?'Proof passage':n.kind)}</span><h2>${esc(n.title)}</h2><p class="summary">${esc(n.summary||'No summary in source.')}</p><p class="extraction">${esc(n.extraction||'Source-reported research claim; not independently verified here.')}</p>${n.status?`<p class="contract-status">${esc(n.status)}</p>`:''}${n.url?`<a class="source" href="${esc(n.url)}" target="_blank" rel="noopener">Open exact source ↗</a>`:""}${n.kind==='Concept'?`<p class="hub">${n.uses} incoming learning links · shared foundation</p>`:""}<div class="actions"><button class="primary" id="expand">Expand connections</button><button id="details">${n.kind==='Concept'?'Explanation & simple proof':'Read details'}</button><button id="foundations">Simpler foundations</button><button id="collapse">Focus here</button></div><div id="contract"></div><div id="detail"></div><div class="section-title">CONNECTIONS · ${connections.length}</div><p class="extraction">Arrows point from an idea toward its background or contained material. Learning links are guidance, not verified proof dependencies. Incoming learning links show reuse, not mathematical importance.</p><div id="connections"></div>`;
 $('#foundations').onclick=showFoundations;$('#expand').onclick=expand;$('#details').onclick=details;$('#collapse').onclick=()=>{rootId=selected;visible=new Set([selected]);expand()};
 renderContract(n);
 let limit=0;function more(){const all=[...outgoing,...incoming],stop=Math.min(limit+40,all.length);for(;limit<stop;limit++){const e=all[limit],isOut=e.source===selected,id=isOut?e.target:e.source,other=nodes.get(id);if(!other)continue;const b=document.createElement('button');b.className='neighbor';b.innerHTML='<small>'+esc((isOut?'→ ':'← ')+(names[e.type]||e.type))+'</small>'+esc(other.title);b.onclick=()=>{visible.add(id);select(id)};$('#connections').append(b)}if(limit<all.length){const b=document.createElement('button');b.textContent=`Show more (${all.length-limit} remaining)`;b.onclick=()=>{b.remove();more()};$('#connections').append(b)}}more();
}
async function details(){
 const id=selected,n=nodes.get(id),container=$('#detail');if(!container)return;
 if(container.textContent){container.innerHTML='';return}
 if(n.id.startsWith('reason:')){container.innerHTML='<div class="section-title">JUSTIFICATION / PROOF SKETCH</div><p class="learning-proof">'+esc(n.justification)+'</p>';return}
 if(n.kind==='Concept'){container.innerHTML='<div class="section-title">EXPLANATION</div><p>'+esc(n.detail)+'</p><div class="section-title">SIMPLE PROOF / WORKED EXAMPLE</div><p class="learning-proof">'+esc(n.proof)+'</p><p class="extraction">An elementary teaching example. This does not prove the connected research results.</p>';return}
 container.textContent='Loading source text…';
 try{const family=n.kind==='Family'?id:n.family;if(!detailCache[family])detailCache[family]=await read('details/'+family+'.json');if(selected!==id)return;
 let text=detailCache[family][id]||n.summary;
 if(n.kind==='Manuscript'){
  const blocks=[...nodes.values()].filter(x=>x.manuscript===id&&['Statement','Definition','Assumption','Proof'].includes(x.kind));
  text+='\n\nEXTRACTED STATEMENTS AND PROOFS\nSource-file order; see the original PDF for the complete manuscript and its reading order.\n\n'+blocks.map(x=>x.title+'\n'+(detailCache[family][x.id]||x.summary)).join('\n\n────────────────────\n\n');
 }
 container.innerHTML='<div class="section-title">SOURCE DETAIL · ORIGINAL TEXT / LATEX</div><pre class="detail">'+esc(text)+'</pre>';
 }catch(e){container.textContent=e.message}
}
function draw(){
 const all=[...visible].filter(id=>nodes.has(id)),positions=new Map(),links=edges.filter(e=>visible.has(e.source)&&visible.has(e.target));
 // Stable concentric layout. Related nodes remain individually selectable.
 positions.set(rootId,{x:500,y:330});const others=all.filter(id=>id!==rootId);
 const rings=Math.max(1,Math.ceil(others.length/18));others.forEach((id,i)=>{const ring=Math.floor(i/18),start=ring*18,count=Math.min(18,others.length-start),a=(i-start)/count*Math.PI*2-Math.PI/2,r=190+ring*140;positions.set(id,{x:500+Math.cos(a)*r*1.35,y:330+Math.sin(a)*r})});
 const scene=$('#scene');scene.innerHTML='';const ns='http://www.w3.org/2000/svg';
 for(const e of links){const a=positions.get(e.source),b=positions.get(e.target);if(!a||!b)continue;const line=document.createElementNS(ns,'line');for(const [k,v] of Object.entries({x1:a.x,y1:a.y,x2:b.x,y2:b.y,class:'edge'+(['REFERENCES','CITES','CATALOGUE_REFERENCE','LEARNING_PREREQUISITE','SUGGESTED_BACKGROUND','PROPOSES_CHANGE','MISSING_PREMISE'].includes(e.type)?' reference-edge':''),'marker-end':'url(#arrow)'}))line.setAttribute(k,v);const title=document.createElementNS(ns,'title');title.textContent=(names[e.type]||e.type)+' '+e.evidence;line.append(title);scene.append(line)}
 for(const id of all){const n=nodes.get(id),p=positions.get(id);if(!p)continue;const g=document.createElementNS(ns,'g');g.setAttribute('class','node'+(selected===id?' selected':''));g.setAttribute('transform',`translate(${p.x},${p.y})`);g.setAttribute('tabindex','0');g.setAttribute('role','button');g.setAttribute('aria-label',n.kind+': '+n.title);const c=document.createElementNS(ns,'circle');c.setAttribute('r',id===rootId?22:n.kind==='Concept'?Math.min(21,12+Math.log2(1+n.uses)):12);c.setAttribute('fill',colors[n.kind]||'#a7afa1');g.append(c);const text=document.createElementNS(ns,'text');text.setAttribute('text-anchor','middle');text.setAttribute('y',id===rootId?42:30);text.textContent=n.title.length>39?n.title.slice(0,36)+'…':n.title;g.append(text);const title=document.createElementNS(ns,'title');title.textContent=n.title;g.append(title);g.onclick=()=>select(id);g.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select(id)}};scene.append(g)}
 transform();
}
function transform(){$('#scene').setAttribute('transform',`translate(${500+pan.x},${330+pan.y}) scale(${scale}) translate(-500,-330)`)}
$('#zoomIn').onclick=()=>{scale=Math.min(3,scale*1.2);transform()};$('#zoomOut').onclick=()=>{scale=Math.max(.12,scale/1.2);transform()};$('#fit').onclick=()=>{scale=Math.min(1,1/(1+Math.floor(Math.max(0,visible.size-2)/18)*.6));pan={x:0,y:0};transform()};
$('#graph').addEventListener('wheel',e=>{e.preventDefault();scale=Math.max(.12,Math.min(3,scale*(e.deltaY>0?.9:1.1)));transform()},{passive:false});let drag=null;
$('#graph').addEventListener('pointerdown',e=>{if(e.target.closest('.node'))return;drag={x:e.clientX,y:e.clientY,px:pan.x,py:pan.y};$('#graph').setPointerCapture(e.pointerId)});
$('#graph').addEventListener('pointermove',e=>{if(!drag)return;const ratio=1000/$('#graph').clientWidth;pan={x:drag.px+(e.clientX-drag.x)*ratio,y:drag.py+(e.clientY-drag.y)*ratio};transform()});$('#graph').addEventListener('pointerup',()=>drag=null);
$('#back').onclick=()=>{const id=history.pop();if(id)select(id,false)};$('#reset').onclick=()=>openFamily(rootId?.startsWith('f')?rootId:'f005');$('#search').oninput=renderList;$('#subject').onchange=renderList;
(async()=>{try{catalogue=await read('catalogue.json');merge(catalogue);merge(await read('foundations.json?v='+document.querySelector('meta[name=mathuni-build]').content));merge(await read('reasoning.json?v='+document.querySelector('meta[name=mathuni-build]').content));const toggle=document.createElement('label');toggle.className='learning-switch';toggle.innerHTML='<input type="checkbox" id="learningMode"> Browse shared foundations';$('#search').before(toggle);const labToggle=document.createElement('label');labToggle.className='learning-switch';labToggle.innerHTML='<input type="checkbox" id="reasoningMode"> Proof workshop · assumptions & routes';$('#search').before(labToggle);$('#reasoningMode').onchange=()=>{if($('#reasoningMode').checked)$('#learningMode').checked=false;renderList()};$('#learningMode').onchange=()=>{if($('#learningMode').checked)$('#reasoningMode').checked=false;renderList()};$('#stats').innerHTML=`<div><strong>${catalogue.meta.counts.Family}</strong><small>RESULT FAMILIES</small></div><div><strong>${catalogue.meta.counts.Manuscript}</strong><small>MANUSCRIPTS</small></div>`;$('#revision').textContent='Pinned revision '+catalogue.meta.commit.slice(0,10);for(const subject of [...new Set(catalogue.nodes.filter(n=>n.kind==='Family').map(n=>n.subject))].sort()){const o=document.createElement('option');o.value=subject;o.textContent=subject;$('#subject').append(o)}
 try{await read('/api/health');database=true}catch{}
 $('#mode').textContent=database?'● Neo4j connected':'● Pinned source snapshot';renderList();const id=location.hash.slice(1);await openFamily(nodes.has(id)?(id.startsWith('reason:')?id:nodes.get(id).family||id):'f005');if(nodes.has(id)&&id!==rootId)await select(id);
 }catch(e){$('#mode').textContent='Load failed';toast(e.message)}})();
