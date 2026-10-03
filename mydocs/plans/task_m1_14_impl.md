# Task #14 implementation plan

Task plan: [task_m1_14.md](task_m1_14.md)
GitHub Issue: [#14](https://github.com/postmelee/pear/issues/14)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Preserve reuse evidence and CI readiness | Dated note and minimal rules/templates | Offline document checks and source review |
| 2 | Qualify and connect a portable subset | Explicit five-suite CI and scoped temp policy | Clean Linux positive/negative execution; approved October 4 |
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

## Stage 3 - Maintenance and promotion coverage (proposal)

Refine after the relevant #3/#6/#8/#9/#10/#13 outcomes exist. Bind candidate/source/test revisions and retain patch provenance, rebase conditions and contribution limits. Qualify incompatible promotion rejection without exposing game/account/signing data. Do not close #14 based on portable CI alone.

## Stage Dependencies, Risks and Approval Boundary

Stage 1 uses the requester's same-thread approval of the concrete prior document proposal. Later stages require a refined plan and explicit continuation after the current stage report. Current #5/#7 owners keep their own scopes and storage ordering. Linux availability and CI results are not checked; all candidate lists remain source-inspection findings.

Stage 2 approval supersedes only its former proposed status; Stage 3 continues to require refined scope and explicit approval.
