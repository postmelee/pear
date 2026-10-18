# Task #63 — Cloudflare provisioning checkpoint

Date: 2026-10-18 (Asia/Seoul). In progress, not production admission.

## Provisioned

- Dedicated D1 `pear-reports`, APAC, ID `16ff47ea-67ea-4574-9623-e7ffaff7fa48`.
- Migration 0001 applied remotely (six statements).
- Worker https://pear-reports.postmelee.workers.dev, version
  `81c0d1fc-24e6-4ce9-a410-25c7d7398cd0`.
- Collection disabled; administrator identity and internal service secrets unset.
- Workers observability disabled in submitted configuration. This does not
  disable Cloudflare platform/security/network-error logging.
- Compatibility date 2026-10-17: Cloudflare rejected the local Korean date
  2026-10-18 as future because its API used the previous UTC date.

## Evidence

Actual HTTPS curl probes: health 200/collection false; admin without authentication
403; forged JWT 403; internal batch/import without secret 401; report PUT 503.
Python urllib's default client was rejected by the edge with 1010, so those
responses are not treated as application authorization evidence.
Local worker tests: 6 passed. Existing catalog tests: 25 passed.
Local follow-up adds bounded admin form reads and batch acknowledgement checking;
these bytes are not yet deployed. No real player report was sent.

## Account blocker

Cloudflare Zero Trust is not activated. Selecting Free led to a checkout requesting
payment method, Terms acceptance and authorization to charge usage beyond the free
allowance. No payment details, terms acceptance or activation were submitted.
Requester was asked to activate directly or select a payment-free authentication
alternative. Admin remains denied until an authenticated path is verified.

## Prepared, not active

GitHub bridge imports selected source IDs/URLs/titles/update dates, not authors or
bodies. Review links an existing app report; no automatic equivalence or duplicate
GitHub posting. Daily Pages workflow is prepared for 09:17 KST (scheduler may delay),
exports a public immutable snapshot, and acknowledges only after Pages succeeds.
No workflow push, secrets registration, schedule activation or catalog deployment
has occurred. The branch also contains held v0.1.0 website changes; do not publish
those accidentally when integrating the catalog bridge.

Remaining: actual administrator login and JWT negative tests; native-to-hosted
report rehearsal; rate limiting/retention/deletion and concurrent publication
checks; approved GitHub source category/label configuration; CI secrets; reviewed
workflow integration and actual Pages acknowledgement; privacy documentation.

## Payment-free OAuth follow-up

Requester approved replacing only administrator authentication. GitHub OAuth with
empty scopes, S256 PKCE, browser-bound single-use transaction, fixed user ID and
one-hour opaque session implemented. Session tokens are hashed in D1; provider
access/refresh tokens are not persisted. Logout checks Origin and revokes the
server session. Expired auth rows are cleaned by the existing daily maintenance.

Seven local tests passed, including state/cookie mismatch, state replay, wrong
account, excessive OAuth scopes, logout CSRF and expired state/session. These use
a synthetic GitHub provider and do not establish real login success. Migration
0002 applied remotely; Worker version 54268ace-3412-41c8-ac53-ff1cbe185dfd deployed.
HTTPS probes: health 200 with collection false, admin 403, unconfigured login 503.

GitHub registration form prepared with exact callback
https://pear-reports.postmelee.workers.dev/auth/callback, no wildcard or device flow.
Requester must create the OAuth client and secret; no secret requested in chat.
Actual login, secret registration and end-to-end catalog verification remain open.
No Zero Trust subscription or card registration was performed.

## Actual GitHub login repair

The real callback failed before receiving a token response with fetch redirect
mode `error`; sanitized failure classification was redirect-related. Switched
provider fetches to `manual`, rejecting every non-2xx response before reading
identity or establishing a session. No redirect following was enabled. Actual
GitHub OAuth login then reached `/admin` with all four review tabs. Credentials
were not changed. Deployed version: 3da46deb-f47c-421c-9592-561c0619b569.
Regression fixture verifies a provider 302 is rejected after one fetch only.
This is real administrator-login evidence, not collection/catalog end-to-end
admission. Collection remains disabled and daily catalog action remains inactive.

## Hosted end-to-end verification and activation

Requester authorized activation. Worker ingestion enabled. Import/export secrets
provisioned in Worker and GitHub without storing them in Git. A disposable report
passed actual HTTPS receipt/retry, wrong-owner (403), stale revision (409), UI
approval into Queued, source-linking of Issue #63, public projection excluding a
private note, capability deletion and replay rejection (410). The exact synthetic
snapshot and source association were deleted before public deployment. Production
Swift URLSessionReportTransport plus ReportingCoordinator also passed hosted
receipt/durable acknowledgement and deletion with synthetic data; no actual game
was run or qualified. Existing app binaries were not changed.

Narrow catalog PR #64 based on master was merged after all ten CI checks passed.
It excludes the held v0.1.0 website changes. GitHub vars enable reporting, select
Show and tell discussions, and point to the Worker. Issues use pear-report label.
Pages run 39078857499 is the first real deployment/acknowledgement check. Daily
schedule 00:17 UTC (09:17 Korea); schedule execution can be delayed by GitHub.
Stage remains in progress: native UI service integration and final app qualification
are not established by the service probe. Public transport test claims remain
separate from gameplay and consent integration acceptance.

First Pages run 39078857499 completed successfully (build and deploy). Public
community-reports.json batch 56e3c163-cc74-5d4a-9f87-9a2f2d294bda matched the run;
acknowledgement retry returned published:true and no synthetic records remained.
Final Worker version 66d525ef-00f5-4357-b4e5-07c04db14ad8. The publication state
transition also checks the newer-batch guard within the D1 batch. Temporary probe
credentials were removed after verification; server/GitHub secret stores retain
the operational credentials. This checkpoint does not close Issue #63.
