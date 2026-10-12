# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import runtime_sign as rs
import runtime_build as rb


class SigningBoundaryTests(unittest.TestCase):
    def test_rejects_private_members_and_traversal(self):
        for name in ['private/credentials', 'Libraries/../private', '/Libraries/Wine/bin/wine']:
            with self.assertRaises(ValueError):
                rs.expected_files({'files':[{'path':name,'sha256':'unused'}]})

    def test_refuses_copy_inside_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with self.assertRaisesRegex(ValueError,'separate'):
                rs.sign(root, root/'missing-manifest', root/'nested', 'unused')
            self.assertFalse((root/'nested').exists())

    def test_extra_input_is_refused_before_signing(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'Libraries';source.mkdir()
            (source/'private-secret').write_text('must not ship')
            manifest=root/'manifest.json';manifest.write_text(json.dumps({'files':[]}))
            with patch.object(rs.subprocess,'run') as signer:
                with self.assertRaisesRegex(ValueError,'differs'):
                    rs.sign(source,manifest,root/'out','unused')
                signer.assert_not_called()
            self.assertFalse((root/'out').exists())


if __name__=='__main__':unittest.main()
