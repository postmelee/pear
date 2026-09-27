# Task #2 — Host capability implementation plan

Task plan: [task_m1_2.md](task_m1_2.md)
GitHub Issue: [#2](https://github.com/postmelee/pear/issues/2)
Milestone: M1

Status: implementation plan and Stage 1 approved on September 27, 2026. The maintainer explicitly resumed the task and approved Stage 2 on September 28, 2026. Stage 3 was then explicitly approved after the Stage 2 report. Later stages retain their own report checkpoints.

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | ARM64 observations | C diagnostic, JSON contract, injected failure fixtures and contributor guide | Native build; meaningful failure cases; Mach-O inspection; redacted actual report |
| 2 | Isolated baseline tests | Child runner and memory/JIT leaf probes | Timeout/signal/output containment; baseline execution semantics |
| 3 | Signed process capabilities | Signing procedure and 4 KiB/process/JIT cases | Real authorized identity/profile; signature checks; normal platform protections |
| 4 | ABI and thread correctness | Narrow x18 thunks and callback/signal/thread fixtures | Guest state preservation; host-mode calls; per-thread initialization |
| 5 | Reproduction and decision | Rebuilt evidence and capability decision | Every Issue criterion mapped to passing evidence or an explicit open prerequisite |

## Document Location Check

| Artifact | Task-plan location | Actual planned path | Match | Notes |
|---|---|---|---|---|
| Diagnostic implementation | `host/probe/` | `host/probe/Makefile`, `host/probe/main.c`, `host/probe/observations.c`, `host/probe/observations.h` | OK | C directly observes host ABI facilities; no manager-language selection |
| Diagnostic tests | `tests/host/` | `tests/host/test_diagnostics.py`, `tests/host/diagnostic_fixture.c` | OK | Standard-library Python and native redistributable fixtures |
| Contributor guide | `docs/host-capabilities.md` | Same | OK | Explicit distinction between observations and execution qualification |
| Later probe modules | `host/probe/` and `tests/host/` | Child runner, memory/JIT and ABI modules | OK | Introduced only at the corresponding approved stage |
| Task evidence | `mydocs/working/` | Stage reports and sanitized result JSON | OK | No raw identity, account or private-path output |

Build outputs and unreviewed local results go under ignored `/.build/`. Existing experimental files remain outside the task worktree.

## Stage 1 — ARM64 observations

### Artifacts

- `host/probe/` C sources and a Makefile using Apple clang and system frameworks, without third-party dependencies.
- `tests/host/` meaningful injected failures and a real native report validation.
- `docs/host-capabilities.md`; link from the existing documentation index.
- A narrow `/.build/` ignore entry and an English sanitized Stage 1 evidence record.

### Changes

Build an ARM64 diagnostic that writes one JSON object and never changes ABI mode, requests restricted capabilities, launches Steam, or modifies system state. Observe the current executable's Mach-O architecture, its own `sysctl.proc_translated` query, OS/build, page size, selected runtime symbols and signature category. Resolve new APIs dynamically; presence is an observation, not permission to use them.

Use one versioned JSON contract: `schema_version`, probe version, current-process scope, architecture/translation observations, host values, runtime symbol presence, signature category, and capability/qualification fields explicitly set to not run or not assessed. Observation statuses distinguish observed, unavailable and failed. A denied query retains its error domain/code; it must never silently become false, unsupported, or passed. Do not print usernames, account/identity strings, private paths, hostnames or private signing material.

Keep the platform observation boundary injectable for a separate test fixture. The shipped diagnostic accepts no fixture mode or result-spoofing flags. Test JSON escaping with adversarial control characters, denied translation queries, absent runtime symbols, unavailable signature data and unsupported architecture input. A real CLI run must parse as JSON and report only its own process; no field may certify a Wine/game process tree.

### Verification

```sh
make -C host/probe
python3 -m unittest discover -s tests/host -p 'test_*.py' -v
file .build/host-probe/pear-host-probe
lipo -archs .build/host-probe/pear-host-probe
.build/host-probe/pear-host-probe > .build/host-probe/local-observations.json
python3 -m json.tool .build/host-probe/local-observations.json > /dev/null
git diff --check
```

Interpret unavailable sandbox observations honestly. A read-only rerun outside the tool sandbox may establish actual observations; it does not authorize restricted ABI transitions. Review any evidence before committing it. No meaningful hardware result is inferred from an injected fixture.

### Commit

`Task #2 Stage 1: add native host observations and diagnostic tests`

## Stage 2 — Isolated baseline tests

### Artifacts and changes

Add a dedicated child runner under `host/probe/` with explicit child ownership, bounded deadlines, exit/signal reporting and output limits. Tests must cover child success, nonzero exit, signal, timeout, malformed/missing/oversized output and cleanup. Use monotonic time and terminate only the runner's own children. Baseline low-mapping/protection tests and an ARM64 JIT leaf returning a known constant run in disposable children.

Record allocation, executable publication, instruction-cache synchronization and the returned value separately. A JIT request rejection is an observed baseline limitation, not a positive capability result. Keep restricted x18/process-page/TSO transitions out of the baseline stage.

### Concrete Stage 2 boundaries

- Add `baseline.h`, `child_runner.c`, `baseline_evaluate.c`, `baseline_child.c` and `baseline_main.c` under `host/probe/`; extend the existing Makefile with separate ARM64 baseline supervisor and child executables. Preserve the observation-only CLI.
- Use a fixed-size, versioned internal packet between same-build processes; validate identity, length, field values and probe phase before interpreting it. Public output remains bounded JSON, with no raw child stderr or private paths.
- Launch children into a dedicated process group, enforce a monotonic execution deadline and stdout/stderr limits, retain ownership until cleanup, and reap the direct child. Bound cleanup to a further one second and report any termination/reaping failure explicitly. This controls cooperative test fixtures; it is not a security sandbox for hostile programs.
- Run ordinary read/write/protection restoration, an expected protected-write fault, a non-overwriting low-address allocation attempt, and a fixed ARM64 JIT leaf returning 42. Record allocation, publication, cache synchronization, execution and cleanup separately. Do not execute downloaded or guest code.
- Keep unavailable baseline behavior distinct from failed instrumentation. Retain the normal linker layout and do not count an unavailable low mapping as a passing runtime prerequisite.
- Add `tests/host/test_baseline.py`, `runner_fixture.c` and `runner_driver.c` for real child lifecycle/failure cases. Stage 1 fixture results remain separate from real baseline results.
- Save reviewed evidence in `mydocs/working/task_m1_2_stage2_observations.json` and update the existing contributor guide. These paths remain within the approved task-plan locations.

### Verification

```sh
make -C host/probe
python3 -m unittest discover -s tests/host -p 'test_*.py' -v
lipo -archs .build/host-probe/pear-baseline-probe
lipo -archs .build/host-probe/pear-probe-child
.build/host-probe/pear-baseline-probe > .build/host-probe/local-baseline.json
python3 -m json.tool .build/host-probe/local-baseline.json > /dev/null
git diff --check
```

Extend the same unittest discovery command with real disposable child fixtures. Re-run native architecture inspection and validate the separate execution-record contract while retaining the Stage 1 observation contract inside parent observations. Inspect for leftover child processes after timeout/error tests and review all cleanup paths. `git diff --check` must pass.

### Commit

`Task #2 Stage 2: isolate baseline memory and JIT probes`

## Stage 3 — Authorized signing and process capability tests

### Artifacts and changes

Document and inspect the real available signing/provisioning path. Add narrowly scoped signed process-page and executable-memory probes only after the required authorization is verified. Compare ordinary/ad-hoc observations with authorized signed execution, with system protections enabled. Verify 4 KiB mapping, protection and decommit behavior in the actual spawned process, not by alignment or API declaration alone.

The current zero-identity observation is inconclusive about the maintainer's account. If identity/profile/capability authorization is missing, ask for the precise platform setup needed without collecting passwords or private keys. Record the gate as unavailable and continue only independent work; do not fabricate entitlements or bypass protections.

### Stage 3 preparation and independent signed control

Ordinary-host inspection on September 28 found one valid Apple Development identity and one valid Developer ID Application identity. Installed profiles include one macOS development profile but no cross-architecture grant. The earlier sandbox zero-identity result remains historical and does not describe this ordinary-host inspection. SIP and Gatekeeper report enabled.

Before restricted probes, add `host/probe/hardened_baseline.py` and `tests/host/test_hardened_baseline.py` within the approved implementation/test locations. This developer tool copies existing ARM64 baseline binaries into temporary app bundles under ignored `.build/`, selects the single available Developer ID Application identity (or an explicit local environment override), and signs two ordinary Hardened Runtime controls. The positive child's only exception is `com.apple.security.cs.allow-jit`; the negative child has no entitlement. Neither control claims cross-architecture support or embeds a profile. The supervisor also has no entitlement exception. No shipping identity, profile or generated bundle is committed.

Use the existing memory/protection/low-address/JIT trials unchanged. Verify actual signature flags and effective entitlement claims before launch. The positive JIT must return 42. The negative JIT must report explicit allocation rejection. EPERM/EACCES remain unavailable observations. The observed macOS EINVAL result is accepted only in the paired control after the same input binaries pass with allow-jit; its underlying failed status and CLI exit one remain recorded. EINVAL without that paired evidence, later-step errors and unrelated crashes remain failures. Preserve all other statuses and distinguish expected low-address unavailability from qualification. Use local signatures without a timestamp only for this non-distributed control; this does not establish notarization or end-user distribution.

If authorization remains unavailable, preserve local preparation evidence without declaring Stage 3 complete and keep the Issue open. Authorization was supplied during this stage, so the completed artifacts use `mydocs/working/task_m1_2_stage3.md` and `task_m1_2_stage3_observations.json`, within the approved report/evidence locations. Update the existing `docs/host-capabilities.md` contributor guide; no documentation relocation is required.

Commands for this independent control:

```sh
make -C host/probe
python3 -m unittest discover -s tests/host -p 'test_*.py' -v
python3 host/probe/hardened_baseline.py
# The tool performs inside-out codesign --options runtime --timestamp=none,
# codesign --verify --strict on each executable and bundle, and native trials.
git diff --check
```

The maintainer subsequently supplied a downloaded Pear profile during the same approved stage. Its CMS-decoded content is unexpired, targets macOS, grants `com.apple.developer.cross-architecture-support`, matches the explicit probe App ID and one valid Apple Development identity, and includes this Mac's Provisioning UDID. Profile preflight checks alone are not a claim of platform execution authorization; the signed launch and actual capability trials supply the next evidence.

Concrete restricted artifacts: add `process_child.c`, `process_evaluate.c`, `process_main.c`, `baseline_child_entry.c`, and `provisioned_probe.py` under `host/probe/`. Extend the shared packet IDs and runner with a typed default/4 KiB mode while preserving the original default API and packet size. Record spawn-attribute invocation/error separately from launch and child behavior; never fall back silently. Refactor the existing baseline child entry for reuse in the self-spawning executable. Build ordinary and `-Wl,-x86_64_layout_emulation,-pagezero_size,0x10000` variants. The layout control retains a protected 64 KiB null region; the emulation flag alone leaves the original 4 GiB PAGEZERO unchanged. This is a bounded low-address probe configuration, not the eventual Wine reservation policy. Add setter-failure and new packet/behavior tests under `tests/host/`; synthetic setters must not call the restricted API.

The native geometry probe records user, Mach user and kernel page sizes independently. New four-KiB children allocate three owned pages and verify independent middle-page protection with preserved neighbor sentinels. A separate ARMED child verifies the actual protected write fault. Reserved decommit/recommit uses an anonymous `MAP_FIXED` replacement restricted to the already-owned middle 4 KiB, verifies neighbors, restores RW and checks every middle byte is zero before write/read 42. A separate ARMED child verifies access to the replaced PROT_NONE page faults. An unavailable required case remains a qualification gap.

`provisioned_probe.py` revalidates the profile and device/certificate match locally, makes fresh ignored app copies, embeds the real profile, claims its actual application/team/cross-architecture grant plus public allow-jit, and signs with the matching Apple Development identity. Verify strict signatures and exact effective claims before launching. Run ordinary and 4 KiB modes for both layout variants. Require actual 4 KiB semantics and low mapping in the selected layout. Keep all profile/certificate/team/device data out of committed evidence.

Commands after setting the local-only `PEAR_PROVISIONING_PROFILE` environment variable to the supplied file:

```sh
make -C host/probe
python3 -m unittest discover -s tests/host -p 'test_*.py' -v
python3 host/probe/hardened_baseline.py
python3 host/probe/provisioned_probe.py --profile "$PEAR_PROVISIONING_PROFILE"
git diff --check
```

The restricted fixture uses the verified development profile and one provisioned app main executable with parent and self-spawned child modes, so authorization is not assumed to inherit into an unprovisioned helper. Verify child `sysconf(_SC_PAGESIZE)` and `vm_page_size` plus actual independent 4 KiB protection and reserved decommit/recommit behavior; kernel page size may remain 16 KiB. Test a distinct layout artifact for low-address needs. Foreign x18 transitions and per-thread ordering remain Stage 4.

### Verification

Record `codesign --verify --strict`, non-sensitive effective entitlement/provisioning evidence, launch outcome and the exact memory/JIT test results for the signed artifact. Keep general-user distribution separate from development-profile execution. The concrete commands and profile-dependent invocation above were added before the signed trials. The Stage 3 report records their outcomes; later stages retain their approval checkpoints.

### Commit

`Task #2 Stage 3: validate authorized process capabilities`

## Stage 4 — ABI and thread correctness

### Artifacts and changes

Implement narrow, auditable ARM64 thunks for custom x18 transitions. No normal C/POSIX/framework operation may occur while foreign mode is active. Preserve guest x18 before returning to host mode; explicitly test nesting, callbacks, asynchronous signal/error entry and all exits in disposable processes. Initialize and verify the memory-order policy for each relevant test thread.

### Verification

Use deterministic register/state fixtures and disassembly review of mode-transition windows. Distinguish a successful policy API return from observed memory-order behavior; a finite stress test does not prove universal ordering. Require the signed prerequisites from Stage 3 and retain coverage limits for later Wine/FEX integration. Re-run containment/failure tests and `git diff --check`.

### Commit

`Task #2 Stage 4: verify foreign ABI and thread transitions`

## Stage 5 — Reproduction and capability decision

### Artifacts and changes

Rebuild from documented inputs, rerun the applicable suite, redact evidence and update the contributor guide with dated outcomes. Link the historical host research to the new evidence without rewriting its original findings. Map all #2 acceptance criteria to actual results.

### Verification

Compare clean-build outcomes, schema/status correctness, architecture, relevant signatures, redaction and known gaps. Required M1 host tests must pass through the authorized path before #2 can be closed. A partial native diagnostic is useful implementation but does not satisfy the entire Issue. General-user distribution and game execution remain separately qualified.

### Commit

`Task #2 Stage 5: record reproducible host capability decision`

## Stage Dependencies and Reports

Each stage commits its source, verification evidence and report together. Stage 2 follows the reviewed Stage 1 results. Stage 3 can stop for a real platform authorization prerequisite; Stage 4 depends on Stage 3. Stage 5 cannot turn failed or unavailable required cases into passing results. The existing Issue remains open until its full acceptance criteria pass.

## Risks and Responses

- SDK symbols may exist while execution is restricted: keep presence, successful calls and behavioral evidence separate.
- Tool sandbox denials can obscure observations: preserve errno and record execution context; do not generalize to unsupported hardware.
- ABI or JIT failures can abort a child: build containment before those tests, preserve host state, and do not disable protections.
- Signature inspection may reveal personal metadata: emit category/status only; keep identity/profile handling outside public results.

## Approval Record

The maintainer explicitly approved this concrete implementation sequence and authorized Stage 1 implementation on September 27, 2026. On September 28, the explicit request to proceed authorized Stage 2 under the existing plan. Its C diagnostic and tests operate within the approved #2 task scope. Later stage reports distinguish completed code from unresolved platform and distribution gates; this approval does not authorize skipping those checkpoints.
