# Task #3 Final Report: Runtime contracts and manager language

GitHub Issue: [#3](https://github.com/postmelee/pear/issues/3)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Date: September 28, 2026

## Work Summary

- Target Issue: #3; five implementation stages completed on `codex/task3`.
- Delivered seven experimental version 1 contracts, an independent bounded reference validator, honest research/owned fixture examples and explicit source/supervisor/observer ownership.
- Compared equivalent native Rust and Swift experiments and selected **Rust for the new #9 manager/supervisor**, based on tested behavior, build/resource evidence and maintenance/FFI review. Swift retains documented advantages; no project-wide Rust or game-speed claim follows.
- Reproduced declared functionality from new outputs on the same Mac. This task completes the contract/language decision, not a production launcher or Rosetta-free Megabonk execution.

## Changed Files and Impact Area

| Path | Change Summary | Impact Area |
|---|---|---|
| `runtime/contracts/` | Seven closed schemas plus shared types, registry, incomplete research and owned synthetic fixture bundle | Inter-component format and evidence identity |
| `tests/contracts/` | Read-only reference evaluator, five-wheel lock and 119 behavioral/adversarial tests | Bounded parsing, relationships, eligibility, privacy and rejection |
| `experiments/manager/` | Equivalent native prototypes, shared owned C fixture, locked dependencies, controlled comparison, failure archives and empty-output reproduction | Evidence-based language choice; no production manager |
| `docs/runtime-contracts.md` | Exact version/identity/eligibility rules, actual #1 handoff and #9/#10 boundary | Contributor and integration specification |
| `docs/decisions/manager-language.md` | Rust decision, Swift alternative, measured costs, limits and reconsideration | Architecture decision |
| `docs/README.md`, `docs/architecture.md`, experiment README | Narrow current-status links and reproducible commands | Discoverability and contributor use |
| `mydocs/plans/`, `working/`, `report/`, daily board | Approvals, exact staged evidence and acceptance mapping | Workflow traceability |

Context: the approved [task plan](../plans/task_m1_3.md), [implementation plan](../plans/task_m1_3_impl.md), architecture/delivery baseline and Hyper-Waterfall v0.3.0 procedures. Existing bounded build/corpus/comparison tooling is reused for reproduction. Wine/FEX/DXMT implementation languages are retained. Newly merged #25 scoped documentation/test rules and report-template guidance were reviewed for final integration; Metal-specific expertise is not applicable to this contract/manager task.

## Document Location Verification

The [approved location judgment](../plans/task_m1_3.md#document-location-judgment) and implementation-plan table match the delivered paths. No product document was moved into `mydocs/manual` and no unrelated manual was rewritten.

| File/group | Planned Location | Actual Location | Result | Evidence |
|---|---|---|---|---|
| Contributor contract specification | `docs/runtime-contracts.md` | Same | OK | Approved plan and final specification |
| Language decision | `docs/decisions/manager-language.md` | Same | OK | Stage 4 decision, Stage 5 reproduction addendum |
| Machine-readable contracts/examples | `runtime/contracts/` | Same | OK | Registry and seven schema files |
| Validator/tests | `tests/contracts/` | Same | OK | Locked dependencies and recorded test IDs |
| Prototypes/comparison/reproduction | `experiments/manager/` | Same | OK | Sanitized public results; local outputs ignored |
| Public entry points | `docs/README.md`, `docs/architecture.md` | Same | OK | Narrow links/current-status changes |
| Plans, reports and daily board | `mydocs/` designated subdirectories | Same | OK | Five bundled stage reports and this final report |

## Quantitative Before/After Comparison

| Metric | Before #3 | Completed result |
|---|---|---|
| Implemented product-record contracts | Conceptual architecture only | Seven version 1 kinds plus shared definitions |
| Reference behavioral tests | None | 119 passing tests |
| Equivalent native corpus | None | 55 cases × two candidates; 110 passing invocations in final reproduction |
| Experiment regression tests | None | 60 passing Python tests, including 20 reproduction checks; two passing Rust fault tests |
| Manager decision | Rust/Swift unresolved | Rust selected with explicit evidence, alternative and reconsideration criteria |
| Controlled comparison | No comparable measurement | 82 retained rows: six clean builds, six incremental builds, ten warmups, 60 scored invocations; earlier failed attempts retained separately |
| Rosetta-free Megabonk qualification | Unestablished | Still unestablished; no game execution in this task |

Final Stage 4 medians for Rust/Swift were **3.670/10.659 s** clean build, **5.918/7.125 s** incremental build, **279.867/303.175 ms** manager invocation, and **2,097,152/7,061,504 bytes** launch `wait4` RSS accounting. These are whole-command fixture costs with overlapping timing ranges, fixed sampling order, retained caches and unmeasured desktop/thermal effects. They are not game FPS, power, pure language startup or process-tree peak memory results. The decision includes Swift's smaller executable and no external package dependency. Stage 5 repeats functionality, not those timings.

## Verification Results

The exact three Issue acceptance criteria are satisfied within the task's experimental scope:

| Acceptance Criterion | Result |
|---|---|
| Schemas/examples distinguish proposed, built, tested and supported states without invented hashes or results | **OK.** Separate research/fixture/runtime contexts, explicit unknown/failed/unsupported observations, exact-byte references and a later qualification overlay prevent self-asserted support. The research example stays inspectable and non-launchable. Real fixture hashes are computed; synthetic signing/policy/module declarations remain explicitly synthetic. Tests cover missing evidence, incorrect bytes, fabricated support and fixture-to-runtime promotion. |
| Architecture decision records language and evidence without presuming Rust makes games faster | **OK.** Equivalent native corpus, frozen comparison, package/FFI/dependency/maintenance review, preserved failures and same-Mac reproduction support the bounded Rust supervisor choice. No upstream rewrite, Cranelift selection or game-performance claim is made. |
| Unknown versions, incompatible families, unsafe paths and invalid profile operations have defined rejection behavior | **OK.** Closed schemas and native subset checks reject unsupported versions/fields, duplicate keys, wrong digests/kinds/families/cache identities, traversal/symlinks/nonregular references, mutable/immutable aliases and arbitrary profile commands. Rejection/privacy and ownership cases pass in the reference suite and common native corpus. Production at-use enforcement remains #9's work. |

Exact test/source identity: Stage 2 reference implementation at `91f2ef2`; final native/comparison inputs at `bd3949a`; Stage 5 runner, tests, all current schema/example and native input SHA-256 values are enumerated in the [reproduction record](../../experiments/manager/results/reproduction.json). That record also binds all ten retained historical JSON records. The report checker verifies current identities and individual test/case coverage; it does not independently authenticate a reporting host.

### Stage Verification Results

| Stage | Source revision | Evidence |
|---|---|---|
| 1 — boundaries and identity | `f03d76a` | [Stage 1](../working/task_m1_3_stage1.md): seven kinds, acyclic qualification, independent policy, ownership and JSON/design review |
| 2 — schemas and eligibility | `91f2ef2` | [Stage 2](../working/task_m1_3_stage2.md): five hash-locked wheels, schema/example CLI and 119 passing tests |
| 3 — equivalent native fixtures | `f7ed773` | [Stage 3](../working/task_m1_3_stage3.md): 110 passing invocations and ten initial harness tests, exact original inputs |
| 4 — comparison and decision | `bd3949a` | [Stage 4](../working/task_m1_3_stage4.md): 40 Python/two Rust tests; four full passing corpora on revision 2; all 82 comparison rows; retained startup failures |
| 5 — reproduction and handoff | This bundled report commit; exact files in reproduction input map | [Stage 5](../working/task_m1_3_stage5.md): first empty-output run passes 119 contract, 60 experiment, two Rust tests and 110 native invocations; three ARM64 builds/package checks; semantic agreement |

The final reproduction SHA-256 is `a214a305dde1d3c05aed9eb4409cd7d12495c3c58d2acf83126e37830f7e291a`. It completed on the same M4 Pro/macOS 26.5.2 host with CPython 3.14.4, Xcode 26.6/SDK 26.5, Swift 6.3.3 and Rust/Cargo 1.94.1. A fresh venv was installed offline from five hash-verified cached wheels; Cargo rebuilt offline from reverified cached inputs. Installed toolchains/SDK/caches were not reconstructed. Rebuilt manager hashes differ from measured Stage 4 payloads; semantic agreement is verified, byte reproducibility is not.

### Source and downstream handoff

The completed #1 audit is merged in [PR #26](https://github.com/postmelee/pear/pull/26) and its Issue is closed, while the actual inventory remains **blocked and not source-ready**. Its manifest digest is `535cdcb7b2e76d4bc536d63ad7d17d31f562f438b7850a75a0ace1b9c88466b8`. `source_inventory_ref` is an opaque typed byte reference in this evaluator. Independent source approval must interpret the audit and future port/build evidence; a matching hash or `audit_complete` does not establish runtime readiness. No importer, fabricated ready lock or new source qualification was created.

#9 owns spawning/reaping/termination, immutable activation, scoped mutable storage and recovery. #10 owns exact-request observation readiness, process generations, sequence/gap reporting and host/module coverage. Backend synchronous replies are distinct from Pear readiness and child entry-point progress. Neither task may treat an ARM64 launcher or missing Rosetta observation as proof of complete Rosetta independence.

## Residual Risks and Follow-up Work

### Residual Risks

- A historical 1,500 ms startup failure remains unexplained. Stage 4's ordinary functional budget was explicitly revised to 5,000 ms while deliberate/scored limits remained 1,500 ms. Original failures and diagnostic uncertainty remain preserved; no startup guarantee follows.
- Python evaluates declared records and external policy; native prototypes implement only a four-record fixture subset. Real trusted producers, source approval and a full manager are unimplemented.
- Concurrent mutation/pathname execution races, cancellation, manager crashes and detached-helper ownership need production verification. Fixture observer flags cannot qualify real process/module coverage.
- Clean-output reproduction reused toolchains/caches on one Mac. It does not establish independent-Mac, minimum-OS, byte-identical payload/signature or third-party wheel source reproducibility.
- Read-only ad-hoc checks are not Developer ID signing, provisioning, notarization or ordinary-user distribution. Wine/FEX/DXMT ports and real Steam/game behavior remain unqualified.

### Follow-up Candidates

Existing issues already own the required work: [#9](https://github.com/postmelee/pear/issues/9) for the Rust manager and [#10](https://github.com/postmelee/pear/issues/10) for observation, alongside the [delivery plan](../../docs/delivery-plan.md) source/host/graphics integration gates. No duplicate Issue or new implementation stage is created by this report. Rust UI, translator replacement and broader game support are not inferred commitments.

## Approval Request to Task Requester

Approve this final report and the acceptance verification, then authorize publication of an Open PR for #3 to `master`. PR publication, merge and Issue closure have not occurred for #3. Implementation completion does not change the remaining runtime/game/distribution qualification gaps.
