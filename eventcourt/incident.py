from .store import one,rows
SCHEMA='''
CREATE TABLE IF NOT EXISTS event_sources(id TEXT PRIMARY KEY,epoch INTEGER,state TEXT);
CREATE TABLE IF NOT EXISTS raw_events(id TEXT PRIMARY KEY,source TEXT,epoch INTEGER,seq INTEGER,service TEXT,uid TEXT,kind TEXT,at INTEGER,incident TEXT);
CREATE TABLE IF NOT EXISTS correlations(id TEXT PRIMARY KEY,service TEXT,uid TEXT,kind TEXT,status TEXT);
'''
def handle(db,x):
 op=x['op']
 if op=='source-register':
  old=one(db,'SELECT * FROM event_sources WHERE id=?',(x['id'],))
  if old and x['epoch']<=old['epoch']:return {'decision':'stale_source'}
  db.execute('INSERT INTO event_sources VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET epoch=excluded.epoch,state=excluded.state',(x['id'],x['epoch'],'active'));return {'decision':'source_active'}
 if op=='event-ingest':
  src=one(db,'SELECT * FROM event_sources WHERE id=?',(x['source'],))
  if not src or src['epoch']!=x['epoch'] or src['state']!='active':return {'decision':'untrusted_source'}
  last=one(db,'SELECT MAX(seq) n FROM raw_events WHERE source=? AND epoch=?',(x['source'],x['epoch']))['n']
  if last is not None and x['seq']<=last:return {'decision':'stale_event'}
  db.execute('INSERT INTO raw_events VALUES(?,?,?,?,?,?,?,?,?)',(x['id'],x['source'],x['epoch'],x['seq'],x['service'],x['uid'],x['kind'],x['at'],None));return {'decision':'event_recorded'}
 if op=='incident-correlate':
  e=one(db,'SELECT * FROM raw_events WHERE id=?',(x['event'],))
  if not e or e['incident']:return {'decision':'event_unavailable'}
  old=one(db,'SELECT * FROM correlations WHERE id=?',(x['id'],))
  if old and (old['service'],old['uid'],old['kind'])!=(e['service'],e['uid'],e['kind']):return {'decision':'different_incident_identity'}
  if not old:db.execute('INSERT INTO correlations VALUES(?,?,?,?,?)',(x['id'],e['service'],e['uid'],e['kind'],'open'))
  db.execute('UPDATE raw_events SET incident=? WHERE id=?',(x['id'],x['event']))
  return {'decision':'incident_open' if not old else 'event_correlated'}
 if op=='incident-split':
  e=one(db,'SELECT * FROM raw_events WHERE id=?',(x['event'],))
  if not e or not e['incident']:return {'decision':'split_denied'}
  db.execute('INSERT INTO correlations VALUES(?,?,?,?,?)',(x['new_id'],e['service'],e['uid'],e['kind'],'open'))
  db.execute('UPDATE raw_events SET incident=? WHERE id=?',(x['new_id'],x['event']))
  return {'decision':'incident_split','original':e['incident']}
 return {'decision':'unknown_operation'}
