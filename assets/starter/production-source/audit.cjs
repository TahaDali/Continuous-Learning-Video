'use strict';
// node audit.cjs [--force] [--jobs N]      the whole course -> review/frame-audit.json
// node audit.cjs --lesson <lessonId>       one lesson       -> review/lesson-audits/<lessonId>.json
// Replays every output-frame timestamp of every lesson. A lesson whose picture dependencies and
// rules are unchanged since its last clean audit keeps that result; --force replays all of them.
// The one-lesson form touches only that lesson's files, so lessons can be audited side by side
// while they are authored; the course audit keeps a clean one-lesson result that is still current.
const fs=require('fs'),path=require('path'),os=require('os'),{spawn}=require('child_process');
const canvasModule=require(process.env.CANVAS_MODULE||'@napi-rs/canvas'),{createCanvas}=canvasModule;
const root=path.resolve(__dirname,'..'),course=require(path.join(root,'course.json'));
const {sourcePaths}=require('./render-sources.cjs');
const {fileSha,drawFor,lessonView,lessonIdentity,canvasVersion}=require('./lesson-scope.cjs');
const authoredSources=sourcePaths(root,course);
if(authoredSources.includes('production-source/design.cjs'))require('./design.cjs').installDesignRuntime(canvasModule);

let force=false,jobs,only,emit;
for(let i=2;i<process.argv.length;i++) {
  const a=process.argv[i];
  if(a==='--force')force=true;
  else if(a==='--jobs')jobs=Number(process.argv[++i]);
  else if(a.startsWith('--jobs='))jobs=Number(a.slice(7));
  else if(a==='--lesson')only=process.argv[++i];
  // Internal: a course audit's child process writes its lesson record to this file.
  else if(a==='--emit')emit=process.argv[++i];
  else throw new Error('Unknown option: '+a);
}
if(jobs===undefined)jobs=os.availableParallelism();
if(!Number.isInteger(jobs)||jobs<1)throw new Error('--jobs needs a positive whole number');

// Rules live in intentional-overlaps.json, or beside a lesson's own module as worlds/<lessonId>.overlaps.json.
const allowances=[...require('./intentional-overlaps.json')];
for(const l of course.lessons) {
  const name='production-source/worlds/'+l.id+'.overlaps.json';
  if(!authoredSources.includes(name))continue;
  const own=JSON.parse(fs.readFileSync(path.join(root,name)));
  if(!Array.isArray(own))throw new Error('Invalid intentional-overlap rule file: '+name);
  for(const rule of own) {
    if(rule.lesson!==undefined&&rule.lesson!==l.id)throw new Error('Invalid intentional-overlap rule: '+name+' names another lesson');
    allowances.push({...rule,lesson:l.id});
  }
}
// A rule's window is absolute seconds, or a named scene so it follows narration-driven retiming.
const windowOf=a=>{
  if(a.scene===undefined)return Number.isFinite(a.start)&&Number.isFinite(a.end)&&a.start<a.end?a:null;
  const scene=a.start===undefined&&a.end===undefined&&course.lessons.find(l=>l.id===a.lesson)?.scenes?.find(s=>s.id===a.scene);
  return scene||null;
};
// A pair rule names two objects that may touch. A rule with type "flash" names one label that may
// be on screen for less than half a second.
for(const a of allowances)if(!a.lesson||!a.a||![undefined,'flash'].includes(a.type)||(a.type==='flash'?a.b!==undefined:!a.b)||!windowOf(a)||!a.reason?.trim())throw new Error('Invalid intentional-overlap rule');

// Flagged frames: the course audit's folder, or one lesson's own when it is audited alone.
const alone=only!==undefined&&emit===undefined,lessonAudits=path.join(root,'review/lesson-audits');
const framesDir=alone?path.join(lessonAudits,only+'-flagged'):path.join(root,'review/flagged');
const framesName=path.relative(path.join(root,'review'),framesDir).split(path.sep).join('/');
const intersects=(a,b)=>Math.min(a.x+a.w,b.x+b.w)>Math.max(a.x,b.x)&&Math.min(a.y+a.h,b.y+b.h)>Math.max(a.y,b.y);
const inside=(a,b)=>a.x>=b.x&&a.y>=b.y&&a.x+a.w<=b.x+b.w&&a.y+a.h<=b.y+b.h;
const identityOf=l=>lessonIdentity(root,course,l,{use:'audit',auditor:fileSha(__filename),canvas:canvasVersion(),fps:course.fps,rules:allowances.filter(a=>a.lesson===l.id)});
let stage;
const canvas=()=>{if(!stage){const c=createCanvas(course.width,course.height),g=c.getContext('2d');stage={c,g,counts:require('./finite-canvas.cjs').install(g)};}return stage;};

function auditLesson(l) {
  const {g,counts}=canvas(),draw=drawFor(root,l),view=lessonView(course,l),fps=course.fps,before={...counts};
  const rules=allowances.filter(a=>a.lesson===l.id),declared=(l.scenes||[]).filter(s=>typeof s.fiction==='boolean');
  const issues=new Map(),accepted=new Map(),n=Math.ceil(l.duration*fps),transitions=[];let transitionFrames=0;
  // Labels by their unbroken time on screen: one that becomes readable (at least half opaque) and is
  // gone within half a second is a flash. A word ghosted for seconds and filled late is not.
  const runs=new Map(),flashes=[],readableFrames=Math.ceil(.5*fps-1e-9);
  // A flagged frame is drawn again on its own canvas: reading the audit canvas back would first
  // rasterize every frame replayed so far.
  function preview(frame) {
    const shot=createCanvas(course.width,course.height);draw(shot.getContext('2d'),l,frame/fps,view);return shot.toBuffer('image/png');
  }
  function file(p,reason,first,last,frames,shown=first) {
    const target=reason?accepted:issues,key=[p.type,p.a,p.b||''].join(':');
    if(!target.has(key)) {
      const value={...p,firstFrame:first,lastFrame:last,frames,reason:reason||null};
      if(!reason){const filename=`${l.id}-${first}-${issues.size}.png`;fs.writeFileSync(path.join(framesDir,filename),preview(shown));value.preview=framesName+'/'+filename;}
      target.set(key,value);
    } else {const v=target.get(key);v.lastFrame=last;v.frames+=frames;}
  }
  for(let frame=0;frame<n;frame++) {
    const t=frame/fps,s=draw(g,l,t,view),moving=s.transition===true;
    if(moving){transitionFrames++;const open=transitions.at(-1);if(open&&open[1]===frame-1)open[1]=frame;else transitions.push([frame,frame]);}
    for(const item of s.items)if(!Number.isFinite(item.alpha)||!['x','y','w','h'].every(k=>Number.isFinite(item.bounds?.[k]))||item.bounds.w<0||item.bounds.h<0)throw Error('Invalid registered geometry '+l.id+' / frame '+frame+' / '+item.id);
    const byId=new Map(s.items.map(i=>[i.id,i]));
    const ownedBy=(child,parent)=>{const visited=new Set([child.id]);let next=child.owner;while(next){if(visited.has(next))throw Error('Cyclic audit ownership: '+child.id);visited.add(next);if(next===parent.id)return true;next=byId.get(next)?.owner;}return false;};
    // Explicit ancestors describe nested illustrated composites. Shared ownership
    // does not exempt sibling collisions; every descendant must fit its ancestor.
    const items=s.items.filter(i=>i.alpha>.1&&intersects(i.bounds,s.viewport)),problems=[];
    for(const a of items)if(a.kind==='label'&&!inside(a.bounds,s.safe))problems.push({type:'safe-zone',a:a.id});
    for(let i=0;i<items.length;i++)for(let j=i+1;j<items.length;j++) {
      const a=items[i],b=items[j];
      if((ownedBy(a,b)&&inside(a.bounds,b.bounds))||(ownedBy(b,a)&&inside(b.bounds,a.bounds)))continue;
      if(intersects(a.bounds,b.bounds))problems.push({type:'intersection',a:a.id,b:b.id});
    }
    if(s.invariants?.expectedTotal!==undefined&&Math.abs(s.invariants.totalUnits-s.invariants.expectedTotal)>1e-6)problems.push({type:'conservation',a:'displayed-total',actual:s.invariants.totalUnits,expected:s.invariants.expectedTotal});
    for(const check of s.invariants?.checks||[])if(check.passed!==true)problems.push({type:'mechanism-invariant',a:check.id,actual:check.actual,expected:check.expected});
    // A scene that declares `fiction` is checked against the badge the stage reports, away from
    // its edges where the badge fades and outside transitions.
    if(!moving)for(const scene of declared) {
      const grace=Math.min(1,(scene.end-scene.start)/3);
      if(t<scene.start+grace||t>scene.end-grace)continue;
      const level=Number(s.notes?.fictionBadge)||0;
      if(scene.fiction?level<.5:level>.1)problems.push({type:'fiction-badge',a:scene.id,actual:+level.toFixed(2),
        expected:scene.fiction?'badge on: the scene declares invented material':'badge off: the scene declares real facts only'});
    }
    for(const p of problems) {
      const reason=rules.find(a=>a.type===undefined&&t>=windowOf(a).start&&t<=windowOf(a).end&&((p.a===a.a&&p.b===a.b)||(p.a===a.b&&p.b===a.a)))?.reason;
      file(p,reason,frame,frame,1);
    }
    // Transition frames register nothing, so they neither extend nor end a label's time on screen.
    if(!moving) {
      const present=new Set();
      for(const item of items)if(item.kind==='label') {
        present.add(item.id);let run=runs.get(item.id);
        if(!run)runs.set(item.id,run={id:item.id,first:frame,shown:0,peak:0});
        run.last=frame;run.shown++;run.peak=Math.max(run.peak,item.alpha);
      }
      for(const [id,run] of runs)if(!present.has(id)){runs.delete(id);if(run.peak>=.5&&run.shown<readableFrames)flashes.push(run);}
    }
  }
  // A label still on screen at the last frame stays until the lesson ends; it is not a flash.
  const operations=Object.fromEntries(Object.entries(counts).map(([k,v])=>[k,v-(before[k]||0)]).filter(([,v])=>v));
  for(const run of flashes) {
    const reason=rules.find(a=>a.type==='flash'&&a.a===run.id&&run.first/fps>=windowOf(a).start&&run.last/fps<=windowOf(a).end)?.reason;
    file({type:'flash',a:run.id,actual:+(run.shown/fps).toFixed(2),expected:'on screen for at least 0.5 s'},reason,run.first,run.last,run.shown,Math.floor((run.first+run.last)/2));
  }
  // Frames whose stage declared a pan, iris or wipe; their transition drawing is unregistered.
  return {id:l.id,frames:n,transitionFrames,unresolved:[...issues.values()],intentional:[...accepted.values()],
    transitions:transitions.map(([a,b])=>[+(a/fps).toFixed(3),+((b+1)/fps).toFixed(3)]),identity:identityOf(l),canvasOperations:operations};
}

const line=r=>`${r.id}: ${r.frames} frames, ${r.unresolved.length} unresolved, ${r.intentional.length} intentional${r.transitionFrames?`, ${r.transitionFrames} transition`:''}`;
if(only!==undefined) {
  const l=course.lessons.find(x=>x.id===only);
  if(!l)throw new Error('No lesson '+only+' in course.json');
  if(emit){fs.writeFileSync(emit,JSON.stringify(auditLesson(l)));return;}
  fs.rmSync(framesDir,{recursive:true,force:true});fs.mkdirSync(framesDir,{recursive:true});
  const record=auditLesson(l);
  fs.writeFileSync(path.join(lessonAudits,l.id+'.json'),JSON.stringify(record,null,2)+'\n');
  console.log(line(record));
  for(const u of record.unresolved)console.log(`  ${u.type} ${u.a}${u.b?' / '+u.b:''}: frames ${u.firstFrame}-${u.lastFrame}${u.expected!==undefined?`, ${u.actual} (expected ${u.expected})`:''} -> review/${u.preview}`);
  if(record.unresolved.length)process.exitCode=1;else fs.rmSync(framesDir,{recursive:true,force:true});
  return;
}

const sha=p=>fileSha(p);
const report={method:'All output-frame timestamps; visible registered axis-aligned actor and label bounds after camera transform, plus label safe zones, label time on screen (a label that becomes readable stays on screen for at least 0.5 s) and the fiction badge against scenes that declare `fiction`. Fully offscreen actors are ignored and actors may cross the clipped viewport. Excludes connector paths, glyph internals, declared transition and decor drawing, and raster/perceptual effects. Owner-contained labels are intentional. A lesson marked reused kept its result because its sources, lesson record, rules and auditor are unchanged since that clean audit.',fps:course.fps,sourceHashes:{},lessons:[],unresolvedPairs:0,totalFrames:0};
for(const name of ['course.json','production-source/intentional-overlaps.json',...authoredSources])report.sourceHashes[name]=sha(path.join(root,name));
const previous=path.join(root,'review/frame-audit.json'),clean=new Map();
const keep=r=>{if(r&&r.identity&&Array.isArray(r.unresolved)&&!r.unresolved.length)clean.set(r.identity,r);};
if(!force) {
  try{JSON.parse(fs.readFileSync(previous)).lessons.forEach(keep);}catch{}
  // A lesson audited alone while it was authored counts, if nothing it depends on has changed since.
  for(const l of course.lessons)try{keep(JSON.parse(fs.readFileSync(path.join(lessonAudits,l.id+'.json'))));}catch{}
}
if(fs.existsSync(framesDir)&&fs.readdirSync(framesDir).length){
  const history=fs.mkdtempSync(path.join(root,'review/audit-history-'));
  if(fs.existsSync(previous))fs.copyFileSync(previous,path.join(history,'frame-audit.json'));
  fs.renameSync(framesDir,path.join(history,'flagged'));
  report.previousFindingsArchived=path.basename(history);
}
fs.mkdirSync(framesDir,{recursive:true});

function child(l) {
  return new Promise((resolve,reject)=>{
    const out=path.join(root,'review',`.audit-${l.id}-${process.pid}.json`);
    spawn(process.execPath,[__filename,'--lesson',l.id,'--emit',out],{stdio:'inherit'}).on('error',reject).on('close',code=>{
      if(code!==0)return reject(new Error('Audit failed: '+l.id));
      const record=JSON.parse(fs.readFileSync(out));fs.rmSync(out,{force:true});resolve(record);
    });
  });
}
(async()=>{
  const records=new Map(),pending=[];
  for(const l of course.lessons) {
    const kept=clean.get(identityOf(l));
    if(kept&&kept.id===l.id)records.set(l.id,{...kept,reused:true});else pending.push(l);
  }
  if(jobs>1&&pending.length>1) {
    const queue=[...pending];let failure;
    await Promise.all(Array.from({length:Math.min(jobs,queue.length)},async()=>{
      while(queue.length&&!failure){const l=queue.shift();try{records.set(l.id,await child(l));}catch(e){failure=e;}}
    }));
    if(failure)throw failure;
  } else for(const l of pending)records.set(l.id,auditLesson(l));
  const operations={};
  for(const l of course.lessons) {
    const r=records.get(l.id);
    report.lessons.push(r);report.totalFrames+=r.frames;report.unresolvedPairs+=r.unresolved.length;
    for(const [k,v] of Object.entries(r.canvasOperations||{}))operations[k]=(operations[k]||0)+v;
    console.log(line(r)+(r.reused?' (unchanged since its last clean audit)':''));
  }
  report.numericCanvas={scope:'Finite numeric arguments to wrapped Canvas methods, including calls inside glyph callbacks. Excludes direct state-property assignments, Path2D internals, unwrapped methods and raster/semantic correctness.',operations};
  fs.writeFileSync(previous,JSON.stringify(report,null,2)+'\n');
  if(report.unresolvedPairs)process.exitCode=1;
})().catch(e=>{console.error(e.message);process.exitCode=1;});
