"""Portable full-module evidence gates and sanitized derivative controls."""
import struct
import shlex
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from tools.fex import build, verify
from tools.fex.common import Error


def pe_bytes():
    data=bytearray(1024);data[:2]=b'MZ';struct.pack_into('<I',data,60,128);data[128:132]=b'PE\0\0'
    struct.pack_into('<HH',data,132,0xaa64,1);struct.pack_into('<H',data,148,240);struct.pack_into('<H',data,150,0x2000)
    struct.pack_into('<H',data,152,0x20b);struct.pack_into('<I',data,152+108,16)
    at=152+240;data[at:at+8]=b'.rdata\0\0';struct.pack_into('<4I',data,at+8,512,4096,512,512);return data


class FullModuleDataTests(unittest.TestCase):
    def test_pe_header_rejects_truncation_and_non_dll(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'fixture.dll';path.write_bytes(pe_bytes())
            self.assertEqual(build.PE(path).machine,0xaa64)
            raw=pe_bytes();struct.pack_into('<H',raw,150,0);path.write_bytes(raw)
            with self.assertRaisesRegex(Error,'full_module_not_dll'):build.PE(path)
            path.write_bytes(b'MZ')
            with self.assertRaisesRegex(Error,'full_module_pe_header'):build.PE(path)

    def test_unmapped_or_ambiguous_data_cannot_be_read_as_exports(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'fixture.dll';raw=pe_bytes();struct.pack_into('<II',raw,152+112,8192,40);path.write_bytes(raw)
            with self.assertRaisesRegex(Error,'full_module_unmapped_rva'):build.PE(path).exports()
            pe=build.PE(path);pe.sections.append(pe.sections[0])
            with self.assertRaisesRegex(Error,'full_module_unmapped_rva'):pe.mapped(4096,4)

    def test_cmake_duplicate_setting_is_refused_instead_of_last_value_wins(self):
        self.assertEqual(build.cache_values(b'// comment\nFLAGS:STRING=exact\n'),{'FLAGS':'exact'})
        with self.assertRaisesRegex(Error,'full_cache_fields'):build.cache_values(b'FLAGS:STRING=first\nFLAGS:STRING=second\n')


class SpacedBuildRecipeTests(unittest.TestCase):
    def test_map_token_and_runtime_dll_locator_are_safe_in_spaced_worktree(self):
        root=Path('/owned/New project/.build/task5/fixture')
        lock={'sdk':{'path':'/SDK','version':'26.5'},'native_tools':{'clang++':{'path':'/Apple/clang++'}}}
        cross={'cross_tools':'/tools/New project/llvm-mingw','build_auxiliary_tools':{'python':{'path':'/python3'}}}
        commands=build.complete_recipe(root,Path('/tools/cmake'),lock,{'cache_line_bytes':128,'dcache_line_log2':5},{'cmake_options':{}},cross)
        for role,module in (('arm64ec','libarm64ecfex.dll'),('wow64','libwow64fex.dll')):
            flag=next(arg for arg in commands[role+'.configure'] if arg.startswith('-DCMAKE_SHARED_LINKER_FLAGS='))
            tokens=shlex.split(flag.split('=',1)[1])
            self.assertEqual([x for x in tokens if '/map:' in x],['-Wl,-Xlink=/map:link.map'])
            self.assertEqual(commands[role+'.inspect'][-1],str(root/'pe'/role/'Bin'/module))
            self.assertIn(str(root/'pe'/role),commands[role+'.build'])


class Stage2CompletionTests(unittest.TestCase):
    def test_native_only_build_cannot_pass_complete_stage(self):
        with mock.patch.object(build,'verify_build',return_value={'phase':'native','component_built':False}):
            with self.assertRaisesRegex(Error,'incomplete_stage2_module_build'):verify.verify_stage2('unused','unused')

    def test_failed_command_row_preserves_error_without_invented_exit_code(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);rows=[]
            def failure(argv,**kwargs):
                (kwargs['output_dir']/'stderr.bin').write_bytes(b'bounded source-build error')
                raise Error('command_output_limit')
            with mock.patch.object(build,'bounded_command',side_effect=failure):
                with self.assertRaisesRegex(Error,'command_output_limit'):build.run_command(root,'target.build',['qualified-tool'],{},rows)
            self.assertEqual(len(rows),1)
            self.assertIsNone(rows[0]['exit_code']);self.assertEqual(rows[0]['status'],'failed')
            self.assertEqual(rows[0]['error'],'command_output_limit');self.assertEqual(rows[0]['logs']['stderr']['size_bytes'],26)
            self.assertNotIn('stdout',rows[0]['logs'])

if __name__=='__main__':unittest.main()
