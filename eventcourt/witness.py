"""Accept a synthetic field artifact only while its recorder is in an approved mode."""
from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS witnesses(id TEXT PRIMARY KEY, endpoint TEXT, incident TEXT, payload TEXT);
"""


def handle(db,x):
    if x['op']!='witness-record':
        return {'decision':'unknown_operation'}
    e=one(db,'SELECT * FROM endpoints WHERE id=?',(x['endpoint'],))
    if not e or e['incident']!=x['incident'] or e['mode']!='assisted' or not x['payload']:
        return {'decision':'witness_denied'}
    db.execute('INSERT INTO witnesses VALUES(?,?,?,?)',(x['id'],e['id'],e['incident'],x['payload']))
    return {'decision':'witness_recorded'}
