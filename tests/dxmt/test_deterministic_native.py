"""Portable distinct-kind/source/namespace/completion refusal controls."""
import ast
from contextlib import contextmanager
import copy
import io
from contextlib import redirect_stderr
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

REPO=Path(os.environ.get('PEAR_TEST_REPO',str(Path(__file__).resolve().parents[2])))
IMPLEMENTATION=Path(os.environ.get('PEAR_TEST_NATIVE_IMPLEMENTATION_ROOT',str(REPO/'tools/dxmt')))
CONSTRUCTOR=Path(os.environ.get('PEAR_TEST_IMPLEMENTATION_ROOT',str(REPO/'tools/dxmt')))
spec=importlib.util.spec_from_file_location('_private_native_scope_controls',IMPLEMENTATION/'deterministic_native.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
spec=importlib.util.spec_from_file_location('_private_reproduction_scope_controls',IMPLEMENTATION/'deterministic_reproduce.py')
reproduction=importlib.util.module_from_spec(spec);spec.loader.exec_module(reproduction)


class Temporary(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='pear-native-adapter-controls-',dir='/private/tmp')
        self.root=Path(self.temporary.name)
    def tearDown(self):self.temporary.cleanup()
    def write(self,path,raw,mode=0o644):
        target=self.root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);target.chmod(mode);return target
    @contextmanager
    def adapter(self):
        with native.adapter(REPO,CONSTRUCTOR)as value:yield value


class Derivation(Temporary):
    def test_literal_only_new_kind_and_scope(self):
        raw=b'def result():\n return {"record_kind":"dxmt_pairing_runtime", "scope":"finite_native_metal_pairing", "value":7}\n'
        namespace={};proof,_=native.selected_functions(raw,namespace,'source.py')
        value=namespace['result']()
        self.assertEqual(value,{'record_kind':'dxmt_deterministic_pairing_runtime','scope':'finite_deterministic_native_metal_pairing','value':7})
        self.assertEqual(proof['source_sha256'],native.digest(raw))
        self.assertNotEqual(proof['before_ast_sha256'],proof['after_ast_sha256'])
        self.assertEqual(proof['literal_changes']['dxmt_pairing_runtime']['count'],1)
    def test_unknown_literal_not_broadened(self):
        raw=b'def result():\n return "dxmt_pairing_unselected"\n'
        namespace={};proof,_=native.selected_functions(raw,namespace,'source.py')
        self.assertEqual(namespace['result'](),'dxmt_pairing_unselected');self.assertEqual(proof['literal_changes'],{})
    def test_original_protocol_literals_and_guards_remain(self):
        raw=b'def result(value):\n assert value is False\n return "pear_metal_pairing"\n'
        namespace={};proof,_=native.selected_functions(raw,namespace,'source.py')
        self.assertEqual(namespace['result'](False),'pear_metal_pairing')
        with self.assertRaises(AssertionError):namespace['result'](True)
        self.assertEqual(proof['before_ast_sha256'],proof['after_ast_sha256'])
    def test_async_or_absent_functions_refused(self):
        for raw in (b'async def x():\n pass\n',b'value=4\n'):
            with self.subTest(raw=raw),self.assertRaises(native.Error):native.selected_functions(raw,{},'source.py')
    def test_main_entrypoint_not_selected(self):
        raw=b'def main():\n raise AssertionError("must not run")\ndef result():\n return 1\n'
        namespace={};proof,_=native.selected_functions(raw,namespace,'source.py')
        self.assertNotIn('main',namespace);self.assertEqual(proof['functions'],['result'])


class Source(Temporary):
    def test_source_alias_and_parent_alias_refused(self):
        self.write('source/data.py',b'pass\n');(self.root/'alias').symlink_to('source',target_is_directory=True)
        (self.root/'source/link.py').symlink_to('data.py')
        for parent,leaf in ((self.root/'alias','data.py'),(self.root/'source','link.py')):
            with self.subTest(leaf=leaf),self.assertRaises(OSError):native.bounded_source(parent,leaf)
    def test_source_unsafe_name_and_size_refused(self):
        self.write('huge.py',b'x'*(2**20+1))
        for name in ('../data.py','a/b.py','','huge.py'):
            with self.subTest(name=name),self.assertRaises(native.Error):native.bounded_source(self.root,name)
    def test_changed_constructor_refused_before_source_execution(self):
        path=self.root/'constructor';path.mkdir()
        for leaf in ('deterministic_pair.py','deterministic_reuse.py','metal_stdin.py','deterministic_monitor.py','reuse-pins.json'):
            shutil.copyfile(CONSTRUCTOR/leaf,path/leaf)
        target=path/'deterministic_pair.py';target.write_bytes(target.read_bytes()+b'\nraise AssertionError("unreviewed execution")\n')
        with self.assertRaisesRegex(native.Error,'native_constructor_source_changed'):
            native.Adapter(REPO,path)
    def test_current_sources_and_derivation_are_separate(self):
        with self.adapter()as value:
            descriptor=value.descriptor('runtime')
            self.assertFalse(descriptor['source_gates']['original_records_accepted'])
            self.assertTrue(descriptor['source_gates']['fresh_39_case_native_execution_required'])
            self.assertEqual(descriptor['constructor_loading']['local_loader'],'closed_preverified_helper_bytes')
            self.assertIn('tools/dxmt/deterministic_native.py',descriptor['producers'])
            self.assertIn('tools/dxmt/pairing_runtime.py',descriptor['producers'])
            self.assertEqual(value.runtime.SCOPE,'development_finite_deterministic_native_metal_pairing')
            self.assertEqual(value.evidence.SCOPE,'finite_deterministic_native_metal_api_pairing')
    def test_unknown_action_descriptor_refused(self):
        with self.adapter()as value,self.assertRaises(native.Error):value.descriptor('game')
    def test_descriptor_bytes_changed_or_missing_refused(self):
        with self.adapter()as value:
            descriptor=value.descriptor('runtime');self.write('adapter.json',native.encoded(descriptor))
            value.descriptor_check(self.root,'runtime')
            descriptor['source_gates']['original_records_accepted']=True
            self.write('adapter.json',native.encoded(descriptor))
            with self.assertRaises(native.Error):value.descriptor_check(self.root,'runtime')
            (self.root/'adapter.json').unlink()
            with self.assertRaises(OSError):value.descriptor_check(self.root,'runtime')
    def test_real_aliases_unchanged_inside_original_wine_supervisor_context(self):
        names=('common','prepare','toolchain','modules','abi_review','dynamic_evidence','exception_evidence','run_fixtures','api_runner')
        sentinels={name:object()for name in names}
        with mock.patch.dict(sys.modules,sentinels):
            with self.adapter()as value:
                with value.runner.wine_helpers(value.repo,value.producers())as helper:
                    for name,original in sentinels.items():self.assertIs(sys.modules[name],original)
                    self.assertTrue(callable(helper.assess_native))
                for name,original in sentinels.items():self.assertIs(sys.modules[name],original)
            self.assertFalse(any(key.startswith(value.capture.name+'.')for key in sys.modules))
    def test_reused_reader_rejects_old_runtime_record_kind_before_prerequisite(self):
        with self.adapter()as value:
            record={key:None for key in value.runtime.RUNTIME_FIELDS}
            record.update(schema_version=1,record_kind='dxmt_pairing_runtime',runtime_eligible=False,game_qualified=False)
            self.write('adapter.json',native.encoded(value.descriptor('runtime')));self.write('runtime.json',native.encoded(record))
            # This only replaces owned-path admission for a portable data-only
            # control. The exact derived field/kind body still executes.
            value.runtime.namespace['owned_directory']=lambda root,repo:Path(root)
            with self.assertRaises(Exception)as error:value.structural(self.root)
            self.assertEqual(getattr(error.exception,'code',None),'unexpected_record_kind')
    def test_original_39_cases_and_metal_validation_settings_preserved(self):
        with self.adapter()as value:
            self.assertEqual(len(value.runner.CASES),39)
            self.assertEqual(value.runner.METAL_ENV['MTL_DEBUG_LAYER_ERROR_MODE'],'assert')
            self.assertEqual(value.runner.METAL_ENV['MTL_SHADER_VALIDATION_REPORT_TO_STDERR'],'1')
            self.assertEqual(value.runner.BOUNDS,{'grace_ms':3000,'terminate_ms':2000,'kill_ms':5000,'drain_ms':1000})


class NativeBinding(Temporary):
    def state(self,run_kind=None,runtime_kind=None,bound=None):
        candidate={'path':str(self.root/'candidate'),'sha256':'a'*64}
        runtime={'record_kind':runtime_kind or native.KIND_MAP['dxmt_pairing_runtime'],'build_ref':bound or candidate}
        runtime_root=self.root/'runtime';runtime_root.mkdir();raw=native.encoded(runtime);(runtime_root/'runtime.json').write_bytes(raw)
        run={'record_kind':run_kind or native.KIND_MAP['dxmt_pairing_run'],
             'runtime_ref':{'path':str(runtime_root),'sha256':native.digest(raw)}}
        run_root=self.root/'run';run_root.mkdir();(run_root/'run.json').write_bytes(native.encoded(run));(run_root/'diagnostics-review.json').write_bytes(b'{}\n')
        observed={'record_kind':native.KIND_MAP['dxmt_pairing_native_evidence'],
             'scope':native.SCOPE_MAP['finite_native_metal_api_pairing'],
             'finite_native_scope_complete':True,'metal_api_validation':'reviewed_no_errors',
             'native_pairing_observed':True,'ordinary_arm64_pe_execution_performed':True,
             'runtime_eligible':False,'game_qualified':False,'distribution_qualified':False,
             **{key:'unperformed'for key in ('shader_workload','general_renderer','performance',
                'hybrid_execution','translated_guest_execution','game_qualification','distribution_qualification')}}
        common=SimpleNamespace(owned_directory=lambda path,repo:Path(path),
            read_relative=lambda root,path,limit=8*1024**2:(Path(root)/path).read_bytes(),decode_json=json.loads)
        # Mocked typed provenance boundaries never stand in for a real execution
        # or grant review; only the independent final-candidate binding is tested.
        return candidate,run_root,SimpleNamespace(repo=self.root,common=common,verify_evidence=lambda root:observed)
    def test_old_run_kind_refused(self):
        candidate,root,adapter=self.state(run_kind='dxmt_pairing_run')
        with self.assertRaisesRegex(reproduction.Error,'old_native_run_refused'):reproduction.native_binding(root,candidate,adapter)
    def test_old_runtime_kind_refused(self):
        candidate,root,adapter=self.state(runtime_kind='dxmt_pairing_runtime')
        with self.assertRaisesRegex(reproduction.Error,'old_native_runtime_refused'):reproduction.native_binding(root,candidate,adapter)
    def test_reference_success_cannot_substitute_for_fresh_candidate(self):
        candidate,root,adapter=self.state(bound={'path':str(self.root/'reference'),'sha256':'a'*64})
        with self.assertRaisesRegex(reproduction.Error,'fresh_candidate_native_required'):reproduction.native_binding(root,candidate,adapter)
    def test_changed_candidate_digest_refused_even_same_path(self):
        candidate,root,adapter=self.state();candidate['sha256']='b'*64
        with self.assertRaisesRegex(reproduction.Error,'fresh_candidate_native_required'):reproduction.native_binding(root,candidate,adapter)
    def test_only_exact_new_candidate_binding_emits_final_origin(self):
        candidate,root,adapter=self.state();value=reproduction.native_binding(root,candidate,adapter)
        self.assertEqual(value['origin'],'fresh_final_candidate');self.assertTrue(value['new_native_execution_performed'])
        self.assertEqual(value['permission_transfer'],'not_inferred')
    def test_missing_review_payload_is_not_native_success(self):
        candidate,root,adapter=self.state();(root/'diagnostics-review.json').unlink()
        with self.assertRaises(OSError):reproduction.native_binding(root,candidate,adapter)
    def test_changed_runtime_bytes_refused(self):
        candidate,root,adapter=self.state();(self.root/'runtime/runtime.json').write_bytes(b'{}\n')
        with self.assertRaisesRegex(reproduction.Error,'native_runtime_changed'):reproduction.native_binding(root,candidate,adapter)
    def test_wrong_evidence_kind_or_scope_or_promoted_workload_refused(self):
        for change in ({'record_kind':'dxmt_pairing_native_evidence'},{'scope':'renderer'},
                       {'shader_workload':'performed'},{'runtime_eligible':True}):
            with self.subTest(change=change):
                # Each mock receipt is data-only, never native qualification.
                child=self.root/('case'+str(len(list(self.root.iterdir()))));child.mkdir()
                previous=self.root;self.root=child
                try:candidate,root,adapter=self.state()
                finally:self.root=previous
                original=adapter.verify_evidence;adapter.verify_evidence=lambda root:dict(original(root),**change)
                with self.assertRaisesRegex(reproduction.Error,'native_scope'):
                    reproduction.native_binding(root,candidate,adapter)
    def test_changed_run_during_evidence_replay_refused(self):
        candidate,root,adapter=self.state();original=adapter.verify_evidence
        def change(path):
            observed=original(path);(root/'run.json').write_bytes(b'{}\n');return observed
        adapter.verify_evidence=change
        with self.assertRaisesRegex(reproduction.Error,'native_changed'):reproduction.native_binding(root,candidate,adapter)
    def test_incomplete_finite_evidence_refused(self):
        candidate,root,adapter=self.state();original=adapter.verify_evidence;adapter.verify_evidence=lambda root:dict(original(root),finite_native_scope_complete=False)
        with self.assertRaisesRegex(reproduction.Error,'native_scope'):reproduction.native_binding(root,candidate,adapter)





class CoordinatorRepairs(Temporary):
    def copied_coordinator(self):
        path=self.root/'helper';path.mkdir()
        for leaf in ['deterministic_native.py','deterministic_reproduce.py','native-pins.json','constructor-pins.json']:
            shutil.copyfile(IMPLEMENTATION/leaf,path/leaf)
        def load():
            spec=importlib.util.spec_from_file_location('_copied_native_coordinator',path/'deterministic_reproduce.py')
            value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
        return path,load
    def test_exact_helper_captured_before_execution(self):
        path,load=self.copied_coordinator();value=load()
        self.assertEqual(value.NATIVE_SOURCE,(path/'deterministic_native.py').read_bytes())
        self.assertEqual(value.native.digest(value.NATIVE_SOURCE),value.NATIVE_SOURCE_PIN)
        with value.native_adapter(REPO,CONSTRUCTOR)as adapter:
            self.assertEqual(adapter.descriptor('runtime')['native_loading']['source_sha256'],value.NATIVE_SOURCE_PIN)
    def test_changed_helper_after_execution_cannot_be_current_producer(self):
        path,load=self.copied_coordinator();value=load();target=path/'deterministic_native.py'
        target.write_bytes(target.read_bytes()+b'\n')
        with self.assertRaisesRegex(value.native.Error,'native_executed_source_changed'):
            with value.native_adapter(REPO,CONSTRUCTOR):self.fail('changed executed source admitted')
    def test_changed_helper_before_execution_refused(self):
        path,load=self.copied_coordinator();target=path/'deterministic_native.py';target.write_bytes(target.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError,'native_loader_source_changed'):load()
    def test_helper_alias_refused_before_execution(self):
        path,load=self.copied_coordinator();target=path/'deterministic_native.py';target.rename(path/'original.py');target.symlink_to('original.py')
        with self.assertRaises(OSError):load()
    def test_wrong_explicit_executed_digest_refused(self):
        with self.assertRaisesRegex(native.Error,'native_executed_source_changed'):
            native.Adapter(REPO,CONSTRUCTOR,executed_native_sha='0'*64)
    def constructor_fixture(self):
        common=SimpleNamespace(output_directory=lambda path,repo:self.mkdir(path),
            write_new=lambda path,value:Path(path).write_bytes(native.encoded(value)),
            read_relative=lambda root,name,limit=8*1024**2:(Path(root)/name).read_bytes())
        return SimpleNamespace(output=str(self.root/'output')),SimpleNamespace(common=common,repo=self.root)
    def mkdir(self,path):
        value=Path(path);value.mkdir();return value
    def test_source_capture_errno_produces_failure_before_recipe(self):
        args,adapter=self.constructor_fixture();primary=OSError(5,'source failure')
        with mock.patch.object(reproduction,'sources',side_effect=primary),self.assertRaises(OSError)as caught:
            reproduction.constructor(args,adapter)
        self.assertIs(caught.exception,primary)
        value=json.loads((self.root/'output/failed.json').read_bytes())
        self.assertEqual(value['phase'],'source_capture');self.assertEqual(value['producers'],{})
        self.assertEqual(value['native_error'],{'domain':'POSIX','code':5});self.assertFalse(value['reconstruction_complete'])
        self.assertFalse((self.root/'output/construction.json').exists())
    def test_source_failure_evidence_secondary_cannot_replace_primary(self):
        args,adapter=self.constructor_fixture();primary=OSError(5,'source failure')
        adapter.common.write_new=mock.Mock(side_effect=OSError(28,'secondary'))
        with mock.patch.object(reproduction,'sources',side_effect=primary),self.assertRaises(OSError)as caught:
            reproduction.constructor(args,adapter)
        self.assertIs(caught.exception,primary);self.assertEqual(primary.evidence_error['code'],28)
    def test_cli_retains_actual_posix_and_attached_native_errors(self):
        for primary,expected in [(OSError(13,'source'),{'domain':'POSIX','code':13}),
                (reproduction.Error('admission_primary'),{'domain':'POSIX','code':5})]:
            if not isinstance(primary,OSError):primary.native_error=expected
            stderr=io.StringIO()
            with mock.patch.object(reproduction,'native_adapter',side_effect=primary),redirect_stderr(stderr):
                status=reproduction.main(['--repo',str(REPO),'--constructor-root',str(CONSTRUCTOR),
                    '--verify','--output',str(self.root)])
            self.assertEqual(status,1);value=json.loads(stderr.getvalue())
            self.assertEqual(value['native_error'],expected);self.assertFalse(value['reconstruction_complete'])
    def test_source_signature_includes_actual_fixed_flag(self):
        old=SimpleNamespace(source_signature=lambda value:'old')
        adapter=SimpleNamespace(capture=SimpleNamespace(load=lambda path:old))
        value={'recipe_policy':{'schema_version':2,'source_date_epoch':'0',
            'stable_wine_objects':'/pear/reconstruction/wine/objects',
            'debug_compilation_directory_flag':'-fdebug-compilation-dir=/pear/reconstruction/wine/objects',
            'source_interface':'stdin_exact_original_bytes','shader_options':{},'shader_inputs':{},
            'normalization':'none','raw_product_comparison_required':True,'fresh_native_evidence_required':True},
            'qualification_ref':{},'constructor_sources':{}}
        first=reproduction.source_signature(value,adapter)
        value['recipe_policy']['debug_compilation_directory_flag']='altered'
        self.assertNotEqual(first,reproduction.source_signature(value,adapter))


class ReviewContextJSON(unittest.TestCase):
    def test_sets_export_as_sorted_lists_without_mutating_raw_review(self):
        context={'notice_pids':{'loader':{32,8},'server':{10}},'run_ref':{'sha256':'a'*64}}
        result=native.review_context_json(context)
        self.assertEqual(json.loads(native.encoded(result))['notice_pids'],{'loader':[8,32],'server':[10]})
        self.assertEqual(context['notice_pids']['loader'],{8,32})
        self.assertIs(result['run_ref'],context['run_ref'])
    def test_malformed_process_identity_refused(self):
        for value in (None,{}, {'loader':[]}, {'loader':set()}, {'loader':{True}},
                      {'loader':{0}}, {'loader':{2**31}}, {4:{10}}):
            with self.subTest(value=value),self.assertRaises(native.Error):
                native.review_context_json({'notice_pids':value})
    def test_unknown_set_is_not_generically_coerced(self):
        value=native.review_context_json({'notice_pids':{'loader':{10}},'unexpected':{1}})
        with self.assertRaises(TypeError):native.encoded(value)
    def test_cli_outputs_actual_context_shape(self):
        context={'notice_pids':{'loader':{32,8}},'run_ref':{'sha256':'b'*64}}
        @contextmanager
        def fake_adapter(*args):yield SimpleNamespace(review_context=lambda root:(context,{}))
        output=io.StringIO()
        with mock.patch.object(native,'adapter',fake_adapter),mock.patch('sys.stdout',output):
            status=native.main(['--repo',str(REPO),'--constructor-root',str(CONSTRUCTOR),
                                '--review-context','--run-root','owned-run'])
        self.assertEqual(status,0)
        self.assertEqual(json.loads(output.getvalue())['notice_pids']['loader'],[8,32])
        self.assertEqual(context['notice_pids']['loader'],{8,32})


if __name__=='__main__':unittest.main()
