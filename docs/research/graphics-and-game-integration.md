# Graphics and game integration audit

Checked: 2026-09-27. Scope: the Rosetta-independent Megabonk milestone for Pear.

This document separates local observations, upstream source evidence, and proposed acceptance criteria. It does not report a new runtime build or a Rosetta-independent game launch. Source links to `main`/`master` describe the state inspected on the date above; the implementation gate must replace them with commit-pinned inputs.

Source-audit follow-up, September 28, 2026: the [completed source qualification](../source-qualification.md) and [Issue #1 final report](../../mydocs/report/task_m1_1_report.md) record matching repeat acquisition, inspected patch/terms evidence and an explicit `blocked` source/build decision. Required Darwin integration remains `needs-port`; tools and configured dependency/notice closure remain unresolved. The original research below retains its historical date and scope.

## Decision

Use **DXMT's ARM64EC Windows components and ARM64 macOS components** as the primary D3D11 implementation to investigate. Integrate them with a compatible ARM64 Wine and FEX runtime as a versioned, tested unit. Retain the working Rosetta-based Wine/DXMT installation as a separate comparison environment.

The work is a runtime integration and potentially platform-porting project. Copying an ARM64EC `d3d11.dll` into the existing x86_64 host runtime is not a design. The runtime must establish Windows ABI transitions, Wine Unix-call interfaces, native Metal access, compatible shader conversion, process creation, and diagnostics across its entire dependency graph.

Rust is not needed to compile DXMT or to make its Metal path native. The current project is predominantly C/C++ and its build uses C++20. Existing C/C++ graphics code should remain in its upstream implementation language unless a measured problem justifies a bounded replacement. A Rust or Swift Pear launcher is a separate product decision. [DXMT build definition](https://github.com/3Shain/dxmt/blob/main/meson.build)

## What is already established locally

The private binary audit recorded these inputs:

| Item | Observation |
|---|---|
| Game | Megabonk, Steam App ID 3405340, Windows depot 3405342 |
| Windows manifest | 446680890915713051 |
| Game code | `GameAssembly.dll`, x86-64 PE, IL2CPP |
| Engine | Unity 2023.2.22f1 |
| Baseline host | M4 Pro, 24 GB, macOS 26.5.2 |
| Baseline runtime | frankea/Whisky Libraries 3.1.1, Wine 11.0, DXMT 0.80, Rosetta |
| Baseline graphics | D3D11 feature level 11_1, Metal, observed output 1512 × 982 |
| Observed gameplay | Main menu and Forest Tier 1; game frame caps of 30 and 60 visibly applied |
| Not established | Rosetta-free operation, complete late-game stability, controlled frame-time comparison, or a power advantage |

The previous power capture was a 120-second system-level measurement with an uncontrolled workload and a paused scene. It must not become Pear's performance baseline. A requested 1920 × 1200 resolution also differed from the observed output. Future results must use measured output dimensions and explicitly controlled power settings.

The Windows and Linux files are both x86-64 IL2CPP distributions. Linux libraries cannot be substituted for macOS libraries. The presence of Windows ARM64 Rewired plugins does not turn the x64 game into a native ARM64 application, and those plugins are not macOS libraries.

These observations are summarized in [Local evidence and limits](local-evidence.md), based on the private binary-audit and Wine/DXMT experiment records. Raw game files, account data, and proprietary extracted content remain outside the repository's published documents. The local observations have not yet been independently reproduced.

## Required execution boundaries

The intended flow is:

```text
Megabonk / Unity / game plugins: Windows x64 code
    │ x64 instructions handled by FEX
    │ Windows API and ABI transitions handled with Wine
    ▼
Wine ARM64EC system DLLs + DXMT ARM64EC D3D11/DXGI
    │ Wine Unix-call / winemetal boundary
    ▼
ARM64 Mach-O host libraries, shader conversion, Metal
    ▼
Apple GPU
```

This is a responsibility diagram, not a claim that every game call traverses every box. Guest x86-64 instructions may remain in the game and third-party DLLs. Rosetta independence requires their execution through the chosen translator, while the macOS host execution path remains native ARM64.

FEX's Windows modules handle CPU emulation; Wine/ABI handling supplies the system-call side. ARM64EC permits native ARM code and translated x64 code to coexist, while WoW64 covers a separate 32-bit path. Therefore the implementation must validate both directions of calls, callbacks, thread entry points, exception/unwind state, and module loading. A Linux FEX root filesystem is not automatically part of this Windows-module design. [FEX ARM64EC architecture and build notes](https://wiki.fex-emu.com/index.php/Development:ARM64EC)

## DXMT: evidence and remaining integration work

### Source and build evidence

The upstream repository contains an explicit ARM64EC cross file using the `arm64ec-w64-mingw32` toolchain and the Windows/aarch64 target. [Cross configuration](https://github.com/3Shain/dxmt/blob/main/build-arm64ec.txt)

The inspected CI defines both debug and release ARM64EC Windows builds, an ARM64 Darwin LLVM build, and packaging of ARM64EC output. Its inputs include LLVM 15.0.7, llvm-mingw 20260908, a `wine-11.2` ARM64EC build from `3Shain/wine`, Xcode 16.1, and Meson 1.10.0. This is stronger evidence than an unused cross file, but this audit did not reproduce the build or verify the upstream artifact's runtime behavior. A `wine-11.2` archive used to compile DXMT does not establish that its entire runtime is the macOS Wine/FEX stack Pear needs. [Upstream CI](https://github.com/3Shain/dxmt/blob/main/.github/workflows/ci.yml)

The development guide describes a mixed build: Windows PE DLLs plus a Mach-O Unix library. It also documents a fully native library build, which is useful for native applications but does not by itself load an existing Windows executable. Its introductory cross-build advice still emphasizes x86_64, so the ARM64EC CI and current source must be reconciled into a tested Pear build recipe. [Build guide](https://github.com/3Shain/dxmt/blob/main/docs/DEVELOPMENT.md)

The `winemetal` build links Wine components such as `ntdll` and `winecrt0`, then invokes Wine's `winebuild` tool. Its Unix side is built for the relevant host architecture. This is an ABI-coupled pair, not an interchangeable collection of DLLs. [winemetal build](https://github.com/3Shain/dxmt/blob/main/src/winemetal/meson.build)

DXMT's shader conversion code has LLVM dependencies and produces Metal shader artifacts. CPU translation and GPU shader conversion are separate problems; replacing FEX's code generator with another compiler would not replace the shader pipeline. [airconv build](https://github.com/3Shain/dxmt/blob/main/src/airconv/meson.build)

### Work required for Pear

1. Pin DXMT, its submodules, the Wine build interfaces, LLVM, llvm-mingw, Xcode/SDK, and build settings. Record where each patch originates and why it is needed.
2. Reproduce an ARM64EC cross build with ARM64 host libraries. Inspect output headers, dependencies, install paths, and code signatures. Host build tools and shipped runtime components must be inventoried separately.
3. Confirm the `winemac.drv` interfaces DXMT needs exist in the selected Wine port. The older installation guide explicitly requires extra exported interfaces and distinguishes builtin from native DLL installation. Translate those requirements to the selected ARM64 build; do not copy its x86_64 paths mechanically. [Installation contract](https://github.com/3Shain/dxmt/wiki/DXMT-Installation-Guide-for-Geeks)
4. Package Windows DLLs, `winemetal`, native libraries, and their matching configuration atomically. Preserve the bundle layout per runtime version and avoid mutating a shared runtime during a game launch.
5. Execute open, redistributable x64 D3D11 tests before Megabonk: device creation, buffer/texture upload, shaders, compute, depth/blend states, swap chain, resize, presentation, and callbacks across translated/native code.
6. Validate actual DLL selection and the renderer through logs and loaded-module evidence. A Metal HUD or an ARM64 launcher alone is insufficient.
7. Run Metal validation for targeted correctness tests, and disable validation layers during performance measurements. Keep shader cache versioning and cold/warm runs explicit.

Shader-cache invalidation, presentation pacing, and resource lifetime must be treated as correctness features. A profile cannot paper over an unstable renderer by silently dropping rendering features.

## Alternative graphics paths

| Candidate | Evidence | Role in Pear |
|---|---|---|
| DXMT | D3D10/11-to-Metal implementation; current ARM64EC build infrastructure; local Megabonk D3D11 baseline already works through its older x64 path | Primary candidate, subject to the build and runtime gates above |
| DXVK + Wine Vulkan + MoltenVK | DXVK implements D3D8/9/10/11 over Vulkan; MoltenVK implements a large Vulkan subset over Metal | Secondary compatibility experiment, not an assumed drop-in equivalent |
| WineD3D | Wine includes a D3D implementation and an OpenGL adapter | Diagnostic/comparison backend; verify the target game's feature requirements and correctness before claiming support |
| D3DMetal / Apple's evaluation environment | Apple provides a Windows-game evaluation path and Metal profiling tools | External reference where available under applicable terms; not the source-maintainable foundation selected here |

Upstream DXVK 3.x now asks for Vulkan 1.4 plus specific features, including transform feedback, robustness2, maintenance5/6, descriptor indexing, and scalar block layout. MoltenVK's current README describes an almost-complete Vulkan 1.4 subset and its portability enumeration requirement. Equal advertised Vulkan version numbers do not prove that every required feature is available. A viable alternative needs a capability dump for the actual Mac, SDK, MoltenVK build, and Wine Vulkan bridge, followed by D3D tests. Avoid both the stale claim that MoltenVK is limited to an older version and the unsupported claim that current DXVK automatically works. [DXVK requirements](https://github.com/doitsujin/dxvk/wiki/Driver-support), [MoltenVK overview](https://github.com/KhronosGroup/MoltenVK)

DXVK's scope and DLL layout are documented upstream; its mature implementation is useful comparative evidence, but its documented target is Linux/Wine. The extra Vulkan layer is not, by itself, proof of worse performance. [DXVK README](https://github.com/doitsujin/dxvk)

WineD3D's OpenGL implementation is available for source-level comparison. This audit did not establish a complete Megabonk feature match or benchmark it. [WineD3D OpenGL adapter](https://github.com/wine-mirror/wine/blob/master/dlls/wined3d/adapter_gl.c)

Apple's current Game Porting Toolkit page describes toolkit 4 and an evaluation environment with Metal 4 support. It does not establish that Pear can rebuild or maintain the complete evaluation runtime from source. The relevant binary license must be checked before any distribution; no redistribution conclusion follows merely from download availability. [Apple's toolkit overview](https://developer.apple.com/games/game-porting-toolkit/)

## Steam is part of the milestone

### Local file architecture inventory

On 2026-09-27, `file` was run read-only on selected installed binaries. No game or Steam process was launched or changed during this audit.

| File group | Observed architecture |
|---|---|
| `Megabonk.exe`, `UnityPlayer.dll`, `GameAssembly.dll` | Windows x86-64 PE |
| Game `steam_api64.dll`, Discord SDK, x86_64 Rewired plugins | Windows x86-64 PE |
| Game `Plugins/ARM64` Rewired plugins | Windows Aarch64 PE; not evidence of loading into the x64 game |
| Installed `Steam/steam.exe`, `steamclient64.dll` | Windows x86-64 PE |
| `cef.win64` and `cef.win7x64` Steam web helpers | Windows x86-64 PE |
| `steamclient.dll`, `cef.win7` helper, Common Files Steam service | Windows i386 PE |

The installed Steam executable is x64 in this snapshot. It would be incorrect to assume all Steam clients are still 32-bit. Conversely, shipping both architectures prevents us from concluding that 32-bit support is unnecessary. Static inventory does not establish which helpers execute or which DLLs load. Steam updates can change this inventory independently of the game.

### Candidate integration routes

**Windows Steam inside the selected Wine environment** is the initial reference route because the prior local baseline used it successfully. Pear must prove login, client startup/update, game launch, Steamworks initialization, and required helpers on the Rosetta-free runtime. It needs either functional WoW64/x86 translation for required 32-bit helpers or measured evidence that the tested route does not need them.

**Native macOS Steam plus a bridge** is a distinct research route that may reduce the Windows client surface. NotProton has a macOS port of Proton's `lsteamclient` and `steam-helper`, but its inspected README targets particular Steam builds and CrossOver Preview 2026082, describes an `ntdll` patch, and reports poorer compatibility for its FEX option. It is useful implementation research, not a proven Pear drop-in or an assurance of upstream Steam support. Its host Steam processes and bridge would need the same architecture audit. [NotProton README](https://github.com/NotProtonNot/NotProton)

For either route:

- Keep the original game Steam API and normal account ownership checks. Pear should not impersonate a licensed account or replace successful initialization with a stub.
- Prefer normal Steam game launch context for the milestone. The earlier `steam_appid.txt` experiment was a development diagnostic; Valve describes it as a development mechanism and says not to ship it with game builds. An App ID is not an ownership credential. [Steamworks initialization documentation](https://partner.steamgames.com/doc/sdk/api)
- The macOS Steam API library having an ARM64 slice does not let an arbitrary Windows DLL call it without an ABI and interface bridge.
- Login credentials stay in the user's Steam environment. Test artifacts must omit tokens, QR codes, account identifiers, and raw client state.
- Record the tested Steam build and dependency inventory. Distinguish core launch support from optional overlay, achievements, cloud synchronization, and Discord presence. Optional failures must remain visible in the support report.

## Verification contract for Rosetta independence

The milestone applies to **the complete required launch and play path**, including Steam, Wine services, graphics libraries, and child helpers. It does not require all Windows guest files to be ARM64. FEX executing x64 PE code is compatible with the objective; macOS executing an x86_64 Mach-O helper through Rosetta is not.

A test report must include:

1. Exact game/depot manifest, Steam build, runtime manifest, source commits, patches, compiler/SDK versions, macOS build, chip, and settings.
2. A startup-to-exit process tree that captures short-lived helpers as well as the long-running game. Identify each required macOS executable and the architecture actually executed; a universal binary merely containing an ARM64 slice is insufficient.
3. Static architecture and dependency inventory for shipped Mach-O files and guest PE modules. Track dynamically loaded libraries as well as executable entry points.
4. Runtime evidence of the selected FEX translator and loaded DXMT/Wine components. Capture the relevant translation state and module mappings for the process, not just `uname -m` from the parent shell.
5. An explicit failure if a required host process falls back to Rosetta. Do not remove Rosetta from the user's daily environment to conduct this test.
6. A second clean validation environment, when available, where the documented installation and launch path does not rely on Rosetta being installed. Treat it as corroboration, not a substitute for attribution of the execution path.

The diagnostic tool should publish a small redacted JSON report and evidence attachments. It should not upload process environments wholesale. The evidence collector itself must run natively and state any blind spots in child-process observation.

## Acceptance tests and measurement design

| Gate | Required evidence |
|---|---|
| Graphics smoke tests | x64 test applications exercise ARM64EC DXMT through the proposed Wine/FEX path; expected images and readback results match; repeated resize/present works |
| Steam launch | Purchased-account login succeeds, Steam launches App 3405340 in the intended prefix, and the game's Steam initialization succeeds |
| Menu and rendering | No blocking missing geometry, corrupt text, broken post-processing, or major rendering defects; actual API/output size logged |
| Gameplay | At least 20 minutes of active gameplay including escalating load, with controls, audio, menus, and pause/resume tested; record what gameplay was actually reached |
| Save and restart | Save after play, exit normally, restart, and verify progression/settings; backup and restore are tested on a copy |
| Input | Keyboard/mouse and focus changes tested. A profile claiming controller support must additionally test at least one named controller and disconnect/reconnect behavior; an initial keyboard/mouse-only profile may explicitly mark controller support untested |
| Audio | Music and effects audible; selected output and a device change tested; no persistent crackle/dropout in the observed run |
| Lifecycle | Three clean launches and exits, plus restart after an induced runner failure on a test copy; no unintended process termination outside the selected prefix |
| Rosetta proof | Complete process/module evidence above, with no required translated Mach-O process |
| Reproducibility | Another documented build/install from pinned sources reproduces the supported route, with signing prerequisites stated |

A support report can mark a feature untested or unsupported; it cannot silently count that feature as passed. Controllers and cloud synchronization should have explicit support status even if keyboard/mouse plus local saves are the initial supported configuration. Cloud tests must use a backup and a controlled account-owned save, avoiding overwriting the user's only progress.

Performance is a quality gate to characterize, not a promise of improvement over Rosetta. Use the same verified game build, output resolution, graphics settings, frame cap, VSync, display mode, Game Mode, power source, Low Power Mode, thermal warmup, and background workload for each comparison. Report menu, paused, early-combat, and later-combat segments separately. Where exact gameplay cannot be replayed, report the uncertainty and workload differences.

Measure frame-time distribution and long stalls, startup time, memory, CPU/GPU utilization, system power estimates, and thermal pressure. Keep cold shader/JIT caches separate from warm-cache runs. Use at least three repeated controlled runs where repeatability is practical. A GPU frame time is not total frame time, instantaneous HUD FPS is not a distribution, and system `powermetrics` power is not per-game power.

The older successful Wine/DXMT installation is a control, not an allowed fallback for passing the Rosetta-free milestone.

## Source and distribution responsibilities

This is an engineering inventory of the checked licenses, not a complete legal review of a future assembled binary distribution.

| Component | Checked upstream terms | Packaging action |
|---|---|---|
| Current DXMT | LGPL-2.1-or-later | Preserve notices, license text and corresponding source/build modifications; choose a compliant library distribution/replacement arrangement |
| Wine | LGPL-2.1 text; inspect individual files and bundled dependencies | Ship applicable notices and the source/patch/build material required for the selected distribution |
| FEX | MIT for the checked top-level project | Preserve copyright and permission notices; audit dependencies separately |
| DXVK | zlib/libpng | Preserve source notices, identify altered versions, and do not misrepresent origin |
| MoltenVK | Apache-2.0 | Preserve license and applicable notices, identify changes, and audit dependencies |
| NotProton | Mixed: bulk GPLv3; `lsteamclient` Steamworks SDK terms; helper and other components have separate terms | Do a per-component review before copying or distributing a bridge; a public repository is not evidence of one uniform license |

Sources: [DXMT license](https://github.com/3Shain/dxmt/blob/main/LICENSE), [Wine license text](https://github.com/wine-mirror/wine/blob/master/COPYING.LIB), [FEX license](https://github.com/FEX-Emu/FEX/blob/main/LICENSE), [DXVK license](https://github.com/doitsujin/dxvk/blob/master/LICENSE), [MoltenVK license](https://github.com/KhronosGroup/MoltenVK/blob/main/LICENSE), [NotProton notice](https://github.com/NotProtonNot/NotProton/blob/main/NOTICE).

Do not carry the legacy DXMT 0.80 license label forward onto current source. Archive the actual notices for every chosen version. A Pear runtime manifest must include a source location, commit/archive checksum, applied patches, build recipe, output hashes, license inventory, and compatibility set identifier. An upstream source URL alone is insufficient if Pear distributes modified binaries.

DXMT's current contribution policy rejects AI/LLM-authored or coauthored contributions, while allowing research findings to be shared. Pear must respect that policy and cannot promise that generated patches will be accepted upstream. This audit is research for Pear; it is not an upstream contribution submission. [DXMT contribution policy](https://github.com/3Shain/dxmt/blob/main/CONTRIBUTING.md)

## Issue-sized work packages

1. **Reproduce DXMT ARM64EC/ARM64 builds.** Deliver a pinned build recipe, artifact inventory, licenses, and output architecture checks. Depends on selection of the Wine interface/toolchain.
2. **Specify and test the Wine–DXMT ABI contract.** Verify driver exports, DLL modes, winemetal pairing, callbacks, and exception behavior. Deliver small redistributable tests and a compatible bundle manifest.
3. **Audit the Steam execution route.** Deliver static and dynamic architecture inventories, a tested login/update/launch route, and a documented decision on WoW64 requirements versus native Steam bridge research.
4. **Build Rosetta-dependency diagnostics.** Deliver process/module attribution, translation-state checks, native collector validation, and redacted evidence output.
5. **Validate Megabonk gameplay and persistence.** Deliver the acceptance matrix above, save backup/restore evidence, known defects, and exact tested versions.
6. **Establish controlled comparison measurements.** Deliver raw non-sensitive measurements and a reproducible protocol; no comparative efficiency claim without comparable data.

Open questions remain: whether the selected macOS Wine/FEX source and signing path can be reproduced and distributed; which Steam helpers are required on that path; whether graphics ABI and shader conversion remain correct under ARM64EC; and which hardware/OS combinations pass. These are milestone gates, not details to postpone until after announcing game support.
