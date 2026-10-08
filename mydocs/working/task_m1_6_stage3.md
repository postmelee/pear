# Task #6 Stage 3 — Translated Ordering and Lifecycle

GitHub Issue: [#6](https://github.com/postmelee/pear/issues/6)
Implementation plan: [task_m1_6_impl.md](../plans/task_m1_6_impl.md)
Stage: 3 — complete locally on October 8, 2026 at 18:35 KST.

## Stage Purpose

Qualify the declared finite multi-worker ordering and repeated lifecycle boundary,
using actual translated guest workers and observed FEX policy. This supports #6;
it does not complete the issue or qualify Megabonk.

Context used: approved task/implementation plans, current #6 body/open issues,
root/runtime/FEX/tests rules, architecture and delivery context carried from Stage
2, and the pinned reuse review in the plan. Hyper-Waterfall v0.3.0
`task-stage-report` and `todo` procedures apply. Metal work is not applicable.

## Artifacts

| File | Change summary |
|---|---|
| `tests/cpu/ordering.c`, `ordering.asm` | Original MIT measured sequences, two workers plus coordinator, bounded epochs, TLS/join and repeated worker lifetimes |
| `tools/cpu/ordering.py`, `compare.py`; `tests/cpu/test_ordering_results.py` | Exact-source PE build, native capture, same-PE comparison, effective policy and checked retirement admission; nine refusal/positive controls |
| `runtime/fex/patches/cpu/0002-*`, `0003-*`, `0004-*` and separate series records | Actual policy observation, confined link diagnostics and authoritative shared-target correction |
| `tools/cpu/fex_build.py`, `runtime.py` | Ordered patch pre/postimages, isolated ARM64EC builds and existing signing/supervision reuse |
| `.github/workflows/cpu-native-reference.yml` | Approved task-branch reference extended to the new calibration/qualification PE; unchanged native corpus not repeated |
| [Reference checkpoint](task_m1_6_stage3_reference_review.md) | Publication scope and preserved reference failures |
| [Sanitized observations](task_m1_6_stage3_observations.json) | Input identities, counts, policies, outcomes, regressions and limits |

## Body Change Scope / Lossless Preservation

All additions remain in approved task/test/tool/runtime locations. No official
product document moved or changed. Stage 1's immutable planning corpus and Stage
2 evidence remain historical snapshots; Stage 3's executable contract is separate.
The four histogram modes bind the declared locked-RMW, message-passing and
store-buffer boundaries; fenced SB is the additional forbidden-outcome control.

Pinned FEX single-thread atomic fixtures and instruction-count TSO tests do not
supply a Windows two-worker oracle. Reuse Pear's existing thread/TLS/join pattern,
FEX's Context policy getters, shared-map lookup and source mutation turn. Keep
C/C++/assembly, existing owner wire ABI, Wine, permissions, W^X publication and
strict guard checks. No new engine, Rust rewrite or upstream submission occurred.

The first calibration found a real link-transaction mismatch. Reproduction showed
valid thread/revision/map/entry/bytes but a different shared target from the
thread-local cached address. The correction reads the authoritative shared target
under its existing lock while holding the source mutation turn. If the source
write epoch changed after the RX snapshot, retain the existing indirect path;
never mint a link transaction from stale bytes. `PatchPrepared` remains strict.

## Verification Results

Execution context: Apple M4 Pro ARM64, macOS 26.5.2 (25F84), Python 3.14.4; existing
hardened development signing/provisioning. Native reference: Windows Server 2022,
AMD Family 25 Model 1 Stepping 1, **two logical CPUs**, native machine `0x8664`,
process machine zero, Python 3.12.10; image `win22` / `20260927.320.1`.
PE tools: NASM 3.02 and LLVM-MinGW 20260908 / Clang 23.1.1, pinned archive hashes.
This is instrumented correctness work, not a timing/power comparison.

The [native reference](https://github.com/postmelee/pear/actions/runs/37757016708)
at `ba5658add1d412701ea0769af4d66777a9d4da33` passed calibration and qualification.
Pear ran its **exact downloaded PE**, SHA-256 `ddfa74961318047c160ffc80f1dee8d4a39504b6df8b1b931ab5880ed489a093`.
FEX DLL: `2925abaafea4d4c3293c30e778629208b507d9690e7d2b128e9b500733608364`.
Runtime: `4995218b3a4d502aa5fbf35291a990047e38b6531bd2390b41db986e38215bd2`.

Command run (environment paths select retained private observations):

```sh
python3 -B -m unittest discover -s tests/cpu -p test_ordering_results.py
python3 -B tools/cpu/compare.py --manifest tests/cpu/corpus.json --reference "$PEAR_NATIVE_REFERENCE" --candidate "$PEAR_STRESS_RUN" --output .build/task6/stage3-comparison
git diff --check
```

Result:

- **9/9** ordering-result controls passed. They reject missing workers/final
  records/counts/joins, forbidden outcomes, failure exits, disabled/missing actual
  policy and missing checked source retirement. Permitted plain SB 00 can pass.
- Each host completed **2,048 iterations × four modes × four rounds = 32,768
  measured pairs**, with **zero forbidden outcomes**. Histogram frequencies need
  not match between schedulers. Neither host observed plain SB 00; this allowed
  result was not required to occur and its absence is not a stronger proof.
- Pear created and normally joined **eight worker lifetimes**, two at a time plus
  one coordinator; TLS remained isolated. Nine actual thread-policy records show
  scalar/vector/memcpy software TSO enabled. Eight `ThreadTerm.complete` records
  occur only after `DestroyPearThreadChecked` reports destroyed and freed.
- Policy observation reads Context getters on actual FEX state creation, then
  maps that state to the Windows thread ID at publication. These same getters
  feed OpcodeDispatcher scalar/vector/memcpy and JIT memory code generation.
  Darwin's existing hardware-TSO service remains unsupported; no hardware claim.
- **7/7 changed-boundary regressions** passed against the unchanged exact-PE native
  Stage 2 reference: API callback, TLS/thread, guest fault/data guard, cross-thread
  changed code, suspend/context, register/stack ABI and SEH/unwind.
- Current authorization before/after, observed ARM64 process/images, owned cleanup
  and sentinel survival passed. The ordering run recorded 41 translation observations
  and 16,439 image events; this is finite observation, not complete late-load coverage.
- Patch-admission controls (4/4), existing execution-evidence controls (4/4), and
  governance (25 documents, 231 local targets) passed during changed-area checks.

Evidence reuse: the same #5 Wine/signing/supervision remains bound to its original
receipts. Native Stage 2's 19-PE reference is unchanged and reused, not rerun.
Seven Pear boundary cases were rerun because the JIT target correction changes the
candidate. Stage 4 must still bind/recheck the remaining instruction cases on this
final FEX candidate; the earlier 18-pass/AVX-unsupported result belongs to Stage 2.

### Failures and calibration

Two initial Pear calibrations failed at link ownership admission. Preserve both
records and the diagnostic cause; neither is relabeled a pass. The first corrected
64-iteration/two-round calibration completed 512 pairs in 7,228 ms. The frozen
qualification budget is 2,048/four rounds, 45 seconds per round, 120 seconds native
capture and 180 seconds owned Pear execution.

Native attempt 37756093282 failed before execution because CRLF checkout changed
source bytes. The runner now materializes the two exact tracked source files with
autocrlf disabled. Attempt 37756466893 then exited 106 at its 45-second round
boundary with no completed round. A bounded scheduler yield was added only to
unmeasured epoch/completion waits; counts, measured ASM, oracle and timeouts stayed
unchanged. This addresses progress with three participants on a smaller runner;
the precise scheduling history of the failed host was not captured.

The changed fixture was recalibrated: Pear 512 pairs passed in 9,262 ms, native
512 pairs passed, then qualification passed on both hosts. Pear qualification took
12,436 ms including cold-prefix execution and supervision. These differently
instrumented elapsed times must not be interpreted as an engine performance ratio.

### Retention

Task-owned `.build/task6/` retains `stage3-fex1..3`, calibration builds/runtimes/runs,
`stage3-native-pe1..3`, `stage3-native-results1..3`, artifact-origin metadata,
`stage3-regression-runtime1`, `cpu-s3reg-*`, `stage3-regressions.json`, and the final
qualification runtime/run/comparison. Owners and exact hashes are in their records.
GitHub artifacts expire after 14 days; source and sanitized results are in Git.
Completed disposable synthetic prefixes are removed only after owned cleanup and
reaping checks; original failures/logs remain. #1/#5/#7 dependency caches remain.
No game files, credentials, private profiles, signing identities or raw private
captures are committed. Early source publication used the approved reference
exception; this stage's final commit binds the completed report and observations.

## Residual Risks

- Finite two-worker correctness does not establish arbitrary concurrency, all x64
  behavior, game-scale resource bounds, game support or distribution qualification.
- i386/WoW64 remains unperformed; AVX remains explicitly unsupported in Stage 2.
- Final instruction/candidate integration remains Stage 4. Complete late-load
  Rosetta evidence, Steam helpers, graphics and gameplay remain other issues.
- Logs are bounded correctness diagnostics. No power/performance benefit is claimed.

## Impact on Next Stage

Stage 4 should retain `stage3-fex3`, the passed native ordering artifacts and both
runtime identities. Reuse the seven current boundary runs; run only the remaining
instruction coverage needed to bind the final candidate. Update the already
approved existing CPU contributor guide and final qualification/report documents.
Do not rebuild unchanged components merely for report wording. #6 stays open;
master was not merged and no final PR was created in Stage 3.

## Approval Request

Review Stage 3 and explicitly continue to the already approved Stage 4 integrated
qualification and handoff. This report does not authorize a master merge.
