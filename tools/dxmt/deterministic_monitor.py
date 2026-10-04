"""Observe deterministic build output, including owned Metal module locks.

The historical Wine monitor and process supervisor remain unchanged. LLVM's
module cache briefly uses absolute sibling lock links; never follow them for
accounting or admit an alias outside this exact compiler-cache namespace.
"""
import os
from pathlib import Path
import re
import stat
from types import FunctionType, SimpleNamespace

LOCK = re.compile(r"dxmt/shader-cache/[A-Z0-9]+/(?:[A-Za-z0-9_-]+\.pcm|modules\.idx)\.lock")


def cache_lock(root, path, original, legacy):
    need = legacy.need
    need(LOCK.fullmatch(path.relative_to(root).as_posix()) is not None,
         'det_monitor_unlisted_alias')
    try:
        target = os.readlink(path)
    except FileNotFoundError:
        return  # The observed compiler lock has already been released.
    # Require a literal absolute sibling path, without normalization/resolve.
    prefix = str(path) + '-'
    need(target.startswith(prefix) and re.fullmatch('[0-9a-f]{8}', target[len(prefix):]) is not None,
         'det_monitor_lock_target')
    try:
        sibling = Path(target).lstat()
    except FileNotFoundError:
        sibling = None  # Lock cleanup can remove the sibling first.
    if sibling is not None:
        need(stat.S_ISREG(sibling.st_mode) and sibling.st_nlink == 1,
             'det_monitor_lock_target_type')
    try:
        current = path.lstat()
    except FileNotFoundError:
        return
    need(stat.S_ISLNK(current.st_mode) and
         (current.st_dev, current.st_ino, current.st_mtime_ns, current.st_ctime_ns) ==
         (original.st_dev, original.st_ino, original.st_mtime_ns, original.st_ctime_ns),
         'det_monitor_lock_changed')
    try:
        need(os.readlink(path) == target, 'det_monitor_lock_changed')
    except FileNotFoundError:
        pass


def directory_usage(root, legacy):
    root = Path(root)
    need = legacy.need
    need(root.is_absolute(), 'det_monitor_absolute_root')
    total = count = 0
    def walk_error(error):
        if not isinstance(error, FileNotFoundError):
            raise error
    for directory, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
        try:
            current = Path(directory).lstat()
        except FileNotFoundError:
            dirs[:] = []
            continue
        need(stat.S_ISDIR(current.st_mode), 'pair_monitor_directory_alias')
        retained = []
        for name in dirs:
            try:
                item = (Path(directory) / name).lstat()
            except FileNotFoundError:
                continue
            need(stat.S_ISDIR(item.st_mode), 'pair_monitor_directory_alias')
            retained.append(name)
        dirs[:] = retained
        for name in names:
            path = Path(directory) / name
            try:
                item = path.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(item.st_mode):
                if path.relative_to(root).as_posix() == legacy.LINK:
                    need(os.readlink(path) == legacy.TARGET, 'pair_monitor_unlisted_alias')
                    source = root / 'wine/source/nls/locale.nls'
                    need(source.is_file() and not source.is_symlink() and path.resolve(strict=True) == source and
                         legacy.sha256(source) == legacy.LOCALE_SHA256, 'pair_monitor_locale_target')
                    need(path.lstat().st_ino == item.st_ino and os.readlink(path) == legacy.TARGET,
                         'pair_monitor_alias_changed')
                else:
                    cache_lock(root, path, item, legacy)
            else:
                need(stat.S_ISREG(item.st_mode), 'pair_monitor_special_output')
            count += 1
            need(count <= legacy.build_native.MAX_OUTPUT_ENTRIES, 'pair_monitor_output_limit')
            total += item.st_blocks * 512
    return total


def bind(legacy):
    observe = lambda root: directory_usage(root, legacy)
    # Reuse the exact captured adapter code and its immutable supervisor source.
    # A private globals copy avoids mutating historical module interpretation.
    original = legacy.monitored_command
    namespace = dict(original.__globals__)
    namespace['directory_usage'] = observe
    command = FunctionType(original.__code__, namespace, original.__name__, original.__defaults__, original.__closure__)
    command.__kwdefaults__ = original.__kwdefaults__
    return SimpleNamespace(directory_usage=observe, monitored_command=command)
