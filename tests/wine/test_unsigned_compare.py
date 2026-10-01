"""Original format fixtures: metadata explanations cannot absorb code changes."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
from common import Error, encoded
import unsigned_compare as subject

OLD = b'/private/tmp/old-root/source/test.c'
NEW = b'/private/tmp/new-root/source/test.c'
PAIRS = ((b'/private/tmp/old-root', b'/private/tmp/new-root'),)


def pe():
    raw = bytearray(2048)
    raw[:2] = b'MZ'
    struct.pack_into('<I', raw, 60, 128)
    raw[128:132] = b'PE\0\0'
    struct.pack_into('<HHIIIHH', raw, 132, 0xaa64, 2, 100, 0, 0, 240, 0)
    struct.pack_into('<H', raw, 152, 0x20b)
    struct.pack_into('<I', raw, 152 + 108, 16)
    struct.pack_into('<II', raw, 152 + 112 + 48, 0x2080, 28)
    for i, (name, rva, offset, flags) in enumerate(((b'.text', 0x1000, 512, 0x60000020),
                                                 (b'.rdata', 0x2000, 1024, 0x40000040))):
        s = 392 + 40 * i
        raw[s:s + len(name)] = name
        struct.pack_into('<IIII', raw, s + 8, 512, rva, 512, offset)
        struct.pack_into('<I', raw, s + 36, flags)
    raw[512:516] = b'code'
    raw[1024:1024 + len(OLD)] = OLD
    struct.pack_into('<IIHHIIII', raw, 1152, 0, 100, 0, 0, 2, 25, 0x20a0, 1184)
    raw[1184:1188] = b'RSDS'
    raw[1188:1204] = bytes(range(16))
    struct.pack_into('<I', raw, 1204, 1)
    return raw


def sign_macho(raw):
    signature = 4096
    cdsize = 88 + 5 + 32
    blobsize = 20 + cdsize
    raw = bytearray(raw[:signature]) + bytearray(blobsize)
    struct.pack_into('>III', raw, signature, 0xfade0cc0, blobsize, 1)
    struct.pack_into('>II', raw, signature + 12, 0, 20)
    cd = signature + 20
    struct.pack_into('>9I', raw, cd, 0xfade0c02, cdsize, 0x20400, 0x20002, 93, 88, 0, 1, signature)
    struct.pack_into('>4B', raw, cd + 36, 32, 2, 0, 12)
    raw[cd + 88:cd + 93] = b'test\0'
    raw[cd + 93:cd + 125] = hashlib.sha256(raw[:signature]).digest()
    return raw


def macho():
    raw = bytearray(4096)
    # One segment with non-overlapping code/string sections, UUID and signature.
    struct.pack_into('<8I', raw, 0, 0xfeedfacf, 0x100000c, 0, 2, 3, 232 + 24 + 16, 0, 0)
    struct.pack_into('<II', raw, 32, 0x19, 232)
    struct.pack_into('<I', raw, 32 + 64, 2)
    for i, (name, offset, flags) in enumerate(((b'__text', 512, 0x80000400),
                                             (b'__cstring', 768, 2))):
        at = 104 + i * 80
        raw[at:at + len(name)] = name
        struct.pack_into('<Q', raw, at + 40, 128)
        struct.pack_into('<I', raw, at + 48, offset)
        struct.pack_into('<I', raw, at + 64, flags)
    struct.pack_into('<II', raw, 264, 0x1b, 24)
    raw[272:288] = bytes(range(16))
    struct.pack_into('<IIII', raw, 288, 0x1d, 16, 4096, 145)
    raw[512:516] = b'code'
    raw[768:768 + len(OLD)] = OLD
    return sign_macho(raw)


def coff():
    raw = bytearray(256)
    struct.pack_into('<HHIIIHH', raw, 0, 0xaa64, 2, 100, 0, 0, 0, 0)
    for i, (name, offset, flags) in enumerate(((b'.text', 128, 0x60000020),
                                             (b'.rdata', 192, 0x40000040))):
        at = 20 + i * 40
        raw[at:at + len(name)] = name
        struct.pack_into('<IIII', raw, at + 8, 64, 0, 64, offset)
        struct.pack_into('<I', raw, at + 36, flags)
    raw[128:132] = b'code'
    raw[192:192 + len(OLD)] = OLD
    return raw


def archive(member):
    header = b'original.o/     ' + b'0           ' + b'0     ' + b'0     ' + b'644     '
    header += str(len(member)).encode().ljust(10) + b'`\n'
    return b'!<arch>\n' + header + member + (b'\n' if len(member) & 1 else b'')


class ExplanationTests(unittest.TestCase):
    def compare(self, before, after, kind='pe', path='lib/wine/aarch64-windows/original.dll'):
        return subject.compare_bytes(bytes(before), bytes(after), kind, path, PAIRS)

    def test_exact_raw_identity_and_raw_hashes_are_kept(self):
        raw = pe()
        result = self.compare(raw, raw)
        self.assertEqual(result['status'], 'exact')
        self.assertEqual(result['before_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['difference_runs'], [])

    def test_pe_only_named_fields_and_recorded_string(self):
        old, new = pe(), pe()
        struct.pack_into('<I', new, 136, 200)
        struct.pack_into('<I', new, 1156, 200)
        new[1188:1204] = bytes(reversed(range(16)))
        new[1024:1024 + len(NEW)] = NEW
        result = self.compare(old, new)
        self.assertEqual(result['status'], 'explained_metadata')
        self.assertEqual({r[2] for r in result['explained_regions']}, {1, 2, 3, 4})
        self.assertEqual(result['changed_bytes'], sum(a != b for a, b in zip(old, new)))
        self.assertEqual(result['changed_bytes'], sum(r[1] for r in result['difference_runs']) + sum(r[3] for r in result['explained_regions']))

    def test_code_data_or_nonpath_debug_change_is_unexplained(self):
        for at in (512, 1064, 1184, 1204, 1500):
            with self.subTest(offset=at):
                old, new = pe(), pe()
                new[at] ^= 1
                self.assertEqual(self.compare(old, new)['status'], 'unexplained')

    def test_unknown_path_or_prefix_substring_is_not_remapped(self):
        for text in (NEW.replace(b'new-root', b'bad-root'), NEW + b'/tail'):
            old, new = pe(), pe()
            new[1024:1024 + len(text)] = text
            self.assertEqual(self.compare(old, new)['status'], 'unexplained')
        self.assertEqual(subject.substitute(b'/private/tmp/old-root-other/x', PAIRS),
                         b'/private/tmp/old-root-other/x')

    def test_path_inside_executable_section_cannot_be_explained(self):
        old, new = pe(), pe()
        old[512:512 + len(OLD)] = OLD
        new[512:512 + len(NEW)] = NEW
        self.assertEqual(self.compare(old, new)['status'], 'unexplained')

    def test_pe_virtual_code_alias_rejects_even_without_raw_overlap(self):
        old, new = pe(), pe()
        for raw in (old, new): struct.pack_into('<I', raw, 392 + 12, 0x2000)
        new[1188] ^= 1
        result = self.compare(old, new)
        self.assertEqual(result['status'], 'unexplained')
        self.assertEqual(result['reason'], 'comparison_pe_virtual_overlap')

    def test_malicious_debug_executable_overlap_is_rejected(self):
        for offset, value in ((392 + 40 + 20, 512), (392 + 40 + 36, 0x60000020)):
            old, new = pe(), pe()
            struct.pack_into('<I', old, offset, value)
            struct.pack_into('<I', new, offset, value)
            new[1188] ^= 1
            self.assertEqual(self.compare(old, new)['status'], 'unexplained')

    def test_changed_layout_size_or_malformed_offsets_not_normalized(self):
        old = pe()
        new = pe(); struct.pack_into('<I', new, 60, 0xffffff00)
        self.assertEqual(self.compare(old, new)['status'], 'unexplained')
        self.assertEqual(self.compare(old, old + b'x')['reason'], 'size_changed')
        new = pe(); struct.pack_into('<I', new, 392 + 40 + 8, 500)
        self.assertEqual(self.compare(old, new)['status'], 'unexplained')

    def test_ledger_includes_final_byte_and_noncontiguous_unexplained_runs(self):
        old, new = pe(), pe()
        new[512] ^= 1; new[514] ^= 1; new[-1] ^= 1
        self.assertEqual(self.compare(old, new)['difference_runs'], [[512, 1, 0], [514, 1, 0], [2047, 1, 0]])

    def test_macho_uuid_path_and_recomputed_hashes_are_explained(self):
        old, new = macho(), macho()
        new[272] ^= 1; new[768:768 + len(NEW)] = NEW
        new = sign_macho(new)
        result = self.compare(old, new, 'macho')
        self.assertEqual(result['status'], 'explained_metadata')
        self.assertEqual({r[2] for r in result['explained_regions']}, {4, 6, 7})

    def test_macho_code_change_remains_unexplained_despite_valid_new_signature(self):
        old, new = macho(), macho()
        new[512] ^= 1
        self.assertEqual(self.compare(old, sign_macho(new), 'macho')['status'], 'unexplained')

    def test_macho_hash_tamper_or_entitlement_shape_cannot_be_stripped(self):
        for at in (-1, 4096 + 20 + 12):
            old, new = macho(), macho(); new[at] ^= 1
            result = self.compare(old, new, 'macho')
            self.assertEqual(result['status'], 'unexplained')
            self.assertIn('comparison_adhoc', result['reason'])

    def test_macho_cstring_cannot_overlap_code_or_signature(self):
        old, new = macho(), macho()
        for raw in (old, new): struct.pack_into('<I', raw, 184 + 48, 512)
        new[512] ^= 1
        self.assertEqual(self.compare(sign_macho(old), sign_macho(new), 'macho')['status'], 'unexplained')

    def test_macho_signature_cannot_overlap_file_backed_code(self):
        old, new = macho(), macho()
        for raw in (old, new):
            struct.pack_into('<Q', raw, 104 + 40, 4096 + 145 - 512)
            struct.pack_into('<Q', raw, 184 + 40, 0)
        new[272] ^= 1
        result = self.compare(sign_macho(old), sign_macho(new), 'macho')
        self.assertEqual(result['status'], 'unexplained')
        self.assertEqual(result['reason'], 'comparison_signature_overlap')

    def test_difference_budget_fails_without_claiming_a_complete_ledger(self):
        old, new = pe(), pe()
        new[512:532:2] = b'z' * 10
        with mock.patch.object(subject, 'MAX_FILE_RUNS', 3):
            result = self.compare(old, new)
        self.assertEqual(result['reason'], 'difference_budget_exceeded')
        self.assertEqual(result['status'], 'unexplained')
        self.assertIsNone(result['changed_bytes'])
        self.assertEqual(result['difference_runs'], [])

    def test_archive_objects_are_parsed_and_do_not_hide_code(self):
        old, new = coff(), coff()
        new[192:192 + len(NEW)] = NEW
        struct.pack_into('<I', new, 4, 200)
        self.assertEqual(self.compare(archive(old), archive(new), 'data')['status'], 'explained_metadata')
        new[128] ^= 1
        self.assertEqual(self.compare(archive(old), archive(new), 'data')['status'], 'unexplained')

    def test_generated_header_banner_only(self):
        old = b'/*** Autogenerated by WIDL 11 from ' + OLD + b' - Do not edit ***/\nint x;\n'
        new = old.replace(OLD, NEW)
        self.assertEqual(self.compare(old, new, 'data', 'include/wine/original.h')['status'], 'explained_metadata')
        self.assertEqual(self.compare(old, new.replace(b'int x', b'int y'), 'data', 'include/wine/original.h')['status'], 'unexplained')
        self.assertEqual(self.compare(old, new, 'data', 'other/original.h')['status'], 'unexplained')



def with_symbols(raw, *, pe_format=False, changed=False):
    """Independent original COFF records with a path literal and a plain symbol."""
    raw = bytearray(raw)
    literal = NEW if changed else OLD
    name = (b'??_C@_0CE@KLMHIOD@?1private?1tmp?1new?9root?1source?1tes@' if changed else
            b'??_C@_0CE@PFOEAPI@?1private?1tmp?1old?9root?1source?1tes@')
    plain = b'ordinary_function'
    # Reorder the strings deliberately; symbol values and their resolved names
    # remain fixed. Changing a value or an unrelated name must still fail.
    entries = (name, plain) if changed else (plain, name)
    strings = b'\0'.join(entries) + b'\0'
    offsets = {entry: 4 + sum(len(e) + 1 for e in entries[:i]) for i, entry in enumerate(entries)}
    table = 1536 if pe_format else 256
    records = bytearray(72)
    for i, (symbol, section, kind, storage, aux) in enumerate(
            ((plain, 1, 0x20, 2, 0), (name, 2, 0, 2, 0), (b'.rdata', 2, 0, 3, 1))):
        at = 18 * i
        if symbol == b'.rdata': records[at:at + 6] = symbol
        else: struct.pack_into('<II', records, at, 0, offsets[symbol])
        struct.pack_into('<IhHBB', records, at + 8, 0, section, kind, storage, aux)
    data_at, data_size = (1024, 512) if pe_format else (192, 64)
    raw[data_at:data_at + len(literal)] = literal
    import zlib
    checksum = zlib.crc32(raw[data_at:data_at + data_size], 0xffffffff) ^ 0xffffffff
    struct.pack_into('<IHHIhBBh', records, 54, data_size, 0, 0, checksum, 2, 2, 0, 0)
    raw = raw[:table] + records + struct.pack('<I', 4 + len(strings)) + strings
    header = 132 if pe_format else 0
    struct.pack_into('<II', raw, header + 8, table, 4)
    return raw, name


def indexed_archive(member, name):
    def wrap(member_name, data):
        header = member_name.ljust(16) + b'0           ' + b'0     ' + b'0     ' + b'644     '
        header += str(len(data)).encode().ljust(10) + b'`\n'
        return header + data + (b'\n' if len(data) & 1 else b'')
    first_size = 8 + len(name) + 1
    second_size = 14 + len(name) + 1
    offset = 8 + 60 + first_size + (first_size & 1) + 60 + second_size + (second_size & 1)
    first = struct.pack('>II', 1, offset) + name + b'\0'
    second = struct.pack('<IIIH', 1, offset, 1, 1) + name + b'\0'
    return b'!<arch>\n' + wrap(b'/', first) + wrap(b'/', second) + wrap(b'original.o/', member)


class SymbolTests(unittest.TestCase):
    def test_literal_checksum_matches_fixed_abi_vectors(self):
        self.assertEqual(subject.msvc_literal_name(OLD),
            b'??_C@_0CE@PFOEAPI@?1private?1tmp?1old?9root?1source?1tes@')
        self.assertEqual(subject.msvc_literal_name(NEW),
            b'??_C@_0CE@KLMHIOD@?1private?1tmp?1new?9root?1source?1tes@')

    def test_pe_symbols_reorder_only_after_name_and_literal_binding(self):
        old, _ = with_symbols(pe(), pe_format=True)
        new, _ = with_symbols(pe(), pe_format=True, changed=True)
        result = subject.compare_bytes(old, new, 'pe', 'original.dll', PAIRS)
        self.assertEqual(result['status'], 'explained_metadata')
        self.assertIn(8, {row[2] for row in result['explained_regions']})
        # A different symbol address remains a real semantic difference.
        struct.pack_into('<I', new, 1536 + 8, 4)
        self.assertEqual(subject.compare_bytes(old, new, 'pe', 'original.dll', PAIRS)['status'], 'unexplained')

    def test_symbol_literal_crc_mismatch_or_unrelated_name_rejects(self):
        old, _ = with_symbols(coff())
        new, _ = with_symbols(coff(), changed=True)
        for needle in (b'KLMHIOD', b'ordinary_function'):
            damaged = new.replace(needle, b'X' + needle[1:])
            result = subject.compare_bytes(archive(old), archive(damaged), 'data', 'original.a', PAIRS)
            self.assertEqual(result['status'], 'unexplained')

    def test_both_archive_indices_bind_member_symbol_and_checked_auxiliary(self):
        old, oldname = with_symbols(coff())
        new, newname = with_symbols(coff(), changed=True)
        before, after = indexed_archive(old, oldname), indexed_archive(new, newname)
        result = subject.compare_bytes(before, after, 'data', 'original.a', PAIRS)
        self.assertEqual(result['status'], 'explained_metadata')
        self.assertIn(9, {row[2] for row in result['explained_regions']})
        self.assertIn(10, {row[2] for row in result['explained_regions']})
        # The first index must point to the actual unchanged member boundary.
        damaged = bytearray(after); damaged[72] ^= 1
        self.assertEqual(subject.compare_bytes(before, damaged, 'data', 'original.a', PAIRS)['status'], 'unexplained')
        damaged = bytearray(new); damaged[256 + 36 + 26] ^= 1
        self.assertEqual(subject.compare_bytes(archive(old), archive(damaged), 'data', 'original.a', PAIRS)['status'], 'unexplained')

    def test_wide_literal_mapping_requires_exact_checksum_and_path(self):
        before, after = pe(), pe()
        for raw, literal in ((before, OLD), (after, NEW)):
            raw[1024:1100] = b'\0' * 76
            data = literal.decode().encode('utf-16-le')
            raw[1024:1024 + len(data)] = data
        result = subject.compare_bytes(before, after, 'pe', 'original.dll', PAIRS)
        self.assertEqual(result['status'], 'explained_metadata')
        after[1024] = ord('X')
        self.assertEqual(subject.compare_bytes(before, after, 'pe', 'original.dll', PAIRS)['status'], 'unexplained')
        name = subject.msvc_literal_name(OLD, wide=True)
        self.assertTrue(name.startswith(b'??_C@_1'))
        self.assertNotEqual(name, subject.msvc_literal_name(NEW, wide=True))

    def test_shorter_crc_name_changes_only_bound_table_size_and_zero_padding(self):
        import zlib
        old, _ = with_symbols(pe(), pe_format=True)
        new, name = with_symbols(pe(), pe_format=True, changed=True)
        literal = b'/private/tmp/nex-root/source/test.c'
        mapped_name = b'??_C@_0CE@EGKJPHMN@?1private?1tmp?1nex?9root?1source?1tes@'
        new = bytearray(new.replace(NEW, literal).replace(name, mapped_name))
        self.assertEqual(len(mapped_name), len(name) + 1)
        struct.pack_into('<I', new, 1540, struct.unpack_from('<I', new, 1540)[0] + 1)
        struct.pack_into('<I', new, 1608, struct.unpack_from('<I', new, 1608)[0] + 1)
        struct.pack_into('<I', new, 1536 + 36 + 26, zlib.crc32(new[1024:1536], 0xffffffff) ^ 0xffffffff)
        old.extend(b'\0' * (2048 - len(old))); new.extend(b'\0' * (2048 - len(new)))
        pairs = ((b'/private/tmp/old-root', b'/private/tmp/nex-root'),)
        result = subject.compare_bytes(old, new, 'pe', 'original.dll', pairs)
        self.assertEqual(result['status'], 'explained_metadata')
        end = 1608 + struct.unpack_from('<I', old, 1608)[0]
        old[end] = 1
        result = subject.compare_bytes(old, new, 'pe', 'original.dll', pairs)
        self.assertEqual(result['status'], 'unexplained')
        self.assertEqual(result['reason'], 'comparison_symbol_padding')

    def test_zero_padding_cannot_hide_unknown_changed_tail(self):
        old, _ = with_symbols(pe(), pe_format=True)
        new, _ = with_symbols(pe(), pe_format=True, changed=True)
        old.extend(b'\0' * 16); new.extend(b'\0' * 16)
        new[-1] = 1
        result = subject.compare_bytes(old, new, 'pe', 'original.dll', PAIRS)
        self.assertEqual(result['status'], 'unexplained')
        self.assertIn([len(new) - 1, 1, 0], result['difference_runs'])

    def test_second_generated_banner_keeps_following_code_exact(self):
        old = b'/* File generated automatically from ' + OLD + b'; do not edit */\nint original;\n'
        new = old.replace(OLD, NEW)
        self.assertEqual(subject.compare_bytes(old, new, 'data', 'include/wine/original.h', PAIRS)['status'],
                         'explained_metadata')
        self.assertEqual(subject.compare_bytes(old, new.replace(b'original', b'mutation'), 'data',
                                              'include/wine/original.h', PAIRS)['status'], 'unexplained')

    def test_symbol_table_cannot_alias_executable_section(self):
        old, _ = with_symbols(pe(), pe_format=True)
        new = bytearray(old)
        for raw in (old, new): struct.pack_into('<I', raw, 132 + 8, 512)
        new[520] ^= 1
        self.assertEqual(subject.compare_bytes(old, new, 'pe', 'original.dll', PAIRS)['status'], 'unexplained')


def debug_object(path, tag):
    """Original ARM64 COFF with one real SECREL-to-debug-string reference."""
    text = b'CODE!!!!'
    linkage = b'?function@?A0x' + tag + b'@@YAXXZ'
    strings = path + b'\0' + linkage + b'\0'
    info = struct.pack('<I', len(path) + 1)
    data_at = 160
    info_at = data_at + len(text) + len(strings)
    reloc_at = info_at + len(info)
    table = reloc_at + 10
    names = b'.debug_str\0.debug_info\0'
    raw = bytearray(table + 18 + 4 + len(names))
    struct.pack_into('<HHIIIHH', raw, 0, 0xaa64, 3, 100, table, 1, 0, 0)
    for i, (name, offset, payload, flags) in enumerate((
            (b'.text', data_at, text, 0x60000020),
            (b'/4', data_at + len(text), strings, 0x40000040),
            (b'/15', info_at, info, 0x40000040))):
        at = 20 + 40 * i
        raw[at:at + len(name)] = name
        struct.pack_into('<IIII', raw, at + 8, 0, 0, len(payload), offset)
        struct.pack_into('<I', raw, at + 36, flags)
        raw[offset:offset + len(payload)] = payload
    struct.pack_into('<I', raw, 100 + 24, reloc_at)
    struct.pack_into('<H', raw, 100 + 32, 1)
    struct.pack_into('<IIH', raw, reloc_at, 0, 0, 8)
    struct.pack_into('<IIIhHBB', raw, table, 0, 4, 0, 2, 0, 3, 0)
    struct.pack_into('<I', raw, table + 18, len(names) + 4)
    raw[table + 22:] = names
    return raw


class StructuralTests(unittest.TestCase):
    def pair(self):
        return (debug_object(b'/private/tmp/old-root/source/test.cpp', b'BF54349D'),
                debug_object(b'/private/tmp/new-root/source/test.cpp', b'BE6B141C'))

    def test_namespace_hash_matches_independent_pinned_xxhash_vectors(self):
        # Generated by compiling the pinned upstream xxhash.h itself, rather
        # than computing expectations with Pear's arithmetic implementation.
        expected = {17: 0x9de37328, 32: 0xe96e4c05, 33: 0x88991e58, 64: 0x89b0ed55,
                    65: 0xe90422d0, 96: 0xea046dfb, 97: 0xdc4e14f4, 128: 0x7ff4c46b}
        for length, value in expected.items():
            self.assertEqual(subject.namespace_path_hash(bytes(range(length))), value)
        self.assertEqual(subject.namespace_path_hash(b'/private/tmp/old-root/source/test.cpp'), 0xbf54349d)
        self.assertEqual(subject.namespace_path_hash(b'/private/tmp/new-root/source/test.cpp'), 0xbe6b141c)
        for length in (16, 129):
            with self.assertRaisesRegex(Error, 'comparison_namespace_path_length'):
                subject.namespace_path_hash(b'a' * length)

    def test_complete_coff_and_archive_reference_replay(self):
        old, new = self.pair()
        value, _ = subject.compare_coff_alignment(old, new, 'original.o', PAIRS)
        self.assertEqual(value['status'], 'explained_metadata')
        self.assertTrue(value['all_file_bytes_accounted'])
        self.assertEqual(value['coff_sections'][2]['verified_ranges'],
                         [[0, 4, 'coff-verified-debug-string-reference']])
        # A one-digit-shorter namespace tag changes a real debug section size,
        # symbol-table location and archive member size; all are replayed.
        new = debug_object(b'/private/tmp/new-0005/source/test.cpp', b'47A858F')
        pairs = ((b'/private/tmp/old-root', b'/private/tmp/new-0005'),)
        value = subject.compare_bytes(archive(old), archive(new), 'data', 'original.a', pairs)
        self.assertEqual(value['status'], 'explained_metadata')
        self.assertTrue(value['archive_members'][0]['comparison']['all_file_bytes_accounted'])

    def test_executable_debug_sections_reject_even_with_equal_size(self):
        old, new = self.pair()
        for raw in (old, new): struct.pack_into('<I', raw, 60 + 36, 0x60000020)
        value, _ = subject.compare_coff_alignment(old, new, 'original.o', PAIRS)
        self.assertEqual(value['status'], 'unexplained')
        self.assertEqual(value['reason'], 'comparison_debug_string_code')

    def test_secrel_is_arm64_only_and_actual_reference_must_match(self):
        old, new = self.pair()
        for raw in (old, new): struct.pack_into('<H', raw, 0, 0x8664)
        value, _ = subject.compare_coff_alignment(old, new, 'original.o', PAIRS)
        self.assertEqual(value['reason'], 'comparison_structural_arm64_header')
        for mutation in ('kind', 'target', 'addend', 'code', 'tag'):
            old, new = self.pair()
            if mutation == 'kind':
                for raw in (old, new):
                    at = struct.unpack_from('<I', raw, 124)[0]
                    struct.pack_into('<H', raw, at + 8, 4)
                new[struct.unpack_from('<I', new, 120)[0]] ^= 1
            elif mutation == 'target':
                at = struct.unpack_from('<I', new, 124)[0]
                struct.pack_into('<I', new, at + 4, 1)
            elif mutation == 'addend': new[struct.unpack_from('<I', new, 120)[0]] ^= 1
            elif mutation == 'code': new[160] ^= 1
            else: new = new.replace(b'BE6B141C', b'BE6B141D')
            value, _ = subject.compare_coff_alignment(old, new, 'original.o', PAIRS)
            self.assertEqual(value['status'], 'unexplained', mutation)

    def test_raw_short_name_padding_and_unused_pointers_are_accounted(self):
        for offset in (27, 299):
            old, _ = with_symbols(coff()); new, _ = with_symbols(coff(), changed=True)
            new[offset] = ord('X')
            value, _ = subject.compare_coff_alignment(old, new, 'original.o', PAIRS)
            self.assertEqual(value['status'], 'unexplained')
            self.assertIn('name_padding', value['reason'])
        old, new = self.pair()
        struct.pack_into('<I', new, 20 + 24, 0x12345678)
        value, _ = subject.compare_coff_alignment(old, new, 'original.o', PAIRS)
        self.assertEqual(value['reason'], 'comparison_structural_unused_relocation_pointer')
        old, new = self.pair()
        for raw in (old, new):
            struct.pack_into('<I', raw, 20 + 16, 0)
            raw[160:168] = b'\0' * 8
        value, _ = subject.compare_coff_alignment(old, new, 'original.o', PAIRS)
        self.assertEqual(value['status'], 'explained_metadata')
        struct.pack_into('<I', new, 20 + 20, 161)
        value, _ = subject.compare_coff_alignment(old, new, 'original.o', PAIRS)
        self.assertEqual(value['reason'], 'comparison_structural_unused_data_pointer')

    def test_linked_translation_units_bind_all_names_and_reject_tag_conflicts(self):
        def table(paths, names):
            return [{'name': b'.debug_str', 'data': b'\0'.join([*paths, *names]) + b'\0'}]
        old_path, new_path = (b'/private/tmp/' + x + b'/source/test.cpp' for x in (b'old-root', b'new-root'))
        old_name, new_name = b'?f@?A0xBF54349D@@YAXXZ', b'?f@?A0xBE6B141C@@YAXXZ'
        old, new = table([old_path], [old_name]), table([new_path], [new_name])
        self.assertEqual(subject.namespace_debug_names(old, new, PAIRS, linked=True), {old_name: new_name})
        new[0]['data'] = new[0]['data'].replace(new_name, new_name.replace(b'YAXXZ', b'YAHXZ'))
        with self.assertRaisesRegex(Error, 'comparison_namespace_tag_binding'):
            subject.namespace_debug_names(old, new, PAIRS, linked=True)
        old = table([old_path, old_path.replace(b'test', b'other')], [])
        new = table([new_path, new_path.replace(b'test', b'other')], [])
        with mock.patch.object(subject, 'namespace_path_hash', side_effect=[1, 2, 1, 3]):
            with self.assertRaisesRegex(Error, 'comparison_namespace_tag_conflict'):
                subject.namespace_debug_names(old, new, PAIRS, linked=True)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.roots = [self.base / 'reference', self.base / 'candidate']
        self.records = []
        self.inventories = []
        for root in self.roots:
            (root / 'install').mkdir(parents=True)
            (root / 'build.json').write_text('{}\n')
            (root / 'install/original').write_bytes(b'original')
            self.inventories.append({'files': [{'path': 'original', 'sha256': subject.digest(b'original'),
                'size_bytes': 8, 'mode': 420, 'kind': 'data'}], 'symlinks': []})
            self.records.append({'variant': 'arm64', 'record_hashes': {}, 'source_manifest': {}, 'patches': [],
                'fixture_hashes': {}, 'sdk': {}, 'tool_prepared_sha256': 'a' * 64, 'configuration': {},
                'fixture_suite': 'mac-driver', 'code_publication_policy': 'page-wx',
                'path_alias': {'invoked': str(self.base), 'resolved': str(self.base)},
                'tools_root': str(self.base / 'tools'), 'artifacts_manifest': {'sha256': 'b' * 64}})
        self.verify = mock.patch('build.verify_build', side_effect=lambda root, current=True: self.records[self.roots.index(root)])
        self.inventory = mock.patch('build.artifact_inventory', side_effect=lambda record, root: self.inventories[self.roots.index(root)])
        self.verify.start(); self.inventory.start()
        self.addCleanup(self.verify.stop); self.addCleanup(self.inventory.stop)

    def compare(self):
        return subject.compare_unsigned(*self.roots)

    def test_complete_inventory_exact_and_public_has_no_paths(self):
        value = self.compare()
        self.assertTrue(value['gate_passed']); self.assertTrue(value['byte_identity'])
        public = subject.public_summary(value)
        self.assertNotIn(str(self.base), json.dumps(public))
        self.assertNotIn('files', public)
        self.assertEqual(public['comparison_sha256'], subject.digest(encoded(value)))

    def test_mode_symlink_and_missing_extra_fail(self):
        self.inventories[1]['files'][0]['mode'] = 493
        self.assertFalse(self.compare()['gate_passed'])
        self.inventories[1]['files'][0]['mode'] = 420
        self.inventories[1]['symlinks'] = [{'path': 'link', 'target': 'original'}]
        self.assertFalse(self.compare()['gate_passed'])
        self.inventories[1]['symlinks'] = []
        self.inventories[1]['files'] = []
        value = self.compare(); self.assertEqual(value['missing_paths'], ['original'])
        self.assertFalse(value['gate_passed'])

    def test_source_difference_cannot_be_classified_as_nondeterminism(self):
        self.records[1]['patches'] = ['different']
        with self.assertRaisesRegex(Error, 'comparison_inputs_differ'): self.compare()

    def test_normalized_source_argument_policies_must_match(self):
        self.assertTrue(self.compare()['gate_passed'])
        self.records[1]['source_argument_policy'] = 'stable_relative_v1'
        with self.assertRaisesRegex(Error, 'comparison_source_argument_policy'):
            self.compare()
        self.records[0]['source_argument_policy'] = 'stable_relative_v1'
        self.assertTrue(self.compare()['gate_passed'])
        self.records[0]['source_argument_policy'] = 'legacy_absolute_v1'
        with self.assertRaisesRegex(Error, 'build_source_argument_policy'):
            self.compare()

    def test_saved_claim_is_recomputed_and_mutation_rejects(self):
        path = self.base / 'comparison.json'
        value = self.compare(); path.write_bytes(encoded(value))
        self.assertEqual(subject.validate_unsigned_comparison(path, *self.roots), value)
        value['exact_files'] = 999; path.write_bytes(encoded(value))
        with self.assertRaisesRegex(Error, 'comparison_record_mismatch'):
            subject.validate_unsigned_comparison(path, *self.roots)
        (self.roots[1] / 'install/original').write_bytes(b'mutation')
        with self.assertRaisesRegex(Error, 'comparison_artifact_changed'): self.compare()

    def test_bool_count_cannot_equal_an_integer_in_saved_replay(self):
        path = self.base / 'comparison.json'
        value = self.compare(); value['exact_files'] = True
        path.write_bytes(encoded(value))
        with self.assertRaisesRegex(Error, 'comparison_record_mismatch'):
            subject.validate_unsigned_comparison(path, *self.roots)

    def test_oversized_record_rejects_before_unbounded_read(self):
        path = self.base / 'oversized.json'
        with path.open('wb') as stream:
            stream.truncate(subject.MAX_COMPARISON + 1)
        with self.assertRaises(Error), mock.patch.object(Path, 'read_bytes', side_effect=AssertionError('unbounded read')):
            subject.validate_unsigned_comparison(path, *self.roots)

    def test_duplicate_path_rejects(self):
        self.inventories[0]['files'] *= 2
        with self.assertRaisesRegex(Error, 'comparison_duplicate_path'): self.compare()


if __name__ == '__main__':
    unittest.main()
