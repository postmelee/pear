"""Exercise ABI evidence rules with synthetic packets and ordinary child exits.

No ABI thunk is linked or executed by these fixtures. A fake x18 enable function
would not make it safe to write macOS's reserved register on a real Mac.
"""

import errno
import json
from pathlib import Path
import platform
import re
import signal
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / ".build/host-probe/test-fixtures"
DRIVER = BUILD / "abi-runner-driver"
FIXTURE = BUILD / "abi-runner-fixture"
ROUNDTRIP, CALLBACKS, SIGNALS, POLICY, LITMUS = range(10, 15)
DEFAULT, PAGES_4K = 0, 1


@unittest.skipUnless(platform.system() == "Darwin", "Requires the macOS SDK")
class AbiCapabilitiesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        BUILD.mkdir(parents=True, exist_ok=True)
        common = ["xcrun", "clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                  "-arch", "arm64", "-I", str(ROOT / "host/probe")]
        builds = [
            [*common, str(ROOT / "tests/host/abi_runner_fixture.c"), "-o", str(FIXTURE)],
            [*common, str(ROOT / "tests/host/abi_runner_driver.c"),
             str(ROOT / "host/probe/child_runner.c"),
             str(ROOT / "host/probe/abi_evaluate.c"),
             str(ROOT / "host/probe/process_evaluate.c"),
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

    def spawn(self, probe, variant="valid"):
        report = self.driver("spawn", FIXTURE, probe, variant)
        self.assertTrue(report["no_children"], report)
        if report["returned"] == 0:
            self.assertTrue(report["child_reaped"], report)
        return report

    def assessment(self, probe, mutation="valid", mode=DEFAULT):
        return self.driver("assess", probe, mode, mutation)["assessment"]

    def test_all_abi_packet_types_accept_complete_evidence(self):
        for probe in range(ROUNDTRIP, LITMUS + 1):
            with self.subTest(probe=probe):
                report = self.spawn(probe)
                self.assertEqual(report["outcome"], "exited")
                self.assertEqual(report["exit_code"], 0)
                self.assertTrue(report["packet_valid"])
                self.assertEqual(report["assessment"], "passed")

    def test_armed_phase_is_never_valid_for_an_abi_probe(self):
        for probe in range(ROUNDTRIP, LITMUS + 1):
            with self.subTest(probe=probe):
                report = self.spawn(probe, "armed")
                self.assertEqual(report["outcome"], "invalid_output")
                self.assertFalse(report["packet_valid"])
                self.assertEqual(report["assessment"], "failed")

    def test_skipped_prerequisites_and_wrong_identity_are_rejected(self):
        for probe in range(ROUNDTRIP, LITMUS + 1):
            for variant in ("missing-prerequisite", "wrong-identity"):
                with self.subTest(probe=probe, variant=variant):
                    report = self.spawn(probe, variant)
                    self.assertEqual(report["outcome"], "invalid_output")
                    self.assertFalse(report["packet_valid"])
                    self.assertEqual(report["assessment"], "failed")

    def test_next_unknown_probe_id_is_rejected_before_spawn(self):
        report = self.spawn(LITMUS + 1)
        self.assertEqual(report["returned"], -1)
        self.assertEqual(report["error_code"], errno.EINVAL)
        self.assertFalse(report["packet_valid"])
        self.assertFalse(report["child_reaped"])

    def test_failure_can_retain_cleanup_without_becoming_success(self):
        for probe in (POLICY, LITMUS):
            with self.subTest(probe=probe):
                report = self.spawn(probe, "failed-with-cleanup")
                self.assertEqual(report["outcome"], "exited")
                self.assertTrue(report["packet_valid"])
                self.assertEqual(report["assessment"], "failed")

    def test_missing_apis_and_cleanup_failures_never_pass(self):
        for probe in range(ROUNDTRIP, LITMUS + 1):
            for variant in ("unavailable", "cleanup-failed"):
                with self.subTest(probe=probe, variant=variant):
                    report = self.spawn(probe, variant)
                    self.assertTrue(report["packet_valid"])
                    self.assertNotEqual(report["assessment"], "passed")

    def test_actual_signal_or_nonzero_exit_invalidates_passing_packet(self):
        for probe in range(ROUNDTRIP, LITMUS + 1):
            for variant in ("signal", "nonzero"):
                with self.subTest(probe=probe, variant=variant):
                    report = self.spawn(probe, variant)
                    self.assertTrue(report["packet_valid"])
                    self.assertEqual(report["assessment"], "failed")
                    if variant == "signal":
                        self.assertEqual(report["outcome"], "signaled")
                        self.assertEqual(report["term_signal"], signal.SIGTERM)
                    else:
                        self.assertEqual(report["exit_code"], 7)

    def test_x18_values_and_completed_iteration_counts_are_exact(self):
        for probe in (ROUNDTRIP, CALLBACKS, SIGNALS):
            self.assertEqual(self.assessment(probe), "passed")
            for index in range(6):
                with self.subTest(probe=probe, index=index):
                    self.assertEqual(self.assessment(probe, f"value-{index}"), "failed")

    def test_policy_initialization_restoration_and_join_counts_are_exact(self):
        self.assertEqual(self.assessment(POLICY), "passed")
        for index in range(6):
            with self.subTest(index=index):
                self.assertEqual(self.assessment(POLICY, f"value-{index}"), "failed")
        report = self.spawn(POLICY, "policy-partial")
        self.assertTrue(report["packet_valid"])
        self.assertEqual(report["assessment"], "failed")

    def test_litmus_allows_any_bounded_baseline_observation(self):
        for mutation in ("valid", "baseline-observed", "baseline-all"):
            with self.subTest(mutation=mutation):
                self.assertEqual(self.assessment(LITMUS, mutation), "passed")
        report = self.spawn(LITMUS, "baseline-reordered")
        self.assertTrue(report["packet_valid"])
        self.assertEqual(report["assessment"], "passed")

    def test_litmus_rejects_impossible_counts_partial_workers_and_enabled_reordering(self):
        for mutation in ("baseline-negative", "baseline-overflow", "partial-workers",
                         "value-1", "value-3", "value-4", "value-5"):
            with self.subTest(mutation=mutation):
                self.assertEqual(self.assessment(LITMUS, mutation), "failed")
        report = self.spawn(LITMUS, "enabled-reordered")
        self.assertTrue(report["packet_valid"])
        self.assertEqual(report["assessment"], "failed")

    def test_termination_and_packet_evidence_are_required_for_every_probe(self):
        mutations = ("null", "not-reaped", "invalid-packet", "wrong-identity",
                     "nonzero-exit", "timeout", "signal", "error-code", "armed",
                     "cleanup-failed", "cleanup-not-run")
        for probe in range(ROUNDTRIP, LITMUS + 1):
            for mutation in mutations:
                with self.subTest(probe=probe, mutation=mutation):
                    self.assertEqual(self.assessment(probe, mutation), "failed")
            for index in range(6):
                with self.subTest(probe=probe, missing=index):
                    self.assertNotEqual(self.assessment(probe, f"missing-{index}"), "passed")

    def test_page_attribute_evidence_matches_the_requested_mode(self):
        for probe in range(ROUNDTRIP, LITMUS + 1):
            self.assertEqual(self.assessment(probe, mode=PAGES_4K), "passed")
            for mutation in ("no-attribute", "attribute-error"):
                with self.subTest(probe=probe, mutation=mutation):
                    self.assertEqual(self.assessment(probe, mutation, PAGES_4K), "failed")
            self.assertEqual(self.assessment(probe, "unexpected-attribute"), "failed")
            self.assertEqual(self.assessment(probe, "attribute-error"), "failed")
            self.assertEqual(self.assessment(probe, mode=99), "failed")


@unittest.skipUnless(platform.system() == "Darwin", "Requires the macOS SDK")
class ThreadWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        BUILD.mkdir(parents=True, exist_ok=True)
        cls.fixture = BUILD / "abi-thread-fixture"
        result = subprocess.run([
            "xcrun", "clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-arch", "arm64", "-DPEAR_THREAD_PROBE_TEST", "-I", str(ROOT / "host/probe"),
            str(ROOT / "tests/host/abi_thread_fixture.c"),
            str(ROOT / "host/probe/thread_probe.c"), "-o", str(cls.fixture)
        ], capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise RuntimeError(f"Thread fixture compilation failed:\n{result.stderr}")

    def run_workers(self, kind, scenario="valid"):
        result = subprocess.run([str(self.fixture), kind, scenario],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def test_policy_is_initialized_enabled_and_restored_on_both_workers(self):
        report = self.run_workers("policy")
        self.assertEqual([report[key] for key in ("initial_calls", "enabled_calls", "restored_calls")],
                         [2, 2, 2])
        self.assertEqual([step["status"] for step in report["steps"]], [1] * 6)
        self.assertEqual([step["value"] for step in report["steps"]], [1, 2, 2, 2, 2, 2])

    def test_missing_policy_never_starts_a_worker(self):
        for kind in ("policy", "litmus"):
            with self.subTest(kind=kind):
                report = self.run_workers(kind, "missing")
                self.assertEqual(report["initial_calls"], 0)
                self.assertEqual(report["enabled_calls"], 0)
                self.assertEqual(report["restored_calls"], 0)
                self.assertEqual(report["steps"][0]["status"], 2)
                self.assertTrue(all(step["status"] == 0 for step in report["steps"][1:]))

    def test_partial_initialization_and_enable_failure_still_restore_both_workers(self):
        for scenario, failed_slot, enabled_count in (("initial-failed", 2, 1),
                                                     ("enable-failed", 3, 2)):
            with self.subTest(scenario=scenario):
                report = self.run_workers("policy", scenario)
                self.assertEqual(report["initial_calls"], 2)
                self.assertEqual(report["enabled_calls"], enabled_count)
                self.assertEqual(report["restored_calls"], 2)
                failure = report["steps"][failed_slot]
                self.assertEqual(failure["status"], 3)
                self.assertEqual(failure["domain"], 2)
                self.assertNotEqual(failure["code"], 0)
                self.assertEqual(failure["value"], 1)
                self.assertTrue(all(step["status"] == 0
                                    for step in report["steps"][failed_slot + 1:5]))
                self.assertEqual(report["steps"][5]["status"], 1)
                self.assertEqual(report["steps"][5]["value"], 2)

    def test_restore_error_is_retained_after_successful_thread_joins(self):
        report = self.run_workers("policy", "restore-failed")
        self.assertEqual(report["restored_calls"], 2)
        self.assertEqual(report["steps"][4]["status"], 3)
        self.assertEqual(report["steps"][5]["status"], 3)
        self.assertEqual(report["steps"][5]["domain"], 2)
        self.assertNotEqual(report["steps"][5]["code"], 0)
        self.assertEqual(report["steps"][5]["value"], 2)

    def test_litmus_completes_both_phases_and_restores_every_worker(self):
        report = self.run_workers("litmus", "baseline-only-forbidden")
        self.assertEqual([report[key] for key in ("initial_calls", "enabled_calls", "restored_calls")],
                         [2, 2, 2])
        self.assertEqual([step["status"] for step in report["steps"]], [1] * 6)
        self.assertEqual([step["value"] for step in report["steps"]], [2, 10000, 10000, 10000, 0, 2])

    def test_enabled_forbidden_outcomes_fail_while_cleanup_remains_visible(self):
        report = self.run_workers("litmus", "forbidden")
        self.assertEqual(report["steps"][2]["status"], 1)
        self.assertEqual(report["steps"][2]["value"], 10000)
        self.assertEqual(report["steps"][4]["status"], 3)
        self.assertEqual(report["steps"][4]["value"], 10000)
        self.assertEqual(report["steps"][5]["status"], 1)
        self.assertEqual(report["steps"][5]["value"], 2)
        self.assertEqual(report["restored_calls"], 2)

    def test_litmus_invalid_payload_and_enable_failure_never_pass(self):
        for scenario, failed_slot in (("invalid-payload", 1), ("enable-failed", 3)):
            with self.subTest(scenario=scenario):
                report = self.run_workers("litmus", scenario)
                self.assertEqual(report["steps"][failed_slot]["status"], 3)
                self.assertEqual(report["restored_calls"], 2)
                self.assertEqual(report["steps"][5]["status"], 1)
                self.assertEqual(report["steps"][5]["value"], 2)


@unittest.skipUnless(platform.system() == "Darwin", "Requires Apple ARM64 assembler tools")
class AbiAssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        BUILD.mkdir(parents=True, exist_ok=True)
        cls.functions = {}
        for source in ("abi_thunks.S", "thread_litmus.S"):
            output = BUILD / f"{Path(source).stem}-review.o"
            built = subprocess.run([
                "xcrun", "clang", "-arch", "arm64", "-I", str(ROOT / "host/probe"),
                "-c", str(ROOT / "host/probe" / source), "-o", str(output)
            ], capture_output=True, text=True, timeout=60)
            if built.returncode:
                raise RuntimeError(built.stderr)
            dumped = subprocess.run([
                "xcrun", "llvm-objdump", "--macho", "--disassemble", "--no-show-raw-insn", str(output)
            ], capture_output=True, text=True, timeout=30)
            if dumped.returncode:
                raise RuntimeError(dumped.stderr)
            current = None
            for line in dumped.stdout.splitlines():
                symbol = re.fullmatch(r"(_\w+):", line)
                if symbol:
                    current = cls.functions.setdefault(symbol[1], {})
                    continue
                instruction = re.match(r"\s*([0-9a-f]+):\s+([a-z][\w.]*)\s*(.*)", line)
                if current is not None and instruction:
                    current[int(instruction[1], 16)] = (instruction[2], instruction[3].strip())

    def test_foreign_windows_only_call_mode_apis_and_restore_mode_before_host_calls(self):
        # This bounded control-flow check assumes the documented API semantics.
        # It cannot establish permission, asynchronous correctness or runtime ABI
        # behavior; those require the separately provisioned native trials.
        names = ("_pear_abi_roundtrip_thunk", "_pear_abi_callback_thunk",
                 "_pear_abi_signal_wait_thunk", "_pear_abi_signal_gateway")
        for name in names:
            instructions = self.functions[name]
            for initial_mode in (0, 1):
                pending = [(min(instructions), initial_mode, None, None)]
                visited = set()
                while pending:
                    state = pending.pop()
                    if state in visited:
                        continue
                    visited.add(state)
                    address, mode, value0, value25 = state
                    self.assertIn(address, instructions, (name, state))
                    opcode, operands = instructions[address]
                    self.assertNotIn(opcode, {"bl", "br", "svc"}, (name, address, opcode))
                    if re.search(r"\bx18\b", operands):
                        self.assertEqual(mode, 1, (name, address, "x18 access in host mode"))
                    if opcode == "blr":
                        self.assertIn(operands, {"x20", "x21", "x24"}, (name, address, operands))
                        if operands == "x20":
                            value0 = mode
                        elif operands == "x21":
                            self.assertIn(value0, (0, 1), (name, address, "unknown setter argument"))
                            self.assertNotEqual(value0, mode, (name, address, "double mode toggle"))
                            mode, value0 = value0, None
                        else:
                            self.assertEqual(mode, 0, (name, address, "host callback in foreign mode"))
                            value0 = None
                    elif opcode in ("mov", "and"):
                        parts = [part.strip() for part in operands.split(",")]
                        if parts[0] in ("x0", "w0", "x25", "w25"):
                            source = parts[1]
                            value = value0 if source in ("x0", "w0") else (
                                value25 if source in ("x25", "w25") else (
                                    int(source[1:], 0) if source.startswith("#") else None))
                            if opcode == "and" and value is not None:
                                value &= int(parts[2][1:], 0)
                            if parts[0] in ("x0", "w0"):
                                value0 = value
                            else:
                                value25 = value
                    elif opcode in ("ldr", "ldar", "add") and operands.startswith(("x0,", "w0,")):
                        value0 = None
                    elif opcode == "ldp" and operands.startswith("x25,"):
                        value25 = None
                    if opcode in ("ret", "brk"):
                        expected = initial_mode if name.endswith("signal_gateway") and opcode == "ret" else 0
                        self.assertEqual(mode, expected, (name, address, "wrong mode at exit"))
                        continue
                    targets = [address + 4]
                    if opcode in ("cbz", "cbnz"):
                        register, target = [part.strip() for part in operands.split(",")]
                        value = value0 if register in ("x0", "w0") else value25 if register in ("x25", "w25") else None
                        branch = value == 0 if opcode == "cbz" else value != 0
                        targets = [int(target, 0), address + 4] if value is None else [
                            int(target, 0) if branch else address + 4]
                    elif opcode == "b":
                        targets = [int(operands, 0)]
                    elif opcode.startswith("b."):
                        targets = [int(operands, 0), address + 4]
                    pending.extend((target, mode, value0, value25) for target in targets)
                self.assertGreater(len(visited), 10)

    def test_callbacks_preserve_guest_x18_across_host_transitions(self):
        for name, saved in (("_pear_abi_callback_thunk", "x22"),
                            ("_pear_abi_signal_gateway", "x26")):
            operations = list(self.functions[name].values())
            saved_at = operations.index(("mov", f"{saved}, x18"))
            restored_at = operations.index(("mov", f"x18, {saved}"))
            callback_at = operations.index(("blr", "x24"))
            self.assertLess(saved_at, callback_at)
            self.assertLess(callback_at, restored_at)
            self.assertIn(("blr", "x21"), operations[saved_at:callback_at])
            self.assertIn(("blr", "x21"), operations[callback_at:restored_at])
            for opcode, operands in operations[saved_at + 1:restored_at]:
                if opcode in ("mov", "ldr", "add", "sub"):
                    self.assertNotIn(operands.split(",")[0].strip(),
                                     {saved, f"w{saved[1:]}"}, "Saved guest x18 was overwritten")
            for operation in ("stp", "ldp"):
                self.assertTrue(any(opcode == operation and
                                    saved in [part.strip() for part in operands.split(",")[:2]]
                                    for opcode, operands in operations))

    def test_litmus_payload_has_plain_ordered_memory_accesses_without_fences(self):
        writer = list(self.functions["_pear_litmus_write"].values())
        reader = list(self.functions["_pear_litmus_read"].values())
        self.assertEqual([operands for opcode, operands in writer if opcode == "str"],
                         ["w2, [x0]", "w2, [x1]"])
        self.assertEqual([operands for opcode, operands in reader if opcode == "ldr"],
                         ["w2, [x1]", "w3, [x0]"])
        forbidden = {"dmb", "dsb", "isb", "ldar", "ldapr", "stlr", "bl", "blr"}
        self.assertFalse(any(opcode in forbidden for opcode, _ in writer + reader))
        self.assertIn(("dmb", "ish"), self.functions["_pear_litmus_reset"].values())


if __name__ == "__main__":
    unittest.main()
