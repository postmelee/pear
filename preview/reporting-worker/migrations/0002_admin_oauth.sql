-- SPDX-FileCopyrightText: 2026 Pear contributors
-- SPDX-License-Identifier: GPL-3.0-or-later
CREATE TABLE oauth_states(hash TEXT PRIMARY KEY, browser_hash TEXT NOT NULL, verifier TEXT NOT NULL, expires INTEGER NOT NULL);
CREATE TABLE admin_sessions(hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires INTEGER NOT NULL);
CREATE INDEX oauth_expiry ON oauth_states(expires);
CREATE INDEX admin_expiry ON admin_sessions(expires);
