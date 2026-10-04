# Task #7 — Reproducible DXMT Build and Verified Native Metal Pairing

GitHub Issue: [#7](https://github.com/postmelee/pear/issues/7)
Milestone: M1

## Work Summary

- Target Issue: #7
- Milestone: M1 — Megabonk on Apple Silicon without Rosetta
- Stage count: 5, complete
- Purpose: produce the versioned ARM64EC/ARM64X graphics artifacts, native ARM64 Metal dependencies and an actually verified Wine/Metal interface.

The task's three acceptance criteria are satisfied. The [Stage 5 report](../working/task_m1_7_stage5.md)
and [sanitized observations](../working/task_m1_7_stage5_reconstruction_observations.json)
contain the final source, build, runtime, two run and independent replay identities.
This completes the development component; it does not qualify Megabonk or a
user-downloadable runtime.

## Changed Files and Impact Area

| Area | Result |
|---|---|
| `runtime/dxmt/`, `tools/dxmt/` | Pinned source/tool/dependency roles, actual graphics builds, typed Wine/Metal interface and strict final reconstruction |
| `runtime/wine/patches/0004-arm64-native-heap-reservation.patch` | Standalone shared loader dependency correcting the reproduced low-address Foundation failure |
| `tests/dxmt/` | Source/refusal/reconstruction controls and original finite native fixture |
| `docs/development/dxmt-build.md`, `wine-host.md`, graphics research | Contributor commands, evidence limits and #5/#8 handoff |
| `mydocs/` | Approved plans, five stage reports, retained failure history, observations and completion board |

## Document Location Verification

| Document | Planned and actual location | Result |
|---|---|---|
| Contributor build procedure | `docs/development/dxmt-build.md` | OK |
| Wine integration handoff | `docs/development/wine-host.md` | OK |
| Dated graphics research | `docs/research/graphics-and-game-integration.md` | OK |
| Reports, plans and observations | Existing `mydocs/` locations | OK |

The original Issue and approved implementation plan define these locations.
No new product-documentation root, roadmap or stable public private-structure ABI was introduced.

## Quantitative Before/After Comparison

| Metric | Before | Final result |
|---|---|---|
| DXMT artifact proof | Upstream CI/source was a starting point | Four builtin ARM64X Windows DLLs and a thin ARM64 native bridge constructed and inspected |
| Wine/Metal boundary | Copied private window layout; unverified pairing | Typed opaque ownership interface, 39 native cases passed in each of two final runs |
| Final unsigned reconstruction | Raw winemetal differences rejected | All 2,878 complete inventory entries equal without normalization |
| Required native failure | 33 rows and missing terminal | Source-built loader correction; 39 rows, PE terminal, physical lifetime and cleanup passed twice |
| Portable final regression | Historical stage-specific results | 530 tests, 522 passed, eight conditional skips |

## Verification Results

| Acceptance criterion | Result |
|---|---|
| Clean complete versioned artifact set with architecture/dependency reports | OK — two fresh graphics constructions, two source-built loader outputs and complete strict raw comparison |
| Documented Wine exports and winemetal pairing against the selected port | OK — source-matched typed boundary, final loader correction and two independently replayed native runs |
| No runtime compatibility claim based solely on compilation/upstream artifacts | OK — executed ordinary native scope is explicit; FEX, translated D3D, games and distribution remain unqualified |

### Stage Verification Results

- [Stage 1](../working/task_m1_7_stage1.md): source/tool/layout accounting.
- [Stage 2](../working/task_m1_7_stage2.md): native shader dependency construction and inspection.
- [Stage 3](../working/task_m1_7_stage3.md): actual Windows/native graphics artifacts and dependency reports.
- [Stage 4](../working/task_m1_7_stage4.md): typed bridge, original finite native protocol and physical lifetime.
- [Stage 5](../working/task_m1_7_stage5.md): strict reconstruction, concrete loader repair, final source-bound execution and handoff.

## Residual Risks and Follow-up Work

### Residual Risks

This is finite same-host component evidence. Older OS versions, other hardware,
arbitrary races, ARM64X runtime loading, translated rendering, Steam, Megabonk,
performance and ordinary-user authorization remain unqualified. Historical
failures and raw private evidence are retained. A common cause for every earlier
fault is not asserted. The reconstruction procedure requires its exact retained
private source/tool/qualification inputs.

### Follow-up Work

#5/#6 integrate the loader patch and revalidate affected low mapping, MAP_JIT and
metadata-budget assumptions before their FEX/x64 claims. #8 verifies actual
translated D3D11 rendering. Existing #10–#13 own full observation, Steam/game and
distribution. No new generic evidence framework or unrelated test matrix is
required by this handoff.

## Completion and Publication Status

Technical acceptance and Stage 5 are complete. The initial completion checkpoint
was intentionally left uncommitted and unpublished. On October 5 the requester
subsequently authorized publication, merge, Issue closure and storage cleanup.
The publication workflow preserves Stage commits and verifies CI on the integrated
head. Final source/runtime evidence is retained at its original path for #5/#8;
only completed diagnostic scratch is selected for verified archival. Actual
remote and cleanup outcomes are recorded after those operations finish.


## Publication Integration Verification — October 5

The completed Stage 5 source/report checkpoint is commit `24e1afa`; the
`330f86f` merge integrates master `abaabc2`. The two conflicts were document
index links and the October 4 board; both tasks' links and all four existing
Issue rows were preserved. No runtime producer changed: all 42 final
reconstruction producer hashes and both successful finalization receipts still
match. No repeated graphics/compiler build or native run was required.

The #14 Stage 4 handoff patch, SHA-256
`7087e30de2b0e7819d7d1004576df6ffa7b7738171e06ea212848d14c8228a5a`,
was applied only after both target before-hashes matched. Its four test-helper
lines use platform TemporaryDirectory selection and resolve the newly allocated
root, preserving strict alias-refusal tests. On the integrated checkout, both
platform-default temp and a physical TMPDIR containing spaces passed: pair
96 run / 88 passed / 8 known optional skips, native 37 run / 37 passed. The
custom scratch directory was empty afterward. Private logs and exit receipts
are retained under `.build/task7/publication1/`. These are synthetic test
results; the earlier final native evidence retains its original scope.

Offline governance passed for 24 documents / 211 local targets; diff checks
passed. Hosted CI remains a separate pre-merge gate. The existing historical
Stage 5 report and observations preserve the original 530-test checkpoint.
