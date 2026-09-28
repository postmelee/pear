# Task #3 Stage 3: Equivalent native manager fixtures

GitHub Issue: [#3](https://github.com/postmelee/pear/issues/3)
Implementation plan: [`task_m1_3_impl.md`](../plans/task_m1_3_impl.md)
Stage: 3
Date: September 28, 2026

## Stage Purpose

Implement equivalent bounded Rust and Swift experiments that validate owned fixture contracts and supervise a native child without delegating either responsibility to Python. Establish functional, ownership, privacy and architecture evidence before selecting a production manager language.

## Artifacts

| File | Change Summary |
|---|---|
| `experiments/manager/rust/` | Native strict JSON parser, fixture contract/digest/path validation and direct process supervision; exact `libc` dependency and Cargo lock. |
| `experiments/manager/swift/` | Dependency-free Swift package with independent parser, contract validation, descriptor access and `posix_spawn` supervision. |
| `experiments/manager/fixtures/child.c`, `native_bridge.c`, `native_bridge.h` | Owned ARM64 child modes and a narrow fixed-width process-creation identity C ABI. |
| `experiments/manager/fixtures/cases.json` | 55 shared functional, negative, ownership and privacy cases with explicit reference-validator context/expectations. |
| `experiments/manager/build.py`, `run_cases.py`, `test_prototypes.py` | Locked builds, native-slice/dependency inspection, actual source/binary identity checks, independent oracle, bounded corpus and ten harness regression tests. |
| `experiments/manager/dependencies.json` | Observed toolchain, exact crate/source/license/build-script review, system-library and FFI boundaries. |
| `experiments/manager/comparison-plan.json`, `README.md` | Frozen future comparison inputs/rubric and executable reproduction instructions with explicit limits. |
| `mydocs/plans/task_m1_3_impl.md`, `mydocs/orders/20260928.md` | Stage authorization/completion and parallel-task status. |
| `mydocs/working/task_m1_3_stage3.md` | This bundled report. |

## Body Change Scope / Lossless Preservation

Existing version 1 schemas, Python reference-validator implementation, contract examples, Stage 1/2 reports and source audit are unchanged. The new native experiments implement a declared four-record subset; they do not replace the seven-contract reference validator or become a production manager. No upstream runtime, Steam, proprietary game, authenticated prefix or private diagnostic was committed. Raw build logs, executable artifacts, fixture source archives, process identities and per-run records remain ignored under `.build/task3/prototypes/`.

Only the approved experiment and workflow-document locations were used. English is used for new documentation, comments and default output. The predetermined future incremental-build comments are inert Stage 3 preparation; no Stage 4 measurement or language decision was performed.

## Verification Results

The final source revision passed all planned commands:

```bash
python3 experiments/manager/build.py --output .build/task3/prototypes --locked
python3 experiments/manager/run_cases.py --build-root .build/task3/prototypes --all --oracle .build/task3/venv/bin/python
python3 -m unittest discover -s experiments/manager -p 'test_*.py'
git diff --check
```

| Check | Actual result and limit |
|---|---|
| Controlled native build | Passed for C fixture, Rust and Swift. Rust uses locked/offline Cargo; Swift has no external packages. Every regular extracted `libc` source file is compared with the verified crate before building. Ambient Cargo configuration is rejected. |
| Static architecture/dependency inspection | `file`, `lipo -archs` and `otool -L` passed; all three executables have only an ARM64 slice. This alone is not execution proof. |
| Common corpus | **55 cases × 2 candidates = 110 passing invocations** with identical declared outcome expectations. The general Python oracle runs independently in the harness. |
| Owned execution | 26 child launches; both candidates report their exact direct child reaped and cleanup passed. All 28 child/descendant creation-identity traces independently disappear. |
| Unrelated processes | Sentinel remains alive at every check; no global process-name cleanup is used. |
| Native running state | Every candidate result reports ARM64 and `translated: false`; every executed child's trace follows its own native/translation check. These are owned fixture processes, not a complete runtime process tree. |
| Time/output/privacy | All cases finish within the outer deadline without watchdog intervention. Output is bounded; no synthetic secret, private bundle path or raw child stream is emitted by a manager. |
| Harness regressions | Ten tests passed, including rejecting a false runtime claim, unknown result fields, missing reaping, wrong result version/exit, deleted source with an old binary, and inconsistent fixture byte identity. |
| Whitespace and frozen plan | `git diff --check` passed. Comparison plan defines both source edits, release builds, sample counts/order, measurements and qualitative gates before measurement. |

Final combined classification counts:

| Classification | Invocations |
|---|---:|
| `success` | 10 |
| `nonzero_exit` | 2 |
| `signal_exit` | 2 |
| `timeout` | 4 |
| `output_limit` | 4 |
| `child_output_invalid` | 2 |
| `observer_not_ready` | 2 |
| `observer_gap` | 2 |
| `spawn_failed` | 2 |
| `invalid_contract` | 76 |
| `ineligible` | 4 |

Negative cases include raw/nested escaped duplicate keys, malformed UTF-8, BOM, floats/nonfinite/oversized numbers, boolean version, unknown fields/kinds/versions, wrong hashes/kinds/family/cache/entry, source/build/terms/payload mutation, traversal/absolute/percent/tilde paths, symlinks, FIFO, hardlink aliases, overlapping state roots, untrusted executable pins, unsupported operations, research context, wrong purpose and string/key/depth bounds. Functional cases include spaces/Unicode arguments, environment isolation, EOF stdin, nonzero/signal exits, delays, excess stdout/stderr, malformed child output, synthetic secret redaction, descendant-held pipes and missing readiness/gaps.

The narrower executable subset rejects identical hardlinked blob aliases even though the general reference validator permits them. It also rejects valid setting operations and unknown provenance. The research case validates its records using the oracle's research context while requiring fixture execution to remain ineligible. These scope differences are declared in the corpus and README; full schema parity is not claimed.

### Native lifecycle finding

On the tested Darwin version, an exited but unreaped child can be absent from `proc_pidinfo`, and signaling its zombie-only process group can return `EPERM`. Each native supervisor keeps the leader unreaped, confirms the exact exit with `waitid(WNOWAIT)`, and accepts this `EPERM` only if a bounded native `proc_listpids(PROC_PGRP_ONLY)` query finds no group member other than that leader. Unknown, truncated or nonempty-other-member observations do not pass cleanup. A pipe-holding descendant reaches the deadline, is terminated with its owned group, and its creation identity disappears before the harness accepts the run. The identity C bridge does not implement this supervision for either language.

### Verified input/output identities

The ignored `build.json`, `build-log.json`, each `cases-*/results.json` and latest `case-results.json` retain exact local records. Public identifiers below contain no raw private paths or PIDs.

| Artifact | SHA-256 |
|---|---|
| Shared corpus | `24c3be1103a5a6630f7c71b388298f420edde3ddfa70156874cd7e4027b0d63a` |
| Final case result | `9b922edb162a2f1e209bb2f75d978e85ecce597805c6b2fe4d49c643a53ea117` |
| Owned native child | `6ab833185c1c5fb43ff588df57b70973de4f405ddf7e6e35d0430bcee2e8477f` |
| Rust candidate | `854313598bd8183dddbcfff9ebc46fa14eec6d4acfe3241dac4794c44d81bf0e` |
| Swift candidate | `f85f7ea3569128ce7564ab7b2886461c7592a94a6f5529878c2e4b29c64f63aa` |

Observed environment: Apple M4 Pro; macOS 26.5.2 (25F84); Xcode 26.6 (17F113), SDK 26.5, Apple clang 21.0.0; Rust 1.94.1/Cargo 1.94.1; Apple Swift 6.3.3. Rust declares `libc =0.2.186` (MIT OR Apache-2.0), with no active transitive crate dependency. Archive, all 360 regular extracted files, license texts and build script were reviewed; source hashes and review boundaries are in the dependency inventory. Both candidates use Apple system CommonCrypto/libproc interfaces; Swift additionally links Foundation and system Swift libraries. These are observed experimental inputs, not Pear release pins.

During review, an inert comparison marker was initially rejected by automatic approval review as possible Stage 4 work. Supplying the existing Stage 3 requirement to freeze future comparison edits resolved the rejection; no later-stage work or new user approval was inferred.

## Residual Risks

- Concurrent bundle mutation is unsupported. Descriptor reads, hashes and immediate executable checks do not eliminate the remaining pathname-execution race. #9 must implement immutable runtime and mutable-state ownership.
- The outer watchdog cannot guarantee cleanup of a fixture's separate process group after an unexpected manager hang. Such a run fails, records unresolved identities and receives no cleanup claim. All published passing cases completed without watchdog intervention.
- Fixture observer flags, owned process traces and static dependencies do not establish real module coverage, Steam behavior, game compatibility, distribution signing or complete Rosetta-free runtime operation.
- The source/build configuration is real owned fixture evidence; signing references remain synthetic. No signature or release approval follows from their contract fields.
- Custom parser maintenance and explicit FFI/unsafe surfaces exist in both candidates. Functional success does not choose a language or establish a performance advantage.
- Local build hashes may change with build paths/compiler metadata. This is one-host functional evidence; clean-output reproduction and language comparison remain later stages.

## Impact on Next Stage

Stage 4 can apply the frozen comparison plan: three clean and three predetermined native-source incremental builds per candidate, five unscored warmups and 30 alternating fresh launches each, plus packaging, FFI, testing and maintenance review. Measurements must retain all valid samples and observed limits. Functional or privacy failures block adoption claims. The resulting language decision and #9/#10 obligations must remain separate from game runtime support.

## Approval Request

Approve the Stage 3 artifacts and verification, then authorize Stage 4 controlled comparison and the manager-language decision in the approved document location. Stage 4 does not authorize game benchmarking, a production launcher or runtime qualification.
