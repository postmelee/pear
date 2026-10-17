# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import json,time,unittest
from pear_runtime.errors import Error
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
    def test_unchanged_manual_control_remains_held_then_matching_finish_ends(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();a,request=self.setup_case(root,'valid')
            control=root/'control.json';original=control.read_bytes()
            with patch('tools.development.game.adapter.time.monotonic_ns',lambda:a.clock_ns),patch('tools.development.game.adapter.time.monotonic',lambda:a.clock_ns/1_000_000_000),patch('tools.development.game.manual.monotonic_ns',lambda:a.clock_ns):
                a.tick(b'')
                self.assertEqual(a.state.state,'user_test_held');ack=deepcopy(a.state.ack)
                for _ in range(2):
                    a.clock_ns+=250_000_000;a.tick(b'')
                    self.assertEqual(a.state.state,'user_test_held');self.assertEqual(a.state.ack,ack)
                self.assertEqual(control.read_bytes(),original)
                self.assertEqual(a.state.accepted_request,request)
                self.assertEqual(json.loads((root/'handoff-request.json').read_text()),request)
                self.assertNotIn('evidence_deadline_ns',request)
                atomic(control,dict(action='finish-user-test',request_id=request['request_id'],operation_id=request['operation_id']))
                a.clock_ns+=250_000_000;a.tick(b'')
            self.assertEqual(a.state.state,'ended');self.assertEqual(a.state.reason,'user_finished');self.assertIsNone(a.state.ack)
            self.assertEqual(a.calls.count('capture-joined'),1);self.assertEqual(a.calls.count('sampler-joined'),1)
            self.assertEqual(a.calls.count('probe'),4);self.assertEqual(a.input_count,0);self.assertNotIn('EVENT',a.calls)

    def test_changed_manual_confirmation_and_foreign_finish_still_refuse(self):
        for change in ('confirmation','finish-request','finish-operation'):
            with self.subTest(change=change),TemporaryDirectory() as tmp:
                root=Path(tmp).resolve();a,request=self.setup_case(root,'valid')
                with patch('tools.development.game.adapter.time.monotonic_ns',lambda:a.clock_ns),patch('tools.development.game.adapter.time.monotonic',lambda:a.clock_ns/1_000_000_000),patch('tools.development.game.manual.monotonic_ns',lambda:a.clock_ns):
                    a.tick(b'');self.assertEqual(a.state.state,'user_test_held')
                    if change=='confirmation':
                        changed=deepcopy(request);changed['requested_deadline_ns']+=1
                    else:
                        changed=dict(action='finish-user-test',request_id=request['request_id'],operation_id=request['operation_id'])
                        changed['request_id' if change=='finish-request' else 'operation_id']='foreign'
                    atomic(root/'control.json',changed);a.clock_ns+=250_000_000
                    with self.assertRaisesRegex(Error,'play_finish_identity'):a.tick(b'')
                self.assertEqual(a.state.state,'ended');self.assertEqual(a.reason,'observation_error');self.assertIsNone(a.state.ack)
                self.assertEqual(a.calls.count('sampler-joined'),1);self.assertEqual(a.input_count,0);self.assertNotIn('EVENT',a.calls)

    def test_derived_manual_expiry_still_rejects_verification_stop_and_probe_delay(self):
        for phase in ('verification','stop','probe'):
            with self.subTest(phase=phase),TemporaryDirectory() as tmp:
                root=Path(tmp).resolve();a,request=self.setup_case(root,'valid')
                # A caller-supplied later deadline cannot replace recomputed evidence age.
                request['evidence_deadline_ns']=a.deadline_ns;atomic(root/'control.json',request)
                original=(root/'control.json').read_bytes();derived={}
                verify=a.verify;stop=a.stop_actions;probe=a.probe
                def delayed_verify(value):
                    result=verify(value);derived['expiry']=value['evidence_deadline_ns']
                    if phase=='verification':a.clock_ns=derived['expiry']
                    return result
                def delayed_stop():
                    result=stop()
                    if phase=='stop':a.clock_ns=derived['expiry']
                    return result
                def delayed_probe(*args):
                    result=probe(*args)
                    if phase=='probe':a.clock_ns=derived['expiry']
                    return result
                a.verify=delayed_verify;a.stop_actions=delayed_stop;a.probe=delayed_probe
                code='play_manual_expired_after_verify' if phase=='verification' else 'play_manual_expired_after_probe'
                with patch('tools.development.game.adapter.time.monotonic_ns',lambda:a.clock_ns),patch('tools.development.game.adapter.time.monotonic',lambda:a.clock_ns/1_000_000_000),patch('tools.development.game.manual.monotonic_ns',lambda:a.clock_ns):
                    with self.assertRaisesRegex(Error,code):a.tick(b'')
                self.assertLess(derived['expiry'],request['evidence_deadline_ns'])
                self.assertEqual((root/'control.json').read_bytes(),original)
                self.assertEqual(a.state.state,'ended');self.assertIsNone(a.state.ack);self.assertFalse((root/'handoff-ack.json').exists())
                self.assertEqual(a.input_count,0);self.assertNotIn('EVENT',a.calls)
if __name__=='__main__':unittest.main()
