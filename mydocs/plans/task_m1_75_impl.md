# Task #75 implementation plan

Task plan: [task_m1_75.md](task_m1_75.md)
GitHub Issue: [#75](https://github.com/postmelee/pear/issues/75)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

This implements the requester's approved three-part scope; continuous stage
transition authorization is pending. Read-only planning/audits may continue.
Do not change product/source files before the documented implementation gate.

## Stage Overview

| Stage | Title | Main output | Verification |
|---|---|---|---|
| 1 | Current baseline and document reconciliation | Existing guides and exact role table | Link/status review, document suite, protected identities |
| 2 | Four-repository publication review | `mydocs/tech/task_m1_75_publication_readiness.md` | Reachable refs/content coverage and remote surface dispositions |
| 3 | WGI source-to-PE investigation | `mydocs/tech/task_m1_75_wgi_binding.md` and bounded recipe if needed | Exact inputs, isolated reproduction/comparison, limits and next work |

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

- `mydocs/tech/task_m1_75_publication_readiness.md`.
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

The concrete build command and storage estimate are an admission prerequisite
to compilation and will be added here after the read-only closure is known.
Verify existing module inputs before/after, reject unknown/shadow dependencies,
record emitted compiler/link commands, compare the untouched candidate module
and fresh output, and independently review the conclusion. Test rejection of
missing/mismatched inputs and unexplained byte differences if new tooling is
introduced. No native/PE execution, install, signing or game result is required.

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

Stage 1 implementation begins after the concrete plan/location gate. Stages 2
and 3 require completed prior-stage verification/report/commit and explicit
continuation or a user-approved continuous-stage scope. Read-only audits may
run concurrently. The current user instruction already authorizes registration,
planning and the listed substantive scope; the pending question concerns the
repository's stage-gate procedure, not renewed permission for that scope.

## Risks and Responses

- **Concurrent existing work:** isolate new branches/outputs and preserve current
  dirty/frozen roots; do not repurpose `pear-runtime`'s historical working copy.
- **Publication/history:** never rewrite history to manufacture a clean review;
  report sensitive findings privately and propose a bounded remedy.
- **Unreproducible WGI baseline:** inspect retained exact inputs first; do not
  silently use a newer generator or substitute a different installed module.
- **Disk pressure:** 512 MiB initial non-build ceiling; calculate actual WGI
  build peak before a substantial operation. No old-artifact deletion.
