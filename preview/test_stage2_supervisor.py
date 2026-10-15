# Copyright (C) 2026 Pear contributors.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure/synthetic guard checks: no real GUI, Wine, shared lock or user state."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

spec = importlib.util.spec_from_file_location('stage2_supervisor', Path(__file__).parent / 'validation/stage2_supervisor.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def process(birth='birth-a', exe='/owned/wine', ppid=1):
    return {'birth': birth, 'exe': exe, 'ppid': ppid, 'pgid': 10}


class SupervisionTests(unittest.TestCase):
    def test_storage_tolerates_child_removed_after_enumeration(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); keep = root / 'keep'; keep.write_bytes(b'kept')
            vanishing = root / 'update.tmp'; vanishing.write_bytes(b'temporary')
            original = Path.lstat
            def remove_child(path, *args, **kwargs):
                if path == vanishing:
                    path.unlink()
                return original(path, *args, **kwargs)
            with patch.object(Path, 'lstat', remove_child):
                logical, allocated = m.storage(root)
            self.assertEqual(logical, 4)
            self.assertGreaterEqual(allocated, 0)

    def test_storage_tolerates_child_directory_removed_before_scan(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); child = root / 'updater'; child.mkdir()
            (root / 'keep').write_bytes(b'kept')
            original = m.os.scandir
            def remove_directory(path):
                if Path(path) == child:
                    child.rmdir()
                return original(path)
            with patch.object(m.os, 'scandir', remove_directory):
                self.assertEqual(m.storage(root)[0], 4)

    def test_storage_does_not_hide_missing_root_or_access_errors(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            with self.assertRaises(FileNotFoundError): m.storage(root / 'absent')
            original = m.os.scandir
            child = root / 'protected'; child.mkdir()
            def deny(path):
                if Path(path) == child: raise PermissionError('fixture access denied')
                return original(path)
            with patch.object(m.os, 'scandir', deny):
                with self.assertRaises(PermissionError): m.storage(root)

    def test_storage_does_not_follow_symlink_to_external_state(self):
        with tempfile.TemporaryDirectory() as name:
            base = Path(name); root = base / 'output'; root.mkdir()
            external = base / 'private'; external.mkdir()
            (external / 'save').write_bytes(b'private data')
            (root / 'link').symlink_to(external, target_is_directory=True)
            (root / 'keep').write_bytes(b'abc')
            self.assertEqual(m.storage(root)[0], 3)

    def test_reinstall_reuses_candidate_and_preserves_external_state(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); source = root / 'source'; source.mkdir()
            (source / 'binary').write_bytes(b'signed candidate')
            trial = root / 'trial'; m.shutil.copytree(source, trial)
            saved = root / 'private-save'; saved.write_bytes(b'preserve')
            inventory = root / 'inventory.json'; m.write(inventory, m.inventory(source))
            target = root / 'reinstalled'
            g = self.guard(); g.phase = 'trial-verified'; g.quiet = Mock()
            g.r.update(source_app=str(source), trial_app=str(trial),
                       reinstalled_app=str(target), app_inventory=str(inventory))
            g.r['actions']['reinstall-app'] = {'from': ['trial-verified'], 'to': 'reinstalled', 'quiet': True}
            g.dispatch({'action': 'reinstall-app'})
            self.assertFalse(trial.exists())
            self.assertEqual(m.inventory(target), m.inventory(source))
            self.assertEqual(saved.read_bytes(), b'preserve')
            g.quiet.assert_called_once()

    def test_pid_reuse_is_not_old_owned_process(self):
        old = process()
        seen = {(10, *m.identity(old)): old}
        _, live, _ = m.classify({10: process('birth-b', '/other/editor')}, {}, seen, set(), ['/owned'], 50)
        self.assertEqual(live, [])

    def test_preexisting_os_service_with_transient_handle_is_preserved(self):
        service = process(exe='/System/Library/TCC/tccd')
        seen, live, excluded = m.classify({634: service}, {634: service}, {}, {634}, ['/owned'], 50)
        self.assertEqual((seen, live, excluded), ({}, [], [634]))

    def test_reparented_owned_helper_remains_tracked(self):
        child = process()
        seen, live, _ = m.classify({10: child}, {}, {}, {10}, ['/owned'], 50)
        changed = {10: {**child, 'ppid': 1}}
        _, live, _ = m.classify(changed, {}, seen, set(), ['/owned'], 50)
        self.assertEqual(live, [10])

    def test_new_descendant_is_tracked_without_handles(self):
        current = {10: process(ppid=50), 11: process(exe='/usr/bin/curl', ppid=10)}
        _, live, _ = m.classify(current, {}, {}, set(), ['/owned'], 50)
        self.assertEqual(live, [10, 11])

    def test_partial_download_requires_bytes_not_activated_cache(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); stage = root / 'stage'; stage.mkdir()
            p = stage / 'SteamSetup.exe'; p.write_bytes(b'ab')
            self.assertTrue(m.partial_download(root, p.name, 4))
            (root / p.name).write_bytes(b'abcd')
            self.assertFalse(m.partial_download(root, p.name, 4))

    def test_partial_symlink_is_not_evidence(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); (root / 'stage').mkdir(); target = root / 'other'; target.write_bytes(b'ab')
            (root / 'stage/SteamSetup.exe').symlink_to(target)
            self.assertFalse(m.partial_download(root, 'SteamSetup.exe', 4))

    def test_grant_rejects_wrong_digest_reused_output_and_retired_assignment(self):
        with tempfile.TemporaryDirectory() as name:
            ready = Path(name).resolve() / 'ready.json'; m.write(ready, {'operation_id': 'op', 'allowed_phases': ['gui']})
            grant = {'consumer': 47, 'single_use': True, 'operation_id': 'op', 'ready': {'path': str(ready), 'sha256': m.sha(ready)}, 'allowed_phases': ['gui']}
            assignment = {'operation_id': 'op', 'released': False}
            m.check_grant(ready, grant, assignment, False)
            for g, a, exists in [({**grant, 'ready': {'path': str(ready), 'sha256': 'bad'}}, assignment, False), (grant, assignment, True), (grant, {**assignment, 'released': True}, False), ({**grant, 'operation_id': 'other'}, assignment, False)]:
                with self.assertRaises(RuntimeError):
                    m.check_grant(ready, g, a, exists)

    def test_inventory_detects_mutation_and_modes(self):
        with tempfile.TemporaryDirectory() as name:
            p = Path(name) / 'app'; p.mkdir(); f = p / 'cli'; f.write_bytes(b'original')
            before = m.inventory(p); f.write_bytes(b'changed')
            self.assertNotEqual(before, m.inventory(p))
            f.write_bytes(b'original'); f.chmod(0o700)
            self.assertNotEqual(before, m.inventory(p))

    def test_private_state_cannot_be_disposable_target(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve(); out = root / 'run'
            ready = {'output_root': str(out), 'trial_state': str(out / 'trial/state'), 'trial_app': str(out / 'app'), 'reinstalled_app': str(out / 'app2'), 'trial_cache': str(out / 'trial/state/cache'), 'existing_state': str(root / 'real-private')}
            m.check_paths(ready)
            ready['trial_state'] = ready['existing_state']
            with self.assertRaises(RuntimeError): m.check_paths(ready)

    def guard(self):
        g = m.Guard.__new__(m.Guard)
        g.r = {'actions': {'launch': {'from': ['prepared'], 'to': 'running', 'command': 'open'}, 'finish': {'from': ['running'], 'to': 'released', 'quiet': True}}}
        g.phase = 'prepared'; g.failed = None; g.history = []; g.roots = ['/owned']
        g.emit = lambda: None
        return g

    def test_normal_shutdown_refuses_to_interrupt_live_game(self):
        g = self.guard(); g.r['actions']['shutdown-existing'] = {'from': ['prepared'], 'command': 'shutdown', 'cleanup': True}
        g.live = [30]; g.current = {30: process(exe='/owned/Megabonk.exe')}; g.sample = lambda: None
        with patch.object(g, 'command') as command:
            with self.assertRaises(RuntimeError): g.dispatch({'action': 'shutdown-existing'})
            command.assert_not_called()

    def test_successful_release_still_requires_independent_owner_check(self):
        g = self.guard(); g.phase = 'running'; g.live = []; g.handles = set(); g.sample = lambda: None
        with patch.object(m, 'system_snapshot', return_value=({}, set())):
            g.dispatch({'action': 'finish'})
        self.assertEqual(g.phase, 'released')
        self.assertIsNone(g.failed)

    def test_wrong_phase_and_failure_cannot_launch(self):
        g = self.guard()
        with patch.object(g, 'command') as command:
            g.phase = 'wrong'
            with self.assertRaises(RuntimeError): g.dispatch({'action': 'launch'})
            g.phase = 'prepared'; g.failed = 'original failure'
            with self.assertRaises(RuntimeError): g.dispatch({'action': 'launch'})
            command.assert_not_called()

    def test_release_refuses_live_owner_or_handle(self):
        g = self.guard(); g.phase = 'running'; g.live = [42]; g.handles = set()
        g.sample = lambda: None
        with self.assertRaises(RuntimeError): g.dispatch({'action': 'finish'})
        self.assertEqual(g.phase, 'running')
        g.live = []; g.handles = {634}
        with self.assertRaises(RuntimeError): g.dispatch({'action': 'finish'})

    def test_failed_guard_can_normal_cleanup_but_cannot_report_pass(self):
        g = self.guard(); g.failed = 'failed check'; g.r['actions']['cleanup'] = {'from': ['prepared'], 'command': 'shutdown', 'cleanup': True}
        with patch.object(g, 'command') as command:
            g.dispatch({'action': 'cleanup'}); command.assert_called_once_with('shutdown')
        self.assertEqual(g.failed, 'failed check')

    def test_requires_real_observation_before_login_pass(self):
        g = self.guard(); g.r['actions']['confirm-login'] = {'from': ['prepared'], 'to': 'login'}
        with self.assertRaises(RuntimeError): g.dispatch({'action': 'confirm-login'})
        self.assertEqual(g.phase, 'prepared')

    def test_stop_targets_direct_child_and_reaps_it(self):
        p = Mock(); p.poll.return_value = None
        m.stop_direct_child(p)
        p.terminate.assert_called_once(); p.wait.assert_called_once_with(timeout=5)
        p.kill.assert_not_called()

    def test_malformed_process_snapshot_fails_closed(self):
        with self.assertRaises(RuntimeError): m.parse_processes('bad')


if __name__ == '__main__':
    unittest.main()
