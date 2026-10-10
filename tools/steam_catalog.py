#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fetch public Steam game identities; never publish raw API responses or keys."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

ENDPOINT = 'https://api.steampowered.com/IStoreService/GetAppList/v1/'
SOURCE = 'Steam IStoreService/GetAppList v1'
MAX_BYTES = 32 * 1024 * 1024
MAX_GAMES = 500000
PAGE_SIZE = 10000


class CatalogError(ValueError):
    """Safe diagnostics: never include response text, request headers or URLs."""


def require(condition, message):
    if not condition:
        raise CatalogError(message)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CatalogError('Steam API redirect refused.')


def read_page(key, cursor, *, opener=None, sleep=time.sleep):
    parameters = dict(include_games=True, include_dlc=False, include_software=False,
                      include_videos=False, include_hardware=False,
                      last_appid=cursor, max_results=PAGE_SIZE)
    request = Request(ENDPOINT + '?' + urlencode({'input_json': json.dumps(parameters)}),
                      headers={'x-webapi-key': key, 'Accept': 'application/json',
                               'User-Agent': 'Pear-Steam-Catalog/1'})
    opener = opener or build_opener(NoRedirect())
    for attempt in range(3):
        try:
            with opener.open(request, timeout=30) as response:
                raw = response.read(MAX_BYTES + 1)
            require(len(raw) <= MAX_BYTES, 'Steam page exceeds size limit.')
            try:
                return json.loads(raw)
            except (ValueError, UnicodeError):
                raise CatalogError('Steam returned invalid JSON.') from None
        except HTTPError as error:
            code = error.code
            error.close()
            if code in (429, 500, 502, 503, 504) and attempt < 2:
                sleep(2 ** attempt)
                continue
            raise CatalogError(f'Steam API HTTP {code}; no snapshot written.') from None
        except (URLError, TimeoutError, OSError):
            if attempt < 2:
                sleep(2 ** attempt)
                continue
            raise CatalogError('Steam API connection failed; no snapshot written.') from None
    raise CatalogError('Steam API retry limit reached.')


def valid_id(value):
    return type(value) is int and 0 < value <= 4294967295


def valid_name(value):
    return (isinstance(value, str) and 0 < len(value.strip()) <= 1000
            and not any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in value))


def fetch_catalog(key, *, fetch_page=read_page, now=None):
    require(isinstance(key, str) and bool(re.fullmatch(r'[0-9a-fA-F]{32}', key)),
            'Set a valid STEAM_WEB_API_KEY environment variable; do not pass it as an argument.')
    cursor = 0
    games = []
    for _ in range(100):
        page = fetch_page(key, cursor)
        require(isinstance(page, dict) and isinstance(page.get('response'), dict),
                'Invalid Steam response envelope.')
        response = page['response']
        apps = response.get('apps')
        require(isinstance(apps, list) and len(apps) <= PAGE_SIZE, 'Invalid Steam app page.')
        more = response.get('more_results', False)
        require(type(more) is bool, 'Invalid Steam continuation flag.')
        for app in apps:
            require(isinstance(app, dict) and valid_id(app.get('appid')),
                    'Invalid Steam App ID.')
            require(app['appid'] > cursor, 'Steam pagination repeated or reordered an App ID.')
            require(valid_name(app.get('name')), 'Invalid Steam game name.')
            cursor = app['appid']
            # Explicit field projection: ignore every other API field.
            games.append({'app_id': str(cursor), 'name': app['name'].strip()})
        require(len(games) <= MAX_GAMES, 'Steam catalog exceeds entry limit.')
        if not more:
            require(bool(games), 'Steam returned an empty catalog; keep the previous snapshot.')
            snapshot = {'schema_version': 1, 'source': SOURCE,
                        'fetched_at': now or datetime.now(timezone.utc).isoformat(timespec='seconds'),
                        'games': games}
            return validate_snapshot(snapshot)
        require(bool(apps) and response.get('last_appid') == cursor,
                'Invalid Steam pagination cursor.')
    raise CatalogError('Steam pagination limit reached; no snapshot written.')


def validate_snapshot(data):
    require(isinstance(data, dict) and set(data) == {'schema_version', 'source', 'fetched_at', 'games'},
            'Invalid Steam snapshot fields.')
    require(type(data['schema_version']) is int and data['schema_version'] == 1
            and data['source'] == SOURCE, 'Invalid Steam snapshot source/version.')
    try:
        stamp = datetime.fromisoformat(data['fetched_at'])
        require(stamp.utcoffset() is not None, 'Steam snapshot timestamp needs a timezone.')
    except (TypeError, ValueError):
        raise CatalogError('Invalid Steam snapshot timestamp.') from None
    require(isinstance(data['games'], list) and 0 < len(data['games']) <= MAX_GAMES,
            'Invalid Steam snapshot game count.')
    previous = 0
    for game in data['games']:
        require(isinstance(game, dict) and set(game) == {'app_id', 'name'},
                'Invalid Steam snapshot game fields.')
        app = game['app_id']
        require(isinstance(app, str) and bool(re.fullmatch(r'[1-9][0-9]{0,9}', app))
                and valid_id(int(app)) and int(app) > previous, 'Invalid Steam snapshot App ID order.')
        require(valid_name(game['name']), 'Invalid Steam snapshot game name.')
        previous = int(app)
    return data


def read_snapshot(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_BYTES,
            'Steam snapshot must be a bounded regular file.')
    try:
        return validate_snapshot(json.loads(path.read_text(encoding='utf-8')))
    except (ValueError, UnicodeError) as error:
        if isinstance(error, CatalogError):
            raise
        raise CatalogError('Invalid Steam snapshot JSON.') from None


def write_snapshot(data, path):
    validate_snapshot(data)
    path = Path(path)
    require(not path.is_symlink(), 'Steam snapshot output must not be a symlink.')
    payload = (json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')
    require(len(payload) <= MAX_BYTES, 'Steam snapshot exceeds size limit.')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.steam-catalog-', delete=False) as output:
            temporary = Path(output.name)
            output.write(payload)
        temporary.replace(path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        snapshot = fetch_catalog(os.environ.get('STEAM_WEB_API_KEY', '').strip())
        write_snapshot(snapshot, args.output)
    except (CatalogError, OSError) as error:
        print(str(error) if isinstance(error, CatalogError) else 'Unable to write Steam snapshot.', file=sys.stderr)
        return 1
    print(f"Saved {len(snapshot['games'])} public game identities; fetched {snapshot['fetched_at']}.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
