"""Every-frame audit checks for defects a sampled review can miss: flashed labels and the fiction badge."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
PRODUCTION = ROOT / 'assets/starter/production-source'
FRAME = "viewport:{x:0,y:0,w:1280,h:720},safe:{x:0,y:0,w:1280,h:720}"
# A label whose opacity is a function of the frame number, at 24 fps.
LABEL = ("exports.draw=(g,l,t)=>{const f=Math.round(t*24),a=(%s);"
         "return {items:a>0?[{id:'note',kind:'label',bounds:{x:100,y:100,w:120,h:30},alpha:a}]:[],transition:(%s),"
         + FRAME + "};};\n")


@unittest.skipUnless(shutil.which('node'), 'Node.js is required')
class AuditCheckTests(unittest.TestCase):
    def setUp(self):
        module = os.environ.get('CANVAS_MODULE') or str(PRODUCTION / 'node_modules/@napi-rs/canvas')
        if not Path(module).is_dir():
            self.skipTest('Canvas runtime is not configured')
        self.env = dict(os.environ, CANVAS_MODULE=module)
        self.temporary = tempfile.TemporaryDirectory(prefix='audit-check-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = self.project('course', '--demo')

    def project(self, name, flag):
        root = Path(self.temporary.name) / name
        subprocess.run([sys.executable, str(ROOT / 'scripts/new_project.py'), str(root), flag], check=True, capture_output=True)
        return root

    def audit(self, world=None, lesson=None, rules=None, root=None):
        root = root or self.root
        if lesson is not None:
            data = json.loads((root / 'course.json').read_text())
            data['lessons'] = [lesson]
            (root / 'course.json').write_text(json.dumps(data))
        if world is not None:
            (root / 'production-source/world.cjs').write_text(world)
        if rules is not None:
            (root / 'production-source/intentional-overlaps.json').write_text(json.dumps(rules))
        result = subprocess.run(['node', str(root / 'production-source/audit.cjs')], env=self.env, capture_output=True, text=True)
        report = root / 'review/frame-audit.json'
        return result, json.loads(report.read_text())['lessons'][0] if result.returncode in (0, 1) and report.is_file() else None

    def flash(self, opacity, transition='false', rules=None):
        return self.audit(LABEL % (opacity, transition), dict(id='01', duration=3), rules or [])

    def test_a_label_gone_within_half_a_second_is_a_flash(self):
        result, lesson = self.flash('f>=24&&f<30?1:0')
        self.assertEqual(result.returncode, 1)
        finding = lesson['unresolved'][0]
        self.assertEqual((finding['type'], finding['a'], finding['actual'], finding['firstFrame'], finding['lastFrame']),
                         ('flash', 'note', .25, 24, 29))
        self.assertTrue((self.root / 'review' / finding['preview']).is_file())

    def test_readable_or_never_readable_labels_are_not_flashes(self):
        cases = {'held for half a second': 'f>=24&&f<36?1:0',
                 'ghosted for a second, then filled briefly': 'f>=12&&f<36?.2:f>=36&&f<42?1:0',
                 'never more than a dim trace': 'f>=24&&f<30?.3:0',
                 'still on screen when the lesson ends': 'f>=68?1:0'}
        for name, opacity in cases.items():
            with self.subTest(name=name):
                result, lesson = self.flash(opacity)
                self.assertEqual(result.returncode, 0, lesson and lesson['unresolved'])
                self.assertEqual(lesson['unresolved'], [])

    def test_a_transition_does_not_cut_a_labels_time_on_screen(self):
        # Transition frames register nothing; the label is on screen for 16 frames around one.
        result, lesson = self.flash('(f>=24&&f<32)||(f>=40&&f<48)?1:0', 'f>=32&&f<40')
        self.assertEqual(result.returncode, 0, lesson and lesson['unresolved'])
        self.assertEqual(lesson['transitions'], [[round(32 / 24, 3), round(40 / 24, 3)]])
        self.assertEqual(lesson['transitionFrames'], 8)

    def test_a_flash_rule_accepts_only_the_named_labels_flash(self):
        rule = {'lesson': '01', 'a': 'note', 'type': 'flash', 'start': .9, 'end': 1.4, 'reason': 'Fixture: a deliberate spark.'}
        result, lesson = self.flash('f>=24&&f<30?1:0', rules=[rule])
        self.assertEqual(result.returncode, 0)
        self.assertEqual([(x['type'], x['a'], x['reason']) for x in lesson['intentional']], [('flash', 'note', rule['reason'])])
        # The same rule cannot excuse a second flash outside its window ...
        result, lesson = self.flash('(f>=24&&f<30)||(f>=60&&f<66)?1:0', rules=[rule])
        self.assertEqual(result.returncode, 1)
        self.assertEqual((lesson['unresolved'][0]['type'], lesson['unresolved'][0]['firstFrame']), ('flash', 60))
        # ... nor another kind of finding about that label.
        outside = ("exports.draw=()=>({items:[{id:'note',kind:'label',bounds:{x:-20,y:100,w:120,h:30},alpha:1}],"
                   "viewport:{x:0,y:0,w:1280,h:720},safe:{x:40,y:88,w:1200,h:499}});\n")
        result, lesson = self.audit(outside, dict(id='01', duration=3), [dict(rule, start=0, end=3)])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(lesson['unresolved'][0]['type'], 'safe-zone')
        for invalid in (dict(rule, b='other'), dict(rule, type='blink'), {k: v for k, v in rule.items() if k != 'reason'}):
            with self.subTest(invalid=invalid):
                result, _ = self.flash('0', rules=[invalid])
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Invalid intentional-overlap rule', result.stderr)

    def test_declared_fiction_is_checked_against_the_reported_badge(self):
        scenes = [dict(id='real', start=0, end=3, fiction=False), dict(id='invented', start=3, end=6, fiction=True),
                  dict(id='mixed', start=6, end=9)]
        lesson = dict(id='01', duration=9, scenes=scenes)
        world = "exports.draw=(g,l,t)=>({items:[],notes:{fictionBadge:(%s)}," + FRAME + "});\n"
        # On over the invented scene, fading across the boundaries; anything over the undeclared scene.
        result, report = self.audit(world % 't<2.7?0:t<3.3?(t-2.7)/.6:t<6?1:.4', lesson, [])
        self.assertEqual(result.returncode, 0, report and report['unresolved'])
        for name, badge, scene, expected in (
                ('left on over real facts', '1', 'real', 'badge off: the scene declares real facts only'),
                ('missing over invented material', '0', 'invented', 'badge on: the scene declares invented material')):
            with self.subTest(name=name):
                result, report = self.audit(world % badge, lesson, [])
                self.assertEqual(result.returncode, 1)
                self.assertEqual([(x['type'], x['a'], x['expected']) for x in report['unresolved']], [('fiction-badge', scene, expected)])
        # A world that reports no badge at all cannot satisfy a scene that declares invented material.
        result, report = self.audit("exports.draw=()=>({items:[]," + FRAME + "});\n", lesson, [])
        self.assertEqual([(x['type'], x['a']) for x in report['unresolved']], [('fiction-badge', 'invented')])

    def test_the_design_demo_declares_fiction_and_a_wrong_declaration_fails(self):
        demo = self.project('designed', '--design-demo')
        result, lesson = self.audit(root=demo)
        self.assertEqual(result.returncode, 0, lesson and lesson['unresolved'])
        self.assertEqual(len(lesson['transitions']), 4)
        data = json.loads((demo / 'course.json').read_text())
        declared = {scene['id']: scene['fiction'] for scene in data['lessons'][0]['scenes']}
        self.assertEqual(declared, {'open': False, 'claim': True, 'transfer': True, 'contrast': True, 'series': True,
                                    'method': False, 'check': True})
        for scene in data['lessons'][0]['scenes']:
            if scene['id'] in {'method', 'transfer'}:
                scene['fiction'] = not scene['fiction']
        (demo / 'course.json').write_text(json.dumps(data))
        result, lesson = self.audit(root=demo)
        self.assertEqual(result.returncode, 1)
        self.assertEqual({(x['type'], x['a']) for x in lesson['unresolved']}, {('fiction-badge', 'transfer'), ('fiction-badge', 'method')})

    def test_a_flagged_frame_is_drawn_without_reading_back_the_audit_canvas(self):
        # The preview is a fresh canvas: it shows the flagged frame even though the audit canvas was never read.
        world = ("exports.draw=(g,l,t)=>{g.fillStyle=t<1?'#ffffff':'#000000';g.fillRect(0,0,1280,720);"
                 "return {items:t>=1?[{id:'late',kind:'label',bounds:{x:-50,y:10,w:100,h:20},alpha:1}]:[],"
                 "viewport:{x:0,y:0,w:1280,h:720},safe:{x:40,y:88,w:1200,h:499}};};\n")
        result, lesson = self.audit(world, dict(id='01', duration=2), [])
        self.assertEqual(result.returncode, 1)
        preview = self.root / 'review' / lesson['unresolved'][0]['preview']
        pixel = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(preview), '-vf', 'scale=1:1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                               capture_output=True, check=True).stdout
        self.assertTrue(all(channel < 16 for channel in pixel), pixel)   # the black frame at t >= 1, not the white one before it


if __name__ == '__main__':
    unittest.main()
