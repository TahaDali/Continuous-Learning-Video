'use strict';
// node render.cjs [all|<lessonId>[,<lessonId>...]|posters] [--silent-preview] [--force] [--jobs N]
// A lesson's picture is drawn and encoded once, to review/silent/<lessonId>.mp4. The narrated
// deliverable copies that video stream and adds audio and captions, so the final picture is the
// reviewed picture bit for bit. A picture is redrawn only when what it depends on has changed.
const fs=require('fs'),path=require('path'),os=require('os'),{spawn}=require('child_process'),{once}=require('events');
const canvasModule=require(process.env.CANVAS_MODULE||'@napi-rs/canvas'),{createCanvas}=canvasModule;
const root=path.resolve(__dirname,'..');
const course=JSON.parse(fs.readFileSync(path.join(root,'course.json')));
const sources=require('./render-sources.cjs').sourcePaths(root,course);
if(sources.includes('production-source/design.cjs'))require('./design.cjs').installDesignRuntime(canvasModule);
const {sha,fileSha,drawFor,lessonView,lessonIdentity,canvasVersion}=require('./lesson-scope.cjs');
const {install:checkCanvas}=require('./finite-canvas.cjs');

let arg='all',silent=false,force=false,jobs;
for(let i=2;i<process.argv.length;i++) {
  const a=process.argv[i];
  if(a==='--silent-preview')silent=true;
  else if(a==='--force')force=true;
  else if(a==='--jobs')jobs=Number(process.argv[++i]);
  else if(a.startsWith('--jobs='))jobs=Number(a.slice(7));
  else if(a.startsWith('--'))throw new Error('Unknown option: '+a);
  else arg=a;
}
const selected=course.lessons.filter(l=>['all','posters'].includes(arg)||arg.split(',').includes(l.id));
if(!selected.length)throw new Error('No matching lessons');
// One lesson keeps a drawing thread and two encoder threads busy.
if(jobs===undefined)jobs=Math.max(1,Math.floor(os.availableParallelism()/2));
if(!Number.isInteger(jobs)||jobs<1)throw new Error('--jobs needs a positive whole number');

const encode=l=>['-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-threads','2','-movflags','+faststart','-t',String(l.duration)];
const identityOf=l=>lessonIdentity(root,course,l,{use:'picture',renderer:fileSha(__filename),canvas:canvasVersion(),encode:encode(l)});
function current(output,record,identity) {
  try{const saved=JSON.parse(fs.readFileSync(record));return saved.identity===identity&&saved.sha256===sha(fs.readFileSync(output));}
  catch{return false;}
}

async function picture(l) {
  const {width:W,height:H,fps}=course;
  const folder=path.join(root,'review/silent');fs.mkdirSync(folder,{recursive:true});
  const output=path.join(folder,l.id+'.mp4'),record=path.join(folder,l.id+'.picture.json'),identity=identityOf(l);
  if(!force&&current(output,record,identity)){console.log(`${l.id}: picture is current, not redrawn`);return output;}
  // No record while drawing: an interrupted render can never pass for a current picture.
  fs.rmSync(record,{force:true});
  const draw=drawFor(root,l),view=lessonView(course,l),c=createCanvas(W,H),g=c.getContext('2d');
  checkCanvas(g);
  const args=['-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgba','-video_size',`${W}x${H}`,'-framerate',String(fps),'-i','pipe:0','-an',...encode(l),output];
  const ff=spawn('ffmpeg',args,{stdio:['pipe','ignore','pipe']});let stderr='',failure;
  ff.stderr.on('data',d=>stderr+=d);ff.stdin.on('error',e=>failure=e);
  const done=new Promise((resolve,reject)=>{ff.on('error',reject);ff.on('close',code=>code===0?resolve():reject(new Error(stderr||'FFmpeg failed')));});
  // Attach rejection handling before the drawing loop so an early encoder exit is handled.
  done.catch(e=>{failure=e;});
  const frames=Math.ceil(l.duration*fps);
  try {
    for(let i=0;i<frames;i++) {
      if(failure)throw failure;
      draw(g,l,i/fps,view);
      if(!ff.stdin.write(g.getImageData(0,0,W,H).data))await Promise.race([once(ff.stdin,'drain'),done.then(()=>{throw new Error('Encoder stopped before all frames');})]);
    }
    ff.stdin.end();await done;
  // Close the pipe before killing: ffmpeg otherwise keeps waiting for input and a world that throws hangs the render.
  } catch(e) {ff.stdin.destroy();ff.kill();throw e;}
  fs.writeFileSync(record,JSON.stringify({lesson:l.id,identity,frames,fps,width:W,height:H,duration:l.duration,sha256:sha(fs.readFileSync(output))},null,2)+'\n');
  console.log(`${l.id}: ${frames} frames -> ${output}`);
  return output;
}

function run(command,args) {
  return new Promise((resolve,reject)=>{
    const child=spawn(command,args,{stdio:['ignore','ignore','pipe']});let stderr='';
    child.stderr.on('data',d=>stderr+=d);child.on('error',reject);
    child.on('close',code=>code===0?resolve():reject(new Error(stderr||command+' failed')));
  });
}

async function narrated(l) {
  const audio=path.join(root,'audio',l.id+'.wav'),srt=path.join(root,'player/captions',l.id+'.srt');
  if(!fs.existsSync(audio)||!fs.existsSync(srt))throw new Error('Measured audio and captions required; use --silent-preview for layout only.');
  const video=await picture(l),folder=path.join(root,'player/videos');fs.mkdirSync(folder,{recursive:true});
  const output=path.join(folder,l.id+'.mp4');
  // The picture is copied, never encoded again: only audio and captions are added.
  await run('ffmpeg',['-hide_banner','-loglevel','error','-y','-i',video,'-i',audio,'-i',srt,'-map','0:v:0','-map','1:a:0','-map','2:0',
    '-c:v','copy','-c:a','aac','-b:a','112k','-c:s','mov_text','-metadata:s:s:0','language='+course.language,'-disposition:s:0','0',
    '-movflags','+faststart','-t',String(l.duration),output]);
  console.log(`${l.id}: picture, narration and captions -> ${output}`);
}

// Several lessons render as separate processes; each keeps its own canvas and encoder.
function child(l) {
  return new Promise((resolve,reject)=>{
    const args=[__filename,l.id,'--jobs','1',...(silent?['--silent-preview']:[]),...(force?['--force']:[])];
    spawn(process.execPath,args,{stdio:'inherit'}).on('error',reject).on('close',code=>code===0?resolve():reject(new Error('Render failed: '+l.id)));
  });
}
async function pool(items,size,work) {
  const queue=[...items];let failure;
  await Promise.all(Array.from({length:Math.min(size,queue.length)},async()=>{
    while(queue.length&&!failure){try{await work(queue.shift());}catch(e){failure=e;}}
  }));
  if(failure)throw failure;
}

(async()=>{
  if(arg==='posters') {
    fs.mkdirSync(path.join(root,'player/posters'),{recursive:true});
    for(const l of selected){const c=createCanvas(course.width,course.height),g=c.getContext('2d');checkCanvas(g);drawFor(root,l)(g,l,l.duration*.55,lessonView(course,l));fs.writeFileSync(path.join(root,'player/posters',l.id+'.png'),c.toBuffer('image/png'));}
    return;
  }
  const work=silent?picture:narrated;
  if(jobs>1&&selected.length>1)await pool(selected,jobs,child);
  else for(const l of selected)await work(l);
})().catch(e=>{console.error(e.message);process.exitCode=1;});
