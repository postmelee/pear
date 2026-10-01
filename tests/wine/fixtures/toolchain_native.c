/* Original Pear compiler fixture; ordinary native execution only. */
#include <stdio.h>

#if !defined(__APPLE__) || !defined(__aarch64__)
#error This fixture requires native ARM64 macOS compilation.
#endif

int main(void)
{
    volatile int input = 40;
    const int value = input + 2;

    if (value != 42) return 1;
    if (printf("{\"fixture\":\"pear-toolchain-native-v1\",\"value\":%d}\n", value) < 0)
        return 1;
    return fflush(stdout) == 0 ? 0 : 1;
}
