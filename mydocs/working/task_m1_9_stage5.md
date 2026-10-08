# Task #9 Stage 5: Document CLI recovery and researched Megabonk profile

GitHub Issue: [#9](https://github.com/postmelee/pear/issues/9)
Implementation plan: [task_m1_9_impl.md](../plans/task_m1_9_impl.md)
Stage: 5
Date: October 9, 2026
Status: Implemented and verified; Stage 6 awaits explicit continuation.

## Stage Purpose

Deliver a versioned researched Megabonk profile with honest current unknowns, official native CLI/setup/recovery guidance and executable documentation checks. The requester explicitly approved this stage with “진행해줘” after Stage 4 report and commit `e4183a9`. The approval covers the existing document-location judgment, implementation, verification, report and bundled commit; it does not authorize Stage 6 or publication.

Context used: root, docs, profiles, manager, runtime, host and tests rules; README, official index, architecture, delivery plan, runtime contracts and relevant local/graphics evidence; current Issue #9, approved task/implementation plans, latest Stage 4 report and reuse record; existing task/Git workflow and conflict/location rules; task-stage-report, todo and central report/board templates. Current read-only checks found master `d019a6e`, Task #8 `2c709b1` and the separate Task #10 planning commit `bbbe357`. The #10 plan explicitly identifies the #9 synthetic transport's lifecycle/clock/coverage limitations and separate integration decision. No other worktree or branch was changed or integrated. Work remains on `codex/task9` from `e4183a9`.

## Artifacts

| File/group | Change Summary |
|---|---|
| `profiles/megabonk/profile.json` | Closed v2 research profile, official store identity, historically observed executable, revision-pinned provenance, explicit unknown runtime/build/save facts and untested features |
| `docs/game-profiles.md` | Profile knowledge/evidence semantics, writable-state boundaries, dated Megabonk facts, dual-consumer inspection and execution refusal |
| `docs/development/runtime-supervisor.md` | Build prerequisites, owned read-only fixture setup, eight native command examples, complete Python socket handoff, A/B persistence, cancellation, status, manual recovery, return values and #9/#10 boundaries |
| `docs/README.md`, `docs/architecture.md`, `docs/runtime-contracts.md` | Narrow links and implemented v2/native-fixture guidance; existing normative qualification/ownership requirements retained |
| `tests/profiles/test_megabonk.py` | Seven tests for actual profile inspection, documented commands, honest unknowns, native/oracle refusals, missing authority and bounded private diagnostics |
| `tests/manager/test_cli.py` | Five tests executing guide code/commands, A/B state preservation, both cancellation signals, readiness refusal, fresh/clean-context recovery and malformed CLI diagnostics |
| [Sanitized evidence](task_m1_9_stage5_evidence.json), reuse record, implementation plan and daily board | Current inputs/results, prior failure, unchanged-build reuse boundary and next-stage checkpoint |

## Body Change Scope / Lossless Preservation

All product documentation paths match the previously approved task-plan location judgment. Existing content was read before narrow edits. The delivery plan remains unchanged as the single roadmap. New public guides live under `docs/`; stage/approval/reuse artifacts remain under `mydocs/`. The native manager, C fixtures, adapters, v1/v2 schema/oracle implementations, dependency manifests/lockfiles, original experiment sources/corpus/history and earlier reports remain unchanged.

The profile identifies Steam App ID 3405340 and `Megabonk.exe`. Its current `game_build`, compatibility family and renderer remain null. Argument, environment, operation and save-path arrays remain empty; save inventory and structured settings/save locations remain explicitly unknown. Historical game 1.0.69, depot 3405342/manifest 446680890915713051, Rosetta-based runtime versions and candidate script arguments/configuration location are scoped provenance, not native defaults. Required game/Steam process labels are requirements rather than a claim of complete helper discovery. Gameplay, runtime architecture, Steam, input/audio, save/relaunch and optional features remain untested for this profile.

Primary Steam listing and Steamworks initialization documentation were reviewed on October 9. Store feature labels are not Pear verification; normal official Steam context and ownership remain required. Revision-pinned repository citations preserve the exact dated local evidence and sanitized script-hint source. No game executable, account, authenticated prefix, private script contents or personal saves were read or imported.

The CLI guide documents actual command/result differences, including native evaluation returning zero with `eligible: false`, status returning zero with `context_incomplete`, launch-specific syntax failures mapping to invalid-contract status, and native errors remaining visible after a narrowly verified cleanup exception. It distinguishes explicit clean-context selection from a global active pointer, preserves old runtime media identity, and states that fresh recovery does not copy/restore/migrate saves. Fixture lifetime/output bounds, synthetic single-main scope, unestablished real clock mapping and absence of a persisted public event bundle are explicit. #10 receives no new authority or protocol semantics.

## Verification Results

Execution context: the existing native ARM64 Stage 4 build on macOS 26.5.2 (25F84), built with Xcode 26.6 (17F113), SDK 26.5, Apple clang 21.0.0 and Rust/Cargo 1.94.1, minimum build target 26.0. These are recorded construction inputs, not a newly repeated build or end-user support requirements. Current tests used the task-owned Python environment, actual owned native fixture children, read-only UDRO media and synthetic sockets. No Wine, Steam, Megabonk or Raft process was executed.

All approved Stage 5 commands passed on the final input bytes:

```sh
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/profiles -p 'test_*.py'
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_cli.py
python3 -B tools/check_governance.py
git diff --check
```

| Verification | Actual final result and scope |
|---|---|
| Profile suite | 12 pass: seven new research/inspection/refusal tests and five existing A/B behavior tests |
| CLI suite | Five pass, including SIGINT and SIGTERM subcases; no failures or skips |
| Document commands | All eight marked command examples executed as argv arrays; both profile-guide inspection commands and the complete Python media/socket examples executed |
| A/B state | Actual distinct arguments, settings and persistent save bytes survived relaunch; other-profile inventories remained unchanged. Concurrent child start times differed by 5,992 microseconds with each successful fixture living at least 500 ms. |
| Recovery/cancellation | Readiness failure spawned no child and left incomplete state; old-context reuse refused. Fresh recovery preserved old inventories without copying saves. Cancellation reaped the actual owned child, completed bounded cleanup/observation and preserved the unrelated sentinel. |
| Native/oracle refusal | Researched request refused on unknown/incompatible family before activation mutation. A separate complete synthetic runtime candidate passed declaration-only evaluation but actual activation returned `runtime_authorization_unavailable`, with empty state preserved. |
| Source/binary reuse | All 120 recorded Stage 4 source hashes and all 13 binary hashes matched before final execution. Eight new/updated documentation/profile/test inputs give 128 bound Stage 5 inputs. |
| Public documentation/privacy | Six public artifacts excluded private-home/temp paths and synthetic secret markers. CLI diagnostics were bounded and did not echo injected secrets or owned private state paths. |
| Links/governance/format | 12 new-guide local links, including heading anchors, resolved; offline governance passed for 27 documents/253 local targets; whitespace check passed. |

There are **17 distinct current passing tests**, zero final failures and zero skips. Earlier exploratory successful runs are not counted again. Stage 4's 505 tests are prior evidence, not tests rerun by this stage.

Evidence reuse: manager/fixture source and build configuration were not changed, so the unchanged Stage 4 executables were reused for their existing fixture scope after exact source/binary checks. New Stage 5 profile/documentation/test files receive independent hashes; current runtime/state images and result collections are recorded separately. No fresh native compilation, whole-runtime reconstruction, qualification or signing result is claimed. Stage 6 retains the approved fresh-construction checks. The original experiment and historical records were not edited, and earlier Stage 4 failures/limitations remain preserved.

One initial test failed because it expected a later activation refusal (`ineligible`, exit 3); the actual native consumer rejected unresolved profile/request family earlier (`incompatible_family`, exit 1). The test now requires that precise earlier refusal and independent oracle agreement, retaining the empty-state assertion. Native implementation was unchanged. The initial failed log remains in ignored Task #9 evidence. Review also caught the native absolute-root requirement and an incorrect dependency-guide heading link; corrected profile command examples and all local anchors passed final execution/checks. No failed run was relabeled as passing.

Final suite logs, unchanged build receipt, current source/binary hashes, command outcomes, runtime-image preservation digests and failure references are recorded in the sanitized evidence. Raw tool logs remain in ignored `.build/task9/` through review/integration. Legacy `stage3-` run labels come from the unchanged adapter, while actual receipts and new input hashes establish this run's scope. Owned media were detached and disposable fixture state removed after each suite.

## Residual Risks

- The research profile does not establish current installed game/Steam identity, a complete save inventory/user mapping or supported native settings. Those inputs remain explicit unknowns.
- Actual Wine/Steam/helper/module observation, runtime authorization, game qualification and ordinary-user distribution are unperformed here. Synthetic observation cannot fill those gaps.
- Exact context compatibility, finite fixture timeouts, conservative media refusal, cooperative lease limits and preservation-first recovery remain as documented in Stage 4. Automatic save migration/rollback and availability during concurrent image churn are unqualified.
- Fresh construction and the complete integrated regression set remain Stage 6. No PR, Issue closure or integration has occurred.

## Impact on Next Stage

Stage 6 must inspect then-current master, Task #8/#10 and relevant completed reports before any separately approved integration; preserve concurrent docs/board changes. Build current manager/fixtures in a new empty task-owned output and execute every approved final command, including the newly added documentation/profile tests. Keep original history, retained failures and unavailable runtime/game/distribution scope explicit. Final report/publication approval remains a separate checkpoint after verified work.

## Approval Request

Please review the Stage 5 artifacts and verification results and approve entering Stage 6: fresh fixture reconstruction, complete integrated checks and final handoff report.
