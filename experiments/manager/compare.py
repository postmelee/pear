"""Measure the frozen native-manager experiment; never qualify a game runtime."""
import argparse
import contextlib
import copy
import datetime
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as native_build
import run_cases as corpus

REPO = HERE.parents[1]
CANDIDATES = ('rust', 'swift')
FORBIDDEN = ('/Users/', '/private/', '/var/folders/', 'PRIVATE_FIXTURE_MARKER', 'PEAR_SECRET_SENTINEL')
HISTORICAL_EVIDENCE = ('prior-comparison-attempts.json', 'fixture-input-revision.json', 'comparison-before-revision2.json', 'final-corpus-before-revision2.json', 'startup-diagnostics-before-revision2.json', 'fixture-input-revision2.json')


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def inventory():
    selected = [HERE / p for p in ['build.py', 'run_cases.py', 'compare.py', 'comparison-plan.json', 'dependencies.json']]
    selected.extend(REPO / path for path in ['tests/contracts/validate.py', 'tests/contracts/fixture_factory.py', 'tests/contracts/requirements.lock', 'tests/contracts/dependencies.json', 'runtime/contracts/contract-index.json'])
    selected.extend((REPO / 'runtime/contracts/v1').glob('*.json'))
    for directory in ['rust', 'swift', 'fixtures']:
        selected.extend(p for p in (HERE / directory).rglob('*') if p.is_file() and not any(x.startswith('.') or x == '__pycache__' for x in p.relative_to(HERE).parts))
    return {str(p.relative_to(REPO)): sha(p) for p in sorted(selected)}


def stats(values):
    if not values:
        return {'count': 0, 'median': None, 'min': None, 'max': None}
    return {'count': len(values), 'median': statistics.median(values), 'min': min(values), 'max': max(values)}


def summaries(samples):
    return {candidate: {phase: {
        'duration_seconds': stats([r['duration_seconds'] for r in samples if r['candidate'] == candidate and r['phase'] == phase and r['passed']]),
        'peak_rss_bytes': stats([r['peak_rss_bytes'] for r in samples if r['candidate'] == candidate and r['phase'] == phase and r['passed'] and r['peak_rss_bytes'] is not None]),
    } for phase in ['clean', 'incremental', 'warmup', 'launch']} for candidate in CANDIDATES}


def load_plan(path):
    plan = json.loads(Path(path).read_bytes())
    if plan.get('status') != 'frozen_before_stage4' or plan.get('version') != 1:
        raise ValueError('unrecognized_frozen_plan')
    builds, launches = plan['build_samples'], plan['launch_samples']
    if (builds['clean_per_candidate'], builds['incremental_per_candidate'], launches['warmups_per_candidate'], launches['recorded_per_candidate']) != (3, 3, 5, 30):
        raise ValueError('unexpected_sample_plan')
    if builds['order'] != ['rust', 'swift', 'swift', 'rust', 'rust', 'swift'] or builds['incremental_order'] != ['swift', 'rust', 'rust', 'swift', 'swift', 'rust']:
        raise ValueError('unexpected_build_order')
    if launches['mode'] != 'success' or launches['timeout_ms'] != 1500 or launches['output_limit'] != 4096 or launches['fresh_bundle_each_time'] is not True:
        raise ValueError('unexpected_launch_plan')
    functional = json.loads((HERE / 'fixtures/cases.json').read_bytes())
    if functional['outer_deadline_seconds'] != 10 or 5000 + 2000 >= functional['outer_deadline_seconds'] * 1000:
        raise ValueError('functional_outer_budget_changed')
    for case in functional['cases']:
        expected_timeout = 1500 if case['id'] in ['timeout', 'descendant_pipe'] else 5000
        if case['timeout_ms'] != expected_timeout:
            raise ValueError('functional_budget_changed')
    manifest = native_build.tomllib.loads((HERE / 'rust/Cargo.toml').read_text())
    if manifest['profile']['release'] != {'opt-level': 3, 'lto': False, 'codegen-units': 1, 'panic': 'abort'}:
        raise ValueError('optimization_changed')
    for edit in builds['incremental_edits']:
        if edit['old'] != '// Stage 4 incremental marker: baseline' or edit['replacements'] != [f'// Stage 4 incremental marker: sample-{i}' for i in range(1, 4)]:
            raise ValueError('incremental_edit_changed')
        if (HERE / edit['path']).read_text().count(edit['old']) != 1:
            raise ValueError('incremental_marker_not_unique')
    return plan


def measured_command(argv, cwd, env, log, timeout):
    """Bound local capture and obtain per-waited-command Darwin rusage.

    Do not poll Popen: wait4 must retain this exact child's exit accounting.
    The leader remains unreaped until its owned group is signaled on watchdog failure.
    """
    log.parent.mkdir(parents=True, exist_ok=True)
    stdout_path, stderr_path = log.with_suffix('.stdout'), log.with_suffix('.stderr')
    failure, usage = None, None
    limit = 8 * 1024 * 1024
    with stdout_path.open('wb') as out, stderr_path.open('wb') as err:
        started = time.perf_counter_ns()
        process = subprocess.Popen([str(v) for v in argv], cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=True)

        def terminate_owned():
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except PermissionError:
                process.kill()
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                pid, status, result_usage = os.wait4(process.pid, os.WNOHANG)
                if pid:
                    process.returncode = os.waitstatus_to_exitcode(status)
                    return result_usage
                time.sleep(.001)
            return None

        try:
            while True:
                pid, status, usage = os.wait4(process.pid, os.WNOHANG)
                if pid:
                    process.returncode = os.waitstatus_to_exitcode(status)
                    break
                if time.perf_counter_ns() - started > timeout * 1e9:
                    failure = 'outer_deadline'
                if max(stdout_path.stat().st_size, stderr_path.stat().st_size) > limit:
                    failure = 'outer_output_limit'
                if failure:
                    usage = terminate_owned()
                    if usage is None:
                        failure = 'cleanup_unverified'
                    break
                time.sleep(.001)
        except BaseException as error:
            # Retain the failed attempt and attempt bounded reaping of the exact leader.
            failure = 'interrupted' if isinstance(error, KeyboardInterrupt) else 'execution_error'
            usage = terminate_owned()
            if usage is None:
                failure = 'cleanup_unverified'
        elapsed = (time.perf_counter_ns() - started) / 1e9
    # A process can exit between polling and a final burst; check final sizes too.
    oversized = max(stdout_path.stat().st_size, stderr_path.stat().st_size) > limit
    if oversized:
        failure = 'outer_output_limit'
    result = {
        'duration_seconds': elapsed,
        'peak_rss_bytes': int(usage.ru_maxrss) if usage is not None and sys.platform == 'darwin' else None,
        'returncode': process.returncode,
        'watchdog': failure,
        'stdout_sha256': sha(stdout_path) if stdout_path.stat().st_size <= limit else None,
        'stderr_sha256': sha(stderr_path) if stderr_path.stat().st_size <= limit else None,
    }
    log.with_suffix('.json').write_text(json.dumps({'argv': [str(v) for v in argv], 'cwd': str(cwd), **result}, indent=2) + '\n')
    with stdout_path.open('rb') as stream:
        stdout = stream.read(limit + 1)
    with stderr_path.open('rb') as stream:
        stderr = stream.read(limit + 1)
    return result, stdout, stderr


def plain_command(argv, env):
    result = subprocess.run([str(v) for v in argv], env=env, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ValueError('host_inspection_failed')
    return result.stdout.strip()


def host_snapshot(env):
    battery = plain_command(['pmset', '-g', 'batt'], env)
    source = re.search(r"Now drawing from '([^']+)'", battery)
    percentage = re.search(r'(\d+)%;', battery)
    settings = plain_command(['pmset', '-g', 'custom'], env)
    low_power = re.findall(r'lowpowermode\s+(\d+)', settings)
    therm = subprocess.run(['pmset', '-g', 'therm'], env=env, capture_output=True, text=True, timeout=15)
    thermal = {key: int(value) for key, value in re.findall(r'(CPU_Speed_Limit|CPU_Available_CPUs|CPU_Scheduler_Limit)\s*=\s*(\d+)', therm.stdout)}
    return {'power_source': source.group(1) if source else 'unknown',
            'battery_percent': int(percentage.group(1)) if percentage else None,
            'configured_low_power_modes': [int(v) for v in low_power],
            'thermal_limits': thermal,
            'thermal_detail': 'Only available numeric pmset limits recorded; no sensor, temperature or power measurement.'}


def tokenized(argv, run_root):
    replacements = [(str(run_root), '<run>'), (str(HERE), '<experiment>'), (str(REPO), '<repo>'), (str(Path.home()), '<home>')]
    result = []
    for arg in map(str, argv):
        for actual, token in replacements:
            arg = arg.replace(actual, token)
        result.append(arg)
    return result


def tree_bytes(path):
    return sum(p.stat().st_size for p in Path(path).rglob('*') if p.is_file() and not p.is_symlink())


def build_command(candidate, source, output, bridge, env):
    candidate_env = env.copy()
    if candidate == 'rust':
        for ancestor in [source, *source.parents]:
            if any((ancestor / '.cargo' / name).exists() or (ancestor / '.cargo' / name).is_symlink() for name in ['config', 'config.toml']):
                raise ValueError('ambient_measurement_cargo_configuration')
        candidate_env.update(CARGO_TARGET_DIR=str(output), RUSTC=str(Path.home() / '.cargo/bin/rustc'), CARGO_ENCODED_RUSTFLAGS='\x1f'.join(['-C', 'link-arg=' + str(bridge), '-C', 'link-arg=-lproc']))
        command = ['cargo', 'build', '--manifest-path', source / 'Cargo.toml', '--locked', '--offline', '--release', '--target', 'aarch64-apple-darwin', '--verbose']
        binary = output / 'aarch64-apple-darwin/release/pear-manager'
    else:
        command = ['xcrun', 'swift', 'build', '--package-path', source, '-c', 'release', '--scratch-path', output, '--triple', 'arm64-apple-macosx26.0', '-Xlinker', bridge, '-Xlinker', '-lproc', '--verbose']
        binary = output / 'arm64-apple-macosx/release/pear-manager-swift'
    return command, candidate_env, binary


def native_inputs(source):
    return {str(p.relative_to(source)): sha(p) for p in sorted(source.rglob('*')) if p.is_file() and not any(x.startswith('.') for x in p.relative_to(source).parts)}


def inspect_packaging(binary, env, log):
    observations = []
    for command in [['vtool', '-show-build', binary], ['codesign', '--verify', '--strict', '--verbose=2', binary], ['codesign', '--display', '--verbose=4', binary], ['otool', '-l', binary]]:
        result = subprocess.run([str(v) for v in command], env=env, capture_output=True, text=True, timeout=30)
        observations.append({'argv': [str(v) for v in command], 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    log.write_text(json.dumps(observations, indent=2) + '\n')
    if any(row['returncode'] for row in observations):
        raise ValueError('packaging_inspection_failed')
    versions = observations[0]['stdout']
    signing = observations[2]['stderr']
    def value(pattern, content):
        found = re.search(pattern, content, re.MULTILINE)
        return found.group(1) if found else None
    rpaths = re.findall(r'cmd LC_RPATH\s+cmdsize \d+\s+path (.*?) \(offset \d+\)', observations[3]['stdout'])
    if any(not path.startswith(('@loader_path', '@executable_path', '/usr/lib/', '/System/Library/')) for path in rpaths):
        raise ValueError('unexpected_binary_rpath')
    return {'platform': value(r'platform (\S+)', versions), 'minimum_macos': value(r'minos (\S+)', versions), 'sdk': value(r'sdk (\S+)', versions),
            'rpaths': rpaths, 'codesign_strict_verify_exit': observations[1]['returncode'], 'signature': value(r'^Signature=(.*)$', signing),
            'linker_signed': 'linker-signed' in signing, 'team_identifier_present': 'TeamIdentifier=not set' not in signing,
            'inspection_log_sha256': sha(log), 'distribution_qualified': False,
            'signing_scope': 'Read-only verification of the linker-generated signature. No signing mutation, Developer ID, provisioning, notarization or application-bundle qualification.'}


def full_gate(build_root, oracle, output):
    with output.open('w') as log, contextlib.redirect_stdout(log):
        result = corpus.run_cases(build_root, oracle)
    return {'passed': result['passed'], 'case_count': result['case_count'], 'execution_count': result['execution_count'], 'report_sha256': sha(build_root / 'case-results.json'),
            'native_observations': all(r['result'].get('host_architecture') == 'arm64' and r['result'].get('translated') is False for r in result['results']),
            'privacy_and_bounds': all(not r['errors'] and r['bounded_completion'] for r in result['results']),
            'unrelated_sentinel_alive': all(r['unrelated_sentinel_alive'] for r in result['results'])}


def expected_source_identity(candidate, phase, number, plan):
    source = HERE / candidate
    result = native_inputs(source)
    if phase == 'incremental':
        edit = next(e for e in plan['build_samples']['incremental_edits'] if e['candidate'] == candidate)
        relative = str(Path(edit['path']).relative_to(candidate))
        replaced = (source / relative).read_text().replace(edit['old'], edit['replacements'][number - 1])
        result[relative] = hashlib.sha256(replaced.encode()).hexdigest()
    return result


def validate_report(report, plan, check_inputs=True):
    """Check sample accounting and arithmetic, never infer validity from a label."""
    errors = []
    if not isinstance(report, dict):
        return ['report_shape']
    required = {'version', 'fixture_only', 'runtime_eligible', 'status', 'plan_sha256', 'source_sha256', 'host', 'toolchains', 'conditions', 'gates', 'preparation', 'samples', 'summary', 'payload', 'limitations', 'failures', 'prior_attempts', 'historical_evidence'}
    if set(report) != required:
        errors.append('report_shape')
    if report.get('version') != 1 or type(report.get('version')) is not int or report.get('fixture_only') is not True or report.get('runtime_eligible') is not False:
        errors.append('report_scope')
    if report.get('status') != 'completed' or report.get('failures'):
        errors.append('incomplete_or_failed_run')
    if any(marker in json.dumps(report) for marker in FORBIDDEN):
        errors.append('private_data')
    if check_inputs and (report.get('plan_sha256') != sha(HERE / 'comparison-plan.json') or report.get('source_sha256') != inventory()):
        errors.append('source_identity_changed')
    samples = report.get('samples', [])
    if not isinstance(samples, list) or any(not isinstance(row, dict) for row in samples):
        return sorted(set(errors + ['sample_shape']))
    if len(samples) != 82:
        errors.append('sample_count')
    expected = [('clean', c) for c in plan['build_samples']['order']] + [('incremental', c) for c in plan['build_samples']['incremental_order']] + [(phase, c) for phase, count in [('warmup', 5), ('launch', 30)] for _ in range(count) for c in CANDIDATES]
    if [(r.get('phase'), r.get('candidate')) for r in samples] != expected:
        errors.append('sample_order')
    numbered = {}
    common_keys = {'sequence', 'phase', 'candidate', 'number', 'passed', 'command', 'binary_sha256', 'duration_seconds', 'peak_rss_bytes', 'returncode', 'watchdog', 'stdout_sha256', 'stderr_sha256'}
    build_keys = common_keys | {'build_environment', 'source_sha256', 'rebuild_observed'}
    launch_keys = common_keys | {'oracle_eligible', 'owned_identity_gone', 'native', 'fresh_bundle', 'sentinel_alive', 'errors'}
    for index, row in enumerate(samples):
        phase, candidate = row.get('phase'), row.get('candidate')
        identity = (phase, candidate)
        numbered[identity] = numbered.get(identity, 0) + 1
        if row.get('number') != numbered[identity] or type(row.get('number')) is not int:
            errors.append('sample_number')
        if set(row) != (build_keys if phase in ['clean', 'incremental'] else launch_keys):
            errors.append('sample_shape')
        for key in ['binary_sha256', 'stdout_sha256', 'stderr_sha256']:
            if not isinstance(row.get(key), str) or not re.fullmatch('[0-9a-f]{64}', row[key]):
                errors.append('sample_digest')
        if row.get('sequence') != index + 1 or row.get('passed') is not True or row.get('returncode') != 0 or row.get('watchdog') is not None:
            errors.append('invalid_attempt')
        duration = row.get('duration_seconds')
        if type(duration) not in (int, float) or not math.isfinite(duration) or duration <= 0:
            errors.append('invalid_duration')
        rss = row.get('peak_rss_bytes')
        if rss is not None and (type(rss) is not int or rss <= 0):
            errors.append('invalid_memory')
        if row.get('phase') in ['clean', 'incremental'] and (not row.get('rebuild_observed') or not row.get('source_sha256') or not re.fullmatch('[0-9a-f]{64}', row.get('binary_sha256', ''))):
            errors.append('missing_build_evidence')
        if check_inputs and phase in ['clean', 'incremental'] and candidate in CANDIDATES and 1 <= numbered[identity] <= 3:
            if row.get('source_sha256') != expected_source_identity(candidate, phase, numbered[identity], plan):
                errors.append('sample_source_identity')
        if phase in ['warmup', 'launch']:
            command = row.get('command')
            if not isinstance(command, list) or command.count('--timeout-ms') != 1:
                errors.append('scored_launch_budget')
            else:
                position = command.index('--timeout-ms')
                if position + 1 >= len(command) or command[position + 1] != str(plan['launch_samples']['timeout_ms']):
                    errors.append('scored_launch_budget')
            last_clean = [r for r in samples if r.get('phase') == 'clean' and r.get('candidate') == candidate and r.get('number') == 3]
            payload = report.get('payload', {}).get(candidate, {})
            if len(last_clean) != 1 or row.get('binary_sha256') != last_clean[0].get('binary_sha256') or row.get('binary_sha256') != payload.get('binary_sha256'):
                errors.append('launch_binary_identity')
            if row.get('errors') != []:
                errors.append('launch_errors')
        if row.get('phase') in ['warmup', 'launch'] and (row.get('oracle_eligible') is not True or row.get('owned_identity_gone') is not True or row.get('native') is not True or row.get('fresh_bundle') is not True or row.get('sentinel_alive') is not True):
            errors.append('invalid_launch_evidence')
    try:
        if report.get('summary') != summaries(samples):
            errors.append('summary_arithmetic')
    except (TypeError, KeyError, statistics.StatisticsError):
        errors.append('summary_invalid')
    for name in ['before', 'after']:
        gate = report.get('gates', {}).get(name, {})
        if set(gate) != {'passed', 'case_count', 'execution_count', 'report_sha256', 'native_observations', 'privacy_and_bounds', 'unrelated_sentinel_alive'} or not isinstance(gate.get('report_sha256'), str) or not re.fullmatch('[0-9a-f]{64}', gate.get('report_sha256', '')):
            errors.append('functional_gate_evidence')
        if any(gate.get(key) is not True for key in ['passed', 'native_observations', 'privacy_and_bounds', 'unrelated_sentinel_alive']) or gate.get('case_count') != 55 or gate.get('execution_count') != 110:
            errors.append('functional_gate')
    if set(report.get('gates', {})) != {'before', 'after'}:
        errors.append('functional_gate_shape')
    conditions = report.get('conditions', {})
    before, after = conditions.get('before', {}), conditions.get('after', {}) or {}
    if before.get('power_source') not in ['AC Power', 'Battery Power'] or before.get('power_source') != after.get('power_source') or before.get('configured_low_power_modes') != after.get('configured_low_power_modes'):
        errors.append('power_condition')
    expected_budgets = {'functional_budget_ms': 5000, 'intentional_timeout_budget_ms': 1500, 'scored_launch_budget_ms': 1500, 'cleanup_budget_ms': 2000, 'outer_budget_seconds': 10}
    if any(type(conditions.get(key)) is not int or conditions.get(key) != value for key, value in expected_budgets.items()):
        errors.append('declared_budgets')
    if conditions.get('coordinator_exclusive_heavy_work_window') is not True:
        errors.append('measurement_window')
    for candidate in CANDIDATES:
        payload = report.get('payload', {}).get(candidate, {})
        if payload.get('native_slices') != ['arm64'] or type(payload.get('manager_binary_bytes')) is not int or payload.get('manager_binary_bytes', 0) <= 0 or payload.get('standalone_distribution_payload_bytes') != payload.get('manager_binary_bytes'):
            errors.append('payload_identity')
    for candidate in CANDIDATES:
        payload = report.get('payload', {}).get(candidate, {})
        required_payload = {'manager_binary_bytes', 'standalone_distribution_payload_bytes', 'binary_sha256', 'native_slices', 'system_dynamic_dependencies', 'signed_app_bundle_bytes', 'signed_app_bundle_reason', 'packaging_inspection'}
        if set(payload) != required_payload:
            errors.append('packaging_fields')
        dependencies = payload.get('system_dynamic_dependencies')
        if not isinstance(dependencies, list) or not dependencies or any(not isinstance(v, str) or not v.startswith(('/usr/lib/', '/System/Library/')) for v in (dependencies or [])):
            errors.append('dynamic_dependencies')
        inspection = payload.get('packaging_inspection', {})
        required_inspection = {'platform', 'minimum_macos', 'sdk', 'rpaths', 'codesign_strict_verify_exit', 'signature', 'linker_signed', 'team_identifier_present', 'inspection_log_sha256', 'distribution_qualified', 'signing_scope'}
        if not isinstance(inspection, dict) or set(inspection) != required_inspection:
            errors.append('packaging_evidence')
        else:
            if inspection['platform'] != 'MACOS' or inspection['minimum_macos'] != '26.0' or inspection['sdk'] != report.get('toolchains', {}).get('sdk'):
                errors.append('packaging_target')
            if type(inspection['codesign_strict_verify_exit']) is not int or inspection['codesign_strict_verify_exit'] != 0 or inspection['signature'] != 'adhoc' or inspection['linker_signed'] is not True or inspection['team_identifier_present'] is not False or inspection['distribution_qualified'] is not False:
                errors.append('signature_scope')
            if not isinstance(inspection['inspection_log_sha256'], str) or not re.fullmatch('[0-9a-f]{64}', inspection['inspection_log_sha256']):
                errors.append('packaging_digest')
            if not isinstance(inspection['rpaths'], list) or any(not isinstance(v, str) or not v.startswith(('@loader_path', '@executable_path', '/usr/lib/', '/System/Library/')) for v in inspection['rpaths']):
                errors.append('packaging_rpaths')
    attempts = report.get('prior_attempts')
    if not isinstance(attempts, list):
        errors.append('prior_attempts')
    else:
        for attempt in attempts:
            required_attempt = {'retained_local_report', 'report_sha256', 'status', 'recorded_sample_count', 'plan_sha256', 'runner_sha256', 'failures', 'failed_cases'}
            if not isinstance(attempt, dict) or set(attempt) != required_attempt:
                errors.append('prior_attempts')
                continue
            if attempt['status'] not in ['failed', 'completed'] or type(attempt['recorded_sample_count']) is not int or attempt['recorded_sample_count'] < 0 or not isinstance(attempt['failures'], list) or not isinstance(attempt['failed_cases'], list):
                errors.append('prior_attempts')
            if not isinstance(attempt['retained_local_report'], str) or not re.fullmatch(r'\.build/task3/comparison-[a-z0-9_]+/comparison\.json', attempt['retained_local_report']):
                errors.append('prior_attempt_path')
            if any(not isinstance(attempt[key], str) or not re.fullmatch('[0-9a-f]{64}', attempt[key]) for key in ['report_sha256', 'plan_sha256', 'runner_sha256']):
                errors.append('prior_attempt_digest')
    history = report.get('historical_evidence', {})
    expected_history = set(HISTORICAL_EVIDENCE)
    if not isinstance(history, dict) or set(history) != expected_history:
        errors.append('historical_evidence')
    else:
        for name, reference in history.items():
            if not isinstance(reference, dict) or set(reference) != {'path', 'sha256'} or reference.get('path') != 'results/' + name or not isinstance(reference.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', reference.get('sha256', '')):
                errors.append('historical_reference')
            elif check_inputs and (not (HERE / reference['path']).is_file() or sha(HERE / reference['path']) != reference['sha256']):
                errors.append('historical_identity')
    return sorted(set(errors))


def prior_attempts(build_parent):
    result = []
    for path in sorted(build_parent.glob('comparison-*/comparison.json')):
        previous = json.loads(path.read_bytes())
        if previous.get('version') != 1 or previous.get('fixture_only') is not True or previous.get('status') not in ['completed', 'failed']:
            raise ValueError('unrecognized_prior_attempt')
        failed_cases = []
        for name in ['gate-before.jsonl', 'gate-after.jsonl']:
            log = path.parent / 'logs' / name
            if log.is_file():
                for line in log.read_text().splitlines():
                    row = json.loads(line)
                    if row.get('passed') is False:
                        failed_cases.append({'gate': name, 'case': row['case'], 'candidate': row['candidate'], 'errors': row['errors']})
        result.append({'retained_local_report': str(path.relative_to(REPO)), 'report_sha256': sha(path), 'status': previous['status'], 'recorded_sample_count': len(previous['samples']),
                       'plan_sha256': previous['plan_sha256'], 'runner_sha256': previous['source_sha256']['experiments/manager/compare.py'],
                       'failures': previous['failures'], 'failed_cases': failed_cases})
    return result


def compare(plan_path, build_root, output):
    plan_path, build_root, output = plan_path.resolve(), build_root.resolve(), output.resolve()
    plan = load_plan(plan_path)
    baseline = corpus.verify_build(build_root)
    native_build.verify_lock()
    env = native_build.controlled_environment()
    actual_toolchains = {name: plain_command(command, env) for name, command in {
        'clang': ['xcrun', 'clang', '--version'], 'sdk': ['xcrun', '--show-sdk-version'],
        'rustc': ['rustc', '--version', '--verbose'], 'cargo': ['cargo', '--version'],
        'swift': ['xcrun', 'swift', '--version'], 'xcode': ['xcodebuild', '-version'],
        'macos': ['sw_vers'], 'machine': ['uname', '-m'],
    }.items()}
    if actual_toolchains != baseline['toolchains']:
        raise ValueError('toolchain_changed_rebuild_baseline')
    oracle = REPO / '.build/task3/venv/bin/python'
    if not oracle.is_file():
        raise ValueError('oracle_missing')
    run_root = Path(tempfile.mkdtemp(prefix='comparison-', dir=build_root.parent))
    (run_root / 'logs').mkdir()
    shutil.copy2(HERE / 'compare.py', run_root / 'compare.py')
    baseline_sources = inventory()
    report = {'version': 1, 'fixture_only': True, 'runtime_eligible': False, 'status': 'running',
              'plan_sha256': sha(plan_path), 'source_sha256': baseline_sources,
              'host': {'architecture': plain_command(['uname', '-m'], env), 'chip': plain_command(['sysctl', '-n', 'machdep.cpu.brand_string'], env), 'memory_bytes': int(plain_command(['sysctl', '-n', 'hw.memsize'], env)), 'macos': baseline['toolchains']['macos']},
              'toolchains': actual_toolchains, 'conditions': {'before': host_snapshot(env), 'after': None, 'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'finished_at_utc': None, 'coordinator_exclusive_heavy_work_window': True, 'functional_budget_ms': 5000, 'intentional_timeout_budget_ms': 1500, 'scored_launch_budget_ms': 1500, 'cleanup_budget_ms': 2000, 'outer_budget_seconds': 10},
              'gates': {}, 'preparation': [], 'samples': [], 'summary': {}, 'payload': {}, 'failures': [], 'prior_attempts': prior_attempts(build_root.parent), 'historical_evidence': {name: {'path': 'results/' + name, 'sha256': sha(HERE / 'results' / name)} for name in HISTORICAL_EVIDENCE},
              'limitations': [
                  'Native fixture managers only; no game FPS, game power, Steam, Wine, translator or production distribution evidence.',
                  'Build durations cover candidate native build commands with verbose compiler evidence capture; shared C compilation is separately recorded preparation. Dependency prefetch and verification are outside timing.',
                  'Clean output and isolated source copies are not cold OS caches. Shared registry and OS/SDK caches are retained; no cache flushing or controlled thermal preconditioning.',
                  'Incremental edits replace predetermined comments in isolated native source modules. This measures invalidation/recompilation, not optimization quality or typical edit workloads.',
                  'Launch preparation and Python oracle run before timing. Timing covers manager Popen through wait4 completion, including validation, child launch and cleanup; temporary-file stdout/stderr capture is included.',
                  'wait4 is polled every 1 ms; scheduling and polling add resolution/overhead. Warmups are retained separately; all valid unfavorable samples are included. No percentiles are estimated. Launch order is fixed Rust then Swift per pair, not randomized or counterbalanced.',
                  'Darwin wait4 ru_maxrss is recorded in bytes for the waited command using OS child accounting; it is not a sampled or independently measured process-tree peak. Build driver and compiler attribution is not separated.',
                  'Distribution payload size is the standalone experimental manager executable only; system libraries, SDK, toolchains and fixture data are reported separately and not bundled.',
                  'No signed app bundle, notarization, clean external Mac, minimum-OS or ordinary-user distribution qualification was executed.',
                  'The coordinator reserved the measurement window from known parallel heavy tasks; no guarantee of system-wide background quiescence. Power state is observed at the beginning and end.',
                  'The functional corpus uses 5000 ms for ordinary/non-timeout cases, retains 1500 ms for deliberate timeout cases, and keeps all traces, cleanup and privacy checks. Scored warmup/launch invocations retain the frozen 1500 ms budget. Passing corpus gates establish only this wider declared functional budget; the earlier 1500 ms observer-gap failure remains unresolved startup-limit evidence.',
                  'A passing run does not erase prior corpus failures. Fresh executable startup consumed the original 300 ms negative-fixture deadline in some attempts; observed late trace creation and the prior failed preflight remain a reliability obligation for #9. The underlying OS cause is unproven.',
              ]}
    output.parent.mkdir(parents=True, exist_ok=True)
    def save():
        report['summary'] = summaries(report['samples'])
        output.write_text(json.dumps(report, indent=2) + '\n')
        (run_root / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    try:
        if report['host']['architecture'] != 'arm64':
            raise ValueError('host_not_native')
        report['gates']['before'] = full_gate(build_root, oracle, run_root / 'logs/gate-before.jsonl')
        if not report['gates']['before']['passed']:
            raise ValueError('initial_functional_gate_failed')
        # Shared native preparation is separate from the candidate build samples.
        flags = ['-arch', 'arm64', '-mmacosx-version-min=26.0', '-O2', '-std=c11', '-Wall', '-Wextra', '-Werror']
        bridge = run_root / 'native_bridge.o'
        preparation_commands = [['xcrun', 'clang', *flags, '-c', HERE / 'fixtures/native_bridge.c', '-o', bridge]]
        for index, command in enumerate(preparation_commands):
            observation, _, _ = measured_command(command, REPO, env, run_root / f'logs/preparation-{index}', 180)
            report['preparation'].append({'command': tokenized(command, run_root), **observation})
            if observation['returncode'] or observation['watchdog']:
                raise ValueError('shared_preparation_failed')
        states, last_clean = {}, {}
        counts = {c: 0 for c in CANDIDATES}
        for phase, order in [('clean', plan['build_samples']['order']), ('incremental', plan['build_samples']['incremental_order'])]:
            counts = {c: 0 for c in CANDIDATES}
            for candidate in order:
                counts[candidate] += 1
                number = counts[candidate]
                edit = next(e for e in plan['build_samples']['incremental_edits'] if e['candidate'] == candidate)
                if phase == 'clean':
                    state_root = run_root / f'clean-{candidate}-{number}'
                    source, target = state_root / 'source', state_root / 'output'
                    shutil.copytree(HERE / candidate, source, ignore=shutil.ignore_patterns('.build', 'target', '__pycache__'))
                    states[candidate] = (source, target)
                else:
                    # Reuse that candidate's third isolated clean output for a true incremental rebuild.
                    source, target = states[candidate]
                    changed = source / Path(edit['path']).relative_to(candidate)
                    old = edit['old'] if number == 1 else edit['replacements'][number - 2]
                    text = changed.read_text()
                    if text.count(old) != 1:
                        raise ValueError('incremental_edit_not_unique')
                    changed.write_text(text.replace(old, edit['replacements'][number - 1]))
                command, candidate_env, binary = build_command(candidate, source, target, bridge, env)
                source_identity = native_inputs(source)
                observation, stdout, stderr = measured_command(command, source, candidate_env, run_root / f'logs/{phase}-{candidate}-{number}', 180)
                combined = stdout + stderr
                if candidate == 'rust':
                    rebuild = b'--crate-name pear_manager' in combined
                else:
                    rebuild = b'swift-frontend' in combined and b'-c ' in combined and b'main.swift' in combined
                passed = observation['returncode'] == 0 and observation['watchdog'] is None and rebuild and binary.is_file()
                row = {'sequence': len(report['samples']) + 1, 'phase': phase, 'candidate': candidate, 'number': number,
                       'passed': passed, 'command': tokenized(command, run_root), 'build_environment': {key: tokenized([candidate_env[key]], run_root)[0] for key in ['MACOSX_DEPLOYMENT_TARGET', 'RUSTC', 'CARGO_TARGET_DIR', 'CARGO_ENCODED_RUSTFLAGS'] if key in candidate_env}, 'source_sha256': source_identity,
                       'rebuild_observed': rebuild, 'binary_sha256': sha(binary) if binary.is_file() else None, **observation}
                report['samples'].append(row)
                save()
                print(json.dumps({'phase': phase, 'candidate': candidate, 'sample': number, 'passed': passed}), flush=True)
                if not passed:
                    raise ValueError('candidate_build_failed')
                if phase == 'clean':
                    retained = run_root / f'{candidate}-clean-manager'
                    shutil.copy2(binary, retained)
                    last_clean[candidate] = retained
        # Baseline source identities are unchanged. Launch the retained, measured clean binaries.
        launch_build = run_root / 'launch-build'
        (launch_build / 'bin').mkdir(parents=True)
        shutil.copy2(build_root / 'bin/fixture-child', launch_build / 'bin/fixture-child')
        launch_metadata = copy.deepcopy(baseline)
        for candidate in CANDIDATES:
            destination = launch_build / 'bin' / f'{candidate}-manager'
            shutil.copy2(last_clean[candidate], destination)
            slices = plain_command(['lipo', '-archs', destination], env)
            if slices != 'arm64':
                raise ValueError('measured_candidate_not_arm64')
            dependencies = plain_command(['otool', '-L', destination], env).splitlines()[1:]
            launch_metadata['binaries'][f'{candidate}-manager'].update(sha256=sha(destination), size_bytes=destination.stat().st_size, slices=slices)
            report['payload'][candidate] = {'manager_binary_bytes': destination.stat().st_size, 'standalone_distribution_payload_bytes': destination.stat().st_size, 'binary_sha256': sha(destination), 'native_slices': [slices], 'system_dynamic_dependencies': [v.strip() for v in dependencies], 'signed_app_bundle_bytes': None, 'signed_app_bundle_reason': 'No distribution bundle is built or qualified.', 'packaging_inspection': inspect_packaging(destination, env, run_root / f'logs/{candidate}-packaging.json')}
        (launch_build / 'build.json').write_text(json.dumps(launch_metadata, indent=2) + '\n')
        corpus.verify_build(launch_build)
        sentinel = subprocess.Popen([str(launch_build / 'bin/fixture-child'), 'sentinel'], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            case = {'mode': 'success', 'mutation': None, 'expected': 'success', 'observer_ready': True, 'observer_gap': False}
            for phase, count in [('warmup', 5), ('launch', 30)]:
                for number in range(1, count + 1):
                    for candidate in CANDIDATES:
                        root = run_root / f'{phase}-{number}-{candidate}'
                        fixture_hash = corpus.create_bundle(root, launch_build, case)
                        oracle_result = corpus.oracle_result(oracle, root, 'fixture')
                        if not oracle_result['eligible']:
                            raise ValueError('launch_oracle_failed')
                        command = [launch_build / 'bin' / f'{candidate}-manager', '--bundle-root', root, '--entry', 'records/request.json', '--fixture-sha256', fixture_hash, '--timeout-ms', '1500', '--output-limit', '4096', '--observer-ready', 'yes', '--observer-gap', 'no']
                        observation, stdout, stderr = measured_command(command, REPO, env, run_root / f'logs/{phase}-{candidate}-{number}', 10)
                        errors = []
                        if stderr or len(stdout) > 16384 or any(m.encode() in stdout for m in FORBIDDEN) or str(root).encode() in stdout:
                            errors.append('privacy_or_output')
                        try:
                            result = json.loads(stdout)
                            errors += corpus.check_result(result, case, observation['returncode'])
                        except (ValueError, TypeError):
                            result = {}
                            errors.append('invalid_result')
                        if result.get('candidate') != candidate:
                            errors.append('candidate_identity')
                        trace = root / 'state/prefix/child.json'
                        gone = trace.is_file() and corpus.disappeared(launch_build, trace)
                        alive = sentinel.poll() is None
                        if not gone or not alive or observation['watchdog']:
                            errors.append('lifecycle')
                        row = {'sequence': len(report['samples']) + 1, 'phase': phase, 'candidate': candidate, 'number': number, 'passed': not errors,
                               'command': tokenized(command, run_root), 'oracle_eligible': oracle_result['eligible'], 'owned_identity_gone': gone,
                               'native': result.get('host_architecture') == 'arm64' and result.get('translated') is False, 'fresh_bundle': True, 'sentinel_alive': alive,
                               'binary_sha256': sha(launch_build / 'bin' / f'{candidate}-manager'), 'errors': errors, **observation}
                        report['samples'].append(row)
                        save()
                        if errors:
                            raise ValueError('launch_measurement_failed')
                    print(json.dumps({'phase': phase, 'pair': number, 'passed': True}), flush=True)
        finally:
            if sentinel.poll() is None:
                sentinel.terminate()
            sentinel.wait(timeout=3)
        report['gates']['after'] = full_gate(launch_build, oracle, run_root / 'logs/gate-after.jsonl')
        if not report['gates']['after']['passed']:
            raise ValueError('final_functional_gate_failed')
        libc = Path.home() / '.cargo/registry/cache/index.crates.io-1949cf8c6b5b557f/libc-0.2.186.crate'
        extracted = libc.parent.parent.parent / 'src' / libc.parent.name / 'libc-0.2.186'
        report['payload']['dependency_inputs'] = {'rust': {'compressed_crate_bytes': libc.stat().st_size, 'extracted_crate_bytes': tree_bytes(extracted), 'archive_sha256': sha(libc), 'active_transitive_crates': 0}, 'swift': {'external_package_cache_bytes': 0, 'external_packages': 0}, 'shared': {'fixture_binary_bytes': (launch_build / 'bin/fixture-child').stat().st_size, 'native_bridge_object_bytes': bridge.stat().st_size, 'apple_sdk_or_toolchain_bytes': None, 'rust_toolchain_bytes': None, 'toolchain_size_reason': 'Installed shared toolchains and SDK are prerequisites, not distribution payload; their complete sizes were not measured.'}}
        report['conditions']['after'] = host_snapshot(env)
        report['conditions']['finished_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        before, after = report['conditions']['before'], report['conditions']['after']
        if before['power_source'] == 'unknown' or before['power_source'] != after['power_source'] or before['configured_low_power_modes'] != after['configured_low_power_modes']:
            raise ValueError('power_configuration_changed')
        if inventory() != baseline_sources:
            raise ValueError('source_changed_during_measurement')
        report['status'] = 'completed'
        save()
        errors = validate_report(report, plan)
        if errors:
            raise ValueError('report_validation_' + '_'.join(errors))
        return report
    except BaseException as error:
        report['status'] = 'failed'
        report['conditions']['finished_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        report['failures'].append({'type': type(error).__name__, 'code': str(error) if isinstance(error, ValueError) and re.fullmatch('[a-z0-9_]+', str(error)) else 'execution_interrupted_or_failed'})
        with contextlib.suppress(Exception):
            report['conditions']['after'] = host_snapshot(env)
        save()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--build-root', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check-report', type=Path)
    args = parser.parse_args()
    try:
        if args.check_report:
            if args.plan or args.build_root or args.output:
                parser.error('--check-report must be used alone')
            report = json.loads(args.check_report.read_bytes())
            errors = validate_report(report, load_plan(HERE / 'comparison-plan.json'))
            print(json.dumps({'report_valid': not errors, 'errors': errors, 'fixture_only': True}))
            return bool(errors)
        if not all([args.plan, args.build_root, args.output]):
            parser.error('--plan, --build-root and --output are required')
        compare(args.plan, args.build_root, args.output)
        print(json.dumps({'comparison': 'completed', 'fixture_only': True, 'runtime_eligible': False}))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({'comparison': 'failed', 'error_type': type(error).__name__}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
