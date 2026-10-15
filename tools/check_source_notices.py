#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Incremental source-header guard; not a full SPDX/REUSE or provenance audit."""
import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

SOURCE_SUFFIXES = frozenset('''
.py .rs .swift .c .h .cc .cpp .cxx .hpp .m .mm .js .cjs .mjs .ts .tsx .jsx
.css .sh .bash .zsh .fish .ps1 .cmake .s .S .asm .html .htm .metal .go .rb
.pl .lua .toml .yaml .yml
'''.split())
SOURCE_NAMES = {'Makefile', 'GNUmakefile', 'CMakeLists.txt', 'Dockerfile'}
# These are audited, unmodified upstream notice/source copies, not Pear code.
UPSTREAM_COPIES = ('preview/licenses/', 'preview/runtime-notices/')
POLICY = '.github/source-notice-exceptions.json'
DEFAULT_LICENSE = 'GPL-3.0-or-later'


def git(root, *args, optional=False):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True)
    if result.returncode and not optional:
        raise ValueError(result.stderr.decode(errors='replace').strip())
    return None if result.returncode else result.stdout


def revision(root, value):
    return git(root, 'rev-parse', '--verify', '--end-of-options', value + '^{commit}').decode().strip()


def blob(root, ref, path):
    return git(root, 'show', f'{ref}:{path}', optional=True)


def working_blob(root, path):
    file = root / path
    # Do not dereference source symlinks or a symlinked ancestor outside the repo.
    if any(p.is_symlink() for p in [file, *file.parents] if p != root and root in p.parents):
        raise ValueError(f'{path}: source symlink needs manual attribution review')
    return file.read_bytes()


def changes(root, base, head):
    args = ['diff', '--name-status', '-z', '--find-renames', '--diff-filter=ACMRT', base]
    if head:
        args.append(head)
    tokens = git(root, *args, '--').decode('utf-8').split('\0')
    found = []
    cursor = 0
    while cursor < len(tokens) - 1:
        status, path = tokens[cursor:cursor + 2]
        cursor += 2
        if status.startswith(('R', 'C')):
            old, path = path, tokens[cursor]
            cursor += 1
        else:
            old = path
        found.append((old, path))
    if not head:
        untracked = git(root, 'ls-files', '--others', '--exclude-standard', '-z').decode().split('\0')
        found.extend((p, p) for p in untracked if p)
    # Changing/removing an exception must recheck its source even if unchanged.
    old_policy = blob(root, base, POLICY)
    new_policy = blob(root, head, POLICY) if head else (working_blob(root, POLICY) if (root / POLICY).exists() else None)
    if old_policy != new_policy:
        for content in (old_policy, new_policy):
            if content:
                found.extend((p, p) for p in load_policy(content))
    return sorted(set(found))


def load_policy(content):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'duplicate exception: {key}')
            result[key] = value
        return result
    policy = json.loads(content, object_pairs_hook=unique) if content else {}
    if not isinstance(policy, dict):
        raise ValueError('notice exceptions must be a path-keyed object')
    for path, entry in policy.items():
        if PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts or not path:
            raise ValueError('exception path must be repository-relative')
        if not isinstance(entry, dict) or set(entry) != {'license', 'reason', 'notice'}:
            raise ValueError(f'{path}: exception needs license, reason and notice')
        if not all(isinstance(v, str) and v.strip() for v in entry.values()):
            raise ValueError(f'{path}: exception fields cannot be empty')
        notice = PurePosixPath(entry['notice'])
        if notice.is_absolute() or '..' in notice.parts:
            raise ValueError(f'{path}: exception notice must be repository-relative')
    return policy


def header(text):
    """Only leading comments count; a tag in code or a docstring is not a notice."""
    result, end = [], None
    for line in text.splitlines():
        stripped = line.strip()
        if end:
            before, separator, after = stripped.partition(end)
            result.append(before.lstrip('*').strip())
            if separator:
                end = None
                if after.strip():
                    break
            continue
        if not stripped or stripped.startswith('#!'):
            continue
        marker = next((m for m in ('/*', '<!--', '--[[') if stripped.startswith(m)), None)
        if marker:
            closing = {'/*': '*/', '<!--': '-->', '--[[': ']]'}[marker]
            before, separator, after = stripped[len(marker):].partition(closing)
            result.append(before.strip())
            if separator and after.strip():
                break
            if not separator:
                end = closing
        elif stripped.startswith(('//', '#', '--', ';')):
            result.append(stripped.lstrip('/#-;! ').strip())
        else:
            break
    return result


def notices(text):
    lines = header(text)
    licenses = {line.split(':', 1)[1].strip() for line in lines
                if line.startswith('SPDX-License-Identifier:')}
    copyrights = {line for line in lines if re.match(
        r'(SPDX-FileCopyrightText:\s*|Copyright\s+(?:\([Cc]\)\s*)?|Copyright\s*©\s*)\d{4}\b.+\S', line)}
    return licenses, copyrights


def check(root, base, head=None):
    read = lambda p: blob(root, head, p) if head else (working_blob(root, p) if (root / p).exists() or (root / p).is_symlink() else None)
    policy = load_policy(read(POLICY))
    errors, checked, excluded = [], [], []
    for old, path in changes(root, base, head):
        if path.startswith(UPSTREAM_COPIES):
            excluded.append(path)
            continue
        data = read(path)
        previous = blob(root, base, old) or b''
        if data is None:  # A removed exception can refer to a deleted source.
            continue
        name = PurePosixPath(path)
        if name.suffix not in SOURCE_SUFFIXES and name.name not in SOURCE_NAMES and not data.startswith(b'#!') and not previous.startswith(b'#!'):
            continue
        checked.append(path)
        try:
            text = data.decode('utf-8')
            before = previous.decode('utf-8')
        except UnicodeDecodeError:
            errors.append(f'{path}: source is not UTF-8; needs manual notice handling')
            continue
        licenses, copyrights = notices(text)
        old_licenses, old_copyrights = notices(before)
        expected = old_licenses or {policy.get(path, {}).get('license', DEFAULT_LICENSE)}
        if licenses != expected or not all(licenses):
            errors.append(f'{path}: expected SPDX license {sorted(expected)}, found {sorted(licenses)}')
        coding = [i for i, line in enumerate(text.splitlines())
                  if re.match(r'^[ \t]*#.*?coding[:=][ \t]*[-\w.]+', line)]
        if name.suffix == '.py' and coding and coding[0] > 1:
            errors.append(f'{path}: Python encoding declaration must remain in the first two lines')
        if not copyrights:
            errors.append(f'{path}: missing copyright holder/year in leading comment header')
        if not old_copyrights.issubset(copyrights):
            errors.append(f'{path}: existing copyright notice removed or changed; preserve it and append new attribution')
        if path in policy and read(policy[path]['notice']) is None:
            errors.append(f'{path}: referenced exception notice is missing')
        if before.startswith('#!') and not text.startswith('#!'):
            errors.append(f'{path}: original shebang must remain the first line')
    return {'checked': checked, 'upstream_copies_for_manual_review': excluded, 'errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, help='exact comparison revision; missing refs fail')
    parser.add_argument('--head', help='committed revision; omit to include working changes and untracked files')
    args = parser.parse_args()
    try:
        root = Path(git(Path.cwd(), 'rev-parse', '--show-toplevel').decode().strip())
        base = revision(root, args.base)
        head = revision(root, args.head) if args.head else None
        result = check(root, base, head)
        print(json.dumps({'base': base, 'head': head or 'worktree', **result}, indent=2))
        return bool(result['errors'])
    except (ValueError, OSError) as error:
        print(f'Source notice check failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
