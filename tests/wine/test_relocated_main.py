"""Execute the exact initial-image decision block from the ordered Wine patch.

The Wine block is LGPL-2.1-or-later. Only loader operations are stubbed; these
pure tests never load Wine, PE code, profiles or executable-memory mappings.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / 'runtime/wine/patches/0003g-relocated-main-startup.patch'


def decisions():
    before, after = [], []
    inside = False
    for line in PATCH.read_text().splitlines(keepends=True):
        if line.startswith('@@ '):
            inside = True
        elif inside:
            if line.startswith((' ', '-')):
                before.append(line[1:])
            if line.startswith((' ', '+')):
                after.append(line[1:])
    def block(value):
        start = '    if (NT_SUCCESS(status))\n'
        end = '    virtual_alloc_first_teb();\n'
        if value.count(start) != 1 or value.count(end) != 1:
            raise ValueError('expected one full initial-image decision block')
        return value[value.index(start):value.index(end)]
    return block(''.join(before)), block(''.join(after))


PREAMBLE = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef int32_t NTSTATUS;
#define NT_SUCCESS(status) ((NTSTATUS)(status) >= 0)
#define STATUS_SUCCESS ((NTSTATUS)0)
#define STATUS_IMAGE_NOT_AT_BASE ((NTSTATUS)0x40000003)
#define STATUS_INVALID_IMAGE_FORMAT ((NTSTATUS)0xc000007b)
#define IMAGE_FILE_DLL 0x2000
#define FALSE 0
static struct { unsigned ImageCharacteristics; unsigned Machine; } main_image_info;
static struct { void *Buffer; } nt_name;
static struct { int filesys_redir; } thread, *data = &thread;
static void *main_module = (void *)(uintptr_t)65536;
static int alternate, unmaps, starts, rebuilds, prepends;
static void *get_alternate_wineloader(unsigned machine) { return alternate ? malloc(1) : NULL; }
static void *GetCurrentProcess(void) { return NULL; }
static void NtUnmapViewOfSection(void *process, void *module) { ++unmaps; }
static void load_start_exe(void *name) { ++starts; }
static void prepend_argv(const char **args, unsigned count) { ++prepends; }
static void rebuild_argv(void) { ++rebuilds; }
'''


class InitialImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        clang = shutil.which('clang')
        if not clang:
            raise unittest.SkipTest('native C compiler unavailable')
        cls.temp = tempfile.TemporaryDirectory(prefix='pear-main-status-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.folder = Path(cls.temp.name)
        before, after = decisions()
        for name, code, enabled in [('before', before, False), ('plain', after, False), ('pear', after, True)]:
            text = PREAMBLE + '\nstatic NTSTATUS decide(NTSTATUS status)\n{\n' + code + '\nreturn status;\n}\n'
            text += r'''
int main(int argc, char **argv)
{
    NTSTATUS status = (NTSTATUS)strtoull(argv[1], NULL, 16);
    main_image_info.ImageCharacteristics = atoi(argv[2]) ? IMAGE_FILE_DLL : 0;
    alternate = atoi(argv[3]);
    thread.filesys_redir = 1;
    nt_name.Buffer = malloc(1);
    status = decide(status);
    printf("%08x %d %d %d %d %d\n", (unsigned)status, unmaps, starts, rebuilds, prepends, thread.filesys_redir);
    if (!unmaps) free(nt_name.Buffer);
    return 0;
}
'''
            source = cls.folder / (name + '.c')
            source.write_text(text)
            command = [clang, '-std=c11', '-fsanitize=undefined', '-fno-sanitize-recover=all']
            if enabled:
                command.append('-DPEAR_NATIVE_PE_PUBLICATION=1')
            result = subprocess.run(command + [str(source), '-o', str(cls.folder / name)],
                                    capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise AssertionError(result.stderr)

    def run_case(self, variant, status, dll=False, alternate=False):
        result = subprocess.run([str(self.folder / variant), f'{status:x}', str(int(dll)), str(int(alternate))],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        return result.stdout.strip().split()

    def test_relocated_main_is_retained_after_native_publication(self):
        self.assertEqual(self.run_case('before', 0x40000003), ['40000003', '1', '1', '0', '1', '1'])
        self.assertEqual(self.run_case('pear', 0x40000003), ['00000000', '0', '0', '1', '0', '0'])

    def test_normal_success_still_rebuilds_original_arguments(self):
        for variant in ('before', 'plain', 'pear'):
            self.assertEqual(self.run_case(variant, 0), ['00000000', '0', '0', '1', '0', '0'])

    def test_genuine_load_errors_keep_fallback_behavior(self):
        for status in (0xc0000135, 0xc0000022, 0xc000007b, 0xc00000bb):
            with self.subTest(status=status):
                expected = [f'{status:08x}', '1', '1', '0', '1', '1']
                self.assertEqual(self.run_case('pear', status), expected)
                self.assertEqual(self.run_case('plain', status), expected)

    def test_dll_and_alternate_loader_errors_are_not_normalized(self):
        for status in (0, 0x40000003):
            for dll, alternate in ((True, False), (False, True), (True, True)):
                with self.subTest(status=status, dll=dll, alternate=alternate):
                    self.assertEqual(self.run_case('pear', status, dll, alternate),
                                     ['c000007b', '1', '1', '0', '1', '1'])

    def test_other_informational_statuses_are_unchanged(self):
        self.assertEqual(self.run_case('pear', 0x4000000e), self.run_case('before', 0x4000000e))

    def test_builds_without_publication_policy_keep_original_behavior(self):
        self.assertEqual(self.run_case('plain', 0x40000003), self.run_case('before', 0x40000003))


if __name__ == '__main__':
    unittest.main()
