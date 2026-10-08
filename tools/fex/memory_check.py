"""Independent byte checks for finite native owner build records.

A valid prototype is not a completed FEX source-integration or runtime gate.
"""
from pathlib import Path
if __package__:
    from .common import REPO, need, load_json, sha256, read_relative, digest_bytes, relative, operation_output
else:
    from common import REPO, need, load_json, sha256, read_relative, digest_bytes, relative, operation_output
if __package__:
    from . import build as baseline
else:
    import build as baseline

FALSE_SCOPE = ('native_execution', 'checked_ec', 'fex_initialization',
               'translated_guest_execution', 'game_qualified', 'runtime_eligible')
COMMANDS = ('baseline-arena.compile', 'owner.compile', 'cooperative.compile',
            'api-launch.compile', 'sentinel.compile')
ARTIFACTS = ('pear-fex-memory', 'pear-fex-cooperative', 'api-launch', 'sentinel')


def verify_build(root):
    root = operation_output(root, repo_root=REPO, require_empty=False, create=False)
    need(root.is_dir(), 'memory_build_root')
    value = load_json(root / 'build.json')
    need(type(value['schema_version']) is int and value['schema_version'] == 1 and value['record_kind'] == 'fex_memory_prototype_build'
         and value['scope'] == 'finite_native_owner' and value['passed'] is True,
         'memory_build_scope')
    need(all(value[key] is False for key in FALSE_SCOPE), 'memory_build_overclaim')
    series = REPO / 'runtime/fex/patches/memory-series.json'
    need(value['series_snapshot'] == 'inputs/memory-series.json' and
         sha256(root / value['series_snapshot']) == value['series_sha256'], 'memory_build_series_changed')
    snapshot = load_json(root / value['series_snapshot'])
    current = load_json(series)
    need(snapshot['component'] == current['component'] == 'wine-fex-memory' and
         snapshot['baseline'] == current['baseline'] and snapshot['patches'][0] == current['patches'][0],
         'memory_build_core_selection_changed')
    source = snapshot['patches'][0]
    need(source['sha256'] == value['patch_sha256'] and
         sha256(REPO / 'runtime/fex/patches' / source['file']) == source['sha256'],
         'memory_build_patch_changed')
    expected_producers = {'tools/fex/memory_build.py', 'tools/fex/build.py', 'tools/fex/common.py',
                          'tools/wine/common.py', 'tools/fex/byte_readers.py'}
    need(set(value['producers']) == expected_producers, 'memory_build_producer_set')
    wine_root = Path(value['wine_build_ref']['path'])
    need(sha256(wine_root / 'build.json') == value['wine_build_ref']['sha256'], 'memory_build_wine_ref')
    wine = load_json(wine_root / 'build.json')
    need(wine['passed'] is True and wine['variant'] == 'arm64' and
         wine['source_manifest']['sha256'] == '2c0c861669f9fd8853f8899eaeb08b18207b0cf26b34dae9efe707919e447bc7' and
         sha256(wine_root / wine['source_manifest']['path']) == wine['source_manifest']['sha256'], 'memory_build_wine_source')
    wine_files = load_json(wine_root / wine['source_manifest']['path'])['files']
    expected_headers = [{'path': 'baseline/' + row['path'], 'sha256': row['sha256']}
                        for row in wine_files if row['path'].startswith('include/')]
    need(value['baseline_headers'] == expected_headers, 'memory_build_header_set')
    need(value['baseline_config_sha256'] == sha256(wine_root / 'objects/include/config.h') and
         sha256(wine_root / 'objects/Makefile') == wine['makefile_sha256'] and
         sha256(wine_root / 'objects/config.log') == wine['config_log_sha256'], 'memory_build_wine_config')
    lock = load_json(REPO / 'runtime/wine/toolchain.json')
    need(sha256(REPO / 'runtime/wine/toolchain.json') == value['toolchain_sha256'] == wine['toolchain_lock_sha256'],
         'memory_build_toolchain_changed')
    need(value['source_manifest_path'] == 'inputs/core-source-files.json' and
         sha256(root / value['source_manifest_path']) == value['source_manifest_sha256'], 'memory_build_source_manifest')
    manifest = load_json(root / value['source_manifest_path'])
    expected_manifest = {row['path']: {'baseline_sha256': row['preimage_sha256'],
             'sha256': row['postimage_sha256'], 'bytes': row['postimage_bytes']} for row in source['sources']}
    need(manifest == expected_manifest, 'memory_build_source_postimages')
    fixtures = ('tests/fex/memory/native_cooperative.c', 'tests/fex/memory/native_owner.c',
       'tests/fex/memory/fixture_suite.c', 'tests/fex/memory/fixture_suite.h', 'tests/fex/memory/wine_debug_quiet.c',
       'tests/wine/fixtures/api_launch.c', 'tests/wine/fixtures/sentinel.c')
    selected_sources = {'source/' + name: row['sha256'] for name, row in expected_manifest.items()}
    selected_sources.update({'inputs/' + name: sha256(REPO / name) for name in fixtures})
    need(value['sources'] == selected_sources, 'memory_build_source_set')
    for name, expected in value['producers'].items():
        need(name.startswith(('tools/fex/', 'tools/wine/')), 'memory_build_producer_path')
        relative(name)
        need(sha256(REPO / name) == expected and
             sha256(root / 'producers' / name) == expected, 'memory_build_producer_changed')
    for name, expected in value['sources'].items():
        relative(name)
        need(sha256(root / name) == expected, 'memory_build_source_changed')
    for row in value['baseline_headers']:
        relative(row['path'])
        need(row['path'].startswith('baseline/include/') and sha256(root / row['path']) == row['sha256'],
             'memory_build_header_changed')
    need(sha256(root / 'baseline/config.h') == value['baseline_config_sha256'], 'memory_build_config_changed')
    need([row['id'] for row in value['commands']] == list(COMMANDS), 'memory_build_command_set')
    compiler = next(row for row in lock['native_tools'] if row['id'] == 'clang')
    need(sha256(Path(compiler['path'])) == compiler['sha256'], 'memory_build_compiler_changed')
    flags = ['/usr/bin/arch', '-arm64', compiler['path'], '-arch', 'arm64',
        '-isysroot', lock['sdk']['path'], '-mmacosx-version-min=' + lock['sdk']['version'],
        '-std=c11', '-Wall', '-Wextra', '-Werror']
    unix = root / 'source/dlls/ntdll/unix'; fixture = root / 'inputs/tests/fex/memory'
    include = ['-D__WINESRC__', '-DWINE_UNIX_LIB', '-DPEAR_NATIVE_PE_PUBLICATION',
        '-I' + str(root / 'source/include'), '-I' + str(root / 'baseline'), '-I' + str(root / 'baseline/include'),
        '-I' + str(unix), '-I' + str(fixture)]
    common_sources = [str(root / 'unsigned/pear-pe-arena.o'), str(unix / 'pear_fex_memory.c')]
    layout = ['-Wl,-x86_64_layout_emulation,-segalign,0x1000,-pagezero_size,0x10000']
    commands = [
       [*flags, *include, '-Wno-error=sign-compare', '-c', str(unix / 'pear_pe_arena.c'), '-o', str(root / 'unsigned/pear-pe-arena.o')],
       [*flags, *include, *common_sources, str(fixture / 'native_owner.c'), str(fixture / 'fixture_suite.c'),
         str(fixture / 'wine_debug_quiet.c'), *layout, '-o', str(root / 'unsigned/pear-fex-memory')],
       [*flags, *include, *common_sources, str(fixture / 'native_cooperative.c'), str(fixture / 'wine_debug_quiet.c'),
         *layout, '-o', str(root / 'unsigned/pear-fex-cooperative')],
       [*flags, str(root / 'inputs/tests/wine/fixtures/api_launch.c'), '-o', str(root / 'unsigned/api-launch')],
       [*flags, str(root / 'inputs/tests/wine/fixtures/sentinel.c'), '-o', str(root / 'unsigned/sentinel')]]
    env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL': 'C', 'LANG': 'C', 'TMPDIR': str(root)}
    need([row['argv'] for row in value['commands']] == commands and
         all(row['environment'] == env for row in value['commands']), 'memory_build_recipe_changed')
    for row in value['commands']:
        need(row['exit_code'] == 0 and row['status'] == 'completed', 'memory_build_command_failed')
        need(set(row['logs']) == {'stdout', 'stderr'}, 'memory_build_log_set')
        for ref in row['logs'].values():
            raw = read_relative(root, ref['path'], 2 * 1024**2)
            need(digest_bytes(raw) == ref['sha256'] and len(raw) == ref['size_bytes'], 'memory_build_log_changed')
    need([row['path'] for row in value['artifacts']] == ['unsigned/' + name for name in ARTIFACTS],
         'memory_build_artifact_set')
    reader = baseline.wine_readers()
    for row in value['artifacts']:
        path = root / row['path']
        raw = read_relative(root, row['path'], 2 * 1024**2)
        need(digest_bytes(raw) == row['sha256'] and len(raw) == row['size_bytes'], 'memory_build_artifact_changed')
        facts = reader.inspect_macho(path)
        need(all(row[key] == observed for key, observed in facts.items()), 'memory_build_native_observation_changed')
        need(facts['architectures'] == [0x100000c] and facts['filetype'] == 2 and
             all(dep.startswith(('/usr/lib/', '/System/Library/')) for dep in facts['dependencies']),
             'memory_build_native_closure')
    return value
