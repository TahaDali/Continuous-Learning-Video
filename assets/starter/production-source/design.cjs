'use strict';
// Design system for explanatory motion. It sits beside motion.cjs and keeps the same audit
// contract: every text and solid object registers screen bounds, owners describe containment,
// connectors and annotations stay unregistered like edge(), and transitions are reported.
// Read references/video/design-system.md before authoring with it.
const path=require('path');

// Bundled SIL Open Font License faces (see fonts/*-OFL.txt). Roles select a face; worlds never name fonts.
const FACES={regular:'Inter-Regular',medium:'Inter-Medium',demi:'Inter-SemiBold',bold:'Inter-Bold',heavy:'Inter-ExtraBold',
  serif:'InstrumentSerif-Regular',serifItalic:'InstrumentSerif-Italic',mono:'JetBrainsMono-Regular',monoBold:'JetBrainsMono-Bold'};
const FONT_FILES=Object.values(FACES).map(face=>'production-source/fonts/'+face+'.ttf');

// The renderer, poster writer and audit install the canvas module they already loaded.
// A world cannot load canvas itself (render-sources rejects dynamic loading), and silent
// fallback fonts would change every measurement, so drawing fails until this has run.
let runtime=null;
function installDesignRuntime(canvasModule) {
  if(!canvasModule?.GlobalFonts||!canvasModule.createCanvas)throw new Error('installDesignRuntime needs the loaded canvas module');
  if(runtime?.module===canvasModule)return runtime;
  for(const face of Object.values(FACES)) {
    if(!canvasModule.GlobalFonts.registerFromPath(path.join(__dirname,'fonts',face+'.ttf'),face))throw new Error('Could not register bundled font: '+face);
  }
  runtime={module:canvasModule,createCanvas:canvasModule.createCanvas,grain:null};
  return runtime;
}

// ---------------------------------------------------------------- tokens
// One paper, one ink, one accent per scene. Teal and gold continue the original palette.
const T={paper:'#F2EDE2',paperHi:'#FBF8F1',paperLo:'#E7DFCF',ink:'#15262C',inkSoft:'#4A5C61',mute:'#8F9A97',rule:'#D3C9B6',
  teal:'#0E7469',tealSoft:'#D2E7E0',accent:'#DE5530',accentSoft:'#F7D8CA',gold:'#F2BF45',goldSoft:'#FAE6B3',goldInk:'#9A6A12',
  blue:'#2F63B5',blueSoft:'#DCE6F6',night:'#13242A',nightHi:'#1D323A',nightRule:'#2E464E',white:'#FFFDF8',good:'#2E8B57'};
// Subject colours (a brand, a map legend) are added once here, never as literals inside a world.
function extendTheme(colours) {
  for(const [k,v] of Object.entries(colours||{})) {
    if(k in T)throw new Error('Theme token already exists: '+k);
    if(!/^#[0-9a-f]{6}$/i.test(v))throw new Error('Theme colours must be #rrggbb: '+k);
    T[k]=v;
  }
  return T;
}
// Roles, not sizes: authors pick a role and may override size; the system owns face and tracking.
const TYPE={
  kicker:{face:'bold',size:15,track:2.6,upper:true},
  display:{face:'heavy',size:88,track:-3},
  headline:{face:'bold',size:44,track:-1.3},
  title:{face:'demi',size:32,track:-.6},
  body:{face:'demi',size:30,track:-.4},
  label:{face:'demi',size:21,track:-.1},
  small:{face:'medium',size:17,track:0},
  accent:{face:'serifItalic',size:70,track:-.4},
  accentMd:{face:'serifItalic',size:38,track:0},
  accentSm:{face:'serifItalic',size:27,track:0},
  numeral:{face:'heavy',size:58,track:-1.5},
  numeralSm:{face:'bold',size:30,track:-.6},
  mono:{face:'mono',size:17,track:0}};
const role=(name,over)=>({...(TYPE[name]||TYPE.body),...over});

// ---------------------------------------------------------------- timing
const clamp=x=>x<0?0:x>1?1:x,lerp=(a,b,p)=>a+(b-a)*p;
const E={linear:x=>x,
  inOut:x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2,
  out:x=>1-Math.pow(1-x,3),
  outQuint:x=>1-Math.pow(1-x,5),
  outExpo:x=>x>=1?1:1-Math.pow(2,-10*x),
  in:x=>x*x*x,
  outBack:x=>{const c=1.6;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2);},
  spring:x=>x>=1?1:1-Math.exp(-6*x)*Math.cos(9*x)};
// Progress of a window that starts at `a` and lasts `d` seconds.
const seg=(t,a,d,ease=E.out)=>ease(clamp((t-a)/Math.max(1e-3,d)));

// Word onsets for one scene: measured narration wins; otherwise distribute across the
// speech span by word length and say so. Display-only text can request its own span.
function wordTimes(words,scene,{from,to}={}) {
  const measured=scene&&Array.isArray(scene.wordTimings)&&scene.wordTimings.length===words.length;
  if(measured)return {times:scene.wordTimings.map(w=>w.start),method:'measured'};
  const a=from??scene?.speechStart??scene?.start??0,b=to??scene?.speechEnd??scene?.end??a+words.length*.3;
  const weights=words.map(w=>w.replace(/[^\w]/g,'').length+2),total=weights.reduce((x,y)=>x+y,0);
  let acc=0;return {times:weights.map(w=>{const s=a+(b-a)*acc/total;acc+=w;return s;}),method:'estimated'};
}

// Narration cues: cue(scene, word, nth) returns when that spoken word starts. Scenes are
// addressed by id or 1-based index. Before narration exists the times are estimated from the
// scene span; afterwards they are the measured word boundaries, with no world change needed.
// A word that is not in the narration throws, so a reveal can never silently drift.
const normWord=s=>String(s).toLowerCase().replace(/[’']/g,'').replace(/[^a-z0-9$%]/g,'');
const cueTables=new WeakMap();
function createCues(lesson) {
  if(!cueTables.has(lesson))cueTables.set(lesson,lesson.scenes.map(scene=>{
    const measured=Array.isArray(scene.wordTimings)&&scene.wordTimings.length>0;
    const words=measured?scene.wordTimings.map(w=>w.text):String(scene.narration||'').split(/\s+/).filter(Boolean);
    const {times,method}=measured?{times:scene.wordTimings.map(w=>w.start),method:'measured'}:wordTimes(words,scene);
    return {id:scene.id,method,words:words.map((w,i)=>({w:normWord(w),start:times[i]}))};
  }));
  const table=cueTables.get(lesson);
  const find=scene=>{const s=typeof scene==='number'?table[scene-1]:table.find(x=>x.id===scene);if(!s)throw new Error('Unknown cue scene: '+scene);return s;};
  const cue=(scene,word,nth=1)=>{let k=0;for(const x of find(scene).words)if(x.w===normWord(word)&&++k===nth)return x.start;
    throw new Error(`Missing narration cue: scene ${scene} "${word}" #${nth}`);};
  // Onsets for on-screen words that repeat the narration in order. Matching starts after the
  // `after` time, so a phrase can follow an earlier occurrence of the same words.
  cue.phrase=(scene,phrase,{after=-Infinity}={})=>{
    const list=find(scene).words;let i=list.findIndex(x=>x.start>after);if(i<0)i=list.length;
    return String(phrase).split(/\s+/).filter(Boolean).map(w=>{const n=normWord(w);while(i<list.length&&list[i].w!==n)i++;
      if(i>=list.length)throw new Error(`Missing narration phrase word: scene ${scene} "${w}" in "${phrase}"`);return list[i++].start;});
  };
  cue.method=scene=>find(scene).method;
  return cue;
}

// Camera: ease between keyframes; equal neighbours hold. Returns speed for motion blur.
function cameraAt(t,keys) {
  if(t<=keys[0].t)return {...keys[0],speed:0};
  for(let i=1;i<keys.length;i++) {
    const a=keys[i-1],b=keys[i];
    if(t<=b.t) {
      const ease=b.ease||E.inOut,span=Math.max(1e-3,b.t-a.t),u=clamp((t-a.t)/span),p=ease(u),h=1/240;
      const speed=Math.hypot(b.x-a.x,b.y-a.y)*(ease(clamp(u+h/span))-p)/h;
      return {x:lerp(a.x,b.x,p),y:lerp(a.y,b.y,p),zoom:lerp(a.zoom,b.zoom,p),speed};
    }
  }
  return {...keys.at(-1),speed:0};
}

// ---------------------------------------------------------------- textures
function grainLayer(W,H) {
  if(runtime.grain&&runtime.grain.width===W&&runtime.grain.height===H)return runtime.grain;
  const layer=runtime.createCanvas(W,H),c=layer.getContext('2d'),img=c.createImageData(W,H);
  let s=1234567;const rnd=()=>{s=(s*1664525+1013904223)>>>0;return s/4294967296;};
  for(let i=0;i<img.data.length;i+=4){const v=rnd()*255;img.data[i]=img.data[i+1]=img.data[i+2]=v;img.data[i+3]=rnd()<.5?10:0;}
  c.putImageData(img,0,0);runtime.grain=layer;return layer;
}
function paintBackground(g,W,H,mode='paper') {
  const night=mode==='night';
  g.save();g.setTransform(1,0,0,1,0,0);g.globalAlpha=1;g.filter='none';
  g.fillStyle=night?T.night:T.paper;g.fillRect(0,0,W,H);
  const v=g.createRadialGradient(W/2,H*.48,H*.35,W/2,H*.5,W*.72);
  v.addColorStop(0,night?'rgba(40,70,78,.22)':'rgba(255,253,246,.28)');v.addColorStop(1,night?'rgba(0,0,0,.32)':'rgba(120,96,50,.12)');
  g.fillStyle=v;g.fillRect(0,0,W,H);g.drawImage(grainLayer(W,H),0,0);g.restore();
}

// ---------------------------------------------------------------- stage
function screenBounds(g,b) {
  const m=g.getTransform();
  const p=[[b.x,b.y],[b.x+b.w,b.y],[b.x,b.y+b.h],[b.x+b.w,b.y+b.h]].map(([x,y])=>({x:m.a*x+m.c*y+m.e,y:m.b*x+m.d*y+m.f}));
  const xs=p.map(q=>q.x),ys=p.map(q=>q.y);
  return {x:Math.min(...xs),y:Math.min(...ys),w:Math.max(...xs)-Math.min(...xs),h:Math.max(...ys)-Math.min(...ys)};
}

function createDesignStage(g,course,{background='paper'}={}) {
  if(!runtime)throw new Error('Design runtime not installed: render.cjs and audit.cjs call installDesignRuntime(canvasModule) before drawing');
  const {width:W,height:H}=course;
  // Same 16:9 safe-zone contract as motion.cjs; the caption band stays clear but unpainted.
  const viewport={x:32,y:80,w:W-64,h:H-205},safe={x:40,y:88,w:W-80,h:H-221},CY=340;
  const items=[],checks=[];let quiet=0,transition=false;
  g.resetTransform();g.globalAlpha=1;g.filter='none';g.letterSpacing='0px';
  paintBackground(g,W,H,background);
  g.save();g.beginPath();g.rect(viewport.x,viewport.y,viewport.w,viewport.h);g.clip();

  function record(id,b,kind,owner=null) {
    if(quiet)return;
    if(items.some(x=>x.id===id))throw new Error('Duplicate audit ID: '+id);
    items.push({id,kind,owner,bounds:screenBounds(g,b),alpha:g.globalAlpha});
  }
  // Unregistered drawing. decor(): trails, grids, rings that carry no label or solid object.
  // transition(): a pan, iris or wipe frame; it is excluded from the geometry audit and the
  // audit reports how many such frames each lesson has.
  function decor(fn){quiet++;try{fn();}finally{quiet--;}}
  function inTransition(fn){transition=true;decor(fn);}
  // Model or timing assertions reported through the audit's mechanism-invariant channel.
  function check(id,passed,actual,expected){if(!checks.some(c=>c.id===id))checks.push({id,passed:passed===true,actual,expected});}
  // A template given its scene end asserts that the spoken span leaves room for its choreography.
  function fits(name,start,end,minimum){if(Number.isFinite(end))check('fit-'+name,end-start>=minimum,+(end-start).toFixed(3),'>= '+minimum+'s');}
  function view(cam,fn,{blur=0}={}) {
    g.save();g.setTransform(1,0,0,1,0,0);g.translate(W/2,CY);g.scale(cam.zoom,cam.zoom);g.translate(-cam.x,-cam.y);
    if(blur>.3)g.filter=`blur(${blur.toFixed(2)}px)`;fn();g.restore();
  }
  function fade(a,fn){if(a<=.002)return;g.save();g.globalAlpha*=Math.min(1,a);fn();g.restore();}
  function actor(id,b,draw,owner=null){record(id,b,'actor',owner);g.save();draw(g);g.restore();}

  function setFont(r){g.font=`${r.size}px "${FACES[r.face]}"`;g.letterSpacing=(r.track||0)+'px';}
  function measure(str,r){g.save();setFont(r);const w=g.measureText(String(str)).width-(r.track||0);g.restore();return w;}
  function text(id,str,x,y,{role:name='body',over,color=T.ink,align='left',blur=0,owner=null}={}) {
    const r=role(name,over),s=r.upper?String(str).toUpperCase():String(str),w=measure(s,r);
    const left=align==='center'?x-w/2:align==='right'?x-w:x;
    record(id,{x:left-2,y:y-r.size*.62,w:w+4,h:r.size*1.24},'label',owner);
    g.save();setFont(r);g.textAlign='left';g.textBaseline='middle';if(blur>.3)g.filter=`blur(${blur.toFixed(2)}px)`;
    g.fillStyle=color;g.fillText(s,left,y);g.restore();return w;
  }

  // motion.cjs-compatible label, so createIllustration(stage) from illustrations.cjs draws here in the system type.
  function label(id,str,x,y,{size=24,color=T.ink,owner=null,align='center',weight=600}={}) {
    return text(id,str,x,y,{role:'label',over:{face:weight>=700?'bold':weight>=600?'demi':'medium',size,track:0},color,align,owner});
  }

  // ------------------------------------------------ kinetic sentence
  function layout(str,{role:name='body',over,maxWidth=900,lineHeight}={}) {
    const r=role(name,over),words=String(str).split(/\s+/).filter(Boolean),space=measure(' ',r)*1.05;
    const lh=lineHeight||r.size*1.32,lines=[[]];let width=0;
    for(const w of words) {
      const ww=measure(w,r),line=lines.at(-1),lw=line.reduce((s,q)=>s+q.w,0)+space*line.length;
      if(line.length&&lw+ww>maxWidth)lines.push([]);
      lines.at(-1).push({text:w,w:ww});
    }
    const out=[];lines.forEach((line,li)=>{const lw=line.reduce((s,q)=>s+q.w,0)+space*(line.length-1);width=Math.max(width,lw);
      let x=0;for(const q of line){out.push({...q,line:li,x,lineWidth:lw});x+=q.w+space;}});
    return {r,words:out,lines:lines.length,lh,width,height:(lines.length-1)*lh+r.size*1.24};
  }
  // reveal: rise | blur | ghost | none. times[i] is word i's onset (use cues).
  // styles[i] = {color, mark:{p,color}, hidden} — hidden leaves the word's slot empty (it is being carried elsewhere).
  function sentence(id,str,x,y,{t,times,reveal='rise',dur=.5,align='left',color=T.ink,ghost=.17,styles={},owner=null,...opts}) {
    const L=layout(str,opts),top=y-(L.lines-1)*L.lh/2;
    const place=q=>({x:x+(align==='center'?-q.lineWidth/2:align==='right'?-q.lineWidth:0)+q.x,y:top+q.line*L.lh});
    const state=L.words.map((q,i)=>{
      const p=reveal==='none'?1:clamp((t-(times?.[i]??0))/dur);
      if(reveal==='ghost')return {a:1,fill:E.out(p),dy:0,blur:0};
      if(reveal==='blur')return {a:E.out(p),fill:1,dy:0,blur:(1-E.out(p))*9};
      return {a:E.out(clamp(p*1.6)),fill:1,dy:(1-E.outExpo(p))*L.r.size*.55,blur:(1-E.out(p))*5};
    });
    // Marks (highlighter) sit behind their word and own it.
    L.words.forEach((q,i)=>{const m=styles[i]?.mark;if(!m||m.p<=0)return;const at=place(q),h=L.r.size*1.36;
      marker(`${id}-mark${i}`,at.x-8,at.y-h/2,q.w+16,h,m.p,{color:m.color||T.gold,owner});});
    L.words.forEach((q,i)=>{const s=state[i],st=styles[i]||{},at=place(q);if(s.a<=.01||st.hidden)return;
      const own=st.mark&&st.mark.p>0?`${id}-mark${i}`:owner,c=st.color||color;
      if(reveal==='ghost')fade(ghost+(1-ghost)*s.fill,()=>text(`${id}-w${i}`,q.text,at.x,at.y,{role:opts.role,over:opts.over,color:c,owner:own}));
      else fade(s.a,()=>text(`${id}-w${i}`,q.text,at.x,at.y+s.dy,{role:opts.role,over:opts.over,color:c,blur:s.blur,owner:own}));
    });
    return {...L,place,words:L.words.map(q=>({...q,...place(q)}))};
  }

  // ------------------------------------------------ objects
  function roundRect(x,y,w,h,r){g.beginPath();g.roundRect(x,y,w,h,r);}
  function card(id,x,y,w,h,{fill=T.paperHi,radius=18,lift=1,stroke=T.rule,owner=null}={}) {
    actor(id,{x,y,w,h},()=>{g.shadowColor='rgba(60,40,10,.16)';g.shadowBlur=26*lift;g.shadowOffsetY=10*lift;
      roundRect(x,y,w,h,radius);g.fillStyle=fill;g.fill();g.shadowColor='transparent';
      if(stroke){g.lineWidth=1.2;g.strokeStyle=stroke;g.stroke();}},owner);
  }
  // Chips keep the same geometry while popping, so a row never shifts; the box is returned even before p>0.
  function chip(id,label,x,y,{p=1,role:name='label',fill=T.ink,color=T.white,padX:px=14,padY=8,radius=null,align='center',owner=null,dot=null}={}) {
    const padX=Math.max(px,4),r=role(name),w=measure(r.upper?label.toUpperCase():label,r)+(dot?18:0),bw=w+padX*2,bh=r.size+padY*2;
    const left=align==='center'?x-bw/2:align==='right'?x-bw:x,s=E.outBack(clamp(p)),box={x:left,y:y-bh/2,w:bw,h:bh};
    if(p<=0)return box;
    g.save();g.globalAlpha*=clamp(p*2.5);g.translate(left+bw/2,y);g.scale(s,s);g.translate(-(left+bw/2),-y);
    actor(id,{x:left,y:y-bh/2,w:bw,h:bh},()=>{roundRect(left,y-bh/2,bw,bh,radius??bh/2);g.fillStyle=fill;g.fill();
      if(dot){g.fillStyle=dot;g.beginPath();g.arc(left+padX+5,y,5,0,Math.PI*2);g.fill();}},owner);
    text(id+'-t',label,left+padX+(dot?18:0),y+1,{role:name,color,owner:id});
    g.restore();return box;
  }
  function marker(id,x,y,w,h,p,{color=T.gold,owner=null}={}) {
    if(p<=0)return;const e=E.inOut(clamp(p));
    actor(id,{x,y,w,h},()=>{g.globalAlpha*=.9;g.fillStyle=color;g.beginPath();
      g.moveTo(x,y+3);g.lineTo(x+w*e,y);g.lineTo(x+w*e-3,y+h);g.lineTo(x+2,y+h-2);g.closePath();g.fill();},owner);
  }
  // Odometer counter: tabular digits roll through their neighbours.
  function counter(id,value,x,y,{role:name='numeral',color=T.ink,align='center',prefix='',suffix='',owner=null}={}) {
    const r=role(name),lo=Math.floor(value+1e-6),frac=value-lo,a=prefix+lo+suffix,b=prefix+(lo+1)+suffix;
    const digit=measure('0',r)+(r.track||0),n=Math.max(a.length,b.length),w=n*digit-(r.track||0);
    const left=align==='center'?x-w/2:align==='right'?x-w:x;
    record(id,{x:left-2,y:y-r.size*.62,w:w+4,h:r.size*1.24},'label',owner);
    g.save();g.beginPath();g.rect(left-4,y-r.size*.62,w+8,r.size*1.24);g.clip();setFont(r);g.letterSpacing='0px';g.textBaseline='middle';g.fillStyle=color;
    // Each glyph is centred in a fixed cell, so narrow figures such as 1 read as tabular.
    const A=a.padStart(n,' '),B=b.padStart(n,' '),put=(ch,cx,yy)=>g.fillText(ch,cx+(digit-(r.track||0)-g.measureText(ch).width)/2,yy);
    for(let i=0;i<n;i++){const cx=left+i*digit;
      if(A[i]===B[i]||frac<.001){put(A[i],cx,y);continue;}
      const off=E.inOut(frac)*r.size*1.1;put(A[i],cx,y-off);put(B[i],cx,y-off+r.size*1.1);}
    g.restore();return w;
  }

  // ------------------------------------------------ annotation (unregistered strokes)
  function partial(points,p,{color=T.ink,width=3,dash=null,alpha=1}={}) {
    if(p<=0||points.length<2)return null;
    const len=points.slice(1).map((q,i)=>Math.hypot(q[0]-points[i][0],q[1]-points[i][1])),total=len.reduce((s,v)=>s+v,0);
    let left=total*clamp(p),end=points[0];g.save();g.globalAlpha*=alpha;g.strokeStyle=color;g.lineWidth=width;g.lineCap='round';g.lineJoin='round';
    if(dash)g.setLineDash(dash);g.beginPath();g.moveTo(...points[0]);
    for(let i=0;i<len.length&&left>0;i++){const k=Math.min(1,left/(len[i]||1));end=[lerp(points[i][0],points[i+1][0],k),lerp(points[i][1],points[i+1][1],k)];g.lineTo(...end);left-=len[i];}
    g.stroke();g.restore();return end;
  }
  const bezier=(a,c,b,n=40)=>Array.from({length:n+1},(_,i)=>{const u=i/n;return [(1-u)**2*a[0]+2*(1-u)*u*c[0]+u*u*b[0],(1-u)**2*a[1]+2*(1-u)*u*c[1]+u*u*b[1]];});
  function arrow(from,to,p,{bend=-.25,color=T.ink,width=2.5,head=12}={}) {
    const mx=(from[0]+to[0])/2,my=(from[1]+to[1])/2,dx=to[0]-from[0],dy=to[1]-from[1];
    const pts=bezier(from,[mx-dy*bend,my+dx*bend],to),end=partial(pts,p,{color,width});
    if(!end||p<.92)return;const k=Math.max(1,Math.floor(pts.length*clamp(p))-2),q=pts[k-1],ang=Math.atan2(end[1]-q[1],end[0]-q[0]);
    partial([[end[0]-head*Math.cos(ang-.5),end[1]-head*Math.sin(ang-.5)],end,[end[0]-head*Math.cos(ang+.5),end[1]-head*Math.sin(ang+.5)]],1,{color,width});
  }
  function scribble(cx,cy,rx,ry,p,{color=T.accent,width=3.2,seed=3,turns=1.12}={}) {
    const pts=[],n=90,a0=-2.2;
    for(let i=0;i<=n;i++){const u=i/n,a=a0+u*Math.PI*2*turns,j=1+.035*Math.sin(u*9+seed)+.05*u;pts.push([cx+Math.cos(a)*rx*j,cy+Math.sin(a)*ry*j]);}
    partial(pts,E.inOut(clamp(p)),{color,width});
  }
  function underline(x1,x2,y,p,{color=T.accent,width=4}={}){partial(bezier([x1,y+2],[(x1+x2)/2,y-5],[x2,y]),E.inOut(clamp(p)),{color,width});}
  function strike(x1,x2,y,p,{color=T.accent,width=3.5}={}){partial([[x1-4,y+3],[x2+4,y-3]],E.inOut(clamp(p)),{color,width});}
  function dotGrid(cx,cy,w,h,{gap=34,color=T.rule,alpha=.55}={}) {
    decor(()=>{g.save();g.globalAlpha*=alpha;g.fillStyle=color;
      for(let x=Math.floor((cx-w/2)/gap)*gap;x<cx+w/2;x+=gap)for(let y=Math.floor((cy-h/2)/gap)*gap;y<cy+h/2;y+=gap)g.fillRect(x-1.2,y-1.2,2.4,2.4);g.restore();});
  }

  // ------------------------------------------------ transitions (screen space, full frame)
  // Leave the content clip for full-frame transitions; call only at the top level of a frame.
  function unclipped(fn){g.restore();try{fn();}finally{g.save();g.beginPath();g.rect(viewport.x,viewport.y,viewport.w,viewport.h);g.clip();}}
  // Two-phase iris: an accent disc swells from a meaningful point, then the next scene opens inside it.
  function iris(cx,cy,p,fn,{mode='paper',color=T.accent}={}) {
    if(p<=0)return;const R=Math.hypot(Math.max(cx,W-cx),Math.max(cy,H-cy))+4,p1=E.inOut(clamp(p*1.8)),p2=E.inOut(clamp((p-.42)/.58));
    g.save();g.setTransform(1,0,0,1,0,0);g.fillStyle=color;g.beginPath();g.arc(cx,cy,Math.max(.5,R*p1),0,Math.PI*2);g.fill();g.restore();
    if(p2<=0)return;
    g.save();g.setTransform(1,0,0,1,0,0);g.beginPath();g.arc(cx,cy,Math.max(.5,R*p2),0,Math.PI*2);g.clip();paintBackground(g,W,H,mode);fn();g.restore();
  }
  // Slanted wipe: the next scene's panel sweeps in from the right.
  function wipe(p,fn,{mode='paper',slant=180}={}) {
    if(p<=0)return;const e=E.inOut(clamp(p)),x=lerp(W+slant,-slant,e);
    g.save();g.setTransform(1,0,0,1,0,0);g.beginPath();g.moveTo(x,0);g.lineTo(W+slant,0);g.lineTo(W+slant,H);g.lineTo(x-slant,H);g.closePath();g.clip();
    paintBackground(g,W,H,mode);fn();g.restore();
  }

  return {g,W,H,T,E,safe,viewport,record,decor,transition:inTransition,check,fits,view,fade,actor,text,label,measure,layout,sentence,card,chip,marker,counter,
    partial,bezier,arrow,scribble,underline,strike,dotGrid,iris,wipe,roundRect,unclipped,
    finish(invariants={}){g.restore();g.filter='none';g.letterSpacing='0px';
      return {items,safe,viewport,invariants:{...invariants,checks:[...(invariants.checks||[]),...checks]},transition};}};
}

module.exports={T,TYPE,FACES,FONT_FILES,E,role,clamp,lerp,seg,wordTimes,createCues,cameraAt,extendTheme,installDesignRuntime,createDesignStage,paintBackground};
