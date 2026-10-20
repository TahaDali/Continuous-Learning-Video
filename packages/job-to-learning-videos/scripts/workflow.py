#!/usr/bin/env python3
"""Maintain a job-course project and export checked player files. No research, speech or hosting requests."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import importlib.metadata
import inspect
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

SKILL = Path(__file__).resolve().parent.parent
STAGES = ('research', 'curriculum', 'script', 'visuals', 'narration', 'media', 'review', 'package', 'delivery')
TIMING = {'start', 'end', 'duration', 'speechStart', 'speechEnd', 'wordTimings', 'timingMethod', 'narrationVoice'}
STATUSES = {'completed', 'partial', 'pending', 'unavailable', 'failed'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as temporary:
        temporary.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        name = temporary.name
    Path(name).replace(path)


def url(value):
    parts = urlsplit(value)
    require(parts.scheme in {'http', 'https'} and parts.hostname and not parts.username and not parts.password,
            'Expected an HTTP/S URL without embedded credentials')
    return value


def dated(value):
    require(isinstance(value, str), 'Missing dated source provenance')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, 'Dates need an explicit timezone')


def index(items, name):
    require(isinstance(items, list), f'{name} must be an array')
    result = {}
    for item in items:
        identifier = item.get('id')
        require(isinstance(identifier, str) and identifier.strip() and identifier not in result,
                f'Missing or duplicate {name} ID')
        result[identifier] = item
    return result


def text(value, message):
    require(isinstance(value, str) and value.strip(), message)


def evidence(root):
    job, material = read(root / 'job.json'), read(root / 'sources.json')
    url(job['url'])
    require(job['status'] == 'verified', 'Retrieve the actual posting or obtain supplied posting text first')
    dated(job['retrievedAt'])
    for key in ('employer', 'title'):
        text(job.get(key), f'Missing job {key}')
    requirements = index(job['requirements'], 'requirement')
    require(requirements, 'No posting responsibilities or requirements')
    for item in requirements.values():
        text(item.get('text'), 'Empty posting requirement')
        require(item.get('kind') in {'responsibility', 'required', 'preferred'}, 'Unknown requirement kind')
    sources, claims = index(material['sources'], 'source'), index(material['claims'], 'claim')
    require(sources and claims, 'Research needs sources and claims')
    for source in sources.values():
        text(source.get('title'), 'Empty source title')
        dated(source.get('accessedAt'))
        require(type(source.get('publish')) is bool, 'Source publish flag must be explicit')
        if source.get('url') is not None:
            url(source['url'])
    for claim in claims.values():
        text(claim.get('text'), 'Empty claim')
        require(claim.get('kind') in {'fact', 'interpretation', 'fiction', 'unknown'}, 'Unknown evidence kind')
        require(isinstance(claim.get('sourceIds'), list) and set(claim['sourceIds']) <= sources.keys(), 'Unknown claim source')
        require(claim['kind'] != 'fact' or claim['sourceIds'], 'A factual claim needs evidence')
    return job, requirements, sources, claims


def curriculum(root):
    job, requirements, sources, claims = evidence(root)
    plan = read(root / 'curriculum.json')
    objectives, lessons = index(plan['objectives'], 'objective'), index(plan['lessons'], 'lesson')
    require(objectives and lessons, 'No curriculum objectives or lessons')
    taught, covered = set(), set()
    for objective in objectives.values():
        text(objective.get('text'), 'Empty objective')
        require(isinstance(objective.get('requirementIds'), list)
                and set(objective['requirementIds']) <= requirements.keys(), 'Unknown objective requirement')
        covered.update(objective['requirementIds'])
    for lesson in lessons.values():
        text(lesson.get('title'), 'Empty lesson title')
        require(lesson.get('objectiveIds') and set(lesson['objectiveIds']) <= objectives.keys(), 'Unknown lesson objective')
        require(lesson.get('claimIds') and set(lesson['claimIds']) <= claims.keys(), 'Unknown or missing lesson evidence')
        taught.update(lesson['objectiveIds'])
    for exclusion in plan.get('exclusions', []):
        require(exclusion.get('requirementId') in requirements, 'Unknown excluded requirement')
        text(exclusion.get('reason'), 'Exclusion needs a reason')
        covered.add(exclusion['requirementId'])
    require(covered == requirements.keys(), 'Posting requirements are missing from the curriculum')
    require(taught == objectives.keys(), 'Some objectives have no lesson')
    return job, sources, claims, plan


def validator(root, media=False):
    spec = importlib.util.spec_from_file_location('job_course_validator', SKILL / 'scripts/validate_project.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate(root, media=media)


def strip_timing(value):
    if isinstance(value, dict):
        return {k: strip_timing(v) for k, v in value.items() if k not in TIMING}
    if isinstance(value, list):
        return [strip_timing(v) for v in value]
    return value


def digest(path, stage=None):
    if stage == 'visuals' and path.name == 'beat-sheet.md':
        # This companion is derived from canonical JSON, including measured timing.
        return digest(path.with_name('beat-sheet.json'), stage)
    if stage in {'script', 'visuals'} and path.name in {'course.json', 'beat-sheet.json'}:
        payload = json.dumps(strip_timing(read(path)), sort_keys=True, ensure_ascii=False).encode()
    else:
        payload = path.read_bytes()
    return hashlib.sha256(payload).hexdigest()


def state(root):
    data = read(root / 'project.json')
    result, upstream = {}, False
    for stage in STAGES:
        checkpoint = data['stages'].get(stage)
        stale = bool(checkpoint) and any(not (root / p).is_file() or digest(root / p, stage) != value
                                         for p, value in checkpoint['fingerprints'].items())
        result[stage] = 'stale' if checkpoint and (stale or upstream) else 'completed' if checkpoint else 'pending'
        upstream |= result[stage] != 'completed'
    return data, result


def ready_before(root, stage):
    data, statuses = state(root)
    required = STAGES[:STAGES.index(stage)]
    require(all(statuses[s] == 'completed' for s in required),
            'Complete or refresh upstream stages: ' + ', '.join(s for s in required if statuses[s] != 'completed'))
    return data


def inside(root, relative):
    path = root / relative
    require(not path.is_symlink() and root.resolve() in path.resolve().parents, 'Evidence must be a regular project file')
    require(path.is_file(), f'Missing artifact: {relative}')
    return path


def record(root, stage):
    data = ready_before(root, stage)
    fixed = {
        'research': ['job.json', 'sources.json'], 'curriculum': ['curriculum.json'],
        'script': ['manuscript.md', 'course.json'],
        'visuals': ['visual-beat-sheet/beat-sheet.json', 'visual-beat-sheet/beat-sheet.md', 'production-source/world.cjs'],
        'narration': ['course.json', 'player/course-data.js', 'settings.json'],
        'media': ['review/frame-audit.json', 'review/validation.json'],
        'review': ['review/acceptance.json'], 'package': ['export-manifest.json'], 'delivery': ['delivery.json']
    }
    artifacts = fixed[stage].copy()
    if stage == 'research':
        evidence(root)
    if stage in {'curriculum', 'script', 'visuals', 'narration', 'media'}:
        _, _, _, plan = curriculum(root)
    if stage in {'script', 'visuals', 'narration', 'media'}:
        course = read(root / 'course.json')
        require([l['id'] for l in course['lessons']] == [l['id'] for l in plan['lessons']], 'Runtime lessons differ from curriculum')
    if stage == 'visuals':
        validator(root)
        refresh_sheet(root)
    if stage == 'narration':
        refresh_sheet(root)
        for lesson in course['lessons']:
            require(all(beat.get('wordTimings') for beat in lesson['scenes']), 'Narration needs measured words')
            artifacts += [f"audio/{lesson['id']}.wav", f"player/captions/{lesson['id']}.srt", f"player/captions/{lesson['id']}.vtt"]
    if stage == 'media':
        validator(root, media=True)
        audit = read(root / 'review/frame-audit.json')
        require(audit['unresolvedPairs'] == 0, 'Unresolved frame audit findings')
        expected_sources = {'course.json', 'production-source/world.cjs', 'production-source/motion.cjs', 'production-source/intentional-overlaps.json'}
        require(set(audit['sourceHashes']) == expected_sources, 'Incomplete frame audit source identity')
        require(audit['totalFrames'] == sum(math.ceil(l['duration'] * course['fps']) for l in course['lessons']), 'Frame audit coverage is incomplete')
        for name, value in audit['sourceHashes'].items():
            require(digest(inside(root, name)) == value, 'Frame audit is stale')
        artifacts += ['production-source/world.cjs', 'production-source/motion.cjs', 'production-source/render.cjs',
                      'production-source/audit.cjs', 'production-source/intentional-overlaps.json']
        for lesson in course['lessons']:
            artifacts += [f"player/videos/{lesson['id']}.mp4", f"player/posters/{lesson['id']}.png"]
    if stage == 'review':
        acceptance(root)
    if stage == 'delivery':
        delivery, package = read(root / 'delivery.json'), read(root / 'export-manifest.json')
        require(delivery.get('status') == 'deployed', 'No confirmed deployment')
        url(delivery['url'])
        for key in ('provider', 'version', 'audience'):
            text(delivery.get(key), f'Missing deployment {key}')
        require(delivery.get('packageSha256') == package['packageSha256'], 'Deployment refers to another export')
        exported = Path(package['output'])
        actual = {str(p.relative_to(exported)): digest(p) for p in sorted(exported.rglob('*')) if p.is_file()}
        require(actual == package['files'], 'Export changed after packaging')
    for name in artifacts:
        inside(root, name)
    for later in STAGES[STAGES.index(stage) + 1:]:
        data['stages'].pop(later, None)
    data['stages'][stage] = {'recordedAt': now(), 'fingerprints': {name: digest(root / name, stage) for name in artifacts}}
    write(root / 'project.json', data)
    return state(root)[1]


def refresh_sheet(root):
    spec = importlib.util.spec_from_file_location('readable_beat_sheet', SKILL / 'scripts/write_beat_sheet.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.write_sheet(root)


def acceptance(root):
    report = read(root / 'review/acceptance.json')
    for field in ('content', 'listening', 'synchronizedViewing', 'silentInspection'):
        item = report.get(field, {})
        require(item.get('status') in STATUSES, f'Missing review status: {field}')
        text(item.get('coverage'), f'Missing review coverage: {field}')
        require(item['status'] != 'failed', f'Failed review: {field}')
        if field in {'listening', 'synchronizedViewing'} and item['status'] == 'completed':
            text(item.get('reviewer'), f'Completed {field} needs a reviewer')
    return report


def export(root, output):
    root, output = root.resolve(), output.resolve()
    ready_before(root, 'package')
    require(not output.exists(), 'Refusing to overwrite an existing export')
    require(output != root and root not in output.parents and output not in root.parents, 'Export must be separate from the working project')
    job, sources, claims, plan = curriculum(root)
    validator(root, media=True)
    report = acceptance(root)
    runtime = read(root / 'course.json')
    course = {k: runtime[k] for k in ('title', 'storageKey', 'language', 'width', 'height', 'fps')}
    lesson_keys = {'id', 'title', 'goal', 'coverage', 'duration', 'part', 'question', 'options', 'answer', 'explanation'}
    course['lessons'] = []
    for lesson in runtime['lessons']:
        public_lesson = {k: value for k, value in lesson.items() if k in lesson_keys}
        public_lesson['scenes'] = [{k: beat[k] for k in ('id', 'headline', 'narration', 'start', 'end')} for beat in lesson['scenes']]
        course['lessons'].append(public_lesson)
    public_sources = [dict(id=s['id'], title=s['title'], url=s['url'], accessedAt=s['accessedAt'])
                      for s in sources.values() if s['publish'] and s.get('url')]
    course['sources'] = public_sources
    course['job'] = {key: job[key] for key in ('employer', 'title', 'url')}
    course['job']['researchedAt'] = job['retrievedAt']
    course['objectives'] = [o['text'] for o in plan['objectives']]
    course['review'] = {key: {'status': value['status'], 'coverage': value['coverage']}
                        for key, value in report.items() if key in {'content', 'listening', 'synchronizedViewing', 'silentInspection'}}
    course['reviewVersion'] = any(value['status'] != 'completed' for value in course['review'].values())
    public_ids = {s['id'] for s in public_sources}
    for lesson, planned in zip(course['lessons'], plan['lessons'], strict=True):
        lesson['sourceIds'] = sorted({sid for cid in planned['claimIds'] for sid in claims[cid]['sourceIds']} & public_ids)
        lesson['evidenceKinds'] = sorted({claims[cid]['kind'] for cid in planned['claimIds']})
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='course-export-', dir=output.parent) as temporary:
        stage = Path(temporary) / 'player'
        stage.mkdir()
        for name in ('index.html', 'style.css', 'player.js'):
            shutil.copy2(inside(root, 'player/' + name), stage / name)
        write_js = 'window.COURSE = ' + json.dumps(course, ensure_ascii=False) + ';\n'
        (stage / 'course-data.js').write_text(write_js)
        for lesson in course['lessons']:
            for folder, suffix in [('videos', '.mp4'), ('captions', '.srt'), ('captions', '.vtt'), ('posters', '.png')]:
                relative = f"{folder}/{lesson['id']}{suffix}"
                (stage / folder).mkdir(exist_ok=True)
                shutil.copy2(inside(root, 'player/' + relative), stage / relative)
        fingerprints = {str(p.relative_to(stage)): digest(p) for p in sorted(stage.rglob('*')) if p.is_file()}
        package_sha = hashlib.sha256(json.dumps(fingerprints, sort_keys=True).encode()).hexdigest()
        stage.rename(output)
    manifest = {'createdAt': now(), 'output': str(output), 'packageSha256': package_sha,
                'files': fingerprints, 'reviewVersion': course['reviewVersion']}
    write(root / 'export-manifest.json', manifest)
    record(root, 'package')
    return manifest


def init(root, job_url):
    url(job_url)
    require(not root.exists(), 'Refusing to overwrite an existing project')
    subprocess.run([sys.executable, str(SKILL / 'scripts/new_project.py'), str(root), '--title', 'Job learning course'], check=True, capture_output=True)
    data = read(root / 'course.json')
    data['lessons'] = []
    write(root / 'course.json', data)
    (root / 'player/course-data.js').write_text('window.COURSE = ' + json.dumps(data) + ';\n')
    write(root / 'visual-beat-sheet/beat-sheet.json', {'lessons': []})
    write(root / 'project.json', {'schemaVersion': 1, 'jobUrl': job_url, 'createdAt': now(), 'stages': {}})
    write(root / 'job.json', {'url': job_url, 'status': 'unretrieved', 'retrievedAt': None,
                            'employer': None, 'title': None, 'requirements': []})
    write(root / 'sources.json', {'sources': [], 'claims': []})
    write(root / 'curriculum.json', {'objectives': [], 'lessons': [], 'exclusions': []})
    write(root / 'settings.json', {'language': 'en', 'audience': 'beginner',
                                  'narration': {'provider': None, 'voice': None},
                                  'hosting': {'provider': None, 'audience': 'private'}})
    return root


def preflight():
    tools = {name: shutil.which(name) is not None for name in ('node', 'ffmpeg', 'ffprobe')}
    try:
        speech = importlib.metadata.version('edge-tts')
        import edge_tts
        compatible = 'boundary' in inspect.signature(edge_tts.Communicate).parameters
    except importlib.metadata.PackageNotFoundError:
        speech = None
        compatible = False
    return {'tools': tools, 'python': sys.version.split()[0], 'edgeTtsVersion': speech,
            'edgeTtsWordBoundaryInterface': compatible,
            'canvas': 'Check @napi-rs/canvas in the project or set CANVAS_MODULE.',
            'remoteCapabilities': 'Discover research and hosting tools in the current session.',
            'serviceRequestsMade': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('preflight')
    create = commands.add_parser('init')
    create.add_argument('project', type=Path)
    create.add_argument('--job-url', required=True)
    for name in ('status', 'record', 'export'):
        command = commands.add_parser(name)
        command.add_argument('project', type=Path)
        if name == 'record':
            command.add_argument('stage', choices=STAGES)
        elif name == 'export':
            command.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'preflight':
            result = preflight()
        else:
            root = args.project.expanduser().resolve()
            if args.command == 'init':
                result = {'project': str(init(root, args.job_url))}
            elif args.command == 'status':
                result = state(root)[1]
            elif args.command == 'record':
                require(args.stage != 'package', 'Use export to record the package stage')
                result = record(root, args.stage)
            else:
                result = export(root, args.output.expanduser().resolve())
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Workflow failed: {error}\n')


if __name__ == '__main__':
    main()
