# Task #62 Stage 3.2 — Signed replacement and archive rejection

GitHub Issue: [#62](https://github.com/postmelee/pear/issues/62)
Approved consolidated plan: [task_m3_62.md](../plans/task_m3_62.md)
Stage: 3.2 — signed pair execution; overall Stage 3 remains in progress.

## Stage Purpose
Execute the protected signed pair from source
`08bfd108e5f109f52e52bde1e051aa6af22fb9a8`, verify actual replacement and reject
an intentionally damaged archive. Context: root/host/test rules, approved #62
plan, Stage 3.1, task-stage-report and daily-board procedures. The requester
approved protected signing, Keychain use and actual update verification in this
thread. No further source changes or runtime rebuild were needed.

## Artifacts
| File or artifact | Change summary |
|---|---|
| CI run 39378692249 | Build 7 target and derived build 6 baseline, separately signed/notarized |
| CI run 39379625792 | Exact signed target startup on macOS 15.7.9 arm64 |
| Qualification pre-release | Signed appcast and exact target archive; not stable/Homebrew/homepage |
| .build/task62/actual-update-verification.json | Exact target inventory, security checks and private-data comparison results |
| .build/task62/qualification-invalid/result.json | Real archive signature rejection and baseline recovery |
| mydocs/orders/20261020.md | Reflect completed qualification subset and outstanding checks |

## Body Change Scope / Lossless Preservation
Only task reporting changes are committed in this substage. Runtime, public user
documents, stable feed and homepage downloads are unchanged. The test apps live
in separate task-owned directories; `/Applications/Pear.app` was not replaced.
Existing Steam installation and data were reused without a full prefix/runtime
copy. Private history/save backups and diagnostics remain ignored and local.

## Verification Results
Local Apple Silicon macOS 26.5.2. Sparkle 2.10.0, framework build 2064, unchanged
admitted upstream archive. Protected [pair CI](https://github.com/postmelee/pear/actions/runs/39378692249)
passed 74 portable fixtures, native builds, macOS 15 execution, signing and Apple
notarization. The separate [signed macOS 15 run](https://github.com/postmelee/pear/actions/runs/39379625792)
passed exact target startup/security checks; this is not gameplay evidence on 15.

- All returned archive sizes and digests matched their manifests. Both baseline
  and target passed Developer ID team, deep strict signature, staple and Gatekeeper
  assessment. The baseline receipt confirmed preserved nested bytes.
- The unavailable qualification feed fell through to Steam. The requester
  confirmed the existing library. This is a real unavailable-feed check, not a
  disconnected-network test; its first process filter cannot establish count.
- The signed feed showed build 6 -> build 7 and release notes from the same GitHub
  release body, converted to HTML. Feed and archive Ed25519 signatures were
  independently verified with the committed public key; no private key export.
- Later retained build 6 and launched one primary Steam process. Restarting Pear
  with Steam active skipped installation and retained the same Steam PID.
- Update and launch downloaded, replaced and automatically relaunched Pear as
  build 7, then launched exactly one primary Steam process. No external launch
  command was used to manufacture the relaunch observation. The requester
  confirmed a normal library and closed Steam/Pear.
- Installed build 7 matched all 123 target files/symlinks. Deep strict signature,
  staple validation and Gatekeeper assessment passed after replacement.
- Eleven save files remained byte-identical. History records, shared report
  mappings, consent and pending-delivery data remained semantically identical.
  JSON byte/order differences were only Swift Set/non-string Dictionary encoding
  order; comparisons normalized those structures, not their values.
- A separate baseline path downloaded a one-byte-damaged archive through a valid
  signed test feed retaining the original archive signature. Sparkle logged
  signature rejection, retained signed build 6 and opened Steam exactly once.
- The normal feed was restored and verified through normal and cache-busted GETs.
  An initial restore check saw stale content; later both matched the normal signed
  feed. The intentionally damaged public asset was removed; local evidence remains.

Key verification commands:
```sh
codesign --verify --deep --strict '-R=anchor apple generic and certificate leaf[subject.OU] = "XH6JHKYXV8"' <app>
xcrun stapler validate <app>
spctl --assess --type execute <app>
```
Per-file SHA-256 inventories, private semantic comparisons and scoped process
snapshots are recorded under `.build/task62`. UI actions used the native UI tool.
No game was run; unchanged runtime gameplay evidence was not repeated.

Timing: wall and monotonic stamps were captured before actual update activation,
at process observation and manual-confirmation recording. These are bounded
observations including tool/coordination time, not exact install latency. A
continuous frozen-source-to-confirmed-user-response baseline across CI and human
handoffs is unavailable; no sum of independent intervals is claimed as that metric.

## Artifact Disposition
| Artifact/root | Actual state | Owner/consumer | Identity/recovery | Release condition |
|---|---|---|---|---|
| Exact signed archives and extracted target | Retained | #62/#47 | CI manifest and source 08bfd108 | Final integration/qualification handoff |
| Task-owned updated app and recovery baseline | Retained | #62 | Build 7 exact target / separately signed build 6 | Remaining recovery/startup checks complete |
| Private update recovery | Retained, local only | Requester/#62 | Original app copy, 11 saves, history snapshot | Final data-preservation handoff |
| Invalid archive fixture and filtered diagnostics | Local only | #62 | One-byte mutation; signature-rejection receipt | Sanitized final report accepted |
| Public invalid archive | Removed after test | None | Local fixture retained | Completed |
| Public qualification feed and normal target | Retained, prerelease only | #62 | Signed normal feed restored | Qualification release retirement decision |
| Dedicated Keychain signing key | Retained private | Update publisher | Committed public key only | Preserve through release lifecycle |

No full runtime copy or substantive new build. Filesystem free-space change and
allocated sizes were not measured; archive size is not a free-space claim.

## Residual Risks
- Latest-build no-update startup, disconnected-network execution and remaining
  recovery/session cases must be reconciled before Stage 3 is marked complete.
  Existing policy/adapter fixtures are not described as actual signed executions.
- Successful replacement uses an updater-enabled derived baseline. Legacy preview
  apps without Sparkle still need one manual installation.
- Qualification uses its dedicated GitHub feed. Stable feed configuration/signing,
  final #63 integration evidence and #47 release publication remain outstanding.
- Failed archive validation is covered; it does not prove every disk/authorization
  failure during installation. Do not infer such coverage from this result.

## Impact on Next Stage
Finish the remaining Stage 3 matrix using these immutable inputs and preserve
normal feed restoration at each test boundary. Keep stable publication gated.
The UI is already accepted; no redesign or repeated long gameplay is required.

## Approval Request
Routine continuation is already explicitly authorized. This is a completed
substage report, not a claim that Stage 3 or v0.1.0 distribution is complete.
