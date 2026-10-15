#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Relocated synthetic runtime checks. Never accepts an existing/private prefix."""
import argparse
import json
import os
from pathlib import Path
import shutil
import selectors
import subprocess
import time
import runtime_build as rb

HERE = Path(__file__).resolve().parent


class CommandFailure(RuntimeError):
    def __init__(self, code, log):
        self.code = code
        super().__init__(f'Check failed ({code}): {log.name}')


def run(cmd, env, log, timeout=120, max_log_bytes=16 * 1024 * 1024, observer=None):
    # Bound bytes while reading, so even a fast failing guest cannot fill the disk.
    with log.open('wb') as output:
        child = subprocess.Popen([str(v) for v in cmd], env=env,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + timeout
        total = 0
        marker_tail = b''
        observed = False
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(child.stdout, selectors.EVENT_READ)
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise RuntimeError('Check timed out: ' + log.name)
                    for key, _ in selector.select(min(remaining, 0.05)):
                        data = os.read(key.fd, 65536)
                        if not data:
                            selector.unregister(key.fileobj)
                            continue
                        available = max_log_bytes - total
                        output.write(data[:available])
                        total += min(len(data), available)
                        marker_tail = (marker_tail + data)[-131072:]
                        if observer and not observed and b'PEAR_RUNTIME_OBSERVE_READY' in marker_tail:
                            observer(child.pid)
                            observed = True
                        if len(data) > available:
                            raise RuntimeError('Check log limit exceeded: ' + log.name)
                remaining = deadline - time.monotonic()
                try:
                    child.wait(timeout=max(remaining, 0))
                except subprocess.TimeoutExpired:
                    raise RuntimeError('Check timed out: ' + log.name) from None
        finally:
            if child.poll() is None:
                child.kill()
            child.wait()
            child.stdout.close()
    if child.returncode:
        raise CommandFailure(child.returncode, log)
    return log.read_text(errors='replace')


def validate_wine_images(text, runtime):
    images = sorted({line[1:] for line in text.splitlines() if line.startswith('n')})
    native = [Path(name) for name in images if name.endswith(('.dylib', '.so'))]
    unexpected = [str(path) for path in native
                  if not path.resolve().is_relative_to(runtime.resolve())
                  and not str(path).startswith(('/System/Library/', '/usr/lib/'))]
    if unexpected:
        raise RuntimeError('External Wine native image: ' + ', '.join(unexpected))
    packaged = sorted({path.name for path in native
                       if path.resolve().is_relative_to(runtime.resolve())})
    if not {'libgnutls.30.dylib', 'libfreetype.6.dylib'}.issubset(packaged):
        raise RuntimeError('Incomplete Wine process helper mapping evidence')
    return {'packaged_helpers': packaged, 'external_helper_loads': 0,
            'native_image_count': len(native)}


def stop_synthetic_server(runtime, output, env):
    stop_code = 0
    try:
        run([runtime / 'bin/wineserver', '-k'], env, output / 'synthetic-stop.log', 30)
    except CommandFailure as error:
        # Wine also returns 1 when the prefix's server already exited. Do not
        # treat that alone as cleanup: wait and independently inspect handles.
        if error.code != 1:
            raise
        stop_code = error.code
    run([runtime / 'bin/wineserver', '-w'], env, output / 'synthetic-wait.log', 30)
    snapshot = run(['/usr/sbin/lsof', '-nP', '-Fpn'], env,
                   output / 'synthetic-handles.log', 25)
    prefix_name = 'n' + str(output / 'synthetic-prefix')
    if any(line == prefix_name or line.startswith(prefix_name + '/')
           for line in snapshot.splitlines()):
        raise RuntimeError('Synthetic output still has open handles')
    return stop_code


def validate(runtime, output):
    if output.exists() or output.is_symlink():
        raise ValueError('Validation requires an absent output root, never an existing prefix')
    output.mkdir()
    prefix = output / 'synthetic-prefix'
    env = {k: os.environ[k] for k in ('HOME', 'USER', 'TMPDIR') if k in os.environ}
    env.update(PATH='/usr/bin:/bin:/usr/sbin:/sbin', WINEPREFIX=str(prefix), WINEARCH='win64',
               WINEDEBUG='+winhttp,+loaddll',
               WINEDLLOVERRIDES='winemenubuilder.exe=d;mscoree,mshtml=d')
    expected = json.loads((runtime.parent.parent / 'runtime-manifest.json').read_text())
    if rb.inventory(runtime) != expected:
        raise ValueError('Runtime no longer matches its build manifest')
    record = {'scope': 'New unauthenticated synthetic prefix, no Steam/game/private data',
              'runtime_manifest_sha256': rb.sha256(runtime.parent.parent / 'runtime-manifest.json'),
              'checks': {}, 'cleanup': 'pending'}
    try:
        run(['clang', '-arch', 'x86_64', HERE / 'native-smoke.c', '-o', output / 'native-smoke'],
            env, output / 'compile-native.log')
        mingw = Path('/opt/homebrew/bin/x86_64-w64-mingw32-gcc')
        record['probe_compiler'] = {'path': str(mingw.resolve()), 'sha256': rb.sha256(mingw)}
        run([mingw, HERE / 'runtime-smoke.c', '-o', output / 'runtime-smoke.exe',
             '-lbcrypt', '-lwinhttp', '-lgdi32'], env, output / 'compile-pe.log')
        for name in ('native-smoke', 'runtime-smoke.exe'):
            record[name + '_sha256'] = rb.sha256(output / name)
        native = run([output / 'native-smoke', runtime / 'lib/libgnutls.30.dylib',
                      runtime / 'lib/libfreetype.6.dylib', runtime / 'lib/libMoltenVK.dylib'],
                     env | {'DYLD_PRINT_LIBRARIES': '1'}, output / 'native.log', 30)
        record['checks']['native_initialization'] = 'passed'
        run([runtime / 'bin/wine', '--version'], env, output / 'wine-version.log', 30)
        def observe(pid):
            snapshot = run(['/usr/sbin/lsof', '-a', '-p', str(pid), '-d', 'txt', '-Fn'],
                           env, output / 'wine-images.log', 5)
            record['checks']['wine_process_images'] = dict(
                pid=pid, **validate_wine_images(snapshot, runtime))
        trace = run([runtime / 'bin/wine', output / 'runtime-smoke.exe'],
                    env | {'DYLD_PRINT_LIBRARIES': '1'}, output / 'windows.log', 180,
                    observer=observe)
        if 'wine_process_images' not in record['checks']:
            raise RuntimeError('Missing owned Wine process observation marker')
        required = ['AES known-answer passed', 'Font metrics height=',
                    'HTTPS store.steampowered.com success=1 status=200',
                    'HTTPS badssl.com success=1 status=200',
                    'HTTPS wrong.host.badssl.com success=0', 'cert verify failed: 12038']
        if not all(x in trace for x in required):
            raise RuntimeError('Missing positive/negative TLS or crypto/font evidence')
        load_lines = [x for x in (native + trace).splitlines() if x.startswith('dyld[')]
        bad = [x for x in load_lines if any(s in x for s in ('/deps/lib/', '/opt/homebrew/',
               '/pear47-inprocess/', '/steam-inprocess-candidate/', '/private/preview-first-login/'))]
        if bad:
            raise RuntimeError('Unexpected external helper load')
        record['checks']['windows_crypto_font_tls'] = 'passed'
        record['checks']['wrong_host_rejected_with_specific_trace'] = True
        record['checks']['external_helper_loads'] = len(bad)
        record['checks']['observed_packaged_helpers'] = sorted({Path(x.split()[-1]).name for x in load_lines
            if str(runtime / 'lib') in x and '.dylib' in x})
        required_helpers = {'libfreetype.6.dylib', 'libgnutls.30.dylib', 'libgmp.10.dylib',
                            'libnettle.9.0.dylib', 'libhogweed.7.0.dylib', 'libtasn1.6.dylib',
                            'libunistring.5.dylib', 'libidn2.0.dylib', 'libpng16.16.dylib',
                            'libMoltenVK.dylib'}
        if not required_helpers.issubset(record['checks']['observed_packaged_helpers']):
            raise RuntimeError('Incomplete packaged helper load evidence')
        # Exercise the actual patched process-creation path in both guest ABIs.
        # The fixture owns every handle it cleans up; Steam and games are absent.
        for arch, compiler in (('x86_64', 'x86_64-w64-mingw32-gcc'),
                               ('i386', 'i686-w64-mingw32-gcc')):
            executable = output / 'browser-lifetime.exe'
            run([Path('/opt/homebrew/bin') / compiler, '-Wall', '-Wextra', '-Werror',
                 '-Wno-misleading-indentation', '-O2', HERE / 'browser-lifetime-smoke.c',
                 '-o', executable], env, output / f'compile-lifetime-{arch}.log')
            shutil.copy2(executable, output / 'other.exe')
            trace = run([runtime / 'bin/wine', executable], env | {'WINEDEBUG': '-all'},
                        output / f'lifetime-{arch}.log', 120)
            record['checks']['browser_lifetime_' + arch] = {
                'status': 'passed', 'fixture_sha256': rb.sha256(executable),
                'source_sha256': rb.sha256(HERE / 'browser-lifetime-smoke.c')}
        record['status'] = 'passed'
    except Exception as error:
        record.update(status='failed', error=str(error))
        raise
    finally:
        # This prefix was created here and has never run Steam or a game. Only its
        # owned synthetic Wine services may be terminated; never use a private prefix.
        if prefix.exists():
            if (prefix / 'drive_c/Program Files (x86)/Steam').exists():
                raise RuntimeError('Unexpected Steam state; refusing synthetic cleanup')
            try:
                record['synthetic_stop_exit'] = stop_synthetic_server(runtime, output, env)
                record['cleanup'] = 'owned synthetic server stopped; prefix retained for bounded cleanup'
            except Exception as error:
                record['cleanup'] = str(error)
                record['status'] = 'failed'
                record.setdefault('error', 'Synthetic cleanup not confirmed: ' + str(error))
        rb.write_json(output / 'result.json', record)
    if record['cleanup'].startswith('owned synthetic server stopped'):
        shutil.rmtree(prefix)
        record['cleanup'] = 'owned synthetic server stopped; unauthenticated prefix removed'
        rb.write_json(output / 'result.json', record)
    else:
        raise RuntimeError('Synthetic cleanup not confirmed')
    print(json.dumps(record, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--release-receipt', type=Path, required=True)
    args = p.parse_args()
    with rb.heavy_slot(Path('/private/tmp/pear-native-compilation.lock'),
                       args.release_receipt, 3 * rb.GIB, args.output.parent):
        validate(args.runtime.resolve(strict=True), args.output.absolute())


if __name__ == '__main__':
    main()
