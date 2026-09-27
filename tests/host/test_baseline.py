"""Exercise real owned child processes, packet failures and baseline meaning."""

import errno
import json
from pathlib import Path
import platform
import signal
import subprocess
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / ".build/host-probe"
FIXTURE = BUILD / "test-fixtures/runner-fixture"
DRIVER = BUILD / "test-fixtures/runner-driver"
BASELINE = BUILD / "pear-baseline-probe"
CHILD = BUILD / "pear-probe-child"


@unittest.skipUnless(platform.system() == "Darwin", "Requires the macOS SDK")
class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        common = ["xcrun", "clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                  "-arch", "arm64", "-I", str(ROOT / "host/probe")]
        runner_object = FIXTURE.parent / "child-runner-for-tests.o"
        builds = [
            [*common, "-Dkill=pear_fixture_kill", "-c",
             str(ROOT / "host/probe/child_runner.c"), "-o", str(runner_object)],
            [*common, str(ROOT / "tests/host/runner_fixture.c"), "-o", str(FIXTURE)],
            [*common, str(ROOT / "tests/host/runner_driver.c"),
             str(runner_object),
             str(ROOT / "host/probe/baseline_evaluate.c"), "-o", str(DRIVER)],
        ]
        for command in builds:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            if result.returncode:
                raise RuntimeError(f"Fixture compilation failed:\n{result.stderr}")

    def run_fixture(self, mode, *, timeout=1500, side_path="", repeats=1, path=FIXTURE):
        command = [str(DRIVER), str(path), mode, str(timeout), str(side_path), str(repeats)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        report = json.loads(result.stdout)
        self.assertEqual(report["not_reaped"], 1 if mode == "denied-cleanup" else 0, report)
        self.assertEqual(report["remaining_children"], 0, report)
        self.assertGreaterEqual(report["fd_before"], 0)
        self.assertEqual(report["fd_before"], report["fd_after"], report)
        self.assertEqual(report["repeats"], repeats)
        return report

    def assert_owned_cleanup(self, report):
        self.assertTrue(report["child_reaped"], report)
        self.assertLess(report["elapsed_ms"], 3000, report)

    def test_success_requires_exact_packet_and_zero_exit(self):
        report = self.run_fixture("success")
        self.assertEqual(report["outcome"], "exited")
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["stdout_bytes"], 160)
        self.assertEqual(report["stderr_bytes"], 0)
        self.assertTrue(report["packet_valid"])
        self.assertEqual(report["assessment"], "passed")
        self.assert_owned_cleanup(report)

    def test_nonzero_exit_cannot_pass_with_valid_packet(self):
        report = self.run_fixture("nonzero")
        self.assertEqual(report["outcome"], "exited")
        self.assertEqual(report["exit_code"], 7)
        self.assertEqual(report["assessment"], "failed")
        self.assert_owned_cleanup(report)

    def test_signal_is_retained_and_child_reaped(self):
        report = self.run_fixture("signal")
        self.assertEqual(report["outcome"], "signaled")
        self.assertEqual(report["term_signal"], signal.SIGTERM)
        self.assertFalse(report["packet_valid"])
        self.assertEqual(report["assessment"], "failed")
        self.assert_owned_cleanup(report)

    def test_deadline_covers_silent_and_partial_output_children(self):
        for mode in ("timeout", "partial-timeout"):
            with self.subTest(mode=mode):
                report = self.run_fixture(mode, timeout=100)
                self.assertEqual(report["outcome"], "timed_out")
                self.assertGreaterEqual(report["elapsed_ms"], 90)
                self.assertEqual(report["assessment"], "failed")
                self.assert_owned_cleanup(report)

    def test_denied_kill_returns_bounded_failure_without_claiming_reap(self):
        with tempfile.TemporaryDirectory() as directory:
            report = self.run_fixture("denied-cleanup", timeout=100,
                                      side_path=Path(directory) / "owned.pid")
        self.assertEqual(report["outcome"], "io_error", report)
        self.assertEqual(report["error_code"], errno.EPERM)
        self.assertFalse(report["child_reaped"])
        self.assertFalse(report["packet_valid"])
        self.assertEqual(report["assessment"], "failed")
        self.assertLess(report["elapsed_ms"], 1800, report)
        self.assertEqual(report["test_cleanup_reaped"], 1)

    def test_missing_truncated_and_invalid_packets_are_rejected(self):
        modes = ("missing", "truncated", "bad-magic", "bad-version", "wrong-probe",
                 "bad-phase", "unexpected-armed", "bad-status", "bad-domain",
                 "pass-with-error", "not-run-with-value", "failure-without-error",
                 "negative-errno", "after-unavailable", "after-not-run")
        for mode in modes:
            with self.subTest(mode=mode):
                report = self.run_fixture(mode)
                self.assertEqual(report["outcome"], "invalid_output")
                self.assertFalse(report["packet_valid"])
                self.assertEqual(report["assessment"], "failed")
                self.assert_owned_cleanup(report)

    def test_one_extra_byte_and_stdout_flood_exceed_packet_limit(self):
        for mode in ("trailing", "stdout-flood"):
            with self.subTest(mode=mode):
                report = self.run_fixture(mode)
                self.assertEqual(report["outcome"], "output_limit", report)
                self.assertEqual(report["stdout_bytes"], 161)
                self.assertEqual(report["assessment"], "failed")
                self.assert_owned_cleanup(report)

    def test_stderr_is_drained_while_stdout_writer_remains_open(self):
        report = self.run_fixture("stderr-flood")
        self.assertEqual(report["outcome"], "output_limit", report)
        self.assertEqual(report["stderr_bytes"], 1025)
        self.assertLessEqual(report["stdout_bytes"], 160)
        self.assertEqual(report["assessment"], "failed")
        self.assert_owned_cleanup(report)

    def test_unexpected_stderr_is_not_hidden_by_success_packet(self):
        report = self.run_fixture("stderr-first")
        self.assertEqual(report["outcome"], "invalid_output")
        self.assertEqual(report["stderr_bytes"], 1)
        self.assertFalse(report["packet_valid"])
        self.assertEqual(report["assessment"], "failed")
        self.assert_owned_cleanup(report)

    def test_closed_parent_stdin_keeps_child_stdio_and_cleanup_correct(self):
        report = self.run_fixture("closed-stdin")
        self.assertEqual(report["outcome"], "exited", report)
        self.assertEqual(report["assessment"], "passed")
        self.assert_owned_cleanup(report)

    def test_child_does_not_inherit_unrelated_parent_descriptor(self):
        report = self.run_fixture("check-inherited")
        self.assertEqual(report["outcome"], "exited", report)
        self.assertEqual(report["assessment"], "passed")
        self.assert_owned_cleanup(report)

    def test_parent_auto_reap_policies_are_rejected_before_spawn(self):
        for mode in ("parent-ignore-sigchld", "parent-nocldwait"):
            with self.subTest(mode=mode):
                report = self.run_fixture(mode)
                self.assertEqual(report["outcome"], "spawn_error")
                self.assertEqual(report["error_code"], errno.EINVAL)
                self.assertFalse(report["child_reaped"])
                self.assertFalse(report["packet_valid"])
                self.assertEqual(report["assessment"], "failed")

    def test_spawn_failure_preserves_errno_without_claiming_reap(self):
        with tempfile.TemporaryDirectory() as directory:
            report = self.run_fixture("success", path=Path(directory) / "absent-child")
        self.assertEqual(report["outcome"], "spawn_error")
        self.assertEqual(report["error_code"], errno.ENOENT)
        self.assertFalse(report["child_reaped"])
        self.assertFalse(report["packet_valid"])
        self.assertEqual(report["assessment"], "failed")

    def assert_process_not_running(self, pid):
        # A killed orphan can briefly remain a zombie until launchd reaps it.
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            result = subprocess.run(["/bin/ps", "-o", "stat=", "-p", str(pid)],
                                    capture_output=True, text=True, timeout=2)
            self.assertEqual(result.stderr, "", "Could not inspect owned descendant")
            self.assertIn(result.returncode, {0, 1})
            state = result.stdout.strip()
            if not state or state.startswith("Z"):
                return
            time.sleep(0.02)
        self.fail(f"Owned descendant {pid} is still running: {state}")

    def test_descendant_cleanup_after_timeout_and_leader_exit_is_scoped(self):
        sentinel = subprocess.Popen(["/bin/sleep", "20"], start_new_session=True)
        try:
            with tempfile.TemporaryDirectory() as directory:
                for mode in ("grandchild", "leader-exit"):
                    with self.subTest(mode=mode):
                        pid_file = Path(directory) / f"{mode}.pid"
                        report = self.run_fixture(mode, timeout=200, side_path=pid_file)
                        self.assertEqual(report["outcome"], "timed_out")
                        self.assert_owned_cleanup(report)
                        self.assertEqual(report["assessment"], "failed")
                        self.assertTrue(pid_file.is_file())
                        owned_pid = int(pid_file.read_text().strip())
                        self.assertGreater(owned_pid, 1)
                        self.assert_process_not_running(owned_pid)
                        self.assertIsNone(sentinel.poll(), "Unrelated process was terminated")
        finally:
            sentinel.terminate()
            sentinel.wait(timeout=3)

    def test_repeated_success_and_failure_do_not_leak_descriptors_or_children(self):
        for mode in ("success", "bad-magic", "stderr-flood"):
            with self.subTest(mode=mode):
                self.run_fixture(mode, repeats=24)

    def test_armed_packet_without_expected_fault_cannot_pass(self):
        for mode in ("protection-armed-exit", "protection-wrong-signal"):
            with self.subTest(mode=mode):
                report = self.run_fixture(mode)
                self.assertEqual(report["assessment"], "failed")
                self.assert_owned_cleanup(report)

    def test_fault_before_armed_packet_cannot_prove_protection(self):
        report = self.run_fixture("protection-before-armed")
        self.assertEqual(report["outcome"], "signaled")
        self.assertFalse(report["packet_valid"])
        self.assertEqual(report["assessment"], "failed")
        self.assert_owned_cleanup(report)

    def test_armed_packet_requires_all_fault_setup_steps(self):
        report = self.run_fixture("protection-missing-prerequisite")
        self.assertEqual(report["outcome"], "invalid_output")
        self.assertFalse(report["packet_valid"])
        self.assertEqual(report["assessment"], "failed")
        self.assert_owned_cleanup(report)

    def test_cleanup_failure_is_not_hidden_by_successful_operations(self):
        report = self.run_fixture("cleanup-failure")
        self.assertEqual(report["outcome"], "exited")
        self.assertTrue(report["packet_valid"])
        self.assertEqual(report["assessment"], "failed")
        self.assert_owned_cleanup(report)

    def test_rejected_jit_allocation_is_unavailable_and_cannot_pass(self):
        report = self.run_fixture("jit-unavailable")
        self.assertEqual(report["outcome"], "exited")
        self.assertTrue(report["packet_valid"])
        self.assertEqual(report["assessment"], "unavailable")
        self.assert_owned_cleanup(report)

    def test_jit_packet_must_contain_the_expected_return_value(self):
        report = self.run_fixture("jit-wrong-return")
        self.assertEqual(report["outcome"], "exited")
        self.assertTrue(report["packet_valid"])
        self.assertEqual(report["assessment"], "failed")
        self.assert_owned_cleanup(report)


@unittest.skipUnless(platform.system() == "Darwin", "Requires the macOS SDK")
class NativeBaselineTests(unittest.TestCase):
    def test_native_cli_reports_actual_baseline_and_never_game_qualification(self):
        for executable in (BASELINE, CHILD):
            self.assertTrue(executable.is_file(), "Run make -C host/probe first")
            architectures = subprocess.run(["/usr/bin/lipo", "-archs", str(executable)],
                                           capture_output=True, text=True, check=True,
                                           timeout=10).stdout.split()
            self.assertEqual(architectures, ["arm64"])
        result = subprocess.run([str(BASELINE)], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.stderr, "")
        report = json.loads(result.stdout)
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["record_kind"], "baseline_execution")
        self.assertEqual(report["scope"], "owned_test_children")
        self.assertEqual(report["qualification"], {
            "runtime": "not_assessed", "rosetta_free_game": "not_assessed",
            "distribution": "not_assessed",
        })
        self.assertEqual(report["parent_observations"]["scope"], "current_process")
        probes = {probe["name"]: probe for probe in report["probes"]}
        self.assertEqual(set(probes), {"memory", "protection", "low-address", "jit"})
        self.assertEqual(len(report["probes"]), 4)
        self.assertEqual(probes["memory"]["status"], "passed", report)
        for name, probe in probes.items():
            with self.subTest(probe=name):
                # An unavailable allocation or JIT permission remains evidence of a gap;
                # an actual failed probe is a failing test, never an allowed substitute.
                self.assertIn(probe["status"], {"passed", "unavailable"}, probe)
                self.assertTrue(probe["execution"]["child_reaped"], probe)
                self.assertTrue(probe["execution"]["packet_valid"], probe)
                self.assertEqual(probe["execution"]["stderr_bytes"], 0)
                for step in probe["steps"].values():
                    self.assertIn(step["status"], {"passed", "not_run", "unavailable"})
                    if step["status"] == "unavailable":
                        self.assertIsNotNone(step["error"])
                        self.assertNotEqual(step["error"]["code"], 0)
                    else:
                        self.assertIsNone(step["error"])
                if probe["status"] == "unavailable":
                    self.assertIn("unavailable", [s["status"] for s in probe["steps"].values()])
                if name == "protection" and probe["status"] == "passed":
                    self.assertTrue(probe["expected_fault_observed"])
                    self.assertEqual(probe["execution"]["outcome"], "signaled")
                    self.assertIn(probe["execution"]["signal"], {signal.SIGBUS, signal.SIGSEGV})
                elif probe["status"] == "passed":
                    self.assertEqual(probe["execution"]["outcome"], "exited")
                    self.assertEqual(probe["execution"]["exit_code"], 0)
        self.assertEqual(result.returncode, 0, report)
        if probes["jit"]["status"] == "passed":
            self.assertEqual(probes["jit"]["steps"]["execute"]["value"], 42)

    def test_shipped_baseline_cli_has_no_fixture_or_child_path_injection(self):
        for arguments in (("--fixture", "success"), ("--child", "/bin/true"),
                          ("unexpected-operand",)):
            with self.subTest(arguments=arguments):
                result = subprocess.run([str(BASELINE), *arguments], capture_output=True,
                                        text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.strip())


if __name__ == "__main__":
    unittest.main()
