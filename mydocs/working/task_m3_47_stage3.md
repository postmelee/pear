# Task #47 Stage 3: Final Preview delivery and user guidance

GitHub Issue: [#47](https://github.com/postmelee/pear/issues/47)
Implementation plan: [task_m3_47_impl.md](../plans/task_m3_47_impl.md)
Stage: 3 — implementation and required verification complete, October 15, 2026.

## Stage Purpose

Qualify the Rosetta Preview's sustained play, save/relaunch and ordinary-user
installation; connect the approved public downloads and catalog to that evidence.
Context: root/docs/tests rules, approved plans and reuse investigation, Stage 1/2
reports, dated Stage 3 preparation, central templates and the task-stage-report,
task-final-report and todo skills. The requester authorized final publication.

## Artifacts

| File | Change summary |
|---|---|
| `preview/` and candidate/runtime workflows | Source-built runtime, safe migration, consent/progress, login-close fix, Pear naming and Steam window feedback; exact signed source remains e574ba1 |
| `README.md`, `docs/README.md`, player/release/contributor guides | Public download routing, component versions, requirements and bounded evidence |
| `docs/compatibility/`, `tools/compatibility.py`, catalog assets | Existing approved site with real DMG/CLI links and an additional dated owner report |
| `tests/docs/`, source notices | Download-link regression contract and preserved Pear/upstream attribution |
| [Dated preparation record](task_m3_47_stage3_preparation.md) | Candidate evolution, failures, reused evidence and signed/public receipts |

## Body Change Scope / Lossless Preservation

The approved official documentation destinations are unchanged. Current release
availability replaces stale preparation language; historical reports keep their
original inputs. Latest master entry points and #48 retention records were
merged with both tasks' board entries preserved. No other worktree was edited.
The approved design and three download tabs are reused; Homebrew remains planned.
The final documentation/catalog revision does not rebuild or modify signed assets.

## Verification Results

Final delivery: Pear 0.1.0-preview.3, source
`e574ba17fa3e3b9b9598d5c6c376ce6f770d6ef8`,
[release](https://github.com/postmelee/pear/releases/tag/v0.1.0-preview.3).
Runtime: `pear-wine11-cw26.3-dxmt0.80-signed-v3`, Wine 11.0 / CodeWeavers 26.3
FOSS and DXMT 0.80 with Rosetta. Runtime archive SHA-256:
`eb32a9ef8012216d11348c1af089254f2127f28e2b330cf4f1c700f41967d7b0`;
matching source kit:
`4577a0d67c82e649194ce85fa932039598243c2d2afcde252c6cf014f5199ec3`.
Both remain immutable preview.2 assets. Tested physical host: Apple M4 Pro,
24 GB, macOS 26.5.2 (25F84). No second physical Mac was available.

| Case | Result and evidence boundary |
|---|---|
| S3-play | Owner confirmed the requested 20+ minutes of actual play, excluding idle/menu time, on signed-v3 with input/audio and no reported problems. Exact duration/graphics settings and frame-time metrics were not instrumented; no performance claim. |
| S3-resume | Final signed app reopened the game; owner confirmed menu/input/audio and latest progress, then normal game/Steam/Pear exit. Earlier actual local restoration remains in Stage 2. |
| S3-clean | Owner confirmed all requested final preview.3 public-download, fresh standard-account setup, official Steam/game launch and save/relaunch items without problems, then deleted the test account. Same Mac with existing host Rosetta/Xcode; no developer tools or security bypass were required in the user flow. Account identity, screenshots and exact per-step timestamps were not collected. This is owner-reported clean-user evidence, not independently reproduced hardware evidence. |
| S3-docs | Real release links, requirements, components, CLI/data preservation and recovery instructions reviewed; generated site navigation/allowlist checked; Mac/CLI tab and visible download link inspected in browser. |
| S3-release | Developer ID, Apple notarization, local Gatekeeper/staple/distribution and CLI explicit notarization checks passed. All five public assets anonymously downloaded and matched size/SHA-256; matching source provided. |

Evidence reuse: runtime gameplay applies to the unchanged signed-v3 payload.
Preview.3 presentation/name changes received new app/CLI/DMG signing and checks,
actual signed app launch/normal exit and final clean-user verification. Stage 2
recovery retains its exact candidate/seam limitations; later migration fixtures
and actual copied-environment preservation checks cover the changed transition.
No historical pass is renamed as a new execution. The game report retains
`reported` rather than independent reproduction/blanket qualification.

[Final candidate CI](https://github.com/postmelee/pear/actions/runs/38669041530)
passed portable 68 checks, macOS Rust 30 checks/Swift fixtures, and the protected
signing job. App/CLI/DMG notarizations were Accepted:
`4002ce10-2331-4ca6-ac92-999427cfbe09`,
`c342fc49-36b8-41dc-8fbc-4cfe297b523d`,
`99ab2451-0d69-41bb-aa2c-f572481f5ce6`.
These are reused exact-artifact results, not a rebuild of the final documentation.

Final documentation checks executed:

```sh
python3 -B tools/check_governance.py
git diff --check
git diff --name-only
git status --short
python3 -B -m unittest discover -s tests/docs -p 'test_*.py'
node --test tests/docs/test_steam_search.cjs
python3 -B tools/check_source_notices.py --base origin/master
python3 tools/compatibility.py --check --site .build/task47/final-catalog
```

Results: governance 37 documents / 360 local targets; 94 Python tests and 6 Node
search tests passed, none skipped. Source notices: 48 changed source files,
zero errors; 148 upstream notice copies remain preserved manual-review inputs.
Catalog: two dated reports, one Steam App ID, 13 allowlisted output files.
Whitespace and local report-link checks passed. Browser confirmed the approved
layout and exact DMG/CLI routes. Remote Pages deployment is a post-merge operation
and must be checked separately before claiming the site is live.

## Residual Risks

- Same-Mac clean-user reproduction shares OS, hardware, Rosetta and host tools;
  another physical Mac and wider compatibility remain unverified.
- Steam can update independently. Controller, Cloud synchronization correctness,
  overlays, anti-cheat, other games and comparative performance are not qualified.
- Window detection means a matching visible window, not readable library readiness.
- Homebrew and full in-app removal/general runtime repair are not implemented.
- No continuous source-freeze-to-manual-input latency was measured; recorded
  process-launch/window intervals are not that metric.

## Retention Handoff

Owner/consumer: #47 release maintenance. Preserve signed assets, matching source,
private verification receipts under ignored `.build/task47/stage3/launch-status`,
authenticated working state and save-recovery archives until their release or
restoration conditions are independently resolved. Public source/assets provide
binary/source recovery but do not replace private saves or local evidence.
The requester already deleted the test account; no further account deletion was
performed or space recovery claimed. This checkout must remain while retained
ignored evidence/private state depends on it. New catalog output is approximately
1.8 MiB displayed by du, within the 50 MiB budget; filesystem free was about
6.5 GiB, not a measurement of cleanup. No runtime/prefix copy was created.

## Impact on Next Stage

All three implementation stages are complete. Integrate through the reviewable
PR, deploy the master-only allowlisted catalog and verify public HTTP/download
routing. Do not change the immutable release source/tag to the documentation SHA.

## Approval Request

The requester explicitly asked to finish final records, release routing and
catalog publication. This report supplies the concrete reviewed scope for that
publication; no new runtime qualification or other-task work is requested.

## Public form check

The live default-branch Show and tell form was inspected in GitHub on October 15.
Steam App ID, date, versions, host, result, individual checks and privacy consent
were rendered. The catalog now links that form as live; its local draft remains
manual and never auto-submits. The fallback is still covered by tests.
