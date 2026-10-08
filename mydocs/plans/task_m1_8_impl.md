# Task #8 Implementation Plan — Translated D3D11 Qualification

Task plan: [task_m1_8.md](task_m1_8.md), approved October 8, 2026.
GitHub Issue: [#8](https://github.com/postmelee/pear/issues/8)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Status: Stage 1 complete; Stage 2 awaiting explicit continuation.

## Stage Overview

| Stage | Title | Main output | Verification |
|---|---|---|---|
| 1 | Coherent candidate and device path | Combined source/payload receipts, bounded x64 device fixture | Exact input admission, actual FEX/DXMT/Metal route and affected bridge checks |
| 2 | Rendering and readback | Deterministic C++/HLSL cases with independent expected values | Buffers, textures, shaders, compute, depth/blend and targeted validation |
| 3 | Presentation and lifetime | Bounded resize/present/device cycles | Actual presentation, callbacks, GPU completion and physical teardown |
| 4 | Integrated handoff | One final-candidate coverage record and contributor recipe | Complete required results, original failures preserved, remaining gaps explicit |

The approved task plan links applicable specifications, scoped rules, licenses
and reuse decisions. Keep upstream C/C++/Objective-C/HLSL and existing Python
orchestration; no new engine or generic evidence framework. Stage 1 may clarify
`runtime/dxmt/AGENTS.md` for approved #8 ownership, preserving #9/#10 boundaries.
Use stage-report/todo procedures at each completed checkpoint and final-report
only after integrated acceptance. No parallel agents or other-task edits.

## Planning Findings and Reuse Boundary

- Base: merged #6/#7 on `d019a6e`; #9 is independently active, observed at
  `75bf1e4`. No #8 source existed before this task. Preserve task-local board rows
  when integrating later #9 changes.
- #6 `tools/cpu/runtime.py` admits a fixed #5 Wine receipt and CPU-only fixture
  format. `pear_run.py` shares existing authorization, APISession, ownership,
  bounded output and cleanup, but requires a CPU-specific runtime kind/path.
  Reuse these primitives through #8 adapters; do not disable their guards or
  make old CPU records accept graphics observations.
- #7 `deterministic_pair.py`, `pairing_runtime.py`, `run_pairing.py` and their
  readers bind distinct native graphics construction/execution. Reuse source,
  tool, signature, dependency and diagnostic admission without changing the old
  producers, hardcoded historical pins or ordinary-native result scope.
- Read-only inspection of #5 `stage6-wine3/source` found neither
  `pear_macdrv_metal_v1.h` nor `pear_metal_bridge.m`. All **14** Wine change entries
  in the #7 graphics series match their recorded preimages, including absent
  added files. This supports applying the existing patch, not a completed build
  or ABI qualification. The installed `d3dcompiler_47.dll` exists; its actual
  shader-compilation route and imported dependencies remain unverified.
- Retained #7 `stage5-deterministic7/8`, final loader/runtime and native replay
  provide immutable graphics inputs. #6 `stage3-fex3` and both final signed
  fixture runtimes provide CPU inputs. Neither is an integrated #8 runtime.
- Actual planning host: ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113), installed
  Metal toolchain resolves through `xcrun`; `gpucapture` and `gpudebug` are absent
  from PATH. About 33 GiB free. Tool discovery is not compilation, permission or
  execution evidence. No new software installation is authorized by this plan.

### Selected Metal guidance

Read the original [using-metal-validation skill](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/using-metal-validation/SKILL.md),
revision `4f42344c90be22112f46becc3fb9687f423f2f88`, plugin `1.0.0-beta.1`, through
the Pear router; also read the relevant local `MetalValidation(1)` sections.
Set validation before device creation and route shader errors to stderr.
The skill's ordinary-app `open --env` recipe is not a replacement for Pear's
owned Wine bootstrap: retain explicit child launch/cleanup and verify the settings
inside the native device process before creation. No unowned LaunchServices run.

Initial correctness settings reuse #7: `MTL_DEBUG_LAYER=1`, API error `assert`,
warning `nslog`, `MTL_SHADER_VALIDATION=1`, fail mode `zerofill`, and
`MTL_SHADER_VALIDATION_REPORT_TO_STDERR=1`. The local manual confirms these modes;
shader zero-fill never makes a logged invalid access pass. Validate intended
process/pipeline instrumentation rather than infer it from the parent environment.
Capture/debug CLI guidance is not applied while tools are absent. Read pinned
presentation/lifetime guidance only when implementing the corresponding boundary;
reconcile it with actual SDK headers. No `.porting` lifecycle or plugin install.

## Document Location Check

| File | Approved location | Stage artifact path | Match | Notes |
|---|---|---|---|---|
| Graphics reproduction/coverage | Existing DXMT guide | `docs/development/dxmt-build.md` | OK | Final scoped addition; preserve historical native evidence |
| Affected CPU handoff | Existing FEX guide | `docs/development/fex-host.md` | OK | Only if integration changes its requirements |
| Component rules | Existing DXMT scoped rules | `runtime/dxmt/AGENTS.md` | OK | Acknowledge #8, preserve other task ownership |
| Fixtures/adapters | Existing test/tool roots | `tests/dxmt/translated_*`, `tools/dxmt/translated_*` | OK | No new public contract family |
| Plans/reports | Existing task folders | `mydocs/plans/`, `working/`, `report/` | OK | Sanitized observations only; raw records ignored |

## Stage 1 — Coherent Candidate and Device Path

### Artifacts

- `tests/dxmt/translated_cases.json`: declared operations, formats, oracles,
  required outcomes, limits and upstream provenance; `translated.cpp` for the
  initial x64 device path. Preserve borrowed file notices beside adapted code.
- Small `tools/dxmt/translated_inputs.py`, `translated_build.py`,
  `translated_runtime.py`, `translated_run.py`, `translated_check.py` adapters.
  Responsibilities are admission, affected construction, signing, owned execution
  and result assessment; reuse existing implementations rather than copy them.
- `tests/dxmt/test_translated_inputs.py` and `test_translated_results.py` for
  changed-input/backend and incomplete-result refusal. Add controls only for new
  observable failure behavior. Expand these files in later stages.
- `.build/task8/` holds private inputs/builds/runtimes/runs; Stage 1 report and
  allowlisted observations live in `mydocs/working/`.

### Changes

1. Re-admit retained #6/#7 sources, tools and final payloads. Inspect complete
   selected DXMT triangle/cube setup, shader compilation and destruction functions;
   bind exact borrowed files/notices. No model/texture assets are needed.
2. Apply #7's existing Wine graphics patch to a task-owned copy of the final
   #5/#6 Wine source using exact pre/postimages. Reuse existing native/ARM64EC build
   roles; inspect generated import archives/exports and required win32u/winemac/
   winemetal interfaces. Preserve loader reservation, owner ABI, x18 and JIT policy.
   Build only affected targets/dependencies if coherent; otherwise rebuild one
   shared Wine closure using the existing recipe and record why. Never mutate the
   retained object/source tree. A cached link step is not a fresh full build claim.
3. Reuse final #6 FEX DLL and verified #7 DXMT DLL/native shader dependencies where
   their exact imports, source interfaces and configuration match. Rebuild DXMT
   only if pairing changes invalidate it; no automatic LLVM or Metal rebuild.
4. Assemble one development runtime with a complete origin ledger. Resolve DLL
   precedence explicitly; inventory ARM64 Mach-O and ARM64X guest components and
   normal native dependency closure. Sign with existing authorized profile, then
   independently verify current payload and per-executable authorization.
5. Adapt a bounded x64 device fixture. Load D3D11/DXGI, create a hardware device,
   query the actual supported feature level and return a structured terminal.
   Require observed FEX dispatch, loaded graphics module paths/addresses matched
   to current hashes, native winemetal/Metal and actual native execution. Adapter
   names, static files, successful HRESULT or overrides alone are insufficient.
   Fail on substitute renderers and relevant observation gaps.
6. Reuse existing loader admission, owned process session, output limits and
   unrelated sentinel. Keep the 180-second outer bound; phase completion or
   failure must be explicit. No timeout extension merely to hide a failure.
7. Rerun #7's existing 39-case native pairing check on the changed bridge plus
   #6 `api-callback` and `abi-state` on the combined candidate. Reuse their exact
   fixtures/oracles; the new runtime gets new evidence. Other CPU results remain
   scoped historical results unless their inputs change (see reuse rules below).

### Verification

Planned module CLI below is to be implemented, not an existing executed command.
`PEAR_TASK5_REPO`, `PEAR_TASK6_REPO`, `PEAR_TASK7_REPO` select retained private
inputs. Each output is fresh. The input record selects admitted tools/build roles;
it is not authority to install tools or bypass signing.

```sh
python3 -B -m tools.dxmt.translated_inputs --cpu-repo "$PEAR_TASK6_REPO" --wine-repo "$PEAR_TASK5_REPO" --graphics-repo "$PEAR_TASK7_REPO" --output .build/task8/inputs1
python3 -B -m tools.dxmt.translated_build --inputs .build/task8/inputs1 --output .build/task8/build1
python3 -B -m tools.dxmt.translated_runtime --build .build/task8/build1 --output .build/task8/runtime1
python3 -B -m tools.dxmt.translated_run --runtime .build/task8/runtime1 --suite device --output .build/task8/device1
python3 -B -m tools.dxmt.translated_check --run "$PEAR_DEVICE_RUN" --runtime "$PEAR_GRAPHICS_RUNTIME"
python3 -B -m tools.dxmt.translated_check --qualification "$PEAR_STAGE1_INDEX" --require-stage 1
python3 -B -m unittest discover -s tests/dxmt -p 'test_translated_*.py'
git diff --check
```

The implemented stage index names the selected runtime/device/native-pairing runs
and full CPU/ordering run set after the core corrections. The standalone device
command is intentionally insufficient for stage completion.

The stage checker requires the separate current native-pairing and CPU regression
records described above, not flags declaring them passed. Preserve original errors,
raw logs and exact receipt hashes. Stage 1 is incomplete without actual translated
device/backend evidence and required cleanup, even if every build passed.

### Commit

`Task #8 Stage 1: integrate the qualified CPU and native Metal device path`

## Stage 2 — Deterministic Rendering and Readback

### Artifacts and Changes

Extend the existing declared fixture and checker, add `translated.hlsl` and exact
shader build/source identities. Use source-built `d3dcompiler_47` after its path is
admitted; otherwise select a separately justified redistributable shader route
within the approved source/tool constraints. No commercial-runtime extraction.

Freeze these small cases before running them:

| Case | Operation | Independent expected outcome |
|---|---|---|
| Buffer | Update/copy/map staging buffer | Exact declared uint32 sequence, including first/last elements |
| Texture | Upload/copy 8×8 RGBA8 texture and point-sample it | Exact texel pattern with row-pitch-aware readback; no sRGB conversion |
| Raster shaders | Draw into 64×64 RGBA8 UNORM target | Analytic constant-colored interior region and distinct clear region; exclude raster edges |
| Depth/blend | Occluding depths then fixed half-alpha overlay | Declared LESS/depth-write states and formula-derived colors; at most one UNORM unit/channel rounding tolerance |
| Compute | Bounded uint UAV transform, copy/readback | Exact integer function of input index, no floating-point tolerance |

Use values/regions that cannot pass on an all-zero, clear-only or unchanged output.
Expected-value formulas are independent of DXMT. Check every required mapped
row/element; record actual sizes/formats/pitches and unexpected HRESULTs.
Retain changed-output controls and incomplete-terminal rejection; add a logged
validation-error control so shader zero-fill cannot be mistaken for success.
Enable the selected API/shader validation before actual Metal device creation;
record current pipeline instrumentation and review stderr/system evidence if
needed. Do not require an unrelated GPU capture when readback and diagnostics
already decide correctness. Reduce any required failure before patching.

### Verification

```sh
python3 -B -m tools.dxmt.translated_run --runtime "$PEAR_GRAPHICS_RUNTIME" --suite rendering --output .build/task8/rendering1
python3 -B -m tools.dxmt.translated_check --run .build/task8/rendering1 --require-stage 2
python3 -B -m unittest discover -s tests/dxmt -p 'test_translated_results.py'
git diff --check
```

Use the newly built exact fixture/shader payload and matching signed runtime;
preparation reuses Stage 1 commands with fresh output paths. Expected: all five
cases complete and match, actual backend/policy admitted, no required validation
error, original errors retained, authorization and owned cleanup pass. No frame
rate or power conclusion. Commit: `Task #8 Stage 2: qualify translated rendering and readback`.

## Stage 3 — Presentation, Callbacks and Lifetime

### Artifacts and Changes

Extend the same fixture with **three sequential device/window cycles**. Each
cycle presents two frames at 64×64, two at 96×80 after resize and two after returning
to 64×64: **18 required presents**, with bounded message pumping and resize callback
counts. Read pinned presentation/lifetime guidance only for these boundaries;
retain DXMT's existing presentation API, rather than adopt unrelated Metal 4 APIs.

Wait for submitted GPU work before releasing its resources; exercise the real
window callback/bridge path and retain source-level native completion/lifetime
observations. Reuse #7 physical view/layer/proxy accounting. Require final balanced
creation/deallocation and zero leases/attachments, not only COM reference counts.
If deferred native destruction remains pending, pump the bounded required queue
and report incomplete teardown at the deadline; do not declare it a leak fix.

Readback alone proves rendered backbuffer contents, not screen presentation.
Require completion evidence from the real presentation path plus an observation
of the visible expected synthetic window before/after resize (captured owned
fixture image or explicit user observation). Do not capture unrelated app content.
A headless/unobserved window is unavailable presentation evidence, not a pass.

### Verification

```sh
python3 -B -m tools.dxmt.translated_run --runtime "$PEAR_GRAPHICS_RUNTIME" --suite presentation --output .build/task8/presentation1
python3 -B -m tools.dxmt.translated_check --run .build/task8/presentation1 --require-stage 3
python3 -B -m unittest discover -s tests/dxmt -p 'test_translated_results.py'
git diff --check
```

Require 18 successful presents, three complete cycles, real callback and GPU
completion records, final physical cleanup, intended loaded backend, bounded
owned process cleanup and sentinel survival. API/shader diagnostics remain scoped
correctness evidence. Commit: `Task #8 Stage 3: verify presentation and translated resource lifetime`.

## Stage 4 — Integrated Qualification and Handoff

### Artifacts and Changes

Bind all required case, reference, source, patch, tool, signature, runtime and
configuration identities in a final coverage report. Re-admit unchanged results
and rerun only invalidated ones. Extend the approved existing DXMT guide with
reproduction, measured scope and known gaps; change the CPU guide only if needed.
Preserve earlier native-only claims and failures. Produce Stage 4 observations,
report and final report; no game-qualified flag without the later game gates.

A bounded optional Megabonk diagnostic may follow a coherent path to locate the
next actual integration failure. Use owned existing files and normal account
checks; no Steam API stub, credential publication or save modification. Optional
diagnostic outcomes stay separate from #8 acceptance and do not replace #11/#12.

### Verification

```sh
python3 -B -m tools.dxmt.translated_check --qualification "$PEAR_GRAPHICS_QUALIFICATION" --require-stage 4
python3 -B tools/check_governance.py
git diff --check
```

Require every declared image/readback/lifecycle result, intended backend proof and
reviewed validation diagnostics on the final candidate. Unknown/unsupported
required features and missing records block completion. Final source and report
are committed together: `Task #8 Stage 4 + final report: record translated D3D11 qualification`.

## Revalidation, Storage and Workflow

- Fixture-only changes require the changed cases; source/config/receipt changes
  require their affected native and translated boundaries. Same-input historical
  #6 CPU and #7 build evidence retain only their original scopes.
- FEX or core loader/memory/ABI changes require the full affected #6 declared
  corpus and ordering checks; a graphics-only bridge change requires native pairing,
  callback/ABI and affected graphics checks. If dependency analysis cannot isolate
  a core change, treat its CPU evidence as invalidated. No required failure waiver.
- Keep one active combined build and candidate per iteration. Use verified source
  and tool reuse, APFS clones where appropriate and isolated new object directories;
  no edits to dependency caches or blanket copies of historical builds.
- Inherit the existing build monitor's 8 GiB growth/4 GiB free-reserve guards where
  applicable. Before construction calculate the actual phase footprint and shared
  free space; these guards are not a promise that 12 GiB fits every phase. Revise
  scheduling/output retention before exceeding the available budget. Remove only
  completed owned scratch after preserving required logs and checking ownership.
- No repeated full rebuild just for report/CI wording. Preserve exact failures and
  current dependency evidence. Raw paths/signing/captures stay private.
- Complete, verify, report and commit each stage before requesting continuation.
  Routine in-scope fixes use this authorization; ownership/ABI redesign, new global
  tools/permissions, official relocation or #9 contract conflict requires review.
- All verification commands above are planned; no GPU/guest test ran while writing
  this document. Worktree source changes start only after implementation approval.

## Current Integration Investigation

See [Stage 1 investigation notes](../working/task_m1_8_stage1_notes.md) for
construction results, preserved failures and pending gates. The existing Stage 1
repair authorization and core-change revalidation rule apply; no new owner ABI,
permissions, tool installation or stage transition is introduced.

## Approval Request

Approve this implementation plan and Stage 1: apply the existing graphics bridge
in an isolated Wine construction, assemble/sign the combined candidate and verify
actual x64 device creation/backend selection plus the affected native/CPU checks.
Later stages retain their explicit continuation checkpoints.

## Stage 1 Authorization

On October 8, 2026, the requester explicitly continued after implementation-plan
review. The planned source integration, development signing and bounded Stage 1
execution are authorized. Later stages retain their continuation checkpoints.
