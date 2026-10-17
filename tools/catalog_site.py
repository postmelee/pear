# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Reusable presentation components for the static Pear website.

Compatibility data and release decisions remain in compatibility.py. This module
owns the page shell, navigation, article presentation and public search projection.
"""
import html
from catalog_icons import ICON_NOTICES, SEARCH_ICON, SUN_ICON, MOON_ICON
from html.parser import HTMLParser
from pathlib import Path
import re
import struct
from dataclasses import dataclass
from datetime import date
from math import ceil
from urllib.parse import urlsplit, urljoin, unquote
import posixpath

ROOT = Path(__file__).resolve().parent.parent
REPO = 'https://github.com/postmelee/pear'
DOCS = REPO + '/blob/master/docs/README.md'
ARTICLE_SLUG = 'running-megabonk-on-an-apple-silicon-mac'
ARTICLE_TITLE = 'Running Megabonk on an Apple Silicon Mac'
ARTICLE_SUMMARY = 'How one Windows game led me to build Pear, and where I want to take it next.'
ARTICLE_PATH = f'blog/{ARTICLE_SLUG}.html'
ARTICLE_IMAGES = ('current-runtime.png', 'rosetta-free-runtime.png')


@dataclass(frozen=True)
class BlogPost:
    slug: str
    title: str
    summary: str
    author: str
    edition: str
    images: tuple
    published: str | None = None
    topics: tuple = ()
    series: str = "Pear development journal"

    @property
    def path(self):
        return f'blog/{self.slug}.html'


POSTS = (BlogPost(ARTICLE_SLUG, ARTICLE_TITLE, ARTICLE_SUMMARY, 'Taegyu Lee',
                  'v0.1.0', ARTICLE_IMAGES, '2026-10-18', ('development', 'megabonk', 'apple-silicon')),)
def topic_path(label):
    return 'blog/topics/' + re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-') + '/index.html'


def post_topics(post):
    return tuple(label for label in (post.series, post.edition) if label)


BLOG_FILES = {'blog/index.html', 'blog/topics/index.html', 'blog/writing.html',
              *(topic_path(label) for post in POSTS for label in post_topics(post)), *(post.path for post in POSTS),
              *(f'blog/images/{name}' for post in POSTS for name in post.images)}
NAVIGATION = (
    ('home', 'Introduction', 'index.html'),
    ('games', 'Games', 'games.html'),
    ('download', 'Download', 'download.html'),
    ('blog', 'Blog', 'blog/index.html'),
    ('about', 'About', 'about.html'),
    ('updates', 'Updates', 'updates.html'),
    ('docs', 'Documentation', DOCS),
)


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain_text(value):
    parser = PlainText()
    parser.feed(value)
    return ' '.join(' '.join(parser.parts).split())


def prepare_content(content, levels=(2,)):
    """Generate stable unique section anchors and a shared navigation outline."""
    used = set(re.findall(r'\bid="([^"]+)"', content))
    outline = []

    def heading(match):
        level, attrs, inner = match.groups()
        existing = re.search(r'\bid="([^"]+)"', attrs)
        title = plain_text(inner)
        if existing:
            anchor = existing[1]
        else:
            base = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-') or 'section'
            anchor, count = base, 2
            while anchor in used:
                anchor = f'{base}-{count}'
                count += 1
            used.add(anchor)
            attrs += f' id="{anchor}"'
        if int(level) in levels and anchor not in {'install-the-mac-app', 'run-from-terminal', 'install-with-homebrew'}:
            outline.append((int(level), anchor, title))
        return f'<h{level}{attrs}>{inner}</h{level}>'

    return re.sub(r'<h([23])([^>]*)>(.*?)</h\1>', heading, content, flags=re.S), outline


def local_link(path, root):
    return path if urlsplit(path).scheme or path.startswith('#') else root + path


def navigation(active, outline, root, article_title=None):
    items = []
    siblings = [item for item in outline if item[1] in {'references', 'linked-mentions', 'you-might-also-enjoy'}] if article_title else []
    outline = [item for item in outline if item not in siblings]
    entries = (('article', article_title, '#article-title'),) if article_title else NAVIGATION
    if article_title:
        active = 'article'
    for key, label, path in entries:
        current = ' aria-current="page"' if key == active else ''
        item = f'<li><a href="{local_link(path, root)}"{current}>{label}</a>'
        if key == active and outline:
            item += '<ul class="toc-outline">' + ''.join(
                f'<li class="toc-depth-{level}"><a href="#{html.escape(anchor)}" data-toc-link>{html.escape(title)}</a></li>'
                for level, anchor, title in outline) + '</ul>'
        items.append(item + '</li>')
    items.extend(f'<li><a href="#{html.escape(anchor)}" data-toc-link>{html.escape(title)}</a></li>' for _, anchor, title in siblings)
    return '<ul class="page-navigation">' + ''.join(items) + '</ul>'


def explore_cards(items):
    """Each card is one semantic link; titles and summaries remain escaped text."""
    return '<div class="explore-grid">' + ''.join(
        f'<a class="explore-card" href="{html.escape(href, quote=True)}"><h3>{html.escape(title)}</h3><p>{html.escape(summary)}</p></a>'
        for title, summary, href in items) + '</div>'


def footer(root, article=False):
    links = ''.join(f'<a href="{local_link(path, root)}">{label}</a>' for key, label, path in NAVIGATION if not (article and key == 'updates'))
    return f'''<footer class="site-footer"><p>Pear is <a href="{REPO}">open source</a> under the <a href="{REPO}/blob/master/LICENSE">GPL-3.0-or-later license</a>.</p>
<nav class="footer-nav" aria-label="Footer">{links}<a href="{REPO}">GitHub</a></nav>
<a class="footer-author" href="{REPO}"><img src="{root}pear.png" alt="" width="32" height="32"><span><span class="muted">by</span> Pear contributors</span></a></footer>'''


def search_dialog():
    return f'''<dialog class="search-dialog" id="site-search" aria-labelledby="search-label">
<div class="search-head">{SEARCH_ICON}<label class="sr-only" id="search-label" for="site-search-input">Search Pear</label><input id="site-search-input" type="search" placeholder="Search Pear…" autocomplete="off" spellcheck="false" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="site-search-results"><button type="button" data-search-close aria-label="Close search"><kbd>esc</kbd></button></div>
<p class="search-status" id="site-search-status" role="status" aria-live="polite">Search pages, games and the development journal.</p>
<div class="search-results" id="site-search-results" role="listbox" aria-label="Search results"></div>
<div class="search-help"><span><kbd>↑</kbd> <kbd>↓</kbd> to navigate</span><span><kbd>↵</kbd> to open</span></div></dialog>'''


def shell(title, content, active='games', *, root='', article=False, description=None):
    content, outline = prepare_content(content, (2, 3) if article else (2,))
    description = description or 'Windows games on Mac. Free and open source. Building a Rosetta-free way to play.'
    e = html.escape
    nav = navigation(active, outline, root, title if article else None)
    return f'''<!doctype html>
<!-- SPDX-FileCopyrightText: 2026 Pear contributors
     SPDX-License-Identifier: GPL-3.0-or-later -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pear · {e(title)}</title><meta name="description" content="{e(description, quote=True)}">
{ICON_NOTICES}
<meta name="color-scheme" content="light dark"><script src="{root}theme.js"></script>
<meta property="og:type" content="{'article' if article else 'website'}"><meta property="og:site_name" content="Pear"><meta property="og:title" content="Pear · {e(title, quote=True)}"><meta property="og:description" content="{e(description, quote=True)}"><meta property="og:image" content="https://postmelee.github.io/pear/social-card.png?v=20261018"><meta property="og:image:type" content="image/png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Pear — Play Windows Steam games on Mac, with a golden Asian pear on the right">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="Pear · {e(title, quote=True)}"><meta name="twitter:description" content="{e(description, quote=True)}"><meta name="twitter:image" content="https://postmelee.github.io/pear/social-card.png?v=20261018"><meta name="twitter:image:alt" content="Pear — Play Windows Steam games on Mac, with a golden Asian pear on the right"><meta name="referrer" content="no-referrer">
<link rel="icon" type="image/png" href="{root}favicon.png"><link rel="stylesheet" href="{root}tokens.css"><link rel="stylesheet" href="{root}components.css"><link rel="stylesheet" href="{root}style.css">
<script src="{root}steam-search.js" defer></script><script src="{root}catalog.js" defer></script><script src="{root}site.js" defer></script></head>
<body data-root="{root}"><a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><a class="wordmark" href="{root}index.html" aria-label="Pear home">Pear</a>
<div class="header-tools"><button class="search-trigger" type="button" aria-label="Search" aria-keyshortcuts="Meta+K Control+K" data-search-open>{SEARCH_ICON}<span>Search</span><kbd class="search-shortcut">⌘K</kbd></button>
<button class="theme-toggle" type="button" role="switch" aria-checked="false" aria-label="Dark mode" title="Toggle dark mode (D)">{SUN_ICON}{MOON_ICON}<span class="theme-knob" aria-hidden="true"></span></button>
<button class="mobile-menu-toggle" type="button" aria-expanded="false" aria-controls="sidebar">Menu <span aria-hidden="true">☰</span></button></div></header>
<nav id="sidebar" class="sidebar" aria-label="{'Article contents' if article else 'Site navigation'}">{nav}</nav>
<div class="page-layout"><main id="main" class="{'article-body' if article else 'page-content'}" tabindex="-1">{content}</main>{footer(root, article)}</div>
{search_dialog()}</body></html>'''


def home_content():
    return f'''<section class="home-intro"><h1 class="sr-only">Pear — Windows games on Mac</h1><img class="hero-logo" src="pear.png" alt="A golden Asian pear" width="120" height="120">
<p class="lede intro-copy">Pear is a free, <a href="{REPO}">open-source</a> Mac app for playing <a href="download.html">Windows Steam games</a> on Apple Silicon.</p></section>
<section class="home-section"><h2 id="how-it-works">How it works</h2><p>Open Pear, sign in to Steam, and choose a game you own. Pear takes care of the setup so you can get to your library.</p>
<ol class="steps-panel"><li><span class="step-number">01</span><div><a href="download.html">Install Pear</a><p>Download the Mac app and let it prepare Windows Steam.</p></div></li><li><span class="step-number">02</span><div>Open your library<p>Sign in through the official Steam client.</p></div></li><li><span class="step-number">03</span><div>Choose a game<p>Install a game you own, then select Play in Steam.</p></div></li></ol>
<p>Start with the <a href="games.html">game reports</a> to see what has been tried, on which Mac, and what happened.</p></section>
<section class="home-section"><h2 id="current-preview">The current Preview</h2><p>The downloadable Preview uses <a href="https://www.winehq.org/">Wine</a>, <a href="https://github.com/3Shain/dxmt">DXMT</a> and Apple’s Rosetta. Megabonk is our first validation game.</p><p>Play, input, audio and saved progress after relaunch have been checked on one M4 Pro. Other games and Macs remain unverified. Every report keeps its configuration and limitations visible.</p><p><a href="download.html">Download Pear</a> · <a href="game-3405340.html">Read the Megabonk reports</a></p></section>
<section class="home-section" id="games"><h2 id="explore">Explore</h2>{explore_cards([
    ('Download', 'Get Pear and open your Steam library.', 'download.html'),
    ('Games', 'Browse tested configurations and player reports.', 'games.html'),
    ('Blog', 'Follow the experiments behind Pear.', 'blog/index.html'),
    ('Documentation', 'Setup, development and contribution guides.', DOCS),
])}</section>
<section class="home-section"><h2 id="pear-in-development">Pear in development</h2><p>Pear began with wanting to play <a href="blog/{ARTICLE_SLUG}.html">Megabonk on a Mac</a>. The next goal is an experience without Rosetta across every required process and library. That runtime is still in development.</p><p>Pear is <a href="{REPO}">open source</a>. Help with the runtime, improve the app, or <a href="report.html">share a game result</a>. Small, concrete observations make the project better.</p></section>'''


def internal_target(href, source_path):
    """Resolve local references without escaping a project's deployment prefix."""
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or href.startswith('/'):
        return None
    resolved = urlsplit(urljoin('https://pear.invalid/pear/' + source_path, href))
    path = unquote(resolved.path)
    if not path.startswith('/pear/') or posixpath.normpath(path) != path:
        return None
    return path.removeprefix('/pear/')


class ArticleValidator(HTMLParser):
    """Only publish the reviewed article's inert text, links, tables and images."""
    TAGS = {'a', 'blockquote', 'code', 'div', 'em', 'strong', 'figure', 'figcaption',
            'h1', 'h2', 'h3', 'img', 'p', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul', 'ol', 'li'}

    def __init__(self, images=ARTICLE_IMAGES, source_path=f'blog/{ARTICLE_SLUG}.html'):
        super().__init__(convert_charrefs=True)
        self.images = images
        self.source_path = source_path
        self.output = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.TAGS:
            raise ValueError(f'Unapproved article element: {tag}')
        rendered = []
        for key, value in attrs:
            if key not in {'id', 'class', 'href', 'src', 'alt', 'tabindex'} or value is None:
                raise ValueError(f'Unapproved article attribute: {key}')
            if key == 'tabindex' and (tag != 'div' or value != '0'):
                raise ValueError('Only scrollable article regions may receive focus')
            if key in {'id', 'class'} and not re.fullmatch(r'[a-zA-Z0-9 _-]+', value):
                raise ValueError('Invalid article identifier')
            if key == 'href':
                parsed = urlsplit(value)
                internal = internal_target(value, self.source_path)
                known = BLOG_FILES | {'index.html', 'games.html', 'about.html', 'updates.html',
                                      'download.html', 'request.html', 'report.html'}
                public_https = (parsed.scheme == 'https' and parsed.hostname
                                and not parsed.username and not parsed.password)
                if (any(c.isspace() for c in value) or '\\' in value
                        or not (public_https or internal in known)):
                    raise ValueError('Article links must be public HTTPS or known local pages')
            if key == 'src' and (tag != 'img' or value not in {f'images/{name}' for name in self.images}):
                raise ValueError('Unapproved article image')
            rendered.append(f' {key}="{html.escape(value, quote=True)}"')
        if tag == 'img':
            if 'src' not in dict(attrs) or 'alt' not in dict(attrs):
                raise ValueError('Article images need a source and alt text')
            image = ROOT / 'docs/assets/blog' / Path(dict(attrs)['src']).name
            with image.open('rb') as source:
                header = source.read(24)
            if len(header) != 24 or header[:8] != b'\x89PNG\r\n\x1a\n':
                raise ValueError('Expected a reviewed PNG figure')
            width, height = struct.unpack('>II', header[16:24])
            rendered.append(f' width="{width}" height="{height}"')
            rendered.append(' loading="lazy"')
        else:
            self.stack.append(tag)
        self.output.append(f'<{tag}{"".join(rendered)}>')

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            raise ValueError('Unbalanced article content')
        self.output.append(f'</{tag}>')

    def handle_data(self, data):
        self.output.append(html.escape(data, quote=False))


def article_content(post=POSTS[0]):
    parser = ArticleValidator(post.images, post.path)
    parser.feed((ROOT / 'docs/blog' / f'{post.slug}.html').read_text(encoding='utf-8'))
    parser.close()
    if parser.stack:
        raise ValueError('Unclosed article element')
    return ''.join(parser.output)


def publication_label(post, compact=False):
    if not post.published:
        return 'Undated'
    published = date.fromisoformat(post.published)
    label = published.strftime('%Y · %m') if compact else f'{published:%B} {published.day}, {published.year}'
    return f'<time datetime="{published.isoformat()}">{label}</time>'


def reading_minutes(content):
    """Estimate reading time from visible article text at 220 words per minute."""
    return max(1, ceil(len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b", plain_text(content))) / 220))


def article_parts(content):
    match = re.match(r'\s*(<h1>.*?</h1>)\s*(<p>.*?</p>)\s*(<p>.*?</p>)(.*)', content, re.S)
    if not match:
        raise ValueError('Articles require a title, subtitle and byline before the body')
    return match.groups()


def update_links(root=''):
    return f'''<section class="blog-updates"><h2 id="receive-updates"><a href="{root}updates.html">Receive updates</a></h2>
<p>Follow updates via <a href="https://x.com/najukoreanpear">X</a>, <a href="https://www.threads.com/@postmelee">Threads</a>, <a href="{REPO}">GitHub</a>, and <a href="{root}updates.html">other options</a>.</p></section>'''


def updates_page():
    content = f'''<h1>Receive updates</h1>
<p class="page-intro">We post project updates on <a href="https://x.com/najukoreanpear">X (Pear)</a>. For personal notes and work in progress, follow Taegyu Lee on <a href="https://x.com/meleeisgloom2">X (Taegyu Lee)</a> and <a href="https://www.threads.com/@postmelee">Threads (Taegyu Lee)</a>.</p>
<h2>Ways to follow</h2>
<ul><li>X.com (Pear): <a href="https://x.com/najukoreanpear">@najukoreanpear</a></li>
<li>X.com (Taegyu Lee): <a href="https://x.com/meleeisgloom2">@meleeisgloom2</a></li>
<li>Threads (Taegyu Lee): <a href="https://www.threads.com/@postmelee">@postmelee</a></li>
<li>GitHub (Pear): <a href="{REPO}">postmelee/pear</a></li></ul>'''
    return shell('Updates', content, 'updates')


def linked_mentions(target, sources):
    mentions = []
    for path, (title, content, summary) in sources.items():
        if path == target:
            continue
        parser = LinkCollector()
        parser.feed(content)
        if any(internal_target(href, path) == target for href in parser.hrefs):
            mentions.append((path, title, summary))
    return sorted(mentions, key=lambda item: (item[1].casefold(), item[0]))


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.links = []
        self.current_href = None
        self.label_parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a' and dict(attrs).get('href'):
            self.current_href = dict(attrs)['href']
            self.hrefs.append(self.current_href)
            self.label_parts = []

    def handle_data(self, data):
        if self.current_href is not None:
            self.label_parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.current_href is not None:
            self.links.append((self.current_href, ' '.join(''.join(self.label_parts).split())))
            self.current_href = None


def references(content):
    """Collect outgoing web references in source order, before generated links."""
    parser = LinkCollector()
    parser.feed(content)
    seen, items = set(), []
    for href, label in parser.links:
        url = urlsplit(href)
        if url.scheme not in {'http', 'https'} or not url.netloc:
            continue
        if url.hostname == 'postmelee.github.io' and (url.path == '/pear' or url.path.startswith('/pear/')):
            continue
        if href in seen:
            continue
        seen.add(href)
        items.append(f'<li><a href="{html.escape(href, quote=True)}">{html.escape(label or href)}</a></li>')
    if not items:
        return ''
    return '<section><h2 id="references">References</h2><ul class="reference-list">' + ''.join(items) + '</ul></section>'


def related_posts(post, posts):
    candidates = [other for other in posts if other.slug != post.slug
                  and set(post.topics).intersection(other.topics)]
    return sorted(candidates, key=lambda other: (
        -len(set(post.topics).intersection(other.topics)),
        -(date.fromisoformat(other.published).toordinal() if other.published else 0),
        other.slug))[:3]


def article_connections(post, posts, sources):
    body = article_parts(sources[post.path][1])[3]
    parts = [references(body)]
    mentions = linked_mentions(post.path, sources)
    if mentions:
        items = ''.join(f'<li><a href="{html.escape(posixpath.relpath(path, "blog"), quote=True)}">{html.escape(title)}</a><p>{html.escape(summary)}</p></li>'
                        for path, title, summary in mentions)
        parts.append(f'<section><h2 id="linked-mentions">Linked mentions</h2><ul class="mention-list">{items}</ul></section>')
    related = related_posts(post, posts)
    if related:
        items = ''.join(f'<li><a href="{html.escape(other.slug, quote=True)}.html">{html.escape(other.title)}</a></li>' for other in related)
        parts.append(f'<section><h2 id="you-might-also-enjoy">You might also enjoy</h2><ul>{items}</ul></section>')
    return '<div class="article-connections">' + ''.join(parts) + '</div>'


def blog_pages(base_pages=None):
    posts = sorted(POSTS, key=lambda post: (post.published or '', post.slug), reverse=True)
    sources = {}
    for path, page in (base_pages or {}).items():
        # Inspect editorial main content before adding generated recommendations.
        content = re.search(r'<main\b[^>]*>(.*?)</main>', page, re.S)[1]
        title = plain_text(re.search(r'<title>(.*?)</title>', page, re.S)[1]).removeprefix('Pear · ')
        paragraph = re.search(r'<p\b[^>]*>(.*?)</p>', content, re.S)
        sources[path] = (title, content, plain_text(paragraph[1]) if paragraph else '')
    contents = {post.slug: article_content(post) for post in posts}
    sources.update({post.path: (post.title, contents[post.slug], post.summary) for post in posts})
    topics = sorted({label for post in posts for label in post_topics(post)}, key=str.casefold)
    def topic_links(source):
        return ', '.join(f'<a href="{posixpath.relpath(topic_path(label), source)}">{html.escape(label)}</a>' for label in topics)
    rows = writing_list(posts)
    latest = latest_item(posts[0], contents[posts[0].slug]) if posts else ''
    listing = f'<h1>Blog</h1><p class="page-intro">Experiments, observations, and the work behind Pear.</p><div class="blog-index"><section><h2 id="latest"><a href="{posts[0].slug + ".html" if posts else "#latest"}">Latest</a></h2>{latest}</section><section><h2 id="topics"><a href="topics/index.html">Topics</a></h2><p>{topic_links("blog")}</p></section><section><h2 id="writing"><a href="writing.html">Writing</a></h2>{rows}</section></div>'
    pages = {'blog/index.html': shell('Blog', listing, 'blog', root='../'),
             'blog/writing.html': shell('Writing', f'<h1>Writing</h1>{rows}', 'blog', root='../'),
             'blog/topics/index.html': shell('Topics', f'<h1>Topics</h1><p>{topic_links("blog/topics")}</p>', 'blog', root='../../')}
    for label in topics:
        path = topic_path(label)
        selected = [post for post in posts if label in post_topics(post)]
        content = f'<h1><a href="../index.html">Topics</a> / {html.escape(label)}</h1><p class="page-intro">{len(selected)} {"entry" if len(selected) == 1 else "entries"} about this topic</p>{writing_list(selected, "../../")}'
        pages[path] = shell(f'Topics / {label}', content, 'blog', root='../../../')
    for post in posts:
        title, subtitle, byline, body = article_parts(contents[post.slug])
        title = title.replace("<h1>", '<h1 id="article-title">', 1)
        minutes = reading_minutes(body)
        timing = f'{minutes} minute{"s" if minutes != 1 else ""} read'
        metadata = f'{publication_label(post)} · {timing}' if post.published else timing
        header = f'<header class="article-header">{title}<p class="article-meta">{metadata} · {author_link(post.author)}</p><div class="article-subtitle">{subtitle}</div></header>'
        article = f'<p class="crumb"><a href="index.html">← All posts</a></p><article>{header}{body}</article>{article_connections(post, posts, sources)}'
        pages[post.path] = shell(post.title, article, 'blog', root='../', article=True, description=post.summary)
    return pages


def author_link(name):
    profiles = {'Taegyu Lee': 'https://x.com/meleeisgloom2'}
    label = html.escape(name)
    if name not in profiles:
        return label
    return f'<a href="{profiles[name]}" rel="author">{label}</a>'


def writing_list(posts, prefix=''):
    return '<ul class="writing-list">' + ''.join(
        f'<li><a href="{prefix}{html.escape(post.slug)}.html"><span class="article-date">{publication_label(post, compact=True)}</span><span class="writing-title">{html.escape(post.title)}</span></a></li>'
        for post in posts) + '</ul>'


def latest_item(post, content):
    minutes = reading_minutes(article_parts(content)[3])
    return f'''<article class="latest-item"><h3><a class="latest-link" href="{html.escape(post.slug)}.html">{html.escape(post.title)}</a></h3><p class="article-meta">{publication_label(post)} · {minutes} min read · {author_link(post.author)}</p><p class="latest-summary">{html.escape(post.summary)} <span class="keep-reading">Keep reading →</span></p></article>'''


def search_index(pages):
    """Index only rendered main content, never navigation or arbitrary files."""
    entries = []
    for path, page in pages.items():
        title = plain_text(re.search(r'<title>(.*?)</title>', page, re.S)[1]).removeprefix('Pear · ')
        content = re.search(r'<main\b[^>]*>(.*?)</main>', page, re.S)[1]
        # Form controls, conditional drafts and empty-state messages are not
        # destinations. Never index personal text entered into the live forms.
        for tag in ('form', 'noscript', 'select', 'nav', 'h1'):
            content = re.sub(fr'<{tag}\b[^>]*>.*?</{tag}>', '', content, flags=re.S)
        content = re.sub(r'<section\b[^>]*\bid="draft"[^>]*>.*?</section>', '', content, flags=re.S)
        content = re.sub(r'<div class="empty-state"[^>]*>.*?</div>', '', content, flags=re.S)
        headings = list(re.finditer(r'<h([23])[^>]*\bid="([^"]+)"[^>]*>(.*?)</h\1>', content, re.S))
        intro_end = headings[0].start() if headings else len(content)
        entries.append({'title': title, 'page': title, 'url': path, 'text': plain_text(content[:intro_end])})
        for i, heading in enumerate(headings):
            end = headings[i + 1].start() if i + 1 < len(headings) else len(content)
            anchor = heading[2]
            if path == 'download.html':
                anchor = {'install-the-mac-app': 'app', 'run-from-terminal': 'cli',
                          'install-with-homebrew': 'homebrew'}.get(anchor, anchor)
            entries.append({'title': plain_text(heading[3]), 'page': title,
                            'url': f'{path}#{anchor}', 'text': plain_text(content[heading.end():end])})
    return entries
