# Task #48 Stage 3: Integrated Retention Verification

GitHub Issue: [#48](https://github.com/postmelee/pear/issues/48)
Implementation plan: [task_m1_48_impl.md](../plans/task_m1_48_impl.md)
Stage: 3
Date: October 11, 2026 (Asia/Seoul)

## Stage Purpose

Verify the complete retention procedure through eight representative document scenarios and every Issue acceptance criterion. The requester approved Stage 3 after the Stage 2 report and commit `926c542`. No policy correction was needed; this stage records the integrated review and updates #48's board row.

Context used: approved task/implementation plans, root rules, canonical manual, three revised templates, task workflow, four revised skills and the [Stage 2 report](task_m1_48_stage2.md). Apply task-stage-report and the existing todo format. Hyper-Waterfall v0.3.0 attribution remains upstream commit `83836828a4da24385d0410515d35ee43946b981f`; the full-task comparison base is Pear `d01f5264cca305649fbf7df488b1dd7badaa5b80`. Apple tooling, native execution and subsystem implementation guidance are Not applicable to this document review.

## Artifacts

| File | Change Summary |
|---|---|
| `mydocs/working/task_m1_48_stage3.md` | Eight reviewed scenarios, acceptance mapping, full-task preservation and verification results |
| `mydocs/orders/20261011.md` | #48 row records three verified stages and pending final reporting/publication |

## Body Change Scope / Lossless Preservation

Both paths match the approved implementation plan. The manual, root obligations, templates and skills at `926c542` remain unchanged in this stage. The full diff against `d01f526` was reviewed: one canonical manual, one short root section, three template fields, four skill hooks, one workflow paragraph, sanitized research and #48 plans/reports/board rows. It contains no runtime code, private payload, recovery archive or unrelated task artifact.

Read-only comparisons verify that removing the new root section reproduces the baseline AGENTS.md exactly, including its security rules and framework notice. All four skills preserve the baseline Trigger, Preconditions and Never Do sections. Stage 2's additive content preservation and narrowly changed merge-cleanup verification remain valid because those files are unchanged. Both discovery symlinks still resolve to the shared source. Existing October 10 board content is intact; only #48 occurs in this worktree's October 11 board.

Current #10/#11/#46/#47 branch/worktree diffs still have no overlap with the policy/manual/template/skill file set. #46's independent October 11 board remains an integration dependency: preserve its row on publication integration. No other worktree or chat was changed. #48 remains OPEN; final reporting, publication, merge and Issue closure are not performed in this stage.

## Verification Results

Execution context: Python 3.14.4, Git 2.53.0; authenticated gh Issue reads succeeded. Fresh checks are offline document and source-diff verification. No platform-specific SDK, signing authorization or Steam session is needed.

Evidence reuse: Stage 1 receipt consistency results and historical limits at `6ef1143` are reused through the unchanged [research note](../tech/task_m1_48_reuse.md). Stage 2's template/skill matrix at `926c542` is reviewed against the unchanged files. This stage does not rehash original runtime payloads or repeat the earlier recovery test. Historical measurements remain dated and do not imply additional reclaimed space.

Commands run: the approved Shared Verification Commands block, extracted from the implementation plan and executed with `bash -e`. It includes the existing governance checker, supplemental changed-Markdown/symlink checks, `git diff --check`, full-task diff names and status. Additional read-only Python comparisons check the full-task allowlist, root text, four skill approval boundaries and board preservation; current worktree diffs are compared with the same rule-file set.

Pre-report results:

- Governance PASS: 27 documents, 269 local targets; offline routing and inventory consistency.
- Supplemental links PASS: 17 changed Markdown documents, 78 literal local targets, both discovery symlinks; four template destinations separately reviewed.
- Whitespace PASS. All 17 existing task paths match the approved allowlist before adding this report.
- Root original text/attribution, four skills' approval boundaries and other board content are preserved.
- No current policy-file overlap with the four inspected active task worktrees.

Post-report verification passed: 18 changed Markdown documents and 82 literal local targets across the full task, four manually reviewed template destinations, both skill discovery symlinks, governance and whitespace. Stage 3 itself changes only the report and #48 board row; all eight scenario outcomes and eight required report headings are present.

The four template destinations are three GitHub Issue URLs parameterized by `{issue}` and the stage report's implementation-plan path parameterized by milestone/Issue. #48 substitution resolves from the actual report folder; the new manual links resolve both in template storage and in the generated plans/working/report folders. All newly added links use literal file destinations without heading fragments or reference definitions. The existing Markdown parser's broader limitations remain; no comprehensive Markdown-renderer claim is made.

### Eight Document Scenarios

These are explicit hypothetical decision reviews against the [canonical manual](../manual/artifact_retention_guide.md) and connected templates/skills, not filesystem operations or automated runtime tests. The section names below refer to the manual unless a template/skill is named.

| ID | Given situation and reviewed path | Observed policy decision | Result and supporting sections |
|---|---|---|---|
| S1 | A later run has the same source, patches, tools, configuration and admitted immutable input; only its output directory differs. Follow planning into the lifecycle table. | Reuse the compatible input and valid scoped evidence; isolate mutable output. A full copy needs a concrete reason and release event. A changed relevant input would invalidate this reuse decision. | PASS — Planning Before Substantial Creation; Minimum Retention Record; task-plan Artifact Lifecycle |
| S2 | A valid cached build exists, but the approved task requires a fresh reconstruction. Apply the reuse rule to that requirement. | Perform the required fresh reconstruction and its checks. Reuse does not waive the gate; budget overlapping outputs and retain their comparison evidence until its release event. | PASS — Planning Before Substantial Creation, steps 1-2; task-plan Verification Plan remains intact |
| S3 | A producer PR is merged, but another task still consumes exact original paths/identities in ignored output. Follow final handoff into merge cleanup. | Keep the dependency and worktree when bindings require them, with owner and release event. Removal requires verified preservation or consumer migration; a Git/app snapshot or merged Issue alone is insufficient. | PASS — Checkpoints and Handoff; final-report Retention Handoff; pr-merge-cleanup procedure 5 and retained-worktree verification |
| S4 | A failed run leaves disposable scratch state mixed with unique original failure inputs/logs. Follow after-run and stage disposition checks. | Secure the smallest sufficient failure/replay set and private state before classifying scratch as disposable. Preserve failed-attempt records; report completed versus deferred cleanup separately. | PASS — Artifact Classes and States; Checkpoints and Handoff; Bounded Cleanup Procedure, steps 3 and 6; stage-report Artifact Disposition |
| S5 | Directory totals suggest large savings, but clones share APFS extents and another worker is writing. Follow accounting into the stage report. | Separate logical, allocated/displayed, archive and filesystem free-space observations. Do not sum nested totals or claim exclusive savings from the net delta; state concurrent activity and uncertainty. | PASS — Storage Accounting; stage-report Storage observations field |
| S6 | An archive is corrupt/missing, or a restore cannot preserve required identity bindings. Apply the archival and legacy-exception branches. | Retain intact originals before retirement. For originals already retired, mark bytes unavailable, preserve surviving recovery material and record the unresolved recovery path. Do not admit empty placeholders; archive listing/compression success is insufficient. | PASS — Bounded Cleanup Procedure, step 5; Legacy Cold-Storage Exception; report state/recovery fields |
| S7 | A prefix contains authenticated Steam state, games or saves, while a task authorizes only synthetic-state cleanup. Follow class, authority and cleanup checks. | Keep private state separate and outside Git/releases; task completion or synthetic cleanup does not authorize its deletion. Publish only sanitized summaries and appropriate identities. | PASS — Purpose and Authority; Artifact Classes and States; Minimum Retention Record; Bounded Cleanup Procedure |
| S8 | A documentation task generates only tracked text and small reproducible check output. Follow the plan and report hooks, including fallback formats. | Use a compact Git-backed record and reasoned Not applicable for material storage/peak space. No large manifest, full-runtime copy or per-command inventory is required. Existing review/approval gates remain. | PASS — Purpose and Authority; all three template fields; task-start/stage/final fallback hooks |

All eight reviews reached an explicit decision without a contradictory instruction in the connected workflow. No correction or expanded scope was required.

### Issue Acceptance Mapping

| Acceptance criterion from Issue #48 | Final text and evidence | Result |
|---|---|---|
| Single canonical internal lifecycle and narrow exception handling | Manual Artifact Classes and States, Bounded Cleanup Procedure, Legacy Cold-Storage Exception; root and hooks link that one source; S6 | PASS |
| Plans include roots, reuse/peak space, owners/consumers, identities and release conditions; small-task exception | Task-plan Artifact Lifecycle table and copy/space fields; task-start procedure 5; S1/S2/S8 | PASS |
| Stage/final reports distinguish disposition and expose restoration dependencies | Stage-report Artifact Disposition and final-report Retention Handoff; S3/S4/S6 | PASS |
| Worktree cleanup handles ignored evidence and downstream consumers first | Manual Checkpoints and Handoff; pr-merge-cleanup procedure 5 and verification; S3 | PASS |
| Full runtime copy is not the default; necessary copies have reasons and release triggers | Manual Planning Before Substantial Creation; task-plan reuse/copy field and lifecycle table; S1/S2 | PASS |
| APFS/concurrent activity accounted for without physical-saving promises | Manual Storage Accounting; stage-report storage observations; dated research explicitly limits prior figures; S5 | PASS |
| Existing evidence/security/approval rules intact without duplicating policy in each skill | Baseline comparisons and reviewed diff; short hooks and one canonical manual; S2/S7/S8 | PASS |
| Representative scenarios and documentation/link/governance checks pass | S1-S8 above, shared verification results and post-report check | PASS |

Unperformed and outside this stage: native builds, game/Steam execution, fresh protected-file scans, archive restore, further artifact cleanup, storage measurement, PR/CI execution and cross-task migration. This report establishes reviewed operating documents on the task branch, not automatic enforcement or qualified runtime behavior.

## Artifact Disposition

| Artifact/root | Actual state and outcome | Remaining owner/consumer | Identity/recovery reference | Retain reason / release condition |
|---|---|---|---|---|
| #48 rules/templates/skills/research/plans/reports | Tracked text; retained | #48 review and future workers | Task commits and report links | Preserve in Git history; final report/publication still pending |
| Prior primary-checkout maintenance store | External retained dependency; untouched | Retired #5/#8 originals | Existing receipt/tool/content-store references in Stage 1 research | Not releasable by #48; original recovery remains dependent on it |
| Stage 3 command output | Summarized in this report | #48 review | Approved commands and current results | No separate material output store created |

Material peak-space and storage observations are Not applicable to this small document review; no new free-space measurement or recovery claim is made. No artifact removal/archival occurred.

## Residual Risks

- Compliance depends on workers applying the rules; no automatic cleanup or admission enforcement is implemented.
- Historical receipts cannot establish present recoverability of every archived artifact. Later operations require current scope/input checks.
- Publication must reconcile the shared daily board and revalidate affected evidence if integration changes files. Remote CI is still unperformed.

## Impact on Next Stage

All three planned implementation stages are verified locally. Next is the final report and publication procedure, using these acceptance/scenario results and the exact final integrated revision. Preserve stage commits, use `codex/publish-task48` to `master`, and carry forward remaining recovery dependencies. Final reporting/publication retains the approval boundary in the implementation plan; merge/Issue closure is separate.

## Approval Request

Approve Stage 3 verification and continue to final reporting and PR preparation/publication under the existing procedure. No further cleanup or runtime work is included.
