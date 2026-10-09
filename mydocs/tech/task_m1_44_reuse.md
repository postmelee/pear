# Task #44: Steam route requirements and reuse research

GitHub Issue: [#44](https://github.com/postmelee/pear/issues/44)
Date: October 10, 2026 (Asia/Seoul)
Scope: Stage 1, read-only research; Stage 2/3 comparisons and investment decision remain pending.

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

## Decisions

- Preserve two Windows route scopes and the independent #11 Dock minimum validation. No universally required i386 Dock helper is demonstrated by the Stage 1 inputs; this is **unknown necessity**, not evidence that i386 can be omitted.
- Reuse the matching historical source/parser evidence within its recorded scope. Do not repeat the known parser refusal or execute peer adapters merely to recover it.
- Carry actual conditional services and prerequisite ownership boundaries into later source comparison and future selected-input checks.
- Retain Wine C and FEX C++/assembly as candidates for any later justified i386 work. Review pinned existing native bridge contracts before substantial shared-runtime investment.

## Non-decisions / Deferred Items

- WoW64 implementation, low-memory owner design, fixed-base admission and ABI changes are unapproved. Stage 2 traces source contracts; Stage 3 makes the investment/experiment proposal.
- No actual selected helper closure, Megabonk CEG/prerequisite requirement, original-game Steamworks success or full Rosetta-free path has been measured here.
- NotProton feasibility, comparative effort and full file-specific license/build review remain open. Existing Wine LGPL, FEX MIT plus no-AI-upstream-contribution rule, Dock GPL/exception/runtime notices and NotProton component-specific GPL/BSD/Steamworks SDK terms are preserved from the plan; no blanket license or distribution clearance is asserted.
- #40's merged correction precedes later shared-loader work; accepted #10 observer interfaces and #11 actual route inputs must be rechecked before integration. AVX/XSTATE remains #42.

## Implementation Impact

This stage edits only approved task research, evidence, plans and the #44 board row. It performs no source implementation, build, guest/native execution, game or Steam launch, login, signing, account-state inspection, runtime lock operation or proprietary acquisition. #11 continues independently. If later evidence proves a specific required i386 helper, its missing execution support is a blocker for that affected route and must not be waived.

## References

- [Approved task plan](../plans/task_m1_44.md), [research implementation plan](../plans/task_m1_44_impl.md), [Stage 1 observations](../working/task_m1_44_stage1_observations.json).
- [#11 Dock integration](https://github.com/postmelee/pear/issues/11), [#10 observation](https://github.com/postmelee/pear/issues/10), [#40 loader correction](https://github.com/postmelee/pear/issues/40), [#42 ISA/XSTATE follow-up](https://github.com/postmelee/pear/issues/42).
- [Pinned NotProton README](https://github.com/NotProtonNot/NotProton/blob/c3a49486c14cdf6b9716e2e7ac55286aa537fcf1/README.md), [NOTICE](https://github.com/NotProtonNot/NotProton/blob/c3a49486c14cdf6b9716e2e7ac55286aa537fcf1/NOTICE); Stage 1 candidate context from prior intake, Stage 2 source-contract review pending.
- Source URLs, full revisions, exact relative artifact paths and hashes are in the observation ledger. Peer-only uncommitted plans/receipts are identified by hash rather than represented as available in master.
