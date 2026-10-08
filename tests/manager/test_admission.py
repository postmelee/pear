"""Native/oracle differential cases; synthetic acceptance never grants execution."""
import copy
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from support import REPO, experiment_build
sys.path.insert(0,str(REPO/'tests/contracts'))
import validate as oracle_v1
import validate_v2 as oracle_v2
from fixture_factory import build_fixture,encoded,rewrite
from test_eligibility import synthetic_candidate
from v2_fixture import upgrade_fixture

BUILD=REPO/os.environ.get('PEAR_MANAGER_BUILD','.build/task9/stage2')
BINARY=BUILD/'bin/pear-manager'

def native(root,entry,*,context='research',purpose='inspect',policy=None):
    with tempfile.TemporaryDirectory() as temp:
        policy_path=Path(temp).resolve()/'policy.json'
        args=[str(BINARY),'evaluate','--bundle-root',str(root),'--entry',entry,'--context',context,'--purpose',purpose]
        if policy is not None:
            policy_path.write_bytes(encoded(policy));args+=['--policy',str(policy_path)]
        if '\0' in entry:
            # argv cannot represent NUL; the native CLI itself cannot receive it.
            return {'record_valid':False,'eligible':False,'outcome_codes':['invalid_path'],'evaluation_only':True}
        result=subprocess.run(args,capture_output=True,timeout=15)
        if result.returncode not in (0,1,3): raise AssertionError((result.returncode,result.stderr))
        if len(result.stdout)>8192 or result.stderr: raise AssertionError('unbounded/private diagnostic')
        message=json.loads(result.stdout)
        if str(root).encode() in result.stdout: raise AssertionError('private root leaked')
        return message

class AdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        receipt=json.loads((BUILD/'build.json').read_bytes())
        if experiment_build.digest(BINARY)!=receipt['binaries']['pear-manager']['sha256']: raise AssertionError('build receipt mismatch')
    def test_runtime_execution_refuses_synthetic_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();bundle=root/'bundle';fixture=upgrade_fixture(bundle,synthetic_candidate(bundle));state=root/'state';state.mkdir(mode=0o700)
            policy=root/'policy';policy.write_bytes(encoded(fixture['policy']))
            result=subprocess.run([str(BINARY),'activate','--bundle-root',str(bundle),'--entry',fixture['paths']['request'],'--context','runtime','--state-root',str(state),'--policy',str(policy)],capture_output=True,timeout=10)
            self.assertEqual(result.returncode,3,result.stdout);self.assertIn(b'runtime_authorization_unavailable',result.stdout);self.assertEqual(list(state.iterdir()),[])
    def test_generic_ids_families_entries_and_versions(self):
        for version in (1,2):
            with self.subTest(version=version),tempfile.TemporaryDirectory() as temp:
                root=Path(temp).resolve();f=build_fixture(root)
                rewrite(root,f,'lock',lambda v:v['compatibility_family'].update(value='independent-family'))
                rewrite(root,f,'artifact',lambda v:v.update(compatibility_family='independent-family'))
                rewrite(root,f,'profile',lambda v:v.update(compatibility_family='independent-family'))
                rewrite(root,f,'request',lambda v:v.update(prefix_family='independent-family'))
                if version==2:upgrade_fixture(root,f)
                self.assertTrue(native(root,f['paths']['request'],context='fixture',purpose='fixture_launch',policy=f['policy'])['eligible'])

    def test_schema_boundary_values_match_oracle(self):
        mutations=[('lock',lambda v:v['components'][0]['source'].update(url='http://unsafe.invalid'),False),
                   ('lock',lambda v:v['components'][0]['source'].update(reason=''),True),
                   ('lock',lambda v:v['components'][0]['source'].update(status='unknown',reason=''),False),
                   ('lock',lambda v:v['toolchains'][0].update(sdk=None),False),
                   ('lock',lambda v:v['toolchains'][0].update(version='unbounded '+('x'*100)),False),
                   ('qualification',lambda v:v.update(limitations=['free text is not an identifier']),False)]
        for name,change,valid in mutations:
            with self.subTest(name=name,valid=valid),tempfile.TemporaryDirectory() as temp:
                root=Path(temp).resolve();f=build_fixture(root);rewrite(root,f,name,change)
                expected=oracle_v1.validate_bundle(root,f['paths'][name],context='fixture');actual=native(root,f['paths'][name],context='fixture')
                self.assertEqual(expected['record_valid'],valid);self.assertEqual(actual['record_valid'],valid,(expected,actual))

# Invoke the original oracle assertions with an additional independent native comparison
# for every evaluation. Python-only registry/monkeypatched resource-budget tests remain
# in their original suite; their artificial constants are not a native configuration.
def differential(module_name,class_name,name,version):
    def test(self):
        module=importlib.import_module(module_name);case=getattr(module,class_name)(name)
        original=oracle_v2.validate_bundle if version==2 else oracle_v1.validate_bundle
        comparisons=[]
        def compare(*args,**kwargs):
            expected=original(*args,**kwargs);actual=native(*args,**kwargs)
            self.assertEqual(actual['record_valid'],expected['record_valid'],(name,expected,actual))
            self.assertEqual(actual['eligible'],expected['eligible'],(name,expected,actual))
            if expected['record_valid']:
                self.assertEqual(actual['outcome_codes'],expected['outcome_codes'],(name,expected,actual))
            comparisons.append(True)
            return expected
        target=oracle_v2 if version==2 else module
        # The path suite imports validate_bundle inside its method.
        if module_name=='test_paths_and_privacy': target=oracle_v1
        with patch.object(target,'validate_bundle',compare,create=True):
            result=unittest.TestResult();case.run(result)
        self.assertFalse(result.errors,result.errors);self.assertFalse(result.failures,result.failures)
        self.assertTrue(comparisons,'scenario did not exercise native evaluation')
    return test

EXCLUDED={'test_v1_evaluation_is_unchanged_when_interleaved_with_v2','test_schema_registry_cannot_redirect_to_remote_file','test_unknown_schema_ref_is_rejected_without_retrieval','test_unresolved_local_definition_is_rejected','test_aggregate_blob_budget_is_checked_before_hashing_next_file','test_aggregate_json_budget_is_checked_before_next_record','test_schema_registration_refuses_remote_resolution','test_schema_registration_rejects_wrong_version','test_v2_aggregate_blob_budget_is_checked','test_direct_api_nul_entry_is_bounded'}
for mod,cls,version in [('test_eligibility','EligibilityTests',1),('test_structure','StructureTests',1),('test_paths_and_privacy','FixturePathAndPrivacyTests',1),('test_v2','V2Tests',2)]:
    module=importlib.import_module(mod)
    for name in unittest.defaultTestLoader.getTestCaseNames(getattr(module,cls)):
        if name not in EXCLUDED:setattr(AdmissionTests,'test_native_'+cls+'_'+name[5:],differential(mod,cls,name,version))
