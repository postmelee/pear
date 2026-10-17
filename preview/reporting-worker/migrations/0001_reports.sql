-- SPDX-FileCopyrightText: 2026 Pear contributors
-- SPDX-License-Identifier: GPL-3.0-or-later
CREATE TABLE reports (
 id TEXT PRIMARY KEY, owner TEXT NOT NULL, revision INTEGER NOT NULL,
 request_id TEXT NOT NULL, payload TEXT, state TEXT NOT NULL DEFAULT 'review',
 approved TEXT, approved_revision INTEGER, published TEXT, published_revision INTEGER,
 updated INTEGER NOT NULL, deleted INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX reports_review ON reports(state,updated);
CREATE TABLE batches (id TEXT PRIMARY KEY, payload TEXT NOT NULL, created INTEGER NOT NULL, published INTEGER);
CREATE TABLE github_sources (
 id TEXT PRIMARY KEY, kind TEXT NOT NULL, url TEXT NOT NULL, title TEXT NOT NULL,
 updated TEXT NOT NULL, report_id TEXT REFERENCES reports(id), needs_review INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE rate_limits (key TEXT PRIMARY KEY, count INTEGER NOT NULL, expires INTEGER NOT NULL);
