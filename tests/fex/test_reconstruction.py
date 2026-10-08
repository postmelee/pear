"""Reject incomplete or altered fresh-build evidence before signing a runtime."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from tools.fex.common import Error
from tools.fex.reconstruction_check import command_gate, H


class ReconstructionAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        log = self.root / 'logs/make'
        log.mkdir(parents=True)
        self.row = dict(id='make', status='completed', exit_code=0,
                        error_domain=None, error_code=None,
                        argv=['/usr/bin/arch', '-arm64', '/usr/bin/make', '-j2'], logs={})
        for stream, raw in [('stdout', b'compiled\n'), ('stderr', b'')]:
            path = log / (stream + '.bin')
            path.write_bytes(raw)
            self.row['logs'][stream] = dict(path=str(path.relative_to(self.root)),
                                           sha256=H(raw), size_bytes=len(raw))
        (log / 'command.json').write_text(json.dumps(self.row))

    def test_current_success_is_read_from_actual_logs(self):
        command_gate(self.root, [self.row], ['make'])
        (self.root / 'logs/make/stdout.bin').write_bytes(b'changed')
        with self.assertRaisesRegex(Error, 'reconstruction_log_changed'):
            command_gate(self.root, [self.row], ['make'])

    def test_partial_failed_or_cleanup_failure_cannot_be_promoted(self):
        for changes in [dict(status='running'), dict(exit_code=None), dict(exit_code=True),
                        dict(exit_code=1), dict(cleanup_error={'domain': 'errno', 'code': 1})]:
            with self.subTest(changes=changes), self.assertRaisesRegex(Error, 'reconstruction_command_failed'):
                command_gate(self.root, [dict(self.row, **changes)], ['make'])

    def test_missing_duplicate_or_non_native_commands_are_rejected(self):
        for rows in [[], [self.row, self.row]]:
            with self.assertRaisesRegex(Error, 'reconstruction_command_set'):
                command_gate(self.root, rows, ['make'])
        row = copy.deepcopy(self.row)
        row['argv'][1] = '-x86_64'
        with self.assertRaisesRegex(Error, 'reconstruction_native_command'):
            command_gate(self.root, [row], ['make'])

    def test_manifest_cannot_override_saved_command(self):
        row = copy.deepcopy(self.row)
        row['argv'][-1] = '-n'
        with self.assertRaisesRegex(Error, 'reconstruction_command_record_changed'):
            command_gate(self.root, [row], ['make'])


if __name__ == '__main__':
    unittest.main()
