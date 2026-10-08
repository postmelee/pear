"""Exercise the actual FEX data-fault recovery header with controlled NT results.

Only the OS calls and vector allocator are substituted; interval selection and
recovery decisions are the real staged implementation. No fault is raised.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'.build/task5/integration-fex-link8/source/Source/Windows/Common/OvercommitTracker.h'
STUB = r'''
#pragma once
#include <cstdint>
#include <cstddef>
#include <mutex>
using NTSTATUS = int32_t;
using SIZE_T = size_t;
constexpr unsigned MEM_PRIVATE=0x20000, MEM_RESERVE=0x2000, MEM_COMMIT=0x1000, PAGE_READWRITE=4;
constexpr int MemoryBasicInformation=0;
constexpr NTSTATUS STATUS_INVALID_PARAMETER=static_cast<NTSTATUS>(0xc000000d);
namespace FEXCore::Utils { constexpr uint64_t FEX_PAGE_SIZE=4096, FEX_PAGE_MASK=~uint64_t(4095); }
struct MEMORY_BASIC_INFORMATION { void *BaseAddress, *AllocationBase; unsigned AllocationProtect; SIZE_T RegionSize; unsigned State, Protect, Type; };
inline void* NtCurrentProcess() { return reinterpret_cast<void*>(~uintptr_t(0)); }
extern MEMORY_BASIC_INFORMATION observed;
extern NTSTATUS query_status, commit_status;
extern bool short_query, changed_address;
extern unsigned queries, commits;
extern SIZE_T committed_size;
NTSTATUS NtQueryVirtualMemory(void*,void*,int,void* output,SIZE_T size,SIZE_T* returned) {
 ++queries; *static_cast<MEMORY_BASIC_INFORMATION*>(output)=observed; *returned=short_query ? size-1 : size; return query_status;
}
NTSTATUS NtAllocateVirtualMemory(void*,void** address,uintptr_t,SIZE_T* size,unsigned type,unsigned protection) {
 ++commits; committed_size=*size;
 if (type!=MEM_COMMIT || protection!=PAGE_READWRITE) return -99;
 if (changed_address) *address=nullptr;
 return commit_status;
}
inline void* VirtualAlloc(void* address,SIZE_T,unsigned,unsigned) { return address; }
'''
HARNESS = r'''
#include "OvercommitTracker.h"
#include <cassert>
MEMORY_BASIC_INFORMATION observed;
NTSTATUS query_status{}, commit_status{};
bool short_query{}, changed_address{};
unsigned queries{}, commits{};
SIZE_T committed_size{};
void reset() {
 observed={reinterpret_cast<void*>(0x108000),reinterpret_cast<void*>(0x100000),PAGE_READWRITE,0x8000,MEM_RESERVE,0,MEM_PRIVATE};
 query_status=commit_status=0; short_query=changed_address=false; queries=commits=0; committed_size=0;
}
int main() {
 FEX::Windows::OvercommitTracker tracker(true);
 tracker.MarkRange(0x100000,0x10000);
 NTSTATUS failure{};
 reset(); assert(!tracker.HandleAccessViolation(0x110000,&failure)); assert(!queries && !commits && !failure);
 reset(); assert(tracker.HandleAccessViolation(0x108888,&failure)); assert(commits==1 && committed_size==0x10000 && !failure);
 reset(); query_status=-41; assert(!tracker.HandleAccessViolation(0x108888,&failure)); assert(failure==-41 && !commits);
 reset(); commit_status=-42; assert(!tracker.HandleAccessViolation(0x108888,&failure)); assert(failure==-42 && commits==1);
 reset(); short_query=true; assert(!tracker.HandleAccessViolation(0x108888,&failure)); assert(failure==STATUS_INVALID_PARAMETER && !commits);
 reset(); observed.State=MEM_COMMIT; assert(!tracker.HandleAccessViolation(0x108888,&failure)); assert(!commits);
 reset(); observed.AllocationProtect=0x40; assert(!tracker.HandleAccessViolation(0x108888,&failure)); assert(!commits);
 reset(); observed.AllocationBase=reinterpret_cast<void*>(0xf0000); assert(!tracker.HandleAccessViolation(0x108888,&failure)); assert(!commits);
 reset(); observed.RegionSize=~SIZE_T(0); assert(!tracker.HandleAccessViolation(0x108888,&failure)); assert(!commits);
 reset(); changed_address=true; assert(!tracker.HandleAccessViolation(0x108888,&failure)); assert(failure==STATUS_INVALID_PARAMETER && commits==1);
 tracker.UnmarkRange(0x100000,0x10000);
 reset(); assert(!tracker.HandleAccessViolation(0x108888,&failure)); assert(!queries && !commits && !failure);
}
'''


class CheckedOvercommitTests(unittest.TestCase):
    def test_real_tracker_handles_only_owned_successful_data_commit(self):
        compiler=shutil.which('clang++')
        if not compiler or not SOURCE.is_file():
            self.skipTest('recorded header or native C++ compiler unavailable')
        series=json.loads((ROOT/'runtime/fex/patches/integration/fex-series.json').read_text())
        row=next(r for p in reversed(series['patches']) for r in p['sources']
                 if r['path']=='Source/Windows/Common/OvercommitTracker.h')
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(),row['postimage_sha256'])
        with tempfile.TemporaryDirectory(prefix='pear-overcommit-') as name:
            folder=Path(name)
            (folder/'FEXCore/fextl').mkdir(parents=True)
            (folder/'FEXCore/fextl/vector.h').write_text('#pragma once\n#include <vector>\nnamespace fextl { template<class T> using vector=std::vector<T>; }\n')
            (folder/'ntstatus.h').write_text(STUB)
            (folder/'winternl.h').write_text('#pragma once\n#include "ntstatus.h"\n')
            (folder/'test.cpp').write_text(HARNESS)
            built=subprocess.run([compiler,'-std=c++20','-fsanitize=undefined','-fno-sanitize-recover=all',
                            '-I'+str(folder),'-I'+str(SOURCE.parent),
                            '-I'+str(ROOT/'.build/task5/stage3-fex-modules14/source/FEXCore/include'),
                            str(folder/'test.cpp'),'-o',str(folder/'test')],capture_output=True,text=True)
            self.assertEqual(built.returncode,0,built.stderr)
            subprocess.run([str(folder/'test')],check=True,capture_output=True,text=True,timeout=10)
