#!/usr/bin/env python3
"""Rebuild both final FEX modules and native UnixLibs without prior objects.

Retain the existing complete compiler recipe and object/dependency inspector.
Historical source snapshots are verified; they are not historical build reuse.
"""
from pathlib import Path
import argparse
import fcntl
import json
import shutil
import sys

if not __package__:
    here = Path(__file__).resolve().parent
    sys.path[:] = [p for p in sys.path if Path(p or '.').resolve() != here]
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.fex.common import REPO, need, sha256, relative
from tools.fex.reconstruct import FEX_BASE, H, read_bound, save, run
from tools.fex import build, memory_fex_build, memory_fex_check as check, tools


def derive(base, manifest):
    series_path = REPO / 'runtime/fex/patches/integration/fex-series.json'
    series = json.loads(series_path.read_text())
    sources = {}
    for patch in series['patches']:
        relative(patch['file'])
        raw = (series_path.parent / patch['file']).read_bytes()
        need(H(raw) == patch['sha256'], 'reconstruct_fex_patch_changed')
        sections = build.patch_sections(raw)
        need(set(sections) == {r['path'] for r in patch['sources']}, 'reconstruct_fex_patch_closure')
        for row in patch['sources']:
            relative(row['path'])
            prior = sources.get(row['path'])
            if prior is None:
                prior = (base / 'source' / row['path']).read_bytes()
            need(H(prior) == row['preimage_sha256'], 'reconstruct_fex_preimage')
            result = build.apply_hunks(prior, sections[row['path']], row['path'])
            need(H(result) == row['postimage_sha256'] and len(result) == row['postimage_bytes'],
                 'reconstruct_fex_postimage')
            sources[row['path']] = result
    need(set(sources) <= {r['path'] for r in manifest['files']}, 'reconstruct_fex_source_set')
    return sources


def construct(base, wine, output):
    old = read_bound(base / 'build.json', FEX_BASE)
    manifest = read_bound(base / 'materialized-source.json', old['materialized_source']['sha256'])
    original = read_bound(Path(old['bindings']['baseline']['root']) / 'build.json',
                          old['bindings']['baseline']['sha256'])
    bindings = original['bindings']
    for name in ('config', 'toolchain', 'host_metadata', 'inputs'):
        read_bound(Path(bindings[name]['path']), bindings[name]['sha256'])
    tool_root = Path(bindings['tools']['path'])
    read_bound(tool_root / 'prepared.json', bindings['tools']['sha256'])
    tools.verify_tools(tool_root, Path(bindings['toolchain']['path']))
    lock = json.loads(Path(bindings['toolchain']['path']).read_text())
    config = build.validate_config(json.loads(Path(bindings['config']['path']).read_text()),
                                   bindings['inputs']['sha256'])
    features = build.host_metadata(Path(bindings['host_metadata']['path']))
    cross = original['cross']
    # The current Wine reconstruction has just admitted the complete cross-tool
    # archive. Verify it again independently for this compiler invocation.
    build.verify_cross(lock, Path(cross['cross_tools']), Path(cross['archive']))
    for row in cross['build_auxiliary_tools'].values():
        need(sha256(Path(row['path']).resolve(strict=True)) == row['sha256'],
             'reconstruct_fex_auxiliary_changed')
    changed = derive(base, manifest)
    memory_fex_build.copy_source(base / 'source', output / 'source', manifest['files'])
    for row in manifest['files']:
        if row['path'] in changed:
            raw = changed[row['path']]
            (output / 'source' / row['path']).write_bytes(raw)
            row.update(sha256=H(raw), size_bytes=len(raw))
    need(check.source_inventory(output / 'source') == manifest['files'], 'reconstruct_fex_materialization')
    save(output / 'materialized-source.json', manifest)
    wire = (wine / 'source/include/wine/pear_fex_memory.h').read_bytes()
    need(H(wire) == old['wire']['sha256'], 'reconstruct_fex_wire_changed')
    (output / 'wire/wine').mkdir(parents=True)
    (output / 'wire/wine/pear_fex_memory.h').write_bytes(wire)
    for directory in ('install', 'fixtures'):
        (output / directory).mkdir()
    recipe = check.recipe(output, tool_root, lock, features, config, cross)
    env = build.complete_environment(lock, cross)
    value = dict(scope='fex_component', kind='fresh_final_fex', passed=False,
                 source_base_sha256=FEX_BASE, source_manifest_sha256=sha256(output / 'materialized-source.json'),
                 series_sha256=sha256(REPO / 'runtime/fex/patches/integration/fex-series.json'),
                 wire_sha256=H(wire), commands=[], source_only_reuse=True, previous_objects_reused=False,
                 producer_sha256=sha256(Path(__file__)), guest_execution=False)
    try:
        for name, argv in recipe.items():
            run(output, value, name, argv, output, env, 3600 if name.endswith('.build') else 600)
        for name in ('libarm64ecfex.so', 'libwow64fex.so'):
            shutil.copy2(output / 'native' / name, output / 'install' / name)
        # Validate actual compile/link/dependency closure using existing readers.
        artifacts, proofs = check.inspect_modules(output, cross, features, config,
                                                  Path(old['bindings']['baseline']['root']))
        save(output / 'module-proofs.json', proofs)
        value.update(artifacts=artifacts, module_proofs_sha256=sha256(output / 'module-proofs.json'))
        deployment = output / 'deployment.dll'
        shutil.copy2(output / 'pe/arm64ec/Bin/libarm64ecfex.dll', deployment)
        run(output, value, 'deployment.strip', ['/usr/bin/arch', '-arm64',
            str(Path(cross['cross_tools']) / 'bin/llvm-strip'), '--strip-debug', str(deployment)],
            output, env)
        value['outputs'] = [dict(path='deployment.dll', sha256=sha256(deployment),
                                 size_bytes=deployment.stat().st_size)]
        need(check.source_inventory(output / 'source') == manifest['files'], 'reconstruct_fex_mutated_source')
        need(derive(base, manifest) == changed, 'reconstruct_fex_series_changed')
        value['passed'] = True
    except BaseException as error:
        value['error'] = getattr(error, 'code', str(error))
        raise
    finally:
        save(output / 'build.json', value)
        shutil.copyfile(__file__, output / 'producer.py')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'wine', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    root = args.output.absolute()
    need(root.parent == REPO / '.build/task5' and not root.exists(), 'reconstruct_fresh_output')
    need(shutil.disk_usage(REPO).free >= 8 * 1024**3, 'reconstruct_disk_admission')
    with open('/private/tmp/pear-native-compilation.lock', 'a+') as guard:
        fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        root.mkdir(mode=0o700)
        try:
            result = construct(args.base.resolve(strict=True), args.wine.resolve(strict=True), root)
        except BaseException as error:
            save(root / 'failure.json', dict(passed=False, error=getattr(error, 'code', str(error))))
            raise
        print(json.dumps({'passed': result['passed'], 'guest_execution': False}))


if __name__ == '__main__':
    main()
