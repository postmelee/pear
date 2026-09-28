"""Export allowlisted Stage 1 facts after validating their local raw evidence."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

from common import Error, HEX256, REPO, decode_json, encoded, load_json, need, read_relative, record, sha256
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--toolchain', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--failed-attempt', action='append', default=[])
    args = parser.parse_args(argv)
    try:
        result = export(args.inputs, args.config, args.toolchain, args.failed_attempt)
        path = Path(args.output)
        need(path.resolve().is_relative_to(REPO / 'mydocs/working') and not path.exists(), 'export_destination')
        with path.open('xb') as stream:
            stream.write(encoded(result))
    except (Error, OSError, ValueError, KeyError, TypeError) as exc:
        print(encoded({'error': getattr(exc, 'code', 'evidence_export_failed')}).decode(), end='')
        return 1
    print('Sanitized Stage 1 evidence exported after local gate validation.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
