// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
'use strict';

// All components are optional so the same controller works on every page.
(() => {
  const root = document.documentElement;
  const toggle = document.querySelector('.theme-toggle');
  const preference = matchMedia('(prefers-color-scheme: dark)');
  let explicit = false;
  try { explicit = ['light', 'dark'].includes(localStorage.getItem('pear-theme')); } catch { /* Session-only theme. */ }
  function applyTheme(theme) {
    root.dataset.theme = theme;
    toggle?.setAttribute('aria-checked', String(theme === 'dark'));
  }
  function toggleTheme() {
    const theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    explicit = true;
    applyTheme(theme);
    try { localStorage.setItem('pear-theme', theme); } catch { /* Keep the current page usable. */ }
  }
  applyTheme(root.dataset.theme);
  toggle?.addEventListener('click', toggleTheme);
  preference.addEventListener('change', event => { if (!explicit) applyTheme(event.matches ? 'dark' : 'light'); });
  window.addEventListener('storage', event => {
    if (event.key === 'pear-theme') {
      explicit = ['light', 'dark'].includes(event.newValue);
      applyTheme(explicit ? event.newValue : preference.matches ? 'dark' : 'light');
    }
  });

  const menu = document.querySelector('.mobile-menu-toggle');
  const sidebar = document.querySelector('.sidebar');
  function closeMenu() { sidebar?.classList.remove('is-open'); menu?.setAttribute('aria-expanded', 'false'); }
  menu?.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded', String(open));
    sidebar.classList.toggle('is-open', open);
  });
  document.addEventListener('click', event => {
    if (!sidebar?.contains(event.target) && !menu?.contains(event.target)) closeMenu();
  });
  sidebar?.addEventListener('click', event => { if (event.target.closest('a')) closeMenu(); });
  matchMedia('(max-width: 760px)').addEventListener('change', closeMenu);

  const links = [...document.querySelectorAll('[data-toc-link]')];
  const sections = links.map(link => ({ link, heading: document.getElementById(decodeURIComponent(link.hash.slice(1))) })).filter(item => item.heading);
  let scheduled = false;
  function updateOutline() {
    scheduled = false;
    let current = -1;
    sections.forEach(({heading}, index) => { if (heading.getBoundingClientRect().top <= innerHeight * .2) current = index; });
    if (scrollY > 0 && scrollY + innerHeight >= document.documentElement.scrollHeight - 2) current = sections.length - 1;
    sections.forEach(({link}, index) => {
      link.classList.toggle('is-read', index < current);
      if (index === current) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }
  function queueOutline() { if (!scheduled) { scheduled = true; requestAnimationFrame(updateOutline); } }
  window.addEventListener('scroll', queueOutline, {passive: true});
  window.addEventListener('resize', queueOutline);
  window.addEventListener('pageshow', queueOutline);
  window.addEventListener('load', queueOutline);
  updateOutline();
  // Native fragment navigation retains browser history and modifier clicks.
  // CSS handles smooth scrolling and the reduced-motion alternative.
  sidebar?.addEventListener('click', event => {
    const link = event.target.closest('[data-toc-link]');
    if (!link || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const heading = document.getElementById(decodeURIComponent(link.hash.slice(1)));
    if (heading) { heading.setAttribute('tabindex', '-1'); heading.focus({preventScroll: true}); }
  });

  const dialog = document.querySelector('#site-search');
  const input = document.querySelector('#site-search-input');
  const results = document.querySelector('#site-search-results');
  const status = document.querySelector('#site-search-status');
  const siteRoot = new URL(document.body.dataset.root || './', location.href);
  let index = null;
  let loading = null;
  let selected = -1;
  let opener = null;
  let currentResults = [];
  const normalize = value => value.toLocaleLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
  function select(index) {
    selected = index;
    [...results.children].forEach((row, i) => row.setAttribute('aria-selected', String(i === selected)));
    if (selected >= 0 && results.children[selected]) {
      input.setAttribute('aria-activedescendant', results.children[selected].id);
      results.children[selected].scrollIntoView({block: 'nearest'});
    } else input.removeAttribute('aria-activedescendant');
  }
  function safeURL(value) {
    const url = new URL(value, siteRoot);
    return url.origin === siteRoot.origin && url.pathname.startsWith(siteRoot.pathname) ? url.href : null;
  }
  function render() {
    if (!index) return;
    const query = normalize(input.value.trim());
    const terms = query.split(/\s+/).filter(Boolean);
    currentResults = index.map((entry, order) => {
      const title = normalize(entry.title), body = normalize(entry.page + ' ' + entry.text);
      const match = terms.every(term => title.includes(term) || body.includes(term));
      const score = title === query ? 0 : title.startsWith(query) ? 1 : title.includes(query) ? 2 : 3;
      return {entry, order, score, match};
    }).filter(item => terms.length ? item.match : !item.entry.url.includes('#'))
      .sort((a, b) => a.score - b.score || a.order - b.order).slice(0, 20).map(item => item.entry);
    results.replaceChildren();
    for (const [i, entry] of currentResults.entries()) {
      const href = safeURL(entry.url);
      if (!href) continue;
      const row = document.createElement('a');
      row.className = 'search-result'; row.id = `search-result-${i}`; row.href = href;
      row.setAttribute('role', 'option'); row.tabIndex = -1;
      const category = document.createElement('small');
      category.textContent = entry.url.includes('#') ? entry.page :
        entry.url.startsWith('blog/') ? 'Blog' : entry.url.startsWith('game-') ? 'Game' : 'Page';
      const title = document.createElement('strong'); title.textContent = entry.title;
      const snippet = document.createElement('p');
      const offset = terms.length ? Math.max(0, normalize(entry.text).indexOf(terms[0]) - 45) : 0;
      snippet.textContent = (offset ? '…' : '') + entry.text.slice(offset, offset + 150) + (entry.text.length > offset + 150 ? '…' : '');
      row.append(category, title, snippet); results.append(row);
    }
    status.textContent = query ? `${results.children.length} ${results.children.length === 1 ? 'result' : 'results'}${results.children.length ? '' : ' — try a page, game, or topic such as Rosetta.'}` : 'Explore Pear, or search for a game, page or topic.';
    input.setAttribute('aria-expanded', String(results.children.length > 0));
    select(results.children.length ? 0 : -1);
  }
  async function loadIndex() {
    if (index) return;
    if (!loading) {
      status.textContent = 'Loading search…';
      loading = fetch(new URL('search-index.json', siteRoot)).then(response => {
        if (!response.ok) throw new Error('Search unavailable');
        return response.json();
      }).then(data => {
        if (!Array.isArray(data) || !data.every(row => row && ['title', 'page', 'url', 'text'].every(key => typeof row[key] === 'string') && safeURL(row.url))) throw new Error('Invalid search index');
        index = data;
      }).finally(() => { loading = null; });
    }
    await loading;
  }
  async function openSearch() {
    if (!dialog || dialog.open) return;
    closeMenu(); opener = document.activeElement;
    dialog.showModal(); input.focus();
    try { await loadIndex(); render(); }
    catch { status.textContent = 'Search could not load. Close and reopen to retry. You can still browse using the navigation.'; }
  }
  function closeSearch() { dialog.close(); }
  document.querySelectorAll('[data-search-open]').forEach(button => button.addEventListener('click', openSearch));
  document.querySelector('[data-search-close]')?.addEventListener('click', closeSearch);
  dialog?.addEventListener('close', () => { input.setAttribute('aria-expanded', 'false'); opener?.focus(); });
  dialog?.addEventListener('click', event => {
    if (event.target === dialog) {
      const rect = dialog.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) closeSearch();
    }
    if (event.target.closest('.search-result')) closeSearch();
  });
  input?.addEventListener('input', render);
  input?.addEventListener('keydown', event => {
    const count = results.children.length;
    if (['ArrowDown', 'ArrowUp'].includes(event.key) && count) {
      event.preventDefault(); select((selected + (event.key === 'ArrowDown' ? 1 : -1) + count) % count);
    } else if (event.key === 'Enter' && selected >= 0) {
      event.preventDefault(); results.children[selected]?.click();
    }
  });
  const shortcut = document.querySelector('.search-shortcut');
  if (shortcut && !/Mac|iPhone|iPad/.test(navigator.platform)) shortcut.textContent = 'Ctrl K';
  document.addEventListener('keydown', event => {
    if (event.isComposing) return;
    if (event.key === 'Escape' && dialog?.open) { event.preventDefault(); closeSearch(); return; }
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); dialog.open ? closeSearch() : openSearch(); return; }
    if (event.key === 'Escape' && menu?.getAttribute('aria-expanded') === 'true') { closeMenu(); menu.focus(); }
    const editing = event.target.closest('input, textarea, select, [contenteditable="true"]');
    if (!editing && !dialog?.open && !event.metaKey && !event.ctrlKey && !event.altKey && event.key.toLowerCase() === 'd') toggleTheme();
  });
})();
