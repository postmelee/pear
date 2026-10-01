"""Actual coordinator/receipt integration using only temporary synthetic records.

No Wine build, signing, guest execution or host compatibility operation occurs.
The static baseline reference and storage preflight are substituted; receipt
creation, source-drift checks, operation capture and terminal serialization are
production implementations.
"""
from pathlib import Path
import hashlib
import io
import json
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
from common import Error, encoded, sha256
import reproduce
import arena_reproduction as fresh_arena
import reproduction_evidence as evidence


class ReceiptExecutionIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='pear-reproduction-integration-')
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name).resolve()
        self.task = self.repo / '.build/task4'
        self.task.mkdir(parents=True)
        self.producer = self.repo / 'producer.py'
        self.producer.write_text('# Original synthetic producer identity.\n')
        configurations = {key: 'records/' + key + '.json' for key in evidence.CONFIGURATION}
        for name in configurations.values():
            path = self.repo / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b'{}\n')
        self.source_cache = self.repo / 'source-cache'
        self.source_cache.mkdir()
        self.tools = self.task / 'tools'
        self.tools.mkdir()
        (self.tools / 'prepared.json').write_bytes(b'{}\n')
        self.local_signing = self.task / 'private/local.json'
        self.local_signing.parent.mkdir()
        self.local_signing.write_bytes(b'{}\n')
        replacements = {
            'REPO': self.repo, 'PRODUCERS': ('producer.py',),
            'SOURCES': {'synthetic': 'producer.py'}, 'CONFIGURATION': configurations,
            'REFERENCE_BUILD': self.task / 'reference',
        }
        for name, value in replacements.items():
            patch = mock.patch.object(evidence, name, value)
            patch.start(); self.addCleanup(patch.stop)
        reference = {'build': {'path': '.build/task4/reference/build.json', 'sha256': 'a' * 64},
                     'public': {'path': 'reference.json', 'sha256': 'b' * 64}}
        for patch in (mock.patch.object(evidence, '_reference', return_value=reference),
                      mock.patch.object(evidence.shutil, 'disk_usage',
                                        return_value=type('Usage', (), {'free': 30 * 1024**3})()),
                      mock.patch('sys.stdout', new_callable=io.StringIO)):
            patch.start(); self.addCleanup(patch.stop)
        self.paths = evidence.layout(self.task / 'reproduction-fixture')
        self.start = evidence.create_start(self.paths['root'], source_cache=self.source_cache,
            tools=self.tools, local_signing=self.local_signing)
        self.calls = []

    def write_operation(self, name):
        path, directory = evidence.operation_paths(self.paths)[name]
        directory.mkdir(parents=True, exist_ok=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded({'synthetic_operation': name}))
        return path

    def steps(self, overrides=None):
        overrides = overrides or {}
        def action(name):
            self.calls.append(name)
            if name in overrides:
                overrides[name]()
            else:
                self.write_operation(name)
        return [(name, lambda name=name: action(name)) for name in evidence.OPERATIONS]

    def terminal(self):
        path = self.paths['root'] / 'reproduction.json'
        self.assertTrue(path.is_file())
        value = json.loads(path.read_bytes())
        self.assertEqual(value['start_sha256'],
                         hashlib.sha256(encoded(self.start)).hexdigest())
        self.assertFalse(value['runtime_qualified'])
        self.assertFalse(value['game_qualified'])
        self.assertFalse(value['distribution_qualified'])
        return value

    def arena_failure(self, *, start_error=None, probe_error=None):
        original_create = fresh_arena.probe.base.create_output
        def begin(root, _):
            if start_error is not None:
                raise start_error
            (root / 'start.json').write_bytes(encoded({'synthetic': True}))
        def fail():
            return fresh_arena.run(self.local_signing, self.paths['native_arena'])
        with mock.patch.object(fresh_arena.probe.base, 'create_output',
                    side_effect=lambda path: original_create(path, repo=self.repo)), \
             mock.patch.object(fresh_arena, '_start', side_effect=begin), \
             mock.patch.object(fresh_arena.probe, 'run', return_value={
                    'native_prerequisite_passed': False, 'error': probe_error}):
            self.assertEqual(reproduce.execute(self.start, self.paths,
                self.steps({'native_arena': fail})), 3)
        terminal = self.terminal()
        private = json.loads((self.paths['native_arena'] / 'reproduction.json').read_bytes())
        self.assertEqual(terminal['error'], private['error'])
        failed_index = evidence.OPERATIONS.index('native_arena')
        self.assertEqual(terminal['operations'][failed_index]['record']['sha256'],
            sha256(self.paths['native_arena'] / 'reproduction.json'))
        self.assertTrue(all(row['status'] == 'unperformed'
            for row in terminal['operations'][failed_index + 1:]))
        return private

    def test_actual_arena_wrapper_oserror_keeps_outer_terminal(self):
        private = self.arena_failure(start_error=OSError('synthetic unavailable profile'))
        self.assertEqual(private['error'], 'fresh_arena_oserror')

    def test_actual_arena_wrapped_interruption_keeps_original_and_outer_terminal(self):
        private = self.arena_failure(probe_error='arena_KeyboardInterrupt')
        self.assertEqual(private['error'], 'arena_keyboardinterrupt')
        self.assertEqual(private['original_error'], 'arena_KeyboardInterrupt')

    def test_real_receipts_complete_without_claiming_qualification(self):
        self.assertEqual(reproduce.execute(self.start, self.paths, self.steps()), 0)
        terminal = self.terminal()
        self.assertTrue(terminal['complete'])
        self.assertEqual(self.calls, list(evidence.OPERATIONS))
        self.assertEqual(evidence._terminal(self.paths['root'], self.start), terminal)
        for row in terminal['operations']:
            self.assertEqual(row['status'], 'passed')
            self.assertEqual(row['record']['sha256'], sha256(self.repo / row['record']['path']))
            self.assertIsNone(row['error'])

    def test_first_failure_without_artifact_keeps_all_unperformed_successors(self):
        def fail():
            raise Error('synthetic_preparation_failure')
        self.assertEqual(reproduce.execute(self.start, self.paths,
            self.steps({'prepare_inputs': fail})), 3)
        terminal = self.terminal()
        self.assertEqual(self.calls, ['prepare_inputs'])
        self.assertFalse(terminal['complete'])
        self.assertEqual(terminal['error'], 'synthetic_preparation_failure')
        failed, *unperformed = terminal['operations']
        self.assertEqual(failed['status'], 'failed')
        self.assertIsNone(failed['record'])
        for row in unperformed:
            self.assertEqual(row['status'], 'unperformed')
            self.assertIsNone(row['error'])
            self.assertIsNone(row['record'])
            self.assertIsNone(row['directory_identity'])
            self.assertIsNone(row['started_ns'])
            self.assertIsNone(row['finished_ns'])
        with self.assertRaisesRegex(Error, 'reproduction_incomplete'):
            evidence._terminal(self.paths['root'], self.start)

    def test_partial_failed_record_keeps_original_error_and_stops_before_signing(self):
        def fail():
            self.write_operation('native_build')
            raise Error('synthetic_compiler_failure')
        self.assertEqual(reproduce.execute(self.start, self.paths,
            self.steps({'native_build': fail})), 3)
        terminal = self.terminal()
        failed_index = evidence.OPERATIONS.index('native_build')
        self.assertEqual(self.calls, list(evidence.OPERATIONS[:failed_index + 1]))
        row = terminal['operations'][failed_index]
        self.assertEqual(row['error'], 'synthetic_compiler_failure')
        self.assertEqual(row['record']['sha256'], sha256(self.paths['native_build'] / 'build.json'))
        self.assertTrue(all(row['status'] == 'unperformed' for row in terminal['operations'][failed_index + 1:]))
        self.assertFalse(self.paths['signed'].exists())
        self.assertFalse(self.paths['bootstrap'].exists())

    def test_missing_success_artifact_becomes_failure_receipt(self):
        self.assertEqual(reproduce.execute(self.start, self.paths,
            self.steps({'prepare_inputs': lambda: None})), 3)
        terminal = self.terminal()
        self.assertEqual(terminal['error'], 'reproduction_missing_artifact')
        self.assertEqual(terminal['operations'][0]['status'], 'failed')
        self.assertEqual(self.calls, ['prepare_inputs'])

    def test_producer_drift_preserves_partial_history_instead_of_rereading_changed_input(self):
        def first():
            self.write_operation('prepare_inputs')
            self.producer.write_text('# Changed synthetic producer.\n')
        self.assertEqual(reproduce.execute(self.start, self.paths,
            self.steps({'prepare_inputs': first})), 3)
        terminal = self.terminal()
        self.assertEqual(self.calls, ['prepare_inputs'])
        self.assertEqual(terminal['operations'][0]['status'], 'passed')
        self.assertEqual(terminal['operations'][1]['status'], 'failed')
        self.assertEqual(terminal['error'], 'reproduction_producer_changed')
        with self.assertRaisesRegex(Error, 'reproduction_producer_changed'):
            evidence.load_start(self.paths['root'])

    def test_interruption_keeps_primary_error_and_existing_prior_artifact_digest(self):
        first_path, _ = evidence.operation_paths(self.paths)['prepare_inputs']
        def interrupt():
            first_path.write_text('changed after its receipt')
            raise KeyboardInterrupt()
        self.assertEqual(reproduce.execute(self.start, self.paths,
            self.steps({'toolchain_check': interrupt})), 3)
        terminal = self.terminal()
        self.assertEqual(terminal['error'], 'reproduction_interrupted')
        self.assertNotEqual(terminal['operations'][0]['record']['sha256'], sha256(first_path))
        self.assertEqual(self.calls, ['prepare_inputs', 'toolchain_check'])
        self.assertFalse(self.paths['native_build'].exists())


if __name__ == '__main__':
    unittest.main()
