#!/usr/bin/env python3
"""Finite macOS host control for a source-pinned FEX resource candidate.

This extracts the exact resource class, substitutes allocation/list providers,
and executes an ordinary ARM64 host fixture. It does not run Wine, FEX engine
initialization, translated code or the actual GuestToHostMap implementation.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[2]
PINS = {
    'FEXCore/include/FEXCore/fextl/memory_resource.h': '075a098eb77a428797a9b6a123fc6273c32bead8cc00273d925d99b6abeacaa6',
    'FEXCore/Source/Interface/Core/LookupCache.h': '5d65e77ad420f99bda70438c7dec7666b62bdd1240bf9069bd200685d1974e95',
    'FEXCore/Source/Interface/Core/LookupCache.cpp': '24127237421f5bd36271c2e690feaeb457c99ab08be21d87d3721e744ec52a63',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, reason):
    if not value:
        raise ValueError(reason)


def run(source, output):
    require(platform.system() == 'Darwin' and platform.machine() == 'arm64', 'native ARM64 macOS required')
    require(not output.exists(), 'fresh output required')
    original = {}
    for name, pin in PINS.items():
        require(digest(source / name) == pin, 'source mismatch: ' + name)
        original[name] = (source / name).read_bytes()
    require(shutil.disk_usage(output.parent).free >= 1024 ** 3, 'one GiB reserve required')
    output.mkdir(mode=0o700)
    record = {'scope': 'isolated_host_resource', 'passed': False, 'commands': [],
              'source_sha256': PINS, 'wine_provider_executed': False,
              'FEX_initialization': False, 'stage3_complete': False}

    def persist():
        (output / 'control.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')

    def command(argv, cwd, label):
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=60,
                              env={'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C',
                                   'TMPDIR': str(output), 'GIT_CEILING_DIRECTORIES': str(output)})
        (cwd / (label + '.stdout')).write_bytes(proc.stdout)
        (cwd / (label + '.stderr')).write_bytes(proc.stderr)
        record['commands'].append({'argv': argv, 'exit_code': proc.returncode,
                                   'stdout_sha256': digest(cwd / (label + '.stdout')),
                                   'stderr_sha256': digest(cwd / (label + '.stderr'))})
        persist()
        require(proc.returncode == 0, label + ' failed; inspect retained stderr')
        return proc.stdout

    try:
        compiler = command(['/usr/bin/xcrun', '--find', 'clang++'], output, 'compiler').decode().strip()
        sdk = command(['/usr/bin/xcrun', '--show-sdk-path'], output, 'sdk').decode().strip()
        record['compiler_sha256'] = digest(Path(compiler))
        fixture = output / 'pmr_lifetime.cpp'
        shutil.copyfile(REPO / 'tests/fex/pmr_lifetime.cpp', fixture)
        record['fixture_sha256'] = digest(fixture)
        patch = output / 'candidate.patch'
        shutil.copyfile(REPO / 'runtime/fex/patches/memory/0003r-fex-pmr-lifetime-candidate.patch', patch)
        record['candidate_patch_sha256'] = digest(patch)
        tree = output / 'patched'
        tree.mkdir()
        for name, raw in original.items():
            path = tree / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        command(['/usr/bin/git', 'apply', '--check', str(patch)], tree, 'check')
        command(['/usr/bin/git', 'apply', str(patch)], tree, 'apply')
        header = 'FEXCore/include/FEXCore/fextl/memory_resource.h'
        record['results'] = []
        for variant, raw in [('baseline', original[header]), ('candidate', (tree / header).read_bytes())]:
            directory = output / variant
            directory.mkdir()
            text = raw.decode()
            start = text.index('  class named_monotonic_page_buffer_resource final')
            end = text.index('\n  /**', start)
            fragment = 'namespace fextl { namespace pmr {\n' + text[start:end] + '\n} }\n'
            (directory / 'resource_under_test.inc').write_text(fragment)
            executable = directory / 'control'
            argv = [compiler, '-arch', 'arm64', '-isysroot', sdk, '-std=c++20', '-O1',
                    '-g', '-fno-exceptions', '-Wall', '-Wextra', '-Werror',
                    '-I' + str(directory), str(fixture), '-o', str(executable)]
            if variant == 'candidate':
                argv.insert(1, '-DPEAR_PMR_CANDIDATE=1')
            command(argv, directory, 'compile')
            architecture = command(['/usr/bin/file', str(executable)], directory, 'architecture').decode()
            require('Mach-O 64-bit executable arm64' in architecture, 'wrong host architecture')
            result = json.loads(command([str(executable), variant], directory, 'run'))
            require(result['baseline'] == (variant == 'baseline') and result['cycles'] == 32,
                    'unexpected result scope')
            require(result['scope_retained_buffers'] == (1 if variant == 'baseline' else 0),
                    'unexpected scope lifetime')
            require(result['cycle_retained_buffers'] > 32 if variant == 'baseline'
                    else result['cycle_retained_buffers'] == 0, 'unexpected cycle lifetime')
            record['results'].append(result)
        require(all((source / name).read_bytes() == raw for name, raw in original.items()), 'original changed')
        record['passed'] = True
    except Exception as exc:
        record['error'] = {'type': type(exc).__name__, 'reason': str(exc)}
        raise
    finally:
        persist()
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = run(args.source.resolve(strict=True), args.output.absolute())
    print(json.dumps({'passed': result['passed'], 'results': result['results'], 'scope': result['scope']}))


if __name__ == '__main__':
    main()
