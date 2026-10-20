# Task #62 Stage 3.3 — Recovery matrix and stable candidate preparation

GitHub Issue: [#62](https://github.com/postmelee/pear/issues/62)
Approved consolidated plan: [task_m3_62.md](../plans/task_m3_62.md)
Stage: 3.3 — remaining qualification checks and build 8 preparation.

## Stage Purpose
Finish bounded-launch recovery checks on the signed qualification pair, strengthen
installer error callback coverage, and prepare the stable-feed candidate. Context:
root/host/test rules, approved plan, Stages 2/3.1/3.2, task-stage-report and todo
procedures. Continuation and final delivery are already authorized in this thread.

## Artifacts
| File or artifact | Change summary |
|---|---|
| preview/test_sparkle_adapter.swift | Installer/auth/relaunch failure and restart-store denial assertions |
| preview/update-public.json | Stable release build 8; retains qualification builds 6/7 |
| .github/workflows/preview-candidate.yml | Explicit stable_candidate dispatch, channel conflict rejection, unchanged protected signing |
| mydocs/plans/task_m3_62.md | Stable candidate scope, input reuse and evidence boundaries |
| .build/task62/no-update-result.json | Signed build 7 no-update execution |
| .build/task62/offline-harness | Process-scoped network-denial evidence and owned-process cleanup |
| .build/task62/cancel-update-result.json | Actual pre-install cancellation and retained build 6 |
| .build/task62/post-recovery-data-check.json | Final data preservation and empty process snapshot |

## Body Change Scope / Lossless Preservation
No production launcher, updater, runtime or reporting implementation changed.
Existing signed build 6/7 evidence remains bound to source 08bfd108. Only tests,
public build configuration, workflow and task records changed. No public user
docs, stable appcast, Homebrew or download page was published. Build 8 changes the
signed Info.plist/feed and therefore needs new CI/security/package admission.

## Verification Results
Local Apple Silicon macOS 26.5.2, Swift 6.3.3, target macOS 15. Reused exact
Sparkle 2.10.0 and signed apps admitted in Stage 3.2; no runtime/gameplay repeat.

| Scenario | Evidence and result |
|---|---|
| No update | Build 7 accepted the signed normal appcast, skipped the offer, opened Steam once and detected its window; requester confirmed termination |
| No outbound Internet | Exact signed build 6 ran under a task-owned sandbox-exec harness denying only outbound IP. Sparkle reported feed download failure with POSIX EPERM and continued to one Steam process. The Mac's network configuration and other apps were untouched |
| Cancel before install | The real signed update reached Preparing Pear update; Continue without updating retained build 6, opened one Steam process and detected its window |
| Timeout | Existing adapter watchdog test reran with the new fixture binary; real eight-second timer released once and rejected a late offer |
| Installer/auth/relaunch errors | Injected Sparkle error codes 4001/4004/4005 after ready-to-install; restart intent cleared, installing state ended, repeated callbacks acknowledged, Steam gate released exactly once |
| Restart-store denial | Injected Keychain write error prevented installer invocation, skipped update and released once |
| Data preservation | All 11 game save files and semantic history/consent/shared mappings unchanged after the complete sequence |
| Cleanup | No Pear, primary Steam, Steam web helpers/service or wineserver remained in the final snapshot |

The first offline harness denied all outbound transport, including Wine local
sockets; this was an invalid Steam-start oracle and was not counted as a pass.
The refined profile allowed local sockets and denied outbound IP only. Its wrapper
identity was not bound correctly by the UI tool after exec; the running exact Pear
path was selected after confirming its process. This is a harness limitation.
The inherited network restriction prevented Steam server access/library completion;
only updater error recovery and Steam process handoff are qualified, not offline
Steam usability or gameplay. Steam -shutdown returned zero but that restricted
startup remained; cleanup verified exact PIDs and open prefix/runtime files before
terminating 13 owned helpers. No blanket Wine termination was used. Subsequent
normal-network cancellation testing opened the Steam window and exited normally.

Commands/results:
```sh
xcrun swiftc -target arm64-apple-macosx15.0 -F .build/task62/admitted -framework Sparkle ... -o .build/task62/adapter-recovery-tests
.build/task62/adapter-recovery-tests
python3 -B preview/ci_checks.py
python3 -B tools/check_governance.py
python3 -B tools/check_source_notices.py --base HEAD
git diff --check
```
Native adapter assertions passed. Portable fixtures: 74 passed, zero skips/errors.
Both actual YAML configuration steps were parsed and executed for stable and
qualification selections; emitted plists had build 8/stable feed or build 7/test
feed, required signed feeds and disabled profiling. Python lacked PyYAML, so the
existing Ruby YAML parser was used without installing dependencies. Conflicting
channel flags are rejected before builds; protected environment/SHA gate unchanged.

Actual filesystem/privileged-installer failure was not forced on this Mac. Error
callback injection is explicitly fixture evidence, combined with real successful
replacement and real corrupt-archive rejection from Stage 3.2. It does not prove
all filesystem/power-loss failures. No unsupported universal recovery claim.
Wall/monotonic observation stamps are retained where captured; complete continuous
candidate-to-human-response latency is unavailable. UI wrapper binding delay is
coordination overhead, not Pear startup latency.

## Artifact Disposition
| Artifact/root | State | Owner/consumer | Identity/recovery | Release condition |
|---|---|---|---|---|
| Signed builds 6/7, CI archives and public qualification feed | Retained normal state | #62/release integration | Stage 3.2 hashes/receipts | Build 8 admitted and handoff complete |
| Offline launch wrapper | Removed after test | None | Small local profile/receipts retained | Completed; no persistent network policy installed |
| Private recovery copies and logs | Retained local/ignored | Requester/#62 | Save/history/app snapshots | Final preservation handoff |
| New adapter test binary | Retained disposable | #62 | Current fixture source, unchanged adapter | Final report accepted |
| Build 8 | Prepared configuration only | Release integration | New commit and future protected CI | Verify before publishing |

No full runtime copy or runtime rebuild. Allocated storage and filesystem free-space
delta were not measured; no storage-recovery claim is made.

## Residual Risks
- Build 8 is not yet signed/notarized/admitted. The stable feed has not been
  published; final release integration must bind it to exact asset signatures.
- Legacy preview apps without Sparkle still need a manual first installation.
- Final signed reporting integration, public docs/download/Homebrew alignment and
  release publication remain separate delivery work. No Issue is closed here.

## Impact on Next Stage
Push the exact prepared revision, select stable_candidate=true and retain all CI
checks. The existing GitHub required-reviewer approval remains a human action.
Admit the new candidate and verify its signed feed/reporting configuration before
final publication. Unchanged runtime gameplay evidence remains reusable.

## Approval Request
Routine continuation is already authorized. Request only the existing protected
signing approval when CI reaches that gate; no new broad approval is required.
