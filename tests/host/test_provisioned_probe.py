"""Check provisioned-probe decisions with synthetic inputs only.

Certificate bytes and identifiers below are fixtures, not credentials. These
tests check consistency and result interpretation, never Apple authorization.
They do not decode real profiles, sign binaries, or execute native commands.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import plistlib
import signal
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "pear_provisioned_probe", ROOT / "host/probe/provisioned_probe.py")
CONTROL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTROL)
FIXTURE_SPEC = importlib.util.spec_from_file_location(
    "pear_synthetic_baseline_fixture", Path(__file__).with_name("test_hardened_baseline.py"))
FIXTURES = importlib.util.module_from_spec(FIXTURE_SPEC)
FIXTURE_SPEC.loader.exec_module(FIXTURES)

NOW = datetime(2026, 9, 28, 12, tzinfo=timezone.utc)
CERTIFICATE = b"synthetic development certificate, never valid for signing"
FINGERPRINT = hashlib.sha1(CERTIFICATE).hexdigest().upper()
TEAM = "TEAMFIXTURE"
PREFIX = "PREFIXFIXTURE"
BUNDLE = "org.example.pear.synthetic-probe"
DEVICE = "SYNTHETIC-DEVICE-ABCD"
IDENTITY = f'  1) {FINGERPRINT} "Apple Development: Synthetic Fixture ({TEAM})"'
METADATA = f"""Executable=/synthetic/private/fixture
CodeDirectory v=20500 size=512 flags=0x10000(runtime) hashes=10+7 location=embedded
Executable Segment flags=0x1
Authority=Apple Development: Synthetic Fixture ({TEAM})
Authority=Apple Worldwide Developer Relations Certification Authority
Authority=Apple Root CA
TeamIdentifier={TEAM}
"""


def profile_fixture():
    return {
        "ExpirationDate": NOW + timedelta(days=30), "Platform": ["OSX"],
        "TeamIdentifier": [TEAM], "ApplicationIdentifierPrefix": [PREFIX],
        "Entitlements": {
            CONTROL.APP_ID: PREFIX + "." + BUNDLE, CONTROL.TEAM_ID: TEAM,
            CONTROL.CROSS_KEYS[0]: True, "com.apple.security.get-task-allow": True,
        },
        "ProvisionedDevices": [DEVICE], "DeveloperCertificates": [CERTIFICATE],
    }


def validate(profile=None, *, identity=IDENTITY, device=DEVICE):
    return CONTROL.validate_profile(profile if profile is not None else profile_fixture(),
                                    identity, device, BUNDLE, now=NOW)


def process_record(mode="4k", *, low_address_pass=False):
    record = FIXTURES.baseline_record()
    record.update(record_kind="process_capabilities", requested_mode=mode)
    page_size = 4096 if mode == "4k" else 16384
    for name in ("memory", "protection", "jit"):
        FIXTURES.probe(record, name)["steps"]["allocate"] = FIXTURES.step(page_size)
    if low_address_pass:
        low = FIXTURES.probe(record, "low-address")
        low.update(status="passed", steps={
            "allocate": FIXTURES.step(0x20000000), "write_read": FIXTURES.step(42),
            "release": FIXTURES.step(0),
        })
    geometry = {
        "name": "geometry", "status": "passed", "execution": FIXTURES.execution(),
        "expected_fault_observed": False,
        "steps": {"user_page_size": FIXTURES.step(page_size),
                  "vm_page_size": FIXTURES.step(page_size),
                  "kernel_page_size": FIXTURES.step(16384)},
    }
    record["probes"].append(geometry)
    if mode == "4k":
        trials = {
            "subpage": (("allocate", "initial_sentinels", "protect_middle", "restore_middle",
                         "verify_neighbors", "release"), (12288, 7, 0, 84, 3, 0)),
            "recommit": (("allocate", "initial_sentinels", "replace_middle", "verify_neighbors",
                          "recommit_zero_and_write", "release"), (12288, 7, 0, 3, 42, 0)),
        }
        for name, (names, values) in trials.items():
            for fault in (False, True):
                steps = {key: FIXTURES.step(value) for key, value in zip(names, values)}
                if fault:
                    for key in names[3:]:
                        steps[key] = FIXTURES.step(status="not_run")
                record["probes"].append({
                    "name": name + ("-fault" if fault else ""), "status": "passed",
                    "execution": FIXTURES.execution(protection=fault),
                    "expected_fault_observed": fault, "steps": steps,
                })
    for probe in record["probes"]:
        probe["execution"].update(page_attribute_called=mode == "4k", page_attribute_error=0)
    return record


class PureCase(unittest.TestCase):
    def setUp(self):
        command = patch.object(CONTROL.BASELINE, "_command",
                               side_effect=AssertionError("Native commands are forbidden in pure tests"))
        command.start()
        self.addCleanup(command.stop)


class ProfileValidationTests(PureCase):
    def test_matching_profile_returns_only_needed_claims_and_public_checks(self):
        result = validate(device=DEVICE.lower())
        self.assertEqual(result["identity"], FINGERPRINT)
        self.assertEqual(result["claims"], {
            CONTROL.APP_ID: PREFIX + "." + BUNDLE, CONTROL.TEAM_ID: TEAM,
            CONTROL.CROSS_KEYS[0]: True, CONTROL.BASELINE.ALLOW_JIT: True,
        })
        self.assertTrue(result["checks"])
        self.assertTrue(all(value is True for value in result["checks"].values()))
        self.assertNotIn(TEAM, json.dumps(result["checks"]))
        profile = profile_fixture()
        profile["ExpirationDate"] = profile["ExpirationDate"].replace(tzinfo=None)
        self.assertEqual(validate(profile)["claims"], result["claims"])

    def test_expired_missing_expiration_and_wrong_platform_are_rejected(self):
        for field, value in (("ExpirationDate", NOW), ("ExpirationDate", NOW - timedelta(seconds=1)),
                             ("ExpirationDate", "2026-10-28"), ("Platform", ["iOS"]),
                             ("Platform", "OSX")):
            profile = profile_fixture()
            profile[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(CONTROL.ControlError):
                validate(profile)

    def test_explicit_application_and_team_binding_are_required(self):
        mutations = (
            lambda p: p["Entitlements"].update({CONTROL.APP_ID: PREFIX + ".*"}),
            lambda p: p["Entitlements"].update({CONTROL.APP_ID: PREFIX + ".org.example.other"}),
            lambda p: p["Entitlements"].update({CONTROL.TEAM_ID: "OTHERTEAM"}),
            lambda p: p.update(ApplicationIdentifierPrefix=["OTHERPREFIX"]),
            lambda p: p.update(ApplicationIdentifierPrefix=[PREFIX, PREFIX]),
            lambda p: p.update(TeamIdentifier=[TEAM, "OTHERTEAM"]),
        )
        for index, mutate in enumerate(mutations):
            profile = profile_fixture()
            mutate(profile)
            with self.subTest(case=index), self.assertRaises(CONTROL.ControlError):
                validate(profile)

    def test_cross_architecture_requires_one_boolean_grant(self):
        for claims in ({}, {CONTROL.CROSS_KEYS[0]: False}, {CONTROL.CROSS_KEYS[0]: 1},
                       {key: True for key in CONTROL.CROSS_KEYS}):
            profile = profile_fixture()
            del profile["Entitlements"][CONTROL.CROSS_KEYS[0]]
            profile["Entitlements"].update(claims)
            with self.subTest(claims=claims), self.assertRaises(CONTROL.ControlError):
                validate(profile)
        profile = profile_fixture()
        del profile["Entitlements"][CONTROL.CROSS_KEYS[0]]
        profile["Entitlements"][CONTROL.CROSS_KEYS[1]] = True
        self.assertEqual(validate(profile)["granted_cross_architecture_key"], CONTROL.CROSS_KEYS[1])

    def test_device_and_available_certificate_must_match(self):
        for device in ("OTHER-DEVICE", "", None):
            with self.subTest(device=device), self.assertRaises(CONTROL.ControlError):
                validate(device=device)
        for identities in ("", IDENTITY.replace(FINGERPRINT, "A" * 40),
                           IDENTITY.replace("Apple Development:", "Developer ID Application:"),
                           IDENTITY + " (CSSMERR_TP_CERT_EXPIRED)"):
            with self.subTest(identities=identities), self.assertRaises(CONTROL.ControlError):
                validate(identity=identities)
        profile = profile_fixture()
        second = b"second synthetic development certificate"
        second_hash = hashlib.sha1(second).hexdigest().upper()
        profile["DeveloperCertificates"].append(second)
        identities = IDENTITY + f'\n  2) {second_hash} "Apple Development: Second ({TEAM})"'
        with self.assertRaises(CONTROL.ControlError):
            validate(profile, identity=identities)


class SignatureValidationTests(PureCase):
    def test_exact_authorized_claims_and_code_directory_flags_are_accepted(self):
        claims = validate()["claims"]
        result = CONTROL.check_signature(METADATA, plistlib.dumps(claims), claims)
        self.assertEqual(result["flags"], 0x10000)
        self.assertTrue(result["profile_claims_match"])
        self.assertNotIn(TEAM, json.dumps(result))

    def test_claim_differences_and_integer_boolean_substitution_are_rejected(self):
        claims = validate()["claims"]
        for key, value in ((CONTROL.APP_ID, PREFIX + ".org.example.other"),
                           (CONTROL.TEAM_ID, "OTHERTEAM"),
                           (CONTROL.CROSS_KEYS[0], 1), (CONTROL.BASELINE.ALLOW_JIT, 1),
                           ("com.apple.security.cs.allow-unsigned-executable-memory", True)):
            actual = {**claims, key: value}
            with self.subTest(key=key), self.assertRaises(CONTROL.ControlError):
                CONTROL.check_signature(METADATA, plistlib.dumps(actual), claims)
        with self.assertRaises(CONTROL.ControlError):
            CONTROL.check_signature(METADATA, b"not a plist", claims)

    def test_metadata_cannot_substitute_segment_flags_or_wrong_identity_category(self):
        claims = validate()["claims"]
        mutations = (
            METADATA.replace("flags=0x10000(runtime)", "flags=0x0(runtime)"),
            METADATA.replace("flags=0x10000(runtime)", "flags=0x10002(runtime,adhoc)"),
            METADATA.replace("flags=0x10000(runtime)", "flags=0x0(none)").replace(
                "Segment flags=0x1", "Segment flags=0x10000(runtime)"),
            METADATA.replace("Authority=Apple Development:", "Authority=Developer ID Application:"),
            METADATA.replace("TeamIdentifier=" + TEAM, "TeamIdentifier=OTHERTEAM"),
            METADATA + "CodeDirectory v=20500 flags=0x10000(runtime)\n",
        )
        for index, metadata in enumerate(mutations):
            with self.subTest(case=index), self.assertRaises(CONTROL.ControlError):
                CONTROL.check_signature(metadata, plistlib.dumps(claims), claims)


class ProcessAssessmentTests(PureCase):
    def assert_rejected(self, record, *, mode="4k", layout=False):
        result = CONTROL.assess_result(record, mode, layout)
        self.assertEqual(result["status"], "failed", result)
        self.assertTrue(result["reason"])

    def test_complete_standard_and_layout_records_are_accepted(self):
        for mode in ("default", "4k"):
            for layout in (False, True):
                with self.subTest(mode=mode, layout=layout):
                    record = process_record(mode, low_address_pass=layout)
                    result = CONTROL.assess_result(record, mode, layout)
                    self.assertEqual(result["status"], "passed", result)

    def test_page_attribute_is_required_for_every_spawn(self):
        for name in ("memory", "geometry", "recommit-fault"):
            for key, value in (("page_attribute_called", False), ("page_attribute_called", 1),
                               ("page_attribute_error", 1), ("page_attribute_error", False)):
                record = process_record()
                FIXTURES.probe(record, name)["execution"][key] = value
                with self.subTest(name=name, key=key, value=value):
                    self.assert_rejected(record)
        record = process_record("default")
        FIXTURES.probe(record, "geometry")["execution"]["page_attribute_called"] = True
        self.assert_rejected(record, mode="default")

    def test_page_geometry_needs_both_user_observations_and_valid_kernel_result(self):
        for name, value in (("user_page_size", 16384), ("vm_page_size", 16384),
                            ("kernel_page_size", 0), ("kernel_page_size", True)):
            record = process_record()
            FIXTURES.probe(record, "geometry")["steps"][name]["value"] = value
            with self.subTest(name=name, value=value):
                self.assert_rejected(record)

    def test_subpage_and_recommit_claims_require_observed_semantics(self):
        mutations = (("subpage", "allocate", "value", 16384),
                     ("subpage", "initial_sentinels", "value", 3),
                     ("subpage", "protect_middle", "status", "failed"),
                     ("subpage", "restore_middle", "value", 42),
                     ("subpage", "verify_neighbors", "value", 1),
                     ("recommit", "replace_middle", "status", "unavailable"),
                     ("recommit", "verify_neighbors", "value", 1),
                     ("recommit", "recommit_zero_and_write", "value", 41),
                     ("recommit", "release", "status", "failed"))
        for name, step, key, value in mutations:
            record = process_record()
            FIXTURES.probe(record, name)["steps"][step][key] = value
            with self.subTest(name=name, step=step, key=key):
                self.assert_rejected(record)

    def test_faults_need_armed_setup_and_actual_protection_signal(self):
        for name in ("subpage-fault", "recommit-fault"):
            for field, value in (("signal", int(signal.SIGTERM)), ("signal", None),
                                 ("outcome", "exited"), ("exit_code", 0)):
                record = process_record()
                FIXTURES.probe(record, name)["execution"][field] = value
                with self.subTest(name=name, field=field):
                    self.assert_rejected(record)
            record = process_record()
            FIXTURES.probe(record, name)["expected_fault_observed"] = False
            self.assert_rejected(record)
            record = process_record()
            FIXTURES.probe(record, name)["steps"]["initial_sentinels"]["value"] = 0
            self.assert_rejected(record)
            record = process_record()
            FIXTURES.probe(record, name)["steps"]["release"] = FIXTURES.step(0)
            self.assert_rejected(record)

    def test_valid_steps_cannot_hide_incomplete_or_failed_child_execution(self):
        for name in ("geometry", "subpage", "recommit-fault"):
            for key, value in (("child_reaped", False), ("packet_valid", False),
                               ("stderr_bytes", 1), ("stdout_bytes", 159),
                               ("error_code", 1), ("elapsed_ms", -1)):
                record = process_record()
                FIXTURES.probe(record, name)["execution"][key] = value
                with self.subTest(name=name, key=key):
                    self.assert_rejected(record)

    def test_layout_requires_low_address_success_and_cannot_hide_jit_failure(self):
        self.assert_rejected(process_record(), layout=True)
        record = process_record(low_address_pass=True)
        FIXTURES.probe(record, "low-address")["steps"]["allocate"]["value"] = 0x20004000
        self.assert_rejected(record, layout=True)
        record = process_record(low_address_pass=True)
        FIXTURES.probe(record, "jit")["steps"]["execute"]["value"] = 41
        self.assert_rejected(record, layout=True)

    def test_record_mode_probe_set_and_native_parent_must_be_consistent(self):
        mutations = (
            lambda r: r.update(schema_version=True),
            lambda r: r.update(requested_mode="default"),
            lambda r: r["probes"].pop(),
            lambda r: r["probes"].append(deepcopy(r["probes"][0])),
            lambda r: r["parent_observations"]["process"]["translated"].update(value=True),
            lambda r: r["qualification"].update(runtime="qualified"),
        )
        for index, mutate in enumerate(mutations):
            record = process_record()
            mutate(record)
            with self.subTest(case=index):
                self.assert_rejected(record)

    def test_sanitizer_drops_identifiers_paths_and_free_form_child_details(self):
        record = process_record()
        private = "PRIVATE-SYNTHETIC-IDENTIFIER-/Users/example/profile.provisionprofile"
        record.update(identity=private, profile_path=private, bundle_id=private)
        record["parent_observations"]["signature"].update(team=private, certificate=private)
        trial = FIXTURES.probe(record, "recommit")
        trial.update(path=private)
        trial["execution"].update(stderr=private, command=[private])
        trial["steps"]["recommit_zero_and_write"]["error"] = {
            "domain": "internal", "code": 14, "details": private,
        }
        trial["steps"]["release"]["value"] = private
        clean = CONTROL.sanitized_result(record)
        self.assertNotIn(private, json.dumps(clean))
        self.assertEqual(len(clean["probes"]), 9)
        self.assertEqual(clean["requested_mode"], "4k")
        cleaned_trial = FIXTURES.probe(clean, "recommit")
        self.assertEqual(cleaned_trial["steps"]["recommit_zero_and_write"]["error"],
                         {"domain": "internal", "code": 14})
        self.assertIsNone(cleaned_trial["steps"]["release"]["value"])
        self.assertEqual(FIXTURES.probe(clean, "geometry")["steps"]["user_page_size"]["value"], 4096)


if __name__ == "__main__":
    unittest.main()
