"""Synthetic packaging tests; gate mocks do not establish host execution.

Reuse the existing Stage 3 export fixture's private evidence scaffolding, then
supply independent Stage 4 receipt semantics. No Wine process, signature or
compiler is created here; these tests exercise selection and cross-record gates.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

REPOSITORY = next(path for path in Path(__file__).resolve().parents if (path / 'tools/wine/common.py').is_file())
sys.path.insert(0, str(REPOSITORY / 'tools/wine'))
sys.path.insert(0, str(REPOSITORY / 'tests/wine'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import abi_review
import api_runner
import build
import evidence
import exception_evidence
import run_fixtures
import stage4_evidence as exporter
from common import Error, encoded, sha256
import test_evidence_stage3 as stage3_fixture
digest = stage3_fixture.digest


class Stage4ExportTests(unittest.TestCase):
    def setUp(self):
        self.api_producers = tuple(api_runner.producers(exporter.SUITE))
        self.bootstrap_producers = tuple(run_fixtures.producer_hashes())
        self.base = stage3_fixture.Stage3ExportTests(methodName='runTest')
        self.addCleanup(self.base.doCleanups)
        self.base.setUp()
        b = self.base
        patcher = mock.patch.object(exporter, 'REPO', b.root)
        patcher.start(); self.addCleanup(patcher.stop)
        for name in exporter.SOURCES.values():
            path = b.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text('Synthetic private producer source: ' + name)
        b.built.update({key: '7'*64 for key in
            ('inputs_sha256', 'config_sha256', 'toolchain_lock_sha256', 'source_prepared_sha256',
             'tool_prepared_sha256', 'patch_series_sha256')})
        b.built['source_manifest'] = {'path': '/Users/PRIVATE_SECRET', 'sha256': '8'*64}
        b.built.update(fixture_suite=exporter.SUITE,
            producer_sha256=self.producer(build.PRODUCERS, True),
            commands=[{'id': name, 'exit_code': 0, 'timed_out': False, 'output_limit': False,
                       'argv': ['/Users/PRIVATE_SECRET'], 'stdout': 'PRIVATE_SECRET'}
                      for name in ['patch-1', *sorted(exporter.COMMANDS)]])
        for item in b.artifacts['files']:
            if item['kind'] == 'macho': item['architectures'] = [0x100000c]
        b.signed.update(authorization_scope=exporter.SCOPE,
                        producer_sha256=self.producer(('signing.py', 'common.py'), True))
        b.review['producer_sha256'] = self.producer(('abi_review.py', 'common.py', 'toolchain.py'), True)
        b.api_record.update(suite=exporter.SUITE, producer_sha256=self.producer(self.api_producers))
        b.bootstrap_record.update(suite='bootstrap', producer_sha256=self.producer(self.bootstrap_producers))
        b.api.update(record_kind='wine_thread_memory_exception_assessment', suite=exporter.SUITE,
            case_count=3, game_qualified=False,
            evidence_scope='instrumented-arm64-thread-memory-exception-with-constrained-owned-descendants',
            producer_sha256=copy.deepcopy(b.api_record['producer_sha256']))
        threads = copy.deepcopy(b.api['cases'][0])
        threads.update(id='threads', fixture_results=copy.deepcopy(api_runner.expected_fixture_rows('threads')))
        b.api['cases'].append(threads)
        for row in b.api['cases']:
            root = self.dynamic_process(row['id'] == 'threads')
            row['dynamic_observations'] = {'policy': 'page-wx', 'dynamic_supported': True,
                'processes': [{'role': item['role'], **self.dynamic_process(row['id'] == 'threads' and item['role'] == 'loader')}
                              for item in row['arena_observations']], 'root': root,
                'runtime_qualified': False, 'game_qualified': False, 'private_path': '/Users/PRIVATE_SECRET'}
        threads['thread_memory_exception_observations'] = {'fixture_sha256': '1'*64,
            'native_fixture_library_sha256': '2'*64, 'workers': 2, 'tls_teb_isolation': True,
            'native_anchor_parts': 34, 'guest_signals': 1, 'host_signals': 1, 'controlled_suspensions': 1,
            'software_exceptions': 1, 'access_faults_recovered': 3, 'guard_faults_retried': 1,
            'handler_order_checks': 6, 'dynamic_results': [42, 84], 'controlled_fault_terminations': 1,
            'controlled_windows_exit': 0xc0000005, 'controlled_native_exit': 5,
            'dynamic_owner': copy.deepcopy(threads['dynamic_observations']),
            'memory_result': dict(exception_evidence.MEMORY),
            'unqualified': ['general_unwinding', 'arbitrary_asynchronous_suspension',
                'native_created_callback_thread', 'x64_guest_translation', 'game_execution', 'general_jit_service'],
            'native_teb': 998877, 'private_profile': 'PRIVATE_SECRET'}
        b.bootstrap.update(record_kind='wine_bootstrap_assessment', suite='bootstrap',
            evidence_scope='retained-local-native-bootstrap-consistency',
            producer_sha256=copy.deepcopy(b.bootstrap_record['producer_sha256']))
        for target, value in [('api_runner.producers', b.api_record['producer_sha256']),
                              ('run_fixtures.producer_hashes', b.bootstrap_record['producer_sha256'])]:
            patcher = mock.patch(target, return_value=value)
            patcher.start(); self.addCleanup(patcher.stop)
        self.refresh()

    def producer(self, names, basenames=False):
        return {name: sha256(self.base.root / ('tools/wine/' + name if basenames else name)) for name in names}

    def dynamic_process(self, active):
        # Native success performs 3 commits, 3 protect operations and 3 revocations;
        # only 1 explicit guest decommit, with the other 2 on release.
        return {'budget_bytes': 524288, 'slots': 8, 'slot_bytes': 65536, 'budget_verified': True,
            'reservations': 2 if active else 0, 'commits': 3 if active else 0,
            'protects': 3 if active else 0, 'decommits': 3 if active else 0, 'releases': 2 if active else 0,
            'compatible_reuses': 1 if active else 0, 'committed_pages': 3 if active else 0,
            'decommitted_pages': 3 if active else 0, 'executable_publications': 2 if active else 0,
            'writable_transitions': 4 if active else 0, 'live_allocations_at_last_observation': 0,
            'private_base': 998877}

    def refresh(self):
        b = self.base
        b.signed['build_ref']['sha256'] = b.review['build_sha256'] = digest(b.built)
        b.rebind_signed()

    def export(self):
        b = self.base
        return exporter.export(b.build, b.api_root, b.bootstrap_root)

    def rejected(self, code=None):
        with self.assertRaises(Error) as raised:
            self.export()
        if code is not None: self.assertEqual(raised.exception.code, code)

    def test_full_export_reuses_current_validators_and_preserves_scope(self):
        result = self.export()
        self.assertEqual(result['record_kind'], 'wine_stage4_observations')
        self.assertEqual(result['signed_sha256'], digest(self.base.signed))
        self.assertEqual(result['build']['build_sha256'], digest(self.base.built))
        self.assertEqual(result['run_assessments']['bootstrap']['run_sha256'], digest(self.base.bootstrap_record))
        self.assertEqual(result['run_assessments']['threads_memory_exceptions']['case_count'], 3)
        self.base.mocks['api_runner.validate_runs'].assert_called_once_with(self.base.api_root, exporter.SUITE)
        self.base.mocks['run_fixtures.validate_runs'].assert_called_once_with(self.base.bootstrap_root, 'bootstrap')
        for key in ('translator_execution', 'game_execution', 'runtime_qualified', 'distribution_qualified'):
            self.assertIs(result[key], False)
        self.assertIn('general_unwinding', result['unqualified'])
        controls = result['run_assessments']['threads_memory_exceptions']['controls']
        self.assertEqual([item['machine'] for item in controls], ['x86_64', 'i386'])
        self.assertTrue(all(item['executed'] is False and item['accepted'] is False for item in controls))

    def test_private_diagnostics_and_identity_fields_never_forwarded(self):
        text = encoded(self.export()).decode()
        for secret in ('PRIVATE_SECRET', '998877', '/Users/', 'native_teb', 'private_base', 'claim_keys',
                       'profile_checks', 'same_team', 'current_provisioning_device_match', 'runtime_path', 'argv'):
            self.assertNotIn(secret, text)

    def test_old_bootstrap_assessment_cannot_be_relabelled_as_stage4(self):
        self.base.bootstrap['record_kind'] = 'wine_native_assessment'
        self.rejected('export_bootstrap_assessment_scope')

    def test_old_api_receipt_not_stage4(self):
        self.base.api['record_kind'] = 'wine_api_abi_assessment'
        self.rejected('export_stage4_assessment_scope')

    def test_bootstrap_different_signed_digest_rejected(self):
        self.base.bootstrap['signed_sha256'] = '9'*64
        self.rejected('export_mixed_signed_runtime')

    def test_raw_bootstrap_different_signed_digest_rejected(self):
        b = self.base
        b.bootstrap_record['signed_sha256'] = '9'*64
        b.bootstrap['run_sha256'] = digest(b.bootstrap_record)
        b.write_records()
        self.rejected('export_mixed_signed_runtime')

    def test_raw_bootstrap_record_kind_rejected(self):
        b = self.base
        b.bootstrap_record['record_kind'] = 'wine_api_run'
        self.refresh()
        self.rejected()

    def test_bootstrap_same_digest_different_runtime_path_rejected(self):
        self.base.bootstrap_record['runtime_path'] = '.build/task4/other-runtime'
        self.refresh()
        self.rejected('export_mixed_runtime_roots')

    def test_signed_build_path_mismatch_rejected(self):
        self.base.signed['build_ref']['path'] = str(self.base.build / 'different.json')
        self.refresh()
        self.rejected('export_tested_build_mismatch')

    def test_same_suite_but_stage3_authorization_rejected(self):
        self.base.signed['authorization_scope'] = 'development_windows_api_abi_fixtures'
        self.refresh()
        self.rejected('export_stage4_signed_scope')

    def test_bound_record_mutation_rejected(self):
        (self.base.bootstrap_root / 'run.json').write_bytes(b'{}\n')
        self.rejected('export_evidence_changed')

    def test_non_arm64_native_slice_rejected(self):
        self.base.artifacts['files'][0]['architectures'] = [0x1000007]
        self.rejected('export_host_architecture')

    def test_boolean_native_artifact_count_rejected(self):
        self.base.built['native_artifact_count'] = True
        self.refresh()
        self.rejected('export_native_artifact_count')

    def test_missing_or_duplicate_build_command_rejected(self):
        self.base.built['commands'][1] = copy.deepcopy(self.base.built['commands'][0])
        self.refresh()
        self.rejected('export_command_coverage')

    def test_failed_command_rejected(self):
        self.base.built['commands'][0]['exit_code'] = 7
        self.refresh()
        self.rejected('export_command_failure')

    def test_source_or_producer_replacement_rejected(self):
        (self.base.root / 'tools/wine/api_runner.py').write_text('different producer')
        self.rejected('export_producer_changed')

    def test_unknown_producer_not_exported(self):
        self.base.api_record['producer_sha256']['/Users/PRIVATE_SECRET'] = 'a'*64
        self.base.api['producer_sha256'] = copy.deepcopy(self.base.api_record['producer_sha256'])
        self.refresh()
        self.rejected('export_producer_not_allowlisted')

    def test_legacy_dynamic_capacity_not_supported_by_stage4_export(self):
        self.base.api['cases'][0]['dynamic_observations']['dynamic_supported'] = False
        self.rejected('export_dynamic_scope')

    def test_dynamic_counts_only_on_threads_root(self):
        self.base.api['cases'][0]['dynamic_observations']['processes'][0]['commits'] = 3
        self.rejected('export_dynamic_counts')

    def test_dynamic_protects_not_counted_as_commit_pages(self):
        self.base.api['cases'][2]['dynamic_observations']['processes'][0]['committed_pages'] = 6
        self.rejected('export_dynamic_counts')

    def test_thread_native_status_binding_preserved(self):
        self.base.api['cases'][2]['thread_memory_exception_observations']['controlled_native_exit'] = 0
        self.rejected('export_thread_facts')

    def test_thread_nested_dynamic_owner_cannot_disagree(self):
        value = self.base.api['cases'][2]['thread_memory_exception_observations']['dynamic_owner']
        value['root']['releases'] = 1
        self.rejected('export_dynamic_root')

    def test_boolean_fixture_numeric_result_rejected(self):
        self.base.api['cases'][2]['fixture_results'][1]['passed'] = True
        self.rejected('export_fixture_results')

    def test_executed_negative_architecture_control_rejected(self):
        self.base.api['controls'][0]['executed'] = True
        self.rejected('export_control_scope')

    def test_extra_non_loader_privileged_claim_rejected(self):
        self.base.signed['native_images'][0]['signature']['claim_keys'] = ['com.apple.security.cs.allow-jit']
        self.refresh()
        self.rejected('export_native_claims')

    def test_diagnostic_adapter_in_either_run_rejected(self):
        for root in (self.base.api_root, self.base.bootstrap_root):
            marker = root / 'diagnostic-adapter.json'
            marker.write_text('{}')
            self.rejected('diagnostic_only_run')
            marker.unlink()

    def test_input_symlink_rejected(self):
        link = self.base.root / '.build/task4/api-link'
        link.symlink_to(self.base.api_root, target_is_directory=True)
        with self.assertRaises(Error):
            exporter.export(self.base.build, link, self.base.bootstrap_root)

    def test_source_change_during_validation_rejected(self):
        original = self.base.mocks['signing.validate_prepared']
        calls = 0
        def validate(runtime):
            nonlocal calls
            calls += 1
            if calls == 2:
                (self.base.root / 'tools/wine/stage4_evidence.py').write_text('changed after source selection')
            return self.base.signed
        original.side_effect = validate
        self.rejected('export_evidence_changed')


if __name__ == '__main__':
    unittest.main()
