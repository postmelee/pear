# Task #14: Preserve verification reuse evidence and prepare regression CI

GitHub Issue: [#14](https://github.com/postmelee/pear/issues/14)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

Current state: Stages 1–5 are complete. PR #30 and the DXMT follow-up PR #35 are merged; #7 already integrated the Stage 4 scratch-root fix. Actual PR #35 CI passed on its final head. The original maintenance/promotion proposal remains Stage 6 and is unapproved. Full #14 remains open.

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


## October 5 Stage 4 approval: isolated DXMT temporary roots

The requester explicitly authorized notifying the successful #7 session and following the proposed sequence: preserve its final working source/reports, refresh the two-test patch, run affected default/custom-root tests and record separate #14 evidence. The #7 owner has intentionally left its completion changes uncommitted. Preserve that decision and its worktree. Continue on existing codex/task14, fast-forwarded to master abaabc2; no #7 source integration, commit, push, PR or Issue closure is included.

Use a local snapshot of #7 tracked working files plus its five named public completion files, with every file hashed and reread to detect concurrent changes. Retain an unchanged baseline and independent candidate under ignored .build/task14/runs/20261005-dxmt-temp-portability in the main workspace. No private build payload, credential, signing material or diagnostic capture is copied. Apply only the two TemporaryDirectory fixed-root removals and physical resolution of their newly created owned roots to the candidate. Reuse existing unittest bodies and cleanup; leave synthetic path literals and producer/verifier bytes unchanged. Record original and modified hashes, Python/platform, exact skipped IDs, counts, command exit status and scratch cleanup. Run each affected file in a fresh Python process with default temp selection and a physical run-owned TMPDIR containing spaces. Inspect and resolve any path alias problem without weakening refusal predicates. No whole native rebuild or GPU execution is warranted.

Placement: existing task/implementation plans and the October 5 daily board record authorization and ownership; mydocs/working/task_m1_14_stage4.md records results. Store the small reviewable source delta as mydocs/working/task_m1_14_stage4.patch because its #7 target files are not yet integrated in master. Private/local detailed manifests and logs stay ignored. These are internal task evidence locations, not official product documentation. The patch is an integration artifact, not a claim that master or the #7 worktree has changed. Recheck target hashes after #7 publication before applying it to tracked tests; do not import the entire uncommitted #7 implementation into this branch.

The original proposed Stage 4 maintenance/promotion work remains intact as Stage 5. Hosted Linux qualification and no-skip CI selection remain follow-up work. Local conditional skips are explicit unperformed observations. Existing native #7 success is referenced only as its original scope and never relabeled as a new #14 result.


## October 5 Stage 5 approval: qualify DXMT suites on Linux

After confirming #7 CLOSED and PRs #33/#34 merged, the requester explicitly said to proceed with updating #14 integration records, Linux qualification and CI connection. This approves the native suite first and then separation/qualification of the pair suite's public tests. Preserve eight optional actual-input tests, with unchanged bodies and selection conditions, in a separate test file. Retain tempfile fixes already integrated by #7; do not reapply the patch or rerun native qualification.

Use the existing pinned Ubuntu 24.04/Python 3.12 workflow, runner and no-skip contract. Add the native suite as manual-only until its hosted run passes; then add the public pair suite as manual-only and qualify the combined workflow before enabling new PR jobs. Existing five suites and documentation remain enabled. Use the publication branch for explicit workflow_dispatch experiments; a source commit is required for each remote experiment. Actual PR creation/merge and full #14 closure remain separate checkpoints. No production runtime/verifier code, private input, toolchain pin or security setting changes.

Locations: existing workflow, tests/dxmt/test_deterministic_pair.py and new tests/dxmt/test_deterministic_pair_optional.py, existing plans/board, and mydocs/working/task_m1_14_stage5.md. These are test/automation implementation and internal task evidence, not new official product documentation. Preserve the historical Stage 4 report and append the integration outcome. Record immutable source/run identities and limitations; original raw logs stay ignored in task/run-owned output. The original maintenance/promotion scope is Stage 6 rather than discarded.


## October 5 approval: publish the verified DXMT CI follow-up

The requester explicitly continued after the completed Stage 5 delivery and the proposal to create a follow-up PR and verify actual pull_request-event CI. This approves publication of Stages 4/5 and their internal delivery record only. Preserve the earlier PR #30 report and append this second partial delivery to the existing report path. The final-report procedure is adapted to this authorized partial scope: #14 remains In progress/Open, with no closing keyword, merge, branch-protection change or Stage 6 implementation.

Use the existing template and SHA-pinned work-document links. Before publication, verify source/test/workflow bytes still match the qualified checkpoint, check new task links/governance/whitespace and commit the delivery documents. The actual PR-event source head, tested synthetic merge commit, all eight checks, nonempty/no-skip counts and deliberate-defect detection must be confirmed before handoff. Record those final source/run identities in the PR body/checks, avoiding a self-referential report commit. A new report-head source change would require renewed relevant checks. No official product document is changed.


## October 5 review, merge and cleanup authorization

The requester authorized review and, absent issues, merge plus follow-up cleanup. Review found no actionable defect: all 96 pair method/decorator ASTs were preserved, repository callers did not reference moved optional IDs, and final-head PR CI passed. PR #35 merged as 9fe70d39089c41ac2b4cb81163dbd772226ca9c8 at 09:29 KST. Keep #14 Open/In progress; this partial merge does not satisfy Stage 6.

Apply post-merge cleanup only to this completed delivery's branches/checkouts. Before archival, copy and hash-verify ignored Task #14 logs into the main workspace's .build/task14/retained/20261005-pr35/build/ (36 files, 2,766,626 bytes); its sibling manifest.json records each hash. Existing main-workspace Stage 4 snapshots remain unchanged. Preserve #5/#7 worktrees and all other workers' inputs. Publish these status/retention updates as a documentation-only cleanup PR, then archive the managed #14 worktree and remove merged work/publication branches after confirming master contains the cleanup commit. No Stage 6 implementation, Issue closure or private evidence deletion is authorized by this cleanup.
