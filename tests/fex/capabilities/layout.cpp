// Original layout assertions consume the exact attributed pinned FEX header.
// FEXUnixLib.h remains in materialized MIT-licensed upstream source.
#include "FEXUnixLib.h"
#include <cstddef>
static_assert(static_cast<unsigned>(FEXUnixLibFunctions::MAX) == 8);
static_assert(alignof(FEXUnixLib_SetHardwareTSOControlArgs) == 1);
static_assert(offsetof(FEXUnixLib_Madvise, Addr) == 0);
static_assert(offsetof(FEXUnixLib_Madvise, Size) == 8);
static_assert(offsetof(FEXUnixLib_Madvise, Advise) == 16);
static_assert(offsetof(FEXUnixLib_SetVMAName, Name) == 16);
static_assert(offsetof(FEXUnixLib_GetSHMStatsVMA, MapSize) == 8);
static_assert(offsetof(FEXUnixLib_GetSHMStatsVMA, MaxSize) == 12);
static_assert(offsetof(FEXUnixLib_MapFile, MapSize) == 8);
static_assert(offsetof(FEXUnixLib_MapFile, Result) == 16);
static_assert(sizeof(FEXUnixLib_GetPID) == 4);
extern "C" const unsigned pear_fex_service_count = 8;

// Complete size/alignment and ordered-enum checks for the selected 64-bit ABI.
static_assert(static_cast<unsigned>(FEXUnixLibFunctions::SetHardwareTSOControl) == 0);
static_assert(sizeof(FEXUnixLib_SetHardwareTSOControlArgs) == 1);
static_assert(alignof(FEXUnixLib_SetHardwareTSOControlArgs) == 1);
static_assert(static_cast<unsigned>(FEXUnixLibFunctions::SetKernelUnalignedAtomicControl) == 1);
static_assert(sizeof(FEXUnixLib_SetKernelUnalignedAtomicControl) == 8);
static_assert(alignof(FEXUnixLib_SetKernelUnalignedAtomicControl) == 8);
static_assert(static_cast<unsigned>(FEXUnixLibFunctions::Madvise) == 2);
static_assert(sizeof(FEXUnixLib_Madvise) == 24);
static_assert(alignof(FEXUnixLib_Madvise) == 8);
static_assert(static_cast<unsigned>(FEXUnixLibFunctions::SetVMAName) == 3);
static_assert(sizeof(FEXUnixLib_SetVMAName) == 24);
static_assert(alignof(FEXUnixLib_SetVMAName) == 8);
static_assert(static_cast<unsigned>(FEXUnixLibFunctions::GetSHMStatsVMA) == 4);
static_assert(sizeof(FEXUnixLib_GetSHMStatsVMA) == 16);
static_assert(alignof(FEXUnixLib_GetSHMStatsVMA) == 8);
static_assert(static_cast<unsigned>(FEXUnixLibFunctions::DeleteSHMStatsFile) == 5);
static_assert(static_cast<unsigned>(FEXUnixLibFunctions::MapFile) == 6);
static_assert(sizeof(FEXUnixLib_MapFile) == 24);
static_assert(alignof(FEXUnixLib_MapFile) == 8);
static_assert(static_cast<unsigned>(FEXUnixLibFunctions::GetPID) == 7);
static_assert(sizeof(FEXUnixLib_GetPID) == 4);
static_assert(alignof(FEXUnixLib_GetPID) == 4);
