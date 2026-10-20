# Task #62 Stage 3.5 — Release feed and public guidance

Issue: [#62](https://github.com/postmelee/pear/issues/62)
Plan: [task_m3_62.md](../plans/task_m3_62.md)

## Stage Purpose
Prepare the approved first stable delivery around immutable signed build 8.
Use the task-stage-report/final-report workflow and approved documentation roots.

## Artifacts / Body Change Scope
- preview/updates/release-notes.md is the GitHub body and HTML appcast note source.
- preview/updates/appcast.xml is generated/signed by upstream Sparkle 2.10.0.
- The catalog renderer copies that signed XML without altering bytes; the existing
  daily Pages workflow triggers on feed changes and always carries the feed.
- README, docs index, player/privacy/release guides and existing download page now
  describe 0.1.0/macOS 15+, app updates, consent and legacy/Homebrew behavior.
- Homebrew 0.1.0/DMG SHA is staged on codex/pear-0.1.0 in the existing tap checkout.

No app/runtime source or signed bytes changed. Generated XML signature comments
are retained as the reviewed notice exception; adding a header invalidates it.

## Verification Results
Official generate_appcast used the admitted final ZIP, final v0.1.0 asset URL,
no deltas and HTML derived from the same Markdown body. sign_update used the
existing Keychain account without exporting its key. Independent CryptoKit checks
validated feed and archive Ed25519 signatures with only the committed public key.
XML identifies build 8, version 0.1.0, ARM64 and macOS 15.0. Stable feed is not yet
public at this checkpoint; public URLs are verified after release publication.

The exact source archive matched all 1,630 committed blobs/symlinks at 51fbe6f2.
Staging has only app/CLI/DMG, matching source, feed, checksums and sanitized
manifest/notary/provenance. All signed bytes retain Stage 3.4 hashes.

Docs/catalog: 116 tests passed. The existing allowlist test now also verifies
signed-feed byte preservation. Worker: 7 tests passed. Governance, notices and
whitespace passed. Homebrew cask Ruby syntax passed; install/upgrade was not run
against unpublished assets. User approved localhost:8953/download.html#app.
Agent browser access was blocked by URL policy; no bypass was attempted.

## Artifact Disposition
The signed candidates and small release staging/source archive remain ignored,
owned by final delivery; no runtime copy or rebuild. Keep the original private
recovery evidence and worktree until downloaded-byte checks and final handoff.
No allocated-space or net free-space recovery claim. Keychain key remains private.

## Residual Risks / Impact on Next Stage
Publish the exact assets, then deploy matching feed/website and update Homebrew.
Verify anonymous feed/archive signatures, actual download hashes and the daily
catalog run. Keep old releases immutable. Legacy apps need a manual bootstrap.
The requester has explicitly approved public deployment of the reviewed page.
