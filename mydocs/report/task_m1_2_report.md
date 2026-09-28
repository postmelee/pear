# Task #2 — Host capability final report

GitHub Issue: [#2](https://github.com/postmelee/pear/issues/2)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Date: September 28, 2026

## Work Summary

- Target Issue: #2, probe macOS ABI, memory, JIT and signing capabilities.
- Milestone: M1; all five approved task stages are complete.
- Purpose: establish a reproducible native host prerequisite for later ARM64 Wine/FEX integration through normal platform authorization.
- Decision: the bounded host gate passes on M4 Pro/macOS 26.5.2 with the selected emulation layout, 4 KiB user pages and validated development profile. This is not a qualified runtime, game or consumer release.

The task adds a C diagnostic, isolated child harness, narrow ARM64 assembly, Python signing/evidence tools and failure tests. It preserves upstream-language flexibility and does not select a new manager language or CPU translator. The task requester approved each stage before execution. Stage 5 reproduced the Stage 4 implementation without source changes.

## Changed Files and Impact Area

| Path | Change Summary | Impact Area |
|---|---|---|
| `host/probe/observations.*`, `main.c` | Versioned, process-local observations with explicit unavailable/error results | Diagnostic contract and privacy |
| `host/probe/baseline*`, `child_runner.c` | Owned child groups, bounded output/deadlines, exact termination evidence, memory/protection/JIT trials | Native lifecycle and failure isolation |
| `host/probe/process_*`, `Makefile` | Default/4 KiB process modes, separate low-address layout, subpage/recommit trials | Host memory and build configuration |
| `host/probe/abi*`, `thread_*` | Foreign/host transitions, nested callbacks/signals/error returns and explicit worker policy | ABI and memory-order prerequisites |
| `host/probe/hardened_baseline.py`, `provisioned_probe.py` | Real authorization checks, fresh signed controls, independent result assessment | Developer signing and evidence |
| `tests/host/` | 126 tests including failure, containment, signing-policy, packet and assembly checks | Regression coverage |
| `docs/host-capabilities.md`, documentation index and host audit | Contributor commands, dated evidence, declared passing configuration and limits | Approved contributor documentation |
| `.gitignore`, `mydocs/` task artifacts | Ignore generated/private artifacts; retain plans, stage evidence and reports | Reproducibility and review |

## Document Location Verification

| File | Planned Location | Actual Location | Result | Evidence |
|---|---|---|---|---|
| Host capability guide | `docs/host-capabilities.md` | Same | OK | [Approved location judgment](../plans/task_m1_2.md#document-location-judgment); reusable contributor instructions |
| Documentation index | `docs/README.md` | Same | OK | Narrow guide link/description; no relocation |
| Historical host audit | `docs/research/macos-runtime-audit.md` | Same | OK | Dated follow-ups preserve original research |
| Plans, stage evidence and final report | `mydocs/plans/`, `mydocs/working/`, `mydocs/report/` | Same | OK | Issue-specific work records remain outside product documentation |

## Quantitative Before/After Comparison

| Metric | Before Issue #2 | After Stage 5 |
|---|---|---|
| Pear native host executables | 0 | 5 ARM64-only targets |
| Automated host tests | 0 | 126 passing in the final run |
| Authorized native process/ABI evidence | No executed Pear suite | Four process and four ABI configuration assessments passed |
| Fresh-output reproduction | None | 38 unchanged source/test hashes; 5/5 pre-signing binary hashes equal Stage 4 |
| Final dedicated child lifecycle evidence | None | 64/64 direct children reaped |
| Final enabled-policy message-passing sample | None | 40,000 trials, zero forbidden observations |

These are engineering coverage counts, not performance measurements or a compatibility score.

## Verification Results

The latest [evidence record](../working/task_m1_2_stage5_observations.json) binds source commit `7fb66dd892ddbe9d44e0e853c3ab0e5eff446959`, source/test hashes, Apple clang 21.0.0, SDK 26.5, rebuilt artifacts, actual signatures and outcomes. Later changes in this report bundle are documentation/evidence only.

| Issue Acceptance Criterion | Result |
|---|---|
| Versioned source, commands and redacted results report each capability as passed, failed or unavailable on the declared Mac/OS | **OK.** Five native binaries and 126 tests built and passed from fresh outputs on M4 Pro/macOS 26.5.2 (25F84). Commands, versions, raw numeric statuses/errors and input/signed hashes are retained in sanitized evidence. Denied sandbox queries, standard-layout low-map unavailability and the negative JIT allocation failure remain explicit. |
| Nested callbacks, signals and failure exits preserve guest/host ABI state; 4 KiB semantics and per-thread policy are verified rather than assumed | **OK within the approved bounded scope.** Each of four ABI configurations completed 64 roundtrips, 32 nested callbacks, 16 injected error returns and host/foreign SIGUSR1 entry/resumption with preservation. Actual 4 KiB protection/recommit and armed faults passed. Workers individually initialized/enabled/restored the policy and joined; 40,000 enabled trials had zero forbidden observations. No getter, inheritance, universal TSO or general exception/unwind result is inferred. |
| Every prerequisite for the declared M1 configuration passes through a normal signed path; any distribution limitation is explicit and cannot be described as a general release | **OK for this Issue's host prerequisite.** The selected emulation layout and requested 4 KiB user pages passed low mapping, memory/JIT and finite ABI/thread tests through a real validated Apple Development profile with cross-architecture support, strict signatures and SIP/Gatekeeper enabled. Standard layout is a comparison. This closes only the host-probe contribution to G0; source qualification, integrated M1 runtime/game tests and ordinary-user distribution remain separate gates. |

The reproduction preserved previous build artifacts before creating a new output directory. Five pre-signing binary hashes and the process disassembly exactly match Stage 4. Process and ABI semantics also match after excluding timings and baseline litmus counts. The final baseline counts were 3, 6, 0 and 0; all enabled counts were zero. All 4 baseline, 8 ordinary hardened, 28 process and 24 ABI children were reaped. No owned probe remained running.

The selected profile was unexpired, targeted macOS, matched the explicit App ID, registered device and available development certificate, and granted the actual claimed restricted entitlement. Both executable and bundle signatures passed strict validation. The ordinary Developer ID JIT positive returned 42; its matched negative preserved errno 22 and CLI exit 1 as the expected paired rejection. No credentials, profile payload, private keys, game files or authenticated prefixes are included.

No CI result is claimed. Native execution and signing occurred locally on the declared development Mac; the local checks do not establish independent remote reproduction.

### Stage Verification Results

- [Stage 1](../working/task_m1_2_stage1.md): native observations, privacy and injected failures; 14 tests passed.
- [Stage 2](../working/task_m1_2_stage2.md): bounded child runner and baseline memory/JIT, with unavailable low mapping retained.
- [Stage 3](../working/task_m1_2_stage3.md): real signed process/4 KiB/JIT controls; 94 tests passed.
- [Stage 4](../working/task_m1_2_stage4.md): finite x18/callback/signal/thread trials; 126 tests and all signed assessments passed.
- [Stage 5](../working/task_m1_2_stage5.md): fresh-output rebuild, exact pre-signing binary matches and complete repetition; 126 tests passed in 14.218 seconds.

## Residual Risks and Follow-up Work

### Residual Risks

- Same-host reproduction is not a clean-machine or second-tester result. Other chips, macOS versions and future entitlement policy are unqualified. Diagnostic deployment flags do not establish a supported OS floor.
- Finite SIGUSR1, explicit error returns and message passing leave broader SEH, unwind, asynchronous callback and CPU memory-model coverage to runtime integration.
- One low address, protected 64 KiB PAGEZERO and reserved middle-page replacement are probe results, not a complete Wine memory layout or physical reclamation contract.
- The harness controls cooperative owned process groups. It is not hostile-code isolation; termination/reaping refusal remains an explicit failure.
- Registered-device development execution and local signatures without timestamps do not qualify notarization, a consumer installer or execution without developer registration.
- No Wine/FEX/DXMT, Steam, Megabonk, full required process/module tree, saves or performance was qualified by this task. M1 remains incomplete.

### Follow-up Candidates

- Continue existing [#1 source/toolchain qualification](https://github.com/postmelee/pear/issues/1) and [#3 runtime contracts](https://github.com/postmelee/pear/issues/3); these are independent workstreams, not requirements to fabricate within #2.
- Carry this host contract into [#4 ARM64 Wine](https://github.com/postmelee/pear/issues/4), [#5 FEX host services](https://github.com/postmelee/pear/issues/5) and [#6 CPU/boundary qualification](https://github.com/postmelee/pear/issues/6).
- Retain complete-process Rosetta evidence in [#10](https://github.com/postmelee/pear/issues/10) and independent signed runtime reproduction in [#13](https://github.com/postmelee/pear/issues/13).
- Ordinary-user distribution still needs a separately approved task with a real distribution package and an unenrolled second Mac. No new Issue or distribution support claim is created by this report.

## Approval Request to Task Requester

Review the final report and Open PR for Issue #2 and approve merge if the bounded acceptance decision is satisfactory. The PR is prepared through the final-report workflow; it is not self-merged. Issue #2 remains open until approval or confirmed merge. Keep the active review branch, worktree and local verification artifacts available until that transition.
