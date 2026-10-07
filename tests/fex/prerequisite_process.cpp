// SPDX-License-Identifier: MIT
// Original ordinary ARM64 prerequisite-only observation.
// No CRT constructors, FEX objects, executable extents or guest entry.
#include <FEXCore/Utils/AllocatorHooks.h>
#include "Source/Windows/PearEmptyInit/CheckedCRT.h"
#include "Source/Windows/Common/Priv.h"
#include <ntstatus.h>
#include <winbase.h>

extern "C" DECLSPEC_NORETURN void WINAPI RtlExitUserProcess(NTSTATUS);

// Standard PE TLS directory with pointer-aligned, zero-payload boundaries.
// Retain the upstream DummyHandlers and libc++abi TLS template unchanged:
// allocating an extra pointer sentinel would change Wine's heap size class.
// The selected FEX CRT owns _tls_index. Wine owns the real TLS allocation;
// no synthetic TLS block, alternative CRT startup or automatic callback is added.
// Directory semantics: https://learn.microsoft.com/en-us/windows/win32/debug/pe-format#the-tls-section
asm(".section .tls,\"dw\"\n"
    ".p2align 3\n.globl _tls_start\n_tls_start:\n"
    ".section .tls$ZZZ,\"dw\"\n"
    ".p2align 3\n.globl _tls_end\n_tls_end:\n");
extern "C" {
extern uint64_t _tls_index;
extern char _tls_start[], _tls_end[];
__attribute__((section(".rdata$T"),used)) extern const IMAGE_TLS_DIRECTORY64 _tls_used={
  reinterpret_cast<ULONGLONG>(_tls_start),reinterpret_cast<ULONGLONG>(_tls_end),
  reinterpret_cast<ULONGLONG>(&_tls_index),0,0,0
};
}

extern "C" void WINAPI PearEmptyProcessEntry() {
  using FEX::Windows::PearEmptyInit::Report;
  using FEX::Windows::PearEmptyInit::Status;
  using FEX::Windows::PearEmptyInit::CRTPlan;
  struct Record { Report Observed; pear_fex_memory_metadata Metadata; } Value {};
  auto& Observed=Value.Observed;
  CRTPlan Plan;
  Observed.Primary=FEX::Windows::PearEmptyInit::InspectPrerequisites(Plan,Observed);
  Value.Metadata=Plan.Metadata;
  // Hex-encode the fixed record without malloc, stdio or an initialized CRT.
  constexpr char Prefix[]="pear_prerequisite_report_v1 ";
  constexpr char Hex[]="0123456789abcdef";
  char Line[sizeof(Prefix)-1+sizeof(Record)*2+1];
  size_t Cursor {};
  for (size_t I=0;I<sizeof(Prefix)-1;++I) Line[Cursor++]=Prefix[I];
  const auto Bytes=reinterpret_cast<const unsigned char*>(&Value);
  for (size_t I=0;I<sizeof(Value);++I) {
    Line[Cursor++]=Hex[Bytes[I]>>4]; Line[Cursor++]=Hex[Bytes[I]&15];
  }
  Line[Cursor++]='\n';
  const auto Parameters=reinterpret_cast<const RTL_USER_PROCESS_PARAMETERS64*>(GetCurrentPEB()->ProcessParameters);
  const auto Output=reinterpret_cast<HANDLE>(Parameters->hStdOutput);
  IO_STATUS_BLOCK IO {};
  auto Written=NtWriteFile(Output,nullptr,nullptr,nullptr,&IO,Line,static_cast<ULONG>(Cursor),nullptr,nullptr);
  if (Written==STATUS_PENDING) {
    LARGE_INTEGER Timeout; Timeout.QuadPart=-100000000;
    Written=NtWaitForSingleObject(Output,FALSE,&Timeout);
    if (!Written) Written=IO.Status;
  }
  if (Written || IO.Information!=Cursor) RtlExitUserProcess(2);
  const bool Complete=Observed.Primary.State==Status::OK && Observed.TLSObserved==1 &&
    Observed.UnixPIDObserved==1 && Observed.OwnerObserved==1 &&
    Observed.ConstructionCleanupAttempted==1 && Observed.ConstructionCleanup.State==Status::OK &&
    Observed.Cleanup.State==Status::OK && Observed.FinalCleanupAttempted==0 &&
    Observed.CRTProcessAttempted==0 && Observed.CRTThreadAttempted==0 &&
    Observed.ContextAttempted==0 && Observed.ThreadAttempted==0 && Observed.CoreAttempted==0 &&
    Observed.GuestExecution==0 && Observed.ARM64ECExecution==0 && Observed.Stage3Complete==0;
  RtlExitUserProcess(Complete ? 0 : 1);
}
