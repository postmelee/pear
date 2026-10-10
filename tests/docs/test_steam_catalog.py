"""Synthetic public metadata fixtures; no real key, account or compatibility claims."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('pear_steam_catalog', ROOT / 'tools/steam_catalog.py')
steam = importlib.util.module_from_spec(spec)
spec.loader.exec_module(steam)
KEY = '0' * 32  # Deliberately synthetic; never sent over a network.
STAMP = '2026-10-11T00:00:00+00:00'


def page(apps, **extra):
    return {'response': {'apps': apps, **extra}}


class Opener:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return io.BytesIO(response)


class SteamCatalogTests(unittest.TestCase):
    def snapshot(self):
        return steam.fetch_catalog(KEY, now=STAMP, fetch_page=lambda *_: page([
            {'appid': 10, 'name': 'Synthetic game <one>', 'unknown_private_field': 'discard'},
            {'appid': 20, 'name': '합성 게임 two'}]))

    def test_pagination_projects_only_public_identity_fields(self):
        calls = []
        def fetch(key, cursor):
            calls.append(cursor)
            return (page([{'appid': 10, 'name': 'One', 'extra': 'discard'}],
                         more_results=True, last_appid=10) if cursor == 0 else
                    page([{'appid': 20, 'name': 'Two'}], more_results=False))
        data = steam.fetch_catalog(KEY, fetch_page=fetch, now=STAMP)
        self.assertEqual(calls, [0, 10])
        self.assertEqual(data['games'], [{'app_id': '10', 'name': 'One'}, {'app_id': '20', 'name': 'Two'}])
        self.assertEqual(set(data), {'schema_version', 'source', 'fetched_at', 'games'})
        self.assertNotIn(KEY, json.dumps(data))

    def test_key_is_header_only_and_query_is_games_only(self):
        opener = Opener([b'{"response":{"apps":[]}}'])
        steam.read_page(KEY, 20, opener=opener)
        request, timeout = opener.requests[0]
        self.assertNotIn(KEY, request.full_url)
        self.assertEqual(request.get_header('X-webapi-key'), KEY)
        self.assertEqual(urlsplit(request.full_url).netloc, 'api.steampowered.com')
        parameters = json.loads(parse_qs(urlsplit(request.full_url).query)['input_json'][0])
        self.assertEqual(parameters['last_appid'], 20)
        self.assertTrue(parameters['include_games'])
        self.assertFalse(any(parameters[name] for name in ('include_dlc', 'include_software', 'include_videos', 'include_hardware')))
        self.assertEqual(timeout, 30)

    def test_redirects_cannot_forward_authentication(self):
        with self.assertRaisesRegex(steam.CatalogError, 'redirect refused'):
            steam.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other.example')

    def test_authentication_errors_do_not_leak_response_or_retry(self):
        opener = Opener([HTTPError('https://example.invalid/?key=' + KEY, 403, KEY, {}, io.BytesIO(KEY.encode()))])
        with self.assertRaises(steam.CatalogError) as caught:
            steam.read_page(KEY, 0, opener=opener)
        self.assertNotIn(KEY, str(caught.exception))
        self.assertIn('403', str(caught.exception))
        self.assertEqual(len(opener.requests), 1)

    def test_transient_retry_is_bounded_and_diagnostic_is_sanitized(self):
        waits = []
        opener = Opener([URLError(KEY)] * 3)
        with self.assertRaises(steam.CatalogError) as caught:
            steam.read_page(KEY, 0, opener=opener, sleep=waits.append)
        self.assertNotIn(KEY, str(caught.exception))
        self.assertEqual(waits, [1, 2])
        self.assertEqual(len(opener.requests), 3)
        opener = Opener([HTTPError('', 429, '', {}, io.BytesIO()), b'{"response":{"apps":[]}}'])
        self.assertIn('response', steam.read_page(KEY, 0, opener=opener, sleep=lambda _: None))

    def test_broken_and_oversized_json_is_rejected(self):
        for raw in (b'not json', b'x' * (steam.MAX_BYTES + 1)):
            with self.subTest(size=len(raw)), self.assertRaises(steam.CatalogError):
                steam.read_page(KEY, 0, opener=Opener([raw]))

    def test_invalid_and_nonprogressing_pages_fail(self):
        trials = [{}, page([]), page([], more_results=True, last_appid=0),
                  page([{'appid': 10, 'name': 'One'}, {'appid': 10, 'name': 'Duplicate'}]),
                  page([{'appid': True, 'name': 'Bad'}]), page([{'appid': 4294967296, 'name': 'Bad'}]),
                  page([{'appid': 10, 'name': ''}]), page([{'appid': 10, 'name': 'Bad\nname'}]),
                  page([{'appid': 10, 'name': 'One'}], more_results=True, last_appid=11),
                  page([{'appid': 10, 'name': 'One'}], more_results='true')]
        for trial in trials:
            with self.subTest(trial=trial), self.assertRaises(steam.CatalogError):
                steam.fetch_catalog(KEY, fetch_page=lambda *_: trial)

    def test_invalid_key_never_reaches_network(self):
        for key in ('', 'not-a-key', KEY + '\nextra'):
            with self.subTest(key_length=len(key)), self.assertRaises(steam.CatalogError):
                steam.fetch_catalog(key, fetch_page=lambda *_: self.fail('Unexpected request'))

    def test_snapshot_rejects_extra_fields_and_bad_identities(self):
        for mutation in (lambda d: d.update(key=KEY),
                         lambda d: d['games'][0].update(token=KEY),
                         lambda d: d['games'][0].update(app_id='../x'),
                         lambda d: d.update(fetched_at='2026-10-11'),
                         lambda d: d['games'].append(copy.deepcopy(d['games'][0]))):
            trial = self.snapshot()
            mutation(trial)
            with self.assertRaises(steam.CatalogError):
                steam.validate_snapshot(trial)

    def test_atomic_snapshot_and_previous_data_preserved_on_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'snapshot.json'
            steam.write_snapshot(self.snapshot(), path)
            previous = path.read_bytes()
            trial = self.snapshot()
            trial['games'][0]['unexpected'] = KEY
            with self.assertRaises(steam.CatalogError):
                steam.write_snapshot(trial, path)
            self.assertEqual(path.read_bytes(), previous)
            self.assertEqual(steam.read_snapshot(path), self.snapshot())
            self.assertEqual([p.name for p in path.parent.iterdir()], ['snapshot.json'])
            link = Path(temp) / 'link.json'
            link.symlink_to(path)
            with self.assertRaises(steam.CatalogError):
                steam.write_snapshot(self.snapshot(), link)
