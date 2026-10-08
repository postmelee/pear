"""Pure byte/argument controls; no compiler or source runtime is invoked."""
import importlib.util
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
REPO = Path(os.environ.get('PEAR_FEX_TEST_REPO', Path(__file__).resolve().parents[2])).resolve(strict=True)
sys.path.insert(0, str(REPO))
from tools.fex import memory_fex_check as e
H = e.H

class AllocatorCompileScope(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='pear-allocator-scope-control-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.source = self.root / 'source'
        self.output = self.root / 'pe/wow64'
        # These small source-byte fixtures replace only the exact pin table.
        # They test the real closed parser; they never claim upstream admission.
        fixtures = {name: ('// injected portable source fixture: '+name+'\n').encode()
                    for name in e.UPSTREAM_ALLOCATOR_INPUTS}
        pins = {name: (H(data), len(data), 0o644) for name, data in fixtures.items()}
        self.pin_patch = patch.object(e, 'UPSTREAM_ALLOCATOR_INPUTS', pins)
        self.pin_patch.start()
        self.addCleanup(self.pin_patch.stop)
        for rel, data in fixtures.items():
            p = self.source / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            p.chmod(0o644)
        self.row = {'file':str(self.source / e.UPSTREAM_ALLOCATOR_SOURCE), 'output':e.UPSTREAM_ALLOCATOR_OBJECT,
                    'directory':str(self.output), 'command':'cc -DENABLE_FEX_ALLOCATOR=1'}
        self.paths = [str(self.source / x) for x in e.UPSTREAM_ALLOCATOR_INPUTS]
    def refused(self, function, *args):
        with self.assertRaises(e.Error): function(*args)
    def test_exact_pinned_translation_unit(self):
        self.assertTrue(e.upstream_allocator_compile_proof(self.row, self.source))
    def test_exact_three_source_dependency_closure(self):
        proof = e.upstream_allocator_dependency_proof(self.row, self.source, self.paths)
        self.assertEqual(set(proof['selected_source_inputs']),set(e.UPSTREAM_ALLOCATOR_INPUTS))
        self.assertFalse(proof['owner_macro_required']);self.assertFalse(proof['source_runtime_qualified'])
    def test_changed_source(self):
        p = self.source / e.UPSTREAM_ALLOCATOR_SOURCE;p.write_bytes(p.read_bytes()+b'\n')
        self.refused(e.upstream_allocator_compile_proof,self.row,self.source)
    def test_changed_source_mode(self):
        (self.source/e.UPSTREAM_ALLOCATOR_SOURCE).chmod(0o600)
        self.refused(e.upstream_allocator_compile_proof,self.row,self.source)
    def test_wrong_cmake_object_target(self):
        self.row['output']=self.row['output'].replace('JemallocLibs.dir','FEXCore_object.dir')
        self.refused(e.upstream_allocator_compile_proof,self.row,self.source)
    def test_owner_undefined(self):
        self.row['command']+=' -UPEAR_FEX_MEMORY_OWNER'
        self.refused(e.upstream_allocator_compile_proof,self.row,self.source)
    def test_owner_split_undefined(self):
        self.row['command']+=' -U PEAR_FEX_MEMORY_OWNER'
        self.refused(e.upstream_allocator_compile_proof,self.row,self.source)
    def test_owner_defined_zero(self):
        self.row['command']+=' -DPEAR_FEX_MEMORY_OWNER=0'
        self.refused(e.upstream_allocator_compile_proof,self.row,self.source)
    def test_owner_defined_one_is_not_silently_new_policy(self):
        self.row['command']+=' -DPEAR_FEX_MEMORY_OWNER=1'
        self.refused(e.upstream_allocator_compile_proof,self.row,self.source)
    def test_owner_related_macro(self):
        self.row['command']+=' -DPEAR_FEX_MEMORY_FINITE_FIXTURE=1'
        self.refused(e.upstream_allocator_compile_proof,self.row,self.source)
    def test_allocator_configuration_missing(self):
        self.row['command']='cc'
        self.refused(e.upstream_allocator_compile_proof,self.row,self.source)
    def test_allocator_redefined(self):
        self.row['command']+=' -DENABLE_FEX_ALLOCATOR=0'
        self.refused(e.upstream_allocator_compile_proof,self.row,self.source)
    def test_forced_include_refused(self):
        self.row['command']+=' -include '+str(self.source/'injected.h')
        self.refused(e.upstream_allocator_compile_proof,self.row,self.source)
    def test_wire_search_root_refused(self):
        self.row['command']+=' -I'+str(self.root/'wire')
        self.refused(e.upstream_allocator_compile_proof,self.row,self.source)
    def test_missing_selected_source_dependency(self):
        self.refused(e.upstream_allocator_dependency_proof,self.row,self.source,self.paths[:-1])
    def test_extra_source_dependency(self):
        self.refused(e.upstream_allocator_dependency_proof,self.row,self.source,self.paths+[str(self.source/'arbitrary.h')])
    def test_changed_selected_header(self):
        p=self.source/'FEXCore/include/FEXCore/Utils/PrctlUtils.h';p.write_bytes(p.read_bytes()+b'\n')
        self.refused(e.upstream_allocator_dependency_proof,self.row,self.source,self.paths)
    def test_curated_wire_dependency(self):
        self.refused(e.upstream_allocator_dependency_proof,self.row,self.source,self.paths+[str(self.root/'wire/wine/pear_fex_memory.h')])
    def test_pear_dependency_in_tool_path(self):
        self.refused(e.upstream_allocator_dependency_proof,self.row,self.source,self.paths+[str(self.root/'tc/include/PearFEXMemory.h')])
    def test_other_source_gets_no_exception(self):
        self.row['file']=str(self.source/'FEXCore/Source/Interface/Core/Core.cpp')
        self.assertFalse(e.upstream_allocator_compile_proof(self.row,self.source))
    def test_other_owner_source_still_requires_macro(self):
        self.row['file']=str(self.source/'FEXCore/Source/Interface/Core/Core.cpp')
        with patch.object(e.original,'compile_command_proof',return_value=self.output/'a.obj'),patch.object(e,'selected_include_proof',return_value=[]):
            self.refused(e.owner_compile_proof,self.row,self.output,self.source,self.root/'tc','aarch64-w64-mingw32',{}, {})
    def test_required_wire_source_set_unchanged(self):
        self.assertIn('FEXCore/Source/Interface/Core/SharedCodeBufferManager.cpp',e.WIRE_REQUIRED_SOURCES)
        self.assertIn('FEXCore/Source/Utils/ArchHelpers/Arm64.cpp',e.WIRE_REQUIRED_SOURCES)



SYMBOL='_ZN7FEXCore5Utils13PearFEXMemory15SourceLifecycle21AttachAllocatedThreadEPKNS_7Context7ContextEPNS_4Core19InternalThreadStateEj'
OWNER='libCommonWindows:PearFEXMemory.cpp.obj'

class SourceLifecycleSymbolScope(unittest.TestCase):
 def setUp(self):
  # Only the unchanged, separate CRT/provider proof is injected. All selected
  # owner/direct-symbol parsing and exact lifetime signature checks are real.
  self.baseline_patch=patch.object(e.original,'source_map_proof',return_value={'baseline':'injected_only'})
  self.baseline_patch.start();self.addCleanup(self.baseline_patch.stop)
  prefix='_ZN7FEXCore5Utils13PearFEXMemory'
  lines=[]
  for name in ('Init','Reserve','RegisterExecutor','Enter','Exit','Handoff','Poll'):
   lines.append(self.row('#'+prefix+str(len(name))+name+'Ev'))
  lines.append(self.row('#'+SYMBOL))
  for name in ('AdmissionOpen','PoisonSourceAdmission','EnqueueDetached','DrainAtNativeGate'):
   lines.append(self.row('#'+prefix+'10Retirement'+str(len(name))+name+'Ev','PearFEXRetirement.cpp.obj'))
  lines.append(self.row('#'+prefix+'5Links18EntryAdmissionOpenEv','PearJITLinks.cpp.obj'))
  for symbol,owner in [
   ('_ZN7FEXCore7Context11ContextImpl12InitPearCoreERNS_5Utils13PearFEXMemory6ResultE','Core.cpp.obj'),
   ('_ZN7FEXCore7Context11ContextImpl16CreatePearThreadEPKNS_4Core8CPUStateERNS_5Utils13PearFEXMemory6ResultEPS8_Pb','Core.cpp.obj'),
   ('_ZNK7FEXCore3CPU10CPUBackend22FindPearRetainedTargetEy','CPUBackend.cpp.obj')]:lines.append(self.row('#'+symbol,owner))
  lines.append(self.row('#'+SYMBOL+'$exit_thunk','Core.cpp.obj'))
  self.text=''.join(lines)
 def refused(self,text):
  with self.assertRaises(e.Error):e.source_symbol_proof(text)
 def row(self,symbol,owner=OWNER):return ' 0001:00000001 '+symbol+' 0000000180000001 '+owner+'\n'
 def test_exact_body_and_distinct_generated_exit_thunk(self):
  self.assertIn(SYMBOL+'$exit_thunk',self.text)
  r=e.source_symbol_proof(self.text);self.assertEqual(r['owner_symbols']['source_lifecycle'],[{'symbol':SYMBOL,'archive':'libCommonWindows','member':'PearFEXMemory.cpp.obj'}])
 def test_wrong_signature(self):self.refused(self.text.replace(SYMBOL,SYMBOL[:-1]+'m'))
 def test_wrong_namespace(self):self.refused(self.text.replace(SYMBOL,SYMBOL.replace('15SourceLifecycle','16ForeignLifecycle')))
 def test_wrong_body_owner(self):self.refused(self.text+ '\n'+self.row(SYMBOL,'libCommonWindows:Foreign.cpp.obj'))
 def test_wrong_archive_owner(self):self.refused(self.text+ '\n'+self.row(SYMBOL,'libForeign:PearFEXMemory.cpp.obj'))
 def test_missing_plain_body_thunk_retained(self):
  lines=[s for s in self.text.splitlines() if SYMBOL not in s or '$exit_thunk' in s]
  self.refused('\n'.join(lines))
 def test_thunk_only_correct_owner_does_not_admit(self):
  text='\n'.join(s for s in self.text.splitlines() if SYMBOL not in s)
  self.refused(text+'\n'+self.row(SYMBOL+'$exit_thunk'))
 def test_legacy_top_level_alias_does_not_substitute(self):
  text='\n'.join(s for s in self.text.splitlines() if SYMBOL not in s)
  self.refused(text+'\n'+self.row('_ZN7FEXCore5Utils13PearFEXMemory21AttachAllocatedThreadEv'))
 def test_legacy_alias_alongside_actual_body_refused(self):
  self.refused(self.text+'\n'+self.row('_ZN7FEXCore5Utils13PearFEXMemory21AttachAllocatedThreadEv'))
 def test_extra_unqualified_overload(self):self.refused(self.text+'\n'+self.row(SYMBOL[:-1]+'m'))
 def test_missing_other_adapter_method_still_refused(self):
  prefix='_ZN7FEXCore5Utils13PearFEXMemory7HandoffE'
  self.refused('\n'.join(s for s in self.text.splitlines() if prefix not in s))
