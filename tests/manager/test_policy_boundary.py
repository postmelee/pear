"""Actual CLI policy-location refusals, with owned immutable fixture controls."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import unittest

from case_adapter import Cases, CORPUS, BINARY, REPO
from state_support import inventory


class PolicyBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        case = {**CORPUS['cases'][0], 'id': 'policy-boundary',
                'schema_version': 2, 'embedded_policy': True}
        cls.cases = Cases([case], only=[case['id']])
        cls.item = cls.cases.entries[case['id']]
        cls.embedded = cls.item['root'] / 'policies/caller.json'
        assert cls.embedded.read_bytes() == cls.item['policy'].read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.cases.close()

    def setUp(self):
        self.state, self.work = self.cases.state()

    def invoke(self, command, policy=None, bundle=None, **options):
        args = [str(BINARY), command]
        if command in ('inspect', 'evaluate', 'activate'):
            args += ['--bundle-root', str(bundle or self.item['root']),
                     '--entry', 'records/request.json', '--context', 'fixture']
        if command == 'evaluate':
            args += ['--purpose', 'fixture_launch']
        if command not in ('inspect', 'evaluate'):
            args += ['--state-root', str(self.state)]
        args += ['--policy', str(policy or self.embedded)]
        for key, value in options.items():
            args += ['--' + key.replace('_', '-'), str(value)]
        process = subprocess.run(args, capture_output=True, timeout=15)
        self.assertEqual(process.stderr, b'')
        self.assertLess(len(process.stdout), 8192)
        self.assertNotIn(str(self.cases.root).encode(), process.stdout)
        result = json.loads(process.stdout)
        self.cases.results.append({'id': self.id().split('.')[-1], 'command': command,
                                   'returncode': process.returncode, 'result': result})
        return process.returncode, result

    def test_nested_and_case_alias_policy_refuse(self):
        alias = self.item['root'].with_name(self.item['root'].name.upper()) / 'policies/caller.json'
        # This owned HFS+ fixture must actually provide the tested case alias.
        self.assertTrue(alias.samefile(self.embedded))
        for path in (self.embedded, alias):
            for command in ('inspect', 'evaluate'):
                with self.subTest(command=command, case_alias=path == alias):
                    code, result = self.invoke(command, path)
                    self.assertEqual(code, 1)
                    self.assertEqual(result['outcome_codes'], ['policy_inside_bundle'])
            if path == self.embedded:
                oracle = subprocess.run([str(REPO / '.build/task9/venv/bin/python'), '-B',
                                         str(REPO / 'tests/contracts/validate_v2.py'),
                                         '--bundle-root', str(self.item['root']), '--entry', 'records/request.json',
                                         '--context', 'fixture', '--purpose', 'fixture_launch',
                                         '--policy', str(path)], capture_output=True, timeout=15)
                self.assertEqual(oracle.returncode, 1)
                self.assertEqual(json.loads(oracle.stdout)['outcome_codes'], ['policy_inside_bundle'])

    def test_activation_refusal_preserves_empty_and_existing_selection(self):
        code, result = self.invoke('activate')
        self.assertEqual((code, result['outcome_codes']), (1, ['policy_inside_bundle']))
        self.assertEqual(list(self.state.iterdir()), [])
        self.assertEqual(self.cases.activate('policy-boundary', self.state, prepare=False).returncode, 0)
        before = inventory(self.state)
        code, result = self.invoke('activate')
        self.assertEqual((code, result['outcome_codes']), (1, ['policy_inside_bundle']))
        self.assertEqual(inventory(self.state), before)

    def test_prepare_and_both_recovery_paths_preserve_state(self):
        self.assertEqual(self.cases.activate('policy-boundary', self.state, prepare=False).returncode, 0)
        before = inventory(self.state)
        for command, options in [('prepare', {'context_id': 'default'}),
                                 ('recover', {'new_context': 'fresh'})]:
            code, result = self.invoke(command, profile='records/profile.json', **options)
            self.assertEqual((code, result['reason']), (3, 'policy_inside_bundle'))
            self.assertEqual(inventory(self.state), before)
        self.assertEqual(self.cases.activate('policy-boundary', self.state).returncode, 0)
        before = inventory(self.state)
        code, result = self.invoke('recover', profile='records/profile.json', context_id='default')
        self.assertEqual((code, result['reason']), (3, 'policy_inside_bundle'))
        self.assertEqual(inventory(self.state), before)

    def test_launch_refuses_before_handshake_spawn_or_journal_mutation(self):
        self.assertEqual(self.cases.activate('policy-boundary', self.state).returncode, 0)
        before = inventory(self.state)
        client, server = socket.socketpair()
        try:
            process = subprocess.run([str(BINARY), 'launch', '--state-root', str(self.state),
                                      '--request', 'records/request.json', '--policy', str(self.embedded),
                                      '--context-id', 'default', '--observer-fd', str(client.fileno())],
                                     pass_fds=(client.fileno(),), capture_output=True, timeout=15)
            result = json.loads(process.stdout)
            self.assertEqual(process.returncode, 1)
            self.assertEqual(result['classification'], 'invalid_contract')
            self.assertFalse(result['spawned']); self.assertFalse(result['reaped'])
            self.assertEqual(inventory(self.state), before)
            server.setblocking(False)
            with self.assertRaises(BlockingIOError):
                server.recv(1)
            self.cases.results.append({'id': self.id().split('.')[-1], 'command': 'launch',
                                       'result': result, 'no_handshake': True, 'state_unchanged': True})
        finally:
            client.close(); server.close()

    def test_independent_identical_external_copy_remains_executable(self):
        # An independently selected copy remains valid even with identical bytes.
        parent = self.cases.root / 'media-policy-boundary-external'; parent.mkdir()
        copy = parent / 'caller.json'; copy.write_bytes(self.embedded.read_bytes())
        self.assertEqual(hashlib.sha256(copy.read_bytes()).digest(),
                         hashlib.sha256(self.embedded.read_bytes()).digest())
        original = self.item['policy']; self.item['policy'] = copy
        try:
            value = self.cases.execute('policy-boundary')
            self.assertEqual(value['result']['classification'], 'success', value)
            self.assertTrue(value['result']['reaped']); self.assertTrue(value['identities_gone'])
            self.assertTrue(value['sentinel_survived']); self.assertIsNone(value['peer_error'])
        finally:
            self.item['policy'] = original

    def test_external_symlink_and_hardlink_aliases_refuse(self):
        owned = self.cases.root / ('aliases-' + self.state.name); owned.mkdir()
        bundle = owned / 'bundle'; shutil.copytree(self.item['root'], bundle)
        sibling = owned / 'bundle-policy'; sibling.mkdir()
        outside = sibling / 'caller.json'; outside.write_bytes(self.embedded.read_bytes())
        code, result = self.invoke('evaluate', outside, bundle=bundle)
        self.assertEqual(code, 0); self.assertTrue(result['eligible'])
        link = owned / 'symlink.json'; link.symlink_to(bundle / 'policies/caller.json')
        parent_link = owned / 'parent-link'; parent_link.symlink_to(bundle / 'policies', target_is_directory=True)
        hardlink = owned / 'hardlink.json'; os.link(bundle / 'policies/caller.json', hardlink)
        for path in (link, parent_link / 'caller.json', hardlink):
            code, result = self.invoke('evaluate', path, bundle=bundle)
            self.assertEqual(code, 1)
            self.assertFalse(result['record_valid']); self.assertFalse(result['eligible'])
