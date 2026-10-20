# Building and releasing the Steam preview

Status: v0.1.0 retains the preview.4 change that lowers the app/CLI deployment target to macOS 15 and reuses the
exact preview.3 runtime. Final signed startup checks passed on macOS 15.7.9 and
26.5.2; earlier fresh-account/gameplay checks retain their original artifact scope. See the [player guide](../rosetta-preview.md)
and [component record](../../preview/THIRD_PARTY_NOTICES.md).

## Build one shared core

Use an Apple Silicon Mac with the Xcode command-line tools and Rust 1.94 or later.
Current evidence uses Rust 1.94.1 and Swift 6.3.3. These are developer prerequisites;
players use prebuilt artifacts. The candidate targets macOS 15.0 and ARM64.

From the repository root, admit pinned Sparkle and fetch locked dependencies,
then build:

```sh
python3 -B preview/sparkle_input.py --download --output .build/task62/admitted
cargo fetch --manifest-path preview/Cargo.toml --locked
preview/build.sh
```

The admission helper verifies the official Sparkle 2.10.0 archive digest, framework
inventory and upstream signature. Do not use an arbitrary installed framework.

The script runs locked/offline tests and a release build, then builds the Swift
window and seals a local development app. Outputs are under `.build/task47/preview`;
`PEAR_PREVIEW_BUILD_ROOT` selects an alternate app output. The Cargo cache is reused.
The output app is Pear.app from preview.3 onward. Its bundle identifier and
existing Pear Preview data directory are preserved across the display-name change.
The app and standalone CLI use the same Rust binary. Default/`steam` opens the
library; `megabonk` requests the bounded reference-game install/launch flow.

## Branding assets

The requester supplied `preview/assets/pear_icon.png` for the distributed app and
`docs/assets/pear.png` for documentation and the catalog favicon. Preserve the
source artwork. `preview/build-icon.sh` uses macOS `sips` and `iconutil` to generate
16–1024 pixel representations in `Contents/Resources/Pear.icns`; the bundle's
`CFBundleIconFile` points to that file. The package allowlist requires it.

Regenerate the 64-pixel catalog favicon after an approved source-image change:

```sh
sips -z 64 64 docs/assets/pear.png --out docs/assets/favicon.png
```

Changing an icon changes the app's sealed resources. Rebuild, sign, notarize,
staple and repackage; never modify a sealed candidate in place. README uses the
original pear image, not the macOS tile. Branding is not runtime qualification.

## Signing and notarization

Use only an owner-authorized Developer ID Application identity. Keep private keys
in Keychain. Set `PEAR_SIGNING_IDENTITY` locally to its identity name or SHA-1 and
run the build. Release mode signs the nested CLI and app with Hardened Runtime
and a secure timestamp, with no entitlement exceptions. Ad-hoc builds are not
ordinary-user release artifacts. Never re-sign an upstream runtime to conceal a
missing permission or disable macOS protections.

Register Apple notarization credentials interactively on the maintainer's Mac:

```sh
xcrun notarytool store-credentials pear-notary --team-id YOUR_TEAM_ID
```

Use the secure prompts. Do not put passwords, API private keys or credentials in
arguments, this repository or logs. `pear-notary` is only a Keychain profile name.

Prepare candidate archives with `preview/package.py --app PATH --output PATH`.
Submit each app and CLI archive with `xcrun notarytool submit ARCHIVE
--keychain-profile pear-notary --output-format json`. Poll its submission ID with
`notarytool info`; retrieve `notarytool log` when rejected. Submission is not
acceptance. Retain sanitized IDs and outcomes, not credentials.

After acceptance, staple the app using `xcrun stapler staple APP`, validate it,
then rebuild the final archives with `preview/package.py --release`. Stapling
changes package bytes: compute SHA-256 only after it. Standalone CLI archives
cannot be stapled like an app; verify the CLI's accepted notarization and the
actual downloaded command on a clean online Mac. Do not assume the app's ticket
covers a different CLI binary. Check the app with `syspolicy_check distribution`
and the CLI with `codesign --verify --strict -R=notarized --check-notarization`.
`spctl --type execute` applies app-specific policy and rejects a raw command-line
binary as not being an app even when its notarization is valid. These preliminary
checks follow [Apple's product-type guidance](https://developer.apple.com/forums/thread/130560)
(revised December 5, 2024; reviewed October 11, 2026); they do not replace the
required clean browser-download and actual execution tests. A source archive must
match the final committed release revision.

## DMG and CLI delivery candidates

The protected CI signing job uses `preview/sign_candidate.py` to retain app and
CLI ZIPs and build a DMG with the audited app plus an Applications shortcut.
The DMG receives its own Developer ID signature, Apple notarization submission
and staple. Image verification, staple validation and Gatekeeper's disk-image
assessment must pass before any packages leave temporary staging. `SHA256SUMS`
and the package manifest bind the final stapled bytes. A failed DMG submission
prevents the transaction from publishing the other candidate packages.

CI outputs remain qualification candidates. Validate actual browser download,
DMG mount, drag to Applications and first launch under normal protections before
claiming user-ready distribution. Keep the original signed app unchanged when
creating the image. CLI users receive the separate notarized archive; Homebrew
is not required for the initial app/CLI release.

## Current candidate checkpoint

Stage 1's corrected app invokes the original notarized Wine loader with
`start /unix`; it does not construct a new unsigned Steam app bundle around a
copied signed executable. That earlier bundle failed macOS resource-seal checks.
The replacement app/CLI passed same-host official Steam login, owned installation,
game Steamworks initialization, menu/input and normal exit. The
[Stage 1 report](../../mydocs/working/task_m3_47_stage1.md) binds the exact candidate,
notarization receipts and source/notice review.

The runtime URL in `preview/src/runtime_pin.rs` points to the immutable
`v0.1.0-preview.2/pear-runtime-signed-v3.tar.gz` asset, published with its matching
source kit as a qualification pre-release. Anonymous delivery and hashes passed.
The preview.3 release reuses these exact runtime bytes, names the app Pear and
adds Steam-opening feedback. Its app/CLI/DMG passed new signing and notarization
with matching e574ba1 source. Preserve published preview.1 and preview.2 assets. Recheck affected app
metadata, package contents and actual launch; do not rebuild the unchanged
runtime or repeat its sustained-play check for a display-name change.
Submission ZIPs are not final downloads: package after stapling and bind source
to the exact committed release revision. Final preview.3 clean-account delivery was confirmed by the owner on October 15
on the same physical Mac. Earlier account checks retain their own artifact scope.

## Release admission

Before any release upload or public-download claim:

- Include Pear's GPL-3.0-or-later text/scope notice and preserved component
  notices. Provide release-matching corresponding source, lockfiles and build
  scripts alongside downloads; a private source URL is insufficient.
- Resolve exact runtime component notices and corresponding-source obligations.
- Pass the required #47 game, setup-recovery, save and second-clean-environment
  checks. Same-host fresh prefixes do not establish browser-delivered installation.
- Verify final app/CLI signatures and notary acceptance, the app staple and
  distribution assessment, and the CLI explicit notarization requirement. Test a
  real browser download with normal security protections.
- Inspect app/CLI archive allowlists, checksums and matching source revision. Never
  include runtime downloads, Steam/game payloads, account state, saves or keys.
- Review the current source, relevant Git history and GitHub content before any
  requested repository visibility change. A private release link is not public.
- Preserve M1/R1 identities, task stage/report/commit requirements and remaining
  failures. Packaging success does not close Issue #47 or authorize a merge.

Publish only the approved exact artifacts and source revision. A preview remains
a pre-release; the authorized first stable release is v0.1.0/build 8. Keep the player guide and README download status synchronized
with actual availability. Do not replace failed tests with a disclaimer to promote
a release. Performance or Rust-port work is outside this delivery task.


## Sparkle feed and release coordination

The public key, stable feed URL and increasing build numbers are in
`preview/update-public.json`. The private Ed25519 key remains in the maintainer's
Keychain; it is not a CI secret or a client credential. Protected dispatch with
`stable_candidate=true` selects the stable feed; `qualification_pair=true` creates
a separate test pair. These inputs are mutually exclusive. Preserve the required
reviewer and exact approved SHA gate. Verify exact returned signed packages with
the separate `signed_run_id`/`signed_revision` macOS 15 workflow dispatch.

Build 8 is source `51fbe6f2dea42c82691d803ef02ae1663c087dd9`. Documentation/feed
changes after this revision do not change its admitted binary identity. Supply
that exact source archive alongside the release; do not describe a later docs
commit as the app's build source. Future app changes need new increasing builds,
new signing and affected verification.

Keep the GitHub body in `preview/updates/release-notes.md`. Convert that same
Markdown to HTML for upstream `generate_appcast --embed-release-notes`, select
the final GitHub release ZIP URL, disable deltas unless separately qualified,
and sign the feed with upstream `sign_update`. The app requires both a signed
feed and a signed archive. Independently verify both signatures with the public
key and match archive size/hash to the admitted manifest. Never hand-edit a
signed XML file. Its generated signature comments are retained rather than
adding a source notice that would invalidate the signature.

`preview/updates/appcast.xml` is copied byte-for-byte to `updates/appcast.xml`
by the catalog renderer, including scheduled catalog publications. Publish the
referenced exact release assets before deploying the feed. Check an anonymous
GET of the deployed feed, its signature, download URL and archive digest. Avoid
advertising a release before its assets are available. Keep existing preview and
runtime assets immutable. Update `postmelee/homebrew-tap` with the final DMG hash;
recognized Caskroom installations defer Sparkle replacement to Homebrew.

Legacy previews require a manual first installation. Keep successful signed
qualification evidence, source/notary manifests and recovery inputs until final
handoff; never publish authenticated prefixes, history or private diagnostics.
