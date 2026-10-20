# Task #62 Stage 3.1 — Signed qualification preparation

GitHub Issue: [#62](https://github.com/postmelee/pear/issues/62)
Approved consolidated plan: [task_m3_62.md](../plans/task_m3_62.md)
Stage: 3.1 — preparation only; real signed replacement is not qualified.

## Stage Purpose
Prepare protected CI to produce an older updater-enabled baseline and newer
notarized target, retaining the accepted #63 UI and unchanged runtime. Context:
root/host rules, #62 approved plan, Stage 2, task-stage-report and daily-board
procedures. The requester accepted the expanded release-notes UI and explicitly
authorized signed qualification in this thread on 2026-10-20.

## Artifacts
| File | Change summary |
|---|---|
| preview/update-public.json | Dedicated public Ed25519 key, qualification/stable feed locations, builds 6 and 7 |
| preview/configure_update.py | Require signed feeds when updates are configured |
| preview/update_baseline.py | Derive baseline from exact signed target; retain nested bytes; separately sign, notarize and assess |
| preview/test_update_baseline.py, test_update_packaging.py | Configuration admission and signed-feed coverage |
| preview/package.py | Bind app build, version, feed and public key in manifest |
| preview/Launcher.swift, SparkleUpdate.swift, UpdateReleaseNotes.swift | Same-version build labels; accepted notes area extends to footer with 16-point gap |
| .github/workflows/preview-candidate.yml | Explicit qualification-pair dispatch; unchanged protected environment and exact SHA gate |

## Body Change Scope / Lossless Preservation
Only planned app/build and mydocs locations changed. Public documentation, server,
installed applications, authenticated prefixes, games and saves are unchanged.
Private Ed25519 material remains in the dedicated login Keychain account; only the
public key is tracked. Upstream framework/tool bytes and licenses are retained.
No runtime rebuild, full runtime copy or distribution publication occurred.

## Verification Results
Local Apple Silicon macOS 26.5.2 / Swift 6.3.3, deployment target macOS 15.
Reused exact admitted Sparkle 2.10.0 input from Stage 2. Rebuilt the changed app and
re-ran affected native/adapter/configuration suites; runtime gameplay evidence is
unchanged and was not repeated.

```sh
PEAR_PREVIEW_BUILD_ROOT="$PWD/.build/task62/app" bash preview/build.sh
python3 -B preview/ci_checks.py
python3 -B tools/check_governance.py
python3 -B tools/check_source_notices.py --base HEAD
git diff --check
```

- App/CLI build, native suites and ad-hoc signature verification passed. This is
  not Developer ID/notarization or actual Sparkle replacement evidence.
- 74 portable fixtures passed, zero skipped/errors/failures. Baseline admission
  rejects mismatched identity/build/feed/key and non-increasing build numbers.
- Committed public configuration was projected to a disposable plist and passed
  baseline admission. Workflow parsed; explicit dispatch defaults false and the
  pear-preview-signing environment remains required.
- Governance: 40 documents / 378 targets passed before this report. Incremental
  source notices and whitespace passed; rerun after this report before commit.
- Expanded notes UI compiled, displayed and was accepted by the requester. Build
  logs: .build/task62/qualification-preflight.log and qualification-portable.log.
  A scroll attempt was interrupted by concurrent user interaction; no automated
  scroll-pass claim is made for that attempt.
- Continuous frozen-source-to-manual-response timing is unavailable for this
  iteration; no latency baseline or summed independent timing is claimed.
- CI notarization, real old-to-new replacement, offline/invalid/install recovery,
  Steam relaunch de-duplication and exact signed macOS 15 checks remain unperformed.

## Artifact Disposition
| Artifact/root | State | Owner/consumer | Identity/recovery | Release condition |
|---|---|---|---|---|
| .build/task62 admitted Sparkle | Retained immutable | #62 build/signing | Stage 2 digest and inventory | Final qualification complete |
| .build/task62/app and logs | Retained local candidate/evidence | #62 | Source at this commit; local ad-hoc build | New signed pair verified |
| .build/task63-ui | Retained accepted preview | Requester/#62 | Shared source; synthetic data only | Signed UI verified |
| Dedicated Keychain update key | Retained private signing authority | Future update publisher | Public key/account in update-public.json | Preserve through release lifecycle |
| Hosted signed pair | Planned, not yet produced | #62 actual replacement | Exact CI SHA, manifest and baseline receipt | Keep through qualification/handoff |
| Existing runtime/releases/private data | Preserved | #47/#63/requester | Existing pins/state | No deletion in this substage |

Filesystem available space was approximately 14 GiB; no measured free-space delta
or logical/allocated size claim. Hosted pair has no runtime payload. Keep all
previous signed inputs until the new pair is verified; no recovery bytes deleted.

## Residual Risks
- The baseline derives from the new source with an older build number. It proves
  updater-enabled app replacement, not a legacy preview.4 automatic update.
- Qualification uses a separate feed; stable URLs and public release remain gated.
- Actual baseline signing/notarization helper has only admission-fixture coverage
  locally; the protected hosted run is the first end-to-end execution.
- Signed artifacts, feed signatures, active-session/race behavior and persistent
  data preservation still require the remaining Stage 3 checks.

## Impact on Next Stage
Push this exact revision and dispatch the pair workflow, retaining all required
checks. Obtain the existing GitHub environment approval when requested. Validate
returned archives and notarization before any local replacement, then sign a
separate qualification appcast with the dedicated local Keychain account.

## Approval Request
Routine continuation is already explicitly authorized by the requester and #62.
The GitHub protected signing approval remains a separate user action. This report
completes preparation only and does not authorize claiming release qualification.
