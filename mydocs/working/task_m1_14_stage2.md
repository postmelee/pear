# Task #14 Stage 2: Portable verifier CI and temporary-output rules

GitHub Issue: [#14](https://github.com/postmelee/pear/issues/14)
Implementation plan: [task_m1_14_impl.md](../plans/task_m1_14_impl.md)
Stage: 2 — approved bounded scope complete; full Issue #14 remains open.

## Stage Purpose

Qualify the five selected master-derived synthetic verifier suites on clean Linux, connect the qualified set to the existing PR workflow, and document portable scratch/evidence ownership. The requester explicitly continued after the concrete scope and location recommendation.

Context used: root/tests rules, existing workflow, Stage 1 report, task plan and refined Stage 2 plan. Applied task-stage-report and existing todo format. No Metal implementation, native host code, dependency lock or #5/#7 candidate was changed.

## Artifacts

| File | Change Summary |
|---|---|
| tests/AGENTS.md | Portable temporary-root selection, isolated automatic cleanup, retained task/run evidence and scoped exceptions |
| .github/workflows/documentation.yml | Five independent Ubuntu/Python matrix suites; strict nonempty/no-skip gates; one bounded false-success detection control |
| Task plans and daily board | Explicit continuation, hosted execution choice, observed experiment and current stage status |
| This report | Actual Linux evidence and limits, retained log identities and handoff status |

## Body Change Scope / Lossless Preservation

Locations match the task plan refinement. The existing documentation job, pinned action revisions, read-only permissions and disabled credential persistence are retained. The new job initially ran only on workflow_dispatch; after qualification its restriction was removed so the existing pull_request and workflow_dispatch events both select it. No new runner/framework or production validator/test implementation was created. #7's OS-specific TemporaryDirectory constructors remain unchanged by this task.

## Verification Results

Execution context: clean GitHub-hosted Ubuntu 24.04 image 20260927.320.1, Linux x86_64, Python 3.12.14, Git 2.55.0. These synthetic tests do not execute ARM64 Wine/FEX/DXMT or qualify any game. Platform temporary storage is selected with runner.temp through TMPDIR. Tests create and clean their own scratch fixtures.

Evidence reuse: existing test and validator implementations from the master baseline were reused unchanged. Stage 1 source inspection was not treated as Linux success. The final workflow configuration was rerun after enabling its PR eligibility; report-only additions do not alter those test/configuration inputs.

Commands run:

```bash
gh workflow run documentation.yml --repo postmelee/pear --ref codex/publish-task14
python3 -B tools/check_governance.py
git diff --check
```

Both hosted executions succeeded:

| Run | Source commit | Result |
|---|---|---|
| [37149720472](https://github.com/postmelee/pear/actions/runs/37149720472) | `a3fdb7345c0881d4249b5e46ef455bd411f7009c` | Six jobs passed |
| [37149821735](https://github.com/postmelee/pear/actions/runs/37149821735) | `8ad879ff8a5f73476b533dce33f3f076705c1251` | Six jobs passed |

| Existing suite | Tests per run | Failures / errors / skips |
|---|---:|---|
| Source inventory | 77 | 0 / 0 / 0 |
| Wine report assessment | 50 | 0 / 0 / 0 |
| Wine input validation | 10 | 0 / 0 / 0 |
| Unsigned artifact comparison | 40 | 0 / 0 / 0 |
| ABI review | 19 | 0 / 0 / 0 |
| **Portable verifier total** | **196** | **0 / 0 / 0** |
| Existing documentation tests | 35 | Passed |

Each matrix job requires discovered > 0, executed == discovered, successful results and no skips, expected failures or unexpected successes. The five suites run in separate jobs so their imports cannot shadow each other.

The wine-report job additionally reused test_success_label_is_not_required_or_sufficient_evidence in a separate process. Only the command_did_not_pass predicate was temporarily ignored through unittest.mock. The existing test produced exactly one assertion failure containing Error not raised, with one test, no errors/skips and exit code 1. The parent control required those exact outcomes and passed. Import/environment errors cannot satisfy this control. The ordinary suite, with the real predicate intact, passed. Other matrix entries intentionally do not run this one control; those conditional step skips are not unit-test skips.

Local governance passed 22 documents and 173 local targets. Whitespace and workflow YAML/inline-Python syntax checks passed. Independent source/log review found no material defect in suite selection, strict result gates, the control, permissions or scoped policy. PR-event execution and required branch-protection configuration have not been exercised or changed; both observed runs used workflow_dispatch on the publication branch.

### Retained evidence

Raw logs and run metadata live under ignored `.build/task14/runs/<run_id>/`. The producing task is #14; commands, inputs and public run URLs are above. Preserve these owned copies through review; clean them only after required evidence is retained elsewhere. Hosted retention is finite, so a public URL alone is not permanent evidence availability. Public report content excludes credentials, private diagnostics and game data.

| Run | run.log SHA-256 | run.json SHA-256 |
|---|---|---|
| 37149720472 | `5dd60e3977c9447a8fdb8b5895aac1b7481760a3605cb588f16a7ff157c4d358` | `8aec5f2f6f4dc96785e9de07305490319aad643e5a2118da9802988ac5fb8932` |
| 37149821735 | `8134aa98d753574f3f70b015038585cf5c3f0dac5c39c67873c75b07d1dc341c` | `f6b7efca2c67c557eb97d8b50f4cfba551a55ddc1b39189c1df3c8a43b78a346` |

### Preparation failures and recovery

The local Docker socket was initially inaccessible in the sandbox; outside it, the daemon was confirmed unavailable. No VM was started. The approved small experiment used hosted Ubuntu instead. One document-generation attempt failed before writing due to nested string quoting; it was replaced with literal heredocs. A local syntax-check helper used filter_map unavailable in installed Ruby, then succeeded with map/compact; the hosted experiment was already dispatched independently. These were preparation failures, not passing checks. No production file or expected test outcome was changed to conceal them.

## Coordination

The requester-authorized advice about test_deterministic_pair.py and test_deterministic_native.py was delivered to #7's owning conversation. It distinguishes actual temporary-directory constructors from synthetic rejection-path literals and requests a safe later application point. #7 was actively rebuilding; this task did not interrupt it, alter its candidate, or claim that either DXMT path was fixed. No additional runtime stage was authorized by the handoff.

## Residual Risks

- #7's two constructor changes await owner coordination and appropriate focused verification.
- Contracts' macOS-specific wheel lock and broader FEX/DXMT Linux suitability remain deferred.
- Workflow configuration and scoped rules are on codex/publish-task14, not yet merged into master. No PR has been opened and no branch protection was changed.
- Portable CI cannot qualify runtime/profile promotion, signing, host execution, Steam or gameplay; full #14 still needs its original prerequisites.

## Impact on Next Stage and Approval Boundary

Preserve this selected suite and its observed scope when integrating later changes. Any expansion needs dependency/platform review and actual execution. Stage 3 remains unapproved; no full Issue completion, PR publication, merge or new runtime work is performed by this stage.
