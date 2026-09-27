# Task #22 — Adoption implementation plan

Task plan: [task_m1_22.md](task_m1_22.md)
GitHub Issue: [#22](https://github.com/postmelee/pear/issues/22)
Milestone: M1

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | English operating documents | Rules, GitHub forms, templates, manuals and artifact placeholders | Exact approved-substitution parity; English text; diff hygiene |
| 2 | Skills and provenance | Shared skills, discovery links, actual version state | Complete manifest coverage; link targets; JSON dates; CLI doctor |
| 3 | Integrated adoption evidence | Hash inventory, stage/final reports and PR | Product preservation; complete inventory; report links; clean tree |

## Document Location Check

All operating files follow manifest targets. Plans, reports, the file-hash inventory and the daily board are normal Issue work records in their planned `mydocs/` folders. No product documentation changes.

## Stage 1 — English operating documents

Copy all approved source-backed candidates except `mydocs/skills/**`. Preserve every existing product file. The exact release source is v0.3.0, commit `83836828a4da24385d0410515d35ee43946b981f`; apply only the substitutions from the approved review.

Verification: compare each installed byte sequence with the approved preview and source/substitution result; scan for Korean prose; stage only the explicit task paths and run `git diff --cached --check`.

Commit: `Task #22 Stage 1: install English operating documents`.

## Stage 2 — Skills and provenance

Copy `mydocs/skills/**`, create both relative discovery symlinks, and create `.hyper-waterfall/version.json` with actual ISO-8601 timestamps. Preserve all Stage 1 files.

Verification: ensure all 54 expected file/link targets exist; validate symlink targets and version-state fields; run `node <pinned-framework>/bin/hyper-waterfall.js doctor --repo <task-worktree>` and inspect its results. Compare source-backed files and record any upstream diagnostic limitations.

Commit: `Task #22 Stage 2: install shared skills and version provenance`.

## Stage 3 — Integrated verification and publication

Create `mydocs/working/task_m1_22_inventory.json` with relative source paths, selected-source and installed SHA-256 hashes, symlink targets and generated-state identity. Review this inventory against the full pinned manifest. Record three stage reports and a final report with actual results and remaining limitations; update the board and publish an open PR from `codex/publish-task22` to `master`.

Verification:

- Compare the complete manifest expansion, exact approved substitutions and installed files; no extras except named task records.
- Check actual version timestamps and both relative symlinks; inspect Git mode 120000 after staging.
- Compare `README.md`, `docs/` and `.gitignore` against the starting commit.
- Verify task links, selected locale, private-data exclusions and `git diff --cached --check`.
- Require a clean task tree before pushing; verify remote PR base/head and repository privacy.

Commit: `Task #22 Stage 3 + final report: verify and document framework adoption`.

## Stage Dependencies

Stage 2 follows verified Stage 1; Stage 3 follows verified Stage 2. The maintainer's approval of the concrete adoption review covers these same three stages. No new product scope is introduced. Any deviation beyond that approved installation is held for separate review.

## Risks and Responses

The upstream manuals retain release-branch examples; the designated project rules prohibit same-branch promotion on Pear. The CLI has Korean display headings although installed sources are English. Published checksums do not fully cover localized sources, so compare against the pinned Git commit and record local digests. A successfully adopted workflow does not qualify the runtime.

## Approval Record

This implementation plan materializes the three stages already included in the approved concrete adoption review. The open PR remains subject to normal review; no self-merge is authorized.
