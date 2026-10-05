"""Optional actual-input controls; excluded from public synthetic CI.

Full test_*.py discovery retains these tests. Supplying an invalid input fails
import; absent private inputs leave explicit skips rather than passing evidence.
"""
from contextlib import contextmanager
import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

import test_deterministic_pair as portable

Temporary = portable.Temporary
pair, reuse, REPO = portable.pair, portable.reuse, portable.REPO

# Supplying an input means it must parse/pass; absent private artifacts alone
# opt out of actual-byte review controls, without suppressing portable tests.
QUAL_PATH=Path(os.environ['PEAR_TEST_QUALIFICATION'])if os.environ.get('PEAR_TEST_QUALIFICATION')else None
QUAL=json.loads(QUAL_PATH.read_bytes())if QUAL_PATH is not None else None
METAL_ROOT=Path(QUAL['metal_control_ref']['path']).parent if QUAL is not None else None


@unittest.skipUnless(QUAL is not None,'optional actual Metal controls require PEAR_TEST_QUALIFICATION')
class MetalControlEnvironment(Temporary):
    def context(self):
        with reuse.legacy(REPO)as cap:
            common=cap.load('tools/dxmt/common.py')
            raw=common.read_relative(METAL_ROOT,'control.json')
        return json.loads(raw)
    @contextmanager
    def common(self):
        with reuse.legacy(REPO)as cap:yield cap.load('tools/dxmt/common.py')
    def test_genuine_predecessor_environment_and_tool_replay(self):
        value=self.context()
        with self.common()as common:
            prior=pair.metal_predecessor(value,METAL_ROOT,QUAL['metal_predecessor_refs'],common)
        self.assertEqual(value['tool_sha256'],prior['tool_sha256'])
    def test_zero_or_rehashed_predecessor_refused(self):
        for pin in ('0'*64,'a'*64,False):
            value=self.context();value['prior_probe_sha256']=pin
            with self.subTest(pin=pin),self.common()as common,self.assertRaises(reuse.Error):
                pair.metal_predecessor(value,METAL_ROOT,QUAL['metal_predecessor_refs'],common)
    def test_extra_dynamic_loader_and_altered_recipe_env_refused(self):
        for key,new in [('DYLD_INSERT_LIBRARIES','/unapproved.dylib'),('SDKROOT','/otherSDK'),
                        ('PATH','/unapproved/bin'),('TMPDIR','/other/tmp'),('HOME','/other/home')]:
            value=self.context();value['environment'][key]=new
            with self.subTest(key=key),self.common()as common,self.assertRaises(reuse.Error):
                pair.metal_predecessor(value,METAL_ROOT,QUAL['metal_predecessor_refs'],common)
    def test_predecessor_refs_are_closed_and_exactly_pinned(self):
        for action in ('extra','missing','changed_digest'):
            refs=copy.deepcopy(QUAL['metal_predecessor_refs'])
            if action=='extra':refs['unexpected']=refs['control']
            elif action=='missing':refs.pop('recipe')
            else:refs['producer']['sha256']='0'*64
            with self.subTest(action=action),self.common()as common,self.assertRaises(reuse.Error):
                pair.metal_predecessor(self.context(),METAL_ROOT,refs,common)
    def test_copied_ref_path_refused_by_original_producer_declaration(self):
        refs=copy.deepcopy(QUAL['metal_predecessor_refs']);original=Path(refs['control']['path'])
        copied=self.write('control.json',original.read_bytes());refs['control']['path']=str(copied)
        with self.common()as common,self.assertRaisesRegex(reuse.Error,'det_metal_predecessor_source_paths'):
            pair.metal_predecessor(self.context(),METAL_ROOT,refs,common)
    def test_altered_tool_digest_refused(self):
        value=self.context();value['tool_sha256']='0'*64
        with self.common()as common,self.assertRaises(reuse.Error):
            pair.metal_predecessor(value,METAL_ROOT,QUAL['metal_predecessor_refs'],common)



class Reuse(Temporary):
    @unittest.skipUnless(os.environ.get('PEAR_TEST_FEX_REPO'),'optional retained FEX input requires PEAR_TEST_FEX_REPO')
    def test_reviewed_fex_package_import_is_captured_without_global_package_alias(self):
        owner = Path(os.environ['PEAR_TEST_FEX_REPO'])
        name = '_pear_dxmt_reviewed_fex_' + reuse.digest(str(owner).encode())[:16]
        with mock.patch('subprocess.Popen', side_effect=AssertionError('no tools')):
            with reuse.legacy(REPO) as cap:
                package = __import__('types').ModuleType(name)
                package.__path__ = [str(owner / 'tools/fex')];package.__package__ = name
                cap.module_view[name] = package
                module = cap.import_module(name + '.tools')
                self.assertNotIn(name, sys.modules);self.assertNotIn(name + '.tools', sys.modules)
                self.assertTrue(module.__name__.startswith(cap.name + '.'))
                self.assertIs(module, cap.module_view[name + '.tools'])
                self.assertTrue(callable(module.verify_tools));cap.closure()
                with self.assertRaises(reuse.Error):cap.import_module(name + '.unreviewed')



@unittest.skipUnless(QUAL is not None and QUAL.get('schema_version')==3,
                     'optional actual fixed-directory controls require qualification3')
class FixedDirectoryActual(unittest.TestCase):
    def test_actual_source_dependency_configuration_and_post_observation_closure(self):
        with reuse.legacy(REPO)as capture:
            common=capture.load('tools/dxmt/common.py')
            original=Path(QUAL['original_ref']['path']).parent
            prior=pair.wine_control(QUAL['wine_control_ref'],original,common)
            value=pair.fixed_compilation_directory(QUAL['wine_compilation_directory_ref'],
                QUAL['wine_compilation_directory_binding_ref'],QUAL['wine_control_ref'],prior,common)
            self.assertFalse(value['full_build']);self.assertTrue(value['configure_source_reused_read_only'])



if __name__ == '__main__':
    unittest.main()
