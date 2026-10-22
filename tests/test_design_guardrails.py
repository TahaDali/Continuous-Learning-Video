"""Design-system guardrails: leak-free grain, full-frame transitions, text checks, cues and helpers."""
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parent.parent
PRODUCTION = ROOT / 'assets/starter/production-source'

# A stage on a fresh 1280x720 canvas; snippets append their own assertions.
STAGE = """
const assert=require('node:assert/strict'),canvas=require(process.env.CANVAS_MODULE),D=require('./design.cjs');
D.installDesignRuntime(canvas);
const course={width:1280,height:720},stage=(opts)=>{const c=canvas.createCanvas(1280,720),g=c.getContext('2d');return {c,g,S:D.createDesignStage(g,course,opts)};};
const px=(g,x,y)=>Array.from(g.getImageData(x,y,1,1).data);
const failed=r=>r.invariants.checks.filter(c=>!c.passed).map(c=>c.id);
"""


class DesignGuardrailTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which('node'):
            self.skipTest('Node.js is required')

    def canvas_environment(self):
        module = os.environ.get('CANVAS_MODULE') or str(PRODUCTION / 'node_modules/@napi-rs/canvas')
        if not Path(module).is_dir():
            self.skipTest('Canvas runtime is not configured')
        return dict(os.environ, CANVAS_MODULE=module)

    def node(self, code, canvas=False):
        env = self.canvas_environment() if canvas else dict(os.environ)
        result = subprocess.run(['node', '-e', (STAGE if canvas else '') + code], cwd=PRODUCTION, env=env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        return result

    def test_grain_is_drawn_from_a_decoded_image_not_a_canvas(self):
        self.node("""
const drawn=[];
const instrument=g=>{const draw=g.drawImage.bind(g);g.drawImage=(img,...a)=>{drawn.push(img instanceof canvas.Image?'image':'canvas');return draw(img,...a);};return g;};
const frame=()=>{const c=canvas.createCanvas(1280,720),g=instrument(c.getContext('2d'));D.createDesignStage(g,course).finish();return g;};
// Before the asynchronous decode lands, a bounded number of paints use the pixel-identical canvas.
const early=frame(),before=early.getImageData(0,0,1280,720).data;
for(let i=0;i<150;i++)frame();
const fallback=drawn.filter(x=>x==='canvas').length;
assert.ok(fallback>=1&&fallback<=64,'bounded fallback, got '+fallback);
(async()=>{
  for(let i=0;i<100&&!drawn.slice(-1).includes('image');i++){await new Promise(r=>setTimeout(r,50));drawn.length=0;frame();}
  drawn.length=0;let late;for(let i=0;i<20;i++)late=frame();
  assert.equal(drawn.length,20);assert.ok(drawn.every(x=>x==='image'),drawn.join());
  // The decoded Image and the early canvas paint produce identical pixels.
  assert.deepEqual(Buffer.from(late.getImageData(0,0,1280,720).data),Buffer.from(before));
})().catch(e=>{console.error(e);process.exitCode=1;});
""", canvas=True)

    def test_iris_and_wipe_paint_the_full_frame_and_clip_only_the_next_scene(self):
        self.node("""
const magenta=([r,g,b])=>r>240&&g<20&&b>240,dark=([r,g,b])=>r+g+b<160,light=([r,g,b])=>r+g+b>600;
const fill=S=>()=>{S.g.save();S.g.setTransform(1,0,0,1,0,0);S.g.fillStyle='#FF00FF';S.g.fillRect(0,0,1280,720);S.g.restore();};
// Phase one: the accent disc covers a corner far outside the content viewport.
let {g,S}=stage();S.transition(()=>S.iris(640,340,.5,()=>{}));S.finish();
const [r,gr,b]=px(g,4,4);assert.ok(r>200&&gr<110&&b<80,'accent corner '+[r,gr,b]);
// Phase two: the next background is painted full-frame; the next scene stays inside the viewport.
({g,S}=stage());S.transition(()=>S.iris(640,340,1,fill(S),{mode:'night'}));S.finish();
assert.ok(dark(px(g,4,4))&&dark(px(g,1275,715)),'night corners');assert.ok(magenta(px(g,640,340)));assert.ok(!magenta(px(g,4,4))&&!magenta(px(g,640,700)));
({g,S}=stage());S.transition(()=>S.wipe(.5,fill(S),{mode:'night'}));S.finish();
assert.ok(dark(px(g,1275,4))&&dark(px(g,1275,715)),'wipe paints outside the viewport');assert.ok(light(px(g,4,715)),'not yet wiped');
assert.ok(magenta(px(g,1200,340))&&!magenta(px(g,1275,340))&&!magenta(px(g,1200,700)));
({g,S}=stage());S.transition(()=>S.wipe(1,fill(S),{mode:'night'}));S.finish();assert.ok(dark(px(g,4,4))&&dark(px(g,4,715)));
// The demo's explicit S.unclipped(() => S.iris(...)) nests safely: the next frame paints full-frame again.
const c=canvas.createCanvas(1280,720),h=c.getContext('2d');let T=D.createDesignStage(h,course);
T.transition(()=>T.unclipped(()=>T.iris(640,340,1,()=>{},{mode:'night'})));T.finish();assert.ok(dark(px(h,4,4)));
T=D.createDesignStage(h,course);T.finish();assert.ok(light(px(h,4,4)),'no clip leaks into the next frame');
""", canvas=True)

    def test_roles_respect_tier_floors_and_the_type_check_reads_screen_size(self):
        self.node("""
assert.deepEqual(D.FLOOR,{content:28,tertiary:24,chrome:18});
assert.equal(D.role('label',{size:12}).size,28);assert.equal(D.role('small',{size:10}).size,24);assert.equal(D.role('chrome').size,18);
assert.equal(D.role('chrome').chrome,true);assert.equal(D.role('label',{tier:'chrome'}).chrome,true);
for(const [name,size,tier] of [['kicker',24,'tertiary'],['label',28,undefined],['small',24,'tertiary'],['mono',28,undefined],['monoSm',24,'tertiary'],['accentSm',28,undefined]])
  {assert.equal(D.TYPE[name].size,size,name);assert.equal(D.TYPE[name].tier,tier,name);}
for(const [name,r] of Object.entries(D.TYPE))assert.ok(r.size>=D.floorOf(r),name);
let {S}=stage();S.view({x:640,y:340,zoom:.5},()=>S.text('tiny','Tiny',640,300,{role:'label'}));
S.text('floor','Floor',300,300,{role:'label'});S.text('tert','Unit',300,400,{role:'small'});S.label('rail','Rail',300,200,{tier:'chrome'});
S.view({x:640,y:340,zoom:.9},()=>S.text('tick','Tick',640,450,{role:'small'}));
S.view({x:640,y:340,zoom:.5},()=>S.fade(.5,()=>S.text('faint','Faint',800,300,{role:'label'})));
let r=S.finish();assert.deepEqual(failed(r).sort(),['type-tick','type-tiny']);
assert.equal(r.invariants.checks.find(c=>c.id==='type-tiny').actual,14);
// A label motion-compatible caller may mark tertiary text; the floor follows the tier.
({S}=stage());S.label('id','A-17',400,300,{size:12,tier:'tertiary'});r=S.finish();
assert.ok(Math.abs(r.items[0].bounds.h-24*1.24)<1e-6);assert.deepEqual(failed(r),[]);
// Transition frames are exempt.
({S}=stage());S.transition(()=>S.view({x:640,y:340,zoom:.5},()=>S.text('pan','Pan',640,300,{role:'label'})));r=S.finish();
assert.deepEqual(failed(r),[]);assert.equal(r.transition,true);
""", canvas=True)

    def test_edge_guard_fades_labels_at_the_frame_edge_and_fails_outside_transitions(self):
        self.node("""
let {S}=stage();
S.text('inside','Inside',400,300);S.text('near','Near',46,300);S.text('cut','Cut',30,300);S.label('chrome','Rail',60,58,{tier:'chrome'});
let r=S.finish(),alpha=Object.fromEntries(r.items.map(i=>[i.id,i.alpha]));
assert.equal(alpha.inside,1);assert.ok(alpha.near>0&&alpha.near<1,'faded '+alpha.near);assert.equal(alpha.cut,0);assert.equal(alpha.chrome,1);
assert.deepEqual(failed(r).sort(),['edge-cut','edge-near']);
// A camera push that carries a label to the edge fails outside a transition and not inside one.
const push=S=>S.view({x:640,y:340,zoom:1.6},()=>S.text('pushed','Pushed',980,340));
({S}=stage());push(S);assert.deepEqual(failed(S.finish()),['edge-pushed']);
({S}=stage());S.transition(()=>push(S));r=S.finish();assert.deepEqual(failed(r),[]);
// onScreen reports a world box's visibility under the current camera.
({S}=stage());assert.equal(S.onScreen({x:600,y:300,w:50,h:20}),1);assert.equal(S.onScreen({x:-100,y:300,w:50,h:20}),0);
S.view({x:640,y:340,zoom:2},()=>{assert.equal(S.onScreen({x:900,y:300,w:40,h:20}),0);assert.equal(S.onScreen({x:640,y:330,w:40,h:20}),1);
  const k=S.onScreen({x:915,y:330,w:10,h:10},{margin:40});assert.ok(k>0&&k<1,String(k));});
S.finish();
""", canvas=True)

    def test_edge_guard_reports_text_it_hides_outside_the_content_area(self):
        self.node("""
const band=(S,id,y,opts)=>S.unclipped(()=>{S.g.save();S.g.setTransform(1,0,0,1,0,0);S.text(id,'Lesson 3 of 8',40,y,opts);S.g.restore();});
// Unclipped non-chrome text in the top or caption band is hidden by the guard and fails, decor or not.
let {S}=stage();S.decor(()=>band(S,'top',58,{role:'small'}));band(S,'cap',650,{role:'label'});S.decor(()=>band(S,'rail',58,{role:'chrome'}));
let r=S.finish();assert.deepEqual(failed(r).sort(),['edge-cap','edge-top']);
assert.equal(r.invariants.checks.find(c=>c.id==='edge-top').expected,'chrome role for text outside the content area');
assert.equal(r.items.find(i=>i.id==='cap').alpha,0);
// Clipped text outside the viewport is invisible either way, and a transition's next scene is clipped again.
({S}=stage());S.text('off','Off camera',640,680);S.view({x:2000,y:340,zoom:1},()=>S.text('far','Far',640,340));
S.unclipped(()=>S.iris(640,340,1,()=>S.text('below','Below',640,680)));r=S.finish();assert.deepEqual(failed(r),[]);
({S}=stage());S.transition(()=>band(S,'moving',58,{role:'label'}));assert.deepEqual(failed(S.finish()),[]);
""", canvas=True)

    def test_transitions_refuse_to_pop_a_camera_alpha_or_actor_state(self):
        self.node("""
const cam={x:640,y:340,zoom:1.5},box={x:600,y:300,w:80,h:80};
const misuses=[S=>S.view(cam,()=>S.transition(()=>S.iris(640,340,.5,()=>{}))),S=>S.fade(.5,()=>S.transition(()=>S.wipe(.5,()=>{}))),
  S=>S.actor('a',{x:0,y:0,w:10,h:10},()=>S.unclipped(()=>{})),S=>D.world(S,0,[{t:0,x:640,y:340,zoom:1.2}],()=>S.iris(640,340,.5,()=>{}))];
for(const misuse of misuses) {
  const {S}=stage();assert.throws(()=>misuse(S),/must be called at the top level of a frame/);
  // The save stack stays balanced: later drawing keeps the identity camera.
  S.actor('after',box,()=>{});assert.deepEqual(S.finish().items.find(i=>i.id==='after').bounds,box);
}
// Inside an unclipped region, view() and nested unclipped calls keep the camera.
let {S}=stage();S.unclipped(()=>S.view(cam,()=>{S.unclipped(()=>{});S.actor('box',box,()=>{});}));
assert.deepEqual(S.finish().items[0].bounds,{x:580,y:280,w:120,h:120});
// A top-level transition leaves the camera of a later view intact.
({S}=stage());S.transition(()=>S.iris(640,340,.5,()=>{}));S.view(cam,()=>S.fade(.5,()=>S.actor('box',box,()=>{})));
const item=S.finish().items[0];assert.deepEqual(item.bounds,{x:580,y:280,w:120,h:120});assert.ok(Math.abs(item.alpha-.5)<.01,String(item.alpha));
""", canvas=True)

    def test_word_budget_counts_visible_content_words(self):
        self.node("""
const grid=(S,n,opts={})=>{for(let i=0;i<n;i++)S.text('w'+i,'word',120+(i%6)*170,140+Math.floor(i/6)*80,opts);};
let {S}=stage();grid(S,24);let r=S.finish();assert.equal(r.words,24);assert.deepEqual(failed(r),[]);
({S}=stage());grid(S,25);r=S.finish();assert.deepEqual(failed(r),['words']);assert.equal(r.invariants.checks.find(c=>c.id==='words').actual,25);
({S}=stage());grid(S,24);S.label('rail','Rail words here',300,58,{tier:'chrome'});S.fade(.3,()=>S.text('ghost','faded words',300,500));
S.decor(()=>S.text('decor','decor words',700,500));r=S.finish();assert.equal(r.words,26);
({S}=stage());S.transition(()=>grid(S,30));r=S.finish();assert.ok(!r.invariants.checks.some(c=>c.id==='words'));
assert.equal(D.WORD_BUDGET,24);assert.equal(D.EDGE,12);
// Words count in any script; scripts written without spaces count their word segments.
({S}=stage());for(let i=0;i<25;i++)S.text('c'+i,i%2?'книга':'ράφι',120+(i%6)*170,140+Math.floor(i/6)*80);
r=S.finish();assert.equal(r.words,25);assert.deepEqual(failed(r),['words']);
({S}=stage());S.sentence('s','Посылка едет на склад, склад закрыт до утра',100,300,{t:99,times:Array(8).fill(0),role:'label',maxWidth:1000});
assert.equal(S.finish().words,8);
({S}=stage());S.text('ja','本は明日棚に戻ります',300,300);r=S.finish();assert.ok(r.words>=4,'unspaced words '+r.words);
({S}=stage());S.text('sym','→ — & · 100% $5 café',300,300);assert.equal(S.finish().words,3);
""", canvas=True)

    def test_ambiguous_cues_throw_until_nth_is_given(self):
        self.node("""
const assert=require('node:assert/strict'),{createCues,wordTimes}=require('./design.cjs');
const text='Ten books leave. Then ten books return.',words=text.split(' ');
const wordTimings=words.map((w,i)=>({text:w.replace(/[.,]/g,''),start:10+i,end:10.5+i}));
const lesson={scenes:[{id:'lend',narration:text,start:9,end:30,wordTimings},
  {id:'plain',narration:'Shelve the book, then lend the book.',start:40,end:44,speechStart:40.2,speechEnd:43.5}]};
const cue=createCues(lesson);
assert.throws(()=>cue('lend','ten'),/Ambiguous narration cue: scene lend "ten" is spoken 2 times; pass nth \\(1\\.\\.2\\)/);
assert.throws(()=>cue('plain','book'),/Ambiguous narration cue: scene plain "book" is spoken 2 times/);
assert.equal(cue('lend','ten',1),10);assert.equal(cue('lend','TEN',2),14);assert.equal(cue('lend','leave'),12);
assert.throws(()=>cue('lend','vanish'),/Missing narration cue/);assert.throws(()=>cue('lend','ten',3),/Missing narration cue/);
assert.equal(cue.count('lend','books'),2);assert.equal(cue.count('lend','absent'),0);assert.equal(cue.count('plain','lend'),1);
assert.equal(cue.end('lend','leave'),12.5);assert.equal(cue.end('lend','return',1),16.5);
assert.throws(()=>cue.end('lend','ten'),/Ambiguous narration cue/);
// Estimated cues: onsets are unchanged and a word ends where the next one starts.
const est=wordTimes('Shelve the book, then lend the book.'.split(' '),lesson.scenes[1]).times;
assert.equal(cue('plain','shelve'),est[0]);assert.equal(cue('plain','book',2),est[6]);assert.equal(cue.end('plain','lend'),est[5]);
assert.equal(cue.end('plain','book',2),43.5);assert.equal(cue.method('plain'),'estimated');
""")

    def test_cues_match_words_in_any_script(self):
        self.node("""
const assert=require('node:assert/strict'),{createCues,wordTimes}=require('./design.cjs');
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,a+' != '+b);
const greek='Το βιβλίο επιστρέφει στο ράφι αύριο. Το ράφι είναι γεμάτο.';
const wordTimings=[{text:'Посылка',start:10,end:10.6},{text:'едет',start:10.7,end:11},{text:'на склад.',start:11.1,end:11.9},
  {text:'Склад',start:12.5,end:13},{text:'закрыт.',start:13.1,end:13.7}];
const lesson={scenes:[{id:'g',narration:greek,start:0,end:10,speechStart:.2,speechEnd:9.5},
  {id:'c',narration:'Посылка едет на склад. Склад закрыт.',start:10,end:14,wordTimings},
  {id:'f',narration:'Le café ferme. Le caf rouvre.',start:20,end:24}]};
const cue=createCues(lesson),est=wordTimes(greek.split(' '),lesson.scenes[0]).times;
// Estimated Greek narration: each word is its own cue; a repeated word needs nth.
assert.equal(cue('g','βιβλίο'),est[1]);assert.equal(cue('g','ΑΎΡΙΟ'),est[5]);assert.equal(cue('g','βιβλίο'.normalize('NFD')),est[1]);
assert.throws(()=>cue('g','ράφι'),/Ambiguous narration cue: scene g "ράφι" is spoken 2 times; pass nth \\(1\\.\\.2\\)/);
assert.equal(cue('g','ράφι',2),est[7]);assert.equal(cue('g','το',2),est[6]);
assert.equal(cue.count('g','ράφι'),2);assert.equal(cue.count('g','αύριο'),1);assert.equal(cue.count('g','βιβλίο'),1);
assert.equal(cue.end('g','αύριο'),est[6]);assert.equal(cue.end('g','ράφι',1),est[5]);
assert.throws(()=>cue('g','σκύλος'),/Missing narration cue/);assert.throws(()=>cue('g','—'),/Missing narration cue/);assert.equal(cue.count('g','—'),0);
assert.deepEqual(cue.phrase('g','Το ράφι',{after:est[5]}),[est[6],est[7]]);
// Measured Cyrillic events, one of them covering two spoken words.
assert.throws(()=>cue('c','склад'),/spoken 2 times/);assert.equal(cue.count('c','СКЛАД'),2);assert.equal(cue('c','на'),11.1);
near(cue('c','склад',1),11.1+.8*3/9);near(cue.end('c','склад',1),11.9);assert.equal(cue('c','склад',2),12.5);assert.equal(cue.end('c','склад',2),13);
assert.throws(()=>cue('c','собака'),/Missing narration cue/);
// Accented Latin words stay distinct from their unaccented neighbours.
assert.equal(cue.count('f','café'),1);assert.equal(cue.count('f','caf'),1);assert.equal(cue.count('f','le'),2);assert.ok(cue('f','café')<cue('f','caf'));
""")

    def test_provider_events_covering_several_words_are_split(self):
        self.node("""
const assert=require('node:assert/strict'),{createCues}=require('./design.cjs');
const wordTimings=[{text:'Opened',start:1,end:1.4},{text:'in 2015',start:1.5,end:2.2},{text:'with',start:2.3,end:2.5},
  {text:'15,000 parcels.',start:2.6,end:3.6}];
const cue=createCues({scenes:[{id:'depot',narration:'Opened in 2015 with 15,000 parcels.',start:0,end:4,wordTimings}]});
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,a+' != '+b);
assert.equal(cue('depot','in'),1.5);near(cue('depot','2015'),1.5+.7*3/7);near(cue.end('depot','in'),1.5+.7*2/7);near(cue.end('depot','2015'),2.2);
assert.equal(cue('depot','15000'),2.6);near(cue('depot','parcels'),2.6+1*7/15);near(cue.end('depot','parcels'),3.6);
assert.deepEqual(cue.phrase('depot','in 2015').map(x=>+x.toFixed(6)),[1.5,1.8]);assert.equal(cue.count('depot','with'),1);
""")

    def test_state_code_validation_aliases_and_drawing(self):
        self.node("""
const T=D.T;
assert.throws(()=>D.stateOf('planned'),/Unknown state/);
assert.throws(()=>D.defineStates({}),/at least one state/);
assert.throws(()=>D.defineStates({teal:{color:'#123456'}}),/Theme token already exists: teal/);
assert.throws(()=>D.defineStates({held:{color:'red'}}),/#rrggbb/);
assert.throws(()=>D.defineStates({held:{color:T.signal.toLowerCase()}}),/meaning colour signal/);
for(const k of ['wrong','good','fiction'])assert.throws(()=>D.defineStates({held:{color:T[k]}}),new RegExp('meaning colour '+k));
assert.throws(()=>D.defineStates({held:{color:'#123456',treatment:'dotted'}}),/solid or hatched/);
assert.throws(()=>D.defineStates({'Bad-name':{color:'#123456'}}),/Invalid state name/);
assert.throws(()=>D.defineStates({held:{color:'#123456'}},{aliases:{kept:'absent'}}),/unknown state/);
// A rejected call leaves no partial state code behind.
assert.throws(()=>D.defineStates({ok:{color:'#123456'},bad:{color:'nope'}}),/#rrggbb/);assert.ok(!('ok' in T)&&!('ok' in D.STATES));
// States that look the same (colour and treatment) cannot be told apart on screen.
assert.throws(()=>D.defineStates({aa:{color:'#111111'},bb:{color:'#111111'}}),/State bb looks the same as aa/);assert.ok(!('aa' in D.STATES));
const states=D.defineStates({planned:{color:'#2350C8',label:'Planned',treatment:'hatched'},shipped:{color:'#13A0B0',label:'Shipped'}},{aliases:{sent:'shipped'}});
assert.throws(()=>D.defineStates({held:{color:'#2350c8',treatment:'hatched'}}),/State held looks the same as planned/);
D.defineStates({reserved:{color:'#2350C8'}});assert.equal(D.STATES.reserved.treatment,'solid');
assert.equal(states,D.STATES);assert.equal(T.planned,'#2350C8');assert.match(T.plannedSoft,/^#[0-9A-F]{6}$/);assert.notEqual(T.plannedSoft,T.planned);
assert.equal(D.STATES.planned.treatment,'hatched');assert.equal(D.STATES.shipped.treatment,'solid');assert.equal(D.STATES.shipped.label,'Shipped');
assert.ok(Object.isFrozen(D.STATES.shipped));
assert.equal(D.stateOf('sent'),'shipped');assert.equal(D.stateOf('planned'),'planned');assert.throws(()=>D.stateOf('lost'),/Unknown state: lost/);
assert.throws(()=>D.defineStates({planned:{color:'#445566'}}),/Theme token already exists|already defined/);
assert.throws(()=>D.defineStates({late:{color:'#445566'}},{aliases:{sent:'late'}}),/duplicate state alias/);
assert.throws(()=>D.extendTheme({shippedSoft:'#000000'}),/already exists/);
// Solid states fill; hatched states never fill solid. Both register when given an id.
const {g,S}=stage();S.stateBox('solid','sent',200,200,200,100);S.stateBox('hatched','planned',500,200,200,100);
S.swatch('sw','shipped',800,250);S.stateBox(null,'planned',900,200,100,100);const r=S.finish();
assert.deepEqual(r.items.map(i=>i.id),['solid','hatched','sw']);
const count=(x,y,w,h,[R,G,B])=>{const d=g.getImageData(x,y,w,h).data;let n=0;for(let i=0;i<d.length;i+=4)if(Math.abs(d[i]-R)+Math.abs(d[i+1]-G)+Math.abs(d[i+2]-B)<12)n++;return n/(w*h);};
const rgb=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
assert.ok(count(220,220,160,60,rgb(T.shipped))>.95);assert.ok(count(520,220,160,60,rgb(T.planned))<.5);
assert.equal(stage({background:'night'}).S.night,true);assert.equal(stage().S.night,false);
""", canvas=True)

    def test_fit_camera_frames_a_box_inside_the_content_band(self):
        self.node("""
const assert=require('node:assert/strict'),{fitCamera}=require('./design.cjs');
const screen=(cam,x,y)=>[640+(x-cam.x)*cam.zoom,340+(y-cam.y)*cam.zoom];
for(const [box,opts] of [[{x:100,y:100,w:400,h:200},{}],[{x:2000,y:900,w:900,h:250},{}],[{x:0,y:0,w:300,h:300},{maxZoom:1.2,top:190,bottom:586}],[{x:-50,y:40,w:3000,h:900},{}]]) {
  const o={top:196,bottom:574,left:54,right:1226,maxZoom:1.6,minZoom:1,...opts},cam=fitCamera(box,opts);
  const z=Math.max(o.minZoom,Math.min(o.maxZoom,(o.right-o.left)/box.w,(o.bottom-o.top)/box.h));assert.ok(Math.abs(cam.zoom-z)<1e-9);
  const [cx,cy]=screen(cam,box.x+box.w/2,box.y+box.h/2);assert.ok(Math.abs(cx-(o.left+o.right)/2)<1e-6&&Math.abs(cy-(o.top+o.bottom)/2)<1e-6);
  const [x0,y0]=screen(cam,box.x,box.y),[x1,y1]=screen(cam,box.x+box.w,box.y+box.h);
  if(cam.zoom>o.minZoom)assert.ok(x0>=o.left-1e-6&&x1<=o.right+1e-6&&y0>=o.top-1e-6&&y1<=o.bottom+1e-6,JSON.stringify([x0,y0,x1,y1]));
}
assert.equal(fitCamera({x:100,y:100,w:400,h:200}).zoom,1.6);assert.equal(fitCamera({x:0,y:0,w:3000,h:900}).zoom,1);
""")

    def test_spoken_numbers_never_show_an_unsaid_value(self):
        self.node("""
const assert=require('node:assert/strict'),{spoken,niceStep,stepValue}=require('./design.cjs');
assert.equal(niceStep(72000),1000);assert.equal(niceStep(150),10);assert.equal(niceStep(-150),10);assert.equal(niceStep(0),1);assert.equal(niceStep(12),1);
const times=[10,10.5,11.2];
for(const [value,from,step] of [[72000,0,undefined],[150,0,undefined],[73,0,10],[40,100,undefined]]) {
  const s=step||niceStep(value-from),seen=[];
  for(let t=8;t<=13;t+=1/48) {
    const w=spoken(t,value,times),l=spoken(t,value,times,{mode:'land'}),c=spoken(t,value,times,{mode:'count',from,step});
    assert.equal(w,t>=10?value:null);assert.equal(l,t>=11.2?value:null);
    if(t<10)assert.equal(c,null);else{assert.ok(c===value||Math.abs((c-from)/s-Math.round((c-from)/s))<1e-9,'off-step '+c);seen.push(c);}
    if(t>=11.2)assert.equal(c,value);
  }
  for(let i=1;i<seen.length;i++)assert.ok(Math.sign(value-from)*(seen[i]-seen[i-1])>=0,'monotonic');
}
assert.equal(spoken(9.8,5,[10],{lead:.25}),5);assert.equal(stepValue(5,{value:30,start:6,end:8,step:10}),0);
""")

    def test_before_push_and_focus_helper_shapes(self):
        self.node("""
const assert=require('node:assert/strict'),{beforePush,talking,focusOf}=require('./design.cjs');
const f=t=>beforePush(t,[10,12]),near=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,a+' != '+b);
assert.equal(f(9),1);near(f(9.7),1);near(f(10),0);assert.equal(f(11),0);near(f(12),0);near(f(12.3),1);assert.equal(f(14),1);
assert.ok(f(9.85)>0&&f(9.85)<1&&f(12.15)>0&&f(12.15)<1);
for(let t=9.7;t<10;t+=.01)assert.ok(f(t+.01)<=f(t)+1e-12);for(let t=12;t<12.3;t+=.01)assert.ok(f(t+.01)>=f(t)-1e-12);
assert.equal(beforePush(9.5,[10,12],{d:.6})<1,true);
assert.equal(talking(0,1,3),0);assert.equal(talking(2,1,3),1);assert.equal(talking(4,1,3),0);
const spk=[{from:1,to:2},{from:3,to:4}];
assert.equal(focusOf(0,spk,0),0);assert.equal(focusOf(2,spk,0),1);assert.ok(Math.abs(focusOf(5,spk,0)-.3)<1e-9);assert.equal(focusOf(5,spk,1),1);
assert.equal(focusOf(9,spk,0,{all:8}),1);assert.equal(focusOf(2,spk,1),0);
""")

    def test_camera_world_planner_and_ordered_keys(self):
        self.node("""
const keys=D.orderKeys([{t:0,x:640,y:340,zoom:1},{t:2,x:1640,y:340,zoom:1},{t:1.9,x:1640,y:340,zoom:1.05}]);
assert.ok(keys[2].t>keys[1].t);
let {S}=stage();const cam=D.world(S,1,keys,()=>S.text('moving','Moving',1640,340),{pans:[[0,2]]});
assert.ok(cam.speed>0);let r=S.finish();assert.equal(r.transition,true);assert.deepEqual(r.items,[]);
({S}=stage());D.world(S,5,keys,()=>S.text('held','Held',1640,340,{align:'center'}),{pans:[[0,2]]});r=S.finish();
assert.equal(r.transition,false);assert.equal(r.items[0].id,'held');assert.ok(Math.abs(r.items[0].bounds.x+r.items[0].bounds.w/2-640)<3);
let builds=0;const plan=D.planner(({cue,sc,win})=>{builds++;return {leave:cue('s','leave'),win:win(sc.s)};});
const lesson={scenes:[{id:'s',narration:'Parcels leave the depot.',start:2,end:6,speechStart:2.2,speechEnd:5.5}]};
assert.equal(plan(lesson),plan(lesson));assert.equal(builds,1);assert.ok(Math.abs(plan(lesson).win[0]-1.7)<1e-9&&Math.abs(plan(lesson).win[1]-2.7)<1e-9);assert.ok(plan(lesson).leave>2.2);
plan({...lesson});assert.equal(builds,2);
""", canvas=True)

    def test_callout_marked_text_and_highlighter_runs(self):
        self.node("""
D.defineStates({lent:{color:'#2350C8'}});
let {g,S}=stage({background:'night'});
const box=S.callout('due','Due',12,300,250,{mark:1,state:'lent'});
const stack=S.callout('st','Shelf','A-4',700,250,{layout:'stack'});
const m=S.markText('mk','On loan',300,420,{p:1,color:S.T.white,role:'title'});
S.sentence('s','one two three four',600,420,{t:10,times:[0,0,0,0],role:'title',styles:{1:{mark:{p:1}},2:{mark:{p:1}}}});
let r=S.finish();const by=Object.fromEntries(r.items.map(i=>[i.id,i]));
assert.deepEqual(Object.keys(by),['due-sw','due-k','due-mk','due-v','st-k','st-v','mk-mk','mk','s-mark1','s-w0','s-w1','s-w2','s-w3']);
assert.equal(by['due-v'].owner,'due-mk');assert.equal(by.mk.owner,'mk-mk');assert.equal(by['s-w1'].owner,'s-mark1');assert.equal(by['s-w2'].owner,'s-mark1');assert.equal(by['s-w3'].owner,null);
assert.ok(box.value.x>box.x&&box.value.x+box.value.w<=box.x+box.w+1e-6);assert.ok(stack.value.y>250);
assert.ok(by['st-v'].bounds.y>=by['st-k'].bounds.y+by['st-k'].bounds.h-1);
const inside=(a,b)=>a.x>=b.x&&a.y>=b.y&&a.x+a.w<=b.x+b.w&&a.y+a.h<=b.y+b.h;
assert.ok(inside(by.mk.bounds,by['mk-mk'].bounds)&&inside(by['s-w2'].bounds,by['s-mark1'].bounds));
// The ink copy under the sweep is not counted twice.
assert.equal(r.words,1+1+1+1+2+4);assert.deepEqual(failed(r),[]);
// Under a full sweep the type is ink on the signal band, not white.
const d=g.getImageData(m.text.x,410,m.text.w,20).data;let white=0,ink=0;
for(let i=0;i<d.length;i+=4){if(d[i]>240&&d[i+1]>240&&d[i+2]>230)white++;if(d[i]<60&&d[i+1]<70&&d[i+2]<70)ink++;}
assert.equal(white,0);assert.ok(ink>20,'ink pixels '+ink);
""", canvas=True)

    def test_meaning_tokens_and_annotation_defaults(self):
        self.node("""
const T=D.T;
assert.equal(T.signal,T.gold);assert.equal(T.signalSoft,T.goldSoft);assert.equal(T.wrong,'#C62F2A');assert.notEqual(T.wrong,T.accent);
assert.equal(T.fiction,'#6A3BEF');assert.equal(T.fictionInk,'#FFFFFF');for(const k of ['wrongSoft','goodSoft'])assert.match(T[k],/^#[0-9A-F]{6}$/);
assert.equal(T.paper,'#F2EDE2');assert.equal(T.ink,'#15262C');assert.equal(T.teal,'#0E7469');assert.equal(T.accent,'#DE5530');
const strokes=[];let {g,S}=stage();const stroke=g.stroke.bind(g);g.stroke=(...a)=>{strokes.push(g.strokeStyle);return stroke(...a);};
S.strike(100,200,300,1);S.underline(100,200,320,1);S.marker('m',100,400,100,40,1);S.finish();
assert.equal(strokes[0].toUpperCase(),T.ink);assert.equal(strokes[1].toUpperCase(),T.accent);
const [r,gg,b]=px(g,150,420);assert.ok(r>220&&gg>170&&b<130,'signal marker '+[r,gg,b]);
for(const name of ['FLOOR','EDGE','WORD_BUDGET','BASELINE','STATES','STATE_ALIASES','floorOf','stepValue','niceStep','spoken','talking','focusOf',
  'orderKeys','fitCamera','beforePush','world','planner','defineStates','stateOf','T','TYPE','FACES','FONT_FILES','E','role','clamp','lerp','seg',
  'wordTimes','createCues','cameraAt','extendTheme','installDesignRuntime','createDesignStage','paintBackground'])assert.ok(name in D,name);
for(const name of ['night','onScreen','callout','markText','stateBox','swatch','hatch','rule','vrule','iris','wipe','unclipped','label'])assert.ok(name in S,name);
""", canvas=True)


if __name__ == '__main__':
    unittest.main()
