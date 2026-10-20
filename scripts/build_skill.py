#!/usr/bin/env python3
"""Assemble one self-contained skill from maintained research and video modules."""
import argparse
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parent.parent
NAME = 'job-to-learning-videos'
IGNORE = shutil.ignore_patterns('node_modules', '__pycache__', '.DS_Store', '.env', '.env.*')


def build(output):
    output = output.expanduser().resolve()
    if output.exists():
        raise ValueError(f'Refusing to overwrite existing path: {output}')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='skill-build-', dir=output.parent) as temporary:
        assembled = Path(temporary) / NAME
        shutil.copytree(ROOT / 'packages' / NAME, assembled, ignore=IGNORE)
        research = ROOT / 'skills/company-role-storyteller/references'
        video = ROOT / 'skills/continuous-learning-videos'
        shutil.copytree(research, assembled / 'references/research', ignore=IGNORE)
        shutil.copytree(video / 'references', assembled / 'references/video', ignore=IGNORE)
        shutil.copytree(video / 'assets', assembled / 'assets', ignore=IGNORE)
        shutil.copytree(video / 'scripts', assembled / 'scripts', dirs_exist_ok=True, ignore=IGNORE)
        assembled.rename(output)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(build(args.output))
    except ValueError as error:
        parser.exit(1, f'{error}\n')
