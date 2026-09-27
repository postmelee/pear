# Task #2 — Stage 2 report

GitHub Issue: [#2](https://github.com/postmelee/pear/issues/2)
Implementation plan: [task_m1_2_impl.md](../plans/task_m1_2_impl.md)
Stage: 2 — Isolated baseline memory and JIT tests
Date: September 28, 2026

## Stage Purpose

Establish a bounded child-process harness and measure ordinary native memory, protection, low-address allocation and JIT behavior before authorized process/ABI tests. The maintainer's explicit request to proceed authorized this stage after the Stage 1 pause.

## Artifacts

| File | Change Summary |
|---|---|
| `host/probe/baseline.h`, `child_runner.c` | Private packet contract; owned process groups, execution deadlines, bounded output, validated termination and bounded cleanup |
| `host/probe/baseline_child.c` | Four disposable native trials; no external or guest code |
| `host/probe/baseline_evaluate.c`, `baseline_main.c` | Semantic assessment and a separate JSON baseline CLI; no fixture switches in production |
| `host/probe/Makefile` | ARM64 supervisor and companion child builds alongside the existing observation-only diagnostic |
| `tests/host/test_baseline.py`, `runner_fixture.c`, `runner_driver.c` | 21 lifecycle/assessment tests and two real native baseline tests |
| [Host capability guide](../../docs/host-capabilities.md) | Commands, execution-result interpretation, observed results and qualification limits |
| [Stage 2 evidence](task_m1_2_stage2_observations.json) | Source/test hashes, binary hashes, compiler/SDK, complete sanitized baseline JSON and test output |
| Implementation plan and [daily board](../orders/20260928.md) | Stage 2 approval, concrete boundaries and current checkpoint |

## Body Change Scope / Lossless Preservation

The Stage 1 CLI, observation contract, source and tests are preserved. The new supervisor embeds observations about itself and separately reports each child's trial. A successful observation, a passing baseline operation and qualified runtime support remain distinct.

The runner uses `posix_spawn` with explicit arguments, an owned process group, closed unrelated descriptors and nonblocking bounded pipes. It retains the leader with `waitid(WNOWAIT)` until group cleanup to prevent PID reuse during signaling. Execution has a three-second deadline; cleanup has a further one-second budget. Failure to terminate or reap is reported as an error rather than an indefinite wait. Auto-reaping SIGCHLD policies are rejected before launch.

macOS can return `EPERM` when a group contains only its unreaped zombie leader. This case is accepted only after confirming the leader has exited and bounded group enumeration finds no other member. Other permission errors remain failures. The behavior was checked against Apple's [signal implementation](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/kern/kern_sig.c). Failed-spawn tests also account for the bounded kernel-owned cleanup described in Apple's [spawn implementation](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/kern/kern_exec.c); they do not hide a reapable unknown child.

The work does not launch Steam, Wine, FEX, DXMT or Megabonk, access game/account/save files, change macOS protections, invoke restricted x18/page/thread APIs, or alter the executable's normal low-address layout. New repository prose and code comments are English.

## Verification Results

The implementation plan's Stage 2 commands were run:

```sh
make -C host/probe
python3 -m unittest discover -s tests/host -p 'test_*.py' -v
lipo -archs .build/host-probe/pear-baseline-probe
lipo -archs .build/host-probe/pear-probe-child
.build/host-probe/pear-baseline-probe > .build/host-probe/local-baseline.json
python3 -m json.tool .build/host-probe/local-baseline.json > /dev/null
git diff --check
```

| Check | Result |
|---|---|
| Native build | Passed with Apple clang 21, SDK 26.5, ARM64 and warnings treated as errors |
| Complete test suite | `Ran 37 tests in 5.902s` / `OK`; 14 existing diagnostics, 21 lifecycle/assessment cases and two native baseline cases |
| Mach-O inspection | All three tools contain only ARM64 slices |
| Signature inspection | Linker-generated ad-hoc signatures; strict verification exits zero for each tool; no identity/profile qualification implied |
| Actual ordinary-host report | Valid JSON; supervisor ARM64, own translation query false; macOS 26.5.2/build 25F84, ordinary 16 KiB pages |
| Child lifecycle | Four real trial children reaped; fixture checks found no running owned descendants or descriptor leaks; unrelated sentinel survived |
| Denied termination regression | Test-only kill shim returns EPERM; runner returns bounded `io_error` with `child_reaped=false`; test driver explicitly waits for natural exit and reaps the child without changing that failed result |
| Evidence and diff | Reviewed JSON, hashes, links, English text and diff hygiene; no proprietary data or private paths included |

Actual baseline outcomes:

| Trial | Result | Evidence and Interpretation |
|---|---|---|
| Memory | Passed | Allocate 16,384 bytes; write/read 42; read-only protection and readback; restore write access; write/read 84; release |
| Protection | Passed | Valid pre-fault evidence followed by SIGBUS (10); parent continued and reaped the child |
| Low address | Unavailable | Non-overwriting allocation at `0x20000000` rejected with Mach `KERN_INVALID_ADDRESS` (1); normal `__PAGEZERO` spans 0–4 GiB |
| JIT | Passed | MAP_JIT allocation; fixed eight-byte ARM64 leaf; publication; instruction-cache synchronization; returned 42; release |

Failure coverage includes nonzero exits despite a valid packet, unexpected signals, silence and partial-output timeouts, malformed/missing/truncated/trailing packets, stdout/stderr floods, invalid field ordering, inherited descriptors, closed stdin, leader exit with descendants holding pipes, repeated cleanup, a wrong JIT return value, incomplete protection setup and a reported mapping cleanup failure. Only the test object substitutes the kill function; shipped binaries have no injection option.

The CLI exits zero when all trials are passed or unavailable. The unavailable low-address trial is not a passing host prerequisite. The protection child's release remains `not_run` because the expected fault terminates it; process teardown ends that trial. JIT publication/cache APIs returning normally are recorded separately from the observed return value.

## Residual Risks

- **Rosetta-free Megabonk execution is not achieved.** Issue #2 remains open, with runtime/game/distribution qualification explicitly unassessed.
- Low-address mapping for the proposed runtime remains unresolved. One rejection in the retained baseline layout does not prove all layouts or addresses impossible.
- Ad-hoc native JIT success does not establish hardened-runtime, restricted capability, provisioning or distribution authorization, nor correct x86 translation.
- The runner controls cooperative owned test groups. Escaped descendants, concurrent external reaping and hostile-code attestation are outside its contract. A platform refusal to clean up is explicit and may leave `child_reaped=false`.
- Protected-write faults are intentional; core dumps are suppressed by the child, but macOS may still record crash diagnostics.
- Results cover this Mac/OS/toolchain and these finite tests. They do not qualify all Apple Silicon hardware, 4 KiB Windows behavior, x18 transitions, callbacks or thread ordering.

## Impact on Next Stage

Stage 3 must establish the actual authorized signing/provisioning route before restricted process/page tests. It should reuse the tested runner and keep baseline ad-hoc evidence separate from the authorized artifact. Exact commands and profile-dependent tests belong in the implementation plan once the real authorization path is known. No passwords or private keys should be requested in chat or committed.

The unresolved low-address and 4 KiB requirements need concrete behavioral evidence. A declared entitlement, available SDK symbol or successful signature verification alone is insufficient. Ordinary-user distribution remains a separate qualification gate.

## Approval Request

Review the completed Stage 2 artifacts and evidence, then approve Stage 3 under the existing implementation plan. No Stage 3 capability execution has been performed as part of this stage.
