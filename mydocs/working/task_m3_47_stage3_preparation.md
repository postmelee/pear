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

## October 15 resumed signed preview.2 checks

The requester resumed the network-paused verification. Frozen preview.2 source
is `d5364ddc9a674cf91df287b2c152468b28e49d44`. Protected CI run
https://github.com/postmelee/pear/actions/runs/38282662453 completed successfully.
App, CLI and DMG notarization were Accepted; local package checks recorded in
`ci-signed-d5364dd/local-package-assessment.json` passed. The final app seal was
checked again before this run. No signed artifact or published preview.1 was changed.

No prior Pear, Wine or Steam process or advisory holder remained at resumption.
The old receipt's unreleased flag is historical, not live ownership. A fresh
OS advisory lock was acquired without invoking another chat. Available filesystem
space was approximately 16 GiB. The isolated retry environment may use up to
4 GiB for runtime and Steam setup; it is retained through candidate review.
Existing authenticated state and recovery archives are preserved separately.

The actual signed app displayed the first-run consent and pinned download sizes.
Download progress reached 255.5 MB of 534.4 MB; Cancel returned Setup paused and
enabled Retry. Retry restarted the download, reached 492.8 MB and transitioned
to Windows environment preparation. Steam visibility and installed-state launch
are still pending at this checkpoint. No additional gameplay claim is made.

Preparation subsequently completed and the signed app displayed Open Steam again.
The official updater requested its current manifest from Valve. This establishes
preparation/handoff only; the requester has been asked to confirm the login UI.
All three signed package SHA-256 values were rechecked and matched SHA256SUMS.
The protected CI app/CLI/DMG acceptance IDs are respectively
`f58d9187-4112-47d0-af4c-0e6061df3e00`,
`db3386f6-7ee5-4724-a50c-3732a6628f1b` and
`2cd9579c-4193-4e4c-b183-c4f011e9a7b0`.

The requester then confirmed that the updated Steam login screen displayed its
text and QR normally. No login was requested for this disposable environment.
The signed preview.2 cancel/retry-to-visible-login check therefore passed on
the recorded host. Existing-installation automatic launch remains the next check.

Closing the unauthenticated login window exited Steam's main process but left
a CPU-active steamwebhelper and Wine services. Open-file inspection bound the
helper to this isolated test root. The exact runtime's wineserver -k, scoped by
that root's WINEPREFIX, terminated the four remaining test lifetimes; an independent
process check confirmed all absent. This is a failed login-window cleanup
observation, not a clean exit. No authenticated prefix was targeted.

The signed app was then opened against the preserved integrated-signing-v2/state.
Read-only setup-info reported runtime_present, steam_present and ready=true.
Without clicking any download/setup button, the actual app reached Open Steam
again and dispatched Steam. User confirmation of existing login/library visibility
and normal Steam-menu exit is pending.

The requester confirmed preserved login and a normal library, then selected
Steam > Exit. A process-name check found no Steam or Wine processes; only Pear
remained. Pear was closed through its window control, and a second process check
found none of the trial applications. The advisory holder was explicitly released
and exited successfully. Existing-state automatic launch and normal menu exit
passed; closing the unauthenticated login window remains a separate known issue.

Release assessment: the latter issue affects background resource cleanup, with
no observed data loss in the unauthenticated isolated test. Normal authenticated
Steam-menu exit passed. This does not invalidate download recovery or existing
login reuse, but must be disclosed rather than reported as universal clean exit.
A preview.2 qualification release draft can retain that limitation while final
browser delivery remains pending. No new runtime build or repeat twenty-minute
game session is justified solely by this presentation change.

Preview.2 draft release 413098631 is prepared at exact source d5364dd, with
prerelease=true and draft=true. Five uploaded assets (DMG, app ZIP, CLI ZIP, exact
Pear source archive and SHA256SUMS) match local sizes and GitHub SHA-256 digests.
The body links the unchanged preview.1 runtime and corresponding source kit,
records component versions, host requirements, tested scope and the login-window
cleanup limitation. No website activation or public preview.2 publication occurred.
The prior sequence exception explicitly named preview.1; obtain confirmation
for the same qualification-publication sequence for preview.2 before public
browser-download verification. Documentation checks: 94 passed; governance
37 documents/358 targets passed; git diff --check passed.
