# Task #47 Stage 3 preparation: signed distribution candidate

Status: Stage 3 in progress. This is an interim receipt, not stage completion.

The requester approved Stage 3 and the protected GitHub signing deployment.
The candidate source is `f9d95781b5460644d9aba25e2bac68faddbdf98f`.
CI: https://github.com/postmelee/pear/actions/runs/38270025717

## Verified scope

- Portable fixtures: 66 passed, no skips. Hosted ARM64 Rust fixtures: 22 passed.
- Developer ID app, CLI and DMG notarization: Accepted; protected credentials cleaned by CI.
- One-time PEAR_SIGNING_APPROVED_SHA repository variable removed after success.
- Downloaded candidate hashes match the package manifest.
- Local read-only DMG integrity/signature/staple/Gatekeeper checks passed.
- Mounted app has the expected 27-file allowlist, valid seal and staple; image detached.
- No local app, Wine, Steam or game was executed during these checks.
- Exact Pear source archive and runtime/source-kit hashes prepared without copying the runtime.

| Artifact | Bytes | SHA-256 |
|---|---|---|
| Pear-0.1.0-preview.1-macos-arm64.zip | 5299832 | `cee04542bc239a66679f21b60dce31ed81e4e9e8b1a6c50bc65819a5311ba918` |
| pear-preview-0.1.0-preview.1-macos-arm64-cli.zip | 337641 | `c9681ba27afc9d2ecfa304704d1c16f0e4b9aad0f2be780f142fe6d2bbbc4fa1` |
| Pear-0.1.0-preview.1-macos-arm64.dmg | 5414660 | `9422328323ef148dc6d32171f6a75af90eb014dea2dbc03d5f78160815b451f4` |

| Submission | Accepted ID |
|---|---|
| app | `b8a58241-15d7-4c40-a4e5-7a24ae702623` |
| cli | `cc31b416-7cd7-485d-899a-cd08cdd9d8f4` |
| dmg | `e4c3402e-d11d-4173-9d52-52bffbd78df7` |

## User-facing wording

Use the same brief line in release notes and the download page:

> This release uses Wine 11.0 and DXMT 0.80.

The runtime is downloaded separately, so “uses” avoids implying that the small
DMG contains it. Keep minimum build target (Apple Silicon, macOS 26) distinct
from observed runtime hardware/OS (M4 Pro, 24 GB, macOS 26.5.2). Do not turn
24 GB into an unsupported RAM minimum. Full source/patch/component detail
belongs behind the existing component link.

## Remaining admission

Actual browser-delivered clean-user setup, measured twenty-minute active play
and save/relaunch remain pending on the final candidate. The compiled runtime
URL is reserved under v0.1.0-preview.1 but no GitHub release exists yet.
A public qualification prerelease is a proposed way to validate the exact
download route; it requires an explicit change to the current rule against
release upload before those checks. No upload or availability claim was made.
Prepared review materials remain in the ignored task-owned Stage 3 distribution
directory; the website stays unavailable until qualification completes.

A fresh standard user on the same Mac is the approved bounded clean-setup
option, not a second physical Mac. Account creation remains a direct requester
action. Preserve the original user, authenticated state and saves.

## Retention

Keep .build/task47/stage3/ci-signed-f9d9578 and distribution-f9d9578 through
release review (approximately 22 MiB combined logical package/source bytes).
Existing runtime and source kit were reused in place. Hosted artifacts expire
after fourteen days; preserve their hashes/receipts before expiry. Private state
and older recovery baseline remain protected. No other chat was invoked.
