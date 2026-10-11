<p align="center"><img src="docs/assets/pear.png" width="144" alt="Pear"></p>

# Pear

**Windows Steam games on Apple Silicon, with simple setup and a free, open-source app.**

Pear prepares a Windows Steam environment so players can open their library without
learning Wine or configuring compatibility tools. The final goal is an experience
with **no Rosetta dependency** across every required process and library.

## Try Pear

The current **Rosetta Preview (M3)** uses Rosetta, Wine and DXMT. Open Pear, sign
into official Windows Steam, then choose an owned game from your library. The app
and optional CLI share the same setup. Routine players should not need Terminal,
Xcode, a developer account or a paid compatibility app.

**A public download is not available yet.** The app and CLI are local notarized
candidates. The pinned replacement runtime has passed notice/source comparison
and same-host Steam/game checks. Recovery, measured sustained play and final
clean-Mac delivery remain pending. Notarization alone does not complete these
checks. The candidate targets Apple Silicon and macOS 26+; observed execution is
limited to M4 Pro/macOS 26.5.2.

| Start here | What you will find |
|---|---|
| [Use the Preview](docs/rosetta-preview.md) | Availability, first Steam session, optional CLI and data preservation |
| [Game reports](docs/compatibility/README.md) | Tested configurations, limitations and how to share a result |
| [Get help](docs/SUPPORT.md) | Questions, bug reports and private reporting routes |
| [Make a first contribution](docs/development/getting-started.md) | Local checks, Preview build and contribution paths |
| [Develop without Rosetta](docs/development/rosetta-free.md) | Native runtime work, existing Issues and current prerequisites |
| [Read the documentation](docs/README.md) | Tutorials, task guides, reference and explanation |

## Two tracks, one goal

| Track | Current scope | Status |
|---|---|---|
| Rosetta Preview (M3) | Make Windows Steam preparation, launch and recovery easy | Signed app/CLI: official login, Megabonk installation, Steamworks and menu/input verified on one Mac; public distribution pending |
| Rosetta-free runtime (M1) | Run owned Windows Megabonk with every required host process and library free of Rosetta | Under development; no player-ready native preview |

On October 11, an experimental ARM64 Wine/FEX/DXMT configuration reached the
Megabonk main menu, and manual menu input was confirmed. Gameplay entry failed
during loading. Verification of Rosetta independence across all required host
processes and libraries, Steamworks integration and gameplay qualification remain
pending. Follow [the native integration work (#11)](https://github.com/postmelee/pear/issues/11).

Megabonk is the first validation game. Selecting another game in Steam does not
establish compatibility. [Recorded results](docs/compatibility/records.md) retain
failed, unknown and untested outcomes as well as successes. Menu interaction is
not sustained gameplay qualification.

The [delivery plan](docs/delivery-plan.md) is the single roadmap. Technical M1,
proposed ordinary-user M2, current M3 and independent CPU research R1 have distinct
acceptance criteria. The [architecture](docs/architecture.md) explains the intended
Wine/FEX/DXMT runtime and reuse choices. A native launcher alone does not meet M1.

## Contribute

Help with Preview setup and recovery, native runtime engineering, tests,
documentation, accessibility or game observations. You do not need an AI service
or programming experience to report a useful result. Start with the
[contributor guide](docs/contributing.md) and [community guide](docs/community.md).
Requests and votes express demand; they do not promise support or a delivery date.

Pear aims to keep official downloads free, publish reproducible component inputs,
record bounded compatibility evidence and preserve users' games and saves during
recovery. Performance, power and memory improvements require measurements; no
comparative claims are established.

## Game files and licensing

Pear is intended to work with game copies provided by users who own them. Game files, Steam account data, and extracted game code or assets are not included in this repository.

Copyright (C) 2026 Pear contributors.

Except where a file or directory specifies separate terms, original Pear code is
free software under the **GNU General Public License, version 3 or (at your
option) any later version**. See [LICENSE](LICENSE). Pear is provided without
any warranty, including implied warranties of merchantability or fitness for a
particular purpose; the full license gives the terms.

Existing third-party code, explicitly licensed fixtures and Hyper-Waterfall
materials retain their own licenses and attribution. This license does not apply
to Steam, Rosetta or games. See the [component record](preview/THIRD_PARTY_NOTICES.md)
and [contributor guide](docs/contributing.md). Official Pear downloads are intended
to be free of charge; GPL also permits others to redistribute copies for a fee.
