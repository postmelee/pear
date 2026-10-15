# Task #48 Stage 2: Artifact Lifecycle Workflow Integration

GitHub Issue: [#48](https://github.com/postmelee/pear/issues/48)
Implementation plan: [task_m1_48_impl.md](../plans/task_m1_48_impl.md)
Stage: 2
Date: October 11, 2026 (Asia/Seoul)

## Stage Purpose

Connect the approved canonical retention procedure to existing planning, reporting and merge checkpoints. The requester approved continuation after the verified Stage 1 commit `6ef1143`. This stage implements the approved Stage 2 document group only.

Context used: the approved task/implementation plans, root rules, task workflow and canonical manual, [Stage 1 report](task_m1_48_stage1.md), existing three templates and four skill sources. The technical and location context is unchanged from the implementation plan. Reuse Hyper-Waterfall v0.3.0, upstream attribution `83836828a4da24385d0410515d35ee43946b981f`, with Pear baseline `d01f5264cca305649fbf7df488b1dd7badaa5b80`. Apply the revised task-stage-report procedure and unchanged todo format. Apple technical guidance and subsystem language decisions are Not applicable to these operating-document edits.

## Artifacts

| File | Change Summary |
|---|---|
| `mydocs/_templates/task_plan.md` | Artifact Lifecycle table and reuse/copy/peak-space fields |
| `mydocs/_templates/stage_report.md` | Artifact Disposition table with actual outcomes, recovery and accounting limits |
| `mydocs/_templates/final_report.md` | Retention Handoff table and cleanup limitations |
| `mydocs/manual/task_workflow_guide.md` | One canonical-policy checkpoint paragraph |
| `mydocs/skills/task-start/SKILL.md` | Planning field hook, including fallback format |
| `mydocs/skills/task-stage-report/SKILL.md` | Disposition hook, including fallback reports |
| `mydocs/skills/task-final-report/SKILL.md` | Handoff hook, including fallback reports |
| `mydocs/skills/pr-merge-cleanup/SKILL.md` | Pre-removal dependency checks and retained-worktree verification outcome |
| `mydocs/orders/20261011.md` | #48 row records Stage 2 completion and Stage 3 approval pending |
| `mydocs/working/task_m1_48_stage2.md` | This report |

## Body Change Scope / Lossless Preservation

All actual paths match the approved location table. Seven of the eight procedure/template/skill files are additive and preserve every pre-existing line. The merge-cleanup skill changes its worktree-removal instruction and corresponding verification condition so a required worktree can be retained with an explicit owner and release condition. Its remaining procedure, existing commands and approval boundaries are preserved.

The four skills' Trigger, Preconditions and Never Do sections are byte-identical to their pre-stage versions. Workflow approval/verification text remains intact. Root AGENTS.md, its framework notice, the canonical manual and Stage 1 research are byte-identical to HEAD; discovery symlinks remain unchanged. No framework update, additional approval gate, runtime code or new service is introduced.

Pre-edit inspection found no overlap between #10/#11/#46/#47 worktree diffs and this stage's eight procedure/template/skill files. #46 also edits the October 11 board in its own worktree. This stage edits only #48's local row; preserve both rows when integrating. Live reads confirmed #48 and these related tasks remain open. No other task's output or chat state changed.

## Verification Results

Execution context: Python 3.14.4, Git 2.53.0; authenticated gh reads succeeded. These are offline document checks and manual workflow review, with no native execution or cleanup operation.

Evidence reuse: Stage 1's canonical policy and historical receipt assessment at `6ef1143` are unchanged. Their bounded conclusions remain the context; no historical payload or restore result is reported as newly verified. Changed-document governance and link checks were rerun for this stage.

Commands run: the exact Shared Verification Commands block from the implementation plan, extracted and run with `bash -e`: Python/Git versions, existing governance checker, supplemental changed-Markdown and symlink checks, whitespace and diff/status. Additional read-only Python comparisons check preserved skill sections, additive document content, unchanged Stage 1 files and link destinations from generated-document folders.

Pre-report results:

- Governance PASS: 27 documents, 269 local targets; offline routing/inventory consistency.
- Supplemental links PASS: 16 changed Markdown documents and 75 literal local targets across the complete task; four template destinations reviewed separately below.
- Both shared-skill discovery symlinks and `git diff --check` pass.
- Four skills preserve Trigger/Preconditions/Never Do. Seven additive documents preserve all prior lines; the merge-cleanup differences were reviewed explicitly.
- The nine pre-report changed files are the eight approved procedure/template/skill files and #48's board. This report is the tenth final stage file.

Post-report verification passed: 17 changed Markdown documents, 78 literal local targets, four reviewed template destinations, both discovery symlinks, governance and whitespace. The final ten-file stage scope, eight revised report headings and preservation of non-#48 board content also passed.

### Checkpoint and Template Consistency

All four hooks link the same [canonical manual](../manual/artifact_retention_guide.md); detailed cleanup, recovery and APFS policy stays there.

| Skill | Checkpoint | Template field / handoff | Review result |
|---|---|---|---|
| `task-start` | Procedure 5, before plan verification/approval | Task plan: Artifact Lifecycle | Exact field name, compact record, reuse/copy/peak-space decisions and fallback coverage match |
| `task-stage-report` | Procedure 2, before report checks/commit | Stage report: Artifact Disposition | Actual versus deferred outcomes, remaining consumers and recovery references match |
| `task-final-report` | Procedure 2, before final board/commit | Final report: Retention Handoff | Remaining owners, release events, ignored evidence and recovery limitations match |
| `pr-merge-cleanup` | Procedure 5, before worktree removal/archival | Revisit final report: Retention Handoff | Current consumers and ignored evidence checked first; retain dependent worktrees with explicit reason/event |

Each template allows a reasoned Not applicable for material storage on small tasks. The three report/plan skill hooks explicitly preserve the field even when falling back because a central template is unavailable. Merge cleanup recognizes host-managed worktree lifecycle; it does not treat an app/Git snapshot as guaranteed preservation of ignored data. Its verification now accepts documented retention as well as completed removal. No cleanup skill was executed in this stage.

Manual link review: the three templates' existing GitHub Issue destinations contain `{issue}` and resolve to the existing Issue URL shape when filled. The stage-report implementation-plan destination resolves from `mydocs/working/` to `mydocs/plans/` using the milestone/Issue filename; the #48 substitution exists. These are the four counted placeholders. New manual links resolve from both template storage and actual `plans/`, `working/`, `report/` locations. New links have no heading fragments or reference definitions requiring additional parsing. Existing code-fenced workflow examples were unchanged.

Unperformed: native builds/execution, cleanup, archive recovery, physical-space measurement and remote CI. These are not document-check successes. The complete eight-scenario acceptance review remains Stage 3, and automatic enforcement is not claimed.

## Artifact Disposition

| Artifact/root | Actual state and outcome | Remaining owner/consumer | Identity/recovery reference | Retain reason / release condition |
|---|---|---|---|---|
| Stage 2 documents and report | Tracked text outputs; no cleanup | #48; future task workers | Bundled stage commit | Review and ongoing procedure use; retain in Git history |
| Prior maintenance recovery store | External retained dependency; untouched | Prior archived #5/#8 artifacts | Stage 1 research references existing receipts/tools/store | Required for retired originals; not releasable by #48 |
| Current verification output | Summarized command results | #48 review | Commands in approved implementation plan and results here | No separate material scratch store created |

Material storage planning is Not applicable to these small text outputs. No allocated/logical/archive/free-space measurements were performed and no reclaimed-space claim is made. Cleanup is neither completed nor newly authorized by this document integration.

## Residual Risks

- Manual application remains necessary; no automated retention enforcement exists.
- Final integration must preserve the independently edited #46 board row and recheck any new shared-document changes.
- Stage 3 must verify all eight representative scenarios and map every acceptance criterion to the final text.

## Impact on Next Stage

Use the connected templates/skills and unchanged canonical manual for Stage 3's integrated review. Correct only bounded inconsistencies within approved files, revalidate affected documents, and keep historical runtime/storage claims separate from fresh document checks. Publication and final-report work remain after the three stages under the existing procedure.

## Approval Request

Approve Stage 2 artifacts and verification, then proceed to Stage 3 integrated document/scenario verification. This does not approve additional cleanup, native implementation or PR publication.
