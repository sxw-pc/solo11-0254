"""Apply local offline interface mode changes after incident-specific acknowledgment."""
from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS endpoints(id TEXT PRIMARY KEY, incident TEXT, mode TEXT);
CREATE TABLE IF NOT EXISTS mode_moves(id TEXT PRIMARY KEY, endpoint TEXT, old TEXT, new TEXT);
"""


def handle(db,x):
    if x['op']=='endpoint-register':
        i=one(db,'SELECT id FROM correlations WHERE id=?',(x['incident'],))
        if not i or x['mode'] not in ('manual','assisted'):
            return {'decision':'endpoint_denied'}
        db.execute('INSERT INTO endpoints VALUES(?,?,?)',(x['id'],i['id'],x['mode']))
        return {'decision':'endpoint_registered'}
    if x['op']=='endpoint-switch':
        e=one(db,'SELECT * FROM endpoints WHERE id=?',(x['endpoint'],))
        d=one(db,'SELECT * FROM deliveries WHERE id=?',(x['delivery'],))
        if (not e or not d or d['incident']!=e['incident'] or d['status']!='acknowledged'
            or x['mode'] not in ('manual','assisted') or x['mode']==e['mode']):
            return {'decision':'switch_denied'}
        db.execute('UPDATE endpoints SET mode=? WHERE id=?',(x['mode'],e['id']))
        db.execute('INSERT INTO mode_moves VALUES(?,?,?,?)',(x['id'],e['id'],e['mode'],x['mode']))
        return {'decision':'endpoint_switched','mode':x['mode']}
    return {'decision':'unknown_operation'}
