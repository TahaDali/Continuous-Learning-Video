'use strict';
const fs=require('fs'),path=require('path'),{spawn}=require('child_process'),{once}=require('events');
const canvasModule=require(process.env.CANVAS_MODULE||'@napi-rs/canvas'),{createCanvas}=canvasModule;
const root=path.resolve(__dirname,'..');
const course=JSON.parse(fs.readFileSync(path.join(root,'course.json')));
const sources=require('./render-sources.cjs').sourcePaths(root,course);
if(sources.includes('production-source/design.cjs'))require('./design.cjs').installDesignRuntime(canvasModule);
const {draw}=require('./world.cjs');
const {install:checkCanvas}=require('./finite-canvas.cjs');
const arg=process.argv[2]||'all',silent=process.argv.includes('--silent-preview');
const selected=course.lessons.filter(l=>['all','posters'].includes(arg)||arg.split(',').includes(l.id));
if(!selected.length)throw new Error('No matching lessons');
async function render(l) {
  const {width:W,height:H,fps}=course,c=createCanvas(W,H),g=c.getContext('2d');
  checkCanvas(g);
  const folder=path.join(root,silent?'review/silent':'player/videos');fs.mkdirSync(folder,{recursive:true});
  const output=path.join(folder,l.id+'.mp4');
  const args=['-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgba','-video_size',`${W}x${H}`,'-framerate',String(fps),'-i','pipe:0'];
  const srt=path.join(root,'player/captions',l.id+'.srt');
  if(!silent) {
    const audio=path.join(root,'audio',l.id+'.wav');
    if(!fs.existsSync(audio)||!fs.existsSync(srt))throw new Error('Measured audio and captions required; use --silent-preview for layout only.');
    args.push('-i',audio,'-i',srt,'-map','0:v:0','-map','1:a:0','-map','2:0','-c:a','aac','-b:a','112k','-c:s','mov_text','-metadata:s:s:0','language='+course.language,'-disposition:s:0','0');
  } else args.push('-an');
  args.push('-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-threads','2','-movflags','+faststart','-t',String(l.duration),output);
  const ff=spawn('ffmpeg',args,{stdio:['pipe','ignore','pipe']});let stderr='',failure;
  ff.stderr.on('data',d=>stderr+=d);ff.stdin.on('error',e=>failure=e);
  const done=new Promise((resolve,reject)=>{ff.on('error',reject);ff.on('close',code=>code===0?resolve():reject(new Error(stderr||'FFmpeg failed')));});
  // Attach rejection handling before the drawing loop so an early encoder exit is handled.
  done.catch(e=>{failure=e;});
  const frames=Math.ceil(l.duration*fps);
  try {
    for(let i=0;i<frames;i++) {
      if(failure)throw failure;
      draw(g,l,i/fps,course);
      if(!ff.stdin.write(g.getImageData(0,0,W,H).data))await Promise.race([once(ff.stdin,'drain'),done.then(()=>{throw new Error('Encoder stopped before all frames');})]);
    }
    ff.stdin.end();await done;
  } catch(e) {ff.kill();throw e;}
  console.log(`${l.id}: ${frames} frames -> ${output}`);
}
(async()=>{
  if(arg==='posters') {
    fs.mkdirSync(path.join(root,'player/posters'),{recursive:true});
    for(const l of selected){const c=createCanvas(course.width,course.height),g=c.getContext('2d');checkCanvas(g);draw(g,l,l.duration*.55,course);fs.writeFileSync(path.join(root,'player/posters',l.id+'.png'),c.toBuffer('image/png'));}
    return;
  }
  for(const l of selected)await render(l);
})().catch(e=>{console.error(e.message);process.exitCode=1;});
