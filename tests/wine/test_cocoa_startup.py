"""Test the current Wine Cocoa startup lifetime patch with Foundation/CF.

The exact 5,153-byte upstream baseline is redistributed with its original
Ken Thomases/CodeWeavers LGPL-2.1-or-later notice and COPYING.LIB. Its origin is
https://github.com/wine-mirror/wine/blob/4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf/dlls/winemac.drv/cocoa_main.m
Git blob: e80aa93473c8ad3429ab8cbb9f307c809045611d.

Apply the tracked ordered patches, checking every relevant preimage, patch and
postimage hash. The harness includes that resulting source; no private build,
configured Wine headers, signing inputs or retained diagnostic is required.
Foundation condition locks and CF run-loop sources are real. AppKit selectors
and timed-wait outcomes are controlled doubles: no windows, Wine execution,
restricted mode, native faults or launch-readiness qualification are involved.
"""
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = next(parent for parent in Path(__file__).resolve().parents
            if (parent / 'runtime/wine/patches/series.json').is_file())
sys.path.insert(0, str(REPO / 'tests/wine'))
from stage4_source import file_diff, ordinary_file

FIXTURES = REPO / 'tests/wine/fixtures/cocoa_startup'
SOURCE = 'dlls/winemac.drv/cocoa_main.m'
BASE_COMMIT = '4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf'
BASELINE_SHA256 = '041d1dc87bde43a3fcf73124cb6b7e0b4bd4461937d5b1a7fa564fc1f4aeb1da'
LIFETIME_PATCH = '0006a-cocoa-startup-request-lifetime.patch'
SUMMARY_KEYS = {'checks', 'failures', 'active_empty_checks', 'clean_cases',
                'claim_races', 'post_timeout_locks', 'live_requests',
                'live_envelopes', 'live_locks', 'appkit_executed'}
TIMEOUT_MARKER = '    /* A failed timed wait leaves ret at -1.'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def patched_source(root):
    """Use the redistributable baseline and exact current ordered changes."""
    current = ordinary_file(FIXTURES, 'cocoa_main.baseline.m').read_bytes()
    if len(current) != 5153 or sha256(current) != BASELINE_SHA256:
        raise AssertionError('pinned upstream Cocoa baseline changed')
    series = json.loads(ordinary_file(REPO, 'runtime/wine/patches/series.json').read_text())
    if series['base_commit'] != BASE_COMMIT:
        raise AssertionError('unexpected Wine source base')
    selected = [row for row in series['patches'] if row['path'] == LIFETIME_PATCH]
    if len(selected) != 1:
        raise AssertionError('startup lifetime patch must occur exactly once')
    target = root / SOURCE
    target.parent.mkdir(parents=True)
    target.write_bytes(current)
    lifetime_applied = False
    for index, row in enumerate(series['patches']):
        changes = [change for change in row.get('changes', []) if change['path'] == SOURCE]
        if not changes:
            continue
        if len(changes) != 1 or sha256(current) != changes[0]['before_sha256']:
            raise AssertionError('ordered startup preimage mismatch')
        patch = ordinary_file(REPO / 'runtime/wine/patches', row['path']).read_bytes()
        if sha256(patch) != row['sha256']:
            raise AssertionError('tracked startup patch bytes changed')
        selected_patch = root / ('selected-%d.patch' % index)
        selected_patch.write_bytes(file_diff(patch, SOURCE))
        applied = subprocess.run(['/usr/bin/patch', '--batch', '--forward', '--fuzz=0',
                                  '-p1', '-d', str(root), '-i', str(selected_patch)],
                                 capture_output=True, text=True, timeout=15)
        if applied.returncode or re.search(r'\b(offset|fuzz)\b', applied.stdout + applied.stderr, re.I):
            raise AssertionError('startup patch did not apply exactly:\n' + applied.stdout + applied.stderr)
        current = ordinary_file(root, SOURCE).read_bytes()
        if sha256(current) != changes[0]['after_sha256']:
            raise AssertionError('ordered startup postimage mismatch')
        lifetime_applied |= row['path'] == LIFETIME_PATCH
    if not lifetime_applied:
        raise AssertionError('lifetime patch did not change the selected source')
    return current.decode('utf-8')


class CocoaStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if platform.system() != 'Darwin' or platform.machine() != 'arm64':
            raise unittest.SkipTest('startup ownership tests require native macOS ARM64')
        if not shutil.which('xcrun') or not Path('/usr/bin/patch').is_file():
            raise unittest.SkipTest('Apple tool selector or exact patch tool is unavailable')
        selected = subprocess.run(['xcrun', '--find', 'clang'], text=True,
                                  capture_output=True, timeout=15)
        sdk = subprocess.run(['xcrun', '--sdk', 'macosx', '--show-sdk-path'],
                             text=True, capture_output=True, timeout=15)
        if selected.returncode or not Path(selected.stdout.strip()).is_file():
            raise unittest.SkipTest('Apple Clang is unavailable')
        if sdk.returncode or not (Path(sdk.stdout.strip()) / 'usr/include/stdlib.h').is_file():
            raise unittest.SkipTest('Apple macOS SDK headers are unavailable')
        cls.compiler, cls.sdk = selected.stdout.strip(), sdk.stdout.strip()
        cls.directory = tempfile.TemporaryDirectory(prefix='pear-cocoa-startup-')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.root = Path(cls.directory.name)
        cls.source = patched_source(cls.root / 'materialized')

    def run_harness(self, name, source):
        root = self.root / name
        (root / 'after').mkdir(parents=True)
        (root / 'after/cocoa_main.m').write_text(source)
        harness = root / 'startup_harness.m'
        shutil.copyfile(ordinary_file(FIXTURES, 'startup_harness.m'), harness)
        binary = root / 'startup-harness'
        command = [self.compiler, '-std=gnu23', '-arch', 'arm64', '-isysroot', self.sdk,
                   '-Wall', '-Wextra', '-Werror', '-fno-objc-arc',
                   '-fsanitize=undefined', '-fno-sanitize-recover=all',
                   '-I' + str(FIXTURES / 'mocks'), '-framework', 'Foundation',
                   '-framework', 'CoreFoundation', str(harness), '-o', str(binary)]
        built = subprocess.run(command, capture_output=True, text=True, timeout=60)
        self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
        observed = subprocess.run([str(binary)], capture_output=True, timeout=15,
                                  env={'PATH': '/usr/bin:/bin', 'TMPDIR': str(root)})
        self.assertLessEqual(len(observed.stdout), 65536)
        self.assertLessEqual(len(observed.stderr), 65536)
        self.assertEqual(len(observed.stdout.splitlines()), 1, repr(observed.stdout + observed.stderr))
        row = json.loads(observed.stdout)
        self.assertEqual(set(row), SUMMARY_KEYS)
        self.assertIs(row['appkit_executed'], False)
        for key in SUMMARY_KEYS - {'appkit_executed'}:
            self.assertIs(type(row[key]), int)
            self.assertGreaterEqual(row[key], 0)
        for key in ('live_requests', 'live_envelopes', 'live_locks'):
            self.assertEqual(row[key], 0, key)
        return observed, row

    def test_current_patched_source_ownership(self):
        observed, row = self.run_harness('current', self.source)
        self.assertEqual(observed.returncode, 0, repr(observed.stderr))
        self.assertEqual(observed.stderr, b'')
        self.assertGreaterEqual(row['checks'], 429)
        self.assertEqual(row['failures'], 0)
        self.assertEqual(row['active_empty_checks'], 3)
        self.assertEqual(row['clean_cases'], 28)
        self.assertEqual(row['claim_races'], 16)
        self.assertEqual(row['post_timeout_locks'], 0)

    def test_timeout_relock_is_rejected_without_changing_ownership(self):
        self.assertEqual(self.source.count(TIMEOUT_MARKER), 1)
        source = self.source.replace(TIMEOUT_MARKER,
            '    else { [request->lock lock]; [request->lock unlock]; }\n' + TIMEOUT_MARKER)
        observed, row = self.run_harness('timeout-relock', source)
        self.assertEqual(observed.returncode, 1)
        self.assertGreater(row['failures'], 0)
        self.assertGreater(row['post_timeout_locks'], 0)
        self.assertIn(b'timeout cleanup does not reacquire condition', observed.stderr)

    def test_timeout_upgrade_is_rejected_without_changing_ownership(self):
        self.assertEqual(self.source.count(TIMEOUT_MARKER), 1)
        source = self.source.replace(TIMEOUT_MARKER, '    else ret = 0;\n' + TIMEOUT_MARKER)
        observed, row = self.run_harness('timeout-upgrade', source)
        self.assertEqual(observed.returncode, 1)
        self.assertGreater(row['failures'], 0)
        self.assertEqual(row['post_timeout_locks'], 0)
        self.assertIn(b'in-flight timeout remains failure', observed.stderr)


if __name__ == '__main__':
    unittest.main()
