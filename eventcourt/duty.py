from .store import one
SCHEMA='''
CREATE TABLE IF NOT EXISTS subscriptions(id TEXT PRIMARY KEY,service TEXT,kind TEXT,team TEXT,generation INTEGER,status TEXT);
CREATE TABLE IF NOT EXISTS oncall_windows(id TEXT PRIMARY KEY,service TEXT,team TEXT,start INTEGER,expires INTEGER,status TEXT);
CREATE TABLE IF NOT EXISTS ownership_claims(id TEXT PRIMARY KEY,service TEXT,from_team TEXT,to_team TEXT,at INTEGER,from_ack TEXT,to_ack TEXT,status TEXT);
'''
def handle(db,x):
 op=x['op']
 if op=='subscription-activate':
  old=one(db,'SELECT * FROM subscriptions WHERE id=?',(x['id'],))
  if old and x['generation']<=old['generation']:return {'decision':'stale_subscription'}
  if old and old['team']!=x['team']:return {'decision':'team_change_requires_handoff'}
  db.execute('INSERT INTO subscriptions VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET service=excluded.service,kind=excluded.kind,team=excluded.team,generation=excluded.generation,status=excluded.status',(x['id'],x['service'],x['kind'],x['team'],x['generation'],'active'))
  return {'decision':'subscription_active'}
 if op=='oncall':
  if x['expires']<=x['start']:return {'decision':'invalid_window'}
  db.execute('INSERT INTO oncall_windows VALUES(?,?,?,?,?,?)',(x['id'],x['service'],x['team'],x['start'],x['expires'],'active'))
  return {'decision':'oncall_active'}
 if op=='duty-handoff':
  if not x.get('from_ack') or not x.get('to_ack') or x['from_ack']==x['to_ack']:return {'decision':'handoff_unconfirmed'}
  current=one(db,'SELECT * FROM subscriptions WHERE id=?',(x['subscription'],))
  if not current or current['team']!=x['from_team'] or x['generation']<=current['generation']:return {'decision':'stale_owner'}
  db.execute('INSERT INTO ownership_claims VALUES(?,?,?,?,?,?,?,?)',(x['id'],current['service'],x['from_team'],x['to_team'],x['at'],x['from_ack'],x['to_ack'],'accepted'))
  db.execute('UPDATE subscriptions SET team=?,generation=? WHERE id=?',(x['to_team'],x['generation'],x['subscription']))
  return {'decision':'duty_transferred'}
 return {'decision':'unknown_operation'}
