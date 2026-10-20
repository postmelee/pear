# Task #70 — Implementation plan

Issue: #70. Approved scope: requester continuation on 2026-10-20, through local preview.

## Stage 1 — Presentation and route contracts
Reuse the existing static renderer. A small HTML parser projects reviewed exact
UI messages into Korean text/accessible attributes, never global substitutions
inside markup or scripts. Explicit translate="no" boundaries protect game names,
report evidence and user-supplied values even when they match a UI message.
Code, commands and form option values retain original vocabulary. A curated
message resource is the source of translations; it is not a machine translation
service. The separately authored Korean article uses the same validated media.

Build Korean source identities under ko/, keeping shared asset URLs at the root.
Rebase once through existing clean-route generation. Add real same-page language
links, canonical/hreflang metadata and locale-scoped search. Explicit URLs win.
Keep stable section IDs and preserve valid fragment/query state across switching.
Future articles without a translation display a visible English-content notice.

## Stage 2 — Content and interaction
Translate all first-party page and dynamic UI messages, author the Korean article,
add the approved correction/date to both versions, and fix current-release claims.
Extend the existing catalog developer guide with maintenance/provenance rules.
Generate under .build/task70/site with shared media; no runtime/app builds.

## Verification
Stage 1: focused localization tests (routing, attributes, option values, protected
content and fallback), existing tests/docs suite, git diff --check.
Stage 2: repeat affected tests; node --test tests/docs/test_steam_search.cjs;
python3 tools/check_governance.py; python3 tools/check_source_notices.py --base
origin/master; git diff --check. Render actual and synthetic approved snapshots;
check local links, feed bytes, translated search, keyboard/mobile/light/dark UX.
No synthetic report is published. Record source-freeze/build/local interaction
wall and monotonic times; distinguish unavailable interaction evidence.

## Documentation and storage
Locations follow the approved task plan. Existing docs/development/catalog.md
gets maintenance guidance; article correction stays in docs/blog. UI resources
live in tools/catalog/locales. Disposable site output is below 200 MB; retain
compact evidence until review. Unrelated private/runtime artifacts are excluded.

## Handoff
Report/commit each completed stage using the stage-report procedure. Stage 2
ends with a local preview for requester review, not a deployment or public PR.
