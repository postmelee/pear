# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Locale boundaries: shared routes/assets, stable payloads and protected evidence."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import catalog_locale as locale
import catalog_site as site


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

if __name__ == '__main__':
    unittest.main()
