# Implementation Plan: Native supervisor and versioned profiles

Task plan: [task_m1_9.md](task_m1_9.md)
GitHub Issue: [#9](https://github.com/postmelee/pear/issues/9)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Branch: `codex/task9`
Date: October 8, 2026 (Asia/Seoul)
Status: implementation plan and Stage 1 approved on October 8, 2026 through an authorized relay, including the three review supplements below. Commands and artifacts below define the approved stages; actual Stage 1 results are in its report, and later-stage execution remains planned. Stage 1 is implemented and verified; see the [Stage 1 report](../working/task_m1_9_stage1.md). Stage 2 was explicitly approved on October 9, 2026 and is implemented and verified; see the [Stage 2 report](../working/task_m1_9_stage2.md). Stage 3 was explicitly approved by the requester on October 9, 2026 and is implemented and verified; see the [Stage 3 report](../working/task_m1_9_stage3.md). Stage 4 was explicitly approved on October 9, 2026 and is implemented and verified; see the [Stage 4 report](../working/task_m1_9_stage4.md). Stage 5 was explicitly approved on October 9, 2026 and is implemented and verified; see the [Stage 5 report](../working/task_m1_9_stage5.md). Stage 6 awaits explicit continuation.

## Context and Authorization

Apply the task plan's requirements, document-location judgment, #3 reuse matrix, Whisky pin/licenses, exclusions and #9/#10 boundary. Root, host, runtime, tests and docs rules, task/Git workflow, conflict rules, document structure, and the central implementation-plan template have been read. Relevant specifications are [runtime contracts](../../docs/runtime-contracts.md), [manager decision](../../docs/decisions/manager-language.md), [architecture](../../docs/architecture.md) and the [delivery plan](../../docs/delivery-plan.md). The latest completed #3 stage/final reports and exact prototype/oracle/build inputs remain the starting implementation, not a reason to repeat language selection.

The requester authorized this planning through the originating chat on October 8, including three specific supplements: compare actual implementation choices for new common functions, examine useful small portions of external implementations, and choose the minimum crash/activation/recovery structure. The subsequent requester instruction approves the supplemented detailed plan and Stage 1 implementation, verification, report and bundled commit, not later stages. Stage reporting will use task-stage-report/todo at the approved checkpoints; final publication uses task-final-report only after all stages. No Apple Metal skill applies: no shader, GPU, drawable or metal-cpp work is planned.

Base remains `2e0985b` plus task-start `a6e60a3`. Updated remote #6 integration is `d019a6e` ([PR #38](https://github.com/postmelee/pear/pull/38)); its final report was inspected from the fetched commit, not borrowed from a private build. #9 remains independent of #6 and does not alter its FEX sources/runner/artifacts. Before final integration, inspect the then-current source/docs/board diff and obtain the repository-required merge/rebase decision. No such integration is authorized in this planning update.

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Reuse, native foundation and explicit contract evolution | Native parser/package foundation, version 2 schemas/oracle adapter and selected reuse record | Locked inputs, original v1 checks, v2 shape/eligibility negatives and ABI applicability |
| 2 | Native admission and immutable activation | Descriptor/hash/policy consumers and atomic activation selection | Real at-use substitution, read-only enforcement, interruption and payload identity |
| 3 | Foreground process supervision and crash refusal | Adapted #3 lifecycle, signals, incomplete journal and observer interface | 55-case adaptation, both pipe faults, cancellation, manager death/detach and unrelated sentinels |
| 4 | State, profile isolation and manual recovery | A/B profiles, exclusive prefix mutation and preservation | Two-profile concurrency/settings/prefix/saves, busy/dirty/incompatible refusal and old-data hashes |
| 5 | Researched Megabonk profile and official guides | Honest profile/provenance, CLI/setup/recovery and interface documentation | Generic consumption, unknown refusal, fixture command walkthrough and local links/privacy |
| 6 | Fresh construction and handoff | Exact final native fixture evidence, reports and board | Fresh output, all required current checks and complete acceptance mapping |

## Actual Implementation Choice Matrix

Selected deployment/build profile: native Apple Silicon/macOS 26.5.2, Rust/Cargo 1.94.1, Apple clang/Xcode 26.6/SDK 26.5; initially retain #3's macOS 26.0 build target. These are development inputs, not general support/minimum-OS or distribution claims. No Rust dependency beyond #3's exact `libc = 0.2.186` is selected. Preserve its existing checksum `68ab91017fe16c622486840e4c83c9a37afeff978bd239b5293d61ece587de66` and MIT OR Apache-2.0 notices.

| Necessary function | Options actually compared | Selected API/module and applicability | Pin/terms and preserved verification / new difference |
|---|---|---|---|
| Prefix/version lease | Handwritten `flock`; std file locks; rustix/nix wrappers; marker/PID file | `std::fs::File::try_lock`, `try_lock_shared`, `unlock` on one descriptor-relative opened inode. Use nonblocking acquisition; distinguish WouldBlock from I/O error. No clone/reentrant acquisition while locked, and close-on-exec ownership is explicit. | Installed Rust 1.94.1 standard library; stable locking API since 1.89. Planning native probe passed contention/release and demonstrated advisory writes. Production concurrent ownership/dirty-state checks remain new; locks do not constrain arbitrary writers or establish PID generations. |
| Temporary files and staging directories | New random-name/cleanup utility; tempfile; Python tempfile; existing Darwin API | Python `tempfile.TemporaryDirectory` for test scratch. Darwin `mkdtempat_np` beneath an already opened owned directory for persistent activation/journal staging, wrapped by a small header-checked C function. File writes use `openat(O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600)`; directories 0700. | SDK declares mkdtempat_np since macOS 10.13; native 0700 probe passed on current host. No new randomness generator or general TempDir class. tempfile 3.23.0 was reviewed, not selected: its destructor cleanup does not solve abrupt death, and persistent recoverable staging requires explicit ownership anyway. Retain failed owned staging, delete only proven disposable scratch. |
| Descriptor traversal and lifetime | Copy/rewrite filesystem subsystem; #3 primitives; rustix/nix wrappers | Adapt #3 `Bundle::directory/open/read`, use `File`/`OwnedFd`/`AsFd` ownership, existing libc `openat`, `fstatat`, `renameat`, `unlinkat`, `fcntl`, `fchdir`. Put conversions/errno handling in `manager/src/fs.rs` plus the existing C ABI bridge. | Same libc pin and SDK. Keep no-follow/nonregular/cycle/alias tests. rustix/nix would replace an existing boundary while libproc/C bridge remains required; no new crate removes the at-use or generation policy. Add only missing publication/state calls and their observable failure controls. |
| Streaming SHA-256 | #3 one-shot CommonCrypto; imported Swift hashing loop; Rust hash crate; new hash algorithm | Retain exact-byte digest meaning; header-checked `CC_SHA256_Init/Update/Final` in a fixed small C wrapper with a 1 MiB chunk buffer and caller-owned descriptor/output. Reuse Python hashlib as independent oracle. | macOS system CommonCrypto/SDK; do not copy or implement SHA. Native split `abc` vector passed. Add multi-chunk, changed-file, read-error and size-bound controls. No handwritten C context layout in Rust, no raw data in errors. |
| Strict JSON and record graph | #3 parser; serde/other decoder; new parser/schema framework | Copy #3 `json.rs` unchanged initially; adapt #3 graph/hash/path logic and use typed error mapping around its existing result boundary. No decoder replacement solely to add a library. | Existing owned source; record provenance to #3 commit/file. Preserve duplicate keys, Unicode, numeric/depth/node bounds and old malformed-input corpus. Native v2 shapes and policy gates are the new work. |
| Spawn, pipes and reap | #3 Rust supervisor; complete Whisky Process wrapper; rustix/nix rewrite; new service/custodian | Adapt #3 `Command`, `env_clear`, explicit argv, nonblocking drain, waitid WNOWAIT leader reservation, identity bridge and bounded cleanup. Use narrow cancellation flag bridge and std monotonic time. | Same libc/C/system interfaces; no new FFI/process framework. Retain both real pipe faults, descendants, direct reaping and sentinel controls. Cancellation, abrupt death refusal and detached ambiguity are explicit added cases. |
| Environment/settings resolution | #3 argument/env collections; Whisky multi-layer resolver; new configuration engine | Retain flat approved profile values plus manager-owned WINEPREFIX/work-root bindings. No user/callsite override cascade is needed. Implement only known typed setting keys and descriptor-relative paths. | No extra dependency. Duplicate/reserved keys and unsupported settings fail. A/B fixtures prove actual different values and outputs; do not implement a second layered resolver that the CLI does not need. |
| Atomic local state/recovery | New database/updater/service; tempfile persistence helpers; std I/O plus existing syscall boundaries | A bounded private journal and activation pointer written by create-new, file sync, descriptor-relative rename and directory sync. No DB, daemon, network updater or automatic migration/restore. | std/libc/SDK. Preserve actual write/sync errors; interruption never rewrites the previous usable selection. Power-loss durability beyond observed system guarantees is not presumed. |

Candidate references reviewed for the table: [std file locking](https://doc.rust-lang.org/std/fs/struct.File.html#method.try_lock), [tempfile 3.23.0](https://docs.rs/tempfile/3.23.0/tempfile/), [rustix 1.1.2](https://docs.rs/rustix/1.1.2/rustix/), [nix 0.30.1](https://docs.rs/nix/0.30.1/nix/). Crates.io version metadata records tempfile MIT OR Apache-2.0/Rust 1.63; rustix Apache-2.0 WITH LLVM-exception OR Apache-2.0 OR MIT/Rust 1.63; nix MIT/Rust 1.69. None was fetched, compiled, adopted or added to Cargo. These are fixed review candidates, not a claim that they are the newest releases. If a selected narrow boundary proves substantially harder than the reviewed wrapper, revisit that boundary with explicit dependency/source/feature/target verification rather than introducing libraries preemptively.

### Planning probes: actual result and limits

Two small standalone probes outside the repository passed on the current Mac:

- Rust source SHA-256 `6fa65a5a592935f6bb15da4952624a250d686154567b186837073a29c2dce9d8`: Rust 1.94.1 native ARM64 build; separate-process lock contention, successful write by a non-lockholder, unlock and drop-release.
- C source SHA-256 `58741ea03f49a9d13ce71ae6c2a929987f6d29a8e0dc2991367b9dad5b41bdcf`: native ARM64 build with SDK headers; mkdtempat_np creates mode 0700 beneath an owned FD; incremental CommonCrypto equals the standard `abc` digest.

The local temporary outputs are owned by task9 planning and retained until Stage 1 incorporates the relevant API checks. They are not repository source, a supervisor stage, lease-crash proof, runtime immutability or signing/game qualification. Stage 1 creates task-owned evidence from the implemented boundary; do not claim these probes tested it. The exact libc source/archive was not found at the checked default Cargo registry paths; acquisition remains a Stage 1 prerequisite. Do not read/modify another task's dependency, build or prefix to fill that gap.

## Small External Portions: Cost and Reuse Decision

Keep the task plan's exact Whisky commit `3abfbae945e3400caaa13cf2e78fe5a187a1405b`, component headers and GPL-3.0-or-later review. Do not acquire another broad source/hash inventory. The comparisons below focus on code that could otherwise be newly written.

| Useful small boundary | Whole module / partial direct adoption / narrow change / #3 comparison | Chosen reduction and remaining verification |
|---|---|---|
| EnvironmentBuilder's deterministic merge/resolve portion | Whole package brings app/resource/dependency context. A standalone Swift slice still needs a Swift build plus serialized/C interface and duplicate-key/allowlist boundary. Narrowing its layers does not remove those obligations. #3 already supplies argv and an empty inherited environment; this CLI needs one approved profile layer only. | Retain #3 and std collections; do not write a layer/provenance engine. Record scenario reference, not code adoption. Test reserved WINEPREFIX/work-root and duplicate environment keys. If later real multi-layer UI requirements appear, evaluate the original Swift boundary then. |
| WhiskyWineInstaller's `sha256(ofFileAt:)` loop | Whole installer has incompatible mutable installation. The isolated Swift loop is small but needs a helper/FFI around CryptoKit. Translating it to Rust is not an attribution escape and still duplicates hashing glue. The existing CommonCrypto dependency supplies incremental functions directly. | Use system streaming hash, not a new algorithm or Swift helper. Retain unreadable/mismatch/missing-payload scenarios and compare with independent hashlib on exact files. Source-code adoption is none. |
| Process+Extensions trailing-output/EOF fixes and tests | Full stream implementation logs raw data and can wait on retained pipes. Copying just handlers retains Foundation/callback concurrency and loses #3's byte/deadline boundary. Direct Swift tests would build a different process path. #3 already drains/reaps the actual child. | Keep #3's path; add only early-EOF and final-burst scenarios informed by `ProcessExtensionTests.swift`, using original C fixtures/companion modes. Preserve byte counts, no spin, deadlines and both pipe fault assertions. No duplicated Swift test target. |
| ProcessRegistry register-before-spawn/per-prefix cases | Stored-PID cleanup is incompatible. A direct register-only Swift portion adds global lock/object identity and a new bridge while needing Pear generation/lease state anyway. Its per-bottle tests show useful isolation triggers but do not independently prove lifecycle cleanup. | Retain #3 generation/reservation; use two actual fixture profiles and std leases. Reuse the registration/isolation scenarios without importing registry code or treating its tests as Pear passes. |
| BottleOperations rollback on failed move/partial duplicate | Full UI registry operations are excluded. A small snapshot helper is tied to bottle metadata; copying it would not replace descriptor publication or cross-process lease handling. | No move/export/duplicate feature. Atomic activation metadata and retained old data replace the need for new general copy/rollback code; simulate interruption at each publication boundary. |

Direct Whisky source/test adoption is **none in this implementation plan**; useful design and scenario references remain explicitly credited. This follows concrete elimination of unnecessary layers/helpers, not a language-based blanket rejection. Standard/system implementations are actual adopted implementations; most native parser/supervisor code comes from #3. New Pear code is limited to policy, version-specific glue, activation/state ownership and missing lifecycle cases. Any later direct Swift adoption preserves original language/headers/provenance and combination terms, and requires review of changed architecture/license scope. No GPL-to-Rust translation, Pear license selection or upstream submission is authorized.

## Minimum Runtime Structure and CLI

### Process and crash choice

| Structure | Required behavior | Cost / limitation | Selection |
|---|---|---|---|
| One foreground supervisor with #3 cleanup and only Drop/lease release | Normal exit/cancellation works | SIGKILL can leave children and makes a released lock misleading | Insufficient alone |
| One foreground supervisor plus durable running/cleanup-pending journal and refusal on uncertain previous run | Normal cleanup remains owned/reserved; abrupt death cannot yield clean status or automatic prefix reuse | Does not automatically reap/terminate after its own SIGKILL; recovery preserves the old prefix and uses a new context unless completion is independently established | Selected minimum for #9 CLI/manual recovery |
| Controller plus per-run custodian watching a private channel | Could clean children after controller death while retaining leases/reservations | Adds another executable role, crash surface, control protocol and test set; custodian SIGKILL still needs journal/refusal | Deferred unless a concrete required scenario cannot be satisfied by the selected documented crash semantics |

The selected design is one foreground manager process, no resident service or management IPC. SIGINT/SIGTERM initiate bounded owned cleanup through a small async-signal-safe cancellation boundary. A running marker is durably published before spawn; it becomes clean only after exact direct-child reap, required owned cleanup and final journal publication succeed. A failed final write leaves an incomplete state.

SIGKILL/abort/panic-abort does not guarantee cleanup. The next invocation must refuse the dirty context even if its file lock is free or the recorded PID is absent/reused. It does not signal a persisted PID after comparing a generation, clear a marker based on liveness alone, or claim orphan reaping. Manual recovery creates a fresh context with preserved old data or selects a previously clean compatible version/context. No automatic save copying/restoration. Finite fault fixtures have independent harness ownership/expiry so this negative test does not leave unbounded children; expected incomplete state is a tested refusal, not a passing cleanup result.

Owned groups remain reserved until cleanup and reaping. A setsid/detached helper is not assumed to belong to the owned group. Declared fixture session/identity evidence tests the boundary; unprovable detachment leaves an explicit cleanup failure/unsupported association and quarantined context. No global scan/kill. A real Wine adapter can use exact owned-prefix server control only after admission and evidence establish that prefix/server/runtime relationship; unavailable real helper proof cannot appear as complete runtime supervision.

### Activation and execution choice

Use an already prepared, OS-enforced read-only local payload (for example a manually created/attached read-only UDIF image using existing macOS hdiutil). The manager does not download, extract, create a general package store, manage volumes or install a background service. Its activation operation verifies the mounted bundle, stages a small version-selection descriptor in its owned state, and commits that selection atomically. Previous versions remain present.

Native `fstatfs` must report read-only for the opened payload root; expected mount/device identity and complete selected payload digests are checked again at use. Writable directory plus chmod/locks is rejected for execution, even with correct hashes. Independent system libraries stay separately classified; reject mutable external payload dependencies/RPATH escapes rather than infer a complete immutable closure from the main EXE alone.

Retain the opened read-only root descriptor and launch `./<declared artifact entry>` after an async-signal-safe `fchdir` in #3's existing pre-exec boundary. Do not reconstruct the imported absolute path or search PATH. Mutable roots are explicit arguments/manager-generated environment bindings, not the executable lookup directory. A task9 fixture entry wrapper may enter its owned mutable work root after native entry before delegating to the unchanged #3 child, preserving its trace/argument scenarios. This wrapper is fixture-only source, not a game-specific manager branch.

Stage 2 must prove this exact lookup under ancestor rename/replacement and concurrent activation using the actual built child and OS read-only payload. Manual image setup uses explicit argv, small owned payloads and bounded task9 harness capture, never shell interpolation or other task images. A failed/missing hdiutil mount, noexec/read-only check or library-closure proof is an unavailable/refused required case; never substitute writable execution and claim that the race is closed. No launch qualification follows before this gate passes.

Threat boundary: protection of activated payload pathname/contents and coordination of Pear-owned operations under normal user permissions. It does not constrain an administrator, malicious same-user replacement of backing media/mount namespace, or a hostile game outside the declared storage boundary. Hashes/advisory locks cannot supply those guarantees. Copying inputs to private staging does not erase external writable handles. Read-only backing-media integrity/owner prerequisites must be documented and checked for the declared local setup; ambiguous media is rejected. Real release packaging or stronger isolation requires its separate task.

### Commands and local protocol

| Command | Concrete operation | Mutations / refusal |
|---|---|---|
| `inspect --bundle-root PATH --entry REL --context research|fixture|runtime` | Bounded native structure/relationship inspection | No execution; unknown use eligibility remains explicit |
| `activate --bundle-root PATH --entry REL --state-root PATH --policy PATH` | Verify read-only local payload and independently selected exact policy; atomic version selection | Small owned metadata only; old selection preserved on failure |
| `prepare --state-root PATH --profile REL --context-id ID --policy PATH` | Create an owned compatible prefix/data context and bounded implemented settings | Reject overlap, unsafe path, unknown family and busy/dirty existing context |
| `launch --state-root PATH --request REL --policy PATH --observer-fd N` | Revalidate selected inputs/leases/readiness, launch and reap foreground owned child | Explicit argv/env; SIGINT/SIGTERM cancellation; no process-control service |
| `status --state-root PATH --context-id ID` | Inspect local bounded journal/lease state | Released lock or missing PID is never reported as confirmed cleanup |
| `recover --state-root PATH --new-context ID --profile REL --policy PATH` | Allocate a new compatible context while preserving the old incomplete one | No automatic migration, restore, save deletion or persisted-PID signaling |

Paths/IDs are exact local operands, not downloaded commands. Exit convention follows #3's distinctions: 0 completed requested operation; 1 invalid input; 2 CLI misuse; 3 ineligible/busy/unsupported request; 4 operational failure/cancellation/cleanup incomplete. Output is a bounded closed diagnostic envelope with version/context, phase/reason, numeric error, byte counts and ownership outcome; secret values, raw streams and personal roots stay private. Public contract events/failures remain their existing record kinds.

The sole new transport boundary is #9's existing observer interface obligation, not management IPC: a caller-selected inherited connected descriptor carries bounded length-framed UTF-8 request/ack/event records (maximum 256 KiB per frame). Bind ack to exact request bytes/run/capture and producer sequence. Unknown/stale ack or EOF before readiness prevents covered spawn; later loss/gaps remain incomplete. No boolean readiness/gap flag can qualify a real runtime. The Python fixture peer is synthetic, uses the existing event factory and has no real module collection authority. #10 supplies actual observation and trusted readiness backend later.

### Bounded observer adapter (Stage 3 implementation)

Use a connected nonblocking descriptor and a 4-byte unsigned network-order length followed by UTF-8 JSON. Reject zero or lengths above 256 KiB before allocating a body. Retain at most one partial incoming frame (256 KiB plus header), at most 512 KiB queued outgoing bytes including headers, and at most 1 MiB total adapter buffers. Queue overflow or allocation failure is an explicit observation failure; never silently drop an event. Do not add a general transport framework.

Readiness has an absolute monotonic 1,500 ms deadline from handshake start, bounded also by the launch deadline. Every later frame assembly and queued send has an absolute 1,500 ms deadline from its first byte/enqueue; partial progress never extends it. Service at most 64 KiB in each direction per loop pass, with at most a 10 ms poll wait, while continuing child stdout/stderr drains, cancellation, execution timeout and owned cleanup. A silent/slow/non-reading peer, partial EOF, malformed length/JSON, EPIPE or connection loss fails readiness before spawn or marks observation incomplete after spawn and initiates the existing bounded owned cleanup. Final notification cannot extend the cleanup deadline; failed delivery remains recorded locally.

Stage 3 `test_observer` includes no response; partial header and body followed by stall; drip feeding across the absolute deadline; zero/oversized frames; peer stops reading until the send queue reaches its bound; cancellation and child exit during that backpressure; disconnect/partial EOF. The independent harness asserts finite termination, actual drain/reap/cleanup outcomes and unrelated sentinel survival, plus incomplete observation rather than success. Stage 1 implements no transport or supervision loop.

## Explicit Version 2 Contract Scope

Keep the seven record kinds and acyclic digest/ownership model. Preserve all v1 schema/example bytes and the v1 reference evaluator's public behavior. Add `runtime/contracts/v2/` with the same seven schema names/shared definitions and a version-specific local registry. It derives unchanged shapes from v1 rather than inventing another profile system. A bundle uses one supported contract version consistently; mixed/reachable reference versions are refused. v1 native launch supports the explicitly declared existing fixture subset; newly executable settings use v2. Unknown versions remain rejected.

| Change | Concrete representation / gate |
|---|---|
| Profile unknown runtime facts | v2 `compatibility_family` and `renderer` permit null for inspectable unselected profiles. Required launch identities remain non-null and compatible. |
| Save/path evidence | Keep executable `save_paths` relative to the separately resolved saves root. Add closed `save_inventory_status` (known/unknown plus bounded reason) and `path_observations` (kind settings/saves, status observed/unknown, typed Windows-user-relative path or null, reason, evidence). Observations do not grant a writable mapping or authorize a save operation. |
| Profile provenance/features | Add closed bounded provenance entries (primary URL, review date, scope/detail) and feature observations (ID, passed/failed/unknown/unsupported/untested, evidence). Self-declared feature success never supplies a qualification overlay. Current Megabonk observations remain dated/untested. |
| Environment and typed settings | Retain existing two fixture keys for submitted environment and existing setting vocabulary. WINEPREFIX and the fixture work root are manager-owned resolved bindings; reject submitted overrides. No arbitrary environment/registry/script/download/migration operations. v2 implements only allowlisted `fixture_flag` settings initially; `dxmt_log_level` executes only if its actual adapter/path semantics are implemented and tested, otherwise refuses. |
| Streaming payload bounds | v2 retains 256 KiB/4 MiB JSON, depth/node/reference/string bounds; declares 8 GiB per blob and 64 GiB aggregate streamed bytes. v1's 64 MiB/256 MiB bounds are unchanged. Quotas/path/regular-file checks precede reads; bounded chunk memory is not whole-file allocation. |
| Policy/eligibility | External exact input approval, actual host/signing scope, source/build evidence and purpose-specific gates stay mandatory; only supported_launch additionally requires prior matching game qualification. Fixture/research promotion, partial disclosure or incomplete observation cannot pass. Version transition changes bytes and requires new policy/evidence, not grandfathered qualification. |

`tests/contracts/validate_v2.py` is a narrow version-specific adapter using existing strict parsing, SafeRoot, reference and eligibility primitives; `fixture_factory.py` remains the base fixture producer. Keep v1 evaluation unchanged; do not fork a second generic validation framework. Native contract consumers implement the matching applicable shapes/eligibility; Python is an independent checker, never a hidden runtime subprocess. Required runtime execution authorization is a current independently approved input/host receipt bound to exact payloads/scope, not merely submitted signing fields or a successful codesign invocation. If the actual producer/grant is unavailable, runtime launch refuses; no new entitlement/provisioning path is included.

The future v2 files and exact closed schema fields above are part of this implementation-plan approval request. Stage 1 verifies the shapes before later execution. If that concrete shape needs an additional operation, policy authority or ownership change, report and update the plan before implementation. A different semantics-preserving file organization is routine; broad scope/contract changes are not.

### Purpose-specific admission semantics

| Purpose | Required candidate gates | Prior game qualification | Required positive/negative controls |
|---|---|---|---|
| `inspect` | Strict version, structure, bytes and relationships | None | Unknown research profile remains inspectable; no execution permission follows |
| `fixture_launch` | Fixture context and the declared complete owned fixture subset | None | Fixture execution cannot authorize a runtime-context launch |
| `qualification_run` | Runtime context; complete source/build/host/signing/family/cache/ownership and observer prerequisites; independently selected exact policy | Not required | A complete synthetic candidate without previous game qualification passes oracle admission; missing host/signing/ownership/observer/policy conditions refuses |
| `supported_launch` | All qualification_run candidate gates plus current accepted qualification matching exact inputs/configuration/entry | Required | The same candidate without qualification refuses; mismatched/stale qualification refuses |

Preserve `docs/runtime-contracts.md` purpose meanings and reuse the Python oracle's existing eligibility implementation. Do not copy #3 native contract.rs's fixture-only entry restriction into the production policy path. Stage 1 tests contract structure/oracle meaning with explicitly synthetic declarations and non-executable bytes. These tests neither authenticate receipts nor grant actual runtime execution. Stage 2 implements native admission and checks actual required authorization/readiness/ownership before execution; no prior-game-qualification circular dependency is introduced.

## Document Location Check

| File/group | Planned Location in Task Plan | Stage Artifact Path | Match | Notes |
|---|---|---|---|---|
| Production source/rules/terms | `manager/` | `manager/Cargo.toml`, `Cargo.lock`, `src/`, `native/`, `AGENTS.md`, `dependencies.json` | OK | Create rules with real code; no empty source area |
| Profiles/rules/provenance | `profiles/` | `profiles/AGENTS.md`, `fixtures/a.json`, `fixtures/b.json`, `megabonk/profile.json` | OK | No game bytes or App ID branches |
| Versioned shared contracts | `runtime/contracts/` | `v2/` seven schemas/common/registry and examples | OK | Preserve v1; version-specific additions in existing root |
| Independent checker/tests | `tests/contracts/`, `tests/manager/`, `tests/profiles/` | `validate_v2.py`, v2 tests; build/case adapters and behavioral fixture tests | OK | Reuse #3 primitives and unittest; no generic runner |
| Official procedures/profile guide | Existing approved docs root | `docs/development/runtime-supervisor.md`, `docs/game-profiles.md` | OK | Fixture/native/runtime/distribution scope explicit |
| Existing public specification/index | Existing paths | `docs/runtime-contracts.md`, `docs/README.md`, `docs/architecture.md` | OK | Narrow implemented-interface/link updates |
| Reuse/stage/final artifacts | Approved mydocs paths | `tech/task_m1_9_reuse.md`, `working/task_m1_9_stage{N}.md` and sanitized evidence, `report/task_m1_9_report.md` | OK | Dated research and Issue results, not second product standards |
| Approval/board | Existing plans/orders paths | This plan, task plan supplements and #9 board row | OK | Preserve other task rows; reconcile only at approved integration |

## Stage 1 — Reuse, Native Foundation and Versioned Shapes

### Artifacts

- `manager/AGENTS.md`, `Cargo.toml`, exact `Cargo.lock`, `dependencies.json`, `src/lib.rs`, reused `src/json.rs`, initial `src/diagnostics.rs`, `src/native.rs`, `native/bridge.h/.c` ABI foundation and `examples/foundation.rs` test probe.
- `runtime/contracts/v2/` closed schemas/registry and non-executable fixture/research examples.
- `tests/contracts/validate_v2.py`, `v2_fixture.py`, `test_v2.py`; `tests/manager/build.py`, `support.py`, `test_foundation.py` as small existing-helper adapters.
- `mydocs/tech/task_m1_9_reuse.md`, Stage 1 report/evidence and approved implementation status.

### Changes

Reuse #3 parser and dependency input unchanged where applicable. Record selected standard/system API ownership and narrow C ABI: caller-owned outputs, native errno values, no retained pointers/unwinding, no post-fork allocation. Stage 1 wraps only header-checked staging/hash/identity primitives, not a new runtime. Record partial upstream non-adoption and useful scenarios without another broad source acquisition. Generate v2 schema shapes using v1 structure and test their exact version/unknown/refusal rules. No spawn/activation/game claim in this stage.

Dependencies: obtain only the existing locked libc and five hash-locked test wheels if absent, using their already reviewed metadata and task9 outputs for the venv/wheels. Default Cargo source cache is an ordinary reviewed tool input; do not replace/delete existing entries or use another task's build cache. Reuse #3 `verify_lock` extraction checks and controlled environment; add a check that the manager manifest/lock has exactly the selected package/dependency closure. Any hash mismatch fails, no floating versions/global package install. Offline/locked builds follow explicit acquisition.

### Verification

```sh
python3 -m venv .build/task9/venv
.build/task9/venv/bin/python -m pip download --only-binary=:all: --require-hashes --no-deps -r tests/contracts/requirements.lock --dest .build/task9/wheels
.build/task9/venv/bin/python -m pip install --no-index --find-links .build/task9/wheels --require-hashes --no-deps -r tests/contracts/requirements.lock
cargo fetch --manifest-path manager/Cargo.toml --locked
python3 -B tests/manager/build.py --output .build/task9/stage1 --locked
.build/task9/venv/bin/python -B tests/contracts/validate.py --check-schemas --check-examples
.build/task9/venv/bin/python -B tests/contracts/validate_v2.py --check-schemas --check-examples
.build/task9/venv/bin/python -B -m unittest discover -s tests/contracts -p 'test_*.py'
python3 -B -m unittest discover -s tests/manager -p test_foundation.py
python3 -B tools/check_governance.py
git diff --check
```

Native build adapter imports #3 environment/lock/capture helpers, adapts its package inspection, runs the foundation library ABI tests and compiles only selected task9 Rust/C, not Swift or Wine. It records commands, tool/SDK/source/binary hashes, linker ad-hoc signature inspection and actual ARM64 slice. Tests include all original v1 IDs, raw duplicate/Unicode/numeric bounds, unknown/null inspection but launch refusal, remote ref refusal and mixed versions. ABI checks repeat locks/staging/hash against the implemented glue; no probe outcome is blindly inherited.

Retain exact source additions separately from historical #3 input maps. #3's current-input report checker may reject an expanded covered inventory; retain that result and unchanged historical report instead of rewriting it. Unchanged original input hashes support only their old fixture claims; Stage 1 and later results have their own identities.

### Commit

`Task #9 Stage 1: reuse native foundations and version profile contracts`

## Stage 2 — Native Admission and Immutable Activation

### Artifacts

- `manager/src/fs.rs`, `contract.rs`, `policy.rs`, `activation.rs`, initial inspect/activate dispatch in `main.rs`; completed narrow native bridge/hash functions.
- `tests/manager/test_admission.py`, `test_activation.py`, `fixtures/entry.c`, a small owned native executable/dylib pair and an alternate marker dylib; task-owned activation snapshots/evidence.

### Changes

Adapt #3 path/graph/hash validation to declared IDs/entries/families and both supported versions without game identity branches. Inspect all reachable bytes/context/eligibility independently from policy authenticity. Hash streams with before/after metadata and exact byte scopes. Verify native activated payload closure; a fake fixture source/signing field cannot authorize runtime.

Implement only local read-only payload admission and staged atomic selection metadata. Reuse existing OS image tooling for manual/fixture preparation; production CLI does not acquire a volume manager. Hold opened root and version selection lease through use. Prove fchdir-relative entry resolution before adding general launch. Mutable operations are disabled here except owned activation metadata. Preserve the old pointer and content under corrupt input, insufficient space/write/sync failure, interrupted publication and concurrent activate/use.

### Verification

```sh
python3 -B tests/manager/build.py --output .build/task9/stage2 --locked
PEAR_MANAGER_BUILD=.build/task9/stage2 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_admission.py
PEAR_MANAGER_BUILD=.build/task9/stage2 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_activation.py
git diff --check
```

Required outcomes: wrong bytes/kind/version/family/policy, unsafe absolute/traversing/symlink/hardlink/nonregular references and incomplete host/signing/source inputs refuse before exec. Actual read-only image blocks payload writes; writable chmod-only input refuses. Rename/replace ancestors at the validation/use barrier and concurrent version change must execute only the selected old bytes or refuse. Hash executable/library inventories before/after. Multi-chunk data above old v1 blob bounds is checked with independent hashlib; oversize metadata refuses without allocating/reading oversized payloads. No actual game or heavy Wine/FEX reconstruction is needed. Native errors/host skips remain explicit; unavailable read-only execution is an unmet required gate.

Declared dynamic dependency controls: build an ARM64 executable using `@rpath/libfixture.dylib`, one approved in-payload dylib and one alternative dylib with different deterministic return/output markers. Use existing `otool -L/-l`, hashes and a closed supported load-command/path policy; no new Mach-O parser framework. An internal `@loader_path`/`@executable_path`-anchored RPATH resolving entirely within the selected read-only payload must execute the approved marker. An absolute writable external dependency or external RPATH candidate must refuse before entry (no executable/alternate marker). At the validation/use barrier replace an ancestor or an external candidate and change activation concurrently: execute only the approved marker or refuse, never the alternate marker. Record exact source/binary hashes, load commands, selected candidates, mount/FD identity, mutation timing, independent stdout/exit markers and before/after hashes. This is a finite declared-dependency admission test, not full module observation.

#9 admission checks declared, supported static dependencies. Arbitrary `dlopen`, plugins, unresolved weak/re-export/dependency forms or dynamic lookup outside the closed supported scope must be explicitly restricted/refused and recorded as integration prerequisites. #10 owns actual complete loaded-module observation; neither this inventory nor a read-only main executable proves every runtime load. Reference: [Apple run-path dependent libraries](https://developer.apple.com/library/archive/documentation/DeveloperTools/Conceptual/DynamicLibraries/100-Articles/RunpathDependentLibraries.html), inspected October 8, 2026; dyld searches run paths in recorded order. No Wine reconstruction is required for these owned fixtures.

Stage 2 also repeats the purpose table's positive/negative admission cases natively, keeping synthetic policy-unit results distinct from actual execution authorization.

### Commit

`Task #9 Stage 2: verify immutable runtime admission and activation`

## Stage 3 — Foreground Supervision, Cancellation and Crash Refusal

### Artifacts

- `manager/src/supervisor.rs`, `observer.rs`, initial private journal functions in `state.rs`, CLI dispatch in `main.rs`.
- `tests/manager/case_adapter.py`, `test_supervision.py`, `test_crash.py`, `test_observer.py`, fixture entry/detach modes and synthetic peer.
- Adapted native `supervisor_tests` with both original pipe fault assertions.

### Changes

Reuse #3 spawn/reservation/nonblocking/reaping core. Cancellation handlers perform only allowed signal-safe flag work; main loop owns cleanup, journal and output. Normal success is not reported before reaping and owned cleanup. Persist running/cleanup-pending before vulnerable transitions and a clean marker only after required observations/publication. No custodian, persisted-PID signal command or management service.

Connect the bounded exact-request observer descriptor interface; fixture peer records synthetic scope. Preserve errors and wrong/stale/no readiness refusal. Bind monotonic producer sequences/exit references, but do not collect real modules or fake observer_complete coverage.

Reuse all 55 original corpus entries through #3 `create_bundle`, mutation/capture/identity functions and a small task9 invocation adapter. Maintain a table from original ID to native operation, expected result and any legitimate production difference. Production raw stdout is not required to be fixture JSON; the original malformed-child protocol case must be retained with its declared changed output-contract scope and independent byte/privacy/cleanup assertions, not silently dropped or called equivalent. Unsupported v1 operations remain refused; v2 implemented settings receive separate positive/negative tests. Historical corpus/source/report bytes remain unchanged. Classification movement to earlier admission is recorded; safety assertions are preserved.

### Verification

```sh
python3 -B tests/manager/build.py --output .build/task9/stage3 --locked
PEAR_MANAGER_BUILD=.build/task9/stage3 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_supervision.py
PEAR_MANAGER_BUILD=.build/task9/stage3 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_crash.py
PEAR_MANAGER_BUILD=.build/task9/stage3 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_observer.py
python3 -B tests/manager/build.py --output .build/task9/stage3 --locked --rust-tests
git diff --check
```

Inputs: fresh owned C fixture/companion and current native manager, actual read-only activation, independent test roots/peer/sentinel. Keep #3 ordinary functional 5,000 ms, deliberate timeout 1,500 ms, cleanup 2,000 ms and original outer 10-second watchdog where applicable. Additional crash scenarios get explicit finite deadlines and outer bounds before execution; a watchdog intervention always fails, no startup failure is erased.

Require 55 mapped cases, both failed pipe positions, actual child/descendant traces, reaping and unrelated sentinel survival. Add early EOF/final output, cancel-before-spawn/during-run, nonzero/signal exit, denied/ambiguous cleanup, actual supervisor SIGKILL/abort and detached helper controls. After abrupt manager death expect incomplete journal, refusal despite free lease/PID reuse, old data preserved and no unrelated signal; no clean reaping claim. Test harness tears down only its directly owned finite fault fixtures and preserves relevant failure evidence. Real detached Wine scope is not qualified by these synthetic controls.

### Commit

`Task #9 Stage 3: supervise owned children and refuse uncertain recovery`

## Stage 4 — Scoped Mutable State and Two Fixture Profiles

### Artifacts

- Completed `manager/src/state.rs`, `profile.rs` and prepare/status/recover commands.
- `profiles/AGENTS.md`, `profiles/fixtures/a.json`, `b.json`; original redistributable state fixture companion.
- `tests/manager/test_state.py`, `tests/profiles/test_profiles.py`; independent preservation inventories.

### Changes

Allocate context roots by compatible runtime family and declared game/library context. Acquire one canonical prefix lock inode via std try_lock; keep its descriptor/identity, reject replaced aliases and reserve it through cleanup. Check dirty journal before reuse even with a free lock. Descriptor-relative settings apply only typed allowed keys; unknown/unsupported paths or operation semantics refuse.

A/B differ in profile ID/App ID, argument values, setting value, prefix and saves. Use the same generic consumer; no manager App ID branch. The fixture writes and reads distinct settings/save markers so isolation is observed across run/relaunch, not inferred from directory names. Cache is disposable and identity-scoped; wrong/unknown identity prevents reuse. Manual new-context and clean previous-compatible selection preserve old data; no save overwrite/rollback/migration algorithm.

### Verification

```sh
python3 -B tests/manager/build.py --output .build/task9/stage4 --locked
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_state.py
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/profiles -p 'test_*.py'
git diff --check
```

Sequential and concurrent A/B launches must show exact different argv/settings and persistent isolated save bytes. Concurrent same-prefix mutation/launch refuses. Test alias/overlap/busy/dirty/wrong-family/cache-invalid/incomplete-save-mapping refusal and interruption before/after publication. Independent hashes show unchanged runtime, other profile, previous prefix and preexisting saves. A free lock is not completion proof; replacing the lock pathname is detected at use. No real authenticated prefix or personal saves are inputs.

### Commit

`Task #9 Stage 4: isolate fixture profiles and preserve recovery data`

## Stage 5 — Megabonk Profile and Official CLI Guidance

### Artifacts

- `profiles/megabonk/profile.json`, sanitized provenance/feature/path observations.
- `docs/development/runtime-supervisor.md`, `docs/game-profiles.md`; narrow existing spec/index/architecture updates.
- `tests/profiles/test_megabonk.py`, `tests/manager/test_cli.py`; fixture documentation walkthrough evidence.

### Changes

Record Steam App ID 3405340 and observed `Megabonk.exe`; historical 1.0.69/depot/manifest, experimental arguments and candidate config location retain dated scope. Current BuildID/Steam/runtime family and save inventory remain unknown unless an independently reviewed input exists. Use null/unknown states and untested optional features; no guessed Wine user or supported steam_appid.txt route.

Document existing manual read-only payload preparation, native activation, two fixture contexts, SIGINT/SIGTERM, incomplete crash state and preservation-first manual recovery. Explain #9 lifecycle versus #10 actual observer coverage, supported launch gates and unavailable real runtime. Public guides use no private diagnostics or macOS grant/signing assumptions. Read existing docs before each narrow edit; follow approved locations, no new roadmap/manual.

### Verification

```sh
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/profiles -p 'test_*.py'
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_cli.py
python3 -B tools/check_governance.py
git diff --check
```

Inspect the researched profile through v2 oracle/native consumer, then require real launch refusal with missing current prerequisites. Run documented CLI commands against fixture setups; preserve independent A/B results and useful typed failures. Review local links, English/public prose, unknown features and bounded exports for synthetic secret markers/paths. Do not execute Steam, Megabonk or Raft to complete this stage.

### Commit

`Task #9 Stage 5: document CLI recovery and researched Megabonk profile`

## Stage 6 — Fresh Construction and Final Handoff

### Artifacts

- Fresh ignored `.build/task9/final-<unique-id>/` with current build/fixture/test receipts, owned retained failures and full input/binary hashes.
- `mydocs/working/task_m1_9_stage6.md`, sanitized evidence, final report and #9 board completion.
- Approved narrow integration resolution if the base/docs/board changed; no other task artifacts touched.

### Changes

Inspect current open work, master changes, relevant reports and exact #3/#6/#7 inputs. Integrate only by the separately approved repository procedure; rerun affected checks after source/configuration/schema/activation changes. Rebuild the current manager/fixture in new empty outputs with exact offline inputs; no language comparison or broad runtime reconstruction. Reuse unchanged historical evidence only for its recorded claim. Preserve failed attempts and record unavailable/unsupported/unperformed game/runtime/distribution scope.

### Verification

```sh
python3 -B tests/manager/build.py --output .build/task9/final-<unique-id> --locked --require-empty
.build/task9/venv/bin/python -B tests/contracts/validate.py --check-schemas --check-examples
.build/task9/venv/bin/python -B tests/contracts/validate_v2.py --check-schemas --check-examples
.build/task9/venv/bin/python -B -m unittest discover -s tests/contracts -p 'test_*.py'
PEAR_MANAGER_BUILD=.build/task9/final-<unique-id> .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p 'test_*.py'
PEAR_MANAGER_BUILD=.build/task9/final-<unique-id> .build/task9/venv/bin/python -B -m unittest discover -s tests/profiles -p 'test_*.py'
python3 -B tests/manager/build.py --output .build/task9/final-<unique-id> --locked --rust-tests
python3 -B -m unittest discover -s experiments/manager -p 'test_*.py'
python3 -B tools/check_governance.py
git diff --check
git status --short
```

The unique-id placeholder is replaced with a new recorded lowercase run label; never delete a failed run to reuse its path. Build adapter records C/Rust test link arguments and locked offline mode instead of depending on ambient RUSTFLAGS. Required result assessment identifies every case/test ID, current executable/fixture/source/tool/input/policy/mount identity, full required counts, bounds, cleanup/sentinel evidence and false-success controls. Skipped or incomplete required native cases do not pass. Review package slices/dependencies and ad-hoc inspection separately from distribution authorization.

All source/report/board changes are committed by the applicable stage/final-report procedure; worktree status must then be clean for PR preparation. Request approval of the final report and concrete PR before publication. No self-merge/Issue close is authorized here.

### Commit

`Task #9 Stage 6 + final report: reconstruct supervisor fixtures and bind evidence`

## Verification and Evidence Reuse Rules

Every stage uses the selected development tools and current native outputs. Python oracle environment is task-owned/hash-locked; standard/system API availability is bounded to recorded host inputs. The v1 reference checks and original prototype sources/corpus/history are retained. Newly added schema/test inventory can make the historical current-input checker ineligible; report that precise scope and preserve old bytes, not a falsely renewed #3 pass. Existing experiment regression tests must still run; any failed required test is repaired within scope or brought to the requester before continuation.

The build/case adapters import existing helpers and produce task9-specific receipts. They are bounded task glue, not a new generic test runner/verifier framework. Native case expectations may change only for an explicitly documented production semantic difference; privacy, bounds, current identities, reaping, owned cleanup and unrelated sentinel checks never disappear. A receipt label/exit zero, old output, absent event, synthetic policy/observer, unverified helper or failed command cannot satisfy a stronger claim.

Private streams/state/signing/account/game data never enter Git. Retain task-owned build/run evidence in `.build/task9/` with source/owner/command/result and cleanup conditions. Tests use platform temporary roots, preserving relevant failures before owned scratch cleanup. No external task artifact/cache/prefix deletion. File locks/read-only media/user permissions are not a hostile-code sandbox.

## Commits and Stage Dependencies

Each stage source commit includes `mydocs/working/task_m1_9_stage{N}.md`, actual verification/evidence limitations and that stage's artifacts. Use the exact stage commit messages above. Complete/report/commit before requesting the next stage. Stage 2 depends on the approved verified shape/ABI foundation; Stage 3 depends on actual immutable entry admission; Stage 4 depends on current lifecycle ownership; Stage 5 depends on generic fixtures/state behavior; Stage 6 depends on all approved stages and then-current integration inputs.

Task-plan and supplemented implementation-plan approval are recorded; Stage 1 is authorized. Stage 2 is the next approval after Stage 1 verification/report/commit. Later explicit continuations in this chat authorize only their next approved scope. If immutable execution, crash semantics, a new custodian, license combination, schema vocabulary or real runtime integration requires a material change, present the concrete gap and revised plan before that dependent work.

## Risks and Responses

- **Immutable execution precondition:** OS read-only media and fchdir-relative lookup are not yet production-tested. Stage 2 must demonstrate actual byte/namespace behavior; writable/ambiguous backing inputs refuse, no advisory-lock substitute.
- **Abrupt death:** one process cannot reap after its own SIGKILL. Journal/quarantine/manual new-context recovery explicitly preserves safety and data; automatic orphan cleanup is not claimed. If a required scope demands that capability, review a minimal custodian then.
- **Detached Wine ownership:** fixture association is synthetic and cannot qualify required real helpers. Keep incomplete/unsupported state and require actual ownership/#10 observation before any complete runtime claim.
- **Version/adaptor drift:** v2 metadata/null/bounds must not reinterpret v1 or self-authorize. Use original evaluator/fixtures, strict registry/version checks and independent native parity; no downloaded executable vocabulary.
- **External reuse cost:** standard APIs/#3 reduce new code; no direct Whisky source adoption is claimed. Revisit only a demonstrated useful small boundary, preserving Swift/GPL provenance and approval scope.
- **Integration state:** #6 merged after branch creation. Preserve its changes and old evidence; review exact docs/board/source overlaps at approved integration, no private artifact copying or needless runtime reruns.
- **Availability:** libc/wheel acquisition and actual read-only mounting remain stage prerequisites. Record failure/unavailable explicitly; do not loosen dependency hashes or required execution checks.

## Approval Record and Next Checkpoint

On October 8, 2026 the requester instructed the originating chat to convey the review findings, correct the plans and proceed with Stage 1. The authorized relay expressly approves these three supplements and Stage 1 implementation, verification, reporting and bundled commit; the same plan/Stage 1 approval must not be requested again. Stage 2 and later retain explicit continuation after the preceding verified/reported/committed stage. Material new architecture or scope changes require a concrete revised proposal.

On October 9, 2026 the requester explicitly instructed this chat to proceed, authorizing Stage 2 under the supplemented plan. Stage 3 remains a separate checkpoint.

- October 9, 2026: after reviewing the Stage 2 completion, the requester explicitly instructed this chat to proceed, authorizing Stage 3 under the existing supplemented plan. Stage 4 remains a separate checkpoint.

On October 9, 2026 the requester explicitly continued after the Stage 3 report and commit, authorizing Stage 4 implementation, verification, reporting and bundled commit. Stage 5 remains a separate checkpoint.

On October 9, 2026 the requester explicitly continued after Stage 4 commit `e4183a9`, authorizing Stage 5 profile/documentation work, verification, reporting and bundled commit at the already approved locations. Stage 6 requires a new continuation. Current inspection found master `d019a6e`, Task #8 `2c709b1` and Task #10 planning commit `bbbe357`; no integration is performed. The #10 plan still treats the #9 synthetic transport as a source-bound dependency, not actual observation authority.
