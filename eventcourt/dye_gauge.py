"""Qualify a printed sample from the actual contents of a simulated vat."""
from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS dye_reads(id TEXT PRIMARY KEY, vat TEXT, volume INTEGER, dark INTEGER, disposition TEXT);
"""


def handle(db, item):
    if item['op'] != 'gauge-read':
        return {'decision': 'unknown_operation'}
    vat = one(db, 'SELECT * FROM dye_vats WHERE id=?', (item['vat'],))
    if not vat or not vat['volume']:
        return {'decision': 'gauge_empty'}
    target = item['dark_per_four']
    if type(target) is not int or not 0 <= target <= 4:
        return {'decision': 'gauge_target_invalid'}
    disposition = 'gauge_pass' if 4 * vat['dark'] == target * vat['volume'] else 'gauge_hold'
    db.execute('INSERT INTO dye_reads VALUES(?,?,?,?,?)', (item['id'], vat['id'], vat['volume'], vat['dark'], disposition))
    return {'decision': disposition, 'volume': vat['volume'], 'dark': vat['dark']}
