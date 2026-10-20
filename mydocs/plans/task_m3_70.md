# Task #70 — Korean website and language switching

GitHub Issue: [#70](https://github.com/postmelee/pear/issues/70)
Milestone: M3 — Rosetta-based Megabonk Preview

## Purpose
Provide an English/Korean Pear website with an explicit language switch and
reviewed Korean content. Preserve the released product, compatibility evidence,
and current English URLs. Show the localized site locally before publication.

## Background
The requester approved Issue registration and task-plan preparation on 2026-10-20.
Pear 0.1.0 is public; PRs #68/#69 completed its delivery. The static website and
shared design were established in #66/#67. Live inspection found no competing
open localization Issue or PR. Source baseline: master `50f1e6e`.

Read root AGENTS.md, README, docs/README.md, architecture, delivery plan,
docs/development/catalog.md, docs/blog/AGENTS.md, docs/AGENTS.md, tests/AGENTS.md,
and task registration/start/document-location procedures. The requester explicitly
requests Korean translation: localized resources are an authorized exception to
English-only product prose; engineering plans/reports/comments remain English.

## Scope
### Included
- Shared header language control labelled English / 한국어, accessible by keyboard.
- Existing English paths plus Korean counterparts under `/pear/ko/`.
- Korean first-party home, download, about, updates, game/report/form UI, search,
  blog index/archive and the existing development article.
- Preserve selected page and stable fragments when changing language. Keep
  language consistent while following internal navigation.
- Language-specific search, metadata and meaningful fallback labels.
- Contributor instructions for maintaining translations and publication checks.
### Excluded
Native app/CLI localization, runtime changes, new compatibility claims, automatic
translation of player submissions, wholesale translation of GitHub documentation,
new external translation services, and changes to signed feeds or release assets.

## Design Direction
- Reuse Python static generation, semantic HTML, CSS tokens and plain JavaScript.
  No framework or localization package is needed for two static languages.
- Add explicit locale-aware message lookup and page metadata; do not translate
  arbitrary rendered HTML through global string replacements. Keep identifiers,
  stored report enums, App IDs, package versions and download URLs invariant.
- Use stable ASCII route/section identifiers. English stays at existing routes;
  Korean uses a `ko/` prefix. Use real links for language switching so JavaScript
  is not required. An explicit URL is authoritative; do not redirect an English
  shared URL solely because a stored preference says Korean.
- Preserve query state where meaningful and fragments present in both pages.
  Shared assets remain shared, avoiding duplicate video/image copies.
- Korean UI labels may translate observations, but user notes and report source
  text remain original. Submission payload vocabulary stays compatible with the
  current GitHub/report pipeline.
- Translate the authored blog as a separate source while retaining its author,
  date, media and historical claim scope. Display English fallback explicitly if
  a future article has no reviewed Korean translation.
- Keep the update feed byte-identical and the catalog daily prepare/deploy/ack
  sequence intact. Localization changes display, not moderation or qualification.
- Review existing template/rendering and browser-controller contracts before
  extracting messages; preserve SPDX and media provenance. Apple tooling and
  Sites skills are not applicable to this existing GitHub Pages static site.

## Document Location Judgment
| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| Korean article | Official translated content | Readers | docs/blog/ko/running-megabonk-on-an-apple-silicon-mac.html | mydocs/ | Authored public content belongs beside the existing blog source |
| Translation maintenance | Official developer guide | Contributors | docs/development/catalog.md | New parallel guide | Extend the existing renderer/content contract |
| UI messages | Source resources | Renderer/contributors | tools/catalog/locales/ | docs/ | Messages are rendering inputs, not standalone documentation |
| Plan/results | Workflow artifacts | Maintainers | mydocs/plans, working, report | docs/ | Issue-specific evidence stays separate from product guidance |

## Expected Changed Files
New: locale resources under tools/catalog/locales/, a small locale helper if
needed, docs/blog/ko/running-megabonk-on-an-apple-silicon-mac.html and focused
localization behavior tests under tests/docs/.

Modified: tools/catalog_site.py, tools/compatibility.py, relevant catalog JS/CSS,
docs/development/catalog.md, and existing Pages allowlists/path triggers only
where localized source discovery requires it.

Task artifacts: mydocs/orders/20261020.md, this plan,
mydocs/plans/task_m3_70_impl.md, mydocs/working/task_m3_70_stage{N}.md and
mydocs/report/task_m3_70_report.md.

## Artifact Lifecycle
| Artifact/root | Class and state | Owner/consumer | Identity and recovery needs | Retain reason | Release condition |
|---|---|---|---|---|---|
| Existing tracked source/media | Reusable input | #70 renderer | Base commit and exact media bytes | English baseline and public assets | Retain in Git |
| .build/task70/site | Planned disposable output | #70 local review | Rebuild from task commit | Desktop/mobile preview | Stop owned server after review/deployment |
| .build/task70/evidence | Planned bounded evidence | #70 review | Commands, source SHA, compact screenshots/timing | Verification and report | Preserve compact final evidence |
| Other .build roots | Retained unrelated/recovery state | Prior tasks/requester | Existing retention records | Not #70 disposable data | Excluded from cleanup |

Reuse the clean attached task47 worktree on the new `codex/task70` branch to avoid
another checkout and preserve its ignored recovery store; do not reuse its old
build outputs as verification. No Wine/game/prefix copy. Main checkout stays on
master and its untracked analysis/research directories remain untouched.

Peak new output target below 200 MB, using shared assets within each generated
site. `df -k` at planning observed 2,472,764 KiB available on /dev/disk3s5; recheck
before generation because concurrent activity changes free space. No app builds,
package downloads or dependency reinstalls are planned.

## Tentative Stages
- **Stage 1 — Locale architecture and core navigation**: implementation plan,
  explicit message/route contracts, locale shell and page mapping; verify English
  route preservation, Korean metadata and shared asset resolution.
- **Stage 2 — Korean content and local UX**: complete first-party page/form/search
  translations and article, mobile/light/dark review; show user-operable preview.
- **Stage 3 — Integration and publication**: approved checks, reviewed public
  snapshot integration, final report/PR, and Pages publication after preview approval.

Complete/report/commit each stage before requesting explicit continuation.

## Verification Plan
Tools observed: Python 3.14.4; Node v24.15.0 at
`/Users/melee/.nvm/versions/node/v24.15.0/bin/node`. Browser accessibility and current
local-tab access remain to be checked; earlier URL-policy failures are not a pass
and must not be bypassed. If blocked, request user visual review.

### Stage Verification
1. Locale mapping tests: English URL compatibility, nested Korean paths, legacy
   redirects, fallback behavior, language metadata and shared relative assets.
2. Test real rendered pages: translated fixed UI, original report data, download
   links, safe form output, language-scoped search, theme/mobile/keyboard behavior,
   retained section anchors and translated article attribution/media.
3. Run existing approved checks:
   - `python3 -m unittest discover -s tests/docs -p 'test_*.py'`
   - `node --test tests/docs/test_steam_search.cjs` using the observed executable
   - `python3 tools/check_governance.py`
   - `python3 tools/check_source_notices.py --base origin/master`
   - `git diff --check`

### Integrated Verification
Render with empty and synthetic approved snapshots locally; never publish synthetic
reports. Check internal URLs under the GitHub Pages `/pear/` prefix and verify the
signed appcast is unchanged byte-for-byte. Inspect both themes at desktop/mobile
sizes, keyboard focus, search, catalog filters, download tabs and draft forms.
Record actual tool output and limitations. Existing runtime/game qualification is
unchanged, so no gameplay or signed-app retest is required. Record continuous
source-freeze-to-operable-preview wall/monotonic timing, separating human response
waiting; do not substitute build time or a screenshot for confirmed interaction.

## Risks
- Missing or stale translations: explicit locale keys, coverage checks and visible
  English fallback for unavailable article translations.
- Route/asset regressions: nested `/pear/ko/` tests and canonical/hreflang checks.
- Changed meaning: preserve unknown/failed observations and consent limits; review
  Korean requirements/privacy text against the original.
- Browser storage unavailable: real language links still work; preference storage
  must be optional and never override explicit URLs.
- Scope growth: technical docs and native apps stay English in this task.

## Approval and expanded editorial scope
On 2026-10-20 the requester explicitly approved implementation through a local
preview, including Korean translation, language switching, stale current-Preview
wording on the home/about pages, and a dated blog correction. Public deployment
remains pending local review. This continuation covers Stages 1 and 2.

Keep the article publication date 2026-10-18 and add updated date 2026-10-20.
The original registered article already described 0.1.0 as available; explain that
premature claim instead of silently moving its publication date. Correct current
release/source links and reporting descriptions; retain historical Preview.4 links.
These edits belong in the existing article and page templates, not a new guide.
