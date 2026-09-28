"""Check harness trust boundaries and fixture construction without running candidates."""
import copy
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('manager_cases', HERE/'run_cases.py')
cases=importlib.util.module_from_spec(spec);spec.loader.exec_module(cases)


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.case=json.loads((HERE/'fixtures/cases.json').read_text())['cases'][0]
        self.valid={'experiment_version':1,'candidate':'rust','fixture_only':True,'runtime_eligible':False,'host_architecture':'arm64','translated':False,'classification':'success','spawned':True,'reaped':True,'cleanup':'passed','exit_code':0,'signal':None,'stdout_bytes':24,'stderr_bytes':0}

    def test_qualified_claim_cannot_pass(self):
        value={**self.valid,'runtime_eligible':True}
        self.assertIn('fixture_scope',cases.check_result(value,self.case,0))

    def test_static_arm_slice_does_not_replace_translation_observation(self):
        value={**self.valid,'translated':None}
        self.assertIn('native_host',cases.check_result(value,self.case,0))

    def test_unreaped_child_cannot_pass(self):
        value={**self.valid,'reaped':False}
        self.assertIn('lifecycle',cases.check_result(value,self.case,0))

    def test_unknown_result_field_is_rejected(self):
        self.assertIn('result_shape',cases.check_result({**self.valid,'private_path':'private'},self.case,0))

    def test_success_label_does_not_override_exit_status(self):
        self.assertIn('exit_status',cases.check_result(self.valid,self.case,4))

    def test_negative_case_cannot_execute(self):
        case={**self.case,'expected':'invalid_contract'}
        value={**self.valid,'classification':'invalid_contract'}
        self.assertIn('lifecycle',cases.check_result(value,case,1))


    def test_result_version_and_success_exit_are_checked(self):
        self.assertIn('result_version',cases.check_result({**self.valid,'experiment_version':True},self.case,0))
        self.assertIn('normal_exit_identity',cases.check_result({**self.valid,'exit_code':7},self.case,0))

    def test_deleted_source_invalidates_old_build(self):
        with tempfile.TemporaryDirectory() as temp:
            repo=Path(temp);experiment=repo/'experiments/manager';build=repo/'build'
            (experiment/'rust/src').mkdir(parents=True);(build/'bin').mkdir(parents=True)
            source=experiment/'rust/src/main.rs';source.write_text('// owned fixture')
            binaries={}
            for name in ['fixture-child','rust-manager','swift-manager']:
                (build/'bin'/name).write_bytes(b'never executed')
                binaries[name]={'sha256':cases.sha(b'never executed')}
            metadata={'fixture_only':True,'runtime_eligible':False,'binaries':binaries,'sources':{str(source.relative_to(repo)):cases.sha(source.read_bytes())}}
            (build/'build.json').write_text(json.dumps(metadata))
            with patch.object(cases,'REPO',repo),patch.object(cases,'EXPERIMENT',experiment):
                cases.verify_build(build)
                source.unlink()
                with self.assertRaisesRegex(ValueError,'source file set changed'):cases.verify_build(build)

    def test_corpus_has_unique_cases_and_explicit_reference_scope(self):
        corpus=json.loads((HERE/'fixtures/cases.json').read_text())
        self.assertEqual(len(corpus['cases']),len({c['id'] for c in corpus['cases']}))
        for case in corpus['cases']:
            self.assertIn(case['oracle'],['eligible','valid','invalid','ineligible'])
            self.assertIn(case['oracle_context'],['fixture','research'])
        expected={c['id'] for c in corpus['cases']}
        self.assertTrue({'descendant_pipe','state_symlink','research_context','untrusted_executable_digest','secret_redaction','missing_observer_ready','observer_gap'} <= expected)

    def test_fixture_archive_and_dag_bind_actual_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            top=Path(temp);build=top/'build';(build/'bin').mkdir(parents=True)
            (build/'bin/fixture-child').write_bytes(b'Owned inert unit fixture, never executed.')
            (build/'build.json').write_text(json.dumps({'toolchains':{'clang':'Apple clang version 21.0.0 (owned test)','sdk':'26.5'}}))
            roots=[top/'first',top/'second']
            for root in roots: cases.create_bundle(root,build,self.case)
            self.assertEqual((roots[0]/'blobs/source.tar').read_bytes(),(roots[1]/'blobs/source.tar').read_bytes())
            with tarfile.open(roots[0]/'blobs/source.tar') as archive:
                self.assertEqual(set(archive.getnames()),{'child.c','native_bridge.c','native_bridge.h'})
                self.assertTrue(all(m.uid==0 and m.gid==0 and m.mtime==0 for m in archive))
            root=roots[0]
            def references(node):
                if isinstance(node,dict):
                    if 'ref_type' in node:
                        self.assertEqual(cases.sha((root/node['path']).read_bytes()),node['digest']['value'])
                    else:
                        for value in node.values():references(value)
                elif isinstance(node,list):
                    for value in node:references(value)
            for path in (root/'records').glob('*.json'):references(json.loads(path.read_bytes()))
            self.assertEqual(len(list((root/'records').glob('*.json'))),4)

if __name__=='__main__':unittest.main()
