# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
"""Tap the existing owner kqueue without changing its process/cleanup decisions.

Install before launch. All queue consumers receive the original events after the
selected segment has recorded sticky invalidation. No exec ordinal is inferred.
"""
import select,time,uuid
from pear_runtime.fixtures.inputs import need
from tools.development.game.handoff import Segment

class ConfirmedExit(Exception):
    """Negative terminal evidence; never a fresh positive or a resource release."""
    code='play_confirmed_exit'
    def __init__(self,segment,secondary=None):
        super().__init__(self.code);self.segment=segment;self.secondary=secondary

class QueueTap:
    def __init__(self,queue,clock=time.monotonic_ns,token=lambda:uuid.uuid4().hex):
        self._queue=queue;self.clock=clock;self.token=token
        self.rows={};self.segment=None;self.selected_pid=None;self.problem=None;self.arm_attempted=False
    def invalidate(self,reason):
        self.problem=self.problem or reason
        if self.segment:self.segment.invalidate(reason,self.clock())
    def fileno(self):return self._queue.fileno()
    def close(self):
        self.invalidate('watch_closed');return self._queue.close()
    def control(self,changes,max_events,timeout=None):
        changes=list(changes) if changes is not None else None
        try:events=self._queue.control(changes,max_events,timeout)
        except BaseException:
            self.invalidate('watch_error');raise
        for change in changes or ():
            if change.filter!=select.KQ_FILTER_PROC:continue
            pid=change.ident
            if change.flags & select.KQ_EV_DELETE:
                if pid==self.selected_pid:self.invalidate('watch_deleted')
                self.rows.pop(pid,None)
            if change.flags & select.KQ_EV_ADD:
                if pid in self.rows:
                    if pid==self.selected_pid:self.invalidate('watch_replaced')
                    self.rows.pop(pid)
                if len(self.rows)>=128:self.invalidate('watch_capacity');continue
                required=select.KQ_NOTE_EXEC|select.KQ_NOTE_EXIT
                self.rows[pid]=dict(watch_id=self.token(),change_token=self.token(),registered_ns=self.clock(),complete=change.fflags&required==required)
        if max_events>0 and len(events)>=max_events:self.invalidate('watch_backlog_unconfirmed')
        for event in events:
            if event.flags & select.KQ_EV_ERROR:self.invalidate('watch_event_error')
            if event.filter!=select.KQ_FILTER_PROC:continue
            row=self.rows.get(event.ident)
            if row is None:self.invalidate('watch_unknown_process');continue
            exec_seen=bool(event.fflags&select.KQ_NOTE_EXEC);exit_seen=bool(event.fflags&select.KQ_NOTE_EXIT)
            if exec_seen or exit_seen:
                row['change_token']=self.token()
                if event.ident==self.selected_pid and self.segment:
                    self.segment.event(exec_seen=exec_seen,exit_seen=exit_seen,at_ns=self.clock())
        return events
    def arm(self,observer,child,run,candidate,role='renderer'):
        need(not self.arm_attempted,'play_watch_one_arming');self.arm_attempted=True
        need(observer.queue is self and self.problem is None,'play_watch_unavailable')
        observer.refresh();row=self.rows.get(child.pid)
        need(row is not None and row['complete'],'play_watch_not_registered')
        before=dict(row);identity=observer.identity(child.pid);executable=observer.executable(child.pid)
        need(identity==child.identity and executable in child.allowed_paths and not child.exited and not child.reaped,'play_watch_baseline')
        observer.refresh()
        need(self.problem is None and observer.queue is self and self.rows.get(child.pid)==before and observer.identity(child.pid)==identity and observer.executable(child.pid)==executable and not child.exited,'play_watch_arming_race')
        self.selected_pid=child.pid
        self.segment=Segment(dict(run=str(run),candidate=candidate,role=role,pid=child.pid,
          birth=[identity['start_sec'],identity['start_usec']],executable=executable,watch_id=row['watch_id'],segment_id=self.token()),self.clock())
        return self.segment
    def confirmed_exit(self,observer,child,secondary=None):
        binding=self.segment.binding
        row=self.rows.get(child.pid)
        if (self.problem is None and observer.queue is self and
            child.exited and getattr(observer,'handles',{}).get(child.pid) is child and
            child.identity['pid']==binding['pid'] and
            [child.identity['start_sec'],child.identity['start_usec']]==binding['birth'] and
            row and row['watch_id']==binding['watch_id'] and
            self.segment.invalid and self.segment.invalid['reason']=='exit'):
            raise ConfirmedExit(self.segment.snapshot(),secondary)
    def fresh(self,observer,child):
        try:
            need(self.segment is not None and observer.queue is self and self.problem is None,'play_watch_unavailable')
            observer.refresh();self.confirmed_exit(observer,child);binding=self.segment.binding
            need(self.segment.invalid is None,'play_watch_segment_invalid')
            try:
                actual=observer.identity(child.pid);executable=observer.executable(child.pid)
            except Exception as exc:
                if getattr(exc,'code',None) not in ('owned_identity_unavailable','owned_executable_unavailable'):raise
                secondary=dict(code=getattr(exc,'code',str(exc)),type=type(exc).__name__,at_ns=self.clock(),phase='renderer-identity-query')
                observer.refresh();self.confirmed_exit(observer,child,secondary)
                raise
            need(actual==child.identity and [actual['start_sec'],actual['start_usec']]==binding['birth'] and executable==binding['executable'] and not child.exited and not child.reaped,'play_watch_identity_changed')
            observer.refresh();self.confirmed_exit(observer,child)
            need(self.segment.invalid is None and self.problem is None,'play_watch_segment_invalid')
            return self.segment.snapshot()
        except ConfirmedExit:
            raise
        except Exception:
            self.invalidate('watch_freshness_failed');raise
