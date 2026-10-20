# Task #71 Stage 2 — Signed installation qualification

Issue: [#71](https://github.com/postmelee/pear/issues/71)
Plan: [task_m3_71.md](../plans/task_m3_71.md)

## Stage purpose and scope
Qualify the unchanged Stage 1 source as 0.1.1/build 9 and prepare the approved delivery channels. The task-stage-report procedure applies; the requester explicitly authorized verification and redistribution. App source is frozen at c582c93fddaf31c5ef271d85f4c60081299e6bad. Only user/release guidance, existing website links and signed feed follow it; no runtime changes.

## Verification
- Protected build/sign/notary run [39399333270](https://github.com/postmelee/pear/actions/runs/39399333270) succeeded after requester approval.
- Exact signed macOS 15.7.9 ARM64 check [39400794147](https://github.com/postmelee/pear/actions/runs/39400794147) passed. This covers startup/signatures, not Steam UI or gameplay on macOS 15.
- Local app/CLI signatures, team requirement, notary tickets, app Gatekeeper assessment and DMG staple passed.
- Actual signed CLI passed the cross-language regression suite against the installed public 0.1.0 CLI, including exact-byte recovery, active-owner refusal and clean initialization.
- On M4 Pro / macOS 26.5.2, the final signed app installed Steam in a history-only root copied from the failed environment. Public 0.1.0 had reproduced the error on that copy. All history/consent values survived (Swift Set serialization order normalized).
- A separate initially absent root displayed welcome; Continue without sharing retained localOnly and an empty queue. Installation completed and Steam opened.
- Requester confirmed readable login text/QR and closed without login for both environments. After quitting Pear, no owned Steam/Wine/Pear processes remained. No game or account used.
- 116 docs/catalog tests passed. Download page preview was prepared at localhost:8971/download/#app. Accepted UI layout is unchanged; a recovery paragraph and version links are added.
- Upstream Sparkle generated/signed the build 9 feed. Independent CryptoKit verification with only the public key passed both feed and exact archive. Source archive matched all 1,663 committed blobs/symlinks.

## Immutable outputs
| Artifact | SHA256 |
|---|---|
| Pear-0.1.1-macos-arm64.zip | 5bd7b953bcf549b667fdbbb4dc3ab7feb993b2faef874d9b2dd2901a5ffd2104 |
| Pear-0.1.1-macos-arm64.dmg | 15a0343ba003e3cc74277387d098b7ca8c54cc07dba4b600ff9afb211c94cbae |
| pear-preview-0.1.1-macos-arm64-cli.zip | b88429a6cfd3543efa2c3b87e12db25fed1db9e559863130e55a25d8e21654f9 |
| pear-source-c582c93.tar.gz | abc3b43b0f0669ee42179afdae693b5e9a1f73fb88d7925a1b529759a64544f1 |

## Artifact disposition
Task-owned .build/task71 retains signed packages, source, receipts, and private recovery snapshots. The completed failed-root trial's runtime/prefix/cache were removed only after no owned processes remained; history and evidence stay. Measured filesystem free bytes changed from 1,772,654,592 to 6,728,339,456 during cleanup; this is a filesystem observation, not exclusive allocation accounting. Empty-root installation is retained for the public-feed build8-to9 trial. Default user data and installed /Applications/Pear.app remain preserved. No authenticated state, history or secrets enter packages.

## Timing and residual scope
Phase wall/monotonic values are retained locally; continuous frozen-source-to-manual-response latency was not instrumented and is not claimed. User response waiting is distinct from build/installation observations. Earlier unchanged runtime gameplay is reused only in its prior scope; no long gameplay repeat.

## Next stage
Publish exact assets before activating the new feed/website, then verify anonymous hashes and actual public-feed 0.1.0-to-0.1.1 replacement using the preserved app copy and ready test root. This public-feed check necessarily follows publication; it is not yet marked passed. Align Homebrew, complete delivery report and preserve required recovery evidence. Existing requester authorization covers this continuation.
