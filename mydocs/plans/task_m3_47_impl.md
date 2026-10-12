# Task #47 Implementation Plan: Rosetta-based Megabonk preview

Task plan: [task_m3_47.md](task_m3_47.md)
GitHub Issue: [#47](https://github.com/postmelee/pear/issues/47)
Milestone: M3 — Rosetta-based Megabonk Preview
Branch: `codex/task47`
Date: October 10, 2026 (Asia/Seoul)
Status: task and implementation plans approved by explicit continuation in this
chat; Stage 1 complete on October 11, 2026; Stage 2 approved and in progress.

## Context and Approval Record

The requester approved M3/Issue registration, then task-start, then the task plan
in successive explicit continuations. Task-start commit is `37694eb`. The next explicit
continuation approved this implementation plan and Stage 1 execution. The requester subsequently explicitly authorized a small setup/login/launch tool
with one-command and double-click entry points. This supersedes the GUI-only
implementation restriction; the concrete design below records that authorized scope.

Apply the task plan's root/scoped documentation rules, workflow, upstream reuse
rationale, private-state boundaries and document-location judgment. Also read
[host rules](../../host/AGENTS.md) and [test rules](../../tests/AGENTS.md) for any
later host or fixture changes. No native-host implementation is currently selected.
The `todo` format applies to board updates; `task-stage-report` and
`task-final-report` apply at their respective boundaries. No Apple Metal technical
skill is selected: ordinary GUI/game observation is not a Metal debugging task.
If graphics diagnosis becomes necessary, select the relevant expertise first.

The preview remains independent of #10/#11's moving native runtime. Use the
attached checkout only. The approved small preview tool may prepare its own runtime/prefix and open
official Steam. No authentication client, new profile contract, native runtime
admission change or general supervisor rewrite is included. Keep unmet game
and distribution gates open.

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Implement and reproduce the shared preview entry point | `mydocs/tech/task_m3_47_reuse.md`, Stage 1 report and sanitized observations | Exact app/runtime identities, normal security, isolated official Steam install/sign-in/owned install/Play and real menu/Steamworks |
| 2 | Qualify setup recovery and save preservation | Stage 2 report, recovery scenario records, reviewed minimal correction only if required | Interrupted setup, bad inputs, low storage, repeat launch, compatible update/recovery and actual save restoration |
| 3 | Qualify the final preview and publish guidance | User guide, README/index/roadmap edits, Stage 3/final reports | 20-minute active play, input/audio, save/exit/relaunch, second clean setup and final delivery conditions |

Each stage ends with required checks, a stage report and commit before explicit
continuation. Failed requirements remain failed; source inspection is not live
execution. Verification tools below are operator checks; the new CLI and app are the
selected user entry points.

## Document Location Check

| File | Planned Location in Task Plan | Stage Artifact Path | Match | Notes |
|---|---|---|---|---|
| Reuse decision | `mydocs/tech/` | `mydocs/tech/task_m3_47_reuse.md` | OK | Stage 1 investigation and later selection updates |
| Stage evidence | `mydocs/working/` | `task_m3_47_stage{N}.md`, `task_m3_47_stage{N}_observations.json` | OK | Sanitized outcomes only |
| User guide | `docs/rosetta-preview.md` | Same | OK | Stage 3, only evidence-backed user steps |
| Entry/index | `README.md`, `docs/README.md` | Same | OK | Stage 3 short navigation, no early download claim |
| Roadmap | `docs/delivery-plan.md` | Same | OK | M3 and temporary Rosetta/M1/M2 relationship only |
| Final report | `mydocs/report/` | `mydocs/report/task_m3_47_report.md` | OK | Final-report procedure after all stages |
| Plans and board | Existing plans/orders | `task_m3_47*.md`, actual working-day board | OK | Preserve unrelated rows |

Private raw evidence/downloads may use ignored `.build/task47/` with restrictive
permissions. App-managed private state must be separately inventoried and owned;
a task output directory alone does not isolate a GUI app's shared container.
Do not create speculative code directories. New source/test paths require the
concrete correction design and applicable scoped rules before changes.

## Authorized Small-Tool Design (Requester Revision)

The requester approved automatic preparation and official Steam launch with one
command or double-click, then asked to reconsider Swift versus Rust. The existing
[manager language decision](../../docs/decisions/manager-language.md) favors Rust
for management, while leaving UI language independent. Use Rust for the shared
preview core and a small Swift/AppKit presentation shell. This is a maintenance
and reuse choice, not a new benchmark or game-performance claim.

Concrete source scope: `preview/Cargo.toml`, locked dependencies,
`preview/src/lib.rs`, `preview/src/main.rs`, `preview/Launcher.swift`, and
`preview/build.sh`, and `preview/build.rs` for the existing C hash bridge. Focused functional checks live alongside the Rust core;
follow `tests/AGENTS.md`. Existing manager source remains unchanged: reuse its
public hashing/path utilities through a local dependency, not fixture admission
or process-supervision APIs. Retain the existing locked libc version. Review
upstream behavior without importing GPL Swift source; download the unchanged
pinned external runtime, whose own notices remain present.

- CLI `pear-preview play` and `Pear Preview.app` invoke the same Rust binary.
  No Node/Python installation is required by that built binary. Build tools are
  developer-only. The Swift shell presents progress and actionable errors. The core sends the verified official-client `-console +app_install 3405340`
  command and retries at a bounded interval until Steam creates its manifest;
  both entries use the same installation state machine without a continue button.
- Create private owned state under `~/Library/Application Support/Pear Preview`;
  developer tests select a separate root. Lock preparation, reject unrelated
  nonempty roots and preserve prefixes/saves on error. Do not adopt Whisky state.
- Download fixed HTTPS runtime/Steam artifacts, verify required size and SHA-256,
  extract only the authenticated runtime into a fresh stage, and activate by
  rename into a version-specific directory. No mutable runtime feed or fallback.
- Initialize a fresh Windows 10/MSync prefix and copy both DXMT architectures by
  replacement, never write through Wine's runtime symlinks. Keep the Wine loader's
  Mac app identity separate from the Swift launcher and retain upstream bytes.
- Install official Steam, show its own login, request the owned game's install,
  then request normal `-applaunch 3405340` only after its installation manifest
  indicates completion. Steam retains ownership, login and Guard. The core uses Steam
  app_install rather than the install-confirmation URI. QR-only interaction is a goal, not a tested promise.
- Keep credentials out of CLI arguments/output; do not inspect login caches.
  Do not launch Megabonk.exe or create steam_appid.txt. Report handoff separately
  from observed game readiness. No global kill command or other prefix cleanup.
- First validate hashes, invalid inputs, path isolation, locking, installation
  state parsing, process failure and repeat preparation with owned fixtures.
  Build the ARM64 CLI/app, then exercise the real private setup. The existing
  Stage 1 Steamworks/menu and later recovery/game/distribution gates still apply.
- A locally built app uses only an ad-hoc resource seal, with no added
  entitlements, and is a development artifact. Developer ID, notarization,
  component licensing and clean browser-delivery checks remain Stage 3 gates.

The requester also approved removing unneeded previous installs. Removed the
newly installed Whisky GUI, duplicate runtime, incomplete empty bottle and DMG;
retained the verified runtime archive and official Steam installer for this core.
Original experiments, authenticated state and other task worktrees are untouched.

## Authorized October 11 Automation Verification

The requester explicitly asked to verify and proceed after the manual Steam
install-confirmation gap was explained. Preserve the current authenticated
preview prefix. First test the existing official client's own installation
command as a bounded experiment: use the same private runtime and Steam binary,
request `-console +app_install 3405340`, then inspect only the target app manifest
and executable. No login-cache read, token transfer, fake manifest, game patch or
new auth implementation is authorized or necessary for this first experiment.
If the current client ignores the command, record that result; do not describe it
as automatic installation. Normal client restart may be evaluated only while no
game is running, preserving the official session and private state.

In parallel with the conceptual comparison (without delegating agents), inspect
pinned DepotDownloader/SteamKit and existing Dock evidence read-only. Reusing a
QR downloader proves acquisition only. A separate runtime client must genuinely
accept its session and launch the owned game before a one-login claim. Do not
copy #11's active adapter or make native FEX progress a preview prerequisite.

## Planning Inventory and Input Pins

Read-only planning on October 10 verified macOS 26.5.2 (25F84), availability of
`python3`, `gh`, `git`, `shasum`, `codesign`, `spctl`, `hdiutil`, `xattr`, and
`sw_vers`. These establish command availability, not effective permissions or
successful app execution. The volume reported about 15 GiB available; this is
transient and not an installation-space guarantee.

| Input | Exact candidate | Verification boundary |
|---|---|---|
| GUI app | [Whisky app-v3.7.0](https://github.com/frankea/Whisky/releases/tag/app-v3.7.0), `Whisky-3.7.0.dmg`, 10,753,689 bytes | GitHub release digest only; artifact not downloaded or executed |
| GUI SHA-256 | `8232b3b96be09b56e8f4e6b091c34a89c74b27c63ccfce92aa8ffe6ce3fbfee2` | Recompute on actual download; no signing conclusion from digest |
| GUI tag revision | `305da2143bf6f73ac5b261303c7e7e957c23a227` | Resolve release code here; prior review was different main revision `3abfbae945e3400caaa13cf2e78fe5a187a1405b` |
| Runtime | [Libraries v3.1.1](https://github.com/frankea/Whisky/releases/tag/v3.1.1), `Libraries.tar.gz`, 332,438,526 bytes | Historical Wine 11.0 / DXMT 0.80 candidate; verify extracted component identities |
| Runtime SHA-256 | `01f3a1b43b98065fe20c529c1023b61dd79a6d2ad93bba6040865f646481ccf3` | Matches published metadata and historical record; no current gameplay proof |
| Steam | Official Windows installer/client obtained from Valve | Resolve current origin, version, hash and update result in Stage 1; do not reuse an old hash as current trust |
| Game | Owner's Steam App 3405340, Windows depot 3405342 | Observe current build/manifest; 1.0.69 and manifest 446680890915713051 are historical, not guaranteed available |

Rosetta installation state, hardware details, app signature/notarization, live GUI
session, account participation, clean-test environment and final release authority
remain unchecked for this preview. No Xcode/compiler is required for the unchanged
app candidate. Read upstream build instructions only if a correction requires it.

## Stage 1 - Implement and Reproduce the Shared Preview Entry Point

### Artifacts

- `mydocs/tech/task_m3_47_reuse.md`: exact source/file review, candidates,
  component notices, distribution boundary, observed GUI capabilities and decision.
- `mydocs/working/task_m3_47_stage1_observations.json`: sanitized case outcomes.
- `mydocs/working/task_m3_47_stage1.md`: complete only after required gates pass.
- Task plan/implementation plan and actual-date board updates as necessary.

### Changes

1. Inspect actual host/resources and existing Whisky installation/container
   presence before launch. Inspect process identities without collecting broad
   environment/command-line secrets. Do not modify an existing global runtime,
   import personal bottles, stop another task, or overwrite `/Applications/Whisky.app`.
   Establish a task-owned bottle and app-state boundary. If the unchanged GUI
   cannot isolate existing state, choose a separate clean user/test setup with
   the requester rather than silently repointing its shared directories.
2. Calculate space for archive, expanded runtime, Steam, game and required backup
   from available manifests/metadata and extraction inventory before full game
   acquisition. Downloading a small DMG is distinct from authorizing unbounded
   game duplication. Do not reclaim another task's files to fit the budget.
3. Inspect the actual app-v3.7.0 source tag for runtime feed configuration,
   installer, hash behavior, bottle/path handling, DXMT selection, Steam launch
   and restore/export facilities. Carry forward earlier findings only if their
   source preimages still match. Record per-file licenses/contribution guidance.
4. Download exact release assets to a task-owned directory, reject hash/size
   mismatch, inspect DMG and contained app read-only, and assess normal macOS
   opening. Browser-delivery/Gatekeeper behavior must remain in the final test;
   CLI acquisition alone does not reproduce a browser quarantine flow. Do not
   remove quarantine, re-sign an upstream artifact or disable protections.
5. Use the shared preview setup core with the verified baseline runtime and
   explicit DXMT settings. Confirm actual Wine/DXMT identity; refuse a silent
   move to beta/GPTK or a renderer fallback. If the remote feed changes, compare
   actual downloaded bytes to the pinned expectation before calling it the baseline.
6. Install official Windows Steam in a fresh preview bottle. The owner signs in
   directly with Valve, using any offered method. Do not read unrelated credential
   caches or record password/QR/token screens. Let Steam apply required updates.
7. Install owned Megabonk through Steam and select its normal Play action.
   Verify responsive menu and original game Steamworks initialization in the
   same run, using narrow redacted evidence and actual behavior. A logged-in
   client or menu image alone is not Steamworks proof. No direct executable
   fallback or shipped `steam_appid.txt` qualifies this gate.
8. Close only the preview's owned game/client normally and record persistence
   locations without copying private content into reports. Validate both entries into the shared core; keep the exact candidate and
   remaining delivery gaps recorded.

### Verification

Run from the isolated checkout. Asset commands use the exact paths below after
acquisition; do not execute a later command after a failed earlier gate.

```sh
sw_vers
uname -m
df -h .
gh release view app-v3.7.0 --repo frankea/Whisky --json tagName,assets
gh release view v3.1.1 --repo frankea/Whisky --json tagName,assets
shasum -a 256 .build/task47/downloads/Whisky-3.7.0.dmg
shasum -a 256 .build/task47/downloads/Libraries.tar.gz
hdiutil verify .build/task47/downloads/Whisky-3.7.0.dmg
python3 -B tools/check_governance.py
git diff --check
```

After a read-only mount, bind `PEAR47_APP` to the inspected app path, not a guessed
installed application. Record mount identity and detach only that owned mount.

```sh
codesign --verify --deep --strict --verbose=2 "$PEAR47_APP"
codesign -dv --verbose=4 "$PEAR47_APP"
spctl --assess --type execute --verbose=4 "$PEAR47_APP"
```

Signature validity and Gatekeeper assessment are separate from actual first-open,
runtime permission and normal Steam/game execution. Retain failure status/errors;
no unavailable query becomes a pass. Record exact app signer identity publicly
only where it is ordinary published certificate information, never private keys.

| Case | Expected result | Evidence |
|---|---|---|
| S1-identity | App/runtime bytes match approved pins; source and extracted dependencies identified | Digests, sizes, source refs, component inventory |
| S1-isolation | Existing installations/prefixes unaffected; owned app/bottle state explicit | Before/after path ownership and narrow non-sensitive sentinel results |
| S1-security | Normal app/runtime opening under normal macOS protections | Actual signature/assessment/open outcomes, declared Rosetta requirement |
| S1-steam | Official install/update/sign-in and owned game installation succeed | Installer/client/game identity and phase outcomes, no account identifiers |
| S1-play | Steam Play reaches responsive menu and actual Steamworks succeeds with selected DXMT | Same-run app/process/game/backend identities and redacted observations |

Any required failure blocks Stage 1 completion. Source-only preparation can be
reported as progress but cannot substitute for S1-play. Account interaction or a
new clean user requires actual requester participation if unavailable.

### Commit

`Task #47 Stage 1: qualify the pinned Rosetta Steam launch route`

## Stage 2 - Qualify Setup Recovery and Save Preservation

### Artifacts

- Stage 2 sanitized observations and stage report in `mydocs/working/`.
- Reuse record updated with exact selected behavior and recovery procedure.
- Only concretely reviewed implementation/test corrections, if Stage 1 requires
  them. Their paths, commands and upstream versions must be added before editing.
- Actual-date board with unrelated rows preserved.

### Changes

Use the Stage 1 app/runtime configuration and separate disposable installation
state for adverse cases. Exercise the selected shared core and preserve the same required recovery cases.
The requester approved setup automation; do not expand into a general manager.
Preserve current owner saves before any restoration and stop only relevant owned
processes before replacing state. A whole-bottle backup may contain credentials:
keep it private and never include it in a release or public evidence bundle.

| Case | Procedure | Required observable result |
|---|---|---|
| S2-download | Interrupt the owned download, restart the GUI and retry | Partial input cannot activate; completion verifies pinned bytes; restart reuses or safely redownloads as documented |
| S2-install | Interrupt disposable extraction/setup, reopen and retry | No false ready state; the verified usable installation can be recovered |
| S2-invalid | Present a truncated/corrupt/missing archive through the actual available installer path or its exact source test seam | Refusal before activation; existing working state preserved; synthetic seam evidence does not replace GUI flow |
| S2-space | Use bounded disposable storage/quota or the actual installer test seam to produce insufficient space | Actionable failure and no loss of previous working data; never fill the host volume |
| S2-repeat | Exit and reopen the app/client/game twice | Existing installation is reused and selected runtime/prefix remain compatible |
| S2-update | Exercise failed/interrupted update in disposable state | Working runtime/prefix/save combination survives or a verified procedure restores it; no unsupported atomicity claim |
| S2-save | Create identifiable game progress, exit, back up locally, make further progress, preserve current state, restore prior backup, relaunch | Correct restored progress/settings observed; pre-restore state still recoverable; no raw save/account data committed |
| S2-removal | Follow proposed removal/reinstall procedure in disposable state | Saves retained unless deliberately removed; relaunch restoration documented |

Missing hash metadata must not silently qualify input identity. If the selected
unchanged app cannot satisfy the approved criteria, document the failing operation
and propose the smallest patch. Do not weaken #47's criteria to avoid a correction.
No downgrade of a real authenticated prefix is used as failure injection.

### Verification

Recompute final asset hashes if installer changes them. Execute the scenario
matrix against the selected GUI and observe user-facing outcomes. Use the same
settings recorded in Stage 1. For exact-source seams, pin dependencies and run the
selected upstream tests after reading that version's build/test instructions;
those commands remain contingent on the actual selected correction and must be
recorded before execution. Do not run an unspecified whole-project build.

```sh
python3 -B tools/check_governance.py
git diff --check
```

Retain case/input identities, phase, expected/actual outcome, preservation proof,
cleanup result, observation gaps and proposed user recovery steps. A successful
fixture restore does not close actual game persistence. Available space and
Stage 1 resources are checked again; low-storage test facilities are not checked
at planning. A required unavailable case remains pending.

### Commit

`Task #47 Stage 2: verify setup recovery and preserve Megabonk saves`

## Stage 3 - Qualify the Final Preview and User Guidance

### Artifacts

- `docs/rosetta-preview.md`; short entry in `README.md`; link in `docs/README.md`.
- Minimal M3/temporary-route distinction in `docs/delivery-plan.md`.
- Stage 3 sanitized observations/report, final report through its skill and board.

### Changes

1. Freeze the final candidate after Stage 2. Match the app/runtime/profile and
   selected settings to the next execution; record current Steam/game changes
   and repeat affected Stage 1/2 checks where inputs changed.
2. Run at least 20 minutes of active gameplay, excluding paused/menu time. Observe
   keyboard/mouse, audio, meaningful game progress, save, clean exit and relaunch.
   Confirm game progress and settings return. Keep optional controller/overlay/
   achievements/Cloud features explicitly untested unless actually verified.
3. Repeat the exact download-to-resume flow on a second clean setup. A second Mac
   or clean OS/test-user setup must have its prior app, runtime, bottle/cache and
   developer/security state recorded. A new bottle alone is insufficient. Do not
   create accounts or erase an existing environment without requester direction.
4. Validate real browser-delivered first-open and ordinary-user runtime execution
   without Xcode, developer enrollment or disabled protections. Upstream app
   delivery can be referenced if unchanged; a Pear modification needs its own
   signing/notarization/source/license solution and new matching verification.
5. Write the guide from observed UI steps: prerequisites and tested hardware/OS,
   Rosetta disclosure, exact downloads/versions, official Steam installation,
   owner sign-in, owned installation, Play, relaunch, preservation/update/recovery,
   removal and sanitized troubleshooting. Identify upstream and Pear roles.
6. Add the short README entry only when the guide's tested route is ready; keep
   M1 and proposed M2 status accurate. Check current shared-document changes before
   editing. No public release upload, repository visibility change or automatic
   Issue closure is authorized by a stage verification result.

### Verification

| Case | Expected result | Evidence |
|---|---|---|
| S3-play | At least 20 active minutes, declared input/audio, no unresolved required-path failure | Start/end and paused-duration accounting, exact identities/settings and failures |
| S3-resume | Save, normal exit and later normal Steam Play restore actual progress | Before/after observed progress, no raw saves |
| S3-clean | Second clean setup repeats the documented full flow | Setup provenance, normal protections, delivery and phase outcomes |
| S3-docs | All stated support/download/recovery claims match final evidence | Guide walkthrough, links, actual versions, limitations and final acceptance mapping |
| S3-release | Exact selected delivery has resolved applicable component and distribution requirements | Notices/source references, signer/distribution route or explicit unresolved gate |

The second setup and owner interaction remain unavailable/unconfirmed at planning.
No historical run or on-host blank bottle is substituted. If the final artifact
changes, revalidate affected cases before calling it qualified.

```sh
python3 -B tools/check_governance.py
git diff --check
git diff --name-only
git status --short
```

Additionally inspect links in changed task artifacts with the existing checker
helpers, since the governance command's default scope does not include all
`mydocs/`. Review staged content for private state and check the guide by following
its UI steps. Documentation checks establish routing, not gameplay.

### Commit

`Task #47 Stage 3: qualify the Rosetta preview and user guide`

After all stages, apply `task-final-report` for the final report, board completion,
final commit and reviewable PR. Actual public binary distribution, merge and
Issue closure retain their applicable authorization and verification boundaries.

## Verification and Evidence Rules

Every sanitized observation records case ID, date, exact inputs, method, expected
and actual outcome, pass/fail/unavailable/unperformed status and known limitations.
Do not commit credentials, usernames/account identifiers, personal paths, save
bytes, raw logs or authenticated screenshots. Keep private raw evidence under
owned access controls and retain only narrowly needed outputs.

Historical September 27 evidence supports the chosen component/settings baseline
and initial direct-launch observation only. No current checker makes it normal
Steam Play, clean distribution or save qualification. App/tag differences, mutable
feeds, runtime/Steam/game updates, settings, OS or packaging changes require
revalidation of affected claims. Preserve required tests and failed attempts.

Run required checks before stage completion; write and commit the corresponding
report with artifacts. If a design/location change is necessary, update the plan
and obtain approval before implementing. Do not use source-only notes or skipped
cases to complete a required stage. No broad native M1 regression rebuild is
needed for documentation or unchanged upstream app testing; shared native runtime
modification is excluded and would require its owner's review.

## Commits

- Planning: `Task #47: approve task plan and define implementation stages`.
- Stage commits use the exact Stage messages above and include their reports.
- Final reporting: `Task #47: final report and daily task board update`.
- Work stays on `codex/task47`; publish via `codex/publish-task47` to `master`.

## Stage Dependencies

Stage 1 starts after approval of this plan. Stage 2 starts after Stage 1 checks,
report, commit and explicit continuation. Stage 3 follows the same rule after
Stage 2. #10/#11/Dock/FEX completion is not a preview prerequisite. Required
owner sign-in, actual available space and second clean setup are real resources,
not assumed completed milestones.

## Risks and Responses

- **15 GiB transient free space:** estimate expanded/download/backup needs before
  full acquisition; reuse verified public archives safely, not authenticated state;
  request a concrete storage decision if insufficient, never delete others' data.
- **Shared GUI containers:** a new bottle is not app-state isolation. Inventory
  and choose an isolated setup before installing/updating the runtime.
- **Source/tag drift:** inspect the release tag, bind artifact identities and do
  not inherit later-main behavior or the feed's new version silently.
- **Same-host game work:** inspect conflicts and serialize heavy work; no name-based
  process killing, shared prefix changes or competing native runtime builds.
- **Installer preservation gap:** retain failure evidence and review the smallest
  required fix; no invented atomic rollback or hash enforcement guarantee.
- **Account/clean setup availability:** continue independent preparation and ask
  for the specific missing interaction/resource; leave dependent gates pending.

## Approval Request

Approve this three-stage implementation plan, evidence cases, artifact locations,
commit messages and Stage 1 start. The current turn only writes planning artifacts.
Approval starts the exact-release review and isolated baseline validation; any
required source correction needs its concrete design before editing. Later stage
transitions retain the repository's explicit continuation rule.


## Authorized October 11 Steam Entry and Distribution Priority

The requester explicitly prioritized making the demonstrated flow usable by other
users, authorized the previously proposed public-document and entry-point work,
and requested downloadable distribution with an optional CLI. Performance,
memory optimization and subsystem rewrites are deferred. This revision brings
entry-point, documentation and package preparation into the current Stage 1
work; it does not claim completion of the existing recovery, sustained-play,
clean-environment or distribution gates and does not approve a stage transition.

The default `pear-preview` / `pear-preview steam` command and double-click app
prepare the same private environment and open official Windows Steam's library.
The user chooses games in Steam. Keep `pear-preview megabonk` as the bounded
Megabonk install-and-launch verification route and retain `play` as its explicit
legacy alias. No default game installation, new auth implementation, general
profile engine or native-manager admission change. Add CLI dispatch tests before
external side effects and test the real reused-prefix Steam entry. Client success
messages describe a request, not confirmed game readiness.

Approved documentation location judgment from the requester discussion:

| File | Audience / purpose | Location rationale |
|---|---|---|
| README.md | Users; free/open-source intent, easy Steam entry, current preview vs final Rosetta-free goal | Short project entry; no second roadmap |
| docs/README.md | Users and contributors; separate start paths | Existing canonical documentation index |
| docs/delivery-plan.md | Current M3 and future M1/M2/R1 relationship | Existing single roadmap; preserve M1/R1 identities and required gates |
| docs/architecture.md | Developers; shared product experience and separate runtime routes | Existing architecture; preserve native requirements |
| docs/rosetta-preview.md | Users; actual app/CLI behavior, prerequisites, recovery limits and release status | Already approved user-guide destination; no unverified download claim |
| docs/development/preview-release.md | Maintainers; exact build/sign/notarize/package/release procedure | Development instructions must not burden ordinary-user flow |
| preview/THIRD_PARTY_NOTICES.md | Package recipients; source/version/license boundaries | Distributed alongside Pear-owned binaries, not game/runtime payload |
| LICENSE (after license selection) | Source and package recipients | Root license excludes separately licensed third-party material |

Package only the Pear app, a CLI archive, documentation and applicable notices;
never include private state, game files, Steam installers or Wine payload. Retain
external artifact pins and original notices. Build locally with an ad-hoc seal;
release mode explicitly signs the nested CLI and app with the owner's authorized
Developer ID, Hardened Runtime and timestamp, without extra entitlements. A
notarization profile name references Keychain credentials; never export keys or
store credentials in source. Submit app and CLI archives to Apple, retain request
identities/status, staple the app, and repackage/check digests. A rejected/missing
notarization blocks release promotion, not preparation of reviewable packages.

The current repository is private and has no product license. The requester
selected preparation for making the existing repository public; visibility is
unchanged until an explicit review of the publication inventory and final action.
The requester confirmed ownership and authorized use of the installed Developer
ID Application identity (team XH6JHKYXV8). Notary Keychain profile and license
selection are pending user input. No certificate/private-key extraction occurs.

Current master advanced through #48; its official product documents are unchanged
from this checkout. Read the new artifact-retention procedure and preserve its
handoff expectations without importing or overwriting another task's board rows.
Reuse .build/task47/preview/cargo and pinned downloads; create only a small new
app/package candidate under .build/task47/release-candidate. Budget less than
300 MiB additional for Pear builds, package copies and source audit reports;
17 GiB free was observed with df before this revision. No additional Wine clone
or game download is planned. Retain signed candidate and minimal sanitized
receipts through release review; private prefixes and saves remain protected.
Superseded app-only packages become disposable after the replacement is verified
and no process uses them. Runtime/download caches serve remaining required tests.

Selected checks: locked/offline Rust tests and release build, CLI help/invalid
argument refusal without setup, shell syntax, package allowlist and artifact
checksums, app/CLI codesign verification, notarization status/staple/Gatekeeper,
actual normal app Steam handoff, governance/link and whitespace checks. The
historical Whisky DMG checks remain retained evidence for that removed candidate;
its notarization never transfers to the Pear app. Preserve all remaining Stage
1-3 game/recovery/security requirements and report missing resources explicitly.


## October 11 Notarization Verification Correction

The requester completed interactive pear-notary credential registration after
accepting Apple's updated agreement. Submit the already reviewed app and CLI
candidates using that Keychain profile; no new credentials are collected.
Both submitted candidates were accepted. The app staple, deep/strict signature,
Gatekeeper assessment and syspolicy_check distribution passed on the build host.

The raw CLI spctl execute assessment rejected its non-app shape. This is the
wrong product-type probe for a command-line binary, not a failed notary request.
Apple's Testing a Notarised Product guidance (thread 130560; revised December 5,
2024; reviewed October 11, 2026) uses codesign with an explicit notarized
requirement for other code. That exact check passed on the accepted CLI. Correct
package.py and the existing release guide to enforce that check for CLI and
syspolicy_check for the app. Preserve the initial rejection in evidence and keep
actual clean-environment download/execution as a separate mandatory release gate.
No runtime, launcher or authentication behavior changes, and no source-license
choice, visibility transition or stage transition is authorized by this correction.


## October 11 Requested License Review

The requester asked for a license review and whether GPL is the safer choice.
Review the current Pear app/CLI boundary, the pinned runtime and existing
repository exceptions within Stage 1. The existing reuse investigation and
sanitized observations hold dated findings; the approved package notice file
holds recipient-facing component facts. No new official document destination is
needed. This review does not select a root license or complete a stage.

Prepare GPL-3.0-or-later as the concrete recommendation for original Pear code
without an existing separate license, subject to the copyright owner's choice.
Retain all existing per-file terms and framework/upstream notices. Compare
copyleft protection with redistribution obligations; do not equate GPL adoption
with clearance of the external runtime or proprietary components.

Inspect only existing cached binaries and small upstream license/build texts.
Do not rebuild or replace the runtime. Keep the notarized candidate sealed;
changed packaged notices require a new final build/sign/notary cycle. Validate
the recorded inventory, documentation/governance and whitespace; no new runtime
execution is needed for this review.


## October 11 Owner Approval: GPL-3.0-or-later

The requester explicitly selected "GPL-3.0-or-later" after the bounded review.
Adopt that license for original Pear code with no existing separate license.
Preserve all existing third-party/file/directory terms; this approval does not
license proprietary components or close runtime provenance.

Location judgment: use the already approved root LICENSE for the canonical
GPLv3 text and README's existing licensing section for the later-version and
scope notice. Update the existing licensing paragraphs in the contributor guide,
preview guide, release guide and delivery plan to reflect this approved choice;
these are consistency edits for their current audiences, not new documentation.
Set package license metadata in both Pear Rust crates. Retain the exact upstream
Madeira additional permission beside its adapted CPU fixture as
tests/cpu/LICENSE-MADEIRA-EXCEPTION.md; this is an upstream license attachment,
not a second product guide. Add no new license terms to upstream files.

Keep existing sealed candidates intact. Build/sign a separate GPL candidate,
verify license/notice inclusion and package boundaries, submit app/CLI to Apple,
staple accepted app and recheck extracted packages. Do not use --release while
the source is uncommitted or treat these local checks as clean-user qualification.
The remaining stage, runtime, visibility and release gates still apply.


## October 11 Approved Public Onboarding and Branding

The requester explicitly approved the Diataxis-oriented public documentation,
community and compatibility-report direction in this thread. They supplied
pear_icon.png for the app and confirmed pear.png for README/favicon. They selected
GitHub private vulnerability reporting and GitHub content reporting, with no
public personal email. Continue within #47 Stage 1; no stage transition, repository
visibility change, release upload or game qualification is implied.

### Location judgment and reuse

| Location | Audience and purpose | Alternative and decision |
|---|---|---|
| README.md and docs/README.md | Player/contributor navigation | Reuse existing entry points; do not create a second roadmap |
| docs/rosetta-preview.md | First Steam experience | Keep the existing tutorial and recovery/reference sections; avoid empty category folders |
| docs/development/getting-started.md | First local contribution/build | Separate from maintainer signing instructions |
| docs/development/rosetta-free.md | Native engineering entry | Link existing source/build/evidence guides and Issues; no new native-preview claim |
| docs/community.md, docs/SUPPORT.md, docs/SECURITY.md, docs/CODE_OF_CONDUCT.md | Public participation and reporting | Official docs root; original concise conduct policy, not internal workflow manuals |
| docs/compatibility/README.md, reports.json, records.md | Reviewed observations and evidence meanings | Versioned JSON and generated table; Wiki is navigation only |
| .github issue/discussion/PR templates | GitHub intake | Reuse existing categories; retain the internal PR/task forms separately |
| tools/compatibility.py and tests/docs/test_compatibility.py | Deterministic public-record renderer | Python standard library; no database, privileged ingestion or new web service |
| .github/workflows/compatibility-pages.yml | Optional public catalog deployment | Official pinned GitHub Actions; public/master plus explicit variable gate; never publish private checkout/history |
| docs/assets and preview/assets | Requester-provided branding | Exact source images; native sips/iconutil format conversion, no generated artwork |
| mydocs/working/task_m3_47_community_posts.json and existing observations | Prepared posts, resulting URLs and validation evidence | Task-owned records, not competing product guidance |

Reviewed Diataxis purposes and GitHub community/form/Pages/security documentation.
Keep technical instructions in their current homes and expose tutorial, how-to,
reference and explanation paths through the index. Build a small static catalog
from reviewed data only; submissions never auto-promote into support claims.
Re-use GitHub Discussions Show and tell for the game-report form and Announcements,
Q&A and General for introductory posts. Prepare exact text before posting.

Private vulnerability reporting requires a public repository. Maintainer-directed
content reports have organization/feature availability constraints; link GitHub
Support's private abuse route without promising maintainer delivery. Record both
activation and availability in public-opening checks.

### Affected verification

Run governance and existing docs tests, validate form syntax, and exercise renderer
rejection of malformed/unsafe/overstated evidence and private-output leakage. Check
generated Markdown freshness and browser rendering/favicon. Generate the ICNS from
the supplied app image, inspect its sizes and bundle reference, rebuild/sign a new
candidate, check package allowlists, notarize and staple, then assess extracted app
and CLI. Preserve older candidates and all incomplete runtime/source/recovery/
clean-Mac gates. This branding change does not require another Steam login.


### Public-onboarding verification checkpoint

October 11: implementation and bounded checks completed for this extension.
Governance: 37 documents / 350 local targets; 46 documentation/catalog tests,
4 package-boundary tests and 9 Rust tests passed. YAML syntax and whitespace
passed. Desktop browser rendering and exact requester-source image copies were
checked; ICNS decoded into 10 representations. GitHub form rendering awaits
default-branch integration; Pages remains disabled.

Four approved introductory Discussions were posted (#50–#53) in the still-private
repository. App and CLI notarization accepted the branded candidate; extracted
app signature/staple/Gatekeeper/distribution and CLI notarization/help passed.
The existing sanitized observations contain artifact hashes, submission IDs and
source input identities. The current Rust build retains an existing dead-code
warning; no test failure was hidden. Stage 1 and Issue #47 remain in progress;
this checkpoint does not bypass runtime provenance or later required gates.


## October 11 Approved Website Review Checkpoint

The requester approved the proposed concise home, Steam identity/artwork, grouped
game details, environment-specific reports and GitHub-backed demand links. They
explicitly require visual review and approval after the website is ready before
any next step. Keep this work local: no merge, visibility change, Pages deployment,
new remote Discussion, form activation or release promotion until that approval.

Retain the accepted headline "Windows games on Mac." Add the final Rosetta-free
goal in a short supporting sentence and label current Rosetta Preview requirements.
Keep detailed claim/evidence rules on game details and documentation.

Location judgment: extend the existing tools/compatibility.py renderer and
tests/docs/test_compatibility.py. Put its maintained CSS/JS in tools/catalog/;
these are implementation assets, not a second documentation root. Add reviewed
game/store/demand metadata at docs/compatibility/games.json; keep execution
observations in reports.json. Update the existing compatibility/community guides
only for the changed user flow. Generated flat game-{AppID}.html, report.html,
request.html, about.html and public assets remain an exact output allowlist, under
the ignored local site build. Retain task review evidence in existing observations.

Reuse: preserve Python standard-library rendering and GitHub Discussion categories,
identities and votes; use native browser form, search, select and details controls.
No new framework, authentication service, vote store or automatic ingestion.
Verify Steam artwork URLs against the public store page; reference upstream
artwork without copying game assets into the repository or claiming GPL rights.
Use a fallback when remote artwork is unavailable. Do not invent games, votes,
users, support or successful tests to fill the UI. Null vote snapshots remain
unavailable rather than zero. Game requests and test reports stay distinct.

The current game has no canonical demand Discussion; show a truthful create-request
path instead of reusing introductory-post votes. A new structured report flow can
prepare a copyable local draft and open GitHub without submitting or storing it.
Make the pending GitHub category-form state visible at that handoff; after approved
integration the same entry will use the live GitHub form.

Verification: preserve evidence validation, add grouping/outcome/metadata/output
allowlist tests, test desktop and narrow layout, search/filter/sort empty states,
game detail navigation, draft/copy/report/request handoffs, image fallback and
absence of runtime/private output. Keep the server available for requester review;
this is not final teardown. Stop for the explicitly requested visual approval
after the concrete working preview and checks are ready.

## October 11 Website Visual Feedback Revision

The requester asked for another local revision before visual approval: simplify
hero copy, remove the Apple Silicon eyebrow, correct the narrow-screen Pear image,
put game/environment headings before badges, use the same structured test fields
for every report, prevent game-name typos with Steam identity selection, and
prepare a home download entry plus app/CLI installation guidance.

Location judgment: continue in tools/compatibility.py and tools/catalog/, add only
its generated download.html to the existing site allowlist, amend the existing
compatibility guide and local Discussion template for the structured fields, and
retain evidence here and in the existing observations JSON. No second docs root,
new hosting service, runtime/package change or remote mutation is authorized by
this review. Keep the original visual-approval gate.

Reuse and choices: reuse the current reviewed games.json, native select/input
controls, Python renderer, existing CLI commands and GitHub handoff. Game identity
is numeric Steam App ID; a known catalog selection supplies its canonical name,
and pasted Steam URLs normalize to that ID. Unlisted IDs remain clearly pending
metadata review and can still be reported/requested without inventing a name.
Steam's documented IStoreService/GetAppList requires a Web API key, and
ISteamApps/GetAppList is deprecated (official docs checked October 11, 2026).
Do not expose a key or introduce an unapproved live proxy. Full Steam search can
later use a reviewed server-side lookup or generated metadata snapshot.
References: https://partner.steamgames.com/doc/webapi/IStoreService and
https://partner.steamgames.com/doc/webapi/ISteamApps.

Home directs to a dedicated download guide. App/CLI download controls remain
unavailable until actual approved assets exist; the planned DMG is not represented
as a built or published package. Show copyable existing CLI commands with the
extracted-CLI prerequisite. Homebrew is a later alternative after versioned,
verified release assets and a tested cask; no fictitious brew command. Reference:
https://docs.brew.sh/Cask-Cookbook (checked October 11, 2026).

Uniform report layout preserves result, play time, observed/failed/not-tested
checks, evidence level, reproduction and qualification links. Replace the initial
record's repetitive global limitation paragraph with its specific menu-input
limit; unperformed work stays visible as structured states and shared definitions.
No evidence promotion or acceptance-rule change. Verify ID normalization and
mismatches, unknown/invalid IDs, form reset/stale draft behavior, structured output,
copy buttons, title hierarchy, 800px image aspect ratio, mobile layout, allowlist,
existing document/catalog checks and unchanged release availability.


## October 11 Typography and Control Alignment Feedback

The requester approved removal of the remaining uppercase eyebrow captions,
consistent dropdown-arrow spacing at every width, and vertical alignment of the
Steam link with the game-name input. Continue in the existing renderer/CSS, with
no new document destination or dependency. Reuse native select interaction and
replace only its visual arrow with a small inline SVG; retain native arrows in
forced-colors mode. Place the name label outside the input/link alignment row.
Check home/detail/report/request selects at desktop and mobile widths and retain
review screenshots. No new tests are needed for these presentation-only edits;
existing catalog checks and focused browser inspection are sufficient. The
requester also asked for Steam API-key issuance guidance; no key has been received
and full-catalog synchronization/search is not implemented by this UI polish.
The existing visual approval and publication gate remains in effect.

## October 11 Approved Steam Search Extension

The requester asked to add whole-Steam name search and then confirmed storage of
STEAM_WEB_API_KEY. The secret name (not its value) was verified through GitHub on
October 11. This authorizes implementing and validating the search inside the
ongoing website review; it does not approve publication or a stage transition.

Location judgment: extend the existing tools/catalog/ intake, use a small
standard-library tools/steam_catalog.py metadata synchronizer, its synthetic
checks in tests/docs/, and .github/workflows/steam-catalog.yml. Amend the existing
docs/compatibility/README.md with maintainer snapshot instructions; no new docs
root. Record evidence in the existing task observations. Reuse Valve's documented
IStoreService/GetAppList with input_json, pagination and x-webapi-key on the public
api.steampowered.com host. Reviewed October 11, 2026:
https://partner.steamgames.com/doc/webapi/IStoreService,
https://partner.steamgames.com/doc/webapi_overview/auth and
https://partner.steamgames.com/doc/webapi_overview.

Use a full games-only snapshot, stripping upstream responses to App ID and name.
Keep it separate from reviewed compatibility records, requests and votes. Static
same-origin lookup gives immediate suggestions; it is not a fresh upstream query
per keystroke. Display the snapshot date and a usable fallback on fetch failure.
No public proxy, browser secret, third-party search service or new dependency.

The saved Actions secret can only be used on a runner. Validate the minimal fetch
script and constrained workflow locally first, then run them on the private,
temporary codex/task47-steam-catalog-check ref. Only the fetcher, its tests and
workflow go to this integration-test ref; website/source task edits remain local.
The workflow uploads only the sanitized JSON artifact and cannot deploy Pages,
write repository contents or post messages. This is within the requested search
verification, not public website integration. Keep the ref/artifact through visual
review; clean up after integration when no longer needed. No recurring schedule
is activated. The existing Pages public/variable guards remain unchanged.

Check bounded pagination, malformed/duplicate IDs, discarded response fields,
non-secret diagnostics, refused redirects, atomic output, fetch failure fallback,
keyboard selection, stale selection/draft clearing, literal text rendering,
large-index matching, App-ID grouping, mobile overflow and existing site checks.


Steam search verification completed inside the review checkpoint: the constrained
private CI run 38074068985 generated 192,045 named Steam game identities. The first
live run exposed blank/control-character names, and the second artifact exposed
an incomplete first-page assumption; both were corrected before acceptance.
The final fetch continues by last App ID until the API returns no entries, without
relying on optional response flags. 72 Python checks and 6 Node search checks pass;
real browser selection, draft identity, missing-list fallback/retry and mobile
layout pass. No stage transition or website publication occurred. Retain the
private verification ref and artifact through review; exact evidence and hashes
are in the existing observations JSON. Website visual approval remains pending.

## October 11 Download Method Navigation and Diataxis Review

The requester asked to expose App, CLI and Homebrew at the top of Downloads,
show one method's instructions at a time, and investigate whether Diataxis helps
the catalog. This is another approved local website revision before visual
approval, not permission for publication or a stage transition.

Location judgment: change the existing download renderer in tools/compatibility.py
and shared tools/catalog/ assets; retain the inquiry and decision here and test
observations in the existing working JSON. No new public documentation page,
new framework, hosting operation or catalog-wide navigation rewrite is needed.
Existing player/contributor documentation stays at its approved docs/ locations.
Reuse native anchors, existing copy controls and the WAI-ARIA tabs pattern; keep
all method sections accessible without JavaScript. Preserve download.html#cli
links and add #app/#homebrew links. Keyboard arrows/Home/End move and activate tabs;
Tab enters the selected panel. App is the default. Shared essential platform
requirements stay visible. Secondary requirements and additional CLI commands
can expand on demand. Unreleased app/CLI buttons remain unavailable; Homebrew
has a planned explanation and no invented installation command.

Research (primary sources reviewed October 11, 2026):
- https://diataxis.fr/start-here/ distinguishes learning, task completion,
  lookup and understanding, and recommends small practical improvements.
- https://diataxis.fr/how-to-guides/ keeps task instructions focused and links
  to background/reference instead of embedding every detail.
- https://diataxis.fr/reference/ recommends neutral, consistent lookup patterns.
- https://diataxis.fr/explanation/ concerns context and understanding.
- https://www.w3.org/WAI/ARIA/apg/patterns/tabs/ supplies the interaction pattern.

Pear-specific assessment (design inference, not measured user-study evidence):
Diataxis is useful for the information behind the catalog. It is not a mandate
for four top-level product-navigation categories, nor evidence that tabs are
universally better. Three short method tabs expose the alternatives at once on
this page; a dropdown would hide them until opened. Keep Games / Download / About
navigation and concise task labels. Apply the four needs as follows:

| User need | Pear destination | Approach |
|---|---|---|
| Learn the first Steam session | Existing player guide; future verified release walkthrough | A guided end-to-end experience after delivery qualification, not a claim that the current unavailable download can be followed today |
| Install, run or share a result | Method-specific Download panels and report/request forms | Short steps and immediate controls; link to details |
| Compare game behavior | Game catalog/detail records, environment, versions and checks | Consistent reference fields, filters and dated evidence; no support inference from votes |
| Understand differences | About/result meanings, Rosetta track explanation and canonical roadmap | Context reached by relevant links, not repeated on each record |

Current uniform report fields and separate forms already fit this approach.
Recommended follow-up after visual approval: assess first-use learning separately
once the release works, and separate any growing result-reference and project
background articles only when content volume requires it. Do not create empty
Diataxis quadrants or additional pages solely to mirror the framework.

Verify all three methods, default/deep-link/reload/hash behavior, keyboard and
focus semantics, copy controls, narrow layout, non-JavaScript fallback, unavailable
release controls, existing docs/catalog checks and unchanged public-output scope.

Requester refinement before visual approval: remove the large method-panel card.
Keep only short installation instructions and the relevant download/launch control
in each tab. Move common official Steam sign-in, game selection and requirements
into always-visible prose below all panels. Remove the extra inline CLI reference
commands in favor of the existing player guide. This supersedes the expandable
shared requirements and panel-contained app walkthrough above. Locations and
publication gates are unchanged. Verify shared content persists across methods.

## October 11 Website Approval and Publication Preparation

The requester explicitly approved the reviewed website ("승인할게") after the
compact download tabs and shared prose were presented. The local visual checkpoint
is satisfied for the source hashes in website_download_navigation. The requester
also asked whether the Diataxis recommendation is being applied; confirm it is
implemented through existing entry points: first Steam session tutorial, download
and report/request tasks, common game-result reference fields, and About/result
explanations. Retain task-oriented navigation; no new category pages are needed.

Resume the already authorized publication preparation. This approval does not
change the selected repository-visibility final-action decision or resolve runtime
source, recovery, gameplay and clean-distribution gates. Stage 1 still has a partial
runtime identity/provenance result; do not write a completed stage report or
publish an incomplete release. Read-only inventory confirms two remote branches,
no tags/releases, four existing introductory discussions and fifteen Actions
artifacts. These artifacts/logs remain in the final publication inventory.

The bounded source review scanned 1,884 available remote-history blobs and 1,300
tracked/nonignored working files. No selected key/token/private-key pattern
matched. This is not a complete security audit. Existing historical personal paths
and Git authorship remain review items; nothing is rewritten or deleted. Master
contains Task #48 retention changes not present in the current task base. Preserve
those changes during eventual integration; a direct working-tree comparison is
not a valid final PR diff. No shared branch/worktree was modified.

## October 11 Approved Runtime Provenance Follow-up

The requester explicitly approved proceeding with the runtime provenance review.
Use the existing reuse investigation, component notices and observations JSON; no
new official documentation destination. Inspect the actual v3.1.1 tag instead of
assuming later app-tag documentation identifies the release. Compare upstream
release binaries read-only where public text cannot establish correspondence.
Allow up to 250 MiB of task-owned comparison downloads within the observed 15 GiB
free space; stream archive contents without extracting/running them. Preserve
upstream notices and hashes, do not execute assembly scripts, remove quarantine,
replace the installed runtime or alter sealed candidates. Keep unmatched sources
and build recipes unresolved. Retain concise evidence and review inputs until
source admission or an explicit runtime replacement decision.


## October 11 Approved Replacement Candidate Validation

The requester explicitly authorized validating a replacement runtime for sustainable
Preview maintenance and proceeding toward distribution after verification. Do not
send the prepared upstream inquiry. This supersedes the previous preference to
contact upstream before selecting a replacement; it does not turn an unverified
candidate into a release or waive the existing stage checks.

First compare the already hash-verified Gcenx Wine 11.0_1 archive with DXMT 0.80,
reusing upstream binaries and the previously inspected pairing/layout behavior.
Use a task-owned isolated runtime and fresh prefix, never migrate or copy signed-in
prefixes. Preserve the working Whisky runtime and sealed app as historical inputs.
No Wine/Steam/game processes were active at the initial process check. Public
Gcenx documentation provides build options and MacPorts/overlay dependency origins;
exact component/source correspondence still needs its own recorded assessment.
Do not assume the current overlay is the release's build recipe.

Location judgment: retain decisions in this implementation plan and existing reuse
investigation, observations in the existing Stage 1 JSON. Necessary bootstrap and
focused checks stay in approved preview/ source paths. Existing component notices
and release guide remain the product documentation locations; no new public page
or documentation root. Candidate-only assembly/diagnostics stay under ignored
.build/task47/runtime-candidate, with private execution state excluded from Git.
Keep concise identities/results; retain diagnostic inputs through candidate review.

Start with isolated extraction, dependency inspection, version/prefix initialization,
then the shared Pear setup and official Steam flow if those checks pass. Preserve
normal macOS protections and original artifact bytes except the explicitly recorded
DXMT pairing/marker transformation. No quarantine deletion or authentication bypass.
Fresh Steam authentication is performed by the owner if required. Record failures
before deciding whether another upstream package or a source-built Wine is needed.
Do not claim Rosetta independence, performance improvement, gameplay qualification,
or clean-machine delivery from these candidate checks.

Read Task #47 and open Issues before this revision. #10/#11/#46 remain separate
native-runtime work; no inputs are imported from their moving branches. Master
still includes #48 retention work absent from this task base; preserve it during
later integration. No Stage 1 report exists because identity/launch admission is
still incomplete. Complete and report the stage before its next approval boundary.

Concrete candidate adapter: replace the in-development bootstrap's aggregate input
with two fixed, independently verified archives (Gcenx Wine and DXMT), assemble in
an owned staging directory and record both digests plus a versioned assembly ID.
Keep the same Libraries/Wine and Libraries/DXMT internal layout to reuse the
existing Steam flow. Pair winemetal.dll/.so and apply only the previously reviewed
six DXMT builtin marker replacements; validate marker bytes before writing.
No DXVK is needed by the selected D3D11 path. The old sealed CLI remains available
for its existing prefix. Reject a different prefix runtime marker before download
or Wine execution; do not implicitly migrate existing state. Keep the developer
archive override pinned, add a pinned DXMT override, and build the new app in a
separate output directory. Test wrong inputs, modified runtime inventory, marker
validation, and old-prefix preservation before the owner login test.

Candidate startup correction: the owner reports that Steam's updater disappears
without a login window. Candidate-only CEF logs report SwapChain11 reset failure,
HRESULT 0x80004005 and EGL_BAD_ALLOC while creating DesktopLoginWindow. Processes
remain alive. Test Steam's own -cef-disable-gpu flag for its web UI only, retaining
the DXMT game path and all sandbox/security settings. Verify the flag in the
installed official client and perform a controlled restart only of this new
unauthenticated prefix. No Metal API/shader change or GPU capture is involved;
Apple Metal expert routing was inspected but no specialist is needed for this
Steam command-line experiment. Preserve the original failed observation.


Candidate rendering revision: the owner confirmed a solid black Steam window after
-cef-disable-gpu. Record this attempt as failed and remove that experimental flag
from subsequent rendering tests. DXMT issue #141 documents the matching cross-
process swapchain failure. Read Whisky Wine.swift at
3abfbae945e3400caaa13cf2e78fe5a187a1405b for launcher-specific DLL overrides,
DXVK pairing and Wine dxgi marker handling. Its native-file overwrite ordering is
not sufficient evidence that DXMT and DXVK can coexist for every Steam-launched
game; do not copy that ordering or claim success without module-load evidence.

First run a task-owned diagnostic assembly, using copy-on-write copies of the
failed, unauthenticated candidate runtime and prefix. This is not a fresh-install
qualification. Preserve both originals. Put unmodified DXMT D3D/bridge builtins
in the diagnostic Wine tree, and DXVK native D3D DLLs plus marker-stripped Wine
dxgi in its prefix. Global registry selects builtin DXMT; Steam and its known
helpers select native DXVK/Wine dxgi through AppDefaults. Remove graphics entries
from WINEDLLOVERRIDES so children can resolve their own program scopes.

DXVK input is the already verified Gcenx native v1.10.3-20230507-repack archive,
2,793,443 bytes, SHA-256
acd1520ad105d8ef124a09c8e11a259a5dc8bdc565ad18e0e52693f9807b2477.
Retain its zlib license and exact source pin
8f1e28deed3ad30802f7e1bdff428ec14e6e7817. No Steam executable is replaced, no
updater/authentication/sandbox protection is disabled. Probe registry selection
and loaded modules as well as visible UI before adopting this layout in the
bootstrap. If it works, use a new immutable assembly ID and independent three-
input hashes, update the same notices/evidence locations, and rerun setup in a
fresh prefix. If it fails, preserve the bounded negative observation.


Source-build candidate assessment after both renderer attempts failed: inspect
CodeWeavers' official crossover-sources-26.3.0.tar.gz (149,054,023 bytes, locally
measured SHA-256 ac99c8ca4b3848f3e81784135f023df266b61c2345726ea55a50b3e030dd6872).
The archive's Wine VERSION is 11.0 and LICENSE is LGPL-2.1-or-later. Extract only
that Wine source into ignored task-owned state, preserving original notices.
Assess configure/build with existing host tools and the already identified
x86_64 helper libraries as a diagnostic dependency set. Do not install packages
system-wide or copy proprietary CrossOver/D3DMetal code. This build is an isolated
candidate experiment, not a distributable runtime: dependency source closure and
full qualification remain required. The 11 GiB available at assessment bounds
storage; inspect configure prerequisites before compiling. No new product document
or changes to another task's source/build tree.

Source-built Wine completed compilation, installation, prefix initialization and a
DXMT D3D11 device creation probe. Official Steam updated to 1788652215, but the
requester confirmed a black login window. This is a failed UI observation, not
a successful replacement. Test the official client flags -cef-disable-gpu and
-cef-disable-gpu-compositing together in this same diagnostic prefix to isolate
CEF GPU composition from game DXMT. Both flags were found in the installed
Steam binaries. Preserve the initial module log; do not change Steam payloads,
update behavior, sandbox options or product bootstrap defaults.

Requester-directed cleanup after the final black-screen observation: retire failed
configuration payloads, retaining bounded metadata and original source/input hashes
in the existing evidence locations. Preserve the successful baseline and all
authenticated/game/save state. No new runtime experiment or stage transition is
part of this cleanup.

October 11 requester-approved baseline comparison: inspect successful Steam logs
and runtime DLL strings before rebuilding replacements. The successful webhelper
command line includes --no-sandbox --in-process-gpu --disable-gpu, and both
kernelbase architectures contain this injection string. Earlier statements about
unchanged security settings cover Pear-supplied arguments only and must not be
read as effective CEF sandbox verification. Do not relaunch real Steam with this
undisclosed workaround. Use an original, no-network argv-printing PE under a fresh
disposable prefix to compare ordinary, steamwebhelper-named and crashpad-handler
control cases. No official Steam binary is replaced; the dummy exists only in
the probe directory. Record outcomes in the existing reuse/evidence locations.
Do not import a full third-party runtime merely from this matching code pattern.

October 11 sandbox-preserving candidate authorized by explicit continuation: build
the same checksum-pinned official FOSS Wine source with one opt-in kernelbase
change. When PEAR_STEAM_IN_PROCESS_GPU=1 and the executable basename is exactly
steamwebhelper.exe, append --in-process-gpu only to the main CEF invocation; skip
subprocess --type= invocations and an already-present option. Do not add
--no-sandbox, disable-gpu-sandbox, disable-site-isolation or --single-process.
This does not itself prove CEF sandbox functionality: inspect effective commands
and observe execution before claiming success. Reuse the reviewed upstream
WineAndAqua process-launch pattern, with original bounded matching/gating code;
retain upstream Wine LGPL notices and an exact patch. No Steam file replacement.

Use ignored .build/task47/steam-inprocess-candidate for source/build/probes.
Existing baseline helper dylibs are read-only diagnostic dependencies, not admitted
release inputs. Keep product bootstrap and authenticated state untouched. Validate
argument controls before fresh official Steam setup. Download the source and
task-local Bison again only for this newly evidenced change; remove temporary
archives after checksum-verified extraction. Preserve small recipes/patch/results
and clean disposable build outputs after the result. No stage transition, new
public document or release is authorized by these diagnostic checks.


October 11 continuation authorizes independent-runtime preparation after the
requester reported problem-free gameplay on the in-process candidate. Record
that report without inferring duration, audio, save or recovery qualification.
Continue Stage 1 source/delivery admission. Keep authenticated prefixes unchanged.

Location/reuse decision: existing preview/ will own eventual runtime build inputs
and patches; existing Task 47 observations/reuse records retain investigation.
Use ignored .build/task47/portable-runtime for a source-pinned dependency build
and relocation tests before changing the product bootstrap. Reuse upstream C
build systems. The CodeWeavers aggregate includes old GnuTLS 3.8.3, so do not adopt
that dependency merely because its source is available. Pin current upstream
release URLs and hashes from Homebrew's recorded metadata, then inspect exact
licenses/configuration. No installed Homebrew package or global prefix changes.

First build the TLS/font dependency closure as x86_64 shared libraries in a local
prefix; omit optional tools, translations, hardware-token integration and font
WOFF2 shaping dependencies from this bounded diagnostic. Preserve TLS certificate
verification. Audit direct Mach-O loads and Wine's dlopen sonames, including
Vulkan, before claiming independence; unsupported/unbuilt paths must stay explicit.
Validate a relocated candidate with ordinary argv/device/network checks before
any authenticated reuse. Preserve successful diagnostic artifacts and keep all
private data out of runtime packages. No public release or stage transition yet.


## October 11 Resumed Source-kit Preparation and Artifact Retention

The requester resumed approved Stage 1 through the coordinating chat. Keep
preview/ as the implementation destination: runtime_build.py, runtime-inputs.json,
patches/steam-inprocess.patch, runtime-notices/ and focused test_runtime_build.py.
Reuse the reviewed source-built dependency recipes and upstream build systems.
No public guide relocation, Stage 2 transition or publication is included.
The previous diagnostic recipe incorrectly skipped deleted dependency outputs
when old passed receipts survived. A new build requires an absent output root,
verifies all input archives and notices, records the current compiler/SDK/tools,
and never treats prior receipts as proof that installed files exist.

| Artifact/root | Class and state | Owner/consumer | Identity/recovery | Release condition |
|---|---|---|---|---|
| portable-runtime/source-cache and Wine archive | Source inputs; retained | #47 reconstruction | runtime-inputs.json hashes | Keep for source delivery; no private payload |
| preview/runtime-inputs.json, patch, notices, build script | Source; active | #47 build/source kit | Exact patch/archive/notice hashes | Retain in source history |
| /private/tmp/pear47-rebuild-v1 | Isolated mutable build output; planned | #47 only | Fresh source extraction, source-built deps, one runtime | Release objects/extracted inputs after successful build and needed evidence capture; retain latest runtime for admitted checks |
| Existing private prefixes and saves | Private state; retained | User/#47 | Preserve original and successful test prefix | No deletion authorization |
| Historical deleted portable Runtime | Released | No current consumer | Historical manifest only | Must rebuild and revalidate; never infer present availability |

Expected peak additional allocation is approximately 9 GiB (Wine objects, source
extraction, dependency objects, one 1.5 GB runtime and possible small source kit),
with 3 GiB headroom for uncertainty/concurrent system activity. Measure filesystem
free bytes immediately before build; do not confuse du totals with recovered
physical space. No new full runtime/prefix copy is planned. The runtime is built
once into isolated output because Wine configure/install and signing modify it.
Build only after task11-first-d24.json has released:true, current processes are
checked and the existing shared flock is acquired. Hold it for build/run lifetime.
If release is absent, finish source preparation/tests and report the dependency.
No task11 source/runtime/prefix is imported or changed.

Reconstruction update: v1 stopped at Wine configure because the pinned Bison
path contained whitespace. Preserve its small failure receipts in
portable-runtime/rebuild-v1-failure; its disposable outputs were released after
an open-handle check. The fresh v2 root is /private/tmp/pear47-rebuild-v2 with
the same ownership, peak-space and release conditions. A local tool-prefix
symlink supplies a space-free Bison path without modifying the installed tool.
The source kit is allowlisted and excludes all Steam, game and private state.


October 11 requester continuation: finish the light Stage 1 source/delivery review
without reclaiming the shared heavy slot from #46/#11. Keep implementation and
bundled notices in existing preview/; record review findings in the existing
reuse/observation documents. Add exact upstream Wine bundled-library notices and
font attribution, a machine-readable delivery checklist and source-kit inclusion
checks. Do not mutate the validated v2 runtime or transfer its execution claims
to an updated package. Notice-only additions require package inventory validation,
not another full Wine compile. A later admitted package still needs the approved
signing and execution checks.

Review cache: .build/task47/source-delivery-review, owner #47; retain exact upstream
metadata and small source archives for provenance until final delivery admission.
Peak additional storage below 300 MiB including one revised source kit; retain the
validated earlier kit separately while referenced by its historical receipt.
No runtime/game/prefix copy or execution is part of this follow-up.


## October 11 Approved App/CLI Runtime Integration

Direct requester approval: finish remaining notice comparison, connect the new
runtime to app and CLI, and verify. Continue Stage 1. Reuse the successful v2
executable payload; no full Wine rebuild. Keep changes in existing preview/
(core, launcher, runtime packaging and focused tests), with findings in the
existing task evidence/reuse documents. These are the approved locations; no
public documentation relocation or publication is included.

Package one pinned Pear runtime archive with Libraries/Wine and Libraries/DXMT.
Retain all exact baseline runtime bytes except updated notices/lock metadata;
record any additional native-DXMT override payload separately. Both entry points
use the same Rust core, archive hash and isolated runtime identity. Remove the
rejected Gcenx download path; before publication an explicit candidate archive
is required. Do not silently migrate any existing prefix. Preserve private state.

Retention: .build/task47/integrated-runtime-v1 is owned by #47. Packaging may use
one temporary full copy to isolate notice/layout changes from the validated
baseline; release that staging copy after archive and extracted inventory checks.
Retain the archive, its receipt and one installed test runtime until integration
and distribution consumers complete. Preserve all authenticated prefixes/saves.
Expected peak additional allocation is 5 GiB including staging, archive, one
installed runtime, fresh Steam prefix and small app/CLI build, plus 3 GiB headroom.
Recheck actual space and shared-slot ownership before material work. Small notice
fetches and source edits may proceed independently. #11 retains next heavy
priority; a live user game session never counts as a released slot.

Verify exact notice pins, unchanged baseline executable hashes, package path and
private-data exclusion, app/CLI common runtime selection, prefix incompatibility
refusal, installation/inventory tamper refusal and patch environment. Build and
perform fresh-prefix Steam/app checks only after live coordination permits.
Signing/notarization, Steamworks evidence and ordinary-user qualification remain
separate from compiler/unit-test success.

Packaging refinement: stream the allowlisted immutable runtime directly into the
archive and inject updated notices plus native DXMT overrides. This avoids the
planned full staging copy; the prior 5 GiB estimate remains a conservative cap.
Only a fresh installed test runtime requires a full materialized copy.


## October 11 Signing and Nonconflicting Verification Continuation

Requester approval: continue nonconflicting work, verify Steam/game through the
new app when execution priority allows, and perform distribution signing and
notarization. Continue Stage 1 and preserve all existing approval boundaries for
public release/repository visibility. Reuse the verified app/CLI executable code;
copy the small app into .build/task47/integrated-signing-v1 before signing with
the previously authorized Developer ID. Do not mutate the previous test candidate.
The app/CLI require no Hardened Runtime exceptions. Submit only audited app/CLI
archives to Apple's notary service using pear-notary. Record exact signed hashes,
submission IDs, logs, staple and policy results. A notarized launcher does not
qualify its separately installed Wine runtime or unperformed game checks.

Retain one small signed app and candidate ZIP/DMG artifacts plus receipts for
normal-open tests; release superseded submissions only after final matched
artifacts verify. Peak additional storage under 200 MiB for this phase. A later
signed runtime copy needs its own measured copy/retention plan and host execution
checks because signatures change its bytes and policy. No authenticated state is
included or copied. Heavy/game execution continues to honor #11 priority and the
shared lock; live user testing is not an available slot. Existing preview/ signing
and packaging tools and task evidence remain the implementation destinations.


Runtime signing substep: use existing preview/ for runtime_sign.py and a narrow
Wine entitlement plist. Apple Hardened Runtime requires executable-memory
exceptions for unsigned generated/loaded code; pinned Wine virtual.c maps Windows
PE executable sections with mprotect/PROT_EXEC (lines 1931–1938 and 3249–3251).
Use only com.apple.security.cs.allow-unsigned-executable-memory on the two Wine
loader executables, no disable-library-validation, DYLD or debug entitlements.
Sign all 45 Mach-O objects with the authorized identity and timestamp; wineserver
and dylibs receive no exceptions. Preserve original DLL/source/runtime bytes.
Compare __TEXT,__text before/after and unchanged non-Mach-O inputs. Retain original
runtime for prior evidence. Validate the signed candidate separately before
replacing the app/CLI runtime pin or making public claims.

.build/task47/signed-runtime-v1: #47-owned immutable candidate copy, ZIP submission,
manifest, signing record and later synthetic prefix. One full Libraries copy is
necessary because signing mutates Mach-O headers/signatures. Peak additional
storage 4 GiB (copy, submission/archive, later installed copy), with 3 GiB headroom;
measure before copying. Remove only synthetic state after owned processes stop;
retain candidate and submission until matched accepted package/consumer checks.
No full authenticated prefix copy or private state upload. References: Apple's
Notarizing macOS software before distribution and Allow Unsigned Executable Memory
Entitlement documentation, reviewed October 11, 2026. Signature and notarization
are distinct from normal game execution and release admission.


Signing checkpoint: app and CLI are Apple Accepted and the app ticket is stapled.
The signed runtime is also Accepted, but fresh synthetic Windows execution failed
at PE executable-section protection; native helper initialization passed. Retain
this as an execution failure, not a release candidate. Do not update runtime_pin.rs.
The failed prefix was stopped and removed after zero owned handles; the original
failure result stays immutable and its repetitive log is gzip-compressed with a
verified restoration hash. Validation now enforces a 16 MiB retained log ceiling
and per-command timeout, with targeted failure-mode tests.

Next runtime experiment (only after #11/#46 readiness priority and shared lock
permit): isolate whether library validation rejects Wine's third-party PE code.
Apple documents disable-library-validation for third-party loaded code. osxEQL's
public signing implementation reports the same noexec failure and uses four Wine
exceptions. Reuse this as a hypothesis, not proof of which exceptions Pear needs.
Try only the additional library-validation exception on the two Wine loaders;
keep the app, CLI, wineserver and libraries unchanged. No system security setting,
disable-executable-page-protection, debugger, DYLD or blanket JIT exception is
approved by inference. Any new signed bytes need fresh execution and notary checks.
Hardened Runtime may suppress DYLD_PRINT_LIBRARIES, so missing traces cannot be
counted as proof of helper isolation; retain an explicit evidence gap until an
external process-image observation or equivalent validated check is available.

Source-kit maintenance is independent of the heavy slot: publish no files; retain
a new local v5 kit containing the bounded validator and its tests. Temporary peak
under 500 MiB for the new archive plus independent extraction, plus existing v4.
After the extracted kit verifies all 11 inputs/127 notices and runtime tests, remove
its disposable extraction and the same-turn superseded v4 archive, retaining v4's
hash/size. Preserve historical v2/v3 kits referenced by earlier executable evidence.


## October 11 Signed-Runtime Retry Preparation

The requester explicitly continued error resolution and new app Steam/game checks,
subject to other experiments' execution order. Prepare only two loader copies
(65,952 input bytes) in .build/task47/signed-runtime-v2-preparation while runtime
execution waits for a fresh fair handoff. Add the documented third-party library
validation exception to the prior unsigned-executable-memory exception; apply it
only to these loader copies. Record signatures, executable text, plist and hashes.
This does not mutate v1, execute Wine, access a prefix, or grant a shared slot.
Retain the small prepared pair for the next isolated runtime candidate; discard
only after that consumer verifies. Preparation peak under 1 MiB; no runtime copy
until the shared execution interval is granted. All candidate execution and final
app/CLI pin updates remain conditional on actual successful checks.


Signed-runtime helper observation reuses macOS lsof on the exact owned Wine PID.
The synthetic PE fixture emits a flushed marker after crypto/font/TLS checks and
holds for five seconds. The existing bounded runner invokes one read-only image
snapshot at that marker. Require actual Wine mappings for GnuTLS and FreeType,
and reject native .so/.dylib mappings outside the candidate or system locations.
Keep native-probe initialization and Wine-process mapping evidence separate; no
DYLD-environment entitlement is added merely for diagnostics. Extend existing
preview/runtime_validate.py, runtime-smoke.c and focused validator tests; no other
process is sampled or terminated. These source-only changes and unit tests do not
consume the shared runtime slot; compile/PE execution still waits for admission.


Storage handoff for the waiting #46 assembly: the integrated-runtime-v1 installed
unsigned Libraries copy is now cold/restore-required. Its 533,646,314-byte pinned
archive, original CLI extraction result, inventories and manifests remain. The
archive's complete file hashes, symlink targets and modes matched the existing
successful extraction again before removal; no open handles were present. The
current signed-v2 trial consumes signed-v1 instead, so it does not need this old
installed tree. Restore from the preserved archive and revalidate before future
unsigned execution or signature reconstruction. The original path's parent contains
RESTORE-REQUIRED.json. No path/inode identity preservation is claimed.

Removed copy: 1,557,713,735 logical bytes; 1,561,681,920 stat-allocated bytes.
Measured filesystem free increase was 1,544,065,024 bytes, subject to concurrent
activity. Current signed v1, prepared v2 loaders, original successful runtime,
source kits, archives and every private prefix/login/game/save remain. Protected
signed input hashes were unchanged. Detailed receipt and restoration command:
.build/task47/integrated-runtime-v1/installed-copy-retirement.json. The shared lock
was returned; no runtime execution or new full copy occurred during this cleanup.


Signed-runtime v2 bounded host observation (2026-10-11): the two prepared
loader changes passed native initialization, Windows AES/font, positive HTTPS,
wrong-host rejection and actual Wine-PID packaged-helper mapping (20 native
images, no external helper). The previous noexec failure did not recur. Original
validation result SHA256 84234c37ef03a91951a3b704a64e1b25f637733436befef22cef2d4f15fcbf3e.
The wrapper failed because synthetic wineserver -k returned 1 without output.
Wine server/main.c uses exit(!kill_lock_owner(...)); server/request.c also returns
0 when no server remains, so this exit alone cannot establish a live failure or
successful cleanup. Independent lsof returned 0 with no owned handles; the new
unauthenticated prefix was removed (1,494,935,009 logical bytes; 1,498,808,320
stat-allocated bytes; measured net free increase 1,500,831,744 bytes). Private
sessions remained unchanged. See signed-runtime-v2/validation/cleanup-verification.json.
The slot was returned to #11 without a retry or Steam/game run.

The validator now accepts stop exit1 only provisionally: it still requires the
prefix-specific wait and successful independent empty-handle inspection. Other
exit codes, failed inspection and remaining handles fail cleanup. 29 focused
runtime tests pass; this revised validator has not been re-executed on Wine.
Automatic approval review rejected persistently adding disable-library-validation
to the production loader recipe pending explicit approval of that security change.
The requester was asked; production signing policy and app/CLI pin stay unchanged.
This checkpoint is neither notarization of the changed loaders nor app/game or
public-distribution qualification. Stage1 remains in progress.


Requester explicitly approved disable-library-validation on only the two Wine
loaders on October 11, 2026, and requested conflict-free new-app Steam/game
verification plus signing/notarization. This supersedes the prior security approval
wait. The app, CLI and other 43 runtime Mach-O images receive no new entitlement.
The existing signed-v2 bytes already match this approved candidate policy; reuse
them after exact inventory/signature verification rather than sign/copy again.
Current Task11 D27 allocation remains first; do not reuse the consumed Task47 grant.

Next retained outputs: signed-runtime-v2 (existing immutable Libraries, renewed
validation under an absent separate output, notary ZIP about 0.5GB); a versioned
integration root for the pinned archive (~0.55GB), installed runtime (~1.56GB), app
and CLI (<0.1GB) and updated corresponding source kit (~0.21GB). A fresh synthetic
prefix adds ~1.5GB temporarily and is removed after verified owned-process cleanup.
Estimated preparation peak additional bytes 4.5GB with 7GiB admission, serial
operations, and current free-space recheck before each material step. An isolated
Steam/game prefix may add several GB and is a later separately admitted operation;
its exact private-state preservation/reuse plan must be ready before launching.
Retain failed v1 evidence, successful v2 bytes and private data. Release superseded
archives only after final replacement/source/notary verification and consumer audit.


The freshly assigned preparation interval completed successfully. The revised
synthetic validator passed Windows crypto/font/TLS and owned-PID helper mapping,
then confirmed server exit and removed only its unauthenticated prefix. The shared
slot was released to Task11 with no owned handles. The signed-v2 archive is
534,424,618 bytes, SHA256 bf660c1ddf0a40cd2c7e345343b32f6515bf34c1fe6566aae337302f221a4127.
The new app and CLI pin this exact archive, pass 12 Rust tests and Developer ID
signature verification. The new corresponding source kit has 155 members, with
11 input archives and 127 notice files matching their pins. Source/recipe content
was streamed and compared in full; this is not another independent rebuild.
All artifacts and receipts are under .build/task47/integrated-signing-v2.
The coordinator permits independent Apple notarization network submission of
three completed ZIPs while Task11 observes its game; no global runtime lock is
held for network waiting. Actual new-app Steam/game still requires a fresh slot.


All three complete submission archives received Apple Accepted. The runtime's 45
Mach-O notarized-policy checks passed; the app was stapled and passed staple
validation, distribution policy and Gatekeeper checks; the signed CLI passed its
notarized-policy check. Submission ZIPs precede app stapling and are not claimed
as the final downloadable package. The original timed-out runtime submission is
retained as unknown and is not the acceptance evidence. An optional loader-only
submission was rejected by automatic review and not performed; the authorized
complete runtime ZIP was submitted instead.

The separately assigned CLI interval passed pinned extraction, installed-file
integrity and rejection checks for modified files, corrupt archives and a foreign
runtime prefix. The foreign-prefix sentinel was preserved, and the app's bundled
CLI equals the signed standalone CLI. No private prefix, Steam or game started.
Owner PID 11618 exited, independent lsof found no state handles and the shared
lock was released. Evidence: integrated-signing-v2/integration-checks.json, SHA256
b8cbe5d67d3b2938706e149b2de28291eb9b82a7864753133eaae027e8aeaeb0.
The coordinator keeps Task11 D29 first; GUI validation requires a fresh handoff.
Retain the verified installed runtime and all private states while waiting.


Signed GUI trial 1 exposed a launcher integration failure: the generated private
Steam Preview.app copies a correctly signed standalone Wine loader into a new
unsigned bundle. Both codesign --verify --deep --strict and spctl rejected it:
"code has no resources but signature indicates they must be present". The real
macOS dialog was reported by the requester. Pear launched; Steam login and game
execution did not succeed. No security override is an accepted remedy.

The minimal correction under the approved app/CLI signing-error scope reuses
pinned Wine programs/start/start.c: /unix translates the exact Steam executable
path, CreateProcessW starts it, and without /wait start exits after handoff.
Call this through the original notarized Wine/bin/wine and existing environment
and bounded runner. Do not generate/copy/re-sign a private app or alter runtime
bytes, entitlements or user data. This replaces the old generated helper identity;
the Wine executable stays separate from the Swift launcher. Retain the failed
bundle as evidence and never adopt it on later launches. Existing account/game
state remains private. Synthetic route/failure/preservation checks are followed
by a new signed app/CLI candidate, their new notarization, then actual UI/game
verification. Runtime archive, source kit and 45 runtime notarization checks are
reusable only while their exact bytes remain unchanged. No public docs change
or GUI success claim follows from preparing this correction. A new host interval
is required; the first GUI grant is consumed.


Original-loader correction validation: 13 Rust tests passed, including exact
Steam arguments through a spaced path, preserved original loader/private bundle
and failed-handoff propagation. The separate app/CLI incrementally built and
received Developer ID signatures without entitlement changes. Both new ZIPs were
Apple Accepted (app d85a8ee3-13dc-4dfa-99e1-389c2436414d; CLI
18c4759c-5f60-4e3b-b27f-25754a31e975). The app was stapled; staple validation,
distribution/Gatekeeper and CLI notarized-policy checks all passed. No Wine or
game ran during this build. Owner31384 exited, lsof showed no owned handles and
the shared slot was returned. Evidence: .build/task47/loader-handoff-v3.
The existing signed-v2 runtime archive and private setup remain unchanged and
are referenced rather than copied. Actual corrected Steam/game UI is still pending
a separate execution interval. Public release and Stage1 completion are not claimed.


Corrected app actual GUI verification completed on October 11, 2026 (KST).
The requester confirmed the official Steam login screen, then login completion.
The signed app-bundled CLI installed App3405340 (build21750826, StateFlags4) and
requested normal Steam Play. Current Player.log recorded Steam initialized and
Direct3D11 on AppleM4Pro. The requester confirmed visible menu, normal input and
normal game exit. Steam -shutdown and Pear window close completed normally;
all 19 pre-cleanup owned identities and the game/guard were absent, lsof found
no state/app handles and the shared lock was returned. No force kill or security
override was used. Existing private14921 remained unchanged. Preserve the newly
authenticated prefix, game and saves; no full runtime copy or migration occurred.
Raw attempt records are retained separately from whole-release.json (SHA256
32926f3a366d76c022fe8be29e758741c3a52c4dab1e00c4ffbd751783f33f1d),
which records released:true, sequence_released:true and no owned PIDs.
The coordinator has the same receipt for Task11's next independent sequence.
This verifies the corrected signed app/CLI handoff on this host; it does not
repeat timed gameplay or establish recovery, a second clean Mac, public release
or Rosetta-free support. Stage reporting and remaining distribution gates remain.


## Stage 1 closure verification reconciliation

The requester explicitly approved Stage 1 reconciliation/report/commit after the
corrected app's successful Steam/game run. Existing approved document locations
remain: update README availability, docs/rosetta-preview.md tested scope and
 docs/development/preview-release.md candidate checkpoint only. No website redesign,
new subsystem, Stage 2 execution or release publication is included.

The original Whisky DMG inspection commands above belong to the rejected GUI
selection. The requester-approved shared entry and source-built replacement
supersede that artifact choice; do not reacquire or execute the retired GUI to
close the current stage. Preserve historical failure outcomes. All S1 cases remain
required and are mapped to the selected signed-v2 runtime and corrected app.

Closure uses these lightweight checks from this checkout, with output retained
under ignored `.build/task47/stage1-closure/`:

```sh
sw_vers
uname -m
df -h .
python3 -B tools/check_governance.py
python3 -B tools/compatibility.py --check
python3 -B -m unittest discover -s tests/docs -p 'test_*.py' -v
node --test tests/docs/test_steam_search.cjs
python3 -B -m unittest discover -s preview -p 'test_*.py' -v
git diff --check
```

Additionally compare all 33 gui-ready.json input digests and the final GUI receipt
chain, confirm source-kit v6 identity, and inspect current app/CLI signatures
without launching them. Reuse the 13 Rust tests from the exact unchanged v3 source
and build receipt, the accepted runtime's 45 image checks and the actual GUI run.
Do not repeat a heavy build or private Steam session solely for reporting. Source
and artifact changes invalidate only affected evidence. Full runtime/source-kit
copies are unnecessary; this closure adds text receipts only (under 5 MiB), with
no private-state traversal, cleanup or modifications. Final release packaging,
recovery, timed gameplay and clean delivery remain later-stage requirements.

The staged diff exposed original whitespace in 26 preserved notice files and
the pinned unified patch. Their exact bytes must remain unchanged for provenance
and package identity. The closure adds .gitattributes entries for these 27 exact
paths only; Pear code/documents keep whitespace validation. Recheck the staged
diff and preserve the source-kit and runtime pins after this metadata correction.


## Stage 2 execution approval and concrete test design

The requester explicitly continued after Stage 1 commit 2c59711. Start with
isolated synthetic failure cases and leave the accepted app/runtime bytes intact.
Reuse the existing Session/Stage transaction, verification, storage and prefix
ownership code. No new download library, recovery subsystem or native manager
admission change is selected. The reviewed Whisky installer removes the existing
runtime before extraction; retain Pear's staged activation instead of importing it.

Current source inspection shows archive acquisition and tar extraction are bound
to absolute system tools, so deterministic interruption tests need a private
source seam. In preview/src/lib.rs, factor only the existing transaction boundaries
into private helpers accepting the download/extraction operation. Production
wrappers still use pinned artifacts, curl HTTPS arguments and tar unchanged.
Test-only fixtures exercise the real verification/rename/cleanup path with tiny
owned files; do not weaken signature or hash admission. Add recovery cases in
preview/src/recovery_tests.rs and use the existing temporary-directory owner.

Cover failed partial download/retry, truncated/missing inputs, failed partial
extraction/retry and existing installation reuse, insufficient-space admission,
compatible partial-prefix resume and unknown-prefix refusal. Assert private save
sentinels and previous ready markers are unchanged on each failure. Explicitly
record seam results separately from real signed CLI interruption and app retry.

Run locked/offline preview Cargo tests with the existing task47 cargo target,
then the 34 Python packaging/runtime tests, governance and diff checks. Incremental
unit-test compilation is a small developer-only operation; no Wine, GPU or private
prefix is started. Retain logs under .build/task47/stage2/unit; keep the Stage 1
sealed app/runtime unchanged. Expected incremental test output below 100 MiB and
synthetic scratch below 2 MiB; preserve exact inputs and remove owned fixture
scratch on exit. Rebuild/sign/notarize any changed app later in an admitted interval.

Actual CLI retry/extraction uses a separate disposable root, the same immutable
archive, at most about 2 GiB additional space and no authenticated state. Request
fresh shared-host coordination before that run. Actual app repeat/save restoration
uses the existing same-runtime task47 private environment only after normal exit
and verified local backup; Steam Cloud interactions and restoration are not yet
qualified. No backup is uploaded or committed. Do not downgrade a live prefix.


Stage 2 discovered a retry usability gap: a corrupt cached archive is rejected
but retained, so the app's Retry repeats the same error. Correct only that cache
path in preview/src/lib.rs. Separate digest/length mismatch from I/O/type errors;
a verified supplied archive remains preferred. When a regular cached artifact
mismatches and its pinned HTTPS download exists, discard only that bad cached
file and use the same staged download/verification. Preserve malformed links,
unreadable inputs and unpublished-runtime cache rather than silently replacing
unknown state. Never touch runtimes/private data. Regression tests must cover
successful retry, failed replacement without activation, offline/unpublished
preservation and unrelated-file survival. Rebuild/sign the changed app later;
Stage 1 sealed candidate stays intact.


## October 11 native checkpoint README clarification

The coordinator relayed the requester's explicit instruction to preserve #47's
README changes while distinguishing the native menu achievement from unfinished
verification. The approved location is the existing root README's two-track
overview, with a public Issue #11 link; no new product document or roadmap is
created. Preserve M3 availability, installation, recovery and license guidance.
This documentation-only change requires no runtime execution or artifact copy.

Evidence reviewed: #11 D32 checkpoint SHA256
c6f451bc8e40a82cffcff93442841d5f6791c779b112eb82fd7b4db3aec1189c
and #12 handoff SHA256
d89fc291a05d24a1d2c8eb2e6c6408ceb92971b087701278cb5fd16732d64891.
The experiment reached the main menu and manual input was confirmed; gameplay
entry failed during loading. Full required host/library Rosetta independence,
Steamworks integration and gameplay qualification remain pending. The M3 signed
Steam result does not establish M1 success. Check governance, links and whitespace.


October 12 Stage 2 actual CLI recovery passed: interrupted extraction never
activated partial files; retry/reuse succeeded; changed runtime content was
refused and restored exact bytes passed. Synthetic state was removed after
process/handle checks; real private state was untouched. Retain receipts under
.build/task47/stage2/cli-recovery-v1. This used frozen Stage 1 CLI bytes.

Build the changed cache-retry source as a separate app-v4 candidate under
.build/task47/stage2, using the existing build/package scripts, cargo target and
authorized Developer ID. Keep the runtime pin, signed-v2 archive and loader
entitlements unchanged. Peak additional output is budgeted at 512 MiB with
3 GiB start headroom. Record exact source inputs before/after; preserve Stage 1
app and all private state. New app/CLI need new notarization and affected GUI
checks; previous notarization does not qualify changed executables. No public
upload or final release is part of this preparation.


## October 12 removal/reinstall preservation check

The requester explicitly continued after actual save restoration and normal
GUI shutdown. Use a disposable Applications directory and a sibling synthetic
Application Support directory under .build/task47/stage2/removal-v1. Copy only
the exact notarized app-v4 bundle (no Wine/runtime/prefix copy). Verify its file,
mode and symlink inventory and signature, remove this trial copy, reinstall the
same app, and compare the data sentinel inventory at every boundary. Run only
the bundled CLI help and a missing-archive check against that synthetic root
to verify the reinstalled executable reopens retained owned state and refuses
the missing input. No GUI, Wine, network download or real private state is used.
This is a lightweight filesystem/CLI check, not a fresh game relaunch proof.

Budget: at most 64 MiB of disposable app/synthetic data and small receipts, with
256 MiB start headroom. Preserve immutable app-v4 and all existing runtime/save
inputs. After process completion and no scratch handles, remove only this new
trial's scratch tree; retain the script, inventories, command outcomes and sizes.
Logical/stat-allocated sizes and measured free-space change remain separate.
Existing approved mydocs/working observation and plan locations are reused; no
public user guide or product-documentation location change is made here.
S2-download's actual interrupted network/GUI retry and S2-removal's post-reinstall
GUI observation remain pending unless independently exercised; source seam and
CLI outcomes must not silently replace those approved observations.


## October 12 combined manual-verification request

The requester wants the remaining interrupted-download GUI retry and actual
post-reinstall launch performed together, without disturbing other work, and is
willing to provide measured active gameplay. Root confirms there is no current
#47 GUI grant; the first ready D33 native-control interval has priority. Prepare
exact readiness before any new app/Wine/Steam/game execution. A request for a
slot is not admission and does not depend on Issue #11 being complete.

Reuse unchanged notarized app-v4. For actual HTTPS interruption, target the
pinned official SteamSetup.exe (2,380,800 bytes, SHA256
7d3654531c32d941b8cae81c4137fc542172bfa9635f169cb392f245a0a12bcb)
through the existing shared archive routine in a disposable unauthenticated
state. The runtime URL remains unset; do not describe this as an actual runtime
network-download test or invent a release URL. Use only a process-scoped
CURL_HOME/.curlrc transfer-rate limit, documented by curl, to make cancellation
observable. Preserve TLS and pinned hash checks, original HOME and global network
settings. Close the trial Pear window normally after partial bytes are observed;
verify child exit, absent cache activation and scratch cleanup; reopen the same
app to retry, verify the pinned final cache and actual Steam login screen. No
login or proprietary game is needed in this disposable state.

This disposable setup requires its own runtime extraction and prefix: the full
runtime copy is justified by isolated preparation and cleanup; it must not share
mutable authentication/game state or write through runtime links. Plan at most
6 GiB additional space including Steam self-update, require 8 GiB free at
admission, and recheck actual space before extraction. Preserve the immutable
runtime archive. Retain only sanitized receipts after normal client shutdown,
owned PID/birth and handle verification; delete only unauthenticated scratch
once the recorded release conditions hold.

Then reinstall an exact copy of the app in a task-owned Applications location
and open the existing same-runtime #47 environment. Verify original app inventory
and signature, real Steam library, normal Megabonk launch and retained settings.
The requester can record active gameplay duration, excluding menu/pause time,
and observe audio/input before normal save/exit/relaunch. Such evidence remains
bound to this exact candidate; it does not approve a Stage 3 transition or final
public-delivery claims. Existing authentication, games and both save backups
remain retained. No new heavy run is started by this planning update.

GitHub macOS CI is suitable for independent package/CLI and failure-path checks,
not automatically the ordinary-player qualification: hosted images include
developer tools. A separately recorded clean standard-user setup or separate
Apple Silicon Mac is the preferred interactive route; record existing system-wide
Rosetta, tools and security configuration and do not equate a fresh prefix with
a clean environment. No user account, paid runner, workflow or public upload is
created by this research.

References reviewed October 12, 2026:
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- https://docs.github.com/en/actions/reference/runners/larger-runners
- https://docs.github.com/en/actions/concepts/runners/github-hosted-runners
- https://curl.se/docs/manpage.html


## October 12 Stage 2 closure plan and same-Mac clean setup proposal

Requested planning scope: finish Stage 2 without silently promoting synthetic
evidence or adding Stage 3 gates. No account creation, OS installation, GUI run,
new signing, publication or stage transition is performed by this plan update.
The existing implementation plan remains the authoritative location; no new
product document is introduced.

### Stage 2 closure sequence

1. Freeze app-v4, its bundled CLI, signed-v2 runtime and corresponding source
   identities. Reconcile every S2 case with exact existing evidence. Reuse
   unchanged observations; distinguish the frozen Stage 1 CLI extraction trial
   from changed app-v4 source tests. In particular, explicitly resolve whether
   the observed failed same-runtime transaction/recovery satisfies S2-update;
   never claim a different-runtime migration or general updater was tested.
   If the existing record misses a required assertion, add only that bounded
   disposable check before closure.
2. Obtain a fresh coordinated slot with exact inputs, private-state ownership,
   process supervision, free-space admission and normal-release checks. The
   current #11 D33 interval takes priority; no need to wait for all of Issue #11.
3. Perform S2-download using unchanged app-v4 and the pinned official Steam
   installer in disposable state, following the preceding process-local rate
   limit/cancellation plan. Require partial download observed, no activated
   partial artifact, normal Pear shutdown with child cleanup, successful GUI
   reopen/retry, final pinned bytes and visible Steam login. Preserve HTTPS.
   This qualifies the shared acquisition path for the Steam installer; final
   hosted runtime download is a separate release-path check after URL wiring.
4. Reinstall the unchanged app copy, retaining the existing separate #47 state.
   Require exact bundle/signature identity, normal Steam library, owned game
   launch, preserved settings/progress and normal game/client/app shutdown.
   Combine S2-removal's actual relaunch with the compatible recovery check where
   valid. Do not repeat already-qualified actual save restoration merely for
   counting tests; preserve baseline and changed-save backups.
5. Reconcile the complete eight-case matrix: S2-download/install/invalid/space/
   repeat/update/save/removal. Required unavailable or failed observations stay
   open. Run governance and diff checks, affected focused tests only if inputs
   changed, verify that no private data is staged, write the Stage 2 report
   through the stage-report procedure, and commit source plus report together.
   Request Stage 3 continuation only after this completion gate passes.

Success means setup failure is recoverable and reinstall/recovery preserves
state for the declared candidate. It does not mean a public download, every game,
Cloud synchronization or Rosetta-free support is qualified. Retention remains
the preceding 6 GiB peak/8 GiB admission proposal for disposable setup; avoid
concurrent full copies and retain all authenticated data. Actual free space must
be rechecked because other work shares the volume.

### Same-Mac clean setup (Stage 3 proposal, not a Stage 2 blocker)

The approved S3-clean criterion already allows a recorded clean OS/test-user
setup; a second physical Mac is not compulsory. Recommend a new standard macOS
user for the first practical pass. The requester creates its password directly
in System Settings. Do not use Guest, migrate account data, sign into iCloud,
copy developer shell configuration, or adopt another user's Pear/Steam prefix.
Record prior app/runtime/cache absence, system-wide Rosetta/developer tools,
security settings and hardware/macOS identity. Existing system-wide tools and
trust state are shared, so report this as a fresh-user setup on the same Mac.

Use final distributable bytes obtained through the intended browser delivery
route. Open through Finder with normal protections and preserved quarantine;
require no developer environment overrides, build tool installation, credentials
copying or security bypass. Install into a location supported for a standard
user, prepare fresh runtime/Steam state, sign in directly to official Steam and
download the owned game. Record loaded runtime dependencies to detect accidental
use of Homebrew, a developer checkout or another user's files. A static source
inspection or restricted PATH alone cannot establish their absence.

After startup, the requester can perform measured 20-minute active gameplay,
excluding menus/pauses, check input/audio, save, exit and relaunch in this same
clean-user session. This can combine S3-clean, S3-play and S3-resume on identical
final bytes once Stage 3 is authorized. Preserve original-user login/saves;
Steam Cloud behavior remains explicit rather than assumed. Schedule a dedicated
interval: fast user switching does not stop other users' processes and all
users still share GPU/memory/disk. Do not reboot or log out active work sessions.

A stronger optional route is fresh compatible macOS on a separate APFS volume
or external SSD, without Migration Assistant or developer tools. It preserves
the original OS when correctly installed to the separate target, but needs a
backup, sufficient storage and coordinated reboot. Current observed free space
is only about 14 GiB; no internal second-OS installation is planned. An external
SSD is preferable if this stronger check becomes necessary. This still tests
the same physical hardware and does not establish broad Mac compatibility.

Account creation, volume changes and reboot are separate future user actions,
not authorized execution from this planning request. GitHub CI can supplement
package and failure-path checks, but its developer-preconfigured runner is not
a substitute for the recorded interactive clean-user/clean-OS flow.

Apple references reviewed October 12, 2026:
- https://support.apple.com/en-gb/guide/mac-help/mchl3e281fc9/26/mac/26
- https://support.apple.com/en-ca/118282

## October 12 authorized independent supervisor preparation

The requester, through the explicitly authorized coordinator, requested concrete
Stage 2 execution supervision and small independent tests while D33 retains
actual-play priority. Add an operator-only Python driver at
preview/validation/stage2_supervisor.py and focused standard-library tests at
preview/test_stage2_supervisor.py. This is not app/runtime product code and does
not change Wine/FEX, signatures or the final candidate. Reuse the existing
Stage 2 grant/hash/shared-lock and normal Steam shutdown patterns, fixing the
previous transient-tccd ownership error by baseline identity classification.

The driver will require an exact single-use Root grant and current assignment,
verify input hashes and output absence, hold the shared lock, and accept only
allowlisted phase commands through a task-local request queue. GUI window close
and human visual observations remain operator actions, never inferred from a
process exit. Track PID birth/executable identity, distinguish pre-existing OS
services from newly observed owned processes, and require zero owned identities
and zero app/state handles before release. On failed checks stop new launches;
retain private state and allow normal shutdown/release only. No broad kill,
security bypass, real-account mutation, automatic retry loop or Stage 3 work.

Prepare exact argv, runtime environment, per-command limits, monitored output/log
limits and manual observation criteria before submitting readiness. Small tests
use temporary synthetic files and injected process/handle snapshots, never the
shared lock, real GUI, Wine, runtime build or private data. Budget under 20 MiB
and one short Python test run; remove fixtures on completion. Retain driver,
tests, ready manifest and sanitized evidence through Stage 2 review. Keep an
explicit pending report outline in existing observation JSON until completion;
do not write a completed Stage 2 report while required GUI checks remain pending.


## October 12 cloud preparation with unchanged qualification gates

The requester chose cloud development with locally downloaded candidate testing,
explicitly retaining interrupted-download GUI retry, actual post-reinstall app
execution and all mandatory pre-release checks. This changes execution locations,
not the approved acceptance matrix or stage progression. This plan extension is
Issue-specific workflow material in this existing plan; no product-document move
or second roadmap is introduced.

Reuse preview/build.sh, package.py, runtime input pins, existing source tests and
notarization procedures. Keep the current signed runtime immutable when its
recorded inputs remain valid. Do not rebuild Wine merely to move development.
Cloud coding handles source, website/document and portable checks. A macOS CI
runner handles the existing Apple-tool-dependent build/sign/package checks;
Swift/AppKit, native smoke builds and actual macOS process/handle supervision
cannot be qualified by Linux fixture success. Actual GUI/game observations remain
on the requester's Mac under the existing shared-resource admission policy.

Before cloud handoff, preserve current uncommitted Stage 2 changes in an explicitly
identified source checkpoint without claiming Stage 2 completion. Transfer only
reviewed source and approved immutable artifacts. Do not upload the entire .build
folder, private prefixes, game data, saves, diagnostic logs, local Keychain or
signing private keys. Hosted signing requires separately authorized credential
provisioning; existing local certificate permission is not cloud-key-export
permission. Local absolute-path ready/grant manifests remain local evidence and
are not portable cloud execution instructions.

| Required evidence | Execution location and retained boundary |
|---|---|
| S2-download | Local GUI: interrupt an owned download, close/reopen and retry; no partial activation, pinned successful bytes. Current SteamSetup case remains distinct from the final hosted-runtime delivery path. |
| S2-install/invalid/space/update | Preserve all eight-case matrix criteria and approved exact-source seam allowances. Portable mocks may run in cloud; actual macOS installer/CLI evidence and unresolved update-scope reconciliation remain explicit. |
| S2-repeat/save | Reuse unchanged exact-input observations; rerun affected checks if CI output, runtime, configuration or current client/game invalidates them. Preserve current and restored local saves. |
| S2-removal | Locally remove/reinstall the candidate app without removing state; actually open the reinstalled GUI, Steam and game and confirm retained progress. An offline file-copy test alone does not close this case. |
| Final package/security | macOS CI verifies final app/CLI/runtime identity, signatures, notarization and applicable tickets/assessments; local browser-download/Finder first-open under normal protections remains mandatory. |
| S3-play/resume/clean | After Stage 2 completion and Stage 3 approval: measured 20-minute active play, input/audio, save/quit/reload and recorded second clean setup. Same-Mac fresh user is an explicitly bounded option, not a new bottle or a CI build VM equivalent. |
| Licensing and publication | Matching source/patches/locks/build instructions and notices, package allowlist and private-data audit, accurate user instructions/download links and final publication/visibility authorization remain required. |

Candidate CI must upload reviewable private/test artifacts without automatically
publishing a user-ready release. Bind each test record to source revision,
app/CLI/runtime digests, package SHA-256, toolchain and host/client/game context.
The existing package.py --release checks do not consume human GUI qualification;
a future publication workflow must separately require reviewed local evidence
for the exact candidate. A green build or Apple acceptance alone cannot pass it.
Promote the tested final package bytes without rebuilding; rebuilding, resigning,
stapling, changing the runtime URL or repackaging creates a new candidate identity
and requires the applicable package/security/delivery and behavior revalidation.
Do not blanket-repeat unaffected evidence or inherit invalidated evidence.

Cloud setup and CI implementation are preparation work, not an implicit Stage 3
start or public release. Audit/pin the available macOS SDK/toolchain and storage
before running builds, configure approved artifact access without exposing private
state, and keep credentials out of PR jobs. Existing #11 no-fallback first-play
priority remains unchanged; no heavy local run is started by this planning work.
Only real local GUI/game sessions require the local execution slot; cloud jobs
must use their own runner and output roots rather than a local self-hosted runner.

Storage for this plan-only change is negligible; no runtime copies or cloud
artifacts are created. Before actual CI execution, record per-job peak storage,
exact immutable runtime/source inputs, candidate retention through local review,
artifact access and release conditions. Preserve the currently submitted local
supervisor readiness bytes and all recovery backups.


### Authorized cloud handoff implementation, October 12

The requester explicitly continued this plan. Prepare a candidate-only workflow
at .github/workflows/preview-candidate.yml, portable test entry
preview/ci_checks.py, and task-specific handoff instructions at
mydocs/working/task_m3_47_cloud_handoff.md. Reuse pinned checkout/upload actions
already used in this repository and preview/build.sh/package.py rather than
introducing a replacement build system. The new workflow has contents:read only,
no signing secrets, no releases/Pages mutation and no Wine/Steam/game execution.
Its ad-hoc-signed output is not an ordinary-user test release. Prepare hosted
signing only after separately approved credential provisioning.

Use the existing codex/task47 local branch and codex/publish-task47 remote branch
for an explicitly incomplete Stage 2 cloud handoff checkpoint, without opening
a completion PR or merging master. Push this reviewed source checkpoint to the
existing private repository to make it available to cloud tasks and trigger the
bounded CI build; do not claim Stage 2 complete. Include existing task-owned
recovery changes after checking their diff, preserving immutable prior evidence.

One Linux portable-check job (10 minutes maximum) and one macOS 26 ARM64 app/CLI
build job (30 minutes maximum) use GitHub-hosted runners, never this Mac. Pin Rust
1.94.1 and select Xcode 26.5 explicitly; record actual SDK, compiler and runner
image. Mismatched prerequisites fail rather than silently switching. Allow about
3 GiB tool/dependency/target scratch plus 1 GiB uncertainty, require 6 GiB initial
free space, and retain only app/CLI ZIPs, checksums and sanitized build provenance
for 14 days as private Actions artifacts. Runtime/archive/source-kit inputs stay
local unchanged for now; no full runtime copies or builds are needed. Scratch is
released with the hosted job; preserve/download the selected candidate and its
receipts before expiration when it is needed for subsequent signing/review.
Local Python fixtures remain below 20 MiB and clean up their own temporary state.

Verification: strict non-skipped Python discovery, existing packaging/runtime
boundary fixtures, actionlint for workflow syntax, governance and git diff checks;
then inspect actual hosted job outcomes/artifact manifest. A hosted build failure
is fixed only in the affected preparation path. No new local heavy slot is used.
The local supervisor readiness and 16 frozen inputs are unchanged; cloud output
requires its own candidate identity and future local test admission.

### Hosted signing preparation, October 12

The requester continued after the private cloud environment and hosted candidate
were verified. Prepare an opt-in signing job in the existing candidate workflow,
preview/sign_candidate.py and portable refusal/cleanup fixtures. Keep the signing
job separate from pull requests and ordinary unsigned builds: only this repository,
codex/publish-task47, a push/manual event and exact repository variable
PEAR_SIGNING_APPROVED_SHA matching github.sha may enter pear-preview-signing.
Provision that environment and credentials only after the owner reviews and
explicitly authorizes the concrete destination and secret set. A default-branch
workflow_dispatch requirement must not force an unapproved merge; the existing
push route can use a reviewed commit selected before push. No configuration
variable or secret is populated by this preparation.

Reuse the official GitHub temporary-keychain recipe and Pear build/package tools.
Build/check with no signing secrets first. Import only the authorized Developer ID
identity into a job-owned temporary keychain, store notarization credentials there,
then sign a disposable app copy, submit app and CLI separately, require Accepted,
staple and assess, and create allowlisted packages with sanitized receipts. Clean
keychain and credential files on all outcomes. No runtime signing/entitlement
changes, local Keychain exports, GUI execution or public release are included.
The signed artifact is still a qualification candidate; retain all local gates.

The new job uses a fresh hosted Mac, pinned Xcode/Rust and owned RUNNER_TEMP roots.
Its rebuild is required to obtain a source-identified app without extracting an
untrusted archive near credential material; no full runtime copy is made. Budget
4 GiB plus 2 GiB uncertainty and require 6 GiB free before building. Retain only
app/CLI archives, checksums, manifest and sanitized notary/provenance receipts for
14 days, downloading the selected candidate before expiry for local qualification.
Delete job scratch on completion and signing material even on failure/cancellation.
Local changes and synthetic tests require less than 20 MiB and no shared GPU slot.

Location judgment: extend this task plan and existing cloud handoff for maintainer
setup instructions; no new product guide or official-document relocation occurs.
Verify fixture refusals, acceptance/error handling, immutable source preservation,
workflow event/secret boundaries and actionlint; actual hosted signing remains
unperformed until credential provisioning is approved and succeeds.


The owner approved GitHub CI signing credential provisioning after protection
verification. Required reviewers were rejected by GitHub's current private-repo
plan. The resulting empty environment was immediately restricted and read back as
codex/publish-task47 only; secret count remains zero and approved SHA is unset.
The owner then asked about public conversion rather than approving reduced review
protection. Public-repository required reviewers are supported per GitHub docs.
Resume existing read-only publication inventory; do not change visibility or
provision secrets until the reviewed final-action approval and protection checks.
58 portable fixtures, actionlint and governance passed; actual hosted signing is
unperformed. No local build/runtime/game was started.


Hosted run 38166760208 passed 58 Python fixtures but failed one existing Rust
recovery reopen test (20/21 passed) with a retained Session lock. Inspecting its
close/reopen boundary identified a shared-open-description lifetime risk during
concurrent child spawning. A disposable local fcntl control demonstrated that
closing the original descriptor retains the lock while its duplicate is live;
explicit unlock permits reacquisition. Add explicit Session Drop unlock and a
Rust duplicate-descriptor regression covering concurrent exclusion, reopen and
survival of the new owner's lock after the old duplicate closes. Do not hide the
failure by serializing or skipping tests. Verify the changed core in hosted CI;
this changes the future app/CLI identity, so the prior local frozen candidate is
historical evidence and a newly signed candidate needs fresh local admission.
No existing signed bytes, retained private state or local ready files are mutated.


### Hosted recovery fix and publication preparation receipt

Source e27e002e4745cd1dbd7ac1b7245ac154e589711a passed hosted run
[38167091034](https://github.com/postmelee/pear/actions/runs/38167091034):
58 Python tests on each Ubuntu/macOS job and 22 Rust tests, with zero skips or
ignored tests. App and CLI packaging succeeded; both downloaded archive sizes
and SHA-256 values match the package manifest. Signing correctly remained skipped.
These are ad hoc candidates, not Developer ID/notarized distribution evidence.
The explicit Session unlock changes app/CLI source identity. The old local frozen
readiness record describes only its old bytes; a newly signed candidate needs
fresh readiness and local execution/recovery qualification. No local GUI started.

Publication preparation scanned 2,100 historical blobs from the three remote refs
at the recorded snapshot (before e27e002), plus 49 Issues/PRs, two issue comments
and four Discussions. Selected credential patterns had no matches; this is not a
complete security/privacy review. Nineteen historical blobs contain personal
absolute paths. Current-ref, Actions log/artifact content and disclosure review
remain. master lacks the approved GPL license and Preview entry/release documents
that exist on this task branch. Align the public default-branch entry separately
without merging unfinished Stage 2 solely to unlock CI. The owner has asked about
public feasibility, not authorized visibility conversion. Keep secrets absent and
the approved signing SHA unset until effective reviewer protection is verified.


### Public-source preparation approved October 12

The requester approved the proposed order: publication-content review and a
minimal default-branch license/entry patch, final visibility approval, effective
required-reviewer protection, then hosted credential provisioning/signing and
remaining local qualification. This does not approve a visibility change yet.

Prepare an exact-base patch against current master in task-owned ignored staging;
do not merge unfinished Stage 2 or alter another checkout. Reuse the approved GPL
text, fixture exception, branding and existing official documentation. Location
judgment: README remains the short public landing; docs/README.md and
docs/contributing.md remain navigation/contribution authorities. Interim links
may pin the completed #47 documentation checkpoint while its implementation is
not integrated. License metadata remains at its existing package/fixture paths.
Keep review records in this plan and existing cloud handoff. No second roadmap.

Read-only remote history, author/path disclosures, Actions logs and artifacts
are reviewed by exact identities. Use .build/task47/publication-audit for private
receipts and proposed patch; inspect archives without executing binaries or
extracting uncontrolled paths. Peak additional storage budget 200 MiB plus
100 MiB uncertainty; current Data-volume free space is 14 GiB (df -h). Retain
compact inventories/hashes and proposed patch until publication review; stream
raw log/archive bytes in memory and discard after scan. No runtime copies, local
builds, Keychain reads or shared execution slot. Reuse existing API inventories
but refresh changed heads and surfaces before final approval.


### Public-source review ready for owner decision (October 12)

The requester approved the preparation sequence. The exact-base public-entry
patch is retained privately at .build/task47/publication-audit/master-entry.patch.
Base master: 4340f2059ae187a0322fec564a700721e57a88f8. Pinned Preview guide
source: 4e1be9114fc76802e21b075e143cfc2f86c66c0a. Patch SHA-256:
4f697e6c290dc6eb01f06860e5a32a769d1f5e33c9f7740b2b1fb4820e6429d2.

Fourteen files provide GPL text/package metadata, short README, documentation
and contribution entry points, security/conduct/support/community policies and
Issue/Discussion forms. Existing approved community files are reused; their
Preview links pin the reviewed task source instead of importing unfinished code.
No workflow, runtime source or implementation change is included. master already
preserves the exact Madeira exception under tests/cpu/LICENSES; no duplicate is
added. Its SHA-256 matches the task copy. This is a proposed narrow integration,
not the final #47 PR, stage completion or permission to close #47.

Verification passed: exact-base cached patch application; pinned file targets;
31 governed documents and 284 local targets; 35 existing documentation tests;
five intake YAML parses; whitespace checks. GitHub-rendered intake and private
reporting still need verification after integration/visibility change. Full site
publication and runtime/game qualification remain separate.

Refreshed remote review covered three branch heads, 37 Actions runs (5,647,479
log bytes), 17 artifacts (646 members including nested app/CLI ZIPs), 49 Issues/PRs,
two issue comments, zero review comments and four Discussions. Selected credential
patterns produced no matches; no history paths ending in the reviewed executable,
archive, credential or save suffixes were found. GitHub body attachment URL scan
found none. Artifact entries contain the expected public Steam identities,
redistributable CPU fixtures/results and ad hoc Pear candidates. Review is bounded,
not a guarantee against every possible secret or a general license clearance.

Historical author names/email and personal absolute paths remain visible if
published. Actions development binaries are not player releases. Zero tags or
releases exist. Wiki is enabled in metadata but its authenticated Git endpoint
returns Repository not found; no readable Wiki contents were available. This
limitation is recorded rather than treating a failed read as an empty-content audit.

No visibility, master, secret or runtime-state change occurred. The exact signing
branch policy and zero environment secrets were read back. After final owner
approval, integrate only the reviewed public-entry change, recheck changed remote
inputs, then make the existing repository public. Verify required reviewer
postmelee, disable administrator bypass and preserve the exact branch rule before
provisioning credentials. A single owner must be able to approve their own run;
this is a manual approval gate, not independent peer review. Enable private
vulnerability reporting, verify intake availability and apply prepared Discussion
50/51 updates. Keep Pages and player downloads gated.

Private review receipts, the prepared tree/patch and after-public draft messages
remain retained for this decision. No raw log/archive downloads were retained,
and no binary was executed. Inspect the latest remote delta again after approval;
prior public-source snapshot hashes are not an unbounded future approval.


### Approved public conversion and credential handoff

On October 12 the requester explicitly approved the final narrow public-entry PR
and existing-history visibility conversion. PR #54 merged as
3a15ddd2539ca5c0578834ff644548e58b7a6a39 after eight hosted checks passed; #47
remains open. Public visibility, required reviewer postmelee (single-owner manual
self-review allowed), exact codex/publish-task47 branch and administrator bypass
disabled were read back. Private vulnerability reporting is enabled. No signing
secrets are present yet. Owner-only encrypted export of the exact Developer ID
identity and a dedicated app password are the remaining credential inputs.

Prepare a local-only helper under .build/task47/publication-audit/ to collect
these through getpass and send them on stdin to gh secret set for the approved
environment. Re-read protection before every secret, refuse a configured approved
SHA, check the public certificate fingerprint and encrypted PKCS#12 key bag, and
never print or write secret values. Do not extract the local pear-notary profile
or export all identities. Retain only non-secret completion metadata. This is an
internal provisioning helper, not product functionality; no documentation move.
Portable synthetic checks cover protection refusal and exact destination routing;
actual credential registration remains pending direct owner input.


### Public source and CI credential registration completed (October 12)

The owner approved the exact public-source change and visibility conversion.
PR #54 merged as 3a15ddd2539ca5c0578834ff644548e58b7a6a39 after eight hosted
checks passed. The repository is public; #47 and Stage 2 remain in progress.
Private vulnerability reporting is enabled. Bug and Show and tell forms rendered
in the browser; the Wiki displayed its empty first-page creation state. Prepared
Discussion 50/51 updates now distinguish public source from a player release.
No Pages deployment or player release was performed.

The owner completed the local credential helper. Its non-secret receipt and
GitHub metadata confirm four expected environment secret names and the approved
public certificate fingerprint. Secret contents were not read back. Protection
was rechecked: required reviewer postmelee, exact codex/publish-task47 branch,
administrator bypass disabled. Single-owner self-review is permitted; this is
manual owner approval, not independent peer review. The original Keychain
identity and owner-exported encrypted certificate remain preserved.

Set PEAR_SIGNING_APPROVED_SHA to e27e002e4745cd1dbd7ac1b7245ac154e589711a and
rerun existing hosted run 38167091034, attempt 2, without debug logging. The
preview/, manager/ and signing workflow trees match current task HEAD 39c5001.
Rerunning preserves the reviewed original commit/ref and avoids changing source
or merging unfinished Stage 2 merely to trigger signing. The protected sign job
must wait for the owner's GitHub approval; do not approve it through automation.
Remove the approved-SHA variable after the selected run finishes. Credential
registration alone does not establish successful import/signing/notarization.

Reuse the existing hosted storage plan and workflow-owned fresh roots: builds
admit at least 6 GiB free; credentials are transient in the job-owned keychain;
only allowlisted candidate packages and sanitized receipts are retained for 14
days. No local substantial build, runtime copy, Steam or game execution occurs.
Local receipts are small task evidence; retain signed candidate bytes through
local qualification and preserve all earlier private state/recovery dependencies.
A fresh signed app needs new readiness and a non-conflicting GUI validation slot.

Attempt 2 passed both portable fixtures and the hosted macOS app/CLI build.
GitHub now reports Approved Developer ID candidate as waiting, with pending
environment pear-preview-signing and owner approval available. No signing job
has started; the owner was directed to Review deployments on the run page.


### Hosted identity discovery correction

Attempt 2 imported the encrypted identity and validated dedicated notary
credentials successfully, then codesign failed with no identity found before any
notary submission. Always-cleanup passed and no signed artifact was uploaded.
The approved SHA was removed. Inspecting GitHub's official macOS certificate
recipe found the missing user keychain-search-list setup. Apply that step only
inside the disposable hosted signing runner, retaining exact certificate selection
and current trust policy. Add an early valid code-signing identity check and
portable acceptance/refusal cases. No local Keychain, app runtime source, Wine,
entitlements or private export changes. Actual success still requires a fresh
owner-reviewed CI run; this is a repair within approved Stage 2 signing scope.
Source: https://docs.github.com/en/actions/how-tos/deploy/deploy-to-third-party-platforms/sign-xcode-applications


### Hosted signed candidate accepted and locally assessed (October 12)

Owner-approved run [38171422915](https://github.com/postmelee/pear/actions/runs/38171422915)
passed on exact source 0f712b93bbd239a1defd959da4dbf1cd0ad9a7a1. The corrected
keychain search-list setup resolved the earlier identity lookup failure. All
three jobs passed: 59 Python fixtures per test job and 22 Rust tests per Mac
build, zero skips/ignored. App and CLI notarization both returned Accepted:
12fff2ca-f4f3-4fa4-aa7d-4e3683e8c2f6 and
04de6001-cf22-4a9d-8b9c-170ae6bd232f, respectively. Job-owned credential cleanup
passed. Removed PEAR_SIGNING_APPROVED_SHA and read back its absence.

Downloaded only the signed artifact to .build/task47/stage2/ci-signed-0f712b9.
Both ZIP sizes/hashes match the manifest; source/provenance/notary receipts agree.
Archive paths/types were checked before separate app/CLI extraction. This Mac
passed deep strict team-bound app signature, staple validation, Gatekeeper,
distribution assessment, CLI notarization and help. The CLI matches the app's
embedded CLI. The app package allowlist excludes runtime/private payloads.
No quarantine/security attribute was removed and no Steam/game/GUI was started.
This is local package assessment, not clean-user or game qualification.

Reuse the existing Stage 2 supervisor with a new immutable candidate inventory,
16 exact inputs and fresh output root final-gui-ci-0f712b9. Readiness SHA-256:
debbf025dde9f319ef596adf4305f7828210618feb3c80faa972612437f7f049.
Readiness is at .build/task47/stage2/supervisor-preparation-ci-0f712b9/ready.json.
Requested a conflict-free fresh coordinator grant for actual download interruption
and GUI retry, then post-reinstall Steam/game launch. The old app/runtime/private
state and old readiness remain preserved. Host free space was about 13 GiB;
small candidate download/extraction stayed within 100 MiB. Exact logical,
stat-allocated and observed free bytes are in the observations record; no cleanup
or free-space attribution is claimed. Retain these packages and receipts through
local qualification. The inherited 8 GiB entry/6 GiB output GUI budget still applies.

Stage 2 remains in progress. Measured gameplay/clean-user qualification is Stage 3;
public runtime URL, final DMG and player release remain separate pending gates.


## October 12 scoped continuation after recovered Steam update

The requester approved proceeding with the storage-observer repair and the
remaining reinstall/Steam/game check. Reuse the existing operator supervisor,
standard-library traversal and signed CI 0f712b9 candidate; no app/runtime rebuild
or repeated download test. The previous interval remains failed due to observer
ENOENT; retain its original Steam error and the separately observed owner retry
after full network recovery (normal login pixels). No failure latch is reset.

Change only preview/validation/stage2_supervisor.py and its synthetic tests.
Enumerate storage without following symlinks; tolerate only disappearing child
entries, preserving root absence and permission/other failures. Test those
boundaries deterministically without Wine, GUI, shared lock or account state.
Keep copyright/SPDX notices on the two modified original files.

Create fresh ignored readiness for a reinstall-only interval: install a small
trial app copy, verify its inventory/signature, use the existing reinstall action
to remove that exact copy and copy the immutable signed source to a new location,
verify and open preserved existing state, then official Steam game launch. Pin
new supervisor/test hashes and source checkpoint, original app/runtime identities
and prior release evidence. The action allowlist excludes trial Steam download,
retry, sign-in and disposal. Normal shutdown and independent whole release remain
mandatory. A fresh coordinator assignment is required for the shared Mac session.

Location judgment: this is internal validation/evidence in existing preview and
mydocs task locations, not product documentation; no public docs changes.
Artifact lifecycle: #47 owns small synthetic scratch (<20 MiB, auto-cleaned),
reinstall preparation (<1 MiB) and two small app copies (<64 MiB). Reuse existing
runtime and authenticated state in place, no full runtime copy. Allow 2 GiB
uncertainty for Steam updates; filesystem free-space monitoring includes growth
of existing mutable state, and output has its own size limit. No minimum-time
gameplay claim. Retain signed inputs, old failure
trial, source checkpoint and receipts through Stage 2 review. Preserve original
private data; release disposable app copies only after normal exit and review.

Verification of this preparation: all 64 Preview Python tests passed (including
22 supervisor cases); changed-source notice validation passed for both modified
Python files; git diff --check passed. These are synthetic/offline results, not
reinstall execution. Storage traversal ignores FileNotFoundError only for child
entries and does not follow static symlinks; root and access failures still stop
new work. Signed app/runtime bytes are not edited. Prior GUI record is retained
under final-gui-ci-0f712b9, including independent-release.json SHA-256
5647c7faef2fae4de89ed7905adfc1515fef59feee149acdcaf539acaa831c72.
The post-close accessibility read unexpectedly reactivated the trial launcher;
that occurrence is excluded from recovery evidence. Future close verification
uses process/handle inspection only, never an accessibility call on a quit app.


Reinstall execution update (October 12, 2026): under fresh operation
`task47-stage2-reinstall-ci-0f712b9-r1`, the exact small app copy was removed and
reinstalled, signature/runtime checks passed, and the requester confirmed Steam
library, Megabonk menu/input/progression and normal game exit. The guard observed
no remaining game process. Steam `-shutdown` returned zero and the app was closed
without any post-close accessibility call. An orphan owned steamwebhelper and
Wine services remained; whole-session cleanup and independent return are pending.
Do not promote normal Steam/main exit to successful full-process cleanup. Reuse
these game observations within the unchanged CI candidate scope only.

Cleanup follow-up: the coordinator verified exact ownership and permitted one
SIGTERM to the orphan steamwebhelper only. Immediate PID/birth/executable/prefix
and no-live-game checks passed; after that signal all owned Wine services exited.
The guard used abort-release rather than claiming normal full-session success.
Independent process/handle/flock checks confirmed full resource return (49 tracked
lifetimes plus owner absent); receipt SHA-256
eb80d8aa8b08fd7b558cb9728f3e1f81746640ce8113795bcc6f5018714066c9.
Existing private state and failed trial are retained, no GUI reacquisition or
extra launch occurred. Reinstall success and abnormal helper cleanup remain
separate observations; Stage 2 matrix/closure review is still pending.


## October 12 non-conflicting Stage 2 evidence review

The requester explicitly asked for Stage 2 result reconciliation and assessment
of whether the remaining Steam helper exit problem blocks distribution. Location
judgment: use `mydocs/working/task_m3_47_stage2_review.md` and the existing JSON
observation record for this internal interim assessment; do not create a formal
completed-stage report or change public product documentation. Existing task
approval covers this requested documentation work.

Reuse exact signed CI 0f712b9, prior app-v4 host observations and supervisor
receipts within their separate scopes. Compare current launcher/core source to
CI and recheck existing CI status without dispatching jobs. No source change,
Steam/Wine/game execution, build, signing, cleanup or shared execution lock.
Storage planning: documentation-only changes below 1 MiB; no substantial output,
full runtime copy or storage reclamation. Preserve all previous retention terms.

The review distinguishes passing reinstall/game observations from abnormal
harness-requested Steam shutdown. Normal Steam UI Exit/reopen is the smallest
remaining host check; it needs a later coordinated interval. Public user exit
risk must be resolved, but this does not itself mandate an upstream runtime
patch or broad repetition of passed tests. Stage 2 remains in progress, and
Stage 3 and final delivery requirements remain unchanged.

Review validation: offline governance check passed (37 documents, 354 local
targets); review-relative links and observations JSON syntax passed; candidate
source identity and coordinator receipt hash matched; git diff --check passed.
No runtime test was repeated and no other worktree was modified.

## October 12 expedited distribution continuation

The requester explicitly asked to continue toward distribution as quickly as
possible. Keep required checks, reuse exact unaffected evidence and avoid a
repeat of the full download/reinstall/game sequence. The focused Stage 2 UI-exit
readiness uses the existing supervisor without source changes and one small app
copy. Fresh operation: `task47-stage2-steam-ui-exit-ci-0f712b9-r1`.
Readiness: `.build/task47/stage2/steam-ui-exit-preparation-ci-0f712b9-r1/ready.json`,
14194 bytes, SHA-256
`6940344ddca60eaf433e38e54f134ef32757986ab02c6e936fc194eeb2a763c8`.
Validate-only passed for 16 exact inputs and the existing app inventory. The
sequence is library open, normal Steam-menu Exit and separate Pear close,
process/handle quiet verification, one library reopen, and final normal UI exit.
There is no game, build, download, sign-in, programmatic Steam shutdown or kill
action. The 120-second normal-exit observation is a bounded test window, not an
assumed success timeout. An abnormal exit requires retained evidence and scoped
cleanup. Execution still requires fresh coordinator assignment and quiet roots.

Retention: reuse immutable app/runtime and authenticated state in place; copy
only the small app at execution. Allow 32 MiB for app/log receipts plus 512 MiB
uncertainty, and 2 GiB for possible Steam self-update growth in existing state.
Retain prior failed and successful receipts. Entry requires 4 GiB free; stop new
work at 2 GiB free, 256 MiB output or 16 MiB aggregate logs; the guard's 20-minute
safety ceiling is not a gameplay test or project time limit. No output run root
is created until admission.

Independent distribution input review: the signed CI app passes the explicit
27-file package allowlist. The matching runtime source kit is
`pear-runtime-source-kit-signing-v6.tar.gz`, 204187222 bytes, SHA-256
`61e7f41f4644c49061e485e3149cc0cc0ee33b4e58aaf417dd6380630b930fbe`;
its bytes match the existing 11-input/127-notice verification receipt. Older
source-kit variants are not selected for distribution. No package was rebuilt
or uploaded by this review.

Remaining delivery work must use one final candidate, not publish today's test
app as a finished installer: its compiled runtime download URL is still empty.
After Stage 2 closure, integrate the already-prepared original-source notices,
bind the runtime/source hosting addresses, build/sign/notarize the resulting
exact revision in approved CI, and prepare final DMG/CLI/source checksums. Changes
to the final candidate require affected delivery checks, not relabeling old
results. Define the same-Mac clean-user test and timed owner gameplay under the
approved Stage 3 scope; retain any limits versus a second physical Mac. Enable
catalog download links only after the actual release assets are available.
Location judgment: this entry records internal execution/distribution preparation
in the existing task plan; no public wording or release-state change yet.

Focused UI-exit closure: the owner confirmed normal library, Steam-menu Exit
and Pear close, preserved login/library after one reopen, and a second normal
Exit/close. The admitted guard passed with no forced cleanup. Independent check
found 69 tracked lifetimes plus owner absent, no owned handles, and the shared
lock returned; receipt SHA-256
`ee7fa7db0c42d48d47030051a6b555110007610db138f39b80c1d406c23c4155`.
The earlier automated -shutdown failure stays historical and is not overwritten.
Stage 2's recovery matrix is complete within the recorded approved seam scopes;
final delivery remains Stage 3. No other chat was invoked to begin other work.

## Stage 3 entry — October 13 requester continuation

The requester explicitly approved Stage 3 after the completed Stage 2 report.
Preview distribution takes priority; do not invoke other chats to start other
work. Preserve the existing signed candidate and private state as recovery
inputs while preparing one final CI candidate.

Reuse the existing package allowlist, signing transaction, Apple hdiutil,
codesign/notarytool/stapler and GitHub protected signing environment. Extend the
signing transaction to produce a separately signed/notarized/stapled DMG containing
only the already-audited app and an Applications link. Hash after stapling and
retain the existing ZIP/CLI outputs. Test rejection and atomic staging boundaries
with synthetic commands; actual Apple validation belongs in hosted macOS CI.

Integrate the already-approved source notice/checker work selectively, preserving
the supervisor fixes. Carry forward master4340f20 artifact-retention rules and
its linked manual plus the separately verified 951264b guidance additions; do
not replace another worker's checkout. Document locations remain README and the
existing docs/contributing.md and docs/development/preview-release.md. These are
previously approved public entry/contributor/release locations; this step adds
notice procedure and DMG packaging facts without claiming released support.

Reserve the immutable final asset URL under GitHub release v0.1.0-preview.1 for
the already-pinned runtime. This source preparation is not evidence that the URL
is live. Keep catalog availability false until final assets exist and affected
browser/download/clean-user checks pass. Matching runtime source kit v6 and exact
Pear source must accompany final distribution. Homebrew is deferred beyond the
app and CLI; it is not a first-release prerequisite.

Storage: this checkout creates only source, synthetic temporary fixtures and
small receipts (<64 MiB); no local Wine/game/build interval. CI owns isolated
build/signing directories, requires 6 GiB free and keeps bounded candidate
artifacts for 14 days. A DMG adds one small app copy and image, conservatively
<128 MiB beyond the existing candidate job. No full runtime copy or rebuild;
retain runtime/source-kit and old signed app through final delivery review.

Stage 3 preparation checks: `python3 -B preview/ci_checks.py` passed 66
synthetic checks with no skips; `python3 -B -m unittest discover -s tests/docs
-p 'test_*.py'` passed 94 checks; governance checked 37 official documents and
358 local targets. These checks do not run Apple signing or qualify the DMG.
The changed Rust fixture explicitly supplies an empty-URL artifact so its
network-refusal oracle remains valid after the real runtime URL is reserved.
The runtime binary and matching source kit remain unchanged. The changed
launcher, package recipe and DMG need exact-revision hosted CI validation.

## October 13 qualification prerelease approval

The requester explicitly approved publishing candidate f9d9578 as a public
qualification Pre-release before the final browser/clean-user/timed-play checks.
This is a narrow sequence exception to the earlier no-upload-before-checks rule:
ship the exact signed app/CLI/DMG, pinned runtime, corresponding source archives
and checksums together under v0.1.0-preview.1, visibly pending qualification.
Do not call it a qualified player release, activate the website download or
change the frozen candidate. Prepare a draft, verify its complete asset set and
exact source target, then publish with prerelease=true and latest=false.
After publication, verify anonymous HTTPS delivery and SHA-256 before the clean
user test. This authorization does not change Stage 3 acceptance criteria.

No runtime rebuild/copy is needed. Upload existing immutable runtime/source files
in place. Bound local download verification to at most one asset at a time;
stream large assets into SHA-256 rather than retaining duplicate archives.
Preserve the existing private state and recovery baseline. The requester will
create any clean standard macOS account directly; do not create accounts, reboot
or log out other users automatically. No other chat is invoked to start work.

The requester also approved a brief shared component sentence in the GitHub
release body and download page: “This release uses Wine 11.0 and DXMT 0.80.”
Location: retain the existing download renderer in tools/compatibility.py and
existing page layout; add one sentence below the platform requirements without
enabling buttons or deploying Pages. This follows the previously approved user
entry-point location; no second roadmap or new product page is introduced.

Fresh-user handoff: the requester created standard user peartest (UID 503).
The read-only baseline records M4 Pro/24 GB/macOS 26.5.2, enabled SIP and
Gatekeeper, existing system Rosetta/Xcode, no global Pear Preview app and no
current Wine/Steam/game/compiler processes. The new user's private state is
not observable from the original user; do not infer absence from permission
denial. This is explicitly the same-Mac fresh-user route, not a clean second OS.

The existing shared advisory lock is reserved for the requester-driven browser
installation/play test by a small task-owned Python/fcntl lease using the
existing OS locking mechanism. It records owner/entry/explicit release, performs
no app launch or cleanup and has no game time limit. The old Stage 2 assignment
is not reused as Stage 3 admission; this operation follows the requester's new
explicit distribution priority and fresh-user approval. No other chat is called.
The helper lives only in ignored Stage 3 scratch; retain its receipt until review.

## October 13 approved first-run presentation refinement

The requester approved the proposed bounded follow-up: explain initial downloads
and sizes, wait for an explicit Download and install action, show download bytes
and progress plus indeterminate preparation stages, and expose version information.
Full removal and destructive settings are deferred. Keep the same Rust core and
Swift/AppKit window; reuse curl, cancellation, hash verification, atomic staging,
ready-state checks and the pinned signed runtime. No new installer framework,
network API or dependency is needed. An initial read-only setup-info command must
not create state or contact the network. Returning installations may open Steam
after the existing core validates their state. CLI commands remain explicit
requests to prepare; add read-only setup-info and version entry points.

Use fixed byte sizes from the artifact pins for the runtime and Steam installer;
Steam updates and games have variable sizes. Do not imply compressed downloads
are installed disk usage or fabricate percentages for extraction/Steam updates.
Use native AppKit controls, keyboard actions and accessible progress text.

Create a distinct preview.2 app/CLI candidate; preserve published preview.1 assets
and its owner-reported evidence. Keep the unchanged runtime URL and source kit.
Tests cover read-only metadata, ready-marker identity, progress while an owned
fixture child runs, cancellation/error preservation, and fragmented UI output.
Run the existing Rust/Python checks and compile the Swift presentation. Re-sign
and notarize in the protected CI environment; recheck affected first-run/retry
and installed-state launch paths on the exact resulting app. Do not require a
new twenty-minute game session solely for unchanged runtime presentation work.

Documentation location: this internal plan and existing Stage 3 receipt record
the change; later update existing preview user/release guides in docs/, keeping
the previously approved destinations. No new product documentation root.
Storage: reuse the current task-owned Rust target; a new small app and Swift
fixture binary go under .build/task47/stage3/first-run-ui, with <256 MiB additional
local outputs expected. No Wine runtime or private prefix copy. Hosted CI uses
its existing isolated build/signing/storage policy. Retain the small candidate
through signed successor review; preserve all current recovery inputs.
