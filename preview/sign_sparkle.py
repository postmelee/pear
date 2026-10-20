#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Sign the pinned Sparkle nested code inside-out, without --deep signing."""
from pathlib import Path
import subprocess
import sys
from sparkle_input import SIGN_TARGETS, verify_framework


def sign_framework(framework, identity, keychain=None):
    verify_framework(framework)
    for relative in SIGN_TARGETS:
        target = framework / relative
        args = ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp']
        if keychain: args += ['--keychain', str(keychain)]
        # Preserve the upstream helper entitlements, not the upstream identity.
        args += ['--preserve-metadata=entitlements', '--sign', identity, str(target)]
        subprocess.run(args, check=True)
    subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(framework)], check=True)


if __name__ == '__main__':
    sign_framework(Path(sys.argv[1]), sys.argv[2])
