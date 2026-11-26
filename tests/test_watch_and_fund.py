import json
import tempfile
import unittest
from pathlib import Path
from eventcourt.store import connect, replay, run


class WatchAndFundTest(unittest.TestCase):
    def test_actual_incident_changes_both_decisions(self):
        p=Path(__file__).resolve().parents[1]/'fixtures/watch-and-fund.json'
        with tempfile.TemporaryDirectory() as folder:
            db_file=Path(folder)/'events.sqlite'
            db=connect(db_file)
            try:
                out=[run(db,e['command'],e['input']) for e in json.loads(p.read_text())]
                self.assertEqual(out[4]['decision'],'watch_no_open_case')
                self.assertEqual(out[6]['decision'],'purchase_denied')
                self.assertEqual(out[8],{'decision':'page','rule':'deploy-first'})
                self.assertEqual(out[9],{'decision':'purchase_recorded','remaining':4})
                self.assertEqual(out[10]['decision'],'purchase_denied')
            finally:
                db.close()
            self.assertTrue(replay(db_file)['verified'])
