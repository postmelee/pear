# Pear for Windows Steam

Status: **[Pear 0.1.1](https://github.com/postmelee/pear/releases/tag/v0.1.1) is available.**
[Download the Mac app](https://github.com/postmelee/pear/releases/download/v0.1.1/Pear-0.1.1-macos-arm64.dmg) or use the
[download guide](https://postmelee.github.io/pear/download.html). This release uses
**Wine 11.0 and DXMT 0.80** and requires Rosetta. The new app/CLI and DMG are signed and notarized. The runtime is unchanged from
preview.3; its prior fresh-account and gameplay evidence retains its original scope.

Pear is intended to be free and open source. Pear prepares Windows Steam
on Apple Silicon so you can use your library without installing or configuring
Wine yourself. It currently requires Rosetta; the final Rosetta-free goal remains
in the [delivery plan](delivery-plan.md).

## Before using a release

The release targets Apple Silicon and macOS 15 or later. Final signed app/CLI
startup was checked on macOS 15.7.9 in CI and macOS 26.5.2 locally. The unchanged
Wine runtime started in macOS 15.7.9 CI. Steam UI and gameplay on macOS 15, exact
15.0 execution and broader hardware compatibility remain unverified.
Rosetta, internet access, a Steam account and ownership of games are required.
Allow several GB for setup plus each game's requirements. Steam's first update
can be larger than Pear itself. Runtime and game installation require storage
beyond the small Pear download.

## App experience

The release page includes downloads, checksums, source and test scope. Open the
DMG, drag **Pear** to Applications, then open it normally. Keep macOS security
protections enabled; no Terminal or developer enrollment is needed for the app.

1. On first setup, review the runtime and Steam installer download
   sizes, then select **Download and install**. Pear shows downloaded bytes and
   a progress bar; extraction and preparation show their current step. Steam
   self-updates and game downloads have separate, variable sizes. **Cancel**
   stops preparation; **Retry** continues with existing data preserved.
2. Steam may update itself. Sign in directly in the official Steam window using
   QR or your account; Pear does not request your password.
3. Choose a game from your Steam library, install it, then use Steam's Play button.
4. After setup, opening Pear checks for an app update and checks the existing installation, then opens Steam
   automatically without asking for download confirmation again. Steam may require an
   update or renewed sign-in; a fresh client download is not required on every run.

While Steam starts, Pear shows **Opening Steam…** and a progress indicator.
**Steam window is open** means a matching window was detected; Steam may still
be loading or updating. If opening takes longer, Pear offers a retry.

**Pear → About Pear** shows the Pear, Wine and DXMT versions. Full removal and automatic
runtime repair are not included in this interface.

You do not need a separate Whisky app or macOS Steam. Pear's status window can be
closed after Steam opens; that does not quit Steam or a running game. Quit games
and Steam through their own menus. Other games are selectable but unverified.

## App updates

Pear checks for app updates when it opens. **Update and launch** installs the
signed update, restarts Pear and opens Steam. **Later**, an unavailable network or
a failed check continues with the installed version. Checking is bounded to eight
seconds so it cannot hold up Steam indefinitely. Steam or games already running
postpone installation. The update screen shows both versions and release notes.

Legacy preview releases have no Sparkle updater: install the current release manually once or
use Homebrew. Keep the existing data folder. Sparkle updates only Pear; Wine and
DXMT retain the existing download and validation path. Sparkle system profiling
is disabled. Update approval is separate from report-sharing consent.

For a recognized Homebrew installation, Pear defers in-app replacement and points
you to Homebrew. Use one installation method and quit Pear, Steam and games before
upgrading. If an update fails, open the installed Pear again; keep your data and
report the error if needed rather than deleting Steam or saves.

## First-install recovery

Version 0.1.0 could create run history before establishing its installation
folder, then stop with “This folder contains unrelated files.” Quit Pear using
**Pear → Quit Pear** (Command-Q), replace only the app with version 0.1.1 or later,
and open it again. Choose **Download and install** to continue. Keep
`~/Library/Application Support/Pear Preview`; do not delete history, Steam, games
or saves to work around this error.

An affected installation cannot reach the normal Sparkle check, so download the
DMG or upgrade with Homebrew. The fix preserves the recognized history-only
layout and sharing preferences. Unrecognized files remain protected; if recovery
is refused, keep the folder and report the error. Quit other Pear instances first.

## Run history and sharing

Open **Window → Run history** (Command-Shift-H) to review recent runs, add a result
or note, share manually, or export. **Pear → Settings → Sharing** (Command-comma)
controls Manual sharing, Ask after each game and Automatic sharing. Nothing is
sent until you explicitly confirm a sharing choice; **Continue without sharing**
keeps sharing off. The first-run selection is a draft, not consent.

Reports are privately reviewed before selected fields may be published. Notes are
private and require explicit sharing. Running time is not verified active play
and never automatically earns a Pass. Read [reporting and privacy](reporting-and-privacy.md)
for fields, retention, offline retries and separate local/server deletion.

## Homebrew

Install the Mac app from Pear's maintained tap:

```sh
brew install --cask postmelee/tap/pear
```

Open Pear from Applications and review the first-run downloads. This installs the
same signed and notarized Mac app as the DMG download. Apple Silicon, macOS 15 or
later and Rosetta are required. The optional standalone CLI remains a separate
download; the cask does not add a command to PATH.

Quit games, Steam and Pear before updating:

```sh
brew update
brew upgrade --cask postmelee/tap/pear
```

Remove the app:

```sh
brew uninstall --cask pear
```

Steam, installed games and saves remain in `~/Library/Application Support/Pear Preview`.
Pear does not currently provide a complete-removal interface. Keep this folder
unless you intentionally want to remove all installed games and local saves.
If you already installed Pear manually, keep using it or remove only Pear.app
before installing through Homebrew. Do not delete its Application Support folder.

## Optional CLI

The CLI uses the same setup and state as the app. It does not require Node.js,
Python, Xcode or Rust on the player's Mac. Download the [CLI archive](https://github.com/postmelee/pear/releases/download/v0.1.1/pear-preview-0.1.1-macos-arm64-cli.zip),
extract it and run:

```sh
./pear-preview
```

Equivalent explicit command: `./pear-preview steam`. `./pear-preview setup`
prepares the environment without opening the Steam library. `--help` lists options.
In preview.2 or later, `./pear-preview setup-info` prints read-only installation hints and
pinned download sizes without creating state or contacting the network.
`./pear-preview --version` shows the version. Invoking `steam` or `setup` explicitly
starts preparation; CLI commands do not display the app's confirmation screen.
No npx package is published.

The optional `./pear-preview megabonk` command requests automatic installation
and normal Steam launch of the first validation game. It does not bypass ownership
or authentication. `play` remains its explicit legacy alias, not the default.

## Tested scope

The corrected signed app and its shared CLI completed official Steam login,
automatic owned Megabonk installation and normal Steam launch on M4 Pro, 24 GB,
macOS 26.5.2 (25F84). The game reported Steam initialization and Direct3D 11 on
Apple M4 Pro; the owner confirmed normal menu/input and normal exit. This uses
Pear's source-built Wine 11.0/CodeWeavers 26.3 candidate with DXMT 0.80,
`pear-wine11-cw26.3-dxmt0.80-signed-v2`, and game build 21750826. The app, CLI and
runtime received Apple notarization acceptance. See the
[Stage 1 record](../mydocs/working/task_m3_47_stage1.md) for exact identities.

Earlier replacement-runtime trials also received owner confirmation of extended
play, audio and retained progress after relaunch. Active play duration was not
measured, and these observations do not substitute for final-package tests.

Stage 2 recorded bounded interrupted-setup recovery, reinstall and local save
restoration. The owner reported completing the preview.1 browser installation,
fresh standard-account setup, requested twenty-minute active-play checklist and
save/relaunch without problems on the same Mac. Exact duration and graphics
settings were not supplied. This is owner-reported evidence, not an instrumented
performance measurement or a second physical Mac test. The host already had
Rosetta and Xcode installed. The preview.2 interface passed first-run consent,
download progress, cancellation and retry. The final signed-v3 runtime passed
requester-confirmed twenty-plus active gameplay minutes, input and audio. The
final signed preview.2 app passed retained-login launch, latest-progress
preservation after relaunch and normal exit. Its public DMG, CLI and runtime
passed anonymous HTTPS checksum verification. On October 15, the owner confirmed the final preview.3 public-download,
fresh standard-account setup, Steam/game launch and save/relaunch checklist
without problems, then deleted the test account. No repeat is required; this
is owner-reported evidence and not an independent second-Mac reproduction. See the [dated verification record](../mydocs/working/task_m3_47_stage3_preparation.md).
No all-game, Steam Cloud, controller, performance or power claim is made.

The previous login-window close issue was corrected in signed-v3. One real
unauthenticated close passed without leftover owned processes, and signed-app
Steam-menu exits also passed. Closing Pear still does not quit Steam or games.

## Data and recovery

Pear stores its environment under `~/Library/Application Support/Pear Preview`.
The preview.3 app name changes to Pear, but this data path and its bundle identifier
stay unchanged. Close Steam and the old app before upgrading. Once Pear is
installed, the older Pear Preview.app can be removed; keep the data folder.
Keep this folder: it includes Steam account state, downloaded games and saves.
Removing the Pear app alone does not remove this folder. Do not include it in
bug reports or share it as an installation package.

If a download fails, keep your data and retry. If Pear reports a changed runtime
or incompatible state, retain the folder and report the exact error; automatic
repair/rollback is not yet qualified. Do not delete the environment to fix a
startup problem. Existing working state is more important than a clean reinstall.

Use [Get help](SUPPORT.md) for a startup problem or [report a game result](compatibility/README.md) for a compatibility observation. Include the Pear version, Mac model, macOS version, affected game and visible error.
Exclude passwords, tokens, QR codes, account details, raw Steam logs and saves.

## Components and release boundaries

Pear uses a pinned externally downloaded runtime and the official Valve installer.
Game downloads come through Steam. Pear's app/CLI packages contain no game files,
Steam account data or Wine runtime payload. See the [component record](../preview/THIRD_PARTY_NOTICES.md).
Pear original code is [GPL-3.0-or-later](../LICENSE); upstream components retain
their terms. The release notice/source comparison is recorded; final binary and source
packages must be paired and made available at release. Downloading separately
is not a blanket exemption from obligations.
