import json
import tempfile
import unittest
from pathlib import Path
from eventcourt.store import connect, replay, run


class RemedyReopenTest(unittest.TestCase):
    def test_attributed_checks_control_traffic_reopening(self):
        fixture = Path(__file__).resolve().parents[1] / 'fixtures/remedy-reopen.json'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'state.sqlite'
            db = connect(path)
            try:
                result = [run(db,event['command'],event['input'])
                          for event in json.loads(fixture.read_text(encoding='utf8'))]
                self.assertEqual([v['decision'] for v in result[11:]], [
                    'impact_cell_recorded','impact_cell_recorded','remedy_check_unattributed',
                    'remedy_check_recorded','impact_still_open','remedy_check_recorded',
                    'remedy_cleared','reopen_issued','remedy_cleared','remedy_check_recorded','reopen_held'])
                self.assertEqual(result[15]['covered'], 2)
                self.assertEqual(result[-1]['check'], 'relapse-s')
            finally:
                db.close()
            self.assertTrue(replay(path)['verified'])
