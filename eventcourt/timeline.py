"""Record durable operator action marks linked to incident response assignments."""
from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS action_marks(id TEXT PRIMARY KEY,assignment TEXT,incident TEXT,at INTEGER,label TEXT);
"""


def handle(db,x):
    if x['op']!='action-mark':
        return {'decision':'unknown_operation'}
    a=one(db,'SELECT * FROM assignments WHERE id=?',(x['assignment'],))
    if not a or a['incident']!=x['incident']:
        return {'decision':'action_unassigned'}
    db.execute('INSERT INTO action_marks VALUES(?,?,?,?,?)',(x['id'],a['id'],a['incident'],x['at'],x['label']))
    return {'decision':'action_recorded'}
