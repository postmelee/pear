// SPDX-License-Identifier: MIT
// Original ordinary ARM64 process entry for the finite source initializer.
// Reuse FEX's custom CRT; the closed source gate is the sole init decision.
#include <FEXCore/Utils/AllocatorHooks.h>
#include "Source/Windows/PearEmptyInit/Report.h"
#include "Source/Windows/Common/Priv.h"
#include <ntstatus.h>
#include <winbase.h>

extern "C" uint32_t WINAPI PearEmptySourceInit(FEX::Windows::PearEmptyInit::Report*);
extern "C" uint32_t PearFiniteCheckpoint;
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
  Report Observed;
  const auto Result=PearEmptySourceInit(&Observed);
  // Hex-encode the fixed record without malloc, stdio or an initialized CRT.
  constexpr char Prefix[]="pear_empty_report_v1 ";
  constexpr char Hex[]="0123456789abcdef";
  char Line[sizeof(Prefix)-1+sizeof(Report)*2+1+32];
  size_t Cursor {};
  for (size_t I=0;I<sizeof(Prefix)-1;++I) Line[Cursor++]=Prefix[I];
  const auto Bytes=reinterpret_cast<const unsigned char*>(&Observed);
  for (size_t I=0;I<sizeof(Observed);++I) {
    Line[Cursor++]=Hex[Bytes[I]>>4]; Line[Cursor++]=Hex[Bytes[I]&15];
  }
  Line[Cursor++]='\n';
  constexpr char CheckpointPrefix[]="pear_finite_checkpoint ";
  for (size_t I=0;I<sizeof(CheckpointPrefix)-1;++I) Line[Cursor++]=CheckpointPrefix[I];
  for (int Shift=28;Shift>=0;Shift-=4) Line[Cursor++]=Hex[(PearFiniteCheckpoint>>Shift)&15];
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
  const bool Complete=Result==0 && Observed.FinalCleanupAttempted==1 && Observed.Cleanup.State==Status::OK;
  RtlExitUserProcess(Complete ? 0 : 1);
}
