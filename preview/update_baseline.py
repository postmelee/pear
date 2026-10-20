#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Derive a separately notarized baseline without rebuilding unchanged nested code."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import tempfile
from sign_candidate import run, accepted_submission, verify_identity
from package import audit_app


def validate_configuration(info, config):
    if info.get('CFBundleIdentifier') != 'org.pear.rosetta-preview':
        raise ValueError('Unexpected app identity')
    if info.get('CFBundleVersion') != config['target_build']:
        raise ValueError('Target build mismatch')
    if not (0 < int(config['baseline_build']) < int(config['target_build'])):
        raise ValueError('Baseline must precede target')
    if (info.get('SUFeedURL') != config['qualification_feed'] or
            info.get('SUPublicEDKey') != config['public_key'] or
            info.get('SURequireSignedFeed') is not True or
            info.get('SUVerifyUpdateBeforeExtraction') is not True):
        raise ValueError('Qualification feed/key/verification mismatch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('packages', 'output', 'keychain'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('identity', 'team', 'notary-profile', 'revision'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    if run('git', '-C', repo, 'rev-parse', 'HEAD') != args.revision or run('git', '-C', repo, 'status', '--porcelain'):
        raise ValueError('Baseline requires exact clean source')
    if args.output.exists() or args.output.is_symlink():
        raise ValueError('Preserve previous baseline; select a fresh output')
    config = json.loads((repo / 'preview/update-public.json').read_text())
    manifest = json.loads((args.packages / 'package-manifest.json').read_text())
    if manifest.get('candidate') is not False or manifest.get('source_revision') != args.revision:
        raise ValueError('Expected source-matched notarized target packages')
    names = [n for n in manifest['artifacts'] if n.startswith('Pear-') and n.endswith('-macos-arm64.zip')]
    if len(names) != 1 or Path(names[0]).name != names[0]:
        raise ValueError('Expected one target app archive')
    archive = args.packages / names[0]
    source_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    if source_hash != manifest['artifacts'][names[0]]['sha256'] or archive.stat().st_size != manifest['artifacts'][names[0]]['size']:
        raise ValueError('Target archive identity mismatch')
    verify_identity(args.identity, args.keychain)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='pear-update-baseline-', dir=args.output.parent) as scratch:
        root = Path(scratch)
        run('/usr/bin/ditto', '-x', '-k', archive, root)
        app = root / 'Pear.app'
        audit_app(app)
        requirement = 'anchor apple generic and certificate leaf[subject.OU] = "' + args.team + '"'
        run('/usr/bin/codesign', '--verify', '--deep', '--strict', '-R=' + requirement, app)
        run('/usr/bin/xcrun', 'stapler', 'validate', app)
        info_path = app / 'Contents/Info.plist'
        info = plistlib.loads(info_path.read_bytes())
        validate_configuration(info, config)
        # Only the outer identity/version changes. Preserve signed CLI/framework bytes.
        preserved = {str(p.relative_to(app)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for top in ['Contents/Frameworks', 'Contents/Resources']
                     for p in (app / top).rglob('*') if p.is_file() and not p.is_symlink()}
        info['CFBundleVersion'] = config['baseline_build']
        info_path.write_bytes(plistlib.dumps(info, sort_keys=False))
        run('/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
            '--keychain', args.keychain, '--sign', args.identity, app)
        run('/usr/bin/codesign', '--verify', '--deep', '--strict', '-R=' + requirement, app)
        submission_zip = root / 'submission.zip'
        run('/usr/bin/ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', app, submission_zip)
        submission = accepted_submission(submission_zip, args.notary_profile, args.keychain)
        run('/usr/bin/xcrun', 'stapler', 'staple', app)
        run('/usr/bin/xcrun', 'stapler', 'validate', app)
        run('/usr/sbin/spctl', '--assess', '--type', 'execute', app)
        run('/usr/bin/syspolicy_check', 'distribution', app)
        audit_app(app)
        for relative, digest in preserved.items():
            if hashlib.sha256((app / relative).read_bytes()).hexdigest() != digest:
                raise ValueError('Nested code/resource changed during baseline signing')
        args.output.mkdir()
        name = 'Pear-update-baseline-build-' + config['baseline_build'] + '.zip'
        output = args.output / name
        run('/usr/bin/ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', app, output)
        receipt = dict(source_revision=args.revision, target_archive_sha256=source_hash,
                       baseline_build=config['baseline_build'], target_build=config['target_build'],
                       qualification_feed=config['qualification_feed'], notarization=submission,
                       nested_bytes_preserved=True, public_release=False,
                       artifact=dict(name=name, sha256=hashlib.sha256(output.read_bytes()).hexdigest(), size=output.stat().st_size))
        (args.output / 'baseline-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print('Notarized baseline ready; nested app resources preserved. Actual replacement still untested.')


if __name__ == '__main__':
    main()
