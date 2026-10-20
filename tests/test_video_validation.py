"""Regression tests for demonstrated content and media failures; no speech requests."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / 'skills/continuous-learning-videos'
SPEC = importlib.util.spec_from_file_location('video_validator', SKILL / 'scripts/validate_project.py')
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
from text_checks import check_words


class VideoValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='video-validation-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'course'
        subprocess.run([sys.executable, str(SKILL / 'scripts/new_project.py'), str(self.root)],
                       check=True, capture_output=True)
        self.data = json.loads((self.root / 'course.json').read_text())
        self.sheet = json.loads((self.root / 'visual-beat-sheet/beat-sheet.json').read_text())

    def save(self):
        (self.root / 'course.json').write_text(json.dumps(self.data))
        (self.root / 'visual-beat-sheet/beat-sheet.json').write_text(json.dumps(self.sheet))
        (self.root / 'player/course-data.js').write_text('window.COURSE = ' + json.dumps(self.data) + ';')

    def test_starter_passes(self):
        self.assertEqual(VALIDATOR.validate(self.root)['status'], 'passed')

    def test_changed_quantities_are_rejected(self):
        for actual, changed in [('1.5', '15'), ('-10', '10'), ('10%', '10'), ('$10', '10')]:
            with self.subTest(actual=actual):
                self.data['lessons'][0]['scenes'][0]['narration'] = f'The value is {actual} units.'
                self.sheet['lessons'][0]['beats'][0]['cues'][0]['text'] = f'The value is {changed} units.'
                self.save()
                with self.assertRaisesRegex(ValueError, 'Sentence cues differ'):
                    VALIDATOR.validate(self.root)

    def test_word_alignment_cannot_drop_negative_sign(self):
        text = 'Value -10.'
        words = [{'text': 'Value', 'charStart': 0, 'charEnd': 5, 'start': 0, 'end': .2},
                 {'text': '10', 'charStart': 7, 'charEnd': 9, 'start': .3, 'end': .5}]
        with self.assertRaisesRegex(ValueError, 'Meaning-bearing'):
            check_words(text, words)

    def test_word_alignment_allows_sentence_punctuation(self):
        text = 'Value ten.'
        check_words(text, [{'text': 'Value', 'charStart': 0, 'charEnd': 5, 'start': 0, 'end': .2},
                           {'text': 'ten', 'charStart': 6, 'charEnd': 9, 'start': .3, 'end': .5}])

    def test_overlapping_sentence_cues_are_rejected(self):
        cue = self.sheet['lessons'][0]['beats'][0]['cues'][0]
        other = copy.deepcopy(cue)
        cue['text'] = 'These two accounts hold'
        other['text'] = 'a total of one hundred fifty units.'
        self.sheet['lessons'][0]['beats'][0]['cues'] = [cue, other]
        self.save()
        with self.assertRaisesRegex(ValueError, 'overlap'):
            VALIDATOR.validate(self.root)

    def test_missing_source_coverage_is_rejected(self):
        del self.data['lessons'][0]['coverage']
        self.save()
        with self.assertRaisesRegex(ValueError, 'source coverage'):
            VALIDATOR.validate(self.root)

    def media_fixture(self, audio_seconds):
        from media_fixture import media_fixture
        media_fixture(self, audio_seconds)

    def test_complete_audio_stream_passes(self):
        self.media_fixture(12)
        report = VALIDATOR.validate(self.root, media=True)
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['factualSourceVerification'], 'not evaluated by this tool')

    def test_truncated_audio_stream_is_rejected(self):
        self.media_fixture(1)
        with self.assertRaisesRegex(ValueError, 'Audio stream duration'):
            VALIDATOR.validate(self.root, media=True)


if __name__ == '__main__':
    unittest.main()
