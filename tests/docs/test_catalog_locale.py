# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Locale boundaries: shared routes/assets, stable payloads and protected evidence."""
import sys
from pathlib import Path
import unittest
import json
import re
import tempfile
from dataclasses import replace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import catalog_locale as locale
import catalog_site as site
import compatibility


class LocaleTests(unittest.TestCase):
    def test_only_presentation_is_translated(self):
        page = locale.translate('<html lang="en"><h1>Games</h1><p translate="no">Games &lt;script&gt;</p><input placeholder="Search Pear…"><select><option>Games</option></select><code>Games</code><script>const s = "Games";</script></html>')
        self.assertIn('<h1>게임</h1>', page)
        self.assertIn('<p translate="no">Games &lt;script&gt;</p>', page)
        self.assertIn('<option value="Games">게임</option>', page)
        self.assertIn('<code>Games</code>', page)
        self.assertIn('const s = "Games";', page)
        self.assertIn('placeholder="Pear 검색…"', page)

    def test_nested_locale_routes_and_one_asset_tree(self):
        english = {'index.html': site.shell('Home', '<h1>Home</h1>'),
                   'download.html': site.shell('Download', '<h1>Download</h1>'),
                   'blog/example.html': site.shell('Example', '<h1>Example</h1><a href="../download.html?app=1#cli">Download</a><video src="media/demo.mp4"></video>', root='../')}
        pages = site.publish_pages(english | locale.korean_pages(english))
        korean = pages['ko/blog/example/index.html']
        self.assertIn('lang="ko"', korean)
        self.assertIn('href="../../download/?app=1#cli"', korean)
        self.assertIn('src="../../../blog/media/demo.mp4"', korean)
        self.assertIn('data-root="../../"', korean)
        self.assertIn('src="../../../site.js"', korean)
        self.assertIn('href="../../../blog/example/" lang="en"', korean)
        self.assertIn('hreflang="ko" href="https://postmelee.github.io/pear/ko/blog/example/"', korean)
        self.assertIn('data-redirect="example/"', pages['ko/blog/example.html'])
        self.assertIn('<html lang="en">', pages['blog/example/index.html'])

    def test_article_dates_correction_links_and_bookmarks(self):
        english = site.blog_pages()[site.ARTICLE_PATH]
        korean = site.blog_pages(language='ko')[site.ARTICLE_PATH]
        self.assertIn('datetime="2026-10-18"', english)
        self.assertIn('datetime="2026-10-20"', english)
        self.assertIn('before its release', english)
        self.assertIn('실제 출시 전에', korean)
        self.assertIn('releases/tag/v0.1.0">release notes', english)
        self.assertIn('releases/tag/v0.1.0-preview.4">Preview.4', english)
        headings = lambda value: set(re.findall(r'<h[23][^>]*id="([^"]+)"', value))
        self.assertEqual(headings(english), headings(korean))
        with self.assertRaises(ValueError):
            site.validate_posts((replace(site.POSTS[0], updated='2026-10-17'),))

    def test_missing_article_translation_is_explicit(self):
        with patch.object(Path, 'is_file', return_value=False):
            page = site.blog_pages(language='ko')[site.ARTICLE_PATH]
        self.assertIn('The Korean translation is not available yet', page)
        self.assertIn('lang="en" translate="no"', page)
        localized = locale.korean_pages({site.ARTICLE_PATH: page})['ko/' + site.ARTICLE_PATH]
        self.assertIn('아직 한국어 번역이 없습니다', localized)
        self.assertIn('I wanted to play Megabonk', localized)

    def test_real_render_preserves_evidence_and_scopes_search(self):
        data = json.loads(compatibility.SOURCE.read_text())
        data['records'][0]['summary'] = 'Download'
        data['records'][0]['settings'] = 'Games'
        with tempfile.TemporaryDirectory() as output:
            compatibility.build_site(data, output)
            root = Path(output)
            page = (root / 'ko/game-3405340/index.html').read_text()
            self.assertIn('<p translate="no">Download</p>', page)
            self.assertIn('<dd translate="no">Games</dd>', page)
            search = json.loads((root / 'ko/search-index.json').read_text())
            self.assertTrue(any(row['title'] == '시스템 요구사항' for row in search))
            self.assertTrue(any(row['url'] == 'download/#app' for row in search))
            self.assertFalse(any(row['url'].startswith('ko/') for row in search))
            self.assertEqual((root / 'updates/appcast.xml').read_bytes(), (site.ROOT / 'preview/updates/appcast.xml').read_bytes())

if __name__ == '__main__':
    unittest.main()
