(()=>{
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const SVG='http://www.w3.org/2000/svg';
 let index=null,indexLoad=null,katexLoad=null;const cache=new Map();
 function loadIndex(){return indexLoad||(indexLoad=fetch('explainers/index.json',{cache:'no-cache'}).then(r=>r.ok?r.json():{families:{}}).then(d=>index=d.families||{}).catch(()=>index={}))}
 function loadKatex(){
  if(katexLoad)return katexLoad;
  const base='vendor/katex/';
  const add=(tag,attrs)=>new Promise((ok,fail)=>{const e=document.createElement(tag);Object.assign(e,attrs);e.onload=ok;e.onerror=fail;document.head.append(e)});
  return katexLoad=add('link',{rel:'stylesheet',href:base+'katex.min.css'}).then(()=>add('script',{src:base+'katex.min.js'})).then(()=>add('script',{src:base+'contrib/auto-render.min.js'})).catch(()=>null);
 }
 function typeset(el){loadKatex().then(()=>{if(window.renderMathInElement)try{renderMathInElement(el,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],throwOnError:false,trust:false})}catch{}})}
 function tex(latex,display){const s=document.createElement(display?'div':'span');s.textContent=display?'$$'+latex+'$$':'$'+latex+'$';return s}

 // Expression grammar shared with swarm/safety.py: numbers, variables, + - * / ^ %, parentheses, whitelisted functions.
 const FN={sin:Math.sin,cos:Math.cos,tan:Math.tan,asin:Math.asin,acos:Math.acos,atan:Math.atan,sinh:Math.sinh,cosh:Math.cosh,tanh:Math.tanh,exp:Math.exp,log:Math.log,ln:Math.log,log10:Math.log10,log2:Math.log2,sqrt:Math.sqrt,abs:Math.abs,floor:Math.floor,ceil:Math.ceil,min:Math.min,max:Math.max,pow:Math.pow,gamma:gamma,factorial:v=>gamma(v+1)};
 function gamma(z){if(z<0.5)return Math.PI/(Math.sin(Math.PI*z)*gamma(1-z));z-=1;const g=7,c=[0.99999999999980993,676.5203681218851,-1259.1392167224028,771.32342877765313,-176.61502916214059,12.507343278686905,-0.13857109526572012,9.9843695780195716e-6,1.5056327351493116e-7];let x=c[0];for(let i=1;i<g+2;i++)x+=c[i]/(z+i);const t=z+g+0.5;return Math.sqrt(2*Math.PI)*Math.pow(t,z+0.5)*Math.exp(-t)*x}
 const CONST={pi:Math.PI,e:Math.E};
 function compile(src,vars){
  const toks=String(src).match(/\d+\.?\d*(?:e[+-]?\d+)?|\.\d+|[a-zA-Z][a-zA-Z0-9]*|[-+*/^%(),]|\S/g)||[];let i=0;
  const peek=()=>toks[i],take=t=>{if(t&&toks[i]!==t)throw Error('expected '+t);return toks[i++]};
  function expr(){let a=term();while(peek()==='+'||peek()==='-'){const op=take(),b=term(),l=a;a=op==='+'?s=>l(s)+b(s):s=>l(s)-b(s)}return a}
  function term(){let a=unary();while(['*','/','%'].includes(peek())){const op=take(),b=unary(),l=a;a=op==='*'?s=>l(s)*b(s):op==='/'?s=>l(s)/b(s):s=>l(s)%b(s)}return a}
  function unary(){if(peek()==='-'){take();const a=unary();return s=>-a(s)}if(peek()==='+'){take();return unary()}return power()}
  function power(){const a=primary();if(peek()==='^'){take();const b=unary();return s=>Math.pow(a(s),b(s))}return a}
  function primary(){const t=take();if(t===undefined)throw Error('unexpected end');
   if(/^[\d.]/.test(t)){const v=parseFloat(t);return()=>v}
   if(t==='('){const a=expr();take(')');return a}
   if(/^[a-zA-Z]/.test(t)){
    if(peek()==='('&&FN[t]){take('(');const args=[];if(peek()!==')'){args.push(expr());while(peek()===','){take(',');args.push(expr())}}take(')');const f=FN[t];return s=>f(...args.map(g=>g(s)))}
    if(vars.includes(t))return s=>s[t];if(t in CONST){const v=CONST[t];return()=>v}
   }
   throw Error('unexpected '+t)}
  const f=expr();if(i<toks.length)throw Error('unexpected '+toks[i]);return f}

 const el=(tag,cls,html)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(html!==undefined)e.innerHTML=html;return e};
 const svgEl=(tag,attrs)=>{const e=document.createElementNS(SVG,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);return e};
 const COLORS=['#a65d35','#274e48','#9268a6','#4f7fa8'];
 function fmtNum(v){if(!isFinite(v))return '—';const a=Math.abs(v);return a!==0&&(a<1e-3||a>=1e5)?v.toExponential(2):(+v.toFixed(a<1?5:3)).toString()}

 function frame(w){const box=el('figure','xw');box.append(el('figcaption','xw-title',esc(w.title)));return box}
 function axes(svg,X,Y,W,H,pad){
  const sx=x=>pad+(x-X[0])/(X[1]-X[0])*(W-2*pad),sy=y=>H-pad-(y-Y[0])/(Y[1]-Y[0])*(H-2*pad);
  svg.append(svgEl('rect',{x:pad,y:pad,width:W-2*pad,height:H-2*pad,class:'xw-plotbg'}));
  if(Y[0]<0&&Y[1]>0)svg.append(svgEl('line',{x1:pad,x2:W-pad,y1:sy(0),y2:sy(0),class:'xw-axis'}));
  if(X[0]<0&&X[1]>0)svg.append(svgEl('line',{y1:pad,y2:H-pad,x1:sx(0),x2:sx(0),class:'xw-axis'}));
  const lab=(t,x,y,anchor)=>{const e=svgEl('text',{x,y,'text-anchor':anchor,class:'xw-tick'});e.textContent=t;svg.append(e)};
  lab(fmtNum(X[0]),pad,H-pad+14,'start');lab(fmtNum(X[1]),W-pad,H-pad+14,'end');lab(fmtNum(Y[1]),pad-4,pad+4,'end');lab(fmtNum(Y[0]),pad-4,H-pad,'end');
  return [sx,sy]}

 function plot(w){
  const box=frame(w),params=w.params||[],state={};params.forEach(p=>state[p.name]=p.value);
  const curves=[{expr:w.expr,label:''},...(w.extra||[])].map((c,i)=>{try{return{f:compile(c.expr,['x',...params.map(p=>p.name)]),label:c.label||c.expr,color:COLORS[i%4]}}catch{return null}}).filter(Boolean);
  const W=340,H=210,pad=34,svg=svgEl('svg',{viewBox:`0 0 ${W} ${H}`,class:'xw-svg',role:'img','aria-label':w.title});box.append(svg);
  const legend=el('div','xw-legend');if(curves.length>1)curves.forEach(c=>legend.append(el('span','',`<i style="background:${c.color}"></i>${esc(c.label)}`)));box.append(legend);
  const controls=el('div','xw-controls');box.append(controls);
  function draw(){svg.replaceChildren();const X=w.x,N=240,pts=curves.map(c=>{const a=[];for(let k=0;k<=N;k++){const x=X[0]+(X[1]-X[0])*k/N;let y;try{y=c.f({...state,x})}catch{y=NaN}a.push([x,y])}return a});
   let Y=w.y;if(!Y){const ys=pts.flat().map(p=>p[1]).filter(isFinite).sort((a,b)=>a-b);if(!ys.length)return;const lo=ys[Math.floor(ys.length*.02)],hi=ys[Math.ceil(ys.length*.98)-1];const m=(hi-lo)*.1||1;Y=[lo-m,hi+m]}
   const[sx,sy]=axes(svg,X,Y,W,H,pad);
   pts.forEach((a,i)=>{let d='',pen=false;for(const[x,y]of a){if(!isFinite(y)||y<Y[0]-(Y[1]-Y[0])*2||y>Y[1]+(Y[1]-Y[0])*2){pen=false;continue}d+=(pen?'L':'M')+sx(x).toFixed(1)+' '+sy(Math.max(Y[0]-(Y[1]-Y[0]),Math.min(Y[1]+(Y[1]-Y[0]),y))).toFixed(1);pen=true}
    svg.append(svgEl('path',{d,class:'xw-curve',stroke:curves[i].color,'clip-path':''}))})}
  params.forEach(p=>{const row=el('label','xw-slider'),out=el('output','',fmtNum(p.value));row.append(el('span','',esc(p.label||p.name)));const r=el('input');Object.assign(r,{type:'range',min:p.min,max:p.max,step:p.step||(p.max-p.min)/100,value:p.value});r.setAttribute('aria-label',p.label||p.name);r.oninput=()=>{state[p.name]=+r.value;out.textContent=fmtNum(+r.value);draw()};row.append(r,out);controls.append(row)});
  draw();box.append(el('p','xw-caption',esc(w.caption)));return box}

 function series(w){
  const box=frame(w);let f;try{f=compile(w.term,['n'])}catch{return null}
  const start=w.start||0,count=w.count||30,sums=[];let s=0;for(let n=start;n<start+count;n++){s+=f({n});sums.push(s)}
  const W=340,H=210,pad=34,svg=svgEl('svg',{viewBox:`0 0 ${W} ${H}`,class:'xw-svg',role:'img','aria-label':w.title});
  const vals=sums.filter(isFinite).concat(w.limit??[]);let lo=Math.min(...vals),hi=Math.max(...vals);const m=(hi-lo)*.08||1;const Y=[lo-m,hi+m],X=[start-.5,start+count-.5];
  const readout=el('div','xw-readout'),controls=el('div','xw-controls'),r=el('input'),play=el('button','','▶ Play');
  Object.assign(r,{type:'range',min:1,max:count,step:1,value:count});r.setAttribute('aria-label','terms shown');
  function draw(k){svg.replaceChildren();const[sx,sy]=axes(svg,X,Y,W,H,pad);let d='';for(let i=0;i<k;i++){const y=sums[i];if(!isFinite(y))continue;d+=(d?'L':'M')+sx(start+i).toFixed(1)+' '+sy(y).toFixed(1)}svg.append(svgEl('path',{d,class:'xw-path'}));for(let i=0;i<k;i++){const y=sums[i];if(!isFinite(y))continue;svg.append(svgEl('circle',{cx:sx(start+i),cy:sy(y),r:i===k-1?4.5:2.6,class:'xw-pt'+(i===k-1?' now':'')}))}
   if(w.limit!=null){const ly=sy(w.limit);svg.append(svgEl('line',{x1:pad,x2:W-pad,y1:ly,y2:ly,class:'xw-limit'}));const t=svgEl('text',{x:W-pad-2,y:ly-4,'text-anchor':'end',class:'xw-tick'});t.textContent=(w.limit_label||'limit')+' ≈ '+fmtNum(w.limit);svg.append(t)}
   const S=sums[k-1];readout.innerHTML=`Sum of first <b>${k}</b> terms: <b>${fmtNum(S)}</b>`+(w.limit!=null?` · gap to ${esc(w.limit_label||'limit')}: <b>${fmtNum(Math.abs(S-w.limit))}</b>`:'')}
  let timer=null;r.oninput=()=>{draw(+r.value)};
  play.onclick=()=>{if(timer){clearInterval(timer);timer=null;play.textContent='▶ Play';return}let k=1;play.textContent='❚❚ Pause';timer=setInterval(()=>{r.value=k;draw(k);if(++k>count){clearInterval(timer);timer=null;play.textContent='▶ Play'}},Math.max(60,2400/count))};
  const row=el('label','xw-slider');row.append(el('span','','terms'),r);controls.append(play,row);
  box.append(svg,readout,controls,el('p','xw-caption',esc(w.caption)));draw(count);return box}

 function steps(w){
  const box=frame(w),list=w.steps||[];let k=0,timer=null;
  const stage=el('div','xw-step'),note=el('p','xw-note'),dots=el('div','xw-dots'),controls=el('div','xw-controls');
  const prev=el('button','','← Back'),next=el('button','','Next →'),play=el('button','','▶ Play');
  list.forEach((_,i)=>{const d=el('button','xw-dot');d.setAttribute('aria-label','step '+(i+1));d.onclick=()=>show(i);dots.append(d)});
  function show(i){k=Math.max(0,Math.min(list.length-1,i));stage.replaceChildren();list.slice(0,k+1).forEach((s,j)=>{const line=tex(s.latex,true);line.className='xw-line'+(j===k?' now':'');stage.append(line)});note.textContent=`Step ${k+1} of ${list.length}: ${list[k].note}`;[...dots.children].forEach((d,j)=>d.classList.toggle('on',j<=k));prev.disabled=k===0;next.disabled=k===list.length-1;typeset(stage)}
  prev.onclick=()=>show(k-1);next.onclick=()=>show(k+1);
  play.onclick=()=>{if(timer){clearInterval(timer);timer=null;play.textContent='▶ Play';return}show(0);play.textContent='❚❚ Pause';timer=setInterval(()=>{if(k>=list.length-1){clearInterval(timer);timer=null;play.textContent='▶ Play';return}show(k+1)},2600)};
  controls.append(prev,play,next);box.append(stage,note,dots,controls,el('p','xw-caption',esc(w.caption)));show(0);return box}

 function network(w){
  const box=frame(w),nodes=w.nodes||[],W=340,H=240,cx=W/2,cy=H/2,R=Math.min(W,H)/2-40;
  const pos={};nodes.forEach((n,i)=>{const a=-Math.PI/2+2*Math.PI*i/nodes.length;pos[n.id]=[cx+R*Math.cos(a)*1.25,cy+R*Math.sin(a)]});
  const svg=svgEl('svg',{viewBox:`0 0 ${W} ${H}`,class:'xw-svg',role:'img','aria-label':w.title});
  svg.append(Object.assign(svgEl('defs',{}),{innerHTML:'<marker id="xwArrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7" fill="#8a9a8d"/></marker>'}));
  (w.edges||[]).forEach(e=>{const a=pos[e.from],b=pos[e.to];if(!a||!b)return;const dx=b[0]-a[0],dy=b[1]-a[1],L=Math.hypot(dx,dy)||1,o=16;svg.append(svgEl('line',{x1:a[0]+dx/L*o,y1:a[1]+dy/L*o,x2:b[0]-dx/L*o,y2:b[1]-dy/L*o,class:'xw-edge','marker-end':'url(#xwArrow)'}));if(e.label){const t=svgEl('text',{x:(a[0]+b[0])/2,y:(a[1]+b[1])/2-3,'text-anchor':'middle',class:'xw-elabel'});t.textContent=e.label;svg.append(t)}});
  nodes.forEach(n=>{const[x,y]=pos[n.id];const g=svgEl('g',{class:'xw-node',tabindex:0});g.append(svgEl('circle',{cx:x,cy:y,r:9}));const t=svgEl('text',{x,y:y+22,'text-anchor':'middle'});t.textContent=String(n.label).slice(0,28);g.append(t);svg.append(g)});
  box.append(svg,el('p','xw-caption',esc(w.caption)));return box}

 const WIDGETS={plot,series,steps,network};
 function list(items,cls){const u=el('ul',cls);(items||[]).forEach(t=>u.append(el('li','',esc(t))));return u}

 function render(d,container){
  const u=d.untangled||{},t=d.intuition||{},c=d.critic||{};
  container.replaceChildren();
  const head=el('div','x-head');
  head.innerHTML=`<p class="x-headline">${esc(u.headline)}</p><p class="x-hook">${esc(t.hook)}</p>`;
  container.append(head);
  if(u.key_equation){container.append(el('div','section-title','THE KEY EQUATION'));const eq=tex(u.key_equation,true);eq.className='x-eq';container.append(eq)}
  if((u.symbols||[]).length){const tb=el('table','x-symbols');(u.symbols).forEach(s=>{const tr=el('tr');const a=el('td');a.append(tex(s.symbol));tr.append(a,el('td','',esc(s.meaning)));tb.append(tr)});container.append(el('div','section-title','WHAT THE SYMBOLS MEAN'),tb)}
  container.append(el('div','section-title','UNTANGLED'),el('p','x-core',esc(u.core_statement)));
  if((u.given||[]).length||(u.concludes||[]).length){const gc=el('div','x-gc');gc.append(el('div','x-col','<b>Given</b>'),el('div','x-col','<b>Concludes</b>'));gc.children[0].append(list(u.given));gc.children[1].append(list(u.concludes));container.append(gc)}
  container.append(el('div','section-title','THE INTUITION'));(t.intuition||[]).forEach(p=>container.append(el('p','x-p',esc(p))));
  if(t.analogy)container.append(el('p','x-analogy','<b>Analogy.</b> '+esc(t.analogy)));
  if(d.video){container.append(el('div','section-title','ANIMATION'));const v=el('video','x-video');Object.assign(v,{controls:true,preload:'metadata',src:d.video,playsInline:true});v.setAttribute('aria-label','Animated explanation');container.append(v)}
  const ws=(d.widgets||[]).map(w=>{try{return WIDGETS[w.type]?.(w)}catch{return null}}).filter(Boolean);
  if(ws.length){container.append(el('div','section-title','PLAY WITH IT'));ws.forEach(w=>container.append(w))}
  if((t.ladder||[]).length){container.append(el('div','section-title','EXPLAIN IT AGAIN, AT YOUR LEVEL'));const tabs=el('div','x-tabs'),body=el('p','x-p');t.ladder.forEach((l,i)=>{const b=el('button','',esc(l.level));b.onclick=()=>{[...tabs.children].forEach(x=>x.classList.remove('on'));b.classList.add('on');body.textContent=l.text;typeset(body)};tabs.append(b);if(!i)b.click()});container.append(tabs,body)}
  if(t.why_it_matters)container.append(el('div','section-title','WHY IT MATTERS'),el('p','x-p',esc(t.why_it_matters)));
  if((t.misconceptions||[]).length)container.append(el('div','section-title','TEMPTING BUT WRONG'),list(t.misconceptions,'x-list'));
  if((t.explore||[]).length)container.append(el('div','section-title','QUESTIONS TO CHASE NEXT'),list(t.explore,'x-list'));
  if((u.foundations||[]).length&&typeof nodes!=='undefined'){const row=el('div','x-chips');u.foundations.forEach(id=>{const n=nodes.get(id);if(!n)return;const b=el('button','x-chip',esc(n.title));b.onclick=()=>{try{visible.add(id);select(id)}catch{}};row.append(b)});if(row.children.length)container.append(el('div','section-title','LEARN THESE FIRST'),row)}
  const score=typeof c.score==='number'?c.score:null;
  container.append(el('p','extraction x-badge',`AI-generated teaching draft (${esc(d.model)})${score!==null?` · reviewer agent score ${esc(score)}/10`:''}. Not verified against the proof; pictures may be simplified toy cases. ${d.source?`<a href="${esc(d.source)}" target="_blank" rel="noopener">Read the source ↗</a>`:''}`));
  typeset(container);
 }

 async function open(fid,container,button){
  if(container.childElementCount){container.replaceChildren();button.textContent=button.dataset.label;return}
  container.innerHTML='<p class="extraction">Loading explainer…</p>';
  try{let d=cache.get(fid);if(!d){const r=await fetch('explainers/'+fid+'.json',{cache:'no-cache'});if(!r.ok)throw 0;d=await r.json();cache.set(fid,d)}render(d,container);button.textContent='Hide intuition'}
  catch{container.innerHTML='<p class="extraction">Explainer unavailable.</p>'}
 }

 async function mount(n){
  if(!n)return;await loadIndex();try{if(selected!==n.id)return}catch{}
  const fid=n.kind==='Family'?n.id:n.family;if(!fid||!index[fid])return;
  const host=document.getElementById('inspector'),anchor=document.getElementById('learningPath');if(!host||!anchor||document.getElementById('explainer'))return;
  const meta=index[fid],wrap=el('section','x-wrap');wrap.id='explainer';
  const label=n.kind==='Family'?'✦ Intuition & animation':'✦ Intuition for this family';
  const b=el('button','primary x-open',label);b.dataset.label=label;
  const sub=el('p','x-sub',esc(meta.headline)+(meta.video?' · with animation':''));
  const body=el('div','x-body');b.onclick=()=>open(fid,body,b);
  wrap.append(b,sub,body);anchor.before(wrap);
 }
 window.mathuniExplain={mount,compile};
 loadIndex();
})();
