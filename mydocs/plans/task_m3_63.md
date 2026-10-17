# Task #63 — Consent-based run history and reporting

GitHub Issue: [#63](https://github.com/postmelee/pear/issues/63)
Milestone: M3 — Rosetta-based Megabonk Preview

## Purpose and scope
Local history first; optional reports pass through private review before catalog
publication. All detailed behavior in Issue #63 is required, not optional scope.
Reuse the existing AppKit UI, native session identity checks, Steam App ID catalog
and reporting evidence model. No new runtime, raw log upload or Steam credentials.

## Design direction
Persist local-only / ask / selected-field-auto modes, consent schema and generation
atomically. Every queue item records origin (manual/auto), consent generation and
allowed-field snapshot. Before scheduling and immediately before network send,
revalidate consent; withdrawal increments generation, cancels queued/in-flight
auto requests and persists local-only without confirmation. Requests already
received cannot be recalled; disclose this and offer separate server deletion.
Never turn prompt suppression into auto consent. Notes are sent only by explicit
Share, never by automatic retries of an unrelated record. Retry the exact approved
payload idempotently; newer result/note uses same report ID with revision control.

Local UI: History button/menu, newest-first rows; detail includes environment,
versions, observed exit state, user result, note, payload/shared status. Show mode,
Sharing settings, Disable automatic sharing; local-only retains manual export.
Exit form result normal/problems/unknown, optional note, Share/Skip, suppress
future prompt. Optional auto-mode completion notification defaults off.

Session ownership: a per-user, per-canonical-root observer remains alive when the
window closes while owned Steam/game session exists; explicit Quit detaches safely
and records incomplete observation, never stops games. Single-instance ownership
lock and PID plus start identity prevents PID-reuse attribution. Inspect only
processes proven under Pear's exact prefix/runtime, use whitelisted Steam App ID
metadata, retain no environment dumps or username paths. A Wine child exit is not
an exit code unless actually observed; crashes/forced quit/sleep gaps remain
unknown. Reconcile interrupted observations at next launch, never fabricate end
or active-play time. App-only update waits for owned session/observer release.

Data: OS/chip/memory; Pear/Wine/DXMT; App ID and available build; local exact start/
end, share calendar date and whole process-minutes only. Distinct user result and
machine observation. No Steam IDs, auth, saves, paths or raw logs. Consent enumerates
shared fields and later public fields. Environment + result may be published only
after review; notes remain private by default and require separate explicit public
permission if public note publication is offered. No automatic Pass promotion.

Proposed retention: local history 90 days (manual export and delete available),
failed/queued transmissions 14 days then manual retry, unreviewed server reports
180 days, reviewed records 365 days before renewal/deletion review. Server deletion
by per-report owner capability also withdraws linked public record on next export;
local deletion never silently deletes shared data. Platform backup/log retention
must be disclosed separately when verified; these are design targets, not deployed
promises. Never call the service completely anonymous.

## Sites admission experiment
Use dedicated owner-private Site appgprj_6ad3ad34532081918cd648c282288d83, synthetic
records only. A service bypass token may test transport in memory but MUST NOT be
packaged in an app. Private Sites require browser identity or service bearer; public
write endpoints need per-report ownership/authentication. Verify URLSession HTTP,
D1 durable insert/read/update/delete, access denied, size/rate bounds, idempotency
and retries. Confirm publication audience can separate public ingest/private admin.
IP/access logging, backups, retention, quotas and operator access are unresolved:
platform tool/docs do not currently specify these. Do not adopt based solely on
D1 availability or successful privileged HTTP. If unsuitable, report exact failed
criteria and evaluate a supported alternative without weakening access controls.

Requester selected no additional ChatGPT login on 2026-10-18: use a public
collection API and a random capability per report. The synthetic Site audience was
changed to public only after replacing the old private-only route with capability
checks. This is not permission to accept real records before integration checks.

API candidate: client-generated report UUID plus 256-bit random owner capability;
hashed owner capability server-side, secrets in Keychain only. No
public admin key/shared client secret. Strict JSON allowlist, size ceilings,
transactional revision/idempotency checks, bounded backoff and durable offline queue.
Admin reviewer identity checked server-side; only approved projection is exported
to existing GitHub Pages data. Requests/upvotes stay GitHub. No collection before
consent, including synthetic consent-disabled endpoint counters in tests.

## Stages and acceptance
1. Sites/native transport/D1 feasibility and scoped observer design; record limits.
2. Local record/consent/queue core and app history/settings/exit UI; local review.
3. Admitted API, access control/private review/catalog projection and privacy text.
4. Integration with #62 and signed tests: consent/withdrawal/restart, duplicate and
   update reports, note privacy, offline retries, deletion, observer/window lifetime,
   other-Wine isolation and unchanged login/game/save data. #47 publishes only then.

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

## Approved local reporting rehearsal (2026-10-18)
Requester approved expanded disclosure, catalog mapping, optional supplementary
observations and a user-operable reporting rehearsal before Sparkle integration.
Use existing AppKit history/coordinator and a separate loopback-only test receiver;
never weaken production HTTPS admission. Test reports stay on this Mac. No runtime
copy, game launch, production upload or public deployment. Source in preview/reporting-review;
small private state under .build/task63-review, retained until user review.
Consent disclosure v2 adds reviewed GitHub/catalog publication; old automatic
consent cannot authorize this scope. Supplemental observations are manual-only.
Catalog mapping preserves unknowns and separates process minutes, active play and
user result; no automatic Pass or qualification. Private notes are never exported.
