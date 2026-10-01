"""Synthetic record rejection tests; these never qualify or execute a runtime."""
import copy
import hashlib
import os
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/wine"))
from common import Error
import evidence
import verify


LOCK_DIGEST = "1" * 64
CONFIG_DIGEST = "2" * 64
NATIVE_STDOUT = '{"fixture":"pear-toolchain-native-v1","value":42}\n'
MACHINES = {"aarch64": 0xAA64, "arm64ec": 0xA641, "x86_64": 0x8664, "i686": 0x14C}
SDK_FRAMEWORKS = (
    "AppKit", "Carbon", "Foundation", "IOKit", "Metal", "OpenGL", "QuartzCore",
    "Security", "CoreText", "ApplicationServices", "CoreFoundation", "CoreServices",
    "DiskArbitration", "SystemConfiguration",
)


def synthetic_report():
    """An in-memory fixture, not a captured command log or executable evidence."""
    checks, commands = [], []

    def check(ident, **details):
        checks.append({"id": ident, "status": "passed", "details": details})

    def command(ident, stdout=""):
        commands.append({"id": ident, "exit_code": 0, "timed_out": False,
                         "output_limit": False, "stdout": stdout, "stderr": ""})

    check("native", architectures=[0x0100000C])
    check("frameworks", executed=False, dependencies=[
        "/System/Library/Frameworks/" + name + ".framework/Versions/A/" + name
        for name in SDK_FRAMEWORKS])
    check("bison", version="bison (GNU Bison) 3.8.2")
    metadata = ("File: fixture.exe\nCHPEMetadataPointer: 0x140003000\n"
                "File: pear-toolchain.dll\nCHPEMetadataPointer: 0x180003000\n")
    check("arm64ec.support", output=metadata)
    command("arm64ec.support.inspect", metadata)
    for variant in ("arm64", "arm64ec-build"):
        check("configure." + variant, wine_runtime_built=False)
        command("configure." + variant)
        command("configure." + variant + ".make-query")
    command("compiler.version", "clang version 23.1.1\n")
    command("native.compile")
    command("native.run", NATIVE_STDOUT)
    command("frameworks.link")
    command("bison.version", "bison (GNU Bison) 3.8.2\n")
    for target, machine in MACHINES.items():
        check(target + ".compile", machine=machine)
        check(target + ".cxx")
        check(target + ".link", pe_machine=0x8664 if target == "arm64ec" else machine,
              executed=False)
        for kind in ("imports", "exports", "resources",
                     "assembly" if target == "i686" else "unwind"):
            check(target + "." + kind)
        for suffix in ("main.obj", "dll.obj", "cpp.obj", "assemble", "resource.compile",
                       "dll.link", "importlib", "exe.link"):
            command(target + "." + suffix)
        command(target + ".unwind.inspect",
                "" if target == "i686" else "RuntimeFunction { UnwindData: 0x1000 }\n")
        command(target + ".imports.inspect",
                "Import {\n  Name: pear-toolchain.dll\n  Symbol: pear_toolchain_add (0)\n}\n")
        command(target + ".exports.inspect",
                "Export {\n  Ordinal: 1\n  Name: pear_toolchain_add\n  RVA: 0x1000\n}\n")
        command(target + ".resources.inspect",
                "Type: RCDATA (10)\nName: (ID 101)\nData (\n  0000: 50454152 2A00 |PEAR*.|\n)\n")
    return {"schema_version": 1, "record_kind": "wine_toolchain_check",
            "lock_sha256": LOCK_DIGEST, "config_sha256": CONFIG_DIGEST,
            "fixture_hashes": {"toolchain_native.c": "3" * 64},
            "sdk": {"version": "26.5", "canonical_name": "macosx26.5", "settings_sha256": "6" * 64,
                    "path": "/Users/private-fixture/PRIVATE-EXPORT-MARKER-SDK"},
            "pe_execution": False, "wine_runtime_execution": False,
            "passed": True, "checks": checks, "commands": commands}


def row(report, category, ident):
    return next(item for item in report[category] if item["id"] == ident)


class ReportAssessmentTests(unittest.TestCase):
    def assess(self, report):
        return verify.assess_report(report, LOCK_DIGEST, CONFIG_DIGEST)

    def rejected(self, report, code=None):
        with self.assertRaises(Error) as caught:
            self.assess(report)
        if code is not None:
            self.assertEqual(caught.exception.code, code)

    def test_complete_synthetic_record_is_consistent_without_execution(self):
        report = synthetic_report()
        original = copy.deepcopy(report)
        checks, commands = self.assess(report)
        self.assertEqual((len(checks), len(commands)), (34, 58))
        self.assertEqual(report, original)
        self.assertFalse(report["pe_execution"])
        self.assertFalse(report["wine_runtime_execution"])

    def test_success_label_is_not_required_or_sufficient_evidence(self):
        report = synthetic_report()
        report["passed"] = False
        self.assess(report)
        report["passed"] = True
        row(report, "commands", "native.run")["exit_code"] = 7
        self.rejected(report, "command_did_not_pass")

    def test_every_required_check_is_required(self):
        original = synthetic_report()
        for missing in original["checks"]:
            with self.subTest(check=missing["id"]):
                report = copy.deepcopy(original)
                report["checks"] = [item for item in report["checks"] if item["id"] != missing["id"]]
                self.rejected(report, "required_checks_incomplete")

    def test_every_required_command_is_required(self):
        original = synthetic_report()
        for missing in original["commands"]:
            with self.subTest(command=missing["id"]):
                report = copy.deepcopy(original)
                report["commands"] = [item for item in report["commands"] if item["id"] != missing["id"]]
                self.rejected(report, "required_commands_incomplete")

    def test_duplicate_check_and_command_ids_rejected(self):
        for category in ("checks", "commands"):
            with self.subTest(category=category):
                report = synthetic_report()
                report[category].append(copy.deepcopy(report[category][0]))
                self.rejected(report, category + "_duplicate")

    def test_unknown_check_rejected(self):
        report = synthetic_report()
        report["checks"].append({"id": "not-reviewed", "status": "passed", "details": {}})
        self.rejected(report, "required_checks_incomplete")

    def test_unexpected_private_command_id_rejected_before_export(self):
        report = synthetic_report()
        extra = copy.deepcopy(report["commands"][0])
        extra["id"] = "/Users/private-fixture/PRIVATE-COMMAND-MARKER"
        report["commands"].append(extra)
        self.rejected(report)

    def test_unavailable_failed_or_malformed_check_cannot_pass(self):
        for changes in ({"status": "unavailable"}, {"status": "failed"},
                        {"status": True}, {"details": []}):
            with self.subTest(changes=changes):
                report = synthetic_report()
                row(report, "checks", "aarch64.cxx").update(changes)
                self.rejected(report, "required_check_failed")

    def test_command_failure_timeout_and_output_limit_rejected(self):
        for changes in ({"exit_code": 9}, {"exit_code": -9}, {"exit_code": False},
                        {"timed_out": True}, {"timed_out": 0},
                        {"output_limit": True}, {"output_limit": 0}):
            with self.subTest(changes=changes):
                report = synthetic_report()
                row(report, "commands", "aarch64.exe.link").update(changes)
                self.rejected(report, "command_did_not_pass")

    def test_command_output_shape_and_bound_rejected(self):
        for value in (None, [], "x" * (4 * 256 * 1024 + 1)):
            with self.subTest(kind=type(value).__name__):
                report = synthetic_report()
                row(report, "commands", "aarch64.exe.link")["stderr"] = value
                self.rejected(report, "command_output_shape")

    def test_wrong_native_result_or_stderr_rejected(self):
        for changes in ({"stdout": NATIVE_STDOUT.replace("42", "41")},
                        {"stdout": NATIVE_STDOUT + "extra\n"}, {"stderr": "unexpected\n"}):
            with self.subTest(changes=changes):
                report = synthetic_report()
                row(report, "commands", "native.run").update(changes)
                self.rejected(report, "native_result_mismatch")

    def test_wrong_native_architecture_rejected(self):
        for architectures in ([0x01000007], [0x0100000C, 0x01000007], [], None):
            with self.subTest(architectures=architectures):
                report = synthetic_report()
                row(report, "checks", "native")["details"]["architectures"] = architectures
                self.rejected(report, "native_architecture")

    def test_each_framework_dependency_required(self):
        for missing in SDK_FRAMEWORKS:
            with self.subTest(framework=missing):
                report = synthetic_report()
                details = row(report, "checks", "frameworks")["details"]
                details["dependencies"] = [path for path in details["dependencies"]
                                           if "/" + missing + ".framework/" not in path]
                self.rejected(report, "framework_dependency_missing")

    def test_framework_execution_is_outside_scope(self):
        report = synthetic_report()
        row(report, "checks", "frameworks")["details"]["executed"] = True
        self.rejected(report, "framework_execution_scope")

    def test_wrong_coff_and_linked_pe_machines_rejected(self):
        for target in MACHINES:
            for kind, field, code in (("compile", "machine", "coff_machine_mismatch"),
                                      ("link", "pe_machine", "pe_machine_or_scope_mismatch")):
                with self.subTest(target=target, kind=kind):
                    report = synthetic_report()
                    row(report, "checks", target + "." + kind)["details"][field] = 0
                    self.rejected(report, code)

    def test_arm64ec_object_and_linked_pe_have_distinct_machine_tags(self):
        report = synthetic_report()
        self.assess(report)
        row(report, "checks", "arm64ec.link")["details"]["pe_machine"] = 0xA641
        self.rejected(report, "pe_machine_or_scope_mismatch")

    def test_any_pe_execution_claim_rejected(self):
        for target in MACHINES:
            with self.subTest(target=target):
                report = synthetic_report()
                row(report, "checks", target + ".link")["details"]["executed"] = True
                self.rejected(report, "pe_machine_or_scope_mismatch")

    def test_missing_import_export_resource_and_unwind_rejected(self):
        for target in MACHINES:
            required = {"imports": "missing_import", "exports": "missing_export",
                        "resources": "missing_resource"}
            if target != "i686":
                required["unwind"] = "missing_unwind"
            for feature, code in required.items():
                with self.subTest(target=target, feature=feature):
                    report = synthetic_report()
                    row(report, "commands", target + "." + feature + ".inspect")["stdout"] = ""
                    self.rejected(report, code)

    def test_import_needs_both_expected_dll_and_symbol(self):
        for output in ("Name: pear-toolchain.dll\n", "Symbol: pear_toolchain_add\n"):
            with self.subTest(output=output):
                report = synthetic_report()
                row(report, "commands", "aarch64.imports.inspect")["stdout"] = output
                self.rejected(report, "missing_import")

    def test_resource_id_and_full_payload_are_required(self):
        for old, new in (("101", "102"), ("50454152", "50454153"), ("2A00", "2B00")):
            with self.subTest(replacement=(old, new)):
                report = synthetic_report()
                item = row(report, "commands", "aarch64.resources.inspect")
                item["stdout"] = item["stdout"].replace(old, new)
                self.rejected(report, "missing_resource")

    def test_i386_assembly_does_not_claim_unwind_support(self):
        report = synthetic_report()
        checks, commands = self.assess(report)
        self.assertIn("i686.assembly", checks)
        self.assertNotIn("i686.unwind", checks)
        self.assertEqual(commands["i686.unwind.inspect"]["stdout"], "")

    def test_arm64ec_requires_two_nonzero_metadata_pointers(self):
        for pointers in ((), ("140003000",), ("0", "180003000"), ("140003000", "0"),
                         ("0", "0"), ("140003000", "180003000", "190003000")):
            with self.subTest(pointers=pointers):
                report = synthetic_report()
                output = "".join("CHPEMetadataPointer: 0x" + value + "\n" for value in pointers)
                row(report, "commands", "arm64ec.support.inspect")["stdout"] = output
                row(report, "checks", "arm64ec.support")["details"]["output"] = output
                self.rejected(report, "arm64ec_metadata_missing")

    def test_arm64ec_metadata_check_binds_actual_inspection_output(self):
        report = synthetic_report()
        details = row(report, "checks", "arm64ec.support")["details"]
        details["output"] = details["output"].replace("140003000", "140004000")
        self.rejected(report, "arm64ec_metadata_missing")

    def test_wrong_compiler_baseline_is_rejected(self):
        for output in ("", "clang version 22.1.0\n", "clang version 23.1.2\n",
                       "clang version 23.1.10\n"):
            with self.subTest(output=output):
                report = synthetic_report()
                row(report, "commands", "compiler.version")["stdout"] = output
                self.rejected(report, "compiler_baseline_mismatch")

    def test_wrong_bison_version_rejected(self):
        for output in ("bison (GNU Bison) 2.3\n", "bison (GNU Bison) 3.8.20\n"):
            with self.subTest(output=output):
                report = synthetic_report()
                row(report, "commands", "bison.version")["stdout"] = output
                self.rejected(report, "bison_version")

    def test_unsupported_schema_kind_and_identity_rejected(self):
        for field, value, code in (
                ("schema_version", 2, "unsupported_record_version"),
                ("schema_version", True, "unsupported_record_version"),
                ("record_kind", "wine_runtime_check", "unexpected_record_kind"),
                ("lock_sha256", "4" * 64, "toolchain_lock_mismatch"),
                ("config_sha256", "5" * 64, "configuration_mismatch")):
            with self.subTest(field=field, value=value):
                report = synthetic_report()
                report[field] = value
                self.rejected(report, code)

    def test_scope_booleans_are_explicit_and_typed(self):
        for field in ("pe_execution", "wine_runtime_execution"):
            for value in (True, None, 0, "false"):
                with self.subTest(field=field, value=value):
                    report = synthetic_report()
                    report[field] = value
                    self.rejected(report, "execution_scope_mismatch")


class CommandLogTests(unittest.TestCase):
    """Real files under an owned temporary root; no subprocess is launched."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.work = self.root / ".build/task4/synthetic.work"
        self.work.mkdir(parents=True)
        patcher = mock.patch.object(verify, "REPO", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def make_report(self, ident="native.compile", stdout=b"compiler output\n", stderr=b""):
        cwd = self.work
        if ident.startswith("configure."):
            cwd = self.work / ("configure-" + ident.split(".")[1])
        logs = cwd / ".pear-command-logs"
        logs.mkdir(parents=True, exist_ok=True)
        command = {"id": ident, "argv": ["/usr/bin/arch", "-arm64", "/synthetic/compiler"],
                   "cwd": str(cwd)}
        for name, data in (("stdout", stdout), ("stderr", stderr)):
            path = logs / (ident + "." + name)
            path.write_bytes(data)
            command[name] = data[:16000].decode("utf-8", errors="replace")
            command[name + "_preview_truncated"] = len(data) > 16000
            command[name + "_log"] = {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(),
                                       "size_bytes": len(data)}
        return {"commands": [command]}

    def check_logs(self, report):
        return verify.verify_command_logs(report, self.work)

    def test_complete_local_log_binding(self):
        report = self.make_report()
        self.assertIsNone(self.check_logs(report))

    def test_configure_and_make_query_bind_their_specific_directories(self):
        for ident in ("configure.arm64", "configure.arm64ec-build",
                      "configure.arm64.make-query", "configure.arm64ec-build.make-query"):
            with self.subTest(ident=ident):
                report = self.make_report(ident)
                self.check_logs(report)
                report["commands"][0]["cwd"] = str(self.work)
                with self.assertRaisesRegex(Error, "command_directory_scope"):
                    self.check_logs(report)

    def test_in_root_wrong_directory_does_not_match_command_role(self):
        report = self.make_report()
        wrong = self.work / "aarch64"
        wrong.mkdir()
        report["commands"][0]["cwd"] = str(wrong)
        with self.assertRaisesRegex(Error, "command_directory_scope"):
            self.check_logs(report)

    def test_recorded_alias_to_expected_directory_is_supported(self):
        report = self.make_report()
        alias = self.root / "owned-alias"
        alias.symlink_to(self.work, target_is_directory=True)
        command = report["commands"][0]
        command["cwd"] = str(alias)
        for stream in ("stdout", "stderr"):
            command[stream + "_log"]["path"] = str(alias / ".pear-command-logs" /
                                                  (command["id"] + "." + stream))
        self.check_logs(report)

    def test_changed_bytes_after_preview_still_fail_hash_binding(self):
        report = self.make_report(stdout=b"x" * 16000 + b"original")
        log = Path(report["commands"][0]["stdout_log"]["path"])
        log.write_bytes(b"x" * 16000 + b"tampered")
        with self.assertRaisesRegex(Error, "command_log_identity"):
            self.check_logs(report)

    def test_size_digest_and_typed_size_are_required(self):
        for field, value in (("sha256", "0" * 64), ("size_bytes", 1), ("size_bytes", False)):
            with self.subTest(field=field, value=value):
                report = self.make_report()
                report["commands"][0]["stderr_log"][field] = value
                with self.assertRaisesRegex(Error, "command_log_identity"):
                    self.check_logs(report)

    def test_multibyte_preview_cut_matches_producer_decoding(self):
        data = b"x" * 15999 + "é".encode("utf-8") + b"tail" * 4000
        report = self.make_report(stdout=data)
        command = report["commands"][0]
        self.assertTrue(command["stdout"].endswith("\ufffd"))
        self.assertTrue(command["stdout_preview_truncated"])
        self.check_logs(report)
        command["stdout"] = "x" * 15999 + "é"
        with self.assertRaisesRegex(Error, "command_log_preview"):
            self.check_logs(report)

    def test_preview_content_and_typed_truncation_flag_are_required(self):
        for field, value in (("stdout", "different"), ("stdout_preview_truncated", True),
                             ("stdout_preview_truncated", 0)):
            with self.subTest(field=field, value=value):
                report = self.make_report()
                report["commands"][0][field] = value
                with self.assertRaisesRegex(Error, "command_log_preview"):
                    self.check_logs(report)

    def test_log_cap_is_enforced_before_full_file_read(self):
        report = self.make_report(stdout=b"x" * (256 * 1024))
        self.check_logs(report)
        command = report["commands"][0]
        log = Path(command["stdout_log"]["path"])
        data = b"x" * (256 * 1024 + 1)
        log.write_bytes(data)
        command["stdout_log"].update(size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        with self.assertRaisesRegex(Error, "input_size_limit"):
            self.check_logs(report)

    def test_missing_log_rejected_with_bounded_error(self):
        report = self.make_report()
        Path(report["commands"][0]["stdout_log"]["path"]).unlink()
        with self.assertRaisesRegex(Error, "command_log_unavailable"):
            self.check_logs(report)

    def test_log_leaf_symlink_rejected(self):
        report = self.make_report()
        log = Path(report["commands"][0]["stdout_log"]["path"])
        target = self.work / "other-file"
        target.write_bytes(log.read_bytes())
        log.unlink()
        log.symlink_to(target)
        with self.assertRaisesRegex(Error, "command_log_path"):
            self.check_logs(report)

    def test_log_parent_symlink_rejected(self):
        report = self.make_report()
        directory = self.work / ".pear-command-logs"
        target = self.work / "moved-logs"
        directory.rename(target)
        directory.symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(Error, "command_log_path"):
            self.check_logs(report)

    def test_fifo_log_is_rejected_without_blocking(self):
        report = self.make_report()
        log = Path(report["commands"][0]["stdout_log"]["path"])
        log.unlink()
        os.mkfifo(log)
        with self.assertRaisesRegex(Error, "nonregular_input"):
            self.check_logs(report)

    def test_different_reported_file_cannot_substitute_matching_bytes(self):
        report = self.make_report()
        original = Path(report["commands"][0]["stdout_log"]["path"])
        other = self.root / "outside-log"
        other.write_bytes(original.read_bytes())
        report["commands"][0]["stdout_log"]["path"] = str(other)
        with self.assertRaisesRegex(Error, "command_log_path"):
            self.check_logs(report)

    def test_missing_metadata_and_wrong_architecture_are_rejected(self):
        report = self.make_report()
        report["commands"][0]["stdout_log"] = None
        with self.assertRaisesRegex(Error, "command_log_shape"):
            self.check_logs(report)
        report = self.make_report()
        report["commands"][0]["argv"] = ["/synthetic/compiler"]
        with self.assertRaisesRegex(Error, "command_architecture_scope"):
            self.check_logs(report)

    def test_unowned_work_root_and_path_command_id_are_rejected(self):
        report = self.make_report()
        with self.assertRaisesRegex(Error, "command_work_scope"):
            verify.verify_command_logs(report, self.root)
        report["commands"][0]["id"] = "../../outside"
        with self.assertRaisesRegex(Error, "command_identifier"):
            self.check_logs(report)


class FailedAttemptsExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.attempts = self.root / ".build/task4"
        self.attempts.mkdir(parents=True)
        patcher = mock.patch.object(evidence, "REPO", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.final_report = synthetic_report()

    def write_attempt(self, name, *, exit_code=1, timed_out=False, prior_digest="7"):
        private = "/Users/private-fixture/PRIVATE-FAILED-ATTEMPT"
        attempt = {"schema_version": 1, "record_kind": "wine_toolchain_check",
                   "passed": False, "pe_execution": False, "wine_runtime_execution": False,
                   "lock_sha256": prior_digest * 64, "config_sha256": "8" * 64,
                   "prepared_sha256": "9" * 64,
                   "fixture_hashes": {key: prior_digest * 64 for key in self.final_report["fixture_hashes"]},
                   "error": "OSError: " + private,
                   "checks": [{"id": "native", "status": "passed", "details": {"path": private}},
                              {"id": "failure", "status": "failed", "details": {"error": private}}],
                   "commands": [{"id": "aarch64.main.obj", "exit_code": exit_code,
                                 "timed_out": timed_out, "output_limit": False,
                                 "argv": [private], "cwd": private, "stderr": private,
                                 "stdout": "PRIVATE-FAILED-ATTEMPT", "account": private}]}
        path = self.attempts / name
        path.write_text(json.dumps(attempt) + "\n", encoding="utf-8")
        return path, attempt

    def test_private_failed_diagnostics_are_excluded_but_failure_is_retained(self):
        path, _ = self.write_attempt("failure.json", exit_code=7)
        before = path.read_bytes()
        result = evidence.summarize_failed_attempts([path], self.final_report)
        serialized = json.dumps(result)
        self.assertNotIn("PRIVATE-FAILED-ATTEMPT", serialized)
        self.assertNotIn("/Users/private-fixture", serialized)
        self.assertNotIn(str(path), serialized)
        self.assertEqual(result[0]["record_sha256"], hashlib.sha256(before).hexdigest())
        self.assertFalse(result[0]["passed"])
        self.assertEqual(result[0]["commands"], [{"id": "aarch64.main.obj", "exit_code": 7,
                                               "timed_out": False, "output_limit": False}])
        self.assertEqual(result[0]["completed_checks"], ["native"])
        self.assertEqual(path.read_bytes(), before)

    def test_driver_exception_history_exports_only_fixed_provenance(self):
        path = self.attempts / "driver-failure.json"
        value = {"schema_version": 1, "record_kind": "wine_toolchain_driver_failure",
                 "exit_code": 1, "completed_check_report": False,
                 "exception": "TypeError: /Users/private-fixture/PRIVATE-DRIVER-ERROR",
                 "argv": ["/Users/private-fixture/PRIVATE-DRIVER-ERROR"],
                 "diagnostic_provenance": "PRIVATE-DRIVER-ERROR"}
        path.write_text(json.dumps(value) + "\n", encoding="utf-8")
        before = path.read_bytes()
        result = evidence.summarize_failed_attempts([path], self.final_report)
        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertEqual(set(item), {"id", "record_sha256", "passed", "kind", "exit_code",
                                     "completed_check_report", "diagnostic_provenance"})
        self.assertEqual(item["kind"], "uncaught_driver_exception")
        self.assertEqual(item["record_sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(item["exit_code"], 1)
        self.assertFalse(item["passed"])
        self.assertFalse(item["completed_check_report"])
        self.assertIn("transcribed", item["diagnostic_provenance"])
        self.assertNotIn("PRIVATE-DRIVER-ERROR", json.dumps(result))
        self.assertNotIn("/Users/private-fixture", json.dumps(result))
        self.assertEqual(path.read_bytes(), before)
        for changes in ({"exit_code": 0}, {"exit_code": True}, {"completed_check_report": True}):
            with self.subTest(changes=changes):
                invalid = dict(value, **changes)
                path.write_text(json.dumps(invalid) + "\n", encoding="utf-8")
                with self.assertRaisesRegex(Error, "driver_failure_scope"):
                    evidence.summarize_failed_attempts([path], self.final_report)

    def test_arbitrary_private_command_id_is_rejected(self):
        path, attempt = self.write_attempt("unknown-command.json")
        attempt["commands"][0]["id"] = "/Users/private-fixture/PRIVATE-FAILED-ATTEMPT"
        path.write_text(json.dumps(attempt) + "\n", encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(Error) as caught:
            evidence.summarize_failed_attempts([path], self.final_report)
        self.assertEqual(str(caught.exception), "attempt_command_scope")
        self.assertEqual(path.read_bytes(), before)

    def test_failure_history_keeps_order_original_digests_and_timeout(self):
        first, first_record = self.write_attempt("first.json", exit_code=1, prior_digest="a")
        second, second_record = self.write_attempt("second.json", exit_code=-9, timed_out=True,
                                                   prior_digest="b")
        originals = [path.read_bytes() for path in (first, second)]
        result = evidence.summarize_failed_attempts([first, second], self.final_report)
        self.assertEqual([item["id"] for item in result], ["attempt-1", "attempt-2"])
        self.assertEqual([item["record_sha256"] for item in result],
                         [hashlib.sha256(data).hexdigest() for data in originals])
        for item, original in zip(result, (first_record, second_record)):
            self.assertFalse(item["passed"])
            self.assertEqual(item["lock_sha256"], original["lock_sha256"])
            self.assertEqual(item["fixture_hashes"], original["fixture_hashes"])
        self.assertEqual(result[1]["commands"][0]["exit_code"], -9)
        self.assertTrue(result[1]["commands"][0]["timed_out"])
        self.assertEqual([path.read_bytes() for path in (first, second)], originals)


class ExportPrivacyTests(unittest.TestCase):
    def test_export_discards_private_raw_fields_and_keeps_only_byte_counts(self):
        # Mock the local-file gate only to isolate the exporter's allowlist.
        report = synthetic_report()
        secret = "PRIVATE-EXPORT-MARKER"
        private_path = "/Users/private-fixture/" + secret
        for command in report["commands"]:
            command.update(argv=[private_path], stdout=secret + "é", stderr=secret,
                           cwd=private_path, stdout_log={"path": private_path},
                           environment={"PRIVATE_ACCOUNT": secret})
        for check in report["checks"]:
            check["details"]["private_diagnostic"] = secret
        report["private_profile"] = private_path
        raw = (json.dumps(report) + "\n").encode("utf-8")
        assessment = {"record_kind": "wine_input_assessment", "scope": "wine_component",
                      "toolchain_evidence_sha256": hashlib.sha256(raw).hexdigest(),
                      "gate_passed": True, "source_ports_complete": False,
                      "qualification": {"runtime": "unassessed", "game": "unassessed",
                                        "distribution": "unassessed"}}
        with mock.patch.object(evidence, "validate_stage1", return_value=assessment) as gate, \
             mock.patch.object(evidence, "read_relative", return_value=raw) as load:
            result = evidence.export("inputs", "config", "raw-evidence")
        gate.assert_called_once_with("inputs", "config", "raw-evidence")
        load.assert_called_once_with(Path("."), "raw-evidence")
        serialized = json.dumps(result)
        self.assertNotIn(secret, serialized)
        self.assertNotIn(private_path, serialized)
        self.assertNotIn("PRIVATE_ACCOUNT", serialized)
        self.assertEqual(result["native_fixture_stdout"], NATIVE_STDOUT)
        self.assertEqual(len(result["commands"]), 58)
        first = result["commands"][0]
        self.assertEqual(set(first), {"id", "exit_code", "timed_out", "output_limit",
                                      "stdout_bytes", "stderr_bytes"})
        self.assertEqual(first["stdout_bytes"], len((secret + "é").encode("utf-8")))
        self.assertEqual(first["stderr_bytes"], len(secret.encode("utf-8")))
        self.assertFalse(result["pe_execution"])
        self.assertFalse(result["wine_runtime_execution"])

    def test_record_changed_after_assessment_is_rejected_before_projection(self):
        report = synthetic_report()
        original = (json.dumps(report) + "\n").encode("utf-8")
        assessment = {"toolchain_evidence_sha256": hashlib.sha256(original).hexdigest()}
        report["commands"][0]["id"] = "/Users/private-fixture/PRIVATE-CHANGED-RECORD"
        changed = (json.dumps(report) + "\n").encode("utf-8")
        with mock.patch.object(evidence, "validate_stage1", return_value=assessment), \
             mock.patch.object(evidence, "read_relative", return_value=changed):
            with self.assertRaises(Error) as caught:
                evidence.export("inputs", "config", "raw-evidence")
        self.assertEqual(str(caught.exception), "export_evidence_changed")

    def test_rejected_gate_prevents_raw_record_read_and_export(self):
        with mock.patch.object(evidence, "validate_stage1", side_effect=Error("fixture_rejected")), \
             mock.patch.object(evidence, "read_relative") as load:
            with self.assertRaisesRegex(Error, "fixture_rejected"):
                evidence.export("inputs", "config", "raw-evidence")
        load.assert_not_called()


if __name__ == "__main__":
    unittest.main()
