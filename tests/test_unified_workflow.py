"""Exercise the built single skill in isolation using explicitly fictional course fixtures."""
import importlib.util
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from build_skill import build
from media_fixture import media_fixture, narration_fixture, render


class UnifiedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='unified-skill-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.skill = build(self.base / 'continuous-learning-video')
        spec = importlib.util.spec_from_file_location('unified_workflow', self.skill / 'scripts/workflow.py')
        self.workflow = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.workflow)
        self.root = self.base / 'working-project'
        self.workflow.init(self.root, 'https://example.org/jobs/fictional-fixture')

    def seed_research(self):
        w = self.workflow
        date = '2026-10-20T12:00:00+00:00'
        w.write(self.root / 'job.json', {'url': 'https://example.org/jobs/fictional-fixture', 'status': 'verified',
                'retrievedAt': date, 'employer': 'Fictional test employer', 'title': 'Fixture analyst',
                'requirements': [{'id': 'r1', 'text': 'Explain a conserved transfer', 'kind': 'responsibility'}]})
        w.write(self.root / 'sources.json', {'sources': [
            {'id': 's1', 'title': 'Synthetic public fixture', 'url': 'https://example.org', 'accessedAt': date, 'publish': True},
            {'id': 's2', 'title': 'Private fixture', 'url': None, 'accessedAt': date, 'publish': False,
             'privateText': 'PRIVATE_FIXTURE_MUST_NOT_EXPORT'}],
             'claims': [{'id': 'c1', 'text': 'Fictional transfer example', 'kind': 'fiction', 'sourceIds': ['s1']}]})
        w.record(self.root, 'research')

    def seed_curriculum(self):
        self.seed_research()
        self.workflow.write(self.root / 'curriculum.json', {'objectives': [
            {'id': 'o1', 'text': 'Explain the conserved quantity', 'requirementIds': ['r1']}],
            'lessons': [{'id': '01', 'title': 'Fictional transfer', 'objectiveIds': ['o1'], 'claimIds': ['c1']}], 'exclusions': []})
        self.workflow.record(self.root, 'curriculum')

    def save(self):
        self.workflow.write(self.root / 'course.json', self.data)
        self.workflow.write(self.root / 'visual-beat-sheet/beat-sheet.json', self.sheet)
        (self.root / 'player/course-data.js').write_text('window.COURSE = ' + json.dumps(self.data) + ';')

    def seed_design(self):
        """Synthetic schema evidence, explicitly not a perceptual quality review."""
        w = self.workflow
        # Tests opt into the mechanical demonstration; actual new projects cannot.
        shutil.copyfile(self.skill / 'assets/starter/production-source/world.cjs', self.root / 'production-source/world.cjs')
        (self.root / 'manuscript.md').write_text('# Synthetic mechanical fixture\n\n## Transfer\n\nNot a researched employer course.\n')
        w.write(self.root / 'narrative-map.json', {
            'parts': [{'id': 'p1', 'title': 'Fixture', 'question': 'What is conserved?'}],
            'chapters': [{'id': 'c1', 'partId': 'p1', 'heading': '## Transfer', 'lessonIds': ['01'],
                          'retainedDecisions': ['Retain the total'], 'adaptation': 'Synthetic schema fixture only'}]})
        w.write(self.root / 'review/editorial.json', {'status': 'completed', 'reviewer': 'Synthetic fixture',
            'findings': [{'partId': 'p1', 'chapterId': 'c1', 'observation': 'Schema fixture only; no teaching-quality claim.'}]})
        w.write(self.root / 'visual-design.json', {'mechanisms': [{'id': 'transfer', 'lessonIds': ['01'],
            'question': 'Does the total stay fixed?', 'states': [{'id': 'a', 'meaning': 'Before'}, {'id': 'b', 'meaning': 'After'}],
            'transitions': [{'from': 'a', 'to': 'b', 'trigger': 'Transfer', 'change': 'Amount moves', 'invariant': 'Total remains fixed'}]}]})
        clip = self.root / 'review/fixture-clip.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=teal:s=32x24:r=8',
                        '-frames:v', '4', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-threads', '1',
                        '-an', '-y', str(clip)], check=True, capture_output=True)
        hashes = {name: hashlib.sha256((self.root / name).read_bytes()).hexdigest()
                  for name in w.renderer_sources(self.root)}
        w.write(self.root / 'review/prototypes.json', {'status': 'completed', 'reviewer': 'Synthetic fixture',
            'worldSha256': hashes['production-source/world.cjs'], 'sourceHashes': hashes,
            'clips': [{'mechanismId': 'transfer', 'path': 'review/fixture-clip.mp4',
                       'observation': 'Generated silent media/schema fixture only; no perceptual review.'}]})

    def design_checks(self):
        spec = importlib.util.spec_from_file_location('fixture_design_checks', self.skill / 'scripts/design_checks.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_missing_parent_chapter_is_rejected(self):
        self.seed_design()
        (self.root / 'manuscript.md').write_text('# Missing mapped chapter\n')
        with self.assertRaisesRegex(ValueError, 'heading is missing'):
            self.design_checks().script(self.root, {'01'})

    def test_unassigned_narrative_lesson_is_rejected(self):
        self.seed_design()
        with self.assertRaisesRegex(ValueError, 'leaves lessons unassigned'):
            self.design_checks().script(self.root, {'01', '02'})

    def test_real_positive_duration_video_prototype_is_accepted(self):
        self.seed_design()
        paths = self.design_checks().visuals(self.root, {'01'})
        self.assertIn('review/fixture-clip.mp4', paths)

    def test_nonvideo_disguised_as_prototype_is_rejected(self):
        self.seed_design()
        (self.root / 'review/fixture-clip.mp4').write_bytes(b'Not video: a saved review form is not a clip.')
        with self.assertRaisesRegex(ValueError, 'positive-duration video stream'):
            self.design_checks().visuals(self.root, {'01'})

    def test_audio_only_prototype_is_rejected(self):
        self.seed_design()
        clip = self.root / 'review/fixture-audio.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=8000:cl=mono',
                        '-t', '0.5', '-y', str(clip)], check=True, capture_output=True)
        review = self.workflow.read(self.root / 'review/prototypes.json')
        review['clips'][0]['path'] = 'review/fixture-audio.wav'
        self.workflow.write(self.root / 'review/prototypes.json', review)
        with self.assertRaisesRegex(ValueError, 'positive-duration video stream'):
            self.design_checks().visuals(self.root, {'01'})

    def test_changed_motion_invalidates_prototype_review(self):
        self.seed_design()
        with (self.root / 'production-source/motion.cjs').open('a') as handle:
            handle.write('\n// Changed after prototype inspection\n')
        with self.assertRaisesRegex(ValueError, 'stale after a render dependency change'):
            self.design_checks().visuals(self.root, {'01'})

    def test_changed_canvas_guard_invalidates_prototype_review(self):
        self.seed_design()
        guard = self.root / 'production-source/finite-canvas.cjs'
        report = self.workflow.read(self.root / 'review/prototypes.json')
        self.assertIn('production-source/finite-canvas.cjs', report['sourceHashes'])
        guard.write_text(guard.read_text() + '\n// Guard contract changed after review.\n')
        with self.assertRaisesRegex(ValueError, 'stale after a render dependency change'):
            self.design_checks().visuals(self.root, {'01'})

    def test_changed_motion_invalidates_recorded_visuals(self):
        self.seed_curriculum()
        self.data = self.workflow.read(self.skill / 'assets/starter/course.json')
        self.sheet = self.workflow.read(self.skill / 'assets/starter/visual-beat-sheet/beat-sheet.json')
        self.save()
        self.seed_design()
        self.workflow.record(self.root, 'script')
        self.workflow.record(self.root, 'visuals')
        with (self.root / 'production-source/motion.cjs').open('a') as handle:
            handle.write('\n// Changed after recorded prototype inspection\n')
        self.assertEqual(self.workflow.state(self.root)[1]['visuals'], 'stale')
        with self.assertRaisesRegex(ValueError, 'visuals'):
            self.workflow.record(self.root, 'media')

    def seed_script(self):
        self.seed_curriculum()
        self.data = self.workflow.read(self.skill / 'assets/starter/course.json')
        self.sheet = self.workflow.read(self.skill / 'assets/starter/visual-beat-sheet/beat-sheet.json')
        self.save()
        self.seed_design()
        self.workflow.record(self.root, 'script')

    def test_narration_and_visuals_follow_the_script_in_either_order(self):
        self.seed_script()
        statuses = self.workflow.state(self.root)[1]
        self.assertEqual(list(statuses), ['research', 'curriculum', 'script', 'narration', 'visuals', 'media',
                                          'review', 'package', 'delivery'])
        # Narration first: measured timing exists before any world is recorded.
        narration_fixture(self, 12)
        readable = self.root / 'visual-beat-sheet/beat-sheet.md'
        statuses = self.workflow.record(self.root, 'narration')
        self.assertEqual((statuses['script'], statuses['narration'], statuses['visuals']), ('completed', 'completed', 'pending'))
        self.assertFalse(readable.exists())            # the readable sheet needs the visual fields
        with self.assertRaisesRegex(ValueError, 'upstream stages: visuals'):
            self.workflow.record(self.root, 'media')
        statuses = self.workflow.record(self.root, 'visuals')
        self.assertEqual((statuses['narration'], statuses['visuals']), ('completed', 'completed'))
        self.assertIn('measured synthetic fixture', readable.read_text())
        # Recording either one again leaves the other in place; recording the script clears both.
        self.assertEqual(self.workflow.record(self.root, 'narration')['visuals'], 'completed')
        self.assertEqual(self.workflow.record(self.root, 'visuals')['narration'], 'completed')
        statuses = self.workflow.record(self.root, 'script')
        self.assertEqual((statuses['narration'], statuses['visuals']), ('pending', 'pending'))

    def test_a_visual_change_does_not_invalidate_recorded_narration(self):
        self.seed_script()
        narration_fixture(self, 12)
        self.workflow.record(self.root, 'narration')
        self.workflow.record(self.root, 'visuals')
        with (self.root / 'production-source/motion.cjs').open('a') as handle:
            handle.write('\n// A visual fix after narration was measured\n')
        statuses = self.workflow.state(self.root)[1]
        self.assertEqual((statuses['narration'], statuses['visuals'], statuses['media']), ('completed', 'stale', 'pending'))
        # A narration change invalidates narration, not the visual plan, whose fingerprint ignores timing.
        self.refresh_prototype_identity()
        self.workflow.record(self.root, 'visuals')
        self.data['lessons'][0]['scenes'][0]['wordTimings'][0]['end'] += .01
        self.save()
        statuses = self.workflow.state(self.root)[1]
        self.assertEqual((statuses['script'], statuses['narration'], statuses['visuals']), ('completed', 'stale', 'completed'))

    def test_per_lesson_course_runs_from_untimed_scripts_to_export_and_a_one_lesson_fix(self):
        """The documented order: scripts, sync, narration, per-lesson worlds, one render, export."""
        w, date = self.workflow, '2026-10-20T12:00:00+00:00'
        self.seed_research()
        w.write(self.root / 'curriculum.json', {'objectives': [{'id': 'o1', 'text': 'Explain the conserved quantity', 'requirementIds': ['r1']}],
            'lessons': [{'id': i, 'title': 'Fictional transfer ' + i, 'objectiveIds': ['o1'], 'claimIds': ['c1']} for i in ('01', '02')],
            'exclusions': []})
        w.record(self.root, 'curriculum')
        # Scripts as an author leaves them: narration and headlines, no timing, no beat sheet.
        starter = w.read(self.skill / 'assets/starter/course.json')
        authored = w.read(self.skill / 'assets/starter/visual-beat-sheet/beat-sheet.json')['lessons'][0]
        lesson = {k: v for k, v in starter['lessons'][0].items() if k != 'duration'}
        lesson['scenes'] = [{k: v for k, v in scene.items() if k not in {'start', 'end'}} for scene in lesson['scenes']]
        course = w.read(self.root / 'course.json')
        course['lessons'] = [dict(json.loads(json.dumps(lesson)), id=i) for i in ('01', '02')]
        w.write(self.root / 'course.json', course)
        report = w.sync(self.root, split=True)
        self.assertEqual((report['cues'], report['estimatedTiming'], report['toAuthor']), (6, ['01', '02'], ['01', '02']))
        (self.root / 'manuscript.md').write_text('# Synthetic mechanical fixture\n\n## Transfer\n\nNot a researched employer course.\n')
        w.write(self.root / 'narrative-map.json', {
            'parts': [{'id': 'p1', 'title': 'Fixture', 'question': 'What is conserved?'}],
            'chapters': [{'id': 'c1', 'partId': 'p1', 'heading': '## Transfer', 'lessonIds': ['01', '02'],
                          'retainedDecisions': ['Retain the total'], 'adaptation': 'Synthetic schema fixture only'}]})
        w.write(self.root / 'review/editorial.json', {'status': 'completed', 'reviewer': 'Synthetic fixture',
            'findings': [{'partId': 'p1', 'chapterId': 'c1', 'observation': 'Schema fixture only; no teaching-quality claim.'}]})
        w.record(self.root, 'script')

        # Narration before any world exists: the project's own finalize() on cached synthetic blocks.
        sys.path.insert(0, str(self.root / 'production-source'))
        spec = importlib.util.spec_from_file_location('fixture_narrate', self.root / 'production-source/narrate.py')
        narrate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(narrate)
        import wave
        data, sheet = w.read(self.root / 'course.json'), w.read(self.root / 'visual-beat-sheet/beat-sheet.json')
        for item in data['lessons']:
            for beat in item['scenes']:
                words, at = [], .05
                for token in beat['narration'].split():
                    text = token.strip('.,')
                    start = beat['narration'].index(text, words[-1]['charEnd'] if words else 0)
                    words.append({'text': text, 'charStart': start, 'charEnd': start + len(text), 'start': round(at, 3), 'end': round(at + .2, 3)})
                    at += .3
                stem = narrate.stem_for(item, beat)
                (self.root / 'audio' / (stem + '.words.json')).write_text(json.dumps({'words': words}))
                with wave.open(str(self.root / 'audio' / (stem + '.wav')), 'wb') as audio:
                    audio.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
                    audio.writeframes(b'\0' * (round(at * 24000) * 2))
        narrate.finalize(data, sheet, self.root, 'synthetic-fixture')
        statuses = w.record(self.root, 'narration')
        self.assertEqual((statuses['script'], statuses['narration'], statuses['visuals']), ('completed', 'completed', 'pending'))

        # Visuals: one module and one beat-sheet file per lesson; the shared mechanism is defined once.
        production = self.root / 'production-source'
        shutil.copyfile(self.skill / 'assets/starter/production-source/world.cjs', production / 'shared.cjs')
        (production / 'worlds').mkdir()
        for i in ('01', '02'):
            (production / 'worlds' / (i + '.cjs')).write_text("'use strict';\nmodule.exports={draw:require('../shared.cjs').draw};\n")
            own = self.root / 'visual-beat-sheet/lessons' / (i + '.json')
            entry = w.read(own)
            self.assertEqual(entry['context']['title'], lesson['title'])
            for beat, planned in zip(entry['beats'], authored['beats'], strict=True):
                self.assertTrue(beat['cues'][0]['timingMethod'].startswith('measured'))
                beat['cues'][0].update({k: v for k, v in planned['cues'][0].items() if k not in {'text', 'start', 'end', 'timingMethod'}})
            w.write(own, entry)
        report = w.sync(self.root)
        self.assertEqual((report['missingVisualFields'], report['estimatedTiming'], report['narrationChangedSinceMeasured']), (0, [], []))
        self.assertEqual(w.state(self.root)[1]['narration'], 'completed')      # syncing leaves measured narration alone
        w.write(self.root / 'visual-design.json', {'mechanisms': [{'id': 'transfer', 'lessonIds': ['01', '02'],
            'question': 'Does the total stay fixed?', 'states': [{'id': 'a', 'meaning': 'Before'}, {'id': 'b', 'meaning': 'After'}],
            'transitions': [{'from': 'a', 'to': 'b', 'trigger': 'Transfer', 'change': 'Amount moves', 'invariant': 'Total remains fixed'}]}]})
        clip = self.root / 'review/fixture-clip.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=teal:s=32x24:r=8', '-frames:v', '4', '-c:v', 'libx264',
                        '-pix_fmt', 'yuv420p', '-threads', '1', '-an', '-y', str(clip)], check=True, capture_output=True)
        w.write(self.root / 'review/prototypes.json', {'status': 'completed', 'reviewer': 'Synthetic fixture', 'worldSha256': '', 'sourceHashes': {},
            'clips': [{'mechanismId': 'transfer', 'path': 'review/fixture-clip.mp4', 'observation': 'Generated silent media/schema fixture only.'}]})
        self.refresh_prototype_identity()
        w.record(self.root, 'visuals')
        fingerprints = w.read(self.root / 'project.json')['stages']['visuals']['fingerprints']
        for name in ('production-source/worlds/01.cjs', 'production-source/worlds/02.cjs', 'production-source/shared.cjs',
                     'production-source/lesson-scope.cjs'):
            self.assertIn(name, fingerprints)

        # Media: one render writes the pictures and the narrated files; the audit covers both lessons.
        self.data = None
        first = render(self)
        self.assertIn('01: picture, narration and captions', first.stdout)
        env = dict(os.environ)
        if not env.get('CANVAS_MODULE'):
            env['CANVAS_MODULE'] = str(ROOT / 'assets/starter/production-source/node_modules/@napi-rs/canvas')
        def node(script, *arguments):
            return subprocess.run(['node', str(production / script), *arguments], env=env, check=True, capture_output=True, text=True)
        node('render.cjs', 'posters')
        node('audit.cjs')
        w.record(self.root, 'media')
        w.write(self.root / 'review/acceptance.json', {
            key: {'status': 'pending', 'coverage': 'Synthetic fixture; no perceptual review performed.'}
            for key in ('content', 'listening', 'synchronizedViewing', 'silentInspection')})
        w.record(self.root, 'review')
        output = self.base / 'export'
        w.export(self.root, output)
        self.assertEqual(sorted(p.name for p in (output / 'videos').iterdir()), ['01.mp4', '02.mp4'])
        exported = json.loads((output / 'course-data.js').read_text()[len('window.COURSE = '):-2])
        self.assertEqual(set(exported['lessons'][1]['scenes'][0]), {'id', 'headline', 'narration', 'start', 'end'})

        # A fix confined to lesson 02 redraws and replays lesson 02 only, and the checkpoints accept it.
        own = production / 'worlds/02.cjs'
        own.write_text(own.read_text() + '// A fix confined to this lesson.\n')
        statuses = w.state(self.root)[1]
        self.assertEqual((statuses['narration'], statuses['visuals'], statuses['media']), ('completed', 'stale', 'stale'))
        self.refresh_prototype_identity()
        w.record(self.root, 'visuals')
        again = render(self)
        self.assertIn('01: picture is current, not redrawn', again.stdout)
        self.assertNotIn('02: picture is current', again.stdout)
        self.assertIn('01: ', node('audit.cjs').stdout.splitlines()[0])
        audit = w.read(self.root / 'review/frame-audit.json')
        self.assertEqual([item.get('reused') for item in audit['lessons']], [True, None])
        self.assertEqual(w.record(self.root, 'media')['media'], 'completed')

    def test_changed_declared_renderer_helper_invalidates_review(self):
        self.seed_design()
        w = self.workflow
        course = w.read(self.root / 'course.json')
        course['renderSources'] = ['production-source/fixture-helper.cjs']
        w.write(self.root / 'course.json', course)
        helper = self.root / course['renderSources'][0]
        helper.write_text('// Synthetic renderer dependency\n')
        review = w.read(self.root / 'review/prototypes.json')
        review['sourceHashes'][course['renderSources'][0]] = hashlib.sha256(helper.read_bytes()).hexdigest()
        w.write(self.root / 'review/prototypes.json', review)
        self.design_checks().visuals(self.root, {'01'})
        helper.write_text('// Changed after prototype inspection\n')
        with self.assertRaisesRegex(ValueError, 'stale after a render dependency change'):
            self.design_checks().visuals(self.root, {'01'})

    def test_bundle_is_self_contained(self):
        self.assertTrue((self.skill / 'references/research/chapter-structure.md').is_file())
        self.assertTrue((self.skill / 'references/video/beat-sheet.md').is_file())
        self.assertTrue((self.skill / 'assets/starter/production-source/text_checks.py').is_file())
        self.assertTrue((self.skill / 'assets/starter/production-source/render-sources.cjs').is_file())
        self.assertTrue((self.skill / 'assets/starter/production-source/illustrations.cjs').is_file())
        self.assertEqual(self.workflow.read(self.root / 'course.json')['lessons'], [])
        self.assertFalse(self.workflow.preflight()['serviceRequestsMade'])
        for path in self.skill.rglob('*.md'):
            for link in re.findall(r'\]\(([^\s)]+)\)', path.read_text()):
                if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', link) or link.startswith('#'):
                    continue
                with self.subTest(file=str(path.relative_to(self.skill)), link=link):
                    self.assertTrue((path.parent / unquote(link.split('#', 1)[0])).is_file())

    def test_new_project_cannot_render_the_demo_or_an_unsupported_visual(self):
        world = self.root / 'production-source/world.cjs'
        code = "const {draw}=require(process.argv[1]); for(const visual of ['conserved-transfer','unimplemented']) { try { draw(null,{visual},0,{}); process.exit(2); } catch(e) { if(!e.message.includes('No authored visual world'))throw e; } }"
        result = subprocess.run(['node', '-e', code, str(world)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual(world.read_bytes(), (self.skill / 'assets/starter/production-source/world.cjs').read_bytes())

    def refresh_prototype_identity(self):
        w = self.workflow
        report = w.read(self.root / 'review/prototypes.json')
        report['sourceHashes'] = {name: hashlib.sha256((self.root / name).read_bytes()).hexdigest()
                                  for name in w.renderer_sources(self.root)}
        report['worldSha256'] = report['sourceHashes']['production-source/world.cjs']
        w.write(self.root / 'review/prototypes.json', report)

    def test_transitive_local_helper_changes_invalidate_visuals_without_manual_listing(self):
        self.seed_curriculum()
        self.data = self.workflow.read(self.skill / 'assets/starter/course.json')
        self.sheet = self.workflow.read(self.skill / 'assets/starter/visual-beat-sheet/beat-sheet.json')
        self.save()
        self.seed_design()
        folder = self.root / 'production-source/nested'
        folder.mkdir()
        (folder / 'paint.cjs').write_text("module.exports = require('./tone.json');\n")
        leaf = folder / 'tone.json'
        leaf.write_text('{"color":"#c8e7d8"}\n')
        world = self.root / 'production-source/world.cjs'
        world.write_text(world.read_text().replace("id==='left'?P.mint:P.sand", "id==='left'?authoredTone.color:P.sand")
                         + "\nconst authoredTone = require('./nested/paint.cjs');\n")
        self.assertEqual(self.data.get('renderSources', []), [])
        self.refresh_prototype_identity()
        self.workflow.record(self.root, 'script')
        self.workflow.record(self.root, 'visuals')
        paths = self.workflow.read(self.root / 'project.json')['stages']['visuals']['fingerprints']
        self.assertIn('production-source/nested/paint.cjs', paths)
        self.assertIn('production-source/nested/tone.json', paths)
        if os.environ.get('CANVAS_MODULE'):
            subprocess.run(['node', str(self.root / 'production-source/audit.cjs')], check=True, capture_output=True)
            audit = self.workflow.read(self.root / 'review/frame-audit.json')
            self.assertIn('production-source/nested/tone.json', audit['sourceHashes'])
            self.assertEqual(audit['unresolvedPairs'], 0)
        leaf.write_text('{"color":"#b8513b"}\n')
        self.assertEqual(self.workflow.state(self.root)[1]['visuals'], 'stale')
        with self.assertRaisesRegex(ValueError, 'stale after a render dependency change'):
            self.design_checks().visuals(self.root, {'01'})

    def test_new_module_resolution_target_invalidates_existing_checkpoint(self):
        self.seed_curriculum()
        self.data = self.workflow.read(self.skill / 'assets/starter/course.json')
        self.sheet = self.workflow.read(self.skill / 'assets/starter/visual-beat-sheet/beat-sheet.json')
        self.save()
        self.seed_design()
        (self.root / 'production-source/tone.json').write_text('{"color":"teal"}\n')
        with (self.root / 'production-source/world.cjs').open('a') as handle:
            handle.write("\nconst authoredTone = require('./tone');\n")
        self.refresh_prototype_identity()
        self.workflow.record(self.root, 'script')
        self.workflow.record(self.root, 'visuals')
        # Node now resolves .js before the unchanged .json; old fingerprints alone cannot notice it.
        (self.root / 'production-source/tone.js').write_text("module.exports={color:'red'};\n")
        self.assertEqual(self.workflow.state(self.root)[1]['visuals'], 'stale')

    def test_dependency_discovery_rejects_opaque_loading_without_executing_world(self):
        world = self.root / 'production-source/world.cjs'
        for loading in ["require(target)", "require(`./${target}.cjs`)", "const load=require;load('./file.cjs')",
                        "import('./file.cjs')", "import x from './file.js'", "module['require']('./file.cjs')",
                        "const {createRequire: make}=require('node:module');const load=make(__filename)"]:
            with self.subTest(loading=loading):
                world.write_text("throw new Error('World must never execute during discovery');\n" + loading + ';\n')
                with self.assertRaisesRegex(ValueError, 'unsupported'):
                    self.workflow.renderer_sources(self.root)

    def test_dependency_discovery_ignores_comment_string_and_regex_examples(self):
        world = self.root / 'production-source/world.cjs'
        world.write_text("""// require('./missing-comment.cjs')
/* require('./missing-block.cjs') */
const text = \"require('./missing-string.cjs')\";
const regex = /require\\('missing-regex'\\)/g;
const template = `A plain teaching example`;
module.exports={};
""")
        paths = self.workflow.renderer_sources(self.root)
        self.assertIn('production-source/world.cjs', paths)
        self.assertFalse(any('missing' in path for path in paths))

    def test_dependency_discovery_rejects_imports_outside_project_and_symlink_ancestors(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (outside / 'tone.cjs').write_text("module.exports={};\n")
        world = self.root / 'production-source/world.cjs'
        world.write_text("require('../../outside/tone.cjs');\n")
        with self.assertRaisesRegex(ValueError, 'escapes the project'):
            self.workflow.renderer_sources(self.root)
        (self.root / 'production-source/linked').symlink_to(outside, target_is_directory=True)
        world.write_text("require('./linked/tone.cjs');\n")
        with self.assertRaisesRegex(ValueError, 'escapes the project|symlink'):
            self.workflow.renderer_sources(self.root)
        internal = self.root / 'production-source/internal'
        internal.mkdir()
        (internal / 'tone.cjs').write_text('module.exports={};\n')
        (self.root / 'production-source/internal-link').symlink_to(internal, target_is_directory=True)
        world.write_text("require('./internal-link/tone.cjs');\n")
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.workflow.renderer_sources(self.root)

    def test_missing_research_blocks_later_stage(self):
        with self.assertRaisesRegex(ValueError, 'upstream'):
            self.workflow.record(self.root, 'curriculum')

    def test_changed_source_invalidates_descendants(self):
        self.seed_curriculum()
        job = self.workflow.read(self.root / 'job.json')
        job['title'] = 'Changed fixture role'
        self.workflow.write(self.root / 'job.json', job)
        self.assertEqual(self.workflow.state(self.root)[1]['research'], 'stale')
        self.assertEqual(self.workflow.state(self.root)[1]['curriculum'], 'stale')

    def test_untaught_requirement_is_rejected(self):
        self.seed_curriculum()
        job = self.workflow.read(self.root / 'job.json')
        job['requirements'].append({'id': 'r2', 'text': 'Another responsibility', 'kind': 'required'})
        self.workflow.write(self.root / 'job.json', job)
        with self.assertRaisesRegex(ValueError, 'missing from the curriculum'):
            self.workflow.curriculum(self.root)

    def test_rejected_visual_acceptance_blocks_delivery_review(self):
        report = {key: {'status': 'pending', 'coverage': 'Synthetic pending review.'}
                  for key in ('content', 'listening', 'synchronizedViewing', 'silentInspection')}
        report['silentInspection'] = {'status': 'failed', 'coverage': 'The course owner rejected the visual direction.'}
        self.workflow.write(self.root / 'review/acceptance.json', report)
        with self.assertRaisesRegex(ValueError, 'silentInspection'):
            self.workflow.acceptance(self.root)

    def test_export_omits_working_data_and_detects_changed_package(self):
        self.seed_curriculum()
        self.data = self.workflow.read(self.skill / 'assets/starter/course.json')
        self.data['privateNotes'] = 'PRIVATE_FIXTURE_MUST_NOT_EXPORT'
        self.data['subtitle'] = 'Public course introduction'
        self.data['tagline'] = 'Follow the evidence.'
        self.data['glossary'] = [{'term': 'Fixture term', 'definition': 'Public reminder', 'privateNotes': 'PRIVATE_FIXTURE_MUST_NOT_EXPORT'},
                                 {'term': 'Incomplete entry'}]
        self.data['lessons'][0].update(question='Which evidence?', options=['Bounded evidence', 'An unsupported leap'],
            answer=0, explanation='General reasoning', optionFeedback=['The evidence addresses the claim.', 'The conclusion exceeds the evidence.'])
        self.sheet = self.workflow.read(self.skill / 'assets/starter/visual-beat-sheet/beat-sheet.json')
        self.save()
        self.seed_design()
        self.workflow.record(self.root, 'script')
        (self.root / 'visual-beat-sheet/beat-sheet.md').write_text('# Synthetic transfer beat sheet\n')
        self.workflow.record(self.root, 'visuals')
        media_fixture(self, 12)
        self.assertEqual(self.workflow.state(self.root)[1]['script'], 'completed')
        self.assertEqual(self.workflow.state(self.root)[1]['visuals'], 'completed')
        self.workflow.record(self.root, 'narration')
        self.assertIn('measured synthetic fixture', (self.root / 'visual-beat-sheet/beat-sheet.md').read_text())
        self.assertEqual(self.workflow.state(self.root)[1]['visuals'], 'completed')
        env = dict(os.environ)
        if not env.get('CANVAS_MODULE'):
            env['CANVAS_MODULE'] = str(ROOT / 'assets/starter/production-source/node_modules/@napi-rs/canvas')
        for script, argument in [('render.cjs', 'posters'), ('audit.cjs', None)]:
            command = ['node', str(self.root / 'production-source' / script)]
            if argument:
                command.append(argument)
            subprocess.run(command, env=env, check=True, capture_output=True)
        self.workflow.record(self.root, 'media')
        # Rendering again redraws nothing, so the recorded media stays current.
        self.assertIn('01: picture is current, not redrawn', render(self).stdout)
        self.assertEqual(self.workflow.state(self.root)[1]['media'], 'completed')
        self.workflow.write(self.root / 'review/acceptance.json', {
            key: {'status': 'pending', 'coverage': 'Synthetic fixture; no perceptual review performed.'}
            for key in ('content', 'listening', 'synchronizedViewing', 'silentInspection')})
        self.workflow.record(self.root, 'review')
        output = self.base / 'export'
        manifest = self.workflow.export(self.root, output)
        self.assertTrue(manifest['reviewVersion'])
        self.assertFalse((output / 'audio').exists())
        self.assertFalse((output / 'job.json').exists())
        self.assertFalse((output / 'sources.json').exists())
        player = (output / 'course-data.js').read_text()
        self.assertNotIn('PRIVATE_FIXTURE_MUST_NOT_EXPORT', player)
        self.assertNotIn('Private fixture', player)
        self.assertIn('Synthetic public fixture', player)
        self.assertIn('Public course introduction', player)
        self.assertIn('Follow the evidence.', player)
        self.assertIn('Public reminder', player)
        self.assertNotIn('Incomplete entry', player)
        self.assertIn('The conclusion exceeds the evidence.', player)
        self.assertIn('fiction', player)
        source_player = self.root / 'player/player.js'
        original = source_player.read_bytes()
        source_player.write_bytes(original + b'\n// Player changed after export\n')
        self.assertEqual(self.workflow.state(self.root)[1]['package'], 'stale')
        source_player.write_bytes(original)
        self.workflow.write(self.root / 'delivery.json', {'status': 'deployed', 'url': 'https://example.org/fictional-fixture',
            'provider': 'test fixture only', 'version': 'fixture', 'audience': 'private', 'packageSha256': manifest['packageSha256']})
        exported_index = output / 'index.html'
        original_exported_index = exported_index.read_bytes()
        exported_index.write_text('Changed after export')
        self.assertEqual(self.workflow.state(self.root)[1]['package'], 'stale')
        with self.assertRaisesRegex(ValueError, 'package'):
            self.workflow.record(self.root, 'delivery')
        exported_index.write_bytes(original_exported_index)
        self.workflow.record(self.root, 'delivery')
        exported_index.write_text('Changed after recorded delivery')
        statuses = self.workflow.state(self.root)[1]
        self.assertEqual(statuses['package'], 'stale')
        self.assertEqual(statuses['delivery'], 'stale')
        exported_index.write_bytes(original_exported_index)
        self.assertEqual(self.workflow.state(self.root)[1]['delivery'], 'completed')
        external = self.base / 'must-not-follow.txt'
        external.write_bytes(original_exported_index)
        exported_index.unlink()
        exported_index.symlink_to(external)
        self.assertFalse(self.workflow.packaged_files_current(self.root))
        self.assertEqual(self.workflow.state(self.root)[1]['delivery'], 'stale')


if __name__ == '__main__':
    unittest.main()
