"""Fresh-wrapper tests using real six-case parsers and synthetic platform boundaries.

No compiler, signing command, native process or restricted operation executes.
Raw lifecycle/fault/cleanup validators remain real; only their Mach-O/signing
prerequisites and toolchain observation are supplied by deterministic test doubles.
"""
import copy
import hashlib
from pathlib import Path
import plistlib
import sys
import tempfile
import unittest
from unittest.mock import patch

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY / 'tools/wine'))
import arena_reproduction as fresh
from common import Error, encoded, sha256
from test_arena_evidence import materialize
from test_pe_arena_probe import BINARY


class FreshArenaTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name).resolve()
        self.root = self.repo / '.build/task4/fresh'
        self.local = self.repo / '.build/task4/private/signing.json'
        self.local.parent.mkdir(parents=True)
        self.profile = self.repo / 'profile.provisionprofile'
        self.profile.write_bytes(b'synthetic-profile-not-authorized')
        self.local.write_bytes(encoded({'schema_version': 1, 'record_kind': 'wine_local_signing',
            'scope': 'wine_component', 'profile_path': str(self.profile),
            'bundle_identifier': fresh.signing.BUNDLE_ID}))
        for name in fresh.PRODUCER_FILES:
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((REPOSITORY / name).read_bytes())
        self.claims = {fresh.signing.APP_ID: 'PREFIX.' + fresh.signing.BUNDLE_ID,
            fresh.signing.TEAM_ID: 'TESTTEAM', fresh.signing.CROSS_KEYS[0]: True}
        self.calls = []
        create = fresh.probe.base.create_output
        patches = [patch.object(fresh, 'REPO', self.repo),
            patch.object(fresh.signing, 'REPO', self.repo),
            patch.object(fresh.probe.base, 'create_output', side_effect=lambda path: create(path, repo=self.repo)),
            patch.object(fresh.signing, '_authorization', side_effect=self.authorize),
            patch.object(fresh.signing, '_signature', side_effect=self.signature),
            patch.object(fresh.probe, 'inspect_closure', return_value={'synthetic': True}),
            patch.object(fresh, '_toolchain', side_effect=lambda report: report['toolchain']),
            patch.object(fresh.arena_evidence, 'verify_artifacts', side_effect=lambda root, report: report['binaries']),
            patch.object(fresh.probe, 'run', side_effect=self.probe_run),
            patch('subprocess.Popen', side_effect=AssertionError('no execution in synthetic tests'))]
        for candidate in patches:
            candidate.start()
            self.addCleanup(candidate.stop)

    def authorize(self, path, bundle, events):
        events.append({'operation': 'synthetic.authorization', 'exit_code': 0})
        return {'profile_sha256': sha256(path), 'profile_bytes': Path(path).read_bytes(),
                'claims': dict(self.claims), 'checks': {key: True for key in fresh.arena_evidence.PROFILE_CHECKS}}

    def signature(self, path, claims, team, label, events):
        self.calls.append(('signature', str(path)))
        events.append({'operation': label + '.verify', 'exit_code': 0})
        return {'synthetic': True}

    def probe_run(self, local_signing, output, require_empty, *, policy):
        self.calls.append(('probe', policy, require_empty))
        self.assertEqual(local_signing, self.local)
        self.assertEqual(policy, 'page-wx')
        output.mkdir(mode=0o700)
        inputs = {}
        for name in (*fresh.probe.PRODUCER_FILES, *fresh.probe.SOURCE_FILES, fresh.probe.LOCK_FILE):
            raw = (self.repo / name).read_bytes()
            path = output / 'inputs' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            inputs[name] = hashlib.sha256(raw).hexdigest()
        cases = []
        original = output / 'original'
        original.mkdir()
        row, directory = materialize(original)
        row['variant'] = 'original-claims'
        (directory / 'case.json').write_bytes(encoded(row))
        directory.rename(output / 'original-claims-lifecycle')
        original.rmdir()
        cases.append(row)
        for mode in fresh.probe.POLICIES['page-wx']:
            row, _ = materialize(output, mode)
            cases.append(row)
        info = plistlib.dumps({'CFBundleIdentifier': fresh.signing.BUNDLE_ID,
                             'CFBundleExecutable': BINARY['name']})
        (output / 'Info.plist').write_bytes(info)
        binaries, helpers = {}, {}
        for variant in fresh.probe.VARIANTS:
            contents = output / variant / 'ArenaProbe.app/Contents'
            (contents / 'MacOS').mkdir(parents=True)
            binary = contents / 'MacOS' / BINARY['name']
            binary.write_bytes(b'synthetic-native-placeholder')
            (contents / 'Info.plist').write_bytes(info)
            (contents / 'embedded.provisionprofile').write_bytes(self.profile.read_bytes())
            claims = dict(self.claims)
            if variant == 'allow-jit':
                claims[fresh.signing.PROFILE.BASELINE.ALLOW_JIT] = True
            (output / variant / 'claims.plist').write_bytes(plistlib.dumps(claims))
            binaries[variant] = {**BINARY, 'claims': claims, 'closure': {'synthetic': True}}
        for role in ('helper', 'sentinel'):
            (output / role).write_bytes(b'synthetic-helper-placeholder')
            helpers[role] = {'sha256': sha256(output / role), 'closure': {'synthetic': True}}
        report = {'schema_version': 1, 'record_kind': 'pear_pe_arena_prerequisite',
            'policy': 'page-wx', 'status': 'passed', 'native_prerequisite_passed': True,
            'qualification': False, **fresh.SCOPES,
            'inputs': inputs, 'producer_sha256': {key: inputs[key] for key in fresh.probe.PRODUCER_FILES},
            'source_sha256': inputs[fresh.probe.SOURCE_FILES[0]], 'binaries': binaries, 'helpers': helpers,
            'toolchain': {'lock_sha256': inputs[fresh.probe.LOCK_FILE],
                'clang': {'sha256': 'a' * 64}, 'sdk': {'settings_sha256': 'b' * 64}},
            'events': [{'operation': 'post.' + role + '.' + suffix, 'exit_code': 0}
                for role in ('helper', 'sentinel', 'original-claims', 'allow-jit')
                for suffix in ('verify', 'metadata', 'claims')], 'cases': cases}
        (output / 'report.json').write_bytes(encoded(report))
        return report

    def complete(self):
        return fresh.run(self.local, self.root)

    def test_current_six_raw_cases_are_revalidated_and_summary_excludes_private_data(self):
        result = self.complete()
        observed = fresh.validate(self.root, self.local)
        self.assertTrue(result['gate_passed'])
        self.assertTrue(observed['gate_passed'])
        self.assertEqual(len(observed['cases']), 6)
        self.assertEqual(sum(row['fault_control'] is not None for row in observed['cases']), 4)
        self.assertEqual([row for row in self.calls if row[0] == 'probe'], [('probe', 'page-wx', True)])
        text = encoded(observed).decode()
        for private in (str(self.repo), 'TESTTEAM', 'PREFIX.', 'synthetic-profile', 'fault_pc', 'nonce'):
            self.assertNotIn(private, text)
        self.assertTrue(all(observed[key] is False for key in fresh.SCOPES))

    def test_refuses_existing_output_without_probe_or_overwrite(self):
        self.complete()
        before = (self.root / fresh.RECEIPT).read_bytes()
        self.calls.clear()
        with self.assertRaisesRegex(Error, 'destination_exists'):
            fresh.run(self.local, self.root)
        self.assertEqual((self.root / fresh.RECEIPT).read_bytes(), before)
        self.assertFalse(self.calls)

    def test_probe_failure_preserves_private_terminal_and_original_error(self):
        def fail(*args, **kwargs):
            return {'native_prerequisite_passed': False, 'error': 'synthetic_owned_cleanup_failed'}
        with patch.object(fresh.probe, 'run', side_effect=fail), self.assertRaisesRegex(Error, 'synthetic_owned_cleanup_failed'):
            self.complete()
        terminal = fresh._read(self.root, fresh.RECEIPT)
        self.assertFalse(terminal['gate_passed'])
        self.assertEqual(terminal['error'], 'synthetic_owned_cleanup_failed')
        self.assertTrue((self.root / 'start.json').is_file())
        with self.assertRaises(Error):
            fresh.validate(self.root, self.local)

    def test_all_six_cases_must_pass_even_if_probe_allow_jit_summary_passes(self):
        original = self.probe_run
        def failed_baseline(*args, **kwargs):
            report = original(*args, **kwargs)
            report['cases'][0]['passed'] = False
            root = Path(args[1])
            (root / 'original-claims-lifecycle/case.json').write_bytes(encoded(report['cases'][0]))
            (root / 'report.json').write_bytes(encoded(report))
            return report
        with patch.object(fresh.probe, 'run', side_effect=failed_baseline), self.assertRaisesRegex(Error, 'arena_receipt_case_failed'):
            self.complete()
        self.assertFalse(fresh._read(self.root, fresh.RECEIPT)['gate_passed'])

    def test_raw_fault_and_cleanup_mutation_cannot_be_hidden_by_summary(self):
        self.complete()
        path = self.root / 'probe/allow-jit-protected-write/probe.stdout.log'
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(Error, 'arena_receipt_bytes_changed'):
            fresh.validate(self.root, self.local)

    def test_changed_current_source_is_rejected_before_platform_reauthorization(self):
        self.complete()
        path = self.repo / fresh.probe.SOURCE_FILES[0]
        path.write_bytes(path.read_bytes() + b'\n')
        with patch.object(fresh.signing, '_authorization', side_effect=AssertionError('must reject first')):
            with self.assertRaisesRegex(Error, 'fresh_arena_current_input_changed'):
                fresh.validate(self.root, self.local)

    def test_changed_profile_snapshot_or_live_profile_rejected(self):
        self.complete()
        for path in (self.profile, self.root / fresh.PROFILE):
            before = path.read_bytes()
            path.write_bytes(before + b'changed')
            with self.assertRaisesRegex(Error, 'fresh_arena_profile_changed'):
                fresh.validate(self.root, self.local)
            path.write_bytes(before)

    def test_actual_bundle_metadata_and_claims_cannot_be_substituted(self):
        self.complete()
        contents = self.root / 'probe/allow-jit/ArenaProbe.app/Contents'
        for path in (contents / 'Info.plist', contents / 'embedded.provisionprofile',
                     self.root / 'probe/allow-jit/claims.plist'):
            before = path.read_bytes()
            path.write_bytes(plistlib.dumps({}))
            with self.assertRaises(Error):
                fresh.validate(self.root, self.local)
            path.write_bytes(before)

    def test_current_signature_failure_rejects_retained_success(self):
        self.complete()
        with patch.object(fresh.signing, '_signature', side_effect=Error('synthetic_expired_signature')):
            with self.assertRaisesRegex(Error, 'synthetic_expired_signature'):
                fresh.validate(self.root, self.local)

    def test_typed_summary_tampering_is_rejected(self):
        self.complete()
        path = self.root / fresh.RECEIPT
        row = fresh._read(self.root, fresh.RECEIPT)
        row['observations']['authorization']['profile_snapshot_bound'] = 1
        path.write_bytes(encoded(row))
        with self.assertRaisesRegex(Error, 'fresh_arena_observations_changed'):
            fresh.validate(self.root, self.local)

    def test_snapshot_changed_during_probe_is_retained_failure(self):
        original = self.probe_run
        def drift(*args, **kwargs):
            result = original(*args, **kwargs)
            (self.root / fresh.PROFILE).write_bytes(b'changed')
            return result
        with patch.object(fresh.probe, 'run', side_effect=drift), self.assertRaisesRegex(Error, 'fresh_arena_profile_changed'):
            self.complete()
        self.assertEqual(fresh._read(self.root, fresh.RECEIPT)['error'], 'fresh_arena_profile_changed')


if __name__ == '__main__':
    unittest.main()
