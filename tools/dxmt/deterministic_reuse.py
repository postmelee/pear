"""Closed captured-source namespace for additive reconstruction.

Original modules and global import paths are not patched. Dynamic local source
loads receive the same captured-byte importer in a unique temporary namespace.
"""
from __future__ import annotations
import builtins
from collections.abc import MutableMapping
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import types

PIN_MANIFEST_SHA = 'd2563ddc36ba8f9f9e35b438ccdf1b4aeefb03a299be9d854ca4fca93205e121'


class Error(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def need(condition, code):
    if not condition:
        raise Error(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_file(root, relative, limit=2**20):
    need(type(relative) is str and not relative.startswith('/') and
         all(p not in ('', '.', '..') for p in relative.split('/')), 'reuse_path')
    root = Path(root)
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in relative.split('/')[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        file_descriptor = os.open(relative.split('/')[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=descriptor)
        try:
            before = os.fstat(file_descriptor)
            need(stat.S_ISREG(before.st_mode) and before.st_size <= limit, 'reuse_regular_bound')
            result = bytearray()
            while len(result) <= limit:
                chunk = os.read(file_descriptor, min(65536, limit + 1 - len(result)))
                if not chunk:
                    break
                result.extend(chunk)
            after = os.fstat(file_descriptor)
            identity = lambda x: (x.st_dev, x.st_ino, x.st_mode, x.st_size, x.st_mtime_ns, x.st_ctime_ns)
            need(identity(before) == identity(after) and len(result) == before.st_size, 'reuse_source_changed')
            return bytes(result)
        finally:
            os.close(file_descriptor)
    finally:
        os.close(descriptor)


class ModuleView(MutableMapping):
    """Closed alias overlay; unrelated interpreter bindings are read-only."""
    LEGACY = {'common': 'tools/wine/common.py', 'prepare': 'tools/wine/prepare.py',
              'toolchain': 'tools/wine/toolchain.py'}
    def __init__(self, captured):
        self.captured, self.aliases = captured, {}
    def __getitem__(self, key):
        if key in self.aliases:
            return self.aliases[key]
        # Historical short aliases are private even when an unrelated global
        # binding exists: an old helper cannot observe or restore that binding.
        if key in self.LEGACY:
            raise KeyError(key)
        return sys.modules[key]
    def __iter__(self):
        return iter(set(sys.modules).difference(self.LEGACY) | set(self.aliases))
    def __len__(self):
        return len(set(self))
    def __setitem__(self, key, value):
        need(type(key) is str and isinstance(value, types.ModuleType), 'reuse_module_assignment')
        if key in self.LEGACY:
            need(value.__name__.startswith(self.captured.name + '.')
                 and self.captured.source_path(value.__file__) == self.LEGACY[key],
                 'reuse_legacy_alias_source')
            self.aliases[key] = value
        elif key.startswith('_pear_dxmt_reviewed_fex_') and '.' not in key:
            self.captured.admit_fex(key, value)
            need(key not in self.aliases and key not in sys.modules, 'reuse_package_collision')
            self.aliases[key] = value
        elif key.startswith(self.captured.name + '.'):
            selected = self.captured.dynamic_specs.get(key)
            need(selected is not None and value.__name__ == key
                 and self.captured.source_path(value.__file__) == selected,
                 'reuse_unregistered_unique_module')
            need(key not in sys.modules or sys.modules[key] is value, 'reuse_namespace_collision')
            sys.modules[key] = value
            self.captured.registered.add(key)
        else:
            raise Error('reuse_unselected_module_write')
    def __delitem__(self, key):
        if key in self.aliases:
            del self.aliases[key]
        elif key.startswith(self.captured.name + '.') and key in self.captured.registered:
            sys.modules.pop(key, None)
            self.captured.registered.discard(key)
        elif key not in self:
            raise KeyError(key)
        else:
            raise Error('reuse_unselected_module_write')


class Captured:
    def __init__(self, repo, pin_root=None):
        self.repo = Path(repo).resolve(strict=True)
        pin_root = Path(pin_root or Path(__file__).parent)
        raw = read_file(pin_root, 'reuse-pins.json')
        need(digest(raw) == PIN_MANIFEST_SHA, 'reuse_pin_manifest_changed')
        manifest = json.loads(raw)
        need(set(manifest) == {'schema_version', 'record_kind', 'files'}
             and type(manifest['schema_version']) is int and manifest['schema_version'] == 1
             and manifest['record_kind'] == 'dxmt_deterministic_predecessor_pins', 'reuse_pin_manifest')
        self.pins = manifest['files']
        need(type(self.pins) is dict and len(self.pins) == 17, 'reuse_pin_set')
        self.raw = {path: read_file(self.repo, path) for path in self.pins}
        need(all(digest(self.raw[path]) == pin for path, pin in self.pins.items()), 'reuse_predecessor_changed')
        self.name = '_pear_deterministic_' + digest(str(self.repo).encode())[:16] + '_' + os.urandom(8).hex()
        self.cache = {}
        self.registered = set()
        self.loaded = []
        self.extra_raw, self.extra_pins, self.extra_cache = {}, {}, {}
        self.fex_packages = {}
        self.dynamic_specs = {}
        self.dynamic_counter = 0
        self.module_view = ModuleView(self)
        self.sys_proxy = types.SimpleNamespace(**dict(vars(sys), modules=self.module_view))
        self.util_proxy = types.SimpleNamespace(**vars(importlib.util))
        self.util_proxy.spec_from_file_location = self.dynamic_spec
        self.import_proxy = types.SimpleNamespace(**dict(vars(__import__('importlib')),
            util=self.util_proxy, import_module=self.import_module))

    def source_path(self, path):
        path = Path(path)
        need(path.is_absolute() and '..' not in path.parts, 'reuse_source_path')
        try:
            relative = path.relative_to(self.repo).as_posix()
        except ValueError:
            key = str(path)
            need(key in self.extra_raw, 'reuse_source_outside_repo')
            return key
        need(relative in self.raw, 'reuse_unselected_source')
        return relative

    def admit_fex(self, name, package):
        # The unchanged old verify_reuse body has already checked its receipt,
        # helper pins and toolchain. This importer independently captures those
        # exact reviewed code bytes before admitting the one package alias.
        tool = self.load('tools/dxmt/tools.py')
        need(type(getattr(package, '__path__', None)) is list and len(package.__path__) == 1,
             'reuse_fex_package_path')
        directory = Path(package.__path__[0])
        need(directory.is_absolute() and '..' not in directory.parts
             and directory.name == 'fex' and directory.parent.name == 'tools', 'reuse_fex_package_path')
        owner = directory.parent.parent
        need(name == '_pear_dxmt_reviewed_fex_' + digest(str(owner).encode())[:16]
             and package.__name__ == name and package.__package__ == name, 'reuse_fex_package_identity')
        pins = dict(tool.REUSE_HELPERS, **{'tools/fex/tools.py': tool.REUSE_PRODUCER_SHA})
        for relative, expected in pins.items():
            path = str(owner / relative)
            raw = read_file(owner, relative)
            need(digest(raw) == expected, 'reuse_fex_source_changed')
            self.extra_raw[path], self.extra_pins[path] = raw, expected
        self.fex_packages[name] = directory

    def import_module(self, name, package=None):
        need(type(name) is str and package is None, 'reuse_import_module_arguments')
        parent, separator, child = name.rpartition('.')
        need(separator and parent in self.fex_packages and child in ('tools', 'common', 'prepare', 'byte_readers'),
             'reuse_unselected_package_import')
        need(parent in self.module_view.aliases, 'reuse_package_not_registered')
        module = self.load(str(self.fex_packages[parent] / (child + '.py')))
        # Preserve the original qualified package view solely inside the proxy.
        self.module_view.aliases[name] = module
        return module

    def import_source(self, name, globals=None, locals=None, fromlist=(), level=0):
        parent = globals or {}
        origin = Path(parent.get('__file__', self.repo / 'tools/dxmt/common.py'))
        if level:
            need(level == 1 and '.' not in name, 'reuse_relative_import')
            if not name:
                need(type(fromlist) in (tuple, list) and fromlist
                     and all(type(item) is str and item.isidentifier() for item in fromlist),
                     'reuse_relative_fromlist')
                selected = {}
                for child in fromlist:
                    location = origin.parent / (child + '.py')
                    key = self.source_path(location)
                    selected[child] = self.load(key)
                return types.SimpleNamespace(**selected)
        if '.' not in name:
            path = origin.parent / (name + '.py')
            try:
                key = path.relative_to(self.repo).as_posix()
            except ValueError:
                key = str(path)
            if key in self.raw or key in self.extra_raw:
                alias = self.module_view.aliases.get(name)
                if alias is not None and self.source_path(alias.__file__) == key:
                    return alias
                return self.load(key)
        if name == 'sys':
            return self.sys_proxy
        if name == 'importlib':
            return self.import_proxy
        if name == 'importlib.util':
            return self.util_proxy if fromlist else self.import_proxy
        # Existing repository-local modules cannot silently fall back to global
        # sys.path. Genuine standard-library imports remain ordinary imports.
        if '.' not in name and (origin.parent / (name + '.py')).exists():
            raise Error('reuse_local_import_unselected')
        return builtins.__import__(name, globals, locals, fromlist, level)

    def dynamic_spec(self, alias, location, *args, **kwargs):
        need(not args and not kwargs, 'reuse_dynamic_loader_arguments')
        relative = self.source_path(location)
        captured = self
        class Loader:
            def create_module(self, spec):
                return None
            def exec_module(self, module):
                captured.initialize(module, relative)
        # Each dynamic requested alias becomes owned, unique and source-bound.
        self.dynamic_counter += 1
        name = self.name + '.dynamic_' + digest((alias + relative).encode())[:16] + '_' + str(self.dynamic_counter)
        self.dynamic_specs[name] = relative
        return importlib.util.spec_from_file_location(name, self.repo / relative, loader=Loader())

    def initialize(self, module, relative):
        raw = self.raw.get(relative, self.extra_raw.get(relative))
        source = self.repo / relative
        actual = read_file(source.parent, source.name) if Path(relative).is_absolute() else read_file(self.repo, relative)
        need(actual == raw, 'reuse_predecessor_changed')
        module.__file__ = str(source)
        module.__package__ = module.__name__.rpartition('.')[0]
        module.__builtins__ = dict(vars(builtins), __import__=self.import_source)
        # Original helper registration uses only the unique dynamic alias.
        if module.__name__ not in sys.modules:
            sys.modules[module.__name__] = module
            self.registered.add(module.__name__)
        else:
            need(sys.modules[module.__name__] is module, 'reuse_namespace_collision')
        exec(compile(raw, module.__file__, 'exec'), vars(module))
        self.loaded.append({'path': relative, 'sha256': self.pins.get(relative, self.extra_pins.get(relative))})

    def load(self, relative):
        need(relative in self.raw or relative in self.extra_raw, 'reuse_unselected_source')
        if relative in self.cache:
            return self.cache[relative]
        name = self.name + '.' + relative.replace('/', '.').removesuffix('.py')
        module = types.ModuleType(name)
        self.cache[relative] = module
        try:
            self.initialize(module, relative)
        except BaseException:
            self.cache.pop(relative, None)
            raise
        return module

    def closure(self):
        need(all(read_file(self.repo, path) == raw for path, raw in self.raw.items()), 'reuse_predecessor_changed')
        need(all(read_file(Path(path).parent, Path(path).name) == raw
                 for path, raw in self.extra_raw.items()), 'reuse_fex_source_changed')
        return dict(self.pins)

    def close(self):
        # Never overwrite/remove an unrelated global module. Original helpers
        # may have registered another unique dynamic module from our spec.
        for name in list(sys.modules):
            if name.startswith(self.name + '.'):
                sys.modules.pop(name, None)
        self.cache.clear()
        self.module_view.aliases.clear()
        self.fex_packages.clear()


@contextmanager
def legacy(repo, pin_root=None):
    captured = Captured(repo, pin_root)
    try:
        yield captured
        captured.closure()
    finally:
        captured.close()
