#!/usr/bin/env python3
"""Assemble one self-contained skill from maintained research and video modules."""
import argparse
from pathlib import Path
import shutil
import json
import hashlib
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
NAME = 'job-to-learning-videos'
IGNORE = shutil.ignore_patterns('node_modules', '__pycache__', '.DS_Store', '.env', '.env.*')


def safe_ignore(directory, names):
    excluded = set(IGNORE(directory, names))
    for name in set(names) - excluded:
        entry = Path(directory) / name
        if entry.is_symlink():
            raise ValueError(f'Skill sources must not contain symlinks: {entry}')
        if not entry.is_file() and not entry.is_dir():
            raise ValueError(f'Unsupported skill source: {entry}')
    return excluded


def copy_sources(source, target, **kwargs):
    if source.is_symlink():
        raise ValueError(f'Skill sources must not contain symlinks: {source}')
    return shutil.copytree(source, target, ignore=safe_ignore, **kwargs)


def destination(path):
    path = path.expanduser().absolute()
    if path.is_symlink():
        raise ValueError(f'Refusing a symlink destination: {path}')
    # Canonicalize ordinary parent aliases such as macOS /var -> /private/var,
    # while keeping a dangling leaf symlink from redirecting a new output.
    path = path.parent.resolve() / path.name
    if path.exists():
        raise ValueError(f'Refusing to overwrite existing path: {path}')
    return path


def build(output):
    output = destination(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='skill-build-', dir=output.parent) as temporary:
        assembled = Path(temporary) / NAME
        copy_sources(ROOT / 'packages' / NAME, assembled)
        research = ROOT / 'skills/company-role-storyteller/references'
        video = ROOT / 'skills/continuous-learning-videos'
        copy_sources(research, assembled / 'references/research')
        copy_sources(video / 'references', assembled / 'references/video')
        copy_sources(video / 'assets', assembled / 'assets')
        copy_sources(video / 'scripts', assembled / 'scripts', dirs_exist_ok=True)
        for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md'):
            source = ROOT / name
            if source.is_symlink():
                raise ValueError(f'Skill sources must not contain symlinks: {source}')
            shutil.copyfile(source, assembled / name)
        assembled.rename(output)
    return output


def archive(skill, output):
    """Create a reproducible, non-overwriting ZIP with per-file checksums."""
    output = destination(output)
    skill = skill.expanduser().absolute()
    if skill.is_symlink():
        raise ValueError(f'Skill archive must not contain symlinks: {skill}')
    skill = skill.resolve()
    files = []
    for path in sorted(skill.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Skill archive must not contain symlinks: {path}')
        if path.is_file():
            files.append((path.relative_to(skill).as_posix(), path.read_bytes()))
    if not any(name == 'SKILL.md' for name, _ in files):
        raise ValueError('Archive source must be an assembled skill containing SKILL.md.')
    manifest = {'skill': NAME, 'files': {name: hashlib.sha256(data).hexdigest() for name, data in files}}
    files.append(('release-manifest.json', (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, data in files:
            info = zipfile.ZipInfo(NAME + '/' + name, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, data, compresslevel=9)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--archive', type=Path, help='Also write a reproducible ZIP with a checksum manifest.')
    args = parser.parse_args()
    try:
        if args.archive:
            destination(args.archive)
        print(build(args.output))
        if args.archive:
            print(archive(args.output, args.archive))
    except ValueError as error:
        parser.exit(1, f'{error}\n')
