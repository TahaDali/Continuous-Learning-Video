"""Local setup and supplied-posting boundaries must fail honestly without service calls."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location('setup_workflow', ROOT / 'scripts/workflow.py')
WORKFLOW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WORKFLOW)


class SetupTests(unittest.TestCase):
    def test_missing_tools_are_reported_without_service_calls(self):
        with patch.object(WORKFLOW.shutil, 'which', return_value=None):
            report = WORKFLOW.preflight()
        self.assertFalse(report['readyForRendering'])
        self.assertFalse(report['canvas']['available'])
        self.assertFalse(any(report['tools'].values()))
        self.assertFalse(report['serviceRequestsMade'])

    def test_supplied_posting_without_url_needs_explicit_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / 'course'
            WORKFLOW.init(project)
            job = WORKFLOW.read(project / 'job.json')
            job.update(status='verified', employer='Fictional Learning Press', title='Fixture analyst',
                       retrievedAt='2026-10-20T12:00:00+00:00', requirements=[{'id':'r1','text':'Reconcile fictional records','kind':'responsibility'}])
            WORKFLOW.write(project / 'job.json', job)
            WORKFLOW.write(project / 'sources.json', {'sources':[{'id':'s1','title':'Supplied fictional text','url':None,'accessedAt':job['retrievedAt'],'publish':False}],
                                                     'claims':[{'id':'c1','text':'Fictional example','kind':'fiction','sourceIds':['s1']}]})
            with self.assertRaisesRegex(ValueError, 'supplied-text provenance'):
                WORKFLOW.evidence(project)
            job.update(sourceKind='supplied-text', sourceNote='User-provided fictional fixture; no live vacancy verified')
            WORKFLOW.write(project / 'job.json', job)
            self.assertIsNone(WORKFLOW.evidence(project)[0]['url'])
            WORKFLOW.record(project, 'research')
            self.assertEqual(WORKFLOW.state(project)[1]['research'], 'completed')

    def test_generator_rejects_nested_source_and_dangling_symlink(self):
        generator = ROOT / 'scripts/new_project.py'
        with tempfile.TemporaryDirectory() as temporary:
            outside = Path(temporary) / 'unexpected'
            link = Path(temporary) / 'link'
            link.symlink_to(outside)
            result = subprocess.run([sys.executable, str(generator), str(link)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('symlink project destination', result.stderr)
            self.assertFalse(outside.exists())
        nested = ROOT / 'must-not-create-a-fixture/child'
        result = subprocess.run([sys.executable, str(generator), str(nested)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('outside the installed skill source', result.stderr)
        self.assertFalse(nested.parent.exists())

    def test_project_preflight_does_not_reuse_author_dependency_implicitly(self):
        if not WORKFLOW.shutil.which('node'):
            self.skipTest('Node is required for the canvas boundary check')
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ):
            os.environ.pop('CANVAS_MODULE', None)
            project = Path(temporary) / 'course'
            WORKFLOW.init(project)
            report = WORKFLOW.preflight(project)
            self.assertFalse(report['canvas']['available'])
            self.assertFalse(report['readyForRendering'])
            self.assertFalse(report['serviceRequestsMade'])


if __name__ == '__main__':
    unittest.main()
