#!/usr/bin/env python3
"""Inspect and replay DXMT component artifacts without loading native or guest code.

The selected Wine PE reader is reused unchanged, without its native-view wrapper.
Construction provenance is replayed separately by the Stage 3 builder. Static
linkage closure does not establish the missing driver interface or runtime use.
"""
from __future__ import annotations
import argparse
import ast
import importlib.util
import os
from pathlib import Path
import re
import stat
import struct
import sys
from common import (REPO, MACH_ARM64, Error, archive_machines, decode_json, digest,
                    encoded, need, open_relative, owned_directory, read_relative,
                    real_directory, relative)
import tools

MAX_ARTIFACT = 128 * 1024**2
PE_READER_SHA = 'ee109f7934562082a4ed74c7c6f90beec75445adff042e2b8b9e82fef086225c'
DXMT_COMMIT = '7c8dee1c2d73415301ceb7d1fa810861cef4cd67'
BUILTIN_MARKER = b'Wine builtin DLL'.ljust(32, b'\0')
PE_PATHS = {'d3d11.dll': 'src/d3d11/d3d11.dll', 'dxgi.dll': 'src/dxgi/dxgi.dll',
            'd3d10core.dll': 'src/d3d10/d3d10core.dll', 'winemetal.dll': 'src/winemetal/winemetal.dll'}
DEFS = {'d3d11.dll': 'src/d3d11/d3d11.def', 'dxgi.dll': 'src/dxgi/dxgi.def',
        'd3d10core.dll': 'src/d3d10/d3d10core.def'}
WINEMETAL_EXPORTS = {'NSObject_retain', 'NSObject_release', 'WMTCopyAllDevices',
                    'CreateMetalViewFromHWND', 'ReleaseMetalView', 'SM50Initialize', 'SM50Compile'}
NATIVE_PATH = 'src/winemetal/unix/winemetal.so'
NATIVE_RPATHS = ['@loader_path/', '@loader_path/../../']
WINE_LAYOUT = {'wine-layout/bin/winebuild': 'native',
               **{'wine-layout/lib/wine/aarch64-windows/'+n: 'companion'
                  for n in ['libwinecrt0.a', 'libntdll.a', 'libdbghelp.a']},
               **{'wine-layout/lib/wine/aarch64-unix/'+n: 'native'
                  for n in ['ntdll.so', 'winemac.so', 'win32u.so']}}
NOTICE_IDS = {'dxmt-upstream', 'dxmt-directx', 'llvm-dxmt', 'wine-upstream',
              'llvm-mingw-source', 'llvm-mingw-llvm', 'mingw-w64-source'}


def load_local(path, alias):
    """Load a reviewed local helper without stdlib/package-name collisions."""
    spec = importlib.util.spec_from_file_location(alias, path)
    need(spec is not None and spec.loader is not None, 'artifact_helper')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pe_readers(repo=REPO):
    data = read_relative(repo, 'tools/wine/modules.py', 1024**2)
    need(digest(data) == PE_READER_SHA, 'artifact_pe_reader_identity')
    tree = ast.parse(data, filename='tools/wine/modules.py')
    selected = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))
                and node.name in ['PE', 'require_hybrid']]
    need(len(selected) == 2 and isinstance(selected[0], ast.ClassDef) and selected[0].name == 'PE'
         and isinstance(selected[1], ast.FunctionDef) and selected[1].name == 'require_hybrid'
         and all(not node.decorator_list for node in selected), 'artifact_pe_reader_definitions')
    namespace = {'__name__': '_pear_dxmt_pe_reader', 'need': need, 'Error': Error,
                 'struct': struct, 'MAX_PE': 64 * 1024**2}
    exec(compile(ast.Module(body=selected, type_ignores=[]), 'tools/wine/modules.py', 'exec'), namespace)
    return namespace['PE'], namespace['require_hybrid']


def file_bytes(root, path, limit=MAX_ARTIFACT):
    """Bind bytes, mode and metadata through one non-following descriptor."""
    fd = open_relative(root, path)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_size <= limit, 'artifact_file_bounds')
        with os.fdopen(os.dup(fd), 'rb') as stream:
            data = stream.read(limit + 1)
        after = os.fstat(fd)
        identity = lambda value: (value.st_dev, value.st_ino, value.st_mode, value.st_size,
                                  value.st_mtime_ns, value.st_ctime_ns)
        need(identity(before) == identity(after) and len(data) == before.st_size, 'artifact_changed')
        mode = stat.S_IMODE(before.st_mode)
        need(mode in [0o644, 0o755], 'artifact_mode')
        return data, {'path': path, 'sha256': digest(data), 'size_bytes': len(data), 'mode': mode}
    finally:
        os.close(fd)


def imports_policy(names):
    need(len(names) <= 1024 and len({name.casefold() for name in names}) == len(names), 'artifact_import_duplicate')
    need(all(re.fullmatch(r'[A-Za-z0-9_.-]+\.dll', name, re.I) for name in names), 'artifact_import_name')
    return [{'name': name, 'kind': 'dxmt_component_dependency' if name.casefold() in PE_PATHS
             else 'external_windows_api_or_crt_dependency', 'runtime_resolution': 'unperformed'} for name in names]


def inspect_pe_bytes(data, repo=REPO):
    PE, require_hybrid = pe_readers(repo)
    pe = PE(data)
    need(pe.machine == 0xaa64, 'artifact_outer_machine')
    need(pe.u('H', pe.pe + 22) & 0x2000, 'artifact_not_dll')
    facts = {'raw_coff_machine': pe.machine, 'machine': pe.machine, 'optional_magic': 0x20b,
             'entrypoint_rva': pe.u('I', pe.opt + 16), 'image_base': hex(pe.base),
             'sections': pe.sections, 'imports': pe.imports(), 'delay_imports': pe.imports(True),
             'exports': pe.exports(), 'load_config': pe.load_config()}
    require_hybrid(facts)
    facts['hybrid_metadata_verified'] = True
    facts['alternate_view_machine'] = 0x8664
    facts['classification_basis'] = 'raw_arm64_outer_header_with_chpe_and_arm64x_dynamic_relocation'
    facts['import_dependencies'] = imports_policy(facts['imports'])
    facts['delay_import_dependencies'] = imports_policy(facts['delay_imports'])
    return facts


def definition_exports(data):
    try:
        text = data.decode('ascii')
    except UnicodeError:
        raise Error('artifact_definition_encoding') from None
    rows, in_exports = {}, False
    for line in text.splitlines():
        line = line.split(';', 1)[0].strip()
        if not line:
            continue
        if line.upper().startswith('LIBRARY '):
            need(not in_exports, 'artifact_definition_shape')
            continue
        if line == 'EXPORTS':
            need(not in_exports, 'artifact_definition_shape')
            in_exports = True
            continue
        match = re.fullmatch(r'([A-Za-z_][A-Za-z0-9_]*)(?:\s+@([0-9]+))?', line)
        need(in_exports and match and match[1] not in rows, 'artifact_definition_shape')
        rows[match[1]] = int(match[2]) if match[2] else None
    need(rows, 'artifact_definition_empty')
    return rows


def check_exports(name, facts, root):
    present = [row for row in facts['exports'] if row['rva']]
    need(len({row['name'] for row in present}) == len(present)
         and all(row['name'] and 'forwarder' not in row for row in present), 'artifact_export_shape')
    by_name = {row['name']: row for row in present}
    if name in DEFS:
        wanted = definition_exports(read_relative(root, 'source/'+DEFS[name], 1024**2))
        need(set(by_name) == set(wanted), 'artifact_definition_exports')
        need(all(ordinal is None or by_name[key]['ordinal'] == ordinal for key, ordinal in wanted.items()),
             'artifact_definition_ordinals')
    else:
        need(WINEMETAL_EXPORTS.issubset(by_name), 'artifact_winemetal_exports')
    return present


def inspect_pe_pair(root, name, repo=REPO):
    raw, raw_row = file_bytes(root, 'compiler/'+name)
    built, built_row = file_bytes(root, 'objects/'+PE_PATHS[name])
    installed, installed_row = file_bytes(root, 'install/aarch64-windows/'+name)
    need(len(raw) >= 96 and struct.unpack_from('<I', raw, 60)[0] >= 96, 'artifact_builtin_dos_bounds')
    need(raw[64:96] != BUILTIN_MARKER, 'artifact_compiler_already_builtin')
    need(built == raw[:64]+BUILTIN_MARKER+raw[96:], 'artifact_builtin_mutation')
    need(installed == built, 'artifact_installed_pe_changed')
    facts = inspect_pe_bytes(raw, repo)
    need(inspect_pe_bytes(built, repo) == facts and inspect_pe_bytes(installed, repo) == facts,
         'artifact_pe_facts_changed')
    check_exports(name, facts, root)
    return {'name': name, 'compiler': raw_row, 'builtin': built_row, 'installed': installed_row,
            'builtin_marker_offset': 64, 'builtin_marker_size': 32, 'facts': facts}


def macho_details(data):
    """Additional bounded native install-name and external-definition facts."""
    need(len(data) >= 32 and data[:4] == b'\xcf\xfa\xed\xfe', 'artifact_native_thin_header')
    cpu, _, filetype, count, command_bytes = struct.unpack_from('<5I', data, 4)
    need(cpu == MACH_ARM64 and count <= 65536 and 32+command_bytes <= len(data), 'artifact_native_commands')
    at, end, ids, symtabs = 32, 32+command_bytes, [], []
    for _ in range(count):
        need(at+8 <= end, 'artifact_native_commands')
        command, size = struct.unpack_from('<II', data, at)
        need(size >= 8 and size % 4 == 0 and at+size <= end, 'artifact_native_command_bounds')
        if command == 0xd:
            need(size >= 24, 'artifact_native_id')
            offset = struct.unpack_from('<I', data, at+8)[0]
            need(24 <= offset < size, 'artifact_native_id')
            raw = data[at+offset:at+size]
            need(b'\0' in raw, 'artifact_native_id')
            try:
                ids.append(raw.split(b'\0', 1)[0].decode('utf-8'))
            except UnicodeError:
                raise Error('artifact_native_id') from None
        elif command == 2:
            need(size == 24, 'artifact_native_symbol_command')
            symtabs.append(struct.unpack_from('<4I', data, at+8))
        at += size
    need(at == end and len(ids) == 1 and len(symtabs) <= 1, 'artifact_native_id_or_symbols')
    symbols = []
    if symtabs:
        symoff, count, stroff, strsize = symtabs[0]
        need(count <= 1000000 and symoff+count*16 <= len(data) and stroff+strsize <= len(data),
             'artifact_native_symbol_bounds')
        strings = data[stroff:stroff+strsize]
        for index in range(count):
            name, kind, _, _, _ = struct.unpack_from('<IBBHQ', data, symoff+16*index)
            if not (kind & 0xe0) and kind & 1 and kind & 0x0e in [2, 0x0e]:
                need(0 < name < len(strings), 'artifact_native_symbol_name')
                stop = strings.find(b'\0', name)
                need(stop >= name and stop-name <= 4096, 'artifact_native_symbol_name')
                try:
                    value = strings[name:stop].decode('ascii')
                except UnicodeError:
                    raise Error('artifact_native_symbol_name') from None
                need(value and all(32 <= ord(c) < 127 for c in value), 'artifact_native_symbol_name')
                symbols.append(value)
    need(len(symbols) == len(set(symbols)), 'artifact_native_symbol_duplicate')
    return {'install_name': ids[0], 'external_defined_symbols': sorted(symbols), 'filetype': filetype}


def inspect_native(root, path):
    fd = open_relative(root, path)
    try:
        before = os.fstat(fd)
        need(stat.S_IMODE(before.st_mode) == 0o755 and before.st_size <= MAX_ARTIFACT, 'artifact_native_mode_or_size')
        info = tools.readers().inspect_macho(Path('/dev/fd')/str(fd))
        with os.fdopen(os.dup(fd), 'rb') as stream:
            stream.seek(0)
            data = stream.read(MAX_ARTIFACT+1)
        after = os.fstat(fd)
        identity = lambda value: (value.st_dev, value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
        need(identity(before) == identity(after) and len(data) == before.st_size, 'artifact_native_changed')
        need(info['architectures'] == [MACH_ARM64] and info['selected_cpu'] == MACH_ARM64
             and info['filetype'] == 6, 'artifact_native_arch_or_type')
        extra = macho_details(data)
        return {'path': path, 'sha256': digest(data), 'size_bytes': len(data), 'mode': 0o755, **info, **extra}
    finally:
        os.close(fd)


def native_dependencies(info, counterparts):
    need(len(info['dependencies']) == len(set(info['dependencies'])), 'artifact_native_dependency_duplicate')
    result = []
    for name in info['dependencies']:
        need(isinstance(name, str) and '\0' not in name and not any(ord(c) < 32 for c in name), 'artifact_native_dependency_name')
        if name.startswith(('/usr/lib/', '/System/Library/')):
            need('..' not in name.split('/') and not any(part == '' for part in name.split('/')[1:]),
                 'artifact_native_system_path')
            result.append({'name': name, 'kind': 'macos_system_dependency', 'runtime_resolution': 'unperformed'})
        else:
            need(name.startswith('@rpath/') and name[len('@rpath/'):] in counterparts,
                 'artifact_native_unaccounted_dependency')
            target = counterparts[name[len('@rpath/'):]]
            result.append({'name': name, 'kind': 'source_bound_wine_counterpart',
                           'counterpart_path': target['path'], 'sha256': target['sha256'],
                           'runtime_resolution': 'unperformed'})
    return result


def inspect_layout(root, record):
    rows = record.get('wine_layout')
    need(isinstance(rows, list) and len(rows) == len(WINE_LAYOUT), 'artifact_wine_layout')
    need(all(isinstance(row, dict) and set(row) == {'path', 'sha256', 'size_bytes', 'mode', 'origin_role', 'origin_path'} for row in rows),
         'artifact_wine_layout_fields')
    mapped = {row['path']: row for row in rows}
    need(len(mapped) == len(rows) and set(mapped) == set(WINE_LAYOUT), 'artifact_wine_layout_paths')
    counterparts, observed = {}, []
    for path, role in WINE_LAYOUT.items():
        row = mapped[path]
        need(row['origin_role'] == role and isinstance(row['origin_path'], str), 'artifact_wine_origin_role')
        relative(row['origin_path'])
        data, fact = file_bytes(root, path, 64*1024**2)
        need(all(type(row[key]) is type(fact[key]) and row[key] == fact[key] for key in fact), 'artifact_wine_layout_changed')
        if path.endswith('.a'):
            fact['coff_machines'] = archive_machines(data)
            need(fact['coff_machines'] == [0xa641, 0xaa64], 'artifact_wine_import_role')
        elif path.endswith('.so'):
            fact = inspect_native(root, path)
            need(fact['install_name'] == '@rpath/'+Path(path).name and fact['rpaths'] == ['@loader_path/'],
                 'artifact_wine_native_role')
            counterparts[Path(path).name] = fact
        else:
            need(fact['mode'] == 0o755, 'artifact_wine_tool_mode')
            # winebuild is a native executable, not a shipped renderer library.
            need(data[:4] == b'\xcf\xfa\xed\xfe' and struct.unpack_from('<II', data, 4)[0] == MACH_ARM64
                 and struct.unpack_from('<I', data, 12)[0] == 2, 'artifact_wine_tool_role')
        observed.append({**fact, 'origin_role': role, 'origin_path': row['origin_path']})
    for name, info in counterparts.items():
        info['dependency_closure'] = native_dependencies(info, counterparts)
    # Preserve dependency facts in the deterministic layout inventory too.
    for fact in observed:
        if Path(fact['path']).name in counterparts:
            fact['dependency_closure'] = counterparts[Path(fact['path']).name]['dependency_closure']
    return sorted(observed, key=lambda row: row['path']), counterparts


def shader_inventory(root):
    rows = []
    for name in ['air_msad', 'air_samplepos', 'air_tessellation']:
        path = 'objects/src/airconv/darwin/libairconv.a.p/'+name
        data, fact = file_bytes(root, path+'.air', 16*1024**2)
        need(len(data) > 32 and data[:4] in [b'BC\xc0\xde', b'\xde\xc0\x17\x0b'], 'artifact_air_format')
        header, header_fact = file_bytes(root, path+'.h', 16*1024**2)
        embedded_header(header, data, name)
        rows += [{**fact, 'kind': 'air'}, {**header_fact, 'kind': 'embedded_header', 'payload_sha256': fact['sha256']}]
    path = 'objects/src/dxmt/libdxmt.a.p/dxmt_command'
    air, air_fact = file_bytes(root, path+'.air', 16*1024**2)
    need(len(air) > 32 and air[:4] in [b'BC\xc0\xde', b'\xde\xc0\x17\x0b'], 'artifact_air_format')
    metallib, metallib_fact = file_bytes(root, path+'.metallib', 16*1024**2)
    need(len(metallib) > 32 and metallib[:4] == b'MTLB', 'artifact_metallib_format')
    header, header_fact = file_bytes(root, path+'.h', 16*1024**2)
    embedded_header(header, metallib, 'dxmt_command')
    rows += [{**air_fact, 'kind': 'air'}, {**metallib_fact, 'kind': 'metallib'},
             {**header_fact, 'kind': 'embedded_header', 'payload_sha256': metallib_fact['sha256']}]
    return sorted(rows, key=lambda row: row['path'])


def embedded_header(content, payload, name):
    # Fixed pure helper, not the native builder CLI or any recorded command.
    helper = load_local(REPO/'tools/dxmt/build_native.py', '_pear_dxmt_embedded_header_reader')
    helper.verify_embedded_header(content, payload, name)


def notice_inventory(root, record, repo):
    reference = record['refs']['inputs']
    relative(reference['path'])
    data = read_relative(repo, reference['path'])
    need(digest(data) == reference['sha256'], 'artifact_notice_inputs')
    lock = decode_json(data)
    components = {row['id']: row for row in lock['components']}
    need(NOTICE_IDS.issubset(components) and components['dxmt-upstream']['commit'] == DXMT_COMMIT,
         'artifact_notice_selection')
    rows = []
    for component in sorted(NOTICE_IDS):
        for term in components[component]['terms']:
            path = 'notices/'+component+'/'+term['path']
            _, fact = file_bytes(root, path, 2*1024**2)
            need(fact['sha256'] == term['sha256'] and fact['size_bytes'] == term['size_bytes'], 'artifact_notice_bytes')
            rows.append({**fact, 'component_id': component, 'source_path': term['path']})
    need(len({row['path'] for row in rows}) == len(rows), 'artifact_notice_duplicate')
    return sorted(rows, key=lambda row: row['path'])


def generated_inventory(root, record):
    rows = record.get('generated_inputs')
    need(isinstance(rows, list) and 0 < len(rows) <= 1024, 'artifact_generated_inputs')
    need(all(isinstance(row, dict) and set(row) == {'path', 'sha256', 'size_bytes', 'mode'} for row in rows),
         'artifact_generated_fields')
    need(len({row['path'] for row in rows}) == len(rows), 'artifact_generated_duplicate')
    observed = []
    for row in rows:
        _, fact = file_bytes(root, row['path'], 2*1024**2)
        need(all(type(row[key]) is type(fact[key]) and row[key] == fact[key] for key in fact), 'artifact_generated_changed')
        observed.append(fact)
    return sorted(observed, key=lambda row: row['path'])


def installed_paths(root):
    base = root/'install'
    real_directory(base)
    paths = []
    for directory, dirs, names in os.walk(base, followlinks=False):
        need(all(not (Path(directory)/name).is_symlink() for name in dirs), 'artifact_install_directory_alias')
        for name in names:
            path = (Path(directory)/name).relative_to(root).as_posix()
            file_bytes(root, path)
            paths.append(path)
    return sorted(paths)


def inspect_outputs(root, record=None, repo=REPO):
    root = owned_directory(root, repo)
    if record is None:
        record = decode_json(read_relative(root, 'build.json'))
    need(type(record.get('schema_version')) is int and record['schema_version'] == 1
         and record.get('record_kind') == 'dxmt_artifact_build' and record.get('scope') == 'dxmt_component',
         'artifact_build_record')
    need(all(record.get(key) is False for key in ['pairing_verified', 'gpu_or_guest_execution_performed', 'runtime_eligible']),
         'artifact_runtime_overclaim')
    wanted = sorted(['install/aarch64-windows/'+name for name in PE_PATHS]+['install/aarch64-unix/winemetal.so'])
    need(installed_paths(root) == wanted, 'artifact_install_set')
    pe = [inspect_pe_pair(root, name, repo) for name in sorted(PE_PATHS)]
    layout, counterparts = inspect_layout(root, record)
    native = inspect_native(root, 'objects/'+NATIVE_PATH)
    installed = inspect_native(root, 'install/aarch64-unix/winemetal.so')
    need(native['sha256'] == installed['sha256'] and native['size_bytes'] == installed['size_bytes'], 'artifact_installed_native_changed')
    need(native['install_name'] == '@rpath/winemetal.so' and native['rpaths'] == NATIVE_RPATHS, 'artifact_native_search_paths')
    need({'___wine_unix_call_funcs', '___wine_unix_call_wow64_funcs'}.issubset(native['external_defined_symbols']),
         'artifact_native_unix_exports')
    native['dependency_closure'] = native_dependencies(native, counterparts)
    generated = generated_inventory(root, record)
    notices = notice_inventory(root, record, repo)
    need({row['path'] for row in notices}.issubset({row['path'] for row in generated}), 'artifact_notice_generated_omission')
    template = read_relative(root, 'source/version.h.in', 1024**2)
    version, version_fact = file_bytes(root, 'objects/version.h', 1024**2)
    need(b'@VCS_TAG@' in template and version == template.replace(b'@VCS_TAG@', DXMT_COMMIT.encode()), 'artifact_version_identity')
    return {'schema_version': 1, 'record_kind': 'dxmt_artifact_inventory', 'scope': 'dxmt_component',
            'pe_modules': pe, 'native_bridge': {'built': native, 'installed': installed},
            'wine_layout': layout, 'shader_outputs': shader_inventory(root), 'version_header': version_fact,
            'generated_inputs': generated, 'notices': notices, 'dxmt_built': True,
            'pairing_verified': False, 'gpu_or_guest_execution_performed': False, 'runtime_eligible': False,
            'game_qualification_performed': False, 'distribution_qualified': False,
            'native_dependency_scope': 'static_source_bound_counterparts_and_system_names_only',
            'runtime_loader_resolution': 'unperformed', 'typed_driver_interface_status': 'unimplemented'}


def verify_artifacts(root, repo=REPO):
    root = owned_directory(root, repo)
    builder = load_local(Path(repo)/'tools/dxmt/build.py', '_pear_dxmt_artifact_builder')
    value = builder.verify_build(root, repo=repo)
    reference = value.get('artifacts_manifest')
    need(isinstance(reference, dict) and set(reference) == {'path', 'sha256'} and reference['path'] == 'artifacts.json',
         'artifact_manifest_reference')
    data = read_relative(root, reference['path'])
    need(digest(data) == reference['sha256'], 'artifact_manifest_digest')
    facts = inspect_outputs(root, value, repo)
    need(data == encoded(facts), 'artifact_manifest_replay')
    return facts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--require-complete', action='store_true', required=True)
    arguments = parser.parse_args(argv)
    try:
        value = verify_artifacts(arguments.root)
        print(encoded({'scope': value['scope'], 'dxmt_built': value['dxmt_built'],
                       'pe_module_count': len(value['pe_modules']), 'native_bridge_count': 1,
                       'shader_output_count': len(value['shader_outputs']), 'pairing_verified': False,
                       'gpu_or_guest_execution_performed': False, 'runtime_eligible': False}).decode().strip())
        return 0
    except (Error, OSError, ValueError, KeyError, TypeError, struct.error) as error:
        print('DXMT artifact verification failed: '+getattr(error, 'code', 'artifact_read_failed'), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
