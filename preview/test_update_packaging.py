# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic update configuration and strict framework packaging boundaries."""
import base64
import json
from pathlib import Path
import plistlib
import tempfile
import unittest
from unittest.mock import patch
from configure_update import configure
from sparkle_input import verify_framework
from package import audit_app, REQUIRED


class UpdatePackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pear-update-package-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plist = self.root / 'Info.plist'
        self.plist.write_bytes(plistlib.dumps({'CFBundleIdentifier': 'test.pear'}))
        self.env = {'PEAR_APP_BUILD': '7', 'PEAR_UPDATE_FEED': 'https://example.invalid/appcast.xml',
                    'PEAR_UPDATE_PUBLIC_KEY': base64.b64encode(b'a'*32).decode()}

    def test_public_config_and_privacy_are_separate(self):
        configure(self.plist, self.env)
        p = plistlib.loads(self.plist.read_bytes())
        self.assertEqual(p['CFBundleVersion'], '7')
        self.assertEqual(p['SUFeedURL'], self.env['PEAR_UPDATE_FEED'])
        for key in ('SUEnableAutomaticChecks', 'SUAllowsAutomaticUpdates', 'SUAutomaticallyUpdate', 'SUEnableSystemProfiling', 'SUSendProfileInfo'):
            self.assertIs(p[key], False)
        self.assertIs(p['SUVerifyUpdateBeforeExtraction'], True)
        self.assertIs(p['SURequireSignedFeed'], True)
        self.assertNotIn('sharing', str(p).lower())

    def test_invalid_or_partial_config_rejected(self):
        for changed in ({'PEAR_APP_BUILD':'0'}, {'PEAR_UPDATE_FEED':'http://example.invalid/a'},
                        {'PEAR_UPDATE_FEED':'https://user:secret@example.invalid/a'},
                        {'PEAR_UPDATE_PUBLIC_KEY':''}, {'PEAR_UPDATE_PUBLIC_KEY':'not-a-key'}):
            with self.assertRaises(ValueError): configure(self.plist, self.env | changed)

    def test_local_candidate_does_not_silently_enable_updates(self):
        configure(self.plist, self.env)
        configure(self.plist, {})
        self.assertNotIn('SUFeedURL', plistlib.loads(self.plist.read_bytes()))

    def test_inventory_rejects_unknown_bytes_links_and_missing_files(self):
        import hashlib
        framework = self.root / 'Sparkle.framework'; framework.mkdir()
        binary = framework / 'Sparkle'; binary.write_bytes(b'fixture')
        link = framework / 'Alias'; link.symlink_to('Sparkle')
        inventory = self.root / 'inventory.json'
        inventory.write_text(json.dumps({'Sparkle': {'sha256':hashlib.sha256(b'fixture').hexdigest()}, 'Alias':{'link':'Sparkle'}}))
        with patch('sparkle_input.INVENTORY', inventory):
            self.assertEqual(verify_framework(framework, hashes=True), {'Sparkle','Alias'})
            binary.write_bytes(b'changed')
            with self.assertRaises(ValueError): verify_framework(framework, hashes=True)
            link.unlink();link.symlink_to('/etc/hosts')
            with self.assertRaises(ValueError): verify_framework(framework)
            link.unlink();link.symlink_to('Sparkle');(framework/'private').write_text('sentinel')
            with self.assertRaises(ValueError): verify_framework(framework)
            (framework/'private').unlink();binary.unlink()
            with self.assertRaises(ValueError): verify_framework(framework)

    def test_framework_root_link_is_rejected(self):
        app=self.root/'Pear.app'
        for name in REQUIRED | {'Contents/Resources/licenses/example.txt'}:
            path=app/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture')
        destination=self.root/'outside';destination.mkdir()
        root=app/'Contents/Frameworks';root.mkdir();(root/'Sparkle.framework').symlink_to(destination)
        with self.assertRaises(ValueError): audit_app(app)


if __name__ == '__main__': unittest.main()
