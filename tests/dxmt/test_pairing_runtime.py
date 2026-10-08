"""Pure development admission/byte controls; synthetic CMS has no signature trust.

All Apple operations are replaced with explicit receipt-writing doubles. These
metadata-only files contain no runnable program or genuine certificate/profile.
"""
import copy
from datetime import datetime, timedelta
import errno
import hashlib
import importlib.util
import os
from pathlib import Path
import plistlib
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'tools/dxmt'))
spec=importlib.util.spec_from_file_location('_pear_dxmt_pair_runtime_tests',REPO/'tools/dxmt/pairing_runtime.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
from common import Error,digest,encoded

CERT=b'owned synthetic certificate, never an Apple identity'
TEAM='SYNTHETICTEAM';DEVICE='OWNED-METADATA-DEVICE'
FINGERPRINT=hashlib.sha1(CERT).hexdigest().upper()
IDENTITIES='  1) '+FINGERPRINT+' "Apple Development: Synthetic Metadata ('+TEAM+')"\n'


def profile():
    reader=runtime.legacy(REPO)
    return {'ExpirationDate':datetime(2040,1,1),'Platform':['OSX'],'TeamIdentifier':[TEAM],
        'ApplicationIdentifierPrefix':['SYNTHETICPREFIX'],
        'Entitlements':{reader.APP_ID:'SYNTHETICPREFIX.'+runtime.BUNDLE_ID,
                        reader.TEAM_ID:TEAM,reader.CROSS_KEYS[0]:True},
        'ProvisionedDevices':[DEVICE],'DeveloperCertificates':[CERT]}


def der(tag,raw):
    size=len(raw)
    length=bytes([size])if size<128 else bytes([128+((size.bit_length()+7)//8)])+size.to_bytes((size.bit_length()+7)//8,'big')
    return bytes([tag])+length+raw


def cms(value):
    # Structural ContentInfo/SignedData only: empty signer set gives no trust.
    data_oid=bytes.fromhex('2a864886f70d010701');signed_oid=bytes.fromhex('2a864886f70d010702')
    body=der(2,b'\1')+der(49,b'')+der(48,der(6,data_oid)+der(160,der(4,plistlib.dumps(value))))+der(49,b'')
    return der(48,der(6,signed_oid)+der(160,der(48,body)))


def metadata(identifier,claims=(),team=TEAM,page=4096):
    return ('Identifier='+identifier+'\nCodeDirectory v=20500 size=256 flags=0x10000(runtime) hashes=1+1\n'
        'Authority=Apple Development: Synthetic Metadata\nTeamIdentifier='+team+'\nPage size='+str(page)+'\n').encode()


def macho(filetype=6,cpu=runtime.MACH_ARM64):
    # Header and textual metadata only, mode 0644; never an executable fixture.
    return struct.pack('<8I',0xfeedfacf,cpu,0,filetype,0,0,0,0)+b'non executable metadata'


def pe(machine=0xaa64):
    raw=bytearray(128);raw[:2]=b'MZ';struct.pack_into('<I',raw,60,64);raw[64:68]=b'PE\0\0'
    struct.pack_into('<H',raw,68,machine);return bytes(raw)


class RuntimeControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='pear-pair-runtime-pure-')
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
        self.reader=runtime.legacy(REPO);self.value=profile();self.raw=cms(self.value)
        self.private=self.reader.profile_authorization(self.value,IDENTITIES,DEVICE,runtime.BUNDLE_ID)

    def put(self,path,raw,root=None,mode=0o644):
        path=(root or self.root)/path;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(mode);return path

    def logs(self,value=None,identity=IDENTITIES,device=DEVICE):
        return {'profile.decode':{'stdout':plistlib.dumps(value or self.value),'stderr':b''},
            'profile.identities':{'stdout':identity.encode(),'stderr':b''},
            'profile.device':{'stdout':encoded({'SPHardwareDataType':[{'provisioning_udid':device}]}),'stderr':b''}}

    def native_double(self,value=None,identity=IDENTITIES,device=DEVICE,certificate=CERT):
        def native(argv,root,ident,commands):
            info=self.logs(value,identity,device)
            if ident in info:stdout,stderr=info[ident]['stdout'],info[ident]['stderr']
            elif ident.endswith('.metadata'):
                target=Path(argv[-1]);restricted=target.name==runtime.BUNDLE or hasattr(self,'runtime_root')and target==self.runtime_root/runtime.MAIN
                match=next((i for i,row in enumerate(self.images)if row['path']==target.relative_to(self.runtime_root).as_posix()),None)if hasattr(self,'images')and target.is_relative_to(self.runtime_root)else None
                identifier=runtime.BUNDLE_ID if restricted else runtime.BUNDLE_ID+'.native.'+str(match)
                stdout,stderr=b'',metadata(identifier)
            elif ident.endswith('.claims'):
                target=Path(argv[-1]);restricted=target.name==runtime.BUNDLE or hasattr(self,'runtime_root')and target==self.runtime_root/runtime.MAIN
                stdout,stderr=plistlib.dumps(self.reader.loader_claims(self.private,'page-wx')if restricted else{}),b''
            elif ident.endswith('.certificates'):
                # Explicit metadata double writes no genuine signing certificate.
                prefix=Path(argv[2].split('=',1)[1])
                self.put(prefix.relative_to(root).as_posix()+'0',certificate,root)
                self.put(prefix.relative_to(root).as_posix()+'1',b'synthetic intermediate metadata',root)
                stdout,stderr=b'',b''
            else:stdout,stderr=b'',b''
            refs={}
            for channel,data in [('stdout',stdout),('stderr',stderr)]:
                path='logs/'+ident+'/'+channel;self.put(path,data,root)
                refs[channel]={'path':path,'sha256':digest(data),'size_bytes':len(data)}
            commands.append({'id':ident,'argv':['/usr/bin/arch','-arm64',*argv],'environment':runtime.ENV,
                'cwd':str(root),'exit_code':0,'elapsed_ms':0,'status':'completed','error':None,
                'bound_outcome':None,'evidence_error':None,'logs':refs})
            return stdout,stderr
        return native

    def sources(self):
        install=self.root/'baseline/install';build=self.root/'build';install.mkdir(parents=True);build.mkdir()
        values={runtime.LOADER:macho(2),runtime.NTDLL:macho(),runtime.SERVER:macho(2),
            runtime.API_LAUNCH:macho(2),runtime.SENTINEL:macho(2),runtime.DRIVER:macho(),runtime.DRIVER_PE:pe(),
            'bin/wine':macho(2),'share/notice':b'redistributable notice metadata'}
        for path,raw in values.items():self.put(path,raw,install)
        (install/'bin/msidb').symlink_to('wine')
        rows=self.reader.inventory(install)
        files=[]
        for row in rows:
            if row['kind']=='file':
                path=row['path'];kind='macho'if values[path][:4]==b'\xcf\xfa\xed\xfe'else'pe'if values[path][:2]==b'MZ'else'data'
                files.append({**{key:row[key]for key in ['path','sha256','mode','size_bytes']},'kind':kind})
        manifest={'files':files,'symlinks':[{'path':'bin/msidb','target':'wine'}]}
        for path,raw in [(runtime.pairing_check.REBUILT_DRIVER,macho()),(runtime.pairing_check.REBUILT_PE,pe()),
                         ('dxmt/install/aarch64-unix/winemetal.so',macho()),(runtime.pairing_check.FIXTURE_PE,pe())]:
            self.put(path,raw,build)
        ledger=runtime.source_ledger(build,install.parent,{},install,manifest,self.reader)
        return install,build,ledger,manifest

    def test_complete_cms_content_matches_but_has_no_signature_trust(self):
        self.assertEqual(runtime.cms_plist(self.raw),self.value)
        result=runtime.profile_from_logs(self.raw,self.logs(),self.reader)
        self.assertEqual(result['identity'],FINGERPRINT)
        self.assertNotIn('signature_trusted',result)
        changed=copy.deepcopy(self.value);changed['ExpirationDate']=datetime(2041,1,1)
        with self.assertRaisesRegex(Error,'pair_cms_decode_content'):
            runtime.profile_from_logs(self.raw,self.logs(changed),self.reader)
        changed=copy.deepcopy(self.value);changed['DeveloperCertificates']=[b'another certificate']
        with self.assertRaisesRegex(Error,'pair_cms_decode_content'):
            runtime.profile_from_logs(self.raw,self.logs(changed),self.reader)

    def test_cms_envelope_oid_lengths_and_trailing_bytes_refuse(self):
        for raw in [self.raw+b'\0',b'\x30\x80'+self.raw[2:],self.raw.replace(bytes.fromhex('2a864886f70d010702'),bytes.fromhex('2a864886f70d010701'),1),
                    der(48,der(6,b'wrong'))]:
            with self.assertRaises(Error):runtime.cms_plist(raw)

    def test_profile_claims_require_current_device_identity_expiration_and_single_grant(self):
        for name in ['device','identity','expired','wildcard','grant']:
            value=copy.deepcopy(self.value);identity,device=IDENTITIES,DEVICE
            if name=='device':device='other'
            if name=='identity':identity='0 valid identities found'
            if name=='expired':value['ExpirationDate']=datetime(2000,1,1)
            if name=='wildcard':value['Entitlements'][self.reader.APP_ID]='SYNTHETICPREFIX.*'
            if name=='grant':value['Entitlements'][self.reader.CROSS_KEYS[1]]=True
            with self.subTest(name=name):
                with self.assertRaises(Error):runtime.profile_from_logs(cms(value),self.logs(value,identity,device),self.reader)

    def test_capture_decodes_owned_bytes_not_mutable_original_profile(self):
        original=self.put('original.provisionprofile',self.raw)
        out=self.root/'owned';out.mkdir();commands=[]
        with mock.patch.object(runtime,'native',side_effect=self.native_double())as native:
            value,_,captured=runtime.capture_authorization(original,out,self.reader,commands)
        self.assertEqual(captured,self.raw)
        self.assertEqual(native.call_args_list[0].args[0][-1],str(out/'captured-profile.provisionprofile'))
        self.assertEqual((out/'captured-profile.provisionprofile').stat().st_mode&0o777,0o600)
        self.assertIs(value['permission_admitted'],False)
        runtime.verify_authorization(out,value,self.reader)
        (out/'captured-profile.provisionprofile').write_bytes(cms({**self.value,'ExpirationDate':datetime(2042,1,1)}))
        with self.assertRaises(Error):runtime.verify_authorization(out,value,self.reader)

    def test_original_profile_change_during_capture_refuses(self):
        original=self.put('original.provisionprofile',self.raw);out=self.root/'owned';out.mkdir();commands=[]
        double=self.native_double()
        def change(argv,root,ident,rows):
            result=double(argv,root,ident,rows)
            if ident=='profile.decode':original.write_bytes(b'changed after immutable capture')
            return result
        with mock.patch.object(runtime,'native',side_effect=change):
            with self.assertRaisesRegex(Error,'pair_profile_changed'):
                runtime.capture_authorization(original,out,self.reader,commands)
        self.assertEqual(len(commands),3)
        self.assertFalse((out/'authorization.json').exists())

    def test_native_command_replay_rejects_boolean_exit_wrong_recipe_and_changed_stream(self):
        commands=[]
        for ident,argv in runtime.profile_recipe(self.root):self.native_double()(argv,self.root,ident,commands)
        runtime.verify_commands(self.root,commands,runtime.profile_recipe(self.root))
        for key,value in [('exit_code',False),('argv',['/bin/true']),('environment',{}),
                          ('bound_outcome',{'timed_out':True}),('evidence_error','missing')]:
            rows=copy.deepcopy(commands);rows[0][key]=value
            with self.subTest(key=key):
                with self.assertRaises(Error):runtime.verify_commands(self.root,rows,runtime.profile_recipe(self.root))
        (self.root/'logs/profile.decode/stdout').write_bytes(b'changed')
        with self.assertRaises(Error):runtime.verify_commands(self.root,commands,runtime.profile_recipe(self.root))

    def test_ordinary_images_refuse_extra_claims_wrong_team_identifier_and_page(self):
        logs={key:{'stdout':b'','stderr':b''}for key in ['native.1.verify','native.1.metadata','native.1.claims']}
        logs['native.1.metadata']['stderr']=metadata('expected')
        self.assertTrue(runtime.signature_from_logs(logs,'native.1',{},self.private,self.reader,'expected')['hardened_runtime'])
        for changed in ['claims','team','identifier','page']:
            rows=copy.deepcopy(logs)
            if changed=='claims':rows['native.1.claims']['stdout']=plistlib.dumps({'com.apple.security.cs.disable-library-validation':True})
            if changed=='team':rows['native.1.metadata']['stderr']=metadata('expected',team='OTHER')
            if changed=='identifier':rows['native.1.metadata']['stderr']=metadata('wrong')
            if changed=='page':rows['native.1.metadata']['stderr']=metadata('expected',page=16384)
            with self.subTest(changed=changed):
                with self.assertRaises(Error):runtime.signature_from_logs(rows,'native.1',{},self.private,self.reader,'expected')

    def test_full_source_ledger_materializes_only_exact_driver_metal_and_fixture_delta(self):
        install,build,ledger,_=self.sources();out=self.root/'bundle';out.mkdir()
        runtime.materialize(out,ledger,install,build,self.raw)
        native,pe_images,_=runtime.inventory_images(out,ledger,install,build,self.reader)
        self.assertEqual(len(native),8)
        self.assertEqual(len(pe_images),2)
        self.assertEqual(sum(row['origin']['path']==runtime.NTDLL for row in native),1)
        roles={row['origin']['role']for row in native+pe_images}
        self.assertEqual(roles,{'baseline-native','fixturehelper','rebuilt-driver','rebuilt-dxmt','fixture-pe'})
        self.assertTrue((out/runtime.PAYLOAD/'bin/msidb').is_symlink())
        self.assertEqual((out/runtime.PAYLOAD/'share/notice').read_bytes(),b'redistributable notice metadata')
        self.assertNotIn('d3d11.dll',[Path(row['path']).name for row in pe_images])
        self.assertEqual(set(runtime.entrypoints()),{'loader','server','bootstrap_helper','sentinel','fixture_pe','winemac_native','winemac_pe','winemetal_native'})

    def test_source_and_output_data_mode_alias_and_native_mutation_refuse(self):
        install,build,ledger,_=self.sources();out=self.root/'bundle';out.mkdir()
        runtime.materialize(out,ledger,install,build,self.raw)
        for change in ['native','pe','data','mode','alias','extra']:
            if change=='native':path=out/runtime.MAIN
            elif change=='pe':path=out/runtime.PAYLOAD/runtime.FIXTURE
            else:path=out/runtime.PAYLOAD/'share/notice'
            old=path.read_bytes();mode=path.stat().st_mode&0o777
            if change=='mode':path.chmod(0o755)
            elif change=='alias':
                path=out/runtime.NTDLL_ALIAS;old_target=os.readlink(path);path.unlink();path.symlink_to('../../Resources/runtime/lib/wine/aarch64-unix/winemac.so')
            elif change=='extra':path=self.put(runtime.BUNDLE+'/unexpected',b'extra data',out)
            else:path.write_bytes(old+b'changed')
            with self.subTest(change=change):
                with self.assertRaises(Error):runtime.inventory_images(out,ledger,install,build,self.reader)
            if change=='alias':path.unlink();path.symlink_to(old_target)
            elif change=='extra':path.unlink()
            else:path.write_bytes(old);path.chmod(mode)

    def test_missing_baseline_member_or_changed_manifest_mode_refuses(self):
        install,build,ledger,manifest=self.sources()
        for changed in ['missing','mode','alias']:
            value=copy.deepcopy(manifest)
            if changed=='missing':value['files'].pop()
            if changed=='mode':value['files'][0]['mode']=False
            if changed=='alias':value['symlinks'][0]['target']='other'
            with self.subTest(changed=changed):
                with self.assertRaises(Error):runtime.source_ledger(build,install.parent,{},install,value,self.reader)

    def test_native_command_failure_retains_attempt_and_original_error_if_log_read_also_fails(self):
        commands=[];error=Error('actual_apple_tool_refusal')
        def fail(argv,**kwargs):
            out=kwargs['log_directory'];(out/'stdout').write_bytes(b'partial');(out/'stderr').write_bytes(b'error')
            raise error
        original=runtime.read_relative
        def read(root,path,*args,**kwargs):
            if path=='stdout':raise Error('secondary_log_read')
            return original(root,path,*args,**kwargs)
        with mock.patch.object(runtime.platform,'system',return_value='Darwin'),\
             mock.patch.object(runtime.platform,'machine',return_value='arm64'),\
             mock.patch.object(runtime,'run_bounded',side_effect=fail),\
             mock.patch.object(runtime,'read_relative',side_effect=read):
            with self.assertRaisesRegex(Error,'actual_apple_tool_refusal'):
                runtime.native(['/usr/bin/codesign','--verify','--strict','owned'],self.root,'native.0.verify',commands)
        self.assertEqual(len(commands),1)
        self.assertIsNone(commands[0]['exit_code'])
        self.assertEqual(commands[0]['error'],'actual_apple_tool_refusal')
        self.assertEqual(commands[0]['evidence_error'],'secondary_log_read')
        self.assertIn('stderr',commands[0]['logs'])

    def test_native_os_start_error_retains_domain_errno_without_exit_or_secondary_override(self):
        commands=[];error=OSError(errno.ENOEXEC,'synthetic failed native start')
        def fail(argv,**kwargs):
            (kwargs['log_directory']/'stdout').write_bytes(b'preserved partial evidence')
            raise error
        original=runtime.read_relative
        def read(root,path,*args,**kwargs):
            if path=='stdout':raise OSError(errno.EIO,'synthetic secondary read')
            return original(root,path,*args,**kwargs)
        with mock.patch.object(runtime.platform,'system',return_value='Darwin'),\
             mock.patch.object(runtime.platform,'machine',return_value='arm64'),\
             mock.patch.object(runtime,'run_bounded',side_effect=fail),\
             mock.patch.object(runtime,'read_relative',side_effect=read):
            with self.assertRaises(OSError)as raised:
                runtime.native(['/usr/bin/codesign','--verify','--strict','owned'],self.root,'native.0.verify',commands)
        self.assertIs(raised.exception,error)
        self.assertEqual(commands[0]['native_error'],{'domain':'POSIX','code':errno.ENOEXEC,'exception_type':'OSError'})
        self.assertEqual(commands[0]['evidence_native_error']['code'],errno.EIO)
        self.assertIsNone(commands[0]['exit_code'])

    def test_signer_leaf_is_exact_selected_profile_certificate_with_bounded_variable_chain(self):
        self.put('certificates/native.0/cert0',CERT)
        self.put('certificates/native.0/cert1',b'ordinary synthetic intermediate')
        self.put('certificates/native.0/cert2',b'ordinary synthetic root')
        result=runtime.signer_leaf(self.root,'native.0',self.private,self.raw)
        self.assertEqual(result['sha1'],FINGERPRINT)
        self.assertEqual(result['chain_count'],3)
        # Other profile certificates need not share the selected signing identity.
        value=copy.deepcopy(self.value);value['DeveloperCertificates'].append(b'another allowed certificate')
        self.assertEqual(runtime.signer_leaf(self.root,'native.0',self.private,cms(value)),result)

    def test_wrong_missing_aliased_and_unbounded_certificate_outputs_refuse(self):
        for change in ['wrong','missing','leaf_alias','directory_alias','gap','extra','count','size']:
            with self.subTest(change=change):
                root=self.root/change;root.mkdir()
                self.put('certificates/native.0/cert0',CERT,root)
                if change=='wrong':self.put('certificates/native.0/cert0',b'same team, different leaf',root)
                elif change=='missing':(root/'certificates/native.0/cert0').unlink()
                elif change=='leaf_alias':
                    self.put('owned-leaf',CERT,root);path=root/'certificates/native.0/cert0'
                    path.unlink();path.symlink_to('../../owned-leaf')
                elif change=='directory_alias':
                    directory=root/'certificates/native.0';directory.rename(root/'other')
                    directory.symlink_to('../other',target_is_directory=True)
                elif change=='gap':self.put('certificates/native.0/cert2',b'gap',root)
                elif change=='extra':self.put('certificates/native.0/unaccounted',b'extra',root)
                elif change=='count':
                    for index in range(1,runtime.MAX_CERTIFICATES+1):self.put('certificates/native.0/cert'+str(index),b'chain',root)
                elif change=='size':self.put('certificates/native.0/cert1',b'x'*(runtime.CERTIFICATE_LIMIT+1),root)
                with self.assertRaises((Error,OSError)):runtime.signer_leaf(root,'native.0',self.private,self.raw)

    def completed_synthetic_runtime(self):
        install,old_build,ledger,manifest=self.sources()
        repo=self.root/'repo';repo.mkdir()
        for name in runtime.PRODUCERS:self.put(name,(REPO/name).read_bytes(),repo)
        build=repo/'.build/task7/artifact';build.mkdir(parents=True)
        self.put('build.json',b'{}\n',build)
        for path in [runtime.pairing_check.REBUILT_DRIVER,runtime.pairing_check.REBUILT_PE,
                     'dxmt/install/aarch64-unix/winemetal.so',runtime.pairing_check.FIXTURE_PE]:
            self.put(path,(old_build/path).read_bytes(),build)
        self.put('build.json',b'{}\n',install.parent)
        baseline={'artifacts_manifest':{'path':'inventory.json','sha256':'0'*64},
                  'arena_capacity':{'policy':'page-wx','limits':{'max_slots':756},'wine_execution':False}}
        self.put('original.provisionprofile',self.raw)
        out=repo/'.build/task7/runtime';self.runtime_root=out
        self.images=[{'path':row['runtime_path']}for row in sorted(ledger,key=lambda row:row['runtime_path'])
                     if row['kind']=='file'and row['format_kind']=='macho']
        prerequisite=({},install.parent,baseline,install,manifest)
        return repo,build,out,prerequisite

    def test_complete_metadata_pipeline_pure_replay_has_no_execution_claim(self):
        repo,build,out,proof=self.completed_synthetic_runtime()
        with mock.patch.object(runtime,'prerequisite',return_value=proof),\
             mock.patch.object(runtime,'native',side_effect=self.native_double()):
            result=runtime.prepare(build,self.root/'original.provisionprofile',out,repo=repo)
            self.assertEqual(len(result['native_images']),8)
            self.assertEqual(len(result['pe_images']),2)
            self.assertIs(result['runtime_eligible'],False)
            self.assertIs(result['game_qualified'],False)
            # Offline structural replay must not call even the Apple double.
            with mock.patch.object(runtime,'native',side_effect=AssertionError('pure replay called a tool')):
                runtime.verify_structural(out,repo=repo)
        self.assertEqual(len(list((out/'admission').glob('*/admission.json'))),1)
        materialization=runtime.decode_json((out/'materialization.json').read_bytes())
        self.assertEqual(materialization['capacity_scope'],'retained_source_bound_loader_capacity')
        self.assertIs(materialization['execution_performed'],False)

    def test_rehashed_receipts_cannot_admit_substituted_pe_or_profile_claims(self):
        repo,build,out,proof=self.completed_synthetic_runtime()
        with mock.patch.object(runtime,'prerequisite',return_value=proof),\
             mock.patch.object(runtime,'native',side_effect=self.native_double()):
            runtime.prepare(build,self.root/'original.provisionprofile',out,repo=repo)
            target=out/runtime.PAYLOAD/runtime.FIXTURE;original=target.read_bytes();target.write_bytes(original+b'changed')
            with self.assertRaisesRegex(Error,'pair_runtime_data_changed'):runtime.verify_structural(out,repo=repo)
            target.write_bytes(original)
            auth=runtime.decode_json((out/'authorization.json').read_bytes())
            auth['claims']['com.apple.security.cs.disable-library-validation']=True
            (out/'authorization.json').write_bytes(encoded(auth))
            report=runtime.decode_json((out/'runtime.json').read_bytes())
            report['authorization']['sha256']=digest((out/'authorization.json').read_bytes())
            (out/'runtime.json').write_bytes(encoded(report))
            with self.assertRaisesRegex(Error,'pair_authorization_claims_changed'):runtime.verify_structural(out,repo=repo)

    def test_live_admission_current_identity_loss_preserves_failure_without_execution(self):
        repo=self.root/'repo';repo.mkdir();owned=repo/'.build/task7/runtime';owned.mkdir(parents=True)
        self.put('runtime.json',b'{}\n',owned);self.put(runtime.BUNDLE+'/Contents/embedded.provisionprofile',self.raw,owned)
        value={'native_images':[],'runtime_eligible':False,'game_qualified':False}
        with mock.patch.object(runtime,'verify_structural',return_value=(value,self.private,self.raw)),\
             mock.patch.object(runtime,'legacy',return_value=self.reader),\
             mock.patch.object(runtime,'native',side_effect=self.native_double(identity='0 valid identities found')):
            with self.assertRaisesRegex(Error,'profile_signing_identity_missing_or_ambiguous'):
                runtime.verify_runtime(owned,repo=repo)
        failures=list((owned/'admission').glob('*/failed.json'))
        self.assertEqual(len(failures),1)
        failed=runtime.decode_json(failures[0].read_bytes())
        self.assertEqual(len(failed['commands']),7)
        self.assertIs(failed['runtime_eligible'],False)
        self.assertFalse(list((owned/'admission').glob('*/admission.json')))

    def test_prepare_native_start_failure_and_fresh_admission_keep_posix_cause(self):
        repo,build,out,proof=self.completed_synthetic_runtime()
        with mock.patch.object(runtime,'prerequisite',return_value=proof),\
             mock.patch.object(runtime.platform,'system',return_value='Darwin'),\
             mock.patch.object(runtime.platform,'machine',return_value='arm64'),\
             mock.patch.object(runtime,'run_bounded',side_effect=OSError(errno.EACCES,'synthetic Apple start refusal')):
            with self.assertRaises(Error)as raised:runtime.prepare(build,self.root/'original.provisionprofile',out,repo=repo)
        failure=runtime.decode_json((out/'failed.json').read_bytes())
        expected={'domain':'POSIX','code':errno.EACCES,'exception_type':'PermissionError'}
        self.assertEqual(failure['native_error'],expected)
        self.assertEqual(failure['errno'],errno.EACCES)
        self.assertEqual(raised.exception.native_error,expected)
        self.assertEqual(failure['authorization_commands'][0]['native_error'],expected)
        self.assertFalse((out/'runtime.json').exists())
        admission=repo/'.build/task7/admission-negative';admission.mkdir()
        self.put('runtime.json',b'{}\n',admission)
        value={'native_images':[],'runtime_eligible':False,'game_qualified':False}
        with mock.patch.object(runtime,'verify_structural',return_value=(value,self.private,self.raw)),\
             mock.patch.object(runtime.platform,'system',return_value='Darwin'),\
             mock.patch.object(runtime.platform,'machine',return_value='arm64'),\
             mock.patch.object(runtime,'run_bounded',side_effect=OSError(errno.ENOTDIR,'synthetic current start refusal')):
            with self.assertRaises(Error)as raised:runtime.verify_runtime(admission,repo=repo)
        failures=list((admission/'admission').glob('*/failed.json'))
        self.assertEqual(len(failures),1)
        observed=runtime.decode_json(failures[0].read_bytes())
        self.assertEqual(observed['native_error'],{'domain':'POSIX','code':errno.ENOTDIR,'exception_type':'NotADirectoryError'})
        self.assertEqual(raised.exception.native_error,observed['native_error'])
        self.assertIsNone(observed['commands'][0]['exit_code'])
        self.assertIs(observed['runtime_eligible'],False)
        self.assertFalse(list((admission/'admission').glob('*/admission.json')))

    def test_fresh_admission_wrong_leaf_refuses_even_when_claims_team_and_identity_match(self):
        repo,build,out,proof=self.completed_synthetic_runtime()
        with mock.patch.object(runtime,'prerequisite',return_value=proof),\
             mock.patch.object(runtime,'native',side_effect=self.native_double()):
            runtime.prepare(build,self.root/'original.provisionprofile',out,repo=repo)
        with mock.patch.object(runtime,'prerequisite',return_value=proof),\
             mock.patch.object(runtime,'native',side_effect=self.native_double(certificate=b'wrong leaf, identical metadata')):
            with self.assertRaisesRegex(Error,'pair_signer_leaf_mismatch'):runtime.verify_runtime(out,repo=repo)
        failures=list((out/'admission').glob('*/failed.json'))
        self.assertEqual(len(failures),1)
        observed=runtime.decode_json(failures[0].read_bytes())
        self.assertEqual(observed['error'],'pair_signer_leaf_mismatch')
        self.assertIs(observed['runtime_eligible'],False)


if __name__=='__main__':unittest.main()
