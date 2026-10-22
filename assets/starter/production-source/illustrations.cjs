'use strict';
// Text uses darker companion inks; object accents retain the reference-family hues.
// Original parameterized drawing vocabulary. All glyphs/labels register with the supplied motion stage.
// These conventional forms are seeds for subject illustration, not a universal course world.
// People with faces: figure() draws a full person, and a course defines its recurring people once
// with defineCast() and stages them with cast(), so the same person looks the same in every lesson.
// Glyph-internal lettering (a document's ID, a revision) is tertiary text on a design stage (24 px floor),
// so a lettered document needs s >= 1.4 there; below that its title and revision collide and the audit says so.
const P={bg:'#f5f2e9',paper:'#fffefa',ink:'#17353d',muted:'#59767b',line:'#bfd0ca',teal:'#087e79',mint:'#c8e7d8',blue:'#376ec3',pale:'#dce8f7',gold:'#d99a31',sand:'#f8e4bd',red:'#b8513b',rose:'#f2dbd1',purple:'#786499'};
const clamp=x=>Math.max(0,Math.min(1,x)),mix=(a,b,p)=>a+(b-a)*p,smooth=x=>{x=clamp(x);return x*x*(3-2*x)},between=(t,a,b)=>smooth((t-a)/(b-a));
function context(g,stage=null){const registry=[];
 const bounds=(x,y,w,h)=>{const m=g.getTransform();return{x:x*m.a+m.e,y:y*m.d+m.f,w:w*Math.abs(m.a),h:h*Math.abs(m.d)}};
 function body(id,x,y,w,h,fn){if(stage){stage.actor(id,{x,y,w,h},fn);return;}g.save();fn();g.restore();registry.push({id,kind:'body',alpha:g.globalAlpha,bounds:bounds(x,y,w,h)});}
 function text(id,value,x,y,{size=20,color=P.ink,align='center',weight=600,owner=null,region='world',alpha=1,allow=[],tier}={}){if(alpha<=0)return;if(stage){g.save();g.globalAlpha*=alpha;stage.label(id,value,x,y,{size,color:({[P.teal]:'#08635f',[P.gold]:'#795117',[P.blue]:'#2b5da7',[P.red]:'#9a402e',[P.muted]:'#526d72'})[color]||color,align,weight,owner,...(tier?{tier}:{})});g.restore();return;}g.save();g.globalAlpha*=alpha;g.font=`${weight} ${size}px Arial`;g.textAlign=align;g.textBaseline='middle';const w=g.measureText(String(value)).width;g.fillStyle=({[P.teal]:'#08635f',[P.gold]:'#795117',[P.blue]:'#2b5da7',[P.red]:'#9a402e',[P.muted]:'#526d72'})[color]||color;g.fillText(String(value),x,y);const xx=x-(align==='center'?w/2:align==='right'?w:0);registry.push({id,kind:'text',owner,region,allow,alpha:g.globalAlpha,bounds:bounds(xx-2,y-size*.6,w+4,size*1.2)});g.restore();}
 function line(points,color=P.line,width=2,completion=1,dash=[]){if(completion<=0)return;const lengths=points.slice(1).map((p,i)=>Math.hypot(p[0]-points[i][0],p[1]-points[i][1])),total=lengths.reduce((a,b)=>a+b,0);let left=total*clamp(completion);g.save();g.strokeStyle=color;g.lineWidth=width;g.lineCap='round';g.lineJoin='round';g.setLineDash(dash);g.beginPath();g.moveTo(...points[0]);for(let i=0;i<lengths.length;i++){if(lengths[i]===0)continue;const p=Math.min(1,left/lengths[i]);g.lineTo(mix(points[i][0],points[i+1][0],p),mix(points[i][1],points[i+1][1],p));left-=lengths[i];if(left<=0)break;}g.stroke();g.restore();}
 function pointOn(points,p){const lengths=points.slice(1).map((v,i)=>Math.hypot(v[0]-points[i][0],v[1]-points[i][1])),total=lengths.reduce((a,b)=>a+b,0);let left=clamp(p)*total;for(let i=0;i<lengths.length;i++){if(lengths[i]===0)continue;if(left<=lengths[i])return[mix(points[i][0],points[i+1][0],left/lengths[i]),mix(points[i][1],points[i+1][1],left/lengths[i])];left-=lengths[i];}return points.at(-1);}
 function arrow(points,color=P.teal,width=2.5,completion=1){line(points,color,width,completion);if(completion<=0)return;const end=pointOn(points,completion),prior=pointOn(points,Math.max(0,completion-.025)),a=Math.atan2(end[1]-prior[1],end[0]-prior[0]);line([[end[0]-9*Math.cos(a-.55),end[1]-9*Math.sin(a-.55)],end,[end[0]-9*Math.cos(a+.55),end[1]-9*Math.sin(a+.55)]],color,width);}
 function rounded(x,y,w,h,fill=P.paper,stroke=P.ink,r=7){g.beginPath();g.roundRect(x,y,w,h,r);g.fillStyle=fill;g.fill();if(stroke){g.strokeStyle=stroke;g.lineWidth=1.8;g.stroke();}}
 function person(id,x,y,s=1,color=P.teal){body(id,x-27*s,y-46*s,54*s,92*s,()=>{g.fillStyle=color;g.beginPath();g.arc(x,y-28*s,15*s,0,Math.PI*2);g.fill();rounded(x-24*s,y-5*s,48*s,45*s,color,null,15*s);});}
 function document(id,x,y,s=1,{revision=null,color=P.teal,fill=P.paper,title='',stamp=true}={}){const w=58*s,h=78*s;body(id,x-w/2-1,y-h/2-1,w+2,h+2,()=>{g.fillStyle=fill;g.strokeStyle=P.ink;g.lineWidth=1.6;g.beginPath();g.moveTo(x-w/2,y-h/2);g.lineTo(x+w/2-13*s,y-h/2);g.lineTo(x+w/2,y-h/2+13*s);g.lineTo(x+w/2,y+h/2);g.lineTo(x-w/2,y+h/2);g.closePath();g.fill();g.stroke();line([[x+w/2-13*s,y-h/2],[x+w/2-13*s,y-h/2+13*s],[x+w/2,y-h/2+13*s]],P.ink,1.3);g.fillStyle=color;g.fillRect(x-w/2+5*s,y-h/2+8*s,w-25*s,5*s);line([[x-w/2+8*s,y-9*s],[x+w/2-8*s,y-9*s]],P.line,1.4);});if(title)text(id+'-title',title,x,y+5*s,{size:14*s,owner:id,tier:'tertiary'});if(revision!==null)text(id+'-revision','r'+revision,x,y+29*s,{size:14*s,color,owner:id,weight:700,tier:'tertiary'});}
 function browser(id,x,y,s=1,{revision=null,color=P.teal,fill=P.paper}={}){const w=132*s,h=98*s;body(id,x-w/2-1,y-h/2-1,w+2,h+2,()=>{rounded(x-w/2,y-h/2,w,h,fill,P.ink,6*s);line([[x-w/2,y-h/2+19*s],[x+w/2,y-h/2+19*s]],P.ink,1.4);for(let i=0;i<3;i++){g.fillStyle=[P.red,P.gold,P.teal][i];g.beginPath();g.arc(x-w/2+(12+i*11)*s,y-h/2+9*s,2*s,0,Math.PI*2);g.fill();}g.fillStyle=P.pale;g.fillRect(x-w/2+11*s,y-h/2+30*s,45*s,29*s);for(let i=0;i<3;i++)line([[x+3*s,y-15*s+i*10*s],[x+w/2-11*s,y-15*s+i*10*s]],i?P.line:P.ink,1.4);g.fillStyle=color;g.fillRect(x-w/2+11*s,y+h/2-31*s,(w-22*s)*.72,5*s);});if(revision!==null)text(id+'-revision','r'+revision,x,y+36*s,{size:16*s,color,owner:id,weight:700,tier:'tertiary'});}
 function monitor(id,x,y,s=1){body(id,x-80*s,y-55*s,160*s,130*s,()=>{rounded(x-78*s,y-53*s,156*s,102*s,P.paper,P.ink,7*s);g.fillStyle=P.pale;g.fillRect(x-66*s,y-42*s,132*s,15*s);g.fillStyle=P.mint;g.fillRect(x-64*s,y-17*s,48*s,42*s);for(let i=0;i<3;i++)line([[x-5*s,y-15*s+i*14*s],[x+62*s,y-15*s+i*14*s]],i?P.line:P.ink,2);line([[x,y+49*s],[x,y+69*s]],P.ink,3);line([[x-23*s,y+71*s],[x+23*s,y+71*s]],P.ink,3);});}
 function envelope(id,x,y,s=1,{open=0,color=P.teal}={}){body(id,x-76*s,y-65*s,152*s,119*s,()=>{g.fillStyle=P.sand;g.strokeStyle=P.ink;g.lineWidth=1.8;g.beginPath();g.moveTo(x-72*s,y-33*s);g.lineTo(x,y-(33+30*open)*s);g.lineTo(x+72*s,y-33*s);g.closePath();g.fill();g.stroke();rounded(x-60*s,y-47*s,120*s,80*s,P.paper,P.ink,3);g.fillStyle=P.pale;g.fillRect(x-48*s,y-36*s,96*s,13*s);for(let i=0;i<2;i++)line([[x-48*s,y-10*s+i*11*s],[x+48*s,y-10*s+i*11*s]],i?P.line:P.ink,1.5);g.fillStyle=P.paper;g.beginPath();g.moveTo(x-72*s,y-32*s);g.lineTo(x,y+17*s);g.lineTo(x+72*s,y-32*s);g.lineTo(x+72*s,y+47*s);g.lineTo(x-72*s,y+47*s);g.closePath();g.fill();g.stroke();line([[x-72*s,y+47*s],[x-21*s,y+3*s]],P.ink,1.5);line([[x+72*s,y+47*s],[x+21*s,y+3*s]],P.ink,1.5);g.fillStyle=color;g.fillRect(x-22*s,y+20*s,44*s,6*s);});}
 function building(id,x,y,s=1,{color=P.teal}={}){body(id,x-72*s,y-65*s,144*s,122*s,()=>{g.fillStyle=P.paper;g.strokeStyle=P.ink;g.lineWidth=1.8;g.beginPath();g.moveTo(x-66*s,y-32*s);g.lineTo(x,y-62*s);g.lineTo(x+66*s,y-32*s);g.closePath();g.fill();g.stroke();rounded(x-59*s,y-28*s,118*s,77*s,P.paper,P.ink,1);for(let k=0;k<3;k++){const xx=x+(k-1)*36*s;g.fillStyle=k===1?P.mint:P.pale;g.fillRect(xx-10*s,y-15*s,20*s,31*s);line([[xx-10*s,y-15*s],[xx-10*s,y+25*s],[xx+10*s,y+25*s],[xx+10*s,y-15*s]],P.ink,1.3);}g.fillStyle=color;g.fillRect(x-13*s,y+17*s,26*s,32*s);line([[x-69*s,y+51*s],[x+69*s,y+51*s]],P.ink,3);});}
 function phone(id,x,y,s=1,{revision=0,time='—',color=P.teal,title='Article',articleId=''}={}){const w=110*s,h=204*s;body(id,x-w/2-1,y-h/2-1,w+2,h+2,()=>{rounded(x-w/2,y-h/2,w,h,P.ink,P.ink,13*s);rounded(x-w/2+5*s,y-h/2+12*s,w-10*s,h-25*s,P.paper,null,9*s);rounded(x-15*s,y-h/2+5*s,30*s,3*s,P.muted,null,1);g.fillStyle=P.pale;g.fillRect(x-w/2+15*s,y-48*s,w-30*s,27*s);line([[x-w/2+15*s,y-10*s],[x+w/2-15*s,y-10*s]],P.ink,2);line([[x-w/2+15*s,y+3*s],[x+w/2-25*s,y+3*s]],P.line,2);g.fillStyle=color;g.fillRect(x-w/2+14*s,y+17*s,w-28*s,33*s);});text(id+'-headline',title,x,y-70*s,{size:14*s,owner:id,tier:'tertiary'});text(id+'-time',time,x,y+34*s,{size:20*s,color:P.paper,owner:id,weight:700,tier:'tertiary'});text(id+'-article',(articleId?articleId+' · ':'')+'r'+revision,x,y+74*s,{size:14*s,owner:id,color:P.muted,tier:'tertiary'});}
 function clock(id,x,y,s=1,hand=.1,color=P.gold){body(id,x-25*s,y-25*s,50*s,50*s,()=>{g.strokeStyle=color;g.lineWidth=2.5;g.beginPath();g.arc(x,y,23*s,0,Math.PI*2);g.stroke();line([[x,y-14*s],[x,y],[x+14*s*Math.sin(hand),y-14*s*Math.cos(hand)]],color,2);});}
 // On a design stage the tag is set in the system type at its tier floor or above, so the pill is sized from that.
 function tag(id,value,x,y,{fill=P.mint,color=P.teal,size=18}={}){let w;if(stage?.layout){const r=stage.layout(String(value),{role:'label',over:{face:'demi',size,track:0}}).r;size=r.size;w=stage.measure(String(value),r)+14;}
  else{g.save();g.font=`600 ${size}px Arial`;w=g.measureText(value).width+14;g.restore();}g.save();rounded(x-w/2,y-size*.68,w,size*1.36,fill,null,4);g.restore();text(id,value,x,y,{size,color});}
 function check(id,x,y,color=P.teal,scale=1){body(id,x-12*scale,y-13*scale,31*scale,29*scale,()=>line([[x-10*scale,y],[x-1*scale,y+10*scale],[x+17*scale,y-13*scale]],color,3));}
 function cross(id,x,y,color=P.red,scale=1){body(id,x-10*scale,y-10*scale,20*scale,20*scale,()=>{line([[x-9*scale,y-9*scale],[x+9*scale,y+9*scale]],color,3);line([[x+9*scale,y-9*scale],[x-9*scale,y+9*scale]],color,3);});}
 return{g,P,registry,body,text,line,arrow,pointOn,rounded,person,document,browser,monitor,phone,clock,envelope,building,tag,check,cross,
  figure:(id,x,y,opts)=>figure(stage,id,x,y,opts),cast:(id,key,x,y,opts)=>cast(stage,id,key,x,y,opts)};
}

// ---------------------------------------------------------------- people with faces
// Identity colours: skin tones, hair and a muted wardrobe. They say WHO someone is, never what a thing
// means, so none is a meaning colour (signal, wrong, good, fiction) or the accent. Looks name these
// keys; a world never writes a colour literal.
const LOOK={skin1:'#F3D4B9',skin2:'#E1AE86',skin3:'#C48A5E',skin4:'#986343',skin5:'#5E3B29',
  hairBlack:'#1D1B1F',hairDark:'#3B2B23',hairBrown:'#6D4A33',hairAuburn:'#87472A',hairSand:'#C8A876',hairGrey:'#A3A7AD',
  charcoal:'#30353D',navy:'#2B3950',slate:'#4E5A6B',denim:'#5A7898',sage:'#93AC93',olive:'#7B8458',sand:'#D8C7A5',stone:'#BCC2CA',oat:'#EDE6D8',white:'#FFFDF8'};
const SKINS=Object.keys(LOOK).filter(k=>/^skin\d$/.test(k)),HAIRS=Object.keys(LOOK).filter(k=>/^hair[A-Z]/.test(k)),WARDROBE=Object.keys(LOOK).filter(k=>!SKINS.includes(k)&&!HAIRS.includes(k));
const HAIR_STYLES=['short','side','crop','wavy','curly','puff','bun','bob','long','ponytail','bald'],TOPS=['blazer','shirt','sweater','cardigan','tee'],LOWERS=['trousers','skirt'];
const PROPS=['laptop','tablet','paper','form','folder','phone','mug'],PLACES=['below','above','left','right','none'];
// A look is everything that makes a person recognisable; cast() never lets a lesson change it.
const LOOK_FIELDS=['skin','hair','style','top','topColor','inner','bottom','lower','glasses','beard','badge'];
const DEFAULT_LOOK={skin:'skin2',hair:'hairDark',style:'short',top:'shirt',topColor:'slate',inner:'white',bottom:'charcoal',lower:'trousers',glasses:false,beard:null,badge:false};
function lookOf(spec,who) {
  const L={...DEFAULT_LOOK};for(const k of LOOK_FIELDS)if(spec[k]!==undefined)L[k]=spec[k];
  const need=(k,ok)=>{if(!ok.includes(L[k]))throw new Error(`${who}: ${k} must be one of ${ok.map(String).join(', ')} (got ${L[k]})`);};
  need('skin',SKINS);need('hair',HAIRS);need('style',HAIR_STYLES);need('top',TOPS);for(const k of ['topColor','inner','bottom'])need(k,WARDROBE);
  need('lower',LOWERS);need('beard',[null,false,'beard','stubble']);need('glasses',[true,false]);need('badge',[true,false]);
  return L;
}
// Arm poses: [[a1,a2],[a1,a2]] for the back and front arm (shoulder angle, then elbow bend), in radians.
const POSES={
  stand:{arms:[[.12,.07],[.12,.07]]},
  point:{arms:[[.12,.07],[1.92,.16]]},
  pointUp:{arms:[[.12,.07],[2.55,.1]]},
  present:{arms:[[.12,.07],[.95,-.78]]},
  raise:{arms:[[.12,.07],[2.9,.06]]},
  wave:{arms:[[.12,.07],[2.35,.85]]},
  hold:{arms:[[.3,-1.48],[.3,-1.48]]},
  hips:{arms:[[.62,-1.22],[.62,-1.22]]},
  shrug:{arms:[[.95,-1.85],[.95,-1.85]]},
  think:{arms:[[.3,-1.62],[.16,-2.98]]},
  cross:{arms:[[.26,-1.82],[.26,-1.72]]},
  sit:{arms:[[.18,-.55],[.18,-.55]],body:'sit'},
  lean:{arms:[[.26,-1.82],[.26,-1.72]],body:'lean'}};
const TAU=Math.PI*2,INK=2.5,inOut=x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2,HEX=/^#[0-9a-f]{6}$/i;
const hexMix=(a,b,k)=>'#'+[1,3,5].map(i=>Math.round(mix(parseInt(a.slice(i,i+2),16),parseInt(b.slice(i,i+2),16),k)).toString(16).padStart(2,'0')).join('');
function armsOf(a) {
  const A=Array.isArray(a)?a:POSES[a]?.arms;if(!A)throw new Error('Unknown pose: '+a);
  if(A.length!==2||!A.every(q=>Array.isArray(q)&&q.length===2&&q.every(Number.isFinite)))throw new Error('arms must be [[a1,a2],[a1,a2]]');
  return A;
}
// Arms between two poses (p 0..1), for a gesture that grows instead of jumping:
// figure(S, id, x, y, {arms: blendArms('stand', 'present', seg(t, said, .4))}).
function blendArms(a,b,p){const A=armsOf(a),B=armsOf(b),e=inOut(clamp(p));return A.map((arm,i)=>arm.map((v,j)=>mix(v,B[i][j],e)));}

// Line, paper and label inks come from the stage: design tokens on a design stage, P on a motion stage. On night the
// outline becomes a light keyline (dark hair, shoes and clothes would vanish); face features stay ink on skin.
const inksOf=S=>{const T=S.T;return T?{ink:T.ink,line:S.night?T.rule:T.ink,soft:T.inkSoft,mute:T.mute,paper:T.paperHi,paperLo:T.paperLo,card:T.white,marks:S.night?T.white:T.ink,name:S.night?T.white:T.ink,role:S.night?T.mute:T.inkSoft}
  :{ink:P.ink,line:P.ink,soft:P.muted,mute:P.line,paper:P.paper,paperLo:P.bg,card:P.paper,marks:P.ink,name:P.ink,role:P.muted};};
const fadeOn=(S,a,fn)=>{if(a<=.002)return;if(S.fade)return S.fade(a,fn);S.g.save();S.g.globalAlpha*=Math.min(1,a);try{fn();}finally{S.g.restore();}};
// Names and roles are content text (28 px): system type through S.text on a design stage, stage.label on a motion stage.
const NAME=28;
const say=(S,id,str,x,y,{heavy=false,align,color,owner})=>S.text?S.text(id,str,x,y,{role:'label',over:heavy?{face:'heavy',track:-.6}:undefined,align,color,owner})
  :S.label(id,str,x,y,{size:NAME,weight:heavy?800:600,align,color,owner});

function drawHairBack(g,{hx,hy,hr,s,f,hair,style,ink}) {
  g.fillStyle=hair;g.strokeStyle=ink;g.lineWidth=INK*Math.max(.8,s);g.lineJoin='round';g.lineCap='round';
  if(style==='long'){g.beginPath();g.roundRect(hx-hr-6*s,hy-hr*.5,2*hr+12*s,hr*1.5+30*s,[hr,hr,8*s,8*s]);g.fill();g.stroke();}
  else if(style==='bob'){g.beginPath();g.roundRect(hx-hr-6*s,hy-hr*.7,2*hr+12*s,hr*1.45,[hr,hr,12*s,12*s]);g.fill();g.stroke();}
  else if(style==='ponytail'){g.beginPath();g.ellipse(hx-f*(hr+4*s),hy+6*s,10*s,26*s,f*.35,0,TAU);g.fill();g.stroke();}
  else if(style==='puff'){g.beginPath();g.arc(hx,hy-hr*.55,hr*1.06,0,TAU);g.fill();g.stroke();}
  else if(style==='bun'){g.beginPath();g.arc(hx-f*6*s,hy-hr-9*s,12*s,0,TAU);g.fill();g.stroke();}
}
// Head and face: ears, head, beard (a jaw crescent that leaves the mouth on skin), hair on top, then
// brows, eyes, nose and a mouth that opens and closes while speaking (phase = t), and glasses.
function drawHead(g,{hx,hy,hr,s,f,skin,hair,style,glasses,beard,speaking,phase,ink,edge}) {
  const line=()=>{g.strokeStyle=edge;g.lineWidth=INK*Math.max(.8,s);g.lineJoin='round';g.lineCap='round';};
  line();g.fillStyle=skin;
  for(const sx of [-1,1]){g.beginPath();g.arc(hx+sx*(hr-1*s),hy+4*s,7*s,0,TAU);g.fill();g.stroke();}
  g.beginPath();g.arc(hx,hy,hr,0,TAU);g.fill();g.stroke();
  if(beard){g.save();g.beginPath();g.arc(hx,hy,hr,0,TAU);g.clip();g.globalAlpha*=beard==='stubble'?.32:1;g.fillStyle=hair;g.beginPath();
    g.moveTo(hx-hr-2,hy-2*s);g.quadraticCurveTo(hx-hr*.55,hy+hr*.72,hx,hy+hr*.6+4*s);g.quadraticCurveTo(hx+hr*.55,hy+hr*.72,hx+hr+2,hy-2*s);
    g.lineTo(hx+hr+2,hy+hr+4);g.lineTo(hx-hr-2,hy+hr+4);g.closePath();g.fill();
    g.globalAlpha=1;g.fillStyle=skin;g.beginPath();g.ellipse(hx+4*f*s,hy+17*s,10*s,6.5*s,0,0,TAU);g.fill();g.restore();
    line();g.beginPath();g.arc(hx,hy,hr,0,TAU);g.stroke();}
  g.fillStyle=hair;line();
  if(style==='short'||style==='side'||style==='wavy'){
    g.beginPath();g.arc(hx,hy,hr+3*s,Math.PI*1.02,Math.PI*1.98);
    if(style==='wavy'){for(let k=0;k<=4;k++){const u=k/4,px=hx+hr*(1-2*u)*.98,py=hy-hr*.5+Math.sin(k*1.9)*4*s;g.quadraticCurveTo(px+6*s,py+7*s,px,py);}}
    else g.quadraticCurveTo(hx+f*hr*.2,hy-hr*(style==='side'?.62:.48),hx-hr-3*s,hy-4*s);
    g.closePath();g.fill();g.stroke();
    if(style==='side'){g.beginPath();g.moveTo(hx-f*hr*.35,hy-hr-2*s);g.quadraticCurveTo(hx+f*hr*.4,hy-hr*.95,hx+f*(hr+3*s),hy-hr*.3);g.stroke();}}
  else if(style==='crop'){g.beginPath();g.arc(hx,hy,hr+1.5*s,Math.PI*1.08,Math.PI*1.92);g.quadraticCurveTo(hx,hy-hr*.72,hx-hr*.98,hy-hr*.38);g.closePath();g.fill();g.stroke();}
  else if(style==='curly'||style==='puff'){const n=style==='curly'?8:6;for(let k=0;k<n;k++){const a=Math.PI*(1+k/(n-1)),cx=hx+Math.cos(a)*hr*.9,cy=hy-3*s+Math.sin(a)*hr*.9;
      g.beginPath();g.arc(cx,cy,(style==='curly'?11:9)*s,0,TAU);g.fill();g.stroke();}
    g.beginPath();g.arc(hx,hy-2*s,hr*.92,Math.PI*1.05,Math.PI*1.95);g.closePath();g.fill();}
  else if(style==='bun'||style==='ponytail'){g.beginPath();g.arc(hx,hy,hr+2*s,Math.PI,TAU);g.quadraticCurveTo(hx+f*hr*.3,hy-hr*.5,hx,hy-hr*.58);
    g.quadraticCurveTo(hx-f*hr*.3,hy-hr*.5,hx-hr-2*s,hy);g.closePath();g.fill();g.stroke();}
  else if(style==='bob'||style==='long'){g.beginPath();g.arc(hx,hy,hr+3*s,Math.PI*.98,Math.PI*2.02);
    if(style==='bob'){g.lineTo(hx+hr+3*s,hy+2*s);g.lineTo(hx+hr*.55,hy-hr*.38);g.lineTo(hx-hr*.7,hy-hr*.38);g.lineTo(hx-hr-3*s,hy+2*s);}
    else{g.quadraticCurveTo(hx+hr*.6,hy-hr*.62,hx+2*s,hy-hr*.88);g.quadraticCurveTo(hx-hr*.6,hy-hr*.62,hx-hr-3*s,hy+hr*.15);}
    g.closePath();g.fill();g.stroke();}
  else if(style==='bald'){for(const sx of [-1,1]){g.beginPath();g.arc(hx+sx*hr*.86,hy-6*s,8*s,Math.PI*(sx<0?.6:1.4),Math.PI*(sx<0?1.5:2.4));g.lineTo(hx+sx*hr*.86,hy-6*s);g.closePath();g.fill();}}
  const ex=k=>hx+(k*11.5+4*f)*s,ey=hy+3*s,lift=speaking>0?2*s*clamp(speaking):0;
  g.strokeStyle=ink;g.lineCap='round';g.lineWidth=2.7*s;
  for(const k of [-1,1]){g.beginPath();g.moveTo(ex(k)-6*s,ey-9*s-lift+(k*f>0?0:1.2*s));g.lineTo(ex(k)+6*s,ey-10.5*s-lift);g.stroke();}
  g.fillStyle=ink;for(const k of [-1,1]){g.beginPath();g.arc(ex(k),ey,3.5*s,0,TAU);g.fill();}
  g.lineWidth=2.2*s;g.beginPath();g.moveTo(hx+5*f*s,ey+3*s);g.lineTo(hx+8*f*s,ey+11*s);g.lineTo(hx+3*f*s,ey+12*s);g.stroke();
  const mx=hx+4*f*s,my=hy+18*s,open=speaking>0?clamp(speaking)*(.3+.7*Math.abs(Math.sin(phase*11.3)*Math.cos(phase*4.1))):0;
  if(open>.08){g.fillStyle=ink;g.beginPath();g.ellipse(mx,my+1*s,6.5*s,(1.6+5.2*open)*s,0,0,TAU);g.fill();}
  else{g.lineWidth=2.6*s;g.beginPath();g.arc(mx,my-5*s,8*s,Math.PI*.22,Math.PI*.78);g.stroke();}
  if(glasses){g.strokeStyle=ink;g.lineWidth=2.2*s;for(const k of [-1,1]){g.beginPath();g.arc(ex(k),ey,8.5*s,0,TAU);g.stroke();}
    g.beginPath();g.moveTo(ex(-1)+8.5*s,ey-1*s);g.lineTo(ex(1)-8.5*s,ey-1*s);g.stroke();}
}

// figure(): a full illustrated person: ink outlines, flat fills, a face with brows, eyes, nose and
// mouth, distinct hair, clothes and skin. (x, y) is the point between the feet on the ground. At
// s = 1 a standing figure is about 300 px tall, a hero while it speaks; use s .65–.75 for supporting
// figures. It draws on a design stage (or a motion stage): the full extent registers through
// stage.actor and the name and role through stage text, so the frame audit sees the whole person.
//   pose:     stand | point | pointUp | present | raise | wave | hold | hips | shrug | think | cross |
//             sit (on a stool) | lean (toward `facing`)
//   arms:     a pose name or [[a1,a2],[a1,a2]] (back arm, front arm); blendArms() grows a gesture
//   facing:   1 right, -1 left (eyes, nose, pointing arm, speech marks)
//   speaking: 0..1 with phase (pass t): the mouth moves and three speech marks appear (design talking())
//   prop:     laptop | tablet | paper | form | folder | phone | mug, between the hands or in the front hand
//   look:     skin, hair (LOOK names), style (HAIR_STYLES), top (TOPS), topColor, inner, bottom (wardrobe
//             names), lower (trousers | skirt), glasses, beard (beard | stubble), badge (a lanyard pass)
//   label:    below | above | left | right | none for the name (heavy) and role (soft ink), both 28 px
//   s or scale, alpha, owner (the figure's container; its labels share it), seat, lean, ground (the colour
//             behind a faded figure: the stage paper or night by default; null fades with plain alpha)
// Returns {bounds, hands:{back,front}, head:[x,y], mouth:[x,y], top} in world space.
function figure(S,id,x,y,opts={}) {
  if(!S?.g||!S.actor||!(S.text||S.label))throw new Error('figure() needs an auditable stage');
  const {pose='stand',arms=null,facing=1,alpha=1,owner=null,speaking=0,phase=0,prop=null,propColor=null,name=null,role=null,label='below',
    nameColor,roleColor,seat=true,lean=.13,ground=S.T?(S.night?S.T.night:S.T.paper):P.bg}=opts,s=opts.scale??opts.s??1,L=lookOf(opts,'figure '+id),K0=inksOf(S),g=S.g;
  if(!POSES[pose])throw new Error('Unknown pose: '+pose);
  if(prop!==null&&!PROPS.includes(prop))throw new Error('Unknown prop: '+prop);
  if(!PLACES.includes(label))throw new Error('Unknown label placement: '+label);
  const {style,top,lower,glasses,beard,badge}=L,look={skin:LOOK[L.skin],hair:LOOK[L.hair],top:LOOK[L.topColor],inner:LOOK[L.inner],bottom:LOOK[L.bottom]};
  const f=facing<0?-1:1,body=POSES[pose].body||'stand',A=armsOf(arms??pose);
  const drop=body==='sit'?60*s:0,hipY=y-122*s+drop,shY=y-206*s+drop,hx=x+(body==='lean'?f*14*s:0),hr=31*s,hy=y-259*s+drop;
  // Arms: shoulder -> elbow -> hand; side -1 is the figure's left (screen left when facing right).
  const U=58*s,F=54*s,arm=(side,[a1,a2])=>{const o=[x+side*40*s,shY+6*s],e=[o[0]+side*U*Math.sin(a1),o[1]+U*Math.cos(a1)],a=a1+a2,h=[e[0]+side*F*Math.sin(a),e[1]+F*Math.cos(a)];return [o,e,h];};
  const back=arm(-f,A[0]),front=arm(f,A[1]),mid=[(back[2][0]+front[2][0])/2,(back[2][1]+front[2][1])/2];
  const hairTop=style==='puff'?hy-hr*1.61:style==='bun'?hy-hr-21*s:style==='curly'?hy-hr*.9-14*s:hy-hr-4*s;
  // Full extent: every part as a box. Sleeves are 27·s strokes, so arm joints are 13.5·s discs; the upper
  // body turns about the hips with a lean, so its boxes turn too; the outline stroke and antialiasing pad it.
  const turn=body==='lean'?f*lean:0,rot=([px,py])=>{const dx=px-x,dy=py-hipY;return [x+dx*Math.cos(turn)-dy*Math.sin(turn),hipY+dx*Math.sin(turn)+dy*Math.cos(turn)];};
  const low=[[x+(5*f-35)*s,y-14*s,x+(5*f+35)*s,y+2*s]],up=[[x-44*s,shY,x+44*s,hipY+2*s],[hx-hr-8*s,hairTop,hx+hr+8*s,hy+hr]];
  if(body==='sit'){low.push([x-36*s,hipY-6*s,x+36*s,y-12*s]);if(seat)low.push([x-50*s,y-70*s,x+50*s,y]);}
  else low.push(lower==='skirt'?[x-48*s,hipY,x+48*s,y-10*s]:[x-30*s,hipY-2*s,x+30*s,y-10*s]);
  if(style==='long')up.push([hx-hr-8*s,hy-4*s,hx+hr+8*s,shY+30*s]);
  if(style==='ponytail'){const px=hx-f*(hr+4*s);up.push([px-13.2*s,hy-22.2*s,px+13.2*s,hy+34.2*s]);}
  for(const [px,py] of [...back,...front])up.push([px-13.5*s,py-13.5*s,px+13.5*s,py+13.5*s]);
  const [mx,my]=mid,[fx,fy]=front[2];
  if(prop)up.push(prop==='laptop'?[mx-54*s,my-51*s,mx+54*s,my+17*s]:prop==='tablet'?[mx-30*s,my-64*s,mx+30*s,my+16*s]:prop==='phone'?[fx-12*s,fy-30*s,fx+12*s,fy+12*s]
    :prop==='mug'?[Math.min(fx-12*s,fx+f*21*s),fy-24*s,Math.max(fx+12*s,fx+f*21*s),fy+2*s]:[mx-35*s,my-75*s,mx+35*s,my+15*s]);
  const sx=hx+f*(hr+12*s),sy=hy+8*s,marks=[Math.min(sx,sx+f*14*s),sy-10.5*s,Math.max(sx,sx+f*14*s),sy+10.5*s];
  const pad=INK*Math.max(.8,s)/2+1,corners=b=>[[b[0],b[1]],[b[2],b[1]],[b[0],b[3]],[b[2],b[3]]];
  const extent=list=>{const pts=[...low.flatMap(corners),...list.flatMap(b=>corners(b).map(rot))],xs=pts.map(q=>q[0]),ys=pts.map(q=>q[1]);
    const x0=Math.min(...xs)-pad,y0=Math.min(...ys)-pad;return {x:x0,y:y0,w:Math.max(...xs)+pad-x0,h:Math.max(...ys)+pad-y0};};
  // Labels are placed as if the speech marks were there, so a name never jumps when someone starts talking.
  const bounds=extent(speaking>0?[...up,marks]:up),room=extent([...up,marks]);
  const out={bounds,hands:{back:rot(back[2]),front:rot(front[2])},head:rot([hx,hy]),mouth:rot([hx+4*f*s,hy+18*s]),top:rot([hx,hairTop])[1]};
  if(alpha<=.002)return out;
  fadeOn(S,alpha,()=>{
    S.actor(id,bounds,g=>{
      // A faded person is drawn opaque in colours mixed toward the ground (only the last 15% of a fade lowers
      // alpha), so a dimmed speaker reads as one faded person, not an x-ray of overlapping parts. A layer
      // composited with drawImage(canvas) would leak a frame per draw; ground:null keeps plain alpha.
      const a=g.globalAlpha,fade=ground&&HEX.test(ground)&&a<.999?1-a:0,c=v=>fade&&HEX.test(v)?hexMix(v,ground,fade):v;if(fade)g.globalAlpha=Math.min(1,a/.15);
      const K=Object.fromEntries(Object.entries(K0).map(([k,v])=>[k,c(v)])),skin=c(look.skin),hair=c(look.hair),topColor=c(look.top),inner=c(look.inner),bottom=c(look.bottom);
      const ink=(w=INK)=>{g.strokeStyle=K.line;g.lineWidth=w*Math.max(.8,s);g.lineJoin='round';g.lineCap='round';};
      // seat, legs and shoes
      if(body==='sit'&&seat){ink();g.fillStyle=K.paperLo;g.fillRect(x-50*s,y-70*s,100*s,12*s);g.strokeRect(x-50*s,y-70*s,100*s,12*s);
        g.beginPath();g.moveTo(x-40*s,y-58*s);g.lineTo(x-46*s,y);g.moveTo(x+40*s,y-58*s);g.lineTo(x+46*s,y);g.moveTo(x-43*s,y-26*s);g.lineTo(x+43*s,y-26*s);g.stroke();}
      ink();g.fillStyle=bottom;
      if(body==='sit'){g.beginPath();g.roundRect(x-36*s,hipY-6*s,72*s,30*s,12*s);g.fill();g.stroke();
        for(const k of [-1,1]){g.beginPath();g.roundRect(x+k*17*s-12*s,hipY+16*s,24*s,y-12*s-(hipY+16*s),6*s);g.fill();g.stroke();}}
      else if(lower==='skirt'){g.fillStyle=skin;for(const k of [-1,1]){g.beginPath();g.roundRect(x+k*14*s-9*s,y-74*s,18*s,64*s,6*s);g.fill();g.stroke();}
        g.fillStyle=bottom;g.beginPath();g.moveTo(x-38*s,hipY);g.lineTo(x+38*s,hipY);g.lineTo(x+48*s,y-66*s);g.lineTo(x-48*s,y-66*s);g.closePath();g.fill();g.stroke();}
      else for(const k of [-1,1]){g.beginPath();g.roundRect(x+(k<0?-30:3)*s,hipY-2*s,27*s,y-10*s-(hipY-2*s),[4*s,4*s,6*s,6*s]);g.fill();g.stroke();}
      g.fillStyle=K.ink;for(const k of [-1,1]){g.beginPath();g.ellipse(x+(k*16+5*f)*s,y-6*s,19*s,8*s,0,0,TAU);g.fill();if(K.line!==K.ink){ink(1.6);g.stroke();}}
      // upper body (turns about the hips with a lean)
      g.save();if(turn){g.translate(x,hipY);g.rotate(turn);g.translate(-x,-hipY);}
      drawHairBack(g,{hx,hy,hr,s,f,hair,style,ink:K.line});
      ink();g.fillStyle=skin;g.fillRect(x-10*s,hy+hr-6*s,20*s,shY-(hy+hr-6*s)+8*s);g.strokeRect(x-10*s,hy+hr-6*s,20*s,shY-(hy+hr-6*s)+8*s);
      g.fillStyle=topColor;g.beginPath();g.moveTo(x-44*s,hipY+2*s);g.lineTo(x-44*s,shY+24*s);g.quadraticCurveTo(x-44*s,shY,x-20*s,shY);g.lineTo(x+20*s,shY);
      g.quadraticCurveTo(x+44*s,shY,x+44*s,shY+24*s);g.lineTo(x+44*s,hipY+2*s);g.closePath();g.fill();ink();g.stroke();
      if(top==='blazer'){g.fillStyle=inner;g.beginPath();g.moveTo(x-17*s,shY);g.lineTo(x,shY+50*s);g.lineTo(x+17*s,shY);g.closePath();g.fill();g.stroke();
        g.lineWidth=2*s;g.beginPath();g.moveTo(x-17*s,shY);g.lineTo(x-8*s,shY+36*s);g.lineTo(x-1*s,shY+52*s);g.moveTo(x+17*s,shY);g.lineTo(x+8*s,shY+36*s);g.lineTo(x+1*s,shY+52*s);
        g.moveTo(x,shY+50*s);g.lineTo(x,hipY);g.stroke();g.fillStyle=K.ink;g.beginPath();g.arc(x+6*s,hipY-26*s,2.6*s,0,TAU);g.fill();}
      else if(top==='shirt'){g.fillStyle=topColor;for(const k of [-1,1]){g.beginPath();g.moveTo(x+k*14*s,shY-2*s);g.lineTo(x,shY+12*s);g.lineTo(x+k*4*s,shY+20*s);g.lineTo(x+k*18*s,shY+6*s);g.closePath();g.fill();g.stroke();}
        g.lineWidth=2*s;g.beginPath();g.moveTo(x,shY+12*s);g.lineTo(x,hipY);g.stroke();g.fillStyle=K.ink;for(let k=0;k<3;k++){g.beginPath();g.arc(x+5*s,shY+34*s+k*24*s,2.2*s,0,TAU);g.fill();}}
      else if(top==='sweater'||top==='tee'){g.fillStyle=skin;g.beginPath();g.ellipse(x,shY+1*s,14*s,8*s,0,0,Math.PI);g.fill();g.stroke();
        if(top==='sweater'){g.lineWidth=2*s;g.beginPath();g.moveTo(x-42*s,hipY-8*s);g.lineTo(x+42*s,hipY-8*s);g.stroke();}}
      else if(top==='cardigan'){g.fillStyle=inner;g.beginPath();g.moveTo(x-13*s,shY);g.lineTo(x+13*s,shY);g.lineTo(x+11*s,hipY);g.lineTo(x-11*s,hipY);g.closePath();g.fill();g.stroke();
        g.fillStyle=skin;g.beginPath();g.ellipse(x,shY+1*s,10*s,6*s,0,0,Math.PI);g.fill();g.stroke();
        g.fillStyle=K.ink;for(let k=0;k<3;k++){g.beginPath();g.arc(x-17*s,shY+34*s+k*24*s,2.2*s,0,TAU);g.fill();}}
      if(badge){g.lineWidth=1.8*s;g.beginPath();g.moveTo(x-12*s,shY);g.lineTo(x-2*s,shY+48*s);g.moveTo(x+12*s,shY);g.lineTo(x+2*s,shY+48*s);g.stroke();
        g.fillStyle=K.card;g.fillRect(x-10*s,shY+46*s,20*s,26*s);ink(2);g.strokeRect(x-10*s,shY+46*s,20*s,26*s);g.fillStyle=K.soft;g.fillRect(x-6*s,shY+52*s,12*s,4*s);}
      // long hair falls in front of the shoulders
      if(style==='long'){g.fillStyle=hair;ink();for(const k of [-1,1]){g.beginPath();g.roundRect(hx+k*(hr+1*s)-7*s,hy-4*s,14*s,shY-hy+34*s,7*s);g.fill();g.stroke();}}
      // arms: an ink-cased sleeve stroke, then the hand
      const sleeve=Q=>{g.lineCap='round';g.lineJoin='round';
        g.strokeStyle=K.line;g.lineWidth=27*s;g.beginPath();g.moveTo(...Q[0]);g.lineTo(...Q[1]);g.lineTo(...Q[2]);g.stroke();
        g.strokeStyle=topColor;g.lineWidth=21.5*s;g.beginPath();g.moveTo(...Q[0]);g.lineTo(...Q[1]);if(top!=='tee')g.lineTo(...Q[2]);g.stroke();
        if(top==='tee'){g.strokeStyle=skin;g.lineWidth=17*s;g.beginPath();g.moveTo(...Q[1]);g.lineTo(...Q[2]);g.stroke();}};
      const hand=p=>{g.fillStyle=skin;g.beginPath();g.arc(p[0],p[1],9.5*s,0,TAU);g.fill();ink(2.2);g.stroke();};
      sleeve(back);sleeve(front);
      // prop between the hands or in the front hand
      const pc=c(propColor)||K.paperLo;
      if(prop==='laptop'){const w=96*s,h=62*s,px=mx,py=my-20*s;g.fillStyle=pc;g.fillRect(px-w/2,py-h/2,w,h);ink();g.strokeRect(px-w/2,py-h/2,w,h);
        g.fillStyle=K.ink;g.fillRect(px-w/2-6*s,py+h/2,w+12*s,6*s);g.lineWidth=1.5*s;g.strokeStyle=K.mute;g.strokeRect(px-9*s,py-9*s,18*s,18*s);}
      else if(prop==='tablet'){const w=60*s,h=80*s,px=mx,py=my-24*s;g.fillStyle=c(LOOK.charcoal);g.beginPath();g.roundRect(px-w/2,py-h/2,w,h,5*s);g.fill();ink();g.stroke();
        g.fillStyle=K.mute;g.beginPath();g.arc(px,py-h/2+8*s,2.5*s,0,TAU);g.fill();}
      else if(prop==='paper'||prop==='form'||prop==='folder'){const w=70*s,h=90*s,px=mx,py=my-30*s;g.fillStyle=prop==='folder'?c(propColor||LOOK.sand):K.paper;
        g.fillRect(px-w/2,py-h/2,w,h);ink();g.strokeRect(px-w/2,py-h/2,w,h);
        if(prop!=='folder'){if(prop==='form'){g.fillStyle=K.ink;g.fillRect(px-w/2,py-h/2,w,14*s);}g.fillStyle=K.mute;for(let k=0;k<4;k++)g.fillRect(px-w/2+9*s,py-h/2+(prop==='form'?24:14)*s+k*12*s,w*(k%2?.48:.66),3*s);
          if(prop==='form'){g.fillStyle=K.ink;g.fillRect(px+w*.05,py+h/2-16*s,w*.36,5*s);}}}
      else if(prop==='phone'){g.fillStyle=K.ink;g.beginPath();g.roundRect(fx-12*s,fy-30*s,24*s,42*s,4*s);g.fill();g.fillStyle=K.paperLo;g.fillRect(fx-8*s,fy-25*s,16*s,28*s);}
      else if(prop==='mug'){g.fillStyle=pc;ink();g.fillRect(fx-12*s,fy-24*s,24*s,26*s);g.strokeRect(fx-12*s,fy-24*s,24*s,26*s);
        g.beginPath();g.arc(fx+f*14*s,fy-12*s,7*s,-Math.PI/2,Math.PI/2,f<0);g.stroke();}
      hand(back[2]);hand(front[2]);
      drawHead(g,{hx,hy,hr,s,f,skin,hair,style,glasses,beard,speaking,phase,ink:K.ink,edge:K.line});
      // speech marks on the facing side
      if(speaking>0){g.save();g.globalAlpha*=clamp(speaking*1.5);ink(2.8);g.strokeStyle=K.marks;
        for(const a of [-.55,0,.55]){const c=Math.cos(a),sn=Math.sin(a);g.beginPath();g.moveTo(sx+f*c*2*s,sy+sn*12*s);g.lineTo(sx+f*c*14*s,sy+sn*20*s);g.stroke();}g.restore();}
      g.restore();
    },owner);
    if(label==='none'||!(name||role))return;
    const half=NAME*.65,gap=6,lh=NAME*1.36;let nx=x,ny,ty,align='center';
    if(label==='below'){ny=room.y+room.h+gap+half;ty=name?ny+lh:ny;}
    else if(label==='above'){ty=room.y-gap-half;ny=role?ty-lh:ty;}
    else{nx=label==='right'?room.x+room.w+gap:room.x-gap;align=label==='right'?'left':'right';ny=out.head[1]-(name&&role?lh/2:0);ty=name?ny+lh:ny;}
    if(name)say(S,id+'-name',name,nx,ny,{heavy:true,align,color:nameColor??K0.name,owner});
    if(role)say(S,id+'-role',role,nx,ty,{align,color:roleColor??K0.role,owner});
  });
  return out;
}

// ---------------------------------------------------------------- the course's cast
// A course defines its recurring people once, defineCast({key:{name, role, skin, hair, style, top,
// topColor, inner, bottom, lower, glasses, beard, badge}}), and stages them with cast(S, id, key, x, y,
// opts). A real or recurring person drawn differently across lessons reads as a different person, so a
// preset's look is fixed: opts may set pose, arms, facing, speaking, phase, s/scale, alpha, prop,
// owner and label placement, and may hide the name or role (false), but a look field throws.
// Two presets with an identical look also throw: they would read as one person. Generic, unnamed
// people are presets with name: null. Worlds read CAST; only defineCast writes it.
const CAST={};
const CAST_OPTIONS=['pose','arms','facing','speaking','phase','s','scale','alpha','owner','prop','propColor','label','name','role','nameColor','roleColor','seat','lean','ground'];
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
function defineCast(spec) {
  const entries=Object.entries(spec||{});
  if(!entries.length)throw new Error('defineCast needs at least one person');
  // Validate everything first, so a rejected call leaves no partial cast behind.
  const out=entries.map(([key,p])=>{
    if(!/^[a-z][A-Za-z0-9]*$/.test(key))throw new Error('Invalid cast key: '+key);
    if(own(CAST,key))throw new Error('Cast member already defined: '+key);
    if(!p||typeof p!=='object')throw new Error('Cast member needs a look: '+key);
    for(const k of Object.keys(p))if(k!=='name'&&k!=='role'&&!LOOK_FIELDS.includes(k))throw new Error(`Unknown cast field for ${key}: ${k}`);
    for(const k of ['skin','hair','style'])if(p[k]===undefined)throw new Error(`Cast member ${key} needs ${k}`);
    for(const k of ['name','role'])if(p[k]!=null&&!(typeof p[k]==='string'&&p[k].trim()))throw new Error(`Cast member ${key}: ${k} must be text or null`);
    return [key,Object.freeze({name:p.name??null,role:p.role??null,...lookOf(p,'cast member '+key)})];
  });
  const sig=e=>JSON.stringify(LOOK_FIELDS.map(k=>e[k]||null)),seen=new Map(Object.entries(CAST).map(([k,e])=>[sig(e),k]));
  for(const [key,e] of out){const twin=seen.get(sig(e));if(twin)throw new Error(`Cast members ${twin} and ${key} look identical; change a look field`);seen.set(sig(e),key);}
  for(const [key,e] of out)CAST[key]=e;
  return CAST;
}
function cast(S,id,key,x,y,opts={}) {
  if(!own(CAST,key))throw new Error('Unknown cast member: '+key);
  for(const k of Object.keys(opts)) {
    if(LOOK_FIELDS.includes(k))throw new Error(`Cast member ${key} always looks the same: ${k} cannot be overridden`);
    if(!CAST_OPTIONS.includes(k))throw new Error('Unknown cast option: '+k);
  }
  for(const k of ['name','role'])if(opts[k]!==undefined&&opts[k]!==false&&opts[k]!==null)throw new Error(`Cast member ${key} keeps its ${k}; pass ${k}: false to hide it`);
  const p=CAST[key],hide=k=>opts[k]===false||opts[k]===null;
  return figure(S,id,x,y,{...p,...opts,name:hide('name')?null:p.name,role:hide('role')?null:p.role});
}

function createIllustration(stage){if(!stage?.g||!stage.actor||!stage.label)throw new Error('An auditable motion stage is required');return context(stage.g,stage);}
module.exports={P,clamp,mix,smooth,between,createIllustration,LOOK,HAIR_STYLES,TOPS,PROPS,LOOK_FIELDS,POSES,CAST,figure,blendArms,defineCast,cast};
