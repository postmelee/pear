# Task #9 Stage 3: Supervise owned children and refuse uncertain recovery

GitHub Issue: [#9](https://github.com/postmelee/pear/issues/9)
Implementation plan: [task_m1_9_impl.md](../plans/task_m1_9_impl.md)
Stage: 3
Date: October 9, 2026
Status: Implemented and verified; Stage 4 awaits explicit continuation.

## Stage Purpose

Connect admitted immutable fixture payloads to the foreground native supervisor, bounded synthetic observer transport and private crash-refusal journal. The requester explicitly approved Stage 3 with “진행해줘” after the Stage 2 checkpoint. This stage does not authorize profile preparation/recovery implementation or publication.

Context used: root, manager, runtime, host and tests rules; README, official index, architecture, delivery plan, runtime contracts, Issue #9, approved task/implementation plans and review supplements; latest Stage 2 report and reuse record; task/Git workflow and document-location rules. The task-stage-report and repository todo skills use the central templates. Relevant open Issues and worktrees were inspected: master remains `d019a6e`, and the separate #8 work advanced to `b049adf`. Neither was integrated or modified. Work continues in the existing `codex/task9` worktree from `afbb21c`.

## Artifacts

| File/group | Change Summary |
|---|---|
| `manager/src/supervisor.rs`, `supervisor_tests.rs` | Adapted #3 foreground ownership, nonblocking pipes, cancellation, bounded cleanup and direct-child reap; original two pipe-fault assertions plus queue/denial controls |
| `manager/src/observer.rs`, `encoding.rs` | Closed synthetic envelope, request/capture/sequence/exit binding, bounded framed nonblocking transport and direct single-buffer encoding |
| `manager/src/state.rs`, `launch.rs`, `main.rs` | Selected-payload launch, retained version/context leases, explicitly prepared private roots, durable run journal and dirty-context refusal |
| `manager/src/activation.rs`, `contract.rs`, `native.rs`, `lib.rs`, `native/bridge.c/.h` | Narrow existing admission/shape accessors, module wiring and bounded system SHA-256 byte wrapper |
| `tests/manager/case_adapter.py`, `case_mapping.json`, `synthetic_peer.py`, `fixtures/supervision_entry.c` | Original producer/mutation/capture/identity reuse, all 55 explicit mappings, real socket peer and finite owned native wrapper |
| `tests/manager/test_supervision.py`, `test_observer.py`, `test_crash.py`, `build.py` | Current native lifecycle, protocol, cancellation, abrupt death and detached-helper controls; locked build receipts |
| [Sanitized evidence](task_m1_9_stage3_evidence.json), reuse record, implementation plan and daily board | Exact inputs, results, scope and next-stage checkpoint |

## Body Change Scope / Lossless Preservation

Locations match the approved Stage 3 plan. No official product documentation, original experiment source/corpus/history, v1/v2 schema, dependency manifest/lock or original strict-parser bytes changed. The manager retains exact `libc = 0.2.186`; no new dependency, service, custodian or general state framework was added. Stage 2 evidence is preserved rather than rewritten.

Launch revalidates selected media, request/artifact/policy identity and fixture admission, retains the payload root/version lease through supervision, clears inherited environment and accepts only the profile's declared arguments/environment. The owned fixture wrapper alone consumes an explicit work descriptor. Real-runtime authorization remains unavailable, independently of successful synthetic policy evaluation.

Signal handlers only store the cancellation flag. The main loop owns child pipe reads, journal publication, signaling and reap. SIGCHLD disposition is reset before spawning so inherited ignore behavior cannot silently discard the child reservation. The direct child remains unreaped while its owned process group is signaled; no saved-PID or post-reap group cleanup is used. Darwin's original EPERM exception still requires an exited reserved leader and a bounded enumeration containing only that leader. A recheck of at most 250 ms handles transient killed-orphan entries within the same two-second cleanup budget. The actual EPERM stays in diagnostics. Denial outside that exception remains cleanup failure even when the direct child can be reaped.

The stream uses a four-byte big-endian length, frames of 1–256 KiB, an allocated outbound queue capped at 512 KiB and raw adapter buffers below 1 MiB. Length is counted before outbound allocation; encoding writes directly to that buffer. Receive capacity, header and scratch are included in accounting. Parsed bounded contract values are semantic state, not a total-process RSS measurement. Each service pass transfers at most 64 KiB per direction, with a two-millisecond loop sleep. Readiness, partial frames and queued sends use absolute 1,500 ms deadlines; incremental progress does not reset them. The original strict parser supplies its own depth/node/string/byte bounds.

Observer packets bind the exact request digest, fresh capture, run, producer sequence, previous record and completed exit reference. Canonical event bytes travel in the framed session; their references identify those bytes, not an independently persisted public evidence bundle. Synthetic readiness never grants real runtime/module observation authority. Queue-pressure setup that bypasses handshake exists only under `cfg(test)`; actual native CLI cases perform the handshake.

Private publication stages and syncs a journal file, renames it relative to held descriptors and syncs the context directory. `running` precedes spawn; `cleanup_pending` precedes cleanup; `clean` requires direct-child reap, successful owned cleanup and complete required synthetic observation. Failed readiness is conservatively dirty. A free lease or stored owner PID never proves completion. Nonempty v1/v2 operations refuse in this stage: no typed setting implementation exists yet. Empty-operation v2 launch is separately tested; applying settings and canonical prefix alias/replacement checks remain Stage 4.

## Verification Results

Execution context: native ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5, Apple clang 21.0.0, Rust/Cargo 1.94.1; `aarch64-apple-darwin`, minimum build target 26.0. All Cargo execution is locked/offline with the original dependency. The build receipt binds 111 inputs. Actual owned native fixtures ran from manually prepared read-only UDRO media. Timings are correctness deadlines, not performance measurements.

All approved commands passed:

```sh
python3 -B tests/manager/build.py --output .build/task9/stage3 --locked
PEAR_MANAGER_BUILD=.build/task9/stage3 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_supervision.py
PEAR_MANAGER_BUILD=.build/task9/stage3 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_crash.py
PEAR_MANAGER_BUILD=.build/task9/stage3 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_observer.py
python3 -B tests/manager/build.py --output .build/task9/stage3 --locked --rust-tests
git diff --check
```

| Verification | Actual result and boundary |
|---|---|
| Current-manager supervision | 61 pass: all 55 original IDs, mapping completeness, early EOF/final burst, actual finite detached helper, v2 empty-operation success and v2 setting refusal |
| Original corpus safety | Original producer/mutations retained; admission refusals execute no child. Spawned paths check actual identity traces, direct reap, cleanup, output bounds/privacy and unrelated sentinel survival. Nonzero exit 7 and signal 15 remain distinct. |
| Declared mapping differences | Malformed child stdout is nine opaque production bytes and succeeds with independent privacy/count/reap checks. Unknown source and unsupported operations are ineligible rather than malformed contracts. Each difference is recorded in `case_mapping.json`. |
| Observer | 23 pass: exact positive binding, pre-spawn/during-run cancellation, silent/nonreading peer, partial header/body stalls and EOF, byte drip, zero/oversized/malformed frames, disconnect, stale capture, wrong request/run/sequence, post-readiness gaps and wrong completion |
| Native Rust | 10 pass, zero ignored: three ABI tests, both original failed pipe positions, full queue, stalled send, cancellation/exit during backpressure and injected denied group cleanup. Original pipe assertions still require both descriptors closed, no reads from failed blocking pipes, cleanup under two seconds, reap, descendant disappearance and unchanged sentinel. |
| Actual crash | Two pass: supervisor SIGKILL and SIGABRT leave dirty journals; the finite orphan expires independently. Relaunch refuses after lease release, and substitution of the recorded owner with an unrelated live sentinel never signals it or changes the journal. |
| Detached helper | Actual fork/setsid helper records a separate group and expires after 1,500 ms. The synthetic peer refuses coverage; the manager reaps its direct child but reports cleanup failure, incomplete observation and a dirty journal. |
| Admission/activation/foundation regressions | 133, 16 and 12 pass respectively. Activation again verifies actual EROFS, distinguishable dylib execution, descriptor retention, faults, interruption, concurrent selection and preservation. |
| Original contracts/experiment regressions | 154 and 60 pass respectively; original source and historical bytes unchanged |
| Governance/format | Offline governance and diff whitespace checks pass |

There are 471 distinct passing tests, with no final failures or skips. Additional regression commands were:

```sh
PEAR_MANAGER_BUILD=.build/task9/stage3 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_admission.py
PEAR_MANAGER_BUILD=.build/task9/stage3 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_activation.py
PEAR_MANAGER_BUILD=.build/task9/stage3 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_foundation.py
.build/task9/venv/bin/python -B -m unittest discover -s tests/contracts -p 'test_*.py'
python3 -B -m unittest discover -s experiments/manager -p 'test_*.py'
python3 -B tools/check_governance.py
```

Evidence reuse: final all-target Cargo testing changed the foundation and activation-probe binaries, so both affected suites were rerun successfully. All 111 inputs and the manager/original-child/wrapper binary hashes match the lifecycle-tested build; its retained receipt remains separately identified. All 58 original #3 source hashes and ten historical records still match. The old reproduction report's current-tree checker still reports `source_or_history_identity` and `unit_test_accounting` because Stage 1 added contract inputs/tests; comparison consistency passes. That historical current-tree mismatch is not concealed or counted as a current Stage 3 gate pass.

Development failures remain explicit: initial Rust module-path and archive-name shadowing errors; a temporary group-query comparison compile error; pipe-fault failures from waiting for group records before reap and a transient EPERM enumeration race; and pressure assertions corrected when accounting expanded from queued data to total buffer capacity. The final code retains the original lifecycle/assertions with the bounded reservation-preserving recheck. Failed logs are retained locally. Seven owned failed-test scratch roots had their relevant traces moved into ignored Task #9 evidence before removal. Successful fixture volumes were detached and disposable state removed.

## Residual Risks

- No Wine/FEX/Steam/Megabonk execution, real module observation, signing/provisioning grant, game qualification or distribution claim follows.
- The synthetic peer explicitly refuses detached scope; this is not a Wine descendant-discovery implementation. Abrupt manager death has no custodian: the tested fixture orphan expires by its own finite lifetime, with no clean-reaping claim.
- EPERM denial was injected at the owned signal boundary. Stored PID substitution models stale/reused data; actual OS PID reuse was not forced. SIGKILL/abort do not establish power-loss durability.
- Cooperative context/version leases and read-only admission do not constrain hostile same-user or administrator interference. Canonical prefix alias/lock-path replacement checks and compatibility rules remain Stage 4 work.
- Private staging may remain after abrupt death. Preparation, status, recovery, setting application and A/B save persistence are unimplemented. The current CLI requires manually prepared private fixture contexts.

## Impact on Next Stage

Stage 4 must build on the held context/version descriptors, preserve dirty-journal refusal and original error/output bounds, implement typed settings and compatible prefix/context isolation, and validate A/B persistent saves plus manual preservation-first recovery. Keep real runtime authorization closed and carry the current required gates forward; do not infer full observation from fixture transport.

## Approval Request

Review the Stage 3 implementation and evidence, then explicitly authorize Stage 4: scoped mutable state, two fixture profiles and manual recovery. This report does not authorize Stage 4, PR publication or merge.
