/* Original Pear PE import fixture. Compile and inspect; do not execute. */
#if !defined(_WIN32)
#error This fixture requires a Windows PE target.
#endif

__declspec(dllimport) int pear_toolchain_add(int left, int right);

/* A custom entry avoids conflating linker checks with CRT startup support. */
int pear_toolchain_entry(void)
{
    return pear_toolchain_add(19, 23);
}
