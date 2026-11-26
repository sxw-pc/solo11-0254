import json
from pathlib import Path
import tempfile
import unittest

from eventcourt.store import connect, replay, run


class PanelTest(unittest.TestCase):
    def test_read_depends_on_committed_light_sequence(self):
        fixture = Path(__file__).resolve().parents[1] / 'fixtures/panel-read.json'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.sqlite'
            database = connect(path)
            try:
                results = [run(database, event['command'], event['input']) for event in json.loads(fixture.read_text())]
                self.assertEqual(results[-3], {'decision': 'panel_read_missing'})
                self.assertEqual(results[-2], {'decision': 'panel_emitted', 'frames': '101'})
                self.assertEqual(results[-1], {'decision': 'panel_read', 'label': 'inspect'})
            finally:
                database.close()
            self.assertTrue(replay(path)['verified'])
