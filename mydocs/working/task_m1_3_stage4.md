# Task #3 Stage 4: Controlled comparison and manager-language decision

GitHub Issue: [#3](https://github.com/postmelee/pear/issues/3)
Implementation plan: [`task_m1_3_impl.md`](../plans/task_m1_3_impl.md)
Stage: 4
Date: September 28, 2026

## Stage Purpose

Apply the predeclared comparison procedure and qualitative rubric to equivalent native manager fixtures, select an implementation direction for #9, and preserve the evidence and limitations. The decision does not select a CPU translator, qualify a runtime, or implement a launcher product.

## Artifacts

| File | Change Summary |
|---|---|
| `experiments/manager/compare.py`, `test_compare.py` | Controlled sampling, bounded capture, source/binary provenance, arithmetic/order checks, native package inspection and historical evidence verification. |
| Rust `main.rs`, `supervisor_tests.rs` | Correct nonblocking-pipe failure cleanup; two owned fault-injection tests verify both failure positions. |
| `fixtures/cases.json`, `fixtures/child.c` | Explicit input corrections separate ordinary functional limits from deliberate timeout tests and unchanged scored-launch limits. |
| `experiments/manager/results/` | Latest passing comparison and final corpus, prior failed/completed attempts, input revisions and bounded diagnostic records. |
| `docs/decisions/manager-language.md` | Rust manager choice, measured costs, Swift tradeoffs, limits, reconsideration triggers and #9/#10 obligations. |
| Experiment README, implementation plan, daily board and this report | Reproduction steps, corrective rationale, actual status and next-stage checkpoint. |

## Body Change Scope / Lossless Preservation

The frozen `comparison-plan.json` is byte-identical to Stage 3: SHA-256 `79766f8e5ca1799bc8d5690a3413a40d3801ead60d72164d27427cb02898ad9c`. Release settings, clean/incremental edit order, five warmups, 30 scored launches per candidate and scored 1,500 ms limits remain unchanged. Source inventories bind the actual input revisions used by each attempt. Stage 1–3 reports remain unchanged.

The Rust fix closes both read ends if either nonblocking setup fails before bounded cleanup can read them; both setup operations are evaluated independently. Fault injection is internal and test-only, with no public CLI/environment backdoor. Existing dependencies and runtime contracts are unchanged.

The final functional corpus uses the existing CLI's 5,000 ms maximum for ordinary/non-timeout cases. Deliberate timeout and descendant-pipe cases use 1,500 ms; the intentional delay is 5,000 ms, cleanup remains bounded at two seconds and the outer watchdog at ten seconds. The [first](../../experiments/manager/results/fixture-input-revision.json) and [second](../../experiments/manager/results/fixture-input-revision2.json) revisions record the changed bytes and reasons. Mandatory native/identity traces, expected classifications, owned cleanup, sentinel survival, privacy and output limits are preserved. This is not a byte-identical reproduction of Stage 3, a guarantee of startup within 1,500 ms, or a claim that an OS issue was fixed.

All raw logs, binary/source copies, private paths, process identities and raw stack samples stay in ignored task-local outputs. Committed records are reviewed derivatives. No proprietary payload, Steam account, profile/private key, signing mutation, security-policy change, runtime/translator port, production manager or game execution was introduced. #1's worktree is independent; its approved final investigation is published in PR #26.

## Verification Results

The planned commands were executed. The comparison command retains each attempt separately, rather than replacing unfavorable samples:

```bash
python3 experiments/manager/compare.py --plan experiments/manager/comparison-plan.json --build-root .build/task3/prototypes --output .build/task3/comparison-raw.json
python3 experiments/manager/compare.py --check-report experiments/manager/results/comparison.json
python3 experiments/manager/run_cases.py --build-root .build/task3/prototypes --all --oracle .build/task3/venv/bin/python
git diff --check
```

Additional verification used the current locked prototype build, targeted negative cases, the full Python experiment suite and the [documented Rust fault-test command](../../experiments/manager/README.md#rust-pipe-setup-failure-regression). After the second fixture revision, native source/binary identity checks established that no further native rebuild was required; only functional corpus parameters and comparison/checker code changed.

| Check | Actual Result |
|---|---|
| Python experiment regressions | 40 pass: report accounting/provenance/history, timing-budget separation, bounded command handling and shared harness checks. |
| Rust fault injection | Two pass on the current native source/C fixture: both read descriptors closed, bounded cleanup, direct child reaped, child/descendant identities gone and unrelated sentinel alive. |
| Revision 2 standalone pre-check | 55 cases × two candidates = 110/110 pass. |
| Comparison before and after gates | 110/110 pass each on their declared binaries; native and privacy/bounds observations pass. |
| Frozen sampling | 82/82 rows pass: six clean builds, six incremental builds with compiler rebuild evidence, ten unscored warmups and 60 scored launches. |
| Required standalone final corpus | 110/110 pass; no failed row or omitted identity trace. |
| Public report consistency | Exit 0; current input hashes, exact order/counts, binary identities, gate hashes, packaging fields, retained history and recomputed summaries match. |
| Native package inspection | Both measured binaries ARM64, minimum macOS 26.0/SDK 26.5; linker-generated ad-hoc signatures pass strict read-only verification. No distribution qualification follows. |
| Documentation/privacy/preservation | Local links resolve, embedded reproduction code parses, evidence JSON and privacy checks pass; prior reports and frozen plan preserved. `git diff --check` passes. |

The [latest comparison](../../experiments/manager/results/comparison.json) SHA-256 is `7f9d00101257b0bbc5bcc3ba37d5e617acd7a847e1752b79911034fd36bd3bc5`. The [latest final corpus](../../experiments/manager/results/final-corpus.json) SHA-256 is `89431fdefeeb48900faa39df4ccef1083368f95529497e4710d547ea90e70f7d`. The [standalone pre-check](../../experiments/manager/results/pre-comparison-corpus-revision2.json) is also preserved. These four passing corpus runs establish the final declared functional budget, not general startup reliability.

### Retained failures and investigation

1. The first original-input attempt stopped at its before-gate: both descendant-pipe cases lacked required traces under 300 ms. No timing rows were produced.
2. The second original-input attempt retained all 82 planned rows but failed its after-gate: both deliberate-timeout cases lacked child traces. Both reports, their samples and four unscored targeted diagnostics remain in the [prior-attempt archive](../../experiments/manager/results/prior-comparison-attempts.json).
3. The first corrected-input comparison passed all 82 rows and both gates, but the separate final baseline corpus passed 109/110. Rust `observer_gap` timed out at 1,500 ms with no child output/trace; direct-child reaping/cleanup and sentinel checks passed. Preserve its [completed comparison](../../experiments/manager/results/comparison-before-revision2.json) and [failed final corpus](../../experiments/manager/results/final-corpus-before-revision2.json) separately. Passing measurements did not override that failure.
4. The bounded [16-invocation diagnostic](../../experiments/manager/results/startup-diagnostics-before-revision2.json) passed without reproducing the failure. Input bytes/permissions/signatures matched between failed and passing cases. One sampled slow successful child showed pre-main dyld remote-notification work. Sampling can perturb execution; monitor identity, installed-source equivalence and the original timeout's cause remain unproven. No monitor or protection was disabled.
5. Revision 2 separates functional liveness from the unchanged scored-launch budget. One new complete comparison and the required final corpus passed. All prior samples and failures remain archived, and none is pooled into the latest result or relabeled as passing.

### Decision and measurements

Select **Rust for the new #9 manager/supervisor only**. The decision weighs explicit ownership, native interface and maintenance costs with lower observed build medians and command RSS. Swift retains real advantages: a smaller executable, no external package dependency and direct macOS integration. Neither language automatically handles process ownership correctly, as the corrected Rust pipe path demonstrates. Future UI selection is independent; upstream runtime languages remain unchanged.

| Final median | Rust | Swift |
|---|---|---|
| Clean-output build, three samples | 3.670 s | 10.659 s |
| Native comment-edit rebuild, three samples | 5.918 s | 7.125 s |
| Whole manager invocation, 30 samples | 279.867 ms | 303.175 ms |
| Launch `wait4` RSS accounting | 2,097,152 bytes | 7,061,504 bytes |
| Standalone manager executable | 544,816 bytes | 246,608 bytes |

The decision document reports every range and the qualitative comparison. RSS is Darwin OS accounting for the waited command, not an independently sampled process-tree peak. Launch includes validation, copied fixture execution and cleanup; it is not pure language startup. Timings vary substantially across retained runs, and the final Rust incremental median exceeds its clean median. Small sample counts, retained OS/SDK caches, fixed Rust-then-Swift pairing, 1 ms polling and unmeasured desktop/thermal interference limit conclusions. No game FPS, power, temperature or general language speed advantage is claimed.

## Residual Risks

- The 1,500 ms startup failure remains historical evidence with an unproven cause. Revised functional success does not establish a startup SLA; real manager startup/cancellation/recovery require broader tests.
- The prototypes implement a controlled four-record subset, custom parsers and narrow native interfaces. Full runtime contracts and real Steam/helper lifecycles remain later work.
- Concurrent bundle mutation and pathname execution races remain unsupported; #9 must establish immutable artifact and mutable-state ownership rather than relying on preflight strings alone.
- The observer-ready/gap inputs are fixtures, not #10's causal readiness and complete process/module coverage. Synchronous observation callbacks can affect startup and need bounded implementation/measurement.
- Read-only ad-hoc signature inspection does not establish Developer ID, provisioning, notarization, app-bundle behavior, older-macOS or independent-Mac support.
- Both extra Rust toolchain/dependency costs and Swift system-framework dependencies remain visible; no project-wide Rust mandate or translator rewrite is justified.

## Impact on Next Stage

Stage 5 must recreate the validator environment and native outputs in a new empty location, rerun contract and native checks, preserve the declared revised budgets and historical failures, and produce the final #3 acceptance mapping. Review the actual #1 source handoff without converting its blocked audit into a runtime lock or readiness claim. Finalize #9/#10 ownership and observation obligations, and add the approved narrow architecture/index links.

Stage 5 has not started. No #3 PR publication, production runtime work, merge or Issue closure is implied by this report.

## Approval Request

Approve the Stage 4 artifacts, corrected fixture limits, retained failure history and Rust manager decision, then authorize Stage 5 reproduction and final contract handoff within the approved plan.
