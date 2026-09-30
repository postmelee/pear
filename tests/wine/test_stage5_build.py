"""Build/source identity controls; no Windows or Cocoa execution is implied."""
from pathlib import Path
import hashlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
import build
from common import Error


class Stage5BuildTests(unittest.TestCase):
    def test_changed_native_observer_or_pe_adapter_cannot_match_recorded_fixture(self):
        pairs = [('window_native.m', 'pear_window_fixture.m'),
                 ('window_control_pe.c', 'pear_window_control.c'),
                 ('stage5_protocol.h', 'stage5_protocol.h'),
                 ('stage5_census.h', 'stage5_census.h')]
        with tempfile.TemporaryDirectory() as name:
            source = Path(name)
            driver = source / 'dlls/winemac.drv'
            driver.mkdir(parents=True)
            originals = {original: ('original ' + original).encode() for original, _ in pairs}
            hashes = {name: hashlib.sha256(data).hexdigest() for name, data in originals.items()}
            for original, copied in pairs:
                (driver / copied).write_bytes(originals[original])
            build.verify_stage5_native_fixture(source, hashes)
            for original, copied in pairs:
                with self.subTest(source=original):
                    target = driver / copied
                    target.write_bytes(originals[original] + b'changed')
                    with self.assertRaisesRegex(Error, 'build_stage5_native_fixture_source_mismatch'):
                        build.verify_stage5_native_fixture(source, hashes)
                    target.write_bytes(originals[original])
            del hashes['window_native.m']
            with self.assertRaises(Error):
                build.verify_stage5_native_fixture(source, hashes)

    def test_window_addition_preserves_the_entire_prior_regression_build(self):
        with patch.object(build, 'native_tool', return_value=Path('/usr/bin/clang')):
            previous = build.fixture_commands(Path('/build'), Path('/tools'),
                {'sdk': {'path': '/sdk'}}, build.STAGE4_SUITE, 'page-wx')
            current = build.fixture_commands(Path('/build'), Path('/tools'),
                {'sdk': {'path': '/sdk'}}, build.STAGE5_SUITE, 'page-wx')
        self.assertEqual({key: current[key] for key in previous}, previous)
        argv = current['fixture-window-arm64']
        self.assertIn('--target=aarch64-w64-windows-gnu', argv)
        self.assertIn('-luser32', argv)
        self.assertIn('-nostdlib', argv)
        self.assertNotIn('-Wl,--allow-multiple-definition', argv)
        self.assertEqual(build.fixture_pe_outputs(build.STAGE5_SUITE, 'page-wx'), {
            **build.fixture_pe_outputs(build.STAGE4_SUITE, 'page-wx'),
            'libexec/pear-stage5/window-arm64.exe': 0xaa64})


if __name__ == '__main__':
    unittest.main()
