# Task #71 Stage 1 — First-install ownership repair

## Purpose and approved scope
Repair the released 0.1.0 first-run regression while preserving data, as explicitly requested on 2026-10-20. The observed default root contained only history; build 8 created it before Session could adopt the root.

## Changes
- CLI initialize establishes local Session ownership and returns setup metadata before reporting construction. setup-info remains read-only.
- Known legacy history-only roots are recognized with same-user regular files, no symlink/hardlink files, bounded schema recognition, retained observer lock and rechecks. Unknown files remain refused. History is not rewritten by recovery.
- Reuse pinned serde_json with upstream licenses rather than extend the manager's integer-only fixture parser. Version 0.1.1 / build 9, same runtime/Sparkle pins.
- Actual Swift store plus actual CLI integration test runs in the normal app build and tests fractional timestamps, consent/note preservation and concurrent-owner refusal.

## Verification
- Rust: 35 tests passed, zero failed/skipped, including new legacy-recovery and refusal cases.
- Portable Python candidate suite: 74 tests passed, zero failures/skips.
- Normal-host app build and native updater/reporting/observer/presentation suites passed. Initial sandbox iconutil failure was resolved using normal host execution, without changing the icon source.
- Cross-language test using installed public 0.1.0 CLI reproduced its unrelated-file refusal, then the fixed CLI preserved exact history bytes and semantic consent/note/date. No network or real account used by this fixture.
- Modified app opened the requester's failed default root and displayed Download and install. This is admission/UI evidence, not completed installation or signed-candidate qualification. No game launched.

## Evidence limits and next stage
Final signed empty/failed installation, update and publication remain mandatory. Earlier clean-account evidence preceded reporting integration and did not cover this changed first-run path; it is not reused as proof. No long gameplay repeat for unchanged runtime.

## Artifact disposition and timing
Outputs are isolated in .build/task71. Unchanged official runtime archive was reacquired because retained task47 location had only receipts; SHA256 eb32a9ef8012216d11348c1af089254f2127f28e2b330cf4f1c700f41967d7b0 matched. Retain through installation tests and release. Existing default-root history was not deleted; initialization creates ownership/cache/private/runtime directories. No before/after byte claim for the live UI reopening (its prelaunch snapshot was not captured); exact preservation evidence is the cross-language fixture. Continuous source-to-human-response timing was not instrumented for this first diagnostic iteration and is unavailable. Later candidate phase timestamps must be recorded separately.

The requester already authorized both validations and 0.1.1 redistribution; continue to that bounded stage, keeping mandatory protected-signing review.
