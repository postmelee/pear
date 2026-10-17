# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
# Adapted from play_adapter.py/manual_play_adapter.py (MIT).
"""Manual feedback observation, preserving existing identity and cleanup guards."""
import time
from pear_runtime.fixtures.inputs import need
from . import witness as play_witness
from tools.development.game.manual import ManualAdapter
from .adapter import companion_session, close_preserving, close_replacement

CAPTURE_SECONDS=20
CAPTURE_COUNT=96
CAPTURE_BYTES=192*1024**2
HUD_STREAM_BYTES=4*1024**2
HUD_STOP_BYTES=3*1024**2

class FeedbackManualAdapter(ManualAdapter):
    def __init__(self,**kwargs):
        began=time.monotonic_ns()
        super().__init__(**kwargs)
        try:
            # Only this new, childless HUD session receives a larger bounded pipe.
            # The game session, witness and process observation code are unchanged.
            need(not self.hud_helpers.children,'feedback_hud_before_children')
            self._hud_module=self.companion_factory()
            self._hud_module.STREAM_LIMIT=HUD_STREAM_BYTES
            replacement=companion_session(self._hud_module,self.root/'hud')
            try:
                self.hud_helpers.selector.close();self.hud_helpers.observer.close()
            except BaseException as primary:
                close_replacement(replacement,primary)
                raise
            self.hud_helpers=replacement
            self.feedback_timing=dict(adapter_begin_ns=began,adapter_ready_ns=time.monotonic_ns())
            play_witness.atomic(self.root/'feedback-observation-policy.json',dict(
                capture_seconds=CAPTURE_SECONDS,capture_count=CAPTURE_COUNT,
                capture_bytes=CAPTURE_BYTES,hud_stream_bytes=HUD_STREAM_BYTES,
                hud_stop_bytes=HUD_STOP_BYTES,automatic_input_allowed=False,
                timing=self.feedback_timing,scope='Observation budget only; original identity, terminal and cleanup guards retained'))
        except BaseException as primary:
            close_preserving(self,primary)
            raise

    def started(self,loader):
        self.feedback_timing['loader_started_callback_ns']=time.monotonic_ns()
        super().started(loader)
        play_witness.atomic(self.root/'feedback-launch-timing.json',self.feedback_timing)

    def capture_start(self):
        if self.experiments_stopped or self.pending_key is not None or self.capture is not None:return
        if len(self.frames)+len(self.capture_gaps)>=CAPTURE_COUNT or self.capture_bytes>=CAPTURE_BYTES:return
        if time.monotonic()-self.last_capture<CAPTURE_SECONDS:return
        self.last_capture=time.monotonic()
        if not self.windows.cg.CGPreflightScreenCaptureAccess():
            if not self.capture_gaps or self.capture_gaps[-1]['reason']!='screen_capture_permission_unavailable':
                self.capture_gaps.append(dict(at_ns=time.monotonic_ns(),reason='screen_capture_permission_unavailable'))
            return
        before=self.renderer_fresh();row=self.windows.exact(self.loader.pid,self.window)
        index=len(self.frames)+len(self.capture_gaps);name='capture-'+str(index);dest=self.root/(name+'.png')
        child=self.helpers.launch(name,['/usr/sbin/screencapture','-x','-o','-l',str(self.window),str(dest)],self.helper_env)
        self.capture=dict(child=child,destination=dest,before=before,window=row,started_ns=time.monotonic_ns(),deadline=time.monotonic()+15)
        self.last_capture=time.monotonic()

    def hud_tick(self):
        if self.hud is None or self.hud_result is not None:return
        self.hud_helpers.pump(0)
        count=sum(x['total_bytes'] for (role,_),x in self.hud_helpers.streams.items() if role=='hud-log')
        if self.hud_helpers.failure or self.hud.exited or count>=HUD_STOP_BYTES:
            self.hud_gap=dict(reason=self.hud_helpers.failure or ('collector_exited' if self.hud.exited else 'collector_output_bound'),at_ns=time.monotonic_ns(),observed_bytes=count)
            self.close_hud()
        elif ('hud-log','stdout') in self.hud_helpers.streams:
            (self.root/'hud-live.ndjson').write_bytes(self.hud_helpers.streams[('hud-log','stdout')]['data'])


def bind_factory(*, gate, companion_factory):
    """Bind the live operation and its captured companion constructor once."""
    def factory(*, session, output, candidate, selection, sampler, deadline, launch, environment):
        return FeedbackManualAdapter(session=session, output=output, candidate=candidate,
            selection=selection, sampler=sampler, deadline=deadline, launch=launch,
            environment=environment, gate=gate, companion_factory=companion_factory)
    return factory
