"""Synthetic reproduction receipts and real file-integrity rejection checks.

No Wine build, signing, native fixture or restricted operation executes here.
Existing heavy gate calls are mocked; receipt/path/hash/serialization selectors
and final source/install/signed tree hashing are exercised on owned temp files.
"""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/wine'))
import build
import reproduction_evidence as r
import signing
from common import Error, encoded, sha256


class ReceiptFixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.repo=Path(self.temp.name).resolve(); self.task=self.repo/'.build/task4'; self.task.mkdir(parents=True)
        self.root=self.task/'reproduction'; self.tools=self.task/'tools'; self.tools.mkdir()
        self.cache=self.repo/'.build/source-cache'; self.cache.mkdir()
        self.local=self.task/'private/signing.json'; self.local.parent.mkdir(); self.local.write_text('PRIVATE_SIGNING_SENTINEL')
        for name in r.CONFIGURATION.values():
            p=self.repo/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(encoded({'fixed':name}))
        self.lock_hash=sha256(self.repo/r.CONFIGURATION['toolchain'])
        self.put(self.tools/'prepared.json',{'lock_sha256':self.lock_hash})
        for name in (*build.PRODUCERS,'reproduction_evidence.py','reproduce.py','unsigned_compare.py'):
            p=self.repo/'tools/wine'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('Synthetic source '+name)
        reference=self.task/'historical'; reference.mkdir(); self.put(reference/'build.json',{'historical':True})
        public=self.repo/'mydocs/working/stage5.json'; public.parent.mkdir(parents=True)
        self.put(public,{'record_kind':'wine_stage5_observations','build':{'build_sha256':sha256(reference/'build.json')}})
        names={name:'tools/wine/'+name for name in ('reproduction_evidence.py','reproduce.py','unsigned_compare.py')}
        for key,value in {'REPO':self.repo,'REFERENCE_BUILD':reference,'REFERENCE_PUBLIC':public,
            'REFERENCE_BUILD_SHA256':sha256(reference/'build.json'),'REFERENCE_PUBLIC_SHA256':sha256(public),
            'SOURCES':names,'PRODUCERS':tuple(names.values())}.items():
            p=patch.object(r,key,value);p.start();self.addCleanup(p.stop)
        p=patch.object(r.shutil,'disk_usage',return_value=SimpleNamespace(free=30*r.GIB));p.start();self.addCleanup(p.stop)
        self.start=self.begin(); self.paths=r.layout(self.root)

    def put(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(encoded(value));return sha256(path)

    def begin(self,root=None):
        return r.create_start(root or self.root,source_cache=self.cache,tools=self.tools,local_signing=self.local)

    def rows(self):
        return [r.operation_result(self.start,name,'passed',started_ns=10+i*10,finished_ns=15+i*10)
                for i,name in enumerate(r.OPERATIONS)]


class ReproductionReceiptTests(ReceiptFixture):
    def test_start_uses_fresh_siblings_and_fixed_absent_roles(self):
        self.assertEqual(len(self.paths['native_build'].name),20)
        self.assertEqual(self.paths['inputs'].parent,self.task)
        self.assertEqual(r.load_start(self.root),self.start)
        for key,path in self.paths.items():
            if key!='root':self.assertFalse(path.exists())
        with self.assertRaisesRegex(Error,'reproduction_output_not_empty'):self.begin()

    def test_existing_sibling_and_symlink_ancestors_are_rejected(self):
        output=self.task/'another'; (self.task/'another-inputs').mkdir()
        with self.assertRaisesRegex(Error,'reproduction_output_exists'):self.begin(output)
        anchor_output=self.task/'anchor-test';(self.task/'anchor-test-anchor6').mkdir()
        with self.assertRaisesRegex(Error,'reproduction_output_exists'):self.begin(anchor_output)
        alias=self.task/'alias'; alias.symlink_to(self.root,target_is_directory=True)
        with self.assertRaisesRegex(Error,'reproduction_symlink'):r.layout(alias)

    def test_start_detects_current_producer_cache_configuration_and_snapshot_drift(self):
        targets=[self.repo/r.PRODUCERS[0],self.tools/'prepared.json',self.local,
                 self.repo/r.CONFIGURATION['config'],self.root/'producer'/r.PRODUCERS[0],r.REFERENCE_PUBLIC]
        for path in targets:
            original=path.read_bytes();path.write_bytes(original+b' ')
            with self.subTest(path=path.name),self.assertRaises(Error):r.load_start(self.root)
            path.write_bytes(original)

    def test_partial_failed_capture_preserves_primary_error_and_unperformed(self):
        self.paths['inputs'].mkdir(); (self.paths['inputs']/'prepared.json').symlink_to(self.local)
        row=r.operation_result(self.start,'prepare_inputs','failed',error='original_failure',started_ns=1,finished_ns=2)
        self.assertIsNone(row['record']);self.assertEqual(row['error'],'original_failure')
        rows=[row]+[r.operation_result(self.start,n,'unperformed') for n in r.OPERATIONS[1:]]
        value=r.write_terminal(self.root,self.start,rows,error='original_failure')
        self.assertFalse(value['complete'])
        self.assertTrue(all(x['status']=='unperformed' for x in value['operations'][1:]))
        with self.assertRaisesRegex(Error,'reproduction_incomplete'):r._terminal(self.root,self.start)

    def test_failed_terminal_survives_altered_start_while_success_cannot(self):
        (self.root/'start.json').write_bytes(b'{"altered":true}')
        rows=[r.operation_result(self.start,r.OPERATIONS[0],'failed',error='reproduction_start_changed',started_ns=1,finished_ns=2)]
        rows.extend(r.operation_result(self.start,n,'unperformed') for n in r.OPERATIONS[1:])
        value=r.write_terminal(self.root,self.start,rows,error='reproduction_start_changed')
        self.assertEqual(value['start_sha256'],hashlib.sha256(encoded(self.start)).hexdigest())
        self.assertEqual(value['error'],'reproduction_start_changed')

    def test_serial_timestamps_and_exact_step_order_are_required(self):
        for _,(path,directory) in r.operation_paths(self.paths).items():
            directory.mkdir(parents=True,exist_ok=True);self.put(path,{'synthetic':True})
        rows=self.rows()
        for change in ('reorder','overlap','boolean','missing','duplicate'):
            value=copy.deepcopy(rows)
            if change=='reorder':value[0],value[1]=value[1],value[0]
            elif change=='overlap':value[1]['started_ns']=value[0]['finished_ns']
            elif change=='boolean':value[0]['started_ns']=True
            elif change=='missing':value.pop()
            else:value[-1]=copy.deepcopy(value[0])
            with self.subTest(change=change),self.assertRaises(Error):r._check_operations(self.start,value,complete=True)
        r._check_operations(self.start,rows,complete=True)

    def test_replay_rejects_input_alias_in_altered_start(self):
        changed=copy.deepcopy(self.start)
        self.paths['native_build'].mkdir()
        changed['source_cache']=self.paths['native_build'].relative_to(self.repo).as_posix()
        self.put(self.root/'start.json',changed)
        with self.assertRaisesRegex(Error,'reproduction_input_output_alias'):r.load_start(self.root)

    def test_root_replacement_is_not_accepted_by_path_alone(self):
        moved=self.task/'moved';self.root.rename(moved);self.root.mkdir()
        (self.root/'start.json').write_bytes((moved/'start.json').read_bytes())
        with self.assertRaisesRegex(Error,'reproduction_root_changed'):r.load_start(self.root)


class ReproductionValidationTests(ReceiptFixture):
    def setUp(self):
        super().setUp()
        p=self.paths; p['inputs'].mkdir(); (p['inputs']/'wine-source.tar').write_bytes(b'original pinned source')
        self.prepared={'components':[{'commit':'1'*40,'tree':'2'*40,'archive_sha256':sha256(p['inputs']/'wine-source.tar'),
            'files_manifest':{'sha256':'3'*64}}]}
        self.put(p['inputs']/'prepared.json',self.prepared)
        self.input_gate={'gate_passed':True,'source_prepared_sha256':sha256(p['inputs']/'prepared.json'),
            'tool_prepared_sha256':sha256(self.tools/'prepared.json'),'checks_passed':38,'commands_passed':59}
        p['toolchain_work'].mkdir(); self.put(p['toolchain_check'],{'source_prepared_path':str(p['inputs']/'prepared.json')})
        self.arena={'gate_passed':True,'policy':'page-wx','scope':'fresh_native_arena_prerequisite',
            'wine_execution':False,'runtime_qualified':False,'game_qualified':False,'cases_passed':6}
        self.put(p['native_arena']/'reproduction.json',{'synthetic_native_arena':True})
        self.built={}
        for key,variant in r.BUILD_ROLES:
            directory=p[key]; (directory/'source').mkdir(parents=True); (directory/'source/source.c').write_text('public source')
            (directory/'install').mkdir(); (directory/'install/native.dylib').write_bytes(struct.pack('<8I',0xfeedfacf,0x100000c,0,2,0,0,0,0))
            pe=bytearray(96);pe[:2]=b'MZ';struct.pack_into('<I',pe,60,64);pe[64:68]=b'PE\0\0';struct.pack_into('<H',pe,68,0xaa64)
            (directory/'install/ntdll.dll').write_bytes(pe)
            source_hash=self.put(directory/'source-files.json',build.inventory(directory/'source'))
            install_hash=self.put(directory/'artifacts.json',build.inventory(directory/'install',binary=True))
            value={'variant':variant,'fixture_suite':'mac-driver','code_publication_policy':'page-wx',
                'source_argument_policy':'stable_relative_v1','install_root':str(directory/'install'),
                'patches':[],'fixture_hashes':{'fixture.c':'6'*64},'sdk':{'version':'synthetic'},
                'configuration':{'variant':variant},
                'source_inputs_root':str(p['inputs']),'tools_root':str(self.tools),
                'source_prepared_sha256':sha256(p['inputs']/'prepared.json'),'tool_prepared_sha256':sha256(self.tools/'prepared.json'),
                'producer_sha256':{name:sha256(self.repo/'tools/wine'/name) for name in build.PRODUCERS},
                'record_hashes':dict(self.start['configuration_sha256']),'source_manifest':{'path':'source-files.json','sha256':source_hash},
                'artifacts_manifest':{'path':'artifacts.json','sha256':install_hash},'native_artifact_count':1,'pe_artifact_count':1,
                'commands':[{'id':'compile','argv':['PRIVATE_ARGV_SENTINEL']}],
                'private_path':'/Users/PRIVATE_PATH_SENTINEL','arena_capacity':{'assessment':{
                    'scope':'compile_only_arm64ec_companion','image_measurement':'arm64_outer_headers_including_arm64x',
                    'fits_native_limits':False,'native_runtime_qualification':'unassessed'}}}
            self.put(directory/'build.json',value);self.built[key]=value
            self.put(directory/'modules.json',{'modules':[{'path':'lib/wine/aarch64-windows/ntdll.dll',
                'sha256':sha256(directory/'install/ntdll.dll'),'hybrid_required':variant=='arm64ec-build',
                'facts':{'machine':0xaa64,'exports':[{'name':'public_export'}]}}]})
        self.put(p['native_build']/'abi-review.json',{'review':'synthetic'})
        bundle=p['signed']/signing.BUNDLE;bundle.mkdir(parents=True);(bundle/'private-profile').write_text('PRIVATE_PROFILE_SENTINEL')
        files_hash=self.put(p['signed']/'signed-files.json',{'files':signing.inventory(bundle)})
        self.put(p['signed']/'signed.json',{'build_ref':{'path':str(p['native_build']/'build.json')},'files_manifest_sha256':files_hash})
        self.native={'build':{'build_sha256':sha256(p['native_build']/'build.json')},'signed_sha256':sha256(p['signed']/'signed.json')}
        for key in ('bootstrap','mac_driver'):self.put(p[key]/'run.json',{'passed':True})
        self.comparison={'record_kind':'wine_unsigned_comparison','gate_passed':True,'reference_build_sha256':sha256(p['native_reference_build']/'build.json'),
            'candidate_build_sha256':sha256(p['native_build']/'build.json'),
            'reference_inventory_sha256':self.built['native_reference_build']['artifacts_manifest']['sha256'],
            'candidate_inventory_sha256':self.built['native_build']['artifacts_manifest']['sha256'],'reference_files':2,'candidate_files':2,'exact_files':2,
            'explained_metadata_files':0,'unexplained_files':0,'missing_paths':[],'extra_paths':[],
            'metadata_changed_paths':[],'symlinks_equal':True,'byte_identity':True,'signed_byte_identity_claimed':False,
            'policy_ids':[],'private_profile':'PRIVATE_COMPARISON_SENTINEL'}
        self.put(p['unsigned_compare'],self.comparison)
        self.rows_value=self.rows();r.write_terminal(self.root,self.start,self.rows_value)
        self.mocks={}
        for target,value in {'prepare.verify_prepared':self.prepared,'toolchain.verify_prepared_tools':{'lock_sha256':self.lock_hash},
            'verify.validate_stage1':self.input_gate,'verify.validate_builds':{'gate_passed':True},
            'stage5_evidence.export':self.native,'modules.validate_inventory':{},
            'unsigned_compare.validate_unsigned_comparison':self.comparison,
            'arena_reproduction.validate':self.arena}.items():
            patcher=patch(target,return_value=value);self.mocks[target]=patcher.start();self.addCleanup(patcher.stop)
        patcher=patch('build.verify_build',side_effect=lambda path:json.loads((Path(path)/'build.json').read_bytes()))
        self.mocks['build.verify_build']=patcher.start();self.addCleanup(patcher.stop)

    def test_public_result_preserves_reuse_scope_and_excludes_private_fields(self):
        value=r.validate(self.root); raw=encoded(value).decode()
        self.assertTrue(value['reproduction_passed']);self.assertTrue(value['tool_cache']['reused'])
        self.assertFalse(value['compiler_rebuilt']);self.assertFalse(value['companion']['guest_execution'])
        self.assertFalse(value['companion']['native_arena_fit_observed'])
        self.assertEqual(value['wine_variants_rebuilt'],['arm64','arm64ec-build'])
        self.assertEqual(value['native_arena_prerequisite'],self.arena)
        self.assertEqual(value['native_rebuild_count'],2)
        self.assertEqual(value['source_argument_policy'],'stable_relative_v1')
        self.assertFalse(value['fresh_reference']['runtime_executed'])
        self.assertFalse(value['fresh_reference']['wine_runtime_executed'])
        self.assertFalse(value['fresh_reference']['development_signed'])
        self.assertFalse(value['historical_reference']['byte_equivalence_reference'])
        self.assertFalse(value['historical_reference']['byte_equivalence_to_fresh_builds_claimed'])
        self.assertEqual(value['fresh_reference']['build_sha256'],sha256(self.paths['native_reference_build']/'build.json'))
        self.mocks['build.verify_build'].assert_called_once_with(self.paths['native_reference_build'])
        self.mocks['unsigned_compare.validate_unsigned_comparison'].assert_called_once_with(
            self.paths['unsigned_compare'],self.paths['native_reference_build'],self.paths['native_build'])
        self.mocks['arena_reproduction.validate'].assert_called_once_with(self.paths['native_arena'],self.local)
        for secret in ('PRIVATE_','/Users/',str(self.repo),'root_identity','started_ns','attempt_id'):
            self.assertNotIn(secret,raw)
        self.mocks['verify.validate_builds'].assert_called_once_with(self.paths['native_build'],self.paths['companion_build'])
        self.mocks['stage5_evidence.export'].assert_called_once_with(self.paths['native_build'],self.paths['mac_driver'],self.paths['bootstrap'])

    def rebind_build(self,key,value):
        path=self.paths[key]/'build.json';self.put(path,value)
        terminal=json.loads((self.root/'reproduction.json').read_bytes())
        next(row for row in terminal['operations'] if row['id']==key)['record']['sha256']=sha256(path)
        self.put(self.root/'reproduction.json',terminal)

    def test_every_fresh_build_requires_the_explicit_stable_policy(self):
        for key,_ in r.BUILD_ROLES:
            original=json.loads((self.paths[key]/'build.json').read_bytes())
            for policy in (None,'legacy_absolute','unknown',True):
                changed=copy.deepcopy(original)
                if policy is None:changed.pop('source_argument_policy')
                else:changed['source_argument_policy']=policy
                self.rebind_build(key,changed)
                with self.subTest(role=key,policy=policy),self.assertRaisesRegex(Error,'reproduction_build_binding'):
                    r.validate(self.root)
            self.rebind_build(key,original)

    def test_historical_or_wrong_inventory_comparison_reference_is_rejected(self):
        for key,value in [('reference_build_sha256',r.REFERENCE_BUILD_SHA256),
                          ('candidate_build_sha256',sha256(self.paths['native_reference_build']/'build.json')),
                          ('reference_inventory_sha256','f'*64)]:
            original=self.comparison[key];self.comparison[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(Error,'reproduction_comparison_reference'):
                r.validate(self.root)
            self.comparison[key]=original

    def test_anchor_must_share_patched_sources_fixtures_sdk_and_current_producers(self):
        key='native_reference_build';original=json.loads((self.paths[key]/'build.json').read_bytes())
        for field in ('source_manifest','fixture_hashes','sdk','producer_sha256'):
            changed=copy.deepcopy(original)
            if field=='source_manifest':changed[field]['sha256']='f'*64
            elif field=='fixture_hashes':changed[field]['fixture.c']='f'*64
            elif field=='sdk':changed[field]['version']='different'
            else:changed[field]['build.py']='f'*64
            self.rebind_build(key,changed)
            with self.subTest(field=field),self.assertRaisesRegex(Error,'reproduction_(shared_build_inputs|build_producer_changed)'):
                r.validate(self.root)
        self.rebind_build(key,original)

    def test_native_arena_failure_or_wine_scope_cannot_be_promoted(self):
        for key,value in [('gate_passed',False),('gate_passed',1),('policy','thread-jit'),
                          ('scope','historical_native_prerequisite_receipt'),('wine_execution',True)]:
            original=self.arena[key];self.arena[key]=value
            with self.subTest(key=key,value=value),self.assertRaisesRegex(Error,'reproduction_native_arena_gate'):
                r.validate(self.root)
            self.arena[key]=original

    def test_native_arena_replay_cannot_replace_bound_receipt(self):
        path=self.paths['native_arena']/'reproduction.json'
        def changed(*args):
            self.put(path,{'replacement_after_validation':True})
            return self.arena
        self.mocks['arena_reproduction.validate'].side_effect=changed
        with self.assertRaisesRegex(Error,'reproduction_record_changed'):r.validate(self.root)

    def test_valid_failed_unsigned_comparison_cannot_be_promoted(self):
        self.comparison.update(gate_passed=False,unexplained_files=1,exact_files=1)
        with self.assertRaisesRegex(Error,'reproduction_unsigned_difference_unexplained'):r.validate(self.root)

    def test_mixed_signed_runtime_or_build_is_rejected(self):
        self.native['signed_sha256']='f'*64
        with self.assertRaisesRegex(Error,'reproduction_signed_root'):r.validate(self.root)
        self.native['signed_sha256']=sha256(self.paths['signed']/'signed.json')
        self.native['build']['build_sha256']='f'*64
        with self.assertRaisesRegex(Error,'reproduction_native_gate'):r.validate(self.root)

    def test_final_actual_byte_guard_catches_late_source_install_and_signed_mutation(self):
        paths=[self.paths['native_reference_build']/'source/source.c',
               self.paths['native_reference_build']/'install/ntdll.dll',
               self.paths['companion_build']/'source/source.c',self.paths['companion_build']/'install/ntdll.dll',
               self.paths['signed']/signing.BUNDLE/'private-profile']
        for path in paths:
            original=path.read_bytes()
            def changed(*args):path.write_bytes(original+b'x');return self.comparison
            self.mocks['unsigned_compare.validate_unsigned_comparison'].side_effect=changed
            with self.subTest(path=path.name),self.assertRaisesRegex(Error,'reproduction_final_'):r.validate(self.root)
            path.write_bytes(original)
        self.mocks['unsigned_compare.validate_unsigned_comparison'].side_effect=None

    def test_changed_receipt_bytes_and_directory_identity_are_rejected(self):
        path=self.paths['bootstrap']/'run.json';original=path.read_bytes();path.write_bytes(original+b' ')
        with self.assertRaisesRegex(Error,'reproduction_record_changed'):r.validate(self.root)
        path.write_bytes(original)
        changed=copy.deepcopy(self.rows_value);changed[0]['directory_identity']['inode']+=1
        with self.assertRaisesRegex(Error,'reproduction_directory_changed'):r._check_operations(self.start,changed,complete=True)

    def test_current_companion_producer_cannot_reuse_an_archived_old_hash(self):
        path=self.paths['companion_build']/'build.json';v=json.loads(path.read_bytes());v['producer_sha256']['build.py']='e'*64
        self.put(path,v)
        terminal=json.loads((self.root/'reproduction.json').read_bytes())
        next(row for row in terminal['operations'] if row['id']=='companion_build')['record']['sha256']=sha256(path)
        self.put(self.root/'reproduction.json',terminal)
        with self.assertRaisesRegex(Error,'reproduction_build_producer_changed'):r.validate(self.root)


class ReproductionProducerCoverageTests(unittest.TestCase):
    def test_current_native_arena_inputs_are_snapshotted(self):
        import arena_reproduction
        import pe_arena_probe
        expected=set(arena_reproduction.PRODUCER_FILES) | set(pe_arena_probe.PRODUCER_FILES) | set(pe_arena_probe.SOURCE_FILES)
        self.assertTrue(expected <= set(r.PRODUCERS))
        self.assertTrue(expected <= set(r.SOURCES.values()))


if __name__=='__main__':unittest.main()
