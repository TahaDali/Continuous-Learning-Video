"""Release boundaries: explicit payloads, no recursion, no outside files or overwrites."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import build_skill


class SkillPackagingTests(unittest.TestCase):
    def fixture(self, root):
        root.mkdir()
        names = ['SKILL.md', 'LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md', 'VERSION', 'skill-files.json']
        for name in names[:-1]:
            (root / name).write_text('1.0.0\n' if name == 'VERSION' else 'Synthetic release fixture\n')
        (root / 'skill-files.json').write_text(json.dumps({'files': names}))
        return root

    def test_source_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = self.fixture(base / 'source')
            private = base / 'private-fixture.txt'
            private.write_text('Harmless outside fixture; never follow it.')
            (root / 'SKILL.md').unlink()
            (root / 'SKILL.md').symlink_to(private)
            with patch.object(build_skill, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'must not contain symlinks'):
                    build_skill.build(base / 'assembled')
            self.assertFalse((base / 'assembled').exists())

    def test_dangling_output_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output, target = root / 'output', root / 'unexpected-destination'
            output.symlink_to(target)
            with self.assertRaisesRegex(ValueError, 'symlink destination'):
                build_skill.build(output)
            self.assertFalse(target.exists())

    def test_nested_output_fails_before_creating_staging_or_parents(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = self.fixture(Path(temporary) / 'source')
            before = sorted(str(p.relative_to(source)) for p in source.rglob('*'))
            with patch.object(build_skill, 'ROOT', source):
                with self.assertRaisesRegex(ValueError, 'outside the source tree'):
                    build_skill.build(source / 'nested/more/assembled')
            self.assertEqual(before, sorted(str(p.relative_to(source)) for p in source.rglob('*')))

    def test_unlisted_ignored_credentials_and_private_notes_never_enter_bundle(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = self.fixture(base / 'source')
            for name in ('fixture.key', 'fixture.pem', '.env', 'private-note.txt'):
                (source / name).write_text('HARMLESS_AUDIT_FIXTURE_NOT_A_SECRET')
            with patch.object(build_skill, 'ROOT', source):
                built = build_skill.build(base / 'assembled')
            self.assertEqual({p.name for p in built.iterdir()}, set(json.loads((source / 'skill-files.json').read_text())['files']))

    def test_credential_path_cannot_be_added_to_payload_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = self.fixture(base / 'source')
            (source / 'fixture.key').write_text('HARMLESS_NOT_A_SECRET')
            manifest = json.loads((source / 'skill-files.json').read_text())
            manifest['files'].append('fixture.key')
            (source / 'skill-files.json').write_text(json.dumps(manifest))
            with patch.object(build_skill, 'ROOT', source):
                with self.assertRaisesRegex(ValueError, 'Unsafe release manifest path'):
                    build_skill.build(base / 'assembled')
            self.assertFalse((base / 'assembled').exists())

    def test_archive_rejects_contamination_and_nested_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            built = build_skill.build(base / 'assembled')
            with self.assertRaisesRegex(ValueError, 'outside the source tree'):
                build_skill.archive(built, built / 'nested/archive.zip')
            (built / 'private-note.txt').write_text('Harmless unlisted fixture')
            with self.assertRaisesRegex(ValueError, 'Unlisted release file'):
                build_skill.archive(built, base / 'archive.zip')
            self.assertFalse((base / 'archive.zip').exists())

    def test_symlink_ancestor_in_payload_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = self.fixture(base / 'source')
            outside = base / 'outside'
            outside.mkdir()
            (outside / 'fixture.txt').write_text('Harmless fixture')
            (source / 'references').symlink_to(outside, target_is_directory=True)
            manifest = json.loads((source / 'skill-files.json').read_text())
            manifest['files'].append('references/fixture.txt')
            (source / 'skill-files.json').write_text(json.dumps(manifest))
            with patch.object(build_skill, 'ROOT', source):
                with self.assertRaisesRegex(ValueError, 'must not contain symlinks'):
                    build_skill.build(base / 'assembled')

    def test_archive_is_reproducible_and_verifiable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = build_skill.build(root / 'assembled')
            first = build_skill.archive(skill, root / 'one.zip')
            second = build_skill.archive(skill, root / 'two.zip')
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as bundle:
                manifest = json.loads(bundle.read(build_skill.NAME + '/release-manifest.json'))
                for required in ('LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md', 'LICENSES/Legacy-MIT.txt'):
                    self.assertIn(required, manifest['files'])
                for name, expected in manifest['files'].items():
                    self.assertEqual(hashlib.sha256(bundle.read(build_skill.NAME + '/' + name)).hexdigest(), expected)
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                build_skill.archive(skill, first)


if __name__ == '__main__':
    unittest.main()
