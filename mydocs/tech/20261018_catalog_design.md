# Catalog design and blog refactor

## Authorization and scope

On 2026-10-18 the requester explicitly waived Issue registration and authorized
implementation and verification through a user-reviewable local server. They also
requested reusable tokens and components. This work uses `codex/catalog-design`
from master `6b7e1a1`; no Issue number, publication or release is invented.

## Design and reuse decisions

Reuse the Python catalog generator, reviewed data and existing JavaScript game
filters, Steam identity search and draft forms. Add a shared rendering module,
semantic CSS tokens, layout/components and independent search/theme behavior.
Match the inspected Pele layout and typography, with system-first fonts; its
publicly observed visual values inform independently implemented styles. No
Pele JavaScript, logo or author identity is imported. Theme behavior follows the
system-preference/persisted-choice pattern inspected at stephango.com.

## Locations and integration

Shared rendering: `tools/catalog_site.py`; tokens and browser components:
`tools/catalog/`. Article source: `docs/blog/`; original embedded figures:
`docs/assets/blog/`. Developer reuse guide: `docs/development/catalog.md`.
These are the product-content and contributor-documentation locations approved
by the request to proceed with the presented scope. Tests remain `tests/docs/`.
The article is requester-supplied prose credited to Taegyu Lee; preserve its
words, links, captions, figures and release-specific qualifications. Do not
reinterpret it as current release metadata or operational instructions.

Active #63 changes the generator, catalog JavaScript and catalog tests in its own
worktree. Do not edit that worktree. Keep existing data contracts and intake
behavior, isolate new presentation code and record integration as outstanding
until that branch is merged. Preserve unrelated `analysis/` and `research/`.

## Verification and artifacts

Run existing documentation/catalog and Steam-search checks, targeted nested
output/search/article validation tests, notice checks and browser checks for
desktop/mobile, theme persistence, TOC history, search keyboard/focus behavior,
blog and existing forms. Use `.build/catalog-design/site` for a loopback-only
preview and `.build/catalog-design/` for timings/screenshots. Expected peak is
under 20 MB for static output/evidence; no native builds or runtime copies.
Keep source images/article and review evidence; generated previews are disposable
after local review and may remain while the user uses the server. Runtime
qualification is not part of website verification.

## Result and verification

Implemented the shared shell, semantic light/dark tokens, responsive navigation,
active/read section TOC, Explore cards, matching footer composition, global
keyboard search, Pear-first titles, blog index and article detail. Existing game
filters, report views, Steam identity lookup, download tabs and local GitHub
request/report preparation remain on their original data/controller path.
Reusable `BlogPost` registry entries derive the blog cards, output allowlist,
article shell, TOC and public search records. The contributor guide documents
adding pages/posts and customizing tokens.

Verification on 2026-10-18:

- 101 documentation/catalog Python tests passed, including seven new behavioral
  tests for complete internal links/assets/fragments under `/pear/`, deterministic
  rebuilds, nested publication boundaries, unsafe article rejection, content and
  figure preservation, search targets and heading hierarchy.
- Six existing Steam identity JavaScript tests passed; browser JavaScript syntax
  checks passed. Governance passed: 38 documents and 373 local targets.
- `git diff --check` passed. Incremental worktree notice inspection found no
  errors in touched files. Its whole-worktree report also includes pre-existing,
  unrelated untracked `analysis/` scripts; those files were not changed.
- Browser: desktop at 1280px and mobile iframe viewports at 390px; home, article
  and games visually inspected. Mobile menu opens, follows a section and closes;
  the mobile search button has a persistent accessible name.
- Search: title/body results, no-result state, Cmd+K, arrows/Enter, Escape and
  focus return verified. Added explicit Escape handling for consistent behavior.
  Article search results navigate to the actual section; download results target
  the correct app/CLI/Homebrew tab. No external form submission was performed.
- Theme: initial system dark appearance, explicit light selection retained on
  navigation, dark selection retained after reload. Article TOC current/read
  states, 32px desktop anchor clearance and browser Back were confirmed.
- Existing game search/reset/runtime/result filters, click/keyboard download tabs
  and local game-request draft generation were exercised. Browser error/warning
  log was empty at the final home inspection.
- Original attachment main text equals the rendered article text after HTML
  normalization. Both extracted PNG byte streams equal the original embedded
  images. Intrinsic dimensions reserve figure space before lazy loading.

Original attachment SHA-256:
`37e79efe115dc1bb6c6cdcbe358a35c818510ed64d281d032f5aca6b3793cf6c`.
Final static-site digest (sorted relative names plus bytes):
`a9d23c0191e368af9da9f349b4e8fddd2b33c70f470b1ffc566e927b57a86953`.

Final frozen-source verification interval: build 0.055 s, Python checks 5.270 s,
Steam checks 0.122 s, governance 0.066 s, whitespace check 0.010 s. One continuous
monotonic interval through automated browser input confirmation was 40.927 s;
this includes tool/coordination and browser preparation. No before-change baseline
was recorded. Human manual-input confirmation remains pending requester review;
the automated endpoint is not claimed as the required manual-response baseline.
Detailed wall/monotonic timestamps are retained in the ignored verification JSON.

## Local handoff and retention

Preview: `http://127.0.0.1:8765/`, served only from
`.build/catalog-design/site` by a loopback-bound Python server. Blog index:
`http://127.0.0.1:8765/blog/`. No production deployment, Issue, PR or external
message was created. Active #63 integration remains a separate future merge;
its worktree and current release metadata were preserved.

Generated output: 2,527,159 logical bytes, 2,580,480 allocated bytes. No filesystem
free-space delta was measured. Keep the server/output for requester review;
retain source assets and this record. Screenshots and detailed check logs are
under `.build/catalog-design/`. The temporary mobile review harness was removed
from the public output after inspection.

## Installation navigation follow-up

The requester authorized an Installation heading above the download-method tabs,
a matching TOC entry, and preservation of the selected tab during section
navigation. The shared heading renderer generates the TOC entry. Download tab
hash handling now changes selection only for recognized method anchors.

Rebuilt the existing local preview. All seven catalog-site tests, JavaScript
syntax validation and whitespace checks passed. Browser input confirmed that
both CLI and Homebrew remain selected after visiting another section and
returning through Installation; the direct `#cli` link still selects CLI.
Screenshot: `.build/catalog-design/download-installation.png`. The prior site
digest and timing above describe the initial handoff, before this follow-up.

## Typography and reference-icon follow-up

The requester authorized a lower heading level inside the installation tabs and
closer reference icons. All three panel titles are now semantic h3 elements,
using the reusable subheading token. At the reviewed 1280px viewport they render
at 16.56px, below the 20px Installation h2.

Inspected live reference DOM and computed CSS: Pele uses a 16px Lucide/Feather
search SVG with a 2-unit rounded stroke. Stephango uses a 36 by 20px track and
an 18px moving Heroicons sun/moon, rather than a circle over Unicode glyphs.
Shared SVG definitions live in `tools/catalog_icons.py`; upstream MIT/ISC and
Feather notices are included in generated pages. Official upstream licenses were
read before reuse. The switch is independently implemented with the observed
geometry, state positions and 100ms timing. Search children use aligned line
boxes and share the same measured vertical center.

Rebuilt the local site; 25 compatibility and seven catalog-site tests passed,
as did the whitespace check. Browser checks confirmed h2/h3 sizes, SVG geometry,
light/dark states and search open/close. Screenshot:
`.build/catalog-design/download-icons-hierarchy.png`. Earlier handoff digests
and timings do not cover this follow-up.

## Theme restoration and mobile review

At the requester's direction, restored the 44 by 24px switch with a circular
sliding knob and text sun/moon symbols. Enlarged the sun from 13px to 16px and
requested text presentation to avoid emoji rendering. Removed unused Heroicons
definitions and notices; the shared Search SVG and its upstream notices remain.
Heading hierarchy and Search alignment are unchanged. On mobile, an invisible
pseudo-element expands the switch hit area to 44px high without changing its
visible dimensions or header spacing.

Reviewed Download at 390px and Games at 320px using local iframe viewports in
both themes, and exercised mobile Search open/close and theme switching.
Desktop inspection confirms the enlarged sun and restored knob. Seven site
tests and whitespace validation passed after rebuilding. Screenshots are
`mobile-theme-restored.png` and `desktop-theme-restored.png` under the ignored
`.build/catalog-design/` directory. Removed the temporary review HTML from the
served output; the existing local server remains available.
