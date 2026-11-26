"""Operate a harmless simulated quality-card punch on incident field materials."""
import json

from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS check_cards(id TEXT PRIMARY KEY, incident TEXT, size INTEGER, holes TEXT);
CREATE TABLE IF NOT EXISTS check_punches(id TEXT PRIMARY KEY, card TEXT, anchor INTEGER, holes TEXT);
"""


def handle(db,item):
    op = item['op']
    if op == 'card-open':
        case = one(db, 'SELECT id FROM correlations WHERE id=?',(item['incident'],))
        if not case or type(item['size']) is not int or not 3 <= item['size'] <= 32:
            return {'decision':'card_rejected'}
        db.execute('INSERT INTO check_cards VALUES(?,?,?,?)',(item['id'],case['id'],item['size'],'[]'))
        return {'decision':'card_opened'}
    if op != 'card-punch':
        return {'decision':'unknown_operation'}
    card = one(db, 'SELECT * FROM check_cards WHERE id=?',(item['card'],))
    anchor = item['anchor']
    offsets = item['offsets']
    if not card or type(anchor) is not int or not 0 <= anchor < card['size'] or not offsets:
        return {'decision':'punch_invalid'}
    previous = set(json.loads(card['holes']))
    if anchor in previous:
        return {'decision':'punch_anchor_broken'}
    if any(type(offset) is not int or offset == 0 or not 0 <= anchor + offset < card['size'] for offset in offsets):
        return {'decision':'punch_invalid'}
    holes = sorted(previous | {anchor + offset for offset in offsets})
    encoded = json.dumps(holes)
    db.execute('UPDATE check_cards SET holes=? WHERE id=?',(encoded,card['id']))
    db.execute('INSERT INTO check_punches VALUES(?,?,?,?)',(item['id'],card['id'],anchor,encoded))
    return {'decision':'card_punched','holes':holes}
