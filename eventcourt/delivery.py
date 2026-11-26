from .store import one,rows
SCHEMA='''
CREATE TABLE IF NOT EXISTS suppression_grants(id TEXT PRIMARY KEY,service TEXT,kind TEXT,start INTEGER,expires INTEGER,approver TEXT,status TEXT);
CREATE TABLE IF NOT EXISTS deliveries(id TEXT PRIMARY KEY,incident TEXT,team TEXT,at INTEGER,status TEXT);
CREATE TABLE IF NOT EXISTS ack_receipts(id TEXT PRIMARY KEY,delivery TEXT,team TEXT,at INTEGER,status TEXT);
'''
def handle(db,x):
 op=x['op']
 if op=='suppression-grant':
  if x['kind']=='hardware' or not x.get('approver') or x['expires']<=x['start']:return {'decision':'suppression_denied'}
  db.execute('INSERT INTO suppression_grants VALUES(?,?,?,?,?,?,?)',(x['id'],x['service'],x['kind'],x['start'],x['expires'],x['approver'],'active'))
  return {'decision':'suppression_active'}
 if op=='notification-route':
  inc=one(db,'SELECT * FROM correlations WHERE id=?',(x['incident'],))
  if not inc or inc['status']!='open':return {'decision':'incident_unavailable'}
  prior=one(db,"SELECT * FROM deliveries WHERE incident=? AND status IN ('suppressed','sent','acknowledged') ORDER BY at DESC LIMIT 1",(x['incident'],))
  if prior:return {'decision':'already_routed','team':prior['team']}
  sub=one(db,"SELECT * FROM subscriptions WHERE service=? AND kind=? AND status='active' ORDER BY generation DESC LIMIT 1",(inc['service'],inc['kind']))
  if not sub:return {'decision':'no_duty_owner'}
  oncall=one(db,"SELECT 1 FROM oncall_windows WHERE service=? AND team=? AND start<=? AND expires>? AND status='active'",(inc['service'],sub['team'],x['at'],x['at']))
  if not oncall:return {'decision':'owner_off_duty'}
  grant=one(db,"SELECT * FROM suppression_grants WHERE service=? AND kind=? AND start<=? AND expires>? AND status='active' LIMIT 1",(inc['service'],inc['kind'],x['at'],x['at']))
  state='suppressed' if grant else 'sent'
  db.execute('INSERT INTO deliveries VALUES(?,?,?,?,?)',(x['id'],inc['id'],sub['team'],x['at'],state))
  return {'decision':state,'team':sub['team']}
 if op=='delivery-ack':
  delivery=one(db,'SELECT * FROM deliveries WHERE id=?',(x['delivery'],))
  if not delivery or delivery['status']!='sent' or delivery['team']!=x['team']:return {'decision':'ack_denied'}
  db.execute('INSERT INTO ack_receipts VALUES(?,?,?,?,?)',(x['id'],x['delivery'],x['team'],x['at'],'accepted'))
  db.execute("UPDATE deliveries SET status='acknowledged' WHERE id=?",(x['delivery'],))
  return {'decision':'acknowledged'}
 if op=='suppression-expire':
  grant=one(db,'SELECT * FROM suppression_grants WHERE id=?',(x['id'],))
  if not grant or x['at']<grant['expires']:return {'decision':'window_not_expired'}
  db.execute("UPDATE suppression_grants SET status='expired' WHERE id=?",(x['id'],))
  changed=[]
  for d in rows(db,"SELECT * FROM deliveries WHERE status='suppressed' AND incident IN (SELECT id FROM correlations WHERE service=? AND kind=?)",(grant['service'],grant['kind'])):
   overlapping=one(db,"SELECT 1 FROM suppression_grants WHERE id<>? AND service=? AND kind=? AND status='active' AND start<=? AND expires>?",(grant['id'],grant['service'],grant['kind'],x['at'],x['at']))
   if overlapping:continue
   sub=one(db,"SELECT * FROM subscriptions WHERE service=? AND kind=? AND status='active' ORDER BY generation DESC LIMIT 1",(grant['service'],grant['kind']))
   shift=one(db,"SELECT 1 FROM oncall_windows WHERE service=? AND team=? AND start<=? AND expires>? AND status='active'",(grant['service'],sub['team'],x['at'],x['at'])) if sub else None
   if not shift:continue
   db.execute("UPDATE deliveries SET status='sent',team=?,at=? WHERE id=?",(sub['team'],x['at'],d['id']));changed.append(d['id'])
  return {'decision':'notifications_released','deliveries':changed}
 return {'decision':'unknown_operation'}
