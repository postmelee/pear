// Original compile-only C++20 capability fixture; no guest execution.
#include <span>
#include <bit>
#include <type_traits>
#include <cstdint>
static_assert(std::is_integral_v<std::uint32_t>);
static_assert(std::rotl(std::uint32_t(1), 3) == 8);
extern "C" __declspec(dllexport) unsigned pear_fex_cpp20(unsigned *input) {
    std::span<unsigned, 4> values(input, 4);
    return std::rotl(values[0], 3) + values[3];
}
