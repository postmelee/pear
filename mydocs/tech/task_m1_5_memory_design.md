# Task #5 Executable Memory and First-Dispatch Design

Status: current internal task design, October 7, 2026.
Authority and acceptance: [implementation plan](../plans/task_m1_5_impl.md).
Historical rationale and detailed source inventory: [frozen record](../troubleshootings/task_m1_5_stage3_history.md).
This document is not a product support specification.

## Reuse and boundaries

Retain pinned FEX C++/assembly, Wine C, the existing decoder/IR/backend,
Darwin UnixLib, actual Context/Thread/Dispatcher objects, source staging buffers,
link/patch adapters and the single-address Wine owner. Retain the original
23-patch Wine baseline and append separately identified CPU supplements.
Do not replace the engine or use a commercial binary as a dependency.

The native owner and Source85 finite source paths have successful evidence.
That evidence covers its exact ordinary ARM64 candidate, not ARM64EC callers,
full Module initialization, translated instructions or delivered exceptions.
The integrated route must connect actual Wine loader, FEX module admission,
code registration and guest dispatch before claiming first x64 execution.

## October 7 upstream reuse decision

Source inspection, not a reproduced upstream execution claim:

| Source pin | Reusable implementation | Dependencies and decision |
|---|---|---|
| FEX `59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa` (current MIT input) | ARM64EC `Module.S` entry/return, `SyncThreadContext` flag merge, generated dispatcher, compiler, call-ret cache invalidation | Keep these implementations and their languages. Restore the original context body behind actual source-identity checks. Add only the missing native entry/exit owner adapters. |
| [Madeira FEX `be778d7`](https://github.com/willfaust/FEX/tree/be778d7ba5b98bee0405fd1d6a50d305a0807df0) | Entry/return synchronization, image notification ordering, host feature selection | Its iOS path depends on dynamic TEB/TSD instruction rewriting, read/write aliases and a code-buffer sweep gate. Copying the assembly alone is not a macOS port. Review informed the boundary analysis; no fork code is imported. |
| [Madeira `bbbf8d0`](https://github.com/willfaust/Madeira/tree/bbbf8d0e20fd8b75f433f4a8d2a8eaf8d5571120) | Loader-to-translator TEB metadata, alias lifetime and host-NX guest mapping | Requires coordinated loader, signal, alias registry and JIT-pool changes. This is a material alternative memory design, not an isolated fix to the missing Pear entry lease. |
| [Integration stack `169a474`](https://github.com/buberlo/madeira-anyps5/tree/169a474b9a77e94c2fc746a52ef53d2d8e82ed51) | Separate guest data/host execution roles, late profile initialization, committed placeholder classification | Retain as concrete references for relevant future memory paths. PS5 arena constants, ELF/HLE and rendering integration do not solve this Windows PE dispatch boundary. |

The inspected fork's `LICENSE-MADEIRA.md` assigns Madeira modifications GPL-3.0-or-later while retaining MIT for original FEX code. Its historical MIT statement requires matching historical provenance before relying on it. The integration stack separately identifies its patch licenses. No new license choice or mixed-license import is made by this decision.

The existing owner is retained for a concrete reason: its `active()` and
`wait_native()` block **all** managed executors before any write or retirement,
including shared-code extents. The dispatcher lease is therefore already the
global execution lease used by the compiler/linker and managed-read adapters;
there is no need to invent a per-basic-block transfer protocol. Source cache
invalidation retains the upstream call-ret stack clearing before old targets
can be reused. Its finite EC simultaneous-owner test now passes; ordinary translated thread teardown and exception lifecycles remain Stage 5.

The incremental change adds two nonvirtual Context methods and one compiled
Module gate, without changing Context layout/vtable or the Wine owner ABI.
It removes the unconditional `SyncThreadContext` refusal. `Module.S` saves all
non-scratch GPRs, all 32 SIMD registers, NZCV/FPCR/FPSR and the exact original SP
around the native gate, then uses the original FEX transfer sequence. Scratch
x16/x17 retain their upstream role. The wrapper aligns its bounded native-call
frame even when the incoming guest SP is only eight-byte aligned. Native-to-native
EC transfers consume no lease; managed exit requires the matching active lease.

The first real compiler call exposed the next required upstream service: lookup
backing is intentionally reserved but not committed. Restore only the original
MIT FEX data-overcommit branch in `ResetToConsistentState`, with checked native
query/allocation status and interval/type/protection bounds. Resume the exact
original native context only after a successful ordinary RW commit; executable
or unrelated faults remain unhandled. This uses Wine's existing native-context
continuation syscall and does not change a JIT lease, permissions or guest PC.
The broader context/exception/suspend paths remain explicitly unsupported until
their separate ownership integration is completed.

The upstream guest syscall handler transfers nonlocally into Wine's exception
dispatcher; it never reaches the usual generated return gate. Release its exact
active dispatcher lease before that transfer, then let `BeginSimulation` acquire
a new lease on return. No source lifetime hold may survive the abandoned frame.
Actual native `NtContinue` was verified to resume the native PC; the observed
second-entry refusal was caused by this later syscall transfer, not a native/guest
bitmap misclassification. Both exit42 and a two-call NT API roundtrip passed.

The finite EC lifecycle probe is separate test instrumentation inside the real
selected translator, after actual ThreadInit. It uses existing Reserve/Write/
Publish/Entry/Handoff/Unpin/Retire operations and reads the actual PEB bitmap.
It must preserve a neighboring extent's bits, refuse a retained generation,
and reject stale entry after reuse. Its instrumented DLL has a separate hash
and cannot substitute for final production-byte reconstruction.

Affected checks: patch replay; compile/link and assembly inspection; first x64
fixture exit 42 through the signed pair; guest register/callback state and code
invalidation/retirement checks before Stage 3/4 completion. The unchanged owner
protocol's earlier tests remain narrow evidence, not proof of this new entry.
No repeated native-only experiment or graphics/game benchmark is required here.

## Required invariants

- Normal macOS signing/provisioning and current per-executable authorization.
  Keep Hardened Runtime and library validation; no unsigned-executable-memory
  exception, private entitlement, no-TEB retry or deliberate native fatal test.
- One executable reservation, no RW/RX aliases. Verify the actual compatibility
  process supports the required 4-KiB protection geometry.
- Preserve the #4 immutable PE class and dynamic class. The current proposed
  arena is 1,588,985,856 bytes of virtual address reservation, not resident use.
- Shared code: 512 MiB total in 16-MiB units, with 16/32/64/128-MiB extents and
  final 4-KiB guard. Dispatcher: 1 MiB total, 16-KiB slots. Keep finite capacity
  and fail on exhaustion rather than reclaiming a live generation.
- Temporary emitted bytes are NX. Before copying or patching, park/drain all
  affected executors at the compiled native gate and retain continuation pins.
  Managed pages transition RX/NONE -> RW/NX -> RX; no W+X publication.
- Wait for quiescence before acquiring source invalidation/lookup/list locks or
  Wine virtual_mutex. Acquisition order is owner gate, source coordination,
  then Wine VM ownership. Revalidate identities after every wait.
- Reuse atomic RESUME, fixed source snapshots and checked epoch/generation
  updates. A pin alone is not a parked acknowledgment. Callback/reentry cannot
  bypass owner admission; raw asynchronous handlers cannot call blocking code.
- Preserve original instruction ordering, cache maintenance and retry PC.
  Inline RX tail locks remain inert; synchronization lives in NX owner state.
- Restore unchanged RX only in the proven pre-copy cancellation path. After an
  uncertain write/protection failure, retain quarantine and the original error.
- Detach entries/links before retirement, drain source references and execution/
  continuation pins, clear actual EC bits, observe NONE and only then recycle.
- Guest x64 bytes and return-stub data are never EC-classified native code.
  Native, ARM64EC, ARM64X and guest roles must be identified from real metadata.

## EC and loader integration

Reuse Wine's actual bitmap, CHPE/ARM64X processing, relocation/import machinery,
TEB/CPU-area layout and source-selected FEX export table. The native-only loader
refusal may be replaced only by explicit validated role-specific paths; unknown
images and malformed metadata continue to fail. A renamed file/header or a
caller-selected flag does not establish a role.

Connect the existing owner EC callback to exact owned views. Register before
entry publication, observe real bitmap backing/bits and protections, and clear
only after drainage. Preserve other live extents sharing bitmap backing.
Do not count the old temporary bitmap self-test as this integrated lifecycle.
Bind actual FEX module/source identity at admission; keep the ordinary test
entry's rejection of unrelated DLL callers. Do not enable a general bypass.

## Resource policy

The 262,144-byte bound remains the historical Source85 fixture's verified
configuration. It is not a game requirement or the integration profile's fixed
budget. The requester approved reassessing this arbitrary prototype constraint
on October 7, rather than rewriting upstream allocation solely to fit it.

Before admitting the integrated run, declare a finite measured/estimated bound
with headroom for owner records, Wine bitmap/protection-directory/view backing,
source adapter allocations and concurrent temporary storage. Distinguish virtual
reservation, committed backing and ordinary upstream engine allocations. Retain
capacity/refusal checks. No unknown cost is zero and no changed profile inherits
the old 256-KiB proof. Record the chosen bound and observations with the actual
candidate, without turning a stack-size micro-optimization into an independent
prerequisite when it does not affect safety or the declared limit.

## Necessary verification

1. Portable checks for changed parsing/role/ownership behavior, including the
   invalid input or known failure the change could introduce.
2. Actual publication/registration/retirement and source lifetime checks affected
   by the new EC connection; reuse unchanged native source evidence narrowly.
3. A deterministic original x64 PE through the real Wine/FEX entry, then required
   API, thread/TLS/callback and code-invalidation integration cases.
4. One fresh final paired reconstruction and the required tests on those bytes.

Keep source/build, synthetic, native, translated, game and distribution claims
separate. Wider differential instruction/fault/ordering stress belongs to #6;
known failures in #5's required paths cannot be deferred as optional coverage.

## Current finite EC evidence

The separately instrumented actual translator passed 62 owner/bitmap lifecycle
checks and then the x64 API roundtrip. Read-only metadata now follows the actual
compiled role through unchanged selected-module/backend admission. The finite
snapshot observed 16 KiB writable coverage in a 4-GiB bitmap virtual extent,
108,564 bytes fixed native owner storage and zero extra arena protection leaves.
This is not aggregate peak or physical-memory measurement. The finite profile
below closes the reviewed bookkeeping estimate; it does not bound whole-process RSS.

Completed synthetic prefixes may be cloned independently with APFS for targeted
runtime checks after matching the Wine pair, update timestamp, current translator
bytes and complete file inventory. Record this input and do not infer fresh-prefix
installation success from it. Preserve independent process ownership, signatures,
cleanup and unrelated-process survival. A cold-prefix run requires its larger
storage margin and separate qualification.

## Finite Stage 3 resource and lifetime acceptance

The admitted evidence profile is one real Context and at most three participating
EC source threads. Keep the owner's existing finite capacities and failure rules.
The 16-MiB bookkeeping estimate charges 12.5 MiB and keeps 3.5 MiB headroom:
128 KiB native owner/adapter, 128 KiB complete writable PE image, 2 MiB source
object allowance, three 1-MiB guest stacks, three 256-KiB emulator stacks,
4 MiB protection-leaf allowance, 2 MiB view-block allowance, 256 KiB retained
bitmap allowance and 256 KiB transition/alignment allowance.

Same-toolchain layouts are Context 1,904, Thread 12,288, JIT 816, dispatcher 752,
lookup 160 and code-buffer holder 200 bytes. Charging full page-rounded objects
(including unchanged upstream fields) and 256 buffer holders costs 1,118,208
bytes, within the 2-MiB allowance. The entire candidate writable PE coverage is
102,400 bytes. Native fixed storage is 108,564 bytes; the observed finite bitmap
has 16 KiB writable backing, no extra protection leaf and at least 1,024 available
view slots. The inherited owner/lookup/compiler capacities still refuse exhaustion.

This is a conservative finite source/VM accounting estimate, not a measured peak,
allocator-span measurement, ordinary-engine allocation bound or a 64-thread/game
profile. It explicitly excludes unchanged upstream IR, lookup-map, compiler data
and allocator backing; virtual JIT/bitmap reservations are reported separately.
A materially larger profile must revisit these costs. No upstream allocator is
rewritten to fit the former ordinary-only 256-KiB experiment.

Two actual EC workers retain their genuine source lifetimes and distinct executor
identities while sharing one published allocation. Active retirement times out;
after HANDOFF plus actual Poll parking, retained pins refuse retirement; after
UNPIN and source-hold release, retirement succeeds and stale entry is rejected.
The old native four-worker and Source85 link/cache/cleanup evidence remains scoped
to its unchanged owner/source algorithms. The finite EC workers park after their
test and are reaped at process exit; ordinary ThreadTerm is explicitly Stage 5.

## Stage 5 source progress and delivered contexts

Actual translated concurrency exposed a missing progress mechanism. Source
compilation, linking and invalidation now share a bounded private mutation turn,
identified by the real registered executor. Pinned contenders use the existing
owner Poll and finite NT wait; metadata and source coordination locks are absent
across those waits. Native entry and atomic resume hold the same turn through
admission, eliminating the scan/entry race. This is source serialization, not a
new owner permission, wire ABI or per-block execution-lease transfer.

A writer requests the existing FEX SuspendDoorbell on actual active EC peers.
The short source registry prevents lifetime sealing during that bounded frame
metadata access; no owner/VM/callback call occurs under it. Existing block-entry
and unconditional-backedge checks are reused, with the missing conditional
backedge added using the same flag-preserving emitter. At the delivered trap,
original FEX reconstruction packs the actual guest state, the real D lease is
released, and all source holds/callback guards end before Wine continuation.
The guest re-enters only after the writer releases its source turn. The same
reconstruction supports Windows suspend/context edits and handled guest faults.

A published current source buffer is a valid real invalidation barrier even
when no direct-link descriptor exists. Direct linking remains optional: a full
finite ticket table or transient entry seal keeps the already supported indirect
branch. Closed/failed source admission still refuses; no live ticket is evicted.
Failed free/unmap notifications preserve live guest intervals and image metadata;
cached translations are invalidated before the VM attempt, and mapping metadata
is removed only after observed VM success.

These changes preserve the owner's quiescence, write epoch, W^X, continuation and
retirement checks. The final mutable PE page coverage remains 102,400 bytes,
within the existing 128-KiB allowance. Ordinary engine allocations/RSS and broad
concurrency stress remain outside that finite bookkeeping claim. The Stage 5
report owns executed cases; Stage 6 must freshly reconstruct the final pair and
revalidate affected native/integrated checks on those bytes.
