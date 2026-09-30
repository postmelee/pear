#!/usr/bin/env python3
"""Build pinned Wine variants in owned directories; never launch a Wine runtime."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import struct
import subprocess
import sys
import time

from common import Error, REPO, decode_json, encoded, load_json, need, read_relative, record, relative, sha256
from prepare import verify_prepared
from toolchain import (MACH_ARM64, alias_directory, base_env, coff_machine, empty_directory,
                       inspect_macho, inspect_sdk, native_tool, task_path, verify_prepared_tools, write_new)

RECORDS = {
    'inputs': 'runtime/wine/inputs.json',
    'config': 'runtime/wine/build-config.json',
    'toolchain': 'runtime/wine/toolchain.json',
    'patch_series': 'runtime/wine/patches/series.json',
}
MAX_BUILD_LOG = 64 * 1024 * 1024
PRODUCERS = ('build.py', 'common.py', 'prepare.py', 'toolchain.py')
REVISION_KEYS = {'artifacts_manifest', 'native_artifact_count', 'pe_artifact_count',
                 'passed', 'error', 'private_error', 'completion_revision'}

FIXTURE_SUITES = {
    'bootstrap': ('bootstrap_native.c', 'sentinel.c'),
    'api-abi': ('bootstrap_native.c', 'sentinel.c', 'api_launch.c',
                'api_pe.c', 'abi_pe.c', 'abi_native.c', 'abi_gateway.S'),
}
STAGE4_SUITE = 'threads-memory-exceptions'
STAGE4_FIXTURES = ('threads_pe.c', 'memory_pe.c', 'exceptions_pe.c', 'threads_gateway.S',
                   'signal_native.c', 'stage4_protocol.h')
FIXTURE_SUITES[STAGE4_SUITE] = FIXTURE_SUITES['api-abi'] + STAGE4_FIXTURES
STAGE5_SUITE = 'mac-driver'
STAGE5_FIXTURES = ('window_pe.c', 'stage5_protocol.h', 'window_control_pe.c', 'window_native.m',
                   'stage5_census.h')
FIXTURE_SUITES[STAGE5_SUITE] = FIXTURE_SUITES[STAGE4_SUITE] + STAGE5_FIXTURES
PE_SUITES = ('api-abi', STAGE4_SUITE, STAGE5_SUITE)
STAGE5_PE = {'libexec/pear-stage5/window-arm64.exe': 0xAA64}
STAGE4_PE = {'libexec/pear-stage4/stage4-arm64.exe': 0xAA64}
STAGE3_PE = {
    'libexec/pear-stage3/api-arm64.exe': 0xAA64,
    'libexec/pear-stage3/api-x64.exe': 0x8664,
    'libexec/pear-stage3/api-i386.exe': 0x14C,
    'libexec/pear-stage3/abi-arm64.exe': 0xAA64,
}

PAGE_WX_FIXTURES = ('lifetime_pe.c', 'lifetime_pe.h', 'missing_import_pe.c',
                    'missing_name.def', 'missing_ordinal.def')
PAGE_WX_PE = {
    'libexec/pear-stage3/lifetime-arm64.dll': 0xAA64,
    'libexec/pear-stage3/missing-name-arm64.dll': 0xAA64,
    'libexec/pear-stage3/missing-ordinal-arm64.dll': 0xAA64,
}


def fixture_suite(value):
    suite = value.get('fixture_suite', 'bootstrap')
    need(suite in FIXTURE_SUITES, 'build_fixture_suite')
    return suite


def code_publication_policy(value):
    """Read a recorded implementation policy, never a caller-supplied launch override."""
    policy = value.get('code_publication_policy', 'none')
    need(policy in ('none', 'page-wx'), 'build_code_publication_policy')
    need(policy == 'none' or fixture_suite(value) in PE_SUITES, 'build_code_publication_scope')
    return policy


def fixture_sources(value):
    return FIXTURE_SUITES[fixture_suite(value)] + (PAGE_WX_FIXTURES
        if code_publication_policy(value) == 'page-wx' else ())


def fixture_pe_outputs(suite, policy='none'):
    outputs = dict(STAGE3_PE, **(PAGE_WX_PE if policy == 'page-wx' else {})) if suite in PE_SUITES else {}
    if suite in (STAGE4_SUITE, STAGE5_SUITE):
        outputs.update(STAGE4_PE)
    if suite == STAGE5_SUITE:
        outputs.update(STAGE5_PE)
    return outputs


def fixture_commands(root, tools, lock, suite, publication_policy='none'):
    """Exact compile/inspection invocations; no PE fixture is executed here."""
    need(suite in FIXTURE_SUITES, 'build_fixture_suite')
    sources = REPO / 'tests/wine/fixtures'
    commands = {}
    native = [('fixture-bootstrap', 'bootstrap_native.c', 'libexec/pear-stage2/bootstrap-native'),
              ('fixture-sentinel', 'sentinel.c', 'libexec/pear-stage2/sentinel')]
    if suite in PE_SUITES:
        native.append(('fixture-api-launch', 'api_launch.c', 'libexec/pear-stage3/api-launch'))
    for ident, filename, output in native:
        commands[ident] = [str(native_tool(lock, 'clang')), '-arch', 'arm64', '-isysroot', lock['sdk']['path'],
            '-std=c11', '-Wall', '-Wextra', '-Werror', str(sources / filename),
            '-o', str(root / 'install' / output)]
    if suite in PE_SUITES:
        clang = str(tools / 'llvm-mingw/bin/clang')
        for target, suffix in [('aarch64', 'arm64'), ('x86_64', 'x64'), ('i686', 'i386')]:
            commands['fixture-api-' + suffix] = [clang, '--target=' + target + '-w64-windows-gnu',
                '-std=c11', '-Wall', '-Wextra', '-Werror', '-O1', '-fno-builtin', '-nostdlib',
                '-Wl,-e,mainCRTStartup', str(sources / 'api_pe.c'), '-lkernel32',
                '-o', str(root / 'install/libexec/pear-stage3' / ('api-' + suffix + '.exe'))]
        commands['fixture-abi-arm64'] = [clang, '--target=aarch64-w64-windows-gnu',
            '-std=c11', '-Wall', '-Wextra', '-Werror', '-O1', '-fno-builtin', '-nostdlib',
            '-Wl,-e,mainCRTStartup', str(sources / 'abi_pe.c'), str(sources / 'abi_gateway.S'),
            '-lkernel32', '-o', str(root / 'install/libexec/pear-stage3/abi-arm64.exe')]
        if publication_policy == 'page-wx':
            flags = [clang, '--target=aarch64-w64-windows-gnu', '-std=c11', '-Wall', '-Wextra',
                     '-Werror', '-O1', '-fno-builtin', '-nostdlib', '-shared', '-Wl,-e,DllMain']
            dest = root / 'install/libexec/pear-stage3'
            commands['fixture-lifetime-dll'] = flags + [str(sources / 'lifetime_pe.c'), '-lkernel32',
                                                       '-o', str(dest / 'lifetime-arm64.dll')]
            for kind in ('name', 'ordinal'):
                importlib = root / ('missing-' + kind + '.a')
                commands['fixture-missing-' + kind + '-importlib'] = [
                    str(tools / 'llvm-mingw/bin/llvm-dlltool'), '-m', 'arm64',
                    '-d', str(sources / ('missing_' + kind + '.def')), '-l', str(importlib)]
                commands['fixture-missing-' + kind + '-dll'] = flags + [
                    str(sources / 'missing_import_pe.c'), str(importlib),
                    '-o', str(dest / ('missing-' + kind + '-arm64.dll'))]
        for ident, path in [('disassemble-ntdll', 'lib/wine/aarch64-unix/ntdll.so'),
                            ('disassemble-abi', 'libexec/pear-stage3/abi-arm64.exe')]:
            commands[ident] = [str(tools / 'llvm-mingw/bin/llvm-objdump'), '--disassemble',
                              str(root / 'install' / path)]
    if suite in (STAGE4_SUITE, STAGE5_SUITE):
        commands['fixture-stage4-arm64'] = [clang, '--target=aarch64-w64-windows-gnu',
            '-std=c11', '-Wall', '-Wextra', '-Werror', '-O1', '-fno-builtin', '-nostdlib',
            '-Wl,-e,mainCRTStartup', *[str(sources / name) for name in
                ('threads_pe.c', 'memory_pe.c', 'exceptions_pe.c', 'threads_gateway.S')],
            '-lkernel32', '-o', str(root / 'install/libexec/pear-stage4/stage4-arm64.exe')]
        commands['disassemble-stage4'] = [str(tools / 'llvm-mingw/bin/llvm-objdump'), '--disassemble',
            str(root / 'install/libexec/pear-stage4/stage4-arm64.exe')]
    if suite == STAGE5_SUITE:
        commands['fixture-window-arm64'] = [clang, '--target=aarch64-w64-windows-gnu',
            '-std=c11', '-Wall', '-Wextra', '-Werror', '-O1', '-fno-builtin', '-nostdlib',
            '-Wl,-e,mainCRTStartup', str(sources / 'window_pe.c'), '-luser32', '-lkernel32',
            '-o', str(root / 'install/libexec/pear-stage5/window-arm64.exe')]
        commands['disassemble-window'] = [str(tools / 'llvm-mingw/bin/llvm-objdump'), '--disassemble',
            str(root / 'install/libexec/pear-stage5/window-arm64.exe')]
    return commands


def verify_stage4_native_fixture(source, hashes):
    for original, copied in [('signal_native.c', 'pear_signal_fixture.c'),
                             ('stage4_protocol.h', 'stage4_protocol.h')]:
        need(sha256(source / 'dlls/ntdll/unix' / copied) == hashes.get(original),
             'build_stage4_native_fixture_source_mismatch')


def verify_stage5_native_fixture(source, hashes):
    for original, copied in [('window_native.m', 'pear_window_fixture.m'),
                             ('window_control_pe.c', 'pear_window_control.c'),
                             ('stage5_protocol.h', 'stage5_protocol.h'),
                             ('stage5_census.h', 'stage5_census.h')]:
        need(sha256(source / 'dlls/winemac.drv' / copied) == hashes.get(original),
             'build_stage5_native_fixture_source_mismatch')


WINMD_PATHS = frozenset('share/wine/winmd/' + name + '.winmd' for name in (
    'windows.applicationmodel', 'windows.globalization', 'windows.graphics',
    'windows.media', 'windows.networking', 'windows.perception', 'windows.storage',
    'windows.system', 'windows.ui', 'windows.ui.xaml'))

# configure.ac restricts these modules to ARM64EC in this companion build.
ARM64EC_PATHS = frozenset('lib/wine/aarch64-windows/' + name for name in
                         ('dpnsvr.exe', 'vcruntime140_1.dll', 'xtajit64.dll'))


def inspect_arm64ec(path):
    """Require positive ARM64EC metadata; its AMD64 header is not native x64 proof.

    This pinned link form includes ARM64EC and x64 guest thunk ranges. Neither
    those ranges nor the companion build establish guest execution support.
    """
    need(Path(path).stat().st_size <= 64 * 1024 * 1024, 'arm64ec_size_limit')
    data = Path(path).read_bytes()
    def number(fmt, at):
        size = struct.calcsize('<' + fmt)
        need(0 <= at and at + size <= len(data), 'arm64ec_structure_bounds')
        return struct.unpack_from('<' + fmt, data, at)[0]
    need(data[:2] == b'MZ', 'arm64ec_pe_header')
    pe = number('I', 60)
    count, size, opt = number('H', pe + 6), number('H', pe + 20), pe + 24
    need(pe >= 64 and data[pe:pe + 4] == b'PE\0\0' and number('H', pe + 4) == 0x8664
         and 1 <= count <= 96 and size >= 240 and number('H', opt) == 0x20B
         and number('I', opt + 108) == 16, 'arm64ec_pe_header')
    base = number('Q', opt + 24)
    image_size = number('I', opt + 56)
    need(0 < image_size <= 1024 * 1024 * 1024, 'arm64ec_image_size')
    sections = []
    for i in range(count):
        at = opt + size + 40 * i
        virtual, rva, raw_size, raw, flags = (number('I', at + n) for n in (8, 12, 16, 20, 36))
        need(raw + raw_size <= len(data) and rva + max(virtual, raw_size) <= image_size, 'arm64ec_section_bounds')
        sections.append((rva, min(virtual, raw_size), raw, flags, max(virtual, raw_size)))
    def mapped(rva, length, executable=False):
        matches = [(raw + rva - address, flags) for address, span, raw, flags, _ in sections
                   if rva >= address and length > 0 and rva - address + length <= span]
        need(len(matches) == 1 and (not executable or matches[0][1] & 0x20000000), 'arm64ec_unmapped_rva')
        return matches[0][0]
    executable_intervals = sorted((rva, rva + span) for rva, _, _, flags, span in sections
                                  if flags & 0x20000000 and span)
    need(all(previous[1] <= current[0] for previous, current in
             zip(executable_intervals, executable_intervals[1:])), 'arm64ec_ambiguous_code_sections')
    def executable_range(rva, length):
        need(length > 0 and rva + length <= image_size, 'arm64ec_code_range')
        cursor, end = rva, rva + length
        # LLVM's x64 thunk range can include executable section alignment padding
        # and cross into the immediately adjacent .hexpthk section.
        for low, high in executable_intervals:
            if low <= cursor < high:
                cursor = min(high, end)
            if cursor == end:
                return
            if low > cursor:
                break
        raise Error('arm64ec_unmapped_code_range')
    config_rva = number('I', opt + 112 + 10 * 8)
    config_size = number('I', opt + 116 + 10 * 8)
    config = mapped(config_rva, config_size)
    need(config_size >= 0xE8 and 0xE8 <= number('I', config) <= config_size, 'arm64ec_load_config')
    pointer = number('Q', config + 0xC8)
    need(pointer > base and number('I', config + 0xE0) == 0 and number('H', config + 0xE4) == 0,
         'arm64ec_load_config')
    metadata = mapped(pointer - base, 80)
    version, codemap, count = (number('I', metadata + n) for n in (0, 4, 8))
    need(version == 2 and 2 <= count <= 4096, 'arm64ec_chpe_header')
    codemap_at = mapped(codemap, count * 8)
    ranges, previous_end = [], 0
    for i in range(count):
        tagged, length = number('I', codemap_at + i * 8), number('I', codemap_at + i * 8 + 4)
        kind, rva = tagged & 3, tagged & ~3
        need(kind in (1, 2) and rva >= previous_end, 'arm64ec_code_range')
        executable_range(rva, length)
        ranges.append({'rva': rva, 'size_bytes': length, 'code_kind': 'arm64ec' if kind == 1 else 'x64'})
        previous_end = rva + length
    need({row['code_kind'] for row in ranges} == {'arm64ec', 'x64'}, 'arm64ec_code_range')
    return {'pe_abi': 'arm64ec', 'chpe_version': version, 'code_ranges': ranges}


def inspect_winmd(path):
    """Recognize only the pinned WIDL metadata container, never executable I386 code."""
    need(Path(path).stat().st_size <= 32 * 1024 * 1024, 'winmd_size_limit')
    data = Path(path).read_bytes()
    def u16(at):
        need(0 <= at and at + 2 <= len(data), 'winmd_truncated')
        return struct.unpack_from('<H', data, at)[0]
    def u32(at):
        need(0 <= at and at + 4 <= len(data), 'winmd_truncated')
        return struct.unpack_from('<I', data, at)[0]
    need(data[:2] == b'MZ', 'winmd_header')
    pe = u32(60)
    opt = pe + 24
    need(pe >= 64 and data[pe:pe + 4] == b'PE\0\0' and u16(pe + 4) == 0x14C
         and u16(pe + 6) == 1 and u16(pe + 20) == 224 and u16(opt) == 0x10B,
         'winmd_header')
    need(u32(opt + 4) == 0 and u32(opt + 16) == 0 and u32(opt + 92) == 16,
         'winmd_executable_content')
    directories = [(u32(opt + 96 + i * 8), u32(opt + 100 + i * 8)) for i in range(16)]
    need(directories[14] == (0x1000, 72)
         and all(pair == (0, 0) for i, pair in enumerate(directories) if i != 14), 'winmd_directories')
    section = opt + 224
    virtual_size, rva, raw_size, raw_at = (u32(section + x) for x in (8, 12, 16, 20))
    need(data[section:section + 8] == b'.text\0\0\0' and u32(section + 36) == 0x40000020
         and raw_at == 512 and section + 40 <= raw_at and raw_at + raw_size <= len(data),
         'winmd_section')
    def mapped(address, size):
        offset = address - rva
        need(size > 0 and offset >= 0 and offset + size <= min(virtual_size, raw_size), 'winmd_rva')
        return raw_at + offset
    com = mapped(*directories[14])
    need(u32(com) == 72 and (u16(com + 4), u16(com + 6)) == (2, 5)
         and u32(com + 16) == 1 and u32(com + 20) == 0
         and data[com + 24:com + 72] == bytes(48), 'winmd_clr')
    size = u32(com + 12)
    metadata = mapped(u32(com + 8), size)
    need(size >= 40 and data[metadata:metadata + 4] == b'BSJB'
         and (u16(metadata + 4), u16(metadata + 6)) == (1, 1) and u32(metadata + 8) == 0
         and u32(metadata + 12) == 20
         and data[metadata + 16:metadata + 36] == b'WindowsRuntime 1.4\0\0', 'winmd_metadata')
    return {'machine': 0x14C, 'metadata_only': True, 'metadata_size_bytes': size,
            'clr_flags': 1, 'native_entrypoint': 0, 'managed_entrypoint': 0}


def inventory(root, binary=False):
    """Record exact ordinary files and contained links without following directory links."""
    root = Path(root).resolve()
    files, links = [], []
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in sorted(dirs + names):
            path = Path(directory) / name
            rel = path.relative_to(root).as_posix()
            relative(rel)
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                target = os.readlink(path)
                need(not target.startswith('/') and '\\' not in target
                     and path.resolve().is_relative_to(root) and path.resolve().exists(), 'install_link_escape')
                links.append({'path': rel, 'target': target})
            elif stat.S_ISREG(info.st_mode):
                row = {'path': rel, 'sha256': sha256(path), 'size_bytes': info.st_size,
                       'mode': stat.S_IMODE(info.st_mode), 'kind': 'data'}
                if binary:
                    with path.open('rb') as stream:
                        magic = stream.read(4)
                    if magic in (b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf'):
                        facts = inspect_macho(path)
                        need(facts['architectures'] == [MACH_ARM64], 'built_native_slice_mismatch')
                        row.update(kind='macho', **facts)
                    elif magic[:2] == b'MZ':
                        if rel in WINMD_PATHS:
                            row.update(kind='pe_metadata', **inspect_winmd(path))
                        else:
                            row.update(kind='pe', machine=coff_machine(path))
                            if rel in ARM64EC_PATHS and row['machine'] == 0x8664:
                                row.update(inspect_arm64ec(path))
                files.append(row)
            else:
                need(stat.S_ISDIR(info.st_mode), 'build_special_file')
    return {'schema_version': 1, 'record_kind': 'wine_build_inventory',
            'files': sorted(files, key=lambda x: x['path']),
            'symlinks': sorted(links, key=lambda x: x['path'])}


def validate_patch(series, row):
    need(isinstance(row, dict) and isinstance(row.get('path'), str), 'patch_shape')
    parts = relative(row['path'])
    need(len(parts) == 1 and parts[0].endswith('.patch'), 'patch_path')
    path = REPO / 'runtime/wine/patches' / parts[0]
    need(sha256(path) == row.get('sha256'), 'patch_digest_mismatch')
    text = path.read_text(encoding='utf-8')
    old, new = [], []
    for line in text.splitlines():
        if line.startswith(('--- ', '+++ ')):
            value = line[4:].split('\t')[0]
            if value == '/dev/null':
                continue
            need(value.startswith('a/' if line.startswith('--- ') else 'b/'), 'patch_header')
            name = value[2:]
            relative(name)
            need(not name.startswith('.git/') and name != '.git', 'patch_git_metadata')
            (old if line.startswith('--- ') else new).append(name)
    need(old or new, 'empty_patch')
    need(len(old) == len(set(old)) and len(new) == len(set(new)), 'ambiguous_patch')
    return path


def run_build_command(rows, ident, argv, cwd, env, timeout, log_limit=MAX_BUILD_LOG):
    """Stream bounded local build logs and terminate only the owned build group."""
    argv = [str(x) for x in argv]
    with Path(argv[0]).open('rb') as executable:
        is_script = executable.read(2) == b'#!'
    if is_script:
        argv = ['/bin/sh', *argv]
    argv = ['/usr/bin/arch', '-arm64', *argv]
    cwd = Path(cwd)
    logs = cwd / '.pear-build-logs'
    logs.mkdir(exist_ok=True)
    row = {'id': ident, 'argv': argv, 'cwd': str(cwd)}
    rows.append(row)
    with (logs / (ident + '.stdout')).open('xb') as out, (logs / (ident + '.stderr')).open('xb') as err:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                   stdout=out, stderr=err, start_new_session=True)
        started, last_progress = time.monotonic(), time.monotonic()
        timed_out = output_limit = interrupted = False
        try:
            while process.poll() is None:
                timed_out = time.monotonic() - started > timeout
                output_limit = max(os.fstat(out.fileno()).st_size, os.fstat(err.fileno()).st_size) > log_limit
                if timed_out or output_limit:
                    os.killpg(process.pid, signal.SIGKILL)
                    break
                if time.monotonic() - last_progress >= 30:
                    print(ident + ': running; stdout bytes=' + str(os.fstat(out.fileno()).st_size), flush=True)
                    last_progress = time.monotonic()
                time.sleep(.1)
            code = process.wait(timeout=5)
        except KeyboardInterrupt:
            interrupted = True
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
            code = process.wait(timeout=5)
        except BaseException:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
            raise
        output_limit = output_limit or max(os.fstat(out.fileno()).st_size, os.fstat(err.fileno()).st_size) > log_limit
        row.update(exit_code=code, timed_out=timed_out, output_limit=output_limit, interrupted=interrupted,
                   elapsed_ms=round((time.monotonic() - started) * 1000))
    for stream in ('stdout', 'stderr'):
        path = logs / (ident + '.' + stream)
        row[stream + '_log'] = {'path': str(path), 'sha256': sha256(path),
                               'size_bytes': path.stat().st_size}
        with path.open('rb') as source:
            row[stream] = source.read(16000).decode('utf-8', errors='replace')
    print(ident + ': exit ' + str(code), flush=True)
    need(not interrupted, 'build_command_interrupted:' + ident)
    need(code == 0 and not timed_out and not output_limit, 'build_command_failed:' + ident)
    return row


def has_native_architecture_policy(value):
    """Use this build's verified patch list, preserving historical configurations."""
    return any(row.get('path') == '0003l-native-architecture-policy.patch'
               for row in value.get('patches', []))


def observed_configuration(makefile, variant, publication_policy="none", *, native_architecture_policy=False):
    text = Path(makefile).read_text()
    observed = {}
    for key in ('HOST_ARCH', 'PE_ARCHS', 'aarch64_TARGET', 'arm64ec_TARGET', 'x86_64_TARGET',
                'APPKIT_LIBS', 'CORETEXT_LIBS', 'FREETYPE_LIBS', 'FONTCONFIG_LIBS', 'COREAUDIO_LIBS'):
        values = re.findall('^' + key + r' = (.*)$', text, re.MULTILINE)
        need(len(values) == 1, 'build_configuration_field')
        observed[key] = values[0].strip()
    if publication_policy == 'page-wx':
        field = 'PEAR_NATIVE_PE_PUBLICATION_CFLAGS'
        values = re.findall('^' + field + r' = (.*)$', text, re.MULTILINE)
        need(values == ['-DPEAR_NATIVE_PE_PUBLICATION=1'], 'build_publication_macro_mismatch')
        observed[field] = values[0]
    if native_architecture_policy:
        field = 'PEAR_NATIVE_ONLY_ARCH_CFLAGS'
        values = re.findall('^' + field + r' = (.*)$', text, re.MULTILINE)
        expected = '-DPEAR_NATIVE_ONLY_ARCH=1' if variant['id'] == 'arm64' else ''
        need(values == [expected], 'build_native_architecture_macro_mismatch')
        observed[field] = values[0]
    need(observed['HOST_ARCH'] == 'aarch64' and observed['PE_ARCHS'].split() == variant['pe_archs'],
         'build_configuration_architecture')
    need('dlls/winemac.drv/cocoa_app.o:' in text, 'build_mac_driver_missing')
    need(observed['APPKIT_LIBS'] == '-framework AppKit' and observed['CORETEXT_LIBS'] == '-framework CoreText',
         'build_frameworks_missing')
    need(not any(observed[key] for key in ('FREETYPE_LIBS', 'FONTCONFIG_LIBS', 'COREAUDIO_LIBS')),
         'build_optional_dependency_changed')
    if variant['id'] == 'arm64ec-build':
        need(observed['x86_64_TARGET'] == 'x86_64-windows', 'build_auxiliary_compiler_missing')
    return observed


def artifact_inventory(record_value, root):
    reference = record_value['artifacts_manifest']
    path = Path(root).joinpath(*relative(reference['path']))
    need(sha256(path) == reference['sha256'], 'build_manifest_identity')
    return record(load_json(path), 'wine_build_inventory')


def expected_source_inventory(original, patches):
    """Derive the complete patched tree from exact base files and ordered changes."""
    files = {}
    for row in original['files']:
        name = row['path']
        relative(name)
        need(name not in files and row['mode'] in ('100644', '100755'), 'base_source_shape')
        files[name] = {'path': name, 'sha256': row['sha256'],
                       'mode': 0o755 if row['mode'] == '100755' else 0o644, 'kind': 'data'}
    for patch in patches:
        seen = set()
        need(patch.get('changes'), 'patch_preimages_missing')
        for change in patch['changes']:
            name = change['path']
            relative(name)
            need(name not in seen, 'patch_change_duplicate')
            seen.add(name)
            previous = files.get(name)
            need((previous is None) if change['before_sha256'] is None else
                 previous is not None and previous['sha256'] == change['before_sha256'],
                 'patch_preimage_changed')
            # The ordered series adds/changes ordinary files only.
            need(isinstance(change['after_sha256'], str) and
                 re.fullmatch('[0-9a-f]{64}', change['after_sha256']), 'patch_postimage_shape')
            files[name] = {'path': name, 'sha256': change['after_sha256'],
                           'mode': previous['mode'] if previous else 0o644, 'kind': 'data'}
    return {'files': sorted(files.values(), key=lambda row: row['path']), 'symlinks': []}


def verify_source_derivation(actual, original, patches):
    expected = expected_source_inventory(original, patches)
    reduced = {'files': [{key: row[key] for key in ('path', 'sha256', 'mode', 'kind')}
                         for row in actual['files']], 'symlinks': actual['symlinks']}
    need(reduced == expected, 'source_patch_derivation_mismatch')


def verify_build_evidence(root, result, current=True):
    """Verify completed commands and their inputs without accepting install outputs."""
    need(result.get('scope') == 'wine_component'
         and result.get('wine_runtime_execution') is False, 'build_scope')
    need(result.get('variant') in ('arm64', 'arm64ec-build'), 'build_variant')
    policy = code_publication_policy(result)
    if current:
        for key, name in RECORDS.items():
            need(sha256(REPO / name) == result['record_hashes'][key], 'build_input_changed')
        series = load_json(REPO / RECORDS['patch_series'])
        need(result['patches'] == series['patches'] and fixture_suite(result) == fixture_suite(series),
             'build_patch_series_changed')
        need(policy == code_publication_policy(series), 'build_code_publication_changed')
        for row in result['patches']:
            validate_patch(None, row)
    source_ref = result['source_manifest']
    source_manifest = root.joinpath(*relative(source_ref['path']))
    need(sha256(source_manifest) == source_ref['sha256'], 'built_source_manifest_changed')
    actual_source = inventory(root / 'source')
    need(actual_source == load_json(source_manifest), 'built_source_changed')
    inputs = task_path(result['source_inputs_root']).resolve()
    verify_prepared(inputs, result['record_hashes']['inputs'])
    need(sha256(inputs / 'prepared.json') == result['source_prepared_sha256'], 'build_prepared_source_changed')
    verify_source_derivation(actual_source, load_json(inputs / 'wine-files.json'), result['patches'])
    install = root / 'install'
    need(result.get('install_root') == str(install), 'build_install_root')
    verify_producer_snapshot(root, 'producer', result['producer_sha256'])
    if current:
        for name in fixture_sources(result):
            need(sha256(REPO / 'tests/wine/fixtures' / name) == result['fixture_hashes'].get(name), 'build_fixture_changed')
    if fixture_suite(result) in PE_SUITES:
        need(sha256(root / 'source/dlls/ntdll/unix/pear_abi_fixture.c') == result['fixture_hashes']['abi_native.c'],
             'build_native_fixture_source_mismatch')
    if fixture_suite(result) in (STAGE4_SUITE, STAGE5_SUITE):
        verify_stage4_native_fixture(root / 'source', result['fixture_hashes'])
    if fixture_suite(result) == STAGE5_SUITE:
        verify_stage5_native_fixture(root / 'source', result['fixture_hashes'])
    config = load_json(REPO / RECORDS['config'])
    variant = next(row for row in config['variants'] if row['id'] == result['variant'])
    verify_build_commands(root, result, variant)
    need(observed_configuration(root / 'objects/Makefile', variant, policy,
                                native_architecture_policy=has_native_architecture_policy(result))
         == result['configuration'],
         'build_configuration_evidence_changed')
    need(sha256(root / 'objects/Makefile') == result['makefile_sha256']
         and sha256(root / 'objects/config.log') == result['config_log_sha256'], 'build_configuration_changed')
    if current:
        verify_build_tools(result)
    return result



def verify_build_commands(root, result, variant):
    """Bind every successful command to its approved invocation, directory and logs."""
    lock = load_json(REPO / RECORDS['toolchain'])
    alias = Path(result['path_alias']['invoked'])
    resolved = Path(result['path_alias']['resolved'])
    need(alias.is_absolute() and resolved == (REPO / '.build/task4').resolve()
         and alias.resolve() == resolved, 'build_command_alias')
    def logical(path):
        return str(alias / Path(path).relative_to(resolved))
    tools = Path(result['tools_root'])
    expected = {}
    for index, patch in enumerate(result['patches'], 1):
        expected['patch-' + str(index)] = ['/usr/bin/patch', '-p1', '--batch', '--forward', '--fuzz=0',
            '-i', str(REPO / 'runtime/wine/patches' / patch['path'])]
    expected['configure'] = ['/bin/sh', logical(root / 'source/configure'), '--prefix=' + logical(root / 'install'),
                            '--with-mingw=' + logical(tools / 'llvm-mingw/bin/clang'), *variant['configure_args']]
    commands = {row['id']: row for row in result['commands']}
    fixtures = fixture_commands(root, tools, lock, fixture_suite(result), code_publication_policy(result))
    expected_order = list(expected) + ['make', 'install'] + list(fixtures)
    need([row['id'] for row in result['commands']] == expected_order and len(commands) == len(expected_order),
         'build_command_coverage')
    make = str(native_tool(lock, 'make'))
    clang = str(native_tool(lock, 'clang'))
    make_args = commands['make']['argv']
    need(isinstance(make_args, list) and len(make_args) == 4 and make_args[-1] in ('-j1', '-j2', '-j3', '-j4'),
         'build_command_invocation')
    expected['make'], expected['install'] = [make, make_args[-1]], [make, 'install']
    expected.update(fixtures)
    for ident, row in commands.items():
        need(type(row.get('exit_code')) is int and row['exit_code'] == 0
             and row.get('timed_out') is False and row.get('output_limit') is False
             and row.get('interrupted') is False, 'build_command_outcome')
        patch = ident.startswith('patch-')
        need(row.get('argv') == ['/usr/bin/arch', '-arm64', *expected[ident]]
             and row.get('cwd') == logical(root / ('source' if patch else 'objects')), 'build_command_invocation')
        for stream in ('stdout', 'stderr'):
            reference = row[stream + '_log']
            target = root / ('patch-logs' if patch else 'objects/.pear-build-logs') / (ident + '.' + stream)
            need(Path(reference['path']).resolve() == target, 'build_command_log_changed')
            data = read_relative(root, target.relative_to(root).as_posix(), limit=MAX_BUILD_LOG)
            need(hashlib.sha256(data).hexdigest() == reference['sha256'] and len(data) == reference['size_bytes']
                 and row[stream] == data[:16000].decode('utf-8', errors='replace'), 'build_command_log_changed')


def verify_build_tools(result):
    """Revalidate the recorded external tool closure and SDK without executing it."""
    lock = record(load_json(REPO / RECORDS['toolchain']), 'wine_toolchain')
    tools = task_path(result['tools_root']).resolve()
    need(sha256(tools / 'prepared.json') == result['tool_prepared_sha256'], 'build_prepared_tools_changed')
    prepared = verify_prepared_tools(lock, tools)
    need(prepared['lock_sha256'] == result['record_hashes']['toolchain'], 'build_tool_lock')
    need(inspect_sdk(lock) == result['sdk'], 'build_sdk_changed')
    for ident in ('clang', 'clang++', 'make', 'flex'):
        native_tool(lock, ident)
    patch = result['patch_tool']
    need(patch['path'] == '/usr/bin/patch' and sha256(patch['path']) == patch['sha256']
         and {'path': patch['path'], 'sha256': patch['sha256'], **inspect_macho(patch['path'])} == patch,
         'build_patch_tool_changed')


def verify_producer_snapshot(root, directory, hashes):
    need(set(hashes) == set(PRODUCERS), 'build_producer_missing')
    for name in PRODUCERS:
        need(hashlib.sha256(read_relative(root, directory + '/' + name)).hexdigest() == hashes[name],
             'build_producer_changed')


def finalizable_record(result):
    permitted_error = result.get('error') == 'build_required_outputs_missing' or (
        result.get('error') == 'build_pe_architecture' and result.get('variant') == 'arm64ec-build')
    need(result.get('passed') is False and permitted_error
         and not any(key in result for key in ('completion_revision', 'artifacts_manifest',
                                              'native_artifact_count', 'pe_artifact_count')),
         'build_not_finalizable')


def verify_completion_revision(root, result):
    revision = result.get('completion_revision')
    if revision is None:
        return
    need(set(revision) == {'mode', 'reason', 'original_record', 'finalizer_sha256',
                           'build_commands_executed', 'wine_runtime_execution'}, 'build_revision_shape')
    need(revision['mode'] == 'validation_only'
         and revision['reason'] == 'corrected_installed_output_validation'
         and revision['build_commands_executed'] is False and revision['wine_runtime_execution'] is False,
         'build_revision_scope')
    reference = revision['original_record']
    need(set(reference) == {'path', 'sha256'} and reference['path'] == 'build-before-finalization.json',
         'build_revision_reference')
    raw = read_relative(root, reference['path'])
    need(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'build_original_record_changed')
    original = record(decode_json(raw), 'wine_build')
    finalizable_record(original)
    need({k: v for k, v in original.items() if k not in REVISION_KEYS}
         == {k: v for k, v in result.items() if k not in REVISION_KEYS}, 'build_revision_evidence_changed')
    need('error' not in result and 'private_error' not in result, 'build_revision_outcome')
    verify_producer_snapshot(root, 'finalizer', revision['finalizer_sha256'])


def verify_build(root, current=True):
    """Rehash a completed local build; does not authorize any executable."""
    root = task_path(root).resolve()
    result = record(load_json(root / 'build.json'), 'wine_build')
    need(result.get('passed') is True, 'build_not_complete')
    verify_build_evidence(root, result, current)
    verify_completion_revision(root, result)
    artifacts = artifact_inventory(result, root)
    required_outputs(artifacts, result['variant'], fixture_suite(result), code_publication_policy(result))
    need(inventory(root / 'install', binary=True) == artifacts, 'build_artifact_changed')
    if code_publication_policy(result) == 'page-wx':
        need(result.get('arena_capacity') == arena_capacity_evidence(root / 'source', root / 'install', artifacts),
             'build_arena_capacity_changed')
    need(result['native_artifact_count'] == sum(row['kind'] == 'macho' for row in artifacts['files'])
         and result['pe_artifact_count'] == sum(row['kind'] == 'pe' for row in artifacts['files']),
         'build_artifact_counts')
    return result


def finalize_only(output):
    """Complete only output validation after a fully successful recorded build."""
    root = task_path(output)
    need(not root.is_symlink() and root.is_dir(), 'build_finalize_root')
    root = root.resolve()
    raw = read_relative(root, 'build.json')
    original = record(decode_json(raw), 'wine_build')
    finalizable_record(original)
    reserved = ('build-before-finalization.json', 'finalizer', 'installed-files.json', '.build-finalized.json')
    need(all(not (root / name).exists() and not (root / name).is_symlink() for name in reserved),
         'build_finalization_destination_exists')
    verify_build_evidence(root, original, current=True)
    artifacts = inventory(root / 'install', binary=True)
    required_outputs(artifacts, original['variant'], fixture_suite(original), code_publication_policy(original))
    if code_publication_policy(original) == 'page-wx':
        need(original.get('arena_capacity') == arena_capacity_evidence(root / 'source', root / 'install', artifacts),
             'build_arena_capacity_changed')
    finalizer = {name: read_relative(Path(__file__).parent, name) for name in PRODUCERS}
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in finalizer.items()}
    need(read_relative(root, 'build.json') == raw, 'build_original_record_changed')
    # Preserve the failed producer's exact bytes and source snapshots. No command is rerun.
    with (root / 'build-before-finalization.json').open('xb') as stream:
        stream.write(raw)
    (root / 'finalizer').mkdir()
    for name, data in finalizer.items():
        with (root / 'finalizer' / name).open('xb') as stream:
            stream.write(data)
    write_new(root / 'installed-files.json', artifacts)
    result = dict(original)
    result.pop('error')
    result.pop('private_error', None)
    result.update(passed=True, artifacts_manifest={'path': 'installed-files.json',
                  'sha256': sha256(root / 'installed-files.json')},
                  native_artifact_count=sum(row['kind'] == 'macho' for row in artifacts['files']),
                  pe_artifact_count=sum(row['kind'] == 'pe' for row in artifacts['files']),
                  completion_revision={'mode': 'validation_only',
                    'reason': 'corrected_installed_output_validation',
                    'original_record': {'path': 'build-before-finalization.json',
                                        'sha256': hashlib.sha256(raw).hexdigest()},
                    'finalizer_sha256': hashes, 'build_commands_executed': False,
                    'wine_runtime_execution': False})
    verify_completion_revision(root, result)
    write_new(root / '.build-finalized.json', result)
    need(read_relative(root, 'build.json') == raw, 'build_original_record_changed')
    os.replace(root / '.build-finalized.json', root / 'build.json')
    return 0

def required_outputs(artifacts, variant, suite='bootstrap', publication_policy='none'):
    files = {row['path']: row for row in artifacts['files']}
    required = {
        'lib/wine/aarch64-unix/wine': 'macho',
        'bin/wineserver': 'macho',
        'lib/wine/aarch64-unix/ntdll.so': 'macho',
        'lib/wine/aarch64-unix/winemac.so': 'macho',
        'lib/wine/aarch64-unix/win32u.so': 'macho',
        'lib/wine/aarch64-windows/ntdll.dll': 'pe',
        'lib/wine/aarch64-windows/wineboot.exe': 'pe',
        'libexec/pear-stage2/bootstrap-native': 'macho',
        'libexec/pear-stage2/sentinel': 'macho',
    }
    need(suite in FIXTURE_SUITES, 'build_fixture_suite')
    if suite in PE_SUITES:
        required.update({path: 'pe' for path in fixture_pe_outputs(suite, publication_policy)})
        required['libexec/pear-stage3/api-launch'] = 'macho'
    need(variant in ('arm64', 'arm64ec-build'), 'build_variant')
    # This Wine pin links ARM64X companions at the aarch64-windows paths.
    # modules.validate_inventory independently requires actual CHPE/DVRT hybrid evidence.
    if variant == 'arm64ec-build':
        required.update({name: 'pe' for name in ARM64EC_PATHS})
    need(len(files) == len(artifacts['files']), 'build_duplicate_artifact')
    for name, kind in required.items():
        need(name in files and files[name]['kind'] == kind, 'build_required_outputs_missing')
    for row in files.values():
        if row['kind'] == 'macho':
            need(row['architectures'] == [MACH_ARM64], 'build_native_architecture')
        elif row['kind'] == 'pe':
            if row['path'] in fixture_pe_outputs(suite, publication_policy):
                need(row.get('machine') == fixture_pe_outputs(suite, publication_policy)[row['path']],
                     'build_fixture_pe_architecture')
            elif row['path'].startswith('lib/wine/aarch64-windows/'):
                if variant == 'arm64ec-build' and row['path'] in ARM64EC_PATHS:
                    need(row.get('machine') == 0x8664 and row.get('pe_abi') == 'arm64ec'
                         and row.get('chpe_version') == 2 and row.get('code_ranges')
                         and {item['code_kind'] for item in row['code_ranges']} == {'arm64ec', 'x64'},
                         'build_pe_architecture')
                else:
                    need(row.get('machine') == 0xAA64, 'build_pe_architecture')
            else:
                raise Error('build_unexpected_pe_path')
        elif row['kind'] == 'pe_metadata':
            need(row['path'] in WINMD_PATHS and row.get('metadata_only') is True
                 and row.get('machine') == 0x14C, 'build_metadata_scope')
    return files


def arena_capacity_evidence(source, install, artifacts):
    """Check the built ARM64 image inventory against the compiled finite owner limits."""
    header = Path(source) / 'dlls/ntdll/unix/pear_pe_arena.h'
    text = header.read_text()
    limits = {}
    for name in ('INTERIOR_BYTES', 'ALIGNMENT', 'MAX_IMAGE_BYTES', 'MAX_SLOTS', 'PAGE_BYTES'):
        rows = re.findall(r'^#define PEAR_ARENA_' + name + r' (?:\(\(SIZE_T\)([0-9]+)\)|([0-9]+)u)$',
                          text, re.MULTILINE)
        need(len(rows) == 1, 'arena_capacity_definition')
        limits[name.lower()] = int(rows[0][0] or rows[0][1])
    need(limits['alignment'] == 65536 and limits['page_bytes'] == 4096
         and limits['interior_bytes'] % limits['alignment'] == 0,
         'arena_capacity_geometry')
    copy_rows = re.findall(r'^#[ \t]*define[ \t]+PEAR_ARENA_RELOCATION_COPIES\b(.*)$', text, re.MULTILINE)
    need(not copy_rows or len(copy_rows) == 1 and copy_rows[0].strip() == '2u',
         'arena_fixture_copy_definition')
    copy_count = 2 if copy_rows else 0
    copy_path = 'libexec/pear-stage3/lifetime-arm64.dll'
    sizes, named_sizes = [], {}
    for row in artifacts['files']:
        if row.get('kind') != 'pe' or row.get('machine') != 0xAA64:
            continue
        path = Path(install).joinpath(*relative(row['path']))
        with path.open('rb') as stream:
            dos = stream.read(64)
            need(len(dos) == 64 and dos[:2] == b'MZ', 'arena_capacity_pe_header')
            offset = struct.unpack_from('<I', dos, 60)[0]
            need(64 <= offset <= path.stat().st_size - 84, 'arena_capacity_pe_header')
            stream.seek(offset)
            pe = stream.read(84)
        need(pe[:4] == b'PE\0\0' and struct.unpack_from('<H', pe, 4)[0] == 0xAA64
             and struct.unpack_from('<H', pe, 24)[0] == 0x20B, 'arena_capacity_pe_header')
        size = struct.unpack_from('<I', pe, 80)[0]
        need(size > 0 and size % limits['page_bytes'] == 0, 'arena_capacity_pe_size')
        rounded = (size + limits['alignment'] - 1) & ~(limits['alignment'] - 1)
        sizes.append(rounded)
        named_sizes[row['path']] = rounded
    need(sizes, 'arena_capacity_inventory_empty')
    if copy_count:
        need(copy_path in named_sizes, 'arena_fixture_copy_source_missing')
    copy_slot_bytes = named_sizes.get(copy_path, 0) if copy_count else 0
    copy_bytes = copy_count * copy_slot_bytes
    largest, total = max(sizes), sum(sizes)
    required_bytes, required_slots = total + largest + copy_bytes, len(sizes) + 1 + copy_count
    need(largest <= limits['max_image_bytes'] and required_slots <= limits['max_slots']
         and required_bytes <= limits['interior_bytes'], 'arena_capacity_inventory_exceeds_limits')
    result = {'policy': 'page-wx', 'header_sha256': sha256(header), 'limits': limits,
              'arm64_image_count': len(sizes), 'total_slot_bytes': total,
              'largest_slot_bytes': largest, 'preparation_margin_bytes': largest,
              'required_interior_bytes': required_bytes, 'required_slots': required_slots,
              'wine_execution': False}
    dynamic_names = ('BYTES', 'SLOTS', 'SLOT_BYTES')
    dynamic = {}
    for name in dynamic_names:
        rows = re.findall(r'^#define PEAR_ARENA_DYNAMIC_' + name + r' (?:\(\(SIZE_T\)([0-9]+)\)|([0-9]+)u)$',
                          text, re.MULTILINE)
        need(len(rows) <= 1, 'arena_dynamic_capacity_definition')
        if rows:
            dynamic[name.lower()] = int(rows[0][0] or rows[0][1])
    if dynamic:
        need(dynamic == {'bytes': 524288, 'slots': 8, 'slot_bytes': 65536},
             'arena_dynamic_capacity_geometry')
        need(re.search(r'^#define PEAR_ARENA_TOTAL_BYTES \(PEAR_ARENA_INTERIOR_BYTES \+ PEAR_ARENA_DYNAMIC_BYTES\)$', text, re.MULTILINE)
             and re.search(r'^#define PEAR_ARENA_MAPPING_BYTES \(PEAR_ARENA_TOTAL_BYTES \+ PEAR_ARENA_ALIGNMENT\)$', text, re.MULTILINE),
             'arena_dynamic_mapping_capacity')
        result['dynamic_limits'] = dynamic
    # Historical headers had no copy allowance; preserve their exact evidence shape.
    if copy_count:
        result['fixture_copies'] = {'path': copy_path, 'count': copy_count,
                                   'slot_bytes': copy_slot_bytes, 'total_bytes': copy_bytes}
    return result


def build(variant_name, inputs, tools, output, jobs):
    need(type(jobs) is int and 1 <= jobs <= 4, 'build_parallelism')
    config = record(load_json(REPO / RECORDS['config']), 'wine_build_config')
    variants = [row for row in config['variants'] if row['id'] == variant_name]
    need(len(variants) == 1, 'build_variant')
    variant = variants[0]
    lock = record(load_json(REPO / RECORDS['toolchain']), 'wine_toolchain')
    inputs, tools = task_path(inputs).resolve(), task_path(tools).resolve()
    prepared = verify_prepared(inputs, sha256(REPO / RECORDS['inputs']))
    prepared_tools = verify_prepared_tools(lock, tools)
    need(prepared_tools['lock_sha256'] == sha256(REPO / RECORDS['toolchain']), 'build_tool_lock')
    sdk = inspect_sdk(lock)
    need(sdk['version'] == config['sdk_version'], 'build_sdk_mismatch')
    series = record(load_json(REPO / RECORDS['patch_series']), 'wine_patch_series')
    need(series['base_commit'] == prepared['components'][0]['commit']
         and series.get('port_complete') is False and isinstance(series.get('patches'), list), 'build_patch_base')
    suite = fixture_suite(series)
    policy = code_publication_policy(series)
    patch_paths = [validate_patch(series, row) for row in series['patches']]
    minimum_space = (8 if variant_name == 'arm64' else 12) * 1024**3
    free = shutil.disk_usage(REPO).free
    need(free >= minimum_space, 'build_storage_budget')
    output = empty_directory(output).resolve()
    result = {'schema_version': 1, 'record_kind': 'wine_build', 'scope': 'wine_component',
              'variant': variant_name, 'fixture_suite': suite, 'code_publication_policy': policy,
              'record_hashes': {key: sha256(REPO / value) for key, value in RECORDS.items()},
              'inputs_sha256': sha256(REPO / RECORDS['inputs']),
              'config_sha256': sha256(REPO / RECORDS['config']),
              'toolchain_lock_sha256': sha256(REPO / RECORDS['toolchain']),
              'source_prepared_sha256': sha256(inputs / 'prepared.json'),
              'tool_prepared_sha256': sha256(tools / 'prepared.json'),
              'patch_series_sha256': sha256(REPO / RECORDS['patch_series']),
              'producer_sha256': {name: sha256(Path(__file__).parent / name) for name in ('build.py','common.py','prepare.py','toolchain.py')},
              'fixture_hashes': {name: sha256(REPO / 'tests/wine/fixtures' / name) for name in fixture_sources(series)},
              'patches': series['patches'], 'sdk': sdk, 'commands': [],
              'storage': {'free_bytes_before': free, 'required_free_bytes': minimum_space},
              'source_inputs_root': str(inputs), 'tools_root': str(tools), 'install_root': str(output / 'install'),
              'wine_runtime_execution': False, 'passed': False}
    try:
        (output / 'producer').mkdir()
        for name in result['producer_sha256']:
            shutil.copyfile(Path(__file__).parent / name, output / 'producer' / name)
        source = output / 'source'
        shutil.copytree(inputs / 'wine', source, symlinks=False)
        copied = inventory(source)
        original = load_json(inputs / 'wine-files.json')['files']
        need(len(copied['files']) == len(original) and not copied['symlinks'], 'build_source_copy_count')
        for actual, expected in zip(copied['files'], original):
            need(actual['path'] == expected['path'] and actual['sha256'] == expected['sha256']
                 and actual['mode'] == (0o755 if expected['mode'] == '100755' else 0o644), 'build_source_copy_changed')
        alias = alias_directory(REPO / '.build/task4')
        result['path_alias'] = {'invoked': str(alias), 'resolved': str(alias.resolve())}
        def logical(path):
            return alias / Path(path).absolute().relative_to(alias.resolve())
        sdk_path = lock['sdk']['path']
        env = base_env(sdk_path, [logical(tools / 'llvm-mingw/bin'), logical(tools / 'bison/bin')])
        env.update(CC=str(native_tool(lock, 'clang')), CXX=str(native_tool(lock, 'clang++')),
                   BISON=str(logical(tools / 'bison/bin/bison')), FLEX=str(native_tool(lock, 'flex')),
                   CFLAGS='-arch arm64 -isysroot ' + sdk_path,
                   CXXFLAGS='-arch arm64 -isysroot ' + sdk_path,
                   MACOSX_DEPLOYMENT_TARGET=config['deployment_target'])
        patch_tool = Path('/usr/bin/patch')
        result['patch_tool'] = {'path': str(patch_tool), 'sha256': sha256(patch_tool), **inspect_macho(patch_tool)}
        for index, path in enumerate(patch_paths, 1):
            changes = series['patches'][index - 1].get('changes', [])
            need(changes, 'patch_preimages_missing')
            for change in changes:
                target = source.joinpath(*relative(change['path']))
                before = change['before_sha256']
                need((not target.exists()) if before is None else sha256(target) == before, 'patch_preimage_changed')
            run_build_command(result['commands'], 'patch-' + str(index),
                              [patch_tool, '-p1', '--batch', '--forward', '--fuzz=0', '-i', path],
                              logical(source), env, 30)
            for change in changes:
                need(sha256(source.joinpath(*relative(change['path']))) == change['after_sha256'], 'patch_result_changed')
        # Logs describe operations, not upstream source bytes.
        patch_logs = source / '.pear-build-logs'
        if patch_logs.exists():
            retained = output / 'patch-logs'
            patch_logs.rename(retained)
            for row in result['commands']:
                for stream in ('stdout_log', 'stderr_log'):
                    row[stream]['path'] = str(retained / Path(row[stream]['path']).name)
        source_manifest = output / 'source-files.json'
        patched_inventory = inventory(source)
        verify_source_derivation(patched_inventory, load_json(inputs / 'wine-files.json'), series['patches'])
        write_new(source_manifest, patched_inventory)
        result['source_manifest'] = {'path': source_manifest.name, 'sha256': sha256(source_manifest)}
        objects = output / 'objects'
        objects.mkdir()
        cwd = logical(objects)
        env['PWD'] = str(cwd)
        argv = [logical(source / 'configure'), '--prefix=' + str(logical(output / 'install')),
                '--with-mingw=' + str(logical(tools / 'llvm-mingw/bin/clang')), *variant['configure_args']]
        run_build_command(result['commands'], 'configure', argv, cwd, env, 300)
        result['configuration'] = observed_configuration(objects / 'Makefile', variant, policy,
                                    native_architecture_policy=has_native_architecture_policy(series))
        result['makefile_sha256'] = sha256(objects / 'Makefile')
        result['config_log_sha256'] = sha256(objects / 'config.log')
        make = native_tool(lock, 'make')
        run_build_command(result['commands'], 'make', [make, '-j' + str(jobs)], cwd, env, 3600)
        run_build_command(result['commands'], 'install', [make, 'install'], cwd, env, 600)
        result['configuration'] = observed_configuration(objects / 'Makefile', variant, policy,
                                    native_architecture_policy=has_native_architecture_policy(series))
        (output / 'install/libexec/pear-stage2').mkdir(parents=True)
        if suite in PE_SUITES:
            (output / 'install/libexec/pear-stage3').mkdir(parents=True)
            need(sha256(source / 'dlls/ntdll/unix/pear_abi_fixture.c') == result['fixture_hashes']['abi_native.c'],
                 'build_native_fixture_source_mismatch')
        if suite in (STAGE4_SUITE, STAGE5_SUITE):
            (output / 'install/libexec/pear-stage4').mkdir(parents=True)
            verify_stage4_native_fixture(source, result['fixture_hashes'])
        if suite == STAGE5_SUITE:
            (output / 'install/libexec/pear-stage5').mkdir(parents=True)
            verify_stage5_native_fixture(source, result['fixture_hashes'])
        for ident, argv in fixture_commands(output, tools, lock, suite, policy).items():
            run_build_command(result['commands'], ident, argv, cwd, env, 60)
        artifacts = inventory(output / 'install', binary=True)
        if policy == 'page-wx':
            result['arena_capacity'] = arena_capacity_evidence(source, output / 'install', artifacts)
        required_outputs(artifacts, variant_name, suite, policy)
        native = [x for x in artifacts['files'] if x['kind'] == 'macho']
        guests = [x for x in artifacts['files'] if x['kind'] == 'pe']
        need(native and guests and any(x['path'].endswith('/ntdll.so') for x in native)
             and any(Path(x['path']).name == 'wineserver' for x in native), 'build_required_outputs_missing')
        manifest_path = output / 'installed-files.json'
        write_new(manifest_path, artifacts)
        result.update(artifacts_manifest={'path': manifest_path.name, 'sha256': sha256(manifest_path)},
                      native_artifact_count=len(native), pe_artifact_count=len(guests), passed=True)
        need(inventory(source) == load_json(source_manifest), 'build_mutated_source')
    except KeyboardInterrupt:
        result.update(passed=False, error='build_interrupted', private_error='Interrupted outside a running build command.')
    except (Error, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        result.update(passed=False, error=getattr(exc, 'code', 'build_operation_failed'))
        result['private_error'] = str(exc)
    write_new(output / 'build.json', result)
    return 0 if result['passed'] else 3


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=('arm64','arm64ec-build'))
    parser.add_argument('--inputs')
    parser.add_argument('--tools')
    parser.add_argument('--output')
    parser.add_argument('--jobs', type=int)
    parser.add_argument('--finalize-only', metavar='EXISTING_OUTPUT')
    args = parser.parse_args(argv)
    try:
        if args.finalize_only is not None:
            need(all(value is None for value in (args.variant, args.inputs, args.tools, args.output, args.jobs)),
                 'build_mixed_modes')
            return finalize_only(args.finalize_only)
        need(all(value is not None for value in (args.variant, args.inputs, args.tools, args.output)),
             'build_missing_arguments')
        return build(args.variant, args.inputs, args.tools, args.output, 4 if args.jobs is None else args.jobs)
    except (Error, OSError, ValueError, KeyError, TypeError) as exc:
        print(encoded({'error': getattr(exc, 'code', 'build_operation_failed')}).decode(), end='')
        return 1


if __name__ == '__main__':
    sys.exit(main())
