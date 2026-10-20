# Task #71 — First-install recovery and Pear 0.1.1

Issue: https://github.com/postmelee/pear/issues/71
Milestone: M3 — Rosetta-based Megabonk Preview

## Approval and scope
The requester explicitly authorized preservation-first repair, empty and already-failed installation validation, and v0.1.1 redistribution with Sparkle, Homebrew and download links on 2026-10-20. This plan records that approved scope. Do not modify unrelated analysis/research files or #70 website localization.

## Design and reuse
Reuse the Rust Session admission/locking and Swift reporting store. Initialize the owned state root locally before constructing reporting. Keep setup-info read-only. Recover only the known 0.1.0 history-only layout, validating regular files, directory ownership, recognizable reporting schema and observer exclusivity before root adoption; reject unknown entries and aliases. Never rename/reset/delete history, consent, prefix or saves. Retain Rust/Swift and pinned Sparkle 2.10.0; existing GPL notices and upstream terms remain.

## Stages
1. Reproduce and fix ownership ordering; test empty/legacy/unrelated/alias/concurrent states and reporting preservation.
2. Build/sign/notarize version 0.1.1 build 9; actual empty and failed-root app setup, existing-state preservation, macOS 15 CI and 0.1.0 update checks. No changed runtime or repeated long gameplay.
3. Publish admitted assets, signed feed, release notes, Homebrew and download links; anonymous retrieval and final report.

## Document location judgment
Update only existing README, docs/rosetta-preview.md and release guidance if required; existing catalog version links and preview/updates release note/feed. Task plan/stage/final evidence goes under mydocs/. These are necessary to the explicitly requested version alignment; no new product-documentation location.

## Verification
Exercise actual bundled CLI initialization before Swift history creation, preserve exact failed history bytes and semantic consent/records after app reopening, reject foreign files/symlink/hardlink roots/history and active legacy observer. Run relevant Rust/native suites and portable CI, exact signed artifact checks and macOS 15 startup. Reproduce first-run installer with normal app UI in isolated per-run roots. Keep network/Steam UI/user input observations separate from fixtures. Verify signed public feed and hashes and Cask versions. Compare source notices against master.

## Artifact lifecycle
Reuse unchanged admitted Wine/DXMT archives and Sparkle from retained task47 worktree after identity checks. New objects and evidence belong to .build/task71; use a separate target/output, do not alter signed build 8. Two isolated installation roots may each need a runtime and prefix to establish actual first-run behavior; they share no writable runtime state. Budget approximately 4–6 GiB additional peak including local/CI app packages, no game downloads. Initial filesystem check: 8.9 GiB available on /dev/disk3s5. Reassess before substantial runtime creation. Retain only receipts and signed candidates through public verification; user state/private recovery is never disposable. No private data in Git/releases.

## Timing
Record wall and monotonic phase boundaries from frozen source through local build and operable UI; user response waiting separately. No invented baseline or summation of unrelated runs.
