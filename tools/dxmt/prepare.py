#!/usr/bin/env python3
"""Derive exact DXMT sources and configured gitlinks; no checkout or build."""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys
from common import (REPO, Error, MAX_BLOB, MAX_LISTING, MAX_SOURCE, decode_json, digest, encoded,
                    fields, git, hex_digest, load_json, need, output_directory, owned_directory,
                    producer_hashes, read_relative, real_directory, relative, tree_entries, validate_bare_repo, write_new)

INPUT_FIELDS = ['schema_version', 'record_kind', 'scope', 'audit_ref', 'components', 'gitlinks', 'wine_baseline', 'limits']
COMPONENT_FIELDS = ['id', 'url', 'commit', 'tree', 'cache_path', 'listing', 'materialize', 'source_path', 'terms', 'source_checks']

SOURCE_POLICY = {'dxmt-upstream': {'terms': ['LICENSE',
                             'COPYING.LIB',
                             'LICENSE.OLD',
                             'CONTRIBUTING.md',
                             'AGENTS.md',
                             'libs/DXBCParser/ShaderBinary.h',
                             'libs/DXBCParser/d3d12tokenizedprogramformat.hpp'],
                   'source_checks': ['.gitmodules',
                                     'build-arm64ec.txt',
                                     'meson.build',
                                     'meson.options',
                                     '.github/workflows/ci.yml',
                                     'src/winemetal/meson.build',
                                     'src/winemetal/unix/meson.build',
                                     'src/winemetal/unix/winemetal_unix.c',
                                     'src/airconv/meson.build',
                                     'src/airconv/darwin/meson.build']},
 'dxmt-directx': {'terms': ['COPYING.MinGW-w64.txt', 'd3d11.h', 'd3dcommon.h'], 'source_checks': []},
 'dxmt-nvapi': {'terms': ['License.txt'], 'source_checks': []},
 'llvm-dxmt': {'terms': ['llvm/LICENSE.TXT', 'CONTRIBUTING.md'], 'source_checks': []},
 'wine-upstream': {'terms': ['COPYING.LIB', 'LICENSE', 'NOTICES.md'],
                   'source_checks': ['dlls/winemac.drv/macdrv.h',
                                     'dlls/winemac.drv/window.c',
                                     'dlls/winemac.drv/Makefile.in']},
 'wine-dxmt-interface': {'terms': ['COPYING.LIB', 'LICENSE'], 'source_checks': []},
 'llvm-mingw-source': {'terms': ['LICENSE.txt'],
                       'source_checks': ['build-llvm.sh', 'build-mingw-w64.sh']},
 'llvm-mingw-llvm': {'terms': ['LICENSE.TXT', 'llvm/LICENSE.TXT'], 'source_checks': []},
 'mingw-w64-source': {'terms': ['COPYING',
                                'COPYING.MinGW-w64-runtime/COPYING.MinGW-w64-runtime.txt',
                                'COPYING.MinGW-w64/COPYING.MinGW-w64.txt'],
                      'source_checks': []}}


def validate_inputs(value, repo=REPO):
    fields(value, INPUT_FIELDS, 'dxmt_build_inputs')
    need(value['scope'] == 'dxmt_component', 'input_scope')
    reference = value['audit_ref']
    fields(reference, ['path', 'sha256'])
    raw = read_relative(repo, reference['path'])
    need(digest(raw) == reference['sha256'], 'audit_digest')
    audit = decode_json(raw)
    record_ids = set()
    source_ids = {row['component_id']: row for row in audit['components']}
    need(isinstance(value['components'], list) and 3 <= len(value['components']) <= 16, 'component_count')
    for item in value['components']:
        fields(item, COMPONENT_FIELDS)
        need(item['id'] not in record_ids and item['id'] in source_ids, 'component_identity')
        record_ids.add(item['id'])
        original = source_ids[item['id']]
        need((item['url'], item['commit'], item['tree'], item['cache_path']) ==
             (original['source']['url'], original['source']['commit_object_id'], original['source']['tree_object_id'],
              original['acquisition']['cache_path']), 'component_pin')
        need(type(item['materialize']) is bool and hex_digest(item['commit'], 40) and hex_digest(item['tree'], 40), 'component_fields')
        relative(item['cache_path'])
        if item['materialize']:
            relative(item['source_path'])
        else:
            need(item['source_path'] is None, 'unmaterialized_path')
        expected = next(row for row in original['content_digests'] if row['scope'] == 'git_tree_listing_bytes')
        need(item['listing'] == {key: expected[key] for key in ['cache_path', 'value', 'size_bytes']}, 'component_listing')
        need(item['id'] in SOURCE_POLICY, 'selected_source_policy')
        for selection in ['terms', 'source_checks']:
            rows = item[selection]
            need(isinstance(rows, list) and len(rows) == len(SOURCE_POLICY[item['id']][selection])
                 and {r['path'] for r in rows} == set(SOURCE_POLICY[item['id']][selection]), 'selected_source_policy')
        for row in item['terms'] + item['source_checks']:
            fields(row, ['path', 'git_blob', 'sha256', 'size_bytes'])
            relative(row['path'])
            need(hex_digest(row['git_blob'], 40) and hex_digest(row['sha256']) and type(row['size_bytes']) is int
                 and 0 <= row['size_bytes'] <= MAX_BLOB, 'source_file_pin')
    need(record_ids == set(SOURCE_POLICY), 'required_component')
    links = value['gitlinks']
    need(isinstance(links, list) and len(links) == 2, 'gitlink_count')
    seen = set()
    for link in links:
        fields(link, ['parent', 'path', 'component', 'commit', 'enabled', 'reason'])
        relative(link['path'])
        need(link['parent'] == 'dxmt-upstream' and link['component'] in record_ids and type(link['enabled']) is bool
             and link['path'] not in seen, 'gitlink_identity')
        child = next(c for c in value['components'] if c['id'] == link['component'])
        need(link['commit'] == child['commit'] and link['enabled'] == child['materialize'], 'gitlink_selection')
        seen.add(link['path'])
    baseline = value['wine_baseline']
    fields(baseline, ['patch_series', 'source_manifest_sha256', 'build_refs'])
    need(hex_digest(baseline['source_manifest_sha256']), 'wine_source_manifest')
    fields(baseline['patch_series'], ['path', 'sha256'])
    series = read_relative(repo, baseline['patch_series']['path'])
    need(digest(series) == baseline['patch_series']['sha256'], 'wine_patch_series')
    need(set(baseline['build_refs']) == {'native', 'companion'}, 'wine_roles')
    for reference in baseline['build_refs'].values():
        fields(reference, ['sha256', 'installed_manifest_sha256'])
        need(hex_digest(reference['sha256']) and hex_digest(reference['installed_manifest_sha256']), 'wine_build_reference')
    need(value['limits'] == {'max_listing_bytes': MAX_LISTING, 'max_blob_bytes': MAX_BLOB,
                             'max_materialized_bytes': MAX_SOURCE}, 'input_limits')
    return value


def inspect_sources(inputs, cache):
    cache = real_directory(cache)
    summaries, listings = [], {}
    for item in inputs['components']:
        repository = validate_bare_repo(cache, item['cache_path'])
        need(git(repository, 'rev-parse', '--show-object-format').strip() == b'sha1', 'git_object_format')
        need(git(repository, 'cat-file', '-t', item['commit']).strip() == b'commit', 'git_commit_type')
        git(repository, 'fsck', '--full', '--no-reflogs')
        need(git(repository, 'rev-parse', item['commit'] + '^{tree}').strip().decode() == item['tree'], 'git_tree_identity')
        listing = git(repository, 'ls-tree', '-r', '-z', '--full-tree', item['commit'])
        need(len(listing) == item['listing']['size_bytes'] and digest(listing) == item['listing']['value'], 'source_listing_digest')
        need(read_relative(cache, item['listing']['cache_path'], MAX_LISTING) == listing, 'cached_listing_bytes')
        # Nonmaterialized upstream LLVM symlinks remain pinned tree metadata only.
        entries = tree_entries(listing, metadata_only=not item['materialize'])
        by_path = {row['path']: row for row in entries}
        for row in item['terms'] + item['source_checks']:
            need(row['path'] in by_path and by_path[row['path']]['mode'] in ['100644', '100755']
                 and by_path[row['path']]['git_object'] == row['git_blob'], 'source_file_object')
            raw = git(repository, 'cat-file', 'blob', row['git_blob'])
            need(len(raw) == row['size_bytes'] and digest(raw) == row['sha256'], 'source_file_digest')
        declared = {l['path']: l for l in inputs['gitlinks'] if l['parent'] == item['id']}
        actual = {row['path']: row['git_object'] for row in entries if row['kind'] == 'commit'}
        need(set(actual) == set(declared) and all(declared[p]['commit'] == h for p, h in actual.items()), 'gitlink_inventory')
        summaries.append({'id': item['id'], 'commit': item['commit'], 'tree': item['tree'],
                          'tree_listing_sha256': digest(listing), 'entries': len(entries),
                          'materialized': item['materialize'], 'unmaterialized_symlink_entries': sum(r['mode'] == '120000' for r in entries),
                          'terms_verified': len(item['terms']),
                          'source_checks_verified': len(item['source_checks'])})
        listings[item['id']] = entries
    return summaries, listings


def scan_materialized(root):
    root = real_directory(root)
    rows, total, identities = [], 0, set()
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            need(not (Path(directory) / name).is_symlink(), 'materialized_symlink')
        for name in sorted(files):
            path = Path(directory) / name
            rel = path.relative_to(root).as_posix()
            relative(rel)
            info = path.lstat()
            need(stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) not in identities, 'materialized_file')
            identities.add((info.st_dev, info.st_ino))
            raw = read_relative(root, rel, MAX_BLOB)
            total += len(raw)
            need(total <= MAX_SOURCE and len(rows) < 2000, 'materialized_limit')
            need(stat.S_IMODE(info.st_mode) in [0o644, 0o755], 'materialized_mode')
            rows.append({'path': rel, 'mode': '100755' if info.st_mode & 0o111 else '100644',
                         'git_blob': hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest(),
                         'sha256': digest(raw), 'size_bytes': len(raw)})
    return sorted(rows, key=lambda r: r['path'])


def expected_materialized(inputs, listings):
    rows = {}
    for item in inputs['components']:
        if item['materialize']:
            for row in listings[item['id']]:
                if row['kind'] == 'blob':
                    name = item['source_path'] + '/' + row['path']
                    need(name not in rows, 'materialized_path_conflict')
                    rows[name] = row
    return rows


def prepare(inputs_path, source_cache, output_value, repo=REPO):
    repo = real_directory(repo)
    input_path = Path(inputs_path)
    input_path = input_path if input_path.is_absolute() else repo / input_path
    need(input_path.is_relative_to(repo), 'input_scope')
    raw = read_relative(repo, input_path.relative_to(repo).as_posix())
    value = validate_inputs(decode_json(raw), repo)
    cache = real_directory(source_cache)
    summaries, listings = inspect_sources(value, cache)
    output = output_directory(output_value, repo)
    need(not cache.is_relative_to(output) and not output.is_relative_to(cache), 'source_output_alias')
    source = output / 'source'
    source.mkdir(mode=0o755)
    total = 0
    expected = expected_materialized(value, listings)
    for item in value['components']:
        if not item['materialize']:
            continue
        repository = cache / item['cache_path']
        for row in listings[item['id']]:
            if row['kind'] == 'commit':
                continue
            content = git(repository, 'cat-file', 'blob', row['git_object'])
            need(len(content) <= MAX_BLOB, 'blob_limit')
            total += len(content)
            need(total <= MAX_SOURCE, 'materialized_limit')
            need(hashlib.sha1(f'blob {len(content)}\0'.encode() + content).hexdigest() == row['git_object'], 'blob_identity')
            target = source / item['source_path'] / row['path']
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            with target.open('xb') as stream:
                stream.write(content)
            target.chmod(0o755 if row['mode'] == '100755' else 0o644)
    rows = scan_materialized(source)
    need(set(r['path'] for r in rows) == set(expected), 'materialized_inventory')
    manifest = {'schema_version': 1, 'record_kind': 'dxmt_source_files', 'files': rows}
    write_new(output / 'source-files.json', manifest)
    need(read_relative(repo, input_path.relative_to(repo).as_posix()) == raw, 'inputs_changed')
    result = {'schema_version': 1, 'record_kind': 'dxmt_prepared_sources', 'scope': 'dxmt_component',
              'inputs_ref': {'path': input_path.relative_to(repo).as_posix(), 'sha256': digest(raw)},
              'source_cache': str(cache), 'components': summaries,
              'manifest_ref': {'path': 'source-files.json', 'sha256': digest(encoded(manifest))},
              'producers': producer_hashes(repo), 'inventory_complete': True,
              'dxmt_built': False, 'pairing_verified': False, 'runtime_eligible': False}
    write_new(output / 'prepared.json', result)
    return result


def verify_prepared(path, repo=REPO):
    root = owned_directory(path, repo)
    value = load_json(root / 'prepared.json')
    fields(value, ['schema_version', 'record_kind', 'scope', 'inputs_ref', 'source_cache', 'components',
                   'manifest_ref', 'producers', 'inventory_complete', 'dxmt_built', 'pairing_verified', 'runtime_eligible'],
           'dxmt_prepared_sources')
    need(value['scope'] == 'dxmt_component' and value['inventory_complete'] is True
         and all(value[k] is False for k in ['dxmt_built', 'pairing_verified', 'runtime_eligible']), 'prepared_scope')
    need(value['producers'] == producer_hashes(repo), 'producer_changed')
    raw = read_relative(repo, value['inputs_ref']['path'])
    need(digest(raw) == value['inputs_ref']['sha256'], 'prepared_input_digest')
    inputs = validate_inputs(decode_json(raw), repo)
    summaries, listings = inspect_sources(inputs, value['source_cache'])
    need(value['components'] == summaries, 'prepared_source_summaries')
    manifest_raw = read_relative(root, value['manifest_ref']['path'])
    need(value['manifest_ref']['path'] == 'source-files.json' and digest(manifest_raw) == value['manifest_ref']['sha256'], 'prepared_manifest_digest')
    manifest = decode_json(manifest_raw)
    fields(manifest, ['schema_version', 'record_kind', 'files'], 'dxmt_source_files')
    rows = scan_materialized(root / 'source')
    need(rows == manifest['files'], 'prepared_materialized_changed')
    expected = expected_materialized(inputs, listings)
    need(set(r['path'] for r in rows) == set(expected), 'prepared_materialized_inventory')
    for row in rows:
        need((row['git_blob'], row['mode']) == (expected[row['path']]['git_object'], expected[row['path']]['mode']),
             'prepared_source_object')
    return value


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs', required=True)
    p.add_argument('--source-cache', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--require-empty', action='store_true', required=True)
    a = p.parse_args()
    try:
        value = prepare(a.inputs, a.source_cache, a.output)
        print(encoded({'prepared': True, 'components': len(value['components']), 'runtime_eligible': False}).decode(), end='')
        return 0
    except (Error, OSError, ValueError, KeyError, StopIteration, UnicodeError, subprocess.SubprocessError) as error:
        print(encoded({'prepared': False, 'error': error.code if isinstance(error, Error) else 'preparation_failed'}).decode(), end='')
        return 1

if __name__ == '__main__':
    sys.exit(main())
