"""Derive a usable offline change restriction from an SLO close."""
from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS advisories(id TEXT PRIMARY KEY,close TEXT,action TEXT);
"""


def handle(db,x):
    if x['op']!='advisory-publish':
        return {'decision':'unknown_operation'}
    c=one(db,'SELECT * FROM slo_closes WHERE id=?',(x['close'],))
    if not c or x['limit']<0:
        return {'decision':'advisory_denied'}
    action='defer_changes' if c['burn']>x['limit'] else 'allow_changes'
    db.execute('INSERT INTO advisories VALUES(?,?,?)',(x['id'],c['id'],action))
    return {'decision':action}
