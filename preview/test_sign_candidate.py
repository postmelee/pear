"""Synthetic candidate boundary checks; no Apple tools or credentials required."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sign_candidate as s

REV = 'a' * 40
IDENTITY = 'b' * 40
SUBMISSION = '12345678-1234-1234-1234-123456789abc'


class CandidateSigningTests(unittest.TestCase):
    def fixture(self, root):
        app = root / 'input/Pear Preview.app'
        for name in s.packages.REQUIRED | {'Contents/Resources/licenses/test.txt'}:
            p = app / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b'public fixture')
        keychain = root / 'fixture.keychain-db'
        keychain.write_bytes(b'synthetic keychain')
        return app, keychain

    def invoke(self, app, out, keychain, revision=REV):
        return s.sign_candidate(app, out, IDENTITY, keychain, 'test', revision, 'XH6JHKYXV8')

    def test_private_payload_refused_before_commands(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); app, keychain = self.fixture(root)
            (app / 'Contents/Resources/private.txt').write_text('must not ship')
            with patch.object(s, 'run') as command:
                with self.assertRaisesRegex(ValueError, 'Unexpected'):
                    self.invoke(app, root / 'out', keychain)
                command.assert_not_called()

    def test_source_mismatch_or_dirty_tree_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); app, keychain = self.fixture(root)
            for responses in [('c' * 40,), (REV, ' M source')]:
                with patch.object(s, 'run', side_effect=responses):
                    with self.assertRaisesRegex(ValueError, 'clean and match'):
                        self.invoke(app, root / 'out', keychain)
                self.assertFalse((root / 'out').exists())

    def test_existing_candidate_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); app, keychain = self.fixture(root)
            out = root / 'out'; out.mkdir(); (out / 'keep').write_text('prior candidate')
            with patch.object(s, 'run', side_effect=[REV, '']):
                with self.assertRaisesRegex(ValueError, 'fresh'):
                    self.invoke(app, out, keychain)
            self.assertEqual((out / 'keep').read_text(), 'prior candidate')

    def test_exact_valid_identity_required(self):
        with patch.object(s, 'run', return_value='  1) ' + IDENTITY.upper() + ' "Synthetic Developer ID"'):
            s.verify_identity(IDENTITY, Path('temporary.keychain-db'))
        for output in ('0 valid identities found',
                       '  1) ' + 'c' * 40 + ' "Different identity"',
                       'Diagnostic text mentioning ' + IDENTITY):
            with self.subTest(output=output), patch.object(s, 'run', return_value=output):
                with self.assertRaisesRegex(ValueError, 'not a valid code-signing identity'):
                    s.verify_identity(IDENTITY, Path('temporary.keychain-db'))

    def test_notary_requires_acceptance_and_valid_receipt(self):
        for receipt in [{'id': SUBMISSION, 'status': 'Invalid'},
                        {'id': SUBMISSION, 'status': 'In Progress'},
                        {'id': 'invalid-id', 'status': 'Accepted'}]:
            with patch.object(s, 'run', return_value=json.dumps(receipt)):
                with self.assertRaisesRegex(ValueError, 'not accepted'):
                    s.accepted_submission('archive', 'profile', 'keychain')
        with patch.object(s, 'run', return_value=json.dumps(
                {'id': SUBMISSION, 'status': 'Accepted', 'unneeded': 'discard'})):
            self.assertEqual(s.accepted_submission('a', 'p', 'k'),
                             {'id': SUBMISSION, 'status': 'Accepted'})

    def test_failure_cleans_staging_preserves_input_and_does_not_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); app, keychain = self.fixture(root)
            before = {str(p.relative_to(app)): p.read_bytes() for p in app.rglob('*') if p.is_file()}
            calls = []
            def command(*args):
                calls.append(args)
                if 'find-identity' in args:
                    return '  1) ' + IDENTITY + ' "Synthetic Developer ID"'
                if args[:4] == ('git', '-C', s.packages.REPO, 'rev-parse'):
                    return REV
                if 'notarytool' in args:
                    return json.dumps({'id': SUBMISSION, 'status': 'Invalid'})
                return ''
            with patch.object(s, 'run', side_effect=command):
                with self.assertRaisesRegex(ValueError, 'not accepted'):
                    self.invoke(app, root / 'out', keychain)
            self.assertFalse((root / 'out').exists())
            self.assertEqual(list(root.glob('pear-sign-*')), [])
            self.assertFalse(any('stapler' in args for args in calls))
            self.assertEqual(before, {str(p.relative_to(app)): p.read_bytes() for p in app.rglob('*') if p.is_file()})


    def test_success_requires_both_tickets_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); app, keychain = self.fixture(root)
            before = {str(p.relative_to(app)): p.read_bytes() for p in app.rglob('*') if p.is_file()}
            submitted = []
            def command(*args):
                if 'find-identity' in args:
                    return '  1) ' + IDENTITY + ' "Synthetic Developer ID"'
                if args[:4] == ('git', '-C', s.packages.REPO, 'rev-parse'):
                    return REV
                if 'notarytool' in args:
                    submitted.append(Path(args[3]).name)
                    return json.dumps({'id': SUBMISSION, 'status': 'Accepted'})
                if str(s.packages.REPO / 'preview/package.py') in [str(a) for a in args]:
                    destination = Path(args[args.index('--output') + 1])
                    destination.mkdir()
                    (destination / 'package-manifest.json').write_text('{}')
                return ''
            with patch.object(s, 'run', side_effect=command):
                self.invoke(app, root / 'out', keychain)
            self.assertEqual(submitted, ['app.zip', 'cli.zip'])
            receipt = json.loads((root / 'out/notarization.json').read_text())
            self.assertFalse(receipt['public_release'])
            self.assertEqual(set(receipt['submissions']), {'app', 'cli'})
            self.assertEqual(list(root.glob('pear-sign-*')), [])
            self.assertEqual(before, {str(p.relative_to(app)): p.read_bytes() for p in app.rglob('*') if p.is_file()})

    def test_policy_failure_after_acceptance_does_not_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); app, keychain = self.fixture(root)
            def command(*args):
                if 'find-identity' in args:
                    return '  1) ' + IDENTITY + ' "Synthetic Developer ID"'
                if args[:4] == ('git', '-C', s.packages.REPO, 'rev-parse'):
                    return REV
                if 'notarytool' in args:
                    return json.dumps({'id': SUBMISSION, 'status': 'Accepted'})
                if str(s.packages.REPO / 'preview/package.py') in [str(a) for a in args]:
                    raise RuntimeError('distribution policy rejected')
                return ''
            with patch.object(s, 'run', side_effect=command):
                with self.assertRaisesRegex(RuntimeError, 'policy rejected'):
                    self.invoke(app, root / 'out', keychain)
            self.assertFalse((root / 'out').exists())
            self.assertEqual(list(root.glob('pear-sign-*')), [])


if __name__ == '__main__':
    unittest.main()
