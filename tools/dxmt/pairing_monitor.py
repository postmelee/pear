"""Reuse the immutable bounded monitor with one source-bound Wine output link.

Wine make creates nls/locale.nls pointing to its exact selected source. No
other leaf/directory alias or special output is admitted or followed.
"""
import ast
import os
from pathlib import Path
import stat
from common import REPO, need, sha256, read_relative
import build_native

LINK = 'wine/objects/nls/locale.nls'
TARGET = '../../source/nls/locale.nls'
LOCALE_SHA256 = 'c35c8f50780a6e4248e05537e96dbc7f8249831c3f1abd3d255d93e85b91d1fd'


def directory_usage(root):
    root = Path(root)
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
                need(path.relative_to(root).as_posix() == LINK and os.readlink(path) == TARGET,
                     'pair_monitor_unlisted_alias')
                source = root / 'wine/source/nls/locale.nls'
                need(source.is_file() and not source.is_symlink() and path.resolve(strict=True) == source and
                     sha256(source) == LOCALE_SHA256,
                     'pair_monitor_locale_target')
                # Exact original Wine locale bytes are checked here and by the
                # independent source gate. Never follow this link to size it.
                need(path.lstat().st_ino == item.st_ino and os.readlink(path) == TARGET,
                     'pair_monitor_alias_changed')
            else:
                need(stat.S_ISREG(item.st_mode), 'pair_monitor_special_output')
            count += 1
            need(count <= build_native.MAX_OUTPUT_ENTRIES, 'pair_monitor_output_limit')
            total += item.st_blocks * 512
    return total


def monitored_command(root, ident, argv, env, policy, commands, cwd=None, timeout=14400):
    # Bind the original function's exact source through the constructor producer
    # snapshot; only its pure output-size observer is scoped to Wine's known link.
    raw = read_relative(REPO, 'tools/dxmt/build_native.py')
    tree = ast.parse(raw)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'monitored_command']
    need(len(nodes) == 1 and not nodes[0].decorator_list, 'pair_monitor_source_function')
    namespace = dict(vars(build_native))
    namespace['directory_usage'] = directory_usage
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'tools/dxmt/build_native.py', 'exec'), namespace)
    return namespace['monitored_command'](root, ident, argv, env, policy, commands, cwd, timeout)
