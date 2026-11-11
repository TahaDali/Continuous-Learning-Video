'use strict';
// One lesson's drawing scope. The renderer, posters and audit share it, so they agree on which
// module draws a lesson, what its picture may depend on, and whether an earlier result is current.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {sourcePaths,lessonWorld}=require('./render-sources.cjs');
// The fields narration re-timing rewrites; workflow.py ignores the same set in the script fingerprint.
const TIMING=['start','end','duration','speechStart','speechEnd','wordTimings','timingMethod','narrationVoice'];
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
const fileHashes=new Map();
const fileSha=file=>{if(!fileHashes.has(file))fileHashes.set(file,sha(fs.readFileSync(file)));return fileHashes.get(file);};

// The module that draws this lesson: production-source/worlds/<id>.cjs when it exists, else world.cjs.
function drawFor(root,lesson) {
  const name=lessonWorld(root,lesson.id),world=require(path.join(root,name));
  if(typeof world.draw!=='function')throw new Error(name+' must export draw(g, lesson, t, course)');
  return world.draw;
}

// What a lesson may read of another lesson: its descriptive fields, never its scenes or timing.
// Reading more throws, so the identity below cannot miss a dependency.
function outline(other,reader) {
  const copy={};
  for(const [key,value] of Object.entries(other)) {
    if(key==='scenes'||TIMING.includes(key))Object.defineProperty(copy,key,{enumerable:false,get(){
      throw new Error(`Lesson ${reader} read ${key} of lesson ${other.id}. A lesson's picture may use another lesson's title, part and goal, not its scenes or timing; put shared values in a course-level field.`);}});
    else copy[key]=value;
  }
  return copy;
}
const views=new WeakMap();
// The course as this lesson's world receives it. One object per lesson, so per-course caches hold.
function lessonView(course,lesson) {
  if(!views.has(lesson))views.set(lesson,{...course,lessons:course.lessons.map(l=>l===lesson?lesson:outline(l,lesson.id))});
  return views.get(lesson);
}

// A stable identity of everything the lesson's picture depends on: its own source files, its own
// lesson record with timing, the course-level fields and the other lessons' descriptive fields.
// `extra` names the consumer (renderer or audit) and its own settings.
function lessonIdentity(root,course,lesson,extra={}) {
  const sources=Object.fromEntries(sourcePaths(root,course,lesson.id).map(name=>[name,fileSha(path.join(root,name))]));
  const {lessons,...shared}=course;
  const others=lessons.filter(l=>l!==lesson).map(l=>Object.fromEntries(Object.entries(l).filter(([k])=>k!=='scenes'&&!TIMING.includes(k))));
  return sha(JSON.stringify({sources,lesson,shared,others,extra}));
}

// The loaded canvas module's version changes pixels, so it belongs to every identity.
function canvasVersion() {
  try{return require((process.env.CANVAS_MODULE||'@napi-rs/canvas')+'/package.json').version;}catch{return null;}
}

module.exports={TIMING,sha,fileSha,drawFor,lessonView,lessonIdentity,canvasVersion};
