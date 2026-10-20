"""Illustrated vocabulary must remain visible to the common geometry auditor."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class IllustrationTests(unittest.TestCase):
    def canvas_environment(self):
        module = os.environ.get('CANVAS_MODULE') or str(ROOT / 'skills/continuous-learning-videos/assets/starter/production-source/node_modules/@napi-rs/canvas')
        if not shutil.which('node') or not Path(module).is_dir():
            self.skipTest('Canvas runtime is not configured')
        return dict(os.environ, CANVAS_MODULE=module)

    def test_numeric_canvas_guard_reaches_bad_clock_internals_with_finite_registry_bounds(self):
        production = ROOT / 'skills/continuous-learning-videos/assets/starter/production-source'
        code = """
const assert=require('node:assert/strict');
const {createCanvas}=require(process.env.CANVAS_MODULE),{createStage}=require('./motion.cjs'),{createIllustration,P}=require('./illustrations.cjs'),{install}=require('./finite-canvas.cjs');
const course={width:1280,height:720};
const plain=createStage(createCanvas(1280,720).getContext('2d'),course),bad=createIllustration(plain);
// Native Canvas ignores the NaN line endpoint; the registered outer clock stays finite.
bad.clock('bad',400,240,1,P.gold);
const registry=plain.finish();assert.ok(registry.items.every(i=>Object.values(i.bounds).every(Number.isFinite)));
const g=createCanvas(1280,720).getContext('2d'),counts=install(g),stage=createStage(g,course),v=createIllustration(stage);
assert.equal(install(g),counts);
v.clock('valid',400,240,1,.3,P.gold);
assert.throws(()=>v.clock('invalid',600,240,1,P.gold),/Non-finite\/non-numeric Canvas lineTo argument/);
assert.ok(counts.lineTo>0);
assert.throws(()=>g.drawImage(createCanvas(2,2)),/Canvas drawImage requires/);
assert.throws(()=>g.ellipse(100,100,10,5,0,Math.PI*2),/Non-finite\/non-numeric Canvas ellipse argument 6/);
"""
        subprocess.run(['node', '-e', code], cwd=production, env=self.canvas_environment(),
                       check=True, capture_output=True, text=True)

    def test_degenerate_illustration_paths_remain_finite(self):
        production = ROOT / 'skills/continuous-learning-videos/assets/starter/production-source'
        code = """
const assert=require('node:assert/strict');
const {createCanvas}=require(process.env.CANVAS_MODULE),{createStage}=require('./motion.cjs'),{createIllustration}=require('./illustrations.cjs'),{install}=require('./finite-canvas.cjs');
const g=createCanvas(1280,720).getContext('2d');install(g);
const v=createIllustration(createStage(g,{width:1280,height:720}));
for(const completion of [0,.01,.5,1]) {
 v.line([[20,30],[20,30],[40,50]],undefined,2,completion);
 v.arrow([[20,30],[20,30]],undefined,2,completion);
 assert.deepEqual(v.pointOn([[20,30],[20,30]],completion),[20,30]);
 assert.ok(v.pointOn([[20,30],[20,30],[40,50]],completion).every(Number.isFinite));
}
"""
        subprocess.run(['node', '-e', code], cwd=production, env=self.canvas_environment(),
                       check=True, capture_output=True, text=True)

    def test_default_audit_and_poster_render_reject_unregistered_nan_drawing(self):
        env = self.canvas_environment()
        with tempfile.TemporaryDirectory(prefix='numeric-canvas-test-') as folder:
            project = Path(folder) / 'course'
            subprocess.run(['python3', str(ROOT / 'skills/continuous-learning-videos/scripts/new_project.py'),
                            str(project), '--demo'], check=True, capture_output=True)
            (project / 'production-source/world.cjs').write_text("""
module.exports={draw(g){g.lineTo(NaN,10);return {items:[],safe:{x:0,y:0,w:1280,h:720},viewport:{x:0,y:0,w:1280,h:720},invariants:{}};}};
""")
            for command in [('audit.cjs',), ('render.cjs', 'posters')]:
                with self.subTest(command=command):
                    result = subprocess.run(['node', str(project / 'production-source' / command[0]), *command[1:]],
                                            env=env, capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('Non-finite/non-numeric Canvas lineTo argument', result.stderr)

    def test_glyphs_register_actual_camera_transformed_bounds_and_owned_labels(self):
        module = os.environ.get('CANVAS_MODULE') or str(ROOT / 'skills/continuous-learning-videos/assets/starter/production-source/node_modules/@napi-rs/canvas')
        if not shutil.which('node') or not Path(module).is_dir():
            self.skipTest('Canvas runtime is not configured')
        production = ROOT / 'skills/continuous-learning-videos/assets/starter/production-source'
        code = """
const {createCanvas}=require(process.env.CANVAS_MODULE),{createStage}=require('./motion.cjs'),{createIllustration}=require('./illustrations.cjs');
const c=createCanvas(1280,720),g=c.getContext('2d'),stage=createStage(g,{width:1280,height:720},{x:640,y:340,zoom:.9}),v=createIllustration(stage);
v.person('reader',200,240);v.document('record',350,240,1,{title:'A17',revision:2});v.browser('web',550,240,1,{revision:2});v.envelope('mail',800,240);v.building('office',1050,240);v.phone('phone',550,440,.6,{title:'Article',revision:2,time:'11 AM'});v.clock('clock',800,440);
console.log(JSON.stringify(stage.finish()));
"""
        env = dict(os.environ, CANVAS_MODULE=module)
        result = subprocess.run(['node', '-e', code], cwd=production, env=env, check=True, capture_output=True, text=True)
        report = json.loads(result.stdout)
        actors = [item for item in report['items'] if item['kind'] == 'actor']
        self.assertEqual(len(actors), 7)
        reader = next(item for item in actors if item['id'] == 'reader')
        self.assertAlmostEqual(reader['bounds']['x'], (200 - 27 - 640) * .9 + 640, delta=.0001)
        self.assertAlmostEqual(reader['bounds']['w'], 54 * .9, delta=.0001)
        labels = [item for item in report['items'] if item['kind'] == 'label']
        self.assertEqual({item['owner'] for item in labels}, {'record', 'web', 'phone'})
        self.assertEqual(len(labels), 6)
        self.assertEqual(len({item['id'] for item in report['items']}), len(report['items']))


if __name__ == '__main__':
    unittest.main()
