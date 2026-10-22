"""Sentence-end review: sentence spans, character-offset sampling and ffmpeg-only contact sheets."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / 'scripts/review_frames.py'
sys.path.insert(0, str(ROOT / 'scripts'))
import review_frames  # noqa: E402

FFMPEG = bool(shutil.which('ffmpeg') and shutil.which('ffprobe'))
# Neutral fiction: one parcel moving through depots, with quotes, an abbreviation and a decimal.
NARRATION = {'initial': 'A parcel leaves the first depot. It is scanned.',
             'move': 'The van carries it to depot B. "Fragile," the label says. Dr. Ho signs for 2.5 kg. It waits.',
             'result': 'The parcel arrives. The parcel is counted once.'}


def timed(scene):
    """Synthetic measured word timings, written the way tests/media_fixture.py writes them."""
    matches = list(re.finditer(r'\S+', scene['narration']))
    step = (scene['end'] - scene['start'] - .2) / len(matches)
    scene['wordTimings'] = [{'text': m.group(), 'charStart': m.start(), 'charEnd': m.end(),
                             'start': scene['start'] + j * step, 'end': scene['start'] + (j + .8) * step}
                            for j, m in enumerate(matches)]
    return scene


def texts(text):
    return [text[a:b] for a, b in review_frames.split_sentences(text)]


def grey_video(path, seconds=12, audio=False):
    """Each whole second has its own grey level, so a tile shows which second was sampled."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sound = ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono', '-c:a', 'aac'] if audio else []
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=c=black:s=320x180:r=24:d={seconds}',
                    *sound, '-vf', "geq=lum='16+18*floor(T)':cb=128:cr=128", '-c:v', 'mpeg4', '-q:v', '2',
                    '-pix_fmt', 'yuv420p', '-t', str(seconds), str(path)], check=True, capture_output=True)


def rgb(path):
    """Decode a PNG to (width, height, RGB bytes) with ffmpeg."""
    info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', '-of', 'json',
                                      str(path)], check=True, capture_output=True, text=True).stdout)['streams'][0]
    data = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                          check=True, capture_output=True).stdout
    return info['width'], info['height'], data


class SentenceSplitTests(unittest.TestCase):
    def test_closing_quotes_and_brackets_stay_with_their_sentence(self):
        self.assertEqual(texts('"They share." "Yes." Then it ends.'), ['"They share."', '"Yes."', 'Then it ends.'])
        self.assertEqual(texts('Wait… Really? (Yes.) Done.'), ['Wait…', 'Really?', '(Yes.)', 'Done.'])
        self.assertEqual(texts('"Why?" she asked. Then... wait... what?'), ['"Why?" she asked.', 'Then... wait... what?'])

    def test_abbreviations_decimals_and_numbered_references_do_not_split(self):
        self.assertEqual(texts('Dr. Ho lends 2.5 books, e.g. a novel. Mr. Lee returns it!'),
                         ['Dr. Ho lends 2.5 books, e.g. a novel.', 'Mr. Lee returns it!'])
        self.assertEqual(texts('See No. 4 on the shelf. The answer is no. Next.'),
                         ['See No. 4 on the shelf.', 'The answer is no.', 'Next.'])

    def test_unterminated_tail_and_surrounding_space_are_kept_exactly(self):
        text = '  One recipe step.  And a tail '
        spans = review_frames.split_sentences(text)
        self.assertEqual([text[a:b] for a, b in spans], ['One recipe step.', 'And a tail'])
        self.assertEqual(spans[0][0], 2)

    def test_lower_case_names_start_sentences_unless_a_quote_ellipsis_or_abbreviation_continues_one(self):
        self.assertEqual(texts('The depot opened. iPhone scans doubled. eBay parcels fell. npm builds the labels.'),
                         ['The depot opened.', 'iPhone scans doubled.', 'eBay parcels fell.', 'npm builds the labels.'])
        self.assertEqual(texts('Vans leave at 9 a.m. and return. Boxes, tape, etc. are stacked. Ask Acme Inc. today.'),
                         ['Vans leave at 9 a.m. and return.', 'Boxes, tape, etc. are stacked.', 'Ask Acme Inc. today.'])


class SamplePointTests(unittest.TestCase):
    def scene(self, narration, start=10., end=14.):
        return timed({'id': 'depot', 'headline': 'Depot', 'narration': narration, 'start': start, 'end': end})

    def test_points_sample_lead_before_each_last_word_and_the_scene_opening(self):
        scene = self.scene('A parcel leaves depot A. It waits at depot B.')
        words = scene['wordTimings']
        plan = review_frames.scene_points(scene, lead=.15)
        self.assertEqual(plan['timing'], 'measured')
        self.assertEqual(plan['points'], [[10.6, review_frames.OPENING],
                                          [round(words[4]['end'] - .15, 2), 'A parcel leaves depot A.'],
                                          [round(words[-1]['end'] - .15, 2), 'It waits at depot B.']])
        self.assertEqual([p[0] for p in review_frames.scene_points(scene, lead=.4)['points'][1:]],
                         [round(words[4]['end'] - .4, 2), round(words[-1]['end'] - .4, 2)])

    def test_repeated_words_map_by_character_offset_not_text(self):
        scene = self.scene('Books move. Books move. Books rest.')
        ends = [w['end'] for w in scene['wordTimings']]
        expected = [round(ends[i] - .15, 2) for i in (1, 3, 5)]
        self.assertEqual([p[0] for p in review_frames.scene_points(scene)['points'][1:]], expected)
        # Older timings without charStart are located in order, never at the first occurrence.
        for w in scene['wordTimings']:
            del w['charStart']
        self.assertEqual([p[0] for p in review_frames.scene_points(scene)['points'][1:]], expected)

    def test_estimated_timing_spreads_over_beat_sheet_cues(self):
        scene = {'id': 'depot', 'narration': 'A parcel leaves depot A. It waits at depot B.', 'start': 10., 'end': 14.,
                 'speechStart': 10.2, 'speechEnd': 13.5}
        cues = [{'text': 'A parcel leaves depot A.', 'start': 10.2, 'end': 12.},
                {'text': 'It waits at depot B.', 'start': 12., 'end': 13.5}]
        plan = review_frames.scene_points(scene, cues=cues)
        self.assertEqual(plan['timing'], 'estimated')
        self.assertEqual([p[0] for p in plan['points']], [10.6, 11.85, 13.35])
        # Without cues the whole spoken span is spread by character position.
        self.assertEqual(review_frames.scene_points(scene)['points'][-1][0], 13.35)

    def test_points_stay_inside_the_scene(self):
        scene = self.scene('Go. Then stop.', start=10., end=11.)
        scene['wordTimings'][0]['end'] = 10.05
        scene['wordTimings'][-1]['end'] = 11.5
        times = [p[0] for p in review_frames.scene_points(scene, frame=1 / 24)['points']]
        self.assertEqual(times, [10.6, 10., round(11 - 1 / 24, 2)])

    def test_sentences_without_timed_words_are_reported_unmapped(self):
        scene = self.scene('The ticket opens. The queue moves.')
        scene['wordTimings'] = scene['wordTimings'][:3]
        plan = review_frames.scene_points(scene)
        self.assertEqual([p[1] for p in plan['points'][1:]], ['The ticket opens.'])
        self.assertEqual(plan['unmapped'], ['The queue moves.'])
        self.assertIn('1 sentences unmapped', review_frames.report([plan], '01', Path('out')))
        self.assertIn('UNMAPPED  The queue moves.', review_frames.report([plan], '01', Path('out')))


class ProjectTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='review-frames-test-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'course'
        subprocess.run([sys.executable, str(ROOT / 'scripts/new_project.py'), str(self.root), '--demo'],
                       check=True, capture_output=True)
        self.data = json.loads((self.root / 'course.json').read_text())
        for scene in self.data['lessons'][0]['scenes']:
            scene['narration'] = NARRATION[scene['id']]
            timed(scene)
        self.save()

    def save(self):
        (self.root / 'course.json').write_text(json.dumps(self.data))

    def run_script(self, *args, lesson='01'):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.root), lesson, *args], capture_output=True, text=True)

    def test_plan_rejects_unknown_lessons_scenes_and_unsafe_ids(self):
        with self.assertRaisesRegex(ValueError, 'No lesson'):
            review_frames.lesson_plan(self.root, '99')
        with self.assertRaisesRegex(ValueError, 'No such scene: missing'):
            review_frames.lesson_plan(self.root, '01', scenes=['missing'])
        with self.assertRaisesRegex(ValueError, 'Unsafe lesson ID'):
            review_frames.review_lesson(self.root, '../01')
        self.data['lessons'][0]['scenes'][0]['id'] = '../escape'
        self.save()
        with self.assertRaisesRegex(ValueError, 'Unsafe scene ID'):
            review_frames.lesson_plan(self.root, '01')

    def test_unknown_lesson_or_video_path_is_reported_as_itself(self):
        # The lesson is checked before the video, and --silent is suggested only for the default video.
        unknown = self.run_script(lesson='99')
        self.assertEqual(unknown.returncode, 1)
        self.assertIn("No lesson '99'", unknown.stderr)
        self.assertNotIn('Missing video', unknown.stderr)
        wrong = self.run_script('--video', str(self.root / 'nowhere.mp4'))
        self.assertEqual(wrong.returncode, 1)
        self.assertIn('Missing video', wrong.stderr)
        self.assertNotIn('--silent', wrong.stderr)

    @unittest.skipUnless(FFMPEG, 'ffmpeg is not installed')
    def test_cli_writes_plan_full_frames_and_time_stamped_sheets(self):
        video = self.root / 'player/videos/01.mp4'
        grey_video(video, audio=True)
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        out = self.root / 'review/sentence-end'
        plan = json.loads((out / '01-plan.json').read_text())
        self.assertEqual([p['scene'] for p in plan], ['initial', 'move', 'result'])
        # Every scene records the video it was sampled from, and the report names it first.
        for scene in plan:
            self.assertEqual(scene['video'], str(video.resolve()))
            self.assertFalse(scene['silent'])
            self.assertAlmostEqual(scene['videoDuration'], 12, delta=.1)
            self.assertEqual(Path(scene['sheet']), out.resolve() / 'sheets/01' / (scene['scene'] + '.png'))
        self.assertTrue(result.stdout.startswith(f'Lesson 01 sampled from {video.resolve()} (with audio, 12.'))
        self.assertEqual([p[1] for p in plan[1]['points']],
                         [review_frames.OPENING, 'The van carries it to depot B.', '"Fragile," the label says.',
                          'Dr. Ho signs for 2.5 kg.', 'It waits.'])
        for sentence in ('Dr. Ho signs for 2.5 kg.', 'Reviewer checklist', 'sheet:', '3 scenes, 8 sentences sampled, 11 frames'):
            self.assertIn(sentence, result.stdout)
        for item in review_frames.CHECKLIST:
            self.assertIn(item, result.stdout)
        levels = {}
        def level(second):
            # Read the reference grey independently of the script under test.
            if second not in levels:
                levels[second] = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(second + .5), '-i', str(video),
                                                 '-frames:v', '1', '-vf', 'scale=4:4', '-f', 'rawvideo', '-pix_fmt',
                                                 'rgb24', '-'], check=True, capture_output=True).stdout[0]
            return levels[second]
        checked = 0
        for scene in plan:
            self.assertEqual(len(scene['frames']), len(scene['points']))
            for frame in scene['frames']:
                self.assertEqual(rgb(Path(frame))[:2], (320, 180))
            width, height, data = rgb(Path(scene['sheet']))
            tiles, rows = len(scene['points']), (len(scene['points']) + 1) // 2
            # Tiles are 160x90 at --scale 0.5 under a 15 px stamp strip, two columns, 6 px gutters.
            self.assertEqual((width, height), (2 * 160 + 6, rows * (15 + 90) + (rows - 1) * 6))
            for k, (t, _) in enumerate(scene['points']):
                x, y = (k % 2) * 166, (k // 2) * 111
                strip = [data[((y + r) * width + x + c) * 3:((y + r) * width + x + c) * 3 + 3]
                         for r in range(15) for c in range(80)]
                self.assertTrue(any(p[0] > 150 and p[1] < 80 and p[2] < 80 for p in strip), f'No time stamp on tile {k}')
                if .1 < t % 1 < .9:
                    at = ((y + 15 + 45) * width + x + 80) * 3
                    self.assertAlmostEqual(data[at], level(int(t)), delta=6, msg=f'{scene["scene"]} tile {k} at {t}')
                    checked += 1
            self.assertTrue(all(a <= b for a, b in zip([p[0] for p in scene['points']], [p[0] for p in scene['points']][1:])))
        self.assertGreaterEqual(checked, 6)

    @unittest.skipUnless(FFMPEG, 'ffmpeg is not installed')
    def test_silent_preview_is_used_only_when_requested(self):
        grey_video(self.root / 'review/silent/01.mp4')
        refused = self.run_script()
        self.assertEqual(refused.returncode, 1)
        self.assertIn('Missing video', refused.stderr)
        self.assertIn('--silent', refused.stderr)
        result = self.run_script('--silent', '--out', str(self.root / 'elsewhere'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / 'elsewhere/sheets/01/move.png').is_file())
        self.assertFalse((self.root / 'review/sentence-end').exists())
        self.assertIn('(silent, no audio stream, ', result.stdout)
        # Without --out a silent run keeps its own folder.
        self.assertEqual(self.run_script('--silent').returncode, 0)
        plan = json.loads((self.root / 'review/sentence-end-silent/01-plan.json').read_text())
        self.assertTrue(all(p['silent'] for p in plan))
        self.assertFalse((self.root / 'review/sentence-end').exists())

    @unittest.skipUnless(FFMPEG, 'ffmpeg is not installed')
    def test_video_of_another_length_is_rejected(self):
        # Every render lasts its lesson's duration: a shorter or longer one is another lesson's or a stale render.
        video = self.root / 'player/videos/01.mp4'
        for seconds in (5, 20):
            grey_video(video, seconds=seconds)
            result = self.run_script()
            self.assertEqual(result.returncode, 1)
            self.assertIn(f'lasts {seconds}.00 s but lesson 01 lasts 12.00 s', result.stderr)
            self.assertFalse((self.root / 'review/sentence-end').exists())

    @unittest.skipUnless(FFMPEG, 'ffmpeg is not installed')
    def test_scene_rerun_never_merges_another_video_into_the_plan(self):
        final, silent = self.root / 'player/videos/01.mp4', self.root / 'review/silent/01.mp4'
        grey_video(final, audio=True)
        grey_video(silent)
        self.assertEqual(self.run_script().returncode, 0)
        out = self.root / 'review/sentence-end'
        before = (out / '01-plan.json').read_text()
        frames = sorted(p.name for p in (out / 'frames/01').glob('*.png'))
        # A silent re-run goes to its own folder and leaves the final encode's evidence alone.
        self.assertEqual(self.run_script('--silent', '--scene', 'move').returncode, 0)
        self.assertEqual((out / '01-plan.json').read_text(), before)
        silent_plan = json.loads((self.root / 'review/sentence-end-silent/01-plan.json').read_text())
        self.assertEqual([(p['scene'], p['silent']) for p in silent_plan], [('move', True)])
        # Pointing a --scene re-run at another video in the same folder is refused before anything is touched.
        refused = self.run_script('--video', str(silent), '--scene', 'move')
        self.assertEqual(refused.returncode, 1)
        self.assertIn('sampled from another video', refused.stderr)
        self.assertEqual((out / '01-plan.json').read_text(), before)
        self.assertEqual(sorted(p.name for p in (out / 'frames/01').glob('*.png')), frames)
        # So is one whose other scenes' timings changed since the plan was made.
        self.data['lessons'][0]['scenes'][0]['wordTimings'][-1]['end'] -= .5
        self.save()
        moved = self.run_script('--scene', 'move')
        self.assertEqual(moved.returncode, 1)
        self.assertIn('(initial)', moved.stderr)

    @unittest.skipUnless(FFMPEG, 'ffmpeg is not installed')
    def test_full_rerun_removes_evidence_of_renamed_scenes(self):
        grey_video(self.root / 'player/videos/01.mp4')
        self.assertEqual(self.run_script().returncode, 0)
        self.data['lessons'][0]['scenes'][1]['id'] = 'carry'
        self.save()
        self.assertEqual(self.run_script().returncode, 0)
        out = self.root / 'review/sentence-end'
        self.assertEqual(sorted(p.name for p in (out / 'sheets/01').iterdir()), ['carry.png', 'initial.png', 'result.png'])
        self.assertEqual(list((out / 'frames/01').glob('move-*.png')), [])
        self.assertEqual(len(list((out / 'frames/01').glob('carry-*.png'))), 5)
        self.assertEqual([p['scene'] for p in json.loads((out / '01-plan.json').read_text())], ['initial', 'carry', 'result'])

    @unittest.skipUnless(FFMPEG, 'ffmpeg is not installed')
    def test_scene_rerun_replaces_only_that_scene_and_its_stale_frames(self):
        grey_video(self.root / 'player/videos/01.mp4')
        self.assertEqual(self.run_script().returncode, 0)
        frames = self.root / 'review/sentence-end/frames/01'
        self.assertEqual(len(list(frames.glob('move-*.png'))), 5)
        scene = self.data['lessons'][0]['scenes'][1]
        scene['narration'] = 'The van carries it to depot B.'
        timed(scene)
        self.save()
        result = self.run_script('--scene', 'move')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(p.name for p in frames.glob('move-*.png')), ['move-00.png', 'move-01.png'])
        plan = json.loads((self.root / 'review/sentence-end/01-plan.json').read_text())
        self.assertEqual([p['scene'] for p in plan], ['initial', 'move', 'result'])
        self.assertEqual(len(plan[1]['points']), 2)
        self.assertEqual(len(list(frames.glob('initial-*.png'))), 3)


if __name__ == '__main__':
    unittest.main()
