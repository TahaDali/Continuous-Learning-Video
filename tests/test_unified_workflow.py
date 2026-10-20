"""Exercise the built single skill in isolation using explicitly fictional course fixtures."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from build_skill import build
from media_fixture import media_fixture


class UnifiedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='unified-skill-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.skill = build(self.base / 'job-to-learning-videos')
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

    def test_bundle_is_self_contained(self):
        self.assertTrue((self.skill / 'references/research/chapter-structure.md').is_file())
        self.assertTrue((self.skill / 'references/video/beat-sheet.md').is_file())
        self.assertTrue((self.skill / 'assets/starter/production-source/text_checks.py').is_file())
        self.assertEqual(self.workflow.read(self.root / 'course.json')['lessons'], [])
        self.assertFalse(self.workflow.preflight()['serviceRequestsMade'])

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

    def test_export_omits_working_data_and_detects_changed_package(self):
        self.seed_curriculum()
        self.data = self.workflow.read(self.skill / 'assets/starter/course.json')
        self.data['privateNotes'] = 'PRIVATE_FIXTURE_MUST_NOT_EXPORT'
        self.sheet = self.workflow.read(self.skill / 'assets/starter/visual-beat-sheet/beat-sheet.json')
        self.save()
        (self.root / 'manuscript.md').write_text('# Synthetic mechanical fixture\n\nNot a researched employer course.\n')
        self.workflow.record(self.root, 'script')
        (self.root / 'visual-beat-sheet/beat-sheet.md').write_text('# Synthetic transfer beat sheet\n')
        self.workflow.record(self.root, 'visuals')
        media_fixture(self, 12)
        self.assertEqual(self.workflow.state(self.root)[1]['script'], 'completed')
        self.assertEqual(self.workflow.state(self.root)[1]['visuals'], 'completed')
        self.workflow.record(self.root, 'narration')
        env = dict(os.environ)
        if not env.get('CANVAS_MODULE'):
            env['CANVAS_MODULE'] = str(ROOT / 'skills/continuous-learning-videos/assets/starter/production-source/node_modules/@napi-rs/canvas')
        for script, argument in [('render.cjs', 'posters'), ('audit.cjs', None)]:
            command = ['node', str(self.root / 'production-source' / script)]
            if argument:
                command.append(argument)
            subprocess.run(command, env=env, check=True, capture_output=True)
        self.workflow.record(self.root, 'media')
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
        self.assertIn('fiction', player)
        self.workflow.write(self.root / 'delivery.json', {'status': 'deployed', 'url': 'https://example.org/fictional-fixture',
            'provider': 'test fixture only', 'version': 'fixture', 'audience': 'private', 'packageSha256': manifest['packageSha256']})
        (output / 'index.html').write_text('Changed after export')
        with self.assertRaisesRegex(ValueError, 'Export changed'):
            self.workflow.record(self.root, 'delivery')


if __name__ == '__main__':
    unittest.main()
