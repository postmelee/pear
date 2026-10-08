# Task #9 Stage 6: Reconstruct supervisor fixtures and bind evidence

GitHub Issue: [#9](https://github.com/postmelee/pear/issues/9)
Implementation plan: [task_m1_9_impl.md](../plans/task_m1_9_impl.md)
Stage: 6
Date: October 9, 2026
Status: Initial Stage 6 verified at `263eb00`; publication approved as PR #39. The current Stage 6.1 correction and verification are recorded in the addendum below.

## Stage Purpose

Reconstruct current native manager and owned fixtures in a new empty output, execute every approved final gate and preserve exact input-bound results. The requester explicitly continued after Stage 5 `95b50a7`, then separately approved merging `origin/master` at `d019a6e` with the prepared daily-board conflict resolution. Merge `2864f7b` preserves all earlier stage commits and the #5/#6/#9 board entries. It does not publish the work or merge Task #9 into master.

Context used: root and applicable manager/host/tests/runtime/profiles/docs rules; README, official documentation index, architecture, delivery plan and runtime contracts; Issue #9, approved task and implementation plans, Stage 5 report and reuse record; task/Git/conflict/document-location manuals, task-stage-report, task-final-report, todo and central templates. No Metal implementation is changed, so the Apple-tooling skill does not apply.

Concurrent-work inspection found master `d019a6e`, #8 `2c709b1` and #10 implementation planning `a16d49b`. #8 records synthetic translated rendering with an unresolved CPU alignment fault, not game qualification. #10 retains a separate actual-observation/clock integration gate and an exact #9 Stage 3 dependency. Read-only review of #3/#6/#7 reports preserves their component/historical scope. No private output from another worktree was copied or reused, and no other worktree was edited.

## Artifacts

| File/group | Change Summary |
|---|---|
| `tests/manager/support.py`, `case_adapter.py`, `test_activation.py` | Retain owned fixture policy/file/mount identities before temporary cleanup and bind result receipts; activation calls record the exact selected policy and root |
| [Sanitized evidence](task_m1_9_stage6_evidence.json) | Current source, tools, binaries, test IDs, corpus IDs, per-case inputs, media lifecycle, outcomes and preservation checks |
| [Final report](../report/task_m1_9_report.md), implementation plan, reuse record and daily board | Acceptance mapping, stage completion and separate publication checkpoint |
| `.build/task9/final-20261009-7dabfd95` | Fresh ignored construction output; full local build/test logs remain under `.build/task9/stage6-review/current/` |

## Body Change Scope / Lossless Preservation

Stage 6 changes only test evidence producers and task artifacts. Native implementation, original experiment producer/corpus/parser, dependency locks, schemas, profiles and public documentation remain unchanged. The helper hashes regular owned fixture files, records symbolic-link target hashes without following them, and records special-file metadata without opening FIFOs. This is fixture receipt collection, not a new production validator or test framework. Original factory, mutation, oracle, bounded capture, ownership and cleanup assertions are unchanged.

The first complete Stage 6 attempt passed 517 distinct tests. Final assessment identified missing retained per-case policy/mount receipts after temporary cleanup. The added evidence fields changed three producer inputs, so every required gate was rerun in a second new empty output. The earlier output `.build/task9/final-20261009-8c0769b5` and its successful logs remain retained; they are not counted twice or relabeled as the new run. The initial run's all-target build changed three probe executables, for which 57 affected tests were rerun successfully. In the final run, all-target construction ran before the full Python suites, so all suites refer to the same final binary receipt.

## Verification Results

Execution context: native ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5, Apple clang 21.0.0, Rust/Cargo 1.94.1 and the task-owned CPython environment. Minimum build target remains macOS 26.0. These are development inputs, not an end-user support claim. Cargo uses exact locked offline dependencies and explicit C/Rust link arguments; `libc = 0.2.186` and the original strict JSON parser are preserved.

All approved commands passed on the final current inputs. Ordering the all-target build before Python execution finalizes the probe bytes first:

```sh
python3 -B tests/manager/build.py --output .build/task9/final-20261009-7dabfd95 --locked --require-empty
python3 -B tests/manager/build.py --output .build/task9/final-20261009-7dabfd95 --locked --rust-tests
.build/task9/venv/bin/python -B tests/contracts/validate.py --check-schemas --check-examples
.build/task9/venv/bin/python -B tests/contracts/validate_v2.py --check-schemas --check-examples
.build/task9/venv/bin/python -B -m unittest discover -s tests/contracts -p 'test_*.py'
PEAR_MANAGER_BUILD=.build/task9/final-20261009-7dabfd95 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p 'test_*.py'
PEAR_MANAGER_BUILD=.build/task9/final-20261009-7dabfd95 .build/task9/venv/bin/python -B -m unittest discover -s tests/profiles -p 'test_*.py'
python3 -B -m unittest discover -s experiments/manager -p 'test_*.py'
python3 -B tools/check_governance.py
git diff --check
git status --short
```

| Gate | Current result |
|---|---|
| Fresh locked construction and native all-target tests | Pass; 13 ARM64 binary entries, exact source/tool/flag receipts; 10 distinct native tests, zero ignored |
| v1 and v2 schemas/examples | Both pass |
| Contract behavioral suite | 154 pass |
| Manager behavioral suite | 281 pass |
| Profile suite | 12 pass |
| Preserved original experiment regression | 60 pass |
| Governance and whitespace | Pass; 27 documents and 260 local targets |
| Test/input assessment | 517 distinct tests, zero required skips/failures; all 55 original corpus IDs observed |
| Preservation | All 58 original source hashes and 10 historical artifact hashes unchanged |

The evidence binds 128 current source/document inputs, all executable/fixture hashes, every discovered test ID, policy hashes, mounted root device/inode/read-only state, file manifests and current result receipts. 7 media-backed run collections retained their inputs and results. All owned attach/detach commands succeeded, with equal attach and detach counts. Read-only payloads were enforced by the OS; malformed/nonregular cases intentionally stayed on writable owned scratch and refused before execution. Regular-file hashes and typed link/special-file records avoid reading outside fixture inputs.

Required behavioral results cover immutable entry/library lookup, actual EROFS controls, atomic activation failures, busy leases, direct-child exit/reaping, both pipe faults, SIGINT/SIGTERM, bounded output and observer backpressure, unrelated sentinel survival, abrupt-manager-death quarantine, detached-helper uncertainty, A/B settings/save isolation and preservation-first manual recovery. Complete cleanup is asserted only for cases whose original outcome permits it; deliberate crash/detach negative controls retain incomplete/failed outcomes. Synthetic observer readiness, exact request acknowledgement and sequence/exit negatives do not establish real process/module coverage.

The profile/documentation suite executes the official CLI examples and refuses researched Megabonk launch with unresolved prerequisites. Actual owned fixture state and read-only images were cleaned only by their owning suites after evidence capture. Public evidence is sanitized; raw owned construction/run logs remain ignored through review/integration.

Evidence reuse: only unchanged historical input-bound claims are retained. The historical reproduction checker still reports `source_or_history_identity` and `unit_test_accounting` because Stage 1 expanded the current contract/test inventory; that old report is not eligible as current Task #9 proof. The preserved comparison checker passes. Neither diagnostic replaces the current required 517-test result, and neither historical report was edited. Builder/run legacy stage labels are retained implementation metadata; exact current output, receipt hashes and test IDs establish Stage 6 scope.

No required current test failed. Earlier Stage 4 and Stage 5 development failures remain described and retained in their reports. Package slice/dependency/ad-hoc signature inspection is recorded separately from permission to sign, provision or distribute.

## Residual Risks

- Real Wine/FEX/Steam/helper observation, common-clock authority, native Megabonk execution, saves and distribution qualification remain unperformed. Fixture success cannot qualify them.
- Abrupt supervisor death can leave a child and incomplete state; the next invocation refuses uncertain reuse. No automatic orphan reaping, global Wine shutdown or save migration/rollback is claimed.
- Local read-only media and cooperative owned leases are not a hostile-code sandbox. Conservative media identification can refuse during unrelated mount churn; no silent retry or writable fallback was added.
- Research profile build/family/renderer/save mapping remain unknown and optional features untested. CI/remote PR checks are unperformed before publication.

## Impact on Next Stage

All six approved implementation stages are complete. The next checkpoint is review of the final report and concrete PR body, followed by publication only if approved. Preserve stage commits and retained Task #9 artifacts through review; do not close the Issue or self-merge.

## Approval Request

Please review the final report and concrete PR proposal and approve publication from `codex/publish-task9` to `master`. This request follows the implementation plan's explicit final-report/publication checkpoint.

## Stage 6.1 Addendum — Enforce the External-Policy Boundary

### Stage Purpose and Authorization

After approving publication of [PR #39](https://github.com/postmelee/pear/pull/39), the requester asked for review and then explicitly requested correction on October 9, 2026. Review reproduced activation and successful owned fixture launch using `--policy` inside the submitted read-only bundle at `263eb00`; the reference CLI rejected it as `policy_inside_bundle`. The old passing 517-test inventory did not cover this policy-location boundary. Its evidence is preserved unchanged and does not establish the missing check.

The correction is authorized within Issue #9/PR #39 and recorded in the implementation plan. Context remains the root, manager, host and tests rules; runtime contracts and official CLI guidance; approved task/implementation plans and the final report. The task-stage-report and todo procedures apply. No new architecture, dependency, product-documentation destination, real-runtime authorization or merge is introduced.

### Artifacts and Body Change Scope

| Artifact | Change |
|---|---|
| `manager/src/fs.rs` | Reuse no-follow absolute traversal with an optional excluded root identity; compare each opened ancestor's device/inode |
| `manager/src/policy.rs` | One shared filesystem policy loader reusing exact-byte bounded record reading and strict JSON parsing |
| `manager/src/main.rs`, `manager/src/launch.rs` | Use the shared loader for inspection/evaluation/activation and selection reload for prepare/recover/launch |
| `tests/manager/case_adapter.py`, `test_policy_boundary.py` | Owned embedded-policy fixture and six actual CLI regressions, including refused state mutation and successful external-copy execution |
| [Correction evidence](task_m1_9_stage6_1_evidence.json), final report, plan and board | Current source/binary/input-bound results and preserved original failing reproduction |

Actual directory identity avoids a lexical prefix check: nested files and HFS+ case aliases refuse, while similarly named external siblings remain eligible. Existing no-follow and single-link checks refuse symbolic-link and hardlink aliases. An external policy copy may legitimately have identical bytes; independent caller review remains required, because file location alone is not authenticity. The programmatic `Admitted::new` API still receives caller-supplied parsed policy; path-based production CLI entry points share the new location check.

Existing original corpus, parser, dependency locks, contract schemas, public guidance and earlier evidence remain byte-preserved. Public documentation already specified an external policy and therefore needs no change. This closes a missing implementation check rather than weakening the reference validator or rewriting prior results.

### Verification Results

Execution context: the recorded native ARM64 macOS 26.5.2 host, Xcode 26.6/SDK 26.5, Apple clang 21.0.0, Rust/Cargo 1.94.1 and task-owned Python environment. A new empty locked offline output was built; all-target construction finalized probe bytes before behavioral suites. Current evidence contains 13 ARM64 binary entries and 129 source/document inputs. No old binary result substitutes for the changed native boundary.

```sh
python3 -B tests/manager/build.py --output .build/task9/policy-fix-49b5b0aa --locked --require-empty
python3 -B tests/manager/build.py --output .build/task9/policy-fix-49b5b0aa --locked --rust-tests
PEAR_MANAGER_BUILD=.build/task9/policy-fix-49b5b0aa .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_policy_boundary.py -v
.build/task9/venv/bin/python -B tests/contracts/validate.py --check-schemas --check-examples
.build/task9/venv/bin/python -B tests/contracts/validate_v2.py --check-schemas --check-examples
.build/task9/venv/bin/python -B -m unittest discover -s tests/contracts -p 'test_*.py'
PEAR_MANAGER_BUILD=.build/task9/policy-fix-49b5b0aa .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p 'test_*.py'
PEAR_MANAGER_BUILD=.build/task9/policy-fix-49b5b0aa .build/task9/venv/bin/python -B -m unittest discover -s tests/profiles -p 'test_*.py'
python3 -B -m unittest discover -s experiments/manager -p 'test_*.py'
python3 -B tools/check_governance.py
git diff --check
git status --short
```

| Verification | Current result |
|---|---|
| Dedicated external-policy regressions | Six pass; repeated within the full manager suite and counted once |
| v1/v2 schemas/examples and contract behavior | Both schema/example gates and 154 tests pass |
| Full native manager behavior | 287 pass, including all 55 original corpus IDs and the six new boundary cases |
| Profiles, original experiment and Rust | 12 + 60 + 10 pass |
| Distinct required tests | **523 pass**, zero required skips or failures |
| Original preservation | All 58 original source inputs and 10 historical artifacts unchanged |
| Governance, links/privacy and whitespace | Pass; final checks recorded with the correction evidence |

Embedded policies refuse before creating/replacing activation selection, preparing/recovering contexts, sending observer handshake bytes, spawning a child or mutating a launch journal. The launch regression starts from a legitimately prepared selection with the same policy hash, proving the check is enforced again at use. HFS+ case aliases are verified by actual file identity, not assumed. External symlink/file-parent aliases and hardlinks refuse; a similarly named external sibling evaluates successfully. An independently selected byte-identical external copy completes actual owned fixture execution, reaping, observation and unrelated-sentinel checks.

The original review reproduction is retained as the negative baseline, including the old successful embedded-policy activation/launch and the oracle refusal. The exact original v1 review reproducer was also rerun against the corrected binary: both native activation and the oracle reject `policy_inside_bundle`, no selection is created, and embedded-policy execution stops at admission. This additional confirmation is not counted as another test. All current correction gates passed on their first run. Dedicated/full repeated cases are not counted twice. Actual owned read-only media were detached by each suite; only their temporary fixture state was removed.

The historical #3 reproduction current-input checker still reports the previously documented source/history identity and test-accounting mismatch; the historical comparison checker passes. Those records are unchanged. These historical diagnostics do not replace the newly repeated current required gates.

### Residual Risks and Handoff

The earlier runtime, real observer, game, save and distribution qualification limits still apply. This is an external-location boundary under existing no-follow/private-root assumptions, not a new policy authentication service or hostile same-user filesystem sandbox. The user-authorized correction will update the existing Open PR with its current evidence; merge and Issue closure remain separate approvals.
