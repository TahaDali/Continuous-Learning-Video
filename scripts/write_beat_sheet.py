#!/usr/bin/env python3
"""Render the canonical sentence plan as readable Markdown with current timing."""
import argparse
import json
from pathlib import Path


def write_sheet(root):
    data = json.loads((root / 'visual-beat-sheet/beat-sheet.json').read_text())
    def cell(value):
        if isinstance(value, list):
            value = '; '.join(value)
        return str(value).replace('|', '\\|').replace('\n', ' ')
    lines = ['# Visual beat sheet', '',
             'Generated from the canonical sentence plan. Timing method is stated for every cue.', '']
    for lesson in data['lessons']:
        lines += [f"## Lesson {lesson['id']}", '',
                  '| Time | Method | Exact narration | Concept | Metaphor and elements | Behavior | Next connection | Silent meaning | Risks |',
                  '|---|---|---|---|---|---|---|---|---|']
        for beat in lesson['beats']:
            for cue in beat['cues']:
                values = [f"{cue['start']:.3f}–{cue['end']:.3f}s", cue['timingMethod'], cue['text'], cue['concept'],
                          cue['metaphor'] + ': ' + cell(cue['elements']), cue['behavior'], cue['next'],
                          cue['silentMeaning'], cue['risks']]
                lines.append('| ' + ' | '.join(cell(v) for v in values) + ' |')
        lines.append('')
    output = root / 'visual-beat-sheet/beat-sheet.md'
    output.write_text('\n'.join(lines) + '\n')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    args = parser.parse_args()
    print(write_sheet(args.project.expanduser().resolve()))
