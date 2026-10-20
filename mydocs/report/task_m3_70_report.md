# Task #70 — Korean website and release chronology

GitHub Issue: [#70](https://github.com/postmelee/pear/issues/70)
Milestone: M3 — Rosetta-based Megabonk Preview

## Work Summary
Three stages deliver reviewed Korean website pages and same-page English/Korean
switching, followed by the authorized integration/publication procedure. The
requester accepted the local preview and requested deployment on October 20, 2026.
Current-release text now describes v0.1.0. The blog retains its October 18 date and
adds an October 20 update/correction instead of silently changing its history.

## Changed Files and Impact Area
| Path | Change Summary | Impact Area |
|---|---|---|
| tools/catalog_locale.py, tools/catalog/locales/ko.json | Reviewed presentation messages, protected values and routes | Korean content |
| tools/catalog_site.py, tools/compatibility.py, tools/community_reports.py | Bilingual generation, metadata, article dates and preservation boundaries | Website output |
| tools/catalog/*.js, style.css | Localized controls, search, stable language navigation and responsive layout | Website interaction |
| docs/blog/ | English correction and translated article with shared media | Authored content |
| docs/development/catalog.md | Locale/provenance maintenance contract | Contributors |
| tests/docs/, .github/workflows/ | Locale behavior tests and CI/deployment discovery | Regression prevention |

## Document Location Verification
| File | Planned Location | Actual Location | Result | Evidence |
|---|---|---|---|---|
| Translated article | docs/blog/ko/ | docs/blog/ko/ | OK | Approved task plan, Stage 2 |
| Original correction | Existing article | docs/blog/running-megabonk-on-an-apple-silicon-mac.html | OK | Approved expanded scope |
| Maintenance guidance | Existing catalog guide | docs/development/catalog.md | OK | Plan location judgment |
| Workflow evidence | mydocs/ | mydocs/plans, working, report | OK | Stage reports |

## Quantitative Before/After Comparison
| Metric | Before | After |
|---|---|---|
| First-party website languages | English | English and Korean |
| Article date metadata | October 18 publication only | Same publication plus October 20 update/correction |
| Final affected test suite | Existing baseline | 121 Python and 8 Node tests passing |
| Runtime/app artifacts changed | None | None |

## Verification Results
| Acceptance Criterion | Result |
|---|---|
| English paths and Korean equivalents | OK: route/legacy/metadata tests, local browser switching |
| Korean content and original data preservation | OK: protected report values, game identities, form enums and notes |
| Search/forms/download navigation | OK: automated tests and actual local keyboard, tab/hash and form interactions |
| Mobile, desktop and both themes | OK: Stage 2 browser inspection at desktop and 390 x 844; local preview accepted |
| Article chronology and historical references | OK: dates, notice and version-pinned current/historical links tested |
| Signed feed and shared media | OK: byte-identical feed test, shared asset route tests |
| Governance and notices | OK: 40 documents/383 local targets, incremental notices and whitespace checks |

### Stage Verification Results
- [Stage 1](../working/task_m3_70_stage1.md): presentation/route contracts; 118 Python tests.
- [Stage 2](../working/task_m3_70_stage2.md): translated content, correction and browser verification; 121 Python + 8 Node tests.
- [Stage 3](../working/task_m3_70_stage3.md): fresh integration verification, unchanged base and deployment-path inspection; 121 Python + 8 Node tests.

CI and production deployment are post-PR operations. Their exact head/run identities
and live checks will be recorded in the PR and .build/task70/evidence/publication.json.
No public deployment success is claimed by this pre-publication report.

## Retention Handoff
| Remaining artifact/root | State and owner/consumer | Identity/recovery reference | Retain reason / release condition |
|---|---|---|---|
| Committed source/reports | Retained; #70 maintainers | Stage commits and final PR head | Authoritative reconstruction |
| .build/task70/site | Disposable after live verification; #70 | Build command and stage manifest | Stop owned server then remove generated output |
| .build/task70/evidence | Retained; #70 publication/audit | Logs, screenshots, timing/source manifest, publication receipt | Compact acceptance evidence |
| Reused task47 worktree and other ignored roots | Retained dependency; #47/#62/#63 | Existing release-cleanup manifest and prior reports | Signed qualification, private recovery and historical state; excluded from #70 removal |

The generated preview is about 77 MB logical; no app/runtime copy was made. Other
worktrees/private state are excluded. Preserve the reused checkout detached at the
merged revision, remove #70 task/publication branches and fast-forward the main
checkout to master after merge. Actual cleanup results belong in the publication
receipt. No filesystem free-space delta or recovery success is inferred.

## Residual Risks and Follow-up Work
Korean strings require ongoing review when English UI changes. Player reports,
proper names, commands and GitHub documentation remain original; unsupported future
article translations display a clear English fallback. No native app localization
or new runtime/game compatibility claim was introduced. Remote CI/live publication
checks remain required before declaring deployment complete.

## Approval Request to Task Requester
Already authorized: the requester accepted the local preview and explicitly asked
to integrate and deploy. Proceed through required CI and existing Pages deployment.
