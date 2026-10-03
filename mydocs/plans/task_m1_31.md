# Task #31: Build timing analysis and targeted Ninja diagnostics

GitHub Issue: [#31](https://github.com/postmelee/pear/issues/31)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Status: task and implementation plans approved; Stage 1 complete; Stage 2 awaiting explicit continuation.
Planning date: October 4, 2026 (Asia/Seoul).

## Purpose

Make slow build iterations diagnosable using the timing records and build tools
Pear already has. Preserve the distinction between time inside build commands,
time elsewhere in the construction invocation, and later qualification. Provide
concise contributor guidance for targeted Ninja diagnostics without changing
active build recipes, validators or correctness requirements.

## Background

Read the [project overview](../../README.md), [documentation index](../../docs/README.md),
[architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md),
[root rules](../../AGENTS.md), [documentation rules](../../docs/AGENTS.md), and the
[task](../manual/task_workflow_guide.md), [Git](../manual/git_workflow_guide.md),
[document-location](../manual/document_structure_guide.md) and
[conflict](../manual/agent_code_hyperfall_rule_conflict.md) procedures.

Live Issue inspection found no duplicate. [#5](https://github.com/postmelee/pear/issues/5)
owns the FEX host integration; [#7](https://github.com/postmelee/pear/issues/7)
owns the DXMT/Metal bridge; [#14](https://github.com/postmelee/pear/issues/14)
owns regression CI and patch maintenance. [#15](https://github.com/postmelee/pear/issues/15)
is runtime/game performance characterization, not build diagnostics.

Task #5 already built pinned ARM64 Ninja 1.13.1 and Task #7 reused it. Existing
Python command receipts record elapsed_ms. Task #7 used 31 bounded link trials
to isolate a nondeterministic link result before constructing two fresh builds.
This task records and generalizes that diagnostic separation; it does not claim
the current tools or diagnosis practices are absent.

### Preliminary observations, not a new benchmark

The following arithmetic was independently recomputed from existing records during
planning. The ten recorded commands are serial top-level operations in each
constructor invocation. Their elapsed times already include their child work;
never add nested Ninja edge times to this sum.

| Recorded invocation | Whole invocation (ms) | Ten command durations (ms) | dxmt.compile within that sum (ms) | Unattributed remainder (ms) | Remainder share |
|---|---:|---:|---:|---:|---:|
| small_stub_reference / build7 | 902376 | 132326 | 82978 | 770050 | 85.34% |
| small_stub_candidate / build8 | 893511 | 119568 | 70049 | 773943 | 86.62% |

Remainder = whole invocation minus sum of the ten command durations. This is
unattributed wall time, not measured hashing time, proof of redundant work, CPU
utilization, or time recoverable by Ninja tuning. It includes work outside the
recorded command spans. Inspect preparation and verification boundaries before
assigning causes. Shared-lock waiting occurs outside these wrapper spans; later
independent comparison and native qualification are also outside them. Confirm
these boundaries against the retained wrapper and constructor source in Stage 1.
No cold/warm controlled experiment or improvement measurement was performed.

Planning sources inspected read-only:

- #5 checkout commit: 275681a07353ccfe5676ed2518530795c4994938.
- #7 checkout commit: e41b7bd7daaab707c3609693ff11e14af6f2d085.
- #7 record: mydocs/working/task_m1_7_stage5_reconstruction_observations.json;
  SHA-256 8a3d8fda4cb037e95f2425ff086d3f295134d08a8cd14f942e47de19964756a1.
- First referenced build record SHA-256:
  fb5648ddb21836b5f0a80a1e546910ee3f46fb9a563a54c1197fe3743cd5dce1.
- Second referenced build record SHA-256:
  5eb2a22a1e6132043ba3be3985683573e23f81893f91b9729b55ef00fb57a31d.
- Local operator build7.json wrapper receipt SHA-256:
  d93facf569f505236c856687c9d3c246398f558ca05fff0d15d46ef3be1135d1.
- Local operator build8.json wrapper receipt SHA-256:
  7accc5fdc754ff5b1054fe2ad5f7ec120bae76cc053d99d73cf07e6869c86f89.

The wrapper receipts are local observations, not independently qualified build
receipts or records committed by this plan. Stage 1 will retain a minimal,
non-sensitive projection with its derivation and limitations; no proprietary
payload, absolute private path, full environment or private diagnostic is copied.
If the source disappears or changes, preserve this dated observation and report
the missing/revised evidence instead of silently assigning it a new identity.

## Scope

### Included

- Read-only, bounded analysis of existing #5/#7 timing records and relevant source.
- A dated analysis and minimal timing projection in mydocs/tech/.
- Concise guidance on attributing time and applying existing Ninja diagnostics.
- One documentation-index link for discovery, after location approval.
- Documentation verification, task artifacts and eventual reviewable publication
  under the existing stage/final-report workflow.

### Excluded

- New instrumentation, receipt/schema/validator changes, timing aggregation tools,
  build system replacement, new CI jobs, cache policy or parallelism tuning.
- Building, signing, benchmarks, qualification, game or guest execution.
- Changes to other worktrees, active outputs, input archives, processes or locks.
- Changes to AGENTS.md, scoped rules, tests, templates or operating manuals.
- Messaging other conversations, recommending integration into their current
  work, merging a PR, closing the Issue or updating other task branches.

## Design Direction

1. Reuse current CMake/Meson/Ninja and existing Python elapsed_ms records. Preserve
   upstream implementation languages. No new subsystem or third-party code copy
   is needed; links and original explanations suffice.
2. First compare whole-invocation and existing command spans. Label unmeasured
   preparation/input replay/storage/post-validation costs as unattributed until
   measured. Recommend future phase timers only as scoped follow-up candidates.
3. Use Ninja tools when command scheduling, individual compilation/linking, or
   unexpected rebuilds are implicated. Candidate examples are -n -d explain,
   -t query, -t commands and .ninja_log interpretation; verify each against the
   pinned version before publishing examples. Do not run them on active output
   directories during this task.
4. Distinguish fresh output directories, verified clean reconstruction, warm
   caches, no-change incremental checks and targeted diagnostic relinks. A fresh
   output root does not prove cold host caches or a clean machine.
5. A targeted diagnosis does not replace the final fresh-build, provenance,
   signature, native fixture or game gates. Preserve failed attempts and exact
   input/tool/recipe identities. Required validation must not be skipped merely
   because it dominates elapsed time.
6. Keep full timing evidence local where sensitive. Future diagnostic output
   should use the owning task's traceable .build/taskN location; no new global
   scratch-directory rule or cleanup is introduced here.
7. Relevant sources: Ninja 1.13.1, commit
   79feac0f3e3bc9da9effc586cd5fea41e7550051 (tree
   28c433f85d2a313387f32724bae3e08c6bbf0b0b), and its
   [official manual](https://ninja-build.org/manual.html), reviewed October 4,
   2026. Stage 2 will bind command behavior to immutable source links. Ninja is
   Apache-2.0 licensed; this documentation task does not redistribute its source
   or change upstream contribution practices.
8. Selected skills: task-register, task-start and todo during planning;
   task-stage-report at stage completion; task-final-report only after all
   approved stages are complete. Apple technical experts are not applicable:
   this is host-only record analysis/documentation, not Metal implementation.

## Document Location Judgment

| File | Classification | Audience | Selected location | Alternative location | Reason |
|---|---|---|---|---|---|
| Build diagnostic guide | Official contributor technical guidance | Contributors and agents | docs/development/build-diagnostics.md | mydocs/manual/ | General build diagnosis belongs in the existing official technical root, not framework workflow manuals. |
| Guide navigation link | Official documentation index | Contributors and agents | docs/README.md | Root AGENTS.md | Existing navigation provides discovery without adding mandatory Ninja-specific rules for unrelated work. |
| Dated timing analysis and projection | Evidence and analysis | Reviewers and task owners | mydocs/tech/20261004_build_timing_analysis.md and .json | docs/development/build-diagnostics.md | One observed pair of builds is dated evidence, not a permanent performance statement or product contract. |
| Plans, reports and work status | Task artifacts | Requester and task owners | Existing mydocs/plans, working, report and orders folders | docs/ | Preserve approval and execution history separately from reusable guidance. |

The requester approved this location judgment with an explicit continuation in
the same thread on October 4, 2026. Official-guide, index and evidence changes
remain assigned to the stages below; this approval update implements none of them.

## Expected Changed Files

New, after approval:

- docs/development/build-diagnostics.md
- mydocs/tech/20261004_build_timing_analysis.md
- mydocs/tech/20261004_build_timing_analysis.json

Modified, after approval:

- docs/README.md: one navigation entry only.

Task artifacts:

- mydocs/orders/20261004.md
- mydocs/plans/task_m1_31.md
- mydocs/plans/task_m1_31_impl.md
- mydocs/working/task_m1_31_stage1.md
- mydocs/working/task_m1_31_stage2.md
- mydocs/working/task_m1_31_stage3.md
- mydocs/report/task_m1_31_report.md

## Tentative Stages

- **Stage 1 - Preserve and attribute existing timing evidence**
  - Retain the sanitized two-run timing projection and dated analysis.
  - Recompute sums/remainders; identify wrapper boundaries, nested timing and
    unavailable measurements without running a build or verification replay.
- **Stage 2 - Write targeted build diagnostic guidance**
  - Add the approved guide and one index link.
  - Verify examples against Ninja 1.13.1; preserve CMake/Meson ownership of build
    definitions and separate diagnostic work from final qualification.
- **Stage 3 - Review scope and verify documentation**
  - Check arithmetic, source links, local routing, evidence limits and changed
    files. Complete stage/final reporting through their approval gates.
  - Publication can make the result reviewable; merge and other-thread handoff
    remain separate requester decisions.

Each stage is reported, verified and committed before requesting continuation.

## Verification Plan

### Stage Verification

- Stage 1: read existing JSON with Python 3 and recompute exact integer totals;
  compare the result with the retained projection. Retain source digests and
  explicit treatment of unmatched time. No implementation-mirroring unit tests.
- Stage 2: inspect immutable Ninja source/manual for command behavior; manually
  review target/path quoting, diagnostic execution boundaries and examples.
- Stage 3: run python3 -B tools/check_governance.py and git diff --check; inspect
  the complete task diff. The existing checker does not validate all Markdown,
  headings, shell examples or external URLs, so manually verify those relevant
  to the new files and retain the performed checks in the report.

### Integrated Verification

- Only the listed documents/task artifacts change; no build/validator/CI source.
- Values in guidance, dated analysis, projection and reports agree, without
  treating two uncontrolled runs as a performance benchmark.
- No new official guide links point to absent local #5/#7 files; use immutable
  upstream/task source links or the task-owned sanitized evidence as appropriate.
- No private path, credentials, signing input, game payload or whole environment
  is introduced. All required qualification boundaries remain explicit.
- Verify worktree status is clean before publication and retain the exact commit.

Observed planning availability: local Git/Python and the repository checker are
present. GitHub live reads/Issue creation succeeded through available tools;
ordinary sandboxed gh initially lacked network connectivity. Documentation checks
will be run on this task's own checkout. Ninja diagnostic execution, new builds,
benchmarks, runtime and game tests are intentionally unperformed.

## Parallel Work and Risks

- Base: d35428f037a91b5db1a22fb0b065d6d13132ccb7, matching live master at planning.
  Work in a separate codex/task31 checkout; do not switch the shared main checkout.
- PR #30's inspected changes do not include the proposed guide, analysis or
  docs/README.md. The common date board is the known merge overlap: this branch
  adds only #31; preserve other tasks' rows when integration is later approved.
- #5/#7 remain independent and need no immediate master update for this work.
  Exact-source verification already in progress must retain its original inputs.
- Public task links can change with later branch cleanup; select immutable commits
  and retain only the minimal task-owned measurement facts needed for review.
- Analysis may show verification dominates, but this is not permission to weaken,
  cache or eliminate checks. Concrete instrumentation/optimization needs its own
  approved implementation scope.
- The requester will reassess other tasks after this work before authorizing
  communication or integration guidance. No such messages are sent by #31 now.

## Approval Request

The requester approved starting separate analysis/documentation work and deferred
other-thread communication/integration on October 4, 2026. That authorization
covers Issue registration and this isolated task-plan preparation. It does not
constitute approval of the newly specified document locations or later stages.

The subsequent explicit continuation approved this scope, document-location
judgment and three-stage sequence. The [implementation plan](task_m1_31_impl.md)
now specifies artifacts and verification. A further explicit continuation approved the implementation plan and Stage 1.
Later stage transitions still require explicit continuation.


## Stage 1 Result — October 4, 2026

The [Stage 1 report](../working/task_m1_31_stage1.md) records completed source
identity, projection, arithmetic and documentation checks. The two original runs
remain unchanged; the pinned Git observation digest is distinguished from the
plan's historical working-copy digest. Stage 2 awaits explicit continuation.
