# Task #25 - Stage 1 report

GitHub Issue: [#25](https://github.com/postmelee/pear/issues/25)
Implementation plan: [task_m1_25_impl.md](../plans/task_m1_25_impl.md)
Stage: 1 - Official documentation and roadmap
Date: September 28, 2026
Status: Complete; approval to begin Stage 2 is pending.

## Stage Purpose

Establish the official documentation root and one roadmap, separate technical M1 from the complete ordinary-user experience, and provide a contribution path for people using their chosen tools. The maintainer explicitly approved the implementation plan and Stage 1 start in this session before these edits.

## Artifacts

| File | Change Summary |
|---|---|
| [README.md](../../README.md) | First-user goal, technical M1 scope, short Phase 1-5 summary, dated host-probe status and contributor links; 115 lines |
| [docs/README.md](../../docs/README.md) | Official docs root, requirements/status/evidence/task-record authority, research limits and recommended Discussions/Wiki roles; 38 lines |
| [docs/delivery-plan.md](../../docs/delivery-plan.md) | Single expanded roadmap; five phases; proposed M2/U01-U07 scope, dependencies and registration follow-up; preserved P/E backlog; 157 lines |
| [docs/architecture.md](../../docs/architecture.md) | Narrow M1, CLI/app, G4 and existing host/tests wording alignment, with updated review dates; 221 lines |
| [docs/contributing.md](../../docs/contributing.md) | Human participation, internal/external workflow boundaries, actual verification evidence, privacy, upstream policy and documentation placement; 61 lines |
| [Task plan](../plans/task_m1_25.md), implementation plan and [daily board](../orders/20260928.md) | Approval and Stage 1 completion state for #25; no other task row changed |

All five product/contributor documents match the approved location judgment. No existing document was moved. Official guidance stays in `docs/`; this report and the approval records stay in `mydocs/`.

## Body Change Scope / Lossless Preservation

The README retains the project vision, values, initial runtime direction, bounded Rosetta-based observations and unresolved license choice. Its phase table summarizes and links to the detailed delivery plan instead of defining another roadmap.

The delivery plan retains all 21 P01-P16/E01-E05 rows byte-for-byte, including existing issue identities and acceptance dependencies. The entire M1 completion section is unchanged. Proposed M2/U01-U07 are explicitly unregistered planning candidates; no new milestone, implementation Issue, registry or schema was created. The first-user proposal's installation, official Steam, owned-game, recovery and clean-setup requirements are now tracked here without relying on temporary research paths. Obsolete statements about missing signing identities or an uncompleted #2 were not imported.

Architecture changes are limited to M1 terminology, the CLI-first technical sequence versus Phase 1's app outcome, the bounded G4 outcome, the existing host/tests state and review dates. Requirements, language decisions, proposed data contracts and the seven checked technical sections remain unchanged. #1 source/pinning and #3 schema/manager-language ownership remain intact.

The contributor guide distinguishes external PRs from internal Hyper-Waterfall task artifacts. It requires no Codex or paid AI service and preserves the upstream contribution-policy boundary. The initial index's engineering/research links are retained. Discussions and Wiki roles are guidance only; no platform setting or content was changed.

## Verification Results

### Planned command execution

Ran the exact Stage 1 verification block in the approved implementation plan from the task worktree root after the final product-document corrections. It runs the Python dependency-row/local-target check, `git diff --check`, and `git diff --stat`.

Result:

```text
PASS: 21 preserved dependency rows; 49 simple local link targets
```

The command block exited zero; `git diff --check` produced no warnings. The pre-staging diff stat excludes the newly created contributor guide by Git's normal untracked-file behavior; that guide was included in the 49-target check and in the final staged-file review.

### Semantic and preservation review

| Topic | Method | Result / Evidence |
|---|---|---|
| M1 acceptance preservation | Compare the complete First-milestone completion section to `a75237a` | PASS - unchanged requirements and final-artifact/requalification boundary |
| Existing implementation/research dependencies | Exact baseline row comparison in the planned command | PASS - 21 matching P/E rows |
| Phase 1 and proposed M2 | Compare the five edited documents to #25 and the maintainer-provided application proposal | PASS - runtime vs ordinary-user evidence distinguished; U01-U07 retain all acceptance dependencies and remain unregistered |
| Phase 2-5 and early groundwork | Read final phase table and ownership notes | PASS - versioned profiles, Steam/evidence matching, reviewed community contributions and sustained maintenance; Phase 1 groundwork allowed |
| Local links and fragment | Planned file-target check plus manual heading inspection | PASS - 49 simple relative targets; `architecture.md#rosetta-independence-evidence` matches the actual heading |
| Architecture scope | Compare sections 2, 4, 5, 6, 7, 9 and 10 to `a75237a` | PASS - all seven sections unchanged; no schema or language selection changed |
| Official root and information authority | Review approved location judgment against actual files/index | PASS - docs, GitHub state, qualification evidence and task artifacts have distinct roles |
| Contributor access and policy | Review human participation and internal/external PR boundaries against existing PR manual | PASS - no AI tool/subscription requirement and no internal report bundle imposed on external PRs |
| Private/unrelated scope | Inspect changed paths and compare protected areas to the base | PASS - no host/tests, planning JSON, root rules, skill links or other implementation changes; original checkout still has only its existing untracked `analysis/` and `research/` |
| English and whitespace | Inspect additions and scan for unintended Korean text; Git whitespace check | PASS - English repository additions and clean diff |

Two independent read-only reviewers checked cross-document consistency and policy scope. Their two wording findings were corrected before the final command run: FEX restrictions apply to code contributions rather than all work, and private signing material is excluded without forbidding an approved release's required provisioning content. No implementation defect or missing Stage 1 requirement remained in those reviews.

### External policy and live-state evidence

On September 28, 2026, the official FEX GitHub API resolved main to `59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa`. Its [pinned CONTRIBUTING.md](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/CONTRIBUTING.md), blob `f0a3c2c511e3209e4959d2b723f74b23b8fa6f70`, is 37 bytes and states: "No AI/ML/LLM/etc code contributions." The contributor guide records this as an upstream code-contribution restriction separate from licensing; it does not invent other contribution permissions or a workaround.

Live Pear lookup confirmed #25, #1 and #3 open, #2 closed and no open PRs at the check. Remote master remained `a75237a6f67a3ade71fcef6068a228686958efe2`. The [existing #2 report](../report/task_m1_2_report.md), rather than stale unchecked Issue-body boxes, provides the bounded host result cited by the product documents.

### Verification limitations

This stage did not run game, Steam, Wine/FEX/DXMT, GPU-capture, signing or performance tests and adds no new runtime qualification. The temporary link check covers simple inline local targets in the five edited documents; it is not a general Markdown parser or comprehensive anchor checker. The new fragment was reviewed manually. Stage 3 will provide the maintained bounded checker and rejection fixtures.

No new CI workflow exists yet and no CI result is claimed. Source, host, game and ordinary-user completion remain distinct. No general end-user distribution, all-Mac compatibility, or power/performance advantage is established by this documentation work.

## Residual Risks

- #3 can later edit the same index/architecture paths. Recheck merged state and resolve only relevant integration overlap before publication, preserving the other task's work.
- M2/U01-U07 are still unregistered candidates. Registration is a separate follow-up, and these rows cannot be treated as started or completed Issues.
- FEX policy and tool availability can change; the documented policy observation has a pinned source and date. Recheck the target project's policy before any upstream submission.
- Root/scoped agent rules, Apple tooling routing and template/checker changes belong to the next approved stages. This stage does not imply they have been applied.

## Impact on Next Stage

Stage 2 should link the new official root and contributor guidance, retain the Phase 1 priorities, and apply only the planned scoped rules and Apple technical routing. Keep optional shader experiments and the `.porting` lifecycle outside the critical path. Add the public tooling guide link to the existing index without introducing a second roadmap or moving research documents.

## Approval Request

Review the Stage 1 documents and verification results, then explicitly approve proceeding to Stage 2. This report does not authorize the next stage, PR publication or merge by itself.
