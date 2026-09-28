"""Export allowlisted scoped facts after validating their local raw evidence."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
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


def _historical_source(name, digest, failed_root, signing=False):
    """Find exact bytes, never execute archived producers or infer current grants."""
    _digest(digest)
    candidates = [REPO / name, failed_root / 'producer' / name]
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('1', '2'), default='1')
    parser.add_argument('--inputs')
    parser.add_argument('--config')
    parser.add_argument('--toolchain')
    parser.add_argument('--build')
    parser.add_argument('--companion')
    parser.add_argument('--runs')
    parser.add_argument('--failed-build', action='append', default=[])
    parser.add_argument('--failed-run', action='append', default=[])
    parser.add_argument('--output', required=True)
    parser.add_argument('--failed-attempt', action='append', default=[])
    args = parser.parse_args(argv)
    try:
        if args.stage == '1':
            need(all((args.inputs, args.config, args.toolchain)) and not any((args.build, args.companion, args.runs, args.failed_build, args.failed_run)), 'export_stage_arguments')
            result = export(args.inputs, args.config, args.toolchain, args.failed_attempt)
        else:
            need(all((args.build, args.companion, args.runs)) and not any((args.inputs, args.config, args.toolchain, args.failed_attempt)), 'export_stage_arguments')
            result = export_stage2(args.build, args.companion, args.runs, args.failed_build, args.failed_run)
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
