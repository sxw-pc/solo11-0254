"""Fit a punched quality card onto a local simulated checking head."""
import json

from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS check_fits(id TEXT PRIMARY KEY, card TEXT, holes TEXT, outcome TEXT);
"""


def handle(db,item):
    if item['op'] != 'card-fit':
        return {'decision':'unknown_operation'}
    card = one(db,'SELECT * FROM check_cards WHERE id=?',(item['card'],))
    if not card:
        return {'decision':'fit_unknown_card'}
    holes = set(json.loads(card['holes']))
    pins = set(item['pins'])
    sealed = set(item['sealed'])
    if pins & sealed or any(type(point) is not int or not 0 <= point < card['size'] for point in pins | sealed):
        return {'decision':'fit_invalid'}
    outcome = 'card_fitted' if pins <= holes and not (sealed & holes) else 'card_wont_fit'
    db.execute('INSERT INTO check_fits VALUES(?,?,?,?)',(item['id'],card['id'],card['holes'],outcome))
    return {'decision':outcome,'holes':sorted(holes)}
