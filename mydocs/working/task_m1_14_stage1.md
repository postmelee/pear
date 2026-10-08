# Task #14 Stage 1: Verification reuse evidence and CI readiness

GitHub Issue: [#14](https://github.com/postmelee/pear/issues/14)
Implementation plan: [task_m1_14_impl.md](../plans/task_m1_14_impl.md)
Stage: 1 — bounded preparation complete; Issue #14 remains incomplete.

## Stage Purpose

Preserve the approved Melee/Handbook research and prevent duplicate work without modifying active runtime integration. Prepare an explicit CI candidate inventory rather than enabling unqualified suites.

Context used: [task plan](../plans/task_m1_14.md), root rules, existing task/implementation/stage/tech templates, source-inspected runtime contracts and latest #5/#7 checkpoints. Applied task-start, todo format and task-stage-report procedures. No new code or Metal implementation required a technical skill.

## Artifacts

| File | Change Summary |
|---|---|
| AGENTS.md | Two rules on active-work discovery and evidence reuse; link to dated non-normative research |
| mydocs/tech/20261004_recompilation_and_verification_reuse.md | External/local evidence, reuse judgments, current blockers, explicit CI candidates and unperformed checks |
| mydocs/_templates/task_plan.md | Existing producer/checker, supported claim, false-success and invalidation prompts |
| mydocs/_templates/task_impl_plan.md | Distinguish reused evidence from current execution and preserve required checks |
| mydocs/_templates/stage_report.md | Attribute reused results without presenting them as newly run |
| Task plans and daily board | Bounded approval, document locations and later-stage boundaries |

## Body Change Scope / Lossless Preservation

All locations match the accepted proposal and task plan. Existing template sections, skill interfaces, framework attribution, CLAUDE routing and discovery symlinks remain intact. Reviewed consuming skills and template index; no new artifact type or skill was introduced. Only two root bullets and one prompt per existing template were added. Product documentation, workflows, runtime/tools/tests, source pins, other worktrees and untracked analysis/research were not modified.

## Verification Results

Execution context: Python 3.14.4, Darwin arm64, isolated codex/task14 worktree based on master d35428f037a91b5db1a22fb0b065d6d13132ccb7. This is source/document inspection, not runtime or Linux execution.

Evidence reuse: #4 merged report and #5/#7 pinned plans/reports retain their original scopes; this task did not rerun their tests. Current #7 link results do not qualify a fresh build or changed native candidate. The actual existing #14 Issue was queried and allows preparatory work before acceptance dependencies finish.

Commands run:

```bash
python3 -B tools/check_governance.py
git diff --check
```

Results:

- Governance: PASS, 22 documents, 173 local targets; offline routing/source inventory consistent.
- Existing link parser initially checked 4 documents/26 targets; final check including this report passed 5 documents/28 local targets.
- Whitespace: passed. Manual diff review confirms planned document-only boundaries.
- Independent read-only review of the CI inventory and rule/template changes found no material defect; no code was executed by that reviewer.
- New test code was unnecessary for reversible prose changes; no runtime regression suite was invoked.

Limits: governance is not a full Markdown parser or a remote-link/agent-behavior verifier. Linux candidate commands, dependencies, CI runs, builds and gameplay were not executed. The storage sidechat is ephemeral and unsupported by the read-thread API; no completion or build authorization was inferred from it.

## Coordination and External Advice

The requester explicitly clarified that messages should deliver useful external research. Source-linked advice was sent to the existing runtime conversation (which also manages #5) and native-restoration conversation. Topics include Melee's original-object fallback guard, synthetic-versus-runtime proof, FEX/DXMT reuse, immutable checkpoints, and the limits of PPC recompilation as a Windows/Unity analogue.

The runtime owner confirmed relevant practices already exist and identified same-candidate Wine patch/ABI verification, checkpoint clarity and later CI portability as useful follow-ups. Existing storage priority and stage gates remain unchanged. The native-restoration message was delivered; no independent technical adoption response is claimed. No new build or research stage was requested.

## Residual Risks

- Proposed Linux suites remain unqualified; contract wheel/marker and private-path assumptions need later work.
- #5/#7 continue independently; recorded commits are dated observations, not current completion guarantees.
- Rules are committed on this branch and are not effective in master until reviewed integration.
- Daily-board rows from concurrent branches must be preserved during eventual integration.

## Impact on Next Stage

Refine Stage 2 around master-only synthetic verification tests on clean Linux, with explicit dependency and failure/skip behavior, before any workflow change. Keep #14's later runtime/promotion dependencies. This report does not recommend a new CPU translator or a second verification framework.

## Approval Boundary

Stage 1 completes the currently approved preparation. Stage 2 and full #14 completion remain unapproved and unperformed. A later explicit continuation must identify the concrete experiment/CI scope; no next stage is started automatically.
