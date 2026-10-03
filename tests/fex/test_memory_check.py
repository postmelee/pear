"""Original pure build/admission/output controls; no native tool or code execution."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.fex import memory_check as checks, memory_run as runner
from tools.fex.common import Error

NONCE = '0123456789abcdef0123456789abcdef'
CHILD = SimpleNamespace(identity={'pid': 17, 'ppid': 19, 'start_sec': 23, 'start_usec': 29})


def ready():
    return dict(version=1, record_kind='pear_fex_memory_admission', event='ready',
        pid=17, parent_pid=19, start_seconds=23, start_microseconds=29, nonce=NONCE,
        user_page=4096, vm_page=4096, kernel_page=16384, translation_result=0,
        translation_errno=0, translation_value=0, translation_size=4, user_page_errno=0,
        kernel_page_result=0, host_port_release_result=0, cpu_type=0x100000c, jit_supported=1,
        geometry_accepted=True, restricted_operations_started=False, checked_ec=False,
        wine_view_registration=False)


def helper():
    return dict(version=1, record_kind='pear_bootstrap_helper', pid=17, ppid=19,
        start_sec=23, start_usec=29, cpu_type=0x100000c, translation_value=0, query_errno=0,
        user_page=16384, vm_page=16384, kernel_page=16384, kernel_error=0)


def owner_row(control, opcode=6, status=0):
    value = dict(version=1, record_kind='pear_fex_memory_fixture', scope='native_owner',
        sequence=1, event='owner_call', control=control, opcode=opcode, returned_status=status,
        status=status, requested_state=0, operation_offset='0000000000000000',
        operation_size='0000000000000000', allocation_id=0, generation=0, extent_offset=0,
        extent_size=0, write_epoch=0, executor_id=0, continuation_id=0, executor_state=0,
        lifecycle=0, protection=0, capabilities=0, native_error_domain=0, native_error_code=0)
    return value


def native_rows():
    """Structural transcript fixture only; counters never establish host admission."""
    rows = [helper(), ready(), dict(version=1, record_kind='pear_fex_memory_admission',
        event='initialize', status=0, native_error_domain=0, native_error_code=0,
        checked_ec=False, wine_view_registration=False)]
    groups = {'register_actual_native_executor': (1, 7), 'reserve_extent': (103, 1),
        'query_current_token': (103, 6), 'begin_two_page_write': (38, 2), 'publish_two_pages': (38, 3),
        'enter_owned_leaf': (73, 8), 'exit_to_native_gate': (73, 9), 'begin_cross_page_instruction_pair': (1, 2),
        'publish_cross_page_instruction_pair': (1, 3), 'enter_before_source_continuation': (1, 8),
        'pin_saved_source_resume': (1, 10), 'direct_owned_handoff_to_native': (1, 13),
        'poll_existing_owned_handoff': (1, 13),
        'admit_finite_saved_resume': (127, 10), 'discard_owned_saved_resume': (127, 11),
        'release_original_pin_epoch': (1, 11), 'begin_unpublished_abort_control': (1, 2),
        'abort_unpublished_window': (1, 4), 'retire_extent': (103, 5), 'unregister_actual_native_executor': (1, 12)}
    for control, (count, opcode) in groups.items():
        rows += [owner_row(control, opcode) for _ in range(count)]
    failures = {'version_mismatch': (6, 2), 'record_size_mismatch': (6, 1), 'unknown_opcode': (14, 1),
        'unknown_flags': (6, 1), 'reserved_word': (6, 1), 'reserved_word64': (6, 1), 'foreign_owner': (6, 6),
        'stale_generation': (6, 6), 'foreign_allocation': (6, 6), 'offset_alias': (6, 6), 'extent_alias': (6, 6),
        'unselected_role': (6, 1), 'native_fixture_cannot_select_arm64ec_role': (7, 3),
        'wrapped_write_range': (2, 1), 'source_guard_write': (2, 1), 'empty_write': (2, 1),
        'ordinary_exit_cannot_drop_saved_resume': (9, 1), 'nested_handoff_refused': (13, 1),
        'poll_requires_original_pin_epoch': (13, 1), 'poll_requires_exact_resume_offset': (13, 1),
        'poll_requires_existing_continuation': (13, 1),
        'unregister_cannot_drop_saved_resume': (12, 1), 'retirement_keeps_saved_generation': (5, 3),
        'continuation_capacity_preserves_old_pins': (10, 4), 'new_epoch_cannot_release_original_pin': (11, 1),
        'duplicate_retirement': (5, 6), 'shared_capacity_exhausted': (1, 4),
        'fragmented_free_bytes_refused': (1, 4), 'dispatcher_capacity_exhausted': (1, 4)}
    rows += [owner_row(c, op, status) for c, (op, status) in failures.items()]
    rows += [owner_row('mixed_extent_query_unavailable', 6, 3) for _ in range(111)]
    for index, row in enumerate(rows[3:], 1): row['sequence'] = index
    calls = len(rows) - 3
    rows += [dict(version=1, record_kind='pear_fex_memory_fixture', scope='native_owner', sequence=calls+1,
        event='suite_complete', passed=True, checked_ec=False, owner_calls=calls, refusals=140,
        allocations=103, retirements=103, publications=39, owned_code_calls=73,
        protection_observations=81, patch_rounds=32, fragmentation_controls=1, continuation_controls=1,
        fex_initialization=False, translated_guest_execution=False, game_execution=False),
        dict(version=1, record_kind='pear_fex_memory_admission', event='finish', observed_regions=81,
        native_owned_code_execution=True, native_arm64_pe_execution=False, checked_ec=False,
        wine_view_registration=False, fex_initialization=False, translated_guest_execution=False,
        game_execution=False, exit_code=0)]
    return rows


def cooperative_rows():
    """Structural schedules; synthetic identities are never current host evidence."""
    rows = [helper(), ready()]
    setup = [('setup_register', 7), ('reserve_extent', 1), ('query_current_token', 6),
             ('begin_two_page_write', 2), ('publish_two_pages', 3), ('setup_unregister', 12)]
    rows += [owner_row(control, opcode) for control, opcode in setup]
    def event(actor, name):
        return dict(version=1, record_kind='pear_fex_memory_cooperative', sequence=1,
                    event=name, actor=actor, native_error_code=0)
    def call(actor, control, opcode, state, status=0):
        return dict(version=1, record_kind='pear_fex_memory_cooperative', sequence=1,
            event='owner_call', actor=actor, control=control, opcode=opcode,
            returned_status=status, status=status, executor_id=0 if status else actor+1,
            continuation_id=0, executor_state=state, write_epoch=0,
            native_error_domain=0, native_error_code=0)
    for actor in range(4):
        rows += [event(actor, 'thread_create'), call(actor, 'register_owned_worker', 7, 1)]
    for phase in range(32):
        for actor in range(3):
            rows.append(call(actor, 'enter_source_leaf', 8, 2))
        rows.append(call(3, ('active_participant_timeout' if phase == 0 else
            'native_pin_without_park_timeout' if phase == 1 else 'cooperative_writer_admission'),
            2, 0 if phase < 2 else 1, 5 if phase < 2 else 0))
        for actor in range(3):
            rows.append(call(actor, 'handoff_to_compiled_native_gate', 13, 3))
        if phase >= 2: rows.append(call(3, 'publish_after_native_park_ack', 3, 1))
        for actor in range(3):
            rows.append(call(actor, 'poll_existing_source_descriptor', 13, 3))
            rows.append(call(actor, 'discard_saved_resume_original_epoch', 11, 1))
    for actor in range(4):
        rows += [call(actor, 'unregister_owned_worker', 12, 5), event(actor, 'thread_join')]
    rows += [owner_row('cleanup_register_after_worker_join', 7),
        owner_row('mixed_extent_query_unavailable', 6, 3), owner_row('retire_extent', 5),
        owner_row('cleanup_unregister_after_retirement', 12)]
    rows.append(dict(version=1, record_kind='pear_fex_memory_cooperative', event='complete', sequence=1,
        passed=True, owned_workers=4, workers_joined=4, schedules=32, timeout_controls=2,
        writes=30, handoffs=96, owned_leaf_calls=96, wire_poll_calls=96, condition_cleanup=0, mutex_cleanup=0,
        trace_cleanup=0, checked_ec=False, wine_view_registration=False, fex_initialization=False,
        translated_guest_execution=False, game_execution=False))
    counts = Counter()
    for row in rows[2:]:
        counts[row['record_kind']] += 1; row['sequence'] = counts[row['record_kind']]
    return rows


class AdmissionAndResult(unittest.TestCase):
    def test_admission_binds_exact_current_identity_and_original_error_facts(self):
        runner.validate_ready(ready(), CHILD, NONCE)
        for key, value in [('pid', 18), ('parent_pid', 20), ('start_microseconds', 30),
            ('translation_value', 1), ('kernel_page_result', 5), ('host_port_release_result', 5),
            ('user_page_errno', 13), ('user_page', 16384), ('geometry_accepted', 1), ('version', True)]:
            row = ready(); row[key] = value
            with self.subTest(field=key), self.assertRaises(Error): runner.validate_ready(row, CHILD, NONCE)
        row = ready(); row['unreviewed_permission'] = True
        with self.assertRaises(Error): runner.validate_ready(row, CHILD, NONCE)

    def test_successful_structural_transcript_keeps_native_scope_and_128_pins(self):
        value = runner.validate_result(native_rows(), 'pear-fex-memory')
        self.assertEqual(value['terminal']['continuation_controls'], 1)
        self.assertEqual(value['owner_calls'], 936)
        self.assertEqual(value['controlled_refusals'], 140)

    def test_duplicate_or_missing_trace_sequence_never_passes(self):
        for change in ('duplicate', 'missing'):
            rows = native_rows(); rows[4]['sequence'] += -1 if change == 'duplicate' else 1
            with self.subTest(change=change), self.assertRaises(Error): runner.validate_result(rows, 'pear-fex-memory')

    def test_unknown_records_extra_fields_and_boolean_status_are_closed(self):
        mutations = [('record_kind', 'unrelated_native_result'), ('status', False),
                     ('native_error_domain', False), ('extra', 0), ('version', True)]
        for key, value in mutations:
            rows = native_rows(); rows[3][key] = value
            with self.subTest(field=key), self.assertRaises(Error): runner.validate_result(rows, 'pear-fex-memory')

    def test_native_error_codes_and_refusal_facts_cannot_be_hidden(self):
        for field, number in [('executor_id', 7), ('generation', 7), ('capabilities', 7),
                              ('native_error_code', 13)]:
            rows = native_rows(); row = next(r for r in rows if r.get('status') == 6); row[field] = number
            with self.subTest(field=field), self.assertRaises(Error): runner.validate_result(rows, 'pear-fex-memory')

    def test_uint64_malformed_range_is_lossless_hex_with_original_json_bound(self):
        rows = native_rows(); row = next(r for r in rows if r.get('control') == 'wrapped_write_range')
        row['operation_offset'] = 'ffffffffffffffff'
        runner.validate_result(rows, 'pear-fex-memory')
        for value in [2**64-1, 'FFFFFFFFFFFFFFFF', '0xffffffffffffffff', 'fff']:
            row['operation_offset'] = value
            with self.subTest(value=value), self.assertRaises(Error): runner.validate_result(rows, 'pear-fex-memory')

    def test_partial_pin_admission_or_generic_native_failure_does_not_qualify(self):
        for change in ('pin', 'failure', 'ec'):
            rows = native_rows()
            if change == 'pin': next(r for r in rows if r.get('control') == 'admit_finite_saved_resume')['opcode'] = 6
            elif change == 'failure':
                r = next(r for r in rows if r.get('control') == 'shared_capacity_exhausted'); r['status'] = r['returned_status'] = 7
                r['native_error_domain'] = 1; r['native_error_code'] = 13
            else: rows[-2]['checked_ec'] = True
            with self.subTest(change=change), self.assertRaises(Error): runner.validate_result(rows, 'pear-fex-memory')

    def test_terminals_are_not_reordered_or_relabelled(self):
        rows = native_rows(); rows[-1], rows[-2] = rows[-2], rows[-1]
        with self.assertRaises(Error): runner.validate_result(rows, 'pear-fex-memory')
        with self.assertRaises(Error): runner.validate_result(native_rows(), 'unknown-fixture')


class CooperativeResult(unittest.TestCase):
    def test_four_owned_workers_and_both_real_timeout_controls_are_required(self):
        result = runner.validate_result(cooperative_rows(), 'pear-fex-cooperative')
        self.assertEqual(result['owner_calls'], 464)
        self.assertEqual(result['controlled_refusals'], 3)
        self.assertEqual(result['terminal']['owned_workers'], 4)

    def test_join_failure_duplicate_actor_and_cleanup_errors_never_pass(self):
        for change in ('join_error', 'duplicate_actor', 'cleanup', 'boolean_count'):
            rows = cooperative_rows()
            if change == 'join_error':
                next(r for r in rows if r.get('event') == 'thread_join')['native_error_code'] = 22
            elif change == 'duplicate_actor':
                joined = [r for r in rows if r.get('event') == 'thread_join']; joined[-1]['actor'] = 0
            elif change == 'cleanup': rows[-1]['trace_cleanup'] = 16
            else: rows[-1]['timeout_controls'] = True
            with self.subTest(change=change), self.assertRaises(Error):
                runner.validate_result(rows, 'pear-fex-cooperative')

    def test_pinned_or_active_state_is_not_a_completed_native_park(self):
        for field, value in [('status', 0), ('executor_state', 3), ('actor', 2), ('opcode', 6)]:
            rows = cooperative_rows()
            row = next(r for r in rows if r.get('control') == 'native_pin_without_park_timeout')
            row[field] = value
            if field == 'status': row['returned_status'] = value
            with self.subTest(field=field), self.assertRaises(Error):
                runner.validate_result(rows, 'pear-fex-cooperative')

    def test_failed_cleanup_or_relabelled_opcode_cannot_count_as_retirement(self):
        for field, value in [('status', 3), ('opcode', 6)]:
            rows = cooperative_rows(); row = next(r for r in rows if r.get('control') == 'retire_extent')
            row[field] = value
            if field == 'status': row['returned_status'] = value
            with self.subTest(field=field), self.assertRaises(Error):
                runner.validate_result(rows, 'pear-fex-cooperative')


class BuildEnvelope(unittest.TestCase):
    def test_scope_and_boolean_versions_fail_before_any_byte_or_tool_read(self):
        base = dict(schema_version=1, record_kind='fex_memory_prototype_build', scope='finite_native_owner', passed=True,
                    **{key: False for key in checks.FALSE_SCOPE})
        controls = [dict(base, schema_version=True), dict(base, scope='game_runtime'), dict(base, checked_ec=True)]
        with tempfile.TemporaryDirectory() as directory:
            for row in controls:
                with self.subTest(record=row), patch.object(checks, 'operation_output', return_value=Path(directory)), \
                     patch.object(checks, 'load_json', return_value=row), \
                     patch.object(checks, 'sha256', side_effect=AssertionError('later byte read')):
                    with self.assertRaises(Error): checks.verify_build(directory)


if __name__ == '__main__': unittest.main()
