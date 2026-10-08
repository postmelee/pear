# Task #40 Plan — Megabonk GameAssembly Image Loading

GitHub Issue: [#40](https://github.com/postmelee/pear/issues/40)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Work branch: `codex/task40`
Planning date: October 9, 2026 (Asia/Seoul)
Status: task plan, scope and document locations approved on October 9, 2026 by
the requester's explicit continuation; detailed implementation plan awaits approval.

## Purpose

Remove the attributable Wine image-loading limitation that prevents the owner's
unchanged Windows `GameAssembly.dll` from loading and initializing. Success means
observed initialization and a named subsequent Unity/game stage, with valid memory
ownership, executable publication and current development authorization. A larger
size constant or a successful mapping return alone is not completion.

## Background

Requirements come from the [README](../../README.md), [official index](../../docs/README.md),
[architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md),
[runtime contracts](../../docs/runtime-contracts.md) and
[source qualification](../../docs/source-qualification.md). Apply root/runtime,
affected FEX/host/tests/docs rules and the task/Git/document workflows. Task-start
and repository todo apply to this planning checkpoint.

- [PR #41](https://github.com/postmelee/pear/pull/41) merged #8 as
  `29f04a3daa028cb8e52e06af9ee74d15c7cbe11e`. #8 is CLOSED. Its reviewed head
  `165014469c199735e47fcc0443c4b262f192628f` passed eight CI jobs; integration
  replay and 36 focused local tests passed. Review identified no blocker within
  the recorded finite scope; it was not independent maintainer approval.
- The [#8 final report](../report/task_m1_8_report.md) and
  [Stage 4 report](../working/task_m1_8_stage4.md) preserve the originating game
  failure. Candidate receipt SHA-256:
  `f90b2a601f556595a07b38bfa695def75b7f1def9bb1018e7dacb73bf7444f5f`.
- Unity memory initialization appeared; GameAssembly mapping returned
  `0xc00000bb`, then the bounded startup timed out. Its `SizeOfImage` is
  57,647,104 bytes; the observed loader maximum is 38,993,920 bytes.
  Static source inspection confirms a size rejection in `pear_pe_plan_read`,
  but the first executed refusal branch remains unproven.
- Planning inspected the original PE publication parser, per-image staging/page
  allocations, relocation maximum, arena slots and reservation, plus the #8
  admission/diagnostic adapters. Later supplements must be inspected in the
  materialized final source before editing. Raising the ceiling can also affect
  relocation and memory costs; neither a one-line fix nor a redesign is selected.
- #9 is merged but its native supervisor still admits fixtures only. #10 is OPEN
  on a separate worktree at `a16d49b`; its approved plans exist and no completed
  stage report was found during planning. Do not edit that worktree or introduce
  competing observer/product contracts. #11/#12 own official Steam and gameplay.
- Retained #1/#3/#5/#6/#7/#8 worktrees hold dependency inputs/evidence. #8 remains
  detached at its reviewed head; its obsolete task/publication branches were
  removed. Main master is updated; existing untracked research is preserved.
  #40 uses a separate attached worktree and fresh ignored outputs.

## Scope

### Included

- Bind the original failure, exact game snapshot and final source/runtime inputs;
  trace the first relevant image-admission refusal and any additional constraints.
- Review size arithmetic, alignment, aggregate arena capacity, metadata, staging,
  relocations, executable publication, unload/reuse and failure rollback.
- Implement the necessary correction in the existing Wine/Pear integration;
  include a reviewed larger-image budget if the traced failure requires it.
- Use a redistributable size/layout fixture and meaningful rejection/lifecycle
  checks, then execute the actual unchanged owned DLL through the normal loader.
- Rebuild affected components, perform required changed-candidate CPU/ordering
  regression and targeted graphics revalidation, and identify the next blocker.

### Excluded

- Steam authentication/Steamworks qualification (#11), 20-minute gameplay,
  input/audio/save/relaunch qualification (#12), complete observation (#10),
  ordinary-user packaging, performance claims or a replacement translation engine.
- Proprietary binary changes, authentication stubs, weaker macOS protections,
  new signing privileges, or treating downstream unknowns as passes.
- Reopening completed #4/#8 scope, or automatically absorbing every later failure.

## Design Direction

| Existing implementation | Reuse decision | Qualification still needed |
|---|---|---|
| Pinned Wine C loader and Pear PE arena from #4 with #5/#8 supplements | Retain upstream language, parser/relocation semantics and current ownership/publication model; inspect final composed source | First actual refusal, required layout and bounded aggregate/temporary memory cost |
| #8 ARM64 Wine/FEX/DXMT candidate | Use exact retained source/build records and unchanged components as inputs; preserve originals | Changed payload identity, current authorization and affected runtime behavior |
| Existing Wine build/signing/APISession and #8 game diagnostic | Adapt only required input/output admission to #40; reuse process ownership, timeout, sentinel and cleanup | New candidate and exact unchanged DLL initialization evidence |
| #6 CPU corpus and finite ordering; #8 graphics readers | Reuse fixtures, Windows references and result readers | Full declared affected CPU/ordering qualification after core loader/memory changes; relevant graphics checks on changed candidate |

Retain Wine C and FEX C++/assembly and their existing source pins, notices and
license boundaries. Review the pinned upstream loader/relocation functions and
applicable contribution policies in Stage 1 before adding subsystem code; do not
submit generated work to upstream projects whose policy excludes it. Rust is not
required. A new allocator, ABI or owner model requires a concrete design review;
prefer extending the existing bounded model when sufficient.

Metal tooling is not selected for PE-admission work. Apply the pinned Pear Apple
skill only if implementation changes an actual Metal/presentation boundary.

## Document Location Judgment

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| Loader budget, reconstruction and measured limits | Official contributor guidance | Runtime integrators | Existing `docs/development/wine-host.md` | A new guide in `mydocs/manual/` | Extend the existing component guide; workflow manuals are not product guidance |
| CPU impact, only if required | Official contributor guidance | CPU integrators | Existing `docs/development/fex-host.md` | Duplicate new CPU guide | Update affected instructions only; preserve historical evidence |
| Plans, stage evidence and final report | Work artifacts | Reviewers and maintainers | Existing `mydocs/plans/`, `mydocs/working/`, `mydocs/report/` | `docs/` | Keep issue-specific decisions separate from official requirements |

No architecture, roadmap, manager/profile contract or new official documentation
root is proposed. Read each existing guide fully before any approved edit.

## Expected Changed Files

New, with exact names finalized by the approved implementation plan:

- `runtime/wine/patches/`: ordered #40 image-admission supplement and provenance.
- `tools/wine/`: narrow #40 construction/admission/diagnostic adapters where existing
  interfaces cannot safely accept the new candidate.
- `tests/wine/`: redistributable large-image fixture and required refusal checks.

Modified only where the correction requires it:

- Relevant Wine builder/evidence admission and memory-budget accounting.
- Existing Wine/FEX developer guides at the approved locations above.
- FEX implementation only if the measured loader fix crosses that boundary;
  no speculative CPU-engine change is planned.

Task artifacts: `mydocs/orders/20261009.md`, this plan,
`mydocs/plans/task_m1_40_impl.md`,
`mydocs/working/task_m1_40_stage{N}.md`,
`mydocs/report/task_m1_40_report.md`; raw private outputs under `.build/task40/`.

## Tentative Stages

1. **Attribute the refusal and select the memory budget.** Re-admit retained inputs,
   inspect the actual composed loader and upstream code, use targeted diagnostics
   to identify the first executed refusal, and calculate required image/arena/
   metadata/relocation costs. Produce a concrete correction and fixture design.
2. **Implement and verify the loader correction.** Add the ordered source change,
   construct only affected components and validate the redistributable positive,
   boundary, malformed-layout/relocation and unload/reuse cases relevant to it.
3. **Verify actual game initialization and affected regressions.** Run the original
   owned game on the corrected candidate, prove DLL initialization and subsequent
   progress, and complete mandatory CPU/ordering plus impacted graphics checks.
   A mere mapped module or generic Unity startup message does not pass this gate.
4. **Finalize reconstruction guidance and handoff.** Replay valid final evidence,
   publish allowlisted outcomes, document limits and the next #11/#12 blocker,
   complete the report and prepare the PR. No repeated native matrix without
   invalidated evidence or an unresolved finding.

## Verification Plan

### Stage Verification

- Stage 1: exact source/tool/game/runtime hashes and first-refusal attribution;
  arithmetic and allocation accounting with actual PE sections and relocations.
  Preserve original private logs; diagnostics remain separately identified.
- Stage 2: required-size success; appropriate immediately-outside-budget rejection,
  malformed/overflowing section or relocation refusal, failure rollback and
  unload/reuse. Select existing fixtures first and add only missing behavior.
- Stage 3: evidence for actual DLL initialization and a named later stage;
  full declared CPU corpus and finite ordering for the core-loader/memory change.
  Rerun graphics behavior invalidated by changed native image/publication paths;
  retain source-only claims for unchanged shader construction. No inherited
  execution pass solely because an unchanged DLL was copied into a new runtime.
- Stage 4: independent readers recompute final results from matching inputs,
  documentation governance and `git diff --check`. Do not rerun already valid
  native tests for documentation-only edits.

Existing producers/checkers: `tools/wine/build.py`, `tools/wine/api_runner.py`,
`tools/fex/memory_wine_runtime.py`, `tools/fex/integration_run.py`,
`tools/dxmt/translated_game_diagnostic.py`, `tools/dxmt/translated_check.py`,
`tools/cpu/compare.py` and `tools/cpu/ordering.py`. Preserve wrong-input, missing
scope, stale receipt and cleanup-failure rejection. Source, patches, toolchain,
configuration, signing, payload or relevant reader changes invalidate affected
claims; old receipts remain historical rather than being overwritten.

Known prior environment: M4 Pro, ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113).
Current execution authorization has not been rechecked during planning. Verify
actual host/tools and each restricted executable before running. Owned snapshot:
App 3405340, depot 3405342, manifest 446680890915713051; it is not assumed current.

### Integrated Verification

- First refusal attributed; the reviewed correction satisfies the exact required
  image layout and explicit memory budget without weakening bounds or ownership.
- The unchanged owned DLL initializes and reaches a named subsequent phase.
- Required changed-candidate regressions, before/after authorization, original-file
  integrity, owned cleanup and unrelated-sentinel survival all pass.
- Preserve original failures and exact private inputs; commit only reviewed
  allowlisted derivatives. Later blockers name their phase and owning Issue.
- All stages have source-bound reports; clean tracked worktree and whitespace
  checks before PR publication. M1/Steam/gameplay remain separately unqualified.

## Risks

- **Multiple refusals:** size incompatibility may not be the first or only failure;
  trace the real path and never infer initialization from mapping alone.
- **Memory growth:** per-image limits affect staging, metadata, aggregate arena and
  relocation cost; measure and bound them together, including failure cleanup.
- **Storage:** approximately 14 GiB free during planning. Use retained inputs and
  serial affected-component builds. Set an evidence-based build-space estimate
  before construction; preserve original failures and remove only owned redundant
  scratch after verification. Do not modify other projects or live #10 outputs.
- **Dependency identity:** #8 adapters contain deliberately exact receipt/path
  bindings. Introduce attributable #40 inputs without weakening those validators
  or editing retained #8 evidence/producers to manufacture a matching receipt.
- **Authorization and downstream gates:** unavailable permissions block execution;
  success here does not qualify Steam, complete Rosetta independence or gameplay.

## Approval Request

Approve the loader-admission scope, four-stage direction, necessary regression
policy and document locations. Then write the detailed implementation plan before
source changes. This checkpoint creates no native candidate and claims no new
runtime execution result.
