"""Template upgrade: top-band chrome, the practice panel, new templates and the stage's text checks."""
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parent.parent
PRODUCTION = ROOT / 'assets/starter/production-source'

# One reusable canvas, as the audit uses; snippets append their own assertions. Examples are
# neutral fiction: parcels moving through depots.
STAGE = """
const assert=require('node:assert/strict'),canvas=require(process.env.CANVAS_MODULE),D=require('./design.cjs'),tpl=require('./templates.cjs');
D.installDesignRuntime(canvas);
D.defineStates({planned:{color:'#2350C8',label:'Planned',treatment:'hatched'},shipped:{color:'#13A0B0',label:'Shipped'},held:{color:'#7A5C2E',label:'Held'}},{aliases:{sent:'shipped'}});
const {T}=D,course={width:1280,height:720},g0=canvas.createCanvas(1280,720).getContext('2d');
const frame=(fn,opts)=>{const S=D.createDesignStage(g0,course,opts);fn(S);return S.finish();};
// Calls expected to throw run on their own canvas, so an abandoned frame cannot leak its clip.
const fresh=(fn,opts)=>{const S=D.createDesignStage(canvas.createCanvas(1280,720).getContext('2d'),course,opts);fn(S);return S.finish();};
const px=(x,y)=>Array.from(g0.getImageData(x,y,1,1).data),sum=p=>p[0]+p[1]+p[2];
const rgb=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
const share=(x,y,w,h,hex,d=40)=>{const a=g0.getImageData(x,y,w,h).data,q=rgb(hex);let n=0;
  for(let i=0;i<a.length;i+=4)if(Math.abs(a[i]-q[0])+Math.abs(a[i+1]-q[1])+Math.abs(a[i+2]-q[2])<d)n++;return n/(w*h);};
const failed=r=>r.invariants.checks.filter(c=>!c.passed).map(c=>c.id);
const ids=r=>r.items.map(i=>i.id),by=r=>Object.fromEntries(r.items.map(i=>[i.id,i]));
const measure=(s,name,over)=>{let w;fresh(S=>{const r=D.role(name,over);w=S.measure(r.upper?s.toUpperCase():s,r);});return w;};
const st=(s,a,d=.25)=>s.split(' ').map((_,i)=>a+i*d);
// The frame audit's rules (audit.cjs): labels in the safe zone, no unowned intersections, no failed checks.
const hit=(a,b)=>Math.min(a.x+a.w,b.x+b.w)>Math.max(a.x,b.x)&&Math.min(a.y+a.h,b.y+b.h)>Math.max(a.y,b.y);
const inside=(a,b)=>a.x>=b.x&&a.y>=b.y&&a.x+a.w<=b.x+b.w&&a.y+a.h<=b.y+b.h;
function problems(r) {
  const m=new Map(r.items.map(i=>[i.id,i])),owns=(c,p)=>{const seen=new Set();for(let n=c.owner;n&&!seen.has(n);n=m.get(n)?.owner){seen.add(n);if(n===p.id)return true;}return false;};
  const its=r.items.filter(i=>i.alpha>.1&&hit(i.bounds,r.viewport)),out=[];
  for(const a of its)if(a.kind==='label'&&!inside(a.bounds,r.safe))out.push('safe-zone:'+a.id);
  for(let i=0;i<its.length;i++)for(let j=i+1;j<its.length;j++){const a=its[i],b=its[j];
    if((owns(a,b)&&inside(a.bounds,b.bounds))||(owns(b,a)&&inside(b.bounds,a.bounds)))continue;if(hit(a.bounds,b.bounds))out.push(a.id+' x '+b.id);}
  return [...out,...failed(r)];
}
// Every output frame (30 fps) of a span, drawn under a held camera and under a slow push.
function sweep(name,from,to,draw,{background='paper',zooms=[1,1.03]}={}) {
  for(let f=Math.floor(from*30);f<=Math.ceil(to*30);f++)for(const zoom of zooms){const t=f/30;
    const r=frame(S=>draw(S,t,fn=>S.view({x:640,y:340,zoom},fn)),{background});assert.deepEqual(problems(r),[],`${name} t=${t.toFixed(3)} zoom=${zoom}`);}
}
"""


class TemplateUpgradeTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which('node'):
            self.skipTest('Node.js is required')
        module = os.environ.get('CANVAS_MODULE') or str(PRODUCTION / 'node_modules/@napi-rs/canvas')
        if not Path(module).is_dir():
            self.skipTest('Canvas runtime is not configured')
        self.env = dict(os.environ, CANVAS_MODULE=module)

    def node(self, code):
        result = subprocess.run(['node', '-e', STAGE + code], cwd=PRODUCTION, env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr[-3000:])
        return result

    def test_fiction_badge_follows_its_windows_and_reads_on_paper_and_night(self):
        self.node("""
const badge=(t,o,background)=>{let box;const r=frame(S=>{box=tpl.fictionBadge(S,t,o);},{background});return {r,box};};
const W={windows:[[1,8],[12,20]]},{r,box}=badge(5,W);
// Right-aligned in the top band on the rail's line, above the content viewport.
assert.ok(Math.abs(box.x+box.w-1240)<1e-9);assert.equal(box.y+box.h/2,tpl.PAGE.bandY);assert.ok(box.y+box.h<=r.viewport.y);
assert.ok(share(Math.ceil(box.x)+2,box.y+2,Math.floor(box.w)-4,5,T.fiction)>.95,'fiction hue');
assert.ok(share(Math.ceil(box.x)+14,box.y+9,Math.floor(box.w)-28,12,T.fictionInk,90)>.05,'white chrome type');
// Chrome: unregistered decor, no content words, and the 18 px chrome floor holds.
assert.deepEqual(r.items,[]);assert.equal(r.words,0);assert.deepEqual(failed(r),[]);
// Off over real material between windows and after the last one; {from, until} is one window.
for(const t of [0,9,10.5,21])assert.equal(badge(t,W).box,null,'off at '+t);
assert.deepEqual(badge(5,{from:1,until:8}).box,box);assert.equal(badge(9,{from:1,until:8}).box,null);
assert.ok(badge(99,{from:1}).box);assert.equal(badge(5,{}).box,null);
// On night a thin light keyline frames the block; paper gets none.
const nb=badge(5,{from:0},'night').box,lit=px(Math.floor(nb.x)-1,50);frame(()=>{},{background:'night'});const dark=px(Math.floor(nb.x)-1,50);
assert.ok(sum(lit)>350&&sum(dark)<200,'keyline '+lit+' / '+dark);
badge(5,{from:0});const edge=px(Math.floor(box.x)-1,50);frame(()=>{});const paper=px(Math.floor(box.x)-1,50);
assert.ok(Math.abs(sum(edge)-sum(paper))<12,'no keyline on paper');
""")

    def test_progress_rail_is_chrome_with_inverted_ink_and_stays_off_night(self):
        self.node("""
const steps=['Arrive','Sort','Ship'],rail=(t,o={},background)=>frame(S=>tpl.progressRail(S,t,{steps,at:[1,5,9],from:0,until:20,...o}),{background});
const pad=16,gap=18,x1=40+measure('Arrive','chrome')+pad+gap,w1=measure('Sort','chrome'),x2=x1+w1+pad+gap,y=tpl.PAGE.bandY;
let r=rail(7);
assert.deepEqual(r.items,[]);assert.equal(r.words,0);assert.deepEqual(failed(r),[]);
// The current section is an ink block with white type; the signal colour never appears in the band.
assert.ok(share(Math.ceil(x1-7),y-12,4,24,T.ink)>.95,'ink block');
assert.ok(share(Math.ceil(x1),y-8,Math.floor(w1),16,T.white,120)>.08,'white type');
assert.equal(share(0,0,1280,80,T.signal,80),0);
// Future sections stay legible: the chrome role is exempt from the edge guard that hid the old rail text.
const dark=(x,w)=>{const a=g0.getImageData(Math.ceil(x),y-8,Math.floor(w),16).data;let n=0;for(let i=0;i<a.length;i+=4)if(a[i]+a[i+1]+a[i+2]<520)n++;return n;};
assert.ok(dark(x2,measure('Ship','chrome'))>40,'future label drawn');
// Old call sites (steps, at, from, until) keep working; states add swatches and must exist.
rail(7,{states:['planned','sent','held']});assert.throws(()=>fresh(S=>tpl.progressRail(S,7,{steps,at:[1,5,9],from:0,until:20,states:['lost']})),/Unknown state: lost/);
// Never over a night panel: hidden on a night stage, and faded out by the start of a night window.
const lightBand=()=>{const a=g0.getImageData(30,20,800,50).data;let n=0;for(let i=0;i<a.length;i+=4)if(a[i]+a[i+1]+a[i+2]>300)n++;return n;};
rail(7,{},'night');assert.equal(lightBand(),0);
const ink=()=>share(30,20,800,50,T.ink,30);
rail(12);assert.ok(ink()>.01);
for(const t of [11,12,15])assert.equal((rail(t,{night:[[11,15]]}),ink()),0,'rail during the night window at '+t);
rail(10.5,{night:[[11,15]]});assert.ok(ink()>.01,'whole until its fade starts');
rail(16,{night:[[11,15]]});assert.ok(ink()>.01,'back after the window');
""")

    def test_question_keeps_old_calls_and_adds_art_tags_and_a_signal_reveal(self):
        self.node("""
const strokes=[],stroke=g0.stroke.bind(g0);g0.stroke=(...a)=>{strokes.push(String(g0.strokeStyle).toUpperCase());return stroke(...a);};
const old={x:640,y:340,start:20,end:31,kicker:'Check yourself',prompt:'If 4 parcels return to a depot of 20, how many are there?',options:['16','24','20'],
  correct:1,revealAt:28,reason:'Returned parcels are added to the depot.'};
const ask=(t,o=old)=>frame(S=>tpl.question(S,t,o),{background:'night'});
// Options are on screen before the reveal; nothing is highlighted or struck yet.
let r=ask(27.5),b=by(r);
for(const i of [0,1,2])assert.ok(b['q-o'+i]&&b['q-o'+i+'-t'].owner==='q-o'+i);assert.ok(!b['q-o1-t-mk']);
// The kicker takes the signal highlighter and owns its words.
assert.equal(b['q-kicker'].owner,'q-kicker-mk');
// On the answer word the correct option takes the signal highlighter; wrong options strike in T.wrong.
strokes.length=0;r=ask(29.5);b=by(r);
assert.equal(b['q-o1-t'].owner,'q-o1-t-mk');assert.equal(b['q-o1-t-mk'].owner,'q-o1');assert.ok(inside(b['q-o1-t-mk'].bounds,b['q-o1'].bounds));
assert.equal(strokes.filter(s=>s===T.wrong).length,2);assert.ok(!strokes.includes(T.accent));
assert.ok(share(612,366,56,4,T.signal,60)>.8,'signal band behind the answer');
assert.ok(b['q-o0'].alpha<.5&&b['q-o1'].alpha===1);
sweep('question',20,31,(S,t)=>tpl.question(S,t,old),{background:'night',zooms:[1,1.015]});
// art draws a picture between the prompt and the options; optionsAt, tags and promptAfter.
let box=null,calls=0;const art=(S,b)=>{box=b;calls++;assert.equal(S.night,true);S.stateBox('shelf','sent',b.x+40,b.y+20,b.w/2,b.h-40);};
const full={...old,art,tags:[{text:'Too few',state:'planned'},{text:'Restocked',state:'shipped'},{text:'Lost one'}],optionsAt:25.5,promptAfter:.3};
r=ask(25.4,full);assert.equal(calls,1);assert.ok(!ids(r).some(i=>/^q-o/.test(i)),'options wait for optionsAt');
assert.ok(box.y>=r.safe.y&&box.y+box.h<=r.safe.y+r.safe.h&&box.x>=r.safe.x&&box.x+box.w<=r.safe.x+r.safe.w);
const promptBottom=Math.max(...r.items.filter(i=>i.id.startsWith('q-prompt-w')).map(i=>i.bounds.y+i.bounds.h));assert.ok(promptBottom<=box.y);
r=ask(28.3,full);assert.ok(!ids(r).some(i=>/^q-t/.test(i)),'tags wait for tagsAt');
r=ask(30,full);b=by(r);
for(const i of [0,1,2]){assert.ok(b['q-o'+i].bounds.y>=box.y+box.h,'options below the picture');assert.ok(b['q-t'+i].bounds.y>=b['q-o'+i].bounds.y+b['q-o'+i].bounds.h);}
assert.ok(b['q-ts0']&&b['q-ts1']&&!b['q-ts2']);assert.ok(b['q-prompt-w0'].alpha<.5,'prompt yields after the reveal');
r=frame(S=>tpl.question(S,30,{...full,tagsAt:31}),{background:'night'});assert.ok(!ids(r).some(i=>/^q-t/.test(i)));
sweep('question with art',20,31,(S,t)=>tpl.question(S,t,full),{background:'night',zooms:[1,1.015]});
""")

    def test_readout_and_state_key_set_the_state_code_beside_their_lanes(self):
        self.node("""
const rows=[{key:'Planned',value:'1,200',state:'planned',y:250,at:1},{key:'Shipped',value:'900',sub:'by Friday',state:'sent',y:350,at:2,valueAt:3,mark:1},
  {key:'Held',value:null,y:450,at:4}],ro=t=>frame(S=>tpl.readout(S,t,{x:820,width:360,cursor:400,rows}));
assert.deepEqual(ro(.5).items,[]);
let b=by(ro(2.5));assert.ok(b['ro-s0']&&b['ro-k0']&&b['ro-v0']&&b['ro-s1']&&b['ro-k1']&&b['ro-u1']);assert.ok(!b['ro-v1']&&!b['ro-k2'],'values land on their own cue');
const r=ro(6);b=by(r);
for(const i of [0,1]){const v=b['ro-v'+i].bounds;assert.ok(Math.abs(v.x+v.w-2-1180)<1e-6,'right-aligned');assert.ok(Math.abs(v.y+v.h/2-rows[i].y)<1e-6,'on its lane');}
assert.equal(b['ro-v1'].owner,'ro-m1');assert.ok(b['ro-k2']&&!b['ro-v2']&&!b['ro-s2'],'a null value draws nothing');
assert.ok(b['ro-u1'].bounds.y>=b['ro-k1'].bounds.y+b['ro-k1'].bounds.h);assert.ok(b['ro-s0'].bounds.x+b['ro-s0'].bounds.w<b['ro-k0'].bounds.x);
assert.deepEqual(problems(r),[]);
// State key: labels default to the state's own label; items land on their cues; the row width is returned.
let w;const k=frame(S=>{w=tpl.stateKey(S,5,{x:100,y:520,items:[{state:'planned',at:1},{state:'sent',label:'On its way',at:2},{state:'held',at:9}]});});
assert.deepEqual(ids(k),['sk-s0','sk-l0','sk-s1','sk-l1']);
const L=by(k);assert.ok(Math.abs(L['sk-l0'].bounds.w-4-measure('Planned','label'))<1e-6);assert.ok(Math.abs(L['sk-l1'].bounds.w-4-measure('On its way','label'))<1e-6);
assert.ok(Math.abs(w-(3*36+measure('Planned','label')+measure('On its way','label')+measure('Held','label')+2*34))<1e-6);
assert.deepEqual(problems(k),[]);
assert.throws(()=>fresh(S=>tpl.stateKey(S,5,{x:100,y:520,items:[{state:'lost',at:0}]})),/Unknown state: lost/);
""")

    def test_section_head_shows_one_item_at_a_time_in_screen_space(self):
        self.node("""
const items=[{text:'Parcels wait at the depot',times:st('Parcels wait at the depot',1,.2)},{text:'Then they ship in batches',times:st('Then they ship in batches',7,.2),marks:{4:8.2}}];
const head=(t,inView)=>frame(S=>{const draw=()=>tpl.sectionHead(S,t,{ruleAt:.5,items,deck:{text:'Week 12',times:[7,7.3]}});inView?S.view({x:2000,y:900,zoom:1.4},draw):draw();});
// The first item lifts away before the second's first word; they never share a frame.
for(let f=0;f<=12*30;f++){const t=f/30,r=head(t),vis=k=>r.items.some(i=>i.id.startsWith(`head${k}-w`)&&i.alpha>.1);
  assert.ok(!(vis(0)&&vis(1)),'both items at '+t);assert.deepEqual(problems(r),[],'t='+t);}
assert.ok(head(3).items.some(i=>i.id==='head0-w4'));assert.ok(!head(9).items.some(i=>i.id.startsWith('head0')));
// Screen space: the same bounds inside a camera view as outside it.
const pos=r=>r.items.map(i=>[i.id,i.bounds]);assert.deepEqual(pos(head(9,true)),pos(head(9)));
const r=head(9),b=by(r);assert.equal(b['head1-w4'].owner,'head1-mark4');assert.ok(Math.abs(b['head1-w0'].bounds.y+b['head1-w0'].bounds.h/2-tpl.PAGE.headY)<1e-6);
assert.ok(Math.abs(b['head-deck0-w1'].bounds.x+b['head-deck0-w1'].bounds.w-2-tpl.PAGE.right)<1e-6,'deck right-aligned');
assert.ok(share(200,tpl.PAGE.ruleY-2,800,4,T.ink,40)>.9,'heavy rule');
// A wrapped head hangs from its first line under the rule.
const long='Every parcel that leaves the north depot is scanned twice before it is loaded onto a van';
const w=frame(S=>tpl.sectionHead(S,9,{items:[{text:long,times:st(long,0,.05)}]}));
assert.ok(Math.abs(by(w)['head0-w0'].bounds.y+by(w)['head0-w0'].bounds.h/2-tpl.PAGE.headY)<1e-6);
assert.deepEqual(failed(frame(S=>tpl.sectionHead(S,1,{items,end:2.5}))),['fit-sectionHead']);
""")

    def test_part_openers_vary_by_part_and_validate_their_definition(self):
        self.node("""
assert.throws(()=>tpl.defineParts({}),/at least one part/);
assert.throws(()=>tpl.defineParts({I:{layout:'heroTop',motif:'columns'}}),/layout must be one of/);
assert.throws(()=>tpl.defineParts({I:{layout:'heroLeft',motif:'stripes'}}),/motif must be one of/);
assert.throws(()=>tpl.defineParts({I:{layout:'heroLeft',motif:'ledger'},II:{layout:'bad',motif:'grid'}}),/layout/);assert.ok(!('I' in tpl.PARTS),'no partial definition');
const P=tpl.defineParts({I:{name:'Arrivals',layout:'heroRight',motif:'columns'},II:{name:'Sorting',layout:'heroLeft',motif:'ledger'},
  III:{name:'Delivery',layout:'heroBelow',motif:'grid'},IV:{layout:'heroRight',motif:'form'},V:{layout:'heroLeft',motif:'calendar'}});
assert.equal(P,tpl.PARTS);assert.ok(Object.isFrozen(P.I));assert.throws(()=>tpl.defineParts({I:{layout:'heroLeft',motif:'ledger'}}),/already defined/);
assert.equal(tpl.partKey('Part II · Sorting'),'II');assert.equal(tpl.partKey('III'),'III');assert.throws(()=>tpl.partLayout('Part IX · Absent'),/Unknown part/);
const L1=tpl.partLayout('I'),L2=tpl.partLayout('Part II · Sorting'),L3=tpl.partLayout('III');
assert.ok(L1.hero.x>L1.title.x+L1.title.w&&L2.hero.x+L2.hero.w<L2.title.x&&L3.hero.y>L3.title.y,'each layout places the hero differently');
const moved=tpl.partLayout('I',{x:2040,y:1240});assert.deepEqual([moved.hero.x,moved.hero.y,moved.title.x],[L1.hero.x+1400,L1.hero.y+900,L1.title.x+1400]);
const title='How a parcel finds its depot',accent='Every scan moves it one step closer.';
for(const part of ['I','II','III','IV','V']) {
  const L=tpl.partLayout(part);let given=null;
  const open=(t,o={})=>frame(S=>tpl.partOpener(S,t,{part,lesson:3,title,accent,start:0,end:12,hero:(S,b)=>{given=b;},...o}));
  // Before the opener starts nothing but the (empty) hero is drawn; the motif then rules the hero box in hairline ink.
  assert.deepEqual(open(-1).items,[]);const hx=L.hero.x,hy=L.hero.y,hw=L.hero.w,hh=L.hero.h;const bare=share(hx,hy,hw,hh,T.rule,30);
  const r=open(10),b=by(r);assert.deepEqual(given,L.hero);assert.ok(share(hx,hy,hw,hh,T.rule,30)>bare+.0015,'motif in part '+part);
  assert.deepEqual(problems(r),[],'part '+part);assert.ok(b['po-kicker']);
  const tw=r.items.filter(i=>i.id.startsWith('po-title-w'));assert.equal(tw.length,6);
  for(const q of tw)assert.ok(q.bounds.x>=L.title.x-2&&q.bounds.x+q.bounds.w<=L.title.x+L.title.w+2,'title inside its column');
  assert.ok(b['po-accent-mark5']&&b['po-accent-w6'].owner==='po-accent-mark5','the last words take the highlighter');
  sweep('partOpener '+part,0,12,(S,t)=>tpl.partOpener(S,t,{part,lesson:3,title,accent,start:0,end:12}),{zooms:[1]});
}
// heroBelow keeps the title on one line; the others allow two before shrinking.
const one=by(frame(S=>tpl.partOpener(S,10,{part:'III',title,start:0,end:12})));assert.equal(new Set(Object.keys(one).filter(k=>k.startsWith('po-title-w')).map(k=>one[k].bounds.y)).size,1);
assert.deepEqual(failed(frame(S=>tpl.partOpener(S,1,{part:'I',title,start:0,end:3}))),['fit-partOpener']);
""")

    def test_every_template_has_a_minimum_span_and_short_spans_fail(self):
        self.node("""
for(const k of ['opener','partOpener','statement','compare','lineStory','stepper','question','sectionHead','readout','stateKey'])assert.ok(tpl.MIN_SPAN[k]>0,k);
const rows=[{key:'Planned',value:'4',y:300,at:1}];
assert.deepEqual(failed(frame(S=>tpl.readout(S,2,{x:800,rows,end:2}))),['fit-readout']);assert.deepEqual(failed(frame(S=>tpl.readout(S,2,{x:800,rows,end:9}))),[]);
assert.deepEqual(failed(frame(S=>tpl.stateKey(S,2,{x:100,y:500,items:[{state:'held',at:1}],end:2}))),['fit-stateKey']);
for(const name of ['opener','partOpener','sectionHead','readout','stateKey','question','progressRail','fictionBadge','defineParts','partLayout','partKey','PAGE','PARTS','PART_LAYOUTS','MOTIFS',
  'statement','carry','compare','lineStory','stepper'])assert.ok(name in tpl,name);
""")

    def test_existing_templates_meet_the_floors_edges_and_word_budget(self):
        self.node("""
// Demo-scale content, every output frame, held and under a slow push: no failed check, no collision.
const agenda=['1  Count the stock','2  Follow the parcel','3  Check the depot'];
for(const at of [{agenda:[4.6,5.5,6.4]},{}])sweep('opener',0,8.4,(S,t,v)=>v(()=>tpl.opener(S,t,{x:150,y:250,start:0,end:8.4,kicker:'Fictional demonstration',
  title:'Parcels move.',accent:"They don't vanish.",agenda,at})));
const claim='Two depots share one fixed stock of 150 parcels.';
sweep('statement',8.4,14.4,(S,t,v)=>v(()=>{const s=tpl.statement(S,t,{x:640,y:320,start:8.4,end:14.4,text:claim,emphasis:'150',times:st(claim,8.6,.3),exitAt:12.6});
  tpl.carry(S,t,{id:'carry-150',text:'150',from:[s.emphasis.x+s.emphasis.w/2,s.emphasis.y],to:[700,141],start:12.6,end:13.4,fromSize:s.emphasis.size});}));
sweep('compare',30.8,42.3,(S,t,v)=>v(()=>tpl.compare(S,t,{x:640,y:340,start:30.8,end:42.3,title:'Stock changed.',subtitle:'The total did not.',focusAt:37.5,
  left:{title:'Changed',dot:T.accent,rows:[{name:'Depot North',from:100,to:90},{name:'Depot South',from:50,to:60}]},
  right:{title:'Conserved',dot:T.teal,rows:[{name:'Total',from:150,to:150,check:true}]},takeaway:'Check the total before you trust the movement.',at:{left:[33,35],right:[36.5]}})));
for(const ends of [[85,65],[80,78]])sweep('lineStory',42.3,51.4,(S,t,v)=>v(()=>tpl.lineStory(S,t,{x:640,y:340,start:42.3,end:51.4,kicker:'Fictional series',
  title:'Four weeks later',labels:['Start','W1','W2','W3','W4'],focusAt:48,note:'flat while stock swings',invariant:{name:'Total 150',value:150},
  series:[{id:'a',name:'North',color:T.teal,values:[100,90,115,70,ends[0]]},{id:'b',name:'South',color:T.goldInk,values:[50,60,35,80,ends[1]]}],at:{series:[44,44.35],invariant:46.5}})));
sweep('stepper',51.4,60.9,(S,t,v)=>v(()=>tpl.stepper(S,t,{x:640,y:340,start:51.4,end:60.9,title:'Read any transfer',accent:'in three steps.',stepAt:[54,56.5,59],
  steps:[{title:'Count the stock',detail:'150 parcels'},{title:'Follow the moving parcel',detail:'10 in transit'},{title:'Check the depots',detail:'90 + 60 = 150'}]})),{zooms:[1,1.02]});
// Page furniture with a world under the camera: section head, readout, state key, rail and badge.
const head=[{text:'Stock by depot',times:st('Stock by depot',1,.2)},{text:'Then the vans leave',times:st('Then the vans leave',6,.2),marks:{3:6.8}}];
sweep('page',0,10,(S,t,v)=>{tpl.sectionHead(S,t,{ruleAt:.6,items:head,deck:{text:'Week 12',times:[1.5,1.7]}});
  v(()=>{tpl.readout(S,t,{x:800,width:340,cursor:420,rows:[{key:'Planned',value:'1,200',state:'planned',y:280,at:2},{key:'Shipped',value:'900',sub:'by Friday',state:'sent',y:390,at:3,mark:D.seg(t,6.8,.4)}]});
    tpl.stateKey(S,t,{x:120,y:520,items:[{state:'planned',at:4},{state:'shipped',at:4.3},{state:'held',at:4.6}]});});
  tpl.progressRail(S,t,{steps:['Count','Follow','Check'],at:[0,4,8],from:0,until:99,states:['planned','shipped','held']});tpl.fictionBadge(S,t,{from:0});},{zooms:[1,1.03]});
""")

    def test_templates_use_the_meaning_tokens(self):
        self.node("""
const strokes=[],stroke=g0.stroke.bind(g0);g0.stroke=(...a)=>{strokes.push(String(g0.strokeStyle).toUpperCase());return stroke(...a);};
// Compare strikes a replaced value in ink (it is not wrong) and checks a conserved row in T.good.
frame(S=>tpl.compare(S,20,{x:640,y:340,start:0,end:20,title:'Stock changed.',focusAt:15,left:{title:'Changed',rows:[{name:'North',from:100,to:90}]},
  right:{title:'Conserved',rows:[{name:'Total',from:150,to:150,check:true}]}}));
assert.ok(strokes.includes(T.ink)&&strokes.includes(T.good));assert.ok(!strokes.includes(T.accent)&&!strokes.includes(T.wrong));
// The statement's emphasis takes the signal highlighter.
const claim='One depot holds 150 parcels.',r=frame(S=>tpl.statement(S,9,{x:640,y:320,start:0,end:9,text:claim,emphasis:'150',times:st(claim,1,.3)}));
const m=by(r)['claim-mark3'].bounds;assert.ok(share(Math.ceil(m.x)+4,Math.ceil(m.y)+6,6,4,T.signal,60)>.8);
// No fill in a meaning colour from the stepper, in any frame: its travelling token is neutral ink
// (white on night) or the caller's course state, never the highlighter (gold equals signal).
const fills=[],fill=g0.fill.bind(g0),fillRect=g0.fillRect.bind(g0);
g0.fill=(...a)=>{fills.push(String(g0.fillStyle).toUpperCase());return fill(...a);};
g0.fillRect=(...a)=>{fills.push(String(g0.fillStyle).toUpperCase());return fillRect(...a);};
const up=a=>a.map(c=>c.toUpperCase()),highlighter=up([T.signal,T.signalSoft,T.gold,T.goldSoft]),meaning=up([...highlighter,T.wrong,T.wrongSoft,T.good,T.goodSoft,T.fiction]);
const steps=[{title:'Take the order',detail:'one recipe'},{title:'Cook the dish',detail:'two pans'},{title:'Plate it',detail:'one plate'}];
const step=(t,o={},background)=>frame(S=>tpl.stepper(S,t,{x:640,y:340,start:0,end:10,title:'Run the kitchen',accent:'in three steps.',stepAt:[3,5.5,7],steps,...o}),{background});
const centre=r=>{const b=by(r)['st-token'].bounds;return [Math.round(b.x+b.w/2)-2,Math.round(b.y+b.h/2)-2];};
for(const state of [null,'held','planned'])for(let f=0;f<=300;f+=3){fills.length=0;step(f/30,{state});
  assert.deepEqual(fills.filter(c=>meaning.includes(c)),[],`stepper ${state} t=${(f/30).toFixed(2)}`);}
let s=step(9),[cx,cy]=centre(s);assert.deepEqual([cx,cy],[628,474]);assert.ok(share(cx,cy,4,4,T.ink,12)>.9,'neutral ink token '+px(cx+2,cy+2));
assert.ok(share(cx-10,cy+1,2,2,T.paperHi,12)>.9,'paper ring '+px(cx-10,cy+1));
s=step(9,{},'night');assert.ok(share(cx,cy,4,4,T.white,12)>.9,'white token on night');
// A state draws the course's code: solid fills the disc; hatched strokes inside a dashed outline, never a solid fill.
step(9,{state:'held'});assert.ok(share(cx,cy,4,4,T.held,12)>.9);step(9,{state:'sent'});assert.ok(share(cx,cy,4,4,T.shipped,12)>.9,'aliases resolve');
fills.length=0;step(9,{state:'planned'});assert.ok(!fills.includes(T.planned.toUpperCase()));
assert.ok(share(cx-14,cy-14,32,32,T.planned,60)>.1&&share(cx-14,cy-14,32,32,T.paperHi,12)>.1,'hatched token');
assert.throws(()=>fresh(S=>tpl.stepper(S,9,{x:640,y:340,start:0,end:10,title:'Run',stepAt:[3,5.5,7],steps,state:'lost'})),/Unknown state: lost/);
// Templates without a highlighter never fill in the signal or gold, through their whole span.
const others=[t=>tpl.opener(S0(),t,{x:150,y:250,start:0,end:8,kicker:'Fictional demonstration',title:'Books move.',accent:'They come back.',agenda:['Lend','Return']}),
  t=>tpl.compare(S0(),t,{x:640,y:340,start:0,end:12,title:'Shelves changed.',focusAt:8,left:{title:'Changed',rows:[{name:'Shelf A',from:40,to:30}]},right:{title:'Kept',rows:[{name:'Total',from:70,to:70,check:true}]},takeaway:'Count the total.'}),
  t=>tpl.lineStory(S0(),t,{x:640,y:340,start:0,end:9,title:'Four weeks',labels:['W0','W1','W2'],focusAt:6,series:[{id:'a',name:'A',color:T.teal,values:[4,6,5]}]}),
  t=>tpl.readout(S0(),t,{x:820,width:360,rows:[{key:'Planned',value:'12',state:'planned',y:300,at:1}]}),
  t=>tpl.stateKey(S0(),t,{x:100,y:520,items:[{state:'planned',at:1},{state:'held',at:2}]}),
  t=>{const S=S0();tpl.progressRail(S,t,{steps:['Lend','Return','Shelve'],at:[0,3,6],from:0,until:99,states:['planned','held','shipped']});tpl.fictionBadge(S,t,{from:0});}];
let cur=null;const S0=()=>cur;
others.forEach((draw,i)=>{for(let t=0;t<=12;t+=.5){fills.length=0;frame(S=>{cur=S;draw(t);});assert.deepEqual(fills.filter(c=>highlighter.includes(c)),[],`template ${i} t=${t}`);}});
""")

    def test_top_band_fails_a_rail_that_runs_under_the_badge_or_off_the_frame(self):
        self.node("""
// Tracked chrome capitals make the rail wide. A neutral five-step agenda ends under the badge; the
// audit hears it through rail-badge, whichever of the two is drawn first.
const five=['Know the queue','Triage a ticket','Escalate safely','Close the loop','Measure the backlog'],at=[0,4,8,12,16,20];
const band=(steps,{badge={from:0},first=false,t=5,background}={})=>{let rail=null,box=null;
  const r=frame(S=>{if(badge&&first)box=tpl.fictionBadge(S,t,badge);rail=tpl.progressRail(S,t,{steps,at:at.slice(0,steps.length),from:0,until:99});
    if(badge&&!first)box=tpl.fictionBadge(S,t,badge);},{background});return {r,rail,box};};
const checks=r=>r.invariants.checks.filter(c=>/^rail-/.test(c.id)).map(c=>c.id).sort();
let {r,rail,box}=band(five);
assert.ok(rail.x+rail.w>box.x-20);assert.deepEqual(failed(r),['rail-badge']);assert.deepEqual(checks(r),['rail-badge','rail-fit']);
assert.deepEqual(failed(band(five,{first:true}).r),['rail-badge']);
// Without the badge, or while it is off, the same rail fits the frame and no rail-badge check runs.
for(const b of [null,{windows:[[20,30]]}]){r=band(five,{badge:b}).r;assert.deepEqual(failed(r),[]);assert.deepEqual(checks(r),['rail-fit']);}
// A sixth step runs the rail off the frame: rail-fit fails with no badge at all.
assert.deepEqual(failed(band([...five,'Report the week'],{badge:null}).r),['rail-fit']);
// A short agenda fits beside the badge; the returned box is the painted extent of the rail.
const short=['Arrive','Sort','Ship'];({r,rail,box}=band(short));assert.deepEqual(failed(r),[]);assert.ok(rail.x+rail.w+20<=box.x);
const ws=short.map(s=>measure(s,'chrome')+16);assert.equal(rail.x,32);assert.ok(Math.abs(rail.x+rail.w-(32+ws[0]+ws[1]+ws[2]+2*18))<1e-6);
frame(()=>{});const empty=g0.getImageData(0,20,1280,50).data;band(short,{badge:null});const drawn=g0.getImageData(0,20,1280,50).data;
let last=-1;for(let i=0;i<drawn.length;i+=4)if(Math.abs(drawn[i]-empty[i])+Math.abs(drawn[i+1]-empty[i+1])+Math.abs(drawn[i+2]-empty[i+2])>30)last=Math.max(last,(i/4)%1280);
assert.ok(Math.abs(last+1-(rail.x+rail.w))<=1.5,'painted to '+last+', box ends at '+(rail.x+rail.w));
// Hidden (a night stage): no box and no rail checks.
const n=band(five,{background:'night'});assert.equal(n.rail,null);assert.deepEqual(checks(n.r),[]);
""")


if __name__ == '__main__':
    unittest.main()
