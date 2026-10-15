// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Synthetic names only; these tests do not assert game compatibility.
const test = require('node:test');
const assert = require('node:assert/strict');
const search = require('../../tools/catalog/steam-search.js');
const snapshot = games => ({schema_version: 1, source: 'Steam IStoreService/GetAppList v1', fetched_at: '2026-10-11T00:00:00Z', games});
const games = search.index([{app_id: '10', name: 'Synthetic sequel'}, {app_id: '20', name: 'Synthetic'}, {app_id: '30', name: 'Other synthetic game'}, {app_id: '40', name: 'Café-Quest'}, {app_id: '50', name: '합성 게임'}]);

test('exact name and App ID rank ahead of partial matches', () => {
  assert.equal(search.match(games, 'synthetic')[0].app_id, '20');
  assert.equal(search.match(games, '40')[0].name, 'Café-Quest');
});
test('case, accents, punctuation, Unicode and multiword search', () => {
  assert.equal(search.match(games, 'CAFE quest')[0].app_id, '40');
  assert.equal(search.match(games, 'game other')[0].app_id, '30');
  assert.equal(search.match(games, '합성')[0].app_id, '50');
});
test('same-name games retain separate App IDs', () => {
  const duplicates = search.index([{app_id: '1', name: 'Same title'}, {app_id: '2', name: 'Same title'}]);
  assert.deepEqual(search.match(duplicates, 'same').map(g => g.app_id), ['1', '2']);
});
test('unknown or short queries cannot silently choose a game', () => {
  assert.deepEqual(search.match(games, ''), []);
  assert.deepEqual(search.match(games, 's'), []);
  assert.deepEqual(search.match(games, 'nothing like this'), []);
});
test('large lists bound results and still find exact matches at the end', () => {
  const large = search.index(Array.from({length: 150000}, (_, i) => ({app_id: String(i + 1), name: `Synthetic ${i}`})));
  assert.equal(search.match(large, 'synthetic').length, 8);
  assert.equal(search.match(large, 'synthetic 149999')[0].app_id, '150000');
});
test('malformed snapshots fail; names remain literal text', () => {
  const good = snapshot([{app_id: '10', name: '<img src=x onerror=alert(1)>'}]);
  assert.equal(search.validate(good).games[0].name, good.games[0].name);
  for (const bad of [snapshot([]), snapshot([{app_id: '../x', name: 'Bad'}]), snapshot([{app_id: '10', name: ''}]), snapshot([{app_id: '10', name: 'One'}, {app_id: '10', name: 'Two'}]), {...good, fetched_at: 'bad'}, {...good, source: 'untrusted'}]) assert.throws(() => search.validate(bad));
});
