"""Track offline mitigation observations and issue cover determinations."""
from .store import one, rows

SCHEMA = """
CREATE TABLE IF NOT EXISTS impact_cells(
    id TEXT PRIMARY KEY, incident TEXT, weight INTEGER, cohort TEXT
);
CREATE TABLE IF NOT EXISTS remedy_checks(
    id TEXT PRIMARY KEY, cell TEXT, delivery TEXT, receipt TEXT, checked_at INTEGER, result TEXT
);
CREATE TABLE IF NOT EXISTS remedy_clearances(
    id TEXT PRIMARY KEY, incident TEXT, checked_at INTEGER, covered INTEGER, total INTEGER
);
"""


def handle(db, item):
    op = item['op']
    if op == 'impact-cell':
        incident = one(db, 'SELECT status FROM correlations WHERE id=?', (item['incident'],))
        if not incident or incident['status'] != 'open' or item['weight'] <= 0:
            return {'decision': 'impact_cell_rejected'}
        db.execute('INSERT INTO impact_cells VALUES(?,?,?,?)',
                   (item['id'],item['incident'],item['weight'],item['cohort']))
        return {'decision': 'impact_cell_recorded'}
    if op == 'remedy-check':
        cell = one(db, 'SELECT * FROM impact_cells WHERE id=?', (item['cell'],))
        delivery = one(db, 'SELECT * FROM deliveries WHERE id=?', (item['delivery'],))
        ack = one(db, 'SELECT * FROM ack_receipts WHERE id=?', (item['receipt'],))
        if (not cell or not delivery or delivery['incident'] != cell['incident'] or
                not ack or ack['delivery'] != delivery['id'] or ack['at'] > item['at'] or
                item['result'] not in ('healthy','impaired')):
            return {'decision': 'remedy_check_unattributed'}
        db.execute('INSERT INTO remedy_checks VALUES(?,?,?,?,?,?)', (
            item['id'],cell['id'],delivery['id'],ack['id'],item['at'],item['result']))
        return {'decision': 'remedy_check_recorded', 'result': item['result']}
    if op == 'remedy-clear':
        cells = rows(db, 'SELECT * FROM impact_cells WHERE incident=? ORDER BY id', (item['incident'],))
        covered = 0
        for cell in cells:
            latest = one(db, 'SELECT result FROM remedy_checks WHERE cell=? AND checked_at<=? '
                         'ORDER BY checked_at DESC,id DESC LIMIT 1', (cell['id'],item['at']))
            if latest and latest['result'] == 'healthy':
                covered += cell['weight']
        total = sum(cell['weight'] for cell in cells)
        if not total or total != covered:
            return {'decision':'impact_still_open','covered':covered,'total':total}
        db.execute('INSERT INTO remedy_clearances VALUES(?,?,?,?,?)',
                   (item['id'],item['incident'],item['at'],covered,total))
        return {'decision':'remedy_cleared','covered':covered,'total':total}
    return {'decision': 'unknown_operation'}
