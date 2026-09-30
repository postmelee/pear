"""Execute the exact patched Wine bitmap predicate as a standalone C regression.

The function is extracted from patch context, not reimplemented. Its upstream
source is Wine 4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf, LGPL-2.1-or-later.
Only the predicate's surrounding types and globals are synthetic. This does not
execute Wine, enter foreign x18 mode, or qualify PE startup or ARM64EC support.
"""
from pathlib import Path
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "runtime/wine/patches/0003c-native-pe-startup.patch"
BASELINE = ROOT / ".build/task4/build-stage3/source/dlls/ntdll/unix/virtual.c"
BASELINE_SHA256 = "26bf2d477dd7c5aa8a73546de82836af01b5a8e2e22e9131b1682c89b7ba8585"


def function(source):
    """Extract a complete definition, rejecting missing or duplicate matches."""
    matches = list(re.finditer(r"^BOOL is_emulated_code\( ULONG_PTR ptr \)\n\{", source, re.M))
    if len(matches) != 1:
        raise ValueError("expected one complete is_emulated_code definition")
    start = matches[0].start()
    level = 0
    for index in range(matches[0].end() - 1, len(source)):
        if source[index] == "{":
            level += 1
        elif source[index] == "}":
            level -= 1
            if not level:
                return source[start:index + 1] + "\n"
    raise ValueError("unterminated is_emulated_code definition")


def patch_functions():
    before, after = [], []
    in_hunk = False
    for line in PATCH.read_text().splitlines(keepends=True):
        if line.startswith("@@ "):
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if line.startswith((" ", "-")):
            before.append(line[1:])
        if line.startswith((" ", "+")):
            after.append(line[1:])
    return function("".join(before)), function("".join(after))


PREAMBLE = r"""
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef int BOOL;
typedef uint64_t UINT64;
typedef uintptr_t ULONG_PTR;
#define FALSE 0
struct file_view { void *base; };
static struct file_view *arm64ec_view;
static const ULONG_PTR page_size = 4096;
static const void *user_space_limit = (void *)(128 * 4096);
static int arm64ec;
static BOOL is_arm64ec(void) { return arm64ec; }
"""
HARNESS = r"""
int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    if (!strcmp(argv[1], "non-ec-null-view"))
    {
        const ULONG_PTR addresses[] = {0, 4095, 64 * 4096, 128 * 4096, UINTPTR_MAX};
        arm64ec = 0;
        arm64ec_view = NULL;
        for (unsigned int i = 0; i < sizeof(addresses) / sizeof(addresses[0]); ++i)
            if (is_emulated_code(addresses[i]) != FALSE) return 10;
        puts("non-ec-null-view:5");
        return 0;
    }
    if (!strcmp(argv[1], "ec-outside-range-null-view"))
    {
        const ULONG_PTR addresses[] = {128 * 4096, 128 * 4096 + 1, UINTPTR_MAX};
        arm64ec = 1;
        arm64ec_view = NULL;
        for (unsigned int i = 0; i < sizeof(addresses) / sizeof(addresses[0]); ++i)
            if (is_emulated_code(addresses[i]) != FALSE) return 11;
        puts("ec-outside-range-null-view:3");
        return 0;
    }
    if (!strcmp(argv[1], "ec-bitmap"))
    {
        /* Page zero, both sides of the word boundary, and the last valid page. */
        UINT64 bits[2] = {UINT64_C(0x8000000000000001), UINT64_C(0x8000000000000001)};
        struct file_view view = {bits};
        arm64ec = 1;
        arm64ec_view = &view;
        for (ULONG_PTR page = 0; page < 128; ++page)
        {
            int expected = !(page == 0 || page == 63 || page == 64 || page == 127);
            if (is_emulated_code(page * 4096) != expected) return 12;
            if (is_emulated_code(page * 4096 + 4095) != expected) return 13;
        }
        puts("ec-bitmap:256");
        return 0;
    }
    return 3;
}
"""


class NativeStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler = shutil.which("clang")
        if not cls.compiler:
            raise unittest.SkipTest("Clang is unavailable; standalone predicate execution unperformed")
        cls.before, cls.after = patch_functions()
        cls.directory = tempfile.TemporaryDirectory(prefix="pear-native-startup-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.root = Path(cls.directory.name)
        for name, body in (("before", cls.before), ("after", cls.after)):
            source = cls.root / (name + ".c")
            source.write_text(PREAMBLE + body + HARNESS)
            subprocess.run([cls.compiler, "-O0", "-Wall", "-Wextra", "-Werror",
                            "-fsanitize=undefined", "-fno-sanitize-recover=all",
                            str(source), "-o", str(cls.root / name)],
                           check=True, capture_output=True, timeout=30)

    def execute(self, version, scenario):
        environment = os.environ.copy()
        environment["UBSAN_OPTIONS"] = "halt_on_error=1:abort_on_error=0:print_stacktrace=0"
        return subprocess.run([str(self.root / version), scenario], capture_output=True,
                              text=True, timeout=5, env=environment)

    def test_patch_context_matches_preserved_actual_source_when_available(self):
        if not BASELINE.is_file():
            self.skipTest("preserved actual Stage 3 source unavailable; source binding unperformed")
        data = BASELINE.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), BASELINE_SHA256)
        self.assertEqual(function(data.decode()), self.before)

    def test_baseline_eager_access_is_detected_before_guard(self):
        for scenario in ("non-ec-null-view", "ec-outside-range-null-view"):
            with self.subTest(scenario=scenario):
                result = self.execute("before", scenario)
                self.assertGreater(result.returncode, 0, result.stderr)
                self.assertRegex(result.stderr, r"runtime error:.*null pointer")
                self.assertEqual(result.stdout, "")

    def test_native_arm64_does_not_require_an_arm64ec_view(self):
        result = self.execute("after", "non-ec-null-view")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "non-ec-null-view:5\n")
        self.assertEqual(result.stderr, "")

    def test_out_of_range_addresses_do_not_require_an_arm64ec_view(self):
        result = self.execute("after", "ec-outside-range-null-view")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "ec-outside-range-null-view:3\n")
        self.assertEqual(result.stderr, "")

    def test_arm64ec_bitmap_lookup_is_preserved(self):
        for version in ("before", "after"):
            with self.subTest(version=version):
                result = self.execute(version, "ec-bitmap")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "ec-bitmap:256\n")
                self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
