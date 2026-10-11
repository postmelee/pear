# Task #47 Plan: Rosetta-based Megabonk preview and user entry point

GitHub Issue: [#47](https://github.com/postmelee/pear/issues/47)
Milestone: [M3 — Rosetta-based Megabonk Preview](https://github.com/postmelee/pear/milestone/3)
Branch: `codex/task47`
Planning date: October 10, 2026 (Asia/Seoul)
Status: Task plan approved by explicit requester continuation on October 10, 2026;
implementation plan approved; Stage 1 complete; Stage 2 awaiting continuation.

## Purpose

Deliver the smallest usable interim path for owners to install and play Windows
Megabonk on a declared Apple Silicon/macOS configuration using Rosetta and
unmodified official Windows Steam. Use a small shared preparation/launch tool exposed by one command and a
double-click app, as subsequently authorized by the requester. Preserve normal
Steam Play, saves and clear user guidance.

This is an explicitly Rosetta-dependent preview. It neither qualifies M1 nor
completes the proposed Rosetta-free M2 experience. The CLI and small Mac entry point share a Rust core; Swift is limited to the
Mac window. QR-only interaction, npx, Dock and ARM64 Wine/FEX completion are not
prerequisites. The implementation plan records the concrete revised scope.

## Background

Read the [root rules](../../AGENTS.md), [README](../../README.md),
[documentation index](../../docs/README.md), [architecture](../../docs/architecture.md),
[delivery plan](../../docs/delivery-plan.md), [documentation rules](../../docs/AGENTS.md),
[task workflow](../manual/task_workflow_guide.md), [Git workflow](../manual/git_workflow_guide.md),
[rule conflicts](../manual/agent_code_hyperfall_rule_conflict.md) and
[document locations](../manual/document_structure_guide.md).

The [local evidence](../../docs/research/local-evidence.md) records M4 Pro,
24 GB RAM, macOS 26.5.2 (25F84), Megabonk 1.0.69, Wine 11.0 and DXMT 0.80
from frankea/Whisky Libraries 3.1.1. Menu and initial Forest combat were observed.
Read-only inspection of the original local script/report confirmed that Steam
sign-in preceded a direct executable launch using `steam_appid.txt`. Normal
Steam installation-to-Play, sustained 20-minute play, save/relaunch, clean
reproduction and ordinary-user delivery are unqualified. Original experiment
files and account data remain private and unchanged.

Registration checks found no substantially identical open Issue. Related
closed work is #9's [fixture supervisor report](../report/task_m1_9_report.md)
and #44's [WoW64 research report](../report/task_m1_44_report.md).
The [current supervisor guide](../../docs/development/runtime-supervisor.md)
explicitly refuses actual Wine/Steam/game execution. Its valid fixture results
are design evidence, not a preview launch facility.

### Existing work and integration boundaries

- Planning base: refreshed `origin/master` at
  `d01f5264cca305649fbf7df488b1dd7badaa5b80`. The primary checkout was already
  at this revision; its untracked `analysis/` and `research/` remain untouched.
  The explicit separate-checkout instruction overrides checking out/pulling in
  the occupied primary checkout. No master branch switch or file change occurs.
- Work in the attached `pear-task47` checkout on `codex/task47`; later publication
  uses `codex/publish-task47` to `master`. No runtime execution started at planning.
- #10 and #11 have active separate worktrees. #11's latest available Stage 1
  report, revised task plan and D19 diagnostic were inspected read-only during
  registration: native menu/Steamworks remained unqualified. Its Dock/direct-game
  runtime ownership and uncommitted work must not be changed by #47.
- Do not import moving #10/#11 runtime branches or make their completion a preview
  prerequisite. The paths may reuse valid facts and test concepts, not claims.
- Before later shared-document edits, compare current master and active changes.
  Preserve other task-board rows and resolve overlapping document ownership
  explicitly. Do not message another chat without requester authorization.
- Before host execution, check resource/process conflicts; use a separate private
  preview bottle and serialize heavy runtime/game work with the existing owner
  through the requester if a conflict exists. Never stop unrelated processes.

## Scope

### Included

- Compare an unchanged upstream GUI release, a small reviewed adapter/patch and
  existing Pear facilities. Choose the smallest route that passes the criteria.
- First reproduce Libraries 3.1.1 / Wine 11.0 / DXMT 0.80, then qualify official
  Windows Steam sign-in, owned App 3405340 installation and normal Steam Play.
- Record app/runtime/source versions and hashes, Steam build, game/depot/manifest,
  selected renderer, host/macOS, settings and date. Keep runtime payload and
  mutable prefix, games, saves, logs and caches separate.
- Verify setup interruption/retry, relaunch, actionable failures, local save
  backup/restore and compatible update/recovery without erasing the only save.
- Verify final delivery under normal macOS protections. Establish exact component
  notices, source and redistribution conditions before any Pear public release.
- Qualify at least 20 minutes of active gameplay, declared input/audio, save,
  clean exit, relaunch and a second clean setup using the exact documented flow.
- Publish only evidence-backed guidance and the approved preview entry point.

### Excluded

- New CPU/Windows/Steam authentication implementations; Dock/FEX completion;
  broad game support; automatic Steam library discovery; a general new UI.
- Game/API/ownership patches, authentication stubs, or `steam_appid.txt` as a
  supported launch route. Old diagnostic success does not qualify Steam Play.
- Distribution of proprietary games, signed-in prefixes, credentials, saves,
  private diagnostics or signing material.
- Unsupported performance/power/Steam Cloud/all-Mac claims, M1 completion or
  changes to another worker's source, branch, runtime or private prefix.

## Design Direction

### Reuse decision and authorized selection

| Candidate | Existing evidence | Proposed use and remaining gate |
|---|---|---|
| frankea/Whisky GUI and upstream DMG | Swift/SwiftUI app, bottle facilities, Steam integration and resumable download source | Initial candidate reviewed; shared CLI/app tool subsequently selected by the requester, pinned inputs and recovery |
| Minimal adaptation of existing Whisky facilities | Installer/download/bottle/Steam code available at the pin below | Only if a demonstrated gap prevents the unchanged app route; retain Swift and file notices, review the smallest patch and delivery obligations before implementation |
| Pear manager #9 | Tested Rust/C fixture admission, isolation and lifecycle | Reuse contract/ownership ideas; no new real-runtime adaptation or relaxation of its admission policy is selected |
| Original private Wine experiment | Working historical Wine/DXMT game baseline | Reuse exact settings and component facts; do not ship the fixed-layout script or its direct-launch shortcut |
| Archived original Whisky / Dock or new launcher | Historical UI or a separate current M1 integration effort | No default selection; adds stale-runtime or unrelated integration work compared with the existing fork |

Reviewed upstream pin:
[frankea/Whisky `3abfbae945e3400caaa13cf2e78fe5a187a1405b`](https://github.com/frankea/Whisky/tree/3abfbae945e3400caaa13cf2e78fe5a187a1405b).
Reviewed files include `WhiskyWineInstaller.swift`, `WhiskyWineDownloadView.swift`,
`dist/pages/WhiskyWineVersion.plist`, `docs/DEPENDENCIES.md` and `CONTRIBUTING.md`.
These are source observations; no app binary/source equivalence is established.

[Upstream Libraries v3.1.1](https://github.com/frankea/Whisky/releases/tag/v3.1.1)
has published archive SHA-256
`01f3a1b43b98065fe20c529c1023b61dd79a6d2ad93bba6040865f646481ccf3`,
matching the historical record. Recheck actual bytes before execution. The
app-v3.7.0 DMG is a candidate inventory item, not a selected or tested app.
Do not silently replace this baseline with a newer beta/GPTK runtime.

The reviewed GUI obtains versions from a mutable remote plist and can skip
archive verification if no hash is advertised. The reviewed installer removes
existing `Libraries` before extraction. These are concrete identity/recovery
gaps to assess, not proof of a qualified preview installer. Determine whether
existing settings and a verified non-destructive procedure suffice; otherwise
propose the minimal correction. Never claim atomic rollback from this source.

Whisky files examined carry GPL-3.0-or-later notices. Exact Wine, DXMT, helpers
and packaging terms require component-level review for the selected artifacts;
no whole-bundle license assumption or Pear license choice is made. Preserve
upstream language and contribution conventions for any selected source reuse.
D3DMetal/GPTK is not selected by this DXMT baseline.

### User flow and preservation

Open the small app or invoke the shared command. The tool prepares a private
preview bottle and installs official Windows Steam. The owner authenticates
directly with Valve; the tool requests automatic installation in the default
Steam library and normal Steam launch after installation completes. Subsequent
launches reuse the same verified installation. Routine users need no Terminal,
Xcode or developer account; implementation/testing tools are separate.

Keep current saves before restore/migration and retain a compatible runtime and
prefix combination for recovery. A runtime-only downgrade does not prove prefix
compatibility. Determine actual save locations through owner testing; do not
assume the historical path or Steam Cloud behavior. Failure injection uses
synthetic/disposable state, not the owner's only game progress.

The final GUI version, direct upstream delivery versus adaptation, verified host
range, clean-test setup and need for Pear redistribution remain open decisions.
Do not translate missing resources into a passing or unsupported blanket claim.

Selected workflow skills: `task-register`, `task-start` and `todo`; subsequent
stage/final skills apply at their boundaries. Apple/Metal technical expertise is
not needed for planning; select it if a later approved graphics diagnostic needs
it. Read new code area's scoped rules before designing changes there.

## Document Location Judgment

The following location judgment was approved with the task plan. No official
product document is changed during planning.

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| Preview entry | Official short entry point | Game owners | `README.md` | Full installation guide in README | Keep the project overview short; link to tested instructions |
| Guide index | Official navigation | Users/contributors | `docs/README.md` | Separate index | Reuse the established official index |
| Preview guide | Official user guidance with bounded evidence | Game owners | `docs/rosetta-preview.md` | `docs/research/` or `mydocs/manual/` | This is installation/play/update/recovery guidance, not dated research or internal workflow |
| Milestone relationship | Official roadmap | Users/contributors | `docs/delivery-plan.md` | New preview roadmap | Minimal temporary-path and M1/M2 distinction in the single roadmap |
| Reuse investigation | Task research | Reviewers/implementers | `mydocs/tech/task_m3_47_reuse.md` | User guide | Preserve alternatives/provenance separately from supported instructions |
| Task plans/reports | Internal work artifacts | Requester/reviewers | Existing `mydocs/` subdirectories | `docs/` | Keep approval and stage history separate from current user guidance |

Read existing documents immediately before editing. Include tested environments,
Rosetta requirements, official Steam ownership, setup, relaunch, updates, backup,
recovery, uninstall preservation, limitations and redacted reporting in the user
guide. Mark unavailable capabilities explicitly; do not publish a premature
Play/download-ready link. Identify upstream distribution versus Pear validation.

## Expected Changed Files

New after applicable approvals:

- `docs/rosetta-preview.md`
- `mydocs/tech/task_m3_47_reuse.md`

Modified after verification: `README.md`, `docs/README.md`, and minimal
`docs/delivery-plan.md` milestone relationship text.

Task artifacts:

- `mydocs/orders/20261010.md` and subsequent actual working-day boards
- `mydocs/plans/task_m3_47.md`
- `mydocs/plans/task_m3_47_impl.md` after task-plan approval
- `mydocs/working/task_m3_47_stage{N}.md` and sanitized supporting observations
- `mydocs/report/task_m3_47_report.md`

The requester approved the small tool: source/build/test paths are under
`preview/`, with Rust core and thin Swift shell as detailed in the implementation
plan. No source changes to the existing native manager are selected. Private execution outputs belong outside tracked artifacts;
no existing personal bottle is copied into Git.

## Tentative Stages

1. **Stage 1 — Select and reproduce the minimum route.** Inspect exact releases,
   licenses, identity and permissions; compare delivery candidates; prepare an
   isolated baseline and verify official Steam installation/sign-in/owned install
   and normal launch. Record necessary corrections and the reuse decision. If
   a correction is required to reach normal launch, review its concrete design
   within this stage rather than mark a failed launch as stage completion.
2. **Stage 2 — Complete setup, relaunch and preservation.** Implement only the
   reviewed missing pieces, or verify existing GUI capabilities. Exercise
   interruption/retry, corrupt/missing input, low storage, update failure,
   retained prefix/runtime compatibility and local save backup/restore.
3. **Stage 3 — Qualify and document the final experience.** Test final artifacts,
   20-minute active play, input/audio, save/exit/relaunch, second-clean-setup
   reproduction and ordinary-user delivery. Complete documentation and reports.

Complete required verification, report and commit each stage before requesting
explicit continuation. Build, source inspection, UI checks, game qualification
and distribution remain separate evidence scopes.

## Verification Plan

### Planning evidence and prerequisites

Available: authenticated GitHub metadata, isolated Git checkout, recorded source
and historical runtime identities, repository checker and source files.
Not checked for this preview: downloaded app signature/notarization, installed
Rosetta state, free storage, actual Steam/game versions, live GUI flow, second
clean setup and available signing/distribution authority. Do not infer these from
historical host records. The owner performs direct Steam sign-in/Steam Guard.

Reuse the existing local record only for the historical component/settings and
menu/initial-combat observation. Its producer was a fixed-layout private script;
no reusable current qualification checker was established. A matching archive
hash alone cannot turn direct launch into normal Steam Play. Invalidating inputs
include app/runtime/profile/Steam/game/OS changes and changes to delivery or
signing; revalidate affected claims and preserve earlier outcomes as history.

### Stage Verification

| Stage | Method and expected result | Evidence retained |
|---|---|---|
| 1 | Verify exact archive hashes/source references and inspect signing/normal opening; observe selected Wine/DXMT; exercise official Steam setup, owner login, owned install and Play | Sanitized identities, selected settings, actual menu and game Steamworks outcome, renderer evidence, blockers and candidate comparison |
| 2 | Interrupt and resume setup; reject corrupt/missing artifacts; exercise low-storage/update failure with disposable state; reopen installation; backup/restore actual saves without losing current data | Before/after integrity and state-preservation results, recovery steps, applicable existing upstream checks and focused tests for new behavior |
| 3 | Run at least 20 active gameplay minutes with declared input/audio; save/quit/reload; repeat the exact user flow on a second clean setup under normal protections | Exact final configuration, active duration, observed persistence, delivery assessment, clean-setup definition and known limits |

Steam self-updates may prevent exact reuse of an old client; record the actual
client and qualify required updates. A new empty bottle alone does not establish
clean machine-level delivery: define and record the second setup's account,
runtime/cache, security and prior-install state. If only limited reproduction is
available, leave the unmet clean-delivery criterion explicit.

### Integrated Verification

- Every Issue acceptance criterion links to matching final evidence. No UI-only,
  hash-only, fixture-only or historical direct-launch result closes game gates.
- Verify normal Steam Play without a shipped `steam_appid.txt`; report original
  Steam/game errors and keep authentication/ownership decisions with Valve.
- Verify keyboard/mouse and audio in the declared flow; document controller,
  overlay, achievements and Steam Cloud as tested or untested.
- Verify update/recovery and app removal guidance preserves saves. No automatic
  migration or broad compatibility promise without corresponding checks.
- Run `python3 -B tools/check_governance.py`, inspect changed Markdown links and
  `git diff --check`. Run focused existing/new functional checks only where the
  chosen implementation changes behavior; preserve approved required checks.
- Verify no private game/account/save/signing data is staged. Require a clean
  task working tree after final commits before PR preparation.
- Recheck exact public delivery inputs; source redistribution/notices and Pear's
  own license remain release decisions if a Pear artifact is needed. A PR or
  signed app does not itself authorize a public release or prove qualification.

## Risks

- **GUI/runtime drift:** a mutable feed can change the tested combination. Bind
  exact artifacts, expose unexpected changes and requalify affected execution.
- **Destructive runtime replacement:** upstream source deletes old runtime before
  extraction. Qualify an actual recovery procedure or review a small correction.
- **Steam/game drift:** client updates or game versions can invalidate historical
  behavior. Use genuine required updates and preserve input-specific records.
- **Private state:** shared app containers, prefixes or restore operations could
  affect existing installations. Inventory first and use independent private state.
- **Resource contention:** #11 runs on the same host. Avoid competing builds/game
  tests and preserve process ownership; coordinate if the actual run conflicts.
- **Distribution gap:** upstream claims are not local Gatekeeper evidence; a
  modified app needs its own authorized delivery and component review.
- **Unavailable clean setup or owner interaction:** keep those criteria pending
  and identify the concrete resource needed; do not substitute synthetic success.

## Approval Request

The requester approved this scope, reuse-first design, document locations, three
tentative stages and verification criteria by explicit continuation in this chat.
The [implementation plan](task_m3_47_impl.md) now defines concrete Stage artifacts,
verification methods and commit messages for review before Stage 1. No product
changes or runtime execution occurred during planning.


## October 11 Requester Revision: User Distribution First

The requester approved general Windows Steam entry through Pear, public-document
alignment and app/CLI release preparation. Pear is intended to be free and open
source, usable without Wine/Whisky/Terminal knowledge. Rosetta-free Windows Steam
gameplay remains the final product goal; this Rosetta preview is an interim route.
Megabonk remains the first validation game, not the only game selectable in Steam.
The implementation plan records the approved paths, exact source/package changes,
retention and outstanding release decisions. Performance and memory work is deferred.
Existing qualification requirements are retained; no all-game or public-release
qualification follows from selecting the general Steam entry.


## Approved Public Onboarding Extension — October 11

The requester approved public README/documentation entry points using Diataxis,
separate Preview/native contribution paths, community forms/policies, reviewed
game records and supplied branding. The implementation plan records the approved
locations, reuse decisions and affected checks. Repository visibility and public
release remain separate pending gates; Stage 1 stays in progress.
