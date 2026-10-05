# Task #14 implementation plan

Task plan: [task_m1_14.md](task_m1_14.md)
GitHub Issue: [#14](https://github.com/postmelee/pear/issues/14)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Preserve reuse evidence and CI readiness | Dated note and minimal rules/templates | Offline document checks and source review |
| 2 | Qualify and connect a portable subset | Explicit five-suite CI and scoped temp policy | Clean Linux positive/negative execution; approved October 4 |
| 3 | Publish the preparatory delivery | Scoped Open PR and delivery reports | Actual PR-event checks and final-head identity; approved October 4 |
| 4 | Validate isolated DXMT scratch-root portability | Source patch, preserved snapshot and local results | Approved October 5; two files, default/custom roots |
| 5 | Qualify and connect public DXMT suites | Explicit native/pair CI entries and optional-input separation | Approved October 5; native-first hosted qualification |
| 6 | Complete maintenance and promotion coverage | Proposed patch/qualification CI | #14 prerequisite and candidate evidence; not approved |

## Document Location Check

Stage 1 uses exactly the task plan's AGENTS.md, mydocs/tech, mydocs/_templates, plans, orders and working locations. No product document is created or changed. Stage 2 locations and commands were approved and executed. Stage 3 adds only the internal stage/delivery reports described in the task plan and updates plans/board. Stages 4/5 use the later explicit approvals below; full maintenance/promotion remains Stage 6.

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

## Stage 2 - Qualify and connect a portable subset

Approval: explicit same-thread continuation on October 4 after the concrete temporary-output/Linux proposal. Use the task plan's appended scope/location refinement; no prior approval is expanded retroactively.

### Artifacts and changes

- tests/AGENTS.md: forbid OS-specific temporary-root hardcoding in portable tests; retain automatic cleanup; distinguish task/run-owned retained evidence and its input/command/result/location references. Allow documented platform exceptions and synthetic path literals.
- .github/workflows/documentation.yml: reuse pinned checkout/setup-python actions and Ubuntu 24.04/Python 3.12. Add five isolated matrix entries: tests/sources/test_inventory.py and tests/wine/test_verification.py, test_inputs.py, test_unsigned_compare.py, test_abi_review.py. Start manual-only; enable PR execution only after a passing clean hosted experiment.
- Existing unittest discovery/runner within each job: require a positive test count, success and no skips/expected failures/unexpected successes. Each suite runs in a separate process/job to avoid module-name collisions. No new test framework, runtime build, proprietary input or dependency installation.
- One bounded control reuses test_success_label_is_not_required_or_sufficient_evidence. In a separate process, temporarily ignore only the command_did_not_pass predicate through unittest.mock, then require that the existing assertion fails exactly once without errors/skips. Production files stay unchanged. This proves detection of that synthetic defect, not arbitrary regression coverage.
- Record runner/source identity and results in hosted logs and job summaries. Download logs to the ignored, task-owned .build/task14 directory with run-specific names; put sanitized results/URLs in the Stage 2 report.
- Send the /private/tmp recommendations to #7's owner. Do not edit its active candidate or treat the handoff as a completed fix.

### Verification

Run manual Actions on codex/publish-task14 with immutable head recorded:

```bash
gh workflow run documentation.yml --repo postmelee/pear --ref codex/publish-task14
```

Inspect the exact returned/listed run source SHA, runner, jobs and logs. All five suites and the narrow failure-detection control must pass; zero tests, skips, errors or an undetected simulated defect fail the experiment. If a candidate exposes a platform assumption, preserve the failure and repair only within approved scope or leave the gate incomplete; do not silently omit it.

After the manual experiment passes, enable the job for the existing pull_request event and manually rerun the final configuration at its new source SHA. PR-event execution itself remains unperformed until a PR is opened; do not infer it from workflow_dispatch.

Local checks:

```bash
python3 -B tools/check_governance.py
git diff --check
```

Review the exact matrix, job permissions, expected-failure control, scoped-rule wording and changed-file ownership. Preserve docs job behavior, contents:read and persist-credentials:false. Whole #14 completion and promotion qualification remain outside this stage.

### Commit

Use Task #14 [Stage 2.N] checkpoints for required remote experiments, then bundle final configuration/report in Task #14 Stage 2: qualify portable verifier CI and temporary-output rules.

## Stage Dependencies, Risks and Approval Boundary

Stages 1/2 used their recorded explicit approvals and are complete. Stage 2 superseded its earlier source-inspection-only Linux status with two successful hosted executions. Stage 3 has now been explicitly approved for partial publication; Stage 4 remains proposed. #5/#7 owners keep their own scopes and operating order.

The Stage 2 approval did not authorize later work. The separate Stage 3 continuation below now authorizes only publication of the completed preparation.

## Stage 2 first hosted experiment

Run [37149720472](https://github.com/postmelee/pear/actions/runs/37149720472) succeeded on a3fdb7345c0881d4249b5e46ef455bd411f7009c. Ubuntu 24.04 image 20260927.320.1, x86_64, Python 3.12.14, Git 2.55.0. Counts: inventory 77, report 50, inputs 10, unsigned comparison 40, ABI review 19; total 196, no skips/failures/errors. Existing documentation tests: 35. The isolated simulated false-success defect produced exactly the expected test failure and nonzero child exit; the control passed. Production sources/tests were unchanged. This first result enabled the PR trigger as planned; final configuration validation subsequently passed in run 37149821735.

Original logs and run metadata: ignored .build/task14/runs/37149720472/. Hosted source/run links remain public; local copies retain transient execution details. Preserve through review, then clean only owned copies after confirming needed evidence is retained.

Stage 2 completed with final hosted run [37149821735](https://github.com/postmelee/pear/actions/runs/37149821735); see the [Stage 2 report](../working/task_m1_14_stage2.md). The original unapproved maintenance/promotion scope is now Stage 4.

## Stage 3 - Publish the preparatory delivery

Approval: requester explicitly continued after the partial-PR and actual PR-event verification proposal. See the task plan's partial-publication exception and report-location judgment. Do not merge, close #14 or start Stage 4.

### Changes

Reconcile stale current-status prose while preserving historical stage reports. Prepare the Open PR using the existing template, without a closing keyword. After its first real pull_request checks pass, write the Stage 3 and preparatory-delivery reports, update the board, commit them together, refresh SHA-pinned PR links, and require successful checks on that final head. Only task documents change in this stage; previously qualified workflow/validator bytes are reused unchanged.

### Verification

```bash
python3 -B tools/check_governance.py
git diff --check
gh pr checks <created-pr-number> --repo postmelee/pear
```

Additionally inspect actual PR head/base, changed-file scope, workflow event/source versus tested merge ref, all six job results, the five nonempty/no-skip suite counts and mutation control. Use existing link_targets for newly changed work-document links. Compare the workflow, tools and test implementation paths with 8ad879ff8a5f73476b533dce33f3f076705c1251; no implementation changes are expected. Preserve hosted run/log metadata under ignored .build/task14/runs/<id>.

### Reports and commit

Write mydocs/working/task_m1_14_stage3.md and mydocs/report/task_m1_14_report.md, with explicit preparatory-delivery-only status and remaining #14 dependencies. Stage 3 publication is complete only when the Open PR is reviewable and final-head checks pass. The report commit describes the first PR execution; the PR body links final-head CI without requiring a self-referential report commit.

Commit: Task #14 Stage 3: publish the verified preparatory delivery.

## Stage 6 - Maintenance and promotion coverage (original Stage 4 proposal)

Refine after the relevant #3/#6/#8/#9/#10/#13 outcomes exist. Bind candidate/source/test revisions and retain patch provenance, rebase conditions and contribution limits. Qualify incompatible promotion rejection without exposing game/account/signing data. Do not close #14 based on portable CI alone.


## Stage 4 - Isolated DXMT temporary-root follow-up

Approved October 5 in this thread, superseding earlier current-stage numbering; historical approvals retain their original scope. Follow the task plan's new snapshot/placement boundaries. Preserve all 503 selected #7 files and their original hashes before edits. The source HEAD alone is insufficient because the completion changes are uncommitted.

Implement the two constructor changes in the independent candidate, resolving each newly created owned root with Path.resolve(strict=True) if the platform default contains aliases. Run the existing pair and native unittest files separately, using a fresh process for each of default TMPDIR selection and explicit physical scratch with spaces. Clear PEAR_TEST_* private-source/input overrides for this synthetic pass. Use unittest discovery and retain the exact discovered/run counts, failures/errors, expected/unexpected outcomes and skipped IDs. The known eight optional pair methods remain unperformed; any new skip or count discrepancy needs investigation. Verify created TemporaryDirectory instances actually use the selected root and are removed by suite completion without altering the constructors' arguments or cleanup behavior in the validation harness. Retain logs and failure details in the owned run directory.

Validate that only the four intended helper lines differ between baseline and candidate, run git apply --check against the preserved baseline, parse changed Python and rehash the owner's selected source files. Run python3 -B tools/check_governance.py and git diff --check in codex/task14. Use the existing link_targets parser for new report/plan relative links. Record any failed first attempt and subsequent correction; do not rewrite failures as passes. Package the validated patch and Stage 4 report together in a stage commit; the local snapshot is not committed. No PR publication or remote CI is part of this approval.


## Stage 5 - Linux qualification and CI connection

October 5 approval and locations are recorded in the task plan. Integrate master 7ba7aa9, preserve both daily board rows, and confirm the two test files match the previously qualified patch's after hashes. Append Stage 4 integration evidence rather than altering its historical execution report.

First add native as a new matrix entry guarded to workflow_dispatch at the suite steps; remote-qualify the untouched 37-test file. Next move the two optional classes and one optional Reuse method from the pair file into test_deterministic_pair_optional.py. Retain each test method AST/decorators and class helper bodies; import the existing portable helper rather than duplicate it. Move optional input parsing into the optional file so public CI does not require private inputs. Confirm total discovery is conserved (pair 88 + optional 8 + native 37); eight optional methods remain skipped without private inputs, not silently discarded. Compare before/after ASTs and discover IDs, and run the two public suites separately with no skips. Run full DXMT discovery once after the split to detect import-order/alias regressions; private controls remain explicitly unperformed.

Test malformed supplied qualification input: public pair discovery must be independent; optional discovery must fail instead of treating supplied bad input as absent. This is a bounded existing-module import control, no new framework. All logs use ignored task/run paths.

Add pair as manual-only and run the complete existing workflow on Ubuntu 24.04/Python 3.12. Require native 37 and pair 88, positive test counts, no skips/expected failures, existing mutation control and all prior checks. Keep original failure records if anything fails and fix only in scope. After successful qualification, remove the new-suite manual-only restrictions, repeat the final configuration hosted check, and record source SHA, run IDs, image/Python/Git and per-suite counts. Preserve contents:read and pinned actions. No private optional controls are in the public matrix.

Local checks: python3 -B tools/check_governance.py, python3 -B -m unittest discover -s tests/docs -p 'test_*.py', git diff --check, and existing link_targets for changed task artifacts. Bundle final implementation and Stage 5 report in one stage completion commit after hosted verification, retaining necessary intermediate remote experiment checkpoints. Full #14 remains open; PR publication and Stage 6 need their subsequent approval.


### Stage 5 completion

Native-first hosted run 37245670780 passed at eb55fc930afed3b1e1e5d045ed73507616efad0f. Combined qualification run 37245822370 passed at 6831af6f97ce5ab4dadf7a3e4e74697135a74c6d. Final PR-enabled configuration run 37245916919 passed at 357f2265ceef360503768aae2f3d4437ee926987: 321 synthetic verifier tests, 35 documentation tests and the existing deliberate-defect control; no unit skips. Local complete DXMT discovery retained 530 tests (522 passed, eight optional-input skips). See the Stage 5 report for actual commands, preservation checks and limitations. Only task documents change after the final hosted source checkpoint; actual follow-up PR-event execution is not claimed.


### Stage 5 publication continuation

Approved explicitly after the Stage 5 report. Append this bounded delivery to mydocs/report/task_m1_14_report.md and retain prior evidence. Publish an Open follow-up PR to master without closing #14. Before handoff, inspect actual pull_request CI, match the tested merge ref parents to the PR base/head, and require eight successful jobs with 321 verifier tests, 35 documentation tests, zero unit skips and the existing controlled-defect detection. Download final run/log metadata under ignored .build/task14/runs/<id>. The PR body records final-head evidence; no merge is authorized.
