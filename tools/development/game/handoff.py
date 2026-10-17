# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
"""Bounded P1 state only; adapters must supply actual watch/input/owner evidence.

No process launch, input, capture, or game qualification occurs in this module.
A segment is a watched interval, never a guessed global exec ordinal.
"""
from copy import deepcopy
from time import monotonic_ns
import re

def positive(value):return type(value) is int and 0<value<2**63

def token(value):return type(value) is str and re.fullmatch(r"[a-zA-Z0-9_-]{1,128}",value) is not None
from pear_runtime.fixtures.inputs import need

class Segment:
    def __init__(self, binding, ready_ns):
        required={'run','candidate','role','pid','birth','executable','watch_id','segment_id'}
        need(type(binding) is dict and set(binding)==required,'play_segment_fields')
        need(positive(binding['pid']) and positive(ready_ns),'play_segment_identity')
        birth=binding['birth']
        need(type(birth) is list and len(birth)==2 and positive(birth[0]) and type(birth[1]) is int and 0<=birth[1]<1_000_000,'play_segment_birth')
        need(binding['role'] in ('renderer','owner') and all(token(binding[k]) for k in ('candidate','watch_id','segment_id')),'play_segment_tokens')
        need(all(type(binding[k]) is str and 0<len(binding[k])<=4096 for k in ('run','executable')),'play_segment_paths')
        self.binding=deepcopy(binding);self.ready_ns=ready_ns;self.invalid=None
    def invalidate(self,reason,at_ns):
        if self.invalid is None:self.invalid={'reason':reason,'at_ns':at_ns}
    def event(self,*,exec_seen=False,exit_seen=False,error=None,at_ns):
        if exec_seen or exit_seen or error:self.invalidate(error or ('exit' if exit_seen else 'exec'),at_ns)
    def check(self,binding,at_ns):
        if binding!=self.binding or at_ns<self.ready_ns:self.invalidate('identity_or_clock',at_ns)
        return self.invalid is None
    def snapshot(self):
        return dict(binding=deepcopy(self.binding),ready_ns=self.ready_ns,global_exec_ordinal=None,invalid=deepcopy(self.invalid))

class PlayHandoff:
    """Terminal-first request/ack with real cancellation and fresh probe hooks.

    probe(request_id, now_ns) must drain the covered watches and return a fresh
    independently witnessed owner plus renderer/window/slot facts. stop_actions
    must cancel/join pending automatic work, not merely set a presentation flag.
    Evidence verification belongs to the adapter and is separately required.
    """
    def __init__(self,renderer,owner,window_id,operation_id,outer_deadline_ns,max_age_ns=2_000_000_000,clock=monotonic_ns):
        need(type(window_id) is int and window_id>0,'play_window')
        need(positive(outer_deadline_ns) and positive(max_age_ns),'play_deadline')
        need(renderer.binding['role']=='renderer' and owner.binding['role']=='owner' and all(renderer.binding[k]==owner.binding[k] for k in ('run','candidate')),'play_role_binding')
        need(token(operation_id),'play_operation')
        self.renderer=renderer;self.owner=owner;self.window_id=window_id;self.operation_id=operation_id
        self.outer_deadline_ns=outer_deadline_ns;self.max_age_ns=max_age_ns;self.clock=clock
        self.state='observing';self.last_observed_ns=max(renderer.ready_ns,owner.ready_ns);self.ack=None;self.attempted=False;self.accepted_request=None;self.reason=None;self.experiments_stopped=False
    def revoke(self,reason):
        self.state='ended';self.reason=reason;self.ack=None
    def observe_clock(self,now_ns):
        if not positive(now_ns) or now_ns<self.last_observed_ns:
            self.revoke('clock_rollback');need(False,'play_clock_rollback')
        self.last_observed_ns=now_ns
    def _probe(self,p,request_id,now_ns,not_before_ns):
        self.observe_clock(now_ns)
        need(p['request_id']==request_id and p['operation_id']==self.operation_id and p['slot_released'] is False,'play_probe_binding')
        need(positive(now_ns) and positive(p['at_ns']) and not_before_ns<=p['at_ns']<=now_ns and now_ns-p['at_ns']<=self.max_age_ns,'play_probe_stale')
        need(p['window_id']==self.window_id and p['renderer_live'] is True and p['owner_live'] is True,'play_probe_live')
        need(p['owner_witness_live'] is True and p['watches_drained'] is True and p['terminal'] is False,'play_probe_watch')
        need(self.renderer.check(p['renderer'],p['at_ns']) and self.owner.check(p['owner'],p['at_ns']),'play_probe_segment')
        need(p['automatic_work_pending'] is False and p['automatic_input_stopped'] is True,'play_probe_pending')
        need(positive(p['owner_deadline_ns']) and p['owner_deadline_ns']>now_ns,'play_owner_expired')
    def step(self,*,now_ns,terminal,request,probe,stop_actions,verify_evidence):
        self.observe_clock(now_ns)
        # Never acknowledge a queued positive request in the same pump as exit/fatal.
        if terminal:
            self.revoke(terminal);return None
        if self.state=='ended':return None
        if self.renderer.invalid or self.owner.invalid:
            self.revoke('segment_invalid');return None
        if now_ns>=self.outer_deadline_ns:
            self.revoke('outer_expired');return None
        if self.state=='user_test_held':
            if now_ns>=self.ack['effective_deadline_ns']:
                self.revoke('hold_expired');return None
            try:
                p=probe(self.ack['request_id'],now_ns);fresh=self.clock()
                self._probe(p,self.ack['request_id'],fresh,now_ns)
                self.ack['effective_deadline_ns']=min(self.ack['effective_deadline_ns'],p['owner_deadline_ns'])
                need(fresh<self.ack['effective_deadline_ns'],'play_hold_expired')
            except Exception:
                self.revoke('live_hold_unconfirmed');raise
            if request is not None:
                if request==self.accepted_request:return None
                need(request=={'action':'finish-user-test','request_id':self.ack['request_id'],'operation_id':self.operation_id},'play_finish_identity')
                self.revoke('user_finished')
            return None
        if request is None:return None
        need(type(request['schema']) is int and request['schema']==1 and request['action']=='actual-play-and-input-confirmed','play_request_action')
        rid=request['request_id'];need(type(rid) is str and re.fullmatch(r'[0-9a-f]{32}',rid) is not None and not self.attempted,'play_request_replay')
        self.attempted=True
        need(request['operation_id']==self.operation_id and request['renderer']==self.renderer.binding and request['owner']==self.owner.binding and request['window_id']==self.window_id,'play_request_binding')
        at=request['at_ns'];need(type(at) is int and max(self.renderer.ready_ns,self.owner.ready_ns)<=at<=now_ns and now_ns-at<=self.max_age_ns,'play_request_clock')
        need(request['visual_status']=='actual-play' and request['input_status']=='responsive','play_request_evidence_status')
        # Derived evidence must not change the repeated control-file identity.
        verification_request=deepcopy(request)
        need(verify_evidence(verification_request) is True,'play_request_evidence')
        need(positive(request['requested_deadline_ns']),'play_requested_deadline')
        verified=self.clock();need(positive(verified) and verified>=now_ns and verified-at<=self.max_age_ns,'play_pair_stale_after_verify')
        manual=request.get('input_source')=='human'
        expiry=verification_request.get('evidence_deadline_ns')
        if manual:need(positive(expiry) and verified<expiry,'play_manual_expired_after_verify')
        try:
            need(stop_actions() is True,'play_stop_unconfirmed')
            self.experiments_stopped=True
            stopped=self.clock();need(positive(stopped) and stopped>=verified and stopped-at<=self.max_age_ns,'play_pair_stale_after_stop')
            p=probe(rid,stopped);now_ns=self.clock();self._probe(p,rid,now_ns,stopped)
            need(now_ns-at<=self.max_age_ns,'play_pair_stale_after_probe')
            if manual:need(now_ns<expiry,'play_manual_expired_after_probe')
            until=min(self.outer_deadline_ns,p['owner_deadline_ns'],request['requested_deadline_ns'])
            need(until>now_ns,'play_hold_expired')
        except Exception:
            self.revoke('hold_unconfirmed');raise
        self.accepted_request=deepcopy(request)
        self.state='user_test_held'
        self.ack=dict(schema=1,request_id=rid,operation_id=self.operation_id,renderer=deepcopy(self.renderer.binding),
          owner=deepcopy(self.owner.binding),window_id=self.window_id,confirmed_as_of_ns=now_ns,
          effective_deadline_ns=until,automatic_input_stopped=True,supervisor_retained_as_of_ns=p['at_ns'],released=False)
        return deepcopy(self.ack)
