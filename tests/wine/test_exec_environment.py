"""Exercise the actual Wine exec environment delta, without executing Wine.

Darwin cases use the host C library's real setenv and inspect ownership while
inside the extracted function. Other-platform and failure boundaries are mocked
explicitly. This is not proof of kernel exec behavior or a qualified runtime.
"""
from pathlib import Path
import errno
import json
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / 'runtime/wine/patches/0003i-owned-exec-environment.patch'


def exec_function():
    lines = []
    active = False
    for line in PATCH.read_text().splitlines(keepends=True):
        if line.startswith('@@ '):
            active = True
        elif active and line.startswith((' ', '+')):
            lines.append(line[1:])
    source = ''.join(lines)
    start = source.index('NTSTATUS exec_wineloader(')
    end = source.index('\n}\n', start) + 3
    return source[start:end]


HARNESS = r'''
#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <signal.h>
#include <setjmp.h>
typedef uint32_t NTSTATUS, UINT;
typedef uint16_t WORD;
typedef uint64_t ULONGLONG;
struct pe_image_info { WORD machine; ULONGLONG base, map_size; int wine_fakedll; unsigned image_flags; };
#define IMAGE_FLAGS_ComPlusNativeReady 1u
#define IMAGE_FILE_MACHINE_AMD64 0x8664u
#define IMAGE_FILE_MACHINE_I386 0x14cu
static const WORD native_machine = 0xaa64;
static int is_machine_64bit(WORD machine) { return machine == 0xaa64; }
static int set_calls, put_calls, launches, owned, inject_call, bootstrap, fatal_error, mapped_error;
static WORD launched_machine;
static NTSTATUS loader_result = 0x12345678u;
static char reserve_value[128], socket_value[128], fatal_operation[64];
static jmp_buf failure_jump;
static int pear_bootstrap_enabled(void) { return bootstrap; }
static void pear_bootstrap_failure(const char *role, const char *operation, int error)
{
    (void)role;
    fatal_error = error;
    snprintf(fatal_operation, sizeof(fatal_operation), "%s", operation);
    longjmp(failure_jump, 1);
}
static NTSTATUS errno_to_status(int error) { mapped_error = error; errno = EDOM; return 0xc0000000u | error; }
static int observed_setenv(const char *name, const char *value, int overwrite)
{
    int ret;
    set_calls++;
    if (set_calls == inject_call) { errno = ENOMEM; return -1; }
    if (overwrite != 1) abort();
    ret = setenv(name, value, overwrite);
    if (!ret && getenv(name) != value) owned++;
    return ret;
}
static int observed_putenv(char *entry)
{
    const char *equals = strchr(entry, '=');
    put_calls++;
    if (!equals) abort();
    if (!strncmp(entry, "WINEPRELOADRESERVE=", sizeof("WINEPRELOADRESERVE=") - 1))
        snprintf(reserve_value, sizeof(reserve_value), "%s", equals + 1);
    else if (!strncmp(entry, "WINESERVERSOCKET=", sizeof("WINESERVERSOCKET=") - 1))
        snprintf(socket_value, sizeof(socket_value), "%s", equals + 1);
    else abort();
    return 0;
}
static NTSTATUS loader_exec(char **argv, WORD machine)
{
    if (!argv) abort();
    launches++;
    launched_machine = machine;
    if (set_calls)
    {
        snprintf(reserve_value, sizeof(reserve_value), "%s", getenv("WINEPRELOADRESERVE"));
        snprintf(socket_value, sizeof(socket_value), "%s", getenv("WINESERVERSOCKET"));
    }
    return loader_result;
}
#define setenv observed_setenv
#define putenv observed_putenv
'''
MAIN = r'''
#undef setenv
#undef putenv
int main(int argc, char **argv)
{
    struct pe_image_info image = {0xaa64, 0x123456789abcdef0ull, 0x1000, 0, 0};
    NTSTATUS status = 0;
    int test, observed_errno;
    if (argc != 2) return 2;
    test = atoi(argv[1]);
    if (setenv("WINEPRELOADRESERVE", "old-reservation", 1) ||
        setenv("WINESERVERSOCKET", "old-socket", 1)) return 3;
    if (test == 1) image.wine_fakedll = 1;
    if (test == 2 || test == 4) inject_call = 1;
    if (test == 3 || test == 5) inject_call = 2;
    if (test == 4 || test == 5) bootstrap = 1;
    if (test == 6) image.image_flags = IMAGE_FLAGS_ComPlusNativeReady;
    if (test == 7) loader_result = 0xc000007bu;
    errno = 0;
    if (!setjmp(failure_jump)) status = exec_wineloader(argv, 1234, &image);
    observed_errno = errno;
    printf("{\"status\":%u,\"set_calls\":%d,\"put_calls\":%d,\"launches\":%d,"
           "\"owned_copies\":%d,\"fatal_error\":%d,\"mapped_error\":%d,\"errno\":%d,"
           "\"machine\":%u,\"fatal_operation\":\"%s\",\"reserve\":\"%s\",\"socket\":\"%s\"}\n",
           status, set_calls, put_calls, launches, owned, fatal_error, mapped_error, observed_errno,
           launched_machine, fatal_operation, reserve_value, socket_value);
    return 0;
}
'''


@unittest.skipUnless(shutil.which('clang'), 'ordinary C compiler required')
class OwnedExecEnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='pear-owned-environment-')
        cls.binaries = {}
        for darwin in (False, True):
            binary = Path(cls.tmp.name) / f'exec-{darwin}'
            source = binary.with_suffix('.c')
            policy = '\n#undef __APPLE__\n#undef __aarch64__\n'
            if darwin:
                policy += '#define __APPLE__ 1\n#define __aarch64__ 1\n'
            source.write_text(HARNESS + policy + exec_function() + MAIN)
            result = subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror',
                                     '-Wno-unused-function', '-O1', '-fsanitize=undefined',
                                     str(source), '-o', str(binary)], capture_output=True, text=True)
            if result.returncode:
                raise AssertionError(result.stderr)
            cls.binaries[darwin] = binary

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_case(self, case, darwin=True):
        result = subprocess.run([str(self.binaries[darwin]), str(case)], check=True,
                                capture_output=True, text=True, timeout=10)
        return json.loads(result.stdout)

    def test_exact_values_overwrite_and_owned_copies(self):
        row = self.run_case(0)
        self.assertEqual((row['reserve'], row['socket']), ('123456789abcdef0-123456789abceef0', '1234'))
        self.assertEqual((row['set_calls'], row['put_calls'], row['owned_copies'], row['launches']), (2, 0, 2, 1))
        self.assertEqual(row['status'], 0x12345678)

    def test_fake_dll_zero_range_preserved(self):
        row = self.run_case(1)
        self.assertEqual((row['reserve'], row['socket']), ('000000000-000000000', '1234'))

    def test_first_allocation_failure_stops_launch(self):
        row = self.run_case(2)
        self.assertEqual((row['set_calls'], row['owned_copies'], row['launches']), (1, 0, 0))
        self.assertEqual((row['errno'], row['mapped_error'], row['status']),
                         (errno.ENOMEM, errno.ENOMEM, 0xc0000000 | errno.ENOMEM))

    def test_second_allocation_failure_stops_launch(self):
        row = self.run_case(3)
        self.assertEqual((row['set_calls'], row['owned_copies'], row['launches']), (2, 1, 0))
        self.assertEqual((row['errno'], row['mapped_error']), (errno.ENOMEM, errno.ENOMEM))

    def test_bootstrap_reports_first_failure(self):
        row = self.run_case(4)
        self.assertEqual((row['fatal_operation'], row['fatal_error'], row['launches']),
                         ('exec_environment', errno.ENOMEM, 0))
        self.assertEqual(row['mapped_error'], 0)

    def test_bootstrap_reports_second_failure(self):
        row = self.run_case(5)
        self.assertEqual((row['fatal_operation'], row['fatal_error'], row['launches'], row['set_calls']),
                         ('exec_environment', errno.ENOMEM, 0, 2))

    def test_machine_selection_preserved(self):
        self.assertEqual(self.run_case(6)['machine'], 0x8664)

    def test_failed_loader_return_is_preserved(self):
        row = self.run_case(7)
        self.assertEqual((row['status'], row['set_calls'], row['launches']), (0xc000007b, 2, 1))
        self.assertEqual((row['mapped_error'], row['fatal_error']), (0, 0))

    def test_other_platform_retains_putenv(self):
        row = self.run_case(0, darwin=False)
        self.assertEqual((row['set_calls'], row['put_calls'], row['launches']), (0, 2, 1))
        self.assertEqual((row['reserve'], row['socket']), ('123456789abcdef0-123456789abceef0', '1234'))


if __name__ == '__main__':
    unittest.main()
