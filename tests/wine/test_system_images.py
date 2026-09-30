"""Pure native-image origin tests; these do not attest an installed macOS image."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
import run_fixtures as runner


class SystemImageOriginTests(unittest.TestCase):
    def test_direct_system_images(self):
        for name in ('/usr/lib/libSystem.B.dylib', '/System/Library/Frameworks/AppKit.framework/AppKit'):
            with self.subTest(name=name):
                self.assertTrue(runner.system_image_origin(name, name))

    def test_same_path_cryptex_aliases(self):
        for name in ('/usr/lib/libExample.dylib',
                     '/System/Library/Frameworks/SafariServices.framework/Versions/A/SafariServices',
                     '/System/Library/PrivateFrameworks/WebGPU.framework/Versions/A/WebGPU'):
            with self.subTest(name=name):
                self.assertTrue(runner.system_image_origin(name, '/System/Volumes/Preboot/Cryptexes/OS' + name))

    def test_arbitrary_preboot_location_does_not_become_system(self):
        observed = '/System/Library/Frameworks/Example.framework/Example'
        for root in ('/System/Volumes/Preboot/other', '/System/Volumes/Preboot/Cryptexes/App',
                     '/System/Volumes/Preboot/Cryptexes/OS.extra', '/private/tmp'):
            with self.subTest(root=root):
                self.assertFalse(runner.system_image_origin(observed, root + observed))

    def test_alias_cannot_change_relative_image_identity(self):
        self.assertFalse(runner.system_image_origin('/System/Library/Frameworks/A.framework/A',
            '/System/Volumes/Preboot/Cryptexes/OS/System/Library/Frameworks/B.framework/B'))

    def test_user_path_cannot_masquerade_as_system_alias(self):
        for observed in ('/Users/example/lib.dylib', '/Library/Frameworks/Example.framework/Example',
                         '/System/Library.extra/lib.dylib', 'System/Library/lib.dylib',
                         '/System/Library/../Library/lib.dylib'):
            with self.subTest(observed=observed):
                self.assertFalse(runner.system_image_origin(observed, '/System/Library/lib.dylib'))

    def test_direct_cryptex_path_requires_a_separately_reviewed_policy(self):
        path = '/System/Volumes/Preboot/Cryptexes/OS/System/Library/lib.dylib'
        self.assertFalse(runner.system_image_origin(path, path))

    def test_system_symlink_cannot_escape_to_user_or_writable_storage(self):
        for resolved in ('/Users/example/lib.dylib', '/private/tmp/lib.dylib',
                         '/System/Volumes/Preboot/Cryptexes/OS/System/Library/../../../../tmp/lib.dylib'):
            with self.subTest(resolved=resolved):
                self.assertFalse(runner.system_image_origin('/usr/lib/lib.dylib', resolved))

    def test_root_directories_are_not_images(self):
        for path in ('/usr/lib', '/System/Library', '/', '/System/Volumes/Preboot/Cryptexes/OS'):
            with self.subTest(path=path):
                self.assertFalse(runner.system_image_origin(path, path))


if __name__ == '__main__':
    unittest.main()
