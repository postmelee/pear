"""Portable source/receipt controls only; all native build/evidence gates mocked.

Fixtures contain ordinary plain text bytes, never synthetic executables.
"""
import contextlib
import copy
import io
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import sys

REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'tools/dxmt'))
import compare as c
import reproduce as r


class Reconstruction(unittest.TestCase):
    def setUp(self):
        self.holder=tempfile.TemporaryDirectory()
        self.repo=Path(self.holder.name).resolve()
        (self.repo/'.build/task7').mkdir(parents=True)
        for name in set(r.OWN_PRODUCERS+r.REPLAY_SOURCES+r.INPUTS):
            self.put(self.repo,name,('source fixture '+name).encode())
        self.donor=self.owned('donor');self.old=self.owned('reference')
        self.run=self.owned('native-run');self.runtime=self.owned('runtime')
        self.output=self.repo/'.build/task7/reconstruction'
        self.candidate=r.expected_candidate(self.output)
        self.put(self.donor,'build.json',b'{"scope":"plain donor metadata"}\n')
        self.put(self.old,'build.json',b'{"scope":"plain reference metadata"}\n')
        self.left=self.pair();self.right=copy.deepcopy(self.left)
        self.put(self.run,r.pairing_evidence.REVIEW,b'{"review":"fixture metadata"}\n')
        self.write_native(self.old)
    def tearDown(self):self.holder.cleanup()
    def owned(self,name):
        path=self.repo/'.build/task7'/name;path.mkdir();return path
    def put(self,root,path,raw,mode=0o644):
        target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);target.chmod(mode)
    def pair(self):
        return {'scope':'typed_native_metal_pairing','passed':True,'prior_artifact':r.reference(self.donor),
                'role_reference':{'path':'source-selected roles','sha256':c.digest(b'roles')},
                'series_sha256':c.digest(b'series'),'supplemental_inputs':{'fixture':'source-bound'},
                'fixture_sources':{'fixture.c':c.digest(b'fixture')},'producer_files':{'builder':c.digest(b'builder')},
                'wine_configuration':{'HOST_ARCH':'aarch64'},
                'source':{name:{'after_files':[{'path':'real-source.c','sha256':c.digest(name.encode()),
                         'size_bytes':len(name),'mode':0o644}]}for name in ['wine','dxmt']},
                **{key:False for key in ['pairing_verified','native_execution','hybrid_execution',
                'translated_guest_execution','game_qualified','runtime_eligible']}}
    def observed(self):
        return {'finite_native_scope_complete':True,'metal_api_validation':'reviewed_no_errors',
                'runtime_eligible':False,'game_qualified':False,'distribution_qualified':False}
    def write_native(self,target):
        self.put(self.runtime,'runtime.json',r.encoded({'build_ref':r.reference(target)}))
        self.put(self.run,'run.json',r.encoded({'runtime_ref':r.reference(self.runtime,'runtime.json')}))
    def args(self):
        return SimpleNamespace(artifact=str(self.donor),reference=str(self.old),native_evidence=str(self.run),
           output=str(self.output),max_growth_bytes=8*1024**3,reserve_free_bytes=4*1024**3,require_empty=True)
    def byte_inventory(self,changed=False):
        return [{'path':'data','kind':'file','mode':0o644,'size_bytes':5,
                 'sha256':c.digest(b'other'if changed else b'owned')}]
    def views(self,changed=False):
        left=self.byte_inventory();right=self.byte_inventory(changed)
        return left,right,{'source':'verified fixture origins'},c.compare_entries(left,right)
    @contextlib.contextmanager
    def constructor_gates(self,changed=False,build_error=None,preflight_error=None):
        def build(args):
            self.assertEqual(args.artifact,str(self.donor));self.assertEqual(args.output,str(self.candidate))
            self.assertEqual(args.max_growth_bytes,8*1024**3);self.assertIs(args.require_empty,True)
            self.candidate.mkdir();self.put(self.candidate,'build.json',b'{"scope":"plain candidate metadata"}\n')
            if build_error:raise build_error
        with contextlib.ExitStack()as stack:
            stack.enter_context(patch.object(r.stage3,'verify_build',side_effect=preflight_error or (lambda *a,**k:{})))
            stack.enter_context(patch.object(r.pairing_build,'construct',side_effect=build))
            stack.enter_context(patch.object(r,'verified_pair',side_effect=lambda root,repo:self.left if root==self.old else self.right))
            stack.enter_context(patch.object(r,'comparison_views',side_effect=lambda *a:self.views(changed)))
            native=stack.enter_context(patch.object(r.pairing_evidence,'verify_native_evidence',return_value=self.observed()))
            yield native
    def complete(self):
        with self.constructor_gates():return r.construct(self.args(),repo=self.repo)
    def rewrite(self,value):self.put(self.output,'reproduction.json',r.encoded(value))
    def test_sibling_candidate_and_length(self):
        self.assertEqual(r.expected_candidate(self.output),self.candidate)
        with self.assertRaises(r.Error):r.expected_candidate(self.output.with_name('a'*90))
    def test_policy_rejects_bool_small_ceiling_and_reserve(self):
        for cap,reserve in [(False,4*1024**3),(1024**3,4*1024**3),(9*1024**3,4*1024**3),(8*1024**3,True),(8*1024**3,3*1024**3)]:
            with self.subTest(cap=cap,reserve=reserve),self.assertRaises(r.Error):r.policy(cap,reserve)
        self.assertIsNone(r.policy(8*1024**3,4*1024**3)['measured_build_peak_bytes'])
    def test_source_signature_includes_real_source_roles_and_fixture(self):
        before=r.source_signature(self.left)
        for key in ['role_reference','supplemental_inputs','fixture_sources','producer_files','wine_configuration']:
            other=copy.deepcopy(self.left);other[key]={'different':'source'}
            with self.subTest(key=key):self.assertNotEqual(before,r.source_signature(other))
        other=copy.deepcopy(self.left);other['source']['wine']['after_files'][0]['mode']=0o755
        self.assertNotEqual(before,r.source_signature(other))
    def test_pair_gate_rejects_false_qualification_claims(self):
        for key in ['pairing_verified','native_execution','hybrid_execution','translated_guest_execution','game_qualified','runtime_eligible']:
            other=copy.deepcopy(self.left);other[key]=True
            with patch.object(r.pairing_check,'verify_build',return_value=other),self.subTest(key=key),self.assertRaises(r.Error):
                r.verified_pair(self.old,self.repo)
    def test_selected_plain_bytes_parent_modes_and_no_extra_glob(self):
        self.put(self.old,'objects/sub/data',b'plain selected bytes')
        self.put(self.old,'objects/irrelevant',b'not selected')
        rows=r.selected_tree(self.old,['objects/sub/data'])
        self.assertEqual([row['path']for row in rows],['objects','objects/sub','objects/sub/data'])
        self.assertEqual(rows[-1]['sha256'],c.digest(b'plain selected bytes'))
    def test_selected_hardlink_alias_and_duplicate_refusal(self):
        self.put(self.old,'objects/data',b'plain selected bytes')
        os.link(self.old/'objects/data',self.old/'objects/other')
        with self.assertRaises(c.Error):r.selected_tree(self.old,['objects/data'])
        (self.old/'objects/other').unlink();(self.old/'alias').symlink_to('objects')
        with self.assertRaises(c.Error):r.selected_tree(self.old,['alias/data'])
        with self.assertRaises(c.Error):r.selected_tree(self.old,['objects/data','objects/data'])
    def test_selected_replaced_or_mode_changed_during_read(self):
        self.put(self.old,'objects/data',b'plain selected bytes')
        original=c.os.read;changed=False
        def mutate(fd,size):
            nonlocal changed
            raw=original(fd,size)
            if raw and not changed:changed=True;(self.old/'objects/data').chmod(0o755)
            return raw
        with patch.object(c.os,'read',side_effect=mutate),self.assertRaises(c.Error):r.selected_tree(self.old,['objects/data'])
    def inventory_fixture(self):
        native=self.owned('baseline');self.put(native,'build.json',b'plain baseline build bytes')
        install=native/'install'
        for path in ['lib/wine/aarch64-unix/winemac.so','lib/wine/aarch64-windows/winemac.drv',
                     'share/retained.winmd','libexec/pear-stage3/api-x64.exe','bin/data']:
            self.put(install,path,('unchanged plain metadata '+path).encode())
        (install/'bin/alias').symlink_to('data')
        rows=c.scan_tree(install)
        manifest={'schema_version':1,'record_kind':'wine_build_inventory',
          'files':[{**{key:row[key]for key in ['path','mode','size_bytes','sha256']},
                    'kind':'pe_metadata'if row['path'].endswith('.winmd')else'data'}for row in rows if row['kind']=='file'],
          'symlinks':[{'path':row['path'],'target':row['target']}for row in rows if row['kind']=='symlink']}
        raw=r.encoded(manifest);self.put(native,'installed-files.json',raw)
        baseline={'install_root':str(install),'artifacts_manifest':{'path':'installed-files.json','sha256':c.digest(raw)}}
        for path in [r.pairing_check.REBUILT_DRIVER,r.pairing_check.REBUILT_PE,r.pairing_check.FIXTURE_PE,
            'dxmt/objects/'+r.stage3.NATIVE_TARGET]+['dxmt/objects/'+p for p in r.stage3.PE_TARGETS.values()]+[
            'dxmt/compiler/'+p for p in r.stage3.PE_TARGETS]+['dxmt/install/aarch64-windows/'+p for p in r.stage3.PE_TARGETS]+[
            'dxmt/install/aarch64-unix/winemetal.so']:
            self.put(self.old,path,('plain output bytes '+path).encode())
        generated=['native.ini','cross.ini','bin/git','bin/xcrun','notices/selected/LICENSE']
        shaders=['objects/shader/fixture'+str(i)+suffix for i,suffix in enumerate(['.air','.h','.air','.h','.air','.h','.air','.metallib','.h'])]
        for path in generated+shaders+['objects/version.h']:self.put(self.old/'dxmt',path,('plain generated '+path).encode())
        facts={'generated_inputs':[{'path':p}for p in generated],
           'shader_outputs':[{'path':p}for p in shaders],'version_header':{'path':'objects/version.h'},
           'notices':[{'path':'notices/selected/LICENSE'}]}
        return native,baseline,facts
    @contextlib.contextmanager
    def inventory_gates(self,native,baseline,facts):
        # These three semantic build gates are mocked. Every ledger read,
        # byte/mode/symlink operation below is the actual portable implementation.
        with patch.object(r.stage3,'selector',return_value=({}, {'native':native},self.left['role_reference'])),\
             patch.object(r.pairing_build,'source_baseline',return_value=baseline),\
             patch.object(r.pairing_check,'inspect_pair',return_value=facts):yield
    def test_full_inventory_retains_metadata_foreign_negative_data_and_aliases(self):
        native,baseline,facts=self.inventory_fixture()
        with self.inventory_gates(native,baseline,facts):rows,origins=r.complete_inventory(self.old,self.left,self.repo)
        mapped={row['path']:row for row in rows}
        for path in ['wine/share/retained.winmd','wine/libexec/pear-stage3/api-x64.exe','wine/bin/alias',
               'wine/libexec/pear-dxmt/pairing-arm64.exe','wine/lib/wine/aarch64-unix/winemetal.so',
               'dxmt/aarch64-unix/winemetal.so','compiler/dxmt/compiler/d3d11.dll',
               'built/wine/objects/dlls/winemac.drv/winemac.so','generated/notices/selected/LICENSE','shaders/objects/version.h']:
            self.assertIn(path,mapped)
        self.assertEqual(mapped['wine/bin/alias']['target'],'data')
        self.assertEqual(origins['baseline_manifest_ref'],baseline['artifacts_manifest'])
        self.assertEqual(origins['baseline_directory_modes'],'actual_current_observation_no_historical_mode_baseline')
    def test_full_inventory_missing_retained_byte_and_alias_refuse(self):
        native,baseline,facts=self.inventory_fixture()
        (native/'install/share/retained.winmd').write_bytes(b'changed retained metadata')
        with self.inventory_gates(native,baseline,facts),self.assertRaises(c.Error):r.complete_inventory(self.old,self.left,self.repo)
    def test_full_inventory_generated_notice_omission_and_extra_install_visible(self):
        native,baseline,facts=self.inventory_fixture()
        wrong=copy.deepcopy(facts);wrong['generated_inputs']=wrong['generated_inputs'][:-1]
        with self.inventory_gates(native,baseline,wrong),self.assertRaises(r.Error):r.complete_inventory(self.old,self.left,self.repo)
        with self.inventory_gates(native,baseline,facts):before,_=r.complete_inventory(self.old,self.left,self.repo)
        self.put(self.old,'dxmt/install/extra/unexpected',b'plain extra bytes')
        with self.inventory_gates(native,baseline,facts):after,_=r.complete_inventory(self.old,self.left,self.repo)
        # The real paired-build inspector rejects this layout. Even if that
        # semantic gate were defective, the complete raw comparison exposes it.
        result=c.compare_entries(before,after);self.assertFalse(result['raw_equal'])
        self.assertIn('dxmt/extra/unexpected',[row['path']for row in result['differences']])
    def test_native_reference_binding_truthful_no_new_execution(self):
        self.candidate.mkdir();self.put(self.candidate,'build.json',b'candidate metadata')
        with patch.object(r.pairing_evidence,'verify_native_evidence',return_value=self.observed()):
            result=r.native_binding(self.run,self.old,self.candidate,{'raw_equal':True},self.left,self.right,self.repo)
        self.assertEqual(result['origin'],'reused_matching_stage4_reference');self.assertIs(result['new_native_execution_performed'],False)
        self.assertEqual(result['permission_transfer'],'not_inferred')
    def test_native_reference_rejects_changed_bytes_and_source(self):
        self.candidate.mkdir();self.put(self.candidate,'build.json',b'candidate metadata')
        with patch.object(r.pairing_evidence,'verify_native_evidence',return_value=self.observed()):
            with self.assertRaises(r.Error):r.native_binding(self.run,self.old,self.candidate,{'raw_equal':False},self.left,self.right,self.repo)
            changed=copy.deepcopy(self.right);changed['wine_configuration']={'changed':True}
            with self.assertRaises(r.Error):r.native_binding(self.run,self.old,self.candidate,{'raw_equal':True},self.left,changed,self.repo)
    def test_native_candidate_binding_and_wrong_build_refusal(self):
        self.candidate.mkdir();self.put(self.candidate,'build.json',b'candidate metadata');self.write_native(self.candidate)
        with patch.object(r.pairing_evidence,'verify_native_evidence',return_value=self.observed()):
            result=r.native_binding(self.run,self.old,self.candidate,{'raw_equal':True},self.left,self.right,self.repo)
            self.assertEqual(result['origin'],'fresh_final_candidate');self.assertIs(result['new_native_execution_performed'],True)
            self.write_native(self.donor)
            with self.assertRaises(r.Error):r.native_binding(self.run,self.old,self.candidate,{'raw_equal':True},self.left,self.right,self.repo)
    def test_native_scope_missing_review_and_changed_raw_refusal(self):
        self.candidate.mkdir();self.put(self.candidate,'build.json',b'candidate metadata')
        wrong=self.observed();wrong['metal_api_validation']='unperformed'
        with patch.object(r.pairing_evidence,'verify_native_evidence',return_value=wrong),self.assertRaises(r.Error):
            r.native_binding(self.run,self.old,self.candidate,{'raw_equal':True},self.left,self.right,self.repo)
        def change(*a,**k):self.put(self.run,r.pairing_evidence.REVIEW,b'different reviewed bytes');return self.observed()
        with patch.object(r.pairing_evidence,'verify_native_evidence',side_effect=change),self.assertRaises(r.Error):
            r.native_binding(self.run,self.old,self.candidate,{'raw_equal':True},self.left,self.right,self.repo)
    def test_native_runtime_ref_bytes_not_rehashed_on_trust(self):
        self.candidate.mkdir();self.put(self.candidate,'build.json',b'candidate metadata')
        self.put(self.runtime,'runtime.json',b'changed runtime bytes')
        with patch.object(r.pairing_evidence,'verify_native_evidence',return_value=self.observed()),self.assertRaises(r.Error):
            r.native_binding(self.run,self.old,self.candidate,{'raw_equal':True},self.left,self.right,self.repo)
    def test_complete_mocked_coordinator_independent_replay(self):
        value=self.complete()
        self.assertEqual(set(value),r.FIELDS);self.assertTrue(value['outcome']['reconstruction_complete'])
        for key in ['compiler_rebuilt','native_prerequisites_rebuilt','second_machine_reproduction','hybrid_execution_performed',
                    'translated_guest_execution_performed','game_qualified','runtime_eligible','distribution_qualified']:
            self.assertIs(value[key],False)
        self.assertTrue((self.output/'producers/tools/dxmt/reproduce.py').is_file())
    def test_raw_difference_preserves_both_inventories_and_primary_error(self):
        with self.constructor_gates(changed=True)as native,self.assertRaisesRegex(r.Error,'reconstruction_unsigned_difference'):
            r.construct(self.args(),repo=self.repo)
        native.assert_not_called()
        failed=r.decode_json(r.read_relative(self.output,'failed.json'))
        self.assertEqual(failed['phase'],'compare');self.assertTrue(failed['source_reconstruction_performed'])
        self.assertTrue(failed['construction_attempted']);self.assertEqual(failed['error'],'reconstruction_unsigned_difference')
        comparison=r.load_ref(self.output,failed['comparison_ref']);self.assertFalse(comparison['raw_equal'])
        self.assertEqual(len(comparison['differences']),1)
        self.assertEqual(set(failed['inventory_refs']),{'reference','candidate','origins'})
        self.assertTrue(self.candidate.is_dir())
    def test_preflight_refusal_and_real_errno_remain_unperformed(self):
        error=OSError(5,'actual portable I/O failure')
        with self.constructor_gates(preflight_error=error),self.assertRaises(OSError)as captured:r.construct(self.args(),repo=self.repo)
        self.assertIs(captured.exception,error)
        failed=r.decode_json(r.read_relative(self.output,'failed.json'))
        self.assertIs(failed['source_reconstruction_performed'],False);self.assertIs(failed['construction_attempted'],False)
        self.assertEqual(failed['native_error'],{'domain':'POSIX','code':5});self.assertFalse(self.candidate.exists())
    def test_failed_constructor_preserves_unknown_partial_completion(self):
        error=r.Error('bound_refusal')
        with self.constructor_gates(build_error=error),self.assertRaises(r.Error):r.construct(self.args(),repo=self.repo)
        failed=r.decode_json(r.read_relative(self.output,'failed.json'))
        self.assertTrue(failed['construction_attempted']);self.assertIs(failed['source_reconstruction_performed'],False)
        self.assertEqual(failed['phase'],'construct');self.assertTrue(self.candidate.exists())
    def test_failed_record_write_does_not_replace_original_error(self):
        original=r.write_new;error=r.Error('first_failure')
        def write(path,value):
            if path.name=='failed.json':raise OSError(28,'actual record write failure')
            return original(path,value)
        with self.constructor_gates(preflight_error=error),patch.object(r,'write_new',side_effect=write),self.assertRaises(r.Error)as result:
            r.construct(self.args(),repo=self.repo)
        self.assertIs(result.exception,error);self.assertEqual(error.reconstruction_record_error,{'type':'OSError','code':28})
    def test_source_producer_copy_or_current_byte_change_refuses(self):
        self.complete()
        self.put(self.output,'producers/tools/dxmt/compare.py',b'wrong source capture')
        with self.assertRaises(r.Error):r.verify(self.output,self.repo)
        self.put(self.output,'producers/tools/dxmt/compare.py',r.read_relative(self.repo,'tools/dxmt/compare.py'))
        self.put(self.repo,'tools/dxmt/compare.py',b'new producer source')
        with self.assertRaises(r.Error):r.verify(self.output,self.repo)
    def test_forged_outcome_qualification_and_bool_schema_refuse(self):
        value=self.complete()
        for key,replacement in [('runtime_eligible',True),('schema_version',True),('outcome',{'reconstruction_complete':True})]:
            changed=copy.deepcopy(value);changed[key]=replacement;self.rewrite(changed)
            with self.constructor_gates(),self.subTest(key=key),self.assertRaises(r.Error):r.verify(self.output,self.repo)
        self.rewrite(value)
    def test_changed_inventory_and_omitted_namespace_refuse_even_rehashed(self):
        value=self.complete();ref=value['inventory_refs']['candidate']
        self.put(self.output,ref['path'],r.encoded([]));value['inventory_refs']['candidate']['sha256']=c.digest(r.encoded([]));self.rewrite(value)
        with self.constructor_gates(),self.assertRaises(r.Error):r.verify(self.output,self.repo)
    def test_policy_bool_and_integer_are_not_interchangeable_on_replay(self):
        value=self.complete();construction=r.decode_json(r.read_relative(self.output,'construction.json'))
        construction['policy']['ceiling_is_peak_measurement']=0;self.put(self.output,'construction.json',r.encoded(construction))
        value['construction_ref']['sha256']=c.digest(r.encoded(construction));self.rewrite(value)
        with self.constructor_gates(),self.assertRaisesRegex(r.Error,'reconstruction_policy_changed'):r.verify(self.output,self.repo)
    def test_changed_comparison_or_native_review_binding_refuse(self):
        value=self.complete();comp=r.load_ref(self.output,value['comparison_ref']);comp['normalization_policy']='ignored_all_metadata'
        self.put(self.output,'comparison.json',r.encoded(comp));value['comparison_ref']['sha256']=c.digest(r.encoded(comp));self.rewrite(value)
        with self.constructor_gates(),self.assertRaises(r.Error):r.verify(self.output,self.repo)
    def test_changed_reference_and_explicit_failed_marker_refuse(self):
        value=self.complete();self.put(self.old,'build.json',b'changed reference bytes')
        with self.constructor_gates(),self.assertRaises(r.Error):r.verify(self.output,self.repo)
        self.put(self.output,'failed.json',r.encoded({'error':'actual earlier failure'}))
        with self.assertRaisesRegex(r.Error,'failed_reconstruction'):r.verify(self.output,self.repo)
    def test_candidate_and_donor_identity_refusal(self):
        args=self.args();args.reference=args.artifact
        with self.assertRaises(r.Error):r.construct(args,self.repo)
        self.assertFalse(self.candidate.exists())
    def test_cli_usage_cannot_mix_construction_and_replay(self):
        with contextlib.redirect_stderr(io.StringIO()):
            for argv in [['--output','x','--verify'],['--output','x','--verify','--require-complete','--artifact','x'],
                         ['--output','x','--artifact','x','--reference','y','--native-evidence','z','--require-empty']]:
                with self.subTest(argv=argv),self.assertRaises(SystemExit)as result:r.main(argv)
                self.assertEqual(result.exception.code,2)
    def build_only(self):
        args=self.args();args.native_evidence=None
        with self.constructor_gates()as native:
            value=r.construct(args,repo=self.repo);native.assert_not_called()
        return value
    def test_build_only_records_immutable_construction_without_complete_claim(self):
        value=self.build_only();self.assertEqual(set(value),r.CONSTRUCTION_FIELDS)
        self.assertIs(value['reconstruction_complete'],False);self.assertEqual(value['native_pairing_evidence'],'unperformed')
        self.assertFalse((self.output/'reproduction.json').exists());self.assertFalse((self.output/'failed.json').exists())
        with self.constructor_gates():self.assertEqual(r.verify_construction(self.output,self.repo),value)
    def test_later_completion_binds_same_candidate_actual_evidence_without_rebuild(self):
        self.build_only();before=r.read_relative(self.output,'construction.json');self.write_native(self.candidate)
        with self.constructor_gates(),patch.object(r.pairing_build,'construct')as builder:
            result=r.complete(self.output,self.run,self.repo);builder.assert_not_called()
        self.assertTrue(result['outcome']['reconstruction_complete'])
        self.assertEqual(result['native_evidence']['origin'],'fresh_final_candidate')
        self.assertIs(result['native_evidence']['new_native_execution_performed'],True)
        self.assertEqual(before,r.read_relative(self.output,'construction.json'))
        self.assertEqual(result['construction_ref'],{'path':'construction.json','sha256':c.digest(before)})
    def test_completion_failure_preserves_construction_and_allows_reviewed_retry(self):
        self.build_only();before=r.read_relative(self.output,'construction.json');self.write_native(self.donor)
        with self.constructor_gates(),self.assertRaises(r.Error):r.complete(self.output,self.run,self.repo)
        self.assertEqual(before,r.read_relative(self.output,'construction.json'))
        self.assertFalse((self.output/'failed.json').exists());self.assertFalse((self.output/'reproduction.json').exists())
        failures=list((self.output/'completion-failures').glob('*/failed.json'));self.assertEqual(len(failures),1)
        failure=r.decode_json(failures[0].read_bytes())
        self.assertEqual(failure['phase'],'native-evidence');self.assertIs(failure['reconstruction_complete'],False)
        self.assertEqual(failure['construction_ref']['sha256'],c.digest(before))
        self.write_native(self.candidate)
        with self.constructor_gates():result=r.complete(self.output,self.run,self.repo)
        self.assertTrue(result['outcome']['reconstruction_complete']);self.assertTrue(failures[0].is_file())
    def test_completion_cannot_overwrite_existing_complete_or_change_candidate(self):
        value=self.complete();before=r.read_relative(self.output,'reproduction.json')
        with self.assertRaisesRegex(r.Error,'completion_destination_exists'):r.complete(self.output,self.run,self.repo)
        self.assertEqual(before,r.read_relative(self.output,'reproduction.json'))
        self.put(self.candidate,'build.json',b'new candidate source receipt')
        with self.constructor_gates(),self.assertRaises(r.Error):r.verify(self.output,self.repo)
    def test_completion_raw_difference_never_qualified_by_new_native_evidence(self):
        self.build_only();self.write_native(self.candidate)
        with self.constructor_gates(changed=True),self.assertRaises(r.Error):r.complete(self.output,self.run,self.repo)
        self.assertFalse((self.output/'reproduction.json').exists())
    def test_completion_original_error_and_failure_write_secondary_preserved(self):
        self.build_only();error=OSError(5,'actual portable failure')
        with self.constructor_gates(),patch.object(r.pairing_evidence,'verify_native_evidence',side_effect=error),\
             self.assertRaises(OSError)as result:r.complete(self.output,self.run,self.repo)
        self.assertIs(result.exception,error)
        failure=r.decode_json(next((self.output/'completion-failures').glob('*/failed.json')).read_bytes())
        self.assertEqual(failure['native_error'],{'domain':'POSIX','code':5})
        error2=r.Error('primary retained')
        with self.constructor_gates(),patch.object(r.pairing_evidence,'verify_native_evidence',side_effect=error2),\
             patch.object(r,'completion_failure',side_effect=OSError(28,'actual record write failure')),\
             self.assertRaises(r.Error)as result:r.complete(self.output,self.run,self.repo)
        self.assertIs(result.exception,error2);self.assertEqual(error2.reconstruction_record_error,{'type':'OSError','code':28})
    def test_completed_replay_rejects_rehashed_modified_construction_claim(self):
        value=self.complete();construction=r.decode_json(r.read_relative(self.output,'construction.json'))
        construction['reconstruction_complete']=True;self.put(self.output,'construction.json',r.encoded(construction))
        value['construction_ref']['sha256']=c.digest(r.encoded(construction));self.rewrite(value)
        with self.constructor_gates(),self.assertRaisesRegex(r.Error,'construction_claims'):r.verify(self.output,self.repo)
    def test_completion_cli_explicit_closed_mode_and_no_auto_launch(self):
        with contextlib.redirect_stderr(io.StringIO()):
            for argv in [['--output','x','--complete','--require-complete'],
              ['--output','x','--complete','--native-evidence','y','--require-complete','--artifact','z'],
              ['--output','x','--complete','--verify','--native-evidence','y','--require-complete']]:
                with self.subTest(argv=argv),self.assertRaises(SystemExit)as result:r.main(argv)
                self.assertEqual(result.exception.code,2)
        with patch.object(r,'complete',return_value={'scope':r.SCOPE,'outcome':{'reconstruction_complete':True}})as finish,\
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(r.main(['--output','x','--complete','--native-evidence','y','--require-complete']),0)
        finish.assert_called_once_with('x','y')


if __name__=='__main__':unittest.main(verbosity=2)
