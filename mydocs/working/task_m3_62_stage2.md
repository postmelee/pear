# Task #62 Stage 2 — Local Sparkle integration

GitHub Issue: [#62](https://github.com/postmelee/pear/issues/62)
Approved plan: [task_m3_62.md](../plans/task_m3_62.md)
Stage: 2 — local integration; signed qualification remains Stage 3.

## Stage Purpose
Integrate upstream Sparkle with the accepted reporting UI and bounded Steam launch
policy. Preserve #63 consent/history and the existing runtime installation path.
Context: root, host and tests AGENTS; approved #62 plan and Stage 1; #63 Stage 2;
Sparkle 2.10.0 headers and official documentation; task-start and task-stage-report
procedures. This is the continuation explicitly authorized in this chat.

## Artifacts
| File | Change summary |
|---|---|
| preview/SparkleUpdate.swift | Main-actor custom driver, eight-second check deadline, independent download/extraction deadlines, late-callback rejection, install deferral |
| preview/UpdateEnvironment.swift | Homebrew ownership checks, scoped Keychain restart intent, actual cross-process CLI/install lock |
| preview/UpdateReleaseNotes.swift | Current/target presentation support, isolated WebKit notes with scripts/resources disabled and bounded display payload |
| preview/Launcher.swift, HistoryWindow.swift | Welcome/update ordering, existing-session reuse, install guard, UI integration |
| preview/sparkle_input.py, sparkle-files.json, sign_sparkle.py | Pinned input admission, strict inventory and inside-out helper signing |
| preview/configure_update.py, build.sh, package.py, sign_candidate.py | Public update configuration before signing and framework packaging |
| preview/test_update_*.swift, test_sparkle_adapter.swift, test_update_packaging.py | Launch, ownership, callback, notes and package/config fixtures |
| preview/ui-review | Synthetic update offer/download/cancel previews; no real app replacement |
| .github/workflows/preview-candidate.yml | Pinned framework admission; existing signing protection retained |

## Body Change Scope / Lossless Preservation
Integrated accepted #63 at merge 9e1fd46 and master 07691fb at fb82e25. Preserved
all reporting suites and the current public catalog/download content. No runtime,
authenticated prefix, saved game, server reports or public release were changed.
Only planned mydocs and app/build locations changed; no new official doc location.
Sparkle retains upstream code/languages and bundled MIT/BSD/Ed25519 notices;
Pear adapter code uses its existing GPL notice. JSON inventory provenance is in
THIRD_PARTY_NOTICES, because JSON cannot carry a leading comment.

## Verification Results
Executed on Apple Silicon, macOS 26.5.2, Swift 6.3.3; target macOS 15.0. Admitted
Sparkle archive SHA256:
`c2bf58aa8387266ac179357b1415d6f2635f044da8be41042af32425dae6da0c`.
Upstream framework inventory and ad-hoc signature verified. This is not an upstream
Developer ID signature. Production helpers will be re-signed with Pear's identity.

Commands run:
```sh
PEAR_PREVIEW_BUILD_ROOT="$PWD/.build/task62/app" bash preview/build.sh
python3 -B preview/ci_checks.py
python3 -B preview/package.py --app .build/task62/app/Pear.app --output .build/task62/packages-20261020
python3 -B tools/check_governance.py
python3 -B tools/check_source_notices.py --base HEAD
git diff --check
```
Results:
- Full app/CLI build and all native suites passed. Adapter used a real eight-second
  watchdog with a fake engine; no-update, Later, offline/start failure, cancellation,
  cached-install rejection, late callbacks, active/unknown session and Homebrew
  cases passed. Release-note failure did not release the choice gate prematurely.
- Environment test acquired the lock across real processes and rejected a symlink;
  restart receipt target/expiry/path scope checks passed. No signed Keychain
  handoff claim: the final adapter fixtures inject a fake restart store.
- Reporting policy/store/transport/observer/host and presentation tests passed.
  The host observer used a synthetic process, not a game.
- 73 portable tests passed, zero skips/failures. Governance: 40 documents and
  378 targets passed. Incremental source notices and whitespace checks passed.
- Package allowlist and local ad-hoc codesign verification passed. Current app
  executable SHA256 `ca04b54a6d76a43e47cc4a2f0d54cbe55319cb8289a5e6805bb0f53d1b20c574`.
- Native UI showed current/target versions and rendered scrollable sample HTML.
  Update selection, download status and cancellation returned to the synthetic
  Steam-ready screen. Screen left open for requester review. Samples are explicitly
  labeled; a GitHub release is not represented as published.
- Prior integrated catalog checks (25 compatibility, 22 catalog-site tests) remain
  valid: those files have not changed since those checks. Existing runtime/game
  qualification is reused only for unchanged runtime bytes; no gameplay repeated.
- Local logs/receipt: `.build/task62/resume-build.log`, `resume-portable.log`,
  `notices-20261020.json`, `stage2-checkpoint.json`. Source digest map retained in
  the checkpoint. No private credentials or diagnostics committed.

Timing: the earlier frozen candidate build/verification interval was 47.687 seconds,
with separate UI preparation/agent coordination and human-review timestamps in
`iteration-timing.json`. This is not end-to-end manual latency. The notes iteration
was interrupted overnight; `notes-iteration-timing.json` is incomplete. No baseline
or confirmed manual-response latency is claimed, and independent intervals are not
summed. Today's local automated UI input response was observed; human review is
separate and pending.

## Artifact Disposition
| Artifact/root | Actual state | Owner/consumer | Identity | Release condition |
|---|---|---|---|---|
| .build/task62/Sparkle-2.10.0.tar.xz, admitted | Retained immutable input | #62 builds/signing | Archive digest above; exact framework inventory | Keep through signed qualification |
| .build/task62/app and packages-20261020 | Retained disposable local candidate | #62 local verification | Checkpoint and package manifest | Replace only after newer verified candidate |
| .build/task62 logs/receipts | Retained local evidence | #62 Stage 3 | Checkpoint source/binary hashes | Final handoff and sanitized report |
| .build/task63-ui/Pear UI Review.app | Retained operable synthetic UI | Requester review | Shared source; sample-only | UI accepted and new signed candidate ready |
| Prior signed runtime/releases | Preserved | #47/#62 | Existing pins/manifests | Unchanged; no cleanup authorized here |

Filesystem available space observed at approximately 15 GiB. No before/after space
recovery claim. Logical/allocated totals were not measured this checkpoint; no full
runtime copy or new runtime download occurred.

## Residual Risks
- Real Developer ID/notarized old-to-new replacement, signed Keychain handoff,
  corrupt-signature and installation-failure recovery, real Steam reentrant launch
  and final macOS 15 execution are not performed. These remain required Stage 3.
- Feed and Ed25519 key are not enabled in the local app; unconfigured builds safely
  continue to Steam. No production update is published.
- Homebrew detection covers standard prefixes conservatively; custom layouts may
  require explicit ownership configuration. No brew process or package mutation.
- Release notes publishing must derive from the GitHub release body and bind exact
  target archive metadata. Current fixture text is not a public release note.
- Required GitHub signing approval is unchanged. Existing canceled v0.1.0 CI is not
  resumed or reclassified as passing authority.

## Impact on Next Stage
Preserve the accepted UI and immutable framework. Prepare separate signed baseline
and target candidates with increasing build numbers, the same bundle identity,
public Ed25519 key and bounded update feed. Keep private keys in Keychain and out of
CI source/client bundles. Record real replacement/relaunch/data checks separately.

## Approval / Continuation
The requester has explicitly authorized implementation and qualification in this
chat; #62 records that routine stage continuation needs no repeated approval.
Local visual review is pending. Protected GitHub signing approval and final local
candidate verification remain required before public distribution.
