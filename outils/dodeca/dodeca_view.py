"""
DODECA VIEW - shows dodeca_core.bbmodel in your browser (rotate with the mouse). No install needed.

Put this file next to  dodeca_core.bbmodel, dodeca_core.png and dodeca_core_glowmask.png, then run:
    python dodeca_view.py
It reads the plates straight from the .bbmodel (the same data Blockbench uses), so what you see is what the model contains.
Mouse: drag = rotate, wheel = zoom.  Modes: simple, fractal level 1/2, animated satellites. Buttons: auto-rotate, glow, "flip" (if the faces do not meet, same as --flip of the generator).
"""
import base64, json, os, webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
def b64(name):
    with open(os.path.join(HERE, name), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

bb = json.load(open(os.path.join(HERE, "dodeca_core.bbmodel")))
res = bb["resolution"]
plates = []
for e in bb["elements"]:
    f = e["faces"]["up"]["uv"]
    plates.append({"c": e["origin"], "rot": e["rotation"], "L": e["to"][0] - e["from"][0], "uv": f})
data = {"plates": plates, "tex": b64("dodeca_core.png"), "glow": b64("dodeca_core_glowmask.png"),
        "tile": plates[0]["uv"][2] - plates[0]["uv"][0], "W": res["width"], "H": res["height"]}

HTML = r"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Fun — Dodécaèdre 💎</title>
<style>
html,body{margin:0;height:100%;background:#0b0714;color:#e9d8f0;font:14px system-ui,sans-serif;overflow:hidden}
canvas{display:block;width:100vw;height:100vh;cursor:grab}canvas:active{cursor:grabbing}
#ui{position:fixed;left:12px;top:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;max-width:calc(100vw - 24px)}
button,label,a#retour{background:#2a1c3a;color:#f3e6fb;border:1px solid #6a4a8a;border-radius:999px;padding:7px 13px;font:inherit;cursor:pointer;text-decoration:none}
#itinfo{position:fixed;right:12px;bottom:12px;background:#2a1c3acc;color:#f3e6fb;border:1px solid #6a4a8a;border-radius:999px;padding:6px 12px;font-size:13px}
#itv{margin-left:4px;color:#ffd9a8}
@media(max-width:640px){
 #ui{max-height:calc(100dvh - 110px);overflow-y:auto}
 #itinfo{bottom:46px;right:auto;left:12px;font-size:12px}
}
button[aria-pressed="true"]{background:#7a3a7a}
input[type=range]{vertical-align:middle;width:90px}
#info{position:fixed;left:12px;bottom:12px;color:#c9b3d6;font-size:13px}
</style></head><body>
<canvas id="c"></canvas>
<div id="ui">
 <a id="retour" href="./index.html">🏡 Retour au petit bal</a>
 <button data-mode="simple" aria-pressed="true">Simple</button>
 <button data-mode="f1" aria-pressed="false">Fractale niv. 1</button>
 <button data-mode="f2" aria-pressed="false">Fractale niv. 2</button>
 <button data-mode="sat" aria-pressed="false">Satellites animés</button>
 <button data-mode="dragon" aria-pressed="false">Dragon</button>
 <button data-mode="cine" aria-pressed="false">Cinématique ▶</button>
 <label>Itérations <input id="iter" type="range" min="5" max="11" value="8"><b id="itv">11</b></label>
 <button id="auto" aria-pressed="true">Rotation auto</button>
 <button id="pulse" aria-pressed="true">Impulsions</button>
 <button id="snd" aria-pressed="true">Son</button>
 <button id="phone" aria-pressed="false">Mode téléphone : désactivé</button>
 <button id="back" aria-pressed="true">Cristal (translucide)</button>
 <button id="flip" aria-pressed="false">Flip (rx, ry)</button>
 <label>Lueur <input id="glow" type="range" min="0" max="150" value="100"></label>
 <label>Copies <input id="copy" type="range" min="15" max="38" value="28"></label>
 <label>Orbite <input id="orbit" type="range" min="0" max="200" value="100"></label>
</div>
<div id="info"></div>
<div id="itinfo"></div>
<script>
const D=__DATA__;
const cv=document.getElementById('c'),ctx=cv.getContext('2d'),info=document.getElementById('info');
let yaw=0.6,pitch=0.35,zoom=1,auto=true,flip=false,glowK=1,drag=null,mode='simple',copyK=0.28,orbitK=1;
let T0=0,SHX=0,SHY=0,DG=null,CE=null,PULSE=true,TRANSL=true,NU=[];
const T=D.tile,L=D.plates[0].L;
const tex=new Image(),glow=new Image();let ready=0;
tex.onload=glow.onload=()=>{ready++};tex.src=D.tex;glow.src=D.glow;
function size(){const r=devicePixelRatio||1;cv.width=innerWidth*r;cv.height=innerHeight*r}
addEventListener('resize',size);size();
const rad=a=>a*Math.PI/180;
function rotZYX(e){let[rx,ry,rz]=e.map(rad);
 const cx=Math.cos(rx),sx=Math.sin(rx),cy=Math.cos(ry),sy=Math.sin(ry),cz=Math.cos(rz),sz=Math.sin(rz);
 return[[cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx],[sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx],[-sy,cy*sx,cy*cx]];}
const mv=(M,v)=>[M[0][0]*v[0]+M[0][1]*v[1]+M[0][2]*v[2],M[1][0]*v[0]+M[1][1]*v[1]+M[1][2]*v[2],M[2][0]*v[0]+M[2][1]*v[1]+M[2][2]*v[2]];
const mm=(A,B)=>A.map((r,i)=>[0,1,2].map(j=>r[0]*B[0][j]+r[1]*B[1][j]+r[2]*B[2][j]));
const I3=[[1,0,0],[0,1,0],[0,0,1]];
function axisRot(ax,ang){const l=Math.hypot(...ax),x=ax[0]/l,y=ax[1]/l,z=ax[2]/l,c=Math.cos(ang),s=Math.sin(ang),t=1-c;
 return[[t*x*x+c,t*x*y-s*z,t*x*z+s*y],[t*x*y+s*z,t*y*y+c,t*y*z-s*x],[t*x*z-s*y,t*y*z+s*x,t*z*z+c]];}
// 20 sommets déduits des 12 plaques (chaque plaque : pentagone de rayon 31px, sommet en haut)
let PL=[];function buildPlates(){PL=D.plates.map(p=>{const rot=flip?[-p.rot[0],-p.rot[1],p.rot[2]]:p.rot;return{c:p.c,R:rotZYX(rot),uv:p.uv}})}
let NORM=[],RIN=0;function buildNorm(){NORM=PL.map(p=>[p.R[0][1],p.R[1][1],p.R[2][1]]);RIN=Math.hypot(...D.plates[0].c)}
buildPlates();buildNorm();NU=NORM.map(n=>{const l=Math.hypot(...n);return n.map(x=>x/l)});
const VDIR=(()=>{const out=[];for(const p of PL){for(let k=0;k<5;k++){const a=rad(-90+72*k),lx=31*Math.cos(a)/T*L,lz=31*Math.sin(a)/T*L;
 const w=mv(p.R,[lx,0,lz]);const v=[p.c[0]+w[0],p.c[1]+w[1],p.c[2]+w[2]];
 if(!out.some(o=>Math.hypot(o[0]-v[0],o[1]-v[1],o[2]-v[2])<1))out.push(v)}}return out})();
const gl=document.createElement('canvas'),gx=gl.getContext('2d');
const pent=[];for(let k=0;k<5;k++){const a=rad(-90+72*k);pent.push([T/2+31*Math.cos(a),T/2+31*Math.sin(a)]);}

let ITER=8,DPTS=null,DIT=0;
function dragonPts(n){let s=[];for(let i=0;i<n;i++){const r=s.slice().reverse().map(x=>-x);s=s.concat([1],r)}
 let p=[[0,0],[1,0]],a=0,x=1,y=0;for(const tn of s){a+=tn*Math.PI/2;x+=Math.round(Math.cos(a));y+=Math.round(Math.sin(a));p.push([x,y])}
 const E=p[p.length-1],len=Math.hypot(E[0],E[1]),an=Math.atan2(E[1],E[0]),c=Math.cos(-an),sn=Math.sin(-an);
 return p.map(q=>[(q[0]*c-q[1]*sn)/len,(q[0]*sn+q[1]*c)/len])}
function dragonProj(t,V,sc,W,H){
 if(!DPTS||DIT!==ITER){DPTS=dragonPts(ITER);DIT=ITER}
 const N=DPTS.length,P=((t/1000)%12)/12,out=[];
 VDIR.forEach((d,i)=>{
  if(i%5!==0&&i%5!==2)return;
  const r=Math.hypot(...d),dir=d.map(x=>x/r),h=Math.abs(dir[1])<0.9?[0,1,0]:[1,0,0];
  let pp=[dir[1]*h[2]-dir[2]*h[1],dir[2]*h[0]-dir[0]*h[2],dir[0]*h[1]-dir[1]*h[0]];const pl=Math.hypot(...pp);pp=pp.map(x=>x/pl);
  pp=mv(axisRot(dir,i*2.4),pp);const sg=(i%2?1:-1),S=r*1.7*(DG!==null?1+CE.ex*0.7:1);
  const g=DG!==null?Math.max(0,Math.min(1,DG*1.12-i*0.012)):Math.max(0,Math.min(1,(P-i*0.012)/0.6)),cnt=Math.max(2,Math.floor(N*smooth(g))),fade=DG!==null?(1-CE.ex):(P>0.85?Math.max(0,1-(P-0.85)/0.15):1);
  const pts=[];
  for(let k=0;k<cnt;k++){const q=DPTS[k],u=q[0]*S,v=q[1]*S*sg;
   const w0=[d[0]+dir[0]*u+pp[0]*v,d[1]+dir[1]*u+pp[1]*v,d[2]+dir[2]*u+pp[2]*v],cc=1,w=[w0[0]*cc,w0[1]*cc,w0[2]*cc],m=mv(V,w);
   pts.push([W/2+SHX+sc*m[0],H/2+SHY-sc*m[1],m[2]])}
  out.push({pts,fade})});
 return out}
function strokeDragon(DR,side,W){
 ctx.globalCompositeOperation='source-over';ctx.lineWidth=Math.max(1,W/1100);ctx.lineJoin='round';
 for(const c of DR){const pts=c.pts;ctx.beginPath();let any=false;
  for(let k=1;k<pts.length;k++){const a=pts[k-1],b=pts[k],z=(a[2]+b[2])/2;if((z<0?-1:1)!==side)continue;ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);any=true}
  if(any){ctx.strokeStyle='rgba(255,246,220,'+(0.7*c.fade).toFixed(3)+')';ctx.shadowColor='rgba(255,210,120,0.9)';ctx.shadowBlur=side>0?4:2;ctx.stroke();ctx.shadowBlur=0}}}
function sphereDraw(V,sc,W,H,t,K){
 const sg=CE.sg;if(sg<=0.002)return;
 const cx=W/2+SHX,cy=H/2+SHY,Rs=sc*RIN*(0.04+0.96*sg)*(1+0.025*Math.sin(t/260)),a=Math.min(1,0.4+0.6*sg)*K*(1-smooth(CE.ex));
 if(a<=0.01)return;
 ctx.setTransform(1,0,0,1,0,0);ctx.globalCompositeOperation='lighter';ctx.globalAlpha=1;
 let g=ctx.createRadialGradient(cx,cy,Rs*0.5,cx,cy,Rs*2.1);
 g.addColorStop(0,'rgba(255,120,175,'+(0.55*a).toFixed(3)+')');g.addColorStop(1,'rgba(255,60,120,0)');
 ctx.fillStyle=g;ctx.fillRect(cx-Rs*2.2,cy-Rs*2.2,Rs*4.4,Rs*4.4);
 g=ctx.createRadialGradient(cx-Rs*0.28,cy-Rs*0.3,0,cx,cy,Rs);
 g.addColorStop(0,'rgba(255,255,255,'+a.toFixed(3)+')');g.addColorStop(0.45,'rgba(255,215,228,'+(0.92*a).toFixed(3)+')');
 g.addColorStop(0.85,'rgba(255,115,165,'+(0.78*a).toFixed(3)+')');g.addColorStop(1,'rgba(255,70,130,'+(0.5*a).toFixed(3)+')');
 ctx.fillStyle=g;ctx.beginPath();ctx.arc(cx,cy,Rs,0,Math.PI*2);ctx.fill();
 ctx.globalCompositeOperation='source-over'}
function horizonDraw(sc,W,H,t){
 if(CE.hg>0.002){
  const cx=W/2+SHX,cy=H/2+SHY,Rh=sc*RIN*(0.04+0.96*CE.hg)*(1-0.9*CE.hf),fa=1-CE.hf,rt=t*0.00018,cg=smooth(Math.max(0,Math.min(1,(CE.hg-0.1)/0.65)));
  ctx.globalCompositeOperation='lighter';
  let g=ctx.createRadialGradient(cx,cy,Rh,cx,cy,Rh*2.5);
  g.addColorStop(0,'rgba(255,215,150,'+(0.9*fa*cg).toFixed(3)+')');g.addColorStop(0.1,'rgba(255,160,85,'+(0.6*fa*cg).toFixed(3)+')');
  g.addColorStop(0.4,'rgba(255,95,55,'+(0.2*fa*cg).toFixed(3)+')');g.addColorStop(1,'rgba(255,60,60,0)');
  ctx.fillStyle=g;ctx.fillRect(cx-Rh*2.6,cy-Rh*2.6,Rh*5.2,Rh*5.2);
  // rayons de la couronne
  for(let k=0;k<42;k++){const an=k*Math.PI*2/42+rt*(k%2?1:-1),hh=Math.abs((Math.sin(k*12.9898)*43758.5453)%1),
    ln=Rh*(0.18+0.85*hh)*(0.75+0.25*Math.sin(t/260+k*1.7)),c=Math.cos(an),sn=Math.sin(an);
   const gr=ctx.createLinearGradient(cx+c*Rh,cy+sn*Rh,cx+c*(Rh+ln),cy+sn*(Rh+ln));
   gr.addColorStop(0,'rgba(255,225,170,'+(0.7*fa*cg).toFixed(3)+')');gr.addColorStop(1,'rgba(255,120,60,0)');
   ctx.strokeStyle=gr;ctx.lineWidth=Math.max(1,Rh*(0.008+0.012*hh));ctx.beginPath();ctx.moveTo(cx+c*Rh,cy+sn*Rh);ctx.lineTo(cx+c*(Rh+ln),cy+sn*(Rh+ln));ctx.stroke()}
  ctx.globalCompositeOperation='source-over';
  ctx.fillStyle='rgba(2,0,5,'+Math.min(1,fa).toFixed(3)+')';ctx.beginPath();ctx.arc(cx,cy,Rh,0,Math.PI*2);ctx.fill();
  // anneau de photons + côté plus brillant (effet Doppler)
  ctx.lineWidth=Math.max(2,Rh*0.045);ctx.strokeStyle='rgba(255,240,215,'+(fa*cg).toFixed(3)+')';ctx.shadowColor='rgba(255,150,70,1)';ctx.shadowBlur=Rh*0.3;
  ctx.beginPath();ctx.arc(cx,cy,Rh*1.02,0,Math.PI*2);ctx.stroke();
  ctx.lineWidth=Math.max(3,Rh*0.1);ctx.strokeStyle='rgba(255,250,235,'+(0.9*fa*cg).toFixed(3)+')';
  ctx.beginPath();ctx.arc(cx,cy,Rh*1.05,Math.PI*0.62,Math.PI*1.38);ctx.stroke();ctx.shadowBlur=0;
  for(let k=0;k<3;k++){const ph=((t/1500)+k/3)%1;ctx.lineWidth=Math.max(1,W/500);ctx.strokeStyle='rgba(255,190,150,'+(0.35*(1-ph)*cg*fa).toFixed(3)+')';ctx.beginPath();ctx.arc(cx,cy,Rh*(1.1+ph*1.8),0,Math.PI*2);ctx.stroke()}
  if(CE.hf>0.01){ctx.lineWidth=Math.max(2,W/300);ctx.strokeStyle='rgba(255,225,190,'+(0.7*(1-CE.hf)).toFixed(3)+')';ctx.beginPath();ctx.arc(cx,cy,Rh+CE.hf*W*0.75,0,Math.PI*2);ctx.stroke()}
 }
}
function waveF(pi,t){const a=t/2600,ax=[Math.cos(a),0.35,Math.sin(a)],n=NU[pi],pr=n[0]*ax[0]+n[1]*ax[1]+n[2]*ax[2],w=0.5+0.5*Math.sin(pr*3.4-t/650);return 0.28+0.72*w*w}
function perim(s){s=((s%5)+5)%5;const e=Math.floor(s),f=s-e,a=pent[e%5],b=pent[(e+1)%5];return[a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f]}
const CYCLE=14;
const smooth=x=>x<=0?0:x>=1?1:x*x*(3-2*x);
function instances(t){
 const root={A:I3,T:[0,0,0],s:1,anc:[]},list=[root],f=copyK;
 if(mode==='f1'||mode==='f2'){
  for(const d of VDIR){const T1=d.map(x=>x*(1-f)),c1={A:I3,T:T1,s:f,anc:[root]};list.push(c1);
   if(mode==='f2')for(const d2 of VDIR)list.push({A:I3,T:[T1[0]+d2[0]*f*(1-f),T1[1]+d2[1]*f*(1-f),T1[2]+d2[2]*f*(1-f)],s:f*f,anc:[root,c1]});}
 }else if(mode==='cine'&&CE){
  if(CE.t>10.5)VDIR.forEach((d,i)=>{const u=Math.max(0,Math.min(1,(CE.t-10.5-i*0.09)/0.8)),e=smooth(u);if(e<=0)return;
   const T1=d.map(x=>x*(1-0.38)*(1+CE.ex*2.2));list.push({A:axisRot([0.3,1,0.2],CE.ex*3),T:T1,s:0.38*e,anc:[root],al:1-smooth(CE.ex)})});
 }else if(mode==='sat'){
  const P=((t/1000)%CYCLE)/CYCLE,Q=Math.max(0,Math.min(1,(P-0.12)/0.76)),e=smooth(Q),bump=Math.sin(Math.PI*e)**2;
  VDIR.forEach((d,i)=>{const r=1+0.9*orbitK*bump,k=(i%2?1:-1)*(1+(i%3));
   const ax=(i%2)?[0,1,0]:[0.45,0.85,0.27],Rg=axisRot(ax,2*Math.PI*k*e);
   const base=d.map(x=>x*(1-f)*r),Tp=mv(Rg,base);
   list.push({A:axisRot([0.3,1,0.2],4*Math.PI*e),T:Tp,s:f,anc:[root]});});
  info.textContent=bump>0.02?(Q<0.5?'Les satellites partent en orbite…':'Les satellites se rassemblent…'):'Rassemblés : fractale niveau 1';
 }
 return list;
}
function draw(t){
 const W=cv.width,H=cv.height;
 CE=null;DG=null;SHX=SHY=0;
 if(mode==='cine'){
  if(!T0)T0=t;let ct=(t-T0)/1000;if(ct>50){T0=t;ct=0;sndStart()}else if(ct>40){ct=40;if(SND&&SND.chain)sndStop()}
  const sm=smooth,ex=sm(Math.max(0,Math.min(1,(ct-23.5)/6.5))),pk=Math.max(0,Math.min(1,(ct-22)/3.6));
  const hg=sm(Math.max(0,Math.min(1,(ct-20.5)/7))),hf=sm(Math.max(0,Math.min(1,(ct-29)/3)));
  CE={t:ct,ex,pk,hg,hf,glow:(0.35+0.65*Math.min(1,ct/9))*(1+0.9*pk*pk)*(1-ex)};
  const sg=sm(Math.max(0,Math.min(1,(ct-10.5)/13.5)));DG=sg;CE.sg=sg;
  yaw=0.4+ct*0.1;pitch=0.4-0.2*sm(ct/25);zoom=0.85+0.4*sm(ct/25);
  
  info.textContent=ct<3?'Éveil…':ct<10.5?'Le dodécaèdre se dessine':ct<24?'La sphère grandit, les dragons se forment':ct<27?'L’espace-temps se déchire…':'Horizon des événements';
 }if(gl.width!==W||gl.height!==H){gl.width=W;gl.height=H}
 const g=ctx.createRadialGradient(W/2,H/2,0,W/2,H/2,Math.max(W,H)*.7);g.addColorStop(0,'#1d0d26');g.addColorStop(1,'#07040c');
 ctx.setTransform(1,0,0,1,0,0);ctx.globalCompositeOperation='source-over';ctx.filter='none';ctx.globalAlpha=1;ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
 if(ready<2)return;
 gx.setTransform(1,0,0,1,0,0);gx.clearRect(0,0,W,H);
 ctx.imageSmoothingEnabled=false;gx.imageSmoothingEnabled=false;
 const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
 const Ry=[[cy,0,sy],[0,1,0],[-sy,0,cy]],Rx=[[1,0,0],[0,cp,-sp],[0,sp,cp]],V=mm(Rx,Ry);
 const extent=mode==='sat'?(1+0.9*orbitK)*1.25:1.0,sc=Math.min(W,H)/(2.7*L)*zoom/(mode==='simple'?1:(mode==='sat'?1.45:mode==='dragon'?2.3:mode==='cine'?2.0:1.25)),ox=W/2+SHX,oy=H/2+SHY,light=[0.4,0.75,0.55],ll=Math.hypot(...light);
 if(CE)sphereDraw(V,sc,W,H,t,1);
 const DR=(mode==='dragon'||(mode==='cine'&&DG>0))?dragonProj(t,V,sc,W,H):null;ctx.setTransform(1,0,0,1,0,0);if(DR)strokeDragon(DR,-1,W);
 const draws=[];
 const inside=(pt,a)=>{if(!a.NW)a.NW=NORM.map(n=>mv(a.A,n));for(const n of a.NW){if((pt[0]-a.T[0])*n[0]+(pt[1]-a.T[1])*n[1]+(pt[2]-a.T[2])*n[2]>a.s*RIN-0.05)return false}return true};
 for(const ins of instances(t)){
  const VA=mm(V,ins.A),Tv=mv(V,ins.T);
  for(const [pi,p] of PL.entries()){
   if(ins.anc.length){const wl=mv(ins.A,p.c),wc=[ins.T[0]+wl[0]*ins.s,ins.T[1]+wl[1]*ins.s,ins.T[2]+wl[2]*ins.s];if(ins.anc.some(a=>inside(wc,a)))continue}
   const R=mm(VA,p.R),n=[R[0][1],R[1][1],R[2][1]];if(n[2]<=0&&!(TRANSL&&!ins.anc.length))continue;
   let pcs=1,al=ins.al===undefined?1:ins.al;
   let og=0,ola=0;
   if(CE&&!ins.anc.length){const u=Math.max(0,Math.min(1,(CE.t-3-pi*0.5)/2.2)),e=smooth(Math.max(0,Math.min(1,(u-0.55)/0.45)));og=Math.min(1,u/0.65);pcs=1+CE.ex*1.6;al=e*(1-smooth(CE.ex));ola=og>0?(1-0.75*e)*(1-smooth(CE.ex)):0}
   if(al<0.01&&og<=0)continue;
   const pc=mv(VA,p.c),c=[Tv[0]+pc[0]*ins.s*pcs,Tv[1]+pc[1]*ins.s*pcs,Tv[2]+pc[2]*ins.s*pcs];
   draws.push({z:c[2],c,R,n,s:ins.s,uv:p.uv,a:al,o:og,ola:ola,pi,root:!ins.anc.length,back:n[2]<=0});
  }
 }
 draws.sort((a,b)=>a.z-b.z);
 for(const q of draws){
  const R=q.R,X=[R[0][0],R[1][0],R[2][0]],Z=[R[0][2],R[1][2],R[2][2]],Ls=L*q.s,c=q.c;
  const px=c[0]-X[0]*Ls/2-Z[0]*Ls/2,py=c[1]-X[1]*Ls/2-Z[1]*Ls/2,k=Ls/T;
  const set=(c2)=>c2.setTransform(sc*X[0]*k,-sc*X[1]*k,sc*Z[0]*k,-sc*Z[1]*k,ox+sc*px,oy-sc*py);
  const sh=0.35+0.65*Math.max(0,(q.n[0]*light[0]+q.n[1]*light[1]+q.n[2]*light[2])/ll);
  ctx.globalAlpha=q.a;set(ctx);ctx.drawImage(tex,q.uv[0],q.uv[1],T,T,0,0,T,T);
  ctx.beginPath();pent.forEach((v,i)=>i?ctx.lineTo(v[0],v[1]):ctx.moveTo(v[0],v[1]));ctx.closePath();
  ctx.fillStyle='rgba(8,3,14,'+(1-sh).toFixed(3)+')';ctx.fill();ctx.globalAlpha=1;
  if(q.o>0&&q.ola>0.01){set(ctx);const tot=q.o*5,full=Math.floor(tot),fr=tot-full;ctx.beginPath();ctx.moveTo(pent[0][0],pent[0][1]);
   for(let k=1;k<=Math.min(full,5);k++)ctx.lineTo(pent[k%5][0],pent[k%5][1]);
   if(full<5){const a=pent[full%5],b=pent[(full+1)%5];ctx.lineTo(a[0]+(b[0]-a[0])*fr,a[1]+(b[1]-a[1])*fr)}
   ctx.lineWidth=2.4;ctx.lineJoin='round';ctx.strokeStyle='rgba(255,240,215,'+q.ola.toFixed(3)+')';ctx.shadowColor='rgba(255,170,90,0.95)';ctx.shadowBlur=8;ctx.stroke();ctx.shadowBlur=0}
  if(PULSE&&q.root&&!q.back&&q.a>0.6){set(ctx);const hd=(((t/2200)+q.pi*0.173)%1)*5,TR=0.9,NS=9;
   for(let j=0;j<NS;j++){const A=perim(hd-TR+TR*j/NS),B=perim(hd-TR+TR*(j+1)/NS);ctx.beginPath();ctx.moveTo(A[0],A[1]);ctx.lineTo(B[0],B[1]);
    ctx.lineWidth=2.6;ctx.strokeStyle='rgba(255,236,225,'+(0.95*Math.pow((j+1)/NS,1.6)*q.a).toFixed(3)+')';ctx.shadowColor='rgba(255,120,150,0.9)';ctx.shadowBlur=7;ctx.stroke()}
   ctx.shadowBlur=0}
  set(gx);gx.globalAlpha=q.a*(0.4+0.6*Math.min(1,q.s*2.5))*((PULSE&&q.root)?waveF(q.pi,t):1);gx.drawImage(glow,q.uv[0],q.uv[1],T,T,0,0,T,T);
 }
 ctx.setTransform(1,0,0,1,0,0);if(CE)horizonDraw(sc,W,H,t);if(DR)strokeDragon(DR,1,W);
 if(CE)sphereDraw(V,sc,W,H,t,0.3*(1-CE.hg));
 const pulse=(0.88+0.12*Math.sin(t/500))*glowK*(CE?CE.glow*(1+0.6*CE.sg):1);
 ctx.setTransform(1,0,0,1,0,0);ctx.globalCompositeOperation='lighter';
 ctx.globalAlpha=Math.min(1,pulse);ctx.drawImage(gl,0,0);
 ctx.filter='blur('+Math.round(W/160)+'px)';ctx.globalAlpha=Math.min(1,0.85*pulse);ctx.drawImage(gl,0,0);
 ctx.filter='blur('+Math.round(W/60)+'px)';ctx.globalAlpha=Math.min(1,0.5*pulse);ctx.drawImage(gl,0,0);
 ctx.globalAlpha=1;ctx.filter='none';ctx.globalCompositeOperation='source-over';
 if(CE)cineFx(V,sc,W,H,t);
}
function cineFx(V,sc,W,H,t){
 const R0=RIN*3.2,n=170;ctx.globalCompositeOperation='lighter';
 for(let i=0;i<n;i++){
  const h=Math.abs((Math.sin(i*127.1)*43758.5453)%1),h2=Math.abs((Math.sin(i*311.7)*43758.5453)%1),h3=Math.abs((Math.sin(i*74.7)*43758.5453)%1);
  const a1=h*Math.PI*2,z=h2*2-1,rr=Math.sqrt(1-z*z),dx=rr*Math.cos(a1),dz=rr*Math.sin(a1),dy=z;let r,al;
  if(CE.t<29){const ph=(CE.t*0.12+h3)%1;r=R0*(1-ph)+RIN*0.6;al=Math.sin(Math.PI*ph)*Math.min(1,CE.t/2)*(1-CE.hf)}
  else{r=RIN*(1.2+CE.ex*5.5)*(0.6+h3*0.6);al=1-CE.ex}
  if(al<=0.01)continue;
  const m=mv(V,[dx*r,dy*r,dz*r]),s=Math.max(1.5,W/600);ctx.globalAlpha=Math.min(1,al*0.9);ctx.fillStyle='rgb(255,190,130)';
  ctx.fillRect(W/2+SHX+sc*m[0],H/2+SHY-sc*m[1],s,s)}
 ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';

}

const LITE=+(new URLSearchParams(location.search).get('lite')||2);
const MASTER=0.8, MAKEUP_GAIN=0.9, PHONE_GAIN=0.6, PHONE_KEY='dodeca-phone-mode';
let NOSND=false,MUTE=false,SND=null,phoneMode=false;
try{phoneMode=localStorage.getItem(PHONE_KEY)==='1'}catch(e){}
const phoneButton=document.getElementById('phone');
function updatePhoneButton(){
 phoneButton.setAttribute('aria-pressed',String(phoneMode));
 phoneButton.textContent='Mode téléphone : '+(phoneMode?'activé':'désactivé');
}
updatePhoneButton();
phoneButton.addEventListener('click',()=>{
 phoneMode=!phoneMode;
 updatePhoneButton();
 try{localStorage.setItem(PHONE_KEY,phoneMode?'1':'0')}catch(e){}
 if(SND&&SND.chain){
  const {hp,mk}=SND.chain,t=SND.ctx.currentTime;
  // Ajuste la sortie sans toucher à l’enveloppe de la cinématique.
  hp.frequency.setTargetAtTime(phoneMode?150:85,t,0.02);
  mk.gain.setTargetAtTime(MAKEUP_GAIN*(phoneMode?PHONE_GAIN:1),t,0.02);
 }
});
function masterChain(c,out){const bus=c.createGain(),hp=c.createBiquadFilter(),cp=c.createDynamicsCompressor(),mk=c.createGain();
 hp.type='highpass';hp.frequency.value=phoneMode?150:85;hp.Q.value=0.7;
 const MIX=new URLSearchParams(location.search).get('mix')||'';
 cp.threshold.value=-20;cp.knee.value=10;cp.ratio.value=14;cp.attack.value=0.003;cp.release.value=0.25;
 if(MIX==='2'){cp.threshold.value=-12;cp.knee.value=24;cp.ratio.value=3;cp.attack.value=0.02;cp.release.value=0.3}
 mk.gain.value=MAKEUP_GAIN*(phoneMode?PHONE_GAIN:1);
 bus.connect(hp);if(MIX==='1'){hp.connect(mk)}else{hp.connect(cp);cp.connect(mk)}mk.connect(out);return {bus,hp,mk}}
function mkNoise(actx){const len=actx.sampleRate*2,b=actx.createBuffer(1,len,actx.sampleRate),d=b.getChannelData(0);let q=12345;for(let i=0;i<len;i++){q=(q*1664525+1013904223)>>>0;d[i]=(q/4294967296)*2-1}return b}
function buildSound(actx,dest,t0){
 const noise=mkNoise(actx);let sd=777;const rnd=()=>{sd=(sd*1664525+1013904223)>>>0;return sd/4294967296};
 function osc(type,f0,f1,ta,tb,vol,att,rel,out){const o=actx.createOscillator(),gn=actx.createGain();o.type=type;
  o.frequency.setValueAtTime(f0,t0+ta);if(f1!==f0)o.frequency.exponentialRampToValueAtTime(f1,t0+tb);
  const ta2=t0+ta+att,tr=Math.max(ta2,t0+tb-rel);
  gn.gain.setValueAtTime(0.0001,t0+ta);gn.gain.linearRampToValueAtTime(vol,ta2);gn.gain.setValueAtTime(vol,tr);gn.gain.linearRampToValueAtTime(0.0001,t0+tb);
  o.connect(gn);gn.connect(out||dest);o.start(t0+ta);o.stop(t0+tb+0.05)}
 function burst(ta,dur,ft,f0,f1,vol,Q,out){const src=actx.createBufferSource(),fl=actx.createBiquadFilter(),gn=actx.createGain();src.buffer=noise;fl.type=ft;fl.Q.value=Q||1;
  fl.frequency.setValueAtTime(f0,t0+ta);if(f1!==f0)fl.frequency.exponentialRampToValueAtTime(f1,t0+ta+dur);
  gn.gain.setValueAtTime(vol,t0+ta);gn.gain.exponentialRampToValueAtTime(0.0001,t0+ta+dur);
  src.connect(fl);fl.connect(gn);gn.connect(out||dest);src.start(t0+ta,rnd()*1.5);src.stop(t0+ta+dur+0.05)}
const rv=actx.createConvolver(),LN=Math.round(actx.sampleRate*(LITE>=2?1.5:4)),ir=actx.createBuffer(2,LN,actx.sampleRate);
 for(let ch=0;ch<2;ch++){const d=ir.getChannelData(ch);for(let i=0;i<LN;i++)d[i]=(rnd()*2-1)*Math.pow(1-i/LN,2.4)}
 rv.buffer=ir;const wet=actx.createGain();wet.gain.value=0.75;rv.connect(wet);wet.connect(dest);
 const sx=actx.createGain();sx.connect(dest);sx.connect(rv);
 const pan=v=>{const p=actx.createStereoPanner();p.pan.value=v;p.connect(sx);return p};
 // 0-3 s : nappe aérienne
 osc('sine',110,110,0,14,0.05,3,3);osc('sine',164.8,164.8,0,14,0.03,4,3);
 // 3-10,5 s : un tintement cristallin à chaque pentagone tracé
 const N=[110,146.8,164.8,196,220,261.6,293.7,329.6,392,440,523.3,587.3];
 // (notes par pentagone retirées pour le moment)
 // 10,5-26 s : bourdon qui monte avec la sphère
 const lp=actx.createBiquadFilter();lp.type='lowpass';lp.frequency.setValueAtTime(180,t0+10.5);lp.frequency.exponentialRampToValueAtTime(3000,t0+26);lp.connect(dest);
 osc('sawtooth',55,55,10.5,29,0.15,4,3,lp);osc('sawtooth',55.6,55.6,10.5,29,0.13,4,3,lp);
 osc('sine',110,440,10.5,26,0.12,3,3);osc('sine',1760,3520,14,26,0.014,4,3);
 // crépitement des dragons (plus dense avec le temps)
 for(let k=0;k<150;k++){const ta=12.5+Math.pow(rnd(),0.6)*14.5;burst(ta,0.04,'bandpass',3000+rnd()*3000,3000+rnd()*3000,0.07*(0.3+0.7*Math.min(1,(ta-12)/14)),4)}
 // trou noir : grave profond + souffle montant
 osc('sine',46,30,20.5,36,0.3,5,8);
 {const src=actx.createBufferSource(),fl=actx.createBiquadFilter(),gn=actx.createGain();src.buffer=noise;src.loop=true;fl.type='lowpass';
  fl.frequency.setValueAtTime(200,t0+22);fl.frequency.exponentialRampToValueAtTime(5000,t0+27.5);
  gn.gain.setValueAtTime(0.0001,t0+22);gn.gain.linearRampToValueAtTime(0.22,t0+27.5);gn.gain.linearRampToValueAtTime(0.0001,t0+29.5);
  src.connect(fl);fl.connect(gn);gn.connect(dest);src.start(t0+22);src.stop(t0+29.6)}
 // onde de choc à 28,6 s
 osc('sine',70,26,28.6,34,0.5,0.02,4.5);burst(28.6,3.5,'lowpass',900,150,0.35,1);
 // ===== ouverture stellaire du trou noir (26 s) puis dissipation =====
 {
  {const src=actx.createBufferSource(),fl=actx.createBiquadFilter(),gn=actx.createGain();src.buffer=noise;src.loop=true;fl.type='highpass';
   fl.frequency.setValueAtTime(500,t0+24.9);fl.frequency.exponentialRampToValueAtTime(9000,t0+26);
   gn.gain.setValueAtTime(0.0001,t0+24.9);gn.gain.exponentialRampToValueAtTime(0.3,t0+25.98);gn.gain.setValueAtTime(0.0001,t0+26.02);
   src.connect(fl);fl.connect(gn);gn.connect(sx);src.start(t0+24.9);src.stop(t0+26.05)}
  osc('sine',62,22,26,32,0.55,0.01,5.5);burst(26,2.6,'lowpass',1400,90,0.4,1);
  [880,1318.5,1760].forEach((f,i)=>osc('sine',f,f,26,35,0.012,1.2,6,pan(-0.6+i*0.6)));
  [1,1.5,2,3,4.5].forEach((r,i)=>osc('sine',110*r,110*r,26,36,0.05,0.5,8,pan(i%2?0.6:-0.6)));
  osc('sine',2400,300,29,36.5,0.07,0.1,5,pan(0));osc('sine',3600,450,29.2,36.5,0.04,0.1,5,pan(0.5));
  for(let k=0;k<40;k++){const ta=29+rnd()*6,f=2000+rnd()*6000;osc('sine',f,f,ta,ta+1.2,0.03*(1-(ta-29)/7),0.004,1.1,pan(rnd()*2-1))}
 }
 // craquements à l'apparition des fractales (10,5-12,5 s)
 for(let i=0;i<20;i++){const ta=10.5+i*0.09+rnd()*0.03,pn=pan(rnd()*2-1);burst(ta,0.14,'bandpass',2600+rnd()*1800,500,0.22,3,pn);osc('sine',1100+rnd()*600,180,ta,ta+0.06,0.06,0.001,0.05,pn)}
 burst(10.4,0.5,'lowpass',500,90,0.18,1);
 // cristal qui se brise quand les faces se séparent (25,7-27,6 s)
 burst(25.7,0.35,'highpass',900,900,0.4,0.7,sx);burst(25.72,0.12,'bandpass',4200,1500,0.35,2,sx);
 for(let k=0;k<70;k++){const ta=25.85+Math.pow(rnd(),1.6)*1.9,f=3500+rnd()*5500,pn=pan(rnd()*2-1);burst(ta,0.03+rnd()*0.09,'bandpass',f,f*0.6,0.16*(1-(ta-25.8)/2.6),6,pn);if(k%3===0)osc('sine',f,f*0.8,ta,ta+0.1,0.02,0.001,0.09,pn)}
}
function sndStart(){
 if(NOSND||MUTE)return;
 try{if(!SND)SND={ctx:new (window.AudioContext||window.webkitAudioContext)(LITE>=1?{latencyHint:'playback'}:undefined)};const c=SND.ctx;c.resume();
  if(SND.chain){const b=SND.chain.bus;b.gain.setTargetAtTime(0,c.currentTime,0.05);setTimeout(()=>{try{b.disconnect()}catch(e){}},500)}
  const t0=c.currentTime+0.05,chain=masterChain(c,c.destination),{bus}=chain;bus.gain.setValueAtTime(MASTER,t0);bus.gain.setValueAtTime(MASTER,t0+38);bus.gain.linearRampToValueAtTime(0.0001,t0+40);
  SND.chain=chain;buildSound(c,bus,t0)}catch(e){}
}
function sndStop(){try{if(SND&&SND.chain){const b=SND.chain.bus;b.gain.setTargetAtTime(0,SND.ctx.currentTime,0.05);SND.chain=null;setTimeout(()=>{try{b.disconnect()}catch(e){}},500)}}catch(e){}}
async function renderAudioWav(){
 const sr=44100,oc=new OfflineAudioContext(2,sr*40,sr),{bus}=masterChain(oc,oc.destination);
 bus.gain.setValueAtTime(MASTER,0);bus.gain.setValueAtTime(MASTER,38);bus.gain.linearRampToValueAtTime(0.0001,40);buildSound(oc,bus,0);
 const buf=await oc.startRendering(),L=buf.getChannelData(0),R=buf.getChannelData(1),n=L.length,dv=new DataView(new ArrayBuffer(44+n*4));
 const ws=(o,t)=>{for(let i=0;i<t.length;i++)dv.setUint8(o+i,t.charCodeAt(i))};
 ws(0,'RIFF');dv.setUint32(4,36+n*4,true);ws(8,'WAVEfmt ');dv.setUint32(16,16,true);dv.setUint16(20,1,true);dv.setUint16(22,2,true);dv.setUint32(24,sr,true);dv.setUint32(28,sr*4,true);dv.setUint16(32,4,true);dv.setUint16(34,16,true);ws(36,'data');dv.setUint32(40,n*4,true);
 for(let i=0;i<n;i++){dv.setInt16(44+i*4,Math.max(-1,Math.min(1,L[i]))*32767,true);dv.setInt16(46+i*4,Math.max(-1,Math.min(1,R[i]))*32767,true)}
 const u=new Uint8Array(dv.buffer);let bin='';for(let i=0;i<u.length;i+=8192)bin+=String.fromCharCode.apply(null,u.subarray(i,i+8192));return btoa(bin)}
window.__nosnd=()=>{NOSND=true};window.__audio=renderAudioWav;
function updIter(){document.getElementById('itv').textContent=ITER;document.getElementById('itinfo').textContent='Itérations du dragon : '+ITER+' → '+(Math.pow(2,ITER)).toLocaleString('fr-FR')+' segments par courbe'}
let FT=null;let last=0;function loop(t){if(auto&&!drag)yaw+=(t-last)/2600;last=t;draw(FT===null?t:FT);requestAnimationFrame(loop)}requestAnimationFrame(loop);
cv.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY];cv.setPointerCapture(e.pointerId)});
cv.addEventListener('pointermove',e=>{if(!drag)return;yaw+=(e.clientX-drag[0])/180;pitch=Math.max(-1.5,Math.min(1.5,pitch+(e.clientY-drag[1])/180));drag=[e.clientX,e.clientY]});
cv.addEventListener('pointerup',()=>drag=null);
cv.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.4,Math.min(3,zoom*(e.deltaY<0?1.08:.92)))},{passive:false});
for(const b of document.querySelectorAll('[data-mode]'))b.addEventListener('click',()=>{mode=b.dataset.mode;if(mode==='cine'){T0=0;auto=false;sndStart()}else sndStop();
 document.querySelectorAll('[data-mode]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
 info.textContent=mode==='f1'?'Fractale niveau 1 : 20 copies aux sommets':mode==='f2'?'Fractale niveau 2 : 420 copies':mode==='dragon'?'Courbes du dragon de Heighway : 8 courbes qui se déplient depuis les sommets':mode==='simple'?'':info.textContent});
const tg=(id,fn)=>document.getElementById(id).addEventListener('click',ev=>{const b=ev.currentTarget,v=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',String(v));fn(v)});
tg('auto',v=>auto=v);tg('snd',v=>{MUTE=!v;if(MUTE)sndStop();else if(mode==='cine'){T0=0;sndStart()}});tg('pulse',v=>PULSE=v);tg('back',v=>TRANSL=v);tg('flip',v=>{flip=v;buildPlates();buildNorm();NU=NORM.map(n=>{const l=Math.hypot(...n);return n.map(x=>x/l)})});
document.getElementById('glow').addEventListener('input',e=>glowK=e.target.value/100);
document.getElementById('copy').addEventListener('input',e=>copyK=e.target.value/100);
document.getElementById('iter').addEventListener('input',e=>{ITER=+e.target.value;updIter()});updIter();
document.getElementById('orbit').addEventListener('input',e=>orbitK=e.target.value/100);
window.__frame=ct=>{T0=1000;FT=1000+ct*1000;return new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(cv.toDataURL('image/jpeg',0.95)))))};
window.__cine=ct=>{T0=performance.now()-ct*1000};
window.__setView=(y,p)=>{yaw=y;pitch=p;auto=false};
window.__setMode=m=>document.querySelector('[data-mode="'+m+'"]').click();
</script></body></html>"""
out = os.path.join(HERE, "dodeca_viewer.html")
open(out, "w", encoding="utf-8").write(HTML.replace("__DATA__", json.dumps(data)))
print("Ecrit :", out)
if os.environ.get("NO_OPEN") != "1":
    webbrowser.open("file://" + out)
