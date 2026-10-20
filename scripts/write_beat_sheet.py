#!/usr/bin/env python3
"""Render the canonical sentence plan as Markdown and accessible HTML with current timing."""
import argparse
import json
from html import escape
from pathlib import Path


def write_sheet(root):
    data = json.loads((root / 'visual-beat-sheet/beat-sheet.json').read_text())
    def cell(value):
        if isinstance(value, list):
            value = '; '.join(value)
        return str(value).replace('|', '\\|').replace('\n', ' ')
    tables = []
    headers = ['Time', 'Method', 'Exact narration', 'Concept', 'Metaphor and elements',
               'Behavior', 'Next connection', 'Silent meaning', 'Risks']
    lines = ['# Visual beat sheet', '',
             'Generated from the canonical sentence plan. Timing method is stated for every cue.', '']
    for number, lesson in enumerate(data['lessons'], 1):
        rows = []
        lines += [f"## Lesson {lesson['id']}", '',
                  '| Time | Method | Exact narration | Concept | Metaphor and elements | Behavior | Next connection | Silent meaning | Risks |',
                  '|---|---|---|---|---|---|---|---|---|']
        for beat in lesson['beats']:
            for cue in beat['cues']:
                values = [f"{cue['start']:.3f}–{cue['end']:.3f}s", cue['timingMethod'], cue['text'], cue['concept'],
                          cue['metaphor'] + ': ' + '; '.join(cue['elements']), cue['behavior'], cue['next'],
                          cue['silentMeaning'], cue['risks']]
                lines.append('| ' + ' | '.join(cell(v) for v in values) + ' |')
                rows.append('<tr>' + ''.join('<td>' + escape(str(v) if not isinstance(v, list) else '; '.join(v)) + '</td>' for v in values) + '</tr>')
        lines.append('')
        heading = 'plan-lesson-' + str(number)
        title = 'Lesson ' + str(lesson['id'])
        tables.append('<section><h2 id="' + heading + '">' + escape(title) + '</h2>'
                      '<div class="scroll" tabindex="0" role="group" aria-labelledby="' + heading + '" aria-describedby="table-help">'
                      '<table aria-labelledby="' + heading + '"><thead><tr>'
                      + ''.join('<th scope="col">' + escape(h) + '</th>' for h in headers)
                      + '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div></section>')
    output = root / 'visual-beat-sheet/beat-sheet.md'
    output.write_text('\n'.join(lines) + '\n')
    # Keep the Markdown contract and offer an accessible, responsive browser view.
    course_path = root / 'course.json'
    language = json.loads(course_path.read_text()).get('language', 'en') if course_path.exists() else 'en'
    html = '<!doctype html>\n<html lang="' + escape(language, quote=True) + '"><head><meta charset="utf-8">' + \
           '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Visual beat sheet</title><style>' + \
           ':root{font:16px/1.65 Arial,sans-serif;color:#102c36;background:#f4f0e7}*{box-sizing:border-box}' + \
           'body{margin:0;padding:24px}.sheet{max-width:1440px;margin:auto}h1{font-size:clamp(2rem,5vw,3rem);line-height:1.2}' + \
           'p{color:#50686c}.scroll{max-width:100%;overflow:auto;overscroll-behavior-inline:contain}' + \
           '.scroll:focus-visible{outline:3px solid #83530d;outline-offset:4px}' + \
           'table{width:100%;min-width:1100px;border-collapse:collapse}th,td{padding:12px;border:1px solid #6e8983;text-align:left;vertical-align:top;overflow-wrap:anywhere}' + \
           'th{background:#deebe2}section{margin:32px 0}@media(max-width:700px){body{padding:16px}}' + \
           '@media(forced-colors:active){.scroll:focus-visible{outline-color:Highlight}}</style></head><body><main class="sheet">' + \
           '<h1>Visual beat sheet</h1><p>Generated from the canonical sentence plan. Timing method is stated for every cue.</p>' + \
           '<p id="table-help">Wide tables scroll horizontally. Focus a table, then use the arrow keys to read all columns.</p>' + \
           ''.join(tables) + '</main></body></html>\n'
    (output.parent / 'beat-sheet.html').write_text(html)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    args = parser.parse_args()
    print(write_sheet(args.project.expanduser().resolve()))
