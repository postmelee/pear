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

## SVG-only theme refinement

The requester retained the circular switch behavior but asked for Stephango's
sun/moon geometry and hover emphasis. Restored the shared Heroicons SVG shapes
and their upstream notices, replacing only the text glyphs. The 44 by 24px track,
16px knob, 20px travel, timing and mobile touch area remain unchanged. Added a
dedicated theme hover token matching the inspected reference action colors:
light `#24837b`, dark `#3aa99f`; keyboard focus uses the same emphasis.

Rebuilt the local preview and passed all seven catalog-site tests and whitespace
checks. Browser input confirmed both checked states, actual `:hover` matching,
computed highlight colors and unchanged knob travel. Screenshot:
`.build/catalog-design/theme-svg-hover.png`.

## Constant toggle-knob color

The requester asked to preserve the dark-theme knob color in both themes.
Added the theme-independent `--color-theme-knob: #cecdc3` token. Rebuilt the
local site; browser checks confirmed `rgb(206, 205, 195)` in both light and dark
states. Whitespace validation passed. Screenshot:
`.build/catalog-design/theme-knob-constant.png`.

## Game-card consistency and responsive artwork

The requester reported inconsistent game-card styling and unused space beside
artwork at intermediate widths. The mobile 240px cover-height cap interacted
with its aspect ratio, reducing the image width. Removed that cap and set an
explicit full-width cover and media link. Card layout now follows a 520px list
container breakpoint rather than the global mobile-navigation breakpoint.

Introduced reusable panel padding/gap and game-art ratio/column tokens. Game
titles use the shared subheading size, metadata uses the common small type,
and status badges retain the shared semantic backgrounds. The card's primary
fill override and secondary boxed action were replaced by the shared standard
button and text-link styles. Other page controls and theme behavior are intact.

Rebuilt the site; 25 compatibility tests and seven catalog-site tests passed.
Browser review covered 390px, 580px and 675px iframe viewports plus desktop in
light/dark themes. Stacked artwork fills the content width without cropping;
wide cards use the side-by-side layout. Result filtering and reset remained
functional. Screenshots: `game-card-responsive.png`, `game-card-desktop.png` in
`.build/catalog-design/`. Removed the temporary responsive review page.

## Restore game-card action emphasis

The requester preferred the original button emphasis. Restored the filled small
primary View game action and outlined small Request support action, retaining
the responsive artwork and other card refinements. Rebuilt locally and checked
the rendered classes/fill and whitespace. Screenshot:
`.build/catalog-design/game-buttons-restored.png`.
Recommended normal body color for page introductions and muted color for
metadata; no introduction-color change was made while discussing that choice.

## Button label wrapping audit

The requester reported a wrapped Request a game label and asked to inspect
other buttons. The shared button now uses nowrap and does not shrink inside
flex layouts. Contribution and section-header rows can wrap their children;
the contribution copy has a flexible basis so the entire action moves below
when necessary. Compact section actions and command-copy buttons also resist
text wrapping. Existing action groups already supported flex wrapping.

Inspected 18 unique generated button labels in a 240px-wide review column:
none wrapped or overflowed. Reviewed actual Games layouts at 320px and 800px;
Request a game stays on one line and card actions move to separate rows on the
narrow viewport. Rebuilt the site and passed whitespace validation. Removed
both temporary review pages. Screenshot:
`.build/catalog-design/button-nowrap-responsive.png`.

## Request-support label

Removed the upward arrow from Request support at the requester's direction.
Rebuilt and verified the label in both Games and the game detail output.
Existing vote labels and button styles remain unchanged.

## Consistent muted page introductions

The requester chose Games-style muted introductions. Added shared intro-copy
color styling alongside page-intro, using the existing theme-aware muted token.
Applied it to Home, Download, both introductory About paragraphs, and the
request/report introductions. Games, Blog and article introductions already
use the same token. Existing spacing and normal body text remain unchanged.
Rebuilt the local site and checked whitespace. Browser checks confirmed light
`#6f6e69` and dark `#878580`; screenshot: `.build/catalog-design/intro-muted.png`.

## Blog metadata, connections and updates

The requester authorized a Stephango-inspired article list retaining subtitles,
automatic article metadata/connections, and the three supplied social accounts.
They explicitly selected 2026-10-18 as the first article's publication date.
Inspected stephango.com, /vcware and /subscribe. Reused the existing Python
registry, source validator and shared tokens, without introducing dependencies.
Implementation stays in tools; the existing contributor guide in
`docs/development/catalog.md` documents metadata and reuse. This location follows
the previously approved official documentation destination.

The index renders date, linked title and muted subtitle. Article headers preserve
the source title, subtitle and byline while adding approved publication date and
body-based reading time (220 words/minute, rounded up; current article: 11 min).
Backlinks are computed from editorial main/source content before generated
sections exist; the homepage is a real mention. Related articles rank by shared
topics, then publication date and slug, capped at three. Empty sections are
omitted, so a single-article registry does not show invented recommendations.
The shared Receive updates section distinguishes official Pear X from personal
developer X and Threads. No social account interaction or subscription occurs.

Validation now permits reviewed local relative article links inside the site
prefix. Tests cover traversal rejection, fragment resolution, duplicate and
self/external-link exclusion, multi-post recommendations, generated-link cycle
avoidance, dates, reading time and empty recommendation behavior. All 104 Python
documentation tests and six Steam-search tests passed. Governance: 38 documents,
373 targets. Whitespace checks passed. Desktop light and mobile 390px dark views
were inspected; TOC navigation reaches Linked mentions and updates. Source prose,
tables and image bytes remain unchanged. Screenshots under `.build/catalog-design/`:
`blog-list-refined.png`, `blog-article-header.png`, `blog-connections.png`, and
`blog-mobile-refined.png`. Temporary responsive review HTML was removed. The
existing loopback server remains available; no Issue or publication was created.

## Blog section and sidebar follow-up

Matched the muted, regular-weight supporting section headings shown on
https://stephango.com/vcware using the existing light/dark muted token. The
updates paragraph now labels links X (Pear), X (Taegyu Lee), and Threads
(Taegyu Lee), distinguishing project updates from personal notes in one sentence.
The shared sidebar reserves a stable scrollbar gutter and 12px inner right gap;
its outer width grows 20px into the existing column gap to retain text width.
The mobile width and padding overrides remain intact.

Rebuilt the local site and passed all 10 catalog tests. Browser inspection
confirmed light rgb(111, 110, 105), dark rgb(135, 133, 128), heading weight 400,
and an independently scrollable 200px sidebar with a stable gutter and 12px
padding. Verified sidebar scrolling and saved blog-followup.png. No article
body, active TOC behavior, account destination or publication state changed.

## Article navigation and Updates page

Requester approved a Posts section on the blog index, article-only navigation
rooted at the article title, and an Updates destination based on the structure
of https://stephango.com/subscribe. Reused the existing shell, outline builder,
footer and search projection. This is a generated public website page in
`tools/catalog_site.py`, not a new official documentation tree. The output
allowlist explicitly includes updates.html.

Blog listing titles are h3 under Posts h2 and do not enter its h2-only outline.
Article navigation contains the article title, its existing section hierarchy,
and Updates; global navigation remains available through Pear home, All posts
and the footer. Shared Receive my updates headings and other options links use
root-aware Updates paths. The concise social sentence points X to official Pear,
Threads to the developer, and GitHub to the existing Pear repository. Updates
lists all four destinations, including personal X, with explicit ownership.
No subscription form or unsupported channel was added.

All 105 Python documentation tests passed, including new checks for index/article
navigation, nested Updates paths and active navigation. Local site rebuilt;
browser verified Posts, article-only navigation and the Updates link destination.
Screenshots: article-toc.png and updates-page.png. Existing local server retained.

## Project voice and visible authors

Updated shared headings to Receive updates and the channel sentence to Follow
updates via. Updates uses We for official project posts and separately identifies
Taegyu Lee's personal notes. Both X entries in Ways to follow now use X.com.
Blog index rows render the existing registry author as By Taegyu Lee; article
headers retain their existing visible source byline. Authored article prose and
summaries remain unchanged. Rebuilt the preview, passed 11 catalog tests and
whitespace checks, and verified both bylines and Updates copy in the browser.
Screenshot: blog-author.png.

## Author links and metadata grouping

Moved listing authors below dates into a separate metadata column; summaries
remain in the title column. Article headers group the original byline with the
publication date and reading time directly below the title, before the subtitle.
A reusable author-link renderer maps Taegyu Lee to the approved personal X URL
and leaves unknown authors as escaped text. Links inherit shared muted text,
underline, hover and focus tokens. Mobile retains a single-column layout with
separation between metadata and title. Source article content remains intact.

Rebuilt local output and passed all 11 catalog tests. Browser verified both
rendered author links target https://x.com/meleeisgloom2 and inspected both
layouts. Screenshots: article-author-link.png and list-author-link.png.

## Latest, Topics and Writing

Requester approved a reference-led index and larger article metadata. Inspected
stephango.com/saw, /writing, /topics and /topics/competition/. At a 1280px
viewport the reference title measured 31.61px, weight 500, line-height 1.25;
date metadata measured 18.2px. Dedicated reusable blog title/metadata tokens
match these desktop sizes with mobile bounds. Article headers show date,
computed reading time and linked author without series/edition labels.

The index now has Latest, Topics and Writing and no Receive updates block or
outline entry. Latest uses a stretched semantic title link, with a separate
raised author link (no nested anchors). Writing uses date/title rows. Series
and edition metadata produce distinct topic archives and entry counts, with
root-aware navigation and generated output allowlisting. Existing related-post
ranking remains based on its separate topic identifiers. Updated the existing
approved contributor guide at docs/development/catalog.md for the new reusable
renderers and metadata; no documentation move or new destination was needed.

All 106 Python documentation tests passed, including multi-post series/version
filtering and header metadata assertions. Browser verified full Latest summary
click navigation, desktop index/article, topic archive, and 390px/320px mobile
views. Removed the temporary responsive harness. Screenshots include
blog-latest-topics-writing.png; local loopback preview remains active.

## Article supporting navigation and spacing

Clarified that Linked mentions is generated from incoming internal editorial
links, not outgoing references such as the GitHub compatibility README. Kept
that behavior. Promoted supporting Linked mentions (and any related-article
section) to article-title-level sidebar entries. Removed Updates from the article
sidebar and footer, and removed the article Receive updates section; the Updates
page remains available elsewhere. Reduced subtitle top spacing from 32px to
16px, removed its paragraph margins and reduced header bottom spacing from 48px
to 24px. Catalog tests (12) pass, including hierarchy and Updates absence checks.
Rebuilt and visually checked the local article; article-spacing-toc.png records
the result.

## Automatic outgoing references

Reused LinkCollector to collect anchor labels and generate References from the
original article body only. External HTTP(S) URLs appear in source order, with
exact duplicate hrefs merged using the first label. Internal Pear links, mail
links and generated author/navigation links are excluded. Labels and URLs are
escaped; empty labels fall back to their URL. Empty sections are omitted.
References is a top-level article sidebar sibling of Linked mentions.

All 13 catalog tests passed, covering duplicate entity-decoded URLs, inline
labels, excluded destinations, missing labels and the requested compatibility
README. Local browser confirmed 15 unique references and the top-level outline.
Restarted the stopped loopback preview on port 8765. Screenshot:
article-references.png. No external content was fetched or republished.

## Exact Latest typography

Compared live stephango.com Latest computed typography and its public CSS.
The previous Latest metadata incorrectly reused the larger article-header size.
Added scoped reusable Latest tokens reproducing the reference responsive size
formulas in Pear's 16px root units. At 1280px, both sites now measure: label
18.2px/27.3px, title 20.76px/26.988px with weight 500, metadata and summary
15.925px/22.295px with weight 400. Title tracking is -0.015em, and weight becomes
600 at the reference's 860px breakpoint. No reference stylesheet was vendored.
Rebuilt preview, checked whitespace and verified computed sizes and screenshot
latest-font-matched.png. Existing article-header sizing is unchanged.

## Article reading typography and recordings

Authorized follow-up: match the saw article's body typography and insert the two
requester-supplied recordings. Location: retain the existing docs/blog article and
keep its reviewed web media under docs/assets/blog/media; no new product docs.
Reused the browser's native video controls, existing article validator and fixed
public asset allowlist. No playback library or reference stylesheet was copied.

Article-only tokens now use 15px + 0.25vw, line height 1.5, a 37em desktop measure
and 88vw below 860px, with matching system font fallback and 1em paragraph margins.
Live comparison at 690px: both reference and Pear body measured 16.725px font,
25.0875px line height, 607.195px width and 16.725px paragraph margins. Different
prose naturally has different break positions; the wrapping constraints match.

Inputs remain untouched in Downloads: gameplay.mov (104,585,803 bytes, 77.72s)
and demo.MOV (981,242,477 bytes, 145.35s). ffmpeg produced H.264/yuv420p + AAC
MP4s with faststart, metadata removed, CRF 25, fast preset: gameplay 960x1280,
demo 1600x1040 at 30fps. JPEG posters come from 25s and 8s respectively.
The requester supplied and authorized these recordings; no ownership of game
artwork or other third-party UI is asserted. Binary files carry no SPDX header.

Storage: original files are not copied into Git. Web derivatives total roughly
70MiB, with one additional local-preview copy; temporary review frames are under
.build/catalog-design/media-review and disposable. No measured free-space delta
or allocated-size claim. Source media and preview copies remain needed for this
local review. No external upload or publication performed.

Gameplay is placed alongside the Rosetta observation; the screen recording is
placed after the Pear-to-Steam flow. Captions describe their scope. Video sources
and posters must be allowlisted; the renderer adds controls, playsinline and
preload=none with no autoplay. Both recordings reached readyState 4 and advanced
time after native Play input in the local browser. Responsive preview screenshot:
article-video-preview.png. The focused catalog suite passes 14 tests, including
rejection of unapproved/remote media and autoplay attributes.

Full docs suite: 108 tests passed. The worktree notice scan includes unrelated
untracked analysis/ files with missing headers; those files were not modified.
Use the exact committed diff for the scoped source-notice verification.

## Article header breathing room

Increased the gap after the complete title/date/summary header from 24px to a
reusable 2em article-header token, leaving the internal header spacing intact.
Rebuilt the local preview and checked the rendered gap (33.45px at the current
690px viewport). Screenshot: article-header-spacing.png. Whitespace check passed.

## Header responsive and theme review

Visually checked 1440x1000 desktop and 390x844 mobile in both light and dark.
Header/body gaps remain 37.2px and 31.95px respectively, with no horizontal page
 overflow. The summary becomes two lines on mobile while retaining the same
separation from prose. Kept the gap unchanged. Prevented the author name from
splitting within its link; the full name now moves together to the next line.
Rebuilt local output, checked whitespace, and saved header-desktop-light/dark.png
and header-mobile-light/dark.png. Restored light mode and default viewport.

## Article-end categories

Added a reusable article_categories component before the supporting-section rule.
It derives links from post_topics, sharing the index's series/edition archives.
Uses muted text at 0.875em, existing link hover/focus tokens and natural wrapping;
no new heading or TOC item. Local render verified both relative archive targets
and the small muted presentation. Catalog tests: 14 passed; diff check passed.
Screenshot: article-categories.png.
