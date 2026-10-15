# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the notice gate against disposable Git repositories, not host state."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[2] / 'tools/check_source_notices.py'
spec = importlib.util.spec_from_file_location('source_notices', TOOL)
n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(n)
HEADER = '# SPDX-FileCopyrightText: 2026 Pear contributors\n# SPDX-License-Identifier: GPL-3.0-or-later\n'


class NoticeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Notice fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'commit.gpgsign', 'false')
        self.write('README.md', 'Disposable fixture\n')
        self.base = self.commit()

    def git(self, *args):
        return n.git(self.root, *args)

    def write(self, name, content):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD').decode().strip()

    def check(self, head=None):
        return n.check(self.root, self.base, head)

    def test_untracked_missing_header_fails(self):
        self.write('new file.py', 'print(1)\n')
        result = self.check()
        self.assertEqual(result['checked'], ['new file.py'])
        self.assertEqual(len(result['errors']), 2)

    def test_valid_added_committed_source(self):
        self.write('new.py', HEADER + 'print(1)\n')
        self.assertEqual(self.check(self.commit())['errors'], [])

    def test_changed_legacy_source_needs_notice_but_unchanged_does_not(self):
        self.write('old.py', 'print(1)\n')
        self.base = self.commit()
        self.assertEqual(self.check()['checked'], [])
        self.write('old.py', 'print(2)\n')
        self.assertTrue(self.check()['errors'])
        self.write('old.py', HEADER + 'print(2)\n')
        self.assertEqual(self.check()['errors'], [])

    def test_staged_addition_and_unstaged_edits_are_both_seen(self):
        self.write('new.py', HEADER)
        self.git('add', '.')
        self.write('new.py', 'print(1)\n')
        self.assertTrue(self.check()['errors'])

    def test_committed_mode_ignores_untracked_private_scratch(self):
        head = self.base
        self.write('scratch.py', 'no header\n')
        self.assertEqual(self.check(head)['checked'], [])

    def test_existing_mit_preserved_without_relicensing(self):
        original = HEADER.replace('GPL-3.0-or-later', 'MIT').replace('Pear contributors', 'Fixture author')
        self.write('fixture.c', original.replace('# ', '// ') + 'int value = 1;\n')
        self.base = self.commit()
        self.write('fixture.c', original.replace('# ', '// ') + 'int value = 2;\n')
        self.assertEqual(self.check()['errors'], [])
        self.write('fixture.c', HEADER.replace('# ', '// ') + 'int value = 2;\n')
        self.assertEqual(len(self.check()['errors']), 2)

    def test_rename_retains_baseline_attribution(self):
        self.write('old.py', HEADER + 'print(1)\n')
        self.base = self.commit()
        self.git('mv', 'old.py', 'renamed file.py')
        result = self.check(self.commit())
        self.assertEqual(result['checked'], ['renamed file.py'])
        self.assertEqual(result['errors'], [])

    def test_renamed_legacy_source_is_not_grandfathered(self):
        self.write('old.py', 'print(1)\n')
        self.base = self.commit()
        self.git('mv', 'old.py', 'renamed.py')
        self.assertTrue(self.check()['errors'])

    def test_deleted_source_needs_no_header(self):
        self.write('gone.py', 'print(1)\n')
        self.base = self.commit()
        self.git('rm', 'gone.py')
        self.assertEqual(self.check()['checked'], [])

    def test_body_string_is_not_a_header(self):
        self.write('new.py', 'text = """\n' + HEADER + '"""\n')
        self.assertEqual(len(self.check()['errors']), 2)

    def test_shebang_and_encoding_are_preserved(self):
        self.write('run', '#!/usr/bin/env python3\n# coding: utf-8\n' + HEADER + 'print(1)\n')
        self.base = self.commit()
        self.write('run', '#!/usr/bin/env python3\n# coding: utf-8\n' + HEADER + 'print(2)\n')
        self.assertEqual(self.check()['errors'], [])

    def test_misplaced_python_encoding_cookie_fails(self):
        self.write('script.py', HEADER + '# coding: utf-8\nprint(1)\n')
        self.assertTrue(any('encoding' in e for e in self.check()['errors']))

    def test_shebang_not_moved_below_notice(self):
        self.write('run.sh', '#!/bin/sh\n' + HEADER + 'exit 0\n')
        self.base = self.commit()
        self.write('run.sh', HEADER + '#!/bin/sh\nexit 0\n')
        self.assertTrue(any('shebang' in e for e in self.check()['errors']))

    def test_deleted_extensionless_shebang_is_still_checked(self):
        self.write('run', '#!/bin/sh\n' + HEADER + 'exit 0\n')
        self.base = self.commit()
        self.write('run', HEADER + 'exit 0\n')
        self.assertTrue(any('shebang' in e for e in self.check()['errors']))

    def test_removed_copyright_with_license_retained_fails(self):
        self.write('one.py', HEADER + 'print(1)\n')
        self.base = self.commit()
        self.write('one.py', '# SPDX-License-Identifier: GPL-3.0-or-later\nprint(1)\n')
        self.assertTrue(any('existing copyright' in e for e in self.check()['errors']))

    def test_supported_comment_styles(self):
        for path, opening, closing in [('one.c', '/*\n', '*/\n'), ('two.html', '<!--\n', '-->\n')]:
            self.write(path, opening + HEADER.replace('# ', '') + closing + 'content\n')
        self.assertEqual(self.check()['errors'], [])

    def test_upstream_copies_reported_without_relabeling(self):
        self.write('preview/runtime-notices/vendor.c', 'original upstream bytes\n')
        result = self.check()
        self.assertEqual(result['checked'], [])
        self.assertEqual(result['upstream_copies_for_manual_review'], ['preview/runtime-notices/vendor.c'])

    def test_exception_requires_actual_notice_and_copyright(self):
        self.write(n.POLICY, json.dumps({'fixture.c': {'license': 'MIT', 'reason': 'Test import', 'notice': 'LICENSE-MIT'}}))
        self.write('fixture.c', HEADER.replace('# ', '// ').replace('GPL-3.0-or-later', 'MIT'))
        self.assertTrue(any('notice is missing' in e for e in self.check()['errors']))
        self.write('LICENSE-MIT', 'Synthetic fixture notice, not a real license\n')
        self.assertEqual(self.check()['errors'], [])
        self.write('fixture.c', '// SPDX-License-Identifier: MIT\n')
        self.assertTrue(any('copyright' in e for e in self.check()['errors']))

    def test_policy_removal_rechecks_unchanged_source(self):
        self.write(n.POLICY, json.dumps({'fixture.py': {'license': 'MIT', 'reason': 'Test import', 'notice': 'NOTICE'}}))
        self.write('NOTICE', 'fixture\n')
        self.write('fixture.py', HEADER.replace('GPL-3.0-or-later', 'MIT'))
        self.base = self.commit()
        self.write(n.POLICY, '{}\n')
        result = self.check()
        self.assertIn('fixture.py', result['checked'])
        # Existing file-level MIT still takes precedence over the root GPL.
        self.assertEqual(result['errors'], [])

    def test_invalid_exception_paths_and_duplicates_fail(self):
        for content in ['{"../outside.py": {}}', '{"a": {}, "a": {}}', '[]']:
            with self.subTest(content=content), self.assertRaises(ValueError):
                n.load_policy(content)

    def test_source_symlink_refuses_external_read(self):
        (self.root / 'bad.py').symlink_to('/unavailable/private.py')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.check()

    def test_missing_revision_cli_fails_closed(self):
        run = subprocess.run([sys.executable, str(TOOL), '--base', 'does-not-exist'], cwd=self.root, capture_output=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn(b'Source notice check failed', run.stderr)


if __name__ == '__main__':
    unittest.main()
