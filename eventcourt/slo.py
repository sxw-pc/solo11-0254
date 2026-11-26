"""Close offline synthetic SLO periods from incident-owned service degradation."""
from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS slo_items(id TEXT PRIMARY KEY,incident TEXT,service TEXT,start INTEGER,end INTEGER);
CREATE TABLE IF NOT EXISTS slo_closes(id TEXT PRIMARY KEY,service TEXT,start INTEGER,end INTEGER,burn INTEGER);
"""


def handle(db,x):
    if x['op']=='slo-observe':
        i=one(db,'SELECT * FROM correlations WHERE id=?',(x['incident'],))
        if not i or i['service']!=x['service'] or x['end']<=x['start']:
            return {'decision':'slo_observation_denied'}
        db.execute('INSERT INTO slo_items VALUES(?,?,?,?,?)',(x['id'],i['id'],i['service'],x['start'],x['end']))
        return {'decision':'slo_observed'}
    if x['op']=='slo-close':
        if x['end']<=x['start']:
            return {'decision':'slo_close_denied'}
        v=one(db,"""SELECT COALESCE(SUM(MIN(end,?)-MAX(start,?)),0) burn FROM slo_items
                    WHERE service=? AND start<? AND end>?""",(x['end'],x['start'],x['service'],x['end'],x['start']))['burn']
        db.execute('INSERT INTO slo_closes VALUES(?,?,?,?,?)',(x['id'],x['service'],x['start'],x['end'],v))
        return {'decision':'slo_closed','burn':v}
    return {'decision':'unknown_operation'}
