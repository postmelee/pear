# Task #14: Preserve verification reuse evidence and prepare regression CI

GitHub Issue: [#14](https://github.com/postmelee/pear/issues/14)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

## Purpose

Prepare the existing regression/patch-maintenance task without duplicating the active FEX and DXMT integrations. Preserve researched verification practices, improve discovery of reusable work, and classify existing tests before a later CI implementation.

## Background

The requester approved the preceding concrete recommendation in the current Melee research conversation on October 4, 2026: one dated technical note, short agent-rule additions, and evidence reuse/invalidation fields in existing templates. The requester also authorized parallel non-conflicting preparation and conveying useful external research to existing conversations. This approval covers the bounded Stage 1 below; it does not authorize all of #14 or any later stage.

Read context: root AGENTS, README, docs/README, docs/architecture, docs/delivery-plan, docs/runtime-contracts, document/task/Git workflow manuals, task-start and todo skills, current #14, and #5/#7 latest plans/reports. #14 explicitly permits preparatory research and fixture work before its acceptance dependencies complete. There is no duplicate new Issue.

## Scope

### Included

- Stage 1: dated external-source and local-state research; minimal root guidance and existing template additions; a source-inspected CI candidate inventory; task records.
- Later proposed scope: isolated portable CI and dependency qualification; maintained patch workflow and integrated runtime/promotion coverage after prerequisites.

### Excluded

- Stage 1 changes to workflows, runtime, tools, tests, component pins, product documentation or another worker's files.
- Native builds, runtime/game execution, storage maintenance, dependency installation and claims of Linux test success.
- New translator/framework, altered #5/#7 acceptance gates, Issue completion, PR publication or merge.

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

1. Preserve research and bounded guidance; source-review CI candidates. Approved scope for this turn.
2. Qualify a small explicit portable suite on clean Linux and add appropriate CI after separate approval. Exact files, runner/dependency identities and commands must be specified before implementation.
3. Complete maintained patch/provenance and promotion regression coverage after #3/#6/#8/#9/#10/#13 evidence, separate plan refinement and approval. Stage 1 does not close #14.

## Verification Plan

Stage 1: run `python3 -B tools/check_governance.py`, `git diff --check`, inspect changed-file boundaries and relative links in new task artifacts using the existing link parser. Record actual Python/platform. This is documentation verification only; no new test is justified for two prose rules.

Stages 2/3: not approved or performed. Plan actual Linux negative-control results, safe fixture dependencies, coverage limits and later matched runtime/promotion evidence before enabling gates.

Integrated acceptance retains #14's failing-fixture detection, incompatible-promotion rejection and traceable revision/coverage criteria. Full dependency evidence is required for Issue completion.

## Risks

- Active #5/#7 share Wine patch integration obligations despite limited path overlap; their owner retains implementation control.
- Storage cleanup currently takes priority over native build/verification. Stage 1 reads source and checks small documents only.
- Portable labels do not prove Linux compatibility; platform wheels, hardcoded paths and private fixtures need inspection and actual testing.
- Handbook synthetic tests and original PPC hashes do not establish ARM64 gameplay equivalence.

## Approval Record and Later Approval Boundary

The current same-thread instruction to proceed adopts the preceding research-note/rules/template proposal and non-conflicting preparation. This plan records that bounded approval rather than asking for it again. Later Stage 2/3 details are proposals, not blanket authorization. Request explicit continuation after the Stage 1 report, with a concrete Stage 2 plan.
