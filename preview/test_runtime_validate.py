# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
import runtime_validate as rv


class ProbeBounds(unittest.TestCase):
    def test_flood_is_stopped_without_touching_sentinel(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);sentinel=root/'save';sentinel.write_text('keep')
            with self.assertRaisesRegex(RuntimeError,'log limit'):
                rv.run([sys.executable,'-c','import os\nwhile True: os.write(1,b"x"*65536)'],os.environ.copy(),root/'log',max_log_bytes=8192)
            self.assertEqual(sentinel.read_text(),'keep')
            self.assertLessEqual((root/'log').stat().st_size,8192)

    def test_timeout_reaps_owned_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError,'timed out'):
                rv.run([sys.executable,'-c','import time;time.sleep(30)'],os.environ.copy(),Path(tmp)/'log',timeout=.05)

    def test_marker_observes_exact_owned_child_once(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            seen=[]
            def observe(pid):
                self.assertNotEqual(pid, os.getpid())
                os.kill(pid, 0)
                seen.append(pid)
            result=rv.run([sys.executable,'-c',
                'import time;print("PEAR_RUNTIME_OBSERVE_READY",flush=True);'
                'print("PEAR_RUNTIME_OBSERVE_READY",flush=True);time.sleep(.1)'],
                os.environ.copy(),Path(tmp)/'log',observer=observe)
            self.assertEqual(len(seen),1)
            self.assertIn('PEAR_RUNTIME_OBSERVE_READY',result)
            with self.assertRaises(ProcessLookupError):os.kill(seen[0],0)

    def test_empty_or_external_helper_evidence_is_refused(self):
        with tempfile.TemporaryDirectory(prefix='runtime with spaces ') as tmp:
            root=Path(tmp)
            names=[str(root/'lib'/name) for name in ('libgnutls.30.dylib','libfreetype.6.dylib')]
            trace='\n'.join('n'+name for name in names)
            result=rv.validate_wine_images(trace,root)
            self.assertEqual(len(result['packaged_helpers']),2)
            with self.assertRaisesRegex(RuntimeError,'Incomplete'):
                rv.validate_wine_images('',root)
            with self.assertRaisesRegex(RuntimeError,'External'):
                rv.validate_wine_images(trace+'\nn/opt/homebrew/lib/other.dylib',root)
            with self.assertRaisesRegex(RuntimeError,'External'):
                rv.validate_wine_images(trace+'\nn'+str(root)+'-other/lib.so',root)


class SyntheticCleanup(unittest.TestCase):
    def test_already_exited_requires_wait_and_empty_handles(self):
        root = Path('/isolated trial')
        with patch.object(rv, 'run', side_effect=[rv.CommandFailure(1, root/'stop'), '', 'p12\nn/isolated trial/output/synthetic-handles.log']) as run:
            self.assertEqual(rv.stop_synthetic_server(root/'runtime', root/'output', {}), 1)
            self.assertEqual(run.call_count, 3)
            self.assertEqual(run.call_args_list[1].args[0][-1], '-w')

    def test_live_handle_and_unavailable_inspection_are_not_cleanup(self):
        root = Path('/isolated trial')
        for observation in ['p12\nn/isolated trial/output/synthetic-prefix/file', RuntimeError('inspection unavailable')]:
            with patch.object(rv, 'run', side_effect=['', '', observation]):
                with self.assertRaises(RuntimeError):
                    rv.stop_synthetic_server(root/'runtime', root/'output', {})

    def test_other_stop_failure_is_preserved(self):
        root = Path('/isolated trial')
        with patch.object(rv, 'run', side_effect=rv.CommandFailure(2, root/'stop')) as run:
            with self.assertRaises(rv.CommandFailure):
                rv.stop_synthetic_server(root/'runtime', root/'output', {})
            self.assertEqual(run.call_count, 1)


if __name__=='__main__':unittest.main()
