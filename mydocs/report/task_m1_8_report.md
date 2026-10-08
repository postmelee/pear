# Task #8 Final Report — Translated D3D11 Qualification

GitHub Issue: [#8](https://github.com/postmelee/pear/issues/8)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

## Work Summary

- Target Issue: #8; four stages, October 8–9, 2026.
- Purpose: qualify finite x64 D3D11 rendering and presentation through one
  source-built ARM64 Wine/FEX/DXMT/Metal candidate.
- Result: the required graphics fixtures pass. Megabonk reaches Unity startup but
  fails game DLL image admission; M1 and ordinary-user support remain incomplete.
- Publication state: publication and review approved; Issue remains open pending PR merge approval.

## Changed Files and Impact Area

| Path | Change Summary | Impact Area |
|---|---|---|
| `runtime/wine/patches/0005-*`, `runtime/fex/patches/graphics/` | Preserve VM owner identity, high-address FEX allocation and delivered scalar repair | Wine/FEX integration |
| `runtime/dxmt/patches/` | Pipeline/presentation observations, managed surface v2 and bounded controls | Native graphics and physical lifetime |
| `tests/dxmt/translated_*`, targeted reader tests | D3D11 fixtures, independent readbacks, visible frames and rejection cases | Finite correctness |
| `tools/dxmt/translated_*` | Admitted construction, existing signing/supervision reuse, execution and evidence replay | Development qualification |
| `docs/development/dxmt-build.md` | Combined-candidate reproduction and measured limits | Contributors/integrators |
| Task plans, four stage reports and allowlisted observations | Decisions, original failures and acceptance evidence | Review/handoff |

## Document Location Verification

| File | Planned Location | Actual Location | Result | Evidence |
|---|---|---|---|---|
| DXMT reproduction/coverage | Existing `docs/development/dxmt-build.md` | Same | OK | Approved plan location judgment; existing native-only sections preserved |
| Affected CPU guide | Existing guide only if needed | Unchanged | OK | Combined graphics handoff records the integration; no relocated CPU contract |
| Plans/reports | Existing `mydocs/` task roots | Same | OK | Four stages, final report and sanitized observations |

## Quantitative Before/After Comparison

| Metric | Before #8 | Final candidate |
|---|---|---|
| Translated D3D11 readbacks | Unperformed | Five cases / seven passing readbacks |
| Individually observed presentation | Unperformed | 18 frames / three device-window cycles |
| Physical graphics teardown | Native-only #7 evidence | Nine native creations and deallocations; zero final leases/attachments |
| Native bridge | 39 on #7 candidate | Original 39 + 23 v2 controls on combined candidate |
| CPU regression | Separate #6 runtime | 18 passes / AVX unexposed, 32,768 ordering pairs on repaired combined runtime |
| Original delivered scalar failures | Two failures during integration | Exact original PEs both recover and exit 42 |
| Actual Megabonk startup | Unperformed on this stack | Unity initialization reached; GameAssembly image admission fails |

## Verification Results

| Acceptance Criterion | Result |
|---|---|
| Expected images/readbacks and lifecycle | OK — all declared finite graphics results pass on one final candidate |
| Intended DXMT/Metal module route | OK — fixture paths/addresses/bytes and native FEX/winemac/winemetal/Metal observations; no silent renderer substitution |
| Targeted validation | OK — required device/pipeline instrumentation observed and raw diagnostics retained; no required error; performance remains unperformed |
| Acceptance dependencies #6/#7 | OK — merged prerequisites reused at exact pins; affected integration and full repaired CPU corpus revalidated |
| Original failure preservation | OK — unchanged original PE/source records retained with actual repair outcomes |

Final runtime receipt SHA-256:
`f90b2a601f556595a07b38bfa695def75b7f1def9bb1018e7dacb73bf7444f5f`.
Host: M4 Pro, ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113), existing development
profile and normal security protections. Forty-one native images have recorded
ARM64 closure/signature evidence. This qualifies observed fixture execution, not
complete late-loaded process coverage or arbitrary games.

### Stage Verification Results

1. [Stage 1](../working/task_m1_8_stage1.md): combined candidate, translated device,
   original native 39, CPU corpus and finite ordering.
2. [Stage 2](../working/task_m1_8_stage2.md): buffers/textures/shaders/compute,
   depth/blend/raster and seven independent readbacks with actual instrumentation.
3. [Stage 3](../working/task_m1_8_stage3.md): v2 Wine surface ownership, 18 actual
   frames, physical lifetime and exact original scalar failure recovery; full
   affected CPU and graphics reruns on the final candidate.
4. [Stage 4](../working/task_m1_8_stage4.md): complete evidence replay, 29 focused
   portable tests, reproduction handoff and one separate owned game diagnostic.

[Stage 4 observations](../working/task_m1_8_stage4_observations.json) bind final
coverage and private evidence hashes. Replayed evidence is not reported as fresh
native execution. No repeated full build was required for Stage 4.

## Residual Risks and Follow-up Work

### Residual Risks

- Megabonk does not yet run successfully. Its unchanged GameAssembly image requires
  57,647,104 bytes, above the loader's 38,993,920-byte image ceiling. Image mapping
  returned `0xc00000bb`; the first refusing branch needs targeted confirmation.
  The 120-second startup deadline expired; cleanup and file integrity passed.
- Normal Steam initialization, input/audio, 20-minute gameplay, save/relaunch and
  complete helper/library Rosetta-independence remain unqualified.
- Sixteen drawable times were zero despite independently observed pixels. Visible
  output passes; timing/performance/power do not inherit that result.
- AVX remains unsupported/not exposed. Finite tests do not establish general
  Windows/WoW64, large workload or arbitrary concurrent self-modifying-code support.
- Existing development authorization is not ordinary-user distribution approval.
- Retained private input/build trees are needed for replay. Independent runtime
  reconstruction and packaging remain #13. No proprietary data or credentials
  are committed; source publication alone cannot replace retained runtime inputs.

### Follow-up Work

- [#40](https://github.com/postmelee/pear/issues/40): trace PE image admission, review larger-image arena and metadata
  budgets with relocation/publication bounds, and reproduce against the unchanged
  owned DLL. Required memory/loader regressions depend on the resulting change.
- #9: consume qualified component identity through the native supervisor/profile.
- #10: complete process and late-loaded module observation.
- #11/#12: normal official Steam and actual Megabonk user flows after loader admission.
- #13–#16: independent assembly, regression, controlled performance and final M1
  qualification only after their own acceptance criteria pass.

## Publication Integration Review

Publication and review were approved on October 9, 2026. Integrated master
`2279f4620e418dfebd2f2da832bc2ff0b897a1d0`, including the merged #9 supervisor.
Only the October 8 and 9 task boards conflicted; both tasks were preserved and
the newer #6 merge/closure status retained. No #8 runtime producer, patch,
configuration or retained candidate input changed during this integration.

- Stage 4 evidence replay passed after integration, including the original
  scalar failures, visible frames, surface controls and affected CPU evidence.
  This is retained-evidence verification, not new native execution.
- Focused portable tests passed: 29 translated reader tests, four surface-control
  tests and three visible-frame tests (36 total).
- Documentation governance passed for 27 documents and 263 local targets;
  staged whitespace checks passed.
- Source review covered delivered scalar repair/publication, VM identity,
  managed surface ownership/rollback/teardown, candidate admission and evidence
  readers. No blocking finding was identified in this bounded review; it is
  not a general concurrency or renderer-conformance audit.
- Existing publication CI covers documentation and portable baseline verifiers.
  The new translated reader/control/frame tests above were run locally;
  broader regression integration remains #14.

## Approval Request to Task Requester

Review the published PR and its CI results before authorizing merge and Issue
closure. Publication is approved; merge and closure are not yet authorized.
