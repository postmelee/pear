#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Package a verified rebuilt runtime, never an authenticated Windows prefix."""
import argparse
import gzip
import hashlib
import io
import json
import re
from pathlib import Path
import tarfile
from runtime_build import inventory, sha256

HERE = Path(__file__).resolve().parent
BASELINE = 'df62f412dfdce96b37ee8358af1ff232a033ee762aa6a3e1b6a1fb1dd722ce36'
RUNTIME_ID = 'pear-wine11-cw26.3-dxmt0.80-v2'
NATIVE_MARKER = bytes.fromhex('0e1fba0e00b409cd21b8014ccd219090')


def native_dxmt(data):
    if data[0x40:0x50] != b'Wine builtin DLL':
        raise ValueError('Unexpected DXMT builtin marker')
    return data[:0x40] + NATIVE_MARKER + data[0x50:]


def notice_files():
    root = HERE / 'runtime-notices'
    lock = json.loads((HERE / 'runtime-inputs.json').read_text())
    actual = {str(p.relative_to(root)): sha256(p) for p in root.rglob('*') if p.is_file()}
    if actual != lock['notice_files']:
        raise ValueError('Notice inventory differs from pinned inputs')
    return root, actual



def admit_notice_refresh(rebuilt_lock, reviewed_sha256):
    """Admit only a notice refresh of an exact reviewed reconstruction lock."""
    if not re.fullmatch(r'[0-9a-f]{64}', reviewed_sha256) or sha256(rebuilt_lock) != reviewed_sha256:
        raise ValueError('Reconstruction input lock changed')
    original = json.loads(rebuilt_lock.read_text())
    current = json.loads((HERE / 'runtime-inputs.json').read_text())
    # Executable sources, patches, options and every unknown field must match.
    original.pop('notice_files')
    current.pop('notice_files')
    if original != current:
        raise ValueError('Only reviewed notice changes may be repackaged')
    notice_files()


def reviewed_identity(digest, runtime_id):
    if not re.fullmatch(r'[0-9a-f]{64}', digest):
        raise ValueError('Expected an explicitly reviewed SHA-256')
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,79}', runtime_id):
        raise ValueError('Invalid runtime identity')


def package(runtime, manifest, output, *, baseline_sha256=None, runtime_id=RUNTIME_ID):
    baseline_sha256 = BASELINE if baseline_sha256 is None else baseline_sha256
    reviewed_identity(baseline_sha256, runtime_id)
    if sha256(manifest) != baseline_sha256:
        raise ValueError('Unreviewed baseline manifest')
    expected = json.loads(manifest.read_text())
    if inventory(runtime) != expected:
        raise ValueError('Baseline runtime changed or contains extra files')
    notices, notice_hashes = notice_files()
    if output.exists():
        raise ValueError('Preserve existing package; select a fresh output')
    files = {}
    for row in expected:
        rel = row['path']
        if rel.startswith('share/pear/licenses/') or rel == 'share/pear/runtime-inputs.json':
            continue
        files['Libraries/Wine/' + rel] = runtime / rel
    for rel in notice_hashes:
        files['Libraries/Wine/share/pear/licenses/' + rel] = notices / rel
    files['Libraries/Wine/share/pear/runtime-inputs.json'] = HERE / 'runtime-inputs.json'
    files['Libraries/THIRD_PARTY_NOTICES.md'] = HERE / 'THIRD_PARTY_NOTICES.md'
    transformed = []
    for short, arch in [('x64', 'x86_64-windows'), ('x32', 'i386-windows')]:
        for name in ['d3d11.dll', 'dxgi.dll', 'd3d10core.dll', 'winemetal.dll']:
            original = runtime / 'share/pear/dxmt' / arch / name
            data = original.read_bytes()
            if name != 'winemetal.dll':
                data = native_dxmt(data)
            dest = f'Libraries/DXMT/{short}/{name}'
            files[dest] = data
            transformed.append({'path': dest, 'source_sha256': sha256(original),
                                'sha256': hashlib.sha256(data).hexdigest()})
    rows = []
    with output.open('xb') as raw, gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0, compresslevel=1) as gz, tarfile.open(fileobj=gz, mode='w|') as archive:
        for name, source in sorted(files.items()):
            info = tarfile.TarInfo(name)
            info.mode = 0o644
            if isinstance(source, Path) and source.is_symlink():
                info.type = tarfile.SYMTYPE
                info.linkname = str(source.readlink())
                archive.addfile(info)
                rows.append({'path': name, 'target': info.linkname})
                continue
            data = source.read_bytes() if isinstance(source, Path) else source
            if isinstance(source, Path):
                info.mode = source.stat().st_mode & 0o777
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
            rows.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    # Re-read the compressed payload; verify all entries and no hidden extra members.
    with tarfile.open(output) as archive:
        observed = []
        for member in archive:
            if member.issym():
                observed.append({'path': member.name, 'target': member.linkname})
            elif member.isfile():
                data = archive.extractfile(member).read()
                observed.append({'path': member.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
            else:
                raise ValueError('Unexpected archive member')
    if observed != rows or inventory(runtime) != expected:
        raise ValueError('Archive verification or unchanged-baseline check failed')
    result = {'runtime_id': runtime_id, 'name': output.name, 'sha256': sha256(output),
              'size': output.stat().st_size, 'url': '', 'baseline_manifest_sha256': baseline_sha256,
              'baseline_unchanged': True, 'notice_files': len(notice_hashes),
              'overrides': transformed, 'files': rows,
              'scope': 'Local integration candidate; public distribution not admitted'}
    output.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def package_signed(libraries, manifest, manifest_sha256, output, *,
                   runtime_id="pear-wine11-cw26.3-dxmt0.80-signed-v2"):
    """Archive exact, separately reviewed signed bytes without transforming PE data."""
    if sha256(manifest) != manifest_sha256:
        raise ValueError('Signed manifest changed')
    reviewed_identity(manifest_sha256, runtime_id)
    expected = json.loads(manifest.read_text())['files']
    if libraries.is_symlink() or inventory(libraries) != expected:
        raise ValueError('Signed runtime inventory changed')
    if output.exists() or output.resolve().is_relative_to(libraries.resolve()):
        raise ValueError('Select a fresh output outside the runtime')
    rows = []
    with output.open('xb') as raw, gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0, compresslevel=1) as gz, tarfile.open(fileobj=gz, mode='w|') as archive:
        for row in expected:
            source = libraries / row['path']
            info = tarfile.TarInfo('Libraries/' + row['path'])
            info.mode = source.lstat().st_mode & 0o777
            if 'target' in row:
                info.type = tarfile.SYMTYPE
                info.linkname = row['target']
                archive.addfile(info)
            else:
                info.size = row['bytes']
                with source.open('rb') as stream:
                    archive.addfile(info, stream)
            rows.append(dict(row, path=info.name, mode=info.mode))
    observed = []
    with tarfile.open(output) as archive:
        for member in archive:
            if member.issym():
                row = {'path': member.name, 'target': member.linkname}
            elif member.isfile():
                data = archive.extractfile(member).read()
                row = {'path': member.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
            else:
                raise ValueError('Unexpected signed archive member')
            observed.append(dict(row, mode=member.mode))
    if observed != rows or inventory(libraries) != expected:
        raise ValueError('Signed archive verification failed')
    result = {'runtime_id': runtime_id,
              'name': output.name, 'sha256': sha256(output), 'size': output.stat().st_size,
              'url': '', 'signing_manifest_sha256': manifest_sha256, 'files': rows,
              'scope': 'Signed candidate; notarization, execution and release qualification are separate'}
    output.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def render_pin(result):
    """Retain source notices whenever the verified pin is regenerated."""
    return ('// SPDX-FileCopyrightText: 2026 Pear contributors\n'
            '// SPDX-License-Identifier: GPL-3.0-or-later\n'
            '// Generated by runtime_package.py from a verified local candidate.\n'
            + f'pub const RUNTIME_ID: &str = "{result["runtime_id"]}";\n'
            + 'pub const RUNTIME: super::Artifact = super::Artifact {\n'
            + f'    name: "{result["name"]}", url: "", sha: "{result["sha256"]}", size: {result["size"]},\n}};\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--write-pin', action='store_true')
    a = p.parse_args()
    r = package(a.runtime, a.manifest, a.output)
    if a.write_pin:
        (HERE / 'src/runtime_pin.rs').write_text(render_pin(r))
    print(json.dumps({k: v for k, v in r.items() if k not in ('files', 'overrides')}))
