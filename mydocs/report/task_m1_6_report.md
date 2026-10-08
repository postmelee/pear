# Task #6 Final Report — CPU Semantics and the Wine Translation Boundary

GitHub Issue: [#6](https://github.com/postmelee/pear/issues/6)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Status: all four stages complete locally; final report and PR publication review pending.

## Work Summary

- Target Issue: #6; prerequisite #5 completed by merged PR #37.
- Milestone: M1; stage count: **4**.
- Purpose: qualify declared x64 CPU/Windows boundaries and actual multi-worker
  ordering on the ARM64 Wine/FEX path against independent native Windows results.
- Result: **18 cases passed, AVX explicitly unsupported, zero required failures**;
  **32,768 ordering pairs per host**, zero forbidden outcomes and eight checked
  worker retirements. The final engine is consistently bound across both suites.
  Megabonk execution is not yet qualified.

## Changed Files and Impact Area

| Path | Change summary | Impact area |
|---|---|---|
| `tests/cpu/` | Source-bound manifest, upstream notices, C/ASM fixtures and focused refusal controls | Defined finite CPU and Windows contracts |
| `tools/cpu/` | Source adaptation, exact-PE generation, native/Pear execution, existing-signing reuse and strict comparison | Reproducible qualification without a new runtime |
| `runtime/fex/patches/cpu/` | Four separately identified patches: private staging label storage, policy observation, link diagnostics and shared-target correction | Required translator fixes and actual per-thread evidence |
| `.github/workflows/cpu-native-reference.yml` | Approved branch-only native x64 reference with pinned tools, bounded execution and LF source preservation | Independent same-PE oracle |
| `docs/development/fex-host.md` | Reproduction and finite-coverage handoff in the existing guide | Contributor integration guidance |
| `mydocs/plans/`, `working/`, `report/`, `orders/` | Approved decisions, stage results, sanitized identities and completion | Review and audit trail |

Pinned FEX C++/ASM, Wine C and Madeira's Python/C fixture design were reused.
FEX's selected ASM remains MIT; adapted optional Madeira fixture tooling retains
its GPL-3.0-or-later notices and stays separate from runtime patches. No Rust
rewrite, new engine, blanket project license change or upstream submission.

Two required translator failures were fixed without a new owner ABI. Private NX
staging now uses upstream dynamic label-reference storage beyond the earlier
fixed limit; direct owner emission remains fixed and fail-closed. Cross-thread
linking now reads the authoritative shared target under existing synchronization
and rejects optional publication from a changed source epoch. Memory permissions,
owner admission and signing protections remain intact.

## Document Location Verification

| File | Planned location | Actual location | Result | Evidence |
|---|---|---|---|---|
| CPU reproduction/coverage | Existing `docs/development/fex-host.md` | Same | OK | Approved task-plan location judgment; historical #5 section retained |
| Task evidence | `mydocs/plans/`, `working/`, `report/`, `orders/` | Same | OK | Four stage reports, sanitized observations, final report and board |

No other official guide was moved or added. Upstream selection did not change
from the approved reuse direction; exact revisions/adaptations live with fixture
metadata and the stage reports rather than a duplicate research page.

## Quantitative Before/After Comparison

| Metric | Before (#5) | After (#6 final candidate) |
|---|---|---|
| Declared independent same-PE comparison | Unperformed | 19 native passes; 18 Pear passes and one unsupported AVX case |
| Upstream ASM selection | No declared #6 corpus | 12 of 2,270 source files selected; 2,258 explicitly excluded |
| Actual two-worker ordering | Unperformed | Four modes, 2,048 iterations, four rounds: 32,768 pairs per host |
| Worker retirement evidence in ordering run | Unperformed | Eight joined workers with checked FEX destruction/free |
| Cross-suite component identity | Not applicable | 40 Mach-O code origins plus PE payload/receipts/configuration bound |
| Stage 4 rebuilds | Not applicable | Zero; 12 affected instruction runs, seven same-candidate boundary results reused |

These counts describe finite correctness coverage, not speed or game support.

## Verification Results

| Acceptance criterion | Result |
|---|---|
| Declared fixture suite passes or explicitly records unsupported coverage; no required failure waived | **OK** — 18 passes, AVX not exposed; i386/WoW64 explicitly unsupported. Final suite retains strict defined register/flag/memory/fault outcomes and complete records |
| Ordering/multithread stress uses actual per-thread policy | **OK** — observed FEX Context scalar/vector/memcpy software TSO for nine participant lifetimes; 32,768 pairs on each host, zero forbidden outcomes, eight checked retirements; hardware TSO not claimed |
| Failures reduced to reproducible fixtures with the responsible boundary identified | **OK** — ABI PE exposed private staging label limit; ordering PE exposed stale shared-target/source-epoch link transactions. Corrected same-PE runs pass. Fixture address collision, source newline and native progress failures remain separately documented |
| Prerequisite #5 and final integration | **OK** — merged #5 receipts retained; final FEX build/payload, Wine code origins, authorization and settings re-admitted across both fixture bundles |

Final FEX DLL SHA-256:
`2925abaafea4d4c3293c30e778629208b507d9690e7d2b128e9b500733608364`.
The [Stage 4 observations](../working/task_m1_6_stage4_observations.json) contain
full corpus, build, reference, bundle and case hashes. Final aggregate `passed`
is true for `declared_x64_cpu_qualification`; `game_qualified` is false.

Host execution: Apple M4 Pro, macOS 26.5.2 (25F84), Python 3.14.4 and authorized
hardened development signing. Native references: Windows Server 2022 x64,
Python 3.12.10, exact downloaded PEs; LLVM-MinGW 20260908 / Clang 23.1.1 and
NASM 3.02. Actual host/image identities are recorded per reference, not inferred
from a runner label. Each admitted Pear run verifies authorization, observed
ARM64 execution, bounded owned cleanup and unrelated sentinel survival.

### Stage Verification Results

- [Stage 1](../working/task_m1_6_stage1.md): source/license/config contract and
  14 manifest controls; 12 ASM selections plus ten declared boundary contracts.
- [Stage 2](../working/task_m1_6_stage2.md): native/Pear 19-case comparison,
  14 harness, four correction and four execution controls; actual 256-label
  fixups and retained direct-owner refusal. That stage's DLL is historical.
- [Stage 3](../working/task_m1_6_stage3.md): corrected ordering on both hosts,
  nine ordering controls and seven final-candidate boundary regressions.
- [Stage 4](../working/task_m1_6_stage4.md): remaining 12 final-candidate cases,
  complete fresh evidence admission, matching component sets, six new aggregate
  controls, governance/local-link verification and clean diff checks.

Native reference runs [37729128660](https://github.com/postmelee/pear/actions/runs/37729128660)
and [37757016708](https://github.com/postmelee/pear/actions/runs/37757016708)
are reused by exact source/PE/results hashes. Their completion does not establish
CI success on the final unpublished commit. Stage 4 did not rerun unchanged guest
ordering or rebuild Wine/FEX. Full raw evidence is retained locally and private;
source and sanitized observations are the publication artifacts.

## Residual Risks and Follow-up Work

### Residual Risks

- AVX and i386/WoW64 execution are unsupported by this qualification; a required
  Steam/game path using them still blocks that later milestone.
- Finite x64 selection, up to three concurrent participants and zero observed
  forbidden outcomes do not prove arbitrary programs, concurrency or all schedules.
- Full late-loaded host-image coverage, Steam, translated graphics, gameplay,
  independent Mac reproduction and ordinary-user distribution remain unperformed.
- Development authorization is not distribution permission. Fresh checkout alone
  lacks private signing/preparation receipts. Keep retained dependency worktrees
  until downstream consumers migrate and verify their inputs.
- Original failures remain failures in retained records. Fixed scratch-address
  adaptation preserves register expectations and adds the original disp32 LEA
  check; it does not qualify access to the originally occupied Wine arena page.
- Instrumented timings are not performance/power evidence. No thermal benefit claimed.

### Follow-up Candidates

Use existing Issues rather than creating duplicates: **#8** translated graphics
integration with this exact FEX and #7; **#9** production supervision; **#10** full
process/module evidence; **#11** Steam and required helper architecture; **#12**
Megabonk gameplay/save/relaunch; **#13** runtime assembly/reproduction. Revalidate
only evidence affected by integration while preserving all required checks.

## Approval Request to Task Requester

Approve this final report and acceptance-criteria verification to publish the
prepared Open PR to `master`. No final PR, master merge or Issue closure has been
performed. The approved early reference-branch publication remains distinct from
final-report approval; merge review follows publication.
