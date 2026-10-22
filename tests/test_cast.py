"""People with faces: a course's cast looks the same everywhere and stays visible to the frame audit."""
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parent.parent
PRODUCTION = ROOT / 'assets/starter/production-source'

# Design stages on fresh canvases. The grain decodes asynchronously, so run() waits for it first:
# afterwards every frame paints the same background and frames can be compared pixel for pixel.
STAGE = """
const assert=require('node:assert/strict'),canvas=require(process.env.CANVAS_MODULE),D=require('./design.cjs'),I=require('./illustrations.cjs');
D.installDesignRuntime(canvas);
const course={width:1280,height:720};
const ready=async()=>{for(let i=0;i<200;i++){const g=canvas.createCanvas(1280,720).getContext('2d');let img=false;const d=g.drawImage.bind(g);
  g.drawImage=(x,...a)=>{img=img||x instanceof canvas.Image;return d(x,...a);};D.createDesignStage(g,course).finish();if(img)return;await new Promise(r=>setTimeout(r,20));}
  throw new Error('grain never decoded');};
const frame=(draw,opts)=>{const g=canvas.createCanvas(1280,720).getContext('2d'),S=D.createDesignStage(g,course,opts),out=draw(S),r=S.finish();
  return {r,out,data:Buffer.from(g.getImageData(0,0,1280,720).data)};};
const item=(r,id)=>r.items.find(i=>i.id===id);
const intersects=(a,b)=>Math.min(a.x+a.w,b.x+b.w)>Math.max(a.x,b.x)&&Math.min(a.y+a.h,b.y+b.h)>Math.max(a.y,b.y);
// Neutral fiction: a lending library and its courier.
const PEOPLE={librarian:{name:'Mira',role:'Librarian',skin:'skin3',hair:'hairBlack',style:'long',top:'cardigan',topColor:'sage',bottom:'navy'},
  courier:{name:'Joss',role:'Courier',skin:'skin5',hair:'hairBlack',style:'puff',top:'tee',topColor:'sand',bottom:'olive',badge:true}};
const run=fn=>ready().then(fn).catch(e=>{console.error(e);process.exitCode=1;});
"""


class CastTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which('node'):
            self.skipTest('Node.js is required')

    def node(self, code):
        module = os.environ.get('CANVAS_MODULE') or str(PRODUCTION / 'node_modules/@napi-rs/canvas')
        if not Path(module).is_dir():
            self.skipTest('Canvas runtime is not configured')
        result = subprocess.run(['node', '-e', STAGE + code], cwd=PRODUCTION, env=dict(os.environ, CANVAS_MODULE=module),
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        return result

    def test_a_preset_draws_identically_wherever_it_is_staged(self):
        self.node("""
run(()=>{
  I.defineCast(PEOPLE);
  const pose={s:.9,pose:'present',facing:-1};
  const a=frame(S=>I.cast(S,'mira','librarian',420,520,pose)),b=frame(S=>I.cast(S,'mira','librarian',420,520,pose));
  assert.ok(a.data.equals(b.data));assert.deepEqual(a.r.items,b.r.items);
  // A preset is exactly its look: figure() with the same fields, or the createIllustration helper, draws the same pixels.
  assert.ok(a.data.equals(frame(S=>I.figure(S,'mira',420,520,{...PEOPLE.librarian,...pose})).data));
  assert.ok(a.data.equals(frame(S=>I.createIllustration(S).cast('mira','librarian',420,520,pose)).data));
  // Another member draws differently; the registry entries are frozen.
  assert.ok(!a.data.equals(frame(S=>I.cast(S,'mira','courier',420,520,pose)).data));
  assert.ok(Object.isFrozen(I.CAST.librarian));assert.equal(I.CAST.courier.badge,true);assert.equal(I.CAST.librarian.inner,'white');
  assert.deepEqual(a.r.items.map(i=>[i.id,i.kind]),[['mira','actor'],['mira-name','label'],['mira-role','label']]);
  // On night the outline turns into a light keyline, so ink shoes and black hair do not vanish.
  const light=(d,[x0,y0,x1,y1])=>{let n=0;for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){const k=(y*1280+x)*4;if(d[k]+d[k+1]+d[k+2]>480)n++;}return n;};
  const night=frame(S=>I.cast(S,'mira','librarian',420,520,{...pose,label:'none'}),{background:'night'});
  assert.ok(light(night.data,[380,505,460,525])>40,'shoes keep a light keyline on night');
});
""")

    def test_look_overrides_and_invalid_casts_throw(self):
        self.node("""
I.defineCast(PEOPLE);
const S=D.createDesignStage(canvas.createCanvas(1280,720).getContext('2d'),course);
// A recurring person always looks the same: every look field is refused, even with the preset's own value.
for(const k of I.LOOK_FIELDS)assert.throws(()=>I.cast(S,'o-'+k,'librarian',400,520,{[k]:I.CAST.librarian[k]}),new RegExp('always looks the same: '+k+' cannot'));
assert.throws(()=>I.cast(S,'o1','librarian',400,520,{name:'Someone else'}),/keeps its name/);
assert.throws(()=>I.cast(S,'o2','librarian',400,520,{colour:'navy'}),/Unknown cast option: colour/);
assert.throws(()=>I.cast(S,'o3','visitor',400,520),/Unknown cast member: visitor/);
I.cast(S,'quiet','librarian',300,520,{s:.8,name:false});I.cast(S,'anon','courier',800,520,{s:.8,label:'none'});
assert.deepEqual(S.finish().items.map(i=>i.id),['quiet','quiet-role','anon']);
// defineCast validates everything before writing anything.
const ok={skin:'skin1',hair:'hairGrey',style:'bald'};
for(const [spec,error] of [[{librarian:ok},/already defined: librarian/],[{'Bad-key':ok},/Invalid cast key/],[{x:{hair:'hairGrey',style:'bald'}},/needs skin/],
    [{x:{...ok,skin:'pink'}},/skin must be one of skin1/],[{x:{...ok,topColor:'signal'}},/topColor must be one of/],[{x:{...ok,style:'mohawk'}},/style must be one of/],
    [{x:{...ok,beard:'goatee'}},/beard must be one of/],[{x:{...ok,shoes:'red'}},/Unknown cast field for x: shoes/],[{x:{...ok,name:''}},/name must be text or null/],
    [{x:{...PEOPLE.courier,name:'Someone'}},/courier and x look identical/],[{x:ok,y:{...ok,role:'Twin'}},/x and y look identical/],[{},/at least one person/]])
  assert.throws(()=>I.defineCast(spec),error);
assert.throws(()=>I.defineCast({fresh:ok,broken:{...ok,skin:'nope',hair:'hairSand'}}),/skin must be one of/);
assert.equal(I.CAST.fresh,undefined);
I.defineCast({fresh:ok});assert.equal(I.CAST.fresh.name,null);
// Figures refuse unknown poses, props, placements and arm shapes, and colours outside the identity palette.
for(const [opts,error] of [[{pose:'dance'},/Unknown pose: dance/],[{prop:'umbrella'},/Unknown prop: umbrella/],[{label:'inside'},/Unknown label placement/],
    [{arms:[[1,2]]},/arms must be/],[{arms:'jump'},/Unknown pose: jump/],[{topColor:'teal'},/topColor must be one of/],[{hair:'skin2'},/hair must be one of/]])
  assert.throws(()=>I.figure(S,'f',400,520,opts),error);
// Identity colours never reuse a meaning colour, the accent or the house teal and gold.
const meanings=['signal','signalSoft','wrong','wrongSoft','good','goodSoft','fiction','fictionInk','accent','accentSoft','teal','tealSoft','gold','goldSoft'].map(k=>D.T[k].toUpperCase());
for(const [k,v] of Object.entries(I.LOOK)){assert.match(v,/^#[0-9A-F]{6}$/i);assert.ok(!meanings.includes(v.toUpperCase()),k);}
""")

    def test_figures_register_their_full_extent_and_clear_labels(self):
        self.node("""
run(()=>{
  const blank=frame(()=>null).data,combos=[];
  Object.keys(I.POSES).forEach((pose,i)=>{for(const facing of [1,-1])combos.push({pose,facing,style:I.HAIR_STYLES[(2*i+(facing>0?0:1))%I.HAIR_STYLES.length],
    top:I.TOPS[i%5],lower:i%3?'trousers':'skirt',speaking:i%2,phase:.14,glasses:i%4===0,beard:['beard','stubble',null][i%3],badge:i%5===0});});
  for(const prop of I.PROPS)for(const facing of [1,-1])combos.push({pose:prop==='phone'||prop==='mug'?'present':'hold',prop,facing,style:'bun'});
  for(const style of I.HAIR_STYLES)combos.push({pose:'lean',style,facing:-1,speaking:1,phase:.14},{pose:'raise',style,speaking:1,phase:.14});
  combos.push({pose:'wave',s:.5,style:'puff'},{pose:'wave',s:1.15,style:'curly',speaking:1,phase:.3},{pose:'point',camera:{x:640,y:380,zoom:1.25}});
  // Every pixel a figure paints lies inside its registered bounds (screen space, through a camera too).
  for(const {camera,...opts} of combos) {
    const draw=S=>I.figure(S,'p',640,560,{...opts,label:'none'}),{data,r}=frame(S=>camera?S.view(camera,()=>draw(S)):draw(S));
    const b=item(r,'p').bounds,x0=Math.floor(b.x),y0=Math.floor(b.y),x1=Math.ceil(b.x+b.w),y1=Math.ceil(b.y+b.h);let painted=0,outside=0;
    for(let y=0;y<720;y++)for(let x=0;x<1280;x++){const k=(y*1280+x)*4;if(data[k]===blank[k]&&data[k+1]===blank[k+1]&&data[k+2]===blank[k+2])continue;
      painted++;if(x<x0||x>=x1||y<y0||y>=y1)outside++;}
    assert.ok(painted>2000,JSON.stringify(opts));assert.equal(outside,0,JSON.stringify(opts)+' paints outside its bounds');
    assert.ok(b.w<(opts.s||1)*(camera?1.25:1)*330&&b.h<(opts.s||1)*(camera?1.25:1)*340,'bounds stay tight: '+JSON.stringify(b));
  }
  // Names and roles are 28 px labels clear of the person, in every placement, sharing the figure's owner.
  for(const label of ['below','above','left','right']) {
    const {r}=frame(S=>{S.actor('panel',{x:60,y:90,w:1160,h:500},()=>{});I.figure(S,'p',640,label==='above'?580:490,{s:.75,name:'Mira',role:'Librarian',label,speaking:1,phase:.2,owner:'panel'});});
    const p=item(r,'p'),n=item(r,'p-name'),o=item(r,'p-role');
    assert.equal(p.owner,'panel');assert.equal(n.owner,'panel');assert.equal(o.owner,'panel');
    for(const [a,c] of [[p,n],[p,o],[n,o]])assert.ok(!intersects(a.bounds,c.bounds),label+': '+a.id+' x '+c.id);
    assert.ok(Math.abs(n.bounds.h-28*1.24)<.01&&Math.abs(o.bounds.h-28*1.24)<.01);
    assert.deepEqual(r.invariants.checks.filter(c=>!c.passed),[],label);
  }
  // Fully faded figures register nothing.
  assert.deepEqual(frame(S=>I.figure(S,'p',640,560,{alpha:0,name:'Mira'})).r.items,[]);
});
""")

    def test_speaking_moves_the_mouth_and_adds_speech_marks(self):
        self.node("""
run(()=>{
  I.defineCast(PEOPLE);
  const at=(speaking,phase,facing=1,label='none')=>frame(S=>I.cast(S,'p','courier',640,560,{speaking,phase,facing,label}));
  const changed=(a,b,[x0,y0,x1,y1])=>{let n=0;for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){const k=(y*1280+x)*4;if(a[k]!==b[k]||a[k+1]!==b[k+1]||a[k+2]!==b[k+2])n++;}return n;};
  const quiet=at(0,.14),open=at(1,.14),closing=at(1,0);
  assert.ok(quiet.data.equals(at(0,.9).data),'a silent mouth does not move');
  assert.deepEqual(open.out.mouth,[644,319]);
  const mouth=[634,305,656,334],marks=[684,297,716,327];
  assert.ok(changed(quiet.data,open.data,mouth)>40,'speaking opens the mouth');
  assert.ok(changed(open.data,closing.data,mouth)>20,'the mouth moves with phase');
  assert.ok(changed(quiet.data,open.data,marks)>20,'speech marks appear on the facing side');
  const left=at(1,.14,-1),mirror=[564,297,596,327];
  assert.ok(changed(at(0,.14,-1).data,left.data,mirror)>20&&changed(quiet.data,open.data,mirror)===0,'marks follow facing');
  // The marks end 14 px past x = head + 43 px (plus their stroke); the bounds cover them on either side.
  assert.ok(open.out.bounds.x+open.out.bounds.w>=698.4&&left.out.bounds.x<=581.6,'the bounds cover the marks');
  // A name placed beside the speaker does not jump when speech starts, even where the marks widen the
  // registered bounds (a lean carries the head past the arms).
  const leaning=speaking=>frame(S=>I.cast(S,'p','courier',560,560,{pose:'lean',speaking,phase:.14,label:'right'}));
  const [still,talks]=[leaning(0),leaning(1)];
  assert.ok(talks.out.bounds.w>still.out.bounds.w+10);assert.deepEqual(item(still.r,'p-name').bounds,item(talks.r,'p-name').bounds);
  // The design focus helper drives it: silent before the window, speaking inside it.
  assert.equal(D.talking(1,2,4),0);assert.ok(D.talking(3,2,4)>.99);
});
""")

    def test_a_dimmed_person_fades_as_one_figure(self):
        self.node("""
run(()=>{
  // focusOf dims earlier speakers to .3. The result must match the ideal composite blank*(1-a) + person*a,
  // not an x-ray in which hair shows through the face and sleeves through the torso.
  const look={skin:'skin3',hair:'hairBlack',style:'long',top:'cardigan',topColor:'sage',bottom:'navy',pose:'present',label:'none'},a=.3;
  for(const background of ['paper','night']) {
    const blank=frame(()=>{},{background}).data,full=frame(S=>I.figure(S,'p',400,560,look),{background}).data;
    const error=o=>{const {data,r}=frame(S=>S.fade(a,()=>I.figure(S,'p',400,560,{...look,...o})),{background});let max=0;
      for(let k=0;k<full.length;k+=4){if(full[k]===blank[k]&&full[k+1]===blank[k+1]&&full[k+2]===blank[k+2])continue;
        for(let j=0;j<3;j++)max=Math.max(max,Math.abs(data[k+j]-(blank[k+j]*(1-a)+full[k+j]*a)));}
      // Canvas keeps alpha in 8 bits (.3 is stored as 76/255).
      assert.ok(Math.abs(item(r,'p').alpha-a)<.01,'the audit still sees the dimmed alpha');return max;};
    const one=error({}),xray=error({ground:null});
    assert.ok(one<=16,background+': faded person off the ideal by '+one);assert.ok(xray>60,background+': plain alpha '+xray);
  }
});
""")

    def test_motion_stage_old_glyphs_and_lettering_keep_working(self):
        self.node("""
run(()=>{
  // figure() also draws on the starter's motion stage, beside the original glyphs.
  const {createStage}=require('./motion.cjs'),st=createStage(canvas.createCanvas(1280,720).getContext('2d'),course),v=I.createIllustration(st);
  v.person('old',200,300);v.figure('fig',600,500,{s:.8,name:'Mira',role:'Librarian',pose:'wave'});
  const m=st.finish();assert.deepEqual(m.items.map(i=>[i.id,i.kind]),[['old','actor'],['fig','actor'],['fig-name','label'],['fig-role','label']]);
  assert.ok(!intersects(item(m,'fig').bounds,item(m,'fig-name').bounds));
  // blendArms grows one pose into another.
  assert.deepEqual(I.blendArms('stand','point',0),I.POSES.stand.arms);assert.deepEqual(I.blendArms('stand','point',1),I.POSES.point.arms);
  const half=I.blendArms('stand',[[0,0],[1,1]],.5);assert.ok(half[1][0]>.12&&half[1][0]<1);
  // On a design stage glyph-internal lettering is tertiary (24 px), and a tag's pill fits the system type.
  const {r,data}=frame(S=>{const w=I.createIllustration(S);w.document('d',300,300,2,{title:'A17',revision:2});w.phone('ph',600,330,1,{title:'Article',revision:2,time:'11 AM'});
    w.document('small',800,300,1,{title:'A17'});w.tag('tg','Due',1000,300);});
  assert.ok(Math.abs(item(r,'small-title').bounds.h-24*1.24)<.01&&Math.abs(item(r,'ph-headline').bounds.h-24*1.24)<.01);
  assert.ok(Math.abs(item(r,'tg').bounds.h-28*1.24)<.01);
  assert.deepEqual(r.invariants.checks.filter(c=>!c.passed),[]);
  const tag=item(r,'tg').bounds,k=(300*1280+Math.floor(tag.x-3))*4;assert.deepEqual([...data.subarray(k,k+3)],[200,231,216],'the pill reaches past the type');
});
""")


if __name__ == '__main__':
    unittest.main()
