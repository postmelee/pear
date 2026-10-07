# Task #5 Stage 4 — Hybrid Loader and First x64 Dispatch

GitHub Issue: [#5](https://github.com/postmelee/pear/issues/5)
Implementation plan: [task_m1_5_impl.md](../plans/task_m1_5_impl.md)
Stage: 4 — completed, October 7, 2026.

## Stage Purpose

Execute original x64 PEs through actual source-built FEX and native ARM64 Wine,
including guest/native ABI return and required file/time/event/callback paths.
Context used: current plan/design, Stage 3 report, root/runtime/FEX/tests rules,
architecture/runtime contracts and stage-report/todo procedures. Joint Stage 3/4
source implementation was authorized and committed with Stage 3.

## Artifacts

| File | Change summary |
|---|---|
| `runtime/fex/patches/integration/` (Stage 3 shared commit) | Native/EC/ARM64X/guest classification, real selected module/bridge binding, initial intervals, entry/return and checked data overcommit |
| `tests/fex/first_dispatch.S`, `ec_roundtrip.S` | Arithmetic result and exact stack/representative nonvolatile integer/SIMD state |
| `tests/fex/guest_api.c` | Original file/time/event and real native-to-guest RunOnce callback fixture |
| `tools/fex/integration_runtime.py`, `integration_run.py`, `integration_assess.py` | Recorded signed pairing, owned execution and focused result assessment |

## Body Change Scope / Lossless Preservation

Reuse original MIT FEX entry assembly, context merge, nonlocal syscall transfer,
Windows tracking and Wine CHPE/redirection mechanisms. There is no engine or
language rewrite, Rosetta/commercial dependency, alias mapping or security
bypass. Preserve the recorded 23-patch Wine baseline and independent CPU series.
Private raw diagnostics, prefixes and authorization material stay outside Git.

## Verification Results

The final normal FEX candidate has **no finite test-header injection**. Its link
receipt is `e68a1d2b06ac2e6a3e94b52394f81d445ca4f80af776943cb95d14ac3472698d`. Wine pair8 is unchanged
from actual Stage 3 EC acceptance. Existing normal correctness checkpoints remain;
this is not a performance build or end-user distribution qualification.

```sh
python3 /private/tmp/pear-fex-integrated-build18.py
python3 tools/fex/integration_run.py --runtime .build/task5/integration-runtime20 --output .build/task5/integration-run21 --reuse <recorded-native-supervisor> --prefix-template .build/task5/integration-prefix-template5
python3 tools/fex/integration_run.py --runtime .build/task5/integration-runtime21 --output .build/task5/integration-run22 --reuse <recorded-native-supervisor> --prefix-template .build/task5/integration-prefix-template6
python3 tools/fex/integration_assess.py --run .build/task5/integration-run21 --runtime .build/task5/integration-runtime20 --output .build/task5/integration-dispatch-acceptance1
python3 tools/fex/integration_assess.py --run .build/task5/integration-run22 --runtime .build/task5/integration-runtime21 --output .build/task5/integration-dispatch-acceptance2
python3 tools/check_governance.py
git diff --check
```

- Original arithmetic fixture previously exited 42 through actual FEX.
- Final normal candidate NT API roundtrip exited 42; exact RSP, RBX/R12/R15 and
  low 64 bits of XMM6/XMM15 survived two calls with a positive timer frequency.
- File/time/event/callback fixture exited 42: positive NT time; create/set/wait/
  reset/event timeout; delete-on-close file write/read byte equality; native
  RtlRunOnceExecuteOnce entered the original x64 callback exactly once across
  two calls and returned the expected context. The file was absent afterward.
- Current profile/signatures before and after, observed ARM64/native processes
  and images, complete owned cleanup and unrelated sentinel survival passed.
- Previously passing actual parser/role/selected-module refusal controls are
  reused for unchanged code. No broad portable or Wine suite was repeated for
  fixture-only additions. Stage 6 retains affected final paired regressions.

| Assessment | SHA-256 |
|---|---|
| Normal NT roundtrip | `7d0ffd6f05156cb66b4c07d64fefe814b1d17085e2059b21c38eae0465944ef8` |
| File/time/event/native callback | `c1148a038505cb02a15f6c288163a018f11cae2909056819459d17e6a1ada5a5` |
| API fixture build | `499ec84d650b3efae2a4067721b9b2ec5247b133d63527fe091e5362f01ad3b2` |

These are actual translated x64 executions with finite recorded native-host
observations. Complete late-load timelines remain #10's scope; no unavailable
observation is represented as complete process coverage.

## Residual Risks

- Initialized synthetic APFS-cloned prefixes were used. This does not newly
  qualify cold installation; earlier cold attempts recorded unavailable optional
  syswow64/rundll32 initialization (c0000135), which is not required by these PEs.
- General thread teardown, translated invalidation, context/suspend and ordinary
  exceptions remain Stage 5. The callback test does not qualify all callback ABIs.
- Stage 6 fresh final reconstruction remains required before Issue #5 closure.
  Steam, Megabonk, graphics, performance and distribution were not tested.

## Impact on Next Stage

Retain the normal paired candidate as a regression baseline. Reuse original
FEX thread cleanup/notification/context implementations and connect them to the
actual source lifetime and quiescence protocol, rather than removing guards.

## Approval Request

The requester explicitly approved Stage 5 implementation after Stage 3/4 closure.
Proceed within that scope; no repeat approval, GitHub publication or Issue closure.
