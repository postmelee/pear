# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Portable current-input refusals using synthetic bytes and fake admission only."""
from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pear_runtime import build
from pear_runtime.errors import Error, need
from pear_runtime.fixtures.admission import prefix_inventory
from tools.development.game import context as g


class Captured:
    def __init__(self,root):
        self.roots={'pear':root};self.logical_bytes=123
        p=root/'producer.py';p.write_text('# synthetic producer\n');self.ref=build.fact(p)
        self.refs={('pear','producer.py'):self.ref}
    def recheck(self):need(build.fact(self.ref['path'])==self.ref,'synthetic_source_changed')
    def preserve(self,output):
        self.recheck();p=output/'producer-sources';p.mkdir();target=p/'source.py'
        target.write_bytes(Path(self.ref['path']).read_bytes())
        rows=[dict(original=self.ref,snapshot=build.fact(target))]
        (output/'producers.json').write_text(json.dumps(rows));return rows


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        for name in ('game','seed','runtime','provider','metadata','output','sources','helpers'):(self.root/name).mkdir()
        game=self.root/'game';files=[];rows=[]
        names=['Megabonk.exe','GameAssembly.dll']+[f'data/f{i:02d}.bin' for i in range(67)]
        for i,name in enumerate(names):
            p=game/name;p.parent.mkdir(exist_ok=True);p.write_bytes(b'synthetic '+str(i).encode())
            files.append(dict(relative=name,ref=build.fact(p)))
            rows.append(dict(path=name,size=p.stat().st_size,sha1=hashlib.sha1(p.read_bytes()).hexdigest(),flags=0))
        self.snapshot=dict(app_id=3405340,platforms={'windows':[{'files':rows}]})
        prefix=self.root/'seed/run/prefix';(prefix/'drive_c/windows/system32').mkdir(parents=True)
        (prefix/'.update-timestamp').write_text('7')
        modules={}
        for name in ('ntdll.dll','xtajit64.dll'):
            prior=prefix/'drive_c/windows/system32'/name;prior.write_bytes(b'seed '+name.encode())
            selected=self.root/'runtime'/name;selected.write_bytes(b'new '+name.encode())
            modules[name]=dict(seed_sha256=build.fact(prior)['sha256'],selected_ref=build.fact(selected))
        def record(path,value):path.write_text(json.dumps(value));return build.fact(path)
        self.record=record
        refs={name:record(self.root/'metadata'/(name+'.json'),{'synthetic':name,'phase_seconds':0.25})
              for name in g.REF_FIELDS}
        refs['runtime_ref']=record(self.root/'runtime/runtime.json',{'passed':True,'phase_seconds':0.25})
        refs['seed_ref']=record(self.root/'seed/case.json',{'synthetic':'seed'})
        refs['snapshot_ref']=record(self.root/'metadata/snapshot.json',self.snapshot)
        helpers={}
        for name in (*g.FIXED_HELPERS,'python'):
            p=self.root/'helpers'/name;p.write_bytes(name.encode());helpers[name]=build.fact(p)
        self.stack.enter_context(patch.object(g,'FIXED_HELPERS',{k:v['path'] for k,v in helpers.items() if k!='python'}))
        self.stack.enter_context(patch.object(g.sys,'executable',helpers['python']['path']))
        self.value=dict(schema_version=1,scope='owned_game_development_inputs',candidate='d25-game',**refs,
            provider_root=str(self.root/'provider'),seed_root=str(self.root/'seed'),seed_inventory=prefix_inventory(prefix),
            modules=modules,output_root=str(self.root/'output'),game_root=str(game),game_files=files,
            helper_refs=helpers,manual_policy='manual_feedback_v1')
        self.path=self.root/'metadata/context.json';self.ref=record(self.path,self.value)
        self.captured=Captured(self.root/'sources')
        self.stack.enter_context(patch.object(g,'_capture',return_value=self.captured))
        self.stack.enter_context(patch.object(g.supervision,'source_refs',return_value={'provider':refs['profile_ref']}))
        self.stack.enter_context(patch.object(g.supervision,'provenance_ref',return_value=refs['producer_manifest_ref']))
        self.admission=self.stack.enter_context(patch.object(g.game_operation,'admit_candidate',
            return_value=(self.root/'runtime',{'passed':True,'phase_seconds':0.25},{'attach_observer':True})))
        self.disk=self.stack.enter_context(patch.object(g.shutil,'disk_usage',return_value=SimpleNamespace(free=64*1024**3)))
        self.stack.enter_context(patch.object(g.game_prerequisites,'admit',return_value={'passed':True}))
        self.output=self.root/'output/run'

    def context(self):return g.GameContext(self.ref)
    def reseal(self):self.ref=self.record(self.path,self.value)
    def active(self,ctx=None):
        ctx=ctx or self.context();op=object.__new__(g.game_operation.GameOperation)
        op.context=ctx;op.operation_id='synthetic-operation';op.output=self.output
        def current(owner,output,ident):
            need(owner is op and owner.context is ctx and owner.output==Path(output) and
                 owner.operation_id==ident and not getattr(owner,'released',False),'synthetic_operation_changed')
        self.stack.enter_context(patch.object(g.game_operation.GameOperation,'assert_current',current))
        ctx.begin_game(self.output,operation=op);self.output.mkdir();return ctx,op
    def copied(self):
        ctx,op=self.active()
        def fake_copy(argv,*,check,timeout):
            self.assertEqual(argv[:2],['/bin/cp','-c']);self.assertIs(check,True);self.assertEqual(timeout,30)
            Path(argv[3]).write_bytes(Path(argv[2]).read_bytes())
        with patch('subprocess.run',side_effect=fake_copy) as cp:prepared=ctx.prepare_game(self.output)
        self.assertEqual(cp.call_count,69);return ctx,op,prepared

    def test_inspection_uses_explicit_inputs_and_never_creates_output(self):
        ctx=self.context();result=ctx.inspect(self.output)
        self.assertEqual(result['status'],'input_admitted');self.assertEqual(result['game_inputs']['file_count'],69)
        self.assertFalse(result['execution_authorized_by_this_record']);self.assertFalse(result['game_execution_performed'])
        self.assertFalse(result['current_authority_assessed']);self.assertFalse(self.output.exists());self.assertIsNone(ctx.operation)
        self.assertFalse(result['storage']['apfs_clone_savings_assumed']);self.assertEqual(result['storage']['reserve_bytes'],6*1024**3)

    def test_closed_shape_and_unknown_candidate_refuse_before_admission(self):
        for field,value in (('candidate','other'),('schema_version',True),('scope','other'),('manual_policy','automatic'),('extra',False)):
            with self.subTest(field=field):
                changed=deepcopy(self.value);changed[field]=value;ref=self.record(self.path,changed)
                with self.assertRaisesRegex(Error,'game_context_shape'):g.GameContext(ref)
        self.admission.assert_not_called()

    def test_descriptor_replace_even_when_instance_ref_resealed_refuses(self):
        ctx=self.context();self.value['manual_policy']='changed';self.reseal();ctx.ref=self.ref
        with self.assertRaisesRegex(Error,'game_context_changed'):ctx.inspect(self.output)

    def test_runtime_and_selected_module_byte_changes_refuse(self):
        for row in (self.value['runtime_ref'],self.value['modules']['xtajit64.dll']['selected_ref']):
            with self.subTest(path=row['path']):
                ctx=self.context();p=Path(row['path']);raw=p.read_bytes();p.write_bytes(b'changed')
                with self.assertRaisesRegex(Error,'d24_input_changed'):ctx.inspect(self.output)
                p.write_bytes(raw)

    def test_independent_candidate_or_closure_refusal_propagates(self):
        ctx=self.context();self.admission.side_effect=Error('independent_code_or_architecture_refusal')
        with self.assertRaisesRegex(Error,'independent_code_or_architecture_refusal'):ctx.inspect(self.output)

    def test_game_byte_change_refuses(self):
        ctx=self.context();Path(self.value['game_files'][0]['ref']['path']).write_bytes(b'changed')
        with self.assertRaisesRegex(Error,'d24_input_changed'):ctx.inspect(self.output)

    def test_resealed_sha256_cannot_replace_independent_snapshot_sha1(self):
        p=Path(self.value['game_files'][0]['ref']['path']);p.write_bytes(b'x'*p.stat().st_size)
        self.value['game_files'][0]['ref']=build.fact(p);self.reseal()
        with self.assertRaisesRegex(Error,'d24_game_manifest'):self.context().inspect(self.output)

    def test_snapshot_mutation_refuses(self):
        ctx=self.context();Path(self.value['snapshot_ref']['path']).write_text('{}')
        with self.assertRaisesRegex(Error,'d24_input_changed'):ctx.inspect(self.output)

    def test_wrong_app_snapshot_order_and_file_set_refuse(self):
        for mode in ('app','order','missing','extra'):
            with self.subTest(mode=mode):
                snapshot=deepcopy(self.snapshot)
                if mode=='app':snapshot['app_id']=1
                elif mode=='order':snapshot['platforms']['windows'][0]['files'].reverse()
                elif mode=='missing':snapshot['platforms']['windows'][0]['files'].pop()
                else:snapshot['platforms']['windows'][0]['files'].append(dict(snapshot['platforms']['windows'][0]['files'][0]))
                self.value['snapshot_ref']=self.record(self.root/'metadata/snapshot.json',snapshot);self.reseal()
                with self.assertRaises(Error):self.context().inspect(self.output)

    def test_manifest_count_duplicate_unknown_and_unsafe_paths_refuse(self):
        base=deepcopy(self.value)
        for mode in ('missing','extra','duplicate','parent','absolute','dot','backslash'):
            with self.subTest(mode=mode):
                self.value=deepcopy(base)
                if mode=='missing':self.value['game_files'].pop()
                elif mode=='extra':self.value['game_files'].append(deepcopy(self.value['game_files'][0]))
                elif mode=='duplicate':self.value['game_files'][-1]=deepcopy(self.value['game_files'][0])
                else:self.value['game_files'][0]['relative']={'parent':'../x','absolute':'/x','dot':'a/./b','backslash':'a\\b'}[mode]
                self.reseal()
                with self.assertRaises(Error):self.context()

    def test_leaf_and_ancestor_aliases_refuse(self):
        p=Path(self.value['game_files'][0]['ref']['path']);target=p.with_suffix('.real');p.rename(target);p.symlink_to(target.name)
        with self.assertRaisesRegex(Error,'game_reference_alias'):self.context()
        p.unlink();target.rename(p)
        alias=self.root/'alias';alias.symlink_to(self.root/'game',target_is_directory=True)
        self.value['game_root']=str(alias)
        for row in self.value['game_files']:row['ref']['path']=str(alias/row['relative'])
        self.reseal()
        with self.assertRaisesRegex(Error,'game_root_alias'):self.context()

    def test_seed_extra_file_and_timestamp_mutation_refuse(self):
        for name in ('extra','.update-timestamp'):
            with self.subTest(name=name):
                ctx=self.context();p=self.root/'seed/run/prefix'/name;raw=p.read_bytes() if p.exists() else None;p.write_bytes(b'changed')
                with self.assertRaisesRegex(Error,'d24_seed_changed'):ctx.inspect(self.output)
                if raw is None:p.unlink()
                else:p.write_bytes(raw)

    def test_output_alias_overlap_and_reuse_refuse(self):
        ctx=self.context();self.output.mkdir()
        with self.assertRaisesRegex(Error,'game_fresh_output'):ctx.inspect(self.output)
        self.output.rmdir();self.output.symlink_to(self.root/'game',target_is_directory=True)
        with self.assertRaisesRegex(Error,'game_fresh_output'):ctx.inspect(self.output)
        self.value['output_root']=self.value['game_root'];self.reseal()
        with self.assertRaisesRegex(Error,'game_output_overlap'):self.context()

    def test_changed_source_is_not_silently_accepted(self):
        ctx=self.context();p=Path(self.captured.ref['path']);p.write_bytes(b'changed')
        with self.assertRaisesRegex(Error,'synthetic_source_changed'):ctx.inspect(self.output)

    def test_game_source_mutate_and_restore_refuses_same_context(self):
        ctx=self.context();ctx.inspect(self.output);p=Path(self.value['game_files'][0]['ref']['path']);raw=p.read_bytes()
        p.write_bytes(b'changed');p.write_bytes(raw)
        with self.assertRaisesRegex(Error,'d24_input_changed_during_check'):ctx.inspect(self.output)

    def test_capacity_requires_full_logical_peak_plus_six_gib_reserve(self):
        ctx=self.context();budget=ctx.storage_admission(self.output)
        self.disk.return_value=SimpleNamespace(free=budget['required_free_bytes']-1)
        with self.assertRaisesRegex(Error,'game_storage_capacity'):ctx.inspect(self.output)

    def test_foreign_structural_operation_is_not_authority(self):
        ctx=self.context();fake=SimpleNamespace(context=ctx,assert_current=lambda *a:None,operation_id='x')
        with self.assertRaisesRegex(Error,'game_context_operation'):ctx.begin_game(self.output,operation=fake)
        with self.assertRaisesRegex(Error,'game_context_operation'):ctx.prepare_game(self.output)

    def test_released_wrong_output_and_reused_context_refuse(self):
        ctx,op=self.active()
        with self.assertRaisesRegex(Error,'game_context_single_run'):ctx.begin_game(self.output,operation=op)
        with self.assertRaisesRegex(Error,'game_context_output'):ctx.prepare_game(self.root/'output/other')
        op.released=True
        with self.assertRaisesRegex(Error,'synthetic_operation_changed'):ctx.prepare_game(self.output)

    def test_synthetic_copy_preserves_exact_order_bytes_and_target(self):
        ctx,op,prepared=self.copied()
        self.assertEqual(prepared.source_files,[r['ref'] for r in self.value['game_files']])
        self.assertEqual(prepared.game_root,self.output/'game');ctx._check_prepared()
        self.assertFalse((self.output/'run').exists())

    def test_mutated_prepared_target_or_extra_file_refuses(self):
        ctx,op,prepared=self.copied();original=prepared.target['sha256'];prepared.target['sha256']='0'*64
        with self.assertRaisesRegex(Error,'game_prepared_changed'):ctx._check_prepared()
        prepared.target['sha256']=original;(prepared.game_root/'extra').write_bytes(b'x')
        with self.assertRaisesRegex(Error,'game_prepared_inventory'):ctx._check_prepared()

    def test_copy_rechecks_original_and_result_before_return(self):
        ctx,op=self.active()
        def corrupt(argv,**kwargs):Path(argv[3]).write_bytes(b'corrupt')
        with patch('subprocess.run',side_effect=corrupt):
            with self.assertRaisesRegex(Error,'game_clone_changed'):ctx.prepare_game(self.output)

    def test_original_copy_cannot_run_outside_live_lease(self):
        ctx=self.context()
        with patch.object(g.inputs,'game_copy') as copy:
            with self.assertRaisesRegex(Error,'game_context_operation'):ctx.prepare_game(self.output)
            copy.assert_not_called()

    def test_baseline_and_finalization_join_same_live_context(self):
        ctx,op,prepared=self.copied();ctx.preserve_sources(self.output);ctx.baseline(self.output/'baseline.log')
        baseline=json.loads((self.output/'baseline.log').read_text());self.assertEqual(baseline['game_context_ref'],self.ref)
        ctx.finish();value=ctx.finalize_assessment(self.output)
        self.assertTrue(value['passed']);self.assertFalse(value['game_qualified'])
        with self.assertRaisesRegex(Error,'game_finalization_state'):ctx.finalize_assessment(self.output)

    def test_missing_or_changed_source_snapshot_prevents_final_pass(self):
        ctx,op,prepared=self.copied();ctx.preserve_sources(self.output);ctx.finish()
        (self.output/'producer-sources/source.py').write_bytes(b'changed')
        with self.assertRaisesRegex(Error,'assembly_reference_changed'):ctx.finalize_assessment(self.output)

    def test_final_original_restore_still_refuses(self):
        ctx,op,prepared=self.copied();ctx.preserve_sources(self.output);ctx.finish()
        p=Path(self.value['game_files'][0]['ref']['path']);raw=p.read_bytes();p.write_bytes(b'x');p.write_bytes(raw)
        with self.assertRaisesRegex(Error,'game_input_changed_after_finish'):ctx.finalize_assessment(self.output)

    def test_helper_role_path_or_bytes_cannot_be_substituted(self):
        self.value['helper_refs']['extra']=deepcopy(self.value['helper_refs']['copy']);self.reseal()
        with self.assertRaisesRegex(Error,'game_helper_set'):self.context()
        self.value['helper_refs'].pop('extra');self.value['helper_refs']['copy']=deepcopy(self.value['helper_refs']['python']);self.reseal()
        with self.assertRaisesRegex(Error,'game_helper_binding'):self.context()

    def test_boolean_size_is_not_integer_identity(self):
        self.value['game_files'][0]['ref']['size_bytes']=True;self.reseal()
        with self.assertRaisesRegex(Error,'game_reference_shape'):self.context()

    def test_prelaunch_recheck_refuses_changed_nontarget_copied_file(self):
        ctx,op,prepared=self.copied();p=prepared.game_root/'data/f00.bin';p.write_bytes(b'changed')
        with self.assertRaisesRegex(Error,'game_prepared_file_changed'):ctx.recheck_prepared(self.output)

    def test_prelaunch_recheck_refuses_original_change_after_authority_phase(self):
        ctx,op,prepared=self.copied();p=Path(self.value['game_files'][10]['ref']['path']);p.write_bytes(b'changed')
        with self.assertRaisesRegex(Error,'d24_input_changed'):ctx.recheck_prepared(self.output)

    def test_capacity_drop_before_copy_refuses_without_copying(self):
        ctx,op=self.active();self.disk.return_value=SimpleNamespace(free=6*1024**3)
        with patch.object(g.inputs,'game_copy') as copy:
            with self.assertRaisesRegex(Error,'game_storage_capacity'):ctx.prepare_game(self.output)
            copy.assert_not_called()


if __name__=='__main__':unittest.main()
