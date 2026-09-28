"""Build the bounded native experiments; never build a game runtime."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tomllib

REPO = Path(__file__).resolve().parents[2]
EXPERIMENT = REPO / 'experiments/manager'
LIBC_SHA256 = '68ab91017fe16c622486840e4c83c9a37afeff978bd239b5293d61ece587de66'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def controlled_environment():
    env = {key: value for key, value in os.environ.items() if not key.startswith(('RUST', 'CARGO_', 'DYLD_', 'LD_', 'LIBC_', 'CC_', 'CFLAGS', 'LDFLAGS', 'SDKROOT', 'DEVELOPER_DIR', 'SWIFT_', 'CLANG_', 'MACOSX_DEPLOYMENT_TARGET'))}
    env.pop('WIND_RELEASE_ID', None)
    env['PATH'] = str(Path.home() / '.cargo/bin') + ':/usr/bin:/bin:/usr/sbin:/sbin'
    env['MACOSX_DEPLOYMENT_TARGET'] = '26.0'
    return env


def verify_lock():
    config_roots = {Path.home() / '.cargo', *(parent / '.cargo' for parent in [REPO, *REPO.parents])}
    for root in config_roots:
        if any((root / name).exists() or (root / name).is_symlink() for name in ['config', 'config.toml']):
            raise ValueError('ambient Cargo configuration is outside this controlled experiment')
    lock = tomllib.loads((EXPERIMENT / 'rust/Cargo.lock').read_text())
    packages = lock['package']
    if len(packages) != 2:
        raise ValueError('unexpected Rust dependency count')
    libc = next(p for p in packages if p['name'] == 'libc')
    if libc['version'] != '0.2.186' or libc['checksum'] != LIBC_SHA256 or libc.get('dependencies'):
        raise ValueError('unreviewed Rust dependency')
    manifest = tomllib.loads((EXPERIMENT / 'rust/Cargo.toml').read_text())
    if manifest['dependencies'] != {'libc': '=0.2.186'}:
        raise ValueError('unexpected direct Rust dependencies')
    cached = Path.home() / '.cargo/registry/cache/index.crates.io-1949cf8c6b5b557f/libc-0.2.186.crate'
    if not cached.is_file() or digest(cached) != LIBC_SHA256:
        raise ValueError('reviewed locked crate missing; prefetch exact Cargo.lock before building')
    source_root = cached.parent.parent.parent / 'src' / cached.parent.name
    with tarfile.open(cached) as archive:
        for member in archive:
            if not member.isfile():
                if member.isdir(): continue
                raise ValueError('unexpected dependency archive member')
            parts = Path(member.name).parts
            if not parts or parts[0] != 'libc-0.2.186' or '..' in parts:
                raise ValueError('unexpected dependency archive path')
            source = source_root.joinpath(*parts)
            if source.is_symlink() or not source.is_file() or source.read_bytes() != archive.extractfile(member).read():
                raise ValueError('extracted dependency differs from reviewed archive')



def build(output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / 'bin').mkdir(exist_ok=True)
    env = controlled_environment()
    commands = []

    def run(args, extra=None):
        result = subprocess.run([str(a) for a in args], cwd=REPO, env={**env, **(extra or {})}, capture_output=True, text=True, timeout=180)
        commands.append({'argv': [str(a) for a in args], 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
        (output / 'build-log.json').write_text(json.dumps(commands, indent=2) + '\n')
        if result.returncode:
            raise RuntimeError('build command failed; inspect local build-log.json')
        return result.stdout.strip()

    verify_lock()
    versions = {name: run(args) for name, args in {
        'clang': ['xcrun', 'clang', '--version'], 'sdk': ['xcrun', '--show-sdk-version'],
        'rustc': ['rustc', '--version', '--verbose'], 'cargo': ['cargo', '--version'],
        'swift': ['xcrun', 'swift', '--version'], 'xcode': ['xcodebuild', '-version'],
        'macos': ['sw_vers'], 'machine': ['uname', '-m'],
    }.items()}
    if versions['machine'] != 'arm64':
        raise ValueError('native ARM64 build host required')
    flags = ['-arch', 'arm64', '-mmacosx-version-min=26.0', '-O2', '-std=c11', '-Wall', '-Wextra', '-Werror']
    bridge = output / 'native_bridge.o'
    child = output / 'bin/fixture-child'
    run(['xcrun', 'clang', *flags, '-c', EXPERIMENT / 'fixtures/native_bridge.c', '-o', bridge])
    run(['xcrun', 'clang', *flags, EXPERIMENT / 'fixtures/child.c', bridge, '-lproc', '-o', child])
    rust_target = output / 'rust'
    rust_env = {'CARGO_TARGET_DIR': str(rust_target), 'RUSTC': str(Path.home() / '.cargo/bin/rustc'),
                'CARGO_ENCODED_RUSTFLAGS': '\x1f'.join(['-C', 'link-arg=' + str(bridge), '-C', 'link-arg=-lproc'])}
    run(['cargo', 'build', '--manifest-path', EXPERIMENT / 'rust/Cargo.toml', '--locked', '--offline', '--release', '--target', 'aarch64-apple-darwin'], rust_env)
    shutil.copy2(rust_target / 'aarch64-apple-darwin/release/pear-manager', output / 'bin/rust-manager')
    swift_root = output / 'swift'
    run(['xcrun', 'swift', 'build', '--package-path', EXPERIMENT / 'swift', '-c', 'release', '--scratch-path', swift_root, '--triple', 'arm64-apple-macosx26.0', '-Xlinker', bridge, '-Xlinker', '-lproc'])
    swift_bin = Path(run(['xcrun', 'swift', 'build', '--package-path', EXPERIMENT / 'swift', '-c', 'release', '--scratch-path', swift_root, '--triple', 'arm64-apple-macosx26.0', '--show-bin-path']))
    shutil.copy2(swift_bin / 'pear-manager-swift', output / 'bin/swift-manager')
    binaries = {}
    for name in ['fixture-child', 'rust-manager', 'swift-manager']:
        path = output / 'bin' / name
        slices = run(['lipo', '-archs', path])
        if slices != 'arm64':
            raise ValueError('unexpected Mach-O slice')
        binaries[name] = {'sha256': digest(path), 'size_bytes': path.stat().st_size, 'slices': slices,
                          'file': run(['file', path]), 'dependencies': run(['otool', '-L', path])}
    sources = {str(p.relative_to(REPO)): digest(p) for p in sorted(EXPERIMENT.rglob('*')) if p.is_file() and not any(part.startswith('.') or part == '__pycache__' for part in p.relative_to(EXPERIMENT).parts)}
    metadata = {'version': 1, 'fixture_only': True, 'runtime_eligible': False, 'toolchains': versions, 'binaries': binaries, 'sources': sources, 'build_log': 'build-log.json', 'locked_offline_rust': True, 'swift_external_dependencies': []}
    (output / 'build.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--locked', action='store_true', required=True)
    args = parser.parse_args()
    try:
        result = build(args.output)
        print(json.dumps({'build': 'passed', 'binaries': list(result['binaries']), 'fixture_only': True}))
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({'build': 'failed', 'reason': str(error)}))
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
