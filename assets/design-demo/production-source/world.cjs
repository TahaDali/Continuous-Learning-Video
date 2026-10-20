'use strict';
// Design-system demonstration: the starter's fictional conserved transfer, staged with
// templates, focus, a travelling camera and motivated transitions. Every time below derives
// from scene spans and narration cues, so the same world follows measured narration after
// narrate.py rewrites the spans; nothing is a hard-coded second. Replace it for a real course.
const {T,E,role,seg,clamp,lerp,cameraAt,createCues,createDesignStage}=require('./design.cjs');
const tpl=require('./templates.cjs');

// One continuous world canvas. The camera pans R1 -> R2 -> R3; an iris opens R4 and a wipe opens R5.
const R1={x:640,y:340},R2={x:2040,y:340},R3={x:2040,y:1240},R4={x:640,y:1240},R5={x:640,y:2140};

// Mechanism geometry (world units). A 130 px vessel holds 120 units.
const M={cardA:{x:195,y:192,w:280,h:300},cardB:{x:805,y:192,w:280,h:300},vessel:{dx:60,dy:70,w:160,h:130},
  from:[392,225],ctrl:[640,190],to:[900,225]};
const level=v=>v*M.vessel.h/120;
const bez=(a,c,b,u)=>[(1-u)**2*a[0]+2*(1-u)*u*c[0]+u*u*b[0],(1-u)**2*a[1]+2*(1-u)*u*c[1]+u*u*b[1]];

// The timeline is computed once per lesson object from its scenes and cues.
const plans=new WeakMap();
function planFor(lesson) {
  if(plans.has(lesson))return plans.get(lesson);
  const cue=createCues(lesson),sc=Object.fromEntries(lesson.scenes.map(s=>[s.id,s]));
  const exitAt=cue('claim','hold'),carryEnd=Math.max(sc.claim.end,exitAt+.8);
  const dep=[cue('transfer','leave'),cue('transfer','leave')+.8];
  const land0=Math.max(cue('transfer','arrive'),dep[1]+1.4),transit=[dep[1],land0],land=[land0,land0+.8];
  // Transitions begin in the closing pause of a scene, so its last reveal stays readable.
  const at=s=>[s.start-.3,s.start+.7],pans=[at(sc.contrast),at(sc.series)],iris=at(sc.method),wipe=at(sc.check);
  const keys=[{t:0,...R1,zoom:1},{t:carryEnd,...R1,zoom:1.03},{t:carryEnd+.8,...R1,zoom:1},
    {t:dep[0]-.2,...R1,zoom:1},{t:dep[0]+.6,x:520,y:R1.y,zoom:1.06},{t:transit[0]+.2,x:520,y:R1.y,zoom:1.06},
    {t:transit[1]-.2,x:760,y:R1.y,zoom:1.06},{t:land[1],x:760,y:R1.y,zoom:1.06},{t:land[1]+1,...R1,zoom:1},
    {t:pans[0][0],...R1,zoom:1.02},{t:pans[0][1],...R2,zoom:1},{t:pans[1][0],...R2,zoom:1.02},
    {t:pans[1][1],...R3,zoom:1},{t:iris[0],...R3,zoom:1.025}];
  // Narration can compress a scene; keep keyframes ordered rather than reversing the camera.
  for(let i=1;i<keys.length;i++)keys[i].t=Math.max(keys[i].t,keys[i-1].t+.05);
  const plan={sc,cue,exitAt,carryEnd,dep,transit,land,pans,iris,wipe,keys,
    build:[cue('transfer','account',1)-.15,cue('transfer','account',2)-.15],route:cue('transfer','now')-.2,
    counted:cue('transfer','counted'),never:cue('transfer','never')};
  plans.set(lesson,plan);return plan;
}

function balances(P,t) {
  const dep=seg(t,P.dep[0],P.dep[1]-P.dep[0],E.inOut),land=seg(t,P.land[0],P.land[1]-P.land[0],E.inOut);
  const A=100-10*dep,B=50+10*land;return {A,B,flight:(100-A)-(B-50)};
}

function vessel(S,id,card,value,{fill,line,owner}) {
  const x=card.x+M.vessel.dx,y=card.y+M.vessel.dy,{w,h}=M.vessel,top=y+h-level(value);
  S.actor(id,{x,y,w,h},g=>{
    g.save();g.beginPath();g.roundRect(x,y,w,h,[0,0,16,16]);g.clip();
    g.fillStyle=fill;g.fillRect(x,top,w,y+h-top);g.globalAlpha*=.55;g.fillStyle=T.white;g.fillRect(x,top,w,3);g.restore();
    g.strokeStyle=T.ink;g.lineWidth=3;g.lineJoin='round';g.beginPath();g.moveTo(x,y-6);g.lineTo(x,y+h-16);g.quadraticCurveTo(x,y+h,x+16,y+h);
    g.lineTo(x+w-16,y+h);g.quadraticCurveTo(x+w,y+h,x+w,y+h-16);g.lineTo(x+w,y-6);g.stroke();
    g.strokeStyle=line;g.lineWidth=1;for(let u=30;u<=120;u+=30){const yy=y+h-level(u);g.beginPath();g.moveTo(x+w-14,yy);g.lineTo(x+w-3,yy);g.stroke();}
  },owner);
}

function account(S,side,value,alpha,build) {
  const card=side==='a'?M.cardA:M.cardB,cx=card.x+card.w/2,pop=E.outBack(clamp(build));
  if(build<=0)return;
  S.fade(alpha*clamp(build*2),()=>{
    const g=S.g;g.save();g.translate(cx,card.y+card.h);g.scale(1,lerp(.92,1,pop));g.translate(-cx,-(card.y+card.h));
    S.card('card-'+side,card.x,card.y,card.w,card.h);
    // Kickers sit on the outer corners so the inner edges stay free for the route.
    S.text(side+'-kicker','Account '+side.toUpperCase(),side==='a'?card.x+30:card.x+card.w-30,card.y+30,{role:'kicker',color:T.inkSoft,align:side==='a'?'left':'right',owner:'card-'+side});
    vessel(S,side+'-vessel',card,value*seg(build,.35,.65,E.out),{fill:side==='a'?T.tealSoft:T.goldSoft,line:side==='a'?T.teal:T.goldInk,owner:'card-'+side});
    S.fade(seg(build,.4,.6),()=>S.counter(side+'-value',value,cx,card.y+250,{role:'numeral',owner:'card-'+side}));
    g.restore();
  });
}

// A term that opens horizontally registers exactly its visible width.
function clippedLabel(S,id,str,x,y,visible,{role:name,color}) {
  const r=role(name);if(visible<=.5)return;
  S.record(id,{x,y:y-r.size*.62,w:visible,h:r.size*1.24},'label');
  S.g.save();S.g.beginPath();S.g.rect(x-2,y-r.size,visible+4,r.size*2);S.g.clip();S.decor(()=>S.text(id,str,x,y,{role:name,color}));S.g.restore();
}

// 90 + 10 in transit + 60 = 150: the transit term opens only while the quantity travels.
function equation(S,P,t,{A,B,flight}) {
  const show=seg(t,P.route+.2,.5),open=seg(t,P.dep[0],.6,E.inOut)*(1-seg(t,P.land[1]-.1,.6,E.inOut));if(show<=0)return;
  const r=role('title'),gap=16,terms=[
    {id:'eq-a',s:String(Math.round(A)),o:1,c:T.ink},{id:'eq-p1',s:'+',o:1,c:T.mute},
    {id:'eq-f',s:`${Math.round(flight)} in transit`,o:open,c:T.accent},{id:'eq-p2',s:'+',o:open,c:T.mute},
    {id:'eq-b',s:String(Math.round(B)),o:1,c:T.ink},{id:'eq-eq',s:'=',o:1,c:T.mute},{id:'eq-t',s:'150',o:1,c:T.teal}];
  for(const q of terms)q.w=S.measure(q.s,r);
  const total=terms.reduce((s,q)=>s+(q.w+gap)*q.o,0)-gap;let x=640-total/2;
  S.fade(show,()=>{for(const q of terms){
    if(q.id==='eq-f'&&q.o>.02)S.decor(()=>S.marker('eq-mark',x-8,540-r.size*.7,q.w*q.o+16,r.size*1.4,seg(t,P.counted,.5),{color:T.accentSoft}));
    S.fade(q.o<1?clamp(q.o*1.4):1,()=>clippedLabel(S,q.id,q.s,x,540,q.w*q.o,{role:'title',color:q.c}));x+=(q.w+gap)*q.o;}});
}

function mechanism(S,P,t) {
  const v=balances(P,t),[d0,d1]=P.dep,[t0,t1]=P.transit,[l0,l1]=P.land,span=t1-t0;
  // Focus hands over: B dims while the quantity leaves A, brightens, then A dims as it lands.
  const dimB=1-.62*seg(t,d0-.2,.4)*(1-seg(t,t0+.4*span,.5)),dimA=1-.62*seg(t,t0+.55*span,.5)*(1-seg(t,l1,.5));
  // The total badge receives the number carried from the claim.
  const badge=seg(t,P.carryEnd,.35,E.outBack);
  if(badge>0)S.fade(clamp(badge*2),()=>{const g=S.g,k=lerp(.8,1,clamp(badge));g.save();g.translate(640,140);g.scale(k,k);g.translate(-640,-140);
    S.card('badge',545,112,190,56,{radius:28,lift:.6});S.text('badge-k','Total',565,141,{role:'kicker',color:T.inkSoft,owner:'badge'});
    S.counter('badge-v',150,700,141,{role:'numeralSm',color:T.teal,owner:'badge'});g.restore();});
  account(S,'a',v.A,dimA,seg(t,P.build[0],1.1,E.linear));account(S,'b',v.B,dimB,seg(t,P.build[1],1.1,E.linear));
  // The route draws before anything travels on it.
  S.partial(Array.from({length:41},(_,i)=>bez(M.from,M.ctrl,M.to,i/40)),seg(t,P.route,.8,E.inOut),{color:T.rule,width:2.5,dash:[2,9]});
  // Token: rises out of A as A drains, rides the route with a trail, sinks into B as B fills.
  const vA=M.cardA.y+M.vessel.dy+M.vessel.h,vB=M.cardB.y+M.vessel.dy+M.vessel.h;
  let pos=null,scale=1,alpha=1;
  if(t>=d0&&t<t0){const p=seg(t,d0,d1-d0,E.inOut);pos=[M.from[0],lerp(vA-level(100)+30,M.from[1],E.outBack(p))];scale=lerp(.4,1,p);}
  else if(t>=t0&&t<l0){const u=seg(t,t0,span,E.inOut);pos=bez(M.from,M.ctrl,M.to,u);
    S.decor(()=>{for(let k=1;k<=5;k++){const w=seg(t-k*.05,t0,span,E.inOut),q=bez(M.from,M.ctrl,M.to,w);
      S.g.save();S.g.globalAlpha*=.12-k*.018;S.g.fillStyle=T.gold;S.g.beginPath();S.g.arc(q[0],q[1],28,0,Math.PI*2);S.g.fill();S.g.restore();}});}
  else if(t>=l0&&t<l1){const p=seg(t,l0,l1-l0,E.inOut);pos=[M.to[0],lerp(M.to[1],vB-level(60)+20,E.in(p))];scale=lerp(1,.45,p);alpha=1-seg(t,l1-.25,.25);}
  if(pos)S.fade(alpha,()=>{const r=28*scale,[x,y]=pos;
    S.actor('token',{x:x-r,y:y-r,w:2*r,h:2*r},g=>{g.shadowColor='rgba(80,50,0,.25)';g.shadowBlur=12;g.shadowOffsetY=5;g.fillStyle=T.gold;g.beginPath();g.arc(x,y,r,0,Math.PI*2);g.fill();
      g.shadowColor='transparent';g.strokeStyle=T.ink;g.lineWidth=2.5;g.stroke();});
    if(scale>.7)S.text('token-v',String(Math.round(v.flight)),x,y+1,{role:'label',over:{face:'heavy',size:21},align:'center',owner:'token'});});
  // A landing ring confirms arrival without a success label.
  const ring=seg(t,l0+.1,.7,E.out);if(ring>0&&ring<1)S.decor(()=>{S.g.save();S.g.globalAlpha*=.5*(1-ring);S.g.strokeStyle=T.gold;S.g.lineWidth=3;
    S.g.beginPath();S.g.ellipse(945,vB-level(60),20+60*ring,6+14*ring,0,0,Math.PI*2);S.g.stroke();S.g.restore();});
  equation(S,P,t,v);
  // Hand-drawn emphasis on what never changed, timed to the spoken word.
  S.scribble(640,140,118,42,seg(t,P.never-.1,.8,E.inOut),{color:T.accent});
  S.fade(seg(t,P.never+.5,.5),()=>S.text('note-total','never changed',790,122,{role:'accentSm',color:T.accent}));
  S.arrow([788,140],[764,146],seg(t,P.never+.8,.4,E.inOut),{bend:.4,color:T.accent,width:2.2,head:8});
  return v;
}

function designedTransfer(g,lesson,t,course) {
  const P=planFor(lesson),{sc,cue}=P,inside=(w)=>t>=w[0]&&t<w[1];
  const S=createDesignStage(g,course,{background:t>=P.wipe[1]?'night':'paper'});
  const cam=cameraAt(t,P.keys),blur=Math.min(3,cam.speed/700);
  let v={A:100,B:50,flight:0},anchor=[R3.x+380,R3.y-125];

  const R1scene=()=>{
    if(t<sc.open.end)tpl.opener(S,t,{x:150,y:250,start:sc.open.start,end:sc.open.end,kicker:'Fictional demonstration',
      title:'Money moves.',accent:"It doesn't vanish.",agenda:['1  Find the total','2  Follow the quantity','3  Check the balance'],
      at:{title:cue.phrase('open','Money moves.'),accent:cue.phrase('open',"It doesn't vanish."),agenda:[cue('open','find'),cue('open','follow'),cue('open','check')]}});
    if(t>=sc.claim.start&&t<P.carryEnd) {
      const claim=tpl.statement(S,t,{x:640,y:320,start:sc.claim.start,end:sc.claim.end,text:'Two accounts share one fixed total of 150 units.',emphasis:'150',
        times:cue.phrase('claim','Two accounts share one fixed total of 150 units.'),exitAt:P.exitAt});
      tpl.carry(S,t,{id:'carry-150',text:'150',from:[claim.emphasis.x+claim.emphasis.w/2,claim.emphasis.y],to:[700,141],
        start:P.exitAt,end:P.carryEnd,fromSize:claim.emphasis.size});
    }
    if(t>=P.carryEnd-.2)v=mechanism(S,P,t);
  };
  const R2scene=()=>{S.dotGrid(R2.x,R2.y,1500,800);const s=sc.contrast;
    tpl.compare(S,t,{x:R2.x,y:R2.y,start:s.start,end:s.end,title:'Balances changed.',subtitle:'The total did not.',focusAt:cue('contrast','did'),
      left:{title:'Changed',dot:T.accent,rows:[{name:'Account A',from:100,to:90},{name:'Account B',from:50,to:60}]},
      right:{title:'Conserved',dot:T.teal,rows:[{name:'Total',from:150,to:150,check:true}]},
      takeaway:'Check the total before you trust the movement.',
      at:{title:cue.phrase('contrast','Balances changed.'),subtitle:cue.phrase('contrast','The total did not.',{after:cue('contrast','rose')}),
        left:[cue('contrast','fell')-.25,cue('contrast','rose')-.25],right:[cue('contrast','total')],
        takeaway:cue.phrase('contrast','Check the total before you trust the movement.',{after:cue('contrast','not')})}});};
  const R3scene=()=>{S.dotGrid(R3.x,R3.y,1500,800);const s=sc.series,b=cue('series','balances');
    anchor=tpl.lineStory(S,t,{x:R3.x,y:R3.y,start:s.start,end:s.end,kicker:'Fictional series',title:'Four transfers later',
      labels:['Start','T1','T2','T3','T4'],focusAt:cue('series','line'),note:'flat while balances swing',
      series:[{id:'a',name:'A',color:T.teal,values:[100,90,115,70,85]},{id:'b',name:'B',color:T.goldInk,values:[50,60,35,80,65]}],
      invariant:{name:'Total 150',value:150},
      at:{title:cue.phrase('series','Four transfers later',{after:cue('series','times')}),series:[b,b+.35],invariant:cue('series','total')}}).anchor;};
  const R4cam={...R4,zoom:1+.02*seg(t,sc.method.start,sc.method.end-sc.method.start,E.inOut)};
  const R5cam={...R5,zoom:1+.015*seg(t,sc.check.start,sc.check.end-sc.check.start,E.inOut)};
  const R4scene=()=>{const s=sc.method;tpl.stepper(S,t,{x:R4.x,y:R4.y,start:s.start,end:s.end,title:'Read any transfer',accent:'in three steps.',
    stepAt:[cue('method','find'),cue('method','follow'),cue('method','check')],
    steps:[{title:'Find the total',detail:'150 units'},{title:'Follow the moving quantity',detail:'10 in transit'},{title:'Check the balance',detail:'90 + 60 = 150'}],
    at:{title:cue.phrase('method','Read any transfer'),accent:cue.phrase('method','in three steps.')}});};
  const R5scene=()=>{const s=sc.check,still=cue('check','still');
    tpl.question(S,t,{x:R5.x,y:R5.y,start:s.start,end:s.end,kicker:'Check yourself',prompt:'If 25 units move from B to A, what is the total?',
      options:['125','150','175'],correct:1,revealAt:still,reason:'Moving units changes balances, not the total.',
      at:{kicker:cue('check','check'),prompt:cue.phrase('check','If 25 units move from B to A, what is the total?'),
        reason:cue.phrase('check','Moving units changes balances, not the total.',{after:still})}});};

  if(t<P.iris[0]) {
    // Continuous canvas: regions draw in world space and the camera travels between them.
    const pan=P.pans.some(inside),draw=()=>{if(t<P.pans[0][1])R1scene();if(t>=P.pans[0][0]&&t<P.pans[1][1])R2scene();if(t>=P.pans[1][0])R3scene();};
    S.view(cam,()=>pan?S.transition(draw):draw(),{blur});
  } else if(t<P.wipe[0]) {
    // Iris from the invariant line's end: the method grows out of the conserved total.
    if(t<P.iris[1]) {
      const c3=cameraAt(P.iris[0],P.keys);S.view(c3,()=>S.transition(R3scene));
      const sx=640+(anchor[0]-c3.x)*c3.zoom,sy=340+(anchor[1]-c3.y)*c3.zoom;
      S.transition(()=>S.unclipped(()=>S.iris(sx,sy,seg(t,P.iris[0],P.iris[1]-P.iris[0],E.linear),()=>S.view(R4cam,R4scene))));
    } else S.view(R4cam,R4scene);
  } else if(t<P.wipe[1]) {
    S.transition(()=>{S.view(R4cam,R4scene);S.unclipped(()=>S.wipe(seg(t,P.wipe[0],P.wipe[1]-P.wipe[0],E.linear),()=>S.view(R5cam,R5scene),{mode:'night'}));});
  } else S.view(R5cam,R5scene);

  tpl.progressRail(S,t,{steps:['Find the total','Follow the quantity','Check the balance'],at:[sc.claim.start,sc.transfer.start,sc.contrast.start],
    from:sc.open.end-.6,until:P.iris[0]-.7});
  return S.finish({totalUnits:v.A+v.flight+v.B,expectedTotal:150});
}

function draw(g,lesson,t,course) {
  if(lesson.visual==='designed-transfer')return designedTransfer(g,lesson,t,course);
  throw new Error(`No authored world for visual: ${lesson.visual}`);
}
module.exports={draw};
