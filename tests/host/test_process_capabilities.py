"""Test process-page protocol and evidence rules using redistributable fixtures.

The separately compiled runner resolves only a fake setter. Neither these tests
nor their simulated passing packets establish an authorized host capability.
"""

import errno
import json
from pathlib import Path
import platform
import signal
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / ".build/host-probe/test-fixtures"
DRIVER = BUILD / "process-runner-driver"
FIXTURE = BUILD / "process-runner-fixture"
GEOMETRY, SUBPAGE, SUBPAGE_FAULT, RECOMMIT, RECOMMIT_FAULT = range(5, 10)
DEFAULT, PAGES_4K = 0, 1


@unittest.skipUnless(platform.system() == "Darwin", "Requires the macOS SDK")
class ProcessCapabilitiesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        BUILD.mkdir(parents=True, exist_ok=True)
        common = ["xcrun", "clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                  "-arch", "arm64", "-I", str(ROOT / "host/probe")]
        runner_object = BUILD / "process-runner-mocked-setter.o"
        builds = [
            [*common, "-Ddlsym=pear_fixture_dlsym", "-c",
             str(ROOT / "host/probe/child_runner.c"), "-o", str(runner_object)],
            [*common, str(ROOT / "tests/host/process_runner_fixture.c"),
             "-o", str(FIXTURE)],
            [*common, str(ROOT / "tests/host/process_runner_driver.c"),
             str(runner_object), str(ROOT / "host/probe/process_evaluate.c"),
             str(ROOT / "host/probe/baseline_evaluate.c"), "-o", str(DRIVER)],
        ]
        for command in builds:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            if result.returncode:
                raise RuntimeError(f"Fixture compilation failed:\n{result.stderr}")

    def driver(self, *arguments):
        result = subprocess.run([str(DRIVER), *map(str, arguments)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def spawn(self, api, probe=GEOMETRY, variant="valid"):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "child-started"
            report = self.driver("spawn", FIXTURE, api, probe, variant, marker)
            report["child_started"] = marker.exists()
        self.assertTrue(report["no_children"], report)
        self.assertGreaterEqual(report["fd_before"], 0)
        self.assertEqual(report["fd_before"], report["fd_after"], report)
        return report

    def assessment(self, probe, mutation="valid", mode=PAGES_4K):
        return self.driver("assess", probe, mode, mutation)["assessment"]

    def test_missing_attribute_never_spawns_or_falls_back(self):
        report = self.spawn("missing")
        self.assertEqual(report["returned"], 0)
        self.assertEqual(report["outcome"], "spawn_error")
        self.assertEqual(report["error_code"], errno.ENOSYS)
        self.assertEqual(report["page_attribute_error"], errno.ENOSYS)
        self.assertFalse(report["page_attribute_called"])
        self.assertEqual(report["lookup_calls"], 1)
        self.assertEqual(report["setter_calls"], 0)
        self.assertFalse(report["child_started"])
        self.assertFalse(report["child_reaped"])
        self.assertEqual(report["assessment"], "failed")

    def test_attribute_rejection_retains_error_without_spawning(self):
        report = self.spawn("reject")
        self.assertEqual(report["returned"], 0)
        self.assertEqual(report["outcome"], "spawn_error")
        self.assertEqual(report["error_code"], errno.EPERM)
        self.assertEqual(report["page_attribute_error"], errno.EPERM)
        self.assertTrue(report["page_attribute_called"])
        self.assertEqual(report["setter_calls"], 1)
        self.assertTrue(report["attributes_ready"])
        self.assertFalse(report["child_started"])
        self.assertFalse(report["child_reaped"])
        self.assertEqual(report["assessment"], "failed")

    def test_invalid_mode_is_rejected_before_lookup_or_spawn(self):
        report = self.spawn("invalid")
        self.assertEqual(report["returned"], -1)
        self.assertEqual(report["error_code"], errno.EINVAL)
        self.assertEqual(report["lookup_calls"], 0)
        self.assertEqual(report["setter_calls"], 0)
        self.assertFalse(report["page_attribute_called"])
        self.assertFalse(report["child_started"])

    def test_default_mode_does_not_request_a_page_attribute(self):
        report = self.spawn("default")
        self.assertEqual(report["outcome"], "exited")
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["lookup_calls"], 0)
        self.assertFalse(report["page_attribute_called"])
        self.assertEqual(report["page_attribute_error"], 0)
        self.assertTrue(report["child_started"])
        self.assertTrue(report["child_reaped"])
        self.assertTrue(report["packet_valid"])
        self.assertEqual(report["assessment"], "passed")

    def test_simulated_setter_success_records_attempt_before_spawn(self):
        report = self.spawn("success", variant="geometry4k")
        self.assertEqual(report["outcome"], "exited")
        self.assertTrue(report["attributes_ready"])
        self.assertEqual(report["setter_calls"], 1)
        self.assertTrue(report["page_attribute_called"])
        self.assertEqual(report["page_attribute_error"], 0)
        self.assertTrue(report["child_started"])
        self.assertTrue(report["child_reaped"])
        self.assertEqual(report["assessment"], "passed")

    def test_geometry_packet_rejects_extra_or_skipped_operations(self):
        for variant in ("geometry-extra", "missing-prerequisite", "unexpected-armed",
                        "wrong-identity"):
            with self.subTest(variant=variant):
                report = self.spawn("default", variant=variant)
                self.assertEqual(report["outcome"], "invalid_output")
                self.assertFalse(report["packet_valid"])
                self.assertTrue(report["child_reaped"])
                self.assertEqual(report["assessment"], "failed")

    def test_subpage_and_recommit_packets_accept_all_six_operations(self):
        for probe in (SUBPAGE, RECOMMIT):
            with self.subTest(probe=probe):
                report = self.spawn("success", probe)
                self.assertEqual(report["outcome"], "exited")
                self.assertTrue(report["packet_valid"])
                self.assertTrue(report["child_reaped"])
                self.assertEqual(report["assessment"], "passed")

    def test_default_mode_cannot_qualify_subpage_or_recommit_operations(self):
        for probe in (SUBPAGE, SUBPAGE_FAULT, RECOMMIT, RECOMMIT_FAULT):
            with self.subTest(probe=probe):
                report = self.spawn("default", probe)
                self.assertTrue(report["packet_valid"])
                self.assertTrue(report["child_reaped"])
                self.assertFalse(report["page_attribute_called"])
                self.assertEqual(report["assessment"], "failed")

    def test_early_fault_setup_failures_preserve_diagnostic_packets(self):
        for probe in (SUBPAGE_FAULT, RECOMMIT_FAULT):
            for variant, expected in (("early-unavailable", "unavailable"),
                                      ("early-failure-cleanup", "failed")):
                with self.subTest(probe=probe, variant=variant):
                    report = self.spawn("success", probe, variant)
                    self.assertEqual(report["outcome"], "exited")
                    self.assertTrue(report["packet_valid"])
                    self.assertTrue(report["child_reaped"])
                    self.assertEqual(report["assessment"], expected)

    def test_new_fault_packets_require_exact_armed_setup(self):
        for probe in (SUBPAGE_FAULT, RECOMMIT_FAULT):
            for variant in ("armed-incomplete", "armed-extra", "wrong-identity"):
                with self.subTest(probe=probe, variant=variant):
                    report = self.spawn("default", probe, variant)
                    self.assertEqual(report["outcome"], "signaled")
                    self.assertFalse(report["packet_valid"])
                    self.assertTrue(report["child_reaped"])
                    self.assertEqual(report["assessment"], "failed")

    def test_new_fault_packets_require_actual_expected_signal(self):
        for probe in (SUBPAGE_FAULT, RECOMMIT_FAULT):
            for variant, expected in (("valid", signal.SIGBUS), ("sigsegv", signal.SIGSEGV)):
                with self.subTest(probe=probe, variant=variant):
                    report = self.spawn("success", probe, variant)
                    self.assertEqual(report["outcome"], "signaled")
                    self.assertEqual(report["term_signal"], expected)
                    self.assertTrue(report["packet_valid"])
                    self.assertTrue(report["child_reaped"])
                    self.assertEqual(report["assessment"], "passed")

    def test_armed_packet_with_exit_or_wrong_signal_cannot_pass(self):
        for probe in (SUBPAGE_FAULT, RECOMMIT_FAULT):
            for variant in ("armed-exit", "wrong-signal"):
                with self.subTest(probe=probe, variant=variant):
                    report = self.spawn("default", probe, variant)
                    self.assertTrue(report["packet_valid"])
                    self.assertTrue(report["child_reaped"])
                    self.assertEqual(report["assessment"], "failed")

    def test_geometry_preserves_default_and_4k_semantic_distinction(self):
        for mode in (DEFAULT, PAGES_4K):
            with self.subTest(mode=mode):
                self.assertEqual(self.assessment(GEOMETRY, mode=mode), "passed")
                self.assertEqual(self.assessment(GEOMETRY, "geometry-mismatched-pages", mode),
                                 "failed")
        for mutation in ("value-0", "value-1", "geometry-zero-kernel",
                         "geometry-negative-kernel"):
            with self.subTest(mutation=mutation):
                self.assertEqual(self.assessment(GEOMETRY, mutation), "failed")

    def test_operation_values_include_neighbor_integrity_and_cleanup(self):
        for probe in (SUBPAGE, RECOMMIT):
            self.assertEqual(self.assessment(probe), "passed")
            for index in range(6):
                with self.subTest(probe=probe, index=index):
                    self.assertEqual(self.assessment(probe, f"value-{index}"), "failed")

    def test_fault_setup_values_are_checked_before_interpreting_signal(self):
        for probe in (SUBPAGE_FAULT, RECOMMIT_FAULT):
            self.assertEqual(self.assessment(probe), "passed")
            self.assertEqual(self.assessment(probe, "sigsegv"), "passed")
            for mutation in ("value-0", "value-1", "value-2", "wrong-signal",
                             "armed-exit", "wrong-phase"):
                with self.subTest(probe=probe, mutation=mutation):
                    self.assertEqual(self.assessment(probe, mutation), "failed")

    def test_every_probe_requires_valid_owned_termination_evidence(self):
        for probe in range(GEOMETRY, RECOMMIT_FAULT + 1):
            for mutation in ("not-reaped", "invalid-packet", "timeout", "io-error",
                             "wrong-phase"):
                with self.subTest(probe=probe, mutation=mutation):
                    self.assertEqual(self.assessment(probe, mutation), "failed")
        for probe in (GEOMETRY, SUBPAGE, RECOMMIT):
            with self.subTest(probe=probe):
                self.assertEqual(self.assessment(probe, "nonzero-exit"), "failed")

    def test_attribute_evidence_must_match_requested_mode(self):
        for probe in range(GEOMETRY, RECOMMIT_FAULT + 1):
            for mutation in ("no-attribute", "attribute-error"):
                with self.subTest(probe=probe, mutation=mutation):
                    self.assertEqual(self.assessment(probe, mutation), "failed")
            self.assertEqual(self.assessment(probe, "unexpected-attribute", DEFAULT), "failed")
            self.assertEqual(self.assessment(probe, "attribute-error", DEFAULT), "failed")
            self.assertEqual(self.assessment(probe, mode=99), "failed")

    def test_failed_or_missing_cleanup_cannot_pass(self):
        for probe in (SUBPAGE, RECOMMIT):
            for mutation in ("cleanup-failed", "cleanup-not-run", "allocation-unavailable"):
                with self.subTest(probe=probe, mutation=mutation):
                    self.assertNotEqual(self.assessment(probe, mutation), "passed")


if __name__ == "__main__":
    unittest.main()
