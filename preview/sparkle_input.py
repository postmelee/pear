#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Admit the pinned upstream Sparkle input separately from app compilation."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

VERSION = '2.10.0'
DIGEST = 'c2bf58aa8387266ac179357b1415d6f2635f044da8be41042af32425dae6da0c'
URL = f'https://github.com/sparkle-project/Sparkle/releases/download/{VERSION}/Sparkle-{VERSION}.tar.xz'
INVENTORY = Path(__file__).with_name('sparkle-files.json')
SIGN_TARGETS = [
    'Versions/B/XPCServices/Downloader.xpc',
    'Versions/B/XPCServices/Installer.xpc',
    'Versions/B/Autoupdate',
    'Versions/B/Updater.app',
    '.',
]


def verify_framework(framework, hashes=False):
    if framework.is_symlink() or not framework.is_dir():
        raise ValueError('Expected a framework directory, not a link')
    expected = json.loads(INVENTORY.read_text())
    found = set()
    for path in framework.rglob('*'):
        name = path.relative_to(framework).as_posix()
        if path.is_symlink():
            if expected.get(name, {}).get('link') != str(path.readlink()):
                raise ValueError(f'Unexpected Sparkle link: {name}')
            if not path.resolve().is_relative_to(framework.resolve()):
                raise ValueError('Sparkle link escapes framework')
        elif path.is_file():
            if name not in expected or 'sha256' not in expected[name]:
                raise ValueError(f'Unexpected Sparkle file: {name}')
            if hashes and hashlib.sha256(path.read_bytes()).hexdigest() != expected[name]['sha256']:
                raise ValueError(f'Changed admitted Sparkle input: {name}')
        elif path.is_dir():
            continue
        else:
            raise ValueError('Unsupported Sparkle entry')
        found.add(name)
    if found != set(expected):
        raise ValueError('Incomplete Sparkle framework')
    return found


def prepare(archive, output):
    if hashlib.sha256(archive.read_bytes()).hexdigest() != DIGEST:
        raise ValueError('Sparkle archive hash mismatch')
    if output.exists():
        verify_framework(output / 'Sparkle.framework', hashes=True)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='sparkle-admit-', dir=output.parent) as scratch:
        root = Path(scratch)
        # The exact archive digest was admitted above, including its upstream links.
        subprocess.run(['tar', '-xf', str(archive.resolve()), '-C', str(root),
                        './Sparkle.framework', './LICENSE'], check=True)
        verify_framework(root / 'Sparkle.framework', hashes=True)
        subprocess.run(['codesign', '--verify', '--deep', '--strict', str(root / 'Sparkle.framework')], check=True)
        (root / 'admission.json').write_text(json.dumps(dict(version=VERSION, archive_sha256=DIGEST, source=URL), indent=2)+'\n')
        shutil.move(str(root), str(output))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    archive = args.archive or args.output.parent / f'Sparkle-{VERSION}.tar.xz'
    if not archive.exists() and args.download:
        archive.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=archive.parent, delete=False) as temp:
            temporary = Path(temp.name)
        try:
            with urllib.request.urlopen(URL, timeout=60) as response, temporary.open('wb') as out:
                shutil.copyfileobj(response, out)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != DIGEST:
                raise ValueError('Downloaded Sparkle hash mismatch')
            temporary.replace(archive)
        finally:
            temporary.unlink(missing_ok=True)
    prepare(archive, args.output)
    print('Sparkle 2.10.0 admitted; upstream MIT/BSD/Ed25519 notices retained.')


if __name__ == '__main__':
    main()
