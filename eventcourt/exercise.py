"""Run a virtual incident training rig with two independent reset handles."""
from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS exercise_rigs (
    id TEXT PRIMARY KEY, repairer TEXT NOT NULL, tick INTEGER NOT NULL,
    service_ready INTEGER NOT NULL, echo_until INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS exercise_resets (
    id TEXT PRIMARY KEY, rig TEXT NOT NULL, tick INTEGER NOT NULL,
    handle TEXT NOT NULL, service_ready INTEGER NOT NULL, echo_until INTEGER NOT NULL);
"""


def handle(db, request):
    rig_id = request['rig']
    rig = one(db, 'SELECT * FROM exercise_rigs WHERE id=?', (rig_id,))
    op = request['op']
    if op == 'open':
        repairer = request['repairer']
        if rig or repairer not in ('A', 'B'):
            return {'decision': 'exercise_denied'}
        db.execute('INSERT INTO exercise_rigs VALUES(?,?,0,0,0)', (rig_id, repairer))
        return {'decision': 'exercise_ready'}
    if not rig or request['at'] != rig['tick'] + 1:
        return {'decision': 'exercise_time_denied'}
    tick = request['at']
    if op == 'wait':
        db.execute('UPDATE exercise_rigs SET tick=? WHERE id=?', (tick, rig_id))
        return {'decision': 'exercise_advanced', 'tick': tick}
    if op != 'reset' or request['handle'] not in ('A', 'B'):
        return {'decision': 'exercise_denied'}
    handle = request['handle']
    service_ready = int(rig['service_ready'] or handle == rig['repairer'])
    echo_until = rig['echo_until'] if handle == rig['repairer'] else tick + 2
    db.execute('UPDATE exercise_rigs SET tick=?,service_ready=?,echo_until=? WHERE id=?',
               (tick, service_ready, echo_until, rig_id))
    db.execute('INSERT INTO exercise_resets VALUES(?,?,?,?,?,?)',
               (request['event_id'], rig_id, tick, handle, service_ready, echo_until))
    return {'decision': 'exercise_reset', 'handle': handle, 'tick': tick}
