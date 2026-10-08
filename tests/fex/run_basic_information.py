#!/usr/bin/env python3
"""Check the selected basic-information helper with a substituted NT provider."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import platform
import subprocess

SOURCE_SHA256 = '731269adedb45b84713c68e903d12428201dcd3fdb6b07e2bf13861c123f3a6e'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def run(source, output):
    need(platform.system() == 'Darwin' and platform.machine() == 'arm64', 'native ARM64 macOS required')
    source = source / 'Source/Windows/Common/WinAPI/Alloc.cpp'
    fixture = Path(__file__).with_name('basic_information.cpp')
    need(sha(source) == SOURCE_SHA256, 'selected source mismatch')
    need(not output.exists(), 'fresh output required')
    with Path('/private/tmp/pear-native-compilation.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        output.mkdir(mode=0o700)
        record = {'scope': 'actual_helper_body_substituted_provider', 'passed': False,
                  'source_sha256': SOURCE_SHA256, 'fixture_sha256': sha(fixture),
                  'commands': [], 'FEX_initialization': False, 'wine_execution': False,
                  'stage3_complete': False}

        def persist():
            (output / 'control.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')

        def command(argv, name):
            row = {'argv': argv, 'exit_code': None}
            record['commands'].append(row)
            persist()
            child = subprocess.run(argv, cwd=output, capture_output=True, timeout=60,
                                   env={'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C', 'TMPDIR': str(output)})
            for channel, data in [('stdout', child.stdout), ('stderr', child.stderr)]:
                path = output / (name + '.' + channel)
                path.write_bytes(data)
                row[channel + '_sha256'] = sha(path)
            row['exit_code'] = child.returncode
            persist()
            need(child.returncode == 0, name + ' failed; inspect retained output')
            return child.stdout

        try:
            raw = source.read_text()
            start = raw.index('namespace FEX::Windows::PearCRT {')
            marker = '} // namespace FEX::Windows::PearCRT'
            end = raw.index(marker, start) + len(marker)
            (output / 'basic_information_under_test.inc').write_text(raw[start:end] + '\n')
            compiler = Path(command(['/usr/bin/xcrun', '--find', 'clang++'], 'compiler').decode().strip())
            compiler_sha = sha(compiler)
            record['compiler_sha256'] = compiler_sha
            sdk = command(['/usr/bin/xcrun', '--show-sdk-path'], 'sdk').decode().strip()
            binary = output / 'fixture'
            command([str(compiler), '-isysroot', sdk, '-arch', 'arm64', '-std=c++20', '-O2',
                     '-Wall', '-Wextra', '-Werror', '-I' + str(output), str(fixture), '-o', str(binary)], 'compile')
            record['result'] = json.loads(command([str(binary)], 'run'))
            need(record['result'] == {'cases': 9, 'passed': True, 'provider': 'substituted'}, 'unexpected behavior')
            need(sha(source) == SOURCE_SHA256 and sha(fixture) == record['fixture_sha256']
                 and sha(compiler) == compiler_sha, 'input changed')
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
    print(json.dumps(run(args.source.resolve(), args.output.resolve())['result']))


if __name__ == '__main__':
    main()
