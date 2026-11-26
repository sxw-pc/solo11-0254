import json,tempfile,unittest
from pathlib import Path
import eventcourt
from eventcourt.store import connect,run,replay,one
ROOT=Path(__file__).resolve().parents[1]
class Business(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'db.sqlite';self.db=connect(str(self.path))
 def tearDown(self):self.db.close();self.tmp.cleanup()
 def steps(self):return json.loads((ROOT/'fixtures/path.json').read_text(encoding='utf-8'))
 def test_handoff_suppression_and_release(self):
  out=[run(self.db,x['command'],x['input']) for x in self.steps()]
  self.assertEqual(out[6]['decision'],'duty_transferred');self.assertEqual(out[8],{'decision':'suppressed','team':'team-b'})
  self.assertEqual(out[9]['decision'],'notifications_released');self.assertEqual(out[10]['decision'],'acknowledged')
  self.assertTrue(replay(str(self.path))['verified'])
 def test_old_generation_cannot_join_new_incident(self):
  p=self.steps()
  for x in p[:3]:run(self.db,x['command'],x['input'])
  bad=dict(p[1]['input'],event_id='late',id='raw-old',seq=1)
  self.assertEqual(run(self.db,'incident',bad)['decision'],'stale_event')
 def test_hardware_suppression_is_denied(self):
  got=run(self.db,'delivery',{'event_id':'hard','op':'suppression-grant','id':'h','service':'svc-a','kind':'hardware','start':0,'expires':10,'approver':'owner'})
  self.assertEqual(got['decision'],'suppression_denied')
 def test_suppression_expiry_uses_current_duty_owner(self):
  p=self.steps()
  for x in p[:9]:run(self.db,x['command'],x['input'])
  run(self.db,'duty',{'event_id':'shift-c','op':'oncall','id':'shift-c','service':'svc-a','team':'team-c','start':18,'expires':30})
  run(self.db,'duty',{'event_id':'transfer-c','op':'duty-handoff','id':'handoff-c','subscription':'sub-1','from_team':'team-b','to_team':'team-c','generation':3,'at':19,'from_ack':'ack-b2','to_ack':'ack-c'})
  self.assertEqual(run(self.db,'delivery',p[9]['input'])['decision'],'notifications_released')
  self.assertEqual(one(self.db,'SELECT team FROM deliveries WHERE id=?',('send-1',))['team'],'team-c')
  self.assertEqual(run(self.db,'delivery',p[10]['input'])['decision'],'ack_denied')
 def test_duplicate_route_does_not_notify_new_team(self):
  p=self.steps()
  for x in p[:9]:run(self.db,x['command'],x['input'])
  duplicate=dict(p[8]['input'],event_id='route-again',id='send-2',at=16)
  self.assertEqual(run(self.db,'delivery',duplicate)['decision'],'already_routed')
  self.assertEqual(one(self.db,'SELECT COUNT(*) n FROM deliveries')['n'],1)
 def test_old_or_different_generation_event_cannot_merge(self):
  p=self.steps()
  for x in p[:3]:run(self.db,x['command'],x['input'])
  fresh=dict(p[1]['input'],event_id='fresh',id='raw-2',seq=2,uid='svc-uid2')
  run(self.db,'incident',fresh)
  self.assertEqual(run(self.db,'incident',{'event_id':'wrong-join','op':'incident-correlate','id':'inc-1','event':'raw-2'})['decision'],'different_incident_identity')
 def test_split_keeps_original_notification_evidence(self):
  p=self.steps()
  for x in p[:9]:run(self.db,x['command'],x['input'])
  self.assertEqual(run(self.db,'incident',{'event_id':'split','op':'incident-split','event':'raw-1','new_id':'inc-2'})['decision'],'incident_split')
  self.assertEqual(one(self.db,'SELECT incident FROM deliveries WHERE id=?',('send-1',))['incident'],'inc-1')
 def test_subscription_reactivation_cannot_bypass_two_party_handoff(self):
  p=self.steps()
  for x in p[:5]:run(self.db,x['command'],x['input'])
  forged=dict(p[3]['input'],event_id='forged-owner',team='team-b',generation=2)
  self.assertEqual(run(self.db,'duty',forged)['decision'],'team_change_requires_handoff')
  self.assertEqual(one(self.db,'SELECT team FROM subscriptions WHERE id=?',('sub-1',))['team'],'team-a')
 def test_overlapping_suppression_keeps_incident_on_hold(self):
  p=self.steps()
  for x in p[:9]:run(self.db,x['command'],x['input'])
  second=dict(p[7]['input'],event_id='second-window',id='maint-2',start=12,expires=25)
  run(self.db,'delivery',second)
  out=run(self.db,'delivery',p[9]['input'])
  self.assertEqual(out['deliveries'],[])
  self.assertEqual(one(self.db,'SELECT status FROM deliveries WHERE id=?',('send-1',))['status'],'suppressed')
 def test_each_fixture_runs_from_empty_database_and_replays(self):
  expected={'incident': 'incident_open', 'duty': 'duty_transferred', 'delivery': 'suppressed'}
  for c in ('incident', 'duty', 'delivery'):
   for suffix in ('normal','failure'):
    with self.subTest(command=c,variant=suffix), tempfile.TemporaryDirectory() as td:
     path=Path(td)/'fixture.sqlite';db=connect(str(path))
     commands=json.loads((ROOT/'fixtures'/f'{c}_{suffix}.json').read_text(encoding='utf-8'))
     results=[run(db,x['command'],x['input']) for x in commands]
     db.close()
     self.assertEqual(results[-1]['decision'],expected[c] if suffix=='normal' else {'incident': 'untrusted_source', 'duty': 'handoff_unconfirmed', 'delivery': 'incident_unavailable'}[c])
     self.assertTrue(replay(str(path))['verified'])
  self.assertEqual(Path(eventcourt.__file__).resolve().parents[1],ROOT)
print('module_file',eventcourt.__file__)
