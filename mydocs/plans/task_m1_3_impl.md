# Implementation Plan: Runtime contracts and manager-language evaluation

Status: the task requester approved this implementation plan and Stage 1 on September 28, 2026, then explicitly approved the Stage 1 report and Stage 2. Stages 1 and 2 are complete; actual verification and limits are recorded in ../working/task_m1_3_stage1.md and ../working/task_m1_3_stage2.md. The task requester approved the Stage 2 report and Stage 3 on September 28, 2026; Stage 3 is complete; see ../working/task_m1_3_stage3.md. The task requester approved Stage 4 on September 28, 2026; Stage 4 is complete; see ../working/task_m1_3_stage4.md. The task requester approved Stage 4 and authorized Stage 5 on September 28, 2026; Stage 5 reproduction and final handoff are complete; see ../working/task_m1_3_stage5.md and ../report/task_m1_3_report.md. The task requester approved the final report and authorized PR publication on September 28, 2026. Planned commands for unstarted stages are not passing results.

Task plan: [`task_m1_3.md`](task_m1_3.md)
GitHub Issue: [#3](https://github.com/postmelee/pear/issues/3)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Work branch: `codex/task3`

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Boundaries, identity and handoff | Proposed specification, registry and honest research example | Design/consumer review and JSON parsing; no runtime implementation |
| 2 | Seven contracts and semantic eligibility | Schemas, reference validator and adversarial fixtures | Schema checks, raw parsing, cross-record and eligibility tests |
| 3 | Equivalent native prototypes | Shared fixture plus Rust and Swift experiments | One functional corpus, ownership, privacy and architecture checks |
| 4 | Comparison and language decision | Reproducible measurements and decision | Predeclared rubric, packaging/FFI review and evidence audit |
| 5 | Reproduction and handoff | Clean-output reproduction, final specification and report | Repeat validation/prototypes; acceptance and downstream mapping |

## Document Location Check

| File | Planned Location in Task Plan | Stage Artifact Path | Match | Notes |
|---|---|---|---|---|
| Contributor specification | `docs/runtime-contracts.md` | Same | OK | Proposed in Stage 1, verified details in Stages 2–5. |
| Language decision | `docs/decisions/manager-language.md` | Same | OK | Written after equivalent experiments; records limitations. |
| Schemas and examples | `runtime/contracts/` | `runtime/contracts/contract-index.json`, `v1/`, `examples/` | OK | Neutral product contracts; no edits to #1 inventory. |
| Contract verification | `tests/contracts/` | Reference validator, dependency lock, fixtures and unittest files here | OK | Reference tooling, not a production manager API. |
| Comparison and reproduction | `experiments/manager/` | `README.md`, prototypes, fixtures, scripts and `results/` | OK | Only sanitized records are committed; binaries/raw logs remain ignored. |
| Existing public links | `docs/README.md`, `docs/architecture.md` | Same | OK | Coordinator applies narrow updates after verification. |
| Workflow records | `mydocs/plans/`, `working/`, `report/` | `task_m1_3_impl.md`, `task_m1_3_stage{N}.md`, `task_m1_3_report.md` | OK | Stage approval and Issue evidence remain separate from specifications. |

No manual, project license, runtime source, #2 evidence, or actual `runtime/sources/manifest.json` changes are planned. Local outputs use `.build/task3/`; preserve existing ignore rules unless an approved path requires a narrow addition.

## Shared Decisions and Dependency Setup

- #1 owns its versioned factual audit inventory and source decision. Agree logical fields: component ID/role/dependencies; source URL, immutable ref and digest scope; ordered patches/base/provenance; toolchain/SDK/host and guest targets; license/notice/contribution references; inspection date, scope, evidence and status. #3 owns their product-contract representation. Neither task waits for the other's completed implementation.
- Use JSON Schema Draft 2020-12 for structural contracts; a Python reference validator supplies bounded parsing and cross-record/eligibility rules. All schema references resolve from the checked-in registry; validation must not fetch URLs. Define supported schema versions and reject unknown mandatory semantics or fields rather than silently dropping them.
- Record digests are SHA-256 of exact stored UTF-8 file bytes, referenced by another record. Binary/source digests identify their actual byte/tree representation separately. No embedded self-digest or circular identity chain; whitespace edits intentionally change a byte digest. Authenticity, matching bytes, semantic compatibility and qualification remain separate checks.
- Distinguish research, fixture and runtime context. Incomplete research records may be structurally valid but cannot authorize launch or qualification. Self-owned fixture inputs use actual computed hashes and never masquerade as upstream revisions. A fixture-context success cannot become a supported game record.
- Current Python lacks JSON Schema packages. In Stage 2, inspect official package metadata and licensing, choose exact `jsonschema` and required transitive releases, and record versions, source URLs and actual wheel hashes in `tests/contracts/requirements.lock` and `dependencies.json` before use. Use binary wheels, a task-local venv and `--require-hashes`; no global installs, floating versions, unnecessary pytest, or package build scripts. If an appropriate pinned dependency cannot be obtained, report that specific setup gap.
- In Stage 3, pin Rust dependencies by exact manifest versions and `Cargo.lock`; retain checksums and a dependency/license inventory. Start Swift with Foundation/Darwin only. If additional parsing support is needed, select and verify an exact release/revision with its lock before use and include its cost in the comparison. Do not claim Foundation decoding detects duplicate keys without a raw-input test. Fetch locked dependencies before controlled builds, then verify with offline/locked modes where supported.
- Record observed Python, compiler, SDK, Rust and Swift versions; the current installed versions are comparison inputs, not Pear release pins. No new restricted capability calls or development-profile tests are needed. #2's committed results remain unchanged references.

## Stage 1 — Boundaries, Identity and Handoff

### Artifacts

- `docs/runtime-contracts.md` — proposed field/ownership matrix, status transitions, digest/version rules, source handoff and execution/observation boundaries.
- `runtime/contracts/contract-index.json` — seven record kinds, version 1, planned schema paths and explicit draft status; no schema availability or support claim.
- `runtime/contracts/examples/research-lock.json` — incomplete, non-launchable research example with explicit missing observations and no fabricated upstream hashes.

### Changes

- Define `runtime_lock`, `runtime_artifact`, `game_profile`, `launch`, `failure`, `run`, and `qualification`; enumerate each producer/consumer, required identity links and unsupported/unknown states. Keep source availability, built/tested state, execution eligibility, and supported scope distinct.
- Document the acyclic links: lock/profile identity precedes artifact and launch; run references its actual inputs; qualification references completed evidence. Mutable local state and raw logs are never part of immutable runtime content.
- Fix bounded profile operations, host-relative versus guest path rules, explicit argument/environment handling, prefix/cache ownership and evidence-redaction fields. The future #9 supervisor owns spawning/reaping/termination and writes; #10 owns observations only.
- Specify run identity, PID plus creation/generation identity, observer-ready acknowledgement before covered execution, monotonic event sequence, missing/dropped event reporting and incomplete shutdown. These are interface designs, not an implemented collector or launcher.
- Cross-review the field mapping with #1 through its Issue link. Its audit `go`/`needs-port`/`blocked` state cannot be treated as a built or qualified runtime. Record unresolved facts without making #3 completion depend on its inventory.

### Verification

```bash
python3 -m json.tool runtime/contracts/contract-index.json > /dev/null
python3 -m json.tool runtime/contracts/examples/research-lock.json > /dev/null
git diff --check
```

Review all seven kinds against the architecture and Issue criteria, inspect the handoff with #1, check relative links, and trace an incomplete research record through a documented rejection of launch and support. JSON parsing here does not claim schema or semantic validation. No prototype, build, dependency installation, or runtime execution occurs in this stage.

### Commit

`Task #3 Stage 1: define contract boundaries and source handoff`

## Stage 2 — Seven Contracts and Semantic Eligibility

### Artifacts

- `runtime/contracts/v1/common.schema.json`, `runtime-lock.schema.json`, `runtime-artifact.schema.json`, `game-profile.schema.json`, `launch.schema.json`, `failure.schema.json`, `run.schema.json`, `qualification.schema.json`.
- `runtime/contracts/examples/` — clearly labeled research records and fixture bundles; update the registry/specification from proposed structure to tested version 1 behavior.
- `tests/contracts/validate.py`, `requirements.lock`, `dependencies.json`, `fixtures/`, `test_structure.py`, `test_eligibility.py`, and `test_paths_and_privacy.py`.

### Changes

- Common definitions cover typed component/source/patch/toolchain/target identities, evidence references, outcomes, host/distribution scope and allowed extensions. Seven schemas define record-specific structure; launch uses explicit request/event variants within its record kind.
- The reference CLI accepts an input bundle and requested context/purpose, returning separate structural validity and eligibility with stable bounded reasons. Implement `--check-schemas` and `--check-examples`; do not infer trusted provenance from a correctly shaped digest or a self-asserted status.
- Parse raw bounded UTF-8 JSON with duplicate-key, malformed encoding, non-finite numeric, unexpected-type and nesting/size checks before schema validation. Specify limits in the contract and test their boundaries. Reject remote schema references and unsupported versions.
- Resolve an explicit local bundle, verify actual file bytes, enforce compatible IDs/families/targets and acyclic links, and prevent a research/fixture record from satisfying runtime qualification. Successful fixtures use hashes generated from owned fixture content, with expectations independent from the code being tested.
- Qualification requires matching final input identities, required passing checks and complete declared observation scope; unknown/failed/unsupported required paths cannot pass. Model developer execution separately from ordinary-user distribution and retain evidence age/configuration limits without manufacturing support.
- Test host traversal, unexpected absolute paths, symlink escapes, guest-path misinterpretation, arbitrary profile commands, immutable writes, incompatible prefix/cache identity, environment leakage and synthetic secret markers. Use temporary owned directories; do not mutate user prefixes. Runtime time-of-use enforcement remains #9's obligation.

### Verification

After the exact dependency lock is reviewed, use the planned setup and checks:

```bash
python3 -m venv .build/task3/venv
.build/task3/venv/bin/python -m pip download --only-binary=:all: --require-hashes --no-deps -r tests/contracts/requirements.lock --dest .build/task3/wheels
.build/task3/venv/bin/python -m pip install --no-index --find-links .build/task3/wheels --require-hashes --no-deps -r tests/contracts/requirements.lock
.build/task3/venv/bin/python tests/contracts/validate.py --check-schemas --check-examples
.build/task3/venv/bin/python -m unittest discover -s tests/contracts -p 'test_*.py'
git diff --check
```

Required negatives include duplicate keys from raw bytes, valid-schema/wrong-digest bundles, reused IDs with incompatible content, unknown required identity, false supported status, signature-versus-payload confusion, cycles, missing helpers/events, wrong host/guest architecture, and fixture-to-runtime promotion. Valid incomplete research must be accepted as research and rejected for execution. None of these tests launches a runtime.

### Commit

`Task #3 Stage 2: validate versioned contracts and eligibility`

## Stage 3 — Equivalent Rust and Swift Experiments

### Artifacts

- `experiments/manager/README.md`, `comparison-plan.json`, `dependencies.json`, `fixtures/child.c`, `fixtures/native_bridge.h`, `fixtures/native_bridge.c`, and `fixtures/cases.json`.
- `experiments/manager/rust/Cargo.toml`, `Cargo.lock`, `src/main.rs`, and supporting modules; `swift/Package.swift`, `Sources/` and a resolved dependency lock only if packages are required.
- `experiments/manager/build.py`, `run_cases.py`, and `test_prototypes.py`; local outputs under `.build/task3/prototypes/`.

### Changes

- Build one C fixture with deterministic success, nonzero, signal, delayed, excess-output and descendant-held-pipe modes. A small C ABI bridge reports process creation identity/error codes only; it does not implement supervision on behalf of either candidate. Document integer/layout/lifetime ownership and no unwinding across the boundary.
- Each native prototype reads the same bounded fixture bundle, verifies actual referenced identities/versions/paths and allowed operations, launches only the declared fixture under an owned root, uses argument arrays and scoped environment, and emits the same bounded structured result. Reject raw duplicate keys in both before information is lost; test malformed and unsupported inputs identically.
- Implement equivalent deadlines, stdout/stderr bounds, nonzero/signal classification and owned-process cleanup. Keep process identity and group ownership safe across exit/PID reuse; preserve honest cleanup errors. Missing observer readiness and fixture event gaps produce explicit outcomes without claiming complete host observation.
- Use the Python validator only as the independent test oracle, not an unreported subprocess that performs a candidate's validation or launch work. Full schema generality is unnecessary in this bounded experiment, but the supported subset and matching rejection semantics must be declared identically.
- Add argument/Unicode/space preservation, inherited-environment rejection, empty/closed standard input, timeouts, malformed child output, descendant pipe retention, spawn failure, symlink escape, synthetic log-secret and unrelated-sentinel survival cases. Each prototype owns only its temporary fixture subtree; no Steam, Wine or user prefix is used.
- Freeze functional gates, build settings, run order, measurements and qualitative rubric in `comparison-plan.json` before Stage 4. Inspect actual native slices and dependencies; any missing required functional or privacy behavior blocks comparative adoption claims.

### Verification

```bash
python3 experiments/manager/build.py --output .build/task3/prototypes --locked
python3 experiments/manager/run_cases.py --build-root .build/task3/prototypes --all --oracle .build/task3/venv/bin/python
python3 -m unittest discover -s experiments/manager -p 'test_*.py'
git diff --check
```

The build script records actual commands/toolchains, verifies dependency locks and checks Mach-O ARM64 slices with `file`/`lipo`; package inspection uses `otool -L`. Case results must match the common expected classifications and show bounded completion, reaped owned children and survival of an unrelated sentinel. Fixture-mode results explicitly remain ineligible for runtime/game qualification.

### Commit

`Task #3 Stage 3: compare equivalent native manager fixtures`

## Stage 4 — Comparison and Manager-Language Decision

### Artifacts

- `experiments/manager/compare.py`, reviewed `results/comparison.json`, and updated reproduction instructions.
- `docs/decisions/manager-language.md`; evidence references linked to the unchanged, predeclared rubric in `comparison-plan.json`.

### Changes

| Criterion | Rule and evidence |
|---|---|
| Functional correctness and privacy | Mandatory: identical corpus expectations, raw-input validation, bounded lifecycle, owned cleanup and no secrets. A failure prevents selecting that candidate until fixed and rerun. |
| Packaging and macOS integration | Inspect native slices, runtime dependencies, bundle/signing requirements and clean invocation. Optional local signing checks use a disposable fixture only and record actual authorization; inspection alone is not executed-signature or distribution evidence. |
| FFI and testing | Compare necessary unsafe/native surface, ownership/error mapping, debug/reproduction steps and failures that require custom bridging. A shared C child does not substitute for native manager behavior. |
| Maintenance and contributors | Record build prerequisites, direct/transitive dependencies and licenses, code organization, diagnostic clarity and documented contribution steps. Explain judgments; line counts are context, not an automatic score. |
| Measured prototype costs | Three clean-output builds after dependency prefetch, three incremental builds after equivalent predetermined behavior-preserving edits in each native manager's own source module, and 30 fresh process launches per candidate in alternating order after five unscored warmups. Freeze the exact Rust and Swift edits in the comparison plan. A shared C-child rebuild is not a native-manager incremental-build measurement. Report samples, median and range, dependency/payload sizes and available peak memory; do not invent missing metrics or tail distributions. |

- Use equivalent optimized release builds, the same host/power condition and corpus; reserve the Mac from concurrent heavy jobs. Incremental edits occur in isolated copies, and each result records the actual source/configuration identity. Clean outputs do not mean cold OS caches. Record cache-control limitations and failed/interrupted runs; never discard valid unfavorable results. Do not measure power or game performance in this task.
- The decision first applies the mandatory gates, then weighs packaging, FFI, testability and maintenance evidence. Measurements inform actual manager costs without a predetermined speed target or game-FPS inference. State the chosen language, reasons, limitations, alternative and reconsideration triggers; leave a material untested requirement unresolved.
- Define the #9 implementation handoff and #10 observer interface obligations. Do not promote a prototype into `manager/` or implement a full collector as part of the decision.

### Verification

```bash
python3 experiments/manager/compare.py --plan experiments/manager/comparison-plan.json --build-root .build/task3/prototypes --output .build/task3/comparison-raw.json
python3 experiments/manager/compare.py --check-report experiments/manager/results/comparison.json
python3 experiments/manager/run_cases.py --build-root .build/task3/prototypes --all --oracle .build/task3/venv/bin/python
git diff --check
```

Review and redact raw results before committing the public record. Verify sample accounting, equivalent settings, functional gate results, measured-versus-inspected packaging claims, unknown fields, dependency provenance and decision traceability. Any fixes affecting measured behavior require rerunning the affected corpus and comparison.

### Commit

`Task #3 Stage 4: record evidence-based manager language decision`

## Stage 5 — Reproduction and Contract Handoff

### Artifacts and Changes

- `experiments/manager/reproduce.py` and sanitized `results/reproduction.json`; finalize `docs/runtime-contracts.md`, the manager decision and experiment README.
- Use a new empty task-local output directory to recreate the validator environment from hashed wheels, rebuild locked native prototypes and rerun all contract/parity checks. Existing outputs and #2 evidence remain untouched. Verify offline dependency reconstruction where available; identify any required network acquisition precisely.
- The coordinator adds narrow links in `docs/README.md` and `docs/architecture.md`, writes `mydocs/report/task_m1_3_report.md`, and maps all Issue criteria to exact source/test revisions and results. A same-Mac clean-output reproduction is not independent-host or game qualification.
- Cross-review the logical #1 handoff and the #9/#10 ownership/readiness contract. If actual #1 inventory is available, a read-only mapping check may expose gaps; its absence does not block #3's schema/fixture acceptance and no actual runtime pin is invented.

### Verification

```bash
python3 experiments/manager/reproduce.py --output .build/task3/reproduction --require-empty
python3 experiments/manager/reproduce.py --check-report experiments/manager/results/reproduction.json
git diff --check
git status --short
```

Require matching semantic outcomes, passing rejection cases and explained payload nondeterminism; byte-identical signatures are not a criterion. Check documentation links, synthetic-versus-real evidence labels, privacy, retained unknowns, and the decision's complete Issue acceptance mapping. No production launch or support status follows from these checks.

### Commit

`Task #3 Stage 5 + final report: reproduce contracts and manager decision`

## Verification, Commits and Stage Dependencies

- Each Stage commit includes `mydocs/working/task_m1_3_stage{N}.md` and its verified artifacts; reports record actual commands, outcomes, source/tool identities and limits. The coordinator owns shared boards/docs and commits. Final publication follows the repository's final-report procedure.
- Stage 1 starts only after approval of this implementation plan and its scope. Each later stage starts after the previous verification/report and task requester approval. Failures are repaired within the approved stage or explicitly reported; failed required checks do not count as completion.
- Stage 2 depends on reviewed Stage 1 identity/ownership decisions and verified test dependencies. Stage 3 depends on the common validator/corpus; Stage 4 depends on functional parity and a frozen rubric; Stage 5 repeats the final implementation. #1 completion is not a hidden prerequisite.
- No unplanned schema/location/scope expansion is folded in silently. Update the relevant plan and obtain approval when the approved contract or document-location decision must change. Do not create `manager/`, alter upstream runtime source or repeat restricted #2 probes here.

## Risks and Responses

- **Schema versus eligibility drift:** use separate structural and semantic results plus incomplete/mismatched/adversarial fixtures; a digest or `supported` label cannot replace evidence.
- **Parser differences:** exercise duplicate keys and malformed raw bytes before native decoding loses information; required parity cannot be waived for a convenient parser.
- **Dependency or packaging gap:** verify exact versions/hashes before use, disclose added libraries and unavailable checks, and avoid uncontrolled latest installs or global changes.
- **Unequal comparison or shared Mac interference:** freeze inputs/rubric, isolate output/prefix paths and coordinate controlled measurements; retain failures and explain cache limits.
- **Prototype scope creep/privacy:** shared fixtures and observation events are not production Steam lifecycle or module coverage. Keep raw paths/logs local, review public records, and preserve #2's evidence unchanged.

## Approval Request

- Approve these five stages, concrete artifact paths, dependency-pinning procedure, verification commands, comparison rubric and stage commit messages.
- Authorize Stage 1's bounded design/specification, registry and research-example work only; later stages retain their approval checkpoints.
- Retain the approved exclusions and ownership split: no production manager/GUI, actual game/Steam work, translator replacement, new restricted execution, or runtime/distribution qualification.

## Approval Record

The task requester approved both #1 and #3 implementation plans and authorized parallel Stage 1 execution on September 28, 2026. That initial approval preserved the task-plan scope and document locations and authorized Stage 1 only. The subsequent Stage 2 approval is recorded below.

### Stage 2 Authorization

The task requester explicitly instructed both tasks to proceed after reviewing the Stage 1 completion request on September 28, 2026. This authorizes Stage 2 within the approved scope and document locations. Stage 3 remains subject to its report approval checkpoint.

### Stage 2 Completion

Stage 2 implementation, independent review and planned verification are complete. The bundled stage report records actual results and remaining limitations. At that checkpoint, Stage 3 had not started; its subsequent authorization is recorded below.

### Stage 3 Authorization

After the combined Stage 2 reports and Stage 3 approval request, the task requester replied with an explicit instruction to proceed in the same main thread on September 28, 2026. This authorizes Stage 3 implementation, dependency setup where planned, fixture execution, verification and bundled stage reports within both approved plans. Stage 4 remains subject to a separate report approval checkpoint.

### Stage 3 Completion

Stage 3 implementation, independent review and all planned verification are complete: 55 common cases passed for both candidates, alongside ten harness regression tests. Native fixture results remain ineligible for runtime qualification. The bundled report records actual evidence and limitations. At that checkpoint, Stage 4 had not started; its subsequent authorization is recorded below.

### Stage 4 Authorization

After the combined Stage 3 reports and explicit Stage 4 approval request, the task requester instructed both tasks to proceed in the same main thread on September 28, 2026. This authorizes the approved Stage 4 source reacquisition/final audit and controlled manager comparison/decision. The frozen comparison plan remains unchanged. Source acquisition and heavy verification must finish before controlled manager measurements. Later stages and publication retain their documented approval checkpoints.


### Stage 4 Corrective Input Revision

The original 300 ms deliberate-timeout fixtures intermittently failed their required child-observation checks in both candidates. Attempt 1 stopped at its before-gate with no timed samples. Attempt 2 passed the before-gate and all 82 planned samples, then failed the after-gate. All source snapshots, raw samples and failures are retained; neither attempt authorizes a language selection. Four unchanged targeted descendant tests passed, with late trace creation, but no specific OS/security cause was proven.

The approved Stage 4 procedure explicitly permits correctness fixes followed by affected corpus and comparison reruns. Apply a narrow fixture correction before any further comparison: use the existing ordinary-case 1,500 ms limit for the two deliberate-timeout cases, and extend the delay fixture from 1,000 to 5,000 ms so it still must be terminated. The descendant remains a pipe-holding child with a 10-second bounded lifetime. Preserve all required child/descendant traces, identity disappearance, direct-child reaping, unrelated sentinel, privacy and bounded-cleanup assertions. No manager deadline implementation or public CLI changes are introduced by this correction.

Record both old and new corpus/fixture identities, rebuild the native fixture, verify the two affected cases, and rerun the entire comparison with new isolated outputs. The unchanged `comparison-plan.json` still controls release settings, three clean/three incremental builds, five warmups/30 launches, exact order, 1,500 ms measured-success timeout and qualitative rubric. The correction changes functional fixture input bytes; it is not represented as a byte-identical repeat of Stage 3 or the two failed attempts. Retain all measurements, including unfavorable values and failed attempts, and make no adoption claim until both complete functional gates pass. New artifact paths remain within the already approved experiment/results and workflow locations.


### Stage 4 Functional Budget Separation

The first corrected-input comparison completed all 82 samples and both 110-invocation gates, but its separately required final baseline corpus failed Rust `observer_gap`: timeout at 1,500 ms, SIGKILL, no output/child trace, successful direct-child reaping/cleanup and a live unrelated sentinel. Preserve that failed final corpus and the completed historical comparison as different evidence. A predefined 16-invocation diagnostic did not reproduce the failure. One sampled slow successful invocation was in dyld's pre-main notification path; sampling may perturb it, and this does not establish the prior failure's cause or identify any monitor.

Use the approved correctness-fix/rerun procedure to separate ordinary functional conformance from scored launch timing. Both existing manager CLIs already accept 100–5,000 ms. Ordinary/non-timeout functional cases will use 5,000 ms; the deliberate timeout and descendant-pipe cases retain 1,500 ms, the deliberate delay remains 5,000 ms, cleanup remains bounded at two seconds, and the outer harness retains ten seconds. No native manager or fixture executable code change is needed for this revision. All trace, native execution, cleanup, privacy and sentinel expectations remain mandatory. A passing result proves conformance under these declared limits, not guaranteed startup within the earlier 1,500 ms budget.

The frozen comparison plan and scored successful-launch timeout remain unchanged at 1,500 ms, with the original release settings, order and sample counts. Bind old/new functional corpus hashes and every prior comparison/final-corpus/diagnostic record in a second input-revision record. Archive the previously completed result before replacing the public latest result; retain all 82 historical samples and failed observations. Verify current native build identity, run the complete baseline corpus, then one full controlled comparison and the required final baseline corpus. Any failure prevents adoption and stage completion; no failed sample is waived or replaced. This remains a fixture-parameter correction within the existing CLI and approved experiment scope, not a new supervisor handshake or a change to runtime contracts.


### Stage 4 Completion

The second corrective input revision passed all planned checks: four full 110-invocation corpus runs, all 82 samples, 40 Python tests and report validation. Two owned Rust fault tests pass on the unchanged native/C fixture sources. Rust is selected for the new manager within the recorded fixture limits; all earlier failures and measurements remain preserved, with no claim that the earlier startup issue was fixed. The bundled Stage 4 report and decision record measured costs, limitations and #9/#10 obligations. Stage 5 has not started and requires the next report approval.


### Stage 5 Authorization

After the Stage 4 report and combined request to merge PR #26 and proceed with Stage 5, the task requester explicitly instructed this thread to proceed on September 28, 2026. This authorizes clean-output reproduction, final contract/source handoff review, the already approved documentation locations and the bundled Stage 5/final report. PR #26 is merged at `3ad083075ba46522d4d01764e2ba453a89a1436d`; Issue #1 is closed while its source-readiness decision remains blocked. Final-report approval is still required before #3 PR publication.


### Stage 5 Completion

The first empty-output reproduction completed successfully: schema/example checks, 119 contract tests, 60 experiment tests, two Rust fault tests, three ARM64 builds with read-only package/signature inspection, and 110 common native invocations with matching semantic outcomes. The five cached wheels were reverified and installed into a new venv; locked/offline Cargo reused the reverified source cache and installed toolchains. No dependency download or timing rerun was requested. All prior native inputs, comparison results and failed observations remain unchanged. The final reports record byte differences, one-Mac scope, the reviewed blocked #1 handoff and #9/#10 production obligations. PR publication remains subject to final-report approval.


### Final Report and Publication Authorization

After reviewing the completed Stage 5/final report and concrete PR body draft, the task requester explicitly instructed this thread to proceed on September 28, 2026. This approves the final report and publication of an Open PR for #3 to `master`. It does not authorize merging the PR or starting a new production implementation task. The checked reproduction inputs and observations remain unchanged.
