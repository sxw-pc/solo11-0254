"""Read a complete light sequence at the local simulated receiver."""
from .signal_panel import CODEWORDS
from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS panel_reads(id TEXT PRIMARY KEY, sequence TEXT, label TEXT);
"""


def handle(db, item):
    if item['op'] != 'panel-read':
        return {'decision': 'unknown_operation'}
    sequence = one(db, 'SELECT * FROM panel_sequences WHERE id=?', (item['sequence'],))
    if not sequence:
        return {'decision': 'panel_read_missing'}
    label = next((label for label, frames in CODEWORDS.items() if frames == sequence['frames']), None)
    if label is None:
        return {'decision': 'panel_unreadable'}
    db.execute('INSERT INTO panel_reads VALUES(?,?,?)', (item['id'], sequence['id'], label))
    return {'decision': 'panel_read', 'label': label}
