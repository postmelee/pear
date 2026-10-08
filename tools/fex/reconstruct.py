#!/usr/bin/env python3
"""Fresh final Wine/FEX construction from verified recorded source and tools.

Reuse existing exact patch application, source copying, recipes and bounded build
supervision. This command builds components only; signing and execution remain
separate operations. No previous object directory is copied or modified.
"""
from pathlib import Path
import argparse
import fcntl
import hashlib
import json
import shutil
import sys
import tempfile

if not __package__:
    here = Path(__file__).resolve().parent
    sys.path[:] = [p for p in sys.path if Path(p or '.').resolve() != here]
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.fex.common import REPO, need, sha256, relative
from tools.fex import integration, memory_wine_build as monitor

H = lambda raw: hashlib.sha256(raw).hexdigest()
WINE_BASE = '16e0c48694d51a1c378de823e54797a0169f44bff1a52cbd21182496b02d7110'
FEX_BASE = '9d4e431ee002099fde7c681327747cbfe653b33eae222dc0152e489dd9d1d304'


def read_bound(path, digest):
    raw = Path(path).read_bytes()
    need(H(raw) == digest, 'reconstruct_input_changed')
    return json.loads(raw)


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def run(root, record, name, argv, cwd, env, timeout=600):
    print(name, flush=True)
    monitor.execute(root, name, argv, str(cwd), env, timeout,
                    record['commands'], 8 * 1024**3, 4 * 1024**3)


def wine(base, baseline, output):
    old = read_bound(base / 'build.json', WINE_BASE)
    # Exact source receipt belongs to the preserved memory-owner build.
    manifest = read_bound(base / 'source-files.json', old['source_manifest_sha256'])
    changed = integration.derive(base)
    for row in manifest['files']:
        if row['path'] in changed:
            raw = changed[row['path']]
            row.update(sha256=H(raw), size_bytes=len(raw))
    need(set(changed) <= {r['path'] for r in manifest['files']}, 'reconstruct_source_closure')
    parent = read_bound(baseline / 'build.json',
                        'd71d69ab5b5612d33b5fd73997d1e38f09b2a72a9625cd9c954817bbf05c77ad')
    tools = Path(parent['tools_root'])
    lock = json.loads((REPO / 'runtime/wine/toolchain.json').read_text())
    tool_record = monitor.verify_tools(lock, parent, baseline)
    sdk = tool_record['sdk']
    need(sdk == parent['sdk'], 'reconstruct_sdk_changed')
    monitor.copy_inventory(base / 'source', output / 'source', manifest, changed)
    save(output / 'source-files.json', manifest)
    for directory in ('objects', 'tmp'):
        (output / directory).mkdir()
    alias = Path(tempfile.mkdtemp(prefix='pear-reconstruct-', dir='/private/tmp'))
    (alias / 'workspace').symlink_to(output, target_is_directory=True)
    (alias / 'tools').symlink_to(tools, target_is_directory=True)
    work, selected_tools = alias / 'workspace', alias / 'tools'
    config = json.loads((REPO / 'runtime/wine/build-config.json').read_text())
    variant = next(v for v in config['variants'] if v['id'] == 'arm64ec-build')
    env = dict(json.loads((base / 'logs/ntdll/command.json').read_text())['environment'])
    env.pop('PWD', None)
    env.update(PATH=str(selected_tools / 'llvm-mingw/bin') + ':' +
               str(selected_tools / 'bison/bin') + ':/usr/bin:/bin:/usr/sbin:/sbin',
               BISON=str(selected_tools / 'bison/bin/bison'), TMPDIR=str(work / 'tmp'),
               aarch64_CFLAGS='', arm64ec_CFLAGS='')
    for key in ('CFLAGS', 'CXXFLAGS', 'CPPFLAGS'):
        env[key] = env[key].replace('-DPEAR_FEX_MEMORY_FINITE_FIXTURE=1', '').strip()
    value = dict(scope='fex_component', kind='fresh_final_wine', passed=False,
                 source_base_sha256=WINE_BASE, series_sha256=sha256(integration.PATCHES / 'series.json'),
                 source_manifest_sha256=sha256(output / 'source-files.json'),
                 tool_receipt_sha256=sha256(tools / 'prepared.json'), sdk=sdk,
                 producer_sha256=sha256(Path(__file__)), commands=[],
                 source_only_reuse=True, previous_objects_reused=False,
                 wine_execution=False, guest_execution=False, alias=str(alias))
    try:
        make = '/Applications/Xcode.app/Contents/Developer/usr/bin/make'
        run(output, value, 'configure', ['/usr/bin/arch', '-arm64', '/bin/sh',
            '../source/configure', '--prefix=' + str(work / 'install'),
            '--with-mingw=' + str(selected_tools / 'llvm-mingw/bin/clang'),
            *variant['configure_args']], work / 'objects', env)
        run(output, value, 'make', ['/usr/bin/arch', '-arm64', make, '-j2'],
            work / 'objects', env, 7200)
        run(output, value, 'install', ['/usr/bin/arch', '-arm64', make, 'install'],
            work / 'objects', env, 900)
        with monitor.wine_readers() as (_, wb):
            series = json.loads((REPO / 'runtime/wine/patches/series.json').read_text())
            suite, policy = wb.fixture_suite(series), wb.code_publication_policy(series)
            for stage in ('pear-stage2', 'pear-stage3', 'pear-stage4', 'pear-stage5'):
                (output / 'install/libexec' / stage).mkdir(parents=True, exist_ok=True)
            for name, argv in wb.fixture_commands(work, selected_tools, lock, suite, policy).items():
                run(output, value, name, ['/usr/bin/arch', '-arm64', *map(str, argv)],
                    work / 'objects', env)
            artifacts = wb.inventory(output / 'install', binary=True)
            wb.required_outputs(artifacts, variant['id'], suite, policy)
            from tools.fex.reconstruct_wine_result import capacity
            value['arena_capacity'] = capacity(output / 'source', output / 'install', artifacts)
            need(wb.inventory(output / 'source') == manifest, 'reconstruct_mutated_source')
        save(output / 'installed-files.json', artifacts)
        value['artifacts_manifest'] = dict(path='installed-files.json', sha256=sha256(output / 'installed-files.json'))
        value['outputs'] = [dict(path='install/' + r['path'], sha256=r['sha256'], size_bytes=r['size_bytes'])
                            for r in artifacts['files'] if r['path'] in
                            ('lib/wine/aarch64-unix/ntdll.so', 'lib/wine/aarch64-windows/ntdll.dll')]
        need(len(value['outputs']) == 2, 'reconstruct_ntdll_pair')
        need(integration.derive(base) == changed, 'reconstruct_series_changed')
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
    parser.add_argument('--component', choices=['wine'], required=True)
    for name in ('base', 'baseline', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    root = args.output.absolute()
    need(root.parent == REPO / '.build/task5' and not root.exists(), 'reconstruct_fresh_output')
    need(shutil.disk_usage(REPO).free >= 16 * 1024**3, 'reconstruct_disk_admission')
    with open('/private/tmp/pear-native-compilation.lock', 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        root.mkdir(mode=0o700)
        try:
            result = wine(args.base.resolve(strict=True), args.baseline.resolve(strict=True), root)
        except BaseException as error:
            save(root / 'failure.json', dict(passed=False, error=getattr(error, 'code', str(error))))
            raise
        print(json.dumps({'passed': result['passed'], 'guest_execution': False}))


if __name__ == '__main__':
    main()
