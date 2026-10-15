# Task #56 implementation plan

Task plan: [task_m1_56.md](task_m1_56.md)
GitHub Issue: [#56](https://github.com/postmelee/pear/issues/56)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

The requester approved continuous progression within the task plan, with verification, reports and commits retained. Private repository creation and necessary owner coordination are separately approved. Additional deletion, public visibility, scope expansion and original environment/Preview changes remain excluded.

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Reconcile source/input authority | Sanitized investigation, exact checkpoint, recovered producer, owner/retention decisions | Current identities, recovery digest, provenance/private exclusions and operation-specific space plan |
| 2 | Import component histories | Private Wine/FEX/DXMT repositories and runtime skeleton | Upstream ancestry, exact selected sources/modes and attribution, single providers |
| 3 | Reconstruct the development candidate | Portable recipes, fixed lock, immutable input manifest, build/assembly receipts | New isolated compilation/link/assembly, input rejection and output comparisons |
| 4 | Verify affected behavior | Required fixture/ABI/graphics and recovery records | Existing required controls on exact candidate; limits explicit |
| 5 | Connect developer entrypoints | Pear development adapter, component/runtime READMEs and links | Selection/diagnostic/recovery behavior, unchanged Preview/default state |
| 6 | Accept authority and hand off | Source cutover, final lock, failure/next-work/retention handoff, report/PR | Cross-repository identities, owner acceptance, links and preserved environment |

## Document Location Check

Component root READMEs and runtime `docs/development.md` own reusable source/build instructions. Pear updates its existing `docs/development/rosetta-free.md` and related architecture/contracts/index links. The dated investigation is `mydocs/tech/20261015_runtime_repository_split.md`; plans/reports/orders stay in their existing workflow directories. These match the requester-approved location judgment in the task plan. Personal path maps, source-edit history metadata, raw evidence and private generation inputs remain outside Git.

## Stage 1 - Reconcile source/input authority

### Artifacts

- This implementation plan and updated dated investigation with sanitized source/input tables.
- Task-owned local identity index for the original investigation, current source comparison and recovered D25 helper.
- Existing-owner responses: exact export checkpoint, newer changes, remaining tests and retention holds. Pending owner acceptance cannot be reported as cutover.
- Per-operation storage estimates; exact optional cleanup proposal, never an expansion of earlier authorization.

### Changes

Supersede the prior scratch-only proposal without rewriting historical evidence. Preserve 53 Wine patches/58 changed units, 83 FEX units, 17 generic diagnostics, private selector exclusion and five DXMT patches as selected candidates, subject to owner reconciliation. Record the unchanged wire ABI and common diagnostic schema ownership. Preserve the exact recovered original D25 file and separately identify the path/coordination adaptation to be implemented later.

Read current owner source and new Preview baseline. The original game failure, source hypotheses and future debug ownership remain explicit. No original source/runtime mutation or game execution occurs here.

### Verification

- Rehash selected source/producers/patch inputs against the captured manifests; inspect owner differences before importing.
- Hash recovered original `phase_build.py`: `3e83e11f7806b639d091052e140a103c2d3dd0eda6187cacc9117f9aae8ab84c`, 9,057 bytes. Parse the Python source without executing it.
- Check source pin/tree, file licenses, notices and private input classification against local pinned upstreams and recorded ancestry.
- Validate sanitized committed records with JSON parsing and scan added text for personal absolute paths, private selectors and game payloads.
- Record source checkout/history size, measured free space and named output roots before acquisition. No substantial build authorized by a source-size estimate alone.
- `git diff --check`.

Retain local verifier outputs and document exactly which checks are hash-based versus stat-only. The source audit's replay proof may be reused for unchanged input identities; it does not prove any newly built payload.

### Commit

`Task #56 Stage 1: reconcile source checkpoint and reconstruction inputs`

## Stage 2 - Import component histories

### Artifacts

- Private `postmelee/pear-wine`, `pear-fex`, `pear-dxmt`, `pear-runtime` repositories and isolated local checkouts.
- Imported upstream ancestry at the pinned revisions; selected accepted and candidate commits with source/patch provenance mapping.
- Component-owned generic source/tests, runtime-owned build/contract/shared diagnostic schema and exact header exports.
- Baseline READMEs/notices and source manifest referring to actual commit identities.

### Changes

Fetch ancestry into new repositories; never change original bare caches. A shallow pinned snapshot alone is insufficient to claim complete upstream history. Preserve upstream commits without rewriting authorship. Downstream imports record originating Pear commits/patch hashes and source authorship; generated checkpoints are explicitly labeled. Keep historical legacy patches frozen as provenance, not a second editable implementation authority.

Separate the game-derived selector from generic FEX source. Import exact generic source first; use a declared private input to reproduce the original diagnostic configuration, and a separately identified synthetic input for redistributable tests. Keep runtime contract schemas/validators together rather than fragmenting relative references. Preserve the Preview manager dependency; no crate move that breaks it.

### Verification

- `git merge-base --is-ancestor <pinned-upstream> HEAD` and inspect repository shallowness/ancestry.
- Compare imported selected file SHA-256, executable modes and symlinks to the approved export; examine every intentional README/provenance/shared-input addition separately.
- Validate provenance mapping, SPDX/notices and shared provider/consumer digest equality.
- Run applicable source/contract tests without private input, then confirm private inputs cannot enter tracked files.
- Verify private remote metadata; no public visibility change. Check pushed refs against local commits. If the initial full-history upload remains active after local source verification, record it explicitly as pending and allow independent recipe implementation; remote identity verification remains mandatory before the final runtime lock/handoff. This scheduling change does not treat an unverified remote ref as available or authorize heavy operations beyond their storage plan.
- `git diff --check` for new metadata and adapted code in each changed repository. Preserve exact imported source bytes: any pre-existing whitespace warning must be enumerated, matched to the frozen selected checkpoint and reported separately; do not normalize source silently or suppress unrelated warnings.

### Commit

`Task #56 Stage 2: import selected component source histories`

Each participating repository may need source/import commits; the Pear stage report binds their exact hashes. Source authority stays with the prior owner until the final explicit accepted cutover.

## Stage 3 - Reconstruct the development candidate

### Artifacts

- Runtime component commit lock and immutable input/configuration manifest.
- Portable builder/assembler under `pear-runtime`, explicit local input binding file outside Git, isolated build logs and receipts.
- Reconstructed native Wine/PE overlay, FEX module and graphics combination; an isolated development candidate bundle.

### Changes

Implement source acquisition/generation/compilation/assembly from fixed commits and identified inputs. Reuse exact original D25 logic/recorded argv where valid; replace only reviewed path and coordination bindings. Never overwrite the historical producer or silently select the newer helper. Preserve original command/environment and new command correspondence.

The bounded first candidate may consume declared immutable lower-layer objects, archives, generated config and toolchains. Each input must have content identity, source/recipe provenance, role, recovery instructions and a named binding. No hidden absolute worktree fallback is allowed. Rebuild the changed current source units from new fork paths, and diagnose missing implicit SDK/linker/header dependencies instead of assuming operand presence closes them.

Generate new build records; compare `.text`/unsigned payloads or explain differences from timestamps/debug paths. Preserve PE ARM64EC/CHPE semantics rather than asserting the outer PE machine field alone. Build outputs and mutable fixtures use new task-owned roots. A separate bundle is justified only for safely replacing/re-signing candidate payloads without touching the original.

### Verification

- Calculate exact input staging + new objects + links + logs + bundle + test overlap before each heavy command; check actual free space and shared heavy-operation lock.
- Validate lock commits and all bound inputs before starting; reject missing/mismatched source/private/generated/toolchain inputs.
- Execute documented portable build commands from new source checkouts and store argv/cwd/environment/tool/hash evidence.
- Audit actual dependency files and implicit libraries; every consumed file must resolve through declared source/toolchain/config/input roots.
- Verify output architecture/sections, selected shared ABI and original/new payload comparison.
- Rehash protected original selections/critical records after building; no old receipt overwrite.

### Commit

`Task #56 Stage 3: reconstruct a pinned development runtime`

## Stage 4 - Verify affected behavior

### Artifacts

- Exact candidate verification matrix and results, portable tests, artifact differences and recovery checks.
- Required test ownership map referencing component tests and runtime integration fixtures.

### Changes

Reuse original fixture and verifier implementation. Run the existing seven D36 synthetic fixture categories and affected Wine/FEX ABI/graphics controls selected by the source owners. Native execution requires valid artifact-specific host authorization and isolation. Read the Pear Apple-tooling skill and relevant pinned guidance before actual affected Metal validation. Avoid replaying unrelated full suites solely because paths moved; do not waive checks whose source/configuration/artifact changed.

Record reused historical evidence with its unchanged inputs/claim scope. Distinguish portable tests, source/build checks, actual host fixture execution, private diagnostic readiness and unperformed game/player qualification. Verify recovery of new local bindings/candidate state without mutating original state.

### Verification

- Execute the exact source-owner required commands recorded in the runtime lock/verification manifest; no invented passing status.
- Required positive/negative ABI, mismatch, lifecycle/refusal, TLS/thread, unwind, code invalidation and affected graphics checks retain their original assertions.
- Validate candidate fixture outputs against the exact rebuilt artifact and signatures; fixture success is not gameplay or full no-Rosetta coverage.
- Verify rebuild/rebind and recovery commands on isolated output roots within measured capacity.
- `git diff --check` and relevant portable test suites.

### Commit

`Task #56 Stage 4: verify reconstructed candidate controls`

## Stage 5 - Connect developer entrypoints

### Artifacts

- Narrow Pear development candidate adapter/configuration and tests, using runtime-owned build/diagnostic entrypoints.
- Each component README and runtime/Pear developer, source-pin, status and recovery links.

### Changes

Use an explicit development/qualification purpose and a task-owned state root. Preserve supported Preview selection/resources and authenticated prefixes/saves. Resolve exact compatible runtime lock/artifact and record selected components before diagnosis. Reuse the existing supervisor/observer seam rather than introducing another game runner; integrate the existing original-game diagnostics with private inputs only when the selected development path permits them.

A documented command must prepare/select/inspect a candidate and provide the exact next diagnostic procedure. The task need not solve or qualify Megabonk. A refusal/unsupported path must remain a refusal, not a fabricated real-runtime success.

### Verification

- Portable tests for candidate lock mismatch, missing input, purpose mismatch, isolation and unchanged default/Preview state.
- Real selected-candidate inspection and approved fixture diagnostic path with exact identities, not only mock records.
- Existing relevant manager/contract tests and source-owner observation checks.
- All READMEs contain role, upstream pin, build/verification commands, dependencies, licenses, support limits and actual related repository links.
- Check Markdown link targets and documented commands; private links are marked as requiring collaborator access.

### Commit

`Task #56 Stage 5: connect isolated native development entrypoints`

## Stage 6 - Accept authority and hand off

### Artifacts

- Accepted source ownership/cutover record with exact fork commits and frozen legacy provenance.
- Final runtime lock, instructions and next #11/#12 implementation/debugging task handoff.
- Final report/retention record and reviewable Pear PR after required checks.

### Changes

Reconcile owner changes one last time. Record the component fork as the only editable implementation authority for the accepted range, and point future changes/tests to their correct repository. Keep source cutover separate from active runtime activation. Preserve rollback/recovery instructions for the previous source and exact private candidate state.

Record the current Megabonk failure, competing hypotheses and evidence limits, exact reproduction inputs/commands, next code locations and required regressions. Do not claim this task solved the game or completed #13/player distribution. Reconcile every new retained artifact and any separately authorized deletion receipt.

### Verification

- Compare final local/remote commit identities and lock references, README status and all dependency links.
- Obtain exact source-owner acceptance of the cutover; merely sending a request is insufficient.
- Verify documented source acquisition/build/selection/diagnostic/recovery entrypoints match exercised commands and available inputs.
- Confirm #47 resources and original execution/private state were not changed by #56.
- Task trees clean before PR publication; `git diff --check`; staged privacy scan and retained evidence index valid.

### Commit

`Task #56 Stage 6 + final report: hand off split runtime development`

## Stage Dependencies and Risks

Stages retain verification/report/commit gates, with continuous user authorization. Parallel read-only work is allowed. Source import does not imply authority cutover; remote creation remains private. A failed required check keeps its stage open while corrective work remains within approved scope. Capacity or missing inputs must be resolved before dependent heavy work, while independent work continues. Any broader implementation or required existing-environment change is brought back as a concrete scope decision.
