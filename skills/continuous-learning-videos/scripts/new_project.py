#!/usr/bin/env python3
"""Create a clean local motion project; never overwrite an existing directory."""
import argparse
import json
import shutil
import uuid
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output', type=Path)
    p.add_argument('--title', default='Continuous learning course')
    p.add_argument('--demo', action='store_true', help='Install the explicit 12-second mechanical demonstration instead of an empty authoring project.')
    args = p.parse_args()
    target = args.output.expanduser().resolve()
    if target.exists():
        p.error(f'Refusing to overwrite existing path: {target}')
    source = Path(__file__).resolve().parent.parent / 'assets' / 'starter'
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('node_modules', '__pycache__', '.DS_Store', '.env', '.env.*'))
    for folder in ['audio', 'transcripts', 'review', 'player/videos',
                   'player/posters', 'player/captions']:
        (target / folder).mkdir(parents=True, exist_ok=True)
    data = json.loads((target / 'course.json').read_text())
    if not args.demo:
        data['lessons'] = []
        (target / 'visual-beat-sheet/beat-sheet.json').write_text('{"lessons": []}\n')
        (target / 'production-source/world.cjs').write_text(
            "'use strict';\n"
            "function draw() { throw new Error('No authored visual world. Implement this course and fail explicitly for every unsupported lesson. Use new_project.py --demo only for the separate mechanical example.'); }\n"
            "module.exports = {draw};\n")
    data['title'] = args.title
    data['storageKey'] = 'motion-course-' + uuid.uuid4().hex
    (target / 'course.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    (target / 'player/course-data.js').write_text('window.COURSE = ' + json.dumps(data, ensure_ascii=False) + ';\n')
    print(target)
    print('Created an explicit mechanical demonstration; not a subject course.' if args.demo else
          'Created an empty authoring project. The renderer refuses to draw until its subject world is implemented.')


if __name__ == '__main__':
    main()
