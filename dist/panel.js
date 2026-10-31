(() => {
 const panel=document.querySelector('.inspector'),grip=document.querySelector('#inspectorGrip'),split=document.querySelector('#inspectorResize'),floatSize=document.querySelector('#inspectorFloatResize'),toggle=document.querySelector('#inspectorToggle');
 const mobile=()=>innerWidth<=800;
 let saved={width:440,floating:false,x:80,y:100,height:600};
 try{Object.assign(saved,JSON.parse(localStorage.getItem('mathuni.inspector')||'{}'))}catch{}
 let active=null;
 const maxWidth=()=>saved.floating?innerWidth-24:innerWidth-(innerWidth>1150?600:400);
 const clamp=(v,min,max)=>Math.max(min,Math.min(max,Number(v)||min));
 function remember(){try{localStorage.setItem('mathuni.inspector',JSON.stringify(saved))}catch{}}
 function apply(){
  const floating=!!saved.floating&&!mobile();
  saved.width=clamp(saved.width,300,Math.max(300,maxWidth()));
  saved.height=clamp(saved.height,260,Math.max(260,innerHeight-100));
  saved.x=clamp(saved.x,0,Math.max(0,innerWidth-saved.width));saved.y=clamp(saved.y,76,Math.max(76,innerHeight-saved.height));
  document.documentElement.style.setProperty('--inspector-width',saved.width+'px');
  panel.classList.toggle('floating',floating);document.querySelector('main').classList.toggle('inspector-floating',floating);
  panel.style.setProperty('--panel-left',saved.x+'px');panel.style.setProperty('--panel-top',saved.y+'px');panel.style.setProperty('--panel-height',saved.height+'px');
  toggle.textContent=floating?'Dock panel':'Float panel';toggle.setAttribute('aria-pressed',String(floating));
  split.setAttribute('aria-valuenow',String(Math.round(saved.width)));split.setAttribute('aria-valuemax',String(Math.max(300,maxWidth())));
 }
 toggle.onclick=()=>{if(!saved.floating){const r=panel.getBoundingClientRect();saved.x=r.left;saved.y=Math.max(76,r.top);saved.height=Math.min(650,innerHeight-100)}saved.floating=!saved.floating;apply();remember()};
 document.querySelector('#inspectorReset').onclick=()=>{saved={width:440,floating:false,x:80,y:100,height:600};apply();remember()};
 function start(e,kind){
  if(mobile()||e.button!==0||e.target.closest('button'))return;
  const r=panel.getBoundingClientRect();
  if(kind==='move'&&!saved.floating){saved.floating=true;saved.x=r.left;saved.y=Math.max(76,r.top);saved.height=Math.min(r.height,innerHeight-100);apply()}
  active={kind,x:e.clientX,y:e.clientY,start:{...saved},target:e.currentTarget};
  e.currentTarget.setPointerCapture(e.pointerId);document.body.classList.add('panel-dragging');e.preventDefault();
 }
 grip.onpointerdown=e=>start(e,'move');split.onpointerdown=e=>start(e,'width');floatSize.onpointerdown=e=>start(e,'size');
 function move(e){if(!active)return;const dx=e.clientX-active.x,dy=e.clientY-active.y,s=active.start;
  if(active.kind==='move'){saved.x=s.x+dx;saved.y=s.y+dy}
  else if(active.kind==='width'){saved.width=s.width-dx;if(saved.floating)saved.x=s.x+dx}
  else{saved.width=s.width+dx;saved.height=s.height+dy}
  apply();
 }
 function end(){if(!active)return;active=null;document.body.classList.remove('panel-dragging');remember()}
 for(const handle of [grip,split,floatSize]){handle.addEventListener('pointermove',move);handle.addEventListener('pointerup',end);handle.addEventListener('pointercancel',end);handle.addEventListener('lostpointercapture',end)}
 split.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();saved.width=e.key==='Home'?300:e.key==='End'?maxWidth():saved.width+(e.key==='ArrowLeft'?24:-24);apply();remember()};
 grip.onkeydown=e=>{if(e.target!==grip||!saved.floating||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();saved.x+=e.key==='ArrowLeft'?-20:e.key==='ArrowRight'?20:0;saved.y+=e.key==='ArrowUp'?-20:e.key==='ArrowDown'?20:0;apply();remember()};
 floatSize.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();saved.width+=e.key==='ArrowLeft'?-24:e.key==='ArrowRight'?24:0;saved.height+=e.key==='ArrowUp'?-24:e.key==='ArrowDown'?24:0;apply();remember()};
 addEventListener('resize',()=>{apply()});apply();
 // A release writes version.json last. Existing tabs pick up completed releases.
 const build=document.querySelector('meta[name="mathuni-build"]')?.content;
 async function checkUpdate(){if(!build||active||document.hidden||document.querySelector('#leanDialog')?.open)return;try{const r=await fetch('version.json?t='+Date.now(),{cache:'no-store'});if(!r.ok)return;const v=await r.json();if(v.build&&v.build!==build){remember();location.reload()}}catch{}}
 setInterval(checkUpdate,30000);document.addEventListener('visibilitychange',checkUpdate);
})();
