"""Synthetic protocol/evidence rejection and ordinary owned-process cleanup.

These tests never execute Wine, Windows PE, a page-mode setter, guest x18 or a
restricted operation under fake authorization. Only the actual runtime suite
can produce the Stage 3 execution evidence.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import struct
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[2] / 'tools/wine'
sys.path.insert(0, str(TOOLS))
import api_runner as api
import run_fixtures as base
from common import Error, encoded

NONCE = 'a' * 32
jsonl = lambda row: json.dumps(row, ensure_ascii=False).encode() + b'\n'


def hello_fixture(kind='loader'):
    identity = {'pid': 102, 'ppid': 101, 'start_sec': 1000, 'start_usec': 20}
    root = SimpleNamespace(pid=102, identity=identity)
    hello = {'version': 1, 'kind': kind, 'nonce': NONCE, **identity, 'pgid': 102,
             'cpu_type': base.MACH_ARM64, 'translation_value': 0, 'translation_error': 0,
             'user_page': 4096, 'vm_page': 4096, 'kernel_page': 16384, 'kernel_error': 0}
    return hello, root


def helper_record():
    hello, root = hello_fixture()
    return {'version': 1, 'record_kind': 'pear_bootstrap_helper', **root.identity,
            'cpu_type': base.MACH_ARM64, 'translation_value': 0, 'query_errno': 0,
            'user_page': 16384, 'vm_page': 16384, 'kernel_page': 16384, 'kernel_error': 0}, root


def lifetime_fixture():
    return [{'version': 1, 'record_kind': 'pear_lifetime_event', 'round': index, 'event': event,
             'module_base': 0x20010000, 'callback_address': 0x20011000}
            for index in range(32) for event in ('loaded', 'retired')]


def relocation_fixture():
    rows, values = [], [0x13579bdf, 0x13579bdf]
    for round in range(2):
        for copy in range(2):
            address = 0x20010000 + copy * 65536
            desired = (0x10203040 if round == 0 else 0x50607080) + copy
            rows.append({'version': 1, 'record_kind': 'pear_relocation_event', 'event': 'probe',
                         'copy': copy, 'round': round, 'module_base': address, 'status': 0,
                         'code_slot': address + 0x4008, 'code_pointer': address + 0x1000,
                         'code_address': address + 0x1000, 'data_slot': address + 0x4010,
                         'data_pointer': address + 0x4000, 'data_address': address + 0x4000,
                         'security_cookie_address': address + 0x4020,
                         'security_cookie': 0x1abcdef01234 + copy,
                         'before': values[copy], 'after': desired,
                         'call_result': desired ^ 0xa5c31f27, 'peer_value': values[1 - copy]})
            values[copy] = desired
    return rows + [{'version': 1, 'record_kind': 'pear_relocation_event', 'event': 'retired',
                    'copy': copy, 'module_base': 0x20010000 + copy * 65536} for copy in range(2)]


def fixture_stdout(helper, kind):
    private = [*relocation_fixture(), *api.IMPORT_EXPECTED, *lifetime_fixture()] if kind == 'abi' else []
    return b''.join(jsonl(row) for row in [helper, *private, *api.expected_fixture_rows(kind)])


class RegistrationTests(unittest.TestCase):
    def check(self, hello, root, registered=None, peer=None, actual=None, executable='/signed/wine'):
        return api.validate_registration(hello, peer or hello['pid'], actual or {
            key: hello[key] for key in ('pid', 'ppid', 'start_sec', 'start_usec')}, root,
            registered or {}, executable, '/signed/wine', NONCE)

    def test_authenticated_root_native_registration(self):
        hello, root = hello_fixture()
        self.check(hello, root)

    def test_authenticated_fork_requires_registered_live_parent(self):
        hello, root = hello_fixture('fork')
        hello.update(pid=103, ppid=102, start_usec=21)
        self.check(hello, root, {102: {'exited': False}})
        for ledger in ({}, {102: {'exited': True}}, {101: {'exited': False}}):
            with self.subTest(ledger=ledger), self.assertRaises(Error):
                self.check(hello, root, ledger)

    def test_peer_pid_and_birth_identity_are_independent(self):
        hello, root = hello_fixture()
        for peer, actual in [(103, root.identity), (102, {**root.identity, 'start_usec': 21}),
                             (102, {**root.identity, 'ppid': 99})]:
            with self.subTest(peer=peer, actual=actual), self.assertRaises(Error):
                self.check(hello, root, peer=peer, actual=actual)

    def test_native_translation_query_and_geometry_required(self):
        for key, value in [('cpu_type', 0x1000007), ('translation_value', 1), ('translation_error', 1),
                           ('translation_error', False), ('user_page', 16384), ('kernel_page', 4096)]:
            hello, root = hello_fixture()
            hello[key] = value
            with self.subTest(key=key), self.assertRaises(Error):
                self.check(hello, root)

    def test_group_escape_unapproved_exec_nonce_and_duplicate_fail(self):
        for key, value in [('pgid', 999), ('nonce', 'b'*32), ('kind', 'unowned'), ('pid', True)]:
            hello, root = hello_fixture()
            hello[key] = value
            with self.subTest(key=key), self.assertRaises(Error):
                self.check(hello, root)
        hello, root = hello_fixture()
        with self.assertRaises(Error):
            self.check(hello, root, executable='/other/wine')
        with self.assertRaises(Error):
            self.check(hello, root, {102: {'exited': False}})

    def test_more_than_finite_process_budget_fails(self):
        hello, root = hello_fixture('fork')
        hello.update(pid=500, ppid=102)
        with self.assertRaises(Error):
            self.check(hello, root, {n: {'exited': False} for n in range(100, 100 + api.MAX_PROCESSES)})


class FixtureResultTests(unittest.TestCase):
    def test_exact_api_and_abi_observations(self):
        helper, loader = helper_record()
        for kind in ('api', 'abi'):
            rows = api.expected_fixture_rows(kind)
            raw = fixture_stdout(helper, kind)
            self.assertEqual(api.fixture_output(raw, kind, loader), rows)

    def test_missing_child_wrong_exit_and_incorrect_digest_fail(self):
        helper, loader = helper_record()
        for mode in ('missing-child', 'exit', 'digest', 'extra'):
            rows = copy.deepcopy(api.expected_api_rows())
            if mode == 'missing-child': rows.pop(1)
            elif mode == 'exit': rows[2]['child_exit'] = 0
            elif mode == 'digest': rows[2]['fnv1a64'] = '0'*16
            else: rows.append(copy.deepcopy(rows[0]))
            with self.subTest(mode=mode), self.assertRaises(Error):
                api.fixture_output(b''.join(jsonl(row) for row in [helper, *rows]), 'api', loader)

    def test_nested_counts_register_and_real_status_results_required(self):
        helper, loader = helper_record()
        for key, value in [('callbacks', 31), ('gateway_calls', 64), ('native_calls', 0),
                           ('host_checks', 0), ('frame_checks', 0), ('register_failure_mask', 1),
                           ('inactive_callback_status', 0), ('error_returns', 0), ('error_step', False)]:
            row = {**api.ABI_EXPECTED, key: value}
            with self.subTest(key=key), self.assertRaises(Error):
                api.fixture_output(b''.join(jsonl(item) for item in
                    [helper, *relocation_fixture(), *api.IMPORT_EXPECTED, *lifetime_fixture(),
                     api.RELOCATION_EXPECTED, api.LIFETIME_EXPECTED, row]), 'abi', loader)

    def test_supported_architecture_requires_exact_typed_observations(self):
        helper, loader = helper_record()
        for field, value in [('status', False), ('returned_bytes', 8.0), ('machines', [43620.0]),
                             ('flags', [7.0]), ('terminator', False), ('machines', [43620, 332]),
                             ('flags', [3]), ('returned_bytes', 12), ('terminator', 1)]:
            rows = copy.deepcopy(api.expected_api_rows())
            rows[0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(Error):
                api.fixture_output(b''.join(jsonl(row) for row in [helper, *rows]), 'api', loader)

    def test_helper_translated_or_missing_result_fails(self):
        helper, loader = helper_record()
        helper['translation_value'] = 1
        with self.assertRaises(Error):
            api.fixture_output(jsonl(helper) + jsonl(api.ABI_EXPECTED), 'abi', loader)
        with self.assertRaises(Error): api.fixture_output(b'', 'api', loader)

    def test_declared_case_bounds_are_fixed(self):
        actual = json.loads(api.CASES.read_text())
        api.validate_cases(actual)
        actual['bounds']['max_processes'] += 1
        with self.assertRaises(Error): api.validate_cases(actual)

    def test_incomplete_or_reordered_image_snapshot_fails(self):
        for rows in [[{'event': 'image', 'index': 0}],
                     [{'event': 'image', 'index': 1}, {'event': 'images_end', 'count': 1}],
                     [{'event': 'images_end', 'count': 0}]]:
            with self.subTest(rows=rows), self.assertRaises(Error): list(api.image_inventories(rows))


class FixtureEnvironmentTests(unittest.TestCase):
    def test_policy_cannot_expand_to_other_dlls_or_general_runtime(self):
        original = json.loads(api.CASES.read_text())
        for change in ({'id': 'arbitrary-runtime'}, {'scope': 'all-wine-processes'},
                       {'WINEDLLOVERRIDES': 'mscoree=;mshtml='}, {'WINEDLLOVERRIDES': ''},
                       {'prefix_initialization': 'preseeded'}, {'mono_support': 'qualified'},
                       {'WINEBOOT': 'disabled'}):
            value = copy.deepcopy(original)
            value['environment_policy'].update(change)
            with self.subTest(change=change), self.assertRaises(Error):
                api.validate_cases(value)
        for key, value in [('environment_policy', None), ('environment', {'WINEBOOT': 'disabled'}),
                           ('qualification', 'game-runtime')]:
            changed = {**original, key: value}
            with self.subTest(key=key), self.assertRaises(Error):
                api.validate_cases(changed)

    def test_caller_settings_cannot_change_fixture_or_base_environment(self):
        home, prefix = Path('/owned/home'), Path('/owned/prefix')
        caller = {'WINEDLLOVERRIDES': 'kernel32=', 'WINEBOOT': 'disabled',
                  'WINEPREFIX': '/unowned', 'DYLD_INSERT_LIBRARIES': '/unowned/lib.dylib'}
        with patch.dict(os.environ, caller):
            env = api.fixture_loader_environment(home, prefix, NONCE, '/owned/control', 123)
            clean = base.environment(home, prefix, NONCE)
        self.assertEqual(env['WINEDLLOVERRIDES'], 'mscoree=')
        self.assertEqual(env['WINEPREFIX'], str(prefix))
        self.assertEqual(env['PEAR_BOOTSTRAP_SERVER_PID'], '123')
        self.assertNotIn('WINEBOOT', env)
        self.assertNotIn('DYLD_INSERT_LIBRARIES', env)
        self.assertNotIn('WINEDLLOVERRIDES', clean)
        self.assertNotIn('PEAR_WINE_ABI_FIXTURE', clean)

    def test_unreviewed_base_environment_change_fails_before_launch(self):
        home, prefix = Path('/owned/home'), Path('/owned/prefix')
        clean = base.environment(home, prefix, NONCE)
        for extra in ({'WINEDLLOVERRIDES': 'kernel32='}, {'WINEBOOT': 'disabled'},
                      {'DYLD_INSERT_LIBRARIES': '/private/lib.dylib'}, {'WINEDEBUG': '+all'}):
            with self.subTest(extra=extra), patch.object(base, 'environment', return_value={**clean, **extra}), \
                    self.assertRaises(Error):
                api.fixture_loader_environment(home, prefix, NONCE, '/owned/control', 123)

    def test_case_requires_actual_recorded_launch_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            record, logs, runtime, signed = case_fixture(directory)
            api.assess_case(record, logs, runtime, signed)
            for key, value in [('environment_policy', None), ('loader_environment', None),
                               ('loader_environment', {'WINEDLLOVERRIDES': 'mscoree=;mshtml='}),
                               ('loader_environment', {'WINEDLLOVERRIDES': 'mscoree=', 'WINEBOOT': 'disabled'})]:
                changed = {**record, key: value}
                with self.subTest(key=key, value=value), self.assertRaises(Error):
                    api.assess_case(changed, logs, runtime, signed)

    def test_real_case_launch_boundary_scopes_override_to_loader(self):
        # Exercise production run_case with a process-free transport double.
        # This observes actual launch dictionaries; it produces no Wine receipt.
        launches, held_reads = {}, []
        session = SimpleNamespace(endpoint='/owned/control', children={}, failure=None,
                                  streams={}, events={'server': [{'event': 'server_ready'}]})
        session.observer = SimpleNamespace(registrations={}, signal_observations=[],
                                          refresh=lambda: None)

        def launch(role, argv, env, **options):
            launches[role] = dict(env)
            child = SimpleNamespace(pid=100 + len(launches), identity={'pid': 100 + len(launches)},
                                    exited=role == 'loader', exit_code=0, reaped=False,
                                    allowed_paths={str(argv[0])})
            session.children[role] = child
            if role == 'sentinel':
                held_reads.append(os.dup(options['pass_fds'][0]))
                session.streams[(role, 'stdout')] = {'data': bytearray(b'{}\n')}
            return child

        def cleanup(roles, bounds):
            for role in roles:
                if role in session.children:
                    session.children[role].reaped = session.children[role].exited = True
            return {'complete': True, 'errors': [], 'observation_gap': False,
                    'reaped': {role: True for role in roles}, 'signals': []}

        session.launch = launch
        session.wait_for = lambda predicate, timeout: predicate()
        session.cleanup = cleanup
        session.finish_logs = lambda timeout: []
        session.pump = lambda: setattr(session.children['sentinel'], 'exited', True)
        session.observer.identity = lambda pid: session.children['sentinel'].identity
        cases = json.loads(api.CASES.read_text())
        entries = {name: name for name in ('api_launch', 'loader', 'server', 'sentinel', 'api_pe')}
        try:
            with tempfile.TemporaryDirectory() as directory, \
                    patch.object(api, 'APISession', return_value=session), \
                    patch.object(base, 'prefix_identity', return_value={'device': 1, 'inode': 2}), \
                    patch.object(base, 'parse_lines', return_value=[{}]), \
                    patch.object(base, 'validate_helper'), \
                    patch.object(api, 'assess_case', return_value={'passed': False}):
                record = api.run_case(cases['cases'][0], Path(directory), {'entrypoints': entries},
                                      Path(directory) / 'api', cases['bounds'])
                self.assertEqual(record['outcome'], 'exited')
                self.assertIsNone(record['error'])
                self.assertEqual(record['loader_environment'], {'WINEDLLOVERRIDES': 'mscoree='})
                self.assertEqual(record['environment_policy'], api.ENVIRONMENT_POLICY)
            self.assertEqual(set(launches), {'loader', 'server', 'sentinel'})
            self.assertEqual(launches['loader']['WINEDLLOVERRIDES'], 'mscoree=')
            for role in ('server', 'sentinel'):
                self.assertNotIn('WINEDLLOVERRIDES', launches[role])
                self.assertNotIn('PEAR_WINE_ABI_FIXTURE', launches[role])
        finally:
            for fd in held_reads:
                os.close(fd)


class TargetControlTests(unittest.TestCase):
    def fixtures(self, root):
        guests = {}
        for role, machine in [('x64_control', 0x8664), ('i386_control', 0x14c)]:
            data = bytearray(96)
            data[:2] = b'MZ'; struct.pack_into('<I', data, 60, 64)
            data[64:68] = b'PE\0\0'; struct.pack_into('<H', data, 68, machine)
            (root / (role + '.exe')).write_bytes(data)
            guests[role] = {'execution_permitted': False, 'sha256': hashlib.sha256(data).hexdigest()}
        requirements = {'fixture_suite': 'api-abi', 'guest_fixtures': guests}
        (root / 'requirements.json').write_bytes(encoded(requirements))
        signed = {'requirements_sha256': hashlib.sha256(encoded(requirements)).hexdigest(),
                  'entrypoints': {role: role + '.exe' for role in guests}}
        return signed, requirements

    def test_wrong_architectures_rejected_before_any_spawn(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); signed, _ = self.fixtures(root)
            with patch('subprocess.Popen', side_effect=AssertionError('must not execute controls')):
                rows = api.target_controls(root, signed)
            self.assertEqual([row['machine'] for row in rows], ['x86_64', 'i386'])
            self.assertTrue(all(row['executed'] is False and row['accepted'] is False for row in rows))

    def test_changed_control_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); signed, _ = self.fixtures(root)
            with (root / 'x64_control.exe').open('ab') as stream: stream.write(b'changed')
            with self.assertRaises(Error): api.target_controls(root, signed)

    def test_execution_permission_cannot_be_enabled_for_control(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); signed, requirements = self.fixtures(root)
            requirements['guest_fixtures']['x64_control']['execution_permitted'] = True
            (root / 'requirements.json').write_bytes(encoded(requirements))
            signed['requirements_sha256'] = hashlib.sha256(encoded(requirements)).hexdigest()
            with self.assertRaises(Error): api.target_controls(root, signed)


@unittest.skipUnless(sys.platform == 'darwin' and hasattr(select := __import__('select'), 'kqueue'),
                     'ordinary native cleanup test needs Darwin kqueue')
class OwnedCleanupTests(unittest.TestCase):
    def test_unregistered_fork_fails_coverage_but_owned_group_is_terminated(self):
        with tempfile.TemporaryDirectory() as directory:
            session = base.Session(Path(directory), observer=api.APIObserver())
            env = {'PATH': '/usr/bin:/bin'}
            executable = session.observer.executable(os.getpid())
            bounds = {'grace_ms': 100, 'terminate_ms': 200, 'kill_ms': 1000, 'drain_ms': 100}
            script = 'import os,time; os.fork(); print("ready",flush=True); time.sleep(20)'
            sentinel = session.launch('sentinel', [executable, '-c', 'import time; time.sleep(20)'], env)
            loader = session.launch('loader', [executable, '-c', script], env)
            try:
                self.assertTrue(session.wait_for(lambda: b'ready' in session.streams[('loader', 'stdout')]['data'], 3))
                result = session.cleanup(('loader',), bounds)
                self.assertFalse(result['complete'])
                self.assertTrue(result['observation_gap'])
                self.assertTrue(result['reaped']['loader'])
                session.observer.refresh()
                self.assertFalse(sentinel.exited)
                self.assertEqual(session.observer.identity(sentinel.pid), sentinel.identity)
            finally:
                session.cleanup(('loader', 'sentinel'), bounds)
                for child in session.children.values():
                    if not child.reaped:
                        session.emergency_reap(child)
                session.finish_logs(100)


if __name__ == '__main__':
    unittest.main()


def case_fixture(directory):
    """Parser-only synthetic native images/observations, never executable receipts."""
    from test_runner import record_fixture
    record, raw = record_fixture()
    runtime = Path(directory).resolve()
    entries = {'loader': 'wine', 'server': 'wineserver', 'ntdll': 'ntdll.so',
               'api_launch': 'api-launch', 'sentinel': 'sentinel'}
    images = []
    for index, name in enumerate(entries.values()):
        data = struct.pack('<8I', 0xfeedfacf, base.MACH_ARM64, 0, 2, 1, 24, 0, 0)
        data += struct.pack('<II', 0x1b, 24) + bytes([index + 1]) * 16
        (runtime / name).write_bytes(data)
        images.append({'path': name, 'sha256': hashlib.sha256(data).hexdigest()})
    signed = {'entrypoints': entries, 'native_images': images, 'code_publication_policy': 'page-wx',
              'arena_capacity': {'policy': 'page-wx', 'wine_execution': False, 'header_sha256': 'a'*64,
                'limits': {'interior_bytes': 1049952256, 'alignment': 65536, 'max_image_bytes': 38993920,
                           'max_slots': 752, 'page_bytes': 4096}}}
    record['record_kind'] = 'wine_api_case'
    record['case'] = {'id': 'api', 'expected_exit': 0}
    record['environment_policy'] = dict(api.ENVIRONMENT_POLICY)
    record['loader_environment'] = dict(api.LOADER_ENVIRONMENT)
    record['prefix'] = record.pop('prefixes')['loader']
    record['pe_executed'] = True
    record['registrations'] = []
    for cleanup in ('cleanup', 'sentinel_cleanup'):
        record[cleanup]['complete'] = True
    for role, process in record['processes'].items():
        names = ['api_launch', 'loader'] if role == 'loader' else [role]
        process['allowed_paths'] = sorted(str(runtime / entries[name]) for name in names)
    server_rows = record['events']['server']
    server_rows[1].update(path=str(runtime / 'wineserver'), uuid='02'*16)
    root_rows = record['events']['loader']
    root_rows[-1] = {**root_rows[-1], 'event': 'stage3_pe_continue'}
    inventory = next(row for row in root_rows if row['event'] == 'image')
    inventory.update(path=str(runtime / 'wine'), uuid='01'*16)
    image_index = root_rows.index(inventory)
    root_rows.insert(image_index + 1, {**inventory, 'index': 1, 'path': str(runtime / 'ntdll.so'), 'uuid': '03'*16})
    next(row for row in root_rows if row['event'] == 'images_end')['count'] = 2
    stamp = root_rows[-1]
    root_rows.extend([
        {**stamp, 'event': 'arena_reserve', 'policy': 'page-wx', 'arena_sequence': 1,
         'mapping_base': 0x20000000, 'interior_base': 0x20000000,
         'mapping_bytes': 1050017792, 'interior_bytes': 1049952256, 'page_bytes': 4096, 'max_slots': 752},
        {**stamp, 'event': 'arena_publish', 'policy': 'page-wx', 'arena_sequence': 2,
         'slot': 0, 'slot_generation': 1, 'original_base': 0x140000000, 'base': 0x20000000, 'size': 65536, 'capacity': 65536,
         'code_pages': 1, 'data_pages': 2, 'relocations': 1, 'reused': False}])
    root_rows.append({**root_rows[-1], 'event': 'stage3_guest_exit', 'exit_code': 0})
    root_rows.append({**root_rows[-1], 'event': 'stage3_process_exit', 'exit_code': 0})
    for role, pid, exit_code in [('loader', 802, 0), ('process-01', 804, 37), ('process-02', 805, 0)]:
        identity = dict(record['processes']['loader']['identity'])
        if role != 'loader': identity.update(pid=pid, ppid=802, start_usec=pid)
        hello, _ = hello_fixture('loader' if role == 'loader' else 'fork')
        hello.update(identity)
        hello['pgid'] = 802
        record['registrations'].append({'role': role, 'hello': hello, 'identity': identity,
            'parent_role': None if role == 'loader' else 'loader', 'exited': True,
            'exit_status': exit_code << 8, 'exit_code': exit_code, 'exit_observed_ns': 5})
        if role != 'loader':
            rows = copy.deepcopy(root_rows)
            fork = {**rows[0], 'event': 'stage3_fork'}
            rows = [fork, *rows[2:]]
            for row in rows:
                row.update(identity)
                if row['event'] in ('stage3_guest_exit', 'stage3_process_exit'): row['exit_code'] = exit_code
            record['events'][role] = rows
            server_rows.append({**server_rows[-1], 'peer_pid': pid})
    record['pre_cleanup'] = {'at_ns': 10, 'processes': {row['role']: {
        'exited': True, 'exit_code': row['exit_code'], 'exit_status': row['exit_status']}
        for row in record['registrations']}}
    record['signal_observations'] = [{'role': 'server', 'signal': int(signal.SIGINT),
                                      'at_ns': 11, 'live_registered_roles': []}]
    raw[('loader', 'stdout')] += b''.join(jsonl(row) for row in api.expected_api_rows())
    for role, rows in record['events'].items(): raw[(role, 'events')] = b''.join(jsonl(row) for row in rows)
    return record, raw, runtime, signed


class CaseAssessmentTests(unittest.TestCase):
    def test_independent_positive_record_reconstruction(self):
        with tempfile.TemporaryDirectory() as directory:
            record, logs, runtime, signed = case_fixture(directory)
            result = api.assess_case(record, logs, runtime, signed)
            self.assertTrue(result['passed'])
            self.assertEqual(result['pe_processes'], 3)
            self.assertNotIn('relocation_observations', result)

    def test_dropped_handshake_unknown_images_bad_geometry_and_generation_fail(self):
        for mode in ('handshake', 'slice', 'mapping', 'exec', 'unknown-image'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                record, logs, runtime, signed = case_fixture(directory)
                rows = record['events']['process-01']
                if mode == 'handshake':
                    record['events']['server'].pop()
                elif mode == 'slice': next(row for row in rows if row['event'] == 'image')['cpu_type'] = 0x1000007
                elif mode == 'mapping': next(row for row in rows if row['event'] == 'memory')['region_size'] = 16384
                elif mode == 'exec': rows.remove(next(row for row in rows if row['event'] == 'loader_entry'))
                else: next(row for row in rows if row['event'] == 'image')['path'] = '/external/unknown.dylib'
                for role, events in record['events'].items(): logs[(role, 'events')] = b''.join(jsonl(row) for row in events)
                with self.assertRaises(Error): api.assess_case(record, logs, runtime, signed)

    def test_unknown_child_exit_changed_registration_and_cleanup_fail(self):
        for mode in ('exit', 'parent', 'group', 'cleanup', 'sentinel', 'log'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                record, logs, runtime, signed = case_fixture(directory)
                if mode == 'exit': record['registrations'][1]['exited'] = False
                elif mode == 'parent': record['registrations'][1]['parent_role'] = 'missing'
                elif mode == 'group': record['registrations'][1]['hello']['pgid'] = 999
                elif mode == 'cleanup': record['cleanup']['complete'] = False
                elif mode == 'sentinel': record['sentinel_survived'] = False
                else: logs[('process-01', 'events')] += jsonl({'event': 'added'})
                with self.assertRaises(Error): api.assess_case(record, logs, runtime, signed)


class ReviewedGapTests(unittest.TestCase):
    def test_consistently_forged_native_root_still_fails_actual_direct_child_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            record, logs, runtime, signed = case_fixture(directory)
            old_pid, forged = record['processes']['loader']['identity']['pid'], 999
            for row in record['registrations']:
                row['hello']['pgid'] = forged
                if row['role'] == 'loader':
                    row['identity']['pid'] = row['hello']['pid'] = forged
                elif row['identity']['ppid'] == old_pid:
                    row['identity']['ppid'] = row['hello']['ppid'] = forged
            for role, rows in record['events'].items():
                for row in rows:
                    if role == 'loader': row['pid'] = forged
                    elif row.get('ppid') == old_pid: row['ppid'] = forged
                    if row.get('peer_pid') == old_pid: row['peer_pid'] = forged
                logs[(role, 'events')] = b''.join(jsonl(row) for row in rows)
            with self.assertRaisesRegex(Error, 'root_registration_identity'):
                api.assess_case(record, logs, runtime, signed)

    def test_unexpected_pre_cleanup_nonzero_or_signal_cannot_pass(self):
        for exit_code, status in [(91, 91 << 8), (-signal.SIGSEGV, signal.SIGSEGV)]:
            with tempfile.TemporaryDirectory() as directory:
                record, _, _, _ = case_fixture(directory)
                child = record['registrations'][2]
                child.update(exit_code=int(exit_code), exit_status=int(status))
                record['pre_cleanup']['processes'][child['role']].update(
                    exit_code=int(exit_code), exit_status=int(status))
                with self.assertRaisesRegex(Error, 'unexpected_pre_cleanup_descendant_exit'):
                    api.assess_descendant_exits(record)

    def test_only_observed_matching_owned_group_signal_can_explain_cleanup_window(self):
        with tempfile.TemporaryDirectory() as directory:
            record, _, _, _ = case_fixture(directory)
            child = record['registrations'][2]
            child.update(exit_code=-int(signal.SIGTERM), exit_status=int(signal.SIGTERM), exit_observed_ns=13)
            record['pre_cleanup']['processes'][child['role']] = {'exited': False, 'exit_code': None, 'exit_status': None}
            record['cleanup']['signals'] = [{'role': 'loader', 'signal': int(signal.SIGTERM)}]
            record['signal_observations'] = [{'role': 'loader', 'signal': int(signal.SIGTERM),
                                              'at_ns': 11, 'live_registered_roles': [child['role']]}]
            api.assess_descendant_exits(record)
            for key, value in [('signal', int(signal.SIGINT)), ('at_ns', 14), ('live_registered_roles', [])]:
                changed = copy.deepcopy(record)
                changed['signal_observations'][0][key] = value
                if key == 'signal': changed['cleanup']['signals'][0][key] = value
                with self.subTest(key=key), self.assertRaises(Error): api.assess_descendant_exits(changed)
            child.update(exit_code=-int(signal.SIGSEGV), exit_status=int(signal.SIGSEGV))
            with self.assertRaisesRegex(Error, 'unexpected_cleanup_window_exit'):
                api.assess_descendant_exits(record)

    def test_missing_pre_cleanup_snapshot_or_unreported_guest_exit_fails(self):
        for mode in ('snapshot', 'guest-exit'):
            with tempfile.TemporaryDirectory() as directory:
                record, _, _, _ = case_fixture(directory)
                if mode == 'snapshot': del record['pre_cleanup']
                else: record['events']['process-02'] = [row for row in record['events']['process-02']
                      if row['event'] not in ('stage3_guest_exit', 'stage3_process_exit')]
                with self.subTest(mode=mode), self.assertRaises(Error): api.assess_descendant_exits(record)


class ArenaObservationTests(unittest.TestCase):
    def test_every_executed_loader_needs_its_own_actual_publication(self):
        for mode in ('missing', 'policy', 'sequence', 'generation', 'bounds', 'counts', 'reuse', 'failure'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                result, _, _, signed = case_fixture(directory)
                rows = result['events']['process-01']
                published = next(row for row in rows if row['event'] == 'arena_publish')
                if mode == 'missing': rows.remove(published)
                elif mode == 'policy': published['policy'] = 'thread-jit'
                elif mode == 'sequence': published['arena_sequence'] += 1
                elif mode == 'generation': published['generation'] = 0
                elif mode == 'bounds': published['base'] += 4096
                elif mode == 'counts': published['code_pages'] = True
                elif mode == 'reuse': published['reused'] = True
                else: published['event'] = 'arena_failure'
                with self.assertRaises(Error): api.assess_arena_events(result, signed, [])

    def test_recorded_capacity_must_match_the_verified_build_in_every_loader(self):
        with tempfile.TemporaryDirectory() as directory:
            result, _, _, signed = case_fixture(directory)
            signed['arena_capacity']['limits']['max_slots'] += 1
            with self.assertRaisesRegex(Error, 'arena_capacity_contract'):
                api.assess_arena_events(result, signed, [])

    def test_dll_lifetime_matches_the_native_slot_generation_timeline(self):
        with tempfile.TemporaryDirectory() as directory:
            result, _, _, signed = case_fixture(directory)
            result['case']['id'] = 'abi'
            rows = result['events']['loader']
            stamp = next(row for row in rows if row['event'] == 'arena_publish')
            for index in range(34):
                publish = {**stamp, 'slot': 1, 'slot_generation': index + 1,
                           'arena_sequence': 3 + index * 2, 'base': 0x20010000, 'reused': bool(index)}
                retire = {**publish, 'event': 'arena_retire', 'arena_sequence': 4 + index * 2}
                rows.extend([publish, retire])
            public = api.assess_arena_events(result, signed, lifetime_fixture())
            self.assertEqual(public[0]['retirements'], 34)
            self.assertEqual(public[0]['compatible_reuses'], 33)
            for mode in ('retired-address', 'callback-outside', 'missing-retire', 'stale-generation', 'live-reuse'):
                changed, private = copy.deepcopy(result), lifetime_fixture()
                target = changed['events']['loader']
                if mode == 'retired-address': target[-1]['base'] += 65536
                elif mode == 'callback-outside': private[0]['callback_address'] = 0x30000000
                elif mode == 'missing-retire': target.pop()
                elif mode == 'stale-generation': target[-2]['slot_generation'] -= 1
                else: target[-3]['event'] = 'arena_publish'
                with self.subTest(mode=mode), self.assertRaises(Error): api.assess_arena_events(changed, signed, private)

    def test_private_fixture_events_require_actual_complete_order_and_typed_results(self):
        helper, loader = helper_record()
        for mode in ('missing-event', 'wrong-round', 'address-change', 'boolean-counter', 'import-status'):
            rows = [helper, *relocation_fixture(), *copy.deepcopy(api.IMPORT_EXPECTED), *lifetime_fixture(),
                    dict(api.RELOCATION_EXPECTED), dict(api.LIFETIME_EXPECTED), dict(api.ABI_EXPECTED)]
            if mode == 'missing-event': rows.pop(9)
            elif mode == 'wrong-round': rows[9]['round'] = 31
            elif mode == 'address-change': rows[10]['module_base'] += 65536
            elif mode == 'boolean-counter': rows[-2]['failed_load_cleanup_checks'] = True
            else: rows[7]['status'] = 0
            with self.subTest(mode=mode), self.assertRaises(Error):
                api.fixture_output(b''.join(jsonl(row) for row in rows), 'abi', loader)


class ProducerSnapshotTests(unittest.TestCase):
    def test_prelaunch_snapshots_preserve_sources_without_executing_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'repo'
            source.mkdir()
            (source / 'source.py').write_text('raise AssertionError("never execute archived code")')
            digest = hashlib.sha256((source / 'source.py').read_bytes()).hexdigest()
            with patch.object(api, 'REPO', source), patch.object(api, 'producers', return_value={'source.py': digest}):
                result = api.snapshot_producers(root / 'run')
                self.assertEqual(result['source.py'], digest)
                self.assertEqual((root / 'run/producer/source.py').read_bytes(), (source / 'source.py').read_bytes())
                with self.assertRaises(FileExistsError): api.snapshot_producers(root / 'run')


class StagedCleanupTests(unittest.TestCase):
    def test_failed_loader_cleanup_still_stops_server_and_retains_all_evidence(self):
        loader_signal = {'role': 'loader', 'signal': int(signal.SIGTERM)}
        server_signal = {'role': 'server', 'signal': int(signal.SIGINT)}
        loader_error = {'role': 'loader', 'code': 'owned_group_survivor'}
        server_error = {'role': 'server', 'code': 'signal_refused'}
        loader = {'signals': [loader_signal], 'errors': [loader_error],
                  'observation_gap': True, 'reaped': {'loader': False}, 'complete': False}
        server = {'signals': [server_signal], 'errors': [server_error],
                  'observation_gap': False, 'reaped': {'server': True}, 'complete': False}
        session = api.APISession.__new__(api.APISession)
        with patch.object(base.Session, 'cleanup', autospec=True, side_effect=[loader, server]) as cleanup, \
                patch.object(session, 'registered_exit_barrier', return_value=None):
            result = session.cleanup(('loader', 'server'), {'drain_ms': 1000})
        self.assertEqual(result, {'signals': [loader_signal, server_signal],
            'errors': [loader_error, server_error], 'observation_gap': True,
            'reaped': {'loader': False, 'server': True}, 'complete': False})
        self.assertEqual([call.args[1] for call in cleanup.call_args_list], [('loader',), ('server',)])
        self.assertEqual(cleanup.call_args_list[0].kwargs, {'allow_interrupt': False})
        self.assertEqual(cleanup.call_args_list[1].kwargs, {})

    def test_first_incomplete_report_cannot_be_overwritten_by_server_success(self):
        loader = {'signals': [], 'errors': [], 'observation_gap': False,
                  'reaped': {'loader': True}, 'complete': False}
        server = {'signals': [], 'errors': [], 'observation_gap': False,
                  'reaped': {'server': True}, 'complete': True}
        session = api.APISession.__new__(api.APISession)
        with patch.object(base.Session, 'cleanup', autospec=True, side_effect=[loader, server]), \
                patch.object(session, 'registered_exit_barrier', return_value=None):
            result = session.cleanup(('loader', 'server'), {'drain_ms': 1000})
        self.assertFalse(result['complete'])
        self.assertEqual(result['reaped'], {'loader': True, 'server': True})

    def test_other_owned_role_cleanup_keeps_existing_policy(self):
        report = {'signals': [], 'errors': [], 'observation_gap': False,
                  'reaped': {'sentinel': True}, 'complete': True}
        session = api.APISession.__new__(api.APISession)
        with patch.object(base.Session, 'cleanup', autospec=True, return_value=report) as cleanup:
            self.assertIs(session.cleanup(('sentinel',), {}), report)
        cleanup.assert_called_once_with(session, ('sentinel',), {})

    def test_successful_server_signal_waits_for_all_registered_exit_observations(self):
        with tempfile.TemporaryDirectory() as directory:
            record, _, _, _ = case_fixture(directory)
            child = record['registrations'][2]
            child.update(exit_code=-int(signal.SIGTERM), exit_status=int(signal.SIGTERM), exit_observed_ns=13)
            record['pre_cleanup']['processes'][child['role']] = {
                'exited': False, 'exit_code': None, 'exit_status': None}
            record['cleanup']['signals'] = [{'role': 'loader', 'signal': int(signal.SIGTERM)},
                                            {'role': 'server', 'signal': int(signal.SIGINT)}]
            record['signal_observations'] = [
                {'role': 'loader', 'signal': int(signal.SIGTERM), 'at_ns': 11,
                 'live_registered_roles': [child['role']]},
                {'role': 'server', 'signal': int(signal.SIGINT), 'at_ns': 14, 'live_registered_roles': []}]
            api.assess_descendant_exits(record)
            for mode in ('reported-live', 'unobserved-exit'):
                changed = copy.deepcopy(record)
                if mode == 'reported-live':
                    changed['signal_observations'][1]['live_registered_roles'] = [child['role']]
                else:
                    # An empty live list cannot hide an exit observed after shutdown.
                    changed['signal_observations'][1]['at_ns'] = 12
                with self.subTest(mode=mode), self.assertRaisesRegex(Error, 'server_shutdown_before_descendants'):
                    api.assess_descendant_exits(changed)

    def test_native_exit_one_during_cleanup_remains_a_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            record, _, _, _ = case_fixture(directory)
            child = record['registrations'][2]
            child.update(exit_code=1, exit_status=1 << 8, exit_observed_ns=13)
            record['pre_cleanup']['processes'][child['role']] = {
                'exited': False, 'exit_code': None, 'exit_status': None}
            record['events'][child['role']] = [row for row in record['events'][child['role']]
                if row['event'] not in ('stage3_guest_exit', 'stage3_process_exit')]
            record['cleanup']['signals'] = [{'role': 'loader', 'signal': int(signal.SIGINT)},
                                            {'role': 'server', 'signal': int(signal.SIGINT)}]
            record['signal_observations'] = [
                {'role': 'loader', 'signal': int(signal.SIGINT), 'at_ns': 11,
                 'live_registered_roles': [child['role']]},
                {'role': 'server', 'signal': int(signal.SIGINT), 'at_ns': 14, 'live_registered_roles': []}]
            with self.assertRaisesRegex(Error, 'unexpected_cleanup_window_exit'):
                api.assess_descendant_exits(record)

    def test_signal_reports_and_observations_must_keep_chronological_order(self):
        with tempfile.TemporaryDirectory() as directory:
            record, _, _, _ = case_fixture(directory)
            record['cleanup']['signals'] = [{'role': 'loader', 'signal': int(signal.SIGTERM)},
                                            {'role': 'server', 'signal': int(signal.SIGINT)}]
            record['signal_observations'] = [
                {'role': 'loader', 'signal': int(signal.SIGTERM), 'at_ns': 12, 'live_registered_roles': []},
                {'role': 'server', 'signal': int(signal.SIGINT), 'at_ns': 11, 'live_registered_roles': []}]
            with self.assertRaisesRegex(Error, 'cleanup_signal_time'):
                api.assess_descendant_exits(record)
            record['signal_observations'].reverse()
            with self.assertRaisesRegex(Error, 'cleanup_signal_binding'):
                api.assess_descendant_exits(record)

    def test_late_registration_cannot_be_explained_by_staged_shutdown(self):
        with tempfile.TemporaryDirectory() as directory:
            record, _, _, _ = case_fixture(directory)
            del record['pre_cleanup']['processes']['process-02']
            with self.assertRaisesRegex(Error, 'late_or_unobserved_registration'):
                api.assess_descendant_exits(record)

    def test_duration_bound_includes_three_shutdown_phases_sentinel_wait_and_drain(self):
        bounds = json.loads(api.CASES.read_text())['bounds']
        self.assertEqual(api.cleanup_allowance_ms(bounds), 37000)
        api.validate_duration(217000, 180000, bounds)
        for elapsed in (217001, -1, True, 217000.0):
            with self.subTest(elapsed=elapsed), self.assertRaisesRegex(Error, 'api_case_duration'):
                api.validate_duration(elapsed, 180000, bounds)
        changed = {**bounds, 'grace_ms': bounds['grace_ms'] + 1}
        self.assertEqual(api.cleanup_allowance_ms(changed), 37003)
        for key in ('grace_ms', 'terminate_ms', 'kill_ms', 'drain_ms'):
            for invalid in (True, -1, 60001, 1.5):
                with self.subTest(key=key, invalid=invalid), self.assertRaisesRegex(Error, 'api_cleanup_budget'):
                    api.cleanup_allowance_ms({**bounds, key: invalid})

    @unittest.skipUnless(sys.platform == 'darwin' and hasattr(__import__('select'), 'kqueue'),
                         'ordinary native staged shutdown needs Darwin kqueue')
    def test_native_loader_term_handler_receives_reply_before_server_shutdown(self):
        # These are ordinary native Python processes with a local IPC dependency.
        # No Wine fixture, fake signing grant or restricted execution is involved.
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            root = Path(directory)
            session = api.APISession(root, root, {}, NONCE)
            env = {'PATH': '/usr/bin:/bin'}
            executable = session.observer.executable(os.getpid())
            bounds = {'grace_ms': 150, 'terminate_ms': 1000, 'kill_ms': 1000, 'drain_ms': 200}
            endpoint = str(root / 'service')
            server_code = '''import os,signal,socket,sys
signal.signal(signal.SIGINT, lambda *_: os._exit(0))
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.bind(sys.argv[1]); s.listen(1)
print('server-ready', flush=True)
while True:
    client, _ = s.accept()
    if client.recv(1) == b'Q': client.sendall(b'A')
    client.close()
'''
            loader_code = '''import os,signal,socket,sys,time
signal.signal(signal.SIGINT, lambda *_: os._exit(99))
def terminate(*_):
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(0.8); client.connect(sys.argv[1]); client.sendall(b'Q')
        if client.recv(1) != b'A': os._exit(92)
        os.write(1, b'term-server-reply\\n')
        os._exit(0)
    except OSError:
        os._exit(93)
signal.signal(signal.SIGTERM, terminate)
print('loader-ready', flush=True)
while True: time.sleep(0.02)
'''
            try:
                sentinel = session.launch('sentinel', [executable, '-c', 'import time; time.sleep(20)'], env)
                server = session.launch('server', [executable, '-c', server_code, endpoint], env)
                self.assertTrue(session.wait_for(lambda: b'server-ready' in
                    session.streams[('server', 'stdout')]['data'], 3))
                loader = session.launch('loader', [executable, '-c', loader_code, endpoint], env)
                self.assertTrue(session.wait_for(lambda: b'loader-ready' in
                    session.streams[('loader', 'stdout')]['data'], 3))
                started = time.monotonic()
                result = session.cleanup(('loader', 'server'), bounds)
                self.assertGreaterEqual(time.monotonic() - started, bounds['grace_ms'] / 1000)
                self.assertTrue(result['complete'], result)
                self.assertEqual((loader.exit_code, server.exit_code), (0, 0))
                self.assertEqual(result['signals'], [{'role': 'loader', 'signal': int(signal.SIGTERM)},
                                                      {'role': 'server', 'signal': int(signal.SIGINT)}])
                self.assertEqual([(row['role'], row['signal']) for row in session.observer.signal_observations],
                                 [(row['role'], row['signal']) for row in result['signals']])
                self.assertIn(b'term-server-reply\n', session.streams[('loader', 'stdout')]['data'])
                session.observer.refresh()
                self.assertFalse(sentinel.exited)
                self.assertEqual(session.observer.identity(sentinel.pid), sentinel.identity)
            finally:
                session.cleanup(('loader', 'server'), bounds)
                session.cleanup(('sentinel',), bounds)
                for child in session.children.values():
                    if not child.reaped:
                        session.emergency_reap(child)
                session.finish_logs(bounds['drain_ms'])


class RegisteredExitBarrierTests(unittest.TestCase):
    def session(self, row):
        session = api.APISession.__new__(api.APISession)
        session.failure = None
        session.observer = SimpleNamespace(registrations={804: row})
        return session

    def reports(self):
        return [{'signals': [], 'errors': [], 'observation_gap': False,
                 'reaped': {'loader': True}, 'complete': True},
                {'signals': [{'role': 'server', 'signal': int(signal.SIGINT)}], 'errors': [],
                 'observation_gap': False, 'reaped': {'server': True}, 'complete': True}]

    def test_delayed_note_exit_receipt_is_observed_before_server_cleanup(self):
        row = {'exited': False, 'exit_code': None, 'exit_status': None, 'exit_observed_ns': None}
        session = self.session(row)
        observed = []
        reports = self.reports()
        def pump(wait):
            self.assertGreaterEqual(wait, 0)
            self.assertLessEqual(wait, .02)
            observed.append('pump')
            # Exited alone is insufficient: first pump lacks the actual status.
            row['exited'] = True
            if observed.count('pump') == 2:
                row.update(exit_code=0, exit_status=0, exit_observed_ns=13)
        session.pump = pump
        def cleanup(owner, roles, bounds, **options):
            observed.append(roles[0])
            if roles == ('server',):
                self.assertEqual(row['exit_observed_ns'], 13)
                self.assertEqual(observed, ['loader', 'pump', 'pump', 'server'])
            return reports[0 if roles == ('loader',) else 1]
        with patch.object(base.Session, 'cleanup', autospec=True, side_effect=cleanup):
            result = session.cleanup(('loader', 'server'), {'drain_ms': 1000})
        self.assertTrue(result['complete'])
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['signals'], reports[1]['signals'])

    def test_receipt_timeout_still_cleans_server_and_cannot_pass(self):
        row = {'exited': False, 'exit_code': None, 'exit_status': None, 'exit_observed_ns': None}
        session = self.session(row)
        session.pump = lambda wait: None
        reports = self.reports()
        with patch.object(base.Session, 'cleanup', autospec=True, side_effect=reports) as cleanup, \
                patch.object(api.time, 'monotonic', side_effect=[0, 0, .011]):
            result = session.cleanup(('loader', 'server'), {'drain_ms': 10})
        self.assertEqual([call.args[1] for call in cleanup.call_args_list], [('loader',), ('server',)])
        self.assertEqual(result['errors'], [{'role': 'observer', 'code': 'registered_exit_barrier_timeout'}])
        self.assertTrue(result['observation_gap'])
        self.assertFalse(result['complete'])
        self.assertEqual(result['signals'], reports[1]['signals'])
        self.assertEqual(result['reaped'], {'loader': True, 'server': True})

    def test_pump_failure_preserves_reason_and_still_cleans_server(self):
        row = {'exited': False}
        for error in (Error('owned_identity_unavailable'), OSError('private OS diagnostic'), KeyboardInterrupt()):
            session = self.session(row)
            reports = self.reports()
            expected = getattr(error, 'code', 'registered_exit_barrier_observation_failed')
            with self.subTest(error=type(error).__name__), \
                    patch.object(session, 'pump', create=True, side_effect=error), \
                    patch.object(base.Session, 'cleanup', autospec=True, side_effect=reports) as cleanup:
                result = session.cleanup(('loader', 'server'), {'drain_ms': 1000})
            self.assertEqual(cleanup.call_count, 2)
            self.assertEqual(result['errors'], [{'role': 'observer', 'code': expected}])
            self.assertNotIn('private OS diagnostic', encoded(result).decode())
            self.assertFalse(result['complete'])
            self.assertTrue(result['observation_gap'])

    def test_registration_or_stream_failure_is_not_hidden_by_exit_flags(self):
        row = {'exited': True, 'exit_code': 0, 'exit_status': 0, 'exit_observed_ns': 13}
        session = self.session(row)
        def pump(wait):
            session.failure = 'registration_ack_failed'
        session.pump = pump
        with patch.object(base.Session, 'cleanup', autospec=True, side_effect=self.reports()) as cleanup:
            result = session.cleanup(('loader', 'server'), {'drain_ms': 1000})
        self.assertEqual(cleanup.call_count, 2)
        self.assertEqual(result['errors'], [{'role': 'observer', 'code': 'registration_ack_failed'}])
        self.assertFalse(result['complete'])

    def test_boolean_or_incomplete_exit_receipts_never_satisfy_barrier(self):
        valid = {'exited': True, 'exit_code': 0, 'exit_status': 0, 'exit_observed_ns': 13}
        for key, invalid in [('exited', 1), ('exited', False), ('exit_code', None), ('exit_code', False),
                             ('exit_status', None), ('exit_status', False), ('exit_observed_ns', None),
                             ('exit_observed_ns', 0), ('exit_observed_ns', True)]:
            session = self.session({**valid, key: invalid})
            session.pump = lambda wait: None
            with self.subTest(key=key, invalid=invalid), \
                    patch.object(api.time, 'monotonic', side_effect=[0, 0, .011]):
                self.assertEqual(session.registered_exit_barrier(10), 'registered_exit_barrier_timeout')

    def test_barrier_continues_observing_new_registrations(self):
        row = {'exited': True, 'exit_code': 0, 'exit_status': 0, 'exit_observed_ns': 13}
        session = self.session(row)
        def pump(wait):
            session.observer.registrations[805] = {'exited': False, 'exit_code': None,
                                                   'exit_status': None, 'exit_observed_ns': None}
        session.pump = pump
        with patch.object(api.time, 'monotonic', side_effect=[0, 0, .011]):
            self.assertEqual(session.registered_exit_barrier(10), 'registered_exit_barrier_timeout')
