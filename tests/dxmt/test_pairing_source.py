"""Original refusal controls for source-derived graphics supplements."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools/dxmt'))
spec = importlib.util.spec_from_file_location('_pear_pairing_source', REPO / 'tools/dxmt/pairing_source.py')
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)


class SourceProjectionControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pear-pairing-source-unit-')
        self.root = Path(self.temp.name).resolve()
        self.cache = self.root / 'cache'
        self.cache.mkdir()
        (self.cache / 'unit.c').write_bytes(b'old source\n')
        (self.cache / 'keep').write_bytes(b'unchanged\n')
        (self.cache / 'unit.c').chmod(0o644)
        (self.cache / 'keep').chmod(0o755)
        self.raw = (b'diff --git a/unit.c b/unit.c\n--- a/unit.c\n+++ b/unit.c\n'
                    b'@@ -1 +1 @@\n-old source\n+new source\n')
        self.declared = [{'path': 'unit.c', 'before_sha256': source.digest(b'old source\n'),
                          'after_sha256': source.digest(b'new source\n'), 'mode': '100644',
                          'payload_file': None, 'payload_sha256': None}]

    def tearDown(self):
        self.temp.cleanup()

    def project(self, destination=None):
        return source.project(self.cache, destination or self.root / 'output',
                              self.declared, source.patch_sections(self.raw))

    def test_exact_change_preserves_cache_unmodified_files_and_modes(self):
        before, after = self.project()
        self.assertEqual((self.cache / 'unit.c').read_bytes(), b'old source\n')
        self.assertEqual((self.root / 'output/unit.c').read_bytes(), b'new source\n')
        self.assertEqual([row for row in before if row['path'] == 'keep'],
                         [row for row in after if row['path'] == 'keep'])

    def test_changed_preimage_refuses_without_mutating_cache(self):
        (self.cache / 'unit.c').write_bytes(b'changed cache\n')
        with self.assertRaises(source.Error):
            self.project()
        self.assertEqual((self.cache / 'unit.c').read_bytes(), b'changed cache\n')

    def test_wrong_postimage_is_refused(self):
        self.declared[0]['after_sha256'] = '0' * 64
        with self.assertRaises(source.Error) as raised:
            self.project()
        self.assertEqual(getattr(raised.exception, 'code', None), 'pair_source_postimage')

    def test_exact_context_refuses_fuzzy_match(self):
        self.raw = self.raw.replace(b'-old source\n', b'-wrong source\n')
        with self.assertRaises(source.Error) as raised:
            self.project()
        self.assertEqual(getattr(raised.exception, 'code', None), 'pair_patch_context')

    def test_hunk_counts_are_checked(self):
        raw = self.raw.replace(b'@@ -1 +1 @@', b'@@ -1,2 +1 @@')
        with self.assertRaises(source.Error) as raised:
            source.apply_hunks(b'old source\n', source.patch_sections(raw)['unit.c'], 'unit.c')
        self.assertEqual(getattr(raised.exception, 'code', None), 'pair_patch_hunk_count')

    def test_changed_hunk_target_is_refused(self):
        with self.assertRaises(source.Error):
            source.patch_sections(self.raw.replace(b'b/unit.c\n---', b'b/other.c\n---'))

    def test_duplicate_and_escape_targets_are_refused(self):
        for raw in [self.raw + self.raw, self.raw.replace(b'unit.c', b'../outside')]:
            with self.subTest(raw=raw), self.assertRaises(source.Error):
                source.patch_sections(raw)

    def test_cache_alias_is_refused(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.cache, target_is_directory=True)
        with self.assertRaises(source.Error):
            source.project(alias, self.root / 'output', self.declared, source.patch_sections(self.raw))

    def test_existing_or_aliased_output_is_refused(self):
        existing = self.root / 'existing'
        existing.mkdir()
        alias = self.root / 'alias'
        alias.symlink_to(existing, target_is_directory=True)
        for destination in [existing, alias]:
            with self.subTest(destination=destination), self.assertRaises(source.Error):
                self.project(destination)
        self.assertEqual(list(existing.iterdir()), [])

    def test_declared_regular_addition_mode_is_preserved(self):
        lines = ['new file mode 100644\n', '--- /dev/null\n', '+++ b/new.h\n',
                 '@@ -0,0 +1 @@\n', '+header\n']
        self.assertEqual(source.apply_hunks(None, lines, 'new.h'), b'header\n')
        lines[0] = 'new file mode 100755\n'
        with self.assertRaises(source.Error):
            source.apply_hunks(None, lines, 'new.h')

    def test_unterminated_upstream_payload_is_preserved_exactly(self):
        raw = (b'diff --git a/header.h b/header.h\n--- /dev/null\n+++ b/header.h\n'
               b'@@ -0,0 +1 @@\n+#endif\n\\ No newline at end of file\n')
        after = source.apply_hunks(None, source.patch_sections(raw)['header.h'], 'header.h')
        self.assertEqual(after, b'#endif')

    def test_unterminated_preimage_and_replacement_are_exact(self):
        raw = (b'diff --git a/unit.c b/unit.c\n--- a/unit.c\n+++ b/unit.c\n'
               b'@@ -1 +1 @@\n-old\n\\ No newline at end of file\n'
               b'+new\n\\ No newline at end of file\n')
        after = source.apply_hunks(b'old', source.patch_sections(raw)['unit.c'], 'unit.c')
        self.assertEqual(after, b'new')

    def test_added_file_has_exact_zero_start_hunk(self):
        raw = b'diff --git a/new.c b/new.c\n--- /dev/null\n+++ b/new.c\n@@ -0,0 +1 @@\n+added\n'
        self.declared = [{'path': 'new.c', 'before_sha256': None,
                          'after_sha256': source.digest(b'added\n'), 'mode': '100644',
                          'payload_file': 'unused in projection', 'payload_sha256': source.digest(b'added\n')}]
        self.raw = raw
        _, after = self.project()
        self.assertEqual((self.root / 'output/new.c').read_bytes(), b'added\n')
        self.assertEqual(len(after), 3)


if __name__ == '__main__':
    unittest.main()
