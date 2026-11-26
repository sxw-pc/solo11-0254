"""Drive local simulated maintenance lights from a recorded field action."""
from .store import one

CODEWORDS = {'inspect': '101', 'hold': '110', 'clear': '011'}
SCHEMA = """
CREATE TABLE IF NOT EXISTS panel_sequences(id TEXT PRIMARY KEY, mark TEXT, frames TEXT);
"""


def handle(db, item):
    if item['op'] != 'panel-emit':
        return {'decision': 'unknown_operation'}
    mark = one(db, 'SELECT * FROM action_marks WHERE id=?', (item['mark'],))
    frames = CODEWORDS.get(mark['label']) if mark else None
    if frames is None:
        return {'decision': 'panel_denied'}
    db.execute('INSERT INTO panel_sequences VALUES(?,?,?)', (item['id'], mark['id'], frames))
    return {'decision': 'panel_emitted', 'frames': frames}
