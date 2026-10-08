# Task #5 Integrated Stage 3/4 Checkpoint

Date: October 7, 2026. Status: first x64 arithmetic and NT API roundtrip passed; 62 finite EC lifecycle checks passed; full Stage 3 acceptance remains open.
Authority: [current implementation plan](../plans/task_m1_5_impl.md).
Neither Stage 3 nor Stage 4 is complete. No GitHub publication or Issue closure occurred.

## Changes

The active implementation plan was reduced from 2,831 lines to 170 lines.
The previous body and decisions remain in the frozen troubleshooting history;
current memory invariants now live in the separate task design. The active plan
owns the next decision, not a growing chronological experiment log.

An independent Wine integration patch series extends the existing Wine11 owner
without rewriting its historical native evidence or the 23-patch #4 baseline:

- Validate native ARM64, ARM64EC and pure guest x64 image roles from actual PE/CHPE metadata.
- Select the ARM64X x64 view in NX staging using Wine dynamic-relocation semantics;
  retain native ARM64 selection for helper processes and check changed directories.
- Publish pure guest images as native NX while retaining their Windows logical
  execution flags; register immutable EC code ranges in Wine's actual bitmap.
- Bind and pin the translator Wine selected before ProcessInit. The private PE
  bridge verifies caller module identity; a filename or environment role flag
  is insufficient. This is paired-runtime admission, not isolation from hostile
  code already inside the process. Final packaging must bind the recorded FEX bytes.
- Connect the JIT owner EC callback to checked Wine views, actual bitmap backing
  and bit observations. Publication still requires RX observation; retirement
  stays behind the existing owner drain/pin rules. Initial runtime publication ran;
  the complete EC safety/lifetime matrix remains unverified.
- Export the owner bridge for ARM64EC as well as ARM64. Reuse FEX's existing ntdll
  CHPE redirection table to resolve the raw native bridge instead of branching
  directly to an x64 fast-forward export stub.

Upstream Wine C and FEX C++/assembly, notices, source pins and contribution policy
are retained. Wine changes are in `runtime/fex/patches/integration/series.json`;
the FEX supplement is independently recorded in `fex-series.json` there.
No signing protections, entitlements or system settings were changed.

The first actual runs identified and repaired three integration boundaries:

- Choose the first main image from the server-validated PE machine while
  `main_image_info` is still empty; an x64 executable must not default to ARM64.
- Build the initial interval snapshot before any guest thread exists without
  trying to invalidate nonexistent translated blocks. Seed the native-NX guest
  return byte in that snapshot. Existing runtime invalidation guards remain.
- Connect `NotifyMapViewOfSection` to the real lifetime/owner invalidation batch
  before taking source locks, then update the upstream interval/image trackers.
  Finish publication/abort outside source locks and preserve actual errors.

Bounded initialization checkpoints use Wine's existing output path. Wine's
module trace distinguishes publication, EC registration and server mapping;
these diagnostics do not change permissions or turn refusals into success.

## Verified execution result

Two original x64 Windows PEs **exited with the expected value 42** through the
actual ARM64EC FEX translator in the signed ARM64 Wine pair:

| Fixture | Observed result | Scope |
|---|---|---|
| `tests/fex/first_dispatch.S` | Computes 6 × 7, then NtTerminateProcess(42); exit42 | Real guest integer dispatch and native termination |
| `tests/fex/ec_roundtrip.S` | Two successful NtQueryPerformanceCounter calls; positive frequency, exact RSP, RBX/R12/R15 and low 64 bits of XMM6/XMM15 preserved; exit42 | Representative guest/native API roundtrip, not complete ABI conformance |

Both passed current authorization/signature checks before and after execution,
owned-process cleanup without an observation gap, and unrelated sentinel survival.
Recorded host translation checks reported ARM64 and translation value/error 0;
each loader's 348-image initial snapshot was ARM64. All 16,437 image events across
the recorded processes were ARM64 (events include repeated snapshots, not unique
libraries). Each run contained 41 host translation observations; the bootstrap
helper separately reported native execution. Full late-loaded image coverage is
still unqualified and belongs to the broader observation integration.

The isolated signed bundles contain 40 ARM64 Mach-O images with checked dependency
closures. Guest PE execution, ARM64EC image selection and native host identity
are different observations and are not inferred from a native launcher alone.

The raw supervisor receipts deliberately retain `guest_execution_qualified:false`
and `stage3_complete:false`. A separate focused assessment establishes the two
fixture results without promoting broader runtime/game/distribution support.
Fresh-prefix setup also attempted unavailable `syswow64/rundll32.exe` and recorded
`c0000135`; this auxiliary failure remains explicit. It did not prevent either
x64 fixture, but these runs do not qualify WoW64 or the complete Steam helper flow.

## Repaired execution boundaries

- Actual EC entry/fill/return now acquire/release the existing global dispatcher
  lease while preserving guest registers, flags and exact SP. The owner still
  requires all managed executors to drain before writes or retirement.
- The original MIT FEX context merge is restored behind actual source identity.
- FEX lookup backing exposed a recoverable ordinary RW data fault. The retained
  upstream overcommit mechanism now checks query status, allocation type/state,
  interval/protection bounds and commit success before resuming the native context.
  Other exception and suspend routes remain explicitly unsupported.
- The guest syscall path transfers nonlocally through Wine rather than the usual
  return gate. It now releases its exact lease before that transfer; the return
  path obtains a new checked lease. This fixed the observed second-entry refusal.
- Wine native-context observations ruled out the earlier suspected resume-mode
  mismatch: the actual NtContinue PC was native and the signal path resumed it.

Distinct unsuccessful runs remain preserved: run7 missing initial lease; run8
reserved lookup backing; runs9–11 missing syscall handoff. Runs10/11 stop promptly
on the definitive owner refusal while retaining normal cleanup. Their failures
were not changed to passing results. No deliberate native fatal fixture was added.

## Targeted verification and exact inputs

| Check | Result |
|---|---|
| Changed Wine/FEX code and assembly | Compiled and linked; original full debug artifacts retained |
| Ordered FEX supplement replay | Nine patches/eight affected files replayed; test-only Module injection recorded separately |
| PE role/ARM64X selection tests | Six passed under clang/UBSan against paired7/linked10 |
| Checked overcommit behavior | Actual selected header passed 11 controlled query/commit/bounds cases under UBSan; original NT failures preserved |
| EC API state test | Actual x64 roundtrip above passed; full SIMD/flags/suspend not claimed |
| Actual EC lifecycle probe | 62 checks passed on linked14/paired8; partial shared-code publication, guard bit, pin, stale generation, neighbor bitmap and recycling; subsequent x64 exit42 |
| EC callback refusals | Actual selected Wine callback with controlled VM responses passed under UBSan: identity/range/role/generation, commit/query/protection failures, bitmap observation failure and neighbor preservation |
| Read-only metadata roles | Actual owner with substituted backing passed native/EC role selection and error/no-write controls |

Private receipts under `.build/task5/` (SHA-256):

| Receipt | Digest |
|---|---|
| `integration-paired7/control.json` | `6faa5168b0c59d2f1f8cf60e2148cb66e16dfefd87e30486f1be1505e4c35383` |
| `integration-fex-link10/control.json` | `8581ae239b641b38f450e33f45ede8dcc38ea5df0ea1c275e8f1e5f5977be6e0` |
| `integration-runtime11/runtime.json` | `f8cd745925a8786d6e8f67d00dcfad8d1724450e813f4ce17271206a78388e30` |
| `integration-run12/case.json` | `db4ce2c9d511a0956bfaa14578ad10d5c0b7aae54a1adef3926cd736ba63739d` |
| `integration-roundtrip1/control.json` | `36ee3f0424b61a5e5bd9150ed1ed3075f48229563bcbef7b32a0d82c60357234` |
| `integration-runtime12/runtime.json` | `39192a48fe2d04e632fb6a881bff1848d97afcefe22a78d5c78123a5045f1140` |
| `integration-run13/case.json` | `64fbe29e6219cd4de6ca8adcb3bfa87fa87acfdb1606710f087501bd457e815a` |

`integration-execution-assessment1/control.json` contains the focused assessment.
Recipes, commands, source identities, test source, original failed runs and raw
logs remain private. Incremental links reuse unchanged Source85 objects and do
not replace the required final reconstruction from recorded source/tool inputs.
No performance, graphics, Steam or game tests were run.

## Actual EC memory result and resource observation

The test-instrumented module uses the actual selected translator, ThreadInit
binding, Wine owner and PEB bitmap. Run15 passed 36 dispatcher lifecycle checks.
Run17 added partial shared-code publication, an unclassified final guard,
retirement and metadata observations; all 62 checks passed, followed by the
same x64 API roundtrip exiting 42. It also passed before/after authorization,
owned cleanup and unrelated sentinel survival. Its 21 recorded host translation
observations and 4,566 image events were ARM64/native in their recorded scopes.

The existing metadata opcode initially refused EC in both source and owner.
It now accepts the actual compiled role only through existing module admission
and backend role validation. No wire format, permission or allocation is added.
The expanded probe initially rejected a readable read-only zero bitmap page;
its reader was corrected to accept read-only or read/write pages. Original run14
and run16 refusals remain preserved. A controlled metadata test initially omitted
the mandatory EC backend callback; the corrected test retains the original failure.

Measured at the initialized-thread lifecycle checkpoint, before guest dispatch:

| Observation | Value | Meaning |
|---|---|---|
| Bitmap virtual extent | 4 GiB | Includes lazy read-only address space; not measured physical memory |
| Writable bitmap coverage | 16 KiB | Retained write-enabled bitmap pages in this finite run |
| Owner fixed native storage | 108,564 bytes | Actual read-only owner/adapter report; not all process storage |
| Extra arena protection leaves | 0 | Relative to the recorded baseline arena |
| Protection leaf / view block | 1 MiB / 1 MiB | Allocation granularity, not an assertion that a new block was allocated |
| Reported available view slots | 1,024 | Observer's capped count |

These are real component observations, not aggregate high-water or resident
memory measurements. Close the remaining source/stack/bitmap accounting and
simultaneous-lifetime acceptance before treating the 16-MiB estimate as qualified.

Latest private receipts:

| Receipt | SHA-256 |
|---|---|
| `integration-paired8/control.json` | `5e4ab7c106939179b50a128f00da1f9cdc2cf981d6ec9a1cef88f6b43aad2c25` |
| `integration-fex-link14/control.json` | `076351b567bd8603495f3da36472fdd957aac246a1407022c7dfb7da9eb628c0` |
| `integration-runtime16/runtime.json` | `31e3b60f08539e1b20dd27fa35ba26ca2eacc2d896c27ff392b3eaf6b828e8ae` |
| `integration-run17/case.json` | `8a867f7e317aaf93e584ea33dcf9f007d73c3b3fa2f11bb1f68ced778fc2e965` |
| `integration-ec-lifecycle-assessment2/control.json` | `eecdebc318f3aef7dc097ae0863df80d06aa1306be17d69b0edbf18db0a85081` |

## Remaining completion conditions

1. Reconcile the passing EC lifecycle/error controls with required source-lifetime
   and simultaneous-executor acceptance. The finite test module does not by itself
   qualify every ordinary module callback or concurrent teardown path.
2. Observe/justify the integrated bookkeeping profile, including retained bitmap
   backing and simultaneous storage. The current 16-MiB estimate is not a measured
   aggregate and does not inherit the old 256-KiB ordinary fixture proof.
3. Complete the separate Stage 3 memory and Stage 4 dispatch acceptance/report/
   commit when all their required checks pass. Later Stage 5 retains required
   thread/TLS/callback, invalidation and exception/context/suspend work; Stage 6
   retains fresh paired reconstruction and affected native regressions.

Stage 3/4 and Issue #5 remain open. Megabonk execution is unperformed.

## Storage and preservation

Three completed disposable native-test prefixes were removed after checking their
successful cleanup and lack of live process references. About 3.21 GiB of logical
payload was released. Their receipts/logs, unique failures, original input caches
and latest Source85 runtime evidence remain. New builds use separate directories;
no other project's files were changed and no artifacts were uploaded.

Repeated large DLL/EXE payloads in completed integration prefixes were replaced
with independent APFS copy-on-write clones only after matching contents and
extended attributes. Paths, contents, modes, timestamps, unique files, registry
state, failed-run diagnostics and receipts remain. This is storage sharing,
not hard links or prefix deletion. Private cleanup receipts record each origin
and hash; transient disk-free measurements are not a stable total saved claim.

Final storage cleanup recovered writable space after a transient ENOSPC during
receipt preparation. That failed command did not run a new fixture or delete
evidence; the subsequent clone-only cleanup completed. Subsequent successful run12/run13 disposable prefixes were removed after confirming
reaped processes; their receipts, logs and signed runtime inputs remain. The
storage gate refused one preparation before execution when space was below its
bound. Space was reclaimed within Pear before continuing; free space fluctuates
with other work on the volume.

The low-space full cold-prefix execution was rejected by automatic approval
review and did not start. A safer initialized-prefix path was then implemented:
independent APFS clone of the completed synthetic run16 prefix, current FEX
bytes overlaid, unchanged Wine pair/fixture, matching wine.inf update timestamp,
and full prefix inventory checks before execution. Only the two known Wine drive
symlinks are admitted. Run17 succeeded through this path with about 2.5 GiB free
remaining. This is not a fresh-prefix setup qualification. Cold execution now
requires 4 GiB free; prepared-prefix execution has a separate 2-GiB guard.

Successful disposable run12/13/15 prefixes were removed, while receipts/logs and
signed inputs remain. Completed duplicate payloads share APFS storage. Successful
incremental object files and never-used linked7 DLLs were pruned with hashes;
full debug DLLs for executed candidates, source snapshots, recipes and original
failures remain. No GitHub write or other-project cleanup occurred.

## Stage 3 closure — October 7

[Stage 3 report](task_m1_5_stage3.md) supersedes the remaining Stage 3 conditions
above. Run20 passed the 62 EC lifecycle checks plus two simultaneous real EC
workers, active timeout, parked-pin refusal, released retirement and stale-entry
rejection, followed by the x64 NT roundtrip exiting 42. All owned cleanup,
sentinel and current authorization checks passed. Run18/19 remain failed fixture
attempts, not runtime passes. The final fixture uses the existing Poll gate.

The current design records the reviewed finite 16-MiB resource profile: 12.5 MiB
accounted and 3.5 MiB headroom, with actual object layouts, writable PE coverage
and Wine component observations. Physical peak/RSS and ordinary upstream engine
allocations are not measured. Stage 4 file/time/event/native callback completion
and Stage 5 ordinary lifecycle remain separate. No GitHub publication occurred.

## Stage 4 closure — October 7

[Stage 4 report](task_m1_5_stage4.md): normal link18 (no finite test injection)
passed the NT state roundtrip and file/time/event/native-to-x64 callback fixtures
in run21/run22, both exit42 with complete cleanup and current authorization.
Stage 5 implementation is explicitly approved. Preserve original FEX C++/assembly
and connect ordinary lifecycles to the owner; do not remove unsupported guards
without that connection. Stage 6 reconstruction and game execution remain later.


## Stage 5 implementation checkpoint — October 7

Stages 3 and 4 are locally committed as `91fc9b3` and `1a29f18`.
Stage 5 is in progress, not completed. No GitHub write has occurred.

- Original MIT FEX self-thread teardown is connected to actual source closure,
  owner unregistration, checked call-ret/emulator-stack frees and CRT cleanup.
  Shared Context/code-buffer descriptors do not impersonate ThreadState holds;
  actual thread entry/batch references still block teardown. Cross-thread forced
  termination remains unsupported pending cooperative context integration.
- Run23's original x64 worker/TLS fixture exited 42 on normal FEX link20. It
  checked distinct worker identity, isolated TLS values, normal worker return,
  worker exit42, unchanged main TLS and owned handle cleanup. The runtime log
  records `ThreadTerm.complete` with status/domain/code zero. Current signing
  authorization, 21 native ARM64 process observations, 4,566 ARM64 image events,
  full owned cleanup and sentinel survival passed. This is finite fixture
  evidence, not complete late-load coverage or Megabonk qualification.
- Receipt identities: link20
  `6c72ca06a23c2216799d10354a116af2641546db02a5ebbc65f94eb1acd1b3b2`;
  case23 `a896e1239a679e3767bc9636eb34520126c4c57a279bd96f1b7639a7ef469d7e`.
- Ordered patches 0005b/0005c reuse FEX interval/cache and Wine before/after
  notifications. A bounded foreign-thread registry hold protects real targets;
  owner write admission precedes source locks and finishes after unlocking.
  No wait is retained across blocking file reads; their existing post-read
  behavior is reused. No wire ABI, native guest execute permission, or Rust
  rewrite is introduced. Link22 compiled and linked successfully, receipt
  `4d4299e909acec84b309e4bfe4fae2c8baedbc77213b1cf033e9c4c3287763f2`.
- `tests/fex/guest_invalidation.c` builds a two-thread 41-to-42 code-mutation
  fixture. Its execution remains unperformed at this checkpoint. Stage 5 also
  retains context/suspend, supported ordinary exceptions/guards and explicit
  i386 helper scope. The old unsupported branches are not passing evidence.

Storage exhaustion prevented the first attempt to save the invalidation fixture;
no runtime test started. Saving/building succeeded after owned cleanup. Completed
run20–23 disposable prefixes were removed after process checks; exact logs,
receipts, runtimes and initialized templates remain. Historical module PE trees
were losslessly compressed, with each archived file/link/mode verified before
removal. Their inventories and restore-required notices remain in private
`historical-pe-archive-oct7` receipts. Current module14 inputs are untouched.


The reuse comparison also inspected the pinned Madeira/FEX fork and
`buberlo/madeira-anyps5` input snapshots. Their thread-exit ordering and iOS
exception adaptations informed boundary review; no GPL fork code was imported.
The implementation reuses the original MIT FEX cleanup, cache, interval and CRT
mechanisms in C++/assembly. iOS-specific VM/SMC changes are not assumed valid on
macOS. Pinned source URLs and hashes remain in the private reuse inventory.

At the end of this implementation checkpoint, free space is approximately
1.8 GiB after archival. This is below the existing 2.5-GiB runtime-preparation
guard. The invalidation runtime was not prepared or executed, and no guard was
lowered. The requester was asked to pause other disk-heavy work or make at least
5 GiB available. The next operation is the recorded link22/guest-invalidation1
signed pairing followed by its one meaningful two-thread mutation test. Then
continue the still-required exception/context/suspend integration. Stage 5
remains open; there is no Stage 5 completion report or completion commit.

## Stage 5 continuation after storage recovery — October 7

Storage is no longer the immediate blocker (approximately 40 GiB free at the
latest check). The earlier storage-wait paragraph is historical. Stage 5 remains
in progress; no GitHub publication or completion claim has been made.

- Actual invalidation runs exposed two source-concurrency bugs: a peer's short
  metadata lock was treated as self-reentry, and concurrent compiler threads
  attempted owner writes without serializing source publication. Ordered patches
  0005d–0005h preserve bounded upstream error diagnostics, distinguish actual TEB
  reentry, and serialize source compilation/link/invalidation using real lifetime
  bindings, existing pinned-owner polling and finite NT waits. Owner admission,
  W^X and wire ABI remain unchanged. Failed runs24–30 and build28 remain retained.
- Run31 passed the original two-thread code-mutation fixture: both threads see
  41 before mutation and 42 after logical protection changes and cache
  invalidation. Patch0005i supplies a real current published-buffer barrier when
  no direct-link descriptor exists. Build29 receipt:
  `08c1c9e35cdd42e026cc22374f466f74a9981c886c39619d0b2e25782b1d368d`.
  Case31: `89566596ce71bd6b213a8ddf2421ce9ed90d015baa59f13f8bd52fb3731b8690`.
- Patches0005j/0005k reuse original MIT FEX register/flags reconstruction,
  ARM64EC packing, exception mapping and suspend doorbell behavior. Exact source
  instruction reads require the actual retained thread and execution owner.
  Source holds and callback guards end before nonlocal NT guest delivery.
- Run32 passed handled guest UD2 with guest RIP/RAX edits, resumption, an ordinary
  data guard fault, one-shot guard behavior and cleanup. Actual delivered codes
  were `c000001d` and `80000001`; exit42. Build31 receipt:
  `1680395ddc684a194cf10b041111dac4fab81901ab8b54a3460fcce8aa455aaf`.
  Case32: `e3614b669f5da040fad178e47a58bab8573cfff1ff6864419c195705e61e84a0`.
- Each passing run above passed before/after authorization, owned cleanup,
  unrelated-sentinel survival, 21 native ARM64 process observations and 4,566
  ARM64 image events. These are finite test observations; full late-load coverage,
  broad instruction support, game execution and distribution remain unqualified.
- The next actual fixture suspends a translated computation loop, verifies and
  edits R12 through Windows context APIs, resumes it and verifies the result.
  Same-candidate affected lifecycle checks and final Stage 5 assessment remain.
  Native guard-page compiler recovery, forced foreign-thread termination and
  broader SMC/unaligned routes are not inferred from the ordinary guest tests.

## Stage 5 completion checkpoint

The same final link35 passed run37–41: worker/TLS, two-thread invalidation with
failed-removal preservation, guest exceptions/guard/nested native call, hot-loop
suspend/context editing, and API/callback. Each exited42 and passed authorization,
ARM64 observations and owned cleanup. The Stage 5 report and sanitized sidecar
own exact hashes and limits. Earlier in-progress notes above remain historical.
The conditional-backedge poll and source writer/entry serialization fix the
observed hot-loop quiescence failure; no owner admission was weakened.

All 24 integration patches independently replay over 15 files. Eight completed
synthetic prefixes were removed after process checks; receipts/logs/runtime
inputs/templates and failures remain. Stage 5 is complete locally; Stage 6 fresh
reconstruction still requires continuation. No GitHub write or Issue closure.

## Reviewed reuse guidance adopted — October 8

The authorized documentation handoff was applied to the existing platform reuse
record and single delivery plan, after recording their location judgment in the
implementation plan. This is a documentation checkpoint, not Stage 6 execution.
The original M1 completion criteria, core backlog, proposed M2 and independent
CPU-engine sections remain byte-identical to the Stage 5 commit. Runtime source
and historical stage reports are unchanged.

The coordinator updated Issue bodies #5, #6, #8, #9 and #11. Independent readback
matched all five delivered bodies and confirmed unchanged titles, states and
milestones. Local documentation bytes match the reviewed patch; relative links
and whitespace checks passed. No runtime regression was repeated for prose-only
changes. Private verification receipts are retained in
`/private/tmp/pear-task5-reuse-integration-20261008`.

Reuse decisions preserve the existing FEX/Wine/DXMT languages and passing owner,
require complete upstream dependency and license review before new boundary
code, and identify existing CPU, graphics and acquisition tools for later tasks.
They do not impose the old 256 KiB prototype limit, waive qualification gates,
choose Pear's license or authorize a runtime rewrite. Stage 6 fresh reconstruction
was subsequently confirmed as authorized by the source conversation's explicit
human instruction to continue the planned next work. The earlier approval-wait
interpretation is superseded; fresh reconstruction and required checks may proceed.
This local documentation commit does not publish runtime code or close Issue #5.
