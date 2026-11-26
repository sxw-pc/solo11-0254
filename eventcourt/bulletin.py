"""Freeze an offline operator bulletin from actually received incident packets."""
from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS bulletins(id TEXT PRIMARY KEY,packet TEXT,team TEXT,body TEXT);
"""


def handle(db,x):
    if x['op']!='bulletin-freeze':
        return {'decision':'unknown_operation'}
    p=one(db,'SELECT * FROM wire_packets WHERE id=?',(x['packet'],))
    if not p or p['status']!='received' or p['team']!=x['team']:
        return {'decision':'bulletin_undelivered'}
    db.execute('INSERT INTO bulletins VALUES(?,?,?,?)',(x['id'],p['id'],p['team'],p['body']))
    return {'decision':'bulletin_frozen','body':p['body']}
