#!/usr/bin/env python3
"""Build only the source-bound finite Wine memory-owner slice; never run Wine.

Reuse: unchanged Wine inventory/configuration and native tool/SDK readers, plus
FEX's exact unified-diff interpreter. Historical constructors remain unchanged.
The baseline install is a byte-preserved overlay, not a freshly rebuilt runtime.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import errno
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
import time

if __package__:
    from .common import REPO, Error, need, relative, read_relative, load_json, sha256, digest_bytes, write_json, operation_output, open_relative
    from .build import patch_sections, apply_hunks
    from . import byte_readers
else:
    from common import REPO, Error, need, relative, read_relative, load_json, sha256, digest_bytes, write_json, operation_output, open_relative
    from build import patch_sections, apply_hunks
    import byte_readers

BASE_BUILD = 'f7041374d7cdc86ea2991f859c8c102e369ed2247cb69a3647f4b9ddfae2f1eb'
BASE_SOURCE = '2c0c861669f9fd8853f8899eaeb08b18207b0cf26b34dae9efe707919e447bc7'
BASE_INSTALL = '15f6021af281269baac31437445369d0b28bd3c89e9329989db962b0edb852d9'
BASE_TOOLS = '9512935ff92fe3600e8aa51539ed82be712e023d8a557dcaa1f7aa945a68f1d6'
WINE_REVISION = '4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf'
RECORDS = ('runtime/wine/inputs.json', 'runtime/wine/build-config.json',
           'runtime/wine/toolchain.json', 'runtime/wine/patches/series.json',
           'runtime/fex/patches/memory-series.json')
PRODUCERS = ('tools/fex/memory_wine_build.py', 'tools/fex/common.py', 'tools/fex/build.py',
             'tools/fex/byte_readers.py', 'tools/wine/common.py', 'tools/wine/prepare.py',
             'tools/wine/toolchain.py', 'tools/wine/build.py')
FIXTURES = ('tests/fex/memory/owner_launch.c', 'tests/fex/memory/wine_owner.c',
            'tests/fex/memory/fixture_suite.c', 'tests/fex/memory/fixture_suite.h')
PATCH_NAMES = ('memory/0003a-wine-owner-core.patch', 'memory/0003b-wine-owner-bridge.patch')
PATCH_PATHS = (
    frozenset(('include/wine/pear_fex_memory.h', 'dlls/ntdll/unix/pear_fex_memory_private.h',
               'dlls/ntdll/unix/pear_fex_memory.c', 'dlls/ntdll/unix/pear_pe_arena.h',
               'dlls/ntdll/unix/pear_pe_arena.c')),
    frozenset(('dlls/ntdll/unix/virtual.c', 'dlls/ntdll/Makefile.in', 'dlls/ntdll/unixlib.h',
               'dlls/ntdll/unix/loader.c', 'dlls/ntdll/ntdll.spec', 'dlls/ntdll/pear_fex_memory.c', 'include/Makefile.in')))
TARGETS = ('dlls/ntdll/ntdll.so', 'dlls/ntdll/aarch64-windows/ntdll.dll')
REPLACEMENTS = dict(zip(TARGETS, ('lib/wine/aarch64-unix/ntdll.so', 'lib/wine/aarch64-windows/ntdll.dll')))
MACRO = '-DPEAR_FEX_MEMORY_FINITE_FIXTURE=1'
FALSE_FLAGS = ('wine_runtime_execution', 'pe_execution', 'fex_initialization',
               'translated_guest_execution', 'arm64ec_role_qualified', 'ec_registration_qualified',
               'runtime_qualified', 'game_qualified', 'distribution_qualified', 'stage3_complete')
MAX_LOG = 64 * 1024**2


@contextmanager
def wine_readers():
    """Isolate the legacy imports; never call a historical constructor/CLI."""
    names = ('common', 'prepare', 'toolchain', 'build')
    saved = {name: sys.modules.get(name) for name in names}
    try:
        for name in names:
            spec = importlib.util.spec_from_file_location(name, REPO / 'tools/wine' / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        try:
            yield sys.modules['toolchain'], sys.modules['build']
        except sys.modules['common'].Error as exc:
            raise Error(exc.code) from None
    finally:
        for name, module in saved.items():
            if module is None: sys.modules.pop(name, None)
            else: sys.modules[name] = module


def real_directory(value):
    path = Path(value).absolute()
    need(path.is_dir() and not path.is_symlink(), 'memory_wine_input_directory')
    # Only input directories may reside outside this worktree, never outputs.
    need(path.resolve() == path, 'memory_wine_input_directory_alias')
    return path


def pin_rows(rows):
    need(isinstance(rows, list) and rows, 'memory_wine_inventory')
    paths = [row.get('path') for row in rows]
    need(paths == sorted(set(paths)), 'memory_wine_inventory_paths')
    for row in rows:
        relative(row['path'])
        need(type(row.get('size_bytes')) is int and 0 <= row['size_bytes'] <= 2 * 1024**3
             and isinstance(row.get('sha256'), str) and re.fullmatch('[0-9a-f]{64}', row['sha256'])
             and type(row.get('mode')) is int and row['mode'] in (0o644, 0o755), 'memory_wine_inventory_row')
    return rows


def baseline_inputs(value):
    root = real_directory(value)
    need(sha256(root / 'build.json') == BASE_BUILD, 'memory_wine_baseline_receipt')
    record = load_json(root / 'build.json')
    need(record.get('record_kind') == 'wine_build' and record.get('passed') is True
         and record['variant'] == 'arm64' and record['wine_runtime_execution'] is False,
         'memory_wine_baseline_scope')
    need(record['source_manifest'] == {'path': 'source-files.json', 'sha256': BASE_SOURCE}
         and record['artifacts_manifest'] == {'path': 'installed-files.json', 'sha256': BASE_INSTALL},
         'memory_wine_baseline_manifests')
    need(sha256(root / 'source-files.json') == BASE_SOURCE and sha256(root / 'installed-files.json') == BASE_INSTALL,
         'memory_wine_baseline_manifest_digest')
    source, install = load_json(root / 'source-files.json'), load_json(root / 'installed-files.json')
    need(real_directory(root / 'source') == root / 'source' and real_directory(root / 'install') == root / 'install',
         'memory_wine_baseline_tree_root')
    pin_rows(source['files']); pin_rows(install['files'])
    need(source['symlinks'] == [], 'memory_wine_source_links')
    with wine_readers() as (_, owner):
        need(owner.inventory(root / 'source') == source, 'memory_wine_baseline_source_changed')
        need(owner.inventory(root / 'install', binary=True) == install, 'memory_wine_baseline_install_changed')
    names = ('inputs', 'config', 'toolchain', 'patch_series')
    need(record['record_hashes'] == {name: sha256(REPO / path) for name, path in zip(names, RECORDS[:4])},
         'memory_wine_baseline_records_changed')
    need(load_json(REPO / RECORDS[0])['components'][0]['commit'] == WINE_REVISION,
         'memory_wine_baseline_revision')
    return root, record, source, install


def checked_series(value):
    need(set(value) == {'schema_version', 'component', 'runtime_execution', 'baseline', 'patches',
                        'preserved_baseline', 'prototype'} and type(value['schema_version']) is int and value['schema_version'] == 1
         and value['component'] == 'wine-fex-memory' and value['runtime_execution'] is False,
         'memory_wine_series_scope')
    need(value['baseline'] == {'wine_revision': WINE_REVISION,
         'wine_patch_series_sha256': sha256(REPO / RECORDS[3]), 'qualified_source_files_sha256': BASE_SOURCE},
         'memory_wine_series_baseline')
    need(value['preserved_baseline'] == {'pe_interior_bytes': 1050345472, 'dynamic_bytes': 524288,
         'dynamic_slots': 8, 'alignment_bytes': 65536} and value['prototype'] == {
         'mapping_bytes': 1588985856, 'shared_bytes': 536870912, 'dispatcher_bytes': 1048576,
         'metadata_limit_bytes': 262144, 'wire_record_bytes': 128, 'unix_index': 10},
         'memory_wine_series_geometry')
    need(type(value['patches']) is list and len(value['patches']) == 2, 'memory_wine_patch_count')
    for index, row in enumerate(value['patches']):
        need(set(row) == {'file', 'sha256', 'license', 'sources'} and row['file'] == PATCH_NAMES[index]
             and type(row['license']) is str and row['license'], 'memory_wine_patch_shape')
        patch = REPO / 'runtime/fex/patches' / row['file']
        raw = read_relative(patch.parent, patch.name, 2 * 1024**2)
        need(digest_bytes(raw) == row['sha256'], 'memory_wine_patch_digest')
        sections = patch_sections(raw)
        need(set(sections) == PATCH_PATHS[index] and type(row['sources']) is list
             and len(row['sources']) == len(sections) and
             {s.get('path') for s in row['sources']} == set(sections), 'memory_wine_patch_path_set')
        for source in row['sources']:
            need(set(source) == {'path', 'preimage_sha256', 'postimage_sha256', 'postimage_bytes'}
                 and (source['preimage_sha256'] is None or re.fullmatch('[0-9a-f]{64}', source['preimage_sha256']))
                 and re.fullmatch('[0-9a-f]{64}', source['postimage_sha256'])
                 and type(source['postimage_bytes']) is int and 0 < source['postimage_bytes'] <= 2 * 1024**2,
                 'memory_wine_patch_source_row')
    return value


def derive_rows(source, series, baseline_root):
    rows = {row['path']: dict(row) for row in source['files']}
    changed = {}
    for patch in series['patches']:
        path = REPO / 'runtime/fex/patches' / patch['file']
        sections = patch_sections(read_relative(path.parent, path.name, 2 * 1024**2))
        for entry in patch['sources']:
            name = entry['path']; prior = rows.get(name)
            need((prior is None) == (entry['preimage_sha256'] is None), 'memory_wine_patch_preimage_presence')
            before = changed[name] if name in changed else (read_relative(baseline_root / 'source', name) if prior else None)
            need((digest_bytes(before) if before is not None else None) == entry['preimage_sha256'],
                 'memory_wine_patch_preimage')
            after = apply_hunks(before, sections[name], name)
            need(digest_bytes(after) == entry['postimage_sha256'] and len(after) == entry['postimage_bytes'],
                 'memory_wine_patch_postimage')
            changed[name] = after
            rows[name] = {'path': name, 'sha256': digest_bytes(after), 'size_bytes': len(after),
                          'mode': prior['mode'] if prior else 0o644, 'kind': 'data'}
    return {'schema_version': 1, 'record_kind': 'wine_build_inventory',
            'files': sorted(rows.values(), key=lambda row: row['path']), 'symlinks': []}, changed


def copy_inventory(origin, destination, inventory, changed=None):
    changed = changed or {}
    destination.mkdir(mode=0o700)
    for row in inventory['files']:
        path = destination.joinpath(*relative(row['path'])); path.parent.mkdir(parents=True, exist_ok=True)
        data = changed[row['path']] if row['path'] in changed else read_relative(origin, row['path'], 2 * 1024**3)
        need(len(data) == row['size_bytes'] and digest_bytes(data) == row['sha256'], 'memory_wine_copy_identity')
        with path.open('xb') as target: target.write(data)
        path.chmod(row['mode'])
    for row in inventory['symlinks']:
        path = destination.joinpath(*relative(row['path'])); path.parent.mkdir(parents=True, exist_ok=True)
        need(type(row['target']) is str and not row['target'].startswith('/') and '\\' not in row['target'],
             'memory_wine_copy_link')
        path.symlink_to(row['target'])
    with wine_readers() as (_, owner):
        actual = owner.inventory(destination, binary=any(row['kind'] != 'data' for row in inventory['files']))
        need(actual == inventory, 'memory_wine_copy_inventory')


def verify_tools(lock, record, baseline_root):
    tools = real_directory(record['tools_root'])
    origin = baseline_root.parents[2]
    need(tools.is_relative_to(origin / '.build/task4') and sha256(tools / 'prepared.json') == BASE_TOOLS
         and record['tool_prepared_sha256'] == BASE_TOOLS, 'memory_wine_tool_receipt')
    prepared = load_json(tools / 'prepared.json')
    need(prepared.get('passed') is True and prepared['lock_sha256'] == sha256(REPO / RECORDS[2]),
         'memory_wine_tool_lock')
    need({a['id'] for a in prepared['artifacts']} == {a['id'] for a in lock['artifacts']}
         and len(prepared['artifacts']) == len(lock['artifacts']), 'memory_wine_tool_set')
    artifacts = []
    for spec in lock['artifacts']:
        artifact = next(row for row in prepared['artifacts'] if row['id'] == spec['id'])
        archive = origin.joinpath(*relative(spec['download_path']))
        need(archive.stat().st_size == spec['size_bytes'] and sha256(archive) == spec['sha256'],
             'memory_wine_tool_archive')
        target = tools / spec['install_subdir']
        need(Path(artifact['path']) == target and not target.is_symlink(), 'memory_wine_tool_root')
        expected = set()
        with tarfile.open(archive, 'r:*') as packed:
            members, _ = byte_readers.archive_members(packed, spec['archive_root'], spec['max_unpacked_bytes'])
            for member, name in members:
                path = target.joinpath(*relative(name))
                if member.isdir(): need(path.is_dir() and not path.is_symlink(), 'memory_wine_tool_directory'); continue
                expected.add(name)
                if member.issym():
                    need(path.is_symlink() and os.readlink(path) == member.linkname
                         and path.resolve().is_relative_to(target), 'memory_wine_tool_link')
                else:
                    with packed.extractfile(member) as stream: digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                    need(sha256(path) == digest, 'memory_wine_tool_payload')
        observed = set()
        for directory, dirs, names in os.walk(target, followlinks=False):
            for name in names + [d for d in dirs if (Path(directory) / d).is_symlink()]:
                observed.add((Path(directory) / name).relative_to(target).as_posix())
        need(expected == observed, 'memory_wine_tool_inventory')
        manifest = Path(artifact['files_manifest']['path'])
        need(manifest.parent == tools and sha256(manifest) == artifact['files_manifest']['sha256'],
             'memory_wine_tool_manifest')
        artifacts.append({'id': spec['id'], 'archive_sha256': spec['sha256'],
                          'files_manifest_sha256': sha256(manifest)})
    with wine_readers() as (tc, _):
        sdk = tc.inspect_sdk(lock)
        native = {name: {'path': str(tc.native_tool(lock, name)),
                        'sha256': sha256(tc.native_tool(lock, name).resolve()),
                        **tc.inspect_macho(tc.native_tool(lock, name))}
                  for name in ('clang', 'clang++', 'make', 'flex')}
    bison = tools / 'bison/bin/bison'
    need(sha256(bison) == prepared['bison']['sha256'] and
         byte_readers.inspect_macho(bison)['architectures'] == [byte_readers.MACH_ARM64],
         'memory_wine_bison')
    verify_bison_logs(tools, prepared)
    closure = {}
    for name in ('clang', 'lld', 'llvm-ar', 'llvm-rc', 'llvm-dlltool', 'llvm-objdump'):
        path = tools / 'llvm-mingw/bin' / name
        closure[name] = byte_readers.inspect_closure(path, tools / 'llvm-mingw')
    invocation = {name: {'sha256': sha256(Path(name)), **byte_readers.inspect_macho(Path(name))}
                  for name in ('/usr/bin/arch', '/bin/sh')}
    return {'root': str(tools), 'invocation_primitives': invocation, 'prepared_sha256': BASE_TOOLS, 'sdk': sdk, 'native': native,
            'cross_closure': closure, 'bison_sha256': sha256(bison), 'artifacts': artifacts}



def verify_bison_logs(tools, prepared):
    """Read historical logs through their exact receipt-bound workspace alias.

    The original constructor invoked Bison through an owned space-free alias.
    Its logical log paths are retained, while bytes are read without aliases
    from the admitted tool root; this does not admit arbitrary redirected logs.
    """
    alias = prepared['alias']
    need(set(alias) == {'invoked', 'resolved'} and alias['resolved'] == str(tools),
         'memory_wine_bison_alias')
    invoked = Path(alias['invoked']); holder = invoked.parent
    need(invoked.name == 'workspace' and holder.parent == Path('/private/tmp')
         and re.fullmatch('pear-task4-[a-z0-9_]+', holder.name)
         and holder.is_dir() and not holder.is_symlink()
         and holder.stat().st_uid == os.getuid()
         and stat.S_IMODE(holder.stat().st_mode) == 0o700
         and invoked.is_symlink() and os.readlink(invoked) == str(tools)
         and invoked.resolve() == tools, 'memory_wine_bison_alias')
    commands = prepared['commands']
    need(type(commands) is list and [row['id'] for row in commands] ==
         ['bison.configure', 'bison.build', 'bison.install'], 'memory_wine_bison_command_set')
    for row in commands:
        need(type(row['exit_code']) is int and row['exit_code'] == 0
             and row['timed_out'] is False and row['output_limit'] is False
             and row['cwd'] == str(invoked / 'bison-build'), 'memory_wine_bison_command')
        for stream in ('stdout', 'stderr'):
            log = row[stream + '_log']
            name = 'bison-build/.pear-command-logs/' + row['id'] + '.' + stream
            need(set(log) == {'path', 'sha256', 'size_bytes'}
                 and log['path'] == str(invoked / name)
                 and type(log['size_bytes']) is int and 0 <= log['size_bytes'] <= 256 * 1024,
                 'memory_wine_bison_log')
            data = read_relative(tools, name, 256 * 1024)
            need(len(data) == log['size_bytes'] and digest_bytes(data) == log['sha256'],
                 'memory_wine_bison_log')


def snapshot(root, paths):
    rows = {}
    for name in paths:
        data = read_relative(REPO, name, 8 * 1024**2)
        path = root / 'inputs' / name; path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream: stream.write(data)
        path.chmod(0o600)
        rows[name] = digest_bytes(data)
    return rows


def verify_snapshots(root, rows, expected):
    need(set(rows) == set(expected), 'memory_wine_snapshot_set')
    for name, digest in rows.items():
        need(sha256(REPO / name) == digest and digest_bytes(read_relative(root / 'inputs', name)) == digest,
             'memory_wine_snapshot_changed')


def make_alias(root, tools):
    holder = Path(tempfile.mkdtemp(prefix='pear-task5-memory-', dir='/private/tmp'))
    holder.chmod(0o700)
    (holder / 'workspace').symlink_to(root, target_is_directory=True)
    (holder / 'tools').symlink_to(tools, target_is_directory=True)
    row = {'holder': str(holder), 'workspace': str(holder / 'workspace'), 'tools': str(holder / 'tools')}
    verify_alias(root, tools, row)
    return row


def verify_alias(root, tools, row):
    need(set(row) == {'holder', 'workspace', 'tools'}, 'memory_wine_alias_shape')
    holder = Path(row['holder'])
    need(holder.parent == Path('/private/tmp') and re.fullmatch('pear-task5-memory-[a-z0-9_]+', holder.name)
         and holder.is_dir() and not holder.is_symlink() and holder.stat().st_uid == os.getuid()
         and stat.S_IMODE(holder.stat().st_mode) == 0o700, 'memory_wine_alias_owner')
    for name, target in (('workspace', root), ('tools', tools)):
        path = Path(row[name]); need(path == holder / name and path.is_symlink()
             and os.readlink(path) == str(target) and path.resolve() == target,
             'memory_wine_alias_target')


def recipe(root, alias, tools, config, jobs):
    need(type(jobs) is int and 1 <= jobs <= 2, 'memory_wine_parallelism')
    workspace, tool_alias = Path(alias['workspace']), Path(alias['tools'])
    sdk = tools['sdk']['path']; native = tools['native']
    env = {'PATH': ':'.join((str(tool_alias / 'llvm-mingw/bin'), str(tool_alias / 'bison/bin'),
                            '/usr/bin', '/bin', '/usr/sbin', '/sbin')),
           'LC_ALL': 'C', 'LANG': 'C', 'SDKROOT': sdk,
           'TMPDIR': str(workspace / 'tmp'),
           'PKG_CONFIG_PATH': '', 'PKG_CONFIG_LIBDIR': '/nonexistent/pear-task5-memory',
           'CC': native['clang']['path'], 'CXX': native['clang++']['path'],
           'BISON': str(tool_alias / 'bison/bin/bison'), 'FLEX': native['flex']['path'],
           'CFLAGS': '-arch arm64 -isysroot ' + shlex.quote(sdk) + ' ' + MACRO,
           'CXXFLAGS': '-arch arm64 -isysroot ' + shlex.quote(sdk) + ' ' + MACRO,
           'CPPFLAGS': MACRO, 'aarch64_CFLAGS': MACRO,
           'MACOSX_DEPLOYMENT_TARGET': config['deployment_target']}
    variants = [v for v in config['variants'] if v['id'] == 'arm64']
    need(len(variants) == 1 and config['host_architecture'] == 'arm64'
         and config['sdk_version'] == '26.5' and config['deployment_target'] == '26.5',
         'memory_wine_configuration')
    arch = ['/usr/bin/arch', '-arm64']
    cross = str(tool_alias / 'llvm-mingw/bin/clang')
    configure = [*arch, '/bin/sh', '../source/configure', '--prefix=' + str(workspace / 'install'),
                 '--with-mingw=' + cross, *variants[0]['configure_args']]
    make = [*arch, native['make']['path'], '-j' + str(jobs), 'dlls/ntdll/all']
    launcher = [*arch, native['clang']['path'], '-arch', 'arm64', '-isysroot', sdk,
                '-std=c11', '-Wall', '-Wextra', '-Werror', '-O1', MACRO,
                str(workspace / 'inputs/tests/fex/memory/owner_launch.c'),
                '-o', str(workspace / 'fixtures/owner-launch')]
    # The ordinary fixture uses the build-only cross toolchain's default CRT.
    # Actual UCRT/API imports are recorded and qualified separately from FEX CRT.
    fixture = [*arch, cross, '--target=aarch64-w64-windows-gnu', '-std=c11', '-Wall', '-Wextra',
               '-Werror', '-O1', '-static', MACRO, '-I' + str(workspace / 'curated-include'),
               '-I' + str(workspace / 'inputs/tests/fex/memory'),
               str(workspace / 'inputs/tests/fex/memory/wine_owner.c'),
               str(workspace / 'inputs/tests/fex/memory/fixture_suite.c'),
               '-lkernel32', '-o', str(workspace / 'fixtures/wine-owner.exe')]
    return [('configure', configure, str(workspace / 'objects'), 600),
            ('ntdll', make, str(workspace / 'objects'), 1200),
            ('owner-launch', launcher, str(workspace), 120),
            ('wine-owner', fixture, str(workspace), 120)], env


def rule(makefile, target):
    lines = makefile.splitlines(); found = []
    for i, line in enumerate(lines):
        if line.startswith(target + ':'):
            cursor = i + 1
            while cursor < len(lines) and lines[cursor].startswith('  '): cursor += 1
            if cursor < len(lines) and lines[cursor].startswith('\t'):
                body = []
                while cursor < len(lines) and (lines[cursor].startswith(('\t', '  '))):
                    body.append(lines[cursor]); cursor += 1
                found.append(' '.join(body).replace('\\', ' '))
    need(len(found) == 1, 'memory_wine_make_rule:' + target)
    return found[0]


def observed_config(root):
    makefile = read_relative(root, 'objects/Makefile', 32 * 1024**2).decode()
    config = load_json(root / 'inputs/runtime/wine/build-config.json')
    variants = [item for item in config['variants'] if item['id'] == 'arm64']
    need(len(variants) == 1, 'memory_wine_configuration_variant')
    with wine_readers() as (_, owner):
        base = owner.observed_configuration(root / 'objects/Makefile', variants[0], 'page-wx',
                                            native_architecture_policy=True,
                                            source_policy='stable_relative_v1')
    variables = dict(re.findall(r'^([A-Za-z0-9_]+) = (.*)$', makefile, re.MULTILINE))
    for name in ('CPPFLAGS', 'CFLAGS', 'aarch64_CFLAGS'):
        need(shlex.split(variables.get(name, '')).count(MACRO) == 1, 'memory_wine_fixture_define:' + name)
    selected = ('dlls/ntdll/unix/pear_fex_memory.o', 'dlls/ntdll/unix/virtual.o',
                'dlls/ntdll/pear_fex_memory.o', 'dlls/ntdll/aarch64-windows/pear_fex_memory.o')
    host = rule(makefile, selected[0]); virtual = rule(makefile, selected[1])
    pe = rule(makefile, selected[3])
    need(all(MACRO in text or '$(CFLAGS)' in text for text in (host, virtual))
         and (MACRO in pe or '$(aarch64_CFLAGS)' in pe), 'memory_wine_fixture_compile_routes')
    need('dlls/ntdll/unix/pear_fex_memory.o' in rule(makefile, TARGETS[0])
         and 'dlls/ntdll/aarch64-windows/pear_fex_memory.o' in rule(makefile, TARGETS[1]),
         'memory_wine_fixture_link_routes')
    config = read_relative(root, 'objects/include/config.h', 2 * 1024**2)
    return {'baseline_configuration': base, 'finite_fixture_macro': MACRO,
            'host_owner_rule_sha256': digest_bytes(host.encode()), 'host_view_rule_sha256': digest_bytes(virtual.encode()),
            'pe_thunk_rule_sha256': digest_bytes(pe.encode()), 'config_header_sha256': digest_bytes(config),
            'makefile_sha256': sha256(root / 'objects/Makefile')}


def storage_size(root):
    total = 0
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in names:
            p = Path(directory) / name; info = p.lstat()
            need(stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode), 'memory_wine_storage_special')
            if stat.S_ISREG(info.st_mode): total += info.st_size
    return total


def budget(root, max_growth, reserve):
    need(type(max_growth) is int and 0 < max_growth <= 8 * 1024**3
         and type(reserve) is int and 0 < reserve <= 128 * 1024**3, 'memory_wine_storage_bounds')
    size, free = storage_size(root), shutil.disk_usage(root).free
    need(size <= max_growth, 'memory_wine_growth_limit')
    need(free >= reserve, 'memory_wine_free_floor')
    return {'owned_regular_bytes': size, 'free_bytes': free}


def execute(root, ident, argv, cwd, env, timeout, rows, max_growth, reserve):
    """Only the parent invokes this constructor; preserve actual child failures."""
    env = {**env, 'PWD': str(cwd)}
    logs = root / 'logs' / ident; logs.mkdir(parents=True)
    row = {'id': ident, 'argv': list(argv), 'cwd': cwd, 'environment': dict(env),
           'timeout_seconds': timeout, 'max_stream_bytes': MAX_LOG,
           'exit_code': None, 'status': 'start_unperformed', 'error_domain': None, 'error_code': None, 'logs': {}}
    rows.append(row)
    process = None; original = None; cleanup = None; started = time.monotonic(); checked = 0.0
    try:
        with (logs / 'stdout.bin').open('xb') as out, (logs / 'stderr.bin').open('xb') as err:
            process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                       stdout=out, stderr=err, start_new_session=True)
            row['status'] = 'running'
            while process.poll() is None:
                now = time.monotonic()
                need(now - started <= timeout, 'memory_wine_command_timeout')
                need(max(os.fstat(out.fileno()).st_size, os.fstat(err.fileno()).st_size) <= MAX_LOG,
                     'memory_wine_command_output_limit')
                if now - checked >= 5:
                    budget(root, max_growth, reserve); checked = now
                time.sleep(0.1)
            row['exit_code'] = process.wait(timeout=5)
            need(max(os.fstat(out.fileno()).st_size, os.fstat(err.fileno()).st_size) <= MAX_LOG,
                 'memory_wine_command_output_limit')
            need(type(row['exit_code']) is int and row['exit_code'] == 0, 'memory_wine_command_nonzero')
            row['status'] = 'completed'
    except BaseException as exc:
        original = exc; row['status'] = 'failed'
        row['error_domain'] = 'errno' if isinstance(exc, OSError) else 'constructor'
        row['error_code'] = exc.errno if isinstance(exc, OSError) else getattr(exc, 'code', type(exc).__name__)
    finally:
        if process is not None:
            if original is not None:
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                except OSError as exc: cleanup = {'domain': 'errno', 'code': exc.errno}
            try: row['exit_code'] = process.wait(timeout=5)
            except BaseException as exc:
                cleanup = {'domain': 'errno' if isinstance(exc, OSError) else 'constructor',
                           'code': exc.errno if isinstance(exc, OSError) else type(exc).__name__}
        row['elapsed_ms'] = round((time.monotonic() - started) * 1000)
        if cleanup is not None: row['cleanup_error'] = cleanup
        try:
            for stream in ('stdout', 'stderr'):
                path = logs / (stream + '.bin')
                if path.exists():
                    row['logs'][stream] = {'path': path.relative_to(root).as_posix(), 'sha256': sha256(path),
                                           'size_bytes': path.stat().st_size}
        except BaseException as exc:
            row['log_collection_error'] = {'domain': 'errno' if isinstance(exc, OSError) else 'constructor',
                                          'code': exc.errno if isinstance(exc, OSError) else getattr(exc, 'code', type(exc).__name__)}
            row['status'] = 'failed'
            if original is None: original = exc
        try: write_json(logs / 'command.json', row)
        except BaseException as exc:
            row['record_write_error'] = {'domain': 'errno' if isinstance(exc, OSError) else 'constructor',
                                        'code': exc.errno if isinstance(exc, OSError) else getattr(exc, 'code', type(exc).__name__)}
            row['status'] = 'failed'
            if original is None: original = exc
    if original is not None: raise original
    need(cleanup is None, 'memory_wine_command_cleanup')
    budget(root, max_growth, reserve)


def pe_facts(data, dll):
    need(isinstance(data, bytes) and len(data) <= 64 * 1024**2, 'memory_wine_pe_size')
    def number(fmt, offset):
        need(0 <= offset and offset + struct.calcsize('<' + fmt) <= len(data), 'memory_wine_pe_bounds')
        return struct.unpack_from('<' + fmt, data, offset)[0]
    need(len(data) >= 64 and data[:2] == b'MZ', 'memory_wine_pe_header')
    at = number('I', 60); opt = at + 24; count = number('H', at + 6); size = number('H', at + 20)
    need(at >= 64 and data[at:at + 4] == b'PE\0\0' and number('H', at + 4) == 0xaa64
         and number('H', opt) == 0x20b and 1 <= count <= 96 and size >= 240
         and number('I', opt + 108) == 16 and bool(number('H', at + 22) & 0x2000) == dll,
         'memory_wine_pe_native_arm64')
    sections = []
    for i in range(count):
        p = opt + size + i * 40
        span, rva, raw_size, raw, flags = [number('I', p + n) for n in (8, 12, 16, 20, 36)]
        need(raw + raw_size <= len(data), 'memory_wine_pe_section')
        sections.append((rva, min(span, raw_size), raw, flags))
    def mapped(rva, span):
        found = [raw + rva - base for base, length, raw, _ in sections
                 if span > 0 and rva >= base and rva - base + span <= length]
        need(len(found) == 1, 'memory_wine_pe_rva'); return found[0]
    def string(rva):
        p = mapped(rva, 1); end = data.find(b'\0', p, min(p + 4096, len(data)))
        need(end > p, 'memory_wine_pe_string'); mapped(rva, end - p + 1)
        return data[p:end].decode('ascii')
    need((number('I', opt + 112 + 13 * 8), number('I', opt + 116 + 13 * 8)) == (0, 0),
         'memory_wine_pe_delay_import')
    import_rva, import_size = number('I', opt + 120), number('I', opt + 124)
    imports = []
    if import_rva or import_size:
        need(import_rva and 20 <= import_size <= 1024**2, 'memory_wine_pe_import_directory')
        p = mapped(import_rva, import_size); terminated = False
        for offset in range(0, import_size - 19, 20):
            row = struct.unpack_from('<5I', data, p + offset)
            if not any(row): terminated = True; break
            name = string(row[3]).lower(); need(name not in imports, 'memory_wine_pe_import_duplicate'); imports.append(name)
        need(terminated, 'memory_wine_pe_import_terminator')
    exports = []; private_thunk = False
    export_rva, export_size = number('I', opt + 112), number('I', opt + 116)
    if export_rva or export_size:
        need(export_rva and 40 <= export_size <= 1024**2, 'memory_wine_pe_exports')
        p = mapped(export_rva, export_size)
        functions, names = number('I', p + 20), number('I', p + 24)
        need(0 < names <= functions <= 4096, 'memory_wine_pe_exports')
        table = mapped(number('I', p + 32), names * 4)
        ordinals = mapped(number('I', p + 36), names * 2)
        addresses = mapped(number('I', p + 28), functions * 4)
        exports = [string(number('I', table + 4 * i)) for i in range(names)]
        selected_ordinals = set()
        for index, name in enumerate(exports):
            ordinal = number('H', ordinals + 2 * index)
            need(ordinal < functions and ordinal not in selected_ordinals, 'memory_wine_pe_export_ordinal')
            selected_ordinals.add(ordinal)
            target = number('I', addresses + ordinal * 4)
            need(target, 'memory_wine_pe_export_missing_target')
            if name == '__wine_pear_fex_memory':
                need(not export_rva <= target < export_rva + export_size, 'memory_wine_pe_thunk_forwarded')
                mapped(target, 1)
                need(any(base <= target < base + length and flags & 0x20000000
                         for base, length, _, flags in sections), 'memory_wine_pe_thunk_non_executable')
                private_thunk = True
        need(len(set(exports)) == len(exports), 'memory_wine_pe_exports')
    return {'machine': 0xaa64, 'dll': dll, 'imports': sorted(imports), 'named_exports': sorted(exports),
            'delay_imports': False, 'private_memory_thunk_export': private_thunk, 'execution': False}


def inspect_rooted_macho(root, name):
    """Parse exactly the descriptor admitted beneath the owned output root."""
    with os.fdopen(open_relative(root, name), 'rb') as stream:
        before = os.fstat(stream.fileno())
        need(before.st_size <= 64 * 1024**2, 'memory_wine_native_output_size')
        data = stream.read(64 * 1024**2 + 1)
        stream.seek(0)
        info = byte_readers.inspect_macho('/dev/fd/' + str(stream.fileno()))
        after = os.fstat(stream.fileno())
        identity = lambda x: (x.st_dev, x.st_ino, x.st_mode, x.st_size, x.st_mtime_ns, x.st_ctime_ns)
        need(identity(before) == identity(after) and len(data) == before.st_size,
             'memory_wine_native_output_changed')
    need(read_relative(root, name, 64 * 1024**2) == data, 'memory_wine_native_output_changed')
    return data, info


def output_facts(root):
    facts = {}
    for name in ('install/lib/wine/aarch64-unix/ntdll.so', 'fixtures/owner-launch'):
        data, macho = inspect_rooted_macho(root, name)
        digest = digest_bytes(data)
        need(macho['architectures'] == [byte_readers.MACH_ARM64],
             'memory_wine_native_output')
        facts[name] = {'sha256': digest, 'size_bytes': len(data), 'role': 'new_native', **macho}
    name = 'install/lib/wine/aarch64-windows/ntdll.dll'
    data = read_relative(root, name, 64 * 1024**2); pe = pe_facts(data, True)
    need(pe['private_memory_thunk_export'] is True, 'memory_wine_thunk_export_missing')
    facts[name] = {'sha256': digest_bytes(data), 'size_bytes': len(data), 'role': 'new_ordinary_arm64_pe', **pe}
    name = 'fixtures/wine-owner.exe'
    data = read_relative(root, name, 64 * 1024**2); pe = pe_facts(data, False)
    need(pe['imports'] and all(value == 'kernel32.dll' or re.fullmatch('api-ms-win-crt-[a-z0-9-]+-l1-1-0.dll', value)
         for value in pe['imports']), 'memory_wine_fixture_import_scope')
    facts[name] = {'sha256': digest_bytes(data), 'size_bytes': len(data),
                   'role': 'new_default_mingw_crt_fixture', **pe}
    return facts


def verify_build(value):
    root = operation_output(value, require_empty=False, create=False)
    need(not (root / 'failure.json').exists(), 'memory_wine_build_failed_replay')
    result = load_json(root / 'build.json')
    need(result.get('record_kind') == 'fex_memory_wine_build' and result.get('scope') == 'fex_component'
         and result.get('build_complete') is True and all(result.get(k) is False for k in FALSE_FLAGS)
         and 'error' not in result and 'private_error' not in result, 'memory_wine_build_not_complete')
    need(type(result['storage_bounds']['max_growth_bytes']) is int
         and 0 < result['storage_bounds']['max_growth_bytes'] <= 8 * 1024**3
         and type(result['storage_bounds']['reserve_free_bytes']) is int
         and 0 < result['storage_bounds']['reserve_free_bytes'] <= 128 * 1024**3,
         'memory_wine_storage_bounds')
    baseline, old, source, install = baseline_inputs(result['baseline_root'])
    series = checked_series(load_json(REPO / RECORDS[4])); expected, _ = derive_rows(source, series, baseline)
    with wine_readers() as (_, owner):
        need(owner.inventory(root / 'source') == expected and load_json(root / 'source-files.json') == expected,
             'memory_wine_derived_source_changed')
        actual_install = owner.inventory(root / 'install', binary=True)
    verify_snapshots(root, result['record_sha256'], RECORDS)
    verify_snapshots(root, result['producer_sha256'], PRODUCERS)
    verify_snapshots(root, result['fixture_sha256'], FIXTURES)
    for name in PATCH_NAMES:
        path = 'runtime/fex/patches/' + name
        need(sha256(root / 'inputs' / path) == sha256(REPO / path), 'memory_wine_patch_snapshot')
    tools = verify_tools(load_json(REPO / RECORDS[2]), old, baseline)
    need(result['tool_facts'] == tools, 'memory_wine_tools_changed')
    verify_alias(root, Path(tools['root']), result['alias'])
    commands, env = recipe(root, result['alias'], tools, load_json(REPO / RECORDS[1]), result['jobs'])
    need(len(result['commands']) == len(commands), 'memory_wine_command_count')
    for row, (ident, argv, cwd, timeout) in zip(result['commands'], commands):
        need(row['id'] == ident and row['argv'] == argv and row['cwd'] == cwd and row['environment'] == {**env, 'PWD': cwd}
             and row['timeout_seconds'] == timeout and row['max_stream_bytes'] == MAX_LOG
             and type(row['exit_code']) is int and row['exit_code'] == 0 and row['status'] == 'completed'
             and row['error_domain'] is None and row['error_code'] is None
             and not any(k in row for k in ('cleanup_error', 'log_collection_error', 'record_write_error')),
             'memory_wine_command_replay')
        need(set(row['logs']) == {'stdout', 'stderr'}, 'memory_wine_command_logs')
        need(load_json(root / 'logs' / ident / 'command.json') == row, 'memory_wine_command_record')
        for channel, log in row['logs'].items():
            need(log['path'] == 'logs/' + ident + '/' + channel + '.bin'
                 and digest_bytes(read_relative(root, log['path'], MAX_LOG)) == log['sha256']
                 and (root / log['path']).stat().st_size == log['size_bytes'], 'memory_wine_command_log_identity')
    need(result['configuration'] == observed_config(root), 'memory_wine_configuration_replay')
    need(result['outputs'] == output_facts(root), 'memory_wine_output_replay')
    # The whole install overlay must differ from native6 only at two recorded files.
    wanted = {r['path']: dict(r) for r in install['files']}
    for name in REPLACEMENTS.values():
        actual = next(r for r in actual_install['files'] if r['path'] == name); wanted[name] = actual
    need(actual_install['files'] == sorted(wanted.values(), key=lambda r: r['path'])
         and actual_install['symlinks'] == install['symlinks'], 'memory_wine_overlay_scope')
    need(load_json(root / 'installed-files.json') == actual_install
         and sha256(root / 'installed-files.json') == result['installed_manifest_sha256']
         and sha256(root / 'source-files.json') == result['source_manifest_sha256'], 'memory_wine_output_manifest')
    header = read_relative(root / 'source', 'include/wine/pear_fex_memory.h')
    need(read_relative(root / 'curated-include', 'wine/pear_fex_memory.h') == header,
         'memory_wine_curated_header')
    need(sorted(p.relative_to(root / 'curated-include').as_posix() for p in
         (root / 'curated-include').rglob('*') if p.is_file()) == ['wine/pear_fex_memory.h'],
         'memory_wine_curated_header_set')
    return result


def construct(args):
    need(type(args.jobs) is int and 1 <= args.jobs <= 2, 'memory_wine_parallelism')
    need(Path(args.toolchain_lock).absolute() == REPO / RECORDS[2]
         and Path(args.memory_series).absolute() == REPO / RECORDS[4], 'memory_wine_record_path')
    root = operation_output(args.output, require_empty=args.require_empty)
    result = {'schema_version': 1, 'record_kind': 'fex_memory_wine_build', 'scope': 'fex_component',
              'build_complete': False, **{key: False for key in FALSE_FLAGS}, 'commands': [],
              'jobs': args.jobs, 'baseline_root': str(Path(args.baseline).absolute()),
              'storage_bounds': {'max_growth_bytes': args.max_growth_bytes, 'reserve_free_bytes': args.reserve_free_bytes}}
    try:
        baseline, old, source, install = baseline_inputs(args.baseline)
        series = checked_series(load_json(REPO / RECORDS[4]))
        result['record_sha256'] = snapshot(root, RECORDS)
        result['producer_sha256'] = snapshot(root, PRODUCERS)
        result['fixture_sha256'] = snapshot(root, FIXTURES)
        snapshot(root, ['runtime/fex/patches/' + name for name in PATCH_NAMES])
        tools = verify_tools(load_json(REPO / RECORDS[2]), old, baseline); result['tool_facts'] = tools
        estimated = sum(row['size_bytes'] for row in source['files'] + install['files'])
        need(estimated <= args.max_growth_bytes and shutil.disk_usage(root).free >= estimated + args.reserve_free_bytes,
             'memory_wine_copy_budget')
        budget(root, args.max_growth_bytes, args.reserve_free_bytes)
        expected, changed = derive_rows(source, series, baseline)
        copy_inventory(baseline / 'source', root / 'source', expected, changed)
        write_json(root / 'source-files.json', expected)
        copy_inventory(baseline / 'install', root / 'install', install)
        for name in ('objects', 'fixtures', 'tmp'): (root / name).mkdir(mode=0o700)
        curated = root / 'curated-include/wine'; curated.mkdir(parents=True)
        (curated / 'pear_fex_memory.h').write_bytes(read_relative(root / 'source', 'include/wine/pear_fex_memory.h'))
        alias = make_alias(root, Path(tools['root'])); result['alias'] = alias
        commands, env = recipe(root, alias, tools, load_json(REPO / RECORDS[1]), args.jobs)
        for ident, argv, cwd, timeout in commands:
            execute(root, ident, argv, cwd, env, timeout, result['commands'], args.max_growth_bytes, args.reserve_free_bytes)
            if ident == 'configure': result['configuration'] = observed_config(root)
        for name, target in REPLACEMENTS.items():
            data = read_relative(root / 'objects', name, 64 * 1024**2)
            path = root / 'install' / target
            need(path.is_file() and not path.is_symlink(), 'memory_wine_replacement_type')
            with path.open('wb') as stream: stream.write(data)
        result['outputs'] = output_facts(root)
        with wine_readers() as (_, owner): installed = owner.inventory(root / 'install', binary=True)
        write_json(root / 'installed-files.json', installed)
        result['installed_manifest_sha256'] = sha256(root / 'installed-files.json')
        result['source_manifest_sha256'] = sha256(root / 'source-files.json')
        result['build_complete'] = True
        write_json(root / 'build.json', result)
        verify_build(root)
        return result
    except BaseException as exc:
        result['build_complete'] = False
        result['error'] = getattr(exc, 'code', 'memory_wine_constructor_failed')
        if isinstance(exc, OSError): result['private_error'] = {'domain': 'errno', 'code': exc.errno}
        path = root / ('failure.json' if (root / 'build.json').exists() else 'build.json')
        write_json(path, result)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--toolchain-lock', default=str(REPO / RECORDS[2]))
    parser.add_argument('--memory-series', default=str(REPO / RECORDS[4]))
    parser.add_argument('--output', required=True)
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--max-growth-bytes', type=int, required=True)
    parser.add_argument('--reserve-free-bytes', type=int, required=True)
    parser.add_argument('--require-empty', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = verify_build(args.output) if args.verify_only else construct(args)
        print('{"build_complete":true,"wine_runtime_execution":false,"stage3_complete":false}')
        return 0
    except (Error, OSError, ValueError, KeyError) as exc:
        print('{"build_complete":false,"error":"' + getattr(exc, 'code', 'memory_wine_constructor_failed') + '"}')
        return 1


if __name__ == '__main__': raise SystemExit(main())
