# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
"""P1 adapter on the existing game owner; bounded owned observation companions.

Only the existing APISession owns and tears down Wine. Companion helpers use
its unchanged base Session ownership rules, with their own private log root.
"""
from pathlib import Path
from contextlib import contextmanager
import json,os,sys,time,uuid
from pear_runtime.fixtures.inputs import fact,need
from tools.development.game.inputs import coordination_read
from . import handoff as play_handoff, watch as play_watch, witness as play_witness, window as play_window
BOUNDS={'grace_ms':200,'terminate_ms':2000,'kill_ms':3000,'drain_ms':1000}

def owner_deadline(config,grant,now_ns):
    seconds=config['hold_seconds'];limit=grant['not_after_monotonic_ns']
    need(type(seconds) is int and seconds in (900,1800),'play_hold_budget')
    need(type(now_ns) is int and type(limit) is int and 0<now_ns<limit<2**63 and type(grant['maximum_play_seconds']) is int and grant['maximum_play_seconds']==seconds,'play_grant_deadline')
    return min(now_ns+seconds*1_000_000_000,limit)

def companion_session(namespace, output):
    """Construct the captured original Session without leaking a partial observer."""
    observer=namespace.DarwinObserver()
    try:return namespace.Session(output,observer=observer)
    except BaseException as primary:
        try:observer.close()
        except BaseException as cleanup:primary.add_note('Partial companion observer cleanup failed: '+str(cleanup))
        raise


def cleanup_note(primary,phase,error):
    primary.evidence_errors=[*getattr(primary,'evidence_errors',[]),
        dict(phase=phase,type=type(error).__name__,code=getattr(error,'code',str(error)))]
    primary.add_note(phase+' also failed: '+str(error))


def record_companions(adapter):
    from pear_runtime.fixtures.game_release import capture_companions
    return capture_companions(adapter,adapter.output)


@contextmanager
def companion_evidence(adapter):
    """Preserve the original close outcome and add its owned-child evidence."""
    try:yield
    except BaseException as primary:
        try:record_companions(adapter)
        except BaseException as error:cleanup_note(primary,'companion-evidence',error)
        raise
    else:record_companions(adapter)


def close_preserving(adapter,primary):
    try:adapter.close()
    except BaseException as error:cleanup_note(primary,'companion-close',error)


def close_replacement(session,primary):
    """Retire only a newly constructed HUD session that was never published."""
    for field in ('selector','observer'):
        try:getattr(session,field).close()
        except BaseException as error:cleanup_note(primary,'unpublished-hud-'+field,error)


def close_unlaunched(adapter, original_queue, primary):
    """Close only companions already constructed before any helper launch."""
    if adapter.session.observer.queue is getattr(adapter,'tap',None):
        adapter.session.observer.queue=original_queue
    errors=[]
    for name in ('hud_helpers','helpers'):
        session=getattr(adapter,name,None)
        if session is None:continue
        for field in ('selector','observer'):
            try:getattr(session,field).close()
            except BaseException as error:errors.append(dict(phase=name+'-'+field,error=str(error)))
    if errors:
        primary.evidence_errors=[*getattr(primary,'evidence_errors',[]),*errors]
        primary.add_note('Partial companion cleanup also failed; see evidence_errors')

    try:record_companions(adapter)
    except BaseException as error:cleanup_note(primary,'partial-companion-evidence',error)


class Adapter:
    def __init__(self,*,session,output,candidate,selection,sampler,deadline,launch,environment,gate,companion_factory):
        self.session=session;self.output=Path(output);self.candidate=candidate;self.sampler=sampler
        self.gate=gate;self.companion_factory=companion_factory
        self.activation,self.ready=self.gate.check('game',self.output)
        self.operation=self.activation['operation_id'];self.config=self.ready['play_observation']
        g=self.gate.grant(self.output,self.operation)
        self.deadline_ns=owner_deadline(self.config,g,time.monotonic_ns())
        self.root=self.output/'play';self.root.mkdir(mode=0o700)
        original_queue=session.observer.queue
        try:
            self._companion_module=self.companion_factory()
            self.helpers=companion_session(self._companion_module,self.root);hud_root=self.root/'hud';hud_root.mkdir();self.hud_helpers=companion_session(self._companion_module,hud_root);self.hud_result=None;self.tap=play_watch.QueueTap(session.observer.queue);session.observer.queue=self.tap
            self.witness_tap=play_watch.QueueTap(self.helpers.observer.queue);self.helpers.observer.queue=self.witness_tap
            self.windows=play_window.Windows();self.loader=None;self.renderer=None;self.owner=None;self.state=None;self.window=None
            self.witness=None;self.witness_segment=None;self.witness_ready=None;self.capture=None;self.frames=[];self.input_records=[];self.pending_key=None
            self.experiments_stopped=False;self.ended=False;self.reason=None;self.last_live=0;self.last_capture=0;self.last_hold_probe=0;self.last_control=None;self.cleanup=None
            self.capture_bytes=0;self.capture_gaps=[];self.input_count=0;self.last_tick=0;self.log_offset=0;self.hud=None;self.hud_gap=None
            self.helper_env=self.gate.context.child_environment(environment)
            self.owner_identity=self.helpers.observer.identity(os.getpid());exe=self.helpers.observer.executable(os.getpid())
            config=dict(output=str(self.root),owner_identity=self.owner_identity,owner_executable=exe,run=str(self.output),candidate=candidate.name,operation_id=self.operation,deadline_ns=self.deadline_ns)
            config.update(self.gate.context.witness_binding())
            play_witness.atomic(self.root/'witness-config.json',config)
        except BaseException as primary:
            close_unlaunched(self,original_queue,primary)
            raise
        # The original Wine environment remains intact; only reviewed per-run HUD switches are added.
        environment.update(MTL_HUD_ENABLED='1',MTL_HUD_LOG_ENABLED='1',MTL_HUD_LOGGING_ENABLED='1')
        try:
            self.witness=self.helpers.launch('owner-witness',['/usr/bin/arch','-arm64',self.gate.context.value['helper_refs']['python']['path'],'-B','-m','tools.development.game.witness','--config',str(self.root/'witness-config.json')],self.helper_env,allowed_paths=['/usr/bin/arch',self.gate.context.value['helper_refs']['python']['path']])
            need(self.helpers.wait_for(lambda:(self.root/'witness-ready.json').exists() or self.witness.exited,5),'play_witness_start_timeout')
            need(not self.witness.exited,'play_witness_start_failed')
            value=coordination_read(self.root/'witness-ready.json');need(value['valid'] is True and value['owner_identity']==self.owner_identity and value['deadline_ns']==self.deadline_ns and value['config']==fact(self.root/'witness-config.json'),'play_witness_ready_binding')
            binding=value['segment']['binding'];need(value['segment']['invalid'] is None and binding['run']==str(self.output) and binding['candidate']==candidate.name and binding['pid']==os.getpid() and binding['role']=='owner','play_witness_ready_segment')
            self.owner=play_handoff.Segment(binding,value['segment']['ready_ns']);self.witness_ready=value
            self.witness_segment=self.witness_tap.arm(self.helpers.observer,self.witness,str(self.output),candidate.name,role='owner')
        except BaseException as primary:
            close_preserving(self,primary);raise
    @property
    def held(self):return bool(self.state and self.state.state=='user_test_held')
    @property
    def done(self):return self.ended or bool(self.state and self.state.state=='ended')
    @property
    def continue_supervision(self):return not self.done and time.monotonic_ns()<self.deadline_ns
    def started(self,loader):
        self.loader=loader
        st=(self.output/'game/GameAssembly.dll').stat();self.target=dict(dev=st.st_dev,ino=st.st_ino,bytes=st.st_size)
        self.hud=self.hud_helpers.launch('hud-log',['/usr/bin/log','stream','--style','ndjson','--level','info','--process',str(loader.pid),'--predicate','subsystem CONTAINS[c] "metal" OR category CONTAINS[c] "metal" OR eventMessage CONTAINS[c] "metal-HUD"'],self.helper_env)
        self.publish_live()
        play_witness.atomic(self.root/'hud-binding.json',dict(pid=loader.pid,identity=loader.identity,collector_identity=self.hud.identity,started_ns=time.monotonic_ns(),environment={'MTL_HUD_ENABLED':'1','MTL_HUD_LOG_ENABLED':'1','MTL_HUD_LOGGING_ENABLED':'1'},available='unconfirmed until visible HUD and matching records'))
    def fatal(self):
        from pear_runtime.fixtures.direct import finish_reason
        raw=bytes(self.session.streams.get(('loader','stderr'),{}).get('data',b''))
        return self.session.failure or (self.loader and self.loader.exited) or (self.loader and finish_reason(raw,self.loader.pid,self.target))
    def renderer_fresh(self):
        need(self.loader is not None and self.renderer is not None,'play_renderer_unarmed')
        current=self.tap.fresh(self.session.observer,self.loader)
        need(current['invalid'] is None,'play_renderer_invalid')
        return current
    def witness_fresh(self,rid,after):
        self.witness_tap.fresh(self.helpers.observer,self.witness)
        need(not (self.root/'witness-final.json').exists(),'play_witness_finalized')
        nonce=uuid.uuid4().hex
        play_witness.atomic(self.root/'witness-challenge.json',dict(operation_id=self.operation,owner=self.owner.binding,nonce=nonce,after_ns=after,request_id=rid))
        end=time.monotonic()+1.5
        while time.monotonic()<end:
            self.helpers.pump(0.01);self.session.pump(0)
            need(not self.helpers.failure and not self.fatal(),'play_probe_terminal')
            self.witness_tap.fresh(self.helpers.observer,self.witness)
            path=self.root/'witness-response.json'
            if path.exists():
                r=coordination_read(path)
                if r.get('nonce')==nonce:
                    now=time.monotonic_ns()
                    need(r['valid'] is True and r['request_id']==rid and r['operation_id']==self.operation and r['config']==self.witness_ready['config'] and r['watcher_identity']==self.witness.identity and r['owner_identity']==self.owner_identity,'play_witness_response_binding')
                    need(r['segment']['binding']==self.owner.binding and r['segment']['invalid'] is None and after<=r['at_ns']<=now and now-r['at_ns']<=2_000_000_000 and now<r['deadline_ns']==self.deadline_ns,'play_witness_response_fresh')
                    need(not (self.root/'witness-final.json').exists(),'play_witness_finalized')
                    return r
        need(False,'play_witness_response_timeout')
    def probe(self,rid,after):
        self.renderer_fresh();r=self.witness_fresh(rid,after);self.renderer_fresh()
        row=self.windows.exact(self.loader.pid,self.window)
        self.gate.assert_current(self.output,self.operation)
        now=time.monotonic_ns();need(now<self.deadline_ns,'play_owner_expired')
        return dict(request_id=rid,operation_id=self.operation,slot_released=False,at_ns=now,window_id=row['kCGWindowNumber'],renderer_live=True,owner_live=self.helpers.observer.identity(os.getpid())==self.owner_identity,owner_witness_live=True,watches_drained=True,terminal=bool(self.fatal()),renderer=self.renderer.binding,owner=self.owner.binding,automatic_work_pending=self.capture is not None or self.pending_key is not None or self.sampler.active is not None,automatic_input_stopped=self.experiments_stopped,owner_deadline_ns=min(self.deadline_ns,r['deadline_ns']))
    def capture_start(self):
        if self.experiments_stopped or self.pending_key is not None or self.capture is not None or len(self.frames)+len(self.capture_gaps)>=32:return
        if self.capture_bytes>=48*1024**2:return
        self.last_capture=time.monotonic()
        if not self.windows.cg.CGPreflightScreenCaptureAccess():
            if not self.capture_gaps or self.capture_gaps[-1]['reason']!='screen_capture_permission_unavailable':self.capture_gaps.append(dict(at_ns=time.monotonic_ns(),reason='screen_capture_permission_unavailable'))
            return
        before=self.renderer_fresh();row=self.windows.exact(self.loader.pid,self.window);index=len(self.frames)+len(self.capture_gaps)
        name='capture-'+str(index);dest=self.root/(name+'.png')
        child=self.helpers.launch(name,['/usr/sbin/screencapture','-x','-o','-l',str(self.window),str(dest)],self.helper_env)
        self.capture=dict(child=child,destination=dest,before=before,window=row,started_ns=time.monotonic_ns(),deadline=time.monotonic()+15)
        self.last_capture=time.monotonic()
    def capture_finish(self,cancel=False):
        if self.capture is None:return
        c=self.capture;child=c['child']
        if not cancel and not child.exited and time.monotonic()<c['deadline']:return
        report=self.helpers.cleanup((child.role,),BOUNDS,allow_interrupt=False)
        need(report['complete'],'play_capture_cleanup')
        try:
            after=self.renderer_fresh();row=self.windows.exact(self.loader.pid,self.window)
            need(not cancel and child.exit_code==0 and c['destination'].is_file() and c['destination'].stat().st_size<=8*1024**2,'play_capture_failed')
            ref=fact(c['destination']);self.capture_bytes+=ref['size_bytes']
            record=dict(image=ref,renderer=self.renderer.binding,owner=self.owner.binding,window_id=self.window,started_ns=c['started_ns'],ended_ns=time.monotonic_ns(),window_before=c['window'],window_after=row,cleanup=report)
            path=c['destination'].with_suffix('.json');play_witness.atomic(path,record);self.frames.append(fact(path))
        except play_watch.ConfirmedExit:
            raise
        except Exception as exc:self.capture_gaps.append(dict(at_ns=time.monotonic_ns(),reason=str(exc)))
        finally:self.capture=None
    def input(self,request):
        need(not self.experiments_stopped and not self.held and self.input_count<16,'play_input_stopped_or_bound')
        need(request['renderer']==self.renderer.binding and request['owner']==self.owner.binding and request['window_id']==self.window and request['operation_id']==self.operation,'play_input_identity')
        need(0<=time.monotonic_ns()-request['at_ns']<=30_000_000_000,'play_input_stale')
        need(self.capture is None and self.pending_key is None,'play_input_pending')
        self.renderer_fresh();row=self.windows.exact(self.loader.pid,self.window)
        if not self.windows.cg.CGPreflightPostEventAccess():
            play_witness.atomic(self.root/'input-unavailable.json',dict(request=request,at_ns=time.monotonic_ns(),reason='post_event_permission_unavailable'));return
        before=self.frames[-1] if self.frames else None;need(before is not None,'play_input_before_capture')
        record=dict(request=request,before_capture=before,posted_ns=time.monotonic_ns(),response_confirmed=False)
        if request['action']=='click':self.windows.click(self.loader.pid,row,request['x'],request['y'])
        elif request['action']=='key':
            need(type(request['duration_ms']) is int and 50<=request['duration_ms']<=250,'play_key_duration')
            self.windows.key(self.loader.pid,request['key'],True);record['posted_ns']=time.monotonic_ns();self.pending_key=dict(key=request['key'],release_at=time.monotonic()+request['duration_ms']/1000,record=record,path=self.root/('input-'+str(self.input_count+1)+'.json'))
        else:need(False,'play_input_action')
        self.input_count+=1;self.input_records.append(record);self.last_capture=0
        play_witness.atomic(self.root/('input-'+str(self.input_count)+'.json'),record)
    def release_key(self):
        if self.pending_key is not None:
            self.renderer_fresh();self.windows.key(self.loader.pid,self.pending_key['key'],False)
            pending=self.pending_key;pending['record']['released_ns']=time.monotonic_ns();pending['record']['observed_hold_ns']=pending['record']['released_ns']-pending['record']['posted_ns'];play_witness.atomic(pending['path'],pending['record']);self.pending_key=None
    def stop_actions(self):
        self.experiments_stopped=True;self.release_key();self.capture_finish(cancel=True);self.sampler.cancel()
        return self.capture is None and self.pending_key is None and self.sampler.active is None
    def verify(self,request):
        need(request['observed_by']=='assistant_visual_inspection','play_visual_observer')
        refs=request['evidence'];need(type(refs) is list and len(refs)==2,'play_visual_pair')
        records=[]
        for ref in refs:
            need(ref in self.frames and fact(ref['path'])==ref,'play_evidence_reference')
            row=coordination_read(ref['path']);need(row['renderer']==self.renderer.binding and row['owner']==self.owner.binding and row['window_id']==self.window and fact(row['image']['path'])==row['image'],'play_evidence_binding')
            need(self.renderer.ready_ns<=row['started_ns']<=row['ended_ns']<=request['at_ns'] and request['at_ns']-row['ended_ns']<=60_000_000_000,'play_evidence_age');records.append(row)
        inp=request['input_evidence'];need(fact(inp['path'])==inp and Path(inp['path']).parent==self.root and Path(inp['path']).name.startswith('input-'),'play_response_input')
        posted=coordination_read(inp['path']);need(posted in self.input_records and posted['request']['renderer']==self.renderer.binding and records[0]['ended_ns']<=posted['posted_ns']<=records[1]['started_ns'],'play_response_order')
        need(request['response_observed']=='in-game movement or action changed visibly','play_response_observer')
        return True
    def end(self,reason):
        self.ended=True;self.reason=self.reason or reason;self.experiments_stopped=True
        if self.state:self.state.revoke(self.reason)
        self.publish_live(force=True)
    def tick(self,raw,terminal=False):
        try:
            self._tick(raw,terminal)
        except play_watch.ConfirmedExit as exc:
            if self.renderer is None or exc.segment['binding']!=self.renderer.binding:
                self.end('companion_terminal');raise
            self.terminal_observation=dict(at_ns=time.monotonic_ns(),segment=exc.segment,secondary=exc.secondary)
            self.end('renderer_exit')
        except BaseException as exc:
            self.observation_error=dict(at_ns=time.monotonic_ns(),phase='play-adapter-tick',type=type(exc).__name__,code=getattr(exc,'code',str(exc)))
            try:self.end('observation_error')
            except BaseException as publication:self.observation_error['publication_error']=str(publication)
            raise
    def _tick(self,raw,terminal=False):
        now=time.monotonic_ns()
        if terminal or now>=self.deadline_ns:
            self.end('terminal' if terminal else 'owner_deadline')
            return
        self.helpers.pump(0)
        need(not self.helpers.failure and not self.witness.exited,'play_companion_unavailable')
        if self.pending_key:
            if time.monotonic()>=self.pending_key['release_at']:self.release_key()
            else:return
        if time.monotonic()-self.last_tick<.2:return
        self.last_tick=time.monotonic()
        if len(raw)>self.log_offset:
            with (self.output/'live-loader.stderr.log').open('ab') as log:log.write(raw[self.log_offset:])
            self.log_offset=len(raw)
        self.hud_tick()
        if self.loader and self.renderer is None:
            path=str((self.session.runtime/self.session.signed['entrypoints']['loader']).resolve())
            if self.loader.pid in self.session.observer.registrations and self.session.observer.executable(self.loader.pid)==path:
                self.renderer=self.tap.arm(self.session.observer,self.loader,str(self.output),self.candidate.name)
        if self.renderer is None:
            self.publish_live();return
        self.renderer_fresh()
        rows=self.windows.rows(self.loader.pid)
        if self.window is None:
            if not rows:
                self.publish_live();return
            self.window=rows[0]['kCGWindowNumber'];self.state=play_handoff.PlayHandoff(self.renderer,self.owner,self.window,self.operation,self.deadline_ns,max_age_ns=60_000_000_000)
        self.windows.exact(self.loader.pid,self.window)
        if self.pending_key and time.monotonic()>=self.pending_key['release_at']:self.release_key()
        self.capture_finish()
        request=None;p=self.root/'control.json'
        if p.exists():
            need(not p.is_symlink() and p.stat().st_size<=65536,'play_control_file');request=coordination_read(p)
        if request is not None and request.get('action') in ('click','key','capture'):
            if request!=self.last_control:
                need(not self.experiments_stopped,'play_control_after_stop')
                if request['action']=='capture':self.capture_start()
                else:self.input(request)
                self.last_control=request
            request=None
        # Human visual inspection takes longer than a kernel probe. Frame-pair
        # age is capped at60s; each live owner challenge independently at2s.
        if request is not None or self.held and time.monotonic()-self.last_hold_probe>=1:
            ack=self.state.step(now_ns=now,terminal=bool(self.fatal()),request=request,probe=self.probe,stop_actions=self.stop_actions,verify_evidence=self.verify)
            self.last_hold_probe=time.monotonic()
            if ack:
                play_witness.atomic(self.root/'handoff-request.json',self.state.accepted_request)
                play_witness.atomic(self.root/'handoff-ack.json',ack);print('Actual play and input confirmed; same game retained for user test',flush=True)
        if not self.experiments_stopped and time.monotonic()-self.last_capture>=10:self.capture_start()
        self.publish_live()
    def publish_live(self,force=False):
        if not force and time.monotonic()-self.last_live<1:return
        play_witness.atomic(self.output/'live.json',dict(run=str(self.output),candidate=self.candidate.name,operation_id=self.operation,loader_identity=self.loader.identity if self.loader else None,renderer=self.renderer.snapshot() if self.renderer else None,owner=self.owner.snapshot() if self.owner else None,window_id=self.window,deadline_ns=self.deadline_ns,updated_ns=time.monotonic_ns(),state='ended' if self.ended else self.state.state if self.state else 'awaiting-window',reason=self.reason,ack=self.state.ack if self.state else None,frames=self.frames[-3:],capture_gaps=self.capture_gaps,hud_gap=self.hud_gap,released=False,automatic_input_stopped=self.experiments_stopped))
        self.last_live=time.monotonic()
    def hud_tick(self):
        if self.hud is None or self.hud_result is not None:return
        self.hud_helpers.pump(0)
        count=sum(x['total_bytes'] for (role,_),x in self.hud_helpers.streams.items() if role=='hud-log')
        if self.hud_helpers.failure or self.hud.exited or count>=192*1024:
            self.hud_gap=dict(reason=self.hud_helpers.failure or ('collector_exited' if self.hud.exited else 'collector_output_bound'),at_ns=time.monotonic_ns(),observed_bytes=count)
            self.close_hud()
        elif ('hud-log','stdout') in self.hud_helpers.streams:
            (self.root/'hud-live.ndjson').write_bytes(self.hud_helpers.streams[('hud-log','stdout')]['data'])
    def close_hud(self):
        if self.hud_result is not None:return
        cleanup=self.hud_helpers.cleanup(tuple(self.hud_helpers.children),BOUNDS,allow_interrupt=False)
        logs=self.hud_helpers.finish_logs(1000)
        self.hud_result=dict(cleanup=cleanup,logs=logs,gap=self.hud_gap,failure=self.hud_helpers.failure)
        play_witness.atomic(self.root/'hud-result.json',self.hud_result)
        self.hud_helpers.selector.close();self.hud_helpers.observer.close()
        need(cleanup['complete'],'play_hud_cleanup')
    def snapshot(self):return dict(terminal_observation=getattr(self,'terminal_observation',None),observation_error=getattr(self,'observation_error',None),state='ended' if self.ended else self.state.state if self.state else 'unarmed',reason=self.reason,ack=self.state.ack if self.state else None,accepted_request=self.state.accepted_request if self.state else None,frames=self.frames,input_count=self.input_count,capture_gaps=self.capture_gaps,owner_deadline_ns=self.deadline_ns,cleanup=self.cleanup)
    def close(self):
        with companion_evidence(self):
            self.experiments_stopped=True;errors=[]
            try:self.end('owner_closed')
            except BaseException as exc:errors.append(dict(phase='terminal-publication',error=str(exc)))
            try:
                if self.pending_key is not None and self.loader and not self.loader.exited:self.release_key()
            except BaseException as exc:errors.append(dict(phase='key-release',error=str(exc)))
            try:self.close_hud()
            except BaseException as exc:errors.append(dict(phase='hud-cleanup',error=str(exc)))
            try:
                (self.root/'witness-stop').touch()
                self.cleanup=self.helpers.cleanup(tuple(self.helpers.children),BOUNDS,allow_interrupt=False)
                logs=self.helpers.finish_logs(1000)
                play_witness.atomic(self.root/'companion-result.json',dict(cleanup=self.cleanup,logs=logs,output_limit=self.helpers.failure,errors=errors,snapshot=self.snapshot()))
            finally:
                self.helpers.selector.close();self.helpers.observer.close()
            need(not errors and self.cleanup['complete'] and self.helpers.failure is None,'play_companion_cleanup')
