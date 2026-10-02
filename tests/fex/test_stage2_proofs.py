"""Portable source-object/link evidence parsing; no compiler or PE execution."""
import json
import shlex
import struct
import tempfile
from pathlib import Path
import unittest
from unittest import mock
from tools.fex import build
from tools.fex.common import Error


def command_row(output, source, tools, extra=()):
    path=source/'Common/CPUFeatures.cpp'
    args=[str(tools/'bin/arm64ec-w64-mingw32-clang++'),'-DPEAR_FEX_DARWIN=1','-DPEAR_FEX_DARWIN_DCACHE_LOG2=5',
          '-fno-exceptions','-fno-strict-aliasing',*extra,'-o','Common/CPUFeatures.cpp.obj','-c',str(path)]
    return {'directory':str(output),'file':str(path),'output':'Common/CPUFeatures.cpp.obj','command':shlex.join(args)}


def map_text(aliases=()):
    owners=[('DllMainCRTStartup','libCommonWindowsRuntime','CRT.cpp.obj'),
            ('_ZN3FEX7Windows12DarwinPolicy5ApplyEv','libCommonWindows','DarwinConfigPolicy.cpp.obj'),
            ('GetSystemInfo','libCommonWindowsRuntime','Misc.cpp.obj'),
            ('NtQuerySystemInformation','libntdll_ex','ntdll.dll'),*aliases]
    return '\n'.join(f' 0001:00000004       #{name} 0000000180001004     {archive}:{member}' for name,archive,member in owners)


def export_bytes():
    data=bytearray(1024);data[:2]=b'MZ';struct.pack_into('<I',data,60,128);data[128:132]=b'PE\0\0'
    struct.pack_into('<HH',data,132,0xaa64,1);struct.pack_into('<H',data,148,240);struct.pack_into('<H',data,150,0x2000)
    struct.pack_into('<H',data,152,0x20b);struct.pack_into('<I',data,152+108,16)
    at=392;data[at:at+8]=b'.rdata\0\0';struct.pack_into('<4I',data,at+8,512,4096,512,512)
    struct.pack_into('<II',data,152+112,4096,80)
    struct.pack_into('<5I',data,512+20,2,1,4200,4210,4220)
    struct.pack_into('<2I',data,616,4350,0);struct.pack_into('<I',data,626,4230);struct.pack_into('<H',data,636,0)
    data[646:650]=b'Run\0'
    return data


class CompileEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.output=Path('/owned/New project/pe/arm64ec');self.source=Path('/owned/New project/source');self.tools=Path('/tool New project')

    def proof(self,row):
        return build.compile_command_proof(row,self.output,self.source,self.tools,'arm64ec-w64-mingw32',{'dcache_line_log2':5})

    def test_exact_operands_and_effective_macros_bind_spaced_paths(self):
        self.assertEqual(self.proof(command_row(self.output,self.source,self.tools)),self.output/'Common/CPUFeatures.cpp.obj')
        for extra,error in ((['-UPEAR_FEX_DARWIN'],'full_compile_policy_define'),
                            (['-DPEAR_FEX_DARWIN=0'],'full_compile_policy_define'),
                            (['-U','PEAR_FEX_DARWIN_DCACHE_LOG2'],'full_compile_cache_define'),
                            (['-DPEAR_FEX_DARWIN_DCACHE_LOG2=6'],'full_compile_cache_define'),
                            (['-fexceptions'],'full_compile_language_policy'),
                            (['--target','aarch64-w64-mingw32'],'full_compile_unreviewed_target_override'),
                            (['-ooutside.obj'],'full_compile_unreviewed_output_override'),
                            (['-Wp,-UPEAR_FEX_DARWIN'],'full_compile_unreviewed_preprocessor_override')):
            with self.subTest(extra=extra),self.assertRaisesRegex(Error,error):self.proof(command_row(self.output,self.source,self.tools,extra))

    def test_output_traversal_wrong_compiler_and_missing_operand_are_refused(self):
        row=command_row(self.output,self.source,self.tools);row['output']='../outside.obj'
        with self.assertRaises(Error):self.proof(row)
        row=command_row(self.output,self.source,self.tools);row['command']=row['command'].replace('arm64ec-w64-mingw32-clang++','aarch64-w64-mingw32-clang++')
        with self.assertRaisesRegex(Error,'full_compile_triple_compiler'):self.proof(row)
        row=command_row(self.output,self.source,self.tools);row['command']=row['command'].rsplit(' -c ',1)[0]+' -c'
        with self.assertRaisesRegex(Error,'full_compile_operand_count'):self.proof(row)

    def test_only_current_empty_output_module_map_can_be_admitted(self):
        with tempfile.TemporaryDirectory(prefix='pear space ') as temp:
            output=Path(temp);source=output/'source';tools=output/'tools'
            module_map=output/'Common/CPUFeatures.cpp.obj.modmap';module_map.parent.mkdir();module_map.write_bytes(b'')
            row=command_row(output,source,tools,['@Common/CPUFeatures.cpp.obj.modmap'])
            self.assertEqual(build.compile_command_proof(row,output,source,tools,'arm64ec-w64-mingw32',{'dcache_line_log2':5}),output/'Common/CPUFeatures.cpp.obj')
            module_map.write_bytes(b'-UPEAR_FEX_DARWIN')
            with self.assertRaisesRegex(Error,'full_compile_nonempty_module_map'):build.compile_command_proof(row,output,source,tools,'arm64ec-w64-mingw32',{'dcache_line_log2':5})
            row=command_row(output,source,tools,['@unreviewed.rsp'])
            with self.assertRaisesRegex(Error,'full_compile_unreviewed_response'):build.compile_command_proof(row,output,source,tools,'arm64ec-w64-mingw32',{'dcache_line_log2':5})


class CompileDatabaseReaderTests(unittest.TestCase):
    def test_cmake_array_is_accepted_without_changing_record_only_owner(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);row=command_row(root,root/'source',root/'tools')
            path=root/'compile_commands.json';path.write_text(json.dumps([row]))
            self.assertEqual(build.compile_database(root),[row])
            with self.assertRaisesRegex(Error,'invalid_document_shape'):build.load_json(path)

    def test_non_array_injection_duplicate_keys_and_wrong_row_types_are_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);path=root/'compile_commands.json';row=command_row(root,root/'source',root/'tools')
            cases=[('{}','full_compile_database'),('[]','full_compile_database'),
                   ('[],"extra":true','full_compile_database_envelope'),
                   ('[{"directory":"one","directory":"two"}]','duplicate_json_key'),
                   (json.dumps([{**row,'command':False}]),'full_compile_database_types'),
                   (json.dumps([{**row,'unsupported_field':'extra'}]),'full_compile_database_fields')]
            for raw,error in cases:
                path.write_text(raw)
                with self.subTest(error=error),self.assertRaisesRegex(Error,error):build.compile_database(root)

    def test_artifact_byte_budget_is_enforced_before_decoding(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'compile_commands.json').write_bytes(b' '*(4*1024**2+1))
            with self.assertRaisesRegex(Error,'input_size_limit'):build.compile_database(root)


class SourceMapTests(unittest.TestCase):
    def test_selected_and_unselected_aliases_are_reported_without_forcing_members(self):
        result=build.source_map_proof(map_text())
        self.assertEqual(set(result['provider_aliases'].values()),{'unselected'})
        result=build.source_map_proof(map_text([('__imp_GetSystemInfo','libCommonWindowsRuntime','Misc.cpp.obj')]))
        self.assertEqual(result['provider_aliases']['__imp_GetSystemInfo'],'selected_source_owner')
        self.assertEqual(result['required_symbols']['NtQuerySystemInformation'],{'archive':'libntdll_ex','member':'ntdll.dll'})

    def test_symbol_text_without_exact_source_member_owner_is_insufficient(self):
        for value in (map_text().replace('libCommonWindowsRuntime:Misc.cpp.obj','kernel32:unrelated.obj'),
                      map_text().replace('NtQuerySystemInformation','SomeOtherQuery'),
                      map_text([('__imp_aux_GetSystemInfo','libCommonWindows','Other.cpp.obj')])):
            with self.subTest(value=value),self.assertRaises(Error):build.source_map_proof(value)


class ExportClosureTests(unittest.TestCase):
    def test_ordinal_only_nonzero_export_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'module.dll';raw=export_bytes();path.write_bytes(raw)
            self.assertEqual(build.PE(path).exports(),{'Run':4350})
            struct.pack_into('<I',raw,620,4360);path.write_bytes(raw)
            with self.assertRaisesRegex(Error,'full_module_ordinal_export'):build.PE(path).exports()

    def test_nonzero_delay_import_directory_is_refused_before_module_admission(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'module.dll';raw=export_bytes();struct.pack_into('<II',raw,152+112+13*8,4250,32);path.write_bytes(raw)
            with self.assertRaisesRegex(Error,'full_module_delay_import'):build.module_facts(path,Path(temp),'wow64')


class NinjaEdgeTests(unittest.TestCase):
    def test_ninja_escapes_are_bounded_and_unexpanded(self):
        self.assertEqual(build.ninja_tokens('path/New$ project.a $$literal $:colon'),['path/New project.a','$literal',':colon'])
        with self.assertRaisesRegex(Error,'full_ninja_unreviewed_variable'):build.ninja_tokens('$UNREVIEWED')

    def test_actual_target_edge_binds_objects_archives_and_relative_map(self):
        with tempfile.TemporaryDirectory(prefix='pear space ') as temp:
            root=Path(temp);output=root/'pe';source=root/'source';tools=root/'tools'
            archives=['Source/Windows/Common/libCommonWindowsRuntime.a','Source/Windows/Common/libCommonWindows.a','Source/Windows/libntdll_ex.a']
            for name in archives:
                path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'parser-only archive bytes')
            object_path=output/'Module.cpp.obj'
            flags=['-static','-Wl,--file-alignment=4096,/mllvm:-align-loops=1','-Wl,-Xlink=/map:link.map','-static','-nostdlib','-nostartfiles','-nodefaultlibs','-lc++abi','-lc++','-lunwind',str(source/'Source/Windows/ARM64EC/libarm64ecfex.def')]
            text='build Bin/libarm64ecfex.dll module.dll.a: CXX_SHARED_LIBRARY_LINKER__module_R Module.cpp.obj | '+' '.join(archives)+'\n  LINK_FLAGS = '+shlex.join(flags)+'\n  LINK_LIBRARIES = '+' '.join(archives)+'\n  TARGET_FILE = Bin/libarm64ecfex.dll\n'
            with mock.patch.object(build,'archive_machines',return_value={'parser_test_only':True}):
                result=build.full_link_edge(text,output,source,'libarm64ecfex.dll',{str(object_path)},tools)
                self.assertEqual(result['working_directory'],str(output));self.assertEqual(result['objects'],[str(object_path)])
                with self.assertRaisesRegex(Error,'full_link_flags'):build.full_link_edge(text.replace('/map:link.map','/map:outside.map'),output,source,'libarm64ecfex.dll',{str(object_path)},tools)
                with self.assertRaisesRegex(Error,'full_link_object_not_built'):build.full_link_edge(text,output,source,'libarm64ecfex.dll',set(),tools)
                changed=text.replace(' | '+' '.join(archives),' | '+' '.join(archives[:-1]))
                with self.assertRaisesRegex(Error,'full_link_archive_edge_closure'):build.full_link_edge(changed,output,source,'libarm64ecfex.dll',{str(object_path)},tools)


if __name__=='__main__':unittest.main()
