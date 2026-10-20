#!/usr/bin/env python3
"""Check portable skill resources and exercise the video starter without speech requests."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
VIDEO = ROOT
from build_skill import payload_sources
from design_checks import design_token_findings


def run(*args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check(render=False):
    node = shutil.which('node')
    require(node, 'Node.js is required for JavaScript syntax checks.')
    files = [path for _, path in payload_sources(ROOT)]
    files += [ROOT / name for name in ('README.md', 'CONTRIBUTING.md', 'SECURITY.md', 'CHANGELOG.md')]
    files += list((ROOT / 'docs').glob('*.md'))
    entry = (ROOT / 'SKILL.md').read_text()
    require(re.search(r'^name: continuous-learning-video$', entry, re.M), 'Incorrect skill name')
    require(re.search(r'^description: .+', entry, re.M), 'Missing skill description')
    require(len([p for p in ROOT.rglob('SKILL.md') if not any(part in {'dist', 'node_modules', '.git'} for part in p.relative_to(ROOT).parts)]) == 1, 'Repository must expose exactly one skill')
    links = 0
    for path in files:
        if path.suffix == '.py':
            compile(path.read_text(), str(path), 'exec')
        elif path.suffix in {'.js', '.cjs'}:
            run(node, '--check', path)
        elif path.suffix == '.json':
            json.loads(path.read_text())
        elif path.suffix == '.md':
            for destination in re.findall(r'\]\(([^\s)]+)\)', path.read_text()):
                if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', destination) or destination.startswith('#'):
                    continue
                target = unquote(destination.split('#', 1)[0])
                require((path.parent / target).is_file(), f'Broken local link in {path}: {destination}')
                links += 1
    with tempfile.TemporaryDirectory(prefix='learning-skills-check-') as temporary:
        project = Path(temporary) / 'course'
        other = Path(temporary) / 'other'
        generator = VIDEO / 'scripts/new_project.py'
        validator = VIDEO / 'scripts/validate_project.py'
        designed = Path(temporary) / 'designed'
        for target in (project, other):
            run(sys.executable, generator, target, '--demo', '--title', 'Portable starter check')
            run(sys.executable, validator, target)
        run(sys.executable, generator, designed, '--design-demo', '--title', 'Design system check')
        run(sys.executable, validator, designed)
        require(not design_token_findings(designed), 'Design demonstration hard-codes colour or type.')
        course = json.loads((project / 'course.json').read_text())
        other_course = json.loads((other / 'course.json').read_text())
        require(course['title'] == 'Portable starter check', 'Requested title was lost.')
        require(course['storageKey'] != other_course['storageKey'], 'Projects share player progress.')
        before = (project / 'course.json').read_bytes()
        refusal = subprocess.run([sys.executable, str(generator), str(project)], capture_output=True)
        require(refusal.returncode != 0, 'Generator overwrote an existing project.')
        require((project / 'course.json').read_bytes() == before, 'Refused generation changed the project.')
        if render:
            env = dict(os.environ)
            if not env.get('CANVAS_MODULE'):
                module = VIDEO / 'assets/starter/production-source/node_modules/@napi-rs/canvas'
                require(module.is_dir(), 'Install the starter canvas dependency or set CANVAS_MODULE.')
                env['CANVAS_MODULE'] = str(module)
            total_frames = 0
            for root in (project, designed):
                total_frames += render_and_audit(node, root, env)
            print(f'Render check passed: {total_frames} frames, no unresolved geometric findings, full silent-video decode.')
    print(f'Checks passed: {len(files)} skill files, {links} local links, syntax, generation, no-overwrite, isolated progress, beat coverage.')
    print('No speech requested. Listening, synchronized viewing, teaching quality, and current company facts were not evaluated.')


def render_and_audit(node, project, env):
    """Render silent previews and posters, audit every frame and decode every preview."""
    course = json.loads((project / 'course.json').read_text())
    production = project / 'production-source'
    run(node, production / 'render.cjs', 'all', '--silent-preview', env=env)
    run(node, production / 'render.cjs', 'posters', env=env)
    run(node, production / 'audit.cjs', env=env)
    report = json.loads((project / 'review/frame-audit.json').read_text())
    require(report['unresolvedPairs'] == 0, f'{project.name} has unresolved geometric findings.')
    expected_frames = sum(math.ceil(lesson['duration'] * course['fps']) for lesson in course['lessons'])
    require(report['totalFrames'] == expected_frames, 'Geometry did not cover every output frame.')
    for lesson in course['lessons']:
        video = project / 'review/silent' / (lesson['id'] + '.mp4')
        probe = run('ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', video,
                    capture_output=True, text=True)
        media = json.loads(probe.stdout)
        require(len(media['streams']) == 1, 'Silent preview contains extra streams.')
        stream = media['streams'][0]
        require(stream['codec_name'] == 'h264', 'Unexpected video codec.')
        require((stream['width'], stream['height']) == (course['width'], course['height']), 'Wrong video size.')
        numerator, denominator = map(float, stream['r_frame_rate'].split('/'))
        require(abs(numerator / denominator - course['fps']) < .001, 'Wrong frame rate.')
        require(abs(float(media['format']['duration']) - lesson['duration']) < 1 / course['fps'] + .1,
                'Unexpected preview duration.')
        decoded = run('ffmpeg', '-v', 'error', '-i', video, '-f', 'null', '-', capture_output=True)
        require(not decoded.stderr, 'Decoder reported an error.')
        require((project / 'player/posters' / (lesson['id'] + '.png')).is_file(), 'Missing poster.')
    return expected_frames


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render', action='store_true')
    arguments = parser.parse_args()
    check(arguments.render)
