"""Evaluate ordered watch rules against persisted offline incident events."""
from .store import one, rows

SCHEMA = """
CREATE TABLE IF NOT EXISTS watch_rules(id TEXT PRIMARY KEY, position INTEGER UNIQUE, service TEXT, kind TEXT, action TEXT);
CREATE TABLE IF NOT EXISTS watch_firings(id TEXT PRIMARY KEY, incident TEXT, rule TEXT, action TEXT);
"""


def handle(db,x):
    if x['op']=='watch-rule':
        if x['action'] not in ('page','hold'):
            return {'decision':'invalid_watch_action'}
        db.execute('INSERT INTO watch_rules VALUES(?,?,?,?,?)',
                   (x['id'],x['position'],x['service'],x['kind'],x['action']))
        return {'decision':'watch_rule_active'}
    if x['op']=='watch-evaluate':
        i=one(db,'SELECT * FROM correlations WHERE id=?',(x['incident'],))
        if not i or i['status']!='open':
            return {'decision':'watch_no_open_case'}
        rules=rows(db,'SELECT * FROM watch_rules ORDER BY position')
        for rule in rules:
            if rule['service'] in ('*',i['service']) and rule['kind'] in ('*',i['kind']):
                db.execute('INSERT INTO watch_firings VALUES(?,?,?,?)',
                           (x['id'],i['id'],rule['id'],rule['action']))
                return {'decision':rule['action'],'rule':rule['id']}
        return {'decision':'watch_no_match'}
    return {'decision':'unknown_operation'}
