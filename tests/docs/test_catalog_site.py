# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Public website content, nested paths and publication-boundary regressions."""
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import patch
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import compatibility
import catalog_site as site


class Elements(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.elements = []
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / 'site'
        self.data = json.loads(compatibility.SOURCE.read_text())
        self.files = compatibility.build_site(self.data, self.output)

    def test_all_internal_links_assets_and_fragments_resolve_under_project_prefix(self):
        base = 'https://example.invalid/pear/'
        for name in self.files:
            if not name.endswith('.html'):
                continue
            content = (self.output / name).read_text()
            self.assertRegex(content, r'<title>Pear · [^<]+</title>')
            nodes = Elements(content).elements
            ids = [attrs['id'] for _, attrs in nodes if 'id' in attrs]
            self.assertEqual(len(ids), len(set(ids)), name)
            for _, attrs in nodes:
                for key in ('href', 'src'):
                    if key not in attrs:
                        continue
                    url = urlsplit(urljoin(base + name, attrs[key]))
                    if url.netloc != 'example.invalid':
                        continue
                    self.assertTrue(url.path.startswith('/pear/'), (name, attrs[key]))
                    target = self.output / unquote(url.path.removeprefix('/pear/'))
                    self.assertTrue(target.is_file(), (name, attrs[key]))
                    if url.fragment:
                        target_ids = {a.get('id') for _, a in Elements(target.read_text()).elements}
                        self.assertIn(unquote(url.fragment), target_ids, (name, attrs[key]))

    def test_article_retains_source_text_links_tables_and_figures(self):
        source = (ROOT / 'docs/blog' / f'{site.ARTICLE_SLUG}.html').read_text()
        rendered = site.article_content()
        self.assertEqual(site.plain_text(source), site.plain_text(rendered))
        original = Elements(source).elements
        output = Elements(rendered).elements
        self.assertEqual([a['href'] for t, a in original if t == 'a'],
                         [a['href'] for t, a in output if t == 'a'])
        self.assertEqual(sum(t == 'table' for t, _ in output), 2)
        images = [a for t, a in output if t == 'img']
        self.assertEqual(len(images), 2)
        for attrs in images:
            self.assertGreater(int(attrs['width']), 0)
            self.assertGreater(int(attrs['height']), 0)
            self.assertTrue(attrs['alt'])
            name = Path(attrs['src']).name
            self.assertEqual((self.output / 'blog/images' / name).read_bytes(),
                             (ROOT / 'docs/assets/blog' / name).read_bytes())

    def test_article_active_markup_and_unreviewed_images_are_rejected(self):
        for value in ('<script>alert(1)</script>', '<p onclick="alert(1)">text</p>',
                      '<a href="javascript:alert(1)">x</a>',
                      '<a href="https://user:password@example.com/">x</a>',
                      '<img src="images/../../secret.png" alt="x">',
                      '<iframe src="https://example.com/"></iframe>'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                site.ArticleValidator().feed(value)

    def test_nested_unexpected_files_and_symlinks_are_rejected_before_writing(self):
        sentinel = self.output / 'index.html'
        sentinel.write_text('unchanged sentinel')
        private = self.output / 'blog/private.txt'
        private.write_text('private sentinel')
        with self.assertRaises(ValueError):
            compatibility.build_site(self.data, self.output)
        self.assertEqual(sentinel.read_text(), 'unchanged sentinel')
        self.assertEqual(private.read_text(), 'private sentinel')
        private.unlink()
        image = self.output / 'blog/images/current-runtime.png'
        image.unlink()
        outside = Path(self.temp.name) / 'outside.png'
        outside.write_text('outside sentinel')
        image.symlink_to(outside)
        with self.assertRaises(ValueError):
            compatibility.build_site(self.data, self.output)
        self.assertEqual(outside.read_text(), 'outside sentinel')
        self.assertEqual(sentinel.read_text(), 'unchanged sentinel')

    def test_search_targets_real_sections_and_download_tabs_without_form_states(self):
        entries = json.loads((self.output / 'search-index.json').read_text())
        self.assertTrue(any(row['url'].startswith(site.ARTICLE_PATH + '#') and 'Rosetta' in row['title'] for row in entries))
        self.assertTrue(any(row['url'] == 'download.html#cli' for row in entries))
        self.assertTrue(any('3405340' in row['text'] for row in entries))
        for row in entries:
            parsed = urlsplit(row['url'])
            self.assertNotIn('draft', parsed.fragment)
            self.assertNotIn('no-results', parsed.fragment)
            self.assertNotIn('Prepare GitHub draft', row['text'])
            content = (self.output / parsed.path).read_text()
            if parsed.fragment:
                self.assertIn(parsed.fragment, {a.get('id') for _, a in Elements(content).elements})

    def test_heading_ids_are_unique_and_generated_outline_preserves_hierarchy(self):
        body, outline = site.prepare_content('<h2>A &amp; B</h2><h3>Detail</h3><h2>A &amp; B</h2>', (2, 3))
        self.assertEqual(outline, [(2, 'a-b', 'A & B'), (3, 'detail', 'Detail'), (2, 'a-b-2', 'A & B')])
        self.assertIn('id="a-b-2"', body)

    def test_blog_dates_reading_time_mentions_and_recommendations(self):
        first = site.POSTS[0]
        second = replace(first, slug='second', title='Second article', images=(),
                         published='2026-10-17', topics=('development',))
        third = replace(second, slug='third', title='Third article', topics=('unrelated',))
        source = '<h1>Example</h1><p><em>Subtitle</em></p><p>By Author</p><p>' + 'word ' * 221 + '</p>'
        second_source = source + f'<p><a href="{first.slug}.html#section">Earlier work</a></p>'
        with patch.object(site, 'POSTS', (first, second, third)), patch.object(
                site, 'article_content', side_effect=lambda post: second_source if post == second else source):
            pages = site.blog_pages()
        article = pages[first.path]
        self.assertIn('October 18, 2026', article)
        self.assertIn('2 minutes read', article)
        self.assertIn('id="linked-mentions"', article)
        self.assertIn('id="you-might-also-enjoy"', article)
        self.assertEqual(site.related_posts(first, (first, second, third)), [second])
        self.assertNotIn('id="linked-mentions"', pages[second.path])
        self.assertEqual(site.reading_minutes(''), 1)
        self.assertNotIn('<time', site.publication_label(replace(first, published=None)))

    def test_backlinks_resolve_relative_fragments_without_external_or_self_mentions(self):
        target = site.POSTS[0].path
        sources = {
            'index.html': ('Home', f'<a href="{target}#one">One</a><a href="{target}">Two</a>', 'Intro'),
            'blog/second.html': ('Second', f'<a href="{site.ARTICLE_SLUG}.html">Link</a>', 'Summary'),
            'about.html': ('About', f'<a href="https://example.com/{target}">External</a>', ''),
            target: ('Self', '<a href="#one">Self</a>', ''),
        }
        self.assertEqual([row[0] for row in site.linked_mentions(target, sources)],
                         ['index.html', 'blog/second.html'])
        for href in ('../../private.html', '//example.com/x', '%2e%2e/%2e%2e/private.html'):
            self.assertIsNone(site.internal_target(href, target))
        site.ArticleValidator().feed('<p><a href="../about.html">About</a></p>')
        with self.assertRaises(ValueError):
            site.ArticleValidator().feed('<a href="../../private.html">Private</a>')

    def test_single_post_hides_empty_recommendations_and_uses_real_update_channels(self):
        article = (self.output / site.ARTICLE_PATH).read_text()
        self.assertNotIn('id="you-might-also-enjoy"', article)
        self.assertIn('id="linked-mentions"', article)
        self.assertIn('datetime="2026-10-18"', article)
        for link in ('https://x.com/najukoreanpear', 'https://github.com/postmelee/pear',
                     'https://www.threads.com/@postmelee'):
            self.assertIn(link, (self.output / 'updates.html').read_text())

    def test_blog_navigation_and_updates_destinations(self):
        listing = (self.output / 'blog/index.html').read_text()
        nav = re.search(r'<nav id="sidebar".*?</nav>', listing, re.S)[0]
        self.assertIn('href="#latest"', nav)
        self.assertIn('href="#topics"', nav)
        self.assertIn('href="#writing"', nav)
        self.assertNotIn('id="receive-updates"', listing)
        self.assertNotIn(site.ARTICLE_TITLE, nav)
        article = (self.output / site.ARTICLE_PATH).read_text()
        nav = re.search(r'<nav id="sidebar".*?</nav>', article, re.S)[0]
        self.assertIn('href="#article-title"', nav)
        self.assertIn(site.ARTICLE_TITLE, nav)
        self.assertNotIn('Introduction', nav)
        self.assertNotIn('updates.html', article)
        self.assertNotIn('Receive updates', article)
        self.assertIn('</ul></li><li><a href="#references" data-toc-link>', nav)
        self.assertIn('<li><a href="#linked-mentions" data-toc-link>', nav)
        updates = (self.output / 'updates.html').read_text()
        self.assertIn('https://x.com/meleeisgloom2', updates)
        self.assertIn('href="updates.html" aria-current="page"', updates)

    def test_topics_group_posts_and_article_metadata_hides_categories(self):
        first = site.POSTS[0]
        second = replace(first, slug='second', title='Second', edition='v0.2.0')
        source = '<h1>Example</h1><p>Subtitle</p><p>By Taegyu Lee</p><p>Body</p>'
        with patch.object(site, 'POSTS', (first, second)), patch.object(site, 'article_content', return_value=source):
            pages = site.blog_pages()
        series = pages[site.topic_path(first.series)]
        self.assertIn('2 entries about this topic', series)
        version = pages[site.topic_path(first.edition)]
        self.assertIn('1 entry about this topic', version)
        self.assertNotIn('second.html', version)
        header = re.search(r'<header class="article-header">.*?</header>', pages[first.path], re.S)[0]
        self.assertNotIn(first.series, header)
        self.assertNotIn(first.edition, header)
        self.assertIn('1 minute read · <a href="https://x.com/meleeisgloom2"', header)
        self.assertNotIn('rel="author"', pages['blog/writing.html'])

    def test_references_use_body_links_deduplicate_and_escape(self):
        content = '<a href="https://example.org/a?x=1&amp;y=2"><em>First</em> &amp; label</a><a href="https://example.org/a?x=1&amp;y=2">Again</a><a href="../index.html">Local</a><a href="https://postmelee.github.io/pear/">Home</a><a href="mailto:a@example.org">Email</a><a href="https://example.org/b"></a>'
        result = site.references(content)
        links = [a['href'] for tag, a in Elements(result).elements if tag == 'a']
        self.assertEqual(links, ['https://example.org/a?x=1&y=2', 'https://example.org/b'])
        self.assertIn('First &amp; label', result)
        self.assertEqual(site.references('<p>No external links</p>'), '')
        article = (self.output / site.ARTICLE_PATH).read_text()
        section = re.search(r'<section><h2 id="references">.*?</section>', article, re.S)[0]
        self.assertIn('https://github.com/postmelee/pear/blob/v0.1.0-preview.4/docs/compatibility/README.md', section)
        self.assertNotIn('https://x.com/meleeisgloom2', section)

    def test_rebuild_is_deterministic_and_does_not_publish_article_source(self):
        before = {name: (self.output / name).read_bytes() for name in self.files}
        second = compatibility.build_site(self.data, self.output)
        self.assertEqual(self.files, second)
        self.assertEqual(before, {name: (self.output / name).read_bytes() for name in second})
        self.assertEqual(set(self.files), compatibility.PUBLIC_FILES | {'game-3405340.html'})
        self.assertFalse((self.output / 'docs').exists())


if __name__ == '__main__':
    unittest.main()
