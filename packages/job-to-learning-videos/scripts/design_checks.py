"""Check traceable editorial/design evidence; never infer teaching quality from metadata."""
import hashlib
import json
from pathlib import Path


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
    dependencies = read(root, 'course.json').get('renderSources', [])
    expected = {'production-source/world.cjs', 'production-source/motion.cjs', *dependencies}
    need(set(review.get('sourceHashes', {})) == expected, 'Prototype review needs the declared render source identity')
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
        files.append(relative)
    return files
