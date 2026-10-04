# Task #31 implementation plan: Build timing analysis and Ninja diagnostics

Task plan: [task_m1_31.md](task_m1_31.md)
GitHub Issue: [#31](https://github.com/postmelee/pear/issues/31)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Status: Stages 1-3 and final reporting complete; publication approved; merge pending.
Date: October 4, 2026 (Asia/Seoul).

The requester approved the task plan and document locations by explicit
continuation after reviewing the planning commit 6bc7fd2. Keep its scope,
exclusions, source pins, reuse rationale and evidence boundaries unchanged.
Follow the [root rules](../../AGENTS.md), [documentation rules](../../docs/AGENTS.md)
and [task workflow](../manual/task_workflow_guide.md). At implementation planning
there was no stage report; performed results are now recorded in the linked
stage reports below. The stage definitions remain the approved intended work.

## Stage Overview

| Stage | Title | Main output | Verification |
|---|---|---|---|
| 1 | Preserve and attribute retained timing evidence | Dated analysis and minimal JSON projection | Source identity, timing boundaries, arithmetic and privacy review |
| 2 | Write targeted build diagnostic guidance | Official guide and one index entry | Pinned Ninja source inspection and manual example review |
| 3 | Verify documentation and scope | Reviewed documents and stage report | Cross-document consistency, links, offline governance and diff checks |

## Document Location Check

| File | Planned location | Stage artifact path | Match | Notes |
|---|---|---|---|---|
| Analysis | mydocs/tech/ | mydocs/tech/20261004_build_timing_analysis.md | OK | Dated observations, not runtime qualification |
| Timing projection | mydocs/tech/ | mydocs/tech/20261004_build_timing_analysis.json | OK | Allowlisted facts; no new runtime schema contract |
| Diagnostic guide | docs/development/ | docs/development/build-diagnostics.md | OK | Reusable contributor guidance |
| Navigation | docs/ | docs/README.md | OK | One link, preserve other entries |
| Stage reports | mydocs/working/ | task_m1_31_stage1.md through task_m1_31_stage3.md | OK | Stage verification and limitations |
| Final report | mydocs/report/ | task_m1_31_report.md | OK | Prepared under the later final-report approval gate |

## Stage 1 - Preserve and attribute retained timing evidence

### Artifacts

New: the dated analysis and JSON projection above, plus
mydocs/working/task_m1_31_stage1.md. Update only #31's daily-board row and plan
status as needed. No official guide or build/validator changes in this stage.

### Changes

- Read the #7 observations at commit e41b7bd7daaab707c3609693ff11e14af6f2d085,
  its two referenced build records and the already inspected local build7/build8
  wrapper receipts. Recheck their digests against the approved task plan. Read
  the original wrapper and constructor to establish exactly what each timer spans.
- Keep the original two-run observation cohort. If current #7 files advance,
  prefer the pinned Git snapshot; never silently replace the cohort with a newer
  run or rewrite other workers' records. Report unavailable originals explicitly.
- Retain only source commit/file digests, non-sensitive run labels, wrapper
  phase/exit_code/elapsed_ms, the ten command id/elapsed_ms/exit_code/stop_reason
  entries, and derived timing totals. Identify local operator receipts separately
  from build provenance records. Do not retain raw paths, argv, environments,
  file inventories or private diagnostics. Use a data-format version only for
  this analysis projection, not a new validator/qualification schema.
- Compute command sum, remainder, compile subset and remainder percentage. Keep
  integer milliseconds authoritative; calculate display percentages from them.
- Explain that the wrapper starts after the shared lock is obtained and excludes
  the subsequent independent comparator/native qualification. Command timers can
  themselves include child work and monitoring. Do not add nested command times
  twice or treat summed parallel edge durations as wall time.
- Identify source preparation, input/provenance verification, generated inputs,
  copying/inventory work and final verification as candidate unmeasured regions
  based on inspected code. The remainder does not establish their individual costs
  or justify skipping any check. Preserve fresh-build versus cold-cache limits.
- Link exact inspected #5/#7 source commits where publicly available. Reuse
  existing records and Python standard-library arithmetic; no new profiler,
  aggregation tool or upstream source copy is introduced.

### Verification

Inputs: the pinned observations and bounded local JSON/source files above.
Tools: Python 3.14.4 observed in this checkout, Git, existing offline checker.
This is arithmetic and source inspection; it does not require reproducing the
original build host/toolchain. No compiler, Ninja build, replay or game is run.

1. Independently load source bytes, hash them before parsing and compare receipt
   references. Cross-check the two ten-command sequences with their build records
   if those originals remain available. Retain precise gaps if they do not.
2. Validate the projection against the allowed fields and source values. Recompute
   sums and percentages; compare every value printed in the Markdown table.
3. Manually inspect wrapper timer/lock order and serial command boundaries.
4. Check both new files for private paths, credentials, raw logs and overclaims.
5. Run the existing governance checker and whitespace checks. Because its scan
   scope is limited, also inspect local Markdown targets in newly added files.

```sh
python3 -B tools/check_governance.py
git diff --check
```

Expected result: 902376/893511 ms wrapper spans, 132326/119568 ms command sums,
770050/773943 ms remainders and 85.34/86.62 percent after rounding, if the source
identities remain the recorded ones. A mismatch requires investigation, not
editing the expected values to make the check pass. Retain performed commands,
source digests, check results and limitations in the stage report. Do not expose
private source locations in public reports.

### Commit

`Task #31 Stage 1: preserve existing build timing evidence and limits`

## Stage 2 - Write targeted build diagnostic guidance

### Artifacts

New: docs/development/build-diagnostics.md and
mydocs/working/task_m1_31_stage2.md. Modify docs/README.md with one navigation
entry. Update #31 task status as appropriate.

### Changes

- Begin with whole-invocation versus command timing, then choose diagnostics for
  the region actually implicated. Point to the dated analysis without presenting
  its two observations as a permanent Pear performance characteristic.
- Provide a short symptom/action table: unexpected rebuilds, slow individual
  compiles/links, dependency ordering and time outside compiler commands.
- Inspect the official Ninja source at commit
  79feac0f3e3bc9da9effc586cd5fea41e7550051 (1.13.1) for -n -d explain,
  -t query, -t commands and .ninja_log semantics. Cite immutable source paths
  and review date. Keep CMake/Meson responsible for generated build definitions.
- Clarify that -t commands prints commands rather than executing them. Audit
  startup/regeneration/log behavior before describing a command as read-only;
  examples are for an owning task's approved, inactive build tree, not another
  worker's active or immutable evidence root. No example is run in this task.
- Explain log start/end timing, overlapping work and repeated invocations;
  do not infer a critical path or achieved parallel speedup from a simple sum.
- Include selection of the already pinned Ninja executable and properly quoted
  paths/targets. Mark placeholders clearly. Preserve bounds and existing job
  policies; no hard-coded job increase, clean/delete step or new tool install.
- Distinguish a targeted diagnostic relink/incremental check from required fresh
  reconstruction, source verification and final candidate qualification. Keep
  deferred phase instrumentation a proposed follow-up, not an implemented feature.

### Verification

Inputs: the approved Stage 1 analysis, pinned Ninja source/manual, existing docs
index and scoped rules. Read upstream source through available GitHub/web tools;
if exact-version behavior cannot be verified, omit that example or label the gap.
No Ninja execution or synthetic build is needed or authorized by this stage.

```sh
python3 -B tools/check_governance.py
git diff --check
```

Manually check each documented option against the pinned implementation, path
quoting, source links, the new navigation target and evidence boundaries. Record
source inspection separately from actual execution, which remains unperformed.
No new automated tests for prose or tests mirroring the examples.

### Commit

`Task #31 Stage 2: document targeted build and Ninja diagnostics`

## Stage 3 - Verify documentation and scope

### Artifacts

New: mydocs/working/task_m1_31_stage3.md. Correct the Stage 1/2 documents only
where review finds a concrete defect; update #31's board and plan status. The
final report remains a separate final-report workflow action after stage approval.

### Changes

- Review all user-facing guidance for reusable instructions, separate dated
  observations and clear limitations. Resolve broken links or inconsistent values.
- Verify the full diff against the approved file list. No tools/, runtime/,
  tests/, .github/, AGENTS.md, workflow/skill/template or other-task file changes.
- Preserve the known daily-board integration overlap with #14; do not merge or
  update other branches. Messaging and integration advice remain deferred by
  the requester even if all verification passes.

### Verification

```sh
python3 -B tools/check_governance.py
git diff --check
git diff d35428f037a91b5db1a22fb0b065d6d13132ccb7 --name-only
git diff --stat d35428f037a91b5db1a22fb0b065d6d13132ccb7
git status --short
```

Recompute projection arithmetic; review changed Markdown local targets and
external source citations. Inspect JSON field names/string values and text for
private information. Confirm that only authorized documents/task artifacts changed.
Record exact check results, manual inspections and unperformed build/runtime/CI
scope in the stage report. Existing offline checks cannot establish command
execution, performance improvement or game qualification. After the stage commit,
require clean status; later publication follows the final-report approval flow.

### Commit

`Task #31 Stage 3: verify build diagnostic documentation and scope`

## Verification and Commits

Each stage uses task-stage-report after its verification passes. Stage artifacts
and report are committed together; failures are resolved before claiming stage
completion. Reports distinguish inspection, derived arithmetic and unperformed
execution. Review the full staged diff before each commit; use exact file lists.

## Stage Dependencies

- Implementation-plan approval authorizes Stage 1 only.
- Stage 2 follows Stage 1 verification/report/commit and explicit continuation.
- Stage 3 follows Stage 2 verification/report/commit and explicit continuation.
- Final reporting/publication follow the repository procedure; no auto-merge,
  other-thread messages or integration instructions are included.

## Risks and Responses

- **Changing or unavailable inputs:** bind to the original identities; preserve
  dated facts and distinguish a retained projection from a replayable original.
- **Incorrect attribution:** call the difference unattributed; do not infer
  duplicate verification, CPU time or an optimization benefit without measurement.
- **Sensitive logs:** publish only allowlisted values; raw receipts stay local.
- **Parallel work:** read only bounded existing files and pinned Git objects;
  do not traverse large source archives, run builds or acquire shared locks.
- **Documentation overreach:** Ninja is one diagnostic tool, not a universal
  build/validation system. Retain existing upstream build systems and contracts.

## Approval Request

The requester approved this concrete stage split and Stage 1 by explicit
continuation in the same thread on October 4, 2026.
The previously approved task scope and document locations are unchanged. Later
stage transitions and eventual publication retain their existing approval gates.


## Stage 1 Result — October 4, 2026

The [Stage 1 report](../working/task_m1_31_stage1.md) records completed source
identity, projection, arithmetic and documentation checks. The two original runs
remain unchanged; the pinned Git observation digest is distinguished from the
plan's historical working-copy digest. Stage 2 awaits explicit continuation.


## Stage 2 Approval — October 4, 2026

The requester explicitly continued after reviewing Stage 1 commit 7de87b9.
Stage 2 guide/index work is approved with the existing locations and scope.
Other-task communication, integration and later stages remain deferred.


## Stage 2 Result — October 4, 2026

The [Stage 2 report](../working/task_m1_31_stage2.md) records the new official
guide, one index insertion, six pinned Ninja source reads and passing document,
link, shell-syntax and scope checks. Ninja commands were not executed.
Stage 3 awaits explicit continuation; communication/integration remain deferred.


## Stage 3 Approval and Result — October 4, 2026

The requester explicitly continued after Stage 2 commit 0d10f6d. The
[Stage 3 report](../working/task_m1_31_stage3.md) records the complete scope,
arithmetic, local links, source availability and privacy review. All three
implementation stages are complete; final reporting/publication awaits approval.
Merge, Issue closure and other-task communication/integration remain deferred.

## Final Reporting and Publication Approval

The requester explicitly continued after Stage 3 commit 9b6f27e, approving final
reporting and PR publication. The [final report](../report/task_m1_31_report.md)
records acceptance results and limitations. Publication uses codex/publish-task31
against master. Merge, Issue closure, other-task messages and integration advice
remain outside this approval.
