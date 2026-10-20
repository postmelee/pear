# Task #47: Rosetta Preview delivery

GitHub Issue: [#47](https://github.com/postmelee/pear/issues/47)
Milestone: M3 — Rosetta-based Megabonk Preview

## Work Summary

Three stages deliver a small Pear app and optional shared CLI for official Windows
Steam, with a source-identifiable Rosetta/Wine/DXMT runtime, preserved state,
ordinary-user signed downloads and a public documentation/catalog entry point.
The final downloadable version is 0.1.0-preview.3 (e574ba1); current website and
reporting changes do not alter those signed bytes or establish Rosetta-free M1.

## Changed Files and Impact Area

| Path | Change summary | Impact area |
|---|---|---|
| `preview/` | Rust core, thin AppKit UI, runtime build/patch/notices, packaging/signing | Installation, official Steam launch, recovery and migration |
| `.github/workflows/` | Portable/macOS candidate checks, protected signing and master-only Pages | Distribution and source-notice enforcement |
| `README.md`, `docs/` | Player/contributor guidance, component disclosures and reviewed reports | Public entry points |
| `tools/catalog/`, catalog generator/tests | Steam identity search, consistent game reports and download tabs | Static site, no separate vote/authentication store |
| `mydocs/` | Plans, evidence, reports and retention handoff | Exact-scope audit trail |

## Document Location Verification

| File | Planned location | Actual location | Result | Evidence |
|---|---|---|---|---|
| Overview and index | README and docs/README.md | Same | OK | Approved plan and final publication direction |
| Player/release guides | docs/rosetta-preview.md, docs/development/preview-release.md | Same | OK | Existing official documentation updated |
| Catalog/community | docs/compatibility and existing docs/community guides | Same | OK | Approved entry-point extension |
| Task evidence | mydocs plans/working/report | Same | OK | Stage/final templates |

## Quantitative Before/After Comparison

| Metric | Before | After |
|---|---|---|
| Public Pear app entry | None | Signed/notarized preview.3 DMG plus app/CLI archives and matching source |
| Reviewed catalog observations | One menu-only record | Two dated records including owner-confirmed sustained play/save/relaunch |
| Final documentation/search checks | Preparation-only routing | 94 Python tests, 6 Node tests passing; 48 changed source notice checks |
| Verified hardware scope | One M4 Pro | Same M4 Pro plus fresh standard account; no expanded hardware claim |

## Verification Results

| Acceptance criterion | Result |
|---|---|
| Reuse/provenance | OK: historical Libraries baseline investigated, replaced with pinned source-built Wine/CodeWeavers/DXMT and corresponding source/notices |
| Ordinary-user app/CLI | OK: signed/notarized packages, public HTTPS checksum verification and owner-confirmed fresh-account app flow without disabling protections |
| Official Steam and owned game | OK: direct owner login, normal installation/Steam Play and recorded Steam initialization |
| Sustained play and state | OK: owner confirmed requested 20+ active minutes, input/audio, progress after signed-app relaunch and normal exit |
| Second clean setup | OK within approved same-Mac test-user route; owner confirmed final checklist then deleted account; not second physical hardware |
| Recovery and preservation | OK within Stage 2 cases and later migration/relaunch checks; no generic repair or all-network recovery claim |
| Runtime/private separation | OK: immutable pinned runtime separate from credentials/games/saves; release allowlists and exact source |
| Guidance and downloads | OK: versioned app/CLI links, current component/OS requirements and bounded evidence; Pages goes live only after master deployment |

### Stage Verification Results

- [Stage 1](../working/task_m3_47_stage1.md): selected source-identifiable runtime and normal official Steam/game route.
- [Stage 2](../working/task_m3_47_stage2.md): bounded interrupted setup, restore, reinstall and preserved-state normal exit.
- [Stage 3](../working/task_m3_47_stage3.md): exact signed preview.3, owner-confirmed final fresh-account checklist, user guide and download wiring.
- [Dated Stage 3 records](../working/task_m3_47_stage3_preparation.md): prior failures, corrections and exact candidate/CI receipts.

## Residual Risks and Follow-up Work

### Residual Risks

Same-Mac clean account shares the host OS/Rosetta/tools. Another physical Mac,
other games, controllers, Steam Cloud correctness and performance remain unverified.
20 minutes is an owner-confirmed lower bound, not instrumented exact timing.
Game/Steam build and graphics settings for the last manual session were not fully
captured; reports show those unknowns. Steam upstream updates may change behavior.
The public Preview remains a pre-release; no latest/stable promotion is implied.

### Follow-up Candidates

Broader community observations, independently reproduced configurations, Homebrew
and preservation-aware removal may be separately scoped. Existing native work
(#11/#12) is unchanged; no other chat was invoked or asked to start work.

## Retention Handoff

Retain #47 checkout and ignored signed/source receipts, authenticated state and
recovery archives until release maintenance/recovery consumers no longer need
them. No ignored evidence is made public or discarded by PR/Issue completion.
The owner deleted the temporary test account after successful verification; this
turn did not reclaim or measure those bytes. Final site output is disposable
following successful deployed-content verification; no extra runtime copy exists.
See Stage 3 for roots, owner/consumers, scope and accounting limitations.

## Approval Request to Task Requester

Final verification and catalog publication were explicitly requested on October 15.
Publish the reviewable PR and complete the master-only deployment within that
scope, preserving immutable preview.3 and all private recovery state.

## Approved download layout publication follow-up — 2026-10-16

The download page keeps its original layout while moving system requirements
below the installation flow and Wine/DXMT versions into Release details. The
requester approved the rendered local preview and deployment. HTML matches that
preview exactly; 94 Python tests, 6 JavaScript tests and governance checks pass.
The existing Pages-only workflow is reused; no workflow configuration, binary,
release assets or home download routing change. This is a bounded #47 follow-up.

Retention handoff: small generated validation output is disposable after public
HTML verification. Existing private runtime/save evidence is outside this change.

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
