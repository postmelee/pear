# Task #2 — Host capability implementation plan

Task plan: [task_m1_2.md](task_m1_2.md)
GitHub Issue: [#2](https://github.com/postmelee/pear/issues/2)
Milestone: M1

Status: implementation plan and Stage 1 explicitly approved by the maintainer on September 27, 2026. Later stages retain their own report checkpoints.

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

### Verification

Extend the same unittest discovery command with real disposable child fixtures. Re-run native architecture inspection and validate per-child records against the Stage 1 status contract. Inspect for leftover child processes after timeout/error tests and review all cleanup paths. `git diff --check` must pass.

### Commit

`Task #2 Stage 2: isolate baseline memory and JIT probes`

## Stage 3 — Authorized signing and process capability tests

### Artifacts and changes

Document and inspect the real available signing/provisioning path. Add narrowly scoped signed process-page and executable-memory probes only after the required authorization is verified. Compare ordinary/ad-hoc observations with authorized signed execution, with system protections enabled. Verify 4 KiB mapping, protection and decommit behavior in the actual spawned process, not by alignment or API declaration alone.

The current zero-identity observation is inconclusive about the maintainer's account. If identity/profile/capability authorization is missing, ask for the precise platform setup needed without collecting passwords or private keys. Record the gate as unavailable and continue only independent work; do not fabricate entitlements or bypass protections.

### Verification

Record `codesign --verify --strict`, non-sensitive effective entitlement/provisioning evidence, launch outcome and the exact memory/JIT test results for the signed artifact. Keep general-user distribution separate from development-profile execution. The exact commands and profile-dependent fixture invocation must be added to this plan when the authorization path is known, before the signed tests run.

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

The maintainer explicitly approved this concrete implementation sequence and authorized Stage 1 implementation. Its C diagnostic and tests operate within the approved #2 task scope. Later stage reports distinguish completed code from unresolved platform and distribution gates; this approval does not authorize skipping those checkpoints.
