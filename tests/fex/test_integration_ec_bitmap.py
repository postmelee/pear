"""Exercise the actual Wine EC callback with controlled VM/error responses.

This checks refusal/error semantics; real mapping, pin and recycling evidence
comes from the separately signed, test-instrumented FEX lifecycle execution.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'.build/task5/integration-paired5/virtual.c'
PREAMBLE = r'''
#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
typedef size_t SIZE_T;
typedef int32_t NTSTATUS;
#define PEAR_FEX_ROLE_ARM64EC 1
#define PEAR_ARENA_MAPPING_BYTES 65536
#define PEAR_FEX_PROTECTION_RX 2
#define VPROT_READ 1
#define VPROT_WRITE 2
#define VPROT_COMMITTED 4
#define PROT_READ 1
#define PROT_WRITE 2
#define STATUS_INVALID_PARAMETER (-10)
#define STATUS_ACCESS_DENIED (-11)
#define ROUND_ADDR(p,m) ((void *)((uintptr_t)(p) & ~(uintptr_t)(m)))
#define ROUND_SIZE(p,s,m) (((uintptr_t)(p)+(s)+(m)) / ((m)+1) * ((m)+1) - ((uintptr_t)(p)&~(uintptr_t)(m)))
struct pear_fex_memory_error { uint32_t domain; int32_t code; };
struct pear_fex_view_record { uint32_t role; uint64_t generation; void *base; SIZE_T size; } record;
struct file_view { unsigned pear_owned; uint64_t pear_generation; void *base; SIZE_T size; } target, bitmap, *arm64ec_view=&bitmap;
struct {uint64_t private_base,owner_pid;} pear_fex_wine_backing;
static const SIZE_T page_mask=4095, page_shift=12;
static int virtual_mutex, ec_process, bad_view, allocation_failure, vprot_failure, protect_failure, query_failure, bits_failure;
static unsigned allocations, changes, locks;
static unsigned char storage[16384];
static int is_arm64ec(void) {return ec_process;}
static void server_enter_uninterrupted_section(int *m,sigset_t *s) {(void)m;(void)s;++locks;}
static void server_leave_uninterrupted_section(int *m,sigset_t *s) {(void)m;(void)s;--locks;}
static struct pear_fex_view_record *pear_fex_view_at(void *p,SIZE_T s) {(void)p;(void)s;return bad_view?NULL:&record;}
static struct file_view *find_view(void *p,SIZE_T s) {(void)p;(void)s;return &target;}
static NTSTATUS pear_fex_checked_bitmap_allocate(void) {++allocations;return allocation_failure?-20:0;}
static int set_vprot(struct file_view *v,void *p,SIZE_T n,int flags) {(void)v;(void)p;(void)n;(void)flags;return !vprot_failure;}
static void pear_fex_nt_error(struct pear_fex_memory_error *e,NTSTATUS s) {e->domain=2;e->code=s;}
static int pear_fex_bitmap_protection(void *p,SIZE_T n,int flags,struct pear_fex_memory_error *e) {
 (void)p;(void)n;(void)flags;if(protect_failure){pear_fex_nt_error(e,-21);return 1;}return 0;
}
static int pear_fex_backing_query(uint64_t a,uint64_t n,int flags,struct pear_fex_memory_error *e) {
 (void)a;(void)n;(void)flags;if(query_failure){pear_fex_nt_error(e,-22);return 1;}return 0;
}
static void change(void *p,SIZE_T n,int value) {
 ++changes;for(uintptr_t page=(uintptr_t)p>>12;page<((uintptr_t)p+n)>>12;++page){
 unsigned char *b=storage+page/8;if(value)*b|=1u<<(page&7);else *b&=~(1u<<(page&7));}
}
static void set_arm64ec_range(void *p,SIZE_T n) {change(p,n,1);}
static void clear_arm64ec_range(void *p,SIZE_T n) {change(p,n,0);}
static int pear_fex_bitmap_bits(void *p,SIZE_T n,int expected) {
 if(bits_failure)return 0;
 for(uintptr_t page=(uintptr_t)p>>12;page<((uintptr_t)p+n)>>12;++page)
  if(((storage[page/8]>>(page&7))&1)!=expected)return 0;
 return 1;
}
'''
HARNESS = r'''
static void reset(void) {
 memset(storage,0,sizeof(storage));ec_process=1;bad_view=allocation_failure=vprot_failure=protect_failure=query_failure=bits_failure=0;
 allocations=changes=locks=0;pear_fex_wine_backing.private_base=0x10000000;pear_fex_wine_backing.owner_pid=getpid();
 record=(struct pear_fex_view_record){1,7,(void*)0x10000000,65536};target=(struct file_view){4,7,(void*)0x10000000,65536};
 bitmap=(struct file_view){0,0,storage,sizeof(storage)};
}
static void refused(uint64_t offset,uint64_t size,int code) {
 struct pear_fex_memory_error e={0};assert(pear_fex_wine_ec_register(offset,size,1,&e));
 assert(e.domain==2&&e.code==code&&!locks&&!changes);
}
int main(void) {
 struct pear_fex_memory_error e={0};
 reset();change((void*)0x10001000,4096,1);changes=0;
 assert(!pear_fex_wine_ec_register(0,4096,1,&e)&&!e.domain&&!locks);
 assert(pear_fex_bitmap_bits((void*)0x10000000,8192,1));
 assert(!pear_fex_wine_ec_register(0,4096,0,&e)&&!e.domain&&!locks);
 assert(pear_fex_bitmap_bits((void*)0x10000000,4096,0)&&pear_fex_bitmap_bits((void*)0x10001000,4096,1));
 reset();ec_process=0;refused(0,4096,-10);assert(!allocations);
 reset();pear_fex_wine_backing.owner_pid++;refused(0,4096,-10);assert(!allocations);
 reset();refused(1,4096,-10);assert(!allocations);
 reset();refused(UINT64_MAX-4095,8192,-10);assert(!allocations);
 reset();record.role=2;refused(0,4096,-10);assert(!allocations);
 reset();bad_view=1;refused(0,4096,-10);assert(!allocations);
 reset();target.pear_generation++;refused(0,4096,-10);assert(!allocations);
 reset();bitmap.size=4096;refused(0,4096,-10);
 reset();allocation_failure=1;refused(0,4096,-20);
 reset();vprot_failure=1;refused(0,4096,-11);
 reset();protect_failure=1;refused(0,4096,-21);
 reset();query_failure=1;refused(0,4096,-22);
 reset();bits_failure=1;assert(pear_fex_wine_ec_register(0,4096,1,&e));assert(e.domain==2&&e.code==-10&&changes==1&&!locks);
 return 0;
}
'''

class ECBits(unittest.TestCase):
    def test_actual_callback_refuses_bad_identity_and_preserves_vm_errors(self):
        if not SOURCE.is_file() or not shutil.which('clang'):
            self.skipTest('recorded Wine source/native compiler unavailable')
        raw=SOURCE.read_bytes()
        series=json.loads((ROOT/'runtime/fex/patches/integration/series.json').read_text())
        row=next(r for p in reversed(series['patches']) for r in p['sources'] if r['path']=='dlls/ntdll/unix/virtual.c')
        self.assertEqual(hashlib.sha256(raw).hexdigest(),row['postimage_sha256'])
        source=raw.decode();start=source.index('static int pear_fex_wine_ec_register(');end=source.index('static int pear_fex_wine_role(',start)
        with tempfile.TemporaryDirectory(prefix='pear-ec-bitmap-') as name:
            root=Path(name);(root/'probe.c').write_text(PREAMBLE+source[start:end]+HARNESS)
            result=subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=undefined',
                '-fno-sanitize-recover=all',str(root/'probe.c'),'-o',str(root/'probe')],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(root/'probe')],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
