"""Pure current-constructor identity controls; no build/admission/run route."""
import ast
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest import mock

REPO=Path(os.environ.get('PEAR_TEST_REPO',str(Path(__file__).resolve().parents[2])))
IMPLEMENTATION=Path(os.environ.get('PEAR_TEST_NATIVE_IMPLEMENTATION_ROOT',str(REPO/'tools/dxmt')))
CONSTRUCTOR=Path(os.environ.get('PEAR_TEST_IMPLEMENTATION_ROOT',str(REPO/'tools/dxmt')))

def load(name):
    spec=importlib.util.spec_from_file_location('_pin_chain_'+name,IMPLEMENTATION/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

native=load('deterministic_native');coordinator=load('deterministic_reproduce')

class ConstructorPinChain(unittest.TestCase):
    @contextmanager
    def no_live_routes(self):
        def forbidden(*args,**kwargs):raise AssertionError('live_route_forbidden')
        with mock.patch.object(subprocess,'Popen',side_effect=forbidden),mock.patch.object(os,'system',side_effect=forbidden):yield
    def test_exact_manifest_sources_and_coordinator_are_current(self):
        raw=native.bounded_source(IMPLEMENTATION,'constructor-pins.json');pin=json.loads(raw)
        self.assertEqual(native.digest(raw),native.CONSTRUCTOR_PIN_SHA)
        self.assertEqual(set(pin['files']),{'deterministic_pair.py','deterministic_reuse.py','metal_stdin.py','deterministic_monitor.py','reuse-pins.json'})
        for leaf,expected in pin['files'].items():
            with self.subTest(leaf=leaf):self.assertEqual(native.digest(native.bounded_source(CONSTRUCTOR,leaf)),expected)
        actual=native.bounded_source(IMPLEMENTATION,'deterministic_native.py')
        self.assertEqual(native.digest(actual),coordinator.NATIVE_SOURCE_PIN)
        self.assertEqual(coordinator.capture_native_source(IMPLEMENTATION),actual)
    def test_current_actual_adapter_closure_accepts_without_live_operation(self):
        with self.no_live_routes(),coordinator.native_adapter(REPO,CONSTRUCTOR)as adapter:
            descriptor=adapter.descriptor('runtime');producer=adapter.producers()
            self.assertEqual(producer['tools/dxmt/constructor-pins.json'],native.CONSTRUCTOR_PIN_SHA)
            self.assertEqual(producer['tools/dxmt/deterministic_native.py'],coordinator.NATIVE_SOURCE_PIN)
            helper=json.loads(native.bounded_source(IMPLEMENTATION,'constructor-pins.json'))['files']['metal_stdin.py']
            self.assertEqual(producer['tools/dxmt/metal_stdin.py'],helper)
            self.assertEqual(descriptor['native_loading']['source_sha256'],coordinator.NATIVE_SOURCE_PIN)
            self.assertFalse(descriptor['source_gates']['original_records_accepted'])
            self.assertTrue(descriptor['source_gates']['fresh_39_case_native_execution_required'])
    def test_changed_constructor_leaf_refused_before_source_execution(self):
        original=native.bounded_source
        for leaf in ['deterministic_pair.py','deterministic_reuse.py','metal_stdin.py','deterministic_monitor.py','reuse-pins.json']:
            def altered(root,name,selected=leaf):
                value=original(root,name)
                return value+b'\nraise AssertionError("unreviewed source executed")\n'if Path(root)==CONSTRUCTOR and name==selected else value
            with self.subTest(leaf=leaf),self.no_live_routes(),mock.patch.object(native,'bounded_source',side_effect=altered):
                with self.assertRaisesRegex(native.Error,'native_constructor_source_changed'):native.Adapter(REPO,CONSTRUCTOR)
    def test_previous_metal_pin_cannot_admit_current_constructor(self):
        original=native.bounded_source;raw=original(IMPLEMENTATION,'constructor-pins.json');pin=json.loads(raw)
        pin['files']['metal_stdin.py']='ab478c4e51026640450b8cbe901def5705b999c23cc49f48b2fd53124d8327e1'
        old=json.dumps(pin,sort_keys=True,indent=2).encode()+b'\n'
        def altered(root,leaf):return old if Path(root)==IMPLEMENTATION and leaf=='constructor-pins.json'else original(root,leaf)
        with self.no_live_routes(),mock.patch.object(native,'bounded_source',side_effect=altered):
            with self.assertRaisesRegex(native.Error,'native_constructor_pins_changed'):native.Adapter(REPO,CONSTRUCTOR)
        # A separately pinned old manifest still cannot admit the new helper.
        with self.no_live_routes(),mock.patch.object(native,'CONSTRUCTOR_PIN_SHA',native.digest(old)),mock.patch.object(native,'bounded_source',side_effect=altered):
            with self.assertRaisesRegex(native.Error,'native_constructor_source_changed'):native.Adapter(REPO,CONSTRUCTOR)
    def test_changed_manifest_bytes_are_not_accepted_by_json_equivalence(self):
        original=native.bounded_source
        def altered(root,leaf):
            value=original(root,leaf)
            return value+b' 'if Path(root)==IMPLEMENTATION and leaf=='constructor-pins.json'else value
        with self.no_live_routes(),mock.patch.object(native,'bounded_source',side_effect=altered):
            with self.assertRaisesRegex(native.Error,'native_constructor_pins_changed'):native.Adapter(REPO,CONSTRUCTOR)
    def test_old_coordinator_native_hash_is_refused(self):
        with self.no_live_routes(),mock.patch.object(coordinator,'NATIVE_SOURCE_PIN','7e1eecef67f5fe6281d4ef2d7eeb4f484273dcf10214dfcbc7b64d6eb6c3f041'):
            with self.assertRaisesRegex(ValueError,'native_loader_source_changed'):coordinator.capture_native_source(IMPLEMENTATION)
    def test_old_explicit_executed_source_is_refused(self):
        with self.no_live_routes(),self.assertRaisesRegex(native.Error,'native_executed_source_changed'):
            native.Adapter(REPO,CONSTRUCTOR,executed_native_sha='7e1eecef67f5fe6281d4ef2d7eeb4f484273dcf10214dfcbc7b64d6eb6c3f041')
    def test_post_capture_constructor_change_blocks_producers(self):
        original=coordinator.native.bounded_source
        with self.no_live_routes(),coordinator.native_adapter(REPO,CONSTRUCTOR)as adapter:
            def altered(root,leaf):
                value=original(root,leaf)
                return value+b'\n'if Path(root)==CONSTRUCTOR and leaf=='metal_stdin.py'else value
            with mock.patch.object(coordinator.native,'bounded_source',side_effect=altered),self.assertRaisesRegex(coordinator.native.Error,'native_constructor_source_changed'):adapter.producers()
    def test_qualification_boundary_is_still_explicit(self):
        self.assertIn('game_qualification',coordinator.UNPERFORMED)
        self.assertIn('distribution_qualification',coordinator.UNPERFORMED)
        self.assertIn('hybrid_execution',coordinator.UNPERFORMED)
        self.assertIn('shader_workload',coordinator.UNPERFORMED)

if __name__=='__main__':unittest.main()
