#!/usr/bin/env python3
"""Source-pinned release success/refusal control; no Wine or fatal trap execution."""
from pathlib import Path
import argparse
import fcntl
import hashlib
import json
import os
import platform
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[2]
SOURCE_FILES = {
    'FEXCore/include/FEXCore/Utils/AllocatorHooks.h': '8bede143837bf3902f23f928b56217f9f22b6c95eb30c8932d47929ec152756a',
    'FEXCore/include/FEXCore/fextl/memory_resource.h': 'e441ca2dacaaeb28d03b81ea8e51a16067670499ff28390395279bb925910eeb',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def run(source, output):
    need(platform.system() == 'Darwin' and platform.machine() == 'arm64', 'native ARM64 macOS required')
    need(not output.exists(), 'fresh output required')
    need(shutil.disk_usage(output.parent).free >= 8 * 1024**3, '8 GiB reserve required')
    for name, digest in SOURCE_FILES.items():
        need(sha(source / name) == digest, 'source mismatch: ' + name)
    with Path('/private/tmp/pear-native-compilation.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        output.mkdir(mode=0o700)
        record = {'scope': 'substituted_provider_and_fatal_sink', 'passed': False, 'commands': [],
                  'source_sha256': SOURCE_FILES, 'FEX_initialization': False, 'wine_execution': False,
                  'actual_fatal_path_executed': False, 'stage3_complete': False, 'results': []}

        def persist():
            (output / 'control.json').write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')

        def command(argv, name):
            row = {'argv': argv, 'exit_code': None}; record['commands'].append(row); persist()
            proc = subprocess.run(argv, cwd=output, capture_output=True, timeout=60,
                                  env={'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C', 'TMPDIR': str(output)})
            for suffix, data in [('stdout', proc.stdout), ('stderr', proc.stderr)]:
                path = output / (name + '.' + suffix); path.write_bytes(data); row[suffix + '_sha256'] = sha(path)
            row['exit_code'] = proc.returncode; persist()
            need(proc.returncode == 0, name + ' failed; inspect retained output')
            return proc.stdout

        try:
            compiler = command(['/usr/bin/xcrun', '--find', 'clang++'], 'compiler').decode().strip()
            sdk = command(['/usr/bin/xcrun', '--show-sdk-path'], 'sdk').decode().strip()
            fixture = output / 'virtual_free_error.cpp'; shutil.copyfile(REPO / 'tests/fex/virtual_free_error.cpp', fixture)
            refs = {str(fixture): sha(fixture), compiler: sha(Path(compiler))}
            fmt_root = source / 'External/fmt/include'
            for path in fmt_root.rglob('*'):
                if path.is_file(): refs[str(path)] = sha(path)
            record['references'] = refs
            raw = (source / 'FEXCore/include/FEXCore/Utils/AllocatorHooks.h').read_text()
            start = raw.index('inline void VirtualFree(void* Ptr, size_t Size) {')
            wrapper = raw[start:raw.index('\ninline void VirtualDontNeed', start)]
            raw = (source / 'FEXCore/include/FEXCore/fextl/memory_resource.h').read_text()
            start = raw.index('  class named_monotonic_page_buffer_resource final')
            resource = 'namespace fextl { namespace pmr {\n' + raw[start:raw.index('\n  /**', start)] + '\n} }\n'
            (output / 'wrapper_under_test.inc').write_text(wrapper)
            (output / 'resource_under_test.inc').write_text(resource)
            for variant in ('baseline', 'checked'):
                binary = output / variant
                argv = [compiler, '-arch', 'arm64', '-isysroot', sdk, '-std=c++20', '-O1', '-fno-exceptions',
                        '-DFMT_HEADER_ONLY=1', '-DASSERTIONS_ENABLED=0', '-I' + str(fmt_root),
                        '-I' + str(output), str(fixture), '-o', str(binary)]
                if variant == 'checked': argv.insert(1, '-DPEAR_FEX_MEMORY_OWNER=1')
                command(argv, variant + '-compile')
                need('Mach-O 64-bit executable arm64' in command(['/usr/bin/file', str(binary)], variant + '-arch').decode(), 'wrong architecture')
                for code in ((87,) if variant == 'baseline' else (0, 87, 4294967295)):
                    result = json.loads(command([str(binary), variant, str(code)], variant + '-' + str(code)))
                    fail = variant == 'checked' and code != 0
                    expected = {'failure_intercepted': fail, 'error': code, 'provider_calls': 2 if fail else 3,
                                'retained_buffers': 2 if fail else (1 if code else 0), 'error_reads': 1 if fail else 0}
                    need(result == expected, 'unexpected release behavior')
                    record['results'].append({'variant': variant, **result}); persist()
            need(all(sha(Path(p)) == h for p, h in refs.items()), 'reference changed')
            need(all(sha(source / p) == h for p, h in SOURCE_FILES.items()), 'source changed')
            record['passed'] = True
        except Exception as exc:
            record['error'] = {'type': type(exc).__name__, 'reason': str(exc)}
            raise
        finally:
            persist()
        return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = run(args.source.resolve(strict=True), args.output.absolute())
    print(json.dumps({'passed': result['passed'], 'results': result['results']}))
