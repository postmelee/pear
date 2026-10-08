#!/usr/bin/env python3
"""Independently reread DXMT inventory bytes; no build or runtime execution."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import shutil
import subprocess
from common import (REPO, Error, decode_json, digest, encoded, fields, load_json, need, owned_directory,
                    producer_hashes, read_relative, sha256)
from prepare import validate_inputs, verify_prepared
from check import cross_probe_argv, inspect_cross_tools, inspect_wine_role, readiness, selected_tool_files, validate_config, validate_toolchain


def verify_inventory(root, repo=REPO):
    root = owned_directory(root, repo)
    value = load_json(root / 'inventory.json')
    fields(value, ['schema_version', 'record_kind', 'scope', 'refs', 'prepared_ref', 'local_roots', 'producers',
                  'sources', 'wine_roles', 'cross_tools', 'tools', 'tool_files', 'commands', 'storage', 'readiness',
                  'inventory_complete', 'dxmt_built', 'pairing_verified', 'runtime_eligible', 'driver_pairing'],
           'dxmt_stage1_inventory')
    need(value['scope'] == 'dxmt_component' and value['inventory_complete'] is True
         and all(value[k] is False for k in ['dxmt_built', 'pairing_verified', 'runtime_eligible']), 'inventory_scope')
    need(value['producers'] == producer_hashes(repo), 'producer_changed')
    need(set(value['refs']) == {'inputs', 'toolchain', 'config'}, 'inventory_references')
    values = {}
    for name, ref in value['refs'].items():
        fields(ref, ['path', 'sha256'])
        raw = read_relative(repo, ref['path'])
        need(digest(raw) == ref['sha256'], 'inventory_input_changed')
        values[name] = decode_json(raw)
    inputs = validate_inputs(values['inputs'], repo)
    toolchain = validate_toolchain(values['toolchain'], repo)
    validate_config(values['config'])
    prepared = verify_prepared(value['prepared_ref']['path'], repo)
    need(sha256(Path(value['prepared_ref']['path']) / 'prepared.json') == value['prepared_ref']['sha256']
         and prepared['inputs_ref'] == value['refs']['inputs'] and prepared['components'] == value['sources'], 'inventory_prepared_changed')
    roots = value['local_roots']
    need(set(roots) == {'wine_native', 'wine_companion', 'tools'}
         and roots['wine_native'] != roots['wine_companion'], 'inventory_roots')
    actual_roles = [inspect_wine_role(roots['wine_native'], 'native', inputs), inspect_wine_role(roots['wine_companion'], 'companion', inputs)]
    need(actual_roles == value['wine_roles'], 'wine_role_changed')
    need(inspect_cross_tools(roots['tools'], toolchain) == value['cross_tools'], 'cross_tools_changed')
    need(value['readiness'] == readiness(value['tools']), 'readiness_claim')
    need(value['tool_files'] == selected_tool_files(toolchain, value['tools']), 'selected_tool_files_changed')
    need(value['storage']['next_build_admitted'] is False and value['storage']['next_build_peak_bytes'] is None
         and type(value['storage']['free_bytes_observed']) is int and value['storage']['free_bytes_observed'] >= 0, 'storage_claim')
    need(value['driver_pairing'] == {'status': 'needs_port', 'evidence_kind': 'pinned_source_inspection',
         'reason': 'Private client-view structure mismatch, missing typed/exported interface and unverified lifetime/errors.'}, 'driver_claim')
    verify_probe_evidence(value, root, toolchain, roots)
    return value


def verify_probe_evidence(value, root, toolchain, roots):
    command_ids = ['git', 'python', 'sdk-version', 'sdk-path', 'metal-resolution', 'metallib-resolution',
                   'arm64ec-w64-mingw32-gcc-version', 'arm64ec-w64-mingw32-g++-version', 'clang-23-version']
    need([c['id'] for c in value['commands']] == command_ids, 'probe_set')
    expected_argv = {
        'git': ['/usr/bin/arch', '-arm64', toolchain['native_tool_paths']['git'], '--version'],
        'python': ['/usr/bin/arch', '-arm64', toolchain['native_tool_paths']['python'], '--version'],
        'sdk-version': ['/usr/bin/arch', '-arm64', toolchain['native_tool_paths']['xcrun'], '--sdk', 'macosx', '--show-sdk-version'],
        'sdk-path': ['/usr/bin/arch', '-arm64', toolchain['native_tool_paths']['xcrun'], '--sdk', 'macosx', '--show-sdk-path'],
        **{name + '-resolution': ['/usr/bin/arch', '-arm64', toolchain['native_tool_paths']['xcrun'], '--sdk', 'macosx', '--find', name] for name in ['metal', 'metallib']},
        **cross_probe_argv(roots['tools'], value['cross_tools'])
    }
    by_tool = {r['id']: r for r in value['tools']}
    for name in ['cmake', 'meson', 'ninja']:
        current = shutil.which(name)
        need(by_tool[name]['path'] == current and by_tool[name]['status'] == ('available_unverified' if current else 'unavailable'), 'tool_resolution_changed')
    for cmd in value['commands']:
        fields(cmd, ['id', 'argv', 'exit_code', 'timed_out', 'output_limit', 'elapsed_ms', 'stdout', 'stderr'])
        need(cmd['timed_out'] is False and cmd['output_limit'] is False and type(cmd['elapsed_ms']) is int
             and cmd['elapsed_ms'] >= 0 and type(cmd['exit_code']) is int, 'probe_outcome')
        need(cmd['argv'] == expected_argv[cmd['id']], 'probe_native_request')
        for stream in ['stdout', 'stderr']:
            ref = cmd[stream]
            fields(ref, ['path', 'sha256', 'size_bytes'])
            need(ref['path'] == 'probe-logs/' + cmd['id'] + '.' + stream, 'probe_log_path')
            raw = read_relative(root, ref['path'], 65536)
            need(digest(raw) == ref['sha256'] and len(raw) == ref['size_bytes'], 'probe_log_changed')
        if cmd['id'] not in ['metal-resolution', 'metallib-resolution']:
            need(cmd['exit_code'] == 0 and cmd['argv'][-1] in ['--version', '--show-sdk-version', '--show-sdk-path'], 'probe_result')
        stdout = read_relative(root, cmd['stdout']['path'], 65536).decode('utf-8', errors='strict').strip()
        if cmd['id'] in ['metal-resolution', 'metallib-resolution']:
            name = cmd['id'].removesuffix('-resolution')
            resolved = cmd['exit_code'] == 0 and Path(stdout).is_absolute() and Path(stdout).is_file()
            need(by_tool[name]['status'] == ('resolved_unverified' if resolved else 'unavailable')
                 and by_tool[name]['path'] == (stdout if resolved else None), 'metal_resolution_claim')
        elif cmd['id'] == 'sdk-version':
            need(stdout == toolchain['sdk']['version'], 'sdk_version_changed')
        elif cmd['id'] == 'sdk-path':
            path = Path(stdout)
            need(path.is_absolute() and '..' not in path.parts and path.is_dir()
                 and path.resolve(strict=True) == Path(toolchain['sdk']['path']).resolve(strict=True), 'sdk_path_changed')
        elif cmd['id'] == 'git':
            need(stdout.startswith('git version '), 'git_version_output')
        elif cmd['id'] == 'python':
            need(stdout.startswith('Python 3.'), 'python_version_output')
        else:
            need('23.1.1' in stdout, 'cross_version_output')


def gate_result(value, shader=False):
    need(value.get('inventory_complete') is True and value.get('runtime_eligible') is False, 'gate_scope')
    need(value['readiness'] == readiness(value['tools']), 'gate_readiness')
    return 3 if shader and not value['readiness']['shader_build_ready'] else 0


def public_observations(value):
    """An intentionally finite allowlist, without private roots or raw tool logs."""
    return {'schema_version': 1, 'record_kind': 'dxmt_stage1_observations', 'scope': 'dxmt_component',
            'inventory_complete': True, 'source_components': value['sources'],
            'wine_roles': [{'role': r['role'], 'build_sha256': r['build_sha256'], 'variant': r['variant'],
                           'source_manifest_sha256': r['source_manifest_sha256'],
                           'import_archive_machines': [f['raw_coff_machines'] for f in r['selected_files'] if f['kind'] == 'coff_archive']}
                          for r in value['wine_roles']],
            'tool_states': [{'id': r['id'], 'status': r['status'], 'capability': r['capability']} for r in value['tools']],
            'readiness': value['readiness'], 'dxmt_built': False, 'pairing_verified': False, 'runtime_eligible': False,
            'compilation_performed': False, 'gpu_or_guest_execution_performed': False,
            'disclosure': 'Private roots and probe streams withheld; source/tool/layout inventory only.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='operation', required=True)
    inv = sub.add_parser('inventory')
    inv.add_argument('--root', required=True)
    gates = inv.add_mutually_exclusive_group(required=True)
    gates.add_argument('--require-accounted', action='store_true')
    gates.add_argument('--require-shader-build-ready', action='store_true')
    shader=sub.add_parser('shader-tools')
    shader.add_argument('--root',required=True);shader.add_argument('--require-ready',action='store_true',required=True)
    native=sub.add_parser('native');native.add_argument('--root',required=True)
    native_gates=native.add_mutually_exclusive_group(required=True)
    native_gates.add_argument('--require-llvm',action='store_true');native_gates.add_argument('--require-complete',action='store_true')
    a = p.parse_args()
    try:
        if a.operation=='shader-tools':
            from check import verify_shader_capabilities
            value=verify_shader_capabilities(a.root)
            print(encoded({'shader_build_ready':value['shader_build_ready'],'gpu_or_guest_execution_performed':False,'runtime_eligible':False}).decode(),end='')
            return 0 if value['shader_build_ready'] else 3
        if a.operation=='native':
            from build_native import verify_llvm,verify_shader_build
            root=owned_directory(a.root);kind=load_json(root/'build.json').get('record_kind')
            need(kind in ['dxmt_llvm_native_build','dxmt_native_shader_build'],'native_build_record_kind')
            complete=kind=='dxmt_native_shader_build'
            (verify_shader_build if complete else verify_llvm)(root)
            print(encoded({'llvm_native_prerequisites':True,'shader_compilation_performed':complete,'stage2_complete':complete,'runtime_eligible':False}).decode(),end='')
            return 3 if a.require_complete and not complete else 0
        value = verify_inventory(a.root)
        status = gate_result(value, a.require_shader_build_ready)
        result = public_observations(value)
        result['requested_gate'] = 'shader_build_ready' if a.require_shader_build_ready else 'accounted_inventory'
        result['requested_gate_met'] = status == 0
        print(encoded(result).decode(), end='')
        return status
    except (Error, OSError, ValueError, KeyError, StopIteration, UnicodeError, subprocess.SubprocessError) as error:
        print(encoded({'inventory_complete': False, 'error': error.code if isinstance(error, Error) else 'verification_failed',
                       'runtime_eligible': False}).decode(), end='')
        return 1

if __name__ == '__main__':
    sys.exit(main())
