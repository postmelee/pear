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


## Playable hosted reporting candidate (2026-10-18)

This section supersedes the earlier unconnected-launcher and retention-preparation
statements. Stage 2 remains in progress until the requester's real game/report
checks and final integration qualification; no public app release is claimed.

The native launcher now connects its durable coordinator to the admitted Workers
HTTPS origin. It wires manual/ask/automatic sends, two-second queue servicing,
immediate automatic-withdrawal cancellation, report-scoped Keychain ownership,
optional notifications (default off), manual supplements and separate server/local
deletion. Server deletion first stops queued sends, persists retry state and blocks
resending that record; confirmation removes the local shared-content receipt.
Local retention is 90 days except queued runs. No report/admin shared secret is
embedded. First launch shows disclosure v2 with fields unchecked and local-only.

Game identity reads only appid/name/buildid from its installation manifest. Chip
name comes from sysctl. Actual macOS fixture execution exposed /var versus
/private/var aliases in process paths; canonical realpath comparison now preserves
exact runtime/prefix isolation across those aliases. The fixture tests a natural
process exit and another-root exclusion without running Wine or a game. It is
included in the macOS build checks. Actual owned Steam observation found 15
processes and zero game processes; that does not yet establish game observation.

Verification: the five Swift suites (policy, durable store, URLSession transport,
pure observer, live Darwin process fixture) passed. New cases cover server-deletion
state/restart/resend prevention, local retention, manifest identity, native DELETE
receipts and exact process path aliases. Incremental source notices, shell syntax
and git diff whitespace checks passed. The production Worker and daily Pages path
reuse the hosted evidence in task_m3_63_cloudflare.md; no new synthetic report was
published. The new app's actual user-game reporting remains a manual check.

Local candidate: .build/task63-live/Pear Reporting.app, ad hoc development signing,
not Developer ID/notarization. Reuses /Applications/Pear.app's existing signed CLI
and installed runtime; no runtime build, copy or authenticated prefix duplication.
CLI SHA256: 9585e2bc13fa67caf604b6b9e741cd784ed4d3ddb2730948162fcb3d1f4e8631.
Launcher SHA256: 8a32d2821c2bb53519756237fed23294c317936874ad35feb46ab7f141446841.
Candidate metadata: org.pear.reporting-test, 0.1.0-reporting-test; observations
identify this app version separately from the reused preview.3 CLI. The user
confirmed old game/Steam/Pear termination before opening the candidate. First
sharing sheet AX and screenshot inspection show the disclosed public/private
boundary, no fields selected, notifications off. Persisted state confirms
localOnly, zero queued requests, zero shared records and zero runs. No real report
has been sent by the agent. The candidate is open for the requester to operate.

Timing (UTC, monotonic in seconds): source freeze 2026-10-17T23:51:03.444168 /
30749.033903166; build ready 23:51:10.512081 / 30756.101783291 (7.068 s);
launch request 23:51:28.946158 / 30774.535907416; UI inspection recorded
2026-10-18T00:02:50.974683 / 31456.561814333. Continuous freeze-to-inspection
707.528 s includes a 580.522 s UI-tool response delay. This is not a measured
source-to-confirmed-human-input endpoint: manual response remains pending.
No resource-slot coordination or additional runtime preparation was needed.
Owned .build/task63-live uses 10,432 KiB allocated; retained for requester testing,
not a reclaimed-space claim. User scenarios belong in the already approved
product guide docs/reporting-and-privacy.md. No other checkout was edited.


## Real-game identification failure and repair (2026-10-18)

The requester selected automatic sharing, played and exited, but no local run was
created. Durable consent was automatic with all four fields selected; queue and
shared receipts were empty. This was an observation defect, not a network failure.
The previous native fixture supplied SteamAppId, whereas the actual Wine children
for Megabonk exposed no SteamAppId in macOS KERN_PROCARGS2. This invalidates the
previous fixture's applicability to actual Steam-launched game identification.
No earlier play duration/result was reconstructed or fabricated.

While the requester left Megabonk at its menu, sanitized live inspection established
that argv[0] was its Windows executable path. Reused the existing installation
manifest reader and exact runtime/prefix/PID-start ownership checks. A bounded
primary-library manifest index maps only argv[0] to one owned installation, never
an arbitrary later argument. Known Unity crash/Steam/overlay helper images are
excluded; conflicting IDs, ambiguous installations, missing/relative images,
symlink escapes and other prefixes remain unidentified. No raw argv/environment,
Steam account data or logs were persisted as reports. Additional Steam libraries
without a proven mapping remain outside the fallback's scope.

The pure observer suite passed new no-SteamAppId, helper, wrong-prefix, conflicting
ID, argument-reference, ambiguous-directory and escaping-symlink controls. The
actual Darwin fixture now also uses posix_spawn with a Windows PE argv[0] and no
native SteamAppId, and passes start and natural-exit observation. Full app build,
source notices and whitespace checks passed. The prior consent/store/transport
checks apply unchanged; no runtime rebuild or long gameplay test was repeated.

Live read-only probe changed from 18 owned processes / zero game processes to 18 /
one game process. The old Pear alone was quit through its normal Quit action;
Steam and Megabonk stayed running. New candidate
.build/task63-game-id/Pear Reporting.app (0.1.0-reporting-test.2) created the
Megabonk record with App ID 3405340 and build 21750826. Requester then confirmed
normal game exit. App persisted observedExit=exited, acknowledged one automatic
report with zero pending requests, and displayed Shared. Actual authenticated
administrator UI showed the same UUID/revision 1 in Needs review, with userResult
unknown, processMinutes 4 and no private note. This was menu/diagnostic observation,
not evidence of four minutes of active play. No approval/public publication was
performed. Direct Wrangler D1 verification returned API authorization error 7403;
the independent verification used normal GitHub OAuth administrator UI instead.
The expired admin session was renewed through the existing authorized login flow.

Launcher SHA256 ff16ba792622f8a6899cd4d50db0bcc5ea5ef63d5ed1bbbce96e71bbf2c82b54.
Unchanged installed CLI/runtime inputs match the previous checkpoint. Source freeze
UTC 2026-10-18T14:34:56.101542+00:00 / monotonic 79683.644485375; local build
8.643 s; launch requested 2026-10-18T14:36:28.515097+00:00 /
79776.058042916. UI button interaction and record rendering were
verified; requester exit/send/admin checks recorded at
2026-10-18T14:47:14.033358+00:00 / 80421.657510666.
The game was already open, so this is not a new-game source-to-manual-input timing.
Exact handoff/response arrival boundaries were not captured; no summed timing is
presented as that endpoint. Final signed release and manual/ask-mode game checks
remain distinct gates. Candidate and small fixtures are retained for those checks.


## Player-facing native presentation checkpoint (2026-10-19)

Requester confirmed manual reporting and ask-after-each-game reporting passed
before this UI revision. Combined with the recorded automatic-mode receipt/admin
verification, all three reporting modes have requester-facing rehearsal evidence.
This does not complete Sparkle integration, final signing or v0.1.0 publication.
Issue #63 had been closed by PR65; reopened for this remaining authorized app work.

Reused native AppKit and Pear's published tokens (master efd9ed7,
https://postmelee.github.io/pear/tokens.css, checked 2026-10-19). Added semantic
cream/charcoal/olive colors with dynamic appearance, native fonts, semantic result
badges and consistent spacing. Main window now uses Auto Layout; setup/launch and
Cancel occupy their own action row, separated from history/About. No process,
launch, observer, transport or runtime ownership behavior changed.

History now begins with the compact list and opens a separate detail page on row
activation. Result and note are primary; environment/version/exit, supplementary
tests, export, sent content and local/server deletion remain under More. Automatic
withdrawal is visible in automatic mode and still applies immediately. Existing
shared records use Update shared result, and retry appears when queued. Navigation
saves the local draft only; it does not enqueue a report. The exit sheet explicitly
names the game and retains an existing note/result. Sharing disclosure is grouped
by purpose/publication, sharing mode, selected fields and after-game preferences;
privacy, retention and deletion boundaries remain visible before consent.

Verification: existing Swift policy, durable-store and presentation suites passed.
Full native launcher build and ad hoc deep/strict signature validation passed;
source-notice check (six original source/build files), shell syntax and whitespace
checks passed. A separate UI-only harness reuses actual presentation, has no
transport or CLI resource, and never runs Steam. Native UI interactions confirmed
list/detail/back, local draft persistence across another run, disabled sent-content
menu for an unsent record, setup table, separated Cancel, named-game exit prompt,
light/dark appearance and the final grouped consent sheet. No real report or
sharing setting was changed, and no game/runtime test was repeated.

Artifacts retained for requester review:
- .build/task63-ui/Pear UI Review.app: synthetic UI only, reproducible with
  `bash preview/ui-review/build.sh`; Preview screens menu switches states/themes.
- .build/task63-ui-candidate/Pear Reporting.app: full app compile against the same
  verified installed CLI, not launched; ad hoc local build, not notarized delivery.
- Final UI executable SHA256: fbccf6da09952bff5f975d10e85e4d7274c6bd626f89fdbc0af9053fbf8dd4e9.
- Full candidate executable SHA256: 81c8aa536113f3756492d144dcca7d21bdcfc58c0aceea4739d8cec93812b5c6.

UI source freeze UTC 2026-10-18T15:26:51.548504+00:00 / monotonic
82799.195151166; ready UTC 15:27:01.995382 / monotonic 82809.642160833,
build 10.447 s. Full candidate build 9.834 s, ready UTC 15:27:11.857974.
Final automated UI confirmation: 2026-10-18T15:34:51.246025+00:00 /
monotonic 83278.897525. An earlier review-app
launch was blocked by the Mac lock; requester confirmed unlocking. Exact human
waiting boundaries and preparation/admission baseline were not captured. These
build durations and automated UI observations are not a confirmed human-input
end-to-end endpoint. User design review remains pending.

Combined logical artifact size at checkpoint: 12,400,818 bytes; allocated size
was 5,748 KiB UI plus 6,404 KiB full candidate before this small timing update.
Filesystem available was about 11 GiB; no reclaimed-space claim. No runtime or
prefix copies. Preserve these small candidates through UI review and discard
superseded output on the next admitted handoff.

### UI follow-up, pending visual confirmation (2026-10-19)
Applied the requester-approved spacing, Game name hierarchy, upper-right About
Pear control, native About menu and compact titlebar branding. Sharing disclosure
now belongs to the same content-sized stack as its controls; all disclosure text
and consent behavior are retained. The isolated app compiled successfully and
incremental notices and whitespace checks passed. During old-harness dismissal
the Mac locked; final new-binary visual inspection and user handoff are pending.
No Steam, runtime, production data or network reporting was exercised. Retain the
small existing UI output until the requester reviews it. Detailed timing boundaries
were not captured for this iteration; no end-to-end input-response claim is made.

Final UI follow-up verification: after requester unlock, the rebuilt harness
visibly shows the corrected introduction-to-Game name spacing and body-sized
Megabonk value. Earlier native interaction confirmed the upper-right About action
opens its sheet, compact titlebar branding and reduced sharing-settings gap.
The final game-exit sheet is left open for requester review. This is synthetic
UI validation only; no production report was transmitted. Build, source-notice
and whitespace checks passed. Human design acceptance remains pending.

### Menu and input refinement verification (2026-10-19)
Main content now has only setup/status and bottom-aligned primary/cancel actions.
About and history remain in the app menu, with Sharing settings (Command-comma)
opening the existing consent sheet directly. History has an explicit Sharing mode
caption. Exit-form captions are muted, game value stronger; shared text editors
use native text/background/caret colors and a bezel instead of the brand surface.
The isolated build passed after fixing a harness-only local-name collision. Native
inspection confirmed bottom actions, direct settings shortcut, and light/dark
input boundaries and text entry. Synthetic note persisted after Skip and reopening.
No real report was sent. Source notices and whitespace checks passed. Exact phase
timestamps were not captured; no latency measurement is claimed. Retain the small
UI harness output for requester review; unchanged runtime was not rebuilt.


### Unified settings and first-run review (2026-10-19)
The main window is now 600 by 340 points, with a closer title/description group
and separate setup/progress content. About remains in the Pear menu; Settings
(Command-comma) opens a dedicated window with a Sharing sidebar section. Run
history remains a separate Window menu action (Command-Shift-H). The titlebar
uses the existing transparent docs/assets/pear.png unchanged as PearMark.png;
the Dock icon is unchanged. Asset SHA256:
ea213ca4c626f12a60289d768e7a35b59e32290d7c68f9b929907f1b98d2ac8b.

The first-run draft selects Automatic sharing and all four field groups as
requested, but persisted consent remains localOnly with no fields until explicit
confirmation. The affirmative action names the selected behavior and has no
Return-key default. Continue without sharing or closing the welcome leaves
sharing disabled. A durable introductionSeen flag prevents repeated unsolicited
welcome windows. Existing consent is preserved. Legacy ask-mode configurations
with questions disabled migrate to manual sharing, preserving their silent choice.
Ask mode now always asks; the exit-form opt-out explicitly switches future games
to manual sharing. Automatic-mode reminders are optional and off by default, with
copy explaining that they invite a result or note and never automatically send notes.
History groups the current sharing mode, behavior explanation and Change action;
automatic sharing can be turned off immediately without confirmation.

Verification: policy and store/coordinator Swift test executables passed, including
welcome dismissal persistence, no automatic enqueue before consent, legacy
migration, withdrawal, note privacy and existing retry/idempotency coverage. The
isolated native UI build, incremental source notices, shell syntax, whitespace
and ad hoc signature checks passed. Native interactions verified settings mode
changes, auto-only reminder visibility, immediate manual switching, compact main
layout, transparent titlebar image and the first-run preselection. Synthetic
fixture inspection before confirmation showed localOnly, empty fields, no
pending reports and introductionSeen=true; after explicit confirmation it showed
automatic, the four selected groups and reminders off. No production preference,
Steam state, runtime, save or report was modified by these UI checks.

These are local synthetic UI and policy checks, not signed distribution or final
user acceptance. The small .build/task63-ui output is retained for requester
review and may be replaced by the next admitted UI build. No runtime copy or
runtime rebuild was needed. Phase timestamps were not captured continuously for
this iteration, so no end-to-end latency or reclaimed-storage claim is made.


### History footer and disclosure grouping (2026-10-19)
Moved the automatic-only optional reminder below the sharing mode and its short
explanation. Added public-use and storage/deletion headings without removing
privacy or publication disclosure. History now leads with the record list; a
separator divides the fixed bottom mode/explanation/settings/off area. Shared
report management is available in the top More menu. Removed Open selected run;
rows open on click or keyboard Return, with a chevron beside the game name.

The native UI harness compiled and passed ad hoc signature, incremental source
notice and whitespace checks. Native interaction verified click and Return detail
navigation, More > Shared reports presence, bottom Sharing settings opening the
separate settings window, ask-mode reminder hiding and automatic-mode reminder
placement. Final light-mode rendering confirms visible chevrons and separated
footer. Only synthetic fixture data was used; no production report, consent,
game, Steam session or runtime was changed. Policy/transport sources are unchanged;
the prior checkpoint's policy/store evidence retains its exact scope.

Final source frozen at 2026-10-18T17:45:58.728750+00:00 / monotonic
90967.074706041; build and ad hoc signing completed at
2026-10-18T17:46:08.459590+00:00 / monotonic 90976.805799333
(9.731 seconds combined; signing not separately timed). Automated settings
input response/render verification finished by 2026-10-18T17:50:23.861752+00:00
/ monotonic 91232.217380916. The continuous interval
includes tool coordination and UI relaunch; preparation/admission were not
separately timed. Requester input response/acceptance remains pending, so this is
not a confirmed human handoff latency. Retain the existing small UI harness for
review under the approved <50 MiB budget; no runtime copy or storage-recovery claim.


## UI acceptance and pre-Sparkle audit (2026-10-19)
Requester explicitly accepted the 1411152 UI and requested overall review before
Sparkle implementation. This supersedes prior pending visual-acceptance notes;
freeze the accepted presentation unless a functional/accessibility defect requires
repair. This checkpoint is not final signed release qualification or Issue closure.

Review found that prepareHistory opened/migrated the reporting store before
acquiring its observer lock. A second instance could therefore migrate persisted
preferences before failing ownership admission. Acquire the existing per-root lock
first; its initializer now safely creates a fresh canonical history directory and
rejects symlink aliases. Added fresh-directory competing-owner/release/reopen and
symlink controls. Existing single-owner, PID identity and exact-prefix boundaries
remain unchanged. No global process termination or live user data access occurred.

Verification on the admitted app sources:
- Six Swift suites passed: reporting policy, durable store/coordinator, URLSession
  transport, pure observer, actual Darwin synthetic-process observer and presentation.
- Full native launcher (including the actual @main entry) compiled for macOS 15.
- Worker: 7 tests passed, including OAuth identity/state, private routes, ownership,
  idempotency, public projection, publication acknowledgement and deletion/replay.
- Local review-server synthetic report round trip: 1 test passed.
- Catalog: 25 tests passed; compatibility --check validated 2 reviewed records.
- Incremental source notices and git diff --check passed.
- Existing #62 UpdateLaunchPolicy and tests from cad0580 were extracted unchanged
  into the audit output and passed. No Sparkle framework was embedded or exercised.

Commands: swiftc -target arm64-apple-macosx15.0 with each suite's declared Swift
sources; node --test preview/reporting-worker/test.mjs; python3 -B -m unittest
discover -s preview/reporting-review -p test_server.py; python3 -B -m unittest
discover -s tests/docs -p test_compatibility.py; python3 -B tools/compatibility.py
--check. Node was not on PATH; the configured bundled Node executable was used.
Swift per-suite compilation/execution seconds are retained in the audit receipt:
- policy: build 1.128; execution 1.361.
- store: build 0.786; execution 0.715.
- transport: build 0.964; execution 0.822.
- observer: build 0.876; execution 0.709.
- observer-host: build 0.818; execution 9.831.
- presentation: build 0.397; execution 0.890.

Read-only hosted checks: PEAR_REPORTS_ENABLED and PEAR_PAGES_ENABLED are true;
latest observed catalog deployment 39151950523 succeeded at master
07691fbda993998a920db59a707a6d2353665d50. The five newer master commits concern
catalog clean URLs and media layout (PR66/67), not native reporting. Preserve them
when integrating #62/#63; the local 25-test catalog result applies to this branch,
not the newer master bytes. No new real report or approval was sent in this audit.
Earlier automatic/manual/ask game reports remain valid within their recorded
input scope; no unchanged-runtime long-duration game test was repeated.

Artifact disposition: .build/task63-audit contains 3827130 logical bytes and
3756 KiB allocated at this checkpoint, retained for #62 integration review;
remove its reproducible executables after handoff, keeping sanitized evidence in
this report. Existing exact CLI/runtime and signed candidates are preserved.
No runtime or authenticated-prefix copies; no filesystem-reclaimed-space claim.
This audit did not launch a new interactive production app, so it makes no new
source-to-human-input timing claim. UI acceptance refers to the reviewed candidate.

Next boundary: #62 Stage 2 may begin using this accepted UI and the existing
cad0580 policy. Final app integration must still validate actual signed old-to-new
Sparkle update, cancellation/offline/timeout/corruption/recovery, owned-session
installation deferral, app relaunch/Steam de-duplication, and data preservation.
#47 retains final signing/notarization, Homebrew, release/docs/download/catalog
alignment. Do not publish v0.1.0 or close #63 on this audit alone.
