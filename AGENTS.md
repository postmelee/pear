# AGENTS.md

Operational rules for every coding agent working in this repository, including Codex and Claude Code. This file is loaded into the system prompt on every turn, so keep only the policies, constraints, and indexes that must always be present. Put detailed procedures in manuals and SKILL files.

## Project Overview

Pear is an open-source platform under development for running Windows games on Apple Silicon without Rosetta, with community-maintained compatibility evidence. The first runtime target is Megabonk. The intended user experience is a downloadable Mac app, official Steam sign-in, owned-game installation and launch, and recovery through verified runtime versions. These are development goals, not existing support claims.

## Core Hyper-Waterfall Rules

This project uses the **Hyper-Waterfall** methodology. Read these rules carefully because they can conflict with an agent's default behavior, especially fast execution and autonomous edits. Details: [`agent_code_hyperfall_rule_conflict.md`](mydocs/manual/agent_code_hyperfall_rule_conflict.md).

- Request task requester approval before modifying source files.
- Track work by GitHub Issue.
- Never skip the order for new features, bug fixes, or structural changes: `Issue -> branch -> daily task board -> plan -> implementation -> verification -> final report -> PR`.
- Do not move to the next stage without approval after completing the current stage.
- If the scope is unclear or could conflict with existing work, ask first.
- Do not revert changes made by the user or another worker.
- Close an Issue only after task requester approval or after confirming the PR was merged.
- Before editing documentation, read the existing content first, change only the necessary parts, and add content only when needed.
- When creating, moving, or editing product, user, contributor, external integration, API, architecture, or roadmap documentation, record a document location judgment in the task plan and get approval.
- `mydocs/manual` is not the target project's product documentation location. The target project must explicitly choose its official documentation root, such as `docs/`, `specs/`, `site/`, `website/`, or `adr/`, in a separate task.
- After work is complete, clean up local and remote artifacts that are not needed for the next task.
- After PR merge and Issue close, return to `master` and remove unneeded `local/task{number}` branches and temporary worktrees.

**Approval assumption rule**: Treat the stage as approved only when the task requester explicitly says to continue in the same thread, such as "continue" or "proceed to the next stage."

## Naming Rules

- Milestone: `M{version}` (for example, M100=v1.0.0, M05x=v0.5.x). Document filenames use lowercase `m{number}` (for example, `m100`).
- Branches: `local/task{issue_number}` for work, `publish/task{issue_number}` for PR publication to `master`.
- Commit messages:
  - Basic: `Task #{number}: summary`
  - Stage: `Task #{number} Stage {N}: summary`
  - Substage: `Task #{number} [Stage {N.M}]: summary`
  - Report bundle: `Task #{number} Stage {N} + final report: summary`
- Document filename: `task_{milestone}_{issue_number}{_impl|_stage{N}|_report}?.md`. New documents must include the milestone. Details: [`document_structure_guide.md`](mydocs/manual/document_structure_guide.md).
- Write all documents in the selected Hyper-Waterfall locale for this repository.

## Mandatory Rules Before Changes

- Write repository documentation, Issues, PR descriptions, reports, code comments, and user-facing default text in English. Use the task requester's preferred language in conversation; do not impose one conversational language on contributors.
- The first runtime milestone is owned Windows Megabonk running without Rosetta in every required host process. A native launcher alone does not meet that requirement.
- Keep proprietary game files, Steam credentials, authenticated prefixes, saves, and private diagnostics out of Git and release artifacts.
- Keep experimental results distinct from qualified support; record unknown, unsupported, and failed observations explicitly.
- Do not disable macOS security protections to qualify a supported runtime. Use a documented signing and provisioning path.
- Retain existing upstream implementation languages unless a measured, reviewed reason justifies replacement. Rust is not mandatory.
- Follow the active coding environment's required branch prefix. In Codex use `codex/task{issue_number}` for work and `codex/publish-task{issue_number}` for PR publication; framework examples using `local/` and `publish/` remain examples.
- Pear currently uses `master` for integration and releases. Do not execute same-branch release-promotion examples; a separate release branch requires a separate decision.
- Existing M1 and R1 milestone names and issue identities remain valid. Framework adoption does not rename them.
- Existing product documentation remains in place during adoption; any later document addition or relocation needs the workflow's document-location judgment.

### Framework attribution

The installed Hyper-Waterfall operating documents and templates are from [v0.3.0](https://github.com/postmelee/hyper-waterfall/releases/tag/v0.3.0), commit `83836828a4da24385d0410515d35ee43946b981f`. The following notice applies to those framework materials, not to a new license choice for Pear:

```text
MIT License

Copyright (c) 2026 postmelee

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Required References

- [`README.md`](README.md) - project overview, setup, and build
- [`mydocs/manual/document_structure_guide.md`](mydocs/manual/document_structure_guide.md) - `mydocs/` folder roles, document filenames, external PR folder policy, Skills location policy
- [`mydocs/manual/task_workflow_guide.md`](mydocs/manual/task_workflow_guide.md) - 15 task workflow steps, commit message rules, work time rules
- [`mydocs/manual/git_workflow_guide.md`](mydocs/manual/git_workflow_guide.md) - branch policy, Git diagrams, maintainer/contributor workflow
- [`mydocs/manual/pr_process_guide.md`](mydocs/manual/pr_process_guide.md) - external contributor PR review
- [`mydocs/manual/agent_code_hyperfall_rule_conflict.md`](mydocs/manual/agent_code_hyperfall_rule_conflict.md) - conflicts between Hyper-Waterfall and default agent behavior
- [`docs/architecture.md`](docs/architecture.md) and [`docs/delivery-plan.md`](docs/delivery-plan.md) - existing technical baseline and tracked implementation dependencies

## Agent Skills

Fixed Hyper-Waterfall procedure points are separated into SKILL files. The source of truth is `mydocs/skills/`. Codex (`.agents/skills`) and Claude Code (`.claude/skills`) read the same content through symbolic links. Details: the "Agent Skills location policy" section in [`document_structure_guide.md`](mydocs/manual/document_structure_guide.md).

## Work Rules

- The task requester decides when work starts and ends. Agents do not propose ending work or impose time limits on their own.
