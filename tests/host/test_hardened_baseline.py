"""Test control decisions with synthetic records, never host qualification claims.

These tests do not access a keychain, sign binaries, or execute native probes.
Actual signing and execution evidence belongs to the separate host trial.
"""

from copy import deepcopy
import errno
import importlib.util
import json
from pathlib import Path
import plistlib
import signal
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "pear_hardened_baseline", ROOT / "host/probe/hardened_baseline.py")
CONTROL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTROL)

FINGERPRINT_A = "A" * 40
FINGERPRINT_B = "B" * 40
IDENTITY_A = f'  1) {FINGERPRINT_A} "Developer ID Application: Fixture A (TEAMFIXTURE)"'
IDENTITY_B = f'  2) {FINGERPRINT_B} "Developer ID Application: Fixture B (TEAMSECOND)"'
METADATA = """Executable=/synthetic/fixture
Identifier=org.pear.fixture
Format=Mach-O thin (arm64)
CodeDirectory v=20500 size=512 flags=0x10000(runtime) hashes=10+7 location=embedded
Executable Segment flags=0x1
Authority=Developer ID Application: Fixture A (TEAMFIXTURE)
Authority=Developer ID Certification Authority
Authority=Apple Root CA
TeamIdentifier=TEAMFIXTURE
Runtime Version=26.5.0
"""


def entitlement_bytes(positive):
    return plistlib.dumps({"com.apple.security.cs.allow-jit": True} if positive else {})


def step(value=None, *, status="passed", error=None):
    return {"status": status, "value": value, "error": error}


def execution(*, protection=False):
    return {
        "outcome": "signaled" if protection else "exited",
        "exit_code": None if protection else 0,
        "signal": int(signal.SIGBUS) if protection else None,
        "error_code": 0, "elapsed_ms": 10, "stdout_bytes": 160,
        "stderr_bytes": 0, "packet_valid": True, "child_reaped": True,
    }


def baseline_record(*, positive=True):
    """Build complete synthetic input, including deliberately unqualified state."""
    not_run = {"status": "not_run", "value": None, "error": None}
    jit = {
        "allocate": step(16384), "write": step(8), "publish": step(0),
        "icache_sync": step(8), "execute": step(42), "release": step(0),
    }
    if not positive:
        jit = {name: deepcopy(not_run) for name in jit}
        jit["allocate"] = step(0, status="unavailable",
                               error={"domain": "errno", "code": errno.EPERM})
    unqualified = {name: "not_assessed" for name in
                   ("runtime", "rosetta_free_game", "distribution")}
    observed = lambda value: {"status": "observed", "value": value, "error": None}
    return {
        "schema_version": 1, "record_kind": "baseline_execution",
        "scope": "owned_test_children", "timeout_ms": 3000,
        "parent_observations": {
            "schema_version": 1, "probe_version": "0.1.0", "scope": "current_process",
            "process": {"architecture": observed("arm64"), "translated": observed(False)},
            "host": {"os_version": observed("26.5.2"), "os_build": observed("25F84"),
                     "page_size_bytes": observed(16384)},
            "runtime_symbols": {},
            "signature": {"category": observed("signed"), "validation": "not_assessed",
                          "authorization": "not_assessed"},
            "capabilities": {name: "not_run" for name in
                             ("x18", "page_4k", "memory_order", "jit")},
            "qualification": deepcopy(unqualified),
        },
        "probes": [
            {"name": "memory", "status": "passed", "execution": execution(),
             "expected_fault_observed": False,
             "steps": {"allocate": step(16384), "write_read": step(42),
                       "protect_read": step(0), "restore_write": step(0),
                       "rewrite_read": step(84), "release": step(0)}},
            {"name": "protection", "status": "passed", "execution": execution(protection=True),
             "expected_fault_observed": True,
             "steps": {"allocate": step(16384), "write_read": step(42),
                       "protect_read": step(0), "unexpected_write": deepcopy(not_run),
                       "unused": deepcopy(not_run), "release": deepcopy(not_run)}},
            {"name": "low-address", "status": "unavailable", "execution": execution(),
             "expected_fault_observed": False,
             "steps": {"allocate": step(0, status="unavailable",
                                        error={"domain": "mach", "code": 3}),
                       "write_read": deepcopy(not_run), "release": deepcopy(not_run)}},
            {"name": "jit", "status": "passed" if positive else "unavailable",
             "execution": execution(), "expected_fault_observed": False, "steps": jit},
        ],
        "qualification": unqualified,
    }


def probe(record, name):
    return next(item for item in record["probes"] if item["name"] == name)


class IdentitySelectionTests(unittest.TestCase):
    def test_one_valid_developer_id_is_selected(self):
        selected = CONTROL.select_identity(IDENTITY_A + "\n 1 valid identities found\n")
        self.assertEqual(selected, FINGERPRINT_A)

    def test_missing_ambiguous_and_wrong_category_identity_are_rejected(self):
        wrong = IDENTITY_A.replace("Developer ID Application", "Apple Development")
        installer = IDENTITY_A.replace("Developer ID Application", "Developer ID Installer")
        for output in (" 0 valid identities found\n", IDENTITY_A + "\n" + IDENTITY_B,
                       wrong, installer):
            with self.subTest(output=output):
                with self.assertRaises(CONTROL.ControlError):
                    CONTROL.select_identity(output)

    def test_override_must_match_an_actual_eligible_identity(self):
        multiple = IDENTITY_A + "\n" + IDENTITY_B
        self.assertEqual(CONTROL.select_identity(multiple, FINGERPRINT_B.lower()),
                         FINGERPRINT_B)
        wrong_category = IDENTITY_A.replace("Developer ID Application", "Apple Development")
        for output, override in ((IDENTITY_A, FINGERPRINT_B), (wrong_category, FINGERPRINT_A),
                                 (IDENTITY_A, "Developer ID Application: Fixture A"),
                                 ("", FINGERPRINT_A)):
            with self.subTest(output=output, override=override):
                with self.assertRaises(CONTROL.ControlError):
                    CONTROL.select_identity(output, override)


class SignaturePolicyTests(unittest.TestCase):
    def test_only_the_intended_entitlement_diff_is_accepted(self):
        for positive in (False, True):
            with self.subTest(positive=positive):
                result = CONTROL.check_signature(METADATA, entitlement_bytes(positive), positive)
                self.assertIsInstance(result, dict)

    def test_runtime_flag_and_certificate_category_are_required(self):
        cases = (
            METADATA.replace("flags=0x10000(runtime)", "flags=0x0(none)"),
            METADATA.replace("flags=0x10000(runtime)", "flags=0x0(runtime)"),
            METADATA.replace("flags=0x10000(runtime)", "flags=0x10002(adhoc,runtime)")
                    + "Signature=adhoc\n",
            METADATA.replace("Developer ID Application:", "Apple Development:"),
            METADATA.replace("TeamIdentifier=TEAMFIXTURE", "TeamIdentifier=not set"),
        )
        for metadata in cases:
            with self.subTest(metadata=metadata):
                with self.assertRaises(CONTROL.ControlError):
                    CONTROL.check_signature(metadata, entitlement_bytes(True), True)

    def test_executable_segment_flags_do_not_replace_code_directory_flags(self):
        signature = CONTROL.check_signature(METADATA, entitlement_bytes(True), True)
        self.assertEqual(signature["flags"], 0x10000)
        misleading_segment = METADATA.replace(
            "flags=0x10000(runtime)", "flags=0x0(none)").replace(
                "Executable Segment flags=0x1", "Executable Segment flags=0x10000(runtime)")
        with self.assertRaises(CONTROL.ControlError):
            CONTROL.check_signature(misleading_segment, entitlement_bytes(True), True)

    def test_missing_false_and_non_boolean_jit_entitlements_are_rejected(self):
        for value in (None, False, 1, "true"):
            contents = {} if value is None else {"com.apple.security.cs.allow-jit": value}
            with self.subTest(value=value):
                with self.assertRaises(CONTROL.ControlError):
                    CONTROL.check_signature(METADATA, plistlib.dumps(contents), True)

    def test_extra_entitlements_and_entitled_negative_control_are_rejected(self):
        extras = ("com.apple.security.cs.allow-unsigned-executable-memory",
                  "com.apple.security.cs.disable-executable-page-protection",
                  "com.apple.developer.cross-architecture-support",
                  "com.apple.developer.cross-architecture-support-unmanaged",
                  "com.apple.security.cs.jit-write-allowlist",
                  "fixture.unexpected.entitlement")
        for name in extras:
            contents = {"com.apple.security.cs.allow-jit": True, name: True}
            with self.subTest(name=name):
                with self.assertRaises(CONTROL.ControlError):
                    CONTROL.check_signature(METADATA, plistlib.dumps(contents), True)
        with self.assertRaises(CONTROL.ControlError):
            CONTROL.check_signature(METADATA, entitlement_bytes(True), False)

    def test_malformed_or_non_dictionary_entitlements_are_rejected(self):
        for contents in (b"not a plist", plistlib.dumps(["allow-jit"])):
            with self.subTest(contents=contents):
                with self.assertRaises(CONTROL.ControlError):
                    CONTROL.check_signature(METADATA, contents, True)


class ResultAssessmentTests(unittest.TestCase):
    def assert_rejected(self, record, *, positive=True):
        assessment = CONTROL.assess_result(record, positive)
        self.assertEqual(assessment["status"], "failed", assessment)
        self.assertTrue(assessment["reason"], assessment)

    def test_complete_synthetic_positive_and_expected_negative_are_accepted(self):
        for positive in (False, True):
            with self.subTest(positive=positive):
                assessment = CONTROL.assess_result(baseline_record(positive=positive), positive)
                self.assertEqual(assessment["status"], "passed", assessment)

    def test_claimed_success_cannot_hide_wrong_constant_or_failed_step(self):
        for step_name, field, value in (("execute", "value", 41),
                                       ("write", "value", 4),
                                       ("icache_sync", "value", 0),
                                       ("release", "status", "failed")):
            record = baseline_record()
            probe(record, "jit")["steps"][step_name][field] = value
            with self.subTest(step_name=step_name, field=field, value=value):
                self.assert_rejected(record)

    def test_execution_failure_cannot_pass_with_valid_jit_steps(self):
        mutations = (("outcome", "signaled"), ("signal", int(signal.SIGTERM)), ("exit_code", 7),
                     ("packet_valid", False), ("child_reaped", False), ("error_code", errno.EIO),
                     ("stderr_bytes", 1), ("stdout_bytes", 159))
        for field, value in mutations:
            record = baseline_record()
            probe(record, "jit")["execution"][field] = value
            with self.subTest(field=field, value=value):
                self.assert_rejected(record)

    def test_protection_requires_the_expected_fault_and_owned_cleanup(self):
        for field, value in (("signal", int(signal.SIGTERM)), ("child_reaped", False),
                             ("packet_valid", False), ("exit_code", 0)):
            record = baseline_record()
            probe(record, "protection")["execution"][field] = value
            with self.subTest(field=field, value=value):
                self.assert_rejected(record)
        record = baseline_record()
        probe(record, "protection")["expected_fault_observed"] = False
        self.assert_rejected(record)

    def test_expected_negative_requires_mmap_permission_denial(self):
        for code in (errno.EPERM, errno.EACCES):
            record = baseline_record(positive=False)
            probe(record, "jit")["steps"]["allocate"]["error"]["code"] = code
            assessment = CONTROL.assess_result(record, False)
            self.assertEqual(assessment["status"], "passed", assessment)
        for status, domain, code in (("failed", "errno", errno.EPERM),
                                     ("unavailable", "errno", errno.ENOMEM),
                                     ("unavailable", "mach", errno.EPERM),
                                     ("unavailable", "internal", 3)):
            record = baseline_record(positive=False)
            probe(record, "jit")["steps"]["allocate"] = step(
                0, status=status, error={"domain": domain, "code": code})
            with self.subTest(status=status, domain=domain, code=code):
                self.assert_rejected(record, positive=False)

    def test_negative_control_cannot_pass_after_executing_or_crashing(self):
        record = baseline_record(positive=False)
        probe(record, "jit")["steps"]["execute"] = step(42)
        self.assert_rejected(record, positive=False)
        for field, value in (("outcome", "signaled"), ("exit_code", 1),
                             ("packet_valid", False), ("child_reaped", False)):
            record = baseline_record(positive=False)
            probe(record, "jit")["execution"][field] = value
            with self.subTest(field=field, value=value):
                self.assert_rejected(record, positive=False)

    def test_einval_rejection_requires_a_successful_matched_positive(self):
        record = baseline_record(positive=False)
        jit = probe(record, "jit")
        jit["status"] = "failed"
        jit["steps"]["allocate"] = step(0, status="failed",
                                          error={"domain": "errno", "code": errno.EINVAL})
        self.assert_rejected(record, positive=False)
        for paired in (False, None, 1, "true"):
            with self.subTest(paired=paired):
                result = CONTROL.assess_result(record, False, paired_positive=paired)
                self.assertEqual(result["status"], "failed")
        result = CONTROL.assess_result(record, False, paired_positive=True)
        self.assertEqual(result, {"status": "passed", "reason": "expected_paired_jit_rejection_observed"})
        # Pair interpretation must not rewrite the original failure observation.
        sanitized = CONTROL.sanitized_result(record)
        self.assertEqual(probe(sanitized, "jit")["status"], "failed")
        self.assertEqual(probe(sanitized, "jit")["steps"]["allocate"]["error"]["code"], errno.EINVAL)

    def test_paired_einval_cannot_hide_other_failures_or_later_steps(self):
        template = baseline_record(positive=False)
        jit = probe(template, "jit")
        jit["status"] = "failed"
        jit["steps"]["allocate"] = step(0, status="failed",
                                          error={"domain": "errno", "code": errno.EINVAL})
        for mutate in (
                lambda record: probe(record, "memory").update(status="failed"),
                lambda record: probe(record, "protection")["execution"].update(signal=int(signal.SIGTERM)),
                lambda record: probe(record, "jit")["execution"].update(exit_code=1),
                lambda record: probe(record, "jit")["steps"].update(execute=step(42)),
                lambda record: probe(record, "jit")["steps"]["allocate"].update(value=4096),
                lambda record: probe(record, "jit")["steps"]["allocate"].update(status="unavailable"),
                lambda record: probe(record, "jit")["steps"]["allocate"]["error"].update(code=errno.ENOMEM)):
            record = deepcopy(template)
            mutate(record)
            self.assertEqual(CONTROL.assess_result(record, False, paired_positive=True)["status"], "failed")

    def test_pair_provenance_requires_completed_positive_and_identical_inputs(self):
        hashes = {"pear-baseline-probe": "a" * 64, "pear-probe-child": "b" * 64}
        negative = {"name": "negative", "input_copy_sha256": deepcopy(hashes)}
        positive = {"name": "positive", "status": "passed", "input_copy_sha256": deepcopy(hashes)}
        report = {"input_binary_sha256": deepcopy(hashes), "controls": [positive, negative]}
        self.assertTrue(CONTROL.paired_positive_matches(report, negative))
        for mutate in (
                lambda data: data["controls"][0].update(status="not_run"),
                lambda data: data["controls"][0].update(status="failed"),
                lambda data: data["controls"].pop(0),
                lambda data: data["controls"][0]["input_copy_sha256"].update({"pear-probe-child": "c" * 64}),
                lambda data: data["input_binary_sha256"].update({"pear-baseline-probe": "c" * 64})):
            changed = deepcopy(report)
            mutate(changed)
            self.assertFalse(CONTROL.paired_positive_matches(changed, negative))
        changed_negative = deepcopy(negative)
        changed_negative["input_copy_sha256"]["pear-probe-child"] = "c" * 64
        self.assertFalse(CONTROL.paired_positive_matches(report, changed_negative))

    def test_low_address_failure_and_other_baseline_failures_are_not_hidden(self):
        for name in ("memory", "protection", "low-address"):
            record = baseline_record()
            probe(record, name)["status"] = "failed"
            with self.subTest(name=name):
                self.assert_rejected(record)
        record = baseline_record()
        probe(record, "memory")["steps"]["rewrite_read"]["value"] = 42
        self.assert_rejected(record)

    def test_native_parent_evidence_is_required(self):
        for name, value in (("architecture", "x86_64"), ("translated", True)):
            record = baseline_record()
            record["parent_observations"]["process"][name]["value"] = value
            with self.subTest(name=name, value=value):
                self.assert_rejected(record)
        record = baseline_record()
        record["parent_observations"]["process"]["translated"] = {
            "status": "unavailable", "value": None, "error": {"domain": "errno", "code": 1}}
        self.assert_rejected(record)

    def test_malformed_duplicate_and_unqualified_schema_is_fail_closed(self):
        for record in (None, [], "passed", {}, {"probes": []}):
            with self.subTest(record=record):
                self.assert_rejected(record)
        for mutate in (lambda record: record.update(schema_version=2),
                       lambda record: record["probes"].append(deepcopy(record["probes"][0])),
                       lambda record: record["probes"].pop(),
                       lambda record: record["probes"][0].update(name=[]),
                       lambda record: record["probes"][0].update(name={}),
                       lambda record: record["qualification"].update(runtime="qualified")):
            record = baseline_record()
            mutate(record)
            self.assert_rejected(record)

    def test_report_sanitizer_drops_arbitrary_private_strings(self):
        record = baseline_record()
        private = "PRIVATE-FIXTURE-IDENTITY-AND-PATH"
        record["identity"] = private
        record["parent_observations"]["private_path"] = private
        jit = probe(record, "jit")
        jit["unknown"] = private
        jit["status"] = private
        jit["execution"].update(outcome=private, signal=private, stderr=private)
        jit["steps"]["execute"] = step(private, status=private,
                                         error={"domain": private, "code": private})
        sanitized = CONTROL.sanitized_result(record)
        self.assertNotIn(private, json.dumps(sanitized))
        clean_jit = probe(sanitized, "jit")
        self.assertEqual(clean_jit["status"], "invalid")
        self.assertEqual(clean_jit["execution"]["outcome"], "invalid")
        self.assertEqual(clean_jit["steps"]["execute"],
                         {"status": "invalid", "value": None, "error": None})
        self.assertEqual(probe(sanitized, "memory")["steps"]["write_read"]["value"], 42)
        for invalid_name in ([], {}):
            malformed = {"probes": [{"name": invalid_name}]}
            self.assertEqual(CONTROL.sanitized_result(malformed), {"probes": []})


if __name__ == "__main__":
    unittest.main()
