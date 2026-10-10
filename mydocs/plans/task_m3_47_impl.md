# Task #47 Implementation Plan: Rosetta-based Megabonk preview

Task plan: [task_m3_47.md](task_m3_47.md)
GitHub Issue: [#47](https://github.com/postmelee/pear/issues/47)
Milestone: M3 — Rosetta-based Megabonk Preview
Branch: `codex/task47`
Date: October 10, 2026 (Asia/Seoul)
Status: task plan approved by explicit continuation in this chat; implementation
plan and Stage 1 execution awaiting approval.

## Context and Approval Record

The requester approved M3/Issue registration, then task-start, then the task plan
in successive explicit continuations. Task-start commit is `37694eb`. The current
continuation authorizes this implementation plan, not unreviewed runtime changes.
No stage or live game test has begun.

Apply the task plan's root/scoped documentation rules, workflow, upstream reuse
rationale, private-state boundaries and document-location judgment. Also read
[host rules](../../host/AGENTS.md) and [test rules](../../tests/AGENTS.md) for any
later host or fixture changes. No native-host implementation is currently selected.
The `todo` format applies to board updates; `task-stage-report` and
`task-final-report` apply at their respective boundaries. No Apple Metal technical
skill is selected: ordinary GUI/game observation is not a Metal debugging task.
If graphics diagnosis becomes necessary, select the relevant expertise first.

The preview remains independent of #10/#11's moving native runtime. Use the
attached checkout only. No source import, new Pear UI, new profile contract,
authentication client or supervisor is authorized by this plan. If existing GUI
capabilities cannot meet a required behavior, review the concrete minimal change
and its file locations before implementation. Keep the failing gate open.

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Select and reproduce the existing GUI route | `mydocs/tech/task_m3_47_reuse.md`, Stage 1 report and sanitized observations | Exact app/runtime identities, normal security, isolated official Steam install/sign-in/owned install/Play and real menu/Steamworks |
| 2 | Qualify setup recovery and save preservation | Stage 2 report, recovery scenario records, reviewed minimal correction only if required | Interrupted setup, bad inputs, low storage, repeat launch, compatible update/recovery and actual save restoration |
| 3 | Qualify the final preview and publish guidance | User guide, README/index/roadmap edits, Stage 3/final reports | 20-minute active play, input/audio, save/exit/relaunch, second clean setup and final delivery conditions |

Each stage ends with required checks, a stage report and commit before explicit
continuation. Failed requirements remain failed; source inspection is not live
execution. Tools below are operator verification, not the end-user interface.

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

## Stage 1 - Select and Reproduce the Existing GUI Route

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
5. Use normal upstream GUI installation with the verified baseline runtime and
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
   locations without copying private content into reports. Select unchanged GUI
   delivery if it passes; otherwise record the smallest concrete correction.

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
state for adverse cases. Start with existing GUI retry/export/restore facilities;
do not invent a product installer because test automation would be convenient.
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
