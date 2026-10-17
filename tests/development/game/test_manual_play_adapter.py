# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import time,unittest
from pear_runtime.fixtures.inputs import fact
from tools.development.game.witness import atomic
from tools.development.game.manual import ManualAdapter
class ManualTests(unittest.TestCase):
    def test_click_and_key_never_reach_event_api(self):
        a=object.__new__(ManualAdapter)
        for action in ('click','key'):
            with self.assertRaises(Exception):a.input({'action':action})
    def fixture(self,root):
        a=object.__new__(ManualAdapter);a.root=root;a.window=7;a.operation='op';a.frames=[];a.input_count=0;a.input_records=[];a.pending_key=None
        now=time.monotonic_ns();a.renderer=SimpleNamespace(binding={'pid':12,'birth':[10,20]},ready_ns=now-10**9);a.owner=SimpleNamespace(binding={'pid':13,'birth':[10,30]})
        for i,delta in enumerate((600_000_000,100_000_000)):
            image=root/f'{i}.png';image.write_bytes(bytes([i]));p=root/f'{i}.json'
            atomic(p,dict(image=fact(image),renderer=a.renderer.binding,owner=a.owner.binding,window_id=7,started_ns=now-delta,ended_ns=now-delta+1));a.frames.append(fact(p))
        human=dict(source='direct_user_message',message='I entered gameplay and movement responded.',renderer=a.renderer.binding,owner=a.owner.binding,window_id=7,operation_id='op',actual_play=True,input_responsive=True,recorded_ns=now-50_000_000)
        p=root/'human-observation.json';atomic(p,human)
        req=dict(observed_by='assistant_visual_inspection',input_source='human',evidence=a.frames,at_ns=now,response_observed='in-game movement or action changed visibly',human_observation=fact(p))
        return a,req,human
    def test_manual_evidence_without_automated_receipt(self):
        with TemporaryDirectory() as d:
            a,r,_=self.fixture(Path(d).resolve());self.assertTrue(a.verify(r))
    def test_other_run_stale_negative_and_malformed_human_evidence_rejected(self):
        for change in ({'window_id':8},{'operation_id':'other'},{'actual_play':False},{'input_responsive':False},{'source':'inferred'},{'recorded_ns':1},{'message':''}):
            with TemporaryDirectory() as d:
                a,r,h=self.fixture(Path(d).resolve());h.update(change);p=a.root/'human-observation.json';atomic(p,h);r['human_observation']=fact(p)
                with self.subTest(change=change),self.assertRaises(Exception):a.verify(r)
    def test_changed_frame_reversed_pair_and_posted_input_rejected(self):
        with TemporaryDirectory() as d:
            a,r,_=self.fixture(Path(d).resolve());a.input_count=1
            with self.assertRaises(Exception):a.verify(r)
            a.input_count=0;r['evidence']=list(reversed(a.frames))
            with self.assertRaises(Exception):a.verify(r)
            r['evidence']=a.frames;(a.root/'0.png').write_bytes(b'changed')
            with self.assertRaises(Exception):a.verify(r)
if __name__=='__main__':unittest.main()
