/* Original Pear PE export fixture. Compile and inspect; do not execute. */
#if !defined(_WIN32)
#error This fixture requires a Windows PE target.
#endif

__declspec(dllexport) int pear_toolchain_add(int left, int right)
{
    return left + right;
}
