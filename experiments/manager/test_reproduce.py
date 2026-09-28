"""Adversarial reproduction checks; synthetic records are never public evidence."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('manager_reproduce', HERE / 'reproduce.py')
reproduce = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reproduce)


def synthetic_report():
    """Build a self-consistent unit-test document; no execution claim is published."""
    comparison = reproduce.strict_json(HERE / 'results/comparison.json')
    corpus = reproduce.strict_json(HERE / 'results/final-corpus.json')
    output = reproduce.REPO / '.build/task3/reproduction-unit-fixture'
    commands = [{'phase': phase, 'argv': reproduce.public_argv(argv, output), 'returncode': 0,
                 'watchdog': None, 'stdout_sha256': 'a' * 64, 'stderr_sha256': 'b' * 64}
                for phase, argv, _ in reproduce.command_specs(output)]
    tests = {'schemas_examples': {'eligible': True, 'evaluation_only': True, 'outcome_codes': [], 'record_count': 0, 'record_valid': True}}
    for name in reproduce.SUITES:
        ids = reproduce.expected_tests(name)
        tests[name] = {'tests_run': len(ids), 'passed_ids': ids, 'failed_ids': [], 'error_ids': [],
                       'skipped_ids': [], 'unexpected_successes': [], 'expected_failures': []}
    tests['rust_faults'] = {'tests_run': 2, 'passed_ids': reproduce.expected_rust_tests(),
                            'failed': 0, 'ignored': 0, 'filtered_out': 0}
    wheels = reproduce.dependency_identity()
    tests['installed_packages'] = {'python': '3.14.4', 'machine': 'arm64', 'platform': 'darwin',
                                   'packages': {row['name']: row['version'] for row in wheels}}
    binaries = {}
    for name in ['fixture-child', 'rust-manager', 'swift-manager']:
        candidate = 'swift' if name == 'swift-manager' else 'rust'
        payload = comparison['payload'][candidate]
        binaries[name] = {'sha256': payload['binary_sha256'], 'size_bytes': payload['manager_binary_bytes'],
                          'slices': 'arm64', 'system_dynamic_dependencies': payload['system_dynamic_dependencies'],
                          'packaging': payload['packaging_inspection'], 'matches_stage4_measured_payload': None if name == 'fixture-child' else True}
    return {'version': 1, 'status': 'completed', 'fixture_only': True, 'runtime_eligible': False,
            'source_sha256': reproduce.inventory(), 'retained_evidence_sha256': reproduce.retained_evidence(),
            'started_at_utc': '2026-09-28T14:00:00+00:00', 'finished_at_utc': '2026-09-28T14:05:00+00:00',
            'output': '.build/task3/reproduction-unit-fixture',
            'reconstruction': {'python_wheels': wheels, 'fresh_venv': True,
                               'python_install': 'offline_no_index_require_hashes_no_deps',
                               'rust_build': 'locked_offline_reused_hash_verified_registry_and_extracted_sources',
                               'swift_external_packages': [], 'network_acquisition': 'none_requested', 'cache_and_toolchain_reset': False},
            'commands': commands, 'tests': tests,
            'build': {'metadata_sha256': corpus['build_metadata_sha256'], 'toolchains': comparison['toolchains'],
                      'binaries': binaries, 'native_source_sha256': {p: value for p, value in reproduce.inventory().items() if any(p.startswith('experiments/manager/' + part + '/') for part in ['rust', 'swift', 'fixtures'])},
                      'locked_offline_rust': True, 'swift_external_dependencies': []},
            'corpus': corpus, 'semantic_match': True, 'budgets': reproduce.BUDGETS,
            'limitations': reproduce.LIMITATIONS, 'failures': []}


class OutputSafetyTests(unittest.TestCase):
    def test_nonempty_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            output = repo / '.build/task3/reproduction'
            output.mkdir(parents=True)
            sentinel = output / 'keep'
            sentinel.write_bytes(b'preserve')
            with self.assertRaisesRegex(ValueError, 'not_empty'):
                reproduce.output_path('.build/task3/reproduction', repo)
            self.assertEqual(sentinel.read_bytes(), b'preserve')

    def test_symlink_ancestors_and_leaf_are_rejected(self):
        for component in ['.build', '.build/task3', '.build/task3/reproduction']:
            with self.subTest(component=component), tempfile.TemporaryDirectory() as temp:
                repo = Path(temp)
                destination = repo / 'other'
                destination.mkdir()
                link = repo / component
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(destination, target_is_directory=True)
                with self.assertRaisesRegex(ValueError, 'symlink'):
                    reproduce.output_path('.build/task3/reproduction', repo)
                self.assertEqual(list(destination.iterdir()), [])

    def test_escape_absolute_and_broad_outputs_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            for value in ['/tmp/reproduction', '.build/task3', '.build/task3/../reproduction',
                          '.build/task3/reproduction/child', '.build//task3/reproduction',
                          './.build/task3/reproduction', '.build/task3/prototypes']:
                with self.subTest(value=value), self.assertRaises(ValueError):
                    reproduce.output_path(value, Path(temp))

    def test_empty_output_is_allowed_without_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            expected = repo / '.build/task3/reproduction-fresh'
            self.assertEqual(reproduce.output_path('.build/task3/reproduction-fresh', repo), expected)
            self.assertFalse(expected.exists())
            expected.mkdir(parents=True)
            self.assertEqual(reproduce.output_path('.build/task3/reproduction-fresh', repo), expected)
            self.assertEqual(list(expected.iterdir()), [])


    def test_internal_suite_cannot_overwrite_or_escape(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(reproduce, 'REPO', Path(temp)):
            repo = Path(temp)
            output = repo / '.build/task3/reproduction-unit'
            output.mkdir(parents=True)
            sentinel = output / 'contracts.json'
            sentinel.write_bytes(b'keep')
            targets = [sentinel, repo / 'outside.json', output / 'experiments.json', output / '../contracts.json']
            for destination in targets:
                with self.subTest(destination=destination), self.assertRaises(ValueError):
                    reproduce.suite_destination('contracts', destination)
            self.assertEqual(sentinel.read_bytes(), b'keep')
            sentinel.unlink()
            (output / 'private').write_bytes(b'keep')
            sentinel.symlink_to('private')
            with self.assertRaisesRegex(ValueError, 'symlink'):
                reproduce.suite_destination('contracts', sentinel)
            self.assertEqual((output / 'private').read_bytes(), b'keep')


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.report = synthetic_report()

    def test_synthetic_consistency_control(self):
        self.assertEqual(reproduce.validate_report(self.report), [])

    def test_schema_example_cli_and_text_blob_inputs_are_required(self):
        self.report['tests']['schemas_examples']['eligible'] = False
        self.assertIn('schema_example_validation', reproduce.validate_report(self.report))
        for name in ['payload.txt', 'source.txt', 'terms.txt']:
            self.assertIn('runtime/contracts/examples/fixture/blobs/' + name, reproduce.inventory())

    def test_source_and_history_change_rejected(self):
        for field in ['source_sha256', 'retained_evidence_sha256']:
            value = copy.deepcopy(self.report)
            key = next(iter(value[field]))
            value[field][key] = '0' * 64
            self.assertIn('source_or_history_identity', reproduce.validate_report(value))

    def test_missing_or_duplicate_unit_result_rejected(self):
        value = copy.deepcopy(self.report)
        ids = value['tests']['contracts']['passed_ids']
        ids[-1] = ids[0]
        self.assertIn('unit_test_accounting', reproduce.validate_report(value))
        value = copy.deepcopy(self.report)
        value['tests']['experiments']['tests_run'] -= 1
        self.assertIn('unit_test_accounting', reproduce.validate_report(value))

    def test_missing_rust_fault_case_rejected(self):
        self.report['tests']['rust_faults']['passed_ids'].pop()
        self.assertIn('rust_fault_test_accounting', reproduce.validate_report(self.report))

    def test_outer_interpreter_path_is_not_report_identity(self):
        output = reproduce.REPO / '.build/task3/reproduction-unit'
        for interpreter in [str(Path.home() / 'tools/python'), str(reproduce.REPO / 'other-venv/bin/python'), str(output / 'venv/bin/python')]:
            with patch.object(reproduce.sys, 'executable', interpreter):
                first = reproduce.command_specs(output)[0][1]
                self.assertEqual(reproduce.public_argv(first, output)[0], '<python>')
                fresh = reproduce.command_specs(output)[1][1]
                self.assertEqual(reproduce.public_argv(fresh, output)[0], '<run>/venv/bin/python')

    def test_ordinary_case_cannot_claim_extra_descendant_trace(self):
        self.report['corpus']['results'][0]['observed_trace_count'] = 2
        self.assertIn('corpus_trace_semantics', reproduce.validate_report(self.report))

    def test_missing_or_reordered_native_case_rejected(self):
        value = copy.deepcopy(self.report['corpus'])
        value['results'].pop()
        self.assertIn('corpus_rows', reproduce.validate_corpus(value))
        value = copy.deepcopy(self.report['corpus'])
        value['results'][0], value['results'][1] = value['results'][1], value['results'][0]
        self.assertIn('corpus_row_identity', reproduce.validate_corpus(value))

    def test_passed_label_cannot_hide_missing_trace_or_overrun(self):
        for mutation, expected in [('trace', 'corpus_trace_semantics'), ('bounds', 'corpus_case_failed')]:
            value = copy.deepcopy(self.report['corpus'])
            row = next(row for row in value['results'] if row['case'] == 'descendant_pipe')
            if mutation == 'trace':
                row['observed_trace_count'] = 0
                row['owned_identities_gone'] = False
            else:
                row['bounded_completion'] = False
            self.assertIn(expected, reproduce.validate_corpus(value))

    def test_native_scope_cleanup_and_oracle_rechecked(self):
        changes = [('result', 'translated', True), ('result', 'reaped', False),
                   ('result', 'runtime_eligible', True), ('oracle', 'eligible', False)]
        for field, key, value in changes:
            corpus = copy.deepcopy(self.report['corpus'])
            corpus['results'][0][field][key] = value
            self.assertTrue(reproduce.validate_corpus(corpus), (field, key))

    def test_installed_dependencies_and_command_flags_checked(self):
        value = copy.deepcopy(self.report)
        value['tests']['installed_packages']['packages']['jsonschema'] = '0.0.0'
        self.assertIn('installed_package_identity', reproduce.validate_report(value))
        value = copy.deepcopy(self.report)
        value['commands'][1]['argv'].remove('--require-hashes')
        self.assertIn('command_evidence', reproduce.validate_report(value))

    def test_private_and_unknown_data_are_rejected(self):
        value = copy.deepcopy(self.report)
        value['build']['toolchains']['clang'] += ' /Users/private-user/token'
        self.assertIn('private_data', reproduce.validate_report(value))
        value = copy.deepcopy(self.report)
        value['surprise'] = True
        self.assertIn('report_shape', reproduce.validate_report(value))

    def test_build_binding_and_payload_match_are_checked(self):
        value = copy.deepcopy(self.report)
        value['build']['metadata_sha256'] = '0' * 64
        self.assertIn('corpus_build_identity', reproduce.validate_report(value))
        value = copy.deepcopy(self.report)
        value['build']['binaries']['rust-manager']['matches_stage4_measured_payload'] = False
        self.assertIn('payload_comparison', reproduce.validate_report(value))

    def test_runtime_and_failed_claims_do_not_pass(self):
        for key, value in [('runtime_eligible', True), ('status', 'failed'), ('version', True)]:
            report = copy.deepcopy(self.report)
            report[key] = value
            self.assertIn('report_scope', reproduce.validate_report(report))

    def test_strict_json_rejects_duplicate_keys_and_nonfinite(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'report.json'
            for data in ['{"version": 1, "version": 1}', '{"value": NaN}']:
                path.write_text(data)
                with self.assertRaises(ValueError):
                    reproduce.strict_json(path)


if __name__ == '__main__':
    unittest.main()
