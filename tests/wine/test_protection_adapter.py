"""Execute exact candidate flag conversion/protection adapter with counted shims.
Both NtProtectVirtualMemory and the existing-private-allocation commit branch
use this adapter. No Wine process or OS permission operation is performed.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest
from stage4_source import materialize, configured_headers

def function(source,name):
    pos=source.index(name+'(')
    begin=source.rfind('\nstatic ',0,pos)+1
    brace=source.index('{',pos)
    depth=1
    end=brace+1
    while depth:
        if source[end]=='{':depth+=1
        elif source[end]=='}':depth-=1
        end+=1
    return source[begin:end]+'\n'

HEADER=r'''
#include "config.h"
#include "ntstatus.h"
#include "windef.h"
#include "winnt.h"
#include "winternl.h"
#include <stdio.h>
#define VPROT_READ 1
#define VPROT_WRITE 2
#define VPROT_EXEC 4
#define VPROT_WRITECOPY 8
#define VPROT_GUARD 16
#define VPROT_COMMITTED 32
struct file_view { unsigned protect,pear_owned; void *pear_dynamic; ULONGLONG pear_generation; };
static unsigned generic_calls,owner_calls,metadata_calls;
static NTSTATUS owner_result;
static BOOL pear_pe_arena_enabled(void) {return TRUE;}
static BOOL set_vprot(struct file_view *view,void *base,SIZE_T size,BYTE vprot)
{++generic_calls;return TRUE;}
static NTSTATUS pear_dynamic_protect(void *slot,ULONGLONG gen,void *base,SIZE_T size,BYTE vprot,BOOL commit)
{++owner_calls;return owner_result;}
static void set_page_vprot(void *base,SIZE_T size,BYTE vprot) {++metadata_calls;}
#define CHECK(x) do {if(!(x)) {fprintf(stderr,"line %d failed\n",__LINE__);return 1;}} while(0)
'''
TAIL=r'''
int main(void)
{
    struct file_view view={0};
    unsigned flags[]={PAGE_EXECUTE,PAGE_EXECUTE_READ,PAGE_EXECUTE_READWRITE};
    for(unsigned i=0;i<3;++i)
    {
        CHECK(set_protection(&view,(void *)0x10000,4096,flags[i])==STATUS_NOT_SUPPORTED);
        CHECK(!generic_calls&&!owner_calls&&!metadata_calls);
    }
    CHECK(!set_protection(&view,(void *)0x10000,4096,PAGE_READWRITE));
    CHECK(generic_calls==1&&!owner_calls&&!metadata_calls);
    view.pear_owned=3;
    unsigned modifiers[]={PAGE_GUARD,PAGE_NOCACHE,PAGE_WRITECOMBINE};
    for(unsigned i=0;i<3;++i)
    {
        CHECK(set_protection(&view,(void *)0x10000,4096,PAGE_READWRITE|modifiers[i])==STATUS_INVALID_PAGE_PROTECTION);
        CHECK(!owner_calls&&!metadata_calls);
    }
    CHECK(set_protection(&view,(void *)0x10000,4096,PAGE_EXECUTE_READWRITE)==STATUS_INVALID_PAGE_PROTECTION);
    CHECK(!owner_calls&&!metadata_calls);
    CHECK(!set_protection(&view,(void *)0x10000,4096,PAGE_READWRITE));
    CHECK(owner_calls==1&&metadata_calls==1);
    owner_result=STATUS_ACCESS_DENIED;
    CHECK(set_protection(&view,(void *)0x10000,4096,PAGE_EXECUTE_READ)==STATUS_ACCESS_DENIED);
    CHECK(owner_calls==2&&metadata_calls==1);
    return 0;
}
'''
class ProtectionAdapterTests(unittest.TestCase):
    def test_refuses_before_mutation_and_commits_metadata_only_after_owner(self):
        objects, source_headers = configured_headers()
        source=materialize('dlls/ntdll/unix/virtual.c')
        bodies=''.join(function(source,n) for n in ('is_view_valloc','get_vprot_flags','set_protection'))
        with tempfile.TemporaryDirectory(prefix='pear-protection-adapter-') as folder:
            path=Path(folder)
            (path/'main.c').write_text(HEADER+bodies+TAIL)
            result=subprocess.run(['/usr/bin/clang','-std=gnu23','-fsanitize=undefined','-fno-sanitize-recover=all',
                '-D__WINESRC__','-DWINE_UNIX_LIB','-I'+str(objects),
                '-I'+str(source_headers),str(path/'main.c'),'-o',str(path/'adapter')],
                text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(path/'adapter')],text=True,capture_output=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
if __name__=='__main__':unittest.main()
