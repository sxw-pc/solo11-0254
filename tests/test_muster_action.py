import json
import tempfile
import unittest
from pathlib import Path
from eventcourt.store import connect, replay, run


class MusterActionTest(unittest.TestCase):
    def test_ack_assignment_and_action(self):
        p=Path(__file__).resolve().parents[1]/'fixtures/muster-action.json'
        with tempfile.TemporaryDirectory() as folder:
            db_file=Path(folder)/'events.sqlite'
            db=connect(db_file)
            try:
                out=[run(db,row['command'],row['input']) for row in json.loads(p.read_text())]
                self.assertEqual(out[11]['decision'],'assign_denied')
                self.assertEqual(out[13]['decision'],'action_unassigned')
                self.assertEqual(out[14],{'decision':'assigned','remaining':2})
                self.assertEqual(out[15]['decision'],'action_recorded')
                self.assertEqual(out[16]['decision'],'assign_denied')
            finally:
                db.close()
            self.assertTrue(replay(db_file)['verified'])
