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

    def test_provider_point_boundary_retains_measured_onset(self):
        spec = importlib.util.spec_from_file_location('fixture_narrate', SKILL / 'assets/starter/production-source/narrate.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        words = module.align('They share.', [
            {'type': 'WordBoundary', 'text': 'They', 'offset': 10000000, 'duration': 0},
            {'type': 'WordBoundary', 'text': 'share', 'offset': 12000000, 'duration': 2000000}])
        self.assertEqual(words[0]['start'], 1)
        self.assertEqual(words[0]['rawEnd'], 1)
        self.assertEqual(words[0]['end'], words[1]['start'])
        self.assertIn('inferred', words[0]['timingMethod'])
        with self.assertRaisesRegex(ValueError, 'timings overlap or are invalid'):
            module.align('They', [{'type': 'WordBoundary', 'text': 'They', 'offset': 10000000, 'duration': 0}])

    def test_caption_chunks_keep_dialogue_quotes_and_compound_tokens(self):
        spec = importlib.util.spec_from_file_location('fixture_caption_narrate', SKILL / 'assets/starter/production-source/narrate.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for source, tokens in [('"They share." "Yes."', ['They', 'share', 'Yes']),
                               ('C-seventeen goes.', ['C', 'seventeen', 'goes'])]:
            with self.subTest(source=source):
                words, cursor = [], 0
                for index, token in enumerate(tokens):
                    at = source.index(token, cursor)
                    words.append(dict(text=token, charStart=at, charEnd=at+len(token), start=index*.3, end=index*.3+.2))
                    cursor = at+len(token)
                chunks = module.caption_chunks(source, words, max_words=1)
                self.assertEqual(' '.join(text for _, text in chunks), source)
                if source.startswith('C-'):
                    self.assertEqual(chunks[0][1], 'C-seventeen')

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

    def test_wrapped_labels_use_measured_nonoverlapping_lines(self):
        env = dict(os.environ)
        if not env.get('CANVAS_MODULE'):
            module = SKILL / 'assets/starter/production-source/node_modules/@napi-rs/canvas'
            if not module.exists():
                self.skipTest('Canvas dependency not installed')
            env['CANVAS_MODULE'] = str(module)
        script = """
const {createCanvas}=require(process.env.CANVAS_MODULE);
const {createStage}=require(process.argv[1]);
const g=createCanvas(1280,720).getContext('2d'),s=createStage(g,{width:1280,height:720});
s.actor('owner',{x:550,y:290,w:180,h:100},()=>{});
s.wrappedLabel('wrapped','Reliable correction delivery',640,340,{maxWidth:156,size:23,owner:'owner'});
const result=s.finish(),labels=result.items.filter(x=>x.kind==='label');
if(labels.length!==3)throw Error('Unexpected measured wrapping');
for(let i=1;i<labels.length;i++)if(labels[i-1].bounds.y+labels[i-1].bounds.h>labels[i].bounds.y)throw Error('Lines overlap');
for(const item of labels)if(item.bounds.x<550||item.bounds.x+item.bounds.w>730||item.bounds.y<290||item.bounds.y+item.bounds.h>390)throw Error('Label escaped authored bounds');
"""
        subprocess.run(['node', '-e', script, str(self.root / 'production-source/motion.cjs')], env=env, check=True, capture_output=True)

    def test_fresh_audit_archives_previous_flagged_findings(self):
        env = dict(os.environ)
        if not env.get('CANVAS_MODULE'):
            module = SKILL / 'assets/starter/production-source/node_modules/@napi-rs/canvas'
            if not module.exists():
                self.skipTest('Canvas dependency not installed')
            env['CANVAS_MODULE'] = str(module)
        self.data['lessons'] = [dict(id='01', duration=1 / self.data['fps'])]
        self.save()
        (self.root / 'production-source/world.cjs').write_text(
            "exports.draw=()=>({items:[],viewport:{x:0,y:0,w:1280,h:720},safe:{x:0,y:0,w:1280,h:720}});")
        flagged = self.root / 'review/flagged'
        flagged.mkdir(parents=True)
        (flagged / 'previous.png').write_bytes(b'previous evidence')
        (self.root / 'review/frame-audit.json').write_text('{"unresolvedPairs": 1}')
        subprocess.run(['node', str(self.root / 'production-source/audit.cjs')],
                       env=env, check=True, capture_output=True)
        report = json.loads((self.root / 'review/frame-audit.json').read_text())
        self.assertEqual(report['unresolvedPairs'], 0)
        self.assertEqual(report['totalFrames'], 1)
        history = self.root / 'review' / report['previousFindingsArchived']
        self.assertEqual((history / 'flagged/previous.png').read_bytes(), b'previous evidence')
        self.assertEqual(json.loads((history / 'frame-audit.json').read_text())['unresolvedPairs'], 1)
        self.assertEqual(list(flagged.iterdir()), [])

    def media_fixture(self, audio_seconds):
        from media_fixture import media_fixture
        media_fixture(self, audio_seconds)

    def test_failed_authored_model_invariant_blocks_audit(self):
        env = dict(os.environ)
        if not env.get('CANVAS_MODULE'):
            module = SKILL / 'assets/starter/production-source/node_modules/@napi-rs/canvas'
            if not module.exists():
                self.skipTest('Canvas dependency not installed')
            env['CANVAS_MODULE'] = str(module)
        self.data['lessons'] = [dict(id='01', duration=1 / self.data['fps'])]
        self.save()
        (self.root / 'production-source/world.cjs').write_text(
            "exports.draw=()=>({items:[],viewport:{x:0,y:0,w:1280,h:720},safe:{x:0,y:0,w:1280,h:720},"
            "invariants:{checks:[{id:'accepted-values',passed:false,actual:97,expected:50}]}});")
        result = subprocess.run(['node', str(self.root / 'production-source/audit.cjs')],
                                env=env, capture_output=True)
        self.assertEqual(result.returncode, 1)
        report = json.loads((self.root / 'review/frame-audit.json').read_text())
        self.assertEqual(report['lessons'][0]['unresolved'][0]['type'], 'mechanism-invariant')

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
