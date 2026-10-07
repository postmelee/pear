# Task #5 Stage 3 — Executable Memory and Source Lifetimes

GitHub Issue: [#5](https://github.com/postmelee/pear/issues/5)
Implementation plan: [task_m1_5_impl.md](../plans/task_m1_5_impl.md)
Stage: 3 — completed for the approved finite integration profile, October 7, 2026.

## Stage Purpose

Connect the single-address Wine JIT owner to actual FEX source lifetimes and
ARM64EC registration, publication, quiescence and retirement. The requester
approved joint Stage 3/4 development and reassessment of the former prototype
metadata ceiling. Stage 3 completion is not game or distribution qualification.

Context used: root/runtime/FEX/tests rules, current plan and memory design,
Stage 2 report, architecture/runtime contracts, recorded upstream reuse review,
Hyper-Waterfall stage-report/todo procedures. Retain FEX MIT C++/assembly and
Wine C; Madeira remains a source reference, with no GPL fork code imported.

## Artifacts

| File | Change summary |
|---|---|
| `runtime/fex/patches/memory/` and ordered manifests | Source85 checked construction, memory/source/link/cache/publication/retirement integration |
| `runtime/fex/patches/integration/` | Shared Stage 3/4 candidate: actual module roles, bitmap callback, EC source gates and read-only metadata |
| `tests/fex/ec_memory_lifecycle.h`, `ec_concurrent_lifetime.h` | Development-only actual EC lifecycle and simultaneous-source checks |
| `tests/fex/integration_layout.cpp` | Same-compiler full-object sizes; no runtime constructor execution |
| `tools/fex/integration*.py`, affected memory builders/readers | Paired private candidates, real supervision and bounded focused assessment |
| Current plan/design/checkpoint and frozen history | Compact current authority; preserve earlier failures without importing obsolete next-step instructions |

## Body Change Scope / Lossless Preservation

The integrated candidate includes Stage 4 entry plumbing because actual EC
memory validation depends on its real translator admission. Stage 4 API/callback
acceptance remains separate. The wire ABI, finite owner capacities, 23-patch Wine
baseline and normal security protections are unchanged. No public product
contract or second roadmap is introduced. Private prefixes, signing material,
raw logs and game content are excluded from Git. Debug DLLs were losslessly
compressed only after decompression matched their original bytes; recipes,
failures and required base objects remain.

## Verification Results

Execution context: this Apple Silicon Mac, ARM64 native Wine compatibility
process with observed 4-KiB user pages, recorded LLVM-MinGW inputs and current
development profile/signature validation. Correctness instrumentation only.

Commands run (private roots abbreviated):

```sh
python3 /private/tmp/pear-fex-integrated-build17.py
python3 tools/fex/integration_runtime.py [recorded paired inputs] --output .build/task5/integration-runtime19
python3 tools/fex/integration_run.py --runtime .build/task5/integration-runtime19 --output .build/task5/integration-run20 --reuse <recorded-native-supervisor> --prefix-template .build/task5/integration-prefix-template4
python3 tools/fex/integration_assess.py --run .build/task5/integration-run20 --runtime .build/task5/integration-runtime19 --layout .build/task5/integration-layout2 --output .build/task5/integration-acceptance2
```

| Required boundary | Result and evidence scope |
|---|---|
| W^X, allocation classes, publication, source snapshots/patch/link/cache invalidation, retained references and cleanup | Prior actual Source85 finite native case `1ea8e36051c5bd7ff870baacc7119e7bc270d03caaf9b2618eb010b198ace979`; unchanged algorithms reused, not relabeled EC execution |
| Ordinary simultaneous owner protocol and failure controls | Four native workers, 32 schedules, 96 handoffs/leaf calls and polls; receipt `24d0f0737fd25779240ddd335053d2f3f3605c863a08c93661ef8b0683110aef` |
| Real EC bitmap/roles/publication/partial shared guard/retirement/reuse | 62 checks passed in the actual selected translator and Wine bitmap |
| Real EC simultaneous lifetimes | Two distinct registered workers: active timeout 5, parked retained-pin refusal 3, released retirement and stale-entry rejection passed |
| Bitmap/native error handling | Previously passing actual callback under controlled VM responses/UBSan and read-only role/no-mutation controls; callback implementation unchanged |
| Aggregate finite resource profile | Reviewed 12.5-MiB estimate plus 3.5-MiB headroom; compiler/layout and actual metadata recorded in the current design |
| Actual guest continuation after memory checks | x64 NT API roundtrip exited 42; exact stack and representative nonvolatile GPR/SIMD checks |
| Host identity and cleanup | 21 native translation observations and 4,566 ARM64 image events; before/after authorization, owned cleanup and sentinel survival passed |

Assessment SHA-256: `5d3339af3023a9254f2d1e49f64b494c353f793af2dc0d0ff4406d48ae9d359e`.
Case SHA-256: `57bfa7ba38f2c8b82b68e203d71eb0fdd34260018e917b2c2ac96b972b59bb4e`.
Compiler layout SHA-256: `e24ff21061c34170d26835a65a8b2acb2d27987e19787da542d1ac14fca63a20`.
The complete commands, snapshots and raw outputs remain in private receipts.

Run18 retained an incorrect test expectation for active timeout; run19 exposed
that a retained pin is not a parked acknowledgment. The fixture now uses the
existing Poll operation and correct distinct refusal codes. Owner protections
were not relaxed. Both original failures and cleanup outcomes remain recorded.

## Residual Risks

- This closes the finite memory/source gate, not general concurrent teardown,
  delivered exception/context/suspend or translated self-modification (Stage 5).
- Worker process exit is observed; ordinary ThreadTerm is not yet qualified.
- Resource accounting is a finite conservative estimate, not physical RSS,
  allocator-span peak or a game-scale memory cap.
- Full late-load coverage, i386 qualification, game execution and distribution
  remain unperformed. Stage 6 retains fresh paired reconstruction.

## Impact on Next Stage

Retain the exact owner/gate behavior and original upstream lifecycle bodies.
Stage 4 must finish normal-module file/time/event/callback checks; Stage 5 must
connect teardown/notifications/exceptions to these source ownership rules.

## Approval Request

Continuation through Stage 4 completion and Stage 5 implementation was explicitly
approved in this thread. No repeated approval is needed for that scope. No GitHub
publication or Issue closure is performed.
