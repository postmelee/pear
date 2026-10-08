# Upstream reuse for the Pear runtime and platform

Original review September 27, 2026; runtime reuse review October 8, 2026. This is an engineering selection record, not a claim that these projects have been integrated into Pear. Core runtime evidence is in the [host audit](macos-runtime-audit.md) and [graphics audit](graphics-and-game-integration.md).

| Project | Useful material | Decision and boundary |
|---|---|---|
| [Wine](https://github.com/wine-mirror/wine) | Windows APIs, PE loader, process/thread environment, macOS driver | Core dependency; preserve upstream architecture and test work. ARM64 macOS completion is a porting task, not assumed from existing x64 Mac support. |
| [FEX](https://github.com/FEX-Emu/FEX) | CPU semantics, IR, ARM64 code generation, Windows emulation modules, tests | Primary CPU candidate. Reuse its engine and port the necessary host boundaries; do not import Linux syscall assumptions into macOS. |
| [DXMT](https://github.com/3Shain/dxmt) | D3D11/DXGI, Metal translation, ARM64EC build work | Primary renderer candidate. Treat Wine driver interfaces and DXMT build variants as one qualified compatibility set. |
| [Hangover](https://github.com/AndreRH/hangover/blob/56e385b7ff490edd281b288f420677093563560b/README.md) | Wine/FEX ARM64EC and WoW64 emulator integration | Inspect existing module selection and Windows/native boundaries before new equivalents. Its Linux execution evidence is not a Darwin qualification. |
| [Madeira](https://github.com/willfaust/Madeira/tree/48f976429c189f8396e23d251d8a82f43c705922) | Darwin loader/signal, FEX context, JIT aliases and guest-memory integration | Review complete functions and dependencies. Its iOS JIT authorization, alias pool and static app composition need a separate macOS design; preserve Pear's passing owner until a concrete alternative is demonstrated. |
| [madeira-anyps5](https://github.com/buberlo/madeira-anyps5/tree/9519e10037c61bf4a6389387e94acba8f464d29b) | Guest-data/host-execution separation, placeholder handling, diagnostic fixtures and patch reconciliation | Select relevant components and file licenses. PS5 ELF/HLE, MoltenVK and device experiments do not qualify Windows PE, Steam or Megabonk in Pear. |
| [frankea/Whisky](https://github.com/frankea/Whisky/tree/3abfbae945e3400caaa13cf2e78fe5a187a1405b/WhiskyKit) | Swift/WhiskyKit prefix, process and runtime management | Review these facilities before rebuilding equivalents for #9 or the application. Check each module's GPL terms and Pear ownership contract; retain #3's Rust supervisor decision. Existing runtime bundles do not establish Rosetta independence. |
| [Whisky original](https://github.com/Whisky-App/Whisky) | Historical SwiftUI and Wine-wrapper design | Archived project; avoid inheriting an old runtime simply to reuse its UI. |
| [NotProton](https://github.com/NotProtonNot/NotProton) | macOS Steam Play integration, lsteamclient and helper adaptations | Separate integration experiment. Current README targets particular Steam clients and CrossOver Preview; it is not an independently source-built Pear runtime. |
| [Heroic known-fixes](https://github.com/Heroic-Games-Launcher/known-fixes) | Declarative game-specific fixes and contribution workflow | Borrow schema/design ideas. Verify licenses for actual copied data or code separately; do not assume the launcher license covers every data repository. |
| [Lutris installer format](https://github.com/lutris/lutris/blob/master/docs/installers.rst) | Separation of game identity, runner, files, and installation steps | Design reference. Linux-specific operations require Mac validation and a bounded operation set. |

## Runtime reuse review

Retain FEX's C++/assembly engine, Wine's C Windows/host services and DXMT for M1. Rust/Cranelift and an independent CPU engine are not prerequisites. The [manager decision](../decisions/manager-language.md) remains specific to the supervisor.

Before new subsystem code or a boundary fix, compare pinned upstream functions together with their loader, context, memory, locking and signal dependencies. Record **adopt/adapt/reject**, exact source and file licenses, and a specific technical reason. Prefer original implementations plus minimal Darwin adapters. This review identifies candidates; it does not assert that an upstream function works in Pear.

| Boundary | Reuse target | Required integration judgment |
|---|---|---|
| EC entry/return, guest state and thread cleanup | FEX `Module.S`, `SyncThreadContext`, `ThreadTerm` and existing exception reconstruction at [Pear's selected FEX pin](https://github.com/FEX-Emu/FEX/tree/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/Source/Windows) | Reuse CPU/ABI semantics; connect actual Wine layouts and execution/continuation ownership. |
| Code changes, invalidation and suspend | FEX interval/call-ret caches and `SuspendDoorbell`; compare [Madeira FEX](https://github.com/willfaust/FEX/tree/be778d7ba5b98bee0405fd1d6a50d305a0807df0) with its alias/sweep dependencies | Preserve publication, global execution draining, native return/callback pins and macOS protections. Copying a function alone is insufficient. |
| CPU fixture generation and execution | Madeira [gen_asmconf.py](https://github.com/willfaust/Madeira/blob/48f976429c189f8396e23d251d8a82f43c705922/tests/x64/gen_asmconf.py) and [asmconf-x64.c](https://github.com/willfaust/Madeira/blob/48f976429c189f8396e23d251d8a82f43c705922/tests/x64/asmconf-x64.c) adapt existing FEX ASM tests to Windows PE | Review before writing a #6 runner. The generator excludes HostFeatures-gated tests and captures SIMD only to 128 bits; reference validity, required AVX coverage, fixed addresses and fault continuation need explicit review. |
| i386 helpers | Hangover/FEX/Madeira WoW64 modules and dependencies | Inspect actual Steam/helper architectures early; implement and qualify required guest modes without authentication/client stubs. A built module is not execution evidence. |
| D3D11 integration | Completed [#7](https://github.com/postmelee/pear/issues/7) component and pinned DXMT [tests/dx11](https://github.com/3Shain/dxmt/tree/7c8dee1c2d73415301ceb7d1fa810861cef4cd67/tests/dx11) | Run suitable existing fixtures as translated x64 with #5's Wine/FEX pairing. Add missing image/readback, lifetime and callback checks required by #8; native component or demo evidence alone is insufficient. |
| CLI acquisition | Existing [DepotDownloader](https://github.com/SteamRE/DepotDownloader) and [SteamKit2](https://github.com/SteamRE/SteamKit) | Review existing authentication/download tools before implementing a client. Pin selected source, license and native architecture; downloading does not establish normal runtime Steam/Steamworks integration. |

Pear's single-address JIT owner and global execution draining are the main custom-integration review target. Local #5 Stage 5 corrected own-protocol integration failures and passed bounded same-candidate x64 lifecycle fixtures. Retain that design until a concrete alternative demonstrates equivalent required behavior under normal macOS protections. Its one-Context/up-to-three-EC-thread profile is not game-scale qualification; i386 execution remains unperformed. The historical 256 KiB prototype metadata cap is not a game requirement. Reuse evidence only for valid unchanged inputs and claim scope, run changed-boundary regressions, and preserve approved safety checks and fresh final reconstruction.

## Avoid treating profiles as verified compatibility

The Whisky fork has an existing [game database](https://github.com/frankea/Whisky/blob/main/WhiskyKit/Sources/WhiskyKit/GameDatabase/Resources/GameDB.json), but its [audit](https://github.com/frankea/Whisky/blob/main/docs/AUDIT.md) distinguishes inferred recipes from verified play tests. Pear should retain that distinction when importing any profile: a suggested setting is not a passing test record.

Pear's reusable asset is a profile plus a versioned qualification record. Community requests and votes identify interest; tests determine the documented support state. Profiles should not require a particular frontend.

## Steam integration tradeoff

NotProton's current design enables Steam Play behavior in macOS Steam and adapts components including lsteamclient and a Steam helper. It explicitly targets selected Steam client and CrossOver Preview versions. This can inform a future native integration but adds client-update and ABI coupling. Its [pinned NOTICE](https://github.com/NotProtonNot/NotProton/blob/c3a49486c14cdf6b9716e2e7ac55286aa537fcf1/NOTICE) includes Steamworks SDK terms for lsteamclient and headers, alongside GPL, BSD and other components. Preserve those boundaries rather than treating the whole project as a uniform library.

For the first runtime milestone, establish the ordinary Windows Steam path in the qualified ARM64 Wine/FEX environment. A native bridge can then be compared on launch behavior, callbacks, save/cloud behavior where used, required host architecture, and maintenance cost.

## Reuse policy

Prefer a small maintained interface or attributable patch series over importing an entire launcher and inheriting its unrelated product assumptions. Reusing GPL/LGPL code is a valid option for an open-source project; license compatibility and source-distribution work should be planned before selecting copied code. No particular Pear license is selected by this document.

License review is component- and revision-specific:

- [Original FEX](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/LICENSE) is MIT. [Madeira FEX modifications](https://github.com/willfaust/FEX/blob/3bec2ac498bf78156ab47c0c194b0e8cb2849756/LICENSE-MADEIRA.md) are GPL-3.0-or-later with the stated author-scoped converter permission. Its contributed WoW64 `IosMonoBridge.cpp` and `IosTeb.h` carry MIT notices. Per-file or historical MIT grants need their own provenance; they do not relicense the GPL changes.
- Madeira's [selected Wine LGPL branch](https://github.com/willfaust/wine/blob/257f271cfffed9f22f7987cac53bc00095d092fe/LICENSE-MADEIRA.md) retains LGPL-2.1-or-later; its earlier GPL-converted branch has different terms.
- [AnyPS5-related notices](https://github.com/buberlo/madeira-anyps5/blob/9519e10037c61bf4a6389387e94acba8f464d29b/NOTICE) distinguish AnyPS5 GPL-2.0-only, GPL-3.0-or-later Madeira/FEX patches, LGPL Wine patches and selected MIT diagnostics. Do not treat GPL-2.0-only as interchangeable with GPL-3.0 modifications.
- [Pear's selected DXMT LICENSE](https://github.com/3Shain/dxmt/blob/7c8dee1c2d73415301ceb7d1fa810861cef4cd67/LICENSE) is LGPL-2.1-or-later. Verify the exact chosen pin and original-file notices; do not copy a historical or fork-wide MIT label onto this version.
- Madeira's [licensing record](https://github.com/willfaust/Madeira/blob/48f976429c189f8396e23d251d8a82f43c705922/docs/LICENSING.md) leaves SwiftSteam public permission/provenance and clean rebuild/relink/install work open. The whole app is therefore not a ready-qualified drop-in. NotProton's Steamworks and other component terms require their own review.

Before importing code, identify compatible combination terms and plan attribution, corresponding source, relinking/installation obligations where applicable, and upstream contribution-policy compliance. This permits considered GPL/LGPL reuse; it does not choose Pear's license or authorize a blanket import, publication or release.

Existing experimental scripts should be moved into product modules only after their assumptions are made explicit. Runtime selection by filename, executable-size heuristics, global environment changes, and arbitrary mixed library versions cannot serve as a compatibility contract.
