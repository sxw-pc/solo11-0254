"""Issue operator-facing traffic reopening tickets from verified impact clearance."""
from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS reopen_tickets(
    id TEXT PRIMARY KEY, clearance TEXT UNIQUE, incident TEXT, service TEXT, issued_at INTEGER,
    status TEXT
);
"""


def handle(db,item):
    if item['op'] == 'reopen-ticket':
        clear = one(db,'SELECT * FROM remedy_clearances WHERE id=?',(item['clearance'],))
        incident = one(db,'SELECT * FROM correlations WHERE id=?',(clear['incident'],)) if clear else None
        if (not clear or not incident or incident['status'] != 'open' or
                item['at'] < clear['checked_at'] or incident['service'] != item['service']):
            return {'decision':'reopen_evidence_missing'}
        later = one(db,"""SELECT c.id FROM remedy_checks c JOIN impact_cells t ON c.cell=t.id
                           WHERE t.incident=? AND c.result='impaired' AND c.checked_at>?
                             AND c.checked_at<=? LIMIT 1""",
                    (incident['id'],clear['checked_at'],item['at']))
        if later:
            return {'decision':'reopen_held','check':later['id']}
        if one(db,'SELECT id FROM reopen_tickets WHERE clearance=?',(clear['id'],)):
            return {'decision':'clearance_already_used'}
        db.execute('INSERT INTO reopen_tickets VALUES(?,?,?,?,?,?)', (
            item['id'],clear['id'],incident['id'],incident['service'],item['at'],'issued'))
        return {'decision':'reopen_issued','service':incident['service']}
    return {'decision':'unknown_operation'}
