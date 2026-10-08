# Task #5 Stage 3 Historical Implementation Record

Frozen October 7, 2026. This is historical evidence, not the current plan.
Current authority: [implementation plan](../plans/task_m1_5_impl.md).
The original implementation-plan SHA-256 before extraction was `69b7042bed95f5e44ac659fed5b0a90b96210535a179dcbaeae847361a788778`.
The source body is preserved below except for its task-plan relative link.
Amendment D was proposed but never separately approved or implemented; the
October 7 integrated execution plan supersedes that isolated-fixture proposal.
Dated failures and incomplete observations must not be read as current state.

---

# Task #5 Implementation Plan — FEX Darwin Services and Wine CPU Integration

Task plan: [`task_m1_5.md`](../plans/task_m1_5.md)
GitHub Issue: [#5](https://github.com/postmelee/pear/issues/5)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

Prepared October 2, 2026. The requester approved the task plan and its document locations. The requester approved this implementation plan and Stage 1 execution on October 2, 2026. Stages 1 and 2 are implemented; their actual results are in the corresponding stage reports. The requester explicitly approved the concrete Stage 3 design and its implementation/prototype on October 3, 2026. Source integration and actual verification remain in progress. Later implementation and expected outcomes remain planned work.

## Applicable Context and Reuse

Follow the approved task plan, [architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md), [runtime contracts](../../docs/runtime-contracts.md), [source qualification](../../docs/source-qualification.md), [macOS runtime audit](../../docs/research/macos-runtime-audit.md), applicable root/runtime/host/tests/docs rules and Hyper-Waterfall v0.3.0 task/Git procedures. #4's [final report](../report/task_m1_4_report.md) and [Wine integration handoff](../../docs/development/wine-host.md#integration-handoff) are the dated native baseline. #1's original aggregate `blocked`/`source_ready: false` decision remains unchanged; closing this selected component does not establish a complete runtime lock or product eligibility.

Retain FEX C++/assembly decoder, IR, ARM64 backend, Windows thread/context/cache machinery and Wine C/platform implementation. Reuse bounded Pear source, artifact, signing and owned-process readers where their actual contracts fit; Python orchestrates builds/evidence and is not the translator. Rust/Cranelift replacement and a wholesale Linux userspace/rootfs port are excluded. Respect FEX MIT and Wine LGPL terms and configured dependency notices; FEX's AI-authored upstream contribution prohibition is separate from downstream reuse rights. No upstream submission is authorized.

| Candidate | Exact Initial Identity | Scope |
|---|---|---|
| FEX | Commit `59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa`, tree `7509ab443d32692ac72ee51c0697ccf86d0a66af` | Windows modules, enabled FEXCore/native UnixLib sources and pinned configured dependencies |
| Wine | Commit `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`, tree `10b47b2965a7b3e1e9694ec506a3d13525211892` | Source base, not a prequalified hybrid runtime |
| #4 baseline layer | 23-patch series SHA-256 `39371f21f25cf153437fd523951be9f938cc1161bed5c4ef923583c74c89d086`; final materialized patched-source manifest `2c0c861669f9fd8853f8899eaeb08b18207b0cf26b34dae9efe707919e447bc7` | Immutable baseline; #5 supplements have their own ordered identity |
| Cross compiler | #4 locked LLVM-MinGW 20260908 / LLVM 23.1.1 | Candidate until actual C++20/static runtime/target-link capabilities pass |
| Native compiler/SDK | #4 observed Xcode 26.6 (17F113), SDK 26.5, macOS 26.5.2 (25F84), M4 Pro | Recheck actual host/tools/settings; historical observation is not present authorization |

Existing `tools/wine/prepare.py` top-level validation is Wine-only and its output paths, along with `toolchain.task_path`, are task4-specific. Its tree reader refuses Git mode 160000, which FEX uses. Do not point those CLIs at FEX, masquerade it as Wine or monkey-patch their globals. Reuse audited low-level bounded algorithms through explicit FEX component adapters, with a selected gitlink mount closure and task5 output owner. Existing PE predicates likewise cannot be applied unchanged: COFF ARM64EC `0xa641`, a PE outer machine and semantic ARM64X/CHPE properties are distinct. Preserve actual bytes and unsupported results; do not rewrite headers to make a validator pass. Shared helper changes require root coordination and affected historical regressions.

Pear Apple-tooling and its Metal experts are not applicable to this CPU/host task. No Apple porting lifecycle, GPU capture, graphics qualification or plugin installation is introduced.

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Source and target-build contract | Selected input/tool/configuration records, isolated sources and compiler/interface capability fixtures | Exact enabled source/terms closure, real C++20/static-link target checks and source-derived module/UnixLib/TEB inventory; no FEX build or dispatch |
| 2 | Darwin services and module construction | Native UnixLib and Windows FEX modules with truthful Darwin service/feature policy | Actual native/PE build identities, eight-call ABI/error behavior, CPU capability and per-thread policy checks |
| 3 | Coordinated executable-memory ownership | Reviewed Wine/FEX JIT allocation/publication/patch/retirement protocol | Actual finite code-owner/protection/lifecycle fixtures; no translated execution before this gate passes |
| 4 | Hybrid loader and first x64 dispatch | Source-matched Wine loader/ARM64EC integration and small original x64 fixtures | Actual identifiable FEX entry, deterministic guest results and required native identities/cleanup; refusal controls retained |
| 5 | Bounded translated lifecycle and conditional WoW64 | Thread/context/callback/invalidation fixtures and applicable i386 route | Finite translated state/lifetime behavior, explicit exception/helper limitations and actual permission controls |
| 6 | Fresh reconstruction and handoff | Final paired Wine/FEX rebuild, independently verified evidence and contributor guide | Same final signed candidate passes declared suites, affected native regressions and strict explained reconstruction comparison |

Each stage has a report/verification/commit and requires explicit continuation before the next. The original stage split did not select Stage 3's concrete capacities, registration, publication/backpatch and retirement strategy. The source-bound proposal below awaits requester approval before any owner prototype or integration, even when the broad scope is unchanged. No successful inventory or compiler fixture promotes runtime eligibility.

## Document Location Check

| File | Planned Location in Task Plan | Stage Artifact Path | Match | Notes |
|---|---|---|---|---|
| FEX contributor/integration guide | `docs/development/fex-host.md` | Same, Stage 6 | OK | Exact source/build/permission and finite execution reproduction |
| Guide index | `docs/README.md` | Same, Stage 6 | OK | Narrow link only |
| Dated CPU-port follow-up | `docs/research/macos-runtime-audit.md` | Same, Stage 6 | OK | Append verified scoped facts; retain historical audit |
| Component source-status link | `docs/source-qualification.md` | Same, Stage 6 | OK | Preserve #1 aggregate and distinguish component closure |
| Wine integration cross-reference | `docs/development/wine-host.md` | Same, Stage 6 | OK | Link source-matched translator facts without replacing dated baseline |
| Plans/reports/boards | Approved `mydocs/` paths | `mydocs/plans/task_m1_5_impl.md`, `mydocs/working/task_m1_5_stage{N}.md`, sanitized sidecars and active-date board | OK | Task history remains outside official product guidance |

No official document is edited in Stage 1. Component records and scoped implementation rules are in the task plan's approved `runtime/fex/`, `tools/fex/` and `tests/fex/` areas. Different product/API locations or scope/owner conflicts require a concrete amendment before changes.

## Shared Input, Evidence and Execution Contract

Component-local records use integer schema versions and `scope: fex_component`; do not add a product record kind to `runtime/contracts/`. Record stored-byte hashes separately for source Git trees/listings/archives, materialized source manifests, ordered patch layers, tools, build configuration, unsigned output, signed output and observations. A valid record is not runtime eligibility. Bind receipts to the exact producer revision and actual command arguments, selected environment keys, timing, statuses, bounded logs and output inventory. Independent readers rederive identities and required results; a producer success boolean/exit zero is insufficient.

Use `.build/task5/` with owned, empty operation outputs, finite time/output/disk/expansion limits and explicit read-only input handles. Reject traversal, symlink escapes, duplicate JSON/archive paths, unsupported entries, incomplete/mismatched mount closure, altered source and existing output destinations. Preserve failed evidence; retry into new owned outputs. No automatic deletion of prior sources/builds/failures or global tool installation. Public sidecars are reviewed allowlisted derivatives; never copy full environments, private absolute paths, profiles/certificate identity, authenticated prefixes, Steam/game payloads or raw private diagnostics.

Planned CLI exits: 0 is the requested gate passing; 1 is an operational/input failure; 2 is usage error; 3 is valid evidence that cannot meet a requested capability/readiness gate. Record operation outcome and negative-control assessment separately. `unavailable`, `unsupported`, `failed`, `unknown` and `unperformed` remain explicit; no default false for a denied query.

Root owns serialization of shared Wine helpers, boards/index changes, heavy builds, signing, native execution and storage maintenance. #5 owns CPU/CHPE/loader/JIT/x18/context supplements; #7 owns graphics/Mac-driver supplements. Anchor independent layers to #4's unchanged series and explicitly record any combined ordering. Disjoint source review and portable fixtures may run in parallel, but source conflicts and CPU/graphics layer compatibility are reviewed before combining. Development authorization is verified for each actual executable before restricted operations; do not infer it from #2/#4 or a parent signature. Preserve Hardened Runtime, library validation and ordinary macOS protections.

## Stage 1 - Source and Target-Build Contract

### Artifacts

New:

- `runtime/fex/AGENTS.md`, component rules with real records/tool implementation, not an empty placeholder directory.
- `runtime/fex/inputs.json`, `toolchain.json`, `build-config.json`: versioned selected-source/gitlink/terms, build-only tool roles, disabled features, target/static-runtime and Wine layer records.
- `tools/fex/{common,prepare,check,verify,tools,byte_readers}.py`: bounded FEX-specific input/materialization, local build-tool setup, capability/interface inventory and independently checked receipts. No full FEX build/native UnixLib port/translator entrypoint in this stage.
- `tests/fex/test_stage1_inputs.py`, `test_stage1_capabilities.py`, `test_stage1_capability_replay.py`, `test_stage1_ec_archive.py`, `test_stage1_tools.py` and original compile/link-only fixtures under `tests/fex/capabilities/`.
- `mydocs/working/task_m1_5_stage1.md` and `task_m1_5_stage1_observations.json`.

Modified: the active-date board through root and this plan only for implemented command/pin clarifications within the approved scope. No historical #1/#4 record, existing patch series or official documentation changes.

### Changes

1. Revalidate FEX's exact root tree and explicitly selected gitlinks, source paths and configured dependency licenses. Root inspection identified regular blobs plus gitlinks; materialization must mount each enabled pin at its declared path and reject incomplete/wrong mounts. Close enabled fmt/range-v3/unordered-dense/rpmalloc/xxHash and bundled SoftFloat/Cephes/tinyjson terms as actually selected. Exclusions of Linux tools/thunks/rootfs/graphics must derive from recorded build options/source graph, not an assumed universal dependency list.
2. Revalidate #4's source/ordered layer and retained native/companion/tool receipts read-only. Build a fresh scoped source materialization; retained binaries may supply explicitly identified compiler/tool/import candidates, not replace later final Wine/FEX construction. Record separate native UnixLib, ARM64EC module and conditional WoW64 target roles.
3. Lock and prepare only required task-local build tools, with authoritative origin, actual payload verification, safe extraction, notices and actual native ARM64 execution. Proposed metadata candidates are CMake 3.31.8 and Ninja 1.13.1 below. Use existing verified tools if their exact identity/capability meets the configured recipe; no global PATH, Homebrew/pip or Xcode/security change. Python >=3.9, CMake >=3.14 and native Apple compiler identities are observed explicitly.
4. Compile/link original minimal C++20 fixtures for required configured PE target roles (ARM64EC and ARM64 WoW64 module ABI; this is not i386 guest execution) using the actual candidate Clang/MinGW toolchain. Check FEX-style no-exceptions/no-strict-aliasing choices, target-specific static libc++/libc++abi/libunwind/builtins and selected CRT/Wine imports through real minimal objects/archive members and link use. No empty fake archive or ignored unresolved-symbol flag can satisfy a capability. Full FEX custom CRT/module construction remains Stage 2; if a required minimal capability cannot link without it, preserve the dependency and review a narrowly justified probe/design amendment rather than silently moving the full module build into Stage 1. Inspect COFF/PE target bytes, imports/exports and unexpected dynamic C++ dependencies. Test the relevant ARM64EC `VirtualAlloc2`/EC-code parameter declarations and module/callback calling convention. No fixture executes a Windows PE or includes a decoder/runtime claim. Missing required static/runtime/import support prevents the positive build-capability gate.
5. Derive a source-bound inventory of native UnixLib's eight ordered calls, argument sizes/alignment/return and ownership semantics, module exports/native search suffix, TEB/CPU-area/x18 entry contracts and feature/policy source paths. Original native/PE compile-only layout probes and small source readers verify actual selected headers. Do not fabricate a functioning Darwin service, Windows engine or cross-platform C++ ABI from matching sizes alone.
6. Record current storage/memory and actual archive/source/tool expansion before each scoped acquisition/extraction. Bound jobs and output; source extraction preserves validated Git modes and archive mtimes with a scoped source-child policy, without changing global umask or private-record permissions. Stage 1 has no full FEX/LLVM/Wine rebuild; later build peaks remain unknown until measured. Preserve actual tool/source failures rather than overwriting them.

### Component and Source Contract Records

`inputs.json` records exact source/tree/listing, enabled mount conditions and notices; `toolchain.json` records source/artifact/current bytes, native slices/dependency closure and required target features; `build-config.json` records target/options, Wine layer identity and unsupported inherited configuration overrides. Private preparation/capability records bind those stored bytes, producer and fixture identities, actual command arrays, object/link/import observations and per-check `required`, `status` and `reason`. Unknown digests cannot be placeholder zero hashes. Public exports retain required failed/unavailable checks.

Module rows distinguish `libarm64ecfex.dll` (x64 guest, ARM64EC PE ABI), `libwow64fex.dll` (i386 guest, native ARM64 PE ABI) and prospective native ARM64 `libarm64ecfex.so`/`libwow64fex.so`. Source requirements, builds, live execution and optional helper scope have separate statuses. Record function versus data exports, caller/return convention and native-library lookup. The eight-call source contract below is inspected 64-bit layout, not a performed Darwin service result; independently derive it from pinned headers and compiled original layout assertions.

| Ordinal | Source Service | Argument Facts / Required Decision |
|---|---|---|
| 0 | `SetHardwareTSOControl` | One-byte boolean; per-thread documented policy with correct software ordering when unavailable |
| 1 | `SetKernelUnalignedAtomicControl` | Eight-byte flags; Linux kernel bits require an explicit Darwin supported/unsupported/software decision |
| 2 | `Madvise` | Address/size/advice at 0/8/16, total 24 bytes; translate semantics, not Linux numeric constants |
| 3 | `SetVMAName` | Address/size/name at 0/8/16, total 24 bytes; optional naming may truthfully remain unsupported |
| 4 | `GetSHMStatsVMA` | Base/size/max-size at 0/8/12, total 16 bytes; profiling initially disabled |
| 5 | `DeleteSHMStatsFile` | Null argument; paired cleanup status distinct from performed deletion |
| 6 | `MapFile` | FD/size/result at 0/8/16, total 24 bytes; duplicated descriptor/mapping ownership on success and failure |
| 7 | `GetPID` | Four-byte result; actual host PID and guest fallback are distinct |

Preserve signed 32-bit NTSTATUS and exact source enum/table order. Record source/blob/byte-hash/line references, native/PE size/alignment/offset checks, configured necessity and `source_inspected` versus unperformed live service statuses. Host-feature rows record actual provider, unavailable registers, effective supported subset, SVE/ordering decisions and thread initialization owner; Stage 1 does not invent an effective CPU model.

Initial effective FEX configuration keeps `DiskCache=false`, `ProfileStats=false` and correctness-preserving `TSOEnabled=true`. Unavailable hardware TSO must **not** become `TSOEnabled=false`; the pinned configuration warns that disabling software TSO can break multithreaded programs. Other half-barrier/split-lock/unaligned options require explicit source/design decisions, not inherited unqualified defaults. Reject unsupported environment/application overrides.

### Build-only Tool Candidates

The table preserves the October 2 planning-time proposals. Their actual checksum/source/native qualification is now recorded in the [Stage 1 report](../working/task_m1_5_stage1.md). CMake's prebuilt universal developer tool remains distinct from a source-built runtime dependency or permission claim; its ARM64 slice was selected and verified.

| Tool | Official Origin / Pin | Proposed Identity and Admission |
|---|---|---|
| CMake 3.31.8 | [Kitware release](https://github.com/Kitware/CMake/releases/tag/v3.31.8), `cmake-3.31.8-macos-universal.tar.gz` | Release API-reported SHA-256 `d1449f969c54d5c00886d5b643340d493dfb3c81cb39ee29b35453395c11ebf7`; official `cmake-3.31.8-SHA-256.txt` metadata SHA-256 `8d08ce0586bf40ff6b80e46fffe2db8855bab5b030db8b3782f11f68b6274ad8`. Actual checksum text/payload/native closure verification remains required. |
| Ninja 1.13.1 | [Official release](https://github.com/ninja-build/ninja/releases/tag/v1.13.1), commit `79feac0f3e3bc9da9effc586cd5fea41e7550051` | Derive source tree/listing/archive identity, inspect bounded bootstrap/build inputs, build native ARM64 into task-owned tool root; no floating tag alone or opaque substituted executable. |

### Verification

Inputs: approved initial records, exact selected read-only caches/#4 receipts and original capability fixtures. Tools: actual installed Python/Git/Xcode utilities, verified native task-local CMake/Ninja as needed, retained LLVM-MinGW 20260908 candidate. Planning found CMake/Ninja absent from inspected PATH. Stage 1 now verifies task-local tools and original static-runtime prerequisite fixtures; the full FEX custom-CRT/module link remains unperformed. SDK/host/grants and tool slices are rechecked; Stage 1 does not require restricted permission or a graphical/Steam session.

Implemented Stage 1 CLI (private placeholders are validated local handles; exact actual arguments are retained privately). The final accepted outputs below follow preserved earlier attempts:

```sh
python3 tools/fex/tools.py prepare --toolchain runtime/fex/toolchain.json --output .build/task5/stage1-tools5 --artifact-cache .build/task5/stage1-tools/downloads --source-cache .build/task5/stage1-tools2/ninja.git --require-empty
python3 tools/fex/prepare.py --inputs runtime/fex/inputs.json --source-cache <read-only-selected-cache> --output .build/task5/stage1-inputs3 --require-empty
python3 tools/fex/check.py capabilities --inputs runtime/fex/inputs.json --config runtime/fex/build-config.json --prepared .build/task5/stage1-inputs3 --tools .build/task5/stage1-tools5 --cross-tools <verified-locked-tools> --wine-roles <verified-local-Wine-role-record> --output .build/task5/stage1-capabilities6 --require-empty
python3 tools/fex/verify.py stage1 --root .build/task5/stage1-capabilities6 --require-complete
python3 -B -m unittest discover -s tests/fex -p 'test_stage1_*.py'
python3 tools/check_governance.py
git diff --check
```

Expected: complete selected identity/dependency/notice/mount closure, actual required compile/link capabilities and source-derived table/target/layout inventory pass independent replay. Tests reject changed Git/payload/tool/receipt bytes, unsafe archive/mount/JSON/path, missing imports/static libraries, wrong target classification, unsupported configuration and incomplete evidence. Capability fixture output is build-only; FEX module construction, Darwin services, JIT, hybrid dispatch and WoW64 execution remain unperformed.

Retain bounded raw compiler/tool operations, rejected-control errors, exact fixtures/output headers/hashes, target matrix and source-derived contract. Export only sanitized role/digest/version/settings/outcome fields. A source inventory can be valid with named missing tools, but Stage 1's required compiler/static-link capability gate must pass before it completes; absence must not become a passing fixture or later build authorization.


Implemented probe clarification: the original DLL fixture uses the complete default MinGW DLL CRT plus static libc++/libc++abi/libunwind/builtins. The full FEX `-nostdlib -nostartfiles -nodefaultlibs`/custom-CRT link in `build-config.json` is source-inspected and remains unperformed until Stage 2. Link libc++abi before libc++ so the latter's bundled ABI copy cannot conceal separate archive contribution. COFF `/map` (forwarded through MinGW `-Xlink`) binds actual selected library members to forced live symbols; ordinary `-Map` lacks that provenance. The default MinGW `chpe.S` emits Version 1, while the earlier #4 executable fixture uses another link form. The component reader checks this actual DLL form, including bounded executable section-alignment extents; it does not alter #4, authorize a host executable mapping or define the future FEX module predicate. Native ARM64 and both PE targets compile complete sizes/alignments and enum order for all eight UnixLib services.

Tool closure binds official CMake bytes and its full extraction, the original Ninja commit/tree/archive/blob/mode/notice graph, selected SDK path/version and actual ARM64 tool execution. Safe framework aliases are resolved before parent traversal. The copied low-level Wine byte readers are component-local; no shared Wine helper or policy changes were made.

### Commit

```text
Task #5 Stage 1: qualify FEX sources and target build contracts
```

## Stage 2 - Darwin Services and Module Construction

### Artifacts

- Attributed FEX Darwin service/build and separate Wine feature/policy supplements in `runtime/fex/patches/` with ordered source/notice identities.
- `tools/fex/build.py`, `services.py`, artifact/service verifiers, native UnixLib and Windows module manifests.
- Original service/layout/error/per-thread fixtures in `tests/fex/services/`, affected portable rejection tests and Stage 2 report/observations.
- Private fresh native/PE builds and per-executable signed service fixture receipts under `.build/task5/`.

### Changes

Port only the selected native Windows UnixLib boundary/build to Darwin; upstream full-root Linux CMake refusal is not solved by removing it. Compile separate native ARM64 Mach-O UnixLib and Windows PE modules with the verified static runtime/import set. Validate actual `.so` naming/search and module table/export roles; selected Wine may correctly append `.so` to a Mach-O module. Build output shape and required ARM64EC/WoW64 flavors are inspected, not predetermined by a label.

Keep the eight-call table order/argument/status/ownership contract. Mapping/PID and any engine-required operations implement real Darwin behavior. Naming/advice/stats/optional acceleration are either supported with actual checks or explicitly disabled/unsupported with documented fallback; no no-op success. Validate descriptor/mapping lifetimes, zeroed outputs, length/overflow/error paths and cleanup without reading unrelated process memory.

Replace Linux-only CPU register/registry assumptions with a truthful Darwin-supported feature policy. Prefer documented actual capability sources; record unavailable privileged/system metadata. If exact useful bits cannot be obtained, expose a verified conservative supported subset and correct software implementation rather than invented Linux registers. Verify initialization and every relevant new thread's ordering choice. Apple TSO authorization is per thread; do not infer inheritance from one successful initialization or another helper. Optional TSO failure must select correctness-preserving software ordering; mandatory unavailable operations fail clearly.

### Verification

Inputs: completed Stage 1 sources/tools/roles, exact new patch layer and original service fixtures. Required tools/platform: verified native/cross compilers/CMake/SDK, isolated owned Wine build/fixture scope, actual private signing/provisioning handle for each restricted executable. Settings: disk admission before full build, bounded serial jobs, controlled descriptors/owned threads/timeouts and preserved failure outputs.

```sh
python3 -B tools/fex/build.py modules --phase complete --inputs runtime/fex/inputs.json --config runtime/fex/build-config.json --prepared .build/task5/stage1-inputs3 --tools .build/task5/stage1-tools5 --host-metadata .build/task5/stage2-host-metadata1/observations.json --cross-tools "$pear_fex_cross_tools" --wine-roles .build/task5/stage1-wine-roles.json --output "$pear_fex_stage2_build" --require-empty
python3 -B tools/fex/verify.py modules --root "$pear_fex_stage2_build" --require-complete
python3 -B tools/fex/sign_services.py --build "$pear_fex_stage2_build" --profile "$pear_fex_service_profile" --output "$pear_fex_stage2_signed" --require-empty
python3 -B tools/fex/services.py run --authorization "$pear_fex_stage2_signed" --output "$pear_fex_stage2_services" --require-empty
python3 -B tools/fex/verify.py stage2 --root "$pear_fex_stage2_build" --services-root "$pear_fex_stage2_services" --require-complete
python3 -B -m unittest discover -s tests/fex -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

Implementation clarification: the command templates now match the implemented split build, signing, live preflight and service replay APIs. Resolve task-specific variables from verified private inputs and fresh `.build/task5/` outputs; never commit their private values. The ordinary service bundle uses the existing Host Probe development profile and requests only application/team claims, with no restricted architecture/JIT/library-validation exception. The pinned source's local `GetSystemInfo` implementation in `CommonWindowsRuntime` queries `NtQuerySystemInformation`; actual selected-member/import proof must establish its use without widening the bootstrap dependency set. These are Stage 2 implementation details in the already approved locations; no engine initialization or new product-documentation scope is added.

Expected: actual native ARM64 UnixLib and required PE modules build/link; source-to-binary table/export/dependency identities and finite service/capability/thread tests pass. Retain syscall/API error domains/codes, optional-service status and fallback, per-thread policy query/observation limitations, grants and owned cleanup. Build and inspect PE modules only. Service/feature/policy fixtures use isolated native/source-defined paths and must not invoke FEX `ProcessInit`, `ThreadInit`, `Context::InitCore` or `CreateThread`. The pinned ARM64EC initialization already creates the core and allocates a RWX return stub before dispatch; merely avoiding x64 execution does not avoid that path. Use owned native fixture threads for policy checks and label them as such; actual translated engine/thread initialization remains deferred to Stage 4/5 after the memory gate. No unsupported executable allocation or engine initialization occurs in Stage 2. If a required platform service cannot work, Stage 2 remains incomplete and records the precise amendment/prerequisite.

### Commit

```text
Task #5 Stage 2: port Darwin host services and build FEX modules
```

## Stage 3 - Coordinated Executable-Memory Ownership

### Artifacts

- Memory contract/design refinement in this implementation plan and component build records, with source-derived allocator/dispatcher/backpatch/retirement inventory.
- Attributed FEX allocator/publication/patch changes and Wine memory/ARM64EC-registration supplements under `runtime/fex/patches/`.
- `tools/fex/memory.py`, independent memory/protection/authorization verifier and original finite code-owner fixtures in `tests/fex/memory/`.
- Exact signed executable/permission, arena geometry/capacity/settings and bounded operation observations; Stage 3 report.

### Changes

Before implementing the owner prototype, review the concrete inventory: every executable allocator, initial 16 MiB/growing 128 MiB shared buffers, dispatch stubs, code bitmap, invalidation and disabled persistent-cache paths. #4's eight 64 KiB slots cannot serve these by assertion. Define measured reservation sizing/admission, alignment, allocation classes, ARM64EC code registration, exhaustion/error behavior and release/reuse rules. Preserve immutable PE versus mutable generated-code ownership and normal security/signature requirements, including actual code-signing page geometry. Do not turn off #4 RWX rejection or use an unqualified private/security shortcut.

Choose a documented feasible publication and patching protocol through an explicitly reviewed design refinement. Protection transitions/dual mappings are alternatives to investigate, not existing FEX options or assumed allowed designs. Specify all writer and executor synchronization, source-address/relocation assumptions, I-cache maintenance, callback reentry, multi-thread observation and retired-version lifetime. The concrete owner strategy in the checkpoint below was explicitly approved on October 3, 2026. Its capacity, registration, synchronization, publication/backpatch and retirement contract now authorizes the finite owner prototype and Stage 3 integration within that scope. Include that refinement with the Stage 3 continuation checkpoint after the completed Stage 2 report. Additional ownership/ABI/security scope changes also require an amended plan before implementation. A successful single code buffer is insufficient for all configured allocation classes.

Reuse temporary emission/relocation and version-held retired buffers; integrate actual copy/publish/rewrite/backpatch/invalidate/free semantics. Published active-code atomic stores must be coordinated with write/execute protection, code registration, instruction cache and all observers. Keep persistent disk cache disabled; identify deferred asynchronous readers/invalidation edges explicitly. Exhaustion, allocation/registration/cache-operation failure and unsupported permission paths produce preserved errors and no partial success.

Run original small native generated-code fixture operations under actual declared executable authorization, then the Wine/FEX owner boundary without translated guest execution. Cover bounded sequential and multi-thread schedules, lookup-versus-retire, patch-versus-entry, immutable mapping refusal and allocation generation/reuse. Use checked errors and controlled finite operations; no new deliberate native fatal-fault fixture or retry of the previously blocked no-TEB route.

### Stage 3 Concrete Design Checkpoint — Approved October 3, 2026

This October 3 refinement selects a **single-address, page-W^X owner with cooperative native quiescence** for the first prototype. It is a proposed design, not a measured working FEX JIT or a completed stage. The requester approved this completed concrete checkpoint on October 3, 2026; source changes, owner construction and finite generated-code fixtures are authorized within its bounds. Additional scope/geometry/ABI/permission changes retain a concrete amendment gate. The location remains this existing implementation plan; no official document, product API or new task-document location is introduced.

#### Source-Bound Inventory and Reuse Decision

The inventory is bound to FEX commit `59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa` and the five-patch Stage 2 source used by `stage2-modules3`. References below are relative to that materialized FEX tree; the ARM64EC/WoW64 module line numbers refer to the Stage 2 derivative. Wine references are relative to #4's final materialized source, manifest `2c0c861669f9fd8853f8899eaeb08b18207b0cf26b34dae9efe707919e447bc7`, rather than an earlier partial patch or the unpatched reproduction input. Those private build roots remain untracked. Revalidate this inventory against the final supplement source/build manifests before accepting a prototype.

| Path and Source Lines | Observed Responsibility | Required Owner Treatment |
|---|---|---|
| `FEXCore/include/FEXCore/Utils/AllocatorHooks.h:49-101`; `Source/Windows/Common/WinAPI/Alloc.cpp:33-103` | Windows executable allocation requests RWX; ARM64EC adds `MEM_EXTENDED_PARAMETER_EC_CODE`; wrappers reach Wine NT allocation/protection | Replace only configured executable paths with explicit owner transactions. Keep ordinary RW allocation separate. Refuse unmanaged executable allocation/protection instead of weakening #4. |
| `FEXCore/Source/Interface/Core/SharedCodeBufferManager.cpp:15-46,59-110` | Shared code starts at 16 MiB, grows to 128 MiB, has a final 4 KiB guard, and frees through allocator hooks | Preserve source growth, guard and shared-generation semantics in a larger bounded owner pool. A guard-protection failure becomes a constructor failure. The upstream comments at 61-79 describe possible mprotect/mirror approaches; neither is an implemented dual-alias option. |
| `FEXCore/Source/Interface/Core/SharedCodeBufferManager.h:34-86` | Atomic 16-byte suballocation; reset changes the cursor | Preserve block alignment and address arithmetic. Reset/reuse requires retirement proof; cursor reset does not revoke escaped pointers. |
| `FEXCore/Source/Interface/Core/JIT/JIT.cpp:853-876,899-921,1144-1168` | Temporary emission, final-address adjustment, copy to shared code, I-cache maintenance; failed allocation currently clears/retries | Reuse emission and relocation. Enter the write transaction before the final copy; publish only after RX/registration/cache verification. Replace unbounded exhaustion retry with a preserved terminal allocation result. |
| `FEXCore/Source/Interface/Core/JIT/JITClass.h:113`; `FEXCore/include/FEXCore/Utils/ThreadPoolAllocator.h:18-38,385-399,410-435`; `FEXCore/Source/Interface/Context/Context.h:437` | Temporary emitter buffers are ordinary RW pooled allocations with timed storage reuse | Retain the non-executable pool. Its 5,000/500 ms reuse policy is not an executable-code retirement grace period. Bound the fixture's temporary storage separately. |
| `FEXCore/Source/Interface/Core/Dispatcher/Dispatcher.cpp:37-51,54-668` | Fixed four-FEX-page dispatcher is emitted directly into executable allocation, then freed | Give the dispatcher a distinct 16 KiB allocation class, staged emission and publication before exposing any pointer. Its entry/parking helpers must remain outside pages undergoing a write transition. |
| `FEXCore/Source/Interface/Core/Core.cpp:869-875,886-913,922-928,1010-1012` | Lookup reads return executable pointers; compilation or cache load precedes lookup insertion | A generation/entry lease must cover every escaped executable pointer and lookup level. Code construction alone does not publish. Cached paths are refused by policy below. |
| `FEXCore/Source/Interface/Core/JIT/JIT.cpp:535-563,603-643,1056-1084`; `FEXCore/Source/Interface/Core/CPUBackend.h:76-99` | Direct/indirect link and delink instruction stores; embedded 64-bit `HostCode`; embedded tail `SpinLockFutex` | All instruction and embedded mutable-data writers belong to one write transaction. Atomics and the current lookup lock do not grant write permission or exclude instruction fetch. Use ordinary RW owner metadata for patch coordination, retaining source-bound code/tail layout unless a separately reviewed layout change is necessary. |
| `FEXCore/Source/Utils/ArchHelpers/Arm64.cpp:1932-1955,2103-2162`; `Source/Windows/ARM64EC/Module.cpp:318-324,730-733`; `Source/Windows/WOW64/Module.cpp:348-357,784-787` | Unaligned-access handling locks the embedded tail and rewrites up to two instructions before retry | Route preparation and write/retry through the checked native exception handoff described below. Disabling the kernel option does not disable these user-space writes; switching to NonAtomic is not an ordering-preserving workaround. |
| `FEXCore/Source/Interface/Core/LookupCache.h:116-145`; `FEXCore/Source/Interface/Core/Core.cpp:484-506,1048-1075` | Invalidation invokes delinkers under lookup locks, clears caches and tracks weak buffer versions | Prepare the affected generation/patch set, release blocking locks before quiescence, then revalidate and commit with existing invalidation/lookup coordination. Detach L1/L2/L3, direct links and call/return references before reclamation. |
| `FEXCore/Source/Interface/Core/CPUBackend.cpp:311-355`; `FEXCore/Source/Interface/Core/CPUBackend.h:148-157`; `FEXCore/Source/Interface/Core/JIT/JIT.cpp:709-716` | Shared references retain current/previous versions, including signal-handler continuations | Retain these references and add explicit executor/continuation pins. A reference, timer or empty lookup alone does not prove that no thread can resume at an old PC. |
| `FEXCore/Source/Interface/Core/JIT/JIT.cpp:802-849`; `Source/Windows/ARM64EC/Module.cpp:688-694,741-749`; `Source/Windows/WOW64/Module.cpp:377-386` | Upstream Windows suspension uses a doorbell and `brk`/exception reconstruction | Reuse state preservation/entry placement where applicable, but do not use this trap as the prototype's parking mechanism or introduce a fatal-fault test. Add a cooperative branch to a native compiled parking helper. Full delivered suspend/exception behavior remains Stage 5. |
| `Source/Windows/ARM64EC/Module.cpp:640-643`; `Source/Windows/WOW64/Module.cpp:556-563` | x64 RET and x86 syscall/unix-call instruction bytes currently request executable memory; WoW64 needs low-2-GiB guest addresses | Classify as guest instruction data, not ARM64EC host code. Preserve guest logical execution/notifications with physical NX data backing through the later loader integration; do not mark them in the EC bitmap. This route is source/build checked here, actual guest/low-address behavior stays Stage 4/conditional Stage 5. |
| `FEXCore/Source/Interface/Core/JIT/JIT.cpp:1202-1215`; `FEXCore/Source/Interface/Core/CodeCache.cpp:665-756,944-1011`; `Source/Windows/Common/ImageTracker.cpp:154,249-264` | Disk-cache copy plus separate experimental file-cache executable allocations/mappings and relocation/finalization | Source-enforce all persistent-cache exclusions below. Keep these paths in the inventory and reject calls while excluded; do not port Linux remap or assume DiskCache alone gates them. |
| `FEXCore/Source/Utils/atomic_segmented_bitmap_allocator.h:54-93,97-155` | Generic executable bucket allocator and ordinary RW bitset, with non-thread-safe clear | No selected Windows runtime consumer was found; the observed instantiations are API tests. Record as unselected and refuse enabling it in this profile. It is distinct from Wine's required EC bitmap; no invented active capacity is assigned. |
| `FEXCore/Source/Interface/Core/LookupCache.cpp:27-92`; `Source/Windows/Common/CallRetStack.h:25-34`; `Source/Windows/Common/InvalidationTracker.cpp:219-248`; `FEXCore/Source/Interface/Core/Core.cpp:1171-1186` | Ordinary RW lookup/call-return storage; guest self-modification and Mono guest writes trigger translated-code invalidation | Keep data backing NX. Audit these notification/delinker edges into the code-owner protocol; do not reinterpret a guest write as authorization to write host JIT code. Guest protection emulation belongs to the later loader/lifecycle stages. |
| Wine `dlls/ntdll/unix/pear_pe_arena.h:7-19`; `pear_pe_arena.c:126-151,192-223,773-940` | One MAP_JIT with immutable PE ownership, eight 64 KiB dynamic slots, actual protection query and checked generation/rollback | Extend this C owner with distinct FEX classes in the same mapping. Retain immutable PE rules, original dynamic class, owner PID/generation and checked rollback; no second MAP_JIT, RWX request, remap alias or relaxation of original PE checks. |
| Wine `dlls/ntdll/unix/virtual.c:1294-1329,2255-2263,3018-3058,5553-5556`; `dlls/ntdll/signal_arm64ec.c:1395,1904` | EC bitmap backing and set/clear are used by call classification; bitmap commit helper currently has no returned status | Reuse the source bitmap representation and classification. Add checked registration/rollback/clear for exact owned code views. Bitmap membership is neither memory permission nor evidence of translated execution. |

Retain upstream C++/assembly and Wine C. New code is the narrowly scoped allocation/lifecycle adapter and its finite tests, not a replacement decoder, IR, ARM64 backend, Rust port or independent CPU engine. Retain MIT/LGPL notices and the independent FEX upstream contribution restriction. No upstream submission is authorized.

#### Allocation Classes, Capacity and Geometry

The following are **initial finite prototype/admission limits**, not measured game requirements or performance targets. Preserve #4's existing reservation as a distinct region: immutable PE interior `1,050,345,472` bytes, dynamic budget `524,288` bytes (8 × 64 KiB), alignment allowance `65,536` bytes. Do not shrink or repurpose those classes. Add two independently bounded classes in the same owner reservation:

| Class | Initial Bound | Alignment / Lifetime |
|---|---|---|
| `fex_shared_code` | 512 MiB (`536,870,912` bytes), 32 × 16 MiB allocation units; allocation sizes 16, 32, 64 or 128 MiB | 64 KiB base alignment; source guard is the final 4 KiB within each allocation; split/coalesce only complete retired extents. Budget counts current and retained versions across all contexts. |
| `fex_dispatcher` | 1 MiB (`1,048,576` bytes), at most 64 source-sized 16 KiB slots | 16 KiB base alignment; publish once and retain until its context/continuations drain. Reserved helper capacity is not a license to add unidentified executable stubs. |
| `owner_metadata` / temporary emission | Ordinary NX backing; at most 128 new FEX extent records, 64 registered executor records, 128 live continuation records and 64 preallocated patch/handoff descriptors for this profile; finite fixtures cap aggregate temporary buffers at 16 MiB | Not part of executable reservation. Reuse source RW emitter storage. Required extra records/workers or larger fixture buffers return a checked capacity error; fixed NX metadata pools must fit a separately asserted 256 KiB total allocation. Descriptor admission allows one pending handoff per executor; nested requests are refused while its slot is occupied. Production limits require later measured review. |
| `guest_instruction_data` | Source-sized ARM64EC RET page and conditional WoW64 stub page | Ordinary NX guest backing, never `fex_shared_code`/EC registered. Low-address admission and guest protection semantics remain later-stage gates. |

With 4 KiB verified protection geometry, insert one 64 KiB no-access separator before each new executable class, retaining class-base alignment. Initial MAP_JIT request is therefore `1,050,345,472 + 524,288 + 536,870,912 + 1,048,576 + 2 × 65,536 + 65,536 = 1,588,985,856` bytes. This is virtual reservation, not a resident-memory estimate. Metadata and temporary RW buffers are excluded from that total. Preserve prefix/suffix alignment slack as NONE; no guard or slack page is allocatable.

The 512 MiB proposal can retain source generations 16 + 32 + 64 + 128 + 128 + 128 MiB (496 MiB) simultaneously. It does not guarantee indefinite nesting or four 128 MiB buffers plus a new generation. Admission accounts for fragmentation and extents, not only free-byte totals. Exhaustion preserves old code and returns `STATUS_NO_MEMORY`/the source adapter's explicit failure; no forced freeing, retry loop or implicit expansion. Generation wrap, foreign/inherited owner, zero/overflow/truncated size, wrong class, duplicate free, stale token and fixed-address requests outside admitted guest-data routes are refused.

Before reservation, bind the actual signed process's guest/native VM page sizes, required protection alignment and code-signing CodeDirectory page geometry. The initial design accepts the qualified 4 KiB Wine compatibility process and existing #4 page-W^X route only when the new executable proves the same operative geometry; an ordinary 16 KiB ARM64 host is not silently admitted. Record CodeDirectory page size independently; it is not substituted for the process VM page size. An operative protection grain above 4 KiB, unavailable geometry/authorization implication or overlapping immutable/generated ownership blocks construction and requires a reviewed geometry amendment. Suballocations may retain source 16-byte offsets, but write transactions include every full protection page they touch, including adjacent published blocks on that page.

This first profile uses no RW/RX aliases and no MAP_FIXED remapping. Keep single-address relocation, branch range, inline tail and exception PC reconstruction assumptions. Measure reservation success, committed/peak resident use, allocation failures and source block-size pressure after approval. Do not advertise these bounds as suitable for Megabonk until the later game milestone measures them.

The reservation does not imply that every pair of code buffers or an external native gate is within an ARM64 immediate-branch range. Preserve the actual `JIT.cpp:603-643` `IsInt26` check and existing indirect `HostCode` thunk fallback. Source-local delink branches still target their same-block thunk; relocation and block-relative ADR/restart rules remain unchanged. New cooperative polling/parking transitions to native compiled functions outside MAP_JIT use a reviewed indirect call/branch with source-equivalent register/vector/flags spill and return reconstruction, or an independently range-checked source-supported form. Do not emit an unchecked immediate branch or assume the 512 MiB class fits a signed 26-bit displacement. Finite controls cover both range boundaries and a deliberately out-of-range target through metadata/owned placement; they do not require a new executable trampoline class. A required new stub/layout or unsupported branch form returns for an amendment before construction.


#### Internal Boundary and ARM64EC Registration

Wine's native ntdll owner remains the authority for MAP_JIT, view classes, effective protection and the EC bitmap. FEX retains its source shared buffer/emitter/generation objects and requests owner operations through a separately versioned **private** Wine/FEX bridge. This bridge is an additional internal ntdll entry, not a renumbering or extension of the source-defined eight-service UnixLib table. Its paired declaration/import/export/build identity and native implementation must be verified; missing/version-mismatched pairing refuses before engine initialization. Keep custom-CRT dependency closure explicit and source matched. The precise ABI layout is reviewed with the fixture before compilation; it must not smuggle an unbounded guest pointer or expose an unrestricted VirtualProtect facility.

The first bridge contract covers `reserve`, `begin_write`, `publish`, `abort_write`, `retire`, `query`, executor register/entry/exit and continuation pin/unpin. A token binds owner PID, class, allocation identity, monotonically increasing generation, exact extent, EC role and lifecycle state; request sizes/opcodes are closed and checked. Requests to immutable PE or ordinary NX backing fail. Allocation states are `reserved_none -> writing_rw_nx -> published_rx -> retiring -> retired_none`; reuse creates a new generation. A published rewrite records the same generation under a closed write epoch and returns to RX before entry can resume. Abort/partial failures never set `published_rx` merely because bytes were copied. Executor/continuation metadata and patch descriptions live outside the executable pages. Validate source-selected offsets, signed ranges, alignment, instruction widths and expected old bytes before any patch. No zero/success fabrication on a refused or unavailable operation.

**Proposed fixed bridge layout for requester review:** private ABI version 1 uses exactly 128-byte request and 128-byte response records with fixed-width C fields and 8-byte alignment; no compiler-sized `bool`, `size_t`, C++ container, callback pointer or architecture-dependent packing appears in the wire record. Keep the existing UnixLib service table unchanged. Verify paired declarations, offsets, sizes, calling convention and import/export identities with static assertions and original portable records before compiling the owner; this proposal is not an implemented or public ABI.

| Record | Fields in Byte Order | Required Validation |
|---|---|---|
| Request, 128 bytes | Four `uint32_t`: `version`, `size`, `opcode`, `flags`; ten `uint64_t`: `owner_pid`, `allocation_id`, `generation`, `write_epoch`, `executor_id`, `continuation_id`, `extent_offset`, `extent_size`, `operation_offset`, `operation_size`; four `uint32_t`: `allocation_class`, `ec_role`, `expected_state`, `reserved0`; two `uint64_t`: `reserved1`, `reserved2` | Exact version/size; closed opcode and opcode-specific allowed fields; reserved/unused fields zero; PID/generation/token/epoch checked; overflow-safe bounded extent/subrange arithmetic. No input pointer or unrestricted protection request. |
| Response, 128 bytes | Seven `uint32_t` and one signed `int32_t` in this order: `version`, `size`, `status`, `flags`, `native_error_domain`, **`native_error_code` (`int32_t`)**, `allocation_class`, `ec_role`; nine `uint64_t`: `owner_pid`, `allocation_id`, `generation`, `write_epoch`, `executor_id`, `continuation_id`, `extent_offset`, `extent_size`, `private_write_base`; two `uint32_t`: `lifecycle_state`, `effective_protection`; two `uint64_t`: `capabilities`, `reserved0` | Zero-initialize before validation. Echo only checked identities; no success/token/address on failure. `private_write_base` is nonzero only for the exact owned `writing_rw_nx` window after observed permission admission, valid only during its closed write epoch; it is never a guest pointer or a general VirtualProtect facility. |

Proposed closed opcodes are `reserve=1`, `begin_write=2`, `publish=3`, `abort_write=4`, `retire=5`, `query=6`, `executor_register=7`, `executor_entry=8`, `executor_exit=9`, `continuation_pin=10`, `continuation_unpin=11`, `executor_unregister=12` and `executor_handoff=13`. Unregister requires no active entry/continuation/request and prevents stale executor reuse. Handoff performs the atomic active-entry-to-native-pinned state transfer below; it is not callable from an unqualified raw asynchronous handler. All request flags are zero in version 1. Publish/abort do not accept a new extent or protection value; they consume the exact existing write epoch. Patch bytes/expected instructions remain source-derived, bounded preallocated FEX NX descriptors, not a pointer-bearing bridge extension. Reject unknown enum values, capabilities and nonzero reserved fields instead of ignoring them.

The following numeric values and field masks close the **proposed** version 1 record. They are subject to requester review; portable layout/validation controls must match them before compilation. No implemented readiness, pointer validation or safe runtime handoff is implied. Both selected host/PE ABIs use the explicitly little-endian fixed-width representation; field offsets, padding and signedness must be asserted in both declarations. Request field offsets are `0,4,8,12;16,24,32,40,48,56,64,72,80,88;96,100,104,108;112,120`; response offsets are `0,4,8,12,16,20,24,28;32,40,48,56,64,72,80,88,96;104,108;112,120`, in their table order. No reserved byte is ignored.

| Domain | Closed Numeric Values / Mask |
|---|---|
| Bridge status | `ok=0`, `invalid_request=1`, `version_mismatch=2`, `unavailable=3`, `capacity=4`, `quiescence_timeout=5`, `stale_identity=6`, `native_failure=7`, `quarantined=8` |
| Native error domain | `none=0`, `errno=1`, `ntstatus=2`, `mach=3`. `native_error_code` is signed 32-bit: preserve the original source NTSTATUS signed value/bit pattern, native errno or Mach code without converting failure to zero or narrowing another width. Domain `none` requires code zero; `ok` requires both zero. Native errors are private evidence; a void cache API supplies no invented native status. |
| Allocation class | `none=0` for unused/global/executor-only fields; `fex_shared_code=1`; `fex_dispatcher=2`. Neither #4 immutable PE/dynamic slots nor guest NX instruction data are reserveable through this bridge. |
| EC role | `none=0` for unused/global fields; `arm64ec_host_code=1`; `native_non_ec_host_code=2`. A nonzero role is checked against the paired source/module profile and allocation class; callers cannot opt into an EC bit or change an existing allocation's role. |
| Allocation lifecycle / expected state | `none=0` only where unused; `reserved_none=1`, `writing_rw_nx=2`, `published_rx=3`, `retiring=4`, `retired_none=5`. Quarantine is a refusal/status, never a successful unknown-protection state. |
| Effective protection | `none=0`, `rw_nx=1`, `rx=2`; no RWX value. The field describes the checked operation window, excluding source guard/slack pages; exact per-page/guard observations remain separately required. Unavailable/unknown protection cannot become `none` on a successful query. |
| Executor state | `none=0`, `native_idle=1`, `managed_active=2`, `native_pinned=3`, `parked=4`, `unregistered=5`. Response `flags` bits 0-2 carry this closed executor-state value only when an executor is part of the response; bits 3-31 and all request flags are zero. Allocation lifecycle retains its separate field and is never reused as executor state. |
| Capabilities | Bit 0 (`0x01`): this single-MAP_JIT owner; bit 1 (`0x02`): observed admitted 4 KiB geometry; bit 2 (`0x04`): global cooperative gate; bit 3 (`0x08`): checked EC bitmap operations. Allowed mask `0x0f`; values reflect actually verified admission, not requested permission. The selected ARM64EC profile needs all four; non-EC fixtures cannot claim the EC bit merely by signing. |

For the opcode table, common header `H` is exactly `version=1`, `size=128`, the listed opcode, `flags=0`, and all three reserved request fields zero. Every operation includes the current `owner_pid`. Token group `T` is the exact owner-issued `allocation_id`, `generation`, `extent_offset`, `extent_size`, `allocation_class` and `ec_role`; ID/generation/size are nonzero and the complete group is checked together. A request never chooses a base address. `X` is a nonzero registered executor ID bound to the actual calling native thread/source context; `C` is a live continuation ID bound to `X` plus the exact allocation generation. Identity counters do not wrap or silently reuse values. Fields absent from a row are **required zero**, rather than defaulted or ignored. An optional `C` may be zero only where stated; an invented cross-thread/foreign continuation is refused.

| Opcode | Allowed Nonheader Fields in Addition to `owner_pid` | State / Zero-Mask Rule |
|---|---|---|
| `reserve=1` | `allocation_class`, `ec_role`, `extent_size`, `X` | Class/role must be selected; source-sized extent admission applies. All allocation IDs/generation/offsets/epochs/continuation/state/operation fields zero. Return a fresh `reserved_none` token. |
| `begin_write=2` | `T`, `X`, optional `C`, `write_epoch`, `expected_state`, `operation_offset`, `operation_size` | Expected state is `reserved_none` or `published_rx`; epoch matches the observed current token state. Nonempty subrange is overflow-checked within usable extent, includes its full protection pages and excludes guard/slack. Close a fresh writer epoch only after native quiescence. |
| `publish=3` | `T`, `X`, optional `C`, `write_epoch`, `expected_state` | Expected state `writing_rw_nx`; exact open write epoch/extent/role/writer must match. Both operation fields zero: consume the stored transaction window, never a new size/protection. Only verified RX/cache/EC/source-entry closure can succeed. |
| `abort_write=4` | `T`, `X`, optional `C`, `write_epoch`, `expected_state` | Expected state `writing_rw_nx`; same exact stored transaction. Both operation fields zero. Verified rollback to its prior state is required; uncertainty returns quarantine with entry closed. |
| `retire=5` | `T`, `X`, `write_epoch`, `expected_state` | Expected state `reserved_none` or `published_rx`; match current epoch. All continuation/operation fields zero. Detachment and complete pin drainage precede EC clear/NONE/reuse; already retired/stale tokens fail. |
| `query=6` | Either `T` with optional `X`/`C`, or optional `X` alone for a global/executor query | All epoch/expected-state/operation fields zero. If allocation ID is zero, every `T` field is zero. Nonzero `C` requires `X` and its complete `T`. Return checked current facts, never fill an unavailable observation with a passing value. |
| `executor_register=7` | `ec_role` | Check the source/module role and actual native caller, return a fresh `X` in `native_idle`. All token/class/epoch/continuation/state/operation fields zero. Capacity counts live records. |
| `executor_entry=8` | `T`, `X`, optional `C`, `write_epoch`, `expected_state`, `operation_offset`, `operation_size` | Expected state `published_rx`, current open epoch; `operation_size=4` and source-bound admitted entry/resume offset is aligned/in bounds, not inline data/guard. Acquire active lease before exposing entry. A source-held continuation requires matching `C`. |
| `executor_exit=9` | `T`, `X`, `write_epoch`, `expected_state` | Expected state `published_rx`; checked active lease/entry epoch. Continuation and operation fields zero. Only at the native gate with no saved managed resumption needing a pin; otherwise use handoff. |
| `continuation_pin=10` | `T`, `X`, `write_epoch`, `expected_state`, `operation_offset`, `operation_size` | Expected state `published_rx`; checked active/held native state; `operation_size=4` and source-bound resume offset. Input continuation ID zero; mint `C` before the last active protection is relinquished. |
| `continuation_unpin=11` | `T`, `X`, `C`, `write_epoch`, `expected_state` | Expected state `published_rx` or `retiring`; epoch belongs to the existing pin, not a fabricated current epoch. Operation fields zero; source proves no remaining saved return/context can resume through this pin before disposal. |
| `executor_unregister=12` | `X` | All allocation/role/epoch/continuation/state/operation fields zero. No active lease, continuation, parked acknowledgment or pending request may remain; consume the executor identity and report `unregistered` without reusing its ID. |
| `executor_handoff=13` | `T`, `X`, optional `C`, `write_epoch`, `expected_state`, `operation_offset`, `operation_size` | Expected state `published_rx`; checked active lease; `operation_size=4` and source-bound saved retry/resume offset. Mint or validate `C`, preserve source state in preallocated NX storage, then atomically transfer to `native_pinned`; parked acknowledgment follows only at the native gate. Unknown/nested/unqualified delivered paths are refused. |

Implementation clarification for the approved native cooperative gate: opcode 13 with `operation_size=0` polls only an already source-bound continuation at its exact saved offset and original pin epoch. It requires nonzero `C`, the same `T`/`X`, `published_rx` and `native_pinned`; it never creates a pin, accepts a new offset or weakens QUERY masks. The initial active handoff still uses `operation_size=4`; nested initial handoffs remain refused. This is the bounded native acknowledgment route for the existing descriptor, with the 128-byte layout and 13-opcode set unchanged. The finite fixture retains missing/foreign/stale continuation, changed offset and inferred-current-epoch refusals and uses that wire route during all four-worker schedules. Source consumers retain the original pin epoch through later writes and must dispose of the pin at a native gate before fresh entry.

All successful responses use `version=1`, `size=128`, `status=ok`, reserved zero and exactly the checked identities/observations relevant to that opcode; unused response fields are zero. Only successful `begin_write` exposes `private_write_base`, and only for its stored bounded window/epoch. Allocation operations report the actual allocation lifecycle and checked window protection; executor-only operations leave those fields zero. Query returns capability bits only from observed owner admission. Failures leave identity/address/capability/state fields zero, preserve the finite status and applicable original signed native error, and do not assert a lifecycle/protection observation. This refusal-only zeroing is not evidence that a failed owner is safe/NONE. A source function cannot dereference or execute a record merely because it parsed; actual native admission, expected-byte/pin checks and the independent source/bridge controls remain mandatory. Any needed additional field/opcode/capability or changed semantics requires a new concrete requester review before implementation.



EC registration applies to generated ARM64EC code emitted by the ARM64EC module, and explicitly identified native dispatcher/helper roles required by that module's call classification. The WoW64 CPU module's native host code follows its actual source role, not an EC flag inferred from its filename. Ordinary x64/x86 guest bytes never acquire EC bits. Commit bitmap backing with observed NT status and actual protection, associate the exact owner view with `VPROT_ARM64EC`, register before publishing any entry pointer and roll back on partial failure. Clear only after entry detachment and generation/continuation drainage, while the owner prevents new entrants; verify exact bits and backing afterward. Retain mixed-role PE/CHPE metadata restrictions for Stage 4. A bitmap read/set fixture does not qualify a hybrid loader or dispatcher.

#### Publication, Patching, Reentry and Retirement Protocol

One process-local writer serializes all managed code transitions. A native compiled gate outside the owner mapping maintains an epoch, executor state and version/continuation pins. Requesting a write closes new managed-code entries, then asks every registered executor to leave/park at that native gate. Active direct links, dispatcher loops, translated block entries, native helper/callback transitions and callback/exception resumes must participate; a direct link cannot bypass the gate. Add cooperative polling at source entry/backedge locations as needed to prevent a tight guest loop from indefinitely hiding from a writer. Preserve guest registers/flags/vector/control state using source spill/reconstruction rules. Do not use a new deliberate trap, a protected-page fault, arbitrary OS suspension or the unqualified no-TEB route to obtain quiescence.

Waiting occurs **before** acquiring Wine `virtual_mutex`, FEX invalidation/lookup/list locks, thread-creation/interval locks or a block-tail spin lock. Existing `CompileBlock`, linker, invalidation and exception callers must therefore prepare/pin their operation, release those locks, acquire quiescence, reacquire the applicable source lock order and revalidate generation/lookup/old bytes. While quiescent, use one reviewed acquisition direction: owner writer gate, FEX invalidation coordination, relevant source list/lookup coordination, then Wine VM ownership. No callback or parking wait occurs under a lower-level lock. Enumerate the final call/lock graph and refuse any reverse edge; this proposal does not claim the upstream graph already obeys that order. Native threads outside the executor registry may not read/write/execute escaped managed pointers; unknown/unregistered reentry blocks publication.

The source inventory finds one mutable inline tail-lock consumer, `ArchHelpers/Arm64.cpp:2106`, and one emitter initialization, `JIT.cpp:1083`. For this first globally serialized profile, replace that consumer's `UniqueSpinMutex(&InlineTail->SpinLockFutex)` coordination with the checked NX owner-writer transaction after validating the pinned generation, block extent, tail offset and expected instruction pair. Keep the source `JITCodeTail` field/layout for reconstruction and initialize `SpinLockFutex` to zero as inert data; neither preparation nor retry may store or lock it in RX memory. The global writer is the replacement serialization authority, so this proposal does not invent an unbounded per-block NX lock table. A newly found consumer or necessary tail/layout change is a refused inventory gap requiring review.

Executor states are explicitly `native_idle`, `managed_active`, `native_pinned`, `parked` and `unregistered`, bound to executor identity plus observed owner epoch. Entry changes `native_idle`/a validated continuation resume to `managed_active` only while the gate is open. Ordinary exit occurs at a compiled native gate outside MAP_JIT. Cooperative/exception handoff first preserves the source state and acquires the generation continuation pin, then atomically transfers its own active lease to `native_pinned` before the writer counts it as quiescent; it never waits for its own interrupted lease. `native_pinned` is not itself a quiescence acknowledgment. Copy every required instruction pair, tail/reconstruction value and expected-byte descriptor into preallocated NX storage while the active/read lease still prevents a writer, before releasing that last read protection. The native gate acknowledges the requested closed epoch and enters `parked` only after no managed-code/data read or write remains pending; saved code/return/tail metadata remain pinned. The writer counts only this completed acknowledgment (or a checked native-idle participant with no pending managed access), never a pin alone, as quiescent. All later preparation uses the NX snapshot and revalidates expected bytes inside the actual closed write transaction. Resume requires a new open epoch, current RX/cache/EC observations and validated continuation identity before restoring state/returning to managed code. Late acknowledgments for a canceled epoch are ignored; callback reentry must take the same entry path. The final source call/lock graph and every such transition are mandatory source-function/bridge evidence before engine initialization.

Prototype quiescence uses a declared monotonic deadline, proposed 2,500 ms per writer request, recorded as an operational refusal bound rather than a performance target. Waits release lower-level locks. Timeout, missing participant, nested unsupported handoff or stale acknowledgment before any permission change returns a preserved refusal, cancels that epoch and keeps existing code/pins intact; reopen only after independently checking the unchanged RX/registration state and publishing a fresh open epoch. Never force a participant, reclaim its pinned generation or treat a timeout as quiescence. A timeout/error after any page/bitmap change requires the existing verified rollback path; uncertain state quarantines the candidate and leaves entry closed. If these outcomes or nested native/exception state cannot be safely represented, the adapter is unavailable and the positive Stage 3 gate remains blocked.


After all affected executors are native/parked, a normal transaction is:

1. Check token, pins, exact pages, current observed RX/NONE state, EC role and expected bytes; no new entry is visible.
2. Change only those full pages to RW/NX, using #4's checked protection/rollback machinery and the actual signed process's JIT permission state. Observe effective protection before writing. No page is simultaneously writable/executable; untouched immutable PE pages keep their original protection.
3. Copy already-emitted code or perform the source-equivalent bounded link/delink/backpatch and embedded-record stores. Retain source barriers/order. Patch coordination uses ordinary RW owner metadata; no lock write is attempted in an RX inline tail.
4. Restore RX, independently observe every page, maintain the ARM64 instruction/data cache through the reviewed source/platform primitive for all changed code and inline literals, and verify required EC registration. If any step fails, detach partial entries and execute no candidate bytes. A recoverable verified rollback is recorded; an uncertain protection/registration state quarantines the owner and stops the candidate. Preserve existing fail-closed fatal handling without deliberately testing that fatal route.
5. Only then release-publish executable pointers/lookup entries and advance the visible epoch; reopen the native gate. Readers acquire the epoch/token before use. Keep a continuation pin whenever a saved return, exception/suspend context or native callback may resume in a generation; a pin prevents retirement but permits a controlled patch while the thread is safely outside managed code.

The entire managed mapping is quiesced in this first design even if a transaction touches one page. It favors a reviewable correctness boundary and makes no throughput/low-power claim. A later concurrent/alias or lock-free publication design needs measured motivation and its own amendment.

**Unaligned exception handoff is a mandatory design gate.** The interrupted executor retains a generation/continuation pin, copies a finite patch/retry descriptor into preallocated NX storage under its active/read lease, transfers its active execution state to the native gate before the writer counts it as parked, and re-enters only after RX/cache/registration verification. Do not wait for its own interrupted lease, allocate/log/lock arbitrarily in a raw asynchronous signal handler or write `JITCodeTail::SpinLockFutex` before quiescence. Keep the source instruction/order/retry-PC behavior; optional kernel backpatch remains unsupported. Source-level review and finite directly invoked exception/patch preparation controls can establish the handoff adapter's bounded contract without provoking a fatal fault. They do not establish real delivered guest exception behavior, which belongs to Stage 5. If the adapter cannot safely transfer every required path, Stage 3 is incomplete and Stage 4 blocked; neither unchecked RWX nor altered TSO semantics is an alternative.

Delivered asynchronous/raw-signal handoff viability remains **unresolved/no-go** in this checkpoint. The current ARM64EC/WoW64 exception entry and source unaligned emulation are not assumed async-signal-safe merely because the owner serializes writers. After requester approval, only directly invoked owned finite preparation/state-transfer fixtures may exercise the proposed descriptor and retry-PC contract in Stage 3. No new handler installs, fault triggering or raw-handler owner/locking calls are authorized by that fixture result. Actual delivered qualification remains Stage 5 work. The mandatory safe source-function/bridge handoff contract must nevertheless pass Stage 3 before any Stage 4 initialization. An unresolved unsafe required source edge keeps Stage 3 incomplete and Stage 4 blocked; if delivered qualification is necessary to establish that required contract sooner, obtain a concrete stage-order amendment rather than creating a Stage 4/5 circular dependency. Optional unselected/raw paths remain explicitly refused, with no invented handler behavior or generic initialization support. Record the exact delivered exception domain/source path and preserve every required edge; never silently enable the source inline write.


Retirement first detaches lookup entries, direct links and call/return caches under source invalidation rules, obtains the native barrier and rechecks all source shared references, active readers and continuation pins. Clear EC registration and make the full retired extent NONE, verify it, then zero/recycle only in a controlled RW/NX phase. Allocate a new generation before reuse. Retain `SignalHandlerCodeBuffers` and inline-context/state reconstruction metadata until their last possible resumption; do not free on weak-pointer expiration, wall-clock delay or a single thread's cache reset. If a pinned old generation consumes the budget, refuse the new allocation rather than steal its backing.

#### Disabled Paths and Actual Permission Admission

In addition to Stage 2's DiskCache/ProfileStats exclusions and required software/vector/memcpy TSO policy, source-enforce `EnableCodeCachingWIP=false`, `EnableLazyCodeCachingWIP=false`, `EnableCodeCacheValidation=false` and refusal of cache-generation/AOT cache publication in this profile. Reject conflicting loaded application/environment overrides before constructing the core. Keep the generic segmented executable allocator, persistent mapped-cache registration/finalization and source paths that cannot identify an owner token unavailable. Document/debug/profiling readers that can retain code ranges must either join the pin protocol or stay disabled. Kernel acceleration is not used to justify unaligned user-space writes or memory ordering.

Apple's [JIT porting guidance](https://developer.apple.com/documentation/apple-silicon/porting-just-in-time-compilers-to-apple-silicon) documents the single MAP_JIT region with Hardened Runtime/allow-jit and thread write/execute restrictions. Its [allow-jit entitlement guidance](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.cs.allow-jit) does not establish this new process's permission or these owner transitions. Preserve the actual #4 page-W^X candidate route and verify it, including any operative thread-local JIT permission requirement, rather than treating `mprotect` success alone as admission. Do not add an unreviewed write-allowlist mode, private entitlement, unsigned-executable-memory exception, disabled library validation or disabled executable-page protection.

Every native owner fixture/Wine loader executable has its own current source/binary/signature/profile/team/device/OS and actual native-ARM64 admission record. Required cross-architecture framework authorization for the compatibility page/x18 route and the declared public JIT entitlement are checked separately; a signed ordinary Stage 2 Host Probe is not the authorization for this new restricted executable. Record CodeDirectory geometry and actual protection observations privately. Genuine signing, an inherited profile path, a parent grant or an EC bitmap cannot satisfy the missing operational capability. Any denied/unavailable/unsupported prerequisite is preserved before restricted operations; distribution/notarization and general user eligibility remain unperformed.

#### Finite Verification and Approval Gate

After approval, implement in this order: (a) attributed source adapters and portable inventory/state/capacity/lock/ABI refusal tests; (b) the actual separately authorized native owner and original ARM64 code fixtures; (c) matched Wine/FEX source/binary integration without `ProcessInit`, `ThreadInit`, `InitCore`, `CreateThread` or guest dispatch. Native fixture workers are original owned threads, not FEX initialized threads. Full-module construction remains serial and root-admitted, preserving all failed build/run outputs. No installed game, Steam login, GPU experiment or new fatal-fault fixture is included.

Initial live fixtures use at most four owned workers, 32 coordinated schedules per case, 16 MiB aggregate RW staging, an explicit operation/output/time budget, unrelated sentinel survival and exact owned cleanup. Reserve the complete proposed VA budget but commit only the bounded fixture pages; an accounting test is distinguished from a full 128 MiB active execution test. Required controls include:

- Exact 16/32/64/128 MiB shared extent admission/guard geometry, dispatcher slot bounds, fragmentation/exhaustion with held generations, immutable/ordinary/foreign/stale/wrong-role/wrapped-generation refusal and unchanged #4 PE/dynamic classes.
- Actual emitted ARM64 fixture results before/after publication and source-equivalent bounded link, delink, inline-literal and each selected unaligned instruction-pair patch. Cross-page writes include adjacent live blocks; effective page protections, cache primitive and bitmap observations are independent of a success boolean.
- Lookup versus retirement, entry versus writer closure, old shared-reference and saved-continuation retention, helper/callback reentry, multiple patch requesters and ordinary directly invoked exception handoff preparation. Hold a participant at each native checkpoint to expose premature publication/reuse. Direct links/backedges cannot bypass the gate; no arbitrary managed-code reader is omitted.
- Checked protection and bitmap commit/register/clear failure injection through controlled return paths; preserve the real observation/error domain and no entry on failure. Cache wrappers may inject an explicit refusal before the actual primitive, but a void cache-maintenance API has no fabricated kernel return/status; verify actual command/source use and fixture behavior separately. Test verified recoverable rollback and refusal/quarantine decisions without deliberately causing a native fatal fault.
- Independent receipt replay of current source/ordered supplements/producers/tools/config/actual signing origin, command and owned logs, every class/token/epoch/protection/bitmap/cache/pin sequence and bounded output closure. Public derivatives contain capacities/counts/digests/named statuses only; no pointers, private roots, profiles or raw diagnostics.

A native owner prototype passing one class is not completion. Stage 3's positive gate requires every configured executable allocation/writer/reader/retirement edge to have a source-bound owner decision and corresponding finite source-function/bridge evidence, actual permission/geometry/registration/protection/cache admission, preserved refusal controls and meaningful affected #4 Wine regressions. Deferred real translated exception/suspend/guest-protection behavior is named Stage 4/5 work, not a passed observation. A required handoff or source path that remains unsafe/unverified keeps Stage 3 incomplete and blocks engine initialization/Stage 4. Runtime, Megabonk and ordinary-user distribution remain false/unperformed.

**Checkpoint requested:** approve this single-address page-W^X strategy, finite reservation/classes, separate internal owner bridge, global cooperative native gate, exception-handoff and reader/retirement invariants, expanded persistent-cache refusal and finite verification scope. Approval authorizes its prototype and Stage 3 implementation only after independent review; it does not approve Stage 4 guest execution or silently waive any failed prerequisite. Any necessary different page geometry, larger budget, alias/concurrent strategy, unqualified handoff, metadata/ABI layout or permission change returns for a concrete amendment before implementation.


### Verification

Required inputs/tools/platform: reviewed concrete design, exact patches/build and owner fixtures, actual native Wine/executable grant/signature, recorded OS/SDK/CPU capability and source/binary identity. Settings: finite capacity/iteration/thread limits, serial native run, isolated prefix, timeout/output bounds, sentinel survival and owned cleanup. Authorization/admission check precedes restricted code operations.

```sh
python3 tools/fex/memory.py --build <verified-owner-build> --config runtime/fex/build-config.json --local-signing <private-authorization-handle> --output .build/task5/stage3-memory --require-empty
python3 tools/fex/verify.py memory --root .build/task5/stage3-memory --require-complete
python3 -B -m unittest discover -s tests/fex -p 'test_*.py'
python3 -B -m unittest discover -s tests/wine -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

Expected: all required declared allocator classes/protection/registration/publication/patch/retirement checks pass with no observed lifecycle violation in the finite schedules. Controls retain raw refusals; no observed failure is not universal race freedom. Any required class, actual permission, registration or published-code write path left unverified blocks translated execution. Run meaningful affected native Wine memory regressions, not only portable mocks. Retain complete owned-address/lifetime evidence privately and sanitized capacities/digests/statuses publicly.

### Commit

```text
Task #5 Stage 3: integrate coordinated Wine FEX code ownership
```

## Stage 4 - Hybrid Loader and First x64 Dispatch

### Artifacts

- Source-matched Wine ARM64EC/ARM64X/x64 loader/emulator-selection and FEX ABI supplements, separated from graphics patches.
- Original redistributable x64 PE/API fixtures under `tests/fex/guest/`; source/expected-result identities and selected fixture target matrix.
- `tools/fex/run.py`, dispatch/module/identity/cleanup verifier, Stage 4 report and public observations.
- Actual paired fresh build, per-executable signed candidate, isolated prefix and bounded native/guest records privately.

### Changes

Implement required hybrid image metadata, imports/redirections, relocation/fixups, guest/native page classes and module lifetime from exact selected Wine/FEX sources. Extend the recorded publisher only for supported explicitly classified images through the verified memory owner; preserve native-only/wrong-module/unhandled-metadata rejection. A dropped CHPE guard or renamed DLL is not integration.

Pair actual ARM64EC entry/callback/TEB/CPU-area/x18 contracts, exception/suspend notification gateway and exported functions. Replace placeholder/unimplemented x64-emulator selection with the real source-built FEX module; bind loaded bytes, table and first guest RIP/result to the selected engine. Validate all required host processes and libraries as native ARM64 with actual translation queries/module formats; unavailable observations cannot satisfy the Rosetta-free claim. Guest x64 PE instructions are translated by FEX rather than treated as native Mach-O identity.

Execute deterministic original small x64 programs: arithmetic/branch/memory results plus bounded Wine API, file/time/event and native callback entry/return cases. Include missing/wrong emulator and unsupported hybrid metadata refusal controls. Record expected guest status/output, emulator entry/exit, native and guest context handoff, owned-child cleanup and unrelated sentinel survival. No game/Steam, new fatal native fixture or performance comparison.

### Verification

Inputs: completed Stage 3 memory owner and Stage 2 services/modules, exact loader patches and original x64 fixtures. Required tools/platform: verified paired Wine/FEX build, current per-executable authorization and native tool/OS identities. Settings: fresh isolated prefix, finite instruction/API cases, timeout/output limits, explicit engine configuration with persistent cache off, bounded serial native execution.

```sh
python3 tools/fex/run.py --build <verified-paired-build> --suite first-dispatch --local-signing <private-authorization-handle> --output .build/task5/stage4-dispatch --require-empty
python3 tools/fex/verify.py dispatch --root .build/task5/stage4-dispatch --require-complete
python3 -B -m unittest discover -s tests/fex -p 'test_*.py'
python3 -B -m unittest discover -s tests/wine -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

Expected: required deterministic x64 fixtures actually enter the recorded FEX translator and return expected results through Wine; required native identities/authorization/cleanup and rejection controls pass independent replay. Module installation/compilation alone cannot pass dispatch. Keep trace instrumentation separate from performance and state observation gaps; #10 later owns complete process/load timelines. New supplemental source/ABI facts have their own hashes, not rewritten #4 evidence.

### Commit

```text
Task #5 Stage 4: execute original x64 fixtures through FEX on Darwin
```

## Stage 5 - Bounded Translated Lifecycle and Conditional WoW64

### Artifacts

- Original finite translated thread/TLS/context/callback/memory-change/exception fixtures under `tests/fex/lifecycle/` and conditional i386 fixtures.
- Required attributable FEX/Wine correctness supplements, suite/config/feature identity and lifecycle verifier.
- Actual final-candidate lifecycle/WoW64 receipts; Stage 5 report and sanitized observations.

### Changes

Exercise translated thread initialization/exit and per-thread policy, TLS, nested native/guest callbacks, guard/protection notifications, code invalidation/retranslation, bounded suspend/read/write/resume guest contexts and supported ordinary exception/unwind paths. Check guest RIP/GPR/SIMD/flags where used and safe lifetime across version/retirement changes. Preserve defined operation failures and context ownership; no mock general unwind, arbitrary asynchronous signal or complete CPU-conformance claim. Broader instruction/ordering/differential qualification belongs to #6.

Review actual WoW64/i386 helper requirements. Build the source-matched module and run original deterministic i386 fixtures when required and supported by the declared route. If optional for this component, document exact unsupported/unavailable cases and downstream Steam/helper dependency; if required for its accepted configuration, absence prevents completion. Avoid claiming both routes from one ARM64EC binary or building unused Linux thunks/rootfs.

Apply fixes only within approved finite scope, then rerun affected dispatch/memory/service/native regressions on the exact changed candidate. No new deliberate native fatal-route fixture or previously blocked no-TEB retry. Keep persistent cache disabled and named asynchronous invalidation gaps visible.

### Verification

Required inputs/tools/settings: the actual verified dispatch candidate, fixture sources/results, bounded controlled schedule/thread/context ranges, exact x64/i386 target inventory and per-executable permission. No independent Windows reference is currently available; deterministic original checks are not differential equivalence.

```sh
python3 tools/fex/run.py --build <verified-final-candidate> --suite lifecycle --local-signing <private-authorization-handle> --output .build/task5/stage5-lifecycle --require-empty
python3 tools/fex/verify.py lifecycle --root .build/task5/stage5-lifecycle --require-complete
python3 tools/fex/run.py --build <verified-final-candidate> --suite wow64 --local-signing <private-authorization-handle> --output .build/task5/stage5-wow64 --require-empty
python3 tools/fex/verify.py wow64 --root .build/task5/stage5-wow64 --require-declared-scope
python3 -B -m unittest discover -s tests/fex -p 'test_*.py'
python3 -B -m unittest discover -s tests/wine -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

If WoW64 is explicitly optional/unsupported, run the declared inventory/refusal gate without invoking an unavailable module and preserve its status/exit as such. Expected: every required finite lifecycle/state/error/cleanup case passes on exact final bytes; optional unperformed/unsupported scopes remain named. Record actual thread policy and invalidation/context/exception outcomes, finite schedule limits and downstream required gaps. Do not convert unavailable reference/helper results into passing claims.

### Commit

```text
Task #5 Stage 5: verify bounded translated lifecycle and helper scope
```

## Stage 6 - Fresh Reconstruction and Integration Handoff

### Artifacts

- `tools/fex/reproduce.py`, strict comparator and independent reconstruction verifier; finalized source/tool/config/patch/notices.
- Fresh owned Wine/FEX outputs, same-final-candidate service/memory/dispatch/lifecycle/native regression and comparison records; Stage 6 report/public sidecars.
- `docs/development/fex-host.md` and narrow approved index/source-status/audit/Wine-guide changes.
- Final task report only through the separate authorized final-report procedure after all stages complete.

### Changes

Reconstruct the selected final Wine/FEX component from exact source and ordered layers into a new owned empty output. Declare compiler/source cache reuse and current-byte verification; no reused prior Wine/FEX binary silently substitutes for fresh construction. Root serializes shared layers/builds/storage with #7. A fresh same-host component build does not imply compiler bootstrap, independent Mac or clean-machine reproduction.

Compare complete unsigned installs and fixture outputs with exact path/mode/symlink/raw hashes. Only independently justified format/path/metadata differences may be accounted for; unexplained executable/data changes fail. Preserve signed identities separately; development signatures need not be deterministic. Bind all required suites and affected native #4 regressions to the same final paired signed candidate; reexecute when changed bytes/settings invalidate earlier results, not simply to duplicate logs.

Publish scoped contributor reproduction, notices, actual host/tool/settings/permissions, enabled features and finite supported fixture boundaries. Append dated follow-up facts and leave #1/#4's historical readiness/results intact. Handoff to #6 wider CPU correctness, #10 process/load coverage and #11/#12 Steam/game work; no launcher, performance superiority, Megabonk or ordinary-user support claim. Reconcile each Issue acceptance dependency with actual selected-source and permission evidence before final completion; unresolved required prerequisite evidence remains open.

### Verification

```sh
python3 tools/fex/reproduce.py --inputs runtime/fex/inputs.json --toolchain runtime/fex/toolchain.json --config runtime/fex/build-config.json --source-cache <read-only-selected-cache> --tools <verified-local-tools> --local-signing <private-authorization-handle> --output .build/task5/final-reproduction --require-empty
python3 tools/fex/verify.py reproduction --root .build/task5/final-reproduction --require-complete
python3 -B -m unittest discover -s tests/fex -p 'test_*.py'
python3 -B -m unittest discover -s tests/wine -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

Inputs/tools/settings: finalized exact component/source/layer/fixture and current actual tool identities, measured admitted storage/jobs, private actual authorization and owned empty outputs. Expected: complete provenance/notices, no unexplained comparison mismatch, required real small-x64/service/JIT/lifecycle and affected native results on the final candidate, independent replay and documentation/local links pass. All required acceptance gaps remain failures/unavailable rather than declared complete. Retain raw failure/comparison and signed/unsigned scopes privately, reviewed sanitized results publicly.

### Commit

```text
Task #5 Stage 6: reconstruct FEX integration and document verified scope
```

## Verification

Run applicable checks before the stage report. Source inspection, compile/link-only capability fixtures, native services/JIT tests, real translated execution, game qualification and distribution are distinct. An unexpected verification failure leaves the stage incomplete; deliberate negative/refusal controls pass only their explicitly named assessment, not the underlying positive capability. Do not write a completion report while required verification fails.

Actual implemented CLI spelling/local layouts are finalized before operation and retained in receipts. Substantial ownership/design/scope/document-location changes require approval before implementation. Run meaningful affected shared/native regressions and public link/governance checks; no unrelated baseline suite repetition without changes or unresolved concern. Preserve failed artifacts and the immutable retained evidence checkout; clean worktrees after commits. Use the stage-report procedure before continuation.

## Commits

Each stage commit includes implementation, meaningful fixtures/verification and `mydocs/working/task_m1_5_stage{N}.md`, sanitized sidecars and root-coordinated board update. Messages follow `Task #5 Stage {N}: summary`. Keep stage commits and ordered patch identities. Final report/PR publication and merge/Issue closure are separate approved procedures, not implied by plan approval.

## Stage Dependencies

- Stage 1 requires explicit approval of this implementation plan and its first-stage scope.
- Stage 2 requires completed Stage 1 capability gates/report/commit and explicit continuation; required real host permission and full-build storage admission precede operations.
- Stage 3 requires completed services/modules and explicit continuation approving the concrete source-bound memory-design refinement before any owner prototype/integration; the broad plan alone does not select or authorize that unresolved protocol. No JIT shortcut follows from a compile success.
- Stage 4 requires verified owner/registration/publication/retirement and source-matched hybrid contracts plus explicit continuation. Missing required geometry/permission/lifetime evidence blocks translated execution.
- Stage 5 requires real verified small-x64 dispatch and explicit continuation; its mandatory/optional WoW64 scope is declared, not inferred from upstream names.
- Stage 6 requires all declared service/memory/dispatch/lifecycle gates and explicit continuation. Final completion also requires the Issue's relevant source/permission/native prerequisite evidence; historical Issue closure alone is insufficient.

## Risks and Responses

- **JIT geometry and live patching:** inventory every configured executable allocator and define measured bounded capacity/synchronization/registration. Preserve security protections and gate translation on actual finite owner tests.
- **Hybrid ABI and target assumptions:** distinguish COFF/PE/CHPE/native roles; inspect actual outputs and entry/context behavior. Refuse unsupported metadata instead of deleting guards.
- **Darwin feature/TSO gaps:** use truthful supported capabilities and per-thread checks, with verified software ordering; no invented register bits or inherited authorization.
- **Retirement/context/exception gaps:** preserve finite schedule and ordinary exception limits, disabled disk caches and named deferred readers; wider conformance belongs to #6.
- **Missing tool/static-link/permission/storage:** scoped actual acquisition/admission and preserved errors; no global/security changes, ignored prerequisite or arbitrary cleanup.
- **Shared CPU/graphics work:** root owns conflicts/common owners/resources and validates independent patch-layer combination before combined use.
- **Licenses/contribution policy:** preserve applicable notices/modified source/build recipes and independent upstream contribution restrictions; no upstream submission or release clearance claimed.

## Approval Request

Approve this six-stage implementation split, component/tool/interface/evidence contracts, exact document-location matches, memory-design review checkpoint and commit messages. Authorize Stage 1 source/tool/static-link/interface closure only. It does not include full FEX module builds, native UnixLib/JIT execution, x64 dispatch, Steam or Megabonk. Later stages need explicit continuation after their completed reports/commits and actual prerequisites.

## Approval Record

On October 2, 2026, the requester explicitly continued in the same thread with “Proceed.” (translated from Korean) after the joint detailed-plan review request. This approves the implementation plan and Stage 1 only. Stage 2 and later transitions retain their separate report, commit and explicit-continuation checkpoints.

On October 2, 2026, the requester explicitly continued in the same thread with “Proceed.” (translated from Korean) after both completed Stage 1 reports and bundled commits. This authorizes Stage 2 within its approved scope. Later stages, the concrete FEX executable-memory design and any additional Metal installation/account interaction retain their separate approval checkpoints.

The requester explicitly continued in the same thread after both completed Stage 2 reports and commits. This authorizes the Stage 3 inventory and concrete-design review recorded above. It does not approve that new owner strategy or its prototype; independent review and explicit requester approval of the concrete checkpoint remain required.

On October 3, 2026, the requester explicitly approved the completed Task #5 concrete single-address memory-owner design and continuation to Task #7 Stage 4 in the same thread. This authorizes Task #5 Stage 3 implementation/prototype within its reviewed capacity, ABI, synchronization, permission and finite verification scope, and Task #7 typed-driver implementation/native verification within its approved plan. Later stages, guest/game execution, new security or shared-scope changes and PR publication retain their separate gates.


## Proposed Stage 3 Resume and Initialization Qualification Amendment

Prepared October 3, 2026; explicitly approved by the requester in the same
thread on October 3, 2026 after the amendment explanation. This authorizes A
and B only within the prerequisites and exclusions below; it is not a Stage 3
completion report. It stays
in the previously approved task implementation-plan location in `mydocs/plans/`;
no product, integration or architecture document is added or changed.

### Observed Need and Completed Independent Work

The version-1 source gate currently performs an original dispatcher continuation
UNPIN followed by ENTRY. A source marker may close, or a direct owner retirement
may intervene, after UNPIN. ENTRY with the original continuation instead retains
it in MANAGED_ACTIVE, where current EXIT/UNPIN cannot consume it. A marker ticket
alone cannot establish owner mapping or C++ object lifetime. Do not qualify either
sequence as completed resumption.

The eleven current source layers passed 22 genuine Git check/application commands
on a new source copy: 6,963 regular files, 40,431,343 bytes, complete expected
bytes/modes and an unchanged baseline. The existing Stage 2 and Wine memory-build
records were independently replayed against current files. Eight genuine
compile-only layout commands subsequently passed, with actual depfiles closed and
input bytes/modes unchanged. The matched ordinary Windows ARM64 C++ and native
macOS C constant tables measure owner+mutex+condition103,392 bytes,
Common Bindings64=18,944 bytes, link Registry13,896 bytes and the compacted reader
snapshot424 bytes. No object was linked/loaded, instance constructed or engine
initialized. Concurrent transient/source-object counts and the genuine unaligned
saved context remain unclosed; these measurements do not pass the aggregate
262,144-byte gate. These are source/build prerequisites only. Actual Wine run2
entered the ordinary ARM64 fixture and passed
three readiness calls, then failed its first reserve because bitmap restoration
was not proved. Its output and cleanup records remain preserved. Diagnostic
instrumentation, compiled metadata accounting and all mandatory source handoff
edges remain separate unfinished obligations.

### A. Atomic Original-Continuation Resume

Propose paired private ABI version 2 and `PEAR_FEX_EXECUTOR_RESUME = 14`. Retain
both 128-byte layouts and offsets, Unix index10, role1/role2, every arena/page
geometry and capacity, the 256-KiB aggregate metadata ceiling and current signing
and permission policy. The other thirteen operations retain their meanings.
Version-mismatched peers refuse; retain all version-1 producer/input/results.

The closed request mask is T|E|X|C|O|S. Supply the genuine dispatcher extent and
registered executor, current published epoch, original nonzero continuation,
exact original resume offset, operation_size4 and PUBLISHED_RX expected state.
Flags/reserved words remain zero. No caller-selected callback or replacement
original epoch is accepted. The continuation/descriptor retain the original epoch;
source validation also compares the real gate's saved epoch before the call.

Under the existing owner mutex, validate the executor/extent/continuation and sole
original descriptor, NATIVE_PINNED, matching allocation/generation/role/offset and
original continuation/executor/descriptor epoch. Keep the original pin through
bounded park and every precommit refusal. Re-resolve/revalidate every identity,
current epoch/state/bounds, backend entry and actual RX observation after any wait
that releases the mutex. A changed current epoch returns stale; a bounded caller
may refresh its real dispatcher snapshot and retry with the unchanged original pin.

Only after those checks, atomically consume the original continuation/descriptor
and renew MANAGED_ACTIVE on the current epoch. Perform no fallible native call or
allocation after that commit. Return continuation_id0, MANAGED_ACTIVE flags and
exact published/RX extent facts. Common updates its actual ACTIVE lease from the
validated response. A malformed post-call response is unresolved; it is not proof
of either retained pin or renewed ACTIVE. A subsequent expected-word mismatch
preserves the primary failure and separately attempts checked EXIT; it cannot
claim that the consumed original pin was restored.

Source resumption also requires a bounded sealed entry reservation, actual
Context/Thread/Dispatcher lifetime admission and every direct writer/retirement
edge. Do not hold source locks over owner park/wait. Temporary source closure
uses the existing original-descriptor Poll plus a finite condition wait. Record
the composed source/owner deadlines honestly; do not promise a single 2,500-ms
wall-clock bound when an in-flight owner call has its own bound.

Required finite ordinary-ARM64 controls cover valid consumption, duplicate/stale
resume, wrong executor/extent/role/offset/epoch/continuation, closed-gate park,
retire refusal while pinned, precommit timeout/native-error pin retention,
malformed response uncertainty, postcommit byte-check cleanup and subsequent
ordinary ENTRY/EXIT. Rebuild and replay the changed paired owner/bridge/source
identities; old native success does not qualify version 2. No guest, game, hybrid
load, GPU or new security permission is included in this operation.

### B. Narrow Source Initialization Qualification Within Stage 3

Propose a separately gated empty-process fixture for the ordinary ARM64/role2
source route, allowing only actual source Context creation, `InitPearCore` and
`CreatePearThread`/matching cleanup after complete input/build/ABI/current
permission and memory-owner admission. It must reuse actual FEX configuration,
host-feature policy, selected source DummySignalDelegator, Windows host services,
real TEB and source-created Thread/Frame/backend. No substitute structures,
borrowed Thread, module-return impersonation or fabricated ACTIVE lease qualify.

Before execution, source/compile/link verification must close that fixture's
actual selected initialization/cleanup call graph and typed failure propagation.
Add a source-known finite native transfer site and spill/restore contract for
original owned ARM64 fixtures; compile/link return labels do not become exception
return labels. Retain the real dispatcher, actual retained JIT owner and required
bounded saved context while changing leases. Qualify directly invoked finite
snapshot/transfer/patch preparation only after those prerequisites pass. Count
all added persistent and concurrent transient metadata before admission; an
unknown size or total over262,144 bytes blocks this fixture.

This narrow exception to the current Stage 3 no-initialization rule permits no
translated x86/x64 instruction, guest dispatch, full exported Module ProcessInit
or ThreadInit path, hybrid image/CPU-area fabrication, delivered/raw fault or
handler installation, arbitrary suspension, Steam or game. ARM64EC/role1 and real
delivered exception behavior retain their later qualification gates. A missing
legitimate finite source path remains unavailable rather than being bypassed.
Stage 3 still requires all mandatory source-function/bridge evidence and affected
Wine regressions before reporting completion; ordinary initialization alone
cannot open Stage 4 or satisfy the Issue acceptance criteria.

### Requested Decision

Approve A's exact paired version-2 atomic resume contract and finite controls,
and B's narrow source-initialization qualification order with the listed mandatory
pre-execution gates. Until explicit approval, continue only the already approved
source/build/finite noninitializing controls. Larger capacities, new permissions,
raw delivered behavior, guest execution, later stages and publication remain
outside this amendment.

## Stage 3 Diagnostic Integration Checkpoint — October 3, 2026

This is a clarification of implementation within the approved Stage 3 source
and finite diagnostic scope, not a completion report or approval of the proposed
resume/initialization amendment above. Wine Run 2 remains failed at the first
shared reservation; its original bitmap-restoration failure and quarantined
prefix are preserved. No newly built Wine diagnostic or FEX initializer ran.

The reviewed diagnostic instrumentation is folded into the existing second
Wine supplement. Its new patch SHA-256 is
`d5e70eca7b9c9b5da91c2f29fb7f62b5762af103825a653266df0046f16bdc1c`;
the new two-patch series SHA-256 is
`538bfba9aa864e5edd105469e24550aa364f42f9280469e855848db39f491a96`.
Only the previous `virtual.c` postimage changes, to
`90de95689164e98ba3d027a9692ba0769222ae915749110712aa239d3dc5505e`.
The original ten-field primary record, success predicates, quarantine,
native-observer call order, geometry, ABI and security policy are preserved.
The 320-byte diagnostic/storage assertion is a local source bound; its actual
compiled size and whole-process metadata accounting remain unperformed/unclosed.
The unchanged builder replayed the genuine #4 source/install baseline and all
12 supplement source postimages without running a compiler or native process.

`tools/fex/memory_wine_bitmap.py` provides closed diagnostic pairing and is
included in the runner's producer snapshot. Completed assessment still requires
the independently derived full self-test count and every original successful
primary predicate with zero native error. Separate failed-prefix observations
retain only validated adjacent pairs with raw offsets, spans and hashes; they
never qualify a completed count. Malformed stdout cannot suppress original
stderr failures, and paired parser refusals cannot replace the primary error.
Independent review re-ran 34 private source/parser controls and 13 prefix/stream
controls. The tracked suites passed 129 distinct relevant portable tests across
the initial 121-test run and the subsequent 80-test run containing eight new
prefix controls. These observations establish Python/source behavior only.

The proposed full-FEX constructor/checker remains private and unpromoted.
Independent review found four derivation gaps requiring correction before an
actual build: selected headers/depfiles, exact source method identities,
canonical system dependency paths and native-link-output-to-install origin.
Fresh Wine/FEX builds, signed runtime admission, bitmap diagnosis, aggregate
metadata and the genuine source handoff remain open. Current available storage
is about 4.0 GiB; fresh construction retains its 8 GiB admission requirement.
Stage 3, translated execution, Megabonk and distribution remain unqualified.


## Incremental Preservation and Storage Authorization — October 3, 2026

The requester explicitly continued and instructed incremental GitHub preservation
of important verification results and artifacts, with removal of unnecessary
repeated local outputs. Publish reviewed source and sanitized in-progress
observations to `codex/publish-task5`; do not call this a completed Stage 3 or
open a final PR before the required checks pass. Preserve original errors,
receipts, commands, producer/source versions and inventories before pruning
redundant generated install/app payloads. Preserve required current donors and
private inputs. Record every pruned root and distinguish retained evidence from
a now-unavailable complete historical payload replay. Never upload profiles,
private diagnostics, prefixes, game content, account state or saves. This
instruction supersedes blanket retention of redundant generated payloads, not
retention of unique failure evidence. Heavy builds and native runs remain
serialized under the root owner with fresh disk admission. No later stage,
guest/game execution, new permission, release, merge or Issue closure follows.

The October 3 incremental source checkpoint passed all 268 currently tracked
FEX portable tests and offline governance (22 documents/172 local targets),
with unstaged whitespace checks clean. The first staged check exposed one
pre-existing trailing space in the newly added builder; a follow-up removes
that space before fresh construction. These are portable/source observations only;
Wine Run 2 remains failed and Stage 3 remains incomplete. The checkpoint
contains ABI1 diagnostic source; approved ABI2/resume and initialization work
has not yet been promoted or executed. Historical free-space observations above
are dated measurements, not current admission.


### October 3 Storage and Diagnostic Build Checkpoint

The reviewed source checkpoint is Git commit `7c78e59` on
`codex/publish-task5`. After preserving private per-file hash/size/mode/link
inventories and embedded profile copies, root removed only the generated
`install` children of failed Wine builds 2–4 and app-bundle children of failed
Wine runtimes 2–4. Source trees, inputs, producer snapshots, receipts,
configuration, commands and raw errors remain local; accepted build5/runtime5/
run2 and all required #4/#5/#7 donors remain. The observed free-space delta
was 6,317,473,792 bytes (about 5.88 GiB), not an inferred `du` total. Full replay
of those six pruned historical payloads is now unavailable; retained inventory
records do not substitute for their bytes. Private cleanup receipt SHA-256:
`43abf8b245262db463533e46e2472c12721c0d7d08c94b17349d20e013c39f1e`.

Fresh diagnostic Wine build6 completed four compiler/build commands with exit0.
Its current source/tool/configuration/install replay passed independently.
The only builder change after the source checkpoint removes one trailing space;
21 builder controls passed. Receipt SHA-256:
`927d3b11d240e71d9833c31d21167d6bc37acdedbba5928b547666dfc6b653b9`;
source inventory `957b25bee9aeaf3184f280b464fd31442f008bfb9c03feac05de61b987fc9173`;
unsigned install inventory
`b9b12dac3bb55e6578dffdedad9a3b191039c5831df8dc2381b11d63c92ae3bd`.
This is a rebuilt ntdll/fixture slice over the preserved #4 baseline install,
not a freshly rebuilt entire runtime. It retains ABI1. No initializer,
translated guest or game ran in this construction. Fresh signing, actual
bitmap diagnosis and approved ABI2/source-lifetime work remain separate gates.


### October 3 Actual Bitmap Failure Diagnosis

Fresh runtime6 passed genuine current development authorization for39 native
images and756 PE images; signed preparation executed no Wine. Fresh Run3 then
entered the ordinary ARM64 fixture, passed readiness and registration, and
failed its first shared reservation with owner status7 and native error0/0.
The actual diagnostic mask was6176 (32+2048+4096): release classification
returned-1, so native release was not attempted and original bitmap/PEB
identities were not restored. Bitmap set/clear, RW cleanup and page-protection
restoration passed; force-exec was false. This rules out the previously
considered force-exec hypothesis for this run. No generated leaf, FEX
initializer, translated instruction or game ran. Loader exit1 was retained;
all owned processes were reaped, cleanup had no errors or observation gap,
and the unrelated sentinel survived. Case receipt SHA-256:
`87934dff2a07ea1f30fbe20c2fcb74068cfbdb6ea8fb2df70d07b8de5566aa53`;
source-failure receipt
`481514a320dd9080d7510b5521b9f96b86f776187f22c2ef97f1da29dce18144`.
The prefix remains quarantined. Stage3 remains incomplete.

Source inspection found the legacy reservation classifier uses a strict
`area_start > view_end` comparison whereas Wine unmap uses half-open
`area_start >= view_end`. Exact adjacency can therefore report partial overlap.
Actual boundary geometry is unperformed; this is a source-supported candidate,
not a confirmed runtime cause. A local bitmap classifier proposal preserves
the generic Wine helper and every genuine partial-overlap/arena/native-error/
restoration refusal. Independently review and test it before promotion. Combine
any accepted fix with the approved ABI2 slice in the next fresh build to avoid
redundant construction; retain Wine6 and its original diagnostic evidence.


### October 3 ABI2 Owner Checkpoint — In Progress

The reviewed atomic leaf now uses private paired wire version2, still128 bytes
and Unix index10. The owner retains the actual original continuation and its
epoch until current source identity, executor, offset, current extent epoch and
RX observation pass. Re-resolution follows any mutex-releasing park. Only then
is the original continuation consumed atomically into ACTIVE; no fallible
operation follows the commit. Source Common retains the pre-call tuple as
Unresolved on called or malformed uncertainty, without retry/ACTIVE authority.
Core call-site replacement, sealed source entry and Context/thread lifetime
remain unclosed; an owner protocol success does not qualify those source paths.

The bitmap release fix changes only its local reservation classifier to
half-open ranges; the generic Wine classifier and all original genuine-partial,
restoration, native-error and quarantine refusals remain intact. Independent
numeric review covered1197 cases and an actual ARM64 C metadata fixture passed
32 cases. C receipt SHA-256:
`bd288c3136f8db02f7aeedb2cef64ce69f963324fbd089add49006aeafbbefc3`.
The actual failed Wine address geometry is still unperformed; its cause is not
claimed fixed before a fresh integrated run.

The original real C fixture adds nine malformed atomic-resume requests, each
followed by an actual original-pin poll, then a real owner write, old-current-
epoch refusal, current-epoch resume, consumed-pin refusal and checked native
exit. Seventy-two portable wire/transcript controls passed. A freshly built,
individually authorized/signed native owner passed964 calls,153 controlled
refusals,40 publications,83 protection observations and73 owned leaf calls.
The separate cooperative fixture passed four owned workers,32 schedules,96
handoffs/leaf calls,30 writes and96 actual wire polls. Both owned sessions
reaped their owner and sentinel with complete cleanup, no cleanup errors and
no observation gaps. Native receipt SHA-256:
`24d0f0737fd25779240ddd335053d2f3f3605c863a08c93661ef8b0683110aef`.
These are finite ordinary ARM64 prototype results, not Wine EC registration,
FEX initialization, translated guest, game, general race-freedom or distribution
qualification. All corresponding eligibility flags remain false.

The first combined Wine attempt rejected an extra manifest field before
compilation (`memory_wine_series_geometry`). The existing closed geometry
schema was retained; authoritative wire-version2 lives in the exact paired
header. That failed receipt remains preserved. The next fresh constructor
combines only the reviewed bitmap boundary fix and ABI2 owner/fixture sources
against the same qualified #4 baseline; no obsolete build is relabelled.
Stage3 remains in progress with full metadata/lifetime/source gates open.


### October 3 Actual ABI2 Wine and Source Reconstruction Checkpoint

The combined current ABI2 Wine build8 completed four actual build commands
with exit0. Its receipt SHA-256 is
`c54cd61b6bf45f6ee76767cdc3d874394d3a6d89aa3802077d60b5cfe4679180`;
source inventory
`901637d2e61ce58189e4c33b590602539aa261e597bbea08f0bf8e929b0bd81e`.
This rebuilds the selected ntdll/ordinary ARM64 fixture slice over the retained
qualified #4 install; it does not freshly reconstruct all Wine. Runtime7 passed
current genuine development admission and individual signing for39 native and
756 PE images. These construction/admission operations did not run an engine.

Actual Wine Run4 exited0 after964 owner calls,153 controlled refusals,40
publications,83 protection observations and73 finite owned leaf calls. The
fixture recorded156 VirtualQuery observations. All38 actual bitmap diagnostic
rows observed set/clear and original source-view, bitmap and PEB restoration,
with zero diagnostic mask. Owned loader/server/sentinel cleanup was complete,
without errors or observation gaps. Its original aggregate assessment failed:
Wine's ordinary PE front door refused the ARM64EC role with UNAVAILABLE3 before
the Unix call, whereas the old checker expected native-owner STALE6. Original
case, failure assessment, producers and raw logs remain immutable. Case SHA:
`0064e898764256e40e5eb79f9050a4eefe2a288628234f80ef43a9026f7a6394`;
source-failure record
`cfba9f505658488b1437db91c6a6dc9e39f2f627564a9647e7545bb753e96702`.
A separate current-reader reassessment is required; do not relabel the original
failed aggregate or its unqualified completed-count field. This finite ordinary
ARM64 run performed no EC registration, FEX initialization or translated/game
execution. The original failed Run3 boundary geometry remains unperformed.

The current transcript reader requires explicit native/Wine scope and its exact
role refusal, request sizes/offsets/states, actual original continuation and
16KiB D extent, initial publication, interposed new publication/current epoch,
and ordered retirement/resume/consumption/exit. It does not accept an arbitrary
greater epoch or a moved pin-retirement control. The repository's complete FEX
portable suite passed442 controls with one genuine APFS case-collision skip.

The approved supplemental source graph is now thirteen ordered strict patches
and exact Git derivatives with sanitized provenance, current ABI2 wire and all
source gates false. Original11 layers and upstream C++/assembly/license notices
are preserved. A fresh projection receipt is checked and its actual digest
bound into each build; another valid receipt cannot replace that saved identity.
The selected Stage2 baseline receipt remains local and scope-bound; contributor
portability is not claimed and private receipts are not published as a workaround.

A genuine projection under the tracked task worktree failed the final byte gate
although all26 Git commands exited0. Every36 affected source path remained the
original baseline and the12 new files were absent. Git discovered the enclosing
Pear repository and skipped patch paths outside its current subdirectory. The
private temporary projection had passed because it had no enclosing Git checkout.
Retain the failed source1 record and isolate ambient Git discovery explicitly
before a new projection. Do not admit the unmodified tree or call compilation.
Full FEX compilation, source lifetime, sealed entry, Core atomic resume, whole
256KiB metadata admission and genuine empty initialization remain separate open
gates. Stage3 is incomplete.


### October 3 Separate Immutable-Record Reassessment and Payload Cleanup

An independent guarded offline evaluation, then a separate root replay, admitted
both original native transcripts and the complete original Wine case using the
current strict native/Wine-scope checkers. The Wine case has964 owner calls and
seven registered processes observed entering ordinary ARM64 PE; it independently
counts38 successful shared reservations and38 paired bitmap/restoration records.
Original launch, event, native-image identity, descendant exit, sentinel and
cleanup checks passed. A separate source-failure scan was empty without parse
error. Its diagnostic-prefix completion field remains false; the completed
count comes from the strict full-case parser, not that partial scan.

All915 bound source/image/record/log/checker files retained exact before/after
bytes, sizes and modes. No execution/subprocess/signaling/observer/CDLL guard
was reached. Derivative control SHA-256:
`16e25f9651ebfeebd150194b3e7457f1c37588e795dbf741772a1967bd6a746b`.
The original Wine aggregate still records `memory_wine_call_status` and remains
false. This derivative is neither historical `verify_run` success, a new native
run, current permission verification, general runtime qualification nor Stage3
completion. FEX initialization, translated/game execution and distribution
qualification remain false. The first root replay pre-copied a directory that
the frozen evaluator creates and stopped with FileExistsError; that preparation
failure was retained and a new output-only replay passed without source changes.

A second reviewed payload cleanup independently rehashed every selected old
and retained current file before deletion, then checked the deletion barrier
and retained unique/control identities. It removed10,836 byte-and-mode-identical
regular files from old build5/6 install/fixture and runtime5/6 app payloads,
totaling4,939,589,088 logical bytes. All88 unique payload copies remain, including
all78 old signed native images and old ABI1 ntdll/owner variants. Sources,
objects, producer snapshots, signatures/profiles, logs, prefixes and current
build8/runtime7 donors were excluded. Observed volume free space increased
2,490,621,952 bytes (about2.32GiB); physical APFS reclaim remains unknown.
Private completed cleanup receipt SHA-256:
`bebd7dbac3a9510478b1459cbc1b7153d6d42ab240f7285a2afafad9632520b9`.
Full pruned historical payload replay requires exact donor-based rehydration;
records and hashes cannot replace those missing bytes.


### October 3 Git-Isolated Tracked Source Projection

The source helper now uses a fixed documented `GIT_CEILING_DIRECTORIES` boundary
at the new canonical output, above its source cwd. Inherited GIT_DIR/WORK_TREE
are not forwarded; aliases, non-directory and colon-separated ambiguous paths
refuse. Existing source hunks, graph, wire, compiler settings and baseline remain
unchanged. The [Git apply manual](https://git-scm.com/docs/git-apply) documents
subdirectory exclusion; the [Git environment manual](https://git-scm.com/docs/git)
documents discovery ceilings. There is no unsafe-path/index/output-repository
initialization workaround. The exact new helper digest is independently pinned
and requires a genuinely fresh source receipt.

A real tiny nested-repository regression reproduces the former exit0 skips,
then applies exact changed/added bytes with the production helper and proves
ambient Git/baseline/outside-file preservation. Root's137 targeted controls
passed with one APFS case-collision skip. The three historical first-adapter
controls remain distinct from the seven new source-driver controls.

The real tracked task output source2 ran26 actual Git check/apply commands with
exit0, materializing all36 changed paths and12 additions:6963 source files /
40,437,635 bytes, with the unchanged final source manifest
`74751c67271521cc86ec14ccc06f98e2019be0be2dae2f742376963c5dde759a`.
Root's independent current-reader replay admitted the actual new control
`89f71d323921557ac68ed7ab358c9317127245d091b6435d6b1be7eb707deb3b`.
The original failed source1 receipt is retained. No compiler, initialization or
owner operation occurred in projection or its pure replay.

The full selected ARM64EC/WoW64 FEX constructor was then admitted with one job,
2GiB growth ceiling,2GiB reserve and actual11,209,162,752 free bytes before the
separate operation. These are operational bounds, not a measured peak. Its
actual compiler/link/object/import proof remains in progress and modules must
not load or initialize. The canonical13-layer source still records every open
lifetime/entry/Core/metadata/initialization/translated/game gate false.

The complete current FEX suite then passed449 controls with one APFS skip;
governance checked22 documents/172 local targets and the diff check passed.
These include source-only Git and explicitly labelled portable control scopes;
there is still no initializer/game qualification.


### October 3 Actual Compiler Refusals and Complete Source Regression

The first real supplemental FEX constructor passed native configure/build/
fixture and ARM64EC configuration, then failed compilation because Dispatcher.h
used Retirement without including its declaration. Its immutable failed receipt
is `9826f46195f6a907813411227d934652a10e843594f25ab14eb48caa498c4474`.
The new layer14 adds only the required conditional PearFEXRetirement.h include;
the first13 strict layers and all closed eligibility gates remain unchanged.

Two source-preparation attempts refused malformed newly written metadata before
creating any output: a required provenance field was absent, then a final source
row used postimage rather than inventory field names. Both preparation failures
are retained. A new regression replays the entire actual selected baseline and
complete graph when available, with an explicit unavailable skip otherwise.
It detected the second defect before any compiler or initializer was called.

The corrected source5 projection passed28 real Git check/apply commands and an
independent final-byte check:6963 files /40,437,680 bytes,36 affected source paths
and12 additions. The final manifest is
`abd8987ac5027540dcdc4c04059f9394b248224deb61abc89d6318d310081495`,
the graph is `6fe637dcd7f952836bbb3653b128f2016c8df26c942fc3a30b4440cd1c1cdcf1`,
and actual source control is
`d0a3279c5a840e112552230ad445fd3ebe51eb77b172051d42e5bdf80ec4a36d`.
The complete FEX suite passed450 controls with one APFS case-collision skip.

The second actual constructor again passed the native operations and ARM64EC
configuration, then refused a missing UniqueSpinMutex template parameter in
the selected unaligned-handler source. Failed receipt:
`bc12916f8ce2a3e9110355428a2413ab8788922e5a11db4da9be3b9ca471875b`.
Both original compiler logs and failed source/objects remain; neither is a
successful full module build, load, initialization or guest qualification.

Inspection of that actual RelWithDebInfo build also confirmed
ENABLE_ASSERTIONS=OFF. Pinned LogManager.h therefore evaluates
LOGMAN_THROW_A_FMT predicates without enforcing refusal. Pear's admission and
lifetime predicates cannot depend on this optional upstream assertion policy.
A separate always-on, no-exception Pear guard derivative must be independently
reviewed before any FEX initialization. Original upstream assertions, security
permissions and historical source layers remain unchanged. Whole metadata,
actual source lifetime/entry/Core, complete compiler/link and empty initialization
gates remain open; Stage3 remains incomplete.


### October 3 Targeted Compiler Repair and Diagnostic Prefix Deduplication

Layer15 supplies the actual uint32_t UniqueSpinMutex specialization required
by std::optional, matching the selected backend's uint32_t SpinLockFutex.
Every prior layer remains unchanged and every eligibility flag remains false.
The entire actual source6 projection passed30 Git check/apply commands:6963
files /40,437,690 bytes, with manifest
`149fd85469e4c71d9c6fdc282c49552326027cce2b04cb53d368a26a1239750d`.
The complete current FEX suite passed450 controls with one APFS skip.

A separate actual one-object diagnostic reuses the retained failed compiler's
exact target/options/generated headers, changes only its owned output and
fresh complete source15 paths, and compiles the genuine Arm64.cpp translation
unit. It passed with exit0 in2.989s. All original/current source, generated
prerequisites and compiler bytes stayed unchanged. Control SHA-256:
`8d6ee4f684693932b066d6be7e339b065c43e0f3cdd18475f3703f9d1a2807ee`.
This repairs the observed type compilation error; it is neither full FEX
construction/link proof, a rewritten old failed build, module load nor init.
Always-on source safety guards, lifetime/sealed entry/Core integration and
complete metadata/initializer admission remain required.

Independent current Wine build8 source/tool/output replay passed without
execution. A separate duplicate audit then compared old owned finite diagnostic
prefixes2/3 to the retained prefix4 and preserved every differing file.
Root independently rehashed both copies and checked identities at the deletion
barrier before removing only1336 identical generated system32/syswow64 DLL/EXE
copies, totaling2,021,785,600 logical bytes. Two unique system payloads remain.
Registry, user directories, credentials, saves, Steam prefixes, symlinks, current
prefix4,91 control/log/producer files and all other files are excluded.
Observed volume free space increased2,023,305,216 bytes (about1.88GiB);
APFS physical-reclaim measurement remains unknown. Completed receipt:
`125bae746b97f9e0a7b757864f39245a5c739cf9a115aad7e57cb6f7806061fa`.
Historical complete-prefix replay requires exact donor rehydration. Initial
read-only audit preparation refused access-time tuple comparison, then an absent
optional syswow64 directory; no files were removed in those failed attempts.
This cleanup does not change the current native results or qualify Stage3.


### October 3 Reviewed Source Lifetime, Release Guards and Source Deduplication

Reviewed layers16/17 bind the actual source Context/Thread lifetime, sealed entry
and cleanup participants and enforce mandatory Pear memory predicates when the
selected Release build disables upstream assertions. Unconditional failure uses
the pinned source's no-exception LogMan::Throw::MFmt; no global assertion policy
or original upstream assertion is changed. Failed cleanup retains its source
tombstone/dependencies. These remain source candidates: fatal behavior, complete
compiler/link closure, actual lifetime, metadata and initialization qualification
are unperformed. No guest, full module initialization or engine support is claimed.

The first15 layer descriptors and all historical artifacts are byte-identical.
Root independently verified the frozen packet and every current preimage before
applying its13 concrete source/checker/test files. Fresh source7 passed all34
actual Git check/apply commands and complete final-byte verification:6964 files /
40,485,352 bytes,39 affected paths and13 additions. Source manifest:
`c5b5f5f82596d2b63f73c407f5243265a84f4bd23c8a9b16f360c21eb3105e4d`;
graph `8e00c0a4d2e7af4b570420f7ad5c46f25a61b2973eb5c654c69ed60f3c593d4e`;
actual source control
`2b4c4866bc898c77d77f97a4d4315e59f2ab92e4de67635c93712c39299f7bb8`.
The complete current FEX suite passed450 controls with one APFS skip.

Root separately compared retained build8 source against obsolete build2–6,
after an independent literal-byte/type/mode/hash audit. Rechecking both identities
at the deletion barrier removed62,346 exact regular source copies totaling
2,003,003,364 logical bytes. All19 differing old files,6885 directories, objects,
inputs,39 selected controls, producers and error/log receipts remain. Current
build8 complete source/tool/output replay passed before and after cleanup.
Completed cleanup receipt:
`f3370aaa6b4ee813ba6b8fedaf8c8c2d09e83ba7e689134c4d033e5ba553e2c1`.
Observed volume free space increased2,183,397,376 bytes (about2.03GiB); physical
APFS reclamation is not measured. Historical complete source replay requires
exact donor rehydration. Current admission dependencies and unique evidence
remain protected. Source snapshots and local hash receipts are not uploaded
as proprietary/private binary evidence. Stage3 remains in progress.


### October 3 Checked Deletion Source and Actual Compilation Refusal

Reviewed layer18 preserves the old void/nonowner APIs and adds typed actual
destructor/deallocation observations. Destroyed is recorded only after the
genuine destructor returns; Freed means only that the validated allocator's
deallocation call returned, never physical OS reclamation. Consumed unique
ownership is not retried after a destroyed-but-not-erased identity. Unknown
cleanup retains its source tombstone/dependencies. The independent source review
passed29 portable controls; it did not establish compiler or runtime acceptance.

Fresh source8 passed36 actual Git check/apply commands:6964 files /40,487,535
bytes,39 affected paths and13 additions. Manifest:
`914d8b5fe92cc44fc0caad6537ae0ac9d56888e23a6d3b5342b3c866a48a637d`;
graph `eb5c0003a31c4131ca6dbcae0fa225341d0cb8266c9fe39d2684edab3ac05056`;
actual source control
`e996ca09e8b43599bfe2cfd889f7bcfed3f760068d3370312c1ee1070530a5c1`.
The complete current FEX suite passed450 controls with one APFS skip.

The third actual full constructor passed native configure/build/fixture and
ARM64EC configuration, then failed Context.cpp compilation: the checked base
Context method calls private SourceLifecycle methods, but existing friendship
belongs to the derived ContextImpl and the deleter. Failed receipt:
`c0150cb790a1be26ddd25ee051d7cca2c0e94352ba2f8bdbfd87688d9f24aa28`.
The five original compiler errors, source, objects and observations remain.
No successful full module/link, load, initializer or allocator execution is
inferred. The repair must retain private lifecycle authority and be independently
reviewed, then pass the exact failed translation unit before any whole-build
repetition. Current data-only sizeof and aggregate budget checks remain pending.
All initialization/guest/game/distribution gates remain false.


### October 3 Context Access Repair and Actual Data-only Layouts

The independently reviewed layer19 keeps the existing private SourceLifecycle
authority and effectful deletion body: the checked base method delegates to a
private derived helper, with friendship for that exact method only. No object
data layout, wire, whole-base friendship or nonowner behavior changes. The
actual failed Context.cpp translation unit compiled successfully after the
repair, exit0 in2176ms; diagnostic control:
`dbe921fe2174685ec9fffbc9ead5672d5a4ac461405ac86b6b9901051298dbc4`.
This does not replace the immutable failed full-module receipt or qualify
linking/loading/initialization.

Before promoting layer19, root completed all nine data-only source18/Wine8
layout compilations and genuine prerequisite/source/tool/input replay before
and after. All nine commands exited0, emitted dependencies were closed and
constant tables were extracted from object bytes without linking/loading.
Control: `b53bbc53e80117b8828448f3daae98f5553b44a92de139e0481459609b213fa6`.
The corrected driver reused8373 already prepared original/prepared byte/mode
pairs. The prior driver failed JSON serialization before any compiler, and
incorrectly exited0 with passed=false; that original control/producer remains
untouched and is not passing evidence. A missing standard-library import was
also corrected before the actual nine-command dispatch.

A sizeof subtotal is not the complete256KiB added-metadata gate. One process
owner, each PE module's separate static pools, allocator/control-block storage,
heap/stack transient peaks, alignment and simultaneous lifetimes still require
source-bound counting. Original-context payload is distinct from added owner
metadata; count rows must not be summed as bytes. No source initializer, owner
call or object loading was performed by this layout probe.

Root verified all10 proposed file preimages and55 retained publication files
before promotion. Fresh source9 then passed38 actual Git check/apply commands:
6964 files /40,488,277 bytes,39 affected paths and13 additions. Graph:
`38bac0349a77b6e5cd59f79852426dcc4bac8ca6c6fe6922cdc3be69c012bf2a`;
manifest `e0fbe556fa5c9f8ddf8734286ba6b80a6f2fe0b243b9eeb3b8fd9c1a95992725`;
source control
`b1d3522358dd748818b4db51d911bb4b295d72bccbd94e5d39d5770cbfbf33ee`.
All450 current FEX tests passed with one APFS skip. The fresh full module
constructor is in progress; metadata/lifetime/initialization/guest/game and
distribution remain unqualified. No prior full-build result is relabelled.


### October 3 Complete Compiler Commands and Strict Artifact Refusal

The fourth actual full constructor completed all nine native configure/build/
fixture, ARM64EC configure/build/inspect and ordinary ARM64 configure/build/
inspect commands with exit0. Its final artifact reader then refused
`fex_memory_owner_macro`; failed control:
`9bcfe26df0d77e9b7753246ff0419c27258b0af3349a26feae399d2128edbeca`.
This remains a failed full build record, not a qualified successful module.
All original commands, raw diagnostics, objects, modules and source are kept.

An initial source/database review found107 of108 C++ units per PE target carry
the required owner definition. The sole absent unit is the unchanged upstream
AllocatorHooks.cpp, compiled by a separate allocator target. A narrow reviewed
source/target/dependency exception may be appropriate; a broad weakened owner
gate or build success assumption is not. Reuse the exact completed outputs
for pure assessment once that contract is proven instead of immediately
repeating the same nine compilation commands. Current lifetime, aggregate
metadata, initializer and runtime qualification remain open.


### October 3 Separate Immutable Artifact Assessment and Storage Retirement

The source19 allocator exception admits only the exact unchanged upstream
AllocatorHooks.cpp JemallocLibs translation unit, its selected target, allocator
configuration and three original source dependencies. All 107 owner-dependent
C++ units per PE target retain the original owner gates. The lifecycle symbol
reader requires the exact SourceLifecycle::AttachAllocatedThread signature
and Common archive body; a legacy alias or generated exit thunk cannot replace
it. No source, compiler configuration, wire or security permission was changed
by these two reader corrections.

A separate offline assessor admits only the reviewed reader transition
59f5a7de to3cd37aa1 while retaining every other historical producer and copied
input. It replays actual Stage2, Wine8, source19, command/log/tool/dependency
and complete raw payload closure before and after inspection. It writes no
historical build.json and invokes no compiler, module or new native process.
The original modules4 constructor remains failed with primary owner-macro
refusal and digest9bcfe26d; nine original successful command receipts are
evidence of those original operations only.

The first separate assessment was created, but its verification refused
json_structure_limit: its complete7,849,168-byte record has326,542 JSON nodes
including keys, exceeding the inherited250,000 default. Original assessment1
and its producer are preserved. A narrow assessor-only repair uses matching
8MiB/500,000-node limits for its successful record, with complete exact-byte
preflight before exclusive creation. Historical reader/failure budgets and
depth, duplicate-key, numeric, scalar, path and file-identity restrictions stay
unchanged. Independent68 controls passed without actual process routes.

Root passed551 current FEX tests with one explicit APFS fixture skip. A fresh
assessment2 under the new assessor producer was then created and independently
verified with actual exit0 in each command. Its identity is
`d65f87085008c990def4b332e138aae7c2e55625f4f9a51bfc4f782832a1e8e8`.
It confirms all32 retained artifacts,211 copied current inputs and nine
original command/log records while preserving the unchanged original failed
build. Its own passed status qualifies only this bounded offline inspection.
Source initialization, aggregate metadata, owner/active-thread bridge, atomic
resume, delivered exceptions, paired EC identity, guest/game/distribution and
Stage3 completion remain unperformed/unqualified. Future source/checker
changes invalidate current replay until exact checkpoint rehydration; they
never retrospectively change this observation or admit a new build.

Requester-authorized exact duplicate retirement preserved active donors,
unique failures, private state and controls. Source-copy plan612f6437 removed
286,307 identical leaves/9,189,166,762 logical bytes while retaining350 unique
leaves and928 controls. Tools/reconstruction plan2a16806b removed104,443
identical leaves/3,801,009,435 logical bytes, retaining31,101 unique leaves
and411 controls. Current-reference audits found no selected old-root use.
Observed volume increases were1,296,900,096 and2,599,272,448 bytes; these are
not independent APFS physical-reclamation measurements.

A further exact ledger109effcd selected3,432 regular system PE DLL/EXE copies
from six closed historical API/ABI fixture prefixes (5,490,737,152 logical
bytes), with1,716 original signed-resource donors retained. Root applied and
verified the retirement; all other prefix objects, case/log/producer records,
registry/user/save/credential/symlink/profile/signing material remain intact.
Its observed free-space delta was-6,111,232 bytes, so no physical increase is
claimed. Historical prefix/payload replay requires exact donor rehydration.
Lossless bounded archival of inactive intermediate objects is under review;
no unique intermediate payload is discarded without a verified recoverable
copy. Only sanitized results/source are published. Stage3 remains in progress.

### October 3 Final Source Closure and Bounded Successful Records

The independently reviewed 22-path update preserves all nineteen predecessor
layers and appends checked Context allocation, checked finite environment
preparation, checked selected factories and the private finite empty fixture.
Upstream C++ and assembly, ordinary target flags and normal initialization
paths remain preserved. The fixture target is OFF; all twelve proof constants
are literally false. No source object has been constructed or initialized.

The outer publication patch passed the private pure parser but its actual Git
check refused a new-file header before any shared mutation. The original
packet and failed wrapper remain preserved. Root rechecked every preimage and
applied the exact frozen postimages directly. This publication check does not
qualify the separate ordered source derivatives.

A fresh source10 projection then completed all 46 actual Git check/apply
operations for the 23 ordered derivatives with exit 0. Its control digest is
`cc991d517d694874f43b77c13742a36cc9fa601360009d8ba8b080cf241eb1d0`.
The final inventory contains 6,973 files and 40,537,903 bytes, with digest
`16f1453f47d293e02c84bd2199810a02e06f597faaed08c03fafaa80cb897383`.
The original selected baseline was rechecked unchanged. Root ran 578 FEX
tests successfully, with one explicit APFS fixture skip.

Only complete successful module build records now use the matching
8 MiB/500,000-node decoder and exact-byte writer preflight. Generic and failed
records retain 250,000 nodes and all existing strict JSON/file controls. This
prevents the separately reproduced 250,351-node successful-record shape from
being written and then refused solely by the old reader limit. It is a bounded
serialization correction, not a completed source23 module build.

The source19 assessment2 observation and its producer checkpoint were
published first and remain immutable. Its current replay is now unavailable
until the exact source19 namespace is rehydrated. It cannot supply a source23
build, initialization, guest or game result.

A reviewed three-unit compile-only measurement is being prepared against the
actual source10 receipt. It measures 51 constants from real fixture, wrapper
and selected libc++ control-block types. Constant extraction, ordinary object
code emission, linking, loading and initialization are distinct observations.
Allocator rounding, full static alignment, phase-bound stack/retention peaks
and the complete 256 KiB aggregate remain unresolved. Stage 3 remains in
progress; no initialization proof flag is opened by these source or test results.

### October 3 Verified Archival and Exact Install Retirement

The storage inventory observed 178.078 GiB across the recorded project/worktree
and temporary roots. This is a historical footprint, not a required working-set
budget or independently measured APFS usage. A later folder inventory observed
156.304 GiB, a 21.774 GiB lower aggregate during concurrent construction.
Folder sums can double-count shared APFS extents; this is not measured unique
physical reclamation or a permanent working-set reduction. Nine major protected roots
totaled 14.024 GiB; that partial grouping is not a complete minimum and does not
authorize removal of other current inputs, controls or unique evidence.

Root completed 26 archival batches: archive, verify, prune and retained-verify
all returned zero (104 actions). The 24,716 inactive leaves represented
5,136,652,549 logical bytes and 24,366 distinct payloads; verified compressed
payloads occupy 1,503,904,568 bytes. Aggregate identity:
`7489e2b1a9825385056c602d1f83c0b358d54d60a23e5e0724d3ecf9349a1517`.
Historical replay requires exact rehydration; full native metadata restoration
and renewed historical qualification are not established by archive verification.

A separate paired-install retirement removed 42,955 exact same-build copies
(19,746,788,016 logical bytes), preserving 688 unique/signing-altered leaves
and every original signed donor. Completed receipt:
`5e22e1142ca6dd8744b24b42755cdcffc92b93742410650894d129493f8b7a4c`.
Volume free space changed from 11,229,503,488 to 12,785,053,696 bytes. The
1,555,550,208-byte observed increase includes concurrent builder activity and
is not attributable APFS reclamation or a continuing admission guarantee.

Source retirement8 separately removed 20,864 exact leaves/120,788,424 logical
bytes while preserving 27 unique leaves, current source9/source10 and controls.
Its completed receipt is
`36a6c974739f7cdd1eb82f96fca7d8728766ec7049c1cc52231a8f8c868316e8`;
`1ab7611070fcdeb9e36cb5dd357ba81bb9cef871d2051b8446484ea1d07f2891`
identifies its ledger. The stage6 research candidate remains frozen and unapplied.
Fresh per-operation storage checks and serialized compilation remain required.
Source23's three measurement compiles await the shared lock. Stage3 and all
initialization, complete metadata, runtime and game gates remain open.

### October 3 Genuine Layout Probe and Reviewed Include Ordering

Root executed the independently reviewed compile-only supervisor against the
current Source23 projection and genuine ordinary ARM64 tool/header closure.
The first layout unit failed with actual compiler exit 1; the two later units
were explicitly unperformed and no layout table was produced. The original
control is retained at identity
`8909ed109170646117b4d518df24550a1f8f0d38063868aae34b7b8423ea8422`.
All seven post-operation input/source/producer/identity gates passed. No object
was linked or loaded and no FEX instance or owner operation was performed.

The real SDK diagnostics show a version macro redefinition followed by an
unavailable directory-notification type. The fixture included CheckedCRT's
Windows headers before the existing upstream AllocatorHooks version setting;
the measurement also included sysinfoapi before that fixture. A separately
reviewed Source24 proposal moves those existing includes into the required
order without changing SDK headers, platform flags, ABI, fixture body or any
of the 12 false permission/lifetime/budget proof flags. Its 23 guarded pure
controls passed independently. The proposal has not been promoted: fresh
24-layer Git projection and genuine current layout compilation remain pending.
Original Source23 inputs, compiler failure and preceding layers stay intact.
The complete 256 KiB metadata accounting, retention/lifetime bounds, source
build and admitted empty initialization remain unqualified. Stage3 continues.

### Latest User-Requested Storage Inventory

Fresh folder allocation observations totaled 156.882 GiB: primary workspace
4.908 GiB, prior Wine worktree 133.676 GiB, prior source worktree 0.727 GiB,
current FEX worktree 9.292 GiB, current graphics worktree 6.658 GiB and
Pear-named temporary entries 1.622 GiB. Inventory identity:
`94e59a1cbe1bc1702cbc7ce37a4a5aa45479ddc266a1e0752432e217794ee012`.
This observed retention footprint is not a required minimum. APFS shared
extents can be counted repeatedly; unique physical allocation was not measured.
Compared with the earlier 178.078 GiB inventory the folder aggregate is
21.196 GiB lower, including intervening construction. Another builder is active;
volume free-space movement cannot be attributed entirely to Pear. Whole-build
admission floors of 6 GiB for graphics and 8 GiB for FEX are operation policies,
not a claim that the whole project needs only those amounts. Complete minimum
storage remains unmeasured; old repeated build retention is the main reduction
opportunity. Current donors, unique failures and private user state are retained.

### Requester-Approved Cleanup Before Further Development

Root retired 37,768 frozen exact source/tool/install/object duplicates from the
inactive Wine Stage6 research workspace (1,886,081,409 logical bytes). Every
selected leaf and retained donor was rehashed under the shared lock; current
references and original controls were checked again after retirement. Receipt:
`3e09fc0a8305f709bfaab64d6dd627fa53eb0c87322ed6d4560f10b89f30c4f4`.
The journal and unchanged retained donors permit exact byte/mode rehydration;
unique files, original failure records and current build inputs remain present.

Five inactive synthetic Wine run roots contained 19 original fixture prefixes.
Root archived only known Wine builtin ARM64 PE system files, verifying case and
prefix provenance, file identity, ordinary PE format and current non-use. No
registry, account, game, save or user-directory payload was selected. Exact
xattrs and observed ACL absence were recorded with original metadata. Of
12,996 retired copies (19,609,747,456 logical bytes), 3,364 distinct payloads
occupy 852,661,060 compressed bytes. Every gzip payload was fully decoded and
hashed before unlink, and the complete retained set was verified again after.
The restore index and operation producers remain in the private archive.
Receipt: `361aa52843975250ff9c182341144f8e167524998ef18c3d3627286447bff4c5`.
Restore index: `d4e5259ed1b393258e52db9f4dd42708bd9c47c731c2cac89fe2976ee95955e2`.
Historical execution requires exact restoration and new admission; original
inode/ctime/birthtime identities and execution qualification are not recreated.

The combined folder inventory fell from 156.882 to 137.674 GiB, including new
archives and the new source projection; project/worktree roots alone total
136.041 GiB and Pear temporary entries 1.633 GiB. Inventory identity:
`a78a893d6f01ce9e322b983e86f2bbb000fde47bec623397c314d72b859de1f1`.
Observed volume free space rose from approximately 2.5 to 10.4 GiB. APFS shared
extents and another active builder prevent attributing that whole change to
Pear. These are measured observations, not a complete minimum working-set claim.

### Source24 Projection and Genuine Three-Unit Layout Measurement

The genuine fixture now includes its existing AllocatorHooks header before
CheckedCRT/Windows headers. Layer24 preserves all preceding layer identities,
target flags, fixture body and twelve false initialization proof constants.
The initial root CLI call rejected relative inputs before output creation;
the corrected absolute-path call applied and checked all 24 patches in 48
successful Git operations. All 6,973 files/40,537,903 bytes matched the reviewed
source inventory; the baseline remained unchanged. Projection receipt:
`7cdd07967988ff34d12862cee58e33bf4a3e699f910b5fc06eb856b1aa4debbf`.
Materialized-source identity:
`9833aa29c2bc04778f195ffdffd2ab95038be4270df5f442c8acd45c04670b83`.

Full regression initially exposed four errors because the proposed checker
retained its old 46-command predicate. Root corrected it to the exact required
48 operations and added refusal of a missing final check/apply pair. The final
579-test run passed with one explicit platform-condition skip. Current checker:
`47ce403764f4a493ff62d434a69faff4a58ae67d80843afc775f31ef7593001b`.
Earlier failed tests and recipe preparation remain preserved. The private
compile recipe was rebound to this reader and actual current fixture paths;
no historical success record or compiler result was relabeled.

Root executed three genuine ordinary ARM64 compile-only units with the selected
LLVM-MinGW/SDK and original no-exceptions policy. All three returned 0 with empty
stdout/stderr; their 1,074/1,121/1,112 actual dependency entries were inside the
verified source/header closure. Fifty-one data constants were extracted from
the resulting ARM64 COFF objects. All seven independent post-operation gates
passed. No object was linked or loaded; no FEX initialization or owner call ran.
Final control: `8a3d70034d4b5f62c6fdf55ac5b91de5e66735238de1fa610da94334b6d6eef6`.
Recipe: `fa594e46faad817f3f6231d00800e7af2969923d4eccd131e3de89a8f09f14c1`.

| Measured type | Owner enabled, bytes | Baseline, bytes |
|---|---:|---:|
| Combined allocate_shared control block | 216 | 56 |
| CodeBuffer (already inside the combined block) | 200 | 40 |
| GuestToHostMap | 176 | 176 |
| Dispatcher | 728 | 544 |
| Arm64JITCore | 808 | 448 |
| ContextImpl | 1,904 | 1,328 |
| InternalThreadState (4,096-byte alignment) | 12,288 | 12,288 |
| CpuStateFrame (already inside thread storage) | 3,840 | 3,840 |

The finite fixture's State/Storage is 4,464 bytes and already contains the
4,152-byte CRTPlan and 268-byte Report; these must not be counted twice. Callback
inspection scratch is 2,048 bytes. These are actual layout observations, not
complete allocation costs or runtime RSS. The 256 KiB added-metadata gate still
needs allocation rounding, concurrent/retained object counts, static placement,
stack peaks and Wine/PMR provider attribution. All initialization, translated
execution, complete metadata and Stage3 completion claims remain false.


### October 4 Source-Bound Allocation Classes and PMR Layouts

The requester explicitly continued the existing Stage 3 work. This checkpoint
uses the approved tests and internal observation/plan locations; it introduces
no product document, runtime patch, permission or budget change. The original
compile-only PMR fixture is retained at `tests/fex/pmr_layout.cpp`; allowlisted
results are in `mydocs/working/task_m1_5_stage3_layout_observations.json`.

Root reused the exact Source24 compiler, closed source/header envelope and
bounded supervisor. Both new ordinary ARM64 data-only compiles exited 0; all
1,116/1,094 dependencies were admitted and the three independent post-checks
passed. The objects were never linked or loaded. Control identity:
`02332fa2f6b2293f134a110c7f6d73e336a9d898a6bce5a31a3842e4228d3f1f`.

The actual owner/baseline map objects are both 32 bytes, PMR resource objects
both 64 bytes and polymorphic allocators both 8 bytes. The selected libc++ map
node is 64 versus 56 bytes, with mapped values 16 versus 8. Its private node alias
was reconciled with the pinned map/__tree headers. The initial empty map takes
one source-calculated 4,096-byte PMR buffer on either route; this is not an
observed commit/RSS result. No linked node is inserted by the finite empty
fixture, and later population/clear growth needs its own accounting.

The Source24 six-allocation comparison uses the unchanged upstream rpmalloc
classes and real measured alignments. For one instance of each selected object,
class-block deltas are 160 bytes for the combined CodeBuffer/control block,
192 for Dispatcher, 368 for Arm64JITCore, 512 for ContextImpl, and 0 for
GuestToHostMap/InternalThreadState: 1,232 bytes total. The bit-index classifier
agreed with a separate linear class-table oracle for 131,072 bounded requests.
This conditional subtotal excludes embedded aliases and cannot qualify total
metadata, multiplicity, backing-page deltas or retention. The fixture's
Storage/Invoked/Retained member sum is 4,476 bytes before linked placement gaps.

Source inspection found another lifetime obligation: the selected upstream
named_monotonic_page_buffer_resource exposes release(), but defines no
destructor invoking it, and the selected GuestToHostMap has no call to that
release(). The Windows VirtualFree wrapper also discards its native return
value. This is a source finding, not an observed runtime leak, and inherited
allocator reuse cannot establish physical release. Exact selected source
identities and the current false qualification flags are preserved. Linked
static/provider proof, complete concurrent/retained counts, stack peaks and
Wine view/vprot attribution still block the 262,144-byte gate. Stage 3 continues.

### October 4 PMR Lifetime Correction Checkpoint

The requester continued toward Megabonk execution. Resume the approved Stage 3
lifetime work after preserving #7's independent diagnostic result. Reuse the
selected Source24 C++ resource implementation and its original hooks. First
isolate the exact named monotonic resource class in a small ARM64 host harness
with explicitly substituted allocation hooks and standard-list storage. Compare
its original destructor behavior with a narrow destructor/release correction;
measure outstanding provider allocations rather than infer release from sizeof.
Retain the upstream class bytes and hashes in private inputs. This finite host
control is not the Windows provider, full FEX initialization, JIT or a 256 KiB
metadata qualification. No executable memory, new signing or OS setting is used.

If the control confirms retention, preserve an unapplied corrective candidate
patch in the existing runtime/fex/patches/memory area and the original fixture
in tests/fex. Review GuestToHostMap's clear/destruction ordering so node lifetime
ends before resource release and queued link tickets remain copied beforehand.
Do not silently rebind Source24 or its historical compile receipts. Integrating
a successor source graph and verifying actual Wine allocation/free errors remain
required before this candidate can qualify the real FEX path. Record sanitized
results in the existing Stage 3 observation sidecar. No product document or
new official-document location is introduced.

The original resource class was extracted byte-for-byte into an ordinary ARM64
macOS harness with substituted allocation hooks and list storage. After one
scope it retained one provider buffer; after 32 cycles it retained 96. The
candidate retained zero in both cases, with a three-buffer peak. The harness
explicitly freed original retained buffers after observation; this is not a
production fix or a Wine physical-memory measurement. Repeated release,
aligned allocation, allocation after release and noncopyable candidate resource
controls passed. Both variants requested 101 buffers in total. All original
inputs stayed unchanged.

Preserved failed attempts: the first compile omitted the explicit SDK and could
not find libc++ headers; the second ran the host controls but its patch check
used an enclosing Git worktree and failed byte replay. Its provisional AlignUp
substitute also differed from the real non-power-of-two algorithm. The third
attempt selected the SDK, used the actual arithmetic and bounded Git discovery;
source-byte and complete three-file patch replay passed. The committed host
runner subsequently reproduced the same result independently in fresh output.

The unapplied candidate adds resource destruction/release, forbids copying or
moving the owning resource, resets its buffer cursor, and destroys the lookup
map before releasing its storage on clear/destruction. Queued link tickets are
copied before map retirement. Two actual ordinary ARM64 Windows compile-only
units (LookupCache and PMR layout) passed with the original no-exceptions policy;
1,117/1,116 dependencies and all three post-checks passed. Neither object was
linked or loaded. This candidate is intentionally outside the active source
graph and does not rebind historical Source24 receipts. Actual provider error
handling, lookup execution, complete metadata and initialization are still open.

Reproduce the finite host control from the exact materialized Source24 input:

```sh
python3 -B tests/fex/run_pmr_lifetime.py --source <source24-tree> --output <fresh-output>
```

The runner refuses changed source preimages and existing output. Its allocation
hooks are explicitly substitutes. The existing Stage 3 observation sidecar
records patch, fixture, producer, input and receipt hashes. No runtime permission,
JIT geometry, product requirement, source cache or completed stage was changed.

Verification after adding the candidate and reproducer: the existing FEX suite
ran 579 tests with no failures/errors and one explicit conditional skip.
Governance passed 22 documents/172 targets; whitespace checks passed. New #5
control outputs total less than 5 MiB, with no whole-runtime rebuild or deletion.
The candidate remains unapplied pending source-graph and real-provider work;
none of these checks qualifies translated execution or closes Stage 3.

### October 4 Source25 PMR Integration and Provider Verification

The requester explicitly continued after review of the PMR candidate. Integrate
its exact three-file correction as layer 25 of the existing source graph,
retaining layers 1-24 and their historical evidence. Preserve the predecessor
reader/manifests privately, pin the successor graph/complete source identity,
and extend exact command/count refusal controls to the new layer. Materialize
from the unchanged Stage 2 baseline into a fresh output and independently replay
all patches and final bytes. Recompile affected source against that actual tree.
The existing candidate file remains an immutable historical comparison input.

Then inspect and exercise the actual Wine ordinary allocation/free provider in
a small original ARM64 PE fixture, reusing an already authorized development
runtime and owned supervisor. This is distinct from complete FEX initialization
and the final metadata gate. Preserve actual VirtualFree error and VirtualQuery
results; do not infer successful physical reclamation from a void wrapper or
from RSS. No JIT permission, geometry, exception policy or global setting change.
Use fresh bounded outputs, the shared lock, an 8 GiB free-space reserve, and no
whole Wine rebuild without a concrete need. Record results in existing Stage 3
plan/observation locations; no product-documentation location changes.

Source25 integration completed as a source/compile checkpoint: all 25 unchanged
predecessor-plus-PMR layers passed 50 real Git check/apply operations in a fresh
projection. Independent replay matched all 6,973 files / 40,538,729 bytes and
preserved the Stage 2 baseline. Source24's graph/reader snapshot and all old
receipts remain intact. The active graph and reader now require the exact new
identity, 53 changed paths, 22 new files and all 50 operations. Initial portable
controls exposed four errors because two synthetic receipt loops still emitted
48 commands; their corrected ranges passed, including missing-final-pair refusal.
The final full FEX suite ran 579 tests with no failures/errors and one skip.

Two actual ordinary ARM64 Windows objects were compiled from the new complete
source tree, with 1,117/1,116 closed dependencies and all post-checks passing.
Read-only COFF extraction confirms the resource remains 64 bytes and the selected
map/node/allocator layouts remain unchanged. This is neither linking nor FEX
initialization, and it does not complete the 256 KiB metadata accounting.

A single new original ordinary ARM64 PE provider diagnostic ran 32 cycles under
the existing authorized #5 Wine runtime. It alternated 4 KiB/16 KiB RW regions,
verified committed state and byte access, submitted an invalid nonzero-size
MEM_RELEASE request, observed error 87 and the still-intact allocation, then
released with size zero and observed MEM_FREE. All cycles, normal guest/process
exit, owned cleanup and sentinel survival passed. Source-registered processes
reported ARM64, no translation and 4 KiB user pages. Bundle bytes and current
signature/identity/profile checks passed before/after; no new signing or full
provenance replay was performed. The original owner verifier correctly refused
this different fixture (`memory_wine_case_failed`); no qualifying owner/run
receipt was produced. Raw stderr contained only the three known fresh-prefix
working-directory fallback warnings. Native code, loader policy and JIT geometry
were unchanged. API free state is not a physical RSS-reclamation measurement.

This closes the narrow source integration and provider-behavior questions.
Actual Source25 GuestToHostMap execution and failure propagation through FEX's
void VirtualFree wrapper remain unqualified. Do not treat successful provider
calls as a fix for ignored provider errors. Complete aggregate metadata, retained
failure state and genuine empty FEX initialization remain the next Stage 3 work;
#7's separate failure is unchanged. The observation sidecar binds all results.

### October 4 Checked Windows Provider Release

The requester continued Stage 3 and explicitly limited testing to checks needed
for the execution goal. Reuse the selected FEX Windows allocation wrapper and
its existing unconditional, non-returning LogMan::Throw::MFmt policy. In Pear's
owner profile, capture GetLastError immediately when MEM_RELEASE fails and
report its original unsigned Win32 value, pointer and requested size before
termination. Do not introduce a new bridge error domain, retry, recoverable
return, global failure registry or allocation metadata. The resource release
loop must not clear its records or proceed after that failure. This preserves
normal fatal-error policy rather than implementing recoverable cleanup.

Integrate one ordered successor layer while preserving Source25. Validate the
changed wrapper's success/refusal behavior with substituted provider and fatal
sink (normal fixture exit, no deliberate native crash), and compile the actual
changed source for ordinary ARM64 Windows and ARM64EC. Run only affected source
graph/replay controls. Existing Wine provider evidence does not need repetition
for unchanged Wine code. No full runtime rebuild or game run is implied.
Results remain in the existing plan, Stage 3 observation and daily-board paths;
no product documentation location changes. #7 is owned by its separate session.

Source26 now checks the Windows wrapper in the Pear owner profile. It captures
the unsigned DWORD immediately after a failed API call and invokes the existing
unconditional non-returning logger before PMR release can clear its records.
Successful calls retain normal behavior. This is fatal failure preservation,
not recoverable cleanup or a new quarantine registry; the OS ultimately owns
process teardown. No new persistent metadata or bridge-domain value was added.
Upstream non-owner Windows and POSIX branches remain unchanged. Call-site review
covered PMR, pooled allocators, lookup and guarded bitmap/cache teardown; no
new automatic retry or null-allocation success was introduced.

The fresh source projection passed all 52 check/apply commands for 6,973 files
and 40,539,244 bytes, followed by independent replay. The initial invocation
used relative input arguments and was refused before output creation; the
correct absolute invocation is retained. Source25 and its checker/graph snapshot
are preserved. Actual LookupCache.cpp compiles passed for ARM64 Windows and
ARM64EC with 1,117/1,118 closed dependencies, empty stderr and unchanged input,
tool and reference checks. Neither object was linked or loaded.

Four finite host cases used the exact selected wrapper/resource fragments, the
selected fmt implementation and substituted provider/list/fatal sink. The old
Windows branch ignored error 87, made three release calls and retained one
buffer. The checked success case released all three buffers. Injected errors
87 and 0xffffffff stopped at the second call, preserved their unsigned value,
and kept the failed and not-yet-attempted buffers valid. The sink exited normally
without a native trap; this does not execute real Wine errors, the production
fatal trap or the complete GuestToHostMap. The existing unchanged Wine provider
result was reused rather than rerun.

Only the affected graph/publication and projection refusal suites ran: 40 tests,
zero failures/errors/skips. No full FEX suite or whole runtime rebuild was
performed. Actual map lifecycle, complete metadata accounting and genuine empty
initialization remain Stage 3 work. No translated guest/game claim or Stage 4
transition follows from this checkpoint.

```sh
python3 -B tests/fex/run_virtual_free_error.py --source <source26-tree> --output <fresh-output>
python3 -B -m unittest tests.fex.test_memory_fex_pair.CanonicalGraphControls tests.fex.test_memory_fex_pair.CurrentProjectionControlControls
```

### October 4 Actual GuestToHostMap Component Lifecycle

The requester continued the next Stage 3 work. Build a small ordinary ARM64
Windows fixture around the unchanged selected Source26 LookupCache.cpp and
allocator/logging sources, using real Windows VM and the selected rpmalloc
provider. Reuse the pinned compiler, matching fmt/rpmalloc implementation and
existing signed Wine runtime. The fixture uses ordinary MinGW CRT startup; it
does not substitute for the custom-CRT full-engine initialization gate.

Observe constructor, an empty-map ClearCache, population of 128 inert map
entries and destruction in two finite cycles. Record PMR buffer allocations
through the existing name callback and check real VirtualQuery states before
and after destruction. The JIT queue boundary explicitly refuses any call;
empty clearing and populated destruction must not invoke it. This tests no
real link retirement, code publication, metadata aggregate or translated guest.
Do not turn inert tickets into admitted executable links. Rebuild only required
component objects and libraries, then perform one admitted Wine diagnostic if
link/import inspection passes. Use the existing shared lock, owned supervisor,
original input/signature checks, a fresh prefix and at least 8 GiB free. Preserve
failure evidence, no retries for a passing result, and no whole runtime rebuild.
The approved existing Stage 3 plan/observation/board locations retain results.

The actual component diagnostic passed once in the existing signed Wine runtime.
Both cycles populated 128 entries in the selected GuestToHostMap. Each used two
observed PMR regions; VirtualQuery found committed read/write storage before
destruction and MEM_FREE with no AllocationBase afterward. The second cycle
also executed the real empty-map ClearCache path before population. No live
JIT link was minted, queued or retired. Pointer checks after destruction used
VirtualQuery only; no freed storage was dereferenced. This does not measure RSS
or rpmalloc pool retention, and does not qualify populated link invalidation.

The actual source26 LookupCache object was reused after byte verification. Ten
small units were compiled around it. Two linker attempts exposed missing
existing Config/SpinWaitLock/ForcedAssert and FileLoading definitions; the final
link added those real sources while reusing every successful object. No fake
configuration or failure implementation was substituted. The sole compilation
warning was the selected rpmalloc os_map_granularity variable set but unused;
other compilation/final link stderr was empty. The 4,501,504-byte result is
ordinary ARM64 PE with static C++/fmt/rpmalloc and Windows CRT/API imports.
Build input/dependency/tool checks passed. No whole FEX/Wine rebuild occurred.

Before/after bundle and current signing/profile checks passed. Both expected
cycle rows and terminal record arrived with loader exit zero, normal guest and
process exit events, complete owned cleanup and sentinel survival. Thirteen
registered processes reported ARM64/no translation/4 KiB user pages; all 14,353
native image observation rows were ARM64 (rows are not unique image counts).
The only stderr lines were three known fresh-prefix working-directory fallback
notices. This is a bounded component observation, not the complete runtime
observer gate. The original owner verifier intentionally retained
`memory_wine_case_failed` for this different fixture; no owner or full-engine
qualification receipt was created. Ordinary MinGW CRT startup remains distinct
from the full FEX custom-CRT/engine initializer.

No full regression suite or repeat Wine run was needed for this fixture-only
checkpoint. Preserve all build attempts, linked fixture, logs and receipts.
After successful review and owned-process cleanup, only the fresh synthetic
prefix was removed: 869 files, 1,148,252,160 allocated bytes. Exact prefix inode
and absence of referencing processes were checked; signed runtime, failed
records and #7 inputs were preserved. The removed prefix can be recreated, but
its reconstruction was not tested. Stage 3 remains incomplete: full-engine
lifetime integration, aggregate metadata accounting and genuine empty FEX
initialization are still required.

### October 5 Finite Initialization Accounting

The requester continued Stage 3 with necessary-only testing. Review the actual
Source26 one-shot fixture and construction/cleanup call graph before assigning
object multiplicities. Reuse prior class-size measurements where the defining
headers are byte-identical. Measure only the three actual PE static-storage
units needed to close the registry/pointer/guard omission. No native run,
whole-runtime rebuild, new product-document location or Stage transition is
needed for this checkpoint. Results stay in the existing observation sidecar
and this plan; the daily row moves to the October 5 board.

The checked finite path attempts at most one Context, Dispatcher, Thread,
shared CodeBuffer/control block, GuestToHostMap and Arm64JITCore. The fixture's
non-resetting one-shot CAS precedes construction. Each failure returns toward
cleanup; uncertain cleanup retains the same tree rather than authorizing a
second attempt. GetPearLatest runs once during thread creation, and the JIT
constructor receives that InitialBuffer by move instead of allocating another.
Context/manager/JIT shared references are aliases, not extra CodeBuffers. These
are conditional source bounds for the isolated one-shot path, not general
engine concurrency or game limits. No other allocation caller or guest/cache
growth may be admitted under this finite count.

The existing measured allocator-class deltas therefore contribute a conditional
1,232 bytes for those selected one-each objects. Defining Context, Dispatcher,
JIT, shared-buffer and CoreState headers match the retained measured source.
Allocator backing pages, unrelated upstream payload and temporary call frames
are separate terms; a block-size delta is not physical RSS or total allocation.
The completed PMR component diagnostic remains valid in its recorded scope.

Three actual ordinary ARM64 Windows compiles passed with 666/1,116/520 closed
dependencies and empty stderr. Before/after source, tools and references were
unchanged. Writable COFF sections are 20,042 bytes for the adapter, 16,480 for
links and 23,736 for retirement: 60,258 bytes per selected PE copy. The link
registry includes its eight-byte Address pointer and eight-byte initialization
guard; llvm-nm independently shows Storage beginning at offset 16. Earlier
16,464-byte Registry-only observations omitted those 16 bytes. The four emitted
input sections permit 28 bytes of alignment slack at their declared eight-byte
alignment, which is not a measurement of final linker/VM page placement.

No object was linked, loaded or run and no complete 256 KiB claim is made.
Remaining accounting concerns the final native/PE placement, matching Wine view
metadata, finite synchronous temporary peak and provider backing attribution.
The original initialization proof selection remains closed. These results
reduce the current one-shot accounting problem without imposing a general-game
allocation budget or weakening existing acceptance predicates.


### October 5 Local-only Construction and Initialization Admission Review

The requester explicitly asked to continue through Stage 3 without saving to
GitHub and to report the final outcome. All changes and evidence in this run
remain local. No push, Issue/PR write, merge, stage transition or completion
commit was performed. Existing plan, observation sidecar and daily-board
locations remain the record destinations; no product-document location changes.

Reuse the pinned FEX custom CRT, C++ engine and static dependencies, native Wine
owner, LLVM-MinGW toolchain and existing signed finite-fixture supervisor. The
new original `tests/fex/empty_process.cpp` uses a real ordinary ARM64 main-image
entry and custom-CRT initializer. It retains Wine's existing exact-main-image
caller restriction. It uses no stdio, heap or unimplemented GetStdHandle wrapper
to emit its fixed record. It does not authorize a general DLL caller, ARM64EC
initialization, translated instructions or a module ProcessInit path.

Four ordered source layers preserve every predecessor. Layer27 repairs the
pinned MinGW declaration's const mismatch for the read-only environment size
query. Layer28 fixes the checked CRT's actual Wine declaration selection,
const-preserving section lookup and unsigned processor-count comparison.
Layer29 keeps all twelve proof selections false while making the actual
initialization body visible to the compiler/linker. A previous successful link
had optimized that body away and therefore was insufficient closure evidence.
Layer30 adds a typed exact-callback replacement for InitBasicInfo: preserve the
NT query error, validate returned length/page/granularity/address observations,
and publish BasicInfo only on success. The original module callback remains
unchanged. This was necessary because its original void callback ignored the
provider error. No security permission, bridge ABI or owner capacity changed.

The complete Source28 native/ARM64EC/ARM64 module build and independent verifier
passed (nine commands, 32 artifacts). This is historical Source28 build evidence,
not a Source30 full-build claim. Its unchanged objects were reused for actual
closed-initializer DLL and main-image links; real Fixture/CheckedCRT objects were
compiled with the previously eliminated construction/cleanup body retained.
Source30 CheckedCRT and ordinary/EC WinAPI compiles then passed. The final link
replaced only the exact WinAPI member from a private archive copy. The archive
contains two different Alloc.cpp.obj members; their hashes identify the intended
one. Every other member was checked unchanged, and the original archive remains
intact. No unresolved-symbol or duplicate-definition bypass was used.

Source30 materialization and independent replay passed: 30 layers, 60 genuine
Git check/apply commands, 6,973 files, 40,541,641 bytes, 54 changed paths and 22 new
files. Graph: `332a161983cc9f6f49109fa34560fbe3e6ae73c49b27766228171285a1ccfce4`.
Manifest: `5ba164dacb62c83849a4402d0bb84108438e059098d6eca185f636924bfb0dea`.

The first closed-entry Wine run was refused before entry because debug sections
made the image 42,827,776 bytes, beyond the unchanged 38,993,920-byte image cap.
Removing only debug sections produced a 4,063,232-byte image. Defined native
section bytes, RVAs and flags match; text file padding after VirtualSize changed
from zero to 0xcc. The original debug binary and map are retained. The corrected
Source29 control reached the ARM64 entry and emitted the exact 268-byte Report
with an Unavailable/Proof outcome. Loader exit 1 is intentional for this refused
initializer. Cleanup completed and the unrelated sentinel survived; current
signature/profile and bundle checks passed before/after. The original owner-suite
assessment remains memory_wine_case_failed because this is a different fixture.
Only the separately named closed-gate observation passed. No FEX initialization
occurred, and this control is not repeated for the Source30 build.

Actual PE callback tables include two FEX callbacks and six GNU callbacks,
including libc++ chrono initialization; XI/XC/XL contain no nonnull callbacks.
This inventory comes from the linked PE bytes and exact link map, not only symbol
names. Source-body testing with a substituted NT query provider passed nine
cases: original error preservation, short output, invalid page/granularity and
address values, unchanged global state on refusal, and successful publication.
This does not execute the real Windows query provider or initialize FEX.

Eight PE units and two real Wine native units were compiled for stack usage.
Selected PE helper-frame sizes sum to 27,584 bytes; native owner functions sum
to 832 and named Wine view functions to 1,952. These are compiler observations,
not a closed concurrent or synchronous peak. Native view compilation retains one
existing declaration-after-statement warning. Full FEX build warnings concern
four upstream emitter return values; they are not ignored owner results.

**Final admission decision for this run: Stage 3 is incomplete.** The approved
262,144-byte extra-metadata ceiling is not yet proved after allocator backing,
final placement and temporary lifetime accounting. The 1,232-byte object-class
delta is not incremental physical backing; rpmalloc commits 64-KiB small pages.
Neither a small sizeof subtotal nor an independent worst-case page estimate
establishes the actual finite peak. No measured memory overrun is claimed.

A further concrete source blocker remains in the actual prelude:
Construct calls Config::Initialize, which invokes fextl::make_unique<MetaLayer>
and ConfigLayers.emplace. The selected make_unique performs placement
construction without checking a null allocator result; container allocation
through FEXAlloc likewise lacks the required typed failure outcome. A checked
Context factory cannot qualify these earlier operations. No fatal allocation
failure was deliberately triggered. Close this actual allocation path and the
aggregate budget before opening any proof selection. Genuine empty initialization,
checked teardown and retained-thread handoff/retirement controls remain required;
none is satisfied by a successful build or deliberate refusal observation.

Only affected source/graph controls ran (44 passed, zero failures/skips), plus
the nine finite provider cases, actual changed-unit compilation/link checks and
necessary closed-entry control. Governance and whitespace checks passed. Failed
attempts and private diagnostics remain local with their original outcomes. No
whole FEX/Wine test suite was repeated. The observation sidecar records exact
artifact hashes, limitations and retained failures. There is no completed Stage 3
report or Stage 4 authorization.

```sh
python3 -B -m unittest tests.fex.test_memory_fex_source tests.fex.test_memory_fex_pair.CanonicalGraphControls tests.fex.test_memory_fex_pair.CurrentProjectionControlControls
python3 -B tests/fex/run_basic_information.py --source <source30-tree> --output <fresh-output>
python3 -B tools/check_governance.py
git diff --check
```

### October 5 Continued Finite Configuration Construction

The requester explicitly continued the remaining Stage 3 conditions, preserving
local-only work. Within the existing finite empty-source scope, prepare a bounded
configuration path using the actual MetaLayer, standard unordered_map and normal
FEX configuration getters. Existing loaded-profile paths retain their allocator.
Review of the pinned implementation found no checked allocation entry for its
map/node operations; the existing page resource can grow and does not close that
failure. Use an allocator attached only to the finite MetaLayer, borrowing a
4-KiB NX array already present in the image. Include the complete array, actual
MetaLayer and bookkeeping in the aggregate memory account; do not raise its cap.

The finite configuration consists of the existing twelve Darwin policy settings
and the source fixture's two mode settings, each a one-character scalar string.
The pinned libc++ reserve(14) path uses one 17-pointer bucket array; insertion uses
fourteen nodes. Bound node size/alignment and observe the actual allocation
pattern with source-bound component controls before any engine run. Preserve the
original failure guard for a changed/unsupported container contract; never return
null to a standard container or silently fall back to heap growth. The existing
module startup and loaded configuration behavior are not qualified by this path.
The actual MetaLayer is constructed in place and destroyed exactly once; an
output construction flag carries cleanup ownership even when post-construction
validation refuses. Seal allocation after applying the source policy. No arbitrary
configuration, loaded file, environment layer or later mutation is admitted.

This is a local source change proposal/implementation within the authorized
Stage 3 initialization prerequisite. It does not open any of the twelve source
proof selections, permit real initialization, change the executable owner or
relax the total metadata limit. Actual compilation, bounded allocator behavior,
policy/default reads and cleanup remain to be verified before admission.


### October 5 Finite Configuration Results and Remaining Admission

Source31 closes the selected configuration allocation prerequisite using the
actual FEX MetaLayer, actual libc++ map and unchanged Darwin policy. The source
projection passed 62 genuine Git operations and independent replay (6,974 files,
40,548,596 bytes; 57 changed paths and 23 additions). Its manifest is
`00231e901e1f3497e2ddc3f2f27bbdd2c939cdb8a074c330a19c1d5cf16fcb1a`.
The relevant source/graph controls passed 44 tests without failures or skips.

Actual Config compilation passed for ordinary ARM64 and ARM64EC. Both compile
to 4,202 bytes for the finite storage payload, including the 4-KiB arena. A small
ordinary ARM64 PE with the real Config, Darwin policy and rpmalloc passed its
Wine execution: original profile reads, loaded-profile exclusion, fourteen
finite settings, incomplete seal refusal, duplicate initialization refusal,
normal destruction and no reuse after consumption. Loader exit was zero;
cleanup completed, the unrelated sentinel survived, and current signature/profile
checks passed before and after. The existing owner-suite assessment deliberately
remains `memory_wine_case_failed` for this different fixture; only the separately
named configuration sequence passed. This used ordinary MinGW CRT and did not
initialize FEX, create a source Thread or execute a guest. No fatal allocator
failure was deliberately triggered.

A fresh full Source31 constructor then passed all nine commands and verified
32 artifacts, including both PE target roles and native UnixLibs. It retained
359,766,231 regular output bytes, not a measured storage peak or required total
project footprint. The changed Config type is not mixed with old consumers.
The current closed initializer and CheckedCRT compile, DLL link and main-image
link also passed. All twelve admission flags remain false; the current closed
entry was not rerun merely to repeat an existing refusal observation.

Actual input-section symbols and the current final PE map now locate the three
owner units, fixture and configuration globals. Their writable payload totals
69,158 bytes and covers nineteen distinct 4-KiB PE pages (77,824 bytes). This is
conservative for Config because it includes unchanged upstream globals. The
actual fixture emits 4,468 writable bytes; the previous 4,476-byte member sum
included an unused retained pointer which this build eliminates. The 8-byte
Config constructor input slot is in the actual read-only PE section; its exact
callback pointer was matched rather than omitted on assumption. The initial
scan failed on this distinction and is preserved. These linked virtual-page
observations are not measured incremental physical backing or the complete
256-KiB aggregate. Native placement, actual allocator backing and simultaneous
stack/source lifetimes still need closure.

The next allocation review must follow actual nested constructors: CPUID's
PerCPUData.resize occurs inside Context construction; CreatePearThread calls
InitializeCompiler, which creates the opcode builder, lookup, decoder, pass
manager and JIT backend. Shared buffer construction also reaches allocate_shared
and GuestToHostMap's PMR objects. Several of these still use unchecked FEX
allocation followed by placement construction or container mutation. The
selected Windows VirtualAlloc returns null on failure, while LookupCache's
existing check tests only the -1 sentinel; this route needs explicit correction
and typed construction/cleanup propagation before admission. Merely replacing
outer unique_ptr allocation or reusing the pre-compiler construction cleanup
would not establish safe partial-compiler teardown. These are source findings,
not observed native crashes. No new fault fixture was run.

Stage 3 remains incomplete. The next required implementation is checked nested
construction with failure-safe partial cleanup, together with complete bounded
metadata/backing accounting. After those pass, prepare the signed current native
UnixLib derivative, admit genuine empty initialization, and finish the mandatory
source handoff/retirement controls and affected Wine regressions. Do not repeat
the passing configuration sequence or whole Source31 build without a relevant
change. No source proof selection, memory ceiling or security policy was relaxed.

Storage maintenance removed only three completed unauthenticated synthetic
prefixes, after exact inode/case identities, owned cleanup and absence of users
were checked under the shared lock. Their files accounted for 3,444,756,480
allocated bytes (about 3.21 GiB); this is not a separately measured APFS volume
reclamation. Logs, binaries, sources, actual results and every failed prefix
remain local. Prefix reconstruction was not tested. No GitHub write, commit,
PR publication or Stage 4 transition occurred.


### October 5 Checked Lookup and Partial Compiler Construction

The requester explicitly requested completion of all remaining Stage 3 work.
Continue in the approved source and task-document locations with no GitHub
publication. Reuse the existing Windows allocation provider and its original
WoW64 address requirements, returning the actual NTSTATUS before Win32 error
conversion. Add no owner-wire error domain or new execution permission. The
lookup constructor must publish pointers only after successful data reservation;
its native cleanup retains backing when release fails and never destroys that
still-owned object. Compiler outer allocations use the existing FEX allocator
with checked null results. Partial compiler construction needs its own checked
cleanup sequence, because the former attach/buffer failure route assumes no
lookup/backend exists. Preserve the first construction failure independently
from cleanup outcomes and retain uncertain trees. Nested container allocations
remain a separate open prerequisite; these changes alone do not admit FEX init.

The selected Darwin feature provider deliberately supplies no hardware MIDRs.
Reuse its existing unknown-product fallback as one constant CPUData row rather
than allocating identical per-core records during Context construction. Preserve
the observed core count, non-Darwin vector behavior, known-MIDR paths and CPUID
output. Brand-string chunks must return zero-filled tails without forming a
pointer beyond a short string. This removes an unnecessary selected allocation;
it does not synthesize hardware IDs or qualify guest execution.


### October 5 Finite Compiler and Emitter Construction

Continue the approved checked-construction amendment in the existing source
layer, fixture and task-evidence locations. Source35 retains the actual upstream
x87, dead-flag and register-allocation pass implementations and order, including
O0 behavior. Its selected non-dumping/non-validation pipeline uses three inline
owning slots and checked object allocation. Other dynamic pipelines retain their
original implementation. The shared code-buffer factory prechecks one 256-byte
allocation before actual std::allocate_shared; the selected control block must
fit by compile-time assertion, and its allocator releases backing only after the
last weak reference. The actual PMR map and allocator are embedded; map nodes
still use the original resource. Clear destroys nodes before releasing resource
pages and reconstructs the empty map in the same storage. Node growth is not
qualified by empty construction.

Source36 removes dynamic forward-label reference allocation from the selected
owner emitter. One first reference and sixteen inline additional references
are bounded; overflow is sticky and refuses dispatcher publication with checked
write-window abort. Source37 also refuses prepared JIT publication after this
failure. Neither layer admits guest compilation. Non-owner labels retain the
original vector. The increased inline stack/object storage must be included in
the current metadata calculation, not offset against an unmeasured heap saving.
The exact upstream emitter and fixups remain in use; no instruction encoder is
replaced.

Source35's nine affected units compiled for ordinary ARM64 and ARM64EC (18
commands). Source37 dispatcher/JIT compiled for both roles (four commands).
The current 37-layer source replay and source/pair suite passed (132 tests,
one recorded skip). A native ARM64 component control exercised the exact
extracted shared-control allocator with real std::shared_ptr/weak_ptr, forward
label bounds, and actual CPU-brand chunk copying. It passed. That control uses
the Mac standard library and source helper bodies; actual PE compilation is
separate evidence. It does not create FEX objects, emit executable code, or
establish the complete engine initialization or metadata gate. Earlier compiler
failure and depfile-closure refusal remain retained.


The current ordinary-ARM64 owner/macro-off type measurement passed. It records
Context1904/1328, Dispatcher736/544, JIT816/448, CodeBuffer200/40,
Lookup160/144, GuestToHostMap216/176, PassManager128/80, Thread12288/12288,
OpDispatchBuilder3736/3736 and ForwardLabel288/40 bytes. Thread alignment is
4096; other measured alignments are8. Enlarged heap size classes can commit
additional 64-KiB allocator pages; summing field deltas cannot admit the budget.

Within the approved finite ordinary-data construction scope, use explicit bounded
backing for the seven enlarged object allocations during the one-shot empty
initializer only. Keep the existing allocator for unchanged objects and outside
this mode. The eight-KiB data array plus exact sixteen-byte-run ledger occupies
one page-aligned twelve-KiB object, with separately counted atomic/TLS ownership
state. All of this backing is charged, including original payload and padding;
no allocator-page saving is presumed. Admission binds one actual TLS thread,
allocation refuses foreign threads, exhaustion and invalid sizes, and shutdown
refuses any live allocation. Existing object destructors and aligned_free route
retain the real lifetimes; a recognized pool allocation must match its exact
run before release. No executable allocation, source ownership protocol, memory
ceiling, guest permission or security setting is changed. Source and component
verification must pass before this finite storage mode can be executed by FEX.


## Approved Stage 3 Amendment C: Read-Only Metadata Admission

Status: approved by the requester in this thread on 2026-10-05 ("Amendment C approved; proceed with implementation", translated). This is a narrow extension of the
existing Stage 3 finite initialization plan, in this existing approved plan
location. It does not change the 262,144-byte ceiling, executable arena geometry,
permissions, capacity of source lifetimes, Stage 4 boundary or publication scope.

### Verified need

Source40's full native/ARM64EC/ordinary-ARM64 module build and independent
artifact verifier passed. The source/pair/owner-compile suites passed 165 tests
with one recorded skip. Actual FEX initialization remains unperformed.
The original allocator source/target has been restored; the finite object
storage is isolated in FEXCore_Base with an explicit owning deletion boundary.
The Source38 link failure and Source39 post-build include-policy refusal remain
preserved. Source39 compiled and linked, but did not pass its artifact verifier.

Wine's page-protection directory contains 1-MiB leaves, each covering 4 GiB of
virtual addresses. The FEX supplement extends the existing reservation by
538,050,560 bytes, represented by 131,360 protection entries. This is not proof
of 131,360 newly allocated bytes: the entries may be inside the same already
allocated directory leaf as the original Wine reservation. Recorded prior
ordinary runs place the mapping at 2,147,418,112 with length 1,588,985,856;
that particular span is inside the existing low 4-GiB leaf. A prior address
cannot establish the next run's result. Wine's file_view records also come from
an existing 1-MiB block/freelist. Counting only sizeof(file_view), or assuming
that a new block cannot be needed, does not close allocator backing admission.
These are specific unobserved runtime quantities, not an observed budget
violation or a reason to omit Wine metadata.

### Proposed private observation contract

Add one paired private owner-bridge operation, OBSERVE_METADATA (15), with ABI
version 3. Keep each existing request/response record at 128 bytes and keep Unix
index 10. Preserve opcodes 1 through 14 and their behavior. Version-2 peers
refuse version 3; retain the original version-2 build and test evidence.

The observation request carries only version, size, operation, current native
owner PID and the ordinary/native source role; every other request field must
be zero. It creates no extent/executor/continuation, changes no permission or
publication state, initializes no allocator/engine, and grants no capability.
The main-image caller and current authorization checks remain in force.
An uninitialized or quarantined owner, unsupported role, malformed request,
failed observation, or unknown count returns a typed refusal.

Use a distinct, fixed metadata-response interpretation rather than treating
counts as executable addresses. Its first 24 bytes retain version, size,
status, native error domain/code and reserved-zero fields. Its remaining
104 bytes contain thirteen uint64_t facts:

1. Native owner PID.
2. Actual arena mapping size.
3. Original pre-FEX reservation size for the identical mapping base.
4. Page size.
5. Protection-directory coverage bytes per leaf.
6. Protection-directory backing bytes per leaf.
7. Number of leaves covering the original reservation.
8. Number of additional leaves required by the extended reservation.
9. Backing bytes of a file_view allocation block.
10. Actual compiled sizeof(file_view).
11. Currently available file_view slots, saturated at the admitted bound.
12. Fixed native owner-and-adapter storage bytes, from the selected build.
13. Reserved zero for closed future evolution.

Collect the snapshot under the existing owner-to-virtual_mutex lock order.
Traverse only bounded existing structures; do not allocate temporary containers,
load symbols at runtime, expose internal pointers, or call a user callback.
If the bounded traversal cannot establish available slots, refuse rather than
reporting a truncated count as complete. The source preflight derives the
budget from the actual snapshot and compiled PE storage/stack bounds. It must
include possible backing allocation, retained cleanup state and current TLS
costs. The observation itself cannot flip a proof selection or bypass a source
lifetime/permission check. Before execution, record the exact construction
view-demand bound and reject insufficient headroom.

### Required verification and completion order

- Exercise the pure snapshot classifier with reused/missing directory leaves,
  exhausted/unknown view capacity, arithmetic overflow, wrong version/role/PID,
  and native observation failure. No deliberate native fatal fault.
- Compile/replay the paired Wine/FEX ABI and prove that original owner operations
  and rejection behavior remain unchanged. Verify the actual signed candidate
  and current profile before its bounded native run.
- Observe actual metadata on that candidate and close the full budget. A failed
  or unknown observation leaves initialization unavailable.
- Only after all existing proof gates pass, perform actual empty Context/Core/
  Thread construction and checked cleanup, then the already mandatory source
  handoff/retirement controls and affected Wine regressions.
- Complete the Stage 3 report and local stage commit only when those checks pass.
  No GitHub write or Stage 4 transition is authorized by this proposal.

Requester approved this read-only paired metadata operation and its finite
controls within Stage 3. Implementation is underway; approval is not execution
evidence and does not mark any proof gate as passed.


### Amendment C implementation checkpoint (October 5, local only)

The approved read-only ABI3 metadata operation is implemented as a third ordered
Wine supplement; the original two ABI2 supplements and their receipts remain
unchanged. FEX layers 41–42 add the typed observer and conservative classifier;
42 places both definitions in their declared external namespace. Source replay
passed for all 42 layers and 6,976 source files. The source/pair/owner-scope suite
ran 165 tests with one recorded platform skip and no failures; the affected Wine
builder/runner controls passed 64 tests. An initial invocation named a nonexistent
test module; its loader error was preserved and the correct test module was run.
The ABI3 unknown-opcode control now uses 16; the original standalone ABI2 fixture
continues to use 15 through the authoritative version selection.

Required native controls and the minimal ordinary-ARM64 Wine observation fixture
are prepared. They have not been compiled or executed: the other Pear task held
the shared native lock throughout this checkpoint. This task's queued test wait
was cancelled without invoking a compiler or interrupting the other task. Disk
space also fell from approximately 12 GiB to 3.3 GiB during the turn; the new Wine
build remains unstarted. The requester was asked to restore 12 GiB free space.
A read-only scan of obsolete successful Wine outputs found their large duplicate
files were already absent; its new candidate list contains only 1,220 payload
bytes and was not executed. Do not delete current donors, unique failures or
private state merely to pass the storage preflight.

Actual FEX initialization, checked cleanup, source handoff/retirement and the
remaining affected Wine execution checks are unperformed. All twelve initializer
proof selections stay false. No Stage 3 completion, GitHub publication or Stage 4
transition is claimed. Resume with the prepared native component controls, fresh
Wine ABI3 build and current signed candidate observation before opening any gate.


### Amendment C actual Wine observation and initialization prelude corrections

After the requester restored storage, native ARM64 component controls passed for
the actual owner observation dispatcher and FEX budget classifier with substituted
providers. The fresh ABI3 Wine build9 passed. Source42's full-build attempt
failed its mandatory CMake wire-header hash check because that check still
selected ABI2; Source43 corrects the exact pin, and its full native/ARM64EC/ARM64
build and independent artifact verification passed. The failure remains intact.

The currently authorized signed runtime8 passed admission. An ordinary ARM64
metadata fixture then registered an idle executor, observed the real owner and
unregistered it successfully. The loader exited zero, owned cleanup completed
and the unrelated sentinel survived; before/after signature, profile and bundle
checks passed. Actual observations were zero additional 1-MiB protection leaves,
at least 1,024 existing view slots and 108,564 fixed native metadata bytes.
These facts belong to that process. They neither establish the complete metadata
budget nor authorize another process from a historical address observation. The
general owner-suite assessor still refuses this different fixture; the separately
named read-only metadata sequence passed. No FEX initialization ran.

Review of the previously linked main image found one new static TLS byte with no
PE TLS directory: the upstream custom CRT uses dynamic TLS instead. Source44
reuses the existing Windows thread-ID wrapper, eliminating this unsupported
static TLS dependency. The checked prelude accepts absent static TLS only after
checking the actual PE sections and absence of TLS callbacks; present static TLS
retains its existing full validation. Native substituted-thread controls and
ordinary/EC compilation must validate the change.

The prelude also queried the owner before any operation initialized it. Source45
reuses the existing checked registration/unregistration helpers to prepare one
idle native executor, capture the read-only observation and release it before
constructing a Context. It refuses any existing source Context/Thread binding;
it creates no fake source lifetime or executable allocation. The existing
construction-cleanup fields record this pre-construction owner cleanup, keeping
its outcome separate from the primary failure. Source46 fixes the prelude's PID
environment key to the name actually set by the existing native owner launcher;
the independent native UnixLib GetPID comparison remains mandatory.

All twelve initialization proof selections remain false. The complete budget,
same-process budget admission, actual empty initialization and cleanup, source
handoff/retirement and affected Wine controls still require completion. The
next native compilation is queued behind Task #7's shared native lock; no other
task was interrupted. No GitHub write, completed stage report or Stage 4
transition has occurred.


### Source47 prerequisite preparation checkpoint (October 5, local only)

The restored disk has approximately 40 GiB free. Source44–46 ordinary/EC
compilation, the substituted-provider owner preparation and finite object storage
controls, and exact-input linking passed. Eight source translation units were
recompiled with stack reporting: all code-section bytes matched their linked
objects. Those frames do not yet establish a whole call-chain peak. The current
closed main's selected additional writable PE inputs cover 23 distinct 4-KiB
pages (94,208 bytes); the complete aggregate remains unqualified.

Further linked-image inspection corrected the earlier partial TLS finding:
removing the new identity byte still leaves 24 bytes of static libc++/libc++abi
TLS. The custom main lacked its PE directory. The test entry now reuses the
pointer-aligned template boundaries from MinGW-w64's public-domain `tlssup.c`
(https://github.com/mingw-w64/mingw-w64/blob/master/mingw-w64-crt/crt/tlssup.c),
retains FEX's existing `_tls_index`, and supplies a standard data-only directory.
The resulting template is 32 bytes, aligned to eight, with zero callbacks and
zero zero-fill. No alternative CRT startup is added. This static observation
cannot be substituted for actual loader initialization or allocator backing.

Source47 factors the existing image/TLS/environment/native-PID/idle-owner
prerequisite checks into a callable observation helper. The engine initializer
still checks the unchanged twelve false proof selections. The prerequisite-only
fixture invokes no CRT constructor, FEX object factory, executable allocation,
source lifetime or guest entry. Its ordinary ARM64 compilation and link passed;
verified debug-section removal reduces the loaded image to 4,120,576 bytes with
all defined native section bytes, RVAs and protections preserved. The source
projection passed for 47 layers and 6,976 files. Affected source/pair controls ran
132 tests, one skipped, with no failures.

The plan's heavy-build, signing, actual native runtime and storage-maintenance
serialization remains in force. Small isolated single-process compilation/link
inspection and portable substituted-provider controls do not perform those
operations and proceeded in independent outputs. Runtime9's signing preparation
is queued behind Task7. The exact-source prerequisite fixture must pass current
runtime admission and bounded supervised execution before any observation is
accepted. Actual empty initialization, whole metadata admission, source handoff/
retirement and remaining Wine execution checks are still unperformed. No stage
completion or GitHub publication is claimed.


### Isolate existing bitmap diagnostics from the empty initializer

The exact Source47 prerequisite fixture now passed under signed runtime10, with
current before/after checks, actual static TLS, native PID agreement, idle-owner
registration/metadata observation/unregistration, zero loader exit and complete
owned cleanup. The unrelated sentinel survived. No CRT constructor or engine
object ran. Runtime9's signing helper refused a copy command before execution;
that failure remains preserved, and runtime10 separates copying from signing.

The initial TLS directory used eight-byte boundary objects. Inspection corrected
the payload attribution: the unchanged template is eight bytes from FEX's
DummyHandlers and sixteen from libc++abi, not 24 bytes solely from libc++.
The fixture now uses pointer-aligned zero-payload COFF boundary labels, preserving
that original 24-byte template and its allocation request. Its second actual
prerequisite run passed. This does not infer allocator backing from payload size;
the complete metadata assessment remains open.

A separate source review found that every shared reservation unconditionally
runs the compile-selected ARM64EC bitmap diagnostic. That diagnostic can create
a full-address-space bitmap and associated Wine protection-directory backing;
the arena-only metadata snapshot does not account for this separate diagnostic
mapping. Treating its cost as zero would invalidate whole-budget admission.

Within the approved separation of finite correctness diagnostics and normal
source initialization, select this existing diagnostic explicitly with a private
process-start setting `PEAR_FEX_BITMAP_DIAGNOSTICS=1`. Absent or `0` means no
bitmap diagnostic; any other value refuses a shared reserve before mutation.
The full owner suite must set `1` and retain its mandatory exact bitmap count,
set/clear/restoration and cleanup assessment. The empty native initializer uses
`0`; it neither requests nor qualifies ARM64EC registration. This changes no
owner opcode, record layout, capacity, native/EC role admission, page protection,
signing/provisioning requirement or 262,144-byte ceiling. It is a diagnostic
selection correction within Stage3, not a waived test or a new capability.
Keep original supplements and failures; add a separately identified Wine layer,
verify affected runner selection, and verify both selected behaviors before
stage completion. No new product-documentation destination or GitHub write.


### Finite callback snapshot bound (October 5)

The exact Source47 prerequisite image has two FEX callbacks and six GNU
callbacks, verified from PE bytes and linked symbols. Its callback snapshot still
reserves 256 entries and GNU inspection reserves 256 pointer slots. Narrow this
private one-shot fixture bound to 16 entries; retain the original callback order,
identity checks and refusal before any constructor when a table exceeds it.
This reduces unused persistent and stack storage. It does not change owner-wire
capacity, source lifetime capacity, security permission or the 262,144-byte cap.
Recompile both affected translation units and entry, relink and remeasure actual
placement/stack sizes. Keep all proof selections closed until the complete budget
and other admission conditions are verified. The diagnostic-selection controls
and the full Wine owner suite have now passed on Wine10; those receipts remain
separate from actual engine initialization, which is still unperformed.


### Preserve view-backing admission at the allocation boundary

The metadata snapshot establishes current spare view records, but does not
reserve them. Reuse its existing bounded, read-only count under virtual_mutex
immediately before the FEX owned-view split; require two spare records (the
maximum split demand) before mutation. This prevents this allocation from
creating a new 1-MiB view block after an earlier observation became stale. Keep
the count and allocations in the same critical section. Exhaustion returns the
existing native-failure/NTSTATUS_NO_MEMORY outcome; invalid observation retains
NTSTATUS_INVALID_PARAMETER. Existing release remains available. No ABI, opcode,
source lifetime, executable protection or capacity increase is introduced.
The finite snapshot classifier and real initializer still need their complete
budget admission; this local guard does not replace it or qualify initialization.
Verify the exact extracted counter at exhausted, reusable, saturated and invalid
free-list states; build and verify the changed Wine and affected native suite.


### Final finite initializer candidate and remaining execution admission

Wine11's unchanged owner suite passed under current signed runtime13 admission.
The exact native metadata link covers 118,784 bytes in the required 4-KiB process
geometry, below the classifier's 122,880-byte native bound. The closed Source49
image has 90,112 bytes of selected mutable PE backing. The reviewed finite phase
model includes constructor/destructor, configuration conversion, source owner,
Wine view/tree and thunk frames; its largest added-frame bound is 40,560 bytes.
Rounding that bound and charging two stack boundary pages gives 49,152 bytes.
The reviewed added-metadata aggregate is therefore 262,144 bytes. This is a
source-selected bound for one ordinary ARM64 empty initializer, not total engine
memory, RSS, a multithreaded handoff budget or a runtime measurement.

Compiler-sized layouts bind 93 function slots in eight concrete source classes.
The eight actual constructor pointers are matched to the final closed image;
logging handlers remain absent, and generated dispatcher helper pointers are
emitted data, not executed callbacks. The review preserves original allocator
requests and TLS payload as baseline costs, charges enlarged objects through
the fixed metadata pool, and includes retained failure state without retries.
The current runtime14 signature, profile and complete inventory replay passed.

Source50 selects a separately identified private one-shot build candidate after
that source review. No environment or caller option can select its proof flags.
Before any invocation, the root must revalidate the final selected image's
mutable backing, affected stack frames, constructors, concrete virtual targets,
input identities and current runtime authorization. A failed or missing check
prevents invocation. Same-process metadata admission and Wine11's atomic spare
view check remain mandatory. Earlier closed candidates and failed inspections
remain preserved; this selection does not establish actual FEX initialization.

Actual empty Context/Core/Thread creation and checked cleanup, followed by the
already required source handoff/retirement controls, remain the completion
criteria. Stage 3 is still in progress; no GitHub write or Stage 4 transition.


### Actual empty initialization and next finite source transfer

The exact Source50 candidate passed its first actual ordinary ARM64 empty
initializer run. All eight constructors returned; actual Context, Core and
Thread creation completed, followed by checked Thread/Context destruction,
allocator completion, configuration shutdown and thread CRT finalization.
The loader exited zero, owned cleanup completed and the unrelated sentinel
survived. Current runtime14 identity/signature/profile inventories passed before
and after. The generic owner-suite assessor correctly refuses this different
fixture; its separately scoped empty-initializer assessment passes. The reviewed
262,144-byte added-metadata bound does not describe total FEX memory or RSS.

Continue amendment B with a source-known finite native transfer in the actual
Dispatcher and real Context/Thread. Reuse BeginPearDispatcherGate,
FinishPearDispatcherGate, checked managed-copy and atomic owner resume. The
finite emitted site tail-branches to a fixed native source callback, preserving
the native wrapper return address. This makes a refusal return directly to
native code without executing pinned managed code. The site changes only
caller-saved argument registers; SP, LR, x18, callee-saved registers and SIMD
state remain untouched. A successful callback explicitly invokes the fixed
original resume leaf only after atomic consumption and expected-byte checks.

Source51 keeps both initialization and this new transfer selection closed until
the affected code, concrete layout, stack, final image and current runtime have
been revalidated. A source deletion attempt permanently closes admission; test
that edge separately rather than assuming a refusal permits subsequent resume.
The first finite control covers actual source handoff, retirement refusal while
pinned, original-pin polling and atomic resume. It does not by itself qualify
JIT patch preparation, all retirement/writer edges, multithreaded schedules,
delivered exceptions, Stage 3 completion or any guest/game execution.

This checkpoint updates only the approved internal plan, observations and daily
board locations. No GitHub write or Stage 4 transition is authorized.


### Actual source transfer and owned JIT snapshot follow-up

Source53 initialized and cleaned up successfully but its finite transfer returned
INVALID_REQUEST. Inspection identified the unchanged Wine finite entry allowlist:
offsets zero and 4096 only. Source54 moved the original finite entry/resume ahead
of the ordinary dispatcher body, at exactly those existing positions. No Wine
entry predicate, page capacity or security claim was broadened. Source55's
selected final candidate passed actual generated ARM64 tail transfer, the real
source Begin/Finish gate, managed resume-word copy, retirement refusal while
pinned, original-pin polling, atomic resume and the original return value.
Checked cleanup and before/after runtime authorization passed; the failed first
run remains preserved. This is neither guest dispatch nor Stage 3 completion.

The next closed candidate reuses the actual backend's empty CodeBuffer, its
atomic allocation, owner WriteGuard and token publication. It supplies original
finite ARM64 bytes and the upstream header/tail layout, then calls actual
source snapshot/reconstruction methods under the dispatcher ACTIVE lease.
A bounded instruction copy feeds the existing half-barrier preparation routine;
only after source handoff does a checked transaction compare the expected bytes,
apply the upstream store order, publish RX and resume. Reacquiring a fresh
retained target precedes post-patch reads. No unaligned access is executed,
no handler is installed and no x86/x64 instruction is translated.

Charge the fixture header/tail's complete 4-KiB generated page conservatively
alongside the added metadata, even though its existing buffer reservation and
layouts are unchanged. Review simultaneous phases separately: the page is not
populated during prerequisite/constructor failures, and CRT inspection or Thread
attachment cannot recur during successful post-publication cleanup. Retain the
256-KiB cap; source57 invocation stays closed until the final phase budget,
provider/code identities and affected error/lifetime paths have passed review.


### Actual owned JIT patch and terminal lifetime follow-up

Source61 passed actual retained-target header/tail reads, both sides of the
upstream compact RIP-pair boundary, instruction snapshot, half-barrier patch
preparation, expected-byte refusal, checked RW/NX publication, atomic source
resume, fresh-target readback and checked cleanup. Runtime14 inventories and
current signature/profile checks passed before and after. Earlier Source58/60
failures are preserved: the fixture had incorrectly expected encoded byte zero
to mean (0,0); the original upstream decoder correctly returns (4,1). Neither
the decoder nor safety predicates were weakened. The selected phase bound
charges 90,112 bytes of PE backing, 122,880 native bytes, the full generated
metadata page and simultaneous stack/boundary pages within 262,144 bytes.

Source62 adds the already required terminal source-lifetime control after the
last successful transfer. Hold the genuine current Context/Thread lifetime,
request checked Thread cleanup, require UNAVAILABLE with backing intact, require
new lifetime admission and open validation to fail, release the original hold,
then require ordinary final cleanup to complete. Closure is irreversible; no
subsequent resume is attempted. The new candidate stays closed until affected
frames and final image are reviewed. Ticket/link and remaining source schedules
still require evidence; Stage3 and guest/game execution remain unqualified.


### Terminal lifetime passed; stable link-batch storage correction

Source63 passed genuine held-lifetime cleanup refusal, unchanged backend/lookup
backing, closed new admission, explicit original-hold release and complete final
Thread/Context cleanup. Current runtime replay passed before and after. The
source/pair suite ran 132 tests, with one explicit skip and no failures.

Review of the next mandatory source edge found a reference-lifetime defect:
BeginBatch constructed WriteGuard against a stack Work.Transaction, then moved
Work into the registry. The guard still referenced the expired stack object.
FinishBatch also moved that storage. Correct this within the same owner design:
construct the transaction and an optional guard in the existing fixed registry
slot, never move the live guard, and reset the slot only after publish/abort and
guard destruction. This reuses C++ optional and removes the additional heap
allocation; it changes no wire ABI, capacity, permission or synchronization
strategy. Remeasure the registry backing and affected frames before execution.

The next finite control calls actual BeginBatch/FinishBatch on the actual
reserved current JIT buffer before code publication, observes closed source
entry while the batch is open, and requires the original abort path to restore
reserved state. No known dangling-reference candidate is deliberately executed.
All initializer selections are closed pending this review. Ticket-bearing link
and delink controls remain separate required work. Stage3 is incomplete.


Source65 passed the actual reserved-target BeginBatch/FinishBatch path, source
entry refusal while the batch is open, the original abort back to RESERVED_NONE,
subsequent JIT snapshot/patch/resume and terminal lifetime/cleanup. The fixed
registry increases selected mutable payload by 168 bytes while retaining 90,112
bytes of linked backing. Maximum finite phase frames are 39,792 bytes before
stack-page rounding; the full aggregate remains within 262,144 bytes. The source
and pair suite again ran 132 tests with one skip and no failures. Ticket-bearing
link/delink, other mandatory source writers and wider source schedules remain
unqualified. No Stage3 completion, Stage4 transition or GitHub write occurred.

Storage pressure interrupted compile2 with signal9 and no compiler diagnostic
while only124 MiB remained; the signal cause is not established. After retaining
case/log/artifact hashes and confirming cleanup/no live users, nine completed
unauthenticated fixture prefixes were retired (10,334,269,440 allocated bytes).
All unique failed prefixes were preserved. A separate compile3 passed. The
bounded run reuses a built runtime and measured approximately1.1-GiB prefix; its
resource-only free-space check is8 GiB, without reducing execution, permission,
metadata or cleanup requirements.


### Actual direct source link cycle passed

Source67 passed actual direct jump and call patching, real source-map ticket
registration, Erase/queue, checked batch delink, fresh RX restoration, source
resume and complete terminal cleanup. Current runtime authorization replay
passed before and after. The existing generic owner-suite assessor refused the
different fixture report; that original refusal is preserved separately from
the scoped 268-byte source-fixture assessment. The latter passed every required
field, loader exit, sentinel and cleanup predicate.

The finite source call graph uses sequential link entry functions, the real
monotonic resource and original map allocators. Nine concrete vtables (98
function slots), eight constructors and current Core/JIT code were bound.
The maximum pre-publication phase is40,288 frame bytes; link and nonempty
cleanup phases each bound35,856 bytes, with the full populated4-KiB fixture
page charged. All phases retain the262,144-byte aggregate limit. The PMR
resource requests the same original4-KiB page for two cumulative64-byte
nodes; this is an added-metadata comparison, not zero process/heap usage.

Next extend only this finite source control to prepared-ticket cancellation
and populated GuestToHostMap::ClearCache. Reuse the actual private descriptor,
map lock, queue and resource teardown, retaining existing bounded storage and
all current permission checks. No guest cache execution, new handler, Module
initialization, Stage4 transition or GitHub publication follows. Stage3 remains
incomplete until every mandatory source edge and schedule has evidence.


Source69 passed four actual jump/call cycles, prepared-ticket entry refusal and
cancellation, Erase/queue and populated whole-map ClearCache/queue/resource
release/reconstruction. Fresh RX bytes and complete final cleanup passed with
current runtime authorization replay. The link-cycle frame bound is36,400 bytes
inside the unchanged262,144-byte aggregate. No guest or L1/L2 cache access ran.
Next cover the five source unaligned instruction families at four widths under
both finite preparation policies, in the same already charged4-KiB fixture page.
All words remain data: no delivered exception, unaligned memory operation or
guest instruction is executed. Current source snapshot, expected-byte check,
ordered write/publication, atomic resume and fresh readback remain mandatory.


Source71 passed all40 actual owned patch cases: LDAR, LDAPR, STLR, LDAPUR
and STLUR at8/16/32/64-bit widths under HalfBarrier and NonAtomic finite
preparation. Every case checked expected bytes, store order, retry delta,
publication, atomic source resume and fresh whole-record readback. These are
direct finite source controls, not delivered exceptions or executed unaligned
accesses. Existing link/cancel/clear, terminal lifetime and checked cleanup also
passed. Source/pair validation ran132 tests, one skip, no failures or errors.

Next qualify the actual CodeBuffer factory/destructor and deferred retirement
for16/32/64/128-MiB reserved source extents, one additional buffer at a time.
Keep a genuine shared reference while dropping the first, drain unrelated
retirement, require the held buffer's native write/abort admission to remain
valid, release the last shared reference, drain its real destructor ticket, and
require the original token to be stale before and after later allocation.
Do not write or execute new code or add metadata pages. All objects use the
existing charged fixed pool; remeasure the source frames before invocation.
This is factory/reference lifetime coverage, not backend buffer replacement or
guest lookup/translation qualification. No GitHub write or Stage4 transition.


Source73 passed actual16/32/64/128-MiB CodeBuffer factory, final shared-reference
destruction and deferred native retirement. A held reference retained valid
write/abort admission; after last release and drain the old token was stale,
including after later allocation. All earlier patch/link/lifetime checks and
complete cleanup passed. This does not qualify backend buffer replacement.

Review of the next required writer found a real abort bookkeeping omission:
DiscardPreparedPublication aborted the native writer without replacing the
CodeBuffer token. Fix it through existing ComparePearUpdate and poison admission
on failed abort or token replacement. Preserve the primary source refusal.
Reuse TryMakePearMetadataObject for the existing WriteGuard pointer so its
finite allocation is checked and charged within the existing fixed pool; no
class layout, owner ABI, capacity, permission or synchronization design changes.

Add a closed original-code source publication control: use the actual existing
private NX emitter allocator, cancel one prepared publication as source-invalid,
verify updated token and clean state, then publish one16-byte LDR-literal/RET
fixture through actual Begin/FinishPreparedPublication. Reacquire a retained
target, verify exact RX bytes and execute only that original native fixture
under the source ACTIVE lease. No guest decoding/IR, guest cache entry, delivered
handler or translated instruction is authorized. The8-KiB original private
emission backing is ordinary source buffer storage, separately below the16-MiB
temporary-emission limit; new owner metadata still requires the262,144-byte
aggregate gate. Bind its actual allocator virtual provider and frames first.


### Prepared publication failure and unchanged-byte cancellation

Source76 actual execution refused before completion (checkpoint low byte80).
Loader exited1; owned process cleanup and unrelated sentinel survival passed,
but FEX object cleanup did not. Full before/after runtime authorization replay
passed. This is a preserved failure, not a passing engine result. The old
two-digit checkpoint truncated higher bits; the fixture now emits all32 bits.
Source78 diagnostic-only candidate was built but not executed after review
identified a semantic error in cancellation.

The existing owner deliberately quarantines Abort on an already published
extent: it cannot assume arbitrary bytes written through the window are safe.
Source cancellation previously used that operation even before copying any
candidate bytes. Source79 adds a separate pre-copy cancellation helper reached
only from FinishPreparedPublication rejection before memcpy. It invokes the
existing checked Publish to restore unchanged original bytes and RX/cache state,
updates the exact source token and publishes no candidate entrypoint. Original
virgin NONE cancellation continues to Abort; uncertain/post-copy failures keep
the original poison/quarantine handling. No owner ABI, permission, allocation
capacity, instance layout or synchronization contract changes. This is a source
correction within the approved prepared-publication scope; actual success and
Stage3 completion remain unverified.


Source80 passed actual private NX/guard observation, pre-copy cancellation to
unchanged RX, exact token refresh, successful retry/entrypoint relocation and
original ARM64 literal/RET execution. Source cleanup, process cleanup, sentinel
and before/after authorization replay passed. Ten concrete tables bind102 slots;
the prepared-publication phase is35,504 frame bytes within262,144 total. The
generic owner-suite report refusal is retained separately from the passing
scoped268-byte source report. Stage3 remains incomplete.

Next exercise actual Arm64JITCore::ClearCache, SharedCodeBufferManager geometric
growth and lookup switching for32/64/128/128-MiB new extents. Retain the old real
shared reference across replacement; drain must not retire it. Observe an
unchanged-byte checked writer while retained, release the final reference, drain
actual destructor retirement and require stale identity. Keep the dispatcher
pinned throughout, no signal context or guest instruction, and clear only the
fixture inline-header pointer before its original generation is retired. All
new records stay in the existing fixed arena. Original weak control blocks and
original vector allocation requests must be included in source review; no
metadata-capacity expansion is authorized. Recheck actual provider/stack bounds
before invocation. This does not qualify translated guest-cache contents.


Source83 passed actual32/64/128/128-MiB manager growth, backend replacement,
lookup switching, retained old-generation admission and final-reference native
retirement. Earlier source snapshots are explicitly released before the
last-reference check. Full source/process cleanup, sentinel and authorization
replay passed. Growth frame bound36,848 and all other phases remain within the
262,144 aggregate. Completed original test prefixes were removed only after
closed successful cleanup, retaining logs/receipts and every unique failure.

Next extend the finite jump/call records from four to six within the same
already charged4-KiB page. The two added cases register one original code-page
metadata entry and use actual Context Begin/FinishPearLinkInvalidation plus
InvalidateCodeBuffersCodeRange under its original unique invalidation lock.
Require exact revision increment, empty affected maps, actual queued delink
and restored caller bytes. Numeric fixture guest identifiers are keys only;
no guest bytes, cache demand fault or delivered handler are used. Bind the
new map/vector and weak-buffer iteration provider frames before invocation.


### Source85 range invalidation and final build admission

Actual Source85 passed the Context range-invalidation path, exact map revision
change, queued jump/call delink, restored caller bytes and all retained earlier
finite controls. Loader exit was zero, terminal checkpoint was `00000021`, and
source/process cleanup, unrelated sentinel and before/after authorization replay
passed. The case digest is
`1ea8e36051c5bd7ff870baacc7119e7bc270d03caaf9b2618eb010b198ace979`.
Numeric guest identifiers were metadata keys only; no guest instructions or
delivered exception handlers ran. All candidate32 metadata phases stay within
262,144 bytes. This is ordinary ARM64 source evidence, not EC role admission.

The affected portable suites completed 469 tests with one genuine APFS skip,
zero failures and zero errors. The producer then failed to serialize its skipped
TestCase object. Its original log and failure are retained; a separate log reader
recorded the completed test outcome without rerunning tests or inventing producer
success. After the snapshot correction below, the affected pair suite passed
128 tests with the same one environment skip.

The final full-module build first refused before compilation because its input
snapshot inventory exceeded 512 files. Each of the 85 selected source layers
contributes three provenance files and four check/apply logs. Raise that finite
file-count ceiling to 1,024, preserving the existing 128-MiB aggregate and 8-MiB
per-file limits, exact inventory, regular-file and traversal checks. Controls
retain every log above the old ceiling and reject excessive sets and traversal.
This changes build evidence capacity, not the runtime 256-KiB metadata ceiling.
The original build refusal is retained; the next full build uses a fresh output.

### Final Source85 build result and acceptance checkpoint

The fresh full build passed all nine commands and 32 artifact checks; a separate
invocation of the independent full-module verifier also passed. The exact build
receipt digest is `9d4e431ee002099fde7c681327747cbfe653b33eae222dc0152e489dd9d1d304`. Its input snapshot retains 642 files. Native host,
ARM64EC and ordinary ARM64 PE modules were compiled/linked; this operation did
not load those modules or run their initializers. Governance passed 22 documents
and 172 local targets; `git diff --check` passed.

| Stage 3 requirement | Current evidence and decision |
|---|---|
| Ordinary native source construction/cleanup | Actual finite Source85 Context/Core/Thread lifecycle passed |
| Code publication, unchanged cancellation, source jump/call links and invalidation | Actual prepared publication, six link records including range invalidation, and 40 selected patch cases passed |
| Buffer growth, held generations and retirement | Actual 16/32/64/128-MiB factory lifetimes and 32/64/128/128-MiB backend growth passed |
| Native permission/protection/cache and finite synchronization | Existing authorized native owner suite and Source85 invocation passed within their declared finite scopes |
| Native added metadata | Candidate32 phase bounds remain at or below 262,144 bytes; not an EC budget |
| Matched full module construction | Source85 full build and independent byte/input replay passed |
| Actual EC owner registration/publication/retirement | Unqualified: EC caller/role rejected and backend callback absent; bitmap diagnostic is insufficient |
| EC retained bitmap metadata | Unqualified; actual backing and simultaneous lifetime must be included |
| Complete role-specific source-edge acceptance | Still required after EC connection; source and synthetic checks do not imply general module admission |
| Stage 3 / guest / Megabonk / distribution | Incomplete / unperformed / unperformed / unperformed |

The current acceptance result is **Stage 3 incomplete**. No stage-completion
report or commit, GitHub publication or Stage 4 transition is made. The following
concrete proposal isolates the unresolved finite EC admission from general
hybrid-module initialization.

## Stage 3 Amendment D proposal: Finite EC Owner Lifecycle Admission

Status: proposed, not approved or implemented. This remains in the existing
approved task-plan location. It does not mark Stage 3 complete or authorize
Stage 4, a general DLL caller, ARM64EC module initialization, guest execution,
delivered exceptions, game qualification, or GitHub publication.

### Concrete acceptance conflict

The approved Stage 3 positive gate requires actual EC registration for required
roles before publication and removal only after reference/pin drainage. The
current Wine11 source cannot perform that lifecycle: its PE entry rejects
`PEAR_FEX_ROLE_ARM64EC`, `pear_fex_wine_role` admits only NATIVE, and the Unix
backend's `ec_register` callback is NULL. These are deliberate admission guards,
not evidence of an environmental failure. The existing 38 successful bitmap
self-tests temporarily classify a NONE view and restore it; they never qualify
EC-role Reserve/Publish/Retire or an EC source caller. The ordinary Source85
initializer and its 13 selected proof controls do not close this gap.

The October 5 local-only admission explicitly retains the exact-main-image
restriction and does not authorize general DLL callers or ARM64EC initialization.
The adapter also labels general paired-module/source/CHPE/TLS admission a Stage 4
gate. Do not delete those guards, treat the bitmap diagnostic as the missing
lifecycle evidence, or initialize the hybrid module merely to satisfy Stage 3.
This proposal requests a narrowly identified finite EC test admission rather
than generalizing the current NATIVE fixture into an arbitrary-role client.

### Proposed implementation and reuse

1. Keep the current ordinary ARM64 source fixture and all its role refusals.
   Add a distinct compile-selected original ARM64 main-image fixture for EC
   owner lifecycle tests. Bind its executable, source, ordered Wine supplements,
   settings and current loader authorization in the existing private supervisor.
   Permit the EC role only for this explicit fixture configuration, exact
   main-image caller and finite entry/range rules. A nonce or module basename
   alone is insufficient evidence. No FEX DLL initialization or CHPE dispatch.
   General paired-module admission remains a later gate.
2. Reuse Wine's actual `arm64ec_view`, PEB bitmap, page representation,
   `VPROT_ARM64EC`, checked mapping/protection observations and original bit
   operations. Add the missing backend callback for exact owned, aligned views;
   observe every backing page and required bit before reporting registration.
   Preserve the owner-writer to Wine-VM lock direction. Register before exposing
   an entry and clear only after the existing source/executor/continuation
   drainage. Track bitmap pages shared by live extents so one retirement cannot
   remove another extent's registration or protection. Refuse foreign ranges,
   stale identities, guest-data roles and unobserved backing.
3. Keep ABI3, its 128-byte records, existing operation meanings, the single
   mapping and normal signing/provisioning. Do not repurpose reserved response
   fields. Use a bounded compile-selected diagnostic to account for the actual
   bitmap backing and any newly required Wine protection-directory/view blocks.
   Such backing is additional metadata unless independently established as
   pre-existing platform storage. Account for retained restoration state and
   simultaneous native/PE stack/storage; do not reuse the native-only budget as
   an EC budget. The 262,144-byte ceiling remains binding. If actual new backing
   cannot fit, retain that measured refusal and present a separately justified
   capacity/representation decision; this proposal grants no silent increase.
4. Use original code fixtures and the existing finite owner operations to check
   Reserve -> Write -> Publish -> Query/Entry -> Pin/Drain -> Retire -> Reuse.
   Observe actual RX/NX, cache maintenance, `VPROT_ARM64EC`, PEB bits and stale
   tokens at each required boundary. Reuse controlled error-return injection
   for bitmap commit/register/clear failures and preserve primary versus cleanup
   errors. No deliberate native fatal fault, delivered signal or x64 instruction.
5. Compile the matched Wine/FEX components once after affected portable checks;
   independently replay their records. Run the new bounded EC lifecycle and
   affected native-owner/source regressions with unrelated-process survival,
   exact owned cleanup and current before/after authorization. All configured
   allocation, writer, reader, handoff and retirement edges still need explicit
   acceptance mapping; EC success alone cannot automatically close Stage 3.

### Completion decision

A passing result qualifies only the finite EC memory-owner lifecycle. It cannot
qualify a hybrid loader, general FEX module entry, translated guest control flow,
real asynchronous exception delivery or ordinary-user distribution. Complete
Stage 3 and make its local stage commit only after the full original acceptance
matrix, including metadata and source-edge evidence, has no required unresolved
row. Otherwise preserve the specific refusal. No GitHub write is requested.

Review is required for this new finite EC caller/role admission because the
current explicitly selected test entry excludes that role and general paired
admission belongs to a later stage. The root AGENTS.md requires: "Ask first if
scope is unclear or conflicts with other work." This is a scope conflict review,
not a new Apple permission request or an automatic approval rejection.
