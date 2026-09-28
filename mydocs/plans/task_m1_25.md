# Task #25 - Official roadmap and task-specific engineering guidance

GitHub Issue: [#25](https://github.com/postmelee/pear/issues/25)
Milestone: M1 - Megabonk on Apple Silicon without Rosetta
Date: September 28, 2026
Work branch: `codex/task25`
Base: `origin/master` at `a75237a6f67a3ade71fcef6068a228686958efe2`
Status: All three stages approved; final report prepared; approval for PR publication pending.

## Purpose

Apply the maintainer-reviewed documentation layout and operating model so contributors can find Pear's product roadmap, understand the evidence needed for support, and select the relevant engineering rules and Apple technical guidance. Preserve the priority of running owned Windows Megabonk without Rosetta in every required host process and library, followed by the complete ordinary-user installation, Steam, play, save and resume experience.

Deliver three reviewable stages: official documentation and roadmap; scoped rules and Apple expert-skill routing; minimal template extensions and reproducible mechanical checks. This work does not implement or qualify a game runtime.

## Background

[Issue #22](https://github.com/postmelee/pear/issues/22) adopted Hyper-Waterfall v0.3.0 in English and deliberately deferred the official product-document root and roadmap decision. Existing [architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md), and [documentation index](../../docs/README.md) remain the baseline.

[Issue #2](https://github.com/postmelee/pear/issues/2) is closed after PR #24. Its [final report](../report/task_m1_2_report.md) records a bounded native host gate PASS with development provisioning on M4 Pro/macOS 26.5.2. This is neither ordinary-user distribution nor a Rosetta-free game qualification. Stale proposal statements about absent signing identities or uncompleted host probes must not be copied into current product guidance.

[Issue #1](https://github.com/postmelee/pear/issues/1) owns runtime source qualification; [Issue #3](https://github.com/postmelee/pear/issues/3) owns actual runtime/profile contracts and the manager-language decision. Both are active in separate worktrees. Issue #3 also plans edits to the documentation index and architecture; this task limits those edits to its approved roadmap and guidance concerns and checks integration again before PR publication.

The maintainer supplied a reviewed application proposal and GPTK investigation. Relevant accepted requirements will become self-contained tracked documentation with source provenance; temporary research files will not be the published source of truth. Existing M1/R1 identities are retained. M2 and U01-U07 are proposals, not registered milestones or Issues.

## Scope

### Included

- Confirm `docs/` as Pear's official product, technical and contributor root; retain `docs/delivery-plan.md` as the only roadmap and link it from a concise README summary.
- Document five phases: first ordinary-user Megabonk experience; versioned multi-game profiles; Steam library/environment/evidence matching with Install/Play; reviewed community profiles and evidence; a maintainable Proton-for-macOS-like experience. These describe expanding user capabilities, not a ban on useful preparatory work.
- Preserve M1's technical qualification and R1's independent CPU research. Incorporate proposed M2/U01-U07 for ordinary-user execution permission, native app/setup, verified runtime versions, official Steam flow, saves/recovery, packaging and clean-environment end-to-end qualification. Record pending registration and acceptance dependencies without inventing Issue numbers.
- Clarify information authority: official documents for requirements and completion criteria; GitHub for live task state; qualification records for execution evidence; `mydocs/` for Issue plans, approvals and reports. Discussions carry requests, votes, questions and proposals; only adopted decisions become docs/Issues. Wiki is initially a guide/link surface, not another rule source.
- Add public contributor guidance without requiring Codex, paid AI or programming for all contributions. Preserve upstream implementation languages, licenses and contribution-policy boundaries, including FEX's AI-generated-code upstream restriction.
- Make root `AGENTS.md` a concise index of enduring constraints and required context lookup. Require the relevant Issue, approved plan, recent stage report and applicable subordinate instructions before edits. Add scoped rules under existing `host/`, `tests/`, and `docs/`; future implementation areas add their own applicable rules when implemented.
- Add a small Pear Apple-tooling router and public development guide. Select relevant expert skills explicitly, record pinned provenance and tool availability, resolve necessary relative references, and keep Apple's technical guidance separate from its `.porting` lifecycle.
- Extend five existing templates minimally for applicable requirements/rules, upstream reuse decisions, selected skills/revisions, tool prerequisites and actual availability, validation method/result/evidence, unverified scope and documentation impact. Permit reasoned `Not applicable` entries.
- Add a small offline documentation/routing/metadata checker, meaningful positive and negative fixtures, and a narrowly scoped documentation PR workflow. Record the actual local/remote verification and its limitations in stage/final reports.

### Excluded

- Runtime source qualification/pins owned by #1, actual schemas or manager-language selection owned by #3, and runtime regression CI owned by #14.
- Runtime/application implementation, new CPU-translation development, upstream-language replacement, or a game support/performance claim.
- Creation of M2 or U01-U07 GitHub entries; retain their registration as an explicit follow-up candidate.
- Standalone MSC/D3DMetal experiments, shader-container classification, stable/beta conversion matrices, or a new GPTK prerequisite for Phase 1. Reconsider only for a concrete graphics blocker or separately approved native-shader path.
- Global plugin installation/configuration, OS/Xcode upgrades, macOS protection changes, source reconstruction from proprietary game material, or publishing raw GPU captures.
- Other workers' worktrees, plans or uncommitted changes; existing untracked `analysis/` and `research/`; game files, credentials, authenticated prefixes, saves or private diagnostics.
- Repository visibility changes, Wiki/Discussions activation or posting, automatic merge and a new Pear product-license decision.

## Design Direction

### Roadmap and evidence

The first user flow is download/install Pear, check supported host and runtime readiness, sign into official Steam, install owned Windows Megabonk, play, save, quit and resume with understandable recovery. A native launcher or a fixture demonstration alone does not satisfy it. Keep complete required host-process/module Rosetta independence explicit. Profile groundwork can begin in Phase 1; Phase 2 describes broadening and versioning that capability.

M1 remains technical runtime qualification, including its permitted development-profile scope. Proposed M2 addresses ordinary users without developer enrollment or tooling. Preserve P01-P16 and E01-E05 identities and acceptance dependencies, and distinguish current task status from dated planning snapshots. Correct the stale architecture statement that only documentation exists; `host/` and `tests/` are present.

Use the existing official documentation root instead of moving research history or creating a competing roadmap. Update only the architectural wording required to align technical M1, ordinary-user Phase 1 and the current repository structure. Do not settle #3's contracts here.

### Reuse, skills and tool availability

Keep the existing Wine/FEX/DXMT direction and upstream languages. Require a recorded review of reusable upstream implementation before new subsystem code. Python's standard library fits the small checker and existing repository tooling; this is not a manager-language decision.

Use `skill-creator` when authoring the Pear router. Its source of truth remains `mydocs/skills/pear-apple-tooling/SKILL.md`, discovered through the existing `.agents/skills` and `.claude/skills` symlinks. Keep the router short and place compact pinned metadata in `references/upstream.json`; refer to original technical documents rather than copying their full content.

The reviewed Apple source baseline is [game-porting-toolkit](https://github.com/apple/game-porting-toolkit/tree/4f42344c90be22112f46becc3fb9687f423f2f88), revision `4f42344c90be22112f46becc3fb9687f423f2f88`, plugin manifest version `1.0.0-beta.1`, rechecked September 28, 2026. Stage 2 verifies the pinned manifest, selected files and necessary references. Route these six experts by relevant task:

- `using-metal-validation`: Metal API/shader correctness diagnostics.
- `using-gpucapture`: obtaining a GPU trace.
- `using-gpudebug`: inspecting a trace and its resources.
- `debugging-rendering-issues`: investigating visible rendering defects.
- `presenting-metal-drawables`: drawable presentation, lifetime and frame pacing.
- `managing-metal-cpp-lifetimes`: metal-cpp ownership and lifetime boundaries.

Shader Converter and Metal 4 guidance applies only to actual corresponding implementation. Apple's expert guidance does not supply a CPU translator or replace the qualified DXMT path. Do not start `porting-assistant`, `porting-discover`, `porting-validate`, or create `.porting` state as part of this routing. Pear retains Issue, approval, stage and report authority.

At inspection, the current session exposed no installed Apple expert skills; fixed upstream text was reviewed. Local macOS 26.5.2/Xcode 26.6 lacked `gpucapture` and `gpudebug` on PATH. Their reviewed instructions require macOS 27+. Document appropriate Xcode capture/debug alternatives and recheck the actual task environment rather than treating inspection as a successful capture. Apple installation commands are sourced guidance only, not actions in this task. Developer-tool prerequisites do not establish Pear's end-user minimum OS.

Separate correctness diagnostics from performance measurement and record tools, flags, input identity, result and evidence. An immutable source pin is provenance, not proof that every example is correct: reconcile expert guidance against actual SDK/header/API contracts and record conflicts. Keep raw captures and potentially embedded game data private. Package/license distinctions from the supplied investigation are bounded references; they do not authorize distributing an Apple component.

## Document Location Judgment

The maintainer explicitly selected the existing `docs/` root in the initiating request. This plan records that choice for review under the document-location rule. `mydocs/manual/` continues to contain workflow procedures, not detailed product requirements. No existing research documents move.

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| README summary and links | Official project entrypoint | Users and contributors | `README.md` | Full roadmap in README | Keep a short overview pointing to one detailed source |
| Index, roadmap and narrow architecture alignment | Official product/technical requirements | Users, contributors and implementers | `docs/README.md`, `docs/delivery-plan.md`, `docs/architecture.md` | `mydocs/tech/`, Wiki, new roadmap file | Retain existing public-facing source paths and avoid competing requirements |
| Contributor guide | Official contribution instructions | Human and agent-assisted contributors | `docs/contributing.md` | `mydocs/manual/`, Wiki | Public-facing participation guidance belongs with official docs; tools remain optional |
| Apple tooling guide | Official development guidance with bounded research provenance | Graphics/runtime contributors | `docs/development/apple-tooling.md` | `mydocs/manual/`, external-only notes | Stable task selection and prerequisites need a shared contributor reference |
| Root and scoped rules | Repository operating rules | Coding agents | `AGENTS.md`, `host/AGENTS.md`, `tests/AGENTS.md`, `docs/AGENTS.md` | One large root file; empty future folders | Keep persistent constraints discoverable and put area details beside existing work |
| Pear tooling router and source metadata | Agent skill and technical-reference index | Agents and reviewers | `mydocs/skills/pear-apple-tooling/SKILL.md`, `references/upstream.json` | Duplicated installed skills; global plugin config | Preserve the established skill source of truth and avoid user-wide changes |
| Issue/PR templates | GitHub platform input/review formats | Contributors and maintainers | Existing `.github/` template paths | `mydocs/_templates/` | Preserve the platform/template boundary |
| Task/implementation/stage templates | Reusable work artifact formats | Task workers | Existing `mydocs/_templates/` paths | Skill body copies | Central templates stay authoritative; skills link to them |
| Plans, approval/result records and board | Issue-specific work artifacts | Task requester and reviewers | `mydocs/plans/`, `working/`, `report/`, `orders/` | Official product guides | Preserve auditable work history without duplicating product requirements |

## Expected Changed Files

New:

- `docs/contributing.md`
- `docs/development/apple-tooling.md`
- `host/AGENTS.md`, `tests/AGENTS.md`, `docs/AGENTS.md`
- `mydocs/skills/pear-apple-tooling/SKILL.md`
- `mydocs/skills/pear-apple-tooling/references/upstream.json`
- `tools/check_governance.py`
- `tests/docs/test_check_governance.py`
- `.github/workflows/documentation.yml`

Modified:

- `README.md`, `docs/README.md`, `docs/delivery-plan.md`, `docs/architecture.md`
- `AGENTS.md`
- `.github/ISSUE_TEMPLATE/task.yml`, `.github/pull_request_template.md`
- `mydocs/_templates/task_plan.md`, `mydocs/_templates/task_impl_plan.md`, `mydocs/_templates/stage_report.md`

Review related template/skill indexes and workflow guidance for consistency. Change them only if the approved additions require a minimal reference correction; record any such necessary path before editing. Keep framework attribution, the historical #22 inventory and installed-version provenance intact; this is a Pear customization, not a new framework release installation.

Task artifacts:

- `mydocs/orders/20260928.md` (and the actual day's board if work continues on another date)
- `mydocs/plans/task_m1_25.md`
- `mydocs/plans/task_m1_25_impl.md`, after task-plan approval
- `mydocs/working/task_m1_25_stage1.md`, `task_m1_25_stage2.md`, `task_m1_25_stage3.md`
- `mydocs/report/task_m1_25_report.md`

The artifacts listed here were prospective at planning time and are now recorded in the stage and [final reports](../report/task_m1_25_report.md). Preserve both existing skill discovery symlinks rather than replacing them or creating per-tool copies.

## Tentative Stages

- **Stage 1 - Official documentation root, roadmap and participation**
  - Update the five product/contributor documents, with Phase 1-5, technical M1, proposed M2/U01-U07 and independent R1 boundaries.
  - Verify required user outcomes, existing Issue/dependency preservation, local references, human contributor accessibility and clear information authority.
- **Stage 2 - Scoped engineering rules and Apple expert routing**
  - Update root instructions, add the three scoped rule files, public tooling guide and small router with pinned reference metadata.
  - Verify skill triggers and relative references, source/version evidence, actual tool-availability statements, the absence of a second lifecycle, and preserved discovery links.
- **Stage 3 - Minimal templates and mechanical documentation checks**
  - Extend the five requested templates, implement the offline checker and representative passing/failing fixtures, and add the documentation PR workflow.
  - Verify local links/routing/metadata, template parse/structure, checker rejection behavior and workflow scope. Recheck the integrated document set before final report and PR preparation.

Each stage produces its own report and commit. The implementation plan is written only after this plan is approved; its artifacts, commands and stage transitions follow the repository's separate approval procedure.

## Verification Plan

### Stage Verification

- Stage 1: inspect the final document diff against the issue acceptance criteria; compare all existing P/E issue mappings and acceptance dependencies; verify local links and absence of invented M2/U issue links; run `git diff --check`.
- Stage 2: validate the skill format using `skill-creator` guidance; compare pinned Apple manifest/version, six skill paths and required relative references against official upstream; parse the metadata; verify both symlink targets; review installed/not-installed and unavailable/not-run wording; run `git diff --check`.
- Stage 3: run `python3 tools/check_governance.py` and `python3 -m unittest discover -s tests/docs -p 'test_*.py' -v`; validate Issue/workflow YAML structure using an available parser or documented equivalent; inspect required template sections; run `git diff --check`.

The checker covers an explicit set of official/scoped documents and Pear routing references. Its implementation plan must state whether heading fragments are supported and how Markdown code examples, external URLs and template placeholders are handled. Do not silently claim a general Markdown/link validator. Keep fixture checks offline and independent of games, accounts, hardware or plugin installation.

Meaningful fixture cases include a valid mini-repository, a broken document target, an incorrect discovery-link target, a moving/short revision instead of an immutable commit, and a missing or incorrect selected-skill reference. Verify exclusion handling without hiding real document links. If heading anchors are supported, include valid and invalid same-file and cross-file fragments.

### Integrated Verification

- Map each #25 acceptance criterion to the final files and actual verification result/evidence; carry unperformed work into explicit limitations.
- Recheck live #1/#3/PR/base state before publication and reconcile overlapping index/architecture or daily-board changes without replacing another task's work.
- Confirm no runtime schema, manager-language choice, unregistered GitHub identity, new global plugin setting, empty future implementation folder, game/private data or unrelated path entered the diff.
- Confirm the planned documentation and skill locations match the actual files and both discovery links retain Git mode `120000`.
- Confirm task records, English additions, framework attribution and existing P/E identities remain coherent.
- After commits, `git status --short` is empty in this task's worktree and `git diff --check` passes. The original checkout may retain its existing untracked directories.
- Publish the approved result to `codex/publish-task25` with an open PR to `master`. Record actual remote checks separately; no CI check establishes game execution or agent comprehension.

## Risks

- **Concurrent document edits:** #3 may alter the index and architecture, and several tasks use the same daily board. Recheck before integration; preserve all task records and avoid modifying other worktrees.
- **Technical vs user completion:** development-provisioned #2/M1 results can be mistaken for a downloadable app. Keep evidence scope, proposed M2 and the Phase 1 end-user outcome explicit.
- **Scope creep:** profile/schema work, optional graphics experiments or a new CPU engine would duplicate other Issues. Reference the owners and retain the stated exclusions.
- **Stale or conflicting tooling guidance:** pin and date sources, verify actual availability at use, prefer actual SDK/API behavior when examples conflict, and record unverified cases.
- **Mechanical-check overclaim:** bounded link and metadata tests cannot establish rendering, performance, support or whether an agent understood instructions. Report exactly what was checked.
- **Framework drift:** minimal Pear template/rule customization will differ from the historical adopted release. Preserve provenance and describe the intentional customization in reports rather than rewriting adoption evidence.
- **Sensitive diagnostics:** captures, raw package data and authentication/game content stay outside Git. Store only necessary sanitized provenance and descriptions in task outputs.

## Approval Request

Issue registration and task-start were explicitly approved in this session on September 28, 2026. That approval covers this plan and daily-board preparation, not automatic implementation or future stage transitions.

Approve this task plan's scope, the document-location judgment, three-stage order, exact expected paths, verification approach and exclusions. After approval, `task_m1_25_impl.md` will define concrete stage artifacts, verification commands and commit messages for the separate implementation-plan review. No runtime/product implementation or new milestone registration is requested by this plan.

Approval recorded: on September 28, 2026, the maintainer explicitly instructed this session to proceed in response to the task-plan approval request. The scope and document-location judgment above are approved. The [implementation plan](task_m1_25_impl.md) was the next review artifact; this task-plan approval did not itself start Stage 1. See the [Stage 1 report](../working/task_m1_25_stage1.md) for the subsequent approved implementation and results.
