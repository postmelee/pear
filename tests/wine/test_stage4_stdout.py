"""Stage 4 raw stdout decoding and both runner assessment entry points.

Synthetic native inventories/publication summaries and fixture byte facts are
mocked in the full-case route; the stdout decoder, Stage 4 semantic assessor,
controlled descendant exit checks and normal helper parser remain real.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'tools/wine/common.py').is_file())
sys.path.insert(0, str(ROOT / 'tools/wine'))
import api_runner as api
import exception_evidence as evidence
from common import Error, decode_json
from test_api_runner import case_fixture, helper_record
from test_exception_evidence import baseline_rows, dynamic, facts, result, select


def wire(row):
    return json.dumps(row, separators=(',', ':')).encode('utf-8') + b'\n'


class Stage4StdoutTests(unittest.TestCase):
    def fixture_route(self, rows=None, transform=None, helper_change=None, kind='threads'):
        helper, loader = helper_record()
        if helper_change:
            helper_change(helper)
        lines = [wire(item) for item in (baseline_rows() if rows is None else rows)]
        if transform:
            index = next(i for i, line in enumerate(lines) if b'"record_kind":"pear_dynamic_call"' in line)
            lines[index] = transform(lines[index])
        return api.fixture_observations(wire(helper) + b''.join(lines), kind, loader)

    def case_route(self, transform=None):
        with tempfile.TemporaryDirectory(prefix='pear-stage4-wire-') as directory:
            record, logs, runtime, signed = case_fixture(directory)
            record['case'] = {'id': 'threads', 'expected_exit': 0}
            record['loader_environment']['PEAR_WINE_STAGE4_FIXTURE'] = '1'
            signed['authorization_scope'] = 'development_windows_thread_memory_exception_fixtures'
            signed['entrypoints']['stage4_pe'] = 'stage4-arm64.exe'
            # Reuse the ordinary runner's owned-process/cleanup fixture, then
            # supply the independently defined finite Stage 4 event protocol.
            record['registrations'] = record['registrations'][:2]
            root, child = record['registrations']
            child.update(exit_code=5, exit_status=5 << 8)
            record['pre_cleanup']['processes'] = {
                item['role']: {'exited': True, 'exit_code': item['exit_code'], 'exit_status': item['exit_status']}
                for item in (root, child)}
            observed = result()
            record['events'] = {'loader': observed['events']['loader'], 'server': [],
                                child['role']: observed['events']['child-1']}
            record['events']['loader'].append({'event': 'stage3_guest_exit', 'exit_code': 0})
            rows = baseline_rows()
            select(rows, 'pear_stage4_result')['native_pid'] = root['identity']['pid']
            select(rows, 'pear_stage4_child_ready')['native_pid'] = child['identity']['pid']
            helper = decode_json(logs['loader', 'stdout'].splitlines()[0])
            lines = [wire(item) for item in rows]
            if transform:
                index = next(i for i, line in enumerate(lines) if b'"record_kind":"pear_dynamic_call"' in line)
                lines[index] = transform(lines[index])
            logs['loader', 'stdout'] = wire(helper) + b''.join(lines)
            for role, events in record['events'].items():
                logs[role, 'events'] = b''.join(wire(item) for item in events)
            owner = {'dynamic_supported': True, **dynamic()}
            with patch.object(api, 'assess_native_events', return_value=2), \
                    patch.object(api, 'assess_arena_events', return_value=[]), \
                    patch.object(api, 'assess_dynamic_events', return_value=owner), \
                    patch.object(evidence, 'fixture_facts', return_value=facts()):
                return api.assess_case(record, logs, runtime, signed)

    def test_uint64_decoder_preserves_exact_large_values(self):
        row = select(baseline_rows(), 'pear_dynamic_call')
        for value in (0, 2**53 - 1, 2**53, 2**63, 2**64 - 1):
            encoded = wire({**row, 'hash': value})
            with self.subTest(value=value):
                self.assertEqual(evidence.decode_stdout_row(encoded)['hash'], value)
                if value >= 2**53:
                    with self.assertRaisesRegex(Error, 'json_integer_limit'):
                        decode_json(encoded)

    def test_raw_rows_reach_fixture_observation_with_fnv64_values(self):
        self.assertTrue(all(row['hash'] > 2**53 for row in baseline_rows() if row['record_kind'] == 'pear_dynamic_call'))
        self.assertEqual(self.fixture_route(), (evidence.expected_results(), [], []))

    def test_raw_rows_reach_complete_stage4_case_assessment(self):
        summary = self.case_route()
        self.assertTrue(summary['passed'])
        self.assertEqual(summary['thread_memory_exception_observations']['dynamic_results'], [42, 84])
        self.assertEqual(summary['thread_memory_exception_observations']['controlled_native_exit'], 5)

    def test_both_runner_routes_reject_malformed_unsigned_wire_values(self):
        replacements = (b'-1', b'-0', b'18446744073709551616', b'9' * 100,
                        b'1.0', b'1e0', b'NaN', b'Infinity', b'-Infinity',
                        b'true', b'false', b'null', b'"1"', b'[]', b'{"nested":1}')
        for replacement in replacements:
            def mutate(line):
                original = str(select(baseline_rows(), 'pear_dynamic_call')['hash']).encode()
                return line.replace(b'"hash":' + original, b'"hash":' + replacement, 1)
            for route in (self.fixture_route, self.case_route):
                with self.subTest(value=replacement, route=route.__name__), self.assertRaises(Error):
                    route(transform=mutate)

    def test_duplicate_keys_including_escaped_spellings_fail(self):
        for name in (b'hash', b'ha\\u0073h'):
            def mutate(line):
                return line.rstrip()[:-1] + b',"' + name + b'":1}\n'
            for route in (self.fixture_route, self.case_route):
                with self.subTest(name=name, route=route.__name__), self.assertRaisesRegex(Error, 'duplicate_json_key'):
                    route(transform=mutate)

    def test_known_flat_fields_and_record_kind_are_required(self):
        baseline = select(baseline_rows(), 'pear_dynamic_call')
        invalid = [dict(baseline, extra=1), {key: value for key, value in baseline.items() if key != 'hash'},
                   dict(baseline, record_kind='pear_unknown'), dict(baseline, record_kind=[]),
                   dict(baseline, version=True), dict(baseline, version=2), [baseline], None]
        for row in invalid:
            with self.subTest(row=row), self.assertRaises(Error):
                evidence.decode_stdout_row(wire(row))

    def test_size_structure_encoding_and_grammar_are_bounded(self):
        invalid = [b' ' * 3073, b'[' * 60 + b'0' + b']' * 60,
                   b'{' + b','.join(b'"key%d":0' % i for i in range(80)) + b'}',
                   b'\xff', b'{"record_kind":"\xed\xa0\x80"}', b'{} {}', b'{', b'']
        for raw in invalid:
            with self.subTest(raw=raw[:60]), self.assertRaises(Error):
                evidence.decode_stdout_row(raw)

    def test_helper_and_older_suites_keep_the_shared_integer_limit(self):
        with self.assertRaisesRegex(Error, 'json_integer_limit'):
            self.fixture_route(helper_change=lambda row: row.update(unscoped_uint64=2**64 - 1))
        for kind in ('api', 'abi'):
            with self.subTest(kind=kind), self.assertRaisesRegex(Error, 'json_integer_limit'):
                self.fixture_route(kind=kind)

    def test_large_hash_is_decodable_but_wrong_hash_cannot_pass_assessment(self):
        def mutate(line):
            item = json.loads(line)
            item['hash'] = 2**64 - 1
            return wire(item)
        # Shape decoding alone is insufficient; the full assessor must still
        # recompute the hash from the two independently expected instructions.
        self.fixture_route(transform=mutate)
        with self.assertRaisesRegex(Error, 'stage4_dynamic_code_result'):
            self.case_route(transform=mutate)


if __name__ == '__main__':
    unittest.main()
