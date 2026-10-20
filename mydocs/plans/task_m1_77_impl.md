# Task #77 implementation plan

Task plan: [task_m1_77.md](task_m1_77.md)
Issue: [#77](https://github.com/postmelee/pear/issues/77)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

The requester's 2026-10-21 directive authorizes the four public conversions and
existing README/related-document updates. All implementation below stays inside
that scope. Refer to the task plan for context, upstream reuse, documentation
locations and the 512 MiB text-only capacity allowance.

## Document Location Check

All files are existing official/component guidance at task-plan locations;
new task artifacts stay under mydocs. Raw remote/local evidence stays outside
public Git. Frozen reports, provenance and input/source/tool pins are unchanged.

## Stage Overview

| Stage | Main output | Verification |
|---|---|---|
| 1 — Current publication preflight | Exact baseline and stage report; draft doc changes | Refs/surfaces/parents/tree comparison and protected-root snapshot |
| 2 — Public conversion and guide update | Four public repositories and current access text | Immediate identity guard; visibility-only PATCH; anonymous exact-blob GETs |
| 3 — Validate and publish documentation | Reports, documentation PRs and current default guidance | Local docs/notices/links, independent review, CI and integrated-diff review |

## Stage 1 — Freeze preflight

Artifacts: mydocs/working/task_m1_77_stage1.md and private preflight receipt.
Compare every component default/ref/tag to the exact Task75 integrated audit;
record PR/Issue/comment/check/Actions/artifact/release/deployment/environment and
Wiki/Pages/discussion dispositions. Reuse only the unchanged tree's downstream
history/provenance review; never assert full inherited-history clearance.
Snapshot 12 protected local roots with Git HEAD/status and existing ignored-file
inventory scope. Draft changes in new isolated documentation checkouts only.
Verification: successful complete collector, no unexpected differences,
git diff --check and incremental source-notice check before commit.
Commit: Task #77 Stage 1: verify unchanged publication and preservation baseline.

## Stage 2 — Convert and reconcile

Artifacts: existing docs listed in task plan and stage2 report. Immediately
before each change, GET repository+branches+tags and assert PRIVATE,
codex/task56 and the expected single exact ref with no tags. PATCH only private:
false. Retain before/response/after facts; do not change settings by inference.
Verify public metadata and exact default commit, then anonymous repository,
raw README, license and provenance reads where present. Compare raw bytes to
Git blobs and retain hashes/HTTP status. Do not retry a mutation after an unknown
outcome without first GETting current visibility.
Update current private/collaborator-only statements to public source access;
preserve private input requirements and dated historical statements. Reflect
merged Task75 correspondence only where current prose incorrectly calls it
unresolved. No recipe, command, ABI, candidate or license change.
Verification: private-to-public transitions all confirmed; anonymous bytes match;
only planned Markdown files changed; stage report and source notice/diff checks.
Commit: Task #77 Stage 2: publish component sources and reconcile access guidance.

## Stage 3 — Verify and integrate documentation

Run from Pear task worktree:

```sh
git diff --check
python3 -B tools/check_governance.py
python3 -B -m unittest discover -s tests/docs -p 'test_*.py' -v
python3 -B tools/check_source_notices.py --base cc23a3c0a0a48624f55f75f2cf310c4a41d95850
```

For all component documentation checkouts: git diff --check against the recorded
base; manual exclusions/provenance review and Pear notice checker against the
explicit component repo where supported. Resolve changed Markdown destinations
using complete Git trees, not sparse working-directory absence. Verify external
links anonymously. An independent agent reviews the exact final patches.
Publish codex/publish-task77 PRs against existing defaults (Pear master;
components codex/task56). Check current source bases before push/merge. Preserve
stage commits and recheck source tree equality outside the approved Markdown
allowlist. Record actual CI availability/results, never infer component CI.
The requested current-document update includes integration of the reviewed
Markdown changes through PRs. Do not merge an unreviewed or failed successor.
Compare protected root identities at completion, preserve old task worktrees and
all runtime/input bytes; no branch/worktree/artifact cleanup is included.
Final report: mydocs/report/task_m1_77_report.md; daily board Done at KST time.
Commit: Task #77 Stage 3 + final report: verify public source access and documentation.

## Reuse and Limits

Python standard-library document checks, Git and authenticated GitHub CLI/API
are available; anonymous HTTP access is checked during conversion. No runtime
build/test/run is needed for visibility and Markdown changes. Prior runtime
results retain exact original identity/scope and are not new executions.
Remaining source/input/license-history limits are carried forward. No operation
changes #47, executable source, app/runtime resources, games, saves or prefixes.
If any mandatory check fails, fix within scope before reporting stage complete.
