"""Inspect the real research profile and prove it cannot authorize execution."""
import copy
import hashlib
import json
import os
import re
import shlex
from string import Template
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tests/manager'))
sys.path.insert(0, str(REPO / 'tests/contracts'))
import validate_v2 as oracle
from fixture_factory import encoded, rewrite
from v2_fixture import build_v2_fixture, upgrade_fixture
from test_eligibility import synthetic_candidate

BUILD = REPO / os.environ.get('PEAR_MANAGER_BUILD', '.build/task9/stage4')
BINARY = BUILD / 'bin/pear-manager'
PROFILE = REPO / 'profiles/megabonk/profile.json'


class MegabonkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        receipt = json.loads((BUILD / 'build.json').read_bytes())
        assert hashlib.sha256(BINARY.read_bytes()).hexdigest() == receipt['binaries']['pear-manager']['sha256']
        for path, digest in receipt['sources'].items():
            assert hashlib.sha256((REPO / path).read_bytes()).hexdigest() == digest, path
        cls.results = []
        cls.retained = REPO / '.build/task9/runs' / ('stage5-profile-' + uuid.uuid4().hex)
        cls.retained.mkdir(parents=True)

    @classmethod
    def tearDownClass(cls):
        (cls.retained / 'results.json').write_text(json.dumps({
            'profile_sha256': hashlib.sha256(PROFILE.read_bytes()).hexdigest(),
            'binary_sha256': hashlib.sha256(BINARY.read_bytes()).hexdigest(),
            'results': cls.results, 'game_executed': False,
        }, indent=2) + '\n')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='pear-task9-profile-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.profile = json.loads(PROFILE.read_bytes())

    def native(self, command, root, entry, context='research', **options):
        args = [str(BINARY), command, '--bundle-root', str(root), '--entry', entry, '--context', context]
        for key, value in options.items():
            args += ['--' + key.replace('_', '-'), str(value)]
        process = subprocess.run(args, capture_output=True, timeout=10)
        self.assertEqual(process.stderr, b'')
        self.assertLess(len(process.stdout), 8192)
        for private in (str(self.root).encode(), b'PRIVATE_PROFILE_SENTINEL'):
            self.assertNotIn(private, process.stdout)
        result = json.loads(process.stdout)
        self.results.append({'test': self.id().split('.')[-1], 'command': command,
                             'returncode': process.returncode, 'result': result})
        return process.returncode, result

    def test_checked_in_profile_is_inspectable_by_both_consumers(self):
        expected = oracle.validate_bundle(REPO, 'profiles/megabonk/profile.json', context='research', purpose='inspect')
        code, actual = self.native('inspect', REPO, 'profiles/megabonk/profile.json')
        self.assertEqual(code, 0)
        for field in ('record_valid', 'eligible', 'outcome_codes', 'evaluation_only'):
            self.assertEqual(actual[field], expected[field], (field, expected, actual))
        self.assertTrue(actual['record_valid'] and actual['eligible'] and actual['evaluation_only'])
        self.assertEqual((self.profile['store'], self.profile['app_id'], self.profile['executable']['path']),
                         ('steam', 3405340, 'Megabonk.exe'))

    def test_documented_profile_inspection_commands(self):
        guide = (REPO / 'docs/game-profiles.md').read_text()
        matches = re.findall(r'<!-- pear-profile-inspect -->\s*```sh\n(.*?)\n```', guide, re.S)
        self.assertEqual(len(matches), 1)
        for line in matches[0].splitlines():
            args = [Template(arg).substitute(PEAR_REPO=str(REPO), PEAR_MANAGER=str(BINARY)) for arg in shlex.split(line)]
            process = subprocess.run(args, cwd=REPO, capture_output=True, timeout=10)
            self.assertEqual(process.returncode, 0, process.stdout)
            self.assertEqual(process.stderr, b'')
            self.assertLess(len(process.stdout), 8192)
            result = json.loads(process.stdout)
            self.assertTrue(result['record_valid'] and result['eligible'] and result['evaluation_only'])
            self.assertNotIn(str(REPO).encode(), process.stdout)
            self.results.append({'test': self.id().split('.')[-1], 'command': 'documented-inspect',
                                 'returncode': process.returncode, 'result': result})

    def test_unknown_current_inputs_do_not_become_executable_defaults(self):
        for field in ('game_build', 'compatibility_family', 'renderer'):
            self.assertIsNone(self.profile[field])
        for field in ('arguments', 'environment', 'operations', 'save_paths'):
            self.assertEqual(self.profile[field], [])
        self.assertEqual(self.profile['save_inventory_status']['status'], 'unknown')
        self.assertTrue(all(item['path'] is None and item['status'] == 'unknown' for item in self.profile['path_observations']))
        for feature in self.profile['features']:
            self.assertEqual(feature['status'], 'untested')
            self.assertEqual(feature['evidence'], [])
        path = self.root / 'profile.json'
        path.write_bytes(PROFILE.read_bytes())
        for purpose in ('qualification_run', 'supported_launch'):
            expected = oracle.validate_bundle(self.root, path.name, context='research', purpose=purpose)
            code, actual = self.native('evaluate', self.root, path.name, purpose=purpose)
            self.assertEqual(code, 0)  # Completed native evaluation can be ineligible.
            self.assertFalse(actual['eligible'])
            self.assertEqual(actual['eligible'], expected['eligible'])
            self.assertEqual(actual['outcome_codes'], expected['outcome_codes'])

    def test_research_request_refuses_activation_without_state_mutation(self):
        bundle = self.root / 'bundle'
        fixture = build_v2_fixture(bundle, 'research')
        rewrite(bundle, fixture, 'profile', lambda value: value.update(self.profile))
        rewrite(bundle, fixture, 'request', lambda value: value.update(purpose='qualification_run'))
        state = self.root / 'state'; state.mkdir(mode=0o700)
        policy = self.root / 'policy.json'; policy.write_bytes(encoded(fixture['policy']))
        expected = oracle.validate_bundle(bundle, 'records/request.json', context='research', purpose='qualification_run', policy=fixture['policy'])
        self.assertFalse(expected['eligible'])
        code, result = self.native('activate', bundle, 'records/request.json', state_root=state, policy=policy)
        self.assertEqual(code, 1, result)
        self.assertEqual(result['outcome_codes'], ['incompatible_family'])
        self.assertFalse(result['record_valid'])
        self.assertIn('incompatible_family', expected['outcome_codes'])
        self.assertEqual(list(state.iterdir()), [])

    def test_complete_synthetic_runtime_still_has_no_execution_authority(self):
        bundle = self.root / 'bundle'
        fixture = upgrade_fixture(bundle, synthetic_candidate(bundle))
        # Even the positive declaration-only control cannot grant real execution.
        expected = oracle.validate_bundle(bundle, 'records/request.json', context='runtime', purpose='qualification_run', policy=fixture['policy'])
        self.assertTrue(expected['eligible'], expected)
        state = self.root / 'state'; state.mkdir(mode=0o700)
        policy = self.root / 'policy.json'; policy.write_bytes(encoded(fixture['policy']))
        code, result = self.native('activate', bundle, 'records/request.json', context='runtime', state_root=state, policy=policy)
        self.assertEqual(code, 3, result)
        self.assertEqual(result['outcome_codes'], ['runtime_authorization_unavailable'])
        self.assertEqual(list(state.iterdir()), [])

    def test_guessed_save_mapping_or_unproved_feature_cannot_pass_inspection(self):
        for mutation in ('save', 'feature', 'path'):
            with self.subTest(mutation=mutation):
                value = copy.deepcopy(self.profile)
                if mutation == 'save': value['save_paths'] = [{'root': 'saves', 'path': 'guessed.dat'}]
                if mutation == 'feature': value['features'][0]['status'] = 'passed'
                if mutation == 'path': value['path_observations'][0]['path'] = {'path_type': 'windows_user_relative', 'path': 'guessed/config.json'}
                (self.root / 'profile.json').write_bytes(encoded(value))
                expected = oracle.validate_bundle(self.root, 'profile.json', context='research', purpose='inspect')
                code, actual = self.native('inspect', self.root, 'profile.json')
                self.assertNotEqual(code, 0)
                self.assertFalse(expected['record_valid'])
                self.assertFalse(actual['record_valid'])

    def test_private_or_malformed_metadata_is_not_echoed(self):
        value = copy.deepcopy(self.profile)
        value['provenance'][0]['url'] = 'https://user:PRIVATE_PROFILE_SENTINEL@example.invalid/source'
        (self.root / 'profile.json').write_bytes(encoded(value))
        code, result = self.native('inspect', self.root, 'profile.json')
        self.assertNotEqual(code, 0)
        self.assertFalse(result['record_valid'])


if __name__ == '__main__':
    unittest.main()
