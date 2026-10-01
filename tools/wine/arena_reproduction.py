"""Reconstruct the current finite native arena prerequisite under fresh authorization.

The historical receipt parser stays unchanged. This wrapper snapshots current
inputs and the authorized profile, delegates six bounded page-W^X cases to the
existing owner, and separately verifies actual bundle metadata and signatures.
Only run() compiles, signs or executes the original probe; validate() rechecks
fresh development authorization and signatures but never executes probe code.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import plistlib
import re
import sys

import arena_evidence
import pe_arena_probe as probe
import signing
from common import Error, REPO, decode_json, encoded, need, read_relative, sha256

SCOPE = 'fresh_native_arena_prerequisite'
PRODUCER_FILES = tuple(sorted(set((*probe.PRODUCER_FILES, *probe.SOURCE_FILES,
    probe.LOCK_FILE, 'tools/wine/arena_reproduction.py', 'tools/wine/arena_evidence.py',
    'tools/wine/evidence.py', 'tools/wine/verify.py', 'tools/wine/build.py'))))
RECEIPT = 'reproduction.json'
PROFILE = 'authorized.provisionprofile'
SCOPES = {'wine_execution': False, 'runtime_qualified': False, 'game_qualified': False}


def exact(left, right, code):
    need(encoded(left) == encoded(right), code)


def _read(root, name):
    return decode_json(read_relative(root, name))


def _write(root, name, value):
    probe.base.write_new(root / name, value)


def _hashes():
    return {name: sha256(REPO / name) for name in PRODUCER_FILES}


def _snapshot(root):
    hashes = {}
    for name in PRODUCER_FILES:
        raw = read_relative(REPO, name, 4 * 1024 * 1024)
        path = root / 'inputs' / name
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with path.open('xb') as stream:
            stream.write(raw)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    exact(hashes, _hashes(), 'fresh_arena_input_changed')
    return hashes


def _start(root, local_signing):
    local_path = signing.owned(local_signing)
    local = signing._local_input(local_path)
    local_hash = sha256(local_path)
    profile = Path(local['profile_path'])
    raw = read_relative(profile.parent, profile.name, signing.LIMIT)
    profile_hash = hashlib.sha256(raw).hexdigest()
    with (root / PROFILE).open('xb') as stream:
        stream.write(raw)
    events = []
    authorized = signing._authorization(profile, signing.BUNDLE_ID, events)
    need(authorized['profile_sha256'] == profile_hash and
         sha256(profile) == profile_hash and sha256(local_path) == local_hash,
         'fresh_arena_authorization_changed')
    value = {'schema_version': 1, 'record_kind': 'pear_native_arena_reproduction_start',
        'scope': SCOPE, 'policy': 'page-wx', 'probe_output_initially_absent': not (root / 'probe').exists(),
        'input_sha256': _snapshot(root), 'local_signing': {'path': str(local_path), 'sha256': local_hash},
        'profile': {'path': str(profile), 'sha256': profile_hash, 'snapshot': PROFILE},
        'profile_checks': authorized['checks'], 'authorization_events': events, **SCOPES}
    need(value['probe_output_initially_absent'] is True, 'fresh_arena_probe_exists')
    _write(root, 'start.json', value)
    return value


def _validate_start(root, local_signing):
    start = _read(root, 'start.json')
    need(set(start) == {'schema_version', 'record_kind', 'scope', 'policy',
        'probe_output_initially_absent', 'input_sha256', 'local_signing', 'profile',
        'profile_checks', 'authorization_events', *SCOPES}, 'fresh_arena_start_shape')
    need(type(start['schema_version']) is int and start['schema_version'] == 1 and
         start['record_kind'] == 'pear_native_arena_reproduction_start' and start['scope'] == SCOPE and
         start['policy'] == 'page-wx' and start['probe_output_initially_absent'] is True and
         all(start[key] is False for key in SCOPES), 'fresh_arena_start_scope')
    exact(start['input_sha256'], _hashes(), 'fresh_arena_current_input_changed')
    for name, digest in start['input_sha256'].items():
        need(hashlib.sha256(read_relative(root, 'inputs/' + name, 4 * 1024 * 1024)).hexdigest() == digest,
             'fresh_arena_input_snapshot_changed')
    local_path = signing.owned(local_signing)
    exact(start['local_signing'], {'path': str(local_path), 'sha256': sha256(local_path)},
          'fresh_arena_local_input_changed')
    local = signing._local_input(local_path)
    profile = Path(local['profile_path'])
    need(set(start['profile']) == {'path', 'sha256', 'snapshot'} and
         start['profile']['path'] == str(profile) and start['profile']['snapshot'] == PROFILE,
         'fresh_arena_profile_reference_changed')
    digest = hashlib.sha256(read_relative(root, PROFILE, signing.LIMIT)).hexdigest()
    need(digest == start['profile']['sha256'] == sha256(profile), 'fresh_arena_profile_changed')
    need(arena_evidence.PROFILE_CHECKS <= set(start['profile_checks']) and
         all(start['profile_checks'][key] is True for key in arena_evidence.PROFILE_CHECKS),
         'fresh_arena_initial_authorization_failed')
    _events(start['authorization_events'])
    return start


def _events(events):
    need(isinstance(events, list) and events and all(isinstance(row, dict) and
         type(row.get('exit_code')) is int and row['exit_code'] == 0 and
         row.get('failure') is None and row.get('cleanup_failure') is None for row in events),
         'fresh_arena_tool_failed')


def _toolchain(report):
    lock = _read(REPO, probe.LOCK_FILE)
    clang = probe.native_tool(lock, 'clang')
    probe.native_tool(lock, 'codesign')
    observed = {'lock_sha256': sha256(REPO / probe.LOCK_FILE),
        'clang': {'path': str(clang), 'sha256': sha256(clang.resolve())},
        'sdk': probe.inspect_sdk(lock)}
    exact(report['toolchain'], observed, 'fresh_arena_toolchain_changed')
    return observed


def _artifacts(root, report, auth, events):
    """Bind metadata to the compiled plist and inspect every actual signed object."""
    target = root / 'probe'
    compiled_info = read_relative(target, 'Info.plist', signing.LIMIT)
    try:
        info = plistlib.loads(compiled_info)
    except (ValueError, TypeError, plistlib.InvalidFileException):
        raise Error('fresh_arena_info_invalid') from None
    need(isinstance(info, dict) and info.get('CFBundleIdentifier') == signing.BUNDLE_ID,
         'fresh_arena_info_identity')
    profile = read_relative(root, PROFILE, signing.LIMIT)
    team = auth['claims'][signing.TEAM_ID]
    state = {'compiled_info_sha256': hashlib.sha256(compiled_info).hexdigest(), 'bundles': {}, 'helpers': {}}
    for variant in probe.VARIANTS:
        row = report['binaries'][variant]
        contents = target / variant / 'ArenaProbe.app/Contents'
        main = contents / 'MacOS' / row['name']
        need(info.get('CFBundleExecutable') == row['name'] and
             read_relative(contents, 'Info.plist', signing.LIMIT) == compiled_info and
             read_relative(contents, 'embedded.provisionprofile', signing.LIMIT) == profile,
             'fresh_arena_bundle_metadata_changed')
        claims = dict(auth['claims'])
        if variant == 'allow-jit':
            claims[signing.PROFILE.BASELINE.ALLOW_JIT] = True
        exact(row['claims'], claims, 'fresh_arena_claims_changed')
        claims_bytes = read_relative(target, variant + '/claims.plist', signing.LIMIT)
        try:
            exact(plistlib.loads(claims_bytes), claims, 'fresh_arena_claims_changed')
        except (ValueError, TypeError, plistlib.InvalidFileException):
            raise Error('fresh_arena_claims_invalid') from None
        before = signing.inventory(contents.parent)
        signing._signature(main, claims, team, 'fresh.' + variant, events)
        signing._signature(contents.parent, claims, team, 'fresh.' + variant + '.bundle', events)
        exact(signing.inventory(contents.parent), before, 'fresh_arena_bundle_changed')
        exact(probe.inspect_closure(main, contents.parent), row['closure'], 'fresh_arena_closure_changed')
        state['bundles'][variant] = {'inventory': before, 'claims_sha256': hashlib.sha256(claims_bytes).hexdigest()}
    for role in ('helper', 'sentinel'):
        main = target / role
        before = sha256(main)
        signing._signature(main, {}, team, 'fresh.' + role, events)
        exact(probe.inspect_closure(main, target), report['helpers'][role]['closure'], 'fresh_arena_closure_changed')
        need(sha256(main) == before == report['helpers'][role]['sha256'], 'fresh_arena_helper_changed')
        state['helpers'][role] = before
    _events(events)
    return state


def _assess(root, local_signing):
    start = _validate_start(root, local_signing)
    target = root / 'probe'
    report_raw = read_relative(target, 'report.json')
    report = decode_json(report_raw)
    need(report.get('status') == 'passed' and report.get('native_prerequisite_passed') is True,
         'fresh_arena_probe_failed')
    names = (*probe.PRODUCER_FILES, *probe.SOURCE_FILES, probe.LOCK_FILE)
    exact(report['inputs'], {name: start['input_sha256'][name] for name in names},
          'fresh_arena_probe_inputs_changed')
    # This existing pure parser checks all six cases, including the original-
    # claims control, raw logs, actual fault reports, code origin and cleanup.
    historical_parser_result = arena_evidence.export(target)
    need(historical_parser_result['policy'] == 'page-wx' and
         historical_parser_result['native_prerequisite_passed'] is True and
         historical_parser_result['legacy_policy_interpretation'] is False,
         'fresh_arena_probe_scope')
    toolchain = _toolchain(report)
    events = []
    auth = signing._authorization(Path(start['profile']['path']), signing.BUNDLE_ID, events)
    need(auth['profile_sha256'] == start['profile']['sha256'], 'fresh_arena_profile_changed')
    state = _artifacts(root, report, auth, events)
    exact(_validate_start(root, local_signing), start, 'fresh_arena_start_changed')
    need(hashlib.sha256(report_raw).hexdigest() == sha256(target / 'report.json'), 'fresh_arena_report_changed')
    # Public values are selected explicitly; profile/certificate identifiers,
    # paths, process identities, addresses and raw diagnostics remain private.
    summary = {'schema_version': 1, 'record_kind': 'pear_native_arena_reproduction_observations',
        'scope': SCOPE, 'policy': 'page-wx', 'gate_passed': True,
        'report_sha256': hashlib.sha256(report_raw).hexdigest(),
        'source_sha256': report['source_sha256'], 'input_sha256': start['input_sha256'],
        'compiler_sha256': toolchain['clang']['sha256'], 'sdk_settings_sha256': toolchain['sdk']['settings_sha256'],
        'cases': historical_parser_result['cases'],
        'authorization': {'scope': 'fresh_development_authorization_and_signature_checks',
            'profile_snapshot_bound': True, 'bundle_metadata_bound': True,
            'current_profile_authorization_assessed': True, 'current_bundle_signature_verified': True,
            'hardened_runtime': True, 'library_validation': 'enabled',
            'ordinary_helpers_have_empty_claims': True, 'native_probe_signature_page_bytes': 4096,
            'allow_jit_empirically_required': False},
        'limits': ['Six original single-thread native cases do not execute Wine, FEX or a game.',
                   'Separate newly signed probe bytes do not replace final Wine-suite validation.',
                   'The two obsolete failed source revisions remain historical; they are not rerun.'], **SCOPES}
    return summary, state, events


def failure_code(exc):
    """Use the coordinator's bounded wire grammar; private reports retain detail."""
    value = exc.code if isinstance(exc, Error) else 'fresh_arena_' + type(exc).__name__
    value = value.lower() if type(value) is str else ''
    return value if re.fullmatch('[a-z0-9_.:-]{1,160}', value) else 'fresh_arena_error'


def run(local_signing, output):
    """Own one fresh attempt; retain its failed terminal before propagating errors."""
    root = probe.base.create_output(output)
    result = {'schema_version': 1, 'record_kind': 'pear_native_arena_reproduction',
        'scope': SCOPE, 'policy': 'page-wx', 'status': 'failed', 'gate_passed': False,
        'error': None, **SCOPES}
    try:
        _start(root, local_signing)
        result['start_sha256'] = sha256(root / 'start.json')
        probe_report = probe.run(local_signing, root / 'probe', True, policy='page-wx')
        need(probe_report.get('native_prerequisite_passed') is True,
             probe_report.get('error') or 'fresh_arena_probe_failed')
        summary, state, events = _assess(root, local_signing)
        result.update(status='passed', gate_passed=True, observations=summary,
                      artifacts=state, verification_events=events)
    except BaseException as exc:
        result['error'] = failure_code(exc)
        result['failure_type'] = type(exc).__name__
        if isinstance(exc, Error):
            result['original_error'] = str(exc.code)[:512]
    finally:
        _write(root, RECEIPT, result)
    need(result['gate_passed'] is True, result['error'] or 'fresh_arena_failed')
    return result


def validate(root, local_signing):
    """Independently recheck fresh evidence; never execute retained native code."""
    root = signing.owned(root)
    raw = read_relative(root, RECEIPT)
    result = decode_json(raw)
    need(set(result) == {'schema_version', 'record_kind', 'scope', 'policy', 'status', 'gate_passed',
         'error', 'start_sha256', 'observations', 'artifacts', 'verification_events', *SCOPES},
         'fresh_arena_receipt_shape')
    need(type(result['schema_version']) is int and result['schema_version'] == 1 and
         result['record_kind'] == 'pear_native_arena_reproduction' and result['scope'] == SCOPE and
         result['policy'] == 'page-wx' and result['status'] == 'passed' and result['gate_passed'] is True and
         result['error'] is None and all(result[key] is False for key in SCOPES), 'fresh_arena_receipt_scope')
    need(result['start_sha256'] == sha256(root / 'start.json'), 'fresh_arena_start_changed')
    _events(result['verification_events'])
    observed, state, _ = _assess(root, local_signing)
    exact(observed, result['observations'], 'fresh_arena_observations_changed')
    exact(state, result['artifacts'], 'fresh_arena_artifacts_changed')
    need(sha256(root / RECEIPT) == hashlib.sha256(raw).hexdigest() and
         result['start_sha256'] == sha256(root / 'start.json'), 'fresh_arena_receipt_changed')
    return {**observed, 'reproduction_sha256': hashlib.sha256(raw).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('run', 'validate'))
    parser.add_argument('--local-signing', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        result = run(args.local_signing, args.output) if args.operation == 'run' else validate(args.output, args.local_signing)
        print(encoded({'scope': SCOPE, 'gate_passed': result['gate_passed'], **SCOPES}).decode(), end='')
        return 0
    except (Error, OSError, ValueError, KeyError, TypeError) as exc:
        print(encoded({'scope': SCOPE, 'gate_passed': False,
            'error': exc.code if isinstance(exc, Error) else 'fresh_arena_failed', **SCOPES}).decode(), end='')
        return 3


if __name__ == '__main__':
    sys.exit(main())
