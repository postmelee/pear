# Task #5 Implementation Plan — FEX Darwin Services and Wine CPU Integration

Task plan: [`task_m1_5.md`](task_m1_5.md)
GitHub Issue: [#5](https://github.com/postmelee/pear/issues/5)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

Prepared October 2, 2026. The requester approved the task plan and its document locations. This implementation plan and Stage 1 execution await explicit approval. All commands, artifacts and expected positive outcomes below describe planned work, not performed builds or runtime results.

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

Each stage has a report/verification/commit and requires explicit continuation before the next. Stage 3's concrete capacities, registration, publication/backpatch and retirement design remains unselected by this plan. Present the measured design refinement for requester approval with the Stage 3 continuation request before any owner prototype or integration, even when the broad scope is unchanged. No successful inventory or compiler fixture promotes runtime eligibility.

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
- `tools/fex/{common,prepare,check,verify,tools}.py`: bounded FEX-specific input/materialization, local build-tool setup, capability/interface inventory and independently checked receipts. No full FEX build/native UnixLib port/translator entrypoint in this stage.
- `tests/fex/test_stage1_inputs.py`, `test_stage1_capabilities.py`, `test_stage1_evidence.py` and original compile/link-only fixtures under `tests/fex/capabilities/`.
- `mydocs/working/task_m1_5_stage1.md` and sanitized observations.

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

These are metadata-based proposals as of October 2, not downloaded/verified installations. Stage 1 must cross-check authoritative checksum text and actual bytes before use. CMake's prebuilt universal developer tool is not a source-built runtime dependency or permission claim; select and verify its ARM64 slice.

| Tool | Official Origin / Pin | Proposed Identity and Admission |
|---|---|---|
| CMake 3.31.8 | [Kitware release](https://github.com/Kitware/CMake/releases/tag/v3.31.8), `cmake-3.31.8-macos-universal.tar.gz` | Release API-reported SHA-256 `d1449f969c54d5c00886d5b643340d493dfb3c81cb39ee29b35453395c11ebf7`; official `cmake-3.31.8-SHA-256.txt` metadata SHA-256 `8d08ce0586bf40ff6b80e46fffe2db8855bab5b030db8b3782f11f68b6274ad8`. Actual checksum text/payload/native closure verification remains required. |
| Ninja 1.13.1 | [Official release](https://github.com/ninja-build/ninja/releases/tag/v1.13.1), commit `79feac0f3e3bc9da9effc586cd5fea41e7550051` | Derive source tree/listing/archive identity, inspect bounded bootstrap/build inputs, build native ARM64 into task-owned tool root; no floating tag alone or opaque substituted executable. |

### Verification

Inputs: approved initial records, exact selected read-only caches/#4 receipts and original capability fixtures. Tools: actual installed Python/Git/Xcode utilities, verified native task-local CMake/Ninja as needed, retained LLVM-MinGW 20260908 candidate. Planning found CMake/Ninja absent from inspected PATH; FEX static C++/CRT linking is unperformed. SDK/host/grants and tool slices are rechecked; Stage 1 does not require restricted permission or a graphical/Steam session.

Planned CLI (private placeholders are validated local handles; actual argument lists are retained privately):

```sh
python3 tools/fex/tools.py prepare --toolchain runtime/fex/toolchain.json --output .build/task5/stage1-tools --require-empty
python3 tools/fex/prepare.py --inputs runtime/fex/inputs.json --source-cache <read-only-selected-cache> --output .build/task5/stage1-inputs --require-empty
python3 tools/fex/check.py capabilities --inputs runtime/fex/inputs.json --config runtime/fex/build-config.json --prepared .build/task5/stage1-inputs --tools .build/task5/stage1-tools --cross-tools <verified-locked-tools> --wine-roles <verified-local-Wine-role-record> --output .build/task5/stage1-capabilities --require-empty
python3 tools/fex/verify.py stage1 --root .build/task5/stage1-capabilities --require-complete
python3 -B -m unittest discover -s tests/fex -p 'test_stage1_*.py'
python3 tools/check_governance.py
git diff --check
```

Expected: complete selected identity/dependency/notice/mount closure, actual required compile/link capabilities and source-derived table/target/layout inventory pass independent replay. Tests reject changed Git/payload/tool/receipt bytes, unsafe archive/mount/JSON/path, missing imports/static libraries, wrong target classification, unsupported configuration and incomplete evidence. Capability fixture output is build-only; FEX module construction, Darwin services, JIT, hybrid dispatch and WoW64 execution remain unperformed.

Retain bounded raw compiler/tool operations, rejected-control errors, exact fixtures/output headers/hashes, target matrix and source-derived contract. Export only sanitized role/digest/version/settings/outcome fields. A source inventory can be valid with named missing tools, but Stage 1's required compiler/static-link capability gate must pass before it completes; absence must not become a passing fixture or later build authorization.

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
python3 tools/fex/build.py modules --inputs runtime/fex/inputs.json --config runtime/fex/build-config.json --tools <verified-local-tools> --wine-roles <verified-patched-Wine-roles> --output .build/task5/stage2-build --require-empty
python3 tools/fex/services.py --build .build/task5/stage2-build --local-signing <private-authorization-handle> --output .build/task5/stage2-services --require-empty
python3 tools/fex/verify.py services --root .build/task5/stage2-services --require-complete
python3 -B -m unittest discover -s tests/fex -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

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

Choose a documented feasible publication and patching protocol through an explicitly reviewed design refinement. Protection transitions/dual mappings are alternatives to investigate, not existing FEX options or assumed allowed designs. Specify all writer and executor synchronization, source-address/relocation assumptions, I-cache maintenance, callback reentry, multi-thread observation and retired-version lifetime. The concrete owner strategy is not selected by this plan: present its capacity, registration, synchronization, publication/backpatch and retirement contract for explicit requester approval before any owner prototype/integration, regardless of whether the broad scope changes. Include that refinement with the Stage 3 continuation checkpoint after the completed Stage 2 report. Additional ownership/ABI/security scope changes also require an amended plan before implementation. A successful single code buffer is insufficient for all configured allocation classes.

Reuse temporary emission/relocation and version-held retired buffers; integrate actual copy/publish/rewrite/backpatch/invalidate/free semantics. Published active-code atomic stores must be coordinated with write/execute protection, code registration, instruction cache and all observers. Keep persistent disk cache disabled; identify deferred asynchronous readers/invalidation edges explicitly. Exhaustion, allocation/registration/cache-operation failure and unsupported permission paths produce preserved errors and no partial success.

Run original small native generated-code fixture operations under actual declared executable authorization, then the Wine/FEX owner boundary without translated guest execution. Cover bounded sequential and multi-thread schedules, lookup-versus-retire, patch-versus-entry, immutable mapping refusal and allocation generation/reuse. Use checked errors and controlled finite operations; no new deliberate native fatal-fault fixture or retry of the previously blocked no-TEB route.

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
- Stage 3 requires completed services/modules and explicit continuation approving the concrete measured memory-design refinement before any owner prototype/integration; the broad plan alone does not select or authorize that unresolved protocol. No JIT shortcut follows from a compile success.
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
