"""Negative controls for the one source-bound generated Wine link."""
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[2] / 'tools/dxmt'
sys.path.insert(0, str(TOOLS))
import pairing_monitor as monitor
from common import Error


class PairMonitorTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name).resolve()
        self.source = self.root / 'wine/source/nls/locale.nls'
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(b'original locale')
        self.link = self.root / monitor.LINK
        self.link.parent.mkdir(parents=True)
        self.lock = patch.object(monitor, 'LOCALE_SHA256', hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.lock.start(); self.addCleanup(self.lock.stop)

    def test_exact_owned_source_link(self):
        self.link.symlink_to(monitor.TARGET)
        self.assertGreaterEqual(monitor.directory_usage(self.root), self.source.stat().st_blocks * 512)

    def test_changed_locale_refused(self):
        self.link.symlink_to(monitor.TARGET)
        self.source.write_bytes(b'changed locale')
        with self.assertRaisesRegex(Error, 'pair_monitor_locale_target'):
            monitor.directory_usage(self.root)

    def test_unlisted_leaf_link_refused(self):
        (self.root / 'unknown').symlink_to(self.source)
        with self.assertRaisesRegex(Error, 'pair_monitor_unlisted_alias'):
            monitor.directory_usage(self.root)

    def test_directory_link_refused(self):
        (self.root / 'alias').symlink_to(self.source.parent, target_is_directory=True)
        with self.assertRaisesRegex(Error, 'pair_monitor_directory_alias'):
            monitor.directory_usage(self.root)

    def test_wrong_target_refused(self):
        self.link.symlink_to('/private/tmp/outside-locale')
        with self.assertRaisesRegex(Error, 'pair_monitor_unlisted_alias'):
            monitor.directory_usage(self.root)

    def test_unmodified_regular_files_allowed(self):
        self.assertGreater(monitor.directory_usage(self.root), 0)

if __name__ == '__main__':
    unittest.main()
