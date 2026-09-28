# Task Plan: Qualify source availability and pin the runtime toolchain

GitHub Issue: [#1](https://github.com/postmelee/pear/issues/1)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

Status: the maintainer approved this task plan, scope and document locations on September 28, 2026, together with Issue #3. Detailed implementation planning is authorized. Stage implementation remains subject to the implementation-plan approval checkpoint; no renewed upstream audit, source acquisition or runtime build is claimed by this record.

## Purpose

Establish an evidence-backed inventory of the source, existing patches, dependencies and toolchain inputs needed for Pear's proposed ARM64 Wine/FEX/DXMT runtime. Identify which inputs are available and attributable, which macOS behavior still needs implementation, and which required inputs remain unavailable. Deliver immutable source identities, measured hashes, a bounded inventory validator, a contributor guide and an explicit source-feasibility decision.

This supplies the source contribution to the architecture's G0 gate and concrete inputs for later implementation tasks. It does not qualify a built runtime, Rosetta-free game execution or general-user distribution. A complete investigation can produce a negative decision; completing its report must never turn an unavailable runtime prerequisite into a pass.

## Background

The [runtime architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md), [macOS runtime audit](../../docs/research/macos-runtime-audit.md) and [graphics audit](../../docs/research/graphics-and-game-integration.md) describe the intended component boundaries. The September 27 audits inspected selected Wine/FEX files and DXMT build infrastructure. Their recorded commits, branch links, release names and tool versions are historical evidence, not newly verified or adopted pins. The macOS audit specifically left the relevant CrossOver source archive unaudited and did not establish that a public release contained all ARM64 Preview changes.

[Issue #2](https://github.com/postmelee/pear/issues/2) is complete. Its [final report](../report/task_m1_2_report.md) records reproduced, authorized native host trials on M4 Pro/macOS 26.5.2 under normal protections. Those finite memory, JIT, ABI and thread results establish a host baseline; they do not establish that Wine, FEX or DXMT contains the integration Pear needs. The recorded Apple clang/SDK versions are useful comparison inputs, not automatic pins for all upstream builds.

Issue #1 has no acceptance dependencies. [Issue #3](https://github.com/postmelee/pear/issues/3) runs independently and owns the runtime-lock, game-profile, launch, failure and qualification contracts plus manager-language evaluation. Source qualification must supply factual inputs to those contracts without creating a competing runtime-lock schema. Later Wine, FEX and graphics implementation remains in [#4](https://github.com/postmelee/pear/issues/4), [#5](https://github.com/postmelee/pear/issues/5) and [#7](https://github.com/postmelee/pear/issues/7).

## Scope

### Included

- Renew the public source audit for Wine, FEX, DXMT and the dependencies required by their selected build paths. Follow submodules, vendored code, generated-input requirements and downloaded build inputs rather than auditing only top-level repositories.
- Resolve selected repositories, release archives and existing public patches to immutable identities. Compute actual content hashes for acquired inputs; record retrieval date, source location, relevant revision and evidence scope.
- Inspect the chosen trees and relevant upstream changes or merge requests. Where relevant, inspect official CrossOver source offerings and downloaded source contents; distinguish a vendor demonstration, available source, applicable patches and missing implementation.
- Map the loader, page/layout, x18, thread/exception/JIT and Wine/graphics interface requirements to inspected implementation or explicit gaps. Reuse #2's host evidence without treating a matching API spelling as complete runtime behavior.
- Inventory Wine build tools and required PE targets, FEX Windows modules and Darwin host-service requirements, DXMT ARM64EC DLLs and paired native Metal/shader dependencies. Distinguish build-host tools, shipped native components, guest PE modules and platform-supplied SDK/framework prerequisites.
- Record exact candidate compiler, cross-toolchain, SDK, build-system and dependency versions supported by the inspected sources. Identify acquisition and architecture requirements, conflicts and unverified compatibility assumptions.
- Audit actual license/notice files, third-party exceptions, patch provenance and contribution policies for the selected revisions. Keep downstream reuse/distribution obligations separate from upstream contribution acceptance.
- Create a factual source manifest and narrow validation/tests for its identities, hashes, provenance, dependency references and decision consistency. Record unavailable data explicitly instead of inventing values.
- Publish a dated source/gap decision and contributor instructions, with narrow follow-ups to the existing audits and documentation index.

### Excluded

- Implementing or modifying Wine, FEX or DXMT ports; replacing their implementation languages; authoring a new CPU translator or graphics backend.
- Producing or qualifying the complete component builds and runtime packages assigned to #4, #5, #7 and #13. Proposed build commands and inferred compatibility remain explicitly unexecuted until their owning tasks verify them.
- Defining #3's runtime-lock/profile/launch/failure/qualification schemas, manager-language decision or product launch behavior.
- Steam login, game acquisition or execution, proprietary binary analysis, a launcher GUI, installation/recovery features, performance comparisons and public releases.
- Repeating restricted host probes, changing system protections or qualifying a new signing/distribution route. Existing #2 results retain their own limits.
- Downloading commercial preview executables as required runtime inputs, copying opaque installed runtime components, or publishing private diagnostics, profiles, credentials, game files or authenticated prefixes.
- Submitting upstream patches or contacting external maintainers. A contribution-policy inventory does not authorize a submission.

## Design Direction

### Source evidence and inventory

Use `runtime/sources/manifest.json` as Issue #1's factual inventory. Its local format may be versioned so validation and interpretation remain stable; it is not an executable runtime lock or a launch authorization. Source identity, availability, inspection coverage and downstream qualification must remain separate fields or explicitly distinguishable records.

For a Git input, retain the canonical source URL, immutable commit and any required submodule identities. For an archive or patch, retain its retrieval URL, measured SHA-256 and its relationship to the selected source revision. State which bytes or tree representation a digest covers. A tag or branch alone is not a pin. Repository-controlled hashes verify acquired identity but do not independently prove publisher authenticity; preserve available publisher verification evidence separately.

Inspect the chosen source scope before making absence claims. A missing string in sampled files is not proof that an implementation is absent from every tree or branch. Existing patch records must identify their base, origin, order, content digest, applicable license and observed applicability; an unimplemented behavior has a gap record and no fabricated patch hash. Do not silently resolve patch failures against a different revision.

Downloaded sources and raw inspection output belong in a dedicated ignored area under `.build/`. Commit reviewed metadata, evidence summaries and the necessary redistributable validation fixtures. Do not vendor entire upstream trees or redefine Pear's project license in this task. Apple toolchains/SDKs and system frameworks are documented external prerequisites; do not describe them as public runtime source or promise redistribution rights.

Toolchain choices are exact candidate inputs tied to inspected requirements, not proof of mutual compatibility. Record source-required, locally observed and not-yet-verified versions distinctly. If requirements conflict, retain the conflict and its evidence; defer the resulting build/port work to the owning Issue rather than selecting unrelated latest versions independently.

### Handoff and parallel ownership

The minimal handoff to #3 and subsequent tasks consists of:

| Information | Issue #1 responsibility |
|---|---|
| Component identity | Stable component ID, role and dependency references |
| Source identity | Source URL, immutable ref, acquired-content digest and digest scope |
| Patch provenance | Base revision, ordered existing patch identities/hashes, origin and applicability evidence; explicit missing-patch gaps |
| Build context | Toolchain/SDK identities, required host and guest targets, relevant source-declared build settings and constraints |
| Terms | Version-specific license/notice locations, exceptions and contribution-policy evidence |
| Evidence and status | Inspection date/scope, evidence references, known/unknown fields, availability and decision status |

Issue #3 owns how these records are represented or referenced by its product contracts under `runtime/contracts/`. An incomplete research inventory can be valid as an honest record while remaining ineligible for runtime selection or qualification. #3 may use clearly labeled synthetic fixtures during parallel work; they cannot become real source pins. Neither task gains an undocumented acceptance dependency on the other's unfinished implementation.

Coordinate changes to the handoff concepts through the task coordinator. Keep Issue #1 writes in its assigned manifest, validation, documentation and work-artifact paths. The coordinator serializes shared documentation-index, audit and daily-board updates; neither worker overwrites the other's work.

### Source-feasibility decision

The final decision must name the exact candidate component set and the requirements considered:

| Decision | Meaning | Downstream effect |
|---|---|---|
| `go` | The audited required source/tool inputs and known existing patches are identified and available; no unresolved input blocks the proposed implementation/build work. | Enables the matching task plans, not a runtime or game acceptance claim. Build and behavioral compatibility still require their own evidence. |
| `needs-port` | Reusable inputs are identified, but concrete required macOS behavior or integration patches remain to be implemented. | Enumerate the gaps, owners and tests for #4/#5/#7. Approved port work may proceed; affected runtime acceptance remains unsatisfied until those gaps are implemented and verified. |
| `blocked` | A required source, usable input, right or prerequisite is unavailable or cannot be established from the inspected evidence. | Record a no-go for the affected candidate path and the exact condition needed to revisit it. Do not unblock dependent runtime acceptance or silently substitute a commercial binary or different architecture. |

An audit/report may be completed with `blocked` when it accurately accounts for every requirement and the maintainer accepts that outcome. Issue closure then means the investigation was completed, not that its source gate passed. A checked dependency box or closed Issue is insufficient evidence to qualify a downstream runtime against a recorded no-go.

## Document Location Judgment

The following proposal reuses Pear's existing `docs/` root and the task-artifact locations already established in the repository. It does not move historical research or place product documentation in `mydocs/manual/`. Approval of this plan must include these locations before those documents are added or changed.

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| Source qualification guide | Official contributor guide with dated source decision and explicit limits | Runtime contributors and reviewers | `docs/source-qualification.md` | `runtime/sources/README.md` | Keep reusable acquisition, inventory interpretation and gap decisions beside the architecture and host guide. |
| Source inventory | Machine-readable engineering input; not a runtime-lock contract | Build/port workers and contract consumers | `runtime/sources/manifest.json` | `docs/research/source-inventory.json` | Separate factual source inputs from prose research and from #3's product contracts. |
| Existing source and graphics audits | Historical technical research with narrow dated follow-ups | Contributors and reviewers | `docs/research/macos-runtime-audit.md`, `docs/research/graphics-and-game-integration.md` | `mydocs/tech/` | Preserve original dates/findings and link renewed evidence without relocation or retrospective rewriting. |
| Documentation index | Official documentation navigation | Contributors | `docs/README.md` | Root `README.md` | Add only a narrow link to the new contributor guide; avoid an unrelated project-status rewrite. |
| Task plans, stage evidence and final report | Issue-specific work artifacts | Task requester, contributors and agents | `mydocs/plans/`, `mydocs/working/`, `mydocs/report/` | `docs/` | Separate approval/progress records from reusable contributor documentation. |

## Expected Changed Files

New, with exact implementation details subject to the later implementation plan:

- `runtime/sources/manifest.json` — factual inventory and source-feasibility metadata.
- `tools/sources/validate_inventory.py` — bounded identity/hash/reference/decision checks; no automatic runtime launch or upstream script execution.
- `tests/sources/` — redistributable positive and failure fixtures for the inventory checks.
- `docs/source-qualification.md` — acquisition/verification instructions, source coverage, terms and gap decision.

Modified only as needed and coordinated with the parallel task:

- `docs/README.md` — guide link.
- `docs/research/macos-runtime-audit.md` and `docs/research/graphics-and-game-integration.md` — dated follow-up links, preserving prior findings.

Task artifacts:

- `mydocs/orders/20260928.md` — coordinator-owned daily-board update.
- `mydocs/plans/task_m1_1.md` — this task plan.
- `mydocs/plans/task_m1_1_impl.md` — created only after task-plan approval.
- `mydocs/working/task_m1_1_stage{N}.md` and reviewed supporting evidence files with the same task prefix.
- `mydocs/report/task_m1_1_report.md`.

Existing `/.build/` exclusions cover local acquisitions and raw results. No change to shared ignore rules, manuals, #2 probe code, #3 contracts or upstream implementation is planned.

## Tentative Stages

- **Stage 1 — Resolve and acquire identifiable source inputs**
  - Revisit the historical references, choose explicit candidate revisions and acquire the required public source/archive/submodule inputs into isolated local storage.
  - Produce the component/dependency inventory with measured identities and explicit unavailable inputs. Record inspection coverage and evidence dates without claiming a build.
- **Stage 2 — Audit source coverage, existing patches and terms**
  - Inspect the selected Wine/FEX/DXMT paths and relevant public changes, including CrossOver source contents where applicable. Map host and graphics requirements to reusable code, existing patches or concrete missing behavior.
  - Record patch provenance/applicability and version-specific licenses, notices, exceptions and contribution policies. Verify that factual claims cite the inspected revision and scope.
- **Stage 3 — Pin candidate tool inputs and validate the inventory**
  - Resolve source-declared build-tool/SDK/target requirements and document conflicts or unverified compatibility. Complete the inventory and the minimal #3 handoff.
  - Implement the bounded validator and meaningful rejection fixtures. Explicit unknowns may remain in research records but cannot pass readiness checks for required candidate inputs.
- **Stage 4 — Reproduce source acquisition and issue the decision**
  - Repeat retrieval/materialization from the documented immutable inputs in fresh local storage, verify hashes and references, and compare outcomes. This is source-input reproduction on the declared environment, not a clean runtime build or independent game qualification.
  - Publish the contributor guide, acceptance mapping and `go`/`needs-port`/`blocked` decision. Preserve historical research and record the precise obligations passed to subsequent tasks.

Each stage retains the workflow's approval checkpoint. This plan does not authorize starting implementation before its approval or skipping the implementation-plan review.

## Verification Plan

### Stage Verification

- Stage 1: resolve repository commits and submodule identities; compute acquired archive/content hashes; verify retrieval locations and required dependency coverage. Check that a moving branch, unacquired archive, missing source or failed request cannot appear as a verified input. Preserve the exact scope of unresolved searches.
- Stage 2: trace every reuse/gap claim to inspected source and every existing patch to its base, origin and bytes. Where applicable, test patch applicability in an isolated disposable source copy without implementing new behavior. Inspect license/notice files and contribution policies at the selected revisions, distinguishing obligations from unresolved questions.
- Stage 3: compare the candidate tool inventory with source build definitions and relevant installed-tool metadata. Test duplicate/missing component identities, mutable-only refs, missing required digests, mismatched local content, broken dependency/evidence references, missing patch provenance and inconsistent readiness decisions. Do not equate valid JSON or a correctly shaped digest with verified source availability.
- Stage 4: repeat source acquisition/materialization from the documented set; verify actual content and ordered existing patch identities. If a host-generated archive is not byte-stable, explain the representation and verify the immutable tree rather than quietly replacing its digest. Check the contributor instructions, final gap table, privacy, document links and unchanged historical findings.

Exact commands and fixtures will be fixed in `task_m1_1_impl.md` after approval. The verification tools must not execute downloaded build scripts merely to inspect a repository, and must not need Steam data, signing secrets or game files.

### Integrated Verification

| Issue #1 Acceptance Criterion | Required evidence |
|---|---|
| A source manifest identifies immutable revisions, archive/patch hashes and build-tool versions, with evidence for every required component. | Reviewed inventory, actual acquired identities/digests, dependency coverage, candidate toolchain/target records and repeat-acquisition evidence. Unavailable required components are explicit and prevent a positive readiness decision. |
| A gap table separates reusable code, patches to implement, unavailable inputs and external prerequisites. | Requirement-to-source mapping with inspected scope, existing-patch provenance, concrete missing behavior, responsible downstream Issue and verification obligation. |
| No opaque preview binary or placeholder hash is classified as a reproducible input; a no-go finding is explicit and downstream work remains blocked. | Validator rejection cases plus the final decision. Unknown values and binary-only inputs cannot pass required source readiness; report completion or Issue closure does not override a recorded no-go. |

- Factual #1 handoff fields remain consistent with #3 ownership; no competing runtime-lock, profile or launch schema is introduced.
- Runtime build, integration, game and distribution qualification remain unassessed by this task. #2's tested host scope is retained rather than generalized to an unbuilt runtime.
- All repository artifacts are English. No credentials, private profiles, game files, installed commercial runtime files or raw personal diagnostics enter Git.
- Task-owned changes are reviewed and committed before PR preparation. Preserve unrelated user or parallel-task work instead of deleting or committing it to force an empty status.
- `git diff --check` passes without warnings; local document links and manifest/evidence references resolve within their declared scope.

## Risks

- **Historical evidence mistaken for current inputs:** refresh source and policy evidence at explicit revisions; retain original audit dates and never promote old branch links or vendor claims to pins without verification.
- **A complete inventory mistaken for a working port:** state source availability and missing behavior separately. Full build/runtime qualification remains with #4/#5/#7 and later gates.
- **Hidden dependency or incompatible toolchain:** inspect actual build rules, submodules and downloaded inputs; record conflicts and avoid adopting a CI binary or unrelated latest version as a shortcut.
- **Incomplete source or unresolved terms:** classify the affected requirement as blocked and retain an explicit no-go. Public download availability alone does not establish source completeness or reuse rights.
- **Contribution restrictions confused with licenses:** inventory both independently; retain upstream languages and attribution, and make no promise of upstream acceptance or submission.
- **Parallel schema/document drift:** keep #1 factual records and #3 product contracts separately owned, agree the minimal handoff, and serialize shared edits through the coordinator.
- **Reproduction scope overstated:** distinguish repeated source acquisition, eventual component builds, same-host checks and independent runtime reproduction. Matching hashes cannot establish CPU, ABI or graphics correctness.

## Approval Request

- Approve the bounded source/toolchain qualification scope, four tentative stages, explicit exclusions and three-way decision semantics.
- Approve the proposed document and inventory locations, preserving the existing audits and keeping task records in `mydocs/`.
- Approve the #1/#3 ownership boundary and minimal factual handoff, with shared documentation/board changes coordinated centrally.

After approval, `task_m1_1_impl.md` will define concrete stage artifacts, acquisition and verification commands, fixtures and commit messages. No runtime source is changed and no fresh source, build or compatibility result is claimed by this task-plan preparation.

## Approval Record

The task requester explicitly approved both task plans and their document locations on September 28, 2026, and subsequently approved both detailed implementation plans and parallel Stage 1 execution. The approved scope and exclusions above remain unchanged. Subsequent stages retain their individual report checkpoints.
