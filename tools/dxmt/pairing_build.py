#!/usr/bin/env python3
"""Build the source-matched graphics pair; execution is a separate gate.

Reuse immutable Stage 3 input, Wine-role, tool, Meson and bounded-build readers.
Only the newly attributed exact graphics supplements alter the source.
"""
from __future__ import annotations
import argparse
import ast
import re
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from common import (REPO, Error, digest, encoded, fields, load_json, need,
                    owned_directory, output_directory, read_relative, real_directory,
                    sha256, write_new)
import build as stage3
import build_native
import pairing_source
import pairing_reuse
import pairing_monitor
import tools

PRODUCERS = ['tools/dxmt/pairing_build.py', 'tools/dxmt/pairing_source.py',
             'tools/dxmt/pairing_reuse.py', 'tools/dxmt/pairing_monitor.py', 'tools/wine/build.py', 'tools/wine/toolchain.py']


def source_baseline(wine_root):
    value = load_json(wine_root / 'build.json')
    ref = value['source_manifest']
    need(ref['sha256'] == pairing_source.BASES['wine']['prior_source_manifest_sha256'] and
         sha256(wine_root / ref['path']) == ref['sha256'], 'pair_wine_source_receipt')
    receipt = load_json(wine_root / ref['path'])
    need(receipt['symlinks'] == [], 'pair_wine_source_aliases')
    expected = [{key: row[key] for key in ['path', 'sha256', 'size_bytes', 'mode']}
                for row in receipt['files']]
    need(tools.files(wine_root / 'source') == expected, 'pair_wine_source_baseline')
    return value


def configuration_reader(wine_build):
    raw = read_relative(REPO, 'tools/wine/build.py', 1024**2)
    need(digest(raw) == wine_build['producer_sha256']['build.py'], 'pair_wine_configuration_reader_changed')
    tree = ast.parse(raw, filename='tools/wine/build.py')
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == 'observed_configuration']
    need(len(selected) == 1 and not selected[0].decorator_list, 'pair_wine_configuration_reader')
    namespace = {'Path': Path, 're': re, 'need': need}
    exec(compile(ast.Module(body=selected, type_ignores=[]), 'tools/wine/build.py', 'exec'), namespace)
    return namespace['observed_configuration']


def native_recipe(root, wine_build, wine_config, tool_root):
    objects = root / 'wine/objects'
    old = next(row for row in wine_build['commands'] if row['id'] == 'configure')['argv']
    need(old[:4] == ['/usr/bin/arch', '-arm64', '/bin/sh', '../source/configure'], 'pair_wine_configure_form')
    variant = next(row for row in wine_config['variants'] if row['id'] == 'arm64')
    args = ['/usr/bin/arch', '-arm64', '/bin/sh', '../source/configure', '--prefix=' + str(root / 'wine/install'),
            '--with-mingw=' + str(tool_root / 'llvm-mingw/bin/clang'), *variant['configure_args']]
    return {'wine.configure': (args, objects),
            'wine.driver': ([next(row['path'] for row in wine_config['_native_tools'] if row['id'] == 'make'), '-j2', 'dlls/winemac.drv/winemac.so',
                             'dlls/winemac.drv/aarch64-windows/winemac.drv'], objects)}


def wine_environment(root, wine_build, lock, tools_root):
    env = {'PATH': str(tools_root / 'llvm-mingw/bin') + ':/usr/bin:/bin:/usr/sbin:/sbin',
           'LANG': 'C', 'LC_ALL': 'C', 'SDKROOT': lock['sdk']['path'],
           'MACOSX_DEPLOYMENT_TARGET': lock['sdk']['version'],
           'PKG_CONFIG_PATH': '', 'PKG_CONFIG_LIBDIR': '/nonexistent/pear-task4',
           'TMPDIR': str(root / 'tmp')}
    if 'HOME' in os.environ:
        env['HOME'] = os.environ['HOME']
    # The retained build records commands/configuration; it has no environment
    # field. Reuse the exact source builder recipe and verify generated flags.
    env.setdefault('CC', next(row['path'] for row in lock['native_tools'] if row['id'] == 'clang'))
    env.setdefault('CXX', next(row['path'] for row in lock['native_tools'] if row['id'] == 'clang++'))
    # Keep the qualified 4 KiB Wine loader ABI policy and selected ARM64 target.
    env.setdefault('CFLAGS', '-arch arm64 -isysroot ' + lock['sdk']['path'])
    env.setdefault('CXXFLAGS', '-arch arm64 -isysroot ' + lock['sdk']['path'])
    env['BISON'] = str(tools_root / 'bison/bin/bison')
    env['PATH'] = str(tools_root / 'bison/bin') + ':' + env['PATH']
    env['FLEX'] = next(row['path'] for row in lock['native_tools'] if row['id'] == 'flex')
    return env


def artifact_rows(root):
    rows = []
    inspector = stage3.inspector()
    for path in ['wine/objects/dlls/winemac.drv/winemac.so',
                 'dxmt/objects/' + stage3.NATIVE_TARGET]:
        rows.append(inspector.inspect_native(root, path))
    for path in ['wine/objects/dlls/winemac.drv/aarch64-windows/winemac.drv'] + [
            'dxmt/objects/' + target for target in stage3.PE_TARGETS.values()] + [
            'fixtures/pear-metal-pairing-arm64.exe']:
        data = read_relative(root, path, 64 * 1024**2)
        PE, _ = inspector.pe_readers()
        pe = PE(data)
        need(pe.machine == 0xaa64 and pe.u('H', pe.opt) == 0x20b, 'pair_pe_target')
        facts = {'raw_coff_machine': pe.machine, 'imports': pe.imports(),
                 'exports': pe.exports(), 'load_config': pe.load_config()}
        if path.startswith('dxmt/'):
            facts = inspector.inspect_pe_bytes(data)
        rows.append({'path': path, 'sha256': digest(data), 'size_bytes': len(data),
                     'format_observation': facts})
    return rows


def construct(args):
    prior_root = owned_directory(args.artifact)
    prior = stage3.verify_build(prior_root)
    inputs, config, lock = stage3.input_values(prior['refs'])
    _, roots, role_ref = stage3.selector(prior['wine_roles_ref']['path'])
    prepared_root = owned_directory(prior['prepared_ref']['path'])
    prepared = stage3.verify_prepared(prepared_root)
    tools_root = owned_directory(prior['tools_ref']['path'])
    tool_record = tools.verify_tools(tools_root)
    native_root = owned_directory(prior['native_ref']['path'])
    native = build_native.verify_shader_build(native_root)
    wine_build = source_baseline(roots['native'])
    series_raw = read_relative(REPO, pairing_source.SERIES)
    series = load_json(REPO / pairing_source.SERIES)
    supplemental, changes = pairing_source.validate_series(series)
    policy = build_native.storage_policy(2, args.max_growth_bytes, args.reserve_free_bytes)
    need(shutil.disk_usage(REPO).free >= policy['growth_ceiling_bytes'] + policy['reserve_free_bytes'],
         'pair_build_storage_admission')
    root = output_directory(args.output)
    value = {'schema_version': 1, 'record_kind': 'dxmt_pairing_build',
             'scope': 'typed_native_metal_pairing', 'prior_artifact': stage3.reference(prior_root, 'build.json'),
             'series_sha256': digest(series_raw), 'supplemental_inputs': supplemental,
             'producers': {path: sha256(REPO / path) for path in PRODUCERS},
             'inherited_producers': stage3.producers(), 'role_reference': role_ref,
             'policy': policy, 'source': {}, 'commands': [], 'artifacts': [],
             'passed': False, 'pairing_verified': False, 'native_execution': False,
             'hybrid_execution': False, 'translated_guest_execution': False,
             'game_qualified': False, 'runtime_eligible': False}
    value['producer_files'] = {**value['inherited_producers'], **value['producers']}
    phase = 'source'
    try:
        for path, expected in value['producer_files'].items():
            raw = read_relative(REPO, path)
            need(digest(raw) == expected, 'pair_producer_snapshot_changed')
            stage3.write_bytes(root, 'producers/' + path, raw)
        for name in ['wine', 'wine/objects', 'dxmt', 'tmp', 'fixtures']:
            (root / name).mkdir(parents=True, exist_ok=True)
        for component, baseline in [('wine', roots['native'] / 'source'),
                                    ('dxmt', prior_root / 'source')]:
            before, after = pairing_source.project(baseline, root / component / 'source', *changes[component])
            value['source'][component] = {'baseline': str(baseline), 'before_files': before, 'after_files': after}
        wine_lock = load_json(REPO / 'runtime/wine/toolchain.json')
        wine_config = load_json(REPO / 'runtime/wine/build-config.json')
        phase = 'wine.tools.verify'
        value['wine_tools_ref'] = pairing_reuse.verify_wine_tools(roots['native'], wine_build, wine_lock)
        wine_tools_root = real_directory(value['wine_tools_ref']['path'])
        wine_config['_native_tools'] = wine_lock['native_tools']
        value['native_resolved_tools'] = []
        for row in wine_lock['native_tools']:
            declared = Path(row['path'])
            target = declared.resolve(strict=True)
            need(target.is_absolute() and target.is_file() and not target.is_symlink() and
                 sha256(target) == row['sha256'], 'pair_native_tool_changed')
            value['native_resolved_tools'].append({'id': row['id'], 'path': str(declared),
                'resolved_path': str(target), 'sha256': row['sha256']})
        holder = Path(tempfile.mkdtemp(prefix='pear-task7-pair-', dir='/private/tmp'))
        invocation = holder / 'output'
        invocation.symlink_to(root, target_is_directory=True)
        tool_alias = holder / 'wine-tools'
        tool_alias.symlink_to(wine_tools_root, target_is_directory=True)
        need(invocation.resolve() == root and tool_alias.resolve() == wine_tools_root, 'pair_owned_alias')
        value['path_aliases'] = {'output': str(invocation), 'tools': str(tool_alias), 'holder': str(holder)}
        wine_env = wine_environment(invocation, wine_build, wine_lock, tool_alias)
        value['wine_environment'] = wine_env
        for ident, (argv, cwd) in native_recipe(invocation, wine_build, wine_config, tool_alias).items():
            phase = ident
            pairing_monitor.monitored_command(root, ident, argv, wine_env, policy, value['commands'], cwd=cwd, timeout=1800)
            if ident == 'wine.configure':
                variant = next(row for row in wine_config['variants'] if row['id'] == 'arm64')
                value['wine_configuration'] = configuration_reader(wine_build)(
                    root / 'wine/objects/Makefile', variant, 'page-wx',
                    native_architecture_policy=True, source_policy='stable_relative_v1')
                value['wine_configuration_files'] = {name: sha256(root / 'wine/objects' / name)
                    for name in ['Makefile', 'config.log', 'include/config.h']}
        phase = 'fixture.compile'
        fixture = root / 'fixtures/pear-metal-pairing-arm64.exe'
        value['fixture_sources'] = {name: sha256(REPO / name) for name in
           ['tests/dxmt/pairing/' + leaf for leaf in ['pairing_pe.c', 'protocol.h',
             'pairing_native.m', 'pairing_control.c', 'upstream/winemetal.h',
             'upstream/winemetal_thunks.h']]}
        for name, expected in value['fixture_sources'].items():
            raw = read_relative(REPO, name)
            need(digest(raw) == expected, 'pair_fixture_snapshot_changed')
            stage3.write_bytes(root, 'inputs/' + name, raw)
        argv = [str(wine_tools_root / 'llvm-mingw/bin/clang'), '--target=aarch64-w64-windows-gnu',
                '-std=c11', '-Wall', '-Wextra', '-Werror', '-O1', '-fno-builtin', '-nostdlib',
                '-Wl,-e,mainCRTStartup', str(root / 'inputs/tests/dxmt/pairing/pairing_pe.c'),
                '-lkernel32', '-luser32', '-o', str(fixture)]
        pairing_monitor.monitored_command(root, phase, argv, wine_env, policy, value['commands'], timeout=60)
        dxroot = root / 'dxmt'
        (dxroot / 'tmp').mkdir()
        cap = load_json(Path(native['capabilities_ref']['path']) / 'capabilities.json')
        _, layout = stage3.role_layout(roots, inputs, lock)
        stage3.copy_layout(dxroot, layout, roots)
        rebuilt = root / 'wine/objects/dlls/winemac.drv/winemac.so'
        selected = dxroot / 'wine-layout/lib/wine/aarch64-unix/winemac.so'
        shutil.copyfile(rebuilt, selected)
        selected.chmod(rebuilt.stat().st_mode & 0o777)
        value['wine_layout'] = []
        for row in layout:
            if row['path'] == 'wine-layout/lib/wine/aarch64-unix/winemac.so':
                value['wine_layout'].append({'path': row['path'], 'sha256': sha256(selected),
                    'size_bytes': selected.stat().st_size, 'mode': selected.stat().st_mode & 0o777,
                    'origin_role': 'rebuilt-native',
                    'origin_path': 'wine/objects/dlls/winemac.drv/winemac.so'})
            else:
                value['wine_layout'].append(row)
        stage3.check_layout(dxroot, value['wine_layout'], value['wine_layout'])
        generated = stage3.generated_bytes(inputs, prepared, tools_root, tool_record, cap, roots)
        for name, (raw, mode) in generated.items():
            stage3.write_bytes(dxroot, name, raw, mode)
        value['generated_inputs'] = stage3.generated_facts(dxroot, generated)
        env = stage3.environment(dxroot, tools_root, tool_record)
        value['dxmt_environment'] = env
        for ident, argv in stage3.recipe(dxroot, tools_root, tool_record, Path(native['llvm_ref']['path']), 2).items():
            phase = ident
            if ident == 'builtin.' + next(iter(stage3.PE_TARGETS)):
                for name, target in stage3.PE_TARGETS.items():
                    stage3.write_bytes(dxroot, 'compiler/' + name, read_relative(dxroot, 'objects/' + target, 64 * 1024**2))
            pairing_monitor.monitored_command(root, ident, argv, env, policy, value['commands'], timeout=1800)
        value['artifacts'] = artifact_rows(root)
        need(all(sha256(REPO / name) == expected for name, expected in value['fixture_sources'].items()),
             'pair_fixture_changed_during_build')
        need(all(sha256(REPO / name) == expected for name, expected in value['producer_files'].items()),
             'pair_producer_changed_during_build')
        need(sha256(REPO / pairing_source.SERIES) == value['series_sha256'] and
             value['producers'] == {path: sha256(REPO / path) for path in PRODUCERS}, 'pair_inputs_changed_during_build')
        value['passed'] = True
        write_new(root / 'build.json', value)
        return value
    except (Error, OSError, ValueError, KeyError, UnicodeError, subprocess.SubprocessError) as error:
        value.update(phase=phase, error=getattr(error, 'code', type(error).__name__), passed=False)
        if isinstance(error, OSError):
            value['native_error'] = {'domain': 'posix_errno', 'code': error.errno, 'operation': phase}
        write_new(root / 'failed.json', value)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--max-growth-bytes', required=True, type=int)
    parser.add_argument('--reserve-free-bytes', required=True, type=int)
    parser.add_argument('--require-empty', required=True, action='store_true')
    try:
        construct(parser.parse_args())
        print(encoded({'pair_constructed': True, 'pairing_verified': False, 'runtime_eligible': False}).decode(), end='')
        return 0
    except (Error, OSError, ValueError, KeyError, UnicodeError, subprocess.SubprocessError) as error:
        print(encoded({'error': getattr(error, 'code', type(error).__name__)}).decode(), end='', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
