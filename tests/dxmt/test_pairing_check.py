"""Original offline refusal controls; metadata bytes are never executed."""
import copy
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools/dxmt'))
spec = importlib.util.spec_from_file_location('_pear_dxmt_pairing_reader_tests', REPO / 'tools/dxmt/pairing_check.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
fixture_spec = importlib.util.spec_from_file_location('_pear_dxmt_pairing_metadata_fixtures', REPO / 'tests/dxmt/test_artifact_pairing.py')
metadata = importlib.util.module_from_spec(fixture_spec)
fixture_spec.loader.exec_module(metadata)
from common import Error, digest, encoded


def uleb(value):
    result = bytearray()
    while value >= 128:
        result.append((value & 127) | 128); value >>= 7
    result.append(value)
    return bytes(result)


def export_image(symbol=reader.GETTER, flags=0, address=1, command=0x80000033):
    """Mach-O/export metadata only: no code, sections or executable payload."""
    edge = symbol.encode() + b'\0'
    child = 2 + len(edge) + 1
    terminal = uleb(flags) + uleb(address)
    trie = b'\0\1' + edge + uleb(child) + uleb(len(terminal)) + terminal + b'\0'
    size = 16 if command == 0x80000033 else 48
    if size == 16:
        load = struct.pack('<4I', command, size, 32 + size, len(trie))
    else:
        load = struct.pack('<12I', command, size, *([0] * 8), 32 + size, len(trie))
    return struct.pack('<8I', 0xfeedfacf, reader.MACH_ARM64, 0, 6, 1, size, 0, 0) + load + trie


class PairingReaderControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pear-dxmt-pair-reader-')
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def put(self, path, data, root=None):
        target = (root or self.root) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data); target.chmod(0o644)
        return target

    def test_complete_inventory_reader_has_a_closed_local_budget(self):
        # Data-only inventory sized like the complete source projection.
        raw = encoded({"files": [0] * 251790})
        self.assertEqual(len(reader.decode_pair_build(raw)["files"]), 251790)
        with self.assertRaisesRegex(Error, "json_structure_limit"):
            reader.decode_pair_build(encoded({"files": [0] * 300001}))
        with self.assertRaisesRegex(Error, "input_size_limit"):
            reader.decode_pair_build(b" " * (8 * 1024**2 + 1))
        for malformed in (b'{"x":1,"x":2}', b"[1.5]", b"[NaN]"):
            with self.assertRaises(Error):
                reader.decode_pair_build(malformed)

    def test_output_monitor_admits_only_source_bound_generated_locale_link(self):
        import os
        source = self.put('wine/source/nls/locale.nls', b'exact locale metadata')
        link = self.root / reader.pairing_monitor.LINK
        link.parent.mkdir(parents=True)
        link.symlink_to(reader.pairing_monitor.TARGET)
        with mock.patch.object(reader.pairing_monitor, 'LOCALE_SHA256', digest(source.read_bytes())):
            self.assertGreaterEqual(reader.pairing_monitor.directory_usage(self.root), 0)
            source.write_bytes(b'changed selected locale')
            with self.assertRaisesRegex(Error, 'pair_monitor_locale_target'):
                reader.pairing_monitor.directory_usage(self.root)
        link.unlink()
        link.symlink_to('../../../wine/source/nls/locale.nls')
        with self.assertRaisesRegex(Error, 'pair_monitor_unlisted_alias'):
            reader.pairing_monitor.directory_usage(self.root)

    def test_output_monitor_refuses_directory_other_leaf_and_special_aliases(self):
        import os
        target = self.put('ordinary', b'non executable metadata')
        for path, directory in [('other-link', False), ('directory-link', True)]:
            link = self.root / path
            link.symlink_to(self.root if directory else target, target_is_directory=directory)
            with self.assertRaises(Error):
                reader.pairing_monitor.directory_usage(self.root)
            link.unlink()
        fifo = self.root / 'pipe'
        os.mkfifo(fifo)
        with self.assertRaisesRegex(Error, 'pair_monitor_special_output'):
            reader.pairing_monitor.directory_usage(self.root)

    def test_getter_requires_actual_export_trie_membership(self):
        result = reader.export_terminal(export_image(), reader.GETTER)
        self.assertEqual(result, {'name': reader.GETTER, 'kind': 'regular_defined', 'exported': True})
        with self.assertRaises(Error):
            reader.export_terminal(export_image(symbol='_other_private_getter'), reader.GETTER)
        # A visible-looking nlist symbol alone cannot pass dlsym admission.
        with self.assertRaises(Error):
            reader.export_terminal(metadata.macho_image('winemac.so', symbols=(reader.GETTER,)), reader.GETTER)

    def test_both_supported_dyld_info_forms_are_parsed(self):
        for command in [0x22, 0x80000022, 0x80000033]:
            with self.subTest(command=command):
                self.assertTrue(reader.export_terminal(export_image(command=command), reader.GETTER)['exported'])

    def test_reexport_resolver_weak_and_zero_export_refuse(self):
        for flags, address in [(1, 1), (2, 1), (4, 1), (8, 1), (16, 1), (0, 0)]:
            with self.subTest(flags=flags, address=address):
                with self.assertRaises(Error):
                    reader.export_terminal(export_image(flags=flags, address=address), reader.GETTER)

    def test_export_bounds_wrong_machine_cycle_and_nonminimal_uleb_refuse(self):
        for change in ['cpu', 'filetype', 'command_span', 'trie_length', 'cycle']:
            raw = bytearray(export_image())
            if change == 'cpu': struct.pack_into('<I', raw, 4, 0x1000007)
            elif change == 'filetype': struct.pack_into('<I', raw, 12, 2)
            elif change == 'command_span': struct.pack_into('<I', raw, 20, 17)
            elif change == 'trie_length': struct.pack_into('<I', raw, 44, len(raw))
            else: raw[48 + 2 + len(reader.GETTER) + 1] = 0
            with self.subTest(change=change), self.assertRaises(Error):
                reader.export_terminal(bytes(raw), reader.GETTER)
        for value in [b'\x80\x00', b'\x80' * 10, b'\xff' * 9 + b'\x02']:
            with self.subTest(value=value), self.assertRaises(Error):
                reader.read_uleb(value, 0, len(value))

    def command(self):
        logs = {}
        for stream in ['stdout', 'stderr']:
            raw = (stream + '\n').encode()
            path = 'logs/native.control/' + stream
            self.put(path, raw)
            logs[stream] = {'path': path, 'sha256': digest(raw), 'size_bytes': len(raw)}
        return {'id': 'native.control', 'argv': ['owned-tool', '--bounded'], 'cwd': str(self.root),
                'environment': {'PATH': '/owned/tools'}, 'exit_code': 0, 'elapsed_ms': 1,
                'stop_reason': None, 'growth_bytes_observed': 2, 'logs': logs}

    def test_command_replay_binds_recipe_environment_current_logs_and_order(self):
        row = self.command()
        recipes = {'native.control': (row['argv'], self.root, row['environment'], 60)}
        policy = {'growth_ceiling_bytes': 100}
        reader.command_rows(self.root, [row], recipes, policy)
        for field, value in [('argv', ['other-tool']), ('cwd', '/other'), ('environment', {}),
                             ('exit_code', False), ('stop_reason', 'timeout'), ('elapsed_ms', -1),
                             ('growth_bytes_observed', 101)]:
            changed = copy.deepcopy(row); changed[field] = value
            with self.subTest(field=field), self.assertRaises(Error):
                reader.command_rows(self.root, [changed], recipes, policy)
        with self.assertRaises(Error): reader.command_rows(self.root, [row, row], recipes, policy)
        self.put('logs/native.control/stderr', b'changed actual stream')
        with self.assertRaises(Error): reader.command_rows(self.root, [row], recipes, policy)

    def test_record_rejects_false_qualification_and_unknown_extensions(self):
        value = {key: None for key in reader.BUILD_FIELDS}
        value.update(schema_version=1, record_kind='dxmt_pairing_build',
                     scope='typed_native_metal_pairing', passed=True)
        for name in reader.RUNTIME_FLAGS: value[name] = False
        reader.record(value)
        for name in reader.RUNTIME_FLAGS:
            changed = dict(value); changed[name] = True
            with self.subTest(name=name), self.assertRaises(Error): reader.record(changed)
        changed = dict(value); changed['native_execution'] = 0
        with self.assertRaises(Error): reader.record(changed)
        changed = dict(value); changed['extra_runtime_claim'] = True
        with self.assertRaises(Error): reader.record(changed)

    def test_full_source_projection_rejects_unchanged_or_modified_file_tamper(self):
        baseline = self.root / 'baseline'; baseline.mkdir()
        before = b'first\nlast\n'; after = b'first\nreplacement\n'
        self.put('changed.c', before, baseline); self.put('unchanged.c', b'original\n', baseline)
        changed = self.root / 'wine/source'; changed.mkdir(parents=True)
        self.put('changed.c', after, changed); self.put('unchanged.c', b'original\n', changed)
        declaration = [{'path': 'changed.c', 'before_sha256': digest(before), 'after_sha256': digest(after),
                        'mode': '100644', 'payload_file': None, 'payload_sha256': None}]
        sections = {'changed.c': ['--- a/changed.c\n', '+++ b/changed.c\n', '@@ -1,2 +1,2 @@\n',
                                 ' first\n', '-last\n', '+replacement\n']}
        facts = {'baseline': str(baseline), 'before_files': reader.tools.files(baseline),
                 'after_files': reader.tools.files(changed)}
        reader.source_projection(self.root, 'wine', baseline, facts, (declaration, sections))
        self.put('unchanged.c', b'tampered\n', changed)
        with self.assertRaises(Error): reader.source_projection(self.root, 'wine', baseline, facts, (declaration, sections))
        self.put('unchanged.c', b'original\n', changed); self.put('changed.c', before, changed)
        with self.assertRaises(Error): reader.source_projection(self.root, 'wine', baseline, facts, (declaration, sections))

    def test_source_projection_rejects_alias_instead_of_following_it(self):
        baseline = self.root / 'baseline'; baseline.mkdir()
        self.put('original.c', b'owned\n', baseline)
        changed = self.root / 'wine/source'; changed.mkdir(parents=True)
        (changed / 'original.c').symlink_to(baseline / 'original.c')
        facts = {'baseline': str(baseline), 'before_files': reader.tools.files(baseline), 'after_files': []}
        with self.assertRaises(Error): reader.source_projection(self.root, 'wine', baseline, facts, ([], {}))

    def test_snapshot_set_and_current_bytes_must_both_match(self):
        repo = self.root / 'repo'; repo.mkdir()
        names = ['tools/owned.py', 'tools/inherited.py']
        hashes = {}
        for name in names:
            raw = (name + '\n').encode(); hashes[name] = digest(raw)
            self.put(name, raw, repo); self.put('producers/' + name, raw)
        value = {'producers': {names[0]: hashes[names[0]]},
                 'inherited_producers': {names[1]: hashes[names[1]]}, 'producer_files': hashes}
        with mock.patch.object(reader.builder, 'PRODUCERS', [names[0]]), \
             mock.patch.object(reader.stage3, 'producers', return_value=value['inherited_producers']):
            reader.producer_copies(self.root, value, repo)
            self.put('producers/extra.py', b'unaccounted')
            with self.assertRaises(Error): reader.producer_copies(self.root, value, repo)
            (self.root / 'producers/extra.py').unlink()
            self.put('producers/' + names[0], b'changed')
            with self.assertRaises(Error): reader.producer_copies(self.root, value, repo)

    def test_ordinary_driver_control_requires_native_metadata_and_real_export(self):
        raw = bytearray(metadata.pe_image({'PearMetalPairingControl': 1}))
        struct.pack_into('<II', raw, 264 + 10 * 8, 0, 0)  # no CHPE/load-config
        facts = reader.ordinary_pe(bytes(raw), False, metadata.inspector)
        self.assertFalse(facts['hybrid_metadata_present'])
        with self.assertRaises(Error):
            reader.ordinary_pe(metadata.pe_image({'PearMetalPairingControl': 1}), False, metadata.inspector)
        missing = bytearray(metadata.pe_image({'AnotherControl': 1}))
        struct.pack_into('<II', missing, 264 + 10 * 8, 0, 0)
        with self.assertRaises(Error): reader.ordinary_pe(bytes(missing), False, metadata.inspector)

    def test_fixture_inputs_require_exact_owned_copies_and_pinned_declarations(self):
        repo = self.root / 'repo'; repo.mkdir()
        expected = {}
        for path in reader.FIXTURE_PATHS:
            raw = (path + '\n').encode(); expected[path] = digest(raw)
            self.put(path, raw, repo); self.put('inputs/' + path, raw)
            if '/upstream/' in path:
                self.put('dxmt/source/src/winemetal/' + Path(path).name, raw)
        value = {'fixture_sources': expected}
        reader.fixture_copies(self.root, value, repo)
        self.put('inputs/unknown.c', b'unaccounted source')
        with self.assertRaises(Error): reader.fixture_copies(self.root, value, repo)
        (self.root / 'inputs/unknown.c').unlink()
        self.put('dxmt/source/src/winemetal/winemetal_thunks.h', b'different ABI declarations')
        with self.assertRaises(Error): reader.fixture_copies(self.root, value, repo)

    def layout(self):
        expected, selected = [], []
        for path, role in metadata.inspector.WINE_LAYOUT.items():
            name = Path(path).name
            if name.endswith('.a'):
                raw, mode = metadata.dual_archive(), 0o644
            elif name == 'winebuild':
                raw, mode = metadata.macho_image(name, filetype=2), 0o755
            else:
                dependencies = ('@rpath/ntdll.so', '@rpath/win32u.so') if name == 'winemac.so' else \
                    (('@rpath/ntdll.so',) if name == 'win32u.so' else ('/usr/lib/libSystem.B.dylib',))
                raw, mode = metadata.macho_image(name, dependencies=dependencies), 0o755
            target = self.put('dxmt/' + path, raw); target.chmod(mode)
            _, fact = metadata.inspector.file_bytes(self.root / 'dxmt', path)
            row = {**fact, 'origin_role': role, 'origin_path': path.removeprefix('wine-layout/')}
            expected.append(row); selected.append(dict(row))
            if name == 'winemac.so':
                replacement = metadata.macho_image(name, dependencies=dependencies, symbols=('__different_build_metadata',))
                rebuilt = self.put(reader.REBUILT_DRIVER, replacement); rebuilt.chmod(0o755)
                target.write_bytes(replacement)
                _, current = metadata.inspector.file_bytes(self.root, reader.REBUILT_DRIVER)
                selected[-1] = {**current, 'path': path, 'origin_role': 'rebuilt-native',
                                'origin_path': reader.REBUILT_DRIVER}
        return expected, selected

    def test_rebuilt_layout_origin_and_actual_dependency_closure_are_required(self):
        expected, selected = self.layout()
        observed, counterparts = reader.paired_layout(self.root, selected, expected, metadata.inspector)
        self.assertEqual(set(counterparts), {'winemac.so', 'win32u.so', 'ntdll.so'})
        driver = next(row for row in observed if row['path'].endswith('/winemac.so'))
        self.assertEqual(driver['origin_role'], 'rebuilt-native')
        self.assertEqual(len(driver['dependency_closure']), 2)
        changed = copy.deepcopy(selected)
        next(row for row in changed if row['path'].endswith('/winemac.so'))['origin_role'] = 'native'
        with self.assertRaises(Error): reader.paired_layout(self.root, changed, expected, metadata.inspector)
        self.put('dxmt/wine-layout/unaccounted.so', b'unaccounted')
        with self.assertRaises(Error): reader.paired_layout(self.root, selected, expected, metadata.inspector)

    def test_layout_refuses_missing_changed_and_aliased_counterparts(self):
        expected, selected = self.layout()
        with self.assertRaises(Error): reader.paired_layout(self.root, selected[:-1], expected, metadata.inspector)
        path = self.root / 'dxmt/wine-layout/lib/wine/aarch64-unix/ntdll.so'
        original = path.read_bytes(); path.write_bytes(b'changed')
        with self.assertRaises(Error): reader.paired_layout(self.root, selected, expected, metadata.inspector)
        path.write_bytes(original); path.unlink()
        alternate = self.put('other-ntdll-metadata', original)
        path.symlink_to(alternate)
        with self.assertRaises(Error): reader.paired_layout(self.root, selected, expected, metadata.inspector)

    def test_failed_build_is_refused_before_prerequisite_or_native_work(self):
        repo = self.root / 'repo'; root = repo / '.build/task7/failed'
        root.mkdir(parents=True); self.put('.build/task7/failed/failed.json', b'{}', repo)
        with mock.patch.object(reader.stage3, 'verify_build', side_effect=AssertionError('must not reach source replay')):
            with self.assertRaises(Error) as result: reader.verify_build(root, repo=repo)
        self.assertEqual(result.exception.code, 'pair_failed_build')

    def test_current_wine_records_are_bound_to_the_qualified_original_recipe(self):
        repo = self.root / 'repo'; repo.mkdir()
        old = {}
        for name, key in [('inputs', 'inputs_sha256'), ('toolchain', 'toolchain_lock_sha256'),
                          ('build-config', 'config_sha256')]:
            raw = encoded({'selected': name}); self.put('runtime/wine/' + name + '.json', raw, repo)
            old[key] = digest(raw)
        lock, config = reader.wine_inputs(old, repo)
        self.assertEqual(lock['selected'], 'toolchain'); self.assertEqual(config['selected'], 'build-config')
        self.put('runtime/wine/build-config.json', encoded({'selected': 'changed configure options'}), repo)
        with self.assertRaises(Error): reader.wine_inputs(old, repo)

    def test_locked_external_tool_alias_is_explicit_and_canonical_bytes_are_bound(self):
        # In-memory/header-only metadata is written as data and never executed.
        target = self.put('apple-clang-tool-metadata', metadata.macho_image('tool', filetype=2))
        alias = self.root / 'clang++'; alias.symlink_to(target.name)
        lock = {'native_tools': [{'id': 'clang++', 'path': str(alias), 'sha256': digest(target.read_bytes())}]}
        self.assertEqual(reader.external_native_tools(lock), [{'id': 'clang++', 'path': str(alias),
            'resolved_path': str(target), 'sha256': lock['native_tools'][0]['sha256']}])
        target.write_bytes(metadata.macho_image('different tool metadata', filetype=2))
        with self.assertRaises(Error): reader.external_native_tools(lock)


if __name__ == '__main__':
    unittest.main()
