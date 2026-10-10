# Task #44: Steam route requirements and reuse research

GitHub Issue: [#44](https://github.com/postmelee/pear/issues/44)
Date: October 10, 2026 (Asia/Seoul)
Scope: Three-stage read-only research, including investment decision and conditional experiment proposal; no runtime implementation or experiment execution.

## Research Background

The requester distinguishes i386 helpers actually required by #11's Dock-backed owned Megabonk route from complete official Windows Steam bootstrap/desktop support. An i386 installer establishes a requirement for that installer route, not broad WoW64 as a universal Megabonk prerequisite. A bounded existing macOS Steam bridge comparison must precede any substantial loader/memory/ABI recommendation, but does not become a new prerequisite for #11's minimum Dock execution.

This note applies the approved [task plan](../plans/task_m1_44.md) and [implementation plan](../plans/task_m1_44_impl.md). It changes no official support claim, runtime or authorization. Current observations are [recorded separately](../working/task_m1_44_stage1_observations.json). Source inspection, retained parser results, host execution and game qualification are distinct evidence classes.

## Research Questions

- Which phase calls which executable or DLL, and is that dependency required, conditional or presently unknown for the selected game route?
- Which old inputs still match their recorded identities, and what does their evidence actually establish?
- Which missing observations would distinguish targeted helper work from broader desktop work?
- What must the existing native-bridge comparison cover before a substantial shared-runtime investment is proposed?

## Research Targets

| Target | Reason | Location |
|---|---|---|
| #11 October 10 priority and current/archived plans | Preserve Dock priority and the unapproved desktop/WoW64 amendment boundary | Hash-bound `task11` context entries in the observation ledger; peer HEAD `504f19d964ce948d770043349af7fa7d75500662` |
| 18 upstream files | Wine/FEX/Hangover/Madeira evidence baseline | `sources` entries with immutable origin URLs; retained from #11 `source-review` |
| 97 Dock comparison files | Trace conditional launch/services and actual upstream build selection | `sources` entries with repository, revision, path and hash; origin/fork remain separate |
| Original SteamSetup.exe | Bind PE32 and fixed-base flags to original bytes | Installer row below; inspected in place, never copied |
| Historical native parser artifacts | Preserve precise refusal/acceptance scope | Retained #11 `stage2-parser1`, #8 `build3` source/config/build receipt and original fixture producer |
| Merged #40 correction | Preserve accepted loader preimage and bounded result | [Stage 3](../working/task_m1_40_stage3.md), [final report](../report/task_m1_40_report.md); receipt hash below |
| Existing native bridge research | Establish comparison candidate and criteria | [Steam/game research](../../docs/research/graphics-and-game-integration.md), [platform reuse](../../docs/research/platform-reuse.md), pinned NotProton references below |

## Findings

### Dated ownership and actual input comparisons

At inspection, #11 is at `504f19d`, #10 at `37395ee04abd55ec67faa2e1b381f30ab47a9be4`, retained #40 at `c692099724c2065114ec431b694240a1b2ddef7e`, and #44 at approved planning commit `1aaf86e9c7f8223bd5f1e4f250b1112d12e31b6d`. #44 integrates master `942bd81`, including #40 PR #43. The exact #11 working-plan/research hashes and Git status are recorded; they are dated context, not accepted runtime interfaces. #11's Stage 1 history remains `09ea427`. The October 9 plans and October 10 priority record are separate inputs.

The corrected bounded reader performed **131 expected SHA-256 comparisons with zero mismatches**: 18 upstream files, 97 Dock files, six parser/producer/harness/observation identities, two build/config identities, three parser sources, four input files and one #40 receipt. Four retained parser stdout files also match the diagnostic strings. The Dock catalog has 36 origin, 37 fork, 15 Madeira and three files each from upstream FEX, Madeira FEX and Madeira Wine. Hash agreement preserves only the original claim scope; it does not rerun a compiler, parser or guest.

The initial inspection incorrectly compared the retained experiment `producer.py` against `fixture_producer_sha256`. Reading its complete producer showed that this field names `tests/wine/test_pe_arena.py`; `producer.py` instead matches `experiment_sha256`. The corrected inspection checks both. The first failed check and corrected reader identities are retained in the observation record. No expected hash was changed to fit different bytes, and no peer artifact was rewritten.

A task-owned ignored copy of all 115 public source files uses 1,909,310 bytes. The first and corrected inspection leaves together retain 3,818,620 source bytes, below the 64 MiB aggregate bound; each file is below 8 MiB. The installer, parser binary and private state were not copied. Reads use 1 MiB SHA-256 chunks, bounded file sizes, regular-file/no-follow checks and before/after file identity/time/size comparisons. The standard-library reader is retained with its SHA-256; it imports no peer tool or fixture module.

### Route and phase matrix

`Source-declared` describes the pinned implementation, not selected Pear binary execution. `Historical static` is a dated installed-file observation. `Unknown` is neither absent nor passing. Exact runtime bytes are identified only where actually available in this research's explicitly selected sanitized inputs.

| Route / phase | Component and role | Identity / architecture evidence | Necessity and remaining evidence |
|---|---|---|---|
| Dock / source build and host entry | `dockhost.exe`, Windows guest host for the genuine client | Origin `7fc8e4d...` builds x86_64 and i686; its explicit staging chooses x64. Madeira `48f97642...` selects its fork `72558e41...` and x86_64 compiler. New #11 receipt reports origin-built x64 Dock SHA-256 `a3762fdfb90b962f67e09ae5f3f61df8e1b700c9d52c7d5c08e3bf9e5bb8c3b7`; reused receipt, not rebuilt by #44. | Required for the selected Dock approach. x64 Dock does not prove all child helpers are x64. The shared no-account diagnostic reaches the client factories but fails before successful global-user creation; game/helper closure remains incomplete. |
| Dock / client loading | Genuine `steamclient64.dll`, client interfaces and session | `_WIN64` selects this filename; non-Win64 selects `steamclient.dll`. Madeira source pins client SHA-256 `71b391fe9f3e2006cbc81a5c75eef3eb4186012deabfdb2c8b7e8d4850ecf640`. The newly shared #11 component receipt reports the same actual file hash, x64 PE and 25,546,904 bytes; #44 reuses that byte-bound static observation. | Required for this client-host path. Selected PE/import records are now available; complete loaded-module, ownership and session behavior remain unqualified; downloader authentication is insufficient. |
| Dock / custom executable preparation | Wine `services.exe`, SCM | `start_manager` builds the path with `GetSystemDirectoryW`; selected file hash and PE machine remain unknown. It is a Windows service-manager role, not a Mach-O host process identity. | Conditional CEG path and service-manager absence, with explicit state/error checks. Neither `system32` nor calling-process bitness proves the selected service's machine. |
| Dock / custom executable preparation | Valve `bin/SteamService.exe /install`, service registration | `install_client_service` selects the loaded genuine client DLL's folder. New #11 receipt: 2,950,296 bytes, SHA-256 `72a406a6a2d3e282ab4b468ed8bfadf171fdd03a97969d6214a5da6fdb8dbd03`, PE32/i386; static imports retained in observations. | Conditional on service missing and installation enabled after SCM readiness. Existing registration prevents this install call but does not prove the registered service is unused. Actual service image/launch necessity requires its own receipt. |
| Dock / one-time game prerequisites | `dockhost.exe --start-services`, Wine service manager, installer executables or `msiexec.exe` | Madeira `DockInstallers.batch` emits a service step then each selected installer. No selected Megabonk prerequisite list or file/architecture receipt was consumed here. | Separate from the CEG path. Actual installer set, preparation state and resulting process closure are unknown. A successful helper exit alone is not SCM readiness evidence. |
| Dock / game and Steamworks | Original Megabonk, `steam_api64.dll`, dependent guest libraries | September 27 inventory reports game/Steam API x64; it is not a current selected-input hash. #40 records unchanged GameAssembly attach and later startup only. | Required game/session behavior remains unperformed by #44 and unqualified by these static inputs. CEG metadata, callback coverage, ownership and actual required helper set are unknown. |
| Both Windows routes / native execution | Wine/FEX and every required Mach-O dependency/helper | Prior limited baseline qualifications and #40 source/receipt are retained; no current complete process/module closure was measured here. | Required host processes and libraries must avoid Rosetta. Guest x86/x64 execution through FEX is a separate classification. Native launcher architecture alone is insufficient. |
| Official Windows bootstrap / installer | Original `SteamSetup.exe` | 2,380,800 bytes; observed SHA-256 `7d3654531c32d941b8cae81c4137fc542172bfa9635f169cb392f245a0a12bcb`; PE32/i386. | Required for the particular original-installer route. It proves nothing about whether Dock must execute that installer. Actual installer execution is unperformed. |
| Official Windows desktop / client and helpers | `steam.exe`, clients, web helpers and service | September 27 inventory: installed steam.exe/steamclient64/cef.win64/cef.win7x64 x64; steamclient.dll/cef.win7/Common Files Steam service i386. New Dock-package inventory instead records an i386 `steam.exe`, SHA-256 `1d2fbcc0402dc5a1f64b2e1d924e6e38e1dd76197c0246ddf89094fb86fda915`. Neither snapshot proves a full current desktop route. | Static presence is not dynamic necessity. Full login/startup/update/game launch requires separate complete selected-build evidence. The old Common Files service cannot be substituted as the identity of Dock's selected `bin/SteamService.exe`. |

Sources for the matrix: [origin build selection](https://github.com/125hz/madeira-dock/blob/7fc8e4d1b5ede349c89b3c155b203a8bf455f5bb/tools/build.sh), [origin main](https://github.com/125hz/madeira-dock/blob/7fc8e4d1b5ede349c89b3c155b203a8bf455f5bb/src/main.c), [origin launch](https://github.com/125hz/madeira-dock/blob/7fc8e4d1b5ede349c89b3c155b203a8bf455f5bb/src/launch.c), [origin SCM](https://github.com/125hz/madeira-dock/blob/7fc8e4d1b5ede349c89b3c155b203a8bf455f5bb/src/scm.c), [validation predicates](https://github.com/125hz/madeira-dock/blob/7fc8e4d1b5ede349c89b3c155b203a8bf455f5bb/src/validation.c), [Madeira build](https://github.com/willfaust/Madeira/blob/48f976429c189f8396e23d251d8a82f43c705922/build/madeira-dock/build.sh), [runtime pins](https://github.com/willfaust/Madeira/blob/48f976429c189f8396e23d251d8a82f43c705922/app/Madeira/SteamRuntime.swift), [game configuration](https://github.com/willfaust/Madeira/blob/48f976429c189f8396e23d251d8a82f43c705922/app/Madeira/MadeiraDock.swift), [prerequisite batch](https://github.com/willfaust/Madeira/blob/48f976429c189f8396e23d251d8a82f43c705922/app/Madeira/DockInstallers.swift), and the [dated Pear inventory](../../docs/research/graphics-and-game-integration.md). Hashes for all retained source files are in the observations.

The initial intake lacked selected Dock component receipts. During Stage 1, #11 explicitly shared `task_m1_11_step2a_observations.json`, `dock-components2/components.json` and `dock-bootstrap1/assessment.json`; their dated update is recorded below without rewriting the initial intake. No authenticated-prefix search, new proprietary download or execution of #11's changing adapters was used. Archive names containing `win32` and the `Program Files (x86)` folder never substitute for PE headers or execution observations. The actual Wine service-manager image and game-specific prerequisite/CEG necessity remain unknown.

### Newly shared #11 selected-component and no-account evidence

The three explicitly shared receipt SHA-256 values are `1ff43a33cd839ecd62c8b62244d1ea2c04db315df206fe32e1678c8f9b3ad2f5`, `608b6cc1ffc44e3f343b091993baaba4bd94b004056817879b5a8e3a884e4119` and `4e9ba560c76006cedea1e7ef602722fc494af6b3566b27e3134c71b9345004ff`, respectively. A separate bounded reader rechecked all three and verified that the 59 file rows from three packages agree across the component and step receipts, and all assessment fields agree. This is receipt-level reuse: #44 did not rehash package payloads, rerun their producer or replay the diagnostic. Five relevant byte-bound file rows, including static imports/delay imports, are preserved in `peer_update.selected_components`.

The genuine x64 client has the source-pinned hash above. Its listed `tier0_s64.dll` and `vstdlib_s64.dll` imports are also statically x64 in this selected package set. The original `bin/SteamService.exe` is statically i386. This strengthens the exact-file classification but does not prove that Megabonk takes its conditional execution path. Package `steam.exe` is i386, whereas the older installed inventory named an x64 file; different selected versions/bytes must not be conflated.

#11's no-account Dock diagnostic reports `public-client021-present=1` and `engine005-present=1`, but no `global-user-created=1`, successful bootstrap, shutdown or probe result. It fails with loader exit 2 and the first reported source guard `JIT.cpp:777 ExitPearFunctionLink`, status 6 (`PEAR_FEX_STALE_IDENTITY`), calling `FinishPearDispatcherGate`; the actual failed predicate remains unknown because multiple returns share that status. The secondary ARM64EC gate report is not a separate established cause. No evidence links this failure to execution of the i386 service. Cleanup/unchanged-input checks passed in #11's receipt; login, ownership, game and Steamworks remain unqualified. Its 11 registered instrumented process observations explicitly lack complete late-load/module coverage.

The peer owner continues direct-game startup investigation independently of Dock. It has not equated the #40 timeout with this Dock guard. #44 retains read-only ownership and does not take over x64 LookupCache/overcommit/resume diagnosis. Before any later overlapping change, name the exact files/preimages: accepted #40 baseline, then any separately reviewed #11 correction, then a separately approved #44 correction if needed. This coordination is not approval of any proposed memory ABI or patch.

### Conditional service paths and ownership

The inspected origin `sh_launch` tests `MADEIRA_STEAM_HOST_CEG` before its CEG preparation path (`src/launch.c:197–220`). In Madeira `configure`, this flag depends on the selected game's `customExecutables` and CEG configuration (`MadeiraDock.swift:409–426`). This is a source path, not an observation of Megabonk's selected depot metadata. Source escape flags are recorded to understand control flow; disabling required behavior is not a proposed workaround.

Within that branch, `sh_ceg_scm_prepare` first opens SCM. It starts a manager only on definite absence (`RPC_S_SERVER_UNAVAILABLE`, 1722), when it does not already own one. `start_manager` uses `GetSystemDirectoryW`, starts `services.exe` detached, then checks readiness and bounded failure paths. `service_registered` distinguishes a missing service from an unexpected error. `sh_should_install_service` returns true only when installation is enabled, the service is unregistered and the error means missing. `install_client_service` waits for the original Valve install process, terminates a stuck owned installer and then the caller rechecks registration. A registered service may still be demand-started by the client. These calls therefore do not establish either universal requirement or universal absence of i386.

The separate `--start-services` mode matters for ownership and false success. `sh_install_scm_start` leaves a responsive newly started Wine manager running for the session and closes its local handle; a later Dock host finds an existing manager and does not own it. In `main`, the helper reports service outcomes but returns zero even for failure; its worker timeout also terminates the helper with zero. Thus helper exit zero cannot qualify SCM readiness or prove the later host supervises the entire service lifetime. Future #11/#9/#10 evidence must account for this boundary; #44 did not change or execute it.

`main` also loads client interfaces, requires `SteamClient021` and `CLIENTENGINE_INTERFACE_VERSION005`, and selects session versus bootstrap behavior. Its game launch path publishes discovery state and asks the genuine client to launch. Those source calls alone do not qualify original-game callbacks, ownership or session continuity. Complete interface/lifetime comparison is Stage 2 work.

### Original installer and retained parser limits

| Field | New bounded static observation |
|---|---|
| Machine / optional header | `0x014c` i386 / `0x010b` PE32 |
| COFF characteristics | `0x010f`: LAA absent, RELOCS_STRIPPED present |
| Preferred base / image size | `0x00400000` / 483,328 bytes |
| DLL characteristics | `0x8540`: DYNAMIC_BASE present |
| Base relocation directory | RVA 0, size 0 |
| Signature / execution | Publisher signature unverified; execution unperformed |

These fields are mutually recorded as found; DYNAMIC_BASE is not evidence of usable relocations. The reader bounds DOS/COFF/optional-header offsets and directory count after checking the unchanged file hash. It does not validate the complete image, imports or guest behavior.

The retained `pear_pe_plan_read_target` source checks the requested target before reading the file and admits only ARM64/AMD64 targets. It then uses `IMAGE_NT_HEADERS64`/PE32+ and requires LAA, unstripped relocations and DYNAMIC_BASE. Its relocation collection accepts DIR64. The observed installer therefore raises separate PE32, four-byte relocation and non-LAA/fixed-base policy questions. Removing one enum gate or adding HIGHLOW cannot establish admission or safe occupied-address behavior. No fix or low-memory design is selected here.

The retained parser outputs are ARM64/x64 `00000000 1`, i386 fixture/original installer `c00000bb 0`, with recorded exit zero. Current checks compare bytes and output records only; the binary was not run. The target-first refusal does not validate the i386 fixture's complete format. Baseline parser sources, build/config receipt, binary, experiment, original fixture producer, harness and observations match their recorded identities. The compiler hash remains a historical receipt field, not a newly checked toolchain qualification.

The #40 candidate receipt still hashes to `d6d053e73eb0a7625177e1901936efeed4ee7eddadd9e822a0094398e8505808`. Its merged reports retain the 64 MiB correction and bounded startup result: GameAssembly attach, metadata read-open and GC Finalizer before a 120-second timeout. Neither the later timeout's cause nor menu/Steamworks is established. The old #8 `0x300000000` arena observation describes one run, not impossibility of all low-address designs. These are reused historical findings, not fresh #44 execution.

### Existing native bridge candidate and decision criteria

Existing Pear research and the approved intake identify NotProton at `c3a49486c14cdf6b9716e2e7ac55286aa537fcf1`: macOS `lsteamclient` and a Proton 9 `steam-helper` port named `steam-shim`. The previously inspected pinned README names Steam `1788652215`/`1790121765`, CrossOver Preview `20261006`/`2026082`, an ntdll patch and an early FEX option while recommending Rosetta. These are upstream declarations retained from planning, not new Stage 1 source-build/runtime validation. Stage 2 must inspect missing pinned implementation files and dependencies.

| Criterion | Stage 1 status | Evidence Stage 2 must distinguish |
|---|---|---|
| Original Windows Steamworks calls and ABI | Unknown for original Megabonk | Exact interface/version and data/handle conversions through existing lsteamclient; native SDK availability alone is insufficient. |
| Callbacks and lifetime | Unknown | Ordinary callbacks and asynchronous call results, thread/re-entry behavior, shutdown and ownership of buffers/handles; init-only success is insufficient. |
| Real ownership and session | Unperformed | Original game connected to genuine client, owning account, App ID and normal launch context; download/QR login is not a runtime session. |
| Complete required Rosetta-free host closure | Unperformed | Selected Steam/bridge/helper/library process and module evidence; a universal file or ARM64 parent does not establish all selected slices. |
| Reproducibility and maintenance | Source coupling identified, cost unresolved | Source availability, component terms, generated API/build dependencies, ntdll changes and Steam/Wine/FEX update regression burden. |

macOS Steam existence neither proves this alternative easier nor establishes functioning Pear/game integration. No bridge adoption, bridge implementation or new loader/memory/ABI proposal follows from this candidate entry.

### Manual claim-scope review

| Potential false inference | Stage 1 disposition |
|---|---|
| SteamSetup i386 means all Megabonk routes need broad WoW64 | Rejected: exact installer-route requirement only. |
| x64 Dock means all helpers are x64 | Rejected: conditional service/prerequisite processes need selected bytes and execution evidence. |
| An installed DLL/helper is required at runtime | Rejected: source conditions and actual required process/module coverage remain separate. |
| Parser result establishes guest execution or complete PE32 validity | Rejected: target-first refusal, native parser only, no rerun. |
| September inventory establishes current Dock/client architectures | Rejected: dated file selection without current exact input linkage. |
| Helper exit zero proves services ready | Rejected: inspected `--start-services` mode intentionally returns zero on failed/timeout paths. |
| macOS Steam existence or SDK ARM64 slice proves a usable bridge | Rejected: all five criteria remain required. |

### Stage 2 source provenance and comparison boundary

Stage 2 follows the requester's explicit continuation after Stage 1 commit `79986eb`. The [Stage 2 ledger](../working/task_m1_44_stage2_observations.json) binds every new source to its origin and digest, and records symbol/line anchors. All 115 task-owned Stage 1 source snapshots were rechecked. New targeted acquisition comprises 26 NotProton files and 19 files from its actual Proton dependency, totaling 6,116,736 bytes. Every acquired file matched its immutable tree entry's size and Git blob SHA-1 and its saved SHA-256. This is targeted source verification, not a complete build or reproduction of the upstream baseline digest.

Nine selected #8 composed FEX sources match the retained `source-files.json` manifest (`2ffc47a300c2c1ca3dd0a36bd40bc7e4c95a455278b7c8fcf47ea739b04e94cb`). Three composed Wine sources match Stage 1 identities. Four integrated #40 patch/metadata files match this task's Git HEAD. The source-review directory contained 11,687,940 bytes at the snapshot checkpoint, including previous copies and method/tree metadata, below 64 MiB. No proprietary payload or peer source was modified. The observation ledger also records the bounded reader and downloader identities; upstream scripts were read, never executed.

Source abbreviations below resolve to full revision/path/hash records and anchors in that ledger: **W** = pinned upstream Wine; **F** = pinned upstream FEX; **PW/PF** = retained composed Pear Wine/FEX, with separate #40 patch metadata; **N** = NotProton `c3a49486...`; **P** = Proton `164e0ccd...`. Composed files are hash-bound build inputs, not claims that an upstream commit alone reproduces Pear. The retained Wine sources precede #40; review of its ordered patches preserves the accepted correction without applying patches or rerunning the parser.

### Wine/FEX reusable functions and missing i386 contracts

| Boundary and source | Reusable behavior found | Missing Pear contract / refusal to preserve |
|---|---|---|
| CPU-module and builtin closure: W `dlls/wow64/syscall.c`, `get_cpu_dll_name`, `process_init`; `dlls/ntdll/unix/loader.c`, `load_wow64_ntdll`; F WOW64 CMake/export definition | Wine selects the x86 CPU module (registry override, ARM64 default `xtajit.dll`), loads WoW64 exports, sets the 32-bit PEB/TEB dispatch fields and loads the foreign-architecture builtin ntdll. FEX already supplies the CPU-module exports and links its existing core/common/runtime dependencies. | `libwow64fex` alone is not the closure: i386 ntdll/imports, wow64/wow64win, host loader/server and dispatch addresses must agree. Wine's `PtrToUlong` publication makes address representability part of the contract. No selected i386 builtin closure was built or executed. Retain C/C++/assembly. |
| PE32 and memory: PW `pear_pe_plan_read_target`, `process_relocation_block`, `map_image_view`, `virtual_map_image`, `set_protection`, `NtFreeVirtualMemory`, `NtQueryVirtualMemory` | Ordinary Wine has HIGHLOW versus DIR64 relocation widths, image-base update and server/view bookkeeping. Mapping tries the preferred address then bounded alternatives. Protection/query/free/unmap maintain view/owner state. | Pear's arena admission selects ARM64/AMD64 and PE32+, relocatable/LAA images. The original fixed-base/non-LAA installer remains refused before parsing. HIGHLOW alone does not solve fixed-base conflicts, 32-bit bounds, import closure, rollback or owner admission. Existing owner protection and free checks must not be bypassed with raw mmap/mprotect. Low ordinary NX address feasibility remains unperformed. |
| Process/thread initialization: F/PF `BTCpuProcessInit`, `BTCpuThreadInit`, `GetWowTEB`, state load/store | Existing configuration sets 32-bit guest mode, hooks/core/image tracking, per-thread GDT/FS, TLS slots, WOW64 context, call/return stack and thread map. PF adds checked context/thread preparation and retains partial state when safe cleanup cannot be proven. | PF initializes some source state but is not an admitted i386 executor. Low dispatch/guest data, source identity, GDT/TLS lifetime and cleanup must compose with Pear. The upstream LDT mirror remains a TODO. Thread creation is not execution qualification. |
| Syscall/unixcall and dispatch: F `WowSyscallHandler::HandleSyscallImpl`, `HandleSyscall`, `BTCpuSimulateImpl`; PF `BTCpuGetBopCode`, `__wine_get_unix_opcode` | Existing code reads 32-bit stack arguments/return EIP, crosses to `Wow64SystemServiceEx` or Wine Unix dispatch, flushes/reloads context and releases/reacquires simulation state around host calls. Upstream INT2E stubs are low-address RWX; PF allocates RW stubs and records logical guest execution. | PF BOP and Unix-opcode getters deliberately return null; simulation returns without executing under `PEAR_FEX_MEMORY_OWNER`. A host-NX stub plus logical execute bookkeeping does not prove source-owner admission, correct JIT entry or return. Preserve the refusals until 32-bit entry, syscall and callback re-entry identities/lifetimes are established. |
| Context, suspend and exception return: F/PF `BTCpuGetContext`, `BTCpuSetContext`, `BTCpuSuspendLocalThread`, `BTCpuResetToConsistentState{Impl}` | Upstream carries integer/EIP/flags/segment and x87/XMM state, reconstructs translated state and handles call/return stack faults, overcommit, JIT guards, invalidation, suspension, unaligned access and guest exception delivery. | PF context get/set and suspend/reset return unsupported (reset helper false). Actual Darwin signal/SEH and native-to-guest resumption, nested callbacks, stack/context widths and owner leases remain unqualified. ARM64EC success cannot supply i386 context semantics; AVX/XSTATE remains #42. |
| Code mutation: PF `BTCpuFlushInstructionCache2`, `BTCpuFlushInstructionCacheHeavy`, `BTCpuNotifyMemoryDirty`; common `InvalidationTracker` | Upstream tracks executable intervals and invalidates translated code; common code distinguishes logical guest permissions from host mapping. | These three PF entry points explicitly refuse. Required gap: actual source-lifetime and writer admission, all affected threads/links, dirty-range semantics and safe completion before code can be reused. No unconditional guard removal. |
| Allocation/protection/free: PF `BTCpuNotifyMemoryAlloc`, `BTCpuNotifyMemoryProtect`, `BTCpuNotifyMemoryFree` | Upstream before/after callbacks serialize updates and apply changes on successful VM operations. ARM64EC's `PearMemoryNotification` admits a link-invalidation batch before taking the thread mutex, records the actual lifetime, and completes after unlocking; failed operations preserve live permissions. | All three WoW64 notifications refuse. The transferable item is the ordering and success/failure discipline, not its ARM64EC CPU-area accessor or pointer types. i386 identity, 32-bit range/overflow, nested notifications, release/decommit and rollback require their own binding. |
| Image/map/unmap/read/DEP: PF `BTCpuNotifyMapViewOfSection`, `BTCpuNotifyUnmapViewOfSection`, `BTCpuNotifyReadFile`, `BTCpuNotifyProcessExecuteFlagsChange` | Existing image/interval tracking and ARM64EC `NotifyMapViewOfSection`/`PearInvalidateGuestRange` expose ordered invalidation semantics. Read-file notification invalidates only on successful after-callback; asynchronous writes need separate coverage. | WoW64 map returns unsupported; unmap/read/execute-flags record unsupported and return. Missing: admitted image/source lifecycle, canonical memory bookkeeping, actual executable bytes affected by synchronous/asynchronous I/O, process-wide DEP changes, and retirement after in-flight work. |
| Teardown: F/PF `BTCpuThreadTerm`, `BTCpuProcessTerm`; PF core `DestroyPearThreadChecked` | Upstream thread teardown suspends/removes state and releases GDT/call-return/context resources; upstream process-term hook is empty. Pear core uses close, source-release proof, detached backend/lookup checks, seal/delete ordering. | Both PF WoW64 termination hooks explicitly refuse. Thread-safe retirement, outstanding callbacks/handles, cross-thread teardown and process cleanup are not supplied by the upstream empty hook or by an ARM64EC adapter. Checked core lifetime semantics are candidates for reuse. |
| Feature reporting: PF `BTCpuIsProcessorFeaturePresent`, `BTCpuUpdateProcessorInformation` | Readiness/CPU-feature/info checks protect existing reporting paths. | Their presence does not qualify i386 ISA or extended-context coverage; do not enable AVX to resolve this task. |

The full refusal groups above cover the inspected `PEAR_FEX_MEMORY_OWNER` export paths, including void notifications that publish unsupported status instead of returning it. They are evidence of missing integration contracts, not defects to remove mechanically. `EnterPearEC`/`ExitPearEC` and `BeginPearLinkInvalidation`/`FinishPearLinkInvalidation` provide useful actual-thread/frame, source-mutation and lifetime checks. The i386 adapter must establish equivalent guarantees with its own context. Common overcommit handling validates reservation/private-RW bounds and exact commit range; this review neither reproduces nor diagnoses #11's later x64 startup issue.

Madeira's guest-window / `CONFIG_GUEST32BASE` approach spans JIT address translation, Wine pointer arguments, TEB/PEB and helper interfaces, with explicit distinctions between guest pointers and host pointers/handles. Its iOS page-zero constraints are not a macOS result. It is a coupled alternative, not a small module replacement. Hangover's selection approach is likewise a reference with its own dependency pin. Neither whole subsystem is adopted.

The accepted loader order remains `0001-admission-diagnostics.patch` followed by `0002-image-admission.patch`. The latter patch hashes to `dd0717923230d2bb9db6c359824300dee4b277b0c3254dee4454a5fdde34acfd`, takes header preimage `89ef518c0dc4008dd2392e6291082260028685005034c9079d20d7bd14422e34` to `dccb37fd2f3506ac95539f8c084860f426b338976862e734b6e307df87a228a3`, raises the bound to 64 MiB and leaves arena geometry unchanged. Full diagnostic preimages and the unchanged older PW source identities are in the ledger. A later proposal must start from accepted #40 plus any separately reviewed overlapping #11 correction, not from this older composed snapshot.

### Existing bridge: representative original-call boundary and return

The source-level candidate is the [NotProton lsteamclient overlay](https://github.com/NotProtonNot/NotProton/blob/c3a49486c14cdf6b9716e2e7ac55286aa537fcf1/lsteamclient/steamclient_main.c) on the [pinned Proton generated wrappers](https://github.com/ValveSoftware/Proton/blob/164e0ccd2ea2b1ec2e5d08dc97f65b184c2539ca/lsteamclient/cppISteamApps_STEAMAPPS_INTERFACE_VERSION008.cpp). The original Megabonk `steam_api64.dll` call stream was not inspected or executed. Thus the trace below starts at the bridge's exported interface boundary; whether that original game reaches it and requests these exact versions remains unknown.

1. N PE `CreateInterface` calls `load_steamclient`/Wine Unix dispatch. N Unix `steamclient_init` opens genuine `steamclient.dylib` under `STEAM_COMPAT_CLIENT_INSTALL_PATH` (with a filename fallback) and resolves `CreateInterface`, callback, call-result and release exports. N `steamclient_CreateInterface` returns the native interface handle. Missing load/export/interface outcomes remain failure paths, not ownership substitutes.
2. N `create_win_interface` caches a Windows wrapper by interface name plus native handle; P's generated constructor table includes `SteamClient021` and `STEAMAPPS_INTERFACE_VERSION008`. Unknown constructors return null. P `winISteamClient_SteamClient021_GetISteamApps` carries the actual user/pipe/version through its Unix wrapper and wraps the returned native Apps interface. Windows vtables and host pointers are separate; the `u_iface` field is a 64-bit handle, with explicit 32-bit forms for relevant guest parameters.
3. P `winISteamApps_STEAMAPPS_INTERFACE_VERSION008_BIsSubscribedApp` packs that handle and a 32-bit App ID, invokes `STEAMCLIENT_CALL`, and returns `params._ret` as `int8_t`. The macro selects the generated Unix dispatch entry. The Unix implementation casts the genuine interface, calls `iface->BIsSubscribedApp(appID)`, stores the actual result and returns dispatch status zero. The dispatch status and ownership result are different fields: zero NTSTATUS does not mean a subscription exists.
4. The inspected native `SteamUser023` methods similarly forward `BLoggedOn` and `GetSteamID`. These source forwards are evidence against an unconditional account/ownership success shim in the representative path. They do not prove the actual owning account, normal launch context, session continuity, interface coverage or real game's entitlement result.

The complete original-game call graph, actual requested SDK/interface versions, unsupported interfaces, authentication/ticket behavior and lifecycle remain gaps. A successful single representative API is not general Steamworks compatibility.

### Existing bridge: callbacks, call results and lifetime

N PE `Steam_BGetCallback` drains queued callbacks around its Unix call. Unix `steamclient_Steam_BGetCallback` calls the genuine native export, retains a descriptor/cookie and computes the Windows payload size. PE allocates a Windows buffer, then `steamclient_callback_message_receive` converts the payload and deletes the descriptor. For callback 703 (`SteamAPICallCompleted_t`), the nested callback length is converted separately. PE's `Steam_FreeLastCallback` frees its saved buffer and calls the genuine native release export. Payload validity therefore depends on this polling/release sequence and original-game consumption, which is unobserved.

A complete representative conversion exists for `LobbyCreated_t` (callback 513). P `callback_def` orders its lengths as **Windows, Unix**. The generated 64-bit callback table's SDK-165 row specifies **16 Windows bytes / 12 Unix bytes**, and `u64_LobbyCreated_t_123::operator w64_LobbyCreated_t_123` copies `m_eResult` and `m_ulSteamIDLobby`; the older row is 16/16. N's size selection and conversion consume the Unix size and produce the appropriate Windows size. Even x64 guest to ARM64 host needs layout conversion; equal pointer widths do not eliminate ABI work.

For asynchronous results, PE `Steam_GetAPICallResult` carries pipe, call handle, callback ID/length and failure output to N Unix code. It allocates a native-layout buffer where needed, calls the real `Steam_GetAPICallResult`, and converts/releases it on success. In the inspected failure branch, a separately allocated conversion buffer has no matching free before return; that is a bounded source finding requiring review before reuse, not a measured leak in Pear. The record makes no change to upstream.

Other registered function/vtable callbacks use a pthread-mutex-protected native queue and a two-step capacity/copy protocol in `steamclient_next_callback`. PE `execute_pending_callbacks` performs the guest dispatch after returning from the Unix call. This avoids treating a native C++ function pointer as a Windows callback, but does not prove Pear/FEX re-entry, nested dispatch, callback-on-another-thread or unload safety.

Specific unresolved edges are retained: the PE `last_callback_data` is global; unknown callback IDs use raw copy; size mismatches may warn/fall back; the manual polling/result conversion calls select `false` for the WoW64-layout flag. The reviewed x64 example must not be generalized to complete i386 callback support. Callback delivery alone does not establish ownership or the game's consuming code and buffer lifetime.

Sources: N [Unix bridge](https://github.com/NotProtonNot/NotProton/blob/c3a49486c14cdf6b9716e2e7ac55286aa537fcf1/lsteamclient/unixlib.cpp), P [callback metadata](https://github.com/ValveSoftware/Proton/blob/164e0ccd2ea2b1ec2e5d08dc97f65b184c2539ca/lsteamclient/unix_private.h), [generated conversions](https://github.com/ValveSoftware/Proton/blob/164e0ccd2ea2b1ec2e5d08dc97f65b184c2539ca/lsteamclient/unixlib_generated.cpp). Exact anchors are in the Stage 2 ledger.

### Existing bridge: session setup and current integration incompatibility

N `steam-shim/steam.cpp` loads `steamclient64.dll`, creates a Steam pipe, connects to the global user and requests real Utils/Apps interfaces. Shutdown releases the user, pipe and client module. Its main path uses `SteamGameId`, publishes discovery/registry/window state, initializes then shuts down that setup connection before launching the child. Initialization failure is logged but does not prevent the later process launch. Registry installed/running flags are not an ownership result. A child-launch success cannot establish a live original-game Steamworks session.

The inspected existing integration also conflicts with this task's exclusions. N [detour.c](https://github.com/NotProtonNot/NotProton/blob/c3a49486c14cdf6b9716e2e7ac55286aa537fcf1/ntdll-patch/detour.c) depends on hard-coded `WINE_MODREF` offsets, obtains write/execute protection for the loaded Valve image, overwrites matching `steamclient64.dll` named-export instructions and its entry point, and suppresses the original DLL entry. N `get_mem_from_steamclient_dll` also allocates interface/data storage inside that loaded image's `.data` section. Original files on disk would not make these mapped images unchanged. The FEX patch build reuses this detour with an AArch64 shim and separate native/guest ntdll hook sites; binary-hash/offset resolution adds Wine-build coupling.

Consequently this inspected path is **not an unchanged drop-in candidate within the approved no-Valve-binary-rewriting scope**. Its ABI wrappers, conversion tables and source organization are separable reuse candidates. A compatible entry mechanism is missing; devising or implementing one is not authorized here. This finding does not prove that every possible bridge is impossible or that broad WoW64 is therefore required.

### Build, host architecture, maintenance and terms

| Component | Source declaration / reusable material | Missing evidence and maintenance burden |
|---|---|---|
| lsteamclient baseline and overlays | N `fetch.sh` pins P `164e0ccd2ea2b1ec2e5d08dc97f65b184c2539ca`, declares 3,133 baseline files and digest `b286df1df46a70d9e2cc674676afcc6e08b1a56ce472e5add0932b86940657bf`, then overlays three authored files. | Only 19 selected P files were acquired and verified; the full digest was not recomputed. Generated interfaces, SDK revisions, manual callbacks and client changes require coordinated regression checks. No source generator/build was run. |
| Source build and Wine | N lsteamclient build supports PE i386/x64 and a Unix Mach-O target matching the Wine loader, default x86_64 or explicit arm64. `bridge/setup-wine-tree.sh` pins Wine 11.15 `2df1ee28039cf84776eb1421ed90bd154cebb65f`; Makefile has a separate ARM64 Unix tree. | This Wine differs from Pear's pin. Availability of an ARM64 build option does not establish a working ARM64 bridge or all required slices. Both PE targets in a build do not prove both are needed by Megabonk. ntdll Unix-call and loader contracts must be reconciled. |
| Steam shim headers | N `fetch-headers.sh` pins OpenVR `f51d87ecf8f7903e859b0aa4d617ff1e5f33db5a` and Wine header commit `015230dc0f78a543032dea0907f6c97304b25ca3`; Steamworks SDK 142 comes from P. | Declared header digests are source references, not newly verified full dependency closure. The shipped shim build is x64 PE. Source build, selected toolchains and linked modules remain unperformed. |
| Launch/runtime dependencies | N `compat_run.sh` selects the macOS Steam client root, real Valve guest client/support DLLs, lsteamclient DLL/Unix library, shim and patched runner. README targets particular Steam/CrossOver builds and recommends Rosetta over its early FEX option. | Required Wine/FEX/ntdll, bridge Unix library, genuine macOS Steam/helper/library selected slices and game-required guest modules need complete process/module evidence. Neither an ARM64 launcher nor SDK library proves Rosetta absence. The source's runner-file checks merely diagnose presence, not this closure. |
| Loader/client updates | N detours, data allocation in Valve images, resolver/build scripts and callback tables expose specific binary/layout coupling. | Client update, interface additions, SDK payload layouts, Wine internal offsets and FEX re-entry affect independent boundaries. No defensible effort or reliability ranking follows without a compatible entry design and measured closure. |
| File-specific terms | N `NOTICE` declares bulk GPLv3; `LICENSE.lsteamclient` and P `lsteamclient/LICENSE` are identical Steamworks SDK terms; `LICENSE.steam-shim` is BSD-3-Clause. SDK headers retain their terms; OpenVR/Wine headers and upstream helper dependencies retain their separate notices. | Public availability does not confer a blanket license or distribution qualification. The targeted selection is not a full redistributable bill of materials. Preserve Wine LGPL, FEX MIT and its no-AI-upstream-contribution rule, and Madeira/Dock component exceptions. No upstream contribution, relicensing or publication is performed. |

### Comparative result for the next decision stage

| Candidate scope | Reuse supported by this source review | What remains required before an investment decision can become implementation |
|---|---|---|
| A concretely required Dock i386 helper | Existing Wine/FEX i386 CPU/syscall/context and VM bookkeeping are the primary reuse candidates. Selected SteamService bytes are i386, but dynamic necessity is unknown. | Name the actual required phase/helper and original bytes first; then scope its missing Pear contracts. Absence before the current failure does not prove absence later. #11 continues its independent minimum run and x64 diagnosis. |
| Full official Windows bootstrap/desktop | Same existing components, with an established original PE32 installer input and broader mixed-bitness client/service/web-helper problem. | Fixed-base/non-LAA admission, original i386 execution categories, full process/module closure and client lifecycle remain separate obligations. Installer bitness cannot transfer those obligations to every Megabonk route. |
| Existing macOS Steam bridge reuse | Concrete native interface forwards, generated Windows/Unix wrappers, callback conversion and genuine-session setup code exist. | Existing entry rewrites Valve images and patched ntdll; a scope-compatible entry is missing. Actual original-game API/callback/session behavior, all required Rosetta-free host components, build closure and maintenance must still be established. Native Steam existence does not make this easier or working. |

Stage 2 supplies this bounded comparison before any substantial loader/memory/ABI recommendation. Stage 3 may turn the precise remaining evidence gaps into a minimum experiment proposal after continuation approval. It does not turn the bridge comparison into a new #11 gate, select a new low-address ABI, authorize a bridge build, or waive a demonstrated required helper.

### Stage 3 dated context and investment decision

The requester approved Stage 3 after `2833306`; this is an investment/experiment proposal, not implementation permission. The [Stage 3 observations](../working/task_m1_44_stage3_observations.json) bind 23 input files, the October 10 public #44/#11/#10 Issue snapshots and the peer checkpoints. The previous ledgers/reports match committed bytes; their source conclusions are reused without another source-wide hash sweep or runtime replay.

At this decision checkpoint #11 remains at `504f19d964ce948d770043349af7fa7d75500662` and #10 at `37395ee04abd55ec67faa2e1b381f30ab47a9be4`. #11's sanitized direct-stall receipt (`9303466d8b248abda52d025bc3cd0be520a1f0003176d6093a5e805d453d9ee5`) records no new game execution. It attributes repeated native resumes in the two retained direct-game timeout runs to `LookupCache::AddL1Entry`, with no source-guard/illegal-instruction record in those runs. Fault address/access type, commit post-state and forward progress remain missing. The receipt explicitly does not establish the same cause as Dock's `FinishPearDispatcherGate` refusal. This is receipt-level reuse, not #44 binary/debugger verification. The latest available #10 Stage 2 report qualifies declared process fixtures; it expressly leaves module storage/content binding, runtime hooks and complete coverage unperformed. None of these updates changes the historical Stage 1/2 evidence.

**Recommendation:** continue #11's selected-route work and its independently owned x64 diagnosis. Do not begin a broad WoW64 implementation or adopt the inspected bridge based on the current evidence. No i386 helper's required execution is yet demonstrated on the selected Dock/game route; its necessity remains unknown, not absent. If #11 demonstrates a required i386 helper, its unsupported execution becomes a blocker for that phase, and the preferred reuse direction is a separately reviewed targeted correction using existing Wine C and FEX C++/assembly. The installer alone is not that trigger.

The bounded native-bridge comparison is complete for this research decision. It finds useful wrapper/conversion source and a concrete incompatibility in the current entry mechanism, plus missing game/session/host-closure evidence. It does not establish that every bridge is impossible or that WoW64 is cheaper. A bridge implementation is deferred pending a scope-compatible entry review; full official Windows bootstrap/desktop is a separately chosen capability. This is a scope and evidence judgment, not a measured engineering-cost estimate.

The nearest useful additional evidence is **E0**, obtained through #11's existing ownership, without another #44 runner. The smallest conditional *new host diagnostic* is **E1**, after its concrete fixture/authorization review. E2-E4 describe later gates for an actually justified i386 correction; they are not a combined implementation request. E5 and E6 are alternatives with separate investment decisions. Failure or absence of an alternative does not suspend #11 or waive a required helper.

### Conditional minimum experiment proposal

All entries below are **design proposals only**. There is no newly executable diagnostic, PE32 adapter, i386 runtime candidate or compatible native-bridge candidate in this task. Current tool/source paths identify reuse points, not runnable commands for the proposed cases. Approval must select a concrete experiment and its source/input/run contract; it does not approve the entire sequence by implication.

Common prerequisites for any later native execution are exact source/ordered patch, generator/fixture, compiler/SDK, candidate/binary and selected dependency identities; an owned isolated run directory; current per-executable signing/provisioning authorization under normal macOS protections; actual supervision and observation interfaces; before/after input integrity; and a component-specific build/storage budget with cleanup and retention. Do not infer executable authorization from a parent's entitlement or an old successful signature. Account operations retain the owner's explicit scope and real Steam flow.

The Stage 3 read-only filesystem check observed 17,643,073,536 available bytes. This is a transient availability value, not a build-space estimate. Native compiler/SDK/dependency readiness, new executable authorization and an independent native i386 reference were **not checked**. No native lock was inspected or acquired. Future native work must coordinate `/private/tmp/pear-native-compilation.lock` without stealing/deleting it and remeasure disk/headroom before acquisition/build. Numeric run/output bounds must be selected in each reviewed producer contract; no future command is fabricated here.

#### E0 — Attribute a required helper on the selected Dock route

Priority: Nearest useful evidence; reuse owner work, not a new #44 runner. Owner: #11 with #10 observation contracts.

Claim: Whether an exact i386 process is required by the selected game phase, rather than merely installed.

| Field | Proposed requirement |
|---|---|
| Admission prerequisites | Owner-selected original Dock/client/game/prerequisite identities and invocation phase; current no-account failure cannot prove later absence. A separately approved next #11 run, existing APISession/supervisor ownership and the actual available #10 coverage contract. Do not repeat current failures only to restate them; consume new owner evidence when available. |
| Exact inputs / unresolved selection | Dock origin x64 SHA-256 a3762fdfb90b962f67e09ae5f3f61df8e1b700c9d52c7d5c08e3bf9e5bb8c3b7 Selected SteamService.exe SHA-256 72a406a6a2d3e282ab4b468ed8bfadf171fdd03a97969d6214a5da6fdb8dbd03 (i386); its necessity is unknown. Exact owner-selected Wine services.exe and game CEG/prerequisite manifest are still missing, not inferred from paths. |
| Command/interface status | Consume #11 sanitized selected-component/launch receipts through its reviewed existing adapters. No new callable or command is selected by #44. |
| Positive observations | Bind phase, parent/process instance, exact helper bytes/machine and the required action to observed invocation and its outcome. Record complete required-set coverage if concluding that a phase uses no i386 helper; an earlier failure cannot support that conclusion. |
| Refusal controls | Missing process/module interval, unselected helper or incomplete prerequisite/CEG evidence -> unknown, never x64-only success. A required helper that cannot run -> blocker for that phase; no skip, service-disable shortcut or fake readiness. Helper exit zero without SCM readiness is insufficient. |
| Resource bounds | Owner-approved finite run/output limits and measured selected closure; no additional #44 native work. |
| Cleanup | Only the actual owner may reap its child/process group; preserve pre-existing SCM/client processes and unrelated sentinel. Keep failures and cleanup gaps. |
| Retained evidence | Allowlisted file hashes, phase/parent/required classification, coverage gaps and outcome; no account/session identifiers or raw private traces. |
| Decision unlocked | If required i386 execution is demonstrated, prepare targeted FEX/Wine contracts E1-E4 for review. Otherwise retain unknowns and continue #11 without a broad WoW64 gate. |

Status: **Proposed, not performed; implementation and execution require separate approval.**

#### E1 — Isolated low-address ordinary host-NX feasibility

Priority: Smallest conditional host diagnostic; design approval first. Owner: Separately assigned runtime/host owner coordinated with #11.

Claim: Whether a bounded low identity-address data reservation can coexist with Pear on the selected host without replacing unowned mappings.

| Field | Proposed requirement |
|---|---|
| Admission prerequisites | A reviewed original C fixture and allocator/query adapter, exact source/compiler/SDK/executable hashes, per-executable current authorization, reviewed run contract. One existing high MAP_JIT owner remains unchanged; no second JIT owner or adopted guest-offset ABI. Select actual usable aligned addresses from availability; do not assume 0x00400000 or any hint is free. |
| Exact inputs / unresolved selection | Original redistributable NX-only host fixture; no Steam or game input. Selected macOS/architecture/page geometry, actual mapping/protection query results, candidate reservation policy and source identity. |
| Command/interface status | Design work: a new bounded case using existing owned native supervision/authorization primitives. tools/wine/pe_arena_probe.py contains executable/fault modes and is not this diagnostic or an approved command. |
| Positive observations | Reserve at most 64 MiB aggregate ordinary host-NX data below 0x80000000 with checked end/size/alignment; query actual RW/NX, write/read owned bytes and release. Observe unchanged high-owner base/identity/generation/protection before/after when a high owner is present; standalone host success without it has the narrower claim only. Exercise bounded owned reservation reuse and clean rollback without changing unowned mappings. |
| Refusal controls | Owned occupied-range control must fail without replacement and preserve its sentinel bytes; never MAP_FIXED over unowned memory. Invalid alignment, range overflow, unavailable range, budget exhaustion and injected partial setup failure yield explicit error plus cleanup. Protection query unavailable -> unknown/refused; do not execute data or deliberately fault native code to establish NX. Busy/stale domain or generation request is rejected; no release of another owner. |
| Resource bounds | Proposed initial <=64 MiB aggregate low reservation/commit including control ranges, below 2 GiB; one owned child per case, at most 12 declared cases, 10 seconds per child and 256 KiB output per case. Supervisory termination/drain limits must be bound to the reviewed owner contract. This is not measured Steam capacity. |
| Cleanup | Release only owned ranges after readers/writers retire; query release, preserve unowned sentinel and high owner; retain original failure if cleanup also fails. |
| Retained evidence | Source/binary/candidate hash, actual queried intervals/protections, OS errors, conflict/refusal and before/after ownership/cleanup receipts. |
| Decision unlocked | Pass establishes only host feasibility. Failure at one tested layout does not prove all low-address designs impossible. Neither outcome authorizes E2 or a memory ABI. |

Status: **Proposed, not performed; implementation and execution require separate approval.**

#### E2 — PE32 parser plus actual Wine owner mapping at admitted low bases

Priority: Conditional after concrete owner/PE32 design approval. Owner: One shared Wine loader owner; accepted #40 baseline first.

Claim: Whether exact PE32 semantics and canonical Wine bookkeeping work in the proposed candidate, including original fixed-base images.

| Field | Proposed requirement |
|---|---|
| Admission prerequisites | E1 is a feasibility input, not integrated admission. Review owner/base/role/domain/generation/32-bit fields, publication, rollback, low range and cleanup first. Construct the accepted #40 ordered source and recheck any later accepted #11 overlapping patch preimages. Review a PE32 extension to existing parser/fixture machinery; current tests/wine/test_pe_arena.py materializes older publication/cookie patches, so do not call it proof of the final composed candidate. |
| Exact inputs / unresolved selection | New original redistributable PE32 relocatable fixture with source/build/hash receipt, imports, known load-config/cookie layout and four-byte canary-surrounded targets. Original fixed-base, non-LAA, relocation-stripped fixture; two genuinely available admitted low bases for the relocatable fixture. Unchanged SteamSetup.exe 2380800 bytes, SHA-256 7d3654531c32d941b8cae81c4137fc542172bfa9635f169cb392f245a0a12bcb, preferred base 0x00400000, only for separately approved original-image parsing/admission; never add synthetic relocations. Existing original PE32+/ARM64X and #40 required/ceiling/beyond/failed-attach controls. |
| Command/interface status | Design work: extend existing parser and image-admission tooling against the actual composed candidate; no ready PE32 CLI exists here. Split parser-only results from actual Wine reserve/map/protect/query/free/unmap results. |
| Positive observations | At two admitted low bases, HIGHLOW changes exactly four bytes to the expected value and preserves adjacent canaries; image/import/load-config addresses remain representable. Validate PE32 security-cookie pointer width and complete field/directory bounds, initialized value and legal storage protection; retain PE32+ eight-byte controls. Fixed-base fixture loads only at its available preferred base within non-LAA limits; actual Wine views/server and owner records agree through reserve/commit/protect/query/unmap/release. Unchanged #40 64 MiB image bound and high owner stay valid; parser pass alone does not claim guest execution. |
| Refusal controls | Malformed/truncated optional header, directory or load config; incorrect field width; unsupported relocation type; malformed/duplicate/overlapping relocations; target overflow/out-of-image or metadata overlap -> precise refusal. Relocation arithmetic follows reviewed Windows 32-bit semantics; distinguish legal modulo arithmetic from invalid mapped address/size overflow, with independent expected values. Occupied preferred address for relocation-stripped/non-LAA fixture -> refuse without relocation or overwrite; preserve the occupying mapping. Failure after reserve/map/prepare/publication/attach rolls back only owned state and preserves canonical VM error plus cleanup status. |
| Resource bounds | Proposed parser-only limits: fixture <=8 MiB, 5 seconds and 256 KiB output per case. Actual loader cases: initial low budget <=64 MiB, 20 seconds and 1 MiB output per child, with the reviewed owner cleanup contract. Bound case manifest and measured build/disk budget before execution; do not apply fixture file caps to proprietary installer/desktop capacity. |
| Cleanup | All successful and refused paths retire source/translation references before range reuse; no stale view, published mapping, handle or owner record remains. |
| Retained evidence | Exact composed-source/patch preimages, producer/fixture hashes, parser statuses, field/canary bytes and actual Wine/owner before-after events. |
| Decision unlocked | Only complete mapping/cleanup evidence permits proposing i386 guest entry. Original installer execution remains a later separate route test. |

Status: **Proposed, not performed; implementation and execution require separate approval.**

#### E3 — Original i386 execution and lifecycle fixtures

Priority: Conditional after admitted source/owner and a reviewed WoW64 adapter. Owner: FEX/Wine runtime owner; coordinate #6 and #42 boundaries.

Claim: Whether i386 dispatch, Windows ABI and lifetime semantics work beyond initial CPU entry.

| Field | Proposed requirement |
|---|---|
| Admission prerequisites | Actual i386 builtin ntdll/import closure, native wow64/wow64win/CPU module and complete host target identities. Preserve unsupported guards until each concrete implementation/contract is approved; no wholesale removal. Redistributable original i386 fixtures and independent same-byte native x86 reference where meaningful; reference host availability is not checked. A native x86 CPU Windows WoW64 reference must identify its actual architecture. |
| Exact inputs / unresolved selection | Fixed fixture source/assembler/compiler/oracle bytes and expected event sequences; no proprietary files. Final Wine/FEX candidate, thread/context/exception/notification producer identities, affected #6 reference receipts. |
| Command/interface status | Design work: reuse the current CPU capture/comparison and owned Wine/FEX supervision machinery with separately reviewed i386 cases/adapter. Existing x64 command results are not i386 qualification. |
| Positive observations | Exit/syscall and Unix-call return values, calling convention/stack cleanup, 32-bit register/address/handle semantics. Two-thread GDT/FS/TLS isolation and join/retirement; repeat thread creation without stale identities. Handled guest exception and resumption with expected registers/flags and x87/XMM state; original unaligned guest access including the reviewed boundary case. Guest->host->guest callback and nested/re-entrant return; required cross-thread callback behavior with actual thread identity and buffer lifetime. Dirty/protect/free/map/unmap invalidation, rewrite/retranslation, unload and same-address reuse under a new generation; no stale compiled link or active callback released early. |
| Refusal controls | Unsupported context/segment/ISA behavior stays unsupported; AVX/XSTATE is #42, not silently exposed. Foreign/stale thread or generation, busy retirement, callback after release and invalid notification pairing -> attributable refusal without host fatal fault. Missing native reference, wrong fixture/candidate hash, incomplete callback/exception event or lost observer interval -> unqualified. Do not substitute native fatal-fault/no-TEB routes or aligned/static fixture successes for original guest cases. |
| Resource bounds | Proposed initial per-case bound: 20 seconds and 4 MiB combined output per owned child, two guest workers for thread/TLS/callback cases, finite declared iteration counts. Separate affected existing ordering regression retains its original 32768-pair scope. Review measured candidate/build space before any native work. |
| Cleanup | Drain callbacks and invalidate links before unload; join/reap owned children/threads, balance handles/leases and preserve unrelated processes and original failures. |
| Retained evidence | Original fixture hashes, independent reference environment/oracles, per-case comparison and refusals, actual native/guest module identities, lifecycle and cleanup receipts. |
| Decision unlocked | Pass qualifies only the named i386 fixture set on that candidate; it does not qualify Steam desktop or an actual required helper. |

Status: **Proposed, not performed; implementation and execution require separate approval.**

#### E4 — Execute only a demonstrated required original i386 helper

Priority: Conditional #11 integration, not broad desktop admission. Owner: #11 with accepted runtime correction and #10 coverage.

Claim: Whether the actual required helper completes its function and preserves the genuine game/client session.

| Field | Proposed requirement |
|---|---|
| Admission prerequisites | E0 identifies required helper/phase and unchanged original bytes; E2/E3 plus all affected regressions qualify the new candidate. Review actual process/service supervision and per-executable authorization; existing manager may not own a pre-existing SCM/service. Any real account action requires the owner current approval and existing authentication path, not inherited downloader login. |
| Exact inputs / unresolved selection | Exact selected helper, dependencies, invocation arguments and required readiness/outcome predicate from #11 receipts. Normal selected Dock/client/game context and candidate hashes; actual service binary selection rather than system32/path inference. |
| Command/interface status | Extend/reuse the reviewed #11 route adapter under its owner. No duplicated auth client, observer, supervisor or full runner. |
| Positive observations | Required helper action and readiness succeed with attributable original process/module closure, return and cleanup. Normal genuine Valve launch leads to the owning-account App ID session and required original-game API/callback outcomes; retain failed/unknown phases separately. |
| Refusal controls | Exit-zero-only, DLL-load-only, global-user-only, launch-only or menu-only evidence does not establish complete Steamworks. Unavailable entitlement/session or disconnect yields real failure; never forge success, add supported steam_appid.txt or alter game/Valve bytes. Any required Rosetta host component or coverage gap blocks Rosetta-free qualification. |
| Resource bounds | Owner-selected finite helper/run/output bounds and measured dependency/prefix storage, preserved original files and saves. |
| Cleanup | Only owned process/service instances stopped/reaped; preserve pre-existing client/SCM, original files and account state; record unresolved cleanup. |
| Retained evidence | Sanitized required-phase outcomes, module/slice/translation coverage and ownership/session assertion results without identifiers, tokens or tickets. |
| Decision unlocked | Success addresses the named helper route only. Other desktop i386 components remain a separate capability. |

Status: **Proposed, not performed; implementation and execution require separate approval.**

#### E5 — Reconsider existing native bridge only after a compatible entry review

Priority: Deferred alternative; not the next runtime implementation recommendation. Owner: Separately approved bridge evaluation with #11/#10 contracts.

Claim: Whether reusable existing wrappers can support unchanged Windows-game semantics through an entirely Rosetta-free genuine native Steam session.

| Field | Proposed requirement |
|---|---|
| Admission prerequisites | First present a source-level entry design that does not rewrite Valve/game images or modify installed Steam/CrossOver, and passes Pear source/lifetime contracts. None is selected here. Pin complete build/SDK/header/Unix-call dependencies and file-specific terms; reconcile NotProton Wine 2df1ee... with Pear, retain upstream languages. Read-only inventory of explicitly selected non-authenticated native client/helper/library bytes may screen architecture, but cannot substitute dynamic complete required closure. A later execution scope must authorize its exact fixtures/client/account operations and original game selection separately. |
| Exact inputs / unresolved selection | NotProton c3a49486c14cdf6b9716e2e7ac55286aa537fcf1 and Proton 164e0ccd2ea2b1ec2e5d08dc97f65b184c2539ca wrappers/conversions; full dependency closure remains missing. Actual original game interface versions, callback IDs/layouts and session requirements, not just the representative Apps008/SteamClient021/LobbyCreated example. |
| Command/interface status | No runnable bridge command is proposed: existing detour/compat_run/build scripts are outside the approved adoption scope. After a compatible design, separately review source build, layout/callback fixture, then original-game session experiments. |
| Positive observations | Source-built selected ARM64 host components and Windows wrappers match their pinned ABI/layout tests, including callback payload and asynchronous result lifetime. Original game reaches real ownership/session methods; callback polling, nested/thread return, shutdown/disconnect/reconnect and call-result failure behave correctly. Every required actual Steam/helper/bridge/Wine/FEX native process/library is observed on ARM64 without Rosetta for the required interval; no incomplete late-load coverage. |
| Refusal controls | Valve image rewrite or commercial installed-binary dependency -> outside candidate scope, not a passing experiment. Wrong/unsupported interface, layout, late callback, shutdown race, failed call result or genuine entitlement/session failure -> real refusal, not success substitute. Native launcher, ARM64 SDK slice, successful init or downloader authentication alone -> insufficient. Required Intel-only host component or unobserved required interval -> route not qualified. |
| Resource bounds | Source-first review before full acquisition/build; enumerate missing artifacts and measured disk/time/output bounds. No cost estimate inferred from macOS Steam availability. |
| Cleanup | Own only isolated evaluation artifacts/processes; no installed-client patches; preserve originals/account state, release pipes/users/callback buffers and retain failures. |
| Retained evidence | Complete candidate and client pins, real interface/layout results, sanitized session outcomes, process/module closure, dependency notices and update regression checklist. |
| Decision unlocked | Only new compatible-entry plus measured evidence reopens route comparison. Current source availability does not justify adopting or claiming this route easier. |

Status: **Proposed, not performed; implementation and execution require separate approval.**

#### E6 — Official Windows bootstrap and desktop qualification

Priority: Independent capability; defer unless separately requested. Owner: Separately scoped Steam desktop/WoW64 task.

Claim: Whether the full original mixed-bitness installer/update/login/desktop route works.

| Field | Proposed requirement |
|---|---|
| Admission prerequisites | Explicit decision to invest in desktop capability independently of #11. Original fixed-base installer admission, i386 lifecycle qualification, selected complete mixed-bitness dependencies and reviewed authenticated execution scope. |
| Exact inputs / unresolved selection | Unchanged installer hash from E2 and exact selected steam.exe/service/web-helper/client versions and bytes. |
| Command/interface status | No desktop implementation or execution command is selected by #44. Reuse existing owned supervision and Steam authentication interfaces after design review. |
| Positive observations | Original bootstrap/install/update/startup and genuine sign-in/game launch complete with full required module/child observation. |
| Refusal controls | Fixed-base conflict, unsupported helper/ABI or required Rosetta process remains a route failure; no binary edits or bypass of services/ownership. |
| Resource bounds | Separately measured full desktop storage/memory/build/run budget; the 64 MiB diagnostic is not a product limit. |
| Cleanup | Isolated owned prefix/runtime with account/save preservation and owned-process cleanup; original inputs unchanged. |
| Retained evidence | Sanitized selected-build identity, per-phase outcomes, full required closure and update/recovery evidence. |
| Decision unlocked | Desktop success/failure has its own scope and does not retroactively impose its installer requirements on Dock. |

Status: **Proposed, not performed; implementation and execution require separate approval.**

### Shared owners, exact preimages and evidence invalidation

| Shared boundary | Accepted or inspected input | Required order / ownership |
|---|---|---|
| Integrated Wine arena | Master `942bd816913d8792c55f821fdc2ad309b1b85daf` includes #40. `0001-admission-diagnostics` followed by `0002-image-admission`; Stage 2 ledger records all patch hashes and before/after values. After both: `pear_pe_arena.c` = `4b91a66df05791bba2d454dd5c3c2131a3dffea339f9608db29c9ed68457d6de`; header = `dccb37fd2f3506ac95539f8c084860f426b338976862e734b6e307df87a228a3`; `virtual.c` = `624b909228b6e3329355b0d8cde2a60bd98c6fa84f7f2cc2d59a0118e05d15f4`. These are accepted patch metadata postimages, not newly materialized sources. | Preserve 64 MiB image correction and unchanged arena geometry. A future correction must compare actual materialized preimages, never apply an older composed file over accepted changes. One source owner for common Wine loader/owner work. |
| FEX WoW64 adapter | Retained `Source/Windows/WOW64/Module.cpp` SHA-256 `4a9211abb2155c1d633ac4d52d7dd49fa4727771d97c10f7e0ff540529e9f221`, manifest `2ffc47a300c2c1ca3dd0a36bd40bc7e4c95a455278b7c8fcf47ea739b04e94cb`. | Historical composed preimage only. Bind any approved patch to the accepted full series and actual source bytes. Do not remove unsupported paths without implementing and qualifying their paired contracts. |
| Shared FEX memory/entry | Retained `Source/Windows/ARM64EC/Module.cpp` = `8ef07e19ea8da75fe5af4dd9f2733ebc27c2161667b48112fcf25fd75dfbbca9`; `Source/Windows/Common/OvercommitTracker.h` = `cb0d569bd1f9189160da36fd3f74af510e6a4016072bc0c76859923ae45bfea7`; `FEXCore/Source/Interface/Core/Core.cpp` = `037fc86f0ec46c5e9d89bbf44c617409dd4d663fbe4b7aea774a7c5e014a3518`. | #11 owns current x64 direct-startup investigation, including LookupCache/overcommit/resume. No #11 correction is selected or integrated by #44. Order is accepted #40 baseline -> separately reviewed overlapping #11 correction if any -> separately approved #44 correction. Recalculate exact postimages after any accepted change. |
| Build/patch series | `runtime/fex/patches/integration/{series,fex-series}.json` and #40 patch metadata are hash-bound in Stage 3 inputs. | These are provenance dependencies, not approval to rebuild. Recheck materialization order, per-file attribution and source/ABI changes before future work. Retain upstream languages and component licenses/contribution rules. |
| Route and observation | #11 exact selected Dock/client/helper/game receipts; #10 final accepted process/module and registration contracts, not its incomplete Stage 2 coverage. | #11 owns authentication, normal launch, menu/Steamworks; #9 owns supervision and #10 observation. Reuse their accepted APIs rather than duplicate them. No implementation dependency on all #44 research. |
| ISA and graphics | #42 owns AVX/XSTATE; #6/#8/#40 remain finite existing qualification scopes. | Do not explain a timeout as AVX/GC/Steam failure without attribution. Apply affected regressions and relevant Apple guidance only to later approved native/graphics work. |

A changed input, fixture, producer, compiler/SDK, configuration, patch order or runtime artifact invalidates the affected build/execution claim. A changed source/client/API version invalidates the affected static/bridge comparison. Rebind the final candidate and rerun affected gates; do not carry a pass merely because a filename is unchanged. An independent native reference can be reused only when its exact fixture/capture/oracle inputs and claim scope remain valid. Missing process/module or account evidence cannot be repaired by document checks.

For a later shared loader/memory/ABI change, preserve the full **affected** regression obligations: #6's 18 supported CPU cases against original independent references, explicit AVX unsupported/not-exposed result and 32,768 ordering pairs with policy/retirement checks; #40's parser/loader/cleanup and 64 MiB required/ceiling/beyond/failed-attach cases plus its original limited GameAssembly initialization claim; and #8's native 39/v2 surface 23 controls, device, five rendering cases/seven readbacks, 18 individual visible frames with resize/teardown, both unchanged original scalar-fault fixtures and balanced physical lifetime. Do not substitute two boundary cases or a rebuilt fixture for the original corpus/failure bytes. Reuse unaffected evidence with unchanged inputs; no native suite was run merely for this documentation proposal.

References for these obligations: [#6 CPU comparison](../working/task_m1_6_stage2.md), [#6 reference review](../working/task_m1_6_stage3_reference_review.md), [#8 Stage 3](../working/task_m1_8_stage3.md), [#40 Stage 3](../working/task_m1_40_stage3.md). Full candidate regression is distinct from #10 complete runtime architecture coverage and original-game Steamworks qualification.

### Research acceptance map and final-report handoff

The following maps the seven #44 acceptance criteria. **Satisfied** means the bounded research artifact is complete with explicit limits, not that the proposed runtime behavior passed. This prepares the evidence mapping for the later final-report/publication procedure; no Issue checkbox, PR or closure is changed here.

| Criterion | Research result | Evidence and remaining runtime boundary |
|---|---|---|
| AC1 — Separate route requirements | Satisfied | Stage 1 route/phase matrix and byte-bound selected i386 service versus installer; actual helper necessity/closure unknown. |
| AC2 — Limited existing bridge comparison before substantial changes | Satisfied | Stage 2 all five criteria and representative call/callback return path; existing-entry incompatibility, original-game session and full required host closure remain explicit. E5 records conditions for reconsideration. |
| AC3 — Reuse and missing function/dependency contracts | Satisfied | Wine/FEX source/refusal matrix covers PE32/fixed-base, address/context/exception/thread/mutation and retirement; E1-E3 name corresponding future observations without suppressing guards. |
| AC4 — Provenance, terms, owners and invalidation | Satisfied | Stage 1/2 source and notice pins, Stage 3 input/preimage/ownership table and invalidation policy. No blanket license/distribution or upstream contribution approval. |
| AC5 — Concrete minimum experiments | Satisfied | E0-E6 each identify claim, known/missing inputs, interface availability, positive/refusal results, authority, resources, cleanup and evidence. E1 is the smallest conditional new host diagnostic. None executed. |
| AC6 — Precise #11 impact | Satisfied | No required i386 execution demonstrated yet; installed i386 bytes alone do not block. A demonstrated required unsupported helper blocks its affected phase. No bridge/desktop completion gate added. |
| AC7 — Reviewable decision/continuation | Satisfied | Retain independent #11 work, prefer conditional targeted Wine/FEX reuse, defer existing bridge adoption and independently scope desktop support. Research review/publication and any experiment/implementation are distinct decisions. |

## Decisions

- Preserve two Windows route scopes and the independent #11 Dock minimum validation. No universally required i386 Dock helper is demonstrated by the Stage 1 inputs; this is **unknown necessity**, not evidence that i386 can be omitted.
- Reuse the matching historical source/parser evidence within its recorded scope. Do not repeat the known parser refusal or execute peer adapters merely to recover it.
- Carry actual conditional services and prerequisite ownership boundaries into E0/E4; #11 remains the route owner.
- Retain Wine C and FEX C++/assembly for a separately approved required-helper correction. The bounded native-bridge review is complete; it supports conditional reuse of wrappers, not adoption of its existing entry. Broad desktop work is separately scoped.

## Non-decisions / Deferred Items

- WoW64 implementation, low-memory owner design, fixed-base admission and ABI changes are unapproved. Stages 2 and 3 record source contracts and conditional experiment proposals above; none is implemented or executed.
- No actual selected helper closure, Megabonk CEG/prerequisite requirement, original-game Steamworks success or full Rosetta-free path has been measured here.
- NotProton actual-game feasibility, comparative effort and full distribution/build closure remain open; Stage 2 records the targeted file-specific license/build review and existing-entry incompatibility. Existing Wine LGPL, FEX MIT plus no-AI-upstream-contribution rule, Dock GPL/exception/runtime notices and NotProton component-specific GPL/BSD/Steamworks SDK terms are preserved from the plan; no blanket license or distribution clearance is asserted.
- #40's merged correction precedes later shared-loader work; accepted #10 observer interfaces and #11 actual route inputs must be rechecked before integration. AVX/XSTATE remains #42.

## Implementation Impact

This stage edits only approved task research, evidence, plans and the #44 board row. It performs no source implementation, build, guest/native execution, game or Steam launch, login, signing, account-state inspection, runtime lock operation or proprietary acquisition. #11 continues independently. If later evidence proves a specific required i386 helper, its missing execution support is a blocker for that affected route and must not be waived.

## References

- [Approved task plan](../plans/task_m1_44.md), [research implementation plan](../plans/task_m1_44_impl.md), [Stage 1 observations](../working/task_m1_44_stage1_observations.json).
- [#11 Dock integration](https://github.com/postmelee/pear/issues/11), [#10 observation](https://github.com/postmelee/pear/issues/10), [#40 loader correction](https://github.com/postmelee/pear/issues/40), [#42 ISA/XSTATE follow-up](https://github.com/postmelee/pear/issues/42).
- [Pinned NotProton README](https://github.com/NotProtonNot/NotProton/blob/c3a49486c14cdf6b9716e2e7ac55286aa537fcf1/README.md), [NOTICE](https://github.com/NotProtonNot/NotProton/blob/c3a49486c14cdf6b9716e2e7ac55286aa537fcf1/NOTICE); Stage 1 candidate context from prior intake; Stage 2 source-contract review recorded above.
- Source URLs, full revisions, exact relative artifact paths and hashes are in the observation ledger. Peer-only uncommitted plans/receipts are identified by hash rather than represented as available in master.
