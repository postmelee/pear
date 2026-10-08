"""Actual abrupt manager death leaves refusal; no persisted-PID signaling."""
import json
import signal
import subprocess
import time
import unittest
from case_adapter import Cases,BUILD,experiment_cases
from synthetic_peer import Peer
class CrashTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=Cases(only=['timeout'])
    @classmethod
    def tearDownClass(cls):cls.cases.close()
    def crash(self,death):
        state,work=self.cases.state();self.assertEqual(self.cases.activate('timeout',state).returncode,0);peer=Peer()
        sentinel=subprocess.Popen([str(BUILD/'bin/fixture-child'),'sentinel'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            p=self.cases.spawn('timeout',state,peer,timeout=5000);trace=work/'state/prefix/child.json';end=time.monotonic()+4
            while not trace.exists() and time.monotonic()<end:time.sleep(.01)
            self.assertTrue(trace.exists());self.assertIsNone(p.poll());journal=work/'.pear-journal.json';before=json.loads(journal.read_bytes());self.assertEqual(before['state'],'running')
            p.send_signal(death);p.communicate(timeout=4);self.assertEqual(p.returncode,-death);peer.close()
            self.assertNotEqual(json.loads(journal.read_bytes())['state'],'clean')
            # The orphan is an independently bounded 5-second fixture. Never signal
            # its persisted PID or group after the supervisor lost its reservation.
            end=time.monotonic()+7
            while time.monotonic()<end:
                if experiment_cases.disappeared(BUILD,trace):break
                time.sleep(.05)
            self.assertTrue(experiment_cases.disappeared(BUILD,trace))
            stored=json.loads(journal.read_bytes());stored.update(owner_pid=sentinel.pid,owner_started_sec=1,owner_started_usec=0);journal.write_text(json.dumps(stored))
            fresh=Peer()
            try:
                retry=self.cases.spawn('timeout',state,fresh);out,err,failure=experiment_cases.capture_bounded(retry,5);result=json.loads(out);self.assertIsNone(failure);self.assertEqual(result['classification'],'context_incomplete');self.assertFalse(result['spawned']);self.assertIsNone(sentinel.poll());self.assertEqual(json.loads(journal.read_bytes()),stored)
            finally:fresh.close()
            self.cases.results.append({'id':'sigkill' if death==signal.SIGKILL else 'abort','actual_manager_signal':death,'journal_dirty':True,'free_lease_retry_refused':True,'substituted_unrelated_owner_survived':True,'finite_orphan_disappeared':True})
        finally:
            if peer.thread.is_alive():peer.close()
            if sentinel.poll() is None:sentinel.kill()
            sentinel.wait(timeout=3)
    def test_sigkill_refuses_even_after_lease_release_and_finite_child_exit(self):self.crash(signal.SIGKILL)
    def test_abort_refuses_without_trusting_stored_pid(self):self.crash(signal.SIGABRT)
