# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
import select
from types import SimpleNamespace as NS
from unittest import TestCase
from tools.development.game.watch import QueueTap, ConfirmedExit
from pear_runtime.errors import Error

class Queue:
    def __init__(self):self.events=[];self.fail=False
    def control(self,changes,count,timeout):
        if self.fail:raise OSError('fixture queue failure')
        events=self.events[:count];self.events=self.events[count:];return events
    def close(self):pass
    def fileno(self):return 123

class Watch(TestCase):
    def setUp(self):
        self.q=Queue();self.n=0
        def token():self.n+=1;return str(self.n)
        self.tap=QueueTap(self.q,clock=lambda:100,token=token)
        self.child=NS(pid=10,identity=dict(pid=10,ppid=5,start_sec=1,start_usec=2),allowed_paths={'/owned/renderer'},exited=False,reaped=False)
        self.observer=NS(queue=self.tap,identity=lambda pid:dict(self.child.identity),executable=lambda pid:'/owned/renderer',refresh=lambda:self.tap.control(None,8,0))
    def register(self,flags=None):
        self.tap.control([NS(filter=select.KQ_FILTER_PROC,ident=10,flags=select.KQ_EV_ADD,fflags=flags if flags is not None else select.KQ_NOTE_EXEC|select.KQ_NOTE_EXIT)],0,0)
    def arm(self):return self.tap.arm(self.observer,self.child,'run','candidate')
    def event(self,flags):return NS(filter=select.KQ_FILTER_PROC,ident=10,flags=0,fflags=flags)
    def test_ready_and_fresh_pair(self):
        self.register();segment=self.arm();self.assertIsNone(self.tap.fresh(self.observer,self.child)['invalid']);self.assertIsNone(segment.snapshot()['global_exec_ordinal'])
    def test_same_image_exec_consumed_by_other_refresh_is_sticky(self):
        self.register();segment=self.arm();self.q.events=[self.event(select.KQ_NOTE_EXEC)]
        self.observer.refresh();self.assertIsNotNone(segment.invalid)
        with self.assertRaises(Exception):self.tap.fresh(self.observer,self.child)
    def test_coalesced_exec_exit_is_not_a_counter(self):
        self.register();segment=self.arm();self.q.events=[self.event(select.KQ_NOTE_EXEC|select.KQ_NOTE_EXIT)]
        self.observer.refresh();self.assertEqual(segment.invalid['reason'],'exit');self.assertIsNone(segment.snapshot()['global_exec_ordinal'])
    def test_late_incomplete_or_failed_watch_cannot_arm(self):
        with self.assertRaises(Exception):self.arm()
        self.setUp();self.register(select.KQ_NOTE_EXIT)
        with self.assertRaises(Exception):self.arm()
        self.setUp();self.q.fail=True
        with self.assertRaises(OSError):self.register()
        self.assertIsNotNone(self.tap.problem)
    def test_close_backlog_or_queue_replacement_invalidates(self):
        for mode in ('close','backlog','replace'):
            self.setUp();self.register();segment=self.arm()
            if mode=='close':self.tap.close()
            elif mode=='backlog':self.q.events=[self.event(0)]*8;self.observer.refresh()
            else:self.observer.queue=self.q
            with self.assertRaises(Exception):self.tap.fresh(self.observer,self.child)
            self.assertIsNotNone(segment.invalid)
    def test_exec_during_arming_cannot_establish_segment(self):
        self.register();calls=[]
        def refresh():
            calls.append(1)
            if len(calls)==2:self.q.events=[self.event(select.KQ_NOTE_EXEC)]
            self.tap.control(None,8,0)
        self.observer.refresh=refresh
        with self.assertRaises(Exception):self.arm()
        self.assertIsNone(self.tap.segment)

class TerminalWatch(Watch):
    def ready(self):
        self.register();self.arm();self.observer.handles={10:self.child}
        def refresh():
            for e in self.tap.control(None,8,0):
                self.child.exited |= bool(e.fflags & select.KQ_NOTE_EXIT)
        self.observer.refresh=refresh
    def test_exit_drain_never_queries_dead_identity(self):
        self.ready();self.q.events=[self.event(select.KQ_NOTE_EXIT)]
        def forbidden(pid):raise AssertionError('identity queried after confirmed exit')
        self.observer.identity=forbidden
        with self.assertRaises(ConfirmedExit):self.tap.fresh(self.observer,self.child)
    def test_identity_race_requires_confirmed_same_child_exit(self):
        for confirm in (False,True):
            self.setUp();self.ready()
            def unavailable(pid):
                if confirm:self.q.events=[self.event(select.KQ_NOTE_EXIT)]
                raise Error('owned_identity_unavailable')
            self.observer.identity=unavailable
            with self.assertRaises(ConfirmedExit if confirm else Error) as caught:self.tap.fresh(self.observer,self.child)
            if confirm:self.assertEqual(caught.exception.secondary['code'],'owned_identity_unavailable')
    def test_exit_does_not_cover_unrelated_programming_error(self):
        self.ready()
        def failed(pid):self.q.events=[self.event(select.KQ_NOTE_EXIT)];raise ValueError('bug')
        self.observer.identity=failed
        with self.assertRaises(ValueError):self.tap.fresh(self.observer,self.child)
    def test_witness_shaped_observer_needs_no_renderer_handles(self):
        self.register();self.arm()
        self.assertIsNone(self.tap.fresh(self.observer,self.child)['invalid'])
        self.q.events=[self.event(select.KQ_NOTE_EXIT)]
        with self.assertRaises(Exception) as caught:self.tap.fresh(self.observer,self.child)
        self.assertNotIsInstance(caught.exception,ConfirmedExit)
    def test_replaced_handle_cannot_claim_terminal(self):
        self.ready();self.observer.handles[10]=object();self.q.events=[self.event(select.KQ_NOTE_EXIT)]
        with self.assertRaises(Exception) as caught:self.tap.fresh(self.observer,self.child)
        self.assertNotIsInstance(caught.exception,ConfirmedExit)
