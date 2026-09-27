# Local evidence and limits

Evidence date: September 27, 2026. This summary contains no game code, assets, credentials, or personal save data. Underlying local experiment files are not included in the repository. These observations are not yet independently reproduced public test results.

## Inputs

The inspected Steam application is Megabonk, App ID `3405340`. The Windows depot is `3405342`, manifest `446680890915713051`; the Linux depot is `3405341`, manifest `6464790072963772385`. The 69 Windows files and 65 Linux files passed the recorded Steam manifest size/hash checks. A common source commit or App BuildID was not established.

Both distributions contain Unity `2023.2.22f1` and IL2CPP metadata interpreted as `29.1`. The Windows GameAssembly and Unity player are x86-64 PE files; the Linux equivalents are x86-64 ELF files. Neither distribution supplies a Mac ARM64 game build. Platform-specific Rewired, Steamworks, and Discord libraries require runtime coverage. Presence in a distribution does not prove a library is loaded during play.

## Existing execution baseline

The recorded test used a MacBook Pro with M4 Pro, 12 CPU cores, 24 GB RAM, and macOS `26.5.2 (25F84)`. Windows Megabonk `1.0.69` launched through Wine `11.0` and DXMT `0.80` from the frankea/Whisky Libraries `3.1.1` package. **The Wine host used Rosetta.**

The test reached the menu and a Forest Tier 1 game session. Steam initialization succeeded after the user signed in through the official client. Game-provided 30 and 60 FPS limits were observed through the HUD. The actual observed render size was `1512 x 982`, not the resolution initially supplied as a launch argument.

This establishes a D3D11 compatibility baseline. It does not establish a Rosetta-free build, sustained frame-time statistics, a complete 20-minute playthrough, late-game stability, or a save/relaunch qualification.

## Power evidence

A 120-second powermetrics collection exercised the collection/summary tooling. The observed game was paused for part of the investigation; battery state, power policy, and background activity were not controlled. The readings were system CPU/GPU estimates, not isolated game power. They cannot support an efficiency comparison or a claim of reduced heat.

## Native restoration research

The initial structural extraction recovered types, signatures, and addresses, not a buildable Unity source project. A later Cpp2IL development build emitted CIL for 15 selected functions from each platform, but 22 of the 30 outputs still contained recovery diagnostics and the sampled outputs had stack-header problems; a simple function also exposed a local-variable typing defect. A manually reconstructed small bit-test function passed its own reference checks, which is not whole-game decompilation or dynamic equivalence testing against the original game.

No native Unity scene, Metal asset pipeline, complete gameplay, or save/relaunch cycle has been demonstrated from restored code. This research informs game behavior and test cases but is not a prerequisite or substitute for Pear's compatibility engine.

## Reusable local tooling

The existing Python inspection, acquisition, launch, and power-summary scripts are experimental inputs. Useful ideas include streaming hashes, PE/ELF inspection, scoped Wine prefixes, explicit DLL overrides, log capture, and separating source files from experiment outputs.

The launch script is tied to a particular x64 runtime and a fixed experimental layout. The static inspector does not yet provide a complete Mach-O/ARM64EC/ARM64X dependency audit. Generalize these tools and test their error handling before they become part of Pear's reproducibility or Rosetta-independence evidence.

## Next evidence required

1. Source-built, pinned ARM64 host and CPU translation stack with normal macOS permissions.
2. Architecture evidence for the complete runtime path, including Steam helpers and loaded host libraries.
3. CPU/ABI and graphics fixtures passing on that stack.
4. Actual gameplay, input/audio, saving, exit, and reload on a clean setup.
5. Matched measurements before any comparative performance or power claim.
