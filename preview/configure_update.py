#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bind public update settings to the app before signing; never load private keys."""
import base64
import os
from pathlib import Path
import plistlib
import re
import sys
from urllib.parse import urlparse


def configure(path, env):
    data = plistlib.loads(path.read_bytes())
    build = env.get('PEAR_APP_BUILD', '6')
    if not re.fullmatch(r'[1-9][0-9]{0,8}', build):
        raise ValueError('PEAR_APP_BUILD must be a monotonic positive integer')
    feed, key = env.get('PEAR_UPDATE_FEED', ''), env.get('PEAR_UPDATE_PUBLIC_KEY', '')
    if bool(feed) != bool(key):
        raise ValueError('Feed and public Ed25519 key must be provided together')
    if feed:
        parsed = urlparse(feed)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment or parsed.query:
            raise ValueError('Update feed must be an HTTPS URL without credentials, fragment or query')
        if len(base64.b64decode(key, validate=True)) != 32:
            raise ValueError('Invalid public Ed25519 key')
        data.update(SUFeedURL=feed, SUPublicEDKey=key)
    else:
        data.pop('SUFeedURL', None); data.pop('SUPublicEDKey', None)
    data.update(CFBundleVersion=build, SUEnableAutomaticChecks=False,
                SUAllowsAutomaticUpdates=False, SUAutomaticallyUpdate=False,
                SUEnableSystemProfiling=False, SUSendProfileInfo=False,
                SUVerifyUpdateBeforeExtraction=True, SURequireSignedFeed=bool(feed))
    path.write_bytes(plistlib.dumps(data, sort_keys=False))


if __name__ == '__main__':
    configure(Path(sys.argv[1]), os.environ)
