# Task #77: Publish native component repositories

GitHub Issue: [#77](https://github.com/postmelee/pear/issues/77)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

## Purpose and Background

Publish the four integrated native component source repositories and reconcile
current source-access guidance. Task75/PR76 and all component PR1s are merged.
The [integrated audit](https://github.com/postmelee/pear/issues/75#issuecomment-6295812832)
provides the bounded baseline; it is not reused as current mutation authority.
The requester's 2026-10-21 instruction explicitly authorizes public conversion,
its immediate recheck, and README/related-document updates with preservation.

## Scope

Included: fresh refs/settings/exposure comparison; four private-to-public
transitions; anonymous source-access verification; existing guide updates;
independent review, reports, commits and documentation PRs.
Excluded: runtime source/behavior or pins, generated/header/license changes,
default-branch renames, Actions configuration, releases, #47 app/selection,
installs/games/saves/prefixes, builds/runs/signing and deletion/cleanup.

## Design Direction

Reuse Task75's exact integrated trees and bounded audit. Current guidance must
separate public source access from retained-input bootstrap and game qualification.
Historical plans/reports/provenance remain dated evidence. Keep existing upstream
languages and licenses; no subsystem implementation or new technical tool is
needed. FEX/DXMT prohibit AI code contributions; this change is documentation only.
Read root/docs rules, README, docs index, architecture, delivery plan, Task75
plans/latest reports, contributor checks and task/retention workflow guidance.

## Document Location Judgment and Expected Changed Files

| Files | Classification / audience | Selected location | Alternative and reason |
|---|---|---|---|
| Pear README.md | Project entry / contributors | Existing root README | No new overview needed |
| Pear docs/README.md, docs/architecture.md, docs/development/rosetta-free.md | Official index/design/development | Existing docs paths | mydocs is inappropriate for current guidance |
| Wine README.md, pear/README.md | Component entry/maintenance | Existing component paths | No ownership or source relocation |
| FEX Readme.md, docs/pear/README.md | Component entry/maintenance | Existing component paths | Preserve upstream structure and notices |
| DXMT README.md, pear/README.md | Component entry/maintenance | Existing component paths | Preserve upstream structure and notices |
| Runtime README.md, docs/development.md | Assembly/development | Existing component paths | Preserve exact execution/input recipes |
| mydocs/plans/task_m1_77*.md, working/task_m1_77_stage*.md, report/task_m1_77_report.md, orders/20261021.md | Task records / maintainers | Existing mydocs types | Do not replace current product docs with task prose |

Update only access/status wording and links to merged evidence. Any stale WGI
source-correspondence sentence in current guidance may point to Task75's existing
result; it must not imply a natural WGI invocation or change execution recipes.
The user's request approves these existing-document locations and bounded scope.

## Artifact Lifecycle

| Artifact | Class / consumer | Identity/recovery | Retention/release |
|---|---|---|---|
| Task56/75 roots, inputs, outputs, existing app/game state | Protected / ongoing debugging and #47 | Existing manifests and original paths | Preserve entirely; no release authorized |
| New Pear task worktree and four sparse documentation checkouts | Text-only / Task77 review | Base commits and Git-backed staged changes | Keep until PR integration and retention review |
| Pre/post audit and checks | Evidence / Task77 | SHA-256 inventory outside public Git; sanitized reports in mydocs | Preserve final receipt; no old evidence deletion |

No runtime copy or build. Pear checkout tracked logical size: 103,888,234 bytes.
Peak incremental allowance: 512 MiB including sparse checkouts, indexes, small
network responses and retained evidence; available 16,461,357,056 bytes at initial
planning. This is not a build budget. No APFS clone savings or reclaimed capacity
is assumed. Runtime/input storage planning is not applicable to this text task.

## Stages and Verification Plan

1. Freeze current baseline and prepare documentation changes. Recheck refs,
   publication surfaces and protected roots. Review all new text and links before
   changing visibility; record evidence and commit the preflight stage report.
2. Recheck each repository immediately before setting visibility public. Verify
   authenticated metadata, anonymous commit/raw-document access and unchanged
   source/default/feature settings. Commit conversion report plus reviewed docs.
3. Run document/link/notice checks and independent review; publish documentation
   PRs, record remote checks and final report. Integrate reviewed documentation
   through PRs within the requested update scope, preserving stage history.

Required checks: git diff --check; python3 -B tools/check_governance.py;
python3 -B -m unittest discover -s tests/docs -p 'test_*.py' -v;
python3 -B tools/check_source_notices.py --base cc23a3c0a0a48624f55f75f2cf310c4a41d95850.
Manually review changed anchors/external links, documentation-only diffs and
component history/notice preservation. Reuse prior runtime evidence only because
no executable/source/input bytes change; no new runtime verification is claimed.

## Risks and Approval

Public history can be copied; a later private setting cannot recall external
copies. The requester explicitly authorizes publication after the bounded audit.
Original FEX template holder/introducing commit gaps, retained lower-layer/tool
inputs and unproved game behavior stay explicit. Unexpected refs or exposure
changes require review before mutation. Verification/report/commit boundaries
remain, with work limited to the newly approved publication/document update.
