# SPDX-License-Identifier: MIT
"""Changed input and omitted build evidence must prevent candidate admission."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.dxmt.translated_inputs import check_files,digest,save
from tools.dxmt.translated_runtime import admit_build

class AdmissionTests(unittest.TestCase):
    def test_replaced_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'module').write_bytes(b'original')
            rows=[dict(path='module',sha256=digest(b'original'),size_bytes=8)]
            check_files(root,rows)
            (root/'module').write_bytes(b'replaced')
            with self.assertRaises(Exception):check_files(root,rows)

    def test_symlink_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'target').write_bytes(b'original');(root/'module').symlink_to('target')
            with self.assertRaises(Exception):
                check_files(root,[dict(path='module',sha256=digest(b'original'),size_bytes=8)])

    def test_incomplete_build_is_rejected_before_payload(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);save(root/'build.json',dict(kind='translated_graphics_build',passed=False))
            with patch('tools.dxmt.translated_runtime.admit') as read_input:
                with self.assertRaises(Exception):admit_build(root)
                read_input.assert_not_called()

    def test_duplicate_artifacts_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'module').write_bytes(b'a')
            row=dict(path='module',sha256=digest(b'a'),size_bytes=1)
            with self.assertRaises(Exception):check_files(root,[row,row])

if __name__=='__main__':unittest.main()
