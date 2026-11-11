#!/usr/bin/env python3
"""Sample every narration sentence's end state into per-scene contact sheets for a reviewer.

For each scene it grabs the frame 0.6 s into the scene and, for every sentence, the frame `lead`
seconds before the sentence's last word ends: the state that sentence should have produced. When
the frame audit recorded transitions for the lesson, each transition's midpoint is sampled too.
It writes a plan (`<lesson>-plan.json`), a reviewer brief (`<lesson>-brief.md`: every sheet beside
its sentences, then the checklist), full-size frames and two-column, time-stamped sheets, and
prints the brief unless --quiet. `all` samples every lesson. ffmpeg does all image work.
It refuses a video whose length is not the lesson's, and the plan records which video each scene
came from. It does not judge the frames; a person or reviewer agent must look at every sheet.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Optional

SAFE_ID = re.compile(r'[a-zA-Z0-9_-]+')
# A sentence ends at . ! ? or … plus any closing quotes/brackets, followed by space or the end.
CLOSERS = '"\'”’)]'
BOUNDARY = re.compile(r'[.!?…]+["\'”’)\]]*(?=\s|$)')
# A full stop after these never ends a sentence; after NUMBERED ones only when a number follows.
ABBREVIATIONS = {'mr', 'mrs', 'ms', 'dr', 'prof', 'st', 'mt', 'vs', 'e.g', 'i.e', 'cf', 'approx', 'incl', 'dept', 'esp'}
NUMBERED = {'no', 'nos', 'fig', 'vol', 'p', 'pp', 'ch', 'sec', 'art'}
# These may end a sentence, so they continue one only when a lower-case word follows ("etc. and").
CONTINUING = {'etc', 'al', 'inc', 'ltd', 'co', 'corp', 'jr', 'sr'}
# A lower-case name with an inner capital ("iPhone", "eBay", "iOS") starts a sentence like any capital.
CAMEL = re.compile(r'[a-z]+[A-Z]')
OPENING = '[scene opens]'
TRANSITION = '[transition midpoint]'
CHECKLIST = [
    'The tile shows the state its sentence has just described: nothing it names is missing, nothing from a later sentence is already there.',
    'Each reveal lands on its spoken word, not on an earlier occurrence of the same word in the scene (compare the tiles before it).',
    'No stale callout, highlight or label from the previous beat remains where it reads as the cause of the next one.',
    'Nothing on screen answers a question the narration has not asked or answered yet.',
    'Counted groups are complete: a camera push or fade must not hide part of a group the narration counts.',
    'Every label is readable: large enough, not sliced by the frame edge, not under the caption band, and on screen long enough to read (at least 0.5 s; check neighbouring tiles or the clip).',
    'A recurring real person looks the same here as in every other lesson.',
    'Invented people, companies and figures carry the fiction badge (practice panels too); purely real facts do not.',
    'Meaning colours are honest: the highlighter (signal) marks only what is being spoken about now; the wrong red marks only '
    'what is wrong or blocked (the red-orange accent marks change and attention annotations and is not a fault).',
    'A transition tile (~) shows both scenes or the incoming one, never a blank page, and starts after the last reveal could be read.',
]
# What a clean frame audit of the same render already established on every frame, so a reviewer
# spends attention on meaning. It lists the checks; it does not claim the audit was run.
AUDITED = ('A clean frame audit (production-source/audit.cjs) already checks every frame of a design-system world for '
           'type floors, frame-edge and caption-band clearance of registered labels, the 24-word budget, registered '
           'overlaps, labels on screen for under 0.5 s, and the fiction badge in scenes that declare `fiction`; a repeated '
           'cue word without its occurrence and a changed cast look fail when the world is drawn. Those items still '
           'deserve a finding when a tile shows them, but most of the review is the meaning the audit cannot see.')
# 5x7 bitmap glyphs for the time stamps, so sheets need neither PIL nor an ffmpeg font filter.
GLYPHS = {
    '0': '01110 10001 10011 10101 11001 10001 01110', '1': '00100 01100 00100 00100 00100 00100 01110',
    '2': '01110 10001 00001 00010 00100 01000 11111', '3': '11110 00001 00001 01110 00001 00001 11110',
    '4': '00010 00110 01010 10010 11111 00010 00010', '5': '11111 10000 11110 00001 00001 10001 01110',
    '6': '00110 01000 10000 11110 10001 10001 01110', '7': '11111 00001 00010 00100 01000 01000 01000',
    '8': '01110 10001 10001 01110 10001 10001 01110', '9': '01110 10001 10001 01111 00001 00010 01100',
    '.': '00000 00000 00000 00000 00000 01100 01100', '=': '00000 00000 11111 00000 11111 00000 00000',
    't': '01000 01000 11100 01000 01000 01001 00110', 's': '00000 00000 01110 10000 01110 00001 11110',
    '#': '01010 01010 11111 01010 11111 01010 01010', '-': '00000 00000 00000 11111 00000 00000 00000',
    '~': '00000 00000 01000 10101 00010 00000 00000',
    ' ': '00000 00000 00000 00000 00000 00000 00000'}
# Red stamps on white strips; grey gutters keep paper-coloured frames apart.
INK, PAPER, GUTTER, GAP = (210, 20, 20), (255, 255, 255), (150, 150, 150), 6


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Character spans of the sentences in `text`, stripped of surrounding space."""
    spans, begin = [], 0
    for m in BOUNDARY.finditer(text):
        before = text[begin:m.start()].split()
        token = before[-1].lstrip('"\'“‘([').lower() if before else ''
        after, mark = text[m.end():].lstrip(), m.group()
        full_stop = mark[0] == '.' and not mark.startswith('..')
        if full_stop and (token in ABBREVIATIONS or (token in NUMBERED and after[:1].isdigit())):
            continue
        # A lower-case word continues the sentence only after a closing quote ('"Why?" she asked'), an
        # ellipsis ("Then... wait") or an abbreviation ("9 a.m. and", "etc. and"); otherwise it starts one
        # ("npm installs doubled.").
        word = after.split(maxsplit=1)[0] if after else ''
        if word[:1].islower() and not CAMEL.match(word):
            abbreviated = full_stop and ('.' in token or token in CONTINUING or token in NUMBERED)
            if mark[-1] in CLOSERS or '..' in mark or '…' in mark or abbreviated:
                continue
        spans.append((begin, m.end()))
        begin = m.end()
    if text[begin:].strip():
        spans.append((begin, len(text)))
    result = []
    for a, b in spans:
        a += len(text[a:b]) - len(text[a:b].lstrip())
        b -= len(text[a:b]) - len(text[a:b].rstrip())
        if b > a:
            result.append((a, b))
    return result


def _offsets(narration, words):
    """Words keep their charStart; older timings without one are located in order."""
    located, cursor = [], 0
    for w in words:
        if not isinstance(w.get('charStart'), int):
            at = narration.casefold().find(str(w.get('text', '')).casefold(), cursor)
            if at < 0:
                raise ValueError(f'Word timing {w.get("text")!r} is not in the narration')
            w = dict(w, charStart=at)
        cursor = max(cursor, w['charStart'] + 1)
        located.append(w)
    return located


def timed_words(scene: dict, cues: Optional[list] = None) -> tuple[list[dict], str]:
    """Measured word timings, or estimates spread by character position over the beat-sheet cues."""
    narration = scene['narration']
    if scene.get('wordTimings'):
        return _offsets(narration, scene['wordTimings']), 'measured'
    spans, cursor = [], 0
    for cue in cues or []:
        at = narration.find(cue.get('text', ''), cursor)
        if cue.get('text') and at >= cursor and cue.get('end', 0) > cue.get('start', 0):
            spans.append((at, at + len(cue['text']), cue['start'], cue['end']))
            cursor = at + len(cue['text'])
    if not spans:
        spans = [(0, len(narration), scene.get('speechStart', scene['start']), scene.get('speechEnd', scene['end']))]
    words = []
    for m in re.finditer(r'\S+', narration):
        span = next((s for s in spans if s[0] <= m.start() < s[1]), None)
        if span:
            a, b, ta, tb = span
            rate = (tb - ta) / max(1, b - a)
            words.append({'text': m.group(), 'charStart': m.start(), 'start': ta + (m.start() - a) * rate,
                          'end': ta + (min(m.end(), b) - a) * rate})
    return words, 'estimated'


def scene_points(scene: dict, lead: float = .15, opening: float = .6, cues: Optional[list] = None,
                 frame: float = 1 / 24) -> dict:
    """The scene's review points: [time, sentence] for the opening and each sentence's end state."""
    words, timing = timed_words(scene, cues)
    start, end = scene['start'], scene['end']
    last = max(start, end - frame)
    def clamp(t):
        return round(min(max(t, start), last), 2)
    points, unmapped = [[clamp(start + opening), OPENING]], []
    for a, b in split_sentences(scene['narration']):
        sentence = scene['narration'][a:b]
        # Map by character offsets, never by word text: the same word recurs across sentences.
        inside = [w for w in words if a <= w['charStart'] < b]
        if inside:
            points.append([clamp(inside[-1]['end'] - lead), sentence])
        else:
            unmapped.append(sentence)
    return {'scene': scene['id'], 'headline': scene.get('headline', ''), 'start': start, 'end': end,
            'timing': timing, 'points': points, 'unmapped': unmapped}


def load_lesson(project: Path, lesson_id: str) -> tuple[dict, dict]:
    """The course and one of its lessons from course.json."""
    course = json.loads((project / 'course.json').read_text())
    lesson = next((l for l in course['lessons'] if l['id'] == lesson_id), None)
    if lesson is None:
        raise ValueError(f'No lesson {lesson_id!r} in course.json')
    return course, lesson


def lesson_plan(project: Path, lesson_id: str, lead: float = .15, scenes: Optional[list] = None) -> list[dict]:
    """Review points for every (or each selected) scene of one lesson."""
    course, lesson = load_lesson(project, lesson_id)
    return _plan(project, course, lesson, lead, scenes)


def _plan(project, course, lesson, lead, scenes):
    lesson_id = lesson['id']
    sheet_path = project / 'visual-beat-sheet/beat-sheet.json'
    beats = {}
    if sheet_path.is_file():
        plan = next((l for l in json.loads(sheet_path.read_text()).get('lessons', []) if l.get('id') == lesson_id), {})
        beats = {b.get('id'): b.get('cues', []) for b in plan.get('beats', [])}
    chosen = [s for s in lesson['scenes'] if not scenes or s['id'] in scenes]
    missing = set(scenes or []) - {s['id'] for s in chosen}
    if missing:
        raise ValueError('No such scene: ' + ', '.join(sorted(missing)))
    for s in chosen:
        if not SAFE_ID.fullmatch(s['id']):
            raise ValueError(f'Unsafe scene ID: {s["id"]!r}')
    return [scene_points(s, lead, cues=beats.get(s['id']), frame=1 / course.get('fps', 24)) for s in chosen]


def audit_transitions(project: Path, lesson: dict, fps: float) -> list[float]:
    """Midpoints of the transitions the frame audit recorded for this lesson, if it covers this timing."""
    try:
        report = json.loads((project / 'review/frame-audit.json').read_text())
        record = next(r for r in report['lessons'] if r.get('id') == lesson['id'])
        if record.get('frames') != math.ceil(lesson['duration'] * fps):
            return []
        return [round((a + b) / 2, 2) for a, b in record.get('transitions', [])]
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        return []


def _probe(video):
    """Width, height and duration of the video, and whether it carries an audio stream."""
    info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                                      'stream=codec_type,width,height:format=duration', '-of', 'json', str(video)],
                                     check=True, capture_output=True, text=True).stdout)
    streams = info.get('streams', [])
    pictures = [s for s in streams if s.get('codec_type') == 'video']
    if not pictures:
        raise ValueError(f'No video stream in {video}')
    audio = any(s.get('codec_type') == 'audio' for s in streams)
    return pictures[0]['width'], pictures[0]['height'], float(info['format']['duration']), audio


def grab(video: Path, time: float, size: tuple[int, int], full: Optional[Path] = None) -> bytes:
    """One frame at `time` as scaled RGB bytes; also saved full-size to `full` when given."""
    w, h = size
    command = ['ffmpeg', '-v', 'error', '-y', '-ss', f'{time:.3f}', '-i', str(video)]
    if full:
        command += ['-map', '0:v:0', '-frames:v', '1', str(full)]
    command += ['-map', '0:v:0', '-frames:v', '1', '-vf', f'scale={w}:{h}:flags=lanczos',
                '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1']
    result = subprocess.run(command, capture_output=True)
    if result.returncode or len(result.stdout) != w * h * 3:
        raise ValueError(f'No frame at {time:.2f} s in {video}: {result.stderr.decode(errors="replace").strip()}')
    return result.stdout


def _stamp(pixels, width, x, y, text, limit, unit):
    """Draw `text` in the bitmap font at (x, y), clipped at x + limit."""
    for k, char in enumerate(text):
        for row, bits in enumerate(GLYPHS.get(char, GLYPHS[' ']).split()):
            for col, bit in enumerate(bits):
                if bit != '1':
                    continue
                gx = x + (k * 6 + col) * unit
                if gx + unit > x + limit:
                    continue
                for dy in range(unit):
                    at = ((y + row * unit + dy) * width + gx) * 3
                    pixels[at:at + unit * 3] = bytes(INK) * unit


def contact_sheet(tiles: list[bytes], labels: list[str], size: tuple[int, int], output: Path, columns: int = 2) -> Path:
    """Tile scaled RGB frames under their time stamps and encode the sheet as PNG with ffmpeg."""
    w, h = size
    unit = 3 if w >= 360 else 2 if w >= 200 else 1
    strip = 7 * unit + 8
    rows = (len(tiles) + columns - 1) // columns
    width, height = columns * w + (columns - 1) * GAP, rows * (strip + h) + (rows - 1) * GAP
    pixels = bytearray(bytes(GUTTER) * (width * height))
    for k, (tile, label) in enumerate(zip(tiles, labels)):
        x, y = (k % columns) * (w + GAP), (k // columns) * (strip + h + GAP)
        for row in range(strip):
            at = ((y + row) * width + x) * 3
            pixels[at:at + w * 3] = bytes(PAPER) * w
        _stamp(pixels, width, x + 4, y + 4, label, w - 8, unit)
        for row in range(h):
            at = ((y + strip + row) * width + x) * 3
            pixels[at:at + w * 3] = tile[row * w * 3:(row + 1) * w * 3]
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{width}x{height}',
                    '-i', 'pipe:0', '-frames:v', '1', str(output)], input=bytes(pixels), check=True, capture_output=True)
    return output


def output_folder(project: Path, silent: bool = False) -> Path:
    """The default output: silent-preview runs never share a folder with the final encode's evidence."""
    return project / ('review/sentence-end-silent' if silent else 'review/sentence-end')


def review_lesson(project: Path, lesson_id: str, out: Optional[Path] = None, video: Optional[Path] = None,
                  lead: float = .15, scale: float = .5, silent: bool = False, scenes: Optional[list] = None,
                  jobs: Optional[int] = None) -> list[dict]:
    """Write the plan, the reviewer brief, full-size frames and one contact sheet per scene; return the plan."""
    if not SAFE_ID.fullmatch(lesson_id):
        raise ValueError(f'Unsafe lesson ID: {lesson_id!r}')
    if not 0 <= lead < 5 or not 0 < scale <= 1:
        raise ValueError('Use 0 <= --lead < 5 and 0 < --scale <= 1')
    for tool in ('ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            raise ValueError(f'{tool} is required')
    # Validate the course, lesson and scenes before looking for a video.
    course, lesson = load_lesson(project, lesson_id)
    plan = _plan(project, course, lesson, lead, scenes)
    expected, fps = lesson.get('duration'), course.get('fps', 24)
    if not isinstance(expected, (int, float)) or expected <= 0:
        raise ValueError(f'Lesson {lesson_id} has no duration in course.json')
    hint = '' if video or silent else ' (use --silent for review/silent previews)'
    video = video or project / ('review/silent' if silent else 'player/videos') / f'{lesson_id}.mp4'
    if not video.is_file():
        raise ValueError(f'Missing video: {video}{hint}')
    video = video.resolve()
    vw, vh, duration, audio = _probe(video)
    # Every render is encoded to its lesson's duration, so another length means another lesson's video or
    # one rendered before the narration changed; its frames would be labelled with the wrong sentences.
    if abs(duration - expected) > 1 / fps + .1:
        raise ValueError(f'{video} lasts {duration:.2f} s but lesson {lesson_id} lasts {expected:.2f} s in course.json; '
                         'render this lesson again or pass its current video')
    late = [t for scene in plan for t, _ in scene['points'] if t >= duration]
    if late:
        raise ValueError(f'{video} ends at {duration:.2f} s, before sample {late[0]:.2f} s; render this lesson again')
    out = out or output_folder(project, silent)
    path, kept = out / f'{lesson_id}-plan.json', []
    if scenes and path.is_file():
        # A --scene re-run keeps the other scenes only when they were sampled from this video at the times
        # course.json gives now, so one plan never mixes a silent preview with the final encode.
        fresh = {p['scene']: p['points'] for p in _plan(project, course, lesson, lead, None)}
        chosen = {p['scene'] for p in plan}
        kept = [p for p in json.loads(path.read_text()) if p.get('scene') in fresh and p['scene'] not in chosen]
        stale = [p['scene'] for p in kept if p.get('video') != str(video) or p.get('points') != fresh[p['scene']]]
        if stale:
            raise ValueError(f'{path} holds scenes sampled from another video or at other times ({", ".join(stale)}); '
                             'rerun every scene without --scene, or pass --out for a separate record')
    path.unlink(missing_ok=True)
    frames, sheets = out / 'frames' / lesson_id, out / 'sheets' / lesson_id
    keep = {p['scene'] for p in kept}
    # Clear all earlier evidence except the kept scenes', so a renamed, removed or shortened scene leaves none.
    for folder, suffix in ((frames, r'-t?\d+\.png'), (sheets, r'\.png')):
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob('*.png'):
            if not any(re.fullmatch(re.escape(s) + suffix, old.name) for s in keep):
                old.unlink()
    modified = datetime.fromtimestamp(video.stat().st_mtime, timezone.utc).isoformat(timespec='seconds')
    size = (max(2, round(vw * scale)), max(2, round(vh * scale)))
    # A transition's midpoint joins the sheet of the scene it falls in, after that scene's sentences.
    midpoints = [t for t in audit_transitions(project, lesson, fps) if t < duration]
    work = []
    for scene in plan:
        # Each scene records what it was sampled from: a merged plan shows which encode each came from.
        scene.update(video=str(video), videoDuration=round(duration, 3), videoModified=modified, silent=not audio)
        scene['transitions'] = [t for t in midpoints if scene['start'] <= t < scene['end']]
        scene['frames'] = [str(frames / f'{scene["scene"]}-{k:02}.png') for k in range(len(scene['points']))]
        scene['transitionFrames'] = [str(frames / f'{scene["scene"]}-t{k:02}.png') for k in range(len(scene['transitions']))]
        work += [(t, Path(full)) for (t, _), full in zip(scene['points'], scene['frames'])]
        work += [(t, Path(full)) for t, full in zip(scene['transitions'], scene['transitionFrames'])]
    # Each grab is its own ffmpeg process, so threads are enough to use every core.
    with ThreadPoolExecutor(max_workers=max(1, jobs or min(8, os.cpu_count() or 1))) as pool:
        grabbed = iter(list(pool.map(lambda item: grab(video, item[0], size, item[1]), work)))
    for scene in plan:
        tiles = [next(grabbed) for _ in scene['points']] + [next(grabbed) for _ in scene['transitions']]
        labels = [f'#{k} t={t:.2f}s' for k, (t, _) in enumerate(scene['points'])]
        labels += [f'~{k} t={t:.2f}s' for k, t in enumerate(scene['transitions'])]
        scene['sheet'] = str(contact_sheet(tiles, labels, size, sheets / f'{scene["scene"]}.png'))
    merged = sorted(kept + plan, key=lambda p: p['start'])
    path.write_text(json.dumps(merged, indent=1, ensure_ascii=False) + '\n')
    # The brief always covers the whole lesson, so a --scene re-run leaves one complete reviewer file.
    (out / f'{lesson_id}-brief.md').write_text(report(merged, lesson_id, out, lead) + '\n')
    return plan


def summary(plan: list[dict], lesson_id: str) -> str:
    """One line of coverage: scenes, sentences, frames and what could not be sampled."""
    sentences = sum(len(p['points']) - 1 for p in plan)
    unmapped = sum(len(p['unmapped']) for p in plan)
    moves = sum(len(p.get('transitions', [])) for p in plan)
    return (f'Lesson {lesson_id}: {len(plan)} scenes, {sentences} sentences sampled, '
            f'{sentences + len(plan)} frames, {unmapped} sentences unmapped.'
            + (f' {moves} transition midpoints sampled.' if moves else ''))


def report(plan: list[dict], lesson_id: str, out: Path, lead: float = .15) -> str:
    """The sentence list per sheet, coverage numbers and the reviewer checklist, as printed."""
    lines = []
    if plan and plan[0].get('video'):
        source = plan[0]
        kind = 'silent, no audio stream' if source['silent'] else 'with audio'
        lines.append(f"Lesson {lesson_id} sampled from {source['video']} ({kind}, {source['videoDuration']:.2f} s, "
                     f"modified {source['videoModified']})")
    for p in plan:
        lines.append(f"\n## {p['scene']} — {p['headline']} ({p['start']:.1f}–{p['end']:.1f} s, {p['timing']} timing)"
                     f"\n   sheet: {p.get('sheet', '')}")
        lines += [f'  #{k:<2} {t:7.2f}  {sentence}' for k, (t, sentence) in enumerate(p['points'])]
        lines += [f'  ~{k:<2} {t:7.2f}  {TRANSITION}' for k, t in enumerate(p.get('transitions', []))]
        lines += [f'  UNMAPPED  {sentence}' for sentence in p['unmapped']]
    lines += ['', summary(plan, lesson_id), f'Plan: {out / (lesson_id + "-plan.json")}']
    estimated = [p['scene'] for p in plan if p['timing'] != 'measured']
    if estimated:
        lines.append('Estimated timing (no measured word timings): ' + ', '.join(estimated))
    lines += ['', f'Reviewer checklist. Tile #0 is 0.6 s into the scene; tile #k is {lead:.2f} s before sentence k ends; '
                  'tile ~k is the midpoint of a transition the frame audit recorded.', AUDITED,
              'View every sheet against its sentences and check, per tile:']
    lines += [f'  [ ] {item}' for item in CHECKLIST]
    lines += ['Record each finding as lesson, scene, time, sentence, what is wrong and why it misleads.',
              'Confirm it on the full-size frame under frames/ (or a fresh clip) before fixing; findings default to refuted.']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('project', type=Path)
    parser.add_argument('lesson', help='A lesson ID, or "all" for every lesson in course.json.')
    parser.add_argument('--out', type=Path, help='Output folder (default <project>/review/sentence-end, '
                                                 'or review/sentence-end-silent with --silent).')
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--video', type=Path, help='Video to sample (default player/videos/<lesson>.mp4).')
    source.add_argument('--silent', action='store_true', help='Sample review/silent/<lesson>.mp4 instead.')
    parser.add_argument('--lead', type=float, default=.15, help='Seconds before each sentence ends (default 0.15).')
    parser.add_argument('--scale', type=float, default=.5, help='Tile scale on the sheets (default 0.5).')
    parser.add_argument('--scene', action='append', help='Only this scene ID; repeat for more (re-verification).')
    parser.add_argument('--quiet', action='store_true',
                        help='Print one coverage line per lesson and the brief path; the sentences and checklist are in the brief.')
    parser.add_argument('--jobs', type=int, help='Frames to grab at once (default: one per core, at most 8).')
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    out = args.out.expanduser().resolve() if args.out else output_folder(project, args.silent)
    try:
        lessons = [args.lesson]
        if args.lesson == 'all':
            lessons = [l['id'] for l in json.loads((project / 'course.json').read_text())['lessons']]
            if 'all' in lessons:
                lessons = ['all']                     # a lesson really named "all" is just that lesson
            elif args.scene or args.video:
                raise ValueError('--scene and --video name one lesson; "all" samples each lesson\'s own video')
        for lesson in lessons:
            plan = review_lesson(project, lesson, out, args.video and args.video.expanduser().resolve(),
                                 args.lead, args.scale, args.silent, args.scene, args.jobs)
            if args.quiet:
                estimated = sum(1 for p in plan if p['timing'] != 'measured')
                print(summary(plan, lesson) + (f' {estimated} scenes on estimated timing.' if estimated else '')
                      + f' Brief: {out / (lesson + "-brief.md")}')
            else:
                print(report(plan, lesson, out, args.lead))
    except (ValueError, KeyError, OSError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Review frames failed: {error}\n')


if __name__ == '__main__':
    main()
