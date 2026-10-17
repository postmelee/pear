# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic publication boundaries; no game or host qualification."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
spec = importlib.util.spec_from_file_location('pear_compatibility', ROOT / 'tools/compatibility.py')
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(catalog.SOURCE.read_text())
        self.data['records'] = self.data['records'][:1]  # Isolate the historical menu fixture.
        self.row = self.data['records'][0]
        self.games = json.loads(catalog.CATALOG.read_text())
        self.games['github_forms_live'] = False  # Exercise the pre-integration fallback explicitly.

    def test_current_record_retains_unmeasured_and_unperformed_checks(self):
        catalog.validate(self.data)
        rendered = catalog.markdown(self.data)
        self.assertIn('not measured', rendered)
        self.assertIn('audio: not-tested', rendered)
        self.assertIn('Interactive menu', rendered)

    def test_claim_promotions_need_separate_evidence(self):
        for level in ('reproduced', 'qualified'):
            with self.subTest(level=level):
                trial = copy.deepcopy(self.data)
                trial['records'][0]['evidence'] = level
                with self.assertRaises(ValueError):
                    catalog.validate(trial)

    def test_menu_cannot_be_qualified_by_adding_links(self):
        self.row.update(evidence='qualified', reproduction_url='https://github.com/postmelee/pear/issues/12',
                        qualification_url='https://github.com/postmelee/pear/issues/16')
        with self.assertRaises(ValueError):
            catalog.validate(self.data)

    def test_native_qualification_requires_architecture_evidence(self):
        self.row.update(track='rosetta-free-development', evidence='qualified', result='active-gameplay',
                        play_minutes=20, reproduction_url='https://github.com/postmelee/pear/issues/12',
                        qualification_url='https://github.com/postmelee/pear/issues/16',
                        checks={k: 'observed' for k in catalog.CHECKS})
        with self.assertRaises(ValueError):
            catalog.validate(self.data)
        self.row['architecture_evidence_url'] = 'https://github.com/postmelee/pear/issues/10'
        catalog.validate(self.data)  # Structural acceptance only; content requires review.

    def test_unsafe_or_private_evidence_urls_are_rejected(self):
        for value in ('javascript:alert(1)', 'file:///private/prefix',
                      'https://user:secret@github.com/postmelee/pear/issues/47',
                      'https://github.com.evil.test/postmelee/pear/issues/47',
                      'https://github.com/postmelee/pear/issues/47?token=secret'):
            with self.subTest(url=value), self.assertRaises(ValueError):
                catalog.public_url(value)

    def test_html_and_markdown_descriptions_remain_text(self):
        self.row['summary'] = '<script>alert(1)</script> [click](javascript:alert(1))'
        catalog.validate(self.data)
        page = catalog.game_page(catalog.group_games(self.data, self.games)[0])
        self.assertNotIn('<script>', page)
        self.assertIn('&lt;script&gt;', page)
        self.assertIn(r'\[click\]', catalog.markdown(self.data))

    def test_invalid_records_and_unmeasured_gameplay_fail(self):
        for field, value in [('id', '../private'), ('app_id', '123/../x'),
                             ('play_minutes', True), ('play_minutes', -1),
                             ('tested_on', '2026-02-30'), ('track', 'native-confirmed')]:
            with self.subTest(field=field, value=value):
                trial = copy.deepcopy(self.data)
                trial['records'][0][field] = value
                with self.assertRaises(ValueError):
                    catalog.validate(trial)
        self.row['result'] = 'active-gameplay'
        with self.assertRaises(ValueError):
            catalog.validate(self.data)

    def test_duplicate_and_extra_fields_rejected(self):
        self.data['records'].append(copy.deepcopy(self.row))
        with self.assertRaises(ValueError):
            catalog.validate(self.data)
        self.data['records'].pop()
        self.row['private_log'] = 'must not publish arbitrary fields'
        with self.assertRaises(ValueError):
            catalog.validate(self.data)

    def test_site_copies_only_allowlisted_public_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'site'
            files = catalog.build_site(catalog.validate(self.data), output)
            self.assertEqual(set(files), catalog.PUBLIC_FILES | {'game-3405340.html'})
            self.assertEqual(json.loads((output / 'reports.json').read_text()), self.data)
            self.assertEqual((output / 'pear.png').read_bytes(), (ROOT / 'docs/assets/pear.png').read_bytes())
            self.assertIn('href="favicon.png"', (output / 'index.html').read_text())
            (output / 'private.log').write_text('private sentinel')
            with self.assertRaises(ValueError):
                catalog.build_site(self.data, output)
            self.assertEqual((output / 'private.log').read_text(), 'private sentinel')

    def test_site_refuses_symlink_output(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / 'target').mkdir()
            (base / 'link').symlink_to(base / 'target', target_is_directory=True)
            with self.assertRaises(ValueError):
                catalog.build_site(self.data, base / 'link')

    def test_empty_catalog_is_explicit(self):
        empty = catalog.validate({'schema_version': 1, 'records': []})
        self.assertIn('No reviewed observations yet.', catalog.markdown(empty))
        page = catalog.games_page(empty, {'schema_version': 1, 'github_forms_live': False, 'games': []})
        self.assertIn('0 games', page)
        self.assertNotIn('data-game data-name=', page)

    def test_reports_group_by_steam_identity_not_one_card_per_report(self):
        second = copy.deepcopy(self.row)
        second.update(id='megabonk-other-environment', host='Synthetic fixture host', tested_on='2026-10-10')
        self.data['records'].append(second)
        groups = catalog.group_games(self.data, self.games)
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]['records']), 2)
        self.assertEqual(groups[0]['records'][0]['tested_on'], '2026-10-11')
        self.assertEqual(catalog.games_page(self.data, self.games).count('data-game data-name='), 1)

    def test_pass_partial_failed_do_not_grant_qualification(self):
        self.assertEqual(catalog.outcome(self.row), 'partial')
        self.row.update(result='active-gameplay', play_minutes=20,
                        checks={key: 'observed' for key in catalog.CHECKS})
        self.assertEqual(catalog.outcome(self.row), 'pass')
        self.assertEqual(self.row['evidence'], 'reported')
        self.row['checks']['audio'] = 'not-tested'
        self.assertEqual(catalog.outcome(self.row), 'partial')
        self.row['checks']['audio'] = 'failed'
        self.assertEqual(catalog.outcome(self.row), 'failed')
        self.row['result'] = 'regression'
        self.assertEqual(catalog.outcome(self.row), 'failed')

    def test_unknown_votes_are_not_rendered_as_zero_or_borrowed_from_other_posts(self):
        group = catalog.group_games(self.data, self.games)[0]
        self.assertEqual(catalog.demand_link(group), 'request.html?app=3405340')
        self.assertIn('No support request yet.', catalog.game_page(group))
        request = self.games['games'][0]['request']
        request.update(discussion_url='https://github.com/postmelee/pear/discussions/123')
        catalog.validate_catalog(self.games, self.data)
        group = catalog.group_games(self.data, self.games)[0]
        self.assertIn('Vote count unavailable', catalog.game_page(group))
        request.update(upvotes=0, synced_at='2026-10-11')
        catalog.validate_catalog(self.games, self.data)
        group = catalog.group_games(self.data, self.games)[0]
        self.assertIn('0 · Vote on GitHub', catalog.demand_label(group))

    def test_votes_need_request_identity_and_timestamp(self):
        request = self.games['games'][0]['request']
        request['upvotes'] = 10
        with self.assertRaises(ValueError):
            catalog.validate_catalog(self.games, self.data)
        request['discussion_url'] = 'https://github.com/postmelee/pear/discussions/123'
        with self.assertRaises(ValueError):
            catalog.validate_catalog(self.games, self.data)
        request['synced_at'] = '2026-10-11'
        catalog.validate_catalog(self.games, self.data)

    def test_missing_game_identity_and_foreign_artwork_fail(self):
        for field, value in [('app_id', '../3405340'), ('image_url', 'https://example.com/secret.jpg'),
                             ('image_url', 'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/99/image.jpg')]:
            trial = copy.deepcopy(self.games)
            trial['games'][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                catalog.validate_catalog(trial, self.data)
        self.games['games'] = []
        with self.assertRaises(ValueError):
            catalog.validate_catalog(self.games, self.data)

    def test_game_without_reports_can_be_requested_without_claiming_support(self):
        empty = {'schema_version': 1, 'records': []}
        catalog.validate_catalog(self.games, empty)
        group = catalog.group_games(empty, self.games)[0]
        self.assertEqual(group['records'], [])
        self.assertIn('Not tested', catalog.game_card(group))
        self.assertNotIn('Verified configuration</span>', catalog.game_card(group))

    def test_pending_github_form_handoff_is_explicit_and_never_auto_submits(self):
        page = catalog.intake_page(self.games, 'report')
        self.assertIn('GitHub report form is not live yet', page)
        self.assertIn('Nothing is submitted automatically', page)
        self.assertIn('readonly', page)
        self.assertNotIn('method="post"', page)
        self.games['github_forms_live'] = True
        page = catalog.intake_page(self.games, 'report')
        self.assertNotIn('GitHub report form is not live yet', page)
        self.assertIn('Use the GitHub form', page)

    def test_generated_site_has_no_broken_local_navigation(self):
        from html.parser import HTMLParser
        from urllib.parse import urlsplit
        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []
            def handle_starttag(self, tag, attrs):
                for key, value in attrs:
                    if key in ('href', 'src'):
                        self.links.append(value)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'site'
            catalog.build_site(self.data, out, self.games)
            for file in out.glob('*.html'):
                parser = Links()
                parser.feed(file.read_text())
                for target in parser.links:
                    url = urlsplit(target)
                    if not url.scheme and url.path:
                        self.assertTrue((out / url.path).is_file(), (file.name, target))

    def test_metadata_cannot_add_unreviewed_private_fields(self):
        self.games['games'][0]['private_prefix'] = 'sensitive sentinel'
        with self.assertRaises(ValueError):
            catalog.validate_catalog(self.games, self.data)

    def test_common_report_fields_preserve_unperformed_and_failed_checks(self):
        from html.parser import HTMLParser
        class Fields(HTMLParser):
            def __init__(self):
                super().__init__()
                self.key = False
                self.keys = []
            def handle_starttag(self, tag, attrs):
                self.key = tag == 'dt'
            def handle_endtag(self, tag):
                if tag == 'dt':
                    self.key = False
            def handle_data(self, value):
                if self.key:
                    self.keys.append(value)
        original = Fields()
        original.feed(catalog.report_card(self.row))
        failed = copy.deepcopy(self.row)
        failed.update(result='launch-failed', checks={key: 'not-tested' for key in catalog.CHECKS})
        failed['checks']['recovery'] = 'failed'
        changed = Fields()
        page = catalog.report_card(failed)
        changed.feed(page)
        self.assertEqual(original.keys, changed.keys)
        for value in ('Not measured', 'Not tested', 'Failed', 'Not qualified', 'Not recorded'):
            self.assertIn(value, page)
        self.assertIn(self.row['limitations'], catalog.report_card(self.row))

    def test_download_guide_links_exact_public_app_and_cli(self):
        from html.parser import HTMLParser
        class Controls(HTMLParser):
            def __init__(self):
                super().__init__()
                self.disabled = 0
                self.assets = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'button' and 'disabled' in attrs:
                    self.disabled += 1
                if tag == 'a' and attrs.get('href', '').endswith(('.dmg', '.zip')):
                    self.assets.append(attrs['href'])
        controls = Controls()
        controls.feed(catalog.download_page())
        self.assertEqual(controls.disabled, 0)
        self.assertEqual(controls.assets, ['https://github.com/postmelee/pear/releases/download/v0.1.0-preview.3/Pear-0.1.0-preview.3-macos-arm64.dmg', 'https://github.com/postmelee/pear/releases/download/v0.1.0-preview.3/pear-preview-0.1.0-preview.3-macos-arm64-cli.zip'])

    def test_game_name_is_canonical_but_reports_remain_identifiable_by_app(self):
        self.row['game'] = 'A different spelling of the same game'
        group = catalog.group_games(self.data, self.games)[0]
        self.assertEqual(group['name'], 'Megabonk')
        self.assertEqual(len(group['records']), 1)
        self.assertNotIn(self.row['game'], catalog.game_card(group))


if __name__ == '__main__':
    unittest.main()


class SteamSiteBoundaryTests(unittest.TestCase):
    def test_search_metadata_does_not_create_compatibility_cards(self):
        data = json.loads(catalog.SOURCE.read_text())
        snapshot = {'schema_version': 1, 'source': 'Steam IStoreService/GetAppList v1',
                    'fetched_at': '2026-10-11T00:00:00Z',
                    'games': [{'app_id': '123', 'name': 'Synthetic lookup only'}]}
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'site'
            files = catalog.build_site(data, output, steam_catalog=snapshot)
            self.assertIn('steam-games.json', files)
            self.assertNotIn('game-123.html', files)
            self.assertNotIn('Synthetic lookup only', (output / 'index.html').read_text())
            self.assertIn('data-steam-index="steam-games.json"', (output / 'report.html').read_text())
            self.assertEqual(json.loads((output / 'steam-games.json').read_text()), snapshot)
            self.assertEqual(json.loads((output / 'reports.json').read_text()), data)
            catalog.build_site(data, output)
            self.assertFalse((output / 'steam-games.json').exists())
            self.assertIn('data-steam-index=""', (output / 'request.html').read_text())

    def test_snapshot_extra_fields_rejected_before_site_output(self):
        data = json.loads(catalog.SOURCE.read_text())
        snapshot = {'schema_version': 1, 'source': 'Steam IStoreService/GetAppList v1',
                    'fetched_at': '2026-10-11T00:00:00Z', 'private': 'must never publish',
                    'games': [{'app_id': '123', 'name': 'Synthetic'}]}
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'site'
            with self.assertRaises(ValueError):
                catalog.build_site(data, output, steam_catalog=snapshot)
            self.assertFalse(output.exists())
