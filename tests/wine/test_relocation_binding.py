"""Synthetic byte/event rejection checks; these tests never execute Wine or PE."""
import copy
import hashlib
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
import api_runner as api
from common import Error, encoded
from test_api_runner import case_fixture, fixture_stdout, helper_record, jsonl, lifetime_fixture, relocation_fixture


BASE = 0x180000000
# Independent, deliberately small PE with separate code, writable data, export
# metadata and relocation sections. It contains no executable test payload.
SECTIONS = [(b'.text', 0x1000, 0x60000020), (b'.data', 0x4000, 0xc0000040),
            (b'.edata', 0x5000, 0x40000040), (b'.reloc', 0x6000, 0x42000040)]


def offset(rva):
    for index, (_, start, _) in enumerate(SECTIONS):
        if start <= rva < start + 512:
            return 1024 + index * 512 + rva - start
    raise AssertionError('test fixture RVA')


def image():
    raw = bytearray(3072)
    raw[:2] = b'MZ'
    struct.pack_into('<I', raw, 60, 128)
    raw[128:132] = b'PE\0\0'
    struct.pack_into('<HH', raw, 132, 0xaa64, len(SECTIONS))
    struct.pack_into('<HHH', raw, 148, 240, 0x2022, 0x20b)
    struct.pack_into('<Q', raw, 176, BASE)
    struct.pack_into('<II', raw, 208, 0x7000, 1024)
    struct.pack_into('<I', raw, 260, 16)
    for index, (name, rva, flags) in enumerate(SECTIONS):
        at = 392 + index * 40
        raw[at:at + 8] = name.ljust(8, b'\0')
        struct.pack_into('<IIII', raw, at + 8, 512, rva, 512, 1024 + index * 512)
        struct.pack_into('<I', raw, at + 36, flags)
    struct.pack_into('<I', raw, offset(0x4000), 0x13579bdf)
    struct.pack_into('<QQ', raw, offset(0x4008), BASE + 0x1000, BASE + 0x4000)
    struct.pack_into('<Q', raw, offset(0x4020), api.SECURITY_COOKIE_DEFAULT)
    struct.pack_into('<II', raw, 264 + 10 * 8, 0x51a0, 96)
    struct.pack_into('<I', raw, offset(0x51a0), 96)
    struct.pack_into('<Q', raw, offset(0x51f8), BASE + 0x4020)
    struct.pack_into('<II', raw, 264, 0x5000, 512)
    names = [('PearRelocationCode', 0x1000), ('PearRelocationData', 0x4000),
             ('PearRelocationCodePointer', 0x4008), ('PearRelocationDataPointer', 0x4010),
             ('PearSecurityCookie', 0x4020)]
    struct.pack_into('<6I', raw, offset(0x5000) + 16, 1, 5, 5, 0x5040, 0x5060, 0x5080)
    cursor = 0x50a0
    for index, (name, rva) in enumerate(names):
        struct.pack_into('<I', raw, offset(0x5040) + index * 4, rva)
        struct.pack_into('<I', raw, offset(0x5060) + index * 4, cursor)
        struct.pack_into('<H', raw, offset(0x5080) + index * 2, index)
        value = name.encode() + b'\0'
        raw[offset(cursor):offset(cursor) + len(value)] = value
        cursor += len(value)
    struct.pack_into('<II', raw, 264 + 5 * 8, 0x6000, 24)
    struct.pack_into('<IIHH', raw, offset(0x6000), 0x4000, 12, 0xa008, 0xa010)
    struct.pack_into('<IIHH', raw, offset(0x6000) + 12, 0x5000, 12, 0xa1f8, 0)
    return raw


def binding_fixture(directory):
    root = Path(directory)
    runtime, case = root / 'runtime', root / 'case'
    runtime.mkdir(); (case / 'work').mkdir(parents=True)
    raw = bytes(image())
    digest = hashlib.sha256(raw).hexdigest()
    (runtime / 'lifetime.dll').write_bytes(raw)
    for name in ('pear-relocation-a.dll', 'pear-relocation-b.dll'):
        (case / 'work' / name).write_bytes(raw)
    requirements = {'fixture_suite': 'api-abi', 'guest_fixtures': {'lifetime_dll': {
        'machine': 0xaa64, 'execution_permitted': True, 'sha256': digest}}}
    data = encoded(requirements)
    (runtime / 'requirements.json').write_bytes(data)
    signed = {'requirements_sha256': hashlib.sha256(data).hexdigest(),
              'entrypoints': {'lifetime_dll': 'lifetime.dll'}}
    events = []
    for index, event, copy in [(1, 'arena_publish', 0), (2, 'arena_publish', 1),
                               (3, 'arena_retire', 0), (4, 'arena_retire', 1)]:
        events.append({'event': event, 'arena_sequence': index, 'base': 0x20010000 + copy * 65536,
                       'slot': 5 + copy, 'slot_generation': 1, 'original_base': BASE,
                       'size': 0x7000, 'capacity': 65536, 'relocations': 3})
    result = {'case': {'id': 'abi'}, 'events': {'loader': events}}
    return result, relocation_fixture(), runtime, signed, case


class RelocationByteTests(unittest.TestCase):
    def test_exports_original_pointer_cells_and_actual_dir64s(self):
        facts = api.relocation_image(bytes(image()))
        self.assertEqual(facts, {'original_base': BASE, 'size': 0x7000, 'relocations': 3,
            'rvas': {'code_address': 0x1000, 'data_address': 0x4000, 'code_slot': 0x4008, 'data_slot': 0x4010, 'security_cookie_address': 0x4020},
            'security_cookie': {'load_config_rva': 0x51a0, 'field_rva': 0x51f8,
                                'default': api.SECURITY_COOKIE_DEFAULT}})

    def test_truncated_and_wrong_architecture_images_fail(self):
        raw = image()
        for size in (0, 63, 130, 300, 1024, len(raw) - 1):
            with self.subTest(size=size), self.assertRaises(Error):
                api.relocation_image(bytes(raw[:size]))
        for at, fmt, value in [(132, 'H', 0xa641), (150, 'H', 0x22), (208, 'I', 0x7001),
                               (176, 'Q', BASE + 1), (212, 'I', len(raw) + 1)]:
            changed = image(); struct.pack_into('<' + fmt, changed, at, value)
            with self.subTest(at=at, value=value), self.assertRaises(Error):
                api.relocation_image(bytes(changed))

    def test_executable_cells_or_non_executable_code_fail(self):
        for section, flags in [(0, 0x40000040), (0, 0xe0000020), (1, 0xe0000040), (1, 0x40000040)]:
            raw = image(); struct.pack_into('<I', raw, 428 + section * 40, flags)
            with self.subTest(section=section, flags=flags), self.assertRaises(Error):
                api.relocation_image(bytes(raw))

    def test_missing_duplicate_forwarded_aliased_or_unmapped_exports_fail(self):
        mutations = [(offset(0x5040), 0), (offset(0x5040), 0x5080),
                     (offset(0x5040) + 8, 0x4010), (offset(0x5040) + 8, 0x4009),
                     (offset(0x5060) + 4, 0x5080), (offset(0x5040) + 4, 0x8000)]
        for at, value in mutations:
            raw = image(); struct.pack_into('<I', raw, at, value)
            with self.subTest(at=at, value=value), self.assertRaises(Error):
                api.relocation_image(bytes(raw))

    def test_foreign_or_already_relocated_pointer_and_wrong_seed_fail(self):
        for rva, fmt, value in [(0x4008, 'Q', BASE + 0x1004), (0x4010, 'Q', 0x20014000),
                                (0x4008, 'Q', 0), (0x4000, 'I', 123)]:
            raw = image(); struct.pack_into('<' + fmt, raw, offset(rva), value)
            with self.subTest(rva=rva, value=value), self.assertRaises(Error):
                api.relocation_image(bytes(raw))

    def test_malformed_relocation_directory_bounds_and_type_fail(self):
        mutations = [(264 + 5 * 8, 'II', (0, 0)), (264 + 5 * 8, 'II', (0x6000, 13)),
                     (offset(0x6000), 'II', (0x4001, 12)), (offset(0x6000), 'II', (0x4000, 7)),
                     (offset(0x6000), 'II', (0x4000, 14)), (offset(0x6000) + 8, 'H', (0x3008,)),
                     (offset(0x6000), 'I', (0xfffff000,)), (offset(0x6000) + 8, 'H', (0xa1ff,))]
        for at, fmt, values in mutations:
            raw = image(); struct.pack_into('<' + fmt, raw, at, *values)
            with self.subTest(at=at, values=values), self.assertRaises(Error):
                api.relocation_image(bytes(raw))

    def test_overlap_and_missing_pointer_relocations_fail(self):
        for fixup in (0xa008, 0xa00c, 0, 0xa018):
            raw = image(); struct.pack_into('<H', raw, offset(0x6000) + 10, fixup)
            with self.subTest(fixup=fixup), self.assertRaises(Error):
                api.relocation_image(bytes(raw))

    def test_abs_padding_is_ignored_but_dir64_count_is_observed(self):
        raw = image()
        struct.pack_into('<I', raw, 264 + 5 * 8 + 4, 28)
        struct.pack_into('<I', raw, offset(0x6000) + 16, 16)
        struct.pack_into('<HH', raw, offset(0x6000) + 24, 0, 0x0abc)
        self.assertEqual(api.relocation_image(bytes(raw))['relocations'], 3)


    def test_cookie_load_config_must_cover_the_actual_pointer_field(self):
        mutations = [(264 + 10 * 8, 'II', (0, 0)),
                     (264 + 10 * 8, 'II', (0x51a0, 88)),
                     (264 + 10 * 8, 'II', (0x51a1, 96)),
                     (264 + 10 * 8, 'II', (0x51a0, 97)),
                     (offset(0x51a0), 'I', (88,)), (offset(0x51a0), 'I', (97,)),
                     (offset(0x51f8), 'Q', (0,)),
                     (offset(0x51f8), 'Q', (BASE + 0x4028,)),
                     (offset(0x51f8), 'Q', (0x20014020,)),
                     (428 + 2 * 40, 'I', (0x60000040,))]
        for at, fmt, values in mutations:
            raw = image(); struct.pack_into('<' + fmt, raw, at, *values)
            with self.subTest(at=at, values=values), self.assertRaises(Error):
                api.relocation_image(bytes(raw))

    def test_cookie_default_and_independent_export_are_required(self):
        mutations = [(offset(0x4020), 'Q', (0,)),
                     (offset(0x4020), 'Q', (api.SECURITY_COOKIE_DEFAULT + 1,)),
                     (offset(0x5040) + 16, 'I', (0,)),
                     (offset(0x5040) + 16, 'I', (0x5080,)),
                     (offset(0x5040) + 16, 'I', (0x4021,)),
                     (offset(0x5040) + 16, 'I', (0x1008,)),
                     (offset(0x5040) + 16, 'I', (0x4010,))]
        for at, fmt, values in mutations:
            raw = image(); struct.pack_into('<' + fmt, raw, at, *values)
            with self.subTest(at=at, values=values), self.assertRaises(Error):
                api.relocation_image(bytes(raw))

    def test_cookie_config_dir64_cannot_be_missing_or_target_a_neighbor(self):
        for fixup in (0, 0xa1f0, 0xa1f9):
            raw = image(); struct.pack_into('<H', raw, offset(0x6000) + 20, fixup)
            with self.subTest(fixup=fixup), self.assertRaises(Error):
                api.relocation_image(bytes(raw))

    def test_relocation_cannot_modify_any_byte_of_the_default_cookie(self):
        # Keep the required three pointer fixups and append an independent data
        # block. Even partial cookie overlap would undermine initialization proof.
        for target in (0x4019, 0x4020, 0x4027):
            raw = image()
            struct.pack_into('<I', raw, 264 + 5 * 8 + 4, 36)
            struct.pack_into('<IIHH', raw, offset(0x6000) + 24, 0x4000, 12,
                             0xa000 | (target & 0xfff), 0)
            with self.subTest(target=target), self.assertRaisesRegex(Error, 'security_cookie_value_relocated'):
                api.relocation_image(bytes(raw))


class RelocationProtocolTests(unittest.TestCase):
    def test_four_observed_calls_and_two_actual_retirements_required(self):
        rows = relocation_fixture()
        self.assertEqual(api.relocation_events(rows), rows)
        for changed in (rows[:-1], rows[1:], rows + [rows[0]], list(reversed(rows))):
            with self.assertRaises(Error): api.relocation_events(changed)

    def test_private_types_addresses_rounds_and_isolation_fail_closed(self):
        changes = [(0, 'version', True), (0, 'copy', False), (0, 'round', True), (0, 'status', 1),
                   (0, 'code_slot', 0), (0, 'data_slot', 0x20014001), (0, 'code_pointer', False),
                   (0, 'before', 0), (1, 'peer_value', 0x13579bdf), (3, 'peer_value', 0x10203040),
                   (0, 'after', 0), (1, 'call_result', 0), (2, 'module_base', 0x20030000),
                   (4, 'module_base', 0x20030000), (5, 'event', 'probe')]
        for index, key, value in changes:
            rows = relocation_fixture(); rows[index][key] = value
            with self.subTest(index=index, key=key, value=value), self.assertRaises(Error):
                api.relocation_events(rows)

    def test_summary_counters_types_and_missing_proof_are_rejected(self):
        helper, loader = helper_record()
        for field in api.RELOCATION_EXPECTED:
            changed = dict(api.RELOCATION_EXPECTED)
            changed[field] = False if type(changed[field]) is int else None
            raw = b''.join(jsonl(row) for row in [helper, *relocation_fixture(), *api.IMPORT_EXPECTED,
                *lifetime_fixture(), changed, api.LIFETIME_EXPECTED, api.ABI_EXPECTED])
            with self.subTest(field=field), self.assertRaises(Error): api.fixture_output(raw, 'abi', loader)


    def test_uninitialized_invalid_or_unstable_runtime_cookie_is_rejected(self):
        for value in (0, api.SECURITY_COOKIE_DEFAULT, -1, 2**48, True, None, '1'):
            rows = relocation_fixture(); rows[0]['security_cookie'] = value
            with self.subTest(value=value), self.assertRaisesRegex(Error, 'security_cookie_uninitialized'):
                api.relocation_events(rows)
        rows = relocation_fixture(); rows[2]['security_cookie'] += 1
        with self.assertRaisesRegex(Error, 'security_cookie_changed'):
            api.relocation_events(rows)
        for key in ('security_cookie', 'security_cookie_address'):
            rows = relocation_fixture(); del rows[0][key]
            with self.subTest(key=key), self.assertRaisesRegex(Error, 'relocation_event_order'):
                api.relocation_events(rows)
        for value in (0, True, 0x20014021):
            rows = relocation_fixture(); rows[0]['security_cookie_address'] = value
            with self.subTest(value=value), self.assertRaisesRegex(Error, 'relocation_event_address'):
                api.relocation_events(rows)

    def test_independent_cookies_may_coincidentally_have_the_same_valid_value(self):
        rows = relocation_fixture()
        for row in rows[:4]: row['security_cookie'] = 0x123456789abc
        self.assertEqual(api.relocation_events(rows), rows)


class RelocationBindingTests(unittest.TestCase):
    def test_two_simultaneous_placements_bind_original_bytes_and_native_events(self):
        with tempfile.TemporaryDirectory() as directory:
            result, rows, runtime, signed, case = binding_fixture(directory)
            proof = api.assess_relocation_events(result, rows, runtime, signed, case)
            self.assertEqual(proof['fixture_sha256'], hashlib.sha256(bytes(image())).hexdigest())
            self.assertEqual(proof['placements'], 2)
            self.assertEqual(proof['relocated_pointer_slots'], 4)
            self.assertTrue(proof['simultaneous_live'])
            self.assertTrue(proof['data_isolation_verified'])
            self.assertEqual(proof['security_cookie_images'], 2)
            self.assertEqual(proof['security_cookie_observations'], 4)
            for key in ('initialized', 'stable', 'destination_verified', 'load_config_verified'):
                self.assertIs(proof['security_cookie_' + key], True)
            self.assertNotIn('security_cookie', proof)
            self.assertNotIn('security_cookie_address', proof)
            self.assertFalse(any(key in proof for key in ('base', 'path', 'slot', 'module_base')))

    def test_full_abi_case_assessment_requires_the_owned_copies_and_relocation_proof(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            relocation, private, runtime, fixture_signed, case = binding_fixture(directory)
            result, logs, runtime, signed = case_fixture(runtime)
            signed['entrypoints'].update(fixture_signed['entrypoints'])
            signed['requirements_sha256'] = fixture_signed['requirements_sha256']
            result['case']['id'] = 'abi'
            for row in result['registrations']:
                row.update(exit_code=0, exit_status=0)
                result['pre_cleanup']['processes'][row['role']].update(exit_code=0, exit_status=0)
                for event in result['events'][row['role']]:
                    if event['event'] in ('stage3_guest_exit', 'stage3_process_exit'):
                        event['exit_code'] = 0
            events = result['events']['loader']
            stamp = next(row for row in events if row['event'] == 'arena_publish')
            completed = events[-2:]; del events[-2:]
            for row in relocation['events']['loader']:
                events.append({**stamp, **row, 'arena_sequence': row['arena_sequence'] + 2,
                               'code_pages': 1, 'data_pages': 4, 'reused': False})
            for index in range(32):
                publish = {**stamp, 'arena_sequence': 7 + index * 2, 'slot': 5,
                           'slot_generation': index + 2, 'original_base': BASE, 'base': 0x20010000,
                           'size': 0x7000, 'capacity': 65536, 'relocations': 3, 'reused': True}
                events.extend([publish, {**publish, 'event': 'arena_retire',
                                         'arena_sequence': publish['arena_sequence'] + 1}])
            events.extend(completed)
            helper = json.loads(logs[('loader', 'stdout')].splitlines()[0])
            logs[('loader', 'stdout')] = fixture_stdout(helper, 'abi')
            for role, rows in result['events'].items():
                logs[(role, 'events')] = b''.join(jsonl(row) for row in rows)
            accepted = api.assess_case(result, logs, runtime, signed, case_root=case)
            self.assertTrue(accepted['passed'])
            self.assertEqual(accepted['relocation_observations']['placements'], 2)
            with self.assertRaisesRegex(Error, 'relocation_case_scope'):
                api.assess_case(result, logs, runtime, signed)
            (case / 'work/pear-relocation-a.dll').write_bytes(b'changed')
            with self.assertRaisesRegex(Error, 'relocation_copy_changed'):
                api.assess_case(result, logs, runtime, signed, case_root=case)

    def test_pointer_addresses_must_equal_independent_export_rvas(self):
        with tempfile.TemporaryDirectory() as directory:
            result, rows, runtime, signed, case = binding_fixture(directory)
            for key in ('code_slot', 'code_pointer', 'code_address', 'data_slot', 'data_pointer', 'data_address', 'security_cookie_address'):
                changed = copy.deepcopy(rows); changed[0][key] += 8
                with self.subTest(key=key), self.assertRaises(Error):
                    api.assess_relocation_events(result, changed, runtime, signed, case)

    def test_actual_publication_metadata_and_retirement_generation_required(self):
        with tempfile.TemporaryDirectory() as directory:
            result, rows, runtime, signed, case = binding_fixture(directory)
            changes = [(0, 'original_base', BASE + 65536), (0, 'size', 0x8000), (0, 'relocations', 0),
                       (2, 'slot_generation', 2), (2, 'capacity', 131072), (2, 'base', 0x20030000),
                       (1, 'slot', 5), (2, 'arena_sequence', 1), (2, 'arena_sequence', 5)]
            for index, key, value in changes:
                changed = copy.deepcopy(result); changed['events']['loader'][index][key] = value
                with self.subTest(index=index, key=key), self.assertRaises(Error):
                    api.assess_relocation_events(changed, rows, runtime, signed, case)
            for index in range(4):
                changed = copy.deepcopy(result); changed['events']['loader'].pop(index)
                with self.subTest(missing=index), self.assertRaises(Error):
                    api.assess_relocation_events(changed, rows, runtime, signed, case)

    def test_sequential_placements_do_not_prove_simultaneous_lifetime(self):
        with tempfile.TemporaryDirectory() as directory:
            result, rows, runtime, signed, case = binding_fixture(directory)
            result['events']['loader'][1]['arena_sequence'] = 3
            result['events']['loader'][2]['arena_sequence'] = 2
            with self.assertRaisesRegex(Error, 'relocation_simultaneous_lifetimes'):
                api.assess_relocation_events(result, rows, runtime, signed, case)

    def test_later_same_slot_reuse_does_not_replace_first_placement_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            result, rows, runtime, signed, case = binding_fixture(directory)
            events = result['events']['loader']
            events.extend([{**events[0], 'arena_sequence': 5, 'slot_generation': 2},
                           {**events[2], 'arena_sequence': 6, 'slot_generation': 2}])
            api.assess_relocation_events(result, rows, runtime, signed, case)
            events.pop(2)
            with self.assertRaisesRegex(Error, 'relocation_retirement_missing'):
                api.assess_relocation_events(result, rows, runtime, signed, case)

    def test_preferred_base_is_not_a_relocation_test(self):
        with tempfile.TemporaryDirectory() as directory:
            result, rows, runtime, signed, case = binding_fixture(directory)
            delta = BASE - rows[0]['module_base']
            for row in rows:
                if row['copy'] == 0:
                    for key in ('module_base', 'code_slot', 'code_pointer', 'code_address',
                                'data_slot', 'data_pointer', 'data_address', 'security_cookie_address'):
                        if key in row: row[key] += delta
            with self.assertRaisesRegex(Error, 'relocation_zero_delta'):
                api.assess_relocation_events(result, rows, runtime, signed, case)

    def test_changed_missing_or_symlink_copy_is_not_qualified(self):
        for mode in ('changed', 'missing', 'symlink', 'work-symlink'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                result, rows, runtime, signed, case = binding_fixture(directory)
                target = case / 'work/pear-relocation-b.dll'
                if mode == 'changed': target.write_bytes(b'changed')
                elif mode == 'missing': target.unlink()
                elif mode == 'symlink':
                    target.unlink(); target.symlink_to(runtime / 'lifetime.dll')
                else:
                    (case / 'work').rename(case / 'elsewhere')
                    (case / 'work').symlink_to(case / 'elsewhere')
                with self.assertRaises((Error, OSError)):
                    api.assess_relocation_events(result, rows, runtime, signed, case)

    def test_hardlinked_copies_cannot_replace_independent_owned_files(self):
        for source_kind in ('original', 'other-copy'):
            with self.subTest(source_kind=source_kind), tempfile.TemporaryDirectory() as directory:
                result, rows, runtime, signed, case = binding_fixture(directory)
                target = case / 'work/pear-relocation-b.dll'
                target.unlink()
                source = runtime / 'lifetime.dll' if source_kind == 'original' else case / 'work/pear-relocation-a.dll'
                os.link(source, target)
                with self.assertRaisesRegex(Error, 'relocation_file_alias'):
                    api.assess_relocation_events(result, rows, runtime, signed, case)

    def test_signed_original_or_requirements_cannot_change(self):
        for mode in ('original', 'requirements', 'machine', 'permission'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                result, rows, runtime, signed, case = binding_fixture(directory)
                if mode == 'original': (runtime / 'lifetime.dll').write_bytes(b'changed')
                elif mode == 'requirements': (runtime / 'requirements.json').write_bytes(b'{}')
                else:
                    import json
                    required = json.loads((runtime / 'requirements.json').read_bytes())
                    item = required['guest_fixtures']['lifetime_dll']
                    item['machine' if mode == 'machine' else 'execution_permitted'] = 0xa641 if mode == 'machine' else False
                    raw = encoded(required); (runtime / 'requirements.json').write_bytes(raw)
                    signed['requirements_sha256'] = hashlib.sha256(raw).hexdigest()
                with self.assertRaises(Error): api.assess_relocation_events(result, rows, runtime, signed, case)

    def test_api_or_missing_owned_case_path_cannot_supply_abi_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            result, rows, runtime, signed, case = binding_fixture(directory)
            with self.assertRaises(Error): api.assess_relocation_events(result, rows, runtime, signed, None)
            result['case']['id'] = 'api'
            with self.assertRaises(Error): api.assess_relocation_events(result, rows, runtime, signed, case)


if __name__ == '__main__':
    unittest.main()
