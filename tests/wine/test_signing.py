"""Pure signing-policy and owned payload tests; no Apple authorization is mocked as real.

Synthetic certificates, device IDs and signatures test rejection boundaries only.
All native commands are replaced with explicit test doubles in preparation tests.
"""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import os
from pathlib import Path
import plistlib
import shutil
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[2] / 'tools/wine'
sys.path.insert(0, str(TOOLS))
import common
import signing

NOW = datetime(2026, 9, 29, tzinfo=timezone.utc)
CERT = b'owned synthetic certificate; never an Apple signing identity'
FINGERPRINT = hashlib.sha1(CERT).hexdigest().upper()
TEAM = 'TESTTEAMONLY'
PREFIX = 'TESTPREFIXONLY'
DEVICE = 'SYNTHETIC-DEVICE-ONLY'
IDENTITIES = '  1) ' + FINGERPRINT + ' "Apple Development: Synthetic Fixture (' + TEAM + ')"'


def profile_fixture():
    return {'ExpirationDate': NOW + timedelta(days=365), 'Platform': ['OSX'],
            'TeamIdentifier': [TEAM], 'ApplicationIdentifierPrefix': [PREFIX],
            'Entitlements': {signing.APP_ID: PREFIX + '.' + signing.BUNDLE_ID,
                             signing.TEAM_ID: TEAM, signing.CROSS_KEYS[0]: True,
                             'com.apple.security.get-task-allow': True},
            'ProvisionedDevices': [DEVICE], 'DeveloperCertificates': [CERT]}


def private_fixture():
    result = signing.profile_authorization(profile_fixture(), IDENTITIES, DEVICE, signing.BUNDLE_ID, NOW)
    data = b'owned synthetic CMS placeholder, not a profile'
    result.update(profile_bytes=data, profile_sha256=hashlib.sha256(data).hexdigest())
    return result


def metadata(flags='10000', team=TEAM, page_size=4096):
    return ('CodeDirectory v=20500 size=512 flags=0x' + flags + '(runtime) hashes=10+7\n'
            'Authority=Apple Development: Synthetic Fixture\nTeamIdentifier=' + team + '\nPage size=' + str(page_size) + '\n')


def macho(filetype=2, cpu=signing.MACH_ARM64):
    return struct.pack('<8I', 0xfeedfacf, cpu, 0, filetype, 0, 0, 0, 0) + b'owned fixture bytes'


def signed_macho(signature=b'old synthetic signature', include_command=True, flags=0):
    command_count = 3 if include_command else 2
    command_size = 160 if include_command else 144
    end = 768 + (len(signature) if include_command else 0)
    header = struct.pack('<8I', 0xfeedfacf, signing.MACH_ARM64, 0, 2,
                         command_count, command_size, flags, 0)
    text = struct.pack('<II16s4Q4I', 0x19, 72, b'__TEXT', 0x100000000, 4096, 0, 512, 5, 5, 0, 0)
    linkedit = struct.pack('<II16s4Q4I', 0x19, 72, b'__LINKEDIT', 0x100001000, 4096,
                           512, end - 512, 1, 1, 0, 0)
    command = struct.pack('<4I', 0x1d, 16, 768, len(signature)) if include_command else b''
    data = (header + text + linkedit + command).ljust(512, b'\0')
    data += b'owned executable and symbol bytes'.ljust(256, b'\0')
    return data + (signature if include_command else b'')


class CodeOriginTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.before, self.after = root / 'unsigned', root / 'signed'
        self.before.write_bytes(signed_macho())
        self.after.write_bytes(signed_macho(b'a different, longer synthetic code signature'))

    def test_signature_replacement_and_linkedit_resize_are_accepted(self):
        signing.verify_code_origin(self.before, self.after)

    def test_added_signature_command_uses_only_existing_zero_padding(self):
        self.before.write_bytes(signed_macho(include_command=False))
        signing.verify_code_origin(self.before, self.after)
        data = bytearray(self.before.read_bytes())
        data[176] = 1
        self.before.write_bytes(data)
        with self.assertRaisesRegex(common.Error, 'signing_overwrote_load_padding'):
            signing.verify_code_origin(self.before, self.after)

    def test_instruction_data_header_and_other_load_command_changes_fail(self):
        for offset in (520, 24, 32 + 24):
            data = bytearray(signed_macho(b'a different, longer synthetic code signature'))
            data[offset] ^= 1
            self.after.write_bytes(data)
            with self.subTest(offset=offset), self.assertRaisesRegex(common.Error, 'signed_code_origin_mismatch'):
                signing.verify_code_origin(self.before, self.after)

    def test_signature_range_trailing_payload_and_segment_growth_fail(self):
        original = signed_macho(b'a different, longer synthetic code signature')
        for kind in ('trailing', 'range', 'vmsize'):
            data = bytearray(original)
            if kind == 'trailing': data += b'extra'
            if kind == 'range': struct.pack_into('<I', data, 184, 512)
            if kind == 'vmsize': struct.pack_into('<Q', data, 136, 1 << 30)
            self.after.write_bytes(data)
            with self.subTest(kind=kind), self.assertRaises(common.Error):
                signing.verify_code_origin(self.before, self.after)


class ProfileTests(unittest.TestCase):
    def test_exact_wine_profile_has_no_probe_jit_or_debug_claims(self):
        value = private_fixture()
        self.assertEqual(set(value['claims']), {signing.APP_ID, signing.TEAM_ID, signing.CROSS_KEYS[0]})
        self.assertNotIn(signing.PROFILE.BASELINE.ALLOW_JIT, value['claims'])
        self.assertNotIn('get-task-allow', str(value['claims']))
        self.assertNotIn(TEAM, str(value['checks']))
        self.assertTrue(all(value['checks'].values()))

    def test_probe_identity_is_not_transferred_to_wine(self):
        profile = profile_fixture()
        profile['Entitlements'][signing.APP_ID] = PREFIX + '.' + signing.PROFILE.DEFAULT_BUNDLE_ID
        with self.assertRaisesRegex(common.Error, 'profile_application_mismatch'):
            signing.profile_authorization(profile, IDENTITIES, DEVICE, signing.BUNDLE_ID, NOW)
        with self.assertRaisesRegex(common.Error, 'wine_application_identifier_mismatch'):
            signing.profile_authorization(profile, IDENTITIES, DEVICE, signing.PROFILE.DEFAULT_BUNDLE_ID, NOW)

    def test_expired_wrong_device_certificate_or_ambiguous_grant_fails(self):
        for kind in ('expired', 'device', 'certificate', 'grant', 'integer_grant', 'wildcard'):
            profile = profile_fixture()
            identities, device = IDENTITIES, DEVICE
            if kind == 'expired': profile['ExpirationDate'] = NOW
            if kind == 'device': device = 'OTHER'
            if kind == 'certificate': identities = ''
            if kind == 'grant': profile['Entitlements'][signing.CROSS_KEYS[1]] = True
            if kind == 'integer_grant': profile['Entitlements'][signing.CROSS_KEYS[0]] = 1
            if kind == 'wildcard': profile['Entitlements'][signing.APP_ID] = PREFIX + '.*'
            with self.subTest(kind=kind), self.assertRaises(common.Error):
                signing.profile_authorization(profile, identities, device, signing.BUNDLE_ID, NOW)

    def test_only_actual_alternative_grant_is_selected(self):
        profile = profile_fixture()
        del profile['Entitlements'][signing.CROSS_KEYS[0]]
        profile['Entitlements'][signing.CROSS_KEYS[1]] = True
        value = signing.profile_authorization(profile, IDENTITIES, DEVICE, signing.BUNDLE_ID, NOW)
        self.assertIn(signing.CROSS_KEYS[1], value['claims'])
        self.assertNotIn(signing.CROSS_KEYS[0], value['claims'])

    def test_loader_code_signature_pages_match_four_kib_layout(self):
        claims = private_fixture()['claims']
        self.assertEqual(signing.signature_check(metadata(), plistlib.dumps(claims), claims, TEAM)
                         ['code_directory_page_size'], 4096)
        with self.assertRaisesRegex(common.Error, 'loader_signature_page_size_mismatch'):
            signing.signature_check(metadata(page_size=16384), plistlib.dumps(claims), claims, TEAM)
        self.assertEqual(signing.signature_check(metadata(page_size=16384), b'', {}, TEAM)
                         ['code_directory_page_size'], 16384)
        for meta in (metadata().replace('Page size=4096\n', ''), metadata() + 'Page size=4096\n',
                     metadata(page_size=0)):
            with self.subTest(meta=meta), self.assertRaises(common.Error):
                signing.signature_check(meta, plistlib.dumps(claims), claims, TEAM)

    def test_server_and_libraries_require_zero_entitlements(self):
        self.assertEqual(signing.signature_check(metadata(), b'', {}, TEAM)['claim_keys'], [])
        for key in (*signing.CROSS_KEYS, signing.PROFILE.BASELINE.ALLOW_JIT,
                    'com.apple.security.cs.disable-library-validation',
                    'com.apple.security.cs.allow-unsigned-executable-memory'):
            with self.subTest(key=key), self.assertRaisesRegex(common.Error, 'entitlements_unexpected'):
                signing.signature_check(metadata(), plistlib.dumps({key: True}), {}, TEAM)

    def test_malformed_effective_claims_are_stable_rejections(self):
        for value in (b'not a plist', b'<?xml version="1.0"?><plist><dict><key>bad</plist>'):
            with self.subTest(value=value), self.assertRaisesRegex(common.Error, 'entitlements_invalid'):
                signing.signature_check(metadata(), value, {}, TEAM)

    def test_hardened_real_signature_and_exact_claim_types_required(self):
        claims = private_fixture()['claims']
        self.assertTrue(signing.signature_check(metadata(), plistlib.dumps(claims), claims, TEAM)['same_team'])
        for meta in (metadata('2'), metadata('0'), metadata(team='OTHER'), metadata().replace('Apple Development:', 'Developer ID Application:')):
            with self.subTest(meta=meta), self.assertRaises(common.Error):
                signing.signature_check(meta, plistlib.dumps(claims), claims, TEAM)
        changed = dict(claims, **{signing.CROSS_KEYS[0]: 1})
        with self.assertRaisesRegex(common.Error, 'entitlements_unexpected'):
            signing.signature_check(metadata(), plistlib.dumps(changed), claims, TEAM)


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo_patch = patch.object(signing, 'REPO', self.root)
        self.repo_patch.start()
        self.addCleanup(self.repo_patch.stop)
        original = TOOLS.parents[1]
        for name in signing.PROVENANCE:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original / name, p)
        self.build = self.root / '.build/task4/build-arm64'
        self.install = self.build / 'install'
        entries = [(signing.LOADER, 2), (signing.NTDLL, 6), (signing.SERVER, 2),
                   ('bin/wine', 2), (signing.BOOTSTRAP_HELPER, 2), (signing.SENTINEL, 2)]
        self.artifacts = []
        for name, filetype in entries:
            p = self.install / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(macho(filetype))
            p.chmod(0o755)
            self.artifacts.append({'path': name, 'kind': 'macho', 'sha256': common.sha256(p)})
        data = self.install / 'share/wine/fixture.txt'
        data.parent.mkdir(parents=True)
        data.write_bytes(b'owned data remains unchanged')
        (self.install / 'bin/wineboot').symlink_to('wine')
        self.built = {'schema_version': 1, 'record_kind': 'wine_build', 'scope': 'wine_component',
                      'variant': 'arm64', 'install_root': str(self.install), 'artifacts': self.artifacts}
        (self.build / 'build.json').write_bytes(common.encoded(self.built))
        self.output = self.root / '.build/task4/signed'
        self.private = private_fixture()
        self.profile = self.root / 'synthetic.provisionprofile'
        self.profile.write_bytes(self.private['profile_bytes'])
        self.local = self.root / '.build/task4/private/signing.json'
        self.local.parent.mkdir(parents=True)
        self.local.write_bytes(common.encoded({'schema_version': 1, 'record_kind': 'wine_local_signing',
            'scope': 'wine_component', 'profile_path': str(self.profile), 'bundle_identifier': signing.BUNDLE_ID}))
        self.events = []

    def native(self, args, label, events, timeout=30):
        self.events.append((args, label))
        self.assertEqual(args[0], '/usr/bin/codesign')
        events.append({'operation': label, 'exit_code': 0, 'stdout_bytes': 0, 'stderr_bytes': 0, 'failure': None})
        path = Path(args[-1])
        if '--display' in args and '--verbose=4' in args:
            return b'', metadata().encode()
        if '--display' in args and '--entitlements' in args:
            restricted = path == self.output / signing.BUNDLE or path == self.output / signing.MAIN
            return plistlib.dumps(self.private['claims'] if restricted else {}), b''
        return b'', b''

    def prepare(self):
        with patch.object(signing, '_build', return_value=self.built), \
             patch.object(signing, '_authorization', return_value=self.private), \
             patch.object(signing, '_native', side_effect=self.native):
            return signing.prepare(self.build, self.local, self.output)

    def validate(self):
        with patch.object(signing, '_build', return_value=self.built), \
             patch.object(signing, '_authorization', return_value=self.private), \
             patch.object(signing, '_native', side_effect=self.native):
            return signing.validate_prepared(self.output)

    def test_requirements_separate_actual_loader_server_and_wrapper(self):
        result = signing.requirement_map(self.build, self.built)
        rows = {x['source_path']: x for x in result['native_images']}
        self.assertTrue(rows[signing.LOADER]['cross_architecture_profile_required'])
        self.assertEqual(rows[signing.LOADER]['required_user_page_size'], 4096)
        self.assertEqual(rows[signing.SERVER]['required_user_page_size'], 16384)
        self.assertFalse(rows['bin/wine']['execution_in_stage2'])
        self.assertFalse(any(row['allow_jit'] for row in rows.values()))
        self.assertEqual(sum(row['cross_architecture_profile_required'] for row in rows.values()), 1)
        self.assertEqual(set(result['entrypoints']), {'loader', 'server', 'ntdll', 'bootstrap_helper', 'sentinel'})
        self.assertEqual(result['authorization'], 'not_assessed')

    def test_missing_output_wrong_slice_duplicate_or_changed_bytes_fail(self):
        for case in ('missing', 'duplicate', 'changed', 'wrong_slice'):
            built = copy.deepcopy(self.built)
            if case == 'missing': built['artifacts'] = built['artifacts'][1:]
            if case == 'duplicate': built['artifacts'].append(built['artifacts'][0])
            path = self.install / signing.LOADER
            if case == 'changed': built['artifacts'][0]['sha256'] = '0' * 64
            if case == 'wrong_slice':
                path.write_bytes(macho(cpu=0x01000007))
                built['artifacts'][0]['sha256'] = common.sha256(path)
            with self.subTest(case=case), self.assertRaises(common.Error):
                signing.requirement_map(self.build, built)
            path.write_bytes(macho())

    def test_bundle_preserves_source_and_resolves_both_internal_links(self):
        before = signing.inventory(self.install)
        self.output.mkdir()
        signing._copy_payload(self.install, self.output)
        self.assertEqual(signing.inventory(self.install), before)
        self.assertEqual((self.output / signing.PAYLOAD / signing.LOADER).resolve(), self.output / signing.MAIN)
        self.assertEqual((self.output / signing.NTDLL_ALIAS).resolve(), self.output / signing.PAYLOAD / signing.NTDLL)
        self.assertEqual((self.output / signing.PAYLOAD / 'bin/wineboot').resolve(), self.output / signing.PAYLOAD / 'bin/wine')
        self.assertEqual((self.output / signing.PAYLOAD / 'share/wine/fixture.txt').read_bytes(), b'owned data remains unchanged')

    def test_escaping_link_special_mode_and_inode_alias_fail(self):
        p = self.install / 'extra'
        p.symlink_to(self.profile)
        with self.assertRaisesRegex(common.Error, 'unsafe_payload_link'):
            signing.inventory(self.install)
        p.unlink()
        p.write_bytes(b'owned')
        p.chmod(0o4755)
        with self.assertRaisesRegex(common.Error, 'unsafe_payload_mode'):
            signing.inventory(self.install)
        p.chmod(0o644)
        os.link(p, self.install / 'hardlink')
        with self.assertRaisesRegex(common.Error, 'payload_inode_alias'):
            signing.inventory(self.install)

    def test_private_input_refuses_broad_claims_and_other_app_id(self):
        value = common.load_json(self.local)
        for key, new in [('entitlements', {'disable-library-validation': True}),
                         ('bundle_identifier', signing.PROFILE.DEFAULT_BUNDLE_ID)]:
            changed = dict(value, **{key: new})
            self.local.write_bytes(common.encoded(changed))
            with self.subTest(key=key), self.assertRaises(common.Error):
                signing._local_input(self.local)

    def test_mismatched_authorization_never_creates_signing_output(self):
        with patch.object(signing, '_build', return_value=self.built), \
             patch.object(signing, '_authorization', side_effect=common.Error('profile_application_mismatch')), \
             patch.object(signing, '_native', side_effect=AssertionError('must not sign')):
            with self.assertRaisesRegex(common.Error, 'profile_application_mismatch'):
                signing.prepare(self.build, self.local, self.output)
        self.assertFalse(self.output.exists())

    def test_occupied_output_and_symlink_parent_preserved(self):
        self.output.mkdir()
        (self.output / 'owned.txt').write_bytes(b'keep')
        with self.assertRaisesRegex(common.Error, 'destination_exists'):
            signing.prepare(self.build, self.local, self.output)
        self.assertEqual((self.output / 'owned.txt').read_bytes(), b'keep')
        alias = self.output.parent / 'alias'
        alias.symlink_to(self.output, target_is_directory=True)
        with self.assertRaisesRegex(common.Error, 'symlink_task_path'):
            signing.owned(alias / 'new')

    def test_synthetic_preparation_signs_inside_out_without_unsafe_options(self):
        result = self.prepare()
        self.assertEqual(result['status'], 'prepared')
        self.assertFalse(result['wine_execution'])
        signs = [(args, label) for args, label in self.events if '--sign' in args]
        self.assertEqual(signs[-1][1], 'loader.sign')
        self.assertIn('--pagesize', signs[-1][0])
        self.assertEqual(signs[-1][0][signs[-1][0].index('--pagesize') + 1], '4096')
        self.assertTrue(all('--pagesize' not in args for args, _ in signs[:-1]))
        self.assertTrue(all('--options' in args and 'runtime' in args for args, _ in signs))
        self.assertEqual(sum('--entitlements' in args for args, _ in signs), 1)
        self.assertNotIn('--deep', str(signs))
        self.assertNotIn(TEAM, str(result))
        self.assertNotIn(FINGERPRINT, str(result))
        self.assertNotIn(DEVICE, str(result))

    def test_payload_profile_entrypoint_or_claim_receipt_mutation_fails(self):
        self.prepare()
        report = common.load_json(self.output / 'signed.json')
        for kind in ('payload', 'profile', 'entrypoint', 'signature'):
            changed = copy.deepcopy(report)
            target = self.output / signing.PAYLOAD / 'share/wine/fixture.txt'
            original = target.read_bytes()
            if kind == 'payload': target.write_bytes(b'changed')
            if kind == 'profile': changed['profile_sha256'] = '0' * 64
            if kind == 'entrypoint': changed['entrypoints']['loader'] = changed['entrypoints']['server']
            if kind == 'signature': changed['native_images'][0]['signature']['claim_keys'] = [signing.CROSS_KEYS[0]]
            (self.output / 'signed.json').write_bytes(common.encoded(changed))
            with self.subTest(kind=kind), self.assertRaises(common.Error):
                self.validate()
            target.write_bytes(original)
        (self.output / 'signed.json').write_bytes(common.encoded(report))

    def test_rehashed_data_and_native_substitutions_still_fail_origin_binding(self):
        self.prepare()
        report = common.load_json(self.output / 'signed.json')
        manifest = common.load_json(self.output / 'signed-files.json')
        for name in (signing.PAYLOAD + '/share/wine/fixture.txt', signing.PAYLOAD + '/' + signing.SERVER):
            path = self.output / name
            original = path.read_bytes()
            path.write_bytes(original + b'changed')
            changed = copy.deepcopy(report)
            for row in changed['native_images']:
                if row['path'] == name: row['sha256'] = common.sha256(path)
            new_manifest = dict(manifest, files=signing.inventory(self.output / signing.BUNDLE))
            (self.output / 'signed-files.json').write_bytes(common.encoded(new_manifest))
            changed['files_manifest_sha256'] = common.sha256(self.output / 'signed-files.json')
            (self.output / 'signed.json').write_bytes(common.encoded(changed))
            with self.subTest(name=name), self.assertRaisesRegex(common.Error, 'origin'):
                self.validate()
            path.write_bytes(original)

    def test_missing_unknown_or_duplicate_native_receipt_fails(self):
        self.prepare()
        report = common.load_json(self.output / 'signed.json')
        for rows in [report['native_images'][:-1], report['native_images'] + report['native_images'][:1],
                     [dict(x, role='unknown') for x in report['native_images']]]:
            changed = dict(report, native_images=rows)
            (self.output / 'signed.json').write_bytes(common.encoded(changed))
            with self.subTest(count=len(rows)), self.assertRaises(common.Error):
                self.validate()


if __name__ == '__main__':
    unittest.main()
