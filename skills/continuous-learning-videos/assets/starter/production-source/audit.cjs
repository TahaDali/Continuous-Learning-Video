'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {createCanvas}=require(process.env.CANVAS_MODULE||'@napi-rs/canvas'),{draw}=require('./world.cjs');
const root=path.resolve(__dirname,'..'),course=require(path.join(root,'course.json'));
const allowances=require('./intentional-overlaps.json');
for(const a of allowances)if(!a.lesson||!a.a||!a.b||!Number.isFinite(a.start)||!Number.isFinite(a.end)||a.start>=a.end||!a.reason?.trim())throw new Error('Invalid intentional-overlap rule');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const report={method:'All output-frame timestamps; visible registered axis-aligned actor and label bounds after camera transform, plus label safe zones. Fully offscreen actors are ignored and actors may cross the clipped viewport. Excludes connector paths, glyph internals and raster/perceptual effects. Owner-contained labels are intentional.',fps:course.fps,sourceHashes:{},lessons:[],unresolvedPairs:0,totalFrames:0};
for(const name of ['course.json','production-source/world.cjs','production-source/motion.cjs','production-source/intentional-overlaps.json',...(course.renderSources||[])])report.sourceHashes[name]=sha(path.join(root,name));
const framesDir=path.join(root,'review/flagged');
if(fs.existsSync(framesDir)&&fs.readdirSync(framesDir).length){
  const history=fs.mkdtempSync(path.join(root,'review/audit-history-'));
  const previous=path.join(root,'review/frame-audit.json');
  if(fs.existsSync(previous))fs.copyFileSync(previous,path.join(history,'frame-audit.json'));
  fs.renameSync(framesDir,path.join(history,'flagged'));
  report.previousFindingsArchived=path.basename(history);
}
fs.mkdirSync(framesDir,{recursive:true});
const intersects=(a,b)=>Math.min(a.x+a.w,b.x+b.w)>Math.max(a.x,b.x)&&Math.min(a.y+a.h,b.y+b.h)>Math.max(a.y,b.y);
const inside=(a,b)=>a.x>=b.x&&a.y>=b.y&&a.x+a.w<=b.x+b.w&&a.y+a.h<=b.y+b.h;
const c=createCanvas(course.width,course.height),g=c.getContext('2d');
for(const l of course.lessons) {
  const issues=new Map(),accepted=new Map(),n=Math.ceil(l.duration*course.fps);
  for(let frame=0;frame<n;frame++) {
    const t=frame/course.fps,s=draw(g,l,t,course),items=s.items.filter(i=>i.alpha>.1&&intersects(i.bounds,s.viewport)),problems=[];
    for(const a of items)if(a.kind==='label'&&!inside(a.bounds,s.safe))problems.push({type:'safe-zone',a:a.id});
    for(let i=0;i<items.length;i++)for(let j=i+1;j<items.length;j++) {
      const a=items[i],b=items[j];
      if((a.owner===b.id&&inside(a.bounds,b.bounds))||(b.owner===a.id&&inside(b.bounds,a.bounds)))continue;
      if(intersects(a.bounds,b.bounds))problems.push({type:'intersection',a:a.id,b:b.id});
    }
    if(s.invariants?.expectedTotal!==undefined&&Math.abs(s.invariants.totalUnits-s.invariants.expectedTotal)>1e-6)problems.push({type:'conservation',a:'displayed-total',actual:s.invariants.totalUnits,expected:s.invariants.expectedTotal});
    for(const check of s.invariants?.checks||[])if(check.passed!==true)problems.push({type:'mechanism-invariant',a:check.id,actual:check.actual,expected:check.expected});
    for(const p of problems) {
      const reason=allowances.find(a=>a.lesson===l.id&&t>=a.start&&t<=a.end&&((p.a===a.a&&p.b===a.b)||(p.a===a.b&&p.b===a.a)))?.reason;
      const target=reason?accepted:issues,key=[p.type,p.a,p.b||''].join(':');
      if(!target.has(key)) {
        const value={...p,firstFrame:frame,lastFrame:frame,frames:1,reason:reason||null};
        if(!reason){const filename=`${l.id}-${frame}-${issues.size}.png`;fs.writeFileSync(path.join(framesDir,filename),c.toBuffer('image/png'));value.preview='flagged/'+filename;}
        target.set(key,value);
      } else {const v=target.get(key);v.lastFrame=frame;v.frames++;}
    }
  }
  report.lessons.push({id:l.id,frames:n,unresolved:[...issues.values()],intentional:[...accepted.values()]});
  report.totalFrames+=n;report.unresolvedPairs+=issues.size;
  console.log(`${l.id}: ${n} frames, ${issues.size} unresolved, ${accepted.size} intentional`);
}
fs.writeFileSync(path.join(root,'review/frame-audit.json'),JSON.stringify(report,null,2)+'\n');
if(report.unresolvedPairs)process.exitCode=1;
