# Task #48 Stage 1: Canonical Retention Policy and Evidence Boundaries

GitHub Issue: [#48](https://github.com/postmelee/pear/issues/48)
Implementation plan: [task_m1_48_impl.md](../plans/task_m1_48_impl.md)
Stage: 1
Date: October 11, 2026 (Asia/Seoul)

## Stage Purpose

Define the reusable artifact lifecycle before wiring it into templates and skills. The requester explicitly approved the implementation plan and Stage 1 in this chat. This stage creates operating documentation; it performs no storage cleanup or runtime implementation.

Context used: the approved task/implementation plans, root AGENTS.md, architecture and delivery boundaries, workflow/location/conflict manuals, existing producer reports and dated reuse research referenced by the plan. The baseline is `d01f5264cca305649fbf7df488b1dd7badaa5b80`; planning ends at `1319373`. Hyper-Waterfall v0.3.0 attribution remains commit `83836828a4da24385d0410515d35ee43946b981f`. The existing [stage-report](../skills/task-stage-report/SKILL.md) and [todo](../skills/todo/SKILL.md) procedures were applied; Apple technical guidance is Not applicable to these document-only changes.

## Artifacts

| File | Change Summary |
|---|---|
| `AGENTS.md` | Three concise obligations link the canonical procedure and cover ownership, release, recovery and accounting |
| `mydocs/manual/artifact_retention_guide.md` | Classes/states, planning, retention record, handoffs, bounded cleanup, legacy exception and storage accounting |
| `mydocs/tech/task_m1_48_reuse.md` | Sanitized historical observations, eight local receipt identities, dependency limits and reuse decision |
| `mydocs/orders/20261011.md` | #48 row records Stage 1 completion and pending Stage 2 approval |
| `mydocs/working/task_m1_48_stage1.md` | This report |

## Body Change Scope / Lossless Preservation

All locations match the approved plan. The manual contains generic procedures; issue-specific measurements and consumer examples remain in research. Existing AGENTS.md text, including approvals, qualification/security rules and framework attribution, is byte-preserved after removing the new section for comparison. Both skill discovery symlinks are unchanged. Only #48's daily-board row changes; the October 10 board and all other task artifacts are unchanged in this stage.

Live Issue reads confirmed #48's approved scope and that #10/#11/#46/#47 remain open. Their current worktree changes do not overlap the root policy/manual/research files. #46 has an independent October 11 board: retain its M1 row together with #48's Common Operations row at integration. No other task's files or chat state were changed. API/runtime behavior is Not applicable because no code changed.

## Verification Results

Execution context: Python 3.14.4, Git 2.53.0; gh authenticated reads available. Work is source/receipt and document review in the isolated `codex/task48` worktree. No native SDK, account session or signing permission is required for these checks.

Evidence reuse: the eight SHA-256-identified receipts in the [research note](../tech/task_m1_48_reuse.md) were read and compared. The historical final receipt reports 49 runtime bundles, 25 synthetic prefixes and 31,902 protected hashes; the earlier restore receipt contains 872 file entries. Recorded before/after free-space arithmetic equals 6,625,034,240 bytes. These are receipt consistency checks, not current payload/metadata scans or a new restore. Existing producer qualification is referenced only within its original scope.

Commands run: the exact Shared Verification Commands block from the approved implementation plan, extracted and executed with `bash -e`, including `python3 tools/check_governance.py`, supplemental changed-Markdown/symlink checks, `git diff --check`, full task diff names and current status. The same block is required again after adding this report before the bundled commit. Additional read-only Python checks compare the root's unchanged text and non-#48 board content with HEAD, restrict the stage's paths, and compare the eight receipt digests and recorded counts.

Pre-report results:

- Governance: PASS, 27 documents and 269 local targets; routing and source inventory consistent offline.
- Supplemental links: PASS, seven changed Markdown documents and 54 local targets across planning plus this stage; zero template-placeholder targets.
- Both discovery symlinks resolve to `mydocs/skills`; whitespace passes.
- Four pre-report files match the approved Stage 1 scope; the stage report is the fifth final file.
- All eight local receipt identities and the selected recorded counts match; existing root rules and non-#48 board content are preserved.

Post-report verification also passed: eight changed Markdown documents, 58 local targets, both discovery symlinks, governance and whitespace. The final five-file Stage 1 scope and all seven required report headings were verified.

Manual policy review:

| Requirement | Supporting manual section | Reviewed result |
|---|---|---|
| Classes, current use and byte availability | Artifact Classes and States | Seven classes and seven states distinguish active, retained, historical, cold, disposable, unavailable and released outcomes |
| Exact reuse and required fresh reconstruction | Planning Before Substantial Creation | Input-bound reuse; relevant changes revalidate; required fresh checks remain |
| Owner, consumer, identity and release event | Minimum Retention Record | Compact table includes path/inode/signing needs, recovery and explicit uncertainty |
| Peak space and necessary full copies | Planning Before Substantial Creation | Creation/archive/restore overlap considered; full-copy reason required without breaking isolation |
| Stage/final/worktree dependencies | Checkpoints and Handoff | Ignored evidence and downstream consumers checked before removal; Git/app snapshot alone insufficient |
| Bounded cleanup and protected state | Bounded Cleanup Procedure | Explicit candidates, transitive/process checks, protected identities and post-change verification |
| Failed or incomplete recovery | Bounded Cleanup Procedure; Legacy Cold-Storage Exception | Retain intact originals on failure; mark already retired unrecoverable bytes unavailable; protect surviving recovery data |
| Narrow inode-bound exception | Legacy Cold-Storage Exception | Explicit scope and actual restore required; changed metadata disclosed; placeholders not executable/available inputs |
| APFS and concurrent work | Storage Accounting | Four quantities separated; no summed-size recovery promise or double counting |
| Scope, privacy and approvals | Purpose and Authority; Bounded Cleanup Procedure | Existing approvals/security retained; no extra gate for authorized cleanup; private data excluded from publication |

The new documents use simple literal file links without heading-fragment or reference-definition dependencies. Their text was reviewed for privacy and scope: no raw private diagnostics, authentication, game payloads, local user-home paths or recovery archives are copied into repository outputs. The full eight-scenario and template/skill consistency review remains Stage 3/Stage 2 work respectively, not a Stage 1 passing claim.

Unperformed: native builds/execution, game/Steam qualification, archive restoration, protected-runtime rescanning, further cleanup and remote CI. They are outside this stage; historical receipts do not substitute for those operations.

## Artifact Disposition

| Artifact | State and owner | Retention / release |
|---|---|---|
| Stage documents and report | Tracked #48 output | Preserve in Git for review and future procedure use |
| Prior maintenance store and receipts | External retained recovery dependency | Preserve in primary checkout while retired originals depend on it; not releasable by #48 |
| Current verification output | Compact command output summarized here | No separate large output store or runtime copy created |

Material creation/restore peak-space planning is Not applicable to these small text-only outputs. No storage reclaimed amount is claimed for Stage 1.

## Residual Risks

- Policy is a documented obligation; automatic enforcement is not implemented.
- Historical archive receipts do not establish present recoverability of every original artifact. Future restoration/cleanup needs current checks.
- Stage 2 must connect the canonical procedure to templates and skills without duplicating rules or altering approval boundaries.
- The shared October 11 board needs row-preserving integration with #46; no cross-worktree edits were made.

## Impact on Next Stage

Use the canonical manual as the single source for Stage 2's compact plan/disposition/handoff fields and four skill hooks. Preserve root rules, source notices, discovery links and required verification. No policy or storage-system scope expansion is needed. Keep #11 execution and #46/#47 work independent.

## Approval Request

Approve Stage 1 artifacts and verification, then proceed to Stage 2 workflow/template/skill integration. Further artifact deletion, runtime changes, publication and merge are not included.
