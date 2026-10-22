'use strict';
// Reusable scene templates for design.cjs. Each one owns the hierarchy and choreography of a
// single teaching move; the subject's own mechanism still belongs in world.cjs.
// Timing: every template takes its scene `start` and `end` plus an optional `at` object of
// narration cue times (from createCues). Missing `at` entries fall back to a compact stagger
// from `start`. Given `end`, a template asserts through the frame audit that the spoken span
// leaves room for its choreography, so short narration fails loudly instead of truncating.
// Every template registers its text and solid objects, so the geometry audit still applies, and
// its default sizes and positions meet the stage's type floors, edge guard and word budget with
// room for a slow push (zoom ≤ 1.03). Chrome (progressRail, fictionBadge) lives in the top band.
// See references/video/design-system.md for when to use each one.
const {T,E,role,seg,lerp,clamp,wordTimes,beforePush,stateOf,STATES}=require('./design.cjs');
const words=s=>String(s).split(/\s+/).filter(Boolean);
const stagger=(s,from,step)=>words(s).map((_,i)=>from+i*step);
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
// Minimum spoken span, in seconds, that each template's choreography needs.
const MIN_SPAN={opener:4.5,partOpener:4.5,statement:3,compare:6,lineStory:6,stepper:5,question:6,sectionHead:2,readout:3,stateKey:2};
// Page furniture in screen space: the top band's chrome line (rail on the left, fiction badge on
// the right), the section rule and the headline under it. Pushes frame below it (fitCamera's band).
const PAGE={left:80,right:1200,ruleY:100,headY:146,bandY:50,railLeft:40,badgeRight:1240};

// Opener: kicker -> display line rises -> serif accent resolves from blur -> agenda chips.
// The agenda names the chapters that progressRail() keeps on screen afterwards.
// at: {title:[...], accent:[...], agenda:[...]}
function opener(S,t,{x,y,start,end,kicker,title,accent,agenda=[],at={}}) {
  S.fits('opener',start,end,MIN_SPAN.opener);
  const out=seg(t,end-.6,.6,E.in),lift=-34*out,accentAt=at.accent||stagger(accent,start+1.3,.2);
  S.fade(1-out,()=>{
    S.fade(seg(t,start+.2,.5),()=>S.text('open-kicker',kicker,x+lerp(-18,0,seg(t,start+.2,.6)),y-95+lift,{role:'kicker',color:T.teal}));
    S.sentence('open-title',title,x,y+lift,{t,times:at.title||stagger(title,start+.5,.22),reveal:'rise',dur:.6,role:'display',maxWidth:1000});
    const A=S.sentence('open-accent',accent,x,y+100+lift,{t,times:accentAt,reveal:'blur',dur:.6,role:'accent',color:T.accent,maxWidth:1000});
    const last=A.words.at(-1);S.underline(last.x-4,last.x+last.w+2,y+100+lift+38,seg(t,accentAt.at(-1)+.5,.6,E.inOut),{color:T.accent});
    // A popping chip overshoots ~9% (E.outBack); the 28 px gap keeps neighbours apart through it.
    let cx=x;agenda.forEach((label,i)=>{const b=S.chip(`open-agenda${i}`,label,cx,y+215+lift,{p:seg(t,at.agenda?.[i]??start+2.8+i*.18,.55,E.linear),
      fill:T.paperLo,color:T.ink,align:'left',role:'label'});cx+=b.w+28;});
  });
}

// ---------------------------------------------------------------- part openers (variation device)
// A course chooses once, with defineParts, how each PART opens its lessons: a layout (where the
// hero sits beside or under the title) and a hairline motif ruled in the hero box. Same part =
// same frame; the next part looks different from its first frame, and every lesson puts its own
// hero object into the hero box. This is the only variation device: colour meanings, type roles
// and page furniture never vary, and the motif is always hairline rule ink.
//   defineParts({I:{name:'Arrivals',layout:'heroRight',motif:'columns'},II:{name:'Sorting',layout:'heroLeft',motif:'ledger'}})
// Boxes are frame coordinates for a region centred at (640, 340); partLayout(part,{x,y}) moves them
// to a region centred elsewhere on the world canvas.
const PART_LAYOUTS={heroLeft:{hero:{x:70,y:108,w:500,h:478},title:{x:640,y:300,w:560}},
  heroRight:{hero:{x:700,y:108,w:510,h:478},title:{x:80,y:300,w:580}},
  heroBelow:{hero:{x:80,y:350,w:1120,h:236},title:{x:80,y:214,w:1120}}};
const MOTIFS=['columns','ledger','grid','form','calendar'];
// Worlds read PARTS; only defineParts writes it. Validation runs before anything is written.
const PARTS={};
function defineParts(spec) {
  const entries=Object.entries(spec||{});if(!entries.length)throw new Error('defineParts needs at least one part');
  for(const [key,p] of entries) {
    if(!key.trim()||own(PARTS,key))throw new Error('Part already defined or unnamed: '+key);
    if(!own(PART_LAYOUTS,p?.layout))throw new Error(`Part ${key} layout must be one of ${Object.keys(PART_LAYOUTS).join(', ')}`);
    if(!MOTIFS.includes(p.motif))throw new Error(`Part ${key} motif must be one of ${MOTIFS.join(', ')}`);
  }
  for(const [key,p] of entries)PARTS[key]=Object.freeze({key,name:String(p.name||''),layout:p.layout,motif:p.motif});
  return PARTS;
}
// Part key from a key or a lesson's `part` string ("Part II · Sorting").
const partKey=p=>{const s=String(p);if(own(PARTS,s))return s;const m=/^\s*Part\s+([^\s·:,]+)/i.exec(s);return m?m[1]:s;};
// The part's hero box and title column (see PART_LAYOUTS), offset to a region centred at (x, y).
function partLayout(part,{x=640,y=340}={}) {
  const P=PARTS[partKey(part)];if(!P)throw new Error('Unknown part: '+part+' (call defineParts first)');
  const L=PART_LAYOUTS[P.layout],dx=x-640,dy=y-340;
  return {...P,hero:{...L.hero,x:L.hero.x+dx,y:L.hero.y+dy},title:{...L.title,x:L.title.x+dx,y:L.title.y+dy}};
}
// The part's ground motif, drawn in hairline rule ink across the hero box as p goes 0 -> 1.
function motif(S,kind,box,p) {
  if(p<=0)return;const g=S.g,e=E.inOut(clamp(p));
  S.decor(()=>{g.save();g.fillStyle=T.rule;
    if(kind==='columns')for(let i=0;i<=5;i++){const x=box.x+box.w*i/5;g.fillRect(x-.75,box.y,1.5,box.h*e);}
    else if(kind==='ledger')for(let y=box.y+24;y<box.y+box.h;y+=40)g.fillRect(box.x,y,box.w*e,1.5);
    else if(kind==='grid'){g.globalAlpha*=e;for(let x=box.x;x<=box.x+box.w;x+=32)for(let y=box.y;y<=box.y+box.h;y+=32)g.fillRect(x-1.5,y-1.5,3,3);}
    else if(kind==='form'){g.fillRect(box.x+16,box.y,1.5,box.h*e);g.fillRect(box.x+22,box.y,1.5,box.h*e);for(let y=box.y+56;y<box.y+box.h;y+=56)g.fillRect(box.x+40,y,(box.w-40)*e,1.5);}
    else if(kind==='calendar'){for(let i=0;i<=12;i++){const x=box.x+box.w*i/12;g.fillRect(x-.75,box.y+box.h-28,1.5,28*e);}g.fillRect(box.x,box.y+box.h-1,box.w*e,2);}
    g.restore();});
}
// Part opener: a heavy rule and kicker name the lesson and its part; the display title rises word
// by word at the largest size (88 down to 56) that sets it in the title column (two lines, three
// at ≤ 72 px; heroBelow wants one line and allows two at ≤ 64 px), centred on the column's line but
// never lifting its kicker into the top edge band; the accent's last `markWords` words take the
// signal highlighter as they are spoken;
// hero(S, box, t) draws the lesson's hero object in the part's hero box over the motif.
// at: {title:[...], accent:[...]}; exitAt (default end - .6) clears the title block, not the hero.
// Returns the layout so a lesson can keep its hero on screen after the title exits.
function partOpener(S,t,{part,lesson,kicker,title,accent,start,end,at={},exitAt,markWords=2,hero=null,motifAt,motifUntil,x=640,y=340}) {
  S.fits('partOpener',start,end,MIN_SPAN.partOpener);
  // The exit lift stays small, so the kicker is faded out before it could reach the edge band.
  const L=partLayout(part,{x,y}),out=seg(t,exitAt??end-.6,.6,E.in),lift=-16*out,tb=L.title;
  const fit=(lines,from)=>{for(let z=from;z>=56;z-=4){const l=S.layout(title,{role:'display',over:{size:z},maxWidth:tb.w});if(l.width<=tb.w&&l.lines<=lines)return l;}return null;};
  const TL=(L.layout==='heroBelow'?fit(1,88)||fit(2,64):fit(2,88)||fit(3,72))||S.layout(title,{role:'display',over:{size:56},maxWidth:tb.w}),size=TL.r.size;
  // First-line centre: centred on the column's line, but the kicker's box never rises above y 118 of the frame.
  const top=Math.max(tb.y-(TL.lines-1)*TL.lh/2,y-177+size*.62),mid=top+(TL.lines-1)*TL.lh/2,bottom=top+(TL.lines-1)*TL.lh;
  motif(S,L.motif,L.hero,seg(t,motifAt??start,1.2,E.inOut)*(motifUntil!=null?1-seg(t,motifUntil,.5):1));
  if(hero)hero(S,{...L.hero},t);
  if(out>=1)return L;
  S.fade(1-out,()=>{
    const ky=top-size*.62-30+lift,name=kicker??[lesson!=null?`Lesson ${lesson}`:`Part ${L.key}`,L.name].filter(Boolean).join(' · ');
    S.rule(tb.x,tb.x+Math.min(tb.w,560),ky-30,seg(t,start,.7,E.inOut),{weight:6});
    S.fade(seg(t,start+.15,.5),()=>S.text('po-kicker',name,tb.x,ky,{role:'kicker',color:T.teal}));
    S.sentence('po-title',title,tb.x,mid+lift,{t,times:at.title||stagger(title,start+.4,.2),reveal:'rise',dur:.6,role:'display',over:{size},maxWidth:tb.w});
    if(accent){const n=words(accent).length,k=Math.max(0,n-markWords),aat=at.accent||stagger(accent,start+1.3,.2),styles={},AL=S.layout(accent,{role:'accentMd',maxWidth:tb.w});
      for(let i=k;i<n;i++)styles[i]={color:T.ink,mark:{p:seg(t,aat[i]??aat.at(-1),.45,E.inOut)}};
      S.sentence('po-accent',accent,tb.x,bottom+size*.62+22+AL.r.size*.62+(AL.lines-1)*AL.lh/2+lift,{t,times:aat,reveal:'rise',dur:.5,role:'accentMd',color:T.inkSoft,maxWidth:tb.w,styles});}
  });
  return L;
}

// Section head: the page furniture of a content section, a heavy rule and a headline under it,
// always in screen space (even when called inside S.view) so the camera moves the world beneath.
// Keep world content below y 196 (fitCamera's default band) while a head is up.
// items: [{text, times (or at), until, marks:{wordIndex: at}, role}]. One item shows at a time:
// an item lifts away in time for its successor (gone before the next one's first word), and the
// next slides in word by word. deck: an optional {text, times, until} (or a list of them) set
// right-aligned on the headline's line.
function sectionHead(S,t,{id='head',x=PAGE.left,y=PAGE.headY,width=PAGE.right-PAGE.left,ruleAt,until=Infinity,items=[],deck=null,headRole='headline',
  deckRole='accentMd',deckColor=T.teal,start,end}) {
  const timesOf=it=>it.times||stagger(it.text,it.at??0,.12),first=items.length?timesOf(items[0])[0]:ruleAt;
  S.fits('sectionHead',start??first,end,MIN_SPAN.sectionHead);
  const show=1-seg(t,until,.4,E.in);if(show<=0)return;
  const g=S.g;g.save();g.setTransform(1,0,0,1,0,0);g.filter='none';
  try{S.fade(show,()=>{
    S.rule(x,x+width,PAGE.ruleY,seg(t,ruleAt??(first??0)-.3,.7,E.inOut),{weight:6});
    items.forEach((it,k)=>{const times=timesOf(it),next=k+1<items.length?timesOf(items[k+1])[0]:Infinity,gone=seg(t,Math.min(it.until??Infinity,next-.38),.35,E.in);
      if(t<times[0]-.05||gone>=1)return;
      const r=it.role||headRole,L=S.layout(it.text,{role:r,maxWidth:width}),styles={};
      for(const [i,m] of Object.entries(it.marks||{}))styles[i]={mark:{p:seg(t,m,.45,E.inOut)}};
      // A wrapped head hangs from its first line, so it never climbs into the rule.
      S.fade(1-gone,()=>{g.save();g.translate(0,-10*gone);
        S.sentence(`${id}${k}`,it.text,x,y+(L.lines-1)*L.lh/2,{t,times,reveal:'slide',dur:.45,role:r,maxWidth:width,styles});g.restore();});});
    (Array.isArray(deck)?deck:deck?[deck]:[]).forEach((dk,k,all)=>{const times=timesOf(dk),next=k+1<all.length?timesOf(all[k+1])[0]:Infinity,gone=seg(t,Math.min(dk.until??Infinity,next-.38),.35,E.in);
      if(t>=times[0]-.05&&gone<1)S.fade(1-gone,()=>S.sentence(`${id}-deck${k}`,dk.text,x+width,y+4,{t,times,reveal:'slide',dur:.45,role:deckRole,color:deckColor,align:'right',maxWidth:width/2}));});
  });}finally{g.restore();}
}

// Readout: lane-aligned values beside a timeline or diagram. Each row sits at its lane's y: an
// optional state swatch and the key (kicker) on the left, the value right-aligned at x + width,
// an optional sub-line under the key; a dotted guide runs from the cursor (a today line, an x in
// the same space) to the row. The key lands at `at`, the value at `valueAt` (its spoken word; a
// null value, as spoken() returns before its word, draws nothing); mark (0..1) sweeps the
// highlighter behind the value. rows: [{key, value, sub, state, y, at, valueAt, mark}]
function readout(S,t,{id='ro',x,width=380,rows,cursor=null,keyRole='kicker',valueRole='numeralSm',valueOver=null,until=Infinity,rule=true,guideAlpha=1,start,end}) {
  S.fits('readout',start??rows[0]?.at,end,MIN_SPAN.readout);
  const show=1-seg(t,until,.4,E.in);if(show<=0||!rows.length)return;
  S.fade(show,()=>{
    if(rule){const y0=Math.min(...rows.map(r=>r.y))-40,y1=Math.max(...rows.map(r=>r.y))+40;S.vrule(x-20,y0,y1,seg(t,rows[0].at-.3,.5,E.inOut),{weight:2.5});}
    rows.forEach((r,i)=>{const p=seg(t,r.at,.45),vp=seg(t,r.valueAt??r.at,.4);if(p<=0)return;
      if(cursor!=null)S.fade(guideAlpha,()=>S.partial([[cursor+10,r.y],[x-30,r.y]],seg(t,r.at-.15,.5,E.inOut),{width:2.5,dash:[2,7],color:T.ink}));
      const kr=role(keyRole),ky=r.y-(r.sub?16:0),sw=r.state?Math.round(kr.size*.86):0,kx=x+(sw?sw+10:0);
      S.fade(p,()=>{if(r.state)S.swatch(`${id}-s${i}`,r.state,x,ky,{size:sw});
        S.text(`${id}-k${i}`,r.key,kx,ky,{role:keyRole,color:T.inkSoft});
        if(r.sub)S.text(`${id}-u${i}`,r.sub,kx,r.y+22,{role:'small',color:T.inkSoft});});
      if(vp>0&&r.value!=null)S.fade(vp,()=>{const vr=role(valueRole,valueOver),v=String(r.value),vw=S.measure(vr.upper?v.toUpperCase():v,vr),vx=x+width-vw;
        if(r.mark>0)S.marker(`${id}-m${i}`,vx-10,r.y-vr.size*.68,vw+20,vr.size*1.36,r.mark);
        S.text(`${id}-v${i}`,v,x+width,r.y,{role:valueRole,over:valueOver,align:'right',owner:r.mark>0?`${id}-m${i}`:null});});});});
}

// State key: a legend row of the course's state swatches and labels (defineStates): teach the
// code once, then reuse it. items: [{state, label, at}]; label defaults to the state's own label.
// Returns the row's width.
function stateKey(S,t,{id='sk',x,y,items,gap=34,labelRole='label',size=26,start,end}) {
  S.fits('stateKey',start??items.find(it=>Number.isFinite(it.at))?.at,end,MIN_SPAN.stateKey);
  let cx=x;items.forEach((it,i)=>{const label=it.label??STATES[stateOf(it.state)].label,p=seg(t,it.at??-Infinity,.4),lw=S.measure(label,role(labelRole));
    if(p>0)S.fade(p,()=>{S.swatch(`${id}-s${i}`,it.state,cx,y,{size});S.text(`${id}-l${i}`,label,cx+size+10,y,{role:labelRole});});
    cx+=size+10+lw+gap;});
  return Math.max(0,cx-gap-x);
}

// Statement: the whole sentence is present as a ghost and words fill as they are spoken.
// One emphasis word receives the signal highlighter. From exitAt the context clears quickly while the emphasis
// slot stays empty; the returned position lets carry() move that word into the next scene.
// times: one onset per word (cue.phrase); without it the scene's word timings are used.
function statement(S,t,{id='claim',x,y,scene,text,emphasis,start,end,markAt,exitAt=Infinity,times:given}) {
  S.fits('statement',start,end,MIN_SPAN.statement);
  const list=words(text),{times,method}=given?{times:given,method:'cued'}:wordTimes(list,scene);
  const k=list.findIndex(w=>w.replace(/[^\w$%]/g,'')===emphasis);
  if(k<0)throw new Error(`Statement emphasis is not in its text: ${emphasis}`);
  const opts={role:'headline',over:{size:56},maxWidth:1040,align:'center'},L=S.layout(text,opts),exit=seg(t,exitAt,.35,E.out);
  // From exitAt itself the emphasis slot is empty, so a carry starting on that frame never doubles it.
  if(t<exitAt)S.fade(seg(t,start,.35),()=>S.sentence(id,text,x,y,{t,times,reveal:'ghost',dur:.35,...opts,
    styles:{[k]:{mark:{p:seg(t,markAt??times[k],.55,E.inOut),color:T.signal}}}}));
  else S.fade(1-exit,()=>S.sentence(id,text,x,y,{t:Infinity,times,reveal:'none',...opts,styles:{[k]:{hidden:true}}}));
  const q=L.words[k];
  return {timing:method,emphasis:{x:x-q.lineWidth/2+q.x,y:y-(L.lines-1)*L.lh/2+q.line*L.lh,w:q.w,size:L.r.size}};
}

// Carry: one word or number travels from where it was said to where it now lives.
// Use it for the hero object of a scene change instead of fading one copy out and another in.
// hold: the word first waits in its slot while the statement's context clears (default 30% of the
// span, at most .3 s), so even a short carry never crosses words that are still fading.
function carry(S,t,{id,text,from,to,start,end,fromRole='headline',fromSize,toRole='numeralSm',toColor=T.teal,hold=Math.min(.3,(end-start)*.3)}) {
  if(t<start||t>=end)return false;
  const p=seg(t,start+hold,end-start-hold,E.inOut),r0=role(fromRole,fromSize?{size:fromSize}:undefined),r1=role(toRole);
  S.text(id,text,lerp(from[0],to[0],p),lerp(from[1],to[1],p),{role:fromRole,over:{size:lerp(r0.size,r1.size,p)},align:'center',color:p>.5?toColor:T.ink});
  return true;
}

// Compare: two columns separated by a drawn divider; old values are struck (ink: replaced, not
// wrong) and new values pop. A conserved row takes the check in T.good.
// The left column dims at focusAt so the eye lands on the conserved side.
// at: {title:[...], subtitle:[...], left:[row onsets], right:[row onsets], takeaway:[...]}
function compare(S,t,{x,y,start,end,title,subtitle,left,right,takeaway,focusAt,at={}}) {
  S.fits('compare',start,end,MIN_SPAN.compare);
  const lx=x-560,rx=x+40,dim=1-.62*seg(t,focusAt,.6,E.inOut);
  S.sentence('cmp-title',title,lx,y-205,{t,times:at.title||stagger(title,start+.15,.15),reveal:'rise',role:'headline'});
  if(subtitle)S.sentence('cmp-sub',subtitle,lx+S.measure(title,role('headline'))+18,y-205,{t,times:at.subtitle||stagger(subtitle,start+.75,.15),reveal:'blur',role:'accentMd',color:T.teal});
  S.partial([[x-25,y-140],[x-25,y+130]],seg(t,start+.4,.8,E.inOut),{color:T.rule,width:2,dash:[6,8]});
  const col=(side,cx,spec,alpha,rowAt)=>S.fade(alpha,()=>{
    S.chip(`cmp-${side}-h`,spec.title,cx,y-112,{p:seg(t,Math.min(start+1.1,(rowAt?.[0]??start+1.5)-.4),.5,E.linear),fill:'transparent',color:T.inkSoft,role:'kicker',align:'left',padX:0,dot:spec.dot});
    spec.rows.forEach((r,i)=>{const ry=y-25+i*100,a=rowAt?.[i]??start+1.5+i*.75,num={size:40};
      S.fade(seg(t,a,.45),()=>S.text(`cmp-${side}-n${i}`,r.name,cx,ry,{role:'title',over:{size:36}}));
      S.fade(seg(t,a+.2,.45),()=>S.text(`cmp-${side}-o${i}`,String(r.from),cx+270,ry,{role:'numeralSm',over:num,color:T.inkSoft,align:'center'}));
      if(r.from!==r.to)S.strike(cx+238,cx+302,ry,seg(t,a+.55,.4),{width:4});
      S.arrow([cx+318,ry],[cx+362,ry],seg(t,a+.6,.35,E.inOut),{bend:0,color:T.mute,width:2.4,head:10});
      S.chip(`cmp-${side}-v${i}`,String(r.to),cx+420,ry,{p:seg(t,a+.85,.55,E.linear),fill:r.from===r.to?T.tealSoft:T.accentSoft,color:T.ink,role:'numeralSm',padX:14,padY:6});
      if(r.check)S.partial([[cx+482,ry],[cx+494,ry+13],[cx+518,ry-14]],seg(t,a+1.3,.4,E.inOut),{color:T.good,width:5});
    });});
  col('l',lx,left,dim,at.left);col('r',rx,right,1,at.right);
  if(takeaway)S.sentence('cmp-take',takeaway,x,y+200,{t,times:at.takeaway||stagger(takeaway,focusAt+.4,.12),reveal:'blur',role:'accentMd',over:{size:36},align:'center',maxWidth:1100});
}

// Label centres spread at least `gap` apart; each crowded cluster stays centred on its own points.
function spread(ys,gap) {
  const groups=[],out=[];
  for(const q of ys.map((y,i)=>({y,i})).sort((a,b)=>a.y-b.y)){groups.push({m:[q],c:q.y});
    for(let k=groups.length-1;k>0;k--){const a=groups[k-1],b=groups[k];if(b.c-(b.m.length-1)*gap/2-(a.c+(a.m.length-1)*gap/2)>=gap)break;
      const m=[...a.m,...b.m];groups.splice(k-1,2,{m,c:m.reduce((s,x)=>s+x.y,0)/m.length});}}
  for(const G of groups)G.m.forEach((q,j)=>{out[q.i]=G.c+(j-(G.m.length-1)/2)*gap;});
  return out;
}

// Line story: axes draw, series trace with dots, the invariant lands last in the accent colour.
// Series swing while the invariant stays flat; the note names that contrast. End chips never
// collide: close line ends spread their chips apart, with a short leader to each line.
// at: {title:[...], series:[one onset per series], invariant}
function lineStory(S,t,{x,y,start,end,kicker,title,series,invariant,labels,focusAt,note,max,at={}}) {
  S.fits('lineStory',start,end,MIN_SPAN.lineStory);
  const top=max??Math.max(invariant?.value??0,...series.flatMap(s=>s.values));
  // The plot keeps clear of the kicker and title above and of the caption band below.
  const X0=x-520,X1=x+380,Y0=y+180,Y1=y-118,px=i=>lerp(X0+20,X1,i/(labels.length-1)),py=v=>lerp(Y0,Y1,v/top);
  if(kicker)S.fade(seg(t,start+.1,.4),()=>S.text('ls-kicker',kicker,X0-40,y-218,{role:'kicker',color:T.teal}));
  S.sentence('ls-title',title,X0-40,y-174,{t,times:at.title||stagger(title,start+.2,.15),reveal:'rise',role:'headline'});
  S.partial([[X0,Y0],[X1+40,Y0]],seg(t,start+.4,.6,E.inOut),{color:T.inkSoft,width:2});
  // Axis ticks are tertiary text (24 px floor).
  labels.forEach((l,i)=>S.fade(seg(t,start+.6+i*.08,.3),()=>S.text(`ls-x${i}`,l,px(i),Y0+27,{role:'small',color:T.inkSoft,align:'center'})));
  const dim=1-.7*seg(t,focusAt,.6,E.inOut),ends=series.map(s=>py(s.values.at(-1)));
  const chipY=spread(invariant?[...ends,py(invariant.value)]:ends,46),leader=(y0,y1,color,p)=>{if(Math.abs(y1-y0)>2)S.partial([[X1+8,y0],[X1+26,y1]],p,{color,width:2});};
  series.forEach((s,si)=>S.fade(dim,()=>{
    const pts=s.values.map((v,i)=>[px(i),py(v)]),a=at.series?.[si]??start+.9+si*.35,p=seg(t,a,2.2,E.inOut);
    S.partial(pts,p,{color:s.color,width:5});
    S.decor(()=>pts.forEach((q,i)=>{const r=seg(t,a+2.2*i/(pts.length-1)-.05,.3,E.outBack);if(r>0){S.g.fillStyle=s.color;S.g.beginPath();S.g.arc(q[0],q[1],7*r,0,Math.PI*2);S.g.fill();}}));
    leader(ends[si],chipY[si],s.color,seg(t,a+2.1,.3));
    S.chip(`ls-${s.id}`,s.name,X1+30,chipY[si],{p:seg(t,a+2.2,.5,E.linear),fill:s.color,color:T.white,role:'label',align:'left',padX:11,padY:5});
  }));
  let anchor=[X1,Y1];
  if(invariant) {
    const ia=at.invariant??start+3.4,iy=py(invariant.value),cy=chipY.at(-1);anchor=[X1,iy];
    S.partial([[X0+20,iy],[X1,iy]],seg(t,ia,1,E.inOut),{color:T.accent,width:6});
    leader(iy,cy,T.accent,seg(t,ia+.8,.3));
    S.chip('ls-total',invariant.name,X1+30,cy,{p:seg(t,ia+.9,.5,E.linear),fill:T.accent,color:T.white,role:'label',align:'left',padX:11,padY:5});
    if(note) {
      S.fade(seg(t,focusAt+.4,.5),()=>S.text('ls-note',note,X1-10,y-210,{role:'accentSm',over:{size:30},color:T.accent,align:'right'}));
      S.arrow([X1-120,y-191],[X1-180,iy-14],seg(t,focusAt+.7,.6,E.inOut),{bend:.3,color:T.accent,width:2.4});
    }
  }
  return {anchor};
}

// Stepper: a persistent token travels down a rail; each step activates, then settles.
// stepAt: one onset per step (normally the cue of each step's first spoken word).
// state: the course state (defineStates) of the quantity the token carries; without it the token
// is neutral ink. It never takes a meaning colour: the signal belongs to the words being spoken.
// at: {title:[...], accent:[...]}
function stepper(S,t,{x,y,start,end,title,accent,steps,stepAt,state=null,at={}}) {
  S.fits('stepper',start,end,MIN_SPAN.stepper);
  const def=state!=null?STATES[stateOf(state)]:null;
  S.sentence('st-title',title,x-510,y-170,{t,times:at.title||stagger(title,start+.25,.14),reveal:'rise',role:'headline'});
  if(accent)S.sentence('st-accent',accent,x-510,y-116,{t,times:at.accent||stagger(accent,start+.75,.16),reveal:'blur',role:'accentMd',color:T.accent});
  const rx=x-10,ys=steps.map((_,i)=>y-160+i*148);
  S.partial([[rx,ys[0]],[rx,ys.at(-1)]],seg(t,start+.6,.7,E.inOut),{color:T.rule,width:3});
  let active=-1;stepAt.forEach((a,i)=>{if(t>=a)active=i;});
  const k=stepAt.findIndex(a=>t<a+.7&&t>=a),moving=k>0;
  steps.forEach((s,i)=>{
    const on=seg(t,stepAt[i]+.15,.5),done=i<active;
    S.decor(()=>{S.g.fillStyle=i<=active?T.ink:T.paperLo;S.g.beginPath();S.g.arc(rx,ys[i],9,0,Math.PI*2);S.g.fill();});
    S.fade(.18+.82*on*(done?.55:1),()=>{
      S.text(`st-n${i}`,s.title,rx+46,ys[i]-12,{role:'title',over:{size:38}});
      S.text(`st-m${i}`,s.detail,rx+48,ys[i]+30,{role:'mono',color:T.inkSoft});
    });
    if(done)S.partial([[rx-6,ys[i]],[rx-1,ys[i]+5],[rx+7,ys[i]-6]],1,{color:T.paperHi,width:2.5});
  });
  // The travelling token keeps the identity of the quantity the steps act on: neutral ink with a
  // paper ring, or the quantity's state in the course's code (solid fill, or hatching inside a
  // dashed outline, as stateBox draws it). The outline is ink on paper and white on night.
  const from=moving?ys[k-1]:ys[Math.max(0,active)],to=ys[Math.max(0,k>=0?k:active)],p=moving?seg(t,stepAt[k],.6,E.inOut):1;
  const ty=lerp(from,to,p),pop=seg(t,stepAt[0]-.3,.5,E.outBack),o=S.night?T.white:T.ink;
  if(pop>0)S.actor('st-token',{x:rx-22*pop,y:ty-22*pop,w:44*pop,h:44*pop},g=>{const R=20*pop,disc=r=>{g.beginPath();g.arc(rx,ty,r,0,Math.PI*2);};disc(R);
    if(def?.treatment==='hatched'){g.fillStyle=S.night?T.night:T.paperHi;g.fill();g.save();g.clip();g.strokeStyle=S.night?T[def.soft]:T[def.token];g.lineWidth=2;g.beginPath();
      for(let q=-2*R;q<2*R;q+=7){g.moveTo(rx-R+q,ty+R);g.lineTo(rx+R+q,ty-R);}g.stroke();g.restore();disc(R);g.setLineDash([6,4]);}
    else{g.fillStyle=def?T[def.token]:o;g.fill();}
    g.strokeStyle=o;g.lineWidth=2.5;g.stroke();g.setLineDash([]);
    if(!def){g.strokeStyle=S.night?T.night:T.paperHi;g.lineWidth=3;disc(R*.55);g.stroke();}});
}

// Question: the practice panel, designed for the night background so the check reads as a
// different mode. The kicker takes the signal highlighter; the prompt is a ghost that fills with
// the narration; art(S, box, t), when given, draws a PICTURE of the situation in a box between the
// prompt and the options (S.night is true there; use stateBox, swatches and illustrations). The
// options are visible before the reveal, so there is time to think. On revealAt — the narrator's
// answer word, never earlier — the correct option takes the signal highlighter (its type turns ink
// exactly under the sweep) and the others dim under a full-strength strike in T.wrong; tags
// ([{text, state}] per option) then say what each option actually is, from tagsAt (default
// revealAt + .45). promptAfter (0..1) is the prompt's strength once the answer is out, so the
// answer, its tags and the reason stay within the word budget.
// at: {kicker, prompt:[...], options (time), reason:[...]}; optionsAt overrides at.options.
function question(S,t,{x=640,y=340,start,end,kicker,prompt,options,correct,revealAt,reason,scene,at={},art=null,tags=null,tagsAt,optionsAt,promptAfter=1}) {
  S.fits('question',start,end,MIN_SPAN.question);
  const pic=typeof art==='function',left=x-510,kp=seg(t,at.kicker??start+.3,.45);
  if(kicker&&kp>0)S.fade(clamp(kp*2),()=>S.markText('q-kicker',kicker,left,pic?y-218:y-190,{role:'kicker',p:kp,color:T.white,pad:8}));
  const times=at.prompt||wordTimes(words(prompt),scene,{from:start+.6,to:start+2.6}).times,oAt=optionsAt??at.options??times.at(-1)+.3;
  // With a picture the prompt hangs from its first line, so the picture keeps the space below it.
  const PL=S.layout(prompt,{role:'headline',maxWidth:1000}),py=pic?y-172+(PL.lines-1)*PL.lh/2:y-110;
  S.fade(1-(1-promptAfter)*seg(t,revealAt+.5,.5),()=>S.sentence('q-prompt',prompt,left,py,{t,times,reveal:'ghost',ghost:.14,dur:.3,role:'headline',maxWidth:1000,color:T.white}));
  let box=null;if(pic){const top=py+(PL.lines-1)*PL.lh/2+PL.r.size*.62+10;box={x:left,y:top,w:1020,h:y+40-top};art(S,{...box},t);}
  const oy=pic?y+88:y+60,R=role('numeral'),n=options.length,step=Math.min(300,1020/n),r=seg(t,revealAt,.5,E.linear),tg=seg(t,tagsAt??revealAt+.45,.4);
  options.forEach((o,i)=>{const ox=x+(i-(n-1)/2)*step,ok=i===correct,p=seg(t,oAt+i*.15,.55,E.linear);if(p<=0)return;
    const s=String(o),bw=S.measure(s,R)+68,bh=R.size+28,id=`q-o${i}`;
    // Each option pops like a chip; its fade reaches full only once the pop has grown past full size.
    S.fade(ok?1:1-.6*r,()=>S.fade(clamp(p*2.3),()=>{const g=S.g,k=E.outBack(clamp(p));g.save();g.translate(ox,oy);g.scale(k,k);g.translate(-ox,-oy);
      S.actor(id,{x:ox-bw/2,y:oy-bh/2,w:bw,h:bh},()=>{S.roundRect(ox-bw/2,oy-bh/2,bw,bh,22);g.fillStyle=T.nightHi;g.fill();});
      S.markText(id+'-t',s,ox,oy+1,{role:'numeral',align:'center',p:ok?r:0,color:T.white,owner:id,pad:14});g.restore();}));
    // The wrong-red strike stays at full strength over its dimmed option.
    if(!ok&&r>0)S.fade(clamp(p*2.3),()=>S.strike(ox-bw/2+18,ox+bw/2-18,oy,r,{color:T.wrong,width:5}));
    const tag=tags?.[i];
    if(tag&&tg>0)S.fade(tg*(ok?1:.9),()=>{const sw=tag.state?36:0,tx=ox-(S.measure(tag.text,role('label'))+sw)/2;
      if(tag.state)S.swatch(`q-ts${i}`,tag.state,tx,oy+68,{size:26});
      S.text(`q-t${i}`,tag.text,tx+sw,oy+68,{role:'label',color:T.white});});});
  if(reason)S.sentence('q-reason',reason,x,pic?y+205:y+178,{t,times:at.reason||stagger(reason,revealAt+.6,.1),reveal:'blur',role:'accentMd',over:{size:36},color:T.white,align:'center',maxWidth:1100});
  return {art:box,optionsY:oy};
}

// ---------------------------------------------------------------- top-band chrome
// The top band (above the content viewport) holds only the progress rail (left) and the fiction
// badge (right), on one line at PAGE.bandY, in the chrome role (18 px, its own floor). Both are
// decor drawn outside the content clip: call them at the top level of a frame, after the scene.
// Decor is not registered, so the band checks its own fit through the audit (S.check):
//   rail-fit    the rail ends inside the frame (by PAGE.badgeRight)
//   rail-badge  in a frame where both show, the rail ends BAND_GAP before the badge
// Each records its extent on the frame's stage; whichever draws second runs rail-badge.
const BAND=new WeakMap(),BAND_GAP=20;
function bandFit(S,part,x0,x1) {
  const b=BAND.get(S)||{};b[part]=[x0,x1];BAND.set(S,b);
  if(b.rail&&b.badge)S.check('rail-badge',b.rail[1]+BAND_GAP<=b.badge[0],+b.rail[1].toFixed(1),'rail ends by x '+Math.floor(b.badge[0]-BAND_GAP)+', before the fiction badge');
}

// Progress rail: the opener's agenda persists in the top band as quiet orientation chrome.
// The current section is inverted ink (an ink block with white type), never the signal colour,
// which belongs to what is being spoken about now; done sections settle to inkSoft.
// It never draws over a night panel: it is hidden on a night stage, and `night` windows
// ([[from, until], ...], such as a wipe into a night question) fade it out before the night
// ground arrives and back in after it leaves. states: one state name per step (optional) puts
// that state's swatch after each label, so the rail keeps the course's state code in view.
// Tracked capitals make the rail wide: keep labels short (rail-fit and rail-badge fail when it
// runs off the frame or under the badge). Returns the rail's box while it shows, otherwise null.
function progressRail(S,t,{steps,at,from,until,night=[],states=null}) {
  const show=seg(t,from,.6)*(1-seg(t,until,.6))*night.reduce((k,w)=>k*beforePush(t,w,{d:.4}),1);if(show<=.002||S.night)return null;
  let active=-1;at.forEach((a,i)=>{if(t>=a)active=i;});
  const r=role('chrome'),y=PAGE.bandY,ws=steps.map((s,i)=>S.measure(String(s).toUpperCase(),r)+16+(states?.[i]?24:0));
  // Block i spans [x - 8, x - 8 + its width] and the next label starts 18 px after it.
  const x0=PAGE.railLeft-8,right=x0+ws.reduce((a,w)=>a+w,0)+18*Math.max(0,ws.length-1);
  S.check('rail-fit',right<=PAGE.badgeRight,+right.toFixed(1),'rail ends by x '+PAGE.badgeRight);bandFit(S,'rail',x0,right);
  S.decor(()=>S.unclipped(()=>{const g=S.g;g.save();g.setTransform(1,0,0,1,0,0);g.filter='none';g.globalAlpha*=show;
    let x=PAGE.railLeft;steps.forEach((s,i)=>{const on=i===active,done=i<active,sw=states?.[i]?24:0,bw=ws[i],p=on?seg(t,at[i],.45,E.inOut):0,cut=x-8+bw*p;
      g.fillStyle=on?T.ink:done?T.mute:T.rule;g.fillRect(x-8,y-22,bw,3);
      if(p>0){g.fillStyle=T.ink;g.fillRect(x-8,y-13,bw*p,26);}
      // The type turns white exactly where the ink block has swept.
      g.save();g.beginPath();g.rect(cut,0,1e4,88);g.clip();S.text('rail'+i,s,x,y,{role:'chrome',color:on||done?T.inkSoft:T.mute});g.restore();
      if(p>0){g.save();g.beginPath();g.rect(x-8,0,cut-x+8,88);g.clip();S.text('rail'+i,s,x,y,{role:'chrome',color:T.white});g.restore();}
      if(sw)S.swatch('rail-s'+i,states[i],x+bw-30,y,{size:14,register:false});
      x+=bw+18;});
    g.restore();}));
  return {x:x0,y:y-22,w:right-x0,h:35};
}

// Fiction badge: a solid block in the fiction hue (used for nothing else) with white uppercase
// chrome type, right-aligned in the top band on the rail's line; on night it gains a thin light
// keyline so it reads on both grounds.
// Rule: keep it on whenever invented people, companies or figures are on screen, including
// practice panels; switch it OFF over purely real facts. Split the windows around real material
// instead of leaving the badge on across it. windows: [[from, until], ...]; {from, until} = one window.
// Returns the badge box while it shows, otherwise null.
function fictionBadge(S,t,{windows,from,until=Infinity,label='Fictional example'}={}) {
  const list=windows??(from!=null?[[from,until]]:[]);
  const show=list.reduce((m,[a,b=Infinity])=>Math.max(m,seg(t,a,.6)*(1-seg(t,b,.6))),0);if(show<=.002)return null;
  const r=role('chrome'),w=S.measure(String(label).toUpperCase(),r)+28,x=PAGE.badgeRight-w,y=PAGE.bandY;bandFit(S,'badge',x,PAGE.badgeRight);
  S.decor(()=>S.unclipped(()=>{const g=S.g;g.save();g.setTransform(1,0,0,1,0,0);g.filter='none';g.globalAlpha*=show;
    g.fillStyle=T.fiction;g.fillRect(x,y-15,w,30);
    if(S.night){g.strokeStyle=T.white;g.lineWidth=1.5;g.strokeRect(x-.75,y-15.75,w+1.5,31.5);}
    S.text('fic-badge',label,x+14,y+.5,{role:'chrome',color:T.fictionInk});g.restore();}));
  return {x,y:y-15,w,h:30};
}

module.exports={MIN_SPAN,PAGE,PARTS,PART_LAYOUTS,MOTIFS,defineParts,partKey,partLayout,partOpener,opener,sectionHead,readout,stateKey,
  statement,carry,compare,lineStory,stepper,question,progressRail,fictionBadge};
