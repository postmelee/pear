# Task #44 Plan: 32-bit Steam requirements and existing bridge reuse

GitHub Issue: [#44](https://github.com/postmelee/pear/issues/44)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Branch: `codex/task44`
Date: October 10, 2026 (Asia/Seoul)
Base: `942bd816913d8792c55f821fdc2ad309b1b85daf` (master, including PR #43)
Status: The requester approved Stage 3 by explicit continuation after `2833306` on October 10, 2026. All three read-only research stages are complete; the investment decision, conditional experiments and acceptance map are recorded in [task_m1_44_stage3.md](../working/task_m1_44_stage3.md). Final-report/publication procedure, runtime/bridge implementation and native experiments require their separate continuation/approval.

## Purpose

Determine what 32-bit execution the selected Dock-backed owned Megabonk route actually requires, independently of complete official Windows Steam bootstrap/desktop support. Produce a source-pinned reuse and missing-contract analysis, a limited comparison with an existing native macOS Steam bridge, and a concrete minimum experiment proposal for the next investment decision.

The i386 Windows installer establishes a requirement for that installer route only. macOS Steam availability establishes neither bridge feasibility nor a Rosetta-free game route. #11 continues its QR/acquisition/Dock minimum execution validation independently. This research can identify a concrete required helper blocker, but does not make its broader desktop or bridge comparison a new #11 prerequisite.

## Background

### Governing context and authorization

Read [root rules](../../AGENTS.md), [README](../../README.md), [official index](../../docs/README.md), [architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md), existing [platform reuse](../../docs/research/platform-reuse.md) and [Steam/game research](../../docs/research/graphics-and-game-integration.md). Apply runtime/FEX, host, tests and documentation rules when inspecting those areas. The task-start/todo skills, central task-plan template and task/Git/conflict/document-location manuals govern this planning change.

The requester authorized read-only research, explicitly added limited native-bridge comparison before substantial loader/memory/ABI proposals, then approved Issue creation and continued to task start. Existing text placing native-bridge comparison after Windows desktop qualification does not override that research ordering. It does not authorize changes to official product requirements, a new bridge or the proposed WoW64 owner.

The shared main checkout contains unrelated `analysis/` and `research/` files. After fetching origin, master and origin/master both identify the base above. A dedicated managed worktree was created from that ref without switching or editing the shared checkout. #11/#10 and retained #40 workspaces are read-only dependencies.

### Existing evidence and concurrent ownership

| Input or owner | Inspected checkpoint | Claim and limit |
|---|---|---|
| #11 | Stage 1 `09ea427`; uncommitted October 10 Dock-priority plans and priority observation; October 9 plans archived locally | Static package/source evidence and approved route priority. Broad WoW64 owner amendment remains unapproved. Current selected Dock helper bytes and actual necessity are not inferred from the installer. |
| #40 / PR #43 | Merged into `942bd81`; correction `7ef56cd`, Stage 3 `da9ff6b`, final report `c692099` | Bounded 64 MiB image correction, unchanged GameAssembly attach, metadata read-open and GC finalizer startup. Later 120-second timeout does not identify a cause or establish menu/Steamworks. |
| #10 | `37395ee`; pending module work | Process-lifetime fixture baseline; complete real runtime process/module evidence and final shared interfaces remain separate work. |
| #42 | Open AVX/AVX2 follow-up | Feature exposure and extended-context support remain its scope. No AVX enablement is selected here. |
| #5/#6/#8 | Merged limited FEX, CPU and graphics baselines | Reuse source and evidence within exact inputs and claims. x64 qualification does not establish i386 semantics. |

The #40 runtime receipt `d6d053e73eb0a7625177e1901936efeed4ee7eddadd9e822a0094398e8505808` was read-only hash-checked during intake. The 18 retained upstream source-review files, 97 Dock comparison files, parser producer/harness/binary/fixture/observation and baseline parser-source hashes also matched their recorded inputs. These checks preserve historical evidence; they are not fresh execution or current signing authorization.

Original SteamSetup.exe: 2,380,800 bytes, SHA-256 `7d3654531c32d941b8cae81c4137fc542172bfa9635f169cb392f245a0a12bcb`. Static headers show PE32/i386, non-LAA, RELOCS_STRIPPED, preferred base `0x00400000`, DYNAMIC_BASE and an empty relocation directory. The recorded native parser rejected i386 before parsing; its ARM64/x64 fixture controls passed. Thus enum/HIGHLOW changes alone cannot establish installer admission: fixed-base/non-LAA policy and occupied-address handling also need review. No guest execution follows from either observation.

The previous `0x300000000` arena observation is above 4 GiB for that run only. The low guest-domain proposal is not proven impossible or selected by this fact. Complete exceptions, callbacks, invalidation, process/thread retirement and memory notifications remain unqualified under the inspected PEAR_FEX_MEMORY_OWNER WoW64 path.

## Scope

### Included

- Make a two-route matrix for Dock/game helpers versus official bootstrap/desktop, recording phase, original file identity, PE/host role, static imports, actual required execution evidence and unknowns. Inspect explicitly selected non-authenticated bytes when available. Missing helper inputs remain unknown and do not stop independent source comparison.
- Read pinned Wine/FEX WoW64 functions and dependencies, including PE32/HIGHLOW and fixed-base handling, low-address reservations, syscall bridges, thread/TLS/context, callbacks, exceptions, notification/invalidation and retire/unload paths. Record reusable contracts and concrete gaps, preserving unsupported guards.
- Compare existing NotProton lsteamclient/steam-shim reuse against required i386 support before recommending substantial shared changes. Assess original Windows Steamworks calls, interface/ABI layouts, callbacks/call results, ownership/session linkage, all required host architectures and maintenance/source-build dependencies.
- Record file-specific source/license/contribution provenance, exact shared input revisions, future patch preimages/order and affected regression obligations. Keep a bounded proposal for the smallest missing experiment without executing it.
- Produce English task research and evidence documents in the approved workflow locations; communicate findings in Korean.

### Excluded

- Runtime/source implementation, compilation or guest/native experiment execution; real Steam sign-in, session/ticket access, game execution, debugging attachment or proprietary package acquisition under this task plan.
- New translator/authentication client/bridge, a whole Madeira import, adopting a guest-offset ABI, changing CPUID/AVX support, or replacing #9/#10 supervision/observation.
- Modifying macOS Steam or CrossOver, rewriting game/Valve binaries, API success substitutes, supported steam_appid.txt shortcuts, or changes to macOS protections/signing/provisioning.
- Editing or cleaning another task's checkout, authenticated state, retained evidence, build caches or native lock. No other chat messaging is authorized.
- Official architecture/roadmap changes, PR publication/merge or Issue closure through this planning approval. Research findings do not qualify a runtime or game.

## Design Direction

### Reuse and source pins

Retain Wine C and FEX C++/assembly for a future required i386 correction. Use the existing readers and retained tests as evidence references rather than writing another PE runner. Read the actual source at each pin and record its dependencies before proposing an adapter.

| Source | Pin and reuse judgment |
|---|---|
| Wine | `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`; WoW64 dispatch, native reservation bookkeeping and PE32 relocation semantics; LGPL terms retained. |
| FEX | `59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa`; primary existing i386 CPU/Windows boundary candidate; MIT downstream reuse and separate prohibition on AI-generated upstream contributions. |
| Hangover | `56e385b7ff490edd281b288f420677093563560b`; module-selection reference, with differing FEX dependency pin; no mixed-binary assumption. |
| Madeira | `48f976429c189f8396e23d251d8a82f43c705922`, FEX gitlink `3bec2ac498bf78156ab47c0c194b0e8cb2849756`; compare coupled guest-window adaptations only as needed, with individual GPL/LGPL/MIT/exception terms. |
| Dock | Origin `7fc8e4d1b5ede349c89b3c155b203a8bf455f5bb`, Madeira gitlink `72558e416a390f3669457930f09a389e54f49556`; reuse the preserved comparison; GPL-3.0-or-later/exception and runtime notices remain distinct. |
| NotProton | `c3a49486c14cdf6b9716e2e7ac55286aa537fcf1`; bounded existing lsteamclient/steam-shim comparison, preserving Steamworks SDK, GPL, BSD and other per-component terms. No distribution clearance or adoption decision. |

At the NotProton pin, the reread README names Steam clients `1788652215`/`1790121765`, CrossOver Preview `20261006`/`2026082`, an ntdll patch and an early FEX path, while recommending Rosetta. These declarations identify coupling to inspect; they provide no Pear compatibility or current-version guarantee. Follow exact call/callback and session paths in source before recommending reuse.

### Decision and integration boundaries

The comparison may support targeted i386 helper work, separately scoped full desktop support, a separately reviewed bridge experiment, or an explicitly unresolved decision. Neither a source function nor an ARM64 library slice proves the original game's Steamworks/session result. Keep download authentication separate from the live client and game session.

Before any later implementation proposal, name actual shared owners and ordered inputs. The merged #40 correction precedes a proposed common-loader supplement, preserving its 64 MiB bounds and regression contracts. #11 owns actual Dock/QR/download/menu/Steamworks integration; #10 owns observer and evidence schema/registration; #42 owns AVX/XSTATE. Future integration must recheck their committed interfaces. Read-only research does not wait for their entire tasks to close.

The current high MAP_JIT plus separate low ordinary host-NX guest domain remains one candidate. Review explicit base/role/domain/generation/32-bit semantics, fixed-base conflicts, protection, rollback and retirement before proposing it. A 64 MiB diagnostic reservation below 2 GiB is an experimental bound, not measured Steam capacity. Do not assume a standalone host reservation proves actual Wine/FEX entry.

No Metal-specific expert applies to this read-only PE/Steam/ABI research. If a later approved runtime change affects graphics or publication, select the Pear Apple-tooling guidance then. No subagent, new plugin or upstream submission is required.

## Document Location Judgment

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| Task and stage plans | Work artifact | Requester and maintainers | `mydocs/plans/task_m1_44{,_impl}.md` | `docs/` | Approval and execution sequencing for this Issue; not an official runtime contract. |
| Reuse/comparison decision | Technical research | Runtime maintainers | `mydocs/tech/task_m1_44_reuse.md` | `docs/research/` | Dated source evidence and unadopted alternatives; no product support or architectural adoption. |
| Stage reports and sanitized receipts | Work evidence | Reviewers | `mydocs/working/task_m1_44_stage{N}.md` and matching observation JSON | `docs/` | Input-bound inspection outcomes and explicit unperformed experiments. |
| Final research report | Work artifact | Requester and maintainers | `mydocs/report/task_m1_44_report.md` | `docs/` | Research acceptance and continuation decision, not a qualification guide. |

No official product/user/API/architecture/roadmap guide is added or edited. `mydocs/manual/` is not a candidate destination. Any later promotion to official guidance requires an explicit location/scope decision.

## Expected Changed Files

New:

- `mydocs/tech/task_m1_44_reuse.md`, developed across the research stages.
- `mydocs/working/task_m1_44_stage{1,2,3}_observations.json`, when needed for allowlisted pins, file hashes, source locations and unknown-status evidence.

Modified:

- No product/runtime/host/test source, source lock, official document, workflow manual or other task artifact.

Task artifacts:

- `mydocs/orders/20261010.md` and later actual work dates when appropriate; preserve other Issue rows.
- `mydocs/plans/task_m1_44.md` and, after approval, `mydocs/plans/task_m1_44_impl.md`.
- `mydocs/working/task_m1_44_stage{1,2,3}.md`.
- `mydocs/report/task_m1_44_report.md` after all approved research stages.

Public-source snapshots may be retained in fresh ignored `.build/task44/source-review/` leaves with exact hashes and ownership. Do not copy account state, private selection files or game payloads there. Planned artifact paths above are not existing files or performed results.

## Tentative Stages

- **Stage 1 - Establish route requirements and retained evidence**
  - Record source/artifact provenance, current owner checkpoints and a phase-specific Dock/helper versus bootstrap/desktop matrix.
  - Reuse valid prior checks; inspect selected available non-authenticated inputs and record missing bytes/necessity without inventing an architecture.
  - Verify catalog hashes and evidence scope, including installer fixed-base flags; no repeat native parser run merely to recover known refusal.
- **Stage 2 - Compare reusable WoW64 and native Steam bridge boundaries**
  - Trace relevant complete functions/dependencies in existing Wine/FEX and pinned NotProton, including original Steamworks call/return, callback/thread/lifetime and real session/ownership connections.
  - Assess required architecture evidence, source-build gaps, licenses, client-update coupling and minimal Darwin adaptation. Keep source declarations separate from measured results.
  - Verify each conclusion against pinned source locations and counterexamples; preserve unresolved contract and private-input gaps.
- **Stage 3 - Deliver investment decision and minimum experiment plan**
  - Recommend the smallest justified next work and identify conditions that would make it a required #11 blocker. An unsupported or unresolved conclusion is a valid research result, with concrete missing evidence.
  - Specify planned experiment inputs, outcomes, negative controls, authorization/resource prerequisites, ownership/order and affected regressions, without implementing or running experiments.
  - Verify all #44 research acceptance criteria, final source references, privacy and non-blocking #11 boundary; prepare the final research report for review.

The workflow's later `_impl.md` will detail these research steps, artifacts, commands and commits. Its name does not authorize a runtime implementation. Stage transitions retain explicit continuation after verification/report/commit.

## Verification Plan

### Stage Verification

- **Stage 1:** Read stable source/receipt hashes and selected PE headers using existing readers or bounded standard-library inspection without invoking runtime entry points. Retain input hash, parser/reader identity, actual fields and status. Distinguish installed file from required helper, PE guest from Mach-O host, and static observation from execution. Changed source, artifact, parser or selection invalidates the affected prior finding; never relabel a missing input as x64-only success.
- **Stage 2:** Bind function-level conclusions to exact upstream commit and path/line or symbol, dependent code and file notices. Cover API interface versions, Windows/host data layout and return paths; callback/call-result lifetime and re-entry; genuine account/App ID/client-session connection; every required native process/library and selected slice; client/Wine/FEX patch maintenance. False-success checks include init-only, DLL-load-only, launch-callback-only, SDK ARM64-slice-only and downloader-login-only reasoning. No source inspection establishes actual-game success.
- **Stage 3:** Check that every recommended experiment has a precise unresolved claim and expected/refused outcomes. Preserve PE32/HIGHLOW width/overflow and fixed-base/non-LAA/occupied-address cases, low NX reservation/protection/conflict/rollback and existing high-owner preservation. Later original i386 fixtures must cover exit/syscall, thread/TLS, handled guest exception, unaligned access, callback/re-entry, invalidation and unload because dispatch alone cannot prove these contracts.

For later shared runtime changes, the proposal must retain applicable full #6 CPU/ordering checks (18 supported cases, AVX explicitly unsupported, 32,768 ordering pairs), #40 parser/loader/cleanup gates and affected #8 native/translated graphics/publication/lifetime checks. Reuse unchanged native Windows references and original fixture bytes only within their valid semantics. These are future execution obligations, not tests run by this research.

Tools currently observed for planning: Git and authenticated GitHub CLI; Python 3 is available for offline inspection/governance. Pin reader/tool versions and source snapshots in the research evidence. A native toolchain, runtime signing/provisioning and actual selected macOS Steam architecture are not checked for execution by this plan. No native build or game-dependent test is appropriate for planning-only documents.

At each document stage, run `python3 -B tools/check_governance.py` and `git diff --check`, check local links/template sections and review the exact changed-file list. These verify documentation routing/format only, not the underlying runtime claims.

### Integrated Verification

- Both Windows routes and the limited native-bridge alternative have explicit requirement/evidence/status mappings; unknowns do not become passing qualification.
- Substantial loader/memory/ABI investment is considered only after the bounded bridge comparison; #11 continues independently.
- Reuse decisions retain exact source/file terms, shared owner/input order and claim-specific evidence invalidation.
- The minimum proposal includes current per-executable authority before restricted execution, owned supervision, privacy and original-file integrity, measured disk/growth budget and `/private/tmp/pear-native-compilation.lock` for later native work. No lock removal, deliberate native fatal fault/no-TEB route or large Wine rebuild is introduced.
- No proprietary bytes, credentials, private selection/profile/signing material, authenticated prefix or raw private diagnostics enter Git. Public source receipts and allowlisted factual metadata are distinct from private execution evidence.
- Every research acceptance criterion is linked to the final report; actual guest/Steam/game/distribution results remain unperformed unless separately performed under future approval.
- `git diff --check` passes; the task worktree is clean after the required commits and before any separately authorized publication.

## Risks

- **Scope inflation:** installer architecture or a bridge reference could trigger broad implementation. Preserve actual required-path evidence and the research-only boundary.
- **Moving peer inputs:** #11/#10 have active changes. Treat their current text as dated context; consume committed interfaces or explicit hash-bound research snapshots, not an implicit latest runtime.
- **Missing helper evidence:** selected Dock component bytes or actual process necessity may be unavailable. Record the exact missing input and continue independent source work; do not block #11 or assume absence.
- **Bridge coupling:** a selected Steam/CrossOver demonstration may depend on unavailable source, x86_64 host code or narrow client ABI. Record concrete dependencies and maintenance obligations before recommending reuse.
- **Evidence overreach:** parser success, mapped DLL or initialization phase cannot establish i386 execution, menu, callbacks or ownership/session success. Keep the exact claim scope beside each observation.
- **Storage/privacy:** intake observed about 13 GiB free, which is transient. Avoid package/runtime reconstruction for source-only questions and retain only bounded task-owned public snapshots and approved sanitized metadata.

## Approval Request

Approve this three-stage research scope, reuse/comparison criteria, ownership boundaries, document locations and verification plan. The next workflow artifact is the detailed research implementation plan; runtime/bridge implementation and proposed native experiments remain excluded. Already authorized read-only investigation is not being reclassified as a new execution grant.

After approval, `task_m1_44_impl.md` will define research-stage artifacts, verification commands and commit messages in detail. Each research stage will be verified, reported and committed before its explicit continuation request. PR publication, merge and Issue closure retain their later approvals.

## Stage 1 Evidence Update

The [Stage 1 research note](../tech/task_m1_44_reuse.md) and [observation ledger](../working/task_m1_44_stage1_observations.json) preserve 115 matching source identities, retained parser evidence and the newly shared #11 step2a/component/bootstrap receipts. The selected Valve service is statically i386; its actual necessity is not demonstrated before the no-account Dock failure. The earlier missing-component observation is superseded only for selected-file identity. #11 owns independent direct-game x64 startup diagnosis. Before any later overlapping implementation, record exact files/preimages in the order accepted #40 baseline -> separately reviewed #11 correction if applicable -> separately approved #44 correction; no correction is implemented here. #11 execution remains independent of this comparison.

## Stage 2 Evidence Update

The [source comparison](../tech/task_m1_44_reuse.md) and [Stage 2 ledger](../working/task_m1_44_stage2_observations.json) bind Wine/FEX reusable functions, all inspected owner-mode WoW64 refusal groups, and a representative native Steam API/callback return path to pinned sources. Existing NotProton entry patches ntdll and rewrites mapped Valve client exports/entry/data, so it is not a drop-in within the approved scope; generated wrappers and conversions remain separable candidates. Original-game interface/session coverage, all required Rosetta-free host components and full build closure remain unperformed. No bridge/WoW64 implementation or native experiment follows. Stage 3 may propose the minimum missing evidence after explicit continuation; #11 remains independent.

## Stage 3 Evidence Update

The [decision and conditional experiment proposal](../tech/task_m1_44_reuse.md) and [Stage 3 observations](../working/task_m1_44_stage3_observations.json) map all seven research acceptance criteria. Continue #11 independently; no actual required i386 Dock helper is demonstrated yet. If one is demonstrated, prefer separately reviewed targeted Wine/FEX reuse. E1 is the smallest conditional new low-address NX diagnostic; E2-E4 retain subsequent loader/i386/helper gates. Existing bridge adoption remains deferred pending a compatible entry design (E5); full desktop is a separate investment (E6). No native experiment or implementation ran. The final-report evidence mapping is ready, but its later publication procedure does not start automatically.
