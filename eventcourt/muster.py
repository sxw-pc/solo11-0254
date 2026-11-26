"""Track synthetic staffed response channels using actual duty assignments."""
from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS responders(id TEXT PRIMARY KEY,team TEXT,capacity INTEGER);
CREATE TABLE IF NOT EXISTS assignments(id TEXT PRIMARY KEY,incident TEXT,responder TEXT,units INTEGER);
"""


def handle(db,x):
    if x['op']=='responder-register':
        if x['capacity']<=0:
            return {'decision':'capacity_invalid'}
        db.execute('INSERT INTO responders VALUES(?,?,?)',(x['id'],x['team'],x['capacity']))
        return {'decision':'responder_registered'}
    if x['op']=='response-assign':
        p=one(db,'SELECT * FROM responders WHERE id=?',(x['responder'],))
        d=one(db,'SELECT * FROM deliveries WHERE id=?',(x['delivery'],))
        load=one(db,'SELECT COALESCE(SUM(units),0) n FROM assignments WHERE responder=?',(x['responder'],))['n']
        if not p or not d or p['team']!=d['team'] or d['status']!='acknowledged' or not 0<x['units']<=p['capacity']-load:
            return {'decision':'assign_denied'}
        db.execute('INSERT INTO assignments VALUES(?,?,?,?)',(x['id'],d['incident'],p['id'],x['units']))
        return {'decision':'assigned','remaining':p['capacity']-load-x['units']}
    return {'decision':'unknown_operation'}
