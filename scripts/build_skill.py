#!/usr/bin/env python3
"""Build the reviewed, self-contained skill using an explicit payload manifest."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
NAME = 'continuous-learning-video'
FORBIDDEN_SUFFIXES = {'.key', '.pem', '.p12', '.pfx', '.log', '.mp3', '.mp4', '.wav', '.zip'}
CACHE_PARTS = {'__pycache__', 'node_modules', '.DS_Store'}


def destination(path, source=None):
    path = path.expanduser().absolute()
    if path.is_symlink():
        raise ValueError(f'Refusing a symlink destination: {path}')
    path = path.parent.resolve() / path.name
    for root in [ROOT, source] if source else [ROOT]:
        root = root.resolve()
        if path == root or root in path.parents:
            raise ValueError('Output must be outside the source tree')
    if path.exists():
        raise ValueError(f'Refusing to overwrite existing path: {path}')
    return path


def payload_sources(root):
    """Only reviewed manifest paths may enter a release, regardless of Git ignores."""
    root = root.absolute()
    manifest_path = root / 'skill-files.json'
    if manifest_path.is_symlink():
        raise ValueError('Skill sources must not contain symlinks')
    manifest = json.loads(manifest_path.read_text())
    names = manifest['files']
    if not isinstance(names, list) or len(names) != len(set(names)):
        raise ValueError('Invalid or duplicate release manifest paths')
    if not {'SKILL.md', 'LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md', 'VERSION', 'skill-files.json'} <= set(names):
        raise ValueError('Release manifest omits required skill or ownership files')
    files = []
    for name in names:
        relative = PurePosixPath(name)
        if (not isinstance(name, str) or not name or relative.is_absolute()
                or relative.as_posix() != name or any(p in {'..', '.'} for p in relative.parts)
                or '\\' in name or any(p.startswith('.env') or p in CACHE_PARTS for p in relative.parts)
                or relative.suffix.lower() in FORBIDDEN_SUFFIXES):
            raise ValueError('Unsafe release manifest path')
        source = root
        for part in relative.parts:
            source = source / part
            if source.is_symlink():
                raise ValueError(f'Skill sources must not contain symlinks: {name}')
        if not source.is_file():
            raise ValueError(f'Missing regular release file: {name}')
        files.append((name, source))
    return sorted(files)


def build(output):
    output = destination(output)
    files = payload_sources(ROOT)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='skill-build-', dir=output.parent) as temporary:
        assembled = Path(temporary) / NAME
        assembled.mkdir()
        for name, source in files:
            target = assembled / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        assembled.rename(output)
    return output


def archive(skill, output):
    """Write a reproducible non-overwriting ZIP with exact payload checksums."""
    if skill.is_symlink():
        raise ValueError('Skill archive must not contain symlinks')
    skill = skill.expanduser().resolve()
    output = destination(output, skill)
    files = payload_sources(skill)
    expected = {name for name, _ in files}
    for path in skill.rglob('*'):
        relative = path.relative_to(skill)
        if path.is_symlink():
            raise ValueError('Skill archive must not contain symlinks')
        if any(part in CACHE_PARTS for part in relative.parts):
            continue
        if path.is_file() and relative.as_posix() not in expected:
            raise ValueError(f'Unlisted release file: {relative.as_posix()}')
    payload = [(name, path.read_bytes()) for name, path in files]
    manifest = {'skill': NAME, 'version': (skill / 'VERSION').read_text().strip(),
                'files': {name: hashlib.sha256(data).hexdigest() for name, data in payload}}
    payload.append(('release-manifest.json', (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, data in payload:
            info = zipfile.ZipInfo(NAME + '/' + name, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, data, compresslevel=9)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New directory outside this repository')
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()
    try:
        if args.archive:
            destination(args.archive, args.output)
        print(build(args.output))
        if args.archive:
            print(archive(args.output, args.archive))
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f'Build failed: {error}\n')
