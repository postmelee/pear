# Report sharing and privacy

Pear 0.1.0 includes local run history and optional reporting. Sharing is not
required to use Pear. No report is transmitted until you confirm a sharing
choice; app-update approval does not enable sharing.

Reports sent with consent enter a private review queue. The administrator signs in
with GitHub; only the configured administrator's numeric account ID is admitted.
Approval queues a public projection for the next catalog deployment. Publication
approval does not certify compatibility or infer active play time from process time.

## What is public

Only selected report fields are eligible: game App ID/build, environment and runtime
versions, date, process minutes, observed exit, user result and optional test details.
Exact timestamps, Steam credentials, saves, account details, user paths and raw logs
are not report fields. Notes remain private and are excluded from catalog exports.
Do not put personal information in optional public test settings.

## GitHub and the daily catalog

The daily Pages job runs at 09:17 Asia/Seoul; GitHub may delay scheduled jobs. It
imports source links from `Show and tell` discussions and Issues labelled
`pear-report`. Imports contain titles, URLs, source IDs and update dates, not authors
or discussion bodies. Administrators can link these sources to an existing report.
Newer source metadata returns the link to review; it does not overwrite app data,
create a new GitHub post or automatically approve a report. Requests and votes stay
on GitHub. Linking is a review aid, not bidirectional content synchronization.

Only approved fields enter an immutable deployment snapshot. The service marks a
batch published after successful Pages deployment. Failed deployments can retry the
same snapshot. Public pages and JSON may be copied by third parties.

## Storage, deletion and network handling

D1 stores unreviewed reports for up to 180 days since their latest update, and
published reports for up to 365 days. Daily maintenance applies expiration. Export
snapshots are retained for seven days. Deletion redacts report contents; an ID and
hashed ownership capability remain to prevent an offline retry recreating it.
Public removal takes effect on the next successful catalog deployment; existing
snapshots/backups and external copies are not instantly erased. GitHub originals
must be removed separately on GitHub.

Ownership capabilities authorize changes to an individual report. Administrator
credentials and CI import/export credentials are never embedded in the app. The
service disables Worker application logs and traces. It uses salted, minute-scoped
IP-derived rate buckets with short expiry rather than storing raw IPs in D1.
Cloudflare still processes network traffic and may retain platform/security data;
this is not a promise of complete anonymity. Local history and server reports have
separate deletion controls. D1 backup retention is separate from live-data deletion.


## Using run history

Open **Pear**, then use **Window → Run history** (Command-Shift-H).
Do not run the old Pear app at the same time. Existing Steam login, games and saves
are retained. Games opened through this Pear installation are observed; unrelated
Wine environments are excluded. When Wine does not expose a Steam App ID to
macOS, Pear matches the running executable to a unique installed-game manifest in
this prefix's primary Steam library. Known Steam, overlay and crash helpers are
excluded. Games in other libraries without a proven mapping remain unidentified.
Observation starts when Pear sees the process; it cannot reconstruct earlier
unobserved time. Closing the Pear window keeps the observer alive
while its Steam or games run. Explicitly choosing Quit Pear stops observation;
interrupted observations remain unknown.

The first-run **Help improve Pear** screen preselects **Automatic sharing** and all
four field groups. This is a draft, not consent: nothing is sent until you click
**Enable automatic sharing**. **Continue without sharing** or closing the window
keeps sharing off. The introduction is remembered across restarts and is not shown
on ordinary updates. Existing choices are preserved.

Use **Pear → Settings → Sharing** (Command-comma) to change these choices, or
**Sharing settings…** at the bottom of Run history. Choose one of three modes:

- **Manual sharing**: keep local records; share an individual record only when you
  choose **Share result**. Select fields before a manual submission.
- **Ask after each game**: choose a result and optional note after exit, then
  **Share result** or **Skip this time**. **Switch to manual sharing after this game**
  stops future questions and automatic sends; it does not enable automatic sharing.
- **Automatic sharing**: enqueue the selected observations
  after game exit. Results stay **Not confirmed** until you supply a result.
  Notes and optional test details are never sent automatically. Completion
  notifications are optional and off by default. **Remind me to add a result or note** opens Run history from a notification; it never sends notes automatically.

**Save changes** saves only on this Mac. **Share result** submits the saved result
and selected fields; check **Include this note when I share** to send a private
note. **Optional test details** adds the catalog's furthest result, active play
minutes, input, audio, save/reload, recovery and settings fields. Unchecked or
unobserved information remains unknown. The Steam App ID and available installed
build are read automatically; a store URL can be derived from the App ID without
additional input. Sharing the game field is optional.

An updated result uses the same report ID with a newer revision. It returns to
private review instead of creating another report. **View shared content** shows
the last acknowledged payload. Failed sends retry with bounded backoff while Pear
is running; after 14 days they require **Retry sending**. Offline records remain
local and survive restarting Pear.

**Turn off automatic sharing** immediately selects Manual sharing and cancels queued
automatic sends. This setting survives restart. Previously sent reports and
explicitly requested manual sends are separate; a request already received by the
server cannot be recalled by cancelling the network operation.

Local records are retained for 90 days, except records with pending transmissions.
**Export** saves a shareable JSON projection, without exact timestamps; a note is
included only when selected. **Delete local record** removes the local record and
its queued sends, but keeps the last shared receipt. **Shared reports** manages
server deletion even after local deletion. A failed deletion can be retried there;
it blocks uploads for that record until confirmed. Keep this Mac's Keychain and
report ownership data if you need to modify or delete submitted reports.

## Manual verification scenarios

Short runs are sufficient; these checks do not require repeating long gameplay
qualification for the unchanged runtime. Exit the game normally between scenarios.

1. **Local and manual**: keep sharing off, play briefly and exit. A named record
   should appear without sending. Add a result, select sharing fields and manually
   share. Check **Shared** and **View shared content**, then the private review
   queue. Add a note with explicit inclusion and share again: the same report
   should update, not duplicate. The note must not appear in the public projection.
2. **Ask after exit**: choose Ask after each game. Exit a short run, select a result
   and Skip; it stays local. On another exit, Share sends the chosen result. Select
   Switch to manual sharing after this game and verify that the mode becomes Manual
   sharing and later exits neither prompt nor upload automatically.
3. **Automatic**: choose automatic sharing and fields, leaving notifications off.
   Close the Pear window, play and exit. Reopen Run history: the record should be
   shared without a question, with an unconfirmed user result and no note. Add a
   result or note later using a manual update.
4. **Offline and withdrawal**: after Steam is usable, disconnect the network,
   finish a run in automatic mode and see a pending/failed send. Turn off automatic
   sharing before reconnecting, restart Pear and confirm that the queued automatic
   report was removed and the mode remains Manual sharing. Manual sharing/retry
   should still work. Avoid changing connectivity during downloads or cloud saves.
5. **Review and removal**: approve a real report in the administrator queue. It
   enters Queued, then Published after the next successful daily deployment.
   Check the store link and unknown fields. Test local deletion and server deletion
   on a disposable report separately; server deletion removes the catalog entry
   on the next successful deployment, not immediately.

Do not approve synthetic test reports for the public catalog. App execution and
manual input response remain user-confirmed checks, distinct from fixture tests.
