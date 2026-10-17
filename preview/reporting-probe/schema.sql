-- SPDX-FileCopyrightText: 2026 Pear contributors
-- SPDX-License-Identifier: GPL-3.0-or-later
-- Snapshot of the generated synthetic migration; not a production schema.
CREATE TABLE `capability_probes` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`revision` integer NOT NULL,
	`request_id` text NOT NULL,
	`value` integer,
	`deleted` integer NOT NULL,
	`expires` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `probe_limits` (
	`bucket` integer PRIMARY KEY NOT NULL,
	`count` integer NOT NULL
);
