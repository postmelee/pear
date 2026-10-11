<p align="center"><img src="https://raw.githubusercontent.com/postmelee/pear/4e1be9114fc76802e21b075e143cfc2f86c66c0a/docs/assets/pear.png" width="144" alt="Pear"></p>

# Pear

**Windows Steam games on Mac. Free and open source.**

Pear is building a simple way to open Windows Steam and play owned games on
Apple Silicon. The long-term goal is **Windows gaming without Rosetta**, across
every required host process and library.

## Try Pear

The **Rosetta Preview** prepares Wine and Windows Steam through a small Mac app
and optional CLI. Sign in through official Steam and choose a game from your
library. You should not need to learn Wine or configure compatibility tools.

**There is no public app download yet.** Preview candidates have been tested on
one M4 Pro with macOS 26.5.2; installation recovery and final delivery checks are
still in progress. The Preview currently requires Rosetta and targets macOS 26+.
The Rosetta-free runtime is a separate development track, not a player-ready app.

| Start here | Guide |
|---|---|
| Try the Preview when released | [Availability and first Steam session](https://github.com/postmelee/pear/blob/4e1be9114fc76802e21b075e143cfc2f86c66c0a/docs/rosetta-preview.md) |
| Check game observations | [Recorded configurations and results](https://github.com/postmelee/pear/blob/4e1be9114fc76802e21b075e143cfc2f86c66c0a/docs/compatibility/README.md) |
| Help with the Preview | [Development setup](https://github.com/postmelee/pear/blob/4e1be9114fc76802e21b075e143cfc2f86c66c0a/docs/development/getting-started.md) |
| Contribute to the Rosetta-free runtime | [Engineering entry point](https://github.com/postmelee/pear/blob/4e1be9114fc76802e21b075e143cfc2f86c66c0a/docs/development/rosetta-free.md) |
| Get help | [Support](docs/SUPPORT.md) · [Community](docs/community.md) |
| Contribute or report a problem | [Contributor guide](docs/contributing.md) · [Issues](https://github.com/postmelee/pear/issues) |
| Explore the project | [Documentation](docs/README.md) · [Architecture](docs/architecture.md) · [Delivery plan](docs/delivery-plan.md) |

Preview guides above are pinned to the reviewed work-in-progress source while
[Issue #47](https://github.com/postmelee/pear/issues/47) completes qualification.
They describe candidates and remaining checks, not an available release.

## Two tracks, one goal

| Track | Purpose | Status |
|---|---|---|
| Rosetta Preview (M3) | Easy setup and official Windows Steam launch | Same-host Megabonk observations; public distribution pending |
| Rosetta-free runtime (M1) | Owned Windows Megabonk without Rosetta in any required host process or library | Active engineering and qualification |

Megabonk is the first validation game. A Steam library entry or successful menu
launch does not establish support for a game or other Macs. Reports retain the
exact tested configuration and unknown or failed checks. Comparative performance,
power and memory claims require separate measurements.

The [delivery plan](docs/delivery-plan.md) is the single roadmap. Players can help
with test reports and usability feedback; contributors can work on setup,
recovery, native runtime development and documentation. Paid AI tools are not
required. Requests and votes express demand without promising support or dates.

## License and game ownership

Copyright (C) 2026 Pear contributors.

Except where a file or directory specifies separate terms, original Pear code is
licensed under **GPL-3.0-or-later**. See [LICENSE](LICENSE). Pear is provided without
any warranty, including implied warranties of merchantability or fitness for a
particular purpose.

Reused components, explicitly licensed fixtures and Hyper-Waterfall materials
retain their own licenses and attribution. See the
[contributor guide](docs/contributing.md) and
[Preview component record](https://github.com/postmelee/pear/blob/4e1be9114fc76802e21b075e143cfc2f86c66c0a/preview/THIRD_PARTY_NOTICES.md).
Steam, Rosetta and games are not relicensed by Pear. Supply your own licensed
games and authenticate through official Steam; game files, credentials and saves
are not part of this repository. Official Pear downloads are intended to be free;
GPL also permits others to redistribute copies for a fee.
