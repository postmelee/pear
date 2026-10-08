# Task #9 Final Report: Native runtime supervisor and Megabonk profile

GitHub Issue: [#9](https://github.com/postmelee/pear/issues/9)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Date: October 9, 2026

## Work Summary

- Target Issue: #9; six approved stages implemented, verified and reported.
- Purpose: provide a native foreground supervisor with strict shared-record admission, immutable local payload selection, owned lifecycle control, isolated profile state and preservation-first recovery.
- Result: seven native CLI operations, two executable synthetic profiles and one researched Megabonk profile with explicit unknowns. The result is verified with owned native fixtures; supported Megabonk execution remains gated.
- Integration: requester-approved merge `2864f7b` imports master `d019a6e` and preserves #6 and #9 board history. PR publication, master integration of #9 and Issue closure remain separate actions.

## Changed Files and Impact Area

| Path | Change Summary | Impact Area |
|---|---|---|
| `manager/` | Rust package reusing #3 strict parser/lifecycle, narrow Darwin C bridge, immutable activation, state and observer boundaries | Native foreground CLI and private local state |
| `runtime/contracts/v2/`, registry and oracle adapter | Explicit versioned profile/launch evolution; v1 behavior retained | Shared bounded contract consumers |
| `profiles/fixtures/`, `profiles/megabonk/` | A/B isolation fixtures and researched profile/provenance | Generic profile inputs; no game-specific manager branch |
| `tests/manager/`, `tests/profiles/`, affected contract tests | Native parity/admission, failure/crash controls, profile and CLI scenarios, exact evidence receipts | Host fixture verification |
| Five official documents; scoped rules/notices; task plans/reports/board | Usage, recovery, boundaries, provenance and approval history | Contributor guidance and review evidence |

Reuse decisions and license/source choices are recorded in the [reuse investigation](../tech/task_m1_9_reuse.md) and [implementation plan](../plans/task_m1_9_impl.md). Prerequisite #3 is merged at `1f229da`; its experiment and historical records are byte-preserved. The native implementation retains Rust and the exact libc dependency; reviewed Whisky source was not copied. No new third-party dependency or replacement hashing/parser framework was introduced.

## Document Location Verification

| File | Planned Location | Actual Location | Result | Evidence |
|---|---|---|---|---|
| CLI/setup/recovery guide | `docs/development/runtime-supervisor.md` | Same | OK | Approved task-plan location table; Stage 5 executable examples |
| Profile/provenance guide | `docs/game-profiles.md` | Same | OK | Approved task-plan location table; dual-consumer examples |
| Contracts/index/architecture links | Existing `docs/runtime-contracts.md`, `docs/README.md`, `docs/architecture.md` | Same | OK | Narrow Stage 5 changes; delivery plan unchanged |
| Machine inputs and implementation rules | `runtime/contracts/`, `profiles/`, `manager/` | Same | OK | Source trees and scoped rules created with implementation |
| Task evidence and procedure artifacts | Existing `mydocs/` subdirectories | Same | OK | Six stage reports, final report, reuse record, plans and board |

The [task plan](../plans/task_m1_9.md#document-location-judgment) records approval rationale. No product guide was placed in task manuals and no duplicate roadmap was created.

## Quantitative Before/After Comparison

| Metric | Before Task #9 | Final current result |
|---|---|---|
| Production native CLI operations | 0 (historical experiment only) | 7: inspect, evaluate, activate, prepare, launch, status, recover |
| Versioned researched Megabonk profile | 0 | 1, with current prerequisites explicitly unknown |
| A/B generic executable profiles | 0 | 2 with observed argv/settings/save isolation |
| Contract behavioral tests | 119 | 154 |
| Complete current required regression | No Task #9 suite | 517 distinct passing tests; zero required skips/failures |
| Qualified native game/distribution | None | None; explicit downstream gates remain |

These are functional coverage counts, not performance measurements. Repeated successful builds/tests are counted once by distinct test ID.

## Verification Results

Fresh final output and exact source/tool/binary/policy/mount identities are recorded in the [Stage 6 report](../working/task_m1_9_stage6.md) and [sanitized evidence](../working/task_m1_9_stage6_evidence.json). Current native execution used ARM64 macOS 26.5.2, Xcode 26.6/SDK 26.5, Apple clang 21.0.0, Rust/Cargo 1.94.1 and locked task-owned Python dependencies. All-target construction preceded behavioral tests to bind them to final probe bytes.

| Acceptance Criterion | Result |
|---|---|
| Explicit contract versions and bounded paths/operations | OK — v1/v2 schema/examples and 154 behavioral tests; native/oracle parity and unknown/version/path/policy negatives |
| Imported runtime bytes cannot self-authorize execution | OK within owned fixture scope — OS read-only admission, exact artifact/policy/media identity, descriptor-retained lookup, library closure and at-use substitution controls |
| Atomic selection and prior version preservation | OK — interrupted/failing publication, ENOSPC/EIO, concurrent activation, retained descriptor/lease and unchanged old selection controls |
| Owned lifecycle, crash reporting and privacy | OK within fixture scope — direct-child reaping, both pipe faults, cancellation, bounded output/backpressure, generation checks and unrelated sentinel survival; uncertain crash/detach stays incomplete |
| Prefix/settings/save isolation and safe recovery | OK — A/B sequential/concurrent actual fixtures preserve distinct data, reject overlap/busy/wrong identity and retain old data through fresh/clean-context recovery |
| Generic researched Megabonk profile | OK — App ID 3405340 and executable provenance represented; current unknowns remain unknown and real activation refuses without authority |
| Reproducible current evidence | OK — fresh empty locked build, 13 ARM64 binary entries, 128 source/document inputs, 55 original case IDs and all 517 distinct tests; retained per-case policy/mount/file identities |
| Documentation and preservation | OK — approved official locations, executed guide examples, governance/whitespace checks, 58 original source and 10 historical hashes unchanged |

Current test accounting: contracts 154 + manager 281 + profiles 12 + original experiment 60 + native Rust 10 = **517**. Media creation/attachment/detachment were actual host operations; synthetic observer messages do not establish real runtime coverage. Ad-hoc signature/dependency inspection is construction evidence only. No remote CI run is claimed.

The historical #3 reproduction current-input checker is ineligible after the planned contract/test expansion (`source_or_history_identity`, `unit_test_accounting`), while original bytes and historical claim scope remain preserved. Its comparison checker passes. This known historical mismatch is distinct from the passing current required gates.

### Stage Verification Results

- [Stage 1](../working/task_m1_9_stage1.md): reuse/ABI foundation, explicit v2 contracts and native strict consumption (`24084cc`).
- [Stage 2](../working/task_m1_9_stage2.md): actual read-only media, immutable entry/library admission and atomic activation (`afbb21c`).
- [Stage 3](../working/task_m1_9_stage3.md): original corpus adaptation, owned supervision, cancellation, crash refusal and bounded synthetic observer handoff (`74d9801`).
- [Stage 4](../working/task_m1_9_stage4.md): A/B state isolation, preservation and manual recovery; retained development failures and corrected Darwin cleanup identity gap (`e4183a9`).
- [Stage 5](../working/task_m1_9_stage5.md): researched profile, executable official guidance and exact early-refusal oracle correction (`95b50a7`).
- [Stage 6](../working/task_m1_9_stage6.md): approved master merge, fresh full construction, exact retained case identities and 517 current passing tests; bundled with this final report.

Earlier development failures remain preserved in their stage evidence. The first complete Stage 6 run passed, then was superseded after improving receipt completeness; the complete required gate set was rerun on the changed producer inputs. No failed or old run was relabeled as current success.

## Residual Risks and Follow-up Work

### Residual Risks

- No owned Windows Megabonk gameplay, real Steam flow, Wine/FEX runtime family, all-host-process Rosetta independence, complete save mapping or ordinary-user distribution is qualified by this task.
- The #9 socket peer is synthetic; actual process/module coverage, trusted backend readiness and shared-clock integration remain #10. A source-bound dependency must not be relabeled as observed runtime authority.
- SIGKILL can leave a live child and dirty context. Recovery refuses uncertain reuse and preserves old data; it does not promise orphan cleanup, automatic save migration or rollback.
- Cooperative locks and local read-only media are not a hostile-code sandbox. Conservative media identification can refuse during mount churn, and real runtime/package/signing authorization remains unavailable.
- Current Megabonk build/family/renderer/save-user details remain unknown and optional features untested. Developer host checks do not establish a supported OS range or distribution permission.

### Follow-up Candidates

Existing issues already cover the remaining work: #10 actual observer integration, #11 official Steam/helper flow, #12 game and save qualification and #13 runtime/package authority. #8 retains its independently reported CPU alignment integration gap. No new follow-up Issue is created, and this report does not close those dependencies or borrow their component results as game proof.

## Approval Request to Task Requester

Please approve this final report and the concrete PR body before publishing `codex/task9` as `codex/publish-task9` for an Open PR to `master`. All six approved stages and current checks are complete. Publication approval does not itself authorize self-merge or Issue closure.
