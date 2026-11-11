"""The plan sync derives structure and timing from course.json and never loses authored visual fields."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import wave

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import sync_plan  # noqa: E402
import validate_project  # noqa: E402
import write_beat_sheet  # noqa: E402

FIELDS = dict(concept='What the sentence teaches.', metaphor='A fixture vessel.', elements=['Vessel'], behavior='It fills.',
              camera='Hold wide.', next='The next sentence.', silentMeaning='Something fills.', risks=['None in a fixture.'])


def creative(sheet):
    """The authored part of a sheet: no timing and none of the fields copied from course.json."""
    def strip(value):
        if isinstance(value, dict):
            return {k: strip(v) for k, v in value.items() if k not in {'start', 'end', 'timingMethod', 'context', 'headline', 'fiction'}}
        if isinstance(value, list):
            return [strip(v) for v in value]
        return value
    return strip(sheet)


class SyncPlanTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='sync-plan-test-')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.project('course')
        # A script as an author leaves it: lessons and scenes with narration, no timing, no beat sheet.
        self.data = json.loads((self.root / 'course.json').read_text())
        self.data['lessons'] = [
            {'id': '01', 'title': 'Arrivals', 'goal': 'Follow one parcel.', 'coverage': 'Fictional fixture.', 'part': 'Part I',
             'scenes': [{'id': 'dock', 'headline': 'At the dock', 'fiction': True,
                         'narration': 'The van reaches dock B. Dr. Ho signs for 2.5 kg, and the gate opens.'},
                        {'id': 'shelf', 'headline': 'On the shelf', 'narration': 'Now the parcel waits.'}]},
            {'id': '02', 'title': 'Sorting', 'goal': 'Sort by route.', 'coverage': 'Fictional fixture.',
             'scenes': [{'id': 'belt', 'headline': 'The belt', 'fiction': False, 'narration': 'Parcels ride one belt.'}]}]
        self.save()
        self.sheet_path = self.root / 'visual-beat-sheet/beat-sheet.json'

    def project(self, name, *flags):
        root = self.base / name
        subprocess.run([sys.executable, str(ROOT / 'scripts/new_project.py'), str(root), *flags], check=True, capture_output=True)
        return root

    def save(self):
        (self.root / 'course.json').write_text(json.dumps(self.data, ensure_ascii=False, indent=2) + '\n')

    def sheet(self):
        return json.loads(self.sheet_path.read_text())

    def author(self, path=None):
        """Fill every missing visual field, as the visual stage would."""
        path = path or self.sheet_path
        sheet = json.loads(path.read_text())
        for lesson in sheet['lessons'] if 'lessons' in sheet else [sheet]:
            for beat in lesson['beats']:
                for cue in beat['cues']:
                    for key, value in FIELDS.items():
                        cue.setdefault(key, value + ' ' + cue['text'] if isinstance(value, str) else value)
        path.write_text(json.dumps(sheet, ensure_ascii=False, indent=2) + '\n')

    def test_skeleton_timing_and_player_data_come_from_the_script(self):
        report = sync_plan.sync(self.root)
        self.assertEqual((report['lessons'], report['cues'], report['estimatedTiming']), (2, 4, ['01', '02']))
        self.assertEqual(report['toAuthor'], ['01', '02'])
        self.assertEqual(report['missingVisualFields'], 4 * len(FIELDS))
        course = json.loads((self.root / 'course.json').read_text())
        first = course['lessons'][0]
        self.assertEqual(first['scenes'][0]['start'], 0)
        self.assertEqual(first['scenes'][1]['start'], first['scenes'][0]['end'])
        self.assertEqual(first['duration'], first['scenes'][1]['end'])
        self.assertEqual(json.loads((self.root / 'player/course-data.js').read_text()[len('window.COURSE = '):-2]), course)
        lesson = self.sheet()['lessons'][0]
        self.assertEqual(lesson['context'], {'title': 'Arrivals', 'part': 'Part I', 'goal': 'Follow one parcel.', 'coverage': 'Fictional fixture.'})
        self.assertEqual([(beat['id'], beat['headline'], beat.get('fiction')) for beat in lesson['beats']],
                         [('dock', 'At the dock', True), ('shelf', 'On the shelf', None)])
        # One cue per sentence, each an exact span; an abbreviation and a decimal do not split one.
        cues = lesson['beats'][0]['cues']
        self.assertEqual([cue['text'] for cue in cues], ['The van reaches dock B.', 'Dr. Ho signs for 2.5 kg, and the gate opens.'])
        self.assertTrue(all(cue['timingMethod'] == 'estimated' for cue in cues))
        self.assertTrue(first['scenes'][0]['start'] <= cues[0]['start'] < cues[0]['end'] <= cues[1]['start'] < cues[1]['end'] <= first['scenes'][0]['end'])
        # A skeleton is not a plan: validation still asks for the visual fields.
        with self.assertRaisesRegex(ValueError, 'Missing cue field: concept'):
            validate_project.validate(self.root)
        self.author()
        self.assertEqual(validate_project.validate(self.root)['sentenceCues'], 4)

    def test_a_second_run_changes_nothing(self):
        sync_plan.sync(self.root)
        self.author()
        before = {name: (self.root / name).read_bytes() for name in ('course.json', 'visual-beat-sheet/beat-sheet.json', 'player/course-data.js')}
        report = sync_plan.sync(self.root)
        self.assertEqual((report['missingVisualFields'], report['estimatedTiming'], report['toAuthor']), (0, [], []))
        self.assertEqual(before, {name: (self.root / name).read_bytes() for name in before})

    def test_changed_narration_keeps_the_fields_of_unchanged_sentences(self):
        sync_plan.sync(self.root)
        self.author()
        kept = self.sheet()['lessons'][0]['beats'][0]['cues'][0]
        scene = self.data = json.loads((self.root / 'course.json').read_text())
        scene = self.data['lessons'][0]['scenes'][0]
        scene['narration'] = 'The van reaches dock B. A clerk signs for it.'
        self.save()
        report = sync_plan.sync(self.root)
        cues = self.sheet()['lessons'][0]['beats'][0]['cues']
        self.assertEqual([cue['text'] for cue in cues], ['The van reaches dock B.', 'A clerk signs for it.'])
        self.assertEqual({k: cues[0][k] for k in FIELDS}, {k: kept[k] for k in FIELDS})
        self.assertNotIn('concept', cues[1])
        self.assertEqual((report['missingVisualFields'], report['toAuthor']), (len(FIELDS), ['01']))
        # The untouched lesson keeps everything.
        self.assertEqual(len(self.sheet()['lessons'][1]['beats'][0]['cues'][0]), len(FIELDS) + 4)

    def test_an_authors_own_segmentation_and_beat_fields_survive(self):
        sync_plan.sync(self.root)
        sheet = self.sheet()
        beat = sheet['lessons'][0]['beats'][0]
        merged = dict(FIELDS, text=self.data['lessons'][0]['scenes'][0]['narration'])
        beat['cues'], beat['design'] = [merged], {'template': 'world mechanism', 'triggers': {'open': 'gate'}}
        self.sheet_path.write_text(json.dumps(sheet))
        sync_plan.sync(self.root)
        beat = self.sheet()['lessons'][0]['beats'][0]
        self.assertEqual(len(beat['cues']), 1)
        self.assertEqual(beat['design']['triggers'], {'open': 'gate'})
        self.assertEqual(beat['cues'][0]['concept'], FIELDS['concept'])

    def test_measured_narration_timing_is_never_estimated_over(self):
        sync_plan.sync(self.root)
        course = json.loads((self.root / 'course.json').read_text())
        scene = course['lessons'][1]['scenes'][0]
        words, at = [], scene['start'] + .2
        for token in ('Parcels', 'ride', 'one', 'belt'):
            start = scene['narration'].index(token)
            words.append({'text': token, 'charStart': start, 'charEnd': start + len(token), 'start': round(at, 3), 'end': round(at + .3, 3)})
            at += .4
        scene['wordTimings'] = words
        (self.root / 'course.json').write_text(json.dumps(course, indent=2) + '\n')
        before = (self.root / 'course.json').read_bytes()
        report = sync_plan.sync(self.root)
        self.assertEqual((self.root / 'course.json').read_bytes(), before)
        cue = self.sheet()['lessons'][1]['beats'][0]['cues'][0]
        self.assertEqual((cue['start'], cue['end'], cue['timingMethod']), (words[0]['start'], words[-1]['end'], 'measured word boundaries'))
        self.assertEqual(report['narrationChangedSinceMeasured'], [])
        # Text changed after it was measured: the cue falls back to an estimate and the report says so.
        scene['narration'] = 'Parcels ride two belts.'
        (self.root / 'course.json').write_text(json.dumps(course, indent=2) + '\n')
        report = sync_plan.sync(self.root)
        self.assertEqual(report['narrationChangedSinceMeasured'], ['02/belt'])
        self.assertEqual(self.sheet()['lessons'][1]['beats'][0]['cues'][0]['timingMethod'], 'estimated')

    def test_lesson_files_are_the_authoring_surface_once_split(self):
        report = sync_plan.sync(self.root, split=True)
        self.assertEqual(report['lessonFiles'], 'visual-beat-sheet/lessons/<lessonId>.json')
        folder = self.root / 'visual-beat-sheet/lessons'
        self.assertEqual(sorted(p.name for p in folder.iterdir()), ['01.json', '02.json'])
        self.assertEqual(json.loads((folder / '01.json').read_text()), self.sheet()['lessons'][0])
        self.author(folder / '02.json')
        report = sync_plan.sync(self.root)                      # split is remembered by the files' presence
        self.assertEqual(report['toAuthor'], ['01'])
        self.assertEqual(self.sheet()['lessons'][1]['beats'][0]['cues'][0]['concept'], FIELDS['concept'] + ' Parcels ride one belt.')
        # A direct edit to the canonical sheet would be overwritten by the lesson file: refuse instead.
        sheet = self.sheet()
        sheet['lessons'][1]['beats'][0]['cues'][0]['concept'] = 'Edited in the wrong file.'
        self.sheet_path.write_text(json.dumps(sheet))
        future = time.time() + 5
        os.utime(self.sheet_path, (future, future))
        with self.assertRaisesRegex(ValueError, 'beat-sheet.json was edited after visual-beat-sheet/lessons/02.json'):
            sync_plan.sync(self.root)
        (folder / '02.json').unlink()
        sync_plan.sync(self.root)
        self.assertEqual(self.sheet()['lessons'][1]['beats'][0]['cues'][0]['concept'], 'Edited in the wrong file.')
        (folder / '09.json').write_text('{"id": "09", "beats": []}')
        with self.assertRaisesRegex(ValueError, 'names no lesson'):
            sync_plan.sync(self.root)

    def test_a_beat_may_state_shared_fields_once(self):
        sync_plan.sync(self.root)
        sheet = self.sheet()
        for lesson in sheet['lessons']:
            for beat in lesson['beats']:
                beat.update(metaphor='One dock, seen from above.', elements=['Dock', 'Van'], camera='Hold on the dock.', risks=['Van near the label.'])
                for cue in beat['cues']:
                    cue.update(concept='c', behavior='b', next='n', silentMeaning='s')
        self.sheet_path.write_text(json.dumps(sheet))
        self.assertEqual(sync_plan.sync(self.root)['missingVisualFields'], 0)
        self.assertEqual(validate_project.validate(self.root)['status'], 'passed')
        readable = write_beat_sheet.write_sheet(self.root).read_text()
        self.assertEqual(readable.count('One dock, seen from above.: Dock; Van'), 4)
        self.assertEqual(readable.count('Van near the label.'), 4)
        # A cue's own value wins, and the per-sentence fields cannot be inherited.
        sheet = self.sheet()
        sheet['lessons'][0]['beats'][0]['cues'][0]['metaphor'] = 'The van alone.'
        self.sheet_path.write_text(json.dumps(sheet))
        self.assertIn('The van alone.: Dock; Van', write_beat_sheet.write_sheet(self.root).read_text())
        sheet['lessons'][0]['beats'][0]['concept'] = 'A beat-level concept is not a sentence purpose.'
        del sheet['lessons'][0]['beats'][0]['cues'][1]['concept']
        self.sheet_path.write_text(json.dumps(sheet))
        with self.assertRaisesRegex(ValueError, 'Missing cue field: concept'):
            validate_project.validate(self.root)

    def test_the_design_demo_survives_a_sync_unchanged(self):
        demo = self.project('designed', '--design-demo')
        before = json.loads((demo / 'visual-beat-sheet/beat-sheet.json').read_text())
        course = (demo / 'course.json').read_bytes()
        report = sync_plan.sync(demo, split=True)
        after = json.loads((demo / 'visual-beat-sheet/beat-sheet.json').read_text())
        self.assertEqual((report['cues'], report['missingVisualFields'], report['estimatedTiming']), (26, 0, []))
        self.assertEqual(creative(before), creative(after))
        self.assertEqual([[(c['start'], c['end']) for c in b['cues']] for b in before['lessons'][0]['beats']],
                         [[(c['start'], c['end']) for c in b['cues']] for b in after['lessons'][0]['beats']])
        self.assertEqual((demo / 'course.json').read_bytes(), course)
        self.assertEqual(validate_project.validate(demo)['status'], 'passed')

    def test_narration_can_be_measured_on_the_skeleton_before_any_visual_field_exists(self):
        """narrate.py's own finalize() on cached synthetic blocks: no speech request."""
        sync_plan.sync(self.root)
        sys.path.insert(0, str(self.root / 'production-source'))
        spec = importlib.util.spec_from_file_location('fixture_narrate', self.root / 'production-source/narrate.py')
        narrate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(narrate)
        data, sheet = json.loads((self.root / 'course.json').read_text()), self.sheet()
        for lesson in data['lessons']:
            for beat in lesson['scenes']:
                words, at = [], .05
                for token in beat['narration'].split():
                    text = token.strip('.,')
                    start = beat['narration'].index(text, words[-1]['charEnd'] if words else 0)
                    words.append({'text': text, 'charStart': start, 'charEnd': start + len(text), 'start': round(at, 3), 'end': round(at + .2, 3)})
                    at += .3
                stem = narrate.stem_for(lesson, beat)
                (self.root / 'audio' / (stem + '.words.json')).write_text(json.dumps({'words': words}))
                with wave.open(str(self.root / 'audio' / (stem + '.wav')), 'wb') as audio:
                    audio.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
                    audio.writeframes(b'\0' * (round(at * 24000) * 2))
        narrate.finalize(data, sheet, self.root, 'synthetic-fixture')
        cues = self.sheet()['lessons'][0]['beats'][0]['cues']
        self.assertTrue(all(cue['timingMethod'].startswith('measured') for cue in cues))
        measured = copy.deepcopy(self.sheet())
        # Authoring and a later sync keep the measured timing and its provider label.
        self.author()
        self.assertEqual(sync_plan.sync(self.root)['estimatedTiming'], [])
        for old, new in zip(measured['lessons'], self.sheet()['lessons']):
            for a, b in zip(old['beats'], new['beats']):
                self.assertEqual([(c['start'], c['end'], c['timingMethod']) for c in a['cues']],
                                 [(c['start'], c['end'], c['timingMethod']) for c in b['cues']])
        self.assertEqual(validate_project.validate(self.root)['status'], 'passed')

    def test_incomplete_scripts_are_refused(self):
        for mutate, message in ((lambda d: d['lessons'][0]['scenes'][0].update(narration=' '), 'has no narration'),
                                (lambda d: d['lessons'][1].update(id='01'), 'Duplicate lesson IDs'),
                                (lambda d: d['lessons'][0].update(id='../x'), 'Unsafe lesson ID'),
                                (lambda d: d.update(lessons=[]), 'Write the lesson scripts')):
            with self.subTest(message=message):
                original = copy.deepcopy(self.data)
                mutate(self.data)
                self.save()
                with self.assertRaisesRegex(ValueError, message):
                    sync_plan.sync(self.root)
                self.data = original
                self.save()

    def test_workflow_sync_command_reports_compactly(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/workflow.py'), 'sync', str(self.root), '--split'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual((report['cues'], report['toAuthor']), (4, ['01', '02']))
        self.assertLess(len(result.stdout), 600)


if __name__ == '__main__':
    unittest.main()
