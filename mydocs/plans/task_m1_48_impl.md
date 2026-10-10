# Task #48 Implementation Plan: Artifact retention and storage cleanup rules

Task plan: [task_m1_48.md](task_m1_48.md)
GitHub Issue: [#48](https://github.com/postmelee/pear/issues/48)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

## Approval and Context

The requester approved the task plan and implementation-plan preparation in this chat on October 11, 2026. The approved task plan is committed at `2620a7b`; the integration baseline is `d01f5264cca305649fbf7df488b1dd7badaa5b80`. This document requests approval before Stage 1. No stage has started and no stage report exists.

Apply the specifications, root rules, reuse rationale, exclusions and document locations in the task plan. The architecture's immutable runtime/private mutable state separation is the relevant technical requirement. Read the existing content before each edit. There are no additional scoped AGENTS.md files under the affected `mydocs/` paths. No native host, test fixture or official `docs/` edits are planned.

Reuse the installed Hyper-Waterfall v0.3.0 manuals, templates and shared skills, attributed to upstream commit `83836828a4da24385d0410515d35ee43946b981f`; their Pear source baseline for this task is `d01f526`. The implementation-plan template is `mydocs/_templates/task_impl_plan.md`. Stage completion uses [task-stage-report](../skills/task-stage-report/SKILL.md); publication later uses [task-final-report](../skills/task-final-report/SKILL.md), and daily boards use [todo](../skills/todo/SKILL.md). Read the actual revised skill before applying it. These are procedure references, not approval to publish or clean up now. Apple technical guidance and subsystem language selection are Not applicable because this work changes operating documents only.

An October 11 live read confirms #48 is OPEN with the approved body and milestone. #10/#11/#46/#47 remain open. Inspection of their current branch/worktree changes against the integration baseline found no overlap with the approved rule/template/skill files. Daily boards remain shared integration surfaces; preserve other task rows. #11 has substantial in-progress diagnostics; its older stage report is not authority to revert its current approved direction. #46's latest available Stage 2 report leaves native execution unadmitted; #47 has uncommitted preview preparation. None is an implementation dependency for this policy. Recheck relevant overlaps before edits and publication without changing or messaging other tasks.

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Canonical policy and evidence boundaries | Internal manual, concise agent entrypoint, sanitized reuse assessment | Policy review, dated-source comparison, governance and links |
| 2 | Workflow, templates and skills | Three template fields, workflow links, four skill hooks | Checkpoint matrix, preservation of approvals, links and symlinks |
| 3 | Integrated document verification | Eight scenario results and acceptance mapping in the stage report | Complete diff, all acceptance criteria, attribution and scope |

Each stage ends with verification, a bundled artifact/report commit and an explicit continuation request. After Stage 3, the final report and publication follow the existing approval procedure; approval of this implementation plan does not authorize PR publication, merge or additional storage cleanup.

## Document Location Check

| File | Planned Location in Task Plan | Stage Artifact Path | Match | Notes |
|---|---|---|---|---|
| Agent entrypoint | `AGENTS.md` | `AGENTS.md` | OK | Stage 1; short obligations and canonical link |
| Canonical procedure | `mydocs/manual/artifact_retention_guide.md` | Same | OK | Stage 1; internal procedure |
| Dated reuse evidence | `mydocs/tech/task_m1_48_reuse.md` | Same | OK | Stage 1; sanitized historical observations |
| Workflow checkpoints | `mydocs/manual/task_workflow_guide.md` | Same | OK | Stage 2; minimal links |
| Planning field | `mydocs/_templates/task_plan.md` | Same | OK | Stage 2 |
| Stage disposition field | `mydocs/_templates/stage_report.md` | Same | OK | Stage 2 |
| Final handoff field | `mydocs/_templates/final_report.md` | Same | OK | Stage 2 |
| Four skill hooks | `mydocs/skills/{task-start,task-stage-report,task-final-report,pr-merge-cleanup}/SKILL.md` | Same | OK | Stage 2; source files, no discovery copies |
| Implementation plan | `mydocs/plans/task_m1_48_impl.md` | Same | OK | Current planning artifact |
| Stage reports | `mydocs/working/task_m1_48_stage{N}.md` | Same | OK | One per stage |
| Daily board | `mydocs/orders/{yyyymmdd}.md` | `mydocs/orders/20261011.md`, later actual dates as needed | OK | Only #48; October 10 history preserved |
| Final report | `mydocs/report/task_m1_48_report.md` | Same | OK | After all stages, through approved reporting/publication procedure |

No new product-document destination or location change is proposed.

## Evidence Reuse and Storage

| Reused input and identity | Supported claim and existing check | False-success case / revalidation trigger |
|---|---|---|
| October 10 local maintenance `final-verification.json`, protected receipts and `restore-roundtrip.json`, under primary-checkout `.build/storage-maintenance/20261010-completed-tasks/` | Historical 49 runtime / 25 synthetic-prefix archives, 31,902 protected hashes and 872-file restore; compare summary with existing receipts | Old receipts do not prove present availability or a new restore. Altered inputs, archives or restoration claims require fresh checks in separately authorized work |
| Same root's `followup-survey/` inventory and reference summary, including the approved policy proposal | Historical residual categories and dependency uncertainty; inspect already collected summaries | Names/reference counts do not prove disposability. Current deletion would require fresh dependency/process/identity checks and separate scope |
| Repository reuse investigation and producer reports linked by the approved plan, at `d01f526` | Existing qualification, reconstruction and retained-consumer boundaries | A build or historical success is not fresh execution; changed source/toolchain/settings/artifacts invalidate affected evidence |
| Existing governance checker at the integration baseline | Local routing and Apple inventory consistency; run anew for edited documents | Its default document set omits most internal manuals/templates. Run the supplemental changed-document check below; inspect anchors/template substitutions manually |

Record actual source receipt names and sanitized findings in Stage 1 research. Do not copy archives, private inventories or large logs into Git. There is no fresh native, game, storage reclamation or restore claim in this task.

Tracked documents and reports are the outputs. Optional `.build/task48/` text verification output is reproducible and expected below 1 MiB; it may be released after required results are committed and no reviewer needs it. No material build/restore peak-space plan applies to this documentation-only execution. Prior recovery archives, receipts and original-path bindings are external retained dependencies and cannot be released by #48. No filesystem-wide rescan or extra full-runtime copy is needed.

## Shared Verification Commands

Run from the #48 worktree with Python 3 and Git. Planning availability: Python 3.14.4, Git 2.53.0 and gh 2.89.0; authenticated GitHub reads succeeded. These checks are offline and require no native SDK, signing permission, Steam session or platform-specific build. Record the actual versions when executing each stage. Remote CI remains unperformed until publication.

Run this block for each stage before its report, then again after writing the report. Keep concise outputs in the stage report; optional raw text belongs only in `.build/task48/`. The supplemental check reuses the existing Markdown parser without changing source or adding a test suite. It covers changed tracked and new Markdown files. Template placeholders are counted and reviewed manually because they are not literal file destinations. Parser limitations include heading anchors, reference-use resolution and complex Markdown; inspect those explicitly in review.

```bash
python3 --version
git --version
python3 tools/check_governance.py
python3 -B - <<'PY'
import runpy
import subprocess
from pathlib import Path

root = Path.cwd().resolve()
module = runpy.run_path('tools/check_governance.py', run_name='task48_link_review')
check = module['GovernanceCheck'](root)
base = 'd01f5264cca305649fbf7df488b1dd7badaa5b80'
changed = subprocess.check_output(['git', 'diff', '--name-only', base], text=True).splitlines()
new = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
paths = sorted({Path(p) for p in changed + new if p.endswith('.md')})
placeholders = 0
for source in paths:
    text = check.read(source)
    if text is None:
        continue
    for target, line in module['link_targets'](text):
        if '{' in target or '}' in target:
            assert source.parts[:2] == ('mydocs', '_templates'), (source, target)
            placeholders += 1
            continue
        check.local_target(source, target, line)
assert not check.errors, '\n'.join(check.errors)
print(f'PASS: {len(paths)} changed Markdown documents; {check.local_links} local targets; {placeholders} template targets require manual review')
for name in ('.agents/skills', '.claude/skills'):
    path = root / name
    assert path.is_symlink() and path.resolve() == root / 'mydocs/skills', name
print('PASS: both skill discovery symlinks preserved')
PY
git diff --check
git diff --name-status d01f5264cca305649fbf7df488b1dd7badaa5b80
git status --short
```

Expected: commands succeed; all literal local targets exist inside the repository; both discovery symlinks still resolve to the shared source; no whitespace errors; only approved files and #48 artifacts differ. Compare displayed scope with the location table rather than treating a successful `git diff` command as scope validation. Record unresolved checks as incomplete, not passing. After each commit, verify `git log -1 --oneline` and a clean `git status --short`.

## Stage 1 - Canonical Policy and Evidence Boundaries

### Artifacts

New: `mydocs/manual/artifact_retention_guide.md`, `mydocs/tech/task_m1_48_reuse.md`, `mydocs/working/task_m1_48_stage1.md`.
Modified: `AGENTS.md` and #48's current daily-board row.

### Changes

- Establish one canonical procedure covering artifact classes/states, ownership and consumers, exact source/configuration identities, peak creation/archive/restore space, reuse, retention and release events.
- Require a reason for a full runtime copy while preserving necessary isolation, signing and fresh reconstruction. Prefer reusable immutable inputs and isolated mutable outputs; no change of runtime copy mechanism is implemented.
- Define bounded cleanup candidates, dependency/process checks, protected-input verification and private-state handling. Unknown dependencies remain unresolved; age, hashes, Issue closure or absent handles alone do not permit deletion.
- Define verified archive/restoration requirements and the narrow legacy inode-preserving exception. Mark retired bytes restore-required; keep recovery stores protected while originals depend on them. Missing/corrupt recovery must not be represented as available evidence.
- Distinguish logical, allocated/displayed, compressed and filesystem free-space observations, including APFS sharing and concurrent work.
- Keep root obligations concise. Put issue-specific measurements, historical limitations and the reuse decision in the research note. Preserve existing approvals, attribution and all unrelated root text.
- Context/source revisions remain those above; no added technical skill or implementation scope.

### Verification

Execute Shared Verification Commands. Review each listed policy requirement against the manual, and compare research figures/limits with the existing local receipts and survey. Confirm no private payload or raw diagnostic is copied. Record exact sections supporting lifecycle states, recovery dependencies, release conditions and accounting. Missing evidence is explicitly unavailable, not an invented pass. No restoration, deletion or native test is run.

### Commit

```text
Task #48 Stage 1: define artifact retention policy and evidence boundaries
```

## Stage 2 - Workflow, Templates and Skill Integration

### Artifacts

Modified: `mydocs/manual/task_workflow_guide.md`; `mydocs/_templates/task_plan.md`, `stage_report.md`, `final_report.md`; the four skill sources in the location table; #48's current daily-board row.
New: `mydocs/working/task_m1_48_stage2.md`.

### Changes

- Task plan: compact Artifact lifecycle field, retention table and reuse/peak-space decision; reasoned Not applicable for small tasks.
- Stage report: Artifact disposition covering actual retained/released/archived/unavailable state, remaining consumers, recovery references and measurement limitations.
- Final report: Retention handoff with owners, downstream dependencies, release events and unresolved cleanup.
- Add minimal template-aligned hooks: task-start records the plan; stage completion reconciles disposition; final reporting records handoff; merge cleanup examines ignored evidence and remaining consumers before removing a worktree.
- Link the canonical procedure at relevant workflow checkpoints. Avoid duplicating policy, new approval gates, new required services or automatic enforcement claims. Preserve existing verification, stage approvals and naming rules.
- Keep framework notices and discovery symlinks intact; do not edit unrelated framework defects. Source changes are the approved Pear additions on the pinned baseline.

### Verification

Execute Shared Verification Commands. In the report, record a matrix of the four skills, their checkpoint, matching template field or handoff reference and canonical-manual link. Inspect all placeholder destinations using their intended document folder. Compare approval/verification text and framework notices with the baseline. Verify ignored worktree evidence is addressed before removal, without treating an app/Git archive as guaranteed preservation. Do not run any cleanup procedure.

### Commit

```text
Task #48 Stage 2: connect artifact lifecycle to task workflows
```

## Stage 3 - Integrated Document Verification

### Artifacts

New: `mydocs/working/task_m1_48_stage3.md` with scenario outcomes and acceptance mapping.
Modified: #48's current daily-board row. Correct bounded inconsistencies in already approved Stage 1/2 files if verification identifies them; record corrections and rerun affected checks. New scope or locations require approval.

### Changes

Review the complete policy as a worker following the templates and skills. Record the following expected decisions and their actual supporting sections. These are document reviews, not executed storage operations.

| Scenario | Expected decision / false success to reject |
|---|---|
| Unchanged build inputs | Reuse only within exact identity and valid claim scope; no redundant full copy by default |
| Required fresh reconstruction | Preserve the required fresh build/check even if a cache exists |
| Active consumer after producer merge | Retain required inputs and ignored evidence until a verified migration/release event |
| Unique failure evidence | Preserve the minimum sufficient failure inputs/logs before disposing of run state |
| APFS clone or shared allocation | Separate displayed bytes from observed filesystem recovery; no summed-size promise |
| Corrupt or missing archive | Do not retire required intact originals; mark already retired bytes unavailable and retain surviving recovery material |
| Authenticated prefix/private state | Keep outside Git/releases and separate from disposable synthetic state; no inferred deletion permission |
| Small documentation task | Reasoned Not applicable for material storage; compact Git-backed evidence without large manifests |

### Verification

Execute Shared Verification Commands. Map all eight Issue acceptance criteria to final sections and scenario evidence: canonical lifecycle, plan fields, report dispositions, ignored worktree evidence, copy rationale, accounting, unchanged evidence/security/approval rules, and passing scenario/document checks. Review the full diff against `d01f526` for attribution, approved paths, #48-only board changes, no runtime/private artifacts and unchanged discovery links. Record historical evidence separately from fresh document checks. All eight scenarios must have explicit reviewed outcomes; an unresolved mismatch prevents stage completion.

### Commit

```text
Task #48 Stage 3: verify retention scenarios and document consistency
```

## Verification and Commits

Shared verification and stage-specific review are required before a passing stage report. Recheck after adding the report so its links and scope are included. Commit each stage's artifacts with its report; do not enter the next stage until the requester explicitly continues. Planning uses `Task #48: implementation plan and daily task board update`.

After all three stages, prepare `mydocs/report/task_m1_48_report.md` and complete the current daily-board row under the existing final-report procedure. Carry forward unchanged document checks only with their exact revision/scope; rerun affected checks after corrections or integration. PR publication uses `codex/publish-task48` to `master`, with separate approval and remote CI evidence. No new release branch, self-merge or Issue closure is authorized here.

## Stage Dependencies

- Stage 1 starts after implementation-plan approval.
- Stage 2 starts after Stage 1 verification, report, commit and explicit continuation.
- Stage 3 starts after Stage 2 verification, report, commit and explicit continuation.
- Final reporting/publication and post-merge cleanup retain existing approval boundaries.

## Risks and Responses

- **Policy ceremony:** one manual, compact template fields and reasoned Not applicable; no per-command inventory requirement.
- **Premature cleanup or indefinite retention:** document both current consumers and concrete release events, preserving unresolved dependencies.
- **Unavailable historical bytes:** preserve recovery-store references and distinguish historical verification from present availability.
- **Overclaimed validation:** supplemental links and scenario review complement the narrow existing checker; no automated policy enforcement or new physical savings claim.
- **Concurrent edits:** inspect overlap before modification/integration and preserve unrelated boards/worktrees. If the base becomes stale, inspect conflicts before choosing an integration operation.

## Approval Request

Approve the three-stage split, exact artifacts, shared verification commands, manual scenarios and commit plan, then begin Stage 1 only. This remains documentation work and does not authorize further artifact deletion, runtime implementation or changes to #11's execution priorities.
