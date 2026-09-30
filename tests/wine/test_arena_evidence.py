"""Offline receipt rejection tests; synthetic records never qualify execution."""
import copy
import hashlib
import json
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
import arena_evidence as receipt
from common import Error, encoded
from test_pe_arena_probe import BINARY, IDENTITY, NONCE, fault_evidence, helper, synthetic_trace


def materialize(root, mode='lifecycle'):
    observations = synthetic_trace(mode, 'page-wx')
    sentinel = helper('pear_sentinel_ready')
    sentinel.update(pid=103)
    raw = {('probe', 'stdout'): b''.join(json.dumps(row).encode() + b'\n'
             for row in [helper(), *observations]), ('probe', 'stderr'): b'',
           ('sentinel', 'stdout'): json.dumps(sentinel).encode() + b'\n' +
               json.dumps({'version': 1, 'record_kind': 'pear_sentinel_done', 'signal': 0, 'command': 81}).encode() + b'\n',
           ('sentinel', 'stderr'): b''}
    processes = {role: {'identity': {**IDENTITY, 'pid': pid}, 'reaped': True, 'fork_seen': False,
                       'setup_error': None, 'emergency_cleanup': None,
                       'exit_code': -int(signal.SIGBUS) if role == 'probe' and mode != 'lifecycle' else 0}
                 for role, pid in [('probe', 102), ('sentinel', 103)]}
    cleanup = lambda role: {'complete': True, 'errors': [], 'observation_gap': False,
                            'reaped': {role: True}, 'signals': []}
    row = {'schema_version': 1, 'record_kind': 'pear_pe_arena_case', 'variant': 'allow-jit',
           'mode': mode, 'policy': 'page-wx', 'nonce': NONCE, 'passed': True,
           'qualification': False, 'wine_execution': False, 'runtime_qualified': False, 'game_qualified': False,
           'outcome': 'exited', 'error': None, 'stream_error': None, 'assessment_error': None,
           'native_failure': None, 'crash': None, 'observations': observations, 'processes': processes,
           'cleanup': cleanup('probe'), 'sentinel_cleanup': cleanup('sentinel'), 'sentinel_survived': True,
           'logs': []}
    folder = root / ('allow-jit-' + mode)
    folder.mkdir()
    for (role, channel), data in raw.items():
        name = role + '.' + channel + '.log'
        (folder / name).write_bytes(data)
        row['logs'].append({'role': role, 'channel': channel, 'path': name,
            'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'observed_bytes': len(data),
            'eof': True, 'write_error': None})
    if mode != 'lifecycle':
        report, _, armed = fault_evidence(mode, 'page-wx')
        data = encoded({}) + encoded(report)
        (folder / 'crash.ips').write_bytes(data)
        matched = receipt.probe.crash_matches(report, row, armed, BINARY)
        row['crash'] = {'path': 'crash.ips', 'sha256': hashlib.sha256(data).hexdigest(), **matched}
    (folder / 'case.json').write_bytes(encoded(row))
    return row, folder


class ReceiptTests(unittest.TestCase):
    def test_complete_raw_lifecycle_exports_only_finite_public_facts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            row, _ = materialize(root)
            with patch('subprocess.Popen', side_effect=AssertionError('offline only')):
                result = receipt.case_receipt(root, row, BINARY, 'page-wx')
            self.assertTrue(result['passed'])
            self.assertEqual(result['actual_observation_counts']['publication'], 6)
            self.assertEqual(result['actual_observation_counts']['leaf_return'], 22)
            text = json.dumps(result)
            for field in ('nonce', 'module_base', 'fault_pc', 'start_sec', 'identity'):
                self.assertNotIn(field, text)

    def test_negative_control_reparses_actual_ips_identity_and_fault(self):
        for mode in ('protected-write', 'retired-call', 'data-exec', 'preparation-exec'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                row, folder = materialize(root, mode)
                self.assertTrue(receipt.case_receipt(root, row, BINARY, 'page-wx')['fault_control']['matched'])
                report = receipt.probe.parse_crash((folder / 'crash.ips').read_bytes())
                report['threads'][0]['threadState']['pc']['value'] += 4
                data = encoded({}) + encoded(report)
                (folder / 'crash.ips').write_bytes(data)
                row['crash']['sha256'] = hashlib.sha256(data).hexdigest()
                (folder / 'case.json').write_bytes(encoded(row))
                with self.assertRaises(Error): receipt.case_receipt(root, row, BINARY, 'page-wx')

    def test_case_summary_cannot_replace_original_streams(self):
        for mode in ('raw-byte', 'raw-record', 'case-record', 'cleanup', 'missing-log'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                row, folder = materialize(root)
                if mode == 'raw-byte':
                    with (folder / 'probe.stdout.log').open('ab') as stream: stream.write(b' ')
                elif mode == 'raw-record':
                    row['observations'].pop()
                    (folder / 'case.json').write_bytes(encoded(row))
                elif mode == 'case-record': row['passed'] = False
                elif mode == 'cleanup':
                    row['cleanup']['observation_gap'] = True
                    (folder / 'case.json').write_bytes(encoded(row))
                else:
                    row['logs'].pop()
                    (folder / 'case.json').write_bytes(encoded(row))
                with self.assertRaises(Error): receipt.case_receipt(root, row, BINARY, 'page-wx')

    def test_legacy_adapter_cannot_relabel_current_success_as_thread_jit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            row, folder = materialize(root)
            with self.assertRaises(Error): receipt.case_receipt(root, row, BINARY, 'thread-jit', legacy=True)

    def test_recorded_signature_cannot_accept_unlisted_claims_or_unverified_facts(self):
        signature = {'claim_keys': [], 'hardened_runtime': True, 'same_team': True,
                     'strict_verification': True, 'ad_hoc': False, 'category': 'apple_development',
                     'code_directory_page_size': 4096}
        receipt.recorded_signature(signature, set(), 4096)
        for key, value in [('claim_keys', [receipt.JIT]), ('ad_hoc', True),
                           ('strict_verification', False), ('code_directory_page_size', True)]:
            with self.subTest(key=key), self.assertRaises(Error):
                receipt.recorded_signature({**signature, key: value}, set(), 4096)

    def test_application_prefix_can_differ_from_recorded_team(self):
        claims = {receipt.signing.APP_ID: 'DISTINCTPREFIX.' + receipt.signing.BUNDLE_ID,
                  receipt.signing.TEAM_ID: 'TEAMIDENTIFIER', receipt.signing.CROSS_KEYS[0]: True}
        for variant in ('original-claims', 'allow-jit'):
            candidate = {**claims, **({receipt.JIT: True} if variant == 'allow-jit' else {})}
            self.assertEqual(receipt.recorded_claims(candidate, variant), set(candidate))
        for key, value in [(receipt.signing.APP_ID, 'DISTINCTPREFIX.other.application'),
                           (receipt.signing.APP_ID, '*.' + receipt.signing.BUNDLE_ID),
                           (receipt.signing.APP_ID, '.' + receipt.signing.BUNDLE_ID),
                           (receipt.signing.TEAM_ID, ''), (receipt.signing.CROSS_KEYS[0], 1)]:
            with self.subTest(key=key, value=value), self.assertRaises(Error):
                receipt.recorded_claims({**claims, key: value}, 'original-claims')

    def test_unretained_profile_and_bundle_hashes_cannot_be_claimed_verified(self):
        with patch.object(receipt.signing, '_authorization', side_effect=AssertionError('no reauthorization')), \
             patch.object(receipt.signing, '_signature', side_effect=AssertionError('no signing tool')):
            result = receipt.authorization_receipt(False)
        self.assertEqual(result['profile_byte_hash_binding'], 'unavailable_not_retained_at_run')
        self.assertEqual(result['bundle_metadata_byte_binding'], 'unavailable_not_retained_at_run')
        self.assertFalse(result['current_profile_authorization_assessed'])
        self.assertFalse(result['current_bundle_signature_verified'])

    def test_snapshot_hashing_refuses_path_escape_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'data').write_bytes(b'original')
            (root / 'link').symlink_to('data')
            digest = hashlib.sha256(b'original').hexdigest()
            self.assertEqual(receipt.bound_bytes(root, 'data', digest), b'original')
            for name in ('../data', 'link'):
                with self.subTest(name=name), self.assertRaises((Error, OSError)):
                    receipt.bound_bytes(root, name, digest)


if __name__ == '__main__':
    unittest.main()
