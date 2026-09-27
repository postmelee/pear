# Pear

**Pear aims to provide an open-source platform for running Windows games on Apple Silicon without Rosetta, with compatibility tested and maintained by its community.**

The first milestone is to **run Megabonk on an Apple Silicon Mac without Rosetta**. Support for additional games will grow through documented testing, game profiles, and compatibility improvements.

> Pear is in the research and prototyping stage. Rosetta-free Megabonk execution has not yet been verified, and an end-user release is not yet available.

## Core values

These values guide development and describe the intended platform:

1. **An open, reproducible runtime**

   Publish source code, build instructions, and component versions so that others can inspect, reproduce, and maintain the runtime.

2. **Verifiable game support**

   Document each game's last verification date, tested Mac models and macOS versions, and known issues.

3. **Straightforward setup and recovery**

   Provide tested settings, save backups, and a way to return to a previous runtime version when problems occur.

4. **Community participation that expands compatibility**

   Use game requests and upvotes to understand demand, and make it possible to contribute settings, test results, documentation, and compatibility patches.

## First milestone: run Megabonk without Rosetta

**Status: not yet achieved.** The target platform is macOS on Apple Silicon.

The milestone will be considered complete when a documented setup can:

- Launch Megabonk and complete at least 20 minutes of gameplay without Rosetta.
- Verify Steam integration, input, audio, and saving and loading game progress.
- Run all required runtime components, including launchers, helpers, and libraries, without Rosetta.
- Be reproduced from available source code, documented patches, pinned component versions, and build instructions, including any required macOS signing and execution permissions.

The verification record must identify the game version, Mac hardware, macOS version, runtime versions, test date, settings, and known limitations. Success on one configuration will establish that tested configuration; broader compatibility requires additional testing.

Early technical checks will use small x64 programs and Direct3D 11 samples before testing the full game. Installer development, save-backup automation, runtime rollback, and support for additional games are subsequent goals.

## Technical direction

The initial candidate stack is **ARM64 Wine, FEX, and an ARM64-compatible DXMT build**. This is a research direction, not a validated Pear release.

| Component | Intended role |
|---|---|
| FEX | Translate the game's x86/x64 CPU instructions for execution on ARM64 |
| ARM64 Wine / ARM64EC integration | Provide Windows APIs and an execution environment, using native ARM components where supported |
| DXMT | Translate Direct3D 11 graphics operations to Metal |
| Pear launcher and game profiles | Manage installation, runtime selection, settings, verification records, backups, and recovery |

Existing x64 games still need CPU instruction translation when running without Rosetta. The first technical work is to verify source and patch availability, reproducible builds, macOS execution requirements, and compatibility across the required runtime components.

Pear intends to reuse existing open-source projects and contribute generally useful improvements in accordance with each upstream project's contribution policies.

## Current status

As of September 27, 2026:

| Area | Status |
|---|---|
| Initial inspection of Megabonk Windows and Linux distribution files | Completed |
| Megabonk launch and initial gameplay with Wine + DXMT on an M4 Pro | Verified with **Rosetta in use** |
| In-game 30 and 60 FPS limits | Verified in the existing test setup |
| Megabonk execution without Rosetta | Not yet verified |
| Extended gameplay validation and power comparisons under matched conditions | Pending |
| End-user installation, save backups, and runtime rollback | Planned |
| Website for game requests and upvotes | Planned |

Comparative performance, power use, and thermal behavior have not yet been established. Claims about improvements will be based on measurements under comparable conditions.

## Participation

Players, testers, developers, and documentation contributors can help shape Pear. Programming experience is not required to contribute game requests, clear problem reports, test results, or documentation improvements.

Useful contributions include:

- Game requests and descriptions of compatibility problems.
- Reproduction steps and test results for specific Mac and macOS configurations.
- Game settings and runtime profiles that others can verify.
- Documentation, usability feedback, and compatibility fixes.

Reports should include the game and runtime versions, Mac chip, macOS version, resolution, graphics settings, test date, and observed behavior. Exclude account credentials, authentication tokens, and personal save data from reports.

Planned voting features will help identify demand. Prioritization will also consider reproducibility, available contributors, expected effort, and whether an improvement helps multiple games. A request or vote does not guarantee support or a delivery date.

## Game files and licensing

Pear is intended to work with game copies provided by users who own them. Game files, Steam account data, and extracted game code or assets are not included in this repository.

Each reused component retains its own license requirements. Pear's own license and detailed contribution process will be established before a public release.
