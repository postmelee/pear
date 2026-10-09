# Task #40 Stage 3 — GameAssembly Initialization and Runtime Regression

GitHub Issue: [#40](https://github.com/postmelee/pear/issues/40)
Implementation plan: [task_m1_40_impl.md](../plans/task_m1_40_impl.md)
Stage: 3 — complete, October 9, 2026.

## Stage Purpose

The unchanged owned GameAssembly now loads and returns successfully from process
attach. Execution then opens IL2CPP metadata and starts its GC finalizer thread.
The required same-candidate CPU/ordering/graphics matrix passes. Startup still
fails to finish within the 120-second observation bound: menu, Steamworks and
playable Megabonk remain unqualified.

Context: approved Stage 3 continuation, root/runtime/host/test and DXMT/FEX rules,
approved plans and Stage 2 report, current #40/#11 scope, and existing #6/#8
oracles. The stage-report and repository todo procedures apply. The Pear Apple
router selected `using-metal-validation` at Apple revision
`4f42344c90be22112f46becc3fb9687f423f2f88`, plugin `1.0.0-beta.1`; its original
skill and local MetalValidation manual were read. Existing Wine supervision
supplies environment before device creation and verifies target-process validation
markers; the generic `open --env` example does not replace that owned launch
protocol. No Apple plugin, OS component or new signing grant was installed.

## Artifacts

| File | Change Summary |
|---|---|
| `tools/wine/image_initialization_{run,trace_run}.py` | Initial owned launch and one focused file/thread diagnostic, preserving prior exact-byte producers |
| `tools/wine/image_initialization_check.py` | Exact image/PID, publication, same-thread attach return, metadata open and GC-start evidence |
| `tools/wine/image_initialization_regression{,_run}.py` | Existing CPU/ordering reference oracles and fixture supervision admitted against #40 |
| `tools/wine/image_initialization_{pairing,graphics,matrix}.py` | Original native, pixel, frame and scalar-recovery checks on one corrected candidate |
| `tools/wine/image_initialization_qualification.py` | Full raw-evidence replay with explicit non-gameplay scope and downstream owner |
| `tests/wine/test_image_initialization.py` | Mapping-only, missing/failed attach, missing/wrong next phase and foreign-candidate rejection |
| [Allowlisted observations](task_m1_40_stage3_observations.json) | Public hashes, outcomes, limits and responsible follow-up Issue |

## Body Change Scope / Lossless Preservation

No native source, patch, binary or signing change was needed after Stage 2.
The candidate still has 41 native images with an ARM64 closure. Stage 1 and Stage
2 producers, original failures and the owned game remain unchanged. No full Wine,
FEX, DXMT or shader rebuild was performed. Existing C/C++/assembly implementations,
licenses, APISession, authorization, cleanup and mathematical oracles are reused.

The current runner copies preserve historical exact-byte evidence, but must not
become a per-option pattern. Following coordination review, further full copies
are prohibited in this task. The concrete narrow follow-up is the two current
game-runner entry points: separate a reviewed callable, candidate admission and
fixed diagnostic choices, and bind common source/configuration hashes for new
runs. Do not modify historical producers or claim these runs validate a future
adapter. No generic interpreter, protocol or new test engine is proposed; no
refactoring-triggered native reruns were added to this stage.

Only approved task/work artifacts changed. Official guide updates remain Stage 4.

## Verification Results

Host: M4 Pro, ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113), retained LLVM-MinGW
inputs and existing development-profile authorization. These are instrumented
correctness runs, not performance or power comparisons.

- **Original game:** 69 owned files verified and cloned, with originals unchanged
  before/after both runs. App 3405340, depot 3405342, manifest
  `446680890915713051`; this is the pinned September 27 snapshot, not a latest-build
  claim. No authenticated Steam prefix, app-id override, API stub or game patch.
- **GameAssembly:** SHA-256
  `4350a7ae25ba7aec35677c213fdceabbb638676bb00ab59131d7d9c37b6e3d9e`.
  The actual 57,647,104-byte guest image publishes with 429,566 relocations and
  zero native executable guest pages. Exact file identity, module path/base and
  raw loader events bind the observation to that DLL.
- Wine records `MODULE_InitDLL ... GameAssembly.dll ... PROCESS_ATTACH - CALL`,
  the matching address/thread `RETURN 1`, then `process_attach ... - END`.
  Later file tracing records the exact owned `global-metadata.dat` read-open and
  a valid returned handle. Thread tracing subsequently records `GC Finalizer`.
  This establishes DLL initialization plus a named later IL2CPP stage, not full
  IL2CPP initialization, a responsive menu or gameplay.
- **CPU:** all 19 declared cases assessed: 18 pass against the original Windows
  x64 reference; AVX remains unsupported/not exposed, not counted as execution
  success. **Ordering:** 32,768 measured pairs, eight worker lifetimes and checked
  retirements pass the existing policy/forbidden-outcome assertions.
- **Graphics:** device; native 39 and v2 surface 23 controls; five rendering cases
  with seven readbacks; 18 individually visible frames with resize and teardown;
  nine physical objects created/destroyed, zero remaining leases/attachments;
  both original delivered-scalar fault fixtures recover and exit 42.
- **Four new evidence controls pass**, zero skips. Stage 2's 27 checks are retained
  for the unchanged candidate/inputs; they were not unnecessarily rerun.
- Every restricted run passes before/after authorization, owned-child cleanup,
  sentinel survival and observed native architecture checks. This is not #10's
  complete late-module coverage or ordinary-user distribution qualification.

Commands used, with private roots supplied through existing retained inputs:

```sh
python3 -B -m tools.wine.image_initialization_run --inputs .build/task40/inputs2 --runtime .build/task40/correction-runtime1 --case game-start --output .build/task40/game-initialization1
python3 -B -m tools.wine.image_initialization_trace_run --inputs .build/task40/inputs2 --runtime .build/task40/correction-runtime1 --case game-start --output .build/task40/game-initialization2
python3 -B -m tools.wine.image_initialization_check --run .build/task40/game-initialization2 --require initialized
python3 -B -m tools.wine.image_initialization_regression --runtime .build/task40/correction-runtime1 --cpu-repo "$PEAR_TASK6" --reuse "$PEAR_TASK7" --seed "$PEAR_TASK8/.build/task8/device15" --suite corpus --name stage3 --output .build/task40/stage3-cpu.json
python3 -B -m tools.wine.image_initialization_matrix --runtime .build/task40/correction-runtime1 --cpu-repo "$PEAR_TASK6" --output .build/task40/stage3-matrix.json
python3 -B -m tools.wine.image_initialization_qualification --index .build/task40/stage3-index.json
python3 -B -m tools.wine.image_initialization_qualification --index .build/task40/stage3-index.json --verify-only
python3 -B -m unittest discover -s tests/wine -p test_image_initialization.py -v
python3 -B tools/check_governance.py
git diff --check
```

Two assessment corrections did not rerun native execution or remove an approved
check. The first adapter incorrectly applied timed-display qualification to the
original scalar-recovery fixture. It now reuses #8 `stage_three`'s exact
boundary/terminal/backend/recovery gate for that fixture; the separate 18-frame
fixture retains every visible-frame and lifetime assertion. Original zero callback
timestamps remain zero and do not qualify timing. The second correction normalizes
three callback tuples to their JSON-array representation for exact replay equality.
Both initial refusal records/assessors are retained privately. Final qualification
recalculates raw logs, images and reference results rather than trusting saved flags.

## #11 Handoff: Later Startup Stall

The active owner is **#11 game-start compatibility integration**, whose plan at
`09ea427` includes responsive menu and Steamworks initialization. #12 retains
combat, input/audio and save/relaunch. This handoff does not expand #40 into all
later game bugs or claim that the stall is a Steam defect.

Stable candidate receipt:
`d6d053e73eb0a7625177e1901936efeed4ee7eddadd9e822a0094398e8505808`.
Build receipt: `2669cf597681ba30c96bcb73395c132c71c53db3951732741b5171a1a1f89878`.
Native correction/provenance is committed in `7ef56cd`, following diagnostic
`8487781`, on integrated base `29f04a3`. There is **no uncommitted runtime-source
dependency**. Stage 3 producer/checker sources are in this report's enclosing
commit; consumers must use that commit and the qualification's recorded hashes.
Retained private dependency trees are still required; clean-machine assembly is #13.

Last confirmed progress: successful GameAssembly attach, successful IL2CPP metadata
read-open, and GC finalizer startup. The subsequent initialization interval is
unresolved. Both attempts reach the 120-second limit; owned termination produces
loader exit `-15`, with total cleanup-inclusive intervals of 125,121 and 125,111 ms.
Player.log remains empty. All children are reaped, the sentinel survives, original
files/runtime remain unchanged and authorization passes. **The GC thread name is
not evidence of a GC deadlock.** Repeated continuation/overcommit diagnostic lines
are observations, not a demonstrated root cause.

Attempt 1 used existing `+loaddll,+seh,+module` with image-admission markers;
attempt 2 additionally used `+file,+thread`, producing about 1.35 MB of stderr.
These diagnostics can perturb timing. The second run was required to identify a
named subsequent operation; neither run establishes real Steam startup. A brief
shared-lock conflict before attempt 2 caused no launch and was retried only after
the lock was free.

Minimum next diagnosis: #11 should first inspect these preserved traces, then use
an isolated experimental candidate/prefix and one bounded post-metadata thread/
continuation-state observation to distinguish ongoing initialization, waiting and
resume-loop behavior. Reuse a fixed diagnostic choice or small adapter, not another
full runner copy. Map observed native/guest PCs to exact binaries before assigning
a cause. Do not change this loader/arena independently or overwrite its source,
immutable candidate or evidence; coordinate any actual shared-boundary correction
with #40. Keep experimental observations separate from this finite qualification.

Private handoff and replay inputs, all under the retained #40 task root:

- `.build/task40/stage3-handoff.json`: read-only consumer routing and exact paths.
- `stage3-index.json`, `stage3-qualification.json`, `stage3-cpu.json`,
  `stage3-ordering.json`, `stage3-matrix.json`: stable candidate-bound records.
- `game-initialization1/` and `game-initialization2/`: raw diagnostics, isolated
  prefixes, original-byte clones, run records and initialization assessments.
- `inputs2/`, `correction-build1/`, `correction-runtime1/`, original retained #8
  seed, graphics result prefixes and frame images: required replay dependencies.
- `stage3-verification/`: test/replay logs and preserved initial assessor refusals.

Completed CPU and ordering scratch prefixes were removed after evidence admission.
Graphics prefixes remain because byte-origin replay and the native seed require
them. Do not delete failed-game contexts or these consumer inputs during cleanup.
Reuse is valid only while source, patch, tool, binary, signature, fixture, settings
and claim scope match; relevant changes invalidate affected execution evidence.
No additional full build is needed merely to read the handoff.

## Residual Risks

- Actual startup remains unresolved after the named next phase; no menu, Steamworks,
  gameplay, performance or M1 completion claim.
- Complete process/module observation and ordinary-user distribution remain open.
- Visible frame correctness is established; many callback timestamps are zero,
  so drawable timing is explicitly unqualified.

## Impact on Next Stage

Stage 4 can document this bounded loader result in the approved existing guides,
replay the final evidence and prepare the final #40 report/PR. #11 owns the later
startup integration with the boundaries above. Existing approval/merge rules apply.

## Approval Request

Approve Stage 3 and continue to Stage 4 documentation, reproduction and final report.
