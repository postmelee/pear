"""Actual staged PE role parser checks, with no MAP_JIT or Wine execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.fex.build import apply_hunks, patch_sections

spec = importlib.util.spec_from_file_location('pear_native_pe_fixtures', ROOT/'tests/wine/test_pe_arena.py')
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
BASE = ROOT/'.build/task5/stage3-wine-build11'
PATCHES = ROOT/'runtime/fex/patches/integration'
H = lambda data: hashlib.sha256(data).hexdigest()

HARNESS = original.HARNESS.split('static int admission(')[0] + r'''
int main(int argc, char **argv)
{
    struct pear_pe_plan *plan = NULL;
    struct pear_pe_image image = {0};
    int fd = open(argv[1], O_RDONLY);
    NTSTATUS status = fd < 0 ? STATUS_OBJECT_NAME_NOT_FOUND :
        pear_pe_plan_read_target(fd, strtoul(argv[2], NULL, 0), &plan, &image);
    if (fd >= 0) close(fd);
    printf("%08x %u %u\n", (unsigned)status, (unsigned)image.role, image.native_entry_rva);
    pear_pe_plan_free(plan);
    return 0;
}
'''


def ec_fixture(version=1):
    data = original.cookie_fixture(length=208, directory_size=208, destination=0)
    struct.pack_into('<H', data, 0x84, 0x8664)
    struct.pack_into('<I', data, 0x98+16, 0x1100)
    struct.pack_into('<Q', data, 0x480+200, original.BASE+0x2020)
    data[0x420:0x470] = bytes(80)
    struct.pack_into('<III', data, 0x420, version, 0x2160, 2)
    struct.pack_into('<I', data, 0x420+16, 0x2170)
    struct.pack_into('<I', data, 0x420+52, 1)
    struct.pack_into('<IIII', data, 0x560, 0x1001, 64, 0x1102, 16)
    struct.pack_into('<II', data, 0x570, 0x1100, 0x1000)
    struct.pack_into('<H', data, 0x608, 0xA148)
    return data


class IntegratedPERoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('clang') or not (BASE/'objects/include/config.h').is_file():
            raise unittest.SkipTest('pinned Wine headers/native clang unavailable')
        cls.temp = tempfile.TemporaryDirectory(prefix='pear-role-parser-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.folder = Path(cls.temp.name)
        manifest = json.loads((PATCHES/'series.json').read_text())
        if H((BASE/'build.json').read_bytes()) != manifest['base_wine_build_sha256']:
            raise AssertionError('Wine baseline identity changed')
        outputs = {}
        for patch in manifest['patches']:
            raw = (PATCHES/patch['file']).read_bytes()
            if H(raw) != patch['sha256']: raise AssertionError('patch identity changed')
            sections = patch_sections(raw)
            if set(sections) != {row['path'] for row in patch['sources']}:
                raise AssertionError('patch source closure differs')
            for row in patch['sources']:
                before = outputs.get(row['path'], (BASE/'source'/row['path']).read_bytes())
                if H(before) != row['preimage_sha256']: raise AssertionError('source identity changed')
                after = apply_hunks(before, sections[row['path']], row['path'])
                if H(after) != row['postimage_sha256']: raise AssertionError('derived source differs')
                outputs[row['path']] = after
        for path, raw in outputs.items(): (cls.folder/Path(path).name).write_bytes(raw)
        (cls.folder/'main.c').write_text(HARNESS)
        command = ['/usr/bin/arch','-arm64',shutil.which('clang'),'-std=gnu23',
                   '-fsanitize=undefined','-fno-sanitize-recover=all','-D__WINESRC__','-DWINE_UNIX_LIB',
                   '-I'+str(BASE/'objects/include'),'-I'+str(BASE/'source/include'),
                   '-I'+str(BASE/'source/dlls/ntdll/unix'),
                   str(cls.folder/'main.c'),'-o',str(cls.folder/'parser')]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode: raise AssertionError(result.stderr)

    def parse(self, data, target=0x8664):
        path=self.folder/'input.dll';path.write_bytes(data)
        result=subprocess.run([str(self.folder/'parser'),str(path),hex(target)],
                              capture_output=True,text=True,timeout=10,check=True)
        self.assertEqual(result.stderr,'')
        return tuple(int(word,16 if i==0 else 10) for i,word in enumerate(result.stdout.split()))

    def test_native_and_guest_are_distinct(self):
        data=original.fixture()
        self.assertEqual(self.parse(data,0xaa64)[:2],(0,1))
        self.assertNotEqual(self.parse(data)[0],0)
        struct.pack_into('<H',data,0x84,0x8664)
        self.assertEqual(self.parse(data)[:2],(0,3))
        self.assertNotEqual(self.parse(data,0xaa64)[0],0)

    def test_ec_versions_and_redirected_entry(self):
        for version in (1,2):
            with self.subTest(version=version):
                self.assertEqual(self.parse(ec_fixture(version)),(0,2,0x1000))

    def test_malformed_metadata_and_native_only_refusal(self):
        self.assertNotEqual(self.parse(ec_fixture(),0xaa64)[0],0)
        mutations=[(0x420,'I',9),(0x424,'I',0xfffffff0),(0x428,'I',0xffffffff),
                   (0x560,'I',0x1003),(0x568,'I',0x1022),(0x56c,'I',0xffffffff),
                   (0x574,'I',0x1100),(0x420+28,'I',0x1000),(0x480+200,'Q',original.BASE-1)]
        for offset,fmt,value in mutations:
            with self.subTest(offset=offset,value=value):
                data=ec_fixture();struct.pack_into('<'+fmt,data,offset,value)
                self.assertNotEqual(self.parse(data)[0],0)

    def test_recorded_wine_arm64x_and_invalid_fixup(self):
        roles=json.loads((ROOT/'.build/task5/stage1-wine-roles.json').read_text())
        path=Path(roles['companion'])/'install/lib/wine/aarch64-windows/ntdll.dll'
        if not path.is_file():self.skipTest('recorded Wine companion unavailable')
        data=path.read_bytes()
        self.assertEqual(self.parse(data)[:2],(0,2))
        self.assertEqual(self.parse(data,0xaa64)[:2],(0,1))
        paired=ROOT/'.build/task5/integration-paired7/ntdll.dll'
        if paired.is_file():
            self.assertEqual(self.parse(paired.read_bytes())[:2],(0,2))
            self.assertEqual(self.parse(paired.read_bytes(),0xaa64)[:2],(0,1))
        # Corrupt the first fixup target to a structural DOS-header field;
        # the staged selector must reject it before applying any relocation.
        changed=bytearray(data);pe=struct.unpack_from('<I',data,60)[0];opt=pe+24
        sections=[]
        for i in range(struct.unpack_from('<H',data,pe+6)[0]):
            vs,rva,size,raw=struct.unpack_from('<IIII',data,opt+240+i*40+8)
            sections.append((rva,vs,raw,size))
        def mapped(rva):
            for address,span,raw,size in sections:
                if address<=rva<address+size:return raw+rva-address
            raise AssertionError('unmapped fixture RVA')
        cfg=struct.unpack_from('<I',data,opt+112+10*8)[0]
        offset,section=struct.unpack_from('<IH',data,mapped(cfg)+224)
        first=mapped(sections[section-1][0]+offset)+8+12+8
        word=struct.unpack_from('<H',data,first)[0]
        struct.pack_into('<H',changed,first,word & 0xf000)
        self.assertNotEqual(self.parse(changed)[0],0)

    def test_recorded_fex_module(self):
        path=ROOT/'.build/task5/stage3-fex-modules14/pe/arm64ec/Bin/libarm64ecfex.dll'
        if not path.is_file():self.skipTest('recorded FEX module unavailable')
        # Keep the baseline per-image arena cap; debug-only sections are not a
        # runtime input. Preserve the original full module and its symbols.
        inspect=json.loads((ROOT/'.build/task5/stage3-fex-modules14/logs/arm64ec.inspect/command.json').read_text())
        strip=Path(inspect['argv'][2]).with_name('llvm-strip')
        deployment=self.folder/'fex-deployment.dll'
        deployment.write_bytes(path.read_bytes())
        subprocess.run(['/usr/bin/arch','-arm64',str(strip),'--strip-debug',str(deployment)],
                       capture_output=True,text=True,check=True,timeout=30)
        self.assertEqual(self.parse(deployment.read_bytes())[:2],(0,2))
        integrated=ROOT/'.build/task5/integration-fex-link10/deployment.dll'
        if integrated.is_file():self.assertEqual(self.parse(integrated.read_bytes())[:2],(0,2))

    def test_original_x64_dispatch_fixture(self):
        fixture=ROOT/'.build/task5/integration-first-dispatch1/first-dispatch.exe'
        if not fixture.is_file():self.skipTest('first-dispatch build unavailable')
        self.assertEqual(self.parse(fixture.read_bytes())[:2],(0,3))
        self.assertNotEqual(self.parse(fixture.read_bytes(),0xaa64)[0],0)

if __name__=='__main__':unittest.main()
