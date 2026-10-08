"""Original portable controls for the ordinary-native service signing boundary."""
from pathlib import Path
import hashlib
import json
from datetime import datetime,timezone
from unittest.mock import patch
import plistlib
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.fex import sign_services as signing
from tools.fex.common import Error


class SigningBoundary(unittest.TestCase):
    def metadata(self,flags='10000',team='fixture-team'):
        return 'CodeDirectory flags=0x'+flags+'(runtime)\nAuthority=Apple Development: Owned Fixture\nTeamIdentifier='+team+'\n'

    def test_ordinary_claims(self):
        claims={signing.APP_ID:'fixture.owned',signing.TEAM_ID:'fixture-team'}
        result=signing.signature_facts(self.metadata(),plistlib.dumps(claims),claims,'fixture-team')
        self.assertTrue(result['hardened_runtime']);self.assertFalse(result['restricted_operations'])

    def test_library_has_no_entitlements(self):
        self.assertEqual(signing.signature_facts(self.metadata(),b'',{},'fixture-team')['claim_keys'],[])

    def test_rejects_signature_category_team_and_claim_errors(self):
        controls=[(self.metadata('10002'),b'',{},'fixture-team'),(self.metadata('0'),b'',{},'fixture-team'),
                  (self.metadata(),b'',{},'different-team'),(self.metadata(),plistlib.dumps({'com.apple.security.cs.disable-library-validation':True}),{},'fixture-team')]
        for args in controls:
            with self.subTest(args=args),self.assertRaises(Error):signing.signature_facts(*args)

    def test_restricted_claim_cannot_be_relabelled_as_ordinary(self):
        claims={'com.apple.security.cs.allow-jit':True}
        with self.assertRaises(Error):signing.signature_facts(self.metadata(),plistlib.dumps(claims),claims,'fixture-team')

    def test_origin_preserves_body_and_machine(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);before=root/'before';after=root/'after'
            data=struct.pack('<8I',0xfeedfacf,0x100000c,0,2,0,0,0,0)+b'owned fixture executable bytes'
            before.write_bytes(data);after.write_bytes(data);signing.verify_origin(before,after)
            after.write_bytes(data[:-1]+b'X')
            with self.assertRaises(Error):signing.verify_origin(before,after)
            after.write_bytes(struct.pack('<8I',0xfeedfacf,0x1000007,0,2,0,0,0,0)+data[32:])
            with self.assertRaises(Error):signing.verify_origin(before,after)

    def test_missing_command_receipts_fail(self):
        with self.assertRaises(Error):signing.verify_command_receipts(Path('/unused'),[],[('required',['/usr/bin/arch'])])

    def test_wrong_command_and_extra_fields_fail_before_logs(self):
        row={'id':'required','argv':['/bin/sh'],'returncode':0,'elapsed_ms':1,'status':'completed','environment':signing.ENV,'logs':{}}
        with self.assertRaises(Error):signing.verify_command_receipts(Path('/unused'),[row],[('required',['/usr/bin/arch'])])
        row['argv']=['/usr/bin/arch'];row['ignored']=True
        with self.assertRaises(Error):signing.verify_command_receipts(Path('/unused'),[row],[('required',['/usr/bin/arch'])])

    def test_recipe_has_exact_nonrestricted_operations(self):
        rows=signing.signing_recipe(Path('/owned-output'),'fixture-identity',Path('/owned-profile'))
        self.assertEqual(len(rows),17)
        self.assertEqual(len({name for name,_ in rows}),17)
        self.assertTrue(all(argv[:2]==['/usr/bin/arch','-arm64'] for _,argv in rows))
        self.assertFalse(any('disable-library-validation' in arg or 'allow-jit' in arg for _,argv in rows for arg in argv))


    def test_bounded_signing_failure_retains_attempt_and_raw_logs(self):
        for code in ('command_timeout','command_output_limit','command_start_failed'):
            with self.subTest(code=code),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);rows=[]
                def fail(argv,**kwargs):
                    if code!='command_start_failed':
                        (kwargs['output_dir']/'stdout.bin').write_bytes(b'partial output')
                        (kwargs['output_dir']/'stderr.bin').write_bytes(b'partial error')
                    raise Error(code)
                with patch.object(signing,'bounded_command',side_effect=fail):
                    with self.assertRaises(Error) as result:
                        signing.native(['/usr/bin/codesign','--verify','/owned'],root,'attempt',rows)
                self.assertEqual(result.exception.code,code)
                self.assertEqual(len(rows),1);row=rows[0]
                self.assertIsNone(row['returncode']);self.assertEqual(row['status'],'failed')
                self.assertEqual(row['error'],code)
                self.assertEqual(row['argv'],['/usr/bin/arch','-arm64','/usr/bin/codesign','--verify','/owned'])
                self.assertEqual(row['environment'],signing.ENV)
                self.assertGreaterEqual(row['elapsed_ms'],0)
                self.assertEqual(set(row['logs']),set() if code=='command_start_failed' else {'stdout','stderr'})
                for stream,ref in row['logs'].items():
                    path=root/ref['path']
                    self.assertEqual(ref['sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
                    self.assertEqual(ref['size_bytes'],path.stat().st_size)

    def test_live_preflight_failure_writes_structured_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);auth=root/'auth';auth.mkdir();output=root/'preflight';output.mkdir()
            (auth/'authorization.json').write_bytes(b'owned authorization fixture')
            row={'id':'profile.decode','returncode':None,'status':'failed','error':'command_timeout'}
            def fail(profile,owned,commands):
                commands.append(row);raise Error('command_timeout')
            with patch.object(signing,'operation_output',side_effect=[auth,output]), \
                 patch.object(signing,'validate_authorization_record',return_value={}), \
                 patch.object(signing,'authorize',side_effect=fail):
                with self.assertRaises(Error):signing.validate_authorization(auth)
            value=json.loads((output/'failure.json').read_text())
            self.assertEqual(value['error'],'command_timeout');self.assertEqual(value['commands'],[row])
            self.assertEqual(value['authorization_sha256'],hashlib.sha256((auth/'authorization.json').read_bytes()).hexdigest())
            self.assertFalse(value['restricted_operations']);self.assertFalse((output/'preflight.json').exists())

    def test_failed_preflight_is_never_promoted_to_positive_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'failure.json').write_bytes(b'{}')
            with patch.object(signing,'operation_output',return_value=root), \
                 patch.object(signing,'validate_authorization_record',side_effect=AssertionError('positive replay')):
                with self.assertRaises(Error) as result:signing.validate_preflight_record(root,root)
            self.assertEqual(result.exception.code,'service_preflight_failed_record')

    @staticmethod
    def der_fixture(tag,content):
        size=len(content)
        length=bytes([size]) if size<128 else bytes([128+(size.bit_length()+7)//8])+size.to_bytes((size.bit_length()+7)//8,'big')
        return bytes([tag])+length+content

    def cms_fixture(self,content):
        # Structural fixture only. This does not claim a valid CMS signature.
        d=self.der_fixture
        encap=d(0x30,d(6,bytes.fromhex('2a864886f70d010701'))+d(0xa0,d(4,content)))
        signed=d(0x30,d(2,b'\x01')+d(0x31,b'')+encap+d(0x31,b''))
        return d(0x30,d(6,bytes.fromhex('2a864886f70d010702'))+d(0xa0,signed))

    def profile_logs(self,root,expiration=None,device='fixture-device'):
        certificate=b'original synthetic certificate bytes'
        fingerprint=hashlib.sha1(certificate).hexdigest().upper()
        profile={'ExpirationDate':expiration or datetime(2030,1,1),'Platform':['OSX'],
                 'Entitlements':{signing.APP_ID:'fixture-prefix.'+signing.BUNDLE_ID,signing.TEAM_ID:'fixture-team',
                                 'com.apple.developer.cross-architecture-support':True},
                 'TeamIdentifier':['fixture-team'],'ApplicationIdentifierPrefix':['fixture-prefix'],
                 'ProvisionedDevices':['fixture-device'],'DeveloperCertificates':[certificate]}
        (root/'captured-profile.provisionprofile').write_bytes(self.cms_fixture(plistlib.dumps(profile)))
        streams={'profile.decode':plistlib.dumps(profile),
                 'profile.identities':('  1) '+fingerprint+' "Apple Development: Synthetic Fixture"\n').encode(),
                 'profile.device':json.dumps({'SPHardwareDataType':[{'provisioning_udid':device}]}).encode()}
        for name,content in streams.items():
            directory=root/'logs'/name;directory.mkdir(parents=True)
            (directory/'stdout.bin').write_bytes(content)

    def test_profile_replay_makes_no_native_call_and_narrows_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.profile_logs(root)
            with patch.object(signing,'native',side_effect=AssertionError('native replay')):
                value=signing.profile_from_receipts(root)
            self.assertEqual(set(value['claims']),{signing.APP_ID,signing.TEAM_ID})
            self.assertTrue(value['checks']['available_development_certificate_match'])

    def test_profile_replay_refuses_expired_or_wrong_device(self):
        controls=[{'expiration':datetime(2000,1,1)},{'device':'unregistered-device'}]
        for control in controls:
            with self.subTest(control=control),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);self.profile_logs(root,**control)
                with self.assertRaises(Error):signing.profile_from_receipts(root)

    def test_preflight_recipe_contains_only_live_read_checks(self):
        rows=signing.preflight_recipe(Path('/unused-output'),Path('/owned-authorization'))
        self.assertEqual(len(rows),13)
        self.assertTrue(all(argv[:2]==['/usr/bin/arch','-arm64'] for _,argv in rows))
        self.assertFalse(any('--force' in argv or '--sign' in argv for _,argv in rows))
        self.assertEqual(rows[0][1][-1],'/unused-output/captured-profile.provisionprofile')


    def test_decoded_profile_changes_cannot_hide_behind_same_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.profile_logs(root)
            path=root/'logs/profile.decode/stdout.bin';decoded=plistlib.loads(path.read_bytes())
            decoded['ExpirationDate']=datetime(2031,1,1)
            path.write_bytes(plistlib.dumps(decoded))
            with self.assertRaises(Error) as result:signing.profile_from_receipts(root)
            self.assertEqual(result.exception.code,'service_profile_decoded_content_changed')

    def test_malformed_cms_envelopes_fail_closed(self):
        raw=self.cms_fixture(b'owned plist bytes')
        controls=[raw+b'extra',raw[:-1],b'\x30\x80'+raw[2:],b'\x30\x81\x01x',raw.replace(bytes.fromhex('2a864886f70d010701'),bytes.fromhex('2a864886f70d010703'))]
        for value in controls:
            with self.subTest(value=value),self.assertRaises(Error):signing.cms_plist_content(value)

    def test_authorize_refuses_read_hash_race_before_native_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);profile=root/'input.profile';profile.write_bytes(b'owned raw bytes')
            with patch.object(signing,'sha256',return_value='0'*64),patch.object(signing,'native',side_effect=AssertionError('unexpected native call')):
                with self.assertRaises(Error):signing.authorize(profile,root,[])


if __name__=='__main__':unittest.main()
