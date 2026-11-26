import json
import tempfile
import unittest
from pathlib import Path
from eventcourt.store import connect, replay, run


class ChannelWorkTest(unittest.TestCase):
    def test_deliveries_control_packets_bulletin_and_work(self):
        fixture=Path(__file__).resolve().parents[1]/'fixtures/channel-work.json'
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'events.db'
            db=connect(path)
            try:
                out=[run(db,row['command'],row['input']) for row in json.loads(fixture.read_text())]
                self.assertEqual(out[9]['decision'],'packet_not_routable')
                self.assertEqual(out[13]['decision'],'bulletin_undelivered')
                self.assertEqual(out[15],{'decision':'bulletin_frozen','body':'open'})
                self.assertEqual(out[16]['decision'],'work_unattributed')
                self.assertEqual(out[17],{'decision':'work_tallied','units':0})
                self.assertEqual(out[19],{'decision':'work_tallied','units':4})
            finally:
                db.close()
            self.assertTrue(replay(path)['verified'])
