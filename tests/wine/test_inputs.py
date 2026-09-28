"""Bounded input records and preservation checks using owned synthetic data."""
import copy
import os
from pathlib import Path
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[2] / 'tools/wine'
sys.path.insert(0, str(TOOLS))
import common
import prepare


def input_fixture(root):
    """No upstream pin is fabricated as execution or qualification evidence."""
    audit = {'schema_version': 1, 'record_kind': 'source_audit', 'decision': 'blocked',
             'source_ready': False, 'components': [{
        'component_id': 'wine-upstream',
        'source': {'kind': 'git', 'object_format': 'sha1', 'commit_object_id': '1' * 40,
                   'tree_object_id': '2' * 40, 'url': 'https://example.invalid/owned-fixture.git'},
        'acquisition': {'status': 'acquired', 'cache_path': 'wine-upstream/repo.git'},
        'content_digests': [{'algorithm': 'sha256', 'scope': 'git_tree_listing_bytes',
                            'value': '3' * 64, 'cache_path': 'wine-upstream/tree-listing.z'}]}]}
    path = root / 'runtime/sources/manifest.json'
    path.parent.mkdir(parents=True)
    path.write_bytes(common.encoded(audit))
    inputs = {'schema_version': 1, 'record_kind': 'wine_build_inputs', 'scope': 'wine_component',
              'audit_ref': {'path': 'runtime/sources/manifest.json', 'sha256': common.sha256(path)},
              'components': [{'id': 'wine', 'audit_component_id': 'wine-upstream', 'commit': '1' * 40,
                'tree': '2' * 40, 'cache_path': 'wine-upstream/repo.git',
                'url': 'https://example.invalid/owned-fixture.git'}], 'dependencies': [],
              'unresolved_ports': [{'id': 'owned-fixture-port', 'status': 'unimplemented'}]}
    return inputs, audit


class InputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.value, self.audit = input_fixture(self.root)

    def test_blocked_audit_can_be_prepared_without_promotion(self):
        before = (self.root / 'runtime/sources/manifest.json').read_bytes()
        observed = prepare.validate_inputs(self.value, self.root)
        self.assertFalse(observed['audit']['source_ready'])
        self.assertEqual(observed['audit']['decision'], 'blocked')
        self.assertEqual((self.root / 'runtime/sources/manifest.json').read_bytes(), before)

    def test_duplicate_keys_unknown_versions_and_extra_fields_rejected(self):
        for data in [b'{"schema_version":1,"schema_version":1}', b'{"a":{"key":1,"k\\u0065y":2}}']:
            with self.subTest(data=data), self.assertRaisesRegex(common.Error, 'duplicate_json_key'):
                common.decode_json(data)
        for version in [True, 2, '1']:
            value = copy.deepcopy(self.value)
            value['schema_version'] = version
            with self.subTest(version=version), self.assertRaisesRegex(common.Error, 'unsupported_record_version'):
                prepare.validate_inputs(value, self.root)
        self.value['source_ready'] = True
        with self.assertRaisesRegex(common.Error, 'input_fields'):
            prepare.validate_inputs(self.value, self.root)

    def test_changed_audit_or_selected_identity_is_rejected(self):
        for field, new in [('commit', 'f' * 40), ('tree', 'e' * 40), ('cache_path', 'other/repo.git'),
                           ('url', 'https://example.invalid/other.git')]:
            value = copy.deepcopy(self.value)
            value['components'][0][field] = new
            with self.subTest(field=field), self.assertRaisesRegex(common.Error, 'audit_source_mismatch'):
                prepare.validate_inputs(value, self.root)
        (self.root / 'runtime/sources/manifest.json').write_bytes(b'{}')
        with self.assertRaisesRegex(common.Error, 'audit_digest_mismatch'):
            prepare.validate_inputs(self.value, self.root)

    def test_unsafe_references_and_symlink_ancestors_are_rejected(self):
        for path in ['../manifest.json', '/tmp/manifest.json', 'a//b', './a', 'a/../b', 'a\\b',
                     '~a', 'a%2fb', 'a:b', 'a\nb']:
            with self.subTest(path=path), self.assertRaises(common.Error):
                common.relative(path)
        target = self.root / 'outside'
        target.mkdir()
        (target / 'record.json').write_bytes(b'{}')
        (self.root / 'linked').symlink_to(target)
        with self.assertRaises(OSError):
            common.read_relative(self.root, 'linked/record.json')

    def test_numbers_encoding_and_structure_are_bounded(self):
        for data in [b'{"n":1.5}', b'{"n":NaN}', b'{"n":9007199254740992}',
                     b'{"a":"\\ud800"}', b'\xff', b'\xef\xbb\xbf{}', b'[' * 70 + b'0' + b']' * 70]:
            with self.subTest(data=data[:30]), self.assertRaises(common.Error):
                common.decode_json(data)
        with self.assertRaisesRegex(common.Error, 'input_size_limit'):
            common.decode_json(b'{"long":"record"}', max_bytes=5)

    def test_diagnostic_whitespace_is_data_but_never_a_path(self):
        text = 'first line\nsecond line\r\n\tindented'
        self.assertEqual(common.decode_json(common.encoded({'diagnostic': text}))['diagnostic'], text)
        with self.assertRaisesRegex(common.Error, 'unsafe_path'):
            common.relative(text)

    def test_diagnostic_text_cap_preserves_bounded_large_output(self):
        value = {'diagnostic': 'x' * 262144}
        self.assertEqual(len(common.decode_json(common.encoded(value))['diagnostic']), 262144)
        value['diagnostic'] += 'x'
        with self.assertRaisesRegex(common.Error, 'json_string_limit'):
            common.decode_json(common.encoded(value))

    def test_special_file_and_leaf_alias_are_not_read_or_hashed(self):
        source = self.root / 'source'
        source.write_bytes(b'owned content')
        alias = self.root / 'alias'
        alias.symlink_to(source)
        with self.assertRaises(OSError):
            common.sha256(alias)
        fifo = self.root / 'fifo'
        os.mkfifo(fifo)
        with self.assertRaisesRegex(common.Error, 'nonregular_input'):
            common.sha256(fifo)
        with self.assertRaisesRegex(common.Error, 'nonregular_input'):
            common.read_relative(self.root, 'fifo')

    def test_malformed_audit_source_shapes_fail_with_bounded_codes(self):
        for field, bad in [('source', None), ('acquisition', []), ('content_digests', 1)]:
            value = copy.deepcopy(self.audit)
            value['components'][0][field] = bad
            path = self.root / self.value['audit_ref']['path']
            path.write_bytes(common.encoded(value))
            self.value['audit_ref']['sha256'] = common.sha256(path)
            with self.subTest(field=field), self.assertRaises(common.Error):
                prepare.validate_inputs(self.value, self.root)

    def test_duplicate_or_missing_audit_component_is_rejected(self):
        self.audit['components'].append(copy.deepcopy(self.audit['components'][0]))
        path = self.root / self.value['audit_ref']['path']
        path.write_bytes(common.encoded(self.audit))
        self.value['audit_ref']['sha256'] = common.sha256(path)
        with self.assertRaisesRegex(common.Error, 'audit_component_identity'):
            prepare.validate_inputs(self.value, self.root)


if __name__ == '__main__':
    unittest.main()
