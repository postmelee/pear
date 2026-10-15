#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Sign a copy of the reviewed runtime; never accept private prefix contents."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import runtime_build as rb

HERE = Path(__file__).resolve().parent
MACHO = {b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe', b'\xca\xfe\xba\xbe'}
LOADERS = {'Wine/bin/wine', 'Wine/lib/wine/x86_64-unix/wine'}
LOADER_ENTITLEMENTS = {
    'com.apple.security.cs.allow-unsigned-executable-memory': True,
    'com.apple.security.cs.disable-library-validation': True,
}


def text_hash(path):
    # Exclude the filename line; preserve architecture markers and exact section bytes.
    text = subprocess.check_output(['otool', '-s', '__TEXT', '__text', str(path)], text=True)
    lines = [line for line in text.splitlines() if not line.startswith(str(path))]
    if not any(('(__TEXT,__text)' in line or '(__TEXT, __text)' in line) for line in lines):
        raise ValueError('Missing executable text section: ' + str(path))
    return hashlib.sha256('\n'.join(lines).encode()).hexdigest()


def expected_files(manifest):
    result = []
    for row in manifest['files']:
        name = row['path']
        if not name.startswith('Libraries/') or '..' in Path(name).parts:
            raise ValueError('Non-runtime package member')
        result.append(dict(row, path=name.removeprefix('Libraries/')))
    return result


def sign(source, manifest_path, output, identity):
    if source.is_symlink() or output.resolve().is_relative_to(source.resolve()):
        raise ValueError('Output must be separate from the immutable input')
    expected = expected_files(json.loads(manifest_path.read_text()))
    if rb.inventory(source) != expected:
        raise ValueError('Input runtime differs from the reviewed package')
    if output.exists():
        raise ValueError('Keep existing candidates; output must be absent')
    if shutil.disk_usage(output.parent).free < 7 * rb.GIB:
        raise ValueError('Insufficient planned copy/archive headroom')
    output.mkdir()
    target = output / 'Libraries'
    shutil.copytree(source, target, symlinks=True)
    signed = []
    for row in expected:
        if 'target' in row:
            continue
        path = target / row['path']
        with path.open('rb') as stream:
            magic = stream.read(4)
        if magic not in MACHO:
            continue
        before = text_hash(path)
        command = ['codesign', '--force', '--options', 'runtime', '--timestamp', '--sign', identity]
        if row['path'] in LOADERS:
            command += ['--generate-entitlement-der', '--entitlements', str(HERE / 'wine-entitlements.plist')]
        subprocess.run(command + [str(path)], check=True, capture_output=True)
        subprocess.run(['codesign', '--verify', '--strict', str(path)], check=True, capture_output=True)
        after = text_hash(path)
        if before != after:
            raise ValueError('Executable text changed while signing')
        entitlement = subprocess.run(['codesign', '-d', '--entitlements', '-', '--xml', str(path)], check=True, capture_output=True).stdout
        parsed = plistlib.loads(entitlement) if entitlement.strip() else {}
        wanted = LOADER_ENTITLEMENTS if row['path'] in LOADERS else {}
        if parsed != wanted:
            raise ValueError('Unexpected runtime entitlement')
        signed.append({'path':row['path'], 'before_sha256':row['sha256'], 'sha256':rb.sha256(path), 'text_sha256':after, 'entitlements':parsed})
    if len(signed) != 45 or not LOADERS.issubset({r['path'] for r in signed}):
        raise ValueError('Unexpected Mach-O inventory')
    signed_names = {r['path'] for r in signed}
    observed = rb.inventory(target)
    if [r for r in observed if r['path'] not in signed_names] != [r for r in expected if r['path'] not in signed_names]:
        raise ValueError('Non-Mach-O runtime content changed')
    if rb.inventory(source) != expected:
        raise ValueError('Original runtime changed')
    record = {'scope':'Developer ID runtime candidate; execution and notarization separate', 'identity':identity, 'signed':signed, 'original_unchanged':True, 'non_macho_unchanged':True, 'executable_text_unchanged':True, 'files':observed}
    rb.write_json(output/'signing.json',record)
    rb.write_json(output/'runtime-manifest.json',[dict(r,path=r['path'].removeprefix('Wine/')) for r in observed if r['path'].startswith('Wine/')])
    return record


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--libraries',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--identity',required=True)
    a=p.parse_args()
    result=sign(a.libraries,a.manifest,a.output,a.identity)
    print(json.dumps({'signed_macho':len(result['signed']),'text_unchanged':result['executable_text_unchanged'],'original_unchanged':result['original_unchanged']}))
