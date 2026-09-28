"""Module inventory tests use synthetic PE bytes and never execute a guest."""
import copy
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
from common import Error, encoded, sha256
import modules


def image():
    data = bytearray(4096)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 128)
    data[128:132] = b'PE\0\0'
    struct.pack_into('<HH', data, 132, 0xaa64, 1)
    struct.pack_into('<H', data, 148, 240)
    struct.pack_into('<H', data, 152, 0x20b)
    struct.pack_into('<Q', data, 176, 0x180000000)
    struct.pack_into('<I', data, 208, 0x2000)
    struct.pack_into('<I', data, 212, 512)
    struct.pack_into('<I', data, 260, 16)
    data[392:400] = b'.rdata\0\0'
    struct.pack_into('<IIII', data, 400, 3584, 0x1000, 3584, 512)
    struct.pack_into('<I', data, 428, 0x40000040)
    return data


def directory(data, index, rva, size):
    struct.pack_into('<II', data, 264 + index * 8, rva, size)


def at(rva):
    return 512 + rva - 0x1000


def exported(data, forward=False):
    directory(data, 0, 0x1000, 0x100)
    struct.pack_into('<6I', data, at(0x1000) + 16, 1, 1, 1, 0x1040, 0x1048, 0x1050)
    struct.pack_into('<I', data, at(0x1040), 0x1080 if forward else 0x1600)
    struct.pack_into('<I', data, at(0x1048), 0x1060)
    struct.pack_into('<H', data, at(0x1050), 0)
    data[at(0x1060):at(0x1060) + 7] = b'Export\0'
    if forward:
        data[at(0x1080):at(0x1080) + 13] = b'NTDLL.Target\0'


def hybrid(data):
    struct.pack_into('<I', data, 428, 0x60000020)
    directory(data, 10, 0x1200, 0x140)
    struct.pack_into('<I', data, at(0x1200), 0x140)
    struct.pack_into('<Q', data, at(0x1200) + 0xc8, 0x180001400)
    struct.pack_into('<IH', data, at(0x1200) + 0xe0, 0x480, 1)
    struct.pack_into('<3I', data, at(0x1400), 2, 0x1440, 2)
    struct.pack_into('<4I', data, at(0x1440), 0x1600, 4, 0x1611, 4)
    struct.pack_into('<II', data, at(0x1480), 1, 24)
    struct.pack_into('<QI', data, at(0x1488), 6, 12)
    struct.pack_into('<IIHH', data, at(0x1494), 0, 12, 0x5084, 0x8664)


class BinaryTests(unittest.TestCase):
    def test_empty_import_and_export_tables_are_valid(self):
        facts = modules.inspect_pe(bytes(image()))
        self.assertEqual((facts['imports'], facts['delay_imports'], facts['exports']), ([], [], []))

    def test_import_and_delay_import_are_separate(self):
        data = image()
        directory(data, 1, 0x1100, 40)
        struct.pack_into('<5I', data, at(0x1100), 0, 0, 0, 0x1180, 0)
        data[at(0x1180):at(0x1180) + 10] = b'first.dll\0'
        directory(data, 13, 0x1140, 64)
        struct.pack_into('<8I', data, at(0x1140), 1, 0x11a0, 0, 0, 0, 0, 0, 0)
        data[at(0x11a0):at(0x11a0) + 9] = b'late.dll\0'
        facts = modules.inspect_pe(bytes(data))
        self.assertEqual(facts['imports'], ['first.dll'])
        self.assertEqual(facts['delay_imports'], ['late.dll'])

    def test_missing_import_terminator_rejected(self):
        data = image()
        directory(data, 1, 0x1100, 20)
        struct.pack_into('<5I', data, at(0x1100), 0, 0, 0, 0x1180, 0)
        with self.assertRaisesRegex(Error, 'module_import_terminator'):
            modules.inspect_pe(bytes(data))

    def test_forwarded_exports_are_not_code_addresses(self):
        data = image()
        exported(data, True)
        self.assertEqual(modules.inspect_pe(bytes(data))['exports'][0]['forwarder'], 'NTDLL.Target')

    def test_export_ordinal_outside_table_rejected(self):
        data = image()
        exported(data)
        struct.pack_into('<H', data, at(0x1050), 1)
        with self.assertRaisesRegex(Error, 'module_export_name_ordinal'):
            modules.inspect_pe(bytes(data))

    def test_header_alone_does_not_prove_hybrid(self):
        with self.assertRaisesRegex(Error, 'module_arm64x_metadata_missing'):
            modules.require_hybrid(modules.inspect_pe(bytes(image())))

    def test_hybrid_requires_chpe_and_machine_dynamic_fixup(self):
        data = image()
        hybrid(data)
        modules.require_hybrid(modules.inspect_pe(bytes(data)))
        struct.pack_into('<H', data, at(0x1494) + 10, 0xaa64)
        with self.assertRaisesRegex(Error, 'module_arm64x_metadata_missing'):
            modules.require_hybrid(modules.inspect_pe(bytes(data)))

    def test_zero_chpe_cannot_qualify_hybrid(self):
        data = image()
        hybrid(data)
        struct.pack_into('<Q', data, at(0x1200) + 0xc8, 0)
        with self.assertRaisesRegex(Error, 'module_arm64x_metadata_missing'):
            modules.require_hybrid(modules.inspect_pe(bytes(data)))

    def test_hybrid_requires_both_native_and_ec_code_ranges(self):
        data = image()
        hybrid(data)
        struct.pack_into('<I', data, at(0x1440), 0x1601)
        with self.assertRaisesRegex(Error, 'module_arm64x_code_ranges_missing'):
            modules.require_hybrid(modules.inspect_pe(bytes(data)))

    def test_unmapped_chpe_code_range_rejected(self):
        data = image()
        hybrid(data)
        struct.pack_into('<I', data, at(0x1440) + 4, 0x100000)
        with self.assertRaisesRegex(Error, 'module_chpe_range_bounds'):
            modules.inspect_pe(bytes(data))

    def test_chpe_range_can_span_adjacent_executable_sections_and_padding(self):
        data = image()
        hybrid(data)
        struct.pack_into('<H', data, 134, 2)
        struct.pack_into('<II', data, 400, 0x340, 0x1000)
        struct.pack_into('<I', data, 408, 0x400)
        data[432:440] = b'.hexpthk'
        struct.pack_into('<IIII', data, 440, 0xa00, 0x1400, 0xa00, 1536)
        struct.pack_into('<I', data, 468, 0x60000020)
        struct.pack_into('<II', data, at(0x1440), 0x1300, 0x200)
        modules.require_hybrid(modules.inspect_pe(bytes(data)))
        struct.pack_into('<I', data, 468, 0x40000040)
        with self.assertRaisesRegex(Error, 'module_chpe_range_unmapped'):
            modules.inspect_pe(bytes(data))

    def test_malformed_dynamic_block_rejected(self):
        data = image()
        hybrid(data)
        struct.pack_into('<I', data, at(0x1494) + 4, 0)
        with self.assertRaisesRegex(Error, 'module_dynamic_block'):
            modules.inspect_pe(bytes(data))

    def test_duplicate_mapping_is_rejected(self):
        data = image()
        exported(data)
        struct.pack_into('<H', data, 134, 2)
        data[432:472] = data[392:432]
        with self.assertRaisesRegex(Error, 'module_unmapped_or_ambiguous_rva'):
            modules.inspect_pe(bytes(data))

    def test_truncated_section_rejected(self):
        with self.assertRaisesRegex(Error, 'module_section_bounds'):
            modules.inspect_pe(bytes(image()[:-1]))

    def test_wrong_native_view_machine_rejected(self):
        data = image()
        struct.pack_into('<H', data, 132, 0x8664)
        with self.assertRaisesRegex(Error, 'module_native_view_machine'):
            modules.inspect_pe(bytes(data))


class TextTests(unittest.TestCase):
    def test_llvm_semantic_arm64x_header_requires_binary_metadata(self):
        data = image()
        hybrid(data)
        facts = modules.inspect_pe(bytes(data))
        text = ('\nFile: /fixture.dll\n  Machine: IMAGE_FILE_MACHINE_ARM64X (0xA64E)\n'
                '  CHPEMetadataPointer: 0x180001400\nDynamicRelocations [\nArm64X [\n')
        modules.assess_readobj(text, facts, Path('/fixture.dll'))
        with self.assertRaisesRegex(Error, 'module_tool_machine'):
            modules.assess_readobj(text, modules.inspect_pe(bytes(image())), Path('/fixture.dll'))
        with self.assertRaisesRegex(Error, 'module_tool_machine'):
            modules.assess_readobj(text.replace('A64E', 'AA64'), facts, Path('/fixture.dll'))

    def test_forwarded_export_crosscheck(self):
        data = image()
        exported(data, True)
        text = ('\nFile: /fixture.dll\n  Machine: IMAGE_FILE_MACHINE_ARM64 (0xAA64)\n'
                'Export {\n  Ordinal: 1\n  Name: Export\n  ForwardedTo: NTDLL.Target\n}\n')
        facts = modules.inspect_pe(bytes(data))
        modules.assess_readobj(text, facts, Path('/fixture.dll'))
        with self.assertRaisesRegex(Error, 'module_tool_exports'):
            modules.assess_readobj(text.replace('NTDLL.Target', 'NTDLL.Other'), facts, Path('/fixture.dll'))

    def test_extra_file_output_rejected(self):
        facts = modules.inspect_pe(bytes(image()))
        text = '\nFile: /fixture.dll\nFile: /other.dll\n  Machine: ARM64 (0xAA64)\n'
        with self.assertRaisesRegex(Error, 'module_tool_file_identity'):
            modules.assess_readobj(text, facts, Path('/fixture.dll'))


class InventoryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.built = {'passed': True, 'variant': 'arm64'}
        (self.root / 'build.json').write_bytes(encoded(self.built))
        self.report = {'schema_version': 1, 'record_kind': 'wine_module_inventory',
                       'coverage': 'selected_native_view_pe_modules', 'guest_execution': False,
                       'variant': 'arm64', 'build_sha256': sha256(self.root / 'build.json'),
                       'producer_sha256': {}, 'tool': {'path': '/readobj'},
                       'modules': [], 'commands': [], 'passed': True}
        self.work = self.root / 'modules.work'
        (self.work / '.pear-command-logs').mkdir(parents=True)
        for name in modules.NAMES:
            relative = 'lib/wine/aarch64-windows/' + name
            module = self.root / 'install' / relative
            module.parent.mkdir(parents=True, exist_ok=True)
            raw = bytes(image())
            module.write_bytes(raw)
            self.report['modules'].append({'path': relative, 'sha256': hashlib.sha256(raw).hexdigest(),
                                           'size_bytes': len(raw), 'facts': modules.inspect_pe(raw),
                                           'hybrid_required': False, 'command_id': name})
            cmd = {'id': name, 'cwd': str(self.work), 'exit_code': 0, 'timed_out': False,
                   'output_limit': False, 'argv': ['/usr/bin/arch', '-arm64', '/readobj', *modules.OPTIONS, str(module)]}
            for stream, text in [('stdout', '\nFile: ' + str(module) + '\n  Machine: ARM64 (0xAA64)\n'), ('stderr', '')]:
                raw = text.encode()
                log = self.work / '.pear-command-logs' / (name + '.' + stream)
                log.write_bytes(raw)
                cmd[stream + '_log'] = {'path': str(log), 'sha256': sha256(log), 'size_bytes': len(raw)}
                cmd[stream] = text
                cmd[stream + '_preview_truncated'] = False
            self.report['commands'].append(cmd)
        for target, replacement in [('task_path', lambda path: Path(path)), ('producers', lambda: {}),
                                    ('tool_identity', lambda built: {'path': '/readobj'})]:
            patcher = mock.patch.object(modules, target, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)

    def validate(self):
        (self.root / 'modules.json').write_bytes(encoded(self.report))
        return modules.validate_inventory(self.root, verified_build=self.built)

    def test_complete_synthetic_record_is_accepted(self):
        self.validate()

    def test_module_changed_after_inspection_rejected(self):
        path = self.root / 'install' / self.report['modules'][0]['path']
        raw = bytearray(path.read_bytes())
        raw[-1] = 1
        path.write_bytes(raw)
        with self.assertRaisesRegex(Error, 'module_bytes_or_facts_changed'):
            self.validate()

    def test_rehashed_forged_facts_rejected(self):
        self.report['modules'][0]['facts']['imports'] = ['invented.dll']
        with self.assertRaisesRegex(Error, 'module_bytes_or_facts_changed'):
            self.validate()

    def test_rehashed_log_with_wrong_observation_rejected(self):
        cmd = self.report['commands'][0]
        log = Path(cmd['stdout_log']['path'])
        text = log.read_text().replace('0xAA64', '0x8664')
        log.write_text(text)
        cmd['stdout_log'].update(sha256=sha256(log), size_bytes=log.stat().st_size)
        cmd['stdout'] = text
        with self.assertRaisesRegex(Error, 'module_tool_machine'):
            self.validate()

    def test_timeout_cannot_be_promoted_by_passed_flag(self):
        self.report['commands'][0]['timed_out'] = True
        with self.assertRaisesRegex(Error, 'module_command_outcome'):
            self.validate()

    def test_missing_or_reordered_modules_rejected(self):
        self.report['modules'].reverse()
        with self.assertRaisesRegex(Error, 'module_bytes_or_facts_changed'):
            self.validate()

    def test_wrong_tool_identity_rejected(self):
        self.report['tool']['path'] = '/unverified/tool'
        with self.assertRaisesRegex(Error, 'module_tool_changed'):
            self.validate()

    def test_duplicate_command_rejected(self):
        self.report['commands'][1] = copy.deepcopy(self.report['commands'][0])
        with self.assertRaisesRegex(Error, 'module_command_outcome'):
            self.validate()


@unittest.skipUnless(sys.platform == 'darwin', 'native ARM64 reader process tests require macOS')
class ReaderTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()

    def test_success_preserves_complete_log(self):
        rows = []
        modules.run_reader(rows, 'reader', ['/usr/bin/printf', 'observed\n'], self.root, {})
        self.assertEqual(rows[0]['stdout'], 'observed\n')
        self.assertEqual(Path(rows[0]['stdout_log']['path']).read_bytes(), b'observed\n')

    def test_timeout_is_a_failed_observation_with_owned_child_reaped(self):
        rows = []
        with self.assertRaisesRegex(Error, 'module_reader_failed'):
            modules.run_reader(rows, 'reader', ['/bin/sleep', '2'], self.root, {}, timeout=0.04)
        self.assertTrue(rows[0]['timed_out'])
        self.assertNotEqual(rows[0]['exit_code'], 0)

    def test_fast_exit_above_output_limit_still_fails_and_bounds_saved_log(self):
        rows = []
        with self.assertRaisesRegex(Error, 'module_reader_failed'):
            modules.run_reader(rows, 'reader', ['/usr/bin/head', '-c', str(modules.MAX_LOG + 1), '/dev/zero'],
                               self.root, {})
        self.assertTrue(rows[0]['output_limit'])
        self.assertEqual(Path(rows[0]['stdout_log']['path']).stat().st_size, modules.MAX_LOG)


if __name__ == '__main__':
    unittest.main()
