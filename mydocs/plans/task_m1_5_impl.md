# Task #5 Implementation Plan — FEX Darwin Integration

Issue: [#5](https://github.com/postmelee/pear/issues/5)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Task scope: [task plan](task_m1_5.md)
Updated: October 8, 2026. State: Stages 3/4/5 completed locally; Stage 6 fresh reconstruction approved and in progress.

## Authority and approved direction

The requester approved reorganizing this plan and continuing development toward
actual x64 execution on October 7: “Proceed that way, and pursue the development
goal” (translated). This approves combining the remaining Stage 3 EC work with
Stage 4's real loader/first-dispatch implementation and reassessing the prototype
metadata limit. It supersedes the isolated Amendment D proposal and the old
requirement to complete every native-only experiment before developing loader
integration. It does not assert that Stage 3 passed or waive safety checks.

Stages 1 and 2 remain completed. Preserve their reports/commits. Stage 3 memory
and Stage 4 dispatch retain their identities, but share one integrated candidate
and development loop. Record each outcome separately and complete its required
checks/report/commit before marking it complete. This continuation authorizes
that integrated work; no repeated approval is needed for routine fixes within it.
The requester subsequently explicitly authorized completing Stages 3/4 and then
implementing Stage 5, maximizing upstream reuse. Stage 5 is approved after the
Stage 3/4 completion reports and local commits; Stage 6 keeps its later checkpoint.
No GitHub publication, Issue
closure, game support or general distribution is authorized by this continuation.

## October 8 reuse-document coordination

The requester authorized issue/development-document updates from the reviewed
reuse investigation and handoff to this implementation session. The coordinator
supplied an exact two-document patch and location judgment; this authorizes the
documentation adoption below. The source conversation subsequently clarified
that the requester also explicitly directed the next planned work: Stage 6 fresh
paired reconstruction and required final checks. This clarification resolves the
earlier coordinator caution; it authorizes no owner redesign, publication, merge,
Issue closure or project-license choice. Historical passing reports remain unchanged.

| Artifact | Approved existing location | Location judgment |
|---|---|---|
| Upstream function/component and license review | `docs/research/platform-reuse.md` | Extend the existing contributor-facing reuse record; no duplicate research page |
| Diagnostic overlap and acceptance sequence | `docs/delivery-plan.md` | Keep the single roadmap; preserve all M1 criteria and dependency tables |
| Adoption and current implementation state | This plan and the existing integration checkpoint | Internal task record, preserving historical stage reports |

Retain the passing FEX/Wine/DXMT path and original implementation languages.
Before new blocking boundary code, compare FEX/Hangover/Madeira functions and
complete dependency sets, then record adopt/adapt/reject with a concrete reason.
The current owner is reviewable; replacement requires a demonstrated macOS
benefit and its own reviewed scope. Do not revive the historical 256 KiB limit.
Use existing Madeira ASM-to-PE tooling as a #6 review candidate, DXMT `tests/dx11`
for #8, and DepotDownloader/SteamKit2 for acquisition before new equivalents.
GPL/LGPL reuse is a valid reviewed option with component-specific obligations.
Diagnostic game startup and helper architecture inspection do not waive final
CPU/graphics/Steam/game qualification or imply a supported release.

## Read first; retrieve history only when needed

- Root/runtime/FEX/tests AGENTS.md; README and docs/README.md.
- [Architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md),
  [runtime contracts](../../docs/runtime-contracts.md) and [source qualification](../../docs/source-qualification.md).
- This plan and [current memory/dispatch design](../tech/task_m1_5_memory_design.md).
- [Stage 2 report](../working/task_m1_5_stage2.md) and the current checkpoint below.
- [Stage 3 observations](../working/task_m1_5_stage3_layout_observations.json) only for the needed evidence key.
- [Frozen history](../troubleshootings/task_m1_5_stage3_history.md) only for a specific prior decision/failure.

This file owns current execution order and task acceptance. The design owns
current invariants. Dated reports/observations own actual results. Historical
“next”, “unperformed” and approval requests do not override this current plan.
Do not append experiment logs or every build attempt here.

## Issue completion contract

| GitHub criterion | Required evidence | Current status |
|---|---|---|
| Small x64 PE executes through recorded FEX in ARM64 Wine without Rosetta | Real translator entry, deterministic guest result and native process/library identity for the required fixture path | Passed for two deterministic fixtures; complete late-load observation remains outside this evidence |
| Required Darwin services and thread/JIT/exception ownership | Existing service results plus affected real integration/lifecycle tests and explicit ownership documentation | Services and native memory passed in recorded scopes; translated integration open |
| Rebuildable source patch series and contribution policy | Pinned source/tools, attributable patches/notices and one fresh final paired reconstruction | Source85 component build passed; final integrated reconstruction open |

Do not close #5 for module installation, native initialization or passing unit
tests alone. Conversely, do not require Megabonk/Steam, broad CPU conformance or
a general-user app before closing this CPU integration Issue.

## Existing reusable work and dependencies

Inspected on October 7: open #5/#6/#8–#21 Issues, local branches/worktrees and
latest reports. Work stays in codex/task5; its uncommitted source/evidence is
preserved. Do not reset the worktree or modify another task's generated outputs.

| Work | Reuse | Integration dependency |
|---|---|---|
| #4 merged native Wine | 23-patch baseline, signed compatibility route, build/supervisor and native regressions | Role-specific hybrid/guest loading remains to connect |
| #5 Stage 2 | Darwin UnixLib services, pinned FEX C++/assembly, ARM64EC/ARM64 module builds | Full module initialization and translated execution unqualified |
| #5 Source85 | Owner, atomic resume, real finite Context/Core/Thread lifecycle, publication/link/patch/invalidation/growth/retirement controls | Ordinary ARM64 lifecycle scope; real EC entry/API return passed, 62 finite EC retirement/reuse/bitmap checks passed; complete lifecycle scope still open |
| #7 closed, PR #33 | Completed DXMT build and Wine–Metal pairing; 39 native cases | Later coherent patch pairing and #8 translated D3D11; not a CPU smoke-test prerequisite |
| #14 partial delivery, current master a29d600 | CI and verification reuse guidance | No direct CPU implementation; do not import unrelated graphics work for first dispatch |
| #6 and #10 open | Wider CPU qualification and full process/module observation responsibilities | #5 still proves its own finite fixture's actual FEX and ARM64 host path |

Source pins remain FEX `59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa` and Wine
`4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`. Keep upstream languages, policies
and notices. No CPU rewrite, Linux-userspace port, commercial runtime or Rosetta.

## Current evidence checkpoint

Source85's final full build has nine successful commands, 32 artifacts and 642
input snapshots; independent replay passed. Receipt SHA-256:
`9d4e431ee002099fde7c681327747cbfe653b33eae222dc0152e489dd9d1d304`.
Actual finite source case:
`1ea8e36051c5bd7ff870baacc7119e7bc270d03caaf9b2618eb010b198ace979`.
It passed source/process cleanup and current authorization before/after its run.
The affected portable suite passed 469 tests with one APFS skip; the later pair
suite passed 128 with one skip. Historical producer serialization failure and
original failed builds/runs remain recorded, not relabeled as successes.

The [October 7 integration checkpoint](../working/task_m1_5_integration_checkpoint.md)
records role-aware loading, selected-module binding and actual EC callbacks.
Two original x64 PEs returned the expected exit 42 through FEX: integer arithmetic
and an NT API roundtrip that checks exact stack and representative integer/SIMD
state. Entry, checked data-overcommit recovery, nonlocal syscall handoff and
native return use the actual execution owner. Authorization/cleanup passed.

Actual finite EC retirement/reuse and bitmap-sharing checks passed (62 checks).
Metadata observation reports 16 KiB writable bitmap coverage, 108,564 bytes fixed
native owner storage and no extra arena protection leaf at that checkpoint.
Two simultaneous real EC workers passed active/pinned refusal, release, retirement
and stale-entry checks. The reviewed finite bookkeeping profile accounts for
12.5 MiB within 16 MiB, with 3.5 MiB headroom; physical RSS remains unmeasured. A compile-selected finite
probe reuses the existing owner API from the actual initialized translator;
it changes no production admission rule, wire ABI, permission or engine.
The Stage 3 report records its acceptance map and retained Stage 5/6 limits.

## Execution order

### Integrated Stage 3/4 — first real x64 execution

1. Preserve historical records, reduce the active plan, inspect existing work
   and reclaim only confirmed disposable owned build/prefix duplicates.
2. Trace and implement the real role-specific Wine loader and FEX entry path.
   Reuse upstream CHPE/ARM64X/TEB/export mechanisms rather than inventing a loader.
3. Connect actual EC registration/publication/retirement and module identity.
   Retain W^X, current authorization, lifetime synchronization and error checks.
4. Declare the integration resource profile from actual source/metadata costs.
   The historical 256-KiB experiment remains valid only for its old candidate;
   it does not force unrelated upstream allocator rewrites in the new profile.
5. Build the affected components and run one original deterministic x64 PE
   through real FEX; observe expected result/exit and the required native path.
   Reduce the observed first failure and repair its boundary before broadening.
6. Add required API/callback and lifecycle integration checks where changes
   introduce risk. Complete the Stage 3 safety matrix and Stage 4 dispatch result
   on the coherent candidate; no unverified required edge is a passing claim.

### Stage 5 — required translated lifecycle (approved)

Exercise representative translated worker/TLS/native callback, code invalidation,
context/suspend and supported ordinary exception/guard behavior. Preserve guest
state and source ownership; no newly invented fatal native fixture. Explicitly
scope i386/WoW64 based on actual required helpers; an optional unsupported route
is documented, while a required failure blocks completion. #6 owns broader
instruction differential coverage and stress, not fixes for known #5 failures.

Stage 5 implementation starts with actual self-thread cleanup and then source
notifications/context paths. Reuse the original MIT ThreadTerm frontend, GDT,
call-ret stack and CRT ownership. Remove the target from the original thread
registry under its mutex, then close source/owner references outside that mutex.
Never free a currently executing emulator stack. Persistent shared code links
hold Context/buffer references, so thread teardown checks actual per-thread
entry/batch references while Context teardown retains its stronger global check.
Cross-thread termination remains explicitly unsupported until cooperative
context ownership is implemented and tested; do not silently mark it complete.
The final candidate passed five actual x64 cases: worker/TLS/self-thread exit,
two-thread code invalidation with failed-removal preservation, handled guest
exceptions/data guard/nested native call, running-loop suspend/context edits,
and the existing file/time/event/native callback case. The [Stage 5 report](../working/task_m1_5_stage5.md)
and [sanitized observations](../working/task_m1_5_stage5_observations.json) own
exact inputs and scope. The source turn and existing FEX SuspendDoorbell provide
writer progress, including conditional backedges; native security/owner checks
remain unchanged. Forced foreign termination and broader JIT-guard/SMC coverage
remain unqualified. i386 is not required by these x64 fixtures; actual Steam
helper architectures and execution remain later explicit dependencies.

### Stage 6 — reconstruction and handoff

Freshly build the final paired Wine/FEX from recorded source/tools. Run the
required integrated suites and affected native regressions on the final signed
bytes; investigate unexplained differences. Reuse existing builders/readers and
add only missing orchestration. Publish the approved contributor-guide locations
only after actual results; then use final-report/PR procedure under its approval.
Keep #1's historical source decision and #4's baseline evidence unchanged.

## Verification policy

- Before a test, identify the Issue criterion, changed behavior or known bug it checks.
- Reuse evidence only for unchanged recorded inputs and the same claim scope.
- Run targeted portable checks for changed boundaries, then the actual affected
  integration case. Do not repeat all suites for wording or unrelated changes.
- Preserve required authorization, W^X, actual registration, lifetime, cleanup,
  unrelated-process survival and relevant negative controls.
- Keep final fresh reconstruction and same-candidate required checks. Do not
  substitute hundreds of validator tests for a single real x64 execution.
- No broad performance, GPU, Steam or game suite in this CPU smoke-test loop.
- Keep source/build, native, translated, game and distribution outcomes distinct.

## Resource and preservation policy

Heavy builds/runs are serial under the existing native-build lock. Check current
space and bounded growth before starting. Keep current needed outputs, original
input caches and unique failure records. Remove only completed disposable
prefixes or reproducible duplicated payloads after checking no process/reference
needs them; record what remains reproducible. Do not touch other projects.
No upload/push is authorized; sensitive diagnostics remain private.

## Document locations and approval

The requester approved the proposed document separation on October 7. All three
locations below are internal Issue artifacts, not new public product contracts.

| Artifact | Location | Reason |
|---|---|---|
| Current implementation plan | This existing plans/task_m1_5_impl.md | Short authoritative order, approval and completion criteria |
| Current memory/dispatch design | mydocs/tech/task_m1_5_memory_design.md | Required implementation invariants without execution diary |
| Frozen pre-replan record | mydocs/troubleshootings/task_m1_5_stage3_history.md | Preserve failures, decisions and approval provenance outside active context |

Keep stage reports/observations in mydocs/working and final report in mydocs/report.
Existing approved official destinations remain docs/development/fex-host.md and
its index/audit/source-status/Wine-guide cross-references. No second roadmap.

## Reporting

Update this checkpoint only for a meaningful change in outcome or next blocker.
Put experiment detail in private bounded records, with sanitized stage summaries.
Use `Task #5 Stage N: summary` commits when the corresponding stage is complete.
Do not mark a stage complete merely to enable the next experiment.
