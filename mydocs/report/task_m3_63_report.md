# Task #63 — Consent-based reports and run history

GitHub Issue: [#63](https://github.com/postmelee/pear/issues/63) · Milestone: M3

## Work Summary
Three stages: service/consent design, local observation/UI/hosted integration, and
signed-app handoff. The requester chose Cloudflare Workers + D1 with no extra user
login and GitHub OAuth for the sole allowed administrator. UI and all three report
modes were reviewed with the requester; publication remains privately reviewed.

## Changed Files and Impact Area
| Area | Outcome |
|---|---|
| ReportingPolicy/Store/Transport.swift | Field consent, durable records/revisions, bounded offline queue and per-report Keychain capabilities |
| RunObserver.swift / Launcher.swift | Exact prefix/runtime ownership, single owner, process identity and window-close lifetime |
| HistoryWindow/AppStyle.swift | Local history/detail, manual result/note/export/delete, settings and separate first-run consent |
| preview/reporting-worker | Validation, quotas, idempotency, OAuth administrator, private review and public projection |
| Catalog/reporting sync | GitHub source links, immutable approved daily snapshot and successful-deploy acknowledgement |

## Document Location Verification
Player/privacy/index guidance is in the plan-approved docs/ paths. Task plans and
reports stay in mydocs/. Public website changes use the existing catalog generator.
Cloudflare operational and retained evidence is in the stage reports, not presented
as an unrestricted privacy guarantee.

## Quantitative Before/After Comparison
Before: no integrated local history or consent-based report path. After: three
persisted modes, four field groups, same-ID report updates, private review and one
daily catalog schedule. Six native reporting/observer/presentation suites and seven
Worker tests passed in their recorded scope; the integrated docs suite has 116
passing tests. Test counts do not establish universal game identification.

## Verification Results
| Acceptance criterion | Result / evidence |
|---|---|
| Default silence and withdrawal | Explicit-confirmation gate; preselected first-run draft is not consent; queue cancellation/restart and race fixtures passed |
| Manual notes and updates | Explicit notes only, same report ID/revision, sent-content/export/retry/delete controls; requester manual/ask tests passed |
| Automatic observation | Megabonk App ID/name/build identified after bounded manifest fallback fix; real automatic receipt verified and owner confirmed |
| Process ownership | Exact prefix/runtime, PID/start checks, single-owner lock before store migration; window close retains observer, explicit quit interrupts |
| Server ownership/security | Wrong owner/stale/replayed deletion rejected; OAuth state/identity tests, no embedded administrator/shared credential |
| Review/catalog | Real administrator login/approval/linking and filtered synthetic snapshot verified; notes excluded; fixture reports removed before catalog publication |
| Final integration | Protected build 8 tests and macOS 15 startup passed; signed update/final startup preserved records/consent/mappings and 11 save files |
| User-facing review | Accepted native UI and October 20 local web preview; agent browser localhost access was blocked, so visual approval is requester evidence |

### Stage Verification Results
- [Stage 1](../working/task_m3_63_stage1.md): scope, consent and provider investigation.
- [Stage 2](../working/task_m3_63_stage2.md): implementation, actual report flows and accepted UX, with dated follow-ups.
- [Cloudflare](../working/task_m3_63_cloudflare.md): hosted access and retention boundaries.
- [Stage 3](../working/task_m3_63_stage3.md): signed integration and delivery evidence.

## Retention Handoff
Retain ignored .build/task63-audit and .build/task62 evidence through final delivery.
Retain user history, ownership capabilities and private recovery state; they are
not release assets or cleanup candidates. Worker/D1 production state remains under
its documented retention: local 90 days (pending exceptions), server 180 days or
365 for published reports, export snapshots seven days. The worktree stays until
delivery checks complete. No new runtime copy or storage-recovery claim.

## Residual Risks and Follow-up Work
Earlier real reports were from the reporting candidate; build 8 did not create a
new game report. Final signed integration is CI/startup/data evidence, not a second
live report test. Unmapped games remain unknown; process duration is not active
play or Pass. Cloudflare processes IP/network metadata; complete anonymity is not
claimed. External copies and backups can outlive live report redaction. GitHub
source linking is not bidirectional content synchronization. Final release/tap/feed
anonymous-download verification remains delivery work.

## Approval Request to Task Requester
The requester authorized final publication after validation and accepted the UI and
public page. Proceed with the integrated release without renewing broad approval;
retain explicit consent and private review for each report.
