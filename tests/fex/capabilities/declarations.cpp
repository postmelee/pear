// Original declaration-only probe; no memory API is invoked.
#define _WIN32_WINNT 0x0A00
#include <windows.h>
#include <type_traits>
static_assert(sizeof(MEM_EXTENDED_PARAMETER) == 16);
static_assert(MEM_EXTENDED_PARAMETER_EC_CODE != 0);
using allocation_type = decltype(&VirtualAlloc2);
static_assert(std::is_pointer_v<allocation_type>);
