# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.util,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from tools.development.game import feedback as mod
class ObservationTests(unittest.TestCase):
    def adapter(self):
        a=object.__new__(mod.FeedbackManualAdapter)
        a.experiments_stopped=False;a.pending_key=None;a.capture=None;a.frames=[];a.capture_gaps=[];a.capture_bytes=0;a.last_capture=0
        a.windows=SimpleNamespace(cg=SimpleNamespace(CGPreflightScreenCaptureAccess=Mock(return_value=True)),exact=Mock(return_value={'window':7}))
        a.renderer_fresh=Mock(return_value={'valid':True});a.loader=SimpleNamespace(pid=12);a.window=7;a.root=Path('/unused');a.helper_env={};a.helpers=SimpleNamespace(launch=Mock(return_value=object()))
        return a
    def test_manual_only_refuses_key_and_click(self):
        for action in ('key','click'):
            with self.assertRaises(Exception):self.adapter().input({'action':action})
    def test_capture_after_old_count_limit_retains_identity_binding(self):
        a=self.adapter();a.frames=[None]*32;a.capture_start()
        a.renderer_fresh.assert_called_once();a.windows.exact.assert_called_once_with(12,7)
        args=a.helpers.launch.call_args.args;self.assertEqual(args[1],['/usr/sbin/screencapture','-x','-o','-l','7','/unused/capture-32.png'])
    def test_count_bytes_stop_and_pacing_prevent_launch(self):
        for field,value in [('frames',[None]*96),('capture_bytes',mod.CAPTURE_BYTES),('last_capture',time.monotonic()),('experiments_stopped',True),('pending_key',{}),('capture',{})]:
            with self.subTest(field=field):
                a=self.adapter();setattr(a,field,value);a.capture_start();a.helpers.launch.assert_not_called()
    def test_permission_gap_does_not_launch_or_repeat_gap(self):
        a=self.adapter();a.windows.cg.CGPreflightScreenCaptureAccess.return_value=False
        a.capture_start();a.last_capture=0;a.capture_start();self.assertEqual(len(a.capture_gaps),1);a.helpers.launch.assert_not_called()
    def test_hud_failure_exit_and_bound_close_without_changing_game(self):
        for failure,exited,count in [('pipe_error',False,0),(None,True,0),(None,False,mod.HUD_STOP_BYTES)]:
            a=self.adapter();a.hud=SimpleNamespace(exited=exited);a.hud_result=None;a.close_hud=Mock();a.hud_helpers=SimpleNamespace(pump=Mock(),failure=failure,streams={('hud-log','stderr'):{'total_bytes':count}})
            a.hud_tick();a.close_hud.assert_called_once();self.assertEqual(a.hud_gap['observed_bytes'],count)
    def test_constructor_failure_closes_existing_witness(self):
        from tools.development.game.manual import ManualAdapter
        def parent(a,**kwargs):
            a.hud_helpers=SimpleNamespace(children={});a.companion_factory=Mock(side_effect=RuntimeError('load_failed'))
        with patch.object(ManualAdapter,'__init__',parent),patch.object(mod.FeedbackManualAdapter,'close') as close:
            with self.assertRaisesRegex(RuntimeError,'load_failed'):mod.FeedbackManualAdapter()
            close.assert_called_once()
    def test_extended_hud_remains_bounded(self):
        a=self.adapter();a.hud=SimpleNamespace(exited=False);a.hud_result=None;a.close_hud=Mock();a.hud_helpers=SimpleNamespace(pump=Mock(),failure=None,streams={('hud-log','stderr'):{'total_bytes':200*1024}})
        a.hud_tick();a.close_hud.assert_not_called();self.assertLess(mod.HUD_STOP_BYTES,mod.HUD_STREAM_BYTES)
if __name__=='__main__':unittest.main(verbosity=2)
