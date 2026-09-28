"""Reject misleading signed ABI evidence using synthetic records only."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "pear_profile_fixtures", Path(__file__).with_name("test_provisioned_probe.py"))
FIXTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURE)
CONTROL = FIXTURE.CONTROL


def abi_record(mode="4k"):
    record = FIXTURE.process_record(mode)
    record["record_kind"] = "abi_capabilities"
    record["probes"] = [p for p in record["probes"] if p["name"] == "geometry"]
    for name, names in CONTROL.ABI_STEP_NAMES.items():
        values = CONTROL.ABI_VALUES[name]
        record["probes"].append({
            "name": name, "status": "passed", "expected_fault_observed": False,
            "execution": {**FIXTURE.FIXTURES.execution(),
                          "page_attribute_called": mode == "4k", "page_attribute_error": 0},
            "steps": {key: FIXTURE.FIXTURES.step(0 if value is None else value)
                      for key, value in zip(names, values)},
        })
    return record


class AbiEvidenceTests(unittest.TestCase):
    def rejected(self, record, mode="4k"):
        self.assertEqual(CONTROL.assess_abi_result(record, mode)["status"], "failed")

    def test_known_good_default_and_four_k_records_remain_finite_evidence(self):
        for mode in ("default", "4k"):
            record = abi_record(mode)
            self.assertEqual(CONTROL.assess_abi_result(record, mode)["status"], "passed")
            self.assertEqual(record["qualification"], CONTROL.BASELINE.QUALIFICATION)

    def test_claimed_success_cannot_hide_guest_state_or_restoration_failure(self):
        for name, key in (("x18-roundtrip", "guest_after_getter"),
                          ("x18-callbacks", "outer_guest_restores"),
                          ("x18-callbacks", "injected_error_returns"),
                          ("x18-signals", "resumed_guest_preserved"),
                          ("thread-policy", "restored_threads"),
                          ("thread-litmus", "restored_and_joined_workers")):
            record = abi_record()
            trial = FIXTURE.FIXTURES.probe(record, name)
            trial["steps"][key]["value"] += 1
            with self.subTest(name=name, key=key):
                self.rejected(record)

    def test_handler_entry_must_show_both_actual_modes_and_host_bodies(self):
        for key in ("host_handler_entry", "foreign_handler_entry", "host_handler_body_calls"):
            record = abi_record()
            steps = FIXTURE.FIXTURES.probe(record, "x18-signals")["steps"]
            steps[key]["value"] += 1
            with self.subTest(key=key):
                self.rejected(record)

    def test_successful_policy_calls_do_not_replace_litmus_evidence(self):
        for key, value in (("initialized_workers", 1), ("enabled_trials", 9999),
                           ("enabled_forbidden", 1), ("baseline_forbidden", -1),
                           ("baseline_forbidden", 10001)):
            record = abi_record()
            FIXTURE.FIXTURES.probe(record, "thread-litmus")["steps"][key]["value"] = value
            with self.subTest(key=key, value=value):
                self.rejected(record)
        record = abi_record()
        FIXTURE.FIXTURES.probe(record, "thread-litmus")["steps"]["baseline_forbidden"]["value"] = 17
        self.assertEqual(CONTROL.assess_abi_result(record, "4k")["status"], "passed")

    def test_every_child_needs_actual_completion_reaping_and_page_mode(self):
        for field, value in (("outcome", "signaled"), ("exit_code", 1), ("signal", 10),
                             ("packet_valid", False), ("child_reaped", False),
                             ("stdout_bytes", 159), ("stderr_bytes", 1), ("error_code", 1),
                             ("elapsed_ms", -1), ("page_attribute_called", False),
                             ("page_attribute_error", 1), ("exit_code", False)):
            record = abi_record()
            FIXTURE.FIXTURES.probe(record, "x18-roundtrip")["execution"][field] = value
            with self.subTest(field=field, value=value):
                self.rejected(record)

    def test_missing_duplicate_or_unavailable_trial_cannot_pass(self):
        base = abi_record()
        for name in CONTROL.ABI_STEP_NAMES:
            record = deepcopy(base)
            FIXTURE.FIXTURES.probe(record, name)["status"] = "unavailable"
            with self.subTest(name=name):
                self.rejected(record)
        record = deepcopy(base)
        record["probes"].pop()
        self.rejected(record)
        record = deepcopy(base)
        record["probes"][-1] = deepcopy(record["probes"][0])
        self.rejected(record)

    def test_wrong_suite_architecture_and_qualification_are_rejected(self):
        mutations = (
            lambda r: r.update(record_kind="process_capabilities"),
            lambda r: r.update(requested_mode="default"),
            lambda r: r.update(schema_version=True),
            lambda r: r["qualification"].update(runtime="qualified"),
            lambda r: r["parent_observations"]["process"]["architecture"].update(value="x86_64"),
            lambda r: r["parent_observations"]["process"]["translated"].update(value=True),
        )
        for mutate in mutations:
            record = abi_record()
            mutate(record)
            self.rejected(record)

    def test_private_details_do_not_survive_abi_sanitization(self):
        record = abi_record()
        private = "/Users/synthetic/private-profile-identifier"
        for p in record["probes"]:
            p["identity"] = private
            p["execution"]["stderr"] = private
            for s in p["steps"].values():
                s["details"] = private
        clean = CONTROL.sanitized_result(record)
        self.assertEqual(len(clean["probes"]), 6)
        self.assertNotIn(private, json.dumps(clean))

    def test_suite_selection_is_explicit_and_duplicate_options_fail(self):
        self.assertEqual(CONTROL._parse_arguments(["--profile", "synthetic"])[2], "process")
        self.assertEqual(CONTROL._parse_arguments(["--profile", "synthetic", "--suite", "abi"])[2], "abi")
        for args in (["--profile", "synthetic", "--suite", "unknown"],
                     ["--profile", "synthetic", "--suite", "abi", "--suite", "process"],
                     ["--profile", "synthetic", "--bundle-id", "org.test.a", "--bundle-id", "org.test.b"]):
            with self.subTest(arguments=args), self.assertRaises(CONTROL.ControlError):
                CONTROL._parse_arguments(args)


if __name__ == "__main__":
    unittest.main()
