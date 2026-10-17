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
