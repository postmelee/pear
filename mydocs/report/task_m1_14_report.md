# Task #14 partial-delivery reports

GitHub Issue: [#14](https://github.com/postmelee/pear/issues/14)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
PR: [#30](https://github.com/postmelee/pear/pull/30)
Status: preparation-only delivery; **not full #14 completion**. Preserve this record when later reporting full acceptance.

The following original delivery sections retain the PR #30 checkpoint. The October 5 DXMT CI follow-up is recorded separately at the end of this document.

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


## October 5 delivery — Public DXMT Verifier CI

### Work Summary

This second partial delivery covers completed Stages 4/5: isolated scratch-root verification (subsequently integrated by #7) and clean Linux qualification of the existing native/pair synthetic controls. The requester approved this follow-up PR and actual PR-event validation. It does not complete the original maintenance/promotion acceptance criteria or close #14. Stage 6 retains that remaining scope.

### Changed Files and Impact Area

- `.github/workflows/documentation.yml`: two explicit matrix additions under the unchanged nonempty/no-skip contract.
- `tests/dxmt/test_deterministic_pair.py` and `test_deterministic_pair_optional.py`: move optional-input parsing and eight methods into their own discovered module; retain 88 public methods and all original assertions/conditions.
- Existing #14 plans, board, this delivery record and Stage 4/5 artifacts: source-bound evidence and remaining integration/acceptance limits.

The native test file and all runtime/host/validator source are unchanged from merged master. The retained Stage 4 patch documents the fix already integrated by #7; do not apply it again.

### Document Location Verification

All changes follow the approved existing task locations. No official product, contributor, architecture or roadmap document changes. The original preparatory report is preserved above; this appendix is the second delivery, not a replacement full-Issue acceptance report.

### Quantitative Before/After Comparison

| Metric | Before this follow-up | After |
|---|---:|---:|
| Public verifier matrix suites | 5 | 7 |
| Hosted synthetic verifier tests | 196 | 321 |
| Documentation tests | 35 | 35 |
| DXMT pair methods / optional methods | 96 in one file, 8 conditional | 88 public + 8 optional, unchanged total |
| Full local DXMT discovery | 530 | 530 (522 passed, 8 optional skips) |

### Verification Results

| Delivery criterion | Result |
|---|---|
| Reuse already integrated scratch fix | Both after-hashes matched Stage 4 and merged #7; no duplicate implementation |
| Preserve test coverage while separating private controls | All 96 method ASTs/decorators preserved; full local discovery count unchanged |
| Refuse supplied malformed optional input | Optional module fails with JSONDecodeError; public module remains independent |
| Qualify public DXMT controls on Linux | Native 37 + pair 88 passed without unit skips on Ubuntu 24.04/Python 3.12 |
| Preserve prior verifier checks and negative control | All seven suites passed; existing simulated false-success defect detected |

[Stage 4 report](../working/task_m1_14_stage4.md) records the initial alias failure, corrected default/custom-root results and exact target hashes. [Stage 5 report](../working/task_m1_14_stage5.md) records AST preservation, local execution and three hosted qualification runs. Final workflow/test bytes are verified at `357f2265ceef360503768aae2f3d4437ee926987` in [run 37245916919](https://github.com/postmelee/pear/actions/runs/37245916919). Only task documentation changes afterward. Actual follow-up PR-event results must pass before handoff and are recorded in the PR body/checks with their final source and tested merge identities.

### Residual Risks and Follow-up Work

The eight private-input controls remain unperformed in this work and stay in full discovery. Their explicit module IDs now use test_deterministic_pair_optional. Synthetic Linux/macOS success does not qualify native graphics, translated D3D, Steam, Megabonk or distribution. The original #3/#6/#8/#9/#10/#13 acceptance dependencies and maintained patch/promotion work remain. No new Issue is necessary for this follow-up.

### Publication and Review Boundary

The requester authorized this Open PR and its actual PR-event checks. Review its exact final head before a separate merge decision. Keep #14 open and the daily row In progress; no full-Issue completion, release or branch-protection change is authorized by this delivery.
