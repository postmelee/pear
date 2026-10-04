# Task #14 preparatory-delivery report

GitHub Issue: [#14](https://github.com/postmelee/pear/issues/14)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
PR: [#30](https://github.com/postmelee/pear/pull/30)
Status: preparation-only delivery; **not full #14 completion**. Preserve this record when later reporting full acceptance.

## Work Summary

Three preparation/publication stages preserve external reuse research, introduce minimal evidence-discovery/reuse and temporary-output guidance, qualify five existing synthetic verifier suites on Linux, and publish an Open PR. The requester approved this partial delivery explicitly. The original maintenance/promotion scope remains Stage 4 and #14 stays open.

## Changed Files and Impact Area

| Path | Change Summary | Impact Area |
|---|---|---|
| .github/workflows/documentation.yml | Five matrix suites and isolated false-success detection control; strict count/skip gates | Synthetic regression CI |
| AGENTS.md / tests/AGENTS.md | Active-work discovery, bounded evidence reuse, portable scratch and retained evidence | Agent/test guidance |
| mydocs/_templates/ | Small evidence reuse/invalidation prompts in three existing templates | Existing task workflow |
| mydocs/tech/20261004_recompilation_and_verification_reuse.md | Dated external research and reuse/CI-readiness findings | Non-normative evidence |
| Task plans, reports and daily board | Stage approvals, source/run identities, remaining full-Issue scope | Internal delivery evidence |

No production runtime, validator implementation or test body is changed. No new test framework or dependency installation is introduced.

## Document Location Verification

All actual paths match the approved judgments in the task plan. Rules stay at existing agent entrypoints, reusable research stays in mydocs/tech, and task evidence stays in mydocs/plans, working, report and orders. No official product document or second roadmap is added. This report uses the existing final-report format for the authorized preparatory slice only; the full Issue is not marked Done.

## Quantitative Before/After Comparison

| Metric | Before | After in this PR |
|---|---|---|
| Selected verifier suites exercised by the workflow | 0 | 5, totaling 196 tests |
| Existing documentation tests | 35 | 35 retained |
| False-success control for this verifier matrix | None | Existing test detects an isolated command-status predicate defect |
| Portable suite empty/skip handling | No portable job | Empty, count mismatch, skip, expected failure or unexpected success fails |

## Verification Results

| Preparatory acceptance criterion | Result |
|---|---|
| Preserve useful researched evidence without a new framework | Met: dated note and existing validator/test reuse |
| Make discovery/evidence rules concise and scoped | Met: minimal root/test rules and template prompts |
| Execute the selected suites on clean Linux | Met: two manual runs and an actual PR-event run; 196 verifier + 35 docs tests per run |
| Detect the bounded simulated false-success defect | Met: exact assertion failure and nonzero child exit; ordinary suite passes |
| Publish a bounded Open PR without completing #14 | Met: PR #30, no automatic-closing reference; final-head checks required before handoff |

### Stage Verification Results

- [Stage 1](../working/task_m1_14_stage1.md): source investigation and document checks; no Linux claim at that stage.
- [Stage 2](../working/task_m1_14_stage2.md): manual hosted qualification and final workflow configuration; no PR-event claim at that stage.
- [Stage 3](../working/task_m1_14_stage3.md): actual PR event, source head versus tested merge commit, publication scope and retained evidence.

Latest reportable PR evidence at report creation: [run 37151656150](https://github.com/postmelee/pear/actions/runs/37151656150). The PR body/checks record the subsequent final report commit's own CI result. Report-only changes reuse unchanged workflow/validator/test inputs and do not claim runtime equivalence.

## Residual Risks and Follow-up Work

### Residual Risks

- The full #14 acceptance criteria are not met by synthetic CI. Maintained patch/rebase rules, incompatible runtime/profile promotion rejection and coherent candidate reporting remain.
- Original dependencies #3/#6/#8/#9/#10/#13 still apply to full completion; their completion must be assessed from appropriate evidence.
- The macOS-specific contract dependency lock and broader FEX/DXMT test portability remain outside this PR.
- #7 retains ownership of its temporary-root follow-up and active build candidate.
- No branch-protection setting, merge, source/runtime release or Rosetta-free gameplay support is claimed.

### Follow-up Candidates

No duplicate Issue is proposed. Continue the retained Stage 4 scope under #14 when its inputs and approval exist; coordinate component fixes with their existing Issues.

## Requester Review Boundary

Review the preparatory PR and its final-head CI. Merging is a separate decision, and #14 must remain open after any partial merge. Do not start Stage 4 or close the Issue based on this report.
