# Task #5 Stage 5 — Translated Lifecycle and Cooperative Contexts

GitHub Issue: [#5](https://github.com/postmelee/pear/issues/5)
Implementation plan: [task_m1_5_impl.md](../plans/task_m1_5_impl.md)
Stage: 5 — completed locally on October 7, 2026. Issue #5 remains open.

## Stage Purpose

Complete the approved finite translated thread, callback, memory-change,
context/suspend and ordinary guest-exception paths through actual FEX in native
ARM64 Wine. These are CPU integration results, not Megabonk or Steam support.

Context used: approved task/implementation plans and memory design; root,
runtime/FEX and tests rules; runtime contracts/source qualification; Stage 3/4
reports; task-stage-report and daily-board procedures. The requester's explicit
Stage 5 continuation covers this implementation. No GitHub publication occurred.

## Artifacts

| File | Change summary |
|---|---|
| `runtime/fex/patches/integration/0005a` through `0005o` | Fifteen ordered, attributable C++ supplements: actual self-thread cleanup, foreign cache holds, paired VM notifications, bounded diagnostics, source mutation serialization, actual published-buffer barriers, guest exceptions and cooperative suspend |
| `runtime/fex/patches/integration/fex-series.json` | Exact patch and per-file before/after hashes; 24 total integration patches |
| `tests/fex/guest_thread.c` | Worker/TLS isolation and normal self-thread return |
| `tests/fex/guest_invalidation.c` | Two-thread 41-to-42 mutation, failed VM-removal preservation, protection and flush |
| `tests/fex/guest_exception.c` | Handled UD2, guest context edit, nested native call, ordinary data guard |
| `tests/fex/guest_context.c` | Hot translated loop, suspend, R12 get/set, resume and worker completion |
| `tools/fex/integration_run.py`, `integration_runtime.py` | Bounded assertion termination and exact development receipt allowlist |
| Existing plan/design/checkpoint/board | Current state and synchronization rationale; historical failures retained |
| [Sanitized observations](task_m1_5_stage5_observations.json) | Exact source/build/run hashes and finite acceptance boundaries |

## Body Change Scope / Lossless Preservation

Retain original MIT FEX C++/assembly and Wine C. Reuse FEX state/flags
reconstruction, ARM64EC packing, exception mapping, interval caches, teardown
and block-boundary SuspendDoorbell. Madeira references informed review but no
GPL fork code was imported. There is no Rust rewrite, new owner wire ABI,
RW/RX alias, new entitlement or weakened write-admission check.

The new private source turn serializes compilation, linking, invalidation and
entry/resume. Waiting pinned executors use actual owner Poll; a writer signals
actual active EC frames under bounded lifetime protection. The missing
conditional-backedge check reuses the existing flag-preserving emitter. A
suspend trap reconstructs guest state and releases the real execution lease
before Wine continuation, ending all source holds before a nonlocal transfer.

Direct linking is optional when its finite table is full or a peer seals entry;
the existing indirect branch remains valid. Failed/closed admission still
refuses. Published buffers without link descriptors now supply a genuine write
barrier. VM removal failures retain live interval/image metadata. Reports remain
in approved internal locations; no public support/architecture claim was added.

Unique failures, exact input caches, runtime signatures and raw private results
remain outside Git. Eight completed synthetic prefixes were removed only after
recorded process reaping and current process checks; logs/receipts, signed
runtimes and initialized templates remain. Their total logical size was about
13.1 GiB; APFS physical recovery was not measured. No authenticated prefix or
other project was removed.

## Verification Results

Host: Apple Silicon, native ARM64, macOS 26.5.2 (25F84). Pinned FEX
`59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa`; Wine
`4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`. Conservative CPU configuration,
software TSO and disabled persistent code caches are preserved. Diagnostics are
for correctness; timings below are not performance measurements.

The final incremental build, link35, compiled affected translation units and
linked against the recorded full module14 input. All construction commands
passed. Existing layouts/vtables remain unchanged; new frontend bookkeeping is
private to the rebuilt module. Complete writable PE coverage is 102,400 bytes,
within the prior 128-KiB allowance; this is not RSS or a whole-engine memory cap.

Actual commands (exact producers are retained with private receipts):

```sh
python3 /private/tmp/pear-fex-integrated-build35.py
python3 /private/tmp/pear-stage5-final-cases.py
python3 /private/tmp/pear-stage5-independent-replay.py
python3 -m py_compile tools/fex/integration_runtime.py tools/fex/integration_run.py tools/fex/integration_assess.py
git diff --check
```

The final case producer invokes existing `integration_runtime.py`,
`integration_run.py` and `integration_assess.py` sequentially for each row.
Original fixtures are compiled with the pinned native llvm-mingw clang,
`--target=x86_64-w64-windows-gnu -O2 -ffreestanding -fno-builtin -std=c11
-nostdlib -Wl,--entry,pear_first_dispatch -Wl,--subsystem,console`, and the
required `kernel32`/`ntdll` imports. Exact argv and PE hashes remain in receipts.
Stage 6 must produce the fresh final reconstruction and its durable public recipe.

| Final candidate case | Required result | Actual |
|---|---|---|
| Worker/TLS, run37 | Distinct worker, isolated TLS, main TLS unchanged, normal ThreadTerm | Exit42; actual cleanup success |
| Invalidation, run38 | Failed removal preserves live code; both threads change 41 to 42 after protection/flush | Exit42 |
| Exceptions, run39 | Guest handler edits RIP/RAX, calls native NT time API, resumes; data guard delivered once | Exit42; `c000001d` and `80000001` delivered |
| Context/suspend, run40 | Running x64 loop pauses; R12 is 17, is set to42, resumes and returns42 | Exit42 |
| API/callback, run41 | File/time/event APIs and native-to-x64 RunOnce callback | Exit42 |

All five runs use **the same final translator source/build** and actual Wine
pair8, with separately recorded guest PE inputs. Each passed current per-image
signing/provisioning authorization before/after, 21 native ARM64 process
observations, 4,566 ARM64 image events, owned cleanup and unrelated-sentinel
survival. Runs use independent APFS clones of the recorded synthetic initialized
prefix; they do not prove fresh installation. No Rosetta translation was observed
in the required finite paths. Complete late-load coverage remains #10's work.

Independent system `patch -p1 -F 0` replay passed all 24 patches over 15 files
with every before/after hash verified, separate from the Python builder's patch
implementation. Python syntax and final diff checks passed. The unchanged native
owner protocol's older tests are reused only for their unchanged inputs; this
stage does not relabel the old 62-check instrumented EC run as a final-byte run.
Stage 6 retains affected native regression requirements.

Original failures are not passes: concurrent writes were refused; normal peer
registry contention was mistaken for reentry; missing no-link invalidation
barriers refused; transient link admission aborted execution; the hot conditional
loop did not acknowledge writer quiescence. Corresponding source fixes were
followed by the five same-candidate passes above. Failed builds/runs and the
unsuccessful attempt to enable general FEX logging remain preserved.

## Residual Risks

- i386/WoW64 execution is unperformed and unsupported in this admitted profile.
  Stage 2 built the ARM64 WoW64 module, but that is not execution evidence. These
  five PEs are x64 and require no i386 guest helper. Steam/login/helper support
  must inspect actual helper architectures and implement/qualify required i386
  paths before claiming the eventual user flow.
- Forced foreign-thread termination, async file-completion invalidation, broad
  RWX inline SMC/unaligned repair, compiler JIT-guard nonlocal recovery, arbitrary
  unwind/exception coverage and concurrency stress are not qualified here. The
  successful guard test is an ordinary guest data guard, not JIT guard recovery.
- Tested limits remain one Context and at most three participating EC threads.
  Game workloads, broader capacity/progress, instruction/ordering correctness
  and performance require later evidence. Bounded refusal remains intentional.
- The final pair is incrementally linked, not freshly reconstructed. Full
  observation, independent Mac, clean-machine, game, GPU and distribution
  qualification remain unperformed. #5 cannot close on this stage alone.

## Impact on Next Stage

Stage 6 starts from final link35, the ordered series, these four original
lifecycle fixtures and the existing API/roundtrip fixtures. Rebuild the coherent
Wine/FEX pair from recorded inputs, run required affected native and integrated
checks on those bytes, and complete the reproducible contributor handoff. Keep
unsupported helper/exception paths explicit; any new known required failure
must be fixed rather than deferred to #6 as optional stress.

## Approval Request

Stage 5 is complete within its approved finite scope. Review this report and
approve Stage 6 fresh reconstruction before that stage starts. GitHub publication
and Issue closure remain separate and unperformed.
