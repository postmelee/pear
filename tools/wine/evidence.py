"""Export allowlisted scoped facts after validating their local raw evidence."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import sys

from common import Error, HEX256, REPO, decode_json, encoded, load_json, need, read_relative, record, relative, sha256
from verify import validate_stage1


def summarize_failed_attempts(paths, final_report):
    """Retain failure identities without publishing diagnostic strings or paths."""
    allowed_commands = {row['id'] for row in final_report['commands']} | {
        'arm64ec.support.compile', 'arm64ec.support.inspect'}
    allowed_checks = {row['id'] for row in final_report['checks']} | {'arm64ec.support'}
    allowed_fixtures = set(final_report['fixture_hashes'])
    result = []
    for index, path in enumerate(paths, 1):
        path = Path(path)
        need(path.resolve().is_relative_to(REPO / '.build/task4'), 'attempt_outside_task')
        attempt = load_json(path)
        if attempt.get('record_kind') == 'wine_toolchain_driver_failure':
            record(attempt, 'wine_toolchain_driver_failure')
            need(type(attempt.get('exit_code')) is int and attempt['exit_code'] != 0
                 and attempt.get('completed_check_report') is False, 'driver_failure_scope')
            result.append({'id': 'attempt-' + str(index), 'record_sha256': sha256(path),
                           'passed': False, 'kind': 'uncaught_driver_exception',
                           'exit_code': attempt['exit_code'], 'completed_check_report': False,
                           'diagnostic_provenance': 'Execution tool output transcribed after completion.'})
            continue
        record(attempt, 'wine_toolchain_check')
        need(attempt.get('passed') is False and attempt.get('pe_execution') is False
             and attempt.get('wine_runtime_execution') is False, 'attempt_scope')
        completed = [row['id'] for row in attempt['checks'] if row.get('status') == 'passed']
        need(set(completed) <= allowed_checks, 'attempt_check_scope')
        commands = []
        for row in attempt['commands']:
            need(row.get('id') in allowed_commands and type(row.get('exit_code')) is int
                 and type(row.get('timed_out')) is bool and type(row.get('output_limit')) is bool,
                 'attempt_command_scope')
            commands.append({key: row[key] for key in ('id', 'exit_code', 'timed_out', 'output_limit')})
        fixtures = attempt['fixture_hashes']
        need(set(fixtures) == allowed_fixtures and all(isinstance(value, str) and HEX256.fullmatch(value)
             for value in fixtures.values()), 'attempt_fixture_scope')
        hashes = {key: attempt[key] for key in ('lock_sha256', 'config_sha256', 'prepared_sha256')}
        need(all(isinstance(value, str) and HEX256.fullmatch(value) for value in hashes.values()),
             'attempt_digest_scope')
        result.append({'id': 'attempt-' + str(index), 'record_sha256': sha256(path),
                       'passed': False, 'fixture_hashes': fixtures, **hashes,
                       'completed_checks': completed, 'commands': commands})
    return result


def export(inputs, config, toolchain, attempts=()):
    assessment = validate_stage1(inputs, config, toolchain)
    report_path = Path(toolchain)
    raw = read_relative(report_path.parent, report_path.name)
    need(hashlib.sha256(raw).hexdigest() == assessment['toolchain_evidence_sha256'], 'export_evidence_changed')
    report = decode_json(raw)
    commands = []
    for row in report['commands']:
        commands.append({'id': row['id'], 'exit_code': row['exit_code'],
                         'timed_out': row['timed_out'], 'output_limit': row['output_limit'],
                         'stdout_bytes': row.get('stdout_log', {}).get('size_bytes', len(row['stdout'].encode('utf-8'))),
                         'stderr_bytes': row.get('stderr_log', {}).get('size_bytes', len(row['stderr'].encode('utf-8')))})
    source_paths = list((REPO / 'tools/wine').glob('*.py')) + list((REPO / 'tests/wine').rglob('*'))
    bindings = {p.relative_to(REPO).as_posix(): sha256(p) for p in sorted(source_paths)
                if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    return {'schema_version': 1, 'record_kind': 'wine_stage1_observations',
            'scope': 'component_inputs_and_compiler_fixtures', 'assessment': assessment,
            'fixture_hashes': report['fixture_hashes'], 'reviewed_source_hashes': bindings,
            'sdk': {key: report['sdk'][key] for key in ('version', 'canonical_name', 'settings_sha256')},
            'llvm_clang_version': '23.1.1', 'bison_version': '3.8.2',
            'failed_attempts': summarize_failed_attempts(attempts, report),
            'checks': [{'id': x['id'], 'status': x['status']} for x in report['checks']],
            'commands': commands, 'native_fixture_stdout': '{"fixture":"pear-toolchain-native-v1","value":42}\n',
            'pe_execution': False, 'wine_runtime_execution': False,
            'limits': ['Same-host component/tool checks, not independent compiler reproduction.',
                       'No PE, Wine runtime, game or distribution execution is qualified.',
                       'Command paths, raw output and identifiers remain in ignored local records.']}


def summarize_build_attempt(path):
    """Retain failed build identity and bounded outcomes, withholding diagnostics."""
    path = Path(path)
    need(path.resolve().is_relative_to(REPO / '.build/task4'), 'attempt_outside_task')
    value = record(load_json(path), 'wine_build')
    need(value.get('scope') == 'wine_component' and value.get('passed') is False
         and value.get('wine_runtime_execution') is False, 'attempt_scope')
    variant = value.get('variant')
    need(variant in ('arm64', 'arm64ec-build'), 'attempt_variant')
    commands = []
    allowed = {'patch-1', 'patch-2', 'configure', 'make', 'install', 'fixture-bootstrap', 'fixture-sentinel'}
    for row in value.get('commands', []):
        need(row.get('id') in allowed and type(row.get('exit_code')) is int
             and type(row.get('timed_out')) is bool and type(row.get('output_limit')) is bool,
             'attempt_command_scope')
        commands.append({key: row[key] for key in ('id', 'exit_code', 'timed_out', 'output_limit')})
    error = value.get('error')
    allowed_errors = {'build_required_outputs_missing', 'build_interrupted'} | {
        prefix + name for name in allowed for prefix in ('build_command_failed:', 'build_command_interrupted:')}
    return {'record_sha256': sha256(path), 'variant': variant, 'passed': False,
            'error': error if error in allowed_errors else 'unclassified_build_failure',
            'commands': commands, 'wine_runtime_execution': False}


def bound_record(path, digest, kind):
    """Use the same bytes for identity validation and public-field selection."""
    path = Path(path)
    raw = read_relative(path.parent, path.name)
    need(hashlib.sha256(raw).hexdigest() == digest, 'export_evidence_changed')
    return record(decode_json(raw), kind)


FAILED_CASES = ('bootstrap', 'bootstrap-timeout', 'wrong-prefix-server')
FAILED_RUN_SOURCES = {
    'tools/wine/run_fixtures.py': 'runner', 'tests/wine/cases.json': 'case_definitions',
    'tests/wine/fixtures/bootstrap_native.c': 'bootstrap_helper',
    'tests/wine/fixtures/sentinel.c': 'sentinel'}
FAILED_ERRORS = {
    'missing_process_events', 'bootstrap_early_exit', 'bootstrap_exit_failed', 'server_early_exit',
    'server_start_timeout', 'sentinel_start_timeout', 'bootstrap_arm_timeout', 'runner_interrupted',
    'runner_os_error', 'output_limit', 'pipe_read_error', 'truncated_event', 'invalid_event',
    'event_line_limit', 'unexpected_descendant_observation_gap', 'launch_observation_setup_failed',
    'cleanup_incomplete', 'unrelated_sentinel_lost', 'unrelated_sentinel_changed', 'pipe_drain_incomplete',
    'drain_observation_failed', 'observer_close_failed', 'selector_close_failed', 'pipe_close_failed',
    'log_write_failed', 'spawn_error', 'missing_actual_handshake', 'unexpected_bootstrap_sequence',
    'unexpected_refusal_sequence', 'missing_server_refusal', 'wrong_server_peer', 'server_generation_mismatch',
    'page_geometry', 'null_guard_unproven', 'owned_low_mapping_unproven', 'wrong_native_slice',
    'translation_not_proven', 'native_bootstrap_failure', 'unbound_loaded_image', 'loaded_uuid_mismatch',
    'signed_runtime_changed', 'case_not_recorded', 'timeout_control_not_triggered',
    'refusal_control_not_triggered', 'missing_bootstrap_terminal', 'owned_group_survivor',
    'owned_group_observation_failed', 'signal_refused', 'reap_failed', 'cleanup_observation_failed'}


def _public_run_error(value):
    need(value is None or isinstance(value, str), 'failed_run_error_shape')
    return value if value is None or value in FAILED_ERRORS else 'unclassified_native_failure'


def _digest(value):
    need(isinstance(value, str) and HEX256.fullmatch(value), 'failed_run_digest_shape')
    return value


def _failed_root(path):
    path = Path(path).absolute()
    root = REPO.resolve()
    need(path.is_relative_to(root / '.build/task4'), 'failed_run_outside_task')
    current = root
    for part in relative(path.relative_to(root).as_posix()):
        current /= part
        need(not current.is_symlink(), 'failed_run_symlink_path')
    return path


def _historical_source(name, digest, failed_root, signing=False, archive_only=False):
    """Find exact bytes, never execute archived producers or infer current grants."""
    _digest(digest)
    candidates = [failed_root / 'producer' / name]
    if not archive_only:
        candidates.insert(0, REPO / name)
    if signing:
        revisions = REPO / '.build/task4/signing-revisions'
        if revisions.exists():
            need(not revisions.is_symlink(), 'failed_run_symlink_path')
            entries = sorted(revisions.iterdir())
            need(len(entries) <= 64, 'historical_source_limit')
            for entry in entries:
                need(not entry.is_symlink(), 'failed_run_symlink_path')
                if entry.is_dir():
                    candidates.append(entry / Path(name).name)
    for candidate in candidates:
        try:
            raw = read_relative(REPO, candidate.relative_to(REPO).as_posix())
        except FileNotFoundError:
            continue
        if hashlib.sha256(raw).hexdigest() == digest:
            return True
    return False


def _failed_cleanup(value, roles):
    need(isinstance(value, dict), 'failed_cleanup_shape')
    for key in ('complete', 'observation_gap'):
        need(type(value.get(key)) is bool, 'failed_cleanup_boolean')
    reaped, errors, signals = value.get('reaped'), value.get('errors'), value.get('signals')
    need(isinstance(reaped, dict) and set(reaped) <= roles and
         all(type(flag) is bool for flag in reaped.values()), 'failed_cleanup_reaped')
    need(isinstance(errors, list) and len(errors) <= 64 and
         isinstance(signals, list) and len(signals) <= 16, 'failed_cleanup_bounds')
    public_errors = []
    for error in errors:
        need(isinstance(error, dict) and error.get('role') in roles | {'observer'}, 'failed_cleanup_error_scope')
        public_errors.append(_public_run_error(error.get('code')))
    for row in signals:
        need(isinstance(row, dict) and row.get('role') in roles and
             type(row.get('signal')) is int and row['signal'] in (2, 15, 9), 'failed_cleanup_signal_scope')
    calculated = not errors and not value['observation_gap'] and all(reaped.values())
    need(value['complete'] is calculated, 'failed_cleanup_label_mismatch')
    return {'complete': calculated, 'observation_gap': value['observation_gap'],
            'observed_process_count': len(reaped), 'reaped_count': sum(reaped.values()),
            'signal_count': len(signals), 'errors': public_errors}


def _summarize_failed_case(root, row, case_id):
    need(row.get('path') == case_id + '/case.json' and type(row.get('passed')) is bool,
         'failed_case_reference')
    expected_sha = _digest(row.get('sha256'))
    public = {'case': case_id, 'record_status': 'partial', 'case_sha256': None,
              'expected_case_sha256': expected_sha, 'reported_passed': row['passed'],
              'missing_records': [], 'logs': []}
    try:
        raw = read_relative(root, row['path'])
    except FileNotFoundError:
        public['missing_records'].append('case_record')
        return public
    need(hashlib.sha256(raw).hexdigest() == expected_sha, 'failed_case_changed')
    value = record(decode_json(raw), 'wine_bootstrap_case')
    need(value.get('pe_executed') is False and value.get('runtime_qualified') is False and
         type(value.get('passed')) is bool, 'failed_case_scope')
    expected = {'bootstrap': ('normal', 120000, 'bootstrap_stop'),
                'bootstrap-timeout': ('hold', 1500, 'timeout'),
                'wrong-prefix-server': ('wrong-prefix', 30000, 'server_refused')}[case_id]
    mode, timeout, terminal = expected
    need(value.get('case') == {'id': case_id, 'mode': mode, 'timeout_ms': timeout, 'expected': terminal},
         'failed_case_configuration')
    need(value.get('outcome') in ('not_started', 'exited', 'timeout', 'error', 'interrupted'), 'failed_case_outcome')
    need(type(value.get('elapsed_ms')) is int and 0 <= value['elapsed_ms'] <= 24*60*60*1000,
         'failed_case_duration')
    public.update(case_sha256=expected_sha, outcome=value['outcome'],
                  error=_public_run_error(value.get('error')),
                  assessment_error=_public_run_error(value.get('assessment_error')),
                  stream_error=_public_run_error(value.get('stream_error')), elapsed_ms=value['elapsed_ms'])
    assessment_name = case_id + '/assessment.json'
    need(row.get('assessment_path') == assessment_name, 'failed_assessment_reference')
    assessment_sha = _digest(row.get('assessment_sha256'))
    try:
        assessment_raw = read_relative(root, assessment_name)
    except FileNotFoundError:
        public['missing_records'].append('gate_assessment')
    else:
        need(hashlib.sha256(assessment_raw).hexdigest() == assessment_sha, 'failed_assessment_changed')
        assessment = record(decode_json(assessment_raw), 'wine_case_gate_assessment')
        need(assessment.get('case_sha256') == expected_sha and
             type(assessment.get('passed')) is bool and assessment['passed'] is row['passed'],
             'failed_assessment_scope')
        need(not assessment['passed'] or value['passed'], 'failed_assessment_promoted')
        public.update(assessment_sha256=assessment_sha,
                      gate_error=_public_run_error(assessment.get('error')))
    processes = value.get('processes')
    roles = {'server', 'loader', 'sentinel'}
    need(isinstance(processes, dict) and set(processes) <= roles, 'failed_process_scope')
    statuses = []
    for role in sorted(processes):
        process = processes[role]
        code = process.get('exit_code')
        need(code is None or type(code) is int and -128 <= code <= 255, 'failed_exit_code')
        need(type(process.get('reaped')) is bool and type(process.get('fork_seen')) is bool,
             'failed_process_boolean')
        statuses.append({'role': role, 'exit_code': code, 'reaped': process['reaped'],
                         'fork_observed': process['fork_seen']})
    public['processes'] = statuses
    public['cleanup'] = _failed_cleanup(value.get('cleanup'), {'loader', 'server'})
    public['sentinel_cleanup'] = _failed_cleanup(value.get('sentinel_cleanup'), {'sentinel'})
    need(type(value.get('sentinel_survived')) is bool, 'failed_sentinel_boolean')
    public['reported_sentinel_survived'] = value['sentinel_survived']
    logs = value.get('logs')
    need(isinstance(logs, list) and len(logs) <= 8, 'failed_log_count')
    allowed = {(role, channel) for role in roles for channel in ('stdout', 'stderr')}
    allowed |= {('server', 'events'), ('loader', 'events')}
    seen, raw_logs = set(), {}
    for log in logs:
        key = (log.get('role'), log.get('channel'))
        need(key in allowed and key not in seen, 'failed_log_scope')
        seen.add(key)
        role, channel = key
        name = role + '.' + channel + '.log'
        need(log.get('path') == name and type(log.get('eof')) is bool and
             type(log.get('bytes')) is int and type(log.get('observed_bytes')) is int,
             'failed_log_shape')
        cap = 2097152 if channel == 'events' else 262144
        need(0 <= log['bytes'] <= cap + 1 and log['bytes'] <= log['observed_bytes'] <= 2**40,
             'failed_log_bounds')
        digest = _digest(log.get('sha256'))
        log_error = _public_run_error(log.get('write_error'))
        try:
            data = read_relative(root, case_id + '/' + name, cap + 1)
        except FileNotFoundError:
            public['missing_records'].append(role + '_' + channel)
            continue
        need(len(data) == log['bytes'] and hashlib.sha256(data).hexdigest() == digest, 'failed_log_changed')
        raw_logs[key] = data
        public['logs'].append({'role': role, 'channel': channel, 'sha256': digest,
                               'bytes': len(data), 'observed_bytes': log['observed_bytes'],
                               'eof': log['eof'], 'write_error': log_error})
    for role, channel in sorted(allowed - seen):
        public['missing_records'].append(role + '_' + channel)
    events = value.get('events')
    need(isinstance(events, dict) and set(events) == {'loader', 'server'}, 'failed_event_scope')
    counts = {}
    for role in ('loader', 'server'):
        rows = events[role]
        need(isinstance(rows, list) and len(rows) <= 16384 and all(isinstance(x, dict) for x in rows),
             'failed_event_bounds')
        data = raw_logs.get((role, 'events'))
        if data is None:
            counts[role] = None
            continue
        decoded, invalid = [], 0
        for line in data.splitlines():
            try:
                decoded.append(decode_json(line, 32768))
            except Error:
                invalid += 1
        if decoded != rows or invalid or data and not data.endswith(b'\n'):
            need(value.get('stream_error') is not None, 'failed_event_log_mismatch')
            public['missing_records'].append(role + '_complete_event_parse')
        counts[role] = len(decoded)
    public['retained_event_counts'] = counts
    if not public['missing_records']:
        public['record_status'] = 'complete'
    return public


def summarize_failed_run(path):
    """Verify retained failure bytes without reauthorizing old signatures or execution."""
    root = _failed_root(path)
    public = {'scope': 'historical_failed_native_bootstrap', 'passed': False,
              'record_status': 'partial', 'run_sha256': None, 'missing_records': [],
              'cases': [], 'pe_execution': False, 'runtime_qualified': False}
    try:
        raw = read_relative(root, 'run.json')
    except FileNotFoundError:
        public['missing_records'].append('run_record')
        return public
    value = record(decode_json(raw), 'wine_bootstrap_run')
    need(value.get('suite') == 'bootstrap' and value.get('passed') is False and
         value.get('pe_executed') is False and value.get('runtime_qualified') is False, 'failed_run_scope')
    public.update(run_sha256=hashlib.sha256(raw).hexdigest(), error=_public_run_error(value.get('error')))
    producers = value.get('producer_sha256')
    need(isinstance(producers, dict) and set(producers) == set(FAILED_RUN_SOURCES), 'failed_source_scope')
    need(value.get('runner_sha256') == producers['tools/wine/run_fixtures.py'] and
         value.get('cases_sha256') == producers['tests/wine/cases.json'], 'failed_source_binding')
    public['source_sha256'] = {}
    for name, label in FAILED_RUN_SOURCES.items():
        digest = _digest(producers[name])
        public['source_sha256'][label] = digest
        if not _historical_source(name, digest, root):
            public['missing_records'].append('source_' + label)
    runtime_name = '/'.join(relative(value.get('runtime_path')))
    runtime = _failed_root(REPO / runtime_name)
    signed_sha = _digest(value.get('signed_sha256'))
    try:
        signed_raw = read_relative(runtime, 'signed.json')
    except FileNotFoundError:
        public['missing_records'].append('signed_record')
    else:
        need(hashlib.sha256(signed_raw).hexdigest() == signed_sha, 'failed_signed_record_changed')
        signed = record(decode_json(signed_raw), 'wine_signed_runtime')
        need(signed.get('wine_execution') is False and signed.get('runtime_qualified') is False,
             'failed_signed_scope')
        public['signed_record_sha256'] = signed_sha
        source = signed.get('producer_sha256')
        need(isinstance(source, dict) and set(source) == {'signing.py', 'common.py'}, 'failed_signer_source_scope')
        public['signer_source_sha256'] = {}
        for name, digest in source.items():
            label = 'signer' if name == 'signing.py' else 'common'
            public['signer_source_sha256'][label] = _digest(digest)
            if not _historical_source('tools/wine/' + name, digest, root, signing=True):
                public['missing_records'].append('source_' + label)
    rows = value.get('cases')
    need(isinstance(rows, list) and len(rows) <= 3 and all(isinstance(row, dict) for row in rows), 'failed_case_count')
    names = [row.get('id') for row in rows]
    need(all(name in FAILED_CASES for name in names) and len(set(names)) == len(names) and
         names == [name for name in FAILED_CASES if name in names], 'failed_case_scope')
    by_name = dict(zip(names, rows))
    for name in FAILED_CASES:
        if name in by_name:
            case = _summarize_failed_case(root, by_name[name], name)
            public['cases'].append(case)
        else:
            public['cases'].append({'case': name, 'record_status': 'partial',
                                    'case_sha256': None, 'missing_records': ['case_reference']})
    public['retained_case_count'] = len(rows)
    if not public['missing_records'] and all(case['record_status'] == 'complete' for case in public['cases']):
        public['record_status'] = 'complete'
    return public


def export_stage2(native_root, companion_root, runs_root, failed_builds=(), failed_runs=()):
    from verify import validate_builds
    from run_fixtures import validate_runs
    from signing import validate_prepared
    builds = validate_builds(native_root, companion_root)
    runs = validate_runs(runs_root, 'bootstrap')
    run_record = bound_record(Path(runs_root) / 'run.json', runs['run_sha256'], 'wine_bootstrap_run')
    runtime_root = REPO / run_record['runtime_path']
    signed = validate_prepared(runtime_root)
    need(bound_record(runtime_root / 'signed.json', runs['signed_sha256'], 'wine_signed_runtime') == signed,
         'export_evidence_changed')
    need(signed['build_ref']['sha256'] == builds['variants'][0]['build_sha256'], 'tested_build_mismatch')
    profile_keys = {'unexpired', 'macos_platform', 'explicit_application_match',
                    'team_and_prefix_consistent', 'single_cross_architecture_grant',
                    'current_provisioning_device_match', 'available_development_certificate_match'}
    need(profile_keys <= set(signed['profile_checks']) and
         all(signed['profile_checks'][key] is True for key in profile_keys), 'export_profile_checks')
    native, companion = [bound_record(Path(root) / 'build.json', variant['build_sha256'], 'wine_build')
                         for root, variant in zip((native_root, companion_root), builds['variants'])]
    # Never export command argv, raw streams, certificates, profile IDs or image paths.
    commands = {value['variant']: [{key: row[key] for key in
                ('id', 'exit_code', 'timed_out', 'output_limit')} for row in value['commands']]
                for value in (native, companion)}
    source_paths = list((REPO / 'tools/wine').glob('*.py')) + list((REPO / 'tests/wine').rglob('*'))
    bindings = {path.relative_to(REPO).as_posix(): sha256(path) for path in sorted(source_paths)
                if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc'}
    return {'schema_version': 1, 'record_kind': 'wine_stage2_observations',
            'scope': 'development_native_wine_bootstrap_before_pe',
            'build_assessment': builds, 'run_assessment': runs,
            'reviewed_source_hashes': bindings, 'commands': commands,
            'sdk': {key: native['sdk'][key] for key in ('version', 'canonical_name', 'settings_sha256')},
            'authorization': {'profile_checks': {key: True for key in sorted(profile_keys)},
                              'native_images_signed': len(signed['native_images']),
                              'hardened_runtime': True, 'library_validation': 'enabled', 'allow_jit': False,
                              'scope': 'development_native_bootstrap_pre_pe'},
            'failed_build_attempts': [summarize_build_attempt(path) for path in failed_builds],
            'failed_native_runs': [summarize_failed_run(path) for path in failed_runs],
            'pe_execution': False, 'guest_x18_execution': False, 'game_execution': False,
            'limits': ['Native bootstrap stops before Windows PE execution or guest x18 initialization.',
                       'ARM64EC/ARM64X modules are build observations, not translator execution.',
                       'Same-host development evidence; no game or distribution qualification.',
                       'Finite directly owned bootstrap process observation, not arbitrary game process coverage.',
                       'Identifiers, profiles, raw logs and local paths remain in ignored records.']}


PROFILE_CHECKS = {'unexpired', 'macos_platform', 'explicit_application_match',
                  'team_and_prefix_consistent', 'single_cross_architecture_grant',
                  'current_provisioning_device_match', 'available_development_certificate_match'}
STAGE3_SOURCES = {
    'exporter': 'tools/wine/evidence.py', 'build_driver': 'tools/wine/build.py',
    'signer': 'tools/wine/signing.py', 'api_runner': 'tools/wine/api_runner.py',
    'bootstrap_runner': 'tools/wine/run_fixtures.py', 'assembly_checker': 'tools/wine/abi_review.py',
    'api_fixture': 'tests/wine/fixtures/api_pe.c', 'abi_guest_fixture': 'tests/wine/fixtures/abi_pe.c',
    'abi_native_fixture': 'tests/wine/fixtures/abi_native.c',
    'abi_gateway': 'tests/wine/fixtures/abi_gateway.S', 'api_launch': 'tests/wine/fixtures/api_launch.c',
    'api_cases': 'tests/wine/cases-stage3.json', 'bootstrap_cases': 'tests/wine/cases.json',
    'common': 'tools/wine/common.py', 'toolchain': 'tools/wine/toolchain.py',
    'pe_module_parser': 'tools/wine/modules.py',
    'lifetime_fixture': 'tests/wine/fixtures/lifetime_pe.c',
    'lifetime_protocol': 'tests/wine/fixtures/lifetime_pe.h',
    'missing_import_fixture': 'tests/wine/fixtures/missing_import_pe.c',
    'missing_named_import': 'tests/wine/fixtures/missing_name.def',
    'missing_ordinal_import': 'tests/wine/fixtures/missing_ordinal.def',
}


def _public_integer(value, maximum=1000000):
    need(type(value) is int and 0 <= value <= maximum, 'export_integer_shape')
    return value


def _stage3_commands(value):
    names = {'configure', 'make', 'install', 'fixture-bootstrap', 'fixture-sentinel',
             'fixture-api-launch', 'fixture-api-arm64', 'fixture-api-x64', 'fixture-api-i386',
             'fixture-abi-arm64', 'disassemble-ntdll', 'disassemble-abi', 'fixture-lifetime-dll',
             'fixture-missing-name-importlib', 'fixture-missing-name-dll',
             'fixture-missing-ordinal-importlib', 'fixture-missing-ordinal-dll'}
    names |= {'patch-' + str(i) for i in range(1, 65)}
    commands = value.get('commands')
    need(isinstance(commands, list) and 0 < len(commands) <= 81, 'export_command_coverage')
    result = []
    for row in commands:
        need(row.get('id') in names and type(row.get('exit_code')) is int and row['exit_code'] == 0 and
             row.get('timed_out') is False and row.get('output_limit') is False, 'export_command_scope')
        result.append({key: row[key] for key in ('id', 'exit_code', 'timed_out', 'output_limit')})
    return result


def _stage3_authorization(signed, native_count):
    from signing import APP_ID, TEAM_ID, CROSS_KEYS
    jit = 'com.apple.security.cs.allow-jit'
    need(signed.get('code_publication_policy') == 'page-wx', 'export_publication_policy')
    checks = signed.get('profile_checks', {})
    need(PROFILE_CHECKS <= set(checks) and all(checks[key] is True for key in PROFILE_CHECKS),
         'export_profile_checks')
    need(signed.get('authorization_scope') == 'development_windows_api_abi_fixtures' and
         signed.get('distribution_qualified') is False and signed.get('runtime_qualified') is False,
         'export_authorization_scope')
    images = signed.get('native_images')
    need(isinstance(images, list) and len(images) == native_count, 'export_native_signature_coverage')
    allowed_roles = {'api-launch-helper', 'bootstrap-helper', 'native-helper', 'native-library',
                     'sentinel', 'wine-loader', 'wine-server', 'wine-wrapper'}
    counts = {name: 0 for name in sorted(allowed_roles)}
    for image in images:
        role = image.get('role')
        need(role in allowed_roles, 'export_native_role')
        counts[role] += 1
        signature = image.get('signature', {})
        need(all(signature.get(key) is True for key in ('hardened_runtime', 'same_team', 'strict_verification'))
             and signature.get('ad_hoc') is False and signature.get('category') == 'apple_development',
             'export_signature_checks')
        keys = signature.get('claim_keys')
        need(isinstance(keys, list) and len(keys) == len(set(keys)), 'export_claim_keys')
        if role == 'wine-loader':
            need({APP_ID, TEAM_ID, jit} <= set(keys) and len(set(keys) & set(CROSS_KEYS)) == 1 and
                 set(keys) <= {APP_ID, TEAM_ID, jit, *CROSS_KEYS} and
                 type(signature.get('code_directory_page_size')) is int and
                 signature['code_directory_page_size'] == 4096, 'export_loader_claims')
        else:
            need(not keys and type(signature.get('code_directory_page_size')) is int and
                 signature['code_directory_page_size'] in (4096, 16384), 'export_native_claims')
    need(all(counts[role] == 1 for role in ('api-launch-helper', 'bootstrap-helper', 'sentinel',
                                         'wine-loader', 'wine-server', 'wine-wrapper')), 'export_native_roles')
    return {'profile_checks': {key: True for key in sorted(PROFILE_CHECKS)},
            'native_images_signed': native_count, 'native_role_counts': counts,
            'hardened_runtime': True, 'library_validation': 'enabled', 'allow_jit': True,
            'allow_jit_scope': 'wine-loader-only', 'code_publication_policy': 'page-wx',
            'loader_signature_page_size': 4096, 'scope': 'development_windows_api_abi_fixtures',
            'ordinary_user_distribution_qualified': False}


def _stage3_assembly(value, build_digest):
    from abi_review import ENTRIES, HELPERS
    need(value.get('analysis_passed') is True and value.get('gate_passed') is True and
         value.get('reader_reproduced') is True and value.get('binary_binding') == 'verified' and
         value.get('runtime_execution') is False and value.get('build_sha256') == build_digest and
         value.get('trusted_reader_required') is True, 'export_assembly_gate')
    entries, helpers = value.get('entries'), value.get('helpers')
    need(isinstance(entries, list) and [row.get('entry') for row in entries] == list(ENTRIES) and
         isinstance(helpers, list) and [row.get('entry') for row in helpers] == list(HELPERS),
         'export_assembly_coverage')
    public_entries, public_helpers = [], []
    for row in entries:
        initial, terminal = ENTRIES[row['entry']]
        need(type(row.get('required_entry_mode')) is int and row['required_entry_mode'] == initial and
             type(row.get('required_return_mode')) is int and row['required_return_mode'] == terminal and
             row.get('x18_only_foreign') is True and row.get('ordinary_calls_only_host') is True,
             'export_assembly_entry')
        public_entries.append({'entry': row['entry'], 'required_entry_mode': initial, 'required_return_mode': terminal,
            'reachable_instruction_states': _public_integer(row.get('reachable_instruction_states'), 4096),
            'terminal_paths': _public_integer(row.get('terminal_paths'), 4096),
            'x18_only_foreign': True, 'ordinary_calls_only_host': True})
    for row in helpers:
        desired = HELPERS[row['entry']]
        need(type(row.get('requested_mode')) is int and row['requested_mode'] == desired and
             row.get('api_sequence') == ['getter', 'setter', 'getter'] and
             row.get('pointer_symbols_bound') is True and row.get('register_spills_checked') is True and
             type(row.get('ordinary_calls')) is int and row['ordinary_calls'] == 0, 'export_assembly_helper')
        public_helpers.append({'entry': row['entry'], 'requested_mode': desired,
            'instruction_count': _public_integer(row.get('instruction_count'), 4096),
            'api_sequence': ['getter', 'setter', 'getter'], 'pointer_symbols_bound': True,
            'register_spills_checked': True, 'ordinary_calls': 0})
    return {'scope': 'six_declared_wine_assembly_entries_and_two_mode_helpers', 'analysis_passed': True,
            'binary_binding': 'verified', 'reader_reproduced': True, 'runtime_execution': False,
            'binary_sha256': _digest(value.get('binary_sha256')),
            'disassembly_sha256': _digest(value.get('disassembly_sha256')),
            'reader_sha256': _digest(value.get('reader_sha256')),
            'instruction_bytes_checked': _public_integer(value.get('instruction_bytes_checked'), 4000000),
            'entries': public_entries, 'helpers': public_helpers,
            'unqualified': ['arbitrary_native_callbacks', 'signal_context_semantics', 'unwinding',
                            'all_wine_control_flow', 'performance']}


def _stage3_relocations(value):
    """Select only the host-verified, finite two-placement relocation facts."""
    need(isinstance(value, dict), 'export_relocation_missing')
    expected_counts = {'placements': 2, 'copied_files_verified': 2,
                       'relocated_pointer_slots': 4, 'probe_calls_verified': 4,
                       'retirements_verified': 2, 'security_cookie_images': 2,
                       'security_cookie_observations': 4}
    public = {'fixture_sha256': _digest(value.get('fixture_sha256'))}
    for key, expected in expected_counts.items():
        need(type(value.get(key)) is int and value[key] == expected, 'export_relocation_count')
        public[key] = expected
    for key in ('simultaneous_live', 'distinct_bases', 'distinct_slots', 'nonzero_deltas',
                'original_pointer_rvas_verified', 'code_targets_verified', 'data_isolation_verified',
                'security_cookie_initialized', 'security_cookie_stable',
                'security_cookie_destination_verified', 'security_cookie_load_config_verified'):
        need(value.get(key) is True, 'export_relocation_proof')
        public[key] = True
    return public


def _stage3_runs(api, bootstrap):
    from api_runner import ENVIRONMENT_POLICY, expected_fixture_rows, validate_environment_policy
    need(api.get('passed') is True and api.get('pe_executed') is True and api.get('runtime_qualified') is False and
         api.get('case_count') == 2 and type(api.get('case_count')) is int and
         api.get('code_publication_policy') == 'page-wx', 'export_api_gate')
    validate_environment_policy(api.get('environment_policy'))
    need(bootstrap.get('passed') is True and bootstrap.get('pe_executed') is False and
         bootstrap.get('runtime_qualified') is False and bootstrap.get('case_count') == 3 and
         type(bootstrap.get('case_count')) is int, 'export_bootstrap_gate')
    need([row.get('id') for row in api['cases']] == ['api', 'abi'] and
         [row.get('id') for row in bootstrap['cases']] == list(FAILED_CASES), 'export_run_cases')
    results = []
    for row in api['cases']:
        validate_environment_policy(row.get('environment_policy'))
        expected = expected_fixture_rows(row['id'])
        need(row.get('fixture_results') == expected and
             all(type(observed[key]) is type(value) for observed, wanted in zip(row['fixture_results'], expected)
                 for key, value in wanted.items()) and
             all(row.get(key) is True for key in ('passed', 'cleanup_complete', 'sentinel_survived')),
             'export_fixture_result')
        arena = row.get('arena_observations')
        need(row.get('code_publication_policy') == 'page-wx' and isinstance(arena, list) and
             len(arena) == row.get('pe_processes') and len({item.get('role') for item in arena}) == len(arena),
             'export_arena_coverage')
        public_arena = []
        for item in arena:
            need(item.get('policy') == 'page-wx' and isinstance(item.get('role'), str) and
                 (item['role'] == 'loader' or re.fullmatch('process-[0-9]{2}', item['role'])),
                 'export_arena_policy')
            counts = {key: _public_integer(item.get(key), 1000000000) for key in
                      ('publications', 'retirements', 'compatible_reuses', 'published_code_pages',
                       'published_data_pages', 'relocations', 'live_images_at_last_observation')}
            need(counts['publications'] > 0 and counts['published_code_pages'] > 0 and
                 counts['retirements'] <= counts['publications'] and
                 counts['live_images_at_last_observation'] == counts['publications'] - counts['retirements'] and
                 counts['compatible_reuses'] < counts['publications'], 'export_arena_counts')
            public_arena.append({'role': item['role'], 'policy': 'page-wx', **counts})
        relocation = {}
        if row['id'] == 'abi':
            relocation['relocation_observations'] = _stage3_relocations(row.get('relocation_observations'))
        else:
            need(row.get('relocation_observations') is None, 'export_relocation_scope')
        # The validated raw run supplied these values. Select only the fixture's
        # fixed public result fields, excluding any future diagnostic additions.
        results.append({'id': row['id'], 'case_sha256': _digest(row.get('case_sha256')), 'passed': True,
                        'native_processes': _public_integer(row.get('native_processes'), 66),
                        'pe_processes': _public_integer(row.get('pe_processes'), 64),
                        'code_publication_policy': 'page-wx', 'environment_policy': dict(ENVIRONMENT_POLICY),
                        'arena_observations': public_arena, **relocation,
                        'fixture_results': [{key: observed[key] for key in wanted}
                                            for observed, wanted in zip(row['fixture_results'], expected)],
                        'cleanup_complete': True, 'sentinel_survived': True})
    controls = api.get('controls')
    need(isinstance(controls, list) and [row.get('role') for row in controls] == ['x64_control', 'i386_control'],
         'export_target_controls')
    public_controls = []
    for row, machine in zip(controls, ('x86_64', 'i386')):
        need(row.get('machine') == machine and row.get('executed') is False and row.get('accepted') is False and
             row.get('reason') == 'translator-not-qualified-for-target', 'export_target_control_scope')
        public_controls.append({'role': row['role'], 'machine': machine, 'sha256': _digest(row.get('sha256')),
                                'executed': False, 'accepted': False, 'reason': 'translator-not-qualified-for-target'})
    bootstrap_results = []
    for row, expected, outcome in zip(bootstrap['cases'], ('bootstrap_stop', 'timeout', 'server_refused'),
                                     ('exited', 'timeout', 'exited')):
        need(row.get('expected') == expected and row.get('outcome') == outcome and
             all(row.get(key) is True for key in ('passed', 'cleanup_complete', 'sentinel_survived')) and
             row.get('actual_handshake') is (expected != 'server_refused'), 'export_bootstrap_case')
        bootstrap_results.append({'id': row['id'], 'case_sha256': _digest(row.get('case_sha256')),
            'expected': expected, 'outcome': outcome, 'passed': True,
            'native_process_count': _public_integer(row.get('native_process_count'), 3),
            'reexecution_count': _public_integer(row.get('reexecution_count'), 1),
            'actual_handshake': row['actual_handshake'], 'cleanup_complete': True, 'sentinel_survived': True})
    return {'api_abi': {'run_sha256': _digest(api.get('run_sha256')), 'case_count': 2, 'passed': True,
                       'code_publication_policy': 'page-wx', 'environment_policy': dict(ENVIRONMENT_POLICY),
                       'cases': results, 'controls': public_controls},
            'bootstrap': {'run_sha256': _digest(bootstrap.get('run_sha256')), 'case_count': 3,
                          'passed': True, 'cases': bootstrap_results}}


FAILED_API_SOURCES = {
    'tools/wine/api_runner.py': 'api_runner', 'tools/wine/run_fixtures.py': 'bootstrap_runner',
    'tests/wine/cases-stage3.json': 'case_definitions', 'tests/wine/fixtures/api_launch.c': 'api_launch',
    'tests/wine/fixtures/api_pe.c': 'api_fixture', 'tests/wine/fixtures/abi_pe.c': 'abi_guest_fixture',
    'tests/wine/fixtures/abi_native.c': 'abi_native_fixture',
    'tests/wine/fixtures/abi_gateway.S': 'abi_gateway', 'tests/wine/fixtures/sentinel.c': 'sentinel',
}
PAGE_WX_API_SOURCES = {**FAILED_API_SOURCES,
    'tests/wine/fixtures/lifetime_pe.c': 'lifetime_fixture',
    'tests/wine/fixtures/lifetime_pe.h': 'lifetime_protocol',
    'tests/wine/fixtures/missing_import_pe.c': 'missing_import_fixture',
    'tests/wine/fixtures/missing_name.def': 'missing_named_import',
    'tests/wine/fixtures/missing_ordinal.def': 'missing_ordinal_import'}
RELOCATION_API_SOURCES = {**PAGE_WX_API_SOURCES, 'tools/wine/modules.py': 'pe_module_parser'}
FAILED_API_ERRORS = FAILED_ERRORS | {
    'api_operation_failed', 'api_exit_failed', 'api_runner_operation_failed', 'api_case_evidence_invalid', 'api_run_failed',
    'missing_case_record', 'server_start_failed', 'pre_cleanup_observation_failed', 'registration_failed',
    'registration_timeout', 'registration_eof', 'registration_output_limit', 'registration_shape',
    'registration_identity', 'registration_scope', 'descendant_group_escape',
    'unapproved_descendant_executable', 'unexpected_root_registration', 'unregistered_native_parent',
    'native_process_limit', 'registration_connection_limit', 'registration_ack_failed',
    'missing_fixture_output', 'fixture_result_mismatch', 'fixture_result_type',
    'api_producer_changed', 'arena_operation_failed', 'arena_reservation_missing', 'arena_publication_missing',
    'arena_policy_sequence', 'lifetime_native_retirement_missing', 'import_rejection_observations',
    'unexpected_descendant_exit', 'descendant_cleanup_exit_unproven', 'missing_guest_exit',
}
FAILED_API_EVENTS = {'loader_entry', 'loader_reexec', 'ntdll_entry', 'server_ready', 'bootstrap_native',
    'image', 'images_end', 'server_peer', 'server_handshake', 'memory', 'bootstrap_stop',
    'bootstrap_hold', 'failure', 'stage3_fork', 'stage3_pe_continue', 'stage3_guest_exit', 'stage3_process_exit',
    'arena_reserve', 'arena_publish', 'arena_retire', 'arena_failure'}


def _failed_api_error(value):
    need(value is None or isinstance(value, str), 'failed_api_error_shape')
    return value if value is None or value in FAILED_API_ERRORS else 'unclassified_api_failure'


def _failed_api_role(value):
    need(value in ('loader', 'server', 'sentinel') or isinstance(value, str) and
         re.fullmatch(r'process-(?:0[1-9]|[1-5][0-9]|6[0-3])', value), 'failed_api_role')
    return value


def _failed_api_exit(value):
    need(value is None or type(value) is int and -128 <= value <= 255, 'failed_api_exit')
    return value


def _summarize_failed_api_case(root, row, case_id):
    from api_runner import CASE_JSON_BYTES, decode_case
    need(row.get('path') == case_id + '/case.json' and type(row.get('passed')) is bool,
         'failed_api_case_reference')
    digest = _digest(row.get('sha256'))
    public = {'case': case_id, 'record_status': 'partial', 'case_sha256': None,
              'expected_case_sha256': digest, 'reported_passed': row['passed'], 'missing_records': []}
    try:
        raw = read_relative(root, row['path'], CASE_JSON_BYTES)
    except FileNotFoundError:
        public['missing_records'].append('case_record')
        return public
    need(hashlib.sha256(raw).hexdigest() == digest, 'failed_api_case_changed')
    value = decode_case(raw)
    need(value.get('runtime_qualified') is False and type(value.get('pe_executed')) is bool and
         type(value.get('passed')) is bool, 'failed_api_case_scope')
    expected = {'id': case_id, 'entrypoint': case_id + '_pe', 'args':
                ['space argument', '\u03a9\ud55c\uae00\U0001f680'] if case_id == 'api' else [],
                'timeout_ms': 180000, 'expected_exit': 0}
    need(value.get('case') == expected and value.get('outcome') in
         ('not_started', 'exited', 'timeout', 'error', 'interrupted'), 'failed_api_case_configuration')
    public.update(case_sha256=digest, outcome=value['outcome'],
                  elapsed_ms=_public_integer(value.get('elapsed_ms'), 24*60*60*1000),
                  reported_guest_exit_observed=value['pe_executed'],
                  error=_failed_api_error(value.get('error')),
                  assessment_error=_failed_api_error(value.get('assessment_error')),
                  stream_error=_failed_api_error(value.get('stream_error')))
    need(row.get('assessment_path') == case_id + '/assessment.json', 'failed_api_assessment_reference')
    assessment_sha = _digest(row.get('assessment_sha256'))
    try:
        assessment_raw = read_relative(root, row['assessment_path'])
    except FileNotFoundError:
        public['missing_records'].append('gate_assessment')
    else:
        need(hashlib.sha256(assessment_raw).hexdigest() == assessment_sha, 'failed_api_assessment_changed')
        assessment = record(decode_json(assessment_raw), 'wine_case_gate_assessment')
        need(assessment.get('case_sha256') == digest and type(assessment.get('passed')) is bool and
             assessment['passed'] is row['passed'] and (not assessment['passed'] or value['passed']),
             'failed_api_assessment_scope')
        public.update(assessment_sha256=assessment_sha, gate_error=_failed_api_error(assessment.get('error')))
    processes = value.get('processes')
    need(isinstance(processes, dict) and set(processes) <= {'loader', 'server', 'sentinel'},
         'failed_api_processes')
    public['direct_processes'] = []
    for role, process in sorted(processes.items()):
        need(type(process.get('reaped')) is bool, 'failed_api_process_boolean')
        public['direct_processes'].append({'role': role, 'exit_code': _failed_api_exit(process.get('exit_code')),
                                            'reported_reaped': process['reaped']})
    registrations, pre = value.get('registrations'), value.get('pre_cleanup', {}).get('processes')
    need(isinstance(registrations, list) and len(registrations) <= 64 and isinstance(pre, dict),
         'failed_api_registrations')
    roles, registered = set(), []
    for item in registrations:
        role = _failed_api_role(item.get('role'))
        need(role not in roles and role not in ('server', 'sentinel') and type(item.get('exited')) is bool,
             'failed_api_registration_shape')
        roles.add(role)
        previous = pre.get(role)
        need(isinstance(previous, dict) and type(previous.get('exited')) is bool,
             'failed_api_pre_cleanup_shape')
        registered.append({'role': role, 'reported_exited': item['exited'],
                           'exit_code': _failed_api_exit(item.get('exit_code')),
                           'exited_before_cleanup': previous['exited'],
                           'exit_code_before_cleanup': _failed_api_exit(previous.get('exit_code'))})
    need(set(pre) == roles, 'failed_api_pre_cleanup_coverage')
    public['registered_processes'] = registered
    public['cleanup'] = _failed_cleanup(value.get('cleanup'), {'loader', 'server'})
    public['sentinel_cleanup'] = _failed_cleanup(value.get('sentinel_cleanup'), {'sentinel'})
    need(type(value.get('sentinel_survived')) is bool, 'failed_api_sentinel_shape')
    public['reported_sentinel_survived'] = value['sentinel_survived']
    events = value.get('events')
    need(isinstance(events, dict) and set(events) <= roles | {'server'}, 'failed_api_event_scope')
    logs = value.get('logs')
    need(isinstance(logs, list) and len(logs) <= 71, 'failed_api_log_count')
    required = {(role, channel) for role in ('loader', 'server', 'sentinel') for channel in ('stdout', 'stderr')}
    required |= {(role, 'events') for role in events}
    seen, counts, public_logs, total = set(), {}, [], 0
    for log in logs:
        role, channel = _failed_api_role(log.get('role')), log.get('channel')
        key = role, channel
        need(key in required and key not in seen and log.get('path') == role + '.' + channel + '.log',
             'failed_api_log_scope')
        seen.add(key)
        cap = 2097152 if channel == 'events' else 262144
        length, observed = _public_integer(log.get('bytes'), cap+1), _public_integer(log.get('observed_bytes'), 2**40)
        need(length <= observed and type(log.get('eof')) is bool, 'failed_api_log_shape')
        log_sha = _digest(log.get('sha256'))
        log_error = _failed_api_error(log.get('write_error'))
        try:
            data = read_relative(root, case_id + '/' + log['path'], cap+1)
        except FileNotFoundError:
            public['missing_records'].append(role + '_' + channel)
            continue
        need(len(data) == length and hashlib.sha256(data).hexdigest() == log_sha, 'failed_api_log_changed')
        public_logs.append({'role': role, 'channel': channel, 'sha256': log_sha, 'bytes': length,
                            'observed_bytes': observed, 'eof': log['eof'], 'write_error': log_error})
        if channel != 'events':
            continue
        total += length
        need(total <= 32*1024*1024+64, 'failed_api_total_events')
        rows = events[role]
        need(isinstance(rows, list) and len(rows) <= 16384 and all(isinstance(row, dict) for row in rows),
             'failed_api_event_bounds')
        decoded, invalid = [], 0
        for line in data.splitlines():
            try:
                item = decode_json(line, 32768)
                need(isinstance(item, dict), 'failed_api_event_object')
                decoded.append(item)
            except Error:
                invalid += 1
        if rows != decoded or invalid or data and not data.endswith(b'\n'):
            need(value.get('stream_error') is not None, 'failed_api_event_log_mismatch')
            public['missing_records'].append(role + '_complete_event_parse')
        histogram = {name: sum(item.get('event') == name for item in decoded) for name in sorted(FAILED_API_EVENTS)}
        histogram['unclassified'] = sum(item.get('event') not in FAILED_API_EVENTS for item in decoded)
        counts[role] = {'retained_event_count': len(decoded), 'events': histogram}
    public['missing_records'].extend(role + '_' + channel for role, channel in sorted(required-seen))
    public['logs'], public['event_counts'] = public_logs, counts
    public['pe_execution_qualified'] = False
    if not public['missing_records']:
        public['record_status'] = 'complete'
    return public


def summarize_failed_api_run(path):
    """Retain historical failures without executing old producers or reauthorizing them."""
    root = _failed_root(path)
    need(not (root / 'diagnostic-adapter.json').exists(), 'diagnostic_only_run')
    public = {'scope': 'historical_failed_instrumented_arm64_api_abi', 'passed': False,
              'record_status': 'partial', 'run_sha256': None, 'missing_records': [], 'cases': [],
              'runtime_qualified': False, 'pe_execution_qualified': False,
              'limits': ['Reported PE execution flags indicate guest-exit markers, not absence of PE entry.',
                         'Exit observations distinguish the pre-cleanup snapshot from final termination; causes are unqualified.',
                         'Historical hashes preserve evidence identity and do not renew signing authorization.']}
    try:
        raw = read_relative(root, 'run.json')
    except FileNotFoundError:
        public['missing_records'].append('run_record')
        return public
    value = record(decode_json(raw), 'wine_api_run')
    need(value.get('suite') == 'api-abi' and value.get('passed') is False and
         value.get('runtime_qualified') is False and type(value.get('pe_executed')) is bool, 'failed_api_run_scope')
    public.update(run_sha256=hashlib.sha256(raw).hexdigest(), error=_failed_api_error(value.get('error')),
                  reported_guest_exit_observed=value['pe_executed'])
    producers = value.get('producer_sha256')
    sources = PAGE_WX_API_SOURCES if value.get('code_publication_policy') == 'page-wx' else FAILED_API_SOURCES
    need(value.get('code_publication_policy') in (None, 'page-wx'), 'failed_api_policy_scope')
    if sources is PAGE_WX_API_SOURCES and isinstance(producers, dict) and set(producers) == set(RELOCATION_API_SOURCES):
        sources = RELOCATION_API_SOURCES
    need(isinstance(producers, dict) and set(producers) == set(sources) and
         value.get('cases_sha256') == producers['tests/wine/cases-stage3.json'], 'failed_api_source_scope')
    public['source_sha256'] = {}
    for name, label in sources.items():
        digest = _digest(producers[name])
        public['source_sha256'][label] = digest
        if not _historical_source(name, digest, root, archive_only=name == 'tools/wine/modules.py'):
            public['missing_records'].append('source_' + label)
    runtime = _failed_root(REPO.joinpath(*relative(value.get('runtime_path'))))
    signed_sha = _digest(value.get('signed_sha256'))
    try:
        signed_raw = read_relative(runtime, 'signed.json')
    except FileNotFoundError:
        public['missing_records'].append('signed_record')
    else:
        need(hashlib.sha256(signed_raw).hexdigest() == signed_sha, 'failed_api_signed_record_changed')
        signed = record(decode_json(signed_raw), 'wine_signed_runtime')
        need(signed.get('wine_execution') is False and signed.get('runtime_qualified') is False and
             signed.get('authorization_scope') == 'development_windows_api_abi_fixtures', 'failed_api_signed_scope')
        public['signed_record_sha256'] = signed_sha
        public['build_record_sha256'] = _digest(signed.get('build_ref', {}).get('sha256'))
        source = signed.get('producer_sha256')
        need(isinstance(source, dict) and set(source) == {'signing.py', 'common.py'}, 'failed_api_signer_scope')
        public['signer_source_sha256'] = {}
        for name, digest in source.items():
            label = 'signer' if name == 'signing.py' else 'common'
            public['signer_source_sha256'][label] = _digest(digest)
            if not _historical_source('tools/wine/' + name, digest, root, signing=True):
                public['missing_records'].append('source_' + label)
    rows = value.get('cases')
    need(isinstance(rows, list) and len(rows) <= 2 and all(isinstance(row, dict) for row in rows), 'failed_api_case_count')
    names = [row.get('id') for row in rows]
    need(names in ([], ['api'], ['api', 'abi']), 'failed_api_case_order')
    public['cases'] = [_summarize_failed_api_case(root, row, row['id']) for row in rows]
    public['retained_case_count'] = len(rows)
    public['unrecorded_cases'] = [name for name in ('api', 'abi') if name not in names]
    if not public['missing_records'] and all(case['record_status'] == 'complete' for case in public['cases']):
        public['record_status'] = 'complete'
    return public


NATIVE_ARENA_RECEIPT = 'offline-receipt-v3.json'
NATIVE_ARENA_FAILURES = (
    ('thread-jit-initial-rwx', '496911207993150d7e1cbc78eeff05878a06311a2b3930c34308656f716c2419'),
    ('thread-jit-initial-none', 'd941bc5c963c15bef7d5ece8cd36775c3598c3e980ee1dd22c24b32d193a6b01'),
)


def native_arena_prerequisites(paths):
    """Package reviewed historical receipts only after current pure validation.

    Require the two preserved failed policies followed by the selected native
    prerequisite. This reads retained bytes and never executes archived code,
    renews signing authorization, or substitutes for the actual Wine gates.
    """
    from arena_evidence import export as validate_native_arena
    need(len(paths) == 3, 'export_native_arena_coverage')
    roots = [_failed_root(path) for path in paths]
    need(len(set(roots)) == 3, 'export_native_arena_duplicate')
    expected = [*NATIVE_ARENA_FAILURES,
                ('page-wx', sha256(REPO / 'tests/wine/fixtures/pe_arena_native.c'))]
    attempts, reports = [], set()
    for index, (root, (ident, source_hash)) in enumerate(zip(roots, expected)):
        receipt_raw = read_relative(root, NATIVE_ARENA_RECEIPT)
        receipt_hash = hashlib.sha256(receipt_raw).hexdigest()
        receipt = decode_json(receipt_raw)
        observed = validate_native_arena(root)
        need(receipt == observed and sha256(root / NATIVE_ARENA_RECEIPT) == receipt_hash,
             'export_native_arena_receipt_changed')
        need(observed.get('record_kind') == 'pear_native_arena_observations' and
             observed.get('scope') == 'historical_native_prerequisite_receipt' and
             observed.get('source_sha256') == source_hash and
             observed.get('policy') == ('thread-jit' if index < 2 else 'page-wx') and
             observed.get('native_prerequisite_passed') is (index == 2) and
             observed.get('legacy_policy_interpretation') is (index < 2) and
             all(observed.get(key) is False for key in ('wine_execution', 'runtime_qualified', 'game_qualified')),
             'export_native_arena_scope')
        report_hash = _digest(observed.get('report_sha256'))
        need(report_hash not in reports, 'export_native_arena_duplicate_report')
        reports.add(report_hash)
        authorization = observed.get('authorization', {})
        need(authorization.get('scope') == 'recorded_at_run_not_reauthorized' and
             authorization.get('profile_byte_hash_binding') == 'unavailable_not_retained_at_run' and
             authorization.get('bundle_metadata_byte_binding') == 'unavailable_not_retained_at_run' and
             authorization.get('current_profile_authorization_assessed') is False and
             authorization.get('current_bundle_signature_verified') is False,
             'export_native_arena_authorization_scope')
        attempts.append({'id': ident, 'retained_receipt_sha256': receipt_hash, 'observations': observed})
    return {'scope': 'historical_native_prerequisite_only', 'selected_policy': 'page-wx', 'attempts': attempts}


def export_stage3(build_root, runs_root, bootstrap_root, failed_api_runs=(), native_arena_runs=()):
    """Bind both executed suites, signed origins and finite assembly inspection."""
    from build import artifact_inventory, verify_build
    from api_runner import validate_runs as validate_api_runs
    from run_fixtures import validate_runs
    from signing import validate_prepared
    from abi_review import inspect_build
    root, runs_root, bootstrap_root = [_failed_root(path) for path in (build_root, runs_root, bootstrap_root)]
    need(not (runs_root / 'diagnostic-adapter.json').exists(), 'diagnostic_only_run')
    build_digest = sha256(root / 'build.json')
    built = verify_build(root)
    need(bound_record(root / 'build.json', build_digest, 'wine_build') == built and
         built.get('fixture_suite') == 'api-abi' and built.get('variant') == 'arm64' and
         built.get('code_publication_policy') == 'page-wx', 'export_build_scope')
    api, bootstrap = validate_api_runs(runs_root), validate_runs(bootstrap_root, 'bootstrap')
    api_record = bound_record(runs_root / 'run.json', api['run_sha256'], 'wine_api_run')
    bootstrap_record = bound_record(bootstrap_root / 'run.json', bootstrap['run_sha256'], 'wine_bootstrap_run')
    need(api['signed_sha256'] == bootstrap['signed_sha256'] and
         api_record['signed_sha256'] == bootstrap_record['signed_sha256'] == api['signed_sha256'],
         'export_mixed_signed_runtime')
    runtime = _failed_root(REPO.joinpath(*relative(api_record['runtime_path'])))
    need(_failed_root(REPO.joinpath(*relative(bootstrap_record['runtime_path']))) == runtime,
         'export_mixed_runtime_roots')
    signed = validate_prepared(runtime)
    need(bound_record(runtime / 'signed.json', api['signed_sha256'], 'wine_signed_runtime') == signed,
         'export_evidence_changed')
    need(signed['build_ref']['sha256'] == build_digest and
         Path(signed['build_ref']['path']).resolve() == root / 'build.json', 'tested_build_mismatch')
    review_digest = sha256(root / 'abi-review.json')
    review = inspect_build(root)
    need(bound_record(root / 'abi-review.json', review_digest, 'wine_abi_assembly_review') == review,
         'export_assembly_evidence_changed')
    assembly = _stage3_assembly(review, build_digest)
    artifacts = artifact_inventory(built, root)
    native_count = sum(row['kind'] == 'macho' for row in artifacts['files'])
    pe_count = sum(row['kind'] == 'pe' for row in artifacts['files'])
    need(native_count == built['native_artifact_count'] and pe_count == built['pe_artifact_count'],
         'export_artifact_coverage')
    sdk = built['sdk']
    need(isinstance(sdk.get('version'), str) and re.fullmatch(r'[0-9]+(?:\.[0-9]+){1,3}', sdk['version']) and
         sdk.get('canonical_name') == 'macosx' + sdk['version'], 'export_sdk_shape')
    public = {'schema_version': 1, 'record_kind': 'wine_stage3_observations',
        'scope': 'development_arm64_windows_api_and_nested_wine_abi_fixtures',
        'build': {'build_sha256': build_digest, 'variant': 'arm64', 'fixture_suite': 'api-abi',
                  'code_publication_policy': 'page-wx',
                  'native_artifact_count': _public_integer(native_count), 'pe_artifact_count': _public_integer(pe_count),
                  'metadata_container_count': sum(row['kind'] == 'pe_metadata' for row in artifacts['files']),
                  'ordered_patch_sha256': [_digest(row.get('sha256')) for row in built['patches']],
                  'commands': _stage3_commands(built)},
        'signed_sha256': _digest(api['signed_sha256']), 'assembly_review_sha256': review_digest,
        'assembly_review': assembly, 'run_assessments': _stage3_runs(api, bootstrap),
        'failed_api_runs': [summarize_failed_api_run(path) for path in failed_api_runs],
        'native_arena_prerequisites': native_arena_prerequisites(native_arena_runs),
        'authorization': _stage3_authorization(signed, native_count),
        'sdk': {'version': sdk['version'], 'canonical_name': sdk['canonical_name'],
                'settings_sha256': _digest(sdk.get('settings_sha256'))},
        'reviewed_source_hashes': {label: sha256(REPO / name) for label, name in STAGE3_SOURCES.items()},
        'pe_execution': True, 'guest_x18_execution': True, 'translator_execution': False,
        'game_execution': False, 'runtime_qualified': False, 'distribution_qualified': False,
        'limits': ['Same-host, development-authorized ARM64 fixtures; no x64/i386 translator or game qualification.',
                   'The six-entry assembly checker is finite; arbitrary signal, exception and unwind behavior is unqualified.',
                   'Instrumented descendants retain the owned root process group; general application ownership is unqualified.',
                   'Native loaded-image snapshots do not constitute a complete library-load timeline.',
                   'Callback lifetime checks use a stable single-thread table and a pinned main-executable continuation; unloadable continuations and concurrent table mutation are unqualified.',
                   'Protection-fault, exhaustion and interrupted-preparation controls belong to the standalone native prerequisite, not integrated Wine execution.',
                   'Private identities, signing materials, paths and raw logs remain in ignored local records.']}
    need(validate_prepared(runtime) == signed and sha256(root / 'build.json') == build_digest and
         sha256(root / 'abi-review.json') == review_digest and
         sha256(runs_root / 'run.json') == api['run_sha256'] and
         sha256(bootstrap_root / 'run.json') == bootstrap['run_sha256'], 'export_evidence_changed')
    return public


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('1', '2', '3'), default='1')
    parser.add_argument('--inputs')
    parser.add_argument('--config')
    parser.add_argument('--toolchain')
    parser.add_argument('--build')
    parser.add_argument('--companion')
    parser.add_argument('--runs')
    parser.add_argument('--bootstrap-runs')
    parser.add_argument('--failed-build', action='append', default=[])
    parser.add_argument('--failed-run', action='append', default=[])
    parser.add_argument('--failed-api-run', action='append', default=[])
    parser.add_argument('--native-arena-run', action='append', default=[],
                        help='Stage 3: three retained arena run directories in failed RWX, failed NONE, then page-W^X order; each contains offline-receipt-v3.json.')
    parser.add_argument('--output', required=True)
    parser.add_argument('--failed-attempt', action='append', default=[])
    args = parser.parse_args(argv)
    try:
        if args.stage == '1':
            need(all((args.inputs, args.config, args.toolchain)) and not any((args.build, args.companion, args.runs, args.bootstrap_runs, args.failed_build, args.failed_run, args.failed_api_run, args.native_arena_run)), 'export_stage_arguments')
            result = export(args.inputs, args.config, args.toolchain, args.failed_attempt)
        elif args.stage == '2':
            need(all((args.build, args.companion, args.runs)) and not any((args.inputs, args.config, args.toolchain, args.failed_attempt, args.bootstrap_runs, args.failed_api_run, args.native_arena_run)), 'export_stage_arguments')
            result = export_stage2(args.build, args.companion, args.runs, args.failed_build, args.failed_run)
        else:
            need(all((args.build, args.runs, args.bootstrap_runs)) and len(args.native_arena_run) == 3 and not any((args.inputs, args.config, args.toolchain, args.companion, args.failed_attempt, args.failed_build, args.failed_run)), 'export_stage_arguments')
            result = export_stage3(args.build, args.runs, args.bootstrap_runs, args.failed_api_run, args.native_arena_run)
        path = Path(args.output)
        need(path.resolve().is_relative_to(REPO / 'mydocs/working') and not path.exists(), 'export_destination')
        with path.open('xb') as stream:
            stream.write(encoded(result))
    except (Error, OSError, ValueError, KeyError, TypeError) as exc:
        print(encoded({'error': getattr(exc, 'code', 'evidence_export_failed')}).decode(), end='')
        return 1
    print('Sanitized Stage ' + args.stage + ' evidence exported after local gate validation.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
