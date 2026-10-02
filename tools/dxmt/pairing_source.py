#!/usr/bin/env python3
"""Replay the independently attributed graphics supplements without execution.

The exact-context hunk reader reuses the MIT Pear Task #5 reader algorithm.
Historic Wine and DXMT source/build receipts remain separate prerequisites.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import stat

from common import (REPO, Error, digest, fields, hex_digest, need, read_relative,
                    relative, real_directory)
import tools

SERIES = 'runtime/dxmt/patches/series.json'
BASES = {
    'wine': {'commit': '4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf',
             'prior_series_sha256': '39371f21f25cf153437fd523951be9f938cc1161bed5c4ef923583c74c89d086',
             'prior_source_manifest_sha256': '2c0c861669f9fd8853f8899eaeb08b18207b0cf26b34dae9efe707919e447bc7'},
    'dxmt': {'commit': '7c8dee1c2d73415301ceb7d1fa810861cef4cd67'},
}


def patch_sections(raw):
    need(type(raw) is bytes and 0 < len(raw) <= 4 * 1024**2, 'pair_patch_bound')
    sections = {}
    current = None
    for line in raw.decode('utf-8').splitlines(True):
        if line.startswith('diff --git '):
            match = re.fullmatch(r'diff --git a/(\S+) b/(\S+)\n', line)
            need(match is not None and match[1] == match[2], 'pair_patch_header')
            relative(match[1])
            current = match[1]
            need(current not in sections, 'pair_patch_duplicate')
            sections[current] = []
        else:
            need(current is not None, 'pair_patch_preamble')
            sections[current].append(line)
    return sections


def apply_hunks(before, lines, path):
    if before is None and lines[:1] == ['new file mode 100644\n']:
        lines = lines[1:]
    need(lines[:2] == ['--- ' + ('a/' + path if before is not None else '/dev/null') + '\n',
                      '+++ b/' + path + '\n'], 'pair_patch_file_header')
    original = (before or b'').decode('utf-8').splitlines(True)
    output, cursor, index = [], 0, 2
    while index < len(lines):
        match = re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n', lines[index])
        need(match is not None, 'pair_patch_hunk_header')
        old_start, old_count = int(match[1]), int(match[2] or 1)
        new_start, new_count = int(match[3]), int(match[4] or 1)
        offset = old_start - 1 if old_start else 0
        need(cursor <= offset <= len(original), 'pair_patch_hunk_order')
        output.extend(original[cursor:offset])
        cursor, index = offset, index + 1
        need(len(output) == (new_start - 1 if new_start else 0), 'pair_patch_new_offset')
        removed = added = 0
        while index < len(lines) and not lines[index].startswith('@@ '):
            line = lines[index]
            need(line and line[0] in ' +-', 'pair_patch_hunk_line')
            datum = line[1:]
            if index + 1 < len(lines) and lines[index + 1] == '\\ No newline at end of file\n':
                need(datum.endswith('\n'), 'pair_patch_no_newline_marker')
                datum = datum[:-1]
                index += 1
            if line[0] in ' -':
                need(cursor < len(original) and original[cursor] == datum, 'pair_patch_context')
                cursor += 1
                removed += 1
            if line[0] in ' +':
                output.append(datum)
                added += 1
            index += 1
        need(removed == old_count and added == new_count, 'pair_patch_hunk_count')
    output.extend(original[cursor:])
    return ''.join(output).encode('utf-8')


def validate_series(value, repo=REPO):
    fields(value, ['schema_version', 'record_kind', 'scope', 'baselines', 'patches'],
           'dxmt_graphics_patch_series')
    need(value['scope'] == 'typed_native_metal_pairing' and value['baselines'] == BASES,
         'pair_patch_baseline')
    rows = value['patches']
    need(type(rows) is list and len(rows) == 2 and
         [row.get('component') for row in rows] == ['wine', 'dxmt'], 'pair_patch_order')
    inputs, changes = {}, {}
    for row in rows:
        fields(row, ['component', 'path', 'sha256', 'license', 'provenance', 'changes'])
        component = row['component']
        expected = {'wine': 'wine/0001-typed-metal-lease.patch',
                    'dxmt': 'dxmt/0001-consume-typed-metal-lease.patch'}[component]
        need(row['path'] == expected and type(row['license']) is str and row['license'] and
             type(row['provenance']) is str and row['provenance'], 'pair_patch_origin')
        name = 'runtime/dxmt/patches/' + row['path']
        raw = read_relative(repo, name, 4 * 1024**2)
        need(hex_digest(row['sha256']) and digest(raw) == row['sha256'], 'pair_patch_bytes')
        sections = patch_sections(raw)
        declared = row['changes']
        need(type(declared) is list and 0 < len(declared) <= 64, 'pair_patch_change_bound')
        need(len({change.get('path') for change in declared}) == len(declared) and
             set(sections) == {change.get('path') for change in declared}, 'pair_patch_closed_set')
        for change in declared:
            fields(change, ['path', 'before_sha256', 'after_sha256', 'mode',
                            'payload_file', 'payload_sha256'])
            relative(change['path'])
            before = change['before_sha256']
            need((before is None or hex_digest(before)) and hex_digest(change['after_sha256']) and
                 change['mode'] == '100644', 'pair_patch_change_identity')
            payload_name = change['payload_file']
            if before is None:
                need(type(payload_name) is str and payload_name.startswith(
                     ('runtime/dxmt/patches/', 'tests/dxmt/pairing/')), 'pair_patch_payload_scope')
                payload = read_relative(repo, payload_name, 2 * 1024**2)
                need(hex_digest(change['payload_sha256']) and digest(payload) ==
                     change['payload_sha256'] == change['after_sha256'], 'pair_patch_payload_identity')
                inputs[payload_name] = digest(payload)
            else:
                need(payload_name is None and change['payload_sha256'] is None, 'pair_patch_modified_payload')
        inputs[name] = digest(raw)
        changes[component] = (declared, sections)
    return inputs, changes


def project(source, destination, declared, sections):
    """Copy regular source bytes only, then apply exact declared changes.

    There is no fuzzy patch, source command, alias, overwrite or cache mutation.
    The returned inventories include every unchanged source file and mode.
    """
    source = real_directory(source)
    destination = Path(destination)
    need(not destination.exists() and not destination.is_symlink() and
         not destination.parent.is_symlink(), 'pair_source_destination')
    real_directory(destination.parent)
    need(set(sections) == {row['path'] for row in declared} and
         len(declared) == len(sections), 'pair_source_closed_changes')
    before_rows = tools.files(source)
    need(all(set(row) == {'path', 'sha256', 'size_bytes', 'mode'} for row in before_rows),
         'pair_source_nonregular')
    need(0 < len(before_rows) <= 50000 and
         sum(row['size_bytes'] for row in before_rows) <= 1024**3, 'pair_source_size')
    destination.mkdir(mode=0o755)
    for row in before_rows:
        path = row['path']
        raw = read_relative(source, path, 32 * 1024**2)
        need(digest(raw) == row['sha256'] and len(raw) == row['size_bytes'], 'pair_source_changed_during_copy')
        target = destination.joinpath(*relative(path))
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
        target.chmod(row['mode'])
    expected = {row['path']: dict(row) for row in before_rows}
    for change in declared:
        path = change['path']
        target = destination.joinpath(*relative(path))
        before = change['before_sha256']
        if before is None:
            need(path not in expected and not target.exists(), 'pair_source_added_exists')
            raw = None
        else:
            need(path in expected and expected[path]['sha256'] == before, 'pair_source_preimage')
            raw = read_relative(destination, path, 32 * 1024**2)
            need(digest(raw) == before, 'pair_source_preimage')
        after = apply_hunks(raw, sections[path], path)
        need(digest(after) == change['after_sha256'], 'pair_source_postimage')
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('wb' if before is not None else 'xb') as stream:
            stream.write(after)
        target.chmod(0o644)
        expected[path] = {'path': path, 'sha256': digest(after),
                          'size_bytes': len(after), 'mode': 0o644}
    after_rows = tools.files(destination)
    need(after_rows == sorted(expected.values(), key=lambda row: row['path']), 'pair_source_full_derivation')
    need(tools.files(source) == before_rows, 'pair_source_cache_changed')
    return before_rows, after_rows
