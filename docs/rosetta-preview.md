# Pear Windows Steam preview

Status: [preview.2 qualification pre-release](https://github.com/postmelee/pear/releases/tag/v0.1.0-preview.2)
is public. App/CLI/DMG signing, notarization, anonymous download verification,
new-runtime gameplay and save/relaunch checks passed. Final fresh-account
installation of this exact runtime remains pending. The preview.3 candidate
renames the app to **Pear** and is awaiting its own signing and package checks.
Local development builds are not notarized releases.
[Release preparation](development/preview-release.md) tracks the remaining work.

Pear is intended to be free and open source. The preview prepares Windows Steam
on Apple Silicon so you can use your library without installing or configuring
Wine yourself. It currently requires Rosetta; the final Rosetta-free goal remains
in the [delivery plan](delivery-plan.md).

## Before using a release

The candidate is built for Apple Silicon and macOS 26 or later; actual execution
has only been observed on M4 Pro, macOS 26.5.2. Broader support is unverified.
Rosetta, internet access, a Steam account and ownership of games are required.
Allow several GB for setup plus each game's requirements. Steam's first update
can be larger than Pear itself. Runtime and game installation require storage
beyond the small Pear download.

## App experience

Once a verified release is published, its release page will provide the app,
checksums, exact requirements and test results. Open its DMG, drag the app to
Applications, then open Pear normally (Pear Preview in preview.2 and earlier).

1. On first setup in preview.2 or later, review the runtime and Steam installer download
   sizes, then select **Download and install**. Pear shows downloaded bytes and
   a progress bar; extraction and preparation show their current step. Steam
   self-updates and game downloads have separate, variable sizes. **Cancel**
   stops preparation; **Retry** continues with existing data preserved.
2. Steam may update itself. Sign in directly in the official Steam window using
   QR or your account; Pear does not request your password.
3. Choose a game from your Steam library, install it, then use Steam's Play button.
4. After setup, opening Pear checks the existing installation and opens Steam
   automatically without asking for download confirmation again. Steam may require an
   update or renewed sign-in; a fresh client download is not required on every run.

**About Pear** shows the Pear, Wine and DXMT versions. Full removal and automatic
runtime repair are not included in this interface.

You do not need a separate Whisky app or macOS Steam. Pear's status window can be
closed after Steam opens; that does not quit Steam or a running game. Quit games
and Steam through their own menus. Other games are selectable but unverified.

## Optional CLI

The CLI uses the same setup and state as the app. It does not require Node.js,
Python, Xcode or Rust on the player's Mac. After extracting a verified CLI release:

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
passed anonymous HTTPS checksum verification. Final fresh-account delivery of
this candidate remains pending. See the [dated verification record](../mydocs/working/task_m3_47_stage3_preparation.md).
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
their terms. The candidate notice/source comparison is recorded; final binary and source
packages must be paired and made available at release. Downloading separately
is not a blanket exemption from obligations.
