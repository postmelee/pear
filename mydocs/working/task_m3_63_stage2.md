# Task #63 Stage 2 — Local history, observer and delivery preparation

Status: in progress; not production admission or release qualification.
Date: 2026-10-18 (Asia/Seoul).

## Scope and preservation
Reused AppKit, Foundation URLSession and Security Keychain APIs. No additional
framework or runtime copy. Work stays on codex/task63; #62 owns Sparkle and #47
owns final release integration. Reviewed Issue #63 and active worktrees; no other
chat was started. Existing Wine/Steam/game/save data and signed artifacts were
not modified. Source-only v0.1.0 release promotion remains on hold.

## Implemented
- History list, semantic result/sharing badges, selected run details, editable
  result/note, projected JSON export, sharing settings and game-exit prompt.
  Requester corrections remove checkbox bullet dots, split privacy prose and
  introduce a Run details heading. Notes require explicit manual sharing.
- Read-only exact runtime/prefix process ownership, PID/start identity checks,
  single observer lock, window-close observer lifetime and uncertain-duration
  handling after missed samples/sleep. No process termination in this observer.
- Durable queue retry metadata: exponential delays from five seconds to one hour,
  automatic retry cutoff at 14 days, explicit immutable-payload retry, unrelated
  report progress while retaining per-report ordering. Withdrawal cancels active
  automatic transmission and removes its pending payloads. Local deletion cancels
  its active request, removes the local run/queue, and retains shared receipts;
  the UI explicitly says it does not delete the server report.
- URLSession adapter: HTTPS endpoint admission, no redirect following, no cookies,
  credential cache or response cache, 15/20-second request/resource limits,
  16 KiB response bound and exact report/request/revision receipt matching.
  Report capabilities are generated separately with Security random bytes and
  stored device-locally in Keychain, scoped to the full collection endpoint.
  No common/admin key, capability output or source-embedded secret.

## Verification performed
Swift target arm64-apple-macosx15.0 on this development Mac:
- Reporting policy tests passed: default silence, field projection, private notes,
  prompt suppression, stable report identity and persisted consent decoding.
- Store tests passed: restart, withdrawal/in-flight cancellation, late callbacks,
  immutable retry, disk failure, corrupt-file preservation, durable retry delay,
  14-day retry cutoff, independent-report progress and deletion cancellation.
- Observer synthetic tests passed: exact ownership, helper exclusion, PID reuse,
  missed observation, sleep gap and single-owner lock.
- URLSession tests passed with an injected URLProtocol: request creation,
  HTTPS-only admission, receipt mismatch/malformed response rejection, 429/302
  rejection, oversized response rejection and cancellation reaching URLProtocol.
  This is an actual native URLSession task with synthetic transport, not an
  external-network/production-server test. The redirect delegate is implemented;
  a real server redirect and Keychain persistence in the signed app remain checks.
- Complete launcher source compilation passed, including the adapter. Incremental
  source notice checks and git diff whitespace checks passed.

The separate local history review app uses synthetic records only, no Steam/game
launch and no transport. The requester reviewed typography/spacing before this
follow-up. Current local review includes retry and local-delete controls. The
actual collection adapter is deliberately not configured in the launcher yet;
Share remains disabled. Do not present this as end-to-end reporting completion.

## Remaining work and protocol decision
Production server validation, request limits, reviewer identity, retention/deletion,
reviewed catalog export, actual session identification, metadata, optional
notifications, automatic enqueue/timer wiring and full signed app integration are
still open. Storage/IP/access-log/backup limits at Sites remain unverified. No
anonymity claim or real player upload is authorized by this experiment alone.

The production server must accept increasing (not necessarily contiguous) client
revisions and recognize identical request retries: cancellation can skip local
revision numbers. Reject stale revisions and keep deletion tombstones so old
queued requests cannot resurrect deleted reports. The current native receipt
requires matching report ID, request ID and revision. This protocol still needs
server-side atomic race and deletion tests; the earlier fixed probe is not it.

Local 90-day/server 180/365-day retention remain design targets, not implemented
claims. Shared receipts retain local copies of sent contents after local run
removal; server-management UI must keep those discoverable and support separate
server deletion. Automatic retry cutoff retains the approved payload for manual
retry; no periodic network scheduling is enabled in the current app.

## Artifacts and timing
Owned small outputs: .build/reporting-{policy,store,transport}-tests,
.build/run-observer-tests, .build/pear-history-launcher and
.build/history-ui-review. Retain for #63 integration/UI review; replace/discard
only after that consumer completes. Tests remove their own temporary synthetic
store. No material runtime/signing/CI build or private-state copy. df -h reported
15 GiB free on /System/Volumes/Data; not a cleanup/reclaimed-space measurement.
No continuous source-to-confirmed-manual-input timing was captured for this
iteration. Compilation and synthetic checks do not establish that endpoint.

## Local end-to-end rehearsal follow-up
The requester approved a local report-flow review before Sparkle/Steam integration.
Added disclosure v2 explaining improvement purpose, private review and possible
GitHub/catalog publication, optional sharing, excluded data and external copies.
Legacy queued requests lacking the disclosure version cannot transmit; legacy
automatic consent cannot enqueue. The local review app shows disclosure on first
launch; production-launch onboarding wiring is still an integration task.

Optional furthest result, active-play minutes, input/audio/save/recovery checks and
settings remain unknown unless supplied. These supplements are manual-only; notes
remain separately opt-in and never enter the public projection. Missing App ID
prevents catalog approval. Store links derive only from a supplied App ID.

A separately compiled AppKit rehearsal uses the real store, coordinator, history
UI and URLSession over a fixed loopback test endpoint. Production HTTPS admission
is unchanged; the rehearsal transport is never compiled into the shipped app.
The loopback Python receiver uses SQLite, per-report capability hashes, bounded
input, idempotent revisions and same-origin/CSRF-protected local review forms.
It is not production authentication or Sites admission. Data never leaves this
Mac. Existing Steam, games, saves and runtime files were not touched.

Verification: policy/store tests pass, including legacy consent/queued request
blocking and manual-only supplementary fields. Native URLSession sent a synthetic
report to the actual local HTTP receiver, matched its receipt and persisted shared
state. Receiver test covers duplicate retry, ownership rejection, approval without
publication, batch publication without notes and revision update requiring review
while retaining the previous public version. Full launcher compilation and existing
transport suite are checked separately. UI accessibility inspection confirmed the
initial disclosure, all field checkboxes off and local-only default. User interaction
confirmation is pending; no continuous source-to-confirmed-input timing is claimed.

Local review: http://127.0.0.1:8964/ and /catalog. Test app and private local state
are in .build/task63-review. One synthetic fixture uses this host's OS/memory but
does not represent an actual game session; no actual play claim is made. The local
catalog reproduces report fields/cards; the existing Pages generator and hosted
Sites workflow are not yet integrated with this new supplemental schema. The
Apply button simulates the daily batch; no scheduled publication was enabled.
Retain small test artifacts until requester review; no runtime copy or release.

Requester UI follow-up: local private review now uses compact game/date/process
time/result/review-state rows. Native details/summary disclosure opens report
fields, private notes and approval controls on demand, one report at a time.
Stored reports and approval/publication behavior are unchanged.

Requester approved status tabs: Needs review (default), Queued and Published,
with counts and a compact queued summary. Approval preserves the current tab;
Queued exposes revision-checked cancellation and the local batch action. Existing
published snapshots survive cancellation of a newer revision. Receiver tests
exercise queue cancellation and reapproval before publication.
