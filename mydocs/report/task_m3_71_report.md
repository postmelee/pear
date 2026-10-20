# Task #71 — First-install recovery and 0.1.1 delivery

GitHub Issue: [#71](https://github.com/postmelee/pear/issues/71)
Milestone: M3 — Rosetta-based Megabonk Preview

## Work Summary

Three stages repaired the 0.1.0 first-install ownership error and delivered signed/notarized 0.1.1/build 9. Pear initializes its installation root before recording history and safely adopts only the recognized history-only layout left by the affected version.

## Changed Files and Impact Area

| Area | Change | Impact |
|---|---|---|
| `preview/src/` and native launcher | Initialization ordering and bounded legacy-history adoption | First installation and recovery |
| Native/Rust/portable checks | Real Swift history regression and rejection cases | Preservation and ownership safety |
| Existing README, user guide, release notes and catalog translations | Recovery instructions and 0.1.1 links | Public distribution |
| Sparkle appcast / Homebrew cask | Signed archive and DMG version/hash | Updates |

## Document Location Verification

Existing public guidance remains in README, `docs/rosetta-preview.md`, `preview/updates/` and catalog content as approved in [the plan](../plans/task_m3_71.md). Plans, stage reports and this report remain under `mydocs/`. No new product-documentation root was introduced.

## Quantitative Before/After Comparison

| Metric | Before | After |
|---|---|---|
| Release/build | 0.1.0 / 8 | 0.1.1 / 9 |
| Recognized history-only first installation | Refused as unrelated files | Preserved and installed |
| Final signed installation scenarios | Failure reproduced | Empty and failed-root paths passed |
| Public delivery verification | Pending | Nine assets hash-matched; public update passed |

## Verification Results

| Acceptance criterion | Result |
|---|---|
| Preserve data | CLI exact-byte checks and real app semantic history/consent preservation passed |
| Refuse unrelated files and unsafe aliases/concurrent ownership | Regression checks passed |
| Empty and failed installations | Signed app completed both; requester confirmed Steam login UI |
| Signing/notarization | Protected run 39399333270 passed |
| Minimum OS startup | Exact signed macOS 15.7.9 ARM64 run 39400794147 passed |
| Public Sparkle update | Actual installed build 8 replaced with 9; valid signature; Steam opened once; requester confirmed normal UI |
| Release, website and Homebrew | v0.1.1, PR #73/Pages and tap PR #4 published and verified |

### Stage Verification Results

- [Stage 1](../working/task_m3_71_stage1.md): repair and regression evidence.
- [Stage 2](../working/task_m3_71_stage2.md): exact signed packages and installation qualification.
- [Stage 3](../working/task_m3_71_stage3.md): public retrieval, update, localization and Homebrew verification.

## Retention Handoff

| Artifact/root | State and consumer | Recovery reference | Release condition |
|---|---|---|---|
| Public signed/source assets | Published; users/release maintenance | v0.1.1 and Stage 2 SHA256s | Retain released versions |
| `.build/task71` receipts and original build 8 | Retained; #71 delivery review | Public assets plus local manifests | Review and verified evidence handoff |
| Private recovery/history snapshots | Retained privately; requester recovery | `.build/task71/private` | Explicit safe retention decision; never upload |
| Isolated trial runtime/prefix/cache | Removed after owned exit | Exact runtime input retained | Completed |
| Actual default installation and `/Applications/Pear.app` | Preserved, updated, in use | Installed build 9 | User-managed; not disposable |
| Worktree and unrelated `analysis/`, `research/` | Retained | Git plus ignored/private evidence | No removal until dependent/private material is preserved |

The requester intentionally reopened Steam to play after confirming closure of the update-test login window. Do not terminate that session or claim it is a remaining failed shutdown. No additional gameplay qualification was required.

## Residual Risks and Follow-up Work

Steam UI and gameplay on macOS 15 remain unverified; macOS 15 CI establishes signed startup only. No full Homebrew install or browser drag-install was repeated. Game compatibility is not universal. The isolated-root Sparkle trial lost its environment override on restart; the subsequent actual default-path trial passed. Timing lacked a continuous frozen-source baseline and is not presented as a performance result.

## Approval Request to Task Requester

The requester explicitly authorized repair, verification and redistribution. Delivery is complete; this report preserves the acceptance evidence and retention boundaries.
