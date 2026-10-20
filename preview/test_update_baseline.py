# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import unittest
from update_baseline import validate_configuration


class BaselineAdmissionTests(unittest.TestCase):
    def test_rejects_wrong_identity_feed_key_and_non_increasing_versions(self):
        config = dict(target_build='7', baseline_build='6', qualification_feed='https://example.invalid/appcast.xml', public_key='fixture')
        info = dict(CFBundleIdentifier='org.pear.rosetta-preview', CFBundleVersion='7',
                    SUFeedURL=config['qualification_feed'], SUPublicEDKey='fixture',
                    SURequireSignedFeed=True, SUVerifyUpdateBeforeExtraction=True)
        validate_configuration(info, config)
        for mutation in [dict(CFBundleIdentifier='other.app'), dict(CFBundleVersion='8'),
                         dict(SUFeedURL='https://example.invalid/stable.xml'),dict(SUPublicEDKey='wrong'),
                         dict(SURequireSignedFeed=False),dict(SUVerifyUpdateBeforeExtraction=False)]:
            with self.assertRaises(ValueError): validate_configuration(info | mutation, config)
        for baseline in ('0', '7', '8'):
            with self.assertRaises(ValueError): validate_configuration(info, config | dict(baseline_build=baseline))


if __name__ == '__main__': unittest.main()
