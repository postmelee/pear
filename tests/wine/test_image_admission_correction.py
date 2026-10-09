# SPDX-License-Identifier: MIT
"""Exercise corrected composed C under UBSan, without claiming JIT publication."""
from pathlib import Path
import importlib.util, os, struct, subprocess, tempfile, unittest
from tools.wine.image_admission_correction_build import admit
from tools.wine.image_admission_inputs import read
spec=importlib.util.spec_from_file_location('original_pe_tests',Path(__file__).with_name('test_pe_arena.py'))
original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)

class CorrectedParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        declared=os.environ.get('PEAR_IMAGE_CORRECTION_BUILD')
        if not declared:raise unittest.SkipTest('explicit corrected build required')
        cls.build=Path(declared).resolve();record=admit(cls.build)
        base=Path(read(Path(record['inputs_ref']['path']))['native_build_ref']['path']).parent
        cls.scratch=tempfile.TemporaryDirectory(prefix='pear-corrected-parser-');cls.addClassCleanup(cls.scratch.cleanup)
        cls.folder=Path(cls.scratch.name)
        (cls.folder/'main.c').write_text(original.HARNESS)
        args=['/usr/bin/clang','-O1','-std=gnu23','-fsanitize=undefined','-fno-sanitize-recover=all','-ffunction-sections','-Wl,-dead_strip',
              '-D__WINESRC__','-DWINE_UNIX_LIB','-I'+str(cls.build/'source/dlls/ntdll/unix'),
              '-I'+str(base/'objects/include'),'-I'+str(base/'source/include'),str(cls.folder/'main.c'),'-o',str(cls.folder/'parser')]
        result=subprocess.run(args,capture_output=True,text=True,timeout=60)
        if result.returncode:raise AssertionError(result.stderr)
    parse=original.NativePEParserTests.parse
    def test_required_size_ceiling_and_next_alignment(self):
        for size,expected in ((57647104,'00000000'),(67108864,'00000000'),(67112960,'c00000bb'),(0xfffff000,'c00000bb')):
            data=original.fixture();struct.pack_into('<I',data,0x98+56,size)
            with self.subTest(size=size):self.assertEqual(self.parse(data)[0],expected)

# Reuse the existing meaningful parser, relocation and finite-owner controls.
for name in ('test_original_fixture_and_relocation','test_compatible_reuse_stale_generation_and_bounded_exhaustion',
             'test_native_relocation_updates_code_and_data_at_two_bases','test_truncated_file_extents',
             'test_misaligned_negative_and_outside_nt_header','test_wrong_machine_optional_header_and_image_bound',
             'test_section_and_raw_overlap_and_declared_extent','test_unsupported_and_overlapping_relocations',
             'test_invalid_relocation_blocks_cannot_loop_or_escape','test_zero_fill_and_absolute_padding_are_allowed',
             'test_iat_cannot_alias_executable_page','test_security_directory_is_checked_as_file_extent',
             'test_unsafe_fixed_base_and_dynamic_hybrid_are_rejected'):
    setattr(CorrectedParserTests,name,getattr(original.NativePEParserTests,name))
if __name__=='__main__':unittest.main()
