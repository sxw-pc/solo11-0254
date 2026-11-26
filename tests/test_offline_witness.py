import json
import tempfile
import unittest
from pathlib import Path
from eventcourt.store import connect,replay,run


class OfflineWitnessTest(unittest.TestCase):
    def test_ack_enables_field_mode_and_evidence(self):
        fixture=Path(__file__).resolve().parents[1]/'fixtures/offline-witness.json'
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'state.sqlite'
            db=connect(path)
            try:
                out=[run(db,e['command'],e['input']) for e in json.loads(fixture.read_text())]
                self.assertEqual(out[11]['decision'],'switch_denied')
                self.assertEqual(out[13]['decision'],'witness_denied')
                self.assertEqual(out[14]['decision'],'endpoint_switched')
                self.assertEqual(out[15]['decision'],'witness_recorded')
            finally:
                db.close()
            self.assertTrue(replay(path)['verified'])
