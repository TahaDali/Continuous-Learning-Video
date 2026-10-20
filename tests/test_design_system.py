"""The shared design system must stay auditable, cue-driven and self-contained."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
PRODUCTION = ROOT / 'assets/starter/production-source'
sys.path.insert(0, str(ROOT / 'scripts'))
import design_checks  # noqa: E402

FACES = ['Inter-Regular', 'Inter-Medium', 'Inter-SemiBold', 'Inter-Bold', 'Inter-ExtraBold',
         'InstrumentSerif-Regular', 'InstrumentSerif-Italic', 'JetBrainsMono-Regular', 'JetBrainsMono-Bold']


def retime(project, words_per_second):
    """Rewrite spans and word timings the way narrate.py does, at a chosen speech rate."""
    data = json.loads((project / 'course.json').read_text())
    for lesson in data['lessons']:
        cursor = 0.
        for scene in lesson['scenes']:
            at, timings = cursor + .18, []
            for match in re.finditer(r'\S+', scene['narration']):
                token = match.group().strip('.,:;?')
                duration = (len(re.sub(r'[^\w]', '', token)) + 2) / (words_per_second * 6.2)
                timings.append({'text': token, 'charStart': match.start(), 'charEnd': match.start() + len(token),
                                'start': round(at, 4), 'end': round(at + duration, 4)})
                at += duration + (.25 if match.group()[-1] in '.,:;?' else .03)
            scene.update(start=round(cursor, 4), speechStart=round(cursor + .18, 4), speechEnd=round(at, 4),
                         end=round(at + .48, 4), wordTimings=timings)
            cursor = scene['end']
        lesson['duration'] = round(cursor, 4)
    (project / 'course.json').write_text(json.dumps(data, indent=2) + '\n')


class DesignSystemTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which('node'):
            self.skipTest('Node.js is required')
        self.temporary = tempfile.TemporaryDirectory(prefix='design-system-test-')
        self.base = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def canvas_environment(self):
        module = os.environ.get('CANVAS_MODULE') or str(PRODUCTION / 'node_modules/@napi-rs/canvas')
        if not Path(module).is_dir():
            self.skipTest('Canvas runtime is not configured')
        return dict(os.environ, CANVAS_MODULE=module)

    def node(self, code, env=None):
        return subprocess.run(['node', '-e', code], cwd=PRODUCTION, env=env or dict(os.environ),
                              check=True, capture_output=True, text=True)

    def project(self, name, *flags):
        target = self.base / name
        subprocess.run([sys.executable, str(ROOT / 'scripts/new_project.py'), str(target), *flags],
                       check=True, capture_output=True)
        return target

    def audit(self, project, env):
        result = subprocess.run(['node', str(project / 'production-source/audit.cjs')], env=env, capture_output=True, text=True)
        return result, json.loads((project / 'review/frame-audit.json').read_text())

    def test_drawing_requires_the_installed_runtime(self):
        self.node("""
const assert=require('node:assert/strict'),D=require('./design.cjs');
assert.throws(()=>D.createDesignStage({},{width:1280,height:720}),/Design runtime not installed/);
assert.throws(()=>D.installDesignRuntime({}),/needs the loaded canvas module/);
assert.throws(()=>D.extendTheme({ink:'#000000'}),/already exists/);
assert.throws(()=>D.extendTheme({brand:'red'}),/#rrggbb/);
""")

    def test_cues_follow_measured_words_and_fail_on_missing_words(self):
        self.node("""
const assert=require('node:assert/strict'),{createCues,wordTimes}=require('./design.cjs');
const text='Ten units leave. Then they arrive, and ten units rest.',words=text.split(' ');
const wordTimings=words.map((w,i)=>({text:w.replace(/[.,]/g,''),start:10+i,end:10.5+i}));
const lesson={scenes:[{id:'move',narration:text,start:9,end:30,wordTimings},
  {id:'plain',narration:'One two three four.',start:40,end:44,speechStart:40.2,speechEnd:43.5}]};
const cue=createCues(lesson);
assert.equal(cue('move','leave'),12);assert.equal(cue('move','UNITS',2),18);assert.equal(cue(1,'arrive'),15);
assert.deepEqual(cue.phrase('move','ten units',{after:cue('move','arrive')}),[17,18]);
assert.equal(cue.method('move'),'measured');assert.equal(cue.method('plain'),'estimated');
const est=['one','two','three','four'].map(w=>cue('plain',w));
assert.ok(est.every((t,i)=>t>=40.2&&t<43.5&&(i===0||t>est[i-1])));
assert.throws(()=>cue('move','vanish'),/Missing narration cue/);
assert.throws(()=>cue('move','leave',2),/Missing narration cue/);
assert.throws(()=>cue.phrase('move','units vanish'),/Missing narration phrase word/);
assert.throws(()=>cue('absent','ten'),/Unknown cue scene/);
assert.equal(wordTimes(words,lesson.scenes[0]).method,'measured');
assert.equal(wordTimes(['a','b'],lesson.scenes[0]).method,'estimated');
""")

    def test_fonts_ship_with_licenses_and_join_the_render_identity(self):
        manifest = set(json.loads((ROOT / 'skill-files.json').read_text())['files'])
        notices = (ROOT / 'THIRD_PARTY_NOTICES.md').read_text()
        for face in FACES:
            self.assertIn(f'assets/starter/production-source/fonts/{face}.ttf', manifest)
        for family, label in [('Inter', 'Inter'), ('InstrumentSerif', 'Instrument Serif'), ('JetBrainsMono', 'JetBrains Mono')]:
            license_path = f'assets/starter/production-source/fonts/{family}-OFL.txt'
            self.assertIn(license_path, manifest)
            self.assertIn('SIL Open Font License', (ROOT / license_path).read_text())
            self.assertIn(label, notices)
        declared = json.loads(self.node("process.stdout.write(JSON.stringify(require('./design.cjs').FONT_FILES))").stdout)
        self.assertEqual(sorted(declared), sorted(f'production-source/fonts/{face}.ttf' for face in FACES))
        helper = PRODUCTION / 'render-sources.cjs'
        mechanical = json.loads(subprocess.check_output(['node', str(helper), str(self.project('plain', '--demo'))]))
        designed = json.loads(subprocess.check_output(['node', str(helper), str(self.project('designed', '--design-demo'))]))
        self.assertFalse(any('/fonts/' in name for name in mechanical))
        self.assertTrue(set(declared) <= set(designed))
        self.assertIn('production-source/templates.cjs', designed)

    def test_generator_installs_one_example_at_a_time(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/new_project.py'), str(self.base / 'both'), '--demo', '--design-demo'],
                                capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.base / 'both').exists())
        project = self.project('designed', '--design-demo')
        subprocess.run([sys.executable, str(ROOT / 'scripts/validate_project.py'), str(project)], check=True, capture_output=True)
        sheet = json.loads((project / 'visual-beat-sheet/beat-sheet.json').read_text())
        self.assertTrue(all(beat['design']['template'] and beat['design']['triggers'] for beat in sheet['lessons'][0]['beats']))

    def test_token_lint_applies_only_to_design_system_worlds(self):
        self.assertEqual(design_checks.design_token_findings(self.project('plain', '--demo')), [])
        project = self.project('designed', '--design-demo')
        self.assertEqual(design_checks.design_token_findings(project), [])
        world = project / 'production-source/world.cjs'
        lines = world.read_text().splitlines()
        world.write_text('\n'.join(lines + ["// '#ff0000' in a comment is ignored",
                                            "const stray='#ff0000';", "function font(g){g.font='12px Arial';}"]) + '\n')
        self.assertEqual(design_checks.design_token_findings(project),
                         [f'production-source/world.cjs:{len(lines) + 2}', f'production-source/world.cjs:{len(lines) + 3}'])

    def test_illustrations_draw_on_the_design_stage(self):
        self.node("""
const assert=require('node:assert/strict'),canvas=require(process.env.CANVAS_MODULE),D=require('./design.cjs');
D.installDesignRuntime(canvas);
const {createIllustration}=require('./illustrations.cjs');
const S=D.createDesignStage(canvas.createCanvas(1280,720).getContext('2d'),{width:1280,height:720});
const v=createIllustration(S);v.person('p',300,300,1);v.document('d',600,300,1);S.label('l','Label',640,500);
const r=S.finish();assert.deepEqual(r.items.map(i=>i.id),['p','d','l']);assert.equal(r.transition,false);
""", self.canvas_environment())

    def test_design_demo_audits_clean_and_follows_retimed_narration(self):
        env = self.canvas_environment()
        project = self.project('designed', '--design-demo')
        result, report = self.audit(project, env)
        self.assertEqual(result.returncode, 0, result.stderr)
        lesson = report['lessons'][0]
        self.assertEqual(report['unresolvedPairs'], 0)
        self.assertEqual(len(lesson['intentional']), 6)
        self.assertTrue(0 < lesson['transitionFrames'] < lesson['frames'] * .1)
        self.assertIn('production-source/fonts/Inter-Bold.ttf', report['sourceHashes'])
        for rate in (2.2, 3.4):
            with self.subTest(rate=rate):
                retime(project, rate)
                result, report = self.audit(project, env)
                self.assertEqual(result.returncode, 0, json.dumps(report['lessons'][0]['unresolved'])[:600])

    def test_too_short_narration_fails_the_template_fit(self):
        env = self.canvas_environment()
        project = self.project('designed', '--design-demo')
        retime(project, 6)
        result, report = self.audit(project, env)
        self.assertNotEqual(result.returncode, 0)
        failures = {(item['type'], item['a']) for item in report['lessons'][0]['unresolved']}
        self.assertIn(('mechanism-invariant', 'fit-lineStory'), failures)

    def test_scene_scoped_overlap_rules_must_name_a_scene(self):
        env = self.canvas_environment()
        project = self.project('designed', '--design-demo')
        rules = project / 'production-source/intentional-overlaps.json'
        data = json.loads(rules.read_text())
        data[0]['scene'] = 'absent'
        rules.write_text(json.dumps(data))
        result = subprocess.run(['node', str(project / 'production-source/audit.cjs')], env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Invalid intentional-overlap rule', result.stderr)


if __name__ == '__main__':
    unittest.main()
