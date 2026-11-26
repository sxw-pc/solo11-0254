import json
from pathlib import Path
import tempfile
import unittest

from eventcourt.store import connect, replay, run


class DyeGaugeTest(unittest.TestCase):
    def test_live_pour_changes_real_gauge_result(self):
        fixture = Path(__file__).resolve().parents[1] / 'fixtures/dye-gauge.json'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.sqlite'
            database = connect(path)
            try:
                results = [run(database, event['command'], event['input']) for event in json.loads(fixture.read_text())]
                self.assertEqual(results[6]['decision'], 'gauge_empty')
                self.assertEqual(results[8], {'decision': 'gauge_hold', 'volume': 4, 'dark': 4})
                self.assertEqual(results[10], {'decision': 'gauge_pass', 'volume': 8, 'dark': 4})
                self.assertEqual(results[11], {'decision': 'pour_denied'})
            finally:
                database.close()
            self.assertTrue(replay(path)['verified'])
