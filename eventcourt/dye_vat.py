"""Simulate whole-cartridge mixing of harmless colored water at an incident bench."""
from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS dye_vats(id TEXT PRIMARY KEY, incident TEXT, volume INTEGER, dark INTEGER, capacity INTEGER);
CREATE TABLE IF NOT EXISTS dye_cartridges(id TEXT PRIMARY KEY, incident TEXT, volume INTEGER, dark INTEGER, spent INTEGER);
CREATE TABLE IF NOT EXISTS dye_pours(id TEXT PRIMARY KEY, cartridge TEXT UNIQUE, vat TEXT, volume INTEGER, dark INTEGER);
"""


def handle(db, item):
    op = item['op']
    if op in ('vat-open', 'cartridge-stock'):
        case = one(db, 'SELECT id FROM correlations WHERE id=?', (item['incident'],))
        if not case:
            return {'decision': 'dye_case_missing'}
        if op == 'vat-open':
            capacity = item['capacity']
            if type(capacity) is not int or capacity < 1:
                return {'decision': 'vat_invalid'}
            db.execute('INSERT INTO dye_vats VALUES(?,?,0,0,?)', (item['id'], case['id'], capacity))
            return {'decision': 'vat_opened'}
        volume, dark = item['volume'], item['dark']
        if type(volume) is not int or type(dark) is not int or not 0 <= dark <= volume or volume < 1:
            return {'decision': 'cartridge_invalid'}
        db.execute('INSERT INTO dye_cartridges VALUES(?,?,?,?,0)', (item['id'], case['id'], volume, dark))
        return {'decision': 'cartridge_stocked'}
    if op == 'vat-pour':
        vat = one(db, 'SELECT * FROM dye_vats WHERE id=?', (item['vat'],))
        cartridge = one(db, 'SELECT * FROM dye_cartridges WHERE id=?', (item['cartridge'],))
        if (not vat or not cartridge or vat['incident'] != cartridge['incident'] or cartridge['spent']
                or vat['volume'] + cartridge['volume'] > vat['capacity']):
            return {'decision': 'pour_denied'}
        volume, dark = vat['volume'] + cartridge['volume'], vat['dark'] + cartridge['dark']
        db.execute('UPDATE dye_cartridges SET spent=1 WHERE id=?', (cartridge['id'],))
        db.execute('UPDATE dye_vats SET volume=?,dark=? WHERE id=?', (volume, dark, vat['id']))
        db.execute('INSERT INTO dye_pours VALUES(?,?,?,?,?)', (item['id'], cartridge['id'], vat['id'], volume, dark))
        return {'decision': 'poured', 'volume': volume, 'dark': dark}
    return {'decision': 'unknown_operation'}
