# Task #62 — Sparkle app updates

GitHub Issue: [#62](https://github.com/postmelee/pear/issues/62)
Milestone: M3 — Rosetta-based Megabonk Preview

## Purpose and scope
Add an app-only updater that never indefinitely blocks opening Steam. Keep the
signed Wine/DXMT installation path unchanged. This follows explicit user approval
and depends on the #63 session-ownership contract for safe installation.

## Design direction and reuse
Use pinned upstream Sparkle 2, retain its signatures, install/relaunch engine and
license; no custom installer. Adapt SPUUserDriver for Update and launch / Later.
Update check deadline initially 8 seconds, no background automatic installation;
late results cannot interrupt Steam after the launch gate completes. Failures,
no-update, decline and timeout pass through a single launch-once gate. Download
and installation are separately cancellable; install failures retain usable app.
Disable SUEnableSystemProfiling and SUSendProfileInfo, return empty profile keys;
no hardware/report payload in update requests. HTTPS/static appcast still has
ordinary server request metadata; do not claim no network metadata.

One app instance coordinates launch/update/session state. Recheck owned Steam/game
activity immediately before install and before replacing the app; active sessions
postpone install. A signed one-use relaunch intent plus running-session check must
avoid duplicate Steam launch and update loops. No process-wide kill commands.

Homebrew proposal: recognize managed app symlink/Caskroom receipt conservatively,
disable in-app replacement for managed installs and show brew upgrade guidance;
normal Steam launch continues. Unknown ownership must not silently overwrite a
package-manager installation. Do not mutate a signed bundle to store ownership.

Legacy preview.4 lacks Sparkle: document one-time manual installation. Actual
Sparkle update verification needs a signed updater-enabled older candidate and a
newer signed candidate, same bundle ID, monotonic build versions and separate
Ed25519 signing key retained outside repo. Never claim legacy automatic update.

## Stages and acceptance
1. Upstream/API/provenance review and launch/update state-machine tests.
2. Sparkle integration, status UI, session deferral and Homebrew policy; local UI.
3. Signed old-to-new update, offline/decline/timeout/failure and data preservation;
   hand off exact passing artifact to #47, after #63 integration.

## Required evidence
No-update, choice, delayed callback, download cancel/failure, corrupt signature,
active process, reentrant relaunch, downgrade rejection, user authorization needed
and Homebrew path scenarios. Final macOS15 checks and local application startup.
Source references: https://sparkle-project.org/documentation/custom-user-interfaces/
and https://sparkle-project.org/documentation/api-reference/Protocols/SPUUpdaterDelegate.html
Reviewed 2026-10-18; framework revision must be pinned before integration.

## Authority, workflow and locations
The requester explicitly authorized implementation, verification and final release
in the same message; routine implementation/stage steps within that scope do not
need renewed permission. UI/public website require local review before deployment.
Use existing M3 identity; this does not establish M1. Root AGENTS, docs/AGENTS,
architecture/delivery-plan and task-register/task-start procedures apply. #47 is
release integration only. No other chats or agents are started.

Plans, implementation notes and reports: mydocs/plans, mydocs/working, mydocs/report.
App code: preview. Official user docs: docs/rosetta-preview.md and a new
`docs/reporting-and-privacy.md` for consent/retention, linked in docs/README.md;
update release operations in docs/development/preview-release.md. This is official
product guidance, not mydocs/manual material. Catalog stays tools/catalog and
compatibility.py. Keep historical result records and source identities unchanged.

## Artifact lifecycle
Reuse exact preview.4 signed runtime and 6afc8f2 app/CLI baseline, not its cancelled
release authority. No authenticated-prefix copies without a specific recovery
need. Local free space was 17 GiB; budget <=2 GiB Sites/tooling, <=1 GiB app/test
builds and small synthetic state. Hosted signing retains bounded outputs for 14
days. No runtime rebuild/copy. Preserve private data and recovery evidence. Keep
small sanitized receipts, release hashes and pinned upstream inputs; delete owned
synthetic state after verification and retain exact update pair until handoff.
Sites uses synthetic records only until server access/privacy gates pass.

## Verification and risks
Record actual input hashes/versions and wall/monotonic boundaries for candidate,
build, runtime preparation and user input; report missing baseline explicitly.
Never infer playtime or qualified support from process duration. Public review and
signing approval remain gates. Feature changes require affected app validation;
unchanged runtime long-duration tests are reused within original scope.


## Stage 2 readiness after accepted reporting UI (2026-10-19)
The requester accepted #63 UI at 1411152 and its pre-Sparkle audit. Preserve its
main-window layout, Settings > Sharing, independent Window > Run history and
explicit sharing consent. Source/UI audit and the lock-before-store fix are on
codex/task63; Stage 1 policy remains on codex/task62 at cad0580. Reuse both; do not
recreate Stage 1 or overwrite #63 with the older Launcher/build script.

Integration order:
1. Inspect clean worktree/branch status, then integrate the accepted #63 checkpoint
   into codex/task62, resolving build.sh by preserving all reporting tests and adding
   the existing update policy test. Preserve newer master catalog PR66/67 changes
   (latest observed 07691fb); revalidate their affected catalog bytes after merge.
2. Admit Sparkle 2.10.0 official release archive, validate its digest and bundled
   licenses/framework identity, retain upstream installation and signature engine.
   Official archive metadata checked: Sparkle-2.10.0.tar.xz, 16,319,840 bytes,
   SHA256 c2bf58aa8387266ac179357b1415d6f2635f044da8be41042af32425dae6da0c.
   This metadata is not a completed download, signature or license admission.
3. Implement the MainActor adapter/driver and bounded check watchdog. Launch
   inspection and sharing introduction must not let updater prompts overlap or
   implicitly grant data consent. Cancel/ignore late update callbacks after release.
4. Treat incomplete owned-process snapshots as unknown, defer replacement, and
   recheck immediately at install boundaries. Separate observer ownership from
   Steam launch: a running observer must receive an open/activate request rather
   than a second steam command. Existing history admission failures currently
   block showSetup; handle lock contention and unavailable history deliberately
   during the launch coordinator integration, never silently create another owner.
5. Implement conservative Homebrew ownership and one-use restart intent, preserved
   outside the signed bundle. Validate across a new process; the Stage 1 in-memory
   launch gate alone is not cross-process de-duplication or authenticated relaunch.
6. Embed/sign the framework and helpers in the right order; use distinct increasing
   build numbers for the signed older/newer test pair. Preserve org.pear.rosetta-preview
   and the existing data root/Keychain scope. Disable profiling and automatic
   background installation, keep reporting consent separate, and show local UI.
7. Run the required real signed update/recovery/session/data-preservation checks,
   then hand the exact passing revision to #47 for release integration.

Rechecked official custom UI/SPUUpdaterDelegate docs on 2026-10-19: custom drivers
must handle permission, authorization and different update states; delegate checks
can suppress updates during setup and restrict profile keys. Sources remain the
URLs above. Actual framework pin admission, update keys/appcast, adapter, Homebrew
ownership, signed pair and macOS 15 final execution are still outstanding; do not
represent the passed policy test as Sparkle integration. No new user permission is
needed to begin the previously authorized implementation; existing GitHub protected
signing approval is retained when CI reaches that gate. No other chat is involved.

## Accepted update-screen direction — 2026-10-19
The requester asked for explicit current and target versions with a release-notes
web view below. Keep Update and launch / Later fixed below the scrollable notes.
Reuse Sparkle's appcast description/release-notes callbacks and WebKit rather
than embed the authenticated GitHub page or build another download service.
The publishing step must derive the appcast notes from the same GitHub release
body. Inline HTML/plain text and HTTPS notes under the Pear Pages updates path
are admitted. Nonpersistent WebKit disables scripts and resource requests;
external navigation is restricted to explicit Pear GitHub release links.
Bound notes to 256 KiB and show an independent eight-second fallback. Missing
notes do not reject a valid app update or hold the Steam launch gate.
UI fixtures are marked sample content and do not represent a published release.
No official document location changes are needed for this presentation change.

## Stage 3 candidate preparation — 2026-10-20
Use a dedicated Pear Ed25519 account in login Keychain, with only its public key
tracked in preview/update-public.json (JSON notice exception: public configuration,
not source code; no secret or capability). Keep private key material off CI and Git.
Both qualification apps use an explicitly selected qualification feed, separated
from the eventual stable Pages feed. Enable Sparkle signed-feed validation as well
as pre-extraction archive validation. Same marketing versions show build numbers
in the offer, so the baseline and target remain distinguishable.

The protected signing run signs/notarizes the target, then derives the baseline
from that exact app while retaining verified nested signatures. Only the baseline's
Info.plist build number and outer app signature change; separately notarize and
staple that app. Record hashes, source, configuration and increasing build numbers.
This tests actual Sparkle replacement between two notarized applications; it is not
a claim that legacy preview.4 has an updater. Keep the baseline outside homepage
and Homebrew downloads. Prepare the feed with upstream generate_appcast and the
same release Markdown, and retain both exact archives through final qualification.

Build/publishing helpers remain in preview; protected CI remains in the existing
preview-candidate workflow. No credential export, signing-gate bypass or runtime
rebuild. Public stable release and final docs remain behind the original checks.

### Update-notes spacing refinement — 2026-10-20
The requester asked to use the empty area above the footer buttons. In the update
offer only, hide the launcher status row and flexible action spacer, and let the
notes view consume the available vertical space with a minimum readable height.
Keep the existing footer inset and 16-point separation from the notes. Other
launcher states retain their spacer and progress row. Verify scrolling and the
offer/download/continue transitions in the isolated UI app before signed builds.

The requester accepted the final expanded-notes layout and explicitly continued
signed qualification on 2026-10-20. Run the workflow with qualification_pair=true;
skip the redundant push-triggered run using the preparation commit's skip-ci
marker. The manual run retains all portable, native, macOS 15 and protected
signing checks. No check or signing approval is removed.
