# Task #6 Stage 2 — Native x64 and Pear CPU Comparison

GitHub Issue: [#6](https://github.com/postmelee/pear/issues/6)
Implementation plan: [task_m1_6_impl.md](../plans/task_m1_6_impl.md)
Stage: 2 — complete locally on October 8, 2026

## Stage Purpose

Compare the declared instruction and Windows ABI fixtures against an independent
native x64 reference, reduce required failures, and retain exact component and
execution identities. This establishes a finite CPU comparison, not Megabonk,
complete CPU conformance, multithread ordering or ordinary-user distribution.

Context: approved task/implementation plans; root/runtime/FEX/tests rules;
architecture, runtime contracts and current #5 memory design. Hyper-Waterfall
v0.3.0 task-stage-report and todo procedures apply. No Metal work applies.
The requester explicitly approved task-branch reference publication, confined
corrections and reruns. No master merge occurred.

## Artifacts

| File | Change Summary |
|---|---|
| `tools/cpu/generate.py`, `build.py`, `adapt.py`; `tests/cpu/runner.c`, `abi.c`, `seh.c`, `adaptations.json` | Source-bound ASM capture, 19 PE builds and explicit address adaptation |
| `tools/cpu/native_run.py`, `results.py`; `tests/cpu/test_harness.py` | Native architecture observation, bounded execution and strict independent result assessment |
| `.github/workflows/cpu-native-reference.yml` | Approved branch-only native x64 reference, pinned actions, read-only token and finite artifact retention |
| `tools/cpu/runtime.py`, `pear_run.py`, `run.py`, `compare.py` | Existing Wine/FEX signing, authorization, process supervision and observation reused for exact CPU inputs |
| `runtime/fex/patches/cpu/`; `tools/cpu/fex_build.py` | Independently hashed ARM64EC FEX correction and fresh component construction; no Wine rebuild |
| `tests/cpu/emitter_labels.cpp`; `tools/cpu/emitter_check.py` | Actual emitter-header branch-fixup and direct-emission refusal controls in NX host memory |
| `tests/cpu/test_execution_evidence.py`, `test_correction_evidence.py` | Reject incomplete/foreign execution, no-op source patches and substituted artifacts |
| [Sanitized observations](task_m1_6_stage2_observations.json) | Exact hashes, native origin, per-case result/evidence counts and retention boundaries |

## Body Change Scope / Lossless Preservation

Locations match the approved plan. No product guide or document destination
changed. Stage 1 source/golden provenance remains unchanged; an independently
hashed adaptation explicitly describes the executed absolute-address fixture.
Original #5 sources, Wine/FEX artifacts, signatures and reports remain immutable.
The final runtime is a new signed bundle with a separately identified FEX DLL.

The ASM generation/capture adaptation retains Madeira's GPL-3.0-or-later notice
and exception alongside original FEX MIT provenance. The CPU runtime correction
retains FEX C++ and its existing vector/allocator and instruction emitter.
No upstream contribution, engine rewrite, owner wire ABI change, permission
expansion, proprietary game content or signing material is included.

## Verification Results

Native reference: Windows Server 2022 x64, native machine `0x8664`, process
machine zero, 64-bit Python 3.12.10; AMD Family 25 Model 17 Stepping 1.
GitHub image `win22` / `20261004.326.1`. The actual architecture probe is required;
the workflow runner label alone is not evidence.

The final [native run 37729128660](https://github.com/postmelee/pear/actions/runs/37729128660)
at `03ebc15bac561cc36e6403b178b6cf11d479c1cb` passed all **19/19** PEs.
Build SHA-256: `77a734c951322789ef364de84b830ed803798e93f8da65311a1bbe9bb13293f3`.
The downloaded PEs, corresponding source, raw results and artifact digests are
retained locally; GitHub artifacts expire after 14 days.

Pear: native ARM64 M4 Pro, macOS 26.5.2, Python 3.14.4, existing development
provisioning and hardened signing path. Runtime SHA-256:
`fe921ee5bf1809870638ebc1ee98b4c3f805b1668b2280669c2968c62a40994d`.
Corrected FEX DLL SHA-256:
`143c3b18ea462eede35de256d66067148139001986881987d11de504c070eaf4`.
This is instrumented correctness evidence; no performance inference is made.

Final comparison: **18 passed, one explicitly unsupported, zero required
failures**. All exposed defined results equal the native same-PE reference.
The unsupported case is AVX lane preservation: Pear reports AVX unavailable and
XCR0 zero, returning the declared feature-absence exit 77. It is not a pass or
proof that AVX is unnecessary for the eventual game/Steam dependency set.

Passing coverage includes integer widths, carry/defined flags, scalar RMW,
packed/scalar floating point, conversion, configured memory, adapted absolute
displacement, Windows API/callback, TLS/worker, guest fault/data guard, changed
code, suspend/context, nested ABI register/SIMD preservation and SEH unwind.
Every candidate run passed current authorization before/after, observed ARM64
host/image checks, owned process cleanup and unrelated sentinel survival.
Complete late-loaded image coverage remains #10's responsibility.

Commands executed (task-owned paths shortened):

```sh
python3 -B -m unittest discover -s tests/cpu -p test_harness.py
python3 -B -m unittest discover -s tests/cpu -p test_execution_evidence.py
python3 -B -m unittest discover -s tests/cpu -p test_correction_evidence.py
python3 -B tools/cpu/emitter_check.py --source .build/task6/stage2-fex2/source --output .build/task6/emitter-control2
python3 -B tools/cpu/compare.py --manifest tests/cpu/corpus.json --build .build/task6/native-build3 --reference .build/task6/native-results3 --candidate .build/task6/candidate4.json --output .build/task6/stage2-comparison
python3 -B tools/check_governance.py
git diff --check
```

The 14 harness, four execution-evidence and four correction-evidence checks
passed. The actual emitter header bound 256 branch instructions to their exact
intended destination, retained zero allocation in direct mode, and rejected
private-reference use after resetting to direct mode. That control uses a host
allocator adapter, not the actual FEX allocator or executable generated code.
The actual translated ABI run separately validates the corrected PE runtime.
Governance passed for 25 documents and 231 targets.

### Failures reduced and resolved

- **Native line endings:** Windows checkout CRLF changed raw JSON bytes before
  execution. Canonical manifest comparison fixes contract identity; exact PE
  hashing remains required. The original failed CI run is retained.
- **Host result parsing:** an actual image observation exceeded the generic
  8-MiB reader bound. Only this private observation reader admits up to 64 MiB;
  guest output remains bounded at 1 MiB. The bootstrap record is admitted by its
  exact observed process identity before extracting guest results.
- **Absolute-address setup:** the unchanged Wine image arena occupied
  `0x7fff0000`, conflicting with the original `0x7ffff000` data page. The explicit
  fixture adaptation moves data accesses to `0x1000f000`, preserves every original
  register expectation and checks `LEA R8 = 0x7ffffff8` independently. Native and
  Pear pass the changed PE. Accesses at the original conflicting page were not
  executed successfully and are not claimed as qualified.
- **ABI hang:** the original same PE reached FEX `ForcedAssert` after
  `Unhandled long bind`. A logging-only diagnostic exposed ASSERT messages that
  the old ERROR-only filter suppressed; a second diagnostic identified the
  earlier Pear limit of 16 additional label references. The final correction
  uses upstream vector storage only while compiling into the existing ordinary
  NX staging buffer. Direct executable-owner emission retains fixed storage
  and refusal behavior; source range checks and later W^X publication remain.
  The unchanged ABI PE then returned 42 with all required state preserved.
- **Patch-preparation false success:** `git apply` from the ignored nested tree
  skipped every target while returning zero. Header verification detected the
  unchanged source; its run was interrupted through owned cleanup. Preparation
  now uses an explicit patch root and exact pre/postimage hashes. Both a focused
  negative test and reassessment of the actual old build reject the no-op claim.
- **Receipt role mismatch:** the comparator initially included the old #5 smoke
  fixture receipt in a three-component reconstruction comparison. It now selects
  the exact Wine/FEX keys; current #6 PE identities remain independently checked.
  Only comparison was rerun; successful guest observations were unchanged.

Evidence reuse: original #5 component admission and source, toolchain, signing,
supervisor and observer implementations were reused with exact identities. The
changed FEX invalidated prior Pear corpus evidence, so every declared case was
observed on the final runtime; its already-completed same-runtime ABI observation
was reused once. The native reference was not rerun for Mac-only changes because
its PE, capture and oracle inputs stayed unchanged. Only ARM64EC FEX was freshly
compiled; no unnecessary Wine or graphics rebuild occurred.

## Residual Risks

- Stage 3 actual per-thread ordering and multithread stress remain unperformed.
  This stage does not complete #6 or establish general CPU conformance.
- AVX and i386/WoW64 execution remain unqualified; eventual required helpers must
  be assessed separately. The corrected ARM64EC DLL is not a WoW64 build claim.
- Source objects and ordinary vector backing are ordinary upstream compiler
  allocations, outside #5's finite owner-bookkeeping estimate. No peak memory,
  game-scale concurrency or performance measurement is claimed.
- Original absolute-page access and complete late-load observation remain limited
  as described above. Megabonk, Steam, rendering and distribution are unperformed.

## Impact on Next Stage

Stage 3 must use this corrected FEX component and exact source/fixture identities.
Add actual two-worker ordering/atomic and necessary repeated lifecycle coverage,
observe each worker's effective policy, and keep finite outcome counts and
forbidden conditions explicit. Reuse unchanged passing boundaries at their
recorded scope; new runtime or fixture changes invalidate affected evidence.

Private evidence is under `.build/task6/`. Retain current source/build/runtime,
native inputs/results and unique failures. Completed synthetic prefixes were
removed only after cleanup, reaping, authorization and sentinel checks. No raw
private logs, profiles, credentials or runtime bundles are included in Git.

## Approval Request

Review Stage 2 and continue to the already planned Stage 3 ordering/lifecycle
implementation. No next-stage execution, master merge or Issue closure occurred.
