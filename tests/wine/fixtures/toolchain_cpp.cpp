// Original Pear C++17 language fixture; compile and inspect only.
#if __cplusplus < 201703L
#error This fixture requires C++17.
#endif

namespace pear_toolchain
{
inline constexpr int base = 19;

template<typename... Values>
constexpr auto sum(Values... values)
{
    return (values + ...);
}

template<typename Value>
struct pair
{
    Value left;
    Value right;
};

template<typename Value> pair(Value, Value) -> pair<Value>;

template<typename Value>
constexpr int result(Value value)
{
    if constexpr (sizeof(Value) == sizeof(int))
    {
        const auto [left, right] = pair{base, value};
        return sum(left, right);
    }
    else
    {
        return 0;
    }
}

static_assert(result(23) == 42, "C++17 constant evaluation must yield 42");
}

extern "C" int pear_toolchain_cpp(int input)
{
    return pear_toolchain::result(input);
}
