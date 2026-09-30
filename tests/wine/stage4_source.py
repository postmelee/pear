"""Materialize selected Wine files from immutable inputs and the tracked series.

Every base, patch, preimage and postimage hash is checked. Applying only the
selected file's exact diff avoids copying the full Wine tree for source tests.
No private edit or historical build source is used as implementation truth.
"""
from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import subprocess
import tempfile
import unittest

REPO = next(parent for parent in Path(__file__).resolve().parents
            if (parent / 'runtime/wine/patches/series.json').is_file())
INPUTS = REPO / '.build/task4/inputs'
HEADERS = REPO / '.build/task4/build-stage3-attempt12'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def ordinary_file(root, relative):
    name = PurePosixPath(relative)
    if not isinstance(relative, str) or str(name) != relative or name.is_absolute() or any(
            value in ('', '.', '..') for value in name.parts) or '\\' in relative:
        raise ValueError('invalid relative source path')
    path = root
    for part in name.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('source or patch path is a symlink')
    if not path.is_file():
        raise ValueError('required ordinary source or patch file is missing')
    return path


def file_diff(patch, relative):
    """Select a unified file diff with exact paired old/new path headers."""
    lines = patch.decode('utf-8').splitlines(keepends=True)
    pairs = [i for i in range(len(lines) - 1)
             if lines[i].startswith(('--- a/', '--- /dev/null')) and lines[i + 1].startswith('+++ b/')]
    selected = [i for i in pairs if lines[i + 1].rstrip('\n') == '+++ b/' + relative]
    if len(selected) != 1:
        raise ValueError('selected file must have one exact patch header')
    start = selected[0]
    old = lines[start].rstrip('\n')
    if old not in ('--- a/' + relative, '--- /dev/null'):
        raise ValueError('patch old path mismatch')
    end = next((i for i in pairs if i > start), len(lines))
    # A following git-style header belongs to the next diff, not this one.
    for i in range(start + 2, end):
        if lines[i].startswith('diff --git '):
            end = i
            break
    return ''.join(lines[start:end]).encode('utf-8')


def materialize(relative):
    if not (INPUTS / 'wine-files.json').is_file() or not (INPUTS / 'wine').is_dir():
        raise unittest.SkipTest('prepared pinned Wine source inputs are unavailable')
    manifest = json.loads((INPUTS / 'wine-files.json').read_text())
    rows = [row for row in manifest['files'] if row['path'] == relative]
    if len(rows) > 1:
        raise ValueError('duplicate immutable source entry')
    current = ordinary_file(INPUTS / 'wine', relative).read_bytes() if rows else None
    if rows and digest(current) != rows[0]['sha256']:
        raise ValueError('immutable source bytes changed')
    series = json.loads((REPO / 'runtime/wine/patches/series.json').read_text())
    if series['base_commit'] != '4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf':
        raise ValueError('unexpected Wine source base')
    for row in series['patches']:
        changes = [change for change in row.get('changes', []) if change['path'] == relative]
        if not changes:
            continue
        if len(changes) != 1:
            raise ValueError('duplicate patch change')
        change = changes[0]
        observed = digest(current) if current is not None else None
        if observed != change['before_sha256']:
            raise ValueError('ordered preimage hash mismatch')
        patch = ordinary_file(REPO / 'runtime/wine/patches', row['path']).read_bytes()
        if digest(patch) != row['sha256']:
            raise ValueError('tracked patch bytes changed')
        with tempfile.TemporaryDirectory(prefix='pear-stage4-source-') as directory:
            folder = Path(directory)
            target = folder.joinpath(*PurePosixPath(relative).parts)
            target.parent.mkdir(parents=True)
            if current is not None:
                target.write_bytes(current)
            selected = folder / 'selected.patch'
            selected.write_bytes(file_diff(patch, relative))
            applied = subprocess.run(['/usr/bin/patch', '--batch', '--forward', '--fuzz=0',
                                      '-p1', '-d', str(folder), '-i', str(selected)],
                                     text=True, capture_output=True, timeout=15)
            if applied.returncode or re.search(r'\b(offset|fuzz)\b', applied.stdout + applied.stderr, re.I):
                raise ValueError('selected patch did not apply exactly: ' + applied.stdout + applied.stderr)
            current = ordinary_file(folder, relative).read_bytes()
        if digest(current) != change['after_sha256']:
            raise ValueError('ordered postimage hash mismatch')
    if current is None:
        raise ValueError('requested source is absent from input and tracked series')
    return current.decode('utf-8')


def configured_headers():
    if not (HEADERS / 'objects/include/config.h').is_file() or not (HEADERS / 'source/include/winnt.h').is_file():
        raise unittest.SkipTest('prepared pinned Wine configured headers are unavailable')
    return HEADERS / 'objects/include', HEADERS / 'source/include'
