#!/usr/bin/env python3
"""Compile a source-bound finite owner prototype; never execute it.

This first slice does not initialize FEX, register Wine EC views, load a PE or
qualify the full Stage 3 gate. Its exact source and failures remain private.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys

if __package__:
    from .common import (REPO, Error, need, load_json, sha256, read_relative,
                        operation_output, write_json, bounded_command, relative, digest_bytes)
else:
    from common import (REPO, Error, need, load_json, sha256, read_relative,
                        operation_output, write_json, bounded_command, relative, digest_bytes)
if __package__:
    from . import build as baseline
else:
    import build as baseline

OWNER_FILES = ('include/wine/pear_fex_memory.h',
               'dlls/ntdll/unix/pear_fex_memory_private.h',
               'dlls/ntdll/unix/pear_fex_memory.c',
               'dlls/ntdll/unix/pear_pe_arena.h',
               'dlls/ntdll/unix/pear_pe_arena.c')
FIXTURES = ('tests/fex/memory/native_cooperative.c', 'tests/fex/memory/native_owner.c', 'tests/fex/memory/fixture_suite.c',
            'tests/fex/memory/fixture_suite.h', 'tests/fex/memory/wine_debug_quiet.c',
            'tests/wine/fixtures/api_launch.c', 'tests/wine/fixtures/sentinel.c')
WINE_SOURCE = '2c0c861669f9fd8853f8899eaeb08b18207b0cf26b34dae9efe707919e447bc7'


def command(root, name, argv, env, rows):
    logs = root / 'logs' / name
    logs.mkdir(parents=True)
    row = {'id': name, 'argv': argv, 'environment': env, 'exit_code': None, 'logs': {}}
    rows.append(row)
    try:
        result = bounded_command(argv, cwd=root, output_dir=logs, env=env,
                                 timeout=60, max_output=2 * 1024**2)
        row.update(exit_code=result['returncode'], elapsed_ms=result['elapsed_ms'], status=result['status'])
    finally:
        for channel in ['stdout', 'stderr']:
            path = logs / (channel + '.bin')
            if path.exists():
                row['logs'][channel] = {'path': path.relative_to(root).as_posix(),
                                        'sha256': sha256(path), 'size_bytes': path.stat().st_size}
    need(row['exit_code'] == 0, 'memory_compile_failed:' + name)


def compile_fixture(source, wine_root, output):
    source = Path(source).absolute()
    need(source.is_dir() and not source.is_symlink(), 'memory_owner_source_root')
    manifests = load_json(source / 'core-source-files.json')
    series_path = REPO / 'runtime/fex/patches/memory-series.json'
    series = load_json(series_path)
    need(series['component'] == 'wine-fex-memory' and series['runtime_execution'] is False,
         'memory_source_series_scope')
    row = series['patches'][0]
    patch_path = REPO / 'runtime/fex/patches' / row['file']
    need(row['file'] == 'memory/0003a-wine-owner-core.patch' and sha256(patch_path) == row['sha256'],
         'memory_source_patch_changed')
    selected = {item['path']: {'baseline_sha256': item['preimage_sha256'],
                'sha256': item['postimage_sha256'], 'bytes': item['postimage_bytes']}
                for item in row['sources']}
    need(manifests == selected, 'memory_source_manifest_differs_from_patch')
    sections = baseline.patch_sections(read_relative(patch_path.parent, patch_path.name, 2 * 1024**2))
    need(set(sections) == set(OWNER_FILES), 'memory_source_patch_set')
    need(type(manifests) is dict and set(manifests) == set(OWNER_FILES), 'memory_owner_source_set')
    wine_root = Path(wine_root).absolute()
    wine = load_json(wine_root / 'build.json')
    need(wine['passed'] is True and wine['variant'] == 'arm64' and
         wine['source_manifest']['sha256'] == WINE_SOURCE and
         sha256(wine_root / wine['source_manifest']['path']) == WINE_SOURCE, 'memory_wine_baseline')
    wine_files = load_json(wine_root / wine['source_manifest']['path'])['files']
    before = {row['path']: row for row in wine_files}
    root = operation_output(output, require_empty=True)
    value = {'schema_version': 1, 'record_kind': 'fex_memory_prototype_build',
             'scope': 'finite_native_owner', 'wine_build_ref': {'path': str(wine_root),
                 'sha256': sha256(wine_root / 'build.json')},
             'source_manifest_sha256': sha256(source / 'core-source-files.json'),
             'source_manifest_path': 'inputs/core-source-files.json',
             'patch_sha256': row['sha256'], 'series_sha256': sha256(series_path),
             'series_snapshot': 'inputs/memory-series.json',
             'sources': {}, 'baseline_headers': [], 'commands': [], 'artifacts': [],
             'producers': {name: sha256(REPO / name) for name in
                           ['tools/fex/memory_build.py', 'tools/fex/build.py', 'tools/fex/common.py',
                            'tools/wine/common.py', 'tools/fex/byte_readers.py']},
             'passed': False, 'native_execution': False, 'checked_ec': False,
             'fex_initialization': False, 'translated_guest_execution': False,
             'game_qualified': False, 'runtime_eligible': False}
    try:
        for name in value['producers']:
            target = root / 'producers' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(read_relative(REPO, name, 2 * 1024**2))
        (root / 'inputs').mkdir(exist_ok=True)
        (root / value['series_snapshot']).write_bytes(read_relative(series_path.parent, series_path.name, 2 * 1024**2))
        (root / value['source_manifest_path']).write_bytes(read_relative(source, 'core-source-files.json', 2 * 1024**2))
        need(shutil.disk_usage(root).free >= 512 * 1024**2, 'memory_compile_storage')
        for name in OWNER_FILES:
            facts = manifests[name]
            need(set(facts) == {'baseline_sha256', 'sha256', 'bytes'}, 'memory_owner_source_fields')
            raw = read_relative(source, name, 2 * 1024**2)
            need(digest_bytes(raw) == facts['sha256'] and len(raw) == facts['bytes'], 'memory_owner_source_bytes')
            if facts['baseline_sha256'] is not None:
                need(name in before and before[name]['sha256'] == facts['baseline_sha256'] and
                     sha256(wine_root / 'source' / name) == facts['baseline_sha256'], 'memory_owner_preimage')
            else:
                need(name not in before, 'memory_owner_addition')
            original = None if facts['baseline_sha256'] is None else read_relative(wine_root / 'source', name, 2 * 1024**2)
            lines = sections[name]
            if original is None and lines[:1] == ['new file mode 100644\n']:
                lines = lines[1:]
            need(baseline.apply_hunks(original, lines, name) == raw, 'memory_source_patch_derivation')
            target = root / 'source' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            value['sources']['source/' + name] = facts['sha256']
        # Copy canonical Wine headers only from the retained verified source.
        for row in wine_files:
            name = row['path']
            if not name.startswith('include/'):
                continue
            raw = read_relative(wine_root / 'source', name, 8 * 1024**2)
            need(digest_bytes(raw) == row['sha256'], 'memory_baseline_header_changed')
            target = root / 'baseline' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            value['baseline_headers'].append({'path': 'baseline/' + name, 'sha256': row['sha256']})
        generated = wine_root / 'objects/include/config.h'
        target = root / 'baseline/config.h'
        target.write_bytes(read_relative(generated.parent, generated.name, 1024**2))
        value['baseline_config_sha256'] = sha256(target)
        for name in FIXTURES:
            raw = read_relative(REPO, name, 2 * 1024**2)
            target = root / 'inputs' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            value['sources']['inputs/' + name] = sha256(target)
        lock = load_json(REPO / 'runtime/wine/toolchain.json')
        value['toolchain_sha256'] = sha256(REPO / 'runtime/wine/toolchain.json')
        compiler = next(row for row in lock['native_tools'] if row['id'] == 'clang')
        need(sha256(Path(compiler['path'])) == compiler['sha256'], 'memory_compiler_changed')
        flags = ['/usr/bin/arch', '-arm64', compiler['path'], '-arch', 'arm64',
                 '-isysroot', lock['sdk']['path'], '-mmacosx-version-min=' + lock['sdk']['version'],
                 '-std=c11', '-Wall', '-Wextra', '-Werror']
        env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL': 'C', 'LANG': 'C',
               'TMPDIR': str(root)}
        (root / 'unsigned').mkdir()
        unix = root / 'source/dlls/ntdll/unix'
        fixture = root / 'inputs/tests/fex/memory'
        argv = [*flags, '-D__WINESRC__', '-DWINE_UNIX_LIB', '-DPEAR_NATIVE_PE_PUBLICATION',
                '-I' + str(root / 'source/include'), '-I' + str(root / 'baseline'),
                '-I' + str(root / 'baseline/include'), '-I' + str(unix),
                '-I' + str(fixture), str(unix / 'pear_pe_arena.c'), str(unix / 'pear_fex_memory.c'),
                str(fixture / 'native_owner.c'), str(fixture / 'fixture_suite.c'),
                str(fixture / 'wine_debug_quiet.c'),
                '-Wl,-x86_64_layout_emulation,-segalign,0x1000,-pagezero_size,0x10000',
                '-o', str(root / 'unsigned/pear-fex-memory')]
        source_position = argv.index(str(unix / 'pear_pe_arena.c'))
        arena_object = root / 'unsigned/pear-pe-arena.o'
        arena_argv = [*argv[:source_position], '-Wno-error=sign-compare', '-c',
                      str(unix / 'pear_pe_arena.c'), '-o', str(arena_object)]
        command(root, 'baseline-arena.compile', arena_argv, env, value['commands'])
        arena_warnings = (root / 'logs/baseline-arena.compile/stderr.bin').read_text()
        import re
        warning_lines = [line for line in arena_warnings.splitlines() if 'warning:' in line]
        need(len(warning_lines) == 4 and all('pear_pe_arena.c:' in line and
             '[-Wsign-compare]' in line for line in warning_lines), 'memory_unreviewed_baseline_warning')
        value['baseline_sign_comparison_warnings'] = len(warning_lines)
        argv[source_position] = str(arena_object)
        command(root, 'owner.compile', argv, env, value['commands'])
        cooperative = [item for item in argv if item not in
            [str(fixture / 'native_owner.c'), str(fixture / 'fixture_suite.c')]]
        position = cooperative.index(str(fixture / 'wine_debug_quiet.c'))
        cooperative[position:position] = [str(fixture / 'native_cooperative.c')]
        cooperative[-1] = str(root / 'unsigned/pear-fex-cooperative')
        command(root, 'cooperative.compile', cooperative, env, value['commands'])
        for name, output in [('api_launch.c', 'api-launch'), ('sentinel.c', 'sentinel')]:
            command(root, output + '.compile', [*flags,
                    str(root / 'inputs/tests/wine/fixtures' / name), '-o', str(root / 'unsigned' / output)],
                    env, value['commands'])
        reader = baseline.wine_readers()
        for name in ['pear-fex-memory', 'pear-fex-cooperative', 'api-launch', 'sentinel']:
            path = root / 'unsigned' / name
            facts = reader.inspect_macho(path)
            need(facts['architectures'] == [0x100000c] and facts['filetype'] == 2 and
                 all(dep.startswith(('/usr/lib/', '/System/Library/')) for dep in facts['dependencies']),
                 'memory_fixture_native_closure')
            value['artifacts'].append({'path': path.relative_to(root).as_posix(),
                'sha256': sha256(path), 'size_bytes': path.stat().st_size, **facts})
        need(sha256(source / 'core-source-files.json') == value['source_manifest_sha256'] and
             sha256(series_path) == value['series_sha256'] and
             all(sha256(REPO / name) == expected for name, expected in value['producers'].items()) and
             all(sha256(REPO / name) == value['sources']['inputs/' + name] for name in FIXTURES),
             'memory_source_changed')
        value['passed'] = True
        write_json(root / 'build.json', value)
        return value
    except (Error, OSError, ValueError, KeyError) as error:
        value.update(error=getattr(error, 'code', type(error).__name__), passed=False)
        write_json(root / 'failed.json', value)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--wine-build', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--require-empty', required=True, action='store_true')
    args = parser.parse_args()
    try:
        compile_fixture(args.source, args.wine_build, args.output)
        print('Finite native prototype compiled; execution and full Stage 3 qualification are unperformed.')
        return 0
    except (Error, OSError, ValueError, KeyError) as error:
        print(getattr(error, 'code', type(error).__name__), file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
