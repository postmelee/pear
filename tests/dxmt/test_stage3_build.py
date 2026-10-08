"""Original Stage 3 ownership/configuration controls; no compiler or guest."""
import ast
import configparser
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/dxmt'))
from common import Error, digest
_spec = importlib.util.spec_from_file_location('_pear_dxmt_stage3_builder_tests', ROOT / 'tools/dxmt/build.py')
builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(builder)


class Stage3BuildControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pear-dxmt-stage3-unit-')
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def test_cross_configuration_selects_hybrid_without_a_guest_wrapper(self):
        parser = configparser.ConfigParser()
        parser.read_string(builder.cross_file(self.root / 'cross tools').decode())
        self.assertEqual(parser['host_machine']['cpu_family'], "'aarch64'")
        self.assertEqual(parser['host_machine']['system'], "'windows'")
        self.assertEqual(parser['properties']['needs_exe_wrapper'], 'true')
        self.assertNotIn('exe_wrapper', parser['binaries'])
        for key in ['c_args', 'cpp_args', 'c_link_args', 'cpp_link_args']:
            self.assertEqual(ast.literal_eval(parser['built-in options'][key]), ['-marm64x'])
        c = ast.literal_eval(parser['binaries']['c'])
        self.assertEqual(c[:2], ['/usr/bin/arch', '-arm64'])
        self.assertTrue(c[-1].endswith('/cross tools/llvm-mingw/bin/arm64ec-w64-mingw32-gcc'))

    @unittest.skipUnless(Path('/bin/sh').is_file(), 'requires an ordinary shell')
    def test_version_adapter_refuses_ambient_repository_operations(self):
        commit = 'a' * 40
        path = self.root / 'git'
        path.write_bytes(builder.version_adapter(commit))
        good = subprocess.run(['/bin/sh', str(path), 'describe', '--always'],
                              capture_output=True, timeout=5)
        self.assertEqual((good.returncode, good.stdout, good.stderr), (0, (commit+'\n').encode(), b''))
        for args in [[], ['--version'], ['describe', '--always', 'HEAD'], ['rev-parse', 'HEAD']]:
            with self.subTest(args=args):
                result = subprocess.run(['/bin/sh', str(path), *args], capture_output=True, timeout=5)
                self.assertEqual(result.returncode, 64)
                self.assertEqual(result.stdout, b'')

    def test_version_adapter_rejects_noncommit_injection(self):
        for value in ['a' * 39, 'G' * 40, "'" * 40, 'a' * 39 + '\n']:
            with self.subTest(value=value):
                with self.assertRaises(Error):
                    builder.version_adapter(value)

    def test_generated_input_bytes_and_modes_are_replayed(self):
        expected = {'bin/adapter': (b'original data\n', 0o755)}
        builder.write_bytes(self.root, 'bin/adapter', *expected['bin/adapter'])
        original = builder.generated_facts(self.root, expected)
        self.assertEqual(original[0]['sha256'], digest(b'original data\n'))
        path = self.root / 'bin/adapter'
        path.chmod(0o644)
        with self.assertRaises(Error):
            builder.generated_facts(self.root, expected)
        path.chmod(0o755)
        path.write_bytes(b'changed data\n')
        with self.assertRaises(Error):
            builder.generated_facts(self.root, expected)

    def test_creation_refuses_an_intermediate_output_alias(self):
        target = self.root / 'other'
        target.mkdir()
        (self.root / 'bin').symlink_to(target, target_is_directory=True)
        with self.assertRaises((Error, OSError)):
            builder.write_bytes(self.root, 'bin/new-file', b'owned output')
        self.assertFalse((target / 'new-file').exists())

    def test_generated_input_intermediate_alias_is_refused(self):
        target = self.root / 'other'
        target.mkdir()
        (target / 'adapter').write_bytes(b'original')
        (self.root / 'bin').symlink_to(target, target_is_directory=True)
        with self.assertRaises((Error, OSError)):
            builder.generated_facts(self.root, {'bin/adapter': (b'original', 0o644)})

    def test_role_copy_preserves_owned_origin_and_refuses_changes(self):
        native = self.root / 'native'
        source = native / 'install/bin'
        source.mkdir(parents=True)
        (source / 'winebuild').write_bytes(b'Original owned fixture')
        out = self.root / 'out'
        out.mkdir()
        row = {'path': 'wine-layout/bin/winebuild', 'origin_role': 'native',
               'origin_path': 'bin/winebuild', 'sha256': digest(b'Original owned fixture'),
               'size_bytes': len(b'Original owned fixture'), 'mode': 0o755}
        builder.copy_layout(out, [row], {'native': native})
        path = out / row['path']
        self.assertEqual(path.read_bytes(), b'Original owned fixture')
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o755)
        (source / 'winebuild').write_bytes(b'Changed')
        other = self.root / 'another'
        other.mkdir()
        with self.assertRaises(Error):
            builder.copy_layout(other, [row], {'native': native})
        self.assertFalse((other / row['path']).exists())

    def test_failed_attempt_cannot_be_promoted_to_artifact_build(self):
        repo = self.root / 'repo'
        output = repo / '.build/task7/failed'
        output.mkdir(parents=True)
        (output / 'failed.json').write_text('{}')
        (output / 'build.json').write_text(json.dumps({'passed': True, 'dxmt_built': True}))
        with self.assertRaises(Error) as error:
            builder.verify_build(output, repo=repo)
        self.assertEqual(error.exception.code, 'failed_artifact_build')

    def test_unknown_or_duplicate_role_selector_is_refused(self):
        repo = self.root / 'repo'
        owned = repo / '.build/task7/role-selection'
        owned.mkdir(parents=True)
        native = self.root / 'native'
        native.mkdir()
        companion = self.root / 'companion'
        companion.mkdir()
        cross = self.root / 'cross'
        cross.mkdir()
        p = owned / 'roles.json'
        value = {'schema_version':1, 'record_kind':'dxmt_wine_role_selection', 'scope':'dxmt_component',
                 'native':str(native), 'companion':str(companion), 'cross_tools':str(cross)}
        p.write_text(json.dumps(value))
        self.assertEqual(builder.selector(p, repo)[1]['native'], native)
        value['companion'] = value['native']
        p.write_text(json.dumps(value))
        with self.assertRaises(Error):
            builder.selector(p, repo)
        value['companion'] = str(companion)
        value['unexpected'] = 'not admitted'
        p.write_text(json.dumps(value))
        with self.assertRaises(Error):
            builder.selector(p, repo)
        p.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaises(Error):
            builder.selector(p, repo)


if __name__ == '__main__':
    unittest.main()
