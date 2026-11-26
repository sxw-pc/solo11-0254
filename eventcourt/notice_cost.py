"""Track offline signed incident remediation purchases and budget commitments."""
from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS recovery_funds(id TEXT PRIMARY KEY, remaining INTEGER);
CREATE TABLE IF NOT EXISTS recovery_purchases(id TEXT PRIMARY KEY, fund TEXT, incident TEXT, cents INTEGER);
"""


def handle(db,x):
    if x['op']=='fund-open':
        if x['cents']<=0:
            return {'decision':'fund_invalid'}
        db.execute('INSERT INTO recovery_funds VALUES(?,?)',(x['id'],x['cents']))
        return {'decision':'fund_opened'}
    if x['op']=='purchase-record':
        incident=one(db,'SELECT * FROM correlations WHERE id=?',(x['incident'],))
        balance=one(db,'SELECT remaining FROM recovery_funds WHERE id=?',(x['fund'],))
        if not incident or incident['status']!='open' or not balance or not 0 < x['cents'] <= balance['remaining']:
            return {'decision':'purchase_denied'}
        db.execute('UPDATE recovery_funds SET remaining=remaining-? WHERE id=?',(x['cents'],x['fund']))
        db.execute('INSERT INTO recovery_purchases VALUES(?,?,?,?)',(x['id'],x['fund'],incident['id'],x['cents']))
        return {'decision':'purchase_recorded','remaining':balance['remaining']-x['cents']}
    return {'decision':'unknown_operation'}
