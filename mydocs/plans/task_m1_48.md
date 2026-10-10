# Task #48 Plan: Reusable artifact retention and storage cleanup rules

GitHub Issue: [#48](https://github.com/postmelee/pear/issues/48)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

## Purpose

Define a reusable internal artifact lifecycle for all Pear tasks. Before material builds or runs, workers should identify reusable inputs, planned outputs, consumers and release conditions. Stage and merge handoffs should leave the smallest sufficient evidence and recoverable dependencies without accumulating unexplained full runtime copies.

This is documentation and workflow work. It does not implement automatic deletion or change runtime execution, qualification or ownership rules.

## Background

The requester approved Issue registration and its scope/locations on October 10, 2026, then explicitly approved task-start in this chat. Issue #48 is OPEN with the documentation label. This plan starts from master `d01f5264cca305649fbf7df488b1dd7badaa5b80` in the separate `codex/task48` worktree. No #48 implementation plan or stage report exists yet.

Context explicitly reviewed during registration/planning:

- [Repository rules](../../AGENTS.md), [README](../../README.md), [official index](../../docs/README.md), [architecture](../../docs/architecture.md) and [delivery plan](../../docs/delivery-plan.md). In particular, immutable runtime inputs and private mutable state have separate responsibilities.
- [Task workflow](../manual/task_workflow_guide.md), [Git workflow](../manual/git_workflow_guide.md), [document structure](../manual/document_structure_guide.md) and [rule precedence](../manual/agent_code_hyperfall_rule_conflict.md).
- [Task-start](../skills/task-start/SKILL.md), [daily board](../skills/todo/SKILL.md), task-register and the stage/final/merge skills and central templates identified below.
- Completed producer reports for [#5](../report/task_m1_5_report.md), [#6](../report/task_m1_6_report.md), [#7](../report/task_m1_7_report.md), [#8](../report/task_m1_8_report.md) and [#40](../report/task_m1_40_report.md), plus their existing local retention/handoff records.
- The [dated verification-reuse investigation](../tech/20261004_recompilation_and_verification_reuse.md), which is supporting evidence rather than a new normative rule.

The October 10 maintenance archived 49 historical runtime bundles and 25 terminated synthetic prefixes. It verified 31,902 protected file hashes and an actual in-place restore of 872 files. The observed free-space increase was approximately 6.17 GiB, including Git temporary-file removal, while concurrent work continued. These are historical local maintenance observations, not fresh verification or a general physical-saving guarantee.

A subsequent read-only survey found approximately 94.39 GiB displayed for #5 and 36.28 GiB for #8. #5 includes 24 prefix templates displaying 39.41 GiB, and build/tool/component-labelled directories displaying 24.39 GiB. Template control records refer to source cases and parent templates; downstream records reference final Wine/FEX and graphics inputs. Name groups and literal references do not prove byte equality, complete dependency closure or safe deletion.

Local evidence remains in the primary checkout's ignored `.build/storage-maintenance/20261010-completed-tasks/`, including `final-verification.json`, the protected/restore receipts, and `followup-survey/`. The content store and cold-archive receipts are recovery dependencies, not #48 scratch data. Preserve them in place; do not copy them into this worktree or publish them.

### Existing work and integration boundaries

Open #10 and #11 own observer/game execution work; #46 and #47 own Steam comparison and the Rosetta preview. #14 covers regression CI and does not duplicate this internal retention policy. #44 remains completed research. Existing #1/#5/#6/#7/#8/#40 retained inputs remain untouched.

Current worktree inspection found active host/observer and Steam-input changes, plus task-specific plans and boards. None requires edits to the proposed #48 rule files. The shared daily board is a known integration dependency: add only #48's row and preserve other task rows during later integration. Recheck overlapping files before implementation and publication; do not message other tasks without requester authorization.

## Scope

### Included

- One canonical internal retention/cleanup manual and a concise AGENTS.md entrypoint.
- Compact lifecycle fields in task-plan, stage-report and final-report templates.
- Minimal workflow and task-start/stage/final/merge skill hooks linking the canonical policy.
- Artifact classes, states, ownership, consumers, input identities, peak-space considerations, release conditions and recovery requirements.
- Immutable-input reuse, disposable per-run state, unique failure evidence and APFS-aware accounting.
- A narrow legacy exception for in-place byte retirement where retained evidence binds file identity; explicit restore-required status and recovery-store protection.
- Dated, sanitized reuse of the existing residual survey and cleanup evidence. Record findings in task research/reports, not event-specific manual sections.

### Excluded

- Runtime/loader/memory/ABI, code-generation or producer implementation changes; new automatic cleanup/cache services or scheduled work.
- Further deletion/archive of residual #5/#8 artifacts, active worktree changes or changes to other tasks' implementation plans.
- Game, credential, authenticated-prefix, save or private-signing deletion/upload; committing local private receipts or binary archives.
- Framework version updates, unrelated manual fixes, new milestone/label definitions, fixed universal retention periods or new M1 qualification gates.
- New native execution/builds, modified required checks or claims that the new policy is automatically enforced.

## Design Direction

- Use the approved registration draft as an input, refining it against the source files and scenarios rather than treating an ignored draft as an applied rule.
- Keep immutable inputs, disposable build/run state, qualification evidence, private user state and recovery archives distinct. Require a recorded reason for a full per-run runtime copy, not a blanket prohibition that breaks isolation or signing.
- Use event-based release conditions. A closed producer Issue does not terminate downstream dependencies, and lack of an open file handle alone does not establish disposability.
- Keep a compact retention table with artifact/root, class/state, owner/consumer, identity/recovery needs, retain reason and release condition. Material tasks also record peak-space uncertainty; small documentation-only tasks may state reasoned Not applicable.
- Preserve necessary fresh reconstruction and evidence invalidation rules. Reuse unchanged checks within their recorded scope, without rerunning native matrices solely for retention documentation.
- Default to an intact retained artifact or deletion of proven disposable data. Do not standardize zero-byte placeholders. Legacy cold storage must be recoverable and visibly unavailable until restored.
- Prefer ordinary deletion, a verified recovery archive or retention based on the actual dependency/identity requirements. Do not mandate hard-linking, moving, compression or a new artifact store implementation.
- Keep all detailed rules in the new manual. Skills contain procedural checks and links; templates contain output fields. Preserve existing approval boundaries and avoid introducing redundant approval requests for already authorized cleanup.
- Reuse Hyper-Waterfall v0.3.0's existing English manuals/templates/skills and preserve attribution. No upstream subsystem code import or language rewrite is involved. Apple Metal guidance is not applicable to this document-only work.

## Document Location Judgment

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| Agent obligation summary | Mandatory agent entrypoint | All Pear agents | `AGENTS.md` | Full policy in AGENTS.md | Keep the entrypoint short and link one canonical procedure |
| Artifact lifecycle procedure | Internal operating manual | Task workers | `mydocs/manual/artifact_retention_guide.md` | `docs/` | Internal repeated work procedure, not a product/public integration contract |
| Workflow checkpoint links | Internal operating manual | Task workers | `mydocs/manual/task_workflow_guide.md` | Duplicate lifecycle manual | Add minimal links without repeating the policy |
| Lifecycle output fields | Central templates | Task workers | `mydocs/_templates/task_plan.md`, `stage_report.md`, `final_report.md` | New per-run report template | Extend existing outputs; no parallel reporting system |
| Lifecycle procedure hooks | Shared agent skills | Codex/Claude workers | Existing four `mydocs/skills/` sources | Copies under discovery directories | Preserve the source of truth and symlinks |
| Dated survey/reuse assessment | Task research | Reviewers/future workers | `mydocs/tech/task_m1_48_reuse.md` | Event details in the manual | Keep the manual neutral and long-lived |
| Plans, stages and report | Task artifacts | Requester/reviewers | Existing `mydocs/plans/`, `working/`, `report/` | Official `docs/` | Preserve Issue-scoped workflow separation |

The registration approved the proposed locations. This plan presents their detailed scope for plan approval before editing rule documents. No official product, user, contributor, architecture or roadmap document is changed.

## Expected Changed Files

New:

- `mydocs/manual/artifact_retention_guide.md`
- `mydocs/tech/task_m1_48_reuse.md`

Modified:

- `AGENTS.md`
- `mydocs/manual/task_workflow_guide.md`
- `mydocs/_templates/task_plan.md`
- `mydocs/_templates/stage_report.md`
- `mydocs/_templates/final_report.md`
- `mydocs/skills/task-start/SKILL.md`
- `mydocs/skills/task-stage-report/SKILL.md`
- `mydocs/skills/task-final-report/SKILL.md`
- `mydocs/skills/pr-merge-cleanup/SKILL.md`

Task artifacts:

- `mydocs/orders/20261010.md` (#48 row only; use later actual dates if needed)
- `mydocs/plans/task_m1_48.md`
- `mydocs/plans/task_m1_48_impl.md` after task-plan approval
- `mydocs/working/task_m1_48_stage{N}.md`
- `mydocs/report/task_m1_48_report.md`

## Artifact Lifecycle for This Task

| Artifact/root | Class/state | Owner/consumer | Identity and recovery needs | Retain reason | Release condition |
|---|---|---|---|---|---|
| Plans/rules/research/reports | Tracked task output | #48 and future workers | Git commits; no private payload | Reviewable policy and decisions | Preserve in repository history |
| Existing primary-checkout maintenance records/content store | External retained dependency | Prior cleanup; archived #5/#8 artifacts | Exact receipts and recovery bytes; original-path/inode bindings | Required restoration, independent of #48 | Not releasable by this task |
| Optional `.build/task48/` checks | Disposable local output | #48 review | Small text/JSON output, reproducible commands | Stage/PR verification review | After results are committed and no reviewer needs raw output |

No runtime copy, source checkout, toolchain build or large binary is needed. Planned additional verification text is below 1 MiB; this is an estimate, not a quota or native build preflight. Reuse existing survey data without a second whole-worktree scan. Do not duplicate the prior archive or hash inventories merely to create this plan.

## Tentative Stages

- **Stage 1 — Canonical policy and evidence boundaries**
  - Add the neutral internal manual, concise AGENTS.md entrypoint and sanitized reuse assessment.
  - Review scope, source/evidence/privacy boundaries and the document locations.
- **Stage 2 — Workflow, templates and skill integration**
  - Add compact planning/disposition/handoff fields and small procedural links.
  - Check template/skill consistency and preserve existing stage/approval behavior.
- **Stage 3 — Integrated document verification and final report**
  - Review representative scenarios against the complete policy and all acceptance criteria.
  - Verify links, governance, attribution, symlinks and final change scope; prepare the final report through the applicable approved procedure.

Each stage is verified, reported and committed before requesting continuation. This task-start does not begin Stage 1.

## Verification Plan

Observed tools at planning: Python 3.14.4, Git 2.53.0 and authenticated gh reads. `tools/check_governance.py` and the existing documentation workflow are available. No native runtime toolchain is needed. The exact stage commands and output locations will be recorded in the implementation plan after this plan is approved.

### Stage Verification

- Stage 1: inspect rule neutrality, defined lifecycle states, preservation/recovery criteria and excluded implementation scope; run existing `python3 tools/check_governance.py`; check new local links and `git diff --check`.
- Stage 2: inspect each existing template/skill call path against the canonical manual, including reasoned Not applicable for small tasks. Check all changed local links, discovery symlinks and `git diff --check`.
- Stage 3: record outcomes for unchanged-build reuse, required fresh reconstruction, active consumer after merge, unique failure, APFS clone, corrupt/missing archive, authenticated private state and a small documentation task. These are document scenario reviews, not runtime tests.

### Integrated Verification

- Map every Issue acceptance criterion to the final text or scenario result.
- Run the existing governance checker, changed-document link checks and `git diff --check`; do not create implementation-mirroring tests for prose.
- Verify only the approved rule/template/skill files and #48 task artifacts changed; other board rows, framework attribution, private files, runtime code and discovery symlinks are preserved.
- No automatic enforcement, native execution or new storage-recovery result is claimed. Historical maintenance evidence is reused with its exact dated limits.
- Verify a clean task worktree before publication. Remote CI is a publication-time result, not an assumed planning pass.

## Risks

- **Over-retention:** release conditions must identify the consumer event that ends retention; avoid indefinite unexplained retention.
- **Premature cleanup:** a reference search or Issue merge is not proof of complete dependency closure. Protect shared/private inputs and describe unknowns explicitly.
- **Misleading capacity claims:** keep displayed sizes, compressed sizes and observed free space separate; note concurrent activity and APFS sharing.
- **Legacy cold storage:** visible paths can have unavailable bytes. Keep restore-required markers and their recovery store discoverable, without making this layout the default.
- **Policy duplication/ceremony:** one canonical procedure, concise hooks and reasoned Not applicable for small work.
- **Concurrent documentation:** recheck overlapping edits before stages/publication and integrate only #48's board row. Existing authorization permits read-only inspection, not messaging other chats or changing their state.

## Approval Request

Approve the proposed document-only scope, exact locations, lifecycle direction, tentative three stages and verification boundaries. After approval, `task_m1_48_impl.md` will define the stage artifacts, commands and commits. No additional artifact deletion or runtime implementation is included.
