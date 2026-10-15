// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
'use strict';

// Compatibility content is reviewed repository data; Steam identities are public metadata. No API token or write API.
for (const image of document.querySelectorAll('.game-art')) {
  const fallback = () => { image.hidden = true; };
  image.addEventListener('error', fallback);
  if (image.complete && !image.naturalWidth) fallback();
}

const search = document.querySelector('#search');
if (search) {
  const list = document.querySelector('.game-list');
  const cards = Array.from(document.querySelectorAll('[data-game]'));
  const result = document.querySelector('#result-filter');
  const track = document.querySelector('#track-filter');
  const sort = document.querySelector('#sort');
  let currentTab = 'all';
  const rows = new Map(cards.map(card => [card, JSON.parse(card.dataset.records)]));
  const labels = {'launch-failed': 'Launch failed', 'launched-unusable': 'Launched, unusable', 'menu-interactive': 'Interactive menu', 'active-gameplay': 'Active gameplay', regression: 'Regression'};
  const noun = count => count === 1 ? 'report' : 'reports';
  const selectedRows = card => rows.get(card).filter(row => track.value === 'all' || row.track === track.value);
  const recent = card => selectedRows(card).reduce((latest, row) => row.date > latest ? row.date : latest, '');
  function update() {
    const query = search.value.trim().toLocaleLowerCase();
    let shown = 0;
    const ordered = [...cards].sort((a, b) => {
      let comparison = 0;
      if (sort.value === 'recent') comparison = recent(b).localeCompare(recent(a));
      if (sort.value === 'votes') comparison = Number(b.dataset.votes) - Number(a.dataset.votes);
      if (sort.value === 'reports') comparison = selectedRows(b).length - selectedRows(a).length;
      return comparison || a.dataset.name.localeCompare(b.dataset.name);
    });
    for (const card of ordered) {
      const reports = selectedRows(card);
      const qualifies = reports.some(row => row.qualified);
      const hasResult = result.value === 'all' || (result.value === 'qualified' && qualifies) || (result.value === 'untested' && rows.get(card).length === 0) || reports.some(row => row.outcome === result.value);
      const hasTrack = track.value === 'all' || reports.length > 0;
      const hasTab = currentTab === 'all' || (currentTab === 'reported' && reports.length > 0) || (currentTab === 'requests' && card.dataset.request === 'yes');
      const matches = !query || card.dataset.name.toLocaleLowerCase().includes(query) || card.dataset.app.includes(query);
      card.hidden = !(hasResult && hasTrack && hasTab && matches);
      if (!card.hidden) shown += 1;
      for (const count of card.querySelectorAll('[data-count]')) count.textContent = reports.filter(row => row.outcome === count.dataset.count).length;
      card.querySelector('[data-report-total]').textContent = `${reports.length} ${noun(reports.length)}`;
      card.querySelector('[data-latest]').textContent = reports.length ? `Last tested ${recent(card)}` : 'No reports yet';
      const stage = card.querySelector('[data-stage]');
      const latest = reports[0];
      if (stage) {
        stage.textContent = qualifies ? 'Verified configuration' : latest ? labels[latest.result] : 'Not tested';
        stage.className = `badge ${qualifies ? 'pass' : latest?.outcome || ''}`;
      }
      const runtime = card.querySelector('[data-runtime]');
      if (runtime) {
        runtime.hidden = !latest;
        runtime.textContent = latest?.track === 'rosetta-free-development' ? 'Rosetta-free development' : 'Rosetta Preview';
      }
      list.append(card);
    }
    document.querySelector('#result-count').textContent = `${shown} ${shown === 1 ? 'game' : 'games'}`;
    document.querySelector('#no-results').hidden = shown !== 0;
    const noRequests = currentTab === 'requests' && !cards.some(card => card.dataset.request === 'yes');
    document.querySelector('#empty-heading').textContent = noRequests ? 'No requests yet' : 'No games found';
    document.querySelector('#empty-copy').textContent = noRequests ? 'Be the first to request a game on GitHub.' : 'Try a different search or filter, or request a game.';
    for (const button of document.querySelectorAll('[data-tab]')) button.setAttribute('aria-pressed', String(button.dataset.tab === currentTab));
  }
  for (const button of document.querySelectorAll('[data-tab]')) button.addEventListener('click', () => { currentTab = button.dataset.tab; update(); });
  for (const field of [search, result, track, sort]) field.addEventListener(field === search ? 'input' : 'change', update);
  document.querySelector('#reset-filters').addEventListener('click', () => {
    search.value = ''; result.value = 'all'; track.value = 'all'; sort.value = 'recent'; currentTab = 'all'; update(); search.focus();
  });
  update();
}

const reportTrack = document.querySelector('#report-track');
if (reportTrack) {
  const result = document.querySelector('#report-result');
  const cards = Array.from(document.querySelectorAll('[data-report]'));
  const section = document.querySelector('#reports').parentElement;
  function filterReports() {
    let visible = 0;
    for (const card of cards) {
      card.hidden = !((reportTrack.value === 'all' || card.dataset.track === reportTrack.value) && (result.value === 'all' || card.dataset.outcome === result.value));
      if (!card.hidden) visible += 1;
    }
    for (const count of section.querySelectorAll('[data-count]')) count.textContent = cards.filter(card => !card.hidden && card.dataset.outcome === count.dataset.count).length;
    document.querySelector('#no-reports').hidden = visible !== 0;
  }
  reportTrack.addEventListener('change', filterReports);
  result.addEventListener('change', filterReports);
}

// Normalize identity before rendering a name or generating a GitHub draft.
function steamAppId(value) {
  let id = value.trim();
  if (!/^[0-9]{1,10}$/.test(id)) {
    try {
      const url = new URL(id);
      if (url.protocol !== 'https:' || url.hostname !== 'store.steampowered.com' || url.username || url.password || url.port) return null;
      const match = url.pathname.match(/^\/app\/([0-9]{1,10})(?:\/[^\r\n]*)?$/);
      if (!match) return null;
      id = match[1];
    } catch { return null; }
  }
  const number = Number(id);
  return Number.isSafeInteger(number) && number > 0 && number <= 4294967295 ? String(number) : null;
}

const form = document.querySelector('#intake');
if (form) {
  const gameName = document.querySelector('#game-name');
  const appID = document.querySelector('#app-id');
  const identity = document.querySelector('#steam-identity');
  const picker = document.querySelector('.game-picker');
  const identityStatus = document.querySelector('#identity-status');
  const steamLink = document.querySelector('#steam-game-link');
  const searchInput = document.querySelector('#steam-search');
  const results = document.querySelector('#steam-results');
  const searchStatus = document.querySelector('#steam-search-status');
  const retry = document.querySelector('#retry-steam-search');
  const reviewed = JSON.parse(picker.dataset.games);
  let games = new Map(reviewed.map(game => [game.app_id, game]));
  let searchIndex = PearSteamSearch.index(reviewed);
  let loaded = false;
  let loading = null;
  let failed = false;
  let snapshotDate = '';
  let matches = [];
  let active = -1;
  let typingTimer;
  const area = document.querySelector('#draft-body');
  const title = document.querySelector('#draft-title');
  const status = document.querySelector('#copy-status');
  const minutes = document.querySelector('#duration');
  const result = document.querySelector('#result');
  function invalidateDraft() { document.querySelector('#draft').hidden = true; status.textContent = ''; }
  function resolveGame(syncSearch = true) {
    const id = steamAppId(identity.value);
    const known = games.get(id);
    appID.value = id || '';
    gameName.value = known?.name || '';
    gameName.placeholder = id ? 'Name not available in this list' : 'Filled from the selected Steam App ID';
    if (syncSearch) searchInput.value = known?.name || '';
    identity.setCustomValidity(id ? '' : 'Choose a search result, or enter a Steam store link or numeric App ID.');
    steamLink.hidden = !id;
    if (id) steamLink.href = `https://store.steampowered.com/app/${id}/`;
    else steamLink.removeAttribute('href');
    identityStatus.textContent = !identity.value ? 'Choose a search result, or paste its Steam store link.' : !id ? 'Enter a Steam store link or a valid numeric App ID.' : known ? `Steam App ${id} · ${loaded ? 'Steam game identity' : 'Name from Pear’s reviewed catalog'}.` : `Steam App ${id} · You can submit by ID. The name will be checked before publication.`;
    invalidateDraft();
  }
  function closeResults() {
    results.hidden = true;
    searchInput.setAttribute('aria-expanded', 'false');
    searchInput.removeAttribute('aria-activedescendant');
    active = -1;
  }
  function activate(index) {
    active = index;
    Array.from(results.children).forEach((option, i) => option.setAttribute('aria-selected', String(i === active)));
    if (active >= 0) {
      const option = results.children[active];
      searchInput.setAttribute('aria-activedescendant', option.id);
      option.scrollIntoView({block: 'nearest'});
    } else searchInput.removeAttribute('aria-activedescendant');
  }
  function choose(game) {
    clearTimeout(typingTimer);
    identity.value = game.app_id;
    resolveGame();
    closeResults();
    searchStatus.textContent = `${game.name} selected · Steam App ${game.app_id}`;
  }
  function showResults() {
    const query = searchInput.value.trim();
    matches = query ? PearSteamSearch.match(searchIndex, query) : reviewed.slice(0, 8);
    results.replaceChildren();
    active = -1;
    searchInput.removeAttribute('aria-activedescendant');
    for (const [i, game] of matches.entries()) {
      const item = document.createElement('li');
      item.id = `steam-result-${i}`;
      item.setAttribute('role', 'option');
      item.setAttribute('aria-selected', 'false');
      const name = document.createElement('span');
      name.textContent = game.name;
      const detail = document.createElement('small');
      detail.textContent = `Steam App ${game.app_id}${reviewed.some(row => row.app_id === game.app_id) ? ' · In Pear’s catalog' : ''}`;
      item.append(name, detail);
      item.addEventListener('pointerdown', event => event.preventDefault());
      item.addEventListener('click', () => choose(game));
      results.append(item);
    }
    results.hidden = !matches.length;
    searchInput.setAttribute('aria-expanded', String(matches.length > 0));
    const state = loaded ? `Steam list updated ${snapshotDate}.` : loading ? 'Loading Steam game list…' : failed ? 'Steam list unavailable. Search Pear games or paste a Steam link.' : 'Steam search is being prepared. Search Pear games or paste a Steam link.';
    searchStatus.textContent = `${query && !matches.length ? 'No matches. Try another name or paste a Steam link. ' : query ? `${matches.length === 8 ? 'Up to 8' : matches.length} suggestions. ` : ''}${state}`;
  }
  async function loadGames() {
    if (loaded || loading || !picker.dataset.steamIndex) return loading;
    loading = (async () => {
      retry.hidden = true;
      failed = false;
      searchInput.setAttribute('aria-busy', 'true');
      searchStatus.textContent = 'Loading Steam game list…';
      try {
        const response = await fetch(picker.dataset.steamIndex, {credentials: 'omit', signal: AbortSignal.timeout(12000)});
        if (!response.ok) throw new Error('Game list unavailable');
        if (Number(response.headers.get('content-length')) > 32 * 1024 * 1024) throw new Error('Game list too large');
        const raw = await response.text();
        if (raw.length > 32 * 1024 * 1024) throw new Error('Game list too large');
        const data = PearSteamSearch.validate(JSON.parse(raw));
        games = new Map([...reviewed, ...data.games].map(game => [game.app_id, game]));
        searchIndex = PearSteamSearch.index([...games.values()]);
        snapshotDate = new Intl.DateTimeFormat('en', {year: 'numeric', month: 'short', day: 'numeric'}).format(new Date(data.fetched_at));
        loaded = true;
        // Resolve the current identity, never the value captured before the fetch.
        if (identity.value) resolveGame();
      } catch {
        failed = true;
        retry.hidden = false;
      } finally {
        loading = null;
        searchInput.setAttribute('aria-busy', 'false');
        if (document.activeElement === searchInput) showResults();
        else searchStatus.textContent = loaded ? `Steam list updated ${snapshotDate}.` : 'Steam list unavailable. Search Pear games or paste a Steam link.';
      }
    })();
    return loading;
  }
  searchInput.addEventListener('focus', () => { if (!failed) loadGames(); showResults(); });
  searchInput.addEventListener('input', () => {
    clearTimeout(typingTimer);
    // Editing a selected name must not leave an unrelated ID in the draft.
    identity.value = '';
    resolveGame(false);
    closeResults();
    typingTimer = setTimeout(showResults, 120);
    if (!failed) loadGames();
  });
  searchInput.addEventListener('keydown', event => {
    if (event.key === 'Escape' || event.key === 'Tab') { clearTimeout(typingTimer); closeResults(); return; }
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      clearTimeout(typingTimer);
      if (results.hidden) showResults();
      if (matches.length) activate((active + (event.key === 'ArrowDown' ? 1 : active < 0 ? 0 : -1) + matches.length) % matches.length);
    }
    if (event.key === 'Enter' && !results.hidden) {
      event.preventDefault();
      if (active >= 0) choose(matches[active]);
    }
  });
  searchInput.addEventListener('blur', () => { clearTimeout(typingTimer); closeResults(); });
  retry.addEventListener('click', () => { failed = false; searchInput.focus(); loadGames(); });
  function validateDuration() {
    if (minutes) minutes.setCustomValidity(result.value === 'Active gameplay' && !(Number(minutes.value) > 0) ? 'Enter the active gameplay minutes you measured.' : '');
  }
  identity.addEventListener('input', () => { closeResults(); resolveGame(); if (steamAppId(identity.value) && !failed) loadGames(); });
  const app = new URLSearchParams(location.search).get('app');
  if (app) identity.value = app;
  resolveGame();
  if (app) loadGames();
  if (minutes) {
    minutes.addEventListener('input', validateDuration);
    result.addEventListener('change', validateDuration);
  }
  form.addEventListener('submit', event => {
    event.preventDefault();
    resolveGame();
    validateDuration();
    if (!form.reportValidity()) return;
    const data = new FormData(form);
    const get = key => String(data.get(key) || '').trim();
    const report = form.dataset.kind === 'report';
    const name = get('game') || `Steam App ${get('app')}`;
    title.value = `${report ? '[Game report]' : '[Game request]'} ${name}${get('game') ? ` (${get('app')})` : ''}`;
    const game = `## Game\n${name}\nSteam App ID: ${get('app')}\nhttps://store.steampowered.com/app/${get('app')}/`;
    const checks = ['input', 'audio', 'save_reload', 'recovery'].map(key => `${({'input':'Input','audio':'Audio','save_reload':'Save / reload','recovery':'Recovery'})[key]}: ${get(key)}`).join('\n');
    area.value = report ? `${game}\n\n## Test date\n${get('date')}\n\n## Runtime path\n${get('track')}\n\n## Mac and macOS\n${get('environment')}\n\n## Versions\n${get('versions')}\n\n## Furthest result\n${get('result')}\n\n## Active play minutes\n${get('minutes') || 'Not measured'}\n\n## Test checks\n${checks}\n\n## Game settings\n${get('settings') || 'Not recorded'}\n\n## Steps and observations\n${get('steps')}\n\nI used a legitimately owned game and removed private data. This is a community observation, not Pear qualification.` : `${game}\n\n## Requested support\n${get('reason')}\n\nI checked existing requests and removed private data. This request expresses interest; it is not a compatibility report.`;
    document.querySelector('#draft').hidden = false;
    status.textContent = 'Draft ready. Copy it and continue on GitHub.';
    title.focus();
  });
  form.addEventListener('input', invalidateDraft);
  form.addEventListener('change', invalidateDraft);
  async function copy(field, label) {
    try {
      await navigator.clipboard.writeText(field.value);
      status.textContent = `${label} copied. Paste it into GitHub.`;
    } catch {
      field.focus(); field.select();
      status.textContent = 'Select and copy the text manually, then paste it into GitHub.';
    }
  }
  document.querySelector('#copy-title').addEventListener('click', () => copy(title, 'Title'));
  document.querySelector('#copy-body').addEventListener('click', () => copy(area, 'Body'));
}

for (const button of document.querySelectorAll('.copy-command')) {
  button.addEventListener('click', async () => {
    const code = document.getElementById(button.dataset.copy);
    const status = document.querySelector('#command-status');
    try {
      await navigator.clipboard.writeText(code.textContent);
      status.textContent = 'Command copied. Run it from the extracted CLI folder.';
    } catch {
      status.textContent = 'Copy the displayed command manually.';
    }
  });
}

// Anchors remain ordinary in-page navigation if JavaScript is unavailable.
const downloadMethods = document.querySelector('.download-methods');
if (downloadMethods) {
  const tabs = Array.from(downloadMethods.querySelectorAll('[data-method]'));
  const panels = Array.from(document.querySelectorAll('[data-download-panel]'));
  downloadMethods.setAttribute('role', 'tablist');
  for (const tab of tabs) {
    tab.setAttribute('role', 'tab');
    tab.setAttribute('aria-controls', tab.dataset.method);
  }
  for (const panel of panels) {
    panel.setAttribute('role', 'tabpanel');
    panel.tabIndex = 0;
  }
  function selectMethod(method, focus = false, updateHash = false) {
    const selected = tabs.find(tab => tab.dataset.method === method) || tabs[0];
    for (const tab of tabs) {
      const active = tab === selected;
      tab.setAttribute('aria-selected', String(active));
      tab.tabIndex = active ? 0 : -1;
    }
    for (const panel of panels) panel.hidden = panel.id !== selected.dataset.method;
    if (updateHash) history.replaceState(null, '', `#${selected.dataset.method}`);
    if (focus) selected.focus();
    const status = document.querySelector('#command-status');
    if (status) status.textContent = '';
  }
  for (const [index, tab] of tabs.entries()) {
    tab.addEventListener('click', event => {
      event.preventDefault();
      selectMethod(tab.dataset.method, false, true);
    });
    tab.addEventListener('keydown', event => {
      const target = event.key === 'ArrowRight' ? (index + 1) % tabs.length :
        event.key === 'ArrowLeft' ? (index + tabs.length - 1) % tabs.length :
        event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : -1;
      if (target >= 0) {
        event.preventDefault();
        selectMethod(tabs[target].dataset.method, true, true);
      } else if (event.key === ' ') {
        event.preventDefault();
        selectMethod(tab.dataset.method, false, true);
      }
    });
  }
  selectMethod(location.hash.slice(1));
  window.addEventListener('hashchange', () => selectMethod(location.hash.slice(1)));
}
