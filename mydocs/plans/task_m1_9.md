# Task Plan: Native runtime supervisor and Megabonk profile

GitHub Issue: [#9](https://github.com/postmelee/pear/issues/9)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Work branch: `codex/task9`
Planning date: October 8, 2026 (Asia/Seoul)
Status: the requester approved this task-plan direction and authorized the narrow reuse/minimal-structure supplements and detailed implementation planning on October 8, 2026, through the originating chat. The supplemented implementation plan and Stage 1 were subsequently approved through the same authorized relay; Stage 1 implementation is authorized. Later stages require explicit continuation in this chat after verification, report and commit.

## Purpose

Deliver a native Rust CLI and game-independent supervisor that consume Pear's existing versioned contracts, verify selected runtime inputs, launch with explicit arguments and a limited environment, own only their processes and mutable state, and produce bounded structured failures. Deliver a versioned Megabonk profile with App ID `3405340`, the observed executable, and explicit evidence limits, plus two redistributable profiles that prove settings, prefix and save isolation without needing the real runtime.

This completes #9's supervision/profile scope. A CLI with documented manual setup and recovery is sufficient. Fixture execution, native manager architecture and a complete build do not qualify Steam, Megabonk, the full Rosetta-free process/module path or ordinary-user distribution.

## Background

The applicable baseline is the [README](../../README.md), [documentation index](../../docs/README.md), [architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md), [runtime contracts](../../docs/runtime-contracts.md), [platform reuse](../../docs/research/platform-reuse.md), [local evidence](../../docs/research/local-evidence.md), and the [dated evidence-reuse investigation](../tech/20261004_recompilation_and_verification_reuse.md). Root, host, runtime, test and documentation `AGENTS.md` files were explicitly read. Task-start, todo, task/Git workflow, conflict rules, document structure and the central task-plan/board templates apply.

### Current task and integration state

Read-only checks on October 8 found:

- #9 is OPEN, in existing M1, with #3 as its only acceptance dependency. Its current body requires a WhiskyKit component review before new common launcher facilities.
- #3 is CLOSED and [PR #28](https://github.com/postmelee/pear/pull/28) merged at `1f229dab08e30afb01080e7664240e317e5df2ef`; that commit is an ancestor of the current `origin/master`.
- The fetched base is `2e0985baafce3d8842bb571bb690218bba42be5c`, including merged #5 and #7. No open PR was returned by the planning query. Relevant open M1 Issues are #6 and #8–#16; R1 #17–#21 remain independent.
- Main remains on `master` with untracked `analysis/` and `research/`; those are preserved. #9 uses the attached worktree `/Users/melee/.codex/worktrees/pear-task9/New project`, created from the fetched base, with `codex/task9`.
- #6 is active in its own worktree. The observed checkpoint was `ba5658a` (Stage 3.3); its latest completed Stage 2 report records 18 passing comparisons and AVX explicitly unsupported, followed by an in-progress ordering/lifecycle reference checkpoint. This is a changing snapshot, not #6 completion. Its private builds, prefix, runner and FEX changes are not #9 inputs or edit targets.
- Retained task1/task3/task5 detached evidence worktrees and the locked task7 evidence worktree remain needed. Do not mutate, clean or remove their artifacts. The main and #6 daily boards have differing task-local updates; #9 adds its own row only and must preserve both sets of rows during eventual integration.

[#5's final report](../report/task_m1_5_report.md) provides a source-built Wine/FEX pair and finite x64 execution, while [#7's report](../report/task_m1_7_report.md) provides graphics construction and finite native pairing. They do not provide a complete launch-eligible product lock/artifact, complete observation, game support or unrestricted distribution. #9 fixture work can proceed without waiting for #6. Future product-record integration must review the actual later source/build/signing evidence; the old #1 blocked audit must not be relabeled as ready.

Follow-up planning check: #6 is now CLOSED and [PR #38](https://github.com/postmelee/pear/pull/38) merged at `d019a6efb202615e84cbcb9be63e5f55ba7f44c1` on October 8, 2026. The fetched remote has advanced to that commit; #9 retains its original base and does not merge/rebase or consume private #6 artifacts during planning. Its final report supplies finite CPU/ordering evidence, with AVX/i386 and game limitations still separate. Review that merged handoff and preserve concurrent board/docs when integrating later. The earlier worktree observations above remain dated snapshots.

### Mandatory #3 reuse inventory

The [#3 plan](task_m1_3.md), [implementation plan](task_m1_3_impl.md), [latest stage report](../working/task_m1_3_stage5.md), [final report](../report/task_m1_3_report.md), [manager decision](../../docs/decisions/manager-language.md), native sources, schema registry/examples, reference checker/tests, fixtures and reproduction tools were inspected. Rust is already selected for this new manager; no new Rust/Swift comparison is proposed.

| Existing artifact | Reuse / adaptation judgment | Production difference or missing work |
|---|---|---|
| `runtime/contracts/contract-index.json`, `v1/`, `examples/` | Reuse as the authoritative language-neutral baseline, exact-byte DAG identities and context/eligibility rules | Do not turn synthetic source/signing/observer declarations into real authority. Explicitly version any new executable semantics. |
| `tests/contracts/validate.py`, `fixture_factory.py`, behavioral/adversarial tests | Reuse the independent evaluation oracle, bundle construction and meaningful rejection scenarios | Evaluation is read-only and cannot authorize at-use access, observe signatures or enforce state ownership. Native launch evaluation must match its applicable semantics; Python is test tooling, not the manager's hidden runtime validator. |
| `experiments/manager/rust/src/json.rs` | Adapt the existing bounded strict parser and duplicate-key/Unicode/numeric checks | Replace unit-only errors with bounded typed diagnostics; verify supported record shapes and existing limits rather than assuming arbitrary Rust decoding is equivalent. |
| `rust/src/contract.rs` | Adapt descriptor-relative traversal, exact hashes, graph/cycle/alias checks | Remove hardcoded record IDs, App ID 1, family, fixed paths and the four-record fixture shape. Add independently selected policy, actual host/signing/source prerequisites, supported qualification references, and at-use mutable-root checks. Stream large payload hashing instead of inheriting a 16 MiB fixture limit as a runtime requirement. |
| `rust/src/main.rs` | Adapt explicit argv, `env_clear`, pipe bounds, monotonic deadlines, unreaped group-leader reservation, cleanup/error distinctions | Add cancellation, concurrent state leases, crash/recovery, detached-helper ownership and useful failures. Immediate inode checks followed by pathname `Command::spawn` do not close the execution race. |
| `rust/src/supervisor_tests.rs` | Preserve both pipe-setup fault scenarios, actual descendant-held pipes, descriptor closure, reaping, identity disappearance and sentinel survival | Task9 tests must use the platform temporary-directory API and owned retained-failure paths rather than copying the prototype's fixed `/private/tmp` scratch path. |
| `fixtures/child.c`, `native_bridge.c/.h`, `cases.json` | Reuse original owned child behavior, narrow creation-time ABI and 55 safety/rejection cases as inputs | Add a task9 companion fixture for settings/saves, detachment and crash/cancellation. Keep historical fixture bytes/results unchanged. State any expectation that changes because a previously unsupported operation becomes explicitly implemented. |
| `build.py`, `run_cases.py`, `reproduce.py`, Python regression tests | Reuse dependency verification, controlled offline builds, bounded capture, oracle and evidence checking; adapt only necessary invocation/build seams | No second generic harness, language comparison or timing campaign. Task9 output/report identities must be separate; a changed producer invalidates affected old input claims. |
| `results/reproduction.json` and retained failure/comparison records | Preserve as historical #3 evidence; current checkers passed at planning | 119 reference tests, 60 experiment tests, two Rust fault tests and Rust/Swift 55-case corpora are recorded results, not tests rerun by this planning turn. Earlier 1,500 ms startup failures remain unresolved. |
| `docs/runtime-contracts.md`, `docs/decisions/manager-language.md` | Reuse ownership, external policy, readiness and language decisions | Implement #9 obligations without claiming #10 collection or changing the language decision without new reviewed evidence. |

The reproduction record SHA-256 remains `a214a305dde1d3c05aed9eb4409cd7d12495c3c58d2acf83126e37830f7e291a`. The planning checker matched its 58 current input identities and ten retained historical records. This establishes record consistency, not independent host authenticity or a fresh functional run. Adding/changing covered tests or schemas may invalidate the current-input comparison; keep the historical report unchanged and produce separate task9 evidence.

### Pinned WhiskyKit component review

Source-only review: [frankea/Whisky](https://github.com/frankea/Whisky/tree/3abfbae945e3400caaa13cf2e78fe5a187a1405b/WhiskyKit), commit `3abfbae945e3400caaa13cf2e78fe5a187a1405b`. The downloaded source archive SHA-256 was `033eb22f95464b68042bbf053ae71855f18123119e862c49fb54f9b3a078b3ec`. No Whisky build, test or runtime was executed. Paths below are relative to `WhiskyKit/Sources/WhiskyKit/` at that exact pin.

The reviewed Swift module headers state GPL version 3 or later and identify the files as part of Whisky; root `LICENSE` contains GPLv3. Package.swift also carries that notice, declares macOS 15, and includes SemanticVersion/DocC and package resources. These are Whisky prerequisites, not Pear support requirements. The pinned `CONTRIBUTING.md` was read: its formatting, localization, changelog, tests and review procedures apply to any future upstream contribution; none is promised here. Root LICENSE SHA-256: `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986`; CONTRIBUTING SHA-256: `a707d13225a9de4055451edf167f238a0cb9df89f754bd60c5dcf869903b3dc1`.

| Component and exact source path | Judgment for #9 | Useful behavior and contract incompatibility |
|---|---|---|
| `Wine/EnvironmentBuilder.swift` and its tests | Adapt design; no source translation/import in preparation | Deterministic layers/removal/provenance are reusable. Pear already has Rust scoped environment construction. Restrict keys and reserve manager-owned prefix/runtime values; Whisky's arbitrary user/callsite layers cannot override them. A Swift helper would add another executable/protocol without removing the existing native ownership path, so direct integration is not selected for this bounded CLI. |
| `Wine/Wine.swift`: `PreparedLaunch`, `prepareProgramLaunch`, `launchArguments` | Adapt preparation-versus-spawn boundary; reject complete wrapper | Explicit argv and resolved backend coherence are useful. Font/profile reconciliation, registry/DLL deployment, `wine64` globals, launcher-specific branches, Discord and implicit graphics choices do not fit a generic contract executor. Do not translate the entire Swift wrapper into Rust. |
| `ProcessRegistry.swift` | Adapt per-prefix registry concept; reject cleanup implementation | Registers before launch and updates PID afterwards. Cleanup signals stored PIDs, waits, checks `kill(pid, 0)` and clears the registry without an OS generation reservation or required cleanup proof. Date/object identity is insufficient for PID reuse or detached ownership. Use #3's reservation and kernel identity boundary instead. |
| `Wine/Wine+ProcessManagement.swift`; `Wine.swift` wineserver controls | Adapt exclusively owned-prefix server-control concept; reject current proof/error handling | `wineserver -k0`/`-k` use bottle WINEPREFIX. Errors can become false liveness or logged-only cleanup. Pear must reserve the prefix, verify exact server/runtime selection and keep unavailable/error outcomes. No global process-name termination. Real Wine adapter behavior remains separately evidenced. |
| `Extensions/Process+Extensions.swift` | Reuse EOF, trailing-output and cancellation failure scenarios; reject stream/log implementation | EOF handlers and post-exit output races are useful checks. `readToEnd` can wait on retained descendant pipes, stream buffering lacks Pear's bounds, and logging writes raw output/arguments/environment. Keep bounded byte capture and structured allowlisted export. |
| `Whisky/BottleLocationValidation.swift` | Adapt actionable permission/capacity preflight design; reject as ownership validator | It explicitly does not check ownership, resolves symlinks and permits unknown capacity. Pear needs descriptor-relative roots, leases and write-time checks. An error domain or capacity observation is not launch authorization. |
| `Wine/WinePrefixValidation.swift` | Adapt missing-prefix/user-directory diagnosis; reject username heuristic | Chooses a sorted non-crossover user directory and checks pathname existence. Pear must resolve the actual declared Wine user mapping; it cannot infer save ownership by first directory or ambient host USER. |
| `Whisky/BottleOperations.swift` | Adapt staging/rollback and in-flight state concepts; exclude move/export/duplicate product features | Metadata snapshots and partial-clone cleanup inform interruption tests. App registry/UI guards and arbitrary directory moves are not cross-process leases or version-safe recovery. #9 preserves data and offers manual recovery; automatic save restore/rollback remains deferred. |
| `WhiskyWine/WhiskyWineInstaller.swift`, `WhiskyWineVersion.swift` | Adapt streaming hash and missing-payload/error scenarios; reject installer/version gate | Installer removes existing Libraries before extraction; optional or malformed hash metadata may become unverified. Pear requires exact trusted identities and isolated staging/activation, preserving active versions. No Whisky runtime download, mutable global install, GPTK import or source-ready claim. |
| `Diagnostics/Redactor.swift` | Reuse privacy threat cases; reject as sole export authority | Common token, URL, JWT and home-path patterns inform fixtures. Best-effort regex and optional inclusion of sensitive values cannot prove public output is safe. Use closed structured exports and bounded local private streams. |

No Whisky source or test is copied in preparation. Design/scenario adaptation is recorded as such, not claimed as adopted implementation. GPL reuse remains a valid option. If Stage 1 identifies a smaller useful direct module boundary, preserve its Swift and original headers, record exact file hashes, provenance, modifications and dependency/combination obligations before incorporation; obtain approval for a changed integration/license scope. Do not select Pear's project license silently or treat translating GPL source as removing its provenance/terms.

For stable source attribution, reviewed file SHA-256 values include EnvironmentBuilder `cb998142476eedf6425bbe89915f530df0687f7e664ece76683646a6b9597923`, ProcessRegistry `a5327e8b9048342b9ac45c9e10c8748e4ed38f3af3b84cc85b8cd8e0ba06b399`, Wine.swift `fd1685afceaaac0346bcf48ea539bb3de1adc59aeeefd39fd2c27a62af0d902b`, Process+Extensions `00f08b99ffdf8b85ee0c6dab449a3fe2927d2867565b6b4e5ab9500699989ae6`, and WhiskyWineInstaller `5b7d10d6cc820f3e27ded177eefdd855966a6b2f084d02b1219b7a6823978827`. Stage 1 retains the complete selected-file/license map in task evidence.

Madeira, madeira-anyps5 and AnyPS5 are broader reference projects in the existing platform study. No #9 need for their PS5 runner, PE loader, CPU translator, JIT implementation or graphics backend was identified. Their full integration and any code copying are excluded; re-pin and inspect relevant file terms if a concrete later launcher boundary needs them.

## Scope

### Included

- Native Rust manager/CLI, shared-contract consumption, independently chosen policy, manifest/payload verification, explicit argv and restricted environment, bounded structured failures and lifecycle output.
- Local verified artifact staging/activation and concurrent launch safety. Separate immutable runtime inputs from prefixes, caches, saves, logs and journals; preserve compatible previous runtime/prefix combinations.
- Prefix ownership and exclusive mutation, settings limited to implemented typed operations, cache identity rejection/invalidation, user-data preservation and documented manual recovery.
- Owned child spawn/reap/termination, cancellation, timeouts, output limits, descendant-held pipes, manager crash and detached-helper ownership/refusal cases, including cleanup failure evidence.
- Versioned Megabonk profile with accurate known/unknown/untested data; two distinct redistributable fixture profiles proving reusable launch behavior and settings/prefix/save isolation.
- #9's side of the exact-request observer handoff and honest readiness/gap handling through a synthetic peer; native collector implementation remains #10.
- Minimal official CLI/setup/recovery and profile guidance; input-bound evidence and normal stage reporting/commits.

### Excluded

- New Rust/Swift comparison, rewriting Wine/FEX/DXMT or an existing Swift subsystem, PS5 execution, new CPU engine/PE loader or graphics work.
- #6 CPU fixtures/ordering fixes and its native runner; #8 graphics qualification; #10 full observation/aggregation; #11 actual Steam qualification; #12 gameplay/save qualification; #13 final signed runtime assembly.
- Polished GUI, Steam-library discovery/import, library browser, integrated install/play UI, network runtime downloader/updater, automatic prefix migration or automatic save backup/rollback.
- Running or qualifying Raft (App ID `648800`), broader game support, performance/power campaigns, signing/provisioning changes, ordinary-user packaging or distribution.
- Private game/account/save/prefix/signing data in Git, changes to other task worktrees, Issue closure, publication/merge or cross-chat messaging during preparation.

## Design Direction

### Native contract and policy boundary

Use #3's Rust implementation as reviewed reusable source, divided into contract/filesystem, activation/storage, launch planning, lifecycle and diagnostics modules. Keep the native supervisor independent of App ID and fixture identity; profiles select behavior through supported declarative operations. Runtime selection is by exact artifact/file ID and compatible family, never ambient PATH, largest EXE, global Whisky paths or a moving upstream release.

A manager validates raw bounded JSON, supported versions, closed shapes, hashes, cross-record relationships and requested-use eligibility. Submitted records cannot authorize themselves. Independent policy selects exact approved inputs and actual host/signing scope. Research, fixture, qualification-run and supported-launch remain distinct. #9 cannot mint real build, signature, source approval, observation or qualification from synthetic fixtures. A supported launch needs matching current qualification; absent prerequisites produce a structured refusal.

Version 1 currently allows only two fixture environment keys, `fixture_flag`/`dxmt_log_level` settings, save-relative paths, and non-null profile family/renderer identifiers. It has no representation for a verified Wine user-to-save mapping or per-profile unknown feature/path observations. Stage 1 must document the concrete gap and freeze the smallest explicit versioned extension needed for the approved CLI/profile. Preserve v1 consumers/examples and their rejection rules. No silent addition of Wine environment keys, placeholder compatible family, invented save path, or weakened runtime eligibility is permitted. If a new schema version is needed, keep the same record/ownership model, add explicit unknown states/provenance and a closed allowed-operation vocabulary; its exact fields are approved in the implementation plan before coding. This is not a second profile framework.

Implement only required launch consumers/outputs and qualification eligibility. Reuse the reference evaluator for independent tests of existing run/qualification semantics; do not implement a competing evidence collector or trust service. Typed errors preserve the failing phase, stable reason and actual native numeric error without raw input, private roots, whole environments or inferred game/backend diagnoses.

### Requester-directed implementation choice supplement

The requester asked to reduce necessary new code through actual existing implementations, not treat a source review as code adoption. The detailed implementation plan must compare #3 reuse, standard APIs, a small external library, thin Pear glue and unavoidable new policy for leases, staging/temp files, descriptors/syscalls and streaming hashes. Preserve the existing strict JSON parser unless a concrete semantics-preserving reduction justifies replacing it. Rust std file locks, tempfile, rustix and nix are candidates to assess, not dependencies to add automatically. Locking does not prevent arbitrary same-user writes and wrappers do not establish process generations or ownership.

WhiskyKit judgments above reject incompatible complete modules, not every independent function or scenario. Compare a small direct Swift portion/test, narrow adaptation and existing #3 behavior at the actual useful boundary. Preserve Swift, headers and GPL provenance if code is directly adopted; do not replace this decision with another broad hash collection or imply that design/test-case references are imported code. The implementation plan records the chosen reductions and remaining verification.

### Activation and mutable storage

Local activation accepts already acquired verified inputs; download/authentication is out of scope. Prefer manual payload preparation using existing OS tools and a read-only payload precondition, then stage only owned activation metadata, verify the complete selected records/payload closure, select the content-identified version atomically, and lease it for the run. Exact at-use execution and namespace guarantees remain mandatory. Refuse unknown versions, incompatible families, unsafe aliases and incomplete artifacts. Retain the old active version across cancellation, failed verification or interruption; do not build a general installer/updater framework.

Do not execute the imported pathname after a one-time metadata check. Freeze a concrete macOS at-use ownership/activation mechanism and threat model in the implementation plan; prove replacement, symlink/hardlink, concurrent activation and stale-path cases with controlled mutations before calling the race closed. Mode bits or a cooperative lock alone are insufficient evidence against arbitrary same-user writers. If the selected mechanism cannot establish its declared guarantee, reject the configuration and report the remaining boundary. These controls are not a hostile-game sandbox and do not disable normal macOS protections.

Mutable roots are separately owned, descriptor-relative and non-overlapping. Prefix identity includes runtime compatibility family and game/library context; save locations preserve user ownership. Acquire an OS-held cross-process lease before mutation or launch, retain it through owned cleanup, and use a bounded durable local journal for interruption/crash states. A stale PID file is not a lease. Never migrate an incompatible prefix in place or silently select the previous runtime against changed state. Recovery preserves current data and refuses uncertain ownership; manual new-prefix and previous-compatible-version selection are sufficient. Restore/destructive data actions require a separate explicit user action and are not automatic profile operations.

Cache identity reuses lock/artifact/profile, translator/configuration, ABI and CPU-feature requirements. Unknown or changed identity forbids reuse; cache remains disposable and is never the sole runtime component. Persistent FEX cache implementation is not part of this task.

### Processes and #9/#10 separation

Retain #3's direct-child reservation through group signaling and reaping, bounded nonblocking pipes and native creation identity. Add explicit cancellation and bounded graceful/forced cleanup. Only exact owned sessions/process generations may be signaled. No `killall`, process-name scan, global Wine shutdown or unrelated-prefix server command is allowed.

Compare a single foreground supervisor with #3 cleanup, OS-held leases and a small durable incomplete-run journal against a controller/custodian. Choose the smallest structure that satisfies the existing cancellation/crash/ownership checks. A custodian is not predetermined: record a concrete failure the simpler design cannot handle before adding a process or protocol. Abrupt death may yield an explicitly incomplete run and quarantined prefix with manual new-context recovery, never asserted automatic cleanup. Detached helpers require attributable ownership/session association; ambiguity yields an explicit unsupported or cleanup-failed state, never speculative PID termination or fabricated complete cleanup. Real Wine/Steam helper behavior remains a later integration gate, while owned detaching fixture controls are required here.

Finalize the launch request before observer readiness. Require an acknowledgement bound to exact request bytes, run/capture identity and declared coverage before a covered launch. Preserve per-producer sequence/previous links and exact exit references. Wrong, stale or unavailable readiness prevents covered execution; later gaps remain incomplete. #9 owns lifecycle and cleanup; #10 owns backend acknowledgements, observation generations, gaps and host/module coverage. Backend synchronous replies, observer readiness and child entry-point progress are different events. The fixture peer is synthetic and cannot establish Rosetta independence.

### Megabonk profile facts

| Field | Planning evidence | Intended handling |
|---|---|---|
| Store/App ID | Official baseline and Issue: Steam `3405340` | Explicit identity in the versioned profile; generic consumer |
| Executable | `Megabonk.exe` in the existing graphics audit and untracked local experiment source | Explicit guest-relative executable, never a size heuristic; no game bytes imported |
| Game/build identity | September 27 observation: game 1.0.69, Windows depot 3405342/manifest 446680890915713051; App BuildID not established | Preserve dated provenance; current build/Steam identity remains unknown until independently supplied/checked |
| Arguments | Local experiment used `-force-d3d11`, window/size arguments and a local Unity log path | Record as historical experimental arguments, not verified native defaults; only approved bounded arguments/private path resolution enter execution |
| Settings/save location | Untracked local script reads `AppData/LocalLow/Ved/Megabonk/Saves/LocalDir/config.json` beneath a chosen Wine user | Historical candidate configuration path; actual save inventory, Wine user mapping, persistence and current native applicability are unverified. Do not guess by ambient USER or treat missing files as no saves. |
| Steam and optional features | Existing Rosetta experiment signed into official Steam; sustained save/relaunch and optional features not qualified | Normal official Steam path remains required downstream. No ownership bypass, success stub or supported `steam_appid.txt` route; overlay/cloud/achievements/controller/Discord remain explicitly untested unless evidence is supplied. |
| Runtime/graphics compatibility | #5/#7 are component results; no final product artifact/family or game record | Unselected/unknown state must refuse real eligible launch until exact prerequisites exist; native launcher success does not change this. |

The untracked local launch script was inspected read-only for dated hints. It is tied to an x64 Rosetta runtime, writes `steam_appid.txt` and raw experimental metadata, and is not reusable production code or public evidence. The profile's sanitized notes must distinguish inspected hints from independently established facts. No live Steam prefix, proprietary payload or saves were read or modified.

Technical skills: task-start and todo apply to preparation; task-stage-report and task-final-report will be loaded when their approved checkpoints apply. Apple Metal expertise is not applicable: this scope does not touch shaders, GPU capture, presentation or metal-cpp lifetimes. Existing C bridge/system interfaces are reused with reviewed ABI ownership; no new Metal diagnostic is proposed.

## Document Location Judgment

This requests approval for the following bounded official documentation paths. Read each existing file again before its eventual edit. Plans/reports/evidence stay in `mydocs/`; no manuals, roadmap rewrite or new documentation root is proposed.

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| CLI, local activation/setup and manual recovery guide | Official contributor/development guide, with fixture and production limits | Developers and CLI testers | `docs/development/runtime-supervisor.md` | `manager/README.md`, `mydocs/manual/` | Reusable procedures belong with current official build/development guides, not task workflow manuals. |
| Profile facts, provenance, unknown features and path rules | Official profile/contributor guide | Profile contributors and testers | `docs/game-profiles.md` | `profiles/README.md`, `mydocs/tech/` | Companion human guidance keeps public profile/evidence meaning in the official root. Machine-readable profiles remain under profiles. |
| Existing contracts and narrow index/architecture links | Official integration specification/navigation | #9/#10 and future frontend contributors | Existing `docs/runtime-contracts.md`, `docs/README.md`, `docs/architecture.md` | New duplicate specification or delivery plan | Update only implemented surfaces and explicitly versioned behavior; preserve ownership and qualification limits. |
| Native manager, scoped rules and notices | Source/implementation constraints | Contributors | `manager/`, including `AGENTS.md` and reviewed provenance/notice records | `experiments/manager/` | Production source must be distinct from preserved historical comparison. Create rules with implementation, not an empty directory. |
| Versioned profiles, provenance and scoped rules | Machine-readable product/test inputs | Consumers and profile contributors | `profiles/`, including `AGENTS.md` | `docs/schemas/`, game code in manager | Declarative shared inputs, no proprietary data and no App ID code branches. |
| Any required versioned schema extension | Machine-readable integration contract | All consumers | `runtime/contracts/` | New manager-specific protocol/profile framework | Reuses existing source of truth and explicit version transitions; preserve v1. |
| Selected-file upstream review and verification evidence | Task-specific research/evidence | Requester and reviewers | `mydocs/tech/task_m1_9_reuse.md`, `mydocs/working/task_m1_9_stage{N}*.json` | `mydocs/manual/`, public support record | Dated reuse decision and synthetic evidence do not become normative policy or game qualification. |
| Plans, reports and board | Work artifacts | Requester, reviewers and agents | Existing `mydocs/plans/`, `working/`, `report/`, `orders/` | `docs/` | Preserve Issue/stage approval and outcome history. |

## Expected Changed Files

New, exact module/test names to be frozen after task-plan approval:

- `manager/` — Rust package/lock, native modules, scoped rules and attribution/dependency inventory; no UI.
- `profiles/` — versioned Megabonk profile, two redistributable fixture profiles, sanitized provenance and scoped rules.
- `tests/manager/`, `tests/profiles/` — native lifecycle/at-use tests and independent fixture/oracle scenarios; task9 companion child/peer fixtures.
- `docs/development/runtime-supervisor.md`, `docs/game-profiles.md`.
- `mydocs/tech/task_m1_9_reuse.md` and sanitized stage evidence as needed.

Modified only where required:

- `runtime/contracts/` registry and a new explicit supported version if Stage 1 confirms a representation gap; preserve v1 semantics and historical examples.
- `tests/contracts/` for new-version/native parity expectations; use existing oracle and fixture factory.
- Existing `docs/runtime-contracts.md`, `docs/README.md`, `docs/architecture.md` for narrow implemented-interface guidance/links.
- Existing experiment build/capture seams only if direct reuse requires them; preserve comparison inputs/reports and identify changed evidence scope. Prefer task9 adapters importing unchanged helpers.
- `.gitignore` only for necessary task9 outputs not already covered by `/.build/`.

Task artifacts:

- `mydocs/orders/20261008.md` — add #9, preserve existing rows.
- `mydocs/plans/task_m1_9.md` — this plan.
- `mydocs/plans/task_m1_9_impl.md` — only after task-plan approval.
- `mydocs/working/task_m1_9_stage{N}.md` and `mydocs/report/task_m1_9_report.md`.

No task6, Wine/FEX/DXMT source/patches, retained build/prefix or live game/account files are planned changes. Shared board/docs need a reviewed integration check before publication, preserving other tasks' concurrent changes.

## Tentative Stages

- **Stage 1 — Freeze reuse and production boundaries**
  - Retain complete pinned-file/license review, chosen native module reuse, exact profile/schema gaps, CLI commands, independent policy, activation threat model and the smallest crash/detachment ownership structure.
  - Introduce scoped rules beside real initial implementation artifacts and any approved contract extension. Verify version/research rejection and independently evaluated shapes without real runtime claims.
- **Stage 2 — Native validation and local activation**
  - Implement native shared-record consumers and strict errors; verified owned staging/activation, runtime leases and at-use enforcement.
  - Test wrong versions/bytes/policy, unsafe aliases/references, activation interruption and concurrent mutation/replacement. Imported bytes cannot be executed merely because their metadata validated.
- **Stage 3 — Owned supervision and failure recovery**
  - Adapt spawn/pipe/cleanup logic, generation reservations, cancellation, crash journal and the approved minimum ownership structure; add synthetic exact-request readiness peer.
  - Test exit/crash, both pipe-setup failures, timeouts, output bounds, crash/disconnect, detach controls and unrelated sentinels. Report ownership/cleanup gaps honestly.
- **Stage 4 — Scoped state and two fixture profiles**
  - Implement prefix/settings/save-root allocation, cross-process leases, cache isolation, preservation and manual compatible-version recovery.
  - Exercise A/B profiles concurrently and sequentially with different settings/argv/data; assert no cross-profile change and no runtime mutation. Verify interruption, incompatible prefix refusal and preserved old data.
- **Stage 5 — Megabonk profile and official CLI guidance**
  - Commit the versioned researched profile, provenance/unknowns, manual setup/recovery and #9/#10 interface guide; supported launch remains gated.
  - Verify profile/schema validity, unknown-to-launch refusal, generic consumer behavior, documentation commands against fixture setups and private-data exclusions.
- **Stage 6 — Fresh fixture reconstruction and handoff**
  - Rebuild task9 manager/fixtures in fresh outputs from pinned inputs, rerun all required integrated checks, retain sanitized source/binary/case identities and map every #9 criterion.
  - Final report, board and final commit through approved workflow; then concrete PR publication approval. No automatic Issue closure or merge.

Every stage ends with passing required checks, a stage report and bundled source/report commit before the next explicit continuation. The implementation plan has its own approval checkpoint; this task-plan approval does not preapprove all stages.

## Verification Plan

Planning availability: native ARM64 macOS 26.5.2, CPython 3.14.4, Rust/Cargo 1.94.1, Xcode 26.6 (17F113), SDK 26.5 were observed. SDK query returned success with filesystem-event/cache warnings; retain material tool errors in later build evidence. These are observed development tools, not minimum supported/release versions. #3 pins `libc = 0.2.186` and five hashed CPython 3.14/macOS ARM64 wheels. Task9 cache/dependency availability and new native output are not yet verified; do not borrow another task's venv/build or weaken locks. Any added dependency needs exact version/hash/license review before use. Existing Linux CI uses Python 3.12 and cannot silently reuse this macOS wheel lock.

### Evidence and false-success mapping

| Claim/check | Reused producer/checker | Required failure controls and invalidation |
|---|---|---|
| Shared structure and eligibility | `tests/contracts/validate.py` and current behavioral suites | Valid JSON with wrong digest, duplicate keys, unknown version/operation, incomplete identities, fixture promotion, submitted self-trust and stale/missing qualification must fail. Relevant schema/producer/policy/input changes invalidate affected evidence. |
| Native argv/environment/reaping/privacy | Existing Rust/C fixture, 55 corpus cases, two pipe faults and Python capture/oracle | Independently observed child traces, exact reaping/identity disappearance and unrelated sentinel survival remain mandatory. Exit zero alone, observer flags, skipped case or watchdog intervention never pass. New source/binary/fixture/budget changes require affected reruns. |
| Runtime immutability/at-use identity | Task9 controlled mutation and activation tests, existing descriptor/hash primitives | Bad payload, changed executable/library/ancestor, symlink/hardlink aliases, concurrent activation and interruption cannot execute mismatched bytes or mutate active content. Test at the validation-to-use boundary, not only lexical paths. |
| State isolation and preservation | Existing fixture factory plus A/B task9 profiles | Distinct settings/argv/prefix/saves, wrong-family/overlap rejection, busy lease, interrupted setup and manual recovery with unchanged old data. Hash inventories prove unaffected runtime/other profile contents; a passing local marker alone is insufficient. |
| Crash/detach ownership | Existing generation bridge plus task9 independent finite child/crash controls | Supervisor crash, lease loss, detached helpers, identity substitution, withheld pipes and denied cleanup preserve original errors. Unknown identity must refuse signaling/reuse, and unrelated processes survive. |
| Observer handoff | Existing v1 events/eligibility tests plus synthetic peer | Wrong/stale request ack, absent readiness, delayed readiness, sequence gaps and missing exit basis produce refusal/incomplete results. No actual module collector or Rosetta-free claim from the peer. |
| Megabonk metadata | Existing dated evidence/audit, later independently supplied metadata if available | Research hints cannot imply current build, save persistence or supported Steam path. Missing prerequisites refuse launch; no `steam_appid.txt` bypass or guessed user/save path. |

Unchanged evidence is reused only for its exact claim/input scope. Preserve historical successes and failures; do not rewrite them to match task9. All required native #9 checks run on the current built manager, independent fixture records and exact activated bytes. Reuse testing infrastructure, not old passing outcomes for changed boundaries.

### Stage Verification

- Stage 1: component/license/source-map review; JSON/schema and independent oracle checks of approved version transitions; preflight tool/dependency inventory; documentation/location and ownership review.
- Stage 2: native parser/semantic parity and hash/path/policy rejection; concurrent stage/activate/use mutation controls; selected native build/architecture/dependency checks.
- Stage 3: existing relevant 55-case behavior plus cancellation/crash/detach cases; both pipe faults; direct-child reaping, exact identity disappearance, unrelated sentinel survival, bounds and synthetic handshake negatives.
- Stage 4: A/B profile isolation, cross-process lease/concurrency, owned write boundaries, cache identity, interrupted setup and manual recovery; hashes prove old save/settings/runtime/other-prefix preservation.
- Stage 5: profile checks through the shared oracle/native consumer; fixture-based documentation command walkthrough; review English text, provenance, unknowns and privacy; offline governance/link checks.
- Stage 6: fresh native build and all task9 required integrated cases, baseline contracts and affected helper regression suites; package/dependency inspection and sanitized evidence assessment on exact final inputs.

Baseline reusable commands (not all executed during planning):

```sh
python3 -B experiments/manager/reproduce.py --check-report experiments/manager/results/reproduction.json
python3 -B experiments/manager/compare.py --check-report experiments/manager/results/comparison.json
python3 -B tools/check_governance.py
.build/task9/venv/bin/python -B tests/contracts/validate.py --check-schemas --check-examples
.build/task9/venv/bin/python -B -m unittest discover -s tests/contracts -p 'test_*.py'
python3 -B -m unittest discover -s experiments/manager -p 'test_*.py'
```

The first three passed in planning on the unchanged base. The governance result was 25 documents/231 local targets. Contract/native functional suites were not rerun in planning. Detailed native task9 commands, locked dependency setup, preserved budgets and retention paths belong in the implementation plan after approval. New tests use native Rust tests and existing Python unittest/oracle tooling; no new generic runner is planned.

### Integrated Verification

- Every #9 acceptance item maps to current execution or explicit research/unsupported evidence: version/path rejection; child exit/crash; bounded redaction; prefix/settings/save isolation; immutable runtime; unrelated Wine/process/prefix survival; honest versioned Megabonk profile; documented CLI/manual recovery.
- Two profiles use the same generic manager with different settings/argv/state. No Megabonk/App ID branch or secret fixture bypass can authorize runtime launch.
- Required process ownership/reaping, native errors and cleanup assertions remain intact under cancellation, manager death and detached-control scenarios. An unsupported real Wine/helper scope is named and cannot be reported as complete supervision.
- Native architecture is inspected for the manager and any actually selected helper. Fixture host execution remains distinct from complete game/runtime Rosetta evidence and distribution authorization.
- Fresh task9 outputs identify source, schema, policy, toolchain/SDK/dependency, fixture, activated artifact, binary and case results; skips, missing observations and failed attempts remain explicit.
- No other task build/cache/prefix is modified. Heavy Wine/FEX/GPU/game runs are not required for fixture acceptance and are not started by this plan.
- `git diff --check` passes. Task-owned worktree status is clean before PR preparation; preserve other workers' rows/documents and required artifacts during integration.

## Risks

- **Contract representation gaps:** v1's narrow operation/environment/profile vocabulary cannot be stretched silently. Freeze minimal explicit evolution and refusal semantics; preserve old consumer behavior and the #9/#10 boundary.
- **Pathname and concurrent writer races:** prototype inode/hash checks alone are insufficient. Define the ownership model and test actual activation/use mutation before claiming closure; refuse guarantees the implementation cannot provide.
- **Crash or detached-process ambiguity:** a reaped PID or liveness probe cannot authorize signaling. Keep reservations, generation/session evidence, minimal crash journal and conservative recovery refusal; real Wine/Steam coverage needs later integration evidence.
- **Runtime readiness versus #9 completion:** #5/#7 results and #1 closure do not automatically produce a complete product artifact. Complete fixture implementation while making unavailable real runtime/Steam prerequisites visible; do not add #6 as a new acceptance dependency.
- **License/language drift:** source designs/tests can carry GPL provenance. Retain exact origins/terms, preserve Swift when directly reused, and review compatible combinations before code adoption; no wholesale import, transliteration or project-license decision.
- **Historical game/path hints:** local Rosetta script paths and old game identities may be stale or only configured assumptions. Keep provenance/unknowns, read no private live state, and reject unsafe or unverified mapping rather than guessing.
- **Shared host/integration changes:** #6 and other tasks may advance while #9 is staged. Recheck current branches/reports and preserve board/docs at integration; source/build changes invalidate affected evidence, not every unrelated check.
- **Deadline/privacy false success:** old startup failure is unresolved, raw streams can hold arbitrary secrets, and stronger budgets do not prove reliability. Preserve approved safety assertions/bounds and allowlisted public output; no timing or game-support inference.

## Original Task-plan Approval Request (Approved)

- Approve #9's bounded scope, six tentative stages, Rust/#3 reuse, component-level WhiskyKit judgments and production ownership/at-use verification requirements.
- Approve the official documentation locations and potential smallest explicitly versioned contract extension; exact fields/CLI/module paths and verification commands will be reviewed in the implementation plan.
- Preserve all listed exclusions, independent policy, #9/#10 responsibilities, two-profile isolation and historical failures/evidence limits.

Task-plan and supplemented implementation-plan approval are recorded below. Stage 1 is implemented and verified in its stage report; Stage 2 requires explicit continuation. Full runtime/game execution, later stages, PR publication, Issue closure and merge retain their separate approval boundaries.

## Approval Record

On October 8, 2026 the requester instructed the originating chat to deliver the requested supplements to this session and proceed with the work. The authorized relay approves the existing task-plan direction, the narrow implementation-choice/partial-reuse/minimal-structure supplements above and detailed implementation planning. It expressly preserves the implementation-plan approval checkpoint and stage-by-stage continuation; the same task-plan approval is not requested again.

The subsequent requester review approved the detailed implementation plan with three narrow supplements: preserve purpose-specific qualification_run/supported_launch admission; bound observer deadlines, framing and backpressure; and test declared dynamic dependencies using small native executable/dylib fixtures. Stage 1 is authorized through verification, report and bundled commit. Stage 2/3 execution and supervision gates remain unperformed until their separately approved stages.
