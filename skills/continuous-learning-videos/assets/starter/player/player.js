(()=>{'use strict';
const D=window.COURSE,$=id=>document.getElementById(id),v=$('video');
document.title=D.title;$('course-title').textContent=D.title;document.documentElement.lang=D.language;if(D.subtitle&&$('course-subtitle')){$('course-subtitle').hidden=false;$('course-subtitle').textContent=D.subtitle;}
let state={done:[],positions:{},lesson:D.lessons[0].id,speed:1,captions:false};
try{Object.assign(state,JSON.parse(localStorage.getItem(D.storageKey)||'{}'));}catch{}
if(!Array.isArray(state.done))state.done=[];
if(!state.positions||typeof state.positions!=='object')state.positions={};
state.done=state.done.filter(id=>D.lessons.some(l=>l.id===id));
let current=0,lastSave=0,pending=0;
const save=()=>{try{localStorage.setItem(D.storageKey,JSON.stringify(state));}catch{}};
const clock=t=>`${Math.floor(t/60)}:${String(Math.floor(t%60)).padStart(2,'0')}`;
const date=value=>/^\d{4}-\d{2}-\d{2}/.test(String(value))?String(value).slice(0,10):String(value);
function sourceLink(source){const a=document.createElement('a');try{const u=new URL(source.url);if(!['http:','https:'].includes(u.protocol))return null;a.href=u.href;}catch{return null;}a.textContent=source.title;a.target='_blank';a.rel='noopener noreferrer';return a;}
if(D.job){$('job-context').hidden=false;const a=sourceLink({url:D.job.url,title:`${D.job.employer} · ${D.job.title}`});if(a)$('job-context').append(a);if(D.job.researchedAt)$('job-context').append(document.createTextNode(` · Researched ${date(D.job.researchedAt)}`));}
if(D.objectives?.length){$('objectives-panel').hidden=false;for(const text of D.objectives){const li=document.createElement('li');li.textContent=text;$('objectives').append(li);}}
if(D.reviewVersion){$('review-status').hidden=false;const names={content:'Content review',listening:'Full listening',synchronizedViewing:'Audio and video review',silentInspection:'Silent visual review'};const limits=Object.entries(D.review||{}).filter(([,r])=>r.status!=='completed').map(([key,r])=>`${names[key]||key}: ${r.status}. ${r.coverage}`);$('review-status').textContent='Review edition. '+limits.join(' ');}
function lessonSources(l){$('sources').replaceChildren();$('evidence-kinds').textContent=l.evidenceKinds?.length?'This lesson includes: '+l.evidenceKinds.join(', ')+'.':'';for(const source of D.sources||[]){if(l.sourceIds&&!l.sourceIds.includes(source.id))continue;const a=sourceLink(source);if(!a)continue;const li=document.createElement('li');li.append(a);if(source.accessedAt)li.append(document.createTextNode(` · Checked ${date(source.accessedAt)}`));$('sources').append(li);}}
function practice(l){const valid=typeof l.question==='string'&&Array.isArray(l.options)&&l.options.length>1&&Number.isInteger(l.answer)&&l.answer>=0&&l.answer<l.options.length;$('practice').hidden=!valid;$('answers').replaceChildren();$('feedback').textContent='';if(!valid)return;$('question').textContent=l.question;for(const [i,text] of l.options.entries()){const b=document.createElement('button');b.textContent=text;b.onclick=()=>{const correct=i===l.answer;$('feedback').textContent=(correct?'Correct. ':'Try again. ')+(l.explanation||'');};$('answers').append(b);}}
function cc(){for(const t of v.textTracks)t.mode=state.captions?'showing':'hidden';$('captions').textContent=state.captions?'Captions on':'Captions off';$('captions').setAttribute('aria-pressed',String(state.captions));}
function progress(){const done=state.done.includes(D.lessons[current].id);$('complete').textContent=done?'Completed ✓':'Mark complete';$('complete').setAttribute('aria-pressed',String(done));$('completion').textContent=`${state.done.length} / ${D.lessons.length} complete`;}
function load(index,focus=false){
  if(v.currentSrc&&!v.ended)state.positions[D.lessons[current].id]=v.currentTime;
  current=Math.max(0,Math.min(D.lessons.length-1,index));const l=D.lessons[current];v.pause();state.lesson=l.id;pending=Number(state.positions[l.id])||0;
  $('lesson-title').textContent=l.title;$('goal').textContent=l.goal;$('coverage').textContent=l.coverage;$('lesson-number').textContent=`${l.part?l.part+' · ':''}Lesson ${current+1} / ${D.lessons.length} · ${clock(l.duration)}`;
  v.innerHTML='';v.poster=`posters/${l.id}.png`;v.src=`videos/${l.id}.mp4`;const track=document.createElement('track');track.kind='captions';track.label=D.language;track.srclang=D.language;track.src=`captions/${l.id}.vtt`;track.addEventListener('load',cc);v.append(track);v.load();$('error').hidden=true;
  $('download-video').href=v.getAttribute('src');$('download-captions').href=track.getAttribute('src');$('previous').disabled=current===0;$('next').disabled=current===D.lessons.length-1;
  lessonSources(l);practice(l);
  $('transcript').replaceChildren();for(const beat of l.scenes){const b=document.createElement('button'),title=document.createElement('strong'),text=document.createElement('span');title.textContent=`${clock(beat.start)} · ${beat.headline}`;text.textContent=beat.narration;b.append(title,text);b.onclick=()=>{v.currentTime=beat.start;v.play().catch(()=>{});};$('transcript').append(b);}
  document.querySelectorAll('[data-lesson]').forEach(b=>b.setAttribute('aria-current',String(b.dataset.lesson===l.id)));history.replaceState(null,'','#lesson-'+l.id);progress();save();if(focus)$('lesson-title').focus({preventScroll:true});
}
let lastPart=null;for(const [index,l] of D.lessons.entries()){if(l.part&&l.part!==lastPart){const heading=document.createElement('h3');heading.className='chapter-heading';heading.textContent=l.part;$('lesson-list').append(heading);lastPart=l.part;}const b=document.createElement('button');b.dataset.lesson=l.id;b.textContent=`${index+1}. ${l.title}`;b.onclick=()=>{load(index,true);$('lesson-list').hidden=true;$('browse').textContent='Show lessons';$('browse').setAttribute('aria-expanded','false');};$('lesson-list').append(b);}
$('browse').onclick=()=>{const hidden=$('lesson-list').hidden=!$('lesson-list').hidden;$('browse').textContent=hidden?'Show lessons':'Hide lessons';$('browse').setAttribute('aria-expanded',String(!hidden));};
const parts=[...new Set(D.lessons.map(l=>l.part).filter(Boolean))];if(parts.length&&$('part-overview')){$('part-overview').hidden=false;for(const part of parts){const lessons=D.lessons.filter(l=>l.part===part),b=document.createElement('button');b.textContent=part+' · '+lessons.length+' chapters · '+clock(lessons.reduce((n,l)=>n+l.duration,0));b.onclick=()=>{load(D.lessons.indexOf(lessons[0]),true);$('lesson-title').scrollIntoView({block:'start'});};$('part-buttons').append(b);}}
$('runtime').textContent=`${D.lessons.length} lessons · ${clock(D.lessons.reduce((a,l)=>a+l.duration,0))} total`;
$('previous').onclick=()=>load(current-1,true);$('next').onclick=()=>load(current+1,true);
$('speed').value=String(state.speed);$('speed').onchange=e=>{state.speed=Number(e.target.value);v.playbackRate=state.speed;save();};
$('captions').onclick=()=>{state.captions=!state.captions;cc();save();};
$('complete').onclick=()=>{const id=D.lessons[current].id;state.done=state.done.includes(id)?state.done.filter(x=>x!==id):[...state.done,id];progress();save();};
v.addEventListener('loadedmetadata',()=>{if(pending>0&&pending<v.duration-1)v.currentTime=pending;v.playbackRate=state.speed;cc();});
v.addEventListener('timeupdate',()=>{if(Date.now()-lastSave>1500){state.positions[D.lessons[current].id]=v.currentTime;lastSave=Date.now();save();}});
v.addEventListener('ended',()=>{const id=D.lessons[current].id;if(!state.done.includes(id))state.done.push(id);state.positions[id]=0;progress();save();});
v.addEventListener('error',()=>{$('error').hidden=false;});
let id=state.lesson;try{id=decodeURIComponent(location.hash.replace(/^#lesson-/,''))||id;}catch{}load(Math.max(0,D.lessons.findIndex(l=>l.id===id)));
})();
