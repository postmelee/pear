"""Pure offline evidence controls; injected facts never qualify a runtime."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
REPO = Path(os.environ.get('PEAR_FEX_TEST_REPO', Path(__file__).resolve().parents[2])).resolve(strict=True)
sys.path.insert(0, str(REPO))
from tools.fex import memory_fex_assess as a


def failed_record():
    value = dict.fromkeys(a.FAILURE_KEYS)
    value.update(schema_version=1, record_kind='fex_memory_modules_build', scope='fex_component',
                 passed=False, modules_built_not_loaded=False, phase='artifact_replay',
                 primary_error={'code': 'fex_memory_owner_macro', 'exception_type': 'Error'},
                 qualification=dict(a.reader.QUALIFICATION),
                 commands=[{'exit_code': 0, 'status': 'completed'} for _ in range(9)],
                 **dict.fromkeys(a.reader.FALSE_FLAGS, False))
    return value


class SourceIdentity(unittest.TestCase):
    def test_genuine_supplied_package_identity(self):
        self.assertEqual(a.source_identity(REPO), REPO)
    def test_unrelated_repository_cannot_select_reader(self):
        with tempfile.TemporaryDirectory(prefix='pear-assessment-identity-') as directory:
            with self.assertRaises(a.Error): a.source_identity(Path(directory).resolve())
    def test_noncanonical_root_refused(self):
        with self.assertRaises(a.Error): a.canonical_root(str(REPO) + '/.')
    def test_double_root_refused(self):
        with self.assertRaises(a.Error): a.canonical_root('/' + str(REPO))
    def test_nonabsolute_root_refused(self):
        with self.assertRaises(a.Error): a.canonical_root('relative-directory')
    def test_reference_source_alias_refused(self):
        with tempfile.TemporaryDirectory(prefix='pear-assessment-identity-') as directory:
            root = Path(directory).resolve(); original = root / 'original.bin'
            original.write_bytes(b'original'); (root / 'alias.bin').symlink_to(original)
            with self.assertRaises(a.Error): a.reference(root / 'alias.bin')
    def test_current_unreviewed_reader_bytes_refused(self):
        with patch.object(a, 'REVIEWED_READER_SHA', '0' * 64), self.assertRaises(a.Error): a.source_identity(REPO)


class FailureScope(unittest.TestCase):
    def setUp(self): self.value = failed_record()
    def check(self):
        raw = a.encoded(self.value)
        return a.failure_gate(self.value, raw, a.reader.H(raw))
    def refuse(self):
        with self.assertRaises(a.Error): self.check()
    def test_original_failure_stays_failed(self):
        result = self.check()
        self.assertIs(result['passed'], False)
        self.assertIs(result['modules_built_not_loaded'], False)
    def test_wrong_failure_digest(self):
        with self.assertRaises(a.Error): a.failure_gate(self.value, a.encoded(self.value), '0' * 64)
    def test_missing_failure_digest(self):
        with self.assertRaises(a.Error): a.failure_gate(self.value, a.encoded(self.value), None)
    def test_historical_success_refused(self): self.value['passed'] = True; self.refuse()
    def test_historical_loading_claim_refused(self): self.value['module_loading'] = True; self.refuse()
    def test_wrong_phase_refused(self): self.value['phase'] = 'command_execution'; self.refuse()
    def test_unreviewed_primary_failure_refused(self): self.value['primary_error']['code'] = 'link_error'; self.refuse()
    def test_missing_original_command_refused(self): self.value['commands'].pop(); self.refuse()
    def test_failed_original_command_refused(self): self.value['commands'][0]['exit_code'] = 1; self.refuse()
    def test_unperformed_original_command_refused(self): self.value['commands'][0]['status'] = 'unperformed'; self.refuse()
    def test_boolean_exit_code_refused(self): self.value['commands'][0]['exit_code'] = False; self.refuse()
    def test_missing_qualification_refused(self): self.value.pop('metadata_qualified'); self.refuse()
    def test_extra_scope_refused(self): self.value['runtime_ready'] = True; self.refuse()


class LegacySnapshots(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pear-assessment-snapshots-')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve() / 'repo'
        self.root = self.repo / '.build/task5/historical-failure'
        (self.root / 'inputs').mkdir(parents=True)
        self.reader = self.repo / a.READER_PATH
        self.other = self.repo / 'tools/fex/build.py'
        self.reader.parent.mkdir(parents=True, exist_ok=True)
        self.old = b'old reviewed reader fixture\n'
        self.new = b'new reviewed reader fixture\n'
        self.reader.write_bytes(self.new); self.reader.chmod(0o644)
        self.other.write_bytes(b'unchanged producer fixture\n'); self.other.chmod(0o644)
        self.paths = sorted([self.reader, self.other], key=str)
        self.rows = []
        for i, path in enumerate(self.paths):
            data = self.old if path == self.reader else path.read_bytes()
            name = f'inputs/{i:04d}.bin'
            (self.root / name).write_bytes(data); (self.root / name).chmod(0o600)
            self.rows.append({'source': str(path), 'copy': name, 'sha256': a.reader.H(data), 'size_bytes': len(data)})
        # Only the approved hash pair is injected for finite fixture bytes.
        for key, value in [('OLD_READER_SHA', a.reader.H(self.old)), ('REVIEWED_READER_SHA', a.reader.H(self.new))]:
            p = patch.object(a, key, value); p.start(); self.addCleanup(p.stop)
    def check(self): return a.historical_snapshots(self.root, self.rows, self.paths, self.repo)
    def refuse(self):
        with self.assertRaises(a.Error): self.check()
    def test_exact_one_reviewed_transition(self):
        result = self.check(); self.assertEqual(result['reviewed_reader_transition_count'], 1)
        self.assertTrue(result['all_other_current_inputs_equal_original_copies'])
    def test_changed_other_current_producer_refused(self): self.other.write_bytes(b'changed'); self.refuse()
    def test_changed_old_reader_copy_refused(self):
        i = self.paths.index(self.reader); (self.root / self.rows[i]['copy']).write_bytes(b'changed'); self.refuse()
    def test_changed_current_reader_refused(self): self.reader.write_bytes(b'changed'); self.refuse()
    def test_wrong_snapshot_mode_refused(self): (self.root / self.rows[0]['copy']).chmod(0o644); self.refuse()
    def test_missing_snapshot_refused(self): self.rows.pop(); self.refuse()
    def test_extra_snapshot_file_refused(self): (self.root / 'inputs/extra.bin').write_bytes(b'x'); self.refuse()
    def test_reordered_snapshot_refused(self): self.rows.reverse(); self.refuse()
    def test_wrong_original_path_refused(self): self.rows[0]['source'] = str(self.reader); self.refuse()
    def test_wrong_original_size_refused(self): self.rows[0]['size_bytes'] += 1; self.refuse()
    def test_reader_copy_already_new_does_not_erase_transition(self):
        i = self.paths.index(self.reader); row = self.rows[i]
        (self.root / row['copy']).write_bytes(self.new)
        row.update(sha256=a.reader.H(self.new), size_bytes=len(self.new)); self.refuse()
    def test_no_reviewed_reader_member_refused(self):
        self.paths = [self.other]; self.rows = self.rows[:1]; self.refuse()


class ProducerTransition(unittest.TestCase):
    def setUp(self):
        self.current = {p: '1' * 64 for p in a.reader.LOCAL_PRODUCERS}
        self.current[a.READER_PATH] = a.REVIEWED_READER_SHA
        self.old = dict(self.current); self.old[a.READER_PATH] = a.OLD_READER_SHA
    def check(self):
        with patch.object(a, 'reference', side_effect=lambda path: {'sha256': self.current[path.as_posix().removeprefix('/repo/')]}):
            return a.producer_transition({'producer_sha256': self.old}, Path('/repo'))
    def refuse(self):
        with self.assertRaises(a.Error): self.check()
    def test_exact_reviewed_reader_only(self): self.assertTrue(self.check()['other_historical_producers_unchanged'])
    def test_other_producer_changed(self): self.current['tools/fex/build.py'] = '2' * 64; self.refuse()
    def test_missing_historical_producer(self): self.old.pop('tools/fex/build.py'); self.refuse()
    def test_extra_historical_producer(self): self.old['arbitrary.py'] = '1' * 64; self.refuse()
    def test_wrong_predecessor_reader(self): self.old[a.READER_PATH] = '2' * 64; self.refuse()
    def test_unreviewed_current_reader(self): self.current[a.READER_PATH] = '2' * 64; self.refuse()


class SeparateAssessment(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pear-offline-assessment-')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve() / 'repo'
        self.build = self.repo / '.build/task5/historical-failure'
        self.build.mkdir(parents=True)
        (self.build / 'failure.json').write_bytes(b'original failure bytes\n')
        self.original = (self.build / 'failure.json').read_bytes()
        self.input = self.repo / 'input.bin'; self.input.write_bytes(b'bound byte fixture\n'); self.input.chmod(0o644)
        self.output = self.repo / '.build/task5/assessment'
        self.policy = {'scope': a.POLICY_SCOPE, 'predecessor_sha256': a.OLD_READER_SHA,
                       'current_sha256': a.REVIEWED_READER_SHA, 'other_historical_producers_unchanged': True}
        self.observed = {'historical_failure': a.reference(self.build / 'failure.json'), 'reader_policy': self.policy,
                         'original_command_count': 9, 'artifact_count': 32, 'synthetic_parser_control': True}
        p = patch.object(a, 'source_identity', return_value=self.repo); p.start(); self.addCleanup(p.stop)
        p = patch.object(a, 'current_producers', return_value={'injected': '1' * 64}); p.start(); self.addCleanup(p.stop)
        self.guard = patch.object(a.reader, 'inspect_modules', side_effect=AssertionError('No real artifacts in synthetic control'))
        self.guard.start(); self.addCleanup(self.guard.stop)
    def evaluator(self): return deepcopy(self.observed), [self.input]
    def run_assess(self, results=None):
        with patch.object(a, 'evaluate', side_effect=results or [self.evaluator(), self.evaluator()]):
            return a.assess(self.build, a.reader.H(self.original), self.output, repo=self.repo)
    def test_distinct_record_and_no_original_rewrite(self):
        result = self.run_assess()
        self.assertIs(result['historical_builder_passed'], False)
        self.assertIs(result['compiler_invoked'], False)
        self.assertIs(result['new_native_execution'], False)
        self.assertTrue(all(result[k] is False for k in a.reader.FALSE_FLAGS))
        self.assertEqual((self.build / 'failure.json').read_bytes(), self.original)
        self.assertFalse((self.build / 'build.json').exists())
        self.assertTrue((self.output / 'assessment.json').exists())
    def test_current_assessment_replays_separately(self):
        self.run_assess()
        with patch.object(a, 'evaluate', return_value=self.evaluator()):
            self.assertIs(a.verify_assessment(self.output, repo=self.repo)['historical_builder_passed'], False)
    def test_changed_artifact_after_assessment_refused(self):
        self.run_assess(); changed = self.evaluator(); changed[0]['artifact_count'] = 31
        with patch.object(a, 'evaluate', return_value=changed), self.assertRaises(a.Error):
            a.verify_assessment(self.output, repo=self.repo)
    def test_changed_snapshot_current_input_refused(self):
        self.run_assess(); self.input.write_bytes(b'changed')
        with patch.object(a, 'evaluate', return_value=self.evaluator()), self.assertRaises(a.Error):
            a.verify_assessment(self.output, repo=self.repo)
    def test_original_failure_refusal_preserved(self):
        exc = a.Error('original_native_or_source_failure')
        with self.assertRaises(a.Error) as caught: self.run_assess([exc])
        self.assertIs(caught.exception, exc)
        value, _ = a.reader.record_bytes(self.output, 'failed-assessment.json')
        self.assertEqual(value['primary_error']['code'], 'original_native_or_source_failure')
        self.assertFalse((self.output / 'assessment.json').exists())
        self.assertEqual((self.build / 'failure.json').read_bytes(), self.original)
    def test_failed_storage_record_does_not_mask_primary(self):
        exc = a.Error('primary_input_error')
        with patch.object(a, 'write_json', side_effect=OSError(28, 'injected disk full')):
            with self.assertRaises(a.Error) as caught: self.run_assess([exc])
        self.assertIs(caught.exception, exc)
        self.assertEqual(exc.assessment_record_error['exception_type'], 'OSError')
    def test_changed_during_inspection_refused(self):
        first = self.evaluator(); second = self.evaluator(); second[0]['artifact_count'] = 31
        with self.assertRaises(a.Error): self.run_assess([first, second])
        self.assertFalse((self.output / 'assessment.json').exists())
    def test_nonempty_output_preserved(self):
        self.output.mkdir(); (self.output / 'existing.bin').write_bytes(b'keep')
        with self.assertRaises(a.Error): self.run_assess()
        self.assertEqual((self.output / 'existing.bin').read_bytes(), b'keep')
    def test_original_build_cannot_be_output(self):
        self.output = self.build
        with self.assertRaises(a.Error): self.run_assess()
        self.assertEqual((self.build / 'failure.json').read_bytes(), self.original)
    def test_failure_record_blocks_verification(self):
        self.run_assess(); (self.output / 'failed-assessment.json').write_bytes(b'{}')
        with patch.object(a, 'evaluate', return_value=self.evaluator()), self.assertRaises(a.Error):
            a.verify_assessment(self.output, repo=self.repo)
    def test_extra_output_blocks_verification(self):
        self.run_assess(); (self.output / 'arbitrary.bin').write_bytes(b'extra')
        with patch.object(a, 'evaluate', return_value=self.evaluator()), self.assertRaises(a.Error):
            a.verify_assessment(self.output, repo=self.repo)
    def test_qualification_tampering_blocks_verification(self):
        self.run_assess(); value, _ = a.reader.record_bytes(self.output, 'assessment.json')
        value['metadata_qualified'] = True
        (self.output / 'assessment.json').write_bytes(a.encoded(value))
        with patch.object(a, 'evaluate', return_value=self.evaluator()), self.assertRaises(a.Error):
            a.verify_assessment(self.output, repo=self.repo)


class AssessmentRecordBounds(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pear-assessment-budget-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
    def read(self, raw):
        (self.root / 'assessment.json').write_bytes(raw)
        return a.assessment_record_bytes(self.root)
    def refuse(self, raw, code):
        with self.assertRaises(a.Error) as caught: self.read(raw)
        self.assertEqual(caught.exception.code, code)
    def test_structure_above_legacy_budget_roundtrips(self):
        value = {'values': [0] * 250001}
        raw = a.encoded(value)
        with self.assertRaises(a.Error) as caught: a.reader.decode_json(raw)
        self.assertEqual(caught.exception.code, 'json_structure_limit')
        a.write_assessment(self.root, value)
        observed, saved = a.assessment_record_bytes(self.root)
        self.assertEqual(observed, value); self.assertEqual(saved, raw)
        self.assertEqual((self.root / 'assessment.json').stat().st_mode & 0o777, 0o600)
    def test_exact_node_budget_including_keys(self):
        value = {'values': [0] * (a.ASSESSMENT_MAX_NODES - 3)}
        a.write_assessment(self.root, value)
        self.assertEqual(a.assessment_record_bytes(self.root)[0], value)
    def test_one_excess_node_refused_before_write(self):
        value = {'values': [0] * (a.ASSESSMENT_MAX_NODES - 2)}
        with self.assertRaises(a.Error) as caught: a.write_assessment(self.root, value)
        self.assertEqual(caught.exception.code, 'json_structure_limit')
        self.assertFalse((self.root / 'assessment.json').exists())
    def test_excess_nodes_on_read_refused(self):
        self.refuse(a.encoded({'values': [0] * (a.ASSESSMENT_MAX_NODES - 2)}), 'json_structure_limit')
    def test_exact_byte_budget_accepted(self):
        raw = b'{"v":0}' + b' ' * (a.ASSESSMENT_MAX_BYTES - 7)
        observed, saved = self.read(raw)
        self.assertEqual(observed, {'v': 0}); self.assertEqual(saved, raw)
    def test_one_excess_byte_refused(self):
        self.refuse(b'{}' + b' ' * (a.ASSESSMENT_MAX_BYTES - 1), 'fex_memory_source_file_kind')
    def test_writer_byte_budget_refuses_before_write(self):
        value = {'padding': ['x' * 262144] * 32}
        with self.assertRaises(a.Error) as caught: a.write_assessment(self.root, value)
        self.assertEqual(caught.exception.code, 'input_size_limit')
        self.assertFalse((self.root / 'assessment.json').exists())
    def test_duplicate_key_still_refused(self):
        self.refuse(b'{"v":0,"v":1}', 'duplicate_json_key')
    def test_depth_still_refused(self):
        self.refuse(b'{"v":' + b'[' * 49 + b'0' + b']' * 49 + b'}', 'json_structure_limit')
    def test_noninteger_number_still_refused(self):
        self.refuse(b'{"v":0.5}', 'noninteger_json_number')
    def test_key_bound_still_refused(self):
        self.refuse(a.encoded({'x' * 257: 0}), 'json_key_limit')
    def test_scalar_string_bound_still_refused(self):
        self.refuse(a.encoded({'v': 'x' * 262145}), 'json_string_limit')
    def test_root_shape_still_refused(self):
        self.refuse(b'[]', 'invalid_document_shape')
    def test_symlink_leaf_refused(self):
        donor = self.root / 'donor.json'; donor.write_bytes(b'{}')
        (self.root / 'assessment.json').symlink_to(donor)
        with self.assertRaises((a.Error, OSError)): a.assessment_record_bytes(self.root)
    def test_hardlink_leaf_refused(self):
        donor = self.root / 'donor.json'; donor.write_bytes(b'{}')
        os.link(donor, self.root / 'assessment.json')
        with self.assertRaises(a.Error) as caught: a.assessment_record_bytes(self.root)
        self.assertEqual(caught.exception.code, 'fex_memory_source_file_kind')
    def test_mutation_during_fd_read_refused(self):
        (self.root / 'assessment.json').write_bytes(b'{}')
        actual = os.fstat; calls = []
        def observe(fd):
            info = actual(fd); calls.append(info)
            # open_relative first reads the descriptor's file kind.
            if len(calls) == 3:
                values = list(info); values[8] += 1
                return os.stat_result(values)
            return info
        with patch.object(a.reader.os, 'fstat', side_effect=observe):
            with self.assertRaises(a.Error) as caught: a.assessment_record_bytes(self.root)
        self.assertEqual(caught.exception.code, 'fex_memory_source_file_changed')
    def test_existing_success_record_preserved(self):
        (self.root / 'assessment.json').write_bytes(b'{"old":true}')
        with self.assertRaises(FileExistsError): a.write_assessment(self.root, {'new': True})
        self.assertEqual((self.root / 'assessment.json').read_bytes(), b'{"old":true}')


class CompleteSuccessfulBudget(unittest.TestCase):
    setUp = SeparateAssessment.setUp
    evaluator = SeparateAssessment.evaluator
    run_assess = SeparateAssessment.run_assess
    def test_full_record_nodes_refused_and_failure_preserved(self):
        # The complete record, including keys and snapshots, must pass the budget.
        self.observed['values'] = [0] * (a.ASSESSMENT_MAX_NODES - 3)
        with self.assertRaises(a.Error) as caught: self.run_assess()
        self.assertEqual(caught.exception.code, 'json_structure_limit')
        self.assertFalse((self.output / 'assessment.json').exists())
        # Failed-record decoding retains its historical budget; this synthetic
        # over-budget failure is inspected as data, never admitted as success.
        value = json.loads((self.output / 'failed-assessment.json').read_bytes())
        self.assertIs(value['passed'], False)
        self.assertEqual(value['primary_error']['code'], 'json_structure_limit')
        self.assertEqual((self.build / 'failure.json').read_bytes(), self.original)


if __name__ == '__main__': unittest.main()
