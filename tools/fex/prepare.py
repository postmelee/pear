#!/usr/bin/env python3
"""Prepare selected FEX sources from read-only caches without executing source.

Reuses Wine's bounded Git archive/data validation algorithms with an explicit
FEX gitlink mount closure. Caller-owned storage must not mutate concurrently;
these checks are not an atomic snapshot of hostile storage or build approval.
"""
from __future__ import annotations

import argparse
import configparser
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import time
import unicodedata

if __package__:
    from .common import (Error, REPO, decode_json, digest_bytes, encoded, load_json, need,
                         open_relative, operation_output, read_relative, record, relative, sha256, write_json)
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from common import (Error, REPO, decode_json, digest_bytes, encoded, load_json, need,
                        open_relative, operation_output, read_relative, record, relative, sha256, write_json)

_spec = importlib.util.spec_from_file_location('pear_fex_source_audit', REPO / 'tools/sources/validate_inventory.py')
_audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_audit)
MAX_MEMBERS = 100000
MAX_ARCHIVE = MAX_CONTENT = 2 * 1024 * 1024 * 1024
MAX_MEMBER = 128 * 1024 * 1024
GIT_TIMEOUT = 120
SELECTED = {'fex-upstream', 'fex-cpp-optparse', 'fex-fmt', 'fex-range-v3',
            'fex-rpmalloc', 'fex-unordered_dense', 'fex-xxhash'}
REQUIREMENTS = {'CMakeLists.txt', 'Source/Common/CMakeLists.txt', 'Source/Windows/CMakeLists.txt',
                'FEXCore/CMakeLists.txt', 'Source/Windows/ARM64EC/CMakeLists.txt',
                'Source/Windows/WOW64/CMakeLists.txt', 'Source/Windows/UnixLib/CMakeLists.txt',
                'Data/CMake/toolchain_mingw.cmake', 'FEXCore/Source/Interface/Config/Config.json.in'}
INTERFACES = {'Source/Windows/UnixLib/FEXUnixLib.h', 'Source/Windows/UnixLib/FEXUnixLib.cpp',
              'Source/Windows/Common/FEXUnixLib.cpp', 'Source/Windows/Common/TSOHandlerConfig.h',
              'Source/Windows/Common/CPUFeatures.cpp', 'Source/Windows/ARM64EC/Module.cpp',
              'Source/Windows/ARM64EC/Module.S', 'Source/Windows/ARM64EC/libarm64ecfex.def',
              'Source/Windows/WOW64/libwow64fex.def', 'FEXCore/include/FEXCore/Utils/AllocatorHooks.h'}
BASELINE_SERIES = '39371f21f25cf153437fd523951be9f938cc1161bed5c4ef923583c74c89d086'
BASELINE_SOURCE = '2c0c861669f9fd8853f8899eaeb08b18207b0cf26b34dae9efe707919e447bc7'


def oid(value, length=40):
    need(isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', value), 'invalid_digest')
    return value


def reference(value):
    need(isinstance(value, dict) and set(value) == {'path', 'sha256'}, 'reference_fields')
    relative(value['path']); oid(value['sha256'], 64)
    return value


def validate_inputs(value, repo_root=REPO):
    record(value, 'fex_build_inputs')
    need(set(value) == {'schema_version', 'record_kind', 'scope', 'audit_ref', 'baseline_ref',
                       'components', 'mounts', 'terms', 'source_requirements', 'interface_sources'}, 'input_fields')
    need(value['scope'] == 'fex_component', 'input_scope')
    audit_ref = reference(value['audit_ref'])
    raw = read_relative(repo_root, audit_ref['path'])
    need(digest_bytes(raw) == audit_ref['sha256'], 'audit_digest_mismatch')
    audit = record(decode_json(raw), 'source_audit')
    baseline = value['baseline_ref']
    need(isinstance(baseline, dict) and set(baseline) == {'wine_commit', 'wine_tree', 'series_ref',
                'materialized_source_manifest_sha256'}, 'baseline_fields')
    need(baseline['wine_commit'] == '4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf'
         and baseline['wine_tree'] == '10b47b2965a7b3e1e9694ec506a3d13525211892'
         and baseline['materialized_source_manifest_sha256'] == BASELINE_SOURCE, 'baseline_identity')
    series = reference(baseline['series_ref'])
    need(series['path'] == 'runtime/wine/patches/series.json' and series['sha256'] == BASELINE_SERIES
         and digest_bytes(read_relative(repo_root, series['path'])) == BASELINE_SERIES, 'baseline_series_identity')
    components = value['components']
    need(isinstance(components, list) and len(components) == len(SELECTED), 'component_count')
    by_id, audit_ids = {}, {c['component_id']: c for c in audit['components']}
    for c in components:
        need(isinstance(c, dict) and set(c) == {'id', 'audit_component_id', 'commit', 'tree',
                    'cache_path', 'url', 'listing_ref'}, 'component_fields')
        cid = c['id']; need(cid in SELECTED and cid not in by_id and c['audit_component_id'] == cid, 'component_identity')
        a = audit_ids[cid]; s = a['source']; d = next(d for d in a['content_digests'] if d['scope'] == 'git_tree_listing_bytes')
        oid(c['commit']); oid(c['tree']); relative(c['cache_path']); reference(c['listing_ref'])
        need(s['kind'] == 'git' and s['object_format'] == 'sha1' and a['acquisition']['status'] == 'acquired'
             and (c['commit'], c['tree'], c['cache_path'], c['url']) ==
             (s['commit_object_id'], s['tree_object_id'], a['acquisition']['cache_path'], s['url'])
             and c['listing_ref'] == {'path': d['cache_path'], 'sha256': d['value']}, 'component_audit_mismatch')
        by_id[cid] = c
    need(set(by_id) == SELECTED, 'component_closure')
    expected_mounts = []
    for d in audit['dependencies']:
        if d.get('parent') in SELECTED and d.get('relationship') == 'git_submodule':
            enabled = d['dependency'] in SELECTED
            expected_mounts.append({'parent': d['parent'], 'component': d['dependency'] if enabled else None,
                'path': d['path'], 'commit': d['declared_commit_object_id'],
                'status': 'enabled' if enabled else 'excluded', 'condition': d['condition']})
    need(value['mounts'] == expected_mounts, 'mount_closure')
    for name in ('terms', 'source_requirements', 'interface_sources'):
        rows = value[name]; need(isinstance(rows, list) and 0 < len(rows) <= 64, 'source_reference_list')
        seen = set()
        for r in rows:
            need(isinstance(r, dict) and set(r) == {'component', 'path', 'sha256', 'git_blob'} |
                 ({'role'} if name == 'terms' else set()), 'source_reference_fields')
            relative(r['path']); oid(r['sha256'], 64); oid(r['git_blob'])
            key = r['component'], r['path']; need(r['component'] in SELECTED and key not in seen, 'source_reference_identity')
            seen.add(key)
            if name == 'terms': need(r['role'] in ('notice', 'contribution_policy'), 'terms_role')
        if name != 'terms':
            need(seen == {('fex-upstream', p) for p in (REQUIREMENTS if name == 'source_requirements' else INTERFACES)},
                 'source_reference_closure')
        else:
            need(all(any(r['component'] == cid and r['role'] == 'notice' for r in rows) for cid in SELECTED), 'terms_closure')
            need({('fex-upstream', 'AGENTS.md'), ('fex-upstream', 'CONTRIBUTING.md'),
                  ('fex-upstream', 'FEXCore/LICENSE'), ('fex-upstream', 'External/tiny-json/LICENSE'),
                  ('fex-upstream', 'External/cephes/LICENSE'),
                  ('fex-upstream', 'External/SoftFloat-3e/include/SoftFloat-3e/softfloat.h')} <= seen, 'bundled_terms_closure')
    return {'audit': audit, 'components': by_id, 'mounts': value['mounts'], 'inputs': value}


def tree_entries(data):
    """Parse exact ls-tree bytes, admitting declared gitlinks but never links."""
    need(isinstance(data, bytes) and 0 < len(data) <= 128 * 1024 * 1024 and data.endswith(b'\0'), 'tree_listing_shape')
    entries, aliases = {}, {}
    for item in data[:-1].split(b'\0'):
        try:
            metadata, raw_path = item.split(b'\t', 1)
            mode, kind, object_id = metadata.decode('ascii').split(' ')
            path = raw_path.decode('utf-8')
        except (ValueError, UnicodeError): raise Error('tree_listing_shape') from None
        parts = relative(path)
        need((mode, kind) in (('100644', 'blob'), ('100755', 'blob'), ('160000', 'commit')), 'unsupported_tree_entry')
        oid(object_id)
        need(path not in entries and len(entries) < MAX_MEMBERS, 'duplicate_or_excess_tree_entry')
        for i in range(1, len(parts) + 1):
            prefix = '/'.join(parts[:i]); key = unicodedata.normalize('NFD', prefix).casefold()
            need(key not in aliases or aliases[key] == prefix, 'tree_path_alias'); aliases[key] = prefix
        entries[path] = {'mode': mode, 'git_object': object_id}
    for path in entries:
        parts = relative(path)
        need(not any('/'.join(parts[:i]) in entries for i in range(1, len(parts))), 'tree_path_conflict')
    return entries


def tree_identity(entries):
    """Reconstruct Git's tree hash including unmaterialized gitlink entries."""
    root = {}
    for path, row in entries.items():
        node = root; parts = relative(path)
        for part in parts[:-1]:
            need(part not in node or isinstance(node[part], dict), 'tree_path_conflict'); node = node.setdefault(part, {})
        need(parts[-1] not in node, 'tree_path_conflict'); node[parts[-1]] = (row['mode'], row['git_object'])
    def digest(node):
        rows = []
        for name, child in sorted(node.items(), key=lambda r: r[0].encode() + (b'/' if isinstance(r[1], dict) else b'')):
            mode, value = ('40000', digest(child)) if isinstance(child, dict) else child
            rows.append(mode.encode() + b' ' + name.encode() + b'\0' + bytes.fromhex(value))
        raw = b''.join(rows); return hashlib.sha1(f'tree {len(raw)}\0'.encode() + raw).hexdigest()
    return digest(root)


def mount_paths(context):
    paths = {'fex-upstream': ''}
    for m in context['mounts']:
        if m['status'] == 'enabled':
            need(m['parent'] in paths and m['component'] not in paths, 'mount_dependency_order')
            paths[m['component']] = '/'.join(p for p in (paths[m['parent']], m['path']) if p)
    need(set(paths) == set(context['components']), 'mount_component_closure')
    return paths


def check_mount_tree(cid, entries, context):
    links = {p: r['git_object'] for p, r in entries.items() if r['mode'] == '160000'}
    mounts = [m for m in context['mounts'] if m['parent'] == cid]
    need(links == {m['path']: m['commit'] for m in mounts}, 'tree_mount_mismatch')
    for m in mounts:
        if m['status'] == 'enabled': need(context['components'][m['component']]['commit'] == m['commit'], 'mounted_commit_mismatch')


def _git(git, repository, *args, operations=None, operation_root=None):
    started = time.monotonic()
    argv = [git, '--no-pager', '--no-optional-locks', '-C', str(repository),
            '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false',
            '-c', 'protocol.allow=never', '-c', 'submodule.recurse=false', '-c', 'gc.auto=0', *args]
    try:
        data = _audit.bounded_git(git, repository, args)
    except _audit.Invalid as error:
        if operations is not None:
            operations.append({'kind': 'git_read', 'argv': argv, 'status': 'failed',
                'returncode': None, 'reason': error.code, 'elapsed_ms': int((time.monotonic() - started) * 1000),
                'stdout_ref': None})
        raise Error(error.code) from None
    if operations is not None:
        name = 'operations/' + str(len(operations)) + '.stdout'
        target = Path(operation_root) / name
        with target.open('xb') as stream: stream.write(data)
        target.chmod(0o600)
        operations.append({'kind': 'git_read', 'argv': argv, 'status': 'completed', 'returncode': 0,
            'reason': None, 'elapsed_ms': int((time.monotonic() - started) * 1000),
            'stdout_ref': {'path': name, 'sha256': digest_bytes(data)}})
    return data


def archive_to_file(git, repository, commit, output):
    """Wine's audited streamed archive algorithm, with task-local output."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_', 'DYLD_', 'LD_'))}
    env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_SYSTEM='/dev/null', GIT_CONFIG_NOSYSTEM='1',
               GIT_TERMINAL_PROMPT='0', GIT_NO_REPLACE_OBJECTS='1', GIT_NO_LAZY_FETCH='1',
               GIT_OPTIONAL_LOCKS='0', GIT_ATTR_NOSYSTEM='1', LC_ALL='C')
    argv = [git, '--no-pager', '--no-optional-locks', '-C', str(repository), '-c', 'core.hooksPath=/dev/null',
            '-c', 'core.fsmonitor=false', '-c', 'protocol.allow=never', '-c', 'submodule.recurse=false',
            '-c', 'gc.auto=0', '-c', 'tar.umask=022', 'archive', '--format=tar', commit]
    with Path(output).open('xb') as target:
        process = subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, start_new_session=True)
        deadline, size = time.monotonic() + GIT_TIMEOUT, 0
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while selector.get_map():
                    remaining = deadline - time.monotonic(); need(remaining > 0, 'git_archive_timeout')
                    for key, _ in selector.select(min(remaining, .25)):
                        chunk = os.read(key.fileobj.fileno(), 65536)
                        if not chunk: selector.unregister(key.fileobj); continue
                        size += len(chunk); need(size <= MAX_ARCHIVE, 'git_archive_size'); target.write(chunk)
                need(process.wait(timeout=max(.01, deadline - time.monotonic())) == 0, 'git_archive_failed')
        except BaseException:
            try: os.killpg(process.pid, signal.SIGKILL)
            except (PermissionError, ProcessLookupError):
                if process.poll() is None: process.kill()
            try: process.wait(timeout=2)
            except subprocess.TimeoutExpired: raise Error('git_archive_cleanup_unverified') from None
            raise
        finally: process.stdout.close()
    os.chmod(output, 0o600)


def extract_verified(archive_path, destination, expected):
    """Extract only blob files; gitlink placeholders are never mounted implicitly."""
    destination = Path(destination); destination.mkdir(parents=True, mode=0o755); destination.chmod(0o755)
    blobs = {p: r for p, r in expected.items() if r['mode'] != '160000'}
    gitlinks = {p for p, r in expected.items() if r['mode'] == '160000'}
    found, seen, rows, total = set(), set(), [], 0
    with tarfile.open(archive_path, mode='r:') as archive:
        for index, member in enumerate(archive):
            need(index < MAX_MEMBERS * 2, 'archive_member_limit')
            name = member.name.rstrip('/') if member.isdir() else member.name; parts = relative(name)
            need(name not in seen, 'duplicate_archive_entry'); seen.add(name)
            need(member.type in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE), 'unsupported_archive_entry')
            need(member.mode & ~0o777 == 0 and not member.mode & 0o022, 'unsafe_archive_mode')
            path = destination.joinpath(*parts)
            if member.isdir():
                if name in gitlinks: continue
                need(any(p.startswith(name + '/') for p in expected), 'unexpected_archive_directory')
                path.mkdir(parents=True, exist_ok=True, mode=0o755); path.chmod(0o755); continue
            need(name in blobs and name not in found, 'unexpected_archive_file')
            need(type(member.size) is int and 0 <= member.size <= MAX_MEMBER, 'archive_member_size')
            need(type(member.mtime) is int and 0 <= member.mtime <= 2**53 - 1, 'archive_mtime')
            total += member.size; need(total <= MAX_CONTENT, 'archive_content_limit')
            desired = blobs[name]; need(bool(member.mode & 0o111) == (desired['mode'] == '100755'), 'archive_mode_mismatch')
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            bh = hashlib.sha1(f'blob {member.size}\0'.encode()); ch = hashlib.sha256(); stream = archive.extractfile(member)
            need(stream is not None, 'archive_content_missing')
            with stream, path.open('xb') as target:
                remaining = member.size
                while remaining:
                    block = stream.read(min(1024 * 1024, remaining)); need(bool(block), 'archive_content_truncated')
                    remaining -= len(block); bh.update(block); ch.update(block); target.write(block)
            need(bh.hexdigest() == desired['git_object'], 'archive_blob_mismatch')
            path.chmod(0o755 if desired['mode'] == '100755' else 0o644); os.utime(path, (member.mtime, member.mtime))
            found.add(name); rows.append({'path': name, 'mode': desired['mode'], 'size_bytes': member.size,
                                        'mtime': member.mtime, 'sha256': ch.hexdigest(), 'git_blob': bh.hexdigest()})
    need(found == set(blobs), 'archive_missing_files')
    return sorted(rows, key=lambda r: r['path']), total


def source_interfaces(fex_root):
    """Derive source contracts, never a compiler ABI or live-service result."""
    sources = {}
    for path in sorted(INTERFACES):
        raw = read_relative(fex_root, path, MAX_MEMBER)
        sources[path] = {'sha256': digest_bytes(raw), 'git_blob': hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest(),
                         'text': raw.decode('utf-8')}
    header = sources['Source/Windows/UnixLib/FEXUnixLib.h']['text']
    match = re.search(r'enum class FEXUnixLibFunctions\s*:\s*uint32_t\s*\{([^}]+)\}', header)
    need(match is not None, 'unixlib_enum_missing')
    names = [x.strip() for x in match.group(1).split(',') if x.strip()]
    need(names[-1] == 'MAX' and len(names) == 9 and len(set(names)) == 9, 'unixlib_enum_shape'); names = names[:-1]
    cpp = sources['Source/Windows/UnixLib/FEXUnixLib.cpp']['text']
    need(re.search(r'using\s+NTSTATUS\s*=\s*int32_t\s*;', cpp) is not None, 'unixlib_status_type')
    need(re.search(r'using\s+unixlib_entry_t\s*=\s*NTSTATUS\s*\(\*\)\(void\*\)\s*;', cpp) is not None, 'unixlib_callback_type')
    statuses = {name: int(value, 0) for name, value in re.findall(r'constexpr NTSTATUS (STATUS_\w+) = (0x[0-9A-Fa-f]+|[0-9]+);', cpp)}
    need(set(statuses) == {'STATUS_SUCCESS', 'STATUS_NOT_SUPPORTED', 'STATUS_INTERNAL_ERROR'}, 'unixlib_status_values')
    table = re.search(r'__wine_unix_call_funcs\[\]\s*=\s*\{([^}]+)\}', cpp)
    need(table is not None, 'unixlib_table_missing')
    handlers = re.findall(r'FEXUnixLib_(\w+)Handler', table.group(1)); need(handlers == names, 'unixlib_table_order')
    type_layout = {'bool': (1, 1), 'uint64_t': (8, 8), 'size_t': (8, 8), 'int32_t': (4, 4), 'uint32_t': (4, 4),
                   'const void*': (8, 8), 'void*': (8, 8), 'const char*': (8, 8)}
    structures = {}
    for m in re.finditer(r'struct\s+(FEXUnixLib_\w+)\s*\{([^}]+)\};', header):
        offset, align, fields = 0, 1, []
        for field in m.group(2).strip().split(';'):
            if not field.strip(): continue
            kind, name = field.strip().rsplit(None, 1); kind = re.sub(r'\s+', ' ', kind)
            need(kind in type_layout, 'unixlib_argument_type'); size, alignment = type_layout[kind]
            align = max(align, alignment); offset = (offset + alignment - 1) // alignment * alignment
            fields.append({'name': name, 'type': kind, 'offset': offset}); offset += size
        size = (offset + align - 1) // align * align
        assertion = re.search(r'static_assert\(sizeof\(' + re.escape(m.group(1)) + r'\) == (\d+)\)', header)
        need(assertion is not None and int(assertion.group(1)) == size, 'unixlib_argument_size')
        structures[m.group(1)] = {'name': m.group(1), 'size': size, 'alignment': align, 'fields': fields,
                                'line': header[:m.start()].count('\n') + 1}
    services = []
    for index, name in enumerate(names):
        struct_name = 'FEXUnixLib_' + name + ('Args' if name == 'SetHardwareTSOControl' else '')
        need(name == 'DeleteSHMStatsFile' or struct_name in structures, 'unixlib_argument_missing')
        services.append({'ordinal': index, 'name': name, 'argument': structures.get(struct_name),
                         'live_status': 'unperformed'})
    modules = []
    for flavor, path in [('arm64ec', 'Source/Windows/ARM64EC/libarm64ecfex.def'), ('wow64', 'Source/Windows/WOW64/libwow64fex.def')]:
        text = sources[path]['text']; library = re.search(r'^LIBRARY\s+(\S+)', text, re.M)
        need(library is not None and '\nEXPORTS' in text, 'module_definition')
        exports = []
        for number, line in enumerate(text.splitlines(), 1):
            words = line.strip().split()
            if not words or words[0] in ('LIBRARY', 'EXPORTS') or line.lstrip().startswith(';'): continue
            need(len(words) in (1, 2) and (len(words) == 1 or words[1] == 'DATA'), 'module_export_shape')
            exports.append({'name': words[0], 'kind': 'data' if len(words) == 2 else 'function', 'line': number})
        modules.append({'id': flavor, 'library': library.group(1), 'guest_architecture': 'x86_64' if flavor == 'arm64ec' else 'i386',
                        'pe_abi': 'ARM64EC' if flavor == 'arm64ec' else 'ARM64', 'exports': exports,
                        'build_status': 'unperformed', 'execution_status': 'unperformed'})
    loader = sources['Source/Windows/Common/FEXUnixLib.cpp']['text']
    search_names = re.findall(r'InitUnicodeString\(L"(lib\w+)"\)', loader)
    need(search_names == [m['library'].removesuffix('.dll') for m in modules], 'native_search_contract')
    module = sources['Source/Windows/ARM64EC/Module.cpp']['text']
    teb = re.search(r'TEBCPUAreaOffset\s*=\s*(0x[0-9a-fA-F]+)', module); need(teb is not None, 'teb_contract_missing')
    assembly = sources['Source/Windows/ARM64EC/Module.S']['text']; x18_lines = [i for i, line in enumerate(assembly.splitlines(), 1) if re.search(r'\bx18\b', line)]
    need(x18_lines, 'x18_contract_missing')
    return {'schema_version': 1, 'record_kind': 'fex_source_interfaces', 'scope': 'fex_component',
            'observation': 'source_inspected', 'layout_method': 'source_model_64bit_not_compiler_abi',
            'pointer_size_assumption': 8, 'services': services, 'modules': modules,
            'native_search': {'names': search_names, 'candidate_suffix': '.so', 'live_status': 'unperformed'},
            'teb_cpu_area_offset': int(teb.group(1), 16), 'x18_source_lines': x18_lines,
            'status_return': 'signed_32bit_NTSTATUS', 'status_values_uint32': statuses,
            'feature_policy': {'darwin_provider': 'unperformed', 'effective_cpu_model': 'unperformed',
                               'per_thread_ordering': 'unperformed', 'required_software_tso_enabled': True,
                               'hardware_tso_capability': 'unperformed'}, 'sources': {p: {k: v for k, v in row.items() if k != 'text'} for p, row in sources.items()},
            'runtime_qualified': False}


def _digest_relative(root, path):
    with os.fdopen(open_relative(root, path), 'rb') as stream:
        before = os.fstat(stream.fileno()); need(before.st_size <= MAX_ARCHIVE, 'input_size_limit')
        digest = hashlib.sha256(); size = 0
        while block := stream.read(1024 * 1024):
            size += len(block); need(size <= MAX_ARCHIVE, 'input_size_limit'); digest.update(block)
        after = os.fstat(stream.fileno())
        need(size == before.st_size and (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
             == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'input_changed')
    return digest.hexdigest()


def _source_files(root):
    files, directories, inodes = {}, set(), set()
    def walk(fd, prefix):
        for name in os.listdir(fd):
            path = '/'.join((*prefix, name)); relative(path)
            need(len(files) + len(directories) < MAX_MEMBERS * 2, 'source_entry_limit')
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            need(stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode), 'source_entry_unsupported')
            if stat.S_ISDIR(info.st_mode):
                directories.add(path); child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                try: walk(child, (*prefix, name))
                finally: os.close(child)
            else:
                identity = (info.st_dev, info.st_ino); need(identity not in inodes, 'source_inode_alias')
                inodes.add(identity); files[path] = identity
    fd = open_relative(root, 'sources/fex', directory=True)
    try: walk(fd, ())
    finally: os.close(fd)
    return files, directories


def verify_prepared(path, expected_inputs_sha256=None, repo_root=REPO):
    root = operation_output(path, repo_root=repo_root, require_empty=False, create=False)
    raw = read_relative(root, 'prepared.json'); prepared = record(decode_json(raw), 'fex_prepared_sources')
    need(set(prepared) == {'schema_version', 'record_kind', 'scope', 'inputs_ref', 'audit_ref', 'baseline_ref',
            'preparation_only', 'runtime_qualified', 'components', 'source_manifest_ref', 'interfaces_ref', 'operations_ref'}, 'prepared_fields')
    need(prepared['scope'] == 'fex_component' and prepared['preparation_only'] is True
         and prepared['runtime_qualified'] is False, 'prepared_scope')
    inputs_ref = reference(prepared['inputs_ref']); input_raw = read_relative(repo_root, inputs_ref['path'])
    need(digest_bytes(input_raw) == inputs_ref['sha256'], 'prepared_inputs_digest')
    if expected_inputs_sha256 is not None: need(inputs_ref['sha256'] == oid(expected_inputs_sha256, 64), 'prepared_inputs_mismatch')
    context = validate_inputs(decode_json(input_raw), repo_root); mounts = mount_paths(context)
    need(prepared['audit_ref'] == context['inputs']['audit_ref'] and prepared['baseline_ref'] == context['inputs']['baseline_ref'], 'prepared_baseline_identity')
    manifest_ref = reference(prepared['source_manifest_ref']); need(manifest_ref['path'] == 'source-manifest.json', 'prepared_manifest_path')
    mr = read_relative(root, manifest_ref['path'])
    need(digest_bytes(mr) == manifest_ref['sha256'], 'prepared_manifest_digest')
    manifest = record(decode_json(mr), 'fex_source_files')
    need(set(manifest) == {'schema_version', 'record_kind', 'scope', 'files'} and manifest['scope'] == 'fex_component', 'manifest_fields')
    need(isinstance(manifest['files'], list) and 0 < len(manifest['files']) <= MAX_MEMBERS, 'manifest_files')
    expected = {}; total = 0
    for row in manifest['files']:
        need(isinstance(row, dict) and set(row) == {'path', 'component', 'component_path', 'mode', 'size_bytes', 'mtime', 'sha256', 'git_blob'}, 'manifest_row_fields')
        relative(row['path']); relative(row['component_path']); oid(row['sha256'], 64); oid(row['git_blob'])
        need(row['component'] in mounts and row['path'] == '/'.join(p for p in (mounts[row['component']], row['component_path']) if p)
             and row['path'] not in expected and row['mode'] in ('100644', '100755')
             and type(row['size_bytes']) is int and 0 <= row['size_bytes'] <= MAX_MEMBER
             and type(row['mtime']) is int and 0 <= row['mtime'] <= 2**53 - 1, 'manifest_row_identity')
        expected[row['path']] = row; total += row['size_bytes']
    need(list(expected) == sorted(expected) and total <= MAX_CONTENT, 'manifest_accounting')
    need(isinstance(prepared['components'], list) and len(prepared['components']) == len(context['components']), 'prepared_components')
    seen = set()
    for c in prepared['components']:
        need(isinstance(c, dict) and set(c) == {'id', 'commit', 'tree', 'mount_path', 'source_path', 'tree_listing_ref', 'archive_ref', 'file_count', 'total_bytes'}, 'prepared_component_fields')
        cid = c['id']; need(cid in context['components'] and cid not in seen, 'prepared_component_identity'); seen.add(cid)
        original = context['components'][cid]
        need((c['commit'], c['tree'], c['mount_path']) == (original['commit'], original['tree'], mounts[cid])
             and c['source_path'] == 'sources/fex' + ('/' + mounts[cid] if mounts[cid] else ''), 'prepared_component_identity')
        lr = reference(c['tree_listing_ref']); need(lr['path'] == 'trees/' + cid + '.z', 'prepared_listing_path')
        listing = read_relative(root, lr['path'], 128 * 1024 * 1024)
        need(digest_bytes(listing) == lr['sha256'] == original['listing_ref']['sha256'], 'prepared_listing_identity')
        entries = tree_entries(listing); check_mount_tree(cid, entries, context)
        need(tree_identity(entries) == c['tree'], 'prepared_tree_identity')
        rows = [r for r in expected.values() if r['component'] == cid]
        need({r['component_path']: {'mode': r['mode'], 'git_object': r['git_blob']} for r in rows}
             == {p: r for p, r in entries.items() if r['mode'] != '160000'}, 'prepared_blob_closure')
        need(type(c['file_count']) is int and c['file_count'] == len(rows)
             and type(c['total_bytes']) is int and c['total_bytes'] == sum(r['size_bytes'] for r in rows), 'prepared_component_accounting')
        ar = reference(c['archive_ref']); need(ar['path'] == 'archives/' + cid + '.tar', 'prepared_archive_path')
        need(_digest_relative(root, ar['path']) == ar['sha256'], 'prepared_archive_digest')
    actual, directories = _source_files(root)
    expected_dirs = {'/'.join(relative(p)[:i]) for p in expected for i in range(1, len(relative(p)))}
    need(set(actual) == set(expected) and directories == expected_dirs, 'prepared_source_inventory')
    for name, row in expected.items():
        source = 'sources/fex/' + name
        with os.fdopen(open_relative(root, source), 'rb') as stream:
            before = os.fstat(stream.fileno()); need((before.st_dev, before.st_ino) == actual[name], 'source_changed')
            need(stat.S_IMODE(before.st_mode) == (0o755 if row['mode'] == '100755' else 0o644)
                 and before.st_size == row['size_bytes'] and before.st_mtime_ns == row['mtime'] * 1000000000, 'prepared_source_metadata')
            ch = hashlib.sha256(); bh = hashlib.sha1(f'blob {row["size_bytes"]}\0'.encode()); remaining = row['size_bytes']
            while remaining:
                chunk = stream.read(min(remaining, 1024 * 1024)); need(chunk, 'prepared_source_size'); remaining -= len(chunk); ch.update(chunk); bh.update(chunk)
            need(not stream.read(1) and ch.hexdigest() == row['sha256'] and bh.hexdigest() == row['git_blob'], 'prepared_source_digest')
            after = os.fstat(stream.fileno()); need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                 == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'source_changed')
    for name in ('terms', 'source_requirements', 'interface_sources'):
        for r in context['inputs'][name]:
            path = '/'.join(p for p in (mounts[r['component']], r['path']) if p); row = expected.get(path)
            need(row is not None and row['sha256'] == r['sha256'] and row['git_blob'] == r['git_blob'], 'source_reference_digest')
    ir = reference(prepared['interfaces_ref']); need(ir['path'] == 'interfaces.json', 'prepared_interface_path')
    interfaces_raw = read_relative(root, ir['path'])
    need(digest_bytes(interfaces_raw) == ir['sha256'] and decode_json(interfaces_raw) == source_interfaces(root / 'sources/fex'), 'prepared_interface_replay')
    operations_ref = reference(prepared['operations_ref'])
    need(operations_ref['path'] == 'preparation-operations.json', 'prepared_operations_path')
    operations_raw = read_relative(root, operations_ref['path'])
    need(digest_bytes(operations_raw) == operations_ref['sha256'], 'prepared_operations_digest')
    operations = record(decode_json(operations_raw), 'fex_source_preparation_operations')
    need(set(operations) == {'schema_version', 'record_kind', 'scope', 'status', 'inputs_sha256',
              'producer_revision', 'producer_sources', 'git_tool', 'operations', 'storage'}, 'operations_fields')
    need(operations['scope'] == 'fex_component' and operations['status'] == 'completed'
         and operations['inputs_sha256'] == inputs_ref['sha256'], 'operations_scope')
    oid(operations['producer_revision'])
    need(isinstance(operations['producer_sources'], list) and len(operations['producer_sources']) == 4, 'producer_sources')
    for producer in operations['producer_sources']:
        reference(producer)
        need(_digest_relative(repo_root, producer['path']) == producer['sha256'], 'producer_source_changed')
    need({r['path'] for r in operations['producer_sources']} == {'tools/fex/prepare.py', 'tools/fex/common.py',
             'tools/wine/common.py', 'tools/sources/validate_inventory.py'}, 'producer_source_closure')
    need(isinstance(operations['git_tool'], dict) and set(operations['git_tool']) == {'path', 'sha256', 'version'}, 'git_tool_fields')
    oid(operations['git_tool']['sha256'], 64)
    need(isinstance(operations['git_tool']['path'], str) and isinstance(operations['git_tool']['version'], str), 'git_tool_identity')
    need(isinstance(operations['operations'], list) and len(operations['operations']) == 37, 'operation_count')
    need(isinstance(operations['storage'], dict) and set(operations['storage']) == {'free_before_bytes', 'source_bytes', 'archive_bytes'}, 'operation_storage')
    need(all(type(x) is int and x >= 0 for x in operations['storage'].values())
         and operations['storage']['source_bytes'] == total, 'operation_storage_accounting')
    archive_bytes = sum(os.stat(root / c['archive_ref']['path'], follow_symlinks=False).st_size for c in prepared['components'])
    need(archive_bytes == operations['storage']['archive_bytes'] and archive_bytes <= MAX_ARCHIVE, 'operation_archive_accounting')
    for index, op in enumerate(operations['operations']):
        need(isinstance(op, dict) and set(op) == {'kind', 'argv', 'status', 'returncode', 'reason', 'elapsed_ms', 'stdout_ref'}
             and op['kind'] in ('git_read', 'git_archive') and op['status'] == 'completed'
             and type(op['returncode']) is int and op['returncode'] == 0 and op['reason'] is None
             and type(op['elapsed_ms']) is int and 0 <= op['elapsed_ms'] <= GIT_TIMEOUT * 1000 + 2000,
             'operation_result')
        need(isinstance(op['argv'], list) and op['argv'] and all(isinstance(a, str) and '\0' not in a for a in op['argv']), 'operation_arguments')
        ref = reference(op['stdout_ref'])
        if op['kind'] == 'git_read':
            need(ref['path'] == 'operations/' + str(index) + '.stdout', 'operation_output_path')
        else:
            need(ref in [c['archive_ref'] for c in prepared['components']], 'operation_archive_identity')
        need(_digest_relative(root, ref['path']) == ref['sha256'], 'operation_output_digest')
    need(operations['operations'][0]['argv'][-2:] == ['rev-parse', 'HEAD']
         and read_relative(root, operations['operations'][0]['stdout_ref']['path']).decode().strip() == operations['producer_revision'], 'producer_revision_receipt')
    need(operations['operations'][1]['argv'][-1:] == ['--version']
         and read_relative(root, operations['operations'][1]['stdout_ref']['path']).decode().strip() == operations['git_tool']['version'], 'git_version_receipt')
    for number, c in enumerate(prepared['components']):
        checks = operations['operations'][2 + number * 4:6 + number * 4]
        expected_args = [['rev-parse', '--show-object-format'], ['cat-file', '-t', c['commit']],
                         ['rev-parse', c['commit'] + '^{tree}'], ['ls-tree', '-r', '-z', '--full-tree', c['commit']]]
        expected_outputs = [b'sha1', b'commit', c['tree'].encode(), read_relative(root, c['tree_listing_ref']['path'], 128 * 1024 * 1024)]
        for op, args, expected_output in zip(checks, expected_args, expected_outputs):
            need(op['kind'] == 'git_read' and op['argv'][-len(args):] == args
                 and op['argv'][0] == operations['git_tool']['path'], 'source_operation_arguments')
            actual_output = read_relative(root, op['stdout_ref']['path'], 128 * 1024 * 1024)
            need(actual_output == expected_output if args[0] == 'ls-tree' else actual_output.strip() == expected_output, 'source_operation_output')
        archive_op = operations['operations'][30 + number]
        need(archive_op['kind'] == 'git_archive' and archive_op['argv'][-3:] == ['archive', '--format=tar', c['commit']]
             and archive_op['stdout_ref'] == c['archive_ref'], 'archive_operation_identity')
    need(read_relative(repo_root, inputs_ref['path']) == input_raw and read_relative(root, 'prepared.json') == raw
         and read_relative(root, manifest_ref['path']) == mr and _source_files(root) == (actual, directories), 'prepared_inputs_changed')
    return prepared


def _prepare(inputs_path, source_cache, output_value, repo_root=REPO, *, git=None, operations=None, operation_root=None):
    root = Path(repo_root); relative(inputs_path); input_raw = read_relative(root, inputs_path)
    context = validate_inputs(decode_json(input_raw), root); mounts = mount_paths(context)
    cache = Path(source_cache).absolute(); need(not cache.is_symlink() and cache.is_dir(), 'cache_directory')
    output = Path(operation_root)
    need(not cache.is_relative_to(output) and not output.is_relative_to(cache), 'input_output_alias')
    git = _git_executable(git or shutil.which('git'))
    audit = _audit.Audit(context['audit'], root, cache)
    inspected = []
    run_git = lambda repo, *args: _git(git, repo, *args, operations=operations['operations'], operation_root=operation_root)
    for cid, c in context['components'].items():
        try: repository = audit.validate_repo(c['cache_path'])
        except (_audit.Invalid, configparser.Error, UnicodeError) as error:
            raise Error(error.code if isinstance(error, _audit.Invalid) else 'unsafe_git_config') from None
        need(run_git(repository, 'rev-parse', '--show-object-format').strip() == b'sha1', 'git_object_format')
        need(run_git(repository, 'cat-file', '-t', c['commit']).strip() == b'commit', 'git_commit_type')
        need(run_git(repository, 'rev-parse', c['commit'] + '^{tree}').strip().decode() == c['tree'], 'git_tree_mismatch')
        listing = run_git(repository, 'ls-tree', '-r', '-z', '--full-tree', c['commit'])
        need(digest_bytes(listing) == c['listing_ref']['sha256'] and read_relative(cache, c['listing_ref']['path'], 128 * 1024 * 1024) == listing, 'cached_listing_mismatch')
        entries = tree_entries(listing); check_mount_tree(cid, entries, context); need(tree_identity(entries) == c['tree'], 'git_tree_mismatch')
        inspected.append((cid, c, repository, listing, entries))
    need(shutil.disk_usage(root).free >= 4 * 1024**3, 'source_storage_unavailable')
    output = Path(operation_root); (output / 'trees').mkdir(mode=0o700); (output / 'archives').mkdir(mode=0o700); (output / 'sources').mkdir(mode=0o700)
    rows, components, total, archive_total = [], [], 0, 0
    for cid, c, repository, listing, entries in inspected:
        listing_path = 'trees/' + cid + '.z'; (output / listing_path).write_bytes(listing); os.chmod(output / listing_path, 0o600)
        need(shutil.disk_usage(output).free >= MAX_ARCHIVE + MAX_CONTENT, 'source_storage_unavailable')
        archive_path = 'archives/' + cid + '.tar'; started = time.monotonic()
        try:
            archive_to_file(git, repository, c['commit'], output / archive_path)
        except Error as error:
            operations['operations'].append({'kind': 'git_archive', 'argv': _archive_argv(git, repository, c['commit']),
                'status': 'failed', 'returncode': None, 'reason': error.code,
                'elapsed_ms': int((time.monotonic() - started) * 1000), 'stdout_ref': None})
            raise
        operations['operations'].append({'kind': 'git_archive', 'argv': _archive_argv(git, repository, c['commit']),
            'status': 'completed', 'returncode': 0, 'reason': None, 'elapsed_ms': int((time.monotonic() - started) * 1000),
            'stdout_ref': {'path': archive_path, 'sha256': sha256(output / archive_path)}})
        archive_total += (output / archive_path).stat().st_size; need(archive_total <= MAX_ARCHIVE, 'aggregate_archive_limit')
        source_path = 'sources/fex' + ('/' + mounts[cid] if mounts[cid] else '')
        files, size = extract_verified(output / archive_path, output / source_path, entries); total += size; need(total <= MAX_CONTENT, 'aggregate_source_limit')
        rows.extend(dict(r, path='/'.join(p for p in (mounts[cid], r['path']) if p), component=cid, component_path=r['path']) for r in files)
        components.append({'id': cid, 'commit': c['commit'], 'tree': c['tree'], 'mount_path': mounts[cid], 'source_path': source_path,
                           'tree_listing_ref': {'path': listing_path, 'sha256': digest_bytes(listing)},
                           'archive_ref': {'path': archive_path, 'sha256': sha256(output / archive_path)}, 'file_count': len(files), 'total_bytes': size})
    manifest = {'schema_version': 1, 'record_kind': 'fex_source_files', 'scope': 'fex_component', 'files': sorted(rows, key=lambda r: r['path'])}
    write_json(output / 'source-manifest.json', manifest); write_json(output / 'interfaces.json', source_interfaces(output / 'sources/fex'))
    prepared = {'schema_version': 1, 'record_kind': 'fex_prepared_sources', 'scope': 'fex_component',
                'inputs_ref': {'path': inputs_path, 'sha256': digest_bytes(input_raw)}, 'audit_ref': context['inputs']['audit_ref'],
                'baseline_ref': context['inputs']['baseline_ref'], 'preparation_only': True, 'runtime_qualified': False,
                'components': components, 'source_manifest_ref': {'path': 'source-manifest.json', 'sha256': sha256(output / 'source-manifest.json')},
                'interfaces_ref': {'path': 'interfaces.json', 'sha256': sha256(output / 'interfaces.json')}}
    operations['storage'].update(source_bytes=total, archive_bytes=archive_total)
    operations['status'] = 'completed'
    write_json(output / 'preparation-operations.json', operations)
    prepared['operations_ref'] = {'path': 'preparation-operations.json', 'sha256': sha256(output / 'preparation-operations.json')}
    need(read_relative(root, inputs_path) == input_raw, 'inputs_changed'); write_json(output / 'prepared.json', prepared)
    return verify_prepared(output, digest_bytes(input_raw), root)


def _git_executable(value):
    need(value is not None, 'git_unavailable')
    try:
        path = Path(value).resolve(strict=True)
        need(path.is_file() and not path.is_symlink(), 'git_nonregular_executable')
    except OSError:
        raise Error('git_executable_unavailable') from None
    return str(path)


def _archive_argv(git, repository, commit):
    return [git, '--no-pager', '--no-optional-locks', '-C', str(repository), '-c', 'core.hooksPath=/dev/null',
            '-c', 'core.fsmonitor=false', '-c', 'protocol.allow=never', '-c', 'submodule.recurse=false',
            '-c', 'gc.auto=0', '-c', 'tar.umask=022', 'archive', '--format=tar', commit]


def prepare(inputs_path, source_cache, output_value, repo_root=REPO, *, git=None):
    root = Path(repo_root); relative(inputs_path); input_raw = read_relative(root, inputs_path)
    validate_inputs(decode_json(input_raw), root)
    git = _git_executable(git or shutil.which('git'))
    free = shutil.disk_usage(root).free; need(free >= MAX_ARCHIVE + MAX_CONTENT, 'source_storage_unavailable')
    output = operation_output(output_value, repo_root=root)
    (output / 'operations').mkdir(mode=0o700)
    operations = {'schema_version': 1, 'record_kind': 'fex_source_preparation_operations', 'scope': 'fex_component',
                  'status': 'started', 'inputs_sha256': digest_bytes(input_raw), 'producer_revision': None,
                  'producer_sources': [{'path': p, 'sha256': _digest_relative(root, p)} for p in
                     ['tools/fex/prepare.py', 'tools/fex/common.py', 'tools/wine/common.py', 'tools/sources/validate_inventory.py']],
                  'git_tool': {'path': str(git), 'sha256': sha256(git), 'version': None}, 'operations': [],
                  'storage': {'free_before_bytes': free, 'source_bytes': 0, 'archive_bytes': 0}}
    try:
        operations['producer_revision'] = _git(git, root, 'rev-parse', 'HEAD', operations=operations['operations'], operation_root=output).decode().strip()
        operations['git_tool']['version'] = _git(git, root, '--version', operations=operations['operations'], operation_root=output).decode().strip()
        return _prepare(inputs_path, source_cache, output_value, root, git=git, operations=operations, operation_root=output)
    except BaseException:
        if not (output / 'preparation-operations.json').exists():
            operations['status'] = 'failed'
            write_json(output / 'preparation-operations.json', operations)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', required=True); parser.add_argument('--source-cache', required=True)
    parser.add_argument('--output', required=True); parser.add_argument('--require-empty', required=True, action='store_true')
    args = parser.parse_args()
    try:
        value = prepare(args.inputs, args.source_cache, args.output)
        print(json.dumps({'prepared': True, 'file_count': sum(c['file_count'] for c in value['components']),
                          'preparation_only': True, 'runtime_qualified': False})); return 0
    except (Error, OSError, ValueError, KeyError, tarfile.TarError, subprocess.SubprocessError) as error:
        print(json.dumps({'prepared': False, 'error': error.code if isinstance(error, Error) else 'preparation_failed',
                          'preparation_only': True, 'runtime_qualified': False})); return 1


if __name__ == '__main__': sys.exit(main())
