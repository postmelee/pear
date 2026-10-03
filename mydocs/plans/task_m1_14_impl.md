# Task #14 implementation plan

Task plan: [task_m1_14.md](task_m1_14.md)
GitHub Issue: [#14](https://github.com/postmelee/pear/issues/14)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Preserve reuse evidence and CI readiness | Dated note and minimal rules/templates | Offline document checks and source review |
| 2 | Qualify and connect a portable subset | Proposed explicit CI suite | Clean Linux positive/negative execution; not approved |
| 3 | Complete maintenance and promotion coverage | Proposed patch/qualification CI | #14 prerequisite and candidate evidence; not approved |

## Document Location Check

Stage 1 uses exactly the task plan's AGENTS.md, mydocs/tech, mydocs/_templates, plans, orders and working locations. No product document is created or changed. Stage 2/3 location and command details require refinement and approval first.

## Stage 1 - Preserve reuse evidence and CI readiness

### Artifacts

- mydocs/tech/20261004_recompilation_and_verification_reuse.md
- AGENTS.md: active-work discovery and bounded evidence reuse, with a non-normative research link.
- mydocs/_templates/task_plan.md, task_impl_plan.md and stage_report.md: small evidence-reuse prompts within existing verification sections.
- Current task plans, daily board and stage report.

### Changes

Follow the approved preceding proposal and the task plan's context. Record immutable #5/#7 checkpoints, avoid copying private diagnostics, and keep research distinct from runtime qualification. Preserve current approval gates and existing framework attribution. Review template-consuming skills and template index; unchanged section structure requires no new skill or index entry.

### Verification

Run from the isolated task worktree with available Python 3; record its actual version. No package installation, build, runtime test or CI execution is required.

```bash
python3 -B tools/check_governance.py
git diff --check
```

Additionally use the existing `tools.check_governance.link_targets` parser to inspect new/changed non-template Markdown local targets. Inspect `git diff --name-only master` and confirm only the planned document paths changed. Record parser limits (not a full Markdown/remote-link verifier), results, base commit and final stage commit. Small documentation inspection does not acquire or alter another worker's native build/storage lock.

### Commit

`Task #14 Stage 1: preserve verification reuse guidance and CI readiness`

## Stage 2 - Qualify and connect a portable subset (proposal)

Before requesting approval, define an explicit master-only test list, clean Linux/Python identities, fixture failure behavior and skip handling. Reuse unittest; no new runner. Resolve contract-wheel locking separately. Avoid loading unpublished worktrees/private .build inputs. Only tested commands may be proposed for workflow integration. No Stage 2 execution or workflow change is authorized by Stage 1.

## Stage 3 - Maintenance and promotion coverage (proposal)

Refine after the relevant #3/#6/#8/#9/#10/#13 outcomes exist. Bind candidate/source/test revisions and retain patch provenance, rebase conditions and contribution limits. Qualify incompatible promotion rejection without exposing game/account/signing data. Do not close #14 based on portable CI alone.

## Stage Dependencies, Risks and Approval Boundary

Stage 1 uses the requester's same-thread approval of the concrete prior document proposal. Later stages require a refined plan and explicit continuation after the current stage report. Current #5/#7 owners keep their own scopes and storage ordering. Linux availability and CI results are not checked; all candidate lists remain source-inspection findings.
