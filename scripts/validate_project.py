#!/usr/bin/env python3
"""Check source/beat coverage; optionally verify and decode every final MP4.
Does not certify perceptual listening, semantic effectiveness or visual geometry.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'assets/starter/production-source'))
from text_checks import check_words, exact_text, finite


def require(condition, message):
    if not condition:
        raise ValueError(message)


def norm(text):
    return exact_text(text)


def parse_stamp(s):
    h, m, sec = s.replace(',', '.').split(':')
    return int(h) * 3600 + int(m) * 60 + float(sec)


def validate(root, media=False):
    data = json.loads((root / 'course.json').read_text())
    sheet = json.loads((root / 'visual-beat-sheet/beat-sheet.json').read_text())
    require(finite(data['fps']) and data['fps'] > 0
            and all(type(data[k]) is int and data[k] > 0 for k in ('width', 'height')), 'Invalid output dimensions/rate')
    lessons = data['lessons']
    require(bool(lessons), 'No lessons')
    require(len({l['id'] for l in lessons}) == len(lessons), 'Duplicate lesson IDs')
    require(len(lessons) == len(sheet['lessons']), 'Lesson coverage differs from beat sheet')
    rows, videos = 0, []
    for lesson, plan in zip(lessons, sheet['lessons'], strict=True):
        require(re.fullmatch(r'[a-zA-Z0-9_-]+', lesson['id']), 'Unsafe lesson ID')
        require(lesson['id'] == plan['id'], 'Lesson order/IDs differ')
        require(finite(lesson['duration']) and lesson['duration'] > 0 and lesson['scenes'], 'Empty lesson')
        require(isinstance(lesson.get('coverage'), str) and lesson['coverage'].strip(), 'Missing source coverage note')
        require(len(lesson['scenes']) == len(plan['beats']), 'Beat coverage differs')
        require(len({s['id'] for s in lesson['scenes']}) == len(lesson['scenes']), 'Duplicate beat IDs')
        previous = 0.
        for beat, planned in zip(lesson['scenes'], plan['beats'], strict=True):
            require(re.fullmatch(r'[a-zA-Z0-9_-]+', beat['id']), 'Unsafe beat ID')
            require(beat['id'] == planned['id'], 'Beat order/IDs differ')
            require(finite(beat['start']) and finite(beat['end'])
                    and previous <= beat['start'] < beat['end'] <= lesson['duration'] + .01, 'Invalid beat timing')
            previous = beat['end']
            cues = planned['cues']
            require(bool(cues), 'No sentence cues')
            require(norm(' '.join(c['text'] for c in cues)) == norm(beat['narration']), 'Sentence cues differ from narration')
            previous_cue_end = beat['start']
            for cue in cues:
                for field in ['text', 'concept', 'metaphor', 'elements', 'behavior', 'camera', 'next', 'silentMeaning', 'timingMethod', 'risks']:
                    require(bool(cue.get(field)), f'Missing cue field: {field}')
                require(finite(cue['start']) and finite(cue['end'])
                        and previous_cue_end <= cue['start'] < cue['end'] <= beat['end'] + .01, 'Sentence cues overlap, are unordered, or outside beat')
                previous_cue_end = cue['end']
                rows += 1
            if media:
                words = beat.get('wordTimings', [])
                require(bool(words), 'Final narration needs measured word boundaries')
                check_words(beat['narration'], words)
                for w in words:
                    require(beat['start'] <= w['start'] < w['end'] <= beat['end'] + .01, 'Word outside beat')
                    require(beat['narration'][w['charStart']:w['charEnd']].casefold() == w['text'].casefold(), 'Word source positions differ')
                require(all(a['end'] <= b['start'] + .01 for a, b in zip(words, words[1:])), 'Word boundaries overlap')
                require(all(c['timingMethod'].startswith('measured') for c in cues), 'Final cue timing remains estimated')
                cursor = 0
                for cue in cues:
                    at = beat['narration'].find(cue['text'], cursor)
                    require(at >= cursor, 'Cue is not an exact ordered source span')
                    end = at + len(cue['text'])
                    chosen = [w for w in words if w['charEnd'] > at and w['charStart'] < end]
                    require(chosen and abs(cue['start'] - chosen[0]['start']) <= .01
                            and abs(cue['end'] - chosen[-1]['end']) <= .01, 'Cue timing differs from measured words')
                    cursor = end
        if not media:
            continue
        expected = norm(' '.join(b['narration'] for b in lesson['scenes']))
        srt = (root / 'player/captions' / (lesson['id'] + '.srt')).read_text()
        texts, spans = [], []
        for block in srt.strip().split('\n\n'):
            lines = block.splitlines()
            require(len(lines) >= 3 and ' --> ' in lines[1], 'Malformed SRT')
            start, end = [parse_stamp(t) for t in lines[1].split(' --> ')]
            spans.append((start, end))
            texts.extend(lines[2:])
        require(norm(' '.join(texts)) == expected, 'Caption text differs from narration')
        require(all(0 <= a < b <= lesson['duration'] + .01 for a, b in spans), 'Caption timing outside lesson')
        require(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])), 'Captions overlap')
        vtt = (root / 'player/captions' / (lesson['id'] + '.vtt')).read_text()
        require(vtt.startswith('WEBVTT') and vtt.count(' --> ') == len(spans), 'VTT cue count differs')
        vtt_text, vtt_spans = [], []
        for block in vtt.strip().split('\n\n')[1:]:
            lines = block.splitlines()
            timing = next(i for i, line in enumerate(lines) if ' --> ' in line)
            a, b = lines[timing].split(' --> ')
            vtt_spans.append((parse_stamp(a), parse_stamp(b.split()[0])))
            vtt_text.extend(lines[timing + 1:])
        require(vtt_spans == spans and norm(' '.join(vtt_text)) == expected, 'VTT differs from SRT')
        video = root / 'player/videos' / (lesson['id'] + '.mp4')
        result = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)]))
        vs = next(s for s in result['streams'] if s['codec_type'] == 'video')
        audio = next(s for s in result['streams'] if s['codec_type'] == 'audio')
        require((vs['width'], vs['height']) == (data['width'], data['height']), 'Video dimensions differ')
        n, d = map(float, vs['r_frame_rate'].split('/'))
        require(abs(n / d - data['fps']) < .001, 'Video frame rate differs')
        require(vs['codec_name'] == 'h264' and audio['codec_name'] == 'aac', 'Unexpected final codecs')
        tolerance = 1 / data['fps'] + .15
        for stream, label in ((vs, 'Video'), (audio, 'Audio')):
            require(abs(float(stream['duration']) - lesson['duration']) < tolerance, f'{label} stream duration differs')
            require(abs(float(stream.get('start_time', 0))) < tolerance, f'{label} stream starts late')
        require(abs(float(result['format']['duration']) - lesson['duration']) < tolerance, 'Container duration differs')
        decoded = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(video), '-f', 'null', '-'], capture_output=True)
        require(decoded.returncode == 0 and not decoded.stderr, 'Full media decode failed')
        videos.append({'id': lesson['id'], 'sha256': hashlib.sha256(video.read_bytes()).hexdigest(), 'decoded': True})
    js = (root / 'player/course-data.js').read_text().strip()
    require(js.startswith('window.COURSE = ') and js.endswith(';'), 'Malformed player data')
    require(json.loads(js[len('window.COURSE = '):-1]) == data, 'Player data is stale')
    report = {'status': 'passed', 'lessons': len(lessons), 'sentenceCues': rows,
              'textAndBeatCoverage': 'passed', 'sourceCoverageNotesPresent': True,
              'factualSourceVerification': 'not evaluated by this tool',
              'mediaChecked': media, 'videos': videos,
              'sourceHashes': {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                               for name in ['course.json', 'visual-beat-sheet/beat-sheet.json']},
              'perceptualListening': 'not evaluated by this tool', 'geometry': 'run production-source/audit.cjs separately'}
    (root / 'review').mkdir(exist_ok=True)
    (root / 'review/validation.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('--media', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.project.resolve(), args.media), indent=2))
    except (ValueError, KeyError, StopIteration, OSError, subprocess.CalledProcessError) as error:
        folder = args.project.resolve() / 'review'
        if folder.is_dir():
            (folder / 'validation.json').write_text(json.dumps({'status': 'failed', 'error': str(error), 'mediaChecked': args.media}, indent=2) + '\n')
        parser.exit(1, f'Validation failed: {error}\n')
