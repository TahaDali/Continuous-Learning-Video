"""One lesson's picture is drawn once, copied into the narrated video, and redone only when it changed."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parent.parent
PRODUCTION = ROOT / 'assets/starter/production-source'
OWN = "'use strict';\n// A lesson's own module; the shared mechanism stays in world.cjs.\nmodule.exports={draw:require('../world.cjs').draw};\n"


@unittest.skipUnless(shutil.which('node') and shutil.which('ffmpeg'), 'Node.js and FFmpeg are required')
class LessonScopeTests(unittest.TestCase):
    def setUp(self):
        module = os.environ.get('CANVAS_MODULE') or str(PRODUCTION / 'node_modules/@napi-rs/canvas')
        if not Path(module).is_dir():
            self.skipTest('Canvas runtime is not configured')
        self.env = dict(os.environ, CANVAS_MODULE=module)
        temporary = tempfile.TemporaryDirectory(prefix='lesson-scope-test-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'course'
        subprocess.run([sys.executable, str(ROOT / 'scripts/new_project.py'), str(self.root), '--demo'], check=True, capture_output=True)
        self.data = json.loads((self.root / 'course.json').read_text())
        # Two two-second lessons that share the starter's mechanical world through their own modules.
        lesson = self.data['lessons'][0]
        for scene in lesson['scenes']:
            scene.update(start=round(scene['start'] / 6, 4), end=round(scene['end'] / 6, 4))
        lesson['duration'] = 2
        self.data['lessons'] = [lesson, dict(copy.deepcopy(lesson), id='02', title='A second fictional lesson')]
        self.save()
        self.production = self.root / 'production-source'
        (self.production / 'worlds').mkdir()
        for name in ('01', '02'):
            (self.production / 'worlds' / (name + '.cjs')).write_text(OWN)

    def save(self):
        (self.root / 'course.json').write_text(json.dumps(self.data, indent=2) + '\n')

    def node(self, script, *arguments, check=True):
        result = subprocess.run(['node', str(self.production / script), *arguments], env=self.env, capture_output=True, text=True)
        if check:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def sources(self, *lesson, project=None):
        result = subprocess.run(['node', str(PRODUCTION / 'render-sources.cjs'), str(project or self.root), *lesson],
                                capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    def audit(self, *arguments):
        self.node('audit.cjs', *arguments)
        return json.loads((self.root / 'review/frame-audit.json').read_text())

    def narration(self):
        """Silent audio and one caption per lesson: enough for the mechanical narrated encode."""
        for lesson in self.data['lessons']:
            with wave.open(str(self.root / 'audio' / (lesson['id'] + '.wav')), 'wb') as audio:
                audio.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
                audio.writeframes(b'\0' * round(48000 * lesson['duration']))
            (self.root / 'player/captions' / (lesson['id'] + '.srt')).write_text('1\n00:00:00,100 --> 00:00:01,900\nSynthetic caption.\n')

    def stream_hash(self, video):
        return subprocess.run(['ffmpeg', '-v', 'error', '-i', str(video), '-map', '0:v:0', '-c', 'copy', '-f', 'hash', '-hash', 'sha256', '-'],
                              capture_output=True, text=True, check=True).stdout.strip()

    def test_each_lesson_depends_on_its_own_module_only(self):
        everything = self.sources()
        for name in ('production-source/world.cjs', 'production-source/worlds/01.cjs', 'production-source/worlds/02.cjs',
                     'production-source/lesson-scope.cjs'):
            self.assertIn(name, everything)
        first = self.sources('01')
        self.assertIn('production-source/worlds/01.cjs', first)
        self.assertIn('production-source/world.cjs', first)          # required by the lesson's module
        self.assertNotIn('production-source/worlds/02.cjs', first)
        # A lesson without its own module is drawn by world.cjs and carries no other lesson's module.
        (self.production / 'worlds/02.cjs').unlink()
        self.assertNotIn('production-source/worlds/01.cjs', self.sources('02'))

    def test_a_project_without_the_scope_module_keeps_one_world(self):
        # Projects created before per-lesson modules keep their renderer's own discovery.
        (self.production / 'lesson-scope.cjs').unlink()
        self.assertNotIn('production-source/worlds/01.cjs', self.sources())

    def test_the_narrated_video_copies_the_reviewed_picture(self):
        self.narration()
        first = self.node('render.cjs', 'all', '--silent-preview')
        self.assertIn('01: 48 frames', first.stdout)
        silent = {name: (self.root / 'review/silent' / (name + '.mp4')).read_bytes() for name in ('01', '02')}
        final = self.node('render.cjs', 'all')
        for name in ('01', '02'):
            self.assertIn(f'{name}: picture is current, not redrawn', final.stdout)
            video = self.root / 'player/videos' / (name + '.mp4')
            self.assertEqual((self.root / 'review/silent' / (name + '.mp4')).read_bytes(), silent[name])
            # The delivered picture is the reviewed picture, packet for packet.
            self.assertEqual(self.stream_hash(video), self.stream_hash(self.root / 'review/silent' / (name + '.mp4')))
            streams = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(video)],
                                                capture_output=True, text=True, check=True).stdout)['streams']
            self.assertEqual([s['codec_name'] for s in streams], ['h264', 'aac', 'mov_text'])

    def test_narrated_render_needs_audio_and_captions(self):
        result = self.node('render.cjs', '01', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Measured audio and captions required', result.stderr)

    def test_only_a_changed_lesson_is_redrawn_and_audited_again(self):
        self.node('render.cjs', 'all', '--silent-preview')
        report = self.audit()
        self.assertEqual([lesson.get('reused') for lesson in report['lessons']], [None, None])
        self.assertEqual([lesson.get('reused') for lesson in self.audit()['lessons']], [True, True])
        own = self.production / 'worlds/02.cjs'
        own.write_text(own.read_text() + '// A fix confined to lesson 02.\n')
        again = self.node('render.cjs', 'all', '--silent-preview')
        self.assertIn('01: picture is current, not redrawn', again.stdout)
        self.assertIn('02: 48 frames', again.stdout)
        report = self.audit()
        self.assertEqual([lesson.get('reused') for lesson in report['lessons']], [True, None])
        self.assertEqual(report['totalFrames'], 96)
        self.assertEqual(report['unresolvedPairs'], 0)
        # The report still identifies every current source, and --force replays every lesson.
        self.assertEqual(set(report['sourceHashes']) - {'course.json', 'production-source/intentional-overlaps.json'}, set(self.sources()))
        self.assertEqual([lesson.get('reused') for lesson in self.audit('--force')['lessons']], [None, None])

    def test_a_lesson_audited_alone_touches_only_its_own_files_and_is_kept_by_the_course_audit(self):
        alone = self.node('audit.cjs', '--lesson', '02')
        self.assertEqual(alone.stdout.strip(), '02: 48 frames, 0 unresolved, 0 intentional')
        review = self.root / 'review'
        self.assertEqual(sorted(p.name for p in review.iterdir()), ['lesson-audits'])
        self.assertEqual([p.name for p in (review / 'lesson-audits').iterdir()], ['02.json'])
        # The course audit replays only the lesson nobody audited, and reports both.
        report = self.audit()
        self.assertEqual([(lesson['id'], lesson.get('reused')) for lesson in report['lessons']], [('01', None), ('02', True)])
        self.assertEqual(report['totalFrames'], 96)
        # A lesson's findings are printed with their frames, and never vouch for the lesson afterwards.
        (self.production / 'worlds/02.cjs').write_text(
            "exports.draw=()=>({items:[{id:'a',kind:'actor',bounds:{x:100,y:100,w:200,h:200},alpha:1},"
            "{id:'b',kind:'actor',bounds:{x:200,y:200,w:200,h:200},alpha:1}],"
            "viewport:{x:0,y:0,w:1280,h:720},safe:{x:0,y:0,w:1280,h:720}});\n")
        failed = self.node('audit.cjs', '--lesson', '02', check=False)
        self.assertEqual(failed.returncode, 1)
        self.assertIn('  intersection a / b: frames 0-47 -> review/lesson-audits/02-flagged/02-0-0.png', failed.stdout)
        self.assertTrue((review / 'lesson-audits/02-flagged/02-0-0.png').is_file())
        self.node('audit.cjs', check=False)
        report = json.loads((review / 'frame-audit.json').read_text())
        self.assertEqual([(lesson['id'], lesson.get('reused'), len(lesson['unresolved'])) for lesson in report['lessons']],
                         [('01', True, 0), ('02', None, 1)])
        unknown = self.node('audit.cjs', '--lesson', '09', check=False)
        self.assertNotEqual(unknown.returncode, 0)
        self.assertIn('No lesson 09', unknown.stderr)

    def test_retiming_one_lesson_leaves_the_other_current(self):
        self.node('render.cjs', 'all', '--silent-preview')
        self.audit()
        second = self.data['lessons'][1]
        second['scenes'][-1]['end'] = second['duration'] = 2.25
        self.save()
        again = self.node('render.cjs', 'all', '--silent-preview')
        self.assertIn('01: picture is current, not redrawn', again.stdout)
        self.assertIn('02: 54 frames', again.stdout)
        self.assertEqual([lesson.get('reused') for lesson in self.audit()['lessons']], [True, None])

    def test_shared_changes_redraw_every_lesson(self):
        self.node('render.cjs', 'all', '--silent-preview')
        self.audit()
        for change in ('module', 'title'):
            with self.subTest(change=change):
                if change == 'module':
                    shared = self.production / 'world.cjs'
                    shared.write_text(shared.read_text() + '// A change to the shared mechanism.\n')
                else:
                    # Another lesson's title may be drawn, so it belongs to every lesson's identity.
                    self.data['lessons'][0]['title'] = 'Renamed'
                    self.save()
                again = self.node('render.cjs', 'all', '--silent-preview')
                self.assertNotIn('picture is current', again.stdout)
                self.assertEqual([lesson.get('reused') for lesson in self.audit()['lessons']], [None, None])

    def test_a_replaced_or_interrupted_picture_is_never_treated_as_current(self):
        self.node('render.cjs', '01', '--silent-preview')
        picture = self.root / 'review/silent/01.mp4'
        picture.write_bytes(picture.read_bytes() + b'changed after rendering')
        self.assertIn('01: 48 frames', self.node('render.cjs', '01', '--silent-preview').stdout)
        # A world that fails part-way leaves no record that could vouch for the partial file.
        own = self.production / 'worlds/01.cjs'
        own.write_text("const {draw}=require('../world.cjs');module.exports={draw:(g,l,t,c)=>{if(t>.5)throw new Error('authored failure');return draw(g,l,t,c);}};\n")
        failed = self.node('render.cjs', '01', '--silent-preview', check=False)
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn('authored failure', failed.stderr)
        self.assertFalse((self.root / 'review/silent/01.picture.json').exists())
        self.assertIn('picture is current', self.node('render.cjs', '02', '--silent-preview').stdout + self.node('render.cjs', '02', '--silent-preview').stdout)

    def test_force_and_parallel_jobs_render_every_selected_lesson(self):
        first = self.node('render.cjs', 'all', '--silent-preview', '--jobs', '2')
        self.assertIn('01: 48 frames', first.stdout)
        self.assertIn('02: 48 frames', first.stdout)
        forced = self.node('render.cjs', 'all', '--silent-preview', '--force', '--jobs', '1')
        self.assertNotIn('picture is current', forced.stdout)
        self.assertNotEqual(self.node('render.cjs', 'all', '--jobs', 'none', check=False).returncode, 0)

    def test_a_lesson_cannot_depend_on_another_lessons_scenes_or_timing(self):
        own = self.production / 'worlds/01.cjs'
        for field, access in (('scenes', 'c.lessons[1].scenes.length'), ('duration', 'c.lessons[1].duration')):
            with self.subTest(field=field):
                own.write_text("const {draw}=require('../world.cjs');module.exports={draw:(g,l,t,c)=>{" + access + ";return draw(g,l,t,c);}};\n")
                result = self.node('render.cjs', '01', '--silent-preview', check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f'Lesson 01 read {field} of lesson 02', result.stderr)
        # Descriptive fields of other lessons, and the lesson's own record, stay readable.
        own.write_text("const {draw}=require('../world.cjs');module.exports={draw:(g,l,t,c)=>{"
                       "if(c.lessons[1].title!=='A second fictional lesson'||c.lessons[0]!==l||!l.scenes.length)throw new Error('lost context');"
                       "return draw(g,l,t,c);}};\n")
        self.node('render.cjs', '01', '--silent-preview')
        self.node('render.cjs', 'posters')
        self.assertTrue((self.root / 'player/posters/02.png').is_file())

    def test_a_lessons_own_overlap_rules_apply_to_that_lesson_only(self):
        overlapping = ("exports.draw=()=>({items:[{id:'a',kind:'actor',bounds:{x:100,y:100,w:200,h:200},alpha:1},"
                       "{id:'b',kind:'actor',bounds:{x:200,y:200,w:200,h:200},alpha:1}],"
                       "viewport:{x:0,y:0,w:1280,h:720},safe:{x:0,y:0,w:1280,h:720}});\n")
        for name in ('01', '02'):
            (self.production / 'worlds' / (name + '.cjs')).write_text(overlapping)
        rules = self.production / 'worlds/01.overlaps.json'
        rules.write_text(json.dumps([{'a': 'a', 'b': 'b', 'start': 0, 'end': 2, 'reason': 'Fixture: the two objects are meant to touch.'}]))
        self.assertIn('production-source/worlds/01.overlaps.json', self.sources('01'))
        self.assertNotIn('production-source/worlds/01.overlaps.json', self.sources('02'))
        result = self.node('audit.cjs', check=False)
        self.assertEqual(result.returncode, 1)
        report = json.loads((self.root / 'review/frame-audit.json').read_text())
        self.assertEqual([len(lesson['intentional']) for lesson in report['lessons']], [1, 0])
        self.assertEqual([len(lesson['unresolved']) for lesson in report['lessons']], [0, 1])
        self.assertIn('production-source/worlds/01.overlaps.json', report['sourceHashes'])
        # A lesson with findings is audited again next time; the clean one is kept.
        self.node('audit.cjs', check=False)
        report = json.loads((self.root / 'review/frame-audit.json').read_text())
        self.assertEqual([lesson.get('reused') for lesson in report['lessons']], [True, None])
        rules.write_text(json.dumps([{'lesson': '02', 'a': 'a', 'b': 'b', 'start': 0, 'end': 2, 'reason': 'Fixture.'}]))
        refused = self.node('audit.cjs', check=False)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('names another lesson', refused.stderr)


if __name__ == '__main__':
    unittest.main()
