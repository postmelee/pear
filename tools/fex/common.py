"""Component-local bounds and exact-byte helpers reused from the Wine owner.

No helper promotes a source or compiler observation to runtime eligibility.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import time

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location('pear_fex_wine_data', REPO / 'tools/wine/common.py')
_data = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_data)
for _name in ('Error', 'need', 'relative', 'open_relative', 'read_relative', 'sha256',
              'decode_json', 'load_json', 'record', 'encoded', 'MAX_JSON', 'MAX_FILE', 'HEX256'):
    globals()[_name] = getattr(_data, _name)


def digest_bytes(data):
    need(isinstance(data, bytes), 'digest_bytes_type')
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    """Write a fresh private record without replacing existing evidence."""
    with Path(path).open('xb') as stream:
        stream.write(encoded(value))
    os.chmod(path, 0o600)
    return {'path': Path(path).name, 'sha256': sha256(path)}


def operation_output(value, *, repo_root=REPO, require_empty=True, create=True):
    """Admit one operation child, never an arbitrary filesystem output root."""
    root = Path(repo_root).absolute()
    candidate = Path(value)
    if candidate.is_absolute():
        try:
            value = str(candidate.relative_to(root))
        except ValueError:
            raise Error('output_scope') from None
    else:
        value = str(value)
    need(re.fullmatch(r'\.build/task5/[a-z0-9][a-z0-9_-]{0,95}', value) is not None, 'output_scope')
    path = root
    for part in relative(value):
        path /= part
        need(not path.is_symlink(), 'symlink_output')
        need(not path.exists() or path.is_dir(), 'non_directory_output')
    need(not require_empty or not path.exists() or not any(path.iterdir()), 'output_not_empty')
    if create:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.chmod(0o700)
    return path


def bounded_command(argv, *, cwd=None, output_dir=None, timeout=120,
                    max_output=8 * 1024 * 1024, env=None):
    """Run a caller-selected command, preserving nonzero exit and raw bytes.

    This is private orchestration, not a command accepted from input records.
    Timeout/output limits kill and reap only the owned process group. A caller
    must separately verify executable provenance and interpret capabilities.
    """
    need(isinstance(argv, list) and argv and all(isinstance(x, str) and '\0' not in x for x in argv),
         'command_arguments')
    need(type(timeout) in (int, float) and 0 < timeout <= 600
         and type(max_output) is int and 0 < max_output <= 128 * 1024 * 1024, 'command_bounds')
    environment = {k: v for k, v in os.environ.items()
                   if not k.startswith(('GIT_', 'DYLD_', 'LD_', 'FEX_'))}
    if env is not None:
        need(isinstance(env, dict) and all(isinstance(k, str) and isinstance(v, str)
             and '\0' not in k + v for k, v in env.items()), 'command_environment')
        environment = dict(env)
    started = time.monotonic()
    try:
        child = subprocess.Popen(argv, cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    except OSError:
        raise Error('command_start_failed') from None
    output = {'stdout': bytearray(), 'stderr': bytearray()}
    failure = None
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ, 'stdout')
            selector.register(child.stderr, selectors.EVENT_READ, 'stderr')
            while selector.get_map():
                remaining = timeout - (time.monotonic() - started)
                need(remaining > 0, 'command_timeout')
                for key, _ in selector.select(min(remaining, .25)):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        output[key.data].extend(chunk)
                        need(sum(map(len, output.values())) <= max_output, 'command_output_limit')
            code = child.wait(timeout=max(.01, timeout - (time.monotonic() - started)))
    except (Error, subprocess.TimeoutExpired) as error:
        failure = error if isinstance(error, Error) else Error('command_timeout')
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except (PermissionError, ProcessLookupError):
            if child.poll() is None:
                child.kill()
        try:
            child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            failure = Error('command_cleanup_unverified')
    finally:
        child.stdout.close()
        child.stderr.close()
        if output_dir is not None:
            root = Path(output_dir)
            for name, data in output.items():
                with (root / (name + '.bin')).open('xb') as stream:
                    stream.write(data)
                os.chmod(root / (name + '.bin'), 0o600)
    if failure:
        raise failure
    return {'argv': list(argv), 'returncode': code, 'elapsed_ms': int((time.monotonic() - started) * 1000),
            'stdout': bytes(output['stdout']), 'stderr': bytes(output['stderr']), 'status': 'completed'}
