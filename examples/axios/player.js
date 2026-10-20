(()=>{'use strict';
const originalCourse=window.COURSE;
const D={...originalCourse,language:'en',storageKey:'axios-motion-v1',lessons:originalCourse.lessons.map(l=>({...l,...window.COURSE_PRACTICE?.[l.id],part:`Chapter ${l.module} · ${l.moduleTitle}`}))},$=id=>document.getElementById(id),v=$('video');
document.documentElement.lang=D.language;
if($('skip-lesson'))$('skip-lesson').onclick=event=>{event.preventDefault();$('lesson-title').focus({preventScroll:true});$('lesson-title').scrollIntoView({block:'start'});};
let state={done:[],positions:{},lesson:D.lessons[0].id,speed:1,captions:false};
try{const saved=JSON.parse(localStorage.getItem(D.storageKey)||'{}');if(saved&&typeof saved==='object'){
 const ids=new Set(D.lessons.map(l=>l.id));state.done=[...new Set((Array.isArray(saved.done)?saved.done:[]).filter(id=>ids.has(id)))];
 if(saved.positions&&typeof saved.positions==='object'&&!Array.isArray(saved.positions))for(const [id,time] of Object.entries(saved.positions))if(ids.has(id)&&typeof time==='number'&&Number.isFinite(time)&&time>=0)state.positions[id]=time;
 if(ids.has(saved.lesson))state.lesson=saved.lesson;if([.75,1,1.25,1.5,2].includes(Number(saved.speed)))state.speed=Number(saved.speed);if(typeof saved.captions==='boolean')state.captions=saved.captions;
}}catch{}
let current=0,lastSave=0,pending=0;
const panel=$('course-panel'),lessonRows=new Map();let courseOpener=$('browse'),panelDestination=null;
function focusLesson(){const heading=$('lesson-title');heading.focus({preventScroll:true});heading.scrollIntoView({block:'start'});}
function closeCourse(toLesson=false){panelDestination=toLesson?'lesson':null;if(panel.open)panel.close();else if(toLesson)focusLesson();}
function openCourse(opener){courseOpener=opener;panelDestination=null;if(!panel.open)panel.showModal();$('browse').setAttribute('aria-expanded','true');$('lesson-browse').setAttribute('aria-expanded','true');const row=lessonRows.get(D.lessons[current].id)?.button;if(row){row.focus({preventScroll:true});row.scrollIntoView({block:'nearest'});}}
panel.addEventListener('close',()=>{$('browse').setAttribute('aria-expanded','false');$('lesson-browse').setAttribute('aria-expanded','false');$('reset-confirm').hidden=true;if(panelDestination==='lesson')focusLesson();else courseOpener.focus({preventScroll:true});panelDestination=null;});
$('browse').onclick=()=>openCourse($('browse'));$('lesson-browse').onclick=()=>openCourse($('lesson-browse'));$('close-panel').onclick=()=>closeCourse();
let mediaEpoch=0,seekSerial=0,mediaObject=null,mediaRequest=null,mediaAbort=null,mediaURL='',autoSeekingAttempted=false;
let playbackWanted=false,lastMediaPaused=v.paused;
function observePlaybackIntent(){if(v.paused!==lastMediaPaused)playbackWanted=!v.paused;lastMediaPaused=v.paused;}
v.addEventListener('play',()=>{lastMediaPaused=v.paused;if(!v.paused)playbackWanted=true;});
v.addEventListener('pause',()=>{lastMediaPaused=v.paused;if(v.paused)playbackWanted=false;});
// load() resets paused and discards queued media events. Preserve intent across
// that internal reset, while observing any user pause before replacing the source.
function replaceMedia(source,keepIntent=true){if(keepIntent)observePlaybackIntent();else playbackWanted=false;v.src=source;v.load();lastMediaPaused=v.paused;}
function resumeWantedPlayback(){observePlaybackIntent();if(playbackWanted&&v.paused)v.play().catch(()=>{});}
function mediaStatus(text='',retry=false){const p=$('media-status');if(p){p.textContent=text;p.hidden=!text;}if($('retry-media'))$('retry-media').hidden=!retry;}
function metadataReady(signal,next=false){return new Promise((resolve,reject)=>{
 const clean=()=>{clearTimeout(timer);v.removeEventListener('loadedmetadata',loaded);v.removeEventListener('error',failed);signal?.removeEventListener('abort',aborted);};
 const loaded=()=>{clean();resolve();},failed=()=>{clean();reject(new Error('Video metadata unavailable'));},aborted=()=>{clean();reject(new DOMException('Chapter changed','AbortError'));};
 const timer=setTimeout(()=>{clean();reject(new Error('Video metadata timed out'));},20000);
 if(signal?.aborted){aborted();return;}if(!next&&v.error){failed();return;}if(!next&&v.readyState>=1){loaded();return;}
 v.addEventListener('loadedmetadata',loaded,{once:true});v.addEventListener('error',failed,{once:true});signal?.addEventListener('abort',aborted,{once:true});
});}
function prepareSeeking(force=false){
 if(mediaRequest)return mediaRequest;if(mediaObject&&!v.error&&!force)return Promise.resolve();
 const epoch=mediaEpoch,signal=mediaAbort.signal,download=new AbortController(),cancel=()=>download.abort();let candidate=null;mediaStatus('Preparing chapter navigation…');
 signal.addEventListener('abort',cancel,{once:true});const downloadTimer=setTimeout(cancel,90000);
 const request=(async()=>{const response=await fetch(mediaURL,{credentials:'same-origin',signal:download.signal});if(!response.ok)throw new Error('Video unavailable');const blob=await response.blob();clearTimeout(downloadTimer);if(epoch!==mediaEpoch)return;
  const position=pending>0?pending:v.currentTime;candidate=URL.createObjectURL(new Blob([blob],{type:'video/mp4'}));if(mediaObject)URL.revokeObjectURL(mediaObject);mediaObject=candidate;pending=position;
  const ready=metadataReady(signal,true);replaceMedia(candidate);await ready;if(epoch!==mediaEpoch)return;if(position<v.duration)v.currentTime=position;pending=0;mediaStatus();$('error').hidden=true;resumeWantedPlayback();
 })().catch(error=>{if(candidate)URL.revokeObjectURL(candidate);if(epoch===mediaEpoch&&!signal.aborted){
   if(mediaObject===candidate)mediaObject=null;if(candidate&&v.getAttribute('src')===candidate)replaceMedia(mediaURL);
   mediaStatus('Chapter navigation could not be prepared. Retry the video or download the MP4.',true);
  }throw error;
 }).finally(()=>{clearTimeout(downloadTimer);signal.removeEventListener('abort',cancel);if(mediaRequest===request)mediaRequest=null;});mediaRequest=request;return request;
}
async function jumpTo(time,requestPlayback=true){observePlaybackIntent();if(requestPlayback)playbackWanted=true;const epoch=mediaEpoch,serial=++seekSerial;pending=time;try{
 if(v.error)await prepareSeeking(true);else if(v.readyState===0)await metadataReady(mediaAbort.signal);
 if(epoch!==mediaEpoch||serial!==seekSerial)return;const end=v.seekable.length?v.seekable.end(v.seekable.length-1):0;if(time>end+.01)await prepareSeeking();
 if(epoch!==mediaEpoch||serial!==seekSerial)return;v.currentTime=Math.min(time,Math.max(0,v.duration-.01));pending=0;resumeWantedPlayback();
 }catch(error){if(epoch===mediaEpoch&&serial===seekSerial&&error.name!=='AbortError')mediaStatus('Chapter navigation could not be prepared. Retry the video or download the MP4.',true);}}
v.addEventListener('loadeddata',()=>{if(!autoSeekingAttempted&&!mediaObject&&v.duration>0&&(!v.seekable.length||v.seekable.end(v.seekable.length-1)<v.duration-.1)){autoSeekingAttempted=true;prepareSeeking().catch(()=>{});}});
if($('retry-media'))$('retry-media').onclick=()=>{observePlaybackIntent();playbackWanted=true;const epoch=mediaEpoch,time=pending||v.currentTime||0;prepareSeeking(true).then(()=>{if(epoch===mediaEpoch)jumpTo(time,false);}).catch(()=>{});};
const save=()=>{try{localStorage.setItem(D.storageKey,JSON.stringify(state));}catch{}};
const clock=t=>`${Math.floor(t/60)}:${String(Math.floor(t%60)).padStart(2,'0')}`;
const date=value=>/^\d{4}-\d{2}-\d{2}/.test(String(value))?String(value).slice(0,10):String(value);
function sourceLink(source){const a=document.createElement('a');try{const u=new URL(source.url);if(!['http:','https:'].includes(u.protocol))return null;a.href=u.href;}catch{return null;}a.textContent=source.title;a.target='_blank';a.rel='noopener noreferrer';return a;}
if(D.job){$('job-context').hidden=false;const a=sourceLink({url:D.job.url,title:`${D.job.employer} · ${D.job.title}`});if(a)$('job-context').append(a);if(D.job.researchedAt)$('job-context').append(document.createTextNode(` · Researched ${date(D.job.researchedAt)}`));}
if(D.objectives?.length){$('objectives-panel').hidden=false;for(const text of D.objectives){const li=document.createElement('li');li.textContent=text;$('objectives').append(li);}}
if(Array.isArray(D.glossary)&&$('glossary')){for(const item of D.glossary){if(!item||typeof item.term!=='string'||!item.term.trim()||typeof item.definition!=='string'||!item.definition.trim())continue;const term=document.createElement('dt'),definition=document.createElement('dd');term.textContent=item.term;definition.textContent=item.definition;$('glossary').append(term,definition);}if($('glossary').children.length)$('glossary-panel').hidden=false;}
if(D.reviewVersion||Object.values(D.review||{}).some(r=>r.status==='failed')){const names={content:'Content review',listening:'Full listening',synchronizedViewing:'Audio and video review',silentInspection:'Silent visual review'},short={content:'content',listening:'listening',synchronizedViewing:'audio/video',silentInspection:'silent review'},entries=Object.entries(D.review||{}),limits=entries.filter(([,r])=>r.status!=='completed'),failed=entries.some(([,r])=>r.status==='failed');$('review-band').hidden=false;$('review-band').dataset.failed=String(failed);$('review-status').textContent=(failed?'Review issue':'Review edition')+(limits.length?' · '+limits.map(([key,r])=>`${short[key]||key} ${r.status}`).join(' · '):' · see coverage');for(const [key,r] of entries){const li=document.createElement('li');li.textContent=`${names[key]||key}: ${r.status}. ${r.coverage||'No coverage recorded.'}`+(r.reviewer?` Reviewer: ${r.reviewer}.`:'');$('review-coverage').append(li);}}
function lessonSources(l){$('evidence-kinds').textContent=l.module===1?'Company context and conceptual explanation. Atlantic Technology and all teaching characters are fictional.':l.module===2?'Illustrative advertiser case. All customer names, prices, campaign figures, and results are invented for teaching.':l.module===3?'Conceptual Salesforce examples. These are fictional records and configurations, not Axios screens or disclosed internal procedures.':l.module===4?'Published role requirements plus simulated candidates, interviews, and assessments. No hiring outcome is promised.':'Illustrative first-year journey. Dates, colleagues, projects, results, and reviews are not an official Axios schedule or career ladder.';$('evidence-kinds').hidden=false;}
function practice(l){
 const valid=typeof l.question==='string'&&Array.isArray(l.options)&&l.options.length>1&&Number.isInteger(l.answer)&&l.answer>=0&&l.answer<l.options.length;
 $('practice').hidden=!valid&&!l.check;$('question').textContent=valid?l.question:'';$('answers').replaceChildren();$('feedback').textContent='';
 $('reflection-question').textContent=l.check?.question||'';$('reflection-prompt').textContent=l.check?.prompt||'';
 if(!valid)return;
 for(const [i,text] of l.options.entries()){
  const b=document.createElement('button');b.type='button';b.textContent=text;b.setAttribute('aria-pressed','false');
  b.onclick=()=>{for(const option of $('answers').children)option.setAttribute('aria-pressed',String(option===b));const correct=i===l.answer,detail=l.optionFeedback?.[i]||l.explanation||'';$('feedback').textContent=(correct?'Correct. ':'Try again. ')+detail;};
  $('answers').append(b);
 }
}
function cc(){for(const t of v.textTracks)t.mode=state.captions?'showing':'hidden';$('captions').textContent=state.captions?'Captions on':'Captions off';$('captions').setAttribute('aria-pressed',String(state.captions));}
function progress(){const done=state.done.includes(D.lessons[current].id),summary=`${state.done.length} / ${D.lessons.length} complete`;$('complete').textContent=done?'Completed ✓':'Mark complete';$('complete').setAttribute('aria-pressed',String(done));$('completion').textContent=summary;$('completion-summary').textContent=summary;$('course-progress').max=D.lessons.length;$('course-progress').value=state.done.length;for(const [id,row] of lessonRows){const complete=state.done.includes(id);row.button.dataset.done=String(complete);row.button.setAttribute('aria-current',String(id===D.lessons[current].id));row.button.setAttribute('aria-label',row.description+(complete?', completed':''));row.check.textContent=complete?'✓':'';}}
function load(index,focus=false,remember=true){
  if(remember&&v.currentSrc&&!v.ended)state.positions[D.lessons[current].id]=v.currentTime;
  mediaEpoch++;seekSerial++;mediaAbort?.abort();mediaAbort=new AbortController();mediaRequest=null;if(mediaObject)URL.revokeObjectURL(mediaObject);mediaObject=null;autoSeekingAttempted=false;mediaStatus();
  current=Math.max(0,Math.min(D.lessons.length-1,index));const l=D.lessons[current];state.lesson=l.id;pending=Number(state.positions[l.id])||0;
  $('lesson-title').textContent=l.title;$('goal').textContent=l.goal;$('coverage').textContent=`Original chapter coverage: ${l.coverage}`;$('lesson-part').textContent=l.part||'The learning journey';$('lesson-number').textContent=`Lesson ${current+1} / ${D.lessons.length} · ${clock(l.duration)}`;
  v.innerHTML='';v.poster=`posters/${l.id}.png`;mediaURL=`videos/${l.id}.mp4`;const track=document.createElement('track');track.kind='captions';track.label=D.language;track.srclang=D.language;track.src=`captions/${l.id}.vtt`;track.addEventListener('load',cc);v.append(track);replaceMedia(mediaURL,false);$('error').hidden=true;
  $('download-video').href=v.getAttribute('src');$('download-captions').href=track.getAttribute('src');$('previous').disabled=current===0;$('next').disabled=current===D.lessons.length-1;
  lessonSources(l);practice(l);$('practice').open=false;
  $('transcript').replaceChildren();for(const beat of l.scenes){const b=document.createElement('button'),time=document.createElement('span'),body=document.createElement('span'),title=document.createElement('strong'),text=document.createElement('span');time.className='scene-time';time.textContent=clock(beat.start);body.className='scene-body';title.textContent=beat.headline;text.className='scene-copy';text.textContent=beat.narration;body.append(title,text);b.append(time,body);b.onclick=()=>jumpTo(beat.start);$('transcript').append(b);}
  document.querySelectorAll('[data-lesson]').forEach(b=>b.setAttribute('aria-current',String(b.dataset.lesson===l.id)));history.replaceState(null,'','#lesson-'+l.id);progress();save();if(focus){if(panel.open)closeCourse(true);else focusLesson();}
}
let lastPart=null;for(const [index,l] of D.lessons.entries()){if(l.part&&l.part!==lastPart){const heading=document.createElement('h3');heading.className='chapter-heading';heading.textContent=l.part;$('lesson-list').append(heading);lastPart=l.part;}const b=document.createElement('button'),number=document.createElement('span'),body=document.createElement('span'),title=document.createElement('span'),duration=document.createElement('span'),check=document.createElement('span');b.dataset.lesson=l.id;number.className='nav-number';number.textContent=String(index+1).padStart(2,'0');title.className='nav-title';title.textContent=l.title;duration.className='nav-duration';duration.textContent=clock(l.duration);check.className='nav-check';check.setAttribute('aria-hidden','true');body.append(title,duration);b.append(number,body,check);lessonRows.set(l.id,{button:b,number,check,description:`Lesson ${index+1}: ${l.title}, ${clock(l.duration)}`});b.onclick=()=>{load(index,false);closeCourse(true);};$('lesson-list').append(b);}
const parts=[...new Set(D.lessons.map(l=>l.part).filter(Boolean))];if(parts.length&&$('part-overview')){$('part-overview').hidden=false;for(const part of parts){const lessons=D.lessons.filter(l=>l.part===part),b=document.createElement('button');b.textContent=part+' · '+lessons.length+' chapters · '+clock(lessons.reduce((n,l)=>n+l.duration,0));b.onclick=()=>{load(D.lessons.indexOf(lessons[0]),false);closeCourse(true);};$('part-buttons').append(b);}}
const minutes=Math.round(D.lessons.reduce((a,l)=>a+l.duration,0)/60),runtime=minutes>=60?`${Math.floor(minutes/60)}h ${String(minutes%60).padStart(2,'0')}m`:`${minutes} min`;$('runtime').textContent=`${D.lessons.length} lessons · ${runtime}`;
$('download-transcript').onclick=()=>{const l=D.lessons[current];const text=`${l.id}. ${l.title}\n\nSynthetic narration. Illustrative cases are fictional.\n\n`+l.scenes.map(s=>`${clock(s.start)} — ${s.headline}\n${s.narration}`).join('\n\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:'text/plain'}));a.download=`${l.id}-transcript.txt`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),5000)};
$('reset').onclick=()=>{$('reset-confirm').hidden=false;$('reset-yes').focus();};$('reset-no').onclick=()=>{$('reset-confirm').hidden=true;$('reset').focus();};$('reset-yes').onclick=()=>{state.done=[];state.positions={};pending=0;v.currentTime=0;load(0,false,false);save();closeCourse(true);};
$('previous').onclick=()=>load(current-1,true);$('next').onclick=()=>load(current+1,true);
$('speed').value=String(state.speed);$('speed').onchange=e=>{state.speed=Number(e.target.value);v.playbackRate=state.speed;save();};
$('captions').onclick=()=>{state.captions=!state.captions;cc();save();};
$('complete').onclick=()=>{const id=D.lessons[current].id;state.done=state.done.includes(id)?state.done.filter(x=>x!==id):[...state.done,id];progress();save();};
v.addEventListener('loadedmetadata',()=>{$('error').hidden=true;if(pending>0&&pending<v.duration-1)v.currentTime=pending;v.playbackRate=state.speed;cc();});
v.addEventListener('timeupdate',()=>{if(Date.now()-lastSave>1500){state.positions[D.lessons[current].id]=v.currentTime;lastSave=Date.now();save();}});
v.addEventListener('ended',()=>{const id=D.lessons[current].id;if(!state.done.includes(id))state.done.push(id);state.positions[id]=0;progress();save();});
v.addEventListener('error',()=>{$('error').hidden=false;if($('retry-media'))$('retry-media').hidden=false;});
function hashLesson(){if(!location.hash.startsWith('#lesson-'))return -1;try{return D.lessons.findIndex(l=>l.id===decodeURIComponent(location.hash.slice(8)));}catch{return -1;}}
const initial=hashLesson();load(initial>=0?initial:Math.max(0,D.lessons.findIndex(l=>l.id===state.lesson)));
window.addEventListener('hashchange',()=>{const index=hashLesson();if(index>=0&&index!==current)load(index,true);});
})();
