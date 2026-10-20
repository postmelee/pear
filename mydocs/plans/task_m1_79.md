# Task #79: native component integration branches

GitHub Issue: [#79](https://github.com/postmelee/pear/issues/79)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

## Purpose

Use `master` as the public default and integration branch of pear-wine,
pear-fex, pear-dxmt and pear-runtime. Preserve exact selected runtime identities.

## Background

[Task #77](https://github.com/postmelee/pear/issues/77) published the component
sources and integrated documentation, leaving temporary `codex/task56` defaults.
The requester now explicitly authorizes this complete branch/reference migration
and dependency-checked cleanup. Existing Issue #13/#14 work and WGI implementation
remain separate. Applicable context is root/docs AGENTS, README, documentation
index, architecture, delivery plan, the Task77 final/stage reports, workflow and
artifact-retention manuals. The live Issue lookup found no duplicate open task.

## Scope

### Included

- Recheck current remote refs, branch policies, automation, PRs and local consumers.
- Create `master` at the exact integration commits; change defaults, update current
  guidance and any affected automation/open PR targets; integrate documentation PRs.
- Resolve live branch URLs before deleting only old remote `codex/task56` refs.
- Preserve locally checked-out task56 branches and path-bound debug worktrees.

### Excluded

No source/recipe/runtime builds or runs, pin updates, history rewrite, visibility
change, artifact deletion, release/Preview resource update or private-state access.
#47, installations, games, saves, prefixes and debug inputs/outputs stay intact.
Unrelated old publication branches are outside the requested task56 cleanup.

## Design Direction

Reuse Git refs and GitHub default-branch/PR APIs, existing Markdown documents and
Pear's `master` integration convention. No new subsystem code, language or license
decision; retain upstream README text and FEX/DXMT contribution restrictions.
New branch creation is additive first. Deletion follows reviewed document integration
and live consumer checks. Dated records retain their historical ref fields; repair
a historical clickable branch URL with the exact historical commit, without changing
the recorded claim. A default branch is never a substitute for a build/tool SHA.

## Document Location Judgment

| Files | Classification / audience | Selected location | Alternative / reason |
|---|---|---|---|
| Pear README and existing docs index, native guide, supervisor and runtime contracts | Official contributor guidance | Existing README/docs paths | No new guide or manual; keep current discovery and reference paths |
| Four component root READMEs and Wine/DXMT pear/README, FEX Pear/README, runtime docs/development | Component integration guidance | Existing component locations | Preserve upstream sections and established downstream entrypoints |
| Historical split research URL | Dated research | Existing mydocs/tech/20261015_runtime_repository_split.md | Repair one target with exact immutable historical commit; no revised history |
| Plan/reports/board | Task records | Existing mydocs types | Not product documentation; private inventories remain external |

## Expected Changed Files

Pear README.md, docs/README.md, docs/development/rosetta-free.md,
docs/development/runtime-supervisor.md, docs/runtime-contracts.md and the one
historical split-research link. Component files are the eight existing guides
listed above. Automation changes only if an actual task56 dependency is found;
do not enable inherited workflows or change unrelated upstream triggers.
Task artifacts: mydocs/plans/task_m1_79{,_impl}.md,
mydocs/working/task_m1_79_stage{1,2,3}.md,
mydocs/report/task_m1_79_report.md and mydocs/orders/20261021.md.

## Artifact Lifecycle

| Artifact | State / consumers | Identity / retention / release |
|---|---|---|
| Existing debug worktrees, local task56 branches, immutable packs and outputs | Retained dependency; #10/#11/#12 and next WGI work | Original paths, HEAD/status and source/build/tool pins preserved; only owners' later accepted successor can release |
| Old remote task56 refs | Migration input | Exact tip recorded; delete only after master contains tip and live refs/PR/automation resolved |
| New isolated documentation clones and receipts | Task79 review evidence | Small Git-backed text; retain through merge/handoff; no runtime copies |
| Historical source records | Historical evidence | Existing SHA and recorded ref fields unchanged; commit-pinned recovery remains available |

No substantial build or runtime copy: material build-space planning is not
applicable. New sparse clones, a Pear worktree and text receipts have a conservative
512 MiB allowance; filesystem observed 16,239,882,240 available bytes before setup
(`df -k`, local Data volume; concurrent allocations are not attributed).

## Tentative Stages

1. Freeze dependency/ref inventory and exact migration/recovery targets.
2. Create master/defaults and reconcile current docs; verify and commit.
3. Independently review/integrate component docs, retire eligible old remote refs,
   verify public links and protected roots, publish coordinating Pear report PR.

## Verification Plan

Fresh Git/GitHub metadata and full-tree search; check rules/Actions/PR surfaces
before changing defaults. Immediate SHA guards before each mutation. Stage2/3:
diff checks, incremental source-notice guard, original pin/command/upstream/source
preservation, relative and public links, Pear governance and 121 document tests
(new run planned, no prior pass substituted). Independent diff/remote review and
available CI before integration. No runtime/game claim or build revalidation is
needed for unchanged executable bytes. Recheck protected HEAD/branch/status and
local refs; a private-payload full rehash is outside this read-only preservation scope.

## Risks

Inherited workflows may name upstream branches; inspect actual activation and
triggers without enabling them. Unknown downstream clones cannot be enumerated;
document new-work acquisition and recovery while preserving known pinned consumers.
Retained local task56 names are dependencies, not public integration branches.

## Authorization

The requester's instruction to perform the migration, references and cleanup
authorizes this bounded plan and its document locations. Stage checks/reports/
commits remain mandatory; no additional scope or artifact deletion is inferred.
