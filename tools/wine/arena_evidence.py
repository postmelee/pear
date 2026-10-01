#!/usr/bin/env python3
"""Offline, sanitized receipts for the retained native arena prerequisite.

Reuses only current pure parsers; never loads archived Python, invokes signing,
reauthorizes an old executable, runs the probe, or qualifies Wine or a game.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re

import pe_arena_probe as probe
import signing
from common import Error, decode_json, encoded, need, read_relative, sha256
from evidence import PROFILE_CHECKS
from toolchain import MACH_ARM64, inspect_macho

LEGACY_FAILED_SOURCES = {
    '496911207993150d7e1cbc78eeff05878a06311a2b3930c34308656f716c2419',
    'd941bc5c963c15bef7d5ece8cd36775c3598c3e980ee1dd22c24b32d193a6b01',
}
SCOPES = ('qualification', 'wine_execution', 'runtime_qualified', 'game_qualified')
JIT = 'com.apple.security.cs.allow-jit'


def digest(value):
    need(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'arena_receipt_digest')
    return value


def bound_bytes(root, name, expected, limit=4 * 1024 * 1024):
    data = read_relative(root, name, limit)
    need(hashlib.sha256(data).hexdigest() == digest(expected), 'arena_receipt_bytes_changed')
    return data


def recorded_signature(value, keys, page_size=None):
    """Validate recorded facts, explicitly without refreshing authorization."""
    need(isinstance(value, dict) and value.get('claim_keys') == sorted(keys) and
         all(value.get(key) is True for key in ('hardened_runtime', 'same_team', 'strict_verification')) and
         value.get('ad_hoc') is False and value.get('category') == 'apple_development',
         'arena_receipt_recorded_signature')
    page = value.get('code_directory_page_size')
    need(type(page) is int and page in (4096, 16384) and (page_size is None or page == page_size),
         'arena_receipt_signature_page')


def recorded_claims(claims, variant):
    """Check retained claim shape; profile-prefix matching is an at-run fact.

    An ApplicationIdentifierPrefix may differ from TeamIdentifier. No profile
    byte hash or decoded profile was archived in these prerequisite reports,
    so this receipt must not reconstruct or renew that original authorization.
    """
    need(variant in probe.VARIANTS and isinstance(claims, dict) and
         len(set(claims) & set(signing.CROSS_KEYS)) == 1, 'arena_receipt_recorded_claims')
    cross = next(iter(set(claims) & set(signing.CROSS_KEYS)))
    expected = {signing.APP_ID, signing.TEAM_ID, cross} | ({JIT} if variant == 'allow-jit' else set())
    application = claims.get(signing.APP_ID)
    suffix = '.' + signing.BUNDLE_ID
    need(set(claims) == expected and claims[cross] is True and
         isinstance(claims.get(signing.TEAM_ID), str) and bool(claims[signing.TEAM_ID]) and
         isinstance(application, str) and application.endswith(suffix) and
         len(application) > len(suffix) and '*' not in application and
         (variant != 'allow-jit' or claims[JIT] is True), 'arena_receipt_recorded_claims')
    return expected


def authorization_receipt(legacy):
    return {'scope': 'recorded_at_run_not_reauthorized',
            'profile_checks': {key: True for key in sorted(PROFILE_CHECKS)},
            'profile_byte_hash_binding': 'unavailable_not_retained_at_run',
            'bundle_metadata_byte_binding': 'unavailable_not_retained_at_run',
            'current_profile_authorization_assessed': False,
            'current_bundle_signature_verified': False,
            'signed_binary_origin': 'verified_against_retained_unsigned_bytes',
            'hardened_runtime': True, 'library_validation': 'enabled',
            'native_probe_signature_page_bytes': 4096, 'ordinary_helpers_have_empty_claims': True,
            'allow_jit_empirically_required': False if not legacy else None}


def verify_artifacts(root, report):
    binaries, helpers = report.get('binaries'), report.get('helpers')
    need(isinstance(binaries, dict) and set(binaries) == set(probe.VARIANTS) and
         isinstance(helpers, dict) and set(helpers) == {'helper', 'sentinel'}, 'arena_receipt_artifact_coverage')
    checks = report.get('profile_checks', {})
    need(PROFILE_CHECKS <= set(checks) and all(checks[key] is True for key in PROFILE_CHECKS),
         'arena_receipt_recorded_profile')
    for role, row in helpers.items():
        bound_bytes(root, role, row.get('sha256'))
        bound_bytes(root, 'unsigned-' + role, row.get('unsigned_sha256'))
        source = 'tests/wine/fixtures/' + ('api_launch.c' if role == 'helper' else 'sentinel.c')
        need(row.get('source_sha256') == report['inputs'][source] and
             report['helper_sha256'].get(role) == row['sha256'], 'arena_receipt_helper_identity')
        recorded_signature(row.get('signature'), set())
        signing.verify_code_origin(root / ('unsigned-' + role), root / role)
        need(inspect_macho(root / role)['architectures'] == [MACH_ARM64], 'arena_receipt_helper_architecture')
    for variant, row in binaries.items():
        name = row.get('name')
        need(isinstance(name, str) and re.fullmatch('pear-arena-[a-z0-9]{1,32}', name), 'arena_receipt_binary_name')
        relative = variant + '/ArenaProbe.app/Contents/MacOS/' + name
        path = root / relative
        need(row.get('path') == str(path), 'arena_receipt_binary_path')
        bound_bytes(root, relative, row.get('sha256'))
        bound_bytes(root, 'unsigned-probe', row.get('unsigned_sha256'))
        expected = recorded_claims(row.get('claims'), variant)
        recorded_signature(row.get('signature'), expected, 4096)
        signing.verify_code_origin(root / 'unsigned-probe', path)
        need(inspect_macho(path)['architectures'] == [MACH_ARM64] and
             probe.base.bound_macho_uuid(path, row['sha256']) == row.get('uuid'), 'arena_receipt_binary_identity')
    return binaries


def case_receipt(root, row, binary, policy, legacy=False):
    variant, mode = row['variant'], row['mode']
    name = variant + '-' + mode
    stored = decode_json(read_relative(root, name + '/case.json'))
    need(stored == row, 'arena_receipt_case_mismatch')
    need(row.get('schema_version') == 1 and row.get('record_kind') == 'pear_pe_arena_case' and
         all(row.get(key) is False for key in SCOPES), 'arena_receipt_case_scope')
    need(row.get('policy') == (None if legacy else policy), 'arena_receipt_case_policy')
    logs = row.get('logs')
    expected_logs = {(role, channel) for role in ('probe', 'sentinel') for channel in ('stdout', 'stderr')}
    need(isinstance(logs, list) and len(logs) == 4 and
         {(item.get('role'), item.get('channel')) for item in logs} == expected_logs,
         'arena_receipt_log_coverage')
    raw = {}
    for item in logs:
        key = item['role'], item['channel']
        need(item.get('path') == '.'.join(key) + '.log', 'arena_receipt_log_path')
        data = bound_bytes(root, name + '/' + item['path'], item.get('sha256'), probe.base.STREAM_LIMIT)
        need(type(item.get('bytes')) is int and item['bytes'] == len(data) == item.get('observed_bytes') and
             item.get('eof') is True and item.get('write_error') is None, 'arena_receipt_log_integrity')
        raw[key] = data
    probe.validate_supervision(row, raw)
    need(set(row['processes']) == {'probe', 'sentinel'} and all(
         child.get('setup_error') is None and child.get('emergency_cleanup') is None
         for child in row['processes'].values()), 'arena_receipt_process_scope')
    for cleanup, role in [('cleanup', 'probe'), ('sentinel_cleanup', 'sentinel')]:
        value = row[cleanup]
        need(value.get('complete') is True and value.get('errors') == [] and
             value.get('observation_gap') is False and value.get('reaped') == {role: True} and
             value.get('signals') == [], 'arena_receipt_cleanup')
    records = probe.records(raw['probe', 'stdout'])
    need(records[1:] == row.get('observations'), 'arena_receipt_observation_mismatch')
    # The two known failed pre-policy sources used the thread-JIT protocol.
    # Adapt only an in-memory copy for current prelude/failure parsers; the
    # original records and failed verdict are never relabeled as a success.
    interpreted = [records[0], *[{**item, 'policy': policy} for item in records[1:]]] if legacy else records
    observations = probe.validate_ready(interpreted, row['processes']['probe']['identity'],
                                         row['nonce'], mode, policy=policy)
    failure = probe.first_native_failure(observations, mode, policy)
    if legacy:
        need(row.get('passed') is False and row.get('crash') is None and failure is not None and
             row['processes']['probe']['exit_code'] in (66, 67), 'arena_receipt_legacy_failure')
        stored_failure = row.get('native_failure')
        if stored_failure is not None:
            need(stored_failure == {key: value for key, value in failure.items() if key != 'policy'},
                 'arena_receipt_native_failure_mismatch')
        matched = None
    else:
        need(row.get('passed') is True and row.get('assessment_error') is None and
             failure is None and row.get('native_failure') is None, 'arena_receipt_case_failed')
        probe.validate_lifecycle(observations, mode, row['processes']['probe']['exit_code'], policy=policy)
        matched = None
        if mode != 'lifecycle':
            crash = row.get('crash')
            need(isinstance(crash, dict) and crash.get('path') == 'crash.ips', 'arena_receipt_crash_missing')
            data = bound_bytes(root, name + '/crash.ips', crash.get('sha256'), probe.CRASH_LIMIT)
            matched = probe.crash_matches(probe.parse_crash(data), row,
                       probe.unique_event(observations, 'fault_armed'), binary)
            need(crash == {'path': 'crash.ips', 'sha256': hashlib.sha256(data).hexdigest(), **matched},
                 'arena_receipt_crash_mismatch')
        else:
            need(row.get('crash') is None, 'arena_receipt_unexpected_crash')
    return {'variant': variant, 'mode': mode, 'policy': policy, 'passed': not legacy,
            'case_sha256': sha256(root / name / 'case.json'),
            'exit_code': row['processes']['probe']['exit_code'],
            'cleanup_complete': True, 'sentinel_survived': True,
            'actual_observation_counts': {event: sum(item.get('event') == event for item in observations)
                for event in ('publication', 'leaf_return', 'mutator_return', 'retirement')},
            'native_failure': failure,
            'fault_control': None if matched is None else {
                'signal': matched['signal'], 'matched': True, 'process_birth_matched': True,
                'signed_image_uuid_matched': True, 'crash_sha256': row['crash']['sha256']}}


def export(root):
    root = signing.owned(root)
    raw = read_relative(root, 'report.json')
    report = decode_json(raw)
    need(report.get('schema_version') == 1 and report.get('record_kind') == 'pear_pe_arena_prerequisite' and
         all(report.get(key) is False for key in SCOPES), 'arena_receipt_scope')
    legacy = report.get('policy') is None
    if legacy:
        need(report.get('source_sha256') in LEGACY_FAILED_SOURCES and report.get('status') == 'failed' and
             report.get('native_prerequisite_passed') is False, 'arena_receipt_legacy_scope')
    else:
        need(report.get('policy') == 'page-wx' and report.get('status') == 'passed' and
             report.get('native_prerequisite_passed') is True, 'arena_receipt_current_scope')
    policy = 'thread-jit' if legacy else 'page-wx'
    inputs = report.get('inputs')
    names = (*probe.PRODUCER_FILES, *probe.SOURCE_FILES, probe.LOCK_FILE)
    need(isinstance(inputs, dict) and set(inputs) == set(names) and report.get('producer_sha256') ==
         {name: inputs[name] for name in probe.PRODUCER_FILES} and
         report.get('source_sha256') == inputs[probe.SOURCE_FILES[0]], 'arena_receipt_input_binding')
    for name, expected in inputs.items(): bound_bytes(root, 'inputs/' + name, expected)
    binaries = verify_artifacts(root, report)
    toolchain = report.get('toolchain', {})
    need(toolchain.get('lock_sha256') == inputs[probe.LOCK_FILE], 'arena_receipt_toolchain_binding')
    digest(toolchain.get('clang', {}).get('sha256'))
    events = report.get('events')
    need(isinstance(events, list) and events and all(item.get('exit_code') == 0 and
         item.get('failure') is None and item.get('cleanup_failure') is None for item in events),
         'arena_receipt_tool_failure')
    operations = [item.get('operation') for item in events]
    for label in ('helper', 'sentinel', 'original-claims', 'allow-jit'):
        for suffix in ('verify', 'metadata', 'claims'):
            need('post.' + label + '.' + suffix in operations, 'arena_receipt_final_signature_observation')
    for item in events:
        if item.get('operation') in ('compile.helper', 'compile.sentinel', 'compile.probe'):
            for channel in ('stdout', 'stderr'):
                log = item[channel]
                need(log.get('path') == item['operation'] + '.' + channel + '.log', 'arena_receipt_compile_log_path')
                data = bound_bytes(root, log['path'], log.get('sha256'))
                need(log.get('bytes') == len(data), 'arena_receipt_compile_log_integrity')
    expected = [('original-claims', 'lifecycle')] + [('allow-jit', mode) for mode in probe.POLICIES[policy]]
    cases = report.get('cases')
    need(isinstance(cases, list) and [(row.get('variant'), row.get('mode')) for row in cases] == expected,
         'arena_receipt_case_coverage')
    public_cases = [case_receipt(root, row, binaries[row['variant']], policy, legacy) for row in cases]
    need(sha256(root / 'report.json') == hashlib.sha256(raw).hexdigest(), 'arena_receipt_report_changed')
    return {'schema_version': 1, 'record_kind': 'pear_native_arena_observations',
            'scope': 'historical_native_prerequisite_receipt', 'policy': policy,
            'legacy_policy_interpretation': legacy, 'report_sha256': hashlib.sha256(raw).hexdigest(),
            'source_sha256': report['source_sha256'], 'input_sha256': inputs,
            'native_prerequisite_passed': not legacy, 'cases': public_cases,
            'authorization': authorization_receipt(legacy),
            'receipt_parser_sha256': sha256(Path(__file__)),
            'current_probe_parser_sha256': sha256(Path(probe.__file__)),
            'wine_execution': False, 'runtime_qualified': False, 'game_qualified': False,
            'limits': ['Offline validation does not renew signing or provisioning authorization.',
                       'Current pure parsers read hash-bound snapshots; archived Python is never executed.',
                       'Fixed single-thread native code does not qualify the Wine loader, FEX or a game.',
                       'Historical signature facts are retained; raw signing-tool output was not archived.',
                       'At-run hashes of profiles and bundle metadata were not retained; their present bytes are not authenticated by this receipt.',
                       'Private identities, addresses, paths and crashes are excluded from this receipt.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        value = export(args.root)
        output = signing.owned(args.output)
        with output.open('xb') as stream: stream.write(encoded(value))
    except (Error, OSError, KeyError, TypeError, ValueError) as exc:
        print(getattr(exc, 'code', 'arena_receipt_failed'))
        return 1
    print('Native prerequisite receipt written; Wine and game qualification remain false.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
