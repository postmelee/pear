# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import time,unittest
from pear_runtime.fixtures.inputs import fact
from tools.development.game.witness import atomic
from tools.development.game.handoff import Segment,PlayHandoff
from tools.development.game.manual import ManualAdapter
class ManualJoint(unittest.TestCase):
    def setup_case(self,root,mode):
        a=object.__new__(ManualAdapter);now=time.monotonic_ns();a.clock_ns=now
        def binding(role,pid):return dict(run=str(root),candidate='d25-game',role=role,pid=pid,birth=[10,pid],executable='/fixture/'+role,watch_id=role,segment_id=role)
        a.root=root;a.operation='operation';a.window=7;a.renderer=Segment(binding('renderer',12),now-200_000_000_000);a.owner=Segment(binding('owner',13),now-200_000_000_000)
        a.frames=[];a.input_records=[];a.input_count=0;a.pending_key=None;a.capture=None;a.experiments_stopped=False;a.ended=False;a.reason=None
        a.deadline_ns=now+900_000_000_000;a.last_tick=0;a.last_capture=time.monotonic();a.last_hold_probe=0;a.last_control=None;a.log_offset=0;a.calls=[]
        a.loader=SimpleNamespace(pid=12);a.helpers=SimpleNamespace(pump=lambda _:None,failure=None);a.witness=SimpleNamespace(exited=False)
        def forbidden(*args):a.calls.append('EVENT');raise AssertionError('manual mode posted an event')
        a.windows=SimpleNamespace(rows=lambda _:[{'kCGWindowNumber':7}],exact=lambda *_:{'kCGWindowNumber':7},key=forbidden,click=forbidden)
        a.hud_tick=lambda:None;a.renderer_fresh=lambda:None;a.publish_live=lambda **_:None;a.capture_start=lambda:None
        def finish(cancel=False):
            if cancel:a.calls.append('capture-joined')
            a.capture=None
        a.capture_finish=finish;a.sampler=SimpleNamespace(active=None)
        def cancel():
            a.calls.append('sampler-joined')
            a.sampler.active=object() if mode=='pending' else None
        a.sampler.cancel=cancel
        a.fatal=lambda:mode=='terminal'
        ages=(90_000_000_000,50_000_000_000) if mode=='double-age' else (59_500_000_000,100_000_000) if mode=='probe-delay' else (600_000_000,100_000_000)
        for i,age in enumerate(ages):
            image=root/f'{i}.png';image.write_bytes(bytes([i]));p=root/f'{i}.json'
            atomic(p,dict(image=fact(image),renderer=a.renderer.binding,owner=a.owner.binding,window_id=7,started_ns=now-age,ended_ns=now-age+1));a.frames.append(fact(p))
        at=now-45_000_000_000 if mode=='double-age' else now
        h=dict(source='direct_user_message',message='Gameplay movement responded to my keyboard.',renderer=a.renderer.binding,owner=a.owner.binding,window_id=7,operation_id='operation',actual_play=True,input_responsive=True,recorded_ns=at-1_000_000_000 if mode=='double-age' else at-50_000_000)
        p=root/'human-observation.json';atomic(p,h)
        request=dict(schema=1,action='actual-play-and-input-confirmed',request_id='a'*32,operation_id='operation',renderer=a.renderer.binding,owner=a.owner.binding,window_id=7,at_ns=at,visual_status='actual-play',input_status='responsive',requested_deadline_ns=a.deadline_ns,observed_by='assistant_visual_inspection',input_source='human',evidence=a.frames,response_observed='in-game movement or action changed visibly',human_observation=fact(p))
        atomic(root/'control.json',request)
        a.state=PlayHandoff(a.renderer,a.owner,7,'operation',a.deadline_ns,max_age_ns=60_000_000_000,clock=lambda:a.clock_ns)
        def probe(rid,after):
            a.calls.append('probe')
            self.assertTrue(a.experiments_stopped);self.assertIsNone(a.capture);self.assertIsNone(a.sampler.active)
            if mode=='probe-delay':a.clock_ns+=1_000_000_000
            return dict(request_id=rid,operation_id='operation',slot_released=False,at_ns=a.clock_ns,window_id=7,renderer_live=True,owner_live=True,owner_witness_live=mode!='witness-stale',watches_drained=True,terminal=False,renderer=a.renderer.binding,owner=a.owner.binding,automatic_work_pending=False,automatic_input_stopped=True,owner_deadline_ns=a.deadline_ns)
        a.probe=probe;return a,request
    def test_tick_manual_handoff_preserves_human_source_and_zero_events(self):
        with TemporaryDirectory() as tmp:
            a,request=self.setup_case(Path(tmp).resolve(),'valid')
            with patch('tools.development.game.adapter.time.monotonic_ns',lambda:a.clock_ns),patch('tools.development.game.manual.monotonic_ns',lambda:a.clock_ns):a.tick(b'')
            self.assertEqual(a.state.state,'user_test_held');self.assertIsNotNone(a.state.ack)
            self.assertEqual(a.calls,['capture-joined','sampler-joined','probe'])
            self.assertEqual(a.state.accepted_request['human_observation'],request['human_observation'])
            self.assertEqual(a.state.accepted_request['input_source'],'human');self.assertNotIn('input_evidence',a.state.accepted_request)
            self.assertEqual(a.input_count,0)
    def test_tick_rejects_double_age_delay_pending_and_stale_witness(self):
        for mode in ('double-age','probe-delay','pending','witness-stale'):
            with self.subTest(mode=mode),TemporaryDirectory() as tmp:
                a,_=self.setup_case(Path(tmp).resolve(),mode)
                with patch('tools.development.game.adapter.time.monotonic_ns',lambda:a.clock_ns),patch('tools.development.game.manual.monotonic_ns',lambda:a.clock_ns):
                    with self.assertRaises(Exception):a.tick(b'')
                self.assertIsNone(a.state.ack);self.assertFalse((a.root/'handoff-ack.json').exists());self.assertNotIn('EVENT',a.calls)
    def test_same_pump_terminal_wins_before_human_request(self):
        with TemporaryDirectory() as tmp:
            a,_=self.setup_case(Path(tmp).resolve(),'terminal')
            with patch('tools.development.game.adapter.time.monotonic_ns',lambda:a.clock_ns),patch('tools.development.game.manual.monotonic_ns',lambda:a.clock_ns):a.tick(b'')
            self.assertIsNone(a.state.ack);self.assertEqual(a.calls,[])
if __name__=='__main__':unittest.main()
