"""Reject incomplete, reordered, relabeled or arithmetically incorrect measurements."""
import copy
import importlib.util
import json
import contextlib
import io
import re
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('manager_comparison', HERE / 'compare.py')
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


def valid_report(plan):
    report = {key: {} for key in ['host', 'toolchains', 'preparation']}
    report.update(version=1, fixture_only=True, runtime_eligible=False, status='completed',
                  plan_sha256='0' * 64, source_sha256={}, conditions={'before': {'power_source': 'AC Power', 'configured_low_power_modes': [0, 0]}, 'after': {'power_source': 'AC Power', 'configured_low_power_modes': [0, 0]}, 'coordinator_exclusive_heavy_work_window': True, 'functional_budget_ms': 5000, 'intentional_timeout_budget_ms': 1500, 'scored_launch_budget_ms': 1500, 'cleanup_budget_ms': 2000, 'outer_budget_seconds': 10},
                  gates={}, samples=[], summary={}, payload={}, limitations=[], failures=[], prior_attempts=[], historical_evidence={name: {'path': 'results/' + name, 'sha256': comparison.sha(HERE / 'results' / name)} for name in comparison.HISTORICAL_EVIDENCE})
    report['toolchains'] = {'sdk': '26.5'}
    for phase in ['before', 'after']:
        report['gates'][phase] = {'passed': True, 'case_count': 55, 'execution_count': 110, 'native_observations': True, 'privacy_and_bounds': True, 'unrelated_sentinel_alive': True, 'report_sha256': 'a' * 64}
    counts = {}
    order = [('clean', c) for c in plan['build_samples']['order']] + [('incremental', c) for c in plan['build_samples']['incremental_order']] + [(phase, c) for phase, count in [('warmup', 5), ('launch', 30)] for _ in range(count) for c in comparison.CANDIDATES]
    for index, (phase, candidate) in enumerate(order):
        counts[(phase, candidate)] = counts.get((phase, candidate), 0) + 1
        row = {'sequence': index + 1, 'phase': phase, 'candidate': candidate, 'number': counts[(phase, candidate)], 'passed': True,
               'command': ['owned-test', '--timeout-ms', '1500'], 'binary_sha256': ('1' if candidate == 'rust' else '2') * 64, 'duration_seconds': (index + 1) / 1000,
               'peak_rss_bytes': 1000000, 'returncode': 0, 'watchdog': None, 'stdout_sha256': '3' * 64, 'stderr_sha256': '4' * 64}
        if phase in ['clean', 'incremental']:
            row.update(build_environment={}, source_sha256={'main': '5' * 64}, rebuild_observed=True)
        else:
            row.update(oracle_eligible=True, owned_identity_gone=True, native=True, fresh_bundle=True, sentinel_alive=True, errors=[])
        report['samples'].append(row)
    for candidate in comparison.CANDIDATES:
        report['payload'][candidate] = {'binary_sha256': ('1' if candidate == 'rust' else '2') * 64, 'native_slices': ['arm64'], 'manager_binary_bytes': 1000, 'standalone_distribution_payload_bytes': 1000,
            'system_dynamic_dependencies': ['/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1351.100.3)'],
            'signed_app_bundle_bytes': None, 'signed_app_bundle_reason': 'No distribution bundle.',
            'packaging_inspection': {'platform': 'MACOS', 'minimum_macos': '26.0', 'sdk': '26.5', 'rpaths': [], 'codesign_strict_verify_exit': 0,
                                     'signature': 'adhoc', 'linker_signed': True, 'team_identifier_present': False, 'inspection_log_sha256': 'b' * 64,
                                     'distribution_qualified': False, 'signing_scope': 'Owned fixture inspection only.'}}

    report['summary'] = comparison.summaries(report['samples'])
    return report


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.plan = comparison.load_plan(HERE / 'comparison-plan.json')
        self.report = valid_report(self.plan)

    def check(self, report=None):
        return comparison.validate_report(report or self.report, self.plan, check_inputs=False)

    def test_complete_accounting_is_accepted(self):
        self.assertEqual(self.check(), [])
        self.assertEqual(self.report['summary']['rust']['launch']['duration_seconds']['count'], 30)
        self.assertEqual(self.report['summary']['swift']['warmup']['duration_seconds']['count'], 5)

    def test_removing_an_unfavorable_sample_is_rejected(self):
        self.report['samples'].pop()
        self.report['summary'] = comparison.summaries(self.report['samples'])
        self.assertIn('sample_count', self.check())

    def test_changed_order_is_rejected_with_complete_counts(self):
        self.report['samples'][0], self.report['samples'][1] = self.report['samples'][1], self.report['samples'][0]
        self.assertIn('sample_order', self.check())

    def test_duplicate_sample_number_is_rejected(self):
        self.report['samples'][-1]['number'] = 29
        self.assertIn('sample_number', self.check())

    def test_summary_must_be_recomputed_from_all_samples(self):
        self.report['summary']['rust']['launch']['duration_seconds']['median'] = 0
        self.assertIn('summary_arithmetic', self.check())

    def test_nonfinite_duration_cannot_enter_comparison(self):
        self.report['samples'][0]['duration_seconds'] = float('nan')
        self.assertIn('invalid_duration', self.check())

    def test_failed_attempt_cannot_be_relabeled_completed(self):
        self.report['samples'][0]['passed'] = False
        self.report['samples'][0]['watchdog'] = 'outer_deadline'
        self.assertIn('invalid_attempt', self.check())

    def test_scored_warmup_cannot_replace_recorded_launch(self):
        self.report['samples'][-1]['phase'] = 'warmup'
        self.assertIn('sample_order', self.check())

    def test_recompilation_evidence_required(self):
        self.report['samples'][6]['rebuild_observed'] = False
        self.assertIn('missing_build_evidence', self.check())

    def test_launch_binary_must_match_last_clean_and_payload(self):
        self.report['samples'][-1]['binary_sha256'] = '9' * 64
        self.assertIn('launch_binary_identity', self.check())
        self.report = valid_report(self.plan)
        self.report['payload']['swift']['binary_sha256'] = '9' * 64
        self.assertIn('launch_binary_identity', self.check())

    def test_native_and_owned_identity_observations_required(self):
        self.report['samples'][-1]['owned_identity_gone'] = False
        self.report['samples'][-1]['native'] = False
        self.assertIn('invalid_launch_evidence', self.check())

    def test_secret_and_unknown_row_field_rejected(self):
        self.report['samples'][0]['private_path'] = '/Users/example/private'
        errors = self.check()
        self.assertIn('private_data', errors)
        self.assertIn('sample_shape', errors)

    def test_corpus_must_pass_before_and_after(self):
        self.report['gates']['after']['passed'] = False
        self.assertIn('functional_gate', self.check())

    def test_changed_power_configuration_is_not_comparable(self):
        self.report['conditions']['after']['power_source'] = 'Battery Power'
        self.assertIn('power_condition', self.check())

    def test_fixture_results_cannot_claim_game_eligibility(self):
        self.report['runtime_eligible'] = True
        self.assertIn('report_scope', self.check())

    def test_gate_result_without_evidence_digest_is_rejected(self):
        del self.report['gates']['after']['report_sha256']
        self.assertIn('functional_gate_evidence', self.check())

    def test_missing_packaging_inspection_cannot_pass(self):
        del self.report['payload']['rust']['packaging_inspection']
        self.assertIn('packaging_evidence', self.check())

    def test_missing_system_dependency_evidence_cannot_pass(self):
        del self.report['payload']['swift']['system_dynamic_dependencies']
        self.assertIn('dynamic_dependencies', self.check())

    def test_fake_release_signature_or_wrong_minimum_os_cannot_pass(self):
        self.report['payload']['rust']['packaging_inspection']['distribution_qualified'] = True
        self.report['payload']['swift']['packaging_inspection']['minimum_macos'] = '15.0'
        self.assertIn('signature_scope', self.check())
        self.assertIn('packaging_target', self.check())

    def test_prior_failure_index_requires_identity_and_safe_path(self):
        self.report['prior_attempts'] = [{'retained_local_report': '/Users/private/run.json', 'report_sha256': 'bad', 'status': 'failed', 'recorded_sample_count': 0,
                                         'plan_sha256': 'a' * 64, 'runner_sha256': 'b' * 64, 'failures': [], 'failed_cases': []}]
        self.assertIn('prior_attempt_path', self.check())
        self.assertIn('prior_attempt_digest', self.check())

    def test_actual_source_and_frozen_comment_edit_are_checked(self):
        for row in self.report['samples']:
            if row['phase'] in ['clean', 'incremental']:
                row['source_sha256'] = comparison.expected_source_identity(row['candidate'], row['phase'], row['number'], self.plan)
        self.report['source_sha256'] = comparison.inventory()
        self.report['plan_sha256'] = comparison.sha(HERE / 'comparison-plan.json')
        self.assertEqual(comparison.validate_report(self.report, self.plan), [])
        self.report['samples'][6]['source_sha256']['Sources/PearManager/main.swift'] = 'f' * 64
        self.assertIn('sample_source_identity', comparison.validate_report(self.report, self.plan))

    def test_tokenization_removes_local_checkout_and_home_paths(self):
        root = Path.home() / 'owned-measurement'
        result = comparison.tokenized([root / 'source/main.rs', HERE / 'rust/Cargo.toml', Path.home() / '.cargo/bin/rustc'], root)
        self.assertEqual(result, ['<run>/source/main.rs', '<experiment>/rust/Cargo.toml', '<home>/.cargo/bin/rustc'])


class CorrectiveFixtureTests(unittest.TestCase):
    def test_functional_budget_is_bounded_and_independent_of_scored_launches(self):
        functional = json.loads((HERE / 'fixtures/cases.json').read_bytes())
        for case in functional['cases']:
            expected = 1500 if case['id'] in ['timeout', 'descendant_pipe'] else 5000
            self.assertEqual(case['timeout_ms'], expected)
            self.assertLess(case['timeout_ms'] + 2000, functional['outer_deadline_seconds'] * 1000)
        self.assertEqual(comparison.load_plan(HERE / 'comparison-plan.json')['launch_samples']['timeout_ms'], 1500)
        report = valid_report(comparison.load_plan(HERE / 'comparison-plan.json'))
        report['samples'][-1]['command'][-1] = '5000'
        self.assertIn('scored_launch_budget', comparison.validate_report(report, comparison.load_plan(HERE / 'comparison-plan.json'), check_inputs=False))

    def test_intentional_sleep_remains_longer_than_negative_deadline(self):
        corpus = json.loads((HERE / 'fixtures/cases.json').read_bytes())
        cases = {row['id']: row for row in corpus['cases']}
        for name in ['timeout', 'descendant_pipe']:
            self.assertEqual(cases[name]['timeout_ms'], 1500)
            self.assertEqual(cases[name]['expected'], 'timeout')
        source = (HERE / 'fixtures/child.c').read_text()
        delay = int(re.search(r'!strcmp\(mode, "delay"\)\) \{ delay_ms\((\d+)\)', source).group(1))
        self.assertGreater(delay, cases['timeout']['timeout_ms'])
        self.assertLess(delay, corpus['outer_deadline_seconds'] * 1000)

    def test_timeouts_still_require_observed_identities(self):
        class OwnedProcess:
            def __init__(self, args, **kwargs):
                self.args = args
                self.returncode = 4
            def poll(self):
                return None
            def terminate(self):
                pass
            def wait(self, **kwargs):
                return 0
        def capture(process, timeout):
            candidate = Path(str(process.args[0])).name.split('-')[0]
            value = {'experiment_version': 1, 'candidate': candidate, 'fixture_only': True, 'runtime_eligible': False,
                     'host_architecture': 'arm64', 'translated': False, 'classification': 'timeout', 'spawned': True,
                     'reaped': True, 'cleanup': 'passed', 'exit_code': None, 'signal': 9, 'stdout_bytes': 0, 'stderr_bytes': 0}
            return json.dumps(value).encode(), b'', None
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); build = root / 'build'; (build / 'bin').mkdir(parents=True)
            (build / 'bin/fixture-child').write_bytes(b'Owned inert test bytes; never executed.')
            (build / 'build.json').write_text(json.dumps({'toolchains': {'clang': 'Apple clang version 21.0.0 (owned test)', 'sdk': '26.5'}}))
            for name in ['timeout', 'descendant_pipe']:
                with patch.object(comparison.corpus, 'verify_build'), patch.object(comparison.corpus, 'oracle_result', return_value={'eligible': True, 'record_valid': True}), patch.object(comparison.corpus.subprocess, 'Popen', OwnedProcess), patch.object(comparison.corpus, 'capture_bounded', capture), contextlib.redirect_stdout(io.StringIO()):
                    report = comparison.corpus.run_cases(build, Path(sys.executable), name)
                self.assertFalse(report['passed'])
                for row in report['results']:
                    self.assertIn('missing_child_observation', row['errors'])
                    if name == 'descendant_pipe':
                        self.assertIn('missing_descendant_observation', row['errors'])
                    self.assertFalse(row['owned_identities_gone'])

    def test_historical_failure_bytes_are_part_of_current_record(self):
        report = valid_report(comparison.load_plan(HERE / 'comparison-plan.json'))
        report['historical_evidence']['prior-comparison-attempts.json']['sha256'] = '0' * 64
        self.assertIn('historical_identity', comparison.validate_report(report, comparison.load_plan(HERE / 'comparison-plan.json')))


class CaptureTests(unittest.TestCase):
    def test_nonzero_attempt_keeps_exit_and_logs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result, stdout, stderr = comparison.measured_command([sys.executable, '-c', 'print("owned"); raise SystemExit(7)'], root, comparison.native_build.controlled_environment(), root / 'attempt', 2)
            self.assertEqual(result['returncode'], 7)
            self.assertIsNone(result['watchdog'])
            self.assertEqual(stdout, b'owned\n')
            self.assertEqual(stderr, b'')
            self.assertTrue((root / 'attempt.json').is_file())

    def test_deadline_reaps_owned_command(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result, _, _ = comparison.measured_command([sys.executable, '-c', 'import time; time.sleep(10)'], root, comparison.native_build.controlled_environment(), root / 'attempt', .03)
            self.assertEqual(result['watchdog'], 'outer_deadline')
            self.assertLess(result['returncode'], 0)
            self.assertLess(result['duration_seconds'], 2.5)

    def test_group_signal_permission_failure_falls_back_to_owned_leader(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(comparison.os, 'killpg', side_effect=PermissionError):
                result, _, _ = comparison.measured_command([sys.executable, '-c', 'import time; time.sleep(10)'], root, comparison.native_build.controlled_environment(), root / 'attempt', .03)
            self.assertEqual(result['watchdog'], 'outer_deadline')
            self.assertLess(result['returncode'], 0)
            self.assertLess(result['duration_seconds'], 2.5)

    def test_exit_burst_still_has_final_output_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result, stdout, _ = comparison.measured_command([sys.executable, '-c', 'import os; os.write(1, b"x" * (9 * 1024 * 1024))'], root, comparison.native_build.controlled_environment(), root / 'attempt', 2)
            self.assertEqual(result['watchdog'], 'outer_output_limit')
            self.assertIsNone(result['stdout_sha256'])
            self.assertLessEqual(len(stdout), 8 * 1024 * 1024 + 1)


if __name__ == '__main__':
    unittest.main()
