const ALPHA=0.25,K=5,LAMBDA=0.15,T=100,SIGMA=0.40,BETA=1.4;
const W1=0.40,W2=0.25,W3=0.20,W4=0.15,JUMP_P=0.35,RANGE=6;
const D6=[[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]];
function mulberry32(a){return function(){let t=a+=0x6D2B79F5;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296}}
function man(a,b){return Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1])+Math.abs(a[2]-b[2])}
function cheb(a,b){return Math.max(Math.abs(a[0]-b[0]),Math.abs(a[1]-b[1]),Math.abs(a[2]-b[2]))}
function key(p){return p[0]+','+p[1]+','+p[2]}
let rng=mulberry32(21); const urand=()=>rng();
function bresenham3(a,b){
  let [z0,y0,x0]=a,[z1,y1,x1]=b;
  const dz=Math.abs(z1-z0),dy=Math.abs(y1-y0),dx=Math.abs(x1-x0);
  const sz=z0<z1?1:-1,sy=y0<y1?1:-1,sx=x0<x1?1:-1;
  const cells=[]; let z=z0,y=y0,x=x0;
  if(dx>=dy && dx>=dz){let py=2*dy-dx,pz=2*dz-dx; for(let i=0;i<=dx;i++){cells.push([z,y,x]); if(z===z1&&y===y1&&x===x1) break; if(py>=0){y+=sy;py-=2*dx} if(pz>=0){z+=sz;pz-=2*dx} x+=sx; py+=2*dy; pz+=2*dz;}}
  else if(dy>=dx && dy>=dz){let px=2*dx-dy,pz=2*dz-dy; for(let i=0;i<=dy;i++){cells.push([z,y,x]); if(z===z1&&y===y1&&x===x1) break; if(px>=0){x+=sx;px-=2*dy} if(pz>=0){z+=sz;pz-=2*dy} y+=sy; px+=2*dx; pz+=2*dz;}}
  else {let px=2*dx-dz,py=2*dy-dz; for(let i=0;i<=dz;i++){cells.push([z,y,x]); if(z===z1&&y===y1&&x===x1) break; if(px>=0){x+=sx;px-=2*dz} if(py>=0){y+=sy;py-=2*dz} z+=sz; px+=2*dx; py+=2*dy;}}
  return cells;
}
function carveBall(walls,d,h,w,z,y,x,rz,ry,rx){
  for(let zz=Math.max(1,z-rz); zz<Math.min(d-1,z+rz+1); zz++)
    for(let yy=Math.max(1,y-ry); yy<Math.min(h-1,y+ry+1); yy++)
      for(let xx=Math.max(1,x-rx); xx<Math.min(w-1,x+rx+1); xx++){
        const A=(zz-z)/Math.max(1,rz),B=(yy-y)/Math.max(1,ry),C=(xx-x)/Math.max(1,rx);
        if(A*A+B*B+C*C<=1.05) walls[zz][yy][xx]=0;
      }
}
function carveLine(walls,d,h,w,a,b,r){
  const n=Math.max(Math.abs(b[0]-a[0]),Math.abs(b[1]-a[1]),Math.abs(b[2]-a[2]),1);
  for(let i=0;i<=n;i++){const t=i/n; carveBall(walls,d,h,w, Math.round(a[0]+t*(b[0]-a[0])), Math.round(a[1]+t*(b[1]-a[1])), Math.round(a[2]+t*(b[2]-a[2])), r,r,r+1);}
}
function makeMoon(w=29,h=19,d=12,seed=21){
  rng=mulberry32(seed>>>0);
  const walls=Array.from({length:d},()=>Array.from({length:h},()=>Array.from({length:w},()=>1)));
  let y=Math.floor(h/2), z=2, points=[];
  for(let x=2;x<w-2;x++){
    if(urand()<0.35) y=Math.max(3,Math.min(h-4,y+[-1,0,1][Math.floor(urand()*3)]));
    if(urand()<0.18) z=Math.max(2,Math.min(Math.floor(d/2),z+[-1,0,1][Math.floor(urand()*3)]));
    points.push([z,y,x]); carveBall(walls,d,h,w,z,y,x,1, urand()<0.25?2:1, 2);
  }
  const start=points[1];
  for(let i=0;i<3;i++){
    const base=points[Math.floor(points.length*0.25+urand()*points.length*0.5)];
    const dy=(urand()<0.5?-1:1)*(3+Math.floor(urand()*4));
    const end=[base[0], Math.max(2,Math.min(h-3,base[1]+dy)), base[2]];
    carveLine(walls,d,h,w,base,end,1); carveBall(walls,d,h,w,...end,2,2,2);
  }
  const lip=points[points.length-3]; const sky=[d-2, lip[1], lip[2]];
  carveLine(walls,d,h,w,lip,sky,1); carveBall(walls,d,h,w,...sky,1,2,2);
  walls[start[0]][start[1]][start[2]]=0; walls[sky[0]][sky[1]][sky[2]]=0;
  const elevation=Array.from({length:d},(_,zz)=>Array.from({length:h},()=>Array.from({length:w},()=>zz/Math.max(1,d-1))));
  const hazard=Array.from({length:d},()=>Array.from({length:h},()=>Array.from({length:w},()=>0)));
  const ice=[];
  for(let zz=0;zz<d;zz++) for(let yy=0;yy<h;yy++) for(let xx=0;xx<w;xx++){
    if(walls[zz][yy][xx]) continue;
    if(zz>=d-3) hazard[zz][yy][xx]=Math.max(hazard[zz][yy][xx], 0.35+0.25*(zz/Math.max(1,d-1)));
    if(urand()<0.06) hazard[zz][yy][xx]=Math.max(hazard[zz][yy][xx],0.55);
    if(zz<=3 && urand()<0.04){ ice.push([zz,yy,xx]); elevation[zz][yy][xx]=Math.min(1,elevation[zz][yy][xx]+0.12); }
  }
  return {w,h,d,walls,elevation,hazard,start,goal:sky,ice};
}
function free(g,p){const[z,y,x]=p;return z>=0&&y>=0&&x>=0&&z<g.d&&y<g.h&&x<g.w&&g.walls[z][y][x]===0}
function neigh(g,p){const out=[];for(const[dz,dy,dx] of D6){const q=[p[0]+dz,p[1]+dy,p[2]+dx];if(free(g,q)) out.push(q)} return out}
function hasLOS(g,p,h){if(!free(g,p)||!free(g,h)) return false; const cells=bresenham3(p,h); for(let i=1;i<cells.length-1;i++) if(!free(g,cells[i])) return false; return true;}
function scan(g,p){
  const list=[];
  for(let z=Math.max(0,p[0]-RANGE);z<Math.min(g.d,p[0]+RANGE+1);z++)
    for(let y=Math.max(0,p[1]-RANGE);y<Math.min(g.h,p[1]+RANGE+1);y++)
      for(let x=Math.max(0,p[2]-RANGE);x<Math.min(g.w,p[2]+RANGE+1);x++){
        const q=[z,y,x]; if(!free(g,q)||cheb(p,q)>RANGE) continue; if(hasLOS(g,p,q)) list.push(q);
      }
  return list;
}
function astar3(g){
  const open=[{p:g.start,f:man(g.start,g.goal)}], came=new Map(), gS=new Map([[key(g.start),0]]), inO=new Set([key(g.start)]);
  while(open.length){
    open.sort((a,b)=>a.f-b.f); const cur=open.shift(); inO.delete(key(cur.p));
    if(key(cur.p)===key(g.goal)){const path=[cur.p]; let k=key(cur.p); while(came.has(k)){const prev=came.get(k); path.push(prev); k=key(prev)} path.reverse(); return path;}
    for(const q of neigh(g,cur.p)){const t=gS.get(key(cur.p))+1; if(t<(gS.get(key(q))??Infinity)){ came.set(key(q),cur.p); gS.set(key(q),t); if(!inO.has(key(q))){open.push({p:q,f:t+man(q,g.goal)}); inO.add(key(q))} }}
  }
  return null;
}
function scoreNode(g,n,cur,gHat,S,D){
  const A=Math.max(0,Math.min(1,g.elevation[n[0]][n[1]][n[2]]-g.elevation[cur[0]][cur[1]][cur[2]]+0.5));
  let raw=0; for(const q of neigh(g,n)) if(!S.has(key(q))&&!D.has(key(q))) raw++;
  return W1*(1/(man(n,gHat)+1))+W2*A+W3*(raw/6)-W4*g.hazard[n[0]][n[1]][n[2]]+urand()*SIGMA;
}
function nudge(scores,m,k){const L=Math.log(1+m); return scores.map((s,i)=>s*Math.max(0.05,1-LAMBDA*L*(i/Math.max(1,k))))}
function lottery(items){
  const w=items.map(([s])=>Math.pow(Math.max(1e-9,s),BETA));
  let tot=w.reduce((a,b)=>a+b,0), pick=urand()*tot, acc=0;
  for(let i=0;i<items.length;i++){acc+=w[i]; if(pick<=acc) return items[i][1]} return items[items.length-1][1];
}
const view=document.getElementById('view'), ctx=view.getContext('2d'), logEl=document.getElementById('log');
function log(m){logEl.textContent+=m+'\n'; logEl.scrollTop=logEl.scrollHeight}
let G=null,Apath=null,agent=null,viewZ=1,autoT=null,lastRitual=false;
function fresh(){
  agent={current:G.start.slice(),H:new Set([key(G.start)]),Hlist:[G.start.slice()],S:new Set([key(G.start)]),D:new Set(),
    gHat:G.goal.slice(),steps:0,moves:0,ritualCount:0,path:[G.start.slice()],done:false,reason:'running'};
  viewZ=G.start[0];
}
function newTube(){
  stopAuto();
  const seed=parseInt(document.getElementById('seed').value,10)||21;
  G=makeMoon(29,19,12,seed); Apath=astar3(G); fresh(); logEl.textContent='';
  document.getElementById('asN').textContent=Apath?String(Apath.length-1):'inf';
  document.getElementById('asS').textContent=Apath?'omniscient 6-conn':'no path';
  log('tube seed '+seed+(Apath?'  A* '+(Apath.length-1):'  A* fail'));
  update(); drawAll();
}
function goTo(p,cost,why){
  agent.current=p.slice(); agent.steps+=cost; agent.S.add(key(p)); agent.path.push(p.slice());
  if(document.getElementById('follow').checked) viewZ=p[0];
  if(key(p)===key(G.goal)){agent.done=true;agent.reason='skylight';stopAuto();log('SKYLIGHT  cost='+agent.steps.toFixed(1)+'  '+why)}
}
function step(){
  if(!agent||agent.done) return;
  const useR=document.getElementById('ritual').checked; const A=agent; A.moves++; lastRitual=false;
  for(const q of scan(G,A.current)) if(!A.H.has(key(q))){A.H.add(key(q)); A.Hlist.push(q)}
  const hubs=A.Hlist.filter(h=>key(h)!==key(A.current)&&hasLOS(G,A.current,h));
  if(hubs.length && urand()<JUMP_P){
    hubs.sort((a,b)=>man(a,A.gHat)-man(b,A.gHat));
    const h=hubs[0]; log('LOS jump z'+h[0]); goTo(h,ALPHA*man(A.current,h),'jump'); if(A.done){update();drawAll();return}
  }
  for(const n of neigh(G,A.current)){
    if(key(n)===key(G.goal)) continue;
    const opens=neigh(G,n);
    if(!opens.length||opens.every(q=>A.S.has(key(q)))) A.D.add(key(n));
  }
  let cand=[];
  for(const n of neigh(G,A.current)){ if(A.D.has(key(n))) continue; cand.push([scoreNode(G,n,A.current,A.gHat,A.S,A.D),n]); }
  if(!cand.length){
    const back=neigh(G,A.current).filter(q=>A.S.has(key(q)));
    if(back.length){ const pick=back[Math.floor(urand()*back.length)]; log('backtrack z'+pick[0]); goTo(pick,1,'backtrack'); update();drawAll(); return; }
    const live=A.Hlist.filter(h=>key(h)!==key(A.current)&&hasLOS(G,A.current,h));
    if(live.length){ live.sort((a,b)=>man(a,A.current)-man(b,A.current)); log('escape hop'); goTo(live[0],ALPHA*man(A.current,live[0]),'hop'); update();drawAll(); return; }
    A.done=true; A.reason='sealed pocket'; stopAuto(); log('sealed pocket'); update();drawAll(); return;
  }
  cand.sort((a,b)=>b[0]-a[0]); let top=cand.slice(0,Math.min(K,cand.length));
  if(useR && (A.moves%T===0||top.length>=4) && top.length>=4){
    A.ritualCount++; lastRitual=true;
    const nd=nudge(top.map(t=>t[0]),A.ritualCount,top.length);
    top=top.map((t,i)=>[nd[i],t[1]]); log('ritual #'+A.ritualCount);
  }
  const chosen=lottery(top);
  if(man(chosen,G.goal)<man(A.gHat,G.goal)) A.gHat=chosen.slice();
  const climb=chosen[0]-A.current[0];
  goTo(chosen,1, climb>0?'up chimney':climb<0?'down':'gallery');
  if(!A.done && A.moves>=4000){A.done=true;A.reason='max_steps';stopAuto()}
  update(); drawAll();
}
function update(){
  document.getElementById('ltN').textContent=agent.steps.toFixed(1);
  document.getElementById('ltS').textContent=(agent.done?agent.reason:'running')+' · mv '+agent.moves+' · rit '+agent.ritualCount;
  const c=agent.current; document.getElementById('pos').textContent='z='+c[0]+' y='+c[1]+' x='+c[2]+'  floor '+viewZ+(viewZ>=G.d-3?'  (near vacuum)':'');
}
function drawSlice(c,g,z,W,H,on){
  c.fillStyle='#0a0705'; c.fillRect(0,0,W,H);
  const pad=6, cell=Math.floor(Math.min((W-pad*2)/g.w,(H-pad*2)/g.h));
  const ox=Math.floor((W-cell*g.w)/2), oy=Math.floor((H-cell*g.h)/2);
  for(let y=0;y<g.h;y++) for(let x=0;x<g.w;x++){
    const px=ox+x*cell, py=oy+y*cell;
    if(g.walls[z][y][x]){c.fillStyle='#2a221b'; c.fillRect(px,py,cell,cell); continue}
    c.fillStyle=z>=g.d-3?'#3a2a18':'#1c1713'; c.fillRect(px,py,cell,cell);
    if(g.hazard[z][y][x]>0.4){c.fillStyle='rgba(200,80,40,.4)'; c.fillRect(px,py,cell,cell)}
  }
  if(g.ice) for(const p of g.ice) if(p[0]===z){c.fillStyle='rgba(140,190,220,.7)'; c.fillRect(ox+p[2]*cell,oy+p[1]*cell,cell,cell)}
  if(agent){ for(const p of agent.Hlist) if(p[0]===z){c.fillStyle='rgba(126,182,255,.25)'; c.fillRect(ox+p[2]*cell,oy+p[1]*cell,cell,cell)} }
  if(document.getElementById('showA').checked && Apath){
    c.fillStyle='rgba(255,107,107,.5)';
    for(const p of Apath) if(p[0]===z) c.fillRect(ox+p[2]*cell+cell*.28,oy+p[1]*cell+cell*.28,cell*.44,cell*.44);
  }
  if(agent){
    c.fillStyle=lastRitual?'#f0d78c':'#e8c07a';
    for(const p of agent.path) if(p[0]===z) c.fillRect(ox+p[2]*cell+cell*.18,oy+p[1]*cell+cell*.18,cell*.64,cell*.64);
    if(agent.current[0]===z){c.fillStyle='#fff6e8'; c.fillRect(ox+agent.current[2]*cell,oy+agent.current[1]*cell,cell,cell)}
  }
  if(g.start[0]===z){c.fillStyle='#7bd88f'; c.fillRect(ox+g.start[2]*cell,oy+g.start[1]*cell,cell,cell)}
  if(g.goal[0]===z){c.fillStyle='#ffe08a'; c.fillRect(ox+g.goal[2]*cell,oy+g.goal[1]*cell,cell,cell)}
  if(on){c.strokeStyle='#e8c07a'; c.lineWidth=3; c.strokeRect(1,1,W-2,H-2)}
}
function drawAll(){
  drawSlice(ctx,G,viewZ,view.width,view.height,false);
  const box=document.getElementById('floors'); box.innerHTML='';
  for(let z=G.d-1;z>=0;z--){
    const wrap=document.createElement('div'); wrap.className='fl'+(z===viewZ?' on':'');
    wrap.innerHTML='<div class="t">z '+z+(z===agent.current[0]?' · rover':'')+(z===G.goal[0]?' · sky':'')+(z<=2?' · ice':'')+'</div>';
    const mini=document.createElement('canvas'); mini.width=160; mini.height=110; wrap.appendChild(mini);
    wrap.onclick=()=>{viewZ=z; drawAll()}; box.appendChild(wrap);
    drawSlice(mini.getContext('2d'),G,z,160,110,z===viewZ);
  }
}
function stopAuto(){if(autoT){clearInterval(autoT);autoT=null} document.getElementById('btnAuto').textContent='Auto'}
document.getElementById('btnNew').onclick=()=>{document.getElementById('seed').value=String((parseInt(document.getElementById('seed').value,10)||0)+1); newTube()};
document.getElementById('btnStep').onclick=step;
document.getElementById('btnAuto').onclick=()=>{
  if(autoT){stopAuto();return}
  document.getElementById('btnAuto').textContent='Pause';
  autoT=setInterval(()=>{if(!agent||agent.done){stopAuto();return} step()},70);
};
document.getElementById('btnReset').onclick=()=>{stopAuto();fresh();log('reset same tube');update();drawAll()};
document.getElementById('showA').onchange=drawAll;
document.getElementById('seed').onchange=newTube;
newTube();
