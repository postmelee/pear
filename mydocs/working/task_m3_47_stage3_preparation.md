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


## October 15 login-window close investigation

The requester rejected publication with the login-close limitation and explicitly
requested a correction first. Release 413098631 was rechecked as draft=true,
prerelease=true at exact d5364dd. Its earlier proposed publication assessment
above is superseded by this instruction; no public preview.2 delivery occurred.

The first failed close remains valid: a CPU-active renderer and Wine services
survived the Steam main process. Subsequent observations on the same immutable
signed runtime are distinct, not a correction of that failure:

- Reopening the unauthenticated prefix and closing its login window did not
  reproduce the renderer orphan. Short-lived Wine services alone were observed.
- The original HTML cache was renamed and retained. After Steam recreated its
  web cache, the requester closed the login window again. The observer completed
  with no surviving exact-prefix helper to sample; an independent process check
  found no Wine/Steam process. No forced cleanup was used for that close.
- A further signed-CLI launch was observed for 200 seconds before sending Steam's
  own -shutdown command. Exact-root observations found no candidates at 10, 30
  and 60 seconds after the request. This is CLI shutdown evidence, not another
  real-window close result. No production patch has been applied.

Ignored evidence is under `.build/task47/stage3/login-exit-fix`: the cache-close
observer, `cold-close-samples.json` (empty), `second-close-observations.json`,
and `delayed-exit.json`. The absence of samples means no target was available;
it is not an empty stack proving the cause. Logs and raw host paths remain private.

The original bootstrap log shows a first-install updater transition from the
bundled 2024 bootstrapper through the win32 client to current win64 Steam build
1791918634. A single additional first-update diagnostic uses a new unauthenticated
prefix with the already verified Steam installer and shares the immutable runtime
without a full runtime copy. Its result is pending at this checkpoint.

Reuse inspection included Wine's existing job-object lifecycle and process
creation support. No job-object patch or host cleanup supervisor is selected:
there is not yet evidence that modifying those mechanisms fixes this failure.
In particular, process-name-only termination and a timer that could interrupt
an authenticated session or game are not acceptable substitutes for ownership.
Existing successful game/save checks and the signed release inputs stay intact.


The first-update comparison subsequently reached a login-window visibility entry
in Steam's own log (not independent visual confirmation). After 200 seconds the
normal Steam shutdown request succeeded. No exact-prefix candidates remained
at 10, 30 or 60 seconds. Thus this test did not reproduce the orphan either and
does not establish that the updater was its cause.

A standalone original synthetic C fixture compiled with MinGW (-Wall -Wextra
-Werror) and ran under the unchanged signed Wine. Atomic job-list assignment,
a nested job child and grandchild exiting on final job-handle close, and survival
of a separately created child all passed. The fixture then cleaned only children
it created through retained process handles. This supports a possible bounded
lifecycle mechanism; it does not test CEF sandbox compatibility or correct Steam
selection, and no such policy is added to the runtime or app.

The final independent process check found no Steam, Wine or fixture process.
The diagnostic advisory lease was explicitly released. Private receipts and
probe sources remain under login-exit-fix; source/binary hashes for the synthetic
fixture are in job-lifecycle-result.json. The directory has 3,073,125,931 logical
bytes and 3,083,018,240 allocated bytes at the retention checkpoint, mostly the
additional Steam prefix. No runtime duplicate was created. Retain the two test
prefixes for the correction's differential checks; after those consumers finish,
keep minimal evidence and release their disposable bytes. Existing authenticated
state, save recovery archives, signed artifacts and other worktrees were untouched.

Current conclusion: intermittent unauthenticated-close failure remains unresolved.
There is no reproducible failing stack or verified production correction yet.
The next correction must establish exact browser/child ownership, respect nested
CEF jobs and preserve games; then revalidate the affected signed candidate.
Do not promote passing comparisons or the synthetic lifecycle probe into a claim
that preview.2's login-window problem is fixed. Publication remains withheld.


## October 15 Stage 3.5: bounded browser-child lifetime candidate

The requester authorized a safe correction, verification and distribution. The
selected candidate adds an opt-in Wine kernelbase policy: an exact configured
browser image may associate same-image renderer/utility children with one
non-inheritable kill-on-close job. Atomic assignment preserves the caller's job
list, including nested CEF sandbox jobs. It excludes Steam, other image paths,
unknown roles and a parent already running as a CEF child. No process-name scan,
host termination timer or sandbox-disable switch is introduced. Wine's original
LGPL notices remain; the additional code has Pear contributors attribution.

A first diagnostic link failed because job creation APIs live in kernel32; using
Wine's existing NtCreateJobObject/NtSetInformationJobObject dependency corrected
that layer violation. Both i386 and x86_64 kernelbase DLLs then built. These are
component-only diagnostics, not a redistributable whole-runtime build. Their
native baseline and signed preview.2 assets remain immutable.

The actual patched DLL passed seven ownership cases in each guest ABI: renderer,
utility, opt-in disabled, mismatched parent path, different child image, CEF-child
parent and unknown role. Positive cases also check that a nested grandchild exits
and a separately created sibling survives; caller-supplied job membership is
checked. The fixture owns retained handles for cleanup. The committed original
fixture is now part of runtime_validate.py and the source-kit allowlist.

In an APFS clone of the unauthenticated Steam prefix, actual Steam build
1791918634 logged the policy on children with both zero and one existing caller
job. The requester confirmed normal login text/QR, then closed the window using
X without login. Three consecutive exact-root observations were empty; an
independent process snapshot also found no Steam/Wine processes. No forced
cleanup was used. This establishes the corrected candidate's observed close
path, not reproduction or a claimed root-cause diagnosis of the original hang.
Sanitized evidence is task_m3_47_login_lifetime.json; raw traces remain private.

The additional first-update comparison prefix had no remaining consumer. Its
logs were archived and byte-verified, account/game absence and no live process
were checked, then only that prefix was removed. Released logical bytes:
3,072,894,385; allocated bytes: 3,082,743,808. Measured filesystem free bytes rose
from 4,528,594,944 to 7,609,548,800; this shared-host delta is recorded separately.
The diagnostic root /private/tmp/pear47-exit-20261015 retains its cloned source,
DLLs, synthetic prefix and no-login Steam clone until the complete-runtime
candidate comparison. Authenticated state and save recovery remain untouched.

A complete reconstruction is prepared for a fresh GitHub macOS runner using
pinned public source inputs, the existing builder and expanded synthetic
validation. It has no signing secrets or release write permission. This avoids
lowering the local full-build storage admission requirement. New runtime
identity, prefix migration, actual game verification and protected signing /
notarization remain required. preview.2 stays draft; no current app pin or
production launch environment has been changed at this checkpoint.

Checks: 31 runtime Python tests passed; 14 actual guest ownership cases passed;
source notice gate and git diff --check passed. This is a Stage 3 continuation
checkpoint, not completion or approval of public distribution.


Follow-up control: the unchanged signed baseline ran the identical i386 fixture.
It failed renderer-owned and utility-owned cleanup as expected while all five
exclusion controls passed. The fixture therefore detects absent containment;
it does not merely pass on either runtime. After exact open-handle absence was
checked, its synthetic-only prefix was released (1,494,487,264 logical bytes;
1,498,288,128 allocated bytes; measured free-space increase 1,500,098,560 bytes).
The executable, source and all outcome logs remain available. The complete CI
runtime will use a fresh synthetic prefix, so this prefix has no remaining
consumer. The task's diagnostic lease was released; no host execution is active.

Complete reconstruction was started from c6a6c4d in GitHub run 38630377016.
The concurrent existing app/CLI candidate run 38630376850 passed its portable
and Apple Silicon checks; its signing job was skipped by the exact-SHA gate.
That app still pins the old runtime and is not the corrected release candidate.


The runtime signing handoff is prepared in preview-runtime-sign.yml. Its required
reviewer and custom branch policy were re-read from GitHub and remain active.
No signing credentials have been loaded by this continuation. Inline Python
blocks and YAML parse, 32 runtime tests pass, and source notices / whitespace
checks pass. The package helpers can record a new explicit identity and reviewed
manifest without rewriting the historical v2 constants; negative digest/name
checks run before output creation. The signing handoff still needs the successful
reconstruction provenance and human approval before execution.


The app/CLI shared launch environment now selects the exact installed CEF browser
path for the opt-in lifetime policy. The existing GPU policy, Wine loader path
and game DLL overrides remain unchanged. All 24 Preview Rust tests, formatting,
incremental source notices and whitespace checks passed. The production runtime
pin remains signed-v2 until the reconstructed/signed candidate is admitted; this
source change alone does not activate the new kernelbase policy on that baseline.

## Complete reconstruction review and signing admission — 2026-10-15

Run 38630377016 (source c6a6c4d412055e62890351b9fd692eb396bd470c) completed
successfully in 46m59s. Native image/load checks, crypto/font checks, valid HTTPS
and wrong-host rejection, both seven-case browser-lifetime suites and owned
synthetic cleanup passed. This remains hosted synthetic runtime evidence, not
new signed-app or real-game qualification.

Reviewed provenance SHA-256:
0027957fbcafed3cdf217567e61c5f0830c6199ed670f40ff66a5cf9a610bd44.
Runtime archive SHA-256 recorded by CI:
89e054ff2631a7f79986bb7516d0fc61778c545cb0a11f322866cea21ca9e07f.
Source archive SHA-256 recorded by CI:
0b23bde973d6c30651a392cc71650349843dd04bffee481e02db590e42ff2c61.
Runtime manifest SHA-256:
088156ef7004e6d0ebdf3494a8917c8e3a2c091b57489912e627f4a511b806dc.
The seven small metadata files were independently hash-checked against provenance.
A bounded range reader retrieved 105,053 bytes instead of downloading/extracting
both large unsigned archives locally. Full archive hashes will be verified in
protected signing before credentials; they are not claimed locally verified yet.

Actual tools: Apple clang 21.0.0, Xcode 26.6 build 17F113, SDK 26.5, GCC 16.2.0
with Homebrew MinGW-w64 14.0.0_3. DEVELOPER_DIR was filtered by the builder;
the receipts, not the workflow's intended Xcode path, define this candidate.
GCC 16.2.0 COPYING.RUNTIME and COPYING3 from gcc-mirror release sources match
the existing 15.2.0 copies byte-for-byte (SHA-256 9d6b43ce4d8de0c878bf16b54d8e7a10d9bd42b75178153e3af6a815bdc90f74
and 8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903).
The new notice names and provenance identify 16.2.0 explicitly; old copies remain.
No executable is changed by this notice refresh. Admission additionally anchors
the original lock at 3f9f87501f3817ba685db9cc422d6a646b588117c9d52ffae72578a18de77da0
and permits only the reviewed notice inventory to differ. Negative tests reject
changed sources, patches, unknown options, wrong original digest and tampered
notices. All 33 runtime Python tests pass.

Required reviewer postmelee and the codex/publish-task47 environment branch
restriction remain active. No signing job has been dispatched at this checkpoint;
no signing credentials were read. Signed runtime admission and local isolated
Steam/game verification remain outstanding. preview.2 remains draft.

Protected runtime signing run 38659029719 was dispatched at exact signing revision
181e2629ac6b11aa6ae575ae4f032ea05d34fd7d; the requester confirmed approval.
YAML and four embedded Python blocks parse, source notice and whitespace checks
pass. Push-triggered reconstruction 38659028866 was cancelled as redundant for
this notice-only repack. App/CLI run 38659029144 passed portable fixtures and the
Apple Silicon build; its still-old-runtime signing job was cancelled before
credentials. Do not treat that app as the new-runtime candidate. A local
read-only check found no Wine/Steam/game processes and the advisory lock available;
recheck when admitting actual host execution. Signing is still in progress.

## Signed runtime admitted for local candidate verification

Protected run 38659029719 completed successfully after human approval. Its
notarization receipt is Accepted (submission 8d008588-a874-4630-b5c0-32fa103eb74a).
Forty-five Mach-O files were signed; the receipt confirms original, non-Mach-O
and executable-text preservation. Only Wine/bin/wine and
Wine/lib/wine/x86_64-unix/wine carry disable-library-validation and unsigned
executable-memory entitlements; the other 43 carry none. Temporary signing
credentials were removed successfully. Artifact 11938217960 retains the runtime,
corresponding source kit and receipts for seven days.

Signed runtime identity: pear-wine11-cw26.3-dxmt0.80-signed-v3;
archive size 542,451,640 bytes; SHA-256
eb32a9ef8012216d11348c1af089254f2127f28e2b330cf4f1c700f41967d7b0.
Corresponding source kit SHA-256:
4577a0d67c82e649194ce85fa932039598243c2d2afcde252c6cf014f5199ec3.
Seven receipt hashes match signing provenance. The runtime payload download is
still in progress at this checkpoint, so local payload verification is pending.

The local app/CLI pin now selects this candidate with no public URL. No release
asset or website download has been enabled. Local Rust tests (24), Swift
presentation fixtures and ad-hoc app signature verification passed. Initially,
locked libc 0.2.186 was absent from the local cache; cargo fetch --locked restored
it and the normal offline build passed. This app is a local development artifact,
not a Developer ID app qualification.

The advisory host lock was acquired; the no-login prefix was copied using APFS
copy-on-write only after confirming no open handles or Steam account record.
The clone has no ready marker. prepare must execute wineboot -u and replace DXMT
before a new-runtime ready marker can exist. The original diagnostic prefix,
authenticated prefix, games and saved-state archives remain unchanged. This is
an isolated test transition; production migration is not claimed implemented.

Local runtime payload verification completed: SHA-256 and 542,451,640-byte size
match the signed candidate manifest. Installed inventory matches signing.json;
all 45 strict codesign checks and exact entitlement comparisons pass locally.
The source kit stays retained in CI and has not been downloaded locally.

An attempted transition of the old diagnostic prefix was rejected as evidence:
prepare completed, but both installed kernelbase.dll hashes still matched old
diagnostic files rather than the reconstructed runtime. Merely calling wineboot
-u or relabeling readiness therefore does not establish this transition. That
quiescent test clone was renamed and retained, not used for the new-runtime UI
claim. A fresh Windows prefix reused only its unauthenticated Steam directory.
Actual prepare completed; both x86_64 and i386 kernelbase hashes now exactly match
the new runtime. Production upgrade behavior remains unresolved and fail-closed.

The local app at d65d713 (ad-hoc app, notarized runtime) was launched into this
fresh no-login environment. Read-only exact-root process observation is active.
The requester was asked to confirm readable login/QR and close Steam without
logging in, then close Pear. No UI/exit success is recorded until that response
and process observations arrive; no forced cleanup is used. Authenticated state
and the prior signed release remain unchanged.

Requester confirmed normal login text/QR and closed both Steam and Pear with X.
A Wine Dock icon was still visible in the 09:38:34 KST screenshot. Exact-root
observation then recorded no owned processes at 09:38:58, 09:39:03 and 09:39:08
KST; an independent current process scan also found no Wine, Steam, PearPreview
or Megabonk processes. No forced cleanup was performed or requested. This real
unauthenticated close attempt passes for the local d65d713 app and notarized
signed-v3 runtime. The Dock screenshot alone was not treated as a live-process
failure. This does not yet qualify the new runtime's game/save behavior, an
existing-prefix upgrade, or the final Developer ID app/CLI/DMG distribution.
Private receipts remain in stage3/signed-runtime-v3. Release the advisory test
lease after the verified process absence; retain the new runtime and both prefix
copies for the remaining comparison and migration investigation.

## Signed-v2 prefix migration and new-runtime game admission (2026-10-15)

The failed diagnostic transition retained PendingFileRenameOperations. Wine's
setupapi deliberately queues loaded builtin replacements; wineboot -r processes
them without force/kill flags. That restart made six x86/x64 core DLLs and all
1,421 installed builtin DLLs checked in the retained copy match signed-v3.

The shared app/CLI core now admits only the reviewed signed-v2 -> signed-v3
upgrade. It validates the old runtime inventory and quiescence, makes a clonefile
copy (no full-copy fallback), runs wineboot -u -r then wineboot -r with natural
server-exit waits, reapplies DXMT and checks installed builtin/core/graphics
bytes. Original-tree metadata is rechecked before a journaled atomic RENAME_SWAP.
The previous prefix remains in private/runtime-upgrade-signed-v3/prefix. An
interrupted post-exchange launch can finish only with matching directory inodes
and byte verification; unknown states fail closed. Cancellation and retries
never kill a game/server or remove the original prefix. An unactivated owned
scratch prefix is disposable only after its server has exited. Additional retry
layout/cancellation guards were added after the first local executable build.

Thirty Rust tests pass, including clone isolation, stale builtin/core/graphics
rejection, external path rejection, save-mutation detection and pre/post-exchange
interruption boundaries. All 68 portable Python fixtures pass without skips.
Swift presentation fixtures and local ad-hoc signature verification pass for the
first migration app. Incremental source notices and governance checks pass.
Final protected CI must build the committed successor with the small retry/UI
metadata and release-URL updates; the running local app is not that final binary.

Actual migration used a private clone of integrated-signing-v2/state; the source
was never launched or modified. The outer clone includes 14,283 files, logical
6,765,474,738 bytes. Measured free space changed from 7,517,900,800 to 7,511,023,616
bytes during cloning; this is a filesystem observation, not exclusive physical
allocation. Preparation took 71.03 seconds and returned success. Ten private
save-related files match the pre-run hashes in the active migrated prefix, its
preserved backup, and the untouched original. The original marker remains
signed-v2; only the test clone is signed-v3.

Local app launch was 00:52:18 UTC, after the frozen initial migration source at
00:49:29 UTC and preparation at 00:50:40–00:51:51 UTC. Steam game handoff completed
at 00:52:34 UTC. Megabonk and UnityCrashHandler64 processes were observed; neither
process creation nor handoff is counted as user-operable gameplay. Requester
confirmation of menu/input/audio and prior progress is pending. Continuous timing
and exact source hashes are retained privately in migration-feedback-timing.json;
the comparable historical baseline is unavailable. Real gameplay duration,
save/relaunch and final signed app qualification remain unperformed for this
candidate until their respective evidence is collected.

The upcoming preview.2 asset URL is pinned in the app/CLI, with the already
verified signed-v3 size/hash. It is a release destination, not a currently working
public download claim. The old public preview.1 and stale preview.2 draft assets
have not been changed. Stage 3 and public distribution remain incomplete.


## Final signed migration candidate and gameplay (2026-10-15)

The requester approved source 1d2a084288b6ab3f2faa1a71d1954cb94157d2dc
for publication and protected CI signing, then approved the required GitHub
environment review. Run 38663035130 completed successfully. The app, CLI and DMG
were accepted by Apple notarization; submission IDs respectively are
0fa7117c-380c-47c8-b650-8bdb228311dd,
cc17c577-dc9b-4101-a80d-69c42d9c9685 and
1fa876c6-d986-408a-b6db-255f932176b1. Downloaded artifacts match the manifest:

| Artifact | Bytes | SHA-256 |
|---|---|---|
| App ZIP | 5336851 | `30de38ce04853791709e3dfd55d0060ff65da161092338ba7df41ab358ec1bc3` |
| CLI ZIP | 356925 | `c1450da9b7cdf2c005d8b74b3da0593141c61fe38d7bd6b784bae0bb9964c56c` |
| DMG | 5455519 | `0936db367777fdb87dd32c4e74a4b492d3f3dba41b6bcdb4a2b947ad189a2acc` |

Local app seal, staple, Gatekeeper and syspolicy_check distribution checks pass;
DMG seal, staple, Gatekeeper and internal CRC checks pass. Standalone CLI bytes
match the app's signed CLI; its explicit codesign notarized requirement and
--version pass. An attempted app-only spctl assessment rejected the standalone
CLI as not an app; the existing package procedure correctly checks CLI
notarization with codesign instead. This was a checker selection correction,
not a signature or notarization change.

The requester confirmed normal menu, manual controls, audio and preserved prior
progress in the migrated signed-v3 environment. After an explicit request for at
least twenty active gameplay minutes, excluding idle/menu time, they confirmed
completion and normal game exit, then explicitly confirmed no audio/control/save
problems. Exact active duration was not supplied; this is requester-confirmed
>=20 minutes, not a process-uptime measurement. The request timestamp is
01:02:09 UTC. Continuous initial source-to-received-manual-input confirmation was
529.98 seconds, including unmeasured human response waiting; exact first manual
input time and a comparable earlier baseline are unavailable.

After the requester closed Steam via its menu and closed Pear, no Wine, Steam,
Megabonk or PearPreview process remained. The final downloaded Developer ID app
was started at 01:22:19 UTC into the preserved migrated test state. Its identical
signed CLI requested the game through official Steam at 01:22:32-34 UTC.
The requester confirmed normal menu, controls, audio and preservation of the
latest gameplay progress, then normally exited game, Steam and Pear. A process
scan again found no matching processes; no force-stop was used. A late game
mapping snapshot was empty after exit and establishes no additional loaded-image
claim. The earlier active-game mapping receipt remains scoped to its own run.
The advisory host lease was released after verifying process absence.

Private receipts are retained under stage3/release-1d2a084 and
stage3/signed-runtime-v3. No authenticated baseline, saved game, old prefix
recovery copy or runtime was removed. The new source kit was also downloaded and
checked: 158 members, eleven pinned source-input archives and the current lock
match. Exact source archive pear-source-1d2a084.tar.gz has 1,657 entries,
10,470,738 bytes and SHA-256
5201a1b20d0adf2e0a53c048cd0386bce4dbbbaa31e94c8e22b6edba2927a9d9.
Retain these approximately 22 MiB app/package/source bytes and the already
retained runtime/source kit through release review. No new runtime copy is needed.

The final signed-app existing-state relaunch and save/exit checks pass. The
previous fresh-standard-account result applies to preview.1; it is not relabeled
as a clean-account delivery test of 1d2a084/signed-v3. Final anonymous delivery
and clean-account first setup remain to be checked for this candidate. Stage 3
is still in progress and the homepage download is not enabled by this receipt.


After the requested login-window correction and game/save verification, the
qualification pre-release v0.1.0-preview.2 was published with prerelease=true and
latest=false. The tag points to exact approved source 1d2a084; seven assets contain
app ZIP, CLI ZIP, DMG, signed-v3 runtime, matching runtime source kit, exact Pear
source archive and SHA256SUMS. All uploaded sizes/digests match the prepared
manifest. The obsolete d5364dd source and binaries were replaced while the
release was still a draft; no published preview.1 asset was changed. The release
body explicitly says final browser delivery and fresh-user installation checks
are pending. The previous instruction to fix login-close before publication has
been met; this is a qualification pre-release, not Stage 3 completion.

The requester cannot switch macOS accounts now. Preserve that remaining final
clean-account delivery check without relabeling old evidence or requiring another
twenty-minute play interval merely for account switching. The published site and
homepage download remain unchanged. A successful anonymous download alone does
not establish ordinary-user installation. Retain all authenticated/recovery state
and the published artifact receipts until this final check can resume. The
completed exact-SHA signing gate was cleared; required-reviewer and branch
protections remain in place.


Anonymous full HTTPS downloads of the published DMG (5,455,519 bytes), CLI
(356,925 bytes) and runtime (542,451,640 bytes) all matched the exact release
SHA-256 values. No credentials were passed; the runtime was streamed into its
hash rather than stored as another local copy. The DMG was mounted read-only:
its 27 app files exactly match the previously verified ZIP app and its
Applications link resolves to /Applications. The seal passed and the volume was
detached without launching another session. The release notes now mark only
final fresh-user installation as pending. Stage 3 remains open; no website
activation or broad compatibility claim follows from this download check.


## Approved Pear naming candidate preview.3 (2026-10-15)

The requester approved Pear as the installed app name, retaining Preview in the
version/channel. The app directory, CFBundleName/CFBundleDisplayName, main window,
About title, error copy and DMG volume become Pear. Build number is 3 and package
version is 0.1.0-preview.3. Bundle identifier org.pear.rosetta-preview, internal
PearPreview executable, pear-preview command and the Pear Preview user-data path
remain unchanged. The runtime pin (including its published preview.2 URL),
source/runtime inputs and migration implementation are byte-identical. Published
preview.2 assets are not overwritten. Updating source and sealed display metadata
requires fresh app/CLI/DMG signing, not a Wine rebuild or another sustained-play run.

Local build passed 30 Rust tests, Swift presentation fixtures, compilation and
ad-hoc seal verification. All 68 portable checks passed without skips. Incremental
source notices and governance pass. Actual built plist names are Pear, retained
identifier is unchanged, CLI reports preview.3 and read-only setup-info admits
the existing migrated state as ready. No Steam/game process was started by these
checks. The existing manager unused-function warning remains unrelated.
The fresh-account requirement remains pending; CI signing and actual final Pear
app presentation/launch will be checked on the new immutable candidate.


## Steam opening feedback (2026-10-15)

The requester approved replacing the misleading post-handoff idle screen with
bounded opening feedback. The app now shows an indeterminate indicator, disables
duplicate opening for thirty seconds, offers retry while delayed, and stops the
observer after two minutes with an unconfirmed message. A matched visible Steam
window changes the heading to "Steam window is open"; no login, library contents
or responsiveness is inferred. Closing Pear/retrying invalidates stale callbacks.

The read-only probe uses CoreGraphics bounds/layer/owner PID and Darwin executable
path/arguments. It admits only the exact current runtime executable, the exact
private prefix and official Steam/CEF executable argument. It requests no screen
recording or Accessibility permission, reads no pixels/titles and logs no process
environment. Failure to obtain metadata remains unknown. Apple's official
CGWindowListCopyWindowInfo documentation and WWDC19 session 701 were reviewed.
The initial live probe failed because Wine rewrites argv, leaving NUL padding
before the environment; the parser correction and a regression fixture cover
that layout. It then detected the owned live Steam window and rejected a different
retained Pear root with that same window present.

Local build, 30 Rust tests, expanded Swift parser/state fixtures, all 68 portable
checks without skips, incremental source notices and governance passed. Actual
AppKit UI observations confirmed opening + spinner + disabled retry, delayed +
enabled retry, and finally detected + no spinner. Timeout is covered synthetically;
a final rebuilt cold-launch observation and protected signed-app validation remain
pending. Tests do not establish readable/login-ready content from window metadata.
The exact runtime pin, migration and Rust launch core remain unchanged. No game
was launched and no new prefix/runtime copy was made. Earlier gameplay/save
results retain their original scope. The unpublished preview.3 candidate must be
replaced only after new source-specific signing; no public asset was changed.

Private build/UI receipts are in stage3/launch-status (under 100 MiB budget).
The first dev launch's continuous source-freeze-to-input baseline was not captured;
its build and manual observation are separate evidence. The fixed-app receipt
starts after build and does not claim a complete build-to-input interval. Preserve
these limitations; capture a fresh continuous interval for the final signed app.


After normal exit and a scan with no Wine/Steam/Pear processes, the corrected
app was launched again against the retained authenticated environment. The probe
observed a matching visible window after 12.25 seconds. AppKit inspection showed
"Steam window is open" and no spinner; the requester confirmed that this switch
was prompt after the library appeared, then normally exited Steam and Pear.
A process scan found no matching runtime/application processes and the owned
host lease was released. This is a process-cold launch with existing user data,
not a new-account installation. The probe interval does not measure readable
library/input readiness; the separate human confirmation establishes that bounded
observation. Receipt: ignored stage3/launch-status/cold-launch.json.

Commit e574ba1 is the new source-specific candidate. Hosted build 38669041530
passed the portable and macOS build jobs; the requester approved its protected
signing job. Exact corresponding Pear source and updated release text are prepared
locally. Signing/notarization and final signed-app checks remain pending at this
checkpoint; preview.3 is still an unpublished draft and preview.2 is unchanged.


## Signed opening-feedback candidate and publication (2026-10-15)

CI 38669041530 completed successfully for exact source e574ba1. App, CLI and
DMG notarization were Accepted (4002ce10-2331-4ca6-ac92-999427cfbe09,
c342fc49-36b8-41dc-8fbc-4cfe297b523d,
99ab2451-0d69-41bb-aa2c-f572481f5ce6). Package hashes, Developer ID team,
notarization requirements, Gatekeeper, syspolicy_check, stapled tickets and DMG
integrity passed locally. The read-only mounted DMG's 27 app files exactly match
the ZIP app; the Applications link is correct. The CLI matches the app's core.
The completed exact-source signing variable was removed; reviewer protection
remains unchanged.

The final signed app was started after confirming all earlier test processes had
exited. The matching Steam window was detected 26.49 seconds after process launch.
AppKit observation confirmed the opening spinner/disabled retry followed by the
window-detected heading/no spinner. The requester confirmed the library and prompt
status transition were normal, then exited Steam and Pear normally. A subsequent
scan found no Wine/Steam/Pear processes; the owned host lease was released. This
is existing-state execution, not a new-account or readable-content inference from
window metadata. Build/signing/preparation precede the recorded execution interval;
no complete source-freeze-to-human-input latency claim is made.

The unpublished preview.3 draft was updated to exact e574ba1 with matching source
and five assets, then published as a qualification pre-release (not latest):
https://github.com/postmelee/pear/releases/tag/v0.1.0-preview.3 . Obsolete naming-only
source/binaries were replaced while still draft; public preview.2 assets remain
unchanged. Full unauthenticated downloads of all five new assets matched their
published sizes and SHA-256. Source archive pear-source-e574ba1.tar.gz contains
1,658 entries, 10,478,219 bytes, SHA-256
70f65ed187d2bc3be80394046bf8dcf2037376f6a5349e755607e82f7a1a30cc.
The unchanged signed-v3 runtime and its corresponding source remain linked from
preview.2. No credentials, game content or saves were published.

Final new-user installation of this candidate remains pending because the
requester cannot currently switch accounts. Earlier clean-user results keep their
original artifact scope. Stage 3 and homepage download activation remain open;
this publication is not broad Mac/game qualification. Retain signed/source archives,
verification receipts and all private authenticated/recovery state. Approximately
30 MiB of new app/package/source output fits the approved 100 MiB budget, with
no additional runtime/prefix copy. Private receipts: stage3/launch-status.


## Final fresh-account confirmation (2026-10-15)

The owner confirmed the final preview.3 installation checklist without problems,
and clarified that all required items were checked before deleting the test
account. Record this as same-Mac fresh standard-user evidence. Account identity,
per-step timestamps and screenshots were not supplied; no second physical Mac
or instrumented timing is inferred. The requester explicitly authorized final
records, real download activation and catalog publication. See the
[Stage 3 report](task_m3_47_stage3.md) for final scope and retention.
