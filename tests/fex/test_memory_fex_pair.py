"""Portable controls for the private new full-module constructor and byte proof.

No compiler, Apple command, module load, FEX initialization or owner call runs.
"""
import copy
import hashlib
import json
import os
import runpy
import subprocess
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

_repository=Path(os.environ.get('PEAR_FEX_TEST_REPO',Path(__file__).resolve().parents[2])).resolve(strict=True)
sys.path.insert(0,str(_repository))
from tools.fex import memory_fex_check as evidence, memory_fex_build as constructor

H=evidence.H


class OwnedFixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='pear-fex-proof-')
        self.root=Path(self.temp.name).resolve()
    def tearDown(self):self.temp.cleanup()
    def file(self,name,data=b'x',mode=0o644):
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);path.chmod(mode);return path


class SourceBounds(OwnedFixture):
    def test_plain_tree_and_copy(self):
        self.file('origin/a.cpp',b'abc');self.file('origin/sub/script',b'#!/x',0o755)
        rows=evidence.source_inventory(self.root/'origin')
        constructor.copy_source(self.root/'origin',self.root/'copy',rows)
        self.assertEqual(evidence.source_inventory(self.root/'copy'),rows)
    def test_copy_rejects_altered_source(self):
        p=self.file('origin/a.cpp',b'abc');rows=evidence.source_inventory(p.parent);p.write_bytes(b'abd')
        with self.assertRaises(evidence.Error):constructor.copy_source(p.parent,self.root/'copy',rows)
    def test_copy_refuses_existing_destination(self):
        p=self.file('origin/a.cpp');rows=evidence.source_inventory(p.parent);(self.root/'copy').mkdir()
        with self.assertRaises(FileExistsError):constructor.copy_source(p.parent,self.root/'copy',rows)
    def test_source_link_refused(self):
        self.file('origin/a');(self.root/'origin/b').symlink_to('a')
        with self.assertRaises(evidence.Error):evidence.source_inventory(self.root/'origin')
    def test_source_hardlink_refused(self):
        p=self.file('origin/a');os.link(p,p.parent/'b')
        with self.assertRaises(evidence.Error):evidence.source_inventory(p.parent)
    def test_source_mode_refused(self):
        p=self.file('origin/a',mode=0o600)
        with self.assertRaises(evidence.Error):evidence.source_inventory(p.parent)
    def test_source_file_size_refused(self):
        p=self.file('origin/a',b'ab')
        with patch.object(evidence,'MAX_SOURCE_FILE',1),self.assertRaises(evidence.Error):evidence.source_inventory(p.parent)
    def test_source_file_count_refused(self):
        self.file('origin/a');self.file('origin/b')
        with patch.object(evidence,'MAX_FILES',1),self.assertRaises(evidence.Error):evidence.source_inventory(self.root/'origin')
    def test_source_directory_alias_refused(self):
        # Case-sensitive systems can create this genuine directory collision;
        # on a case-insensitive volume the OS itself merges the candidates.
        self.file('origin/A/x');self.file('origin/a/y')
        if len(list((self.root/'origin').iterdir()))==1:self.skipTest('case-insensitive fixture volume')
        with self.assertRaises(evidence.Error):evidence.source_inventory(self.root/'origin')


class CanonicalPatchControls(unittest.TestCase):
    def setUp(self):
        self.strict=b'diff --git a/a b/a\n--- /dev/null\n+++ b/a\n@@ -0,0 +1 @@\n+x\n'
        self.rows=[{'path':'a','preimage_sha256':None,'postimage_sha256':H(b'x\n'),'postimage_bytes':2}]
    def test_new_file_exact_metadata(self):
        git=evidence.render_declared_git(self.strict,self.rows)
        self.assertEqual(git,self.strict.replace(b'--- /dev/null',b'new file mode 100644\n--- /dev/null'))
    def test_existing_file_has_no_added_metadata(self):
        strict=b'diff --git a/a b/a\n--- a/a\n+++ b/a\n@@ -1 +1 @@\n-y\n+x\n'
        rows=[dict(self.rows[0],preimage_sha256=H(b'y\n'))]
        self.assertEqual(evidence.render_declared_git(strict,rows),strict)
    def test_non_null_misdeclared_header(self):
        with self.assertRaises(evidence.Error):evidence.render_declared_git(self.strict,[dict(self.rows[0],preimage_sha256='0'*64)])
    def test_extra_metadata_is_not_stripped(self):
        with self.assertRaises(evidence.Error):evidence.render_declared_git(self.strict.replace(b'--- /dev/null',b'new file mode 100644\n--- /dev/null'),self.rows)
    def test_duplicate_paths(self):
        with self.assertRaises(evidence.Error):evidence.change_rows(self.rows+self.rows)
    def test_traversal_path(self):
        with self.assertRaises(evidence.Error):evidence.change_rows([dict(self.rows[0],path='../a')])
    def test_boolean_size(self):
        with self.assertRaises(evidence.Error):evidence.change_rows([dict(self.rows[0],postimage_bytes=True)])


class SnapshotControls(OwnedFixture):
    def setUp(self):
        super().setUp();self.paths=[self.file('original/a',b'one'),self.file('original/b',b'two')]
        self.output=self.root/'output';self.output.mkdir();self.rows=constructor.snapshot(self.output,self.paths)
    def test_current_exact_set(self):evidence.verify_snapshots(self.output,self.rows,self.paths)
    def test_omitted_input(self):
        with self.assertRaises(evidence.Error):evidence.verify_snapshots(self.output,self.rows[:1],self.paths)
    def test_reordered_inputs(self):
        with self.assertRaises(evidence.Error):evidence.verify_snapshots(self.output,self.rows[::-1],self.paths)
    def test_copy_name_mismatch(self):
        rows=copy.deepcopy(self.rows);rows[0]['copy']='inputs/0001.bin'
        with self.assertRaises(evidence.Error):evidence.verify_snapshots(self.output,rows,self.paths)
    def test_current_source_altered(self):
        self.paths[0].write_bytes(b'bad')
        with self.assertRaises(evidence.Error):evidence.verify_snapshots(self.output,self.rows,self.paths)
    def test_copy_altered(self):
        (self.output/self.rows[0]['copy']).write_bytes(b'bad')
        with self.assertRaises(evidence.Error):evidence.verify_snapshots(self.output,self.rows,self.paths)
    def test_copy_mode_wrong(self):
        (self.output/self.rows[0]['copy']).chmod(0o644)
        with self.assertRaises(evidence.Error):evidence.verify_snapshots(self.output,self.rows,self.paths)
    def test_extra_copy(self):
        (self.output/'inputs/extra').write_bytes(b'x')
        with self.assertRaises(evidence.Error):evidence.verify_snapshots(self.output,self.rows,self.paths)


class OutputControls(OwnedFixture):
    def test_manifest_excludes_only_root_control_records(self):
        self.file('build.json',b'x');self.file('output-files.json',b'y');self.file('nested/build.json',b'z')
        rows=evidence.output_inventory(self.root)
        self.assertEqual([r['path'] for r in rows],['nested/build.json'])
    def test_output_symlink(self):
        self.file('a');(self.root/'b').symlink_to('a')
        with self.assertRaises(evidence.Error):evidence.output_inventory(self.root)
    def test_output_hardlink(self):
        p=self.file('a');os.link(p,self.root/'b')
        with self.assertRaises(evidence.Error):evidence.output_inventory(self.root)
    def test_output_current_bytes(self):
        p=self.file('a',b'one');before=evidence.output_inventory(self.root);p.write_bytes(b'two')
        self.assertNotEqual(evidence.output_inventory(self.root),before)


class ByteAlgorithms(OwnedFixture):
    def archive(self,machine=0xaa64):
        blob=struct.pack('<H',machine)+b'\0'*18
        header=(b'a.obj/          '+b'0           '+b'0     '+b'0     '+b'100644  '+str(len(blob)).encode().ljust(10)+b'`\n')
        self.assertEqual(len(header),60);return b'!<arch>\n'+header+blob
    def test_archive_parity_with_original_reader(self):
        raw=self.archive();p=self.file('a.lib',raw)
        self.assertEqual(evidence.archive_bytes(raw),evidence.check.archive_machines(p))
    def test_archive_truncated_member(self):
        with self.assertRaises(evidence.Error):evidence.archive_bytes(self.archive()[:-1])
    def test_archive_invalid_machine(self):
        with self.assertRaises(evidence.Error):evidence.archive_bytes(self.archive(0x1234))
    def test_metadata_only_archive(self):
        with self.assertRaises(evidence.Error):evidence.archive_bytes(b'!<arch>\n')
    def test_chpe_private_path_adapter_does_not_mutate_globals(self):
        old=evidence.check.inspect_fixture_arm64ec.__globals__['Path']
        with self.assertRaises(evidence.Error):evidence.module_bytes(b'invalid',self.root,'arm64ec')
        self.assertIs(evidence.check.inspect_fixture_arm64ec.__globals__['Path'],old)
        self.assertIs(evidence.original.module_facts.__globals__['PE'],evidence.original.PE)


class AdmissionAndFailures(OwnedFixture):
    def test_each_runtime_claim_refused(self):
        value={'qualification':dict(evidence.QUALIFICATION),**dict.fromkeys(evidence.FALSE_FLAGS,False)}
        evidence.qualification_gate(value)
        for flag in evidence.FALSE_FLAGS:
            with self.subTest(flag=flag):
                changed=copy.deepcopy(value);changed[flag]=True
                with self.assertRaises(evidence.Error):evidence.qualification_gate(changed)
    def test_qualification_unknown_refused(self):
        value={'qualification':dict(evidence.QUALIFICATION),**dict.fromkeys(evidence.FALSE_FLAGS,False)}
        value['qualification']['aggregate_metadata']='qualified'
        with self.assertRaises(evidence.Error):evidence.qualification_gate(value)
    def test_no_minimum_free_no_native_call(self):
        output=self.root/'out';output.mkdir()
        with patch.object(constructor.shutil,'disk_usage',return_value=shutil._ntuple_diskusage(100,99,1)):
            with self.assertRaises(evidence.Error):constructor.resource_gate(output,constructor.MAX_GROWTH,constructor.RESERVE_FREE)
    def test_native_errno_retained(self):
        actual=OSError(28,'full');row=constructor.observed_error(actual)
        self.assertEqual(row['native_error'],{'domain':'errno','code':28})
    def test_attached_errno_retained(self):
        actual=evidence.Error('spawn_error');actual.native_error={'domain':'errno','code':24}
        self.assertEqual(constructor.observed_error(actual)['native_error'],actual.native_error)
    def test_unknown_error_does_not_invent_native_error(self):
        self.assertNotIn('native_error',constructor.observed_error(evidence.Error('refused')))
    def test_record_failure_does_not_replace_original(self):
        actual=OSError(28,'full')
        with patch.object(constructor,'write_json',side_effect=OSError(13,'permission')):
            constructor.preserve_failure(self.root,{'passed':False},actual)
        self.assertEqual(actual.errno,28);self.assertEqual(actual.failure_record_error['native_error']['code'],13)
    def test_recipe_does_not_change_original(self):
        recipe={key:['cc'] for key in ('native.configure','native.build','native.fixture',
            'arm64ec.configure','arm64ec.build','arm64ec.inspect','wow64.configure','wow64.build','wow64.inspect')}
        with patch.object(evidence.original,'complete_recipe',return_value=recipe):
            result=evidence.recipe(self.root,self.root,{}, {}, {}, {})
        self.assertIn('-DPEAR_FEX_MEMORY_OWNER=ON',result['arm64ec.configure'])
        # Original complete_recipe returns fresh lists; the wrapper must also
        # preserve its caller-returned recipe object, including under doubles.
        self.assertNotIn('-DPEAR_FEX_MEMORY_OWNER=ON',recipe['arm64ec.configure'])


class ExactCommandControls(OwnedFixture):
    def setUp(self):
        super().setUp();self.env={'PATH':'/usr/bin','SDKROOT':'/exact/sdk'}
        self.expected={'native.configure':['/usr/bin/arch','-arm64','/qualified/cmake']}
        logs={}
        for name,data in [('stdout',b'ok\n'),('stderr',b'')]:
            path='logs/native.configure/'+name+'.bin';self.file(path,data,0o600)
            logs[name]={'path':path,'sha256':H(data),'size_bytes':len(data)}
        self.row={'id':'native.configure','argv':self.expected['native.configure'],'cwd':str(self.root),
            'environment':{**self.env,'PWD':str(self.root)},'timeout_seconds':600,
            'max_stream_bytes':evidence.MAX_LOG,'exit_code':0,'status':'completed','error_domain':None,
            'error_code':None,'logs':logs,'elapsed_ms':1}
        self.file('logs/native.configure/command.json',evidence.encoded(self.row),0o600)
    def test_exact_recipe(self):evidence.command_gate(self.root,[self.row],self.expected,self.env)
    def test_boolean_exit_refused(self):
        row=copy.deepcopy(self.row);row['exit_code']=False
        with self.assertRaises(evidence.Error):evidence.command_gate(self.root,[row],self.expected,self.env)
    def test_extra_argument_refused(self):
        row=copy.deepcopy(self.row);row['argv'].append('--unknown')
        with self.assertRaises(evidence.Error):evidence.command_gate(self.root,[row],self.expected,self.env)
    def test_environment_override_refused(self):
        row=copy.deepcopy(self.row);row['environment']['HOME']='/synthetic'
        with self.assertRaises(evidence.Error):evidence.command_gate(self.root,[row],self.expected,self.env)
    def test_raw_log_altered_refused(self):
        (self.root/'logs/native.configure/stdout.bin').write_bytes(b'xx\n')
        with self.assertRaises(evidence.Error):evidence.command_gate(self.root,[self.row],self.expected,self.env)
    def test_original_command_receipt_altered_refused(self):
        row=copy.deepcopy(self.row);row['elapsed_ms']=2
        with self.assertRaises(evidence.Error):evidence.command_gate(self.root,[row],self.expected,self.env)
    def test_missing_command_refused(self):
        with self.assertRaises(evidence.Error):evidence.command_gate(self.root,[],self.expected,self.env)
    def test_failure_fields_not_positive(self):
        row=copy.deepcopy(self.row);row['error_domain']='errno';row['error_code']=28
        with self.assertRaises(evidence.Error):evidence.command_gate(self.root,[row],self.expected,self.env)


class CompilerAndLinkProof(OwnedFixture):
    def test_owner_effective_macro_values(self):
        defined,undef=evidence.macro_values(['cc','-DPEAR_FEX_MEMORY_OWNER=1','-D','PEAR_FEX_MEMORY_OWNER=1'])
        self.assertEqual(defined,{'PEAR_FEX_MEMORY_OWNER':['1','1']});self.assertEqual(undef,set())
    def test_owner_conflicting_macro_is_visible(self):
        defined,undef=evidence.macro_values(['cc','-DPEAR_FEX_MEMORY_OWNER=1','-UPEAR_FEX_MEMORY_OWNER','-DPEAR_FEX_MEMORY_OWNER=0'])
        self.assertEqual(defined['PEAR_FEX_MEMORY_OWNER'],['1','0']);self.assertIn('PEAR_FEX_MEMORY_OWNER',undef)
    def real_map(self):
        # The old CRT proof remains an exact unchanged lower-level helper. This
        # finite owner-only map control mocks only that separate baseline fact.
        prefix='_ZN7FEXCore5Utils13PearFEXMemory';lines=[]
        def add(symbol,owner):lines.append(' 0001:00000001 '+symbol+' 0000000180000001 '+owner)
        for name in ('Init','Reserve','RegisterExecutor','Enter','Exit','Handoff','Poll','AttachAllocatedThread'):
            add('#'+prefix+str(len(name))+name+'Ev','libCommonWindows:PearFEXMemory.cpp.obj')
        for name in ('AdmissionOpen','PoisonSourceAdmission','EnqueueDetached','DrainAtNativeGate'):
            add('#'+prefix+'10Retirement'+str(len(name))+name+'Ev','PearFEXRetirement.cpp.obj')
        add('#'+prefix+'5Links18EntryAdmissionOpenEv','PearJITLinks.cpp.obj')
        for symbol,owner in [
            ('_ZN7FEXCore7Context11ContextImpl12InitPearCoreERNS_5Utils13PearFEXMemory6ResultE','Core.cpp.obj'),
            ('_ZN7FEXCore7Context11ContextImpl16CreatePearThreadEPKNS_4Core8CPUStateERNS_5Utils13PearFEXMemory6ResultEPS8_Pb','Core.cpp.obj'),
            ('_ZNK7FEXCore3CPU10CPUBackend22FindPearRetainedTargetEy','CPUBackend.cpp.obj')]:add('#'+symbol,owner)
        # Compiler-generated thunks have distinct ownership; no unused alias
        # is forced into the actual selected Common/direct-object bodies.
        add('#'+prefix+'4InitEv$exit_thunk','CodeCache.cpp.obj')
        return '\n'.join(lines)
    def test_actual_owner_map_and_generated_thunk(self):
        with patch.object(evidence.original,'source_map_proof',return_value={'baseline':'checked'}):
            proof=evidence.source_symbol_proof(self.real_map())
        self.assertEqual(len(proof['owner_symbols']['adapter']),8)
    def test_wrong_body_owner(self):
        text=self.real_map().replace('libCommonWindows:PearFEXMemory.cpp.obj','libCommonWindows:Foreign.cpp.obj',1)
        with patch.object(evidence.original,'source_map_proof',return_value={}),self.assertRaises(evidence.Error):evidence.source_symbol_proof(text)
    def test_missing_required_actual_body(self):
        text='\n'.join(line for line in self.real_map().splitlines() if 'AttachAllocatedThread' not in line)
        with patch.object(evidence.original,'source_map_proof',return_value={}),self.assertRaises(evidence.Error):evidence.source_symbol_proof(text)
    def test_system_git_exception_is_not_generic(self):
        p=self.file('git',b'x')
        with self.assertRaises(evidence.Error):evidence.regular_bytes(p.parent,p.name,1024,system_git=True)


class ReviewTwoControls(OwnedFixture):
    real_map=CompilerAndLinkProof.real_map
    def test_each_foreign_source_method_name_refused(self):
        for name in ('InitPearCore','CreatePearThread','FindPearRetainedTarget'):
            changed=self.real_map().replace(name,'Foreign'+name)
            with self.subTest(name=name),patch.object(evidence.original,'source_map_proof',return_value={}),self.assertRaises(evidence.Error):
                evidence.source_symbol_proof(changed)
    def test_wrong_source_method_argument_refused(self):
        text=self.real_map().replace('22FindPearRetainedTargetEy','22FindPearRetainedTargetEm')
        with patch.object(evidence.original,'source_map_proof',return_value={}),self.assertRaises(evidence.Error):evidence.source_symbol_proof(text)
    def test_wrong_source_method_namespace_refused(self):
        text=self.real_map().replace('7Context11ContextImpl12InitPearCore','7Foreign11ContextImpl12InitPearCore')
        with patch.object(evidence.original,'source_map_proof',return_value={}),self.assertRaises(evidence.Error):evidence.source_symbol_proof(text)
    def test_closed_header_search_order(self):
        source=self.root/'source';output=self.root/'pe/wow64';wire=str(self.root/'wire')
        target='Core/CMakeFiles/engine.dir';row={'output':target+'/a.obj',
            'command':'cc -I'+str(source)+' -I'+wire}
        policy={target:{(str(source),)}}
        self.assertEqual(evidence.selected_include_proof(row,source,policy),[str(source),wire])
        row['command']='cc -I/foreign -I'+str(source)+' -I'+wire
        with self.assertRaises(evidence.Error):evidence.selected_include_proof(row,source,policy)
    def test_each_forced_or_alternate_header_option_refused(self):
        for flag in ('-include','-include-pch','-imacros','-isystem','-iquote','-idirafter',
                     '--sysroot=','-isysroot','-resource-dir=','-fmodule-map-file=','-fprebuilt-module-path='):
            with self.subTest(flag=flag),self.assertRaises(evidence.Error):evidence.include_arguments(['cc',flag+'/foreign'])
    def test_depfile_escaped_space_and_continuation(self):
        target,paths=evidence.make_dependencies(b'a.obj: /input/New\\ project/a.cpp \\\n /input/header.h\n')
        self.assertEqual((target,paths),('a.obj',['/input/New project/a.cpp','/input/header.h']))
    def test_depfile_wrong_target_or_variables_refused(self):
        for raw in (b'a.obj b.obj: a.h\n',b'a.obj: $include\n',b'a.obj: a.h #comment\n',b'a.obj: a.h a.h\n'):
            with self.subTest(raw=raw),self.assertRaises(evidence.Error):evidence.make_dependencies(raw)
    def test_actual_selected_dependency_and_wire(self):
        output=self.root/'pe/wow64';source=self.root/'source';tc=self.root/'tc'
        cpp=self.file('source/Source/Windows/Common/PearFEXMemory.cpp',b'// fixture\n')
        wire=self.file('wire/wine/pear_fex_memory.h',b'// authoritative fixture\n')
        name='Source/Windows/Common/CMakeFiles/CommonWindows.dir/PearFEXMemory.cpp.obj'
        row={'output':name,'file':str(cpp)}
        raw=(name+': '+str(cpp)+' '+str(wire)+'\n').encode()
        self.file('pe/wow64/'+name+'.d',raw)
        proof=evidence.dependency_proof(row,output,source,tc,{})
        self.assertIn(str(wire),proof['dependencies'])
        self.file('pe/wow64/'+name+'.d',(name+': '+str(cpp)+'\n').encode())
        with self.assertRaises(evidence.Error):evidence.dependency_proof(row,output,source,tc,{})
    def test_foreign_or_shadow_wire_dependency_refused(self):
        output=self.root/'pe/wow64';source=self.root/'source';tc=self.root/'tc'
        cpp=self.file('source/a.cpp',b'a');shadow=self.file('pe/wow64/generated/wine/pear_fex_memory.h',b'bad')
        row={'output':'CMakeFiles/a.dir/a.obj','file':str(cpp)}
        for header in (shadow,self.file('foreign/x.h',b'x')):
            raw=(row['output']+': '+str(cpp)+' '+str(header)+'\n').encode()
            self.file('pe/wow64/'+row['output']+'.d',raw)
            with self.subTest(header=header),self.assertRaises(evidence.Error):evidence.dependency_proof(row,output,source,tc,{})
    def macho(self,dependency=None,tail=b'',rpaths=()):
        commands=[]
        for kind,value in ((0xc,dependency),*((0x8000001c,item) for item in rpaths)):
            if value is None:continue
            raw=value.encode()+b'\0';length=(12+len(raw)+3)&~3
            commands.append(struct.pack('<III',kind,length,12)+raw+b'\0'*(length-12-len(raw)))
        command=b''.join(commands)
        return struct.pack('<8I',0xfeedfacf,evidence.byte_readers.MACH_ARM64,0,6,
                           len(commands),len(command),0,0)+command+tail
    def test_each_noncanonical_rpath_refused_before_normalization(self):
        for name in ('@loader_path/.','@loader_path//','@loader_path/../install',
                     '@executable_path/.','@executable_path//','/usr/lib/.','/usr/lib//',
                     '//usr/lib','@rpath','relative/path'):
            self.file('install/a.so',self.macho('@rpath/leaf.dylib',rpaths=(name,)))
            self.file('install/leaf.dylib',self.macho())
            with self.subTest(name=name),self.assertRaises(evidence.Error):
                evidence.rooted_native_closure(self.root,'install/a.so',self.root/'install')
    def test_canonical_loader_rpath_resolves_actual_owned_bytes(self):
        self.file('install/a.so',self.macho('@rpath/leaf.dylib',rpaths=('@loader_path',)))
        self.file('install/leaf.dylib',self.macho())
        rows=evidence.rooted_native_closure(self.root,'install/a.so',self.root/'install')
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['resolved_dependencies'][0]['path'],str(self.root/'install/leaf.dylib'))
    def test_noncanonical_unused_rpath_also_refused(self):
        self.file('install/a.so',self.macho(rpaths=('@loader_path/.',)))
        with self.assertRaises(evidence.Error):
            evidence.rooted_native_closure(self.root,'install/a.so',self.root/'install')
    def test_inherited_rpath_never_skips_raw_component_admission(self):
        self.file('install/a.so',self.macho('@rpath/b.dylib',rpaths=('@loader_path',)))
        self.file('install/b.dylib',self.macho('@rpath/leaf.dylib',rpaths=('@loader_path//',)))
        self.file('install/leaf.dylib',self.macho())
        with self.assertRaises(evidence.Error):
            evidence.rooted_native_closure(self.root,'install/a.so',self.root/'install')
    def test_each_noncanonical_system_dependency_refused(self):
        for name in ('/usr/lib/../../x.dylib','/System/Library/./x.dylib','/usr/lib//x.dylib','//usr/lib/x.dylib'):
            self.file('install/a.so',self.macho(name))
            with self.subTest(name=name),self.assertRaises(evidence.Error):
                evidence.rooted_native_closure(self.root,'install/a.so',self.root/'install')
    def test_canonical_system_dependency_is_external_input(self):
        self.file('install/a.so',self.macho('/usr/lib/libSystem.B.dylib'))
        row=evidence.rooted_native_closure(self.root,'install/a.so',self.root/'install')[0]
        self.assertEqual(row['resolved_dependencies'][0]['kind'],'macos_system_dependency')
    def test_installed_native_requires_real_linker_output_bytes_and_mode(self):
        self.file('native/libarm64ecfex.so',self.macho(),0o755)
        self.file('install/libarm64ecfex.so',self.macho(),0o755)
        with patch.object(evidence.original,'NATIVE_ARTIFACTS',{'install/libarm64ecfex.so':'arm64ec_native_unixlib'}):
            proof=evidence.native_artifacts(self.root)[0]
            self.assertEqual(proof['copy_origin']['path'],'native/libarm64ecfex.so')
            self.file('install/libarm64ecfex.so',self.macho(tail=b'changed'),0o755)
            with self.assertRaises(evidence.Error):evidence.native_artifacts(self.root)
            self.file('install/libarm64ecfex.so',self.macho(),0o644)
            with self.assertRaises(evidence.Error):evidence.native_artifacts(self.root)




class PortabilityAndHelperControls(OwnedFixture):
    """Synthetic read-only helper admission; the production digest stays pinned."""
    DATA=b'raise RuntimeError("helper must never execute")\n'
    def helper(self,name='proposal.py',data=None,mode=0o644):
        return self.file(name,self.DATA if data is None else data,mode)
    def pinned(self):
        return patch.object(evidence,'SOURCE_HELPER_SHA',H(self.DATA))
    def test_package_producers_are_supplied_repo_local(self):
        self.assertEqual(Path(evidence.__file__).resolve(),_repository/'tools/fex/memory_fex_check.py')
        self.assertEqual(Path(constructor.__file__).resolve(),_repository/'tools/fex/memory_fex_build.py')
        self.assertEqual(evidence.REPO,_repository)
        self.assertEqual(constructor.REPO,_repository)
    def test_standalone_imports_same_supplied_repository(self):
        previous=list(sys.path)
        try:
            check=runpy.run_path(str(_repository/'tools/fex/memory_fex_check.py'),run_name='pear_private_check_control')
            build=runpy.run_path(str(_repository/'tools/fex/memory_fex_build.py'),run_name='pear_private_build_control')
        finally:sys.path[:]=previous
        self.assertEqual(check['REPO'],_repository)
        self.assertEqual(build['REPO'],_repository)
        self.assertIs(build['verifier'],evidence)
        self.assertIs(check['original'],evidence.original)
    def test_pinned_python_text_read_without_execution(self):
        helper=self.helper()
        with self.pinned():reference=evidence.source_helper_reference(helper)
        self.assertEqual(reference,{'path':str(helper),'sha256':H(self.DATA),
                                   'size_bytes':len(self.DATA),'mode':0o644})
    def test_exact_historical_bytes_can_move(self):
        first=self.helper('first/proposal.py');second=self.helper('second/proposal.py')
        with self.pinned():
            a=evidence.source_helper_reference(first);b=evidence.source_helper_reference(second)
        self.assertNotEqual(a['path'],b['path'])
        self.assertEqual({k:a[k] for k in a if k!='path'},{k:b[k] for k in b if k!='path'})
    def test_wrong_digest_refused(self):
        helper=self.helper(data=b'different')
        with self.pinned(),self.assertRaises(evidence.Error):evidence.source_helper_reference(helper)
    def test_mode_change_refused(self):
        helper=self.helper(mode=0o600)
        with self.pinned(),self.assertRaises(evidence.Error):evidence.source_helper_reference(helper)
    def test_relative_input_refused(self):
        self.helper()
        with self.pinned(),self.assertRaises(evidence.Error):evidence.source_helper_reference('proposal.py')
    def test_raw_noncanonical_components_not_normalized(self):
        helper=self.helper('sub/proposal.py')
        for value in (str(helper.parent)+'/./proposal.py',str(helper.parent)+'//proposal.py',
                      str(helper.parent)+'/../sub/proposal.py','/'+str(helper)):
            with self.subTest(value=value),self.pinned(),self.assertRaises(evidence.Error):
                evidence.source_helper_reference(value)
    def test_leaf_symlink_refused(self):
        helper=self.helper();alias=self.root/'alias.py';alias.symlink_to(helper)
        with self.pinned(),self.assertRaises(evidence.Error):evidence.source_helper_reference(alias)
    def test_ancestor_symlink_refused(self):
        helper=self.helper('original/proposal.py');alias=self.root/'alias';alias.symlink_to(helper.parent)
        with self.pinned(),self.assertRaises(evidence.Error):evidence.source_helper_reference(alias/'proposal.py')
    def test_hardlink_refused(self):
        helper=self.helper();os.link(helper,self.root/'second.py')
        with self.pinned(),self.assertRaises(evidence.Error):evidence.source_helper_reference(helper)
    def test_bound_reference_exact_fields_types_and_bytes(self):
        helper=self.helper()
        with self.pinned():
            ref=evidence.source_helper_reference(helper)
            self.assertEqual(evidence.bound_source_helper(ref),helper)
            changed=[{**ref,'extra':False},{k:v for k,v in ref.items() if k!='mode'},
                     {**ref,'sha256':'0'*64},{**ref,'size_bytes':True},{**ref,'mode':True},
                     {**ref,'size_bytes':ref['size_bytes']+1},{**ref,'path':str(self.helper('other',b'other'))}]
            for row in changed:
                with self.subTest(row=row),self.assertRaises(evidence.Error):evidence.bound_source_helper(row)
    def test_current_helper_change_invalidates_bound_reference(self):
        helper=self.helper()
        with self.pinned():
            ref=evidence.source_helper_reference(helper);helper.write_bytes(b'changed')
            with self.assertRaises(evidence.Error):evidence.bound_source_helper(ref)
    def test_helper_snapshot_copy_and_current_original_are_exact(self):
        helper=self.helper();output=self.root/'output';output.mkdir()
        with self.pinned():
            ref=evidence.source_helper_reference(helper)
            rows=constructor.snapshot(output,[evidence.bound_source_helper(ref)])
            evidence.verify_snapshots(output,rows,[helper])
            (output/rows[0]['copy']).write_bytes(b'altered')
            with self.assertRaises(evidence.Error):evidence.verify_snapshots(output,rows,[helper])
    def test_replay_derives_explicit_helper_from_bound_reference(self):
        helper=self.helper();baseline=self.root/'baseline';projection=self.root/'projection';derivatives=self.root/'derivatives'
        with self.pinned():ref=evidence.source_helper_reference(helper)
        value={'schema_version':1,'record_kind':'fex_memory_modules_build','scope':'fex_component',
               'bindings':{'baseline':{'root':str(baseline),'sha256':evidence.BASE_BUILD_SHA},
                   'projection':{'root':str(projection),'control_sha256':'1'*64,
                       'source_manifest_sha256':evidence.PROJECTION_MANIFEST_SHA,'source_helper':ref},
                   'derivatives':{'root':str(derivatives),'sha256':evidence.GRAPH_SHA},'wine_build':{}},
               'producer_sha256':{},'input_snapshots':[],'materialized_source':{},'wire':{},'source_interfaces':{},
               'commands':[],'artifacts':[],'module_proofs':{},'resources':{},'output_manifest':{},
               'modules_built_not_loaded':True,'qualification':dict(evidence.QUALIFICATION),'passed':True,
               **dict.fromkeys(evidence.FALSE_FLAGS,False)}
        sentinel=evidence.Error('synthetic_stop_before_any_recipe_or_artifact')
        # Only the historical admission and unused enclosing build receipt are
        # doubles. The new bound-helper read and explicit replay argument run.
        with self.pinned(),patch.object(evidence,'operation_output',return_value=self.root), \
             patch.object(evidence,'LOCAL_PRODUCERS',()), \
             patch.object(evidence,'record_bytes',return_value=(value,b'fixture')), \
             patch.object(evidence.original,'verify_build',return_value={}), \
             patch.object(evidence,'sha256',return_value=evidence.BASE_BUILD_SHA), \
             patch.object(evidence,'projection_gate',side_effect=sentinel) as gate:
            with self.assertRaises(evidence.Error) as caught:
                evidence.verify_build(self.root,repo=self.root)
        self.assertIs(caught.exception,sentinel)
        gate.assert_called_once_with(projection,baseline,derivatives,source_helper=helper,expected_control_sha256='1'*64)
    def test_finite_snapshot_set_consumes_required_helper_input(self):
        helper=self.helper();fixture=self.file('native_fixture.cpp',b'fixture')
        metadata=self.file('host.json',b'{}');normalizer=self.file('normalizer.py',b'normalizer')
        old={'bindings':{'host_metadata':{'path':str(metadata)}},
             'cross':{'wine_roles':{'path':str(self.root/'roles.json')}}}
        graph={'normalization_helper':{'path':'normalizer.py'},'publication_series':{'path':'series.json'},'layers':[]}
        control={'commands':[]}
        def records(root,path):
            return (graph if path=='derivatives.json' else control,b'fixture')
        with self.pinned(),patch.object(evidence,'LOCAL_PRODUCERS',()), \
             patch.object(evidence.original,'FIXTURE',fixture), \
             patch.object(evidence.original,'PATCH_ROOT',self.root/'patches'), \
             patch.object(evidence.original,'patch_set',return_value={'patches':[]}), \
             patch.object(evidence,'load_json',return_value={'commands':[]}), \
             patch.object(evidence,'record_bytes',side_effect=records), \
             patch.object(evidence,'graph_path',side_effect=lambda root,ref,limit:Path(root)/ref['path']):
            paths=evidence.snapshot_sources(self.root,self.root/'baseline',self.root/'projection',
                self.root/'derivatives',self.root/'wine',old,source_helper=helper)
        self.assertIn(helper,paths)
        self.assertEqual(paths,sorted(set(paths),key=str))
    def test_required_helper_keyword_precedes_any_native_work(self):
        with patch.object(constructor.monitor,'execute',side_effect=AssertionError('native forbidden')) as execute:
            with self.assertRaises(TypeError):constructor.construct(*([self.root]*5),repo=self.root)
        execute.assert_not_called()




class CanonicalGraphControls(OwnedFixture):
    def reference(self,path,data):
        return {'path':path,'sha256':H(data),'size_bytes':len(data)}
    def test_root_relative_data_read_without_code_execution(self):
        raw=b'raise RuntimeError("data only")\n';self.file('graph/helpers/a.py',raw)
        ref=self.reference('helpers/a.py',raw)
        self.assertEqual(evidence.graph_input(self.root/'graph',ref,1024),raw)
        self.assertEqual(evidence.graph_path(self.root/'graph',ref,1024),self.root/'graph/helpers/a.py')
    def test_absolute_parent_dot_empty_and_double_component_refused(self):
        raw=b'x';self.file('graph/a',raw)
        for path in ('/a','../a','./a','a/../a','a//b','a/',''):
            with self.subTest(path=path),self.assertRaises(evidence.Error):
                evidence.graph_input(self.root/'graph',self.reference(path,raw),1024)
    def test_closed_reference_fields(self):
        raw=b'x';self.file('graph/a',raw);ref=self.reference('a',raw)
        for changed in ({**ref,'extra':False},{k:v for k,v in ref.items() if k!='sha256'},{**ref,'size_bytes':True}):
            with self.subTest(changed=changed),self.assertRaises(evidence.Error):evidence.graph_input(self.root/'graph',changed,1024)
    def test_current_graph_data_change_refused(self):
        raw=b'x';path=self.file('graph/a',raw);ref=self.reference('a',raw);path.write_bytes(b'y')
        with self.assertRaises(evidence.Error):evidence.graph_input(self.root/'graph',ref,1024)
    def test_graph_artifact_mode_change_refused(self):
        raw=b'x';self.file('graph/a',raw,0o600)
        with self.assertRaises(evidence.Error):evidence.graph_input(self.root/'graph',self.reference('a',raw),1024)
    def test_graph_symlink_leaf_and_ancestor_refused(self):
        raw=b'x';path=self.file('graph/sub/a',raw);(self.root/'graph/alias').symlink_to('sub')
        (self.root/'graph/sub/b').symlink_to('a')
        for name in ('alias/a','sub/b'):
            with self.subTest(name=name),self.assertRaises((evidence.Error,OSError)):
                evidence.graph_input(self.root/'graph',self.reference(name,raw),1024)
    def test_graph_hardlink_refused(self):
        raw=b'x';p=self.file('graph/a',raw);os.link(p,self.root/'graph/b')
        with self.assertRaises(evidence.Error):evidence.graph_input(self.root/'graph',self.reference('a',raw),1024)
    def test_actual_canonical_series_matches_thirteen_layer_graph(self):
        root=_repository/'runtime/fex/patches/memory/source-graph'
        graph=json.loads((root/'derivatives.json').read_text())
        series=evidence.publication_series_gate(root,graph)
        self.assertEqual(len(series['patches']),15)
        self.assertEqual(series['authoritative_header']['sha256'],evidence.WIRE_SHA)
        self.assertEqual((root/'memory-fex-series.json').read_bytes(),
                         (_repository/'runtime/fex/patches/memory-fex-series.json').read_bytes())
        for layer in graph['layers']:
            raw=evidence.graph_input(root,layer['strict_patch'],2*1024**2)
            git=evidence.graph_input(root,layer['git_derivative'],2*1024**2)
            self.assertEqual(git,evidence.render_declared_git(raw,layer['changes']))
    def changed_series_refused(self,mutate):
        root=_repository/'runtime/fex/patches/memory/source-graph'
        graph=json.loads((root/'derivatives.json').read_text())
        series=json.loads((root/'memory-fex-series.json').read_text());mutate(series)
        # Only input bytes for the named finite schema check are injected. The
        # production graph digest/current-byte admission remains mandatory.
        with patch.object(evidence,'graph_input',return_value=evidence.encoded(series)),self.assertRaises(evidence.Error):
            evidence.publication_series_gate(root,graph)
    def test_reordered_canonical_series_refused(self):
        self.changed_series_refused(lambda s:s['patches'].reverse())
    def test_abi_one_wire_series_refused(self):
        self.changed_series_refused(lambda s:s['authoritative_header'].update(sha256='2957188b00a74a46196341aa1237cf1cf44b375e5253c8bd9457bfc0d6b2aee1'))
    def test_missing_source_gate_fields_refused(self):
        self.changed_series_refused(lambda s:s.update(source_gates={}))
    def test_positive_source_runtime_gate_refused(self):
        self.changed_series_refused(lambda s:s['source_gates'].update(fex_initialization=True))
    def test_extra_publication_series_fields_refused(self):
        self.changed_series_refused(lambda s:s.update(unknown=False))
    def test_genuine_standalone_python_cli_help_imports_without_sibling_shadow(self):
        # Real fresh Python processes reproduce the script-directory sys.path
        # that an in-process runpy control cannot model. --help exits before
        # any build, verifier replay, Git call, source copy or initializer.
        env=dict(os.environ);env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
        for name in ('memory_fex_build.py','memory_fex_check.py','memory_fex_source.py'):
            argv=[sys.executable,'-B','-S',str(_repository/'tools/fex'/name),'--help']
            child=subprocess.run(argv,cwd=self.root,env=env,stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
            with self.subTest(name=name):
                self.assertEqual(child.returncode,0,child.stderr.decode(errors='replace'))
                self.assertIn(b'usage:',child.stdout)
                self.assertEqual(child.stderr,b'')




class CurrentProjectionControlControls(OwnedFixture):
    """Finite schema controls over explicit injected Git receipts, not Git runs.

    selected_projection and its two fixed source pins are narrowly injected for
    this small owned source fixture. Record/log/source reads and immutable
    receipt binding use the production functions. The separate genuine source
    CLI replay is recorded outside this portable suite.
    """
    def setUp(self):
        super().setUp()
        from contextlib import ExitStack
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.source=b'finite original source fixture\n'
        self.rows=[{'path':'fixture.cpp','sha256':H(self.source),'size_bytes':len(self.source),'mode':0o644}]
        self.manifest=evidence.encoded({'schema_version':1,'record_kind':'fex_materialized_source',
                                      'scope':'fex_component','files':self.rows})
        self.helper=self.file('helper.py',b'projection helper data only\n')
        self.stack.enter_context(patch.object(evidence,'SOURCE_HELPER_SHA',H(self.helper.read_bytes())))
        self.stack.enter_context(patch.object(evidence,'PROJECTION_MANIFEST_SHA',H(self.manifest)))
        self.derived={'scope':'source_only','source_files':self.rows,'layer_count':15}
        self.stack.enter_context(patch.object(evidence,'selected_projection',return_value=self.derived))
        self.git,_=evidence.regular_bytes(Path('/usr/bin'),'git',32*1024**2,system_git=True)
        self.derivatives=self.root/'graph'
        norm=b'normalizer data only\n';self.file('graph/normalization.py',norm)
        self.graph={'normalization_helper':{'path':'normalization.py','sha256':H(norm),'size_bytes':len(norm)},
                    'layers':[{'order':i,'git_derivative':{'path':f'git/{i:02d}.patch'}} for i in range(1,16)]}
        raw=evidence.encoded(self.graph);self.file('graph/derivatives.json',raw)
        self.stack.enter_context(patch.object(evidence,'GRAPH_SHA',H(raw)))
        self.proposal=evidence.encoded({'schema_version':1,'record_kind':'fex_memory_source_proposal','scope':'source_only',
            'baseline_manifest_sha256':evidence.BASE_SOURCE_SHA,'derivatives_manifest_sha256':H(raw),
            'files':self.rows,'materialization_performed':False,'compilation_performed':False})
        self.file('graph/final-source-proposal.json',self.proposal)
        self.baseline=self.root/'baseline'

    def receipt(self,name='projection',elapsed=7):
        root=self.root/name
        self.file(name+'/source/fixture.cpp',self.source)
        self.file(name+'/materialized-source.json',self.manifest)
        commands=[]
        for order in range(1,16):
            for action in ('check','apply'):
                row={'action':action,'layer':order,'argv':['/usr/bin/git','apply',*(['--check'] if action=='check' else []),
                     str(self.derivatives/f'git/{order:02d}.patch')],'cwd':str(root/'source'),
                     'attempted':True,'exit_code':0,'elapsed_ms':elapsed+order}
                for channel in ('stdout','stderr'):
                    data=b'' if channel=='stdout' else b'explicitly injected finite receipt log\n'
                    path=f'{order:02d}-{action}.{channel}';self.file(name+'/'+path,data)
                    row[channel]=path;row[channel+'_bytes']=len(data);row[channel+'_sha256']=H(data)
                commands.append(row)
        value={'schema_version':1,'record_kind':'fex_source_git_application_control','scope':'source_only','passed':True,
            'git_execution_performed':True,'compilation_performed':False,'module_initialization_performed':False,
            'owner_execution_performed':False,'guest_execution_performed':False,'stage3_complete':False,
            'layers':15,'changed_paths':36,'new_files':12,'inputs':{'baseline_manifest_sha256':evidence.BASE_SOURCE_SHA,
                'derivatives_sha256':evidence.GRAPH_SHA,'expected_manifest_sha256':H(self.proposal),
                'source_helper_sha256':evidence.SOURCE_HELPER_SHA},
            'git':{'path':'/usr/bin/git','sha256':H(self.git),'size_bytes':len(self.git)},'commands':commands,
            'baseline_unchanged_observed':True,'materialized_source_sha256':H(self.manifest),
            'source_files':len(self.rows),'source_bytes':len(self.source)}
        self.write(root,value)
        return root,value

    def write(self,root,value):
        (root/'control.json').write_bytes(evidence.encoded(value))

    def admit(self,root,expected=None):
        return evidence.projection_gate(root,self.baseline,self.derivatives,source_helper=self.helper,
                                        expected_control_sha256=expected)

    def refused(self,mutate):
        root,value=self.receipt();mutate(value);self.write(root,value)
        with self.assertRaises(evidence.Error):self.admit(root)

    def test_current_control_digest_is_returned_without_historical_success_pin(self):
        root,value=self.receipt();_,ref=self.admit(root)
        self.assertEqual(ref['control_sha256'],H((root/'control.json').read_bytes()))
        self.assertEqual(ref['source_manifest_sha256'],H(self.manifest))

    def test_different_current_paths_and_observed_elapsed_times_are_admissible(self):
        first,_=self.receipt('first',7);second,_=self.receipt('second',101)
        _,a=self.admit(first);_,b=self.admit(second)
        self.assertNotEqual(a['root'],b['root']);self.assertNotEqual(a['control_sha256'],b['control_sha256'])
        self.assertEqual(a['source_manifest_sha256'],b['source_manifest_sha256'])

    def test_successfully_bound_record_replays_immutably(self):
        root,_=self.receipt();_,ref=self.admit(root)
        _,again=self.admit(root,ref['control_sha256']);self.assertEqual(again,ref)

    def test_changed_successful_clock_record_refused_after_binding(self):
        root,value=self.receipt();_,ref=self.admit(root)
        value['commands'][0]['elapsed_ms']+=1;self.write(root,value)
        # Still admissible as a different current receipt, but never as the old
        # receipt already copied into an enclosing build.json binding.
        self.admit(root)
        with self.assertRaises(evidence.Error) as caught:self.admit(root,ref['control_sha256'])
        self.assertEqual(caught.exception.code,'fex_memory_projection_control_changed')

    def test_missing_current_control_refused(self):
        root,_=self.receipt();(root/'control.json').unlink()
        with self.assertRaises(OSError):self.admit(root)

    def test_omitted_control_field_refused(self):self.refused(lambda v:v.pop('source_bytes'))
    def test_extra_control_error_refused(self):self.refused(lambda v:v.update(primary_error={'code':'original_error'}))
    def test_extra_control_field_refused(self):self.refused(lambda v:v.update(unreviewed=True))
    def test_wrong_schema_scope_or_kind_refused(self):
        for key,value in [('schema_version',True),('scope','native'),('record_kind','unrelated')]:
            with self.subTest(key=key):
                root,v=self.receipt(key);v[key]=value;self.write(root,v)
                with self.assertRaises(evidence.Error):self.admit(root)
    def test_failed_or_unperformed_projection_refused(self):
        for key in ('passed','baseline_unchanged_observed','git_execution_performed'):
            with self.subTest(key=key):
                root,v=self.receipt(key);v[key]=False;self.write(root,v)
                with self.assertRaises(evidence.Error):self.admit(root)
    def test_native_or_initializer_overclaim_refused(self):
        for key in ('compilation_performed','module_initialization_performed','owner_execution_performed',
                    'guest_execution_performed','stage3_complete'):
            with self.subTest(key=key):
                root,v=self.receipt(key);v[key]=True;self.write(root,v)
                with self.assertRaises(evidence.Error):self.admit(root)
    def test_incorrect_source_count_or_bytes_refused(self):
        for key,value in [('source_files',True),('source_bytes',True),('source_files',2),('source_bytes',0)]:
            with self.subTest(key=key,value=value):
                root,v=self.receipt(key+str(value));v[key]=value;self.write(root,v)
                with self.assertRaises(evidence.Error):self.admit(root)
    def test_omitted_input_field_refused(self):self.refused(lambda v:v['inputs'].pop('source_helper_sha256'))
    def test_extra_git_reference_field_refused(self):self.refused(lambda v:v['git'].update(alternate='tool'))
    def test_incorrect_git_reference_type_refused(self):self.refused(lambda v:v['git'].update(size_bytes=True))
    def test_omitted_command_refused(self):self.refused(lambda v:v['commands'].pop())
    def test_omitted_command_field_refused(self):self.refused(lambda v:v['commands'][0].pop('elapsed_ms'))
    def test_command_error_field_refused(self):self.refused(lambda v:v['commands'][0].update(error={'exception_type':'OSError'}))
    def test_command_failed_or_unperformed_refused(self):
        for key,value in [('attempted',False),('exit_code',None),('exit_code',1),('exit_code',True),
                          ('elapsed_ms',-1),('elapsed_ms',True)]:
            with self.subTest(key=key,value=value):
                root,v=self.receipt(key+str(value));v['commands'][0][key]=value;self.write(root,v)
                with self.assertRaises(evidence.Error):self.admit(root)
    def test_original_command_path_is_required(self):self.refused(lambda v:v['commands'][0].update(cwd='/different/source'))
    def test_altered_log_bytes_refused(self):
        root,_=self.receipt();(root/'01-check.stderr').write_bytes(b'changed')
        with self.assertRaises(evidence.Error):self.admit(root)
    def test_altered_materialized_source_refused(self):
        root,_=self.receipt();(root/'source/fixture.cpp').write_bytes(b'changed')
        with self.assertRaises(evidence.Error):self.admit(root)
    def test_changed_manifest_identity_refused(self):
        root,_=self.receipt();(root/'materialized-source.json').write_bytes(self.manifest+b' ')
        with self.assertRaises(evidence.Error):self.admit(root)
    def test_verify_build_refuses_omitted_null_or_malformed_saved_control_digest_before_replay(self):
        helper=evidence.source_helper_reference(self.helper)
        value={'schema_version':1,'record_kind':'fex_memory_modules_build','scope':'fex_component',
            'bindings':{'baseline':{'root':str(self.baseline),'sha256':evidence.BASE_BUILD_SHA},
                'projection':{'root':str(self.root/'projection'),'control_sha256':'1'*64,
                    'source_manifest_sha256':evidence.PROJECTION_MANIFEST_SHA,'source_helper':helper},
                'derivatives':{'root':str(self.derivatives),'sha256':evidence.GRAPH_SHA},'wine_build':{}},
            'producer_sha256':{},'input_snapshots':[],'materialized_source':{},'wire':{},'source_interfaces':{},
            'commands':[],'artifacts':[],'module_proofs':{},'resources':{},'output_manifest':{},
            'modules_built_not_loaded':True,'qualification':dict(evidence.QUALIFICATION),'passed':True,
            **dict.fromkeys(evidence.FALSE_FLAGS,False)}
        original=value['bindings']['projection'].copy()
        for digest in (None,True,'0'*63,'g'*64,'omitted'):
            value['bindings']['projection']=original.copy()
            if digest=='omitted':value['bindings']['projection'].pop('control_sha256')
            else:value['bindings']['projection']['control_sha256']=digest
            # Enclosing baseline/build facts are explicit doubles. The actual
            # new saved-digest admission executes before any projection replay.
            with self.subTest(digest=digest),patch.object(evidence,'operation_output',return_value=self.root), \
                 patch.object(evidence,'LOCAL_PRODUCERS',()), \
                 patch.object(evidence,'record_bytes',return_value=(value,b'explicit build fixture')), \
                 patch.object(evidence.original,'verify_build',return_value={}), \
                 patch.object(evidence,'sha256',return_value=evidence.BASE_BUILD_SHA), \
                 patch.object(evidence,'projection_gate',side_effect=AssertionError('replay forbidden')) as gate:
                with self.assertRaises(evidence.Error):evidence.verify_build(self.root,repo=self.root)
            gate.assert_not_called()

    def test_omitted_or_invalid_saved_binding_cannot_authorize_replay(self):
        root,_=self.receipt()
        for value in ('',True,'0'*63,'g'*64,'0'*64):
            with self.subTest(value=value),self.assertRaises(evidence.Error):self.admit(root,value)

if __name__=='__main__':unittest.main()
