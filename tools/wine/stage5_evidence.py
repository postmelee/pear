"""Export finite Stage 5 observations after current private gate validation.

This reader never launches or signs Wine. It reuses the existing exporter's
bounded record, scalar, assembly and relocation selectors. Stage 5 suite and
runtime identities are checked directly; older assessments are not relabeled.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

import evidence
import stage4_evidence
import window_evidence
from stage4_evidence import exact, role, arena_summary, dynamic_summary, thread_summary
from common import Error, REPO, encoded, need, relative, sha256
from evidence import _digest, _public_integer, bound_record, _stage3_assembly, _stage3_relocations

SUITE = 'mac-driver'
SCOPE = 'development_windows_mac_driver_fixtures'
SOURCES = {**stage4_evidence.SOURCES, 'stage5_exporter': 'tools/wine/stage5_evidence.py',
    'window_validator': 'tools/wine/window_evidence.py', 'stage5_cases': 'tests/wine/cases-stage5.json',
    'window_fixture': 'tests/wine/fixtures/window_pe.c', 'window_protocol': 'tests/wine/fixtures/stage5_protocol.h',
    'window_control_fixture': 'tests/wine/fixtures/window_control_pe.c',
    'window_native_fixture': 'tests/wine/fixtures/window_native.m',
    'window_census_header': 'tests/wine/fixtures/stage5_census.h'}
SOURCE_LABELS = {name: label for label, name in SOURCES.items()}
COMMANDS = stage4_evidence.COMMANDS | {'fixture-window-arm64', 'disassemble-window'}
UNQUALIFIED = list(dict.fromkeys([*stage4_evidence.UNQUALIFIED, *window_evidence.UNQUALIFIED]))


def task_root(path):
    """Reuse the owned-path policy, including every ancestor symlink check."""
    need(REPO == evidence.REPO, 'export_repository_identity')
    return evidence._failed_root(path)




def source_hashes():
    return {label: sha256(REPO / name) for label, name in SOURCES.items()}


def producer_hashes(value, expected_names, sources, basenames=False):
    need(isinstance(value, dict) and set(value) == set(expected_names), 'export_producer_coverage')
    result = {}
    for name in expected_names:
        path = 'tools/wine/' + name if basenames else name
        need(path in SOURCE_LABELS, 'export_producer_not_allowlisted')
        label = SOURCE_LABELS[path]
        need(_digest(value[name]) == sources[label], 'export_producer_changed')
        result[label] = value[name]
    return result


def commands(built):
    rows, patches = built.get('commands'), built.get('patches')
    need(isinstance(patches, list) and 0 < len(patches) <= 64, 'export_patch_coverage')
    names = COMMANDS | {'patch-' + str(i) for i in range(1, len(patches) + 1)}
    need(isinstance(rows, list) and len(rows) == len(names) and
         {row.get('id') for row in rows} == names, 'export_command_coverage')
    public = []
    for row in rows:
        need(type(row.get('exit_code')) is int and row['exit_code'] == 0 and
             row.get('timed_out') is False and row.get('output_limit') is False, 'export_command_failure')
        public.append({'id': row['id'], 'exit_code': 0, 'timed_out': False, 'output_limit': False})
    return public


def signing_summary(signed, count):
    from signing import APP_ID, TEAM_ID, CROSS_KEYS
    need(signed.get('authorization_scope') == SCOPE and signed.get('code_publication_policy') == 'page-wx' and
         signed.get('distribution_qualified') is False and signed.get('runtime_qualified') is False,
         'export_stage5_signed_scope')
    checks = signed.get('profile_checks', {})
    need(isinstance(checks, dict) and all(checks.get(key) is True for key in evidence.PROFILE_CHECKS),
         'export_signing_checks')
    roles = {'api-launch-helper', 'bootstrap-helper', 'native-helper', 'native-library',
             'sentinel', 'wine-loader', 'wine-server', 'wine-wrapper'}
    rows = signed.get('native_images')
    need(isinstance(rows, list) and len(rows) == count, 'export_signature_coverage')
    counts = {role: 0 for role in sorted(roles)}
    for row in rows:
        role = row.get('role')
        need(role in roles, 'export_native_role')
        counts[role] += 1
        signature = row.get('signature', {})
        need(all(signature.get(key) is True for key in ('hardened_runtime', 'same_team', 'strict_verification')) and
             signature.get('ad_hoc') is False and signature.get('category') == 'apple_development',
             'export_signature_checks')
        keys = signature.get('claim_keys')
        need(isinstance(keys, list) and all(type(key) is str for key in keys) and len(set(keys)) == len(keys),
             'export_claim_keys')
        page = signature.get('code_directory_page_size')
        need(type(page) is int, 'export_signature_page')
        if role == 'wine-loader':
            jit = 'com.apple.security.cs.allow-jit'
            need({APP_ID, TEAM_ID, jit} <= set(keys) and len(set(keys) & set(CROSS_KEYS)) == 1 and
                 set(keys) <= {APP_ID, TEAM_ID, jit, *CROSS_KEYS} and page == 4096, 'export_loader_claims')
        else:
            need(not keys and page in (4096, 16384), 'export_native_claims')
    need(all(counts[role] == 1 for role in ('api-launch-helper', 'bootstrap-helper', 'sentinel',
                                         'wine-loader', 'wine-server', 'wine-wrapper')), 'export_native_roles')
    return {'execution_scope': SCOPE, 'current_validation_passed': True,
            'native_images_signed': count, 'native_role_counts': counts, 'hardened_runtime': True,
            'library_validation': 'enabled', 'allow_jit_scope': 'wine-loader-only',
            'loader_signature_page_bytes': 4096, 'ordinary_user_distribution_qualified': False}










def window_summary(value):
    need(isinstance(value, dict), 'export_window_summary')
    expected = {'cycles': 20, 'native_main_thread_verified': True, 'wine_callback_thread_verified': True,
        'cocoa_close_events': 20, 'application_messages': 20, 'callback_reentries': 20,
        'destroyed_windows': 20, 'deallocated_windows': 20,
        'final_queue_idle_verified': True, 'observed_late_callbacks': 0,
        'active_windows_at_completion': 0, 'pending_owned_events_at_completion': 0,
        'loaded_driver_verified': True, 'loaded_appkit_verified': True, 'loaded_corefoundation_verified': True,
        'observation_scope': 'twenty_owned_lifetimes_through_final_barrier',
        'unqualified': list(window_evidence.UNQUALIFIED)}
    exact({key: value.get(key) for key in expected}, expected, 'export_window_facts')
    barriers = _public_integer(value.get('main_thread_barriers'), 2000)
    drains = _public_integer(value.get('event_drains'), 2000)
    turns = _public_integer(value.get('appkit_event_turns'), 2000)
    parts = _public_integer(value.get('native_anchor_parts'), 16527)
    loaded = _public_integer(value.get('native_image_snapshot_count'), 2048)
    need(20 <= turns <= barriers == drains <= 2000 and parts == 527 + 4 * barriers + 4 * turns and loaded >= 3,
         'export_window_count_binding')
    return {**expected, **{key: _digest(value.get(key)) for key in
                ('fixture_sha256', 'driver_pe_sha256', 'native_driver_sha256')},
            'appkit_event_turns': turns, 'main_thread_barriers': barriers, 'event_drains': drains, 'native_anchor_parts': parts,
            'native_image_snapshot_count': loaded}


def run_summaries(api, bootstrap):
    from api_runner import ENVIRONMENT_POLICY, expected_fixture_rows, validate_environment_policy
    need(api.get('record_kind') == 'wine_mac_driver_assessment' and api.get('suite') == SUITE and
         api.get('passed') is True and api.get('pe_executed') is True and api.get('runtime_qualified') is False and
         api.get('game_qualified') is False and api.get('code_publication_policy') == 'page-wx' and
         api.get('evidence_scope') == 'instrumented-arm64-mac-driver-with-constrained-owned-descendants',
         'export_stage5_assessment_scope')
    exact(api.get('case_count'), 4, 'export_case_count')
    validate_environment_policy(api.get('environment_policy'))
    need([row.get('id') for row in api['cases']] == ['api', 'abi', 'threads', 'window'], 'export_case_order')
    cases = []
    for row in api['cases']:
        name = row['id']
        validate_environment_policy(row.get('environment_policy'))
        need(row.get('code_publication_policy') == 'page-wx' and all(row.get(key) is True for key in
             ('passed', 'cleanup_complete', 'sentinel_survived')), 'export_case_gate')
        expected = expected_fixture_rows(name)
        exact(row.get('fixture_results'), expected, 'export_fixture_results')
        arena = arena_summary(row)
        dynamic = dynamic_summary(row.get('dynamic_observations'), arena, name == 'threads')
        native = _public_integer(row.get('native_processes'), 66)
        need(native >= len(arena) + 2, 'export_native_process_count')
        case = {'id': name, 'case_sha256': _digest(row.get('case_sha256')), 'passed': True,
                'native_processes': native, 'pe_processes': len(arena), 'code_publication_policy': 'page-wx',
                'environment_policy': dict(ENVIRONMENT_POLICY), 'arena_observations': arena,
                'dynamic_observations': dynamic, 'fixture_results': expected,
                'cleanup_complete': True, 'sentinel_survived': True}
        if name == 'abi':
            case['relocation_observations'] = _stage3_relocations(row.get('relocation_observations'))
        else:
            need(row.get('relocation_observations') is None, 'export_relocation_scope')
        if name == 'threads':
            case['thread_memory_exception_observations'] = thread_summary(row.get('thread_memory_exception_observations'), dynamic)
        else:
            need(row.get('thread_memory_exception_observations') is None, 'export_thread_scope')
        if name == 'window':
            case['window_observations'] = window_summary(row.get('window_observations'))
        else:
            need(row.get('window_observations') is None, 'export_window_scope')
        cases.append(case)
    controls = api.get('controls')
    need(isinstance(controls, list) and [item.get('role') for item in controls] == ['x64_control', 'i386_control'],
         'export_negative_controls')
    selected = []
    for item, machine in zip(controls, ('x86_64', 'i386')):
        need(item.get('machine') == machine and item.get('executed') is False and item.get('accepted') is False and
             item.get('reason') == 'translator-not-qualified-for-target', 'export_control_scope')
        selected.append({'role': item['role'], 'machine': machine, 'sha256': _digest(item.get('sha256')),
                         'executed': False, 'accepted': False, 'reason': 'translator-not-qualified-for-target'})
    need(bootstrap.get('record_kind') == 'wine_bootstrap_assessment' and bootstrap.get('suite') == 'bootstrap' and
         bootstrap.get('evidence_scope') == 'retained-local-native-bootstrap-consistency' and
         bootstrap.get('passed') is True and bootstrap.get('pe_executed') is False and
         bootstrap.get('runtime_qualified') is False, 'export_bootstrap_assessment_scope')
    exact(bootstrap.get('case_count'), 3, 'export_bootstrap_count')
    need([row.get('id') for row in bootstrap['cases']] == list(evidence.FAILED_CASES), 'export_bootstrap_cases')
    regressions = []
    for row, expected, outcome in zip(bootstrap['cases'], ('bootstrap_stop', 'timeout', 'server_refused'),
                                     ('exited', 'timeout', 'exited')):
        fields = {'expected': expected, 'outcome': outcome, 'passed': True, 'native_process_count': 3,
                  'reexecution_count': 1, 'actual_handshake': expected != 'server_refused',
                  'cleanup_complete': True, 'sentinel_survived': True}
        exact({key: row.get(key) for key in fields}, fields, 'export_bootstrap_case')
        regressions.append({'id': row['id'], 'case_sha256': _digest(row.get('case_sha256')), **fields})
    return {'mac_driver': {'run_sha256': _digest(api.get('run_sha256')), 'case_count': 4,
        'passed': True, 'cases': cases, 'controls': selected},
        'bootstrap': {'run_sha256': _digest(bootstrap.get('run_sha256')), 'case_count': 3,
                      'passed': True, 'pe_executed': False, 'cases': regressions}}


def export(build_root, runs_root, bootstrap_root):
    from build import artifact_inventory, verify_build, PRODUCERS
    from api_runner import validate_runs as validate_api_runs, producers
    from run_fixtures import validate_runs, producer_hashes as bootstrap_producers
    from signing import validate_prepared
    from abi_review import inspect_build
    from toolchain import MACH_ARM64
    root, runs_root, bootstrap_root = [task_root(path) for path in (build_root, runs_root, bootstrap_root)]
    need(len({root, runs_root, bootstrap_root}) == 3, 'export_input_roots')
    need(all(not (path / 'diagnostic-adapter.json').exists() for path in (runs_root, bootstrap_root)), 'diagnostic_only_run')
    sources = source_hashes()
    build_digest = sha256(root / 'build.json')
    built = verify_build(root)
    need(bound_record(root / 'build.json', build_digest, 'wine_build') == built and
         built.get('fixture_suite') == SUITE and built.get('variant') == 'arm64' and
         built.get('code_publication_policy') == 'page-wx' and built.get('passed') is True, 'export_build_scope')
    api, bootstrap = validate_api_runs(runs_root, SUITE), validate_runs(bootstrap_root, 'bootstrap')
    api_record = bound_record(runs_root / 'run.json', _digest(api.get('run_sha256')), 'wine_api_run')
    bootstrap_record = bound_record(bootstrap_root / 'run.json', _digest(bootstrap.get('run_sha256')), 'wine_bootstrap_run')
    need(api_record.get('suite') == SUITE and bootstrap_record.get('suite') == 'bootstrap', 'export_record_suite')
    signed_digest = _digest(api.get('signed_sha256'))
    need(bootstrap.get('signed_sha256') == api_record.get('signed_sha256') ==
         bootstrap_record.get('signed_sha256') == signed_digest, 'export_mixed_signed_runtime')
    runtime = task_root(REPO.joinpath(*relative(api_record.get('runtime_path'))))
    need(task_root(REPO.joinpath(*relative(bootstrap_record.get('runtime_path')))) == runtime,
         'export_mixed_runtime_roots')
    signed = validate_prepared(runtime)
    need(bound_record(runtime / 'signed.json', signed_digest, 'wine_signed_runtime') == signed, 'export_signed_changed')
    need(signed.get('build_ref', {}).get('sha256') == build_digest and
         task_root(signed['build_ref']['path']) == root / 'build.json', 'export_tested_build_mismatch')
    review_digest = sha256(root / 'abi-review.json')
    review = inspect_build(root)
    need(bound_record(root / 'abi-review.json', review_digest, 'wine_abi_assembly_review') == review, 'export_review_changed')
    assembly = _stage3_assembly(review, build_digest)
    artifacts = artifact_inventory(built, root)
    native = [row for row in artifacts['files'] if row.get('kind') == 'macho']
    pe_count = sum(row.get('kind') == 'pe' for row in artifacts['files'])
    need(native and all(row.get('architectures') == [MACH_ARM64] for row in native), 'export_host_architecture')
    exact(built.get('native_artifact_count'), len(native), 'export_native_artifact_count')
    exact(built.get('pe_artifact_count'), pe_count, 'export_pe_artifact_count')
    producer_records = {
        'build': producer_hashes(built.get('producer_sha256'), PRODUCERS, sources, True),
        'signer': producer_hashes(signed.get('producer_sha256'), ('signing.py', 'common.py'), sources, True),
        'assembly': producer_hashes(review.get('producer_sha256'), ('abi_review.py', 'common.py', 'toolchain.py'), sources, True),
        'stage5_run': producer_hashes(api_record.get('producer_sha256'), producers(SUITE), sources),
        'bootstrap_run': producer_hashes(bootstrap_record.get('producer_sha256'), bootstrap_producers(), sources)}
    exact(api.get('producer_sha256'), api_record['producer_sha256'], 'export_api_producer_binding')
    exact(bootstrap.get('producer_sha256'), bootstrap_record['producer_sha256'], 'export_bootstrap_producer_binding')
    sdk = built['sdk']
    need(isinstance(sdk.get('version'), str) and re.fullmatch(r'[0-9]+(?:\.[0-9]+){1,3}', sdk['version']) and
         sdk.get('canonical_name') == 'macosx' + sdk['version'], 'export_sdk_shape')
    public = {'schema_version': 1, 'record_kind': 'wine_stage5_observations',
        'scope': 'instrumented_arm64_windows_mac_driver_fixtures',
        'build': {'build_sha256': build_digest, 'variant': 'arm64', 'fixture_suite': SUITE,
            'input_record_sha256': {key: _digest(built.get(key)) for key in
                ('inputs_sha256', 'config_sha256', 'toolchain_lock_sha256', 'source_prepared_sha256',
                 'tool_prepared_sha256', 'patch_series_sha256')},
            'patched_source_manifest_sha256': _digest(built.get('source_manifest', {}).get('sha256')),
            'code_publication_policy': 'page-wx', 'native_artifact_count': len(native), 'pe_artifact_count': pe_count,
            'metadata_container_count': sum(row.get('kind') == 'pe_metadata' for row in artifacts['files']),
            'ordered_patch_sha256': [_digest(row.get('sha256')) for row in built['patches']],
            'commands': commands(built)},
        'signed_sha256': signed_digest, 'assembly_review_sha256': review_digest, 'assembly_review': assembly,
        'run_assessments': run_summaries(api, bootstrap), 'signing_validation': signing_summary(signed, len(native)),
        'host_observation': {'architecture': 'arm64', 'translated': False,
            'scope': 'validated_instrumented_process_and_loaded_image_snapshots', 'complete_load_timeline': False},
        'sdk': {'version': sdk['version'], 'canonical_name': sdk['canonical_name'], 'settings_sha256': _digest(sdk.get('settings_sha256'))},
        'reviewed_source_hashes': sources, 'producer_hashes': producer_records,
        'pe_execution': True, 'guest_x18_execution': True, 'translator_execution': False,
        'game_execution': False, 'runtime_qualified': False, 'distribution_qualified': False,
        'unqualified': list(UNQUALIFIED),
        'limits': ['Same-host development execution of instrumented ARM64 fixtures only.',
            'x64 and i386 controls were refused before execution; no guest translation or game claim follows.',
            'The Mac-driver case covers twenty owned Win32/Cocoa lifetimes on the observed local graphical session.',
            'No-late-callback checks end at the final main-thread barrier and event drain; normal process exit is verified separately.',
            'Signals and suspension regressions cover only source-bound cooperative fixture windows.',
            'Exception recovery and handler ordering do not establish general unwind support.',
            'Native-created guest callback threads, arbitrary callbacks and concurrent code mutation remain unqualified.',
            'Metal rendering, DXMT private-driver pairing and ordinary-user game launching remain unqualified.',
            'Owned descendants retain the root process group; loaded-image snapshots are not a complete load timeline.',
            'Per-process arena counters are observations, not performance measurements or a general JIT service.',
            'Local paths, identities, signing materials, raw events and diagnostics are excluded.']}
    need(validate_prepared(runtime) == signed and sha256(runtime / 'signed.json') == signed_digest and
         sha256(root / 'build.json') == build_digest and sha256(root / 'abi-review.json') == review_digest and
         sha256(runs_root / 'run.json') == api['run_sha256'] and
         sha256(bootstrap_root / 'run.json') == bootstrap['run_sha256'] and source_hashes() == sources,
         'export_evidence_changed')
    return public


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', required=True)
    parser.add_argument('--runs', required=True)
    parser.add_argument('--bootstrap-runs', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        result = export(args.build, args.runs, args.bootstrap_runs)
        destination = Path(args.output).absolute()
        approved = REPO.resolve() / 'mydocs/working'
        need(destination.is_relative_to(approved) and destination.suffix == '.json' and not destination.exists(),
             'export_destination')
        current = REPO.resolve()
        for part in relative(destination.relative_to(current).as_posix()):
            current /= part
            need(not current.is_symlink(), 'export_destination_symlink')
        with destination.open('xb') as stream:
            stream.write(encoded(result))
    except (Error, OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(encoded({'error': getattr(exc, 'code', 'stage5_export_failed')}).decode(), end='')
        return 1
    print('Sanitized Stage 5 evidence exported after local gate validation.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
