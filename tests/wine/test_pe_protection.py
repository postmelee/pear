"""Execute exact PE final-protection blocks extracted from the ordered patch.

The Wine source is 4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf with the preceding
Pear patches, under LGPL-2.1-or-later. Surrounding PE structures and protection
operations are synthetic; no Wine process or executable-memory operation runs.
These regressions establish fail-closed control flow, not mapping authorization
or integration cleanup qualification.
"""
from pathlib import Path
import hashlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "runtime/wine/patches/0003d-pe-protection-failure.patch"
BASELINE = ROOT / ".build/task4/build-stage3-attempt2/source/dlls/ntdll/unix/virtual.c"
BASELINE_SHA256 = "1f58c6498782faa5fb89a9173e20335a5c7afc1487b67c9efd1b58a87c6ac1a8"
AFTER_SHA256 = "f3219145c8a7063a0651f2f7d31f50c59eff834ce22651bd19be4ed275a19491"


def patch_contexts():
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
    return "".join(before), "".join(after)


def protection_blocks(source):
    """Keep actual control flow, including the success assignments after checks."""
    flat_start = "        /* set the image protections */\n"
    section_start = "    /* set the image protections */\n\n"
    flat_end = "        /* no relocations are performed on non page-aligned binaries */\n"
    for marker in (flat_start, section_start, flat_end):
        if source.count(marker) != 1:
            raise ValueError("expected one complete PE protection block")
    start = source.index(flat_start)
    end = source.index("        goto done;\n", source.index(flat_end))
    flat = source[start:end + len("        goto done;\n")]
    start = source.index(section_start)
    end = source.index("\ndone:\n", start)
    return flat, source[start:end]


PREAMBLE = r"""
#include <errno.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint32_t NTSTATUS;
typedef size_t SIZE_T;
typedef unsigned char BYTE;
#define STATUS_SUCCESS 0u
#define STATUS_INVALID_IMAGE_FORMAT 0xc000007bu
#define STATUS_ACCESS_DENIED 0xc0000022u
#define VPROT_READ 0x01
#define VPROT_WRITE 0x02
#define VPROT_EXEC 0x04
#define VPROT_WRITECOPY 0x08
#define VPROT_COMMITTED 0x20
#define IMAGE_SCN_MEM_EXECUTE 0x20000000u
#define IMAGE_SCN_MEM_READ 0x40000000u
#define IMAGE_SCN_MEM_WRITE 0x80000000u
#define ROUND_SIZE(addr, size, mask) (((size) + ((uintptr_t)(addr) & (mask)) + (mask)) & ~(mask))
struct file_view { char *base; };
struct nt_headers { struct { unsigned int NumberOfSections; } FileHeader; };
struct section {
    char Name[8];
    union { unsigned int VirtualSize; } Misc;
    unsigned int VirtualAddress, SizeOfRawData, Characteristics;
};
static int fail_call, failure_errno, calls, logs, wrong_geometry;
static BYTE observed[4];
static char diagnostic[512];
static const char *debugstr_us(const char *value)
{
    /* Exercise errno preservation across diagnostic argument evaluation. */
    errno = ERANGE;
    return value;
}
static void record_error(const char *format, ...)
{
    va_list args;
    va_start(args, format);
    vsnprintf(diagnostic, sizeof(diagnostic), format, args);
    va_end(args);
    ++logs;
    errno = EIO;
}
#define ERR(...) record_error(__VA_ARGS__)
static int set_vprot(struct file_view *view, char *base, size_t size, BYTE flags)
{
    if (calls >= 4) abort();
    if ((size != 4096 && size != 16384) || base != view->base + calls * 4096)
        ++wrong_geometry;
    observed[calls++] = flags;
    if (calls == fail_call) { errno = failure_errno; return 0; }
    return 1;
}
"""
FLAT_SETUP = r"""
static NTSTATUS flat_image(void)
{
    char memory[16384], *ptr = memory;
    struct file_view view_value = {memory}, *view = &view_value;
    size_t total_size = sizeof(memory);
    const char *nt_name = "fixture.exe";
    (void)nt_name;
    NTSTATUS status = STATUS_INVALID_IMAGE_FORMAT;
"""
SECTION_SETUP = r"""
static NTSTATUS section_image(void)
{
    char memory[16384], *ptr = memory;
    struct file_view view_value = {memory}, *view = &view_value;
    struct nt_headers headers = {{3}}, *nt = &headers;
    struct section sec[] = {
        {".text", {4096}, 4096, 4096, IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_EXECUTE},
        {".data", {0}, 8192, 17, IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE},
        {".rdata", {3}, 12288, 3, IMAGE_SCN_MEM_READ}
    };
    const char *nt_name = "fixture.exe";
    size_t header_size = 512, align_mask = 4095;
    unsigned int i;
    NTSTATUS status = STATUS_INVALID_IMAGE_FORMAT;
"""
END = "\n    goto done;\ndone:\n    return status;\n}\n"
MAIN = r"""
int main(int argc, char **argv)
{
    NTSTATUS status;
    if (argc != 4) return 2;
    fail_call = atoi(argv[2]);
    failure_errno = atoi(argv[3]);
    if (!strcmp(argv[1], "flat")) status = flat_image();
    else if (!strcmp(argv[1], "sections")) status = section_image();
    else return 3;
    printf("%08x %d %d %d %u %u %u %u\n", status, calls, logs, wrong_geometry,
           observed[0], observed[1], observed[2], observed[3]);
    fputs(diagnostic, stderr);
    return 0;
}
"""


class PEProtectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler = shutil.which("clang")
        if not cls.compiler:
            raise unittest.SkipTest("Clang unavailable; extracted protection execution unperformed")
        cls.contexts = patch_contexts()
        cls.directory = tempfile.TemporaryDirectory(prefix="pear-pe-protection-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.root = Path(cls.directory.name)
        for name, context in zip(("before", "after"), cls.contexts):
            flat, sections = protection_blocks(context)
            source = cls.root / (name + ".c")
            source.write_text(PREAMBLE + FLAT_SETUP + flat + END +
                              SECTION_SETUP + sections + END + MAIN)
            result = subprocess.run([cls.compiler, "-O0", "-Wall", "-Wextra", "-Werror",
                                     "-fsanitize=undefined", "-fno-sanitize-recover=all",
                                     str(source), "-o", str(cls.root / name)],
                                    capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise RuntimeError("extracted C harness compilation failed: " + result.stderr)

    def execute(self, version, scenario, fail_call=0, failure_errno=13):
        result = subprocess.run([str(self.root / version), scenario, str(fail_call),
                                 str(failure_errno)], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        fields = result.stdout.split()
        self.assertEqual(len(fields), 8, result.stdout)
        self.assertEqual(fields[3], "0", "unexpected 4 KiB protection geometry")
        return fields[0], int(fields[1]), int(fields[2]), list(map(int, fields[4:])), result.stderr

    def test_patch_applies_to_preserved_exact_source_when_available(self):
        if not BASELINE.is_file():
            self.skipTest("preserved actual source unavailable; source binding unperformed")
        data = BASELINE.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), BASELINE_SHA256)
        self.assertEqual(protection_blocks(data.decode()), protection_blocks(self.contexts[0]))
        destination = self.root / "applied/dlls/ntdll/unix/virtual.c"
        destination.parent.mkdir(parents=True)
        destination.write_bytes(data)
        patch_tool = shutil.which("patch")
        if not patch_tool:
            self.skipTest("patch utility unavailable; full source application unperformed")
        result = subprocess.run([patch_tool, "--batch", "--fuzz=0", "-p1", "-i", str(PATCH)],
                                cwd=self.root / "applied", capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(hashlib.sha256(destination.read_bytes()).hexdigest(), AFTER_SHA256)
        self.assertEqual(protection_blocks(destination.read_text()), protection_blocks(self.contexts[1]))

    def test_success_preserves_protection_order_flags_and_4k_ranges(self):
        for version in ("before", "after"):
            for scenario, expected in (("flat", [0x2d, 0, 0, 0]),
                                       ("sections", [0x21, 0x25, 0x29, 0x21])):
                with self.subTest(version=version, scenario=scenario):
                    status, calls, logs, flags, diagnostic = self.execute(version, scenario)
                    self.assertEqual(status, "00000000")
                    self.assertEqual(calls, 1 if scenario == "flat" else 4)
                    self.assertEqual(flags, expected)
                    self.assertEqual((logs, diagnostic), (0, ""))

    def test_baseline_returns_success_after_each_injected_failure(self):
        for scenario, failures in (("flat", (1,)), ("sections", (1, 2, 3, 4))):
            for failure in failures:
                with self.subTest(scenario=scenario, failure=failure):
                    status, calls, _, _, _ = self.execute("before", scenario, failure)
                    self.assertEqual(status, "00000000")
                    self.assertEqual(calls, 1 if scenario == "flat" else 4)

    def test_flat_failure_stops_before_success_assignment(self):
        status, calls, logs, _, diagnostic = self.execute("after", "flat", 1)
        self.assertEqual((status, calls, logs), ("c0000022", 1, 1))
        self.assertIn("flat image protection", diagnostic)
        self.assertIn("errno 13", diagnostic)

    def test_header_failure_stops_before_any_section(self):
        status, calls, logs, flags, diagnostic = self.execute("after", "sections", 1)
        self.assertEqual((status, calls, logs), ("c0000022", 1, 1))
        self.assertEqual(flags, [0x21, 0, 0, 0])
        self.assertIn("image header protection", diagnostic)

    def test_each_section_failure_stops_before_later_sections(self):
        for failure, name in ((2, ".text"), (3, ".data"), (4, ".rdata")):
            with self.subTest(section=name):
                status, calls, logs, flags, diagnostic = self.execute("after", "sections", failure)
                self.assertEqual((status, calls, logs), ("c0000022", failure, 1))
                self.assertEqual(flags[failure:], [0] * (4 - failure))
                self.assertIn("section " + name, diagnostic)

    def test_errno_snapshot_survives_diagnostic_formatting_for_all_paths(self):
        for scenario, failure in (("flat", 1), ("sections", 1), ("sections", 2)):
            for error in (1, 13, 22):
                with self.subTest(scenario=scenario, failure=failure, error=error):
                    status, _, _, _, diagnostic = self.execute("after", scenario, failure, error)
                    self.assertEqual(status, "c0000022")
                    self.assertIn("errno " + str(error) + " (", diagnostic)


if __name__ == "__main__":
    unittest.main()
