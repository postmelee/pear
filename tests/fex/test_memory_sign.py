"""Original pure authorization/signing boundary controls; no Apple/native calls.

Synthetic authorization never establishes a real profile, certificate or grant.
"""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import plistlib
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.fex import memory_sign as signer, memory_reuse as reuse
from tools.fex.common import Error

NOW = datetime(2026, 10, 3, tzinfo=timezone.utc)
CERT = b'original synthetic certificate; no Apple identity'
TEAM, PREFIX, DEVICE = 'SYNTHETIC-TEAM', 'SYNTHETIC-PREFIX', 'SYNTHETIC-DEVICE'


class ReusedAuthorizationPolicy(unittest.TestCase):
    def test_exact_explicit_app_and_single_boolean_grant_remain_required(self):
        with reuse.wine_namespace() as (policy, _):
            identities = '  1) ' + hashlib.sha1(CERT).hexdigest().upper() + ' "Apple Development: Synthetic"'
            base = dict(ExpirationDate=NOW+timedelta(days=1), Platform=['OSX'], TeamIdentifier=[TEAM],
                ApplicationIdentifierPrefix=[PREFIX], ProvisionedDevices=[DEVICE], DeveloperCertificates=[CERT],
                Entitlements={policy.APP_ID: PREFIX+'.'+policy.BUNDLE_ID, policy.TEAM_ID: TEAM,
                              policy.CROSS_KEYS[0]: True})
            good = policy.profile_authorization(base, identities, DEVICE, policy.BUNDLE_ID, NOW)
            before = deepcopy(good)
            claims = policy.loader_claims(good, 'page-wx')
            self.assertEqual(good, before)
            self.assertEqual(set(claims), {policy.APP_ID, policy.TEAM_ID, policy.CROSS_KEYS[0],
                                         policy.PROFILE.BASELINE.ALLOW_JIT})
            for mutation in ('wildcard', 'other_app', 'integer_grant', 'two_grants', 'expired', 'other_device'):
                value = deepcopy(base); device = DEVICE
                if mutation == 'wildcard': value['Entitlements'][policy.APP_ID] = PREFIX+'.*'
                elif mutation == 'other_app': value['Entitlements'][policy.APP_ID] = PREFIX+'.other'
                elif mutation == 'integer_grant': value['Entitlements'][policy.CROSS_KEYS[0]] = 1
                elif mutation == 'two_grants': value['Entitlements'][policy.CROSS_KEYS[1]] = True
                elif mutation == 'expired': value['ExpirationDate'] = NOW
                else: device = 'OTHER-SYNTHETIC-DEVICE'
                with self.subTest(mutation=mutation), self.assertRaises(policy.Error):
                    policy.profile_authorization(value, identities, device, policy.BUNDLE_ID, NOW)

    def test_namespace_restores_every_prior_module_even_after_failure(self):
        names = ('common', 'prepare', 'toolchain', 'build', 'signing', 'run_fixtures')
        before = {name: sys.modules.get(name) for name in names}
        with self.assertRaisesRegex(RuntimeError, 'original controlled exception'):
            with reuse.wine_namespace(): raise RuntimeError('original controlled exception')
        self.assertEqual({name: sys.modules.get(name) for name in names}, before)


class SigningTransaction(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.build = self.root/'build'; self.output = self.root/'signed'
        (self.build/'unsigned').mkdir(parents=True); self.output.mkdir()
        (self.build/'build.json').write_text('{}')
        self.built = {'artifacts': []}
        for name in signer.ARTIFACTS:
            p = self.build/'unsigned'/name; p.write_bytes(('owned synthetic '+name).encode())
            self.built['artifacts'].append({'path': 'unsigned/'+name, 'sha256': signer.sha256(p), 'size_bytes': p.stat().st_size})
        self.claims = {'application-identifier': 'SYNTHETIC.'+'io.github.postmelee.pear.wine-loader',
            'com.apple.developer.team-identifier': TEAM, 'com.apple.developer.test-cross-grant': True}
        self.auth = dict(profile_sha256='1'*64, profile_bytes=b'synthetic CMS placeholder',
            claims=self.claims, identity='synthetic identity', checks={'synthetic': True},
            granted_cross_architecture_key='com.apple.developer.test-cross-grant')
        self.effective = dict(self.claims, **{'com.apple.security.cs.allow-jit': True})
        self.observed = []
        self.on_authorize = lambda: None
        def authorize(*_): self.on_authorize(); return self.auth
        def native(argv, label, events, timeout):
            events.append({'id': label, 'argv': argv, 'status': 'completed', 'exit_code': 0})
            return b'owned synthetic stdout', b''
        def signature(target, claims, team, name, events):
            self.observed.append((name, claims, team)); return {'synthetic': True}
        def origin(before, after):
            if before.read_bytes() != after.read_bytes(): raise Error('synthetic_origin_changed')
            return {'synthetic': True}
        self.policy = SimpleNamespace(Error=Error, BUNDLE_ID='io.github.postmelee.pear.wine-loader',
            TEAM_ID='com.apple.developer.team-identifier', _native=native, _authorization=authorize,
            loader_claims=lambda *_: self.effective, _signature=signature, verify_code_origin=origin)
        @contextmanager
        def namespace(): yield self.policy, None
        self.enterContext(patch.object(signer, 'wine_namespace', namespace))
        self.enterContext(patch.object(signer, 'operation_output', return_value=self.output))
        self.verify = self.enterContext(patch.object(signer, 'verify_build', return_value=self.built))

    def test_restricted_claims_stay_only_on_two_owner_executables(self):
        value = signer.sign(self.build, '/synthetic/profile', self.output)
        self.assertTrue(value['passed']); self.assertFalse(value['native_execution'])
        self.assertFalse(value['runtime_eligible'])
        self.assertEqual([claims for _, claims, _ in self.observed], [self.effective, self.effective, {}, {}])
        self.assertTrue(all(team == TEAM for _, _, team in self.observed))
        for index, row in enumerate(value['artifacts']):
            executable = self.output/row['path']
            if index < 2:
                self.assertEqual((executable.parent.parent/'embedded.provisionprofile').read_bytes(), self.auth['profile_bytes'])
            self.assertEqual(row['unsigned_sha256'], next(r['sha256'] for r in self.built['artifacts']
                if r['path'] == 'unsigned/'+row['name']))

    def test_unsigned_mutation_during_authorization_does_not_get_old_build_reference(self):
        def mutation(): (self.build/'unsigned'/signer.ARTIFACTS[0]).write_bytes(b'changed after original verification')
        self.on_authorize = mutation
        with self.assertRaises(Error): signer.sign(self.build, '/synthetic/profile', self.output)
        self.assertFalse((self.output/'signing.json').exists())
        self.assertIs(plistlib.loads((self.output/'claims.plist').read_bytes())['com.apple.security.cs.allow-jit'], True)

    def test_private_signature_failure_does_not_publish_success(self):
        def failure(*_): raise Error('original_signature_error')
        self.policy._signature = failure
        with self.assertRaisesRegex(Error, 'original_signature_error'):
            signer.sign(self.build, '/synthetic/profile', self.output)
        self.assertFalse((self.output/'signing.json').exists())
        import json
        failure_record = json.loads((self.output/'failed.json').read_text())
        self.assertFalse(failure_record['passed']); self.assertEqual(failure_record['error'], 'original_signature_error')


if __name__ == '__main__': unittest.main()
