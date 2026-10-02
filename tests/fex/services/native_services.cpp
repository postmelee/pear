// SPDX-License-Identifier: MIT
// Original finite fixture for the pinned eight-call FEX native service ABI.
// Calls only ordinary Darwin services through the native UnixLib data table.
#include "FEXUnixLib.h"
#include "DarwinConfigPolicy.h"
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <fcntl.h>
#include <limits>
#include <initializer_list>
#include <pthread.h>
#include <sys/mman.h>
#include <sys/sysctl.h>
#include <unistd.h>

#ifndef PEAR_FEX_DARWIN_DCACHE_LINE_BYTES
#error The fixture requires the source-bound observed cache-line value
#endif
using NTSTATUS = int32_t;
using Entry = NTSTATUS (*)(void*);
constexpr NTSTATUS SUCCESS = 0;
constexpr NTSTATUS INVALID = static_cast<int32_t>(0xC000000D);
constexpr NTSTATUS HANDLE = static_cast<int32_t>(0xC0000008);
constexpr NTSTATUS UNSUPPORTED = static_cast<int32_t>(0xC00000BB);
static void require(bool result, const char* id) {
  if (!result) { std::fprintf(stderr, "FAIL: %s errno=%d\n", id, errno); std::exit(2); }
}
static NTSTATUS call(Entry* table, FEXUnixLibFunctions function, void* args) {
  return table[static_cast<uint32_t>(function)](args);
}
static bool closed(int fd) { errno=0; return fcntl(fd,F_GETFD)==-1 && errno==EBADF; }
struct Worker { Entry* table; NTSTATUS enable {}, disable {}; bool software_required {}; };
static void* worker(void* opaque) {
  auto data=static_cast<Worker*>(opaque);
  FEXUnixLib_SetHardwareTSOControlArgs args {true};
  data->enable=call(data->table,FEXUnixLibFunctions::SetHardwareTSOControl,&args);
  args.Enable=false;
  data->disable=call(data->table,FEXUnixLibFunctions::SetHardwareTSOControl,&args);
  // This is the native caller's fallback decision, not an initialized FEX thread.
  data->software_required=data->enable==UNSUPPORTED && data->disable==UNSUPPORTED;
  return nullptr;
}
int main(int argc, char** argv) {
  require(argc==3,"arguments");
  unsigned policy_controls=0;
  for(const auto& setting:FEX::Windows::DarwinPolicy::Settings) {
    require(FEX::Windows::DarwinPolicy::AcceptJSON(setting.JSONName,setting.Value) &&
            FEX::Windows::DarwinPolicy::AcceptEnvironment(setting.EnvironmentName,setting.Value),"policy-accepted-preset");
    ++policy_controls;
    auto conflict=setting.Value=="1" ? "0" : "1";
    require(!FEX::Windows::DarwinPolicy::AcceptJSON(setting.JSONName,conflict) &&
            !FEX::Windows::DarwinPolicy::AcceptEnvironment(setting.EnvironmentName,conflict),"policy-conflict-refused");
    ++policy_controls;
  }
  require(!FEX::Windows::DarwinPolicy::AcceptJSON("UnreviewedTuning","1"),"unknown-json-policy-refused");++policy_controls;
  require(!FEX::Windows::DarwinPolicy::AcceptEnvironment("FEX_UNREVIEWEDTUNING","1"),"unknown-env-policy-refused");++policy_controls;
  require(policy_controls==20,"policy-control-count");
  void* library=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);
  require(library!=nullptr,"native-unixlib-load");
  auto table=static_cast<Entry*>(dlsym(library,"__wine_unix_call_funcs"));
  auto count=static_cast<const uint32_t*>(dlsym(library,"pear_fex_unix_call_count"));
  require(table && count && *count==static_cast<uint32_t>(FEXUnixLibFunctions::MAX) && *count==8,"service-table-count");
  for(uint32_t i=0;i<*count;++i) {
    require(table[i]!=nullptr,"service-table-entry");
    if(i!=static_cast<uint32_t>(FEXUnixLibFunctions::DeleteSHMStatsFile)) require(table[i](nullptr)==INVALID,"null-argument");
  }
  size_t cacheline=0, length=sizeof(cacheline);
  require(sysctlbyname("hw.cachelinesize",&cacheline,&length,nullptr,0)==0 && cacheline==PEAR_FEX_DARWIN_DCACHE_LINE_BYTES,"observed-cache-line");
  FEXUnixLib_GetPID pid {};
  require(call(table,FEXUnixLibFunctions::GetPID,&pid)==SUCCESS && pid.Result==static_cast<uint32_t>(getpid()),"real-process-pid");
  FEXUnixLib_SetHardwareTSOControlArgs tso {true};
  require(call(table,FEXUnixLibFunctions::SetHardwareTSOControl,&tso)==UNSUPPORTED,"hardware-tso-unsupported");
  FEXUnixLib_SetKernelUnalignedAtomicControl atomic {FEX_UNALIGN_ATOMIC_EMULATE};
  require(call(table,FEXUnixLibFunctions::SetKernelUnalignedAtomicControl,&atomic)==UNSUPPORTED,"kernel-control-unsupported");
  atomic.Flags=~uint64_t{};
  require(call(table,FEXUnixLibFunctions::SetKernelUnalignedAtomicControl,&atomic)==INVALID,"kernel-control-invalid-flags");
  char owned[32] {};
  FEXUnixLib_Madvise advice {owned,sizeof(owned),14,0};
  require(call(table,FEXUnixLibFunctions::Madvise,&advice)==UNSUPPORTED,"linux-hugepage-advice-unsupported");
  advice.Advise=15;
  require(call(table,FEXUnixLibFunctions::Madvise,&advice)==UNSUPPORTED,"linux-nohugepage-advice-unsupported");
  advice.Size=0;
  require(call(table,FEXUnixLibFunctions::Madvise,&advice)==INVALID,"empty-advice-range");
  advice={reinterpret_cast<void*>(std::numeric_limits<uintptr_t>::max()-8),32,14,0};
  require(call(table,FEXUnixLibFunctions::Madvise,&advice)==INVALID,"overflow-advice-range");
  FEXUnixLib_SetVMAName name {owned,sizeof(owned),"owned-fixture"};
  require(call(table,FEXUnixLibFunctions::SetVMAName,&name)==UNSUPPORTED,"vma-naming-unsupported");
  FEXUnixLib_GetSHMStatsVMA stats {owned,16,32};
  require(call(table,FEXUnixLibFunctions::GetSHMStatsVMA,&stats)==UNSUPPORTED && stats.SHMBase==nullptr,"stats-unsupported-zero-output");
  require(call(table,FEXUnixLibFunctions::DeleteSHMStatsFile,nullptr)==UNSUPPORTED,"stats-delete-unsupported");
  int directory=open(argv[2],O_RDONLY|O_DIRECTORY|O_CLOEXEC|O_NOFOLLOW);
  require(directory>=0,"owned-directory");
  int original=openat(directory,"mapping-fixture.bin",O_CREAT|O_EXCL|O_RDWR|O_CLOEXEC|O_NOFOLLOW,0600);
  require(original>=0,"owned-file-create");
  constexpr char payload[]="Pear owned file mapping fixture";
  require(write(original,payload,sizeof(payload))==sizeof(payload),"owned-file-write");
  int transferred=dup(original);
  require(transferred>=0,"owned-file-duplicate");
  FEXUnixLib_MapFile mapping {transferred,sizeof(payload),owned};
  require(call(table,FEXUnixLibFunctions::MapFile,&mapping)==SUCCESS && mapping.Result!=nullptr && mapping.FD==-1 && closed(transferred),"mapping-owned-fd-consumed");
  require(std::memcmp(mapping.Result,payload,sizeof(payload))==0,"mapping-read-contents");
  require(munmap(mapping.Result,sizeof(payload))==0,"mapping-release");
  // Every rejected nonnegative descriptor is a new owned duplicate.
  for(uint64_t size: {uint64_t{0},uint64_t{sizeof(payload)+1},std::numeric_limits<uint64_t>::max()}) {
    transferred=dup(original); require(transferred>=0,"rejection-file-duplicate");
    mapping={transferred,size,owned};
    require(call(table,FEXUnixLibFunctions::MapFile,&mapping)==INVALID && mapping.Result==nullptr && mapping.FD==-1 && closed(transferred),"invalid-size-owned-fd-consumed");
  }
  transferred=dup(directory); require(transferred>=0,"directory-duplicate");
  mapping={transferred,1,owned};
  require(call(table,FEXUnixLibFunctions::MapFile,&mapping)==UNSUPPORTED && mapping.Result==nullptr && closed(transferred),"nonregular-fd-consumed");
  mapping={-1,1,owned};
  require(call(table,FEXUnixLibFunctions::MapFile,&mapping)==HANDLE && mapping.Result==nullptr,"invalid-fd-zero-output");
  require(fcntl(original,F_GETFD)>=0,"caller-original-fd-survives");
  require(close(original)==0 && unlinkat(directory,"mapping-fixture.bin",0)==0 && close(directory)==0,"owned-file-cleanup");
  pthread_t threads[2] {}; Worker workers[2] {{table},{table}};
  for(unsigned i=0;i<2;++i) require(pthread_create(&threads[i],nullptr,worker,&workers[i])==0,"owned-worker-create");
  for(unsigned i=0;i<2;++i) require(pthread_join(threads[i],nullptr)==0 && workers[i].software_required,"owned-worker-fallback-and-join");
  require(dlclose(library)==0,"native-library-close");
  std::printf("{\"schema_version\":1,\"record_kind\":\"fex_native_service_observation\",\"scope\":\"fex_component\",\"service_count\":8,\"cache_line_bytes\":%zu,\"pid\":%u,\"mapping_controls\":7,\"policy_controls\":%u,\"owned_workers\":2,\"workers_joined\":2,\"software_tso_required\":true,\"hardware_tso_status\":%d,\"kernel_control_status\":%d,\"linux_advice_status\":%d,\"vma_naming_status\":%d,\"stats_status\":%d,\"descriptor_cleanup\":true,\"restricted_operations\":false,\"fex_initialization\":false,\"jit_execution\":false,\"pe_execution\":false,\"guest_execution\":false,\"passed\":true}\n",cacheline,pid.Result,policy_controls,UNSUPPORTED,UNSUPPORTED,UNSUPPORTED,UNSUPPORTED,UNSUPPORTED);
  return 0;
}
