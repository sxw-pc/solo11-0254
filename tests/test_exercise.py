import json
from pathlib import Path
import unittest

from eventcourt.store import connect, run


class ExerciseTest(unittest.TestCase):
    def test_real_contacts_and_dwell_distinguish_identical_dashboard_histories(self):
        db = connect(':memory:')
        self.addCleanup(db.close)
        fixture = Path(__file__).resolve().parents[1] / 'fixtures/exercise-causal.json'
        events = json.loads(fixture.read_text(encoding='utf-8'))
        result = {row['input']['event_id']: run(db, row['command'], row['input']) for row in events}
        for world in ('A', 'B'):
            self.assertEqual(result[f'{world}-both-read-2']['value'], 'ready')
            self.assertEqual(result[f'{world}-both-read-3']['value'], 'ready')
        self.assertEqual(result['A-intervention-read-3']['value'], 'ready')
        self.assertEqual(result['B-intervention-read-2']['value'], 'ready')
        self.assertEqual(result['B-intervention-read-3']['value'], 'ready')
        self.assertEqual(result['A-intervention-read-4']['value'], 'ready')
        self.assertEqual(result['B-intervention-read-4']['value'], 'fault')
        self.assertEqual(result['A-contact-contact']['value'], 'echo')
        self.assertEqual(result['B-contact-contact']['value'], 'service_contact')
