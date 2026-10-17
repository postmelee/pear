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

## Download layout follow-up — 2026-10-16

The requester approved the second local preview and Pages publication. The
original tabs, install copy and download-button order remain. Requirements now
appear under System requirements; Wine 11.0 / DXMT 0.80 appears under native
collapsible Release details. Home download routing remains unchanged.

Verification: generated download.html matches the approved local preview byte for
byte; 94 documentation/catalog Python tests and 6 Steam identity JavaScript tests
passed. Governance checks passed (37 documents, 360 local targets), as did
`git diff --check`. No app/runtime input or artifact changed. The existing
master-only Reviewed compatibility catalog workflow is enabled and will deploy
this source revision without app signing or builds.

## README follow-up — 2026-10-17

Following requester confirmation that PR #58 was merged, the README homepage label
is Website & game reports. The dated native experiment narrative is replaced by
a concise source-ownership/development-validation summary, retaining explicit
incomplete gameplay and full no-Rosetta qualification. Existing #58 guide routing
and exact Preview download URLs remain. The exact #56 report is linked for scope.
Governance passed (37 documents, 372 local targets); incremental source notices
and diff checks passed. This documentation-only change performs no runtime tests.
The repository About homepage is https://postmelee.github.io/pear/.
No material build output or change to retained private state.

## Social-preview follow-up — 2026-10-17

Applied the requester-approved 1200×630 composition of the Pear wordmark and
existing supplied pear image. Shared Open Graph and Twitter large-image metadata
now reference the absolute public social-card.png URL on all six generated pages.
The favicon and visible page layout are unchanged. No external image service,
new dependency, runtime rebuild or game qualification is involved.

Verification: 94 documentation/catalog tests passed; governance passed (37
documents, 372 local targets); incremental notices against 5daa083 and diff checks
passed. Parsed all six HTML heads, checked 1200×630 PNG dimensions and exact copied
image/favicon bytes. The image SHA-256 is
`f6820a737ff3b77b489108cdd102d07b33b603366b27900d70636fb428e96cc6`.
The requester visually approved the composition before implementation. Pages-only
publication and public byte verification follow integration. Sharing services may
retain earlier previews until their caches refresh; no service-specific rendering
is claimed. Retention: keep the small public asset; generated local site is
disposable after verification. Private evidence and other tasks are untouched.

## Social-preview revision — 2026-10-18

Applied the approved v3 image: black 140 px Pear title and gray 35 px subtitle
“Play Windows Steam games on Mac”. The existing pear and favicon are preserved.
Shared image URLs now include v=20261018 and alternative text includes the subtitle.
94 catalog/document tests, governance (37 documents, 372 local targets), incremental
notices against 599c382 and diff checks passed. All six HTML heads and the exact
approved 1200×630 PNG bytes were verified; SHA-256: `d794aa23682f82296a9eb430eff8afccb1ccf9bd6b2ad515c95d0f93263f8511`.
The requester approved the visual before implementation. Existing Pages workflow
performs publication after integration; third-party cache refresh remains external.
No runtime changes. Retain public PNG; generated site is disposable after live
verification. Private state and other worktrees remain untouched.

## macOS floor investigation and candidate — 2026-10-18

Pinned public runtime cache was SHA-256 verified against runtime_pin.rs. All 46
Mach-O entries were inspected: 42 declare 14.0, two 12.0 and two winemetal.so copies
15.0. Both winemetal bytes match the pinned archive. Therefore unchanged runtime
reuse selects 15.0, not 14.0, as the candidate floor. This is static compatibility
evidence, not older-OS gameplay qualification. No runtime or private state changed.

App/CLI build targets and candidate package text now target 15.0; preview.4 keeps
all preview.3 runtime pins. Existing 68 portable tests, incremental source notices
and whitespace checks passed. The existing macOS 26 builder remains pinned; a new
macOS 15 job consumes its exact artifact, checks hashes/targets, executes read-only
CLI and isolated first-run app startup, audits and starts the unchanged Wine under
Rosetta. Signing depends on this job and retains existing protected approval.
Hosted execution is pending; public docs still describe released preview.3.

## macOS 15 and Homebrew delivery — 2026-10-18

Preview.4 source d0cbbbc4987850daf98ed7ded94951bcfff233ed rebuilds only the
Pear app/CLI for macOS 15.0. The signed-v3 Wine 11.0 / DXMT 0.80 runtime is
unchanged. Its verified SHA-256 is
`eb32a9ef8012216d11348c1af089254f2127f28e2b330cf4f1c700f41967d7b0`.
The highest deployment target in its 46 Mach-O files is 15.0, so 14.0 is excluded.

Verification and release:
- [Candidate CI](https://github.com/postmelee/pear/actions/runs/39047129494):
  68 portable tests, build, macOS 15.7.9 arm64 CLI/app process startup, exact
  archive audit and Wine 11.0 execution under Rosetta passed.
- [Signing CI](https://github.com/postmelee/pear/actions/runs/39047911515):
  requester-approved protected environment; app, CLI and DMG Apple notarization
  accepted. Existing reviewer and branch protection retained.
- [Final artifact CI](https://github.com/postmelee/pear/actions/runs/39048418706):
  same signed d0cbbbc artifacts passed Gatekeeper, signatures, tickets, CLI and
  isolated app process startup on macOS 15.7.9. Workflow dd4d07d consumes the signed
  artifact directly without rebuilding; unchanged runtime evidence is reused.
- Local macOS 26.5.2: final DMG verification, Gatekeeper/tickets/signatures, CLI
  version/setup-info and isolated app process startup passed. No personal prefix
  or running game was used.
- Public [preview.4](https://github.com/postmelee/pear/releases/tag/v0.1.0-preview.4)
  includes DMG, app/CLI archives, exact source archive and SHA256SUMS. DMG SHA-256:
  `1ff1588a24cfe7510d80fe0d78ae19a919d401231bd25b372155df2772342631`.
- [Homebrew cask](https://github.com/postmelee/homebrew-tap/blob/dd338ce/Casks/pear.rb)
  uses that DMG and checksum, arm64 and Sequoia constraints. Homebrew style and
  online audit passed. Install into a disposable app directory, Gatekeeper/CLI
  execution and uninstall passed; /Applications/Pear.app and private data were
  preserved. A version-scoped prerelease allowlist admits this intentional
  preview; livecheck is skipped until a reviewed update. No zap/data deletion.
- Documentation/catalog suite: 94 tests; Steam identity search: six Node tests;
  governance: 37 documents / 373 local targets; incremental notices and diff
  checks passed. Existing download layout retained with Homebrew command/copy
  control, current links and scoped requirements.

Limits: no macOS 15 Steam UI/gameplay, exact 15.0 execution or fresh-user test of
preview.4. Prior preview.3 game evidence on macOS 26 retains its original scope.
No new gameplay/performance claim. Startup checks only establish process/CLI
execution. Continuous user-operable game timing is not applicable to this bounded
packaging change; hosted build/signing intervals are retained in linked CI runs,
with human approval separate. No latency improvement claim.

Retention handoff: public release assets/source/checksums and tap are durable
inputs; hosted artifacts expire after 14 days. Local .build/preview4-release holds
small downloaded final packages, receipts, tap clone and generated site for this
handoff; disposable after publication verification. Temporary test cask was
uninstalled. Preserve the cached pinned runtime, personal authenticated prefixes,
saves and all prior recovery evidence. No shared runtime or other task was edited.
Website/README publication proceeds through the integration PR and existing
Pages-only workflow; the public release and Homebrew tap are already available.

### Owner confirmation — 2026-10-18

After opening the final signed preview.4 app with the existing local installation,
the requester reported no problems in response to the Megabonk gameplay and saved
state check. This is owner-confirmed local macOS 26 evidence, not macOS 15 gameplay
evidence. No new measured-duration claim is made.

The requester proposed the first v0.1.0 release with the macOS 15 minimum retained,
and requested local website review before deployment. Website publication is held
for that review. Existing preview.4 artifacts and links remain unchanged until the
versioned v0.1.0 app/CLI has been built, signed and checked; the Wine/DXMT runtime
can remain pinned.

### Stable candidate preparation — 2026-10-18

Requester approved v0.1.0 publication and the reviewed website. Package version
is 0.1.0, CFBundleVersion is 5, and app presentation no longer says Preview.
Runtime, data paths and bundle identifier are unchanged. Current download links
and Homebrew guidance are prepared for v0.1.0, but not published before signed
artifact acceptance. 68 portable fixtures, 94 documentation tests, governance,
incremental notices and diff checks passed. Existing signed preview.4 remains
available while this candidate builds.
