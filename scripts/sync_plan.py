#!/usr/bin/env python3
"""Derive from course.json everything that need not be typed twice. No research, speech or hosting requests.

After the lesson scripts are written (or changed) this:
- gives scenes without timing an estimated span, and leaves measured narration timing alone;
- rewrites player/course-data.js to match course.json;
- builds the sentence-cue skeleton of visual-beat-sheet/beat-sheet.json from each scene's exact
  narration, keeping every authored visual field of a cue whose text is unchanged;
- with --split, or when they already exist, keeps one working file per lesson in
  visual-beat-sheet/lessons/<lessonId>.json. Author there; the canonical sheet is rebuilt from them.

It writes structure and timing only. The concept, behaviour and other visual fields stay authored work.
"""
import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'assets/starter/production-source'))
from review_frames import split_sentences  # noqa: E402
from text_checks import exact_text  # noqa: E402

SAFE_ID = re.compile(r'[a-zA-Z0-9_-]+')
TIMING = {'start', 'end', 'timingMethod'}
# Copied from course.json on every run so a lesson's working file can be authored without opening
# the whole course (measured word timings make that file large). Never read back as input.
DERIVED = {'context', 'headline', 'fiction'}
CONTEXT = ('title', 'part', 'goal', 'coverage', 'visual', 'question', 'options', 'answer', 'explanation')
# Per sentence. A beat may instead state metaphor, elements, camera and risks once for its cues.
CUE_FIELDS = ('concept', 'metaphor', 'elements', 'behavior', 'camera', 'next', 'silentMeaning', 'risks')
INHERITED = ('metaphor', 'elements', 'camera', 'risks')
HEAD, TAIL, WORDS_PER_SECOND = .18, .48, 2.5


def need(condition, message):
    if not condition:
        raise ValueError(message)


def estimate(course):
    """Give untimed scenes an estimated span. Returns the IDs of the lessons it re-timed."""
    changed = []
    for lesson in course['lessons']:
        scenes = lesson['scenes']
        timed = [all(isinstance(scene.get(key), (int, float)) for key in ('start', 'end')) for scene in scenes]
        if all(timed) and isinstance(lesson.get('duration'), (int, float)):
            continue
        # One measured scene among untimed ones cannot be laid out: narration re-times the whole lesson.
        need(not any(scene.get('wordTimings') for scene in scenes),
             f"Lesson {lesson['id']} mixes measured and untimed scenes; run production-source/narrate.py to re-time it")
        cursor = 0.
        for scene in scenes:
            at = cursor + HEAD
            for token in scene['narration'].split():
                at += (len(re.sub(r'[^\w]', '', token)) + 2) / (WORDS_PER_SECOND * 6.2)
                at += .25 if token[-1] in '.,:;?!' else .03
            scene.update(start=round(cursor, 3), speechStart=round(cursor + HEAD, 3), speechEnd=round(at, 3),
                         end=round(at + TAIL, 3))
            cursor = scene['end']
        lesson['duration'] = round(cursor, 3)
        changed.append(lesson['id'])
    return changed


def cue_timing(scene, spans):
    """[start, end, method] per character span: measured words when they fit the text, else an even spread."""
    words, narration = scene.get('wordTimings') or [], scene['narration']
    measured = bool(words) and all(isinstance(w.get('charStart'), int) and isinstance(w.get('charEnd'), int)
                                   and narration[w['charStart']:w['charEnd']].casefold() == str(w.get('text', '')).casefold()
                                   for w in words)
    result = []
    a, b = scene.get('speechStart', scene['start']), scene.get('speechEnd', scene['end'])
    rate = (b - a) / max(1, len(narration))
    for begin, end in spans:
        chosen = [w for w in words if w['charEnd'] > begin and w['charStart'] < end] if measured else []
        if chosen:
            result.append((chosen[0]['start'], chosen[-1]['end'], True))
        else:
            result.append((round(a + begin * rate, 3), round(a + end * rate, 3), False))
    return result, bool(words) and not measured


def exact_spans(narration, texts):
    """Character spans of the given cue texts when they are exact, ordered spans of the narration."""
    spans, cursor = [], 0
    for text in texts:
        at = narration.find(text, cursor) if isinstance(text, str) and text else -1
        if at < cursor:
            return None
        spans.append((at, at + len(text)))
        cursor = at + len(text)
    return spans


def rebuild(lesson, existing):
    """One lesson's beats from its scenes, carrying over authored fields of unchanged cue text."""
    old_beats = {beat.get('id'): beat for beat in (existing or {}).get('beats', [])}
    beats, stale, missing, cues_total = [], [], 0, 0
    for scene in lesson['scenes']:
        need(SAFE_ID.fullmatch(scene['id']), f"Unsafe scene ID: {scene['id']!r}")
        narration, old = scene['narration'], old_beats.get(scene['id'], {})
        old_cues = [cue for cue in old.get('cues', []) if isinstance(cue, dict)]
        texts = [cue.get('text') for cue in old_cues]
        spans = exact_spans(narration, texts) if texts else None
        if spans and exact_text(' '.join(texts)) == exact_text(narration):
            cues = [dict(cue) for cue in old_cues]            # the author's own segmentation still covers the text
        else:
            spans = split_sentences(narration)
            by_text = {}
            for cue in old_cues:
                by_text.setdefault(cue.get('text'), cue)
            cues = [dict(by_text.get(narration[a:b], {}), text=narration[a:b]) for a, b in spans]
        timings, outdated = cue_timing(scene, spans)
        if outdated:
            stale.append(scene['id'])
        # Estimates an author or an earlier run already placed inside this scene are kept as they are.
        placed, previous = True, scene['start']
        for cue in cues:
            a, b = cue.get('start'), cue.get('end')
            placed = placed and all(isinstance(x, (int, float)) for x in (a, b)) and previous <= a < b <= scene['end'] + .01
            previous = b if placed else previous
        for cue, (start, end, measured) in zip(cues, timings):
            method = cue.get('timingMethod', '')
            if measured:
                cue.update(start=start, end=end, timingMethod=method if method.startswith('measured') else 'measured word boundaries')
            elif not placed or method.startswith('measured'):
                cue.update(start=start, end=end, timingMethod='estimated')
            else:
                cue['timingMethod'] = method or 'estimated'
        beat = {key: value for key, value in old.items() if key not in {'id', 'cues', 'start', 'end'} | DERIVED}
        derived = {'headline': scene.get('headline', '')}
        if isinstance(scene.get('fiction'), bool):
            derived['fiction'] = scene['fiction']
        beat = {'id': scene['id'], **derived, **beat, 'start': scene['start'], 'end': scene['end'], 'cues': cues}
        missing += sum(1 for cue in cues for field in CUE_FIELDS
                       if not (cue.get(field) or (field in INHERITED and beat.get(field))))
        cues_total += len(cues)
        beats.append(beat)
    entry = {key: value for key, value in (existing or {}).items() if key not in {'id', 'beats'} | DERIVED}
    context = {key: lesson[key] for key in CONTEXT if key in lesson}
    return {'id': lesson['id'], 'context': context, **entry, 'beats': beats}, {'cues': cues_total, 'missing': missing, 'stale': stale}


def untimed(value):
    if isinstance(value, dict):
        return {k: untimed(v) for k, v in value.items() if k not in TIMING | DERIVED}
    if isinstance(value, list):
        return [untimed(v) for v in value]
    return value


def sync(root, split=False):
    root = root.expanduser().resolve()
    course_path, sheet_path = root / 'course.json', root / 'visual-beat-sheet/beat-sheet.json'
    course = json.loads(course_path.read_text())
    lessons = course.get('lessons')
    need(isinstance(lessons, list) and lessons, 'Write the lesson scripts in course.json first')
    need(len({lesson.get('id') for lesson in lessons}) == len(lessons), 'Duplicate lesson IDs')
    for lesson in lessons:
        need(isinstance(lesson.get('id'), str) and SAFE_ID.fullmatch(lesson['id']), f"Unsafe lesson ID: {lesson.get('id')!r}")
        need(isinstance(lesson.get('scenes'), list) and lesson['scenes'], f"Lesson {lesson['id']} has no scenes")
        need(len({scene.get('id') for scene in lesson['scenes']}) == len(lesson['scenes']), f"Duplicate scene IDs in lesson {lesson['id']}")
        for scene in lesson['scenes']:
            need(isinstance(scene.get('narration'), str) and scene['narration'].strip(),
                 f"Scene {lesson['id']}/{scene.get('id')} has no narration")
    retimed = estimate(course)
    original = course_path.read_text()
    text = json.dumps(course, ensure_ascii=False, indent=2) + '\n'
    if retimed and text != original:
        course_path.write_text(text)
    (root / 'player').mkdir(exist_ok=True)
    (root / 'player/course-data.js').write_text('window.COURSE = ' + json.dumps(course, ensure_ascii=False) + ';\n')

    sheet = json.loads(sheet_path.read_text()) if sheet_path.is_file() else {'lessons': []}
    canonical = {entry.get('id'): entry for entry in sheet.get('lessons', [])}
    folder = sheet_path.parent / 'lessons'
    split = split or (folder.is_dir() and any(folder.glob('*.json')))
    for old in (folder.glob('*.json') if folder.is_dir() else []):
        need(old.stem in {lesson['id'] for lesson in lessons}, f'{old.relative_to(root)} names no lesson in course.json; move or delete it')
    entries, report = [], {'lessons': len(lessons), 'cues': 0, 'missingVisualFields': 0, 'toAuthor': [],
                           'estimatedTiming': retimed, 'narrationChangedSinceMeasured': []}
    for lesson in lessons:
        source, own = canonical.get(lesson['id']), folder / (lesson['id'] + '.json')
        if own.is_file():
            fragment = json.loads(own.read_text())
            need(fragment.get('id', lesson['id']) == lesson['id'], f'{own} belongs to another lesson')
            # A direct edit to the canonical sheet would be lost when the working file replaces it.
            need(not (source and untimed(source.get('beats')) != untimed(fragment.get('beats'))
                      and sheet_path.stat().st_mtime > own.stat().st_mtime + 1),
                 f"beat-sheet.json was edited after {own.relative_to(root)} and they differ for lesson {lesson['id']}. "
                 'Author in the lesson file, or delete it to keep the canonical edit.')
            source = fragment
        entry, counts = rebuild(lesson, source)
        entries.append(entry)
        report['cues'] += counts['cues']
        report['missingVisualFields'] += counts['missing']
        if counts['missing']:
            report['toAuthor'].append(lesson['id'])
        report['narrationChangedSinceMeasured'] += [f"{lesson['id']}/{scene}" for scene in counts['stale']]
    extra = {key: value for key, value in sheet.items() if key != 'lessons'}
    sheet_path.parent.mkdir(parents=True, exist_ok=True)
    sheet_path.write_text(json.dumps({**extra, 'lessons': entries}, ensure_ascii=False, indent=2) + '\n')
    if split:
        folder.mkdir(exist_ok=True)
        for entry in entries:
            (folder / (entry['id'] + '.json')).write_text(json.dumps(entry, ensure_ascii=False, indent=2) + '\n')
        report['lessonFiles'] = 'visual-beat-sheet/lessons/<lessonId>.json'
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('project', type=Path)
    parser.add_argument('--split', action='store_true', help='Keep one working beat-sheet file per lesson.')
    args = parser.parse_args()
    try:
        print(json.dumps(sync(args.project, args.split), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f'Sync failed: {error}\n')
