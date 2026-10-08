// Original compile/link fixture; the DLL and its functions are never run.
#include <vector>
#include <cstdint>
#include <chrono>
extern "C" __declspec(dllimport) long __stdcall NtYieldExecution(void);
extern "C" std::uintptr_t _Unwind_GetIP(void *);
extern "C" int __cxa_guard_acquire(std::uint64_t *);
extern "C" __declspec(dllexport) std::uint64_t pear_fex_static_runtime(
    std::uint64_t input, std::uint64_t divisor, void *context, std::uint64_t *guard) {
    std::vector<std::uint64_t> values;
    values.reserve(4);
    values.push_back(input);
    values.push_back(input ^ 42);
    // Runtime operands require the 128-bit compiler division builtin.
    const unsigned __int128 numerator = (static_cast<unsigned __int128>(input) << 64) | divisor;
    const unsigned __int128 denominator = static_cast<unsigned __int128>(divisor) | 1;
    return values[0] + values[1] + std::chrono::steady_clock::now().time_since_epoch().count()
         + static_cast<std::uint64_t>(numerator / denominator)
         + _Unwind_GetIP(context) + __cxa_guard_acquire(guard) + NtYieldExecution();
}
