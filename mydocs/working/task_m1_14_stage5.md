# Task #14 Stage 5 — Linux Qualification for Public DXMT Verifiers

GitHub Issue: [#14](https://github.com/postmelee/pear/issues/14)
Implementation plan: [task_m1_14_impl.md](../plans/task_m1_14_impl.md)
Stage: 5 — complete October 5, 2026; follow-up PR publication pending.

## Stage Purpose

Reuse #7's integrated temporary-root fix and existing synthetic DXMT controls in public Linux CI without treating missing private inputs as passing qualification. The requester explicitly continued after the native-first and optional-test separation recommendation. Full #14 patch maintenance/promotion coverage remains Stage 6, not completed by this delivery.

Context: root/tests rules, existing architecture/delivery/evidence boundaries, #14 Issue and approved plans, Stage 4 report, merged #7 reports and PRs #33/#34, existing workflow and task-stage-report/todo procedures. No graphics implementation or GPU diagnostics change; the Apple tooling skill is not applicable. Reuse Python unittest, existing tests and pinned Actions; no new dependency/framework or upstream code is introduced.

## Artifacts

| File | Change Summary |
|---|---|
| `.github/workflows/documentation.yml` | Add exact native and public-pair matrix entries under the existing strict nonempty/no-skip runner |
| `tests/dxmt/test_deterministic_pair.py` | Retain 88 public methods; move optional inputs and their controls out of public discovery |
| `tests/dxmt/test_deterministic_pair_optional.py` | Preserve eight existing optional methods, conditions and helper bodies for full/local discovery |
| #14 plans, October 5 board, Stage 4 addendum | Record integrated scratch-root fix and current approval/results without overwriting prior evidence |
| This report | Source-bound local/hosted results and remaining limits |

## Body Change Scope / Lossless Preservation

Merged master 7ba7aa9 into codex/task14, resolving the daily-board add/add conflict by retaining both #7 and #14 rows. The #7 scratch fix is already in ea6c018 / PR #33 and both file after-hashes matched Stage 4. Do not reapply its retained historical patch.

Moved MetalControlEnvironment, FixedDirectoryActual and the optional Reuse FEX method to the optional file. The original 96 method ASTs and decorators are exactly preserved as 88 public + 8 optional; the two whole optional classes are AST-identical. The optional file imports the existing portable Temporary helper and source loader rather than duplicating them. Its test module IDs change, but method names/assertions and conditional criteria remain. The native file is unchanged from master. No runtime, tools, host, dependency pins or native fixture changed.

Optional qualification parsing now occurs only in the optional module. Supplied malformed qualification input produces JSONDecodeError there; public-module import succeeds independently. Full test_*.py discovery still finds every optional method. The runner does not dynamically filter skips, and its public no-skip policy is unchanged. Existing contents:read, persist-credentials:false, pinned actions and five earlier suites remain intact. No proprietary game, credentialed prefix, signing material or actual private qualification input is used.

## Verification Results

Local context: Python 3.14.4, macOS 26.5.2, arm64. Hosted context: Ubuntu 24.04 x86_64 image 20260927.320.1, Python 3.12.14, Git 2.55.0. Hosted jobs use runner.temp; local regression used a physical task-owned `scratch with spaces` TMPDIR, with PEAR_TEST_* private overrides cleared. No build, signing, GPU, game or performance run was executed.

Evidence reuse: the Stage 4 path patch and #7 component evidence retain their original identities/scope. The split test layout is newly verified below. Native success is never inferred from these Python controls. Necessary intermediate commits publish the exact sources for remote experiments; the stage report records the completed sequence.

Local commands:

```sh
python3 -B -m unittest discover -s tests/dxmt -p test_deterministic_native.py -v
python3 -B -m unittest discover -s tests/dxmt -p test_deterministic_pair.py -v
python3 -B -m unittest discover -s tests/dxmt -p 'test_*.py' -v
python3 -B tools/check_governance.py
python3 -B -m unittest discover -s tests/docs -p 'test_*.py'
git diff --check
```

| Check | Result |
|---|---|
| Native file | 37 passed, no skips |
| Public pair file | 88 passed, no skips |
| Full DXMT discovery after partition | 530 discovered: 522 passed, the same eight optional-input methods skipped |
| Original method/decorator AST conservation | All 96 preserved exactly, no lost or duplicated methods |
| Supplied malformed qualification | Public import succeeds; optional import fails with JSONDecodeError as required |
| Test scratch cleanup | Owned scratch directory empty after regression |
| Local documentation unit tests | 35 passed |
| Offline governance / task-artifact links / whitespace | Passed; governance checked 24 documents and 211 local targets |

Remote command for each immutable publication checkpoint:

```sh
gh workflow run documentation.yml --repo postmelee/pear --ref codex/publish-task14
```

| Run | Source commit | Verified scope |
|---|---|---|
| [37245670780](https://github.com/postmelee/pear/actions/runs/37245670780) | `eb55fc930afed3b1e1e5d045ed73507616efad0f` | Native-first qualification; 233 verifier + 35 documentation tests, seven jobs |
| [37245822370](https://github.com/postmelee/pear/actions/runs/37245822370) | `6831af6f97ce5ab4dadf7a3e4e74697135a74c6d` | Native + public pair; 321 verifier + 35 documentation tests, eight jobs |
| [37245916919](https://github.com/postmelee/pear/actions/runs/37245916919) | `357f2265ceef360503768aae2f3d4437ee926987` | Final configuration with PR restriction removed; same totals, eight jobs |

All three workflow_dispatch runs succeeded. Final verifier counts: inventory 77, Wine report 50, Wine inputs 10, unsigned comparison 40, ABI review 19, DXMT native 37, DXMT pair 88. Each has positive discovery, equal run count, zero failures/errors/skips/expected failures/unexpected successes. The existing isolated simulated command-status defect was detected in every hosted run. Its one intentional assertion failure is required by the negative control, not a failing workflow. The conditional negative-control step is intentionally omitted in unrelated matrix jobs; this is distinct from skipping unit tests.

The final workflow and test bytes are qualified at 357f226. Only task-report/plan/board text changes after that checkpoint; their local document checks pass separately. This report does not claim an Actions run for its own future commit. Actual follow-up pull_request-event execution and merge remain unperformed.

Raw logs and run metadata are in ignored `.build/task14/runs/<run_id>/` in the #14 worktree; local partition/execution/import-control records are under `.build/task14/runs/stage5-local/`. Retain through follow-up review/integration, then clean only owned copies after preserving required evidence. Final run log SHA-256: `82c2f85b6968195a7afc961d3064c2db107433738e8c28042765009a776b5a5f`.

## Residual Risks

- Eight optional actual-input controls remain unperformed in this work. Full discovery preserves them; public CI intentionally selects only the two public files.
- Linux/Python 3.12 and same-host macOS/Python 3.14 synthetic tests do not establish other platforms or native runtime compatibility.
- The partition changes optional fully qualified test IDs. Callers selecting those classes explicitly must use test_deterministic_pair_optional; standard test_*.py discovery remains compatible.
- The CI addition is on codex/task14/publication branch, not yet merged into master. PR-event validation remains a publication-stage check.

## Impact on Next Stage

Review and publish this bounded #14 follow-up, preserving the merged #7 evidence and the retained Stage 4 record. Verify actual PR-event checks on the publication head before considering merge. Do not close #14: maintained patch provenance/rebase and incompatible runtime/profile promotion still require the original dependencies and Stage 6 approval.

## Approval Request

Stage 5 artifacts and verification are ready for review. Subsequent PR publication and full maintenance/promotion work remain separate approved scopes.
