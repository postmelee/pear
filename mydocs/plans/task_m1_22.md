# Task #22 — Adopt Hyper-Waterfall in English

GitHub Issue: [#22](https://github.com/postmelee/pear/issues/22)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

## Purpose

Install the approved English Hyper-Waterfall v0.3.0 operating environment, with immutable source provenance and shared agent skills. Establish the development workflow without changing Pear product code or technical requirements.

## Background

The maintainer requested framework adoption and English repository artifacts. A complete patch preview, source inventory, placeholder choices and three adoption stages were presented. The maintainer explicitly approved proceeding with that reviewed adoption on September 27, 2026. This document records the approved scope; it does not expand it.

## Scope

### Included

- Release v0.3.0 at `83836828a4da24385d0410515d35ee43946b981f`, English locale.
- All manifest operating files, relative skill-discovery symlinks and generated version state.
- Approved repository-specific substitutions and framework MIT notice.
- Issue-backed plans, three stage reports, final report, daily board and open PR.

### Excluded

- Product code, README and `docs/` edits; a new product-documentation-root decision.
- Runtime qualification, application implementation, Steam/game data, changes to repository visibility.
- New labels, milestone renaming or a new release branch.

## Design Direction

Preserve source text, replacing only declared placeholders. The designated AGENTS project section records English artifacts, private data boundaries, accurate support claims, normal platform protections, optional language choices and framework attribution. The current coding environment requires `codex/task22` and `codex/publish-task22`; the branch examples in copied manuals remain intact. Keep `master` as the existing base and release branch, explicitly disabling same-branch release-promotion examples until a separate decision.

Use an isolated worktree so existing private experiments stay outside the adoption diff. The strict-manifest installation and the lifecycle-required task records are separately identifiable. No product artifacts are installation side effects.

## Document Location Judgment

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| Manifest operating documents | Framework operating material | Contributors and coding agents | Manifest-defined targets | None in strict adoption | Required by pinned manifest |
| Issue-specific plans/reports/board | Work artifacts | Reviewers and task workers | `mydocs/plans`, `mydocs/working`, `mydocs/report`, `mydocs/orders` | GitHub-only text | Normal lifecycle workflow requires persistent records |
| Existing product documentation | Existing project material | Users and contributors | Unchanged | Relocation deferred | Adoption must not choose or change a product documentation root |

## Expected Changed Files

New: `AGENTS.md`, `CLAUDE.md`, `.github/ISSUE_TEMPLATE/task.yml`, `.github/pull_request_template.md`, manifest-defined `mydocs/` files, `.agents/skills`, `.claude/skills`, `.hyper-waterfall/version.json`.

Modified existing files: none.

Task artifacts: `mydocs/orders/20260927.md`, `mydocs/plans/task_m1_22.md`, `mydocs/plans/task_m1_22_impl.md`, `mydocs/working/task_m1_22_stage{1,2,3}.md`, `mydocs/report/task_m1_22_report.md`.

## Tentative Stages

1. Install English rules, GitHub templates, output templates, manuals and folder placeholders/guides; verify exact source/substitution parity.
2. Install shared skills and discovery symlinks, then record real installation timestamps and provenance; verify all manifest targets.
3. Perform integrated validation, record results, and prepare the open PR.

## Verification Plan

### Stage Verification

- Stage 1: compare installed files against immutable English sources plus the approved substitutions; inspect English text and staged diff hygiene.
- Stage 2: compare full installed file set, check relative links, validate version-state JSON and ISO-8601 timestamps, and run the pinned framework CLI doctor.
- Stage 3: repeat integrated inventory/parity checks, confirm existing product files unchanged, verify report links, and verify clean worktree before publication.

### Integrated Verification

The 25 manifest entries expand to 51 source files and two symlinks; the generated version record adds one file. Separate task records must account for every additional path. No unresolved project-specific placeholder or private experimental file may enter the change. `git diff --check` and the final clean-tree check must pass.

## Risks

- The framework's copied release-promotion examples are inapplicable to the current single-branch layout; the designated project rules explicitly prevent executing them.
- CLI display headings remain Korean upstream; installed documents are English. CLI display text is not committed as a report.
- Published manifest checksums are incomplete and default-source hashes do not attest the English pack. Pin the source commit and verify selected files directly.
- Framework installation does not establish a working runtime or a distributable app.

## Approval Record

The maintainer approved the concrete adoption review, its file set, repository substitutions and tracked three-stage procedure before any repository application. The plans materialize that approved review. New product tasks and any scope change require their own review. No merge approval has been requested or inferred.
