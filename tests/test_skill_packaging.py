"""A release bundle must not follow outside files or replace a user's files."""
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
    def test_source_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / 'packages/job-to-learning-videos'
            package.mkdir(parents=True)
            private = root / 'private-fixture.txt'
            private.write_text('Never copy this outside the source tree.')
            (package / 'linked.txt').symlink_to(private)
            with patch.object(build_skill, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'must not contain symlinks'):
                    build_skill.build(root / 'assembled')
            self.assertFalse((root / 'assembled').exists())

    def test_dangling_output_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'output'
            target = root / 'unexpected-destination'
            output.symlink_to(target)
            with self.assertRaisesRegex(ValueError, 'symlink destination'):
                build_skill.build(output)
            self.assertFalse(target.exists())

    def test_archive_is_reproducible_and_verifiable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = build_skill.build(root / 'assembled')
            first = build_skill.archive(skill, root / 'one.zip')
            second = build_skill.archive(skill, root / 'two.zip')
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as bundle:
                manifest = json.loads(bundle.read(build_skill.NAME + '/release-manifest.json'))
                self.assertIn('LICENSE', manifest['files'])
                self.assertIn('THIRD_PARTY_NOTICES.md', manifest['files'])
                for name, expected in manifest['files'].items():
                    self.assertEqual(hashlib.sha256(bundle.read(build_skill.NAME + '/' + name)).hexdigest(), expected)
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                build_skill.archive(skill, first)


if __name__ == '__main__':
    unittest.main()
