#!/usr/bin/env python3
"""Account for DXMT Stage 1 sources, tools and Wine roles without building."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from common import (REPO, MACH_ARM64, Error, archive_machines, decode_json, digest, encoded, fields,
                    hex_digest, load_json, macho_slices, need, output_directory, producer_hashes,
                    read_relative, real_directory, relative, resolve_contained, run_bounded, sha256, write_new)
from prepare import validate_inputs, verify_prepared

CONFIG_FIELDS = ['schema_version', 'record_kind', 'scope', 'build_type', 'wine_builtin_dll', 'guest_target',
                 'guest_flags', 'native_target', 'windows_install_dir', 'unix_install_dir', 'native_llvm_major',
                 'features', 'max_jobs', 'ownership_root', 'graphics_patch_status', 'source_accounting_gate',
                 'shader_readiness_gate', 'runtime_eligible', 'source_terms_limit']
TOOL_FIELDS = ['schema_version', 'record_kind', 'scope', 'reused_wine_lock', 'llvm_mingw_archive',
               'cache_manifest_sha256', 'cache_prepared_sha256', 'cross_tools', 'candidates',
               'native_tool_paths', 'sdk', 'metal_toolchain', 'installation_performed']

SOURCE_TERMS_LIMIT = 'Selected source/header/build-tool notices only; shipped payload and corresponding-source closure remain later work.'


def validate_config(value):
    fields(value, CONFIG_FIELDS, 'dxmt_build_configuration')
    need(value['scope'] == 'dxmt_component' and value['build_type'] == 'release'
         and value['wine_builtin_dll'] is True and value['guest_target'] == 'arm64ec-w64-mingw32'
         and value['guest_flags'] == ['-marm64x'] and value['native_target'] == 'arm64-apple-darwin'
         and value['windows_install_dir'] == 'aarch64-windows' and value['unix_install_dir'] == 'aarch64-unix'
         and value['native_llvm_major'] == 15 and value['ownership_root'] == '.build/task7'
         and value['runtime_eligible'] is False and value['graphics_patch_status'] == 'unimplemented', 'config_selection')
    need(value['features'] == {k: False for k in ['enable_nvapi', 'enable_nvngx', 'enable_d3d12',
         'build_airconv_for_windows', 'enable_tests']} and type(value['max_jobs']) is int
         and 1 <= value['max_jobs'] <= 4 and all(type(v) is bool for v in value['features'].values()), 'config_features')
    need(value['source_accounting_gate'] == 'accounted_inventory'
         and value['shader_readiness_gate'] == 'available_tools_and_unperformed_capabilities'
         and value['source_terms_limit'] == SOURCE_TERMS_LIMIT, 'config_gate')
    return value


def validate_toolchain(value, repo=REPO):
    fields(value, TOOL_FIELDS, 'dxmt_toolchain_candidates')
    need(value['scope'] == 'dxmt_component' and value['installation_performed'] is False, 'toolchain_scope')
    ref = value['reused_wine_lock']
    fields(ref, ['path', 'sha256'])
    raw = read_relative(repo, ref['path'])
    need(digest(raw) == ref['sha256'], 'toolchain_wine_lock')
    original = decode_json(raw)
    need(value['llvm_mingw_archive'] == {k: original['artifacts'][0][k] for k in ['url', 'sha256', 'size_bytes']}, 'toolchain_archive')
    need(hex_digest(value['cache_manifest_sha256']) and hex_digest(value['cache_prepared_sha256']), 'toolchain_cache_pin')
    need(value['cross_tools'] == ['arm64ec-w64-mingw32-gcc', 'arm64ec-w64-mingw32-g++',
         'arm64ec-w64-mingw32-ar', 'arm64ec-w64-mingw32-strip', 'arm64ec-w64-mingw32-windres', 'clang-23'], 'cross_tool_selection')
    need(isinstance(value['candidates'], list) and len(value['candidates']) == 3 and {c['id'] for c in value['candidates']} == {'cmake', 'meson', 'ninja'}, 'tool_candidates')
    for candidate in value['candidates']:
        fields(candidate, ['id', 'origin', 'status', 'version', 'archive_sha256', 'checksum_origin', 'checksum_sha256']
               if candidate['id'] == 'cmake' else ['id', 'origin', 'status', 'version', 'commit'])
        if candidate['id'] == 'cmake':
            need(hex_digest(candidate['checksum_sha256']) and candidate['checksum_origin'].startswith('https://'), 'candidate_checksum')
        need(candidate['status'] == 'proposed_unacquired' and candidate['origin'].startswith('https://')
             and '@' not in candidate['origin'] and '?' not in candidate['origin'], 'tool_candidate_state')
        need(hex_digest(candidate.get('archive_sha256')) if candidate['id'] == 'cmake'
             else hex_digest(candidate.get('commit'), 40), 'tool_candidate_identity')
    need(value['metal_toolchain'] == {'status': 'unresolved', 'version': None,
         'reason': 'metal lookup alone does not establish functional compiler/metallib, platform compatibility or an acquired Metal toolchain.'}, 'metal_unqualified')
    need(value['sdk'] == original['sdk'], 'sdk_candidate')
    need(set(value['native_tool_paths']) == {'git', 'python', 'xcrun', 'xxd'}
         and all(isinstance(p, str) and Path(p).is_absolute() and '..' not in Path(p).parts
                 for p in value['native_tool_paths'].values()), 'native_tool_selection')
    return value


def file_fact(root, path, expected):
    relative(path)
    raw = read_relative(root, path, 64 * 1024 * 1024)
    need(digest(raw) == expected['sha256'] and len(raw) == expected['size_bytes'], 'role_file_digest')
    mode = (Path(root) / path).lstat().st_mode
    need(stat.S_ISREG(mode) and stat.S_IMODE(mode) == expected['mode'], 'role_file_mode')
    return {'path': path, 'sha256': digest(raw), 'size_bytes': len(raw), 'mode': stat.S_IMODE(mode)}


def inspect_wine_role(root, role, inputs):
    root = real_directory(root)
    raw = read_relative(root, 'build.json')
    ref = inputs['wine_baseline']['build_refs'][role]
    need(digest(raw) == ref['sha256'], 'wine_build_digest')
    build = decode_json(raw)
    need(build['record_kind'] == 'wine_build' and build['scope'] == 'wine_component'
         and build['passed'] is True and build['variant'] == ('arm64' if role == 'native' else 'arm64ec-build'), 'wine_role_variant')
    need(build['patch_series_sha256'] == inputs['wine_baseline']['patch_series']['sha256'], 'wine_role_patch_series')
    source_raw = read_relative(root, build['source_manifest']['path'])
    need(digest(source_raw) == build['source_manifest']['sha256'] == inputs['wine_baseline']['source_manifest_sha256'], 'wine_role_source')
    manifest_raw = read_relative(root, build['artifacts_manifest']['path'])
    need(digest(manifest_raw) == build['artifacts_manifest']['sha256'] == ref['installed_manifest_sha256'], 'wine_role_manifest')
    manifest = decode_json(manifest_raw)
    files = {r['path']: r for r in manifest['files']}
    need(len(files) == len(manifest['files']), 'wine_manifest_duplicates')
    install = real_directory(build['install_root'])
    need(install == root / 'install', 'wine_install_root')
    selected = ['bin/winebuild', 'lib/wine/aarch64-unix/ntdll.so', 'lib/wine/aarch64-unix/winemac.so']
    selected += ['lib/wine/aarch64-windows/lib' + n + '.a' for n in ['ntdll', 'winecrt0', 'dbghelp']]
    observed = []
    for path in selected:
        need(path in files, 'wine_role_file_missing')
        row = file_fact(install, path, files[path])
        if path.endswith('.a'):
            row.update(kind='coff_archive', raw_coff_machines=archive_machines(read_relative(install, path, 64 * 1024 * 1024)),
                       arm64ec_link_compatible='unperformed')
        else:
            slices = macho_slices(install / path)
            need(slices == [MACH_ARM64], 'wine_native_slice')
            row.update(kind='macho', architectures=slices)
        observed.append(row)
    return {'role': role, 'build_sha256': digest(raw), 'variant': build['variant'],
            'source_manifest_sha256': digest(source_raw), 'installed_manifest_sha256': digest(manifest_raw),
            'selected_files': observed, 'guest_execution': 'unperformed', 'pairing_verified': False}


def inspected_cache_member(install, files, name):
    path = 'bin/' + name
    need(path in files, 'cross_tool_missing')
    leaf = resolve_contained(install, path)
    current, seen, links = path, set(), []
    while 'symlink' in files[current]:
        need(current not in seen and len(seen) < 16, 'cross_link_cycle')
        seen.add(current)
        target = files[current]['symlink']
        need(os.readlink(install / current) == target and not target.startswith('/'), 'cross_link_changed')
        relative(target)
        links.append({'path': current, 'target': target})
        current = (Path(current).parent / target).as_posix()
        need(current in files, 'cross_link_unrecorded')
    row = files[current]
    observed = leaf.stat()
    need(stat.S_ISREG(observed.st_mode) and leaf == install / current
         and sha256(leaf) == row['sha256'] and observed.st_size == row['size_bytes'], 'cross_tool_digest')
    mode = stat.S_IMODE(observed.st_mode)
    # The pinned legacy #4 tool manifest has byte identities but no mode field.
    # Account for current mode separately; do not manufacture a historical pin.
    if 'mode' in row:
        need(type(row['mode']) is int and mode == row['mode'], 'cross_tool_digest')
    with leaf.open('rb') as stream:
        raw = stream.read(4096)
    fact = {'id': name, 'path': path, 'resolved_path': current, 'sha256': row['sha256'], 'links': links,
            'size_bytes': row['size_bytes'], 'mode': mode, 'executable_mode_observed': bool(mode & 0o111),
            'mode_baseline': 'manifest' if 'mode' in row else 'unavailable_in_legacy_manifest',
            'target_capability': 'unperformed'}
    if raw.startswith(b'#!'):
        need(raw.splitlines()[0] == b'#!/bin/sh', 'cross_script_interpreter')
        need(name in ['arm64ec-w64-mingw32-gcc', 'arm64ec-w64-mingw32-g++']
             and b'CLANG="$DIR/clang"\n' in raw, 'cross_script_driver')
        driver = inspected_cache_member(install, files, 'clang')
        need(driver['kind'] == 'macho' and driver['resolved_path'] == 'bin/clang-23', 'cross_wrapper_driver')
        fact.update(kind='shell_wrapper', interpreter='/bin/sh', native_wrapper_target='clang', wrapper_driver=driver)
    else:
        slices = macho_slices(leaf)
        need(MACH_ARM64 in slices, 'cross_native_slice')
        fact.update(kind='macho', architectures=slices)
    return fact


def inspect_cross_tools(root, toolchain):
    root = real_directory(root)
    prep_raw = read_relative(root, 'prepared.json')
    need(digest(prep_raw) == toolchain['cache_prepared_sha256'], 'cross_cache_prepared')
    prepared = decode_json(prep_raw)
    need(prepared['record_kind'] == 'wine_toolchain_prepared' and prepared['passed'] is True
         and prepared['lock_sha256'] == toolchain['reused_wine_lock']['sha256'], 'cross_cache_identity')
    artifact = next(r for r in prepared['artifacts'] if r['id'] == 'llvm-mingw')
    need(artifact['archive_sha256'] == toolchain['llvm_mingw_archive']['sha256'], 'cross_cache_archive')
    manifest_raw = read_relative(root, 'llvm-mingw-files.json')
    need(digest(manifest_raw) == artifact['files_manifest']['sha256'] == toolchain['cache_manifest_sha256'], 'cross_cache_manifest')
    manifest = decode_json(manifest_raw)
    files = {r['path']: r for r in manifest['files']}
    need(len(files) == len(manifest['files']), 'cross_cache_duplicates')
    install, observed = real_directory(root / 'llvm-mingw'), []
    for name in toolchain['cross_tools']:
        observed.append(inspected_cache_member(install, files, name))
    notices = []
    for row in artifact['notices']:
        raw = read_relative(install, row['path'])
        need(digest(raw) == row['sha256'] and len(raw) == row['size_bytes'], 'cross_notice_digest')
        notices.append({'path': row['path'], 'sha256': digest(raw), 'size_bytes': len(raw)})
    return {'prepared_sha256': digest(prep_raw), 'manifest_sha256': digest(manifest_raw),
            'selected_tools': observed, 'notices': notices, 'inspection_scope': 'selected_tools_and_notices',
            'compiler_target_capability': 'unperformed', 'runtime_eligible': False}


def selected_tool_files(toolchain, rows):
    """Read actual selected host/tool bytes without executing candidate tools."""
    requests = {**toolchain['native_tool_paths'], 'arch': '/usr/bin/arch', 'shell': '/bin/sh'}
    requests.update({r['id']: r['path'] for r in rows if r['path'] is not None})
    result = []
    for name, value in sorted(requests.items()):
        path = Path(value)
        need(path.is_absolute() and '..' not in path.parts and path.exists(), 'selected_tool_path')
        resolved = path.resolve(strict=True)
        need(resolved.is_file(), 'selected_tool_file')
        before = resolved.stat()
        with resolved.open('rb') as stream:
            prefix = stream.read(4096)
        content_digest = sha256(resolved)
        after = resolved.stat()
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'selected_tool_changed')
        row = {'id': name, 'path': str(path), 'resolved_path': str(resolved), 'sha256': content_digest,
               'size_bytes': after.st_size, 'mode': stat.S_IMODE(after.st_mode), 'capability': 'unperformed'}
        if prefix[:4] in [b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf']:
            slices = macho_slices(resolved)
            if name in toolchain['native_tool_paths'] or name in ['arch', 'shell']:
                need(MACH_ARM64 in slices, 'selected_tool_native_slice')
            row.update(kind='macho', architectures=slices)
        else:
            need(name not in toolchain['native_tool_paths'] and name not in ['arch', 'shell'], 'selected_tool_native_format')
            row.update(kind='script_or_other_unverified', architectures=None)
        result.append(row)
    return result


def save_probe(output, label, argv):
    result = run_bounded(argv, timeout=30, limit=65536)
    logs = output / 'probe-logs'
    logs.mkdir(exist_ok=True, mode=0o700)
    refs = {}
    for stream in ['stdout', 'stderr']:
        path = logs / (label + '.' + stream)
        with path.open('xb') as out:
            out.write(result.pop(stream))
        refs[stream] = {'path': path.relative_to(output).as_posix(), 'sha256': sha256(path), 'size_bytes': path.stat().st_size}
    result.update(refs)
    return result


def cross_probe_argv(tools_root, cross):
    """Choose explicit native shell invocation for inspected shebang wrappers."""
    selected = {row['id']: row for row in cross['selected_tools']}
    need(len(selected) == len(cross['selected_tools']), 'cross_probe_tool_set')
    requests = {}
    for name in ['arm64ec-w64-mingw32-gcc', 'arm64ec-w64-mingw32-g++', 'clang-23']:
        need(name in selected, 'cross_probe_tool_set')
        row = selected[name]
        path = str(Path(tools_root) / 'llvm-mingw/bin' / name)
        if row['kind'] == 'shell_wrapper':
            need(row['interpreter'] == '/bin/sh' and row['native_wrapper_target'] == 'clang'
                 and row['wrapper_driver']['kind'] == 'macho'
                 and row['wrapper_driver']['resolved_path'] == 'bin/clang-23', 'cross_probe_wrapper')
            requests[name + '-version'] = ['/usr/bin/arch', '-arm64', '/bin/sh', path, '--version']
        else:
            need(row['kind'] == 'macho', 'cross_probe_native')
            requests[name + '-version'] = ['/usr/bin/arch', '-arm64', path, '--version']
    return requests


def tool_observations(toolchain, tools_root, output, cross, run_probes=True):
    rows, commands = [], []
    for name in ['cmake', 'meson', 'ninja']:
        path = shutil.which(name)
        rows.append({'id': name, 'status': 'available_unverified' if path else 'unavailable',
                     'path': path, 'capability': 'unperformed', 'candidate_acquired': False})
    xcrun = toolchain['native_tool_paths']['xcrun']
    need(Path(xcrun).is_file(), 'xcrun_missing')
    # Version probes execute only approved developer tools, not fixture/guest code.
    if run_probes:
        for name, argv in [('git', ['/usr/bin/arch', '-arm64', toolchain['native_tool_paths']['git'], '--version']),
                           ('python', ['/usr/bin/arch', '-arm64', toolchain['native_tool_paths']['python'], '--version']),
                           ('sdk-version', ['/usr/bin/arch', '-arm64', xcrun, '--sdk', 'macosx', '--show-sdk-version']),
                           ('sdk-path', ['/usr/bin/arch', '-arm64', xcrun, '--sdk', 'macosx', '--show-sdk-path'])]:
            commands.append({'id': name, **save_probe(output, name, argv)})
        for name in ['metal', 'metallib']:
            cmd = save_probe(output, name + '-resolution', ['/usr/bin/arch', '-arm64', xcrun, '--sdk', 'macosx', '--find', name])
            raw = read_relative(output, cmd['stdout']['path'], 65536)
            text = raw.decode('utf-8', errors='strict').strip()
            usable = cmd['exit_code'] == 0 and Path(text).is_absolute() and Path(text).is_file()
            rows.append({'id': name, 'status': 'resolved_unverified' if usable else 'unavailable',
                         'path': text if usable else None, 'capability': 'unperformed', 'candidate_acquired': False})
            commands.append({'id': name + '-resolution', **cmd})
        for label, argv in cross_probe_argv(tools_root, cross).items():
            commands.append({'id': label, **save_probe(output, label, argv)})
        need(all(c['exit_code'] == 0 for c in commands if c['id'] not in ['metal-resolution', 'metallib-resolution']), 'tool_version_probe')
    return rows, commands


def readiness(tool_rows):
    need(isinstance(tool_rows, list) and len(tool_rows) == 5 and {r['id'] for r in tool_rows} == {'cmake', 'meson', 'ninja', 'metal', 'metallib'}, 'tool_observation_set')
    unavailable = [r['id'] for r in tool_rows if r['status'] == 'unavailable']
    # Stage 1 performs no compiler/shader capability test, even if paths resolve.
    for row in tool_rows:
        fields(row, ['id', 'status', 'path', 'capability', 'candidate_acquired'])
        need(row['status'] in ['available_unverified', 'resolved_unverified', 'unavailable']
             and row['capability'] == 'unperformed' and row['candidate_acquired'] is False, 'tool_observation_state')
        need((row['path'] is None) == (row['status'] == 'unavailable'), 'tool_observation_path')
    return {'shader_build_ready': False, 'unavailable_tools': sorted(unavailable),
            'unperformed_capabilities': ['native_llvm_15_headers_libraries', 'metal_compile', 'metallib_link',
                                         'dxmt_cross_compile', 'wine_arm64ec_import_link'],
            'reason': 'Required usable toolchain and actual compilation capabilities are not established in Stage 1.'}


def inventory(inputs_path, toolchain_path, config_path, prepared_path, wine_native, wine_companion, tools, output_value, repo=REPO):
    repo = real_directory(repo)
    refs, values = {}, {}
    for name, path in [('inputs', inputs_path), ('toolchain', toolchain_path), ('config', config_path)]:
        relative(path)
        raw = read_relative(repo, path)
        refs[name] = {'path': path, 'sha256': digest(raw)}
        values[name] = decode_json(raw)
    inputs = validate_inputs(values['inputs'], repo)
    toolchain = validate_toolchain(values['toolchain'], repo)
    validate_config(values['config'])
    prepared = verify_prepared(prepared_path, repo)
    need(prepared['inputs_ref'] == refs['inputs'], 'prepared_input_selection')
    roles = [inspect_wine_role(wine_native, 'native', inputs), inspect_wine_role(wine_companion, 'companion', inputs)]
    need(Path(wine_native).resolve() != Path(wine_companion).resolve(), 'wine_role_alias')
    cross = inspect_cross_tools(tools, toolchain)
    output = output_directory(output_value, repo)
    initial_host_files = selected_tool_files(toolchain, [])
    rows, commands = tool_observations(toolchain, tools, output, cross)
    all_tool_files = selected_tool_files(toolchain, rows)
    need(initial_host_files == [r for r in all_tool_files if r['id'] in {f['id'] for f in initial_host_files}], 'host_tools_changed_during_probes')
    storage = os.statvfs(output)
    result = {'schema_version': 1, 'record_kind': 'dxmt_stage1_inventory', 'scope': 'dxmt_component',
              'refs': refs, 'prepared_ref': {'path': str(Path(prepared_path).absolute()), 'sha256': sha256(Path(prepared_path) / 'prepared.json')},
              'local_roots': {'wine_native': str(real_directory(wine_native)), 'wine_companion': str(real_directory(wine_companion)),
                              'tools': str(real_directory(tools))},
              'producers': producer_hashes(repo), 'sources': prepared['components'], 'wine_roles': roles,
              'cross_tools': cross, 'tools': rows, 'tool_files': all_tool_files, 'commands': commands,
              'storage': {'free_bytes_observed': storage.f_bavail * storage.f_frsize,
                          'next_build_peak_bytes': None, 'next_build_admitted': False,
                          'reason': 'LLVM/DXMT peak budget is not measured by source-only Stage 1.'},
              'readiness': readiness(rows), 'inventory_complete': True, 'dxmt_built': False,
              'pairing_verified': False, 'runtime_eligible': False,
              'driver_pairing': {'status': 'needs_port', 'evidence_kind': 'pinned_source_inspection',
                 'reason': 'Private client-view structure mismatch, missing typed/exported interface and unverified lifetime/errors.'}}
    write_new(output / 'inventory.json', result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='operation', required=True)
    inv = sub.add_parser('inventory')
    for name in ['inputs', 'toolchain', 'config', 'prepared', 'wine-native', 'wine-companion', 'tools', 'output']:
        inv.add_argument('--' + name, required=True)
    inv.add_argument('--require-accounted', required=True, action='store_true')
    a = p.parse_args()
    try:
        v = inventory(a.inputs, a.toolchain, a.config, a.prepared, a.wine_native, a.wine_companion, a.tools, a.output)
        print(encoded({'inventory_complete': True, 'shader_build_ready': v['readiness']['shader_build_ready'],
                       'unavailable_tools': v['readiness']['unavailable_tools'], 'runtime_eligible': False}).decode(), end='')
        return 0
    except (Error, OSError, ValueError, KeyError, StopIteration, UnicodeError, subprocess.SubprocessError) as error:
        print(encoded({'inventory_complete': False, 'error': error.code if isinstance(error, Error) else 'inventory_failed',
                       'runtime_eligible': False}).decode(), end='')
        return 1

if __name__ == '__main__':
    sys.exit(main())
