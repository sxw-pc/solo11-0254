"""Record outbound offline operator packets and explicit endpoint receipts."""
from .store import one, rows

SCHEMA = """
CREATE TABLE IF NOT EXISTS wire_packets(id TEXT PRIMARY KEY,delivery TEXT,team TEXT,body TEXT,status TEXT);
CREATE TABLE IF NOT EXISTS wire_receipts(id TEXT PRIMARY KEY,packet TEXT,team TEXT);
"""


def handle(db,x):
    if x['op']=='packet-emit':
        d=one(db,'SELECT * FROM deliveries WHERE id=?',(x['delivery'],))
        if not d or d['status'] not in ('sent','acknowledged') or d['team']!=x['team']:
            return {'decision':'packet_not_routable'}
        db.execute('INSERT INTO wire_packets VALUES(?,?,?,?,?)',(x['id'],d['id'],d['team'],x['body'],'outstanding'))
        return {'decision':'packet_emitted','team':d['team']}
    if x['op']=='packet-receive':
        p=one(db,'SELECT * FROM wire_packets WHERE id=?',(x['packet'],))
        if not p or p['team']!=x['team']:
            return {'decision':'packet_receipt_denied'}
        if p['status']=='received':
            return {'decision':'packet_already_received'}
        db.execute('INSERT INTO wire_receipts VALUES(?,?,?)',(x['id'],p['id'],p['team']))
        db.execute("UPDATE wire_packets SET status='received' WHERE id=?",(p['id'],))
        return {'decision':'packet_received'}
    if x['op']=='packet-read':
        queue=rows(db,"SELECT id,body FROM wire_packets WHERE team=? AND status='outstanding' ORDER BY rowid",(x['team'],))
        return {'decision':'packet_queue','packets':queue}
    return {'decision':'unknown_operation'}
