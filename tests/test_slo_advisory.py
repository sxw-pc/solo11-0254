import json
import tempfile
import unittest
from pathlib import Path
from eventcourt.store import connect,replay,run


class SloAdvisoryTest(unittest.TestCase):
    def test_real_close_changes_advice(self):
        fixture=Path(__file__).resolve().parents[1]/'fixtures/slo-advisory.json'
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'state.sqlite'
            db=connect(path)
            try:
                out=[run(db,e['command'],e['input']) for e in json.loads(fixture.read_text())]
                self.assertEqual(out[3]['decision'],'advisory_denied')
                self.assertEqual(out[5],{'decision':'slo_closed','burn':6})
                self.assertEqual(out[6]['decision'],'defer_changes')
            finally:
                db.close()
            self.assertTrue(replay(path)['verified'])
