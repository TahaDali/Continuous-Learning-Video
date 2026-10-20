#!/usr/bin/env python3
"""Optional Microsoft narration helper. Send only authorized adapted narration.
Requires an edge-tts client exposing WordBoundary events, plus FFmpeg.
No service request happens on import. --sample sends only the first narration block.
"""
import argparse
import asyncio
import hashlib
import html
import json
import inspect
from pathlib import Path
import re
import subprocess
import wave
from text_checks import check_words, exact_text

ROOT = Path(__file__).resolve().parent.parent


def norm(text):
    return exact_text(text)


def stamp(seconds, vtt=True):
    whole = round(seconds * 1000)
    hours, whole = divmod(whole, 3600000)
    minutes, whole = divmod(whole, 60000)
    secs, ms = divmod(whole, 1000)
    return f'{hours:02}:{minutes:02}:{secs:02}' + ('.' if vtt else ',') + f'{ms:03}'


def align(text, events):
    pos, words = 0, []
    for event in events:
        if event.get('type') != 'WordBoundary':
            continue
        token = html.unescape(event['text'])
        at = text.casefold().find(token.casefold(), pos)
        if at < 0:
            raise ValueError(f'Cannot align returned word {token!r} at source position {pos}')
        words.append({'text': token, 'charStart': at, 'charEnd': at + len(token),
                      'start': event['offset'] / 1e7,
                      'end': (event['offset'] + event['duration']) / 1e7})
        pos = at + len(token)
    check_words(text, words)
    return words


def stem_for(lesson, beat):
    return lesson['id'] + '-' + beat['id']


async def request(text, voice, rate, output):
    import edge_tts
    if 'boundary' not in inspect.signature(edge_tts.Communicate).parameters:
        raise ValueError('This edge-tts client lacks the required boundary option; use a compatible WordBoundary client before generating narration.')
    events = []
    temporary = output.with_suffix('.part.mp3')
    try:
        for attempt in range(3):
            try:
                events = []
                with temporary.open('wb') as f:
                    async for item in edge_tts.Communicate(
                        text, voice, rate=rate, boundary='WordBoundary',
                        connect_timeout=15, receive_timeout=40
                    ).stream():
                        if item['type'] == 'audio':
                            f.write(item['data'])
                        else:
                            events.append(item)
                words = align(text, events)
                if temporary.stat().st_size < 100:
                    raise ValueError('Empty speech result')
                temporary.replace(output)
                return words
            except Exception:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 + 3 * attempt)
    finally:
        temporary.unlink(missing_ok=True)


def finalize(data, sheet, root, voice):
    """Assemble cached measured blocks and update every downstream text/timing asset."""
    cache = root / 'audio'
    all_words, complete_transcript = [], []
    for lesson, plan in zip(data['lessons'], sheet['lessons'], strict=True):
        if lesson['id'] != plan['id']:
            raise ValueError('Beat sheet lesson IDs/order differ')
        pcm, cur, vtt, srt, cue_number = bytearray(), 0., ['WEBVTT', ''], [], 0
        transcript = [f"# {lesson['id']}. {lesson['title']}", '', lesson['goal'], '',
                      f'Synthetic narration: {voice}.', '']
        for beat, planned in zip(lesson['scenes'], plan['beats'], strict=True):
            if beat['id'] != planned['id']:
                raise ValueError('Beat IDs/order differ')
            stem = stem_for(lesson, beat)
            with wave.open(str(cache / (stem + '.wav')), 'rb') as f:
                if (f.getnchannels(), f.getsampwidth(), f.getframerate()) != (1, 2, 24000):
                    raise ValueError('Cached audio must be mono 24kHz PCM16')
                raw = f.readframes(f.getnframes())
            dur, head, tail = len(raw) / 48000, .18, .48
            measured = json.loads((cache / (stem + '.words.json')).read_text())['words']
            check_words(beat['narration'], measured)
            if measured[-1]['end'] > dur + .03:
                raise ValueError('Measured speech extends past decoded audio')
            beat.update(start=round(cur, 4), end=round(cur + head + dur + tail, 4),
                        speechStart=round(cur + head, 4), speechEnd=round(cur + head + dur, 4),
                        narrationVoice=voice)
            words = [{**w, 'start': round(w['start'] + cur + head, 4),
                      'end': round(w['end'] + cur + head, 4)} for w in measured]
            beat['wordTimings'] = words
            all_words.extend({'lesson': lesson['id'], 'beat': beat['id'], **w} for w in words)
            cursor = 0
            for cue in planned['cues']:
                at = beat['narration'].find(cue['text'], cursor)
                if at < 0:
                    raise ValueError('Cue text must be an exact span of narration')
                end = at + len(cue['text'])
                chosen = [w for w in words if w['charEnd'] > at and w['charStart'] < end]
                if not chosen:
                    raise ValueError('No measured words for sentence cue')
                cue.update(start=chosen[0]['start'], end=chosen[-1]['end'],
                           timingMethod='measured Microsoft WordBoundary')
                cursor = end
            if norm(' '.join(c['text'] for c in planned['cues'])) != norm(beat['narration']):
                raise ValueError('Sentence cues do not cover narration')
            planned.update(start=beat['start'], end=beat['end'])
            chunks, chunk = [], []
            for w in words:
                chunk.append(w)
                following = beat['narration'][w['charEnd']:w['charEnd'] + 1]
                if len(chunk) >= 10 or (following and following in '.!?;:'):
                    chunks.append(chunk)
                    chunk = []
            if chunk:
                chunks.append(chunk)
            for i, ch in enumerate(chunks):
                cue_number += 1
                text = beat['narration'][ch[0]['charStart']:ch[-1]['charEnd']]
                following = beat['narration'][ch[-1]['charEnd']:ch[-1]['charEnd'] + 1]
                if following and following in '.!?,;:':
                    text += following
                start, end = ch[0]['start'], ch[-1]['end'] + .08
                if i + 1 < len(chunks):
                    end = min(end, chunks[i + 1][0]['start'])
                vtt.extend([str(cue_number), f'{stamp(start)} --> {stamp(end)} line:86% position:50% size:88% align:center', text, ''])
                srt.extend([str(cue_number), f'{stamp(start, False)} --> {stamp(end, False)}', text, ''])
            pcm.extend(b'\0' * round(head * 24000) * 2)
            pcm.extend(raw)
            pcm.extend(b'\0' * round(tail * 24000) * 2)
            transcript.extend([f"## {stamp(cur)} — {beat['headline']}", '', beat['narration'], ''])
            cur = beat['end']
        lesson['duration'] = round(len(pcm) / 48000, 4)
        with wave.open(str(cache / (lesson['id'] + '.wav')), 'wb') as f:
            f.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
            f.writeframes(pcm)
        for suffix, lines in [('vtt', vtt), ('srt', srt)]:
            (root / 'player/captions' / f"{lesson['id']}.{suffix}").write_text('\n'.join(lines))
        (root / 'transcripts' / f"{lesson['id']}.md").write_text('\n'.join(transcript))
        complete_transcript.append('\n'.join(transcript))
    (root / 'course.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    (root / 'visual-beat-sheet/beat-sheet.json').write_text(json.dumps(sheet, ensure_ascii=False, indent=2) + '\n')
    (root / 'production-source/word-timing-manifest.json').write_text(json.dumps(all_words, ensure_ascii=False, indent=2) + '\n')
    (root / 'player/course-data.js').write_text('window.COURSE = ' + json.dumps(data, ensure_ascii=False) + ';\n')
    (root / 'transcripts/COMPLETE-TRANSCRIPT.md').write_text('\n\n---\n\n'.join(complete_transcript))


async def main(args):
    data = json.loads((ROOT / 'course.json').read_text())
    sheet = json.loads((ROOT / 'visual-beat-sheet/beat-sheet.json').read_text())
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.voice):
        raise ValueError('Use a Microsoft voice identifier, not a file path')
    for lesson in data['lessons']:
        for value in [lesson['id'], *(b['id'] for b in lesson['scenes'])]:
            if not re.fullmatch(r'[A-Za-z0-9_-]+', value):
                raise ValueError('Unsafe lesson or beat identifier')
    if args.sample:
        output = ROOT / 'review' / ('voice-sample-' + args.voice + '.mp3')
        await request(data['lessons'][0]['scenes'][0]['narration'], args.voice, args.rate, output)
        print(output)
        return
    sem = asyncio.Semaphore(args.concurrency)

    async def make(lesson, beat):
        stem = stem_for(lesson, beat)
        mp3, manifest, wav = (ROOT / 'audio' / (stem + s) for s in ['.mp3', '.words.json', '.wav'])
        rate = beat.get('rate', args.rate)
        signature = hashlib.sha256(json.dumps([args.voice, rate, beat['narration']]).encode()).hexdigest()
        async with sem:
            cached = json.loads(manifest.read_text()) if manifest.exists() else {}
            regenerated = not mp3.exists() or mp3.stat().st_size < 100 or cached.get('signature') != signature
            if regenerated:
                try:
                    words = await request(beat['narration'], args.voice, rate, mp3)
                except Exception as error:
                    raise RuntimeError(f'Narration failed for {stem} after bounded retries: {type(error).__name__}') from error
                manifest.write_text(json.dumps({'signature': signature, 'voice': args.voice, 'rate': rate, 'words': words}, indent=2))
            if regenerated or not wav.exists() or wav.stat().st_mtime < mp3.stat().st_mtime:
                subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(mp3), '-ar', '24000', '-ac', '1', '-c:a', 'pcm_s16le', str(wav)], check=True)
            print('Narration ready: ' + stem, flush=True)
    await asyncio.gather(*(make(l, s) for l in data['lessons'] for s in l['scenes']))
    finalize(data, sheet, ROOT, args.voice)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--voice', required=True)
    parser.add_argument('--rate', default='-3%')
    parser.add_argument('--sample', action='store_true')
    parser.add_argument('--concurrency', type=int, choices=range(1, 5), default=2,
                        help='Bound simultaneous speech requests; cached blocks are reused')
    asyncio.run(main(parser.parse_args()))
