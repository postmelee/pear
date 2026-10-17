# Task #47: Rosetta Preview delivery

GitHub Issue: [#47](https://github.com/postmelee/pear/issues/47)
Milestone: M3 — Rosetta-based Megabonk Preview

## Work Summary

Three stages deliver a small Pear app and optional shared CLI for official Windows
Steam, with a source-identifiable Rosetta/Wine/DXMT runtime, preserved state,
ordinary-user signed downloads and a public documentation/catalog entry point.
The final downloadable version is 0.1.0-preview.3 (e574ba1); current website and
reporting changes do not alter those signed bytes or establish Rosetta-free M1.

## Changed Files and Impact Area

| Path | Change summary | Impact area |
|---|---|---|
| `preview/` | Rust core, thin AppKit UI, runtime build/patch/notices, packaging/signing | Installation, official Steam launch, recovery and migration |
| `.github/workflows/` | Portable/macOS candidate checks, protected signing and master-only Pages | Distribution and source-notice enforcement |
| `README.md`, `docs/` | Player/contributor guidance, component disclosures and reviewed reports | Public entry points |
| `tools/catalog/`, catalog generator/tests | Steam identity search, consistent game reports and download tabs | Static site, no separate vote/authentication store |
| `mydocs/` | Plans, evidence, reports and retention handoff | Exact-scope audit trail |

## Document Location Verification

| File | Planned location | Actual location | Result | Evidence |
|---|---|---|---|---|
| Overview and index | README and docs/README.md | Same | OK | Approved plan and final publication direction |
| Player/release guides | docs/rosetta-preview.md, docs/development/preview-release.md | Same | OK | Existing official documentation updated |
| Catalog/community | docs/compatibility and existing docs/community guides | Same | OK | Approved entry-point extension |
| Task evidence | mydocs plans/working/report | Same | OK | Stage/final templates |

## Quantitative Before/After Comparison

| Metric | Before | After |
|---|---|---|
| Public Pear app entry | None | Signed/notarized preview.3 DMG plus app/CLI archives and matching source |
| Reviewed catalog observations | One menu-only record | Two dated records including owner-confirmed sustained play/save/relaunch |
| Final documentation/search checks | Preparation-only routing | 94 Python tests, 6 Node tests passing; 48 changed source notice checks |
| Verified hardware scope | One M4 Pro | Same M4 Pro plus fresh standard account; no expanded hardware claim |

## Verification Results

| Acceptance criterion | Result |
|---|---|
| Reuse/provenance | OK: historical Libraries baseline investigated, replaced with pinned source-built Wine/CodeWeavers/DXMT and corresponding source/notices |
| Ordinary-user app/CLI | OK: signed/notarized packages, public HTTPS checksum verification and owner-confirmed fresh-account app flow without disabling protections |
| Official Steam and owned game | OK: direct owner login, normal installation/Steam Play and recorded Steam initialization |
| Sustained play and state | OK: owner confirmed requested 20+ active minutes, input/audio, progress after signed-app relaunch and normal exit |
| Second clean setup | OK within approved same-Mac test-user route; owner confirmed final checklist then deleted account; not second physical hardware |
| Recovery and preservation | OK within Stage 2 cases and later migration/relaunch checks; no generic repair or all-network recovery claim |
| Runtime/private separation | OK: immutable pinned runtime separate from credentials/games/saves; release allowlists and exact source |
| Guidance and downloads | OK: versioned app/CLI links, current component/OS requirements and bounded evidence; Pages goes live only after master deployment |

### Stage Verification Results

- [Stage 1](../working/task_m3_47_stage1.md): selected source-identifiable runtime and normal official Steam/game route.
- [Stage 2](../working/task_m3_47_stage2.md): bounded interrupted setup, restore, reinstall and preserved-state normal exit.
- [Stage 3](../working/task_m3_47_stage3.md): exact signed preview.3, owner-confirmed final fresh-account checklist, user guide and download wiring.
- [Dated Stage 3 records](../working/task_m3_47_stage3_preparation.md): prior failures, corrections and exact candidate/CI receipts.

## Residual Risks and Follow-up Work

### Residual Risks

Same-Mac clean account shares the host OS/Rosetta/tools. Another physical Mac,
other games, controllers, Steam Cloud correctness and performance remain unverified.
20 minutes is an owner-confirmed lower bound, not instrumented exact timing.
Game/Steam build and graphics settings for the last manual session were not fully
captured; reports show those unknowns. Steam upstream updates may change behavior.
The public Preview remains a pre-release; no latest/stable promotion is implied.

### Follow-up Candidates

Broader community observations, independently reproduced configurations, Homebrew
and preservation-aware removal may be separately scoped. Existing native work
(#11/#12) is unchanged; no other chat was invoked or asked to start work.

## Retention Handoff

Retain #47 checkout and ignored signed/source receipts, authenticated state and
recovery archives until release maintenance/recovery consumers no longer need
them. No ignored evidence is made public or discarded by PR/Issue completion.
The owner deleted the temporary test account after successful verification; this
turn did not reclaim or measure those bytes. Final site output is disposable
following successful deployed-content verification; no extra runtime copy exists.
See Stage 3 for roots, owner/consumers, scope and accounting limitations.

## Approval Request to Task Requester

Final verification and catalog publication were explicitly requested on October 15.
Publish the reviewable PR and complete the master-only deployment within that
scope, preserving immutable preview.3 and all private recovery state.

## Approved download layout publication follow-up — 2026-10-16

The download page keeps its original layout while moving system requirements
below the installation flow and Wine/DXMT versions into Release details. The
requester approved the rendered local preview and deployment. HTML matches that
preview exactly; 94 Python tests, 6 JavaScript tests and governance checks pass.
The existing Pages-only workflow is reused; no workflow configuration, binary,
release assets or home download routing change. This is a bounded #47 follow-up.

Retention handoff: small generated validation output is disposable after public
HTML verification. Existing private runtime/save evidence is outside this change.

## README follow-up — 2026-10-17

Following requester confirmation that PR #58 was merged, the README homepage label
is Website & game reports. The dated native experiment narrative is replaced by
a concise source-ownership/development-validation summary, retaining explicit
incomplete gameplay and full no-Rosetta qualification. Existing #58 guide routing
and exact Preview download URLs remain. The exact #56 report is linked for scope.
Governance passed (37 documents, 372 local targets); incremental source notices
and diff checks passed. This documentation-only change performs no runtime tests.
The repository About homepage is https://postmelee.github.io/pear/.
No material build output or change to retained private state.
