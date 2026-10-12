# Task #47 Stage 3 preparation: signed distribution candidate

Status: Stage 3 in progress. This is an interim receipt, not stage completion.

The requester approved Stage 3 and the protected GitHub signing deployment.
The candidate source is `f9d95781b5460644d9aba25e2bac68faddbdf98f`.
CI: https://github.com/postmelee/pear/actions/runs/38270025717

## Verified scope

- Portable fixtures: 66 passed, no skips. Hosted ARM64 Rust fixtures: 22 passed.
- Developer ID app, CLI and DMG notarization: Accepted; protected credentials cleaned by CI.
- One-time PEAR_SIGNING_APPROVED_SHA repository variable removed after success.
- Downloaded candidate hashes match the package manifest.
- Local read-only DMG integrity/signature/staple/Gatekeeper checks passed.
- Mounted app has the expected 27-file allowlist, valid seal and staple; image detached.
- No local app, Wine, Steam or game was executed during these checks.
- Exact Pear source archive and runtime/source-kit hashes prepared without copying the runtime.

| Artifact | Bytes | SHA-256 |
|---|---|---|
| Pear-0.1.0-preview.1-macos-arm64.zip | 5299832 | `cee04542bc239a66679f21b60dce31ed81e4e9e8b1a6c50bc65819a5311ba918` |
| pear-preview-0.1.0-preview.1-macos-arm64-cli.zip | 337641 | `c9681ba27afc9d2ecfa304704d1c16f0e4b9aad0f2be780f142fe6d2bbbc4fa1` |
| Pear-0.1.0-preview.1-macos-arm64.dmg | 5414660 | `9422328323ef148dc6d32171f6a75af90eb014dea2dbc03d5f78160815b451f4` |

| Submission | Accepted ID |
|---|---|
| app | `b8a58241-15d7-4c40-a4e5-7a24ae702623` |
| cli | `cc31b416-7cd7-485d-899a-cd08cdd9d8f4` |
| dmg | `e4c3402e-d11d-4173-9d52-52bffbd78df7` |

## User-facing wording

Use the same brief line in release notes and the download page:

> This release uses Wine 11.0 and DXMT 0.80.

The runtime is downloaded separately, so “uses” avoids implying that the small
DMG contains it. Keep minimum build target (Apple Silicon, macOS 26) distinct
from observed runtime hardware/OS (M4 Pro, 24 GB, macOS 26.5.2). Do not turn
24 GB into an unsupported RAM minimum. Full source/patch/component detail
belongs behind the existing component link.

## Public qualification candidate and fresh-user result

The requester explicitly approved qualification publication before final manual
checks. Release `v0.1.0-preview.1` was published on October 13 (Asia/Seoul),
with prerelease=true and latest=false, targeting exact source f9d9578:
https://github.com/postmelee/pear/releases/tag/v0.1.0-preview.1
All nine assets were checked against their expected sizes and SHA-256 digests.
Anonymous HTTPS downloads of the complete DMG, CLI and runtime matched their
hashes. No duplicate large runtime archive was retained.

The requester created a fresh standard macOS account and was instructed to use
Safari delivery, normal DMG installation, initial preparation, official Steam
sign-in and owned Megabonk installation; measure at least twenty active minutes,
check input/audio, save, quit, relaunch, confirm progress and exit normally.
The requester reported completion with no problems. This is owner-reported
completion of that checklist. Exact play duration/timestamps and graphics
settings were not supplied; no instrumented timing, frame-time or performance
claim is established. Browser-delivered CLI execution remains separate.

The test used a fresh account on the same M4 Pro/24 GB/macOS 26.5.2 host, with
system Rosetta and Xcode already installed. It is not a second physical Mac or
clean OS. Existing authenticated state and recovery archives were preserved.
After the response, a read-only process-name check found no Wine, Steam,
Megabonk or PearPreview matches. The advisory holder was explicitly released
and exited successfully; no application was forcibly terminated.

The requester suggested an initial list of required downloads and sizes,
explicit download start and a progress indicator. Inspection confirms the frozen
launcher starts preparation immediately and displays text notifications only.
This is a proposed UX change, not present in the published candidate. Show the
pinned runtime download size (534424618 bytes) separately from installed space;
Steam self-updates and game downloads have variable sizes. Reuse the existing
Swift presentation and Rust installation flow. An implementation would require
a new signed/notarized app candidate and affected first-run/cancel/retry checks;
unchanged runtime evidence stays scoped to the same artifact. Do not replace
published assets silently or label the old app as having the new interface.
The website remains disabled pending final delivery review.

## Retention

Keep .build/task47/stage3/ci-signed-f9d9578 and distribution-f9d9578 through
release review (approximately 22 MiB combined logical package/source bytes).
Existing runtime and source kit were reused in place. Hosted artifacts expire
after fourteen days; preserve their hashes/receipts before expiry. Private state
and older recovery baseline remain protected. No other chat was invoked.

## Approved preview.2 first-run interface

The requester approved a bounded first-run presentation refinement and version
information, deferring full removal. The app now requests Download and install
before fresh setup; read-only setup-info does not create the state folder or
contact the network. Sizes come from the core's pinned artifact metadata. Existing
installations bypass the initial screen and enter normal core verification and
Steam handoff. The optional CLI retains explicit command-driven setup and adds
setup-info/--version. Full removal and automatic repair are not implemented.

Reused the existing Rust/curl/hash/staging/cancellation flow and native AppKit
controls, without adding a dependency. Progress reports received archive bytes;
extraction/preparation are indeterminate. The UI buffers fragmented UTF-8/lines.
Apple's NSProgressIndicator guidance was reviewed on October 13:
https://developer.apple.com/documentation/appkit/nsprogressindicator
A visual check found the original reused indeterminate bar retained its animation;
separate native determinate and busy controls fixed the displayed fraction.

Local verification: Rust 24 tests passed, Swift presentation fixtures passed,
Swift compilation/ad-hoc seal passed, Python 66 checks passed after removing a
stale preview.1 filename assumption from the DMG test. An initial offline Cargo
attempt lacked the locked libc crate; a locked fetch followed by the build passed.
There is an existing unused pear_process_identity warning in the manager crate.

Actual AppKit checks confirmed fresh setup waits, the pre-consent state path
remains absent, the two sizes are visible, About shows preview.2 and component
versions, download byte updates arrive, Cancel returns Retry and Retry restarts.
The second transfer completed/extracted before the next Cancel; no Steam install
or account login occurred, and no Wine/Steam process remained. Disposable test
state was released only after process/marker checks: 3587946998 logical bytes,
3595812864 allocated bytes; measured filesystem free space increased from
5645615104 to 9247416320 bytes (not attributed exclusively on a shared host).
All previous private/recovery inputs remain intact.

A small separate UI-only fixture then showed a determinate 25% bar, cancellation,
and automatic Steam-handoff dispatch for ready=true without starting real Steam.
This is explicitly synthetic presentation evidence. It is excluded from the
package and remains under ignored first-run-ui/ui-fixture until candidate review.
Runtime inventory, download hash checks, isolated staging and existing recovery
failure tests remain in place. Signed preview.2 actual-delivery checks remain
pending; these local ad-hoc/fixture results are not release qualification.
