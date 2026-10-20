'use strict';
// Reusable scene templates for design.cjs. Each one owns the hierarchy and choreography of a
// single teaching move; the subject's own mechanism still belongs in world.cjs.
// Timing: every template takes its scene `start` and `end` plus an optional `at` object of
// narration cue times (from createCues). Missing `at` entries fall back to a compact stagger
// from `start`. Given `end`, a template asserts through the frame audit that the spoken span
// leaves room for its choreography, so short narration fails loudly instead of truncating.
// Every template registers its text and solid objects, so the geometry audit still applies.
// See references/video/design-system.md for when to use each one.
const {T,E,role,seg,lerp,wordTimes}=require('./design.cjs');
const words=s=>String(s).split(/\s+/).filter(Boolean);
const stagger=(s,from,step)=>words(s).map((_,i)=>from+i*step);
// Minimum spoken span, in seconds, that each template's choreography needs.
const MIN_SPAN={opener:4.5,statement:3,compare:6,lineStory:6,stepper:5,question:6};

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
    let cx=x;agenda.forEach((label,i)=>{const b=S.chip(`open-agenda${i}`,label,cx,y+215+lift,{p:seg(t,at.agenda?.[i]??start+2.8+i*.18,.55,E.linear),
      fill:T.paperLo,color:T.ink,align:'left',role:'label'});cx+=b.w+14;});
  });
}

// Statement: the whole sentence is present as a ghost and words fill as they are spoken.
// One emphasis word receives a highlighter. From exitAt the context clears quickly while the emphasis
// slot stays empty; the returned position lets carry() move that word into the next scene.
// times: one onset per word (cue.phrase); without it the scene's word timings are used.
function statement(S,t,{id='claim',x,y,scene,text,emphasis,start,end,markAt,exitAt=Infinity,times:given}) {
  S.fits('statement',start,end,MIN_SPAN.statement);
  const list=words(text),{times,method}=given?{times:given,method:'cued'}:wordTimes(list,scene);
  const k=list.findIndex(w=>w.replace(/[^\w$%]/g,'')===emphasis);
  if(k<0)throw new Error(`Statement emphasis is not in its text: ${emphasis}`);
  const opts={role:'headline',over:{size:56},maxWidth:1040,align:'center'},L=S.layout(text,opts),exit=seg(t,exitAt,.35,E.out);
  if(exit<=0)S.fade(seg(t,start,.35),()=>S.sentence(id,text,x,y,{t,times,reveal:'ghost',dur:.35,...opts,
    styles:{[k]:{mark:{p:seg(t,markAt??times[k],.55,E.inOut),color:T.gold}}}}));
  else S.fade(1-exit,()=>S.sentence(id,text,x,y,{t:Infinity,times,reveal:'none',...opts,styles:{[k]:{hidden:true}}}));
  const q=L.words[k];
  return {timing:method,emphasis:{x:x-q.lineWidth/2+q.x,y:y-(L.lines-1)*L.lh/2+q.line*L.lh,w:q.w,size:L.r.size}};
}

// Carry: one word or number travels from where it was said to where it now lives.
// Use it for the hero object of a scene change instead of fading one copy out and another in.
function carry(S,t,{id,text,from,to,start,end,fromRole='headline',fromSize,toRole='numeralSm',toColor=T.teal}) {
  if(t<start||t>=end)return false;
  const p=seg(t,start,end-start,E.inOut),r0=role(fromRole,fromSize?{size:fromSize}:undefined),r1=role(toRole);
  S.text(id,text,lerp(from[0],to[0],p),lerp(from[1],to[1],p),{role:fromRole,over:{size:lerp(r0.size,r1.size,p)},align:'center',color:p>.5?toColor:T.ink});
  return true;
}

// Compare: two columns separated by a drawn divider; old values are struck and new values pop.
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
      if(r.from!==r.to)S.strike(cx+238,cx+302,ry,seg(t,a+.55,.4),{color:T.accent,width:4});
      S.arrow([cx+318,ry],[cx+362,ry],seg(t,a+.6,.35,E.inOut),{bend:0,color:T.mute,width:2.4,head:10});
      S.chip(`cmp-${side}-v${i}`,String(r.to),cx+420,ry,{p:seg(t,a+.85,.55,E.linear),fill:r.from===r.to?T.tealSoft:T.accentSoft,color:T.ink,role:'numeralSm',padX:14,padY:6});
      if(r.check)S.partial([[cx+482,ry],[cx+494,ry+13],[cx+518,ry-14]],seg(t,a+1.3,.4,E.inOut),{color:T.teal,width:5});
    });});
  col('l',lx,left,dim,at.left);col('r',rx,right,1,at.right);
  if(takeaway)S.sentence('cmp-take',takeaway,x,y+200,{t,times:at.takeaway||stagger(takeaway,focusAt+.4,.12),reveal:'blur',role:'accentMd',over:{size:36},align:'center',maxWidth:1100});
}

// Line story: axes draw, series trace with dots, the invariant lands last in the accent colour.
// Series swing while the invariant stays flat; the note names that contrast.
// at: {title:[...], series:[one onset per series], invariant}
function lineStory(S,t,{x,y,start,end,kicker,title,series,invariant,labels,focusAt,note,max,at={}}) {
  S.fits('lineStory',start,end,MIN_SPAN.lineStory);
  const top=max??Math.max(invariant?.value??0,...series.flatMap(s=>s.values));
  const X0=x-520,X1=x+380,Y0=y+195,Y1=y-125,px=i=>lerp(X0+20,X1,i/(labels.length-1)),py=v=>lerp(Y0,Y1,v/top);
  if(kicker)S.fade(seg(t,start+.1,.4),()=>S.text('ls-kicker',kicker,X0-40,y-228,{role:'kicker',color:T.teal}));
  S.sentence('ls-title',title,X0-40,y-190,{t,times:at.title||stagger(title,start+.2,.15),reveal:'rise',role:'headline'});
  S.partial([[X0,Y0],[X1+40,Y0]],seg(t,start+.4,.6,E.inOut),{color:T.inkSoft,width:2});
  labels.forEach((l,i)=>S.fade(seg(t,start+.6+i*.08,.3),()=>S.text(`ls-x${i}`,l,px(i),Y0+28,{role:'label',over:{size:20},color:T.inkSoft,align:'center'})));
  const dim=1-.7*seg(t,focusAt,.6,E.inOut);
  series.forEach((s,si)=>S.fade(dim,()=>{
    const pts=s.values.map((v,i)=>[px(i),py(v)]),a=at.series?.[si]??start+.9+si*.35,p=seg(t,a,2.2,E.inOut);
    S.partial(pts,p,{color:s.color,width:5});
    S.decor(()=>pts.forEach((q,i)=>{const r=seg(t,a+2.2*i/(pts.length-1)-.05,.3,E.outBack);if(r>0){S.g.fillStyle=s.color;S.g.beginPath();S.g.arc(q[0],q[1],7*r,0,Math.PI*2);S.g.fill();}}));
    S.chip(`ls-${s.id}`,s.name,X1+30,py(s.values.at(-1)),{p:seg(t,a+2.2,.5,E.linear),fill:s.color,color:T.white,role:'label',align:'left',padX:11,padY:5});
  }));
  let anchor=[X1,Y1];
  if(invariant) {
    const ia=at.invariant??start+3.4,iy=py(invariant.value);anchor=[X1,iy];
    S.partial([[X0+20,iy],[X1,iy]],seg(t,ia,1,E.inOut),{color:T.accent,width:6});
    S.chip('ls-total',invariant.name,X1+30,iy,{p:seg(t,ia+.9,.5,E.linear),fill:T.accent,color:T.white,role:'label',align:'left',padX:11,padY:5});
    if(note) {
      S.fade(seg(t,focusAt+.4,.5),()=>S.text('ls-note',note,X1-10,y-215,{role:'accentSm',over:{size:30},color:T.accent,align:'right'}));
      S.arrow([X1-120,y-196],[X1-180,iy-14],seg(t,focusAt+.7,.6,E.inOut),{bend:.3,color:T.accent,width:2.4});
    }
  }
  return {anchor};
}

// Stepper: a persistent token travels down a rail; each step activates, then settles.
// stepAt: one onset per step (normally the cue of each step's first spoken word).
// at: {title:[...], accent:[...]}
function stepper(S,t,{x,y,start,end,title,accent,steps,stepAt,at={}}) {
  S.fits('stepper',start,end,MIN_SPAN.stepper);
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
  // The travelling token keeps the identity of the quantity the steps act on.
  const from=moving?ys[k-1]:ys[Math.max(0,active)],to=ys[Math.max(0,k>=0?k:active)],p=moving?seg(t,stepAt[k],.6,E.inOut):1;
  const ty=lerp(from,to,p),pop=seg(t,stepAt[0]-.3,.5,E.outBack);
  if(pop>0)S.actor('st-token',{x:rx-22*pop,y:ty-22*pop,w:44*pop,h:44*pop},g=>{g.fillStyle=T.gold;g.beginPath();g.arc(rx,ty,20*pop,0,Math.PI*2);g.fill();
    g.strokeStyle=T.ink;g.lineWidth=2.5;g.stroke();});
}

// Question: a ghosted prompt fills, options pop, and the correct one resolves with its reason.
// Designed for the night background so the check reads as a different mode.
// at: {kicker, prompt:[...], options, reason:[...]}
function question(S,t,{x,y,start,end,kicker,prompt,options,correct,revealAt,reason,scene,at={}}) {
  S.fits('question',start,end,MIN_SPAN.question);
  S.fade(seg(t,at.kicker??start+.3,.4),()=>S.text('q-kicker',kicker,x-510,y-190,{role:'kicker',color:T.gold}));
  const times=at.prompt||wordTimes(words(prompt),scene,{from:start+.6,to:start+2.6}).times,optionsAt=at.options??times.at(-1)+.3;
  S.sentence('q-prompt',prompt,x-510,y-110,{t,times,reveal:'ghost',ghost:.14,dur:.3,role:'headline',maxWidth:1000,color:T.white});
  options.forEach((o,i)=>{const ox=x-300+i*300,ok=i===correct,r=seg(t,revealAt,.5,E.linear);
    S.fade(ok?1:1-.6*r,()=>{
      const b=S.chip(`q-o${i}`,o,ox,y+60,{p:seg(t,optionsAt+i*.15,.55,E.linear),fill:ok&&r>0?T.gold:T.nightHi,color:ok&&r>0?T.ink:T.white,role:'numeral',padX:34,padY:14,radius:22});
      if(!ok)S.strike(b.x+18,b.x+b.w-18,y+60,r,{color:T.accent,width:4});
    });});
  S.sentence('q-reason',reason,x,y+178,{t,times:at.reason||stagger(reason,revealAt+.6,.1),reveal:'blur',role:'accentMd',over:{size:36},color:T.white,align:'center',maxWidth:1100});
}

// Progress rail: the opener's agenda persists in the top band as quiet orientation chrome.
// It sits outside the content viewport, so it is decor and never competes with the scene.
function progressRail(S,t,{steps,at,from,until}) {
  const show=seg(t,from,.6)*(1-seg(t,until,.6));if(show<=0)return;
  let active=-1;at.forEach((a,i)=>{if(t>=a)active=i;});
  S.decor(()=>S.unclipped(()=>{const g=S.g;g.save();g.setTransform(1,0,0,1,0,0);g.globalAlpha=show;
    let x=40;steps.forEach((s,i)=>{const on=i===active,done=i<active,w=S.measure(s,role('small'))+28;
      g.fillStyle=on?T.ink:done?T.mute:T.rule;g.fillRect(x,40,w-12,3);
      S.text('rail'+i,s,x,58,{role:'small',color:on?T.ink:T.mute});x+=w+6;});
    g.restore();}));
}

module.exports={MIN_SPAN,opener,statement,carry,compare,lineStory,stepper,question,progressRail};
