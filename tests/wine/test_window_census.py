"""Bounded ownership diagnostics, separate from Wine execution qualification.

The portable ledger exercises actual mutex-protected state transitions. The
Darwin source test executes the selected Wine C event/query ownership functions
against ordinary Foundation objects; it creates no AppKit windows and does not
enter restricted mode. Retained generated headers are compiler dependencies,
not newly qualified build artifacts.
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


class WindowCensusLedgerTests(unittest.TestCase):
    def test_bounded_concurrent_ledger_and_incomplete_observations(self):
        compiler = shutil.which('clang')
        if compiler is None:
            self.skipTest('Clang is unavailable for the ordinary C ledger test')
        with tempfile.TemporaryDirectory(prefix='pear-window-census-') as directory:
            root = Path(directory)
            shutil.copyfile(REPO / 'tests/wine/fixtures/stage5_census.h', root / 'stage5_census.h')
            harness = REPO / 'tests/wine/window_census_harness.c'
            binary = root / 'ledger'
            command = [compiler, '-std=c11', '-Wall', '-Wextra', '-Werror',
                       '-fsanitize=undefined', '-fno-sanitize-recover=all', '-pthread',
                       '-I' + str(root), str(harness), '-o', str(binary)]
            built = subprocess.run(command, capture_output=True, text=True, timeout=60)
            self.assertEqual(built.returncode, 0, built.stderr)
            ran = subprocess.run([str(binary)], capture_output=True, text=True, timeout=20)
            self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr)
            row = json.loads(ran.stdout)
            self.assertEqual(row['failed'], 0)
            self.assertGreaterEqual(row['checks'], 520)
            self.assertIs(row['wine_executed'], False)
            self.assertIs(row['restricted_mode_executed'], False)


class WindowCensusSourceLifetimeTests(unittest.TestCase):
    def test_actual_event_query_and_indirect_focus_ownership(self):
        if platform.system() != 'Darwin' or platform.machine() != 'arm64':
            self.skipTest('Foundation source lifetime test requires native Darwin ARM64')
        if shutil.which('xcrun') is None:
            self.skipTest('Apple compiler selector is unavailable')
        compiler = subprocess.run(['xcrun', '--find', 'clang'], capture_output=True, text=True, timeout=15)
        sdk = subprocess.run(['xcrun', '--sdk', 'macosx', '--show-sdk-path'], capture_output=True, text=True, timeout=15)
        if compiler.returncode or not Path(compiler.stdout.strip()).is_file():
            self.skipTest('Apple Clang is unavailable')
        if sdk.returncode or not (Path(sdk.stdout.strip()) / 'usr/include/stdlib.h').is_file():
            self.skipTest('Apple SDK headers are unavailable')
        objects, headers = configured_headers()
        source = materialize('dlls/winemac.drv/cocoa_event.m')
        first = source.index('macdrv_event* macdrv_create_event(')
        end = source.index('/***********************************************************************\n *              macdrv_set_query_done', first)
        bind = source.index('        pear_stage5_census_object(PEAR_S5_CENSUS_QUERY,PEAR_S5_CENSUS_BIND,')
        bind_end = source.index(';', bind) + 1
        with tempfile.TemporaryDirectory(prefix='pear-window-census-source-') as directory:
            root = Path(directory)
            for name in ('macdrv.h', 'unixlib.h', 'macdrv_cocoa.h', 'macdrv_res.h',
                         'cocoa_window.h', 'cocoa_event.h', 'cocoa_app.h'):
                (root / name).write_text(materialize('dlls/winemac.drv/' + name))
            shutil.copyfile(REPO / 'tests/wine/fixtures/stage5_census.h', root / 'stage5_census.h')
            (root / 'event_lifetime_source.inc').write_text(source[first:end])
            (root / 'query_bind_source.inc').write_text(source[bind:bind_end] + '\n')
            harness = REPO / 'tests/wine/window_census_lifetime_harness.m'
            binary = root / 'lifetime'
            command = [compiler.stdout.strip(), '-std=gnu23', '-arch', 'arm64',
                       '-isysroot', sdk.stdout.strip(), '-D__WINESRC__', '-DWINE_UNIX_LIB',
                       '-Wall', '-Wextra', '-Werror', '-Wno-unused-function',
                       '-Wno-deprecated-declarations', '-Wno-nonnull',
                       '-fsanitize=undefined', '-fno-sanitize-recover=all',
                       '-fno-stack-protector', '-fno-strict-aliasing', '-fvisibility=hidden',
                       '-U_FORTIFY_SOURCE', '-D_FORTIFY_SOURCE=0',
                       '-I' + str(root), '-I' + str(objects), '-I' + str(headers),
                       str(harness), '-framework', 'Foundation', '-o', str(binary)]
            built = subprocess.run(command, capture_output=True, text=True, timeout=60)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            ran = subprocess.run([str(binary)], capture_output=True, text=True, timeout=20)
            self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr)
            row = json.loads(ran.stdout)
            self.assertEqual((row['checks'], row['failed']), (9, 0))
            self.assertEqual((row['objects_deallocated'], row['terminal_observations']), (4, 5))
            for key in ('wine_executed', 'cocoa_windows_created', 'restricted_mode_executed'):
                self.assertIs(row[key], False)


if __name__ == '__main__':
    unittest.main()
