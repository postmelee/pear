"""Exercise the actual opt-in spawn-input audit with ordinary native Mach reads.

No Wine process, custom page mode, restricted operation or signed runtime is
executed. These checks establish bounded observation of inaccessible/unterminated
input memory, not whether posix_spawn will accept an audited launch.
"""
from pathlib import Path
import json
import platform
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / 'runtime/wine/patches/0003h-spawn-input-diagnostics.patch'


def audit_source():
    source = ''.join(line[1:] for line in PATCH.read_text().splitlines(keepends=True)
                     if line.startswith('+') and not line.startswith('+++'))
    start = source.index('#if defined(__APPLE__) && defined(__aarch64__)')
    end = source.index('\n#endif', start) + len('\n#endif')
    return source[start:end]


HARNESS = r'''
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <spawn.h>
#include <dlfcn.h>
#include <sys/mman.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
static int pear_bootstrap_enabled(void) { return 1; }
static void pear_bootstrap_event(const char *role, const char *event, const char *details)
{ (void)role; printf("{\"event\":\"%s\"%s}\n", event, details); }
'''
MAIN = r'''
int main(int argc, char **argv)
{
    struct pear_spawn_audit audit = {.outcome="ok", .part="string"};
    const char *normal[] = {"private-fixture-value-do-not-log", "two", NULL};
    const char *bad[] = {(const char *)1, NULL};
    const char **entries;
    unsigned int i;
    size_t page = (size_t)sysconf(_SC_PAGESIZE);
    char *mapping = mmap(NULL, page * 2, PROT_READ | PROT_WRITE,
                         MAP_PRIVATE | MAP_ANON, -1, 0);
    if (argc != 2 || mapping == MAP_FAILED || mprotect(mapping + page, page, PROT_NONE)) return 2;
    switch (atoi(argv[1]))
    {
    case 0:
        pear_spawn_audit_vector((uintptr_t)normal, &audit);
        break;
    case 1:
        pear_spawn_audit_vector(1, &audit);
        break;
    case 2:
        pear_spawn_audit_vector((uintptr_t)bad, &audit);
        break;
    case 3:
        memcpy(mapping + page - 8, "secret!", 8);
        pear_spawn_audit_string((uintptr_t)(mapping + page - 8), &audit);
        break;
    case 4:
        memset(mapping + page - 8, 'x', 8);
        pear_spawn_audit_string((uintptr_t)(mapping + page - 8), &audit);
        break;
    case 5:
        entries = calloc(PEAR_SPAWN_AUDIT_ENTRIES + 1, sizeof(*entries));
        if (!entries) return 3;
        for (i = 0; i <= PEAR_SPAWN_AUDIT_ENTRIES; i++) entries[i] = "";
        pear_spawn_audit_vector((uintptr_t)entries, &audit);
        free(entries);
        break;
    case 6:
        mapping = malloc(PEAR_SPAWN_AUDIT_STRING);
        if (!mapping) return 4;
        memset(mapping, 'x', PEAR_SPAWN_AUDIT_STRING);
        pear_spawn_audit_string((uintptr_t)mapping, &audit);
        free(mapping);
        break;
    case 7:
        pear_spawn_audit_vector(UINTPTR_MAX - 2, &audit);
        break;
    case 8:
    {
        posix_spawnattr_t attr;
        if (posix_spawnattr_init(&attr)) return 5;
        pear_spawn_audit_inputs("private-path-do-not-log", (char *const *)normal,
                               (char *const *)normal, &attr);
        posix_spawnattr_destroy(&attr);
        return 0;
    }
    case 9:
        unsetenv("PEAR_SPAWN_DIAGNOSTICS");
        if (pear_spawn_diagnostics_enabled()) return 6;
        setenv("PEAR_SPAWN_DIAGNOSTICS", "0", 1);
        if (pear_spawn_diagnostics_enabled()) return 7;
        setenv("PEAR_SPAWN_DIAGNOSTICS", "1", 1);
        if (!pear_spawn_diagnostics_enabled()) return 8;
        break;
    default: return 9;
    }
    pear_spawn_audit_report("fixture", &audit);
    return 0;
}
'''


@unittest.skipUnless(platform.system() == 'Darwin' and platform.machine() == 'arm64'
                     and shutil.which('clang'), 'ordinary native Apple Silicon compiler required')
class SpawnInputAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='pear-spawn-audit-')
        cls.binary = Path(cls.tmp.name) / 'audit'
        source = Path(cls.tmp.name) / 'audit.c'
        source.write_text(HARNESS + audit_source() + MAIN)
        subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-Wno-unused-function', '-O1', '-fsanitize=undefined',
                        str(source), '-o', str(cls.binary)], check=True, capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_case(self, case):
        result = subprocess.run([str(self.binary), str(case)], check=True,
                                capture_output=True, text=True, timeout=10)
        self.assertNotIn('private-', result.stderr)
        self.assertNotIn('secret!', result.stderr)
        self.assertNotIn('0x', result.stderr)
        return [json.loads(line) for line in result.stderr.splitlines()]

    def test_readable_vector(self):
        row = self.run_case(0)[0]
        self.assertEqual((row['outcome'], row['entries']), ('ok', 2))

    def test_inaccessible_vector(self):
        row = self.run_case(1)[0]
        self.assertEqual((row['outcome'], row['part'], row['index']), ('unreadable', 'vector', 0))
        self.assertNotEqual(row['error'], 0)

    def test_inaccessible_string(self):
        row = self.run_case(2)[0]
        self.assertEqual((row['outcome'], row['part'], row['index']), ('unreadable', 'string', 0))

    def test_terminator_at_protected_boundary(self):
        row = self.run_case(3)[0]
        self.assertEqual((row['outcome'], row['bytes']), ('ok', 8))

    def test_unterminated_string_into_protected_page(self):
        row = self.run_case(4)[0]
        self.assertEqual((row['outcome'], row['offset']), ('unreadable', 8))

    def test_vector_bound(self):
        row = self.run_case(5)[0]
        self.assertEqual((row['outcome'], row['part'], row['index']), ('limit', 'vector', 4096))

    def test_string_bound(self):
        row = self.run_case(6)[0]
        self.assertEqual((row['outcome'], row['offset'], row['bytes']), ('limit', 131072, 131072))

    def test_pointer_overflow(self):
        self.assertEqual(self.run_case(7)[0]['outcome'], 'overflow')

    def test_all_inputs_and_opaque_public_attribute(self):
        rows = self.run_case(8)
        self.assertEqual(rows[0]['event'], 'spawn_input_context')
        self.assertEqual([row['kind'] for row in rows[1:]], ['path', 'argv', 'envp', 'attr'])
        self.assertTrue(all(row['outcome'] == 'ok' for row in rows[1:]))
        self.assertEqual(rows[-1]['part'], 'storage_first_byte')

    def test_explicit_opt_in(self):
        self.assertEqual(self.run_case(9)[0]['outcome'], 'ok')


if __name__ == '__main__':
    unittest.main()
