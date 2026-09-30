"""Source-bound finite observer checks with synthetic Wine/Cocoa operations.

An ordinary Foundation object exercises deallocation; no AppKit window, Wine
runtime or restricted x18 operation is executed. Retained generated headers are
compiler dependencies, not independently qualified historical build evidence.
"""
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = next(parent for parent in Path(__file__).resolve().parents
            if (parent / 'runtime/wine/patches/series.json').is_file())
sys.path.insert(0, str(REPO / 'tests/wine'))
from stage4_source import configured_headers, materialize


class WindowObserverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if platform.system() != 'Darwin' or platform.machine() != 'arm64':
            raise unittest.SkipTest('synthetic observer requires native Darwin ARM64')
        if not shutil.which('xcrun'):
            raise unittest.SkipTest('Apple compiler selector is unavailable')
        selected = subprocess.run(['xcrun', '--find', 'clang'], text=True,
                                  capture_output=True, timeout=15)
        sdk = subprocess.run(['xcrun', '--sdk', 'macosx', '--show-sdk-path'],
                             text=True, capture_output=True, timeout=15)
        if selected.returncode or not Path(selected.stdout.strip()).is_file():
            raise unittest.SkipTest('Apple Clang is unavailable')
        if sdk.returncode or not (Path(sdk.stdout.strip()) / 'usr/include/stdlib.h').is_file():
            raise unittest.SkipTest('Apple SDK headers are unavailable')
        objects, headers = configured_headers()
        cls.directory = tempfile.TemporaryDirectory(prefix='pear-window-observer-')
        cls.addClassCleanup(cls.directory.cleanup)
        root = Path(cls.directory.name)
        for name in ('macdrv.h', 'unixlib.h', 'macdrv_cocoa.h', 'macdrv_res.h',
                     'cocoa_window.h', 'cocoa_event.h', 'cocoa_app.h'):
            (root / name).write_text(materialize('dlls/winemac.drv/' + name))
        (root / 'wine').mkdir()
        (root / 'wine/pear_bootstrap.h').write_text(materialize('include/wine/pear_bootstrap.h'))
        for name in ('window_native.m', 'stage5_protocol.h', 'stage5_census.h'):
            shutil.copyfile(REPO / 'tests/wine/fixtures' / name, root / name)
        harness = Path(__file__).with_name('window_observer_harness.m')
        shutil.copyfile(harness, root / harness.name)
        binary = root / 'window-observer'
        command = [selected.stdout.strip(), '-std=gnu23', '-arch', 'arm64',
                   '-isysroot', sdk.stdout.strip(), '-D__WINESRC__', '-DWINE_UNIX_LIB',
                   '-Wall', '-Werror', '-Wno-deprecated-declarations', '-Wno-nonnull',
                   '-fno-stack-protector', '-fno-strict-aliasing', '-fvisibility=hidden',
                   '-U_FORTIFY_SOURCE', '-D_FORTIFY_SOURCE=0',
                   '-fsanitize=undefined', '-fno-sanitize-recover=all',
                   '-I' + str(root), '-I' + str(objects), '-I' + str(headers),
                   str(root / harness.name), '-framework', 'Foundation', '-o', str(binary)]
        built = subprocess.run(command, text=True, capture_output=True, timeout=60)
        if built.returncode:
            raise AssertionError('synthetic observer compile failed:\n' + built.stdout + built.stderr)
        ran = subprocess.run([str(binary)], capture_output=True, timeout=20,
                             env={'PATH': '/usr/bin:/bin', 'TMPDIR': str(root)})
        if ran.returncode:
            raise AssertionError('synthetic observer checks failed: ' + repr(ran.stdout + ran.stderr))
        diagnostic_rows = [json.loads(line) for line in ran.stderr.splitlines()]
        census = [row for row in diagnostic_rows if row['record_kind'] == 'pear_stage5_census']
        if len(census) % 5:
            raise AssertionError('incomplete private ownership census')
        cls.census = []
        for index in range(0, len(census), 5):
            merged = {}
            for part, row in enumerate(census[index:index + 5], 1):
                if row['part'] != part or row['cycle'] != census[index]['cycle'] or row['attempt'] != census[index]['attempt']:
                    raise AssertionError('misordered census parts')
                merged.update(row)
            cls.census.append(merged)
        cls.dealloc_entries = [row for row in diagnostic_rows if row['record_kind'] == 'pear_stage5_dealloc_enter']
        parts = [row for row in diagnostic_rows if row['record_kind'] == 'pear_stage5_ownership']
        if len(parts) % 3:
            raise AssertionError('incomplete private diagnostic snapshot')
        cls.diagnostics = []
        for index in range(0, len(parts), 3):
            merged = {}
            for part, row in enumerate(parts[index:index + 3], 1):
                if row['part'] != part or row['cycle'] != parts[index]['cycle'] or row['attempt'] != parts[index]['attempt']:
                    raise AssertionError('misordered diagnostic parts')
                merged.update(row)
            cls.diagnostics.append(merged)
        if any(len(line) >= 512 for line in ran.stderr.splitlines()):
            raise AssertionError('diagnostic line exceeds atomic write bound')
        cls.lines = ran.stdout.splitlines()
        cls.rows = [json.loads(line) for line in cls.lines]
        cls.events, cls.summary = cls.rows[:-1], cls.rows[-1]

    def test_native_state_and_negative_controls(self):
        self.assertEqual(self.summary['record_kind'], 'synthetic_window_observer')
        self.assertGreaterEqual(self.summary['checks'], 340)
        self.assertEqual(self.summary['failed'], 0)
        for key in ('wine_executed', 'cocoa_windows_created', 'restricted_mode_executed'):
            self.assertIs(self.summary[key], False)

    def test_pending_ownership_diagnostics_are_bounded_and_not_completion(self):
        self.assertEqual(len(self.dealloc_entries), 25)
        self.assertEqual(len(self.diagnostics), 3)
        self.assertEqual([row['attempt'] for row in self.diagnostics], [1, 1, 100])
        for row in self.diagnostics:
            self.assertEqual(row['record_kind'], 'pear_stage5_ownership')
            self.assertEqual((row['cycle'], row['main_thread'], row['close_observer_hits']), (1, 1, 1))
            self.assertEqual(row['deallocated'], 0)
            self.assertEqual(row['clock_ok'], 1)
            self.assertGreaterEqual(row['elapsed_us'], 0)
        self.assertEqual(self.diagnostics[1]['elapsed_us'], 0)
        self.assertGreaterEqual(self.diagnostics[2]['elapsed_us'], self.diagnostics[1]['elapsed_us'])
        for row in self.diagnostics[1:]:
            # A cleared fd can coexist with an unmatched queued event and a
            # containing event frame. Diagnostics must not convert that to pass.
            self.assertEqual(row['fd_empty'], 1)
            self.assertEqual((row['queue_total'], row['queue_target'], row['queue_target_event_refs']), (1, 1, 2))
            self.assertEqual((row['wine_event_present'], row['wine_event_target'], row['wine_event_refs']), (1, 1, 1))
            self.assertEqual(row['queue_matches'], 1)

    def test_census_declares_its_epoch_and_ownership_limits(self):
        self.assertEqual([row['attempt'] for row in self.census], [1, 1, 100])
        for row in self.census:
            self.assertEqual((row['epoch_only'], row['direct_targets_only']), (1, 1))
            self.assertEqual((row['marker_submitted'], row['marker_completed']), (1, 1))
            self.assertEqual((row['draw_order_valid'], row['ledger_complete']), (1, 1))
            self.assertEqual((row['allocations'], row['events_live'], row['queries_live']), (0, 0, 0))
            self.assertNotIn('draw_completed', row)
            self.assertEqual(row['draw_body_completed'], 0)

    def test_fixed_bounded_parts_and_lifecycle(self):
        fields = {1: {'hwnd', 'window', 'token'}, 2: {'thread_id', 'main', 'mode', 'value'},
                  3: {'driver_base', 'driver_entry', 'teb', 'native_tid'}}
        phases = []
        position = 0
        while position < len(self.events):
            first = self.events[position]
            self.assertEqual(first['seq'], len(phases) + 1)
            count = 3 if first['phase'] == 0 else 2
            for part in range(1, count + 1):
                row = self.events[position + part - 1]
                self.assertEqual(set(row), {'event', 'seq', 'cycle', 'phase', 'part'} | fields[part])
                self.assertEqual(row['event'], 'stage5_window')
                self.assertEqual(row['part'], part)
                for key in ('seq', 'cycle', 'phase'):
                    self.assertEqual(row[key], first[key])
                for key in set(row) - {'event'}:
                    self.assertIs(type(row[key]), int)
                    self.assertGreaterEqual(row[key], 0)
                detail = self.lines[position + part - 1][len(b'{"event":"stage5_window"'):-1]
                self.assertLessEqual(len(detail), 220)
            phases.append({**first, **self.events[position + 1]})
            position += count
        self.assertEqual((phases[0]['phase'], phases[-1]['phase']), (0, 16))
        for cycle in range(1, 21):
            own = [row for row in phases if row['cycle'] == cycle]
            self.assertEqual((own[0]['phase'], own[-1]['phase']), (1, 15))
            self.assertEqual(sum(row['phase'] == 12 for row in own), 1)
            for phase in (17, 18):
                self.assertEqual(sum(row['phase'] == phase for row in own), 1)
                turn = next(row for row in own if row['phase'] == phase)
                self.assertEqual(turn['value'], (0x505335 << 24) | (cycle << 8) | 1)
            consumed = next(row['seq'] for row in own if row['phase'] == 18)
            last_barrier = max(row['seq'] for row in own if row['phase'] == 13)
            self.assertGreater(last_barrier, consumed)
            self.assertTrue(all(row['token'] == 0x53350000 + cycle for row in own))
        self.assertEqual(len(self.events), 773)

    def test_actual_queue_result_controls_completion(self):
        values = [row['value'] for row in self.events if row['phase'] == 14 and row['part'] == 2]
        # First drain still owns the object; the second has deallocated it but
        # still reports a nonempty queue. Only the third may complete cycle 1.
        self.assertEqual(values[:3], [30, 46, 63])
        self.assertEqual(values[3:], [31, 47] * 19)
        final_samples = [row['value'] for row in self.events if row['phase'] == 19 and row['part'] == 2]
        self.assertEqual(final_samples, [14, 15])
        callbacks = [row['value'] for row in self.events if row['phase'] == 8 and row['part'] == 2]
        self.assertEqual(callbacks, [(0x53350000 + i) ^ 0x13579bdf for i in range(1, 21)])


if __name__ == '__main__':
    unittest.main()
