# Task #5 Plan — FEX Darwin Services and Wine CPU Integration

GitHub Issue: [#5](https://github.com/postmelee/pear/issues/5)

Milestone: M1 — Megabonk on Apple Silicon without Rosetta

Planning date: October 2, 2026

## Purpose

Run small owned x64 Windows PE programs through an identifiable FEX module in Pear's ARM64 macOS Wine host, with no Rosetta fallback. Port the required Darwin host services and the coordinated Wine/FEX loader, generated-code, thread and context boundaries from source, preserving normal macOS protections and reproducible evidence.

This is the first translated CPU integration component, not general CPU conformance, Steam/Megabonk support or ordinary-user distribution. #6 owns wider CPU/translation qualification; #7 can develop its independent graphics build and typed driver pairing in parallel.

## Background

The [architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md), [runtime contracts](../../docs/runtime-contracts.md), [source qualification](../../docs/source-qualification.md) and [macOS runtime audit](../../docs/research/macos-runtime-audit.md) govern this work. Read root [AGENTS.md](../../AGENTS.md), [runtime](../../runtime/AGENTS.md), [tests](../../tests/AGENTS.md), [host](../../host/AGENTS.md) and [docs](../../docs/AGENTS.md) rules before changes. Follow Hyper-Waterfall v0.3.0 [task](../manual/task_workflow_guide.md), [Git](../manual/git_workflow_guide.md) and [conflict](../manual/agent_code_hyperfall_rule_conflict.md) procedures.

[#4's final report](../report/task_m1_4_report.md), [Stage 6 evidence](../working/task_m1_4_stage6.md) and [Wine host guide](../../docs/development/wine-host.md#integration-handoff) provide a reproducible native ARM64 component and finite Windows API/callback/thread/memory/window observations. That component rejects non-ARM64 executable publication and nonzero CHPE metadata, has a compile-only ARM64EC companion and does not install a working x64 translator. Its eight 64 KiB dynamic slots are a fixture budget, not a FEX JIT service.

Read-only source inspection found that a UnixLib-only Darwin port is insufficient. FEX's Windows executable allocator requests RWX plus ARM64EC code registration, its shared buffers start at 16 MiB and grow to 128 MiB, and active-code backpatching writes published code. Existing comments describe aliases/protection changes as possible workarounds; no implemented macOS alias option was found in the bounded selected-source search. Wine also supplies Linux-only ARM64 register metadata that FEX consumes. These need explicit integrated design and verification.

#1 is closed as an investigation with a blocked aggregate source-readiness decision; #2 retains its finite development-provisioned result. Issue closure does not clear those technical gaps. Preserve their dated records and #4's exact baseline while closing this task's selected inputs and port requirements.

## Scope

### Included

- Revalidate pinned FEX enabled sources/gitlinks, compiler/static-runtime requirements, notices and Windows/Wine module interfaces.
- Port required Windows UnixLib host services and native build rules without bringing the full Linux loader/syscall userspace to macOS.
- Define truthful Darwin CPU-feature reporting, per-thread memory-order policy and optional-service unsupported behavior.
- Integrate FEX-generated code with an explicitly owned Wine executable-memory reservation, bounded capacity/classes, publication, cache maintenance, patching and retirement.
- Support the selected Wine ARM64EC/ARM64X/x64 module roles, metadata, exports, native Unix-library search and actual FEX dispatch, retaining native-only rejection controls.
- Verify small original x64 PE/API fixtures and bounded translated thread/callback/context/invalidation/lifecycle behavior, with actual process/module identity, permission and cleanup evidence.
- Inspect/build the WoW64 route where applicable; provide necessary i386 support or state its unavailable/unsupported scope and downstream helper dependency explicitly.
- Freshly reconstruct the final source-built component and document the #6/#10 handoff.

### Excluded

- A wholesale Linux FEX userspace/rootfs/syscall port, a Rust or Cranelift engine replacement, or a new Windows API implementation.
- Full differential CPU conformance, graphics/DXMT pairing, Steam authentication/helper qualification, game launch, performance/power claims and ordinary-user packaging/recovery.
- Persistent translated-code caches unless added through a reviewed design amendment with invalidation and lifetime tests; keep them explicitly disabled initially.
- New deliberate native fatal-fault fixtures or retry of the previously blocked no-TEB route. Existing approved finite fixture coverage remains separately scoped.
- Bypassing loader/signature/permission/security checks, substituting Rosetta or an opaque commercial runtime, or changing the original source-audit snapshot.
- Proprietary game content, credentials, authenticated prefixes, saves or private signing/raw diagnostics in Git; upstream submission or release clearance.

## Design Direction

### Source and reuse decision

| Input | Initial Immutable Candidate | Role |
|---|---|---|
| FEX | `59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa`, tree `7509ab443d32692ac72ee51c0697ccf86d0a66af` | Windows CPU modules, FEXCore decoder/IR/ARM64 backend and native UnixLib boundary |
| Wine | `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`, tree `10b47b2965a7b3e1e9694ec506a3d13525211892` | Windows API/ARM64EC integration and Darwin host machinery |
| #4 ordered baseline | 23-patch series SHA-256 `39371f21f25cf153437fd523951be9f938cc1161bed5c4ef923583c74c89d086` | Immutable base for separately attributable translator supplements; #4 final materialized patched-source manifest `2c0c861669f9fd8853f8899eaeb08b18207b0cf26b34dae9efe707919e447bc7` |
| Cross compiler | #4 locked LLVM-MinGW 20260908 / LLVM 23.1.1 | Candidate only until FEX C++20, static libraries/imports and actual PE module features are verified |

Retain upstream FEX C++/assembly, Windows context/thread/invalidation machinery and Wine C/platform code. Reuse existing Pear materialization, build, signing, owned-process and evidence owners where appropriate; Python coordination does not replace the runtime. No measured reason justifies a language/backend rewrite.

Stage 1 will close only enabled pinned dependencies, including relevant fmt/range-v3/unordered-dense/rpmalloc/xxHash and bundled terms. Keep Linux tools/thunks/rootfs/graphics inputs excluded only when the selected build proves them unused. Preserve FEX MIT and Wine LGPL notices, and distinguish downstream reuse rights from FEX's prohibition on AI-generated upstream code contributions. No upstream submission is part of this task.

### Required platform contracts

| Boundary | Source Evidence | Required Direction |
|---|---|---|
| Windows/native modules | [Windows CMake](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/Source/Windows/CMakeLists.txt), [UnixLib](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/Source/Windows/UnixLib/FEXUnixLib.cpp) | Separate Windows PE and ARM64 Mach-O builds; required mapping/PID operations must work. Optional Linux advice/naming/stats are explicitly implemented, disabled or unsupported, never silent successes. |
| Native naming/dispatch | [Common UnixLib loader](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/Source/Windows/Common/FEXUnixLib.cpp) | Preserve the eight-function table's order/structure/status semantics. `.so` may correctly name a Mach-O library because selected Wine appends that suffix; validate format/search/export/signature, not suffix assumptions. |
| Thread ordering and features | [TSO policy](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/Source/Windows/Common/TSOHandlerConfig.h), [CPU feature input](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/Source/Windows/Common/CPUFeatures.cpp) | Verify required policy on every relevant thread, rather than infer inheritance/process-wide TSO. Use accurate Darwin capabilities or an explicit conservative supported subset; no fabricated Linux register/registry values. Retain correct software ordering when acceleration is unavailable. |
| Executable allocation | [Allocator hooks](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/FEXCore/include/FEXCore/Utils/AllocatorHooks.h), [shared buffers](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/FEXCore/Source/Interface/Core/SharedCodeBufferManager.cpp) | Design capacity, classes, ARM64EC registration and write/execute ownership for all executable allocators, dispatcher and bitmap/cache paths. Do not remove #4's RWX rejection or enlarge budgets without a reviewed owner/protocol. |
| Publication and patching | [ARM64 JIT](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/FEXCore/Source/Interface/Core/JIT/JIT.cpp) | Reuse temporary emission, relocation and version-held buffers; integrate copy/publication/backpatch/I-cache/retirement synchronization and explicit error paths. A one-time RX flip is insufficient. |
| Hybrid dispatch/context | [ARM64EC module](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/Source/Windows/ARM64EC/Module.cpp), [assembly entry](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/Source/Windows/ARM64EC/Module.S) | Pair exact Wine TEB/CPU-area, exports, calling conventions and hybrid metadata. Observe loaded module bytes and real emulator entry/guest execution; installation or placeholder xtajit64 is insufficient. |

The executable-memory/loader design is a concrete review gate within the detailed plan. Choose a feasible measured publication/backpatch strategy before enabling translated execution; protection transitions or dual aliases are candidates, not already available/authorized designs. If platform/permission/geometry evidence contradicts the approved design, preserve the failure and request a concrete amendment rather than relax security or declare success.

### Execution, evidence and parallel ownership

Use isolated `codex/task5` and `.build/task5/` outputs. Keep original source caches, the detached #4 evidence checkout, failed records and private aliases unchanged. Reused caches are immutable inputs with fresh identity checks; no earlier compiled Wine output silently substitutes for fresh reconstruction.

#5 owns translator-specific Wine loader/memory/x18/context patches and shared CPU builder changes. #7 owns Mac-driver/Metal interface supplements and graphics fixtures. Anchor both independent patch layers to the recorded #4 base; verify ordering/compatibility before combining. Root serializes shared helper/index/board edits, large builds, signing, native execution and storage changes; source review and disjoint fixtures may proceed in parallel. A shared conflict requires review before source changes.

Actual executable authorization is checked before restricted operations; a #2 probe or previous #4 signature cannot authorize a different helper. Keep Hardened Runtime/library validation and normal protections. Missing grants, unsupported APIs, absent host features or unperformed tests stay explicit. Bounded snapshots support the small-fixture claim; #10 owns full process/load timelines. Pear Apple-tooling is not applicable to this host/CPU task; no Metal expert or Apple porting lifecycle is invoked.

## Document Location Judgment

The following official locations are proposed for approval. Task plans/reports remain in `mydocs/`; no product guidance moves into workflow manuals and no second roadmap is created.

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| FEX build/integration guide | Official technical guide | Contributors/integrators | `docs/development/fex-host.md` | `mydocs/manual/` | Public exact source/build/permission reproduction belongs in `docs/` |
| Guide index link | Official index | All readers | `docs/README.md` | README roadmap copy | Existing entrypoint, no duplicated roadmap |
| Dated CPU-port follow-up | Technical research | Contributors | `docs/research/macos-runtime-audit.md` | Replacement historical audit | Preserve original evidence and append scoped verified facts |
| Scoped source-status link | Official technical evidence | Contributors | `docs/source-qualification.md` | Edit #1's original manifest | Record the component result without promoting the blocked aggregate |
| Wine integration cross-reference | Technical guide | Runtime integrators | `docs/development/wine-host.md` | Repeated private ABI contract | Link new verified translator facts while preserving dated native evidence |

## Expected Changed Files

New after approval:

- `runtime/fex/AGENTS.md`, exact input/tool/build records and attributable FEX/supplemental-Wine patch series under `runtime/fex/`.
- Isolated build/service/module/evidence tooling under `tools/fex/`, with original x64/native/WoW64 and lifecycle/rejection fixtures under `tests/fex/`.
- `docs/development/fex-host.md`.

Modified only as needed after reading current contents:

- `tools/wine/` owners when reuse needs explicit component/patch/suite extension; preserve historical schemas/evidence interpretation and old source identities. No unrelated manager/observer contract changes.
- The four existing official locations above; original #4 patch series and #1 manifest remain intact.
- Existing `.build/` exclusion only if proved insufficient; private artifacts remain untracked.

Task artifacts: `mydocs/plans/task_m1_5.md`, later `task_m1_5_impl.md`, `mydocs/working/task_m1_5_stage{N}.md` and sanitized observation sidecars, `mydocs/report/task_m1_5_report.md`, and active-date boards. Create scoped rules together with real implementation, not empty placeholder directories.

## Stage Structure (October 7 execution-order update)

1. **Stage 1 — Source and target-build contract:** enabled pinned sources/terms, compiler/static-runtime capability checks, target/module/table/TEB inventory and isolated materialization. Record missing prerequisites and actual configuration; no translated execution.
2. **Stage 2 — Darwin services and module construction:** native UnixLib/PE module builds, truthful service errors, Darwin CPU feature and per-thread ordering integration, structure/ownership and bounded capability checks under actual permission gates.
3. **Stage 3 — Coordinated executable-memory ownership:** review and prototype reservation/capacity/classes, ARM64EC code registration, publication/backpatch/cache/retirement protocol. Passing finite original code-owner checks and protection/lifecycle controls are required before the translator runs.
4. **Stage 4 — ARM64EC loader and first x64 dispatch:** implement source-matched hybrid/native/guest mapping and emulator selection; execute deterministic original x64 PE/API programs through real FEX, with actual native identities, entry/exit and cleanup evidence. Keep missing/wrong translator and native-only refusals explicit.
5. **Stage 5 — Bounded lifecycle/context and conditional WoW64:** translated thread/TLS/nested callbacks, memory-change/invalidation, suspend/context and allowed exception paths; required i386 route or explicit helper-support gap. Reuse appropriate original finite fixtures; no new native fatal-route test or broad CPU correctness claim.
6. **Stage 6 — Fresh reconstruction and handoff:** rebuild the final selected Wine/FEX configuration, preserve native baseline regressions, independently verify source/build/signature/suite bindings and documented reproduction; hand off to #6/#10 with unsupported and unperformed cases visible.

The requester approved integrated development of the remaining Stage 3 memory/EC work and Stage 4 first-dispatch path on October 7, 2026. Their outcomes remain separate and incomplete until demonstrated. The current implementation plan supersedes the earlier strictly separated execution order.

Every stage is verified, reported and committed before explicit continuation. Stage 3/4 memory/loader coupling can require an amended reviewed design; the detailed plan will define executable artifacts, commands and commit messages after this task plan is approved.

## Verification Plan

### Planning-time Availability

| Item | Observation / Remaining Check |
|---|---|
| Public sources | Exact FEX commit/tree and required Windows/UnixLib/core files inspected read-only; enabled gitlink/hash/dependency closure still requires Stage 1 |
| Native Wine | #4 accepted its specific native build, finite fixtures and same-host reconstruction; ARM64EC companion is compile-only and native loader refuses CHPE/non-ARM64 publication |
| Host/tools | #4 recorded M4 Pro/macOS 26.5.2, Xcode 26.6 (17F113), SDK 26.5; LLVM-MinGW 20260908/LLVM 23.1.1 available as a reused candidate. FEX C++20/static libc++/libc++abi/libunwind/builtins/import linkage not yet checked |
| Build generator | FEX source requires CMake >=3.14 and Python >=3.9; usable locked generator/version not selected during planning. No tool installation/build occurred |
| JIT/CPU capabilities | Source contradictions identified; FEX-compatible allocation/publication, Darwin feature metadata and per-thread ordering inside translated Wine remain unqualified |
| Permission | #4's development grant exists as historical input; actual changed executables and any new helper need fresh grant/signature verification before restricted operation |
| Storage | About 12 GiB free during planning; no FEX/combined-build peak budget established. Measure and admit each build before extraction, preserve evidence, bound jobs and serialize shared heavy work |
| WoW64/reference | No i386 FEX execution, native Windows reference, independent Mac or clean-machine result established by planning |

### Stage Verification

| Stage | Required Method / Result | Retained Evidence |
|---|---|---|
| 1 | Verify source/tool/config bytes and enabled terms; real C++20/cross/static-runtime feature and layout/export checks; reject mismatched/incomplete input | Input/target matrix, commands/hashes, unavailable prerequisites and errors |
| 2 | Native ARM64 service and Windows module compile/link; correct eight-call layout/errors; truthful capabilities and per-thread policy under actual authorization | Native/PE inventories, bounded service/thread results and ownership limits |
| 3 | Original bounded code-owner publication/rewrite/backpatch/invalidation/retirement cases and required protection controls; no unsupported RWX path accepted; no observed lifecycle violation in the declared finite cases | Reviewed memory design, actual grants/source/binary identities and finite observations |
| 4 | Actual selected FEX entry runs small x64 PE/API programs, expected deterministic results, ARM64/nontranslated native identities and owned cleanup; refusal controls still fail explicitly | Paired signed artifact, module/entry and result/exit records |
| 5 | Required finite translated thread/callback/context/cache cases and applicable i386 route or named unsupported scope; no fabricated general exception/unwind coverage | Guest/native state/lifetime records and preserved negative/unperformed cases |
| 6 | Fresh final component build/sign/run and independent replay, affected native baseline regressions, strict explained comparison and terms | Complete provenance, same-artifact results and sanitized handoff |

### Integrated Verification

Map #5's three Issue criteria to actual small-x64 FEX execution, required tested/documented host services and source-derived patch/tool closure respecting upstream policy. Compilation and module presence cannot establish dispatch. Observe actual native processes/libraries and guest module bytes while preserving cleanup/sentinels; retain every required error or unavailable test. The same final signed configuration must pass the declared combined suites.

Run meaningful component/rejection/lifecycle tests and affected Wine regressions when shared owners change. Documentation governance, local links and `git diff --check` must pass; task worktree is clean after commits and before PR preparation. Public exports are allowlisted; build, synthetic, authorized host, translated fixture, game and ordinary-user results remain distinct. No performance claim follows from instrumented correctness checks.

## Risks

- **Memory policy and geometry:** RWX defaults, executable code registration, growth and live backpatching conflict with #4's finite arena. Define and verify the owner/protocol before translation; no permissive shortcut is selected by this plan.
- **Hybrid ABI/metadata:** CHPE/ARM64X, Wine imports, TEB and dispatch state can compile yet fail at entry or callbacks; inspect and exercise the actual paired set with finite source-bound controls.
- **Feature/ordering mismatch:** a Linux registry stub or one-thread TSO success can misconfigure the engine. Convey accurate supported capabilities and verify every relevant thread or retain correct software behavior.
- **Lifecycle/exception scope:** code invalidation, retired versions, suspended translated context and async reads have unqualified edges. Preserve explicit limitations and broader #6 tests rather than promote a smoke pass.
- **Tools/storage/permission:** unknown dependency closure or grant/budget failure blocks the relevant stage; inspect real inputs and preserve prior evidence instead of weakening gates or assuming inherited authority.
- **Contribution/licensing:** FEX forbids AI-generated upstream code submissions independently of downstream MIT reuse; preserve provenance/notices and no upstream acceptance or release clearance claim.

## Approval Request

Approve this scope, reuse/platform direction, executable-memory/loader design gate, official document locations, initial sources and six tentative stages. Authorize detailed implementation-plan preparation; Stage 1 execution requires that concrete plan's explicit approval, and later stages retain their report/continuation checkpoints.

The instruction to proceed in the stated order authorizes #5 planning with #7 parallel preparation. Until this concrete task plan is approved, tracked changes are limited to the plan and daily board; no implementation plan, runtime/source changes or translated execution is performed.

## Approval Record

On October 2, 2026, the requester replied “proceed” to the joint task-plan approval request. This approves the task scope, reuse direction, proposed official document locations and detailed implementation-plan preparation. Stage 1 implementation remains subject to approval of `task_m1_5_impl.md`; later stages retain explicit report/continuation checkpoints. No runtime source changes, component build or native execution are authorized by this planning approval alone.
