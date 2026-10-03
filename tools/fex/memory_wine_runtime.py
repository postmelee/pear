#!/usr/bin/env python3
"""Materialize one source-bound development-only ordinary Wine owner runtime.

Reuse exact reviewed Task #7 signing/profile functions in an isolated namespace.
Structural replay is pure; only the orchestrator calls Apple signing/admission.
No FEX initialization, Wine launch, generated-code entry or guest work runs here.
"""
from __future__ import annotations
import argparse
import ast
import ctypes
import errno
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import platform
import plistlib
import re
import selectors
import signal
import stat
import struct
import subprocess
import sys
import time
from types import SimpleNamespace
import uuid

if __package__:
    from .common import (REPO, Error, need, relative, read_relative, open_relative,
                         decode_json, load_json, record, encoded, sha256, digest_bytes,
                         write_json, operation_output)
    from . import memory_wine_build as builder, byte_readers
else:
    from common import (REPO, Error, need, relative, read_relative, open_relative,
                        decode_json, load_json, record, encoded, sha256, digest_bytes,
                        write_json, operation_output)
    import memory_wine_build as builder
    import byte_readers

BUNDLE_ID = 'io.github.postmelee.pear.wine-loader'
BUNDLE = 'PearWineLoader.app'
PAYLOAD = BUNDLE + '/Contents/Resources/runtime'
MAIN = BUNDLE + '/Contents/MacOS/wine'
NTDLL_ALIAS = BUNDLE + '/Contents/MacOS/ntdll.so'
LOADER = 'lib/wine/aarch64-unix/wine'
NTDLL = 'lib/wine/aarch64-unix/ntdll.so'
NTDLL_PE = 'lib/wine/aarch64-windows/ntdll.dll'
SERVER = 'bin/wineserver'
SENTINEL = 'libexec/pear-stage2/sentinel'
LAUNCHER = 'libexec/pear-fex-memory/owner-launch'
FIXTURE = 'libexec/pear-fex-memory/wine-owner.exe'
SCOPE = 'development_finite_native_memory_owner'
RESERVE = 4 * 1024**3
LIMIT = 2 * 1024**2
CLONE_FLAGS = 0x0001 | 0x0002 | 0x0008
CLONE_FALLBACK = frozenset((errno.ENOTSUP, errno.EOPNOTSUPP, errno.EXDEV))
INFO = {'CFBundleIdentifier': BUNDLE_ID, 'CFBundleExecutable': 'wine', 'CFBundleName': 'Pear Wine Loader',
        'CFBundlePackageType': 'APPL', 'CFBundleVersion': '1', 'CFBundleShortVersionString': '0.1',
        'LSMinimumSystemVersion': '26.5'}
REUSE_PINS = {
    'tools/dxmt/pairing_runtime.py': '617b00dbd281271b26bc1d0d9621dcd68246805218b5bf96bdc811947f9811d5',
    'tools/dxmt/common.py': '3593e8e2a80d535143e2baae7e945ce90918520711993848dc33355d9dac0e75',
    'tools/dxmt/build.py': '283e52d5d2f9a42d403624370537e8bf4ebe1859a75a5436d57a90975e8ef144',
}
REUSE_NAMES = {
    'tools/dxmt/common.py': ('digest', 'fields', 'real_directory', 'write_new', 'clean_env', 'run_bounded'),
    'tools/dxmt/build.py': ('write_bytes',),
    'tools/dxmt/pairing_runtime.py': (
        'same', 'native_error', 'failure_fields', 'wrapped_error', 'certificate_prefix', 'signer_leaf',
        'select_functions', 'source_constant', 'legacy', 'pe_machine', 'cms_plist', 'native', 'verify_commands',
        'profile_recipe', 'profile_from_logs', 'capture_authorization', 'verify_authorization',
        'signature_recipe', 'signature_from_logs', 'signing_recipe', 'signatures_from_logs'),
}
PRODUCERS = tuple(sorted(set(builder.PRODUCERS) | {
    'tools/fex/memory_wine_runtime.py', 'tools/wine/signing.py',
    'host/probe/provisioned_probe.py', 'host/probe/hardened_baseline.py'}))
FALSE_FLAGS = ('wine_runtime_execution', 'pe_execution', 'generated_code_execution', 'fex_initialization',
               'hybrid_execution', 'translated_guest_execution', 'arm64ec_role_qualified',
               'ec_registration_qualified', 'runtime_qualified', 'game_qualified', 'distribution_qualified',
               'stage3_complete')
RUNTIME_FIELDS = ('schema_version', 'record_kind', 'scope', 'build_ref', 'signing_reuse', 'producers',
                  'native_images', 'pe_images', 'entrypoints', 'authorization', 'signed_receipt',
                  'baseline_loader_capacity', 'code_publication_policy', 'runtime_eligible', *FALSE_FLAGS)


def same(left, right, code):
    if type(left) is bytes or type(right) is bytes:
        need(type(left) is bytes and type(right) is bytes and left == right, code)
    else:
        need(encoded(left) == encoded(right), code)


def fields(value, names, kind=None):
    need(type(value) is dict and set(value) == set(names), 'memory_runtime_fields')
    if kind:
        need(value.get('schema_version') == 1 and type(value['schema_version']) is int
             and value.get('record_kind') == kind, 'memory_runtime_record_kind')


def producers(repo=REPO):
    return {name: digest_bytes(read_relative(repo, name)) for name in PRODUCERS}


def selected(raw, names, namespace, label):
    nodes = [node for node in ast.parse(raw, filename=label).body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    need(len(nodes) == len(names) and {node.name for node in nodes} == set(names)
         and all(not node.decorator_list for node in nodes), 'memory_runtime_reuse_functions')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), label, 'exec'), namespace)


def signing_helpers(reuse_root, repo=REPO):
    """Exact captured function bodies, no source-script entrypoint or monkeypatch.

    Fixed globals adapt only the reviewed signing/receipt scope to Task #5.
    Full upstream helper bytes remain pinned and captured, never rewritten.
    """
    reuse_root = builder.real_directory(reuse_root)
    captured = {}
    for path, pin in REUSE_PINS.items():
        raw = read_relative(reuse_root, path, LIMIT)
        need(digest_bytes(raw) == pin, 'memory_runtime_reuse_pin')
        captured[path] = raw
    namespace = {'REPO': Path(repo), 'Error': Error, 'need': need, 'relative': relative,
        'read_relative': read_relative, 'open_relative': open_relative, 'decode_json': decode_json, 'record': record,
        'encoded': encoded, 'sha256': sha256, 'Path': Path, 'os': os, 'stat': stat, 're': re,
        'hashlib': hashlib, 'ast': ast, 'datetime': datetime, 'timezone': timezone, 'plistlib': plistlib,
        'platform': platform, 'struct': struct, 'sys': sys, 'time': time, 'uuid': uuid,
        'selectors': selectors, 'signal': signal, 'subprocess': subprocess,
        'SimpleNamespace': SimpleNamespace, 'MACH_ARM64': byte_readers.MACH_ARM64,
        'MAX_LISTING': 32 * 1024**2, 'LIMIT': LIMIT, 'CERTIFICATE_LIMIT': 128 * 1024,
        'MAX_CERTIFICATES': 8, 'BUNDLE_ID': BUNDLE_ID, 'BUNDLE': BUNDLE, 'MAIN': MAIN,
        'SCOPE': SCOPE, 'ENV': {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LANG': 'C', 'LC_ALL': 'C'}}
    selected(captured['tools/dxmt/common.py'], REUSE_NAMES['tools/dxmt/common.py'], namespace,
             'reviewed Task #7 tools/dxmt/common.py')
    byte_namespace = {'relative': relative, 'os': os}
    selected(captured['tools/dxmt/build.py'], REUSE_NAMES['tools/dxmt/build.py'], byte_namespace,
             'reviewed Task #7 tools/dxmt/build.py')
    namespace['stage3'] = SimpleNamespace(write_bytes=byte_namespace['write_bytes'])
    selected(captured['tools/dxmt/pairing_runtime.py'], REUSE_NAMES['tools/dxmt/pairing_runtime.py'], namespace,
             'reviewed Task #7 tools/dxmt/pairing_runtime.py')
    return SimpleNamespace(**namespace), captured


def prerequisite(root, repo=REPO):
    root = operation_output(root, repo_root=repo, require_empty=False, create=False)
    # The current source/tool/build replay is mandatory; no passed-flag shortcut.
    built = builder.verify_build(root)
    baseline_root, baseline, _, old_install = builder.baseline_inputs(built['baseline_root'])
    need(baseline['variant'] == 'arm64' and baseline['code_publication_policy'] == 'page-wx',
         'memory_runtime_baseline_scope')
    install = builder.real_directory(root / 'install')
    manifest = load_json(root / 'installed-files.json')
    need(sha256(root / 'installed-files.json') == built['installed_manifest_sha256'],
         'memory_runtime_install_manifest')
    return built, baseline_root, baseline, baseline_root / 'install', install, manifest, old_install


def metadata_reader(repo=REPO):
    """Reuse the source-bound Wine metadata-only container reader unchanged."""
    raw = read_relative(repo, 'tools/wine/build.py')
    assignments = [node for node in ast.parse(raw).body if isinstance(node, ast.Assign)
        and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == 'WINMD_PATHS']
    need(len(assignments) == 1, 'memory_runtime_metadata_paths_source')
    namespace = {'Path': Path, 'struct': struct, 'need': need, 'Error': Error}
    exec(compile(ast.Module(body=assignments, type_ignores=[]), 'source-bound Wine WINMD_PATHS', 'exec'), namespace)
    selected(raw, ('inspect_winmd',), namespace, 'source-bound Wine inspect_winmd')
    return SimpleNamespace(**namespace)


def validate_metadata(root, name, logical_path, expected, reader):
    need(logical_path in reader.WINMD_PATHS and expected.get('kind') == 'pe_metadata'
         and expected.get('metadata_only') is True and expected.get('machine') == 0x14c,
         'memory_runtime_metadata_scope')
    raw = read_relative(root, name, 32 * 1024**2)
    facts = reader.inspect_winmd(root / name)
    need(read_relative(root, name, 32 * 1024**2) == raw, 'memory_runtime_metadata_changed')
    same(facts, {key: expected.get(key) for key in facts}, 'memory_runtime_metadata_facts')
    return facts


def pe_scope(row, machine, repo=REPO):
    """Classify preserved negative controls without granting load admission."""
    raw = read_relative(repo, 'tools/wine/signing.py')
    nodes = [node for node in ast.parse(raw).body if isinstance(node, ast.Assign)
        and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == 'API_GUESTS']
    need(len(nodes) == 1, 'memory_runtime_negative_pe_source')
    guests = ast.literal_eval(nodes[0].value)
    controls = {'x64_control': ('libexec/pear-stage3/api-x64.exe', 0x8664, False),
                'i386_control': ('libexec/pear-stage3/api-i386.exe', 0x14c, False)}
    need(type(guests) is dict and all(encoded(guests.get(role)) == encoded(item) for role, item in controls.items()),
         'memory_runtime_negative_pe_source')
    selected_controls = {item[0]: item[1] for item in controls.values()}
    need(type(machine) is int, 'memory_runtime_ordinary_pe_machine')
    if row['path'] in selected_controls:
        need(row['origin']['role'] == 'baseline-native' and row['origin']['path'] == row['path']
             and machine == selected_controls[row['path']], 'memory_runtime_negative_pe_scope')
        return {'machine': machine, 'classification': 'retained_wrong_architecture_fixture',
                'load_admission': 'refused', 'execution_performed': False}
    need(machine == 0xaa64, 'memory_runtime_ordinary_pe_machine')
    return {'machine': machine, 'classification': 'ordinary_arm64_image',
            'load_admission': 'unperformed', 'execution_performed': False}


def source_ledger(root, baseline_install, install, manifest, old_manifest, reader, repo=REPO):
    observed = reader.inventory(install)
    files = {row['path']: row for row in observed if row['kind'] == 'file'}
    expected = {row['path']: row for row in manifest['files']}
    need(len(expected) == len(manifest['files']) and set(files) == set(expected), 'memory_runtime_install_set')
    for path, row in files.items():
        same({key: row[key] for key in ('path', 'sha256', 'size_bytes', 'mode')},
             {key: expected[path][key] for key in ('path', 'sha256', 'size_bytes', 'mode')},
             'memory_runtime_install_bytes')
    same([{'path': row['path'], 'target': row['target']} for row in observed if row['kind'] == 'symlink'],
         manifest['symlinks'], 'memory_runtime_install_aliases')
    old = {row['path']: row for row in old_manifest['files']}
    need(set(old) == set(expected), 'memory_runtime_overlay_set')
    replacements = {NTDLL, NTDLL_PE}
    metadata = None; result = []
    for original in observed:
        row = dict(original); path = row['path']
        row['runtime_path'] = MAIN if path == LOADER else PAYLOAD + '/' + path
        if row['kind'] == 'file':
            row['format_kind'] = expected[path]['kind']
            need(row['format_kind'] in ('macho', 'pe', 'data', 'pe_metadata'), 'memory_runtime_format')
            if row['format_kind'] == 'pe_metadata':
                need(path not in replacements, 'memory_runtime_metadata_scope')
                metadata = metadata or metadata_reader(repo)
                validate_metadata(install, path, path, expected[path], metadata)
            if path in replacements:
                origin = {'role': 'rebuilt-memory-ntdll', 'path': 'install/' + path, 'sha256': row['sha256']}
            else:
                same(expected[path], old[path], 'memory_runtime_overlay_scope')
                source = read_relative(baseline_install, path, 512 * 1024**2)
                need(digest_bytes(source) == row['sha256'], 'memory_runtime_baseline_bytes')
                origin = {'role': 'baseline-native', 'path': path, 'sha256': row['sha256']}
            row['origin'] = origin
        result.append(row)
    for path, origin_path, kind, role in [
        (LAUNCHER, 'fixtures/owner-launch', 'macho', 'fixture-launcher'),
        (FIXTURE, 'fixtures/wine-owner.exe', 'pe', 'fixture-pe')]:
        need(path not in files, 'memory_runtime_fixture_collision')
        raw = read_relative(root, origin_path, 64 * 1024**2)
        mode = stat.S_IMODE((root / origin_path).stat().st_mode)
        need(mode in (0o644, 0o700, 0o755) and (kind != 'macho' or mode & 0o111),
             'memory_runtime_fixture_mode')
        result.append({'path': path, 'kind': 'file', 'mode': mode, 'sha256': digest_bytes(raw),
            'size_bytes': len(raw), 'runtime_path': PAYLOAD + '/' + path, 'format_kind': kind,
            'origin': {'role': role, 'path': origin_path, 'sha256': digest_bytes(raw)}})
    added = 'libexec/pear-fex-memory'
    need(added not in {row['path'] for row in observed}, 'memory_runtime_directory_collision')
    result.append({'path': added, 'kind': 'directory', 'mode': 0o755, 'runtime_path': PAYLOAD + '/' + added})
    need({LOADER, NTDLL, NTDLL_PE, SERVER, SENTINEL, LAUNCHER, FIXTURE} <=
         {row['path'] for row in result if row['kind'] == 'file'}, 'memory_runtime_entrypoint_sources')
    return sorted(result, key=lambda row: row['path'])


def origin_file(row, baseline_install, root):
    origin = row['origin']; role = origin['role']
    need(role in ('baseline-native', 'rebuilt-memory-ntdll', 'fixture-launcher', 'fixture-pe'),
         'memory_runtime_origin_role')
    parent = baseline_install if role == 'baseline-native' else root
    raw = read_relative(parent, origin['path'], 512 * 1024**2)
    need(digest_bytes(raw) == origin['sha256'] == row['sha256'] and len(raw) == row['size_bytes'],
         'memory_runtime_origin_bytes')
    return parent / origin['path'], raw


def file_identity(info):
    return {'device': info.st_dev, 'inode': info.st_ino, 'size_bytes': info.st_size,
            'mode': stat.S_IMODE(info.st_mode), 'nlinks': info.st_nlink}


def descriptor_bytes(fd, limit):
    before = os.fstat(fd)
    need(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit, 'memory_runtime_copy_source')
    with os.fdopen(os.dup(fd), 'rb') as stream:
        stream.seek(0); raw = stream.read(limit + 1)
    after = os.fstat(fd)
    need(len(raw) == before.st_size and len(raw) <= limit
         and file_identity(before) == file_identity(after)
         and before.st_mtime_ns == after.st_mtime_ns and before.st_ctime_ns == after.st_ctime_ns,
         'memory_runtime_copy_changed')
    return raw


def copy_parent(root, name):
    parts = relative(name); fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            try: os.mkdir(part, mode=0o755, dir_fd=fd)
            except FileExistsError: pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = child
        return fd, parts[-1]
    except BaseException:
        os.close(fd); raise


def public_clone(source_fd, destination_parent_fd, destination_name):
    """Root-only public descriptor-based file clone; never a hard link."""
    need(platform.system() == 'Darwin', 'memory_runtime_clone_platform')
    library = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
    function = library.fclonefileat
    function.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
    function.restype = ctypes.c_int
    value = function(source_fd, destination_parent_fd, destination_name.encode('utf-8'), CLONE_FLAGS)
    if value != 0:
        raise OSError(ctypes.get_errno(), 'public fclonefileat failed')
    return value


def copy_payload(root, row, baseline_install, built_root, helpers, prefer_clone=False):
    parent = baseline_install if row['origin']['role'] == 'baseline-native' else built_root
    source_fd = open_relative(parent, row['origin']['path']); destination_fd = None; parent_fd = None
    try:
        original = os.fstat(source_fd); donor = file_identity(original)
        raw = descriptor_bytes(source_fd, 512 * 1024**2)
        need(digest_bytes(raw) == row['sha256'] == row['origin']['sha256'] and len(raw) == row['size_bytes']
             and donor['mode'] == row['mode'], 'memory_runtime_copy_origin')
        parent_fd, leaf = copy_parent(root, row['runtime_path'])
        try: os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError: pass
        else: raise Error('memory_runtime_copy_destination_exists')
        result = {'status': 'unperformed', 'return_value': None, 'native_error': None}; method = 'byte_copy'
        if prefer_clone:
            try:
                code = public_clone(source_fd, parent_fd, leaf)
                need(type(code) is int and code == 0, 'memory_runtime_clone_return')
                method = 'public_fclonefileat'
                result = {'status': 'completed', 'return_value': code, 'native_error': None}
            except OSError as exc:
                if exc.errno not in CLONE_FALLBACK: raise
                result = {'status': 'failed', 'return_value': -1,
                          'native_error': {'domain': 'POSIX', 'code': exc.errno}}
                # Atomic clone failure must leave no destination. Never replace
                # a partially created or caller-controlled output on fallback.
                try: os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
                except FileNotFoundError: pass
                else:
                    failure = Error('memory_runtime_clone_failed_output')
                    failure.native_error = {'domain': 'POSIX', 'code': exc.errno,
                                            'exception_type': type(exc).__name__}
                    raise failure from exc
        if method == 'byte_copy':
            helpers.stage3.write_bytes(root, row['runtime_path'], raw, row['mode'])
        destination_fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent_fd)
        copied_before = os.fstat(destination_fd)
        need(stat.S_ISREG(copied_before.st_mode) and copied_before.st_nlink == 1
             and (copied_before.st_dev, copied_before.st_ino) != (original.st_dev, original.st_ino),
             'memory_runtime_copy_independence')
        os.fchmod(destination_fd, row['mode'])
        need(descriptor_bytes(destination_fd, 512 * 1024**2) == raw,
             'memory_runtime_copy_bytes')
        copied = file_identity(os.fstat(destination_fd))
        need(copied['mode'] == row['mode'] and copied['size_bytes'] == row['size_bytes'],
             'memory_runtime_copy_mode')
        need(file_identity(os.fstat(source_fd)) == donor
             and original.st_mtime_ns == os.fstat(source_fd).st_mtime_ns
             and original.st_ctime_ns == os.fstat(source_fd).st_ctime_ns
             and descriptor_bytes(source_fd, 512 * 1024**2) == raw,
             'memory_runtime_copy_source_changed')
        current_fd = open_relative(parent, row['origin']['path'])
        try:
            need(file_identity(os.fstat(current_fd)) == donor
                 and descriptor_bytes(current_fd, 512 * 1024**2) == raw,
                 'memory_runtime_copy_source_changed')
        finally: os.close(current_fd)
        return {'path': row['runtime_path'], 'method': method, 'clone_result': result,
                'donor': donor, 'copied': copied}
    finally:
        if destination_fd is not None: os.close(destination_fd)
        if parent_fd is not None: os.close(parent_fd)
        os.close(source_fd)


def copy_policy():
    return {'public_clone_preferred': True, 'public_api': 'fclonefileat', 'flags': CLONE_FLAGS,
            'fallback_errno_codes': sorted(CLONE_FALLBACK), 'hard_links_allowed': False}


def copy_counts(copies):
    return {method: sum(row['method'] == method for row in copies)
            for method in ('public_fclonefileat', 'byte_copy')}


def verify_copies(root, ledger, baseline_install, built_root, copies):
    selected_files = {row['runtime_path']: row for row in ledger if row['kind'] == 'file'}
    need(type(copies) is list and [row.get('path') for row in copies] == list(selected_files),
         'memory_runtime_copy_set')
    for value in copies:
        fields(value, ('path', 'method', 'clone_result', 'donor', 'copied'))
        row = selected_files[value['path']]
        for key in ('donor', 'copied'):
            facts = value[key]; fields(facts, ('device', 'inode', 'size_bytes', 'mode', 'nlinks'))
            need(all(type(item) is int and item >= 0 for item in facts.values())
                 and facts['size_bytes'] == row['size_bytes'] and facts['mode'] == row['mode']
                 and facts['inode'] > 0 and facts['nlinks'] > 0, 'memory_runtime_copy_stat')
        result = value['clone_result']; fields(result, ('status', 'return_value', 'native_error'))
        if value['method'] == 'public_fclonefileat':
            need(result['status'] == 'completed' and type(result['return_value']) is int
                 and result['return_value'] == 0 and result['native_error'] is None,
                 'memory_runtime_copy_method')
        else:
            need(value['method'] == 'byte_copy' and result['status'] == 'failed'
                 and type(result['return_value']) is int and result['return_value'] == -1,
                 'memory_runtime_copy_method')
            fields(result['native_error'], ('domain', 'code'))
            need(result['native_error']['domain'] == 'POSIX' and type(result['native_error']['code']) is int
                 and result['native_error']['code'] in CLONE_FALLBACK, 'memory_runtime_copy_fallback')
        parent = baseline_install if row['origin']['role'] == 'baseline-native' else built_root
        donor_fd = open_relative(parent, row['origin']['path']); current_fd = None
        try:
            current_fd = open_relative(root, row['runtime_path'])
            donor = file_identity(os.fstat(donor_fd)); current = file_identity(os.fstat(current_fd))
            same(value['donor'], donor, 'memory_runtime_copy_source_changed')
            need(value['copied']['nlinks'] == 1 and current['nlinks'] == 1
                 and (value['copied']['device'], value['copied']['inode']) != (donor['device'], donor['inode'])
                 and (current['device'], current['inode']) != (donor['device'], donor['inode'])
                 and current['mode'] == row['mode'], 'memory_runtime_copy_independence')
            # Signing may replace the destination inode and append signature
            # bytes. Code-origin and signed payload byte proof is separate;
            # the donor remains unchanged and each current image independent.
            need(digest_bytes(descriptor_bytes(donor_fd, 512 * 1024**2)) == row['sha256'],
                 'memory_runtime_copy_source_changed')
        finally:
            if current_fd is not None: os.close(current_fd)
            os.close(donor_fd)
    return copies


def materialize(root, ledger, baseline_install, built_root, raw_profile, helpers, prefer_clone=False):
    copies = []
    for row in ledger:
        path = root / row['runtime_path']
        if row['kind'] == 'directory':
            path.mkdir(parents=True, exist_ok=True, mode=row['mode']); path.chmod(row['mode'])
        elif row['kind'] == 'file':
            copies.append(copy_payload(root, row, baseline_install, built_root, helpers, prefer_clone=prefer_clone))
    for row in ledger:
        if row['kind'] == 'symlink':
            path = root / row['runtime_path']; path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(row['target'])
    original = root / PAYLOAD / LOADER
    original.symlink_to(os.path.relpath(root / MAIN, original.parent))
    alias = root / NTDLL_ALIAS; alias.symlink_to(os.path.relpath(root / PAYLOAD / NTDLL, alias.parent))
    helpers.stage3.write_bytes(root, BUNDLE + '/Contents/embedded.provisionprofile', raw_profile, 0o600)
    helpers.stage3.write_bytes(root, BUNDLE + '/Contents/Info.plist', plistlib.dumps(INFO), 0o644)
    return copies


def entrypoints():
    return {'loader': MAIN, 'server': PAYLOAD + '/' + SERVER, 'bootstrap_helper': PAYLOAD + '/' + LAUNCHER,
        'sentinel': PAYLOAD + '/' + SENTINEL, 'fixture_pe': PAYLOAD + '/' + FIXTURE,
        'ntdll_native': PAYLOAD + '/' + NTDLL, 'ntdll_pe': PAYLOAD + '/' + NTDLL_PE}


def inventory_images(root, ledger, baseline_install, build_root, reader, helpers, repo=REPO):
    natives = []; pes = []; closures = []; metadata = None
    names = {BUNDLE + '/' + row['path'] for row in reader.inventory(root / BUNDLE)}
    expected = {row['runtime_path'] for row in ledger}
    expected |= {PAYLOAD + '/' + LOADER, NTDLL_ALIAS,
                 BUNDLE + '/Contents/embedded.provisionprofile', BUNDLE + '/Contents/Info.plist'}
    parents = {BUNDLE + '/Contents', BUNDLE + '/Contents/MacOS', BUNDLE + '/Contents/Resources', PAYLOAD}
    seal = {BUNDLE + '/Contents/_CodeSignature', BUNDLE + '/Contents/_CodeSignature/CodeResources'}
    need(expected <= names and names - expected - parents <= seal, 'memory_runtime_payload_set')
    for row in ledger:
        path = root / row['runtime_path']
        if row['kind'] == 'directory':
            need(path.is_dir() and not path.is_symlink() and stat.S_IMODE(path.stat().st_mode) == row['mode'],
                 'memory_runtime_directory_changed'); continue
        if row['kind'] == 'symlink':
            need(path.is_symlink() and os.readlink(path) == row['target'], 'memory_runtime_alias_changed'); continue
        raw = read_relative(root, row['runtime_path'], 512 * 1024**2)
        need(stat.S_IMODE(path.stat().st_mode) == row['mode'], 'memory_runtime_file_mode')
        origin, source = origin_file(row, baseline_install, build_root)
        if row['format_kind'] == 'macho':
            need(source[:4] == b'\xcf\xfa\xed\xfe', 'memory_runtime_native_format')
            reader.verify_code_origin(origin, path)
            info = byte_readers.inspect_macho(path)
            need(info['architectures'] == [byte_readers.MACH_ARM64] and info['filetype'] in (2, 6, 8),
                 'memory_runtime_native_target')
            closure = byte_readers.inspect_closure(path, root / BUNDLE)
            need(all(item['architectures'] == [byte_readers.MACH_ARM64]
                     and item['selected_cpu'] == byte_readers.MACH_ARM64 for item in closure),
                 'memory_runtime_dependency_target')
            natives.append({'path': row['runtime_path'], 'sha256': digest_bytes(raw), 'size_bytes': len(raw),
                'origin': row['origin'], 'code_origin': {'scope': 'macho_signature_fields_only', 'verified': True},
                'signature': None})
            closures.append({'path': row['runtime_path'], 'images': closure})
        else:
            need(raw == source, 'memory_runtime_data_changed')
            if row['format_kind'] == 'pe_metadata':
                need(row['origin']['role'] == 'baseline-native', 'memory_runtime_metadata_scope')
                metadata = metadata or metadata_reader(repo)
                facts = metadata.inspect_winmd(origin)
                validate_metadata(root, row['runtime_path'], row['path'],
                    {'kind': 'pe_metadata', **facts}, metadata)
            if row['format_kind'] == 'pe':
                scope = pe_scope(row, helpers.pe_machine(source), repo)
                pes.append({'path': row['runtime_path'], 'sha256': digest_bytes(raw), 'size_bytes': len(raw),
                            'origin': row['origin'], **scope})
    for path, target in [(PAYLOAD + '/' + LOADER, os.path.relpath(root / MAIN, (root / PAYLOAD / LOADER).parent)),
                         (NTDLL_ALIAS, os.path.relpath(root / PAYLOAD / NTDLL, (root / NTDLL_ALIAS).parent))]:
        need((root / path).is_symlink() and os.readlink(root / path) == target, 'memory_runtime_owned_alias')
    need(sum(row['origin']['role'] == 'rebuilt-memory-ntdll' and row['origin']['path'] == 'install/' + NTDLL
             for row in natives) == 1, 'memory_runtime_ntdll_unique')
    return sorted(natives, key=lambda row: row['path']), sorted(pes, key=lambda row: row['path']), closures


def reuse_record(root):
    return {'root': str(root), 'source_sha256': dict(REUSE_PINS),
            'selected_functions': {path: list(names) for path, names in REUSE_NAMES.items()},
            'scope': 'reviewed_signing_receipt_helpers_only'}


def capture_sources(root, current, reuse_root, captured, helpers, repo=REPO):
    for path, pin in current.items():
        raw = read_relative(repo, path); need(digest_bytes(raw) == pin, 'memory_runtime_producer_changed')
        helpers.stage3.write_bytes(root, 'producers/' + path, raw)
    for path, raw in captured.items():
        helpers.stage3.write_bytes(root, 'signing-reuse/' + path, raw)


def materialization_record(build_root, baseline_root, baseline, ledger, copies):
    return {'schema_version': 1, 'record_kind': 'fex_memory_wine_materialization', 'scope': SCOPE,
        'build_ref': {'path': str(build_root), 'sha256': sha256(build_root / 'build.json')},
        'baseline_ref': {'path': str(baseline_root), 'sha256': sha256(baseline_root / 'build.json')},
        'baseline_manifest': baseline['artifacts_manifest'], 'source_ledger': ledger, 'entrypoints': entrypoints(),
        'baseline_loader_capacity': baseline['arena_capacity'], 'capacity_scope': 'retained_source_bound_loader_only',
        'copy_policy': copy_policy(), 'copies': copies, 'copy_methods': copy_counts(copies),
        'signing_performed': False, 'execution_performed': False}


def failure_detail(exc):
    if isinstance(exc, OSError):
        return {'domain': 'POSIX', 'code': exc.errno if type(exc.errno) is int else None,
                'exception_type': type(exc).__name__}
    return getattr(exc, 'native_error', None)


def preserve_failure(root, kind, phase, exc, commands, authorization_commands):
    value = {'schema_version': 1, 'record_kind': kind, 'scope': SCOPE, 'phase': phase,
        'error': getattr(exc, 'code', 'memory_runtime_operation'), 'native_error': failure_detail(exc),
        'exception_type': type(exc).__name__, 'commands': commands, 'authorization_commands': authorization_commands,
        'passed': False, 'runtime_eligible': False, **{key: False for key in FALSE_FLAGS}}
    try: write_json(root / 'failed.json', value)
    except BaseException as secondary:
        # The first exception always remains the thrown operation failure.
        exc.evidence_write_error = failure_detail(secondary) or {'exception_type': type(secondary).__name__}


def prepare(build_root, profile_path, output, signing_reuse_root, repo=REPO):
    root = operation_output(output, repo_root=repo, require_empty=True)
    root.chmod(0o700); commands = []; authorization_commands = []; phase = 'build_replay'
    try:
        build_root = operation_output(build_root, repo_root=repo, require_empty=False, create=False)
        _, baseline_root, baseline, baseline_install, install, manifest, old = prerequisite(build_root, repo)
        phase = 'signing_source_replay'; helpers, captured = signing_helpers(signing_reuse_root, repo)
        reader = helpers.legacy(repo)
        ledger = source_ledger(build_root, baseline_install, install, manifest, old, reader, repo=repo)
        need(__import__('shutil').disk_usage(repo).free >= sum(row.get('size_bytes', 0) for row in ledger) + RESERVE,
             'memory_runtime_storage_admission')
        current = producers(repo); capture_sources(root, current, signing_reuse_root, captured, helpers, repo)
        phase = 'authorization'
        authorization, private, raw_profile = helpers.capture_authorization(profile_path, root, reader, authorization_commands)
        phase = 'materialization'
        copies = materialize(root, ledger, baseline_install, build_root, raw_profile, helpers, prefer_clone=True)
        write_json(root / 'materialization.json', materialization_record(build_root, baseline_root, baseline, ledger, copies))
        helpers.stage3.write_bytes(root, 'authorized-entitlements.plist', plistlib.dumps(authorization['claims']), 0o600)
        images, _, _ = inventory_images(root, ledger, baseline_install, build_root, reader, helpers, repo=repo)
        phase = 'signing'
        for ident, argv in helpers.signing_recipe(root, images, private['identity']):
            helpers.native(argv, root, ident, commands)
        phase = 'signed_byte_replay'
        images, pes, closures = inventory_images(root, ledger, baseline_install, build_root, reader, helpers, repo=repo)
        logs = helpers.verify_commands(root, commands, helpers.signing_recipe(root, images, private['identity']))
        signed_images = helpers.signatures_from_logs(root, images, logs, authorization['claims'], private, reader, raw_profile)
        need(read_relative(root, BUNDLE + '/Contents/embedded.provisionprofile', LIMIT) == raw_profile,
             'memory_runtime_embedded_profile_changed')
        signed = {'schema_version': 1, 'record_kind': 'fex_memory_wine_signed_runtime', 'scope': SCOPE,
            'materialization_ref': {'path': 'materialization.json', 'sha256': sha256(root / 'materialization.json')},
            'commands': commands, 'native_dependency_closure': closures, 'bundle_inventory': reader.inventory(root / BUNDLE),
            'passed': True, 'execution_performed': False, 'runtime_eligible': False, 'distribution_qualified': False}
        write_json(root / 'signed.json', signed)
        runtime = {'schema_version': 1, 'record_kind': 'fex_memory_wine_runtime', 'scope': 'fex_component',
            'build_ref': {'path': str(build_root), 'sha256': sha256(build_root / 'build.json')},
            'signing_reuse': reuse_record(builder.real_directory(signing_reuse_root)), 'producers': current,
            'native_images': signed_images, 'pe_images': pes, 'entrypoints': entrypoints(),
            'authorization': {'path': 'authorization.json', 'sha256': sha256(root / 'authorization.json')},
            'signed_receipt': {'path': 'signed.json', 'sha256': sha256(root / 'signed.json')},
            'baseline_loader_capacity': baseline['arena_capacity'], 'code_publication_policy': 'page-wx',
            'runtime_eligible': False, **{key: False for key in FALSE_FLAGS}}
        same(producers(repo), current, 'memory_runtime_producer_changed')
        write_json(root / 'runtime.json', runtime)
        phase = 'current_admission'; return verify_runtime(root, repo=repo)
    except BaseException as exc:
        preserve_failure(root, 'fex_memory_wine_runtime_failure', phase, exc, commands, authorization_commands)
        raise


def snapshot_set(root, prefix, expected):
    parent = builder.real_directory(root / prefix); actual = set()
    for directory, dirs, names in os.walk(parent, followlinks=False):
        for name in dirs:
            info = (Path(directory) / name).lstat()
            need(stat.S_ISDIR(info.st_mode), 'memory_runtime_snapshot_directory')
        for name in names:
            path = Path(directory) / name; info = path.lstat()
            need(stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o644,
                 'memory_runtime_snapshot_file')
            actual.add(path.relative_to(parent).as_posix())
            need(len(actual) <= 256, 'memory_runtime_snapshot_limit')
    need(actual == set(expected), 'memory_runtime_snapshot_set')


def verify_structural(root, repo=REPO):
    """Replay bytes/authorization/signing receipts only; never call native tools."""
    root = operation_output(root, repo_root=repo, require_empty=False, create=False)
    need(not (root / 'failed.json').exists(), 'memory_runtime_failed')
    runtime = load_json(root / 'runtime.json'); fields(runtime, RUNTIME_FIELDS, 'fex_memory_wine_runtime')
    need(runtime['scope'] == 'fex_component' and runtime['code_publication_policy'] == 'page-wx'
         and runtime['runtime_eligible'] is False and all(runtime[key] is False for key in FALSE_FLAGS),
         'memory_runtime_scope')
    fields(runtime['signing_reuse'], ('root', 'source_sha256', 'selected_functions', 'scope'))
    same(runtime['signing_reuse'], reuse_record(builder.real_directory(runtime['signing_reuse']['root'])),
         'memory_runtime_reuse_record')
    helpers, captured = signing_helpers(runtime['signing_reuse']['root'], repo)
    current = producers(repo); same(runtime['producers'], current, 'memory_runtime_producer_changed')
    for path, pin in current.items():
        need(digest_bytes(read_relative(root, 'producers/' + path)) == pin, 'memory_runtime_producer_snapshot')
    for path, raw in captured.items():
        need(read_relative(root, 'signing-reuse/' + path, LIMIT) == raw, 'memory_runtime_reuse_snapshot')
    snapshot_set(root, 'producers', current)
    snapshot_set(root, 'signing-reuse', captured)
    reader = helpers.legacy(repo)
    fields(runtime['build_ref'], ('path', 'sha256'))
    built_root = operation_output(runtime['build_ref']['path'], repo_root=repo, require_empty=False, create=False)
    need(sha256(built_root / 'build.json') == runtime['build_ref']['sha256'], 'memory_runtime_build_changed')
    _, baseline_root, baseline, baseline_install, install, manifest, old = prerequisite(built_root, repo)
    ledger = source_ledger(built_root, baseline_install, install, manifest, old, reader, repo=repo)
    for key, name in [('authorization', 'authorization.json'), ('signed_receipt', 'signed.json')]:
        fields(runtime[key], ('path', 'sha256')); need(runtime[key]['path'] == name
             and sha256(root / name) == runtime[key]['sha256'], 'memory_runtime_receipt_changed')
    authorization = load_json(root / 'authorization.json')
    private, raw_profile = helpers.verify_authorization(root, authorization, reader)
    same(read_relative(root, BUNDLE + '/Contents/embedded.provisionprofile', LIMIT), raw_profile,
         'memory_runtime_embedded_profile_changed')
    need(stat.S_IMODE((root / BUNDLE / 'Contents/embedded.provisionprofile').stat().st_mode) == 0o600,
         'memory_runtime_private_profile_mode')
    same(plistlib.loads(read_relative(root, 'authorized-entitlements.plist', LIMIT)), authorization['claims'],
         'memory_runtime_claims_changed')
    need(stat.S_IMODE((root / 'authorized-entitlements.plist').stat().st_mode) == 0o600,
         'memory_runtime_private_claims_mode')
    signed = load_json(root / 'signed.json')
    fields(signed, ('schema_version', 'record_kind', 'scope', 'materialization_ref', 'commands',
        'native_dependency_closure', 'bundle_inventory', 'passed', 'execution_performed', 'runtime_eligible',
        'distribution_qualified'), 'fex_memory_wine_signed_runtime')
    need(signed['scope'] == SCOPE and signed['passed'] is True and all(signed[key] is False for key in
         ('execution_performed', 'runtime_eligible', 'distribution_qualified')), 'memory_runtime_signed_scope')
    fields(signed['materialization_ref'], ('path', 'sha256'))
    need(signed['materialization_ref']['path'] == 'materialization.json'
         and sha256(root / 'materialization.json') == signed['materialization_ref']['sha256'],
         'memory_runtime_materialization_changed')
    materialized = load_json(root / 'materialization.json')
    copies = verify_copies(root, ledger, baseline_install, built_root, materialized.get('copies'))
    same(materialized, materialization_record(built_root, baseline_root, baseline, ledger, copies),
         'memory_runtime_materialization_derivation')
    images, pes, closures = inventory_images(root, ledger, baseline_install, built_root, reader, helpers, repo=repo)
    logs = helpers.verify_commands(root, signed['commands'], helpers.signing_recipe(root, images, private['identity']))
    natives = helpers.signatures_from_logs(root, images, logs, authorization['claims'], private, reader, raw_profile)
    same(natives, runtime['native_images'], 'memory_runtime_signed_images')
    same(pes, runtime['pe_images'], 'memory_runtime_pe_images')
    same(closures, signed['native_dependency_closure'], 'memory_runtime_dependency_closure')
    same(reader.inventory(root / BUNDLE), signed['bundle_inventory'], 'memory_runtime_signed_inventory')
    same(runtime['entrypoints'], entrypoints(), 'memory_runtime_entrypoints')
    same(runtime['baseline_loader_capacity'], baseline['arena_capacity'], 'memory_runtime_capacity_scope')
    same(plistlib.loads(read_relative(root, BUNDLE + '/Contents/Info.plist', LIMIT)), INFO, 'memory_runtime_bundle_identity')
    need(stat.S_IMODE((root / BUNDLE / 'Contents/Info.plist').stat().st_mode) == 0o644, 'memory_runtime_bundle_info_mode')
    same(producers(repo), current, 'memory_runtime_producer_changed_during_replay')
    return runtime, private, raw_profile


def admission_recipe(root, runtime, helpers):
    recipe = helpers.profile_recipe(root)
    for index, row in enumerate(runtime['native_images']):
        recipe.extend(helpers.signature_recipe(root.parents[1] / row['path'], 'current.' + str(index), root))
    recipe.extend(helpers.signature_recipe(root.parents[1] / BUNDLE, 'current.bundle', root))
    return recipe


def admission_directory(root, value):
    """Admit one explicit owned receipt, never select the newest directory."""
    root = builder.real_directory(root)
    directory = builder.real_directory(value)
    need(directory.parent == root / 'admission'
         and re.fullmatch('[0-9a-f]{32}', directory.name) is not None,
         'memory_runtime_admission_path')
    need(stat.S_IMODE(directory.stat().st_mode) == 0o700
         and not (directory / 'failed.json').exists(), 'memory_runtime_admission_failed')
    return directory


def admission_observations(root, directory, runtime, original, raw_profile, commands, helpers, repo):
    """Pure exact command/log/current-profile/signer-leaf replay."""
    reader = helpers.legacy(repo)
    need(read_relative(directory, 'captured-profile.provisionprofile', LIMIT) == raw_profile
         and stat.S_IMODE((directory / 'captured-profile.provisionprofile').stat().st_mode) == 0o600,
         'memory_runtime_current_profile_changed')
    logs = helpers.verify_commands(directory, commands, admission_recipe(directory, runtime, helpers))
    current = helpers.profile_from_logs(raw_profile, logs, reader)
    same(current['claims'], original['claims'], 'memory_runtime_current_profile_claims')
    need(current['identity'] == original['identity'], 'memory_runtime_current_identity')
    claims = reader.loader_claims(current, 'page-wx')
    for index, row in enumerate(runtime['native_images']):
        restricted = row['path'] == MAIN; ident = 'current.' + str(index)
        observed = helpers.signature_from_logs(logs, ident, claims if restricted else {}, current, reader,
            BUNDLE_ID if restricted else BUNDLE_ID + '.native.' + str(index))
        helpers.signer_leaf(directory, ident, current, raw_profile)
        same(observed, row['signature'], 'memory_runtime_current_signature')
    helpers.signature_from_logs(logs, 'current.bundle', claims, current, reader, BUNDLE_ID)
    helpers.signer_leaf(directory, 'current.bundle', current, raw_profile)
    need(read_relative(root, BUNDLE + '/Contents/embedded.provisionprofile', LIMIT) == raw_profile,
         'memory_runtime_current_profile_changed')
    return current


def verify_admission(root, admission_root, repo=REPO):
    """Pure replay of one selected receipt; no new Apple admission or execution."""
    root = operation_output(root, repo_root=repo, require_empty=False, create=False)
    runtime, original, raw_profile = verify_structural(root, repo=repo)
    directory = admission_directory(root, admission_root)
    value = load_json(directory / 'admission.json')
    fields(value, ('schema_version', 'record_kind', 'scope', 'runtime_ref', 'profile_sha256',
        'commands', 'current_checks', 'passed', 'execution_performed', 'runtime_eligible',
        'distribution_qualified'), 'fex_memory_wine_admission')
    need(value['scope'] == SCOPE and value['passed'] is True and all(value[key] is False for key in
         ('execution_performed', 'runtime_eligible', 'distribution_qualified')), 'memory_runtime_admission_scope')
    fields(value['runtime_ref'], ('path', 'sha256'))
    same(value['runtime_ref'], {'path': str(root), 'sha256': sha256(root / 'runtime.json')},
         'memory_runtime_admission_runtime_changed')
    need(value['profile_sha256'] == digest_bytes(raw_profile), 'memory_runtime_admission_profile_changed')
    helpers, _ = signing_helpers(runtime['signing_reuse']['root'], repo)
    current = admission_observations(root, directory, runtime, original, raw_profile, value['commands'], helpers, repo)
    same(current['checks'], value['current_checks'], 'memory_runtime_admission_checks_changed')
    repeated, _, _ = verify_structural(root, repo=repo)
    same(repeated, runtime, 'memory_runtime_changed_during_admission')
    return value


def admit_runtime(root, repo=REPO):
    """Root-only fresh Apple admission, returning its exact owned receipt path."""
    root = operation_output(root, repo_root=repo, require_empty=False, create=False)
    runtime, original, raw_profile = verify_structural(root, repo=repo)
    helpers, _ = signing_helpers(runtime['signing_reuse']['root'], repo)
    directory = root / 'admission' / uuid.uuid4().hex; directory.mkdir(parents=True, mode=0o700)
    commands = []; phase = 'current_profile_capture'
    try:
        helpers.stage3.write_bytes(directory, 'captured-profile.provisionprofile', raw_profile, 0o600)
        recipe = admission_recipe(directory, runtime, helpers)
        phase = 'current_apple_admission'
        for ident, argv in recipe: helpers.native(argv, directory, ident, commands)
        current = admission_observations(root, directory, runtime, original, raw_profile, commands, helpers, repo)
        repeated, _, _ = verify_structural(root, repo=repo); same(repeated, runtime, 'memory_runtime_changed_during_admission')
        write_json(directory / 'admission.json', {'schema_version': 1, 'record_kind': 'fex_memory_wine_admission',
            'scope': SCOPE, 'runtime_ref': {'path': str(root), 'sha256': sha256(root / 'runtime.json')},
            'profile_sha256': digest_bytes(raw_profile), 'commands': commands, 'current_checks': current['checks'],
            'passed': True, 'execution_performed': False, 'runtime_eligible': False, 'distribution_qualified': False})
        verify_admission(root, directory, repo=repo)
        return runtime, directory
    except BaseException as exc:
        preserve_failure(directory, 'fex_memory_wine_admission_failure', phase, exc, commands, [])
        raise


def verify_runtime(root, repo=REPO):
    """Compatibility wrapper: fresh Apple admission, no Wine/owner execution."""
    runtime, _ = admit_runtime(root, repo=repo)
    return runtime


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', required=True); parser.add_argument('--profile', required=True)
    parser.add_argument('--signing-reuse-root', required=True); parser.add_argument('--output', required=True)
    parser.add_argument('--require-empty', required=True, action='store_true'); args = parser.parse_args(argv)
    try:
        runtime = prepare(args.artifact, args.profile, args.output, args.signing_reuse_root)
        print(encoded({'development_admission': 'passed', 'native_images': len(runtime['native_images']),
            'pe_images': len(runtime['pe_images']), 'execution_performed': False, 'runtime_eligible': False}).decode(), end='')
        return 0
    except (Error, OSError, ValueError, KeyError, TypeError, struct.error, NameError, AttributeError) as exc:
        print(encoded({'development_admission': 'failed', 'error': getattr(exc, 'code', 'memory_runtime_failed'),
            'exception_type': type(exc).__name__, 'execution_performed': False, 'runtime_eligible': False}).decode(), end='', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
