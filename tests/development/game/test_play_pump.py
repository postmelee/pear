# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
import unittest
from types import SimpleNamespace
from pear_runtime.fixtures.direct import pump_observations
class PlayPump(unittest.TestCase):
    def test_key_posted_or_already_pending_skips_active_sampler(self):
        for newly_posted in (False,True):
            with self.subTest(newly_posted=newly_posted):
                calls=[]
                adapter=SimpleNamespace(ended=False,experiments_stopped=False,pending_key=None if newly_posted else {'key':'w'})
                def tick(data,terminal):calls.append('adapter');adapter.pending_key={'key':'w'}
                adapter.tick=tick
                def blocking_sample(*args):raise AssertionError('optional cleanup overlaps key hold')
                sampler=SimpleNamespace(active=object(),tick=blocking_sample)
                pump_observations(adapter,adapter,sampler,None,None,b'',set(),False)
                self.assertEqual(calls,['adapter'])
    def test_release_resumes_optional_sampler(self):
        calls=[];adapter=SimpleNamespace(ended=False,experiments_stopped=False,pending_key={'key':'w'})
        def tick(data,terminal):adapter.pending_key=None;calls.append('released')
        adapter.tick=tick;sampler=SimpleNamespace(tick=lambda *args:calls.append('sample'))
        pump_observations(adapter,adapter,sampler,None,None,b'',set(),False)
        self.assertEqual(calls,['released','sample'])
    def test_terminal_and_stopped_block_optional_work(self):
        for terminal,stopped in ((True,False),(False,True)):
            calls=[];adapter=SimpleNamespace(ended=False,experiments_stopped=stopped,pending_key=None,tick=lambda *args,**kwargs:calls.append('adapter'))
            sampler=SimpleNamespace(tick=lambda *args:calls.append('sample'))
            pump_observations(adapter,adapter,sampler,None,None,b'',set(),terminal)
            self.assertEqual(calls,['adapter'])
    def test_fixture_without_adapter_retains_sample_behavior(self):
        calls=[];sampler=SimpleNamespace(tick=lambda *args:calls.append('sample'))
        pump_observations(None,None,sampler,None,None,b'',set(),False)
        self.assertEqual(calls,['sample'])
if __name__=='__main__':unittest.main()
