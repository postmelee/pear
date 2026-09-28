# Task #25 - Implementation plan

Task plan: [task_m1_25.md](task_m1_25.md)
GitHub Issue: [#25](https://github.com/postmelee/pear/issues/25)
Milestone: M1 - Megabonk on Apple Silicon without Rosetta
Work branch: `codex/task25`; publication branch: `codex/publish-task25`; PR base: `master`
Status: Stage 1 complete on September 28, 2026; approval to begin Stage 2 is pending.

## Approval and Working Context

The maintainer explicitly approved the task plan and continuation to implementation-plan preparation in this session on September 28, 2026. This records approval of the scope and document-location judgment in the task plan. Implementation-plan approval and each completed-stage transition remain separate gates.

Use the attached `pear-governance` worktree. Before each stage, read #25, the approved task/implementation plans, the latest existing stage report and applicable `AGENTS.md` files. At implementation-plan preparation, no stage report existed. The latest completed stage is now recorded in the [Stage 1 report](../working/task_m1_25_stage1.md). Preserve #1 source ownership, #3 contract/language ownership, their separate worktrees and existing untracked `analysis/` and `research/`.

The planning base is `a75237a6f67a3ade71fcef6068a228686958efe2`. At preparation, #25 is open, remote master still matches that base and no PR is open. These are dated observations; recheck before integration. #3 may later touch `docs/README.md` and `docs/architecture.md`.

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Official documentation and roadmap | README, docs index, delivery plan, contributor guide and narrow architecture alignment | User outcomes, M1/M2/Phase distinctions, P/E dependency preservation and document links |
| 2 | Scoped rules and Apple expert routing | Root/scoped rules, public tooling guide, short skill and pinned metadata | Source/version/reference review, skill validation, discovery and availability boundaries |
| 3 | Templates and mechanical verification | Five templates, offline checker, fixture tests and documentation CI | Passing/rejection cases, YAML/format checks and integrated document consistency |

## Document Location Check

All destinations follow the approved task-plan judgment; no document relocation is proposed.

| File | Planned Location in Task Plan | Stage Artifact Path | Match | Notes |
|---|---|---|---|---|
| Overview, index and roadmap | Root README and existing docs | `README.md`, `docs/README.md`, `docs/delivery-plan.md` | OK | One roadmap source |
| Architecture alignment | Existing architecture | `docs/architecture.md` | OK | Only M1/Phase wording and present structure |
| Contributor and tooling guidance | Official docs | `docs/contributing.md`, `docs/development/apple-tooling.md` | OK | Human-facing reusable guidance |
| Agent instructions | Root and existing work areas | `AGENTS.md`, `host/AGENTS.md`, `tests/AGENTS.md`, `docs/AGENTS.md` | OK | No empty future implementation folders |
| Skill and source metadata | Shared skill source | `mydocs/skills/pear-apple-tooling/SKILL.md`, `mydocs/skills/pear-apple-tooling/references/upstream.json` | OK | Existing discovery symlinks preserved |
| Platform templates | Existing GitHub paths | `.github/ISSUE_TEMPLATE/task.yml`, `.github/pull_request_template.md` | OK | Minimal context additions |
| Work templates | Existing central templates | `mydocs/_templates/task_plan.md`, `mydocs/_templates/task_impl_plan.md`, `mydocs/_templates/stage_report.md` | OK | Reuse existing evidence sections |
| Verification code and workflow | Tools, tests and GitHub | `tools/check_governance.py`, `tests/docs/test_check_governance.py`, `.github/workflows/documentation.yml` | OK | Offline documentation checks only |
| Task artifacts | Existing work folders | `mydocs/plans/task_m1_25*.md`, `mydocs/working/task_m1_25_stage{1,2,3}.md`, `mydocs/report/task_m1_25_report.md`, dated board | OK | Approval, actual results and limitations |

The stage file lists below exclude routine updates to this task's approval/status records and dated board. Review related skill/template indexes as required by the manuals; no index/manual edit is currently necessary. If one is demonstrated necessary, record the exact narrow correction before editing and obtain approval for any scope/location change.

## Stage 1 - Official Documentation and Roadmap

### Artifacts and Changes

- Add `docs/contributing.md`. Describe requests, bug reports, real-owner testing, docs, profiles and code contributions. Human contributions need no Codex or paid AI. Link the applicable contribution workflow and retain source/license/upstream-policy boundaries, including the FEX AI-generated-code contribution restriction.
- Update `README.md` with the first ordinary-user flow, current qualified/unqualified distinction, short five-phase summary and official roadmap/contribution links. Preserve the existing project vision and bounded experimental observations.
- Update `docs/README.md` to establish the official root and information authority. Distinguish normative requirements from dated research within that root; do not promote all research to a support claim. Describe the recommended Discussions/Wiki roles without claiming activation or creating platform content.
- Expand `docs/delivery-plan.md` as the sole roadmap. Keep P01-P16/E01-E05 issue rows and acceptance dependencies intact. Add Phase 1-5 and the proposed M2/U01-U07 scope, acceptance dependencies and pending-registration status. Phase 1 includes the ordinary-user flow, while M1 remains technical qualification; useful profile groundwork can start early. Phase 4 includes PRs, schema/redistributable fixture checks, owner testing, a reviewed registry and requests/votes/database.
- Make narrow `docs/architecture.md` corrections: technical M1 terminology, CLI-first development versus the ordinary-user app outcome, the bounded technical G4 result, and existing host/tests directories. Retain subsystem contracts and #3 ownership.

The proposed U01-U07 scope must preserve official Steam ownership/authentication, runtime identity and atomic installation/recovery, save preservation before restore, normal protections, release packaging and qualification on a second clean setup. Do not copy obsolete zero-identity or uncompleted-#2 claims from temporary proposals. Optional MSC/D3DMetal experiments and R1 remain outside the Phase 1 critical path.

### Verification

Review the five-file diff against #25 and the supplied proposal. Manually follow local heading fragments, verify that new U identifiers have no fabricated Issue links, and verify the current FEX contribution policy from its official source before describing it. Record actual source/date and the review result in the report.

Run from the worktree root:

```sh
python3 - <<'PY'
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit
base = subprocess.check_output(['git', 'show', 'a75237a:docs/delivery-plan.md'], text=True)
current = Path('docs/delivery-plan.md').read_text()
rows = lambda text: re.findall(r'^\| [PE]\d{2} \|.*$', text, re.M)
assert len(rows(base)) == 21 and rows(base) == rows(current), 'P/E rows changed'
paths = ['README.md', 'docs/README.md', 'docs/delivery-plan.md', 'docs/architecture.md', 'docs/contributing.md']
count = 0
for name in paths:
    source = Path(name)
    text = source.read_text()
    text = re.sub(r'(?ms)^```.*?^```[^\n]*', '', text)
    for target in re.findall(r'\]\(([^\s()]+)\)', text):
        url = urlsplit(target)
        if url.scheme or url.netloc or not url.path:
            continue
        assert (source.parent / unquote(url.path)).exists(), (name, target)
        count += 1
print(f'PASS: 21 preserved dependency rows; {count} simple local link targets')
PY
git diff --check
git diff --stat
```

This temporary check covers simple inline file targets in the five edited documents, not all Markdown forms or anchors. The reviewed links must use that form or receive explicit manual review. Stage 3 adds the maintained bounded checker.

### Commit

Use `task-stage-report` after verification; include the source changes and `mydocs/working/task_m1_25_stage1.md` in one commit:

```text
Task #25 Stage 1: establish the official roadmap and contributor guidance
```

## Stage 2 - Scoped Rules and Apple Expert Routing

### Artifacts and Changes

- Update root `AGENTS.md`: retain enduring constraints, English repository language, approval workflow, Codex branch rules, normal-security/Rosetta evidence and attribution. Replace the automatic-every-turn loading guarantee with required context discovery. Point to the official root, relevant subordinate rules and shared skills.
- Add `host/AGENTS.md` for native process/ABI evidence, upstream reuse and bounded authorized diagnostics; `tests/AGENTS.md` for redistributable fixtures, real failure cases and limits of synthetic/platform-skipped results; `docs/AGENTS.md` for approved locations, authoritative requirements versus dated observations and source provenance.
- Add `docs/development/apple-tooling.md` and link it from `docs/README.md` (the index is already in the approved changed-file set). Record the six task-specific expert routes, immutable official sources, platform prerequisites and candidate Xcode alternatives. Keep source inspection, tool availability, capture, rendering and performance results distinct.
- Use `skill-creator` to add a short `mydocs/skills/pear-apple-tooling/SKILL.md` and `references/upstream.json`. No optional UI metadata or copied upstream manuals are needed. Keep shared `.agents/skills` and `.claude/skills` unchanged.
- Route only technical expertise: `using-metal-validation`, `using-gpucapture`, `using-gpudebug`, `debugging-rendering-issues`, `presenting-metal-drawables`, `managing-metal-cpp-lifetimes`. Resolve selected relative reference files at the same revision. Shader Converter/Metal 4 experts apply only to corresponding implementation work.

The metadata will record the upstream repository URL, reviewed 40-hex revision, review date, plugin manifest path/version, selected skill paths, necessary relative-reference paths and source-backed tool requirements. It is a source-reference inventory, not a runtime or game-profile schema. Observation dates and tool availability in the guide do not become timeless installation claims.

Start from reviewed revision `4f42344c90be22112f46becc3fb9687f423f2f88` and manifest version `1.0.0-beta.1`. Verify its manifest and selected original files in Stage 2 and preserve exact provenance. If main has moved, report the difference rather than silently changing the reviewed pin. Explain how to read pinned raw files and resolve sibling references when the plugin is not installed. Apple's documented plugin installation commands are informational; do not execute them.

Retain Hyper-Waterfall as the sole task/approval/report workflow; do not invoke the Apple `.porting` lifecycle. Record the macOS 27 requirement for the new capture/debug CLIs separately from the current host and eventual end-user requirements. Keep diagnostic/performance settings separate and raw captures private. Do not blindly copy lifetime examples when they conflict with actual SDK/header/API contracts.

### Verification

Read the pinned README, plugin manifest, six selected SKILL files and the five identified rendering/drawable reference files from official upstream. Check the declared routes and source requirements against those files. Record exact URLs, revision/version and source-check results in the stage report; do not claim the offline checker proves remote source content. Inspect the actual environment and installed-skill availability again without altering global configuration or executing captures.

The skill-creator validator imports PyYAML. The current system and bundled Python lack it; use an isolated temporary authoring environment, not a global or project runtime dependency. [PyYAML 6.0.3](https://pypi.org/project/PyYAML/6.0.3/) is the reviewed package version. Create the environment only during this approved stage, record its resolved path/version and retain it for Stage 3 YAML verification if useful:

```sh
PEAR_TASK25_VALIDATION_ENV=$(mktemp -d /private/tmp/pear-task25-validation.XXXXXX)
python3 -m venv "$PEAR_TASK25_VALIDATION_ENV"
"$PEAR_TASK25_VALIDATION_ENV/bin/python" -m pip install --disable-pip-version-check --only-binary=:all: 'PyYAML==6.0.3'
"$PEAR_TASK25_VALIDATION_ENV/bin/python" "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" mydocs/skills/pear-apple-tooling
python3 -m json.tool mydocs/skills/pear-apple-tooling/references/upstream.json
python3 - <<'PY'
from pathlib import Path
root = Path.cwd()
for name in ['.agents/skills', '.claude/skills']:
    link = root / name
    assert link.is_symlink() and link.resolve() == root / 'mydocs/skills', name
print('PASS: both skill discovery links preserved')
PY
git ls-files -s .agents/skills .claude/skills
sw_vers -productVersion
xcodebuild -version
python3 - <<'PY'
import shutil
for name in ['gpucapture', 'gpudebug']:
    print(name + ': ' + (shutil.which(name) or 'unavailable on PATH; not executed'))
PY
git diff --check
```

The validator path is an authoring-host dependency, not a requirement for human contributors. If a required validator/source check cannot be run, record and resolve that limitation before claiming this stage complete; never convert a failed or missing tool into success. Static availability checks above are expected to report unavailable tools honestly. No GPU execution is a Stage 2 acceptance requirement.

### Commit

Bundle the stage files and `mydocs/working/task_m1_25_stage2.md`:

```text
Task #25 Stage 2: connect scoped rules and pinned Apple technical guidance
```

## Stage 3 - Templates and Mechanical Verification

### Artifacts and Changes

- Extend `.github/ISSUE_TEMPLATE/task.yml`, `.github/pull_request_template.md`, `mydocs/_templates/task_plan.md`, `mydocs/_templates/task_impl_plan.md`, and `mydocs/_templates/stage_report.md` minimally. Reuse existing evidence and document-location sections; add missing requirements/rules, reuse decision, selected skills/revisions, availability/settings and unverified scope. Planned checks are distinct from performed results. Permit reasoned `Not applicable`.
- Add `tools/check_governance.py` using Python standard library only, with optional `--root` for isolated fixtures and default repository-root resolution from the script path. Return zero only when every governed check passes; failures identify the source and offending target/field.
- Add `tests/docs/test_check_governance.py` with isolated synthetic repositories and real checker/CLI execution. No game files, account state, GPU tools or external network access.
- Add `.github/workflows/documentation.yml` running the checker and unit tests on PRs to master and manual dispatch. Use read-only contents permission, a bounded job timeout, no secrets, no pull_request_target execution and no runtime/game jobs. Verify selected action revisions from their official repositories when implementing. Keep the job small enough to run on every PR instead of maintaining a fragile documentation path filter.
- Add the checker command and its bounded coverage to `docs/contributing.md`, already in the approved changed-file set.

### Checker Contract

1. Govern `README.md`, `AGENTS.md`, `CLAUDE.md`, the required three scoped AGENTS files, `docs/**/*.md` and the Pear router `SKILL.md`. Exclude historical `mydocs/` work artifacts/templates and unrelated root `analysis/` and `research/` as input trees. Required entrypoint/scoped/router files cannot disappear silently.
2. Check local file/directory targets in inline Markdown links/images and reference definitions, including plain and angle-bracket destinations. Ignore fenced code, inline code, HTML comments and external scheme/protocol-relative URLs. Decode URL-escaped paths and strip query/fragment for path resolution.
3. Resolve targets relative to their source. Reject absolute local paths and resolved paths escaping the repository, and reject missing targets. Reference-use resolution, same-file fragments and heading-fragment validity are outside automated coverage; manually verify newly added anchors. Nested/escaped Markdown edge cases and raw HTML links are outside the supported subset and must be reported as limitations rather than claimed complete coverage.
4. Verify both skill discovery symlinks reach `mydocs/skills`; verify the router links to the actual public tooling guide and source metadata. Test link relationships, not exact prose.
5. Validate the source inventory structure, exact Apple repository identity, full immutable revision, nonempty plugin version and expected manifest path, six selected skill identities/paths, required relative reference entries and sourced capture/debug minimum-platform fields. Require referenced source URLs to use the recorded revision. These checks establish internal consistency, not remote availability or technical accuracy.

Fixture cases: valid mini-repository; missing linked file; missing required rule/router; bad or escaping discovery link; absolute/escaping link destination; moving/short/malformed source revision; absent or wrong skill/source-reference entry; mismatched pinned URL; broken guide/router link; external/code/comment exclusions; and URL-escaped local paths with query/fragment. Include CLI exit behavior and diagnostics. A fragment's existence is not a passing claim of this checker.

### Verification

```sh
python3 tools/check_governance.py
python3 -m unittest discover -s tests/docs -p 'test_*.py' -v
ruby --disable-gems -rpsych - <<'RUBY'
issue = Psych.safe_load(File.read('.github/ISSUE_TEMPLATE/task.yml'))
abort 'Issue body missing' unless issue.is_a?(Hash) && issue['body'].is_a?(Array)
ids = issue['body'].map { |field| field['id'] }.compact
abort 'Duplicate Issue field IDs' unless ids.uniq == ids
workflow = Psych.safe_load(File.read('.github/workflows/documentation.yml'))
abort 'Workflow jobs missing' unless workflow.is_a?(Hash) && workflow['jobs'].is_a?(Hash)
puts 'PASS: Issue and workflow YAML parsed; body IDs unique; jobs present'
RUBY
git diff --check
git diff --stat a75237a
```

Use the existing local Ruby/Psych for this authoring-time YAML check; it is not a new project dependency or a complete GitHub schema validator. Quote the workflow `on` key so YAML 1.1 parsers preserve its spelling. Manually review events, permissions, commands and action pins. Review template sections and their related skills/indexes for consistency without mirroring exact wording in tests. Remote workflow acceptance is recorded only after an actual PR run.

### Commit

Bundle implementation, documentation/template updates and `mydocs/working/task_m1_25_stage3.md`:

```text
Task #25 Stage 3: validate documentation routing and strengthen task templates
```

## Verification

Run each stage's commands and semantic review before writing its report. Preserve concise command/result/evidence summaries, source metadata and meaningful failures; do not commit raw external packages or private diagnostic output. Failed checks must be resolved in the current stage. If a verification command needs correction, document the correction and its reason without concealing the original failure.

For integrated verification, rerun the Stage 3 checker/tests after the final relevant edits, compare all #25 acceptance criteria to files/results, and verify planned versus actual document locations. Inspect the full diff for changes outside the approved paths and recheck #1/#3 and origin/master before publication. Do not edit the other task worktrees; reconcile merged overlap in this worktree, preserving their changes. If integrated master changes the relevant baseline, record the new base and why in the final report.

Use `task-final-report` only after all stages and their approvals are complete. Prepare the final report, mark the actual day's #25 board row Done with time, and commit with `Task #25: final report and daily task board completion`. Obtain the final-report approval required by the workflow before publication. Publish `codex/task25:codex/publish-task25`, create an open PR to master, attach it to this chat and record actual remote check links/results. Do not auto-merge or close #25 before approved closure or confirmed merge. Keep the worktree available for review; after merge use the repository cleanup procedure and managed-worktree archival.

## Commits

- Implementation-plan preparation changes only this plan, the task plan's approval record and the #25 board note; commit as `Task #25: implementation plan and task plan approval`.
- Each stage commit contains its implementation and corresponding stage report together.
- Final-report/board completion is committed separately after approved stage completion. No task branch is pushed directly as a remote work branch.

## Stage Dependencies

- Approval of this implementation plan permits Stage 1 to begin.
- Stage 2 starts only after Stage 1 implementation, verification, report/commit and the maintainer's explicit approval to continue.
- Stage 3 starts only after the corresponding Stage 2 approval.
- Final report and PR follow successful integrated verification and the remaining workflow approvals.

## Risks and Responses

- Concurrent index/architecture/board edits: inspect current master and linked work before publication; preserve unrelated work.
- Documentation or CI overclaim: mark tools unavailable/not run, separate source inspection from execution, and keep anchor/Markdown limits explicit.
- Optional tooling expanding Phase 1: retain Wine/FEX/DXMT and existing Issue ownership; no global plugin lifecycle, native-shader experiment or new schema here.
- Provenance drift: use immutable Apple/action revisions; preserve framework license and historical adoption records; record deliberate Pear customization.
- Local validator dependencies: use a disposable environment for the authoring helper only; production checker/tests remain Python standard library and offline.

## Approval Request

Approve these three stages, artifacts, verification commands, bounded checker coverage and commit messages so Stage 1 can begin. This approval does not waive subsequent stage/report gates or authorize any excluded runtime, plugin, platform-security or repository-publication setting change.

Approval recorded: on September 28, 2026, the maintainer explicitly instructed this session to proceed in response to the implementation-plan review and Stage 1 start request. The three-stage implementation plan is approved, and Stage 1 is authorized. Later stage transitions remain subject to their report approvals.
