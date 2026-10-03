# AGENTS.md

Persistent rules for agents working on Pear. Read the applicable context explicitly; do not assume that every tool automatically loads this file, subordinate rules or skills.

## Context before changes

Pear is an open-source platform under development for running owned Windows games on Apple Silicon without Rosetta. Megabonk is the first runtime target; the downloadable Mac app, official Steam flow, installation, play and recovery are goals, not existing support claims.

- Read the relevant GitHub Issue, approved task and implementation plans, latest available stage report, applicable ancestor/scoped `AGENTS.md` files and selected skills. During registration and planning, use the artifacts that already exist.
- Start with [README](README.md), the [official documentation index](docs/README.md), [architecture](docs/architecture.md) and the single [delivery plan](docs/delivery-plan.md). Read the requirements relevant to the affected area before choosing an implementation.
- Review reusable upstream implementations before new subsystem code and record the reuse decision. Retain upstream languages unless a measured, reviewed reason justifies replacement; Rust is not mandatory. Respect upstream licenses and contribution policies.
- Before new implementation, inspect relevant open Issues, active work branches/worktrees and latest reports; record existing reusable work and unresolved integration dependencies.
- Reuse verification evidence only when its recorded inputs and claim scope remain valid; revalidate affected evidence after integration or relevant source, toolchain, configuration or artifact changes. Preserve approved required checks. See the [dated reuse investigation](mydocs/tech/20261004_recompilation_and_verification_reuse.md) for non-normative examples.

## Approval and workflow

- Track work by GitHub Issue. Obtain requester approval before source changes and follow `Issue -> branch -> daily task board -> plan -> implementation -> verification -> final report -> PR`.
- Complete, verify, report and commit each stage before requesting approval for the next. A stage transition is approved only by explicit continuation in the same thread, such as “continue” or “proceed to the next stage.” Existing authorization applies only to its approved scope.
- Ask first if scope is unclear or conflicts with other work. Preserve changes made by the requester and other workers.
- Before editing documentation, read the existing content and change only what is necessary. For product, user, contributor, integration, API, architecture or roadmap document additions, moves or edits, record the location judgment in the task plan and obtain approval.
- `docs/` is the approved official documentation root. Keep task plans, reports and workflow procedures in `mydocs/`; `mydocs/manual/` is not a product-documentation destination.
- Close an Issue only after requester approval or confirmed PR merge. After merge and Issue closure, return to `master` and remove unneeded task/publication branches and temporary worktrees; preserve artifacts still needed by another task or review.
- The requester decides when work starts and ends. Do not propose ending work or impose time limits.

## Naming and repository constraints

- Write repository documents, Issues, PR descriptions, reports, code comments and default user-facing text in English. Use the requester's preferred language in conversation.
- In Codex use `codex/task{issue_number}` for work and `codex/publish-task{issue_number}` for publication to `master`. Other environments follow their required prefix; framework `local/` and `publish/` names are examples.
- `master` is the integration and release branch. Do not execute same-branch release-promotion examples; a separate release branch needs a separate decision.
- Preserve existing M1/R1 milestone names and Issue identities. Use the milestone-inclusive filename `task_{milestone}_{issue_number}{_impl|_stage{N}|_report}?.md` with lowercase milestone text. New milestone conventions follow the manuals.
- Use `Task #{number}: summary`, `Task #{number} Stage {N}: summary`, `Task #{number} [Stage {N.M}]: summary`, or `Task #{number} Stage {N} + final report: summary` for the corresponding commit type.

## Evidence and security

- The first runtime milestone requires owned Windows Megabonk without Rosetta in every required host process and library. A native launcher alone is insufficient.
- Keep source inspection, builds, synthetic tests, host execution, game qualification and ordinary-user distribution distinct. Record unknown, unavailable, unsupported, failed and unperformed observations explicitly; experiments do not establish qualified support.
- Keep proprietary game files, Steam credentials, authenticated prefixes, saves, private signing material and private diagnostics out of Git and release artifacts.
- Preserve macOS security protections. Use documented signing and provisioning authorization; successful signing alone does not establish permission or distribution qualification.

## Scoped rules and procedures

| Work | Read when applicable |
|---|---|
| Native host code and probes | [host/AGENTS.md](host/AGENTS.md) |
| Tests and fixtures | [tests/AGENTS.md](tests/AGENTS.md) |
| Product and contributor documentation | [docs/AGENTS.md](docs/AGENTS.md) |
| Metal diagnostics, capture, rendering, presentation or metal-cpp lifetime work | [Pear Apple-tooling skill](mydocs/skills/pear-apple-tooling/SKILL.md); select only relevant technical experts |
| Task and report procedures | [Task workflow](mydocs/manual/task_workflow_guide.md), [Git workflow](mydocs/manual/git_workflow_guide.md), [rule conflicts](mydocs/manual/agent_code_hyperfall_rule_conflict.md) and relevant [shared skills](mydocs/skills/) |
| Document locations and skill discovery | [Document structure](mydocs/manual/document_structure_guide.md) |
| External contributor PRs | [PR process](mydocs/manual/pr_process_guide.md) and [contributor guide](docs/contributing.md) |

Shared skill source is `mydocs/skills/`; preserve the `.agents/skills` and `.claude/skills` discovery symlinks. Apple expertise does not replace Pear's Issue, approval or reporting workflow. Introduce scoped rules for future `runtime/`, `profiles/` or `manager/` areas when those implementations are added; do not create empty directories just for rules.

## Framework attribution

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
