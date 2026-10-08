#!/usr/bin/env python3
"""Assess immutable compiled FEX artifacts without changing a failed build.

This offline reader admits one reviewed policy transition, retains the original
failure, and writes a separate assessment. It never compiles, links, loads or
initializes a module. Runtime and aggregate metadata qualification stay closed.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import re
import sys

if __package__:
    from . import memory_fex_check as reader
    from .common import Error, REPO, need, operation_output, write_json, encoded
else:
    script_directory = Path(__file__).resolve().parent
    sys.path[:] = [entry for entry in sys.path if Path(entry or os.getcwd()).resolve() != script_directory]
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.fex import memory_fex_check as reader
    from tools.fex.common import Error, REPO, need, operation_output, write_json, encoded

OLD_READER_SHA = '59f5a7de0239c7ab927ec763de36e9ed87c07c13b56d88ac53884bf794d6e183'
REVIEWED_READER_SHA = '3cd37aa153f5629a35a7173494a9952620e2a69433a5296ac1eb3d37919863cf'
READER_PATH = 'tools/fex/memory_fex_check.py'
ASSESSOR_PATH = 'tools/fex/memory_fex_assess.py'
SCOPE = 'immutable_compiled_artifacts_no_initialization'
POLICY_SCOPE = 'exact_unchanged_upstream_allocator_and_SourceLifecycle_AttachAllocatedThread'
ASSESSMENT_MAX_BYTES = 8 * 1024**2
ASSESSMENT_MAX_NODES = 500000
FAILURE_KEYS = ('schema_version', 'record_kind', 'scope', 'bindings', 'producer_sha256',
                'input_snapshots', 'materialized_source', 'wire', 'source_interfaces',
                'commands', 'resources', 'modules_built_not_loaded', 'qualification',
                'passed', 'phase', 'primary_error', *reader.FALSE_FLAGS)
ASSESSMENT_KEYS = ('schema_version', 'record_kind', 'scope', 'passed', 'historical_builder_passed',
                   'historical_failure_preserved', 'compiler_invoked', 'new_native_execution',
                   'qualification', 'reader_policy', 'assessment', 'input_snapshots',
                   'producer_sha256', *reader.FALSE_FLAGS)


def assessment_record_bytes(root):
    """Decode only our successful assessment with its explicit bounded budget."""
    raw, _ = reader.regular_bytes(root, 'assessment.json', ASSESSMENT_MAX_BYTES)
    return reader.decode_json(raw, max_bytes=ASSESSMENT_MAX_BYTES,
                              max_nodes=ASSESSMENT_MAX_NODES), raw


def write_assessment(root, value):
    """Preflight the complete successful record, then write those exact bytes."""
    raw = encoded(value)
    reader.decode_json(raw, max_bytes=ASSESSMENT_MAX_BYTES,
                       max_nodes=ASSESSMENT_MAX_NODES)
    path = Path(root) / 'assessment.json'
    with path.open('xb') as stream:
        stream.write(raw)
    path.chmod(0o600)


def canonical_root(value):
    text = os.fspath(value)
    need(type(text) is str and text.startswith('/') and not text.startswith('//'),
         'fex_assessment_absolute_root')
    reader.relative(text[1:])
    root = Path(text)
    need(str(root) == text and root.resolve(strict=True) == root and root.is_dir(),
         'fex_assessment_root_alias')
    return root


def reference(path):
    path = Path(path)
    need(path.is_absolute() and path.resolve(strict=True) == path, 'fex_assessment_reference_alias')
    raw, mode = reader.regular_bytes(Path('/'), str(path)[1:], 128 * 1024**2)
    return {'path': str(path), 'sha256': reader.H(raw), 'size_bytes': len(raw), 'mode': mode}


def source_identity(repo):
    repo = canonical_root(repo)
    need(Path(__file__).resolve(strict=True) == repo / ASSESSOR_PATH and
         Path(reader.__file__).resolve(strict=True) == repo / READER_PATH,
         'fex_assessment_supplied_repository')
    need(reference(repo / READER_PATH)['sha256'] == REVIEWED_READER_SHA,
         'fex_assessment_unreviewed_reader')
    return repo


def failure_gate(value, raw, expected_sha256):
    need(type(expected_sha256) is str and re.fullmatch('[0-9a-f]{64}', expected_sha256) and
         reader.H(raw) == expected_sha256, 'fex_assessment_failure_changed')
    reader.exact(value, FAILURE_KEYS, 'fex_assessment_failure_fields')
    need(type(value['schema_version']) is int and value['schema_version'] == 1 and
         value['record_kind'] == 'fex_memory_modules_build' and value['scope'] == 'fex_component' and
         value['passed'] is False and value['modules_built_not_loaded'] is False and
         value['phase'] == 'artifact_replay', 'fex_assessment_failure_scope')
    reader.qualification_gate(value)
    reader.exact(value['primary_error'], ('code', 'exception_type'), 'fex_assessment_primary_fields')
    need(value['primary_error'] == {'code': 'fex_memory_owner_macro', 'exception_type': 'Error'},
         'fex_assessment_unreviewed_failure')
    need(type(value['commands']) is list and len(value['commands']) == 9,
         'fex_assessment_nine_commands_required')
    # command_gate performs full recipe, supervision and log checks later.
    need(all(type(row) is dict and type(row.get('exit_code')) is int and row['exit_code'] == 0 and
             row.get('status') == 'completed' for row in value['commands']),
         'fex_assessment_unperformed_or_failed_command')
    return value


def producer_transition(value, repo):
    historical = value['producer_sha256']
    reader.exact(historical, reader.LOCAL_PRODUCERS, 'fex_assessment_historical_producers')
    current = {path: reference(repo / path)['sha256'] for path in reader.LOCAL_PRODUCERS}
    need(historical[READER_PATH] == OLD_READER_SHA and current[READER_PATH] == REVIEWED_READER_SHA and
         all(historical[path] == current[path] for path in reader.LOCAL_PRODUCERS if path != READER_PATH),
         'fex_assessment_unreviewed_producer_transition')
    return {'predecessor_sha256': OLD_READER_SHA, 'current_sha256': REVIEWED_READER_SHA,
            'scope': POLICY_SCOPE, 'other_historical_producers_unchanged': True}


def historical_snapshots(root, rows, paths, repo):
    """Replay original copies; only the reviewed reader change may differ now."""
    need(type(rows) is list and len(rows) == len(paths) and 0 < len(rows) <= 512,
         'fex_assessment_historical_snapshot_inventory')
    total = 0
    changed = 0
    for index, (row, path) in enumerate(zip(rows, paths)):
        reader.exact(row, ('source', 'copy', 'sha256', 'size_bytes'), 'fex_assessment_snapshot_fields')
        need(row['source'] == str(path) and row['copy'] == f'inputs/{index:04d}.bin' and
             type(row['size_bytes']) is int and 0 <= row['size_bytes'] <= 8 * 1024**2,
             'fex_assessment_snapshot_path')
        saved, mode = reader.regular_bytes(root, row['copy'], 8 * 1024**2)
        current, _ = reader.regular_bytes(path.parent, path.name, 8 * 1024**2)
        total += len(saved)
        need(mode == 0o600 and reader.H(saved) == row['sha256'] and len(saved) == row['size_bytes'] and
             total <= 128 * 1024**2, 'fex_assessment_historical_snapshot_changed')
        if path == repo / READER_PATH:
            need(reader.H(saved) == OLD_READER_SHA and reader.H(current) == REVIEWED_READER_SHA,
                 'fex_assessment_snapshot_reader_transition')
            changed += 1
        else:
            need(saved == current, 'fex_assessment_unreviewed_snapshot_change')
    need(changed == 1 and {p.name for p in (root / 'inputs').iterdir()} ==
         {f'{i:04d}.bin' for i in range(len(paths))}, 'fex_assessment_snapshot_set')
    return {'count': len(paths), 'reviewed_reader_transition_count': changed,
            'all_other_current_inputs_equal_original_copies': True}


def evaluate(build_root, expected_failure_sha256, *, repo=REPO):
    """Read existing evidence only. No constructor or subprocess route is used."""
    repo = source_identity(repo)
    root = canonical_root(operation_output(build_root, repo_root=repo, require_empty=False, create=False))
    need(not (root / 'build.json').exists(), 'fex_assessment_historical_success_record_present')
    value, raw = reader.record_bytes(root, 'failure.json')
    failure_gate(value, raw, expected_failure_sha256)
    policy = producer_transition(value, repo)
    bindings = value['bindings']
    reader.exact(bindings, ('baseline', 'projection', 'derivatives', 'wine_build'), 'fex_assessment_bindings')
    reader.exact(bindings['baseline'], ('root', 'sha256'), 'fex_assessment_baseline_fields')
    reader.exact(bindings['derivatives'], ('root', 'sha256'), 'fex_assessment_derivative_fields')
    baseline = canonical_root(bindings['baseline']['root'])
    derivatives = canonical_root(bindings['derivatives']['root'])
    projection = canonical_root(bindings['projection']['root'])
    wine_root = canonical_root(bindings['wine_build']['root'])
    old = reader.original.verify_build(baseline)
    need(reference(baseline / 'build.json')['sha256'] == bindings['baseline']['sha256'] == reader.BASE_BUILD_SHA,
         'fex_assessment_baseline_changed')
    reader.exact(bindings['projection'], ('root', 'control_sha256', 'source_manifest_sha256', 'source_helper'),
                 'fex_assessment_projection_fields')
    helper = reader.bound_source_helper(bindings['projection']['source_helper'])
    derived, projection_ref = reader.projection_gate(projection, baseline, derivatives, source_helper=helper,
                                expected_control_sha256=bindings['projection']['control_sha256'])
    need(projection_ref == bindings['projection'] and bindings['derivatives']['sha256'] == reader.GRAPH_SHA,
         'fex_assessment_projection_changed')
    wire, wire_ref = reader.wire_gate(wine_root)
    need(wire_ref == bindings['wine_build'], 'fex_assessment_wine_changed')
    manifest, manifest_raw = reader.record_bytes(root, 'materialized-source.json')
    need(value['materialized_source'] == {'path': 'materialized-source.json', 'sha256': reader.H(manifest_raw)} and
         manifest == {'schema_version': 1, 'record_kind': 'fex_memory_materialized_source',
                      'scope': 'fex_component', 'files': derived['source_files']} and
         reader.source_inventory(root / 'source') == derived['source_files'], 'fex_assessment_source_changed')
    need(reader.source_inventory(root / 'wire') == [{'path': 'wine/pear_fex_memory.h', 'sha256': reader.WIRE_SHA,
              'size_bytes': len(wire), 'mode': 0o644}] and value['wire'] ==
         {'path': 'wire/wine/pear_fex_memory.h', 'sha256': reader.WIRE_SHA, 'size_bytes': len(wire)},
         'fex_assessment_wire_changed')
    interfaces = reader.prepare.source_interfaces(root / 'source')
    need(interfaces == value['source_interfaces'] and len(interfaces['services']) == 8 and
         [len(m['exports']) for m in interfaces['modules']] == [20, 23], 'fex_assessment_source_interface_changed')
    lock = reader.load_json(old['bindings']['toolchain']['path'])
    config = reader.original.validate_config(reader.load_json(old['bindings']['config']['path']),
                                              old['bindings']['inputs']['sha256'])
    features = reader.original.host_metadata(Path(old['bindings']['host_metadata']['path']))
    expected = reader.recipe(root, old['bindings']['tools']['path'], lock, features, config, old['cross'])
    reader.command_gate(root, value['commands'], expected, reader.original.complete_environment(lock, old['cross']))
    paths = reader.snapshot_sources(repo, baseline, projection, derivatives, wine_root, old, source_helper=helper)
    snapshots = historical_snapshots(root, value['input_snapshots'], paths, repo)
    artifacts, proofs = reader.inspect_modules(root, old['cross'], features, config, baseline)
    need(len(artifacts) == 32, 'fex_assessment_artifact_count')
    current_paths = set(paths) | {repo / ASSESSOR_PATH, root / 'failure.json',
                                 root / 'materialized-source.json', root / 'wire/wine/pear_fex_memory.h'}
    for row in value['commands']:
        current_paths.add(root / f"logs/{row['id']}/command.json")
        for log in row['logs'].values(): current_paths.add(root / log['path'])
    current_paths = sorted(current_paths, key=str)
    need(len(current_paths) <= 512, 'fex_assessment_current_input_limit')
    failure_ref = reference(root / 'failure.json')
    need(failure_ref['sha256'] == expected_failure_sha256, 'fex_assessment_failure_changed_during_inspection')
    result = {'historical_failure': failure_ref,
              'historical_primary_error': value['primary_error'], 'historical_phase': value['phase'],
              'reader_policy': policy, 'bindings': bindings, 'original_command_count': len(value['commands']),
              'original_commands': value['commands'], 'historical_snapshots': snapshots,
              'source_interfaces': interfaces, 'artifact_count': len(artifacts),
              'artifacts': artifacts, 'module_proofs': proofs,
              'original_payload_inventory': reader.output_inventory(root),
              'current_input_refs': [reference(path) for path in current_paths]}
    need(len(encoded(result)) <= 8 * 1024**2, 'fex_assessment_record_limit')
    return result, current_paths


def current_producers(repo):
    return {path: reference(Path(repo) / path)['sha256'] for path in (*reader.LOCAL_PRODUCERS, ASSESSOR_PATH)}


def snapshot(root, paths):
    (root / 'inputs').mkdir(mode=0o700)
    rows = []
    total = 0
    for index, path in enumerate(paths):
        raw, _ = reader.regular_bytes(path.parent, path.name, 8 * 1024**2)
        total += len(raw)
        need(total <= 128 * 1024**2, 'fex_assessment_snapshot_total')
        name = f'inputs/{index:04d}.bin'
        with (root / name).open('xb') as stream: stream.write(raw)
        (root / name).chmod(0o600)
        rows.append({'source': str(path), 'copy': name, 'sha256': reader.H(raw), 'size_bytes': len(raw)})
    return rows


def assessment_gate(value):
    reader.exact(value, ASSESSMENT_KEYS, 'fex_assessment_record_fields')
    need(type(value['schema_version']) is int and value['schema_version'] == 1 and
         value['record_kind'] == 'fex_memory_artifact_assessment' and value['scope'] == SCOPE and
         value['passed'] is True and value['historical_builder_passed'] is False and
         value['historical_failure_preserved'] is True and value['compiler_invoked'] is False and
         value['new_native_execution'] is False, 'fex_assessment_record_scope')
    reader.qualification_gate(value)


def preserve_failure(root, value, exc):
    value.update(passed=False, primary_error={'code': getattr(exc, 'code', type(exc).__name__),
                                              'exception_type': type(exc).__name__})
    if isinstance(exc, OSError): value['primary_error']['native_error'] = {'domain': 'errno', 'code': exc.errno}
    try: write_json(root / 'failed-assessment.json', value)
    except BaseException as storage_error:
        try: exc.assessment_record_error = {'exception_type': type(storage_error).__name__,
                                            'code': getattr(storage_error, 'code', type(storage_error).__name__)}
        except (AttributeError, TypeError): pass


def assess(build_root, expected_failure_sha256, output, *, repo=REPO):
    repo = source_identity(repo)
    source_root = canonical_root(operation_output(build_root, repo_root=repo, require_empty=False, create=False))
    root = operation_output(output, repo_root=repo, require_empty=True)
    need(root != source_root and root.resolve(strict=True) == root, 'fex_assessment_output_alias')
    value = {'schema_version': 1, 'record_kind': 'fex_memory_artifact_assessment', 'scope': SCOPE,
             'passed': False, 'historical_builder_passed': False, 'historical_failure_preserved': True,
             'compiler_invoked': False, 'new_native_execution': False,
             'qualification': dict(reader.QUALIFICATION), **dict.fromkeys(reader.FALSE_FLAGS, False)}
    try:
        before, paths = evaluate(source_root, expected_failure_sha256, repo=repo)
        value['reader_policy'] = before['reader_policy']
        value['producer_sha256'] = current_producers(repo)
        value['input_snapshots'] = snapshot(root, paths)
        after, after_paths = evaluate(source_root, expected_failure_sha256, repo=repo)
        need(before == after and paths == after_paths, 'fex_assessment_inputs_changed_during_assessment')
        reader.verify_snapshots(root, value['input_snapshots'], paths)
        need(value['producer_sha256'] == current_producers(repo), 'fex_assessment_producer_changed')
        value.update(assessment=after, passed=True)
        assessment_gate(value)
        write_assessment(root, value)
        return value
    except BaseException as exc:
        preserve_failure(root, value, exc)
        raise


def verify_assessment(root, *, repo=REPO):
    repo = source_identity(repo)
    root = canonical_root(operation_output(root, repo_root=repo, require_empty=False, create=False))
    need(not (root / 'failed-assessment.json').exists(), 'fex_assessment_failed_record')
    value, _ = assessment_record_bytes(root)
    assessment_gate(value)
    need(value['producer_sha256'] == current_producers(repo), 'fex_assessment_producer_changed')
    failure = value['assessment']['historical_failure']
    reader.exact(failure, ('path', 'sha256', 'size_bytes', 'mode'), 'fex_assessment_failure_reference_fields')
    need(type(failure['path']) is str and Path(failure['path']).name == 'failure.json',
         'fex_assessment_failure_reference_path')
    observed, paths = evaluate(Path(failure['path']).parent, failure['sha256'], repo=repo)
    need(observed == value['assessment'] and value['reader_policy'] == observed['reader_policy'],
         'fex_assessment_replay_changed')
    reader.verify_snapshots(root, value['input_snapshots'], paths)
    need({p.name for p in root.iterdir()} == {'assessment.json', 'inputs'}, 'fex_assessment_extra_output')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('assess')
    create.add_argument('--build-root', required=True)
    create.add_argument('--failure-sha256', required=True)
    create.add_argument('--output', required=True)
    verify = commands.add_parser('verify')
    verify.add_argument('--root', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'assess': assess(args.build_root, args.failure_sha256, args.output)
        else: verify_assessment(args.root)
        print('PASS: separate immutable artifact assessment; original builder remains failed; initialization unperformed')
        return 0
    except (Error, OSError, ValueError, KeyError, IndexError, TypeError, UnicodeError) as exc:
        print('FAIL: ' + getattr(exc, 'code', type(exc).__name__), file=sys.stderr)
        return 1


if __name__ == '__main__': raise SystemExit(main())
