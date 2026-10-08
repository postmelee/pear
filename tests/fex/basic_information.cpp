// SPDX-License-Identifier: MIT
// Original finite source-body control with a substituted NT query provider.
// This does not execute Wine, FEX initialization, or the real Windows ABI.
#include <cstdint>
#include <cstring>
#include <cstdio>
using NTSTATUS=int32_t;
using ULONG=uint32_t;
constexpr NTSTATUS STATUS_SUCCESS=0;
constexpr NTSTATUS STATUS_INVALID_PARAMETER=static_cast<int32_t>(0xc000000d);
constexpr int SystemEmulationBasicInformation=62;
struct SYSTEM_BASIC_INFORMATION {
  ULONG PhysicalPageSize, AllocationGranularity;
  uintptr_t LowestUserAddress, HighestUserAddress;
};
static SYSTEM_BASIC_INFORMATION BasicInfo, Supplied;
static ULONG Bytes;
static NTSTATUS ProviderStatus;
static unsigned Calls;
static void InitBasicInfo() {}
static NTSTATUS NtQuerySystemInformation(int Kind,void* Out,ULONG Size,ULONG* Returned) {
  ++Calls;
  if (Kind!=SystemEmulationBasicInformation || Size!=sizeof(Supplied) || !Returned) return -1;
  *Returned=Bytes;
  std::memcpy(Out,&Supplied,sizeof(Supplied));
  return ProviderStatus;
}
#include "basic_information_under_test.inc"
int main() {
  using namespace FEX::Windows::PearCRT;
  if (!IsOriginalBasicInfoInitializer(reinterpret_cast<uintptr_t>(&InitBasicInfo)) ||
      IsOriginalBasicInfoInitializer(0)) return 1;
  unsigned Passed=0;
  const SYSTEM_BASIC_INFORMATION Valid {4096,65536,65536,0x7ffeffff};
  const SYSTEM_BASIC_INFORMATION Sentinel {7,11,13,17};
  for (unsigned Case=0;Case<9;++Case) {
    BasicInfo=Sentinel;Supplied=Valid;Bytes=sizeof(Supplied);ProviderStatus=0;Calls=0;
    NTSTATUS Expected=STATUS_INVALID_PARAMETER;
    switch (Case) {
      case 0:ProviderStatus=static_cast<int32_t>(0xc0000004);Expected=ProviderStatus;break;
      case 1:Bytes--;break;
      case 2:Supplied.PhysicalPageSize=16384;break;
      case 3:Supplied.AllocationGranularity=0;break;
      case 4:Supplied.AllocationGranularity=12288;break;
      case 5:Supplied.AllocationGranularity=2048;break;
      case 6:Supplied.LowestUserAddress=Supplied.HighestUserAddress+1;break;
      case 7:Supplied.HighestUserAddress=Supplied.LowestUserAddress=1;break;
      case 8:Expected=0;break;
    }
    const auto Actual=InitializeBasicInfoChecked();
    const auto& ExpectedState=Expected ? Sentinel : Supplied;
    if (Actual!=Expected || Calls!=1 || std::memcmp(&BasicInfo,&ExpectedState,sizeof(BasicInfo))) return 2+Case;
    ++Passed;
  }
  std::printf("{\"cases\":%u,\"passed\":true,\"provider\":\"substituted\"}\n",Passed);
}
