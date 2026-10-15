#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Select an explicit development runtime without changing Pear Preview state.

Preparation/selection/inspection never grants execution. Each diagnostic delegates
its current lease, authority, ownership and cleanup to the runtime operation.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import uuid

PURPOSE = 'development_diagnostics'
SPEC_FIELDS = {'schema_version', 'scope', 'purpose', 'runtime_checkout', 'lock_ref',
               'fixture_descriptor_ref', 'game_descriptor_ref', 'state_root', 'protected_roots'}
LOCK_FIELDS = {'schema_version', 'scope', 'purpose', 'candidate', 'component_sources',
               'reconstruction', 'tool_sources', 'assembly_tool_checkpoint'}
MAX_JSON = 16 * 1024**2
PEAR_ROOT = Path(__file__).resolve().parents[2]


class Refusal(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(value, code):
    if not value:
        raise Refusal(code)


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_json_key')
        result[key] = value
    return result


def canonical(path, *, directory=False, fresh=False):
    require(type(path) is str, 'path_type')
    value = Path(path)
    require(value.is_absolute() and value == value.resolve(strict=not fresh), 'path_alias')
    require(not value.is_symlink(), 'path_alias')
    if fresh:
        require(value.parent.is_dir() and value.parent.resolve(strict=True) == value.parent,
                'fresh_parent')
        require(not value.exists(), 'output_exists')
    elif directory:
        require(value.is_dir(), 'directory_required')
    else:
        require(value.is_file(), 'file_required')
    return value


def metadata_bytes(path):
    path = canonical(str(path))
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_JSON, 'metadata_size')
        chunks, total = [], 0
        while True:
            raw = os.read(fd, min(65536, MAX_JSON + 1 - total))
            if not raw:
                break
            chunks.append(raw)
            total += len(raw)
            require(total <= MAX_JSON, 'metadata_size')
        after = os.fstat(fd)
        current = canonical(str(path)).stat()
        fields = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns)
        require(fields(before) == fields(after) == fields(current) and total == after.st_size,
                'metadata_changed')
        return b''.join(chunks)
    finally:
        os.close(fd)


def fact(path):
    path = canonical(str(path))
    raw = metadata_bytes(path)
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))


def identity(value):
    require(type(value) is dict and set(value) == {'sha256', 'size_bytes'}, 'identity_shape')
    require(type(value['size_bytes']) is int and 0 <= value['size_bytes'] <= MAX_JSON and
            type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}', value['sha256']),
            'identity_value')
    return value


def compact(ref):
    require(type(ref) is dict and set(ref) == {'path', 'sha256', 'size_bytes'}, 'reference_shape')
    return identity({key: ref[key] for key in ('sha256', 'size_bytes')})


def read_ref(ref):
    compact(ref)
    require(fact(ref['path']) == ref, 'reference_changed')
    raw = metadata_bytes(ref['path'])
    require(hashlib.sha256(raw).hexdigest() == ref['sha256'], 'reference_changed')
    value = json.loads(raw, object_pairs_hook=unique,
                       parse_constant=lambda _: (_ for _ in ()).throw(Refusal('json_nonfinite')))
    require(fact(ref['path']) == ref, 'reference_changed')
    return value


def commit(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{40}', value), 'commit_identity')
    return value


def git(root, *args):
    result = subprocess.run(['/usr/bin/git', '-C', str(root), *args], capture_output=True,
                            text=True, timeout=30, check=False)
    require(result.returncode == 0, 'checkout_git_refused')
    return result.stdout.strip()


def checkout(value):
    require(type(value) is dict and set(value) == {'path', 'commit'}, 'checkout_shape')
    root = canonical(value['path'], directory=True)
    require(git(root, 'rev-parse', '--show-toplevel') == str(root), 'checkout_root')
    require(git(root, 'rev-parse', 'HEAD') == commit(value['commit']), 'checkout_commit')
    flags = git(root, 'ls-files', '-v', '-z').split('\0')
    require(all(not row or row.startswith('H ') for row in flags), 'checkout_hidden_index_flags')
    require(git(root, 'status', '--porcelain=v1', '--untracked-files=all') == '', 'checkout_dirty')
    return root


def isolated(a, b):
    return not a.is_relative_to(b) and not b.is_relative_to(a)


def selection(ref):
    value = read_ref(ref)
    require(type(value) is dict and set(value) == SPEC_FIELDS and
            type(value['schema_version']) is int and value['schema_version'] == 1 and
            value['scope'] == 'pear_development_selection' and value['purpose'] == PURPOSE,
            'selection_scope')
    root = checkout(value['runtime_checkout'])
    lock = read_ref(value['lock_ref'])
    require(type(lock) is dict and set(lock) == LOCK_FIELDS and
            type(lock['schema_version']) is int and lock['schema_version'] == 1 and
            lock['scope'] == 'pear_development_candidate_lock' and lock['purpose'] == PURPOSE,
            'lock_scope')
    require(type(lock['tool_sources']) is dict and set(lock['tool_sources']) == {'runtime', 'wine', 'fex'},
            'lock_tool_sources')
    for pin in (*lock['tool_sources'].values(), lock['assembly_tool_checkpoint']):
        commit(pin)
    require(lock['tool_sources']['runtime'] == value['runtime_checkout']['commit'], 'lock_tool_commit')
    historical = lock['reconstruction']
    require(type(historical) is dict and set(historical) == {'path', 'sha256', 'size_bytes'} and
            historical['path'] == 'locks/task56-reconstruction-v1.json', 'reconstruction_path')
    read_ref({**historical, 'path': str(root / historical['path'])})
    candidate = lock['candidate']
    require(type(candidate) is dict and set(candidate) == {'runtime', 'assembly_operation', 'builds'} and
            type(candidate['builds']) is dict and set(candidate['builds']) == {'fex', 'wine', 'graphics'},
            'lock_candidate')
    for item in (candidate['runtime'], candidate['assembly_operation'], *candidate['builds'].values()):
        identity(item)
    pins = lock['component_sources']
    require(type(pins) is dict and set(pins) == {'wine', 'fex', 'dxmt'}, 'component_source_set')
    for pin in pins.values():
        commit(pin)
    descriptor = read_ref(value['fixture_descriptor_ref'])
    require(compact(descriptor['runtime_ref']) == candidate['runtime'] and
            compact(descriptor['operation_ref']) == candidate['assembly_operation'], 'candidate_lock_mismatch')
    runtime = read_ref(descriptor['runtime_ref'])
    builds = runtime['development_assembly']['builds']
    require(type(builds) is list and len(builds) == 3 and
            sorted((r['sha256'], r['size_bytes']) for r in builds) ==
            sorted((r['sha256'], r['size_bytes']) for r in candidate['builds'].values()), 'build_lock_mismatch')
    observed = {}
    operations = runtime['development_assembly']['component_operations']
    require(type(operations) is list and len(operations) == 3, 'component_operation_set')
    for ref_ in builds:
        built = read_ref(ref_)
        require(built.get('status') == 'passed' and built.get('scope') == 'development_component_build' and
                built.get('failure') is None and built.get('failure_code') is None, 'component_build_failed')
        matched = [row for row in operations if row['path'] ==
                   str(Path(ref_['path']).parent / 'operation.json')]
        require(len(matched) == 1, 'component_operation_binding')
        operation = read_ref(matched[0])
        require(operation.get('scope') == 'task56_component_build' and
                type(built.get('operation_id')) is str and
                operation.get('operation_id') == built['operation_id'] and
                operation.get('released') is True, 'component_operation_unreleased')
        for name, source in built['roots'].items():
            if name in pins:
                require(source.get('kind') == 'git' and source.get('commit') == pins[name], 'component_source_mismatch')
                observed[name] = source['commit']
    require(observed == pins, 'component_source_missing')
    descriptors = [descriptor]
    if value['game_descriptor_ref'] is not None:
        game = read_ref(value['game_descriptor_ref'])
        require(game['runtime_ref'] == descriptor['runtime_ref'] and
                game['operation_ref'] == descriptor['operation_ref'], 'game_candidate_mismatch')
        descriptors.append(game)
    manifests = [read_ref(d['producer_manifest_ref']) for d in descriptors]
    for manifest in manifests:
        require(manifest['roots']['runtime'] == str(root), 'producer_runtime_checkout')
    roots = {root, PEAR_ROOT, Path(descriptor['runtime_ref']['path']).parent,
             Path(ref['path']).parent, Path(value['lock_ref']['path']).parent}
    for d, manifest in zip(descriptors, manifests):
        roots.update(Path(p) for p in manifest['roots'].values())
        roots.update(Path(d[k]) for k in ('provider_root', 'seed_root', 'output_root'))
        roots.add(Path(d['profile_ref']['path']).parent)
        if 'game_root' in d:
            roots.add(Path(d['game_root']))
        # Metadata must not be overwritten through a selector state alias.
        roots.update(Path(v['path']).parent for v in d.values()
                     if type(v) is dict and set(v) == {'path', 'sha256', 'size_bytes'})
    protected = value['protected_roots']
    require(type(protected) is list and protected and len(protected) == len(set(protected)), 'protected_roots')
    roots.update(canonical(p, directory=True) for p in protected)
    state = Path(value['state_root'])
    if state.exists():
        canonical(str(state), directory=True)
    else:
        canonical(str(state), fresh=True)
    require(all(isolated(state, p) for p in roots), 'state_input_overlap')
    require(all(isolated(Path(d['output_root']), p) for d in descriptors for p in
                (canonical(r, directory=True) for r in protected)), 'diagnostic_protected_overlap')
    require(read_ref(ref) == value, 'selection_changed')
    return value, lock, descriptor


def load_runtime(value, descriptor):
    root = Path(value['runtime_checkout']['path'])
    manifest = read_ref(descriptor['producer_manifest_ref'])
    require(type(manifest.get('files')) is list and manifest['files'], 'producer_file_set')
    roots = {'runtime': root}
    pins = {'runtime': value['runtime_checkout']['commit']}
    if 'fex' in manifest['roots']:
        pins['fex'] = read_ref(value['lock_ref'])['tool_sources']['fex']
        roots['fex'] = checkout(dict(path=manifest['roots']['fex'], commit=pins['fex']))
    for row in manifest['files']:
        if row['root'] not in roots:
            continue
        owner_root = roots[row['root']]
        relative = Path(row['path'])
        require(not relative.is_absolute() and all(p not in ('', '.', '..') for p in relative.parts),
                'producer_relative_path')
        raw = metadata_bytes(owner_root / relative)
        blob = subprocess.run(['/usr/bin/git', '-C', str(owner_root), 'cat-file', 'blob',
                               pins[row['root']] + ':' + row['path']],
                              capture_output=True, check=False, timeout=30)
        require(blob.returncode == 0 and blob.stdout == raw and
                hashlib.sha256(raw).hexdigest() == row['sha256'] and len(raw) == row['size_bytes'],
                'producer_commit_content')
    for name, module in tuple(sys.modules.items()):
        if name == 'pear_runtime' or name.startswith('pear_runtime.'):
            path = getattr(module, '__file__', None)
            require(path is not None and Path(path).resolve().is_relative_to(root), 'loaded_runtime_origin')
    # The captured producer validator checks every loaded runtime/FEX module.
    paths = [str(root)]
    if 'fex' in manifest['roots']:
        paths.append(str(canonical(manifest['roots']['fex'], directory=True)))
    for path in reversed(paths):
        if path not in sys.path:
            sys.path.insert(0, path)
    return importlib.import_module('pear_runtime.fixtures.context')


@contextmanager
def no_execution(_output):
    raise Refusal('inspection_cannot_execute')
    yield  # pragma: no cover


def inspect(ref, *, kind='auto'):
    value, lock, descriptor = selection(ref)
    require(kind in ('auto', 'fixture', 'game'), 'inspection_kind')
    if kind == 'auto':
        kind = 'game' if value['game_descriptor_ref'] is not None else 'fixture'
    if kind == 'game':
        require(value['game_descriptor_ref'] is not None, 'game_descriptor_required')
    bootstrap = read_ref(value['game_descriptor_ref']) if kind == 'game' else descriptor
    api = load_runtime(value, bootstrap)
    require(set(descriptor) == api.FIELDS and type(descriptor['schema_version']) is int and
            descriptor['schema_version'] == 1 and descriptor['scope'] == 'redistributable_runtime_fixtures' and
            descriptor['candidate'] == 'd25-game', 'fixture_descriptor_shape')
    suffix = 'selection-inspection-' + uuid.uuid4().hex
    fixture = game_result = None
    if kind == 'fixture':
        from pear_runtime.fixtures.types import Selection
        context = api.FixtureContext(value['fixture_descriptor_ref'],
            Selection('d25-game', Path(descriptor['runtime_ref']['path']).parent), no_execution)
        fixture = context.inspect(Path(descriptor['output_root']) / suffix)
    else:
        require(value['game_descriptor_ref'] is not None, 'game_descriptor_required')
        from tools.development.game.context import GameContext
        game = GameContext(value['game_descriptor_ref'])
        game_result = game.inspect(Path(game.value['output_root']) / suffix)
    require(read_ref(ref) == value, 'selection_changed')
    checkout(value['runtime_checkout'])
    return dict(schema_version=1, scope='pear_development_selection_inspection',
                selection_ref=ref, lock_ref=value['lock_ref'], runtime_checkout=value['runtime_checkout'],
                component_sources=lock['component_sources'], inspected_kind=kind,
                fixture=fixture, game=game_result, other_descriptor_metadata_only=True,
                current_authority_assessed=False, execution_authorized_by_this_record=False,
                runtime_execution_performed=False, game_qualified=False)


def write_new(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    with path.open('xb') as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return fact(path)


def state_root(value, *, create=False):
    root = Path(value['state_root'])
    marker = dict(schema_version=1, scope='pear_development_selection_state', purpose=PURPOSE)
    if create and not root.exists():
        root.mkdir(mode=0o700)
        write_new(root / 'owner.json', marker)
        (root / 'selections').mkdir(mode=0o700)
        (root / 'transactions').mkdir(mode=0o700)
    canonical(str(root), directory=True)
    owner = read_ref(fact(root / 'owner.json'))
    require(type(owner) is dict and type(owner.get('schema_version')) is int and
            owner == marker, 'foreign_state_root')
    for name in ('selections', 'transactions'):
        canonical(str(root / name), directory=True)
    return root


def prepare(spec_path):
    ref = fact(spec_path)
    inspected = inspect(ref)
    value = read_ref(ref)
    root = state_root(value, create=True)
    target = root / 'selections' / (ref['sha256'] + '.json')
    record = dict(schema_version=1, scope='pear_prepared_development_selection',
                  specification_ref=ref, specification=value, inspection=inspected)
    if target.exists():
        existing_ref, existing = prepared(target)
        require(existing['specification_ref'] == ref and existing['specification'] == value,
                'prepared_selection_conflict')
        # Prior inspection remains historical; fresh inspection was performed above.
        return existing_ref
    return write_new(target, record)


def prepared(path):
    ref = fact(path)
    value = read_ref(ref)
    require(type(value) is dict and set(value) == {'schema_version', 'scope', 'specification_ref',
            'specification', 'inspection'} and type(value['schema_version']) is int and
            value['schema_version'] == 1 and value['scope'] == 'pear_prepared_development_selection',
            'prepared_selection_shape')
    require(read_ref(value['specification_ref']) == value['specification'], 'prepared_specification_changed')
    spec = value['specification']
    root = state_root(spec)
    require(Path(ref['path']) == root / 'selections' / (value['specification_ref']['sha256'] + '.json'),
            'prepared_selection_path')
    return ref, value


def select(path):
    ref, value = prepared(path)
    inspect(value['specification_ref'])
    root = state_root(value['specification'])
    lock = os.open(root / 'selection.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        active = root / 'active.json'
        previous = None
        if active.exists() or active.is_symlink():
            previous = read_ref(fact(active))
            require(type(previous) is dict and set(previous) == {'schema_version', 'scope', 'prepared_ref'} and
                    type(previous['schema_version']) is int and previous['schema_version'] == 1 and
                    previous['scope'] == 'pear_active_development_selection', 'foreign_active_selection')
            old_ref, old_record = prepared(previous['prepared_ref']['path'])
            require(old_ref == previous['prepared_ref'], 'previous_selection_changed')
            require(Path(old_record['specification']['state_root']) == root, 'previous_selection_foreign_state')
        selected = dict(schema_version=1, scope='pear_active_development_selection', prepared_ref=ref)
        ident = uuid.uuid4().hex
        journal = write_new(root / 'transactions' / (ident + '.json'),
                            dict(previous=previous, selected=selected, selector_ref=fact(__file__)))
        temporary = root / (ident + '.active.json')
        write_new(temporary, selected)
        os.replace(temporary, active)
        return dict(active_ref=fact(active), transaction_ref=journal, prepared_ref=ref,
                    preview_changed=False, execution_authorized_by_this_record=False)
    finally:
        os.close(lock)


def active_path(root):
    root = canonical(str(root), directory=True)
    value = read_ref(fact(root / 'active.json'))
    require(type(value) is dict and set(value) == {'schema_version', 'scope', 'prepared_ref'} and
            type(value['schema_version']) is int and value['schema_version'] == 1 and
            value['scope'] == 'pear_active_development_selection', 'active_selection_shape')
    ref, record = prepared(value['prepared_ref']['path'])
    require(ref == value['prepared_ref'] and Path(record['specification']['state_root']) == root,
            'active_selection_binding')
    return ref['path']


def diagnose(path, request_path, *, game=False):
    ref, record = prepared(path)
    spec_ref = record['specification_ref']
    inspect(spec_ref, kind='game' if game else 'fixture')
    value, _, descriptor = selection(spec_ref)
    request_ref = fact(request_path)
    request = read_ref(request_ref)
    wanted = value['game_descriptor_ref'] if game else value['fixture_descriptor_ref']
    require(wanted is not None and request.get('descriptor_ref') == wanted, 'diagnostic_descriptor_mismatch')
    if game:
        from tools.development.game.context import GameContext
        from tools.development.game.feedback import bind_factory
        from pear_runtime.fixtures.game_operation import execute
        if os.getpgrp() != os.getpid():
            os.setpgid(0, 0)
        return execute(Path(request_ref['path']), context=GameContext(wanted), play_factory=bind_factory)
    # Exec the canonical worker. It owns interruption, lease, current authority,
    # final evidence and cleanup; no second process supervisor is introduced.
    from pear_runtime.fixtures.driver import review
    review(Path(request_ref['path']))
    root = state_root(value)
    dispatch = write_new(root / 'transactions' / (uuid.uuid4().hex + '.fixture-dispatch.json'),
        dict(scope='pear_fixture_dispatch', prepared_ref=ref, request_ref=request_ref,
             selector_ref=fact(__file__), execution_authorized_by_this_record=False))
    manifest = read_ref(descriptor['producer_manifest_ref'])
    environment = {key: val for key, val in os.environ.items()
                   if not key.startswith(('PYTHON', 'WINE', 'FEX', 'DYLD_'))}
    environment['PYTHONPATH'] = os.pathsep.join(manifest['roots'][k] for k in ('runtime', 'fex')
                                              if k in manifest['roots'])
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    environment['PEAR_DEVELOPMENT_DISPATCH'] = dispatch['path']
    interpreter = str(Path(sys.executable).resolve(strict=True))
    require(fact(request_path) == request_ref and fact(path) == ref, 'diagnostic_binding_changed')
    os.chdir(value['runtime_checkout']['path'])
    os.execve(interpreter, [interpreter, '-B', '-m', 'pear_runtime.fixtures', 'execute',
                           '--request', request_ref['path']], environment)
    raise Refusal('diagnostic_exec_returned')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare'); p.add_argument('--spec', type=Path, required=True)
    p = sub.add_parser('select'); p.add_argument('--prepared', type=Path, required=True)
    for command in ('inspect', 'diagnose-fixture', 'diagnose-game'):
        p = sub.add_parser(command)
        group = p.add_mutually_exclusive_group(required=True)
        group.add_argument('--prepared', type=Path)
        group.add_argument('--state', type=Path)
        if command == 'inspect':
            p.add_argument('--kind', choices=('auto', 'fixture', 'game'), default='auto')
        if command.startswith('diagnose-'):
            p.add_argument('--request', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            result = dict(prepared_ref=prepare(args.spec), selected=False)
        elif args.command == 'select':
            result = select(args.prepared)
        else:
            path = args.prepared or active_path(args.state)
            if args.command == 'inspect':
                _, record = prepared(path)
                result = inspect(record['specification_ref'], kind=args.kind)
            else:
                result = diagnose(path, args.request, game=args.command == 'diagnose-game')
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print(json.dumps(dict(status='refused', code=getattr(error, 'code', type(error).__name__))), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
