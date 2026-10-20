# Task #75 implementation plan

Task plan: [task_m1_75.md](task_m1_75.md)
GitHub Issue: [#75](https://github.com/postmelee/pear/issues/75)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

The requester approved all three stages continuously on 2026-10-20, including
the document locations below, with verification, reports and commits at every
stage boundary. Visibility changes, game execution and deletion of existing
inputs/artifacts remain excluded. This approval does not broaden the task scope.

## Stage Overview

| Stage | Title | Main output | Verification |
|---|---|---|---|
| 1 | Current baseline and document reconciliation | Existing guides and exact role table | Link/status review, document suite, protected identities |
| 2 | Four-repository publication review | `mydocs/tech/task_m1_75_publication_readiness.md` | Reachable refs/content coverage and remote surface dispositions |
| 3 | WGI source-to-PE investigation | `mydocs/tech/task_m1_75_wgi_binding.md` and bounded recipe if needed | Exact inputs, isolated reproduction/comparison, limits and next work |
| 4 | Approved notice/publication extension | FEX adjacent notice and five review PRs | Exact provenance/source checks, documentation integration and remote PR verification |

## Document Location Check

| File | Planned location | Stage artifact path | Match | Notes |
|---|---|---|---|---|
| Current Pear guidance | Existing README/docs | Same existing files | OK | No new roadmap or public private-path inventory |
| Component status/notice guidance | Source-owned existing files | Separate Task75 component branches | OK | Frozen provenance unchanged |
| Publication/WGI findings | `mydocs/tech/` | `task_m1_75_publication_readiness.md`, `task_m1_75_wgi_binding.md` | OK | Sanitized dated evidence |
| Raw exact records | Private task evidence | External Task75 audit/build roots | OK | No payload/credential export |

## Stage 1 — Reconcile baseline and current documentation

### Artifacts

- Pear README and affected existing development/boundary guides.
- Runtime README/development/NOTICE and Wine/DXMT/FEX guidance only where the
  final published revisions contain an actually stale statement.
- A sanitized baseline table in the WGI/publication research note as appropriate.
- `mydocs/working/task_m1_75_stage1.md`.

### Changes

1. Preserve main/master and both locked Task56 producer worktrees; work from a
   fresh `codex/task75` Pear branch based on `2c151f1`.
2. Pin final private source tips: Wine `007291b`, FEX `4ae26dd`,
   DXMT `d0ad509`, runtime `9be1545`. Retain complete hashes in evidence.
   Separately record the candidate's compiled component pins, runtime tool
   `6f0202b`, FEX tool `9c9b602` and corrected Pear producer `400da114`.
3. Update README's old `9147257` final-report pointer to the merged corrected
   report without altering historical reports. Correct publication-pending and
   proposed-ownership language only in current component guidance.
4. Keep the CodeWeavers/Rosetta Preview separate from the selected ARM Wine
   lineage; state the retained-input limits and WGI investigation boundary.
5. No implementation changes to selected candidate sources or source cutover.

### Verification

Use the existing document validator/test entrypoints inspected in
`.github/workflows/documentation.yml`. Retain exact commands/output in the stage record.

```sh
git diff --check
python3 -B tools/check_governance.py
python3 -B -m unittest discover -s tests/docs -p 'test_*.py' -v
python3 -B tools/check_source_notices.py --base 2c151f1d074fab5a55bc2d77e25b5fb81aedc257
```

The incremental notice command follows `docs/contributing.md`.
Do not add tests that assert prose.
Check changed Markdown targets/anchors, exact pinned public references,
component ref metadata and preservation identities. Runtime execution is not
needed for documentation-only changes.

### Commit

`Task #75 Stage 1: reconcile split-runtime ownership and development baseline`

## Stage 2 — Review publication readiness

### Artifacts

- `mydocs/tech/task_m1_75_publication_readiness.md` and adjacent sanitized
  `task_m1_75_publication_details.json` evidence data.
- Private exact ref/object inventories, audit commands and redacted/manual
  dispositions for Wine/FEX/DXMT/runtime.
- `mydocs/working/task_m1_75_stage2.md`.

### Changes

1. Inventory every remote branch/tag and reviewable GitHub publication surface.
   Identify all remote reachable commits and any refs unavailable locally.
2. Reuse known public upstream ancestry as inherited baseline, preserving its
   exact identity. Inspect all reachable downstream-added/changed blobs,
   commit/tag text and path metadata; document object-size/byte-budget skips.
   Runtime has no equivalent upstream code-history exemption.
3. Inspect privacy patterns without printing secrets or raw private snippets.
   Review every hit; distinguish source fixtures/public upstream examples from
   newly committed private data. Any exposure blocker remains explicit.
4. Verify license/provenance/notice dispositions and contribution-policy
   attribution. A machine notice pass is not legal clearance.
5. Inspect Actions runs/log/artifact and release/Issue/PR surfaces as exposed by
   current permissions. Do not delete or alter them. State absent, inspected or
   unavailable coverage per surface and repository.
6. Produce READY / READY WITH LIMITS / BLOCKED / INCOMPLETE decisions tied to
   exact refs and findings, with no visibility mutation or release claim.

### Verification

Read-only `gh api` queries and Git `for-each-ref`, `rev-list`,
`cat-file --batch`/`ls-tree` produce pinned inventories. Audit tools must fail on
truncation/read errors and count every disposition. Reconcile scan coverage to
the ref/object inventory, manually review hits and recheck remote heads at the
end. Hash retained private records; scan public summary for private material.

### Commit

`Task #75 Stage 2: record four-component source publication readiness`

## Stage 3 — WGI source-to-development-PE correspondence

### Artifacts

- Exact private module/input inventory, command plan and output comparison.
- `mydocs/tech/task_m1_75_wgi_binding.md`.
- Minimal recipe/comparison code and meaningful tests if the existing tooling
  cannot express the needed module. Record exact component-owned paths here
  before editing; preserve all upstream file terms.
- `mydocs/working/task_m1_75_stage3.md` and final task handoff.

### Changes

1. Locate candidate3/runtime12 WGI PE and recoverable historical module records.
   Check SHA/size/PE machine, section/import/export/debug metadata; do not run it.
2. Join the selected Wine revision and module `Makefile.in`, spec/IDL, C sources,
   generated headers/import libraries, compile definitions, compiler/linker and
   SDK inputs. A source-tree filename or current source similarity is insufficient.
3. Identify reusable input bytes and their current availability. Define a fresh
   module-only output root. Measure peak source/generated/object/link/comparison
   overlap before compilation; do not create a full candidate/game/prefix copy.
4. Execute only the bounded build/comparison if admitted inputs and storage
   permit. Retain original and rebuilt bytes, exact commands and differences.
   Any timestamp/debug normalization must be explicitly field-bound and
   explained; unexplained executable differences prevent an equality claim.
5. Record whether provenance, exact reproduction or an evidenced mismatch
   establishes the relationship. Identify unresolved missing inputs precisely.
   Natural-call observation and HRESULT-preserving repair remain next work.

### Verification

Read-only closure identifies 65 original actions (36 generation, 28 compilation,
one ARM64X link), 173 source/header inputs and 11 preserved lower-layer libraries.
Implement the bounded adapter, when required, in common-runtime
`pear_runtime/recipes/wgi.py`, `recipes/wine/wgi-v1.json` and
`tests/build/test_wgi.py`; document it in existing `recipes/wine/README.md`.
The generated original Makefile/log-derived argv are reused; no upstream module
or existing candidate source is changed. New original adapter/tests retain Pear
GPL-3.0-or-later notices. No implicit fallback to the old source tree is allowed.

Before compilation, the private exact action/input plan must be admitted by hash.
The planned additional ceiling is 128 MiB: 60 MiB for the 57,077,930-byte input
pack (57,659,392 stat-allocated bytes), 32 MiB for generated/object/link/comparison
output, 32 MiB for diagnostics and 4 MiB for small evidence. Keep a separate
6 GiB reserve: at least 6,576,668,672 available bytes. Remeasure at execution.
Final pack admission measured 281 files, 57,220,780 logical / 57,802,752
stat-allocated bytes, still below the 60 MiB pack allocation. Preserve a failed
control-link trace attempt; a fresh retry adds a full 32 MiB output, 4 MiB final
record and 8 MiB diagnostics allowance to all retained bytes. Its reviewed peak
was 126,810,798 bytes, below the unchanged aggregate 128 MiB ceiling.
Reuse the 782,265,656-byte LLVM tree read-only; no toolchain/runtime/game/prefix
copy. Record exact CLI, admitted digest and actual storage in Stage 3 evidence.
All original inputs remain immutable. Compiler dependency and linker diagnostics
must identify actual inputs; unknown dependencies prevent a reproduction claim.
Verify existing module inputs before/after, reject unknown/shadow dependencies,
record emitted compiler/link commands, compare the untouched candidate module
and fresh output, and independently review the conclusion. Test rejection of
missing/mismatched inputs and unexplained byte differences if new tooling is
introduced. Only admitted build tools may execute. No Wine/runtime/guest execution, install,
signing or game result is part of this task.

### Commit

`Task #75 Stage 3: establish the WGI source and development PE correspondence`

## Integrated Verification and Commits

- Preserve stage gates, checks, reports and commits, with only the approved
  stage-transition authorization changing whether a separate continuation is needed.
- A non-ready publication verdict is a valid completed review result if the
  review itself is complete; a failed/incomplete checker is not a pass.
- A WGI identity conclusion must be supported by exact evidence. Do not declare
  source correspondence merely because candidate3 and runtime12 match.
- Keep final/private ref roles distinct; no changed source receives reused
  native qualification automatically.
- `git diff --check`, relevant source notices/tests and privacy review pass.
- Final report and daily board identify actual status, retained inputs and
  remaining decisions. PR publication/merge and repository visibility are
  separate actions; actual visibility conversion awaits requester review.

## Stage Dependencies and Approval

The requester approved the concrete three-stage plan and continuous progression
on 2026-10-20. Stages remain ordered by completed verification, report and commit;
read-only supporting audits may run concurrently. No renewed stage approval is
needed within this scope. Actual public conversion, game execution and deletion
remain excluded. Component documentation changes use separate `codex/task75`
worktrees; Wine uses a sparse documentation checkout to keep the initial
512 MiB non-build allowance. Component stage reports use their existing
`mydocs/working/` role and are committed with the corresponding documentation.

## Risks and Responses

- **Concurrent existing work:** isolate new branches/outputs and preserve current
  dirty/frozen roots; do not repurpose `pear-runtime`'s historical working copy.
- **Publication/history:** never rewrite history to manufacture a clean review;
  report sensitive findings privately and propose a bounded remedy.
- **Unreproducible WGI baseline:** inspect retained exact inputs first; do not
  silently use a newer generator or substitute a different installed module.
- **Disk pressure:** 512 MiB initial non-build ceiling; calculate actual WGI
  build peak before a substantial operation. No old-artifact deletion.

## Stage 4 — Complete FEX adjacent notices and publish review PRs

On 2026-10-21 the requester explicitly authorized correcting and verifying the
three FEX generated-header provenance/license notices, then publishing Task75
changes as PRs. This is a bounded completion extension, not a visibility change,
merge, game run, source behavior change or deletion. Stage verification, reports
and commits remain required; the instruction authorizes continuous progression
from notice correction to verified PR publication without another approval.

### Locations and ownership

- In an isolated FEX `codex/task75` worktree based on `4ae26ddf9a21b52cd50d096504c4d0ea5ab49204`,
  add `Pear/Diagnostics/include/NOTICE.md` adjacent to the three unchanged headers.
  Bind exact header/template/schema hashes, first known import and missing original
  holder/Git-revision facts; reproduce the MIT grant/warranty without inventing
  attribution or converting terms. Preserve all frozen headers/manifests.
- Link that notice from existing `Pear/README.md`; keep historical import metadata
  as historical evidence. Record component checks in `mydocs/working/task_m1_75_stage4.md`.
  Adjacent component attribution belongs with its source, not in Pear's product docs.
- Update current Pear publication-readiness findings, final report and daily board;
  preserve dated Stage1–3 reports and detail JSON as snapshots. Record Stage4 in
  `mydocs/working/task_m1_75_stage4.md`; update these task/implementation plans.
- Publish Pear as `codex/publish-task75` targeting `master`. Publish reviewed
  component branches under the same publication name targeting their existing
  `codex/task56` default branches; no new integration/default branch is created.
  Create four private component PRs and one coordinating Pear PR with exact links.
  Do not merge, close #75 or change visibility. Show final reviewed refs and limits.

### Verification and reuse

1. Check exact retained origin proof and per-header producer joins; independently
   review the notice and unchanged MIT grant text. Copyright absence stays explicit.
2. Verify all 99 FEX imported source/payload bytes and modes, original upstream
   ancestry, no tracked private selector and shared provider hashes using the
   existing `Pear/Tools/check_source.py` with explicit Wine/runtime roots.
3. Confirm the three frozen headers and provenance manifests remain identical to
   the imported ref; run incremental notice, local-link, whitespace and bounded
   privacy checks on the documentation delta. No synthetic test that merely
   asserts prose is added. No native/code behavior changed, so no rebuild is needed.
4. Reuse Stage3 WGI build/test evidence only after checking its source/recipe/test
   and committed identities are unchanged. Recheck affected docs using the existing
   governance checker; run the document suite if integration changes its inputs.
5. Refresh component branch/tag/privacy and reviewable remote exposure inventory.
   Audit new content since the earlier pinned inventory. After publishing, verify
   exact remote heads/base branches/PR diffs and inspect any CI results; list absent
   or unavailable checks explicitly. Reconcile final readiness with actual PR refs.
6. Verify a clean task worktree and source notices before each commit/PR. Preserve
   old execution and all debug inputs/outputs; no cleanup is authorized.

### Retention and peak storage

The FEX sparse checkout materializes the needed source-check paths and `Pear/`
only: 159 blobs, 2,583,062 logical bytes at planning. Share existing Git objects;
no clone, toolchain/runtime copy, build or submodule initialization. Reserve an
additional 32 MiB for this checkout, notices and audit/PR text; observed available
space was 15,839,916,032 bytes. Preserve existing Task75 worktrees/evidence, exact
original inputs, #47 and all private state. Retain new review records for PR review
and any later authorized visibility decision. Report actual logical/allocated
usage separately; no reclaimed-space claim.

### Commit and publication gate

Component: `Task #75 Stage 4: document generated-header provenance and MIT terms`.
Pear: `Task #75 Stage 4 + final report: complete source notices and publish review handoff`.
The existing `task-final-report` procedure applies to the authorized Open PR
publication after verification. Visibility and merge require separate decisions.
