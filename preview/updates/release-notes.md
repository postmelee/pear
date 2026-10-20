# Pear 0.1.0

Pear's first stable release makes Windows Steam setup, app updates and optional game reports available in one Mac app. Game compatibility still depends on the game and your Mac; this is not a claim that every game works.

**Apple Silicon · macOS 15+ · Rosetta required**  
Includes the Pear app and optional CLI. First-run setup downloads **Wine 11.0 and DXMT 0.80** separately, using the unchanged signed runtime.

## Install or upgrade

[Download Pear for Mac](https://github.com/postmelee/pear/releases/download/v0.1.0/Pear-0.1.0-macos-arm64.dmg), open the DMG and drag Pear to Applications. Quit games, Steam and the old Pear app before replacing it. Existing Steam login, games, saves and sharing preferences are preserved; keep the Pear Preview folder in Application Support.

Homebrew: `brew install --cask postmelee/tap/pear`. Existing Homebrew users: `brew update` then `brew upgrade --cask postmelee/tap/pear`.

## What is new

- **App updates with Sparkle.** Pear checks at launch and offers the installed and new versions with release notes. Choose **Update and launch** or **Later**. No update, a declined update, a failed check or a check timeout continues to Steam. Installation is deferred while Steam or games are active. Wine/DXMT keep their existing installation and validation path.
- **Your choice of reporting.** Keep records local, review after each game, or enable automatic sharing of selected observations. Nothing is sent until you confirm a sharing choice. The welcome screen preselects Automatic sharing and the four field groups; **Continue without sharing** keeps sharing off. Update choices do not grant report-sharing consent.
- **Run history and optional details.** Open **Window → Run history** to add a result, share, export or manage a record. Notes require explicit sharing and remain private. Reports enter private review before selected fields may appear in the catalog or on GitHub. Process time is not verified play time and never automatically becomes a Pass.
- **Clearer setup and startup.** Review required downloads, follow progress and cancel preparation. Settings are in **Pear → Settings → Sharing**; the Steam window detection shows when to continue in Steam.

Legacy preview apps do not contain Sparkle: install this release manually once, or update with Homebrew. Recognized Homebrew-managed installations defer in-app replacement; use Homebrew to update. Sparkle system profiling is disabled. [Updates and recovery](https://github.com/postmelee/pear/blob/master/docs/rosetta-preview.md#app-updates) · [Reporting and privacy](https://github.com/postmelee/pear/blob/master/docs/reporting-and-privacy.md).

## Verification scope

App, CLI and DMG passed Developer ID signing and Apple notarization. The exact signed app/CLI passed macOS 15.7.9 ARM64 startup checks; Steam UI and gameplay on macOS 15 and exact macOS 15.0 execution remain unverified.

On M4 Pro / macOS 26.5.2, an updater-enabled signed build 6 updated to build 7 and reopened Steam once. Decline, active-session reuse, unavailable/offline update-check fallback, corrupt-archive rejection and pre-install cancellation were checked. Timeout and installer-error callbacks have fixture coverage; arbitrary filesystem or power-loss recovery is not claimed. Final stable-feed build 8 retained login/library, all 11 checked save files, history and sharing preferences.

The unchanged Wine/DXMT runtime retains earlier owner-confirmed Megabonk gameplay, audio, save/relaunch, recovery and same-Mac fresh-account installation evidence. Long gameplay was not repeated for these app changes. Automatic, manual and ask-after-game reporting were checked with the owner; public approval is separate from compatibility qualification. No all-game, performance or second-physical-Mac claim is made.

## Downloads, source and licenses

Use `SHA256SUMS` to verify the attached downloads. The app ZIP is the Sparkle update archive; ordinary installation uses the DMG. The CLI is optional and has no automatic updater.

App/CLI source: `pear-source-51fbe6f.tar.gz`, commit `51fbe6f2dea42c82691d803ef02ae1663c087dd9`, app version 0.1.0/build 8. The unchanged runtime and corresponding source kit remain in the [runtime release](https://github.com/postmelee/pear/releases/tag/v0.1.0-preview.2). Pear original source is GPL-3.0-or-later; Sparkle and other third-party components retain their licenses and bundled notices.

[Build and signing](https://github.com/postmelee/pear/actions/runs/39383912617) · [Exact signed macOS 15 check](https://github.com/postmelee/pear/actions/runs/39385304875)
