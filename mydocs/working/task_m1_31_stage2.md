# Task #31 Stage 2: Targeted build and Ninja diagnostics

GitHub Issue: [#31](https://github.com/postmelee/pear/issues/31)
Implementation plan: [task_m1_31_impl.md](../plans/task_m1_31_impl.md)
Stage: 2 — complete; Stage 3 awaiting explicit continuation.
Date: October 4, 2026 (Asia/Seoul).

## Stage Purpose

Turn the approved timing analysis into reusable contributor guidance: attribute
elapsed time first, select a bounded Ninja diagnostic only when applicable, and
preserve existing final verification requirements. The requester explicitly
approved this stage after Stage 1 commit 7de87b9.

Context used: the approved task/implementation plans, root and docs/AGENTS.md
rules, documentation index, Stage 1 report and task-stage-report procedure.
Reuse current Ninja/CMake/Meson and timing records; no new build system, tool
installation, instrumentation or Apple-specific implementation is required.

## Artifacts

| File | Change summary |
|---|---|
| docs/development/build-diagnostics.md | Attribution, workspace selection, three target diagnostics, log interpretation and qualification boundaries |
| docs/README.md | One discovery link; all previous content preserved |
| mydocs/plans/task_m1_31.md | Stage 2 approval and completion status |
| mydocs/plans/task_m1_31_impl.md | Stage 2 approval and outcome |
| mydocs/orders/20261004.md | Update #31 only |
| This report | Source review, documentation checks and limitations |

## Body Change Scope / Lossless Preservation

The guide and index use the approved official-documentation locations. Dated
analysis stays in mydocs/tech and is linked rather than rewritten or promoted to
a general speed claim. Both Stage 1 evidence files are byte-unchanged in this
stage's diff. The index diff is exactly one inserted line.

No source, build recipe, validator, receipt schema, CI, agent-rule, template,
other-task branch or existing build output was changed. No other-thread message,
integration recommendation, merge or Issue closure occurred. Documentation does
not authorize running a diagnostic against an active or immutable evidence tree.

## Verification Results

### Upstream inspection

Six official files were fetched at Ninja commit
79feac0f3e3bc9da9effc586cd5fea41e7550051; version.cc identifies 1.13.1.
The guide cites these immutable paths and review date. Git blob IDs returned by
the source provider are recorded below; deps_log.cc was read at lines 160-345.

| Source file | Git blob ID | Relevant review |
|---|---|---|
| src/version.cc | 69d25fcfa124839c7d0a739fbbc1d812b2d9b60d | Version string |
| doc/manual.asciidoc | 1fa208a4c49d09556e5b4925fecf96c7f6d3c27b | Tool meaning and log location |
| src/ninja.cc | 92d0761aa38e5b866dc1118f62c3974539665b44 | Tool dispatch, global option order, log setup and manifest dry-run |
| src/build.cc | 7ad08117be4c5f6a30c9c4f5ddbaf4afb6b4f981 | Dry-run command runner, filesystem operations and edge timing |
| src/build_log.cc | 890a3cd3b3a3ed1669eae488825286ee27c8138c | Per-output rows, command hashes, load/compaction and invalid-version removal |
| src/deps_log.cc | 169ec49d52850144f2cc466f0ad0456f838c7f15 | Invalid-log removal and truncated-log recovery |

Manual source-to-example review established:

- -t commands traverses the loaded target/input graph and prints commands. It
  dispatches before log setup and manifest regeneration; it does not execute the
  printed commands or report only dirty edges.
- query dispatches after log loading. The example puts -n before -t to suppress
  ordinary write-open/compaction paths; global parsing ends when a tool is selected.
- -n -d explain selects explanation output and the dry-run runner. It does not
  execute compiler/linker commands, but filesystem neutrality is not guaranteed:
  log recovery and directory/response-file handling have write paths. Therefore
  examples require an approved inactive mutable diagnostic tree.
- Dry-run manifest regeneration can exit before reaching the requested target.
  The guide warns against treating that output as a no-change target result.
- Log rows are per output, so multiple rows can represent one edge. Recorded
  start/end milliseconds share an invocation origin. Overlap, multiple invocations,
  compaction and unrecorded failures limit timing conclusions. No critical path
  or CPU time is inferred from duration sums.

These are source-inspection results, not observed command executions.

### Local documentation verification

Context: Python 3.14.4, local Git, /bin/sh syntax checking and the existing offline
checker in codex/task31. No Ninja binary or compiler was executed.

```sh
python3 -B tools/check_governance.py
git diff --check
```

Results: PASS: 23 documents, 175 local targets; skill routing and source inventory
consistent (offline). Whitespace checks passed.

An in-memory Python review also verified:

- The sole sh example block passes /bin/sh -n syntax checking, without executing it.
- New/changed local links exist, and the Reproducibility heading exists in the
  referenced architecture document.
- All six named source references resolve within the guide to the reviewed commit.
- Removing the one new index entry produces exactly the previous index bytes.
- Neither Stage 1 evidence file changed; no private user/tmp paths, credential
  markers or private-key material appear in the changed documents.

Manual review covered quoted placeholders, no shell evaluation of printed
commands, measurement caveats, appropriate evidence/workspace boundaries, and
retention of final fresh-build requirements. The guide remains usable without
agent software, paid tooling or a new dependency.

### Unperformed checks

No new build, Ninja diagnostic, full provenance replay, native/game test, timing
benchmark or CI run was performed. These are outside this documentation stage.
Shell syntax and source inspection do not establish command execution or speedup.
External-link review of the historical Pear evidence remains in Stage 3; the six
Ninja source files were successfully fetched during this stage.

## Residual Risks

- Different Ninja pins require a fresh behavior review; version strings alone do
  not establish provenance.
- A copied build tree can retain original absolute paths; the guide does not
  prescribe copying immutable artifacts or claim a copied tree is isolated.
- Log compaction and multiple runs limit retrospective reconstruction. The guide
  does not add a log parser, critical-path analyzer or phase instrumentation.
- The dated two-run analysis remains limited to its original measurement boundaries.

## Impact on Next Stage

Stage 3 reviews the complete task diff, arithmetic, source-link availability and
scope. Retain all exclusions; no task-owner handoff or branch integration is part
of that review. Final reporting/publication retain their normal approval gates.

## Approval Request

Approve the guide and these verification results to proceed to Stage 3: final
cross-document, link and scope review.
