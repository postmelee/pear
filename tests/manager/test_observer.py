"""Real framed socket readiness, stalls and cleanup through the native manager."""
import json
import signal
import time
import unittest
from case_adapter import Cases,experiment_cases
from synthetic_peer import Peer
class ObserverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=Cases(only=['success','timeout'])
    @classmethod
    def tearDownClass(cls):cls.cases.close()
    def refused(self,mode,after=False):
        value=self.cases.execute('success',mode);r=value['result'];self.assertEqual(value['phase'],'supervision',value);self.assertFalse(r['observation_complete'],value);self.assertTrue(value['sentinel_survived']);self.assertTrue(value['identities_gone']);self.assertLess(value['elapsed_seconds'],4.5)
        if after:
            self.assertIn(r['classification'],('observer_gap','cleanup_failed'),value);self.assertTrue(r['reaped']);self.assertGreater(r['stdout_bytes'],0)
        else:self.assertEqual(r['classification'],'observer_not_ready',value);self.assertFalse(r['spawned']);self.assertEqual(value['trace_count'],0)
        self.assertNotEqual(json.loads((value['work']/'.pear-journal.json').read_bytes())['state'],'clean')
    def test_positive_request_capture_sequence_and_exit_basis(self):
        value=self.cases.execute('success');self.assertTrue(value['result']['observation_complete']);self.assertEqual(value['result']['classification'],'success')
    def cancellation(self,before):
        state,work=self.cases.state();self.assertEqual(self.cases.activate('timeout',state).returncode,0)
        peer=Peer('cancel_before' if before else 'after_ready_no_read')
        try:
            p=self.cases.spawn('timeout',state,peer,timeout=5000)
            self.assertTrue((peer.hello_seen if before else peer.ready_sent).wait(3));time.sleep(.1);p.send_signal(signal.SIGINT)
            out,err,failure=experiment_cases.capture_bounded(p,5);self.assertIsNone(failure);self.assertEqual(err,b'');result=json.loads(out);self.assertEqual(result['classification'],'cancelled',result);self.assertFalse(result['observation_complete'])
            self.assertEqual(result['spawned'],not before)
            if not before:self.assertTrue(result['reaped']);self.assertEqual(result['cleanup'],'passed')
            self.cases.results.append({'id':'cancel_before' if before else 'cancel_during_backpressure','result':result})
        finally:peer.close()
    def test_cancellation_before_spawn(self):self.cancellation(True)
    def test_cancellation_during_nonreading_peer(self):self.cancellation(False)
for mode in ['silent','no_read','partial_header','partial_body','partial_header_eof','partial_body_eof','drip','zero','oversize','malformed','disconnect','wrong_hash','stale_capture','wrong_run','wrong_sequence']:
    def test(self,mode=mode):self.refused(mode)
    setattr(ObserverTests,'test_readiness_'+mode,test)
for mode in ['after_ready_no_read','after_ready_partial','after_ready_disconnect','wrong_completion','gap']:
    def test(self,mode=mode):self.refused(mode,True)
    setattr(ObserverTests,'test_after_spawn_'+mode,test)
