# Reuse beyond the CPU and graphics engines

Reviewed September 27, 2026. This is an engineering selection record, not a claim that these projects have been integrated into Pear. Core runtime evidence is in the [host audit](macos-runtime-audit.md) and [graphics audit](graphics-and-game-integration.md).

| Project | Useful material | Decision and boundary |
|---|---|---|
| [Wine](https://github.com/wine-mirror/wine) | Windows APIs, PE loader, process/thread environment, macOS driver | Core dependency; preserve upstream architecture and test work. ARM64 macOS completion is a porting task, not assumed from existing x64 Mac support. |
| [FEX](https://github.com/FEX-Emu/FEX) | CPU semantics, IR, ARM64 code generation, Windows emulation modules, tests | Primary CPU candidate. Reuse its engine and port the necessary host boundaries; do not import Linux syscall assumptions into macOS. |
| [DXMT](https://github.com/3Shain/dxmt) | D3D11/DXGI, Metal translation, ARM64EC build work | Primary renderer candidate. Treat Wine driver interfaces and DXMT build variants as one qualified compatibility set. |
| [frankea/Whisky](https://github.com/frankea/Whisky) | Swift/WhiskyKit prefix and process management, runtime distribution, game-profile ideas | Inspect individual reusable modules and their GPL terms. The current local runtime is a baseline, not the foundation of Rosetta independence. |
| [Whisky original](https://github.com/Whisky-App/Whisky) | Historical SwiftUI and Wine-wrapper design | Archived project; avoid inheriting an old runtime simply to reuse its UI. |
| [NotProton](https://github.com/NotProtonNot/NotProton) | macOS Steam Play integration, lsteamclient and helper adaptations | Separate integration experiment. Current README targets particular Steam clients and CrossOver Preview; it is not an independently source-built Pear runtime. |
| [Heroic known-fixes](https://github.com/Heroic-Games-Launcher/known-fixes) | Declarative game-specific fixes and contribution workflow | Borrow schema/design ideas. Verify licenses for actual copied data or code separately; do not assume the launcher license covers every data repository. |
| [Lutris installer format](https://github.com/lutris/lutris/blob/master/docs/installers.rst) | Separation of game identity, runner, files, and installation steps | Design reference. Linux-specific operations require Mac validation and a bounded operation set. |

## Avoid treating profiles as verified compatibility

The Whisky fork has an existing [game database](https://github.com/frankea/Whisky/blob/main/WhiskyKit/Sources/WhiskyKit/GameDatabase/Resources/GameDB.json), but its [audit](https://github.com/frankea/Whisky/blob/main/docs/AUDIT.md) distinguishes inferred recipes from verified play tests. Pear should retain that distinction when importing any profile: a suggested setting is not a passing test record.

Pear's reusable asset is a profile plus a versioned qualification record. Community requests and votes identify interest; tests determine the documented support state. Profiles should not require a particular frontend.

## Steam integration tradeoff

NotProton's current design enables Steam Play behavior in macOS Steam and adapts components including lsteamclient and a Steam helper. It explicitly targets selected Steam client and CrossOver Preview versions. This can inform a future native integration but adds client-update and ABI coupling. Its [NOTICE](https://github.com/NotProtonNot/NotProton/blob/main/NOTICE) lists distinct component licenses. Preserve those boundaries rather than treating the whole project as a uniform library.

For the first runtime milestone, establish the ordinary Windows Steam path in the qualified ARM64 Wine/FEX environment. A native bridge can then be compared on launch behavior, callbacks, save/cloud behavior where used, required host architecture, and maintenance cost.

## Reuse policy

Prefer a small maintained interface or attributable patch series over importing an entire launcher and inheriting its unrelated product assumptions. Reusing GPL/LGPL code is a valid option for an open-source project; license compatibility and source-distribution work should be planned before selecting copied code. No particular Pear license is selected by this document.

Existing experimental scripts should be moved into product modules only after their assumptions are made explicit. Runtime selection by filename, executable-size heuristics, global environment changes, and arbitrary mixed library versions cannot serve as a compatibility contract.
