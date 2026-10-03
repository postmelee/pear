# Task #14: Preserve verification reuse evidence and prepare regression CI

GitHub Issue: [#14](https://github.com/postmelee/pear/issues/14)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

Current state: Stages 1 and 2 are complete. Stage 3 is the requester-approved partial publication of that preparation; Stage 4 retains the original full #14 maintenance/promotion work and is not approved. This PR must not close #14.

## Purpose

Prepare the existing regression/patch-maintenance task without duplicating the active FEX and DXMT integrations. Preserve researched verification practices, improve discovery of reusable work, and classify existing tests before a later CI implementation.

## Background

The requester approved the preceding concrete recommendation in the current Melee research conversation on October 4, 2026: one dated technical note, short agent-rule additions, and evidence reuse/invalidation fields in existing templates. The requester also authorized parallel non-conflicting preparation and conveying useful external research to existing conversations. That initial approval covered Stage 1 only. Subsequent same-thread approvals for Stages 2 and 3 are recorded below; none authorizes full #14 completion.

Read context: root AGENTS, README, docs/README, docs/architecture, docs/delivery-plan, docs/runtime-contracts, document/task/Git workflow manuals, task-start and todo skills, current #14, and #5/#7 latest plans/reports. #14 explicitly permits preparatory research and fixture work before its acceptance dependencies complete. There is no duplicate new Issue.

## Scope

### Included

- Stage 1: dated external-source and local-state research; minimal root guidance and existing template additions; a source-inspected CI candidate inventory; task records.
- Stage 2: qualified five-suite portable CI and temporary-output rules.
- Stage 3: reconcile current status, publish this preparation as an Open PR and inspect real PR-event CI.
- Stage 4 proposal: maintained patch workflow and integrated runtime/promotion coverage after prerequisites.

### Excluded

- Stage 1 changes to workflows, runtime, tools, tests, component pins, product documentation or another worker's files.
- Native builds, runtime/game execution, storage maintenance and dependency installation. Stage 1 made no Linux-success claim; Stage 2 now has recorded hosted evidence.
- New translator/framework, altered #5/#7 acceptance gates, full Issue completion or merge. PR publication was outside Stages 1/2 and is explicitly authorized for Stage 3.

## Design Direction

Reuse Pear's existing validators and unittest entrypoints. Retain Wine/FEX/DXMT and upstream languages. Melee's verifier is design evidence; no external code or full handbook text is copied. Preserve upstream license and contribution-policy distinctions. No Metal implementation is changed, so the Apple-tooling skill is not applicable to this stage.

Inspect active work branches and their immutable checkpoints before new implementation. Reuse evidence only within recorded identities and claim boundaries. Existing stage approvals remain scoped; new guidance does not retroactively invalidate reports or excuse required checks.

## Document Location Judgment

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| Dated research note | Non-normative technical evidence | Contributors/agents | mydocs/tech/20261004_recompilation_and_verification_reuse.md | docs/research/ | Dated alternatives and CI readiness, not a new product contract |
| AGENTS.md additions | Existing agent rules | Agents | AGENTS.md | CLAUDE.md | Keep one rules entrypoint; avoid duplicated instructions |
| Task/implementation/stage template additions | Operating templates | Task authors | mydocs/_templates/ | New skill | Extend existing verification sections without adding a workflow |
| Plans, board and stage report | Issue work artifacts | Requester/workers | Existing mydocs folders | docs/ | Preserve task scope and evidence outside product documentation |

Locations and bounded document changes follow the requester's accepted recommendation. No official document is added, moved or edited.

## Expected Changed Files

New: the dated technical note; mydocs/plans/task_m1_14.md; mydocs/plans/task_m1_14_impl.md; mydocs/orders/20261004.md; mydocs/working/task_m1_14_stage1.md.

Modified: AGENTS.md; mydocs/_templates/task_plan.md; mydocs/_templates/task_impl_plan.md; mydocs/_templates/stage_report.md.

The daily board is branch-local. Preserve other workers' rows during eventual integration; do not copy their volatile status as this branch's authoritative state.

## Tentative Stages

1. Preserve research and bounded guidance: complete; Stage 1 report retained.
2. Qualify five portable suites on hosted Linux and connect CI: complete; Stage 2 report retained.
3. Publish and verify the preparatory delivery: approved October 4; no merge or Issue closure.
4. Complete maintained patch/provenance and promotion coverage after #3/#6/#8/#9/#10/#13 evidence and separate approval.

## Verification Plan

Stage 1: run `python3 -B tools/check_governance.py`, `git diff --check`, inspect changed-file boundaries and relative links in new task artifacts using the existing link parser. Record actual Python/platform. This is documentation verification only; no new test is justified for two prose rules.

Stage 2: 196 selected verifier tests and 35 documentation tests passed in both recorded workflow_dispatch runs; the bounded mutation control detected the simulated defect. Stage 3 must inspect a real pull_request run, the final head and check conclusions. Stage 4 remains unapproved and unperformed.

Integrated acceptance retains #14's failing-fixture detection, incompatible-promotion rejection and traceable revision/coverage criteria. Full dependency evidence is required for Issue completion.

## Risks

- Active #5/#7 share Wine patch integration obligations despite limited path overlap; their owner retains implementation control.
- Native build/storage coordination belongs to #5/#7. This task does not interrupt their operations; its Linux tests use hosted runners.
- Portable labels do not prove Linux compatibility; platform wheels, hardcoded paths and private fixtures need inspection and actual testing.
- Handbook synthetic tests and original PPC hashes do not establish ARM64 gameplay equivalence.

## Approval Record and Later Approval Boundary

Each stage follows its own same-thread continuation. The Stage 1 and Stage 2 reports preserve their historical approval boundaries; the current Stage 3 approval below does not retroactively authorize any unperformed runtime work.

## October 4 Stage 2 approval and location refinement

After the Stage 1 report and a concrete recommendation to refine temporary-output rules, qualify five master-only suites on Linux, coordinate DXMT fixes with #7, and connect only passing suites to CI, the requester explicitly said to proceed in this thread. At that checkpoint Stage 2 was approved and later work was not. The separate Stage 3 approval below now supersedes that proposed publication status. Earlier Stage 1 exclusions describe that completed stage, not this approval.

Stage 2 may modify tests/AGENTS.md and the existing .github/workflows/documentation.yml, plus these task plans, the daily board and a Stage 2 report. No production validator/test implementation, #5/#7 file or dependency lock is changed. tests/AGENTS.md is scoped agent policy; the workflow is automation configuration. Neither is a new product document. The stage report stays in mydocs/working/task_m1_14_stage2.md. These locations implement the approved recommendation without a new policy manual.

Five candidates: source inventory; Wine report assessment, input validation, unsigned comparison and ABI review. Use existing Python unittest with no package installation. The current local Docker daemon is unavailable; qualify in GitHub's clean Ubuntu 24.04/Python 3.12 hosted jobs instead of starting a competing VM. Initially restrict the new job to workflow_dispatch on the task publication branch; only after positive and negative-control evidence passes enable the PR trigger. Existing documentation checks continue unchanged. Source commits, runner/image identity, Python/Git versions, executed counts/skips, run URLs and control behavior must be recorded.

## October 4 Stage 3 partial-publication approval

The requester explicitly said to proceed after the proposal to reconcile this plan, publish only the completed preparatory work, and verify actual PR-event CI. The original unapproved maintenance/promotion stage is retained as Stage 4 rather than discarded. This approved partial delivery is an explicit exception to the usual one-final-PR/whole-Issue completion procedure: no closing keyword, Issue closure, Done status for all #14, merge or branch-protection change is authorized.

New artifacts are mydocs/working/task_m1_14_stage3.md and mydocs/report/task_m1_14_report.md. The latter is explicitly a preparatory-delivery report, not the final acceptance report for all #14; future full completion must preserve this historical delivery record. Both locations are internal task evidence covered by the approved preparation/report placement. Reuse the existing PR and report templates, retaining their verification/result structure without asserting full-Issue completion. Keep the daily #14 row In progress with a clear preparation-PR note.

Stage 3 changes only plans/reports/board and the PR description. Preserve workflow and test implementation bytes qualified in Stage 2. Verify local governance, document links and whitespace, then publish from codex/publish-task14 to master. Inspect actual pull_request run identity (including the tested merge ref versus PR source head), all six jobs and the deliberate-defect control. Record source/run IDs and coverage limits. A final documentation-only report commit must also receive successful PR checks before delivery.
