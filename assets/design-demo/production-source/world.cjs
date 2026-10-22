'use strict';
// Design-system demonstration: the starter's fictional conserved transfer, staged with
// templates, focus, a travelling camera and motivated transitions. Every time below derives
// from scene spans and narration cues, so the same world follows measured narration after
// narrate.py rewrites the spans; nothing is a hard-coded second. It also makes the choices a
// real course makes once (a state code, a recurring cast, the fiction badge's windows) and shows
// a reframing push, spoken numbers and a practice panel with a picture. Replace it for a real course.
const {T,E,role,seg,clamp,lerp,cameraAt,fitCamera,beforePush,orderKeys,planner,world,spoken,stepValue,talking,
  defineStates,createDesignStage}=require('./design.cjs');
const tpl=require('./templates.cjs');
const {defineCast,cast}=require('./illustrations.cjs');

// The course's state code, defined once: a unit is held in an account or travels between two.
// Hatched means not yet arrived. Colours come from tokens: a world never writes a colour literal.
defineStates({held:{color:T.blue,soft:T.blueSoft,label:'Held'},transit:{color:T.goldInk,label:'In transit',treatment:'hatched'}});
// The recurring cast, defined once: the clerk looks the same wherever a lesson stages her.
defineCast({clerk:{name:'Mira',role:'Clerk',skin:'skin4',hair:'hairBlack',style:'bun',top:'cardigan',topColor:'sage',inner:'white',
  bottom:'navy',glasses:true}});

// One continuous world canvas. The camera pans R1 -> R2 -> R3; an iris opens R4 and a wipe opens R5.
const R1={x:640,y:340},R2={x:2040,y:340},R3={x:2040,y:1240},R4={x:640,y:1240},R5={x:640,y:2140};

// Mechanism geometry (world units). A 130 px vessel holds 120 units. Each card names its account
// under the vessel, so the route can run just above the vessel rims and under the total badge
// without the travelling quantity crossing a label.
const M={cardA:{x:195,y:192,w:280,h:320},cardB:{x:805,y:192,w:280,h:320},vessel:{dx:60,dy:40,w:160,h:130},
  from:[405,210],ctrl:[640,200],to:[875,210],legend:[215,135],
  // The reframing push frames the route and the ledger set under it, between the cards.
  focus:{x:380,y:170,w:520,h:260},ledger:{x:500,width:280,ys:[312,360,408]}};
const level=v=>v*M.vessel.h/120;
// A gentle ease for the long journey: the units are visibly travelling soon after they leave.
const glide=x=>x<.5?2*x*x:1-2*(1-x)*(1-x);
const bez=(a,c,b,u)=>[(1-u)**2*a[0]+2*(1-u)*u*c[0]+u*u*b[0],(1-u)**2*a[1]+2*(1-u)*u*c[1]+u*u*b[1]];

// The timeline is computed once per lesson object from its scenes and cues.
const planFor=planner(({cue,sc,win})=>{
  const exitAt=cue('claim','hold'),carryEnd=Math.max(sc.claim.end,exitAt+.8);
  const leave=cue('transfer','leave'),dep=[leave,leave+.8];
  const land0=Math.max(cue('transfer','arrive'),dep[1]+1.4),transit=[dep[1],land0],land=[land0,land0+.8];
  // The in-transit term opens as the units leave and closes as they land; each balance figure steps
  // when its term is half open, so the line always adds up.
  const swap=[dep[0]+.2,land[0]+.3];
  // A reframing push (fitCamera) follows the units in as they travel and comes back out as they
  // arrive. A push is not a transition: whatever it would carry off frame fades first
  // (beforePush, S.onScreen) and returns after it.
  const in0=Math.max(transit[0],cue('transfer','while')-.3),push=[in0,in0+.7],back0=Math.max(push[1]+1.6,land0-.8),back=[back0,back0+.8];
  // Transitions begin in the closing pause of a scene, so its last reveal stays readable.
  const pans=[win(sc.contrast),win(sc.series)],iris=win(sc.method),wipe=win(sc.check);
  const wide={...R1,zoom:1},near=fitCamera(M.focus,{maxZoom:1.3});
  // A slow push stays a hand-written zoom of at most 1.06; narration can compress a scene, so keys stay ordered.
  const keys=orderKeys([{t:0,...wide},{t:carryEnd,...R1,zoom:1.03},{t:carryEnd+.8,...wide},{t:push[0],...wide},{t:push[1],...near},
    {t:back[0],...near},{t:back[1],...wide},{t:pans[0][0],...R1,zoom:1.02},{t:pans[0][1],...R2,zoom:1},{t:pans[1][0],...R2,zoom:1.02},
    {t:pans[1][1],...R3,zoom:1},{t:iris[0],...R3,zoom:1.025}]);
  return {sc,cue,exitAt,carryEnd,dep,transit,land,swap,push,back,pans,iris,wipe,keys,
    build:[cue('transfer','account',1)-.15,cue('transfer','account',2)-.15],route:cue('transfer','now')-.2,
    // Spoken numbers: a balance counts up while its figure is said ("holds 100"); "holds" is said
    // twice in the scene, so each cue names its occurrence.
    said:{a:[cue('transfer','holds',1),cue('transfer','100')],b:[cue('transfer','holds',2),cue('transfer','50')]},
    still:cue('transfer','still',1),counted:cue('transfer','counted'),ten:cue('transfer','ten',2),then:cue('transfer','then'),never:cue('transfer','never'),
    // The badge is on over invented figures and over the practice panel, and off over the opener's
    // general claim and the general method: the windows split around the method, never one window
    // left on across it.
    fiction:[[sc.claim.start,iris[0]+.4],[wipe[0],Infinity]],
    mira:cue('check','mira'),ask:[cue('check','if'),cue.end('check','total',1)],units:cue('check','25'),move:cue('check','move'),
    reveal:cue('check','still')};
});

function balances(P,t) {
  const dep=seg(t,P.dep[0],P.dep[1]-P.dep[0],E.inOut),land=seg(t,P.land[0],P.land[1]-P.land[0],E.inOut);
  const A=100-10*dep,B=50+10*land;return {A,B,flight:(100-A)-(B-50)};
}

// A vessel holds its units in the held state's colours.
function vessel(S,id,card,value,{owner}) {
  const x=card.x+M.vessel.dx,y=card.y+M.vessel.dy,{w,h}=M.vessel,top=y+h-level(value);
  S.actor(id,{x,y,w,h},g=>{
    g.save();g.beginPath();g.roundRect(x,y,w,h,[0,0,16,16]);g.clip();
    g.fillStyle=T.heldSoft;g.fillRect(x,top,w,y+h-top);g.globalAlpha*=.55;g.fillStyle=T.white;g.fillRect(x,top,w,3);g.restore();
    g.strokeStyle=T.ink;g.lineWidth=3;g.lineJoin='round';g.beginPath();g.moveTo(x,y-6);g.lineTo(x,y+h-16);g.quadraticCurveTo(x,y+h,x+16,y+h);
    g.lineTo(x+w-16,y+h);g.quadraticCurveTo(x+w,y+h,x+w,y+h-16);g.lineTo(x+w,y-6);g.stroke();
    g.strokeStyle=T.held;g.lineWidth=1;for(let u=30;u<=120;u+=30){const yy=y+h-level(u);g.beginPath();g.moveTo(x+w-14,yy);g.lineTo(x+w-3,yy);g.stroke();}
  },owner);
}

// An account card: a vessel over a stacked callout (the account, then its balance). The balance
// counts up through round steps while its figure is spoken (spoken(..., {mode:'count'})) and the
// vessel fills with it; afterwards the vessel follows the model and the figure steps to each
// result. The figure fades with S.onScreen before the push carries it to the frame edge.
function account(S,P,t,side,{level:model,shown:result},alpha,build) {
  const card=side==='a'?M.cardA:M.cardB,cx=card.x+card.w/2,pop=E.outBack(clamp(build)),said=side==='a'?100:50;
  if(build<=0)return;
  const n=spoken(t,said,P.said[side],{mode:'count'}),counting=n!==null&&n<said;
  S.fade(alpha*clamp(build*2),()=>{
    const g=S.g;g.save();g.translate(cx,card.y+card.h);g.scale(1,lerp(.92,1,pop));g.translate(-cx,-(card.y+card.h));
    S.card('card-'+side,card.x,card.y,card.w,card.h);
    vessel(S,side+'-vessel',card,n===null?0:counting?n:model,{owner:'card-'+side});
    S.callout(side+'-bal','Account '+side.toUpperCase(),n===null?'':String(counting?n:result),cx,card.y+card.h-108,{layout:'stack',align:'center',
      keyRole:'kicker',keyColor:T.inkSoft,valueRole:'numeral',owner:'card-'+side,
      valueP:n===null?0:S.onScreen({x:card.x,y:card.y+card.h-96,w:card.w,h:96})});
    g.restore();
  });
}

// A term that opens horizontally registers exactly its visible width.
function clippedLabel(S,id,str,x,y,visible,{role:name,color}) {
  const r=role(name);if(visible<=.5)return;
  S.record(id,{x,y:y-r.size*.62,w:visible,h:r.size*1.24},'label');
  S.g.save();S.g.beginPath();S.g.rect(x-2,y-r.size,visible+4,r.size*2);S.g.clip();S.decor(()=>S.text(id,str,x,y,{role:name,color}));S.g.restore();
}

// 90 + 10 in transit + 50 = 150: the transit term opens only while the quantity travels. The push
// would carry the line off frame, so beforePush fades it before the push and returns it after.
// Figures step to each result; they never count through values the narration does not say.
function equation(S,P,t,{A,B,flight}) {
  const show=seg(t,P.route+.2,.5)*beforePush(t,[P.push[0],P.back[1]]),open=seg(t,P.swap[0],.6,E.inOut)*(1-seg(t,P.swap[1],.6,E.inOut));
  if(show<=0)return;
  const r=role('title'),gap=16,terms=[
    {id:'eq-a',s:String(A),o:1,c:T.ink},{id:'eq-p1',s:'+',o:1,c:T.mute},
    {id:'eq-f',s:`${flight} in transit`,o:open,c:T.transit},{id:'eq-p2',s:'+',o:open,c:T.mute},
    {id:'eq-b',s:String(B),o:1,c:T.ink},{id:'eq-eq',s:'=',o:1,c:T.mute},{id:'eq-t',s:'150',o:1,c:T.teal}];
  for(const q of terms)q.w=S.measure(q.s,r);
  const total=terms.reduce((s,q)=>s+(q.w+gap)*q.o,0)-gap;let x=640-total/2;
  // A term's type shows only once it is more than half open, when the balances have stepped.
  S.fade(show,()=>{for(const q of terms){S.fade(q.o<1?clamp((q.o-.5)*2.4):1,()=>clippedLabel(S,q.id,q.s,x,540,q.w*q.o,{role:'title',color:q.c}));x+=(q.w+gap)*q.o;}});
}

// The travelling quantity is drawn in its state: hatched (in transit) inside a dashed outline.
// Its figure shows only above the vessel rims, so it never crosses into a vessel.
function token(S,x,y,scale,value) {
  const r=30*scale;
  S.actor('token',{x:x-r,y:y-r,w:2*r,h:2*r},g=>{g.save();g.beginPath();g.arc(x,y,r,0,Math.PI*2);g.fillStyle=T.paperHi;g.fill();g.clip();
    S.hatch(x-r,y-r,2*r,2*r,{color:T.transit,gap:7,width:2.2});g.restore();g.fillStyle=T.paperHi;g.beginPath();g.arc(x,y,r*.66,0,Math.PI*2);g.fill();
    g.setLineDash([6,5]);g.strokeStyle=T.ink;g.lineWidth=2.5;g.beginPath();g.arc(x,y,r,0,Math.PI*2);g.stroke();g.setLineDash([]);});
  if(scale>.7&&y<=M.cardA.y+M.vessel.dy-20)S.text('token-v',String(value),x,y+1,{role:'label',over:{face:'heavy'},align:'center',owner:'token'});
}

function mechanism(S,P,t) {
  const v=balances(P,t),[d0,d1]=P.dep,[t0,t1]=P.transit,[l0,l1]=P.land,span=t1-t0;
  const [s0,s1]=P.swap,shown={A:stepValue(t,{value:90,start:s0,end:s0+.3,step:10,from:100}),B:stepValue(t,{value:60,start:s1,end:s1+.3,step:10,from:50}),flight:10};
  // Focus hands over: B dims while the quantity leaves A, brightens, then A dims as it lands.
  const dimB=1-.62*seg(t,d0-.2,.4)*(1-seg(t,t0+.4*span,.5)),dimA=1-.62*seg(t,t0+.55*span,.5)*(1-seg(t,l1,.5));
  // The total badge receives the number carried from the claim. It pops like a chip: its fade reaches
  // full only once the pop has grown past full size, so its kicker never reads below its floor.
  const pb=seg(t,P.carryEnd,.35,E.linear);
  if(pb>0)S.fade(clamp(pb*2.3),()=>{const g=S.g,k=lerp(.8,1,E.outBack(pb));g.save();g.translate(640,140);g.scale(k,k);g.translate(-640,-140);
    S.card('badge',545,112,190,56,{radius:28,lift:.6});S.text('badge-k','Total',565,141,{role:'kicker',color:T.inkSoft,owner:'badge'});
    S.counter('badge-v',150,700,141,{role:'numeralSm',color:T.teal,owner:'badge'});g.restore();});
  // The state code is taught once, where each state first appears; later scenes reuse it unexplained.
  tpl.stateKey(S,t,{id:'key',x:M.legend[0],y:M.legend[1],items:[{state:'held',at:P.said.a[0]},{state:'transit',at:d0}]});
  account(S,P,t,'a',{level:v.A,shown:shown.A},dimA,seg(t,P.build[0],1.1,E.linear));account(S,P,t,'b',{level:v.B,shown:shown.B},dimB,seg(t,P.build[1],1.1,E.linear));
  // The route draws before anything travels on it.
  S.partial(Array.from({length:41},(_,i)=>bez(M.from,M.ctrl,M.to,i/40)),seg(t,P.route,.8,E.inOut),{color:T.rule,width:2.5,dash:[2,9]});
  // Token: rises out of A as A drains, rides the route with a trail, sinks into B as B fills.
  const vA=M.cardA.y+M.vessel.dy+M.vessel.h,vB=M.cardB.y+M.vessel.dy+M.vessel.h;
  let pos=null,scale=1,alpha=1;
  if(t>=d0&&t<t0){const p=seg(t,d0,d1-d0,E.inOut);pos=[M.from[0],lerp(vA-level(100)+30,M.from[1],E.outBack(p))];scale=lerp(.4,1,p);}
  else if(t>=t0&&t<l0){const u=seg(t,t0,span,glide);pos=bez(M.from,M.ctrl,M.to,u);
    S.decor(()=>{for(let k=1;k<=5;k++){const w=seg(t-k*.05,t0,span,glide),q=bez(M.from,M.ctrl,M.to,w);
      S.g.save();S.g.globalAlpha*=.12-k*.018;S.g.fillStyle=T.transit;S.g.beginPath();S.g.arc(q[0],q[1],30,0,Math.PI*2);S.g.fill();S.g.restore();}});}
  else if(t>=l0&&t<l1){const p=seg(t,l0,l1-l0,E.inOut);pos=[M.to[0],lerp(M.to[1],vB-level(60)+20,E.in(p))];scale=lerp(1,.45,p);alpha=1-seg(t,l1-.25,.25);}
  if(pos)S.fade(alpha,()=>token(S,pos[0],pos[1],scale,10));
  // A landing ring in the held colour confirms arrival without a success label.
  const ring=seg(t,l0+.55,.7,E.out);if(ring>0&&ring<1)S.decor(()=>{S.g.save();S.g.globalAlpha*=.5*(1-ring);S.g.strokeStyle=T.held;S.g.lineWidth=3;
    S.g.beginPath();S.g.ellipse(945,vB-level(60),20+60*ring,6+14*ring,0,0,Math.PI*2);S.g.stroke();S.g.restore();});
  // Inside the push, a ledger says where every unit is. The in-transit figure appears on its spoken
  // word and takes the signal highlighter while it is said; the ledger leaves as the push releases,
  // before the units land, so it is never read as the state after arrival.
  const L=M.ledger,led=1-seg(t,P.back[0],.4);
  if(led>0)S.fade(led,()=>tpl.readout(S,t,{id:'ledger',x:L.x,width:L.width,rule:false,rows:[
    {key:'Account A',value:shown.A,state:'held',y:L.ys[0],at:P.still-.15},
    {key:'In transit',value:spoken(t,10,[P.ten]),state:'transit',y:L.ys[1],at:P.counted-.15,valueAt:P.ten,mark:seg(t,P.ten,.45)*(1-seg(t,P.then,.3))},
    {key:'Account B',value:shown.B,state:'held',y:L.ys[2],at:P.counted+.15}]}));
  equation(S,P,t,shown);
  // Hand-drawn emphasis on what never changed, timed to the spoken word.
  S.scribble(640,140,118,42,seg(t,P.never-.1,.8,E.inOut),{color:T.accent});
  S.fade(seg(t,P.never+.5,.5),()=>S.text('note-total','never changed',790,126,{role:'accentSm',color:T.accent}));
  S.arrow([788,142],[764,148],seg(t,P.never+.8,.4,E.inOut),{bend:.4,color:T.accent,width:2.2,head:8});
  return v;
}

// The practice panel's picture: the clerk asks while the situation sits beside her. Both balances
// are held; the 25 units that would move are hatched (not yet moved), and their figure appears on
// its spoken word. It shows the question, never the answer.
function situation(S,P,t,box) {
  const s=Math.min(.6,(box.h-8)/300),fx=box.x+70,feet=box.y+box.h-4;
  S.fade(seg(t,P.mira-.2,.4),()=>cast(S,'clerk','clerk',fx,feet,{s,pose:'present',role:false,label:'right',speaking:talking(t,P.ask[0],P.ask[1]),phase:t}));
  const k=3.4,x0=box.x+400,ya=box.y+box.h*.3,yb=box.y+box.h*.72,h=30,lanes=seg(t,P.ask[0],.5);
  if(lanes<=0)return;
  S.fade(lanes,()=>{
    S.text('lane-a','A',x0-22,ya,{role:'label',color:T.white,align:'right'});S.text('lane-b','B',x0-22,yb,{role:'label',color:T.white,align:'right'});
    S.stateBox('bar-a','held',x0,ya-h/2,90*k,h,{p:lanes});S.stateBox('bar-b','held',x0,yb-h/2,35*k,h,{p:lanes});
    S.stateBox('bar-m','transit',x0+35*k,yb-h/2,25*k,h,{p:lanes});
    S.arrow([x0+47.5*k,yb-h/2-6],[x0+90*k+14,ya+4],seg(t,P.move,.6,E.inOut),{bend:-.35,color:T.white,width:2.4,head:10});
    const n=spoken(t,25,[P.units]);
    S.callout('moves','Moves',n??'',x0+60*k+24,yb,{state:'transit',keyColor:T.white,valueColor:T.white,keyP:seg(t,P.units-.15,.35),valueP:n===null?0:seg(t,P.units,.3)});
  });
}

function designedTransfer(g,lesson,t,course) {
  const P=planFor(lesson),{sc,cue}=P;
  const S=createDesignStage(g,course,{background:t>=P.wipe[1]?'night':'paper'});
  let v={A:100,B:50,flight:0},anchor=[R3.x+380,R3.y-125];

  const R1scene=()=>{
    if(t<sc.open.end)tpl.opener(S,t,{x:150,y:250,start:sc.open.start,end:sc.open.end,kicker:'Design-system demonstration',
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
      right:{title:'Conserved',dot:T.good,rows:[{name:'Total',from:150,to:150,check:true}]},
      takeaway:'Check the total before you trust the movement.',
      at:{title:cue.phrase('contrast','Balances changed.'),subtitle:cue.phrase('contrast','The total did not.',{after:cue('contrast','rose')}),
        left:[cue('contrast','fell')-.25,cue('contrast','rose')-.25],right:[cue('contrast','total',1)],
        takeaway:cue.phrase('contrast','Check the total before you trust the movement.',{after:cue('contrast','not')})}});};
  const R3scene=()=>{S.dotGrid(R3.x,R3.y,1500,800);const s=sc.series,b=cue('series','balances');
    anchor=tpl.lineStory(S,t,{x:R3.x,y:R3.y,start:s.start,end:s.end,kicker:'Repeated transfers',title:'Four transfers later',
      labels:['Start','T1','T2','T3','T4'],focusAt:cue('series','line'),note:'flat while balances swing',
      series:[{id:'a',name:'A',color:T.teal,values:[100,90,115,70,85]},{id:'b',name:'B',color:T.ink,values:[50,60,35,80,65]}],
      invariant:{name:'Total 150',value:150},
      at:{title:cue.phrase('series','Four transfers later',{after:cue('series','times')}),series:[b,b+.35],invariant:cue('series','total')}}).anchor;};
  const R4cam={...R4,zoom:1+.02*seg(t,sc.method.start,sc.method.end-sc.method.start,E.inOut)};
  const R5cam={...R5,zoom:1+.015*seg(t,sc.check.start,sc.check.end-sc.check.start,E.inOut)};
  // The method is general, so its details carry no invented figures and the fiction badge is off.
  const R4scene=()=>{const s=sc.method;tpl.stepper(S,t,{x:R4.x,y:R4.y,start:s.start,end:s.end,title:'Read any transfer',accent:'in three steps.',
    stepAt:[cue('method','find'),cue('method','follow'),cue('method','check')],
    steps:[{title:'Find the total',detail:'the fixed sum'},{title:'Follow the moving quantity',detail:'still counted'},
      {title:'Check the balance',detail:'before = after'}],
    at:{title:cue.phrase('method','Read any transfer'),accent:cue.phrase('method','in three steps.')}});};
  const R5scene=()=>{const s=sc.check;
    tpl.question(S,t,{x:R5.x,y:R5.y,start:s.start,end:s.end,kicker:'Check yourself',prompt:'If 25 units move from B to A, what is the total?',
      options:['125','150','175'],correct:1,revealAt:P.reveal,reason:'Moving units changes balances, not the total.',
      art:(S,box,t)=>situation(S,P,t,box),promptAfter:.3,tagsAt:P.reveal+.7,
      tags:[{text:'Loses 25',state:'transit'},{text:'Conserved'},{text:'Adds 25',state:'transit'}],
      at:{kicker:cue('check','check'),prompt:cue.phrase('check','If 25 units move from B to A, what is the total?'),
        reason:cue.phrase('check','Moving units changes balances, not the total.',{after:P.reveal})}});};

  if(t<P.iris[0]) {
    // Continuous canvas: regions draw in world space and the camera travels between them; pans are transitions.
    world(S,t,P.keys,()=>{if(t<P.pans[0][1])R1scene();if(t>=P.pans[0][0]&&t<P.pans[1][1])R2scene();if(t>=P.pans[1][0])R3scene();},{pans:P.pans});
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

  // Top-band chrome, drawn last at the top level of the frame.
  tpl.progressRail(S,t,{steps:['Find the total','Follow the quantity','Check the balance'],at:[sc.claim.start,sc.transfer.start,sc.contrast.start],
    from:sc.open.end-.6,until:P.iris[0]-.7});
  tpl.fictionBadge(S,t,{windows:P.fiction});
  return S.finish({totalUnits:v.A+v.flight+v.B,expectedTotal:150});
}

function draw(g,lesson,t,course) {
  if(lesson.visual==='designed-transfer')return designedTransfer(g,lesson,t,course);
  throw new Error(`No authored world for visual: ${lesson.visual}`);
}
module.exports={draw};
