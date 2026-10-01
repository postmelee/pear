"""Public evidence excludes private fields and cannot turn a failed build into success."""
import json
import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
from common import Error, encoded
import evidence


class FailedBuildExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.path = self.root / '.build/task4/attempt.json'
        self.path.parent.mkdir(parents=True)
        patcher = mock.patch.object(evidence, 'REPO', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.value = {'schema_version': 1, 'record_kind': 'wine_build', 'scope': 'wine_component',
                      'variant': 'arm64', 'passed': False, 'wine_runtime_execution': False,
                      'error': 'build_command_failed:configure', 'private_error': 'PRIVATE_SECRET',
                      'commands': [{'id': 'configure', 'exit_code': 1, 'timed_out': False,
                                    'output_limit': False, 'argv': ['PRIVATE_SECRET'],
                                    'stdout': 'PRIVATE_SECRET', 'cwd': '/Users/PRIVATE_SECRET'}]}

    def export(self):
        self.path.write_bytes(encoded(self.value))
        return evidence.summarize_build_attempt(self.path)

    def test_only_allowlisted_failure_fields_are_public(self):
        result = self.export()
        self.assertNotIn('PRIVATE_SECRET', json.dumps(result))
        self.assertEqual(result['commands'], [{'id': 'configure', 'exit_code': 1,
                                              'timed_out': False, 'output_limit': False}])
        self.assertFalse(result['passed'])
        self.value['error'] = '/Users/PRIVATE_SECRET'
        self.assertEqual(self.export()['error'], 'unclassified_build_failure')

    def test_wrong_scope_success_and_private_values_in_boolean_fields_reject(self):
        for field, value in [('passed', True), ('wine_runtime_execution', True), ('variant', 'PRIVATE_SECRET')]:
            previous = self.value[field]
            self.value[field] = value
            with self.subTest(field=field), self.assertRaises(Error):
                self.export()
            self.value[field] = previous
        self.value['commands'][0]['timed_out'] = 'PRIVATE_SECRET'
        with self.assertRaises(Error):
            self.export()

    def test_undeclared_command_name_rejects(self):
        self.value['commands'][0]['id'] = 'PRIVATE_SECRET'
        with self.assertRaises(Error):
            self.export()


class FailedRunExportTests(unittest.TestCase):
    """Synthetic private records and real bounded files; no signing or Wine calls."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.failed = self.root / '.build/task4/failed'
        self.failed.mkdir(parents=True)
        self.runtime = self.root / '.build/task4/signed-old'
        self.runtime.mkdir()
        patcher = mock.patch.object(evidence, 'REPO', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.producers = {}
        for name in evidence.FAILED_RUN_SOURCES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            data = ('Original synthetic producer ' + name).encode()
            path.write_bytes(data)
            self.producers[name] = hashlib.sha256(data).hexdigest()
        signer = {}
        for name in ('signing.py', 'common.py'):
            data = ('Original synthetic signing producer ' + name).encode()
            (self.root/'tools/wine'/name).write_bytes(data)
            signer[name] = hashlib.sha256(data).hexdigest()
        signed = {'schema_version': 1, 'record_kind': 'wine_signed_runtime',
                  'wine_execution': False, 'runtime_qualified': False, 'producer_sha256': signer,
                  'private_profile': 'PRIVATE_SECRET', 'private_path': '/Users/PRIVATE_SECRET'}
        signed_raw = encoded(signed)
        (self.runtime/'signed.json').write_bytes(signed_raw)
        self.value = {'schema_version': 1, 'record_kind': 'wine_bootstrap_run', 'suite': 'bootstrap',
                      'passed': False, 'pe_executed': False, 'runtime_qualified': False, 'error': None,
                      'producer_sha256': self.producers, 'runner_sha256': self.producers['tools/wine/run_fixtures.py'],
                      'cases_sha256': self.producers['tests/wine/cases.json'],
                      'runtime_path': '.build/task4/signed-old', 'signed_sha256': hashlib.sha256(signed_raw).hexdigest(),
                      'cases': []}
        self.cases = {}
        expected = [('normal', 120000, 'bootstrap_stop'), ('hold', 1500, 'timeout'),
                    ('wrong-prefix', 30000, 'server_refused')]
        for case_id, (mode, timeout, terminal) in zip(evidence.FAILED_CASES, expected):
            directory = self.failed/case_id
            directory.mkdir()
            server_events = [{'role': 'server', 'event': 'server_ready', 'pid': 998877,
                              'nonce': 'PRIVATE_SECRET', 'path': '/Users/PRIVATE_SECRET'}]
            case = {'schema_version': 1, 'record_kind': 'wine_bootstrap_case',
                    'case': {'id': case_id, 'mode': mode, 'timeout_ms': timeout, 'expected': terminal},
                    'passed': False, 'pe_executed': False, 'runtime_qualified': False,
                    'error': None, 'stream_error': None, 'outcome': 'exited',
                    'assessment_error': 'missing_process_events', 'elapsed_ms': 1500,
                    'nonce': 'PRIVATE_SECRET', 'private_path': '/Users/PRIVATE_SECRET',
                    'events': {'loader': [], 'server': server_events},
                    'cleanup': {'complete': True, 'errors': [], 'observation_gap': False,
                                'reaped': {'loader': True, 'server': True},
                                'signals': [{'role': 'server', 'signal': 2}]},
                    'sentinel_cleanup': {'complete': True, 'errors': [], 'observation_gap': False,
                                         'reaped': {'sentinel': True}, 'signals': []},
                    'sentinel_survived': True,
                    'processes': {role: {'exit_code': -10 if role == 'loader' else 0, 'reaped': True,
                                        'fork_seen': False, 'identity': {'pid': 998877},
                                        'allowed_paths': ['/Users/PRIVATE_SECRET']}
                                  for role in ('loader', 'server', 'sentinel')}, 'logs': []}
            for role in ('loader', 'server', 'sentinel'):
                channels = ('stdout', 'stderr', 'events') if role != 'sentinel' else ('stdout', 'stderr')
                for channel in channels:
                    data = (b''.join(encoded(row) for row in server_events) if channel == 'events' and role == 'server'
                            else b'' if channel == 'events' else b'PRIVATE_SECRET')
                    # Event records are actual one-line JSONL; encoded() is a pretty document.
                    if channel == 'events' and role == 'server':
                        data = b''.join(json.dumps(row).encode()+b'\n' for row in server_events)
                    name = role + '.' + channel + '.log'
                    (directory/name).write_bytes(data)
                    case['logs'].append({'role': role, 'channel': channel, 'path': name,
                        'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
                        'observed_bytes': len(data), 'eof': True, 'write_error': None})
            self.cases[case_id] = case
            self.write_case(case_id)
        self.write_run()

    def write_case(self, case_id):
        raw = encoded(self.cases[case_id])
        (self.failed/case_id/'case.json').write_bytes(raw)
        digest = hashlib.sha256(raw).hexdigest()
        assessment = {'schema_version': 1, 'record_kind': 'wine_case_gate_assessment',
                      'case_sha256': digest, 'passed': False,
                      'error': self.cases[case_id]['assessment_error']}
        assessment_raw = encoded(assessment)
        (self.failed/case_id/'assessment.json').write_bytes(assessment_raw)
        row = {'id': case_id, 'path': case_id+'/case.json', 'sha256': digest, 'passed': False,
               'assessment_path': case_id+'/assessment.json',
               'assessment_sha256': hashlib.sha256(assessment_raw).hexdigest()}
        self.value['cases'] = [existing for existing in self.value['cases'] if existing['id'] != case_id] + [row]
        self.value['cases'].sort(key=lambda row: evidence.FAILED_CASES.index(row['id']))

    def write_run(self):
        (self.failed/'run.json').write_bytes(encoded(self.value))

    def export(self):
        self.write_run()
        return evidence.summarize_failed_run(self.failed)

    def test_complete_failed_history_preserves_hashes_counts_and_signal_without_private_data(self):
        result = self.export()
        self.assertEqual(result['record_status'], 'complete')
        self.assertFalse(result['passed'])
        self.assertEqual(result['retained_case_count'], 3)
        self.assertNotIn('PRIVATE_SECRET', json.dumps(result))
        self.assertNotIn('998877', json.dumps(result))
        self.assertNotIn('/Users/', json.dumps(result))
        for case in result['cases']:
            self.assertEqual(case['retained_event_counts'], {'loader': 0, 'server': 1})
            self.assertEqual(len(case['logs']), 8)
            self.assertEqual(next(row['exit_code'] for row in case['processes'] if row['role'] == 'loader'), -10)
            self.assertTrue(case['cleanup']['complete'])
            self.assertTrue(case['reported_sentinel_survived'])

    def test_private_failure_string_is_classified_not_exported(self):
        case = self.cases['bootstrap']
        case['error'] = '/Users/PRIVATE_SECRET'
        case['assessment_error'] = 'PRIVATE_SECRET'
        self.write_case('bootstrap')
        result = self.export()['cases'][0]
        self.assertEqual(result['error'], 'unclassified_native_failure')
        self.assertEqual(result['assessment_error'], 'unclassified_native_failure')
        self.assertNotIn('PRIVATE_SECRET', json.dumps(result))

    def test_changed_raw_case_log_or_gate_assessment_reject(self):
        for leaf, code in [('case.json', 'failed_case_changed'), ('loader.stdout.log', 'failed_log_changed'),
                           ('assessment.json', 'failed_assessment_changed')]:
            path = self.failed/'bootstrap'/leaf
            before = path.read_bytes()
            path.write_bytes(before+b' ')
            with self.subTest(leaf=leaf), self.assertRaisesRegex(Error, code):
                self.export()
            path.write_bytes(before)

    def test_missing_records_remain_explicitly_partial_never_passed(self):
        (self.failed/'bootstrap/case.json').unlink()
        (self.failed/'bootstrap-timeout/assessment.json').unlink()
        (self.failed/'wrong-prefix-server/loader.stdout.log').unlink()
        result = self.export()
        self.assertEqual(result['record_status'], 'partial')
        self.assertFalse(result['passed'])
        self.assertIn('case_record', result['cases'][0]['missing_records'])
        self.assertIn('gate_assessment', result['cases'][1]['missing_records'])
        self.assertIn('loader_stdout', result['cases'][2]['missing_records'])

    def test_missing_run_has_no_claimed_hash_or_case_results(self):
        (self.failed/'run.json').unlink()
        result = evidence.summarize_failed_run(self.failed)
        self.assertEqual(result['missing_records'], ['run_record'])
        self.assertIsNone(result['run_sha256'])
        self.assertEqual(result['cases'], [])
        self.assertFalse(result['passed'])

    def test_old_source_archive_is_verified_without_current_signing_gate(self):
        original = (self.root/'tools/wine/signing.py').read_bytes()
        archive = self.root/'.build/task4/signing-revisions/initial'
        archive.mkdir(parents=True)
        (archive/'signing.py').write_bytes(original)
        (self.root/'tools/wine/signing.py').write_bytes(b'changed current source')
        self.assertEqual(self.export()['record_status'], 'complete')
        (archive/'signing.py').unlink()
        result = self.export()
        self.assertEqual(result['record_status'], 'partial')
        self.assertIn('source_signer', result['missing_records'])

    def test_unknown_duplicate_and_out_of_order_case_ids_reject(self):
        original = copy.deepcopy(self.value['cases'])
        for mutation in ('unknown', 'duplicate', 'order'):
            self.value['cases'] = copy.deepcopy(original)
            if mutation == 'unknown':
                self.value['cases'][0]['id'] = 'PRIVATE_SECRET'
            elif mutation == 'duplicate':
                self.value['cases'][1] = self.value['cases'][0]
            else:
                self.value['cases'].reverse()
            with self.subTest(mutation=mutation), self.assertRaisesRegex(Error, 'failed_case_scope'):
                self.export()

    def test_string_values_in_public_boolean_fields_are_rejected(self):
        mutations = [lambda c: c.update(sentinel_survived='PRIVATE_SECRET'),
                     lambda c: c['cleanup'].update(complete='PRIVATE_SECRET'),
                     lambda c: c['cleanup'].update(observation_gap='PRIVATE_SECRET'),
                     lambda c: c['processes']['loader'].update(reaped='PRIVATE_SECRET'),
                     lambda c: c['processes']['loader'].update(fork_seen='PRIVATE_SECRET'),
                     lambda c: c['logs'][0].update(eof='PRIVATE_SECRET')]
        original = copy.deepcopy(self.cases['bootstrap'])
        for index, mutate in enumerate(mutations):
            self.cases['bootstrap'] = copy.deepcopy(original)
            mutate(self.cases['bootstrap'])
            self.write_case('bootstrap')
            with self.subTest(index=index), self.assertRaises(Error):
                self.export()

    def test_success_wrong_scope_unsafe_root_and_symlink_log_reject(self):
        for key in ('passed', 'runtime_qualified', 'pe_executed'):
            self.value[key] = True
            with self.subTest(key=key), self.assertRaisesRegex(Error, 'failed_run_scope'):
                self.export()
            self.value[key] = False
        with self.assertRaisesRegex(Error, 'failed_run_outside_task'):
            evidence.summarize_failed_run(self.root/'outside')
        log = self.failed/'bootstrap/loader.stdout.log'
        log.unlink()
        log.symlink_to(self.root/'tools/wine/common.py')
        with self.assertRaises(OSError):
            self.export()

    def test_partial_case_references_are_reported_in_fixed_known_order(self):
        self.value['cases'] = self.value['cases'][:1]
        result = self.export()
        self.assertEqual([case['case'] for case in result['cases']], list(evidence.FAILED_CASES))
        self.assertEqual(result['cases'][1]['missing_records'], ['case_reference'])
        self.assertFalse(result['passed'])
        self.assertEqual(result['record_status'], 'partial')

    def test_raw_event_count_cannot_be_changed_without_matching_log_bytes(self):
        self.cases['bootstrap']['events']['server'].append({'event': 'invented'})
        self.write_case('bootstrap')
        with self.assertRaisesRegex(Error, 'failed_event_log_mismatch'):
            self.export()


if __name__ == '__main__':
    unittest.main()
