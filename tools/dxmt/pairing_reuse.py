"""Read-only reuse of the exact historical Wine toolchain reader.

The namespace relocation only selects its already-owned Stage 6 input cache;
no old producer, archive, executable, or qualification record is changed.
"""
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import sys
from common import REPO, Error, digest, need, read_relative, real_directory, sha256


@contextmanager
def historical_toolchain(wine_root):
    owner = real_directory(wine_root).parents[2]
    names = ('common', 'prepare', 'toolchain')
    saved = {name: sys.modules.get(name) for name in names}
    try:
        for name in names:
            spec = importlib.util.spec_from_file_location(name, REPO / 'tools/wine' / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        reader = sys.modules['toolchain']
        # This immutable reader scopes archives and task_path to its owner.
        reader.REPO = owner
        yield reader
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def verify_wine_tools(wine_root, wine_build, lock):
    for name in ('common.py', 'prepare.py', 'toolchain.py'):
        expected = wine_build['producer_sha256'][name]
        need(digest(read_relative(REPO, 'tools/wine/' + name)) == expected,
             'pair_historical_toolchain_reader_changed')
    tools = real_directory(wine_build['tools_root'])
    need(tools.is_relative_to(real_directory(wine_root).parents[2] / '.build/task4'),
         'pair_historical_tools_owner')
    with historical_toolchain(wine_root) as reader:
        try:
            reader.verify_prepared_tools(lock, tools)
        except reader.Error as error:
            raise Error(error.code) from error
    return {'path': str(tools), 'sha256': sha256(tools / 'prepared.json')}
