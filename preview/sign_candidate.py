#!/usr/bin/env python3
"""Sign a disposable Preview app copy using an already provisioned Keychain."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import package as packages


def run(*args):
    return subprocess.check_output([str(a) for a in args], text=True).strip()


def verify_identity(identity, keychain):
    identities = run('/usr/bin/security', 'find-identity', '-v', '-p',
                     'codesigning', keychain)
    fingerprints = re.findall(r'^\s*\d+\)\s+([0-9A-Fa-f]{40})\s', identities, re.M)
    if identity.upper() not in {value.upper() for value in fingerprints}:
        raise ValueError('Approved certificate is not a valid code-signing identity in the temporary keychain.')


def accepted_submission(archive, profile, keychain):
    receipt = json.loads(run('/usr/bin/xcrun', 'notarytool', 'submit', archive,
                             '--keychain-profile', profile, '--keychain', keychain,
                             '--wait', '--timeout', '15m', '--output-format', 'json'))
    submission = receipt.get('id', '')
    if receipt.get('status') != 'Accepted' or not re.fullmatch(
            r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', submission):
        raise ValueError('Notarization was not accepted; retain the submission in Apple history.')
    return {'id': submission, 'status': 'Accepted'}


def sign_candidate(app, output, identity, keychain, profile, revision, team):
    # Refuse private payloads and mutable/unidentified source before signing.
    packages.audit_app(app)
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('An exact source commit is required.')
    if not re.fullmatch(r'[0-9A-Fa-f]{40}', identity):
        raise ValueError('Use the exact Developer ID certificate SHA-1 identity.')
    if not re.fullmatch(r'[A-Z0-9]{10}', team) or not profile or not keychain.is_file():
        raise ValueError('An existing Keychain profile and Apple team are required.')
    if run('git', '-C', packages.REPO, 'rev-parse', 'HEAD') != revision or run(
            'git', '-C', packages.REPO, 'status', '--porcelain'):
        raise ValueError('The source must be clean and match the approved commit.')
    app = app.resolve()
    if output.is_symlink() or output.exists():
        raise ValueError('Select a fresh output directory.')
    output = output.resolve()
    if output == packages.REPO or app == output or app in output.parents:
        raise ValueError('Select a separate output directory.')
    verify_identity(identity, keychain)
    run('/usr/bin/codesign', '--verify', '--deep', '--strict', app)
    # Staging is outside both the input app and final output; failures cannot
    # overwrite an earlier candidate or leave a success-looking package behind.
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='pear-sign-', dir=output.parent) as scratch:
        root = Path(scratch)
        staged = root / app.name
        run('/usr/bin/ditto', app, staged)
        cli = staged / 'Contents/Resources/pear-preview'
        for target in (cli, staged):
            run('/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
                '--keychain', keychain, '--sign', identity, target)
            run('/usr/bin/codesign', '--verify', '--strict',
                '-R=anchor apple generic and certificate leaf[subject.OU] = "' + team + '"', target)
        app_zip, cli_zip = root / 'app.zip', root / 'cli.zip'
        run('/usr/bin/ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', staged, app_zip)
        run('/usr/bin/ditto', '-c', '-k', '--keepParent', cli, cli_zip)
        receipts = {name: accepted_submission(archive, profile, keychain)
                    for name, archive in [('app', app_zip), ('cli', cli_zip)]}
        run('/usr/bin/xcrun', 'stapler', 'staple', staged)
        # Existing release packaging checks require staple, Gatekeeper,
        # distribution assessment and explicit CLI notarization.
        built = root / 'packages'
        run('python3', '-B', packages.REPO / 'preview/package.py', '--app', staged,
            '--output', built, '--release')
        (built / 'notarization.json').write_text(json.dumps({
            'source_revision': revision, 'team_id': team, 'submissions': receipts,
            'distribution_signed': True, 'notarized': True, 'public_release': False,
            'gui_game_qualification': 'Not performed by this signing job',
        }, indent=2) + '\n')
        (built / 'CANDIDATE.txt').write_text(
            'SIGNED QUALIFICATION CANDIDATE. No public release is authorized.\n'
            'No runtime, Steam account, game or save data is included.\n'
            'Runtime delivery URL and local GUI/recovery/game checks remain separate.\n')
        shutil.move(str(built), str(output))
    return receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--identity', required=True)
    parser.add_argument('--keychain', type=Path, required=True)
    parser.add_argument('--notary-profile', required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--team', required=True)
    args = parser.parse_args()
    sign_candidate(args.app, args.output, args.identity, args.keychain,
                   args.notary_profile, args.revision, args.team)
    print('Signed candidate checks passed; local qualification remains required.')


if __name__ == '__main__':
    main()
