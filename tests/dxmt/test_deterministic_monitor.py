"""Output accounting and rejection controls for transient compiler cache locks."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[2] / 'tools/dxmt'
sys.path.insert(0, str(TOOLS))
import deterministic_monitor as monitor
import pairing_monitor as legacy
from common import Error


class Monitor(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.link = self.root / 'dxmt/shader-cache/1RIS3SY4XDABG/metal_math-46Y4VH5SL9BI.pcm.lock'
        self.link.parent.mkdir(parents=True)
        self.target = Path(str(self.link) + '-0abe6f73')
        self.target.write_bytes(b'compiler lock owner')
        self.link.symlink_to(self.target)
        self.bound = monitor.bind(legacy)

    def test_owned_absolute_sibling_and_regular_storage_counted(self):
        self.assertEqual(self.bound.directory_usage(self.root),
                         (self.link.lstat().st_blocks + self.target.stat().st_blocks) * 512)

    def test_modules_index_lock_admitted(self):
        self.link.unlink(); self.link = self.link.with_name('modules.idx.lock')
        self.target = Path(str(self.link) + '-dca258ba')
        self.target.write_bytes(b'index lock'); self.link.symlink_to(self.target)
        self.assertGreater(self.bound.directory_usage(self.root), 0)

    def test_released_target_can_disappear_first(self):
        self.target.unlink()
        self.assertEqual(self.bound.directory_usage(self.root), self.link.lstat().st_blocks * 512)

    def test_released_link_during_read_is_tolerated(self):
        original = self.link.lstat(); self.link.unlink()
        monitor.cache_lock(self.root, self.link, original, legacy)

    def test_external_relative_and_wrong_sibling_refused(self):
        for target in ('/private/tmp/outside', self.target.name,
                       str(self.link) + '-nothex12', str(self.link) + '-012345678',
                       str(self.link.parent / 'other.pcm.lock-01234567')):
            self.link.unlink(); self.link.symlink_to(target)
            with self.subTest(target=target), self.assertRaises(Error):
                self.bound.directory_usage(self.root)

    def test_unknown_lock_namespace_refused(self):
        self.link.unlink()
        for name in ('other/cache/ABC/a.pcm.lock', 'dxmt/shader-cache/ABC/a.lock',
                     'dxmt/shader-cache/ABC/a/b.pcm.lock', 'dxmt/shader-cache/../a.pcm.lock'):
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(str(path) + '-01234567')
            try:
                with self.subTest(name=name), self.assertRaises(Error):
                    self.bound.directory_usage(self.root)
            finally: path.unlink()

    def test_directory_alias_refused(self):
        (self.root / 'alias').symlink_to(self.link.parent, target_is_directory=True)
        with self.assertRaisesRegex(Error, 'pair_monitor_directory_alias'):
            self.bound.directory_usage(self.root)

    def test_symlink_lock_target_refused(self):
        self.target.unlink(); self.target.symlink_to(self.root / 'absent')
        with self.assertRaisesRegex(Error, 'det_monitor_lock_target_type'):
            monitor.cache_lock(self.root, self.link, self.link.lstat(), legacy)

    def test_directory_lock_target_refused(self):
        self.target.unlink(); self.target.mkdir()
        with self.assertRaisesRegex(Error, 'det_monitor_lock_target_type'):
            monitor.cache_lock(self.root, self.link, self.link.lstat(), legacy)

    def test_hardlinked_lock_target_refused(self):
        os.link(self.target, self.root / 'other-owner')
        with self.assertRaisesRegex(Error, 'det_monitor_lock_target_type'):
            self.bound.directory_usage(self.root)

    def test_replacement_link_refused(self):
        original = self.link.lstat(); self.link.unlink(); self.link.symlink_to(self.target)
        with self.assertRaisesRegex(Error, 'det_monitor_lock_changed'):
            monitor.cache_lock(self.root, self.link, original, legacy)

    def test_special_output_refused(self):
        os.mkfifo(self.root / 'fifo')
        with self.assertRaisesRegex(Error, 'pair_monitor_special_output'):
            self.bound.directory_usage(self.root)

    def test_entry_bound_preserved(self):
        with patch.object(legacy.build_native, 'MAX_OUTPUT_ENTRIES', 1):
            with self.assertRaisesRegex(Error, 'pair_monitor_output_limit'):
                self.bound.directory_usage(self.root)

    def test_locale_guard_preserved(self):
        source = self.root / 'wine/source/nls/locale.nls'; source.parent.mkdir(parents=True)
        source.write_bytes(b'original')
        link = self.root / legacy.LINK; link.parent.mkdir(parents=True); link.symlink_to(legacy.TARGET)
        with patch.object(legacy, 'LOCALE_SHA256', hashlib.sha256(b'original').hexdigest()):
            self.assertGreater(self.bound.directory_usage(self.root), 0)
            source.write_bytes(b'changed')
            with self.assertRaisesRegex(Error, 'pair_monitor_locale_target'):
                self.bound.directory_usage(self.root)

    def test_historical_monitor_still_rejects_cache_alias(self):
        with self.assertRaisesRegex(Error, 'pair_monitor_unlisted_alias'):
            legacy.directory_usage(self.root)
        self.assertIs(legacy.monitored_command.__globals__['directory_usage'], legacy.directory_usage)

    def test_exact_supervisor_runs_with_new_observer(self):
        commands = []
        self.bound.monitored_command(self.root, 'control', [sys.executable, '-I', '-c', 'print("done")'],
            dict(os.environ), {'growth_ceiling_bytes': 1024**2, 'reserve_free_bytes': 0}, commands, timeout=10)
        self.assertEqual(commands[0]['exit_code'], 0)
        self.assertIsNone(commands[0]['stop_reason'])
        self.assertEqual((self.root / 'logs/control/stdout').read_text(), 'done\n')


if __name__ == '__main__':
    unittest.main()
