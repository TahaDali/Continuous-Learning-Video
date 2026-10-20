"""Readable browser plans preserve canonical text and expose usable table semantics."""
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location('beat_sheet', ROOT / 'scripts/write_beat_sheet.py')
SHEET = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SHEET)


class PlanHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def handle_data(self, text):
        self.text.append(text)


class BeatSheetAccessibilityTests(unittest.TestCase):
    def test_browser_plan_preserves_text_escapes_markup_and_names_each_table(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'visual-beat-sheet').mkdir()
            data = json.loads((ROOT / 'assets/starter/visual-beat-sheet/beat-sheet.json').read_text())
            first_cue = data['lessons'][0]['beats'][0]['cues'][0]
            first_cue['text'] = 'Keep <script>literal</script> & all qualifications.'
            first_cue['elements'] = ['A < B', 'a vertical | bar']
            second = json.loads(json.dumps(data['lessons'][0]))
            second['id'] = 'quoted " lesson'
            data['lessons'].append(second)
            (root / 'visual-beat-sheet/beat-sheet.json').write_text(json.dumps(data))
            (root / 'course.json').write_text(json.dumps({'language': 'fr'}))
            markdown = SHEET.write_sheet(root)
            page = PlanHTML()
            page.feed((markdown.parent / 'beat-sheet.html').read_text())
            self.assertIn(first_cue['text'], markdown.read_text())
            self.assertIn('a vertical \\| bar', markdown.read_text())
            self.assertNotIn('script', [tag for tag, _ in page.elements])
            self.assertIn(('html', {'lang': 'fr'}), page.elements)
            text = ''.join(page.text)
            for lesson in data['lessons']:
                for beat in lesson['beats']:
                    for cue in beat['cues']:
                        self.assertIn(cue['text'], text)
                        self.assertIn(cue['behavior'], text)
                        for element in cue['elements']:
                            self.assertIn(element, text)
            groups = [attrs for _, attrs in page.elements if attrs.get('role') == 'group']
            tables = [attrs for tag, attrs in page.elements if tag == 'table']
            ids = [attrs['id'] for _, attrs in page.elements if 'id' in attrs]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertEqual(len(groups), len(data['lessons']))
            self.assertEqual(len(tables), len(groups))
            for group, table in zip(groups, tables):
                self.assertEqual(group['tabindex'], '0')
                self.assertIn(group['aria-labelledby'], ids)
                self.assertIn(group['aria-describedby'], ids)
                self.assertEqual(group['aria-labelledby'], table['aria-labelledby'])
            headers = [attrs for tag, attrs in page.elements if tag == 'th']
            self.assertEqual(len(headers), 9 * len(tables))
            self.assertTrue(all(attrs.get('scope') == 'col' for attrs in headers))


if __name__ == '__main__':
    unittest.main()
