# SPDX-License-Identifier: MIT
"""Exercise the actual composed parser and diagnostic returns, without MAP_JIT."""
from pathlib import Path
import importlib.util,os,shutil,struct,subprocess,tempfile,unittest
from tools.wine.image_admission_inputs import read

HARNESS=r'''
#include <fcntl.h>
#include "pear_pe_arena.c"
_Static_assert(sizeof(struct pear_pe_plan) == 88, "Task 40 budget layout");
unsigned char __wine_dbg_get_channel_flags(struct __wine_debug_channel *channel) { return 0; }
const char *__wine_dbg_strdup(const char *text) { return text; }
int __wine_dbg_output(const char *text) { return 0; }
int __wine_dbg_header(enum __wine_debug_class cls, struct __wine_debug_channel *channel, const char *function) { return 0; }
int main(int argc, char **argv) {
    struct pear_pe_plan *plan = NULL;
    struct pear_pe_image image;
    int fd = open(argv[1], O_RDONLY);
    NTSTATUS status = pear_pe_plan_read_target(fd, IMAGE_FILE_MACHINE_ARM64, &plan, &image);
    printf("%08x\n", (unsigned)status);
    pear_pe_plan_free(plan);
    close(fd);
    return 0;
}
'''

class ImageAdmissionNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        declared=os.environ.get('PEAR_IMAGE_ADMISSION_BUILD')
        if not declared:raise unittest.SkipTest('set PEAR_IMAGE_ADMISSION_BUILD to the verified diagnostic build')
        cls.build=Path(declared).resolve(strict=True);v=read(cls.build/'build.json')
        inputs=read(Path(v['inputs_ref']['path']));cls.base=Path(inputs['native_build_ref']['path']).parent
        cls.scratch=tempfile.TemporaryDirectory(prefix='pear-image-parser-');cls.addClassCleanup(cls.scratch.cleanup)
        cls.root=Path(cls.scratch.name);cls.binaries={}
        spec=importlib.util.spec_from_file_location('pear_original_pe_fixture',Path(__file__).with_name('test_pe_arena.py'))
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);cls.fixture=staticmethod(mod.fixture)
        for kind,source in [('original',cls.base/'source/dlls/ntdll/unix'),('diagnostic',cls.build/'source/dlls/ntdll/unix')]:
            folder=cls.root/kind;folder.mkdir();(folder/'main.c').write_text(HARNESS)
            cc=['/usr/bin/clang','-O1','-std=gnu23','-fsanitize=undefined','-fno-sanitize-recover=all','-ffunction-sections','-Wl,-dead_strip',
                '-D__WINESRC__','-DWINE_UNIX_LIB','-I'+str(source),'-I'+str(cls.base/'objects/include'),'-I'+str(cls.base/'source/include'),
                str(folder/'main.c'),'-o',str(folder/'parser')]
            r=subprocess.run(cc,capture_output=True,text=True,timeout=60)
            if r.returncode:raise AssertionError(r.stderr)
            cls.binaries[kind]=folder/'parser'
    def run_fixture(self,data,enabled=True):
        p=self.root/'input.dll';p.write_bytes(data);env=dict(os.environ)
        env.pop('PEAR_STAGE3_CONTROL',None);env.pop('PEAR_IMAGE_ADMISSION_DIAGNOSTIC',None)
        if enabled:env['PEAR_IMAGE_ADMISSION_DIAGNOSTIC']='1'
        result={}
        for kind,exe in self.binaries.items():
            r=subprocess.run([str(exe),str(p)],capture_output=True,text=True,env=env,timeout=15)
            self.assertEqual(r.returncode,0,r.stderr);result[kind]=r
        self.assertEqual(result['original'].stdout,result['diagnostic'].stdout)
        return result['diagnostic']
    def test_size_refusal(self):
        data=self.fixture();struct.pack_into('<I',data,0x98+56,57647104)
        r=self.run_fixture(data);self.assertEqual(r.stdout.strip(),'c00000bb');self.assertIn('phase=parser.return08',r.stderr)
    def test_earlier_flags_win(self):
        data=self.fixture();struct.pack_into('<I',data,0x98+56,57647104);struct.pack_into('<H',data,0x80+22,0x2002)
        r=self.run_fixture(data);self.assertEqual(r.stdout.strip(),'c00000bb');self.assertIn('phase=parser.return06',r.stderr);self.assertNotIn('phase=parser.return08',r.stderr)
    def test_opt_out_keeps_status(self):
        data=self.fixture();struct.pack_into('<I',data,0x98+56,57647104)
        r=self.run_fixture(data,False);self.assertEqual(r.stdout.strip(),'c00000bb');self.assertEqual(r.stderr,'')

if __name__=='__main__':unittest.main()
