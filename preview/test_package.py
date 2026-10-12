# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Distribution boundary tests use synthetic payloads, never a private prefix."""
import tempfile
import unittest
from pathlib import Path
from package import REQUIRED, audit_app


class PackageBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="pear-package-test-")
        self.addCleanup(self.scratch.cleanup)
        self.app = Path(self.scratch.name) / "Pear Preview.app"
        for name in REQUIRED | {"Contents/Resources/licenses/example.txt"}:
            p = self.app / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("fixture")

    def test_known_payload_is_admitted(self):
        self.assertEqual(set(audit_app(self.app)), REQUIRED | {"Contents/Resources/licenses/example.txt"})

    def test_private_state_is_rejected(self):
        p = self.app / "Contents/Resources/private/prefix/account.dat"
        p.parent.mkdir(parents=True)
        p.write_text("synthetic private sentinel")
        with self.assertRaises(ValueError):
            audit_app(self.app)

    def test_external_link_is_rejected(self):
        (self.app / "Contents/Resources/licenses/linked.txt").symlink_to("/etc/hosts")
        with self.assertRaises(ValueError):
            audit_app(self.app)

    def test_incomplete_bundle_is_rejected(self):
        (self.app / "Contents/Resources/pear-preview").unlink()
        with self.assertRaises(ValueError):
            audit_app(self.app)


if __name__ == "__main__":
    unittest.main()
