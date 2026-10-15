# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import time,unittest
from tools.development.game.adapter import Adapter,owner_deadline
from tools.development.game.handoff import Segment
from tools.development.game.witness import atomic
from pear_runtime.fixtures.inputs import fact
class AdapterBoundaries(unittest.TestCase):
    def bare(self):
        a=object.__new__(Adapter);a.ended=False;a.reason=None;a.state=None;a.experiments_stopped=False;a.publish_live=lambda **kwargs:None;a.deadline_ns=time.monotonic_ns()+1_000_000_000
        return a
    def test_terminal_wins_before_companion_or_positive_request(self):
        a=self.bare();a.tick(b'',terminal=True)
        self.assertTrue(a.done);self.assertEqual(a.reason,'terminal')
    def test_real_deadline_ends_even_without_a_request(self):
        a=self.bare();a.deadline_ns=1;a.tick(b'')
        self.assertTrue(a.done);self.assertFalse(a.continue_supervision)
    def test_stop_cancels_pending_actions_before_ack(self):
        a=self.bare();calls=[];a.experiments_stopped=False;a.pending_key={'key':'w'};a.capture={'pending':True}
        def release():calls.append('key-up');a.pending_key=None
        def finish(cancel):self.assertTrue(cancel);calls.append('capture-join');a.capture=None
        def cancel():calls.append('sampler-join');a.sampler.active=None
        a.release_key=release;a.capture_finish=finish;a.sampler=SimpleNamespace(active=object(),cancel=cancel)
        self.assertTrue(a.stop_actions());self.assertEqual(calls,['key-up','capture-join','sampler-join']);self.assertTrue(a.experiments_stopped)
    def test_uncancelled_action_cannot_ack(self):
        a=self.bare();a.pending_key=None;a.capture=None;a.release_key=lambda:None;a.capture_finish=lambda cancel:None;a.sampler=SimpleNamespace(active=object(),cancel=lambda:None)
        self.assertFalse(a.stop_actions())
    def test_evidence_requires_same_segment_window_bytes_and_input_order(self):
        with TemporaryDirectory() as tmp:
            a=self.bare();a.root=Path(tmp).resolve();a.window=17;a.frames=[];now=time.monotonic_ns()
            base=dict(run=str(a.root),candidate='d25-game',role='renderer',pid=10,birth=[20,30],executable='/fixture',watch_id='watch',segment_id='segment')
            a.renderer=Segment(base,now-1_000_000_000);a.owner=Segment({**base,'role':'owner','pid':11,'watch_id':'owner'},now-1_000_000_000)
            refs=[]
            for index,delta in enumerate((600_000_000,100_000_000)):
                image=a.root/(str(index)+'.png');image.write_bytes(b'fixture-'+str(index).encode())
                row=dict(image=fact(image),renderer=a.renderer.binding,owner=a.owner.binding,window_id=17,started_ns=now-delta,ended_ns=now-delta+1)
                path=a.root/(str(index)+'.json');atomic(path,row);refs.append(fact(path))
            a.frames=refs;posted=dict(request={'renderer':a.renderer.binding},posted_ns=now-300_000_000);a.input_records=[posted];path=a.root/'input-1.json';atomic(path,posted)
            req=dict(observed_by='assistant_visual_inspection',evidence=refs,input_evidence=fact(path),at_ns=now,response_observed='in-game movement or action changed visibly')
            self.assertTrue(a.verify(req))
            image.write_bytes(b'changed')
            with self.assertRaises(Exception):a.verify(req)
    def test_optional_hud_overflow_does_not_poison_witness(self):
        with TemporaryDirectory() as tmp:
            a=self.bare();a.root=Path(tmp);a.hud=SimpleNamespace(exited=False);a.hud_result=None;a.hud_gap=None
            a.helpers=SimpleNamespace(failure=None)
            closed=SimpleNamespace(close=lambda:None)
            a.hud_helpers=SimpleNamespace(failure='output_limit',children={'hud-log':a.hud},streams={('hud-log','stdout'):{'total_bytes':262145}},pump=lambda wait:None,cleanup=lambda *args,**kwargs:{'complete':True},finish_logs=lambda ms:[{'observed_bytes':262145}],selector=closed,observer=closed)
            a.hud_tick()
            self.assertEqual(a.hud_gap['reason'],'output_limit');self.assertIsNone(a.helpers.failure)
            self.assertEqual(a.hud_result['failure'],'output_limit');self.assertTrue(a.hud_result['cleanup']['complete'])
    def test_pending_key_excludes_optional_capture_work(self):
        a=self.bare();a.experiments_stopped=False;a.pending_key={'release_at':time.monotonic()+10}
        a.capture_start()  # No windows/child helpers exist: it must return first.
        calls=[];a.helpers=SimpleNamespace(pump=lambda wait:calls.append('pump'),failure=None);a.witness=SimpleNamespace(exited=False)
        a.tick(b'')
        self.assertEqual(calls,['pump']);self.assertIsNotNone(a.pending_key)
    def test_hud_cleanup_error_still_cleans_required_witness(self):
        with TemporaryDirectory() as tmp:
            a=self.bare();a.root=Path(tmp);a.pending_key=None;a.loader=None;a.cleanup=None
            def bad_hud():raise RuntimeError('injected optional cleanup failure')
            a.close_hud=bad_hud;a.snapshot=lambda:{};calls=[]
            closed=SimpleNamespace(close=lambda:calls.append('closed'))
            a.helpers=SimpleNamespace(children={'witness':None},cleanup=lambda *args,**kwargs:(calls.append('witness cleanup') or {'complete':True}),finish_logs=lambda ms:[],failure=None,selector=closed,observer=closed)
            with self.assertRaises(Exception):a.close()
            self.assertTrue((a.root/'witness-stop').exists());self.assertIn('witness cleanup',calls)
    def test_effective_deadline_is_capped_by_actual_grant(self):
        self.assertEqual(owner_deadline({'hold_seconds':900},{'not_after_monotonic_ns':500,'maximum_play_seconds':900},100),500)
        self.assertEqual(owner_deadline({'hold_seconds':900},{'not_after_monotonic_ns':10**15,'maximum_play_seconds':900},100),900_000_000_100)
        for grant in ({'not_after_monotonic_ns':100,'maximum_play_seconds':900},{'not_after_monotonic_ns':500,'maximum_play_seconds':1800},{'not_after_monotonic_ns':True,'maximum_play_seconds':900}):
            with self.assertRaises(Exception):owner_deadline({'hold_seconds':900},grant,100)
if __name__=='__main__':unittest.main()

class TerminalAdapter(AdapterBoundaries):
    def test_capture_exit_propagates_to_terminal_before_control_or_sampler(self):
        from tools.development.game.watch import ConfirmedExit
        from pear_runtime.fixtures.direct import pump_observations
        a=self.bare();a.capture={'child':SimpleNamespace(exited=True,role='capture'),'deadline':0}
        a.helpers=SimpleNamespace(cleanup=lambda *args,**kwargs:{'complete':True})
        binding={'role':'renderer','pid':10};a.renderer=SimpleNamespace(binding=binding)
        def exit_probe():raise ConfirmedExit({'binding':binding,'invalid':{'reason':'exit'}})
        a.renderer_fresh=exit_probe;a.capture_gaps=[];a.pending_key=None
        def tick(raw,terminal):
            a.capture_finish()
            raise AssertionError('control ran after capture consumed EXIT')
        a._tick=tick
        sampler=SimpleNamespace(tick=lambda *args:self.fail('sample after EXIT'))
        pump_observations(a,a,sampler,None,None,b'',set(),False)
        self.assertTrue(a.ended);self.assertTrue(a.experiments_stopped);self.assertIsNone(a.capture)
        self.assertEqual(a.capture_gaps,[]);self.assertEqual(a.reason,'renderer_exit')
    def test_terminal_live_publication_bypasses_throttle(self):
        import json
        with TemporaryDirectory() as tmp:
            a=self.bare();a.publish_live=Adapter.publish_live.__get__(a)
            a.output=Path(tmp);a.last_live=time.monotonic();a.candidate=SimpleNamespace(name='fixture');a.operation='fixture'
            a.loader=None;a.renderer=None;a.owner=None;a.window=None;a.frames=[];a.capture_gaps=[];a.hud_gap=None
            a.end('renderer_exit');v=json.loads((a.output/'live.json').read_text())
            self.assertEqual(v['state'],'ended');self.assertIsNone(v['ack']);self.assertFalse(v['released']);self.assertTrue(v['automatic_input_stopped'])
    def test_unknown_observer_failure_is_preserved(self):
        a=self.bare()
        def tick(*args):raise RuntimeError('original observer failure')
        a._tick=tick
        with self.assertRaisesRegex(RuntimeError,'original observer failure'):a.tick(b'')
        self.assertTrue(a.ended);self.assertEqual(a.observation_error['code'],'original observer failure')
