# Task #44 Final Report: Steam route requirements and reuse investment

GitHub Issue: [#44](https://github.com/postmelee/pear/issues/44)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Date: October 10, 2026 (Asia/Seoul)
Status: All three read-only research stages complete. The requester approved final-report preparation and research-document PR publication after Stage 3 commit `ecabcfa`. Implementation, experiments, merge and Issue closure are not authorized by that continuation.

## Work Summary

- Target Issue: #44
- Milestone: M1
- Stage count: 3
- Work purpose: distinguish actually required Dock i386 helpers from complete Windows Steam bootstrap/desktop support, compare existing Wine/FEX and native Steam bridge reuse, and make a bounded investment/experiment recommendation.

The Windows installer is i386, and the selected Valve service is also statically i386. The available observations do not demonstrate that the latter is required on the selected Megabonk route. Unknown necessity is not evidence of absence. #11 continues its independently owned Dock/game validation and x64 startup diagnosis; this research adds no bridge or broad desktop prerequisite.

Pinned NotProton/Proton source contains real native ownership-method forwarding and callback-layout conversion. Its inspected entry patches ntdll and rewrites mapped Valve client exports, entry and data, conflicting with the current no-Valve-binary-rewriting scope. Wrapper/conversion source remains reusable material, but original-game interface/session coverage, compatible entry, complete Rosetta-free host closure and full build/maintenance cost remain unresolved. macOS Steam existence establishes neither easier implementation nor working integration.

**Investment decision:** do not start broad WoW64 or adopt that bridge from current evidence. If #11 demonstrates an actually required unsupported i386 helper, prefer separately reviewed targeted Wine C/FEX C++/assembly reuse. E0 consumes owner evidence; E1 is the smallest conditional new low-address NX diagnostic; E2-E4 preserve the later PE32/loader, i386 lifecycle and actual-helper gates. E5 reconsiders bridging only after a compatible entry review; E6 treats full desktop support independently. Every experiment remains proposed, not performed.

## Changed Files and Impact Area

| Path | Change Summary | Impact Area |
|---|---|---|
| [task plan](../plans/task_m1_44.md), [implementation plan](../plans/task_m1_44_impl.md) | Scope, approved stages, reuse/locations, verification and publication authorization | Task governance |
| [research note](../tech/task_m1_44_reuse.md) | Route matrix, function/refusal and bridge comparison, conditional experiments, owner/preimage and acceptance maps | Non-normative engineering research |
| [Stage 1](../working/task_m1_44_stage1.md), [Stage 2](../working/task_m1_44_stage2.md), [Stage 3](../working/task_m1_44_stage3.md) and matching observation JSON | Input-bound findings, actual checks and limitations | Research evidence |
| [daily board](../orders/20261010.md) | #44 marked Done for completed research; PR review/merge remain separate | Task status only |
| This report | Full research acceptance and final review handoff | Long-term task record |

No source, tests, build configuration, official guide, workflow, runtime binary or account/game state changes. The branch contains 11 task-document files relative to master. Other tasks' board rows and all prior stage evidence are preserved.

## Document Location Verification

Product/user/API/architecture/roadmap documentation changes: **Not applicable**. This task records dated research and unadopted proposals; it does not amend official support claims or runtime requirements.

| File | Planned Location | Actual Location | Result | Evidence |
|---|---|---|---|---|
| Plans | `mydocs/plans/` | `mydocs/plans/task_m1_44{,_impl}.md` | OK | Approved task-plan location judgment |
| Research | `mydocs/tech/` | `mydocs/tech/task_m1_44_reuse.md` | OK | Approved non-normative decision/evidence scope |
| Stage evidence | `mydocs/working/` | Stage 1-3 reports and observation JSON | OK | Committed stage artifacts |
| Final report | `mydocs/report/` | `mydocs/report/task_m1_44_report.md` | OK | Planned final-report destination |
| Daily status | `mydocs/orders/` | `mydocs/orders/20261010.md` | OK | #44 row only |

## Quantitative Before/After Comparison

These are research coverage counts, not runtime performance or qualification metrics.

| Metric | Before task | After research |
|---|---|---|
| Consolidated #44 source comparison | No #44 ledger | 115 retained public sources plus 61 Stage 2 source identities; 105 Stage 2 anchor records |
| Route/bridge decision coverage | Related retained findings, no consolidated decision | Two Windows route scopes and five explicit bridge criteria |
| Concrete conditional proposals | Unapproved broad design context | Seven E0-E6 records, each with input/prerequisite, positive/refusal outcomes, resources, cleanup and retention |
| Research acceptance mapping | Seven open criteria | Seven mapped as satisfied within research scope, with runtime unknowns retained |
| Runtime experiments or implementation by #44 | None | None |

## Verification Results

“OK” below means the research criterion is met. It does not mean a proposed runtime or game path passed.

| Acceptance Criterion | Result |
|---|---|
| AC1 — Separate Dock/helper and bootstrap/desktop requirements | OK — Stage 1 phase/input/status matrix; actual i386 helper necessity remains unknown. |
| AC2 — Limited existing bridge comparison before broad changes | OK — Stage 2 all five criteria, representative real API/callback path and explicit existing-entry incompatibility. |
| AC3 — Reusable functions and missing contracts | OK — Wine/FEX matrix covers PE32/fixed-base, low-address, syscall/context/thread/exception, notification and retirement; unsupported guards preserved. |
| AC4 — Pins, terms, owners and invalidation | OK — Exact ledgers, file-specific notices, accepted #40 preimages/order, #11/#10/#42 boundaries and evidence invalidation policy. |
| AC5 — Concrete minimum experiments | OK — E0-E6 specify known/missing inputs, interface availability, success/refusal, authority, resource bounds and cleanup. No experiment ran. |
| AC6 — Precise #11 impact | OK — No universally required i386 helper demonstrated; no new bridge/desktop gate. Any demonstrated required unsupported helper blocks its affected phase. |
| AC7 — Reviewable investment/continuation decision | OK — Conditional targeted Wine/FEX reuse; defer existing bridge adoption; independently scope desktop. Implementation remains separately approved. |

### Stage Verification Results

- [Stage 1](../working/task_m1_44_stage1.md), commit `79986eb`: 131 expected SHA-256 comparisons with zero mismatches; retained parser output comparison and selected component/receipt checks. Preserved initial reader error and correction. Historical parser/host results were not rerun.
- [Stage 2](../working/task_m1_44_stage2.md), commit `2833306`: 45 targeted acquired files verified against immutable Git blobs, size and SHA-256; nine composed FEX, three Wine and four integrated patch files checked. Final reader checked 176 source hashes, 105 anchors and 39 local links. Preserved incorrect initial Madeira literal and corrected source reference.
- [Stage 3](../working/task_m1_44_stage3.md), commit `ecabcfa`: 23 inputs, three Issue snapshots, seven proposal/acceptance records and 49 local links passed; Stage 1/2 artifacts and other board rows remained unchanged. Complete source-wide checks were reused rather than repeated.

### Integrated Publication Verification

Before this report, the Stage 3 planned commands and scoped reader passed again against the committed final stage, including the 23 inputs/three snapshots and 49 links. Stage 1/2 JSON serialization also passed. Python 3.14.4 and Git 2.53.0 were used on the ARM64 macOS worktree. Offline governance output: `PASS: 27 documents, 268 local targets; skill routing and source inventory consistent (offline)`.

Final document checks passed for all three JSON records, report-template sections, 77 local links, the 11-file branch scope, six unchanged earlier reports/observations and the #44-only daily-board change. Staged whitespace is checked before the final commit. Retained publication outputs belong to ignored `.build/task44/final-verification1/`. Local evidence snapshots are not claimed to be public or self-contained native reproduction inputs.

A fresh fetch confirmed `origin/master` remains `942bd816913d8792c55f821fdc2ad309b1b85daf`, an ancestor of this branch; no conflict recovery or rebase was needed. No existing `codex/publish-task44` PR was found before publication. The PR uses the repository template and commit-pinned report links. Remote CI results will be reported in the PR after publication; no future check is represented as a pass in this report.

Native execution, compilation, signing, parser replay, bridge construction, account operations, game/Steam launch and runtime regression suites were unperformed in this documentation-only task. The existing documentation/portable CI does not qualify those behaviors.

## Residual Risks and Follow-up Work

### Residual Risks

- Actual helper necessity and complete required process/module coverage are unresolved. Installed-file architecture alone cannot establish either requirement or absence.
- Original-game API/callback/session behavior and complete required Rosetta-free native closure remain unqualified for the bridge. Its current entry cannot be adopted unchanged within scope.
- PE32/fixed-base/low-owner and i386 execution/lifetime contracts remain unimplemented or explicitly refused. A proposed 64 MiB diagnostic is not measured Steam capacity.
- #11 owns direct-game x64 diagnosis; #10 owns observer/module completion; #42 owns AVX/XSTATE. Later accepted changes require exact preimage and affected-evidence revalidation, preserving #6/#8/#40 regression obligations.
- Targeted source/notice review is not full dependency-build reproducibility or distribution clearance. No precise bridge-versus-WoW64 cost estimate is justified.

### Follow-up Candidates

- If a required i386 helper is demonstrated, register/review only the corresponding targeted Wine/FEX correction and selected E1-E4 evidence plan. Do not create implementation approval from this research PR.
- A scope-compatible bridge entry and E5 evaluation remain conditional, separately approved alternatives.
- Full Windows Steam bootstrap/desktop support (E6) needs its own investment decision. #11/#10/#42 already track their existing scopes; no duplicate Issue is created here.

## Approval Request to Task Requester

Final-report preparation and research-document PR publication were explicitly approved after Stage 3. Review the resulting Open PR for merge separately. Publication does not authorize E0-E6 execution, runtime/bridge implementation, account operations, self-merge or immediate Issue closure.
