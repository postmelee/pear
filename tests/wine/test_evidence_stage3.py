"""Synthetic exporter gates; no Wine execution or simulated authorization calls.

Mocks stand only for already validated private records. These tests cover
cross-record identity and public-field selection, not any execution claim.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
import abi_review
import arena_evidence
import api_runner
import evidence
import signing
from common import Error, encoded


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


class Stage3ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.build = self.root / '.build/task4/build'
        self.runtime = self.root / '.build/task4/signed'
        self.api_root = self.root / '.build/task4/api'
        self.bootstrap_root = self.root / '.build/task4/bootstrap'
        for path in (self.build, self.runtime, self.api_root, self.bootstrap_root):
            path.mkdir(parents=True)
        patcher = mock.patch.object(evidence, 'REPO', self.root)
        patcher.start(); self.addCleanup(patcher.stop)
        for name in evidence.STAGE3_SOURCES.values():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Original synthetic source: ' + name)
        self.built = {'schema_version': 1, 'record_kind': 'wine_build', 'variant': 'arm64',
            'fixture_suite': 'api-abi', 'code_publication_policy': 'page-wx', 'passed': True, 'native_artifact_count': 38, 'pe_artifact_count': 750,
            'patches': [{'path': 'PRIVATE_SECRET', 'sha256': 'a'*64}],
            'sdk': {'version': '26.5', 'canonical_name': 'macosx26.5', 'settings_sha256': 'b'*64,
                    'resolved_path': '/Users/PRIVATE_SECRET'},
            'commands': [{'id': 'make', 'exit_code': 0, 'timed_out': False, 'output_limit': False,
                          'argv': ['/Users/PRIVATE_SECRET'], 'stdout': 'PRIVATE_SECRET'}],
            'private': {'device': 'PRIVATE_SECRET', 'pid': 998877}}
        self.artifacts = {'files': [{'kind': kind, 'path': '/Users/PRIVATE_SECRET'}
            for kind, count in [('macho', 38), ('pe', 750), ('pe_metadata', 10)] for _ in range(count)]}
        roles = ['api-launch-helper', 'bootstrap-helper', 'sentinel', 'wine-loader', 'wine-server', 'wine-wrapper']
        roles += ['native-helper'] * 6 + ['native-library'] * 26
        self.signed = {'schema_version': 1, 'record_kind': 'wine_signed_runtime',
            'authorization_scope': 'development_windows_api_abi_fixtures',
            'code_publication_policy': 'page-wx',
            'distribution_qualified': False, 'runtime_qualified': False,
            'build_ref': {'path': str(self.build / 'build.json'), 'sha256': digest(self.built)},
            'profile_checks': {key: True for key in evidence.PROFILE_CHECKS},
            'native_images': [{'role': role, 'path': '/Users/PRIVATE_SECRET', 'pid': 998877,
                'signature': {'hardened_runtime': True, 'same_team': True, 'strict_verification': True,
                    'ad_hoc': False, 'category': 'apple_development', 'code_directory_page_size': 4096,
                    'claim_keys': sorted([signing.APP_ID, signing.TEAM_ID, sorted(signing.CROSS_KEYS)[0],
                                          'com.apple.security.cs.allow-jit'])
                                  if role == 'wine-loader' else [], 'team': 'PRIVATE_SECRET'}} for role in roles],
            'private_profile': 'PRIVATE_SECRET'}
        self.review = {'schema_version': 1, 'record_kind': 'wine_abi_assembly_review',
            'analysis_passed': True, 'gate_passed': True, 'reader_reproduced': True,
            'binary_binding': 'verified', 'runtime_execution': False, 'trusted_reader_required': True,
            'build_sha256': digest(self.built), 'binary_sha256': 'c'*64, 'disassembly_sha256': 'd'*64,
            'reader_sha256': 'e'*64, 'instruction_bytes_checked': 10000,
            'entries': [{'entry': name, 'required_entry_mode': first, 'required_return_mode': last,
                        'reachable_instruction_states': 100, 'terminal_paths': 2, 'x18_only_foreign': True,
                        'ordinary_calls_only_host': True, 'private': '/Users/PRIVATE_SECRET'}
                        for name, (first, last) in abi_review.ENTRIES.items()],
            'helpers': [{'entry': name, 'requested_mode': mode, 'instruction_count': 88,
                         'api_sequence': ['getter', 'setter', 'getter'], 'pointer_symbols_bound': True,
                         'register_spills_checked': True, 'ordinary_calls': 0, 'private': 'PRIVATE_SECRET'}
                        for name, mode in abi_review.HELPERS.items()],
            'private_disassembly': 'PRIVATE_SECRET'}
        self.api_record = {'schema_version': 1, 'record_kind': 'wine_api_run',
                           'runtime_path': '.build/task4/signed', 'signed_sha256': digest(self.signed)}
        self.bootstrap_record = {'schema_version': 1, 'record_kind': 'wine_bootstrap_run',
                                 'runtime_path': '.build/task4/signed', 'signed_sha256': digest(self.signed)}
        self.api = {'passed': True, 'case_count': 2, 'pe_executed': True, 'runtime_qualified': False,
            'environment_policy': dict(api_runner.ENVIRONMENT_POLICY),
            'run_sha256': digest(self.api_record), 'signed_sha256': digest(self.signed),
            'code_publication_policy': 'page-wx',
            'cases': [{'id': name, 'case_sha256': 'f'*64, 'passed': True, 'native_processes': 8,
                       'pe_processes': 3, 'code_publication_policy': 'page-wx',
                       'environment_policy': dict(api_runner.ENVIRONMENT_POLICY),
                       'arena_observations': [{'role': role, 'policy': 'page-wx', 'publications': 34,
                           'retirements': 32, 'compatible_reuses': 31, 'published_code_pages': 100,
                           'published_data_pages': 100, 'relocations': 100, 'live_images_at_last_observation': 2}
                          for role in ('loader', 'process-01', 'process-02')],
                       'fixture_results': copy.deepcopy(api_runner.expected_fixture_rows(name)),
                       'cleanup_complete': True, 'sentinel_survived': True, 'pid': 998877,
                       'raw_log': 'PRIVATE_SECRET'} for name in ('api', 'abi')],
            'controls': [{'role': role, 'machine': machine, 'sha256': 'a'*64,
                          'executed': False, 'accepted': False, 'reason': 'translator-not-qualified-for-target',
                          'path': '/Users/PRIVATE_SECRET'}
                          for role, machine in [('x64_control', 'x86_64'), ('i386_control', 'i386')]],
            'private': 'PRIVATE_SECRET'}
        self.api['cases'][1]['relocation_observations'] = {
            'fixture_sha256': 'a' * 64, 'placements': 2, 'copied_files_verified': 2,
            'relocated_pointer_slots': 4, 'probe_calls_verified': 4, 'retirements_verified': 2,
            'simultaneous_live': True, 'distinct_bases': True, 'distinct_slots': True,
            'nonzero_deltas': True, 'original_pointer_rvas_verified': True,
            'code_targets_verified': True, 'data_isolation_verified': True,
            'security_cookie_images': 2, 'security_cookie_observations': 4,
            'security_cookie_initialized': True, 'security_cookie_stable': True,
            'security_cookie_destination_verified': True, 'security_cookie_load_config_verified': True,
            'private_path': '/Users/PRIVATE_SECRET', 'private_address': 998877}
        self.bootstrap = {'passed': True, 'case_count': 3, 'pe_executed': False, 'runtime_qualified': False,
            'run_sha256': digest(self.bootstrap_record), 'signed_sha256': digest(self.signed),
            'cases': [{'id': name, 'case_sha256': 'b'*64, 'expected': expected, 'outcome': outcome,
                       'passed': True, 'native_process_count': 3, 'reexecution_count': 1,
                       'actual_handshake': expected != 'server_refused', 'cleanup_complete': True,
                       'sentinel_survived': True, 'raw': 'PRIVATE_SECRET'}
                       for name, expected, outcome in zip(evidence.FAILED_CASES,
                            ('bootstrap_stop', 'timeout', 'server_refused'), ('exited', 'timeout', 'exited'))]}
        # Small synthetic receipts exercise packaging only. The native receipt
        # parser has separate raw-stream, crash and identity rejection tests.
        native_source = self.root / 'tests/wine/fixtures/pe_arena_native.c'
        native_source.parent.mkdir(parents=True, exist_ok=True)
        native_source.write_text('Synthetic native source; never compiled or executed.')
        self.native_roots, self.native_receipts = [], {}
        sources = [source for _, source in evidence.NATIVE_ARENA_FAILURES] + [
            hashlib.sha256(native_source.read_bytes()).hexdigest()]
        for index, source in enumerate(sources):
            root = self.root / '.build/task4' / ('native-' + str(index))
            root.mkdir()
            self.native_roots.append(root)
            policy = 'thread-jit' if index < 2 else 'page-wx'
            modes = ('lifecycle', 'protected-write', 'retired-call', 'data-exec',
                     'writer-exec' if index < 2 else 'preparation-exec')
            receipt = {'schema_version': 1, 'record_kind': 'pear_native_arena_observations',
                'scope': 'historical_native_prerequisite_receipt', 'policy': policy,
                'source_sha256': source, 'report_sha256': str(index + 1) * 64,
                'legacy_policy_interpretation': index < 2, 'native_prerequisite_passed': index == 2,
                'wine_execution': False, 'runtime_qualified': False, 'game_qualified': False,
                'authorization': arena_evidence.authorization_receipt(index < 2),
                'cases': [{'variant': variant, 'mode': mode, 'policy': policy, 'passed': index == 2,
                           'cleanup_complete': True, 'sentinel_survived': True}
                          for variant, mode in [('original-claims', 'lifecycle')] +
                               [('allow-jit', mode) for mode in modes]]}
            self.native_receipts[root] = receipt
            (root / evidence.NATIVE_ARENA_RECEIPT).write_bytes(encoded(receipt))
        patcher = mock.patch('arena_evidence.export', side_effect=lambda root: self.native_receipts[root])
        self.native_validator = patcher.start(); self.addCleanup(patcher.stop)
        self.write_records()
        mocks = [('build.verify_build', self.built), ('build.artifact_inventory', self.artifacts),
                 ('api_runner.validate_runs', self.api), ('run_fixtures.validate_runs', self.bootstrap),
                 ('signing.validate_prepared', self.signed), ('abi_review.inspect_build', self.review)]
        self.mocks = {}
        for name, value in mocks:
            patcher = mock.patch(name, return_value=value)
            self.mocks[name] = patcher.start(); self.addCleanup(patcher.stop)

    def write_records(self):
        for path, value in [(self.build/'build.json', self.built), (self.runtime/'signed.json', self.signed),
                            (self.build/'abi-review.json', self.review), (self.api_root/'run.json', self.api_record),
                            (self.bootstrap_root/'run.json', self.bootstrap_record)]:
            path.write_bytes(encoded(value))

    def rebind_signed(self):
        value = digest(self.signed)
        self.api_record['signed_sha256'] = self.bootstrap_record['signed_sha256'] = value
        self.api['signed_sha256'] = self.bootstrap['signed_sha256'] = value
        self.api['run_sha256'] = digest(self.api_record)
        self.bootstrap['run_sha256'] = digest(self.bootstrap_record)
        self.write_records()

    def export(self):
        return evidence.export_stage3(self.build, self.api_root, self.bootstrap_root,
                                      native_arena_runs=self.native_roots)

    def test_actual_validated_summaries_are_allowlisted_without_private_data(self):
        value = self.export()
        text = json.dumps(value)
        for private in ('PRIVATE_SECRET', '/Users/', str(self.root), '998877', 'argv', 'raw_log'):
            self.assertNotIn(private, text)
        self.assertEqual(value['authorization']['native_images_signed'], 38)
        self.assertEqual(value['build']['metadata_container_count'], 10)
        self.assertEqual(value['run_assessments']['api_abi']['cases'][1]['fixture_results'], api_runner.expected_fixture_rows('abi'))
        self.assertEqual(len(value['assembly_review']['entries']), 6)
        self.assertTrue(value['pe_execution'])
        self.assertFalse(value['translator_execution'])
        self.assertFalse(value['distribution_qualified'])
        self.assertEqual(self.mocks['signing.validate_prepared'].call_count, 2)

    def test_two_actual_relocation_placements_are_required_and_sanitized(self):
        cases = self.export()['run_assessments']['api_abi']['cases']
        self.assertNotIn('relocation_observations', cases[0])
        observed = cases[1]['relocation_observations']
        expected = {key: value for key, value in self.api['cases'][1]['relocation_observations'].items()
                    if not key.startswith('private_')}
        self.assertEqual(observed, expected)
        saved = self.api['cases'][1].pop('relocation_observations')
        with self.assertRaisesRegex(Error, 'export_relocation_missing'):
            self.export()
        self.api['cases'][1]['relocation_observations'] = saved
        self.api['cases'][0]['relocation_observations'] = saved
        with self.assertRaisesRegex(Error, 'export_relocation_scope'):
            self.export()
        del self.api['cases'][0]['relocation_observations']

    def test_relocation_receipt_requires_exact_counts_and_actual_proof_flags(self):
        observed = self.api['cases'][1]['relocation_observations']
        for key in ('placements', 'copied_files_verified', 'relocated_pointer_slots',
                    'probe_calls_verified', 'retirements_verified', 'security_cookie_images',
                    'security_cookie_observations'):
            saved = observed[key]
            for invalid in (saved - 1, saved + 1, float(saved), True, None):
                observed[key] = invalid
                with self.subTest(key=key, invalid=invalid), self.assertRaisesRegex(Error, 'export_relocation_count'):
                    self.export()
            observed[key] = saved
        for key in ('simultaneous_live', 'distinct_bases', 'distinct_slots', 'nonzero_deltas',
                    'original_pointer_rvas_verified', 'code_targets_verified', 'data_isolation_verified',
                    'security_cookie_initialized', 'security_cookie_stable',
                    'security_cookie_destination_verified', 'security_cookie_load_config_verified'):
            for invalid in (False, 1, None):
                observed[key] = invalid
                with self.subTest(key=key, invalid=invalid), self.assertRaisesRegex(Error, 'export_relocation_proof'):
                    self.export()
            observed[key] = True
        observed['fixture_sha256'] = '/Users/PRIVATE_SECRET'
        with self.assertRaisesRegex(Error, 'failed_run_digest_shape'):
            self.export()


    def test_cookie_details_remain_private_and_cookie_proof_cannot_be_omitted(self):
        observed = self.api['cases'][1]['relocation_observations']
        details = {'security_cookie': 0x123456789abc, 'security_cookie_address': 0x20014020,
                   'security_cookie_values': [0x123456789abc, 0x23456789abcd],
                   'load_config_rva': 0x2000, 'cookie_field_rva': 0x2058}
        observed.update(details)
        public = self.export()['run_assessments']['api_abi']['cases'][1]['relocation_observations']
        self.assertFalse(set(details) & set(public))
        for key in ('security_cookie_images', 'security_cookie_observations',
                    'security_cookie_initialized', 'security_cookie_stable',
                    'security_cookie_destination_verified', 'security_cookie_load_config_verified'):
            saved = observed.pop(key)
            with self.subTest(key=key), self.assertRaises(Error): self.export()
            observed[key] = saved

    def test_native_fixture_environment_policy_is_exact_and_public(self):
        result = self.export()['run_assessments']['api_abi']
        self.assertEqual(result['environment_policy'], api_runner.ENVIRONMENT_POLICY)
        self.assertTrue(all(row['environment_policy'] == api_runner.ENVIRONMENT_POLICY for row in result['cases']))
        for source in (self.api, self.api['cases'][0], self.api['cases'][1]):
            with self.subTest(source=source.get('id', 'run')):
                saved = source.pop('environment_policy')
                with self.assertRaisesRegex(Error, 'api_environment_policy'):
                    self.export()
                source['environment_policy'] = {**saved, 'WINEDLLOVERRIDES': 'mscoree=n'}
                with self.assertRaisesRegex(Error, 'api_environment_policy'):
                    self.export()
                source['environment_policy'] = saved

    def test_native_prerequisites_keep_failed_attempts_and_absent_authorization_bindings(self):
        result = self.export()['native_arena_prerequisites']
        self.assertEqual(result['selected_policy'], 'page-wx')
        self.assertEqual([row['observations']['native_prerequisite_passed'] for row in result['attempts']],
                         [False, False, True])
        self.assertEqual(self.native_validator.call_count, 3)
        for root, row in zip(self.native_roots, result['attempts']):
            self.assertEqual(row['retained_receipt_sha256'], hashlib.sha256(
                (root / evidence.NATIVE_ARENA_RECEIPT).read_bytes()).hexdigest())
            auth = row['observations']['authorization']
            self.assertEqual(auth['profile_byte_hash_binding'], 'unavailable_not_retained_at_run')
            self.assertFalse(auth['current_profile_authorization_assessed'])

    def test_three_distinct_ordered_native_runs_are_required(self):
        for roots in ([], self.native_roots[:2], self.native_roots * 2,
                      [self.native_roots[0]] * 3, list(reversed(self.native_roots))):
            with self.subTest(count=len(roots)), self.assertRaises(Error):
                evidence.native_arena_prerequisites(roots)

    def test_retained_receipt_cannot_substitute_for_recomputed_raw_validation(self):
        root = self.native_roots[2]
        receipt = copy.deepcopy(self.native_receipts[root])
        receipt['private'] = '/Users/PRIVATE_SECRET'
        (root / evidence.NATIVE_ARENA_RECEIPT).write_bytes(encoded(receipt))
        with self.assertRaisesRegex(Error, 'export_native_arena_receipt_changed'):
            evidence.native_arena_prerequisites(self.native_roots)
        (root / evidence.NATIVE_ARENA_RECEIPT).write_bytes(encoded(self.native_receipts[root]))
        with mock.patch('arena_evidence.export', side_effect=Error('arena_receipt_bytes_changed')):
            with self.assertRaisesRegex(Error, 'arena_receipt_bytes_changed'):
                evidence.native_arena_prerequisites(self.native_roots)

    def test_native_success_cannot_promote_wine_or_profile_byte_qualification(self):
        root = self.native_roots[2]
        for key in ('runtime_qualified', 'profile_byte_hash_binding'):
            original = copy.deepcopy(self.native_receipts[root])
            if key == 'runtime_qualified': self.native_receipts[root][key] = True
            else: self.native_receipts[root]['authorization'][key] = 'verified'
            (root / evidence.NATIVE_ARENA_RECEIPT).write_bytes(encoded(self.native_receipts[root]))
            with self.subTest(key=key), self.assertRaises(Error):
                evidence.native_arena_prerequisites(self.native_roots)
            self.native_receipts[root] = original
            (root / evidence.NATIVE_ARENA_RECEIPT).write_bytes(encoded(original))

    def test_cli_requires_three_native_inputs_only_for_stage3_and_forwards_them(self):
        destination = self.root / 'mydocs/working/synthetic-cli.json'
        destination.parent.mkdir(parents=True)
        args = ['--stage', '3', '--build', str(self.build), '--runs', str(self.api_root),
                '--bootstrap-runs', str(self.bootstrap_root), '--output', str(destination)]
        inputs = [part for root in self.native_roots for part in ('--native-arena-run', str(root))]
        with mock.patch.object(evidence, 'export_stage3', return_value={'scope': 'synthetic_cli_only'}) as export, \
             mock.patch('builtins.print'):
            self.assertEqual(evidence.main(args + inputs[:-2]), 1)
            export.assert_not_called()
            self.assertFalse(destination.exists())
            self.assertEqual(evidence.main(args + inputs), 0)
            self.assertEqual(export.call_args.args[-1], [str(root) for root in self.native_roots])
        with mock.patch.object(evidence, 'export') as stage1, mock.patch('builtins.print'):
            self.assertEqual(evidence.main(['--stage', '1', '--inputs', 'synthetic', '--config', 'synthetic',
                '--toolchain', 'synthetic', '--output', str(destination), *inputs]), 1)
            stage1.assert_not_called()

    def test_mixed_signed_identity_or_runtime_root_rejects(self):
        self.bootstrap['signed_sha256'] = '0'*64
        with self.assertRaisesRegex(Error, 'export_mixed_signed_runtime'): self.export()
        self.bootstrap['signed_sha256'] = self.api['signed_sha256']
        self.bootstrap_record['runtime_path'] = '.build/task4/different-signed'
        self.bootstrap['run_sha256'] = digest(self.bootstrap_record)
        self.write_records()
        with self.assertRaisesRegex(Error, 'export_mixed_runtime_roots'): self.export()

    def test_signed_build_hash_and_exact_build_root_are_required(self):
        original = copy.deepcopy(self.signed['build_ref'])
        for key, value in [('sha256', '0'*64), ('path', str(self.build.parent/'other'/'build.json'))]:
            self.signed['build_ref'] = {**original, key: value}
            self.rebind_signed()
            with self.subTest(key=key), self.assertRaisesRegex(Error, 'tested_build_mismatch'): self.export()

    def test_stored_assembly_review_must_match_recomputed_actual_gate(self):
        stored = copy.deepcopy(self.review)
        stored['instruction_bytes_checked'] += 1
        (self.build/'abi-review.json').write_bytes(encoded(stored))
        with self.assertRaisesRegex(Error, 'export_assembly_evidence_changed'): self.export()
        self.write_records()
        self.review['build_sha256'] = '0'*64
        self.write_records()
        with self.assertRaisesRegex(Error, 'export_assembly_gate'): self.export()

    def test_incomplete_checker_or_missing_actual_pointer_identity_rejects(self):
        original = copy.deepcopy(self.review)
        for field in ('entry', 'pointer', 'runtime'):
            self.review.clear(); self.review.update(copy.deepcopy(original))
            if field == 'entry': self.review['entries'].pop()
            elif field == 'pointer': self.review['helpers'][0]['pointer_symbols_bound'] = False
            else: self.review['runtime_execution'] = True
            self.write_records()
            with self.subTest(field=field), self.assertRaises(Error): self.export()

    def test_unknown_command_text_or_private_sdk_value_never_leaks(self):
        self.built['commands'][0]['id'] = 'PRIVATE_SECRET'
        with self.assertRaisesRegex(Error, 'export_command_scope'): evidence._stage3_commands(self.built)
        self.built['commands'][0]['id'] = 'make'
        self.built['sdk']['version'] = '/Users/PRIVATE_SECRET'
        with self.assertRaises(Error): self.export()

    def test_no_unverified_hardening_or_extra_entitlement_claims(self):
        for mode in ('profile', 'hardening', 'claims', 'count'):
            value = copy.deepcopy(self.signed)
            if mode == 'profile': value['profile_checks']['unexpired'] = False
            elif mode == 'hardening': value['native_images'][0]['signature']['hardened_runtime'] = False
            elif mode == 'claims': value['native_images'][0]['signature']['claim_keys'] = ['PRIVATE_SECRET']
            else: value['native_images'].pop()
            with self.subTest(mode=mode), self.assertRaises(Error): evidence._stage3_authorization(value, 38)

    def test_page_policy_and_loader_only_jit_claim_are_required(self):
        for mode in ('policy', 'missing-loader-jit', 'helper-jit'):
            value = copy.deepcopy(self.signed)
            if mode == 'policy': value['code_publication_policy'] = 'thread-jit'
            elif mode == 'missing-loader-jit':
                image = next(row for row in value['native_images'] if row['role'] == 'wine-loader')
                image['signature']['claim_keys'].remove('com.apple.security.cs.allow-jit')
            else: value['native_images'][0]['signature']['claim_keys'] = ['com.apple.security.cs.allow-jit']
            with self.subTest(mode=mode), self.assertRaises(Error): evidence._stage3_authorization(value, 38)

    def test_failed_or_incomplete_execution_summaries_cannot_export_success(self):
        for mode in ('api-failed', 'bootstrap-failed', 'fixture', 'boolean-counter', 'control'):
            api, bootstrap = copy.deepcopy(self.api), copy.deepcopy(self.bootstrap)
            if mode == 'api-failed': api['passed'] = False
            elif mode == 'bootstrap-failed': bootstrap['passed'] = False
            elif mode == 'fixture': api['cases'][1]['fixture_results'][-1]['native_calls'] = 0
            elif mode == 'boolean-counter': api['cases'][1]['fixture_results'][0]['error_step'] = False
            else: api['controls'][0]['executed'] = True
            with self.subTest(mode=mode), self.assertRaises(Error): evidence._stage3_runs(api, bootstrap)

    def test_publication_observations_are_required_for_every_executed_loader(self):
        for mode in ('missing', 'duplicate', 'policy', 'counts'):
            value = copy.deepcopy(self.api)
            rows = value['cases'][0]['arena_observations']
            if mode == 'missing': rows.pop()
            elif mode == 'duplicate': rows[-1]['role'] = rows[0]['role']
            elif mode == 'policy': rows[0]['policy'] = 'thread-jit'
            else: rows[0]['live_images_at_last_observation'] = 999
            with self.subTest(mode=mode), self.assertRaises(Error): evidence._stage3_runs(value, self.bootstrap)

    def test_diagnostic_adapter_cannot_promote_an_otherwise_passing_run(self):
        (self.api_root/'diagnostic-adapter.json').write_text('{}')
        with self.assertRaisesRegex(Error, 'diagnostic_only_run'): self.export()

    def test_private_record_mutation_after_gate_is_rejected(self):
        with (self.api_root/'run.json').open('ab') as stream: stream.write(b' ')
        with self.assertRaisesRegex(Error, 'export_evidence_changed'): self.export()

class FailedStage3ExportTests(unittest.TestCase):
    """Historical hashes and observations only; no signing or execution gates."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.failed = self.root / '.build/task4/failed'
        self.runtime = self.root / '.build/task4/signed'
        self.case_root = self.failed / 'api'
        self.case_root.mkdir(parents=True)
        self.runtime.mkdir()
        patcher = mock.patch.object(evidence, 'REPO', self.root)
        patcher.start(); self.addCleanup(patcher.stop)
        producers = {}
        for name in evidence.FAILED_API_SOURCES:
            data = ('Original synthetic source ' + name).encode()
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            archived = self.failed/'producer'/name
            archived.parent.mkdir(parents=True, exist_ok=True)
            archived.write_bytes(data)
            producers[name] = hashlib.sha256(data).hexdigest()
        signer = {}
        for name in ('signing.py', 'common.py'):
            path = self.root/'tools/wine'/name
            path.write_text('Original synthetic signer ' + name)
            signer[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.signed = {'schema_version': 1, 'record_kind': 'wine_signed_runtime',
            'wine_execution': False, 'runtime_qualified': False,
            'authorization_scope': 'development_windows_api_abi_fixtures',
            'producer_sha256': signer, 'build_ref': {'sha256': '1'*64, 'path': '/Users/PRIVATE_SECRET'},
            'private_profile': 'PRIVATE_SECRET'}
        (self.runtime/'signed.json').write_bytes(encoded(self.signed))
        roles = ('loader', 'process-01')
        self.case = {'schema_version': 1, 'record_kind': 'wine_api_case',
            'case': {'id': 'api', 'entrypoint': 'api_pe', 'args': api_runner.API_ARGS,
                     'timeout_ms': 180000, 'expected_exit': 0},
            'runtime_qualified': False, 'pe_executed': False, 'passed': False,
            'outcome': 'timeout', 'elapsed_ms': 180517, 'error': None,
            'assessment_error': 'api_operation_failed', 'stream_error': None,
            'nonce': 'PRIVATE_SECRET', 'private': '/Users/PRIVATE_SECRET',
            'processes': {role: {'exit_code': code, 'reaped': True, 'identity': {'pid': 998877}}
                          for role, code in [('loader', -2), ('server', 0), ('sentinel', 0)]},
            'registrations': [{'role': role, 'exited': True, 'exit_code': -2 if role == 'loader' else -9,
                               'identity': {'pid': 998877}, 'private': 'PRIVATE_SECRET'} for role in roles],
            'pre_cleanup': {'at_ns': 123456789, 'processes': {
                role: {'exited': False, 'exit_code': None} for role in roles}},
            'cleanup': {'complete': True, 'observation_gap': False, 'reaped': {'loader': True, 'server': True},
                        'errors': [], 'signals': [{'role': 'loader', 'signal': 2}]},
            'sentinel_cleanup': {'complete': True, 'observation_gap': False, 'reaped': {'sentinel': True},
                                 'errors': [], 'signals': []}, 'sentinel_survived': True,
            'events': {'loader': [{'event': 'stage3_pe_continue', 'pid': 998877}],
                       'process-01': [{'event': 'stage3_fork', 'path': '/Users/PRIVATE_SECRET'}],
                       'server': [{'event': 'server_ready', 'nonce': 'PRIVATE_SECRET'}]}, 'logs': []}
        pairs = [(role, channel) for role in ('loader', 'server', 'sentinel') for channel in ('stdout', 'stderr')]
        pairs += [(role, 'events') for role in self.case['events']]
        for role, channel in pairs:
            data = b''.join((json.dumps(row, separators=(',', ':')) + '\n').encode() for row in self.case['events'][role]) if channel == 'events' else b'PRIVATE_SECRET\n'
            name = role + '.' + channel + '.log'
            (self.case_root/name).write_bytes(data)
            self.case['logs'].append({'role': role, 'channel': channel, 'path': name,
                'bytes': len(data), 'observed_bytes': len(data), 'eof': True, 'write_error': None,
                'sha256': hashlib.sha256(data).hexdigest()})
        self.run = {'schema_version': 1, 'record_kind': 'wine_api_run', 'suite': 'api-abi',
            'passed': False, 'pe_executed': False, 'runtime_qualified': False, 'error': 'api_operation_failed',
            'producer_sha256': producers, 'cases_sha256': producers['tests/wine/cases-stage3.json'],
            'runtime_path': '.build/task4/signed', 'signed_sha256': digest(self.signed), 'cases': []}
        self.write_records()

    def write_records(self, gate_error='api_operation_failed'):
        raw = encoded(self.case)
        (self.case_root/'case.json').write_bytes(raw)
        gate = {'schema_version': 1, 'record_kind': 'wine_case_gate_assessment', 'passed': False,
                'case_sha256': hashlib.sha256(raw).hexdigest(), 'error': gate_error}
        (self.case_root/'assessment.json').write_bytes(encoded(gate))
        self.run['cases'] = [{'id': 'api', 'path': 'api/case.json', 'sha256': gate['case_sha256'],
            'assessment_path': 'api/assessment.json', 'assessment_sha256': digest(gate), 'passed': False}]
        (self.failed/'run.json').write_bytes(encoded(self.run))

    def export(self):
        return evidence.summarize_failed_api_run(self.failed)

    def test_failed_timeout_preserves_termination_timing_without_claiming_no_pe_entry(self):
        with mock.patch('api_runner.validate_runs', side_effect=AssertionError('historical run was revalidated')), \
             mock.patch('signing.validate_prepared', side_effect=AssertionError('old grant was renewed')):
            value = self.export()
        text = json.dumps(value)
        for private in ('PRIVATE_SECRET', '/Users/', str(self.root), '998877', 'nonce'):
            self.assertNotIn(private, text)
        self.assertEqual(value['record_status'], 'complete')
        self.assertFalse(value['passed'])
        self.assertEqual(value['unrecorded_cases'], ['abi'])
        case = value['cases'][0]
        self.assertEqual(case['outcome'], 'timeout')
        self.assertFalse(case['reported_guest_exit_observed'])
        self.assertEqual(case['event_counts']['loader']['events']['stage3_pe_continue'], 1)
        process = case['registered_processes'][1]
        self.assertEqual(process['exit_code'], -9)
        self.assertFalse(process['exited_before_cleanup'])
        self.assertIsNone(process['exit_code_before_cleanup'])
        self.assertTrue(case['cleanup']['complete'])
        self.assertTrue(case['reported_sentinel_survived'])

    def test_failed_guest_exit_keeps_known_error_and_observed_termination(self):
        self.run['error'] = 'api_exit_failed'
        self.case.update(outcome='exited', elapsed_ms=1335, assessment_error='api_exit_failed')
        self.case['processes']['loader']['exit_code'] = 53
        self.case['registrations'][0]['exit_code'] = 53
        self.case['pre_cleanup']['processes']['loader'] = {'exited': True, 'exit_code': 53}
        self.write_records(gate_error='api_exit_failed')
        value = self.export()
        self.assertEqual(value['record_status'], 'complete')
        self.assertEqual(value['error'], 'api_exit_failed')
        self.assertFalse(value['passed'])
        self.assertFalse(value['pe_execution_qualified'])
        self.assertEqual(value['unrecorded_cases'], ['abi'])
        case = value['cases'][0]
        self.assertEqual(case['assessment_error'], 'api_exit_failed')
        self.assertEqual(case['gate_error'], 'api_exit_failed')
        self.assertEqual(case['outcome'], 'exited')
        self.assertFalse(case['reported_guest_exit_observed'])
        self.assertEqual(case['direct_processes'][0]['exit_code'], 53)
        self.assertEqual(case['registered_processes'][0]['exit_code_before_cleanup'], 53)
        self.assertTrue(case['registered_processes'][0]['exited_before_cleanup'])

    def test_exact_archived_sources_survive_current_producer_changes(self):
        (self.root/'tools/wine/api_runner.py').write_text('changed producer')
        self.assertEqual(self.export()['record_status'], 'complete')
        (self.failed/'producer/tools/wine/api_runner.py').unlink()
        value = self.export()
        self.assertEqual(value['record_status'], 'partial')
        self.assertIn('source_api_runner', value['missing_records'])

    def test_large_failed_case_reuses_strict_reader_and_raw_hash_checks(self):
        # Two bounded synthetic image streams exceed the generic node budget.
        # Their repetition demonstrates receipt handling, never real execution.
        event = {'event': 'image', 'pid': 1, 'generation': 0, 'sequence': 1,
                 'cpu': 16777228, 'uuid': '0' * 36, 'path': '/System/Library/Synthetic.dylib'}
        for role in ('loader', 'process-01'):
            rows = [{**event, 'sequence': index} for index in range(8500)]
            self.case['events'][role] = rows
            data = b''.join((json.dumps(row, separators=(',', ':')) + '\n').encode() for row in rows)
            self.assertLess(len(data), 2 * 1024 * 1024)
            (self.case_root / (role + '.events.log')).write_bytes(data)
            log = next(item for item in self.case['logs'] if (item['role'], item['channel']) == (role, 'events'))
            log.update(bytes=len(data), observed_bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        self.write_records()
        value = self.export()
        self.assertEqual(value['record_status'], 'complete')
        self.assertEqual(value['cases'][0]['event_counts']['loader']['retained_event_count'], 8500)
        self.assertNotIn('environment_policy', value)
        self.assertNotIn('environment_policy', value['cases'][0])
        with (self.case_root / 'loader.events.log').open('ab') as stream:
            stream.write(b' ')
        with self.assertRaisesRegex(Error, 'failed_api_log_changed'):
            self.export()
        original = self.case_root / 'loader.events.log'
        original.write_bytes(original.read_bytes()[:-1])
        retained = original.with_suffix('.retained')
        original.rename(retained)
        original.symlink_to(retained)
        with self.assertRaises(OSError):
            self.export()

    def test_legacy_and_relocation_producer_sets_are_exact_and_parser_archive_bound(self):
        self.run['code_publication_policy'] = 'page-wx'
        for name in evidence.PAGE_WX_API_SOURCES:
            if name in self.run['producer_sha256']:
                continue
            data = ('Original synthetic source ' + name).encode()
            for path in (self.root / name, self.failed / 'producer' / name):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            self.run['producer_sha256'][name] = hashlib.sha256(data).hexdigest()
        self.write_records()
        legacy = self.export()
        self.assertEqual(legacy['record_status'], 'complete')
        self.assertNotIn('pe_module_parser', legacy['source_sha256'])
        name = 'tools/wine/modules.py'
        data = b'Original synthetic PE reader, never executed'
        current = self.root / name
        archive = self.failed / 'producer' / name
        current.write_bytes(data)
        archive.write_bytes(data)
        self.run['producer_sha256'][name] = hashlib.sha256(data).hexdigest()
        self.write_records()
        actual = self.export()
        self.assertEqual(actual['record_status'], 'complete')
        self.assertEqual(actual['source_sha256']['pe_module_parser'], hashlib.sha256(data).hexdigest())
        # A matching current source cannot substitute for the new parser archive.
        archive.unlink()
        missing = self.export()
        self.assertEqual(missing['record_status'], 'partial')
        self.assertIn('source_pe_module_parser', missing['missing_records'])
        archive.write_bytes(data + b' changed')
        self.assertEqual(self.export()['record_status'], 'partial')
        archive.write_bytes(data)
        current.write_bytes(b'New current parser')
        self.assertEqual(self.export()['record_status'], 'complete')
        self.run['producer_sha256']['tools/wine/diagnostic_adapter.py'] = 'd' * 64
        self.write_records()
        with self.assertRaisesRegex(Error, 'failed_api_source_scope'):
            self.export()
        del self.run['producer_sha256']['tools/wine/diagnostic_adapter.py']
        del self.run['code_publication_policy']
        self.write_records()
        with self.assertRaisesRegex(Error, 'failed_api_source_scope'):
            self.export()

    def test_changed_raw_evidence_and_forged_event_counts_reject(self):
        with (self.case_root/'loader.events.log').open('ab') as stream: stream.write(b' ')
        with self.assertRaisesRegex(Error, 'failed_api_log_changed'): self.export()
        path = self.case_root/'loader.events.log'
        path.write_bytes(path.read_bytes()[:-1])
        self.case['events']['loader'].append({'event': 'stage3_guest_exit'})
        self.write_records()
        with self.assertRaisesRegex(Error, 'failed_api_event_log_mismatch'): self.export()

    def test_missing_records_stay_explicitly_partial(self):
        (self.case_root/'assessment.json').unlink()
        (self.case_root/'loader.events.log').unlink()
        value = self.export()
        self.assertEqual(value['record_status'], 'partial')
        self.assertEqual(set(value['cases'][0]['missing_records']), {'gate_assessment', 'loader_events'})
        (self.failed/'run.json').unlink()
        value = self.export()
        self.assertEqual(value['missing_records'], ['run_record'])
        self.assertIsNone(value['run_sha256'])

    def test_private_failure_strings_are_classified_and_bad_types_rejected(self):
        self.case['assessment_error'] = '/Users/PRIVATE_SECRET'
        self.run['error'] = 'PRIVATE_SECRET'
        self.write_records()
        value = self.export()
        self.assertEqual(value['error'], 'unclassified_api_failure')
        self.assertEqual(value['cases'][0]['assessment_error'], 'unclassified_api_failure')
        self.case['pre_cleanup']['processes']['loader']['exited'] = 'PRIVATE_SECRET'
        self.write_records()
        with self.assertRaisesRegex(Error, 'failed_api_pre_cleanup_shape'): self.export()

    def test_success_diagnostic_adapters_and_unordered_cases_reject(self):
        self.run['passed'] = True
        self.write_records()
        with self.assertRaisesRegex(Error, 'failed_api_run_scope'): self.export()
        self.run['passed'] = False
        self.write_records()
        (self.failed/'diagnostic-adapter.json').write_text('{}')
        with self.assertRaisesRegex(Error, 'diagnostic_only_run'): self.export()
        (self.failed/'diagnostic-adapter.json').unlink()
        self.run['cases'][0]['id'] = 'abi'
        (self.failed/'run.json').write_bytes(encoded(self.run))
        with self.assertRaisesRegex(Error, 'failed_api_case_order'): self.export()


if __name__ == '__main__':
    unittest.main()
