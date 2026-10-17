# Report review and publication

The reporting service is separate from the released Preview app. The app's new
consent and reporting integration is still under development; enabling this service
does not enable uploads from existing installations.

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
