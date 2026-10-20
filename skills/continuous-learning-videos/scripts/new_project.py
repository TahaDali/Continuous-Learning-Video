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
    args = p.parse_args()
    target = args.output.expanduser().resolve()
    if target.exists():
        p.error(f'Refusing to overwrite existing path: {target}')
    source = Path(__file__).resolve().parent.parent / 'assets' / 'starter'
    shutil.copytree(source, target)
    for folder in ['audio', 'transcripts', 'review', 'player/videos',
                   'player/posters', 'player/captions']:
        (target / folder).mkdir(parents=True, exist_ok=True)
    data = json.loads((target / 'course.json').read_text())
    data['title'] = args.title
    data['storageKey'] = 'motion-course-' + uuid.uuid4().hex
    (target / 'course.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    (target / 'player/course-data.js').write_text('window.COURSE = ' + json.dumps(data, ensure_ascii=False) + ';\n')
    print(target)
    print('Created a demonstration starter. Replace its sample script, beat sheet and world before delivery.')


if __name__ == '__main__':
    main()
