# Task #40 Stage 2 — Bounded Large-Image Loader Correction

GitHub Issue: [#40](https://github.com/postmelee/pear/issues/40)
Implementation plan: [task_m1_40_impl.md](../plans/task_m1_40_impl.md)
Stage: 2 — complete, October 9, 2026.

## Stage Purpose

Implement the approved 64 MiB per-image budget and verify real large-DLL loading,
initialization, relocation, failure cleanup and unload/reuse under native ARM64
Wine and the x64/FEX path. These are original redistributable fixtures, not game
qualification. Unchanged GameAssembly initialization remains the Stage 3 gate.

Context used: approved Stage 1 report/budget and requester continuation; root,
runtime, host and test rules; architecture, runtime contracts, source qualification,
delivery plan, task/implementation plans and current open Issues/worktrees.
The stage-report and repository todo procedures apply. Metal-specific expertise
is not applicable to this loader-only correction. #10/#11 worktrees were preserved.

## Artifacts

| File | Change Summary |
|---|---|
| `runtime/wine/patches/gameassembly/0002-image-admission.*` | Ordered, exact-preimage 64 MiB limit correction and MIT provenance |
| `tools/wine/image_admission_correction_build.py` | Dependency-bound isolated ntdll relink, unmodified-origin control and two affected objects |
| `tools/wine/image_admission_correction_runtime.py` | One corrected signed ntdll overlay retaining final #8 FEX/graphics components |
| `tools/wine/image_admission_fixtures.py` | Native/guest PE builds and explicit synthetic image-size variants |
| `tests/wine/fixtures/image_admission_pe.c` | Original DLL/driver with real attach, exported code/data pointers, large zero-fill data, failure, unload and reload |
| `tools/wine/image_admission_correction_run.py` | Existing owned supervisor, synthetic prefix, current authorization and immutable input checks |
| `tools/wine/image_admission_correction_check.py` | Raw terminal, publication/retirement generation, role, relocation and cleanup assessment |
| `tests/wine/test_image_admission_correction.py` | Actual corrected parser under UBSan; reuses meaningful #4 controls |
| `tests/wine/test_image_admission_loader_evidence.py` | Reject incomplete, unrelocated, unreused and unsupervised observations |
| [Stage observations](task_m1_40_stage2_observations.json) | Allowlisted hashes and results without proprietary inputs or private paths |

## Body Change Scope / Lossless Preservation

The runtime correction changes one bounded constant from 38,993,920 to 67,108,864
bytes. Stage 1 established the actual first refusal and memory budget before this
change. The existing 1,050,345,472-byte PE interior, 756 slots, dynamic region,
FEX regions and 1,588,985,856-byte integrated mapping remain unchanged. The bounded
relocation-array limit follows the image limit; the Stage 1 maximum temporary
payload calculation remains 100,679,768 bytes, excluding allocator overhead and
other process memory. No performance or final game memory claim follows.

Wine C and Pear's existing parser, relocation, staging, slot and page-publication
implementation are reused. The only header consumers are `pear_pe_arena.c` and
`virtual.c`; the builder checks this source dependency set, compiles these two
objects and records compiler dependencies. A control relink first reproduces the
actual #5 native origin used by the final #8 runtime. All other qualified object
inputs and the final FEX/graphics overlays remain intact. No full Wine rebuild,
new owner ABI, new security entitlement, Rust rewrite or upstream submission.

Stage 1 producers and original failures remain unchanged. Separate correction
adapters preserve their exact-byte replay contracts while reusing the same build,
signing and APISession primitives. The only runtime code replacement is ntdll;
41 native images retain an ARM64 dependency closure and the existing development
signing/provisioning path. Fixtures are separately identified PE inputs, not
proprietary payloads or an ordinary-user distribution.

The fixture generator alters only its own synthetic PE `SizeOfImage` after
compilation, never the game. Successful DLLs contain 57,600,000 bytes of zero-fill
data and genuine code/data DIR64 relocations. Both the required size and ceiling
execute DLL attach and an exported probe, then unload and reload at the same
compatible address. Every reload proves reset data, initialized state and two
working relocated pointer cells. Deliberate attach rejection is a normal loader
failure; no deliberate fatal host fault was introduced.

Documentation changes are limited to the approved task plan, daily board and
stage artifacts. Official integration guidance remains Stage 4 work.

## Verification Results

Execution context: ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113), the retained
LLVM-MinGW toolchain and existing development profile. Native parser checks use
Clang UBSan. Runtime runs enable existing loader diagnostics; they are correctness
runs, not performance measurements. Native compilation and restricted execution
used the existing shared lock.

Evidence reuse: retained #8 final runtime and synthetic prefix were admitted by
historical readers; original #5 native object identity was control-relinked.
Unchanged upstream inputs are reused, but changed-candidate loader execution was
newly performed. Historical CPU/graphics success does not qualify this candidate;
the approved Stage 3 matrix is still required.

Commands run (paths are task-owned under `.build/task40`; private roots omitted):

```sh
python3 -B -m tools.wine.image_admission_correction_build --inputs .build/task40/inputs2 --mode correction --output .build/task40/correction-build1
python3 -B -m tools.wine.image_admission_fixtures --inputs .build/task40/inputs2 --output .build/task40/fixtures1
python3 -B -m tools.wine.image_admission_correction_runtime --inputs .build/task40/inputs2 --build .build/task40/correction-build1 --output .build/task40/correction-runtime1
python3 -B -m tools.wine.image_admission_correction_run --inputs .build/task40/inputs2 --runtime .build/task40/correction-runtime1 --fixtures .build/task40/fixtures1 --role aarch64 --case loader-fixtures --output .build/task40/loader-arm64-1
python3 -B -m tools.wine.image_admission_correction_run --inputs .build/task40/inputs2 --runtime .build/task40/correction-runtime1 --fixtures .build/task40/fixtures1 --role x86_64 --case loader-fixtures --output .build/task40/loader-x64-1
python3 -B -m tools.wine.image_admission_correction_check --run .build/task40/loader-arm64-1 --require loader
python3 -B -m tools.wine.image_admission_correction_check --run .build/task40/loader-x64-1 --require loader
PEAR_IMAGE_ADMISSION_BUILD=.build/task40/diagnostic-build2 PEAR_IMAGE_CORRECTION_BUILD=.build/task40/correction-build1 python3 -B -m unittest discover -s tests/wine -p 'test_image_admission*.py' -v
git diff --check
```

Results:

- **27 tests passed, zero skipped.** Includes retained Stage 1 checks, 14 corrected
  parser/owner checks and four loader-evidence controls. Required size and exact
  64 MiB pass; 64 MiB + 4 KiB and overflowing image geometry reject. Invalid
  sections, malformed/overlapping/out-of-range relocations, stale generation,
  exhausted allocation and incompatible backing controls remain effective.
- **ARM64: 8/8 execution conditions passed**, exit 42, 6,813 ms including cleanup.
- **x64/FEX: 8/8 execution conditions passed**, exit 42, 4,474 ms including cleanup.
  Each run covers two ceiling refusals, two attach failures and four initialized
  load/call/unload cycles across the required and ceiling sizes.
- The exact file/PID diagnostics prove two `parser.return08` size refusals and two
  successful publications for each admitted DLL. Six large-image publications
  each have a matching generation-specific retirement. Failed attachment reuses
  its released slot before subsequent successful loads.
- Native published code pages remain executable under the existing page-WX
  policy. x64 guest publications have **zero native executable code pages**;
  FEX initialization and guest exit are observed. Both preserve relocation and
  generation checks rather than relaxing native/guest separation.
- Before/after authorization, immutable fixtures/runtime, owned-child reaping,
  sentinel survival and observed ARM64 processes/modules passed. Complete late
  module coverage remains #10's separate scope.
- Raw build/run records and final inputs remain ignored and local. Two completed
  synthetic execution prefixes (about 804 MiB each by `du`, with APFS shared
  storage) were removed; both assessments replayed successfully afterward.
  Original failures, game clone, retained seed and final candidate remain intact.
  Physical space recovery is not inferred from the clones' logical size.
- Actual GameAssembly initialization, full changed-candidate CPU/graphics
  qualification, Steam and gameplay were **not performed in Stage 2**.

## Residual Risks

- Raising admission does not prove that the actual game's remaining layout,
  initialization or Windows APIs succeed. Those are Stage 3 observations.
- Finite original fixtures do not establish arbitrary PE or game support.
- Development-profile authorization is not ordinary-user distribution approval.
- No thermal, frame-time or power improvement has been measured.

## Impact on Next Stage

Use `correction-runtime1` as the candidate and retain its exact build/overlay
identities. Next, launch the unchanged owned game, require actual GameAssembly
initialization completion and a named later Unity/game phase, then run the
approved same-candidate CPU/ordering and affected graphics checks. A mapping
success alone cannot close #40. Record subsequent Steam/game blockers for #11/#12.

## Approval Request

Approve the Stage 2 artifacts and results, then continue to Stage 3 original-game
initialization and changed-candidate regression verification.
