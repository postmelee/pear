# Task #62 Stage 1 — Update launch policy foundation

Date: 2026-10-18 (Asia/Seoul). Implementation remains incomplete; no new release.
Pinned-version investigation found official Sparkle 2.10.0. Integration/archive
identity and framework licensing review are pending; no framework was embedded.
Reviewed official custom-user-interface and SPUUpdaterDelegate documentation:
https://sparkle-project.org/documentation/custom-user-interfaces/
https://sparkle-project.org/documentation/api-reference/Protocols/SPUUpdaterDelegate.html
Use upstream installation/signature engine and custom presentation, not a new
installer. Disable system profiling independently of report sharing.

Implemented UpdateLaunchPolicy.swift, a deterministic serialized launch gate with
an eight-second check deadline and stale callback suppression. No-update, Later,
network/cancel/failure all release normal Steam continuation once. Homebrew-managed
or active/unknown session state skips installation. A session appearing between
choice and ready-to-install defers installation. Added native Swift checks to the
existing macOS build script; tests passed for all these paths.

This does not establish Sparkle integration, active-session detection, actual
Steam de-duplication, signed update/relaunch or failure recovery on disk. The adapter
must serialize consent/session/installation boundaries and use existing root-scoped
process ownership. New-process relaunch intent needs its own exactly-once evidence.
No private state, running app or runtime changed. Keep small policy test executable
in .build/task62 until integration; disposable afterwards. No game test repeated.

Legacy preview.4 cannot receive a Sparkle update because it contains no updater.
First installation is manual, then an actual signed older updater-enabled candidate
must update to a newer candidate. Both are required before final v0.1.0 delivery.
Homebrew policy is to retain Homebrew ownership, show its upgrade guidance and
avoid replacing its app from Sparkle. No shared/private key is added to source.
