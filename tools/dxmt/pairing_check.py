#!/usr/bin/env python3
"""Replay the exact graphics build and inspect its native interface offline.

Source/build/static ABI evidence never establishes loader resolution, interface
invocation, physical lifetime, hybrid execution or qualified game support.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat
import struct
import sys

from common import (REPO, MACH_ARM64, Error, decode_json, digest, encoded, fields,
                    need, owned_directory, read_relative, real_directory,
                    relative, sha256, macho_slices)
import build as stage3
import build_native
import pairing_build as builder
import pairing_source
import pairing_reuse
import pairing_monitor
import tools

FIXTURE_PATHS = (
    'tests/dxmt/pairing/pairing_control.c',
    'tests/dxmt/pairing/pairing_native.m',
    'tests/dxmt/pairing/pairing_pe.c',
    'tests/dxmt/pairing/protocol.h',
    'tests/dxmt/pairing/upstream/winemetal.h',
    'tests/dxmt/pairing/upstream/winemetal_thunks.h',
)
BUILD_FIELDS = (
    'schema_version', 'record_kind', 'scope', 'prior_artifact', 'series_sha256',
    'supplemental_inputs', 'producers', 'inherited_producers', 'producer_files',
    'role_reference', 'policy', 'source', 'commands', 'artifacts', 'passed',
    'pairing_verified', 'native_execution', 'hybrid_execution',
    'translated_guest_execution', 'game_qualified', 'runtime_eligible',
    'path_aliases', 'wine_configuration', 'wine_configuration_files',
    'fixture_sources', 'wine_environment', 'dxmt_environment', 'wine_layout',
    'wine_tools_ref', 'generated_inputs',
    'native_resolved_tools',
)
RUNTIME_FLAGS = ('pairing_verified', 'native_execution', 'hybrid_execution',
                 'translated_guest_execution', 'game_qualified', 'runtime_eligible')
GETTER = '_pear_macdrv_metal_v1_get_interface'
REBUILT_DRIVER = 'wine/objects/dlls/winemac.drv/winemac.so'
REBUILT_PE = 'wine/objects/dlls/winemac.drv/aarch64-windows/winemac.drv'
FIXTURE_PE = 'fixtures/pear-metal-pairing-arm64.exe'


def record(value):
    fields(value, BUILD_FIELDS, 'dxmt_pairing_build')
    need(value['scope'] == 'typed_native_metal_pairing' and value['passed'] is True
         and all(value[name] is False for name in RUNTIME_FLAGS), 'pair_build_scope')
    return value


def equal_facts(left, right, code):
    """JSON booleans must never compare equal to integer format/mode facts."""
    need(encoded(left) == encoded(right), code)


def producer_copies(root, value, repo=REPO):
    current = {path: digest(read_relative(repo, path)) for path in builder.PRODUCERS}
    inherited = stage3.producers(repo)
    equal_facts(value['producers'], current, 'pair_producer_changed')
    equal_facts(value['inherited_producers'], inherited, 'pair_inherited_producer_changed')
    combined = dict(inherited)
    for path, sha in current.items():
        need(path not in combined or combined[path] == sha, 'pair_producer_conflict')
        combined[path] = sha
    equal_facts(value['producer_files'], combined, 'pair_producer_file_set')
    for path, sha in combined.items():
        relative(path)
        raw = read_relative(root, 'producers/' + path)
        need(digest(raw) == sha, 'pair_producer_snapshot_changed')
    snapshots = tools.files(root / 'producers')
    need({row['path'] for row in snapshots} == set(combined) and
         all(row['mode'] == 0o644 for row in snapshots), 'pair_producer_snapshot_set')


def wine_inputs(wine_build, repo=REPO):
    result = {}
    for name, path, key in [
        ('inputs', 'runtime/wine/inputs.json', 'inputs_sha256'),
        ('lock', 'runtime/wine/toolchain.json', 'toolchain_lock_sha256'),
        ('config', 'runtime/wine/build-config.json', 'config_sha256'),
    ]:
        raw = read_relative(repo, path)
        need(digest(raw) == wine_build[key], 'pair_wine_record_changed')
        result[name] = decode_json(raw)
    return result['lock'], result['config']


def external_native_tools(lock):
    """Resolve only exact external locked tools, retaining original argv paths."""
    rows = lock['native_tools']
    need(type(rows) is list and len({row.get('id') for row in rows}) == len(rows),
         'pair_native_tool_set')
    observed = []
    for row in rows:
        path = Path(row['path'])
        need(path.is_absolute() and '..' not in path.parts, 'pair_native_tool_path')
        resolved = path.resolve(strict=True)
        need(resolved.is_file() and sha256(resolved) == row['sha256']
             and MACH_ARM64 in macho_slices(resolved), 'pair_native_tool_changed')
        observed.append({'id': row['id'], 'path': str(path),
                         'resolved_path': str(resolved), 'sha256': row['sha256']})
    return observed


def fixture_copies(root, value, repo=REPO):
    expected = {name: digest(read_relative(repo, name)) for name in FIXTURE_PATHS}
    equal_facts(value['fixture_sources'], expected, 'pair_fixture_source_set')
    for path, sha in expected.items():
        need(digest(read_relative(root, 'inputs/' + path)) == sha,
             'pair_fixture_copy_changed')
    inspector = stage3.inspector()
    expected_files = sorted('inputs/' + path for path in FIXTURE_PATHS)
    rows = tools.files(root / 'inputs')
    need(sorted('inputs/' + row['path'] for row in rows) == expected_files and
         all(row['mode'] == 0o644 for row in rows),
         'pair_fixture_copy_set')
    # Pinned DXMT declarations must equal the actual selected source headers.
    for name in ['winemetal.h', 'winemetal_thunks.h']:
        need(read_relative(root, 'inputs/tests/dxmt/pairing/upstream/' + name) ==
             read_relative(root, 'dxmt/source/src/winemetal/' + name),
             'pair_fixture_upstream_header_changed')
    return inspector


def source_projection(root, component, baseline, facts, changes):
    fields(facts, ['baseline', 'before_files', 'after_files'])
    need(facts['baseline'] == str(baseline), 'pair_source_baseline_reference')
    before = tools.files(baseline)
    equal_facts(facts['before_files'], before, 'pair_source_preimage_inventory')
    declared, sections = changes
    expected = {row['path']: dict(row) for row in before}
    need(len(expected) == len(before), 'pair_source_duplicate')
    for change in declared:
        path = change['path']
        if change['before_sha256'] is None:
            need(path not in expected, 'pair_source_added_preimage')
            original = None
        else:
            need(path in expected and expected[path]['sha256'] == change['before_sha256'],
                 'pair_source_preimage')
            original = read_relative(baseline, path, 32 * 1024**2)
            need(digest(original) == change['before_sha256'], 'pair_source_preimage')
        projected = pairing_source.apply_hunks(original, sections[path], path)
        need(digest(projected) == change['after_sha256'], 'pair_source_postimage')
        expected[path] = {'path': path, 'sha256': digest(projected),
                          'size_bytes': len(projected), 'mode': 0o644}
    after = tools.files(root / component / 'source')
    equal_facts(after, sorted(expected.values(), key=lambda row: row['path']),
                'pair_source_full_projection')
    equal_facts(facts['after_files'], after, 'pair_source_record_changed')


def alias_paths(root, facts, wine_tools_root):
    fields(facts, ['output', 'tools', 'holder'])
    holder = real_directory(facts['holder'])
    need(holder.parent == Path('/private/tmp') and
         holder.name.startswith('pear-task7-pair-') and len(holder.name) <= 128,
         'pair_alias_holder')
    output, selected = holder / 'output', holder / 'wine-tools'
    need(facts['output'] == str(output) and facts['tools'] == str(selected)
         and output.is_symlink() and selected.is_symlink()
         and output.resolve() == root and selected.resolve() == wine_tools_root
         and {path.name for path in holder.iterdir()} == {'output', 'wine-tools'},
         'pair_alias_changed')
    return output, selected


def command_rows(root, commands, recipes, policy):
    need(type(commands) is list and [row.get('id') for row in commands] == list(recipes),
         'pair_command_set')
    for row in commands:
        fields(row, ['id', 'argv', 'cwd', 'environment', 'exit_code', 'elapsed_ms',
                     'stop_reason', 'growth_bytes_observed', 'logs'])
        argv, cwd, env, timeout = recipes[row['id']]
        need(row['argv'] == [str(arg) for arg in argv] and row['cwd'] == str(cwd)
             and row['environment'] == env and type(row['exit_code']) is int
             and row['exit_code'] == 0 and row['stop_reason'] is None
             and type(row['elapsed_ms']) is int and 0 <= row['elapsed_ms'] <= timeout * 1000 + 10000
             and type(row['growth_bytes_observed']) is int
             and 0 <= row['growth_bytes_observed'] <= policy['growth_ceiling_bytes'],
             'pair_command_recipe')
        fields(row['logs'], ['stdout', 'stderr'])
        total = 0
        for stream, ref in row['logs'].items():
            fields(ref, ['path', 'sha256', 'size_bytes'])
            need(ref['path'] == 'logs/' + row['id'] + '/' + stream
                 and type(ref['size_bytes']) is int and 0 <= ref['size_bytes'] <= 32 * 1024**2,
                 'pair_command_log_path')
            raw = read_relative(root, ref['path'], 32 * 1024**2)
            need(digest(raw) == ref['sha256'] and len(raw) == ref['size_bytes'],
                 'pair_command_log_changed')
            total += len(raw)
        need(total <= 32 * 1024**2, 'pair_command_log_bound')


def read_uleb(data, offset, end):
    value = 0
    for index in range(10):
        need(offset < end, 'pair_export_uleb_bounds')
        byte = data[offset]; offset += 1
        need(index < 9 or byte < 2, 'pair_export_uleb_overflow')
        value |= (byte & 0x7f) << (7 * index)
        if not byte & 0x80:
            need(index == 0 or byte != 0, 'pair_export_uleb_nonminimal')
            return value, offset
    raise Error('pair_export_uleb_overflow')


def export_terminal(data, wanted):
    """Resolve one exact symbol through a bounded native dyld export trie."""
    need(type(data) is bytes and len(data) >= 32 and data[:4] == b'\xcf\xfa\xed\xfe'
         and struct.unpack_from('<I', data, 4)[0] == MACH_ARM64
         and struct.unpack_from('<I', data, 12)[0] == 6, 'pair_getter_native_target')
    count, span = struct.unpack_from('<II', data, 16)
    need(count <= 65536 and 32 + span <= len(data), 'pair_export_commands')
    at, end, references = 32, 32 + span, []
    for _ in range(count):
        need(at + 8 <= end, 'pair_export_commands')
        command, size = struct.unpack_from('<II', data, at)
        need(size >= 8 and size % 4 == 0 and at + size <= end, 'pair_export_command_bounds')
        if command in [0x22, 0x80000022]:
            need(size == 48, 'pair_export_info_shape')
            offset, length = struct.unpack_from('<II', data, at + 40)
            if length: references.append((offset, length))
        elif command == 0x80000033:
            need(size == 16, 'pair_export_trie_shape')
            references.append(struct.unpack_from('<II', data, at + 8))
        at += size
    need(at == end and len(set(references)) == 1, 'pair_getter_export_trie_missing')
    offset, length = references[0]
    need(0 < length <= 32 * 1024**2 and offset >= end and offset + length <= len(data),
         'pair_export_trie_bounds')
    trie, node, consumed, visited = data[offset:offset + length], 0, 0, set()
    for _ in range(128):
        need(node not in visited and 0 <= node < len(trie), 'pair_export_trie_cycle')
        visited.add(node)
        terminal, position = read_uleb(trie, node, len(trie))
        terminal_end = position + terminal
        need(terminal_end < len(trie), 'pair_export_terminal_bounds')
        if consumed == len(wanted):
            need(terminal > 0, 'pair_getter_not_exported')
            flags, position = read_uleb(trie, position, terminal_end)
            need(flags == 0, 'pair_getter_export_kind')
            address, position = read_uleb(trie, position, terminal_end)
            need(position == terminal_end and address > 0, 'pair_getter_export_address')
            return {'name': wanted, 'kind': 'regular_defined', 'exported': True}
        child_count, position = trie[terminal_end], terminal_end + 1
        matches, edges = [], set()
        for _ in range(child_count):
            stop = trie.find(b'\0', position)
            need(stop > position and stop - position <= 4096, 'pair_export_edge_bounds')
            edge = trie[position:stop]
            need(edge not in edges and all(32 <= char < 127 for char in edge), 'pair_export_edge_duplicate')
            edges.add(edge)
            child, position = read_uleb(trie, stop + 1, len(trie))
            need(0 <= child < len(trie), 'pair_export_child_bounds')
            if wanted[consumed:].encode('ascii').startswith(edge):
                matches.append((child, len(edge)))
        need(len(matches) == 1, 'pair_getter_not_exported')
        node, taken = matches[0]; consumed += taken
    raise Error('pair_export_trie_depth')


def ordinary_pe(data, executable, inspector, repo=REPO):
    PE, _ = inspector.pe_readers(repo)
    pe = PE(data)
    need(pe.machine == 0xaa64 and pe.u('H', pe.opt) == 0x20b
         and bool(pe.u('H', pe.pe + 22) & 0x2000) is (not executable),
         'pair_ordinary_pe_target')
    config = pe.load_config()
    need(config['chpe_pointer'] == '0x0' and config['arm64x_machine_fixups'] == []
         and not config.get('chpe'), 'pair_ordinary_pe_hybrid')
    exports = pe.exports()
    if executable:
        need(pe.u('I', pe.opt + 16) > 0 and
             {name.casefold() for name in pe.imports()} == {'kernel32.dll', 'user32.dll'}
             and not pe.imports(True), 'pair_fixture_pe_scope')
    else:
        selected = [row for row in exports if row['name'] == 'PearMetalPairingControl']
        need(len(selected) == 1 and selected[0]['rva'] > 0 and 'forwarder' not in selected[0],
             'pair_control_export_missing')
    return {'raw_coff_machine': pe.machine, 'optional_magic': 0x20b,
            'hybrid_metadata_present': False, 'imports': pe.imports(),
            'delay_imports': pe.imports(True), 'exports': exports,
            'windows_runtime_resolution': 'unperformed'}


def paired_layout(root, rows, expected, inspector):
    need(type(rows) is list and len(rows) == len(expected), 'pair_layout_set')
    observed, counterparts = [], {}
    mapped = {row.get('path'): row for row in rows}
    need(len(mapped) == len(rows) and set(mapped) == {row['path'] for row in expected}, 'pair_layout_set')
    need({'wine-layout/' + row['path'] for row in tools.files(root / 'dxmt/wine-layout')} == set(mapped),
         'pair_layout_file_set')
    for old in expected:
        path = old['path']; row = mapped[path]
        fields(row, ['path', 'sha256', 'size_bytes', 'mode', 'origin_role', 'origin_path'])
        if path.endswith('/winemac.so'):
            data, actual = inspector.file_bytes(root, REBUILT_DRIVER)
            need(row['origin_role'] == 'rebuilt-native' and row['origin_path'] == REBUILT_DRIVER,
                 'pair_layout_rebuilt_origin')
            expected_row = {**actual, 'path': path, 'origin_role': 'rebuilt-native',
                            'origin_path': REBUILT_DRIVER}
        else:
            expected_row = old
        equal_facts(row, expected_row, 'pair_layout_origin_changed')
        data, fact = inspector.file_bytes(root / 'dxmt', path)
        equal_facts(fact, {key: row[key] for key in fact}, 'pair_layout_changed')
        if path.endswith('.so'):
            info = inspector.inspect_native(root / 'dxmt', path)
            need(info['install_name'] == '@rpath/' + Path(path).name
                 and info['rpaths'] == ['@loader_path/'], 'pair_layout_native_search_path')
            counterparts[Path(path).name] = info
            observed.append({**info, 'origin_role': row['origin_role'], 'origin_path': row['origin_path']})
        elif path.endswith('.a'):
            need(inspector.archive_machines(data) == [0xa641, 0xaa64], 'pair_layout_import_architecture')
            observed.append({**fact, 'origin_role': row['origin_role'], 'origin_path': row['origin_path']})
        else:
            need(fact['mode'] == 0o755 and data[:4] == b'\xcf\xfa\xed\xfe'
                 and struct.unpack_from('<I', data, 4)[0] == MACH_ARM64
                 and struct.unpack_from('<I', data, 12)[0] == 2, 'pair_layout_native_tool')
            observed.append({**fact, 'origin_role': row['origin_role'], 'origin_path': row['origin_path']})
    for row in observed:
        if Path(row['path']).name in counterparts:
            row['dependency_closure'] = inspector.native_dependencies(row, counterparts)
    return sorted(observed, key=lambda row: row['path']), counterparts


def inspect_pair(root, value, repo=REPO, expected_layout=None):
    inspector = stage3.inspector()
    if expected_layout is None:
        prior = stage3.verify_build(owned_directory(value['prior_artifact']['path'], repo), repo=repo)
        inputs, _, lock = stage3.input_values(prior['refs'], repo)
        _, roots, _ = stage3.selector(prior['wine_roles_ref']['path'], repo)
        _, expected_layout = stage3.role_layout(roots, inputs, lock)
    layout, counterparts = paired_layout(root, value['wine_layout'], expected_layout, inspector)
    driver = inspector.inspect_native(root, REBUILT_DRIVER)
    driver['dependency_closure'] = inspector.native_dependencies(driver, counterparts)
    driver['required_export'] = export_terminal(read_relative(root, REBUILT_DRIVER, inspector.MAX_ARTIFACT), GETTER)
    need(driver['sha256'] == counterparts['winemac.so']['sha256'], 'pair_driver_layout_changed')
    ordinary = {}
    for path, executable in [(REBUILT_PE, False), (FIXTURE_PE, True)]:
        raw, fact = inspector.file_bytes(root, path)
        ordinary[path] = {**fact, 'format_observation': ordinary_pe(raw, executable, inspector, repo)}
    dxroot = root / 'dxmt'
    need(inspector.installed_paths(dxroot) == sorted(
        ['install/aarch64-windows/' + name for name in inspector.PE_PATHS] +
        ['install/aarch64-unix/winemetal.so']), 'pair_dxmt_install_set')
    pe = [inspector.inspect_pe_pair(dxroot, name, repo) for name in sorted(inspector.PE_PATHS)]
    bridge = inspector.inspect_native(dxroot, 'objects/' + inspector.NATIVE_PATH)
    installed = inspector.inspect_native(dxroot, 'install/aarch64-unix/winemetal.so')
    need(bridge['sha256'] == installed['sha256'] and bridge['size_bytes'] == installed['size_bytes']
         and bridge['install_name'] == '@rpath/winemetal.so'
         and bridge['rpaths'] == inspector.NATIVE_RPATHS
         and {'___wine_unix_call_funcs', '___wine_unix_call_wow64_funcs'}.issubset(bridge['external_defined_symbols']),
         'pair_dxmt_native_bridge')
    bridge['dependency_closure'] = inspector.native_dependencies(bridge, counterparts)
    prior = stage3.verify_build(owned_directory(value['prior_artifact']['path'], repo), repo=repo)
    generated = inspector.generated_inventory(dxroot, value)
    notices = inspector.notice_inventory(dxroot, prior, repo)
    need({row['path'] for row in notices}.issubset({row['path'] for row in generated}), 'pair_notices_omitted')
    template = read_relative(dxroot, 'source/version.h.in')
    version, version_fact = inspector.file_bytes(dxroot, 'objects/version.h')
    need(b'@VCS_TAG@' in template and version == template.replace(b'@VCS_TAG@', inspector.DXMT_COMMIT.encode()),
         'pair_version_header')
    return {'schema_version': 1, 'record_kind': 'dxmt_pairing_static_inventory',
            'scope': 'typed_native_metal_pairing', 'driver': driver,
            'ordinary_arm64_pe': ordinary, 'wine_layout': layout, 'pe_modules': pe,
            'native_bridge': {'built': bridge, 'installed': installed},
            'shader_outputs': inspector.shader_inventory(dxroot), 'version_header': version_fact,
            'generated_inputs': generated, 'notices': notices,
            'native_export_admission': True, 'runtime_loader_resolution': 'unperformed',
            'native_dependency_scope': 'static_source_bound_counterparts_and_system_names_only',
            'typed_interface_invocation': 'unperformed', 'physical_lifetime': 'unperformed',
            'pairing_verified': False, 'ordinary_arm64_pe_execution_performed': False,
            'gpu_execution_performed': False, 'hybrid_execution_performed': False,
            'translated_guest_execution_performed': False, 'game_qualified': False,
            'runtime_eligible': False, 'distribution_qualified': False}


def decode_pair_build(raw):
    # Exact before/after source inventories exceed the historical 250k-node
    # default. Keep the 8 MiB/depth/string rules and a finite local budget.
    return decode_json(raw, max_bytes=8 * 1024**2, max_nodes=300000)


def verify_build(root, repo=REPO):
    root = owned_directory(root, repo)
    need(not (root / 'failed.json').exists(), 'pair_failed_build')
    value = record(decode_pair_build(read_relative(root, 'build.json')))
    producer_copies(root, value, repo)
    fixture_copies(root, value, repo)
    fields(value['prior_artifact'], ['path', 'sha256'])
    prior_root = owned_directory(value['prior_artifact']['path'], repo)
    need(digest(read_relative(prior_root, 'build.json')) == value['prior_artifact']['sha256'], 'pair_prior_changed')
    prior = stage3.verify_build(prior_root, repo=repo)
    inputs, _, lock = stage3.input_values(prior['refs'], repo)
    _, roots, role_ref = stage3.selector(prior['wine_roles_ref']['path'], repo)
    equal_facts(value['role_reference'], role_ref, 'pair_roles_changed')
    wine_build = builder.source_baseline(roots['native'])
    wine_tools = real_directory(wine_build['tools_root'])
    fields(value['wine_tools_ref'], ['path', 'sha256'])
    need(value['wine_tools_ref']['path'] == str(wine_tools) and
         digest(read_relative(wine_tools, 'prepared.json')) == value['wine_tools_ref']['sha256'],
         'pair_wine_tools_changed')
    # The constructor's source-bound Wine adapter supplies legacy archive/build
    # proof; calling it never executes the admitted compiler or Bison.
    wine_lock, wine_config = wine_inputs(wine_build, repo)
    equal_facts(value['wine_tools_ref'],
                pairing_reuse.verify_wine_tools(roots['native'], wine_build, wine_lock),
                'pair_wine_toolchain_changed')
    series_raw = read_relative(repo, pairing_source.SERIES)
    need(digest(series_raw) == value['series_sha256'], 'pair_series_changed')
    supplemental, changes = pairing_source.validate_series(decode_json(series_raw), repo)
    equal_facts(value['supplemental_inputs'], supplemental, 'pair_supplemental_changed')
    need(set(value['source']) == {'wine', 'dxmt'}, 'pair_source_component_set')
    for component, baseline in [('wine', roots['native'] / 'source'), ('dxmt', prior_root / 'source')]:
        source_projection(root, component, baseline, value['source'][component], changes[component])
    equal_facts(value['native_resolved_tools'], external_native_tools(wine_lock),
                'pair_native_tool_resolution_changed')
    wine_config['_native_tools'] = wine_lock['native_tools']
    invocation, tool_alias = alias_paths(root, value['path_aliases'], wine_tools)
    wine_env = builder.wine_environment(invocation, wine_build, wine_lock, tool_alias)
    equal_facts(value['wine_environment'], wine_env, 'pair_wine_environment_changed')
    prepared_root = owned_directory(prior['prepared_ref']['path'], repo)
    prepared = stage3.verify_prepared(prepared_root)
    tools_root = owned_directory(prior['tools_ref']['path'], repo)
    tool_record = tools.verify_tools(tools_root)
    native = build_native.verify_shader_build(owned_directory(prior['native_ref']['path'], repo), repo=repo)
    cap = decode_json(read_relative(owned_directory(native['capabilities_ref']['path'], repo), 'capabilities.json'))
    env = stage3.environment(root / 'dxmt', tools_root, tool_record)
    equal_facts(value['dxmt_environment'], env, 'pair_dxmt_environment_changed')
    expected_generated = stage3.generated_bytes(inputs, prepared, tools_root, tool_record, cap, roots)
    equal_facts(value['generated_inputs'], stage3.generated_facts(root / 'dxmt', expected_generated),
                'pair_generated_changed')
    policy = value['policy']
    equal_facts(policy, build_native.storage_policy(policy['jobs'], policy['growth_ceiling_bytes'],
                                                   policy['reserve_free_bytes']), 'pair_policy_changed')
    need(policy['jobs'] == 2 and policy['growth_ceiling_bytes'] <= 8 * 1024**3
         and policy['reserve_free_bytes'] >= 4 * 1024**3, 'pair_policy_scope')
    recipes = {name: (argv, cwd, wine_env, 1800)
               for name, (argv, cwd) in builder.native_recipe(invocation, wine_build, wine_config, tool_alias).items()}
    fixture = root / FIXTURE_PE
    recipes['fixture.compile'] = ([str(wine_tools / 'llvm-mingw/bin/clang'), '--target=aarch64-w64-windows-gnu',
        '-std=c11', '-Wall', '-Wextra', '-Werror', '-O1', '-fno-builtin', '-nostdlib',
        '-Wl,-e,mainCRTStartup', str(root / 'inputs/tests/dxmt/pairing/pairing_pe.c'),
        '-lkernel32', '-luser32', '-o', str(fixture)], root, wine_env, 60)
    for name, argv in stage3.recipe(root / 'dxmt', tools_root, tool_record, Path(native['llvm_ref']['path']), 2).items():
        recipes[name] = (argv, root, env, 1800)
    command_rows(root, value['commands'], recipes, policy)
    variant = next(row for row in wine_config['variants'] if row['id'] == 'arm64')
    actual_config = builder.configuration_reader(wine_build)(root / 'wine/objects/Makefile', variant, 'page-wx',
        native_architecture_policy=True, source_policy='stable_relative_v1')
    equal_facts(value['wine_configuration'], actual_config, 'pair_wine_configuration_changed')
    equal_facts(value['wine_configuration_files'], {name: sha256(root / 'wine/objects' / name)
        for name in ['Makefile', 'config.log', 'include/config.h']}, 'pair_wine_configuration_files_changed')
    equal_facts(value['artifacts'], builder.artifact_rows(root), 'pair_artifact_record_changed')
    _, layout = stage3.role_layout(roots, inputs, lock)
    inspect_pair(root, value, repo=repo, expected_layout=layout)
    # Replay the same closed generated locale-link exception independently.
    # No source/output directory alias or other special leaf is admitted.
    pairing_monitor.directory_usage(root)
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', required=True)
    parser.add_argument('--require-native-abi', required=True, action='store_true')
    args = parser.parse_args(argv)
    try:
        root = owned_directory(args.artifact)
        value = verify_build(root)
        facts = inspect_pair(root, value)
        print(encoded({'scope': facts['scope'], 'build_replayed': True,
            'native_export_admission': True, 'pe_module_count': len(facts['pe_modules']),
            'pairing_verified': False, 'runtime_loader_resolution': 'unperformed',
            'typed_interface_invocation': 'unperformed', 'physical_lifetime': 'unperformed',
            'runtime_eligible': False}).decode(), end='')
        return 0
    except (Error, OSError, ValueError, KeyError, TypeError, struct.error) as error:
        print(encoded({'build_replayed': False, 'pairing_verified': False, 'runtime_eligible': False,
            'error': getattr(error, 'code', 'pair_build_read_failed')}).decode(), end='', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
