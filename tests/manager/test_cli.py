"""Execute the official CLI examples against owned fixtures, including recovery."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import signal
from string import Template
import subprocess
import time
import unittest

from state_support import StateTestBase, inventory
from case_adapter import BINARY, BUILD, REPO, experiment_cases
from synthetic_peer import Peer

GUIDE = REPO / 'docs/development/runtime-supervisor.md'


def block(marker, language):
    pattern = r'<!-- ' + re.escape(marker) + r' -->\s*```' + language + r'\n(.*?)\n```'
    matches = re.findall(pattern, GUIDE.read_text(), re.S)
    if len(matches) != 1: raise AssertionError('missing or ambiguous executable example: ' + marker)
    return matches[0]


class CliTests(StateTestBase):
    @classmethod
    def setUpClass(cls):
        namespace = {}
        exec(compile(block('pear-fixture-setup', 'python'), str(GUIDE), 'exec'), namespace)
        cls.cases = namespace['media']
        cls.runtime_before = inventory(cls.cases.mount)
        cls.image_before = hashlib.sha256(cls.cases.image.read_bytes()).hexdigest()
        cls.executed = set()

    @classmethod
    def tearDownClass(cls):
        required = set(re.findall(r'<!-- pear-cli: ([a-z-]+) -->', GUIDE.read_text()))
        cls.cases.results.append({'id': 'documentation_examples', 'guide_sha256': hashlib.sha256(GUIDE.read_bytes()).hexdigest(),
                                  'executed': sorted(cls.executed), 'required': sorted(required)})
        super().tearDownClass()
        if required != cls.executed: raise AssertionError('unexecuted documentation command example')

    def arguments(self, example, letter='a', id=None, fd=None, new='fresh'):
        item = self.cases.entries[letter]
        values = {'PEAR_MANAGER': str(BINARY), 'PEAR_BUNDLE': str(item['root']),
                  'PEAR_POLICY': str(item['policy']), 'PEAR_STATE': str(self.state),
                  'PEAR_CONTEXT': id or letter, 'PEAR_NEW_CONTEXT': new,
                  'PEAR_OBSERVER_FD': str(fd)}
        # Parse quoting before substitution so paths remain individual argv values.
        args = [Template(arg).substitute(values) for arg in shlex.split(block('pear-cli: ' + example, 'sh'))]
        self.assertEqual(args[0], str(BINARY))
        self.executed.add(example)
        return args

    def command(self, example, letter='a', id=None, new='fresh'):
        p = subprocess.run(self.arguments(example, letter, id, new=new), capture_output=True, timeout=10)
        self.assertEqual(p.stderr, b''); self.assertLess(len(p.stdout), 8192)
        for private in (str(self.state).encode(), b'PRIVATE_FIXTURE_MARKER_93c8'):
            self.assertNotIn(private, p.stdout)
        result = json.loads(p.stdout)
        self.cases.results.append({'id': self.id().split('.')[-1], 'example': example,
                                   'returncode': p.returncode, 'result': result})
        return p.returncode, result

    def prepared(self, letter='a', id=None):
        for example in ('inspect', 'evaluate', 'activate', 'prepare'):
            code, result = self.command(example, letter, id)
            self.assertEqual(code, 0, result)
            if example in ('inspect', 'evaluate'): self.assertTrue(result['eligible'])
        return self.state / 'contexts' / (id or letter)

    def launch_example(self, letter='a', id=None, mode='normal'):
        peer = Peer(mode); peer.work = self.state / 'contexts' / (id or letter)
        peer.start(); self.peers.append(peer)
        fd = peer.client.fileno()
        p = subprocess.Popen(self.arguments('launch', letter, id, fd), stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, pass_fds=(fd,), start_new_session=True,
                             env={**os.environ, 'PEAR_SECRET_SENTINEL': 'PRIVATE_FIXTURE_MARKER_93c8'})
        peer.client.close(); self.live.append(p)
        return p, peer

    def test_documented_two_profile_relaunch_and_recovery(self):
        roots = {letter: self.prepared(letter) for letter in ('a', 'b')}
        for round in range(2):
            for letter, marker, flag in [('a', 'alpha', True), ('b', 'beta', False)]:
                other = 'b' if letter == 'a' else 'a'; before = inventory(roots[other])
                p, peer = self.launch_example(letter); self.finish(p, peer, letter)
                self.preserved(roots[other], before)
                record = json.loads((roots[letter] / f'state/prefix-{letter}/last-run.json').read_bytes())
                self.assertEqual((record['marker'], record['setting'], record['previous_save']), (marker, flag, bool(round)))
                self.assertEqual((roots[letter] / f'state/saves-{letter}/{marker}/save.dat').read_bytes(), marker.encode())
                self.assertEqual(self.command('status', letter)[1]['reason'], 'context_clean')
                self.cases.results.append({'id': 'documented_profile_observation', 'profile': letter,
                                          'round': round, 'marker': marker, 'setting': flag, 'previous_save': bool(round)})
        before = {letter: inventory(root) for letter, root in roots.items()}
        self.assertEqual(self.command('recover-existing', 'a')[1]['reason'], 'compatible_context_selected')
        self.assertEqual(self.command('activate', 'a')[0], 0)
        self.assertEqual(self.command('recover-new', 'a')[0], 0)
        for letter in roots: self.preserved(roots[letter], before[letter])
        self.assertEqual(inventory(self.state / 'contexts/fresh/state/saves-a'), {})
        p, peer = self.launch_example('a', id='fresh'); self.finish(p, peer, 'a', id='fresh')
        self.assertEqual(self.command('recover-new', 'a')[1]['reason'], 'recovery_requires_new_context')

    def test_manual_python_descriptor_handoff_runs(self):
        root = self.prepared()
        namespace = {'state': self.state, 'manager': str(BINARY), 'policy_a': str(self.cases.entries['a']['policy'])}
        with contextlib.redirect_stdout(io.StringIO()) as output:
            exec(compile(block('pear-fixture-launch', 'python'), str(GUIDE), 'exec'), namespace)
        result = namespace['result']
        self.assertNotIn(str(self.state), output.getvalue())
        self.assertTrue(experiment_cases.disappeared(BUILD, root / 'state/prefix-a/identity.json'))
        self.assertEqual((root / 'state/saves-a/alpha/save.dat').read_bytes(), b'alpha')
        self.cases.results.append({'id': 'manual_python_descriptor_handoff', 'result': result})

    def test_readiness_refusal_leaves_incomplete_state_and_fresh_recovery_preserves_it(self):
        root = self.prepared(); p, peer = self.launch_example(mode='silent')
        result = self.finish(p, peer, success=False)
        self.assertEqual(result['classification'], 'observer_not_ready'); self.assertFalse(result['spawned'])
        self.assertEqual(self.command('status')[1]['reason'], 'context_incomplete')
        before = inventory(root)
        p, peer = self.launch_example(); result = self.finish(p, peer, success=False)
        self.assertEqual(result['classification'], 'context_incomplete'); self.assertFalse(result['spawned'])
        self.assertEqual(self.command('recover-existing')[1]['reason'], 'context_incomplete')
        self.assertEqual(self.command('recover-new')[0], 0)
        self.preserved(root, before)
        p, peer = self.launch_example(id='fresh'); self.finish(p, peer, id='fresh')

    def test_both_documented_signals_cancel_only_the_owned_run(self):
        for signum, id in [(signal.SIGINT, 'interrupt'), (signal.SIGTERM, 'terminate')]:
            with self.subTest(signal=signum):
                root = self.prepared(id=id); p, peer = self.launch_example(id=id)
                trace = root / 'state/prefix-a/identity.json'
                deadline = time.monotonic() + 3
                while not trace.exists() and p.poll() is None and time.monotonic() < deadline: time.sleep(.002)
                self.assertTrue(trace.exists(), 'child never published an owned trace')
                p.send_signal(signum)
                result = self.finish(p, peer, id=id, success=False)
                self.assertEqual(p.returncode, 4, result)
                self.assertEqual(result['classification'], 'cancelled')
                self.assertTrue(result['reaped']); self.assertEqual(result['cleanup'], 'passed')
                self.assertTrue(result['observation_complete'])
                self.assertTrue(experiment_cases.disappeared(BUILD, trace))
                self.assertIsNone(self.sentinel.poll())

    def test_unknown_and_duplicate_options_have_bounded_private_diagnostics(self):
        for args in [[], ['--help'], ['status', '--private', str(self.state)],
                     ['status', '--state-root', str(self.state), '--state-root', str(self.state)],
                     ['launch', '--private', 'PRIVATE_FIXTURE_MARKER_93c8']]:
            with self.subTest(args=args[:1]):
                p = subprocess.run([str(BINARY), *args], capture_output=True, timeout=5)
                self.assertIn(p.returncode, (1, 2)); self.assertEqual(p.stderr, b'')
                self.assertLess(len(p.stdout), 8192); self.assertIsInstance(json.loads(p.stdout), dict)
                self.assertNotIn(str(self.state).encode(), p.stdout)
                self.assertNotIn(b'PRIVATE_FIXTURE_MARKER_93c8', p.stdout)
                self.cases.results.append({'id': 'cli_misuse', 'returncode': p.returncode, 'result': json.loads(p.stdout)})


if __name__ == '__main__':
    unittest.main()
