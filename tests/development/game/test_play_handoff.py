# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
from copy import deepcopy
from unittest import TestCase
from tools.development.game.handoff import Segment,PlayHandoff

class PlayState(TestCase):
    def setUp(self):
        def binding(role,pid):return dict(run='run',candidate='candidate',role=role,pid=pid,birth=[1,pid],executable='/owned/'+role,watch_id=role+'watch',segment_id=role+'segment')
        self.r=Segment(binding('renderer',10),100);self.o=Segment(binding('owner',20),100)
        self.now=200;self.h=PlayHandoff(self.r,self.o,30,'operation',1000,max_age_ns=100,clock=lambda:self.now)
        self.request=dict(schema=1,action='actual-play-and-input-confirmed',request_id='a'*32,operation_id='operation',renderer=self.r.binding,owner=self.o.binding,window_id=30,at_ns=150,visual_status='actual-play',input_status='responsive',requested_deadline_ns=900)
        self.order=[]
    def probe(self,rid,now):
        self.order.append('probe')
        return dict(request_id=rid,operation_id='operation',slot_released=False,at_ns=self.now,window_id=30,renderer_live=True,owner_live=True,owner_witness_live=True,watches_drained=True,terminal=False,renderer=self.r.binding,owner=self.o.binding,automatic_work_pending=False,automatic_input_stopped=True,owner_deadline_ns=800)
    def stop(self):self.order.append('stop');return True
    def step(self,**changes):
        args=dict(now_ns=self.now,terminal=None,request=self.request,probe=self.probe,stop_actions=self.stop,verify_evidence=lambda r:True);args.update(changes)
        return self.h.step(**args)
    def test_positive_is_after_stop_and_bounded_by_real_owner(self):
        ack=self.step();self.assertEqual(self.order,['stop','probe']);self.assertEqual(ack['effective_deadline_ns'],800)
        self.assertEqual(self.h.state,'user_test_held')
    def test_fatal_same_pump_never_acknowledges(self):
        self.assertIsNone(self.step(terminal='owner_refused'));self.assertEqual(self.order,[]);self.assertEqual(self.h.state,'ended')
    def test_same_path_and_coalesced_exec_stick(self):
        for exits in (False,True):
            self.setUp();self.r.event(exec_seen=True,exit_seen=exits,at_ns=160)
            self.assertIsNone(self.step());self.assertIsNotNone(self.r.invalid)
            self.assertFalse(self.r.check(self.r.binding,200))
    def test_menu_or_sent_input_does_not_hold(self):
        for key,value in [('visual_status','menu'),('input_status','sent')]:
            self.setUp();self.request[key]=value
            with self.assertRaises(Exception):self.step()
            self.assertNotEqual(self.h.state,'user_test_held');self.assertEqual(self.order,[])
    def test_wrong_window_birth_or_preready_capture_refuses(self):
        for key in ('window','birth','clock'):
            self.setUp();self.request=deepcopy(self.request)
            if key=='window':self.request['window_id']=31
            elif key=='birth':self.request['renderer']['birth']=[1,99]
            else:self.request['at_ns']=99
            with self.assertRaises(Exception):self.step()
            self.assertNotEqual(self.h.state,'user_test_held')
    def test_cancel_failure_cannot_hold(self):
        with self.assertRaises(Exception):self.step(stop_actions=lambda:False)
        self.assertEqual(self.h.state,'ended');self.assertIsNone(self.h.ack)
    def test_fresh_probe_gap_owner_loss_or_pending_work_refuses(self):
        for key,value in [('owner_witness_live',False),('watches_drained',False),('owner_live',False),('automatic_work_pending',True),('slot_released',True),('at_ns',90),('terminal',True)]:
            self.setUp()
            def broken(rid,now):p=self.probe(rid,now);p[key]=value;return p
            with self.assertRaises(Exception):self.step(probe=broken)
            self.assertEqual(self.h.state,'ended')
    def test_post_ack_event_revokes_without_new_input(self):
        self.step();self.o.event(exec_seen=True,at_ns=210);self.now=220
        self.assertIsNone(self.step(request=None));self.assertIsNone(self.h.ack);self.assertEqual(self.order,['stop','probe'])
    def test_expiry_and_bound_finish(self):
        self.step();self.now=800;self.step(request=None);self.assertEqual(self.h.reason,'hold_expired')
        self.setUp();self.step();self.now=250
        with self.assertRaises(Exception):self.step(request={'action':'finish-user-test','request_id':'b'*32,'operation_id':'operation'})
        self.step(request={'action':'finish-user-test','request_id':'a'*32,'operation_id':'operation'});self.assertEqual(self.h.reason,'user_finished')
    def test_owner_deadline_cannot_extend_hold(self):
        self.step();self.now=300
        def later(rid,now):p=self.probe(rid,now);p['owner_deadline_ns']=950;return p
        self.step(request=None,probe=later);self.assertEqual(self.h.ack['effective_deadline_ns'],800)

    def test_callback_delay_and_pre_stop_probe_cannot_hold(self):
        for mode in ('verify','stop','probe','rollback'):
            self.setUp()
            def verify(request):
                if mode=='verify':self.now=700
                return True
            def stop():
                self.now=700 if mode=='stop' else 199 if mode=='rollback' else 210
                return True
            def probe(rid,now):
                p=self.probe(rid,now)
                if mode=='probe':p['at_ns']=200
                return p
            with self.assertRaises(Exception):self.step(verify_evidence=verify,stop_actions=stop,probe=probe)
            self.assertNotEqual(self.h.state,'user_test_held')
    def test_cross_run_candidate_and_bad_shapes_refuse(self):
        for key in ('run','candidate'):
            binding=deepcopy(self.o.binding);binding[key]='different'
            with self.assertRaises(Exception):PlayHandoff(self.r,Segment(binding,100),30,'operation',1000)
        for birth in (True,[0,1],[1,True],[1,1_000_000],{'sec':1}):
            binding=deepcopy(self.r.binding);binding['birth']=birth
            with self.assertRaises(Exception):Segment(binding,100)
        for value in (True,0,1.5,float('nan')):
            self.setUp();self.request['requested_deadline_ns']=value
            with self.assertRaises(Exception):self.step()
            self.setUp();self.request['schema']=value
            with self.assertRaises(Exception):self.step()
    def test_stop_failure_is_not_confirmed(self):
        with self.assertRaises(Exception):self.step(stop_actions=lambda:False)
        self.assertFalse(self.h.experiments_stopped)
    def test_duplicate_is_idempotent_changed_payload_refuses(self):
        original=self.step();self.now=220;self.step()
        self.assertEqual(self.h.ack,original);self.assertEqual(self.order.count('stop'),1)
        self.request['requested_deadline_ns']=999
        with self.assertRaises(Exception):self.step()
        self.assertEqual(self.order.count('stop'),1)
    def test_rejected_requests_have_one_attempt_budget(self):
        self.request['window_id']=999
        with self.assertRaises(Exception):self.step()
        self.request['window_id']=30;self.request['request_id']='b'*32
        with self.assertRaisesRegex(Exception,'play_request_replay'):self.step()
        self.assertTrue(self.h.attempted);self.assertIsNone(self.h.accepted_request)

    def test_clock_rollback_after_ack_or_later_tick_revokes(self):
        for advanced in (False,True):
            self.setUp();self.step()
            if advanced:self.now=300;self.step(request=None)
            self.now=250 if advanced else 150
            with self.assertRaisesRegex(Exception,'play_clock_rollback'):self.step(request=None)
            self.assertEqual(self.h.state,'ended');self.assertIsNone(self.h.ack)
