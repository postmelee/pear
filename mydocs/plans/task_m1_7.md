# Task #7 Plan — ARM64EC DXMT and Native Metal Build Pairing

GitHub Issue: [#7](https://github.com/postmelee/pear/issues/7)

Milestone: M1 — Megabonk on Apple Silicon without Rosetta

Planning date: October 2, 2026

## Purpose

Produce a source-derived DXMT ARM64EC/ARM64X Windows DLL set with matching ARM64 macOS winemetal and shader-conversion dependencies. Verify the selected Wine driver's actual interface, exports and ownership against the paired bridge. Successful compilation alone will not qualify translated Direct3D, Steam, Megabonk or distribution.

This work may progress alongside #5's FEX/Darwin integration. #5 owns translator-specific Wine loader, executable-memory and ARM64EC changes; #7 owns graphics-specific driver/bridge pairing. Full translated rendering qualification remains #8 after #5/#6.

## Background

The [architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md), [runtime contracts](../../docs/runtime-contracts.md), [source qualification](../../docs/source-qualification.md) and [graphics audit](../../docs/research/graphics-and-game-integration.md) govern this task. Read root [AGENTS.md](../../AGENTS.md), [runtime](../../runtime/AGENTS.md), [tests](../../tests/AGENTS.md), [host](../../host/AGENTS.md) and [docs](../../docs/AGENTS.md) rules before changes. Hyper-Waterfall v0.3.0 [task](../manual/task_workflow_guide.md), [Git](../manual/git_workflow_guide.md) and [conflict](../manual/agent_code_hyperfall_rule_conflict.md) procedures apply.

[#4's completed component](../report/task_m1_4_report.md) and [Stage 6](../working/task_m1_4_stage6.md) qualify finite native Wine fixtures and fresh component reconstruction. Its [typed driver handoff](../../docs/development/wine-host.md#native-driver-interface-handoff-to-7) documents a concrete mismatch: Wine's client view is at offset 16, while pinned DXMT copies a private structure and reads offset 24. The selected table/accessors are absent or unexported, and current null/error/borrowed-lifetime behavior needs explicit pairing. Native Objective-C BOOL spelling is not the demonstrated mismatch.

#1 is closed as an investigation with a blocked aggregate source-readiness decision. #4 did not clear that combined decision. This task will preserve the original manifest and dated evidence, then record its own exact ports and configured dependency/notice closure.

## Scope

### Included

- Revalidate the pinned DXMT, DirectX headers, configured optional sources, native LLVM 15 shader library, cross-toolchain and Wine interface inputs in isolated materialized trees.
- Select actual local build-only tools and SDK/Metal compiler settings; record their origins, architecture and usable feature results before full builds.
- Build native ARM64 LLVM/shader dependencies and the required ARM64EC/ARM64X DXMT PE DLLs plus native winemetal using source-built paired Wine tools/imports/libraries.
- Inventory Mach-O slices, PE/hybrid metadata, imports/exports, builtin/native modes, install/rpath/search layout, source/output hashes and configured source/license obligations.
- Implement an attributable typed Wine/DXMT adapter with explicit version, errors and object lifetime; verify exact exports and native pairing on actual artifacts.
- Reconstruct the final component from empty owned outputs, independently verify evidence and document the #8 integration handoff.

### Excluded

- FEX/x64 dispatch, Wine CPU/CHPE loader changes, translated CPU semantics and general executable-memory policy; #5/#6 own these.
- Full x64 D3D11 validation, Unity scenes, game play, Steam, power comparisons, launcher/profile contracts and release distribution.
- A Rust rewrite, new graphics driver, D3D12, D3DMetal/GPTK runtime substitution, standalone Metal Shader Converter experiments, global plugin installation or OS/security changes.
- Proprietary game assets, authenticated prefixes, account information or raw GPU/private signing diagnostics in Git.
- Changing #1's original snapshot or claiming a complete runtime lock/go decision from a component build; no upstream submission is authorized.

## Design Direction

### Reviewed input and reuse decision

| Input | Initial Immutable Candidate | Role and Evidence |
|---|---|---|
| DXMT | `7c8dee1c2d73415301ceb7d1fa810861cef4cd67` | [CI](https://github.com/3Shain/dxmt/blob/7c8dee1c2d73415301ceb7d1fa810861cef4cd67/.github/workflows/ci.yml), [ARM64EC cross file](https://github.com/3Shain/dxmt/blob/7c8dee1c2d73415301ceb7d1fa810861cef4cd67/build-arm64ec.txt), C++20/Meson source |
| DirectX headers | `9df86f2341616ef1888ae59919feaa6d4fad693d` | Required selected gitlink, revalidated before materialization |
| Native LLVM shader library | `8dfdcc7b7bf66834a761bd8de445840ef68e4d1a` | LLVM 15.0.7; distinct from Apple LLVM and cross LLVM 23.1.1 |
| Optional NVAPI | `d08488fcc82eef313b0464db37d2955709691e94` | Initially disabled with NVNGX and optional Windows airconv; no implicit CI release feature inheritance |
| Wine | `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf` + #4's 23 patches | Source-built Pear interface/tool candidate, not the opaque upstream CI `wine-11.2` archive |
| LLVM-MinGW | 20260908 / LLVM 23.1.1 | Revalidate #4's exact existing locked ARM64EC cross tools; their presence is not pairing qualification |

Retain upstream C/C++/Objective-C, Meson, LLVM and Wine callback scheduling. Use Python for bounded source/build/inspection evidence where existing Pear owners can be reused. A source inspection does not prove a build or runtime result. Changes to these initial source choices require recorded attribution and review; do not substitute floating branches or unrelated latest artifacts.

The inspected DXMT cross file uses `-marm64x`; output classification must include actual ARM64X/CHPE metadata. Native `.so` suffixes can identify Mach-O libraries in this Wine layout. Verify headers and loader contracts instead of renaming files mechanically. Native and companion Wine imports must not be mixed by directory convenience.

### Typed bridge and ownership

Replace or isolate DXMT's copied private Wine window structure with a deliberately typed, versioned opaque boundary or a reviewed source-matched adapter. Preserve Wine's existing main-thread/reentrant scheduling and guest/native transitions. Define supported exports/table versions, output initialization, missing-symbol/null/no-view errors and paired acquire/release. State which view/layer references are borrowed or retained and how resize/detach/destroy invalidate them. Mere symbol export or field renaming is insufficient.

Keep graphics-specific supplemental Wine patches in the #7 component layer, anchored to the immutable #4 series and any explicitly consumed #5 layer. Do not mutate historical #4 patches. Inspect compatibility/order before constructing combined artifacts; any shared implementation conflict requires review before editing.

### Technical guidance and prerequisites

Use [Pear Apple tooling guidance](../../docs/development/apple-tooling.md) only for approved concrete Metal validation or metal-cpp ownership checks. Its Apple source is pinned to `4f42344c90be22112f46becc3fb9687f423f2f88`, plugin reference `1.0.0-beta.1`. Select and read only the relevant expert when the implementation design needs it, reconcile actual SDK/headers, and record the choice. GPU capture/debug/presentation experts are not needed for initial source/build planning; no Apple porting lifecycle or plugin installation is started here.

Before execution, verify actual Metal compiler/library output, host slices and per-executable authorization. Development Wine signing is not ordinary-user distribution permission and does not automatically authorize a new executable. Global Xcode selection, optional toolchain installation, account/license interaction or system changes need their own concrete authorization where not covered by the reviewed stage plan.

### Concurrency and preservation

Use isolated `codex/task7` and `.build/task7/` outputs, with original cached sources and #4 evidence read-only. #5 owns CPU-specific loader/memory/x18 patches and shared CPU builder changes; #7 owns graphics patches, records, tools and bridge fixtures. The root worker serializes shared Wine-tool changes, docs/index and board updates, signing, large builds, native runs and storage maintenance. Source review and separate fixture work may run in parallel; no competing live runs on this Mac.

## Document Location Judgment

Official contributor guidance stays in `docs/`; task history stays in `mydocs/`. These are proposed paths for approval, not documentation edits made during planning.

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| Exact build/pairing guide | Official technical guide | Contributors/integrators | `docs/development/dxmt-build.md` | `mydocs/manual/` | Public source/tool/configuration instructions belong in the official root |
| Guide index link | Official index | All readers | `docs/README.md` | Root roadmap expansion | Existing documentation entrypoint; no duplicate roadmap |
| Dated graphics follow-up | Technical research | Contributors | `docs/research/graphics-and-game-integration.md` | Replacement source audit | Preserve the original observations and append only verified scoped results |
| Driver handoff cross-reference | Technical guide | CPU/graphics integrators | `docs/development/wine-host.md` | Copy of private driver layout in a new guide | Link the verified adapter and retain the original dated mismatch/ownership evidence |

## Expected Changed Files

New after approval:

- `runtime/dxmt/AGENTS.md`, component input/tool/configuration records and attributable DXMT/Wine supplemental patch series under `runtime/dxmt/`.
- Build/materialization/inspection/evidence helpers under `tools/dxmt/` and original bridge/rejection fixtures under `tests/dxmt/`.
- `docs/development/dxmt-build.md`.

Modified only as needed after reading existing contents:

- Approved three existing official locations above; shared Wine helpers only through root-coordinated, reviewed changes that preserve historical record interpretation.
- Existing `.build/` ignore rules only if proved insufficient; no private outputs may enter Git.

Task artifacts: `mydocs/plans/task_m1_7.md`, later `task_m1_7_impl.md`, `mydocs/working/task_m1_7_stage{N}.md` and sanitized observation sidecars, `mydocs/report/task_m1_7_report.md`, and active-date daily boards. No implementation plan or source is written before task-plan approval.

## Tentative Stages

1. **Stage 1 — Input and tool closure:** exact sources/gitlinks/terms, configuration and tool/SDK matrix, isolated materialization and build-only capability checks. No graphics runtime claim.
2. **Stage 2 — Native shader prerequisites:** prepare approved local tools/Metal inputs and build native ARM64 LLVM 15 plus required shader dependencies, retaining actual slices, dependencies, commands and notices.
3. **Stage 3 — ARM64EC/native artifact construction:** clean paired Meson build of required PE DLLs/native winemetal; inspect hybrid metadata, Wine imports/native tool provenance, modes, rpaths and complete output hashes.
4. **Stage 4 — Typed driver pairing:** attributable adapter and source/binary ABI checks; execute approved native/ordinary ARM64 boundary fixtures for actual ownership/error paths. Do not bypass CHPE/refusal guards to execute hybrid modules. If the chosen pairing cannot be proved without unfinished #5, its acceptance remains open.
5. **Stage 5 — Fresh reconstruction and handoff:** another empty-output build of the final required configuration, strict explained comparison and independent evidence review; scoped contributor guide and #8 handoff, no translated rendering qualification.

Each stage is verified, reported and committed before explicit continuation. Detailed implementation artifacts, commands and commit messages are defined only after this task plan is approved.

## Verification Plan

### Planning-time Availability

| Item | Observed or Remaining Check |
|---|---|
| Source cache | Selected DXMT/LLVM/header repositories and exact revisions inspected read-only; fresh derivation/hash/terms verification remains Stage 1 |
| Host baseline | #4 recorded M4 Pro/macOS 26.5.2, Xcode 26.6 (17F113), SDK 26.5; reconcile upstream Xcode 16.1 assumptions rather than inherit CI success |
| Cross tools/Wine inputs | Retained #4 ARM64EC tools, source-built Wine tools/imports/native libraries exist; not reexecuted or paired for #7 during planning |
| CMake/Meson/Ninja | Not found through inspected PATH; actual scoped acquisition/usable versions unresolved, not global absence |
| Metal Toolchain | `metal` resolves, `metallib` lookup failed with exit 72; no compiler/shader/GPU check performed |
| Native LLVM shader library | Required LLVM 15 sources available; usable built library/header set not established |
| Storage | About 12 GiB available during planning; no DXMT/LLVM peak budget established. Measure before each large build, preserve evidence and bound jobs; #4's 26 GiB estimate is not this task's estimate |
| Execution permission | #4's device-bound grant is historical evidence; actual changed executables/signatures/grants must be checked before any restricted #7 fixture |

### Stage Verification

| Stage | Method / Required Result | Evidence |
|---|---|---|
| 1 | Exact source/gitlink/tool bytes and enabled dependency/notice matrix; materialization and compiler/Metal-feature checks with real unavailable/rejection outcomes | Input records, commands, hashes and explicit unresolved prerequisites |
| 2 | Native ARM64 LLVM/airconv and shader prerequisites from recorded sources; correct headers/library majors/dependencies and actual metal/metallib work | Build recipes, slice/symbol/dependency inventory, output identities and notices |
| 3 | Required `d3d11`, `dxgi`, `d3d10core`, matching winemetal and configured dependencies; full PE/Mach-O/mode/import/rpath inspection | Complete built artifact inventory and exact paired Wine roles |
| 4 | Correct ABI/version/signatures and null/error/acquire-release/lifetime behavior against actual paired artifacts; owned fixture cleanup | Source/binary pairing, native boundary observations and finite coverage limits |
| 5 | Independently reproducible final input/output set, strict explained unsigned comparison and notices; no hidden code differences | Fresh build/replay records and sanitized handoff |

### Integrated Verification

Map all three #7 Issue criteria to a clean versioned build, proved Wine-driver/winemetal pairing and explicitly bounded claims. Missing essential Metal/LLVM/Wine interfaces or unverified actual adapter behavior remain failed/unavailable, even if some DLLs compile. Full translated D3D validation remains #8.

Use meaningful component and rejection/lifecycle tests appropriate to changed code; run affected Wine regressions for shared changes. `python3 tools/check_governance.py`, local-document link checks and `git diff --check` must pass. The task worktree is clean after commits and before PR preparation. Public evidence is allowlisted; source/build/host/GPU/game/distribution outcomes stay distinct.

## Risks

- **Private driver ABI:** copied offsets, absent accessors and borrowed object lifetime can cause use-after-release or wrong view pointers; typed pairing and actual finite race/error tests are required.
- **Build role mismatch:** native LLVM 15, cross LLVM 23 and Wine import variants are distinct; exact role/source/binary identities are required.
- **Hybrid execution dependency:** ARM64X compilation does not clear the #4 loader guard; defer translated execution to a proved #5/#6 path.
- **Missing tools/storage:** determine concrete usable inputs and measured budget before installation/build; preserve failed and accepted evidence rather than overwrite/delete it.
- **Terms/contribution policy:** current DXMT is LGPL-2.1-or-later, unlike older MIT releases. Inspect all enabled notices; its policy restricts AI-authored upstream contributions independently of downstream reuse. No upstream submission or release clearance is assumed.

## Approval Request

Approve this scope, typed-pairing direction, document locations, initial input candidates and five tentative stages. Authorize preparation of the detailed implementation plan, with Stage 1 execution subject to that plan's explicit approval. Later stage continuations remain separate checkpoints.

The requester's instruction to proceed in the stated order authorizes starting #5/#7 planning. It is not a substitute for approval of this concrete plan or permission to implement/render/play/distribute. Until approval, changes are limited to this task plan and the daily board.
