"""Original synthetic records and ordinary subprocess lifecycle tests.

No test executes Wine, a 4 KiB setter, PE code or an operation under a simulated
signing grant. Synthetic observations are evidence-parser inputs only.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import struct
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[2] / 'tools/wine'
sys.path.insert(0, str(TOOLS))
import common
import run_fixtures as runner

NONCE = 'a' * 32


def fixture(expected='bootstrap_stop'):
    children = {role: SimpleNamespace(role=role, pid=pid, identity={
        'pid': pid, 'ppid': 800, 'start_sec': 1000, 'start_usec': pid})
        for role, pid in [('server', 801), ('loader', 802), ('sentinel', 803)]}
    prefixes = {role: {'device': 1, 'inode': 10, 'namespace': '/private/tmp/owned-synthetic'}
                for role in ('server', 'loader')}
    def event(role, name, generation=0, **detail):
        value = {'version': 1, 'role': role, 'event': name, 'nonce': NONCE,
                 **children[role].identity, 'identity_error': 0, 'generation': generation}
        if name in runner.SNAPSHOTS:
            value.update(cpu_type=runner.MACH_ARM64, translation_value=0, translation_error=0,
                         user_page=4096 if role == 'loader' else 16384,
                         vm_page=4096 if role == 'loader' else 16384,
                         kernel_page=16384, kernel_error=0,
                         thread_main=0 if name == 'bootstrap_native' else 1,
                         prefix_dev=1, prefix_ino=10, prefix_error=0)
        value.update(detail)
        return value
    server = [event('server', 'server_ready'),
              event('server', 'image', index=0, path='/synthetic/wineserver', cpu_type=runner.MACH_ARM64, uuid='1'*32),
              event('server', 'images_end', count=1)]
    loader = [event('loader', 'loader_entry'), event('loader', 'ntdll_entry'),
              event('loader', 'loader_reexec', next_generation=1),
              event('loader', 'loader_entry', 1), event('loader', 'ntdll_entry', 1)]
    if expected == 'server_refused':
        prefixes['loader']['inode'] = 11
        for row in loader:
            if 'prefix_ino' in row:
                row['prefix_ino'] = 11
        loader.append(event('loader', 'failure', 1, operation='unowned_server_fallback', error=1))
    else:
        server.append(event('server', 'server_handshake', peer_pid=802, server_start='133000000000000000'))
        loader.extend([event('loader', 'server_peer', 1, peer_pid=801, peer_error=0),
                       event('loader', 'server_handshake', 1, peer_pid=801, server_start='133000000000000000'),
                       event('loader', 'bootstrap_native', 1),
                       event('loader', 'memory', 1, pagezero_address=0, pagezero_size=65536,
                             null_read_error=1, guard_end_read_error=1, low_address=0x7ffe0000,
                             region_address=0x7ffe0000, region_size=4096, region_protection=1, region_error=0),
                       event('loader', 'image', 1, index=0, path='/synthetic/wine', cpu_type=runner.MACH_ARM64, uuid='2'*32),
                       event('loader', 'images_end', 1, count=1),
                       event('loader', 'bootstrap_hold' if expected == 'timeout' else 'bootstrap_stop', 1,
                             **({} if expected == 'timeout' else {'pe_entered': False, 'foreign_mode_entered': False}))])
    return {'server': server, 'loader': loader}, children, prefixes


def record_fixture(expected='bootstrap_stop'):
    events, children, prefixes = fixture(expected)
    def helper(role, kind):
        return {'version': 1, 'record_kind': kind, **children[role].identity,
                'cpu_type': runner.MACH_ARM64, 'translation_value': 0, 'query_errno': 0,
                'user_page': 16384, 'vm_page': 16384, 'kernel_page': 16384, 'kernel_error': 0}
    dump = lambda rows: b''.join(json.dumps(row).encode() + b'\n' for row in rows)
    logs = {('sentinel', 'stdout'): dump([helper('sentinel', 'pear_sentinel_ready'),
            {'version': 1, 'record_kind': 'pear_sentinel_done', 'signal': 0, 'command': 81}]),
            ('loader', 'stdout'): dump([helper('loader', 'pear_bootstrap_helper')]),
            ('server', 'events'): dump(events['server']), ('loader', 'events'): dump(events['loader'])}
    result = {'schema_version': 1, 'record_kind': 'wine_bootstrap_case', 'error': None, 'stream_error': None,
              'runtime_qualified': False, 'pe_executed': False, 'nonce': NONCE, 'events': events,
              'prefixes': prefixes, 'case': {'expected': expected}, 'sentinel_survived': True,
              'cleanup': {'errors': [], 'observation_gap': False, 'reaped': {'server': True, 'loader': True},
                          'signals': [{'role': 'server', 'signal': int(signal.SIGINT)}]},
              'sentinel_cleanup': {'errors': [], 'observation_gap': False, 'reaped': {'sentinel': True}, 'signals': []},
              'outcome': 'timeout' if expected == 'timeout' else 'exited',
              'processes': {role: {'identity': child.identity, 'exit_code':
                   (-signal.SIGINT if expected == 'timeout' else 125 if expected == 'server_refused' else 0)
                   if role == 'loader' else 0, 'reaped': True, 'fork_seen': False}
                   for role, child in children.items()}, 'passed': True}
    return result, logs


class EvidenceTests(unittest.TestCase):
    def test_source_derived_normal_timeout_and_refusal_records(self):
        for expected in ('bootstrap_stop', 'timeout', 'server_refused'):
            events, children, prefixes = fixture(expected)
            with self.subTest(expected=expected):
                runner.validate_events(events, children, NONCE, prefixes, expected)
                result, logs = record_fixture(expected)
                self.assertTrue(runner.assess_case_record(result, logs))

    def test_socket_ready_or_producer_pass_label_is_not_a_handshake(self):
        result, logs = record_fixture()
        result['events']['server'].pop()
        logs[('server', 'events')] = b''.join(json.dumps(row).encode()+b'\n' for row in result['events']['server'])
        with self.assertRaises(common.Error):
            runner.assess_case_record(result, logs)

    def test_wrong_slice_denied_translation_and_wrong_pages_fail(self):
        for key, value in [('cpu_type', 0x1000007), ('translation_value', 1), ('translation_error', 1),
                           ('translation_error', False), ('kernel_error', 1), ('user_page', 16384),
                           ('vm_page', 16384), ('kernel_page', 4096)]:
            events, children, prefixes = fixture()
            events['loader'][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(common.Error):
                runner.validate_events(events, children, NONCE, prefixes, 'bootstrap_stop')

    def test_nonce_pid_parent_generation_and_prefix_bindings(self):
        for key, value in [('nonce', 'b'*32), ('pid', 999), ('ppid', 999), ('start_sec', 999),
                           ('start_usec', 999), ('generation', 1), ('identity_error', 1),
                           ('identity_error', False), ('prefix_ino', 999), ('prefix_error', 1)]:
            events, children, prefixes = fixture()
            events['loader'][0][key] = value
            with self.subTest(key=key), self.assertRaises(common.Error):
                runner.validate_events(events, children, NONCE, prefixes, 'bootstrap_stop')

    def test_wrong_server_pid_or_generation_rejects_handshake(self):
        for key, value in [('peer_pid', 999), ('server_start', '133000000000000001'), ('server_start', 123)]:
            events, children, prefixes = fixture()
            next(row for row in events['loader'] if row['event'] == 'server_handshake')[key] = value
            with self.subTest(key=key), self.assertRaises(common.Error):
                runner.validate_events(events, children, NONCE, prefixes, 'bootstrap_stop')

    def test_missing_reexec_or_reordered_stop_cannot_pass(self):
        for reorder in (False, True):
            events, children, prefixes = fixture()
            if reorder:
                events['loader'].insert(0, events['loader'].pop())
            else:
                del events['loader'][2]
            with self.subTest(reorder=reorder), self.assertRaises(common.Error):
                runner.validate_events(events, children, NONCE, prefixes, 'bootstrap_stop')

    def test_real_low_mapping_and_null_guard_are_required(self):
        for key, value in [('low_address', 0x20000000), ('region_address', 0), ('region_size', 16384),
                           ('region_protection', 3), ('region_error', 1), ('null_read_error', 0),
                           ('guard_end_read_error', 0), ('pagezero_size', 4096)]:
            events, children, prefixes = fixture()
            next(row for row in events['loader'] if row['event'] == 'memory')[key] = value
            with self.subTest(key=key), self.assertRaises(common.Error):
                runner.validate_events(events, children, NONCE, prefixes, 'bootstrap_stop')

    def test_missing_images_wrong_counts_or_foreign_image_arch_reject(self):
        for key, value in [('index', 2), ('cpu_type', 0x1000007), ('uuid', ''), ('path', 'relative')]:
            events, children, prefixes = fixture()
            next(row for row in events['loader'] if row['event'] == 'image')[key] = value
            with self.subTest(key=key), self.assertRaises(common.Error):
                runner.validate_events(events, children, NONCE, prefixes, 'bootstrap_stop')
        events, children, prefixes = fixture()
        next(row for row in events['loader'] if row['event'] == 'images_end')['count'] = 2
        with self.assertRaisesRegex(common.Error, 'image_count'):
            runner.validate_events(events, children, NONCE, prefixes, 'bootstrap_stop')

    def test_missing_mode_setter_is_a_failure_not_a_fallback_success(self):
        events, children, prefixes = fixture()
        events['loader'][-1].update(event='failure', operation='page_setter', error=78)
        with self.assertRaises(common.Error):
            runner.validate_events(events, children, NONCE, prefixes, 'bootstrap_stop')

    def test_pe_or_foreign_execution_cannot_be_stage2_bootstrap(self):
        for key in ('pe_entered', 'foreign_mode_entered'):
            events, children, prefixes = fixture()
            events['loader'][-1][key] = True
            with self.subTest(key=key), self.assertRaises(common.Error):
                runner.validate_events(events, children, NONCE, prefixes, 'bootstrap_stop')

    def test_timeout_must_be_armed_and_actual_timeout_retained(self):
        result, logs = record_fixture('timeout')
        result['outcome'] = 'exited'
        with self.assertRaisesRegex(common.Error, 'timeout_control_not_triggered'):
            runner.assess_case_record(result, logs)

    def test_cleanup_label_cannot_hide_refusal_gap_or_survivor(self):
        for key, value in [('errors', [{'role': 'loader', 'code': 'signal_refused'}]),
                           ('observation_gap', True), ('reaped', {'server': True, 'loader': False})]:
            result, logs = record_fixture()
            result['cleanup']['complete'] = True
            result['cleanup'][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(common.Error, 'cleanup_incomplete'):
                runner.assess_case_record(result, logs)

    def test_sentinel_signal_or_interference_never_passes(self):
        result, logs = record_fixture()
        result['cleanup']['signals'].append({'role': 'sentinel', 'signal': int(signal.SIGINT)})
        with self.assertRaisesRegex(common.Error, 'cleanup_signal_scope'):
            runner.assess_case_record(result, logs)
        result, logs = record_fixture()
        logs[('sentinel', 'stdout')] = logs[('sentinel', 'stdout')].replace(b'"signal": 0', b'"signal": 2')
        with self.assertRaisesRegex(common.Error, 'unrelated_sentinel_changed'):
            runner.assess_case_record(result, logs)

    def test_event_payload_must_equal_exact_raw_log(self):
        result, logs = record_fixture()
        result['events']['loader'][0]['extra'] = 'tampered'
        with self.assertRaisesRegex(common.Error, 'event_log_mismatch'):
            runner.assess_case_record(result, logs)

    def test_changed_loaded_native_bytes_and_external_images_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ('wine', 'ntdll.so', 'wineserver'):
                # Minimal original Mach-O identity fixture, never executable.
                header = struct.pack('<IIIIIIII', 0xfeedfacf, runner.MACH_ARM64, 0, 2, 1, 24, 0, 0)
                command = struct.pack('<II', 0x1b, 24) + bytes.fromhex('1' * 32)
                (root/name).write_bytes(header + command + name.encode())
            signed = {'entrypoints': {'server': 'wineserver', 'loader': 'wine', 'ntdll': 'ntdll.so'},
                      'native_images': [{'path': name, 'sha256': common.sha256(root/name)}
                                        for name in ('wine', 'ntdll.so', 'wineserver')]}
            image = lambda path: {'event': 'image', 'path': str(path), 'uuid': '1' * 32}
            events = {'server': [image(root/'wineserver')], 'loader': [image(root/'wine'), image(root/'ntdll.so')]}
            runner.validate_native_images(events, root, signed, 'bootstrap_stop')
            events['loader'][0]['uuid'] = '2' * 32
            with self.assertRaisesRegex(common.Error, 'loaded_uuid_mismatch'):
                runner.validate_native_images(events, root, signed, 'bootstrap_stop')
            events['loader'][0]['uuid'] = '1' * 32
            (root/'ntdll.so').write_bytes(b'changed')
            with self.assertRaisesRegex(common.Error, 'unbound_loaded_image'):
                runner.validate_native_images(events, root, signed, 'bootstrap_stop')
            events['loader'] = [image(root/'wine'), image('/external/library.dylib')]
            with self.assertRaisesRegex(common.Error, 'external_loaded_image'):
                runner.validate_native_images(events, root, signed, 'bootstrap_stop')


class RetainedLogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'bootstrap').mkdir()
        self.result, self.raw = record_fixture()
        required = {(role, channel) for role in ('server', 'loader', 'sentinel') for channel in ('stdout', 'stderr')}
        required |= {('loader', 'events'), ('server', 'events')}
        self.result['logs'] = []
        for role, channel in sorted(required):
            data = self.raw.setdefault((role, channel), b'')
            name = role + '.' + channel + '.log'
            (self.root / 'bootstrap' / name).write_bytes(data)
            self.result['logs'].append({'role': role, 'channel': channel, 'path': name,
                'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
                'observed_bytes': len(data), 'eof': True})


    def test_failed_postcheck_preserves_completed_observations_and_new_failed_assessment(self):
        path = self.root / 'bootstrap/case.json'
        self.result['assessment_error'] = None
        path.write_bytes(common.encoded(self.result))
        before = path.read_bytes()
        row = runner.write_case_assessment(self.root, 'bootstrap', self.result, 'unbound_loaded_image')
        self.assertFalse(row['passed'])
        self.assertEqual(path.read_bytes(), before)
        assessment = common.load_json(self.root / row['assessment_path'])
        self.assertFalse(assessment['passed'])
        self.assertEqual(assessment['error'], 'unbound_loaded_image')
        self.assertEqual(assessment['case_sha256'], hashlib.sha256(before).hexdigest())
        with self.assertRaises(FileExistsError):
            runner.write_case_assessment(self.root, 'bootstrap', self.result, None)

    def test_exact_logs_feed_independent_case_assessment(self):
        logs = runner.verify_case_logs(self.root, 'bootstrap', self.result)
        self.assertEqual(logs, self.raw)
        self.assertTrue(runner.assess_case_record(self.result, logs))

    def test_changed_or_missing_bytes_never_use_case_pass_label(self):
        path = self.root / 'bootstrap/loader.stdout.log'
        path.write_bytes(path.read_bytes() + b'changed')
        with self.assertRaisesRegex(common.Error, 'log_integrity_mismatch'):
            runner.verify_case_logs(self.root, 'bootstrap', self.result)
        path.unlink()
        with self.assertRaises(OSError):
            runner.verify_case_logs(self.root, 'bootstrap', self.result)

    def test_symlink_log_cannot_read_unrelated_file(self):
        path = self.root / 'bootstrap/loader.stdout.log'
        private = self.root / 'unrelated'
        private.write_bytes(b'PRIVATE_SECRET_NEVER_READ')
        path.unlink()
        path.symlink_to(private)
        with self.assertRaises(OSError):
            runner.verify_case_logs(self.root, 'bootstrap', self.result)

    def test_missing_duplicate_and_wrong_path_log_entries_reject(self):
        for mutation in ('missing', 'duplicate', 'path', 'eof', 'size'):
            result = copy.deepcopy(self.result)
            if mutation == 'missing':
                result['logs'].pop()
            elif mutation == 'duplicate':
                result['logs'][-1] = result['logs'][0]
            elif mutation == 'path':
                result['logs'][0]['path'] = '../../private'
            elif mutation == 'eof':
                result['logs'][0]['eof'] = False
            else:
                result['logs'][0]['observed_bytes'] += 1
            with self.subTest(mutation=mutation), self.assertRaises(common.Error):
                runner.verify_case_logs(self.root, 'bootstrap', result)

    def test_valid_hash_cannot_hide_truncated_event_line(self):
        log = next(row for row in self.result['logs'] if row['channel'] == 'events')
        path = self.root / 'bootstrap' / log['path']
        data = path.read_bytes().rstrip(b'\n')
        path.write_bytes(data)
        log.update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), observed_bytes=len(data))
        with self.assertRaisesRegex(common.Error, 'truncated_event_log'):
            runner.verify_case_logs(self.root, 'bootstrap', self.result)


class SafetyTests(unittest.TestCase):
    def test_fresh_output_rejects_existing_symlink_and_outside(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            created = runner.create_output('.build/task4/one', root)
            (created/'evidence').write_bytes(b'keep')
            for name in ('.build/task4/one', '.build/task4/../elsewhere', str(root/'outside')):
                with self.subTest(name=name), self.assertRaises(common.Error):
                    runner.create_output(name, root)
            (root/'.build/task4/link').symlink_to(created, target_is_directory=True)
            with self.assertRaises(common.Error):
                runner.create_output('.build/task4/link/new', root)
            self.assertEqual((created/'evidence').read_bytes(), b'keep')

    def test_auth_environment_never_inherited(self):
        with patch.dict(os.environ, {'STEAM_TOKEN': 'PRIVATE', 'WINEPREFIX': '/private/auth',
                                     'DYLD_LIBRARY_PATH': '/private/injection', 'WINESERVERSOCKET': '99'}):
            env = runner.environment(Path('/owned/home'), Path('/owned/prefix'), NONCE)
        self.assertNotIn('PRIVATE', json.dumps(env))
        self.assertNotIn('WINESERVERSOCKET', env)
        self.assertNotIn('DYLD_LIBRARY_PATH', env)
        self.assertEqual(env['HOME'], '/owned/home')
        self.assertEqual(env['WINEPREFIX'], '/owned/prefix')

    def test_bad_cases_cannot_escape_output_or_inflate_bounds(self):
        cases = common.load_json(runner.REPO/'tests/wine/cases.json')
        runner.validate_cases(cases)
        changed = copy.deepcopy(cases)
        changed['cases'][0]['id'] = '../../escape'
        with self.assertRaises(common.Error):
            runner.validate_cases(changed)
        changed = copy.deepcopy(cases)
        changed['bounds']['kill_ms'] = 100000000
        with self.assertRaises(common.Error):
            runner.validate_cases(changed)

    def test_denied_signing_never_spawns_or_creates_output(self):
        denied = SimpleNamespace(validate_prepared=lambda _: (_ for _ in ()).throw(common.Error('grant_denied')))
        with tempfile.TemporaryDirectory() as temp, patch.dict(sys.modules, {'signing': denied}), \
             patch.object(runner.subprocess, 'Popen') as launch:
            with self.assertRaisesRegex(common.Error, 'grant_denied'):
                runner.run('bootstrap', Path(temp), Path(temp)/'never-created', True)
            launch.assert_not_called()
            self.assertFalse((Path(temp)/'never-created').exists())


@unittest.skipUnless(sys.platform == 'darwin' and hasattr(__import__('select'), 'kqueue'),
                     'ordinary native Darwin ownership checks require kqueue')
class OrdinaryLifecycleTests(unittest.TestCase):
    """Real self-owned Python children only; no Wine/signing-grant simulation."""
    BOUNDS = {'grace_ms': 300, 'terminate_ms': 300, 'kill_ms': 1000, 'drain_ms': 300}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.session = runner.Session(self.output)

    def child(self, role, code, events=False):
        # Use the actual framework image; Homebrew's bin/python launcher self-execs.
        executable = self.session.observer.executable(os.getpid())
        return self.session.launch(role, [executable, '-c', code],
                                   {'PATH': '/usr/bin:/bin'}, event_pipe=events)

    def finish(self, roles):
        cleanup = self.session.cleanup(roles, self.BOUNDS)
        self.session.finish_logs(self.BOUNDS['drain_ms'])
        return cleanup



    def test_late_drain_and_observer_close_failures_preserve_bounded_logs(self):
        child = self.child('loader', 'import time; print("owned-evidence",flush=True); time.sleep(.05)')
        self.assertTrue(self.session.wait_for(lambda: child.exited, 3))
        self.assertTrue(self.session.cleanup(('loader',), self.BOUNDS)['complete'])
        # Force one final drain iteration even when this fast child already gave EOF.
        with patch.object(self.session.selector, 'get_map', return_value={'synthetic': True}), \
             patch.object(self.session, 'pump', side_effect=common.Error('synthetic_drain_failure')), \
             patch.object(self.session.observer, 'close', side_effect=OSError('synthetic close failure')):
            logs = self.session.finish_logs(100)
        self.session.observer.queue.close()
        self.assertEqual(self.session.failure, 'synthetic_drain_failure')
        self.assertEqual((self.output/'loader.stdout.log').read_bytes(), b'owned-evidence\n')
        self.assertEqual(len(logs), 2)
        self.assertTrue(child.reaped)
        self.assertTrue(child.process.stdout.closed)
        self.assertTrue(child.process.stderr.closed)

    def test_interrupt_before_spawn_still_writes_failed_case_record(self):
        # Exercise interruption reporting only: launch is interrupted before Popen.
        # There is no fake signing grant or Wine process in this test.
        self.session.selector.close()
        self.session.observer.close()
        case = {'id': 'bootstrap', 'mode': 'normal', 'timeout_ms': 120000, 'expected': 'bootstrap_stop'}
        paths = {'loader': 'wine', 'server': 'wineserver', 'bootstrap_helper': 'helper', 'sentinel': 'sentinel'}
        with patch.object(runner.Session, 'launch', side_effect=KeyboardInterrupt), \
             patch.object(runner.subprocess, 'Popen') as launch:
            result = runner.run_case(case, self.output, paths, self.output / 'interrupted', self.BOUNDS)
            launch.assert_not_called()
        self.assertEqual(result['outcome'], 'interrupted')
        self.assertEqual(result['error'], 'runner_interrupted')
        self.assertFalse(result['passed'])
        self.assertEqual(common.load_json(self.output/'interrupted/case.json'), result)

    def test_real_exit_is_observed_before_reap_and_other_child_survives(self):
        sentinel = self.child('sentinel', 'import time; time.sleep(30)')
        owned = self.child('loader', 'import time; print("owned",flush=True); time.sleep(.1)')
        self.assertTrue(self.session.wait_for(lambda: owned.exited, 3))
        self.assertFalse(owned.reaped)
        self.assertIsNone(owned.process.returncode)
        cleanup = self.session.cleanup(('loader',), self.BOUNDS)
        self.assertTrue(cleanup['complete'])
        self.assertEqual(owned.exit_code, 0)
        self.assertFalse(sentinel.exited)
        self.assertEqual(self.session.observer.identity(sentinel.pid), sentinel.identity)
        self.assertTrue(self.finish(('sentinel',))['complete'])

    def test_real_timeout_cleanup_reaps_only_owned_child(self):
        child = self.child('loader', 'import time; time.sleep(30)')
        self.assertFalse(self.session.wait_for(lambda: child.exited, .08))
        self.assertTrue(self.finish(('loader',))['complete'])
        self.assertTrue(child.reaped)

    def test_real_output_limit_is_bounded_and_cleanup_completes(self):
        child = self.child('loader', 'import os,time; os.write(1,b"x"*400000); time.sleep(30)')
        with self.assertRaisesRegex(common.Error, 'output_limit'):
            self.session.wait_for(lambda: child.exited, 3)
        self.assertTrue(self.finish(('loader',))['complete'])
        self.assertLessEqual((self.output/'loader.stdout.log').stat().st_size, runner.STREAM_LIMIT+1)

    def test_real_spawn_error_has_no_synthetic_child(self):
        with self.assertRaisesRegex(common.Error, 'spawn_error'):
            self.session.launch('loader', ['/no/such/pear-owned-fixture'], {}, event_pipe=True)
        self.assertEqual(self.session.children, {})
        self.assertTrue(self.finish(())['complete'])

    def test_event_pipe_parser_rejects_duplicate_keys(self):
        code = 'import os,time; os.write(int(os.environ["PEAR_BOOTSTRAP_FD"]),b\'{"version":1,"version":2}\\n\'); time.sleep(30)'
        child = self.child('loader', code, events=True)
        with self.assertRaisesRegex(common.Error, 'invalid_event'):
            self.session.wait_for(lambda: child.exited, 3)
        self.assertTrue(self.finish(('loader',))['complete'])



    def test_forked_owned_group_member_is_terminated_without_harming_sentinel(self):
        sentinel = self.child('sentinel', 'import time; time.sleep(30)')
        code = ('import os,time; time.sleep(.05); pid=os.fork(); '
                'print("owned-fork",flush=True); time.sleep(.1 if pid else 30)')
        leader = self.child('loader', code)
        deadline = time.monotonic() + 3
        while not leader.exited and time.monotonic() < deadline:
            self.session.pump()
        self.assertTrue(leader.exited)
        self.assertTrue(self.session.observer.group_members(leader))
        cleanup = self.session.cleanup(('loader',), self.BOUNDS)
        self.assertTrue(leader.reaped)
        self.assertTrue(cleanup['observation_gap'])
        self.assertFalse(cleanup['complete'])
        self.assertNotIn('owned_group_survivor', [row['code'] for row in cleanup['errors']])
        self.assertFalse(sentinel.exited)
        self.assertEqual(self.session.observer.identity(sentinel.pid), sentinel.identity)
        self.assertTrue(self.finish(('sentinel',))['complete'])

    def test_observer_setup_failure_terminates_and_reaps_owned_child(self):
        with patch.object(self.session.observer, 'add', side_effect=common.Error('synthetic_observer_failure')):
            with self.assertRaisesRegex(common.Error, 'launch_observation_setup_failed'):
                self.child('loader', 'import time; time.sleep(30)', events=True)
        child = self.session.children['loader']
        self.assertTrue(child.reaped)
        self.assertTrue(child.emergency_cleanup['reaped'])
        self.assertFalse(self.finish(('loader',))['complete'])

    def test_first_and_second_pipe_registration_failure_close_all_streams(self):
        # A separate session per fault ensures the evidence paths are exclusive.
        for failure_at in (1, 2, 3):
            with self.subTest(failure_at=failure_at):
                if failure_at > 1:
                    directory = self.output / str(failure_at)
                    directory.mkdir()
                    self.session = runner.Session(directory)
                original = self.session.add_stream
                calls = 0
                def fail_pipe(role, channel, stream):
                    nonlocal calls
                    calls += 1
                    if calls == failure_at:
                        raise OSError('synthetic pipe setup failure')
                    return original(role, channel, stream)
                with patch.object(self.session, 'add_stream', side_effect=fail_pipe):
                    with self.assertRaisesRegex(common.Error, 'launch_observation_setup_failed'):
                        self.child('loader', 'import time; time.sleep(30)', events=True)
                child = self.session.children['loader']
                self.assertTrue(child.reaped)
                self.assertTrue(child.process.stdout.closed)
                self.assertTrue(child.process.stderr.closed)
                self.assertFalse(self.session.selector.get_map())
                self.assertFalse(self.finish(('loader',))['complete'])

    def test_fast_exit_after_observer_failure_reaped_once_without_signaling_reused_pid(self):
        def failed_add(child):
            time.sleep(.05)
            raise common.Error('synthetic_late_observer_failure')
        with patch.object(self.session.observer, 'add', side_effect=failed_add):
            with self.assertRaisesRegex(common.Error, 'launch_observation_setup_failed'):
                self.child('loader', 'pass')
        child = self.session.children['loader']
        self.assertTrue(child.reaped)
        self.assertEqual(child.exit_code, 0)
        self.assertEqual(child.emergency_cleanup['signals'], [])
        self.assertFalse(self.finish(('loader',))['complete'])

    def test_refused_signal_is_reported_even_after_safe_recovery(self):
        child = self.child('loader', 'import time; time.sleep(30)')
        original = self.session.observer.signal_owned
        calls = 0
        def refused_once(target, number):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise PermissionError('Synthetic owned signal refusal')
            return original(target, number)
        with patch.object(self.session.observer, 'signal_owned', side_effect=refused_once):
            cleanup = self.finish(('loader',))
        self.assertFalse(cleanup['complete'])
        self.assertTrue(child.reaped)
        self.assertEqual(cleanup['errors'], [{'role': 'loader', 'code': 'signal_refused'}])


if __name__ == '__main__':
    unittest.main()
