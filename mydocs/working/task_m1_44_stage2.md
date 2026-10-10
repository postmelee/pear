# Task #44 Stage 2: WoW64 and native Steam bridge source comparison

GitHub Issue: [#44](https://github.com/postmelee/pear/issues/44)
Implementation plan: [task_m1_44_impl.md](../plans/task_m1_44_impl.md)
Stage: 2
Date: October 10, 2026 (Asia/Seoul)
Authorization: Explicit requester continuation after Stage 1 commit `79986eb`; read-only source research only.

## Stage Purpose

Compare reusable Wine/FEX i386 contracts and the existing macOS Steam bridge before any substantial loader/memory/ABI investment recommendation. Preserve the distinction between actually required Dock helpers and full Windows bootstrap/desktop support. #11's minimum Dock run and direct-game startup diagnosis continue independently.

Context used: the approved [task plan](../plans/task_m1_44.md), implementation plan and [Stage 1 report](task_m1_44_stage1.md); root/runtime/FEX rules; official requirements and workflow context already recorded in the plan; the [stage-report skill](../skills/task-stage-report/SKILL.md) and central template. No Metal work or native experiment applies. Repository `codex/task44` naming overrides the framework's example branch prefix.

## Artifacts

| File | Change Summary |
|---|---|
| [Research note](../tech/task_m1_44_reuse.md) | Adds function/refusal matrix; API and callback traces; genuine-session limits; bridge entry incompatibility; build/architecture/terms comparison and unresolved scope differences. |
| [Stage 2 observations](task_m1_44_stage2_observations.json) | 61 new source identities, 105 symbol/literal anchor records, retained input binding, complete inspected refusal groups, five bridge criteria, dependency pins, counterexamples and unknowns. |
| [Task plan](../plans/task_m1_44.md), [implementation plan](../plans/task_m1_44_impl.md) | Records Stage 2 continuation/completion and carries source findings into the next decision boundary. |
| [Daily board](../orders/20261010.md) | Updates only #44; Stage 3 awaits continuation. |
| This report | Stage verification, limitations and next-stage approval request. |

The inspected bridge provides a concrete native `BIsSubscribedApp` call/return and callback conversion example. It does not establish the original game's interface coverage or session. Its current entry patches ntdll and overwrites mapped Valve client exports/entry/data; therefore unchanged adoption conflicts with the approved no-Valve-binary-rewriting scope. Generated wrappers and conversions remain separable reuse candidates. No alternative entry design is implemented or approved.

Existing Wine/FEX functions cover many i386 mechanisms, but the composed Pear owner-mode WoW64 entry, context, exception, memory notification and teardown paths retain explicit refusals. ARM64EC lifetime/invalidation ordering offers reusable semantics, not a complete i386 adapter. Neither finding establishes that broad WoW64 is necessary for every Megabonk route.

## Body Change Scope / Lossless Preservation

All six tracked paths match the approved `mydocs/` locations. Stage 1 findings and observations remain historical evidence; new Stage 2 sections extend the note and update only current scope/deferred-status wording. Stage 1 observation bytes match Git HEAD. Other daily-board rows are unchanged. No runtime, host, test, tool, source-lock, official document, workflow manual or peer file changes occur.

New ignored snapshots contain targeted public sources and reader/tree metadata only. The snapshot checkpoint uses 11,687,940 bytes under the 64 MiB limit, with files below 8 MiB. Later small inspection/verification records do not add source payloads. No game payload, account state, prefix, credential, signing material or private diagnostics enter tracked artifacts. The native compilation lock is untouched.

## Verification Results

Execution context: Python 3.14.4, Git 2.53.0, GitHub CLI 2.89.0; macOS ARM64 task worktree. Standard-library source hashing/JSON and offline governance/document checks only. Downloaded scripts, fixture producers, retained parser binaries, compilers and guests were not executed.

Evidence reuse: all 115 Stage 1 source snapshots were rechecked. The historical parser refusal, selected #11 component/no-account receipts and #40 startup result retain their earlier claim scope, without replay. Nine selected composed FEX files match the recorded #8 source manifest; three Wine files match Stage 1. Four accepted #40 patch/metadata files match Git HEAD and preserve patch preimages/order separately from older composed Wine sources. No unchanged-input claim depends on a mismatching digest.

Commands run from the task worktree:

```sh
python3 -B -m json.tool mydocs/working/task_m1_44_stage2_observations.json > /dev/null
python3 -B tools/check_governance.py
git diff --check
git diff --name-only
```

Result:

- All four planned checks passed. Governance output: `PASS: 27 documents, 268 local targets; skill routing and source inventory consistent (offline)`.
- Targeted acquisition: 26 NotProton and 19 pinned Proton files, 6,116,736 source bytes. Saved SHA-256, immutable-tree size and Git blob checks passed for all 45. This does not verify the full declared 3,133-file Proton baseline digest or dependency/build closure.
- The stage verification reader rechecked **176 source hashes** (61 new plus 115 retained), **105 source anchor records**, unchanged Stage 1 JSON, #44-only scope and preservation of other board rows. No source mismatch occurred.
- Before report creation, 28 existing local links passed and the two plan links to this report were explicitly pending. The post-report run checks all existing local links with no pending-file allowance, template headings and the complete six-file scope.
- Manual review traced the representative ownership call, payload conversion and return path, ordinary callback polling/release, asynchronous call results, session setup/shutdown and failure fallthrough. Callback 513's checked table uses **12 Unix bytes to 16 Windows bytes**, with separately defined old layouts. Game endpoints, nested/concurrent callback behavior and Rosetta-free closure remain unknown/unperformed.
- The first anchor assembly failed because `FEX_GUEST32BASE` was not a literal in Madeira's design note. Source inspection corrected the note to guest-window / `CONFIG_GUEST32BASE` terminology and anchored the actual module plus design text. The failed attempt and corrected reader hashes are retained. No expected source digest was altered.
- Retained local command/check outputs: `.build/task44/stage2-verification1/{pre-report,post-report}-commands.json` and matching `-checks.json`. The source snapshot ledger and method files are under `.build/task44/source-review/stage2-pear1/`. The tracked observations carry source/method hashes and the failed/corrected anchor check; ignored files are not represented as published artifacts.

No runtime tests are appropriate for unchanged source. No native build, memory probe, guest execution, Steam/game launch, sign-in, SDK regeneration, signing, debugging or distribution qualification was performed. Document checks do not replace those missing results.

## Residual Risks

- Actual necessity of the selected i386 Steam service and any other game prerequisite remains unknown. The current x64 failure before later phases cannot eliminate future helper requirements.
- Original Megabonk's actual Steamworks interfaces, callbacks/call results, ownership, account/App ID and session continuity remain unobserved by #44.
- Existing NotProton entry is incompatible with the current scope; a compatible entry is an unresolved design requirement. Its global callback buffer, fallback layouts and result-failure cleanup require review before reuse. No runtime defect reproduction is claimed.
- Complete required native Steam/bridge/Wine/FEX/helper/library architecture coverage, including late-loaded modules, remains unperformed. Source ARM64 options and a native launcher are insufficient.
- Full source-build reproducibility, dependency/file-specific distribution terms and update cost are not established by targeted acquisition. WoW64 low-address/fixed-base, context, exception, mutation and retirement contracts remain unqualified.

## Impact on Next Stage

Stage 3 can now make an evidence-based investment decision and specify the smallest missing experiments, including refusal controls, required i386 execution categories and affected #6/#8/#40 regressions. It must distinguish a source hypothesis, build, host feasibility, guest execution and owned-game qualification; no experiment runs in that stage.

Preserve the integration order: accepted #40 changes, any separately reviewed overlapping #11 correction, then separately approved #44 work. Recheck #10's accepted observer interfaces when available; #42 retains ISA/XSTATE ownership. Do not take over #11's x64 LookupCache/overcommit/resume diagnosis or create a new bridge prerequisite for its minimum execution.

## Approval Request

Approve these Stage 2 artifacts and continue to **Stage 3 only: investment decision and minimum experiment proposal**. Runtime/WoW64/bridge implementation, native experiments, PR publication and Issue closure remain outside this continuation.
