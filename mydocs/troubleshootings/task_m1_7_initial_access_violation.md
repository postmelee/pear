# Task #7 — Initial native pairing access violation

Issue: [#7](https://github.com/postmelee/pear/issues/7).
Last reviewed: October 5, 2026.

## Status

**Corrected for the selected Stage 5 finite route, October 5.** The low-address
Foundation failure class has an independent reproduction and a source-built
ARM64 loader reservation correction. Two final ordinary runs passed all 39
cases, physical deallocation, guest/host termination, current authorization,
raw-log review and owned cleanup. The [Stage 5 report](../working/task_m1_7_stage5.md)
binds the exact final source, loader and graphics receipts. Historical failures
and unsuccessful diagnostics remain preserved; a common cause for every older
fault, arbitrary schedule safety and other OS/runtime combinations are not claimed.

This is the single incident handoff. Preserve the linked observation records
rather than copying the diagnostic chronology into each daily update. Deferring
speculative investigation does not waive required verification or close #7.

## Symptom

The initial final-candidate native pairing run emitted 33 of 39 expected case
rows, ending with `destroy_acquire`, then terminated without the remaining six
rows or the terminal PE record. The recorded guest process exit status was
`0xc0000005` (access violation); the Wine loader returned 5 and the outer command
returned 1. Owned cleanup completed and the unrelated sentinel survived.

`destroy_acquire` is the last recorded observation, not the proven faulting
instruction. The interval after it includes native return/autorelease handling,
the PE transition and window destruction. No fault address or stack was captured.
The loader's numeric exit code does not establish a permissions failure.

## Reproduction Conditions

The original procedure is known; a deterministic trigger is not.

```sh
# Use the exact recorded inputs and a new output name; never overwrite a failure.
python3 -B -m tools.dxmt.deterministic_native \
  --repo "$pear_repo" --constructor-root "$pear_repo/tools/dxmt" \
  --run --runtime "$pear_runtime" --output "$pear_fresh_pairing_output"
```

- Host: Apple M4 Pro, 24 GiB, macOS 26.5.2 (25F84), active graphical session.
- Source implementation: `e6565f6`; later progress commits changed records only.
- Tools: Xcode 26.6 (17F113), SDK 26.5, LLVM-MinGW 20260908 / LLVM 23.1.1;
  use the recorded Python 3.14.4 deterministic adapter environment.
- Exact selected build: `.build/task7/stage5-deterministic8`; native link option
  `-Wl,-objc_stubs_small`, byte-verified retained prerequisites.
- Original signed runtime: `.build/task7/stage5-deterministic-runtime2`.
- Failed output: `.build/task7/stage5-deterministic-pairing2`.
- Original ordinary ARM64 fixture, fresh synthetic prefix, `WINEDEBUG=-all`,
  original runner's pre-device Metal validation environment and ownership bounds.
  No debugger, exception-handler fixture replacement or debugger entitlement.
- Normal macOS protections and the recorded development authorization apply.
  No Steam credentials, game files or saves are required for this fixture.

| Evidence | SHA-256 |
|---|---|
| Selected build receipt | `5eb2a22a1e6132043ba3be3985683573e23f81893f91b9729b55ef00fb57a31d` |
| Signed runtime receipt | `d278123d23993a527e632411eba7e0eaa166251a7746366d67b4a670006ac6dd` |
| Original ordinary ARM64 fixture | `525be80925f96013e705fd4825574d75a93d22165ecf53bb7271d58055a616d3` |
| Failed case receipt | `95fdf884fc593916ea4b4d6537f2eebffb43fca46e3d5b40d96b1115f5bf77d1` |
| Failure receipt | `960e289a0b362c0ce09a42882aa97f917200d8f1965466b552fb202c1c62f951` |

## Cause

Unknown. No evidence distinguishes a Wine, DXMT bridge, fixture, timing, OS or
hardware cause. Environment-dependent timing may expose a software defect;
these explanations are not mutually exclusive. Successful later checks do not
prove a fix or establish that the original environment caused the failure.

## Resolution

No confirmed fix. Speculative investigation was deferred until the unchanged
formal run met the same-boundary recurrence condition. Investigation is now
limited to the new incomplete-execution/exit-path evidence. No speculative
production patch is justified by the current evidence.

A separate debugger ownership/cleanup defect was investigated and its finite
handoff controls passed. That work is not a repair of this access violation;
the earlier failed diagnostic cleanup remains failed in its historical record.

## Recurrence Prevention

Continue the original task's required unchanged-candidate verification and
integration work. Do not add whole rebuilds, repeated executions or debugger
extensions solely because this nonreproduced incident exists. Do not silently
replace a failed required verification with a successful retry. Refer here in
the final report and relevant integration handoff instead of duplicating a
standing warning in each routine update.

The progress-journal interpretation that every historical unexplained failure
must be root-caused before #7 completion is distinct from the original Issue's
component-build and paired-interface criteria. Any completion decision must
state its finite evidence and this unresolved risk explicitly. Actual required
runtime/game correctness gates remain unchanged.

## Reopen Conditions

Resume targeted investigation if the same path or symptom recurs, useful new
fault-address/stack evidence becomes available, or source review identifies a
concrete related defect. A recurrence in required verification or game execution
is a correctness blocker. Preserve the first new failing record and investigate
that evidence rather than continuing a pass-seeking test loop.

## Verification

The original run failed; its outcome is immutable. A later unchanged-fixture
quiet control passed all 39 rows and its case assessment. Logging/observer and
debugger variants also completed, but they are diagnostic evidence and do not
replace the formal original-candidate run and explicit diagnostics review.

Two successful debugger cases had the same layer-deallocation count at row 33
as the original failure. That count alone does not distinguish the failure and
does not rule out a timing/lifetime defect. The first run in the current predeclared formal batch failed, and the second
ordinary run was cancelled. No completion or general stability claim follows.

## New Formal Failure on October 4, 2026

The unchanged candidate passed 163 fresh admission commands, then emitted 33
matching status/facts rows through `destroy_acquire`. OS loader exit was zero,
but the loader-role guest/process exit events, PE terminal and last six rows
were absent. The verifier correctly refused `pair_guest_exit_missing`. Owned
cleanup completed, the sentinel survived, all 20 raw-stream hashes checked,
and all 2,788 signed bundle inventory entries remained unchanged. Native case
time was 6,382 ms; the complete failed operation including admission was
1,115,783 ms. The normal post-execution full provenance replay was not reached.

The failed output is `.build/task7/stage5-final-pairing1`. Its case receipt is
`25fc223ab323916fe18b88082921ea36d99e5c334591039c4903c2a9a448e7cd`;
the failure receipt is
`81596053d30f70759b3a022a03add5fb3baf86f38de377923a31893855beeb7b`.
A loader-only nine-second system-log query found no confirmed cause, and no
matching Wine/Pear crash report was found in the checked user report directory.
Neither absence establishes that no exception occurred.

One narrow diagnostic using the already authorized debugger copy captured an
`exit_process` stop with `NtTerminateProcess` as its caller and exit argument
zero. That diagnostic completed all 39 rows with balanced physical lifetimes,
acknowledged debugger detach, complete Wine/debugger cleanup and surviving
sentinel. It observed normal completion, not the failed original-candidate exit.
The ordinary verifier correctly rejects its changed fixture/signature route
with `pair_launch_changed`. No bad-access or causally useful failing stack was
captured; do not start additional identical attempts to obtain one.

A narrow source review confirmed that `willRemoveSubview` clears the cached
Metal view and that lease release retains the binding until its last lease is
removed. That reading does not prove arbitrary lifetime safety or identify the
failure. No production fix was applied. The next useful discriminator would
separate ordinary Wine window teardown from Metal attachment teardown under
explicitly controlled conditions; further work must target that evidence gap.
A same observation boundary does not by itself prove a shared cause with the
original access violation; preserve their different exit signatures.

## Network and Lid-Closure Evidence Review on October 4, 2026

The requester reported losing internet connectivity and then closing the lid,
with no recalled time. The supplied screenshot shows Codex name-resolution and
reconnection errors. It establishes a communication problem in the app, not a
fault location or interruption of the native Wine case.

Read-only `pmset -g log` completed successfully. In local KST time, the failed
native case ran approximately 14:36:45–14:36:52. The retained power log records
display-on at 14:05:20, display-off at 14:43:57 and display-on at 14:58:56; no
sleep, wake or display transition was found during the case. The test wrapper's
idle-system-sleep and idle-display-sleep assertions were released at 14:36:53,
after the recorded case interval. The later display-off event cannot explain
an earlier failure. This does not identify the physical lid-close time, prove
complete logging of every environmental change or explain the original
historical access violation.

The finite pairing fixture performs local window/Metal operations, without a
Steam login or download. Pear's control channel and Wine's server connection
use `AF_UNIX` local IPC. The case receipt records `exited`, no stream error and
completed owned cleanup; it does not record a supervisor interruption. There
is therefore no observed direct causal link from the internet outage to this
failure. The outage's exact time remains unknown.

Source review identified separate, unconfirmed zero-exit paths: Wine can call
`abort_thread(0)` after local server-reply EOF/EPIPE or through its ARM64 SIGQUIT
handler, and the last thread can reach `_exit(0)` through `abort_process`.
These paths need not emit the normal `NtTerminateProcess` guest-exit event.
They are candidate discriminators, not observed events in the failed run;
local IPC closure is not the same as loss of internet connectivity. The owned
cleanup's recorded server signal follows the loader's observed exit and does
not establish that it caused that exit.

Raw power logs remain private. The sanitized observations include their hash
and the private review receipt hash. No production change, rebuild, extra
native run, network-setting change or power-setting change was performed.
The required verification remains failed and its root cause remains unknown.

## Separate Window and Metal Teardown Controls

On October 4, two distinct PE-side boundary-marker diagnostics completed once
each against the unchanged signed candidate: a Win32 window sequence bypassing
pairing calls, then the full pairing sequence. The first produced zero native
pairing rows as intended; the second produced all 39 expected rows. Both
recorded return from WM_DESTROY, WM_NCDESTROY and DestroyWindow, terminal primary
and cleanup errors zero, cleanup flags 7 and normal guest/process exit events.
Owned cleanup and unrelated-sentinel survival passed. All captured nonfixture
lines were reviewed: each case had three known fresh-prefix working-directory
fallback warnings and six API/six GPU validation notices attributable to its
source-registered processes, with no unclassified line or API error. No shader
workload qualification follows. An initial review helper considered only direct
children and refused descendant notices; using the existing registered process
identities resolved that review error without changing any raw evidence.

This reused the original signed runtime without a debugger, exception handler,
Wine rebuild or re-signing. Bundle inventory and current signature/identity/
profile checks passed before and after; this was limited diagnostic admission,
not the full qualification replay. The unchanged verifier correctly refused
both changed fixtures with `pair_launch_changed`. Private evidence is retained
under `.build/task7/stage5-teardown-controls1` (approximately 2.17 GiB).

The observed window paths completed under these instrumented conditions. The
markers can change scheduling, and neither diagnostic repairs the original
failure or demonstrates general race freedom. No concrete production correction
was found. Preserve #7's failed required gate and these bounded discriminators;
do not repeat them solely to collect more passes. Independent approved #5 FEX
memory/lifetime work can proceed while this #7 gate remains open.

## Independent Exit-Path Review in the Dedicated Session

On October 4, the dedicated #7 session independently verified the failed formal
case digest, all 20 captured stream digests/lengths/EOF states and all 39 captured
producer digests. The loader still has 33 rows and no guest/process exit event.
Its exit was already recorded in the pre-cleanup snapshot; the only recorded
supervisor signal was server SIGINT 1,062.885291 ms after that snapshot. This
rules out that recorded cleanup signal as the initiating event, but does not
account for signals or IPC actions internal to Wine or from external actors.

The selected build-8 Wine source exposes an earlier observation gap:

- `dlls/ntdll/unix/thread.c:1497` decrements `nb_threads` in `abort_thread`.
  Only the last thread reaches `abort_process`; other threads close their local
  request/reply/wait descriptors and call `pthread_exit` through its wrapper.
  The prior exit diagnostic's four breakpoints do not stop at this earlier path.
- `dlls/ntdll/unix/server.c:361` handles a zero-cookie server wakeup by calling
  `abort_thread(reply.signaled)`. This is an additional discriminator alongside
  reply EOF/request EPIPE and ARM64 `quit_handler`, not an observed failed event.
- `server/thread.c:1569` can send that wakeup or SIGQUIT and clean up an individual
  thread while the server process itself remains alive. Server survival therefore
  cannot exclude per-thread IPC teardown. A server-side kill may itself be a
  consequence, so its existence would not alone identify the originating defect.
- The ordinary `NtTerminateProcess` event is emitted only after the server call
  returns (`dlls/ntdll/unix/process.c:975`). Its absence does not prove that the
  function was never entered. `get_unix_exit_code` prevents a nonzero status with
  a zero low byte from becoming zero; status truncation alone is not a supported
  explanation for the observed OS exit zero through this helper.

These are source findings, not a failing stack or a production defect. Existing
normal teardown diagnostics cannot distinguish these paths in the failed run.
The implementation plan contains a pending one-case first-thread-exit capture
proposal. No new native execution, rebuild, signing change or deletion occurred.

## Approved First-Thread Capture Result

The single approved follow-up on October 4 resolved `abort_thread` and
`quit_handler` in the loaded diagnostic ntdll before release. It completed all
39 native rows and the zero-error PE terminal. The first selected stop was
`exit_process` from `NtTerminateProcess` with argument zero; no first-thread
abort, SIGQUIT or bad access was captured. The result again describes normal
completion, not the failed ordinary candidate. It neither confirms nor excludes
the source-only thread/IPC hypotheses.

Acknowledged detach, complete Wine/debugger cleanup, sentinel survival and
before/after original/debugger inventory and current authorization checks passed.
Independent row/terminal/lifetime and log review passed within this diagnostic
scope; the unchanged ordinary verifier correctly refused `pair_launch_changed`.
No new fixture compilation, runtime rebuild or signing occurred. The one-case
batch is exhausted and will not be repeated to obtain a desired outcome.

Case receipt SHA-256:
`5071ace00467c872ea8a00ee240882489cdd352b09efa0fdb778a3bdfd93a611`.
Private review SHA-256:
`c6f1dbdb8c7cf7ab31c9b01830afa7db270f89d94367f11c9251dcd8c837f701`.
Evidence remains under `.build/task7/stage5-lldb2/wine-first-thread1` with its
captured controller and separate review producer. No causal failing stack or
production fix exists; the required formal verification remains failed.

## Exit-Only Diagnostic Result

On October 5, one original-PE case ran without debugger, rendezvous, delay or
new entitlement, using an isolated source-matched ntdll with fixed-size exit
records. Its original link and four affected objects reproduced byte-for-byte
before instrumentation. All 39 rows, physical lifetime, terminal, guest/process
exit, cleanup and sentinel checks completed. Original and diagnostic inventory,
current signature, certificate and profile authorization passed before/after.

The fixture loader recorded two NtTerminateProcess entries and exit_process,
all status zero. Two killed-thread replies and abort_thread entries belonged to
an owned descendant. No SIGQUIT, IPC EOF/EPIPE or fault-handler record appeared.
All 20 streams were reviewed; no unclassified diagnostic or API error appeared.
These observations describe this normal case and do not exclude those paths
from the historical failure. The ordinary assessor refused the changed ntdll
with unbound_loaded_image; diagnostic success does not qualify the candidate.

The single-case budget is exhausted. No failure reproduced, no causal correction
was established, and the required ordinary verification remains failed. Retained
preparation failures do not count as Wine runs. Private evidence is under
.build/task7/stage5-exit-reasons3. Case SHA-256:
`dd7e39ab2891fbb9e60a767d66e656e97a9ac668d9011affdf6f4a1b75299b5e`.
Review SHA-256:
`08adf041ea4c29586efb91ab87292eac7870e8a1f56bbd7eb9fca83a9558849d`.

## System-Thread Exception Identified

Further server-only diagnostics reproduced the same 33-row boundary twice with
unchanged client ntdll, PE and graphics images. The server received a system
thread's terminate_process request with STATUS_ACCESS_VIOLATION and killed the
fixture guest thread; the observed loader OS exit remained zero. With err+seh,
Wine also reported the access violation in a system thread. The silent zero exit
therefore does not imply successful fixture completion.

A third reproduction with live sampling captured the failed process's image map.
The exception address lies at offset 0xbca0 in libswiftCore.dylib, UUID
7669D858-D332-36C7-9C6C-4564FFBEA8D2. Local symbolization against that same UUID
resolves _swift_release_dealloc + 48. The call graph was empty because the
process exited before stack samples were collected. The caller and invalid
object are still unknown; this does not establish a Pear, Wine or Apple defect.
Raw addresses from a different process cannot be reused without its image slide.

Case receipts, respectively:

- 48efc971aee815b4190f663126346006fa36da18d00c516fd4407cba7b4dd0e6
- 25634ec0d00940d77414ed871e46542d4700ea9cde75a2d94c99a0b820947637
- 15c2ec41b6bf5ea7a8e5cf3e3f9864d378652df421bc2d47dc459a276420da31

The private roots are stage5-server-exit1/execution1, execution2 and
stage5-live-sample1 under .build/task7. Current inventory/signature/profile
admission, all captured streams and owned cleanup/sentinel checks passed.
Diagnostic images remain outside ordinary qualification. Post-fault server-hold
variants, a fixed three-case batch, a combined live/held sample and the embedded
hold-server case did not reproduce the exception. Their normal completion does
not erase the failures or clear the formal gate. The implementation plan records
the continued bounded investigation and prefix archival/restoration requirements.

## Evidence Retention

Retain the original case/failure receipts, raw captured streams referenced by
those receipts, source/producer identities, exact input/build/signing identities
and the procedure above. Keep required original inputs or verified restorable
copies for active consumers. Public records contain sanitized outcomes and
hashes, not raw private diagnostics, signing profiles or account data.

Incident preservation does not require every large diagnostic build or prefix
to remain forever. Only reproducible duplicates unreferenced by active checks,
other tasks or retained replay evidence may become cleanup candidates. A GitHub
hash or document is not a backup of its referenced bytes. Review dependency and
restore requirements before any deletion; this incident record authorizes none.

## References

- [Implementation plan](../plans/task_m1_7_impl.md)
- [Sanitized Stage 5 observations](../working/task_m1_7_stage5_reconstruction_observations.json)
- [DXMT build and pairing guide](../../docs/development/dxmt-build.md)


## Captured failing stack, October 5

The server-only hold case reproduced the 33-row termination with unchanged
client ntdll, PE and graphics images. PEAR_EXIT_CAPTURE_RELEASE was supplied only
to the diagnostic server; earlier hold controls also changed the loader's
environment. Do not treat their successful completion as a correction.

The captured main-thread chain is AppKit window layout -> SwiftUICore image
value/environment comparison -> Foundation Locale.== -> outlined destroy of
LocalePreferences -> swift_cvw_destroyImpl -> Swift reference-count release ->
Wine signal gateway -> system-thread termination. The guest thread is waiting
for OnMainThread while executing NtUserDestroyWindow and macdrv_WindowPosChanged.
This narrows the failing path but does not identify the corrupt object or prove
an OS/framework defect. Apple documents automatic main-thread deallocation of
NSResponder descendants since macOS 10.15, so an off-main final release alone
is not sufficient grounds for a speculative window-deallocation patch.

Private case: .build/task7/stage5-server-only-hold1.
Case SHA-256: 06c1fdfc974250fb9140025c82d32fa525e57d26d947e78c3dfbff3429cce2fc.
Sample SHA-256: 1cacb166ab5894a372ea48607e2bd16207ab00a10d819d2afbe76734175714a6.
The sample has 92 observations of the blocked failing stack. Current admission,
20 stream integrity checks, cleanup and sentinel survival passed. This remains
a changed-server diagnostic, not final-candidate qualification.


## Independent low-address Foundation reproduction, October 5

The captured allocation history now identifies the failed pointer as a freed
Swift array allocated during Foundation locale prewarming. The later fatal
release refers to the same address with no intervening allocation. A minimal
Foundation-only executable, using the same user locale and Wine-like low-address
link layout, fails its first Locale equality comparison without Wine, Metal,
AppKit or guest execution. With identical source and 4KB execution, moving the
native allocation boundary above 4GB completes 100 comparisons and exits zero.
Swift's Darwin ARM64 ABI reserves pointer representations below 4GB as extra
inhabitants. This identifies a reproducible native-heap layout incompatibility
in the captured path; it does not prove a common cause for every historical fault.

An ASLR-preserving zero-fill reservation candidate also passes that minimal
reproduction. The private Wine loader candidate still awaits actual ordinary
pairing and source-bound integration. No failure has been waived and Stage 5
remains incomplete. Allocation-history and paired-control hashes and failed
layout candidates are retained in the implementation plan; raw memory and user
locale diagnostics remain private.


## Final correction and disposition

The final patch retains Wine's existing zero-fill reservation mechanism, adapted
to ARM64's shared-cache layout and Swift heap-pointer boundary. It preserves PIE
and low guest mappings; startup fails if reservation remapping fails. The
original x86_64 reservation path remains separate. The unchanged original runner,
PE and environment passed twice on the final source-bound candidate without a
debugger, diagnostic ntdll, server hold or altered locale. This clears #7's finite
required pairing gate. See the final reconstruction observations for both run
and review hashes. Reopen investigation for an actual recurrence or newly changed
integration inputs; do not discard the original failure evidence.
