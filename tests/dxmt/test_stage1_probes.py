"""Original metadata-probe fixtures exercise replay without native tool runs."""
import copy
from pathlib import Path
import struct
import unittest
from unittest.mock import patch
from support import Fixture
from common import Error, MACH_ARM64, digest
import check
import verify


class Probes(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.addCleanup(self.f.close)
        self.root = self.f.root / 'probe-fixtures'
        self.root.mkdir()
        (self.root / 'probe-logs').mkdir()
        self.toolchain = {'native_tool_paths': {'git': '/fixture/git', 'python': '/fixture/python',
                          'xcrun': '/fixture/xcrun', 'xxd': '/fixture/xxd'}, 'sdk': {'version': '26.5', 'path': str(self.root / 'original-sdk')}}
        Path(self.toolchain['sdk']['path']).mkdir()
        self.roots = {'tools': '/fixture/cross'}
        rows = [{'id': n, 'status': 'unavailable', 'path': None, 'capability': 'unperformed', 'candidate_acquired': False}
                for n in ['cmake', 'meson', 'ninja', 'metal', 'metallib']]
        xcrun = self.toolchain['native_tool_paths']['xcrun']
        specifications = [('git', ['/fixture/git', '--version'], b'git version fixture\n', 0),
                          ('python', ['/fixture/python', '--version'], b'Python 3.13.0\n', 0),
                          ('sdk-version', [xcrun, '--sdk', 'macosx', '--show-sdk-version'], b'26.5\n', 0),
                          ('sdk-path', [xcrun, '--sdk', 'macosx', '--show-sdk-path'], (self.toolchain['sdk']['path'] + '\n').encode(), 0),
                          ('metal-resolution', [xcrun, '--sdk', 'macosx', '--find', 'metal'], b'', 1),
                          ('metallib-resolution', [xcrun, '--sdk', 'macosx', '--find', 'metallib'], b'', 1)]
        for name in ['arm64ec-w64-mingw32-gcc', 'arm64ec-w64-mingw32-g++', 'clang-23']:
            specifications.append((name + '-version', ([('/bin/sh')] if name != 'clang-23' else []) + ['/fixture/cross/llvm-mingw/bin/' + name, '--version'], b'clang version 23.1.1\n', 0))
        commands = []
        for name, argv, stdout, code in specifications:
            cmd = {'id': name, 'argv': ['/usr/bin/arch', '-arm64', *argv], 'exit_code': code,
                   'timed_out': False, 'output_limit': False, 'elapsed_ms': 1}
            for stream, data in [('stdout', stdout), ('stderr', b'')]:
                path = 'probe-logs/' + name + '.' + stream
                (self.root / path).write_bytes(data)
                cmd[stream] = {'path': path, 'sha256': digest(data), 'size_bytes': len(data)}
            commands.append(cmd)
        self.value = {'commands': commands, 'tools': rows, 'cross_tools': {'selected_tools': [
            {'id': name, 'kind': 'shell_wrapper', 'interpreter': '/bin/sh', 'native_wrapper_target': 'clang',
             'wrapper_driver': {'kind': 'macho', 'resolved_path': 'bin/clang-23'}}
            for name in ['arm64ec-w64-mingw32-gcc', 'arm64ec-w64-mingw32-g++']] + [{'id': 'clang-23', 'kind': 'macho'}]}}

    def replay(self):
        with patch('verify.shutil.which', return_value=None):
            verify.verify_probe_evidence(self.value, self.root, self.toolchain, self.roots)

    def test_explicit_missing_metallib_is_valid_accounted_probe_evidence(self):
        self.replay()

    def test_metal_resolution_uses_its_own_stdout(self):
        metal = self.root / 'original-metal-path-fixture'
        metal.write_bytes(b'original resolution fixture')
        cmd = next(c for c in self.value['commands'] if c['id'] == 'metal-resolution')
        raw = (str(metal) + '\n').encode()
        (self.root / cmd['stdout']['path']).write_bytes(raw)
        cmd['stdout'].update(sha256=digest(raw), size_bytes=len(raw))
        cmd['exit_code'] = 0
        self.value['tools'][3].update(status='resolved_unverified', path=str(metal))
        self.replay()

    def test_changed_probe_bytes_are_refused(self):
        (self.root / self.value['commands'][0]['stdout']['path']).write_bytes(b'changed\n')
        with self.assertRaisesRegex(Error, 'probe_log_changed'):
            self.replay()

    def test_omitted_arm64_request_is_refused(self):
        self.value['commands'][0]['argv'] = ['/fixture/git', '--version']
        with self.assertRaisesRegex(Error, 'probe_native_request'):
            self.replay()

    def test_reported_timeout_is_refused(self):
        self.value['commands'][0]['timed_out'] = True
        with self.assertRaisesRegex(Error, 'probe_outcome'):
            self.replay()

    def test_probe_sdk_mismatch_is_refused(self):
        self.toolchain['sdk']['version'] = '25.0'
        with self.assertRaisesRegex(Error, 'sdk_version_changed'):
            self.replay()

    def test_false_metal_available_claim_is_refused(self):
        self.value['tools'][3].update(status='resolved_unverified', path='/invented/tool')
        with self.assertRaisesRegex(Error, 'metal_resolution_claim'):
            self.replay()

    def test_same_version_different_sdk_directory_is_refused(self):
        other = self.root / 'other-sdk'
        other.mkdir()
        self.toolchain['sdk']['path'] = str(other)
        with self.assertRaisesRegex(Error, 'sdk_path_changed'):
            self.replay()

    def test_sdk_alias_is_compared_by_actual_resolved_directory(self):
        alias = self.root / 'sdk-alias'
        alias.symlink_to(self.toolchain['sdk']['path'])
        self.toolchain['sdk']['path'] = str(alias)
        self.replay()

    def test_omitted_sdk_path_probe_is_refused(self):
        self.value['commands'] = [c for c in self.value['commands'] if c['id'] != 'sdk-path']
        with self.assertRaisesRegex(Error, 'probe_set'):
            self.replay()

    def test_inspected_wrapper_requires_explicit_native_shell_argv(self):
        cmd = next(c for c in self.value['commands'] if c['id'] == 'arm64ec-w64-mingw32-gcc-version')
        self.assertEqual(cmd['argv'][:3], ['/usr/bin/arch', '-arm64', '/bin/sh'])
        cmd['argv'].remove('/bin/sh')
        with self.assertRaisesRegex(Error, 'probe_native_request'):
            self.replay()

    def cache_fixture(self):
        install = self.root / 'original-cache'
        (install / 'bin').mkdir(parents=True)
        clang = install / 'bin/clang-23'
        clang.write_bytes(b'\xcf\xfa\xed\xfe' + struct.pack('<I', MACH_ARM64) + b'\0' * 24)
        clang.chmod(0o755)
        script = install / 'bin/original-wrapper.sh'
        script.write_bytes(b'#!/bin/sh\nCLANG="$DIR/clang"\n# Original fixture; never executed.\n')
        script.chmod(0o755)
        (install / 'bin/clang').symlink_to('clang-23')
        (install / 'bin/arm64ec-w64-mingw32-gcc').symlink_to('original-wrapper.sh')
        files = {}
        for path in [clang, script]:
            files[path.relative_to(install).as_posix()] = {'sha256': digest(path.read_bytes()), 'size_bytes': path.stat().st_size, 'mode': 0o755}
        files.update({'bin/clang': {'symlink': 'clang-23'}, 'bin/arm64ec-w64-mingw32-gcc': {'symlink': 'original-wrapper.sh'}})
        return install, files

    def test_wrapper_driver_alias_is_bound_before_metadata_execution(self):
        install, files = self.cache_fixture()
        result = check.inspected_cache_member(install, files, 'arm64ec-w64-mingw32-gcc')
        self.assertEqual(result['wrapper_driver']['resolved_path'], 'bin/clang-23')
        self.assertEqual(result['wrapper_driver']['links'], [{'path': 'bin/clang', 'target': 'clang-23'}])
        self.assertEqual(result['mode'], 0o755)

    def test_changed_wrapper_driver_alias_is_refused(self):
        install, files = self.cache_fixture()
        other = install / 'bin/other-native'
        other.write_bytes((install / 'bin/clang-23').read_bytes())
        (install / 'bin/clang').unlink()
        (install / 'bin/clang').symlink_to('other-native')
        with self.assertRaisesRegex(Error, 'cross_link_changed'):
            check.inspected_cache_member(install, files, 'arm64ec-w64-mingw32-gcc')

    def test_changed_cached_tool_mode_is_refused(self):
        install, files = self.cache_fixture()
        (install / 'bin/clang-23').chmod(0o644)
        with self.assertRaisesRegex(Error, 'cross_tool_digest'):
            check.inspected_cache_member(install, files, 'arm64ec-w64-mingw32-gcc')

    def test_legacy_manifest_records_current_mode_without_inventing_pin(self):
        install, files = self.cache_fixture()
        for row in files.values():
            row.pop('mode', None)
        result = check.inspected_cache_member(install, files, 'arm64ec-w64-mingw32-gcc')
        self.assertEqual(result['mode'], 0o755)
        self.assertTrue(result['executable_mode_observed'])
        self.assertEqual(result['mode_baseline'], 'unavailable_in_legacy_manifest')
        self.assertEqual(result['wrapper_driver']['mode_baseline'], 'unavailable_in_legacy_manifest')
        self.assertFalse(any('mode' in row for row in files.values()))

    def test_legacy_mode_mutation_changes_replayed_observations(self):
        install, files = self.cache_fixture()
        for row in files.values():
            row.pop('mode', None)
        before = check.inspected_cache_member(install, files, 'arm64ec-w64-mingw32-gcc')
        (install / 'bin/clang-23').chmod(0o644)
        after = check.inspected_cache_member(install, files, 'arm64ec-w64-mingw32-gcc')
        self.assertNotEqual(before, after)
        self.assertEqual(after['wrapper_driver']['mode'], 0o644)
        self.assertFalse(after['wrapper_driver']['executable_mode_observed'])
        self.assertEqual(after['wrapper_driver']['target_capability'], 'unperformed')

    def test_changed_tool_bytes_change_inventory_without_execution(self):
        tool = self.root / 'original-native-header'
        tool.write_bytes(b'\xcf\xfa\xed\xfe' + struct.pack('<I', MACH_ARM64) + b'\0' * 24)
        candidates = {'native_tool_paths': {'git': str(tool), 'python': str(tool), 'xcrun': str(tool), 'xxd': str(tool)}}
        old = check.selected_tool_files(candidates, [])
        tool.write_bytes(tool.read_bytes() + b'original changed bytes')
        new = check.selected_tool_files(candidates, [])
        self.assertNotEqual(old, new)
        self.assertTrue(all(row['capability'] == 'unperformed' for row in new))

if __name__ == '__main__':
    unittest.main()
