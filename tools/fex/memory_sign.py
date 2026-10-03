#!/usr/bin/env python3
"""Authorize individual finite ARM64 prototypes; this does not execute them."""
import argparse
from pathlib import Path
import plistlib
import shutil
import sys
if __package__:
    from .common import REPO, Error, need, load_json, operation_output, read_relative, sha256, write_json
else:
    from common import REPO, Error, need, load_json, operation_output, read_relative, sha256, write_json
if __package__:
    from .memory_check import verify_build, ARTIFACTS
else:
    from memory_check import verify_build, ARTIFACTS
if __package__:
    from .memory_reuse import wine_namespace
else:
    from memory_reuse import wine_namespace

PRODUCERS = ('tools/fex/memory_sign.py', 'tools/fex/memory_check.py', 'tools/fex/memory_reuse.py',
             'tools/wine/signing.py', 'tools/wine/run_fixtures.py', 'tools/wine/toolchain.py',
             'tools/wine/build.py', 'tools/wine/common.py', 'tools/wine/prepare.py',
             'host/probe/provisioned_probe.py', 'host/probe/hardened_baseline.py')


def sign(artifact, profile, output):
    artifact = Path(artifact).absolute()
    built = verify_build(artifact)
    root = operation_output(output, require_empty=True)
    value = {'schema_version': 1, 'record_kind': 'fex_memory_prototype_signing',
             'scope': 'finite_native_owner', 'build_ref': {'path': str(artifact), 'sha256': sha256(artifact / 'build.json')},
             'producers': {}, 'operations': [], 'artifacts': [], 'passed': False,
             'native_execution': False, 'runtime_eligible': False}
    with wine_namespace() as (signing, observer):
        original = signing._native
        def recording(argv, label, events, timeout=30):
            stdout, stderr = original(argv, label, events, timeout)
            target = root / 'private-tools' / label
            target.mkdir(parents=True)
            logs = {}
            for channel, raw in [('stdout', stdout), ('stderr', stderr)]:
                path = target / channel
                path.write_bytes(raw)
                logs[channel] = {'path': path.relative_to(root).as_posix(), 'sha256': sha256(path), 'bytes': len(raw)}
            events[-1]['private_logs'] = logs
            return stdout, stderr
        signing._native = recording
        try:
            for name in PRODUCERS:
                raw = read_relative(REPO, name, 2 * 1024**2)
                target = root / 'producers' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                value['producers'][name] = sha256(target)
            auth = signing._authorization(profile, signing.BUNDLE_ID, value['operations'])
            claims = signing.loader_claims(auth, 'page-wx')
            value['authorization'] = {key: auth[key] for key in
               ['profile_sha256', 'claims', 'identity', 'checks', 'granted_cross_architecture_key']}
            value['loader_claims'] = claims
            claims_path = root / 'claims.plist'
            claims_path.write_bytes(plistlib.dumps(claims, sort_keys=True))
            value['claims_sha256'] = sha256(claims_path)
            empty_path = root / 'empty.plist'
            empty_path.write_bytes(plistlib.dumps({}))
            for index, name in enumerate(ARTIFACTS):
                original_unsigned = artifact / 'unsigned' / name
                expected_unsigned = next(row for row in built['artifacts'] if row['path'] == 'unsigned/' + name)
                raw_unsigned = read_relative(artifact, 'unsigned/' + name, 2 * 1024**2)
                from hashlib import sha256 as hash_bytes
                need(hash_bytes(raw_unsigned).hexdigest() == expected_unsigned['sha256'] and
                     len(raw_unsigned) == expected_unsigned['size_bytes'], 'memory_signing_source_changed')
                unsigned = root / 'unsigned' / name
                unsigned.parent.mkdir(exist_ok=True)
                unsigned.write_bytes(raw_unsigned)
                if index < 2:
                    bundle = root / (name + '.app')
                    contents = bundle / 'Contents'
                    target = contents / 'MacOS' / name
                    target.parent.mkdir(parents=True)
                    (contents / 'Info.plist').write_bytes(plistlib.dumps({
                        'CFBundleIdentifier': signing.BUNDLE_ID, 'CFBundleExecutable': name,
                        'CFBundleName': name, 'CFBundlePackageType': 'APPL', 'CFBundleVersion': '1'}))
                    (contents / 'embedded.provisionprofile').write_bytes(auth['profile_bytes'])
                    identifier = signing.BUNDLE_ID
                    selected_claims = claims
                    signing_target = bundle
                    entitlement_file = claims_path
                else:
                    target = root / 'helpers' / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    identifier = signing.BUNDLE_ID + '.finite.' + name
                    selected_claims = {}
                    signing_target = target
                    entitlement_file = empty_path
                shutil.copyfile(unsigned, target)
                target.chmod(0o755)
                argv = ['/usr/bin/codesign', '--force', '--sign', auth['identity'], '--options', 'runtime',
                        '--timestamp=none', '--pagesize', '4096', '--entitlements', str(entitlement_file),
                        '--identifier', identifier, str(signing_target)]
                recording(argv, name + '.sign', value['operations'])
                facts = signing._signature(target, selected_claims, auth['claims'][signing.TEAM_ID], name, value['operations'])
                origin = signing.verify_code_origin(unsigned, target)
                value['artifacts'].append({'name': name, 'path': target.relative_to(root).as_posix(),
                    'sha256': sha256(target), 'unsigned_sha256': sha256(unsigned), 'signature': facts, 'code_origin': origin})
            need(value['producers'] == {name: sha256(REPO / name) for name in PRODUCERS}, 'memory_signing_inputs_changed')
            value['passed'] = True
            write_json(root / 'signing.json', value)
            return value
        except (Error, signing.Error, OSError, ValueError, KeyError) as error:
            value['error'] = getattr(error, 'code', type(error).__name__)
            write_json(root / 'failed.json', value)
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', required=True)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--require-empty', required=True, action='store_true')
    args = parser.parse_args()
    try:
        sign(args.artifact, args.profile, args.output)
        print('Individual signatures and authorization verified; native execution remains unperformed.')
        return 0
    except Exception as error:
        # Normalize imported historical Error classes without leaking private tool output.
        print(getattr(error, 'code', type(error).__name__), file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
