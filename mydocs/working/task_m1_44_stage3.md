# Task #44 Stage 3: Investment decision and minimum experiment proposal

GitHub Issue: [#44](https://github.com/postmelee/pear/issues/44)
Implementation plan: [task_m1_44_impl.md](../plans/task_m1_44_impl.md)
Stage: 3
Date: October 10, 2026 (Asia/Seoul)
Authorization: Explicit requester continuation after Stage 2 commit `2833306`; research/proposal only.

## Stage Purpose

Turn the completed route and source comparison into a reviewable investment decision, conditional minimum experiments and a seven-criterion research acceptance map. Preserve #11's independent execution work and the separate approval required for any implementation, native experiment or bridge route.

Context used: [task plan](../plans/task_m1_44.md), implementation plan, [Stage 2 report](task_m1_44_stage2.md), live #44/#11/#10 Issues, applicable root/runtime/host/test rules, README/official index/architecture/delivery plan, original #6/#8/#40 evidence boundaries, task workflow, central technical-note/stage-report templates and the [stage-report](../skills/task-stage-report/SKILL.md)/[todo](../skills/todo/SKILL.md) procedures. No Metal diagnostics or graphics change applies. No final-report/publication skill is invoked because this stage only prepares its evidence mapping.

## Artifacts

| File | Change Summary |
|---|---|
| [Research note](../tech/task_m1_44_reuse.md) | Final research decision, dated peer context, E0-E6 conditional proposals, exact shared preimages/owners, affected regressions and all seven acceptance criteria. |
| [Stage 3 observations](task_m1_44_stage3_observations.json) | 23 input identities, three Issue snapshots, seven proposal records and acceptance records, availability checks/unknowns, evidence invalidation and verification identities. |
| [Task plan](../plans/task_m1_44.md), [implementation plan](../plans/task_m1_44_impl.md) | Stage 3 authorization/completion, decision handoff and remaining approval boundaries. |
| [Daily board](../orders/20261010.md) | Only #44 updated; research stages reported, final-report/publication review pending. |
| This report | Verification, remaining risks and separate continuation request. |

## Body Change Scope / Lossless Preservation

All six paths match the approved task-document locations. Existing Stage 1/2 observations and reports are byte-identical to committed inputs. The research note adds Stage 3 findings and updates its current decision/status wording; previous evidence remains dated. Other board rows remain unchanged. No official architecture/roadmap, source, test, build tool, source lock or peer worktree is modified.

No new public source acquisition was needed. Stage 2 source conclusions and its 176-source/105-anchor verification are reused through unchanged committed reports/ledgers; those checks were not redundantly repeated. New local Issue snapshots and verification records are ignored under `.build/task44/`. Peer reads are limited to named sanitized reports/observations, not private input discovery. The native lock and account/game/prefix state are untouched.

The final-report acceptance mapping is prepared in the note and observations. The later `_report.md`/publication procedure does not start automatically under Stage 3 authorization, as specified by the implementation plan. No Issue checkbox, closure, remote branch or PR is changed.

## Verification Results

Execution context: Python 3.14.4, Git 2.53.0 and the existing GitHub CLI; macOS ARM64 task worktree. Read-only source/report/Issue inspection plus JSON, governance, hash, link and scope checks. The filesystem check observed 17,643,073,536 available bytes at intake, not a native-build capacity estimate. Native toolchain/dependency readiness, future per-executable authorization and independent i386 reference availability were not checked; no compiler, native fixture or guest ran.

Commands run from the task worktree:

```sh
python3 -B -m json.tool mydocs/working/task_m1_44_stage3_observations.json > /dev/null
python3 -B tools/check_governance.py
git diff --check
git diff --name-only
```

Result:

- All four planned checks passed. Governance output: `PASS: 27 documents, 268 local targets; skill routing and source inventory consistent (offline)`.
- All **23 input SHA-256/size comparisons** and **three retained Issue-snapshot hashes** passed. Committed inputs match Git HEAD. Prior Stage 1/2 artifacts and unrelated board rows remain unchanged.
- All **seven Issue acceptance criteria** map to research evidence with explicit runtime limits. All **seven E0-E6 proposal records** contain claim, prerequisite/input, command/interface availability, positive/refusal outcomes, resource bounds, cleanup, retention and decision. All are marked proposed/not performed with separate approval required.
- Before report creation, **37 existing local links** passed; two links to this report were pending. The post-report pass resolves all local links without a pending-file allowance, verifies report headings and checks the exact six-file scope. Staged whitespace is checked before the bundled commit.
- Manual review confirms source hypothesis, build, host feasibility, guest execution, actual owned-game Steamworks and distribution are separate claims. No low-memory, installer, callback, menu, SDK-slice or downloader result is promoted to whole-route support.
- Retained command/check outputs: `.build/task44/stage3-verification1/{pre-report,post-report}-commands.json` and matching `-checks.json`; reader hash is recorded in the observations. Intake reader and Issue snapshots are retained under `.build/task44/stage3-intake1/`. These ignored local records are not claimed to be published.

Newly consumed #11 context: sanitized direct-stall receipt `9303466d8b248abda52d025bc3cd0be520a1f0003176d6093a5e805d453d9ee5`, which itself records no new game execution. It reports two retained direct-game timeouts without the Dock source guard, source attribution to `LookupCache::AddL1Entry`, and missing fault/commit/progress observations. #44 did not recheck binaries or diagnose their cause. The latest available #10 Stage 2 report still excludes complete module/runtime coverage. Both are dated owner evidence, not an accepted new integration interface.

No runtime suite was run for unchanged documentation. No bridge build, low-address allocation, PE32 parser execution, i386 reference/guest, proprietary installer/helper, real session, original-game run, signing, debugger, native lock operation or distribution check occurred.

## Residual Risks

- The selected i386 service is identified statically, but its actual game-route necessity and the complete helper set remain unknown. A required unsupported helper must block its affected phase if demonstrated.
- Existing bridge entry rewrites mapped Valve images and relies on patched ntdll. A compatible entry, full original-game API/callback/session behavior, build closure and required Rosetta-free host closure are unresolved. Source reuse does not establish lower cost or feasibility.
- Low-address host feasibility, PE32/fixed-base admission, i386 context/exception/re-entry/invalidation/retirement and final-candidate regressions are unperformed. A diagnostic 64 MiB bound is not measured Steam capacity.
- #11's x64 startup issue and #10's complete process/module integration remain their owners' work. Future accepted changes invalidate affected preimages and evidence; no live peer source is adopted here.

## Impact on Next Stage

The research recommends preserving #11's independent work and requesting no broad WoW64 or bridge implementation now. E0 is the nearest useful owner evidence. If an exact required i386 helper is demonstrated, prefer separately reviewed targeted Wine/FEX reuse; E1 is the smallest new host diagnostic, followed only after further approval by E2 parser/loader, E3 i386 lifecycle and E4 actual-helper gates. E5 bridge reconsideration requires a compatible entry design; E6 desktop support is an independent investment.

The seven-criterion mapping is ready for the final-report/publication procedure. Final research review/publication is distinct from approving any E0-E6 execution or implementation. Preserve accepted #40 -> separately reviewed overlapping #11 correction if applicable -> separately approved #44 correction, exact source preimages, original #6/#8/#40 regressions, #10 observer ownership and #42 ISA/XSTATE scope.

## Approval Request

Review the completed three-stage research and approve proceeding to the **final report and research-document PR publication procedure**. This continuation would not authorize runtime/WoW64/bridge implementation, native experiments, account operations, merge or Issue closure.
