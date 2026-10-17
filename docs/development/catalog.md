# Website design and content components

The Pear website is a static build from reviewed catalog data and local article
sources. It reuses Python, HTML, CSS and JavaScript; no application framework,
account, or external search service is required.

## Run locally

From the repository root:

```sh
python3 tools/compatibility.py --check --site .build/catalog-design/site
python3 -m http.server 8765 --bind 127.0.0.1 --directory .build/catalog-design/site
```

Open `http://127.0.0.1:8765/`. The server serves only the generated public output.
Use a new empty output directory when changing the allowlist; the builder refuses
unknown files and symlinks instead of deleting them.

## Design tokens

`tools/catalog/tokens.css` is the shared customization surface. Both themes use
the same semantic names:

| Group | Main tokens | Purpose |
|---|---|---|
| Typography | `--font-sans`, `--font-size-body`, `--font-size-heading`, `--font-size-title`, `--line-height-body` | Font stack, scale and reading rhythm |
| Colors | `--color-bg`, `--color-surface`, `--color-text`, `--color-muted`, `--color-border` | Page, panel, text and separators |
| States | `--color-focus`, `--color-positive`, `--color-warning`, `--color-negative` and their backgrounds | Focus and report outcomes |
| Spacing | `--space-1` through `--space-13`, `--section-gap` | Shared spacing scale |
| Layout | `--reading-width`, `--sidebar-width`, `--sidebar-gap`, `--anchor-offset` | Reading column, navigation and anchor clearance |
| Shape | `--radius-small`, `--radius-panel`, `--radius-pill` | Controls, cards and switch |

The dark theme overrides colors under `:root[data-theme="dark"]`. The light
palette is the root default. A media-query fallback handles JavaScript-disabled
browsers. Update both dark definitions together if changing the dark palette.
The font stack prefers the platform system font; no remote font request is needed.

The visual values were inspected at [Pele](https://pele.run/) on 2026-10-18.
Pear's CSS and browser controllers are independently implemented; Pele's logo,
author identity and application code are not bundled. The system preference and
persisted theme choice follow the behavior observed at
[Steph Ango's website](https://stephango.com/).

## Shared components

`tools/catalog/components.css` provides typography, the responsive page shell,
sidebar/TOC, footer, Explore cards, buttons, form controls, badges and search dialog.
`tools/catalog/style.css` contains only page compositions: home, blog, game list,
reports and download panels. New page styles should consume semantic tokens.

`tools/catalog_site.py` exposes reusable renderers:

- `shell(title, content, active, root='', article=False, description=None)`:
  metadata, header, navigation, heading anchors, footer and search dialog.
- `prepare_content(content, levels)`: stable heading anchors and the outline.
  Supply explicit IDs when a URL must survive future heading edits.
- `navigation(active, outline, root)` and `footer(root)`: one shared navigation
  definition, including root-relative resolution for nested output pages.
- `explore_cards(items)`: semantic links from `(title, summary, href)` tuples.
- `latest_item(post, content)`, `writing_list(posts, prefix)` and `blog_pages()`:
  latest preview, chronological writing rows, topic archives and article shell.
- `search_index(pages)`: public page/section records from rendered main content.
  Forms, drafts and conditional empty states are omitted.

The `active` key is one of the keys in `NAVIGATION`. A page one directory below
the site root uses `root='../'`; keep its own article links relative to that page.
The builder and link regression test support the GitHub Pages `/pear/` prefix.

`theme.js` applies the initial theme before styles load. `site.js` manages the
switch, mobile navigation, current/read TOC state and search. `catalog.js` and
`steam-search.js` retain the catalog filters, download tabs, game identity lookup
and local GitHub draft behavior. Global search does not replace Steam lookup.

## Add a blog post

1. Add a reviewed HTML article fragment to `docs/blog/<slug>.html`, with one
   `h1`, an introduction, byline and `h2`/`h3` sections. Preserve attribution and
   applicable source notices. Do not include a document shell, inline styles,
   scripts or event handlers.
2. Add any reviewed PNG figures to `docs/assets/blog/`. Use unique filenames,
   meaningful alt text and article-relative `images/<filename>.png` sources.
   The renderer reads intrinsic image dimensions to reserve layout space.
3. Add a `BlogPost` record to `POSTS` in `tools/catalog_site.py`. Supply title,
   summary, author, edition, the exact image tuple, an approved ISO publication
   date (`published`) and a tuple of topic identifiers (`topics`). The list sorts
   newest first. Latest shows the full date, computed reading time, linked author
   and summary; Writing shows year/month and title. `series` (default Pear
   development journal) and `edition` generate Topics and their filtered archives.
   The separate `topics` identifiers continue to rank related articles.
   Omit the date if unknown; it is never inferred from build time or file dates.
4. Rebuild and run the checks below. The registry derives the public page/image
   allowlist and index cards; rendered content supplies the search index and TOC.

Article validation fails on unsupported markup, unsafe links, unknown images or
unbalanced elements. Expand the supported format only with appropriate tests.
The first article came solely from the requester-supplied HTML, credited to
Taegyu Lee; its prose, HTTPS links, two tables and original PNG bytes are retained.
Its release-specific statements are independent of current download metadata.

## Automatic article components

The article renderer preserves the source title, subtitle, byline and body while
placing the publication date and estimated reading time directly below the title.
Reading time is rounded up at 220 words per minute, with a one-minute minimum;
it uses body text, including headings and captions, but excludes generated
navigation, recommendations, title, subtitle and byline.

`linked_mentions` scans actual links in editorial page content and source
articles before adding generated recommendation sections. Local relative links
resolve from the source page, including fragments; external links, self-links,
navigation and generated backlinks do not produce mentions. Each source appears
once. Article sources can link to known published local pages as well as public
HTTPS URLs; private paths and paths escaping the site prefix are rejected.

`related_posts` ranks other registered articles by shared topics, then date and
slug, with at most three results. Sections with no matches are omitted. With only
one article, no recommendation is fabricated. `update_links` renders the shared
Receive updates section using the official Pear X account and the developer's
personal X and Threads accounts. These are ordinary links, not subscriptions or
embedded social widgets. First-article publication date 2026-10-18 was explicitly
supplied by the requester.

## Verify a change

```sh
python3 -m unittest discover -s tests/docs -p 'test_*.py'
node --test tests/docs/test_steam_search.cjs
python3 tools/check_governance.py
python3 tools/check_source_notices.py --base <comparison-commit>
git diff --check
```

Inspect desktop and narrow mobile views in both themes. Check keyboard search,
Escape/focus return, direct section URLs, browser history, mobile navigation,
tables/figures, game filters, download tabs and draft forms. Static-site checks
never establish runtime or game compatibility. Review deployment separately;
local preview does not publish the site.
