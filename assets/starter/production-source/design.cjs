'use strict';
// Design system for explanatory motion. It sits beside motion.cjs and keeps the same audit
// contract: every text and solid object registers screen bounds, owners describe containment,
// connectors and annotations stay unregistered like edge(), and transitions are reported.
// The stage also enforces, through the audit's mechanism-check channel (S.check):
//   type-<id>   a fully visible label below its tier floor on screen (28 px; 24 tertiary; 18 chrome)
//   edge-<id>   a visible label the edge guard had to fade (it came within EDGE px of the safe area),
//               including unclipped non-chrome text in the top or caption band, which it hides
//   words       more than WORD_BUDGET content words visible in one frame
// Colour is a small set of meanings: signal = ONLY what is being spoken about now (the
// highlighter); wrong = ONLY wrong, blocked or rejected; good = ONLY correct or conserved;
// fiction = ONLY the fiction badge; accent = change and attention annotations. A course's own
// state code (defineStates) never reuses a meaning colour.
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
  if(!canvasModule?.GlobalFonts||!canvasModule.createCanvas||!canvasModule.Image)throw new Error('installDesignRuntime needs the loaded canvas module');
  if(runtime?.module===canvasModule)return runtime;
  for(const face of Object.values(FACES)) {
    if(!canvasModule.GlobalFonts.registerFromPath(path.join(__dirname,'fonts',face+'.ttf'),face))throw new Error('Could not register bundled font: '+face);
  }
  runtime={module:canvasModule,createCanvas:canvasModule.createCanvas,grain:null};
  return runtime;
}

// ---------------------------------------------------------------- tokens
// One paper, one ink, one accent per scene. Teal and gold continue the original palette.
// Meaning tokens (signal, wrong, good, fiction) each carry one meaning; see the header.
const T={paper:'#F2EDE2',paperHi:'#FBF8F1',paperLo:'#E7DFCF',ink:'#15262C',inkSoft:'#4A5C61',mute:'#8F9A97',rule:'#D3C9B6',
  teal:'#0E7469',tealSoft:'#D2E7E0',accent:'#DE5530',accentSoft:'#F7D8CA',gold:'#F2BF45',goldSoft:'#FAE6B3',goldInk:'#9A6A12',
  blue:'#2F63B5',blueSoft:'#DCE6F6',night:'#13242A',nightHi:'#1D323A',nightRule:'#2E464E',white:'#FFFDF8',good:'#2E8B57',
  // signal is the highlighter (the gold value): only what the narration is speaking about now.
  signal:'#F2BF45',signalSoft:'#FAE6B3',
  // wrong: only wrong, blocked or rejected (a red kept distinct from the accent). good: only correct or conserved.
  wrong:'#C62F2A',wrongSoft:'#F6E0DF',goodSoft:'#E0EEE6',
  // The fiction badge hue and its type. Used for nothing else, on paper or night.
  fiction:'#6A3BEF',fictionInk:'#FFFFFF'};
const MEANINGS=['signal','signalSoft','wrong','wrongSoft','good','goodSoft','fiction'];
const HEX=/^#[0-9a-f]{6}$/i;
// Subject colours (a brand, a map legend) are added once here, never as literals inside a world.
function extendTheme(colours) {
  for(const [k,v] of Object.entries(colours||{})) {
    if(k in T)throw new Error('Theme token already exists: '+k);
    if(!HEX.test(v))throw new Error('Theme colours must be #rrggbb: '+k);
    T[k]=v;
  }
  return T;
}
// A soft tint of a #rrggbb colour (mixed toward white), for derived state fills.
const softOf=(hex,k=.85)=>'#'+[1,3,5].map(i=>{const c=parseInt(hex.slice(i,i+2),16);return Math.round(c+(255-c)*k).toString(16).padStart(2,'0');}).join('').toUpperCase();

// ---------------------------------------------------------------- state code
// A course defines once what its quantities can BE (a parcel planned, shipped, delivered; a book
// on shelf, lent, overdue) and reuses that code whenever one moves. Each state gets T[name] and
// T[name+'Soft']; treatment 'solid' (default) or 'hatched' (hatching inside a dashed outline,
// never solid: possible, planned, not yet). Draw states with S.stateBox / S.swatch.
// Worlds read STATES; only defineStates writes it.
const STATES={},STATE_ALIASES={};
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
function defineStates(spec,{aliases={}}={}) {
  const entries=Object.entries(spec||{}),meaning=new Map(MEANINGS.map(k=>[T[k].toUpperCase(),k]));
  if(!entries.length)throw new Error('defineStates needs at least one state');
  // Validate everything first, so a rejected call leaves no partial state code behind.
  const out=entries.map(([name,s])=>{
    if(!/^[a-z][A-Za-z0-9]*$/.test(name))throw new Error('Invalid state name: '+name);
    if(own(STATES,name)||own(STATE_ALIASES,name))throw new Error('State already defined: '+name);
    for(const k of [name,name+'Soft'])if(k in T)throw new Error('Theme token already exists: '+k);
    const color=s?.color,soft=s?.soft??(HEX.test(String(color))?softOf(color):color),treatment=s?.treatment||'solid';
    for(const c of [color,soft])if(!HEX.test(String(c)))throw new Error('State colours must be #rrggbb: '+name);
    for(const c of [color,soft])if(meaning.has(c.toUpperCase()))throw new Error(`State ${name} reuses the meaning colour ${meaning.get(c.toUpperCase())}`);
    if(!['solid','hatched'].includes(treatment))throw new Error(`State treatment must be solid or hatched: ${name}`);
    return {name,color,soft,entry:Object.freeze({name,token:name,soft:name+'Soft',label:s.label||name[0].toUpperCase()+name.slice(1),treatment,meaning:s.meaning||''})};
  });
  // Two states with the same colour and treatment cannot be told apart on screen.
  const looks=new Map(Object.values(STATES).map(s=>[T[s.token].toUpperCase()+s.treatment,s.name]));
  for(const s of out){const k=s.color.toUpperCase()+s.entry.treatment;
    if(looks.has(k))throw new Error(`State ${s.name} looks the same as ${looks.get(k)} (same colour and treatment)`);looks.set(k,s.name);}
  const names=new Set(out.map(s=>s.name));
  for(const [alias,target] of Object.entries(aliases||{})) {
    if(!/^[a-z][A-Za-z0-9]*$/.test(alias)||own(STATES,alias)||own(STATE_ALIASES,alias)||names.has(alias))throw new Error('Invalid or duplicate state alias: '+alias);
    if(!names.has(target)&&!own(STATES,target))throw new Error(`State alias ${alias} points to an unknown state: ${target}`);
  }
  for(const s of out){T[s.name]=s.color;T[s.name+'Soft']=s.soft;STATES[s.name]=s.entry;}
  for(const [alias,target] of Object.entries(aliases||{}))STATE_ALIASES[alias]=target;
  return STATES;
}
// Resolves an alias to its state name; unknown states throw instead of drawing a wrong colour.
const stateOf=name=>{const k=own(STATE_ALIASES,name)?STATE_ALIASES[name]:name;if(!own(STATES,k))throw new Error('Unknown state: '+name);return k;};

// ---------------------------------------------------------------- type
// Roles, not sizes: authors pick a role and may override size; the system owns face and tracking.
// Floors by tier: text that carries meaning >= 28 px; tertiary text (row units, axis ticks,
// glyph-internal IDs) >= 24 px; chrome (rail, badge) >= 18 px. role() never returns less.
const FLOOR={content:28,tertiary:24,chrome:18};
const TYPE={
  chrome:{face:'bold',size:18,track:1.4,upper:true,chrome:true,tier:'chrome'},
  kicker:{face:'bold',size:24,track:2.6,upper:true,tier:'tertiary'},
  display:{face:'heavy',size:88,track:-3},
  headline:{face:'bold',size:44,track:-1.3},
  title:{face:'demi',size:32,track:-.6},
  body:{face:'demi',size:30,track:-.4},
  label:{face:'demi',size:28,track:-.1},
  // The bold key of a callout ("Shelf: 12").
  key:{face:'bold',size:28,track:-.2},
  small:{face:'medium',size:24,track:0,tier:'tertiary'},
  accent:{face:'serifItalic',size:70,track:-.4},
  accentMd:{face:'serifItalic',size:38,track:0},
  accentSm:{face:'serifItalic',size:28,track:0},
  numeral:{face:'heavy',size:58,track:-1.5},
  numeralSm:{face:'bold',size:30,track:-.6},
  mono:{face:'mono',size:28,track:0},
  monoSm:{face:'mono',size:24,track:0,tier:'tertiary'}};
const floorOf=r=>r.chrome||r.tier==='chrome'?FLOOR.chrome:r.tier==='tertiary'?FLOOR.tertiary:FLOOR.content;
const role=(name,over)=>{const r={...(TYPE[name]||TYPE.body),...over};if(r.tier==='chrome')r.chrome=true;const f=floorOf(r);if(!(r.size>=f))r.size=f;return r;};
// Inter's em box: with textBaseline 'middle', the alphabetic baseline sits .363 em below y.
const BASELINE=.363;
// Edge guard band (px) inside the safe area, and the per-frame content word budget.
const EDGE=12,WORD_BUDGET=24;

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
// A word that is not in the narration throws, so a reveal can never silently drift. A word
// spoken more than once throws unless nth is given: the first occurrence is often seconds
// before the sentence the reveal belongs to. cue.count(scene, word) says how often it is
// spoken; cue.end(scene, word, nth) is when it ends (measured end, or the next word's onset).
// Words match in any script: letters (with their combining marks) and digits survive, in NFC so a
// composed and a decomposed "é" agree; apostrophes and punctuation drop ("Don't" = "dont",
// "$15,000" = "$15000"). A cue word with no letter or digit matches nothing and throws.
const normWord=s=>String(s).normalize('NFC').toLowerCase().replace(/[’'ʼ]/g,'').replace(/[^\p{L}\p{M}\p{N}$%]/gu,'');
const cueTables=new WeakMap();
function createCues(lesson) {
  if(!cueTables.has(lesson))cueTables.set(lesson,lesson.scenes.map(scene=>{
    const measured=Array.isArray(scene.wordTimings)&&scene.wordTimings.length>0;
    if(measured) {
      // A provider event can cover several spoken words ("in 2015", "15,000 dollars"). Split it and
      // place each later sub-word by its character position inside the measured event.
      const words=[];
      for(const m of scene.wordTimings){const text=String(m.text),parts=text.split(/\s+/).filter(Boolean),len=Math.max(1,text.length);
        const span=Number.isFinite(m.end)&&m.end>m.start?m.end-m.start:0;let off=0;
        for(const part of parts){const at=text.indexOf(part,off),b=at+part.length;
          words.push({w:normWord(part),start:m.start+span*at/len,end:span?m.start+span*b/len:NaN});off=b;}}
      // A word without a measured end ends where the next one starts.
      words.forEach((x,i)=>{if(!Number.isFinite(x.end))x.end=words[i+1]?.start??x.start+.3;});
      return {id:scene.id,method:'measured',words};
    }
    const words=String(scene.narration||'').split(/\s+/).filter(Boolean),{times,method}=wordTimes(words,scene);
    const last=Number.isFinite(scene.speechEnd)?scene.speechEnd:null;
    return {id:scene.id,method,words:words.map((w,i)=>({w:normWord(w),start:times[i],end:times[i+1]??(last>times[i]?last:times[i]+.3)}))};
  }));
  const table=cueTables.get(lesson);
  const find=scene=>{const s=typeof scene==='number'?table[scene-1]:table.find(x=>x.id===scene);if(!s)throw new Error('Unknown cue scene: '+scene);return s;};
  const count=(scene,word)=>{const n=normWord(word);return n?find(scene).words.filter(x=>x.w===n).length:0;};
  const hit=(scene,word,nth)=>{
    if(nth===undefined){const n=count(scene,word);if(n>1)throw new Error(`Ambiguous narration cue: scene ${scene} "${word}" is spoken ${n} times; pass nth (1..${n})`);nth=1;}
    const n=normWord(word);let k=0;if(n)for(const x of find(scene).words)if(x.w===n&&++k===nth)return x;
    throw new Error(`Missing narration cue: scene ${scene} "${word}" #${nth}`);};
  const cue=(scene,word,nth)=>hit(scene,word,nth).start;
  cue.end=(scene,word,nth)=>hit(scene,word,nth).end;
  cue.count=count;
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

// ---------------------------------------------------------------- spoken numbers
// A spoken count: steps through round multiples of `step` from `from` and lands EXACTLY on `value`
// at `end` (the onset of the last spoken word of the number). Before `start` it returns `from`.
// It never shows a value that is not a multiple of `step` away from `from`, so a viewer never
// sees "69,621" while the narrator says "seventy-two thousand".
function stepValue(t,{value,start,end,step,from=0,ease=E.inOut}) {
  if(!(t>start))return from;if(t>=end)return value;
  const p=ease(clamp((t-start)/Math.max(1e-3,end-start))),n=Math.floor(Math.abs(value-from)/step);
  return from+Math.sign(value-from)*Math.min(n,Math.floor(n*p+1e-9))*step;
}
// A round step that divides the distance (largest of 1, 2, 2.5, 5 × 10^k giving 8–30 steps).
function niceStep(d) {
  d=Math.abs(d);if(!d)return 1;
  for(let k=Math.floor(Math.log10(d));k>=0;k--)for(const m of [5,2.5,2,1]){const s=m*10**k;if(Number.isInteger(s)&&d%s===0&&d/s>=8&&d/s<=30)return s;}
  return Math.max(1,10**Math.max(0,Math.floor(Math.log10(d))-1));
}
// The value to SHOW for a figure the narrator says. `times` are the onsets of the spoken words of
// the number (cue.phrase(scene,'twelve thousand')). No mode ever shows a value that is not said:
//   'word'  (default): null before the first spoken word, then exactly `value` — on its word.
//   'count': round multiples of `step` between the first and the last spoken word, landing exactly
//            on `value` at the last word's onset (a stock filling up).
//   'land':  null until the last spoken word, then exactly `value`.
// `lead` (s) lets 'word' and 'count' start slightly early. Callers draw nothing while it is null.
function spoken(t,value,times,{step,from=0,mode='word',lead=0}={}) {
  const a=times[0]-lead,b=times.at(-1);
  if(mode==='word')return t>=a?value:null;
  if(mode==='land')return t>=b?value:null;
  if(t<a)return null;
  return stepValue(t,{value,start:a,end:b,step:step||niceStep(value-from),from});
}

// ---------------------------------------------------------------- speaking and focus
// Speaking intensity for a person: rises at `from`, falls after `to` (cue times of the words they
// say, or of the narration describing them).
const talking=(t,from,to,{fade=.25}={})=>seg(t,from-.05,fade)*(1-seg(t,to,fade));
// Focus for a sequence of speakers: speakers[i] = {from, to}. 0 before speaker i first speaks,
// then 1 while they are the active one and `dim` once the next speaker starts; `all` (a time)
// brings everyone back to full.
function focusOf(t,speakers,i,{dim=.3,all=Infinity,d=.4}={}) {
  const me=speakers[i],next=speakers[i+1];
  const on=seg(t,me.from-.1,d),off=next?seg(t,next.from-.1,d):0,back=seg(t,all,d);
  if(t<me.from-.1)return 0;
  return Math.max(back,lerp(1,dim,off)*on);
}

// ---------------------------------------------------------------- camera
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
// Keep camera keyframes ordered when narration compresses a scene (mutates and returns keys).
function orderKeys(keys){for(let i=1;i<keys.length;i++)keys[i].t=Math.max(keys[i].t,keys[i-1].t+.05);return keys;}
// A camera key {x,y,zoom} that frames a world box inside the content band (below the section head,
// above the captions) of the 1280×720 stage, as large as possible within maxZoom. Use it for a
// reframing push; a slow drift across a scene stays a hand-written zoom of at most 1.06.
function fitCamera(box,{top=196,bottom=574,left=54,right=1226,maxZoom=1.6,minZoom=1}={}) {
  const z=Math.max(minZoom,Math.min(maxZoom,(right-left)/box.w,(bottom-top)/box.h));
  // screen = 640 + (wx - cx) * z ; 340 + (wy - cy) * z: centre the box in the band.
  return {x:box.x+box.w/2-((left+right)/2-640)/z,y:box.y+box.h/2-((top+bottom)/2-340)/z,zoom:z};
}
// Fade for a label or group a camera move would carry to the frame edge: 1 outside the move
// window [a, b], 0 inside it, with `d`-second ramps that END before the move starts and START
// after it ends. Pair with S.onScreen(box) for anything computed from geometry.
const beforePush=(t,[a,b],{d=.3}={})=>1-seg(t,a-d,d)*(1-seg(t,b,d));
// Draw world-space content through the camera with motion blur; frames inside `pans` windows are
// reported as transition frames (their drawing is unregistered). Returns the camera.
function world(S,t,keys,draw,{pans=[]}={}) {
  const cam=cameraAt(t,keys),blur=Math.min(3,cam.speed/700),pan=pans.some(w=>t>=w[0]&&t<w[1]);
  S.view(cam,()=>pan?S.transition(draw):draw(),{blur});
  return cam;
}
// Plans are computed once per lesson object (narration re-timing produces a new object).
// build({lesson, cue, sc, win}) gets the cues, scenes by id and win(scene) = a transition window
// that begins in the closing pause before the scene.
function planner(build) {
  const cache=new WeakMap();
  return lesson=>{if(!cache.has(lesson)){const cue=createCues(lesson),sc=Object.fromEntries(lesson.scenes.map(s=>[s.id,s]));
    cache.set(lesson,build({lesson,cue,sc,win:s=>[s.start-.3,s.start+.7]}));}return cache.get(lesson);};
}

// ---------------------------------------------------------------- textures
// Grain is drawn from a decoded Image, never from a canvas: in @napi-rs/canvas 0.1.x every
// drawImage(canvas), and every pattern built from one, snapshots a full frame that is never freed
// (≈3.6 MB per frame at 1280×720; a 55,912-frame audit was killed). The same rule holds for any
// cached canvas drawn per frame: encode it once and draw the decoded Image. Decoding is
// asynchronous, so until it lands (the first frames of a render, a fully synchronous audit or
// poster loop) up to GRAIN_FALLBACK paints draw the pixel-identical canvas, a bounded cost;
// past that budget a paint skips the grain until the Image is ready. No synchronous, leak-free
// substitute exists in 0.1.x (patterns from a canvas or ImageData leak the same way), so a loop
// that never yields loses the grain after the budget: `render.cjs posters` grains roughly its
// first 60 posters (one paint per lesson, more for iris and wipe frames), and later ones are flat.
const GRAIN_FALLBACK=64;
function grainLayer(W,H) {
  const cached=runtime.grain;
  if(cached&&cached.W===W&&cached.H===H)return cached.ready?cached.image:cached.layer&&cached.fallback-->0?cached.layer:null;
  const layer=runtime.createCanvas(W,H),c=layer.getContext('2d'),img=c.createImageData(W,H);
  let s=1234567;const rnd=()=>{s=(s*1664525+1013904223)>>>0;return s/4294967296;};
  for(let i=0;i<img.data.length;i+=4){const v=rnd()*255;img.data[i]=img.data[i+1]=img.data[i+2]=v;img.data[i+3]=rnd()<.5?10:0;}
  c.putImageData(img,0,0);
  const entry={W,H,layer,fallback:GRAIN_FALLBACK,ready:false,image:new runtime.module.Image()};
  entry.image.onload=()=>{entry.ready=true;entry.layer=null;};
  entry.image.onerror=()=>{entry.failed=true;};
  entry.image.src=layer.toBuffer('image/png');
  runtime.grain=entry;entry.fallback--;return layer;
}
function paintBackground(g,W,H,mode='paper') {
  const night=mode==='night';
  g.save();g.setTransform(1,0,0,1,0,0);g.globalAlpha=1;g.filter='none';
  g.fillStyle=night?T.night:T.paper;g.fillRect(0,0,W,H);
  const v=g.createRadialGradient(W/2,H*.48,H*.35,W/2,H*.5,W*.72);
  v.addColorStop(0,night?'rgba(40,70,78,.22)':'rgba(255,253,246,.28)');v.addColorStop(1,night?'rgba(0,0,0,.32)':'rgba(120,96,50,.12)');
  g.fillStyle=v;g.fillRect(0,0,W,H);const grain=grainLayer(W,H);if(grain)g.drawImage(grain,0,0);g.restore();
}

// ---------------------------------------------------------------- stage
// Content words in any script: a whitespace token with a letter, digit, $ or %. Scripts written
// without spaces (Chinese, Japanese, Thai...) count their dictionary word segments instead.
const UNSPACED=/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Thai}\p{Script=Lao}\p{Script=Khmer}\p{Script=Myanmar}]/u;
const SEGMENTER=typeof Intl.Segmenter==='function'?new Intl.Segmenter('und',{granularity:'word'}):null;
const countWords=s=>String(s).split(/\s+/).reduce((n,x)=>n+(!/[\p{L}\p{N}$%]/u.test(x)?0:
  SEGMENTER&&UNSPACED.test(x)?Math.max(1,[...SEGMENTER.segment(x)].filter(q=>q.isWordLike).length):1),0);

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
  // open: inside unclipped(); bare: drawing is not clipped to the viewport; depth: callbacks of
  // view/fade/actor, whose saved state unclipped() must not pop.
  const items=[],checks=[],guards=new Set();let quiet=0,moving=0,transition=false,words=0,open=0,bare=false,depth=0;
  const night=background==='night';
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
  // audit reports how many such frames each lesson has. Text drawn inside decor() is not
  // registered but still meets its tier's floor; only transition frames skip the text checks.
  function decor(fn){quiet++;try{fn();}finally{quiet--;}}
  function inTransition(fn){transition=true;moving++;try{decor(fn);}finally{moving--;}}
  // Model or timing assertions reported through the audit's mechanism-invariant channel.
  function check(id,passed,actual,expected){if(!checks.some(c=>c.id===id))checks.push({id,passed:passed===true,actual,expected});}
  // A template given its scene end asserts that the spoken span leaves room for its choreography.
  function fits(name,start,end,minimum){if(Number.isFinite(end))check('fit-'+name,end-start>=minimum,+(end-start).toFixed(3),'>= '+minimum+'s');}
  function view(cam,fn,{blur=0}={}) {
    g.save();g.setTransform(1,0,0,1,0,0);g.translate(W/2,CY);g.scale(cam.zoom,cam.zoom);g.translate(-cam.x,-cam.y);
    if(blur>.3)g.filter=`blur(${blur.toFixed(2)}px)`;depth++;try{fn();}finally{depth--;g.restore();}
  }
  function fade(a,fn){if(a<=.002)return;g.save();g.globalAlpha*=Math.min(1,a);depth++;try{fn();}finally{depth--;g.restore();}}
  function actor(id,b,draw,owner=null){record(id,b,'actor',owner);g.save();depth++;try{draw(g);}finally{depth--;g.restore();}}

  // Edge guard. A label whose screen box comes within EDGE px of the safe-area edge fades, reaching
  // zero at the edge, so text is never sliced by the frame or the content clip — during pans and
  // pushes too. Outside transitions, a visible label the guard has to touch fails `edge-<id>`:
  // fade it yourself (S.onScreen, beforePush) before the camera move carries it to the edge.
  // Chrome-tier text (rail, badge) lives outside the content area and is exempt. Clipped text
  // outside the viewport is invisible anyway; unclipped text anywhere on the canvas is not, so a
  // non-chrome label in the top or caption band (hidden by the guard) fails too.
  const intersectsView=b=>Math.min(b.x+b.w,viewport.x+viewport.w)>Math.max(b.x,viewport.x)&&Math.min(b.y+b.h,viewport.y+viewport.h)>Math.max(b.y,viewport.y);
  const onCanvas=b=>b.x+b.w>0&&b.y+b.h>0&&b.x<W&&b.y<H;
  function edgeFactor(sb,margin=EDGE){const d=Math.min(sb.x-safe.x,safe.x+safe.w-(sb.x+sb.w),sb.y-safe.y,safe.y+safe.h-(sb.y+sb.h));return d>=margin?1:d<=0?0:d/margin;}
  // Visibility (0..1) of a world-space box under the current camera: fade a group with it before a move.
  function onScreen(b,{margin=EDGE+8}={}){return edgeFactor(screenBounds(g,b),margin);}
  // Type floor: a fully visible label whose on-screen size (role size × transform scale) is below
  // its tier's floor fails the audit — a zoomed-out camera or a scaled group can shrink text.
  function typeFloor(id,r) {
    if(g.globalAlpha<.9)return;
    const m=g.getTransform(),px=r.size*Math.sqrt(Math.abs(m.a*m.d-m.b*m.c)),f=floorOf(r);
    if(px<f-.25){guards.add('type-'+id);check('type-'+id,false,+px.toFixed(1),'>= '+f+'px on screen');}
  }
  // Every label passes through the guard, the type floor and the word budget (n content words).
  function guarded(id,r,box,owner,n,draw) {
    const sb=screenBounds(g,box),inView=intersectsView(sb),vis=inView||bare&&onCanvas(sb),k=r.chrome?1:edgeFactor(sb),live=!moving;
    if(live&&!r.chrome&&vis&&k<.98&&g.globalAlpha>.1){guards.add('edge-'+id);
      check('edge-'+id,false,+k.toFixed(2),inView?'label clear of the frame edge':'chrome role for text outside the content area');}
    g.save();g.globalAlpha*=k;record(id,box,'label',owner);
    if(k>.002) {
      if(live)typeFloor(id,r);
      if(live&&!r.chrome&&vis&&g.globalAlpha>.5)words+=n;
      draw();
    }
    g.restore();
  }
  const edgeOf=(r,box)=>r.chrome?1:edgeFactor(screenBounds(g,box));

  function setFont(r){g.font=`${r.size}px "${FACES[r.face]}"`;g.letterSpacing=(r.track||0)+'px';}
  function measure(str,r){g.save();setFont(r);const w=g.measureText(String(str)).width-(r.track||0);g.restore();return w;}
  function paint(s,left,y,r,color,blur=0){g.save();setFont(r);g.textAlign='left';g.textBaseline='middle';if(blur>.3)g.filter=`blur(${blur.toFixed(2)}px)`;
    g.fillStyle=color;g.fillText(s,left,y);g.restore();}
  function text(id,str,x,y,{role:name='body',over,color=T.ink,align='left',blur=0,owner=null}={}) {
    const r=role(name,over),s=r.upper?String(str).toUpperCase():String(str),w=measure(s,r);
    const left=align==='center'?x-w/2:align==='right'?x-w:x;
    guarded(id,r,{x:left-2,y:y-r.size*.62,w:w+4,h:r.size*1.24},owner,countWords(s),()=>paint(s,left,y,r,color,blur));
    return w;
  }

  // motion.cjs-compatible label, so createIllustration(stage) from illustrations.cjs draws here in the system type.
  // tier 'tertiary' (floor 24) or 'chrome' (floor 18) marks text that may sit below the content floor.
  function label(id,str,x,y,{size=28,color=T.ink,owner=null,align='center',weight=600,tier}={}) {
    return text(id,str,x,y,{role:'label',over:{face:weight>=700?'bold':weight>=600?'demi':'medium',size,track:0,...(tier?{tier}:{})},color,align,owner});
  }

  // ------------------------------------------------ kinetic sentence
  function layout(str,{role:name='body',over,maxWidth=900,lineHeight}={}) {
    const r=role(name,over),words=String(str).split(/\s+/).filter(Boolean),space=measure(' ',r)*1.05;
    const lh=lineHeight||r.size*1.32,lines=[[]];let width=0;
    for(const w of words) {
      const ww=measure(r.upper?w.toUpperCase():w,r),line=lines.at(-1),lw=line.reduce((s,q)=>s+q.w,0)+space*line.length;
      if(line.length&&lw+ww>maxWidth)lines.push([]);
      lines.at(-1).push({text:w,w:ww});
    }
    const out=[];lines.forEach((line,li)=>{const lw=line.reduce((s,q)=>s+q.w,0)+space*(line.length-1);width=Math.max(width,lw);
      let x=0;for(const q of line){out.push({...q,line:li,x,lineWidth:lw});x+=q.w+space;}});
    return {r,words:out,lines:lines.length,lh,width,space,height:(lines.length-1)*lh+r.size*1.24};
  }
  // reveal: rise | slide | blur | ghost | none. times[i] is word i's onset (use cues). 'slide' moves
  // words in sideways only, for furniture that sits close above other content.
  // styles[i] = {color, mark:{p,color}, hidden} — hidden leaves the word's slot empty (it is being carried elsewhere).
  // Marks on consecutive words of one line join into one highlighter band (a sentence highlighter
  // run) that sweeps word by word and owns its words; marked words hold still.
  function sentence(id,str,x,y,{t,times,reveal='rise',dur=.5,align='left',color=T.ink,ghost=.17,styles={},owner=null,...opts}) {
    const L=layout(str,opts),top=y-(L.lines-1)*L.lh/2;
    const place=q=>({x:x+(align==='center'?-q.lineWidth/2:align==='right'?-q.lineWidth:0)+q.x,y:top+q.line*L.lh});
    const state=L.words.map((q,i)=>{
      const p=reveal==='none'?1:clamp((t-(times?.[i]??0))/dur);
      if(reveal==='ghost')return {a:1,fill:E.out(p),dx:0,dy:0,blur:0};
      if(reveal==='blur')return {a:E.out(p),fill:1,dx:0,dy:0,blur:(1-E.out(p))*9};
      if(reveal==='slide')return {a:E.out(clamp(p*1.4)),fill:1,dx:(1-E.outExpo(p))*L.r.size*.3,dy:0,blur:0};
      return {a:E.out(clamp(p*1.6)),fill:1,dx:0,dy:(1-E.outExpo(p))*L.r.size*.55,blur:(1-E.out(p))*5};
    });
    const runs=[],ownerOf={};
    L.words.forEach((q,i)=>{const m=styles[i]?.mark;if(!m||m.p<=0)return;const last=runs.at(-1);
      if(last&&last.end===i-1&&L.words[i-1].line===q.line&&last.color===m.color){last.end=i;last.p=m.p;}else runs.push({start:i,end:i,p:m.p,color:m.color});});
    // Bands of stacked lines stay apart; a single line keeps the classic 1.36 em band.
    const pad=Math.max(2,Math.min(8,L.space-3)),h=L.lines>1?Math.max(L.r.size*1.26,Math.min(L.r.size*1.36,L.lh-2)):L.r.size*1.36;
    runs.forEach(r=>{const a=place(L.words[r.start]),eq=L.words[r.end],e=place(eq),x0=a.x-pad,full=e.x+eq.w+pad;
      const from=r.end>r.start?place(L.words[r.end-1]).x+L.words[r.end-1].w+pad:x0,right=lerp(from,full,E.inOut(clamp(r.p))),rid=`${id}-mark${r.start}`;
      actor(rid,{x:x0,y:a.y-h/2,w:full-x0,h},()=>band(x0,a.y-h/2,right,h,r.color||T.signal),owner);
      for(let i=r.start;i<=r.end;i++)ownerOf[i]=rid;});
    L.words.forEach((q,i)=>{const s=state[i],st=styles[i]||{},at=place(q);if(s.a<=.01||st.hidden)return;
      const own=ownerOf[i]||owner,c=st.color||color,still=!!ownerOf[i];
      if(reveal==='ghost')fade(ghost+(1-ghost)*s.fill,()=>text(`${id}-w${i}`,q.text,at.x,at.y,{role:opts.role,over:opts.over,color:c,owner:own}));
      else fade(s.a,()=>text(`${id}-w${i}`,q.text,at.x+(still?0:s.dx),at.y+(still?0:s.dy),{role:opts.role,over:opts.over,color:c,blur:still?0:s.blur,owner:own}));
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
  // The fade reaches full only once the pop has grown past full size, so popping type never reads below its floor.
  function chip(id,label,x,y,{p=1,role:name='label',fill=T.ink,color=T.white,padX:px=14,padY=8,radius=null,align='center',owner=null,dot=null}={}) {
    const padX=Math.max(px,4),r=role(name),w=measure(r.upper?label.toUpperCase():label,r)+(dot?18:0),bw=w+padX*2,bh=r.size+padY*2;
    const left=align==='center'?x-bw/2:align==='right'?x-bw:x,s=E.outBack(clamp(p)),box={x:left,y:y-bh/2,w:bw,h:bh};
    if(p<=0)return box;
    g.save();g.globalAlpha*=clamp(p*2.3);g.translate(left+bw/2,y);g.scale(s,s);g.translate(-(left+bw/2),-y);
    actor(id,{x:left,y:y-bh/2,w:bw,h:bh},()=>{roundRect(left,y-bh/2,bw,bh,radius??bh/2);g.fillStyle=fill;g.fill();
      if(dot){g.fillStyle=dot;g.beginPath();g.arc(left+padX+5,y,5,0,Math.PI*2);g.fill();}},owner);
    text(id+'-t',label,left+padX+(dot?18:0),y+1,{role:name,color,owner:id});
    g.restore();return box;
  }
  // The highlighter shape: a band from x to `right`, slightly skewed like a hand-drawn stroke.
  function band(x,y,right,h,color){g.globalAlpha*=.9;g.fillStyle=color;g.beginPath();
    g.moveTo(x,y+3);g.lineTo(right,y);g.lineTo(right-3,y+h);g.lineTo(x+2,y+h-2);g.closePath();g.fill();}
  // Highlighter in the signal colour: only on what the narration is speaking about now.
  function marker(id,x,y,w,h,p,{color=T.signal,owner=null}={}) {
    if(p<=0)return;const e=E.inOut(clamp(p));
    actor(id,{x,y,w,h},()=>band(x,y,x+w*e,h,color),owner);
  }
  // Marked text: the highlighter sweeps behind the words and the type turns ink exactly under the
  // swept part (clipped to the sweep), so light text on night stays readable on the signal band.
  // Returns the band box and the text span.
  function markText(id,str,x,y,{role:name='label',over,align='left',p=0,color=T.ink,inkColor=T.ink,markColor=T.signal,owner=null,pad=12}={}) {
    const r=role(name,over),s=r.upper?String(str).toUpperCase():String(str),w=measure(s,r),left=align==='center'?x-w/2:align==='right'?x-w:x;
    const h=r.size*1.36,x0=left-pad,bw=w+2*pad,swept=x0+bw*E.inOut(clamp(p)),box={x:left-2,y:y-r.size*.62,w:w+4,h:r.size*1.24};
    if(p>0)marker(id+'-mk',x0,y-h/2,bw,h,p,{color:markColor,owner});
    g.save();g.beginPath();g.rect(swept,y-h,1e5,2*h);g.clip();text(id,s,left,y,{role:name,over,color,owner:p>0?id+'-mk':owner});g.restore();
    // The ink copy under the sweep is the same words, already registered and counted above.
    if(p>0){const k=edgeOf(r,box);if(k>.002){g.save();g.globalAlpha*=k;g.beginPath();g.rect(x0-4,y-h,swept-x0+4,2*h);g.clip();paint(s,left,y,r,inkColor);g.restore();}}
    return {x:x0,y:y-h/2,w:bw,h,text:{x:left,w}};
  }
  // Odometer counter: tabular digits roll through their neighbours. For a spoken figure use
  // spoken() (round steps that land on the word) with S.text or S.callout instead.
  function counter(id,value,x,y,{role:name='numeral',color=T.ink,align='center',prefix='',suffix='',owner=null}={}) {
    const r=role(name),lo=Math.floor(value+1e-6),frac=value-lo,a=prefix+lo+suffix,b=prefix+(lo+1)+suffix;
    const digit=measure('0',r)+(r.track||0),n=Math.max(a.length,b.length),w=n*digit-(r.track||0);
    const left=align==='center'?x-w/2:align==='right'?x-w:x;
    guarded(id,r,{x:left-2,y:y-r.size*.62,w:w+4,h:r.size*1.24},owner,1,()=>{
      g.save();g.beginPath();g.rect(left-4,y-r.size*.62,w+8,r.size*1.24);g.clip();setFont(r);g.letterSpacing='0px';g.textBaseline='middle';g.fillStyle=color;
      // Each glyph is centred in a fixed cell, so narrow figures such as 1 read as tabular.
      const A=a.padStart(n,' '),B=b.padStart(n,' '),put=(ch,cx,yy)=>g.fillText(ch,cx+(digit-(r.track||0)-g.measureText(ch).width)/2,yy);
      for(let i=0;i<n;i++){const cx=left+i*digit;
        if(A[i]===B[i]||frac<.001){put(A[i],cx,y);continue;}
        const off=E.inOut(frac)*r.size*1.1;put(A[i],cx,y-off);put(B[i],cx,y-off+r.size*1.1);}
      g.restore();});
    return w;
  }
  // Callout: a bold key then its value — "Shelf: 12". The replacement for quantity pills.
  // layout 'inline' sets both on one baseline; 'stack' puts the key above the value.
  // mark (0..1) sweeps the highlighter behind the value. keyP / valueP stage the reveal: the key
  // lands first, the value when its number is spoken. state: a state swatch before the key.
  // Returns the whole box and the value box.
  function callout(id,key,value,x,y,{layout:mode='inline',keyRole='key',valueRole='numeralSm',keyOver,valueOver,keyColor=T.ink,valueColor=T.ink,
    align='left',mark=0,markColor=T.signal,colon,gap,owner=null,keyP=1,valueP=1,state=null,swatchP=1}={}) {
    const rk=role(keyRole,keyOver),rv=role(valueRole,valueOver),ks=(colon??mode==='inline')?key+':':key,vs=String(value);
    const sw=state?Math.round(rk.size*.82):0,sg=state?sw+10:0;
    const kw=measure(rk.upper?ks.toUpperCase():ks,rk)+sg,vw=measure(rv.upper?vs.toUpperCase():vs,rv);
    const put=(kx,ky,vx,vy)=>{
      if(keyP>0)fade(keyP,()=>{if(state)fade(swatchP,()=>swatch(id+'-sw',state,kx,ky,{size:sw,owner}));
        text(id+'-k',ks,kx+sg,ky,{role:keyRole,over:keyOver,color:keyColor,owner});});
      if(valueP>0)fade(valueP,()=>{if(mark>0)marker(id+'-mk',vx-8,vy-rv.size*.68,vw+16,rv.size*1.36,mark,{color:markColor,owner});
        text(id+'-v',vs,vx,vy,{role:valueRole,over:valueOver,color:valueColor,owner:mark>0?id+'-mk':owner});});
    };
    if(mode==='inline') {
      const gp=gap??Math.round(rk.size*.4),w=kw+gp+vw,left=align==='center'?x-w/2:align==='right'?x-w:x,vx=left+kw+gp;
      put(left,y+BASELINE*(rv.size-rk.size),vx,y);
      return {x:left,y:y-rv.size*.62,w,h:rv.size*1.24,value:{x:vx,y,w:vw,size:rv.size}};
    }
    const w=Math.max(kw,vw),gp=gap??4,vy=y+rk.size*.62+gp+rv.size*.62,at=bw=>align==='center'?x-bw/2:align==='right'?x-bw:x;
    put(at(kw),y,at(vw),vy);
    return {x:at(w),y:y-rk.size*.62,w,h:vy+rv.size*.62-(y-rk.size*.62),value:{x:at(vw),y:vy,w:vw,size:rv.size}};
  }

  // ------------------------------------------------ the course's state code (defineStates)
  // stateBox: a rectangle in a state's treatment. hatched = hatching inside a dashed outline (never
  // solid); solid = a solid fill with a solid outline. p sweeps the fill left to right (the outline
  // is always whole). register:false (or no id) draws it as decor.
  function stateBox(id,state,x,y,w,h,{p=1,owner=null,register=true,outline=null,weight=2,gap=10,dash=true,alpha=1}={}) {
    const def=STATES[stateOf(state)],col=T[def.token],o=outline||(night?T.white:T.ink),e=clamp(p);
    const draw=()=>{g.save();g.globalAlpha*=alpha;
      if(def.treatment==='hatched'){if(e>0){g.save();g.beginPath();g.rect(x,y,w*e,h);g.clip();g.strokeStyle=night?T[def.soft]:col;g.lineWidth=1.8;g.beginPath();
          for(let q=-h;q<w;q+=gap){g.moveTo(x+q,y+h);g.lineTo(x+q+h,y);}g.stroke();g.restore();}
        g.strokeStyle=o;g.lineWidth=weight;if(dash)g.setLineDash([8,6]);g.strokeRect(x,y,w,h);g.setLineDash([]);}
      else{if(e>0){g.fillStyle=col;g.fillRect(x,y,w*e,h);}g.strokeStyle=o;g.lineWidth=weight;g.strokeRect(x,y,w,h);}
      g.restore();};
    if(register&&id)actor(id,{x,y,w,h},draw,owner);else decor(draw);
    return {x,y,w,h};
  }
  // A legend swatch for a state: a small square at (x, y) = left edge, vertical centre.
  function swatch(id,state,x,y,{size=26,owner=null,register=true,p=1}={}) {
    return stateBox(id,state,x,y-size/2,size,size,{owner,register,p,gap:7,weight:2});
  }

  // ------------------------------------------------ rules and texture (unregistered)
  // Horizontal rule drawn left to right with p. Heavy rules (5–6 px) open a section; hairlines divide.
  function rule(x1,x2,y,p=1,{weight=2,color=T.ink}={}){if(p<=0)return;const e=E.inOut(clamp(p));
    decor(()=>{g.save();g.fillStyle=color;g.fillRect(Math.min(x1,x2),y-weight/2,Math.abs(x2-x1)*e,weight);g.restore();});}
  function vrule(x,y1,y2,p=1,{weight=2,color=T.ink}={}){if(p<=0)return;const e=E.inOut(clamp(p));
    decor(()=>{g.save();g.fillStyle=color;g.fillRect(x-weight/2,Math.min(y1,y2),weight,Math.abs(y2-y1)*e);g.restore();});}
  // Diagonal hatching: the texture of a hatched state (see stateBox) and of "not yet".
  function hatch(x,y,w,h,{color=T.ink,gap=9,width=1.6,alpha=1}={}) {
    decor(()=>{g.save();g.globalAlpha*=alpha;g.beginPath();g.rect(x,y,w,h);g.clip();g.strokeStyle=color;g.lineWidth=width;g.beginPath();
      for(let k=-h;k<w;k+=gap){g.moveTo(x+k,y+h);g.lineTo(x+k+h,y);}g.stroke();g.restore();});
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
  // Strike: ink for "replaced"; pass T.wrong only when the struck thing is wrong.
  function strike(x1,x2,y,p,{color=T.ink,width=3.5}={}){partial([[x1-4,y+3],[x2+4,y-3]],E.inOut(clamp(p)),{color,width});}
  function dotGrid(cx,cy,w,h,{gap=34,color=T.rule,alpha=.55}={}) {
    decor(()=>{g.save();g.globalAlpha*=alpha;g.fillStyle=color;
      for(let x=Math.floor((cx-w/2)/gap)*gap;x<cx+w/2;x+=gap)for(let y=Math.floor((cy-h/2)/gap)*gap;y<cy+h/2;y+=gap)g.fillRect(x-1.2,y-1.2,2.4,2.4);g.restore();});
  }

  // ------------------------------------------------ transitions (screen space, full frame)
  // Leave the content clip for full-frame transitions. It pops the content clip's saved state, so
  // it runs only at the top level of a frame (or inside transition() or decor()): inside view(),
  // fade() or actor() it would pop their camera, alpha or clip instead, so it throws there.
  // Nested calls run inside the already unclipped region. clippedRun(fn): fn is clipped again.
  function unclipped(fn) {
    if(open)return fn();
    if(depth)throw new Error('S.unclipped, S.iris and S.wipe must be called at the top level of a frame (or inside S.transition or S.decor), not inside S.view, S.fade or S.actor');
    open++;bare=true;g.restore();try{fn();}finally{open--;bare=false;g.save();g.beginPath();g.rect(viewport.x,viewport.y,viewport.w,viewport.h);g.clip();}
  }
  function clippedRun(fn){const was=bare;bare=false;try{fn();}finally{bare=was;}}
  // Two-phase iris: an accent disc swells from a meaningful point, then the next scene opens inside
  // it. Both phases paint the full frame; only fn() (the next scene) is clipped to the viewport.
  function iris(cx,cy,p,fn,{mode='paper',color=T.accent}={}) {
    if(p<=0)return;const R=Math.hypot(Math.max(cx,W-cx),Math.max(cy,H-cy))+4,p1=E.inOut(clamp(p*1.8)),p2=E.inOut(clamp((p-.42)/.58));
    unclipped(()=>{g.save();g.setTransform(1,0,0,1,0,0);g.fillStyle=color;g.beginPath();g.arc(cx,cy,Math.max(.5,R*p1),0,Math.PI*2);g.fill();g.restore();
      if(p2<=0)return;
      g.save();g.setTransform(1,0,0,1,0,0);g.beginPath();g.arc(cx,cy,Math.max(.5,R*p2),0,Math.PI*2);g.clip();paintBackground(g,W,H,mode);
      g.beginPath();g.rect(viewport.x,viewport.y,viewport.w,viewport.h);g.clip();clippedRun(fn);g.restore();});
  }
  // Slanted wipe: the next scene's page sweeps in from the right across the full frame.
  function wipe(p,fn,{mode='paper',slant=180}={}) {
    if(p<=0)return;const e=E.inOut(clamp(p)),x=lerp(W+slant,-slant,e);
    unclipped(()=>{g.save();g.setTransform(1,0,0,1,0,0);g.beginPath();g.moveTo(x,0);g.lineTo(W+slant,0);g.lineTo(W+slant,H);g.lineTo(x-slant,H);g.closePath();g.clip();
      paintBackground(g,W,H,mode);g.beginPath();g.rect(viewport.x,viewport.y,viewport.w,viewport.h);g.clip();clippedRun(fn);g.restore();});
  }

  return {g,W,H,T,E,safe,viewport,night,record,decor,transition:inTransition,check,fits,view,fade,actor,text,label,measure,layout,sentence,card,chip,marker,markText,counter,callout,
    stateBox,swatch,onScreen,rule,vrule,hatch,partial,bezier,arrow,scribble,underline,strike,dotGrid,iris,wipe,roundRect,unclipped,
    finish(invariants={}){g.restore();g.filter='none';g.letterSpacing='0px';
      // Transition frames are excluded from the text checks; the words budget applies to the rest.
      const kept=transition?checks.filter(c=>!guards.has(c.id)):checks;
      if(!transition)check('words',words<=WORD_BUDGET,words,'<= '+WORD_BUDGET+' content words on screen');
      return {items,safe,viewport,invariants:{...invariants,checks:[...(invariants.checks||[]),...kept]},transition,words};}};
}

module.exports={T,TYPE,FACES,FONT_FILES,FLOOR,EDGE,WORD_BUDGET,BASELINE,STATES,STATE_ALIASES,E,role,floorOf,clamp,lerp,seg,wordTimes,createCues,
  stepValue,niceStep,spoken,talking,focusOf,cameraAt,orderKeys,fitCamera,beforePush,world,planner,
  extendTheme,defineStates,stateOf,installDesignRuntime,createDesignStage,paintBackground};
