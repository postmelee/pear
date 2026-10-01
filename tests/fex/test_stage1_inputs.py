"""Portable source-owner rejection tests; no engine build or guest execution."""
from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import shutil
import subprocess
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.fex import common, prepare


def listing(rows):
    return b''.join((mode + ' ' + ('commit' if mode == '160000' else 'blob') + ' ' + oid + '\t' + path).encode() + b'\0'
                    for path, mode, oid in rows)


def blob(data):
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.value = common.load_json(REPO / 'runtime/fex/inputs.json')

    def reject(self, value, code):
        with self.assertRaises(common.Error) as error:
            prepare.validate_inputs(value)
        self.assertEqual(error.exception.code, code)

    def test_exact_selected_records_bind_historical_audit_and_baseline(self):
        result = prepare.validate_inputs(self.value)
        self.assertEqual(set(result['components']), prepare.SELECTED)
        self.assertEqual(result['audit']['decision'], 'blocked')
        self.assertFalse(result['audit']['source_ready'])
        paths = prepare.mount_paths(result)
        self.assertEqual(paths['fex-cpp-optparse'], 'Source/Common/cpp-optparse')
        self.assertEqual(paths['fex-range-v3'], 'External/range-v3')
        self.assertEqual(len([m for m in result['mounts'] if m['status'] == 'enabled']), 6)

    def test_missing_enabled_dependency_and_mount_fail(self):
        v = copy.deepcopy(self.value); v['components'].pop(); self.reject(v, 'component_count')
        v = copy.deepcopy(self.value); v['mounts'].pop(); self.reject(v, 'mount_closure')

    def test_wrong_pin_wrong_listing_and_wrong_baseline_fail(self):
        for key in ('commit', 'tree'):
            v = copy.deepcopy(self.value); v['components'][0][key] = '0' * 40
            self.reject(v, 'component_audit_mismatch')
        v = copy.deepcopy(self.value); v['components'][0]['listing_ref']['sha256'] = '0' * 64
        self.reject(v, 'component_audit_mismatch')
        v = copy.deepcopy(self.value); v['baseline_ref']['materialized_source_manifest_sha256'] = '0' * 64
        self.reject(v, 'baseline_identity')

    def test_terms_and_interface_coverage_cannot_be_omitted(self):
        v = copy.deepcopy(self.value); v['terms'] = [r for r in v['terms'] if 'SoftFloat' not in r['path']]
        self.reject(v, 'bundled_terms_closure')
        v = copy.deepcopy(self.value); v['interface_sources'].pop()
        self.reject(v, 'source_reference_closure')
        v = copy.deepcopy(self.value); v['source_requirements'].append(v['source_requirements'][0])
        self.reject(v, 'source_reference_identity')

    def test_product_kind_and_unreviewed_field_rejected(self):
        v = copy.deepcopy(self.value); v['record_kind'] = 'runtime_lock'; self.reject(v, 'unexpected_record_kind')
        v = copy.deepcopy(self.value); v['source_ready'] = True; self.reject(v, 'input_fields')

    def test_duplicate_json_and_noninteger_budget_rejected(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":1.2}', b'{"a":NaN}'):
            with self.assertRaises(common.Error): common.decode_json(raw)


class ExistingOwnerIntegrationTests(unittest.TestCase):
    def test_real_bounded_git_owner_version_and_worktree_head(self):
        git = prepare._git_executable(shutil.which('git'))
        observed = prepare._git(git, REPO, '--version')
        self.assertTrue(observed.startswith(b'git version '))
        head = prepare._git(git, REPO, 'rev-parse', 'HEAD')
        self.assertRegex(head.decode(), r'^[0-9a-f]{40}\n$')
        reference = subprocess.run([git, '-C', str(REPO), 'rev-parse', 'HEAD'], check=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
        self.assertEqual(head, reference)


class TreeTests(unittest.TestCase):
    def test_reconstruction_includes_gitlink_and_executable_mode(self):
        rows = [('file', '100644', blob(b'x')), ('run', '100755', blob(b'run')),
                ('vendor', '160000', '1' * 40)]
        entries = prepare.tree_entries(listing(rows))
        raw = b''.join(mode.encode() + b' ' + path.encode() + b'\0' + bytes.fromhex(oid)
                       for path, mode, oid in rows)
        self.assertEqual(prepare.tree_identity(entries), hashlib.sha1(f'tree {len(raw)}\0'.encode() + raw).hexdigest())
        self.assertNotEqual(prepare.tree_identity(entries), prepare.tree_identity({p: r for p, r in entries.items() if p != 'vendor'}))

    def test_links_aliases_parent_conflicts_and_duplicate_paths_rejected(self):
        cases = [[('link', '120000', '1' * 40)], [('File', '100644', '1' * 40), ('file', '100644', '2' * 40)],
                 [('e\u0301', '100644', '1' * 40), ('é', '100644', '2' * 40)],
                 [('file', '100644', '1' * 40), ('file/child', '100644', '2' * 40)],
                 [('../escape', '100644', '1' * 40)], [('x', '100644', '1' * 40), ('x', '100644', '2' * 40)]]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(common.Error): prepare.tree_entries(listing(rows))

    def test_incomplete_mount_or_wrong_mounted_commit_rejected(self):
        context = {'components': {'root': {}, 'dep': {'commit': '1' * 40}},
                   'mounts': [{'parent': 'root', 'component': 'dep', 'path': 'vendor', 'commit': '1' * 40, 'status': 'enabled'}]}
        entries = prepare.tree_entries(listing([('vendor', '160000', '1' * 40)]))
        prepare.check_mount_tree('root', entries, context)
        context['mounts'][0]['commit'] = '2' * 40
        with self.assertRaises(common.Error): prepare.check_mount_tree('root', entries, context)
        context['mounts'][0]['commit'] = '1' * 40; context['components']['dep']['commit'] = '2' * 40
        with self.assertRaises(common.Error): prepare.check_mount_tree('root', entries, context)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); self.root = Path(self.tmp.name)

    def archive(self, rows):
        path = self.root / 'input.tar'
        with tarfile.open(path, 'w') as archive:
            for name, data, kind, mode in rows:
                info = tarfile.TarInfo(name); info.mode = mode; info.mtime = 123456789
                info.type = kind; info.size = len(data) if kind == tarfile.REGTYPE else 0
                if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE): info.linkname = '../escape'
                archive.addfile(info, io.BytesIO(data) if info.size else None)
        return path

    def test_git_blob_mode_and_mtime_preserved_gitlink_placeholder_not_extracted(self):
        data = b'original owned source\n'; expected = {'dir/run': {'mode': '100755', 'git_object': blob(data)},
                                                       'vendor': {'mode': '160000', 'git_object': '1' * 40}}
        path = self.archive([('dir', b'', tarfile.DIRTYPE, 0o755), ('dir/run', data, tarfile.REGTYPE, 0o755),
                             ('vendor', b'', tarfile.DIRTYPE, 0o755)])
        old_mask = os.umask(0o077)
        try: rows, total = prepare.extract_verified(path, self.root / 'out', expected)
        finally: os.umask(old_mask)
        self.assertEqual(total, len(data)); self.assertEqual(rows[0]['git_blob'], blob(data))
        self.assertEqual((self.root / 'out/dir/run').stat().st_mode & 0o777, 0o755)
        self.assertEqual((self.root / 'out/dir/run').stat().st_mtime_ns, 123456789000000000)
        self.assertFalse((self.root / 'out/vendor').exists())

    def test_unsafe_archive_members_duplicate_missing_or_changed_payload_rejected(self):
        expected = {'x': {'mode': '100644', 'git_object': blob(b'ok')}}
        cases = [[('x', b'ok', tarfile.SYMTYPE, 0o644)], [('x', b'ok', tarfile.LNKTYPE, 0o644)],
                 [('../x', b'ok', tarfile.REGTYPE, 0o644)], [('x', b'ok', tarfile.REGTYPE, 0o666)],
                 [('x', b'changed', tarfile.REGTYPE, 0o644)], [],
                 [('x', b'ok', tarfile.REGTYPE, 0o644), ('x', b'ok', tarfile.REGTYPE, 0o644)]]
        for i, rows in enumerate(cases):
            with self.subTest(i=i), self.assertRaises(common.Error):
                prepare.extract_verified(self.archive(rows), self.root / str(i), expected)

    def test_executable_mode_mismatch_rejected(self):
        path = self.archive([('x', b'ok', tarfile.REGTYPE, 0o644)])
        with self.assertRaises(common.Error):
            prepare.extract_verified(path, self.root / 'out', {'x': {'mode': '100755', 'git_object': blob(b'ok')}})

    def test_selected_git_symlink_resolves_to_exact_regular_tool(self):
        actual = self.root / 'git-real'; actual.write_bytes(b'original owned fixture tool')
        alias = self.root / 'git-alias'; alias.symlink_to(actual)
        selected = prepare._git_executable(str(alias))
        self.assertEqual(selected, str(actual.resolve()))
        self.assertEqual(common.sha256(selected), hashlib.sha256(actual.read_bytes()).hexdigest())
        with self.assertRaises(common.Error): prepare._git_executable(self.root / 'missing')

    def test_output_scoped_fresh_and_no_symlink(self):
        allowed = common.operation_output('.build/task5/fixture', repo_root=self.root)
        (allowed / 'preserved').write_text('keep')
        with self.assertRaises(common.Error): common.operation_output(allowed, repo_root=self.root)
        for path in ['.build/task4/x', '.build/task5/../escape', '/private/tmp/arbitrary']:
            with self.assertRaises(common.Error): common.operation_output(path, repo_root=self.root)
        (self.root / '.build/task5/link').symlink_to(allowed, target_is_directory=True)
        with self.assertRaises(common.Error): common.operation_output('.build/task5/link', repo_root=self.root)

    def test_source_walk_rejects_extra_links_and_hardlink_aliases(self):
        (self.root / 'sources/fex').mkdir(parents=True)
        (self.root / 'sources/fex/a').write_text('owned')
        os.link(self.root / 'sources/fex/a', self.root / 'sources/fex/b')
        with self.assertRaises(common.Error): prepare._source_files(self.root)
        (self.root / 'sources/fex/b').unlink(); (self.root / 'sources/fex/b').symlink_to('a')
        with self.assertRaises(common.Error): prepare._source_files(self.root)


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); self.root = Path(self.tmp.name)
        names = ['SetHardwareTSOControl', 'SetKernelUnalignedAtomicControl', 'Madvise', 'SetVMAName',
                 'GetSHMStatsVMA', 'DeleteSHMStatsFile', 'MapFile', 'GetPID']
        header = 'enum class FEXUnixLibFunctions : uint32_t {' + ','.join(names + ['MAX']) + '};\n'
        structs = [('SetHardwareTSOControlArgs', 'bool Enable;', 1), ('SetKernelUnalignedAtomicControl', 'uint64_t Flags;', 8),
                   ('Madvise', 'const void* Addr; size_t Size; int32_t Advise; uint32_t pad;', 24),
                   ('SetVMAName', 'const void* Addr; size_t Size; const char* Name;', 24),
                   ('GetSHMStatsVMA', 'void* SHMBase; uint32_t MapSize; uint32_t MaxSize;', 16),
                   ('MapFile', 'int32_t FD; uint64_t MapSize; void* Result;', 24), ('GetPID', 'uint32_t Result;', 4)]
        for name, fields, size in structs:
            header += f'struct FEXUnixLib_{name} {{{fields}}};\nstatic_assert(sizeof(FEXUnixLib_{name}) == {size});\n'
        for path in prepare.INTERFACES:
            target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_text('// Original synthetic source fixture.\n')
        (self.root / 'Source/Windows/UnixLib/FEXUnixLib.h').write_text(header)
        (self.root / 'Source/Windows/UnixLib/FEXUnixLib.cpp').write_text('using NTSTATUS = int32_t; using unixlib_entry_t = NTSTATUS (*)(void*);\nconstexpr NTSTATUS STATUS_SUCCESS = 0;\nconstexpr NTSTATUS STATUS_NOT_SUPPORTED = 0xC00000BB;\nconstexpr NTSTATUS STATUS_INTERNAL_ERROR = 0xC00000E5;\n__wine_unix_call_funcs[] = {' + ','.join('FEXUnixLib_' + n + 'Handler' for n in names) + '};')
        for flavor, module in [('ARM64EC', 'arm64ec'), ('WOW64', 'wow64')]:
            (self.root / f'Source/Windows/{flavor}/lib{module}fex.def').write_text(f'LIBRARY lib{module}fex.dll\nEXPORTS\n  ProcessInit\n  BeginSimulation DATA\n')
        (self.root / 'Source/Windows/Common/FEXUnixLib.cpp').write_text('InitUnicodeString(L"libarm64ecfex"); InitUnicodeString(L"libwow64fex");\n')
        (self.root / 'Source/Windows/ARM64EC/Module.cpp').write_text('constexpr size_t TEBCPUAreaOffset = 0x1788;\n')
        (self.root / 'Source/Windows/ARM64EC/Module.S').write_text('ldr x0, [x18]\n')

    def test_contract_is_source_model_not_performed_abi_or_runtime(self):
        value = prepare.source_interfaces(self.root)
        self.assertEqual(value['observation'], 'source_inspected'); self.assertFalse(value['runtime_qualified'])
        self.assertEqual(value['teb_cpu_area_offset'], 0x1788)
        self.assertEqual(value['services'][6]['argument']['fields'][1]['offset'], 8)
        self.assertEqual(value['services'][6]['argument']['size'], 24)
        self.assertIsNone(value['services'][5]['argument'])
        self.assertTrue(all(s['live_status'] == 'unperformed' for s in value['services']))
        self.assertEqual(value['modules'][0]['exports'][1]['kind'], 'data')

    def test_changed_handler_order_or_argument_declaration_cannot_pass(self):
        path = self.root / 'Source/Windows/UnixLib/FEXUnixLib.cpp'; original = path.read_text()
        path.write_text(original.replace('FEXUnixLib_GetPIDHandler', 'FEXUnixLib_MadviseHandler'))
        with self.assertRaises(common.Error): prepare.source_interfaces(self.root)
        path.write_text(original)
        path = self.root / 'Source/Windows/UnixLib/FEXUnixLib.h'; path.write_text(path.read_text().replace('uint64_t MapSize;', 'uint32_t MapSize;'))
        with self.assertRaises(common.Error): prepare.source_interfaces(self.root)


if __name__ == '__main__': unittest.main()
