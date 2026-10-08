# Task #14 Stage 3: Publish the verified preparatory delivery

GitHub Issue: [#14](https://github.com/postmelee/pear/issues/14)
Implementation plan: [task_m1_14_impl.md](../plans/task_m1_14_impl.md)
PR: [#30](https://github.com/postmelee/pear/pull/30)
Stage: 3 — partial publication; full #14 remains open.

## Stage Purpose

Publish completed research/guidance and portable CI as a bounded preparation PR, observe a real pull_request run, and preserve the original maintenance/promotion scope as unapproved Stage 4. The requester explicitly approved this partial-publication exception; no Issue closure or merge follows.

Context used: root/tests rules, task and implementation plans, prior stage reports, PR/report templates and PR command guide. The full-task final-report procedure's Done/Issue-completion actions do not apply to this explicitly scoped partial delivery. Existing report structure is retained with a clear preparation-only status.

## Artifacts

| File | Change Summary |
|---|---|
| mydocs/plans/task_m1_14.md | Current completed/approved/deferred scope and partial-publication location judgment |
| mydocs/plans/task_m1_14_impl.md | Stage 3 publication criteria and retained Stage 4 maintenance/promotion requirements |
| mydocs/orders/20261004.md | Preparation PR status; full Issue remains In progress |
| mydocs/report/task_m1_14_report.md | Preparatory-delivery report, not full #14 acceptance |
| This report / PR #30 body | Real PR-event evidence and explicit remaining limits |

## Body Change Scope / Lossless Preservation

Only internal task documents and PR metadata change in this stage. Existing Stage 1/2 reports retain their historical observations. Workflow, production validators and test implementations match the qualified Stage 2 revision 8ad879ff8a5f73476b533dce33f3f076705c1251. The original broader scope is deferred, not deleted. Product documentation, another worker's files and private build/game data are unchanged.

## Verification Results

Execution context: Ubuntu 24.04 hosted Linux x86_64, Python 3.12.14, Git 2.55.0. Source observation date October 4, 2026, Asia/Seoul. No native runtime or game executes here.

Evidence reuse: the same five existing synthetic suites and unchanged workflow gates were reused. Earlier manual runs remain scoped to their own commits. This stage adds actual PR-event evidence:

- [PR run 37151656150](https://github.com/postmelee/pear/actions/runs/37151656150): event `pull_request`, six jobs successful.
- PR source head: `951dcbd42d0824e7c485583cb8d164a821e95238`.
- Checked-out synthetic PR merge commit reported by all five verifier jobs: `87954f39423fbb0efdc47027900aada388831322`. This is distinct from the source head and is not a merge into master.
- Source inventory 77, report assessment 50, inputs 10, unsigned comparison 40, ABI review 19: **196 passed**, no failures/errors/unit-test skips/expected failures.
- Existing documentation suite: **35 passed**.
- Deliberate-defect control: exact existing assertion failure detected in the isolated process; normal suite passes with the production predicate unchanged.
- PR is Open, non-draft, from codex/publish-task14 to master; closingIssuesReferences is empty.

Commands and inspection:

```bash
python3 -B tools/check_governance.py
git diff --check
gh pr checks 30 --repo postmelee/pear
```

Local governance passes 22 documents/173 local targets. Changed-file and read-only review found no material defect. A temporary extra blank line at EOF was caught by diff --check and removed; it was not treated as a pass. No implementation repair or broader test rerun was needed.

Raw run evidence is in ignored `.build/task14/runs/37151656150/`: run.log SHA-256 `50238c80f1b0b33a1e3853a77f6d16176eb8752bac66b55286cd3fbb9cb09e23`; run.json SHA-256 `992b4bb244c8f69706dbdf8c065d7993c96208850ebc6a0c943564a68b28c34e`. Retain these owned copies through review and preserve necessary evidence before cleanup. Hosted log retention is finite.

This report describes the first real PR execution before the report commit. The publication procedure also requires the final report commit's PR checks to pass; the PR body/checks retain that final head/run association without a circular self-reference in this file.

## Residual Risks

- No merge or required-check branch protection has been performed. New rules are not yet master defaults.
- Full #14 maintenance, incompatible-promotion rejection and final runtime qualification still require original prerequisites and Stage 4 approval.
- DXMT constructor fixes remain with #7; this task did not change its active build candidate.
- The Linux matrix does not establish macOS execution, signing, Steam or game behavior.

## Impact on Next Stage and Approval Boundary

The preparation is ready for requester review once final-head PR checks pass. Keep #14 open even if this partial PR is later merged. Stage 4 needs a refined plan, prerequisite evidence and separate explicit continuation. Merge remains a separate requester decision.
