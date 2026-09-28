# Task Plan: Define runtime contracts and choose the manager language

Status: the maintainer approved this task plan, scope and document locations on September 28, 2026, together with Issue #1. Detailed implementation planning is authorized. Stage implementation remains subject to the implementation-plan approval checkpoint; no production manager or passing runtime claim is included in this record.

GitHub Issue: [#3](https://github.com/postmelee/pear/issues/3)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Work branch: `codex/task3`

## Purpose

Define the versioned data and ownership contracts that let independently developed Pear components agree on source identity, compatible runtime selection, bounded launch requests, failures, and qualification evidence. Deliver schemas, redistributable examples, and executable contract tests that distinguish a valid research record from a complete, executable or qualified configuration.

Choose the initial native runtime-manager language through the same bounded experiment in Rust and Swift. Compare functional correctness, macOS packaging and signing requirements, foreign-function interfaces, dependencies, testability, and maintenance cost. Manager startup or build measurements are supporting evidence for this choice, not evidence that either language makes Megabonk or the CPU translator faster.

## Background

The [runtime architecture](../../docs/architecture.md) proposes runtime-lock, artifact, profile, run, and qualification records, but these are not implemented contracts. [Issue #1](https://github.com/postmelee/pear/issues/1) will independently establish actual source and toolchain inputs. [Issue #2](https://github.com/postmelee/pear/issues/2) provides bounded host-probe evidence; its probe protocol is not automatically the product-wide format. [Issue #9](https://github.com/postmelee/pear/issues/9) needs the manager and launch contract, while [Issue #10](https://github.com/postmelee/pear/issues/10) needs process identity, observation readiness, lifecycle events, and privacy rules.

The [engine and language study](../../docs/research/engine-and-language-options.md) makes Rust optional and retains upstream languages for Wine, FEX, and DXMT. The [platform reuse study](../../docs/research/platform-reuse.md) supports inspecting launcher and declarative-profile designs without importing their unrelated runtime assumptions or treating suggested recipes as tested compatibility. The [delivery plan](../../docs/delivery-plan.md) allows #1 and #3 to proceed independently; this task must not add a new acceptance dependency on #1.

A read-only local preflight on September 28, 2026 found Apple Swift 6.3.3 targeting ARM64 macOS, Rust/Cargo 1.94.1, and macOS SDK 26.5 installed. These observations remove an immediate tool-installation blocker for the bounded comparison; they are not approved release pins, verified prototype results, or a broader host-support claim.

## Scope

### Included

- Versioned JSON contracts for the runtime lock, runtime artifact, game profile, launch request and lifecycle, classified failure, run record, and qualification record, including shared source/component identity and evidence references.
- Structural and semantic validation, record identity and digest rules, schema evolution, compatible-component families, and explicit proposed, built, tested, and supported states with unknown, unsupported, and failed observations.
- Ownership rules for immutable runtime artifacts and separately writable prefixes, saves, caches, logs, temporary staging, and evidence. Cache identity and invalidation requirements follow the architecture; production cache or updater implementation is deferred.
- Bounded declarative profile operations, scoped environments, argument arrays, host and guest path distinctions, and rejection behavior for unsafe paths, unknown versions, incompatible records, and unsupported operations.
- A shared, redistributable fixture corpus and equivalent Rust and Swift manager experiments: read and validate records, resolve a fixture launch, start an owned test child, collect bounded redacted output and termination, and classify failure.
- A documented manager-language decision, reproducible comparison results, and contributor-facing contract documentation in English.
- A coordination contract with #1 for its source inventory and with future #9/#10 workers for supervision and observation, without implementing those issues in full.

### Excluded

- The production #9 manager/CLI, a graphical application, installers, automatic runtime activation or rollback, automatic save backup, and a public release.
- Wine/FEX/DXMT builds or ports, CPU translator replacement, Steam login, actual game installation or execution, and Rosetta-free game qualification.
- Selecting the actual Wine/FEX/DXMT revisions, patch contents, source hashes, or release toolchain pins owned by #1 and later build tasks.
- A complete process/module collector or proof that every Steam helper is observed; #10 owns this implementation and its architecture evidence.
- New restricted host-capability execution, security-policy changes, collection of private signing material, or a claim that signing a fixture establishes unrestricted distribution.
- Importing a full third-party launcher or copying code, game profiles, or tests without an attributable license and reuse review.

## Design Direction

### Contract ownership and handoff

| Producer / owner | Owned artifact or behavior | Interface agreed in this task |
|---|---|---|
| #1 — source qualification | Actual inventory at proposed `runtime/sources/manifest.json`; real revisions, hashes, patch inventory, toolchains, notices, gaps, and source evidence | Stable component IDs; source locations and immutable refs; typed content digests; ordered patches and digests; toolchain/SDK identity; host and guest targets; license/notice and contribution-policy references; evidence and status. |
| #3 — this task | Versioned contracts at proposed `runtime/contracts/`, validation rules, examples, comparison fixtures, and the manager-language decision | Structure and meaning of shared records, incomplete-state representation, record/digest references, rejection rules, and compatible schema evolution. This task does not overwrite #1's inventory. |
| #9 — future supervisor | Process creation, termination and reaping; prefix/data mutation; immutable-runtime selection; production launch behavior | A launch request and lifecycle contract, bounded output/failure records, and the observer readiness handoff. |
| #10 — future observer | Process/module observation and evidence attribution | Run identity; process identity beyond a reusable PID; required observation readiness; ordered or explicitly incomplete events; host versus guest architecture; detached-helper coverage; redaction and gaps. The observer does not independently reap or terminate the supervisor's children. |

Agree the #1/#3 handoff concepts before schema details diverge. #3 can use clearly labeled incomplete research records and locally generated redistributable fixture records while #1 is in progress. Schema-valid incomplete records must fail launch or qualification eligibility when required identity or evidence is missing. No invented hash or guessed version may become an executable production lock. Final import of #1's actual inventory and qualification of a resulting runtime remain later integration work; #3 can complete its contract and comparison independently.

### Record meaning and validation

- Give every record an explicit kind and schema version. Define supported-version handling, required fields, extension policy, stable identity, digest computation, and cross-record references. Keep JSON parsing checks, schema checks, and semantic eligibility distinct; a schema match alone cannot authorize launch or support status.
- Reject ambiguous or malformed inputs, including duplicate keys, invalid digest forms, unsupported schema versions or operations, incompatible component/ABI families, and mismatched lock/artifact/profile/evidence references. Document which optional unknown observations can be retained and which missing required fields block execution or qualification.
- Separate immutable source/build provenance from actual execution and qualification results. A compiled fixture, an available entitlement declaration, or a supported-state label without matching evidence cannot promote a runtime or game profile.
- Bind a run and qualification to the exact applicable runtime-lock/artifact, profile, game/Steam identity, test revision, configuration, and evidence. A relevant change invalidates the affected qualification. Missing required process or module coverage remains unknown and prevents a Rosetta-independence claim.
- Model distribution scope independently from developer execution. Reuse #2's evidence through explicit references or an adapter where appropriate; do not rewrite its committed observations or broaden its claims.
- Keep game identity and guest PE targets separate from native Mach-O host architecture. A guest x64 executable is expected input; it must not be confused with a Rosetta-translated Intel host process.

### Execution and state boundaries

- Launch descriptions contain an explicit executable selection, argument array, working-directory policy, allowed environment fields, runtime/profile identity, and owned writable roots. They are not downloaded shell scripts and do not interpolate shell commands.
- Define path semantics for host-relative artifact entries, local user-owned storage, and Windows guest paths separately. Specify rejection of traversal, unintended absolute paths, symlink escapes from owned roots, unsafe operations, and writes to immutable runtime content. The production supervisor remains responsible for enforcing these rules at use time.
- Define ownership and compatibility for prefixes and caches. An incompatible prefix upgrade must not mutate the only usable copy; cache entries must include the guest/runtime/translator/ABI identities needed for invalidation and remain disposable. The contract describes required behavior without implementing migration or recovery here.
- Define the supervisor-to-observer readiness and completion handshake before future parallel #9/#10 implementation. A required observation gap must be represented rather than silently launching and asserting complete coverage. Process identity must include creation or equivalent generation information; ordering, dropped events, detached processes, and incomplete shutdown need explicit outcomes.
- Separate local operational data from public evidence. Use allowlisted structured fields, bounded output, and redacted failure details; do not serialize whole environments, account tokens, private paths, authenticated prefixes, or saves. Synthetic secret markers are appropriate rejection/redaction fixtures, not real credentials.

### Rust and Swift comparison

- Implement the same fixture protocol and input corpus in both languages, using the same success and failure expectations. Keep the experiment under `experiments/manager/` and label it as a comparison prototype; it is not the production CLI.
- Use a small redistributable native child with deterministic output and exit modes. Test manifest/path/version rejection, scoped environment, argument preservation, bounded stdout/stderr, success, nonzero exit, signal termination, timeout, and owned-child cleanup. Reuse suitable #2 fixture behavior or code only after reviewing its interface and attribution; do not silently turn the host-probe runner into the manager API.
- Include a narrow C-ABI interaction when needed to compare actual macOS process or inspection integration. Specify ownership, errors, callback/thread behavior, and panic/exception containment without exposing guest pointers or C++ objects through the management contract.
- Set the evaluation rubric and any measurements before running the comparison. Functional and privacy failures are disqualifying until resolved. Evaluate repeatable builds, package contents and native slices, signing/runtime dependency requirements, dependency and license footprint, test/debug experience, FFI surface, readability, and contributor maintenance cost.
- Measure only relevant prototype costs, such as clean/incremental build time, launch latency, binary/dependency size, or memory use where tooling can measure them reliably. Record equivalent release settings, toolchain versions, sample procedure, warm/cold conditions, and measurement limits. Keep controlled runs separate from concurrent heavy builds. Do not extrapolate results to game frame rates or translator performance.
- Record a reasoned choice and reconsideration triggers. A language is not selected merely because it is memory-safe, native to Apple platforms, already installed, or presumed faster. If equivalent behavior or a material packaging requirement cannot be evaluated, record the gap and keep that part of the decision unresolved rather than inventing a passing result.

## Document Location Judgment

This plan requests approval to extend Pear's existing `docs/` root for reusable contributor and integration documentation. It preserves the current architecture and research locations. Machine-readable contracts belong with their runtime consumers; task-specific progress remains in `mydocs/`. No operating manual changes are planned.

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| `docs/runtime-contracts.md` | Official contributor/integration specification, versioned with the schemas; initially proposed until implemented and verified | Runtime, manager, observer, profile, and tooling contributors | `docs/runtime-contracts.md` | `runtime/contracts/README.md`, `mydocs/tech/` | Explains public ownership, validation, evidence and evolution rules beside the architecture; schemas remain the machine-readable source of truth. |
| `docs/decisions/manager-language.md` | Official architecture decision with bounded research evidence and reconsideration triggers | Maintainers and manager/UI contributors | `docs/decisions/manager-language.md` | `docs/research/engine-and-language-options.md`, `mydocs/working/` | Keeps the concrete manager decision separate from the broader historical language survey and temporary stage reports. |
| `runtime/contracts/` schemas and examples | Versioned machine-readable integration contracts and clearly labeled examples | Implementers and automated validators | `runtime/contracts/` | `docs/schemas/`, `manager/` | Allows #1, #9, #10 and build/test tools to consume one neutral contract without coupling it to a chosen manager implementation. |
| `experiments/manager/README.md` and sanitized comparison records | Reproducible experiment instructions and supporting evidence; not end-user launch instructions | Contributors reproducing the language comparison | `experiments/manager/` | `docs/`, `mydocs/working/` | Keeps commands, fixture limitations and machine-readable comparison evidence adjacent to the prototypes; the official decision links the relevant evidence. |
| `docs/README.md` and a narrow contract/decision link in `docs/architecture.md` | Official index and existing architecture | Contributors and maintainers | Existing paths | New duplicate overview or a root README rewrite | Makes the approved specification discoverable while preserving established research and product-status wording. |
| Plans, stage reports and final report | Issue-specific work artifacts | Task requester, reviewers and agents | `mydocs/plans/`, `mydocs/working/`, `mydocs/report/` | `docs/` | Records approval, execution and verification without creating another normative contract or support claim. |

## Expected Changed Files

New, with exact filenames and schema tooling to be fixed in the implementation plan:

- `runtime/contracts/` — versioned schemas, shared definitions, and labeled examples; no actual #1 source inventory edits.
- `tests/contracts/` — structural and semantic validation, cross-record identity, path/operation, status, and privacy fixtures.
- `experiments/manager/` — shared corpus/child fixture, bounded Rust and Swift prototypes, comparison runner, reproducibility instructions, and sanitized results.
- `docs/runtime-contracts.md` — the reusable contract and ownership specification.
- `docs/decisions/manager-language.md` — comparison evidence, decision, limits, and reconsideration conditions.

Modified only as needed:

- `docs/README.md` and `docs/architecture.md` — narrow links and consistency updates after the contract and decision are verified.
- `.gitignore` — only if new prototype/build/result locations require exclusions; private data and generated binaries remain excluded.

The task owner coordinates edits to shared documentation and the daily task board across #1 and #3. Parallel workers do not independently overwrite those files or the other issue's source inventory.

Task artifacts:

- `mydocs/orders/20260928.md` — coordinated by the task owner because #1 is active in parallel.
- `mydocs/plans/task_m1_3.md`.
- `mydocs/plans/task_m1_3_impl.md` — created only after this task plan is approved.
- `mydocs/working/task_m1_3_stage{N}.md`.
- `mydocs/report/task_m1_3_report.md`.

## Tentative Stages

- **Stage 1 — Contract boundaries and shared identity**
  - Establish the #1/#3 field handoff, record kinds and lifecycle, source versus runtime identity, version/digest rules, ownership, and proposed schema structure.
  - Review incomplete research records and explicit non-eligibility cases without waiting for actual #1 component pins.
- **Stage 2 — Versioned schemas and rejection fixtures**
  - Implement the seven record contracts and shared definitions with structural and semantic validation; document paths, bounded operations, evidence linkage, readiness, and redaction.
  - Verify complete fixture acceptance and malformed, unknown, incompatible, unsafe, incomplete, and unsupported cases. Synthetic fixture evidence cannot become a production support claim.
- **Stage 3 — Equivalent Rust and Swift experiments**
  - Implement the same manifest/child/output/failure behavior and narrow native interface in both comparison prototypes using one corpus and rubric.
  - Verify functional parity, containment, redaction, and packaging requirements before considering measurements.
- **Stage 4 — Comparison and manager-language decision**
  - Run the agreed reproducible comparison, inspect native packaging/dependencies/FFI and maintenance tradeoffs, and write the architecture decision with measured limits.
  - Identify concrete interfaces and remaining obligations for #9 and #10; keep their production implementations outside this task.
- **Stage 5 — Reproduction and contract handoff**
  - Repeat validation and both experiments from clean generated outputs, finalize the contributor specification and decision, and map each #3 acceptance criterion to evidence.
  - Verify #1 and #9/#10 handoff consistency without requiring #1 to have completed its source inventory or implying a working runtime.

Each stage requires its own verified report and task requester approval before proceeding to the next stage. These are tentative stages; exact files, commands, and bounded checks belong in the separately approved implementation plan.

## Verification Plan

### Stage Verification

- Stage 1: review the field/ownership matrix against #1 and the existing architecture; trace every #3 Issue criterion and each future consumer to an explicit contract; reject examples that imply nonexistent source hashes or supported features.
- Stage 2: execute schema and semantic fixtures for every record, valid incomplete research states, unsupported schema versions, duplicate keys, cross-record mismatch, invalid component families, path escapes, illegal operations, missing observation coverage, and redaction. Show that syntactic validity and launch/qualification eligibility produce distinct outcomes.
- Stage 3: run one functional corpus against both language prototypes. Assert equivalent classified results, bounded termination/output, scoped arguments/environment, no unrelated process or prefix effects, and explicit native interface ownership. Record actual toolchains and native architectures.
- Stage 4: use the predeclared rubric and controlled comparison procedure; retain reproducible, non-sensitive measurements and explain incomparable or unavailable results. Check signing/package claims against the evidence actually collected, without treating fixture packaging as general distribution approval.
- Stage 5: recreate generated outputs and rerun documented checks; review all examples and results for synthetic-versus-real identity, privacy, evidence scope, and reproducibility; verify links and the #1/#9/#10 handoff against the final contract.

### Integrated Verification

- Every required contract has a version, ownership model, accepted/rejected fixtures, and an evolution policy. Valid incomplete records cannot silently pass launch or qualification gates.
- Unknown versions, incompatible components, unsafe paths, unsupported operations, wrong evidence identities, and incomplete required observation coverage have documented and tested outcomes.
- Rust and Swift execute the same bounded comparison with a reviewable functional result and maintenance/packaging decision; no language selection rests on an unmeasured game-performance claim.
- The source-inventory handoff lets #1 publish real findings without a competing schema owner. #3 does not require a finished #1 inventory to complete its own contract or manager decision.
- Future #9 and #10 implement one agreed launch/observation interface with clear process and state ownership. This task's fixtures do not assert their production integration is complete.
- Repository output contains no proprietary game files, credentials, private signing material, authenticated prefixes, personal saves, or raw private diagnostics.
- The task's committed paths are clean before PR preparation, and `git diff --check` passes. Preserve unrelated worker changes and local private inputs rather than deleting or committing them to obtain a clean status.

## Risks

- **Parallel contract drift:** #1 and #3 may assign different meanings to IDs, hashes, build targets, or evidence. Agree the handoff early, keep one schema owner, and review changes across worktrees before integration; do not edit the other task's inventory or shared board independently.
- **Premature generalization:** an ambitious schema can assume unsupported features or freeze untested implementation details. Limit required behavior to the current architecture and bounded consumer needs, version changes explicitly, and record unresolved runtime facts without placeholder success.
- **Validation confused with trust:** a matching schema or digest does not prove source authenticity, semantic compatibility, complete observation, or qualification. Keep these gates separate and test cross-record evidence and eligibility failures.
- **Unequal language experiments:** different workloads, dependencies, failure handling, build modes, or measurement conditions can produce an unjustified winner. Use common fixtures and predeclared criteria; disclose unavoidable differences and prioritize functional/maintenance evidence.
- **Prototype mistaken for product:** fixtures cannot establish robust Steam lifecycle handling, a public release, or Megabonk execution. Keep prototype paths, output scope, and downstream obligations explicit.
- **Shared Mac contention:** concurrent heavy builds or game/measurement sessions can distort timing and interfere with local state. Use task-local output directories and fixture storage; coordinate any controlled measurements and signing inspection with the other worker. Do not consume live Steam prefixes or shared app bundles.
- **Privacy and imported assumptions:** process logs, arbitrary profile commands, and copied launcher modules can carry private data or unrelated security/license obligations. Use a bounded operation set, synthetic inputs, redacted structured output, and attributable reuse decisions.

## Approval Request

- Approve the bounded #3 scope, five tentative stages, versioned contracts and semantic rejection gates, and the equivalent Rust/Swift manager comparison.
- Approve the proposed documentation and artifact locations, especially `docs/runtime-contracts.md`, `docs/decisions/manager-language.md`, `runtime/contracts/`, and `experiments/manager/`.
- Approve the #1/#3 ownership split and future #9/#10 launch/observation handoff without making #3 depend on completion of the actual source inventory.
- Retain the listed exclusions: this plan does not approve a production manager, GUI, Steam/game execution, translator replacement, runtime qualification, or general-user distribution work.

After approval, `task_m1_3_impl.md` will define concrete artifacts, verification commands, and stage commit messages. No implementation plan or source changes are authorized by this draft alone.

## Approval Record

The task requester explicitly approved both task plans and their document locations on September 28, 2026. The approved scope and exclusions above remain unchanged. The next review is the concrete implementation plan and authorization to start Stage 1; subsequent stages retain their individual report checkpoints.
