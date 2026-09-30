"""Synthetic native-arena evidence and failure cleanup; no restricted execution.

The accepted synthetic record set tests the parser contract only. Neither these
records nor their acceptance establish host, Wine, or game qualification.
"""
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

TOOLS = Path(__file__).resolve().parents[2] / 'tools/wine'
sys.path.insert(0, str(TOOLS))
import pe_arena_probe as arena
from common import Error

NONCE = 'a' * 32
IDENTITY = {'pid': 102, 'ppid': 101, 'start_sec': 1700000000, 'start_usec': 123400}
BINARY = {'name': 'pear-arena-unit', 'uuid': 'a'*32}


def prelude(mode='lifecycle', policy='thread-jit'):
    common = {'version': 1, 'record_kind': 'pear_pe_arena_probe', 'mode': mode, 'policy': policy}
    begin = {**common, 'event': 'begin', 'diagnostic_only': True, 'runtime_qualified': False,
             'single_threaded': True, 'mapping_bytes': 196608, 'interior_bytes': 131072,
             'slot_bytes': 65536, 'slot_capacity': 2, 'guest_page_bytes': 4096,
             'reuse_rounds': 4, 'private_vm_flags': False}
    identity = {**common, 'event': 'identity', 'pid': 102, 'parent_pid': 101,
                'start_seconds': 1700000000, 'start_microseconds': 123400, 'nonce': NONCE}
    geometry = {**common, 'event': 'geometry', 'user_page': 4096, 'user_errno': 0,
                'vm_page': 4096, 'kernel_page': 16384, 'kernel_result': 0, 'port_release_result': 0,
                'cpu_type': 0x100000c, 'translation_query_result': 0, 'translation_query_errno': 0,
                'translation_query_size': 4, 'translation_value': 0, 'accepted': True}
    ready = {**common, 'event': 'ready', 'nonce': NONCE,
             'restricted_operations_started': False, 'timeout_ms': 10000}
    return [begin, identity, geometry, ready]


def helper(kind='pear_bootstrap_helper'):
    return {'version': 1, 'record_kind': kind, **IDENTITY, 'cpu_type': 0x100000c,
            'translation_value': 0, 'query_errno': 0, 'user_page': 16384, 'vm_page': 16384,
            'kernel_page': 16384, 'kernel_error': 0}


def synthetic_trace(mode='lifecycle', policy='thread-jit'):
    # Use the declared operation contract to populate structurally valid rows;
    # independent mutations below remove or contradict actual observations.
    rows = prelude(mode, policy)
    for row in arena.expected_lifecycle(mode, policy):
        row = {'version': 1, 'record_kind': 'pear_pe_arena_probe', 'mode': mode, **row}
        if row['event'] == 'region': row['maximum_protection'] = 7
        if row['event'] == 'alignment': row['prefix_bytes'] = 4096
        if row['event'] == 'allocation': row['flags'] = 0x1802
        if row['event'] == 'fault_armed':
            pc = 0x101004 if mode == 'protected-write' else 0x200000
            row.update(expected_pc_min=pc, expected_pc_max=pc + 4,
                       expected_address_min=0x200000, expected_address_max=0x200004)
        rows.append(row)
    return rows


def fault_evidence(mode='protected-write', policy='thread-jit'):
    armed = synthetic_trace(mode, policy)[-1]
    code = -signal.SIGBUS
    result = {'mode': mode, 'policy': policy, 'processes': {'probe': {'identity': dict(IDENTITY), 'exit_code': code}}}
    birth = datetime.fromtimestamp(1700000000.1234, timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f %z')
    report = {'pid': 102, 'procLaunch': birth, 'procName': BINARY['name'],
              'procPath': '/Users/USER/*/ArenaProbe.app/Contents/MacOS/' + BINARY['name'],
              'cpuType': 'ARM-64', 'translated': False,
              'usedImages': [{'arch': 'arm64', 'uuid': 'a'*32, 'name': BINARY['name'],
                              'base': 0x100000, 'size': 0x10000}],
              'exception': {'type': 'EXC_BAD_ACCESS', 'signal': 'SIGBUS', 'rawCodes': [2, 0x200000]},
              'termination': {'namespace': 'SIGNAL', 'code': int(signal.SIGBUS)},
              'faultingThread': 0, 'threads': [{'threadState': {'flavor': 'ARM_THREAD_STATE64',
                  'pc': {'value': armed['expected_pc_min']}, 'far': {'value': 0x200000},
                  'esr': {'value': (0x24 << 26) | 0x40 if mode == 'protected-write' else (0x20 << 26)}}}]}
    return report, result, armed


class ProtocolTests(unittest.TestCase):
    def test_ready_requires_actual_child_identity_and_native_geometry(self):
        rows = [helper(), *prelude()]
        arena.validate_ready(rows, IDENTITY, NONCE, 'lifecycle', before_release=True)
        for row, field, value in [(2, 'pid', 103), (2, 'start_microseconds', 123401),
                                  (3, 'user_page', 16384), (3, 'translation_value', 1),
                                  (3, 'translation_query_errno', 2),
                                  (4, 'nonce', 'b'*32), (4, 'restricted_operations_started', True)]:
            altered = copy.deepcopy(rows); altered[row][field] = value
            with self.subTest(field=field), self.assertRaises(Error):
                arena.validate_ready(altered, IDENTITY, NONCE, 'lifecycle', before_release=True)

    def test_operation_or_duplicate_ready_before_go_is_rejected(self):
        rows = [helper(), *prelude()]
        for candidate in [rows + [rows[-1]], rows + [{'event': 'allocation'}],
                          [rows[0], rows[1], rows[3], rows[2], rows[4]]]:
            with self.subTest(candidate=candidate[-1]), self.assertRaises(Error):
                arena.validate_ready(candidate, IDENTITY, NONCE, 'lifecycle', before_release=True)

    def test_output_bounds_partial_and_duplicate_json_keys(self):
        self.assertEqual(arena.records(b'{"event":"ready"}\n{"event":', partial=True), [{'event': 'ready'}])
        for data in [b'{"event":', b'null\n', b'{"event":1,"event":2}\n', b'x' * (arena.base.STREAM_LIMIT + 2)]:
            with self.subTest(size=len(data)), self.assertRaises(Error): arena.records(data)

    def test_complete_lifecycle_and_paired_fault_preludes(self):
        for mode in arena.MODES:
            with self.subTest(mode=mode):
                rows = synthetic_trace(mode)
                arena.validate_ready([helper(), *rows], IDENTITY, NONCE, mode)
                arena.validate_lifecycle(rows, mode, 0 if mode == 'lifecycle' else -signal.SIGBUS)

    def test_summary_cannot_replace_operations_or_prove_cleanup(self):
        rows = synthetic_trace()
        subset = prelude() + [row for row in rows if row['event'] in ('lifecycle_summary', 'cleanup')]
        with self.assertRaises(Error): arena.validate_lifecycle(subset, 'lifecycle', 0)
        for event in ('leaf_return', 'mutator_return', 'rollback', 'all_retired', 'cleanup', 'result'):
            altered = copy.deepcopy(rows)
            altered.pop(next(i for i, row in enumerate(altered) if row['event'] == event))
            with self.subTest(event=event), self.assertRaises(Error): arena.validate_lifecycle(altered, 'lifecycle', 0)

    def test_observed_values_permissions_generations_and_cleanup_must_match(self):
        cases = [('leaf_return', 'matched', False), ('leaf_return', 'value', 999),
                 ('mutator_return', 'data_value', 0), ('mutator_return', 'sentinel_preserved', False),
                 ('publication', 'native_writer_closed', False), ('publication', 'cache_invalidated', False),
                 ('rollback', 'all_pages_inaccessible', False), ('reuse', 'generation', 2),
                 ('reuse', 'peer_generation_preserved', False), ('slot_protections', 'pages_checked', 1),
                 ('allocation_rejected', 'request_submitted', False),
                 ('allocation_rejected', 'slot_metadata_preserved', False),
                 ('retirement', 'active_leases', 1), ('region', 'current_protection', 3),
                 ('all_retired', 'retirements', 4), ('cleanup', 'result', -1),
                 ('cleanup', 'original_mapping_bytes', 65536), ('result', 'exit_code', 70)]
        for event, key, value in cases:
            rows = synthetic_trace(); next(row for row in rows if row['event'] == event)[key] = value
            with self.subTest(event=event, field=key), self.assertRaises(Error):
                arena.validate_lifecycle(rows, 'lifecycle', 0)

    def test_fault_is_not_allowed_before_retirement_or_with_broad_ranges(self):
        for key, value in [('state', 'published'), ('lifecycle_passed', False),
                           ('control', 'protected-write'), ('access', 'write'),
                           ('expected_pc_max', 0x210000), ('writer_mode_requested_next', True)]:
            rows = synthetic_trace('retired-call'); rows[-1][key] = value
            with self.subTest(key=key), self.assertRaises(Error):
                arena.validate_lifecycle(rows, 'retired-call', -signal.SIGBUS)
        rows = synthetic_trace('retired-call')
        rows.pop(-2)
        with self.assertRaises(Error): arena.validate_lifecycle(rows, 'retired-call', -signal.SIGBUS)


class PolicyBindingTests(unittest.TestCase):
    def test_both_policies_have_separate_valid_native_protocols(self):
        for policy, modes in arena.POLICIES.items():
            for mode in modes:
                with self.subTest(policy=policy, mode=mode):
                    rows = synthetic_trace(mode, policy)
                    arena.validate_ready([helper(), *rows], IDENTITY, NONCE, mode, policy=policy)
                    arena.validate_lifecycle(rows, mode, 0 if mode == 'lifecycle' else -signal.SIGBUS,
                                             policy=policy)

    def test_records_from_other_policy_cannot_release_or_pass(self):
        for selected, other in (('thread-jit', 'page-wx'), ('page-wx', 'thread-jit')):
            rows = synthetic_trace('lifecycle', other)
            with self.subTest(selected=selected), self.assertRaises(Error):
                arena.validate_ready([helper(), *rows[:4]], IDENTITY, NONCE, 'lifecycle',
                                     before_release=True, policy=selected)
            with self.assertRaises(Error): arena.validate_lifecycle(rows, 'lifecycle', 0, policy=selected)
            rows = synthetic_trace('lifecycle', selected)
            next(row for row in rows if row['event'] == 'publication')['policy'] = other
            with self.assertRaises(Error): arena.validate_lifecycle(rows, 'lifecycle', 0, policy=selected)

    def test_preparation_exec_and_thread_writer_exec_are_not_interchangeable(self):
        for policy, mode in [('thread-jit', 'preparation-exec'), ('page-wx', 'writer-exec')]:
            with self.subTest(policy=policy), self.assertRaises(Error): arena.expected_lifecycle(mode, policy)
            with self.assertRaises(Error): arena.validate_policy(policy, mode)
        with self.assertRaises(Error): arena.validate_policy('unknown')

    def test_page_policy_requires_actual_rw_preparation_and_rx_publication(self):
        for event, field, value in [('code_write_ready', 'code_protection', 7),
                                    ('publication', 'code_protection', 7),
                                    ('publication', 'pthread_jit_toggle_used', True)]:
            rows = synthetic_trace('lifecycle', 'page-wx')
            next(row for row in rows if row['event'] == event)[field] = value
            with self.subTest(event=event, field=field), self.assertRaises(Error):
                arena.validate_lifecycle(rows, 'lifecycle', 0, policy='page-wx')

    def test_preparation_exec_requires_new_generation_rw_target_and_executable_peer(self):
        for event, field, value in [('preparation_fault_ready', 'target_protection', 7),
                                    ('preparation_fault_ready', 'target_pages_checked', 1),
                                    ('preparation_fault_ready', 'peer_leaf_value', 0),
                                    ('preparation_fault_ready', 'peer_lease_released', False),
                                    ('preparation_fault_ready', 'published', True),
                                    ('fault_armed', 'generation', 6),
                                    ('fault_armed', 'state', 'published'),
                                    ('fault_armed', 'writer_mode_requested_next', True)]:
            rows = synthetic_trace('preparation-exec', 'page-wx')
            next(row for row in rows if row['event'] == event)[field] = value
            with self.subTest(event=event, field=field), self.assertRaises(Error):
                arena.validate_lifecycle(rows, 'preparation-exec', -signal.SIGBUS, policy='page-wx')
        report, result, armed = fault_evidence('preparation-exec', 'page-wx')
        self.assertTrue(arena.crash_matches(report, result, armed, BINARY)['matched'])
        report['threads'][0]['threadState']['pc']['value'] += 4
        with self.assertRaises(Error): arena.crash_matches(report, result, armed, BINARY)

    def test_crash_policy_must_match_the_armed_operation(self):
        report, result, armed = fault_evidence('data-exec', 'page-wx')
        self.assertTrue(arena.crash_matches(report, result, armed, BINARY)['matched'])
        armed['policy'] = 'thread-jit'
        with self.assertRaises(Error): arena.crash_matches(report, result, armed, BINARY)

    def test_page_policy_query_and_peer_failure_have_precise_diagnostics(self):
        for phase in ('code_write_page', 'preparation_fault_page'):
            row = {'version': 1, 'record_kind': 'pear_pe_arena_probe', 'mode': 'preparation-exec',
                   'policy': 'page-wx', 'event': 'region', 'phase': phase, 'accepted': False,
                   'mach_result': 0, 'port_release_result': 0, 'requested_bytes': 4096,
                   'current_protection': 7, 'maximum_protection': 7, 'expected_protection': 3}
            failure = arena.first_native_failure([row], 'preparation-exec', 'page-wx')
            self.assertEqual((failure['operation'], failure['phase']), ('mach_vm_region', phase))
        rows = synthetic_trace('preparation-exec', 'page-wx')
        row = next(row for row in rows if row['event'] == 'preparation_fault_ready')
        row.update(accepted=False, peer_leaf_matched=False, peer_leaf_value=0)
        failure = arena.first_native_failure(rows, 'preparation-exec', 'page-wx')
        self.assertEqual((failure['operation'], failure['peer_leaf_value']), ('fixed_code_return', 0))

    def test_failure_from_other_policy_is_not_named_as_selected_policy(self):
        row = {'version': 1, 'record_kind': 'pear_pe_arena_probe', 'mode': 'lifecycle',
               'policy': 'thread-jit', 'event': 'protection_failure', 'slot': 0, 'generation': 2,
               'page': 0, 'state': 'published', 'protection': 0, 'result': -1, 'errno': 13}
        self.assertIsNone(arena.first_native_failure([row], 'lifecycle', 'page-wx'))
        self.assertEqual(arena.first_native_failure([row], 'lifecycle', 'thread-jit')['policy'], 'thread-jit')


class FailureExplanationTests(unittest.TestCase):
    def failure(self, **changes):
        return {'version': 1, 'record_kind': 'pear_pe_arena_probe', 'mode': 'lifecycle', 'policy': 'thread-jit',
                'event': 'protection_failure', 'slot': 0, 'generation': 0, 'page': 0,
                'state': 'reserved', 'protection': 0, 'result': -1, 'errno': 13, **changes}

    def test_first_native_error_is_preserved_before_cleanup_or_fixture_exit(self):
        rows = prelude() + [self.failure(), {'version': 1, 'record_kind': 'pear_pe_arena_probe',
            'mode': 'lifecycle', 'policy': 'thread-jit', 'event': 'cleanup', 'original_mapping_bytes': 196608,
            'result': -1, 'errno': 22, 'prior_exit_code': 66},
            {'version': 1, 'record_kind': 'pear_pe_arena_probe', 'mode': 'lifecycle', 'policy': 'thread-jit',
             'event': 'result', 'passed': False, 'exit_code': 66}]
        failure = arena.first_native_failure(rows, 'lifecycle')
        self.assertEqual(failure, {'record_index': 4, 'event': 'protection_failure',
            'operation': 'mprotect', 'policy': 'thread-jit', 'slot': 0, 'generation': 0, 'page': 0,
            'state': 'reserved', 'protection': 0, 'result': -1, 'errno': 13, 'errno_name': 'EACCES'})
        with self.assertRaises(Error): arena.validate_lifecycle(rows, 'lifecycle', 66)

    def test_expected_rollback_and_admission_rejections_are_not_failures(self):
        self.assertIsNone(arena.first_native_failure(synthetic_trace(), 'lifecycle'))
        for mode in arena.MODES[1:]:
            self.assertIsNone(arena.first_native_failure(synthetic_trace(mode), mode))

    def test_only_allowlisted_fields_from_scoped_well_typed_failures_are_exposed(self):
        row = self.failure(pid=999, path='/private/fixture', expected_pc_min=123)
        observed = arena.first_native_failure([row], 'lifecycle')
        self.assertFalse({'pid', 'path', 'expected_pc_min'} & observed.keys())
        for changes in ({'errno': True}, {'errno': '13'}, {'state': '/private/data'},
                        {'page': 16}, {'mode': 'other'}, {'version': True},
                        {'record_kind': 'untrusted'}, {'result': 0}, {'event': []}, {'event': 'unknown'}):
            with self.subTest(changes=changes):
                self.assertIsNone(arena.first_native_failure([self.failure(**changes)], 'lifecycle'))

    def test_failed_cleanup_is_reported_when_it_is_the_first_failure(self):
        rows = synthetic_trace()
        cleanup = next(row for row in rows if row['event'] == 'cleanup')
        cleanup.update(result=-1, errno=22)
        failure = arena.first_native_failure(rows, 'lifecycle')
        self.assertEqual((failure['operation'], failure['errno_name']), ('munmap', 'EINVAL'))
        with self.assertRaises(Error): arena.validate_lifecycle(rows, 'lifecycle', 70)

    def test_initial_none_does_not_remove_actual_retirement_protection_gate(self):
        rows = synthetic_trace('retired-call')
        region = next(row for row in rows if row['event'] == 'region')
        self.assertEqual(region['expected_protection'], 0)
        retire_protection = rows[-3]
        self.assertEqual(retire_protection['event'], 'slot_protections')
        retire_protection['published'] = True
        with self.assertRaises(Error): arena.validate_lifecycle(rows, 'retired-call', -signal.SIGBUS)


class CrashBindingTests(unittest.TestCase):
    def test_exact_owned_write_and_instruction_faults(self):
        for mode in arena.MODES[1:]:
            with self.subTest(mode=mode):
                report, result, armed = fault_evidence(mode)
                self.assertTrue(arena.crash_matches(report, result, armed, BINARY)['matched'])

    def test_other_pid_generation_image_architecture_and_codesigning_are_not_controls(self):
        changes = [('pid', 103), ('procLaunch', '2023-11-14 22:13:21.123400 +0000'),
                   ('procName', 'other'), ('translated', True), ('cpuType', 'X86-64')]
        for key, value in changes:
            report, result, armed = fault_evidence(); report[key] = value
            with self.subTest(key=key), self.assertRaises(Error): arena.crash_matches(report, result, armed, BINARY)
        for alteration in ('uuid', 'codesigning', 'outside-image'):
            report, result, armed = fault_evidence()
            if alteration == 'uuid': report['usedImages'][0]['uuid'] = 'b'*32
            if alteration == 'codesigning':
                report['termination'] = {'namespace': 'CODESIGNING', 'code': 2}
                result['processes']['probe']['exit_code'] = -signal.SIGKILL
            if alteration == 'outside-image': report['usedImages'][0]['size'] = 16
            with self.subTest(alteration=alteration), self.assertRaises(Error):
                arena.crash_matches(report, result, armed, BINARY)

    def test_same_signal_wrong_pc_address_or_read_access_fails(self):
        for field, value in [('pc', 0x101008), ('far', 0x200004), ('esr', 0x24 << 26)]:
            report, result, armed = fault_evidence(); report['threads'][0]['threadState'][field]['value'] = value
            with self.subTest(field=field), self.assertRaises(Error): arena.crash_matches(report, result, armed, BINARY)
        report, result, armed = fault_evidence('writer-exec')
        report['threads'][0]['threadState']['esr']['value'] = (0x24 << 26) | 0x40
        with self.assertRaises(Error): arena.crash_matches(report, result, armed, BINARY)

    def test_crash_missing_registers_or_trailing_content_is_rejected(self):
        report, result, armed = fault_evidence()
        del report['threads'][0]['threadState']['far']
        with self.assertRaises(Error): arena.crash_matches(report, result, armed, BINARY)
        encoded = b'{}\n' + json.dumps(report).encode()
        self.assertEqual(arena.parse_crash(encoded), report)
        with self.assertRaises(Error): arena.parse_crash(encoded + b'{}')

    def test_owned_unexpected_crash_is_retained_as_failed_evidence(self):
        report, result, armed = fault_evidence(); report['threads'][0]['threadState']['pc']['value'] += 4
        result['observations'] = [armed]
        data = b'{}\n' + json.dumps(report).encode()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary); crash = directory / 'reports'; crash.mkdir()
            (crash / (BINARY['name'] + '-sample.ips')).write_bytes(data)
            actual = arena.collect_crash(result, BINARY, directory, crash_directory=crash)
            self.assertFalse(actual['matched'])
            self.assertEqual(actual['error'], 'arena_crash_pc_mismatch')
            self.assertEqual((directory / 'crash.ips').read_bytes(), data)


class ProvenanceAndCompilerTests(unittest.TestCase):
    def test_source_snapshot_rejects_live_or_retained_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / 'source'; source.mkdir()
            output = root / 'output'; output.mkdir()
            (source / 'fixture.c').write_text('int owned_fixture;\n')
            with patch.object(arena, 'REPO', source), patch.object(arena, 'PRODUCER_FILES', ()), \
                 patch.object(arena, 'SOURCE_FILES', ('fixture.c',)), patch.object(arena, 'LOCK_FILE', 'lock.json'):
                (source / 'lock.json').write_text('{}\n')
                inputs = arena.snapshot_inputs(output)
                arena.validate_inputs(output, inputs)
                (source / 'fixture.c').write_text('changed\n')
                with self.assertRaises(Error): arena.validate_inputs(output, inputs)
                (source / 'fixture.c').write_text('int owned_fixture;\n')
                (output / 'inputs/fixture.c').write_text('changed\n')
                with self.assertRaises(Error): arena.validate_inputs(output, inputs)

    def test_compiler_setup_interruption_kills_and_reaps_retained_group(self):
        for interruption in (KeyboardInterrupt(), SystemExit(4), RuntimeError('selector failed')):
            selector = Mock(); selector.register.side_effect = interruption
            process = Mock(pid=321, returncode=None)
            def waited(timeout): process.returncode = -signal.SIGKILL; return process.returncode
            process.wait.side_effect = waited
            events = []
            with tempfile.TemporaryDirectory() as temporary, \
                 patch.object(arena.selectors, 'DefaultSelector', return_value=selector), \
                 patch.object(arena.subprocess, 'Popen', return_value=process), \
                 patch.object(arena.os, 'set_blocking'), patch.object(arena.os, 'killpg') as kill:
                with self.assertRaises(type(interruption)):
                    arena.compile_native(['/pinned/clang', 'fixture.c'], Path(temporary), 'compile.test', events)
                kill.assert_called_once_with(321, signal.SIGKILL)
                process.wait.assert_called_once_with(timeout=5)
                process.stdout.close.assert_called_once(); process.stderr.close.assert_called_once()
                self.assertIsNotNone(events[0]['failure'])
                self.assertEqual(events[0]['exit_code'], -signal.SIGKILL)
                self.assertTrue((Path(temporary) / 'compile.test.stdout.log').is_file())

    def test_compile_failure_cannot_become_a_passed_prerequisite(self):
        with tempfile.TemporaryDirectory() as temporary, \
             patch.object(arena.base, 'create_output', return_value=Path(temporary)), \
             patch.object(arena, 'snapshot_inputs', return_value={}), \
             patch.object(arena, 'validate_inputs'), \
             patch.object(arena, 'prepare_binaries', side_effect=Error('arena_compile_failed')):
            result = arena.run('/unused/local-input.json', temporary, True)
            self.assertEqual(result['error'], 'arena_compile_failed')
            self.assertFalse(result['native_prerequisite_passed'])
            self.assertFalse(result['runtime_qualified'])
            self.assertEqual(result['cases'], [])
            self.assertTrue((Path(temporary) / 'report.json').is_file())


class CleanupTests(unittest.TestCase):
    def test_baseexception_cleanup_attempts_emergency_reap_without_claiming_success(self):
        child = SimpleNamespace(reaped=False)
        for fault in (KeyboardInterrupt(), SystemExit(9), RuntimeError('observer failed')):
            session = SimpleNamespace(children={'probe': child}, cleanup=Mock(side_effect=fault),
                observer=SimpleNamespace(signal_owned=Mock(side_effect=RuntimeError())),
                emergency_reap=Mock(return_value={'reaped': True}))
            result = arena.cleanup_role(session, 'probe')
            self.assertFalse(result['complete'])
            session.emergency_reap.assert_called_once_with(child)

    def test_incomplete_normal_cleanup_also_gets_terminal_fallback(self):
        child = SimpleNamespace(reaped=False)
        session = SimpleNamespace(children={'probe': child}, cleanup=Mock(return_value={'complete': False}),
            observer=SimpleNamespace(signal_owned=Mock()), emergency_reap=Mock(return_value={'reaped': True}))
        self.assertFalse(arena.cleanup_role(session, 'probe')['complete'])
        session.emergency_reap.assert_called_once_with(child)

    def test_probe_cleanup_failure_does_not_skip_sentinel_or_logs(self):
        calls = []
        session = SimpleNamespace(children={}, cleanup=lambda roles, bounds: calls.append(roles[0]) or {'complete': False},
                                  finish_logs=Mock(return_value=[]))
        result = arena.finish_session(session, None)
        self.assertEqual(calls, ['probe', 'sentinel'])
        self.assertFalse(result[2]); session.finish_logs.assert_called_once()

    def test_interruption_during_launch_preserves_report_and_cleanup(self):
        calls = []
        class Session:
            def __init__(self, output): self.children = {}; self.streams = {}; self.failure = None
            def launch(self, *args, **kwargs): raise KeyboardInterrupt()
            def cleanup(self, roles, bounds): calls.append(roles[0]); return {'complete': True}
            def finish_logs(self, duration): return []
        with tempfile.TemporaryDirectory() as temporary:
            result = arena.run_case('allow-jit', 'lifecycle', {'path': '/unused'},
                {'sentinel': '/unused', 'helper': '/unused'}, Path(temporary) / 'case', session_factory=Session)
            self.assertEqual(result['outcome'], 'interrupted')
            self.assertFalse(result['passed']); self.assertFalse(result['wine_execution'])
            self.assertEqual(calls, ['probe', 'sentinel'])
            self.assertTrue((Path(temporary) / 'case/case.json').is_file())

    def test_sentinel_failure_and_owned_fork_prevent_acceptance(self):
        rows = [helper('pear_sentinel_ready'), {'version': 1, 'record_kind': 'pear_sentinel_done', 'signal': 0, 'command': 81}]
        raw = {('sentinel', 'stdout'): b''.join(json.dumps(row).encode()+b'\n' for row in rows),
               ('sentinel', 'stderr'): b'', ('probe', 'stderr'): b''}
        result = {'outcome': 'exited', 'error': None, 'stream_error': None,
                  'cleanup': {'complete': True}, 'sentinel_cleanup': {'complete': True}, 'sentinel_survived': True,
                  'processes': {role: {'identity': IDENTITY, 'reaped': True, 'fork_seen': False, 'exit_code': 0}
                                for role in ('sentinel', 'probe')}}
        arena.validate_supervision(result, raw)
        for bad in ('fork', 'sentinel', 'cleanup'):
            actual = copy.deepcopy(result)
            if bad == 'fork': actual['processes']['probe']['fork_seen'] = True
            elif bad == 'sentinel': actual['sentinel_survived'] = False
            else: actual['cleanup']['complete'] = False
            with self.subTest(bad=bad), self.assertRaises(Error): arena.validate_supervision(actual, raw)


if __name__ == '__main__':
    unittest.main()
