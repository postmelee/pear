// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
'use strict';

// Retain bookmarked tab selections, intake parameters and article fragments.
if (location.pathname.endsWith('.html')) {
  const target = document.querySelector('script[data-redirect]').dataset.redirect;
  const url = new URL(target, location.href);
  url.search = location.search;
  url.hash = location.hash;
  location.replace(url.href);
}
