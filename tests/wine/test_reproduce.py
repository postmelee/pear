"""Coordinator containment tests; no Wine build, signing or runtime execution."""
from pathlib import Path
import io
import sys
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
from common import Error
import reproduce


class SerialExecutionTests(unittest.TestCase):
    def setUp(self):
        self.names = ('prepare_inputs', 'native_build', 'signing', 'bootstrap')
        self.start = {'immutable': 'input identity'}
        self.paths = {'root': Path('/unused-owned-root')}
        self.rows, self.terminals, self.calls = [], [], []
        def row(start, name, status, **values):
            self.assertIs(start, self.start)
            value = dict(id=name, status=status, **values)
            self.rows.append(value)
            return value
        self.evidence = types.SimpleNamespace(OPERATIONS=self.names,
            load_start=mock.Mock(return_value=self.start), operation_result=row,
            write_terminal=lambda root, start, rows, error: self.terminals.append((root, start, rows, error)))
        self.patch = mock.patch.dict(sys.modules, {'reproduction_evidence': self.evidence})
        self.patch.start(); self.addCleanup(self.patch.stop)
        self.output = mock.patch('sys.stdout', new_callable=io.StringIO)
        self.output.start(); self.addCleanup(self.output.stop)

    def steps(self, failed=None, error=None):
        def step(name):
            self.calls.append(name)
            if name == failed:
                raise error
        return [(name, lambda name=name: step(name)) for name in self.names]

    def test_serial_completion_records_order_and_does_not_claim_independent_gate(self):
        code = reproduce.execute(self.start, self.paths, self.steps())
        self.assertEqual(code, 0)
        self.assertEqual(self.calls, list(self.names))
        self.assertEqual([row['status'] for row in self.rows], ['passed'] * 4)
        for previous, current in zip(self.rows, self.rows[1:]):
            self.assertLessEqual(previous['finished_ns'], current['started_ns'])
        self.assertEqual(len(self.terminals), 1)
        self.assertIsNone(self.terminals[0][3])

    def test_failed_build_preserves_failure_and_never_signs_or_launches(self):
        code = reproduce.execute(self.start, self.paths,
            self.steps('native_build', Error('fixture_build_failure')))
        self.assertEqual(code, 3)
        self.assertEqual(self.calls, ['prepare_inputs', 'native_build'])
        self.assertEqual([row['status'] for row in self.rows], ['passed', 'failed', 'unperformed', 'unperformed'])
        self.assertEqual(self.rows[1]['error'], 'fixture_build_failure')
        self.assertEqual(self.terminals[0][3], 'fixture_build_failure')
        self.assertNotIn('started_ns', self.rows[-1])

    def test_changed_inputs_stop_before_mutation_and_keep_terminal_record(self):
        self.evidence.load_start.side_effect = [self.start, {'immutable': 'changed'}]
        self.assertEqual(reproduce.execute(self.start, self.paths, self.steps()), 3)
        self.assertEqual(self.calls, ['prepare_inputs'])
        self.assertEqual(self.terminals[0][3], 'reproduction_start_changed')

    def test_interruption_records_unperformed_successors(self):
        self.assertEqual(reproduce.execute(self.start, self.paths,
            self.steps('prepare_inputs', KeyboardInterrupt())), 3)
        self.assertEqual(self.calls, ['prepare_inputs'])
        self.assertEqual(self.terminals[0][3], 'reproduction_interrupted')
        self.assertEqual([row['status'] for row in self.rows], ['failed'] + ['unperformed'] * 3)

    def test_os_error_does_not_publish_local_path(self):
        reproduce.execute(self.start, self.paths,
            self.steps('prepare_inputs', OSError('/Users/PRIVATE_SECRET/identity')))
        self.assertNotIn('PRIVATE_SECRET', repr(self.terminals))
        self.assertEqual(self.terminals[0][3], 'reproduction_operation_failed')

    def test_missing_or_reordered_steps_are_rejected_before_work(self):
        with self.assertRaisesRegex(Error, 'reproduction_operation_order'):
            reproduce.execute(self.start, self.paths, list(reversed(self.steps())))
        self.assertEqual(self.calls, [])
        self.assertEqual(self.terminals, [])


if __name__ == '__main__':
    unittest.main()
