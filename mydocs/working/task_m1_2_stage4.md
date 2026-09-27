# Task #2 — Stage 4 report

GitHub Issue: [#2](https://github.com/postmelee/pear/issues/2)
Implementation plan: [task_m1_2_impl.md](../plans/task_m1_2_impl.md)
Stage: 4 — ABI and thread correctness
Date: September 28, 2026

## Stage Purpose

Test the native host/foreign x18 boundary, nested callbacks, asynchronous signal restoration and explicitly initialized thread-ordering policy using the authorized signing route from Stage 3. The maintainer explicitly approved this stage after reviewing Stage 3. These finite host trials do not execute or qualify Wine, FEX, Steam or Megabonk.

## Artifacts

| File | Change Summary |
|---|---|
| `host/probe/abi.h`, `abi_child.c`, `abi_thunks.S` | Checked assembly offsets, host-side setup and isolated x18 roundtrip/callback/signal trials |
| `host/probe/abi_evaluate.c` | Exact result assessment; partial initialization, missing restoration and unexpected termination cannot pass |
| `host/probe/thread_probe.h`, `thread_probe.c`, `thread_litmus.S`, `thread_child.c` | Per-worker policy requests, bounded message-passing test, restoration and owned child output |
| `host/probe/baseline.h`, `child_runner.c`, `process_main.c`, `Makefile` | Additional private IDs and explicit ABI suite; default process suite preserved |
| `host/probe/provisioned_probe.py` | Explicit signed ABI invocation, independent semantic validation and sanitized evidence |
| `tests/host/test_abi_capabilities.py`, three `abi_*` C fixtures | 23 protocol, lifecycle, worker-failure and disassembly tests; no unprovisioned x18 execution |
| `tests/host/test_abi_evidence.py` | Nine pure checks of signed result interpretation, privacy and suite selection |
| [Contributor guide](../../docs/host-capabilities.md) | Commands, result interpretation, measured outcomes and remaining boundaries |
| [Stage 4 evidence](task_m1_2_stage4_observations.json) | Source/test/binary bindings, build metadata, full sanitized native reports and verification output |
| Implementation plan and [daily board](../orders/20260928.md) | Explicit approval, concrete contracts and Stage 5 checkpoint |

## Body Change Scope / Lossless Preservation

The original observation CLI, default process suite, Stage 3 controls and historical reports remain intact. `--suite abi` selects a geometry trial plus five new records in the existing self-spawning provisioned executable. The packet remains a private 160-byte same-build contract. The ABI child deadline is ten seconds; ordinary process probes retain three seconds, with existing bounded cleanup after either deadline.

The x18 getter and setter are resolved in host mode. Foreign windows contain audited assembly and calls only to those permitted APIs. Mode checks normalize the boolean result and prevent redundant toggles. Guest x18 is saved before disabling custom mode and restored only after confirming re-entry; macOS restores its own host-side value. Failure exits recheck host mode and trap in assembly if a safe C return cannot be established. Callee-saved registers and stack alignment are preserved.

Each host callback performs a nested guest roundtrip with a different sentinel. Half return an injected error value. Neither a normal return nor an explicit error return may lose the outer guest value or leave host code in foreign mode.

The signal gateway measures entry mode and switches to host mode before its C body. The body uses lock-free state, a precomputed errno address and a pre-resolved async-signal-safe writer. Its compiled code contains only two indirect calls: the allowed getter and writer. The gateway restores the interrupted guest value before return. Cleanup blocks SIGUSR1, joins the sender, drains its pending signal, restores the disposition and clears the published pointer before restoring the mask. Failure to establish a safe lifetime exits the disposable child rather than returning with a live sender referencing stack storage.

Thread workers individually request policy disable/enable/disable. No getter is exposed in the inspected SDK, so results distinguish accepted requests from observed finite behavior. The message-passing payload uses standalone plain STR/STR and LDR/LDR instructions, with coordination outside those pairs. Payload words are not concurrently accessed by ordinary C. Work has a six-second internal budget and a two-second cooperative cleanup budget; the parent remains the final ten-second execution bound. Failed restoration is retained even when joining succeeds.

The relevant x18 contract is documented in SDK 26.5 `usr/include/os/arch/arm64.h`, and the thread setter in `usr/include/mach/mach_traps.h`. The [Wine maintainer's host notes](https://list.winehq.org/hyperkitty/list/wine-devel@list.winehq.org/message/CKG5CEN2BE5VRXZ7O7NX4YUSBH3247WH/) describe the per-thread policy. Older public kernel/trampoline snapshots are not treated as proof of the current implementation. Actual signed behavior supplies this stage's platform evidence.

No source language replacement, system protection change, game launch or distribution qualification is included. Profile contents, identity/device identifiers and generated signed bundles remain outside Git.

## Verification Results

The implementation plan's commands were run:

```sh
make -C host/probe
python3 -m unittest discover -s tests/host -p 'test_*.py' -v
xcrun llvm-objdump --disassemble --no-show-raw-insn .build/host-probe/pear-process-probe
python3 host/probe/provisioned_probe.py --profile "$PEAR_PROVISIONING_PROFILE" --suite abi
python3 host/probe/provisioned_probe.py --profile "$PEAR_PROVISIONING_PROFILE"
git diff --check
```

| Check | Result |
|---|---|
| Build | Passed with Apple clang 21.0.0, SDK 26.5, ARM64 and warnings treated as errors |
| Complete regression suite | `Ran 126 tests in 10.431s` / `OK`; 94 retained tests plus 23 ABI/worker/assembly and nine evidence tests |
| Assembly review | Checked foreign-window call targets, mode transitions, guest saves/restores, 96-byte frames and unfenced litmus payload; no x18-writing fixture executed with fake mode setters |
| Signing and provisioning | Actual unexpired profile, device/certificate binding, effective claims and strict executable/bundle signatures passed |
| Native execution | ABI suite passed in all four layout/page-mode combinations; signed supervisors observed ARM64 and own translation status false |
| Shared-code regression | Rebuilt Stage 3 process suite passed all four combinations with the same input binaries as the ABI run |
| Lifecycle | All 24 ABI and 28 process-suite direct children reaped; worker initialization/restoration/join failures covered separately by fixtures |
| Protections | SIP enabled; Gatekeeper assessments enabled |
| Evidence | Source, assembly, test and binary hashes retained; private strings and local links checked; diff hygiene passed |

Actual ABI results on M4 Pro/macOS 26.5.2 (25F84), in each of the four configurations:

| Trial | Observed result |
|---|---|
| Roundtrip | 64 completed; host/foreign/host states 0/1/0; guest value `0x11223344` preserved across the getter |
| Callbacks | 32 host callbacks, nested guest returns and outer restorations; all 16 injected error returns propagated correctly; final host mode 0 |
| Signals | Host handler entry 0, foreign handler entry 1; two actual host-body writes; interrupted context and resumed guest value preserved; final host mode 0 |
| Policy lifecycle | Two workers each initialized, enabled, restored and joined successfully |

Message-passing results:

| Configuration | Baseline trials | Baseline forbidden observations | Enabled trials | Enabled forbidden observations |
|---|---:|---:|---:|---:|
| Standard / default pages | 10,000 | 3 | 10,000 | 0 |
| Standard / 4 KiB pages | 10,000 | 2 | 10,000 | 0 |
| Emulation / default pages | 10,000 | 0 | 10,000 | 0 |
| Emulation / 4 KiB pages | 10,000 | 0 | 10,000 | 0 |

Here, forbidden means observing flag=1 and data=0 after writer data=1 then flag=1. The five baseline observations demonstrate that this payload can expose an ordering difference on the test machine. Zero forbidden observations across 40,000 enabled-policy trials is finite supporting evidence, not a universal TSO proof. Store-buffering both-zero is allowed under x86-TSO and is deliberately not used as a failure condition. The [x86-TSO model](https://www.cl.cam.ac.uk/~pes20/weakmemory/x86tso-paper.pdf) provides the model distinction.

The process regression retained 16 KiB default user pages, 4 KiB requested user pages and 16 KiB kernel pages. JIT returned 42 in every configuration; middle-page protection/recommit passed. Standard-layout low mapping stayed unavailable, while the explicit 64 KiB PAGEZERO layout passed. No unavailable comparison result was relabeled as a positive prerequisite.

## Residual Risks

- Rosetta-free Megabonk execution is not achieved. Wine/FEX integration, translated instruction correctness, graphics and performance remain separate work.
- The ABI tests cover deterministic nesting, explicit error returns and controlled SIGUSR1 interruption. They do not implement Windows SEH, general unwinding, longjmp, arbitrary callback frameworks or all asynchronous interruption points.
- The ordering setter has no inspected getter. Successful calls plus finite litmus observations do not directly read a hardware mode bit or prove a complete x86 memory model.
- These results cover this registered Mac, OS/toolchain and development profile. Ordinary-user distribution, notarization, other hosts and future platform changes remain unqualified.
- Runner containment assumes cooperative owned groups. It is not hostile-code isolation, and a platform refusal to terminate/reap remains a reported failure.
- Stage 5 clean-build reproduction and the complete Issue #2 acceptance mapping remain outstanding.

## Impact on Next Stage

Stage 5 should rebuild from the documented source and toolchain, repeat the approved observation/process/ABI suites through the same authorized route, and map each Issue #2 criterion to passing evidence or an explicit unresolved item. Preserve historical observations and the distinction between native host prerequisites, developer runtime execution and ordinary-user distribution. Do not close #2 on the basis of this stage alone.

## Approval Request

Review the Stage 4 artifacts and evidence, then approve Stage 5: clean-build reproduction and the host capability decision. Stage 5 work has not been performed in this stage.
