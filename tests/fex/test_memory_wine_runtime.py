"""Portable memory runtime origin/scope controls, with no native Apple calls.

Binary controls contain headers only and no executable instructions. Passing
metadata controls do not qualify a real Wine, profile, owner or FEX runtime.
"""
import ast
import copy
import errno
import io
import json
import builtins
import dis
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
from types import SimpleNamespace, FunctionType, CodeType
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
from tools.fex import memory_wine_runtime as runtime
from tools.fex.common import Error, digest_bytes, encoded
# Exact external reviewed source is an explicit test prerequisite, never a tool install.
SIGNING_REUSE = Path(os.environ.get('PEAR_TEST_SIGNING_REUSE_ROOT',
    str(REPO.parents[1] / 'pear-task7' / REPO.name)))
if not (SIGNING_REUSE / 'tools/dxmt/pairing_runtime.py').is_file() and (REPO / 'tools/dxmt/pairing_runtime.py').is_file():
    SIGNING_REUSE = REPO


def macho_metadata(cpu=0x100000c):
    return struct.pack('<8I', 0xfeedfacf, cpu, 0, 8, 0, 0, 0, 0)


def pe_metadata(machine=0xaa64):
    value = bytearray(90); value[:2] = b'MZ'; struct.pack_into('<I', value, 60, 64)
    value[64:68] = b'PE\0\0'; struct.pack_into('<H', value, 68, machine)
    return bytes(value)


def winmd_metadata():
    """Headers and empty CLR metadata only; no native or managed instructions."""
    raw = bytearray(1024); raw[:2] = b'MZ'; struct.pack_into('<I', raw, 60, 64)
    raw[64:68] = b'PE\0\0'; struct.pack_into('<H', raw, 68, 0x14c)
    struct.pack_into('<H', raw, 70, 1); struct.pack_into('<H', raw, 84, 224)
    opt = 88; struct.pack_into('<H', raw, opt, 0x10b); struct.pack_into('<I', raw, opt + 92, 16)
    struct.pack_into('<II', raw, opt + 96 + 14 * 8, 0x1000, 72)
    section = opt + 224; raw[section:section + 8] = b'.text\0\0\0'
    struct.pack_into('<4I', raw, section + 8, 512, 0x1000, 512, 512)
    struct.pack_into('<I', raw, section + 36, 0x40000020)
    struct.pack_into('<IHH4I', raw, 512, 72, 2, 5, 0x1048, 40, 1, 0)
    raw[584:588] = b'BSJB'; struct.pack_into('<HHII', raw, 588, 1, 1, 0, 20)
    raw[600:620] = b'WindowsRuntime 1.4\0\0'
    return bytes(raw)


class RuntimeControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pear-memory-runtime-pure-')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve() / 'repo'; self.repo.mkdir()
        self.out = self.repo / '.build/task5/runtime'; self.out.mkdir(parents=True)
        self.build = self.repo / '.build/task5/build'; self.build.mkdir()
        self.install = self.build / 'install'; self.install.mkdir()
        self.baseline = self.repo / '.build/task5/baseline'; self.baseline.mkdir()
        self.old_install = self.baseline / 'install'; self.old_install.mkdir()
        if not all((SIGNING_REUSE / path).is_file() for path in runtime.REUSE_PINS):
            self.skipTest('Pinned read-only Task #7 source prerequisite unavailable; no runtime qualification')
        self.helpers, _ = runtime.signing_helpers(SIGNING_REUSE, repo=REPO)
        self.reader = self.helpers.legacy(REPO)
        self.files = {
            runtime.LOADER: (macho_metadata(), 'macho', 0o755),
            runtime.NTDLL: (macho_metadata(), 'macho', 0o644),
            runtime.NTDLL_PE: (pe_metadata(), 'pe', 0o644),
            runtime.SERVER: (macho_metadata(), 'macho', 0o755),
            runtime.SENTINEL: (macho_metadata(), 'macho', 0o755),
            'share/wine/metadata.txt': (b'ordinary source metadata', 'data', 0o644),
        }
        for name, (raw, _, mode) in self.files.items():
            self.put(self.install, name, raw, mode); self.put(self.old_install, name, raw, mode)
        (self.install / 'bin/wine').symlink_to('../' + runtime.LOADER)
        (self.old_install / 'bin/wine').symlink_to('../' + runtime.LOADER)
        self.put(self.build, 'fixtures/owner-launch', macho_metadata(), 0o755)
        self.put(self.build, 'fixtures/wine-owner.exe', pe_metadata(), 0o755)
        self.manifest = self.manifest_for(self.install)
        self.old_manifest = self.manifest_for(self.old_install)
        # Only the newly rebuilt ntdll files may differ in source bytes.
        self.put(self.install, runtime.NTDLL, macho_metadata() + b'new metadata', 0o644)
        self.put(self.install, runtime.NTDLL_PE, pe_metadata() + b'new metadata', 0o644)
        self.manifest = self.manifest_for(self.install)

    def put(self, root, name, raw, mode=0o644):
        path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw); path.chmod(mode); return path

    def manifest_for(self, root):
        inventory = self.reader.inventory(root)
        return {'files': [{**row, 'kind': self.files[row['path']][1],
            **(runtime.metadata_reader(REPO).inspect_winmd(root / row['path'])
               if self.files[row['path']][1] == 'pe_metadata' else {})}
            for row in inventory if row['kind'] == 'file'],
            'symlinks': [{'path': row['path'], 'target': row['target']} for row in inventory if row['kind'] == 'symlink']}

    def ledger(self):
        return runtime.source_ledger(self.build, self.old_install, self.install, self.manifest, self.old_manifest, self.reader)

    def test_only_two_ntdll_overlay_files_and_two_original_fixtures_have_new_origins(self):
        ledger = self.ledger()
        rebuilt = [row for row in ledger if row.get('origin', {}).get('role') == 'rebuilt-memory-ntdll']
        self.assertEqual({row['path'] for row in rebuilt}, {runtime.NTDLL, runtime.NTDLL_PE})
        self.assertEqual({row['origin']['path'] for row in rebuilt}, {'install/' + runtime.NTDLL, 'install/' + runtime.NTDLL_PE})
        self.assertEqual(len([row for row in ledger if row.get('origin', {}).get('role') == 'fixture-launcher']), 1)
        self.assertEqual(len([row for row in ledger if row.get('origin', {}).get('role') == 'fixture-pe']), 1)
        self.assertEqual(next(row['runtime_path'] for row in ledger if row['path'] == runtime.LOADER), runtime.MAIN)

    def test_changed_unselected_baseline_data_mode_alias_or_missing_install_file_is_refused(self):
        for change in ['bytes', 'mode', 'alias', 'missing']:
            with self.subTest(change=change):
                name = 'share/wine/metadata.txt'; path = self.install / name; raw = path.read_bytes()
                if change == 'bytes': path.write_bytes(raw + b'changed'); self.manifest = self.manifest_for(self.install)
                elif change == 'mode': path.chmod(0o600); self.manifest = self.manifest_for(self.install)
                elif change == 'alias':
                    alias = self.install / 'bin/wine'; alias.unlink(); alias.symlink_to('../share/wine/metadata.txt')
                else: path.unlink()
                with self.assertRaises((Error, OSError)): self.ledger()
                if change == 'alias': alias.unlink(); alias.symlink_to('../' + runtime.LOADER)
                else: self.put(self.install, name, raw)
                self.manifest = self.manifest_for(self.install)

    def test_fixture_path_collision_unlisted_role_and_changed_origin_cannot_be_admitted(self):
        row = next(row for row in self.ledger() if row.get('origin', {}).get('role') == 'fixture-pe')
        wrong = copy.deepcopy(row); wrong['origin']['role'] = 'fex-translator'
        with self.assertRaisesRegex(Error, 'memory_runtime_origin_role'):
            runtime.origin_file(wrong, self.old_install, self.build)
        self.put(self.build, 'fixtures/wine-owner.exe', b'changed bytes')
        with self.assertRaisesRegex(Error, 'memory_runtime_origin_bytes'):
            runtime.origin_file(row, self.old_install, self.build)
        self.put(self.install, runtime.FIXTURE, b'extra fixture')
        self.manifest['files'].append({'path': runtime.FIXTURE, 'sha256': digest_bytes(b'extra fixture'),
            'size_bytes': 13, 'mode': 0o644, 'kind': 'pe'})
        self.manifest['files'].sort(key=lambda item: item['path'])
        with self.assertRaises(Error): self.ledger()

    def test_materialized_full_tree_preserves_data_modes_aliases_and_unique_new_ntdll(self):
        ledger = self.ledger(); profile = b'non-authorizing private test metadata'
        runtime.materialize(self.out, ledger, self.old_install, self.build, profile, self.helpers)
        for row in ledger:
            path = self.out / row['runtime_path']
            if row['kind'] == 'file':
                _, raw = runtime.origin_file(row, self.old_install, self.build)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(path.stat().st_mode & 0o777, row['mode'])
            elif row['kind'] == 'symlink': self.assertEqual(path.readlink().as_posix(), row['target'])
        self.assertEqual((self.out / runtime.PAYLOAD / runtime.LOADER).resolve(), self.out / runtime.MAIN)
        self.assertEqual((self.out / runtime.NTDLL_ALIAS).resolve(), self.out / runtime.PAYLOAD / runtime.NTDLL)
        natives, pes, _ = runtime.inventory_images(self.out, ledger, self.old_install, self.build, self.reader, self.helpers)
        self.assertEqual(sum(row['origin']['path'] == 'install/' + runtime.NTDLL for row in natives), 1)
        self.assertEqual(len([row for row in pes if row['origin']['role'] == 'fixture-pe']), 1)
        self.assertFalse((self.out / 'runtime.json').exists())

    def test_current_payload_extra_file_or_changed_data_or_nonarm64_fixture_is_refused(self):
        ledger = self.ledger(); runtime.materialize(self.out, ledger, self.old_install, self.build, b'profile metadata', self.helpers)
        extra = self.put(self.out, runtime.BUNDLE + '/unexpected-data', b'extra')
        with self.assertRaisesRegex(Error, 'memory_runtime_payload_set'):
            runtime.inventory_images(self.out, ledger, self.old_install, self.build, self.reader, self.helpers)
        extra.unlink(); target = self.out / runtime.PAYLOAD / 'share/wine/metadata.txt'; raw = target.read_bytes()
        target.write_bytes(raw + b'changed')
        with self.assertRaisesRegex(Error, 'memory_runtime_data_changed'):
            runtime.inventory_images(self.out, ledger, self.old_install, self.build, self.reader, self.helpers)
        target.write_bytes(raw)
        self.put(self.build, 'fixtures/wine-owner.exe', pe_metadata(0xa641), 0o755)
        changed = self.ledger()
        row = next(row for row in changed if row['path'] == runtime.FIXTURE)
        (self.out / row['runtime_path']).write_bytes(pe_metadata(0xa641))
        with self.assertRaisesRegex(Error, 'memory_runtime_ordinary_pe_machine'):
            runtime.inventory_images(self.out, changed, self.old_install, self.build, self.reader, self.helpers)

    def test_genuine_source_declared_winmd_is_preserved_without_loaded_pe_admission(self):
        name = 'share/wine/winmd/windows.applicationmodel.winmd'
        raw = winmd_metadata(); self.files[name] = (raw, 'pe_metadata', 0o644)
        self.put(self.install, name, raw); self.put(self.old_install, name, raw)
        self.manifest = self.manifest_for(self.install); self.old_manifest = self.manifest_for(self.old_install)
        ledger = self.ledger(); selected = next(row for row in ledger if row['path'] == name)
        self.assertEqual(selected['format_kind'], 'pe_metadata')
        self.assertEqual(selected['origin']['role'], 'baseline-native')
        runtime.materialize(self.out, ledger, self.old_install, self.build, b'profile metadata', self.helpers)
        _, pes, _ = runtime.inventory_images(self.out, ledger, self.old_install, self.build, self.reader, self.helpers)
        self.assertFalse(any(row['path'] == runtime.PAYLOAD + '/' + name for row in pes))
        actual = self.out / runtime.PAYLOAD / name
        self.assertEqual(actual.read_bytes(), raw)
        bad = bytearray(raw); struct.pack_into('<I', bad, 88 + 16, 0x1000)
        expected = next(row for row in self.manifest['files'] if row['path'] == name)
        actual.write_bytes(bad)
        with self.assertRaisesRegex(Error, 'memory_runtime_data_changed'):
            runtime.inventory_images(self.out, ledger, self.old_install, self.build, self.reader, self.helpers)
        with self.assertRaisesRegex(Error, 'winmd_executable_content'):
            runtime.validate_metadata(self.out, runtime.PAYLOAD + '/' + name, name, expected, runtime.metadata_reader(REPO))
        with self.assertRaisesRegex(Error, 'memory_runtime_metadata_scope'):
            runtime.validate_metadata(self.install, name, 'lib/wine/aarch64-windows/not-metadata.dll',
                expected, runtime.metadata_reader(REPO))

    def test_arbitrary_pe_cannot_be_reclassified_as_nonexecuting_winmd(self):
        expected = next(row for row in self.manifest['files'] if row['path'] == runtime.NTDLL_PE)
        expected.update(kind='pe_metadata', machine=0x14c, metadata_only=True)
        with self.assertRaisesRegex(Error, 'memory_runtime_metadata_scope'): self.ledger()
        name = 'share/wine/winmd/unlisted.winmd'; raw = winmd_metadata()
        self.files[name] = (raw, 'pe_metadata', 0o644)
        self.put(self.install, name, raw); self.put(self.old_install, name, raw)
        self.manifest = self.manifest_for(self.install); self.old_manifest = self.manifest_for(self.old_install)
        with self.assertRaisesRegex(Error, 'memory_runtime_metadata_scope'): self.ledger()

    def test_only_retained_exact_source_negative_pe_fixtures_are_preserved_as_refused(self):
        controls = {'libexec/pear-stage3/api-x64.exe': 0x8664,
                    'libexec/pear-stage3/api-i386.exe': 0x14c}
        for name, machine in controls.items():
            raw = pe_metadata(machine); self.files[name] = (raw, 'pe', 0o755)
            self.put(self.install, name, raw, 0o755); self.put(self.old_install, name, raw, 0o755)
        self.manifest = self.manifest_for(self.install); self.old_manifest = self.manifest_for(self.old_install)
        ledger = self.ledger()
        runtime.materialize(self.out, ledger, self.old_install, self.build, b'profile metadata', self.helpers)
        _, pes, _ = runtime.inventory_images(self.out, ledger, self.old_install, self.build, self.reader, self.helpers)
        negative = [row for row in pes if row['classification'] == 'retained_wrong_architecture_fixture']
        self.assertEqual({row['path']: row['machine'] for row in negative},
                         {runtime.PAYLOAD + '/' + name: machine for name, machine in controls.items()})
        self.assertTrue(all(row['origin']['role'] == 'baseline-native' and row['load_admission'] == 'refused'
                            and row['execution_performed'] is False for row in negative))
        ordinary = [row for row in pes if row['classification'] == 'ordinary_arm64_image']
        self.assertTrue(all(row['machine'] == 0xaa64 and row['load_admission'] == 'unperformed' for row in ordinary))
        row = next(row for row in ledger if row['path'] == 'libexec/pear-stage3/api-x64.exe')
        wrong = copy.deepcopy(row); wrong['origin']['role'] = 'fixture-pe'
        with self.assertRaisesRegex(Error, 'memory_runtime_negative_pe_scope'):
            runtime.pe_scope(wrong, 0x8664, repo=REPO)
        with self.assertRaisesRegex(Error, 'memory_runtime_negative_pe_scope'):
            runtime.pe_scope(row, 0xaa64, repo=REPO)
        wrong = copy.deepcopy(row); wrong['path'] = 'lib/wine/aarch64-windows/foreign-x64.dll'
        with self.assertRaisesRegex(Error, 'memory_runtime_ordinary_pe_machine'):
            runtime.pe_scope(wrong, 0x8664, repo=REPO)
        actual = self.out / runtime.PAYLOAD / row['path']; actual.write_bytes(pe_metadata(0xaa64))
        with self.assertRaisesRegex(Error, 'memory_runtime_data_changed'):
            runtime.inventory_images(self.out, ledger, self.old_install, self.build, self.reader, self.helpers)

    def test_negative_pe_original_source_contract_must_explicitly_refuse_execution(self):
        root = self.repo / 'source-contract'; (root / 'tools/wine').mkdir(parents=True)
        path = root / 'tools/wine/signing.py'
        path.write_text("API_GUESTS = {'x64_control': ('libexec/pear-stage3/api-x64.exe', 0x8664, True), "
                        "'i386_control': ('libexec/pear-stage3/api-i386.exe', 0x14c, False)}\n")
        row = {'path': 'libexec/pear-stage3/api-x64.exe',
               'origin': {'role': 'baseline-native', 'path': 'libexec/pear-stage3/api-x64.exe'}}
        with self.assertRaisesRegex(Error, 'memory_runtime_negative_pe_source'):
            runtime.pe_scope(row, 0x8664, repo=root)
        path.write_text(path.read_text().replace('0x8664, True', '0x8664, 0'))
        with self.assertRaisesRegex(Error, 'memory_runtime_negative_pe_source'):
            runtime.pe_scope(row, 0x8664, repo=root)

    def clone_metadata_copy(self, source_fd, parent_fd, leaf):
        # Mock operation writes only non-executing test bytes. It does not call
        # the Apple clone API or qualify filesystem sharing/native execution.
        raw = runtime.descriptor_bytes(source_fd, 1024**2)
        fd = os.open(leaf, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent_fd)
        try:
            with os.fdopen(os.dup(fd), 'wb') as stream: stream.write(raw)
        finally: os.close(fd)
        return 0

    def copy_one(self, row=None):
        row = row or next(row for row in self.ledger() if row['path'] == 'share/wine/metadata.txt')
        return runtime.copy_payload(self.out, row, self.old_install, self.build, self.helpers, prefer_clone=True)

    def test_mock_clone_full_copy_ledger_independence_and_private_writes_are_verified(self):
        ledger = self.ledger()
        with mock.patch.object(runtime, 'public_clone', side_effect=self.clone_metadata_copy) as operation:
            copies = runtime.materialize(self.out, ledger, self.old_install, self.build,
                b'private non-authorizing metadata', self.helpers, prefer_clone=True)
        self.assertEqual(operation.call_count, len([row for row in ledger if row['kind'] == 'file']))
        self.assertEqual(runtime.copy_counts(copies), {'public_fclonefileat': len(copies), 'byte_copy': 0})
        self.assertEqual(runtime.verify_copies(self.out, ledger, self.old_install, self.build, copies), copies)
        profile = self.out / runtime.BUNDLE / 'Contents/embedded.provisionprofile'
        self.assertEqual(profile.read_bytes(), b'private non-authorizing metadata')
        self.assertFalse(any(row['path'] == profile.relative_to(self.out).as_posix() for row in copies))
        self.assertEqual(profile.stat().st_mode & 0o777, 0o600)
        copied = next(row for row in copies if row['path'] == runtime.PAYLOAD + '/share/wine/metadata.txt')
        actual = self.out / copied['path']; original = (self.old_install / 'share/wine/metadata.txt').read_bytes()
        actual.write_bytes(b'private independent destination change')
        self.assertEqual((self.old_install / 'share/wine/metadata.txt').read_bytes(), original)
        changed = copy.deepcopy(copies); changed[0]['clone_result']['return_value'] = False
        with self.assertRaisesRegex(Error, 'memory_runtime_copy_method'):
            runtime.verify_copies(self.out, ledger, self.old_install, self.build, changed)

    def test_only_documented_unsupported_and_cross_device_clone_errno_fall_back(self):
        row = next(row for row in self.ledger() if row['path'] == 'share/wine/metadata.txt')
        for code in sorted(runtime.CLONE_FALLBACK):
            destination = self.out / row['runtime_path']
            with mock.patch.object(runtime, 'public_clone', side_effect=OSError(code, 'mock unsupported filesystem')):
                copy_row = self.copy_one(row)
            self.assertEqual(copy_row['method'], 'byte_copy')
            self.assertEqual(copy_row['clone_result'], {'status': 'failed', 'return_value': -1,
                'native_error': {'domain': 'POSIX', 'code': code}})
            self.assertEqual(destination.read_bytes(), (self.old_install / row['path']).read_bytes())
            runtime.verify_copies(self.out, [row], self.old_install, self.build, [copy_row])
            changed = copy.deepcopy(copy_row); changed['clone_result']['native_error']['code'] = errno.ENOSPC
            with self.assertRaisesRegex(Error, 'memory_runtime_copy_fallback'):
                runtime.verify_copies(self.out, [row], self.old_install, self.build, [changed])
            destination.unlink()
        cause = OSError(errno.ENOSPC, 'mock full filesystem')
        with mock.patch.object(runtime, 'public_clone', side_effect=cause):
            with self.assertRaises(OSError) as thrown: self.copy_one(row)
        self.assertIs(thrown.exception, cause); self.assertFalse(destination.exists())

    def test_existing_or_partial_clone_output_is_never_replaced_on_fallback(self):
        row = next(row for row in self.ledger() if row['path'] == 'share/wine/metadata.txt')
        target = self.out / row['runtime_path']; target.parent.mkdir(parents=True); target.write_bytes(b'owned previous file')
        with mock.patch.object(runtime, 'public_clone', side_effect=AssertionError('clone must not run')):
            with self.assertRaisesRegex(Error, 'memory_runtime_copy_destination_exists'): self.copy_one(row)
        self.assertEqual(target.read_bytes(), b'owned previous file'); target.unlink()
        def partial(fd, parent_fd, leaf):
            raw_fd = os.open(leaf, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=parent_fd)
            os.write(raw_fd, b'partial source evidence'); os.close(raw_fd)
            raise OSError(errno.ENOTSUP, 'mock unsupported with forbidden side effect')
        with mock.patch.object(runtime, 'public_clone', side_effect=partial):
            with self.assertRaisesRegex(Error, 'memory_runtime_clone_failed_output') as raised: self.copy_one(row)
        self.assertEqual(target.read_bytes(), b'partial source evidence')
        self.assertEqual(raised.exception.native_error['code'], errno.ENOTSUP)

    def test_mock_hard_link_and_source_or_destination_alias_are_refused_before_chmod(self):
        row = next(row for row in self.ledger() if row['path'] == 'share/wine/metadata.txt')
        original = self.old_install / row['path']; mode = original.stat().st_mode & 0o777
        def linked(fd, parent_fd, leaf):
            os.link(original, leaf, dst_dir_fd=parent_fd); return 0
        with mock.patch.object(runtime, 'public_clone', side_effect=linked):
            with self.assertRaisesRegex(Error, 'memory_runtime_copy_independence'): self.copy_one(row)
        self.assertEqual(original.stat().st_mode & 0o777, mode)
        target = self.out / row['runtime_path']; target.unlink()
        moved = original.with_name('source-moved'); original.rename(moved); original.symlink_to(moved.name)
        with mock.patch.object(runtime, 'public_clone', side_effect=AssertionError('clone must not run')):
            with self.assertRaises((Error, OSError)): self.copy_one(row)
        original.unlink(); moved.rename(original)
        parent = target.parent; parent.rename(parent.with_name('owned-moved')); parent.symlink_to('owned-moved')
        with mock.patch.object(runtime, 'public_clone', side_effect=AssertionError('clone must not run')):
            with self.assertRaises((Error, OSError)): self.copy_one(row)

    def test_clone_post_bytes_and_source_mutation_cannot_produce_copy_success(self):
        row = next(row for row in self.ledger() if row['path'] == 'share/wine/metadata.txt')
        def changed_destination(fd, parent_fd, leaf):
            self.clone_metadata_copy(fd, parent_fd, leaf)
            target = self.out / row['runtime_path']; target.write_bytes(b'changed copied bytes'); return 0
        with mock.patch.object(runtime, 'public_clone', side_effect=changed_destination):
            with self.assertRaisesRegex(Error, 'memory_runtime_copy_bytes'): self.copy_one(row)
        (self.out / row['runtime_path']).unlink()
        def changed_source(fd, parent_fd, leaf):
            self.clone_metadata_copy(fd, parent_fd, leaf)
            (self.old_install / row['path']).write_bytes(b'changed donor bytes'); return 0
        with mock.patch.object(runtime, 'public_clone', side_effect=changed_source):
            with self.assertRaisesRegex(Error, 'memory_runtime_copy_source_changed'): self.copy_one(row)

    def test_public_clone_uses_exact_installed_api_flags_and_preserves_errno(self):
        function = mock.Mock(return_value=0)
        library = SimpleNamespace(fclonefileat=function)
        with mock.patch.object(runtime.ctypes, 'CDLL', return_value=library) as load, \
             mock.patch.object(runtime.platform, 'system', return_value='Darwin'):
            self.assertEqual(runtime.public_clone(1, 2, 'owned'), 0)
        load.assert_called_once_with('/usr/lib/libSystem.B.dylib', use_errno=True)
        function.assert_called_once_with(1, 2, b'owned', 0x0001 | 0x0002 | 0x0008)
        function.return_value = -1
        with mock.patch.object(runtime.ctypes, 'CDLL', return_value=library), \
             mock.patch.object(runtime.platform, 'system', return_value='Darwin'), \
             mock.patch.object(runtime.ctypes, 'get_errno', return_value=errno.EIO):
            with self.assertRaises(OSError) as raised: runtime.public_clone(1, 2, 'owned')
        self.assertEqual(raised.exception.errno, errno.EIO)

    def test_fixed_reviewed_ast_reuse_changes_no_import_cache_or_native_calls(self):
        before = {key: sys.modules.get(key) for key in ['common', 'build', 'signing']}
        with mock.patch.object(runtime.subprocess, 'Popen', side_effect=AssertionError('native command forbidden')):
            helpers, captured = runtime.signing_helpers(SIGNING_REUSE, repo=REPO)
            reader = helpers.legacy(REPO)
        self.assertEqual({name: digest_bytes(raw) for name, raw in captured.items()}, runtime.REUSE_PINS)
        self.assertEqual(helpers.SCOPE, runtime.SCOPE)
        self.assertEqual(before, {key: sys.modules.get(key) for key in before})
        self.assertTrue(callable(reader.profile_authorization))
        reuse = self.repo / 'reviewed-sources'; reuse.mkdir()
        for path, raw in captured.items(): self.put(reuse, path, raw)
        self.put(reuse, 'tools/dxmt/pairing_runtime.py', captured['tools/dxmt/pairing_runtime.py'] + b'\n')
        with self.assertRaisesRegex(Error, 'memory_runtime_reuse_pin'): runtime.signing_helpers(reuse, repo=REPO)
        with self.assertRaisesRegex(Error, 'memory_runtime_reuse_functions'):
            runtime.selected(b'@decorator\ndef expected():pass\n', ('expected',), {}, 'malformed metadata')

    def test_every_selected_helper_and_nested_body_has_closed_real_globals(self):
        def missing(namespace):
            result = []; visited = set()
            def function(value, prefix):
                if id(value) in visited: return
                visited.add(id(value))
                if isinstance(value, FunctionType):
                    declared = value.__globals__
                    fallback = declared.get('__builtins__', builtins)
                    fallback = fallback if isinstance(fallback, dict) else vars(fallback)
                    def code(body):
                        for item in dis.get_instructions(body):
                            if item.opname == 'LOAD_GLOBAL' and item.argval not in declared and item.argval not in fallback:
                                result.append((prefix, item.argval))
                        for item in body.co_consts:
                            if isinstance(item, CodeType): code(item)
                    code(value.__code__)
                elif isinstance(value, SimpleNamespace):
                    for name, child in vars(value).items(): function(child, prefix + '.' + name)
            function(namespace, 'reviewed')
            return sorted(set(result))
        with mock.patch.object(runtime.subprocess, 'Popen', side_effect=AssertionError('native command forbidden')):
            reader = self.helpers.legacy(REPO)
            self.assertEqual(missing(self.helpers), [])
            self.assertEqual(missing(reader), [])
            self.assertEqual(missing(runtime.metadata_reader(REPO)), [])
            actual = {'schema_version': 1, 'record_kind': 'finite_metadata_test'}
            self.helpers.fields(actual, actual.keys(), 'finite_metadata_test')
            with self.assertRaisesRegex(Error, 'unexpected_record_kind'):
                self.helpers.fields(actual, actual.keys(), 'wrong_kind')
            with self.assertRaisesRegex(Error, 'unsupported_record_version'):
                self.helpers.fields({**actual, 'schema_version': True}, actual.keys(), 'finite_metadata_test')
            globals_ = self.helpers.fields.__globals__; original = globals_.pop('record')
            try:
                self.assertIn(('reviewed.fields', 'record'), missing(self.helpers))
            finally: globals_['record'] = original

    def test_only_wine_main_requests_profile_cross_and_jit_claims_all_ordinary_images_zero(self):
        reader = self.reader; grant = reader.CROSS_KEYS[0]
        private = {'claims': {reader.APP_ID: 'TEST.' + runtime.BUNDLE_ID, reader.TEAM_ID: 'TEST', grant: True},
                   'granted_cross_architecture_key': grant}
        claims = reader.loader_claims(private, 'page-wx')
        self.assertEqual(set(claims), {reader.APP_ID, reader.TEAM_ID, grant, reader.PROFILE.BASELINE.ALLOW_JIT})
        images = [{'path': runtime.MAIN}, {'path': runtime.PAYLOAD + '/' + runtime.NTDLL},
                  {'path': runtime.PAYLOAD + '/' + runtime.LAUNCHER}]
        recipe = self.helpers.signing_recipe(self.out, images, '0' * 40)
        ordinary = [argv for ident, argv in recipe if ident.startswith('native.') and ident.endswith('.sign')]
        self.assertTrue(all('--entitlements' not in argv and '--deep' not in argv for argv in ordinary))
        loader = next(argv for ident, argv in recipe if ident == 'loader.sign')
        self.assertIn('--entitlements', loader); self.assertIn('4096', loader)
        current = runtime.admission_recipe(self.out / 'admission' / 'owned', {'native_images': images}, self.helpers)
        self.assertEqual(current[0][0], 'profile.decode')
        self.assertTrue(any(str(self.out / runtime.MAIN) in argv for _, argv in current))

    def test_missing_or_changed_capture_and_source_snapshot_is_refused(self):
        self.put(self.out, 'producers/a.py', b'source')
        runtime.snapshot_set(self.out, 'producers', {'a.py'})
        self.put(self.out, 'producers/extra.py', b'extra')
        with self.assertRaisesRegex(Error, 'memory_runtime_snapshot_set'):
            runtime.snapshot_set(self.out, 'producers', {'a.py'})
        (self.out / 'producers/extra.py').unlink()
        (self.out / 'producers/a.py').rename(self.out / 'producers/b.py')
        (self.out / 'producers/a.py').symlink_to('b.py')
        with self.assertRaisesRegex(Error, 'memory_runtime_snapshot_file'):
            runtime.snapshot_set(self.out, 'producers', {'a.py', 'b.py'})

    def test_constructor_preflight_failure_records_original_errno_and_no_sign_or_init(self):
        cause = OSError(errno.EIO, 'test preflight read failure')
        output = self.repo / '.build/task5/refused'
        with mock.patch.object(runtime, 'prerequisite', side_effect=cause), \
             mock.patch.object(runtime.subprocess, 'Popen', side_effect=AssertionError('native command forbidden')):
            with self.assertRaises(OSError) as raised:
                runtime.prepare(self.build, self.repo / 'not-a-real-profile', output, SIGNING_REUSE, repo=self.repo)
        self.assertIs(raised.exception, cause)
        record = runtime.load_json(output / 'failed.json')
        self.assertEqual(record['native_error'], {'domain': 'POSIX', 'code': errno.EIO, 'exception_type': 'OSError'})
        self.assertEqual(record['phase'], 'build_replay')
        self.assertEqual(record['commands'], []); self.assertFalse(record['fex_initialization'])
        self.assertFalse(record['runtime_eligible']); self.assertFalse((output / 'runtime.json').exists())

    def test_reused_native_start_failure_has_unknown_exit_and_preserved_original_errno(self):
        helpers = self.helpers; directory = self.repo / '.build/task5/native-refusal'; directory.mkdir()
        rows = []; cause = OSError(errno.EACCES, 'test native start failure')
        with mock.patch.dict(helpers.native.__globals__, {'run_bounded': mock.Mock(side_effect=cause),
                'platform': SimpleNamespace(system=lambda: 'Darwin', machine=lambda: 'arm64')}):
            with self.assertRaises(OSError) as raised:
                helpers.native(['/usr/bin/security', 'cms', '-D'], directory, 'profile.decode', rows)
        self.assertIs(raised.exception, cause); self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]['exit_code']); self.assertEqual(rows[0]['status'], 'failed')
        self.assertEqual(rows[0]['native_error']['code'], errno.EACCES)
        self.assertEqual(rows[0]['native_error']['domain'], 'POSIX')


class ByteReceiptControls(unittest.TestCase):
    """Real profile-byte boundary statements, no authorization/signing mocks."""
    def test_same_bytes_are_exact_and_json_type_distinctions_remain_strict(self):
        runtime.same(b'\0private-profile\xff', bytes(bytearray(b'\0private-profile\xff')), 'mismatch')
        for left, right in [(b'profile', b'changed'), (b'profile', 'profile'),
                            ('profile', b'profile'), (b'profile', bytearray(b'profile'))]:
            with self.subTest(left_type=type(left).__name__, right_type=type(right).__name__):
                with self.assertRaisesRegex(Error, 'mismatch'): runtime.same(left, right, 'mismatch')
        runtime.same({'claims': True}, {'claims': True}, 'mismatch')
        for left, right in [({'claims': True}, {'claims': 1}), ({'claims': False}, {'claims': 0}),
                            ({'claims': []}, {'claims': {}})]:
            with self.assertRaisesRegex(Error, 'mismatch'): runtime.same(left, right, 'mismatch')

    def test_actual_structural_embedded_profile_statements_compare_current_bytes_and_mode(self):
        # Execute the real structural component with real rooted file reads. The
        # surrounding upstream authorization is deliberately not simulated.
        module = ast.parse(Path(runtime.__file__).read_bytes())
        body = next(node.body for node in module.body if isinstance(node, ast.FunctionDef)
                    and node.name == 'verify_structural')
        checks = {'memory_runtime_embedded_profile_changed', 'memory_runtime_private_profile_mode'}
        selected = [node for node in body if any(isinstance(child, ast.Constant)
                    and child.value in checks for child in ast.walk(node))]
        self.assertEqual(len(selected), 2)
        function = ast.FunctionDef(name='profile_component',
            args=ast.arguments(posonlyargs=[], args=[ast.arg(arg='root'), ast.arg(arg='raw_profile')],
                kwonlyargs=[], kw_defaults=[], defaults=[]), body=selected, decorator_list=[])
        code = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
        namespace = dict(vars(runtime)); exec(compile(code, runtime.__file__, 'exec'), namespace)
        with tempfile.TemporaryDirectory(prefix='pear-profile-bytes-pure-') as temporary:
            root = Path(temporary).resolve(); path = root / runtime.BUNDLE / 'Contents/embedded.provisionprofile'
            path.parent.mkdir(parents=True); raw = b'non-authorizing test CMS bytes\0\xff'
            path.write_bytes(raw); path.chmod(0o600)
            namespace['profile_component'](root, raw)
            for changed in [raw + b'changed', raw.decode('latin1')]:
                with self.assertRaisesRegex(Error, 'memory_runtime_embedded_profile_changed'):
                    namespace['profile_component'](root, changed)
            path.chmod(0o644)
            with self.assertRaisesRegex(Error, 'memory_runtime_private_profile_mode'):
                namespace['profile_component'](root, raw)
            path.chmod(0o600); path.rename(path.with_suffix('.preserved'))
            path.symlink_to('embedded.preserved')
            with self.assertRaises((Error, OSError)): namespace['profile_component'](root, raw)


class AdmissionReceiptControls(unittest.TestCase):
    """Pure synthetic receipts test the explicit-handle boundary on every OS."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pear-memory-admission-pure-')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve() / 'repo'; self.repo.mkdir()
        self.root = self.repo / '.build/task5/runtime'; self.root.mkdir(parents=True)
        self.directory = self.root / 'admission' / ('1' * 32); self.directory.mkdir(parents=True, mode=0o700)
        self.profile = b'non-authorizing test metadata'
        self.runtime = {'native_images': [], 'signing_reuse': {'root': 'fixed-reviewed-source'}}
        self.original = {'claims': {'test': True}, 'identity': 'test'}
        self.record = {'schema_version': 1, 'record_kind': 'fex_memory_wine_admission', 'scope': runtime.SCOPE,
            'runtime_ref': {'path': str(self.root), 'sha256': runtime.digest_bytes(b'original runtime bytes')},
            'profile_sha256': runtime.digest_bytes(self.profile), 'commands': [], 'current_checks': {'finite': True},
            'passed': True, 'execution_performed': False, 'runtime_eligible': False, 'distribution_qualified': False}
        (self.root / 'runtime.json').write_bytes(b'original runtime bytes')
        runtime.write_json(self.directory / 'admission.json', self.record)

    def replay(self, *, observation=None):
        with mock.patch.object(runtime, 'verify_structural', return_value=(self.runtime, self.original, self.profile)), \
             mock.patch.object(runtime, 'signing_helpers', return_value=(SimpleNamespace(), {})), \
             mock.patch.object(runtime, 'admission_observations', return_value=observation or {'checks': {'finite': True}}), \
             mock.patch.object(runtime.subprocess, 'Popen', side_effect=AssertionError('native command forbidden')):
            return runtime.verify_admission(self.root, self.directory, repo=self.repo)

    def test_explicit_receipt_replay_does_not_run_apple_tools(self):
        self.assertEqual(self.replay(), self.record)
        outside = self.repo / '.build/task5/other/admission' / ('1' * 32); outside.mkdir(parents=True, mode=0o700)
        with self.assertRaisesRegex(Error, 'memory_runtime_admission_path'):
            runtime.admission_directory(self.root, outside)
        self.directory.rename(self.directory.parent / 'latest')
        with self.assertRaisesRegex(Error, 'memory_runtime_admission_path'):
            runtime.admission_directory(self.root, self.directory.parent / 'latest')

    def test_failed_changed_runtime_profile_scope_or_checks_refuses_receipt(self):
        (self.directory / 'failed.json').write_bytes(b'original failure')
        with self.assertRaisesRegex(Error, 'memory_runtime_admission_failed'): self.replay()
        (self.directory / 'failed.json').unlink()
        for key, value, error in [('passed', 1, 'memory_runtime_admission_scope'),
                                 ('execution_performed', True, 'memory_runtime_admission_scope'),
                                 ('scope', 'general-runtime', 'memory_runtime_admission_scope'),
                                 ('profile_sha256', '0' * 64, 'memory_runtime_admission_profile_changed')]:
            with self.subTest(key=key):
                changed = copy.deepcopy(self.record); changed[key] = value
                (self.directory / 'admission.json').write_bytes(runtime.encoded(changed))
                with self.assertRaisesRegex(Error, error): self.replay()
        (self.directory / 'admission.json').write_bytes(runtime.encoded(self.record))
        with self.assertRaisesRegex(Error, 'memory_runtime_admission_checks_changed'):
            self.replay(observation={'checks': {'finite': False}})
        (self.root / 'runtime.json').write_bytes(b'changed current runtime bytes')
        with self.assertRaisesRegex(Error, 'memory_runtime_admission_runtime_changed'): self.replay()

    def test_cli_program_dependency_failure_is_truthful_and_does_not_fabricate_native_error(self):
        stderr = io.StringIO(); cause = NameError('missing selected helper dependency')
        args = ['--artifact', str(self.root), '--profile', 'not-a-real-profile',
                '--signing-reuse-root', 'reviewed-source', '--output', 'fresh-output', '--require-empty']
        with mock.patch.object(runtime, 'prepare', side_effect=cause), mock.patch.object(runtime.sys, 'stderr', stderr):
            self.assertEqual(runtime.main(args), 1)
        value = json.loads(stderr.getvalue())
        self.assertEqual(value['exception_type'], 'NameError')
        self.assertFalse(value['execution_performed']); self.assertFalse(value['runtime_eligible'])
        self.assertEqual(value['error'], 'memory_runtime_failed')
        self.assertNotIn('native_error', value)

    def test_fresh_admission_returns_exact_handle_and_wrapper_preserves_runtime_only(self):
        with mock.patch.object(runtime, 'admit_runtime', return_value=(self.runtime, self.directory)) as call:
            self.assertEqual(runtime.verify_runtime(self.root, repo=self.repo), self.runtime)
        call.assert_called_once_with(self.root, repo=self.repo)

    def test_raw_log_recipe_replay_and_current_profile_and_signature_are_mandatory(self):
        # A locally specified fake profile evaluator isolates the log boundary;
        # it does not validate or create any real profile/signing authorization.
        if not all((SIGNING_REUSE / path).is_file() for path in runtime.REUSE_PINS):
            self.skipTest('Pinned read-only Task #7 source prerequisite unavailable; no runtime qualification')
        helpers, _ = runtime.signing_helpers(SIGNING_REUSE, repo=REPO)
        current = {'claims': self.original['claims'], 'identity': self.original['identity'], 'checks': {'finite': True}}
        helpers.legacy = lambda repo: SimpleNamespace(loader_claims=lambda private, policy: {'finite': True})
        helpers.profile_from_logs = lambda raw, logs, reader: current
        helpers.signature_from_logs = lambda *args: {'signed': True}
        helpers.signer_leaf = lambda *args: None
        for path in [self.directory / 'captured-profile.provisionprofile',
                     self.root / runtime.BUNDLE / 'Contents/embedded.provisionprofile']:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(self.profile); path.chmod(0o600)
        rows = []
        for ident, argv in runtime.admission_recipe(self.directory, self.runtime, helpers):
            logs = {}
            for channel in ['stdout', 'stderr']:
                name = 'logs/' + ident + '/' + channel; path = self.directory / name
                path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'bounded test log')
                logs[channel] = {'path': name, 'sha256': runtime.digest_bytes(b'bounded test log'), 'size_bytes': 16}
            rows.append({'id': ident, 'argv': ['/usr/bin/arch', '-arm64', *argv], 'environment': helpers.ENV,
                'cwd': str(self.directory), 'exit_code': 0, 'elapsed_ms': 1, 'status': 'completed', 'error': None,
                'bound_outcome': None, 'evidence_error': None, 'logs': logs})
        def observe():
            with mock.patch.object(runtime.subprocess, 'Popen', side_effect=AssertionError('native command forbidden')):
                return runtime.admission_observations(self.root, self.directory, self.runtime, self.original,
                    self.profile, rows, helpers, REPO)
        self.assertEqual(observe(), current)
        first = rows[0]; original = first['argv']; first['argv'] = original + ['--changed']
        with self.assertRaisesRegex(Error, 'pair_signing_command_recipe'): observe()
        first['argv'] = original
        target = self.directory / first['logs']['stdout']['path']; target.write_bytes(b'changed raw log')
        with self.assertRaisesRegex(Error, 'pair_signing_log_changed'): observe()
        target.write_bytes(b'bounded test log')
        current['claims'] = {'different': True}
        with self.assertRaisesRegex(Error, 'memory_runtime_current_profile_claims'): observe()
        current['claims'] = self.original['claims']
        helpers.signer_leaf = mock.Mock(side_effect=Error('wrong_leaf'))
        with self.assertRaisesRegex(Error, 'wrong_leaf'): observe()


if __name__ == '__main__':
    unittest.main()
