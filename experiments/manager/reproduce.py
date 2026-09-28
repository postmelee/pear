"""Rebuild owned manager fixtures in empty outputs; no game/runtime qualification."""
import argparse
import ast
import datetime
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import build as native_build
import compare
import run_cases

PUBLIC = HERE / 'results/reproduction.json'
SUITES = {'contracts': REPO / 'tests/contracts', 'experiments': HERE}
BUDGETS = {'functional_ms': 5000, 'intentional_timeout_ms': 1500,
           'scored_launch_ms': 1500, 'cleanup_ms': 2000, 'outer_seconds': 10}
LIMITATIONS = [
    'Same-Mac clean-output reproduction, not a clean-machine or independent-host test.',
    'Installed CPython, Rust, Apple toolchains, SDK, Cargo registry/source cache and OS/compiler caches are reused. The locked crate and all extracted source members are reverified; the Cargo cache is not reconstructed.',
    'The five reviewed wheels are copied and hash-verified, then installed offline into a fresh virtual environment. The native rpds wheel is not rebuilt from source. No network acquisition is requested by this runner; it does not independently audit all operating-system network traffic.',
    'Raw logs and fixture bundles stay local. Unit tests may create and clean temporary owned directories; existing reproduction/prototype outputs and historical public reports are not overwritten.',
    'Only owned fixtures run. Passing schemas, synthetic policy tests and native manager cases cannot qualify Wine, Steam, Megabonk, complete host-process/module coverage or distribution.',
    'The functional corpus retains 5000 ms ordinary and 1500 ms deliberate-timeout limits, with 2000 ms cleanup and a 10-second outer watchdog. The Stage 4 scored 1500 ms launch experiment is checked as retained evidence, not repeated here. Earlier startup failures remain unresolved.',
    'Binary hashes and sizes are recorded for these exact build outputs. Relocated build inputs, linker UUID/signature bytes or compiler metadata can affect payload identity; any differing bytes are reported without assigning an unmeasured cause. Semantic equivalence, not byte-identical signatures, is required.',
    'Report checking establishes consistency with current source and retained evidence; it does not independently attest that reported observations were produced by a trusted host.',
]


def sha(path):
    return compare.sha(path)


def encoded(value):
    return (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()


def strict_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate_json_key')
            result[key] = value
        return result
    data = Path(path).read_bytes()
    if len(data) > 32 * 1024 * 1024:
        raise ValueError('report_size')
    return json.loads(data.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite_json')))


def inventory():
    """Exclude mutable documentation/public reproduction output from source identity."""
    paths = {REPO / p for p in compare.inventory()}
    paths.update((REPO / 'tests/contracts').glob('*.py'))
    paths.update(p for p in (REPO / 'runtime/contracts/examples').rglob('*') if p.is_file())
    paths.update(HERE.glob('test_*.py'))
    paths.add(Path(__file__))
    return {str(p.relative_to(REPO)): sha(p) for p in sorted(paths)}


def retained_evidence():
    return {str(p.relative_to(REPO)): sha(p) for p in sorted((HERE / 'results').glob('*.json')) if p != PUBLIC}


def expected_tests(name):
    """Enumerate current simple unittest methods without importing their dependencies."""
    tests = []
    for path in sorted(SUITES[name].glob('test_*.py')):
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                for method in node.body:
                    if isinstance(method, ast.FunctionDef) and method.name.startswith('test_'):
                        tests.append(f'{path.stem}.{node.name}.{method.name}')
    if not tests or len(tests) != len(set(tests)):
        raise ValueError('test_inventory')
    return sorted(tests)


def expected_rust_tests():
    text = (HERE / 'rust/src/supervisor_tests.rs').read_text()
    return sorted('supervisor_tests::' + name for name in re.findall(r'#\[test\]\s+fn ([a-z0-9_]+)\(', text))


def dependency_identity():
    dep = strict_json(REPO / 'tests/contracts/dependencies.json')
    expected = {}
    wheels = []
    for package in dep['packages']:
        expected[package['name']] = (package['version'], package['wheel']['sha256'])
        wheels.append({'name': package['name'], 'version': package['version'], **{k: package['wheel'][k] for k in ['filename', 'sha256', 'size_bytes']}})
    locked = {}
    for line in (REPO / 'tests/contracts/requirements.lock').read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([a-z0-9-]+)==([0-9.]+) --hash=sha256:([a-f0-9]{64})', line)
        if not match or match[1] in locked:
            raise ValueError('python_lock_format')
        locked[match[1]] = (match[2], match[3])
    if locked != expected or len(wheels) != 5:
        raise ValueError('python_lock_disagreement')
    return sorted(wheels, key=lambda row: row['name'])


def output_path(value, repo=None):
    """Allow one dedicated leaf only; never delete or reuse nonempty output."""
    repo = REPO if repo is None else Path(repo)
    if not isinstance(value, str) or not re.fullmatch(r'\.build/task3/reproduction(?:-[a-z0-9_-]+)?', value):
        raise ValueError('output_must_be_new_task_local_reproduction_leaf')
    path = repo
    for part in Path(value).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('symlink_output_component')
        if path.exists() and not path.is_dir():
            raise ValueError('output_component_not_directory')
    if path.exists() and any(path.iterdir()):
        raise ValueError('output_not_empty')
    return path


def suite_destination(name, destination):
    destination = Path(destination)
    if not destination.is_absolute():
        raise ValueError('suite_output_must_be_absolute')
    try:
        relative = destination.relative_to(REPO)
    except ValueError:
        raise ValueError('suite_output_outside_repository') from None
    if destination.name != name + '.json' or not re.fullmatch(r'\.build/task3/reproduction(?:-[a-z0-9_-]+)?', str(relative.parent)):
        raise ValueError('suite_output_scope')
    current = REPO
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError('suite_output_symlink')
    if destination.exists() or not destination.parent.is_dir():
        raise ValueError('suite_output_exists_or_parent_missing')
    return destination


def suite_result(name, destination):
    """Run every discovered case and retain identifiers, never private failure text."""
    destination = suite_destination(name, destination)
    sys.path.insert(0, str(SUITES[name]))
    suite = unittest.defaultTestLoader.discover(str(SUITES[name]), pattern='test_*.py')
    class Results(unittest.TextTestResult):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.passed_ids = []
        def addSuccess(self, test):
            self.passed_ids.append(test.id())
            super().addSuccess(test)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, resultclass=Results).run(suite)
    value = {'tests_run': result.testsRun, 'passed_ids': sorted(result.passed_ids),
             'failed_ids': sorted(t.id() for t, _ in result.failures),
             'error_ids': sorted(t.id() for t, _ in result.errors),
             'skipped_ids': sorted(t.id() for t, _ in result.skipped),
             'unexpected_successes': sorted(t.id() for t in result.unexpectedSuccesses),
             'expected_failures': sorted(t.id() for t, _ in result.expectedFailures)}
    with destination.open('xb') as stream:
        stream.write(encoded(value))
    return 0 if not validate_suite(value, name) else 1


def validate_suite(value, name):
    keys = {'tests_run', 'passed_ids', 'failed_ids', 'error_ids', 'skipped_ids', 'unexpected_successes', 'expected_failures'}
    if not isinstance(value, dict) or set(value) != keys:
        return ['unit_result_shape']
    expected = expected_tests(name)
    if type(value['tests_run']) is not int or value['tests_run'] != len(expected) or value['passed_ids'] != expected or any(value[key] != [] for key in keys - {'tests_run', 'passed_ids'}):
        return ['unit_test_accounting']
    return []


def semantic_projection(report):
    """Output-limit races may vary byte/trace counts; retain their checked contract."""
    result = []
    for row in report['results']:
        native = row['result']
        result.append({'case': row['case'], 'candidate': row['candidate'], 'oracle': row['oracle'],
                       'classification': native['classification'], 'spawned': native['spawned'],
                       'reaped': native['reaped'], 'cleanup': native['cleanup'],
                       'host_architecture': native['host_architecture'], 'translated': native['translated'],
                       'fixture_only': native['fixture_only'], 'runtime_eligible': native['runtime_eligible']})
    return result


def validate_corpus(report):
    required = {'version', 'fixture_only', 'runtime_eligible', 'case_count', 'execution_count', 'passed', 'results', 'trace_scope', 'corpus_sha256', 'build_metadata_sha256', 'harness_sha256'}
    if not isinstance(report, dict) or set(report) != required:
        return ['corpus_shape']
    errors = []
    cases = strict_json(HERE / 'fixtures/cases.json')['cases']
    if type(report['version']) is not int or report['version'] != 1 or report['fixture_only'] is not True or report['runtime_eligible'] is not False or report['passed'] is not True:
        errors.append('corpus_scope')
    if type(report['case_count']) is not int or report['case_count'] != len(cases) or type(report['execution_count']) is not int or report['execution_count'] != 2 * len(cases):
        errors.append('corpus_count')
    rows = report['results']
    expected = [(case, candidate) for i, case in enumerate(cases) for candidate in (['rust', 'swift'] if i % 2 == 0 else ['swift', 'rust'])]
    if not isinstance(rows, list) or len(rows) != len(expected):
        return errors + ['corpus_rows']
    row_keys = {'case', 'candidate', 'passed', 'errors', 'result', 'oracle', 'observed_trace_count', 'owned_identities_gone', 'unrelated_sentinel_alive', 'bounded_completion'}
    for row, (case, candidate) in zip(rows, expected):
        if not isinstance(row, dict) or set(row) != row_keys or row.get('case') != case['id'] or row.get('candidate') != candidate:
            errors.append('corpus_row_identity')
            continue
        if row['passed'] is not True or row['errors'] != [] or row['bounded_completion'] is not True or row['unrelated_sentinel_alive'] is not True:
            errors.append('corpus_case_failed')
        result = row['result']
        code = 0 if case['expected'] == 'success' else 1 if case['expected'] == 'invalid_contract' else 3 if case['expected'] in ['ineligible', 'observer_not_ready'] else 4
        if not isinstance(result, dict) or run_cases.check_result(result, case, code) or result.get('candidate') != candidate:
            errors.append('corpus_result_semantics')
            continue
        count = row['observed_trace_count']
        if type(count) is not int or not 0 <= count <= 2 or type(row['owned_identities_gone']) is not bool:
            errors.append('corpus_trace_shape')
        else:
            expected_counts = {0} if not result['spawned'] else {2} if case['mode'] == 'descendant_pipe' else {0, 1} if case['expected'] == 'output_limit' else {1}
            if count not in expected_counts or row['owned_identities_gone'] != (count > 0):
                errors.append('corpus_trace_semantics')
        oracle = row['oracle']
        if not isinstance(oracle, dict) or set(oracle) != {'eligible', 'evaluation_only', 'outcome_codes', 'record_count', 'record_valid'}:
            errors.append('corpus_oracle_shape')
            continue
        if oracle['evaluation_only'] is not True or type(oracle['record_valid']) is not bool or type(oracle['eligible']) is not bool or type(oracle['record_count']) is not int or not 0 <= oracle['record_count'] <= 4 or not isinstance(oracle['outcome_codes'], list) or any(not isinstance(code, str) or not re.fullmatch('[a-z0-9_]+', code) for code in oracle['outcome_codes']):
            errors.append('corpus_oracle_shape')
        elif (case['oracle'] == 'invalid' and oracle['record_valid']) or (case['oracle'] == 'eligible' and not oracle['eligible']) or (case['oracle'] == 'ineligible' and (not oracle['record_valid'] or oracle['eligible'])) or (case['oracle'] == 'valid' and not oracle['record_valid']):
            errors.append('corpus_oracle_semantics')
    if report['corpus_sha256'] != sha(HERE / 'fixtures/cases.json') or report['harness_sha256'] != sha(HERE / 'run_cases.py') or not digest_string(report['build_metadata_sha256']):
        errors.append('corpus_input_identity')
    return sorted(set(errors))


def digest_string(value):
    return isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None


def command_specs(output):
    """Stable public command records; paths are replaced by owned scope tokens."""
    python = output / 'venv/bin/python'
    return [
        ('venv', [sys.executable, '-I', '-m', 'venv', output / 'venv'], 120),
        ('install', [python, '-I', '-m', 'pip', '--isolated', 'install', '--disable-pip-version-check', '--no-index', '--no-cache-dir', '--find-links', output / 'wheels', '--require-hashes', '--no-deps', '-r', REPO / 'tests/contracts/requirements.lock'], 120),
        ('packages', [python, '-I', str(HERE / 'reproduce.py'), '--internal-packages'], 30),
        ('schemas_examples', [python, '-I', REPO / 'tests/contracts/validate.py', '--check-schemas', '--check-examples'], 30),
        ('contracts', [python, '-I', HERE / 'reproduce.py', '--internal-suite', 'contracts', '--suite-output', output / 'contracts.json'], 180),
        ('experiments', [python, '-I', HERE / 'reproduce.py', '--internal-suite', 'experiments', '--suite-output', output / 'experiments.json'], 180),
        ('build', [python, '-I', HERE / 'build.py', '--output', output / 'prototypes', '--locked'], 300),
        ('corpus', [python, '-I', HERE / 'run_cases.py', '--build-root', output / 'prototypes', '--all', '--oracle', python], 600),
        ('rust_faults', ['cargo', 'test', '--manifest-path', HERE / 'rust/Cargo.toml', '--locked', '--offline', '--target', 'aarch64-apple-darwin', '--', '--test-threads=1'], 180),
        ('retained_comparison', [python, '-I', HERE / 'compare.py', '--check-report', HERE / 'results/comparison.json'], 30),
    ]


def public_argv(argv, output):
    argv = list(map(str, argv))
    if argv[1:4] == ['-I', '-m', 'venv'] and argv[0] == sys.executable:
        argv[0] = '<python>'
    return compare.tokenized(argv, output)


def validate_report(report):
    """Verify identity, exact test coverage and actual semantic fields, not pass labels."""
    if not isinstance(report, dict):
        return ['report_shape']
    keys = {'version', 'status', 'fixture_only', 'runtime_eligible', 'source_sha256', 'retained_evidence_sha256', 'started_at_utc', 'finished_at_utc', 'output', 'reconstruction', 'commands', 'tests', 'build', 'corpus', 'semantic_match', 'budgets', 'limitations', 'failures'}
    if set(report) != keys:
        return ['report_shape']
    errors = []
    try:
        if type(report['version']) is not int or report['version'] != 1 or report['status'] != 'completed' or report['fixture_only'] is not True or report['runtime_eligible'] is not False or report['failures'] != []:
            errors.append('report_scope')
        serialized = json.dumps(report, allow_nan=False)
        if any(marker in serialized for marker in (*compare.FORBIDDEN, 'PRIVATE_MARKER_DO_NOT_DISCLOSE', str(Path.home()))):
            errors.append('private_data')
        if report['source_sha256'] != inventory() or report['retained_evidence_sha256'] != retained_evidence():
            errors.append('source_or_history_identity')
        if report['budgets'] != BUDGETS or report['limitations'] != LIMITATIONS:
            errors.append('scope_limits')
        if not re.fullmatch(r'\.build/task3/reproduction(?:-[a-z0-9_-]+)?', report['output']):
            errors.append('output_scope')
        dates = [datetime.datetime.fromisoformat(report[key]) for key in ['started_at_utc', 'finished_at_utc']]
        if any(date.utcoffset() != datetime.timedelta(0) for date in dates) or dates[1] < dates[0]:
            errors.append('report_time')
        reconstruction = report['reconstruction']
        wanted = {'python_wheels': dependency_identity(), 'fresh_venv': True, 'python_install': 'offline_no_index_require_hashes_no_deps', 'rust_build': 'locked_offline_reused_hash_verified_registry_and_extracted_sources', 'swift_external_packages': [], 'network_acquisition': 'none_requested', 'cache_and_toolchain_reset': False}
        if reconstruction != wanted:
            errors.append('dependency_reconstruction')
        output = REPO / report['output']
        specs = command_specs(output)
        commands = report['commands']
        if not isinstance(commands, list) or len(commands) != len(specs):
            errors.append('command_count')
        else:
            for row, (phase, argv, _) in zip(commands, specs):
                if set(row) != {'phase', 'argv', 'returncode', 'watchdog', 'stdout_sha256', 'stderr_sha256'} or row['phase'] != phase or row['argv'] != public_argv(argv, output) or type(row['returncode']) is not int or row['returncode'] != 0 or row['watchdog'] is not None or not all(digest_string(row[key]) for key in ['stdout_sha256', 'stderr_sha256']):
                    errors.append('command_evidence')
        tests = report['tests']
        if set(tests) != {'schemas_examples', 'contracts', 'experiments', 'rust_faults', 'installed_packages'}:
            errors.append('test_shape')
        else:
            if tests['schemas_examples'] != {'eligible': True, 'evaluation_only': True, 'outcome_codes': [], 'record_count': 0, 'record_valid': True}:
                errors.append('schema_example_validation')
            for name in SUITES:
                errors.extend(validate_suite(tests[name], name))
            fault = tests['rust_faults']
            if fault != {'tests_run': len(expected_rust_tests()), 'passed_ids': expected_rust_tests(), 'failed': 0, 'ignored': 0, 'filtered_out': 0} or len(expected_rust_tests()) != 2:
                errors.append('rust_fault_test_accounting')
            wanted_packages = {r['name']: r['version'] for r in dependency_identity()}
            if tests['installed_packages'] != {'python': '3.14.4', 'machine': 'arm64', 'platform': 'darwin', 'packages': wanted_packages}:
                errors.append('installed_package_identity')
        built = report['build']
        if set(built) != {'metadata_sha256', 'toolchains', 'binaries', 'native_source_sha256', 'locked_offline_rust', 'swift_external_dependencies'} or built['locked_offline_rust'] is not True or built['swift_external_dependencies'] != [] or built['toolchains']['machine'] != 'arm64' or not digest_string(built['metadata_sha256']):
            errors.append('build_scope')
        native = {p: value for p, value in inventory().items() if any(p.startswith('experiments/manager/' + part + '/') for part in ['rust', 'swift', 'fixtures'])}
        if built['native_source_sha256'] != native:
            errors.append('native_source_identity')
        if set(built['binaries']) != {'fixture-child', 'rust-manager', 'swift-manager'}:
            errors.append('binary_inventory')
        comparison = strict_json(HERE / 'results/comparison.json')
        if compare.validate_report(comparison, compare.load_plan(HERE / 'comparison-plan.json')):
            errors.append('retained_comparison_invalid')
        for name, binary in built['binaries'].items():
            if set(binary) != {'sha256', 'size_bytes', 'slices', 'system_dynamic_dependencies', 'packaging', 'matches_stage4_measured_payload'} or not digest_string(binary['sha256']) or type(binary['size_bytes']) is not int or binary['size_bytes'] <= 0 or binary['slices'] != 'arm64':
                errors.append('binary_identity')
            dependencies = binary['system_dynamic_dependencies']
            if not isinstance(dependencies, list) or not dependencies or any(not isinstance(item, str) or not item.startswith(('/usr/lib/', '/System/Library/')) for item in dependencies):
                errors.append('binary_dependencies')
            inspection = binary['packaging']
            if set(inspection) != {'platform', 'minimum_macos', 'sdk', 'rpaths', 'codesign_strict_verify_exit', 'signature', 'linker_signed', 'team_identifier_present', 'inspection_log_sha256', 'distribution_qualified', 'signing_scope'} or inspection['platform'] != 'MACOS' or inspection['minimum_macos'] != '26.0' or inspection['sdk'] != built['toolchains']['sdk'] or type(inspection['codesign_strict_verify_exit']) is not int or inspection['codesign_strict_verify_exit'] != 0 or inspection['signature'] != 'adhoc' or inspection['linker_signed'] is not True or inspection['team_identifier_present'] is not False or inspection['distribution_qualified'] is not False or not digest_string(inspection['inspection_log_sha256']):
                errors.append('packaging_evidence')
            if not isinstance(inspection['rpaths'], list) or any(not isinstance(item, str) or not item.startswith(('@loader_path', '@executable_path', '/usr/lib/', '/System/Library/')) for item in inspection['rpaths']):
                errors.append('packaging_rpaths')
            matched = None if name == 'fixture-child' else binary['sha256'] == comparison['payload'][name.split('-')[0]]['binary_sha256']
            if binary['matches_stage4_measured_payload'] is not matched:
                errors.append('payload_comparison')
        errors.extend(validate_corpus(report['corpus']))
        if report['corpus']['build_metadata_sha256'] != built['metadata_sha256']:
            errors.append('corpus_build_identity')
        baseline = strict_json(HERE / 'results/final-corpus.json')
        if validate_corpus(baseline):
            errors.append('baseline_corpus_invalid')
        if report['semantic_match'] is not True or semantic_projection(report['corpus']) != semantic_projection(baseline):
            errors.append('semantic_mismatch')
    except (KeyError, TypeError, ValueError, AttributeError, IndexError):
        errors.append('malformed_evidence')
    return sorted(set(errors))


def reproduction(output_value):
    if platform.machine() != 'arm64' or sys.platform != 'darwin' or platform.python_version() != '3.14.4':
        raise ValueError('recorded_native_cpython_3_14_4_required')
    output = output_path(output_value)
    wheels = dependency_identity()
    native_build.verify_lock()
    for row in wheels:
        wheel = REPO / '.build/task3/wheels' / row['filename']
        if wheel.is_symlink() or not wheel.is_file() or sha(wheel) != row['sha256'] or wheel.stat().st_size != row['size_bytes']:
            raise ValueError('reviewed_wheel_missing_or_changed')
    output.mkdir(parents=True, exist_ok=True)
    for name in ['logs', 'wheels', 'tmp']:
        (output / name).mkdir()
    report = {'version': 1, 'status': 'running', 'fixture_only': True, 'runtime_eligible': False,
              'source_sha256': inventory(), 'retained_evidence_sha256': retained_evidence(),
              'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'finished_at_utc': None,
              'output': output_value, 'reconstruction': {'python_wheels': wheels, 'fresh_venv': True,
              'python_install': 'offline_no_index_require_hashes_no_deps', 'rust_build': 'locked_offline_reused_hash_verified_registry_and_extracted_sources',
              'swift_external_packages': [], 'network_acquisition': 'none_requested', 'cache_and_toolchain_reset': False},
              'commands': [], 'tests': {}, 'build': {}, 'corpus': {}, 'semantic_match': False,
              'budgets': BUDGETS, 'limitations': LIMITATIONS, 'failures': []}
    def save():
        (output / 'reproduction.json').write_bytes(encoded(report))
    save()
    env = native_build.controlled_environment()
    env = {key: value for key, value in env.items() if not key.startswith('PYTHON')}
    env['TMPDIR'] = str(output / 'tmp')
    try:
        for row in wheels:
            target = output / 'wheels' / row['filename']
            shutil.copyfile(REPO / '.build/task3/wheels' / row['filename'], target)
            if sha(target) != row['sha256']:
                raise ValueError('copied_wheel_changed')
        for phase, argv, timeout in command_specs(output):
            phase_env = env.copy()
            if phase == 'rust_faults':
                base = output / 'prototypes'
                phase_env.update(CARGO_TARGET_DIR=str(output / 'rust-faults'),
                                 CARGO_ENCODED_RUSTFLAGS='\x1f'.join(['-C', 'link-arg=' + str(base / 'native_bridge.o'), '-C', 'link-arg=-lproc']),
                                 PEAR_MANAGER_TEST_FIXTURE=str(base / 'bin/fixture-child'))
            observation, stdout, _ = compare.measured_command(argv, REPO, phase_env, output / 'logs' / phase, timeout)
            report['commands'].append({'phase': phase, 'argv': public_argv(argv, output), **{key: observation[key] for key in ['returncode', 'watchdog', 'stdout_sha256', 'stderr_sha256']}})
            save()
            print(json.dumps({'phase': phase, 'passed': observation['returncode'] == 0 and observation['watchdog'] is None}), flush=True)
            if observation['returncode'] != 0 or observation['watchdog'] is not None:
                raise ValueError('command_failed_' + phase)
            if phase == 'packages':
                report['tests']['installed_packages'] = json.loads(stdout)
            elif phase == 'schemas_examples':
                report['tests']['schemas_examples'] = json.loads(stdout)
            elif phase in SUITES:
                report['tests'][phase] = strict_json(output / (phase + '.json'))
            elif phase == 'rust_faults':
                text = stdout.decode()
                passed = sorted(re.findall(r'^test ([a-z0-9_:]+) \.\.\. ok$', text, re.MULTILINE))
                matches = re.findall(r'test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored; \d+ measured; (\d+) filtered out;', text)
                if len(matches) != 1:
                    raise ValueError('rust_fault_summary_missing')
                counts = list(map(int, matches[0]))
                report['tests']['rust_faults'] = dict(zip(['tests_run', 'failed', 'ignored', 'filtered_out'], counts), passed_ids=passed)
            elif phase == 'corpus':
                report['corpus'] = strict_json(output / 'prototypes/case-results.json')
            save()
        base = output / 'prototypes'
        metadata = run_cases.verify_build(base)
        comparison = strict_json(HERE / 'results/comparison.json')
        report['build'] = {'metadata_sha256': sha(base / 'build.json'), 'toolchains': metadata['toolchains'],
                           'binaries': {}, 'native_source_sha256': {p: value for p, value in metadata['sources'].items() if any(p.startswith('experiments/manager/' + part + '/') for part in ['rust', 'swift', 'fixtures'])},
                           'locked_offline_rust': metadata['locked_offline_rust'], 'swift_external_dependencies': metadata['swift_external_dependencies']}
        for name, observed in metadata['binaries'].items():
            report['build']['binaries'][name] = {key: observed[key] for key in ['sha256', 'size_bytes', 'slices']}
            report['build']['binaries'][name].update(system_dynamic_dependencies=[line.strip() for line in observed['dependencies'].splitlines()[1:]],
                packaging=compare.inspect_packaging(base / 'bin' / name, env, output / 'logs' / (name + '-packaging.json')),
                matches_stage4_measured_payload=None if name == 'fixture-child' else observed['sha256'] == comparison['payload'][name.split('-')[0]]['binary_sha256'])
        report['semantic_match'] = semantic_projection(report['corpus']) == semantic_projection(strict_json(HERE / 'results/final-corpus.json'))
        report['finished_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        report['status'] = 'completed'
        save()
        errors = validate_report(report)
        if errors:
            raise ValueError('report_validation_' + '_'.join(errors))
        return report
    except BaseException as error:
        report['status'] = 'failed'
        report['finished_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        report['failures'].append({'type': type(error).__name__, 'code': str(error) if isinstance(error, ValueError) and re.fullmatch('[a-z0-9_]+', str(error)) else 'execution_failed_or_interrupted'})
        save()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output')
    parser.add_argument('--require-empty', action='store_true')
    parser.add_argument('--check-report', type=Path)
    parser.add_argument('--internal-suite', choices=sorted(SUITES), help=argparse.SUPPRESS)
    parser.add_argument('--suite-output', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--internal-packages', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.internal_suite or args.internal_packages:
            if args.output or args.require_empty or args.check_report or (args.internal_suite and args.internal_packages):
                parser.error('internal modes cannot be combined')
            if args.internal_packages:
                if args.suite_output:
                    parser.error('unexpected suite output')
                print(json.dumps({'python': platform.python_version(), 'machine': platform.machine(), 'platform': sys.platform,
                                  'packages': {row['name']: importlib.metadata.version(row['name']) for row in dependency_identity()}}))
                return 0
            if not args.suite_output:
                parser.error('suite output required')
            return suite_result(args.internal_suite, args.suite_output)
        if args.suite_output:
            parser.error('suite output requires internal suite')
        if args.check_report:
            if args.output or args.require_empty:
                parser.error('--check-report must be used alone')
            errors = validate_report(strict_json(args.check_report))
            print(json.dumps({'report_valid': not errors, 'errors': errors, 'fixture_only': True, 'runtime_eligible': False}))
            return bool(errors)
        if not args.output or not args.require_empty:
            parser.error('--output and --require-empty are required')
        reproduction(args.output)
        print(json.dumps({'reproduction': 'completed', 'report': args.output + '/reproduction.json', 'fixture_only': True, 'runtime_eligible': False}))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, RecursionError) as error:
        print(json.dumps({'reproduction': 'failed', 'error_type': type(error).__name__}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
