"""Exercise the real observer with synthetic Darwin contexts and a private pipe.

These tests do not deliver signals, enter restricted mode, execute Wine, or
qualify the generated headers retained from a previous local Wine build.
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

HEADER_FIELDS = {'version', 'role', 'event', 'nonce', 'pid', 'ppid',
                 'start_sec', 'start_usec', 'generation', 'identity_error'}
REGISTER_FIELDS = ('teb', 'native_tid', 'ntdll_base', 'guest_begin', 'guest_end',
                   'host_begin', 'host_end', 'init_seen', 'init_host_mode',
                   'init_tls_matches')
SIGNAL_FIELDS = ('teb', 'native_tid', 'ntdll_base', 'guest_begin', 'guest_end',
                 'host_begin', 'host_end', 'before_count', 'after_count', 'signal',
                 'entry_mode', 'handler_mode', 'return_mode', 'before_pc',
                 'after_pc', 'before_x18', 'after_x18', 'before_x19', 'after_x19',
                 'before_sp', 'after_sp', 'error')
MAXIMUM = 2**64 - 1


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('duplicate JSON key: ' + key)
        value[key] = item
    return value


class SignalObserverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if platform.system() != 'Darwin' or platform.machine() != 'arm64':
            raise unittest.SkipTest('synthetic observer requires a native Darwin ARM64 compiler host')
        if not shutil.which('xcrun'):
            raise unittest.SkipTest('Apple compiler selection tool is unavailable')
        selected = subprocess.run(['xcrun', '--find', 'clang'], capture_output=True,
                                  text=True, timeout=15)
        if selected.returncode or not Path(selected.stdout.strip()).is_file():
            raise unittest.SkipTest('Apple Clang is unavailable')
        sdk = subprocess.run(['xcrun', '--sdk', 'macosx', '--show-sdk-path'],
                             capture_output=True, text=True, timeout=15)
        if sdk.returncode or not (Path(sdk.stdout.strip()) / 'usr/include/stdlib.h').is_file():
            raise unittest.SkipTest('Apple macOS SDK headers are unavailable')
        objects, source_headers = configured_headers()
        cls.directory = tempfile.TemporaryDirectory(prefix='pear-observer-unit-')
        cls.addClassCleanup(cls.directory.cleanup)
        root = Path(cls.directory.name)
        # The checked series supplies these private interfaces. Only generated
        # configuration and ordinary include dependencies come from old headers.
        for relative, output in (
                ('dlls/ntdll/unix/unix_private.h', 'unix_private.h'),
                ('dlls/ntdll/unixlib.h', 'unixlib.h'),
                ('include/wine/pear_bootstrap.h', 'wine/pear_bootstrap.h')):
            target = root / output
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(materialize(relative))
        fixtures = REPO / 'tests/wine/fixtures'
        for name in ('signal_native.c', 'stage4_protocol.h'):
            source = fixtures / name
            if not source.is_file():
                raise AssertionError('tracked observer fixture is missing: ' + name)
            shutil.copyfile(source, root / name)
        harness = Path(__file__).with_name('signal_observer_harness.c')
        shutil.copyfile(harness, root / harness.name)
        binary = root / 'observer-control'
        command = [selected.stdout.strip(), '-isysroot', sdk.stdout.strip(),
                   '-arch', 'arm64', '-std=gnu23', '-O1',
                   '-fsanitize=undefined', '-fno-sanitize-recover=all',
                   '-Wall', '-Werror', '-fno-stack-protector',
                   '-I' + str(root), '-I' + str(objects), '-I' + str(source_headers),
                   '-D__WINESRC__', '-DFAR=', '-DZ_SOLO', '-D_NTSYSTEM_',
                   '-D_ACRTIMP=', '-DWINBASEAPI=', '-DPEAR_NATIVE_PE_PUBLICATION=1',
                   '-DWINE_UNIX_LIB', str(root / harness.name), '-o', str(binary)]
        compiled = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if compiled.returncode:
            raise AssertionError('observer unit compilation failed:\n' + compiled.stdout + compiled.stderr)
        # No inherited Pear descriptors, signing state, or execution variables.
        completed = subprocess.run([str(binary)], capture_output=True, timeout=15,
                                   env={'PATH': '/usr/bin:/bin', 'TMPDIR': str(root)})
        if completed.returncode or completed.stderr:
            raise AssertionError('observer synthetic checks failed:\n' + repr(completed.stderr))
        cls.lines = completed.stdout.splitlines(keepends=True)
        cls.rows = [json.loads(line, object_pairs_hook=unique_object) for line in cls.lines]
        if len(cls.rows) != 14:
            raise AssertionError('expected 12 native parts and two harness summaries')
        cls.events = cls.rows[:12]

    def test_synthetic_context_checks(self):
        self.assertEqual(self.rows[-1], {
            'synthetic_observer_checks': 44, 'passed': True,
            'signal_delivery_performed': False, 'restricted_mode_performed': False})

    def test_fixed_record_parts(self):
        for rows, event, names, control in (
                (self.events[:4], 'stage4_thread_register', REGISTER_FIELDS, {'slot', 'part'}),
                (self.events[4:], 'stage4_signal', SIGNAL_FIELDS, {'slot', 'phase', 'part'})):
            for part, row in enumerate(rows):
                with self.subTest(event=event, part=part):
                    self.assertEqual(row['event'], event)
                    self.assertEqual(row['part'], part)
                    self.assertEqual(row['slot'], 0)
                    self.assertEqual(set(row), HEADER_FIELDS | control | set(names[3*part:3*part+3]))
                    if event == 'stage4_signal':
                        self.assertEqual(row['phase'], 3)

    def test_unsigned_values_survive_parts(self):
        for rows, names in ((self.events[:4], REGISTER_FIELDS), (self.events[4:], SIGNAL_FIELDS)):
            for part, row in enumerate(rows):
                for name in names[3*part:3*part+3]:
                    with self.subTest(part=part, name=name):
                        self.assertIs(type(row[name]), int)
                        if name in ('host_begin', 'host_end'):
                            self.assertTrue(0 < row[name] <= MAXIMUM)
                        else:
                            self.assertEqual(row[name], MAXIMUM)
        self.assertEqual(self.events[1]['host_begin'], self.events[5]['host_begin'])
        self.assertEqual(self.events[2]['host_end'], self.events[6]['host_end'])
        self.assertLess(self.events[1]['host_begin'], self.events[2]['host_end'])

    def test_private_pipe_headers(self):
        identity = {name: self.events[0][name] for name in ('pid', 'ppid', 'start_sec', 'start_usec')}
        for row in self.events:
            self.assertEqual(row['version'], 1)
            self.assertEqual(row['role'], 'loader')
            self.assertEqual(row['nonce'], '0123456789abcdef0123456789abcdef')
            self.assertEqual(row['generation'], 0)
            self.assertEqual(row['identity_error'], 0)
            self.assertEqual({name: row[name] for name in identity}, identity)
            for name, value in identity.items():
                self.assertIs(type(value), int)
                self.assertGreaterEqual(value, 0 if name == 'start_usec' else 1)
            self.assertLess(row['start_usec'], 1000000)

    def test_atomic_pipe_line_bound(self):
        maximum = max(len(line) for line in self.lines[:12])
        self.assertLessEqual(maximum, 472)
        self.assertTrue(all(line.endswith(b'\n') for line in self.lines))
        self.assertEqual(self.rows[-2], {'native_part_rows': 12, 'maximum_line_bytes': maximum})


if __name__ == '__main__':
    unittest.main()
