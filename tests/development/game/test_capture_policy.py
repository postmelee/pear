# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
import unittest
from tools.development.game.capture_policy import eligible

class CapturePolicy(unittest.TestCase):
    def row(self,**changes):
        v=dict(kCGWindowOwnerPID=42,kCGWindowNumber=100,kCGWindowLayer=0,kCGWindowIsOnscreen=True,kCGWindowBounds=dict(Width=960.0,Height=572.0));v.update(changes);return v
    def test_same_owned_window_survives_fullscreen_layer_transition(self):
        self.assertTrue(eligible(self.row(),42))
        self.assertTrue(eligible(self.row(kCGWindowLayer=26,kCGWindowBounds=dict(Width=1512.0,Height=982.0)),42))
    def test_foreign_offscreen_and_unobserved_layers_are_excluded(self):
        for changes in (dict(kCGWindowOwnerPID=43),dict(kCGWindowIsOnscreen=False),dict(kCGWindowIsOnscreen=None),dict(kCGWindowLayer=25),dict(kCGWindowNumber=0),dict(kCGWindowNumber=True)):
            self.assertFalse(eligible(self.row(**changes),42))
    def test_owned_menu_bars_and_bad_dimensions_are_excluded(self):
        for bounds in (dict(Width=1512,Height=33),dict(Width=float('nan'),Height=900),dict(Width=100,Height=True),None,{}):
            self.assertFalse(eligible(self.row(kCGWindowBounds=bounds),42))

if __name__=='__main__':unittest.main()
