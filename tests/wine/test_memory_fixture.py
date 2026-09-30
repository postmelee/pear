"""Run original fixture control flow against deterministic fake Win32 APIs.
Generated ARM64 code is inspected by a stub, never executed. This validates
counter/cleanup/error propagation, not Wine memory or exception behavior.
"""
from pathlib import Path
import json
import subprocess
import tempfile
import unittest
from stage4_source import REPO
FIXTURES = REPO / 'tests/wine/fixtures'
PRELUDE=r'''
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define WINAPI
#define __declspec(x)
#define ERROR_SUCCESS 0
#define ERROR_INVALID_DATA 13
#define ERROR_NOT_SUPPORTED 50
#define ERROR_INVALID_PARAMETER 87
#define ERROR_WRITE_FAULT 29
#define MEM_COMMIT 0x1000
#define MEM_RESERVE 0x2000
#define MEM_DECOMMIT 0x4000
#define MEM_RELEASE 0x8000
#define MEM_FREE 0x10000
#define MEM_PRIVATE 0x20000
#define PAGE_NOACCESS 1
#define PAGE_READONLY 2
#define PAGE_READWRITE 4
#define PAGE_EXECUTE_READ 0x20
#define PAGE_EXECUTE_READWRITE 0x40
#define PAGE_GUARD 0x100
#define FALSE 0
#define TRUE 1
typedef uint32_t DWORD;
typedef size_t SIZE_T;
typedef uintptr_t ULONG_PTR;
typedef struct { DWORD dwPageSize, dwAllocationGranularity; } SYSTEM_INFO;
typedef struct { void *BaseAddress, *AllocationBase; SIZE_T RegionSize; DWORD State, Protect, AllocationProtect, Type; } MEMORY_BASIC_INFORMATION;
static unsigned fail_at, api_count, reported_error, observed_fields, emit_fail;
static DWORD last_error;
static unsigned char *normal_base, *dynamic_base;
static unsigned normal_active,dynamic_active;
static DWORD normal_state[3], normal_protect[3], dynamic_state, dynamic_protect;
static int failure(void) { if (++api_count == fail_at) { last_error=999; return 1; } return 0; }
static DWORD GetLastError(void) { return last_error; }
static void SetLastError(DWORD value) { last_error=value; }
static void GetSystemInfo(SYSTEM_INFO *info) { info->dwPageSize=4096; info->dwAllocationGranularity=65536; }
static void *GetCurrentProcess(void) { return (void *)-1; }
static void *VirtualAlloc(void *address, SIZE_T bytes, DWORD type, DWORD prot)
{
    if (failure()) return NULL;
    if (type == MEM_RESERVE)
    {
        if (address) abort();
        if (prot == PAGE_NOACCESS)
        {
            if (bytes != 12288 || normal_active) abort();
            if (!normal_base && posix_memalign((void **)&normal_base,65536,65536)) abort();
            normal_active=1;
            for(unsigned i=0;i<3;++i) { normal_state[i]=MEM_RESERVE; normal_protect[i]=0; }
            return normal_base;
        }
        if(prot != PAGE_EXECUTE_READ || bytes !=4096 || dynamic_active) abort();
        if(!dynamic_base && posix_memalign((void **)&dynamic_base,65536,65536)) abort();
        dynamic_active=1; dynamic_state=MEM_RESERVE; dynamic_protect=0;
        return dynamic_base;
    }
    if(type != MEM_COMMIT || prot != PAGE_READWRITE) abort();
    if(address == dynamic_base)
    {
        if(bytes !=4096 || !dynamic_active) abort();
        if(dynamic_state!=MEM_COMMIT) memset(dynamic_base,0,4096);
        dynamic_state=MEM_COMMIT; dynamic_protect=PAGE_READWRITE;
        return dynamic_base;
    }
    uintptr_t offset=(uintptr_t)address-(uintptr_t)normal_base;
    if(!normal_active || offset%4096 || bytes%4096 || offset+bytes>12288) abort();
    for(unsigned i=offset/4096;i<(offset+bytes)/4096;++i)
    {
        if(normal_state[i]!=MEM_COMMIT) memset(normal_base+i*4096,0,4096);
        normal_state[i]=MEM_COMMIT; normal_protect[i]=PAGE_READWRITE;
    }
    return address;
}
static SIZE_T VirtualQuery(const void *address, MEMORY_BASIC_INFORMATION *info, SIZE_T bytes)
{
    if(failure()) return 0;
    if(bytes!=sizeof(*info)) abort();
    memset(info,0,sizeof(*info)); info->BaseAddress=(void *)address;info->RegionSize=4096;
    if(address==dynamic_base)
    {
        if(!dynamic_active) {info->State=MEM_FREE;info->Protect=PAGE_NOACCESS;return bytes;}
        info->AllocationBase=dynamic_base; info->AllocationProtect=PAGE_EXECUTE_READ;
        info->State=dynamic_state;info->Protect=dynamic_protect;info->Type=MEM_PRIVATE;
        return bytes;
    }
    uintptr_t offset=(uintptr_t)address-(uintptr_t)normal_base;
    if(!normal_active||offset%4096||offset>=12288) abort();
    info->AllocationBase=normal_base;info->AllocationProtect=PAGE_NOACCESS;
    info->State=normal_state[offset/4096];info->Protect=normal_protect[offset/4096];info->Type=MEM_PRIVATE;
    return bytes;
}
static int VirtualProtect(void *address,SIZE_T bytes,DWORD prot,DWORD *old)
{
    if(failure()) return 0;
    if(bytes!=4096) abort();
    if(address==dynamic_base)
    {
        if(prot==PAGE_EXECUTE_READWRITE||prot==(PAGE_READWRITE|PAGE_GUARD)) {last_error=ERROR_INVALID_PARAMETER;return 0;}
        if(dynamic_state!=MEM_COMMIT) abort();
        *old=dynamic_protect;dynamic_protect=prot;return 1;
    }
    uintptr_t offset=(uintptr_t)address-(uintptr_t)normal_base;
    if(offset!=4096||normal_state[1]!=MEM_COMMIT) abort();
    if(prot==PAGE_EXECUTE_READ) {last_error=ERROR_NOT_SUPPORTED;return 0;}
    *old=normal_protect[1];normal_protect[1]=prot;return 1;
}
static int VirtualFree(void *address,SIZE_T bytes,DWORD type)
{
    if(failure()) return 0;
    if(address==dynamic_base)
    {
        if(!dynamic_active) abort();
        if(type==MEM_RELEASE&&bytes==0) {dynamic_active=0;return 1;}
        if(type!=MEM_DECOMMIT||bytes!=4096) abort();
        dynamic_state=MEM_RESERVE;dynamic_protect=0;return 1;
    }
    uintptr_t offset=(uintptr_t)address-(uintptr_t)normal_base;
    if(!normal_active) abort();
    if(type==MEM_RELEASE&&bytes==0&&offset==0) {normal_active=0;return 1;}
    if(type!=MEM_DECOMMIT||bytes!=4096||offset!=4096) abort();
    normal_state[1]=MEM_RESERVE;normal_protect[1]=0;return 1;
}
static int FlushInstructionCache(void *process,const void *address,SIZE_T bytes)
{
    if(failure()) return 0;
    if(process!=(void *)-1||address!=dynamic_base||bytes!=8||dynamic_protect!=PAGE_EXECUTE_READ) abort();
    return 1;
}
static int pear_expect_memory_fault(volatile unsigned char *address,unsigned access,unsigned code)
{
    if(address!=normal_base+4096) abort();
    if(code==0x80000001u)
    {
        if(access||normal_protect[1]!=(PAGE_READWRITE|PAGE_GUARD)) abort();
        normal_protect[1]=PAGE_READWRITE;return 0;
    }
    if(code!=0xc0000005u) abort();
    if(access && normal_protect[1]!=PAGE_READONLY) abort();
    if(!access && normal_state[1]!=MEM_RESERVE) abort();
    return 0;
}
static unsigned test_dynamic_call(volatile unsigned char *address)
{
    if(address!=dynamic_base||dynamic_protect!=PAGE_EXECUTE_READ) abort();
    volatile uint32_t *words=(volatile uint32_t *)address;
    if(words[1]!=0xd65f03c0u||(words[0]!=0x52800540u&&words[0]!=0x52800a80u)) abort();
    return words[0]==0x52800540u?42:84;
}
static int pear_emit(const char *kind,const char *const *names,const uint64_t *values,unsigned count)
{
    if(emit_fail && !strcmp(kind,"pear_dynamic_call")) {emit_fail=0;return 0;}
    printf("{\"record_kind\":\"%s\"",kind);
    for(unsigned i=0;i<count;++i) printf(",\"%s\":%llu",names[i],(unsigned long long)values[i]);
    puts("}");
    if(!strcmp(kind,"pear_memory_result")) {reported_error=values[1];observed_fields=count;}
    return 1;
}
'''
TAIL=r'''
int main(int argc,char **argv)
{
    if(argc>1) fail_at=atoi(argv[1]);
    if(argc>2) emit_fail=atoi(argv[2]);
    int result=pear_memory_checks();
    printf("{\"result\":%d,\"api_count\":%u,\"normal_active\":%u,\"dynamic_active\":%u,\"reported_error\":%u}\n",
        result,api_count,normal_active,dynamic_active,reported_error);
    if(observed_fields!=22) return 3;
    return 0;
}
'''
EXPECTED={'error_step':0,'error_code':0,'queries':22,'sentinel_checks':4,'zero_bytes':28672,
'access_faults':2,'guard_faults':1,'ordinary_commits':2,'ordinary_protects':3,'ordinary_decommits':1,'ordinary_releases':1,
'dynamic_reserves':2,'dynamic_commits':3,'dynamic_protects':3,'dynamic_decommits':1,'dynamic_releases':2,'flushes':2,'code_calls':2,
'first_value':42,'second_value':84,'reuse_checks':1,'negative_controls':3}

class MemoryFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='pear-memory-flow-')
        cls.addClassCleanup(cls.tmp.cleanup)
        folder=Path(cls.tmp.name)
        src=(FIXTURES/'memory_pe.c').read_text()
        src='\n'.join(line for line in src.splitlines() if not line.startswith('#include'))
        begin=src.index('__declspec(dllexport) __declspec(noinline) unsigned WINAPI PearDynamicCall(')
        end=src.index('\nstatic int publish_call',begin)
        src=src[:begin]+'''static unsigned PearDynamicCall(volatile unsigned char *address)
{ return test_dynamic_call(address); }
'''+src[end:]
        (folder/'main.c').write_text(PRELUDE+src+TAIL)
        cls.exe=folder/'fixture'
        result=subprocess.run(['/usr/bin/clang','-std=gnu23','-fsanitize=undefined','-fno-sanitize-recover=all',
            str(folder/'main.c'),'-o',str(cls.exe)],text=True,capture_output=True)
        if result.returncode: raise AssertionError(result.stderr)

    def run_case(self,number=0,emit=0):
        result=subprocess.run([str(self.exe),str(number),str(emit)],text=True,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return [json.loads(line) for line in result.stdout.splitlines()]

    def test_complete_control_flow_counts(self):
        rows=self.run_case()
        summary=next(row for row in rows if row.get('record_kind')=='pear_memory_result')
        self.assertEqual({k:v for k,v in summary.items() if k!='record_kind'},EXPECTED)
        self.assertEqual(rows[-1]['result'],0)
        self.assertEqual(rows[-1]['normal_active']+rows[-1]['dynamic_active'],0)
        calls=[r for r in rows if r.get('record_kind')=='pear_dynamic_call']
        self.assertEqual([r['value'] for r in calls],[42,84])
        self.assertEqual(calls[0]['base'],calls[1]['base'])

    def test_each_win32_api_failure_retains_error(self):
        total=self.run_case()[-1]['api_count']
        for at in range(1,total+1):
            with self.subTest(api_call=at):
                rows=self.run_case(at)
                self.assertNotEqual(rows[-1]['result'],0)
                self.assertEqual(rows[-1]['reported_error'],999)

    def test_output_failure_preserves_error_and_releases_allocations(self):
        rows=self.run_case(0,1)
        self.assertEqual(rows[-1]['result'],29)
        self.assertEqual(rows[-1]['reported_error'],29)
        self.assertEqual(rows[-1]['normal_active']+rows[-1]['dynamic_active'],0)

if __name__=='__main__':unittest.main()
