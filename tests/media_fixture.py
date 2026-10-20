"""Synthetic audio/timing fixtures for mechanical tests; no speech generation."""
import json
import os
from pathlib import Path
import re
import subprocess
import wave

SKILL = Path(__file__).resolve().parent.parent


def media_fixture(fixture, audio_seconds):
    """Silent PCM and synthetic timings test mechanical validation only."""
    blocks = []
    def stamp(seconds, separator):
        return f'00:00:{int(seconds):02}{separator}{round((seconds % 1) * 1000):03}'
    for i, (beat, planned) in enumerate(zip(fixture.data['lessons'][0]['scenes'], fixture.sheet['lessons'][0]['beats']), 1):
        matches = list(re.finditer(r'\S+', beat['narration']))
        step = (beat['end'] - beat['start'] - .2) / len(matches)
        beat['wordTimings'] = [{'text': m.group(), 'charStart': m.start(), 'charEnd': m.end(),
                                'start': beat['start'] + j * step,
                                'end': beat['start'] + (j + .8) * step}
                               for j, m in enumerate(matches)]
        cue = planned['cues'][0]
        cue.update(start=beat['wordTimings'][0]['start'], end=beat['wordTimings'][-1]['end'],
                   timingMethod='measured synthetic fixture; not speech')
        blocks.append((i, cue['start'], cue['end'], beat['narration']))
    fixture.save()
    for extension, separator in [('srt', ','), ('vtt', '.')]:
        body = '\n\n'.join(f'{i}\n{stamp(a, separator)} --> {stamp(b, separator)}\n{text}'
                           for i, a, b, text in blocks) + '\n'
        (fixture.root / 'player/captions' / f'01.{extension}').write_text(('WEBVTT\n\n' if extension == 'vtt' else '') + body)
    with wave.open(str(fixture.root / 'audio/01.wav'), 'wb') as audio:
        audio.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
        audio.writeframes(b'\0' * round(48000 * audio_seconds))
    env = dict(os.environ)
    if not env.get('CANVAS_MODULE'):
        module = SKILL / 'assets/starter/production-source/node_modules/@napi-rs/canvas'
        if not module.exists():
            fixture.skipTest('Rendering dependencies not installed')
        env['CANVAS_MODULE'] = str(module)
    subprocess.run(['node', str(fixture.root / 'production-source/render.cjs'), 'all'], env=env, check=True, capture_output=True)
