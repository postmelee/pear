"""Independent finite ABI2 owner transcript checks; no runtime admission."""
from collections import Counter

POSITIVES = {
    'atomic_enter_dispatcher': (1, 8),
    'atomic_handoff_dispatcher': (1, 13),
    'atomic_refusal_preserves_original_pin': (9, 13),
    'atomic_consume_original_pin_on_current_epoch': (1, 14),
    'atomic_exit_consumed_continuation': (1, 9),
}
REFUSALS = {
    'atomic_wrong_size': (14, 1),
    'atomic_wrong_offset': (14, 1),
    'atomic_wrong_continuation': (14, 6),
    'atomic_missing_continuation': (14, 1),
    'atomic_stale_current_epoch': (14, 6),
    'atomic_old_wire_version': (14, 2),
    'atomic_wrong_generation': (14, 6),
    'atomic_wrong_executor': (14, 6),
    'atomic_wrong_role': (14, 6),
    'atomic_retirement_preserves_original_pin': (5, 3),
    'atomic_original_epoch_requires_retry': (14, 6),
    'atomic_consumed_continuation_cannot_repeat': (14, 6),
}

def controls():
    counts = {key: value[0] for key, value in POSITIVES.items()}
    counts.update(dict.fromkeys(REFUSALS, 1))
    statuses = {key: value[1] for key, value in REFUSALS.items()}
    opcodes = {key: value[1] for key, value in POSITIVES.items()}
    opcodes.update({key: value[0] for key, value in REFUSALS.items()})
    return counts, statuses, opcodes

def validate(calls, need):
    selected = [row for row in calls if row['control'].startswith('atomic_')]
    counts, statuses, opcodes = controls()
    need(Counter(row['control'] for row in selected) == counts, 'memory_atomic_control_counts')
    for row in selected:
        need(row['opcode'] == opcodes[row['control']] and row['status'] == statuses.get(row['control'], 0),
             'memory_atomic_control_result')
    good = [row for row in selected if row['status'] == 0]
    for row in good:
        size = 4 if row['control'] in ('atomic_enter_dispatcher', 'atomic_handoff_dispatcher',
                                       'atomic_consume_original_pin_on_current_epoch') else 0
        need(row['requested_state'] == 3 and row['operation_offset'] == '0000000000000000'
             and row['operation_size'] == format(size, '016x') and row['lifecycle'] == 3
             and row['extent_size'] == 16384, 'memory_atomic_operation_shape')
    enter, handoff, *tail = good
    need(enter['control'] == 'atomic_enter_dispatcher' and handoff['control'] == 'atomic_handoff_dispatcher',
         'memory_atomic_entry_order')
    need(enter['executor_state'] == 2 and not enter['continuation_id'] and
         handoff['executor_state'] == 3 and handoff['continuation_id'] > 0,
         'memory_atomic_initial_state')
    need(enter['protection'] == 2 and not handoff['protection'], 'memory_atomic_initial_protection')
    identity = ('allocation_id', 'generation', 'extent_offset', 'extent_size', 'executor_id')
    need(all(enter[key] == handoff[key] and enter[key] > 0 for key in identity if key != 'extent_offset')
         and enter['extent_offset'] == handoff['extent_offset'] and enter['write_epoch'] > 0
         and enter['write_epoch'] == handoff['write_epoch'], 'memory_atomic_initial_identity')
    need(len(tail) == 11, 'memory_atomic_positive_count')
    for poll in tail[:9]:
        need(poll['control'] == 'atomic_refusal_preserves_original_pin' and poll['executor_state'] == 3
             and poll['continuation_id'] == handoff['continuation_id']
             and not poll['protection'] and poll['write_epoch'] == handoff['write_epoch']
             and all(poll[key] == handoff[key] for key in identity), 'memory_atomic_original_pin')
    resume, exit_row = tail[-2:]
    need(resume['control'] == 'atomic_consume_original_pin_on_current_epoch' and
         exit_row['control'] == 'atomic_exit_consumed_continuation' and
         all(row['continuation_id'] == 0 for row in (resume, exit_row)) and
         resume['executor_state'] == 2 and exit_row['executor_state'] == 1 and
         resume['write_epoch'] > handoff['write_epoch'] and exit_row['write_epoch'] == resume['write_epoch']
         and all(row[key] == handoff[key] for row in (resume, exit_row) for key in identity),
         'memory_atomic_committed_state')
    need(resume['lifecycle'] == 3 and resume['protection'] == 2 and
         exit_row['lifecycle'] == 3 and not exit_row['protection'], 'memory_atomic_committed_protection')
    positions = {id(row): index for index, row in enumerate(calls)}
    negatives = [row for row in selected if row['control'] in list(REFUSALS)[:9]]
    need(len(negatives) == 9, 'memory_atomic_negative_count')
    for negative, poll in zip(negatives, tail[:9]):
        need(positions[id(poll)] == positions[id(negative)] + 1, 'memory_atomic_refusal_pin_pair')
    retry = next(row for row in selected if row['control'] == 'atomic_original_epoch_requires_retry')
    duplicate = next(row for row in selected if row['control'] == 'atomic_consumed_continuation_cannot_repeat')
    need(positions[id(resume)] == positions[id(retry)] + 1 and
         positions[id(duplicate)] == positions[id(resume)] + 1 and
         positions[id(exit_row)] == positions[id(duplicate)] + 1, 'memory_atomic_commit_order')
    return {'actual_owner_operations': len(selected), 'precommit_refusals': 11,
            'committed_resumes': 1, 'source_lifetime_qualified': False,
            'fex_initialization': False}
