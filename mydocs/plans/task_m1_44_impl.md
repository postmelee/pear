# Task #44 Implementation Plan: Read-only Steam route and reuse research

Task plan: [task_m1_44.md](task_m1_44.md)
GitHub Issue: [#44](https://github.com/postmelee/pear/issues/44)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Branch: `codex/task44`; base: `942bd816913d8792c55f821fdc2ad309b1b85daf`
Date: October 10, 2026 (Asia/Seoul)
Status: The requester approved Stage 3 by explicit continuation after `2833306` on October 10, 2026. All three read-only research stages are complete; the investment decision, conditional experiments and acceptance map are recorded in [task_m1_44_stage3.md](../working/task_m1_44_stage3.md). Final-report/publication procedure, runtime/bridge implementation and native experiments require their separate continuation/approval.

## Context and Evidence Rules

Apply the task plan's root/scoped rules, official requirements, upstream pins, reuse and license decisions, exclusions and document-location judgment. This workflow's implementation-plan filename describes execution of research and reporting steps; all three stages remain read-only with respect to runtime, bridge, game and account state. No compiler, guest program, native memory probe, debugger attachment, login, signing operation or proprietary download is part of these stages.

The #11 live Issue now names QR acquisition and Dock-backed Megabonk integration. Its current local branch includes the accepted #40 merge at `504f19d`, while the Dock-priority plans, acquisition adapters and tests are still changing. The original Stage 1 evidence remains bound to `09ea427`. Do not execute those live adapters or treat uncommitted source as an accepted interface. #10 remains at `37395ee` with pending observer/module/owner-hook work. #40's correction and reports are available on this plan's merged base; the preserved private candidate is a historical reference, not a fresh execution authorization.

The current read-only research permission remains valid. This plan fixes the formal artifact/verification sequence without expanding that permission. A Windows i386 installer is not evidence that #11 needs broad WoW64. Before recommending substantial loader/memory/ABI changes, Stage 2 compares existing macOS Steam bridge reuse. That comparison never becomes a prerequisite for #11's minimum Dock run. A concretely demonstrated required helper remains a blocker for its own route.

### Input selection and retention

- Select source inputs by the exact task-plan commits and explicit retained catalog paths, never the newest matching build or an authenticated-prefix search. Use committed files through Git where possible; identify useful uncommitted research documents by their actual content hash and inspection date.
- Read #11's `mydocs/working/task_m1_11_stage1_observations.json`, `task_m1_11_stage2_diagnostic.json`, `task_m1_11_stage2_reuse_observations.json` and `task_m1_11_priority_20261010.json`. Only public/allowlisted metadata is eligible for new tracked receipts.
- Retained public source roots are `.build/task11/source-review/` and `.build/task11/dock-review1/`; the parser evidence leaf is `.build/task11/stage2-parser1/`. The exact installer may be inspected in place at its previously selected acquisition location after its known hash is checked. Do not copy proprietary bytes or open `selection.json`/account/prefix/profile material.
- New public source snapshots, when missing locally, go in fresh ignored `.build/task44/source-review/<review-id>/` leaves. Fetch only targeted files/tree metadata at an immutable commit. Record origin, commit, path, size, digest and license source; never execute downloaded code/build scripts. Initial bound: 8 MiB per file and 64 MiB total public-source material, with bounded network commands; any larger need is assessed before acquisition. No full repository/submodule checkout or runtime reconstruction is implied.
- Preserve failures and differing historical bytes. If a retained input differs from its receipt, record the mismatch and stop using that claim; do not overwrite its expected hash. A new snapshot may support a separate dated claim after inspection.
- Public observations use a small task-local JSON record, not a new product schema: scope `read_only_research`, source/artifact identities, claim-to-source references, actual inspection outcomes, explicit unknown/unavailable/unperformed entries and limitations. Do not export private absolute paths, account identifiers, tokens, source excerpts from proprietary files or raw execution diagnostics.

The available planning tools are Python 3.14.4, Git 2.53.0 and GitHub CLI 2.89.0. Python standard-library hashing/JSON/PE-header inspection and existing offline governance checks suffice. Re-record versions when they matter to a performed check. Native compilation/signing authority and the actual selected macOS Steam host architecture have not been checked for execution. Source-only work takes no native compilation lock and does not interfere with its owner.

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Establish route requirements and evidence inputs | Research note, route matrix, Stage 1 observations | Exact catalog/receipt comparisons, bounded static headers, claim-scope and unknown checks |
| 2 | Compare existing WoW64 and native bridge contracts | Function/dependency and bridge comparison matrices | Pinned source paths/symbols, license terms, call/callback/session/architecture evidence gaps |
| 3 | Decide next investment and specify minimal experiments | Decision, evidence-to-experiment mapping, Stage 3 report | All research acceptance criteria, precise future gates, shared input order and preserved #11 independence |

Commands below are planned checks. Existing historical results are named separately and cannot be counted as new execution. Each stage is verified, reported and committed before requesting the next stage.

## Document Location Check

| File | Planned Location in Task Plan | Stage Artifact Path | Match | Notes |
|---|---|---|---|---|
| Research findings and decision | `mydocs/tech/` | `mydocs/tech/task_m1_44_reuse.md` | OK | One dated research note developed across the three stages; no official adoption/support claim. |
| Stage observations | `mydocs/working/` | `mydocs/working/task_m1_44_stage{1,2,3}_observations.json` | OK | Allowlisted source/hash/status evidence only. |
| Stage reports | `mydocs/working/` | `mydocs/working/task_m1_44_stage{1,2,3}.md` | OK | Actual checks and limitations; use stage-report template/procedure. |
| Plans and daily status | Approved task roots | Current plans and actual dated `mydocs/orders/` file | OK | Change only #44's row and approvals. |
| Final report | `mydocs/report/` | `mydocs/report/task_m1_44_report.md` | OK | Later final-report procedure after research completion and publication authorization. |

No `docs/`, runtime, host, tests, tools, source lock, manual or other task artifacts are edited by these research stages. New findings that require official guidance remain a named follow-up and location decision.

## Stage 1 - Establish Route Requirements and Evidence Inputs

### Artifacts

New: `mydocs/tech/task_m1_44_reuse.md`, `mydocs/working/task_m1_44_stage1_observations.json`, `mydocs/working/task_m1_44_stage1.md`.

Modified: #44's plan approval/status and daily-board row as appropriate. Use the technical-note and stage-report templates already provided by the repository.

### Changes

1. Record current owner commits and exact #11 research input hashes. Preserve the distinction between the October 9 desktop proposal and October 10 Dock priority. Review any newer sanitized #11 helper inventory only if available; source/receipt changes are recorded, not silently merged into an earlier claim.
2. Establish a route matrix with phase, role, exact bytes/version when known, PE machine, native host role, dependency origin, required/conditional/unknown status and evidence type. Include Dock, genuine steamclient64, Wine services.exe, SteamService.exe and game prerequisites separately from the original SteamSetup/bootstrap/desktop path. A source call to an executable establishes a conditional dependency, not that its selected bytes are i386 or that the game takes that path.
3. Recheck or reuse the 18-file upstream catalog and 97-file Dock catalog according to their unchanged inputs. For Stage 1's durable receipt, retain the comparison method, actual checked counts and mismatches; do not merely copy the intake's pass field. Compare the preserved parser observation and producer/harness/fixture identities without rerunning its binary.
4. Bind the installer-header observation to the known original hash: PE32/i386, non-LAA, RELOCS_STRIPPED, preferred `0x00400000`, DYNAMIC_BASE, empty relocation directory. Record why both fixed-base policy and actual conflict behavior remain unresolved behind the target gate. Do not classify an untested PE32 fixture as fully valid because the target was rejected first.
5. Add the existing native-bridge candidate and five decision criteria as an unqualified comparison entry, ready for Stage 2. No substantial owner/ABI adoption recommendation precedes that comparison. Context and source pins remain as approved; no technical Metal skill is applicable.

### Verification

Inputs: exact retained public catalogs, historical parser receipt, original installer identified above, merged #40 reports and current sanitized owner context. Inspect only explicitly selected non-authenticated helper files if the source owner has exposed them in a suitable input/evidence set. Missing helper bytes or dynamic necessity evidence remain `unknown`/`unperformed`; stage completion means accurate bounded research, not a complete helper runtime.

Methods and expected outcomes:

- Standard-library streaming SHA-256 with at most 1 MiB chunks; compare size/digest against the selected catalog. All claims marked unchanged must match. A mismatch is retained and cannot support unchanged evidence reuse.
- Parse bounded DOS/COFF/optional-header fields only after checking offsets and file extents, or reuse a pinned existing reader after inspecting its safe entry point. Retain reader/command identity and decoded allowlisted fields. Do not import or execute #11's live changing adapters.
- Compare source/role conclusions with the exact relevant Dock service and launch functions. Keep `GetSystemDirectoryW` selection, detached-process ownership and conditional installer dispatch visible. No service binary runs.
- Review false-success cases manually: i386 installer -> all game routes need WoW64; x64 Dock -> all helpers x64; installed DLL -> required at runtime; parser result -> guest execution; old inventory -> current client architecture. Each inference must remain rejected or supported by additional actual evidence.

Common commands, run from this task worktree:

```sh
git status --short --branch
git log -1 --oneline
python3 -B -m json.tool mydocs/working/task_m1_44_stage1_observations.json > /dev/null
python3 -B tools/check_governance.py
git diff --check
git diff --name-only
```

The stage report records exact read-only Python/reader commands actually used and their input/hash ledger. JSON parse success checks serialization only. Independently inspect the note's source references, template sections and local links. Run no CPU/graphics/native suites for unchanged documentation.

Existing evidence reuse: #11's parser controls establish the recorded ARM64/x64 acceptance and early i386 rejection at the exact old parser, not a present #40 parser execution. The #40 candidate receipt/report establishes its historical correction and bounded results, not arbitrary PE32 support. Changed parser/producer/input bytes invalidate the affected historical comparison; current ownership/authorization must be checked separately for any future execution.

### Commit

`Task #44 Stage 1: record route requirements and retained evidence`

## Stage 2 - Compare Existing WoW64 and Native Steam Bridge Contracts

### Artifacts

Extend `mydocs/tech/task_m1_44_reuse.md`; add `mydocs/working/task_m1_44_stage2_observations.json` and `mydocs/working/task_m1_44_stage2.md`. Preserve the Stage 1 receipt as historical evidence.

### Changes

1. Trace Wine's CPU-module selection and i386 builtin closure; the Pear arena caller/parser and ordinary Wine PE32 relocation code; address reservation/protection/query/unmap and fixed-base handling. Record reusable source versus Pear-specific constraints and exact merged #40 patch preimages.
2. Trace complete FEX WoW64 process/thread initialization, GDT/FS/TLS/context, syscall/unixcall entry, callback re-entry, exception reset, memory alloc/protect/dirty/free/map/unmap/read notifications, invalidation and thread/process retirement. Pair each PEAR_FEX_MEMORY_OWNER refusal with its actual missing contract. Review qualified ARM64EC helpers only for semantics that can legitimately transfer; do not propose wholesale guard removal.
3. At pinned NotProton `c3a49486c14cdf6b9716e2e7ac55286aa537fcf1`, inspect the tree and relevant build/generated-interface, lsteamclient, steam-shim and ntdll-patch sources. Use retained public files first and fetch only missing targeted inputs. Resolve gitlinks or external generated headers by their actual identities; absent source or an unpinned dependency stays unresolved.
4. Map original Windows steam_api64 calls through existing interfaces to genuine native Steam, then map ordinary callbacks/asynchronous call results, data/handle conversions, thread/re-entry, lifetime and shutdown. Record the owning account/App ID/client session and normal launch context requirements from actual code. No token/session inspection or claim of game-specific complete API coverage follows from this static work.
5. Compare the three candidate work scopes: required Dock i386 helper correction; broader Windows bootstrap/desktop capability; reuse of an existing macOS Steam bridge. For each, record exact extra runtime/source/build/host architecture needs, updater/ABI coupling, required future evidence and file-specific terms. macOS Steam and an ARM64 SDK slice do not prove the required native process/library closure.
6. Preserve the task-plan pins, languages and license/contribution boundaries. If a pin lacks a relevant implementation, identify the gap and candidate source explicitly before expanding the source selection. No runtime architecture, official-document location or Apple technical-guidance change is introduced.

### Verification

Inputs: Stage 1 source ledger, task-plan upstream commits, exact retained Pear composed sources where required and pinned NotProton source/notice files. Tools: same read-only Python/Git/GitHub CLI with command/version records; no native runtime prerequisite.

For each matrix row, record source commit, path, complete relevant symbol/function and dependent helpers; distinguish source-declared behavior, Pear execution evidence and required-but-unperformed proof. Inspect call and return paths and their callers, not only symbol names or search hits. Trace at least one representative interface call and callback path end to end where source is available; explicitly name any gap preventing the trace.

Check the five bridge criteria individually: original call/ABI coverage; callbacks and lifetime; genuine ownership/session; complete required Rosetta-free host closure; reproducibility and update maintenance. Reject init-only, launched-process-only, menu-only, callback-only, host-slice-only and downloader-login-only conclusions. Separate supported interface versions from the selected game's presently unknown dynamic interface set.

```sh
python3 -B -m json.tool mydocs/working/task_m1_44_stage2_observations.json > /dev/null
python3 -B tools/check_governance.py
git diff --check
git diff --name-only
```

Rehash newly selected source files once against their recorded immutable origin and verify all links/citations. Reuse Stage 1 input comparisons where their bytes and role are unchanged; fresh upstream/main is never substituted for a pin. Source hash/call interface/patch/build configuration changes invalidate affected comparisons. Lack of actual runtime evidence remains a limitation, not a failed source-only verification or a successful compatibility result.

### Commit

`Task #44 Stage 2: compare WoW64 and native Steam bridge reuse`

## Stage 3 - Decide Next Investment and Specify Minimal Experiments

### Artifacts

Complete `mydocs/tech/task_m1_44_reuse.md`; add `mydocs/working/task_m1_44_stage3_observations.json` and `mydocs/working/task_m1_44_stage3.md`. Prepare the evidence mapping needed for `mydocs/report/task_m1_44_report.md`; the later final-report/publication procedure does not start automatically.

### Changes

1. Assess each #44 acceptance criterion against the completed research. State which helper requirement, if any, is demonstrated on #11's selected route, what still needs actual observation and what belongs only to broad desktop support. Update dated context from newly available sanitized peer reports without retroactively changing earlier evidence.
2. Use the bridge comparison to recommend the smallest justified next investment, with remaining unknowns and an explicit separate approval boundary. A result may retain FEX for a required helper, defer broad desktop work or propose a bounded existing-bridge experiment. Do not promote comparative source availability into a guarantee of lower cost or successful execution.
3. For every proposed experiment, specify the unresolved claim, exact input/producer/candidate prerequisites, original fixtures, expected positive and refusal outcomes, command/interface selection, cleanup and retained evidence. If no executable adapter yet exists, label commands as design work instead of inventing a runnable tool.
4. Preserve the original low-address and i386 requirements as conditional proposals: ordinary host-NX reservation/query/read-write below 2 GiB, 64 MiB initial bound, ownership/conflict/exhaustion/rollback/unload, and unchanged high MAP_JIT; actual PE32/HIGHLOW two-base and four-byte width/overflow controls; non-LAA/relocation-stripped fixed-base success/refusal; original i386 syscall/thread/TLS/handled-exception/unaligned/callback/invalidation/retirement fixtures. A standalone low reservation does not establish Wine/FEX entry or Steam capacity.
5. State later changed-boundary regression obligations: full affected #6 CPU/order with original references and AVX unsupported status, #40 loader/parser/cleanup, and affected #8 native/translated publication/graphics/lifetime. No deliberate native fatal-fault/no-TEB route, synthetic relocation of the installer or changed proprietary bytes.
6. Name exact input integration order: merged #40 correction before common-loader supplement, #10's accepted observer interfaces when available, #11's actual route identity and #42 for ISA/XSTATE changes. Preserve per-executable actual authorization, owned supervision, original-file integrity, measured disk budget and shared lock ownership for future native work. This stage executes none of those experiments.

### Verification

Inputs: immutable Stage 1/2 ledgers and source references, actual peer evidence available at decision time and original #44 acceptance criteria. Tools: read-only inspection and document/JSON checks; native build/tool/authorization availability for each future experiment is reported as checked, unknown or not checked, without fabricated receipts.

Review every proposed experiment against a named missing claim, scoped input and measurable outcome. Verify both success and refusal controls, required original i386 fixture categories and regression invalidation. Record the difference between a source-ready hypothesis, a buildable candidate, host feasibility, original guest execution and real Steam/game qualification. No broader implementation follows merely because the research is complete.

```sh
python3 -B -m json.tool mydocs/working/task_m1_44_stage3_observations.json > /dev/null
python3 -B tools/check_governance.py
git diff --check
git diff --name-only
```

The final research acceptance map must cover route separation, bridge criteria, reusable/missing functions, exact provenance/owners, concrete experiment proposal, #11 impact and continuation decision. Unavailable helper/session/runtime data can remain explicitly unresolved with its required next check; it cannot support a positive claim that i386 is unnecessary or that a bridge works. Such honest limits can satisfy this research scope while actual integration remains open.

### Commit

`Task #44 Stage 3: record investment decision and minimum experiment proposal`

## Verification

- Verify actual stage inputs, claim-to-source references, JSON serialization, document links, scoped file changes and whitespace before the stage report/commit. Governance and JSON success do not validate runtime semantics.
- Use the technical-note/stage-report templates. Include actual commands, input identities, results and unperformed operations; keep task observation JSON separate from the product evidence schemas.
- Planning-only checks now: template-required headings, three complete stage sections, document-location agreement, local links, #44-only board changes, `python3 -B tools/check_governance.py` and `git diff --check`. No runtime test is appropriate or claimed.
- Preserve all original failures and required future regressions. Reuse results only where source/tool/artifact/configuration and claim scope still match. Never refresh a pass field to hide a missing input.

## Commits

This planning commit: `Task #44: implementation plan and approval record`.

Stage commits use the messages above and bundle that stage's research note/observations with its stage report and scoped board updates. After research completion, final-report preparation/publication follows its separate procedure and authorization. No remote push is part of this implementation-plan commit.

## Stage Dependencies

1. The approved task plan permits this detailed research plan. Approval of this plan with Stage 1 continuation starts only Stage 1's formal artifacts and checks; read-only research authorization does not approve any runtime experiment.
2. Stage 2 follows Stage 1 verification, report, commit and explicit continuation in this chat. It uses Stage 1's retained inputs and named gaps.
3. Stage 3 follows the corresponding Stage 2 completion and explicit continuation. A substantial owner/loader/ABI proposal depends on the bounded bridge comparison; #11 execution does not.
4. Later implementation, experimental execution, official-document changes, PR publication, merge and Issue closure retain their separate approvals. Missing actual helper evidence does not prevent unrelated source research or convert into a passed integration gate.

## Risks and Responses

- **Live peer source:** #11 inputs and #10 hooks are changing. Use committed inputs or explicit hash-bound research snapshots, inspect available sanitized evidence and leave their files/processes intact.
- **Ambiguous absence:** no observed i386 helper may mean incomplete coverage. Keep phase/required-set gaps and rely on #10's actual final coverage before route qualification.
- **Bridge scope growth:** stay with the pinned existing lsteamclient/steam-shim path and concrete missing contracts; no new client/bridge, macOS Steam modification or wholesale launcher adoption.
- **License/source coupling:** retain per-component notices and source-build dependencies. A public source tree or blanket license label is not distribution clearance.
- **Approval confusion:** these three stages produce research artifacts. The unapproved high/low memory owner remains a candidate, and every proposed native experiment remains unperformed.
- **Private inputs/storage:** use explicit retained non-secret artifacts, keep raw private material out of Git and source snapshots bounded, and perform no heavy rebuild or cleanup of another task's cache.

## Approval Request

Approve this detailed three-stage research plan and begin **Stage 1 only**: establish the exact retained input ledger and Dock/helper versus bootstrap/desktop requirement matrix, verify static evidence and document unknowns. Later stage continuation and any runtime/bridge implementation or native experiment remain separate decisions.

## Stage 1 Evidence Update

The [Stage 1 research note](../tech/task_m1_44_reuse.md) and [observation ledger](../working/task_m1_44_stage1_observations.json) preserve 115 matching source identities, retained parser evidence and the newly shared #11 step2a/component/bootstrap receipts. The selected Valve service is statically i386; its actual necessity is not demonstrated before the no-account Dock failure. The earlier missing-component observation is superseded only for selected-file identity. #11 owns independent direct-game x64 startup diagnosis. Before any later overlapping implementation, record exact files/preimages in the order accepted #40 baseline -> separately reviewed #11 correction if applicable -> separately approved #44 correction; no correction is implemented here. #11 execution remains independent of this comparison.

## Stage 2 Evidence Update

The [source comparison](../tech/task_m1_44_reuse.md) and [Stage 2 ledger](../working/task_m1_44_stage2_observations.json) bind Wine/FEX reusable functions, all inspected owner-mode WoW64 refusal groups, and a representative native Steam API/callback return path to pinned sources. Existing NotProton entry patches ntdll and rewrites mapped Valve client exports/entry/data, so it is not a drop-in within the approved scope; generated wrappers and conversions remain separable candidates. Original-game interface/session coverage, all required Rosetta-free host components and full build closure remain unperformed. No bridge/WoW64 implementation or native experiment follows. Stage 3 may propose the minimum missing evidence after explicit continuation; #11 remains independent.

## Stage 3 Evidence Update

The [decision and conditional experiment proposal](../tech/task_m1_44_reuse.md) and [Stage 3 observations](../working/task_m1_44_stage3_observations.json) map all seven research acceptance criteria. Continue #11 independently; no actual required i386 Dock helper is demonstrated yet. If one is demonstrated, prefer separately reviewed targeted Wine/FEX reuse. E1 is the smallest conditional new low-address NX diagnostic; E2-E4 retain subsequent loader/i386/helper gates. Existing bridge adoption remains deferred pending a compatible entry design (E5); full desktop is a separate investment (E6). No native experiment or implementation ran. The final-report evidence mapping is ready, but its later publication procedure does not start automatically.
