# Task #6 Stage 4 — Integrated CPU Qualification and Handoff

GitHub Issue: [#6](https://github.com/postmelee/pear/issues/6)
Implementation plan: [task_m1_6_impl.md](../plans/task_m1_6_impl.md)
Stage: 4 — complete locally on October 8, 2026; final publication review pending.

## Stage Purpose

Bind the declared instruction, Windows-boundary and ordering results to the same
final Wine/FEX component set. Complete the contributor recipe and final report
without rebuilding unchanged components or implying game qualification.

Context used: the approved task and implementation plans, current Issue #6,
root/tests/docs rules, architecture/delivery documents, Stage 3 report and pinned
reuse decisions. Hyper-Waterfall v0.3.0 `task-stage-report` and `todo` procedures
and the central final-report template apply. #9 has a separate active worktree;
its work and all shared dependency caches remain unchanged.

## Artifacts

| File | Change summary |
|---|---|
| `tools/cpu/qualify.py` | Reuse existing strict comparators, then bind both fixture bundles to matching actual code, receipts, authorization and configuration |
| `tests/cpu/test_qualification.py` | Six focused controls for mixed engine/configuration, changed runtime payload and undeclared fixture differences |
| [Sanitized observations](task_m1_6_stage4_observations.json) | Final component/corpus/reference hashes, all 19 case results and finite ordering counts |
| [CPU guide](../../docs/development/fex-host.md) | Existing approved guide extended with reproduction, coverage and integration handoff |
| [Final report](../report/task_m1_6_report.md) | All three Issue criteria mapped to evidence and remaining limits |

## Body Change Scope / Lossless Preservation

Only the existing approved CPU guide is extended; historical #5 evidence remains
scoped to its original candidate. No new official document or relocated content.
The new verifier reuses `compare.py`, `ordering.py` and existing signing readers.
It independently admits inventories and compares every native Mach-O code origin
before allowing signature-byte differences. Only declared fixture PE paths may
vary; other runtime payload bytes and modes must match. Receipt, authorization
and memory/configuration differences fail closed. No runtime implementation,
Wine/FEX rebuild, owner ABI or security permission change in Stage 4.

## Verification Results

Execution context: Apple M4 Pro ARM64, macOS 26.5.2 (25F84), Python 3.14.4,
existing hardened development authorization. Native Windows x64 host identities,
exact PEs and tool hashes remain those recorded in Stages 2 and 3. These are
instrumented synthetic correctness checks, not gameplay or performance runs.

Commands run from the task worktree (`PEAR_REUSE_SOURCE` selects retained #7):

```sh
python3 -B tools/cpu/run.py --runtime .build/task6/stage3-regression-runtime1 --build .build/task6/native-build3 --reuse "$PEAR_REUSE_SOURCE" --output .build/task6/stage4-candidate.json --name s3reg
python3 -B -m unittest discover -s tests/cpu -p test_qualification.py
python3 -B tools/cpu/qualify.py --build .build/task6/native-build3 --reference .build/task6/native-results3 --candidate .build/task6/stage4-candidate.json --ordering-reference .build/task6/stage3-native-results3/qualification --ordering-candidate .build/task6/stage3-candidate.json --output .build/task6/stage4-qualification
python3 -B tools/check_governance.py
git diff --check
```

- Final-candidate comparison: **18 passed, one AVX case unsupported, zero required
  failures**. Twelve instruction cases were newly executed; seven Stage 3 boundary
  runs were re-admitted unchanged. AVX exit 77 is not an instruction pass.
- Ordering evidence re-admitted: **32,768 measured pairs per host**, zero forbidden
  outcomes, eight joined workers and eight checked FEX retirements. Actual scalar,
  vector and memcpy software TSO is enabled for all nine participant lifetimes.
- Both fixture bundles use FEX DLL
  `2925abaafea4d4c3293c30e778629208b507d9690e7d2b128e9b500733608364`.
  **40 native code origins**, remaining runtime payload, source/build receipts,
  authorization and configuration match. Distinct signed fixture bundles do not
  mean distinct engine candidates.
- **6/6** new qualification controls passed. Earlier corpus/harness/correction/
  execution/ordering controls retain their unchanged scoped evidence; no unrelated
  full test suite or runtime rebuild was repeated.
- Required before/after authorization, observed ARM64 process/images, owned
  cleanup and sentinel survival passed for admitted host runs. Full late-loaded
  image coverage remains incomplete and belongs to #10.
- Governance (25 documents, 238 local targets) and changed-document local links pass; `git diff --check` passes.
  Publication-head remote checks remain unperformed pending final review.

Evidence reuse: native [19-PE reference](https://github.com/postmelee/pear/actions/runs/37729128660)
and [ordering reference](https://github.com/postmelee/pear/actions/runs/37757016708)
are reused by exact PE/source/results identity, not rerun. Stage 3's final engine,
seven boundary runs and ordering run are unchanged. Stage 2's older Pear DLL
results cannot qualify this candidate; the remaining 12 checks were executed on
the final candidate instead. Lower-level comparison records retain broad
`cpu_qualified: false`; only this declared finite aggregate is qualified.

### Retention

The [observations](task_m1_6_stage4_observations.json) name retained task-owned
`.build/task6/` inputs/results; Stage 2/3 reports retain unique failure records.
Successful synthetic prefixes were removed after owned cleanup admission. Keep
#1/#5/#7 dependency worktrees and current signed binaries for #8. No duplicate
Wine/FEX build was created in this stage. About 33 GiB free was observed before
report completion. Private authorization, credentials and raw captures stay out
of Git; source and sanitized summaries are the review artifacts. Hosted native
artifacts have 14-day retention; their exact local copies remain retained.

## Residual Risks

- AVX and i386/WoW64 execution remain unsupported by this qualification. A future
  required game/helper path cannot waive either limitation.
- Finite representative x64 tests and two concurrent workers do not prove the full
  ISA, arbitrary concurrency, every exception/code-change case or all interleavings.
- Steam, translated graphics, Megabonk gameplay, complete late-load observation,
  independent Mac reproduction and ordinary-user distribution are unperformed.
- Correctness instrumentation provides no performance or power comparison.

## Impact on Next Stage

All four planned stages now satisfy their declared criteria. Review the final
report and PR body before publication. #8 must use this exact final FEX candidate
and #7 graphics inputs, revalidating affected evidence after integration. #9/#10
retain supervision/observation responsibilities; #11–#13 retain Steam, gameplay
and runtime assembly responsibilities. Issue #6 remains open until approved
completion or confirmed merge; no master merge has occurred.

## Approval Request

Review [the final report](../report/task_m1_6_report.md) and approve PR publication.
This completes Stage 4 preparation and does not authorize a merge.
