"""Capture actual display or directly attributable actuator results on the training rig."""
from .store import one

SCHEMA = """
CREATE TABLE IF NOT EXISTS exercise_observations (
    id TEXT PRIMARY KEY, rig TEXT NOT NULL, tick INTEGER NOT NULL,
    instrument TEXT NOT NULL, value TEXT NOT NULL, reset TEXT);
"""


def handle(db, request):
    rig = one(db, 'SELECT * FROM exercise_rigs WHERE id=?', (request['rig'],))
    if not rig or request['at'] != rig['tick']:
        return {'decision': 'observation_stale'}
    tick = rig['tick']
    if request['op'] == 'dashboard':
        reset_id = None
        value = 'ready' if rig['service_ready'] or tick < rig['echo_until'] else 'fault'
    elif request['op'] == 'contact':
        reset_id = request['reset']
        motion = one(db, 'SELECT * FROM exercise_resets WHERE id=? AND rig=?', (reset_id, rig['id']))
        if not motion or motion['tick'] != tick:
            return {'decision': 'contact_stale'}
        # An echo is generated on the handle's local display contact only.
        value = 'echo' if motion['echo_until'] == tick + 2 else 'service_contact'
    else:
        return {'decision': 'unknown_operation'}
    db.execute('INSERT INTO exercise_observations VALUES(?,?,?,?,?,?)',
               (request['event_id'], rig['id'], tick, request['op'], value, reset_id))
    return {'decision': 'exercise_observed', 'tick': tick, 'value': value}
