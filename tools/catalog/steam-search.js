'use strict';
// Public identity search only. No compatibility inference or Steam API credentials.
const PearSteamSearch = (() => {
  const fold = value => value.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
  function validate(data) {
    if (data?.schema_version !== 1 || data.source !== 'Steam IStoreService/GetAppList v1' ||
        typeof data.fetched_at !== 'string' || !Number.isFinite(Date.parse(data.fetched_at)) ||
        !Array.isArray(data.games) || !data.games.length || data.games.length > 500000) throw new Error('Invalid game list');
    let previous = 0;
    for (const game of data.games) {
      if (!game || typeof game.app_id !== 'string' || !/^[1-9][0-9]{0,9}$/.test(game.app_id) ||
          Number(game.app_id) <= previous || Number(game.app_id) > 4294967295 ||
          typeof game.name !== 'string' || !game.name.trim() || game.name.length > 1000 ||
          /[\u0000-\u001f\u007f-\u009f]/u.test(game.name)) throw new Error('Invalid game identity');
      previous = Number(game.app_id);
    }
    return data;
  }
  function index(games) {
    return games.map(game => ({app_id: game.app_id, name: game.name, search: fold(game.name)}));
  }
  function match(games, query, limit = 8) {
    const text = fold(query);
    if (!text || (text.length < 2 && !/^[0-9]+$/.test(text))) return [];
    const words = text.split(' ');
    const buckets = [[], [], [], []];
    for (const game of games) {
      let rank = game.app_id === text || game.search === text ? 0 :
        game.search.startsWith(text) || game.app_id.startsWith(text) ? 1 :
        game.search.includes(text) ? 2 : words.every(word => game.search.includes(word)) ? 3 : -1;
      if (rank >= 0 && buckets[rank].length < limit) buckets[rank].push(game);
    }
    return buckets.flat().slice(0, limit);
  }
  return {validate, index, match};
})();
if (typeof module !== 'undefined' && module.exports) module.exports = PearSteamSearch;
