# Task #40 Implementation Plan — GameAssembly Image Admission

Task plan: [task_m1_40.md](task_m1_40.md)
GitHub Issue: [#40](https://github.com/postmelee/pear/issues/40)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Branch: `codex/task40`; base: `29f04a3daa028cb8e52e06af9ee74d15c7cbe11e`
Status: task and implementation plans approved October 9, 2026; Stage 1
implementation and diagnostic execution authorized by explicit continuation.
Stage 1 is complete; the [Stage 1 report](../working/task_m1_40_stage1.md) records
the exact native origin and proposed 64 MiB budget. Stage 2 and the 64 MiB
per-image bound were approved by explicit requester continuation on October 9,
2026. Stage 2 is complete; the [Stage 2 report](../working/task_m1_40_stage2.md)
records 27 passing tests and native/guest loader execution. Stage 3 was approved
by explicit requester continuation on October 9, 2026 and is complete.
The [Stage 3 report](../working/task_m1_40_stage3.md) records initialization,
regressions and the explicit #11 startup handoff. Stage 4 was approved by explicit
requester continuation on October 9, 2026 and completed after midnight on
October 10. The final report and PR draft await publication approval.
Stage 3 uses new `image_initialization_*` adapters to preserve frozen producers.
Frozen Stage 1 producers remain unchanged; correction adapters use the
`image_admission_correction_*` module prefix with the same planned CLI modes.
#10 (`4773150`) and #11 (`62f7430`) remain separate integration dependencies.

## Context and Reuse

Use the task plan's requirements, scoped rules, document locations and reuse
policy. The four-stage scope is unchanged. No new Metal design or technical skill
is needed for loader admission. Stage-report and final-report skills apply at
their respective boundaries; repository todo applies to board updates.

Planning inspected the retained #8 `build3` source. The actual entry is
`pear_pe_plan_read_target` in `dlls/ntdll/unix/pear_pe_arena.c`, called by
`virtual.c` after machine/offset/shared-mapping admission. The parser checks
machine, image flags and alignments before image size; all can refuse independently.
This refines the earlier reference to its native `pear_pe_plan_read` wrapper.
No runtime-first-failure attribution has yet been established.

The existing header keeps the PE interior at 1,050,345,472 bytes, a 38,993,920-byte
per-image limit, 756 image slots, a separate 524,288-byte dynamic region, and
integrated MAP_JIT geometry of 1,588,985,856 bytes. The latter includes FEX regions;
it is not all free PE capacity. Relocations and staging consume additional memory.
The first design choice is whether the existing interior suffices with a reviewed
per-image bound; do not enlarge the entire mapping without an observed need.

Read-only host checks during planning found ARM64, macOS 26.5.2, Xcode 26.6
(17F113), and approximately 13 GiB free. Current per-executable authorization is
not yet checked. #10 remains independent at `a16d49b`; a new `codex/task11`
worktree also exists. Preserve their sources and outputs, and keep Steam work in
#11. There were no open PRs at the planning query.

| Retained input | Identity / role | Reuse boundary |
|---|---|---|
| #8 final runtime | Receipt `f90b2a601f556595a07b38bfa695def75b7f1def9bb1018e7dacb73bf7444f5f` | Original failure baseline, not authorization for a changed candidate |
| #8 build3 | Receipt `1ba8ac8b92ba72ef54b85ef3a02d973660eb5168d89c5eaa393d085363f2dc90` | Composed Wine source and tool/command inputs; retain later owner/surface supplements |
| #8 managed surface and scalar repair | Exact final overlay records and source ledger | Preserve corrected native modules and FEX; never reconstruct from an earlier partial runtime |
| #6 CPU fixtures and Windows references | Existing build/reference receipts admitted by CPU readers | Unchanged reference semantics; new Pear execution after the loader change |
| #8 original game diagnosis | 69-file owned depot snapshot and private failure records | Original DLL/EXE identities, isolated synthetic prefix, no authenticated Steam state |

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Attribute refusal and budget the correction | Diagnostic evidence and concrete budget decision | Actual first-refusal branch, input identities, memory calculation |
| 2 | Correct image admission | Ordered patch, bounded fixture and signed candidate | Size/layout, relocation, rollback, unload/reuse and publication |
| 3 | Initialize the original DLL | Same-candidate game and regression results | DLL initialization, next stage, CPU/ordering and affected graphics |
| 4 | Reproduce and hand off | Existing guide updates and final report | Evidence replay, required checks and explicit next blocker |

## Document Location Check

| File | Planned Location | Stage Artifact Path | Match | Notes |
|---|---|---|---|---|
| Wine contributor guidance | Existing official guide | `docs/development/wine-host.md` | OK | Stage 4; preserve historical results |
| CPU guidance, if affected | Existing official guide | `docs/development/fex-host.md` | OK | No new CPU guide |
| Reports and allowlisted evidence | Work artifacts | `mydocs/working/task_m1_40_stage{N}.md` and matching observations JSON | OK | No raw proprietary diagnostics |
| Final report | Work artifact | `mydocs/report/task_m1_40_report.md` | OK | No second roadmap |

## Stage 1 — Attribute Refusal and Budget the Correction

### Artifacts and Changes

- Add `tools/wine/image_admission_inputs.py` to bind retained source/build/runtime,
  original failure and proprietary input facts. Export only allowlisted facts;
  private paths and raw logs stay in `.build/task40/`.
- Add `runtime/wine/patches/gameassembly/0001-admission-diagnostics.patch` and
  its provenance record. Add bounded opt-in reason markers at the actual caller,
  parser and reservation/publication outcomes. Preserve original return codes,
  cleanup, checks and lock behavior. No game bytes or memory policy change here.
- Add `tools/wine/image_admission_build.py` and `image_admission_runtime.py` as
  narrow adapters over the existing build/signing primitives. Copy only needed
  source/object inputs to fresh owned outputs, preserve source manifests and
  full dependency closure, and rebuild/relink affected ntdll targets from their
  recorded commands. Never relink against modified retained objects.
- Add `tools/wine/image_admission_run.py` and `image_admission_check.py`, reusing
  APISession, restricted bootstrap, authorization and cleanup. Correlate events
  with the exact image/file identity and mapping attempt; a same-status line
  from another DLL is not attribution. Preserve bounded output and failure logs.
- Review the pinned upstream Wine map/relocation path and current Pear/FEX
  supplements and licenses. Record reuse versus required new code in the report.
- Calculate actual section layout, image/slot rounding, relocation storage,
  staging peak, page metadata and simultaneous-load demand. Record a concrete
  proposed bound and fixture layout in the Stage 1 report for Stage 2 review.

### Verification

Run input admission, an isolated diagnostic build and one bounded owned launch;
repeat only after a changed diagnostic or unresolved observation. Diagnostics
must identify the first failing branch for the unchanged GameAssembly image.
An independently encoded redistributable PE checks that a marker distinguishes
size from an earlier flag/alignment rejection without changing the NTSTATUS.
Missing identity/events, wrong-image correlation and incomplete cleanup must fail
assessment. No full CPU/graphics rerun is required for this diagnostic-only stage.

Proposed CLI commands below become implemented interfaces, not existing tools:

```sh
python3 -B -m tools.wine.image_admission_inputs --baseline-repo "$PEAR_TASK8" --output .build/task40/inputs1
python3 -B -m tools.wine.image_admission_build --inputs .build/task40/inputs1 --mode diagnostic --output .build/task40/diagnostic-build1
python3 -B -m tools.wine.image_admission_runtime --inputs .build/task40/inputs1 --build .build/task40/diagnostic-build1 --output .build/task40/diagnostic-runtime1
python3 -B -m tools.wine.image_admission_run --inputs .build/task40/inputs1 --runtime .build/task40/diagnostic-runtime1 --case game-start --output .build/task40/diagnostic-run1
python3 -B -m tools.wine.image_admission_check --run .build/task40/diagnostic-run1 --require refusal
python3 -B -m unittest discover -s tests/wine -p 'test_image_admission*.py'
git diff --check
```

Resolve the owned game/snapshot locations from private retained evidence; never
hardcode credentials or publish those paths. Use the existing 120-second startup
bound and owned cleanup. Each build and run has immutable fresh output identities.
Required result: attributable refusal and budget/design recommendation, not a fix.

Commit: `Task #40 Stage 1: attribute GameAssembly image admission refusal`.

## Stage 2 — Correct Image Admission

### Artifacts and Changes

- Add `runtime/wine/patches/gameassembly/0002-image-admission.patch` with ordered
  provenance, based on the reviewed Stage 1 budget. Preserve original baseline
  patches and frozen producers. Update only affected capacity/admission tooling.
- Extend the Stage 1 builders for a correction candidate; retain final #8 graphics
  and FEX overlays. A full Wine rebuild is needed only if dependency-complete
  targeted relinking cannot establish the resulting native/PE identities.
- Add original `tests/wine/fixtures/image_admission_pe.c` and minimal generated PE
  layout variants, plus `tests/wine/test_image_admission*.py`. Reuse the native
  parser harness in `test_pe_arena.py`; bind it to the corrected composed source
  rather than assuming its historical default source is current.
- Test an initialized large DLL through Wine using `LoadLibrary`, an exported
  result and unload/reload. Test both original native publication behavior and
  the affected x64 guest role without weakening native/guest separation.

### Verification

Required positive image covers at least the observed 57,647,104-byte layout.
Exercise the selected aligned ceiling and next admissible alignment beyond it;
reject invalid section bounds, overlapping/out-of-range relocations and arithmetic
overflow using existing cases where applicable. Verify relocation at a different
base, failure cleanup, stale generation refusal and compatible unload/reuse.
Parser-only success does not qualify executable publication. No deliberate new
fatal host faults are needed for this task.

Use the Stage 1 interfaces with `--mode correction`, `--case loader-fixtures`,
and checker `--require loader`. Run the changed parser tests and source-bound
native fixture checks. Retain commands, source/patch/tool hashes, signatures,
actual stage markers and cleanup results. A skipped native prerequisite fails
this gate. Fixtures do not substitute for the actual game in Stage 3.

Commit: `Task #40 Stage 2: support the required GameAssembly image layout`.

## Stage 3 — Initialize the Original DLL and Revalidate the Runtime

### Artifacts and Changes

- Extend only the #40 runner/checker to admit its changed runtime and existing
  CPU/graphics fixtures; reuse #6/#8 semantics and Windows references unchanged.
- Record actual loader attach/initialization completion for GameAssembly and a
  named later Unity/game operation. Generic Unity startup text, a mapped address
  or absence of the old error is insufficient. If existing Wine module traces
  cannot prove initialization, add narrowly scoped loader entry/return diagnostics
  through source-built Wine, never by editing the game or stubbing Steam.
- Keep the normal game's Steam checks. Record any subsequent blocker for #11/#12;
  failure before DLL initialization remains a #40 blocker.

### Verification

Run `--case game-start` on the corrected final candidate, checked with
`--require initialized`; retain original-file hashes before/after. Before and
after each restricted run, verify actual authorization, owned children reaped,
sentinel survival, no supervision gap and unchanged immutable payload.

Run the full declared #6 CPU corpus and finite ordering on this exact candidate,
reusing `tools/cpu/compare.py` and `ordering.py` and the #8 adapters. AVX remains
explicitly unsupported/not exposed, never counted as a passing instruction test.
Because the shared PE loader changes, revalidate device, five rendering cases /
seven readbacks, 18-frame lifecycle, native 39 + v2 23 controls and the two original
scalar-fault fixtures on this candidate. Reuse unchanged shader/build provenance;
do not repeat independent graphics reconstruction. Sequence runs and dispose of
owned completed synthetic prefixes only after evidence verification.

The #40 checker must reject an old candidate's CPU/graphics result relabeled as
current, missing DLL initialization, missing next-phase evidence and cleanup
failure. Use only necessary regression runs; changes or failures justify reruns.

Commit: `Task #40 Stage 3: verify GameAssembly initialization and runtime regression`.

## Stage 4 — Reproduction and Handoff

### Artifacts and Changes

Read and update the existing approved guides with component reconstruction,
selected memory bounds, current execution recipe and measured limitations.
Write final report and allowlisted observations; reference actual #11/#12 blockers.
Preserve all original failures and the final candidate; identify removable exact
scratch duplicates instead of deleting evidence required by consumers.

### Verification

Recompute final assessment from raw matching inputs with the #40 checker in
`--verify-only` mode. Run relevant portable refusal tests, documentation governance
and whitespace checks. Documentation-only edits require no new native matrix.

```sh
python3 -B -m tools.wine.image_initialization_qualification --index .build/task40/stage3-index.json --verify-only
PEAR_IMAGE_ADMISSION_BUILD=.build/task40/diagnostic-build2 PEAR_IMAGE_CORRECTION_BUILD=.build/task40/correction-build1 python3 -B -m unittest discover -s tests/wine -p 'test_image_admission*.py' -v
python3 -B -m unittest discover -s tests/wine -p test_image_initialization.py -v
python3 -B tools/check_governance.py
git diff --check
```

Commit: `Task #40 Stage 4 + final report: record loader qualification and handoff`.
Publish through the final-report procedure after all criteria pass; merge is a
separate authorization. Do not report menu, Steam, gameplay or M1 success here.

## Stage Dependencies, Resources and Approval

Each stage requires its verification, committed report and requester continuation
before the next. Stage 1's completed report must include the concrete memory
budget for Stage 2 approval. New allocator/owner/ABI geometry beyond the existing
model requires an explicit amendment; diagnostic findings alone do not authorize it.

Use the existing shared native-compilation lock and task-owned output leases.
Estimate actual copy/build/runtime peaks before each build, use two compiler jobs
initially, and preserve a cleanup reserve. Current 13 GiB free is an observation,
not permission to fill the disk or proof a full rebuild fits. No new toolchain
installation or signing profile is approved. Missing current authorization is
reported honestly. Preserve read-only dependency worktrees and #10/#11 outputs.

Approve this implementation plan and Stage 1 diagnostic implementation/execution.
The task plan approval is already recorded and is not being requested again.


## Stage 3 Coordination Clarification

The October 9 coordination review was checked against #11's task plan at
`09ea427`: #11 owns normal game startup through a responsive menu and Steamworks,
including necessary game-start compatibility corrections. Hand off the observed
post-attach initialization stall to that owner; #12 retains combat, input/audio
and save/relaunch qualification. #40 continues to own this loader/arena correction
and its required regression evidence. Consumers inspect retained inputs read-only
and create separate experimental outputs; neither another source tree mutation
nor qualification of an experimental candidate is implied.

Preserve existing exact-byte runner producers and the in-progress matrix. Do not
add another full runner copy for a diagnostic flag. The next concrete cleanup
location is `image_initialization_run.py` / `image_initialization_trace_run.py`:
new execution should use a reviewed callable with separate candidate admission
and a fixed diagnostic allowlist, recording common code and selected settings in
its input closure. This is a narrow follow-up, not a new protocol or engine.
Do not retroactively claim that historical runs qualify that future adapter or
rebuild Wine merely to refactor Python. Current Stage 3 execution is not restarted.


## Stage 4 Execution Clarification

Use the implemented Stage 3 qualification command above instead of the planning
placeholder `image_admission_check --qualification`. The explicit diagnostic and
correction build variables select actual composed parser sources and prevent
native prerequisites being silently skipped. This updates command names to the
completed implementation without removing checks or adding runtime scope.
Only `docs/development/wine-host.md` needs an official guide change: #40 changes
Wine admission, not FEX code, ABI or reconstruction. Preserve `fex-host.md` and
its historical CPU claims. Stage 4 replays existing native evidence and reruns
only the required portable/parser checks; it does not repeat game execution.
