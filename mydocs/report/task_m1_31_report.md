# Task #31: Build timing analysis and targeted Ninja diagnostics — Final Report

GitHub Issue: [#31](https://github.com/postmelee/pear/issues/31)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Date: October 4, 2026 (Asia/Seoul).

## Work Summary

- Target Issue: #31.
- Stage count: 3, each verified and committed after the applicable approval.
- Purpose: make existing build timing evidence and targeted Ninja diagnosis reusable without changing active build recipes or qualification requirements.
- Outcome: a source-pinned timing analysis, minimal measurement projection and official contributor guide. Existing ARM64 Ninja 1.13.1 remains the selected tool; no replacement dependency was introduced.

Two retained Task #7 construction invocations spent 85.34% and 86.62% of their
wrapper duration outside the ten monitored command spans. This identifies an
unmeasured region for later investigation, not a measured hashing bottleneck,
removable verification cost or speedup. The guide explains targeted commands,
query and dry-run diagnosis, timing boundaries and build-log limitations.

## Changed Files and Impact Area

| Path | Change Summary | Impact Area |
|---|---|---|
| docs/development/build-diagnostics.md | Pinned Ninja behavior, timing attribution and safe diagnostic ownership | Contributor guidance |
| docs/README.md | One navigation entry | Documentation discovery |
| mydocs/tech/20261004_build_timing_analysis.md | Dated measurements, source identities and limits | Research evidence |
| mydocs/tech/20261004_build_timing_analysis.json | Two runs and 20 selected command rows, no raw private logs | Minimal evidence projection |
| mydocs/plans/task_m1_31.md | Approved scope, reuse/location decisions and approval history | Task plan |
| mydocs/plans/task_m1_31_impl.md | Three-stage implementation and verification contract | Implementation plan |
| mydocs/working/task_m1_31_stage1.md | Source/timing/privacy verification | Stage 1 report |
| mydocs/working/task_m1_31_stage2.md | Pinned Ninja source review and guide verification | Stage 2 report |
| mydocs/working/task_m1_31_stage3.md | Final consistency, source availability and scope review | Stage 3 report |
| mydocs/orders/20261004.md | #31 completion record | Daily board |
| mydocs/report/task_m1_31_report.md | Acceptance results and remaining risks | Final report |

No host, runtime, tool, validator, test, CI, agent-rule, skill or template file
changed. Other workers' branches and outputs were not modified.

## Document Location Verification

The actual locations match the approved [task plan](../plans/task_m1_31.md)
and [implementation plan](../plans/task_m1_31_impl.md).

| File | Planned Location | Actual Location | Result | Evidence |
|---|---|---|---|---|
| build-diagnostics.md | docs/development/ | docs/development/ | OK | Approved contributor-guide destination |
| README.md navigation entry | docs/ | docs/ | OK | Exactly one added line |
| Dated analysis and JSON | mydocs/tech/ | mydocs/tech/ | OK | Research evidence remains separate from product support claims |
| Plans / stage reports / final report | mydocs/plans/, mydocs/working/, mydocs/report/ | Same | OK | Existing workflow destinations retained |

## Quantitative Before/After Comparison

| Metric | Before | After |
|---|---|---|
| Dedicated build-diagnostics guide | Absent | One guide, one index link |
| Public minimal timing projection for the selected pair | Absent | Two runs, 20 command rows |
| Added build or runtime executions in this task | 0 | 0 |
| Performance improvement established by this task | None | None; no benchmark or implementation change |

| Retained run | Wrapper ms | Command sum ms | Unattributed remainder ms | Remainder percent |
|---|---:|---:|---:|---:|
| small_stub_reference | 902376 | 132326 | 770050 | 85.34 |
| small_stub_candidate | 893511 | 119568 | 773943 | 86.62 |

The command spans include supervision overhead. The remainder covers several
unmeasured regions; it cannot be assigned to hashing alone. These two runs are
not a controlled before/after benchmark. Fresh output directories do not imply
cold caches. See the [analysis](../tech/20261004_build_timing_analysis.md).

## Verification Results

| Acceptance Criterion | Result |
|---|---|
| Preserve existing tool use and reuse decisions | OK — #5/#7 sources reviewed; retain Ninja 1.13.1, generators and existing receipts |
| Retain auditable timing attribution | OK — selected original receipts and pinned observations checked; Decimal arithmetic reproduces both remainders |
| Avoid publishing private payloads | OK — JSON allowlist and document review exclude private paths, raw argv/environment, credentials and game material |
| Provide source-grounded targeted diagnostics | OK — six pinned Ninja source files reviewed; global/tool ordering, dry-run side effects and log limitations documented |
| Preserve final verification requirements | OK — diagnostic work cannot replace clean reconstruction, provenance or applicable host/game qualification |
| Verify documentation and scope | OK — offline governance passes (23 documents, 175 local targets); whitespace, links, syntax-only shell checks and complete diff review pass |
| Confirm cited Pear sources remain accessible | OK — eight remote files at immutable commits return blob IDs matching local objects |
| Keep parallel work independent | OK — isolated task branch; no messages, integration, CI implementation or shared build changes |

Integrated verification reran `python3 -B tools/check_governance.py` and
`git diff --check` and inspected names, statistics and status against base
`d35428f037a91b5db1a22fb0b065d6d13132ccb7`. The final reporting change adds the
eleventh approved file and updates only the task plans and daily board; the guide
and timing projection remain unchanged from their completed stages.

### Stage Verification Results

- [Stage 1](../working/task_m1_31_stage1.md), commit 7de87b9: receipt identities, selected-field projection, timer boundaries, arithmetic and privacy review.
- [Stage 2](../working/task_m1_31_stage2.md), commit 0d10f6d: Ninja source inspection, guide/index review and syntax-only example checks.
- [Stage 3](../working/task_m1_31_stage3.md), commit 9b6f27e: cross-document consistency, complete scope audit and eight-file remote identity checks.

### Verification Boundaries

No Ninja command, compiler, new build, full provenance replay, native/game test or
benchmark was run by this task. Shell syntax checking does not execute examples.
Private original evidence is not a public replay package; the historical whole
working-copy snapshot remains unavailable as detailed in Stage 1. Remote source
identity checking does not remove those limits. PR-triggered CI and publication
status are recorded in the PR after publication; this pre-publication report does
not claim those operations have occurred.

## Residual Risks and Follow-up Work

### Residual Risks

- Two uncontrolled runs do not establish typical build performance or individual phase costs.
- Ninja dry-run is not a filesystem sandbox. Use an owned, inactive mutable diagnostic tree and respect absolute-path aliases; do not mutate immutable qualification evidence.
- Same-date daily boards may overlap another branch. Any later integration must preserve other rows; this task does not integrate other work.
- This documentation does not establish Rosetta-free game execution or ordinary-user distribution support.

### Follow-up Candidates

- If separately approved, instrument unmeasured construction regions in the owning build task before choosing an optimization; retain all correctness checks.
- After the requester reassesses active tasks, share the guide and recommend integration at an appropriate boundary. No messages or integration advice have been sent by this task.
- No new follow-up Issue was created, and no CI work was added to #14.

## Approval Request to Task Requester

The requester explicitly approved final reporting and PR publication after the
Stage 3 report. Publish a non-draft PR from codex/publish-task31 to master using
this report and immutable document links. Review and merge remain separate
requester decisions. Do not merge, close #31 or send other-task messages under
this publication approval.
