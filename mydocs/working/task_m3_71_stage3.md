# Task #71 Stage 3 — Public delivery and update qualification

GitHub Issue: [#71](https://github.com/postmelee/pear/issues/71)
Implementation plan: [task_m3_71_impl.md](../plans/task_m3_71_impl.md)
Stage: 3

## Stage Purpose

Complete authorized 0.1.1 redistribution and verify the public update path. Context and reuse boundaries remain those in the approved plan and Stage 2. Task-stage-report and task-final-report procedures apply.

## Artifacts

| Artifact | Outcome |
|---|---|
| v0.1.1 release | Nine admitted assets published, including corresponding source |
| Public appcast and English/Korean download pages | Version 0.1.1 active |
| Homebrew cask | Version and DMG hash updated |
| Installed app | Public Sparkle update replaced build 8 with build 9 |

## Body Change Scope / Lossless Preservation

Signed app source remains c582c93fddaf31c5ef271d85f4c60081299e6bad. Release guidance integrated the concurrently merged Korean website without replacing its layout or localization. No runtime rebuild. User history and sharing consent were preserved; no account, game or save data was deleted.

## Verification Results

- Release integration [PR #73](https://github.com/postmelee/pear/pull/73) merged as d4b9bd37369b6590cc775a99eed64c6255a6471c. Integration checks passed, including 121 documentation/catalog tests.
- Pages [39404556800](https://github.com/postmelee/pear/actions/runs/39404556800) succeeded. Assets were published before feed activation. Pages workflow was re-enabled; scheduled catalog publication remains active.
- Anonymous HTTPS retrieval of all nine release assets matched admitted hashes. Public appcast matched repository bytes; independent CryptoKit Ed25519 verification passed against the downloaded app ZIP. Downloaded DMG verified, mounted, and contained signed build 9.
- Homebrew [PR #4](https://github.com/postmelee/homebrew-tap/pull/4) merged as 9874a5113c4f4c7927697c396a7e237977c4366d. Public cask version/hash and Ruby syntax passed.
- A copied build 8 updated to build 9 through the public feed. Sparkle restart did not inherit the isolated-root environment override; this trial proves replacement, not Steam launch in that isolated root.
- Subsequently prepared the actual default installation using the exact admitted runtime archive. History bytes were unchanged during setup. Updated the actual `/Applications/Pear.app` from 0.1.0/build 8 to 0.1.1/build 9 through the public feed, without a root override.
- `codesign --verify --deep --strict /Applications/Pear.app` passed after replacement. History and consent were semantically unchanged. One primary Steam process opened automatically; Pear displayed “Steam window is open.”
- Requester confirmed normal Steam login text and QR, then closed without signing in. The requester subsequently intentionally reopened Steam to play. That active session is preserved; a final no-process state is not claimed. Both isolated installation trials had separately established clean owned-process exit.

Local evidence: `.build/task71/public-downloads/receipt.json`, `feed/verify-public.json`, `update/default-result.json`, `default-pre-update.json`, and `qualification.json`. Private evidence is intentionally excluded from Git.

Execution: M4 Pro/macOS 26.5.2; earlier exact signed macOS 15.7.9 startup checks retain only their stated scope. No repeated long gameplay, full Homebrew installation or browser drag-to-Applications test is claimed. Continuous source-freeze-to-manual-response timing was unavailable.

## Artifact Disposition

Both isolated trials' runtime/prefix/cache directories were removed after owned-process exit; ownership/history receipts remain. Empty-trial cleanup observed filesystem free bytes rise from 1,336,205,312 to 6,202,597,376; concurrent filesystem activity prevents exclusive attribution. Actual user installation remains intact and in use.

Retain `.build/task71` signed/source inputs, receipts, original build 8 backup and private recovery snapshots for delivery review. Worktree removal is deferred until those ignored artifacts have a verified recovery handoff and unrelated analysis/research ownership is resolved. Public artifacts are recoverable from v0.1.1 with Stage 2 hashes; private snapshots are not public.

## Residual Risks

Steam UI/gameplay on macOS 15 and universal game compatibility remain unverified. Existing limitations are disclosed in release guidance. No new runtime qualification claim.

## Impact on Next Stage

None. Delivery acceptance is complete; final report records retained evidence.

## Approval Request

Publication and verification were explicitly authorized by the requester. Report publication completes that scope.
