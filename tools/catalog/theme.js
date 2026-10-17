// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Runs before styles load to prevent a saved dark preference flashing light.
(() => {
  let saved;
  try { saved = localStorage.getItem('pear-theme'); } catch { /* Storage may be disabled. */ }
  document.documentElement.dataset.theme = saved === 'light' || saved === 'dark'
    ? saved : matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
})();
