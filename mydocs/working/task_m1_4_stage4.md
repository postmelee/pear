# Task #4 Stage 4 — Wine Threads, Memory and Exception Boundaries

GitHub Issue: [#4](https://github.com/postmelee/pear/issues/4)

Implementation plan: [`task_m1_4_impl.md`](../plans/task_m1_4_impl.md)

Stage: 4

Verification date: September 30, 2026

## Stage Purpose

The approved Stage 4 establishes finite Windows thread, memory and exception behavior in the actual ARM64 Wine host. Two Wine-created workers, controlled signals and suspension, recoverable and terminating faults, ordinary 4 KiB memory operations and fixed mutable ARM64 code passed. Existing API/ABI cases and all three bootstrap controls also passed on the same signed runtime. This completes Stage 4 of #4, not the complete Wine port or Rosetta-free Megabonk milestone.

Context used: the approved [task plan](../plans/task_m1_4.md), [implementation plan and reuse decisions](../plans/task_m1_4_impl.md), [Stage 3 report](task_m1_4_stage3.md), [root rules](../../AGENTS.md), [runtime rules](../../runtime/AGENTS.md), [test rules](../../tests/AGENTS.md), [host rules](../../host/AGENTS.md), [documentation rules](../../docs/AGENTS.md), [architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md) and [runtime contracts](../../docs/runtime-contracts.md). Reporting follows the installed Hyper-Waterfall v0.3.0 [stage-report](../skills/task-stage-report/SKILL.md) and [daily-board](../skills/todo/SKILL.md) procedures and central stage-report template. No Metal work or new Apple-tooling selection was needed.

Upstream reuse: retain Wine commit `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`, its C/assembly implementation and existing thread startup, TLS/TEB, ARM64 signal/context, vectored exception, virtual-memory and server lifecycle paths. Extend the approved single-allocation executable-memory owner instead of replacing Wine's subsystem or introducing a second `MAP_JIT`. Original fixtures and test controllers exercise those real paths. Rust replacement is neither required nor introduced.

## Artifacts

| File | Change Summary |
|---|---|
| `runtime/wine/patches/0004-darwin-dynamic-memory.patch` | Separate finite mutable-code slots, Windows memory adapter and independent native lifetime observations within the existing single JIT allocation |
| `runtime/wine/patches/0004a-darwin-thread-signal-observation.patch` | Opt-in native thread/signal anchors, controlled dispatch helper and bounded records emitted without formatting or allocation in signal handlers |
| `runtime/wine/patches/series.json` | Append two attributable patches and Stage 4 scope; retain the 17 preceding patch identities and incomplete-port status |
| `tests/wine/fixtures/{threads_pe.c,memory_pe.c,exceptions_pe.c,threads_gateway.S,signal_native.c,stage4_protocol.h}` | Original combined ARM64 Windows fixture and its native observation helper |
| `tests/wine/cases-stage4.json`, `stage4_source.py`, `signal_observer_harness.c`, `test_*` additions and runner test updates | Bounded case definitions, actual original C harnesses, ownership/error injection, strict decoder/evidence rejection and cleanup regressions |
| `tools/wine/{build.py,signing.py,abi_review.py}` | Build/identify the new fixture, bind its actual code labels and authorize the declared development scope |
| `tools/wine/{run_fixtures.py,api_runner.py,verify.py}` | Same-runtime acceptance, independently bound observations, client-before-server cleanup and bounded exit-receipt barrier |
| `tools/wine/{dynamic_evidence.py,exception_evidence.py,stage4_evidence.py}` | Finite dynamic/thread/fault validators and allowlisted public exporter |
| [`task_m1_4_stage4_observations.json`](task_m1_4_stage4_observations.json) | Public counts, source/output hashes, signing scope and explicit qualification limits |
| [`wine-host.md`](../../docs/development/wine-host.md), task/implementation plans and daily board | Approved contributor instructions, retained failure analysis and current stage status |

## Body Change Scope / Lossless Preservation

The only official-document destination changed is the approved existing `docs/development/wine-host.md`. Plans, this report, public observations and the daily board remain under `mydocs/`. Earlier stage reports, the original source inventory, combined source decision, architecture and delivery milestones are preserved. No game files, credentials, authenticated prefixes, saves, signing profiles, private keys or raw diagnostics enter Git.

The new original owner/fixture material retains its notices; Wine integration retains the applicable Wine LGPL terms. The first 17 patches are unchanged. The immutable PE arena and Stage 3 Unix-call entry remain separate from mutable-code ownership and the new fixture-only entry. The new observation path is enabled only for the combined Stage 4 fixture and its controlled child. The general JSON decoder remains unchanged; only bounded, known Stage 4 stdout records accept unsigned 64-bit register/hash values.

Cleanup retains process identity, owned-group and unrelated-sentinel checks. It gives clients a bounded natural-exit interval, with owned TERM/KILL escalation available, and observes every registered client's exit receipt before signaling the server. A missing receipt, unexpected nonzero exit, observer gap or incomplete cleanup remains a failure. No new status-1 or CtrlRoutine-status exception is accepted.

Storage was reclaimed without deleting retained evidence. An audited APFS clone operation replaced 82,470 duplicate file copies with independently writable clone inodes after byte and metadata verification: 80,314 unchanged public Wine source files and 2,156 matching unsigned installation files. Logical duplicate content totaled 7.617 GiB; the measured free-space increase attributable to the operation was 7.681 GiB. All 38 protected receipt hashes and 19 inventories matched afterward, including the prior failures. This is filesystem sharing, not a claim that build outputs were backed up to GitHub. The verification receipt remains private with SHA-256 `402d5ea2e0c8dbec5e525d5d81d1b6c1bb30f47cbe190c59534593519a599784`.

## Verification Results

### Execution context and identity

Actual host: Apple M4 Pro, ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5. The pinned LLVM-MinGW 20260908 tools selected their ARM64 host slices; Clang reported 23.1.1. Bison was the prepared 3.8.2 build. These were instrumented original ARM64 Windows fixtures in real Wine processes on this Mac, not game execution, native Windows reference runs or performance measurements.

The existing device-bound Wine-loader development authorization was revalidated. The loader's restricted cross-architecture claim, public `allow-jit` entitlement and actual 4 KiB code-signature page size passed; ordinary helpers did not acquire those claims. Hardened Runtime and library validation remained enabled. Successful development checks do not establish ordinary-user distribution permission.

| Retained record | SHA-256 |
|---|---|
| Stage 4 build | `b73738833223f8346582a2300c07df03d072e295fd86cc67229223451b029d8c` |
| Signed runtime | `b231bd2e48afb0e1f421536864187daf6e18240c8f6f71f99c1df9b88399c373` |
| Assembly review | `441ca0cdb76f7dc0acd7e0c39d909e0b12ce9fdb49f2c864da73817209398379` |
| Final full suite, `runs-stage4-attempt4` | `8147ec8847d52e6b99fecba3a354c7ff11e4c87cf6b80a11e0cf2b3f42dec241` |
| Final bootstrap, `runs-stage4-bootstrap-attempt2` | `483b7b63ed138be2ad33f258bf2f950ce2ff367298090387520242ffce2318bc` |
| Public Stage 4 observations | `9d01b99e020f444cd0c1f6b800eddc61455f53a79be98c9a9e4ee058a2e8b278` |

The combined fixture SHA-256 is `34ba10714780cca79093b8d521b3ad61fff69d8e086b20d161228cb5d6296b89`. Its signed native observation library is `e8e131339d702e18a528dada5927971cf33b5bc790f128b03355915303ed85d2`. Exact source/producer/patch identities are in the public observations. The dynamic-memory patch is `2a80b367d3fe2b4f86dc5269c74a0dcf55323e0ba50c0e0a6f0618a26239ebb1`; the thread/signal patch is `0af8fff4dffac4f380c970311e40c10a975d3c039a77a752224a606d97120e63`.

### Build, authorization and actual runtime commands

The Stage 4 build and signed bytes were produced once. Subsequent corrections concerned readers and the test controller; the final full and bootstrap suites were rerun with the final controller. Commands below use their actual retained output names; do not overwrite them for reproduction.

```sh
python3 tools/wine/build.py --variant arm64 --inputs .build/task4/inputs --tools .build/task4/tools --output .build/task4/build-stage4 --jobs 4
python3 tools/wine/abi_review.py --build .build/task4/build-stage4 --output .build/task4/build-stage4/abi-review.json
python3 tools/wine/signing.py prepare --build .build/task4/build-stage4 --local-input .build/task4/private/signing.json --output .build/task4/signed-stage4 --require-empty
python3 tools/wine/run_fixtures.py --suite threads-memory-exceptions --runtime .build/task4/signed-stage4 --output .build/task4/runs-stage4-attempt4 --require-empty
python3 tools/wine/verify.py runs --root .build/task4/runs-stage4-attempt4 --suite threads-memory-exceptions --require-complete
python3 tools/wine/run_fixtures.py --suite bootstrap --runtime .build/task4/signed-stage4 --output .build/task4/runs-stage4-bootstrap-attempt2 --require-empty
python3 tools/wine/verify.py runs --root .build/task4/runs-stage4-bootstrap-attempt2 --suite bootstrap --require-complete
python3 tools/wine/stage4_evidence.py --build .build/task4/build-stage4 --runs .build/task4/runs-stage4-attempt4 --bootstrap-runs .build/task4/runs-stage4-bootstrap-attempt2 --output mydocs/working/task_m1_4_stage4_observations.json
```

All commands passed. The build completed 38 commands with all 19 patches and produced 38 ARM64-only native artifacts and 754 PE artifacts, including 752 ARM64 artifacts and two unexecuted x64/i386 controls. The controls were rejected before execution because no translator is qualified. Assembly analysis and independent reader reproduction passed for six declared entry contracts and two mode helpers, bound to actual native bytes. The legacy `instruction_bytes_checked` field counts 158,154 instruction encodings matched to their bytes; it is not a byte total.

The separately required Stage 3 relocation-instruction check was repeated on the actual Stage 4 `lifetime-arm64.dll` using the pinned ARM64 `llvm-objdump`, `inspect_relocation_indirection` and `relocation_image`. Its private receipt, `stage4-research/relocation-instruction-review.json`, has SHA-256 `a86929bed73f9df1872baa1ee4cf0808e5b861aa214ee8e2ca42499821834b6e` and binds DLL, reader, checkers and disassembly hashes. This was a static binary check in addition to actual two-placement execution in the ABI case.

| Final case | Native processes | PE processes | Required result |
|---|---:|---:|---|
| API | 17 | 8 | API, process, architecture, memory-owner, exit and cleanup checks passed |
| ABI | 15 | 7 | Nested x18 callbacks, distinct DLL placements, indirect code/data probes, cookies, lifetime and cleanup checks passed |
| Threads/memory/exceptions | 17 | 8 | All declared operations, independent native anchors, controlled child status and cleanup checks passed |
| Bootstrap normal stop | 3 | 0 | Actual handshake and expected stop passed |
| Bootstrap timeout | 3 | 0 | Expected bounded timeout and owned cleanup passed |
| Wrong-prefix server | 3 | 0 | Expected server refusal and owned cleanup passed |

Every case retained complete required observations and a surviving unrelated sentinel. The final API/ABI/thread cases required only server SIGINT after clients exited naturally. Actual Wine TERM/KILL escalation was not exercised by those successful runs; separate real ordinary-native-process tests covered escalation. Registered-exit receipt ordering is checked independently of process-group membership. The composed cleanup allowance is bounded at 37,000 ms; it is not an observed run duration.

### Thread, signal and exception observations

- Two workers passed distinct TLS/TEB initialization, synchronized work, two injected error returns, Windows thread-handle waits, native exit-entry observations and handle cleanup. Individual POSIX `pthread_join` completion was not instrumented; the tested completion contract is the Windows worker wait and cleanup path. The 34 native anchor parts comprise eight registration parts, 24 signal parts and two exit parts. The field named `native_tid` is the Wine thread ID seen in native code, not a Darwin kernel thread ID; the targeted native thread handle remains private.
- One signal in a labeled guest window, one in a labeled native window and one handshake-controlled suspend/resume passed. Captured PC/SP/x18/x19, host-handler mode and return mode matched independent native records and actual signed instruction ranges. Native signal records are individually below the 512-byte atomic pipe-write limit; formatting and allocation are outside the signal handler.
- One software exception, three recovered access faults, one guard fault/retry and six handler-order checks passed. Hardware faults bound the exact labeled instruction, access kind, owned address, registers and recovery label. For software `RaiseException`, the captured runtime PC equaled `ExceptionAddress`; that captured call-site context is distinct from checking restoration of the caller's register sentinel.
- A separate child observed its declared access fault in both ordered handlers, then deliberately called `TerminateProcess`. Windows status `0xc0000005` (3221225477), signed native status -1073741819 and process exit byte 5 matched. This checks controlled fault-derived termination, not the default unhandled-exception policy or general stack unwinding.

### Ordinary memory and mutable-code observations

The three-page ordinary allocation passed reserve/commit/protect/decommit/recommit/release, exact 4 KiB middle-page changes, intact neighboring sentinels, zeroed recommit and guard retry. The fixed dynamic-code path passed RW publication to RX, instruction-cache flush, execution returning 42, RW rewrite, second RX publication/flush and execution returning 84. Decommit, zeroed recommit, release and compatible reuse also passed.

Dynamic capacity is eight 64 KiB slots (524,288 bytes), separate from immutable PE ownership within one `MAP_JIT` allocation. Its native observations recorded two reservations, three commits, three protection operations, three decommits including implicit release cleanup, two releases, one reuse, two executable publications and four writable transitions. Three committed pages were decommitted; no dynamic allocation remained live at the final observation. These are counts and address-space limits, not resident-memory or performance measurements.

RWX, unsupported dynamic guards/fixed-address or extended allocation forms, and ordinary anonymous RW-to-RX promotion remain refused. The fixed ARM64 code does not qualify concurrent mutation, x64 guest translation or a general FEX JIT service.

### Retained failures and corrections

The original receipts and directories were preserved. Their statuses were not rewritten as successes. The detailed source analysis is in the [implementation plan](../plans/task_m1_4_impl.md#stage-4-retained-diagnostic-history-2026-09-30).

| Retained attempt | Rejection and correction |
|---|---|
| `runs-stage4` | API exited normally but `dynamic_budget_before_execution` rejected the actual loader handoff order. Corrected the reader to require continuation, arena reservation, dynamic budget and PE publication in the observed source-defined order, still before dynamic operations. |
| `runs-stage4-diagnostic1` | A private single-case diagnostic completed operations but rejected a valid unsigned 64-bit code hash under the general 53-bit JSON limit. Added a strict flat Stage 4-only decoder with bounded record/digit sizes, exact known schemas and rejection of duplicate keys, invalid integers and nested data. The original failed diagnostic remains excluded from suite acceptance. |
| `runs-stage4-attempt2` | `unexpected_cleanup_window_exit` rejected a client status 1 after near-simultaneous loader/server signals. Wine's server shutdown/client-abort source paths are consistent with this result, but the exact executed call chain was not conclusively observed. Changed cleanup sequencing instead of accepting that unexpected exit. |
| `runs-stage4-attempt3` | `server_shutdown_before_descendants` rejected server signaling before the final registered exit receipt. Group absence did not establish observer completion; the exit receipt arrived 16.347 ms after the signal in that record. Added a bounded explicit receipt barrier. This timing is an observation-order difference, not a kernel latency measurement. |

Receipt SHA-256 values, respectively: `b4e009dd511b06da32896281f7ccf20d598df15225d6238038597b02a47197d2`, `e544dfa18ddd12efcd6a6314392a06623a51e07f02f2b2c2e7f20187159d9a7b`, `8cfb3e8b7ea4a5b44f986338389c1fb37514ee0c768b088d91f34ded5d23c2e8`, and `2a96be20f13de92c14553038a1bed4f578b868c674b4cef1183c2a8aa3fe9265`. The diagnostic hash identifies its diagnostic result, not a complete suite manifest. The earlier successful bootstrap is also retained; the final bootstrap attempt supersedes it after shared-runner changes.

### Regression, governance and public evidence checks

```sh
python3 -m unittest discover -s tests/wine -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

The final complete Wine test run passed **688 tests in 25.620 seconds**, with no skips. It includes compiled original C/UBSan harnesses, ownership and protection error injection, signal-observer checks, strict integer decoding through actual reader routes, invalid/reordered evidence rejection, and real ordinary-native-process cleanup/escalation/unknown-fork/sentinel tests. These regressions complement the actual Wine cases; they do not substitute for them. Governance and whitespace checks passed after the final document updates.

Private console receipts remain in `.build/task4/stage4-research/`, including `build-stage4-console.log`, `runtime-stage4-attempt4-console.log`, `verify-stage4-attempt4.log`, `bootstrap-stage4-attempt2-console.log`, `verify-stage4-bootstrap-attempt2.log`, `tests-stage4-receipt-final.log` and `export-stage4-console.log`. The exporter independently revalidated the complete final suites, current producer hashes, exact build/signed identities, actual signatures and assembly reader. Separate read-only reviews confirmed source/build and public/raw count/hash consistency and found no remaining must-fix owner/evidence defect or private data in the public artifact. Public output is restricted to reviewed counts, bounded facts, hashes and limitations; it omits private paths, addresses, process/account identifiers, profile material and raw diagnostics.

## Residual Risks

- This is a same-host, instrumented, finite ARM64 fixture result. No native Windows reference execution, independent tester or clean-machine distribution test was performed.
- General SEH/unwinding, arbitrary asynchronous suspension, native-created callback threads, concurrent code mutation and a general translated-code memory service are unqualified. The selected boundary uses Wine-created workers, so a native-created callback thread was not required for this stage.
- Native image snapshots and the opt-in descendant registration protocol do not establish an exhaustive production process/library timeline. The acknowledged fork-to-registration interval remains. Unknown required observations still fail the finite gate.
- The original API/ABI no-Mono policy and restricted build feature selection are unchanged. CLR, networking/authentication, audio/codecs, Vulkan, font rendering and other omitted game dependencies are not qualified by this build.
- Mac-driver execution and final fresh two-variant reconstruction remain Stages 5 and 6. The historical ARM64EC companion has not been rebuilt or executed with Stage 4 changes. The aggregate source decision remains blocked.
- No FEX/x64 translation, Steam, Megabonk, DXMT/rendering, performance/power result or ordinary-user installation/distribution is established.

## Impact on Next Stage

Stage 5 can use the verified native Wine build/authorization and thread/memory/exception regressions while investigating the real `winemac.drv` Cocoa/event boundary. It must create/message/destroy a minimal window 20 times, observe actual native events, guest callback re-entry, ownership and teardown, and rerun affected checks after any driver fix. A guest-only message loop is insufficient. No Metal or game qualification follows from window success.

Keep the finite dynamic owner, immutable PE lifetime, opt-in observers, current cleanup barriers and retained failures intact. Later FEX integration must explicitly resolve dynamic-code concurrency/lifetime and translated thread/exception state instead of treating these fixed ARM64 checks as that contract. Stage 6 must rebuild both final variants and reproduce the declared suites from fresh outputs.

## Approval Request

Review the completed Stage 4 artifacts and results, then approve Stage 5 — Mac-driver Boundary. Stage 5 implementation, final-report publication and PR creation have not begun.
