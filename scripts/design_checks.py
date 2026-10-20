"""Check traceable editorial/design evidence; never infer teaching quality from metadata."""
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

# Shared system modules own their palettes and faces; authored modules use their tokens and roles.
SYSTEM_MODULES = {'production-source/design.cjs', 'production-source/templates.cjs', 'production-source/motion.cjs',
                  'production-source/illustrations.cjs', 'production-source/finite-canvas.cjs',
                  'production-source/render-sources.cjs'}
HEX_COLOUR = re.compile(r'''['"`]#[0-9a-fA-F]{3,8}['"`]''')
FONT_CHOICE = re.compile(r'''\.font\s*=|registerFromPath|font-family|\d+px\s+['"]?[A-Za-z]''')


def need(value, message):
    if not value:
        raise ValueError(message)


def read(root, name):
    path = root / name
    need(path.is_file() and not path.is_symlink(), f'Missing design evidence: {name}')
    return json.loads(path.read_text())


def named(items, label):
    need(isinstance(items, list) and items, f'Missing {label}')
    result = {}
    for item in items:
        identifier = item.get('id')
        need(isinstance(identifier, str) and identifier.strip() and identifier not in result, f'Invalid {label} identity')
        result[identifier] = item
    return result


def prose(value, label):
    need(isinstance(value, str) and value.strip(), f'Missing {label}')


def video_prototype(path):
    """Check local media structure; never infer visual review or full decodability."""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-protocol_whitelist', 'file,pipe',
            '-show_streams', '-show_format', '-of', 'json', str(path),
        ], capture_output=True, text=True, timeout=15)
    except FileNotFoundError as error:
        raise ValueError('ffprobe is required to check prototype video streams') from error
    except subprocess.TimeoutExpired as error:
        raise ValueError('Prototype video probe timed out') from error
    need(result.returncode == 0, 'Prototype must contain a positive-duration video stream')
    try:
        data = json.loads(result.stdout)
    except (ValueError, TypeError) as error:
        raise ValueError('Invalid prototype video probe result') from error
    for stream in data.get('streams', []):
        if stream.get('codec_type') != 'video' or stream.get('disposition', {}).get('attached_pic'):
            continue
        try:
            # Some containers expose duration only at the format level.
            duration = stream.get('duration')
            if duration in (None, 'N/A'):
                duration = data.get('format', {}).get('duration')
            duration = float(duration)
            width, height = int(stream.get('width', 0)), int(stream.get('height', 0))
        except (TypeError, ValueError, OverflowError):
            continue
        if math.isfinite(duration) and duration > 0 and width > 0 and height > 0:
            return
    raise ValueError('Prototype must contain a positive-duration video stream')


def script(root, lessons):
    plan = read(root, 'narrative-map.json')
    parts = named(plan.get('parts'), 'narrative parts')
    chapters = named(plan.get('chapters'), 'manuscript chapters')
    manuscript = (root / 'manuscript.md').read_text()
    taught = set()
    for part in parts.values():
        prose(part.get('title'), 'part title')
        prose(part.get('question'), 'part learning question')
    for chapter in chapters.values():
        need(chapter.get('partId') in parts, 'Unknown chapter part')
        heading = chapter.get('heading')
        prose(heading, 'manuscript heading')
        need(manuscript.splitlines().count(heading) == 1, f'Manuscript heading is missing or ambiguous: {heading}')
        assigned = chapter.get('lessonIds')
        need(isinstance(assigned, list) and assigned and set(assigned) <= lessons, 'Unknown adapted lesson')
        taught.update(assigned)
        need(chapter.get('retainedDecisions'), 'Chapter needs retained decisions')
        for decision in chapter['retainedDecisions']:
            prose(decision, 'retained decision')
        prose(chapter.get('adaptation'), 'adaptation account')
    need(taught == lessons, 'Narrative map leaves lessons unassigned')
    review = read(root, 'review/editorial.json')
    need(review.get('status') == 'completed', 'Editorial review must be resolved before production')
    prose(review.get('reviewer'), 'editorial reviewer')
    reviewed = set()
    for finding in review.get('findings', []):
        cid = finding.get('chapterId')
        need(cid in chapters and finding.get('partId') == chapters[cid]['partId'], 'Editorial evidence points to another chapter or part')
        prose(finding.get('observation'), 'editorial observation')
        reviewed.add(finding['partId'])
    need(reviewed == parts.keys(), 'Editorial review does not examine every planned part')
    return ['narrative-map.json', 'review/editorial.json']


def render_sources(root):
    helper = Path(__file__).resolve().parent.parent / 'assets/starter/production-source/render-sources.cjs'
    result = subprocess.run(['node', str(helper), str(root)], capture_output=True, text=True)
    need(result.returncode == 0, 'Render dependency discovery failed: ' + result.stderr.strip())
    return set(json.loads(result.stdout))


def design_token_findings(root, sources=None):
    """List authored lines that bypass design.cjs tokens or type roles.

    Applies only when the render sources include design.cjs; worlds built directly on
    motion.cjs keep their own palette. This is a guardrail for literal hex colours and font
    choices, not a style analyser: computed colours and rgba() shadows are not inspected.
    """
    sources = render_sources(root) if sources is None else sources
    if 'production-source/design.cjs' not in sources:
        return []
    findings = []
    for name in sorted(sources):
        if name in SYSTEM_MODULES or not name.endswith(('.cjs', '.js')):
            continue
        for number, line in enumerate((root / name).read_text().splitlines(), 1):
            if not line.lstrip().startswith('//') and (HEX_COLOUR.search(line) or FONT_CHOICE.search(line)):
                findings.append(f'{name}:{number}')
    return findings


def visuals(root, lessons):
    design = read(root, 'visual-design.json')
    mechanisms = named(design.get('mechanisms'), 'visual mechanisms')
    taught = set()
    for mechanism in mechanisms.values():
        prose(mechanism.get('question'), 'silent mechanism question')
        ids = mechanism.get('lessonIds')
        need(isinstance(ids, list) and ids and set(ids) <= lessons, 'Mechanism references an unknown lesson')
        taught.update(ids)
        states = named(mechanism.get('states'), 'mechanism states')
        for state in states.values():
            prose(state.get('meaning'), 'state meaning')
        need(mechanism.get('transitions'), 'Mechanism needs visible transitions')
        for transition in mechanism['transitions']:
            need(transition.get('from') in states and transition.get('to') in states, 'Transition references an unknown state')
            for key in ('trigger', 'change', 'invariant'):
                prose(transition.get(key), f'transition {key}')
    need(taught == lessons, 'Visual design leaves lessons unassigned')
    review = read(root, 'review/prototypes.json')
    need(review.get('status') == 'completed', 'Prototype findings must be resolved before production')
    prose(review.get('reviewer'), 'prototype reviewer')
    world = root / 'production-source/world.cjs'
    need(review.get('worldSha256') == hashlib.sha256(world.read_bytes()).hexdigest(), 'Prototype review is stale after a world change')
    expected = render_sources(root)
    need(set(review.get('sourceHashes', {})) == expected, 'Prototype review needs the complete discovered render source identity')
    findings = design_token_findings(root, expected)
    need(not findings, 'Design-system world hard-codes colour or type; use T tokens (extendTheme for subject colours) '
         'and TYPE roles: ' + ', '.join(findings[:8]))
    for name, value in review['sourceHashes'].items():
        source = root / name
        need(root.resolve() in source.resolve().parents and source.is_file() and not source.is_symlink(), 'Invalid render dependency')
        need(hashlib.sha256(source.read_bytes()).hexdigest() == value, 'Prototype review is stale after a render dependency change')
    files = ['visual-design.json', 'review/prototypes.json']
    need(review.get('clips'), 'No inspected prototype clips')
    for clip in review['clips']:
        need(clip.get('mechanismId') in mechanisms, 'Prototype references an unknown mechanism')
        relative = clip.get('path', '')
        path = root / relative
        need(relative and not Path(relative).is_absolute() and root.resolve() in path.resolve().parents
             and path.is_file() and not path.is_symlink(), 'Prototype must be a regular project file')
        prose(clip.get('observation'), 'prototype observation')
        video_prototype(path)
        files.append(relative)
    return files
