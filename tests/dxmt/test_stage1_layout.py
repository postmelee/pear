"""Owned output, contained files and bounded binary-format contracts."""
from pathlib import Path
import struct
import unittest
from support import Fixture
from common import (Error, MACH_ARM64, archive_machines, decode_json, macho_slices,
                    output_directory, read_relative, tree_entries)
import prepare

class Layout(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.addCleanup(self.f.close)

    def test_existing_destination_is_not_reused(self):
        output_directory('.build/task7/existing', self.f.root)
        with self.assertRaisesRegex(Error, 'destination_exists'):
            output_directory('.build/task7/existing', self.f.root)

    def test_task4_destination_is_not_generic_reuse(self):
        with self.assertRaisesRegex(Error, 'output_scope'):
            output_directory('.build/task4/other', self.f.root)

    def test_traversal_destination_is_refused(self):
        with self.assertRaisesRegex(Error, 'output_scope'):
            output_directory('.build/task7/../other', self.f.root)

    def test_symlink_output_parent_is_refused(self):
        build = self.f.root / '.build'
        build.mkdir()
        (build / 'task7').symlink_to(self.f.cache, target_is_directory=True)
        with self.assertRaisesRegex(Error, 'symlink_output'):
            output_directory('.build/task7/escape', self.f.root)

    def test_leaf_symlink_read_is_refused(self):
        (self.f.root / 'leaf').symlink_to(self.f.root / self.f.input_path)
        with self.assertRaises(OSError):
            read_relative(self.f.root, 'leaf')

    def test_materialized_symlink_is_refused(self):
        self.f.derive()
        root = self.f.root / '.build/task7/prepared'
        (root / 'source/dxmt/linked').symlink_to(self.f.root / self.f.input_path)
        with self.assertRaisesRegex(Error, 'materialized_file'):
            prepare.verify_prepared(root, self.f.root)

    def test_duplicate_json_key_is_refused(self):
        with self.assertRaisesRegex(Error, 'duplicate_json_key'):
            decode_json(b'{"a":1,"a":2}')

    def test_floating_point_json_is_refused(self):
        with self.assertRaisesRegex(Error, 'noninteger_json_number'):
            decode_json(b'{"a":1.5}')

    def test_json_byte_budget_is_enforced(self):
        with self.assertRaisesRegex(Error, 'input_size_limit'):
            decode_json(b'{"payload":"large"}', max_bytes=8)

    def test_listing_duplicate_and_symlink_modes_are_refused(self):
        blob = 'a' * 40
        for raw in [f'100644 blob {blob}\tx\0'.encode() * 2, f'120000 blob {blob}\tx\0'.encode()]:
            with self.assertRaises(Error):
                tree_entries(raw)

    def test_macho_actual_thin_arm64_header(self):
        p = self.f.root / 'native-header'
        p.write_bytes(b'\xcf\xfa\xed\xfe' + struct.pack('<7I', MACH_ARM64, 0, 2, 0, 0, 0, 0))
        self.assertEqual(macho_slices(p), [MACH_ARM64])

    def test_macho_wrong_fat_inner_cpu_is_refused(self):
        p = self.f.root / 'fat-header'
        outer = b'\xca\xfe\xba\xbe' + struct.pack('>I5I', 1, MACH_ARM64, 0, 28, 32, 0)
        inner = b'\xcf\xfa\xed\xfe' + struct.pack('<7I', 0x1000007, 0, 2, 0, 0, 0, 0)
        p.write_bytes(outer + inner)
        with self.assertRaisesRegex(Error, 'macho_slice_header'):
            macho_slices(p)

    def test_raw_arm64ec_import_header_machine_is_preserved(self):
        body = struct.pack('<HHHHIII', 0, 65535, 0, 0xa641, 0, 0, 0)
        header = b'original.obj/'.ljust(16) + b'0           ' + b'0     ' + b'0     ' + b'644     ' + str(len(body)).encode().ljust(10) + b'`\n'
        self.assertEqual(len(header), 60)
        self.assertEqual(archive_machines(b'!<arch>\n' + header + body), [0xa641])

    def test_truncated_archive_is_refused(self):
        with self.assertRaisesRegex(Error, 'archive_header'):
            archive_machines(b'!<arch>\n' + b'x')

    def test_literal_percent_allowed_only_for_nonmaterialized_git_metadata(self):
        from common import tree_entries
        raw = b'100644 blob ' + b'a' * 40 + b'\tpolly/ir_%for.cond\0'
        self.assertEqual(tree_entries(raw, metadata_only=True)[0]['path'], 'polly/ir_%for.cond')
        with self.assertRaisesRegex(Error, 'unsafe_path'):
            tree_entries(raw)

    def test_metadata_tree_name_still_refuses_literal_traversal(self):
        from common import tree_entries
        for name in [b'../escape', b'/absolute', b'folder/../escape', b'folder\\escape', b'uri:name']:
            raw = b'100644 blob ' + b'a' * 40 + b'\t' + name + b'\0'
            with self.assertRaisesRegex(Error, 'unsafe_path'):
                tree_entries(raw, metadata_only=True)

if __name__ == '__main__':
    unittest.main()
