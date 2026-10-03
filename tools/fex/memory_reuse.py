"""Isolate unchanged Wine signing and owned-process primitives for this task.

Only pure signing/observation APIs are reused. No old signing/run CLI, fatal
fixture, prefix helper or source producer is changed or executed by import.
"""
from contextlib import contextmanager
import importlib.util
import sys
if __package__:
    from .common import REPO
else:
    from common import REPO


@contextmanager
def wine_namespace():
    names = ('common', 'prepare', 'toolchain', 'build', 'signing', 'run_fixtures')
    saved = {name: sys.modules.get(name) for name in names}
    try:
        for name in names:
            spec = importlib.util.spec_from_file_location(name, REPO / 'tools/wine' / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        yield sys.modules['signing'], sys.modules['run_fixtures']
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
