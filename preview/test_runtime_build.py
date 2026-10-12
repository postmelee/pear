# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import runtime_build as rb
import runtime_validate as rv


class RebuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / 'kit'
        (self.base / 'runtime-notices').mkdir(parents=True)
        (self.base / 'runtime-notices/NOTICE').write_text('upstream notice')
        (self.base / 'change.patch').write_text('patch')
        self.archive = self.root / 'source.tar'
        self.archive.write_bytes(b'original archive')
        self.mapping = {'component': str(self.archive)}
        self.lock = {'inputs': {'component': {'sha256': rb.sha256(self.archive), 'filename': 'source.tar'}},
                     'patch': {'file': 'change.patch', 'sha256': rb.sha256(self.base / 'change.patch')},
                     'notice_files': {'NOTICE': rb.sha256(self.base / 'runtime-notices/NOTICE')}}

    def test_input_and_notice_integrity(self):
        self.assertEqual(rb.verify_inputs(self.mapping, self.lock, self.base)['component'], self.archive.resolve())
        self.archive.write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            rb.verify_inputs(self.mapping, self.lock, self.base)

    def test_missing_output_receipt_cannot_skip_input_check(self):
        (self.root / 'old-result.json').write_text('{"passed":true}')
        self.archive.unlink()
        with self.assertRaises(FileNotFoundError):
            rb.verify_inputs(self.mapping, self.lock, self.base)

    def test_missing_and_extra_inputs_refused(self):
        for mapping in ({}, self.mapping | {'unreviewed': str(self.archive)}):
            with self.assertRaisesRegex(ValueError, 'exactly'):
                rb.verify_inputs(mapping, self.lock, self.base)

    def test_missing_or_modified_notice_refused(self):
        notice = self.base / 'runtime-notices/NOTICE'
        notice.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            rb.verify_inputs(self.mapping, self.lock, self.base)
        notice.unlink()
        with self.assertRaisesRegex(ValueError, 'inventory'):
            rb.verify_inputs(self.mapping, self.lock, self.base)

    def test_old_success_output_is_not_reused(self):
        output = self.root / 'old-build'; output.mkdir()
        (output / 'result.json').write_text('{"build":"passed"}')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            rb.fresh_output(output)
        self.assertFalse((output / 'Runtime').exists())

    def test_bison_uses_space_free_tool_path(self):
        original = self.root / 'tools with spaces/bison/bin/bison'
        original.parent.mkdir(parents=True); original.write_text('tool')
        build = self.root / 'build'; build.mkdir()
        selected = rb.local_bison(build, original)
        self.assertNotIn(' ', str(selected))
        self.assertEqual(selected.read_text(), 'tool')
        self.assertEqual(selected.resolve(), original.resolve())

    def test_physical_path_with_spaces_refused(self):
        real = self.root / 'has spaces'; real.mkdir()
        alias = self.root / 'alias'; alias.symlink_to(real, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'whitespace'):
            rb.fresh_output(alias / 'new')

    def test_missing_or_false_release_refused(self):
        receipt = self.root / 'release.json'
        with self.assertRaises(FileNotFoundError):
            rb.require_release(receipt)
        for val in (False, 'true', 1, None):
            receipt.write_text(json.dumps({'released': val}))
            with self.assertRaises(ValueError):
                rb.require_release(receipt)
        receipt.write_text('{"released":true}')
        rb.require_release(receipt)

    def test_lock_contention_and_release(self):
        lock = self.root / 'lock'
        with rb.heavy_slot(lock, None, 0, self.root):
            with self.assertRaises(BlockingIOError):
                with rb.heavy_slot(lock, None, 0, self.root):
                    self.fail('second owner admitted')
        with rb.heavy_slot(lock, None, 0, self.root):
            pass

    def test_insufficient_storage_refused(self):
        with self.assertRaisesRegex(ValueError, 'Insufficient'):
            with rb.heavy_slot(self.root / 'lock', None, 10 ** 30, self.root):
                self.fail('storage preflight bypassed')

    def test_archive_traversal_refused(self):
        archive = self.root / 'bad.tar'
        with tarfile.open(archive, 'w') as tar:
            info = tarfile.TarInfo('../escape'); info.size = 1
            tar.addfile(info, io.BytesIO(b'x'))
        with self.assertRaises(tarfile.FilterError):
            rb.extract(archive, self.root / 'extracted')
        self.assertFalse((self.root / 'escape').exists())

    def test_external_runtime_symlink_refused(self):
        runtime = self.root / 'Runtime'; runtime.mkdir()
        (runtime / 'helper').symlink_to(self.archive)
        with self.assertRaisesRegex(ValueError, 'External'):
            rb.inventory(runtime)

    def test_validation_refuses_existing_private_state(self):
        private = self.root / 'existing'; private.mkdir()
        (private / 'saved-state').write_text('keep')
        with self.assertRaisesRegex(ValueError, 'absent'):
            rv.validate(self.root / 'Runtime', private)
        self.assertEqual((private / 'saved-state').read_text(), 'keep')

    def test_validation_refuses_changed_runtime_before_execution(self):
        runtime = self.root / 'relocated/Runtime'; runtime.mkdir(parents=True)
        (self.root / 'runtime-manifest.json').write_text('[]')
        (runtime / 'unexpected').write_text('changed')
        with patch.object(rv.subprocess, 'run') as execute:
            with self.assertRaisesRegex(ValueError, 'manifest'):
                rv.validate(runtime, self.root / 'validation')
            execute.assert_not_called()

    def test_notice_install_preserves_nested_files_and_matches_wine_source(self):
        wine = self.root / 'wine-source'; wine.mkdir()
        nested = self.base / 'runtime-notices/wine/libs/example/COPYING'
        nested.parent.mkdir(parents=True); nested.write_text('separate component terms')
        for name in ('LICENSE', 'COPYING.LIB', 'AUTHORS', 'README.md'):
            (wine / name).write_text(name + ' source text')
        (self.base / 'runtime-notices/wine/LICENSE').write_text('LICENSE source text')
        with patch.object(rb, 'HERE', self.base):
            rb.install_notices(self.root / 'licenses', wine)
        self.assertEqual((self.root / 'licenses/wine/libs/example/COPYING').read_text(),
                         'separate component terms')
        self.assertEqual((self.root / 'licenses/wine/AUTHORS').read_text(), 'AUTHORS source text')
        (wine / 'LICENSE').write_text('different source')
        with patch.object(rb, 'HERE', self.base):
            with self.assertRaisesRegex(ValueError, 'source/notice mismatch'):
                rb.install_notices(self.root / 'mismatched-licenses', wine)

    def test_source_kit_allowlist_excludes_private_state(self):
        (self.base / 'runtime-notices/LICENSE').write_text('separate upstream license')
        self.lock['notice_files']['LICENSE'] = rb.sha256(self.base / 'runtime-notices/LICENSE')
        (self.base / 'runtime_build.py').write_text('builder')
        (self.base / 'runtime-inputs.json').write_text(json.dumps(self.lock))
        (self.root / 'LICENSE').write_text('GPL license fixture')
        (self.base / 'private-token').write_text('must not export')
        (self.base / 'THIRD_PARTY_NOTICES.md').write_text('component delivery boundaries')
        output = self.root / 'kit.tar.gz'
        with patch.object(rb, 'HERE', self.base):
            rb.source_kit(output, {'component': self.archive}, self.lock)
        with tarfile.open(output) as kit:
            self.assertNotIn('private-token', kit.getnames())
            self.assertIn('input-map.json', kit.getnames())
            self.assertEqual(kit.extractfile('THIRD_PARTY_NOTICES.md').read(), b'component delivery boundaries')
            self.assertIn('runtime-notices/NOTICE', kit.getnames())
            self.assertEqual(len(kit.getnames()), len(set(kit.getnames())))
            self.assertEqual(kit.extractfile('LICENSE').read(), b'GPL license fixture')
            self.assertEqual(kit.extractfile('runtime-notices/LICENSE').read(), b'separate upstream license')
            self.assertEqual(kit.extractfile('inputs/source.tar').read(), b'original archive')
            self.assertTrue(all(not m.uname and not m.gname for m in kit.getmembers()))


if __name__ == '__main__':
    unittest.main()
