#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build a fresh Rosetta candidate from pinned inputs; never reuse stale receipts."""
import argparse
import contextlib
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import time

HERE = Path(__file__).resolve().parent
GIB = 1024 ** 3
ORDER = ('gmp', 'nettle', 'libtasn1', 'libunistring', 'libidn2',
         'gnutls', 'libpng', 'freetype')


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def verify_inputs(mapping, lock, base=HERE):
    if set(mapping) != set(lock['inputs']):
        raise ValueError('Input map must contain exactly the locked component names')
    result = {}
    for name, pin in lock['inputs'].items():
        path = Path(mapping[name]).resolve(strict=True)
        if not path.is_file() or sha256(path) != pin['sha256']:
            raise ValueError('Input checksum mismatch: ' + name)
        result[name] = path
    patch = base / lock['patch']['file']
    if sha256(patch) != lock['patch']['sha256']:
        raise ValueError('Patch checksum mismatch')
    notices = base / 'runtime-notices'
    actual = {str(p.relative_to(notices)) for p in notices.rglob('*') if p.is_file()}
    if actual != set(lock['notice_files']):
        raise ValueError('Notice inventory mismatch')
    for name, digest in lock['notice_files'].items():
        if sha256(notices / name) != digest:
            raise ValueError('Notice checksum mismatch: ' + name)
    return result


def fresh_output(root):
    root = Path(os.path.abspath(root))
    if root.exists() or root.is_symlink():
        raise ValueError('Output already exists; preserve its evidence and choose a fresh root')
    # Autoconf/libtool builds require a physical path without whitespace.
    if any(c.isspace() for c in str(root.resolve())):
        raise ValueError('Build root must resolve to a path without whitespace')
    if not root.parent.is_dir():
        raise ValueError('Output parent must already exist')
    return root


def require_release(path):
    if path is not None:
        data = json.loads(Path(path).read_text())
        if data.get('released') is not True:
            raise ValueError('Preceding heavy task has not released the host')


@contextlib.contextmanager
def heavy_slot(path, release, required_free, filesystem):
    require_release(release)
    with Path(path).open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require_release(release)
        free = shutil.disk_usage(filesystem).free
        if free < required_free:
            raise ValueError(f'Insufficient free space: {free} < {required_free} bytes')
        yield free


def extract(archive, destination, prefix=None):
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as source:
        members = source.getmembers()
        if prefix:
            members = [m for m in members if m.name == prefix or m.name.startswith(prefix + '/')]
            if not members:
                raise ValueError('Missing archive subtree: ' + prefix)
        source.extractall(destination, members=members, filter='data')


def command(cmd, cwd, env, log, steps):
    print(log.stem, flush=True)
    start = time.monotonic()
    with log.open('w') as output:
        status = subprocess.run([str(x) for x in cmd], cwd=cwd, env=env,
                                stdout=output, stderr=subprocess.STDOUT).returncode
    steps.append({'command': [str(x) for x in cmd], 'cwd': str(cwd),
                  'exit': status, 'seconds': round(time.monotonic() - start, 2)})
    write_json(log.parent / 'commands.json', steps)
    if status:
        raise RuntimeError(f'{log.stem} failed; inspect {log}')


def toolchain(bison, env):
    checks = {'clang': ['clang', '--version'], 'clang_target': ['clang', '-print-target-triple'],
              'sdk_path': ['xcrun', '--show-sdk-path'], 'sdk_version': ['xcrun', '--show-sdk-version'],
              'xcode': ['xcodebuild', '-version'], 'make': ['make', '--version'],
              'bison': [str(bison), '--version'], 'pkg_config': ['pkg-config', '--version'],
              'mingw_x86_64': ['x86_64-w64-mingw32-gcc', '--version'],
              'mingw_i686': ['i686-w64-mingw32-gcc', '--version']}
    result = {}
    for key, cmd in checks.items():
        q = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        result[key] = q.stdout.strip()
    for name in ('clang', 'make', 'pkg-config', 'x86_64-w64-mingw32-gcc', 'i686-w64-mingw32-gcc'):
        path = Path(shutil.which(name, path=env['PATH'])).resolve()
        result[name + '_file'] = {'path': str(path), 'sha256': sha256(path)}
    if '3.8.2' not in result['bison'].splitlines()[0]:
        raise ValueError('This recipe requires Bison 3.8.2')
    for name in ('clang', 'make', 'ld', 'codesign'):
        path = Path(subprocess.check_output(['xcrun', '--find', name], env=env, text=True).strip()).resolve()
        result['selected_' + name] = {'path': str(path), 'sha256': sha256(path)}
    result['bison_file'] = {'path': str(bison), 'sha256': sha256(bison)}
    return result


def dependency_options(name, deps):
    return {
        'gmp': ['--disable-cxx'],
        'nettle': ['--disable-documentation', '--disable-openssl',
                   '--with-lib-path=' + str(deps / 'lib'), '--with-include-path=' + str(deps / 'include')],
        'libtasn1': ['--disable-doc', '--disable-tools'], 'libunistring': [],
        'libidn2': ['--disable-doc', '--disable-nls'],
        'gnutls': ['--disable-doc', '--disable-tools', '--disable-tests', '--disable-cxx',
                   '--disable-nls', '--without-p11-kit', '--disable-guile', '--disable-dane',
                   '--without-zstd', '--without-brotli', '--without-zlib',
                   '--with-included-unistring=no', '--with-included-libtasn1=no'],
        'libpng': [],
        'freetype': ['--with-harfbuzz=no', '--with-brotli=no', '--with-bzip2=no',
                     '--with-png=yes', '--with-zlib=yes'],
    }[name]


def inventory(root):
    files = []
    for path in sorted(root.rglob('*')):
        rel = str(path.relative_to(root))
        if path.is_symlink():
            if not path.resolve(strict=True).is_relative_to(root.resolve()):
                raise ValueError('External runtime symlink: ' + rel)
            files.append({'path': rel, 'target': os.readlink(path)})
        elif path.is_file():
            files.append({'path': rel, 'bytes': path.stat().st_size, 'sha256': sha256(path)})
    return files


def install_notices(destination, wine_source):
    """Preserve nested attribution and reject a source/notice mismatch."""
    shutil.copytree(HERE / 'runtime-notices', destination)
    wine_notices = destination / 'wine'
    wine_notices.mkdir(exist_ok=True)
    for name in ('LICENSE', 'COPYING.LIB', 'AUTHORS', 'README.md'):
        source = wine_source / name
        target = wine_notices / name
        if target.exists() and sha256(target) != sha256(source):
            raise ValueError('Wine source/notice mismatch: ' + name)
        shutil.copy2(source, target)


def assemble(root, inputs, lock, env, steps):
    runtime = root / 'Runtime'
    for path in (root / 'deps/lib').glob('*.dylib'):
        dest = runtime / 'lib' / path.name
        if path.is_symlink():
            dest.symlink_to(path.readlink())
        else:
            shutil.copy2(path, dest)
    extract(inputs['moltenvk'], root / 'binary-inputs/moltenvk')
    moltenvk = root / 'binary-inputs/moltenvk/MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib'
    shutil.copy2(moltenvk, runtime / 'lib/libMoltenVK.dylib')
    extract(inputs['dxmt'], root / 'binary-inputs/dxmt')
    dxmt = root / 'binary-inputs/dxmt/v0.80'
    for arch in ('x86_64-windows', 'i386-windows'):
        shutil.copy2(dxmt / arch / 'winemetal.dll', runtime / 'lib/wine' / arch / 'winemetal.dll')
    shutil.copy2(dxmt / 'x86_64-unix/winemetal.so', runtime / 'lib/wine/x86_64-unix/winemetal.so')
    share = runtime / 'share/pear'
    shutil.copytree(dxmt, share / 'dxmt')
    install_notices(share / 'licenses', root / 'sources/sources/wine')
    write_json(share / 'runtime-inputs.json', lock)
    for path in (runtime / 'lib').glob('*.dylib'):
        if path.is_symlink():
            continue
        loads = subprocess.check_output(['otool', '-L', str(path)], text=True)
        cmd = ['install_name_tool', '-id', '@loader_path/' + path.name]
        for line in loads.splitlines():
            if not line.startswith('\t'):
                continue
            link = line.strip().split(' (')[0]
            if link.startswith(str(root / 'deps/lib') + '/'):
                cmd += ['-change', link, '@loader_path/' + Path(link).name]
        command(cmd + [path], root, env, root / 'logs' / (path.name + '-relocate.log'), steps)
        command(['codesign', '--force', '--sign', '-', path], root, env,
                root / 'logs' / (path.name + '-sign.log'), steps)
    audit = []
    for path in runtime.rglob('*'):
        if not path.is_file() or path.is_symlink():
            continue
        with path.open('rb') as stream:
            magic = stream.read(4)
        if magic not in (b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe', b'\xca\xfe\xba\xbe'):
            continue
        loads = subprocess.check_output(['otool', '-L', str(path)], text=True)
        links = [x.strip().split(' (')[0] for x in loads.splitlines() if x.startswith('\t')]
        if any(not x.startswith(('/usr/lib/', '/System/Library/', '@loader_path/',
                                 '@rpath/', '@executable_path/')) for x in links):
            raise ValueError('Nonportable dylib load: ' + str(path))
        commands = subprocess.check_output(['otool', '-l', str(path)], text=True)
        if any(x in commands for x in (str(root / 'deps'), '/opt/homebrew', '/pear47-inprocess/helpers')):
            raise ValueError('Build/helper path in load commands: ' + str(path))
        audit.append({'path': str(path.relative_to(runtime)), 'dependencies': links})
    write_json(root / 'load-audit.json', audit)
    write_json(root / 'runtime-manifest.json', inventory(runtime))


def local_bison(root, bison):
    tools = root / 'toolchain'
    tools.mkdir()
    (tools / 'bison').symlink_to(bison.parent.parent.resolve(), target_is_directory=True)
    return tools / 'bison/bin/bison'


def build(root, inputs, lock, bison, jobs):
    root.mkdir()
    (root / 'logs').mkdir()
    steps = []
    recipe_hash = sha256(Path(__file__))
    shutil.copy2(Path(__file__), root / 'build-recipe.py')
    bison = local_bison(root, bison)
    base_env = {k: os.environ[k] for k in ('HOME', 'USER', 'TMPDIR') if k in os.environ}
    base_env.update(PATH='/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin', LC_ALL='C')
    write_json(root / 'toolchain.json', toolchain(bison, base_env))
    write_json(root / 'inputs.json', lock)
    try:
        for name in ORDER:
            pin = lock['inputs'][name]
            extract(inputs[name], root / 'sources')
            source = root / 'sources' / pin['source_directory']
            deps = root / 'deps'
            obj = root / 'objects' / name
            obj.mkdir(parents=True)
            env = base_env | {'CC': 'clang -arch x86_64', 'CXX': 'clang++ -arch x86_64',
                'CFLAGS': '-O2', 'CXXFLAGS': '-O2', 'MACOSX_DEPLOYMENT_TARGET': '14.0',
                'CPPFLAGS': '-I' + str(deps / 'include'), 'LDFLAGS': '-L' + str(deps / 'lib'),
                'PKG_CONFIG_LIBDIR': str(deps / 'lib/pkgconfig'), 'PKG_CONFIG_PATH': '', 'MAKEINFO': 'true'}
            if name == 'freetype':
                env.update(LIBPNG_CFLAGS='-I' + str(deps / 'include/libpng16'),
                           LIBPNG_LIBS='-L' + str(deps / 'lib') + ' -lpng16 -lz', ZLIB_LIBS='-lz')
            args = [source / 'configure', '--prefix=' + str(deps), '--host=x86_64-apple-darwin',
                    '--build=aarch64-apple-darwin', '--enable-shared', '--disable-static',
                    *dependency_options(name, deps)]
            write_json(root / 'logs' / (name + '-environment.json'), env)
            for label, cmd in [('configure', args), ('build', ['make', '-j' + str(jobs)]),
                               ('install', ['make', 'install'])]:
                command(cmd, obj, env, root / 'logs' / (name + '-' + label + '.log'), steps)
        extract(inputs['wine'], root / 'sources', prefix='sources/wine')
        source = root / 'sources/sources/wine'
        command(['patch', '-p1', '--batch', '--forward', '-i', HERE / lock['patch']['file']],
                source, base_env, root / 'logs/wine-patch.log', steps)
        obj = root / 'objects/wine'
        obj.mkdir()
        (obj / 'libfreetype.dylib').symlink_to(root / 'deps/lib/libfreetype.6.dylib')
        env = base_env | {'CC': 'clang -arch x86_64', 'CXX': 'clang++ -arch x86_64',
            'CFLAGS': '-O2', 'CXXFLAGS': '-O2', 'MACOSX_DEPLOYMENT_TARGET': '14.0',
            'BISON': str(bison), 'BISON_PKGDATADIR': str(bison.parent.parent / 'share/bison'),
            'GNUTLS_CFLAGS': '-I' + str(root / 'deps/include'),
            'GNUTLS_LIBS': '-L' + str(root / 'deps/lib') + ' -lgnutls',
            'FREETYPE_CFLAGS': '-I' + str(root / 'deps/include/freetype2'),
            'FREETYPE_LIBS': '-L' + str(root / 'deps/lib') + ' -lfreetype',
            'LDFLAGS': '-Wl,-headerpad_max_install_names',
            'PKG_CONFIG_LIBDIR': str(root / 'deps/lib/pkgconfig'), 'PKG_CONFIG_PATH': '',
            'ac_cv_lib_soname_gnutls': '@loader_path/../../libgnutls.30.dylib',
            'ac_cv_lib_soname_freetype': '@loader_path/../../libfreetype.6.dylib',
            'ac_cv_lib_soname_vulkan': '@loader_path/../../libMoltenVK.dylib'}
        args = [source / 'configure', '--build=x86_64-apple-darwin', '--enable-win64',
                '--enable-archs=i386,x86_64', '--disable-tests',
                *['--without-' + x for x in ('x', 'wayland', 'opengl', 'gstreamer', 'alsa',
                                            'pulse', 'dbus', 'fontconfig', 'usb', 'sane',
                                            'udev', 'krb5', 'gssapi')],
                '--prefix=' + str(root / 'Runtime')]
        write_json(root / 'logs/wine-environment.json', env)
        for label, cmd in [('configure', args), ('build', ['make', '-j' + str(jobs)]),
                           ('install', ['make', 'install-lib'])]:
            command(cmd, obj, env, root / 'logs' / ('wine-' + label + '.log'), steps)
        shutil.copy2(obj / 'include/config.h', root / 'wine-config.h')
        assemble(root, inputs, lock, base_env, steps)
        write_json(root / 'result.json', {'build': 'passed', 'execution': 'not-tested',
                   'distribution': 'not-qualified', 'recipe_sha256': recipe_hash})
    except Exception as error:
        write_json(root / 'result.json', {'build': 'failed', 'error': str(error)})
        raise


def source_kit(output, inputs, lock):
    """Allowlisted source/input kit; never traverses private runtime state."""
    if output.exists():
        raise ValueError('Source kit already exists')
    license_path = HERE / 'LICENSE' if (HERE / 'LICENSE').exists() else HERE.parent / 'LICENSE'
    source_files = [HERE / 'runtime_build.py', HERE / 'runtime-inputs.json',
                    HERE / lock['patch']['file'], license_path]
    source_files += [HERE / n for n in ('runtime_validate.py', 'runtime-smoke.c', 'native-smoke.c',
                                      'test_runtime_build.py', 'test_runtime_validate.py', 'runtime_package.py', 'test_runtime_package.py',
                                      'runtime_sign.py', 'test_runtime_sign.py', 'wine-entitlements.plist', 'THIRD_PARTY_NOTICES.md') if (HERE / n).is_file()]
    source_files += [HERE / 'runtime-notices' / p for p in sorted(lock['notice_files'])]
    def public_metadata(info):
        info.uid = info.gid = 0
        info.uname = info.gname = ''
        info.mtime = 0
        info.pax_headers = {}
        return info

    with tarfile.open(output, 'x:gz') as kit:
        for name, path in inputs.items():
            kit.add(path, arcname='inputs/' + lock['inputs'][name]['filename'], recursive=False, filter=public_metadata)
        for path in source_files:
            arcname = 'LICENSE' if path == license_path else str(path.relative_to(HERE))
            kit.add(path, arcname=arcname, recursive=False, filter=public_metadata)
        generated = {
            'input-map.json': json.dumps({k: 'inputs/' + v['filename'] for k, v in lock['inputs'].items()}, indent=2),
            'REBUILD.txt': ('Pear Rosetta runtime source/input kit\n\n'
                'Requires macOS with Apple command-line tools, Python >= 3.12, make, pkg-config, Bison 3.8.2 and MinGW-w64 GCC for x86_64 and i686.\n'
                'From this extracted directory, verify inputs with:\n'
                '  python3 runtime_build.py verify --input-map input-map.json\n'
                'Build into a new physical path without spaces (at least 12 GiB free):\n'
                '  python3 runtime_build.py build --input-map input-map.json --bison /absolute/path/to/bison --output /private/tmp/pear-runtime-build\n'
                'Build holds the shared Pear compilation lock. For coordinated local work also supply --release-receipt.\n'
                'Runtime is the output. Toolchain identity and executed commands are recorded beside it.\n'
                'No old success receipt is used to skip deleted outputs. Existing output roots are refused.\n'
                'DXMT and MoltenVK are pinned upstream binaries; their source revisions are in runtime-inputs.json.\n'
                'This is not a byte-identical reproduction claim or qualified public release.\n'
                'No Steam, games, authentication, saves or signing credentials are included.\n')
        }
        for name, text in generated.items():
            data = text.encode(); info = tarfile.TarInfo(name); info.size = len(data)
            kit.addfile(public_metadata(info), io.BytesIO(data))
    return {'sha256': sha256(output), 'bytes': output.stat().st_size,
            'scope': 'Pinned source/input kit; upstream binary inputs explicitly identified; not complete release admission'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('verify', 'build', 'source-kit'))
    parser.add_argument('--input-map', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--bison', type=Path)
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--release-receipt', type=Path)
    parser.add_argument('--lock', type=Path, default=Path('/private/tmp/pear-native-compilation.lock'))
    parser.add_argument('--peak-gib', type=int, default=9)
    parser.add_argument('--headroom-gib', type=int, default=3)
    args = parser.parse_args()
    lock = json.loads((HERE / 'runtime-inputs.json').read_text())
    inputs = verify_inputs(json.loads(args.input_map.read_text()), lock)
    if args.action == 'verify':
        print(json.dumps({'verified_inputs': len(inputs), 'verified_notices': len(lock['notice_files'])}))
        return
    if args.output is None:
        parser.error('--output is required')
    if args.action == 'source-kit':
        print(json.dumps(source_kit(args.output, inputs, lock)))
        return
    if args.bison is None or not args.bison.is_file() or not 1 <= args.jobs <= 6:
        parser.error('Provide an existing Bison tool and 1..6 jobs')
    if args.peak_gib < 9 or args.headroom_gib < 3:
        parser.error('The planned 9 GiB peak and 3 GiB headroom must not be reduced')
    root = fresh_output(args.output)
    with heavy_slot(args.lock, args.release_receipt, (args.peak_gib + args.headroom_gib) * GIB, root.parent):
        build(root, inputs, lock, args.bison.resolve(), args.jobs)


if __name__ == '__main__':
    main()
