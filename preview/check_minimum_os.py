#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Execute a frozen candidate on macOS 15; never use Steam accounts or games."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import subprocess
import tarfile
import time
import urllib.request


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def command(*args, timeout=60, **kwargs):
    return subprocess.check_output(args, text=True, timeout=timeout, **kwargs).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packages', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-revision')
    parser.add_argument('--signed-app-only', action='store_true')
    args = parser.parse_args()
    revision = args.expected_revision or os.environ.get('GITHUB_SHA')
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = {'scope': 'macOS 15 startup only; no Steam UI, Metal rendering or gameplay qualification',
               'passed': False, 'started': time.time(), 'source': revision}
    try:
        receipt['os'] = command('sw_vers', '-productVersion')
        receipt['arch'] = command('uname', '-m')
        assert receipt['os'].split('.')[0] == '15' and receipt['arch'] == 'arm64'
        manifest = json.loads((args.packages / 'package-manifest.json').read_text())
        assert manifest['source_revision'] == revision and not manifest['source_dirty']
        for name, expected in manifest['artifacts'].items():
            assert Path(name).name == name
            path = args.packages / name
            assert path.stat().st_size == expected['size'] and digest(path) == expected['sha256']
        app_zips = list(args.packages.glob('Pear-*-macos-arm64.zip'))
        assert len(app_zips) == 1
        command('/usr/bin/ditto', '-x', '-k', str(app_zips[0]), str(args.output))
        app = args.output / 'Pear.app'
        with (app / 'Contents/Info.plist').open('rb') as f:
            assert plistlib.load(f)['LSMinimumSystemVersion'] == '15.0'
        cli = app / 'Contents/Resources/pear-preview'
        if args.signed_app_only:
            assert not manifest['candidate']
            command('/usr/bin/codesign', '--verify', '--deep', '--strict', str(app))
            command('/usr/bin/xcrun', 'stapler', 'validate', str(app))
            command('/usr/sbin/spctl', '--assess', '--type', 'execute', str(app))
            command('/usr/bin/codesign', '--verify', '--strict', '-R=notarized', '--check-notarization', str(cli))
            receipt['signed_app_checks'] = True
        for binary in [app / 'Contents/MacOS/PearPreview', cli]:
            build = command('xcrun', 'vtool', '-show-build', str(binary))
            assert re.search(r'minos\s+15\.0\b', build)
        receipt['cli_version'] = command(str(cli), '--version')
        command(str(cli), '--help')
        root = args.output / 'fresh-state'
        info = json.loads(command(str(cli), 'setup-info', '--root', str(root)))
        receipt['setup_info'] = info
        env = dict(os.environ, PEAR_PREVIEW_ROOT=str(root))
        with (args.output / 'app.log').open('w') as log:
            child = subprocess.Popen([str(app / 'Contents/MacOS/PearPreview')], env=env, stdout=log, stderr=log)
            try:
                time.sleep(8)
                assert child.poll() is None, 'App exited during isolated first-run startup'
                receipt['app_process_startup'] = True
            finally:
                if child.poll() is None:
                    child.terminate()
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait(timeout=10)
        if args.signed_app_only:
            receipt['runtime_scope'] = 'Unchanged pin; runtime checks retained from source-matched candidate CI'
            receipt['passed'] = True
            return
        # Immutable, already published runtime: verify before extracting it.
        pin = Path(__file__).with_name('src').joinpath('runtime_pin.rs').read_text()
        url = re.search(r'url: "([^"]+)"', pin)[1]
        sha = re.search(r'sha: "([^"]+)"', pin)[1]
        size = int(re.search(r'size: (\d+)', pin)[1])
        archive = args.output / 'runtime.tar.gz'
        with urllib.request.urlopen(url, timeout=60) as response, archive.open('wb') as out:
            total = 0
            while data := response.read(1024 * 1024):
                total += len(data)
                assert total <= size
                out.write(data)
        assert archive.stat().st_size == size and digest(archive) == sha
        receipt['runtime_sha256'] = sha
        runtime = args.output / 'runtime'
        with tarfile.open(archive) as tar:
            tar.extractall(runtime, filter='data')
        versions = {}
        for path in runtime.rglob('*'):
            if path.is_symlink() or not path.is_file():
                continue
            with path.open('rb') as f:
                magic = f.read(4)
            if magic not in [bytes.fromhex(v) for v in ['cffaedfe', 'cefaedfe', 'cafebabe', 'bebafeca']]:
                continue
            build = command('xcrun', 'vtool', '-show-build', str(path))
            minima = re.findall(r'minos\s+([\d.]+)', build)
            if not minima:
                build = command('otool', '-l', str(path))
                minima = re.findall(r'cmd LC_VERSION_MIN_MACOSX\s+cmdsize \d+\s+version ([\d.]+)', build)
            assert minima and all(tuple(map(int, v.split('.'))) <= (15, 0, 0) for v in minima), path.name
            versions[str(path.relative_to(runtime))] = minima
        assert len(versions) >= 40
        receipt['runtime_minimum_versions'] = versions
        command('/usr/sbin/softwareupdate', '--install-rosetta', '--agree-to-license', timeout=180)
        receipt['wine_version'] = command(str(runtime / 'Libraries/Wine/bin/wine'), '--version')
        assert '11.0' in receipt['wine_version']
        receipt['passed'] = True
    finally:
        receipt['finished'] = time.time()
        (args.output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
