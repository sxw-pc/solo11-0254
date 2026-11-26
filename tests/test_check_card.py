import json
from pathlib import Path
import tempfile
import unittest

from eventcourt.store import connect, replay, run


class CheckCardTest(unittest.TestCase):
    def test_a_real_extra_cut_removes_a_tabling_anchor(self):
        path = Path(__file__).resolve().parents[1] / 'fixtures/check-card.json'
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory)/'state.sqlite'
            db = connect(db_path)
            try:
                receipts = [run(db, step['command'], step['input']) for step in json.loads(path.read_text())]
                self.assertEqual(receipts[4]['decision'], 'card_wont_fit')
                self.assertEqual(receipts[6], {'decision':'card_fitted','holes':[3,4]})
                self.assertEqual(receipts[7]['decision'], 'punch_anchor_broken')
                self.assertEqual(receipts[8]['decision'], 'card_wont_fit')
                self.assertEqual(receipts[11], {'decision':'card_fitted','holes':[3]})
                self.assertEqual(receipts[13], {'decision':'card_fitted','holes':[3,6]})
            finally:
                db.close()
            self.assertTrue(replay(db_path)['verified'])
