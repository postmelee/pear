"""Verify diagnostic meaning using injected observations and the native CLI."""

import errno
import json
from pathlib import Path
import platform
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / ".build/host-probe/pear-host-probe"
FIXTURE = ROOT / ".build/host-probe/test-fixtures/diagnostic-fixture"
SYMBOLS = {
    "os_set_custom_x18_abi_enabled",
    "os_custom_x18_abi_enabled",
    "posix_spawnattr_set_4k_page_size_np",
    "thread_set_x86_64_compat",
}


@unittest.skipUnless(platform.system() == "Darwin", "Requires the macOS SDK")
class DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PROBE.is_file():
            raise RuntimeError("Build the diagnostic with make -C host/probe first")
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        command = [
            "xcrun", "clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-arch", "arm64", "-I", str(ROOT / "host/probe"),
            str(ROOT / "tests/host/diagnostic_fixture.c"),
            str(ROOT / "host/probe/observations.c"),
            "-framework", "Security", "-framework", "CoreFoundation",
            "-o", str(FIXTURE),
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise RuntimeError(f"Fixture compilation failed:\n{result.stderr}")

    def run_json(self, command):
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        report = json.loads(result.stdout)
        self.assertIsInstance(report, dict)
        return report, result.stdout

    def fixture(self, name):
        return self.run_json([str(FIXTURE), name])[0]

    def assert_no_qualification(self, report):
        self.assertEqual(report["scope"], "current_process")
        self.assertEqual(report["capabilities"], {
            "x18": "not_run",
            "page_4k": "not_run",
            "memory_order": "not_run",
            "jit": "not_run",
        })
        self.assertEqual(report["qualification"], {
            "runtime": "not_assessed",
            "rosetta_free_game": "not_assessed",
            "distribution": "not_assessed",
        })
        self.assertEqual(report["signature"]["validation"], "not_assessed")
        self.assertEqual(report["signature"]["authorization"], "not_assessed")

    def assert_observed(self, observation, value):
        self.assertEqual(observation["status"], "observed")
        self.assertEqual(observation["value"], value)
        self.assertIsNone(observation["error"])

    def test_denied_translation_query_remains_unavailable(self):
        report = self.fixture("translation-denied")
        observation = report["process"]["translated"]
        self.assertEqual(observation["status"], "unavailable")
        self.assertIsNone(observation["value"])
        self.assertEqual(observation["error"], {"domain": "errno", "code": errno.EPERM})
        self.assert_no_qualification(report)

    def test_missing_translation_query_is_not_native_execution_evidence(self):
        report = self.fixture("translation-missing")
        observation = report["process"]["translated"]
        self.assertEqual(observation["status"], "unavailable")
        self.assertIsNone(observation["value"])
        self.assertEqual(observation["error"], {"domain": "errno", "code": errno.ENOENT})
        self.assert_no_qualification(report)

    def test_unexpected_translation_value_is_not_coerced_to_boolean(self):
        report = self.fixture("translation-unexpected")
        observation = report["process"]["translated"]
        self.assertEqual(observation["status"], "failed")
        self.assertIsNone(observation["value"])
        self.assertEqual(observation["error"], {"domain": "internal", "code": errno.EPROTO})
        self.assert_no_qualification(report)

    def test_translation_values_have_boolean_type_without_qualification(self):
        for name, expected in (("baseline", False), ("translation-observed", True)):
            with self.subTest(fixture=name):
                report = self.fixture(name)
                observation = report["process"]["translated"]
                self.assert_observed(observation, expected)
                self.assertIs(type(observation["value"]), bool)
                self.assert_no_qualification(report)

    def test_absent_symbols_are_observations_not_capability_results(self):
        report = self.fixture("missing-symbols")
        self.assertEqual(set(report["runtime_symbols"]), SYMBOLS)
        for name, observation in report["runtime_symbols"].items():
            with self.subTest(symbol=name):
                self.assert_observed(observation, False)
                self.assertIs(observation["value"], False)
        self.assert_no_qualification(report)

    def test_present_symbols_do_not_prove_authorization(self):
        report = self.fixture("baseline")
        for observation in report["runtime_symbols"].values():
            self.assert_observed(observation, True)
            self.assertIs(observation["value"], True)
        self.assert_no_qualification(report)

    def test_unavailable_signature_preserves_error_without_authorization(self):
        report = self.fixture("unavailable-signature")
        observation = report["signature"]["category"]
        self.assertEqual(observation["status"], "unavailable")
        self.assertIsNone(observation["value"])
        self.assertEqual(observation["error"], {"domain": "osstatus", "code": -12345})
        self.assert_no_qualification(report)

    def test_unsupported_architecture_is_rejected_without_qualification(self):
        report = self.fixture("unsupported-architecture")
        observation = report["process"]["architecture"]
        self.assertEqual(observation["status"], "failed")
        self.assertIsNone(observation["value"])
        self.assertEqual(observation["error"], {"domain": "errno", "code": errno.ENOTSUP})
        self.assert_no_qualification(report)

    def test_intel_architecture_is_not_reported_as_arm64_support(self):
        report = self.fixture("intel-architecture")
        self.assert_observed(report["process"]["architecture"], "x86_64")
        self.assert_no_qualification(report)

    def test_adversarial_text_round_trips_without_json_injection(self):
        report, output = self.run_json([str(FIXTURE), "adversarial-text"])
        expected = "".join(chr(value) for value in range(1, 32)) + (
            ' quote:" slash:/ backslash:\\ fake:"forged":true UTF-8:\u2603'
        )
        self.assert_observed(report["host"]["os_version"], expected)
        self.assertNotIn("forged", report)
        self.assertNotIn("forged", report["host"])
        # json.loads is strict about literal control bytes inside JSON strings.
        self.assertIn("\\u0001", output)
        self.assert_no_qualification(report)

    def test_oversized_text_fails_without_truncating_evidence(self):
        report = self.fixture("oversized-text")
        observation = report["host"]["os_version"]
        self.assertEqual(observation["status"], "failed")
        self.assertIsNone(observation["value"])
        self.assertEqual(observation["error"], {"domain": "internal", "code": errno.EOVERFLOW})
        self.assert_no_qualification(report)

    def test_invalid_utf8_is_rejected_before_json_output(self):
        report = self.fixture("invalid-utf8")
        observation = report["host"]["os_version"]
        self.assertEqual(observation["status"], "failed")
        self.assertIsNone(observation["value"])
        self.assertEqual(observation["error"], {"domain": "internal", "code": errno.EILSEQ})
        self.assert_no_qualification(report)

    def test_shipped_cli_rejects_invalid_options_and_fixture_injection(self):
        for arguments in (("--unknown-option",), ("unexpected-operand",),
                          ("--fixture", "translation-denied")):
            with self.subTest(arguments=arguments):
                result = subprocess.run([str(PROBE), *arguments], capture_output=True,
                                        text=True, timeout=15)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.strip())

    def test_native_binary_reports_only_its_current_process(self):
        architectures = subprocess.run(["/usr/bin/lipo", "-archs", str(PROBE)],
                                       capture_output=True, text=True, check=True,
                                       timeout=15).stdout.split()
        self.assertEqual(architectures, ["arm64"])
        report, _ = self.run_json([str(PROBE)])
        self.assertEqual(report["schema_version"], 1)
        self.assertIsInstance(report["probe_version"], str)
        self.assertTrue(report["probe_version"])
        self.assertEqual(set(report["process"]), {"architecture", "translated"})
        self.assert_observed(report["process"]["architecture"], "arm64")
        translation = report["process"]["translated"]
        self.assertIn(translation["status"], {"observed", "unavailable", "failed"})
        if translation["status"] == "observed":
            self.assertIs(type(translation["value"]), bool)
            self.assertIsNone(translation["error"])
        else:
            self.assertIsNone(translation["value"])
            self.assertIsInstance(translation["error"]["code"], int)
        self.assertEqual(set(report["runtime_symbols"]), SYMBOLS)
        self.assert_no_qualification(report)


if __name__ == "__main__":
    unittest.main()
