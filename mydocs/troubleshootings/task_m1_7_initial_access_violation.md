# Task #7 — Initial native pairing access violation

Issue: [#7](https://github.com/postmelee/pear/issues/7).
Last reviewed: October 4, 2026.

## Status

**Reopened after incomplete execution recurred in unchanged-candidate formal
verification; root cause unknown.** The new run again ended after observation
33, but its loader exited zero and did not record `0xc0000005`. The original
access-violation code has not been reproduced; a common cause is unproven.
This incident is neither fixed nor attributed to the Mac environment.

This is the single incident handoff. Preserve the linked observation records
rather than copying the diagnostic chronology into each daily update. Deferring
speculative investigation does not waive required verification or close #7.

## Symptom

The initial final-candidate native pairing run emitted 33 of 39 expected case
rows, ending with `destroy_acquire`, then terminated without the remaining six
rows or the terminal PE record. The recorded guest process exit status was
`0xc0000005` (access violation); the Wine loader returned 5 and the outer command
returned 1. Owned cleanup completed and the unrelated sentinel survived.

`destroy_acquire` is the last recorded observation, not the proven faulting
instruction. The interval after it includes native return/autorelease handling,
the PE transition and window destruction. No fault address or stack was captured.
The loader's numeric exit code does not establish a permissions failure.

## Reproduction Conditions

The original procedure is known; a deterministic trigger is not.

```sh
# Use the exact recorded inputs and a new output name; never overwrite a failure.
python3 -B -m tools.dxmt.deterministic_native \
  --repo "$pear_repo" --constructor-root "$pear_repo/tools/dxmt" \
  --run --runtime "$pear_runtime" --output "$pear_fresh_pairing_output"
```

- Host: Apple M4 Pro, 24 GiB, macOS 26.5.2 (25F84), active graphical session.
- Source implementation: `e6565f6`; later progress commits changed records only.
- Tools: Xcode 26.6 (17F113), SDK 26.5, LLVM-MinGW 20260908 / LLVM 23.1.1;
  use the recorded Python 3.14.4 deterministic adapter environment.
- Exact selected build: `.build/task7/stage5-deterministic8`; native link option
  `-Wl,-objc_stubs_small`, byte-verified retained prerequisites.
- Original signed runtime: `.build/task7/stage5-deterministic-runtime2`.
- Failed output: `.build/task7/stage5-deterministic-pairing2`.
- Original ordinary ARM64 fixture, fresh synthetic prefix, `WINEDEBUG=-all`,
  original runner's pre-device Metal validation environment and ownership bounds.
  No debugger, exception-handler fixture replacement or debugger entitlement.
- Normal macOS protections and the recorded development authorization apply.
  No Steam credentials, game files or saves are required for this fixture.

| Evidence | SHA-256 |
|---|---|
| Selected build receipt | `5eb2a22a1e6132043ba3be3985683573e23f81893f91b9729b55ef00fb57a31d` |
| Signed runtime receipt | `d278123d23993a527e632411eba7e0eaa166251a7746366d67b4a670006ac6dd` |
| Original ordinary ARM64 fixture | `525be80925f96013e705fd4825574d75a93d22165ecf53bb7271d58055a616d3` |
| Failed case receipt | `95fdf884fc593916ea4b4d6537f2eebffb43fca46e3d5b40d96b1115f5bf77d1` |
| Failure receipt | `960e289a0b362c0ce09a42882aa97f917200d8f1965466b552fb202c1c62f951` |

## Cause

Unknown. No evidence distinguishes a Wine, DXMT bridge, fixture, timing, OS or
hardware cause. Environment-dependent timing may expose a software defect;
these explanations are not mutually exclusive. Successful later checks do not
prove a fix or establish that the original environment caused the failure.

## Resolution

No confirmed fix. Speculative investigation was deferred until the unchanged
formal run met the same-boundary recurrence condition. Investigation is now
limited to the new incomplete-execution/exit-path evidence. No speculative
production patch is justified by the current evidence.

A separate debugger ownership/cleanup defect was investigated and its finite
handoff controls passed. That work is not a repair of this access violation;
the earlier failed diagnostic cleanup remains failed in its historical record.

## Recurrence Prevention

Continue the original task's required unchanged-candidate verification and
integration work. Do not add whole rebuilds, repeated executions or debugger
extensions solely because this nonreproduced incident exists. Do not silently
replace a failed required verification with a successful retry. Refer here in
the final report and relevant integration handoff instead of duplicating a
standing warning in each routine update.

The progress-journal interpretation that every historical unexplained failure
must be root-caused before #7 completion is distinct from the original Issue's
component-build and paired-interface criteria. Any completion decision must
state its finite evidence and this unresolved risk explicitly. Actual required
runtime/game correctness gates remain unchanged.

## Reopen Conditions

Resume targeted investigation if the same path or symptom recurs, useful new
fault-address/stack evidence becomes available, or source review identifies a
concrete related defect. A recurrence in required verification or game execution
is a correctness blocker. Preserve the first new failing record and investigate
that evidence rather than continuing a pass-seeking test loop.

## Verification

The original run failed; its outcome is immutable. A later unchanged-fixture
quiet control passed all 39 rows and its case assessment. Logging/observer and
debugger variants also completed, but they are diagnostic evidence and do not
replace the formal original-candidate run and explicit diagnostics review.

Two successful debugger cases had the same layer-deallocation count at row 33
as the original failure. That count alone does not distinguish the failure and
does not rule out a timing/lifetime defect. The first run in the current predeclared formal batch failed, and the second
ordinary run was cancelled. No completion or general stability claim follows.

## New Formal Failure on October 4, 2026

The unchanged candidate passed 163 fresh admission commands, then emitted 33
matching status/facts rows through `destroy_acquire`. OS loader exit was zero,
but the loader-role guest/process exit events, PE terminal and last six rows
were absent. The verifier correctly refused `pair_guest_exit_missing`. Owned
cleanup completed, the sentinel survived, all 20 raw-stream hashes checked,
and all 2,788 signed bundle inventory entries remained unchanged. Native case
time was 6,382 ms; the complete failed operation including admission was
1,115,783 ms. The normal post-execution full provenance replay was not reached.

The failed output is `.build/task7/stage5-final-pairing1`. Its case receipt is
`25fc223ab323916fe18b88082921ea36d99e5c334591039c4903c2a9a448e7cd`;
the failure receipt is
`81596053d30f70759b3a022a03add5fb3baf86f38de377923a31893855beeb7b`.
A loader-only nine-second system-log query found no confirmed cause, and no
matching Wine/Pear crash report was found in the checked user report directory.
Neither absence establishes that no exception occurred.

One narrow diagnostic using the already authorized debugger copy captured an
`exit_process` stop with `NtTerminateProcess` as its caller and exit argument
zero. That diagnostic completed all 39 rows with balanced physical lifetimes,
acknowledged debugger detach, complete Wine/debugger cleanup and surviving
sentinel. It observed normal completion, not the failed original-candidate exit.
The ordinary verifier correctly rejects its changed fixture/signature route
with `pair_launch_changed`. No bad-access or causally useful failing stack was
captured; do not start additional identical attempts to obtain one.

A narrow source review confirmed that `willRemoveSubview` clears the cached
Metal view and that lease release retains the binding until its last lease is
removed. That reading does not prove arbitrary lifetime safety or identify the
failure. No production fix was applied. The next useful discriminator would
separate ordinary Wine window teardown from Metal attachment teardown under
explicitly controlled conditions; further work must target that evidence gap.
A same observation boundary does not by itself prove a shared cause with the
original access violation; preserve their different exit signatures.

## Evidence Retention

Retain the original case/failure receipts, raw captured streams referenced by
those receipts, source/producer identities, exact input/build/signing identities
and the procedure above. Keep required original inputs or verified restorable
copies for active consumers. Public records contain sanitized outcomes and
hashes, not raw private diagnostics, signing profiles or account data.

Incident preservation does not require every large diagnostic build or prefix
to remain forever. Only reproducible duplicates unreferenced by active checks,
other tasks or retained replay evidence may become cleanup candidates. A GitHub
hash or document is not a backup of its referenced bytes. Review dependency and
restore requirements before any deletion; this incident record authorizes none.

## References

- [Implementation plan](../plans/task_m1_7_impl.md)
- [Sanitized Stage 5 observations](../working/task_m1_7_stage5_reconstruction_observations.json)
- [DXMT build and pairing guide](../../docs/development/dxmt-build.md)
