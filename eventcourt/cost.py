"""Close offline operator work tallies from incident-owned acknowledgments."""
from .store import one,rows

SCHEMA = """
CREATE TABLE IF NOT EXISTS operator_work(id TEXT PRIMARY KEY,receipt TEXT,team TEXT,inc TEXT,units INTEGER);
CREATE TABLE IF NOT EXISTS operator_tally(id TEXT PRIMARY KEY,team TEXT,units INTEGER);
"""


def handle(db,x):
    if x['op']=='work-record':
        r=one(db,'SELECT * FROM ack_receipts WHERE id=?',(x['receipt'],))
        d=one(db,'SELECT * FROM deliveries WHERE id=?',(r['delivery'],)) if r else None
        if not d or r['team']!=x['team'] or r['at']>x['ended'] or x['units']<=0:
            return {'decision':'work_unattributed'}
        db.execute('INSERT INTO operator_work VALUES(?,?,?,?,?)',(x['id'],r['id'],r['team'],d['incident'],x['units']))
        return {'decision':'work_recorded','incident':d['incident']}
    if x['op']=='work-tally':
        total=one(db,'SELECT COALESCE(SUM(units),0) n FROM operator_work WHERE team=?',(x['team'],))['n']
        db.execute('INSERT INTO operator_tally VALUES(?,?,?)',(x['id'],x['team'],total))
        return {'decision':'work_tallied','units':total}
    return {'decision':'unknown_operation'}
