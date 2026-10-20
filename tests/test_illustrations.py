"""Illustrated vocabulary must remain visible to the common geometry auditor."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parent.parent


class IllustrationTests(unittest.TestCase):
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
