"""Execute the exact image-count gate and enumeration from the ordered patch.

The extracted LGPL-2.1-or-later function uses synthetic dyld observations and
an event sink. Ordinary native child processes retain the real exit status;
no Wine, PE, signing, page-mode changes or runtime qualification occurs.
"""
from pathlib import Path
import errno
import json
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / 'runtime/wine/patches/0003j-image-count-diagnostic.patch'


def image_functions(patch=PATCH):
    before, after = [], []
    inside = False
    for line in patch.read_text().splitlines(keepends=True):
        if line.startswith('@@ '):
            inside = True
        elif inside:
            if line.startswith((' ', '-')):
                before.append(line[1:])
            if line.startswith((' ', '+')):
                after.append(line[1:])
    def function(lines):
        text = ''.join(lines)
        start = 'static inline __attribute__((unused)) void pear_bootstrap_images( const char *role )\n'
        if text.count(start) != 1:
            raise ValueError('expected one complete image enumeration function')
        begin = text.index(start)
        end = text.index('\n}\n', begin) + 3
        return text[begin:end]
    return function(before), function(after)


HARNESS = r'''
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#define MH_MAGIC_64 0xfeedfacfu
#define LC_UUID 0x1bu
struct mach_header_64 { uint32_t magic; int32_t cputype, cpusubtype; uint32_t filetype, ncmds, sizeofcmds, flags, reserved; };
struct load_command { uint32_t cmd, cmdsize; };
struct uuid_command { uint32_t cmd, cmdsize; uint8_t uuid[16]; };
static struct { struct mach_header_64 header; struct uuid_command uuid; } sample;
static uint32_t supplied_count;
static unsigned int count_calls, header_calls, name_calls;
static int enabled = 1, malformed;
static int pear_bootstrap_enabled(void) { return enabled; }
static uint32_t _dyld_image_count(void) { count_calls++; return supplied_count; }
static const void *_dyld_get_image_header(uint32_t index)
{
    (void)index;
    header_calls++;
    return malformed == 1 || (malformed == 3 && index == supplied_count - 1) ? NULL : &sample.header;
}
static const char *_dyld_get_image_name(uint32_t index)
{
    (void)index;
    name_calls++;
    return "/System/Library/PearSynthetic.dylib";
}
static int pear_bootstrap_escape(char *out, size_t size, const char *input)
{
    if (strlen(input) >= size) return 0;
    strcpy(out, input);
    return 1;
}
static void pear_bootstrap_event(const char *role, const char *event, const char *details)
{
    printf("{\"role\":\"%s\",\"event\":\"%s\",\"count_calls\":%u,"
           "\"header_calls\":%u,\"name_calls\":%u%s}\n",
           role, event, count_calls, header_calls, name_calls, details);
}
static void pear_bootstrap_failure(const char *role, const char *operation, int error)
{
    char details[128];
    snprintf(details, sizeof(details), ",\"operation\":\"%s\",\"error\":%d", operation, error);
    pear_bootstrap_event(role, "failure", details);
    _exit(125);
}
'''
MAIN = r'''
int main(int argc, char **argv)
{
    if (argc != 4 || setvbuf(stdout, NULL, _IONBF, 0)) return 2;
    supplied_count = (uint32_t)strtoull(argv[1], NULL, 10);
    enabled = atoi(argv[2]);
    malformed = atoi(argv[3]);
    sample.header.magic = MH_MAGIC_64;
    sample.header.cputype = 0x0100000c;
    sample.header.ncmds = 1;
    sample.header.sizeofcmds = sizeof(sample.uuid);
    sample.uuid.cmd = LC_UUID;
    sample.uuid.cmdsize = malformed == 2 ? 0 : sizeof(sample.uuid);
    for (unsigned int i = 0; i < 16; i++) sample.uuid.uuid[i] = i;
    pear_bootstrap_images("loader");
    pear_bootstrap_event("loader", "returned", "");
    return 0;
}
'''


@unittest.skipUnless(shutil.which('clang'), 'ordinary native C compiler required')
class ImageCountTests(unittest.TestCase):
    patch = PATCH

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='pear-image-count-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.folder = Path(cls.temp.name)
        for variant, source in zip(('before', 'after'), image_functions(cls.patch)):
            path = cls.folder / (variant + '.c')
            path.write_text(HARNESS + source + MAIN)
            result = subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror',
                '-O1', '-fsanitize=undefined', '-fno-sanitize-recover=all', str(path),
                '-o', str(cls.folder / variant)], capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise AssertionError(result.stderr)

    def run_case(self, variant, count, enabled=True, malformed=0):
        result = subprocess.run([str(self.folder / variant), str(count), str(int(enabled)), str(malformed)],
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.stderr, '')
        return result.returncode, [json.loads(line) for line in result.stdout.splitlines()]

    def test_exact_limit_enumerates_every_image_unchanged(self):
        before = self.run_case('before', 1024)
        after = self.run_case('after', 1024)
        self.assertEqual(after, before)
        code, rows = after
        self.assertEqual(code, 0)
        images = [row for row in rows if row['event'] == 'image']
        self.assertEqual([row['index'] for row in images], list(range(1024)))
        self.assertTrue(all(row['cpu_type'] == 0x0100000c and
            row['uuid'] == '000102030405060708090a0b0c0d0e0f' for row in images))
        self.assertEqual((rows[-2]['event'], rows[-2]['count'], rows[-2]['header_calls']),
                         ('images_end', 1024, 1024))
        self.assertEqual(rows[-2]['name_calls'], 1024)

    def test_over_limit_preserves_count_without_enumerating(self):
        for count in (1025, 4096, 2**32 - 1):
            with self.subTest(count=count):
                code, rows = self.run_case('after', count)
                self.assertEqual(code, 125)
                self.assertEqual(rows, [{'role': 'loader', 'event': 'failure',
                    'count_calls': 1, 'header_calls': 0, 'name_calls': 0,
                    'operation': 'image_count', 'error': errno.EOVERFLOW,
                    'observed_count': count, 'limit': 1024}])
                old_code, old_rows = self.run_case('before', count)
                self.assertEqual(old_code, code)
                self.assertEqual(old_rows, [{key: value for key, value in rows[0].items()
                    if key not in ('observed_count', 'limit')}])

    def test_below_limit_and_empty_counts_keep_original_behavior(self):
        for count in (0, 1, 1023):
            with self.subTest(count=count):
                self.assertEqual(self.run_case('after', count), self.run_case('before', count))

    def test_disabled_observer_does_not_query_or_enumerate(self):
        for variant in ('before', 'after'):
            code, rows = self.run_case(variant, 2**32 - 1, enabled=False)
            self.assertEqual(code, 0)
            self.assertEqual(rows, [{'role': 'loader', 'event': 'returned',
                'count_calls': 0, 'header_calls': 0, 'name_calls': 0}])

    def test_invalid_image_identity_still_fails(self):
        before = self.run_case('before', 1, malformed=1)
        after = self.run_case('after', 1, malformed=1)
        self.assertEqual(after, before)
        self.assertEqual(after[0], 125)
        self.assertEqual(after[1][0]['operation'], 'image_identity')

    def test_invalid_load_command_still_fails(self):
        before = self.run_case('before', 1, malformed=2)
        after = self.run_case('after', 1, malformed=2)
        self.assertEqual(after, before)
        self.assertEqual(after[0], 125)
        self.assertEqual(after[1][0]['operation'], 'image_commands')


class ImageObservationBudgetTests(ImageCountTests):
    """Reuse the native harness and unchanged malformed/disabled controls."""
    patch = ROOT / 'runtime/wine/patches/0003k-image-observation-budget.patch'

    def assert_full_inventory(self, count):
        code, rows = self.run_case('after', count)
        self.assertEqual(code, 0)
        self.assertEqual(len(rows), count + 2)
        images = rows[:-2]
        self.assertEqual([row['event'] for row in images], ['image'] * count)
        self.assertEqual([row['index'] for row in images], list(range(count)))
        self.assertTrue(all(row['cpu_type'] == 0x0100000c and
            row['uuid'] == '000102030405060708090a0b0c0d0e0f' and
            row['path'] == '/System/Library/PearSynthetic.dylib' for row in images))
        self.assertEqual((rows[-2]['event'], rows[-2]['count'], rows[-2]['header_calls'],
            rows[-2]['name_calls']), ('images_end', count, count, count))
        self.assertEqual(rows[-1]['event'], 'returned')
        return images

    def test_observed_1041_images_are_fully_enumerated(self):
        self.assert_full_inventory(1041)
        code, rows = self.run_case('before', 1041)
        self.assertEqual(code, 125)
        self.assertEqual((rows[0]['operation'], rows[0]['observed_count'], rows[0]['limit']),
                         ('image_count', 1041, 1024))
        self.assertEqual(rows[0]['header_calls'], 0)

    def test_exact_limit_enumerates_every_image_unchanged(self):
        images = self.assert_full_inventory(2048)
        old_code, old_rows = self.run_case('before', 1024)
        self.assertEqual(old_code, 0)
        self.assertEqual(images[:1024], old_rows[:-2])

    def test_over_limit_preserves_count_without_enumerating(self):
        for count in (2049, 4096, 2**32 - 1):
            with self.subTest(count=count):
                code, rows = self.run_case('after', count)
                self.assertEqual(code, 125)
                self.assertEqual(rows, [{'role': 'loader', 'event': 'failure',
                    'count_calls': 1, 'header_calls': 0, 'name_calls': 0,
                    'operation': 'image_count', 'error': errno.EOVERFLOW,
                    'observed_count': count, 'limit': 2048}])
                old_code, old_rows = self.run_case('before', count)
                self.assertEqual(old_code, code)
                self.assertEqual(old_rows, [{**rows[0], 'limit': 1024}])

    def test_below_limit_and_empty_counts_keep_original_behavior(self):
        for count in (0, 1, 1023, 1024):
            with self.subTest(count=count):
                self.assertEqual(self.run_case('after', count), self.run_case('before', count))

    def test_invalid_image_in_added_range_is_not_skipped(self):
        for count in (1041, 2048):
            with self.subTest(count=count):
                code, rows = self.run_case('after', count, malformed=3)
                self.assertEqual(code, 125)
                self.assertEqual([row['index'] for row in rows[:-1]], list(range(count - 1)))
                self.assertEqual((rows[-1]['event'], rows[-1]['operation'], rows[-1]['header_calls']),
                                 ('failure', 'image_identity', count))
                self.assertFalse(any(row['event'] == 'images_end' for row in rows))


if __name__ == '__main__':
    unittest.main()
