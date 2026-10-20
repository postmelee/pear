# Pear 0.1.1

Fixes a first-install error in 0.1.0 that could stop setup with “This folder contains unrelated files.” Pear now establishes its local installation folder before creating run history and safely recognizes the history-only folder left by the affected version.

**Apple Silicon · macOS 15+ · Rosetta required**  
Uses the unchanged **Wine 11.0 and DXMT 0.80** runtime.

## If setup stopped in 0.1.0

Quit Pear with **Pear → Quit Pear** (Command-Q), download this version and replace Pear in Applications. Open Pear again and choose **Download and install**. **Keep `~/Library/Application Support/Pear Preview`; do not delete your data to recover setup.** Existing history and sharing preferences are preserved. Unknown files are still refused, and recovery waits if another Pear is using the history.

The affected first-install screen cannot reach the normal app-update flow, so use the DMG or Homebrew for this recovery. Already configured installations can use **Update and launch**. Quit Steam and games before installing an update.

[Download Pear for Mac](https://github.com/postmelee/pear/releases/download/v0.1.1/Pear-0.1.1-macos-arm64.dmg)

Homebrew: `brew update` then `brew upgrade --cask postmelee/tap/pear`. New installations: `brew install --cask postmelee/tap/pear`. Recognized Homebrew-managed installations use Homebrew instead of Sparkle replacement.

## Verification

The final Developer ID signed and Apple-notarized app completed installation and opened Steam in both an empty environment and a copy of the history-only environment that reproduced the 0.1.0 failure. The owner confirmed normal login text and QR display without signing in. History and sharing preferences were preserved. These checks ran on M4 Pro / macOS 26.5.2.

The exact signed app and CLI passed startup and signature checks on macOS 15.7.9 ARM64 CI; Steam UI and gameplay on macOS 15 remain unverified. Regression tests include active-observer refusal, unknown-file and link protection, and byte-preserving CLI recovery with real Swift history snapshots.

The runtime is unchanged. Earlier Megabonk gameplay and save/relaunch results retain their recorded scope; long gameplay is not repeated for this launcher fix. Compatibility is not guaranteed for every game or Mac.

## Source and downloads

Use `SHA256SUMS` to verify downloads. The app ZIP is the Sparkle update archive; ordinary installation uses the DMG. The optional CLI has no automatic updater.

App/CLI source: `pear-source-c582c93.tar.gz`, commit `c582c93fddaf31c5ef271d85f4c60081299e6bad`, version 0.1.1/build 9. The unchanged runtime and corresponding source remain in the [runtime release](https://github.com/postmelee/pear/releases/tag/v0.1.0-preview.2). Pear original source is GPL-3.0-or-later; third-party notices are retained.

[Updates and recovery](https://github.com/postmelee/pear/blob/master/docs/rosetta-preview.md#app-updates) · [Reporting and privacy](https://github.com/postmelee/pear/blob/master/docs/reporting-and-privacy.md)

[Build and signing](https://github.com/postmelee/pear/actions/runs/39399333270) · [Signed macOS 15 check](https://github.com/postmelee/pear/actions/runs/39400794147)
