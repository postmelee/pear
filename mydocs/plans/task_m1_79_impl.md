# Task #79 implementation plan

Task plan: [task_m1_79.md](task_m1_79.md)
Issue: [#79](https://github.com/postmelee/pear/issues/79)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

The current requester instruction authorizes all three bounded stages, reference
updates and dependency-checked remote cleanup. Keep verification/report/commit gates.
Context, location judgment, source-policy limits and retention are in the task plan.

## Document Location Check

Use only existing README/component/docs locations listed in the task plan.
Repair the historical research link and component Stage6 links with their existing record's exact commit.
New task records stay in mydocs; raw path-bearing inventories remain local.

## Stage Overview

| Stage | Output | Required verification |
|---|---|---|
| 1 | Exact refs, consumer audit, preservation baseline and Stage1 report | Live metadata/policies/PRs/automation, Git-tree reference classification |
| 2 | Four master defaults and reviewed current-doc successors | Immediate SHA guards, metadata/ref readback, docs/notices/pins/source checks |
| 3 | Integrated docs, old remote cleanup and durable handoff | Independent review, PR CI, ancestry/equality, anonymous links and protected roots |

## Stage 1 — Freeze dependencies

Inspect full current component trees and protected local worktree metadata.
Record old refs and exact integration tips; inspect active PR targets, rules,
Actions settings/triggers, environments, Pages and branch-named external links.
Separate historical evidence fields, live URLs and local checkout bindings.
Stop mutation on unexpected divergent tips or unresolved active consumer.
Verification: all four current tips match remote; inventory complete; notice
guard and `git diff --check` before committing report.
Commit: Task #79 Stage 1: verify integration branch dependencies.

## Stage 2 — Add master and update guidance

Immediately GET current public metadata, old ref and branches. Require the
recorded old SHA and no master. Create refs/heads/master with that SHA; GET and
require exact equality, PATCH only default_branch=master, verify default and
symbolic remote HEAD. Re-read state after any ambiguous network result before
retrying a mutation. Keep old refs until Stage3. Retarget open PRs only if found;
closed PRs retain history and immutable document references.
Update downstream Markdown only, preserving all existing 40-hex pins, commands except the obsolete branch-fetch argument,
upstream text and runtime sources. State new PR base and distinguish retained
local task56 worktrees. Repair five dated clickable URLs to its recorded commit.
Run from Pear task checkout:

```sh
git diff --check
python3 -B tools/check_governance.py
python3 -B -m unittest discover -s tests/docs -p 'test_*.py' -v
python3 -B tools/check_source_notices.py --base 7a677152c96f7d3cbaf06ca4a38e34a8c8f817d8
```

Each component runs diff and Pear's incremental notice checker from its own cwd
against its recorded initial tip; full-tree relative link and pin comparison.
Commit docs in component task79 branches; Pear Stage2 docs/report bundled commit.
Commit: Task #79 Stage 2: adopt master and align integration guidance.

## Stage 3 — Integrate, retire and publish

Independent review of exact diffs. Push codex/publish-task79, create component PRs
against master and merge only unchanged reviewed heads with checks satisfied.
Before old remote deletion, confirm master contains the recorded tip, old ref
still equals that tip, no open PR/branch rule/automation/default consumer remains,
and all reviewed live doc links point at master or an immutable commit. Record
exact branch list. Delete only refs/heads/codex/task56, verify absence, master
identity, anonymous default/raw URLs and commit-pinned recovery. Retain all local
task56 refs/config and debug roots; never prune or force-update those checkouts.
Recovery, if separately requested: recreate the old remote ref at the recorded
tip, without moving any existing ref or replacing selected producer roots.

Run final governance/notices/diff checks after report-only edits. Reuse Stage2
document-test results only if tests/checkers/fixtures and relevant guides are
unchanged; otherwise rerun affected checks. Stage3 and final report record actual
component merges/cleanup; Pear publication/CI/merge readback goes in the Issue.
Publish coordinating Pear PR against master, inspect available CI and exact
reviewed tree before merge. Check preserved roots and pins after integration;
only reviewed docs may advance Pear main. Close Issue after confirmed merge.
Commit: Task #79 Stage 3 + final report: verify master migration and retention.

## Verification boundaries

Git, gh and Python are available; exact versions/results recorded in reports.
No added runtime tests for metadata/Markdown edits. Component CI availability
is reported explicitly; empty checks do not mean passed tests. No inherited
workflow activation, new secret, build/run/sign/install or artifact deletion.
No cleanup of unrelated remote publication branches or protected local worktrees.
