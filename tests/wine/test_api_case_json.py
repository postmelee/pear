"""Finite API-case decoding of synthetic records; no runtime execution."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
import api_runner
import common


def case_bytes(extra):
    return json.dumps({'schema_version': 1, 'record_kind': 'wine_api_case', **extra},
                      separators=(',', ':')).encode()


class APICaseJSONTests(unittest.TestCase):
    def test_case_node_budget_does_not_widen_generic_reader(self):
        # Repeated scalars isolate reader bounds; this is not a runtime record.
        raw = case_bytes({'observations': [0] * 300000})
        with self.assertRaisesRegex(common.Error, 'json_structure_limit'):
            common.decode_json(raw)
        self.assertEqual(len(api_runner.decode_case(raw)['observations']), 300000)
        self.assertEqual(common.MAX_NODES, 250000)

    def test_case_byte_budget_and_descriptor_read_remain_finite(self):
        raw = case_bytes({'diagnostic_chunks': ['x' * 262144] * 33})
        self.assertGreater(len(raw), common.MAX_JSON)
        self.assertLess(len(raw), api_runner.CASE_JSON_BYTES)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'case.json'
            path.write_bytes(raw)
            with self.assertRaisesRegex(common.Error, 'input_size_limit'):
                common.read_relative(path.parent, path.name)
            actual = common.read_relative(path.parent, path.name, api_runner.CASE_JSON_BYTES)
        with self.assertRaisesRegex(common.Error, 'input_size_limit'):
            common.decode_json(actual)
        self.assertEqual(len(api_runner.decode_case(actual)['diagnostic_chunks']), 33)
        oversized = b' ' * (api_runner.CASE_JSON_BYTES + 1)
        with mock.patch.object(common.json, 'loads', side_effect=AssertionError('JSON allocated')):
            with self.assertRaisesRegex(common.Error, 'input_size_limit'):
                api_runner.decode_case(oversized)

    def test_dense_case_rejected_before_object_graph_allocation(self):
        raw = b'{"schema_version":1,"record_kind":"wine_api_case","values":[' + b'0,' * 1000000 + b'0]}'
        with mock.patch.object(common.json, 'loads', side_effect=AssertionError('JSON allocated')):
            with self.assertRaisesRegex(common.Error, 'json_structure_limit'):
                api_runner.decode_case(raw)

    def test_preflight_counts_keys_empty_containers_and_depth(self):
        raw = b'{"a":[],"b":{},"c":[1,true,null]}'
        self.assertEqual(common.decode_json(raw, max_nodes=10)['c'], [1, True, None])
        with mock.patch.object(common.json, 'loads', side_effect=AssertionError('JSON allocated')):
            with self.assertRaisesRegex(common.Error, 'json_structure_limit'):
                common.decode_json(raw, max_nodes=9)
            with self.assertRaisesRegex(common.Error, 'json_structure_limit'):
                api_runner.decode_case(b'{"a":' + b'[' * 49 + b'0' + b']' * 49 + b'}')

    def test_string_escapes_do_not_change_structural_count(self):
        value = {'text': '{}[], \\" \\ \n\r\t \U0001f680', 'list': [{}, []]}
        raw = json.dumps(value, ensure_ascii=True).encode()
        self.assertEqual(common.decode_json(raw, max_nodes=7), value)
        with self.assertRaisesRegex(common.Error, 'json_structure_limit'):
            common.decode_json(raw, max_nodes=6)

    def test_widened_reader_preserves_all_strict_data_checks(self):
        cases = [
            (b'{"x":{"key":1,"k\\u0065y":2}}', 'duplicate_json_key'),
            (case_bytes({'x': 'a' * (common.MAX_STRING + 1)}), 'json_string_limit'),
            (case_bytes({'x' * 257: 0}), 'json_key_limit'),
            (b'{"x":"\\ud800"}', 'json_string_limit'),
            (b'{"x":"\\u007f"}', 'json_string_limit'),
            (b'{"x":"\\u0001"}', 'json_string_limit'),
            (b'{"x":9007199254740992}', 'json_integer_limit'),
            (b'{"x":-9007199254740992}', 'json_integer_limit'),
            (b'{"x":1.0}', 'noninteger_json_number'),
            (b'{"x":NaN}', 'noninteger_json_number'),
            (b'{"x":-Infinity}', 'noninteger_json_number'),
            (b'[]', 'invalid_document_shape'),
            (b'\xff', 'invalid_json'),
            (b'\xef\xbb\xbf{}', 'invalid_json'),
            (b'{"x":"\\q"}', 'invalid_json'),
            (b'{"x":"\\u12"}', 'invalid_json'),
            (b'{"x":"unterminated}', 'invalid_json'),
            (b'{"x": [1, 2}', 'invalid_json'),
            (b'{"x":tru}', 'invalid_json'),
            (b'{"x":true false}', 'invalid_json'),
            (b'{"x":01}', 'invalid_json'),
            (b'{"x":0,}', 'invalid_json'),
            (case_bytes({'record_kind': 'wine_bootstrap_case'}), 'unexpected_record_kind'),
        ]
        for raw, error in cases:
            with self.subTest(error=error, prefix=raw[:64]):
                with self.assertRaisesRegex(common.Error, error):
                    api_runner.decode_case(raw)

    def test_window_envelope_requires_trusted_case_and_suite(self):
        raw = case_bytes({'case': {'id': 'window'}, 'suite': 'mac-driver',
                          'observations': [0] * 1_100_000})
        for selection in ({}, {'suite': api_runner.STAGE5_SUITE}, {'case_id': 'window'},
                          {'suite': api_runner.STAGE5_SUITE, 'case_id': 'threads'}):
            with self.subTest(selection=selection), self.assertRaisesRegex(common.Error, 'json_structure_limit'):
                api_runner.decode_case(raw, **selection)
        decoded = api_runner.decode_case(raw, suite=api_runner.STAGE5_SUITE, case_id='window')
        self.assertEqual(len(decoded['observations']), 1_100_000)
        self.assertEqual(api_runner.CASE_JSON_BYTES, 16 * 1024 * 1024)
        self.assertEqual(api_runner.CASE_JSON_NODES, 1_000_000)

    def test_window_byte_and_node_overflow_rejected_before_allocation(self):
        selected = {'suite': api_runner.STAGE5_SUITE, 'case_id': 'window'}
        too_large = b' ' * (32 * 1024 * 1024 + 1)
        too_dense = b'{"v":[' + b'0,' * 2_000_000 + b'0]}'
        for raw, code in ((too_large, 'input_size_limit'), (too_dense, 'json_structure_limit')):
            with self.subTest(code=code), mock.patch.object(common.json, 'loads',
                    side_effect=AssertionError('JSON allocated')), self.assertRaisesRegex(common.Error, code):
                api_runner.decode_case(raw, **selected)

    def test_window_reader_preserves_strict_scalars_keys_depth_and_kind(self):
        for raw, code in ((b'{"x":1,"x":2}', 'duplicate_json_key'),
                          (case_bytes({'x': 9007199254740992}), 'json_integer_limit'),
                          (case_bytes({'x': 1.5}), 'noninteger_json_number'),
                          (case_bytes({'record_kind': 'wine_bootstrap_case'}), 'unexpected_record_kind'),
                          (b'{"x":' + b'[' * 49 + b'0' + b']' * 49 + b'}', 'json_structure_limit')):
            with self.subTest(code=code), self.assertRaisesRegex(common.Error, code):
                api_runner.decode_case(raw, suite=api_runner.STAGE5_SUITE, case_id='window')

    def test_invalid_budget_cannot_disable_limits(self):
        for budget in (None, True, 0, -1, float('inf')):
            with self.subTest(budget=budget), self.assertRaisesRegex(common.Error, 'invalid_json_budget'):
                common.decode_json(b'{}', max_nodes=budget)


if __name__ == '__main__':
    unittest.main()
