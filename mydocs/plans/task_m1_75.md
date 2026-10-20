# Task #75 — Split-runtime readiness and WGI source binding

GitHub Issue: [#75](https://github.com/postmelee/pear/issues/75)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

## Purpose

Reconcile the documented split-runtime structure with the accepted development
baseline, review the four private repositories for source publication, and
establish the evidence available for WGI source-to-development-PE correspondence.
Present publication findings before any visibility change. Preserve the working
Rosetta release and all native debugging inputs and artifacts.

## Background

[Task #56](../report/task_m1_56_report.md) and PR #58 completed the bounded
source/ownership split and developer route. The README still links the report
before the P1/P2 remediation. Final component docs also retain obsolete
publication/cutover statements. These are current narrative corrections; frozen
provenance and original stage reports must remain unchanged.

The [current handoff](../../docs/development/rosetta-free.md#continue-the-developer-megabonk-investigation)
records matching candidate3/runtime12 WGI bytes, but not their source/build
binding or an observed natural failing call. The bounded Wine reconstruction
recipe does not compile WGI. The original D36 loading refusal, EC status 3 and
owner cleanup remain the observed outcome, without a root-cause conclusion.

Live open-Issue/PR inspection on 2026-10-20 found no duplicate bounded task.
#10/#11/#12/#13 retain architecture observation, Steam/game and assembly scopes.
No open PR currently overlaps this work. Main master is `2c151f1d074fab5a55bc2d77e25b5fb81aedc257`.

## Scope

### Included

- Existing documentation and current editing/build/tool baseline reconciliation.
- Exact private remote refs, downstream reachable history, upstream provenance,
  license/notice handling, private-data exclusions and GitHub publication surfaces.
- Read-only WGI source/object/generated/header/tool/PE investigation and a
  bounded explicit reproduction/comparison procedure when prerequisites permit.
- Issue, task/implementation plans, stage verification/report/commits and final
  sanitized review results with private exact evidence retained separately.

### Excluded

- Repository visibility/default-branch changes, history rewriting or upstream submissions.
- Natural game-call observation runs, behavior fixes, gameplay, Steam, input injection,
  signing, candidate activation, installation or public runtime distribution.
- Deletion/movement of old worktrees, private state, builds, games or debugging inputs.
- Full lower-layer rebuild or a claim of clean-clone player readiness.

## Design Direction

- Reuse the existing five ownership boundaries and official documentation tree.
  Wine owns WGI C code and its module tests; common runtime owns composition,
  exact input admission and shared diagnostics; Pear owns product/game policy.
- Preserve upstream Wine Makefile/spec/IDL/C patterns and existing toolchains.
  New tooling, if required, is a small explicit recipe/comparison adapter.
  No language rewrite or alternate runtime/PE runner is proposed.
- Separate final documentation/source tips from candidate build pins and executed
  tool pins; keep Task56's original signed/frozen identities unchanged.
- Audit public upstream ancestry separately from Pear-added/reachable history.
  A limited scan or existing notice-check pass is not whole-history publication
  clearance. Record absent/unreadable/oversized surfaces and manual dispositions.
- Use actual upstream licenses and contributor policies. Public downstream
  hosting does not imply upstream acceptance. Apple Metal guidance is not
  applicable to this source/PE-only scope.

## Document Location Judgment

The requester approved reconciling existing documents and current baseline in
the preceding proposal and current instruction. This table concretizes those
locations; it adds no new product-documentation root or roadmap.

| File | Classification | Audience | Selected location | Alternative | Reason |
|---|---|---|---|---|---|
| Pear README and documentation index | Official entry | Users/contributors | Existing `README.md`, `docs/README.md` | New overview | Correct links/status where readers already start |
| Architecture/runtime/development boundaries | Official guidance | Developers/integrators | Existing `docs/architecture.md`, `docs/runtime-contracts.md`, `docs/development/rosetta-free.md` | `mydocs/manual/` | Existing canonical owner/baseline description |
| Component README/development/NOTICE | Component guidance/attribution | Contributors | Existing files in their separate source repositories | Pear-only copy | Keep source owner and provenance together |
| Publication/WGI findings | Dated investigation | Maintainers | `mydocs/tech/task_m1_75_*.md` | Permanent policy text | Evidence, not a second architecture or roadmap |
| Plans, reports and daily board | Workflow | Maintainers | Existing `mydocs/` roles | `docs/` | Preserve task history separately |
| Raw audit/input/PE records | Private operational evidence | Local developers | Task-owned external private evidence root | Git/release | Avoid personal paths, selectors, logs or payload exposure |

## Expected Changed Files

Modified when relevant: Pear `README.md`, `docs/README.md`,
`docs/development/rosetta-free.md`, `docs/architecture.md`,
`docs/runtime-contracts.md`; component existing README/development/NOTICE files.
Do not sweep unrelated product wording or edit frozen source-cutover records.

New: sanitized `mydocs/tech/task_m1_75_publication_readiness.md` and
`mydocs/tech/task_m1_75_wgi_binding.md`; minimal component-owned recipe/comparison
files only if investigation establishes their need, with exact paths added to
the implementation plan before edits.

Task artifacts: `mydocs/orders/20261020.md`, this task plan,
`mydocs/plans/task_m1_75_impl.md`, `mydocs/working/task_m1_75_stage{1,2,3}.md`,
and `mydocs/report/task_m1_75_report.md`.

## Artifact Lifecycle

| Artifact/root | Class/state | Owner/consumer | Identity/recovery | Retain reason | Release condition |
|---|---|---|---|---|---|
| Task56 component/build/tool pins and candidate3 | Retained immutable dependency | Task56/#12/#13 | Exact existing locks/closure and paths | WGI comparison and later diagnosis | No release in #75 |
| Old/corrected Pear producer roots and component source roots | Retained input | Existing selectors/builders | Preserve byte/mode/path bindings and dirty state | Current consumers | No release in #75 |
| Installed app, Steam/game/prefix/save/signing state | Active/private | User and existing release | No writes, copies or execution | User operation | No release in #75 |
| New Task75 Pear/component worktrees | Source output | #75 review | Separate branches from exact recorded bases | Reviewable changes | After merge and independent dependency check |
| Private audit and WGI outputs | Evidence/new input | #75 and next WGI task | Hashed inventories, scripts, commands, timings | Reproduce findings without originals changing | After accepted successor evidence; no blanket deletion |

Reuse/copy decision: reuse existing Git object stores and immutable inputs
read-only. No complete runtime, game or prefix copy is required. Prefer sparse
documentation worktrees for large component repositories.

Peak-space planning: the new Pear checkout has 103,781,446 logical tracked bytes;
the observed filesystem free space was 21,797,498,880 bytes before substantial
work. Initial sources/audit/evidence have a 512 MiB incremental ceiling. Do not
copy large history, download archives or begin compilation under this estimate.
Stage 3 must calculate module-specific source/generated/tool/intermediate/final
overlap and available space before a build; unknown peak requirements block
that build, not independent read-only investigation.

## Tentative Stages

- **Stage 1 — Reconcile the development baseline and documents**
  - Pin current authority/compiled/tool identities and preserve existing inputs.
  - Correct current status/link statements in isolated branches.
  - Verify affected documentation, references, notices and unchanged runtime bytes.
- **Stage 2 — Review source-publication readiness**
  - Review all four private repositories and remote publication surfaces.
  - Record coverage, inherited upstream boundaries, findings and readiness decisions.
  - Keep visibility private and present unresolved findings without concealing them.
- **Stage 3 — Bind WGI source/build inputs to the development PE**
  - Inventory the selected module and exact source/build prerequisites.
  - Reproduce and compare when possible, with an explicit storage plan.
  - Record exact correspondence or demonstrated mismatch/remaining evidence gaps;
    hand off natural-call observation without performing it.

Read-only investigations supporting these stages may proceed concurrently.
Implementation, required verification, stage report and commit remain ordered.

## Verification Plan

### Stage Verification

- Stage 1: exact remote/base/source-role records; document link/status checks;
  existing portable documentation suite; incremental notice checker; `git diff --check`.
- Stage 2: pinned remote heads/tags, reachable history scope, streamed content
  inventory/scanner coverage, manual hit review, GitHub metadata/Actions inventory;
  no unresolved scanner failure represented as a clean publication result.
- Stage 3: source/generated/header/compiler/link input facts; PE identity,
  command trace and byte/section comparison; test meaningful rejection and
  unexplained-difference cases for new tooling. Preserve raw original evidence.

Git/Python/gh are available during planning. Exact WGI compiler/SDK/object inputs
remain under read-only investigation; no native/build result is claimed yet.
Historical controls are reused only as provenance of unchanged candidate bytes.
They do not validate new WGI output or authorize execution.

### Integrated Verification

- Stage outputs agree on source ownership and current revision roles.
- Public summaries contain no private paths/game material/credentials.
- Protected artifacts and current states remain unchanged within observed scope.
- Four repositories stay private; no default/ref/history alteration outside task branches.
- Required checks pass; clean tracked worktrees and `git diff --check` before PR.

## Risks

- **Historical vs current refs:** preserve immutable reports and change only current guidance.
- **Public exposure:** audit all reachable downstream additions and remote surfaces;
  classify unverified scope explicitly, retain sensitive detail privately.
- **WGI ambiguity:** binary equality between candidates is not source provenance.
  Do not silently substitute current source or normalize unexplained bytes.
- **Missing input or space:** record exact gap and solve only within approved scope;
  no broad rebuild or old-artifact deletion.
- **Concurrent work:** Task47 cleanup belongs to its owner; shared/runtime roots
  remain read-only, and existing uncommitted source is never overwritten.

## Approval Record and Request

The requester explicitly authorized this Issue-backed work and the preceding
document/baseline proposal on 2026-10-20. Registration and planning implement
that request. The implementation plan supplies concrete stage gates.

Confirm whether the three stages may proceed continuously with verification,
reports and commits at each boundary, or whether individual stage continuation
should be requested under `AGENTS.md`. Repository visibility change, game/native
execution and unrelated deletion remain excluded either way.
