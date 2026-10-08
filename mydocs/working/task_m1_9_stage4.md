# Task #9 Stage 4: Isolate fixture profiles and preserve recovery data

GitHub Issue: [#9](https://github.com/postmelee/pear/issues/9)
Implementation plan: [task_m1_9_impl.md](../plans/task_m1_9_impl.md)
Stage: 4
Date: October 9, 2026
Status: Implemented and verified; Stage 5 awaits explicit continuation.

## Stage Purpose

Implement prepared, identity-bound mutable contexts, typed fixture settings, explicit preservation-first recovery and two independently persistent fixture profiles. The requester explicitly approved Stage 4 with “진행해줘” after the Stage 3 report and commit. This scope includes implementation, verification, reporting and one bundled commit.

Context used: root, manager, runtime, host and tests rules; README, official documentation index, architecture, delivery plan and runtime contracts; Issue #9, approved task and implementation plans, review supplements, latest Stage 3 report and reuse investigation; task/Git workflow, document-location rules, task-stage-report and repository todo skills. The new profiles rules follow the approved location. Open Issues and active worktrees were inspected: master remains `d019a6e`; separate Task #8 is at `2c709b1`, with synthetic translated-rendering evidence and an unresolved CPU alignment case. No Task #8 game qualification or integration is assumed. This work remains on `codex/task9`, based on Stage 3 commit `74d9801`; other worktrees were not modified.

## Artifacts

| File/group | Change Summary |
|---|---|
| `manager/src/state.rs`, `profile.rs` | Prepared context metadata, immutable selection snapshots, canonical leases, typed settings, cache identity checks and explicit recovery |
| `manager/src/main.rs`, `launch.rs`, `lib.rs`, `fs.rs` | Closed prepare/status/recover CLI dispatch, prepared-context launch, held mutable-root descriptors and hard-link refusal |
| `manager/src/supervisor.rs`, `supervisor_tests.rs` | At-use context validation before spawn; bounded retry of existing native ownership proofs during a transient exit-visibility gap; unchanged pipe-fault assertions with additional failure diagnostics |
| `manager/examples/state_probe.rs` | Test-only publication/settings fault and synchronization hooks |
| `profiles/AGENTS.md`, `profiles/fixtures/a.json`, `b.json` | Scoped profile rules and two generic v2 profiles with different App IDs, arguments, settings and save paths |
| `tests/manager/fixtures/state.c`, `supervision_entry.c` | Finite owned native state companion, independent strict identity trace and distinguishable runtime variants |
| `tests/manager/state_support.py`, `test_state.py`, `tests/profiles/test_profiles.py` | Preparation/recovery fault controls, actual persistence and simultaneous execution, independent preservation inventories |
| `tests/manager/build.py`, `case_adapter.py`, `synthetic_peer.py`, `test_supervision.py` | Locked build receipts, original adapter reuse, prepared contexts and bounded synthetic readiness barrier |
| [Sanitized evidence](task_m1_9_stage4_evidence.json), reuse record, implementation plan and daily board | Exact source/binary inputs, retained failures, passing results and next-stage checkpoint |

## Body Change Scope / Lossless Preservation

Artifact locations match the approved Stage 4 plan. No official product documentation, original experiment source/corpus/history, v1/v2 schemas, dependency manifests/lockfiles or original strict-parser bytes changed. Exact `libc = 0.2.186` remains the only dependency. The existing Rust manager, C fixture and native bridge are reused; the [reuse record](../tech/task_m1_9_reuse.md) records the decision. No manager branch dispatches on an App ID.

Private context metadata binds the lower-case caller-selected game/library context ID to runtime family, store/App ID, exact profile digest, complete cache identity and declared mutable roots. Each context snapshots its admitted selection. Compatibility is deliberately exact: a family match alone does not permit reuse with another profile, request or cache identity. Launch reads the context snapshot, allowing an explicitly selected older clean runtime context after another runtime has been activated.

Preparation serializes through the contexts-directory lease. Context and prefix leases retain exclusive descriptors and device/inode identities through mutation or supervision. Metadata records root and lease identities; admission and at-use validation reject replacements, aliases, overlaps, hard links, unavailable cache identity and incompatible bindings. A final validation follows synthetic observer readiness and precedes spawn. A free lease never overrides a dirty journal or proves that an earlier run finished; recorded PIDs are never signaled for recovery.

New contexts are privately staged, settings and metadata are synced, and publication uses an exclusive rename followed by parent sync. Interrupted staging remains unselected; existing contexts are not overwritten. Reapplying settings to an existing compatible context publishes a running journal before mutation and a clean journal only afterward. An interruption leaves incomplete state. The only executable v2 operation is a boolean `fixture_flag` at `prefix/config/options.json`; unrelated JSON keys survive. Unsupported keys, paths and duplicate/conflicting operations refuse. Nonempty v1 operations still refuse. Known complete fixture save mappings are required for v2 preparation; the manager does not write save contents.

`status` distinguishes prepared, clean and incomplete state. `recover --new-context` creates fresh state while preserving previous data; `recover --context-id` verifies an explicitly named clean compatible context, subsequently used by `launch --context-id`. It does not rewrite a global active-context pointer. Neither path copies, restores, migrates or deletes saves. The runtime and five mutable root descriptors remain held through execution; only the owned fixture companion consumes the explicit fixture descriptor environment.

Required regression testing exposed a transient Darwin exit-visibility gap in the inherited supervisor path: process identity could be unavailable before the reserved child's WNOWAIT exit became visible. The correction retries the existing identity-match or reserved-exit proof, and the existing narrow EPERM proof, at two-millisecond intervals for at most 250 ms within the original two-second cleanup budget. It neither broadens ownership nor signals a persisted PID. Numeric native errors remain available. The original two pipe-fault safety assertions remain intact; additional diagnostics explain failures without changing their acceptance conditions.

## Verification Results

Execution context: native ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5, Apple clang 21.0.0, Rust/Cargo 1.94.1, minimum build target 26.0. Cargo uses locked/offline inputs. The final build receipt binds 120 source inputs and current binary hashes. All final suites use those unchanged inputs. Owned native fixtures execute from read-only UDRO payloads with a synthetic observer. These are correctness tests, not game execution or performance measurements.

All approved Stage 4 commands passed:

```sh
python3 -B tests/manager/build.py --output .build/task9/stage4 --locked
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_state.py
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/profiles -p 'test_*.py'
git diff --check
```

| Verification | Final result and claim scope |
|---|---|
| State | 29 pass: binding, status, dirty/busy refusal, lease/root replacement, aliases, cache identity, family, save mapping, settings, real SIGKILL and injected EIO publication interruption, fresh recovery and previous-context selection |
| Profiles | 5 pass: sequential relaunch/persistence, simultaneous A/B execution, precise setting edits, changed-setting refusal and preservation of unrelated preexisting saves |
| Supervision | 61 pass, including all 55 original mapped IDs; supported v2 fixture settings now prepare and launch successfully while unsupported v1 operations still refuse |
| Observer / crash | 23 / 2 pass on the current manager and prepared-context path |
| Admission / activation / foundation | 133 / 16 / 12 pass; immutable admission, actual fixture activation and native foundation remain verified |
| Contracts / original experiment | 154 / 60 pass; original source/corpus assertions retained |
| Native Rust | 10 pass, zero ignored, including both original pipe-fault positions and denied/ambiguous cleanup controls |
| Additional race repetitions | Each original pipe-fault test passed 30 further repetitions; these 60 executions are not added to the distinct test count |
| Governance / whitespace | Offline governance and `git diff --check` pass |

There are 505 distinct final passing tests and no final failures or skips. Additional regression commands were:

```sh
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_supervision.py
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_observer.py
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_crash.py
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_admission.py
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_activation.py
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_foundation.py
.build/task9/venv/bin/python -B -m unittest discover -s tests/contracts -p 'test_*.py'
python3 -B -m unittest discover -s experiments/manager -p 'test_*.py'
python3 -B tools/check_governance.py
```

A/B actual child observations contain different arguments, boolean settings and save markers, and relaunches read previous saves. In the final concurrent case the recorded process-generation start times differ by 10,089 microseconds; both successful children execute the fixture's 500 ms delay, establishing overlap. Recovery tests execute distinguishable runtime variant 2 and then the previous clean variant 1 with its save preserved. Independent inventory/image hashes confirm unchanged old contexts, other-profile state, preexisting saves and runtime payloads. Unknown setting keys survive the permitted setting edit. A mismatching preexisting save causes fixture exit 75 without overwriting it.

Evidence reuse: the original 58 source inputs and ten historical records remain byte-identical, but changed manager/fixture inputs required current execution of all affected suites. Historical results are retained only for their original claim scope. The old reproduction report's current-tree checker still reports `source_or_history_identity` and `unit_test_accounting` after Stage 1 added contract inputs/tests; comparison consistency passes. This known historical mismatch is explicitly recorded and is not counted as a passing current gate. The sanitized evidence binds final logs, source/binary identities, native test names, preservation digests and retained failures. Legacy local run-directory labels containing `stage3-` are adapter naming only; the actual receipt and inputs identify Stage 4.

Development failures were retained rather than reclassified as successes:

- Initial refactoring left an out-of-scope request variable; compilation was corrected before executable verification.
- Six initial state and three profile assertions failed because an expanded observation record was supplied to the unchanged strict five-field identity helper. The companion now emits a separate original-shape identity record; the helper remains unchanged.
- Native pipe-fault runs exposed the identity/exit gap described above. An EPERM-only recheck was insufficient. Retained diagnostics show the owned group and observed generation, failed instantaneous identity proof, exit not yet visible and successful signal. The bounded proof retry passed the required native suite and both 30-run repetitions.
- One profile preparation refused `unidentified_media` while other suites attached/detached owned images. Its exact cause was not independently established. The failed log and evidence remain retained. The final profile suite passed with image lifecycle activity isolated, while its A/B children still ran simultaneously. No automatic retry or writable execution fallback was added; availability during concurrent image churn remains unqualified.

Raw logs and receipts remain under ignored `.build/task9/` through review/integration. Three owned failed-native-test scratch roots had their traces copied into retained evidence before removal. Successful media were detached and disposable test state removed. No real Wine/FEX/Steam/Megabonk, real observer authority, signing/provisioning or distribution verification was performed.

## Residual Risks

- Cooperative inode leases and metadata checks do not constrain a hostile same-user writer or administrator.
- SIGKILL and injected EIO test observed interruption behavior; power-loss durability is unproven. Unselected staging debris is preserved rather than automatically removed.
- Exact compatibility is conservative. Recovery provides fresh state or explicit clean-context reuse; automatic upgrade, migration, save restoration and copying remain unimplemented.
- Settings and save mappings are fixture-scoped. Successful native fixture execution supplies no real-runtime, game or ordinary-user distribution qualification.
- Read-only media discovery can refuse when identity is unavailable. Concurrent mount-lifecycle availability is not qualified by the isolated final suite.
- Synthetic observation does not establish real descendant/module coverage. The existing abrupt-death and detached-helper limitations remain.

## Impact on Next Stage

Stage 5 can document the verified prepare/activate/launch/status/recover behavior and record the researched Megabonk profile with explicit unknowns. Read existing official documentation and follow approved `docs/` locations. Inherit the exact-compatibility restriction, explicit context selection, preservation-first recovery, synthetic observer boundary and real-runtime refusal. Do not turn historical or fixture evidence into supported gameplay claims. Stage 5 has not started and requires explicit requester continuation.

## Approval Request

Please review the Stage 4 artifacts and verification results and approve entering Stage 5: the researched Megabonk profile and official CLI/recovery guidance.
